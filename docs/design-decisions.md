# Design Decisions (plain-language version)

Last updated: Oct 16, 2026

This file explains **what we decided, why, and what is still open**.
It is written so someone who has never built a robot can follow it.
It adds to `project-reqs.md` and, where they differ, it is newer.
(Example: `project-reqs.md` says the PCB talks to the Pi over "serial/I2C".
We have now picked serial only.)

---

## The big picture in one paragraph

The turret has two "brains".

- **Brain 1: the Raspberry Pi 5.** It looks through the camera, runs our
  self-trained AI model to answer "is there a hand (later a drone) and where?",
  and decides when the target is locked.
- **Brain 2: the STM32 chip on our custom PCB.** It does exactly what the Pi
  tells it: spin the two motors to the right angle, and switch the laser.

Why two brains? The Pi runs a full operating system (like a tiny laptop), so it
can't promise exact timing. Motors need exact timing or they stutter. The STM32
only does simple jobs, so it can be exact. The Pi does the thinking, the STM32
does the moving.

```
 Camera --> [ Raspberry Pi 5 ] --serial wire--> [ STM32 on custom PCB ] --> 2 motors
             runs the AI model                   exact motor timing         + laser
             decides "lock on"
```

---

## Decision 1: The motor brain is an STM32 chip (not an ESP32)

**What:** STM32G431. For Prototype 1 we use the **Nucleo-G431RB** dev board
(a ready-made board with the chip plus a USB programmer built in). On the final
PCB we solder the bare chip.

**Why:**
- STM32 chips are what real robots, drones and motor products use. "Custom PCB
  built around an STM32" is a stronger resume line than ESP32.
- The G4 family has precise built-in timers, which is exactly what makes motor
  pulses accurate.

**The catch (honest):** STM32 is harder to learn than ESP32.
To keep it fast, we write code in the simple **Arduino style** (using
PlatformIO in VS Code). That adds roughly 5-6 hours compared with an ESP32,
instead of 10-15 hours with ST's own tools. We can switch the tricky parts to
ST's own libraries later (a semester 2 option).

**Escape hatch:** if the Nucleo is not driving a motor by **Oct 26**, we switch
to an ESP32-S3. Nothing else in the design changes.

---

## Decision 2: Pi and PCB talk over UART serial

**What:** Two wires plus a ground wire (TX, RX, GND), at 3.3 V.

**Why:** The Pi only sends tiny messages like "aim here" or "fire". That does
not need a fast or fancy connection. UART is the simplest option, works on
every Pi and STM32, and is easy to debug with a laptop.

**Alternatives we rejected:** USB cable (needs extra USB circuitry on the PCB),
I2C (motor electrical noise can corrupt it), SPI (overkill).

---

## Decision 3: The motors run on 12 V

**What:** 12 volt supply for the motors.

**Why:**
- A 12 V battery is made of 3 cells and is cheap. A 24 V battery needs 6 cells
  (or an extra boost circuit), roughly $40-70 more overall (estimate).
- A turret is light and slow. 12 V is plenty. The cost of 12 V is a lower top
  speed (per the MKS maker: it "works but gives lower high-speed performance"),
  which this project will not need.

**Catch:** many "industrial" closed-loop motor drivers need 24 V or more (every
StepperOnline closed-loop driver we checked had a 24 V minimum). So we are
choosing the hobby-grade **MKS SERVO42-style** closed-loop drivers, which accept
12-24 V and accept simple step/direction signals. See "Still open".

**The 24 V hedge (agreed Oct 16):** a turret has to track a moving target, so
we don't want to be stuck if 12 V feels slow. The drivers accept 12-24 V, so:
1. The PCB is built with parts that can handle 24 V (capacitors, fuse,
   connectors, traces), which costs almost nothing extra.
2. We run at 12 V now.
3. If the turret feels slow in P2, upgrading means swapping the battery and one
   small protection diode (SMCJ15A -> a 24 V-class one). No new board.

**What "closed-loop" means:** a normal stepper motor moves N steps and *assumes*
it got there. If it is bumped, it loses its place without knowing. A
closed-loop stepper has a small position sensor (an encoder) so the driver can
check and fix its position. Same motor, plus feedback.

---

## Decision 4: The PCB powers the Pi

**What:** The final PCB takes the battery in, and splits it into two paths:
1. Motors (12 V), protected by a fuse and a surge-protector diode.
2. The Pi, through a **ready-made 5 V converter module** (plugged into a socket
   on the PCB, so we don't design a regulator from scratch). It must supply
   5 V at about 5 A.

**Why:** one battery, one plug, one switch. That is cleaner and what a real
product looks like. It also matches the original plan that the PCB handles
"power distribution".

**Because the PCB order only happens once** (it must go out by Nov 2), this
power path has to be in the first design.

**Safety net:** the PCB is brand new, so in Prototype 2 the Pi runs from its
own official wall power supply (about $12) first. We switch to PCB power only
after we test the board and trust it. That way a PCB bug cannot ruin the
Prototype 2 checkpoint.

**Noise note:** motors create electrical noise that can reset a Pi. The Pi's
5 V path gets its own capacitors and short, thick traces to keep it clean.

---

## Decision 5: Power plan by prototype (cost control)

The budget is tight, so we buy only what each prototype needs.

| When | Power parts | Rough cost |
|---|---|---|
| **P1** (now) | 12 V 5 A wall adapter, 15 A fuse and holder, XT60 connector pigtail and capacitor, SMCJ15A surge diode | about $35 |
| **P2** | Pi's official 27 W wall power supply | about $12 |
| **P3** | Battery pack, charger, switch, cheaper 5 V converter module | about $80+ |

Notes:
- **No fire box.** We dropped the $80 box as overkill. Rule instead: charge the
  battery only while awake and in the room, on a tile or metal tray, never
  overnight, and never use a dented or puffy cell.
- **Battery** is built from 6 cells in a protected 3-in-series, 2-in-parallel
  pack (about 11.1 V, roughly 60 Wh). Buying a ready-made pack versus building
  one is decided at P3. The pre-made packs we checked either miss the current
  spec (Tenergy: 9 A continuous, built to order in 3-7 days) or lack a stated
  protection board (Nexus). Prices are estimates until verified.
- The turret should draw about 45 W on average and about 87 W at peak (a
  deliberately cautious guess). 20 minutes of runtime needs about 15 Wh.

---

## Decision 6: Raspberry Pi 5, Coral waits

**What:** Raspberry Pi 5. **4 GB or 8 GB is not locked** (no wiring or code
difference; 4 GB is cheaper and enough because training happens elsewhere).

**Training vs running (the thing that confused us):**
- **Training** = teaching the model with thousands of pictures. Heavy work. Done
  once on a laptop or free Google Colab.
- **Running** = using the finished model on live camera frames. Light work.
  Done by the Pi, by itself, with no laptop needed.

**Coral accelerator:** deferred. It plugs into the Pi (USB or PCIe), so adding
it later does not change the PCB or the wiring. Decide at P2 (Nov 20 or later).
Without it, the Pi's CPU runs the model; this probably meets our 2-5
detections-per-second goal but is NOT verified. We also need to check Coral
availability, since that product line is aging.

**Timing:** the Pi is not needed in P1 (motors are tested with the STM32 only,
and the model is trained and tested on a laptop webcam). So do not buy the Pi
yet.

---

## Still open (not decided)

1. **Exact motors and drivers.** Direction: hobby-grade MKS SERVO42-style
   closed-loop drivers (12-24 V) plus NEMA 17 motors, about $70-130 for two
   axes. Need specific listings, seller checks and delivery dates, because
   delivery must land before Nov 2 and many are shipped from China.
2. **Laser is IN Prototype 1 (decided Oct 16).** The laptop webcam runs the
   hand-detection model. When it is confident, the laptop sends one message over
   USB serial to the STM32, which switches the laser on. No Pi needed in P1.
   Safety: true Class 2 means 1 mW or less (5 mW is Class 3R, not Class 2).
   Buy a red-dot module from a reputable seller that states under 1 mW, since
   cheap modules often mislabel their power. Test only on a wall or paper
   target. Never aim at people or mirror-like surfaces.
3. **Confidence threshold** for firing the laser (decided during P2/P3).
4. **Pi RAM size** (4 GB vs 8 GB) and **Coral** (see above).
5. **Battery: buy vs build** (decided at P3, order in late Nov).
6. **Overall budget:** about $370 total across the whole project. A stricter
   monthly spending limit applies; ask Aru for the exact number before
   finalizing the BOM.

## Hard rules that do not change

- No weapon. No RF jammer (illegal, FCC).
- Laser is low-power (1 mW or less), only fires above the confidence threshold,
  never aimed at people.
- The AI model is self-trained. It makes the real detect/classify decision.
- Breadboard first, then finalize the PCB (PCB parts must be ordered by Nov 2).
