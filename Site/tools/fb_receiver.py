"""Tiny local receiver for Facebook photo links (see the pahibalo-photos skill).

    python tools/fb_receiver.py      # leave running; then from the Facebook page:
    location.href = "http://127.0.0.1:8799/save?name=<list>&d=" + encodeURIComponent(JSON.stringify({key: imageUrl}))

Saves _downloads/fb-lists/<list>.json. Then: python tools/fb_sheet.py <list> <folder under _downloads>
"""
import json, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "_downloads" / "fb-lists"
OUT.mkdir(parents=True, exist_ok=True)


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        msg = "ok"
        if u.path == "/save" and "name" in q and "d" in q:
            name = "".join(c for c in q["name"][0] if c.isalnum() or c in "-_")
            data = json.loads(q["d"][0])
            (OUT / f"{name}.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
            msg = f"saved {name}: {len(data)} items"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(f"<!doctype html><title>{msg}</title><p>{msg}</p>".encode())

    def log_message(self, *a):
        pass


HTTPServer(("127.0.0.1", 8799), H).serve_forever()
