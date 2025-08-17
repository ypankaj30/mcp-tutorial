#!/usr/bin/env python3
"""
Remote MCP Server Wrapper
This script wraps an existing MCP server and exposes it via HTTP/SSE for remote access.
"""

import asyncio
import subprocess
import sys
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import uvicorn
import json
from typing import AsyncGenerator

class MCPServerWrapper:
    def __init__(self, server_script_path: str):
        self.server_script_path = server_script_path
        self.process = None
        
    async def start_server(self):
        """Start the MCP server as a subprocess"""
        self.process = await asyncio.create_subprocess_exec(
            "python", self.server_script_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
    async def send_message(self, message: dict) -> dict:
        """Send a message to the MCP server and get response"""
        if not self.process:
            raise RuntimeError("Server not started")
            
        # Send message to server
        message_json = json.dumps(message) + "\n"
        self.process.stdin.write(message_json.encode())
        await self.process.stdin.drain()
        
        # Read response
        response_line = await self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("Server closed connection")
            
        return json.loads(response_line.decode())
    
    async def stop_server(self):
        """Stop the MCP server"""
        if self.process:
            self.process.terminate()
            await self.process.wait()

# Global server wrapper
server_wrapper = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the lifecycle of the MCP server"""
    global server_wrapper
    
    if len(sys.argv) < 2:
        print("Usage: python mcp_server_remote.py <path_to_mcp_server.py>")
        sys.exit(1)
    
    server_script = sys.argv[1]
    server_wrapper = MCPServerWrapper(server_script)
    
    try:
        await server_wrapper.start_server()
        print(f"Started MCP server: {server_script}")
        yield
    finally:
        if server_wrapper:
            await server_wrapper.stop_server()
            print("Stopped MCP server")

# Create FastAPI app
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "MCP Remote Server is running", "endpoint": "/sse"}

@app.get("/sse")
async def sse_endpoint():
    """SSE endpoint for MCP communication"""
    
    async def generate_sse() -> AsyncGenerator[str, None]:
        try:
            # Initialize connection
            init_message = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "remote-client",
                        "version": "1.0.0"
                    }
                },
                "id": 1
            }
            
            response = await server_wrapper.send_message(init_message)
            yield f"data: {json.dumps(response)}\n\n"
            
            # Keep connection alive and handle incoming messages
            # This is a simplified implementation - a full implementation
            # would need to handle bidirectional communication properly
            
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e)
                },
                "id": None
            }
            yield f"data: {json.dumps(error_response)}\n\n"
    
    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )

@app.post("/call")
async def call_tool(request: dict):
    """HTTP endpoint for calling MCP tools"""
    try:
        response = await server_wrapper.send_message(request)
        return response
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": str(e)
            },
            "id": request.get("id")
        }

if __name__ == "__main__":
    print("Starting MCP Remote Server...")
    print("This will expose your MCP server via HTTP on port 8000")
    print("SSE endpoint: http://localhost:8000/sse")
    print("HTTP endpoint: http://localhost:8000/call")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
