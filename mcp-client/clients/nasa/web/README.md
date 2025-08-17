# NASA Space Explorer Web App 🚀

A beautiful Streamlit-based web interface for exploring NASA data through the NASA MCP server.

## Features

- 🌌 **Space-themed UI** with animated stars and shooting stars
- 🎯 **Natural language queries** - ask anything about NASA data
- 🖼️ **Image display** for APOD and Mars rover photos
- 📱 **Responsive design** that works on desktop and mobile
- ⚡ **Real-time data** from NASA APIs
- 🛠️ **Tool sidebar** showing available NASA tools

## Quick Start

### 1. Install Dependencies

```bash
cd mcp-client/clients/nasa/web
pip install -r requirements.txt
```

### 2. Start NASA HTTP Server

In a separate terminal:
```bash
cd mcp-server/server_wrapper
python nasa_http_server_sync.py --port 8001
```

### 3. Launch Web App

```bash
python run_web_app.py
```

The web app will be available at: http://localhost:8501

## Example Queries

### Astronomy Picture of the Day (APOD)
- "Show me today's astronomy picture"
- "Get APOD for 2023-12-25"
- "What's the astronomy picture today?"

### Mars Rover Photos
- "Get Mars rover photos from Curiosity sol 1000"
- "Show me Perseverance photos from sol 500"
- "Mars rover images from sol 2000 using MAST camera"

### Near Earth Objects (NEO)
- "What's the closest asteroid on April 13th 2029?"
- "What asteroids are approaching Earth?"
- "Show me near earth objects this week"
- "Any space rocks coming close to Earth?"
- "Show me asteroids in March 2029"
- "What NEOs are there in April 2030?"
- "Asteroids next month"
- "Space rocks in December 2025"

## UI Features

### Theme
- Dark space-themed background with gradient
- Animated starfield with twinkling stars
- Shooting star animations
- Futuristic fonts (Orbitron and Space Mono)

### Layout
- **Header**: Animated gradient title with space emoji
- **Sidebar**: Available tools and example queries
- **Chat Interface**: Conversation-style interaction
- **Input Bar**: Natural language query input
- **Image Display**: Automatic image rendering for NASA photos

### Responsive Design
- Works on desktop, tablet, and mobile
- Adaptive layout based on screen size
- Touch-friendly interface

## Architecture

```
Web App Architecture:
┌─────────────────┐    HTTP     ┌─────────────────┐    stdio    ┌─────────────────┐
│  Streamlit App  │ ──────────► │  HTTP Server    │ ──────────► │   NASA Server   │
│  (Port 8501)    │             │  (Port 8001)    │             │   (MCP stdio)   │
└─────────────────┘             └─────────────────┘             └─────────────────┘
```

### Components

1. **Streamlit App** (`nasa_streamlit_app.py`)
   - Web UI with space theme
   - Natural language query parsing
   - HTTP client for NASA server
   - Image display and formatting

2. **NASA HTTP Server** (`../../../mcp-server/server_wrapper/nasa_http_server_sync.py`)
   - HTTP wrapper for MCP server
   - REST API endpoints
   - Request/response handling

3. **NASA MCP Server** (`../../../mcp-server/nasa_server.py`)
   - Core NASA tool implementations
   - Direct NASA API integration
   - MCP protocol compliance

## Query Parsing

The web app includes intelligent query parsing that maps natural language to NASA tools:

### APOD Tool
- Keywords: picture, photo, image, apod, astronomy picture, today
- Date extraction from queries like "APOD for 2023-12-25"

### Mars Rover Tool
- Keywords: mars, rover, curiosity, perseverance, opportunity, spirit, ingenuity
- Sol extraction from "sol 1000" or "day 500"
- Camera detection (FHAZ, RHAZ, MAST, etc.)

### NEO Tool
- Keywords: asteroid, near earth, neo, objects, space rocks
- Date range parsing or defaults to next 7 days

## Customization

### Styling
Edit the CSS in `load_css()` function to customize:
- Colors and gradients
- Animations
- Fonts
- Layout

### Query Parsing
Modify `parse_user_query()` to add:
- New keywords
- Better date parsing
- Additional parameter extraction

### Result Formatting
Update `format_*_result()` functions to change:
- Data presentation
- Image handling
- Error messages

## Troubleshooting

### Common Issues

1. **"Cannot connect to NASA MCP Server"**
   - Ensure HTTP server is running on port 8001
   - Check if `nasa_http_server_sync.py` is accessible

2. **"Import streamlit could not be resolved"**
   - Install dependencies: `pip install -r requirements.txt`

3. **Images not loading**
   - Check NASA API key in server configuration
   - Verify internet connection for external images

4. **Rate limiting errors**
   - Replace DEMO_KEY with actual NASA API key
   - Wait before making more requests

### Debug Mode

Add debug logging by setting environment variable:
```bash
export STREAMLIT_LOGGER_LEVEL=debug
python run_web_app.py
```

## Development

### File Structure
```
web/
├── nasa_streamlit_app.py   # Main Streamlit application
├── run_web_app.py          # Launcher script
├── requirements.txt        # Dependencies
└── README.md              # This file
```

### Adding New Features

1. **New NASA Tools**: Update query parsing and result formatting
2. **UI Enhancements**: Modify CSS and layout components
3. **Additional APIs**: Extend client class and add tool mappings

## License

Part of the MCP Tutorial project. See main project LICENSE file.
