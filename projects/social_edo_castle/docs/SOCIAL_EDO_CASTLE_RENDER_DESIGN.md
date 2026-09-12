# SOCIAL_EDO_CASTLE — 映像設計図・設計方法

## 0. Authority

```text
WORK_ID=SOCIAL_EDO_CASTLE
PROJECT_ROOT=~/WANSTAGE_NEW/projects/social_edo_castle
CANONICAL_WRITE_AUTHORITY=False
LOCAL_AI_ROLE=ADVISORY_ONLY
PUBLIC_POST_EXECUTED=False
MASTER_RENDER_EXECUTED=False
TERMINAL_SESSION_PRESERVATION=True
DIRECT_EXIT_COMMAND_ALLOWED=False
```

この設計書は、江戸城30秒縦型歴史ショートの「構成」「素材契約」「レンダー方法」「QC」「変更境界」を固定するための設計 authority とする。

---

## 1. 目的

1本30秒の縦型歴史ショートを、MacBook Pro M2 / 8GB上でローカル生成・編集・検証する。

最終目標:

```text
DURATION=30s
RESOLUTION=1080x1920
FPS=30
VIDEO_CODEC=H.264 High
PIX_FMT=yuv420p
COLOR_RANGE=tv
COLOR_SPACE=bt709
COLOR_TRANSFER=bt709
COLOR_PRIMARIES=bt709
AUDIO_CODEC=AAC-LC
AUDIO_SAMPLE_RATE=48000
AUDIO_CHANNELS=2
CONTAINER=MP4
FASTSTART=True
```

---

## 2. 全体設計図

```text
[SHOT_A PNG 1:1] ─┐
[SHOT_B PNG 1:1] ─┤
[SHOT_C PNG 1:1] ─┤
[SHOT_D PNG 1:1] ─┤
[SHOT_E PNG 1:1] ─┘
        │
        ▼
各6秒の縦型カットへ変換
        │
        ├─ 背景: 同一画像を拡大・crop・blur・darken
        ├─ 前景: 1:1画像を1080x1080で中央配置
        ├─ Motion: slow push-in / zoompan
        ├─ Caption: AppKitで透明PNG生成
        └─ Color: RGB → yuv420p / BT.709 limited
        │
        ▼
SHOT_A〜E 各6秒
        │
        ▼
30秒に連結
        │
        ├─ Primary BGM: Stable Audio 3 sm-music
        ├─ BGM source: 44.1kHz stereo PCM
        └─ Final mix: 48kHz stereo AAC-LC
        │
        ▼
30秒 Master MP4
        │
        ├─ ffprobe
        ├─ full decode
        ├─ duration/fps/codec/color
        ├─ faststart
        └─ Human full-watch QC
        │
        ▼
PUBLICATION_QUALITY=UNPROVEN until human final QC
```

---

## 3. Project directory

```text
~/WANSTAGE_NEW/projects/social_edo_castle/
├── assets/
│   ├── shot_a.png
│   ├── shot_b.png
│   ├── shot_c.png
│   ├── shot_d.png
│   ├── shot_e.png
│   ├── bgm.wav
│   └── bgm_sa3.wav
├── docs/
│   └── SOCIAL_EDO_CASTLE_RENDER_DESIGN.md
├── logs/
├── output/
└── tmp/
```

役割:

```text
assets = 固定入力
docs   = 設計書
logs   = 検証・実行証跡
output = master / deliverable
tmp    = 中間生成物
```

---

## 4. Shot構成

### SHOT_A — 1457年

```text
DURATION=6s
SUBJECT=太田道灌期の初期江戸城
CAPTION=
1457年、太田道灌が
江戸城を築いた。
```

素材条件:

- 15世紀後半の中世城郭
- 土塁、堀、木柵、木造門
- 低湿地、水路
- 後世の巨大石垣・巨大天守を避ける
- 1:1 PNG
- 画像内文字なし

状態:

```text
SHOT_A_SOURCE=PROVEN
SHOT_A_TECHNICAL_RENDER=PASS
SHOT_A_HUMAN_QC=PASS
SHOT_A_RENDER_DESIGN=PROVEN
```

---

### SHOT_B — 1590年

```text
DURATION=6s
SUBJECT=徳川家康の江戸入府と城・町の改造開始
CAPTION=
1590年、徳川家康が江戸へ。
城と町の大改造が始まる。
```

素材条件:

- 大規模な造成・建設途中
- 武士、職人、人夫、木材、石材
- 水路、橋、未整備道路
- 完成済み巨大都市として描かない
- 1:1 PNG
- 画像内文字なし

---

### SHOT_C — 1603年

```text
DURATION=6s
SUBJECT=江戸幕府成立と政治都市化
CAPTION=
1603年、江戸幕府が開かれ、
江戸は政治の中心へ。
```

素材条件:

- 城下町の拡張
- 水路、道路、武家屋敷、町人地
- 江戸幕府初期の雰囲気
- 明治・現代東京を入れない
- 1:1 PNG

---

### SHOT_D — 本丸御殿

```text
DURATION=6s
SUBJECT=本丸御殿
CAPTION=
本丸御殿は、
表向・中奥・大奥に分かれていた。
```

素材条件:

- 江戸城本丸御殿の内部・御殿構成を想起
- 和室、畳、襖、廊下
- 近代家具や西洋家具なし
- 1:1 PNG

---

### SHOT_E — 18世紀初頭

```text
DURATION=6s
SUBJECT=人口100万規模の江戸
CAPTION=
そして18世紀初頭、
江戸は人口100万規模の巨大都市へ。
```

素材条件:

- 密集した武家地・町人地
- 橋、水路、舟、人通り
- 巨大都市感
- 1657年焼失後の天守は描かない
- 1:1 PNG

---

## 5. 共通画像契約

```text
FORMAT=PNG
ASPECT_RATIO=1:1
WIDTH=HEIGHT
PREFERRED_SIZE>=1024x1024
TEXT_IN_IMAGE=False
CAPTION_BURN_IN=False
LOGO=False
WATERMARK=False
STYLE=cinematic historical reconstruction
REALISM=high
LIGHTING=natural
```

AI画像は史実資料そのものではなく、歴史再現イメージとして扱う。

---

## 6. 6秒Shotレンダー設計

### 6.1 Canvas

```text
OUTPUT_WIDTH=1080
OUTPUT_HEIGHT=1920
FPS=30
DURATION=6s
```

### 6.2 Background layer

元の1:1画像を縦画面全体へ拡張する。

処理:

```text
scale → crop → blur → brightness down → saturation slight down
```

目的:

- 黒帯を作らない
- foregroundを邪魔しない
- SNS縦型画面を自然に埋める

### 6.3 Foreground layer

```text
SIZE=1080x1080
POSITION_Y≈420
```

元画像の比率を壊さず中央配置する。

### 6.4 Motion

基本:

```text
TYPE=slow push-in
START_ZOOM≈1.00
END_ZOOM≈1.05
DURATION=6s
FPS=30
```

禁止:

```text
violent pan
fast zoom
random camera shake
AI object motion
frame interpolation by default
```

理由:

- 歴史資料風の落ち着きを維持
- AI画像の人物や建築物が崩れるリスクを回避
- SHOT_AでHuman QC PASS済み

### 6.5 Caption

FFmpeg drawtextは使用しない。

```text
CAPTION_RENDERER=macOS AppKit
OUTPUT=transparent PNG
SIZE=1080x320
```

字幕仕様:

```text
FONT=macOS system Japanese-capable font
TEXT_COLOR=white
STROKE=black
BACKGROUND_PANEL=semi-transparent black
ALIGN=center
```

配置:

```text
BOTTOM_AREA≈y=1420
```

---

## 7. Color pipeline

入力AI PNGは主にRGB。

```text
RGB source
  ↓
FFmpeg scale/color conversion
  ↓
yuv420p
  ↓
limited range (tv)
  ↓
BT.709 matrix / transfer / primaries
  ↓
H.264
```

最終stream条件:

```text
pix_fmt=yuv420p
color_range=tv
color_space=bt709
color_transfer=bt709
color_primaries=bt709
```

注意:

`setparams`やH.264 metadataは「タグ」の設定であり、単独では実画素の色変換を証明しない。
RGB→YUV変換をfilter chain内で明示する。

---

## 8. Video encode

```text
ENCODER=h264_videotoolbox
PROFILE=High
PIX_FMT=yuv420p
FPS=30
RESOLUTION=1080x1920
COLOR=BT.709 limited
MOVFLAGS=+faststart
```

VideoToolboxはMac M2のhardware encoderを利用する。

---

## 9. BGM設計

### Primary

```text
ENGINE=Stable Audio 3
VARIANT=sm-music
DECODER=same-s
SECONDS=30
STEPS=8
SEED=1457
CFG=3.0
SOURCE_SAMPLE_RATE=44100
CHANNELS=2
FORMAT=PCM_S16LE
```

採用済みauthority:

```text
~/WANSTAGE_NEW/projects/social_edo_castle/assets/bgm_sa3.wav
```

SHA256:

```text
3ccdd7405e45fbe9f239b169cd94e68728c9eaf3fc39da8a802c8697a7f1acd7
```

Human A/B QC:

```text
A_OR_B_PREFERRED=B
FITS_EDO_CASTLE=True
TOO_MODERN=False
TOO_DRAMATIC=False
DISTRACTS_FROM_NARRATION=False
STRUCTURE_NATURAL=True
WOULD_USE_FOR_BASELINE=True
```

### Fallback

```text
~/WANSTAGE_NEW/projects/social_edo_castle/assets/bgm.wav
```

削除しない。

### Final audio

```text
SOURCE=44100Hz stereo
FINAL=48000Hz stereo
CODEC=AAC-LC
```

master mix時にresampleする。

---

## 10. 30秒Master構成

```text
00:00–00:06 SHOT_A
00:06–00:12 SHOT_B
00:12–00:18 SHOT_C
00:18–00:24 SHOT_D
00:24–00:30 SHOT_E
```

映像:

```text
5 shots × 6 sec = 30 sec
```

音:

```text
bgm_sa3.wav
→ resample 48kHz
→ final level adjustment
→ AAC-LC stereo
```

---

## 11. QC設計

### Machine QC

必須:

```text
OUTPUT_EXISTS=True
FFPROBE_RC=0
DECODE_RC=0

codec_name=h264
profile=High
width=1080
height=1920
pix_fmt=yuv420p
avg_frame_rate=30/1

color_range=tv
color_space=bt709
color_transfer=bt709
color_primaries=bt709

audio_codec=aac
audio_profile=LC
sample_rate=48000
channels=2

duration=30.000000
FASTSTART=True
```

Machine QCで判定できないもの:

```text
story quality
historical plausibility
caption readability
motion smoothness
visual appeal
music suitability
publication quality
```

### Human QC

SHOT単位:

```text
MOTION_SMOOTH=
NO_VISIBLE_STUTTER=
CAPTION_READABLE=
CAPTION_NOT_CLIPPED=
FOREGROUND_COMPOSITION_OK=
COLOR_LOOKS_NATURAL=
HISTORICAL_VISUAL_ACCEPTABLE=
```

Master:

```text
WATCHED_FULL_30SEC=
NO_VISIBLE_STUTTER=
SHOT_TRANSITIONS_ACCEPTABLE=
CAPTION_READABLE_ALL=
BGM_VOLUME_ACCEPTABLE=
BGM_NOT_DISTRACTING=
HISTORICAL_FLOW_COHERENT=
WOULD_PUBLISH=
```

---

## 12. Terminal safety contract

WANSTAGEのTerminal貼り付けコードは、Terminalセッション自体を終了させない。

```text
TERMINAL_SESSION_PRESERVATION=True
DIRECT_EXIT_COMMAND_ALLOWED=False
EARLY_ABORT_SCOPE=BLOCK_OR_FUNCTION_ONLY
FAILURE_CLASSIFICATION=HOLD
SHELL_TERMINATED_BY_SCRIPT=False
```

禁止:

```bash
exit 1
exit 2
exit 3
```

代替:

- if / else
- function + return
- DECISION=HOLD
- 後続mutationを実行しない

すべての検証ブロック末尾に:

```text
SHELL_TERMINATED_BY_SCRIPT=False
```

を出力する。

---

## 13. Change control

1度に変更する主因子は原則1つ。

例:

```text
motion problem → zoompanだけ変更
caption problem → captionだけ変更
color problem → color pipelineだけ変更
BGM problem → BGMだけ変更
```

既にPASSした境界は、理由なく作り直さない。

```text
SHOT_A_RENDER_DESIGN=PROVEN
BGM_PRIMARY=PROVEN_AND_FROZEN
```

したがってB〜Eは同じレンダー設計を再利用する。

---

## 14. 現在の状態

```text
SHOT_A_SOURCE=PROVEN
SHOT_A_TECHNICAL_RENDER=PASS
SHOT_A_HUMAN_QC=PASS
SHOT_A_RENDER_DESIGN=PROVEN

BGM_PRIMARY=STABLE_AUDIO_3_SM_MUSIC
BGM_SELECTION=PROVEN
BGM_PRIMARY_FREEZE=PASS

SHOT_B=IMAGE_CREATED_NOT_YET_CANONICALLY_PLACED
SHOT_C=NOT_PLACED
SHOT_D=NOT_PLACED
SHOT_E=NOT_PLACED

MOTION_DESIGN=PROVEN
CAPTION_PATH=PROVEN
BT709_PATH=PROVEN
VIDEOTOOLBOX_PATH=PROVEN

MASTER_30SEC=HOLD
PUBLICATION=HOLD
```

---

## 15. 次工程

```text
BOTTLENECK=SHOT_B_TO_E_NOT_PLACED
CAUSE=30秒masterに必要な4画像が未固定
UNBLOCK=SHOT_B→C→D→Eを1:1 PNGで生成・SHA固定
NEXT=PLACE_AND_VERIFY_SHOT_B
DECISION=GO_CONTENT_PRODUCTION
```

順序:

```text
SHOT_B placement
→ verify identity
→ SHOT_C creation
→ SHOT_D creation
→ SHOT_E creation
→ all-assets audit
→ 30-sec master render
→ machine QC
→ human full-watch QC
```

---

## 16. 設計原則

```text
Safety
→ Reproducibility
→ Recoverability
→ Observability
→ Maintainability
→ Total Expected Completion Time
→ Performance
→ Profitability
```

この順序を優先する。

「動画ファイルが生成できた」ことと、
「人が最後まで見られる品質」
「SNS公開品質」
「収益化品質」
は別判定とする。

```text
VIDEO_GENERATION_CAPABILITY=GO
TECHNICAL_EXPORT_QUALITY=GO
CONTENT_QUALITY=UNPROVEN_UNTIL_FINAL_HUMAN_QC
PUBLICATION_QUALITY=UNPROVEN
MONETIZATION_QUALITY=UNPROVEN
```
