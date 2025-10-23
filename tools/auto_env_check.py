import subprocess
import sys

modules = [
    "moviepy",
    "imageio",
    "imageio_ffmpeg",
    "numpy",
    "soundfile",
    "gtts",
    "tqdm",
    "pandas",
    "requests",
    "yaml",
]
missing = []
for mod in modules:
    try:
        __import__(mod)
    except ImportError:
        print(f"📦 {mod} が見つかりません → インストール対象")
        missing.append(mod)
if missing:
    print("🧠 自動修復実行中...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade"] + missing)
else:
    print("✅ 全ての依存関係が正常です！")
