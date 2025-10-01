#!/usr/bin/env bash
set -euo pipefail

SCRIPT_TEXT="${1:-WANSTAGEのお知らせです。今日もコツコツやっていきます。}"
BG_IMAGE="${2:-public/sample.jpg}"
OUT_MP4="${3:-out.mp4}"

# 1) 台本→音声（macOS TTS）
say -v Kyoko "$SCRIPT_TEXT" -o /tmp/voice.aiff
ffmpeg -y -i /tmp/voice.aiff -ar 44100 -ac 2 -b:a 192k /tmp/voice.m4a >/dev/null 2>&1

# 2) 画像→縦1080x1920 へフィット
ffmpeg -y -loop 1 -i "$BG_IMAGE" -i /tmp/voice.m4a \
  -c:a aac -b:a 192k -c:v libx264 -pix_fmt yuv420p \
  -tune stillimage -shortest \
  -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2" \
  "$OUT_MP4"

echo "✅ Generated: $OUT_MP4"
