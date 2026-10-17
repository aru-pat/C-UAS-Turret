# Design Decisions (plain-language version)

Last updated: Oct 17, 2026

This file explains **what we decided, why, and what is still open**.
It is written so someone who has never built a robot can follow it.
It adds to `project-reqs.md` and, where they differ, it is newer.
(Example: `project-reqs.md` says the PCB talks to the Pi over "serial/I2C".
We have now picked serial only.)

The parts list with links, prices, and "decide by / order by" dates lives in the
BOM spreadsheet (`turret_bom.xlsx`). This file is the reasoning behind it.

---

## The big picture in one paragraph

The turret has two "brains".

- **Brain 1: the Raspberry Pi 5.** It looks through the camera, runs our
  self-trained AI model to answer "is there a hand (later a drone) and where?",
  and decides when the target is locked.
- **Brain 2: the STM32 chip on our custom PCB.** It does exactly what the Pi
  tells it: send the right pulses to the two motors, and switch the laser.

Why two brains? The Pi runs a full operating system (like a tiny laptop), so it
can't promise exact timing. Motors need exact timing or they stutter. The STM32
only does simple jobs, so it can be exact. The Pi does the thinking, the STM32
does the moving.

```
 Camera --> [ Raspberry Pi 5 ] --serial wire--> [ STM32 on custom PCB ] --> 2 motor kits
             runs the AI model                   exact motor timing         + laser
             decides "lock on"
```

**Chip vs board (a common mix-up):** the STM32 is the *chip*. The **Nucleo** is
that chip already mounted on a small ready-made board. Our custom PCB is a
**carrier board**: the Nucleo plugs into it, and its copper traces connect the
Nucleo to the motors, laser, power and Pi. So the same Nucleo we use in
Prototype 1 stays in the finished turret.

---

## Decision 1: The motor brain is an STM32G474 (not an ESP32)

**What:** STM32G474. For Prototype 1 we use the **Nucleo-G474RE** dev board
(a ready-made board with the chip plus a USB programmer built in, about $20 at
Digi-Key).

**Updated Oct 17: carrier-board PCB.** The final custom PCB is a **carrier
board that the Nucleo plugs into** (decided Oct 17), not a board with the bare
chip soldered on. The PCB still carries the real design work (connectors, power
input, fuse, surge diode, laser MOSFET, 5 V module socket, motor connectors),
and there is still soldering. The chip stays on the Nucleo, which is already
known to work. That removes fine-pitch chip soldering, chip start-up problems and
the extra programming header. The bare STM32G474RET6 (64-pin, about $10.70) and
a chip-down board remain in the BOM as an **optional, not-counted** upgrade.

**Resume wording:** say "custom carrier PCB for an STM32 Nucleo". Do not say
Aru designed his own microcontroller board.

**Pi link option:** the Pi can talk to the Nucleo over one USB cable into its
programmer port (it shows up as a serial port), instead of separate TX/RX/GND
wires. Choose one when designing the board.

**One power rule:** the Nucleo and the carrier board must never both power the
same pin. Pick a single power path when laying out the board.

**Changed from the earlier plan:** this doc used to say STM32G431 / Nucleo-G431RB.
That board is out of stock with a 99-week lead time, so we moved to the G474 in
the same family. Code and pin choices carry over.

**Why STM32:**
- STM32 chips are what real robots, drones and motor products use. "Custom PCB
  built around an STM32" is a stronger resume line than ESP32.
- The G4 family has precise built-in timers, which is exactly what makes motor
  pulses accurate.

**The catch (honest):** STM32 is harder to learn than ESP32.
To keep it fast, we write code in the simple **Arduino style** (using
PlatformIO in VS Code). That adds roughly 5-6 hours compared with an ESP32,
instead of 10-15 hours with ST's own tools.

**Escape hatch:** if the Nucleo is not driving a motor by **Oct 26**, we switch
to an ESP32-S3. Nothing else in the design changes.

---

## Decision 2: Pi and PCB talk over UART serial

**What:** Two wires plus a ground wire (TX, RX, GND), at 3.3 V.

**Why:** The Pi only sends tiny messages like "aim here" or "fire". That does
not need a fast or fancy connection. UART is the simplest option, works on
every Pi and STM32, and is easy to debug with a laptop.

**In Prototype 1** the laptop plays the Pi's role over USB serial.

**Alternatives we rejected:** USB cable (needs extra USB circuitry on the PCB),
I2C (motor electrical noise can corrupt it), SPI (overkill).

---

## Decision 3: The motors run on 12 V, with a 24 V hedge

**What:** 12 volt supply for the motors.

**Why:**
- A 12 V battery is made of 3 cells and is cheap. A 24 V battery needs 6 cells
  (or an extra boost circuit), roughly $40-70 more overall (estimate).
- A turret is light and slow. 12 V is plenty. The cost of 12 V is a lower top
  speed, which this project will not need.

**The 24 V hedge (agreed Oct 16):**
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

## Decision 4: The motors are BIGTREETECH S42C closed-loop kits (decided Oct 17)

**What:** Two **BIGTREETECH S42C V1.1** kits (one for pan, one for tilt),
$39.99 each on Amazon. Each kit is the motor plus its driver and position
sensor in one unit, so there is nothing to match up. The STM32 only sends simple
step and direction pulses.

**Why:** we want closed-loop (backlash was named as a top failure risk), and
this is the cheapest hobby-grade closed-loop kit that arrives before our Oct 26
check. Plain steppers plus separate drivers (about $50 for two axes) stay in the
BOM only as a not-counted alternative; they are open-loop, which breaks the spec.

**Honest unknowns:**
- The Amazon page does not state the voltage. BTT's V1.0 manual rates the driver
  at 1.65 A at 12 V. **First power-up is on a bench supply at 12 V with about a
  1 A current limit.**
- The pinout in the V1.0 manual may differ on V1.1. Read the labels printed on
  the board.
- Some reviewers report dead units. Amazon returns are free for 30 days, so test
  both on arrival.

---

## Decision 5: The PCB powers the Pi

**What:** The final PCB takes power in, and splits it into two paths:
1. Motors (12 V), protected by a fuse and a surge-protector diode.
2. The Pi, through a **ready-made 5 V converter module** (plugged into a socket
   on the PCB, so we don't design a regulator from scratch). It must supply
   5 V at about 5 A.

**Why:** one power input and one switch. That is cleaner and what a real
product looks like. It also matches the original plan that the PCB handles
"power distribution".

**Because the PCB order only happens once** (it must go out by Nov 2), this
power path has to be in the first design.

**Safety net:** the PCB is brand new, so in Prototype 2 the Pi runs from its
own official wall power supply (about $12) first. We switch to PCB power only
after we test the board and trust it.

**Noise note:** motors create electrical noise that can reset a Pi. The Pi's
5 V path gets its own capacitors and short, thick traces to keep it clean.

**Still open: which 5 V module.** Option A is the Pololu D24V50F5 ($32.95, known
good). Option B is a generic AliExpress 5 V / 5 A board ($5.24, unproven, and the
"5 A" claim is doubtful). The two have different sizes, so this must be decided
before the PCB layout is final. Revisit about Oct 24.

---

## Decision 6: Power input connector on the PCB (decided Oct 17)

**What:** **Option D**: a barrel jack *and* an XT60 battery connector footprint
on the same board. Only one is connected at a time.

**Why:**
- Today the wall adapter plugs into the barrel jack. It cannot be plugged in
  backwards.
- Later a battery drops into the XT60 (the standard drone battery plug, built
  for high current, also hard to reverse), with no board redesign.
- The extra cost is only a few dollars and a little board space.

**Rejected:** a bare screw terminal alone. It is cheap, but it can be wired
**backwards**, which can kill the chip and drivers, and the wires can work loose
from vibration on a moving turret. Barrel jack alone does not suit a battery.

**Rules:**
- Never connect both at once. A label on the board says which one is live.
- The fuse sits right at the power entry, before anything else.
- Optional: a small reverse-polarity protection part as a cheap safety net.

---

## Decision 7: Power plan by prototype (cost control)

The budget is tight, so we buy only what each prototype needs.

| When | Power parts | Notes |
|---|---|---|
| **P1** (now) | 12 V 5 A wall adapter, barrel-jack to screw-terminal adapter, 15 A fuse and holder, SMCJ15A surge diode, 1000 uF capacitor | Check the Purdue ECE shop first; it may have the adapter, jack, fuse parts and capacitor for free |
| **P2** | Pi's 27 W wall power supply | The Pi runs on its own wall supply until the PCB is trusted |
| **P3** | PCB power path (5 V module). Battery only if built. | Battery is optional (see below) |

Notes:
- **Fuse parts:** skip the online store (Hemlock) because of shipping. Buy a
  regular-size ATC inline holder (rated 15 A or more, thick wire) and 15 A ATC
  fuses at an auto parts store, or ask the ECE shop.
- **No fire box.** We dropped the $80 box as overkill.
- **Battery is optional and not counted** in the totals. If built later, it is
  a protected 3-in-series, 2-in-parallel pack (about 11.1 V). Charge only while
  awake and in the room, on a tile or metal tray, never overnight, never use a
  dented or puffy cell. Buy vs build is decided in late November.
- The turret should draw about 45 W on average and about 87 W at peak (a
  deliberately cautious guess).

---

## Decision 8: Raspberry Pi 5 8 GB, bought at P2; Coral waits

**What:** Raspberry Pi 5, **8 GB** (decided Oct 16). The RAM can't be upgraded
later. We do **not** buy the Pi now (decided Oct 17): the Pi, power supply and
cooler are P2 purchases, ordered by about Nov 13.

**Training vs running (the thing that confused us):**
- **Training** = teaching the model with thousands of pictures. Heavy work. Done
  once on a laptop or free Google Colab.
- **Running** = using the finished model on live camera frames. Light work.
  Done by the Pi, by itself, with no laptop needed.

**Coral accelerator: PINNED.** It plugs into the Pi (USB), so adding it later
does not change the PCB or the wiring. Keep the 5 V module sized for 5 A and
leave a little space in the enclosure. Decide at P2 after measuring the model on
the Pi alone. Without it the Pi's CPU runs the model; this probably meets our
2-5 detections-per-second goal but is NOT verified. Its price swings widely
($89-$200) and the Newark listing is unusable (deliveries from Jan 2027).

---

## Decision 9: One USB camera, bought now, used from day one (decided Oct 17)

**What:** **Arducam 1080p HDR autofocus USB camera** (78 degree view, small metal
body), $19.99 on Amazon. It replaces the Raspberry Pi Camera Module 3 and its
ribbon cable, which are removed from the BOM.

**Why:**
- Training photos must come from the **same camera** the turret will use, or
  the model sees a different "look" than it was trained on.
- The camera mount in the CAD depends on the camera's exact size, so choosing
  the final camera now means no redo.
- A USB camera works on the laptop today and plugs into the Pi later. The
  Camera Module 3 only works on a Pi, and we are not buying the Pi yet.

**Plan:** unscrew it from its stand and mount just the case in a 3D-printed
holder.

**Checks when it arrives:**
- The page does not list MJPEG. Confirm **MJPG at 1920x1080, 30 fps**
  (`v4l2-ctl --list-formats-ext` on Linux, or OBS on the laptop). Over USB 2,
  uncompressed 1080p is only a few fps, so MJPEG is required. Return it if
  missing.
- Measure the case with calipers before finishing the mount.

**Trade-off we accepted:** cheaper image quality than a $39-65 camera. If the
project continues, we upgrade, which means retaking the main training dataset.
So collect only a small starter set on this camera to prove the pipeline.

---

## Decision 10: Laser is IN Prototype 1; cheap 5 mW module chosen (decided Oct 17)

**What:** In P1 the laptop runs the hand-detection model on frames from the
Arducam USB camera. When it is confident, the laptop sends one message over USB
serial to the STM32, which switches the laser on. No Pi needed in P1.

The laser is a cheap **AREALER 5 mW, 650 nm, 5 V red dot module** (4-pack,
$7.61 at Walmart). The STM32 pin is too weak to power it directly, so an
**IRLZ44N logic-level MOSFET** (2 for $3.60 at Digi-Key, one spare) acts as the
on/off switch, with power coming from 5 V.

---

## Decision 11: Mechanical build and ordering

- A 3D printer is available, so the pan-tilt structure and camera holder are
  printed. Exact **screws and fasteners** are chosen after the CAD (NEMA 17 motor
  mounts are usually M3). The BOM holds a $15 placeholder.
- Wires and a USB cable are already owned.
- **Monday Oct 19** is the P1 order day, after checking what the Purdue ECE shop
  has. Amazon items (motor kits, adapter, jack, camera) go in one order over
  $25. Digi-Key takes the Nucleo (if the ECE shop has none), 2 MOSFETs and the
  surge diode.
- Slow China orders (if any) are placed early, and a $30 "unknowns" allowance is
  in the BOM.

---

## Still open (not decided)

1. **5 V module for the Pi:** Pololu vs AliExpress. Revisit about Oct 24, and it
   must be settled before the PCB layout (Oct 30).
2. **YOLO fine-tune vs from-scratch network.** Parked for now. Note the project
   rule says "self-trained, not pretrained". Fine-tuning a small YOLO on our own
   photos is the practical route; training a tiny network from scratch is a
   stronger story but riskier for the Dec 12 deadline. Resume wording must
   match whichever we do.
3. **Confidence threshold** for firing the laser (decided during P2/P3).
4. **Coral:** pinned, revisit at P2 (about Nov 24).
5. **Battery: buy vs build** (decided in late November).
6. **Friend's funding and role.** A friend may help fund the project in exchange
   for a resume credit. The role split and who keeps the hardware are not
   defined yet; agree on them so each person's resume claim is honest.
7. **Overall budget.** The original ~$370 target is no longer binding. The BOM
   currently counts about **$540 without optional items** and about **$733 with
   the battery set and Coral**. Real prices will shift as we order.

## Hard rules that do not change

- No weapon. No RF jammer (illegal, FCC).
- Laser is low-power, only fires above the confidence threshold, never aimed at
  people.
- The AI model is self-trained. It makes the real detect/classify decision.
- Breadboard first, then finalize the PCB (PCB parts must be ordered by Nov 2).
