"""Fine-tune a small pretrained YOLO on our own drone data.

This is intentionally a THIN wrapper around Ultralytics. The learning for us is
in the DATA and the EVALUATION, not in re-implementing YOLO. We start from
pretrained weights (transfer learning) so a few hundred labeled frames are
enough — the model already knows edges/shapes/"object-ness" and we teach it the
one new concept "drone".

Run on your laptop or free Google Colab (training is heavy; the Pi only runs
inference later — Decision #8). After it finishes, WRITE THE RUN DOWN in
experiments/log.md.

  python -m src.vision.train
  python -m src.vision.train --epochs 120 --imgsz 1280   # push small-object perf
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config")
    p.add_argument("--model", help="override pretrained weights (e.g. yolo11n.pt)")
    p.add_argument("--epochs", type=int)
    p.add_argument("--imgsz", type=int)
    p.add_argument("--batch", type=int)
    p.add_argument("--from-scratch", action="store_true",
                   help="train from random init instead of pretrained "
                        "(the 'pretrained vs random' experiment)")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    tc = cfg["train"]
    data_yaml = cfg["paths"]["dataset"] / "dataset.yaml"
    if not data_yaml.exists():
        print(f"Missing {data_yaml}. Run dataset.py first.")
        return 1

    # Import here so --help works without ultralytics installed.
    try:
        from ultralytics import YOLO
    except ImportError:
        print("ultralytics not installed. python -m pip install -r requirements.txt")
        return 1

    model_name = args.model or tc["model"]
    if args.from_scratch:
        # Same architecture, random weights: pass the .yaml not the .pt
        model_name = model_name.replace(".pt", ".yaml")
        print(f"Training FROM SCRATCH (random init): {model_name}")

    model = YOLO(model_name)
    model.train(
        data=str(data_yaml),
        epochs=args.epochs or tc["epochs"],
        imgsz=args.imgsz or tc["imgsz"],
        batch=args.batch or tc["batch"],
        patience=tc["patience"],
        project=str(cfg["paths"]["runs"]),
        name="train",
    )

    print("\nTraining done. Weights are under", cfg["paths"]["runs"])
    print("Now:  python -m src.vision.evaluate   (measure on the TEST set)")
    print("And:  record this run in experiments/log.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
