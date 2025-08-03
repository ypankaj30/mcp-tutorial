# NASA MCP Demo - Quick Start Guide

## 🚀 What We've Built

The NASA MCP Tutorial project now includes a complete NASA API integration with:

### 🌌 NASA MCP Server (`nasa_server.py`)
- **Astronomy Picture of the Day (APOD)** - Get NASA's daily space image with explanations
- **Mars Rover Photos** - Browse photos from Curiosity, Perseverance, and other rovers
- **Near Earth Objects (NEOs)** - Track asteroids and comets approaching Earth

### 🌐 HTTP Server Wrapper (`nasa_http_server_sync.py`)
- Exposes NASA MCP server via REST API
- Provides JSON-RPC over HTTP for remote access
- CORS enabled for web browser access

### 🖥️ Tkinter GUI Client (`nasa_gui_client.py`)
- User-friendly graphical interface
- Image viewing and downloading capabilities
- Tabbed interface for different NASA APIs
- Real-time data fetching and display

## 🎯 Quick Start

### Option 1: Complete Demo (Server + GUI)
```bash
cd /Users/pankajyawale/projects/mcp/mcp-tutorial
python nasa_demo.py
```

### Option 2: Server Only
```bash
python nasa_demo.py --server-only
```
Then visit http://localhost:8001/docs for API documentation

### Option 3: GUI Client Only
```bash
python nasa_demo.py --client-only
```
(Make sure server is running separately)

## 📋 Available Endpoints

When the HTTP server is running on port 8001:

- **Status**: `GET http://localhost:8001/`
- **List Tools**: `GET http://localhost:8001/tools`
- **Call Tool**: `POST http://localhost:8001/call`

## 🛠️ Example API Calls

### Get Today's APOD
```bash
curl -X POST http://localhost:8001/call \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_astronomy_picture_of_the_day",
      "arguments": {}
    },
    "id": 1
  }'
```

### Search Mars Rover Photos
```bash
curl -X POST http://localhost:8001/call \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "search_mars_rover_photos",
      "arguments": {
        "rover_name": "curiosity",
        "sol": 1000,
        "camera": "NAVCAM"
      }
    },
    "id": 1
  }'
```

### Get Near Earth Objects
```bash
curl -X POST http://localhost:8001/call \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_near_earth_objects",
      "arguments": {
        "start_date": "2025-08-03",
        "end_date": "2025-08-10"
      }
    },
    "id": 1
  }'
```

## 🔧 Testing

Run the test suite to verify everything is working:

```bash
python test_nasa.py
```

## 📁 File Structure

```
mcp-tutorial/
├── nasa_demo.py                    # Main launcher script
├── test_nasa.py                    # Test suite
├── mcp-server/
│   └── nasa_server.py             # NASA MCP server
├── mcp-client/
│   ├── server_wrapper/
│   │   └── nasa_http_server_sync.py   # HTTP wrapper
│   └── clients/nasa/
│       └── nasa_gui_client.py      # Tkinter GUI client
└── pyproject.toml                  # Dependencies (includes Pillow)
```

## 🌟 Features Demonstrated

### Model Context Protocol (MCP)
- ✅ Server implementation with tool registration
- ✅ JSON-RPC communication protocol
- ✅ HTTP transport wrapper
- ✅ Client-server architecture

### NASA API Integration
- ✅ APOD API with date filtering
- ✅ Mars Rover Photos API with rover and camera selection
- ✅ Near Earth Objects API with date range queries
- ✅ Error handling and rate limiting awareness

### GUI Development
- ✅ Tkinter multi-tab interface
- ✅ Image loading and display with PIL/Pillow
- ✅ Async operations in GUI threads
- ✅ File saving capabilities

### HTTP Server
- ✅ REST API endpoints
- ✅ CORS support for web access
- ✅ JSON-RPC message handling
- ✅ Process management and cleanup

## ⚠️ Notes

- **API Key**: Currently uses NASA's DEMO_KEY which has rate limits
- **Production**: Get a free API key at https://api.nasa.gov/ for higher limits
- **Dependencies**: All required packages are in `pyproject.toml`
- **Python Version**: Requires Python 3.10+

## 🎯 Next Steps

1. **Get NASA API Key**: Replace DEMO_KEY with your own for better performance
2. **Extend Tools**: Add more NASA APIs (Earth Imagery, Exoplanets, etc.)
3. **Web Interface**: Create a web-based client using the HTTP endpoints
4. **Mobile App**: Build a mobile client using the REST API
5. **AI Integration**: Connect with Gemini/Claude for natural language queries

## 🐛 Troubleshooting

- **Port conflicts**: Change port with `--port 8002`
- **API errors**: Check internet connection and API key limits
- **GUI issues**: Ensure tkinter and Pillow are installed
- **Server startup**: Check that no other processes are using the port

The NASA MCP integration is now complete and fully functional! 🎉
