from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from ai_ads.agents import SearchAgentOrchestrator, ad_from_dict, search_from_dict, to_json
from ai_ads.storage import AdStore

store = AdStore("ads.db")
orchestrator = SearchAgentOrchestrator(store)
WEB_DIR = Path(__file__).parent / "web"


class AppHandler(BaseHTTPRequestHandler):
    def _send_json(self, data: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = to_json(data)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        route = urlparse(self.path).path

        if route == "/":
            self._send_file(WEB_DIR / "index.html", "text/html; charset=utf-8")
            return

        if route == "/health":
            self._send_json({"status": "ok", "message": "AI Ads prototype is running"})
            return

        if route == "/ads":
            rows = [dict(row) for row in store.all_ads()]
            self._send_json({"count": len(rows), "ads": rows})
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        route = urlparse(self.path).path
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length else b"{}"

        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON body"}, status=HTTPStatus.BAD_REQUEST)
            return

        if route == "/ads":
            try:
                ad = ad_from_dict(payload)
                ad_id = orchestrator.ingest_ad(ad)
                self._send_json({"message": "ad created", "ad_id": ad_id}, status=HTTPStatus.CREATED)
            except KeyError as exc:
                self._send_json({"error": f"missing field: {exc}"}, status=HTTPStatus.BAD_REQUEST)
            return

        if route == "/search":
            try:
                request = search_from_dict(payload)
                result = orchestrator.search(request)
                self._send_json(result)
            except KeyError as exc:
                self._send_json({"error": f"missing field: {exc}"}, status=HTTPStatus.BAD_REQUEST)
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)


def run() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", 8000), AppHandler)
    print("Server running on http://localhost:8000")
    server.serve_forever()


if __name__ == "__main__":
    run()
