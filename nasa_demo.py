#!/usr/bin/env python3
"""
NASA MCP Demo Launcher

This script starts the NASA MCP server ecosystem:
1. NASA MCP Server (stdio)
2. NASA HTTP Server Wrapper (port 8001)
3. NASA GUI Client (Tkinter)

Usage:
    python nasa_demo.py [--server-only] [--client-only] [--port PORT]
"""

import argparse
import subprocess
import sys
import time
import os
import signal
import threading
import webbrowser
from pathlib import Path

def find_project_root():
    """Find the project root directory"""
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return Path.cwd()

def start_nasa_server(project_root: Path, port: int = 8001):
    """Start the NASA HTTP server wrapper"""
    server_script = project_root / "mcp-client" / "server_wrapper" / "nasa_http_server_sync.py"
    
    if not server_script.exists():
        print(f"❌ Server script not found: {server_script}")
        return None
    
    print(f"🚀 Starting NASA HTTP Server on port {port}...")
    
    # Change to server directory and start
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    
    process = subprocess.Popen([
        sys.executable, str(server_script), "--port", str(port)
    ], cwd=str(project_root / "mcp-client" / "server_wrapper"), env=env)
    
    return process

def start_gui_client(server_url: str):
    """Start the NASA GUI client"""
    project_root = find_project_root()
    client_script = project_root / "mcp-client" / "clients" / "nasa" / "nasa_gui_client.py"
    
    if not client_script.exists():
        print(f"❌ Client script not found: {client_script}")
        return None
    
    print(f"🖥️  Starting NASA GUI Client...")
    print(f"   Server URL: {server_url}")
    
    # Change to client directory and start
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    
    process = subprocess.Popen([
        sys.executable, str(client_script), server_url
    ], cwd=str(project_root / "mcp-client"), env=env)
    
    return process

def wait_for_server(port: int, timeout: int = 30):
    """Wait for server to be ready"""
    import socket
    import time
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.5)
    return False

def main():
    parser = argparse.ArgumentParser(description="NASA MCP Demo Launcher")
    parser.add_argument("--server-only", action="store_true", help="Start only the server")
    parser.add_argument("--client-only", action="store_true", help="Start only the client")
    parser.add_argument("--port", type=int, default=8001, help="Server port (default: 8001)")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser for API docs")
    
    args = parser.parse_args()
    
    project_root = find_project_root()
    server_url = f"http://localhost:{args.port}"
    
    print("🌌 NASA MCP Demo Launcher")
    print(f"📁 Project root: {project_root}")
    print("=" * 50)
    
    processes = []
    
    try:
        # Start server if requested
        if not args.client_only:
            server_process = start_nasa_server(project_root, args.port)
            if server_process:
                processes.append(("NASA HTTP Server", server_process))
                
                # Wait for server to be ready
                print("⏳ Waiting for server to start...")
                if wait_for_server(args.port, timeout=30):
                    print(f"✅ Server is ready at {server_url}")
                    
                    # Open API docs in browser
                    if not args.no_browser:
                        time.sleep(1)  # Give server a moment
                        docs_url = f"{server_url}/docs"
                        print(f"📖 Opening API docs: {docs_url}")
                        webbrowser.open(docs_url)
                else:
                    print("❌ Server failed to start within timeout")
                    return 1
        
        # Start client if requested
        if not args.server_only:
            if args.client_only:
                # If client-only, wait a moment for user to start server manually
                print(f"ℹ️  Make sure NASA HTTP Server is running at {server_url}")
                time.sleep(2)
            
            client_process = start_gui_client(server_url)
            if client_process:
                processes.append(("NASA GUI Client", client_process))
        
        if not processes:
            print("❌ No processes started")
            return 1
        
        print("\n🎉 NASA MCP Demo is running!")
        print("\n📋 Active processes:")
        for name, process in processes:
            print(f"   • {name} (PID: {process.pid})")
        
        print(f"\n🌐 Server API docs: {server_url}/docs")
        print("🖥️  GUI client should open automatically")
        print("\n💡 Usage tips:")
        print("   • Try getting today's Astronomy Picture of the Day")
        print("   • Browse Mars Rover photos from different sols and cameras")
        print("   • Check Near Earth Objects for upcoming week")
        print("\n⚠️  Note: NASA APIs use DEMO_KEY with rate limits")
        print("   For production use, get a free API key at https://api.nasa.gov/")
        
        print("\n🛑 Press Ctrl+C to stop all processes")
        
        # Wait for processes
        try:
            while True:
                # Check if any process has died
                for name, process in processes:
                    if process.poll() is not None:
                        print(f"⚠️  {name} has stopped")
                        return_code = process.returncode
                        if return_code != 0:
                            print(f"❌ {name} exited with code {return_code}")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    finally:
        # Clean shutdown
        for name, process in processes:
            if process.poll() is None:  # Still running
                print(f"🛑 Stopping {name}...")
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"⚡ Force killing {name}...")
                    process.kill()
                except Exception as e:
                    print(f"⚠️  Error stopping {name}: {e}")
        
        print("✅ All processes stopped")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
