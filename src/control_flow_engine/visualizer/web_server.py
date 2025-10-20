#!/usr/bin/env python3
"""
Simple web server for the Control Flow Visualizer.
Serves the HTML visualizer and can regenerate diagrams on demand.
"""

import http.server
import socketserver
import webbrowser
import json
from pathlib import Path
import subprocess
import sys


class VisualizerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=Path(__file__).parent, **kwargs)

    def do_GET(self):
        if self.path == "/api/refresh":
            self.handle_refresh()
        else:
            super().do_GET()

    def handle_refresh(self):
        """Regenerate diagrams from the latest CONTROL_FLOWS_SPEC.md"""
        try:
            # Run the visualizer script
            result = subprocess.run(
                [sys.executable, "control_flow_visualizer.py"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent,
            )

            if result.returncode == 0:
                response = {
                    "status": "success",
                    "message": "Diagrams regenerated successfully",
                    "output": result.stdout,
                }
            else:
                response = {
                    "status": "error",
                    "message": "Failed to regenerate diagrams",
                    "error": result.stderr,
                }
        except Exception as e:
            response = {"status": "error", "message": f"Exception: {str(e)}"}

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())


def main():
    """Start the visualizer web server."""
    port = 8000

    # Find an available port
    while port < 8010:
        try:
            with socketserver.TCPServer(("", port), VisualizerHandler) as httpd:
                print(f"🌐 Control Flow Visualizer Server")
                print(f"📍 Serving at: http://localhost:{port}")
                print(f"📄 Open: http://localhost:{port}/control_flow_visualizer.html")
                print(f"🔄 Refresh API: http://localhost:{port}/api/refresh")
                print(f"⌨️  Press Ctrl+C to stop")

                # Try to open browser automatically
                try:
                    webbrowser.open(
                        f"http://localhost:{port}/control_flow_visualizer.html"
                    )
                except Exception:
                    # Browser open failed, user can open manually
                    pass

                httpd.serve_forever()
        except OSError:
            port += 1

    print("❌ Could not find an available port")


if __name__ == "__main__":
    main()
