#!/usr/bin/env python3
"""
Debug script to test MCP HTTP server communication
"""

import json
import httpx
import asyncio

async def test_mcp_server(server_url: str):
    """Test MCP server endpoints"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        print(f"Testing MCP server at: {server_url}")
        
        # Test 1: Check if server is running
        print("\n1. Testing server status...")
        try:
            response = await client.get(f"{server_url}/")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")
            return
        
        # Test 2: Try to initialize
        print("\n2. Testing initialize...")
        init_message = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "debug-client",
                    "version": "1.0.0"
                }
            },
            "id": 1
        }
        
        try:
            response = await client.post(f"{server_url}/call", json=init_message)
            result = response.json()
            print(f"Initialize response: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"Initialize error: {e}")
            return
        
        # Test 3: Try different ways to list tools
        print("\n3. Testing tools/list with different formats...")
        
        # Format 1: With empty params
        tools_message_1 = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        }
        
        try:
            response = await client.post(f"{server_url}/call", json=tools_message_1)
            result = response.json()
            print(f"tools/list (with params): {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"tools/list (with params) error: {e}")
        
        # Format 2: Without params
        tools_message_2 = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 3
        }
        
        try:
            response = await client.post(f"{server_url}/call", json=tools_message_2)
            result = response.json()
            print(f"tools/list (no params): {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"tools/list (no params) error: {e}")
        
        # Format 3: Try list_tools instead
        tools_message_3 = {
            "jsonrpc": "2.0",
            "method": "list_tools",
            "id": 4
        }
        
        try:
            response = await client.post(f"{server_url}/call", json=tools_message_3)
            result = response.json()
            print(f"list_tools: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"list_tools error: {e}")
        
        # Format 4: Try with null params
        tools_message_4 = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": None,
            "id": 5
        }
        
        try:
            response = await client.post(f"{server_url}/call", json=tools_message_4)
            result = response.json()
            print(f"tools/list (null params): {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"tools/list (null params) error: {e}")
        
        # Format 5: Try initialized notification first, then tools/list
        print("\n4. Sending initialized notification first...")
        initialized_message = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        try:
            response = await client.post(f"{server_url}/call", json=initialized_message)
            print(f"✓ Sent initialized notification, response: {response.status_code}")
            
            # Wait a moment for the notification to be processed
            await asyncio.sleep(0.1)
            
            # Now try tools/list again
            tools_message_5 = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 6
            }
            
            response = await client.post(f"{server_url}/call", json=tools_message_5)
            result = response.json()
            print(f"tools/list (after initialized): {json.dumps(result, indent=2)}")
            
        except Exception as e:
            print(f"After initialized error: {e}")
        
        # Test 6: Try with completely different method names
        print("\n5. Testing alternative method names...")
        
        # Try resources/list (another MCP method)
        resources_message = {
            "jsonrpc": "2.0",
            "method": "resources/list",
            "params": {},
            "id": 7
        }
        
        try:
            response = await client.post(f"{server_url}/call", json=resources_message)
            result = response.json()
            print(f"resources/list: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"resources/list error: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python debug_mcp.py <server_url>")
        print("Example: python debug_mcp.py http://localhost:8000")
        sys.exit(1)
    
    server_url = sys.argv[1]
    asyncio.run(test_mcp_server(server_url))
