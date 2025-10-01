#!/bin/zsh
set -eu
text="${1:?usage: tts_ja.sh 'テキスト'}"
out="${2:-media/audio/voiceover.aiff}"
# Kyoko は macOS の日本語音声
say -v Kyoko "$text" -o "$out"
echo "[TTS] generated: $out"
