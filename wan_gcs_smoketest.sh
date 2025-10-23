#!/usr/bin/env bash
set -euo pipefail

: "${GCS_BUCKET:?Set GCS_BUCKET (e.g. export GCS_BUCKET=my-bucket)}"
GCS_DIR="${GCS_DIR:-wanstage/test}"
OUT="${OUT:-$HOME/out_gcs_smoke.jpg}"

command -v gcloud >/dev/null || { echo "gcloud not found"; exit 1; }
command -v gsutil >/dev/null || { echo "gsutil not found"; exit 1; }
command -v magick >/dev/null || { echo "ImageMagick (magick) not found"; exit 1; }
command -v sqlite3 >/dev/null || true

echo "== 1) make test image =="
magick -size 800x500 gradient: -gravity center -pointsize 22 -annotate 0 "WANSTAGE GCS SMOKE" "$OUT"
echo "image: $OUT"

echo "== 2) upload to GCS =="
TS=$(date +%Y%m%d_%H%M%S)
OBJ="$GCS_DIR/smoke_${TS}.jpg"
gsutil cp -n "$OUT" "gs://$GCS_BUCKET/$OBJ" >/dev/null
URL="https://storage.googleapis.com/$GCS_BUCKET/$OBJ"
echo "uploaded: $URL"

export WAN_IMAGE_URL="$URL"

echo "== 3) init SQLite (if needed) and dry-run post =="
python3 - <<'PY'
import os, json, datetime, sqlite3
p = os.path.expanduser('~/WANSTAGE/python_src/wanstage_insta_gen_post.py')
ns = {}
with open(p, 'r', encoding='utf-8') as f:
    code = f.read()
exec(code, ns, ns)

# 3-1) DB init
conn = ns['init_log_db']()
conn.close()

# 3-2) caption (失敗時はフォールバック)
prompt = "短いポスト用キャプションを1行で。"
try:
    caption = ns['generate_caption'](prompt)
except Exception as e:
    print("[caption] fallback due to:", e)
    caption = "Test post #wanstage"

# 3-3) dry-run投稿（Graph API呼ばずに戻る）
url = os.getenv('WAN_IMAGE_URL')
result = ns['post_to_instagram'](url, caption, publish=False, dry_run=True)
print("[dry-run result]", json.dumps(result, ensure_ascii=False))

# 3-4) ログ挿入
img = os.path.expanduser('~/out_gcs_smoke.jpg')
db_path = os.path.expanduser('~/WANSTAGE/post_log.sqlite3')
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS post_log(
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    image_path TEXT,
    image_url TEXT,
    caption TEXT,
    response_json TEXT,
    success INTEGER
)""")
cur.execute("INSERT INTO post_log(timestamp,image_path,image_url,caption,response_json,success) VALUES (?,?,?,?,?,?)",
    (datetime.datetime.utcnow().isoformat(), img, url, caption, json.dumps(result, ensure_ascii=False), 1 if result.get("ok") else 0))
conn.commit(); conn.close()
print("[log] inserted one row ->", db_path)
PY

echo "== 4) show last log rows =="
if [ -f "$HOME/WANSTAGE/post_log.sqlite3" ]; then
  sqlite3 "$HOME/WANSTAGE/post_log.sqlite3" 'SELECT id, substr(timestamp,1,19), success FROM post_log ORDER BY id DESC LIMIT 3;' || true
else
  echo "no sqlite db found"
fi

echo "== DONE =="
