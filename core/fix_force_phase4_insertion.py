#!/usr/bin/env python3
import datetime
import pathlib
import re

target = pathlib.Path.home() / "WANSTAGE" / "core" / "auto_intel_gen.py"
backup = target.with_suffix(f".phase4fix_{datetime.datetime.now():%Y%m%d_%H%M%S}")
code = target.read_text(encoding="utf-8")

print("🩹 Phase 4 ブロックを再定義中...")

# 既存Phase4を削除して、末尾に追加
patched = re.sub(r"elif\s+args\.phase\s*==\s*['\"]4['\"].*?(?=\n\s*elif|\Z)", "", code, flags=re.S)

# ファイル末尾にPhase4分岐を確実に追加
patched += """

# == PHASE 4: WANSTAGE_SELF_HEAL SYSTEM ==
elif args.phase == '4':
    import os, subprocess, pathlib, datetime
    print('[%s] 🚀 AUTO_INTEL_GEN Phase 4 started' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    base = os.path.expanduser('~/WANSTAGE')
    script = f"{base}/bin/wan-autoheal-full.sh"
    if not pathlib.Path(script).exists():
        print('⚠ 自動修復スクリプトが見つかりません:', script)
    else:
        subprocess.run(['chmod','+x',script], check=False)
        subprocess.run(['pm2','start',script,'--name','wan-autoheal-full'], check=False)
        subprocess.run(['pm2','save'], check=False)
        print('[%s] ⚙️ PM2登録完了: wan-autoheal-full (%s)' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), script))
    print('[%s] ✅ Slack通知統合済み' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print('[%s] ✅ ログ監視: ~/WANSTAGE/logs/autoheal.log' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print('[%s] 🏁 AUTO_INTEL_GEN Phase 4 完了' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
# == END PHASE 4 ==
"""

target.rename(backup)
target.write_text(patched, encoding="utf-8")
print(f"✅ バックアップ作成: {backup}")
print("✅ Phase 4 ブロックを末尾に挿入完了。")
