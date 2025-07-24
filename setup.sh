#!/bin/bash

# MCP Tutorial Setup Script
# This script demonstrates the unified environment setup

echo "🚀 MCP Tutorial - Unified Environment Setup"
echo "============================================"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the mcp-tutorial root directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    uv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "🔧 Installing dependencies..."
source .venv/bin/activate
uv pip install -e .

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Please create one with your API keys:"
    echo "   GEMINI_API_KEY=your_key_here"
    echo "   ANTHROPIC_API_KEY=your_key_here"
else
    echo "✅ Environment file found"
fi

echo ""
echo "🎉 Setup complete! You can now run:"
echo ""
echo "   # Activate environment"
echo "   source .venv/bin/activate"
echo ""
echo "   # Test local client"
echo "   cd mcp-client/clients/gemini"
echo "   uv run python client_gemini_local.py ../../../mcp-server/weather_server.py"
echo ""
echo "   # Test HTTP remote (in 2 terminals)"
echo "   cd mcp-client/server_wrapper"
echo "   uv run python mcp_http_server_sync_remote.py ../../mcp-server/weather_server.py 8000"
echo ""
echo "   cd mcp-client/clients/gemini"
echo "   uv run python client_gemini_http_remote.py http://localhost:8000"
echo ""
