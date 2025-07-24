# MCP Tutorial Project

A comprehensive tutorial project demonstrating Model Context Protocol (MCP) implementations with both client and server components, supporting multiple AI models and deployment patterns.

## 📁 Project Structure

```
mcp-tutorial/
├── .git/                      # Git repository (unified)
├── .gitignore                 # Git ignore rules (unified)
├── .venv/                     # Unified virtual environment
├── .env                       # Environment variables (API keys)
├── pyproject.toml            # Unified dependencies and configuration
├── setup.sh                  # Quick setup script
├── README.md                 # This comprehensive guide
├── mcp-client/               # MCP clients for different AI models
│   ├── clients/
│   │   ├── anthropic/        # Claude MCP clients
│   │   └── gemini/          # Google Gemini MCP clients
│   ├── server_wrapper/      # HTTP server wrappers
│   ├── utils/              # Debugging tools
│   └── docs/               # Client-specific documentation
└── mcp-server/             # MCP server implementations
    ├── weather_server.py   # Weather data MCP server
    └── main.py            # Main server entry point
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** with `uv` package manager installed
2. **API Keys**:
   - **Gemini**: Get from [Google AI Studio](https://aistudio.google.com/)
   - **Anthropic**: Get from [Anthropic Console](https://console.anthropic.com/)

### Environment Setup

#### Quick Setup (Recommended)

```bash
cd mcp-tutorial
./setup.sh
```

#### Manual Setup

```bash
# Clone and navigate to project
cd mcp-tutorial

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate     # On Windows

# Install all dependencies from unified pyproject.toml
uv pip install -e .

# Optional: Install development dependencies
uv pip install -e ".[dev]"
```

### Environment Variables

Create a `.env` file in the root `mcp-tutorial` directory:

```bash
# .env file (in mcp-tutorial root directory)
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## 🔧 Available Implementations

### MCP Clients

#### Local Clients (stdio connection)
- **Gemini Local**: `clients/gemini/client_gemini.py`
- **Anthropic Local**: `clients/anthropic/client.py`

#### Remote Clients (HTTP/SSE connection)
- **Gemini HTTP**: `clients/gemini/client_gemini_http.py`
- **Gemini SSE**: `clients/gemini/client_gemini_remote.py`

#### Server Wrappers
- **Sync HTTP Wrapper**: `server_wrapper/mcp_http_server_sync.py` (recommended)
- **Async HTTP Wrapper**: `server_wrapper/mcp_http_server_async.py`
- **SSE Wrapper**: `server_wrapper/mcp_server_remote.py`

#### Utilities
- **Debug Tool**: `utils/debug_mcp.py` - MCP protocol debugging and testing

### MCP Servers

- **Weather Server**: `mcp-server/weather_server.py` - Provides weather data and alerts

## 🎯 Usage Examples

### 1. Local Gemini Client with Weather Server

```bash
# From mcp-tutorial root with activated virtual environment
cd mcp-client/clients/gemini
uv run python client_gemini_local.py ../../../mcp-server/weather_server.py
```

### 2. Remote HTTP Setup

```bash
# Terminal 1: Start HTTP server wrapper (from mcp-tutorial root)
cd mcp-client/server_wrapper
uv run python mcp_http_server_sync_remote.py ../../mcp-server/weather_server.py 8000

# Terminal 2: Connect with HTTP client (from mcp-tutorial root)
cd mcp-client/clients/gemini
uv run python client_gemini_http_remote.py http://localhost:8000
```

### 3. Remote SSE Setup

```bash
# Terminal 1: Start SSE server wrapper (from mcp-tutorial root)
cd mcp-client/server_wrapper
uv run python mcp_sse_server_remote.py ../../mcp-server/weather_server.py 8000

# Terminal 2: Connect with SSE client (from mcp-tutorial root)
cd mcp-client/clients/gemini
uv run python client_gemini_sse_remote.py http://localhost:8000/sse
```

### 4. Debug MCP Communication

```bash
# From mcp-tutorial root
cd mcp-client/utils
uv run python debug_mcp.py http://localhost:8000
```

### 2. Remote HTTP Setup

```bash
# Terminal 1: Start HTTP server wrapper
cd mcp-client/server_wrapper
uv run python mcp_http_server_sync.py ../mcp-server/weather_server.py 8000

# Terminal 2: Connect with HTTP client
cd ../clients/gemini
uv run python client_gemini_http.py http://localhost:8000
```

### 3. Remote SSE Setup

```bash
# Terminal 1: Start SSE server wrapper
cd mcp-client/server_wrapper
uv run python mcp_server_remote.py ../mcp-server/weather_server.py 8000

# Terminal 2: Connect with SSE client
cd ../clients/gemini
uv run python client_gemini_remote.py http://localhost:8000/sse
```

### 4. Debug MCP Communication

```bash
cd mcp-client/utils
uv run python debug_mcp.py http://localhost:8000
```

## 🔧 API Configuration

### Gemini Setup

1. **Get API Key**: Visit [Google AI Studio](https://aistudio.google.com/)
2. **Dependencies**: All dependencies are included in the unified `pyproject.toml`
3. **Key Features**:
   - Uses `gemini-1.5-flash` model (better free tier limits)
   - Automatic retry logic with exponential backoff
   - Converts between MCP and Gemini message formats
   - Full function calling support

### Anthropic Setup

1. **Get API Key**: Visit [Anthropic Console](https://console.anthropic.com/)
2. **Dependencies**: All dependencies are included in the unified `pyproject.toml`

## 🏗️ Architecture Patterns

### Local Architecture (stdio)
```
┌─────────────────┐    stdio     ┌─────────────────┐
│ AI Client       │ ◄──────────► │ MCP Server      │
│ (Gemini/Claude) │              │ (Weather)       │
└─────────────────┘              └─────────────────┘
```

### Remote Architecture (HTTP/SSE)
```
┌─────────────────┐    HTTP/SSE   ┌─────────────────┐    stdio    ┌─────────────────┐
│ AI Client       │ ◄───────────► │ Server Wrapper  │ ◄─────────► │ MCP Server      │
│ (Gemini/Claude) │               │ (Port 8000)     │             │ (Weather)       │
└─────────────────┘               └─────────────────┘             └─────────────────┘
```

## 🛠️ Development Features

### Client Features
- ✅ Multiple AI model support (Gemini, Claude)
- ✅ Local and remote connection modes
- ✅ Function calling support
- ✅ Interactive chat loops
- ✅ Error handling and retry logic
- ✅ Multi-turn conversations with tool usage
- ✅ Rate limiting and backoff strategies

### Server Features
- ✅ Weather data and alerts
- ✅ RESTful API endpoints
- ✅ MCP protocol compliance
- ✅ Error handling
- ✅ Extensible architecture

### Wrapper Features
- ✅ HTTP and SSE transport protocols
- ✅ CORS support for web access
- ✅ Multiple client support
- ✅ Network debugging capabilities
- ✅ Language-agnostic HTTP interface

## 🔍 Testing the Setup

### Test Server Status
```bash
curl http://localhost:8000/
```

### Test MCP Call Directly
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

### Interactive Testing
Ask questions like:
- "What are the weather alerts for California?"
- "Get current weather for New York"
- "List all available tools"

## 🛡️ Security Considerations

### Development
- HTTP wrappers have no authentication by default
- Only run on localhost or trusted networks
- Use environment variables for API keys

### Production
- Add API authentication (keys/tokens)
- Use HTTPS for remote connections
- Implement rate limiting
- Add input validation and sanitization
- Monitor and log all requests

## 🐛 Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure server wrapper is running on correct port
   - Check firewall settings

2. **API Key Issues**
   - Verify API keys are set correctly in `.env`
   - Check API key permissions and quotas

3. **Import Errors**
   - All dependencies are managed in the unified `pyproject.toml`
   - Ensure virtual environment is activated from mcp-tutorial root
   - Run `uv pip install -e .` if packages are missing

4. **Rate Limits**
   - Both Gemini and Claude have rate limits
   - Client includes automatic retry logic
   - Add delays if needed for heavy usage

5. **MCP Server Issues**
   - Check server wrapper logs for MCP communication errors
   - Verify server script paths are correct
   - Ensure server script is executable

6. **CORS Issues**
   - Server includes CORS headers for web browser access
   - Check browser console for specific CORS errors

## 📚 Additional Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [Google Generative AI Python SDK](https://github.com/google-gemini/generative-ai-python)
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)

## 🤝 Contributing

### Version Control Setup

This project uses a unified git repository at the root level:

```bash
# Initialize git repository (if cloning, this is already done)
git init

# Add and commit project files
git add .
git commit -m "Initial commit: MCP tutorial project"

# The .gitignore automatically excludes:
# - Virtual environments (.venv/)
# - Environment files (.env)
# - Python cache files (__pycache__/)
# - Build artifacts (*.egg-info/, dist/, build/)
# - IDE files (.vscode/, .idea/)
# - OS-specific files (.DS_Store, Thumbs.db)
# - Logs and temporary files
```

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with both local and remote setups
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.
