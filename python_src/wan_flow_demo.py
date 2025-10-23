#!/usr/bin/env python3
import datetime
import json
import os
import shutil
import subprocess
from pathlib import Path

from dotenv import load_dotenv

# ---- 設定読み込み ----
load_dotenv(os.path.expanduser("~/WANSTAGE/.env"))
OUT_DIR = Path(os.getenv("OUT_DIR", str(Path.home() / "WANSTAGE/out/insta")))
OUT_DIR.mkdir(parents=True, exist_ok=True)
PREVIEW = os.getenv("WAN_PREVIEW_MODE", "open").lower()  # open/quicklook/none
IG_MODE = os.getenv("IG_MODE", "mock").lower()  # mock/live
DEFAULT_HASHTAGS = os.getenv("DEFAULT_HASHTAGS", "").strip()


# ---- プレビュー ----
def preview_image(path: Path | str | None):
    if not path:
        print("[preview] no path")
        return
    p = Path(path)
    if not p.exists():
        print(f"[preview] missing: {p}")
        return
    if PREVIEW == "none":
        print(f"[preview] skipped (WAN_PREVIEW_MODE=none) -> {p}")
        return
    try:
        if PREVIEW == "quicklook" and shutil.which("qlmanage"):
            subprocess.Popen(
                ["qlmanage", "-p", str(p)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print(f"[preview] quicklook -> {p}")
        else:
            subprocess.run(["open", str(p)], check=False)
            print(f"[preview] open -> {p}")
    except Exception as e:
        print("[preview] error:", e)


# ---- Gemini(ダミー) ----
# 実運用に差し替える場合：google-genai で API 呼び出し→ text を返す
def generate_caption(prompt: str) -> str:
    base = f"今日のひとこと：{prompt.strip()} "
    tags = f"\n\n{DEFAULT_HASHTAGS}" if DEFAULT_HASHTAGS else ""
    return base + tags


# ---- 画像生成（ImageMagick を呼ぶ）----
def generate_image(text: str) -> Path:
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = OUT_DIR / f"post_{now}.jpg"
    cmd = [
        "magick",
        "-size",
        "1024x1024",
        "gradient:#eeeeff-#cceeff",
        "-gravity",
        "center",
        "-fill",
        "black",
        "-pointsize",
        "36",
        "-annotate",
        "0",
        text[:90],
        str(out),
    ]
    subprocess.run(cmd, check=True)
    return out


# ---- Instagram 投稿（モック/本番）----
def post_to_instagram(image_path: Path, caption: str) -> dict:
    if IG_MODE == "mock":
        payload = {
            "mode": "mock",
            "image": str(image_path),
            "caption": caption[:120] + ("…" if len(caption) > 120 else ""),
        }
        print("[IG][mock] 投稿シミュレーション:", json.dumps(payload, ensure_ascii=False))
        return {"ok": True, "mock": True, "id": "mock_12345"}
    else:
        # TODO: ここに Graph API 実投稿（media→publish）を接続
        # 例: os.getenv('IG_BUSINESS_ID'), os.getenv('FB_PAGE_TOKEN') を使用
        print("[IG][live] 実投稿stub: 実装箇所に到達。環境変数と認可を確認してください。")
        return {"ok": False, "mock": False, "reason": "not-implemented"}


def main():
    print("[flow] start")

    # 1) Gemini(ダミー)でキャプション生成
    prompt = "柔らかな朝の光と静かなコーヒータイム"
    caption = generate_caption(prompt)
    print("[flow] caption generated")

    # 2) 画像生成・保存
    img = generate_image("やわらかな朝")
    print(f"[flow] image saved -> {img}")

    # 3) プレビュー
    preview_image(img)

    # 4) Instagram 投稿
    result = post_to_instagram(img, caption)
    print("[flow] post result:", result)
    print("[flow] done")


if __name__ == "__main__":
    main()
