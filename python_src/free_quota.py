import datetime
import json
import logging
import os
from typing import Optional

from account import get_user_plan

log = logging.getLogger(__name__)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USAGE_DIR = os.path.join(BASE, "data", "usage")


def _today_key():
    return datetime.datetime.now().strftime("%Y%m%d")


def _file_for(date_key: str):
    return os.path.join(USAGE_DIR, f"{date_key}.json")


def _load(date_key: str):
    p = _file_for(date_key)
    if not os.path.exists(p):
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.error("usage load error: %s", e)
        return {}


def _save(date_key: str, data: dict):
    os.makedirs(USAGE_DIR, exist_ok=True)
    p = _file_for(date_key)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, p)


def _limit_for_plan(plan: str, env_limit: int) -> int:
    if plan == "pro":
        return max(env_limit, env_limit * 10)  # 例：proはfreeの10倍
    return env_limit


def can_use_post(user_id: str, env_limit: Optional[int] = None) -> bool:
    if env_limit is None:
        try:
            env_limit = (
                env_limit
                if env_limit is not None
                else int(os.environ.get("FREE_DAILY_POST_LIMIT", "3"))
            )
        except Exception:
            env_limit = 3
    plan = get_user_plan(user_id)
    limit = _limit_for_plan(plan, env_limit)
    today = _today_key()
    data = _load(today)
    used = int(data.get(user_id, 0))
    return used < limit


def increment_user_usage(user_id: str):
    today = _today_key()
    data = _load(today)
    data[user_id] = int(data.get(user_id, 0)) + 1
    _save(today, data)
