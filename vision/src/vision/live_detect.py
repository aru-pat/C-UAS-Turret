"""Run the trained model on the live Arducam feed, with a confidence readout.

This is the Prototype 1 vision demo: "model detects a drone in live video,
reports a confidence score". It also contains the hook for the P1 laser trigger
— when a drone is detected above the firing threshold, we (eventually) send one
message over USB serial to the STM32, which switches the laser.

The serial/fire part is STUBBED and OFF by default, because:
  - the hardware may not be wired yet, and
  - you never want an accidental fire. Enable it explicitly with --serial.

SAFETY: the laser only ever points at a wall/paper, never at a person. The fire
signal is gated on confidence >= threshold (Decision #3 — bias the threshold
HIGH; a false fire is worse than a missed detection).

  python -m src.vision.live_detect
  python -m src.vision.live_detect --weights .../best.pt --conf 0.6
  python -m src.vision.live_detect --serial /dev/ttyACM0   # enable fire signal
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .config import load_config

try:
    import cv2
except ImportError:
    cv2 = None


class FireSignal:
    """Sends the 'drone locked' signal to the STM32 over serial.

    Kept deliberately simple and OFF unless a port is given. The STM32 firmware
    decides what to do with the message; here we just send a one-line command.
    """

    def __init__(self, port: str | None, baud: int = 115200):
        self.ser = None
        if not port:
            return
        try:
            import serial  # pyserial
        except ImportError:
            print("pyserial not installed; --serial ignored.", file=sys.stderr)
            return
        self.ser = serial.Serial(port, baud, timeout=0.1)
        print(f"Serial fire signal ENABLED on {port} @ {baud}")

    def set_fire(self, on: bool) -> None:
        if self.ser is None:
            return
        # Simple, human-readable protocol. Match this in the STM32 firmware.
        self.ser.write(b"FIRE:1\n" if on else b"FIRE:0\n")

    def close(self) -> None:
        if self.ser is not None:
            self.set_fire(False)   # always leave the laser off
            self.ser.close()


def _find_best_weights(cfg: dict) -> Path | None:
    runs = cfg["paths"]["runs"]
    candidates = sorted(runs.glob("**/weights/best.pt"))
    return candidates[-1] if candidates else None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config")
    p.add_argument("--weights", help="path to best.pt (default: latest run)")
    p.add_argument("--conf", type=float, help="firing/display confidence threshold")
    p.add_argument("--serial", help="serial port to the STM32, e.g. /dev/ttyACM0 "
                   "(omit to keep the fire signal OFF)")
    args = p.parse_args(argv)

    if cv2 is None:
        sys.exit("OpenCV not installed. python -m pip install -r requirements.txt")

    cfg = load_config(args.config)
    conf = args.conf if args.conf is not None else cfg["detect"]["conf_threshold"]

    try:
        from ultralytics import YOLO
    except ImportError:
        print("ultralytics not installed. python -m pip install -r requirements.txt")
        return 1

    weights = Path(args.weights) if args.weights else _find_best_weights(cfg)
    if not weights or not weights.exists():
        print("No trained weights found. Run train.py first, or pass --weights.")
        return 1

    model = YOLO(str(weights))
    fire = FireSignal(args.serial)

    cam = cfg["camera"]
    cap = cv2.VideoCapture(cam["index"])
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*cam["fourcc"]))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam["width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam["height"])
    if not cap.isOpened():
        print(f"Could not open camera index {cam['index']}.")
        return 1

    print(f"Live detection (conf={conf}). Press 'q' to quit.")
    last = time.time()
    fps = 0.0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            results = model.predict(frame, conf=conf, verbose=False)
            r = results[0]

            # Best drone confidence this frame (0 if none detected).
            best = 0.0
            if r.boxes is not None and len(r.boxes) > 0:
                best = float(r.boxes.conf.max())

            locked = best >= conf
            fire.set_fire(locked)   # no-op unless --serial was given

            # measure FPS (one of the spec's required numbers)
            now = time.time()
            dt = now - last
            last = now
            if dt > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / dt)

            annotated = r.plot()  # draws boxes + conf
            status = f"LOCK {best:.2f}" if locked else f"conf {best:.2f}"
            color = (0, 0, 255) if locked else (0, 255, 0)
            cv2.putText(annotated, f"{status}  |  {fps:4.1f} FPS",
                        (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
            cv2.imshow("drone detection (q to quit)", annotated)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    except KeyboardInterrupt:
        pass
    finally:
        fire.close()
        cap.release()
        cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
