"""A local email provider with a real HTTP API, for the lab.

POST /v1/emails with a JSON body {"to": ..., "subject": ...} and an Idempotency-Key header sends
one email and answers 202 with its id. Like real providers, it remembers each key for a day: a
request that repeats a key gets the first answer again and sends nothing.

faults scripts what goes wrong for each recipient, one entry per request:
  "lost"         the email is sent, then the connection drops before the answer arrives
  "unavailable"  503, nothing is sent
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class EmailAPI:
    def __init__(self, faults: dict[str, list[str]] | None = None) -> None:
        self.faults = {to: list(script) for to, script in (faults or {}).items()}
        self.keys: dict[str, str] = {}
        self.sent: list[tuple[str, str]] = []
        self.requests = 0
        self.lock = threading.Lock()
        api = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                message = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                status, body = api.handle(message, self.headers.get("Idempotency-Key"))
                if status == 0:  # the answer is lost: close the connection without one
                    self.close_connection = True
                    return
                data = json.dumps(body).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, format: str, *args: object) -> None:
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/v1/emails"

    def handle(self, message: dict, key: str | None) -> tuple[int, dict]:
        with self.lock:
            self.requests += 1
            script = self.faults.get(message["to"])
            fault = script.pop(0) if script else "ok"
            if fault == "unavailable":
                return 503, {"error": "service unavailable"}
            if key is None or key not in self.keys:
                self.sent.append((message["to"], message["subject"]))
                result = f"em_{len(self.sent):04d}"
                if key is not None:
                    self.keys[key] = result
            else:
                result = self.keys[key]
            return (0, {}) if fault == "lost" else (202, {"id": result})

    def __enter__(self) -> "EmailAPI":
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.server.shutdown()
        self.server.server_close()

    def count(self, to: str) -> int:
        return sum(1 for recipient, _ in self.sent if recipient == to)
