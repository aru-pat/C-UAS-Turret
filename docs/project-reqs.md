# Counter-UAS Turret — Project requirements (Semester 1)

Last updated: Oct 17, 2026
The reasoning behind each choice is in `design-decisions.md`. Parts, links, prices
and order dates are in `turret_bom.xlsx`.

## Goal
Autonomous turret detects a hand (a drone later), tracks it, and fires a
low-power laser as a lock-on indicator.

## Must have
- Pan-tilt motors, controlled by a **custom PCB** (a carrier board that an
  STM32 Nucleo plugs into)
- **Self-trained** neural network (not pretrained, not color-threshold-only).
  Open question: fine-tune a small YOLO on my own photos, or train a small
  network from scratch. Parked for now; resume wording must match whichever I do.
- Classical CV for fast tracking between AI checks (AI about 2-5 Hz, CV about
  30 Hz or more)
- Laser activates only above a confidence threshold
- Measured: accuracy %, lock-on latency, FPS

## Won't have
- Weapon
- RF jammer
- Anything aimed at people

## Budget
- Original target: about $370 (Tier 2). **No longer binding**: a friend may help
  fund the build in exchange for a resume credit (role split still to be agreed).
- Current BOM (counted rows, incl. $80 shipping/tax/China/unknowns allowances):
  **about $530** without optional items, **about $722** with the optional
  battery set and Coral.
- Prices marked "Estimate" in the BOM (PCB fab, PCB parts, microSD, screws) will
  move as I order.

## Hardware split
- **Vision brain:** Raspberry Pi 5 **8 GB** (bought for Prototype 2, not now),
  plus a **USB camera** (Arducam 1080p autofocus) that is the same camera for
  training and the final build. Runs the neural net and decides "lock on".
  Coral accelerator is **optional and pinned** (decide at P2 after measuring the
  Pi alone).
- **Motor brain:** **STM32G474** on a **Nucleo-G474RE** that plugs into my
  custom carrier PCB. Sends step/direction pulses to two closed-loop motor
  kits, switches the laser, and the PCB handles power distribution.
- **Motors:** two **BIGTREETECH S42C V1.1** closed-loop stepper kits (motor,
  driver and encoder in one), run at **12 V** (PCB parts rated for 24 V as an
  upgrade hedge).
- **Link between brains:** serial (UART, or one USB cable into the Nucleo's
  programmer port). I2C is not used.
- **Power:** 12 V wall adapter now; a barrel jack and an XT60 footprint on the
  PCB so a battery can be added later. The PCB powers the Pi through a 5 V
  module (to be chosen about Oct 24); in Prototype 2 the Pi runs on its own wall
  supply as a safety net.
- **Laser:** cheap 5 mW 650 nm red dot module switched by a logic-level MOSFET,
  in Prototype 1 so I can see it fire on detection.

## Tools and access
- 3D printer available (pan-tilt frame and camera holder are printed)
- Purdue ECE shop for free small parts (check Monday Oct 19)

## Next semester
- Mount on drone
- Push inference toward on-chip
