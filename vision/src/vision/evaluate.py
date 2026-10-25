"""Measure the model honestly on the TEST set, and SAVE its mistakes.

The numbers (mAP, precision, recall) tell you how good the model is. The saved
mistake images tell you WHY it's wrong — and that's what drives the next round
of data collection. Looking at failures is the single most valuable habit in
practical ML, so this script makes it easy.

For a laser turret, remember: a FALSE POSITIVE (firing at a bird) is worse than
a false negative (missing a drone). So watch precision at your firing threshold.

  python -m src.vision.evaluate
  python -m src.vision.evaluate --weights experiments/runs/train/weights/best.pt
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config


def _find_best_weights(cfg: dict) -> Path | None:
    runs = cfg["paths"]["runs"]
    candidates = sorted(runs.glob("**/weights/best.pt"))
    return candidates[-1] if candidates else None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config")
    p.add_argument("--weights", help="path to best.pt (default: latest run)")
    p.add_argument("--conf", type=float, help="confidence threshold for the "
                   "failure dump (default: config detect.conf_threshold)")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_yaml = cfg["paths"]["dataset"] / "dataset.yaml"
    if not data_yaml.exists():
        print(f"Missing {data_yaml}. Run dataset.py first.")
        return 1

    try:
        from ultralytics import YOLO
    except ImportError:
        print("ultralytics not installed. python -m pip install -r requirements.txt")
        return 1

    weights = Path(args.weights) if args.weights else _find_best_weights(cfg)
    if not weights or not weights.exists():
        print("No trained weights found. Run train.py first, or pass --weights.")
        return 1

    conf = args.conf if args.conf is not None else cfg["detect"]["conf_threshold"]
    print(f"Evaluating {weights} on the TEST split (conf={conf}) ...")

    model = YOLO(str(weights))

    # Metrics on the held-out TEST set (split='test' uses test.txt from the yaml).
    metrics = model.val(data=str(data_yaml), split="test", conf=conf,
                        project=str(cfg["paths"]["runs"]), name="eval")

    # Ultralytics exposes the headline numbers here.
    try:
        print("\n=== TEST metrics ===")
        print(f"  mAP@50:      {metrics.box.map50:.3f}")
        print(f"  mAP@50-95:   {metrics.box.map:.3f}")
        print(f"  precision:   {metrics.box.mp:.3f}")
        print(f"  recall:      {metrics.box.mr:.3f}")
    except Exception as e:  # metric attribute names can shift across versions
        print(f"(could not read summary metrics cleanly: {e})")
        print("See the eval run folder for plots (PR curve, confusion matrix).")

    print(f"\nPlots + predictions saved under {cfg['paths']['runs']}/eval*")
    print("ACTION: open the predicted images, find what the failures share,")
    print("        film targeted data for that case, retrain. Log it all.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
