import json
import pathlib
import subprocess
import sys

root = pathlib.Path(__file__).resolve().parents[1]
p_json = root / "data/outputs/posts_next.json"
work = root / "media/work"
work.mkdir(parents=True, exist_ok=True)
outdir = root / "media/video"
outdir.mkdir(parents=True, exist_ok=True)

slot = int(sys.argv[1]) if len(sys.argv) > 1 else 1
data = json.loads(p_json.read_text(encoding="utf-8"))
row = next((r for r in data if int(r["slot"]) == slot), data[0])

title = row["title"]
body = row["body"]
image = row["image"]  # リモートURLでも ffmpeg で読み込み可（https 対応ビルド）
voice = root / "media/audio/test.aiff"
if not voice.exists():
    # ない場合はダミー無音3秒
    subprocess.run(
        [
            "ffmpeg",
            "-f",
            "lavfi",
            "-t",
            "3",
            "-i",
            "anullsrc=r=44100:cl=stereo",
            "-y",
            str(voice),
        ],
        check=True,
    )

# テロップ文
caption = f"{title}\n{body}"
caption = caption.replace('"', '\\"')
txt = work / "caption.txt"
txt.write_text(caption, encoding="utf-8")

# 出力
out = outdir / f"post_slot{slot}.mp4"

# 画像→15秒の動画＋テロップ＋音声合成
# - vf drawtext はデフォルトフォント使用（日本語は環境依存。必要ならフォントパス指定）
cmd = [
    "ffmpeg",
    "-loop",
    "1",
    "-i",
    image,
    "-i",
    str(voice),
    "-t",
    "15",
    "-vf",
    f"drawtext=textfile='{txt}':fontcolor=white:fontsize=36:box=1:boxcolor=0x00000088:boxborderw=12:x=(w-text_w)/2:y=h-200",
    "-c:v",
    "libx264",
    "-pix_fmt",
    "yuv420p",
    "-c:a",
    "aac",
    "-shortest",
    "-y",
    str(out),
]
subprocess.run(cmd, check=True)
print(f"[VIDEO] -> {out}")
