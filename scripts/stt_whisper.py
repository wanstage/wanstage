import sys, pathlib
from faster_whisper import WhisperModel

audio = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
if not audio or not audio.exists():
    sys.exit("usage: python stt_whisper.py <audio-file>")

model = WhisperModel("base", device="cpu")
segments, info = model.transcribe(str(audio), language="ja")

out = audio.with_suffix(".txt")
with out.open("w", encoding="utf-8") as f:
    for seg in segments:
        f.write(seg.text.strip() + "\n")
print(f"[STT] -> {out}")
