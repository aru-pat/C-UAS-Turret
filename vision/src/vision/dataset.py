"""Build the YOLO dataset.yaml that train.py / evaluate.py consume.

Reads the train/val/test image lists produced by split.py and writes a
dataset.yaml in the Ultralytics format. YOLO finds each image's labels by
swapping `/images/` -> `/labels/` and `.jpg` -> `.txt` in the path, OR by
looking in a sibling `labels/` dir. We keep labels in data/labels/ and point
YOLO there explicitly.

  python -m src.vision.dataset
"""
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from .config import load_config


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    dataset_dir: Path = cfg["paths"]["dataset"]
    labels_dir: Path = cfg["paths"]["labels"]

    for split in ("train", "val", "test"):
        lst = dataset_dir / f"{split}.txt"
        if not lst.exists():
            print(f"Missing {lst}. Run split.py first.")
            return 1

    # Ultralytics reads class names and the three list files from this yaml.
    data_yaml = {
        "path": str(dataset_dir),
        "train": "train.txt",
        "val": "val.txt",
        "test": "test.txt",
        "names": {i: name for i, name in enumerate(cfg["classes"])},
        # tell YOLO where labels live (one .txt per image, same stem)
        "labels": str(labels_dir),
    }
    out = dataset_dir / "dataset.yaml"
    with open(out, "w") as f:
        yaml.safe_dump(data_yaml, f, sort_keys=False)

    print(f"Wrote {out}")
    print("Classes:", data_yaml["names"])
    print("\nNOTE: YOLO expects each image to have a matching label file.")
    print(f"      Put YOLO-format .txt labels in: {labels_dir}")
    print("      (an image with no drone = an EMPTY .txt file, not a missing one)")
    print("\nNext: train.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
