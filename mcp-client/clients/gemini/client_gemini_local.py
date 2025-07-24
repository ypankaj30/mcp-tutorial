import asyncio
import json
import time
from typing import Optional, List, Dict, Any
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()  # load environment variables from .env

# This MCP client is all Gemini-specific.

class MCPGeminiClient:
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

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )
        print(f"Connecting to MCP server using command: {command} {server_script_path}")

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        print("\nConnected to MCP server. Initializing session...")
        await self.session.initialize()

        # List available tools
        print("\nListing available tools...")
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

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

    def _build_chat_history(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert messages to Gemini chat history format"""
        chat_history = []
        
        for message in messages:
            if message["role"] == "user":
                chat_history.append({
                    "role": "user",
                    "parts": [{"text": message["content"]}]
                })
            elif message["role"] == "assistant":
                # Handle assistant messages with potential function calls
                parts = []
                if isinstance(message["content"], list):
                    for content in message["content"]:
                        if hasattr(content, 'type'):
                            if content.type == 'text':
                                parts.append({"text": content.text})
                            elif content.type == 'tool_use':
                                parts.append({
                                    "function_call": {
                                        "name": content.name,
                                        "args": content.input
                                    }
                                })
                        elif isinstance(content, dict):
                            if content.get("type") == "text":
                                parts.append({"text": content["text"]})
                else:
                    parts.append({"text": message["content"]})
                
                if parts:
                    chat_history.append({
                        "role": "model",
                        "parts": parts
                    })
        
        return chat_history

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
                        # Execute tool call
                        result = await self.session.call_tool(tool_name, tool_args)
                        final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")
                        
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
                        final_text.append(f"Error executing tool {tool_name}: {str(e)}")
        
        return "\n".join(final_text) if final_text else "No response received"

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Gemini Client Started!")
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
        print("Usage: python client_gemini.py <path_to_server_script>")
        print("Note: Make sure to set GEMINI_API_KEY environment variable")
        sys.exit(1)

    client = MCPGeminiClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())
