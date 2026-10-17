# Counter-UAS Turret — Project requirements (Semester 1)

## Goal
Autonomous turret detects a hand, tracks it, fires a low-power laser lock-on.

## Must have
- Pan-tilt motors, custom PCB control
- Self-trained neural network (not pretrained, not color-threshold-only)
- Classical CV for fast tracking between AI checks
- Laser activates only above confidence threshold
- Measured: accuracy %, lock-on latency, FPS

## Won't have
- Weapon
- RF jammer
- Anything aimed at people

## Budget
~$370 (Tier 2 — closed-loop steppers, Pi 5 + Coral accelerator)

## Hardware split
- Raspberry Pi 5 (8GB) + Coral accelerator — vision brain: camera, neural net
- Custom PCB — motor brain: motor control, power distribution, sensors
- Connected over serial/I2C

## Next semester
- Mount on drone
- Push inference toward on-chip
