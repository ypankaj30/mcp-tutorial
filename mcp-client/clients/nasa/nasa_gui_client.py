#!/usr/bin/env python3
"""
NASA MCP Tkinter GUI Client

A graphical user interface for interacting with NASA's MCP server.
Features:
- Astronomy Picture of the Day viewer
- Mars Rover photo browser
- Near Earth Objects tracker
- Image display and download capabilities
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from datetime import datetime, date, timedelta
import json
import threading
import asyncio
from typing import Dict, Any, Optional, List
import httpx
from PIL import Image, ImageTk
import io
import os
import webbrowser

class NASAMCPClient:
    """NASA MCP client for HTTP communication"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip('/')
        self.request_id = 0
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the NASA MCP server"""
        self.request_id += 1
        message = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": self.request_id
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{self.server_url}/call", json=message)
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                raise Exception(f"Tool call failed: {result['error']}")
            
            return result.get("result", {})
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.server_url}/tools")
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                raise Exception(f"List tools failed: {result['error']}")
            
            return result.get("result", {}).get("tools", [])

class ImageLoader:
    """Utility class for loading and caching images"""
    
    def __init__(self):
        self.cache = {}
    
    async def load_image_from_url(self, url: str, max_size: tuple = (600, 400)) -> Optional[ImageTk.PhotoImage]:
        """Load and resize image from URL"""
        if url in self.cache:
            return self.cache[url]
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # Load image
                image_data = io.BytesIO(response.content)
                pil_image = Image.open(image_data)
                
                # Resize while maintaining aspect ratio
                pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(pil_image)
                self.cache[url] = photo
                
                return photo
                
        except Exception as e:
            print(f"Error loading image from {url}: {e}")
            return None

class NASAGUIApp:
    """Main GUI application for NASA MCP client"""
    
    def __init__(self, server_url: str = "http://localhost:8001"):
        self.server_url = server_url
        self.client = NASAMCPClient(server_url)
        self.image_loader = ImageLoader()
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("NASA MCP Explorer")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.setup_ui()
        
        # Test connection on startup
        self.root.after(100, self.test_connection)
    
    def setup_ui(self):
        """Setup the user interface"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_apod_tab()
        self.create_mars_rover_tab()
        self.create_neo_tab()
        self.create_about_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief='sunken')
        self.status_bar.pack(side='bottom', fill='x')
    
    def create_apod_tab(self):
        """Create Astronomy Picture of the Day tab"""
        self.apod_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.apod_frame, text="🌌 APOD")
        
        # Date selection
        date_frame = ttk.Frame(self.apod_frame)
        date_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(date_frame, text="Date:").pack(side='left')
        self.apod_date_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        date_entry = ttk.Entry(date_frame, textvariable=self.apod_date_var, width=12)
        date_entry.pack(side='left', padx=(5, 0))
        
        ttk.Button(date_frame, text="Today", 
                  command=lambda: self.apod_date_var.set(date.today().strftime("%Y-%m-%d"))).pack(side='left', padx=5)
        ttk.Button(date_frame, text="Random", command=self.random_apod_date).pack(side='left')
        ttk.Button(date_frame, text="Get APOD", command=self.get_apod).pack(side='left', padx=5)
        
        # Content area
        content_frame = ttk.Frame(self.apod_frame)
        content_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Left side - image
        image_frame = ttk.LabelFrame(content_frame, text="Image")
        image_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        self.apod_image_label = ttk.Label(image_frame, text="No image loaded")
        self.apod_image_label.pack(padx=10, pady=10)
        
        # Image controls
        img_controls = ttk.Frame(image_frame)
        img_controls.pack(fill='x', padx=5, pady=5)
        
        self.apod_image_url = tk.StringVar()
        ttk.Button(img_controls, text="Open Full Size", command=self.open_apod_image).pack(side='left')
        ttk.Button(img_controls, text="Save Image", command=self.save_apod_image).pack(side='left', padx=5)
        
        # Right side - info
        info_frame = ttk.LabelFrame(content_frame, text="Information")
        info_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # Title
        self.apod_title_var = tk.StringVar()
        title_label = ttk.Label(info_frame, textvariable=self.apod_title_var, font=('Arial', 12, 'bold'))
        title_label.pack(anchor='w', padx=5, pady=5)
        
        # Explanation
        self.apod_explanation = scrolledtext.ScrolledText(info_frame, wrap='word', height=15)
        self.apod_explanation.pack(fill='both', expand=True, padx=5, pady=5)
    
    def create_mars_rover_tab(self):
        """Create Mars Rover photos tab"""
        self.mars_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.mars_frame, text="🚀 Mars Rovers")
        
        # Controls
        controls_frame = ttk.Frame(self.mars_frame)
        controls_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(controls_frame, text="Rover:").pack(side='left')
        self.rover_var = tk.StringVar(value="curiosity")
        rover_combo = ttk.Combobox(controls_frame, textvariable=self.rover_var, 
                                  values=["curiosity", "opportunity", "spirit", "perseverance", "ingenuity"],
                                  width=12, state="readonly")
        rover_combo.pack(side='left', padx=(5, 10))
        
        ttk.Label(controls_frame, text="Sol:").pack(side='left')
        self.sol_var = tk.StringVar(value="1000")
        sol_entry = ttk.Entry(controls_frame, textvariable=self.sol_var, width=8)
        sol_entry.pack(side='left', padx=(5, 10))
        
        ttk.Label(controls_frame, text="Camera:").pack(side='left')
        self.camera_var = tk.StringVar()
        camera_combo = ttk.Combobox(controls_frame, textvariable=self.camera_var,
                                   values=["", "FHAZ", "RHAZ", "MAST", "CHEMCAM", "MAHLI", "MARDI", "NAVCAM"],
                                   width=10, state="readonly")
        camera_combo.pack(side='left', padx=(5, 10))
        
        ttk.Button(controls_frame, text="Search Photos", command=self.search_mars_photos).pack(side='left', padx=5)
        
        # Photos display
        photos_frame = ttk.LabelFrame(self.mars_frame, text="Photos")
        photos_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create canvas with scrollbar for photos
        canvas_frame = ttk.Frame(photos_frame)
        canvas_frame.pack(fill='both', expand=True)
        
        self.mars_canvas = tk.Canvas(canvas_frame)
        mars_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.mars_canvas.yview)
        self.mars_scrollable_frame = ttk.Frame(self.mars_canvas)
        
        self.mars_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.mars_canvas.configure(scrollregion=self.mars_canvas.bbox("all"))
        )
        
        self.mars_canvas.create_window((0, 0), window=self.mars_scrollable_frame, anchor="nw")
        self.mars_canvas.configure(yscrollcommand=mars_scrollbar.set)
        
        self.mars_canvas.pack(side="left", fill="both", expand=True)
        mars_scrollbar.pack(side="right", fill="y")
    
    def create_neo_tab(self):
        """Create Near Earth Objects tab"""
        self.neo_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.neo_frame, text="🌍 Near Earth Objects")
        
        # Date controls
        date_controls = ttk.Frame(self.neo_frame)
        date_controls.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(date_controls, text="Start Date:").pack(side='left')
        self.neo_start_date = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        ttk.Entry(date_controls, textvariable=self.neo_start_date, width=12).pack(side='left', padx=(5, 10))
        
        ttk.Label(date_controls, text="End Date:").pack(side='left')
        end_date = date.today() + timedelta(days=7)
        self.neo_end_date = tk.StringVar(value=end_date.strftime("%Y-%m-%d"))
        ttk.Entry(date_controls, textvariable=self.neo_end_date, width=12).pack(side='left', padx=(5, 10))
        
        ttk.Button(date_controls, text="This Week", command=self.set_this_week).pack(side='left', padx=5)
        ttk.Button(date_controls, text="Search NEOs", command=self.search_neos).pack(side='left', padx=5)
        
        # Results display
        results_frame = ttk.LabelFrame(self.neo_frame, text="Near Earth Objects")
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.neo_results = scrolledtext.ScrolledText(results_frame, wrap='word')
        self.neo_results.pack(fill='both', expand=True, padx=5, pady=5)
    
    def create_about_tab(self):
        """Create about tab"""
        about_frame = ttk.Frame(self.notebook)
        self.notebook.add(about_frame, text="ℹ️ About")
        
        about_text = """
🚀 NASA MCP Explorer

This application connects to NASA's APIs through a Model Context Protocol (MCP) server
to provide access to fascinating space data and imagery.

Features:
• 🌌 Astronomy Picture of the Day (APOD)
• 🚀 Mars Rover Photo Browser
• 🌍 Near Earth Objects Tracker

Data Sources:
• NASA APOD API
• NASA Mars Rover Photos API
• NASA NeoWs (Near Earth Object Web Service)

MCP Server: NASA tools for space exploration data
GUI Framework: Tkinter with PIL for image handling

⚠️ Note: This application requires an active NASA MCP server
running on the configured URL.

For more information about NASA's APIs, visit:
https://api.nasa.gov/
        """
        
        about_label = ttk.Label(about_frame, text=about_text, justify='left')
        about_label.pack(padx=20, pady=20)
        
        # Connection info
        conn_frame = ttk.LabelFrame(about_frame, text="Connection")
        conn_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(conn_frame, text=f"Server URL: {self.server_url}").pack(anchor='w', padx=10, pady=5)
        
        self.connection_status = tk.StringVar(value="Not connected")
        ttk.Label(conn_frame, textvariable=self.connection_status).pack(anchor='w', padx=10, pady=5)
        
        ttk.Button(conn_frame, text="Test Connection", command=self.test_connection).pack(anchor='w', padx=10, pady=5)
    
    def test_connection(self):
        """Test connection to NASA MCP server"""
        def test():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                tools = loop.run_until_complete(self.client.list_tools())
                self.root.after(0, lambda: self.connection_status.set(f"✅ Connected - {len(tools)} tools available"))
                self.root.after(0, lambda: self.status_var.set("Connected to NASA MCP server"))
            except Exception as e:
                self.root.after(0, lambda: self.connection_status.set(f"❌ Error: {str(e)}"))
                self.root.after(0, lambda: self.status_var.set(f"Connection failed: {str(e)}"))
        
        threading.Thread(target=test, daemon=True).start()
    
    def random_apod_date(self):
        """Set a random date for APOD"""
        import random
        # APOD started June 16, 1995
        start_date = date(1995, 6, 16)
        end_date = date.today()
        
        time_between = end_date - start_date
        days_between = time_between.days
        random_days = random.randrange(days_between)
        random_date = start_date + timedelta(days=random_days)
        
        self.apod_date_var.set(random_date.strftime("%Y-%m-%d"))
    
    def get_apod(self):
        """Get Astronomy Picture of the Day"""
        def fetch():
            try:
                self.root.after(0, lambda: self.status_var.set("Fetching APOD..."))
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                arguments = {}
                apod_date = self.apod_date_var.get().strip()
                if apod_date:
                    arguments["date"] = apod_date
                
                result = loop.run_until_complete(
                    self.client.call_tool("get_astronomy_picture_of_the_day", arguments)
                )
                
                # Parse the result
                content = result.get("content", [])
                if content and content[0].get("text"):
                    text = content[0]["text"]
                    self.parse_apod_response(text)
                
                self.root.after(0, lambda: self.status_var.set("APOD loaded successfully"))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to get APOD: {str(e)}"))
                self.root.after(0, lambda: self.status_var.set("Error loading APOD"))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def parse_apod_response(self, text: str):
        """Parse APOD response text and update UI"""
        lines = text.split('\n')
        title = ""
        explanation = ""
        image_url = ""
        
        # Parse the formatted response
        for line in lines:
            if line.startswith("🏷️ Title:"):
                title = line.split("🏷️ Title:", 1)[1].strip()
            elif line.startswith("📝 Explanation:"):
                # Start collecting explanation
                idx = lines.index(line) + 1
                explanation_lines = []
                while idx < len(lines) and not lines[idx].startswith("🔗"):
                    explanation_lines.append(lines[idx])
                    idx += 1
                explanation = '\n'.join(explanation_lines).strip()
            elif line.startswith("🔗 Image URL:"):
                image_url = line.split("🔗 Image URL:", 1)[1].strip()
        
        # Update UI
        self.root.after(0, lambda: self.apod_title_var.set(title))
        self.root.after(0, lambda: self.update_apod_explanation(explanation))
        self.root.after(0, lambda: self.apod_image_url.set(image_url))
        
        # Load image
        if image_url:
            self.load_apod_image(image_url)
    
    def update_apod_explanation(self, text: str):
        """Update APOD explanation text"""
        self.apod_explanation.delete('1.0', tk.END)
        self.apod_explanation.insert('1.0', text)
    
    def load_apod_image(self, url: str):
        """Load APOD image from URL"""
        def load():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                photo = loop.run_until_complete(self.image_loader.load_image_from_url(url))
                
                if photo:
                    self.root.after(0, lambda: self.apod_image_label.configure(image=photo, text=""))
                    # Keep a reference to prevent garbage collection
                    self.apod_image_label.image = photo
                else:
                    self.root.after(0, lambda: self.apod_image_label.configure(text="Failed to load image"))
                    
            except Exception as e:
                self.root.after(0, lambda: self.apod_image_label.configure(text=f"Error loading image: {str(e)}"))
        
        threading.Thread(target=load, daemon=True).start()
    
    def open_apod_image(self):
        """Open APOD image in browser"""
        url = self.apod_image_url.get()
        if url:
            webbrowser.open(url)
    
    def save_apod_image(self):
        """Save APOD image to file"""
        url = self.apod_image_url.get()
        if not url:
            messagebox.showwarning("Warning", "No image URL available")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG files", "*.jpg"), ("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if filename:
            def save():
                try:
                    import httpx
                    
                    with httpx.Client(timeout=30.0) as client:
                        response = client.get(url)
                        response.raise_for_status()
                        
                        with open(filename, 'wb') as f:
                            f.write(response.content)
                    
                    self.root.after(0, lambda: messagebox.showinfo("Success", f"Image saved to {filename}"))
                    
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to save image: {str(e)}"))
            
            threading.Thread(target=save, daemon=True).start()
    
    def search_mars_photos(self):
        """Search for Mars rover photos"""
        def search():
            try:
                self.root.after(0, lambda: self.status_var.set("Searching Mars photos..."))
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                arguments = {
                    "rover_name": self.rover_var.get(),
                    "sol": int(self.sol_var.get())
                }
                
                camera = self.camera_var.get()
                if camera:
                    arguments["camera"] = camera
                
                result = loop.run_until_complete(
                    self.client.call_tool("search_mars_rover_photos", arguments)
                )
                
                # Parse the result
                content = result.get("content", [])
                if content and content[0].get("text"):
                    text = content[0]["text"]
                    self.display_mars_photos(text)
                
                self.root.after(0, lambda: self.status_var.set("Mars photos loaded"))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to search photos: {str(e)}"))
                self.root.after(0, lambda: self.status_var.set("Error searching photos"))
        
        threading.Thread(target=search, daemon=True).start()
    
    def display_mars_photos(self, text: str):
        """Display Mars rover photos"""
        # Clear previous photos
        for widget in self.mars_scrollable_frame.winfo_children():
            widget.destroy()
        
        # Parse photo URLs from text
        photo_urls = []
        lines = text.split('\n')
        for line in lines:
            if "🔗 URL:" in line:
                url = line.split("🔗 URL:", 1)[1].strip()
                photo_urls.append(url)
        
        # Display photos in grid
        cols = 2
        for i, url in enumerate(photo_urls[:10]):  # Limit to 10 photos
            row = i // cols
            col = i % cols
            
            # Create frame for each photo
            photo_frame = ttk.LabelFrame(self.mars_scrollable_frame, text=f"Photo {i+1}")
            photo_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            
            # Placeholder for image
            img_label = ttk.Label(photo_frame, text="Loading...")
            img_label.pack(padx=5, pady=5)
            
            # Open button
            ttk.Button(photo_frame, text="Open in Browser", 
                      command=lambda u=url: webbrowser.open(u)).pack(pady=2)
            
            # Load image asynchronously
            self.load_mars_photo(img_label, url, (200, 150))
    
    def load_mars_photo(self, label: ttk.Label, url: str, size: tuple):
        """Load a Mars rover photo"""
        def load():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                photo = loop.run_until_complete(self.image_loader.load_image_from_url(url, size))
                
                if photo:
                    self.root.after(0, lambda: label.configure(image=photo, text=""))
                    # Keep reference
                    label.image = photo
                else:
                    self.root.after(0, lambda: label.configure(text="Failed to load"))
                    
            except Exception as e:
                self.root.after(0, lambda: label.configure(text="Error"))
        
        threading.Thread(target=load, daemon=True).start()
    
    def set_this_week(self):
        """Set date range to this week"""
        start = date.today()
        end = start + timedelta(days=7)
        self.neo_start_date.set(start.strftime("%Y-%m-%d"))
        self.neo_end_date.set(end.strftime("%Y-%m-%d"))
    
    def search_neos(self):
        """Search for Near Earth Objects"""
        def search():
            try:
                self.root.after(0, lambda: self.status_var.set("Searching Near Earth Objects..."))
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                arguments = {
                    "start_date": self.neo_start_date.get(),
                    "end_date": self.neo_end_date.get()
                }
                
                result = loop.run_until_complete(
                    self.client.call_tool("get_near_earth_objects", arguments)
                )
                
                # Display result
                content = result.get("content", [])
                if content and content[0].get("text"):
                    text = content[0]["text"]
                    self.root.after(0, lambda: self.update_neo_results(text))
                
                self.root.after(0, lambda: self.status_var.set("NEO search completed"))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to search NEOs: {str(e)}"))
                self.root.after(0, lambda: self.status_var.set("Error searching NEOs"))
        
        threading.Thread(target=search, daemon=True).start()
    
    def update_neo_results(self, text: str):
        """Update NEO results display"""
        self.neo_results.delete('1.0', tk.END)
        self.neo_results.insert('1.0', text)
    
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

def main():
    """Main entry point"""
    import sys
    
    # Get server URL from command line or use default
    server_url = "http://localhost:8001"
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    
    print(f"Starting NASA MCP GUI Client")
    print(f"Server URL: {server_url}")
    print("Note: Make sure the NASA MCP HTTP server is running!")
    
    try:
        app = NASAGUIApp(server_url)
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
