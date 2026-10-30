"""Split frames into train/val/test — BY CLIP, never by frame.

Why this file exists and matters:
  Frames sampled from the same clip are near-duplicates. If some land in train
  and some in test, the model has effectively "seen" the test frames and your
  test score becomes a lie (it looks great, then fails in the real world). The
  only honest way is to keep ALL frames from a given clip together in one split.

How it works:
  Each frame's filename begins with its clip_id (e.g. `20261024-153000_...jpg`).
  We group frames by that prefix, then assign whole CLIPS to train/val/test
  using the fractions in configs/drone.yaml. A fixed seed makes it reproducible.

Output: writes data/dataset/{train,val,test}.txt, each listing image paths.
These lists are consumed by dataset.py.

  python -m src.vision.split
"""
from __future__ import annotations

import argparse
import random
from collections import defaultdict
from pathlib import Path

from .config import load_config


def clip_id_of(frame_path: Path) -> str:
    """Recover the clip_id from a frame filename (text before the last '_')."""
    stem = frame_path.stem            # 20261024-153000_000123
    return stem.rsplit("_", 1)[0]     # 20261024-153000


def group_by_clip(frames_dir: Path) -> dict[str, list[Path]]:
    groups: dict[str, list[Path]] = defaultdict(list)
    for img in sorted(frames_dir.glob("*.jpg")):
        groups[clip_id_of(img)].append(img)
    return groups


def assign_clips(clip_ids: list[str], fracs: dict, seed: int):
    """Shuffle clips once and slice them into train/val/test."""
    rng = random.Random(seed)
    ids = list(clip_ids)
    rng.shuffle(ids)

    n = len(ids)
    n_train = round(n * fracs["train"])
    n_val = round(n * fracs["val"])
    # test gets the remainder so the three always sum to n
    train = ids[:n_train]
    val = ids[n_train:n_train + n_val]
    test = ids[n_train + n_val:]
    return {"train": train, "val": val, "test": test}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    frames_dir: Path = cfg["paths"]["frames"]
    dataset_dir: Path = cfg["paths"]["dataset"]
    dataset_dir.mkdir(parents=True, exist_ok=True)

    groups = group_by_clip(frames_dir)
    if not groups:
        print(f"No frames in {frames_dir}. Run extract_frames.py first.")
        return 1

    if len(groups) < 3:
        print(f"WARNING: only {len(groups)} clip(s) found. With so few clips the "
              "split can't be meaningful (you may get empty val/test sets). "
              "Record more clips across different conditions before trusting "
              "any metrics.")

    assignment = assign_clips(list(groups.keys()), cfg["split"], cfg["split"]["seed"])

    summary = []
    empty = []
    for split_name, clip_ids in assignment.items():
        lines = []
        for cid in clip_ids:
            for img in groups[cid]:
                lines.append(str(img.resolve()))
        out = dataset_dir / f"{split_name}.txt"
        out.write_text("\n".join(lines) + ("\n" if lines else ""))
        summary.append((split_name, len(clip_ids), len(lines)))
        if not clip_ids:
            empty.append(split_name)

    print("Split by clip (seed "
          f"{cfg['split']['seed']}):")
    print(f"  {'split':6}  {'clips':>5}  {'frames':>6}")
    for name, nclips, nframes in summary:
        print(f"  {name:6}  {nclips:>5}  {nframes:>6}")
    if empty:
        print(f"\nWARNING: these splits got ZERO clips: {', '.join(empty)}.")
        print("  With few clips, rounding can empty a split — and you CANNOT "
              "evaluate on an empty test set. Rule of thumb: you want at least "
              "~10 clips (ideally more, across varied conditions) before the "
              "metrics mean anything. Record more clips.")

    print(f"\nWrote lists to {dataset_dir}. Next: dataset.py")

    # Leakage self-check: no clip may appear in more than one split.
    seen: dict[str, str] = {}
    for split_name, clip_ids in assignment.items():
        for cid in clip_ids:
            if cid in seen:
                print(f"  !! LEAKAGE BUG: clip {cid} in both "
                      f"{seen[cid]} and {split_name}")
            seen[cid] = split_name
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
