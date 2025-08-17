#!/usr/bin/env python3
"""
NASA Streamlit Web App Launcher

This script launches the NASA Streamlit web application.
Make sure the NASA HTTP server is running before starting this app.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("🚀 NASA Space Explorer Web App")
    print("=" * 40)
    
    # Get the directory of this script
    script_dir = Path(__file__).parent.absolute()
    app_file = script_dir / "nasa_streamlit_app.py"
    
    if not app_file.exists():
        print(f"❌ Streamlit app not found: {app_file}")
        sys.exit(1)
    
    print("📋 Prerequisites:")
    print("   1. NASA HTTP Server should be running on http://localhost:8001")
    print("   2. Install dependencies: pip install -r requirements.txt")
    print()
    print("🌐 Starting Streamlit web app...")
    print("   Access the app at: http://localhost:8501")
    print("   Press Ctrl+C to stop")
    print()
    
    try:
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(app_file),
            "--server.port=8501",
            "--server.address=localhost",
            "--theme.base=dark"
        ], cwd=script_dir)
    except KeyboardInterrupt:
        print("\n🛑 Web app stopped")
    except Exception as e:
        print(f"❌ Error running web app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
