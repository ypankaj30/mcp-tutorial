#!/usr/bin/env python3
"""
Quick test to verify Gemini integration for NASA web app
"""

import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv

def test_gemini_integration():
    """Test if Gemini is properly configured"""
    print("🧪 Testing Gemini Integration for NASA Web App...")
    
    # Load environment variables
    load_dotenv(dotenv_path="../../../.env")
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment variables")
        print("💡 Please add your Gemini API key to the .env file")
        return False
    
    print(f"✅ Found Gemini API key: {api_key[:10]}...")
    
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        print("✅ Gemini model initialized successfully")
        
        # Test a simple query
        test_query = "Show me today's astronomy picture"
        prompt = f"""
        You are a NASA query parser. Determine which NASA tool to call.
        
        Available tools:
        - get_astronomy_picture_of_the_day
        - search_mars_rover_photos  
        - get_near_earth_objects
        
        User query: "{test_query}"
        
        Respond with JSON: {{"tool_name": "exact_tool_name", "arguments": {{}}, "reasoning": "brief explanation"}}
        """
        
        print("🚀 Testing query parsing...")
        response = model.generate_content(prompt)
        print(f"✅ Gemini response: {response.text[:100]}...")
        
        print("\n🎉 All tests passed! Gemini is ready for NASA web app.")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Gemini: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_gemini_integration()
    sys.exit(0 if success else 1)
