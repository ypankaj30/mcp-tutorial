#!/usr/bin/env python3
"""
NASA MCP Streamlit Web App

A beautiful web interface for NASA MCP server with space-themed UI.
Features:
- Interactive prompt bar for natural language queries
- Space-themed background with animated elements
- Real-time NASA data visualization
- Support for all NASA MCP tools
"""

import streamlit as st
import requests
import json
import base64
from datetime import datetime, date, timedelta
import re
from typing import Dict, Any, Optional
import time
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from the mcp-client directory
load_dotenv(dotenv_path="../../../.env")

# Page configuration
st.set_page_config(
    page_title="NASA Space Explorer",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for space theme
def load_css():
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Space+Mono:wght@400;700&display=swap');
    
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 25%, #16213e 50%, #0f3460 75%, #0e1b3a 100%);
        color: #ffffff;
        font-family: 'Space Mono', monospace;
    }
    
    /* Animated stars background */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(2px 2px at 20px 30px, #eee, transparent),
            radial-gradient(2px 2px at 40px 70px, rgba(255,255,255,0.8), transparent),
            radial-gradient(1px 1px at 90px 40px, #fff, transparent),
            radial-gradient(1px 1px at 130px 80px, rgba(255,255,255,0.6), transparent),
            radial-gradient(2px 2px at 160px 30px, #ddd, transparent);
        background-repeat: repeat;
        background-size: 200px 100px;
        animation: sparkle 3s linear infinite;
        pointer-events: none;
        z-index: 0;
    }
    
    @keyframes sparkle {
        from { transform: translateY(0px); }
        to { transform: translateY(-100px); }
    }
    
    /* Header styling */
    .main-header {
        font-family: 'Orbitron', sans-serif;
        font-size: 3rem;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4, #ffd93d);
        background-size: 400% 400%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradient 3s ease infinite;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 30px rgba(255, 255, 255, 0.5);
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .subtitle {
        font-family: 'Space Mono', monospace;
        text-align: center;
        color: #a0a0a0;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    /* Chat container */
    .chat-container {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
    }
    
    /* Message styling */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px 20px;
        border-radius: 20px 20px 5px 20px;
        margin: 10px 0;
        color: white;
        font-family: 'Space Mono', monospace;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 50%, #2c3e50 100%);
        border-left: 4px solid #3498db;
        padding: 15px 20px;
        border-radius: 20px 20px 20px 5px;
        margin: 10px 0;
        color: white;
        font-family: 'Space Mono', monospace;
        box-shadow: 0 4px 15px rgba(52, 152, 219, 0.2);
    }
    
    /* Tool result styling */
    .tool-result {
        background: rgba(76, 175, 80, 0.1);
        border-left: 4px solid #4caf50;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
        font-family: 'Space Mono', monospace;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        border: 2px solid rgba(255, 255, 255, 0.2);
        border-radius: 25px;
        padding: 15px 20px;
        font-family: 'Space Mono', monospace;
        font-size: 16px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #4ecdc4;
        box-shadow: 0 0 20px rgba(78, 205, 196, 0.3);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 10px 30px;
        font-family: 'Orbitron', sans-serif;
        font-weight: 700;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 7px 14px rgba(102, 126, 234, 0.4);
    }
    
    /* Sample prompt section styling */
    .sample-prompts {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Sample prompt buttons - different colors for different categories */
    .stButton > button[data-testid*="sample_apod"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .stButton > button[data-testid*="sample_mars"] {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    .stButton > button[data-testid*="sample_neo"] {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    /* Tip section styling */
    .tip-section {
        background: linear-gradient(135deg, rgba(255, 193, 7, 0.1) 0%, rgba(255, 152, 0, 0.1) 100%);
        border-left: 4px solid #ffc107;
        padding: 15px;
        border-radius: 5px;
        margin: 15px 0;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
    }
    
    /* Metrics styling */
    [data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1rem;
        border-radius: 10px;
        backdrop-filter: blur(10px);
    }
    
    /* Image styling */
    .nasa-image {
        border-radius: 15px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Hide Streamlit menu and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Shooting star animation */
    .shooting-star {
        position: fixed;
        top: 50%;
        left: 100%;
        width: 2px;
        height: 2px;
        background: white;
        border-radius: 50%;
        box-shadow: 0 0 6px 2px white;
        animation: shooting 3s linear infinite;
        opacity: 0;
    }
    
    @keyframes shooting {
        0% {
            transform: translateX(0) translateY(0);
            opacity: 1;
        }
        100% {
            transform: translateX(-100vw) translateY(-100px);
            opacity: 0;
        }
    }
    
    /* Top input bar styles */
    .top-input-container {
        position: sticky;
        top: 0;
        background: rgba(0, 0, 0, 0.9);
        backdrop-filter: blur(15px);
        padding: 20px;
        border-bottom: 2px solid rgba(52, 152, 219, 0.3);
        z-index: 100;
        margin-bottom: 20px;
    }
    
    /* Input form styling */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.1);
        border: 2px solid rgba(52, 152, 219, 0.3);
        border-radius: 25px;
        color: white;
        font-family: 'Space Mono', monospace;
        padding: 15px 20px;
        font-size: 16px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3498db;
        box-shadow: 0 0 20px rgba(52, 152, 219, 0.4);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(45deg, #3498db, #2980b9);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 10px 20px;
        font-family: 'Space Mono', monospace;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4);
    }
    </style>
    
    <!-- Add shooting stars -->
    <div class="shooting-star" style="animation-delay: 0s; top: 20%;"></div>
    <div class="shooting-star" style="animation-delay: 1s; top: 40%;"></div>
    <div class="shooting-star" style="animation-delay: 2s; top: 60%;"></div>
    <div class="shooting-star" style="animation-delay: 3s; top: 80%;"></div>
    """, unsafe_allow_html=True)

class NASAWebClient:
    """Client for communicating with NASA MCP HTTP server"""
    
    def __init__(self, server_url: str = "http://localhost:8001"):
        self.server_url = server_url
        self.session = requests.Session()
        
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the NASA MCP server"""
        payload = {
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        try:
            response = self.session.post(
                f"{self.server_url}/call",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to call tool: {str(e)}"}
    
    def list_tools(self) -> Dict[str, Any]:
        """Get list of available tools"""
        try:
            response = self.session.get(f"{self.server_url}/tools", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to list tools: {str(e)}"}
    
    def check_connection(self) -> bool:
        """Check if the server is accessible"""
        try:
            response = self.session.get(f"{self.server_url}/", timeout=5)
            return response.status_code == 200
        except:
            return False

class LLMQueryProcessor:
    """Use LLM to process natural language queries and determine NASA tool calls"""
    
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            # Use gemini-1.5-flash for better free tier rate limits
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
        
        # Available NASA tools and their descriptions
        self.tools_info = """
        Available NASA MCP Tools:
        
        1. get_astronomy_picture_of_the_day
           - Gets NASA's Astronomy Picture of the Day for a specific date
           - Parameters: date (optional, format: YYYY-MM-DD)
           - Use for: space pictures, APOD, astronomy images, daily photos
        
        2. search_mars_rover_photos  
           - Search for photos taken by Mars rovers on a specific Martian day (Sol)
           - Parameters: rover_name (curiosity/perseverance/opportunity/spirit/ingenuity), sol (integer), camera (optional)
           - Use for: Mars photos, rover images, red planet, Mars exploration
        
        3. get_near_earth_objects
           - Get Near Earth Objects (asteroids) within a date range (max 7 days)
           - Parameters: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD)
           - Use for: asteroids, NEOs, space rocks, objects approaching Earth
           - Note: Date range limited to 7 days by NASA API
        """
    
    def parse_query_with_llm(self, query: str) -> tuple[str, dict]:
        """Use LLM to parse natural language query and determine tool call"""
        
        if not self.model:
            # Fallback to regex-based parsing if no LLM available
            return self.fallback_parse_query(query)
        
        try:
            today = date.today().strftime('%Y-%m-%d')
            
            prompt = f"""
            You are a NASA query parser. Given a natural language query about space/NASA data, determine which NASA tool to call and with what parameters.

            Current date: {today}

            {self.tools_info}

            Important rules:
            - For NEO/asteroid queries, date ranges are limited to 7 days maximum
            - If user asks about a specific date (like "April 13th 2029"), create a 7-day range centered around that date or starting from that date
            - If user asks about future years (like 2029) without specific dates, use the first week of that year
            - Mars rover Sol numbers should be reasonable (0-4000 range typically)
            - Default to get_astronomy_picture_of_the_day if query is ambiguous

            Date parsing examples:
            - "asteroids in March 2029" -> use March 1-7, 2029
            - "NEOs in April 2030" -> use April 1-7, 2030  
            - "closest asteroid on April 13th 2029" -> use April 13-19, 2029 (7 days starting from specified date)
            - "asteroids around April 13th 2029" -> use April 10-16, 2029 (7 days centered around specified date)
            - "asteroids next month" -> calculate next month from today
            - "space rocks this week" -> use current week
            - "asteroids in 2029" (no month specified) -> use current month of 2029

            User query: "{query}"

            Respond with a JSON object containing:
            {{
                "tool_name": "exact_tool_name",
                "arguments": {{"param1": "value1", "param2": "value2"}},
                "reasoning": "brief explanation of your choice and date extraction"
            }}

            Examples:
            - "Show me today's space picture" -> {{"tool_name": "get_astronomy_picture_of_the_day", "arguments": {{}}, "reasoning": "User wants today's APOD"}}
            - "Mars rover photos from sol 1000" -> {{"tool_name": "search_mars_rover_photos", "arguments": {{"rover_name": "curiosity", "sol": 1000}}, "reasoning": "User wants Mars rover photos from sol 1000"}}
            - "Asteroids in March 2029" -> {{"tool_name": "get_near_earth_objects", "arguments": {{"start_date": "2029-03-01", "end_date": "2029-03-07"}}, "reasoning": "User specified March 2029, using first week of March due to 7-day API limit"}}
            - "closest asteroid on April 13th 2029" -> {{"tool_name": "get_near_earth_objects", "arguments": {{"start_date": "2029-04-13", "end_date": "2029-04-19"}}, "reasoning": "User specified April 13th 2029, using 7-day range starting from that date"}}
            - "NEOs in April 2030" -> {{"tool_name": "get_near_earth_objects", "arguments": {{"start_date": "2030-04-01", "end_date": "2030-04-07"}}, "reasoning": "User specified April 2030, using first week of April"}}
            - "Asteroids next month" -> {{"tool_name": "get_near_earth_objects", "arguments": {{"start_date": "2025-09-01", "end_date": "2025-09-07"}}, "reasoning": "Next month from current date, using first week"}}
            """
            
            # Generate response using Gemini
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Parse the JSON response
            try:
                parsed = json.loads(response_text)
                tool_name = parsed.get("tool_name")
                arguments = parsed.get("arguments", {})
                reasoning = parsed.get("reasoning", "")
                
                # Store reasoning for debugging
                st.session_state.debug_reasoning = reasoning
                
                return tool_name, arguments
                
            except json.JSONDecodeError:
                # If JSON parsing fails, fall back to regex
                return self.fallback_parse_query(query)
                
        except Exception as e:
            # If LLM call fails, fall back to regex
            st.warning(f"Gemini parsing failed: {str(e)}, using fallback parser")
            return self.fallback_parse_query(query)
    
    def fallback_parse_query(self, query: str) -> tuple[str, dict]:
        """Fallback regex-based parsing when LLM is not available"""
        query_lower = query.lower()
        
        # Mars rover patterns (check first - more specific)
        if any(word in query_lower for word in ['mars', 'rover', 'curiosity', 'perseverance', 'opportunity', 'spirit', 'ingenuity']):
            arguments = {}
            
            # Extract rover name
            if 'curiosity' in query_lower:
                arguments['rover_name'] = 'curiosity'
            elif 'perseverance' in query_lower:
                arguments['rover_name'] = 'perseverance'
            elif 'opportunity' in query_lower:
                arguments['rover_name'] = 'opportunity'
            elif 'spirit' in query_lower:
                arguments['rover_name'] = 'spirit'
            elif 'ingenuity' in query_lower:
                arguments['rover_name'] = 'ingenuity'
            else:
                arguments['rover_name'] = 'curiosity'  # default
            
            # Extract sol (Martian day)
            sol_match = re.search(r'\bsol\s*(\d+)\b', query_lower)
            if sol_match:
                arguments['sol'] = int(sol_match.group(1))
            else:
                # Extract general day/number
                day_match = re.search(r'\bday\s*(\d+)\b', query_lower)
                if day_match:
                    arguments['sol'] = int(day_match.group(1))
                else:
                    arguments['sol'] = 1000  # default
            
            # Extract camera
            cameras = ['fhaz', 'rhaz', 'mast', 'chemcam', 'mahli', 'mardi', 'navcam']
            for camera in cameras:
                if camera in query_lower:
                    arguments['camera'] = camera.upper()
                    break
            
            return "search_mars_rover_photos", arguments
        
        # NEO patterns - Enhanced date parsing
        elif any(word in query_lower for word in ['asteroid', 'near earth', 'neo', 'objects', 'space rocks']):
            today = date.today()
            start_date = today.strftime('%Y-%m-%d')
            end_date = (today + timedelta(days=7)).strftime('%Y-%m-%d')
            
            # Month name mapping
            months = {
                'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
                'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6,
                'july': 7, 'jul': 7, 'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
                'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
            }
            
            # Check for specific date patterns first (e.g., "April 13th 2029", "April 13 2029")
            specific_date_pattern = r'\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})(?:st|nd|rd|th)?\s*,?\s*(\d{4})\b'
            specific_date_match = re.search(specific_date_pattern, query_lower)
            
            if specific_date_match:
                month_name = specific_date_match.group(1)
                day = int(specific_date_match.group(2))
                year = int(specific_date_match.group(3))
                month_num = months.get(month_name, 1)
                
                # Create 7-day range starting from the specified date
                try:
                    target_date = date(year, month_num, day)
                    start_date = target_date.strftime('%Y-%m-%d')
                    end_date = (target_date + timedelta(days=6)).strftime('%Y-%m-%d')
                except ValueError:
                    # If invalid date, fall back to first week of the month
                    start_date = f"{year}-{month_num:02d}-01"
                    end_date = f"{year}-{month_num:02d}-07"
            
            # Check for specific month and year patterns (e.g., "April 2029")
            elif re.search(r'\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\s+(\d{4})\b', query_lower):
                month_year_pattern = r'\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\s+(\d{4})\b'
                month_year_match = re.search(month_year_pattern, query_lower)
                month_name = month_year_match.group(1)
                year = int(month_year_match.group(2))
                month_num = months.get(month_name, 1)
                start_date = f"{year}-{month_num:02d}-01"
                end_date = f"{year}-{month_num:02d}-07"
                
            # Check for year with just month name (e.g., "March 2029")
            elif any(month in query_lower for month in months.keys()):
                for month_name, month_num in months.items():
                    if month_name in query_lower:
                        # Look for year near the month
                        year_match = re.search(rf'{month_name}\s*(\d{{4}})', query_lower)
                        if not year_match:
                            year_match = re.search(rf'(\d{{4}})\s*{month_name}', query_lower)
                        
                        if year_match:
                            year = int(year_match.group(1))
                        else:
                            # Use current year if month hasn't passed, otherwise next year
                            year = today.year if month_num >= today.month else today.year + 1
                        
                        start_date = f"{year}-{month_num:02d}-01"
                        end_date = f"{year}-{month_num:02d}-07"
                        break
            
            # Check for relative time expressions
            elif 'next month' in query_lower:
                next_month = today.month + 1
                year = today.year
                if next_month > 12:
                    next_month = 1
                    year += 1
                start_date = f"{year}-{next_month:02d}-01"
                end_date = f"{year}-{next_month:02d}-07"
                
            elif 'next year' in query_lower:
                next_year = today.year + 1
                # Use current month of next year, not January
                start_date = f"{next_year}-{today.month:02d}-01"
                end_date = f"{next_year}-{today.month:02d}-07"
                
            elif 'next week' in query_lower:
                start_date = (today + timedelta(days=7)).strftime('%Y-%m-%d')
                end_date = (today + timedelta(days=14)).strftime('%Y-%m-%d')
            
            # Check for just year (e.g., "2029")
            elif re.search(r'\b(\d{4})\b', query_lower):
                year_match = re.search(r'\b(\d{4})\b', query_lower)
                year = int(year_match.group(1))
                if year >= today.year:
                    # Use current month of that year, not January
                    current_month = today.month
                    start_date = f"{year}-{current_month:02d}-01"
                    end_date = f"{year}-{current_month:02d}-07"
            
            return "get_near_earth_objects", {"start_date": start_date, "end_date": end_date}
        
        # Default to APOD
        else:
            # Extract date if mentioned
            date_match = re.search(r'\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b', query)
            if date_match:
                date_str = date_match.group(1).replace('/', '-')
                return "get_astronomy_picture_of_the_day", {"date": date_str}
            else:
                return "get_astronomy_picture_of_the_day", {}

def format_tool_result(result: Dict[str, Any], tool_name: str) -> str:
    """Format tool result for display"""
    if "error" in result:
        return f"❌ Error: {result['error']}"
    
    if "result" not in result:
        return "❌ No result returned"
    
    content = result["result"]["content"]
    if not content:
        return "❌ Empty response"
    
    text_content = content[0]["text"]
    
    # Parse JSON if it looks like JSON
    try:
        if text_content.strip().startswith('{'):
            data = json.loads(text_content)
            if tool_name == "get_astronomy_picture_of_the_day":
                return format_apod_result(data)
            elif tool_name == "search_mars_rover_photos":
                return format_mars_result(data)
            elif tool_name == "get_near_earth_objects":
                return format_neo_result(data)
    except json.JSONDecodeError:
        pass
    
    return text_content

def format_apod_result(data: Dict) -> str:
    """Format APOD result"""
    if 'error' in data:
        return f"❌ NASA API Error: {data['error']}"
    
    title = data.get('title', 'Unknown')
    explanation = data.get('explanation', 'No explanation available')
    url = data.get('url', '')
    date = data.get('date', '')
    
    result = f"🌟 **{title}**\n\n"
    if date:
        result += f"📅 Date: {date}\n\n"
    result += f"📝 {explanation}\n\n"
    if url:
        result += f"🔗 [View Image]({url})"
    
    return result

def format_mars_result(data: Dict) -> str:
    """Format Mars rover result"""
    if 'error' in data:
        return f"❌ NASA API Error: {data['error']}"
    
    photos = data.get('photos', [])
    if not photos:
        return "🔍 No photos found for the specified criteria"
    
    result = f"🚀 **Found {len(photos)} Mars Rover Photos**\n\n"
    
    for i, photo in enumerate(photos[:5]):  # Limit to first 5
        result += f"📸 **Photo {i+1}**\n"
        result += f"   • Camera: {photo.get('camera', {}).get('full_name', 'Unknown')}\n"
        result += f"   • Sol: {photo.get('sol', 'Unknown')}\n"
        result += f"   • Date: {photo.get('earth_date', 'Unknown')}\n"
        result += f"   • [View Image]({photo.get('img_src', '')})\n\n"
    
    if len(photos) > 5:
        result += f"... and {len(photos) - 5} more photos"
    
    return result

def format_neo_result(data: Dict) -> str:
    """Format Near Earth Objects result in tile view"""
    if 'error' in data:
        return f"❌ NASA API Error: {data['error']}"
    
    near_earth_objects = data.get('near_earth_objects', {})
    if not near_earth_objects:
        return "🔍 No Near Earth Objects found for the specified date range"
    
    # Collect all objects across all dates for tile view
    all_objects = []
    total_objects = 0
    for date_key, objects in near_earth_objects.items():
        total_objects += len(objects)
        for obj in objects:
            obj["approach_date"] = date_key  # Add the date to the object
            all_objects.append(obj)
    
    # Limit to first 12 objects for tile view
    all_objects = all_objects[:12]
    
    result = f"🌍 **Near Earth Objects - Tile View**\n\n"
    result += f"🔢 Total Objects: {total_objects} (showing first {len(all_objects)})\n\n"
    
    # Create tiles in a grid format
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
            size_icon = "🌖"  # Medium
        else:
            size_icon = "🌗"  # Small
        
        # Create tile with border (using markdown code block for formatting)
        result += f"""
```
╔═══════════════════════════════════════════╗
║ {size_icon} {name[:35]:<35} ║
║                                           ║
║ 📅 Date: {approach_date:<27} ║
║ 📏 Size: {avg_size:.3f} km                ║
║ 📍 Distance: {miss_distance_display:<23} ║
║ 🚀 Speed: {velocity_display:<26} ║
║ {hazard_icon} Status: {hazard_text:<25} ║
║ 🆔 ID: {neo_reference_id[-23:]:<25} ║
╚═══════════════════════════════════════════╝
```

"""
    
    if len(all_objects) == 12 and total_objects > 12:
        result += f"📋 *Showing 12 of {total_objects} objects in tile view*"
    
    return result

def process_query(query_text):
    """Process a NASA query and show results in overlay"""
    if not query_text:
        return
        
    st.session_state.current_query = query_text
    
    with st.spinner("🔍 Exploring NASA data..."):
        # Parse query using LLM or fallback
        tool_name, arguments = st.session_state.llm_processor.parse_query_with_llm(query_text)
        
        # Debug: Show what tool is being called
        st.session_state.debug_tool = f"Calling {tool_name} with {arguments}"
        if hasattr(st.session_state, 'debug_reasoning'):
            st.session_state.debug_tool += f" (Reasoning: {st.session_state.debug_reasoning})"
        
        # Call the tool
        result = st.session_state.client.call_tool(tool_name, arguments)
        
        # Debug: Store raw result
        st.session_state.debug_raw_result = str(result)
        
        # Format and display result
        formatted_result = format_tool_result(result, tool_name)
        
        # Debug: Store formatted result
        st.session_state.debug_formatted = formatted_result
        
        # Extract image URLs for separate storage
        url_pattern = r'https?://[^\s\)]+\.(?:jpg|jpeg|png|gif)'
        image_urls = re.findall(url_pattern, formatted_result)
        
        # Remove image URLs from text to prevent duplicate display
        clean_text = re.sub(url_pattern, '', formatted_result)
        clean_text = re.sub(r'\[View Image\]\(\)', '', clean_text)  # Remove empty markdown links
        clean_text = re.sub(r'🔗\s*$', '', clean_text, flags=re.MULTILINE)  # Remove dangling link emojis
        
        # Store result for overlay
        st.session_state.current_result = clean_text
        st.session_state.current_images = image_urls
        st.session_state.show_overlay = True
        
        # Debug overlay state
        st.session_state.debug_overlay_triggered = True
        st.session_state.debug_result_length = len(clean_text)
        st.session_state.debug_image_count = len(image_urls)
        
        # Also add to messages for history
        st.session_state.messages.append({"role": "user", "content": query_text})
        assistant_message = {"role": "assistant", "content": clean_text}
        if image_urls:
            assistant_message["images"] = image_urls
        st.session_state.messages.append(assistant_message)

def main():
    """Main Streamlit app"""
    load_css()
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'client' not in st.session_state:
        st.session_state.client = NASAWebClient()
    if 'llm_processor' not in st.session_state:
        st.session_state.llm_processor = LLMQueryProcessor()
    if 'show_overlay' not in st.session_state:
        st.session_state.show_overlay = False
    if 'current_result' not in st.session_state:
        st.session_state.current_result = ""
    if 'current_images' not in st.session_state:
        st.session_state.current_images = []
    if 'current_query' not in st.session_state:
        st.session_state.current_query = ""
    
    # Check server connection
    with st.spinner("🔗 Connecting to NASA MCP Server..."):
        if not st.session_state.client.check_connection():
            st.error("❌ Cannot connect to NASA MCP Server. Please ensure it's running on http://localhost:8001")
            st.info("💡 Start the server with: `cd mcp-server/server_wrapper && python nasa_http_server_sync.py --port 8001`")
            return
        else:
            st.success("✅ Connected to NASA MCP Server")

    # Check LLM status
    if st.session_state.llm_processor.model:
        st.success("🤖 Gemini LLM ready for intelligent query parsing")
    else:
        st.warning("⚠️ Gemini API key not found - using fallback regex parser")
        st.info("💡 Add GEMINI_API_KEY to your .env file for enhanced natural language understanding")

    # Header
    st.markdown('<h1 class="main-header">🚀 NASA Space Explorer</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Explore the cosmos with NASA\'s finest data</p>', unsafe_allow_html=True)
    
    # Show overlay FIRST if needed (before other content)
    if st.session_state.show_overlay:
        show_result_overlay()
        # Add some space after overlay
        st.markdown("---")
    
    # Top input bar (sticky)
    st.markdown('<div class="top-input-container">', unsafe_allow_html=True)
    
    with st.form("query_form", clear_on_submit=False):
        col1, col2 = st.columns([8, 1])
        
        with col1:
            user_input = st.text_input(
                "Ask NASA anything...",
                placeholder="Try: 'What's today's space picture?' or 'Show me Mars rover photos' or 'Any asteroids approaching Earth?'",
                key="query_input",
                value=st.session_state.get('current_query', ''),
                autocomplete="off"
            )
        
        with col2:
            submitted = st.form_submit_button("🚀", use_container_width=True, help="Search NASA data")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Process user input
    if submitted and user_input:
        process_query(user_input)
        # Rerun to show overlay
        st.rerun()
    
    # Always show sample questions
    st.markdown("### 🌟 Try These Sample Questions")
    st.markdown("Click any example below or type your own question in the search bar above:")
    
    # Create columns for better layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🌌 Astronomy Picture of the Day")
        if st.button("🖼️ Show me today's astronomy picture", key="sample_apod_today", use_container_width=True):
            process_query("Show me today's astronomy picture")
            st.rerun()
        
        if st.button("📅 Get APOD for Christmas 2023", key="sample_apod_christmas", use_container_width=True):
            process_query("Get APOD for 2023-12-25")
            st.rerun()
        
        if st.button("🎆 Show me New Year's Day 2024 space picture", key="sample_apod_newyear", use_container_width=True):
            process_query("Get astronomy picture for 2024-01-01")
            st.rerun()
    
    with col2:
        st.markdown("#### 🚀 Mars Rover Photos")
        if st.button("📸 Get Curiosity photos from sol 1000", key="sample_mars_curiosity", use_container_width=True):
            process_query("Get Mars rover photos from Curiosity sol 1000")
            st.rerun()
        
        if st.button("🔴 Show me recent Perseverance photos", key="sample_mars_perseverance", use_container_width=True):
            process_query("Show me Perseverance photos from sol 500")
            st.rerun()
        
        if st.button("📷 Get Mars photos with MAST camera", key="sample_mars_mast", use_container_width=True):
            process_query("Get Curiosity rover photos from sol 2000 using MAST camera")
            st.rerun()
    
    # Full width examples
    st.markdown("#### 🌍 Near Earth Objects")
    if st.button("☄️ What asteroids are approaching Earth this week?", key="sample_neo_week", use_container_width=True):
        process_query("What asteroids are approaching Earth this week?")
        st.rerun()
    
    if st.button("🌌 Asteroids in March 2029", key="sample_neo_march_2029", use_container_width=True):
        process_query("Show me asteroids in March 2029")
        st.rerun()
    
    if st.button("🚀 NEO objects in April 2030", key="sample_neo_april_2030", use_container_width=True):
        process_query("What near earth objects are there in April 2030?")
        st.rerun()
    
    if st.button("� Asteroids next month", key="sample_neo_next_month", use_container_width=True):
        process_query("Show me near earth objects next month")
        st.rerun()
    
    st.markdown("---")
    st.markdown('<div class="tip-section">💡 <strong>Tip</strong>: You can ask questions in natural language like <em>"Show me Mars photos from yesterday"</em> or <em>"What\'s today\'s space picture?"</em><br/>📅 <strong>Note</strong>: NASA NEO API has a 7-day limit, so year/month queries show the first week of that period.</div>', unsafe_allow_html=True)
    
    # Sidebar with tools (optional)
    with st.sidebar:
        st.markdown("### 🛠️ Available Tools")
        tools_result = st.session_state.client.list_tools()
        if "error" not in tools_result and "result" in tools_result:
            tools = tools_result["result"]["tools"]
            for tool in tools:
                st.markdown(f"**{tool['name']}**")
                st.markdown(f"_{tool['description']}_")
                st.markdown("---")
        
        st.markdown("### 📜 Recent Queries")
        if st.session_state.messages:
            user_messages = [msg for msg in st.session_state.messages if msg["role"] == "user"]
            for i, message in enumerate(reversed(user_messages[-10:])):  # Show last 10 user messages
                # Create unique key using both index and content hash
                unique_key = f"history_{i}_{hash(message['content'])}"
                if st.button(f"🔄 {message['content'][:50]}...", key=unique_key, use_container_width=True):
                    process_query(message["content"])
                    st.rerun()
    
    # Debug information (remove this later)
    st.sidebar.write(f"Debug - Show overlay: {st.session_state.show_overlay}")
    if hasattr(st.session_state, 'current_result'):
        st.sidebar.write(f"Debug - Has result: {bool(st.session_state.current_result)}")
    
    # Footer
    st.markdown("---")
    st.markdown(
        '<p style="text-align: center; color: #666; font-family: Space Mono;">🌌 Powered by NASA APIs and Model Context Protocol</p>',
        unsafe_allow_html=True
    )

def show_result_overlay():
    """Display result in an overlay popup using Streamlit native components"""
    
    # Create a prominent container that appears like an overlay
    st.markdown("""
    <style>
    .overlay-container {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border: 3px solid rgba(52, 152, 219, 0.8);
        border-radius: 20px;
        padding: 20px;
        margin: 20px 0;
        box-shadow: 0 25px 80px rgba(52, 152, 219, 0.4);
        backdrop-filter: blur(10px);
        position: relative;
        z-index: 100;
    }
    .overlay-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #3498db;
        margin-bottom: 15px;
        text-align: center;
    }
    .overlay-close-area {
        background: rgba(231, 76, 60, 0.1);
        border: 1px solid rgba(231, 76, 60, 0.3);
        border-radius: 10px;
        padding: 10px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create the overlay container
    with st.container():
        st.markdown('<div class="overlay-container">', unsafe_allow_html=True)
        
        # Header with query info
        st.markdown(f'<div class="overlay-header">🚀 NASA Query Results</div>', unsafe_allow_html=True)
        st.markdown(f"**Your Query:** _{st.session_state.current_query}_")
        
        # Close button area
        st.markdown('<div class="overlay-close-area">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("❌ Close Results", key="close_overlay_main", use_container_width=True, type="secondary"):
                st.session_state.show_overlay = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Content area
        if st.session_state.current_result:
            st.markdown("### 📊 Results")
            st.markdown(st.session_state.current_result)
        else:
            st.warning("No result to display")
            # Debug information
            st.write("**Debug Info:**")
            st.write(f"- Query: {st.session_state.get('current_query', 'None')}")
            st.write(f"- Result length: {len(st.session_state.get('current_result', ''))}")
            st.write(f"- Images count: {len(st.session_state.get('current_images', []))}")
            
            if hasattr(st.session_state, 'debug_tool'):
                st.write(f"- Tool called: {st.session_state.debug_tool}")
            
            if hasattr(st.session_state, 'debug_raw_result'):
                with st.expander("Raw API Result"):
                    st.text(st.session_state.debug_raw_result[:1000] + "..." if len(st.session_state.debug_raw_result) > 1000 else st.session_state.debug_raw_result)
            
            if hasattr(st.session_state, 'debug_formatted'):
                with st.expander("Formatted Result"):
                    st.text(st.session_state.debug_formatted[:500] + "..." if len(st.session_state.debug_formatted) > 500 else st.session_state.debug_formatted)
        
        # Images section
        if st.session_state.current_images:
            st.markdown("### 🖼️ NASA Images")
            # Display images in a nice grid
            if len(st.session_state.current_images) == 1:
                st.image(st.session_state.current_images[0], caption="NASA Image", use_container_width=True)
            else:
                for i, img_url in enumerate(st.session_state.current_images):
                    try:
                        st.image(img_url, caption=f"NASA Image {i+1}", use_container_width=True)
                    except Exception as e:
                        st.error(f"Could not load image: {img_url}")
        
        st.markdown("---")
        
        # Bottom close area
        st.markdown('<div class="overlay-close-area">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Done Viewing", key="close_overlay_bottom", use_container_width=True, type="primary"):
                st.session_state.show_overlay = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
