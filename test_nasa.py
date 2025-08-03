#!/usr/bin/env python3
"""
Test script for NASA MCP components

This script tests:
1. NASA MCP Server directly (stdio)
2. NASA HTTP Server Wrapper
3. Basic functionality of all tools
"""

import asyncio
import json
import subprocess
import sys
import time
import httpx
from pathlib import Path

def find_project_root():
    """Find the project root directory"""
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return Path.cwd()

async def test_nasa_server_direct():
    """Test NASA MCP server directly via stdio"""
    print("🧪 Testing NASA MCP Server (direct)...")
    
    project_root = find_project_root()
    server_script = project_root / "mcp-server" / "nasa_server.py"
    
    if not server_script.exists():
        print(f"❌ Server script not found: {server_script}")
        return False
    
    try:
        # Start server process
        process = subprocess.Popen(
            [sys.executable, str(server_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(project_root / "mcp-server")
        )
        
        # Send initialization
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Read response
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            if "result" in response:
                print("✅ NASA MCP Server initialization successful")
                
                # Test tool listing
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list"
                }
                
                process.stdin.write(json.dumps(tools_request) + "\n")
                process.stdin.flush()
                
                tools_response = process.stdout.readline()
                if tools_response:
                    tools_data = json.loads(tools_response.strip())
                    if "result" in tools_data:
                        tools = tools_data["result"]["tools"]
                        print(f"✅ Found {len(tools)} tools:")
                        for tool in tools:
                            print(f"   • {tool['name']}: {tool['description']}")
                        
                        process.terminate()
                        return True
        
        process.terminate()
        print("❌ Failed to communicate with NASA MCP Server")
        return False
        
    except Exception as e:
        print(f"❌ Error testing NASA MCP Server: {e}")
        return False

async def test_nasa_http_server():
    """Test NASA HTTP server wrapper"""
    print("\n🧪 Testing NASA HTTP Server Wrapper...")
    
    server_url = "http://localhost:8001"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test health endpoint
            health_response = await client.get(f"{server_url}/health")
            if health_response.status_code == 200:
                print("✅ NASA HTTP Server health check passed")
            else:
                print(f"❌ Health check failed: {health_response.status_code}")
                return False
            
            # Test tools listing
            tools_response = await client.get(f"{server_url}/tools")
            if tools_response.status_code == 200:
                tools_data = tools_response.json()
                if "result" in tools_data:
                    tools = tools_data["result"]["tools"]
                    print(f"✅ HTTP Server tools endpoint working ({len(tools)} tools)")
                else:
                    print("❌ Invalid tools response format")
                    return False
            else:
                print(f"❌ Tools endpoint failed: {tools_response.status_code}")
                return False
            
            # Test APOD tool
            apod_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "get_astronomy_picture_of_the_day",
                    "arguments": {}
                },
                "id": 1
            }
            
            apod_response = await client.post(f"{server_url}/call", json=apod_request)
            if apod_response.status_code == 200:
                apod_data = apod_response.json()
                if "result" in apod_data:
                    print("✅ APOD tool call successful")
                    content = apod_data["result"]["content"]
                    if content and len(content[0]["text"]) > 100:
                        print("✅ APOD returned substantial content")
                    else:
                        print("⚠️  APOD returned minimal content")
                else:
                    print(f"❌ APOD call failed: {apod_data}")
                    return False
            else:
                print(f"❌ APOD call HTTP error: {apod_response.status_code}")
                return False
            
            print("✅ NASA HTTP Server wrapper working correctly")
            return True
            
    except httpx.ConnectError:
        print("❌ Cannot connect to NASA HTTP Server")
        print("   Make sure the server is running: python nasa_demo.py --server-only")
        return False
    except Exception as e:
        print(f"❌ Error testing NASA HTTP Server: {e}")
        return False

def test_gui_dependencies():
    """Test GUI client dependencies"""
    print("\n🧪 Testing GUI Dependencies...")
    
    try:
        import tkinter as tk
        print("✅ Tkinter available")
        
        # Test if we can create a root window
        root = tk.Tk()
        root.withdraw()  # Hide the window
        root.destroy()
        print("✅ Tkinter window creation works")
        
    except ImportError:
        print("❌ Tkinter not available")
        return False
    except Exception as e:
        print(f"❌ Tkinter error: {e}")
        return False
    
    try:
        from PIL import Image, ImageTk
        print("✅ Pillow (PIL) available")
    except ImportError:
        print("❌ Pillow (PIL) not available")
        return False
    
    try:
        import httpx
        print("✅ HTTPX available")
    except ImportError:
        print("❌ HTTPX not available")
        return False
    
    print("✅ All GUI dependencies available")
    return True

async def main():
    """Run all tests"""
    print("🚀 NASA MCP Component Tests")
    print("=" * 40)
    
    # Test dependencies
    deps_ok = test_gui_dependencies()
    
    # Test direct server
    server_ok = await test_nasa_server_direct()
    
    # Test HTTP server (may not be running)
    print("\n💡 Testing HTTP server (start with: python nasa_demo.py --server-only)")
    http_ok = await test_nasa_http_server()
    
    print("\n📊 Test Results:")
    print(f"   Dependencies: {'✅' if deps_ok else '❌'}")
    print(f"   NASA MCP Server: {'✅' if server_ok else '❌'}")
    print(f"   NASA HTTP Server: {'✅' if http_ok else '❌'}")
    
    if deps_ok and server_ok:
        print("\n🎉 Core NASA MCP components are working!")
        if not http_ok:
            print("💡 To test the full system, run: python nasa_demo.py")
    else:
        print("\n❌ Some components have issues")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(result)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted")
        sys.exit(1)
