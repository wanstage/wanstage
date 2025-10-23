import csv
import os
import shlex
import subprocess
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent
BIN = BASE / "bin"
OUT = BASE / "out"
LOG = BASE / "logs"
load_dotenv(BASE / ".env")


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def slack(msg):
    subprocess.run(
        f"python3 {shlex.quote(str(BIN / 'slack_notify.py'))} {shlex.quote(msg)}",
        shell=True,
    )


def pick_img():
    r = subprocess.run(
        f"python3 {shlex.quote(str(BIN / 'image_picker.py'))}",
        shell=True,
        capture_output=True,
        text=True,
    )
    return r.stdout.strip()


def ab(key):
    return subprocess.run(
        f"python3 {shlex.quote(str(BIN / 'ab_pick.py'))} {key}",
        shell=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def main():
    style = ab("AB_STYLES")
    seconds = ab("AB_VIDEO_SECONDS")
    window = ab("AB_POST_WINDOWS")
    img1 = pick_img()
    if not img1:
        slack("⚠️ 画像見つからず（IMAGE_DIRSを確認）")
        return
    # 詩生成
    poem_cmd = f"python3 {shlex.quote(str(BIN / 'generate_poem_from_image.py'))} {shlex.quote(img1)} {shlex.quote(style)}"
    poem = sh(poem_cmd).stdout.strip()
    pf = OUT / "poems" / f"poem_{int(time.time())}.txt"
    pf.parent.mkdir(parents=True, exist_ok=True)
    pf.write_text(poem, encoding="utf-8")
    # 動画（最大3枚）
    imgs = [img1]
    for _ in range(10):
        j = pick_img()
        if j and j not in imgs:
            imgs.append(j)
        if len(imgs) >= 3:
            break
    vid_cmd = [
        "python3",
        str(BIN / "create_slideshow_video.py"),
        *imgs,
        str(pf),
        seconds,
    ]
    vid = subprocess.run(vid_cmd, capture_output=True, text=True).stdout.strip()
    if vid.endswith(".mp4"):
        slack(f"🎬 動画生成: {vid}")
    else:
        slack("❌ 動画生成に失敗")
        vid = ""
    # 投稿（有効化時のみ）
    ig_id = ""
    yt_id = ""
    if os.getenv("ENABLE_INSTAGRAM", "false").lower() == "true":
        # Instagramは公開画像URLが必要（S3/CF Images等のURLを渡してください）
        # ここでは投稿せず、キャプション例を通知
        slack(f"📝 IGキャプション案:\n{poem[:1900]}")
    if os.getenv("ENABLE_YOUTUBE", "false").lower() == "true" and vid:
        yt = sh(
            f"python3 {shlex.quote(str(BIN / 'youtube_upload.py'))} {shlex.quote(vid)} {shlex.quote('WANSTAGE 詩スライド')} {shlex.quote(poem[:4500])} {shlex.quote('wanstage,poem,photo')}"
        )
        yt_id = yt.stdout.strip()
        if yt_id:
            slack(f"📺 YouTube: https://youtu.be/{yt_id}")
    # KPI
    if yt_id:
        subprocess.run(f"python3 {shlex.quote(str(BIN / 'kpi_logger.py'))} yt {yt_id}", shell=True)
    # ログ
    csvp = LOG / "runs_api.csv"
    new = not csvp.exists()
    with csvp.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(
                [
                    "ts",
                    "style",
                    "seconds",
                    "window",
                    "img1",
                    "poem_file",
                    "video",
                    "ig_media_id",
                    "yt_video_id",
                ]
            )
        w.writerow(
            [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                style,
                seconds,
                window,
                img1,
                str(pf),
                vid,
                ig_id,
                yt_id,
            ]
        )
    print("✅ done.")


if __name__ == "__main__":
    main()
