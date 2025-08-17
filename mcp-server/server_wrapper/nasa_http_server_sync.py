#!/usr/bin/env python3
"""
NASA MCP HTTP Server Wrapper

Wraps the NASA MCP server to provide HTTP access via REST API.
This allows remote clients to access NASA MCP tools over HTTP.
"""

import asyncio
import json
import subprocess
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
from typing import Dict, Any, Optional
import os

class MCPServerWrapper:
    """Manages the MCP server subprocess and handles communication"""
    
    def __init__(self, server_script_path: str):
        self.server_script_path = os.path.abspath(server_script_path)
        self.process = None
        self.request_id = 0
        
    def start_server(self):
        """Start the MCP server subprocess"""
        print(f"Starting NASA MCP server: {self.server_script_path}")
        
        try:
            self.process = subprocess.Popen(
                [sys.executable, self.server_script_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            # Initialize the MCP session
            self._send_initialize()
            print("✓ NASA MCP server initialized")
            
        except Exception as e:
            print(f"Failed to start MCP server: {e}")
            raise
    
    def _send_initialize(self):
        """Send initialization message to MCP server"""
        self.request_id += 1
        init_message = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "nasa-http-wrapper",
                    "version": "1.0.0"
                }
            },
            "id": self.request_id
        }
        
        response = self._send_message(init_message)
        if "error" in response:
            raise Exception(f"Failed to initialize: {response['error']}")
        
        # Send initialized notification
        initialized_message = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        self._send_message(initialized_message, expect_response=False)
    
    def _send_message(self, message: Dict[str, Any], expect_response: bool = True) -> Optional[Dict[str, Any]]:
        """Send a message to the MCP server and get response"""
        if not self.process:
            raise Exception("MCP server not started")
        
        try:
            # Send message
            message_str = json.dumps(message)
            print(f"Sending to NASA MCP server: {message_str}")
            
            self.process.stdin.write(message_str + "\n")
            self.process.stdin.flush()
            
            if not expect_response:
                return None
            
            # Read response
            response_line = self.process.stdout.readline()
            if not response_line:
                raise Exception("No response from MCP server")
            
            response = json.loads(response_line.strip())
            print(f"Got response from NASA MCP server: {response}")
            
            return response
            
        except Exception as e:
            print(f"Error communicating with MCP server: {e}")
            if self.process and self.process.stderr:
                stderr_output = self.process.stderr.read()
                if stderr_output:
                    print(f"MCP server stderr: {stderr_output}")
            raise
    
    def call_tool(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP method"""
        self.request_id += 1
        message = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self.request_id
        }
        
        return self._send_message(message)
    
    def stop_server(self):
        """Stop the MCP server"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None

class NASAHTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for NASA MCP server"""
    
    def __init__(self, *args, mcp_wrapper=None, **kwargs):
        self.mcp_wrapper = mcp_wrapper
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == "/":
            # Status endpoint
            self._send_json_response({
                "message": "NASA MCP HTTP Server is running",
                "endpoints": {
                    "status": "GET /",
                    "call_tool": "POST /call",
                    "list_tools": "GET /tools"
                }
            })
        elif parsed_path.path == "/tools":
            # List tools endpoint
            try:
                response = self.mcp_wrapper.call_tool("tools/list", {})
                self._send_json_response(response)
            except Exception as e:
                self._send_error_response(500, f"Error listing tools: {str(e)}")
        else:
            self._send_error_response(404, "Not found")
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == "/call":
            try:
                # Read request body
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data.decode('utf-8'))
                
                # Forward to MCP server
                response = self.mcp_wrapper.call_tool(
                    request_data.get("method", ""),
                    request_data.get("params", {})
                )
                
                self._send_json_response(response)
                
            except json.JSONDecodeError:
                self._send_error_response(400, "Invalid JSON")
            except Exception as e:
                self._send_error_response(500, f"Error processing request: {str(e)}")
        else:
            self._send_error_response(404, "Not found")
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self._send_cors_headers()
        self.end_headers()
    
    def _send_json_response(self, data: Dict[str, Any], status_code: int = 200):
        """Send JSON response"""
        self.send_response(status_code)
        self._send_cors_headers()
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response_json = json.dumps(data, indent=2)
        self.wfile.write(response_json.encode())
    
    def _send_error_response(self, status_code: int, message: str):
        """Send error response"""
        self._send_json_response({
            "error": {
                "code": status_code,
                "message": message
            }
        }, status_code)
    
    def _send_cors_headers(self):
        """Send CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def log_message(self, format, *args):
        """Override to reduce log noise"""
        return

def create_handler(mcp_wrapper):
    """Create request handler with MCP wrapper"""
    def handler(*args, **kwargs):
        return NASAHTTPRequestHandler(*args, mcp_wrapper=mcp_wrapper, **kwargs)
    return handler

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="NASA MCP HTTP Server Wrapper")
    parser.add_argument("--port", type=int, default=8001, help="HTTP server port (default: 8001)")
    parser.add_argument("--server", default="nasa_server.py", help="MCP server script path (default: nasa_server.py)")
    
    args = parser.parse_args()
    
    # Find the NASA server script
    if not os.path.isabs(args.server):
        # Look for the script relative to this wrapper's location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        server_script = os.path.join(project_root, "mcp-server", args.server)
    else:
        server_script = args.server
    
    if not os.path.exists(server_script):
        print(f"❌ NASA server script not found: {server_script}")
        sys.exit(1)
    
    port = args.port
    
    # Create MCP wrapper
    mcp_wrapper = MCPServerWrapper(server_script)
    
    try:
        # Start MCP server
        mcp_wrapper.start_server()
        
        # Create HTTP server
        handler = create_handler(mcp_wrapper)
        httpd = HTTPServer(('localhost', port), handler)
        
        print(f"Starting NASA HTTP server on port {port}")
        print(f"Server URL: http://localhost:{port}")
        print("Endpoints:")
        print(f"  Status: GET http://localhost:{port}/")
        print(f"  List tools: GET http://localhost:{port}/tools")
        print(f"  Call tool: POST http://localhost:{port}/call")
        print("\nPress Ctrl+C to stop")
        
        # Start HTTP server
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up
        try:
            mcp_wrapper.stop_server()
        except:
            pass
        print("Server stopped")

if __name__ == "__main__":
    main()
