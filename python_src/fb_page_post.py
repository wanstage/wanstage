#!/usr/bin/env python3
import datetime as dt
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional

import requests

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

API = "https://graph.facebook.com/v24.0"

PAGE_ID = os.getenv("FB_PAGE_ID", "")
PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN", "")


def _need(v: str, name: str):
    if not v:
        raise RuntimeError(f"missing env: {name}")


def _unix(dt_obj: dt.datetime) -> int:
    # UTCでUNIX秒へ
    if dt_obj.tzinfo is None:
        dt_obj = dt_obj.replace(tzinfo=dt.timezone.utc)
    return int(dt_obj.timestamp())


def _ensure_window(unix_ts: int):
    """10分後〜30日後の範囲チェック"""
    now = int(time.time())
    min_ok = now + 10 * 60
    max_ok = now + 30 * 24 * 60 * 60
    if not (min_ok <= unix_ts <= max_ok):
        raise ValueError("scheduled_publish_time must be 10 minutes to 30 days from now")


def schedule_feed_post(
    message: str,
    link: str | None = None,
    when_unix: int | None = None,
    geo_countries: list[str] | None = None,
    geo_cities: list[dict] | None = None,
):
    """
    - message: 本文
    - link: 同時に貼るURL（任意）
    - when_unix: 未来時刻（UNIX秒）。Noneなら10分後に自動設定
    - geo_*: ターゲティング（countries=["JP"], cities=[{"key":"296875"}] など）
             ※ 国と都市を同時指定すると重複エラーになる場合あり
    """
    _need(PAGE_ID, "FB_PAGE_ID")
    _need(PAGE_TOKEN, "FB_PAGE_TOKEN")

    if when_unix is None:
        when_unix = int(time.time()) + 10 * 60  # デフォルト10分後
    _ensure_window(when_unix)

    payload = {
        "message": message,
        "published": "false",
        "scheduled_publish_time": str(when_unix),
        "access_token": PAGE_TOKEN,
    }
    if link:
        payload["link"] = link

    # ターゲティング（必要なときだけ）


def build_targeting(
    geo_countries: Optional[List[str]] = None,
    geo_cities: Optional[List[str]] = None,
    age_min: Optional[int] = None,
    age_max: Optional[int] = None,
    genders: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Build Facebook Ads targeting dict safely.
    None や空は無視して、必要キーだけを組み立てる。
    """
    targeting: Dict[str, Any] = {}
    if geo_countries:
        targeting.setdefault("geo_locations", {})["countries"] = geo_countries
    if geo_cities:
        targeting.setdefault("geo_locations", {})["cities"] = geo_cities
    if age_min is not None:
        targeting["age_min"] = age_min
    if age_max is not None:
        targeting["age_max"] = age_max
    if genders:
        targeting["genders"] = genders
    return targeting


# 既存コード側では:
# targeting = build_targeting(geo_countries, geo_cities, age_min, age_max, genders)


def schedule_photo_post(
    photo_url: str,
    caption: str,
    when_unix: int | None = None,
):
    """
    - photo_url: 直接アクセス可能な画像URL
    - caption: キャプション
    - when_unix: 未来時刻（UNIX秒）。Noneなら10分後
    """
    _need(PAGE_ID, "FB_PAGE_ID")
    _need(PAGE_TOKEN, "FB_PAGE_TOKEN")

    if when_unix is None:
        when_unix = int(time.time()) + 10 * 60
    _ensure_window(when_unix)

    url = f"{API}/{PAGE_ID}/photos"
    payload = {
        "url": photo_url,
        "caption": caption,
        "published": "false",
        "scheduled_publish_time": str(when_unix),
        "access_token": PAGE_TOKEN,
    }
    r = requests.post(url, data=payload)
    try:
        j = r.json()
    except Exception:
        j = {"raw": r.text}
    if r.status_code != 200 or "id" not in j:
        return {"ok": False, "status": r.status_code, "resp": j}

    # j には photo_id / post_id が入る
    post_id = j.get("post_id")
    confirm = None
    if post_id:
        r2 = requests.get(
            f"{API}/{post_id}",
            params={
                "fields": "id,scheduled_publish_time,is_published,message",
                "access_token": PAGE_TOKEN,
            },
        )
        try:
            confirm = r2.json()
        except Exception:
            confirm = {"raw": r2.text}

    return {"ok": True, "status": r.status_code, "resp": j, "confirmed": confirm}


def list_scheduled(limit: int = 10):
    """未公開（scheduled）投稿の確認"""
    _need(PAGE_ID, "FB_PAGE_ID")
    _need(PAGE_TOKEN, "FB_PAGE_TOKEN")
    url = f"{API}/{PAGE_ID}/feed"
    r = requests.get(
        url,
        params={
            "fields": "id,message,created_time,scheduled_publish_time,is_published",
            "limit": str(limit),
            "access_token": PAGE_TOKEN,
        },
    )
    try:
        return {"ok": True, "resp": r.json(), "status": r.status_code}
    except Exception:
        return {"ok": False, "resp": r.text, "status": r.status_code}


if __name__ == "__main__":
    # 使い方:
    #   1) テキスト/リンク: python3 fb_page_post.py feed "本文" "https://example.com" 20m
    #   2) 写真:           python3 fb_page_post.py photo "https://picsum.photos/1080" "キャプション" 45m
    #   3) 一覧:           python3 fb_page_post.py list
    argv = sys.argv[1:]
    if not argv:
        print("usage: fb_page_post.py feed|photo|list ...", file=sys.stderr)
        sys.exit(1)

    kind = argv[0]

    def parse_when(s: str | None):
        if not s:
            return None
        s = s.strip().lower()
        now = int(time.time())
        if s.endswith("m"):
            return now + int(s[:-1]) * 60
        if s.endswith("h"):
            return now + int(s[:-1]) * 3600
        if s.endswith("d"):
            return now + int(s[:-1]) * 86400
        # 数字ならUNIX秒とみなす
        if s.isdigit():
            return int(s)
        raise ValueError("time format: 20m / 2h / 1d / <unix>")

    if kind == "feed":
        # feed "message" [link_or_-] [when]
        msg = argv[1]
        link = None if len(argv) < 3 or argv[2] == "-" else argv[2]
        when = parse_when(argv[3]) if len(argv) >= 4 else None
        out = schedule_feed_post(msg, link=link, when_unix=when)
        print(json.dumps(out, ensure_ascii=False, indent=2))

    elif kind == "photo":
        # photo "image_url" "caption" [when]
        img = argv[1]
        cap = argv[2]
        when = parse_when(argv[3]) if len(argv) >= 4 else None
        out = schedule_photo_post(img, cap, when_unix=when)
        print(json.dumps(out, ensure_ascii=False, indent=2))

    elif kind == "list":
        out = list_scheduled()
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print("unknown kind", file=sys.stderr)
        sys.exit(2)
