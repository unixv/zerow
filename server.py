#!/usr/bin/env python3
"""Zero-dependency HTTP server for the Pi Zero W game."""
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "static"
HOST = os.environ.get("ZEROW_HOST", "127.0.0.1")
PORT = int(os.environ.get("ZEROW_PORT", "8080"))

class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()

if __name__ == "__main__":
    print(f"Serving Zero W Snake on http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), partial(Handler, directory=str(ROOT))).serve_forever()
