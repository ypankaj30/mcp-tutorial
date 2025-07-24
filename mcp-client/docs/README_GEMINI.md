# MCP Gemini Client Setup

This is a Gemini-compatible version of the MCP client that uses Google's Generative AI instead of Anthropic's Claude.

## Setup

### 1. Install Dependencies

You'll need to install the Google Generative AI library in addition to the existing dependencies:

```bash
pip install google-generativeai
```

Or add it to your `pyproject.toml`:

```toml
dependencies = [
    "anthropic>=0.57.1",
    "mcp>=1.10.1", 
    "python-dotenv>=1.1.1",
    "google-generativeai>=0.8.0",
]
```

### 2. Get Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create or select a project
3. Generate an API key
4. Set the environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Or add it to your `.env` file:

```
GEMINI_API_KEY=your-api-key-here
```

### 3. Usage

Run the Gemini client the same way as the original client:

```bash
python client_gemini.py path/to/your/mcp_server.py
```

## Key Differences from Anthropic Client

1. **API Library**: Uses `google-generativeai` instead of `anthropic`
2. **Model**: Uses `gemini-1.5-flash` (better free tier rate limits than gemini-1.5-pro)
3. **Function Calling**: Adapts MCP tools to Gemini's function calling format
4. **Message Format**: Converts between MCP/Anthropic message format and Gemini's chat format
5. **Environment Variable**: Requires `GEMINI_API_KEY` instead of Anthropic's API key
6. **Rate Limiting**: Includes automatic retry logic with exponential backoff for rate limits

## Features

- ✅ Connects to MCP servers
- ✅ Lists available tools
- ✅ Function calling support
- ✅ Interactive chat loop
- ✅ Error handling
- ✅ Multi-turn conversations with tool usage

## Troubleshooting

1. **API Key Issues**: Make sure `GEMINI_API_KEY` is set correctly
2. **Import Errors**: Install `google-generativeai` with pip
3. **Rate Limits**: Gemini has rate limits; add delays if needed
4. **Tool Schema**: Some complex tool schemas might need adjustment for Gemini's format
