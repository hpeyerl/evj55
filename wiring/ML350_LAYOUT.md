# ML350 Fuse/Relay Box - Layout Scaffold

Working design doc for migrating the truck's power distribution from the hand-wired
AliExpress box to the reused Mercedes ML350 box. Paper scaffold **before** touching the
live Splice FuseRelay page.

Sources: `ML350 fuse box - Pinout.csv` (box truth), `ml350_annotated.png` (PCB),
`evj-55.plan.json` (old Splice page = models the DEAD AliExpress box).

Status: 2026-09-12 - **master-contactor architecture (sec 0) is now primary; it supersedes
the V-master coil scheme and the always-hot-busbar model.** 2026-08-27 first pass below.
(!) = needs a buzz-out / confirm at the box.

---

## 0. ARCHITECTURE (CURRENT) - external master contactor, no V (2026-09-12)

Supersedes the "always-hot busbar B" model and the V-master-relay coil scheme (sec 3).
Sections 1-2 (box facts) still stand; sec 3/4/5/5b/6 are historical where they describe V -
see the banner on each.

**Power entry = ONE external contactor on the B+ feed bolt.**
- **Panasonic AEV14012 (M21):** 120A SPST-NO, 450V DC contacts, 12V coil, 34 ohm ->
  ~0.35A / ~4.2W hold. Plain coil (**NOT** economized) - fine here, because the contactor is
  OPEN in sleep, so the coil only burns in drive (DCDC running) and charge (shore power).
  Check the main-terminal polarity marking (magnetic blowout); wire battery side to the
  marked terminal.
- **Coil-hi = permanent Bat+** (pre-contactor, so it's available key-off). **Coil-lo sunk by a
  low-side FET** driven by **(Ignition OR charge Pin-B)** through two signal diodes (the
  existing charge-wake OR, sec 5b). The **same OR node = CM3 wake-GPIO** and the **BOX-AWAKE**
  signal for the EPB enable.
- **Trigger location (DECIDED 2026-09-12): a small PROTOBOARD in the Hammond box next to the
  ML350 - explicitly NOT the HAT** (no HAT respin). The protoboard holds the 2 signal diodes +
  OR + low-side FET + contactor-coil drive; it takes IGN, charge Pin-B, permanent Bat+, GND and
  exposes **BOX-AWAKE** (to CM3 wake-GPIO and EPB enable). On the Splice page it's ONE black-box
  module, not discretes; the HAT does not own the box-on logic.
- Effect: **the entire box busbar B is now SWITCHED** - hot only in drive or charge, fully
  dead in sleep = zero parasitic drain. The old constant-Bat+ busbar is gone.

**F-Main** (battery -> box feed bolt): **~100A slow-blow (MEGA / ANL) on 4-6 AWG.** Protects
the feed cable + bolt only (each load is individually fused inside). Keep **<= 120A**
(contactor carry); slow curve so it rides EPAS inrush without nuisance-blowing. Final number
gated by EPAS worst-case current (homework).

**Three power states, gated by this ONE part:**

| State | Trigger | Box | Notes |
|-------|---------|-----|-------|
| Drive | Ignition | hot | everything available |
| Charge | Pin-B (key off) | hot | **steering / brakes / EPB available** (Blazer-like, decided 2026-09-12) |
| Sleep | neither | dark | zero parasitic; only CM3 standby (fed upstream of contactor) |

**V master relay DROPPED (2026-09-12).** With steering / brakes / EPB wanted live in charge,
V had nothing left to gate drive-only. The oil pump (the one true drive-only load) is
Zombie-PWM'd, so it stays idle in charge even when powered - doesn't need V either. Dropping V
also removes the coil-low commoning bus and the K@P4:7 / L@P4:1 crimp-terminal adds.

**Box collapses to FUSE-DIRECT + let the controllers manage behavior:**
- **EPAS, iBooster, oil pump = fuse-direct off the switched busbar** (no per-load relay).
  Relays **K, N, M are freed** (leave seated unused, or repurpose).
- **iBooster stays on the master (door #2).** SPOF accepted: iBooster power-loss = unboosted
  manual pedal (mechanical pushthrough), not zero brakes. Fail-open only happens at
  charge/park speeds where it's a heavy pedal at walking pace.
- **EPB = fuse-direct power + controller ENABLE on the BOX-AWAKE signal (IGN OR Pin-B)**
  (DECIDED 2026-09-12). NOT raw always-on and NOT raw-ignition - tying the enable to box-awake
  keeps EPB toggleable while parked charging (forgot-pawl case) yet dead in sleep. **L freed** as
  a relay.
- **CM3 = CONSUMER of EPB / vehicle state only** (for later policy decisions). It does **not**
  drive EPB.
- **Rad fan = relay M, Coolant pumps = relay R** (revised 2026-09-13). Both sockets have coils that
  are **already factory-wired the way we need** - coil-hi on the Bat+ common (= switched B+ now),
  coil-lo brought out to a **populated P-pin** - so **no coil rework and no S/T/U gang** (this drops
  the earlier O-rework + gang plans):
  - **Rad fan -> M:** coil-lo **P5:14** <- Zombie CoolingFan (or overtemp switch); contact out f49 -> H1:1.
  - **Coolant -> R:** coil-lo **P5:1** <- Zombie CoolantPump; contact out f59 -> P6:5,6 (2 pins for the
    higher-flow VW pump). Relayed (not Zombie-direct) so the pump's running + inrush go through R's
    contacts, not the Zombie GP-out FET.
  Both coils energize only when the box is hot (coil-hi = switched B+), so they run in drive AND charge
  (Zombie awake in both). R and M are the big 4RA relays = oversized for these loads = reliable.
- Everything else = fuse-direct.

**Failure modes:**
- Master **fails open** mid-drive: box goes dark. EPAS drops (accepted - assist only matters at
  parking speed) and brakes degrade to manual pedal. Single point, but bounded consequence.
- Master **welds closed**: box never sleeps -> battery drain over days. **Add a box-hot sense
  line to CM3** to alarm (CM3 reads it as state; it does not act on power).

**Relays in use: M (rad fan) + R (coolant)** - chosen for their ready coils (see sec 8). **Freed:**
K, N, O, S, T, U, V (+ P dead). The ML350 is now mostly a fused distribution block + two relays
(fan, coolant), with the external master contactor doing all power-state gating.

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
| **U** | AddBrown (U output) | - | **RE-TASKED 2026-09-02: U = IGN-switched accessory relay.** Coil on the S/T/U gang (arms with ignition); contacts pass Bat+ -> **F21 status feed (pg6) + F23 CDL (pg8)**, both ignition-switched (piggybacked on ONE relay to save relays; V stays the spare). (!) PHYSICAL: F21/F23 are currently CONSTANT-busbar slots - making them IGN-switched via U means isolating them from the Bat+ busbar and feeding from U's switched output (or add-a-fuse on U's AddBrown output - and you're short that holder). Resolve at the box. |
| **L** | AddRed (output) | - | EPB. (!) **CORRECTION 2026-09-04: Herb does NOT have the AddRed add-a-fuse holder** (they are color-keyed; his only pigtail is a not-red/not-brown color). So L needs the SAME cut/reroute as U: isolate a real slot from the Bat+ busbar and jumper L's switched output in. ML350 has ~40 mostly-spare real slots f20-f48 - prefer a spare real slot. |

Everything else (f20-f48 minus S/T outputs, f50/51/58, f64/65) = **constant Bat+ busbar "B"**,
always-hot, straight to output pins. f64/f65 = empty slots.

---

## 3. Coil control - as-traced ((!) several unverified)

> **[SUPERSEDED 2026-09-12 by sec 0 - kept for box facts.]** The V-master-relay coil scheme
> in this section is DROPPED. The per-relay coil-pin traces below are still valid box facts,
> but the muscle loads are now fuse-direct (no coil-low bus, no V). Ignore the V/option-B wiring.

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

**[SUPERSEDED 2026-09-12 - V dropped, muscle loads fuse-direct, see sec 0. Kept for history.]**
**Coil-drive intent (Herb 2026-09-02):** K(iBooster), N(EPAS), M(oil-pump), L(EPB) + the S/T/U gang
all **ARM ON IGNITION (drive-mode)** - one common ignition trigger. M is on/off enable only (Zombie
PWMs the pump; pump quiescent until PWM). R = wake FET (drive OR charge, done). O = Zombie CoolingFan
(thermostatic). P dead. **DECIDED + DRAWN 2026-09-02 (option B, RELAY not FET):** coil-highs (85) on
**Bat+**; coil-lows (86) of K/N/M/L/S/T/U **commoned into one bus** grounded by the **V master relay**
(V coil = IGN(drive); V contacts sink the bus to GND on ignition - no FET needed, uses the spare V
socket + a relay from inventory). R coil-low -> wake Q1; O coil-low (86) -> Zombie **GP Out 1** (J1
pin 31), O coil-high -> Bat+ constant (also fixes the old "fan must be live in charge" gating). Drawn
on the FuseRelay page. (!) verify IGN(drive) can source V's ~150mA coil.

Center-of-socket **BAT tap** exists (unused) at U/P/S/T for a 5-pin variant - ignore for now.

---

## 4. Load assignment - HYBRID (current direction, 2026-08-27 *)

> **[REVISED 2026-09-12 by sec 0.]** The per-load muscle relay map below is HISTORICAL:
> EPAS/iBooster/oil-pump/EPB are now **fuse-direct** off the switched busbar (no relay), so
> K/N/M/L are freed. Only O (rad fan) keeps a relay. Use this table only for the current-class
> homework figures.

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
| CDL | ign-switched (actuator) | **U** (shared w/ F21 status) | F23; U = the IGN-switched accessory relay - piggybacks status + CDL on one relay to save a relay; V stays the spare |

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

> **[UPDATE 2026-09-12, see sec 0.]** The wake scheme below is now realized by the **external
> master contactor**, which gates the WHOLE box, not just the Zombie/BMS logic rail. The
> internal "wake relay = socket K or R" is REMOVED (R freed). Charge now keeps steering/brakes/
> EPB available. The three-state model, the charger-connector pinout, and the Pin-B rating below
> all still stand - only the relay that acts on them changed (internal socket -> external AEV14012).

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
- [x] **Add iBooster (=K)** - DONE. **[UPDATED 2026-09-12: coolant is now a RELAY (coil low-sided by
      Zombie), not Zombie-direct - new higher-flow VW pump; socket TBD by pump current; see sec 0. The
      old ~480mA-direct note is obsolete.]** U re-tasked to the ign-switched accessory relay (F21/F23).
- [x] **Re-number fuses to real ML350 slots** - DONE 2026-09-02: F11-F17 -> f44/f45/f49/f52-56/f57/
      AddRed/sw12(f59-61); F21/F23 -> ign-switched via U (their real slots pending the cut/reroute TODO).
- [~] **Coils** - the 2026-09-02 V-master scheme is **SUPERSEDED 2026-09-12 (sec 0)**. New target for the
      Splice page: external master contactor gates the whole box; EPAS/iBooster/oil-pump = fuse-direct off
      the switched busbar (delete K/N/M/L as muscle relays); EPB = fuse-direct power + ignition-gated
      controller enable; O rad-fan coil-lo -> Zombie GP Out 1 (kept); P dead; R/V dropped. The page still
      shows the V scheme and needs re-doing. (2026-09-02 cleanup - old coil-ground shorts + red/violet
      AliExpress cruft - stays purged.)
- [x] Resolve **f60/f61 R/P "???"** shared rail - **buzz-out 2026-08-30: R, P, f60, f61 all one common node, nothing else on the rail; P bridged onto R's rail (not independent).**
- [~] Orphan purge: the visible old **red/violet AliExpress conductors + coil-ground shorts were PURGED
      2026-09-02** (canvas decluttered). The ~491 stale assignment refs remain DEFERRED (harmless; only a
      full `save_plan` compacts them).
- [~] Coil sources: the V ignition-master wiring (2026-09-02) is now SUPERSEDED (sec 0). Re-draw per the
      master-contactor + fuse-direct model above.

---

## 7. Open homework (at the box)

- [x] f60/f61 R-vs-P shared rail - **buzz-out 2026-08-30: not "R vs P" - R, P, f60, f61 are ONE common node, nothing else on it. P is bridged onto R's f59-f61 rail (not an independent output). (!) Confirm whether P socket is physically populated - if so, R+P are hard-paralleled and P is unusable as a separate relay; adjust the relay budget.**
- [MOOT 2026-09-12] Add terminals at **P4:1 (L)** and **P4:7 (K)** for external control -
      **no longer needed:** V is dropped and the muscle loads are fuse-direct (sec 0), so K/L are not
      driven as relays. History retained below.
      - **BOTH CONFIRMED as coil-low control taps (2026-08-30); physical crimp insertion DEFERRED (not a blocker).**
      **CONFLICT found 2026-08-30:** the Pinout CSV maps **P4:1,2 -> f43** and **P4:7,8 -> f46**,
      BOTH "tied directly to the constant Bat+ busbar B." If that copper is really busbar, these
      positions are always-hot +12V and **cannot** be K/L coil-low control taps (a terminal there
      ties coil-low to +12V -> relay never switches / can cook the sinking driver). sec 3's P4:1/P4:7
      were flagged "(!)" unverified. **BUZZ P4:1 & P4:7 against a known Bat+ pin (f20 @ P1:9/10)
      FIRST:** continuous = busbar (item moot; K/L need a different control path, e.g. in-box FET
      on the coil pin) // isolated = sec 3 was right, then just add terminals.
      **RESULT 2026-08-30: P4:1 & P4:7 do NOT connect to B+** -> isolated, so sec 3's coil-low-control
      reading stands and the CSV's f43/f46-busbar mapping for these two pins is WRONG. Remaining:
      confirm P4:1->L coil pin and P4:7->K coil pin continuity, then add terminals (harvest a
      spare from any unused busbar-B fuse-output position).
      **CONFIRMED 2026-08-30: P4:1 -> L's control pin AND P4:7 -> K's control pin** (both genuine
      coil-low taps; the CSV's f43/f46-busbar mapping for these pins is wrong). Crimp insertion
      deferred; donor terminals = P5:9 (orphaned P coil-low) + any spare busbar-B fuse output.
- [LIKELY MOOT 2026-09-12] **F21/F23 cut+reroute:** with the master contactor the whole busbar is
  already switched (F21/F23 die in sleep for free), so this reroute is only needed if F21 (status) /
  F23 (CDL) must be dead in **charge** specifically - they almost certainly don't. Drop unless a reason
  surfaces. (Original: isolate F21/F23 from the Bat+ busbar and jumper U's switched output in - U is
  freed anyway now.)
- [SUPERSEDED 2026-09-12] **L/EPB reroute:** L is dropped as a relay (sec 0). EPB power is now
  **fuse-direct off the switched busbar** (any real spare slot, no add-a-fuse), with an
  **ignition-gated ENABLE** to the EPB controller. See the EPB (!) reconcile item below.
- [ ] **V spare socket:** its output DOES route to an (undocumented) DNP fuse slot, so V is usable
  IF populated - but it needs 6 pins Herb likely can't source, so V stays unpopulated/unused.
- [ ] Current rating on the `4RA 007 793-02` (K/R/M/N) - confirm the ~40-70A class figure.
- [ ] Key-off quiescent draw per controller (gates the Option-B permanent-feed decision).
- [ ] Confirm coil-high feed on the relays not yet Sharpie-traced.

**New homework (master-contactor architecture, 2026-09-12):**
- [ ] **F-Main final size:** real numbers now = EPAS 60A + iBooster 40A = **100A coincident** (hard
  steer + hard brake) + fan/coolant ~= 125A -> brushes the AEV14012's 120A. Bump F-Main toward **~120A**
  (contactor limit) or drop in a bigger contactor from the stash for margin; slow MAXI rides brief peaks.
  Pick feed-cable gauge to match.
- [ ] **Protoboard build (Hammond box, next to ML350):** 2 signal diodes + OR + low-side FET +
  contactor-coil drive; ins = IGN, charge Pin-B, perm Bat+, GND; outs = contactor coil-lo + BOX-AWAKE
  (to CM3 wake-GPIO and EPB enable). NOT on the HAT.
- [ ] **Master-contactor drive:** size the low-side FET for AEV14012 coil pull-in + ~0.35A hold; pick the
  two signal diodes for the (IGN OR Pin-B) trigger; confirm coil-hi tap is on **permanent** Bat+
  (pre-contactor). Verify AEV14012 main-terminal polarity/orientation for mounting.
- [ ] **Box-hot sense line to CM3** (weld-closed / stuck-on detection). CM3 reads it as state only.
- [DECIDED 2026-09-12] EPB enable = **BOX-AWAKE (IGN OR Pin-B)** - toggleable while charging, dead in
  sleep. CM3 is a state consumer, not the EPB driver.
- [ ] **Inverter (traction) enable:** hard-gate to drive-only in wiring (charge interlock), or leave it
  to Zombie's charge/drive mutual-exclusion + HVIL? If wiring-gated, it's the one enable that keeps a
  drive-only path.
- [ ] **Unused relay sockets M/N/R/K/T/U/V:** decide leave-seated vs. pull. In use: **O** (rad fan) +
  **S** (coolant, via the S/T/U gang coil).

---

## 8. Proposed load assignments (pending box-check) - 2026-09-12

Concrete map for the rototill, per sec 0 (master contactor, no V, fuse-direct + 2 relays).
Cross-referenced to `ML350 fuse box - Pinout.csv` + the pigtail inventory (sec 7). (!) = box-check.

**Power entry:** Battery+ -> F-Main -> AEV14012 master contactor -> **switched B+ bus** (feeds
busbar B + the MAXI slots + the O/S relay contacts). Trigger = the Hammond-box protoboard (sec 0):
IGN + Pin-B -> diodes -> OR -> FET -> contactor coil; exposes BOX-AWAKE.

**Big loads -> the box's 5 MAXI (large blade) slots** = F24, F29, F30, F35, F40 (all fed off busbar
B = switched; the "1/2" output positions on P1/P2/P3 are heavy spades, ~10/12 AWG, confirmed 2026-09-13):

| Load | MAXI -> output | Note |
|------|----------------|------|
| EPAS | **F24** 60A -> P1:2 | heavy spade; factory fuse 60A; 10AWG rides the brief stall peaks |
| iBooster | **F29** 40A -> P1:1 | heavy spade; Tesla fuses it at 40A |
| spare | F40 -> P3:1 | populated |
| spare | F30 -> P2:2, F35 -> P2:1 | output pigtails currently unpopulated |

**Relays (only 2):**

| Relay | Load | Fuse -> pin | Coil |
|-------|------|-------------|------|
| M | Rad Fan | f49 -> H1:1 | READY: hi = Bat+ common (switched B+), lo = **P5:14** <- Zombie CoolingFan |
| R | Coolant pumps | f59 -> P6:5,6 | READY: hi = Bat+ common, lo = **P5:1** <- Zombie CoolantPump |

**Fuse-direct mini slots** (busbar B; avoids F20-F23 = V-contact donors):

| Load | Fuse -> pin | Note |
|------|-------------|------|
| Oil Pump | f37 -> P3:7 | mini |
| EPB power | f39 -> P3:4 | mini (one caliper, not 40A); **ENABLE = BOX-AWAKE** signal |
| Zombie logic | f26 -> P2:7 | 10A |
| Inverter | f27 -> P2:5 | 10A |
| Bat Boxes | f28 -> P2:3 | 10A |
| Controls | f33 -> P2:6 | 10A |
| CDL | f34 -> P2:4 | |
| Status (old F21) | f25 -> P2:9 | |

Unused sockets: K, N, O, S, T, U, V. Relay contacts in play: M + R only.

**Sizing flag:** EPAS 60A + iBooster 40A = 100A coincident, + fan/coolant ~= 125A -> brushes the
AEV14012's 120A and exceeds a 100A F-Main. Brief peaks (slow MAXI rides them), but bump **F-Main
toward ~120A** or use a bigger contactor for margin. Per-branch MAXI (60/40) still protect each load.

**Box-checks (status 2026-09-13):**
- [x] **Single switched domain CONFIRMED:** ONE main B+ bolt feeds everything (busbar B + the 5 MAXI
  slots + the relay contact-commons). The master contactor on that bolt gates the WHOLE box - and this
  also settles the FEED side of the MAXI slots and the O/S relay contacts.
- [x] **F20-F23 out** (contacts pulled for V) - nothing routed there.
- [x] **MAXI OUTPUT routing CONFIRMED (2026-09-13):** MAXIs = F24/F29/F30/F35/F40; outputs on the "1/2"
  positions of P1/P2/P3 are **heavy spades (~10/12 AWG)**. EPAS -> F24 (60A) -> P1:2; iBooster -> F29
  (40A) -> P1:1. F40 -> P3:1 spare (populated); F30/F35 outputs unpopulated. Box carries both natively.
- [x] **Relay-coil choice REVISED 2026-09-13:** use **M (rad fan)** + **R (coolant)** - their coils are
  already coil-hi = Bat+ common (switched B+) + coil-lo on a populated P-pin (M->P5:14, R->P5:1), so NO
  coil rework and NO S/T/U gang. Drops the old O-rework plan entirely.
- [x] **M/R coils buzzed CONFIRMED (2026-09-13):** M coil-lo -> P5:14, R coil-lo -> P5:1 (both
  populated), contact-ins on busbar B. M out f49 -> H1:1; R out f59 -> P6:5,6. **All box-checks done
  except the low-priority P4 pin-count -> cleared to wire + rototill the Splice page.**
- [ ] **P4 pin-count** (CSV 14-pin vs pigtail-walk 10-pin) - low priority, already routed around it.

---

## 9. Splice rototill progress (live canvas) - 2026-09-14

Rototilling the FuseRelay page (`page_1774975610452_xv22udce3`, project `17410eef-...`) to sec 8.
Driven from a fork holding the plan snapshot (cost discipline). Progress:

- **Phase 1 DONE - demolition:** removed the superseded V-master coil scheme + the wake-trigger block
  (33 conductors, 11 nodes: V, Q1, D1/D2/Dz/Dfb/Rg/Rpd, 2 Pin-B ferrules, stray X116).
- **Phase 2 DONE - power entry + coils:** created Perm B+ -> F-Main -> **AEV14012** contactor -> relabeled
  the old Bat+ bus to **"Switched B+"**; **PROTOBOARD** module (IGN / charge Pin-B [freed Dilong pin-B] /
  Perm B+ / GND -> contactor coil + BOX-AWAKE). MAXI **F24**(EPAS)/**F29**(iBooster) inputs on Switched B+.
- **Phase 3 DONE - core loads:** EPAS -> F24 -> "EPAS steering" stub; iBooster -> F29 -> X_iBoost;
  rad-fan relay **M** (contact SwB+ -> f49 -> "Rad Fan" stub); coolant relay **R** (contact SwB+ -> f59 20A ->
  "Coolant pump" stub). Both relay coils wired (see GP-output note).
- **Phase 4 IN PROGRESS:** fuse-direct minis (oil/EPB/Zombie/inverter/bat-boxes/controls/CDL/status),
  BOX-AWAKE -> EPB-enable + CM3-wake (cross-page ferrules), retire relay nodes N/K/O/S/T/U/L.

**★ Zombie GP-output assignment (hard-won 2026-09-14):**
- **GPOUT2 (J1 pin 4) = NEGATIVE CONTACTOR.** Herb originally put neg-contactor on **GPOUT1**, it never
  closed, moved it to GPOUT2 and it worked. So GPOUT1 is suspect (Herb debugging separately).
- **GPOUT1 = J1 pin 31** (the CAD mislabels pin 31 "Neg Contactor LS Switch"; the old doc line "GP Out 1 =
  J1 pin 31" was right about the pin). Flagged **DNC**, but used **provisionally** for the rad fan.
- **Rad fan** = relay M coil-low (ML350 P5:14) -> **GPOUT1 (pin 31)**. **Coolant pump** = relay R coil-low
  (P5:1) -> **GPOUT3 (J1 pin 3)**. Assign in Zombie **IOMatrix** (func 14 = CoolingFan; a coolant-pump func
  on GPOUT3). ⚠ If GPOUT1 proves dead, the fan moves to a **PWM output** (pins 7/6/5) - but the web UI may
  not expose PWM-as-fan, so that's a firmware edit. There is NO plain "GP Out 1" pin in the CAD besides 31.
- The CAD relays use Splice pins **30/85/86/87** (ISO), not the ML350 physical 1/2/3/5.

### Phase 4 status + RESUME NOTES (2026-09-15)

**DONE on the live canvas (NOT yet `save_plan`'d - verify Herb Ctrl+S'd):**
- Phase 4A retirement: removed contact/common conductors + deleted relay nodes **N/K/O/S/T/U/L** and
  orphan fuses **f52-56, f57, f62-63**; killed the iBooster f62-63->X_iBoost double-feed.
- Oil Pump: Switched B+ -> **f45** (comp_1774975815037_l7q81ke5b) -> OilPump (existing OUT).
- EPB: Switched B+ -> **f39** (NEW, comp_1789300000001_f39epb) -> PBCtrl.4 (pin-c6f4af4f).
  **AddRed node DELETED** - Herb has no AddRed add-a-fuse holder (also lacks **AddBrown** - use real slots).
  EPB "enable" = switched-busbar power itself (PBCtrl has NO separate enable pin; pin4 Sw12v = power).

**PENDING - do when the fork oracle is back (limit resets 12pm Edmonton) or Herb gives IDs:**
1. **F-Coil fix (design agreed):** contactor coil-hi (pin_mc_85) + protoboard B+ (pin_pb_bp) are on RAW
   unfused Perm B+. Add small **F-Coil ~5A** off Perm B+ (comp_1789100000001_permbp001 / pin_permb_p),
   move both onto it. Remove conductors **cond_1789101000004_pwa000004** (coil-hi) +
   **cond_1789101000008_pwa000008** (proto B+), re-wire via F-Coil. (F-Main stays 100A for the contact path only.)
2. **Group membership:** F24 (comp_1789100000005_maxi24epa), F29 (comp_1789100000006_maxi29ibo),
   f59 (comp_1789200000003_f59cool), f39 (comp_1789300000001_f39epb) were created OUTSIDE the ML350
   group -> add them (AddToDeviceGroupCommand, need group id). External (stay out): Perm B+, F-Main,
   contactor, protoboard, load stubs. **Fastest: Herb drags these 4 into the group in-browser.**
3. **Tail loads (fuse-direct off switched busbar, real slots only - NO AddRed/AddBrown):**
   Zombie logic -> J1 pin 50 (GP12v Input); Inverter -> comp_1774050003985_eq8v54gm6;
   Bat Boxes + Controls -> NO connector exists, create stubs; CDL (F23 comp_1776605083775_7kwzmgp3u)
   + Status (F21 comp_1780404612403_j6v4g7dby) -> swap feeds from X105/IGN+ to switched busbar.
4. **BOX-AWAKE -> CM3 wake:** protoboard BOX-AWAKE (pin_pb_awake) -> cross-page ferrule, net BOX_AWAKE ->
   DD_Sigs (comp_1778936362771_glngrghpf, free pins 3/12/13/14/15) on the CM3/dashboard page.
5. **Cleanup:** bare orphan connectors X46-X51 (relay-common leftovers); empty links from removed conductors.

**Switched B+ (Bat+ comp_1774975815037_4dyvjr01w) pin usage:** used = orig 2,3,4,12 + 5(contactor feed),
6(F24),7(F29),8(M.85),9(M.30),10(f45),13(f39). Free = 11,14,15 (only 3 left -> grow the bus or chain for the tail).
Project id = 17410eef-ffcd-4a2a-adb7-dab94271a8f4; FuseRelay page = page_1774975610452_xv22udce3.

**Update 2026-09-15 (resumed after session-limit gap):**
- **F-Coil fix DONE:** Perm B+ -> **F-Coil ~5A** (comp_1789400000001_fcoil001) -> contactor coil-hi + protoboard B+.
  Removed the old raw-B+ conductors. F-Main (100A) now carries the contact path only.
- **All prior rototill edits verified intact** (fork re-pull) - the user's rearrange was position-only, 146 components.
- **Group fix needs a heavier pull:** device-group membership is NOT in get_plan_summary. To add F24/F29/f59/f39
  to the ML350 group programmatically needs get_plan/get_project for the group id - OR the user drags them into
  the group box in-browser (fastest).
- **Inverter has NO fuse-direct target:** the page's "Inverter" connector (comp_1774050003985_eq8v54gm6) is the
  GS450H **signal** connector (MTH/DRN/CLK/resolver), no 12V power pin. Does the inverter even take box 12V? TBD.
  **Bat Boxes + Controls** also have no page connectors. All three need stubs or clarification.
- **Tail resume IDs:** Zombie logic -> J1 pin 50 GP12v Input = pin_1774035486594_d69p9liel. Feed-swap conductors:
  F23.IN<-X105.1 = cond_1788402000002_v2c; F21.In<-IGN+.10 = cond_1788403000004_u4c. BOX-AWAKE -> DD_Sigs
  (comp_1778936362771_glngrghpf) pin 12 = pin-eba139db (DD_Sigs page unknown -> cross-page ferrule both sides).
- Switched B+ free pins now: 11, 14, 15 (chain or grow the bus for the remaining tail feeds).

**Update 2026-09-15 #2 - tail nearly done:**
- **Group fix:** user dragged F24/F29/f59/f39 into the ML350 group in-browser. Done.
- **Zombie logic:** SwB+ -> new **f26** (comp_1789400000002_fzomb001) -> J1 pin50 GP12v. Done.
- **Bat Boxes:** SwB+ -> existing **sw12** (comp_1774975815037_d00gxn79t, IN pin_1774975815037_r4yi8n7zz) ->
  InDtsch12-M.12 (front battery box LV feed). Done.
- **CDL:** feed-swapped F23.IN from X105 to SwB+ (last free bus pin 15). Done. **Bat+ bus now FULL - chain remaining taps.**
- **Status (F21):** LEFT ignition-gated per Herb (not needed live in charge). No change.
- **DONE-list total:** power entry+F-Coil, both relays (M fan/R coolant), EPAS/iBooster MAXI, oil, EPB(f39),
  Zombie, Bat Boxes, CDL. Retirement of N/K/O/S/T/U/L complete.

**REMAINING (cross-page; blocked on page identity - summary has no page field):**
- **Inverter:** feed 12V to pins 10/11 = **pin_1774050040459_j08b5ljae ("BR2+")** + **pin_1774050040459_e4t2gojyg ("BR2")**.
  ⚠ CAD labels them BR2+/BR2 (brake-resistor), not BR+/BR2+ - CONFIRM these are the 12V power pins before wiring.
- **Controls accessory rail** (connectors, pins): SW12V to DD_Sigs pin1 `pin-d9a21d0f`, PRNDL(M5Dial
  comp_1776692290252_s8d78i2c8) pin1 `pin-690c003d`, CDLSw(comp_1776692123566_u1ekw8xva) pin2 `pin-749939cd`.
  Gnd to DD_Power(comp_1786277490575_rtbhwboph) pin2 `pin-958215d4`, DD_Sigs pin2 `pin-0b2324c6`, PRNDL pin2
  `pin-3523b320`, PBCtrl(comp_1776685436607_kvtr0m7ju) pin3 `pin-6d922ed5`.
- **DD permanent Bat+ (dashboard/CM3 main power):** DD_Power pin1 "Bat+ in" `pin-18b3bc51` <- **Perm B+** (keep-alive fuse), NOT switched.
- **BOX-AWAKE -> CM3 wake:** protoboard pin_pb_awake -> DD_Sigs pin12 `pin-eba139db` (cross-page ferrule, net BOX_AWAKE).
- **Gnd bus free pins:** 2 `pin_1774975815037_h05t96hj2`, 3 `pin_1774975815037_f94yczozi`, 4 `pin_1774975815037_vysg4wnwj`, 9 `pin-58986012`.
- **Cleanup:** orphan connectors X46-X51, empty links.
- Note: these Controls/DD/PRNDL connectors' PAGE is unknown from summary -> need get_plan/get_project to know if cross-page ferrules are required, or wire in-browser.

**Update 2026-09-16 - TAIL COMPLETE (functional rototill done):**
- Pages confirmed: **Zombie = page_1774035261476_uynpwwfao**, **Controls = page_1776685218842_k8pqaps5n**.
  (⚠ `get_plan` returns last-SAVED state, not live - unsaved edits invisible there; trust execute_command successes. **Herb: Ctrl+S to persist.**)
- **Inverter:** SwB+ -> f_inv (comp_1789400000003_finv0001) -> cross-page ferrule pair (net **INV_12V**,
  comp_..._ferain0 on FuseRelay / comp_..._ferbin0 on Zombie) -> Inverter pins 10 + 11 (BR2+/BR2 = the 12V feed per Herb's docs).
- **X124 park-detect FIXED:** SwB+ -> X124.pin1 (comp_1784639381642_umevbzntd; spans Zombie+FuseRelay, so it self-bridges)
  -> ShiftConn.B+ (pin8) -> [dry contact closes in Park] -> ShiftConn.P (pin3) -> HSDN (Inverter pin25). Used SwB+ (switched) - revisit if park-detect wants a different domain.
- **Controls accessory rail (cross-page to Controls page), all via ferrule pairs + shared nets:**
  - **SW12V_ACC:** SwB+ -> f_acc (Controls SW12V 10A) -> ferrule -> DD_Sigs.1, PRNDL.1, CDLSw.2.
  - **GND_ACC:** Gnd bus -> ferrule -> DD_Sigs.2, DD_Power.2, PRNDL.2, PBCtrl.3.
  - **PERM_BPLUS:** Perm B+ -> f_ddkeep (DD/CM3 keep-alive 15A) -> ferrule -> DD_Power.1 (dashboard/CM3 main power, permanent).
  - **BOX_AWAKE:** protoboard BOX-AWAKE -> ferrule -> DD_Sigs.12 (CM3 wake-GPIO).
- **Status (F21):** left ignition-gated (unchanged).
- **Group:** F24/F29/f59/f39/f26/f_inv added to ML350 device group dg_1788006772406_1x17l72f2 (Herb also added the first 4 in-browser; AddToDeviceGroup is idempotent).

**STILL OPEN (minor):**
- Cosmetic cleanup: orphan connectors X46-X51 (retired relay-common leftovers) + empty links from removed conductors.
- **SAVE (Ctrl+S)** then re-pull to verify the whole thing end-to-end.
- Inverter BR2+/BR2 label vs 12V-feed: Herb confirmed from external docs these are the power pins.

**Update 2026-09-18 - CANVAS HAS BUGS + CHEAP-FIX PLAN (thread got too expensive; continue FRESH):**
The blind programmatic rototill introduced real wiring bugs (Herb found them eyeballing the live canvas).
The DESIGN (sec 8 above) is correct; the Splice CANVAS execution needs cleanup. Known issues:
- **Backfeed:** f59(coolant).OUT appears tied to f45(oil).OUT - their outputs must NOT share a node.
- **f44 orphan IN:** lost its feed when relay S was retired; f44.OUT still -> X1.15. Fix = feed f44.IN from
  SwB+ if X1 is a live load, else delete f44. (f44 = comp_1774975815037_lscms2trw, IN pin_1774975815037_d2fadmv6o)
- **F24 anomaly:** Herb sees F24 bridging B+:15 -> B+:6 (EPAS maybe unfed); does NOT match my records
  (F24.IN<-B+:6 cond_1789101000010, F24.OUT->EPAS stub cond_1789101000018). Needs eyes-on reconcile.
- **Stale labels:** DONE f49->"Rad Fan", f45->"Oil Pump". Still likely stale: sw12 (now Bat Boxes), and
  relays M/R are labelled by socket not function (M=Rad Fan, R=Coolant). Check F23/F21 too.
- **Hand-built ferrules are messy** (X124/X104/X127 + my ferrule pairs). ★LESSON: cross-page wires drawn
  IN-BROWSER auto-insert the ferrule + the nice off-page "(Pg.N)" clickable label - cleaner than hand-placing.
  Prefer drawing cross-page bridges in-browser.

**CHEAP FIX RECIPE (do NOT repeat-pull - repeated get_plan pulls burned a 5hr limit in ~20min):**
1. Herb: **Ctrl+S** so a pull reflects the live canvas (get_plan returns last-SAVED state).
2. Fresh session: **ONE** fork pull of the canvas -> distilled DIFF vs sec 8 (every orphan / backfeed /
   mislabel / stray ferrule + its conductor/node ID). One pull, kept in the fork.
3. Fix all same-page (FuseRelay) issues in ONE batch from that diff.
4. Cross-page bridges (Inverter/Controls/CM3): draw in-browser (auto-ferrule) OR redo carefully - not many.
Bus is full (chain taps). Project 17410eef-ffcd-4a2a-adb7-dab94271a8f4, FuseRelay page page_1774975610452_xv22udce3.

**Update 2026-09-18 #2 - CHEAP FIX EXECUTED (recipe followed; ONE pull, fork-held).**
Ran the recipe exactly: single `get_plan_summary` in a fork, distilled diff, one surgical batch. Results:
- **The two 09-18 headline bugs were REFUTED in saved state** (were live-canvas visual overlaps, not real wiring):
  - **Backfeed f59/f45: NOT present.** f45 Oil.OUT->OilPump.5 and f59 coolant.OUT->P6:5,6 are separate nodes.
  - **F24 anomaly: REFUTED.** F24.IN<-SwB+.6 (cond_1789101000010), F24.OUT->EPAS P1:2 (cond_1789101000018); EPAS IS fed.
    The B+:15->B+:6 "bridge" was the neighboring B+.15->F23.IN reading as a self-bridge.
  - Orphan connectors X46-X51: already gone.
- **SAFE BATCH APPLIED (9 items, all PASS; live canvas, Herb to Ctrl+S):**
  - Deleted stale switched feed SwB+.1->DD_Power.1 `cond_1786277626734_nhpzqd6e4` (would kill CM3 in sleep;
    DD_Power.1 correctly fed by PERM_BPLUS `cond_1789101000048`). Frees SwB+ pin 1.
  - Deleted duplicate park-detect conductor `cond_1789559637000_7dcggz3a9` (dup of ShiftConn.8->X124.1).
  - Deleted **redundant M.85->R.85 coil-hi jumper** `cond_1789101000013_pwa000013` (both 85s already reach
    SwB+ via own bus pins R.85->B+.2 / M.85->B+.8; jumper was leftover daisy-chain). **Herb caught this.**
  - Deleted stray F21 ferrule `xf21fr` node `comp_1788410000001_xf21fr` + its conductor `cond_1788410100001_f21c`.
  - Fixed net: `cond_1789561497560_7frw9z6q9` NET_mu42pkuw -> NET_f21_status.
  - Renamed sw12->"Bat Boxes", M->"M (Rad Fan)", R->"R (Coolant)".
- **★New Splice command shapes learned (add to SPLICE_CAD_SKILL.md sec 4):**
  - **`RemoveNewConductorCommand {conductorId}`** = surgical single-conductor delete (does NOT touch link siblings,
    unlike RemoveLinkCommand which nukes all conductors on the link). Use this to delete one wire by its cond_ id.
  - **`UpdateNewConductorCommand {conductorId, updates:{netName:"..."}}`** = in-place conductor edit (netName confirmed).
- **STILL OPEN (need Herb's eye, cross-page):**
  1. **DD_Sigs.1 double-booked** - carries both NET_f21_status (F21 status) and SW12V_ACC (accessory 12V power);
     move accessory 12V to a free DD_Sigs pin (Herb picks pin + function).
  2. **Stale Trans Park-Pawl (HSDN) block** on J1.50 - superseded by live X124/ShiftConn.8->3/Inverter.25 path;
     delete old block (`cond_1787925199021_v1xgjm42e` J1.50->PawlOut, `cond_1787925199021_ufcdcvt74` sw12.1->Pawl.B,
     the Park-Pawl node, and duplicate sw12 `comp_1787925199021_1cmxqqice`). SAFETY-ADJACENT - confirm first.
  3. **f44 orphan** (`comp_1774975815037_lscms2trw`) - IN unfed, OUT->X1.15 = "Ignition T15 In" (an ignition INPUT,
     not a load); delete f44 + `cond_1788403000001_u1c` once confirmed nothing wants switched-12V out there.

**Update 2026-09-18 #3 - session 2 cleanup + wake/protoboard design SETTLED (done live; Herb Ctrl+S'd through most):**
- **#2 park-pawl + #4 f44 DONE:** deleted the stale Trans Park-Pawl (HSDN) block (`comp_1787925199021_njb2ic33t`),
  its duplicate sw12 node (`comp_1787925199021_1cmxqqice`), and conductors v1xgjm42e/ufcdcvt74 - this also cleared
  the J1.50 double-feed (f26->J1.50 now sole Zombie-logic feed). Deleted f44 (`comp_1774975815037_lscms2trw`) +
  its X1.15 conductor `cond_1788403000001_u1c`.
- **f49 Rad Fan IN was genuinely orphaned** (relay M pin 87 contact-out was never wired). FIXED: added conductor
  `cond_1789810000001_m87f49` (M.87 -> f49.IN, net RADFAN, link `link_1789810000001_m87f49`). Fan path now closed:
  SwB+.9 -> M.30 -> [contact] -> M.87 -> f49.IN -> f49 -> Rad Fan (H1:1). (R/coolant was already correct: R.87->f59.IN.)
- **F21 is NOT dead** - still feeds `EB2.+12v` (ignition status power) via `cond_1780418505177_nwziatcrj`; only its
  DD_Sigs branch was removed. Relabeled `comp_1780404612403_j6v4g7dby` -> **"F21 (EB2 +12v)"**.
- **DD_Sigs.1 double-book RESOLVED:** dropped F21-status leg `cond_1788410100002_ddc` + its dead F21_Out ferrule
  chain. DD_Sigs.1 now carries only `SW12V_ACC` = the CM3 Sw12v+ **wake pin**.
- **★WAKE ARCHITECTURE SETTLED:** CM3 wake pin = **DD_Sigs.1 (Sw12v+)**, fed by **SW12V_ACC** (10A fuse off
  **Switched B+** = POST-contactor 12V; same tap feeds PRNDL.1 + CDLSw.2). Sequence: IGN or Pin-B -> protoboard OR
  -> FET -> master contactor closes -> Switched B+ hot -> SW12V_ACC hot -> DD_Sigs.1 hot -> CM3 wakes. **The wake
  signal only says "box is hot" - it CANNOT distinguish charge vs ign.** CM3 discriminates via **CAN** (Zombie mode
  / charger frames), NOT a hardware pin - forced anyway because the **manufactured HAT DD_Sigs (DE15) has NO free
  pins** (live: 1 Sw12v+, 4 EPB_GRN, 5 EPB_RED, 6 DIMMER, 7 CDL, 8 TCASE_LO, 9 VSS_SIG, 10 VSS_12V, 11 VSS_GND,
  SH=GND; **NC/dead: 3,12,13,14,15** - from Herb's KiCad J_SIGS1 screenshot). **Intended CM3 behavior:** charge ->
  SoC progress bar ONLY; ign-on -> full active display, decided via CAN.
- **BOX_AWAKE net DELETED as vestigial (Herb's call):** removed conductors cond_1789101000044 (proto->ferrule),
  cond_1789732444207 (proto->X127), cond_1789732472619 (X127->ferrule), cond_1789101000049 (dead pin-12 leg);
  removed nodes X127 `comp_1789732291206_g726pysny` + BOX_AWAKE ferrules `comp_1789600000006_fawka00` /
  `comp_1789600000010_fawkb00`. **Protoboard `comp_1789100000004_proto0001` KEPT** (still drives contactor via
  coil/IGN/Pin-B/GND/F-Coil-B+). BOX_AWAKE was redundant: its only landing was DD_Sigs.12 (NC on mfg'd HAT), and
  the wake is already served by SW12V_ACC on pin 1.
- **★PROTOBOARD (Hammond box, next to ML350) - SIMPLE, final:** inputs = IGN+, charger Pin-B, Perm Bat+, GND.
  **2 signal diodes (IGN+ & Pin-B) => diode-OR** (diodes exist ONLY to stop IGN+ and Pin-B back-feeding each other)
  -> **FET gate** -> FET sinks AEV14012 **coil-low**; coil-high = Perm Bat+ via **F-Coil 5A**. Either source high ->
  contactor closes. Parts: 2 signal diodes + 1 FET + gate resistor + contactor coil. Diodes tiny (gate uA only; coil
  current from Perm Bat+ through the FET). NOT on the HAT (no respin).
- **STILL OPEN (session hit 97% usage):** (a) **X1.15 "Ignition T15 In"** - does the Zombie actually need ignition
  fed there? (wrong f44 feed deleted; may need a correct IGN+ -> X1.15 wire). (b) **Switched B+ cosmetic pin reorder**
  - Herb deferred (connectivity-safe, wires follow pin IDs). (c) hand-built cross-page direct wires (f26->J1.50,
  f39->PBCtrl.4, f45->OilPump.5, sw12->InDtsch12-M) are connected but render off-page - optional tidy to ferrule pairs.
- **★New Splice command shapes confirmed (now in SPLICE_CAD_SKILL.md):** `RemoveNewConductorCommand {conductorId}`
  (surgical single-wire delete), `UpdateNewConductorCommand {conductorId, updates:{netName}}`.

**PENDING (NOT DONE - hit session limit, resets 11am Edmonton 2026-09-18): split Switched B+ doubled pins.**
Canvas is UNCHANGED by this op - nothing half-applied. Goal: each SwB+ pin carries exactly ONE wire (Herb prefers
single-connection pins over multi-tap). SwB+ = `comp_1774975815037_4dyvjr01w`. Do it as same-page delete+recreate
(NO ferrule - dragging endpoints in-browser auto-ferrules = the mess Herb hit). Cheap: from a held snapshot, no need
for repeated pulls.
- **pin 10** = f45 Oil (KEEP) + f_acc Controls SW12V (MOVE, was cond_...039)
- **pin 11** = f26 Zombie (KEEP) + f_inv Inverter (MOVE, was cond_...034)
- **pin 14** = sw12 BatBoxes (KEEP) + X124 park-detect (MOVE; ⚠ X124 self-bridges Zombie+FuseRelay - handle carefully)
- Targets: **pin 1 is now FREE** (its DD_Power.1 feed was deleted this session) -> reuse it + add 2 new SwB+ pins
  (adding pins must include ALL existing pins if using array-replace, else conductors drop). Move the 3 second-legs
  onto pin 1 + 2 new pins, preserving each conductor's netName/color/gauge.
