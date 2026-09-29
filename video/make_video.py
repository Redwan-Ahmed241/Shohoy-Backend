"""Combine frame_*.jpg images in this folder into one MP4.

Usage:
    python make_video.py            # default 24 fps
    python make_video.py 10         # 10 fps
    python make_video.py 0.5 -o "my clip.mp4"
"""
import argparse
from pathlib import Path

import imageio.v2 as imageio

HERE = Path(__file__).resolve().parent

parser = argparse.ArgumentParser(description="Make a video from image frames.")
parser.add_argument("fps", nargs="?", type=float, default=2, help="frames per second (default 24)")
parser.add_argument("-o", "--output", default="man saving a child.mp4", help="output file name")
args = parser.parse_args()

frames = sorted(HERE.glob("frame_*.jpg"))
if not frames:
    raise SystemExit("No frame_*.jpg files found.")

out = HERE / args.output
with imageio.get_writer(out, fps=args.fps, codec="libx264", quality=8, macro_block_size=1) as writer:
    for f in frames:
        writer.append_data(imageio.imread(f))

print(f"Wrote {out.name}: {len(frames)} frames at {args.fps:g} fps = {len(frames) / args.fps:.2f}s")
