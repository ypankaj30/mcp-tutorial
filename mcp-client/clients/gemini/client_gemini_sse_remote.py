import asyncio
import json
import time
from typing import Optional, List, Dict, Any
from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.sse import sse_client

import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()  # load environment variables from .env

# This MCP client connects to remote MCP servers via HTTP/SSE

class MCPGeminiRemoteClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        
        # Configure Gemini
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        # Use gemini-1.5-flash for better free tier rate limits
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def connect_to_server(self, server_url: str):
        """Connect to a remote MCP server via SSE

        Args:
            server_url: URL of the MCP server (e.g., http://localhost:3000/sse)
        """
        print(f"Connecting to remote MCP server at: {server_url}")
        
        try:
            # Connect to remote MCP server via SSE with timeout
            print("Step 1: Creating SSE client connection...")
            
            # Add timeout to prevent hanging
            try:
                sse_transport = await asyncio.wait_for(
                    self.exit_stack.enter_async_context(sse_client(server_url)),
                    timeout=30.0  # 30 second timeout
                )
                print("Step 2: SSE transport created successfully")
            except asyncio.TimeoutError:
                raise Exception("Timeout while connecting to SSE endpoint. Server may not be responding.")
            
            read, write = sse_transport
            print("Step 3: Got read/write streams from SSE transport")
            
            print("Step 4: Creating MCP ClientSession...")
            self.session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            print("Step 5: ClientSession created successfully")

            print("Step 6: Initializing MCP session...")
            try:
                await asyncio.wait_for(self.session.initialize(), timeout=15.0)
                print("Step 7: MCP session initialized successfully")
            except asyncio.TimeoutError:
                raise Exception("Timeout during MCP session initialization")

            # List available tools
            print("Step 8: Listing available tools...")
            try:
                response = await asyncio.wait_for(self.session.list_tools(), timeout=10.0)
                tools = response.tools
                print(f"Step 9: Successfully retrieved {len(tools)} tools")
                print("\nConnected to server with tools:", [tool.name for tool in tools])
            except asyncio.TimeoutError:
                raise Exception("Timeout while listing tools")
            
        except Exception as e:
            print(f"Failed to connect to remote MCP server: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            print("Make sure the MCP server is running and accessible at the specified URL")
            raise

    def _convert_mcp_tools_to_gemini(self, mcp_tools: List) -> List[Dict[str, Any]]:
        """Convert MCP tools to Gemini function calling format"""
        gemini_tools = []
        
        for tool in mcp_tools:
            # Clean the input schema to remove unsupported fields
            parameters = self._clean_schema_for_gemini(tool.inputSchema)
            
            function_declaration = {
                "name": tool.name,
                "description": tool.description,
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

    def _extract_content_from_mcp_result(self, result) -> str:
        """Extract text content from MCP result object"""
        if hasattr(result, 'content'):
            content = result.content
            
            # Handle list of content items
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if hasattr(item, 'text'):
                        text_parts.append(item.text)
                    elif hasattr(item, 'type') and item.type == 'text' and hasattr(item, 'text'):
                        text_parts.append(item.text)
                    else:
                        text_parts.append(str(item))
                return "\n".join(text_parts)
            
            # Handle single content item
            elif hasattr(content, 'text'):
                return content.text
            elif hasattr(content, 'type') and content.type == 'text' and hasattr(content, 'text'):
                return content.text
            else:
                return str(content)
        
        # Fallback to string representation
        return str(result)

    async def process_query(self, query: str) -> str:
        """Process a query using Gemini and available tools"""
        # Get available tools
        response = await self.session.list_tools()
        mcp_tools = response.tools
        
        # Convert to Gemini format
        gemini_tools = self._convert_mcp_tools_to_gemini(mcp_tools)
        
        # Create chat session (tools are passed to generate_content/send_message instead)
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
                        result = await self.session.call_tool(tool_name, tool_args)
                        final_text.append(f"[Calling remote tool {tool_name} with args {tool_args}]")
                        
                        # Extract content from MCP result
                        result_content = self._extract_content_from_mcp_result(result)
                        
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
        print("\nMCP Gemini Remote Client Started!")
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
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python client_gemini_remote.py <server_url>")
        print("Example: python client_gemini_remote.py http://localhost:3000/sse")
        print("Note: Make sure to set GEMINI_API_KEY environment variable")
        sys.exit(1)

    server_url = sys.argv[1]
    client = MCPGeminiRemoteClient()
    try:
        await client.connect_to_server(server_url)
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())
