import os
import re

p = os.path.expanduser("~/WANSTAGE/python_src/wanstage_insta_gen_post.py")
src = open(p, "r", encoding="utf-8").read()

# 1) import threading… の直後に helper を挿入（重複防止）
helper = r'''
# --- preview helper (macOS) ---
import subprocess, shutil

def preview_image(path: str | None):
    """WAN_PREVIEW_MODE=open|quicklook|none で画像プレビュー制御"""
    import os
    if not path or not os.path.exists(path):
        print(f"[preview] file not found or empty: {path}")
        return
    mode = os.getenv("WAN_PREVIEW_MODE", "open").lower()
    if mode == "none":
        print(f"[preview] skipped (WAN_PREVIEW_MODE=none) -> {path}")
        return
    try:
        if mode == "quicklook" and shutil.which("qlmanage"):
            subprocess.Popen(["qlmanage","-p",path],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[preview] quicklook -> {path}")
        else:
            subprocess.run(["open", path], check=False)
            print(f"[preview] open -> {path}")
    except Exception as e:
        print(f"[preview] error: {e}")
# --- end preview helper ---
'''.lstrip(
    "\n"
)

if "def preview_image(" not in src:
    src = re.sub(r"(import threading.*?\n)", r"\1" + helper, src, count=1, flags=re.S)

# 2) Instagram 直前にプレビュー呼び出し（重複防止）
call_line = 'preview_image(os.getenv("WAN_LAST_IMAGE", "media_path_placeholder.jpg"))\n    '
if call_line not in src:
    src = re.sub(
        r"(result = post_to_instagram\(caption\))",
        call_line + r"\1",
        src,
        count=1,
        flags=re.S,
    )

bak = p + ".bak"
open(bak, "w", encoding="utf-8").write(src)
os.replace(bak, p)
print("Patched:", p)
