#!/usr/bin/env python
import os, argparse, glob
from moviepy.editor import ImageClip, concatenate_videoclips
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--images", default="image")
    p.add_argument("--out", default="out/test.mp4")
    p.add_argument("--fps", type=int, default=1)
    p.add_argument("--size", default="1080x1920")
    args=p.parse_args()
    W,H=map(int,args.size.lower().split("x"))
    imgs=sorted([p for p in glob.glob(os.path.join(args.images,"*")) if p.lower().endswith((".jpg",".jpeg",".png"))])
    if not imgs: raise SystemExit(f"no images in {args.images}")
    clips=[]
    for im in imgs:
        c=ImageClip(im).resize(height=H).on_color(size=(W,H), color=(0,0,0), col_opacity=1).set_duration(1.0/args.fps)
        clips.append(c)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    concatenate_videoclips(clips, method="compose").write_videofile(args.out, fps=args.fps, codec="libx264", audio=False, preset="veryfast")
    print("[make_video_from_post] ok ->", args.out)
if __name__=="__main__":
    main()
