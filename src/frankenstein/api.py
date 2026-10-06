from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
import json

from .engine import FrankensteinEngine
from .types import WorldEvent


class APIServer:
    def __init__(self, engine: FrankensteinEngine, host: str = "127.0.0.1", port: int = 8765, token: str | None = None):
        if host not in {"127.0.0.1", "localhost", "::1"} and not token:
            raise ValueError("a bearer token is required for non-loopback binding")
        self.engine = engine
        self.host = host
        self.port = port
        self.token = token
        outer = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "FrankensteinHTTP/0.1"

            def log_message(self, format, *args):
                return

            def _authorized(self) -> bool:
                if not outer.token:
                    return True
                return self.headers.get("Authorization", "") == f"Bearer {outer.token}"

            def _json(self, code: int, payload):
                data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)

            def _body(self):
                length = int(self.headers.get("Content-Length", "0"))
                if length > 1_000_000:
                    raise ValueError("request body too large")
                return json.loads(self.rfile.read(length) or b"{}")

            def do_GET(self):
                if not self._authorized():
                    return self._json(401, {"error": "unauthorized"})
                path = urlparse(self.path).path
                if path == "/health":
                    return self._json(200, {"ok": True})
                if path == "/status":
                    return self._json(200, outer.engine.status())
                return self._json(404, {"error": "not found"})

            def do_POST(self):
                if not self._authorized():
                    return self._json(401, {"error": "unauthorized"})
                try:
                    body = self._body()
                    path = urlparse(self.path).path
                    if path == "/chat":
                        actor = str(body.get("actor_id", "user"))
                        text = str(body.get("text", ""))
                        return self._json(200, {"text": outer.engine.chat(actor, text)})
                    if path == "/event":
                        event = WorldEvent(
                            summary=str(body.get("summary", "")),
                            actor_id=body.get("actor_id"),
                            tags=tuple(str(x) for x in body.get("tags", [])),
                            salience=float(body.get("salience", 0.5)),
                            valence=float(body.get("valence", 0.0)),
                            arousal=float(body.get("arousal", 0.0)),
                            metadata=dict(body.get("metadata", {})),
                        )
                        stored = outer.engine.observe(event)
                        return self._json(201, {"event_id": stored.event_id, "seq": stored.seq})
                    if path == "/outcome":
                        stored = outer.engine.record_outcome(
                            str(body.get("action_name", "")),
                            reward=float(body.get("reward", 0.0)),
                            summary=str(body.get("summary", "")),
                            cause_ids=tuple(str(x) for x in body.get("cause_ids", [])),
                        )
                        return self._json(201, {"event_id": stored.event_id, "seq": stored.seq})
                    if path == "/verify":
                        report = outer.engine.store.verify_integrity()
                        return self._json(200 if report.ok else 409, {"ok": report.ok, "checked_events": report.checked_events, "errors": report.errors})
                    return self._json(404, {"error": "not found"})
                except (ValueError, KeyError, TypeError) as exc:
                    return self._json(400, {"error": str(exc)})
                except Exception:
                    return self._json(500, {"error": "internal server error"})

        self.httpd = ThreadingHTTPServer((host, port), Handler)

    def serve_forever(self):
        self.httpd.serve_forever()

    def shutdown(self):
        self.httpd.shutdown()
