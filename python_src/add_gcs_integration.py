import datetime
import os
import re

TARGET = os.path.expanduser("~/WANSTAGE/python_src/wanstage_insta_gen_post.py")
src = open(TARGET, "r", encoding="utf-8").read()
bak = TARGET + ".gcs.bak." + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
open(bak, "w", encoding="utf-8").write(src)

helper = r'''
# --- GCS helper (upload -> public URL) ---
from google.cloud import storage

def _gcs_client():
    return storage.Client()  # uses ADC from gcloud

def gcs_upload_local(local_path: str, bucket_name: str | None = None, dst_prefix: str = "wanstage/insta") -> str:
    """
    ローカル画像を GCS へアップロードして公開URLを返す。
    返り値例: https://storage.googleapis.com/<bucket>/<dst_key>
    """
    import os, time, mimetypes, pathlib
    if not os.path.exists(local_path):
        raise FileNotFoundError(local_path)

    bucket_name = bucket_name or os.getenv("GCS_BUCKET")
    if not bucket_name:
        raise RuntimeError("GCS_BUCKET が未設定です")

    client = _gcs_client()
    bucket = client.bucket(bucket_name)

    # 拡張子とキー
    p = pathlib.Path(local_path)
    ts = time.strftime("%Y%m%d_%H%M%S")
    dst_key = f"{dst_prefix}/{ts}_{p.name}"

    blob = bucket.blob(dst_key)
    ctype, _ = mimetypes.guess_type(str(p))
    if ctype is None:
        ctype = "application/octet-stream"

    # アップロード
    blob.upload_from_filename(str(p), content_type=ctype)

    # 公開（バケットが public なら不要だが、個別でも可）
    try:
        blob.make_public()
    except Exception:
        # すでに public なバケットなら OK
        pass

    public_base = os.getenv("GCS_PUBLIC_BASE", f"https://storage.googleapis.com/{bucket_name}")
    return f"{public_base}/{dst_key}"
# --- end GCS helper ---
'''.lstrip(
    "\n"
)

# 1) helper が未挿入なら、import 群の後ろに追加
if "def gcs_upload_local(" not in src:
    src = re.sub(
        r"(\nfrom google import genai\s*\n)",
        r"\1" + helper + "\n",
        src,
        count=1,
        flags=re.S,
    )

# 2) Instagram 投稿前に、ローカルパスだったら GCS へ上げて WAN_IMAGE_URL を差し替え
inject = r"""
    # --- auto GCS upload if local path ---
    _m = media_path_or_url
    if not (_m.startswith("http://") or _m.startswith("https://")):
        try:
            gcs_url = gcs_upload_local(_m, os.getenv("GCS_BUCKET"))
            os.environ["WAN_IMAGE_URL"] = gcs_url
            _m = gcs_url
            print(f"[GCS] uploaded -> {gcs_url}")
        except Exception as e:
            raise RuntimeError(f"GCS upload failed: {e}")
    # --- end auto GCS ---
"""

# post_to_instagram の 画像URL決定 直後に差し込み（not http のブランチより前）
pattern = r"(\n\s*# 画像URLを決定\s*\n\s*m = media_path_or_url\s*\n)"
if re.search(pattern, src):
    src = re.sub(pattern, r"\1" + inject, src, count=1)
else:
    # フォールバック: 関数先頭に差す
    src = re.sub(
        r'(def post_to_instagram\(.*?\):\s*"""[\s\S]*?"""\s*\n\s*import os, requests\s*\n[\s\S]*?\n)',
        r"\1" + inject,
        src,
        count=1,
    )

# 3) 成功/失敗ログを既存の init_log_db() を使って保存（既にあれば多重挿入しない）
log_snippet = r"""
    # --- post log ---
    try:
        conn = init_log_db()
        cur = conn.cursor()
        try_image_url = os.getenv("WAN_IMAGE_URL")
        # 直近レスポンスを JSON で格納
        cur.execute(
            "INSERT INTO post_log(timestamp, image_path, image_url, caption, response_json, success) VALUES (?, ?, ?, ?, ?, ?)",
            (
                datetime.datetime.utcnow().isoformat(),
                str(media_path_or_url),
                try_image_url if (try_image_url and try_image_url.startswith("http")) else _m,
                caption,
                json.dumps(locals().get("j2") or locals().get("j1") or {}, ensure_ascii=False),
                1  # 成功扱い（例外に落ちたら下の except で失敗ログ）
            )
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print("[log] failed to write log:", e)
    # --- end post log ---
"""
if "INSERT INTO post_log(" not in src:
    # publish 成功の return の直前に入れる
    src = re.sub(
        r"(return\s*\{\s*\'ok\':\s*True,\s*\'id\':\s*j2\.get\(\'id\'\),[\s\S]*?\}\s*\n)",
        log_snippet + r"\1",
        src,
        count=1,
    )

# 4) 失敗時ログ（publish 失敗 raise の直前）
fail_snippet = r"""
        try:
            conn = init_log_db(); cur = conn.cursor()
            try_image_url = os.getenv("WAN_IMAGE_URL")
            cur.execute(
                "INSERT INTO post_log(timestamp, image_path, image_url, caption, response_json, success) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    datetime.datetime.utcnow().isoformat(),
                    str(media_path_or_url),
                    try_image_url if (try_image_url and try_image_url.startswith("http")) else _m,
                    caption,
                    json.dumps(j2, ensure_ascii=False),
                    0
                )
            )
            conn.commit(); conn.close()
        except Exception as _:
            pass
"""
src = re.sub(
    r"(raise RuntimeError\(f\'Publish failed:[\s\S]*?\)\n)",
    fail_snippet + r"\1",
    src,
    count=1,
)

open(TARGET, "w", encoding="utf-8").write(src)
print("Patched with GCS integration:", TARGET)
print("Backup at:", bak)
