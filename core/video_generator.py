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

subprocess.run(
    [
        "ffmpeg",
        "-loop",
        "1",
        "-i",
        IMAGE_PATH,
        "-i",
        AUDIO_PATH,
        "-c:v",
        "libx264",
        "-tune",
        "stillimage",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-pix_fmt",
        "yuv420p",
        "-shortest",
        OUTPUT_PATH,
    ]
)
print("✅ 動画生成完了:", OUTPUT_PATH)
