#!/bin/bash
set -euo pipefail

BASE="$HOME/WANSTAGE"
CORE="$BASE/core"
BIN="$BASE/bin"
LOG="$BASE/logs"
mkdir -p "$CORE" "$BIN" "$LOG"

# --- 音声合成クライアント ---
cat <<PYEOF > "$CORE/voicevox_client.py"
import requests
import soundfile as sf

class VoiceVoxClient:
    def __init__(self, base_url="http://127.0.0.1:50021"):
        self.base_url = base_url

    def synthesize(self, text, speaker=1, output_path="voice.wav"):
        res = requests.post(f"{self.base_url}/audio_query", params={"text": text, "speaker": speaker})
        res.raise_for_status()
        query = res.json()
        res = requests.post(f"{self.base_url}/synthesis", params={"speaker": speaker}, json=query)
        res.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(res.content)
PYEOF

# --- 動画生成スクリプト ---
cat <<PYEOF > "$CORE/video_generator.py"
import os
import subprocess
from voicevox_client import VoiceVoxClient

SCRIPT_PATH = os.path.expanduser("~/WANSTAGE/logs/video_script.txt")
AUDIO_PATH = os.path.expanduser("~/WANSTAGE/logs/voice.wav")
OUTPUT_PATH = os.path.expanduser("~/WANSTAGE/logs/output.mp4")
IMAGE_PATH = os.path.expanduser("~/WANSTAGE/assets/default_bg.jpg")

client = VoiceVoxClient()
with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
    text = f.read()

client.synthesize(text, output_path=AUDIO_PATH)

subprocess.run([
    "ffmpeg", "-loop", "1", "-i", IMAGE_PATH,
    "-i", AUDIO_PATH, "-c:v", "libx264", "-tune", "stillimage",
    "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p",
    "-shortest", OUTPUT_PATH
])
print("✅ 動画生成完了:", OUTPUT_PATH)
PYEOF

# --- 実行シェル ---
cat <<'SHEOF' > "$BIN/wan_phase9_video.sh"
#!/bin/bash
set -e

BASE="$HOME/WANSTAGE"
LOG="$BASE/logs"
mkdir -p "$LOG"
echo "こんにちは、これはWANSTAGE自動動画生成テストです。" > "$LOG/video_script.txt"

python3 "$BASE/core/video_generator.py"
SHEOF

chmod +x "$BIN/wan_phase9_video.sh"
echo "✅ 生成完了: $BIN/wan_phase9_video.sh"
echo "▶️ 実行するには: bash $BIN/wan_phase9_video.sh"
