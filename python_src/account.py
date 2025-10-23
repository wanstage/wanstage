import json
import logging
import os
import time

log = logging.getLogger(__name__)
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USERS_FILE = os.path.join(BASE, "data", "users.json")

DEFAULT_PLAN = "free"  # "pro" などに拡張可


def _load():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.error("users.json load error: %s", e)
        return {}


def _save(d):
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    tmp = USERS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    os.replace(tmp, USERS_FILE)


def get_user_plan(user_id: str) -> str:
    d = _load()
    return d.get(user_id, {}).get("plan", DEFAULT_PLAN)


def set_user_plan(user_id: str, plan: str) -> None:
    d = _load()
    d.setdefault(user_id, {})["plan"] = plan
    d[user_id]["updated_at"] = int(time.time())
    _save(d)
