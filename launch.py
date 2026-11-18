import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class HealthHandler(BaseHTTPRequestHandler):
      def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"M.O.M. online")

      def log_message(self, *_args):
                pass


def serve_health():
      port = int(os.getenv("PORT", "10000"))
      ThreadingHTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()


threading.Thread(target=serve_health, daemon=True).start()

import main  # noqa: E402  - starts the Discord bot after the health server
