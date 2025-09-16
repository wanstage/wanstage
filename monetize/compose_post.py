import json
import os
import pathlib
import shlex
import subprocess

from dotenv import load_dotenv

BASE = pathlib.Path(os.path.expanduser("~/WANSTAGE"))
LOGS = BASE / "logs"
LOGS.mkdir(parents=True, exist_ok=True)
load_dotenv(BASE / ".env")

# 直近生成の meta を読み込み
meta = {"engine": None}
gen_json_path = LOGS / "generated.json"
if gen_json_path.exists():
    try:
        meta = json.loads(gen_json_path.read_text(encoding="utf-8")).get("meta", meta)
    except Exception:
        pass

raw_text = (
    (LOGS / "post_text.txt").read_text(encoding="utf-8").strip()
    if (LOGS / "post_text.txt").exists()
    else "今日の学びをシェア。"
)
promo = os.getenv("PROMO_URL", "").strip()

# Shopify割引（任意）
if os.getenv("SHOPIFY_STORE") and os.getenv("SHOPIFY_ADMIN_TOKEN"):
    try:
        code = subprocess.check_output(
            ["python3", str(BASE / "monetize/shopify_discount.py")], text=True, timeout=60
        ).strip()
        if code:
            sep = "&" if "?" in promo else "?"
            promo = f"{promo}{sep}discount={code}"
    except Exception:
        pass

# アフィ付与
final_url = ""
if promo:
    cmd = f'python3 "{BASE}/monetize/build_affiliate_link.py" "{promo}"'
    try:
        final_url = subprocess.check_output(shlex.split(cmd), text=True).strip()
    except Exception:
        final_url = promo

# Bitly短縮（任意）
if final_url and os.getenv("BITLY_GENERIC_TOKEN"):
    try:
        final_url = subprocess.check_output(
            ["python3", str(BASE / "monetize/bitly_utils.py"), "shorten", final_url], text=True
        ).strip()
    except Exception:
        pass

# A/B
ab = json.loads(
    subprocess.check_output(
        ["python3", str(BASE / "experiments/ab_picker.py"), "multi", final_url or ""], text=True
    )
)
parts = [raw_text, "", ab["cta"], (ab["link_label"] + ": " + final_url) if final_url else ""]
text = "\n".join([p for p in parts if p]).strip()
print(
    json.dumps(
        {"text": text, "link_url": final_url, "variant": ab, "meta": meta}, ensure_ascii=False
    )
)
