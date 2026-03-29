from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from ai_ads.agents import SearchAgentOrchestrator, ad_from_dict, search_from_dict, to_json
from ai_ads.storage import AdStore

store = AdStore("ads.db")
orchestrator = SearchAgentOrchestrator(store)


class AppHandler(BaseHTTPRequestHandler):
    def _send_json(self, data: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = to_json(data)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json({"status": "ok", "message": "AI Ads prototype is running"})
            return

        if self.path == "/ads":
            rows = [dict(row) for row in store.all_ads()]
            self._send_json({"count": len(rows), "ads": rows})
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length else b"{}"

        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON body"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/ads":
            try:
                ad = ad_from_dict(payload)
                ad_id = orchestrator.ingest_ad(ad)
                self._send_json({"message": "ad created", "ad_id": ad_id}, status=HTTPStatus.CREATED)
            except KeyError as exc:
                self._send_json({"error": f"missing field: {exc}"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/search":
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
