# Labeling guide

Inconsistent boxes are the #1 silent killer of a detector. If "future you" and
"today you" draw boxes differently, the model learns confusion. So we fix the
rules here and follow them every time.

## Format: YOLO

One `.txt` file per image, same name as the image, in `data/labels/`.
Each line is one box:

```
<class_id> <x_center> <y_center> <width> <height>
```

- `class_id`: 0 for `drone` (the only class for now — see `configs/drone.yaml`).
- All four numbers are **normalized 0–1** (fraction of image width/height).
- An image with **no drone** gets an **empty `.txt` file** (important — these
  negatives teach the model what a drone is NOT).

## The rules (decide once, follow always)

1. **Tight boxes.** The box hugs the drone — include props/arms, exclude empty
   space. Consistency matters more than perfection, but be tight.
2. **Include the whole drone**, props and landing gear included, even thin parts.
3. **Occlusion:** if you can still tell it's a drone and >~25% is visible, box the
   *visible* extent. If it's barely visible (<~25%), skip it (no box).
4. **Motion blur:** still label it — blurry drones are what the camera sees.
   Box the blurred extent.
5. **Multiple drones:** one box each.
6. **Too small / ambiguous dots:** if you genuinely can't tell it's a drone,
   don't label it (and consider whether that frame belongs in the dataset yet).
7. **Hard negatives (birds, kites, etc.):** leave the file empty (no box). They
   are negatives — we want the model to NOT fire on them. (If we later add a
   `bird` class to actively suppress, that changes — not yet.)

## Tooling

Any tool that exports **YOLO txt format** works. The big efficiency win is
**model-assisted labeling**: label a handful by hand, train a rough model, let it
pre-label the rest, and you just correct. Options to evaluate when we get there
(check current versions/pricing at decision time):

- **Roboflow** — cloud, strong auto-labeling/augmentation/export. Fast, easy.
- **CVAT** — self-hostable, good for video (interpolate boxes across frames).
- **labelImg / Label Studio** — simpler local options.

Since clips give near-duplicate consecutive frames, a tool that **interpolates
boxes across video frames** (CVAT) saves enormous time vs. boxing every frame.

## Sanity check before training

Run the dataset build (`dataset.py`) and spot-check: open a few images with
their boxes drawn on. Wrong-looking boxes now = a model that learns the wrong
thing later. Catch it here.
