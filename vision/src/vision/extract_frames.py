"""Turn recorded clips into sampled image frames.

Clips are redundant (30 near-identical frames per second), so we sample 1 of
every N frames and cap how many we take per clip. Each saved frame's filename
STARTS WITH ITS clip_id, e.g. `20261024-153000_000123.jpg`. That prefix is how
split.py later groups frames by clip to avoid train/test leakage. Do not rename
frames in a way that drops the clip_id prefix.

  python -m src.vision.extract_frames
  python -m src.vision.extract_frames --every 5 --max 200
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import load_config

try:
    import cv2
except ImportError:
    cv2 = None


def extract_clip(clip_path: Path, out_dir: Path, every_n: int, max_per_clip: int) -> int:
    """Sample frames from one clip. Returns how many frames were written."""
    clip_id = clip_path.stem  # e.g. 20261024-153000
    cap = cv2.VideoCapture(str(clip_path))
    if not cap.isOpened():
        print(f"  ! could not open {clip_path.name}, skipping")
        return 0

    written = 0
    idx = 0
    while written < max_per_clip:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % every_n == 0:
            name = f"{clip_id}_{idx:06d}.jpg"
            cv2.imwrite(str(out_dir / name), frame)
            written += 1
        idx += 1
    cap.release()
    return written


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config")
    p.add_argument("--every", type=int, help="sample 1 of every N frames")
    p.add_argument("--max", type=int, help="max frames per clip")
    args = p.parse_args(argv)

    if cv2 is None:
        sys.exit("OpenCV not installed. python -m pip install -r requirements.txt")

    cfg = load_config(args.config)
    every_n = args.every or cfg["extract"]["every_n_frames"]
    max_per_clip = args.max or cfg["extract"]["max_per_clip"]

    raw_dir: Path = cfg["paths"]["raw_clips"]
    out_dir: Path = cfg["paths"]["frames"]
    out_dir.mkdir(parents=True, exist_ok=True)

    clips = sorted(p for p in raw_dir.glob("*") if p.suffix.lower() in {".mp4", ".avi", ".mov", ".mkv"})
    if not clips:
        print(f"No clips found in {raw_dir}. Record some with capture.py --record.")
        return 1

    print(f"Extracting from {len(clips)} clip(s): every {every_n} frames, "
          f"max {max_per_clip} per clip.")
    total = 0
    for clip in clips:
        n = extract_clip(clip, out_dir, every_n, max_per_clip)
        total += n
        print(f"  {clip.name}: {n} frames")
    print(f"\nWrote {total} frames to {out_dir}")
    print("Next: label them (see docs/labeling-guide.md), then run split.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
