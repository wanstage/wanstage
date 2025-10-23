#!/usr/bin/env python3
import datetime
import pathlib
import re

target = pathlib.Path.home() / "WANSTAGE" / "core" / "auto_intel_gen.py"
backup = target.with_suffix(f".argfix_{datetime.datetime.now():%Y%m%d_%H%M%S}")
code = target.read_text(encoding="utf-8")

# --- argparse構造を確認 ---
if "add_argument('--phase'" in code:
    print("✅ --phase オプションはすでに存在しています。修正不要。")
else:
    print("🩹 add_argument('--phase') を追加します...")
    patched = re.sub(
        r"(parser\s*=\s*argparse\.ArgumentParser\(.*?\)\n)",
        r"\1    parser.add_argument('--phase', default='3', help='実行フェーズ指定 (1〜4)')\n",
        code,
        flags=re.S,
    )
    target.rename(backup)
    target.write_text(patched, encoding="utf-8")
    print(f"✅ バックアップ作成: {backup}")
    print("✅ --phase 引数パッチ適用完了。")
