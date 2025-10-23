#!/usr/bin/env python3
import csv
import os
import re
import sys

if len(sys.argv) < 2:
    print("Usage: categorize-tools.py filelist.txt [output_csv]")
    sys.exit(1)
inp = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else "categories.csv"
rules = [
    (r"ffmpeg|ffprobe|rav1e|x264|x265|avif|aom|dav1d|mpg123|sox|vmaf|webp", "media"),
    (
        r"cwebp|dwebp|vwebp|webpmux|magick|mogrify|convert|montage|identify|exr|tiff|jpeg|png",
        "image",
    ),
    (
        r"curl|httpie|http[^s]*$|wget|nmap|(^|/)nc$|ncat|nping|ngrok|cloudflared|kubectl|helm|minikube|kind",
        "network",
    ),
    (r"git|gh|gcloud|gsutil|wrangler|pm2|node|npm|npx|pnpm|yarn|pip|python", "devtool"),
    (r"zip|unzip|xz|zstd|lz4|brotli|(^|/)tar$", "archiver"),
    (r"gpg|openssl|md5|sha|argon2|nettle|mbedtls|^pk_|^rsa_|^ecdsa|^ecdh", "crypto"),
    (r"tesseract|ocr|cntraining|lstmtraining|text2image|unicharset", "ocr"),
]


def categorize(name):
    for pat, cat in rules:
        if re.search(pat, name):
            return cat
    return "other"


rows = []
with open(inp, "r", encoding="utf-8") as f:
    for line in f:
        p = line.strip()
        if not p:
            continue
        base = os.path.basename(p)
        rows.append({"name": base, "category": categorize(base), "path": p})
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["name", "category", "path"])
    w.writeheader()
    w.writerows(rows)
print(f"Wrote {out} with {len(rows)} rows")
