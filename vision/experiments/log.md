# Experiment log

Required by the project's AI requirements: record the date, dataset size,
settings and metrics for **every** training run. This is also how you learn —
patterns only show up when you can compare runs.

Copy the template for each run. Newest at the top.

---

## Template (copy me)

### Run YYYY-MM-DD-NN — short name
- **Goal / hypothesis:** what are you testing? (e.g. "does +backlit data help?")
- **Dataset:** N frames from M clips. Stages covered: ___. Split seed: ___.
- **Model / settings:** yolo11n.pt, epochs ___, imgsz ___, batch ___.
- **Env:** laptop / Colab; torch ___, ultralytics ___.
- **Results (on the TEST set, never seen in training):**
  - mAP@50: ___
  - precision: ___   recall: ___
  - false lock-ons (false positives above conf threshold): ___
- **Failures seen:** what did the wrong-prediction images have in common?
- **Next action:** what data/change will you try because of this?

---

<!-- runs go below, newest first -->
