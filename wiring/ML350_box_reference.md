# Mercedes ML350 Fuse/Relay Box - Hardware Reference

A concise reference for reusing the Mercedes ML350 (W164-era) fuse/relay box in a DIY build.
Box-hardware facts only. Relay/coil traces below were buzzed out on a single unit - **verify on
your own box** before relying on them; connector/coil details can vary by part number and year.

Source of the pin map: the box's own pinout label + continuity buzz-out.

---

## 1. Relays

**11 relay sockets, labelled K R M N L O P S T U V.** All are `4RA` Hella = **SPST-NO
(make-only), no normally-closed contact anywhere.** The PCB is passive - **no coil flyback diodes.**

| Sockets | Part | Class | Contact rating |
|---------|------|-------|----------------|
| **K, R, M, N** | Hella `4RA 007 793-02` (MB `A 002 542 15 19`) | high-current | ~40-70A (sibling `-03` is 70A; `-02` unprinted) |
| **L, O, P, S, T, U** | Hella `4RA 931 716-00` | standard | 20A |
| **V** | (empty socket) | - | - |

- **Pin numbering (both types): coil = pins 1,2  /  NO contacts = pins 3,5.** (NOT the ISO
  85/86/30/87 - matters when you socket-wire.)
- The **20A group** (`4RA 931 716-00`) has an **integral coil-suppression RESISTOR** (molded across
  the coil) -> the coil is **non-polarized**, and it already has spike suppression built in.
- Sockets **U, P, S, T** have an extra center contact (between the two coil pins) tied to **BAT** -
  a provision for a 5-pin/center-Bat relay variant. The standard 4-pin relays don't engage it; unused.

## 2. Relay -> internal fuse rail -> output connector pins

| Relay | Fuse rail | Output pins | Note |
|-------|-----------|-------------|------|
| **N** | f52-f56 (5-gang) | P5:5-14 | high-current parallel rail |
| **M** | f49 | P4:13,14 -> H1:1 | single isolated loop |
| **R** | f59,f60,f61 | P6:5-10 | 3-fuse parallel rail |
| **K** | f62,f63 | P6:11-14 | dual-fuse sub-bus |
| **O** | f57 | P6:1,2 | single isolated loop |
| **S** | f44 | P4:3,4 | |
| **T** | f45 | P4:5,6 | |
| **P** | (bridged onto R's f59-f61 rail) | - | **P is NOT an independent output** - it parallels R. Closing P just parallels R's contacts. |
| **L, U** | (route to add-a-fuse output positions) | - | not standard numbered slots; need an add-a-fuse holder or a jumper from a spare slot |

**Everything else = a constant Bat+ busbar "B"**: always-hot, straight to the output pins. Most of
the ~46 fuse slots (roughly f20-f65) hang off this busbar. **f64/f65 = empty.**

## 3. Coil wiring (how each relay is switched)

The box is **ground-switched**: each coil's high side sits at a fixed feed, and the relay fires by
**sinking its coil-low to ground.** The coil-high feed is **NOT uniformly Bat+** - trace each:

| Relay | Coil-high feed | Coil-low (control) tap | Note |
|-------|----------------|------------------------|------|
| K | Bat+ common | P4:7 | ⚠ pin has NO terminal fitted - add one to control K |
| R | Bat+ common | P5:1 | populated, ready |
| M | Bat+ common | P5:14 | populated, ready |
| L | Bat+ (direct) | P4:1 | ⚠ pin has NO terminal fitted - add one |
| N | external (both legs) | P6:12 & P5:2 | not Bat+ commoned |
| O | fuse-52 feed | P6:4 | fused/second-stage feed |
| P | fuse-50 feed | P5:9 | fused feed |
| S/T/U | ganged (both legs external) | P5:4 & P5:10 | all three arm together |

## 4. Output connectors + pigtail population

Output on connectors **P1-P6, D1, H1**. Not every position is pigtailed from the factory - only the
populated pins are usable without adding terminals:

| Connector | Populated pins |
|-----------|----------------|
| P1 (10-pin) | 1, 2, 3, 5, 7, 10 |
| P2 (10-pin) | 3, 4, 5, 6, 7, 9, 10 |
| P3 | 1, 4, 7 |
| P4 (10-pin) | 2, 3, 4, 5, 6, 8, 9, 10 |
| P5 (14-pin) | 1, 2, 3, 4, 6, 8, 9, 11, 12, 14 |
| P6 | 2, 3, 4, 5, 6, 8, 9, 11, 12 |
| D1 | 2, 4, 6 |
| H1 | 1, 3 |

## 5. Practical notes for reuse

- **~46 fuse slots, ~8 usable relays** (K R M N big + L O P S T U small; V empty, P dependent on R).
  Plenty of always-hot fused distribution; relay count is the limiting resource.
- **No flyback diodes on the board.** The 20A group self-suppresses (resistor); the high-current
  group was not confirmed. If you drive a coil from a bare semiconductor (FET) instead of a
  mechanical contact, add your own flyback/clamp at that driver.
- Relays are **generic sourceable Hella 4RA minis** - nothing bespoke; any SPST-NO ISO-ish mini fits
  the standard sockets (mind the 1,2 / 3,5 pinout).
- The box case is the intended **ground/heatsink**; bond it to chassis.
