# Vision / Detection

This is the drone-detection half of the C-UAS turret. It owns everything from
**camera → dataset → trained model → live detection with a confidence score**.

It is built around one idea: **the model is a swappable box, and the data
discipline is enforced by the tooling.** You collect and label data, the tools
keep you from the classic mistakes (data leakage, inconsistent labels), you
fine-tune a small YOLO on your own drone footage, and you measure it honestly.

## The pipeline, start to finish

```
  record clips          extract frames        label              split (by clip)
  (Arducam)             (sample video)        (boxes)            no leakage!
  capture.py       -->  extract_frames.py --> [label tool]  -->  split.py
       |                                                              |
       |  log each clip's conditions in data/clips.csv                v
       |                                                        dataset.py
       v                                                     (build YOLO yaml)
  data/raw_clips/                                                     |
                                                                      v
                            live_detect.py  <--  evaluate.py  <--  train.py
                            (webcam, live)       (mAP, P/R,        (fine-tune
                                                  save failures)    small YOLO)
```

## Where the work runs

- **This repo / your laptop:** collect, extract, label, split, run live detection.
- **Training:** your laptop *or* free Google Colab (Decision #8 — training is
  heavy, inference is light). `train.py` runs in both.
- **The Pi:** runs the final exported model (Prototype 2+). Not needed yet.

## Quick start (once the deps are installed)

```bash
cd vision
python -m pip install -r requirements.txt

# 0. Confirm the Arducam does MJPG 1080p30 (Decision #9 check)
python -m src.vision.capture --check

# 1. Record a clip and log its conditions
python -m src.vision.capture --record --drone "dji-mini" --light "hangar-day" \
    --distance "bench" --notes "slow hand-held pass"

# 2. Turn clips into frames
python -m src.vision.extract_frames

# 3. (label the frames with your chosen tool — see docs/labeling-guide.md)

# 4. Split by CLIP (never by frame) into train/val/test
python -m src.vision.split

# 5. Build the YOLO dataset file
python -m src.vision.dataset

# 6. Fine-tune
python -m src.vision.train

# 7. Evaluate honestly (writes wrong predictions to inspect)
python -m src.vision.evaluate

# 8. See it live
python -m src.vision.live_detect
```

## Read these first

- `docs/data-collection.md` — the data-collection staircase and how to film clips.
- `docs/labeling-guide.md` — the labeling rules that keep your boxes consistent.
- `experiments/log.md` — write down every training run. This is required by the
  project's AI requirements and it is how you actually learn.

## The one rule that matters most

**Split by clip, not by frame.** Frames from the same video clip are near
duplicates. If some land in train and some in test, your test score is a lie.
`split.py` enforces this for you — do not work around it.
