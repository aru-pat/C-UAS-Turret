"""Load configs/drone.yaml once, give everything a consistent view of settings.

Every script imports `load_config()` from here instead of hard-coding paths or
hyperparameters. Change the YAML, not the code.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# vision/ directory = three parents up from this file
# (src/vision/config.py -> src/vision -> src -> vision)
VISION_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = VISION_ROOT / "configs" / "drone.yaml"


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Read the YAML config and return it as a dict.

    Relative paths in the `paths:` section are resolved to absolute paths rooted
    at the vision/ directory, so scripts work no matter where you run them from.
    """
    cfg_path = Path(path) if path else DEFAULT_CONFIG
    if not cfg_path.exists():
        raise FileNotFoundError(
            f"Config not found: {cfg_path}\n"
            "Run commands from the vision/ directory, or pass --config."
        )
    with open(cfg_path, "r") as f:
        cfg = yaml.safe_load(f)

    # Resolve paths relative to vision/ so they are absolute everywhere.
    resolved = {}
    for key, rel in cfg.get("paths", {}).items():
        resolved[key] = (VISION_ROOT / rel).resolve()
    cfg["paths"] = resolved
    cfg["_vision_root"] = VISION_ROOT
    return cfg


if __name__ == "__main__":
    # Quick sanity check: `python -m src.vision.config`
    import json

    c = load_config()
    print("Loaded config. Resolved paths:")
    for k, v in c["paths"].items():
        print(f"  {k}: {v}")
    print("\nClasses:", c["classes"])
