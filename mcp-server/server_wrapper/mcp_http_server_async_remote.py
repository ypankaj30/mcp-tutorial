#!/usr/bin/env python3
"""
Simple HTTP MCP Server Wrapper
This script wraps an existing MCP server and exposes it via simple HTTP endpoints.
"""

import asyncio
import subprocess
import sys
import json
import signal
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import queue
import time

class MCPServerWrapper:
    def __init__(self, server_script_path: str):
        self.server_script_path = server_script_path
        self.process = None
        self.request_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.running = False
        
    async def start_server(self):
        """Start the MCP server as a subprocess"""
        print(f"Starting MCP server: {self.server_script_path}")
        self.process = await asyncio.create_subprocess_exec(
            "python", self.server_script_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        self.running = True
        
        # Start the communication thread
        self.comm_thread = threading.Thread(target=self._communication_loop)
        self.comm_thread.daemon = True
        self.comm_thread.start()
        
        # Initialize the MCP server
        await self.send_message({
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
        print("✓ MCP server initialized")
        
    def _communication_loop(self):
        """Handle communication with MCP server in a separate thread"""
        while self.running:
            try:
                # Check for requests to send
                try:
                    message = self.request_queue.get(timeout=0.1)
                    if message is None:  # Shutdown signal
                        break
                        
                    # Send to MCP server
                    message_json = json.dumps(message) + "\n"
                    self.process.stdin.write(message_json.encode())
                    
                    # Read response
                    response_line = self.process.stdout.readline()
                    if response_line:
                        response = json.loads(response_line.decode())
                        self.response_queue.put(response)
                    else:
                        self.response_queue.put({"error": "Server closed connection"})
                        
                except queue.Empty:
                    continue
                except Exception as e:
                    self.response_queue.put({"error": str(e)})
                    
            except Exception as e:
                print(f"Communication error: {e}")
                break
        
    async def send_message(self, message: dict) -> dict:
        """Send a message to the MCP server and get response"""
        if not self.running:
            raise RuntimeError("Server not started")
            
        # Put request in queue
        self.request_queue.put(message)
        
        # Wait for response (with timeout)
        start_time = time.time()
        while time.time() - start_time < 10:  # 10 second timeout
            try:
                response = self.response_queue.get(timeout=0.1)
                return response
            except queue.Empty:
                continue
                
        raise TimeoutError("No response from MCP server")
    
    async def stop_server(self):
        """Stop the MCP server"""
        self.running = False
        if hasattr(self, 'comm_thread'):
            self.request_queue.put(None)  # Shutdown signal
            self.comm_thread.join(timeout=2)
            
        if self.process:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=3)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()

# Global server wrapper
server_wrapper = None

class MCPHTTPHandler(BaseHTTPRequestHandler):
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
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data.decode())
                
                # Send to MCP server using asyncio.run_coroutine_threadsafe
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    response = loop.run_until_complete(server_wrapper.send_message(request_data))
                finally:
                    loop.close()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
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

async def main():
    global server_wrapper
    
    if len(sys.argv) < 2:
        print("Usage: python mcp_http_server.py <path_to_mcp_server.py> [port]")
        print("Example: python mcp_http_server.py ../weather/weather.py 8000")
        sys.exit(1)
    
    server_script = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    
    # Start MCP server wrapper
    server_wrapper = MCPServerWrapper(server_script)
    
    try:
        await server_wrapper.start_server()
        
        # Start HTTP server
        print(f"Starting HTTP server on port {port}")
        print(f"Server URL: http://localhost:{port}")
        print("Endpoints:")
        print(f"  Status: GET http://localhost:{port}/")
        print(f"  MCP calls: POST http://localhost:{port}/call")
        print("\nPress Ctrl+C to stop")
        
        httpd = HTTPServer(('', port), MCPHTTPHandler)
        
        def signal_handler(sig, frame):
            print("\nShutting down...")
            httpd.shutdown()
        
        signal.signal(signal.SIGINT, signal_handler)
        httpd.serve_forever()
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if server_wrapper:
            await server_wrapper.stop_server()

if __name__ == "__main__":
    asyncio.run(main())
