"""Verify the Arducam and record labeled clips.

Two jobs:
  --check   Confirm the camera can actually do MJPG 1080p30 (Decision #9).
            Over USB 2, uncompressed 1080p is only a few fps, so MJPG is
            required. If this fails, the camera/cable/port is the problem.

  --record  Record a clip to data/raw_clips/ AND append a row to data/clips.csv
            describing its conditions. The condition log is what lets us split
            without leakage and report results per condition later.

Examples:
  python -m src.vision.capture --check
  python -m src.vision.capture --record --drone dji-mini --light hangar-day \\
      --distance bench --background plain --notes "slow hand-held pass"
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from pathlib import Path

from .config import load_config

try:
    import cv2
except ImportError:
    cv2 = None  # checked in main() so the module still imports for --help


def _require_cv2() -> None:
    if cv2 is None:
        sys.exit(
            "OpenCV not installed. Run:  python -m pip install -r requirements.txt"
        )


def _open_camera(cfg: dict):
    """Open the camera and request MJPG at the configured resolution/fps."""
    cam = cfg["camera"]
    cap = cv2.VideoCapture(cam["index"])
    # Request MJPG BEFORE size/fps — order matters on many drivers.
    fourcc = cv2.VideoWriter_fourcc(*cam["fourcc"])
    cap.set(cv2.CAP_PROP_FOURCC, fourcc)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam["width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam["height"])
    cap.set(cv2.CAP_PROP_FPS, cam["fps"])
    return cap


def check(cfg: dict) -> int:
    """Report what the camera actually gives us vs. what we asked for."""
    _require_cv2()
    cap = _open_camera(cfg)
    if not cap.isOpened():
        print(f"Could not open camera index {cfg['camera']['index']}.")
        print("Is it plugged in? Try a different --config camera.index.")
        return 1

    # Read back what the driver actually settled on.
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    raw = int(cap.get(cv2.CAP_PROP_FOURCC))
    fourcc = "".join(chr((raw >> (8 * i)) & 0xFF) for i in range(4))

    ok, frame = cap.read()
    cap.release()

    want = cfg["camera"]
    print("Camera report (requested -> actual):")
    print(f"  resolution: {want['width']}x{want['height']} -> {w}x{h}")
    print(f"  fps:        {want['fps']} -> {fps}")
    print(f"  fourcc:     {want['fourcc']} -> {fourcc}")
    print(f"  first frame read: {'OK' if ok else 'FAILED'}")

    problems = []
    if not ok:
        problems.append("Camera opened but returned no frame.")
    if fourcc.strip("\x00").upper() != want["fourcc"].upper():
        problems.append(
            f"Not MJPG (got '{fourcc}'). Over USB 2 you'll be stuck at a few fps "
            "at 1080p. Decision #9 says confirm MJPG or return the camera."
        )
    if (w, h) != (want["width"], want["height"]):
        problems.append("Resolution differs from requested.")

    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print(f"  - {p}")
        print("\nAlso cross-check with: v4l2-ctl --list-formats-ext  (Linux)")
        return 1
    print("\nLooks good: MJPG at the requested resolution.")
    return 0


def record(cfg: dict, meta: dict) -> int:
    """Record frames to a clip file and log the clip's conditions.

    Recording stops on 'q' or Ctrl-C. A preview window shows what's being
    captured (close it / press q to stop).
    """
    _require_cv2()
    cap = _open_camera(cfg)
    if not cap.isOpened():
        print(f"Could not open camera index {cfg['camera']['index']}.")
        return 1

    raw_dir: Path = cfg["paths"]["raw_clips"]
    raw_dir.mkdir(parents=True, exist_ok=True)

    now = dt.datetime.now()
    clip_id = now.strftime("%Y%m%d-%H%M%S")
    out_path = raw_dir / f"{clip_id}.mp4"

    cam = cfg["camera"]
    writer = cv2.VideoWriter(
        str(out_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        cam["fps"],
        (cam["width"], cam["height"]),
    )

    print(f"Recording {out_path.name} ... press 'q' in the window to stop.")
    n = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Frame read failed; stopping.")
                break
            writer.write(frame)
            n += 1
            cv2.imshow("recording (press q to stop)", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        writer.release()
        cv2.destroyAllWindows()

    print(f"Saved {n} frames to {out_path}")
    _log_clip(cfg, clip_id, out_path.name, now, meta)
    return 0


def _log_clip(cfg: dict, clip_id: str, filename: str, when: dt.datetime, meta: dict) -> None:
    """Append one row to data/clips.csv. Creates the header if missing."""
    log_path: Path = cfg["paths"]["clip_log"]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    header = ["clip_id", "filename", "date", "drone", "lighting",
              "distance", "background", "notes"]
    exists = log_path.exists() and log_path.stat().st_size > 0
    with open(log_path, "a", newline="") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(header)
        w.writerow([
            clip_id, filename, when.strftime("%Y-%m-%d"),
            meta.get("drone", ""), meta.get("light", ""),
            meta.get("distance", ""), meta.get("background", ""),
            meta.get("notes", ""),
        ])
    print(f"Logged clip conditions to {log_path}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config", help="path to a config yaml (default: configs/drone.yaml)")
    p.add_argument("--check", action="store_true", help="verify MJPG 1080p30")
    p.add_argument("--record", action="store_true", help="record a clip")
    # clip metadata (for --record); all free-text, logged to clips.csv
    p.add_argument("--drone", default="", help="which drone, e.g. dji-mini")
    p.add_argument("--light", default="", help="lighting, e.g. hangar-day/backlit")
    p.add_argument("--distance", default="", help="bench/close/mid/far")
    p.add_argument("--background", default="", help="plain/clutter/sky")
    p.add_argument("--notes", default="", help="anything useful")
    args = p.parse_args(argv)

    cfg = load_config(args.config)

    if args.check:
        return check(cfg)
    if args.record:
        meta = dict(drone=args.drone, light=args.light, distance=args.distance,
                    background=args.background, notes=args.notes)
        return record(cfg, meta)
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
