#!/usr/bin/env zsh
set -euo pipefail

# 使い方:
#   scripts/make-video-rich.sh "台本テキスト" [背景画像] [出力MP4] [BGM] [ロゴPNG]
#
# 例:
#   scripts/make-video-rich.sh "WANSTAGEの近況！" public/sample.jpg out.mp4 assets/bgm.m4a assets/logo.png

SCRIPT_TEXT="${1:-WANSTAGEのお知らせです。今日もコツコツ行きます。}"
BG_IMAGE="${2:-public/sample.jpg}"
OUT_MP4="${3:-out.mp4}"
BGM_PATH="${4:-}"      # 省略可
LOGO_PATH="${5:-}"     # 省略可

# 0) サンプル背景が無ければ作る（単色）
if [ ! -f "$BG_IMAGE" ]; then
  echo ">> $BG_IMAGE が無いので単色背景を生成します"
  ffmpeg -f lavfi -i color=c=skyblue:s=1200x800 -frames:v 1 "$BG_IMAGE" -y >/dev/null 2>&1
fi

# 1) 台本 → 音声（macOS TTS）
say -v Kyoko "$SCRIPT_TEXT" -o /tmp/voice.aiff
ffmpeg -y -i /tmp/voice.aiff -ar 44100 -ac 2 -b:a 192k /tmp/voice.m4a >/dev/null 2>&1

# 2) 音声長を取得（字幕の終了時刻に使う）
DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 /tmp/voice.m4a)
# 3) 超シンプル字幕（全テキストを0〜DURで1枚）— 後で台本分割に拡張可能
cat > /tmp/subs.srt <<SRT
1
00:00:00,000 --> $(python - <<'PY'
d=float(open(0).read());
h=int(d//3600); m=int((d%3600)//60); s=int(d%60); ms=int((d-int(d))*1000)
print(f"{h:02d}:{m:02d}:{s:02d},{ms:03d}")
PY <<< "$DUR")
$SCRIPT_TEXT
SRT

# 4) フィルタ構築（1080x1920化 → ロゴ → 字幕）
#   入力順: 0:画像 1:音声 2:BGM(任意) 3:ロゴ(任意)
#   映像チェーン: [0:v] scale/pad → [base] → (ロゴあれば overlay) → [v] → subtitles
VID_FILTER="[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2[base]"
if [ -n "$LOGO_PATH" ] && [ -f "$LOGO_PATH" ]; then
  VID_FILTER="${VID_FILTER};[3:v]scale=300:-1[logo];[base][logo]overlay=W-w-40:40[v]"
else
  VID_FILTER="${VID_FILTER};[base]copy[v]"
fi
# 字幕を合成
VID_FILTER="${VID_FILTER};[v]subtitles=/tmp/subs.srt[vout]"

# 5) 音声（BGMありならミックス、なければ音声そのまま）
if [ -n "$BGM_PATH" ] && [ -f "$BGM_PATH" ]; then
  # ボイス1.0、BGM0.15でミックス（簡易ダッキングは後でsidechainに拡張可）
  AUD_FILTER="[1:a]volume=1.0[voice];[2:a]volume=0.15[bgm];[voice][bgm]amix=inputs=2:duration=shortest[aout]"
  ffmpeg -y -loop 1 -i "$BG_IMAGE" -i /tmp/voice.m4a -i "$BGM_PATH" ${LOGO_PATH:+-i "$LOGO_PATH"} \
    -filter_complex "${VID_FILTER};${AUD_FILTER}" \
    -map "[vout]" -map "[aout]" -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest "$OUT_MP4"
else
  ffmpeg -y -loop 1 -i "$BG_IMAGE" -i /tmp/voice.m4a ${LOGO_PATH:+-i "$LOGO_PATH"} \
    -filter_complex "${VID_FILTER}" \
    -map "[vout]" -map 1:a -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest "$OUT_MP4"
fi

echo "✅ Generated: $OUT_MP4"
