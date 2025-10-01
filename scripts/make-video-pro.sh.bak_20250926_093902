#!/usr/bin/env bash
set -euo pipefail

# 使い方:
#   scripts/make-video-pro.sh "台本テキスト" [背景画像] [出力MP4] [BGM] [ロゴPNG]
# 例:
#   scripts/make-video-pro.sh "今週の進捗まとめ" public/sample.jpg out.mp4

SCRIPT_TEXT="${1:-WANSTAGEのお知らせです。今日もコツコツ行きます。}"
BG_IMAGE="${2:-public/sample.jpg}"
OUT_MP4="${3:-out.mp4}"
BGM_PATH="${4:-}"      # 任意（無ければ自動合成）
LOGO_PATH="${5:-}"     # 任意

W=1080; H=1920

# 背景なければ単色作成
if [ ! -f "$BG_IMAGE" ]; then
  ffmpeg -y -f lavfi -i color=c=skyblue:s=${W}x${H} -frames:v 1 "$BG_IMAGE" >/dev/null 2>&1
fi

# 音声（macOSのTTS）
say -v Kyoko "$SCRIPT_TEXT" -o /tmp/voice.aiff
ffmpeg -y -i /tmp/voice.aiff -ar 44100 -ac 2 -b:a 192k /tmp/voice.m4a >/dev/null 2>&1
DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 /tmp/voice.m4a)
printf '%s' "$DUR" > /tmp/voice.duration

# BGM 自動合成（指定がなければ柔らかいシンセ）
if [ -z "$BGM_PATH" ]; then
  BGM_PATH="/tmp/auto-bgm.m4a"
  LEN=$(cat /tmp/voice.duration)
  # 2トーン + ノイズをミックスしてローパス、軽い揺れとフェード
  ffmpeg -y \
    -f lavfi -t "$LEN" -i "sine=frequency=220:beep_factor=0:sample_rate=44100" \
    -f lavfi -t "$LEN" -i "sine=frequency=440:beep_factor=0:sample_rate=44100" \
    -f lavfi -t "$LEN" -i "anoisesrc=color=pink:amplitude=0.06" \
    -filter_complex "[0:a]volume=0.08[a0];[1:a]volume=0.06[a1];[2:a]lowpass=f=1800,volume=0.05[a2];[a0][a1]amix=inputs=2:normalize=0[a01];[a01][a2]amix=inputs=2:normalize=0[a];[a]afade=t=in:st=0:d=0.5,afade=t=out:st=$(( ${LEN%.*} > 1 ? ${LEN%.*}-1 : 0 )).0:d=1" \
    -map "[a]" -c:a aac -b:a 128k "$BGM_PATH" >/dev/null 2>&1 || true
fi

# ASS 字幕（句読点分割 + 長行は約13文字で改行）
python3 - <<'PY' <<'TEXT'
import re, sys, json
text = sys.stdin.read().strip()
dur = float(open('/tmp/voice.duration').read().strip())

# 句読点で文分割
parts = [p.strip() for p in re.split(r'(?<=[。！？!?])\s*', text) if p.strip()]
if not parts: parts=[text]

# 長すぎる行は約 12〜16 文字で \N 改行（助詞の直後は避け気味）
def soft_wrap(s, width_min=12, width_max=16):
    out=[]
    line=""
    for ch in s:
        line += ch
        # 改行候補：句読点・読点・中点・スペース
        if len(line) >= width_min and (ch in "、。・・!?！？　 " or len(line) >= width_max):
            out.append(line.strip())
            line=""
    if line: out.append(line.strip())
    return "\\N".join(out)

parts_wrapped = [soft_wrap(p) for p in parts]

# 尺の配分（最低1.2秒）
lens = [max(1, len(re.sub(r'\s+','',p))) for p in parts_wrapped]
min_dur=1.2
remain=max(dur, min_dur*len(parts_wrapped))
w=[l/sum(lens) for l in lens]
base=[wi*remain for wi in w]
adj=[max(min_dur,b) for b in base]
scale=dur/sum(adj); adj=[a*scale for a in adj]

def ts(sec):
    if sec<0: sec=0
    h=int(sec//3600); m=int((sec%3600)//60); s=int(sec%60); cs=int((sec-int(sec))*100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

W,H=1080,1920
ass=[]
ass+=["[Script Info]","ScriptType: v4.00+",
      f"PlayResX: {W}",f"PlayResY: {H}","WrapStyle: 2","ScaledBorderAndShadow: yes","",
      "[V4+ Styles]",
      "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
      # 白字・濃い縁取り・柔らか影 / 下中央
      "Style: Default,Noto Sans CJK JP,64,&H00FFFFFF,&H00000000,&H00303030,&H64000000,0,0,0,0,100,100,0,0,1,3.2,6,2,60,60,90,1",
      "", "[Events]",
      "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
t=0.0
for p,d in zip(parts_wrapped,adj):
    start,end=ts(t),ts(t+d)
    ass.append(f"Dialogue: 0,{start},{end},Default,,0000,0000,0000,,{p}")
    t+=d
open('/tmp/subs.ass','w',encoding='utf-8').write('\n'.join(ass))
PY
TEXT
$SCRIPT_TEXT
PY

# 映像フィルタ（縦動画化 + ロゴ影 + ASS字幕）
VID_FILTER="[0:v]scale=${W}:${H}:force_original_aspect_ratio=decrease,pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2:color=black[base]"
if [ -n "$LOGO_PATH" ] && [ -f "$LOGO_PATH" ]; then
  VID_FILTER="${VID_FILTER};[2:v]format=rgba,scale=360:-1,split=2[lg][lg2];[lg]boxblur=20[shadow];[base][shadow]overlay=W-w-56:56[b1];[b1][lg2]overlay=W-w-40:40[v0]"
else
  VID_FILTER="${VID_FILTER};[base]null[v0]"
fi
VID_FILTER="${VID_FILTER};[v0]subtitles=/tmp/subs.ass[vout]"

# 音声ミックス（ダッキング）
AUD_FILTER="[1:a]aformat=channel_layouts=stereo,volume=1.0[voice];[3:a]aformat=channel_layouts=stereo,volume=1.0[bgm];[bgm][voice]sidechaincompress=threshold=0.08:ratio=8:attack=5:release=250:makeup=4[bgmd];[voice][bgmd]amix=inputs=2:duration=shortest:dropout_transition=2[aout]"

# 入力: 0=BG, 1=voice, 2=logo(任意), 3=BGM
ffmpeg -y -loop 1 -i "$BG_IMAGE" -i /tmp/voice.m4a ${LOGO_PATH:+-i "$LOGO_PATH"} -i "$BGM_PATH" \
  -filter_complex "${VID_FILTER};${AUD_FILTER}" \
  -map "[vout]" -map "[aout]" -c:v libx264 -profile:v high -pix_fmt yuv420p -c:a aac -shortest "$OUT_MP4"

echo "✅ Generated: $OUT_MP4"
