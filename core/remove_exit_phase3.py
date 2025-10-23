#!/usr/bin/env python3
import datetime
import pathlib
import re

target = pathlib.Path.home() / "WANSTAGE" / "core" / "auto_intel_gen.py"
backup = target.with_suffix(f".noexit_{datetime.datetime.now():%Y%m%d_%H%M%S}")
code = target.read_text(encoding="utf-8")

print("🩹 Phase3 での premature exit を削除中...")
patched = re.sub(
    r"(if\s+args\.phase\s*==\s*['\"]3['\"].*?)sys\.exit\(.*?\)", r"\1", code, flags=re.S
)

target.rename(backup)
target.write_text(patched, encoding="utf-8")
print(f"✅ バックアップ作成: {backup}")
print("✅ sys.exit() を削除し、Phase4 へ到達可能にしました。")
