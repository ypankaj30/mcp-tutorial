import asyncio
import json
import time
from typing import Optional, List, Dict, Any
import httpx

import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()  # load environment variables from .env

# This MCP client connects to remote MCP servers via HTTP

class MCPGeminiHTTPClient:
    def __init__(self):
        # Configure Gemini
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        # Use gemini-1.5-flash for better free tier rate limits
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # HTTP client for MCP communication
        self.http_client = None
        self.server_url = None
        self.request_id = 0

    async def connect_to_server(self, server_url: str):
        """Connect to a remote MCP server via HTTP

        Args:
            server_url: Base URL of the MCP server (e.g., http://localhost:8000)
        """
        self.server_url = server_url.rstrip('/')
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        print(f"Connecting to remote MCP server at: {self.server_url}")
        
        try:
            # Test connection
            response = await self.http_client.get(f"{self.server_url}/")
            if response.status_code != 200:
                raise Exception(f"Server returned status {response.status_code}")
            
            # Initialize MCP session
            await self._send_initialize()
            
            # List available tools
            tools = await self._list_tools()
            print(f"\nConnected to server with tools: {[tool['name'] for tool in tools]}")
            
        except Exception as e:
            print(f"Failed to connect to remote MCP server: {e}")
            print("Make sure the MCP server is running and accessible at the specified URL")
            raise

    async def _send_initialize(self):
        """Send initialize message to MCP server"""
        self.request_id += 1
        message = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "gemini-remote-client",
                    "version": "1.0.0"
                }
            },
            "id": self.request_id
        }
        
        response = await self.http_client.post(f"{self.server_url}/call", json=message)
        result = response.json()
        
        if "error" in result:
            raise Exception(f"Initialize failed: {result['error']}")
        
        # Send initialized notification (required by MCP protocol)
        self.request_id += 1
        initialized_message = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        
        # Don't wait for response to notification
        await self.http_client.post(f"{self.server_url}/call", json=initialized_message)
        print("✓ MCP session initialized")

    async def _list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from MCP server"""
        self.request_id += 1
        message = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": self.request_id
        }
        
        response = await self.http_client.post(f"{self.server_url}/call", json=message)
        result = response.json()
        
        if "error" in result:
            raise Exception(f"List tools failed: {result['error']}")
        
        return result.get("result", {}).get("tools", [])

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool on the remote MCP server"""
        self.request_id += 1
        message = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": self.request_id
        }
        
        response = await self.http_client.post(f"{self.server_url}/call", json=message)
        result = response.json()
        
        if "error" in result:
            raise Exception(f"Tool call failed: {result['error']}")
        
        # Extract content from the result
        tool_result = result.get("result", {})
        content = tool_result.get("content", [])
        
        if isinstance(content, list) and content:
            # Get text from first content item
            first_content = content[0]
            if isinstance(first_content, dict) and "text" in first_content:
                return first_content["text"]
        
        return str(tool_result)

    def _convert_tools_to_gemini(self, mcp_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert MCP tools to Gemini function calling format"""
        gemini_tools = []
        
        for tool in mcp_tools:
            # Clean the input schema to remove unsupported fields
            parameters = self._clean_schema_for_gemini(tool.get("inputSchema", {}))
            
            function_declaration = {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": parameters
            }
            gemini_tools.append(function_declaration)
        
        return gemini_tools
    
    def _clean_schema_for_gemini(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Clean JSON schema to be compatible with Gemini function calling"""
        if not isinstance(schema, dict):
            return schema
        
        # Fields that Gemini doesn't support
        unsupported_fields = {
            'title', 'examples', 'default', '$schema', '$id', 
            'additionalProperties', 'patternProperties', 'dependencies',
            'allOf', 'anyOf', 'oneOf', 'not'
        }
        
        cleaned = {}
        for key, value in schema.items():
            if key in unsupported_fields:
                continue
            elif key == 'properties' and isinstance(value, dict):
                # Recursively clean properties
                cleaned[key] = {
                    prop_name: self._clean_schema_for_gemini(prop_schema)
                    for prop_name, prop_schema in value.items()
                }
            elif key == 'items' and isinstance(value, dict):
                # Clean array item schema
                cleaned[key] = self._clean_schema_for_gemini(value)
            elif isinstance(value, dict):
                # Recursively clean nested objects
                cleaned[key] = self._clean_schema_for_gemini(value)
            else:
                cleaned[key] = value
        
        return cleaned

    async def process_query(self, query: str) -> str:
        """Process a query using Gemini and available tools"""
        # Get available tools
        mcp_tools = await self._list_tools()
        
        # Convert to Gemini format
        gemini_tools = self._convert_tools_to_gemini(mcp_tools)
        
        # Create chat session
        chat = self.model.start_chat(history=[])
        
        # Send the query with retry logic for rate limits
        tools_param = [{"function_declarations": gemini_tools}] if gemini_tools else None
        
        max_retries = 3
        base_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                response = chat.send_message(query, tools=tools_param)
                break
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        print(f"\nRate limit hit. Retrying in {delay} seconds...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        return f"Rate limit exceeded after {max_retries} attempts. Please try again later or upgrade your Gemini API plan."
                else:
                    raise e
        
        final_text = []
        
        # Process the response
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    final_text.append(part.text)
                elif hasattr(part, 'function_call') and part.function_call:
                    # Handle function call
                    function_call = part.function_call
                    tool_name = function_call.name
                    tool_args = dict(function_call.args)
                    
                    try:
                        # Execute tool call on remote server
                        result_content = await self._call_tool(tool_name, tool_args)
                        final_text.append(f"[Calling remote tool {tool_name} with args {tool_args}]")
                        
                        # Send function response back to Gemini
                        function_response = {
                            "function_response": {
                                "name": tool_name,
                                "response": {
                                    "result": result_content
                                }
                            }
                        }
                        
                        # Continue the conversation with the function result
                        for attempt in range(max_retries):
                            try:
                                response = chat.send_message([function_response], tools=tools_param)
                                break
                            except Exception as e:
                                if "429" in str(e) or "quota" in str(e).lower():
                                    if attempt < max_retries - 1:
                                        delay = base_delay * (2 ** attempt)
                                        print(f"\nRate limit hit on function response. Retrying in {delay} seconds...")
                                        await asyncio.sleep(delay)
                                        continue
                                    else:
                                        final_text.append("Rate limit exceeded when processing function response.")
                                        break
                                else:
                                    raise e
                        
                        # Add the final response
                        if response.candidates and response.candidates[0].content.parts:
                            for final_part in response.candidates[0].content.parts:
                                if hasattr(final_part, 'text') and final_part.text:
                                    final_text.append(final_part.text)
                    
                    except Exception as e:
                        final_text.append(f"Error executing remote tool {tool_name}: {str(e)}")
        
        return "\n".join(final_text) if final_text else "No response received"

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Gemini HTTP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        if self.http_client:
            await self.http_client.aclose()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python client_gemini_http.py <server_url>")
        print("Example: python client_gemini_http.py http://localhost:8000")
        print("Note: Make sure to set GEMINI_API_KEY environment variable")
        sys.exit(1)

    server_url = sys.argv[1]
    client = MCPGeminiHTTPClient()
    try:
        await client.connect_to_server(server_url)
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())
