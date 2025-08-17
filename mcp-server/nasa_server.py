#!/usr/bin/env python3
"""
NASA MCP Server

Provides tools for accessing NASA's APIs including:
- Astronomy Picture of the Day (APOD)
- Mars Rover Photos
- Near Earth Objects (NEOs)
"""

import asyncio
import json
import os
import sys
from datetime import datetime, date
from typing import Any, Dict, List, Optional
import httpx
from dotenv import load_dotenv
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    CallToolRequestParams,
    TextContent,
    Tool,
)
import mcp.server.stdio

# Load environment variables from .env file
load_dotenv()

# NASA API key - get from https://api.nasa.gov/
NASA_API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")  # Load from .env file or fallback to DEMO_KEY

server = Server("nasa-server")

def validate_date_format(date_str: str) -> bool:
    """Validate date string is in YYYY-MM-DD format"""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available NASA tools"""
    return [
        Tool(
            name="get_astronomy_picture_of_the_day",
            description="Get NASA's Astronomy Picture of the Day (APOD) for a specific date. Returns the title, explanation, and image URL.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format. If not provided, returns today's APOD.",
                        "pattern": r"^\d{4}-\d{2}-\d{2}$"
                    }
                },
                "required": []
            },
        ),
        Tool(
            name="search_mars_rover_photos",
            description="Search for photos taken by Mars rovers on a specific Martian day (Sol). Returns a list of photos with URLs and camera information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "rover_name": {
                        "type": "string",
                        "description": "Name of the Mars rover",
                        "enum": ["curiosity", "opportunity", "spirit", "perseverance", "ingenuity"]
                    },
                    "sol": {
                        "type": "integer",
                        "description": "Martian day (Sol) since the rover's landing",
                        "minimum": 0
                    },
                    "camera": {
                        "type": "string",
                        "description": "Optional camera filter (e.g., 'FHAZ', 'RHAZ', 'MAST', 'CHEMCAM', 'MAHLI', 'MARDI', 'NAVCAM')"
                    }
                },
                "required": ["rover_name", "sol"]
            },
        ),
        Tool(
            name="get_near_earth_objects",
            description="Get list of Near Earth Objects (asteroids) passing close to Earth within a date range. Returns object details including size and closest approach.",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format",
                        "pattern": r"^\d{4}-\d{2}-\d{2}$"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format",
                        "pattern": r"^\d{4}-\d{2}-\d{2}$"
                    }
                },
                "required": ["start_date", "end_date"]
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Dict[str, Any]
) -> List[TextContent]:
    """Handle tool calls"""
    
    if name == "get_astronomy_picture_of_the_day":
        return await get_astronomy_picture_of_the_day(arguments)
    elif name == "search_mars_rover_photos":
        return await search_mars_rover_photos(arguments)
    elif name == "get_near_earth_objects":
        return await get_near_earth_objects(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

async def get_astronomy_picture_of_the_day(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get NASA's Astronomy Picture of the Day"""
    
    # Get date parameter or use today
    apod_date = arguments.get("date")
    if apod_date and not validate_date_format(apod_date):
        return [TextContent(
            type="text",
            text="Error: Date must be in YYYY-MM-DD format"
        )]
    
    url = "https://api.nasa.gov/planetary/apod"
    params = {"api_key": NASA_API_KEY}
    
    if apod_date:
        params["date"] = apod_date
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Format the response
            result = f"""🌌 NASA Astronomy Picture of the Day
📅 Date: {data.get('date', 'Today')}
🏷️ Title: {data.get('title', 'N/A')}

📝 Explanation:
{data.get('explanation', 'No explanation available')}

🔗 Image URL: {data.get('url', 'No URL available')}

📊 Media Type: {data.get('media_type', 'image')}
"""
            
            if data.get('copyright'):
                result += f"©️ Copyright: {data['copyright']}\n"
            
            if data.get('hdurl'):
                result += f"🖼️ HD Image URL: {data['hdurl']}\n"
            
            return [TextContent(type="text", text=result)]
            
    except httpx.HTTPStatusError as e:
        return [TextContent(
            type="text",
            text=f"NASA API error: {e.response.status_code} - {e.response.text}"
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error fetching APOD: {str(e)}"
        )]

async def search_mars_rover_photos(arguments: Dict[str, Any]) -> List[TextContent]:
    """Search for Mars rover photos"""
    
    rover_name = arguments.get("rover_name", "").lower()
    sol = arguments.get("sol")
    camera = arguments.get("camera")
    
    if not rover_name or sol is None:
        return [TextContent(
            type="text",
            text="Error: rover_name and sol are required parameters"
        )]
    
    # Validate rover name
    valid_rovers = ["curiosity", "opportunity", "spirit", "perseverance", "ingenuity"]
    if rover_name not in valid_rovers:
        return [TextContent(
            type="text",
            text=f"Error: Invalid rover name. Must be one of: {', '.join(valid_rovers)}"
        )]
    
    url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/{rover_name}/photos"
    params = {
        "api_key": NASA_API_KEY,
        "sol": sol
    }
    
    if camera:
        params["camera"] = camera.upper()
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            photos = data.get("photos", [])
            
            if not photos:
                return [TextContent(
                    type="text",
                    text=f"No photos found for {rover_name.title()} rover on Sol {sol}"
                )]
            
            # Limit to first 10 photos to avoid overwhelming output
            photos = photos[:10]
            
            result = f"""🚀 Mars Rover Photos - {rover_name.title()}
📅 Sol (Martian Day): {sol}
📸 Found {len(photos)} photos (showing first 10)

"""
            
            for i, photo in enumerate(photos, 1):
                result += f"""📷 Photo {i}:
   🔗 URL: {photo.get('img_src', 'N/A')}
   📹 Camera: {photo.get('camera', {}).get('full_name', 'Unknown')} ({photo.get('camera', {}).get('name', 'N/A')})
   🗓️ Earth Date: {photo.get('earth_date', 'N/A')}
   🆔 Photo ID: {photo.get('id', 'N/A')}

"""
            
            return [TextContent(type="text", text=result)]
            
    except httpx.HTTPStatusError as e:
        return [TextContent(
            type="text",
            text=f"NASA API error: {e.response.status_code} - {e.response.text}"
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error fetching Mars rover photos: {str(e)}"
        )]

async def get_near_earth_objects(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get Near Earth Objects within a date range"""
    
    start_date = arguments.get("start_date")
    end_date = arguments.get("end_date")
    
    if not start_date or not end_date:
        return [TextContent(
            type="text",
            text="Error: start_date and end_date are required parameters"
        )]
    
    if not validate_date_format(start_date) or not validate_date_format(end_date):
        return [TextContent(
            type="text",
            text="Error: Dates must be in YYYY-MM-DD format"
        )]
    
    url = "https://api.nasa.gov/neo/rest/v1/feed"
    params = {
        "api_key": NASA_API_KEY,
        "start_date": start_date,
        "end_date": end_date
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            element_count = data.get("element_count", 0)
            near_earth_objects = data.get("near_earth_objects", {})
            
            if element_count == 0:
                return [TextContent(
                    type="text",
                    text=f"No Near Earth Objects found between {start_date} and {end_date}"
                )]
            
            result = f"""🌍 Near Earth Objects (NEOs) - Tile View
📅 Date Range: {start_date} to {end_date}
🔢 Total Objects: {element_count}

"""
            
            # Collect all objects across all dates for tile view
            all_objects = []
            for date_str, objects in near_earth_objects.items():
                for obj in objects:
                    obj["approach_date"] = date_str  # Add the date to the object
                    all_objects.append(obj)
            
            # Limit to first 12 objects for tile view
            all_objects = all_objects[:12]
            
            # Create tiles in a grid format (3 columns)
            for i, obj in enumerate(all_objects):
                name = obj.get("name", "Unknown")
                neo_reference_id = obj.get("neo_reference_id", "N/A")
                approach_date = obj.get("approach_date", "N/A")
                
                # Get size estimates
                estimated_diameter = obj.get("estimated_diameter", {})
                size_km = estimated_diameter.get("kilometers", {})
                min_size = size_km.get("estimated_diameter_min", 0)
                max_size = size_km.get("estimated_diameter_max", 0)
                avg_size = (min_size + max_size) / 2
                
                # Get close approach data
                close_approach_data = obj.get("close_approach_data", [])
                if close_approach_data:
                    approach = close_approach_data[0]
                    miss_distance_km = approach.get("miss_distance", {}).get("kilometers", "N/A")
                    relative_velocity = approach.get("relative_velocity", {}).get("kilometers_per_hour", "N/A")
                    
                    # Format distance for readability (already in kilometers)
                    if miss_distance_km != "N/A":
                        try:
                            dist_float = float(miss_distance_km)
                            miss_distance_display = f"{dist_float:,.0f} km"
                        except:
                            miss_distance_display = miss_distance_km
                    else:
                        miss_distance_display = "N/A"
                    
                    # Format velocity (already in kilometers per hour)
                    if relative_velocity != "N/A":
                        try:
                            vel_float = float(relative_velocity)
                            velocity_display = f"{vel_float:,.0f} km/h"
                        except:
                            velocity_display = relative_velocity
                    else:
                        velocity_display = "N/A"
                else:
                    miss_distance_display = "N/A"
                    velocity_display = "N/A"
                
                # Determine hazard status and icon
                is_hazardous = obj.get("is_potentially_hazardous_asteroid", False)
                hazard_icon = "⚠️" if is_hazardous else "✅"
                hazard_text = "HAZARDOUS" if is_hazardous else "Safe"
                
                # Size category for visual representation
                if avg_size > 1.0:
                    size_icon = "🌕"  # Large
                elif avg_size > 0.1:
                    size_icon = "�"  # Medium
                else:
                    size_icon = "🌗"  # Small
                
                # Create tile with border
                tile_border = "═" * 45
                result += f"""
╔{tile_border}╗
║ {size_icon} {name[:35]:<35} ║
║                                             ║
║ 📅 Date: {approach_date:<29} ║
║ 📏 Size: {avg_size:.3f} km {size_icon:<20} ║
║ � Distance: {miss_distance_display:<26} ║
║ 🚀 Speed: {velocity_display:<30} ║
║ {hazard_icon} Status: {hazard_text:<29} ║
║ 🆔 ID: {neo_reference_id[-25:]:<30} ║
╚{tile_border}╝
"""
            
            if len(all_objects) == 12 and element_count > 12:
                result += f"\n📋 Showing 12 of {element_count} objects in tile view\n"
            
            return [TextContent(type="text", text=result)]
            
    except httpx.HTTPStatusError as e:
        return [TextContent(
            type="text",
            text=f"NASA API error: {e.response.status_code} - {e.response.text}"
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error fetching Near Earth Objects: {str(e)}"
        )]

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="nasa-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    print("Starting NASA MCP Server...", file=sys.stderr)
    asyncio.run(main())
