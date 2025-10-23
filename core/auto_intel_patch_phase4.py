#!/usr/bin/env python3
import datetime
import pathlib
import re

base = pathlib.Path.home() / "WANSTAGE" / "core"
target = base / "auto_intel_gen.py"
backup = target.with_suffix(f".bak_{datetime.datetime.now():%Y%m%d_%H%M%S}")
code = target.read_text(encoding="utf-8")

# --- Phase4セクション存在チェック ---
if "--phase=4" in code or "Phase 4" in code:
    print("✅ Phase 4 セクションはすでに存在します。パッチ不要。")
else:
    print("🌀 Phase 4 セクションを追加します...")
    patched = re.sub(
        r"(if\s+args\.phase\s*==\s*['\"]3['\"]:.*?)(\n\s*#\s*==\s*END\s*PHASE\s*3)",
        r"\1\2\n\n    elif args.phase == '4':\n        print('[%s] 🚀 AUTO_INTEL_GEN Phase 4 started' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))\n        import subprocess, os\n        base=os.environ.get('HOME')+'/WANSTAGE'\n        script=f'{base}/bin/wan-autoheal-full.sh'\n        if not pathlib.Path(script).exists():\n            print('⚠ 自動修復スクリプトが見つかりません:', script)\n        else:\n            subprocess.run(['chmod','+x',script], check=False)\n            subprocess.run(['pm2','start',script,'--name','wan-autoheal-full'], check=False)\n            subprocess.run(['pm2','save'], check=False)\n            print('[%s] ⚙️ PM2登録完了: wan-autoheal-full (%s)' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), script))\n        print('[%s] ✅ Slack通知統合済み' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))\n        print('[%s] ✅ ログ監視: ~/WANSTAGE/logs/autoheal.log' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))\n        print('[%s] 🏁 AUTO_INTEL_GEN Phase 4 完了' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))",
        code,
        flags=re.S,
    )
    target.rename(backup)
    target.write_text(patched, encoding="utf-8")
    print(f"✅ バックアップ作成: {backup}")
    print("✅ Phase 4 パッチ適用完了。")
