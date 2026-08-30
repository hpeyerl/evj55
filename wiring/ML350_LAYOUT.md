# ML350 Fuse/Relay Box - Layout Scaffold

Working design doc for migrating the truck's power distribution from the hand-wired
AliExpress box to the reused Mercedes ML350 box. Paper scaffold **before** touching the
live Splice FuseRelay page.

Sources: `ML350 fuse box - Pinout.csv` (box truth), `ml350_annotated.png` (PCB),
`evj-55.plan.json` (old Splice page = models the DEAD AliExpress box).

Status: 2026-08-27 first pass. (!) = needs a buzz-out / confirm at the box.

---

## 1. Relay roster (confirmed at box 2026-08-24)

11 sockets, **V empty -> 10 populated relays.** All `4RA` = SPST-NO (make-only), no NC anywhere.
Passive PCB, **no flyback diodes** (small group has an integral suppression *resistor*).

| Relay | Part | Class | Contact rating |
|-------|------|-------|----------------|
| **K, R, M, N** | Hella `4RA 007 793-02` (MB `A 002 542 15 19`) | High-current | ~40-70A (sibling -03 = 70A; -02 unprinted) |
| **L, O, P, S, T, U** | Hella `4RA 931 716-00` | Standard | 20A |
| V | - | empty socket (DNP) | - |

Pin convention (BOTH types): **coil = pins 1,2  /  NO contacts = pins 3,5.** (Not 85/86/30/87.)

---

## 2. Relay -> fuse rail -> output pin (from CSV)

| Relay | Fuse rail | Output connector pins | Note |
|-------|-----------|-----------------------|------|
| **N** | f52-f56 (5-gang) | P5:5-14 | Master high-current parallel rail |
| **M** | f49 | P4:13,14 -> H1:1 | Single isolated loop |
| **R** | f59,f60,f61 | P6:5-10 | 3-fuse parallel rail; **P bridged onto f60/f61 of this same rail** (buzz-out 2026-08-30) |
| **K** | f62,f63 | P6:11-14 | Dual-fuse sub-bus |
| **P** | f60,f61 | P6:7-10 | **RESOLVED (buzz-out 2026-08-30):** R, P, f60, f61 = one common node, nothing else on the rail -> **P is NOT an independent output, it's bridged onto R's f59-f61 rail.** (!) Confirm P socket populated vs empty - if it holds a relay, R+P are hard-paralleled and P can't serve as a separate relay. |
| **O** | f57 | P6:1,2 | Single isolated loop |
| **S** | f44 | P4:3,4 | |
| **T** | f45 | P4:5,6 | |
| **U** | AddBrown | (add-a-fuse) | ganged w/ S,T - see sec 4 |
| **L** | AddRed | (add-a-fuse) | |

Everything else (f20-f48 minus S/T outputs, f50/51/58, f64/65) = **constant Bat+ busbar "B"**,
always-hot, straight to output pins. f64/f65 = empty slots.

---

## 3. Coil control - as-traced ((!) several unverified)

Box is **ground-switched**: coil-high sits at a fixed feed, relay fires by **sinking coil-low.**
BUT the coil-high feed is **NOT uniformly Bat+** - trace each individually.

| Relay | Coil-high | Coil-low (control) tap | Gotcha |
|-------|-----------|------------------------|--------|
| K | Bat+ common | **P4:7** | (!) P4:7 has NO terminal - must add one to control K |
| R | Bat+ common | P5:1 | ok (populated) |
| M | Bat+ common | P5:14 | ok |
| L | Bat+ (direct) | **P4:1** | (!) P4:1 has NO terminal - must add one |
| N | external both legs | P6:12 & P5:2 | not Bat+ commoned |
| O | fuse 52 feed | P6:4 | fused/second-stage feed |
| P | fuse 50 feed | P5:9 | fused feed |
| S/T/U | ganged, external both legs | **P5:4 & P5:10** | all 3 arm together |

Center-of-socket **BAT tap** exists (unused) at U/P/S/T for a 5-pin variant - ignore for now.

---

## 4. Load assignment - HYBRID (current direction, 2026-08-27 *)

**Herb's call (2026-08-27):** the aggressive "collapse to ~1-2 relays" was too far. Split by
current class:

- **Muscle loads -> dedicated relay + fuse EACH** (motor/actuator loads with real current;
  want independent switching, fault isolation, and full de-power on sleep):
  **Oil Pump  /  EPB  /  EPAS  /  Rad Fan  /  iBooster  /  Coolant pumps.**
- **Signal-level controller ENABLES -> collapse into ONE ganged ignition enable** (milliamps,
  not muscle): Zombie  /  inverter  /  bat-boxes  /  controls -> the **S/T/U gang**.

=> ~6 muscle relays + 1 gang. Fits the ML350 (K,R,M,N big + L,O,P,S,T,U small) with spares.

### Proposed relay map ((!) current figures = homework)

| Load | Current class | -> Relay | Note |
|------|---------------|---------|------|
| EPAS | ~40-80A (heaviest) | **N** (5-gang master) | |
| iBooster | high peak on hard braking (!) | **K** or **R** (big) | NEW to table; exact A = homework |
| Oil Pump | moderate (!) | **M** or a big spare | trans oil pump |
| EPB (elec park brake) | brief actuation | **20A** (L/O/P) | = old "Parking Brake" |
| Rad Fan | **~100W ~ 8A** | **20A** (L/O/P) | small relay plenty; coil = Zombie `CoolingFan` OR overtemp switch |
| Coolant pumps | motor, low-teens A (!) | **20A** (L/O/P) | OR Zombie low-sides directly - TBD |
| **S/T/U gang** | signal enables | Zombie + inverter + bat-boxes + controls arm together on IGN | |
| CDL | - | **spare** | |

Inverter is now an **enable** (in the gang), not a muscle relay - it has its own contactor/driver.

Caveat carried forward: for anything you'd instead leave permanently fused, confirm its
**key-off quiescent draw** is negligible first (STR parasitic-drain concern).

---

## 5. Coil control ownership

| Owner | Loads | How |
|-------|-------|-----|
| **Zombie** | coolant pump(s) | already low-side -> literal drop-in to coil-low |
| **Ignition-gated** | EPAS, inverter, park brake, oil-pump enable, bat boxes, Zombie-enable, rad fan | ONE ignition-driven low-side grounds the group (fail-safe) |
| **CM3** | *future/additive only* | remote-fire (e.g. Webasto pre-heat) - but Webasto is likely CAN/W-Bus, so probably NOT a box relay at all |

CM3 owns **no** fuse-box relay today.

---

## 5b. Power domains - THREE states (2026-08-27 *)

The truck has three power states, not two. This decides which rail each electronics load sits on.

| State | Trigger | Alive |
|-------|---------|-------|
| **Drive** | ignition (key) | Zombie, EPAS, dash, muscle relays ... + BMS |
| **Charge** | **AC plugged in** (key OFF) | Zombie + charger + **BMS** + coolant pumps |
| **Sleep/off** | bounded STR -> full powerdown | **CM3 standby only** |

**Keyswitch rule:** the column keyswitch carries **only relay coil current** (tens of mA), never
load current. Loads pull from battery through relay contacts; the key just closes the relay.

**CM3** = **permanent-B+** with ignition as a **wake-GPIO** (not its power source) - needs standby
to hold RAM through STR. Its standby draw = the bounded-STR parasitic budget.

**Small awake-only electronics** (M5Dial, dash peripherals) = **switched-B+ rail**, each fused, off
the ignition/master relay. Not one relay each.

### Charge domain - RESOLVED via the charger connector (2026-08-27) *

The onboard charger's connector was built for exactly this. Pinout:

| Pin | Function |
|-----|----------|
| A / G | CAN Bus High / Low (Zombie <-> charger) |
| **B** | **BMS/VCU Power +, 12V+ when AC applied** <- the charge-wake source |
| **C** | BMS/VCU Power - (12V-) |
| E / F | HVIL interlock loop (HV safety, series - NOT power) |
| T | DCDC logic power (apply 9-16V) |
| S | DCDC enable (9-16V) - **OR'd with Zombie's CAN enable** (Zombie = DCDC master) |

**Wake scheme (FINAL 2026-08-27 - see `charge-wake-arch.svg`/`.png`):** OR the *trigger*, let a relay
switch battery - **no standalone relay, no power diodes**.

```
  Ignition ->|-+                         (>| = signal diode, mA, anti-backfeed)
               +-o OR -+--> low-side FET --> sinks WAKE-RELAY coil-low
  Pin-B ----->|-+      +--> CM3 wake-GPIO
                                          WAKE RELAY = ML350 socket K or R (ground-switched):
                                            coil-hi = Bat+ (permanent)  /  coil-lo = FET
                                            contacts: Bat+ ---> Zombie + BMS logic rail
```

- **Diodes are two SIGNAL diodes on the coil trigger** (milliamps) - they only stop Ignition and
  Pin-B backfeeding *each other*. **No power diodes; no backfeed into the keyswitch.**
- **Real current comes from Bat+ through the relay contacts**, so **pin B only drives the FET gate
  (uA)** -> its capacity is a non-issue.
- ***Pin-B rating (datasheet) = 0.16A (pin C same).** This SETTLES the design: 160mA **cannot**
  power Zombie+BMS directly (BMS ESP32 alone ~120-160mA w/ WiFi; VCU board adds ~100-200mA ->
  ~250-400mA total). Pin B is a **wake-signal supply, not a power bus** (160mA ~ one relay coil -
  the charger intends pin B to *fire a relay*, not run electronics). => the FET/wake-relay is the
  correct branch, **not** a fallback; a plain diode-OR onto the logic rail would brown them out.
- **One ML350 socket (K or R) + one low-side FET + two signal diodes**, all on the HAT. K and R are
  the free sockets and both are Bat+-commoned coil-high (ground-switched) -> coil-hi is *permanently*
  Bat+ (always available key-off (ok)); the FET sinks coil-low when (Ignition OR Pin-B) is hot.
- **CM3** = permanent-B+; the **same OR signal is its wake-GPIO**. Display OFF during charge = CM3
  software (headless wake, backlight off; SoC-over-Sim7060 is a software job). Not wiring.
- **Rad fan (O) + Coolant (P)** = Zombie-controlled, **coil-lo <- Zombie, power <- Bat+** -> they run
  whenever Zombie is awake (drive *or* charge). Rule: feed O/P from Bat+, not an ignition-only rail.
- **HV-Request is NOT the wake** - it's a *close-contactors command to an already-powered Zombie*.
  The wake relay is what powers Zombie up on plug-in.
- **BMS** = Lilygo T-CAN485 ESP32, ~50-150mA, **no CAN-wake**, no park-monitoring needed -> rides the
  logic rail (dies cleanly when neither driving nor charging). No dedicated relay.
- Open picks/checks: **K vs R** for the wake socket; pin-B current rating; and (firmware, non-blocking)
  how Zombie *enters charge mode* once awake - read Stm32-vcu.

---

## 6. Delta vs current Splice FuseRelay page (the rototill checklist)

The page (`page_1774975610452_xv22udce3`) modelled the AliExpress box. Conversion progress:

- [x] **Delete phantom K18/K19/K20** + partner fuses F18/F19 + both dup F20 (done 2026-08-27,
      committed baseline `f07fe62`/plan push `1772d7a`).
- [x] **Rename K11-K17 -> real relays** (done 2026-08-27): N=EPAS, M=Oil Pump, L=EPB, O=Rad Fan,
      S=Zombie / T=Inverter / U=Bat Boxes (the ignition-enable gang). K/R/P still free.
- [ ] **Add** iBooster (-> K or R, big) and Coolant pumps (-> P) as NEW symbols.
- [ ] Re-number fuses to **real ML350 slots** (f20-f63) per sec 2; map old logical F11-F17/F21/F23.
- [ ] Draw coils **ground-switched** - coil-high fixed, control on **coil-LOW** (per sec 3) + S/T/U gang.
- [x] Resolve **f60/f61 R/P "???"** shared rail - **buzz-out 2026-08-30: R, P, f60, f61 all one common node, nothing else on the rail; P bridged onto R's rail (not independent).**
- [ ] Orphan purge (~491 stale assignment refs): **DEFERRED** - harmless, and no bridge command
      drops the keys (only a full `save_plan` compacts them). Left in place by decision 2026-08-27.
- [ ] Note: coil sources were never actually wired in the plan - only floating legend symbols
      + IGN+/12V+ stubs. Coil intent = design intent, not drawn.

---

## 7. Open homework (at the box)

- [x] f60/f61 R-vs-P shared rail - **buzz-out 2026-08-30: not "R vs P" - R, P, f60, f61 are ONE common node, nothing else on it. P is bridged onto R's f59-f61 rail (not an independent output). (!) Confirm whether P socket is physically populated - if so, R+P are hard-paralleled and P is unusable as a separate relay; adjust the relay budget.**
- [x] Add terminals at **P4:1 (L)** and **P4:7 (K)** for external control - **BOTH CONFIRMED as coil-low control taps (2026-08-30); physical crimp insertion DEFERRED (not a blocker).**
      **CONFLICT found 2026-08-30:** the Pinout CSV maps **P4:1,2 -> f43** and **P4:7,8 -> f46**,
      BOTH "tied directly to the constant Bat+ busbar B." If that copper is really busbar, these
      positions are always-hot +12V and **cannot** be K/L coil-low control taps (a terminal there
      ties coil-low to +12V -> relay never switches / can cook the sinking driver). §3's P4:1/P4:7
      were flagged "(!)" unverified. **BUZZ P4:1 & P4:7 against a known Bat+ pin (f20 @ P1:9/10)
      FIRST:** continuous = busbar (item moot; K/L need a different control path, e.g. in-box FET
      on the coil pin) // isolated = §3 was right, then just add terminals.
      **RESULT 2026-08-30: P4:1 & P4:7 do NOT connect to B+** -> isolated, so §3's coil-low-control
      reading stands and the CSV's f43/f46-busbar mapping for these two pins is WRONG. Remaining:
      confirm P4:1->L coil pin and P4:7->K coil pin continuity, then add terminals (harvest a
      spare from any unused busbar-B fuse-output position).
      **CONFIRMED 2026-08-30: P4:1 -> L's control pin AND P4:7 -> K's control pin** (both genuine
      coil-low taps; the CSV's f43/f46-busbar mapping for these pins is wrong). Crimp insertion
      deferred; donor terminals = P5:9 (orphaned P coil-low) + any spare busbar-B fuse output.
- [ ] Current rating on the `4RA 007 793-02` (K/R/M/N) - confirm the ~40-70A class figure.
- [ ] Key-off quiescent draw per controller (gates the Option-B permanent-feed decision).
- [ ] Confirm coil-high feed on the relays not yet Sharpie-traced.
