# MCP Remote Client Setup

This directory contains different versions of MCP clients that can connect to remote MCP servers.

## Files Created:

### 1. `client_gemini_remote.py` - SSE-based Remote Client
- Connects to MCP servers via Server-Sent Events (SSE)
- Uses the official MCP SSE client
- Requires `mcp.client.sse` module

### 2. `client_gemini_http.py` - HTTP-based Remote Client  
- Connects to MCP servers via simple HTTP calls
- Uses `httpx` for HTTP communication
- Simpler implementation, easier to debug

### 3. `mcp_http_server.py` - HTTP Server Wrapper
- Wraps any existing MCP server to expose it via HTTP
- Simple HTTP endpoints for MCP communication
- No external dependencies beyond Python standard library

## Setup Instructions:

### Step 1: Install Additional Dependencies

```bash
# For HTTP client
uv add httpx

# For SSE client (if using the SSE version)
uv add mcp[sse]

# For FastAPI server wrapper (alternative)
uv add fastapi uvicorn
```

### Step 2: Start the Remote MCP Server

Option A - Using the simple HTTP wrapper (Recommended):
```bash
# In terminal 1 - Start the simple HTTP MCP server wrapper
cd /Users/pankajyawale/projects/llm-agents/mcp-client
python mcp_http_server_simple.py /Users/pankajyawale/projects/llm-agents/weather/weather.py 8000
```

Option B - Using uv run:
```bash
# In terminal 1 - Start the HTTP MCP server wrapper with uv
cd /Users/pankajyawale/projects/llm-agents/mcp-client
uv run mcp_http_server_simple.py /Users/pankajyawale/projects/llm-agents/weather/weather.py 8000
```

### Step 3: Connect with Remote Client

```bash
# In terminal 2 - Connect with HTTP client
cd /Users/pankajyawale/projects/llm-agents/mcp-client
uv run client_gemini_http.py http://localhost:8000
```

## Testing the Setup:

1. **Check server status:**
   ```bash
   curl http://localhost:8000/
   ```

2. **Test MCP call directly:**
   ```bash
   curl -X POST http://localhost:8000/call \
     -H "Content-Type: application/json" \
     -d '{
       "jsonrpc": "2.0",
       "method": "tools/list",
       "params": {},
       "id": 1
     }'
   ```

3. **Use the Gemini client:**
   - Run the client and ask: "What are the weather alerts for California?"
   - The client will call the remote weather server via HTTP

## Architecture:

```
┌─────────────────┐    HTTP     ┌─────────────────┐    stdio    ┌─────────────────┐
│ Gemini Client   │ ◄─────────► │ HTTP Wrapper    │ ◄─────────► │ MCP Server      │
│ (HTTP)          │             │ (Port 8000)     │             │ (Weather)       │
└─────────────────┘             └─────────────────┘             └─────────────────┘
```

## Benefits of Remote Setup:

1. **Separation of Concerns**: Client and server can run on different machines
2. **Scalability**: Multiple clients can connect to the same server
3. **Network Access**: Can be accessed from web browsers or remote machines
4. **Language Agnostic**: Any HTTP client can connect
5. **Debugging**: Easy to inspect HTTP traffic

## Security Considerations:

- The HTTP wrapper has no authentication
- Only run on localhost or trusted networks
- Consider adding API keys or tokens for production use
- Use HTTPS in production environments

## Troubleshooting:

1. **Connection Refused**: Make sure the HTTP server is running on the correct port
2. **MCP Server Issues**: Check the server wrapper logs for MCP communication errors
3. **Rate Limits**: The HTTP client includes the same rate limiting as the local client
4. **CORS Issues**: The server includes CORS headers for web browser access
