#!/usr/bin/env python3
"""
Simple HTTP MCP Server Wrapper (Synchronous Version)
This script wraps an existing MCP server and exposes it via simple HTTP endpoints.
Uses synchronous subprocess communication to avoid event loop conflicts.
"""

import subprocess
import sys
import json
import signal
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import queue
import time
import os

class SimpleMCPServerWrapper:
    def __init__(self, server_script_path: str):
        self.server_script_path = server_script_path
        self.process = None
        self.running = False
        
    def start_server(self):
        """Start the MCP server as a subprocess"""
        print(f"Starting MCP server: {self.server_script_path}")
        
        # Use uv run if available, otherwise fall back to python
        if os.system("which uv > /dev/null 2>&1") == 0:
            command = ["uv", "run", self.server_script_path]
        else:
            command = ["python", self.server_script_path]
            
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        self.running = True
        
        # Initialize the MCP server
        init_response = self.send_message({
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "http-wrapper",
                    "version": "1.0.0"
                }
            },
            "id": 1
        })
        
        if "error" in init_response:
            raise Exception(f"Failed to initialize MCP server: {init_response['error']}")
        
        print("✓ MCP server initialized")
        
    def send_message(self, message: dict) -> dict:
        """Send a message to the MCP server and get response (synchronous)"""
        if not self.running or not self.process:
            raise RuntimeError("Server not started")
            
        try:
            print(f"Sending to MCP server: {json.dumps(message)}")
            
            # Send message to server
            message_json = json.dumps(message) + "\n"
            self.process.stdin.write(message_json)
            self.process.stdin.flush()
            
            # Read response with timeout using select (Unix-like systems)
            import select
            ready, _, _ = select.select([self.process.stdout], [], [], 10.0)  # 10 second timeout
            
            if not ready:
                raise RuntimeError("MCP server response timeout")
            
            response_line = self.process.stdout.readline()
            if not response_line:
                raise RuntimeError("Server closed connection")
            
            print(f"Got response from MCP server: {response_line.strip()}")
            return json.loads(response_line.strip())
            
        except Exception as e:
            print(f"Error in send_message: {e}")
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e)
                },
                "id": message.get("id")
            }
    
    def stop_server(self):
        """Stop the MCP server"""
        self.running = False
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

# Global server wrapper
server_wrapper = None

class SimpleMCPHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                "message": "MCP HTTP Server is running",
                "endpoints": {
                    "status": "GET /",
                    "call_tool": "POST /call"
                }
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == "/call":
            try:
                print(f"Received POST request to /call")
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data.decode())
                
                print(f"Request data: {json.dumps(request_data, indent=2)}")
                
                # Send to MCP server (synchronous)
                response = server_wrapper.send_message(request_data)
                
                print(f"Sending HTTP response: {json.dumps(response, indent=2)}")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                print(f"Error in POST handler: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    },
                    "id": request_data.get("id", None) if 'request_data' in locals() else None
                }
                self.wfile.write(json.dumps(error_response).encode())
        else:
            self.send_error(404)
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Override to reduce log noise"""
        if "POST /call" in format % args:
            print(f"MCP call: {args[0]}")

def main():
    global server_wrapper
    
    if len(sys.argv) < 2:
        print("Usage: python mcp_http_server.py <path_to_mcp_server.py> [port]")
        print("Example: python mcp_http_server.py ../weather/weather.py 8000")
        sys.exit(1)
    
    server_script = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    
    # Start MCP server wrapper
    server_wrapper = SimpleMCPServerWrapper(server_script)
    
    try:
        server_wrapper.start_server()
        
        # Start HTTP server
        print(f"Starting HTTP server on port {port}")
        print(f"Server URL: http://localhost:{port}")
        print("Endpoints:")
        print(f"  Status: GET http://localhost:{port}/")
        print(f"  MCP calls: POST http://localhost:{port}/call")
        print("\nPress Ctrl+C to stop")
        
        httpd = HTTPServer(('', port), SimpleMCPHTTPHandler)
        
        def signal_handler(sig, frame):
            print("\nShutting down...")
            httpd.shutdown()
        
        signal.signal(signal.SIGINT, signal_handler)
        httpd.serve_forever()
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if server_wrapper:
            server_wrapper.stop_server()

if __name__ == "__main__":
    main()
