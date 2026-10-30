# Data collection — the staircase

The model is only as good as the data. Since we have a hangar of drones we can
image and fly, we collect our **own** footage on the **Arducam** (the same camera
the turret uses). This is our biggest advantage — use it.

We build difficulty in **stages**. Don't try to do "all conditions" on day one.
Each stage is a loop: collect → train → look at failures → collect more.

| Stage | What you film | Difficulty | Teaches you |
|---|---|---|---|
| 1 | One drone, close/bench range, stationary then slow-moving, hangar light, plain-ish background | Easy | Proves the whole pipeline end to end |
| 2 | Drone flying in the hangar, varied distance/position, real clutter | Medium | Motion blur, scale variation, real backgrounds |
| 3 | Different drone models/sizes/colors | Medium | Generalization (not memorizing one airframe) |
| 4 | Drone against sky/trees/buildings, at range (small object) | Hard | Small-object detection, sky-vs-clutter |
| 5 | Dusk, backlight, birds, partial occlusion, fast passes | Hardest | Hard negatives, robustness (P3 stress test) |

**Prototype 1 (now) only needs Stage 1, reaching into Stage 2.** Stages 4–5 are
Window C / next semester.

## How to film (do this every time)

1. **Film in CLIPS, not single photos.** A few seconds of video while the drone
   moves gives you varied, slightly-blurred, in-domain frames for free. We sample
   frames from clips later.
2. **One condition per clip where possible.** Keep a clip to roughly one lighting
   / distance / drone so you can later say "the model fails on backlit clips".
3. **Log every clip.** `capture.py` appends a row to `data/clips.csv` with the
   drone, lighting, distance, and notes. This log is what lets you split without
   leakage AND report results per condition.
4. **Use the Arducam at MJPG 1080p30.** Not your phone. A model trained on phone
   footage underperforms on the turret's actual camera.

## Diversity that actually matters

Vary these deliberately across clips (not all at once — one step at a time):

- **Lighting:** bright, dim, backlit, warm/cool, shadows. (Biggest failure cause.)
- **Background:** plain, cluttered, sky, trees — and empty frames with no drone.
- **Distance / scale:** close, mid, far — the sizes the turret will really see.
- **Angle:** drone seen from below, side, head-on, tilted.
- **Drone type:** different models/sizes/colors once past Stage 1.
- **Motion blur:** the target moves; blurry drones are what the camera sees.
- **Hard negatives:** birds, kites, hand-like/drone-like objects, people. These
  are training data too — they teach "what is NOT a drone" and cut false fires.

## How much?

For single-class fine-tuning, a realistic starting target is **~300–800
well-labeled, diverse frames** to prove the pipeline, then scale where evaluation
shows weakness. **Diversity beats raw count.** 500 near-identical frames of one
drone in one light is worse than 300 varied ones.

## The failure-analysis loop (this is the real ML skill)

After each training run, open the wrong predictions `evaluate.py` saves. Ask
"what do the failures have in common?" (e.g. all backlit). Go film targeted data
for exactly that case. Retrain. Record the before/after numbers in
`experiments/log.md`. Doing this loop a few times across the stages is how you
genuinely learn practical ML.
