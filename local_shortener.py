import json
import os
import threading
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

app = FastAPI()

BASE = os.path.expanduser("~/WANSTAGE")
DATA = os.path.join(BASE, "data")
os.makedirs(DATA, exist_ok=True)
DB_LINKS = os.path.join(DATA, "links.json")  # code -> long_url
DB_CLICKS = os.path.join(DATA, "clicks.json")  # code -> {"total":int,"byDay":{YYYY-MM-DD:int}}

_lock = threading.Lock()


def _load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def load_links():
    return _load(DB_LINKS, {})


def save_links(d):
    with _lock:
        _save(DB_LINKS, d)


def load_clicks():
    return _load(DB_CLICKS, {})


def save_clicks(d):
    with _lock:
        _save(DB_CLICKS, d)


class CreateReq(BaseModel):
    url: str
    code: str | None = None


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.post("/admin/create")
def admin_create(req: CreateReq, request: Request):
    # 認証（簡易）
    token = os.getenv("ADMIN_TOKEN", "set-me")
    if request.headers.get("authorization") != f"Bearer {token}":
        raise HTTPException(401, "unauthorized")

    long_url = (req.url or "").strip()
    if not long_url:
        long_url = req.url

    if not long_url:
        raise HTTPException(400, "url required")

    links = load_links()
    code = req.code
    if not code:
        import secrets

        alphabet = "abcdefghjkmnpqrstuvwxyz23456789"
        code = "".join(secrets.choice(alphabet) for _ in range(6))
    if code in links:
        raise HTTPException(409, "code exists")

    links[code] = req.url
    save_links(links)
    return {"code": code, "link": f"http://127.0.0.1:8000/{code}", "long_url": req.url}


@app.get("/admin/stats")
def stats(code: str, request: Request):
    token = os.getenv("ADMIN_TOKEN", "set-me")
    if request.headers.get("authorization") != f"Bearer {token}":
        raise HTTPException(401, "unauthorized")
    links = load_links()
    clicks = load_clicks()
    return {
        "code": code,
        "long_url": links.get(code),
        "stats": clicks.get(code, {"total": 0, "byDay": {}}),
    }


@app.get("/admin/stats/all")
def stats_all(request: Request):
    token = os.getenv("ADMIN_TOKEN", "set-me")
    if request.headers.get("authorization") != f"Bearer {token}":
        raise HTTPException(401, "unauthorized")
    return {"links": load_links(), "clicks": load_clicks()}


@app.head("/{code}")
def head_redirect(code: str):
    if code not in load_links():
        raise HTTPException(404)
    return {}


@app.get("/{code}")
def go(code: str, request: Request):
    links = load_links()
    long_url = links.get(code)
    if not long_url:
        raise HTTPException(404)

    clicks = load_clicks()
    day = time.strftime("%Y-%m-%d")
    c = clicks.get(code, {"total": 0, "byDay": {}})
    c["total"] += 1
    c["byDay"][day] = c["byDay"].get(day, 0) + 1
    clicks[code] = c
    save_clicks(clicks)

    return RedirectResponse(long_url, status_code=302)
