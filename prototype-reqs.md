# Prototype requirements

## Prototype 1 — Parts move, AI sees (Window A)

**Motor half**
- [ ] Breadboard wiring: stepper drivers + steppers + pan-tilt bracket
- [ ] Send a command (e.g. `PAN:45,TILT:-10`), motors reach that angle
- [ ] Power doesn't brown out under load (motors + Pi + laser on one supply)

**Vision half**
- [ ] Collect hand photos: different lighting, angles, backgrounds, plus non-hand objects
- [ ] Train detection model v1
- [ ] Model detects hand in live video, reports a confidence score

**PCB design (gate before ordering)**
- [ ] Breadboard motor logic confirmed working (above two boxes checked)
- [ ] Driver chip, power regulation values, pin assignments finalized
- [ ] Full PCB designed (connectors, footprints, traces)
- [ ] Fab order submitted by end of Window A, so it ships during Window B

## Prototype 2 — Combined tracking, checkpoint (Window C start)

- [ ] Wire Raspberry Pi to motors (serial/I2C from Pi → breadboard driver circuit)
- [ ] Pi's detections drive motor commands live
- [ ] Hybrid loop: neural net runs ~2–5Hz, classical CV (e.g. KCF) tracks between checks at ~30Hz+
- [ ] No stutter/oscillation during tracking
- [ ] **Decision logged:** continue as planned, or simplify (drop hybrid CV, accept slower neural-net-only loop)

## Prototype 3 — Final, measured (Window C end)

Matches full project reqs:
- [ ] Custom PCB installed, replaces breadboard
- [ ] Pan-tilt motors on custom PCB control (final, not breadboard)
- [ ] Self-trained neural network running (not pretrained, not threshold-only)
- [ ] Classical CV tracking between AI checks
- [ ] Laser fires only above confidence threshold
- [ ] Measured and recorded: accuracy %, lock-on latency, FPS
- [ ] Stress test: bad lighting, partial occlusion
- [ ] Demo video recorded
- [ ] No weapon, no jammer, nothing aimed at people — confirmed
