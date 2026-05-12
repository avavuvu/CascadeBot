#!/usr/bin/env python3
"""
Thought Server — sidecar HTTP server for the Cascade visualiser.

Agents POST their thought process here as JSON arrays.
The Svelte visualiser GETs them to display alongside the game.

Endpoints:
  POST /thoughts        { "player": "RED"|"BLUE", "turn": int, "thoughts": [...] }
  GET  /thoughts        returns all stored thought payloads
  GET  /thoughts/latest returns only the most recently posted payload
  POST /thoughts/clear  wipe all stored thoughts (e.g. on new game)

CORS is open so the Vite dev server (any port) can reach it.
"""

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

THOUGHT_SERVER_PORT = 8767

_thoughts: list[dict] = []
_lock = threading.Lock()


class ThoughtHandler(BaseHTTPRequestHandler):
    # ------------------------------------------------------------------ #
    #  Routing                                                             #
    # ------------------------------------------------------------------ #

    def do_OPTIONS(self):
        """Preflight CORS requests from the browser."""
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path == "/thoughts":
            self._post_thoughts()
        elif self.path == "/thoughts/clear":
            self._clear_thoughts()
        else:
            self._respond(404, {"error": "not found"})

    def do_GET(self):
        if self.path == "/thoughts":
            self._get_all_thoughts()
        elif self.path == "/thoughts/latest":
            self._get_latest_thought()
        else:
            self._respond(404, {"error": "not found"})

    # ------------------------------------------------------------------ #
    #  Handlers                                                            #
    # ------------------------------------------------------------------ #

    def _post_thoughts(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = self.rfile.read(length)
            data = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            self._respond(400, {"error": "invalid JSON"})
            return

        if not isinstance(data.get("thoughts"), list):
            self._respond(400, {"error": "missing 'thoughts' array"})
            return

        with _lock:
            _thoughts.append(data)

        print(
            f"  [thoughts] turn={data.get('turn', '?')} "
            f"player={data.get('player', '?')} "
            f"items={len(data['thoughts'])}",
            flush=True,
        )
        self._respond(201, {"ok": True, "stored": len(_thoughts)})

    def _clear_thoughts(self):
        with _lock:
            _thoughts.clear()
        print("  [thoughts] cleared", flush=True)
        self._respond(200, {"ok": True})

    def _get_all_thoughts(self):
        with _lock:
            payload = list(_thoughts)
        self._respond(200, payload)

    def _get_latest_thought(self):
        with _lock:
            payload = _thoughts[-1] if _thoughts else None
        self._respond(200, payload or {})

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _respond(self, code: int, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else THOUGHT_SERVER_PORT
    server = HTTPServer(("localhost", port), ThoughtHandler)
    print(f"* Thought server listening on http://localhost:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n* Thought server stopped.", flush=True)
