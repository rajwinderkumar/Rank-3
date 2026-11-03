"""Rank Wise Flask API — run from the backend folder: python app.py"""

from __future__ import annotations

import json
import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from seo import run_audit

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "audits.json"
FRONTEND = ROOT.parent  # rank-wise/ (static files)

app = Flask(__name__, static_folder=None)
CORS(app, resources={r"/api/*": {"origins": "*"}})


def _load() -> list:
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save(items: list) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(items[:100], ensure_ascii=False, indent=2), encoding="utf-8")


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "service": "Rank Wise"})


@app.post("/api/audit")
def audit():
    body = request.get_json(silent=True) or {}
    url = (body.get("url") or "").strip()
    try:
        result = run_audit(url)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {e}"}), 500

    items = _load()
    items = [i for i in items if i.get("id") != result["id"]]
    items.insert(0, result)
    _save(items)
    return jsonify(result)


@app.get("/api/audit/<audit_id>")
def get_audit(audit_id: str):
    for item in _load():
        if item.get("id") == audit_id:
            return jsonify(item)
    return jsonify({"error": "Audit not found"}), 404


@app.get("/api/history")
def history():
    items = _load()
    slim = [
        {
            "id": i.get("id"),
            "url": i.get("url"),
            "fetchedUrl": i.get("fetchedUrl"),
            "score": i.get("score"),
            "status": i.get("status"),
            "grade": i.get("grade"),
            "analyzedAt": i.get("analyzedAt"),
            "sample": i.get("sample", False),
        }
        for i in items
    ]
    return jsonify(slim)


# Serve frontend when API and static are run together (optional)
@app.get("/")
def index():
    return send_from_directory(FRONTEND, "index.html")


@app.get("/history.html")
def history_page():
    return send_from_directory(FRONTEND, "history.html")


@app.get("/favicon.svg")
def favicon():
    return send_from_directory(FRONTEND, "favicon.svg")


@app.get("/css/<path:filename>")
def css(filename: str):
    return send_from_directory(FRONTEND / "css", filename)


@app.get("/js/<path:filename>")
def js(filename: str):
    return send_from_directory(FRONTEND / "js", filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
