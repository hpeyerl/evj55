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
  existing charge-wake OR, sec 5b). The **same OR node = CM3 wake-GPIO**.
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
- **Rad fan = relay O** (coil-lo <- Zombie CoolingFan or an overtemp switch).
- **Coolant pumps = relay too** (DECIDED 2026-09-12): a freed socket, **coil low-sided by Zombie**
  (CoolantPump output), pump power **fuse-direct off switched B+**. Relayed (not Zombie-direct)
  because the new **higher-flow VW pump** draws more running + motor inrush - the relay contacts
  absorb that instead of the Zombie GP-out FET, and the small ML350 relays have an integral coil
  snubber so the FET sees only the coil. **Socket = a 20A small (S/T/U/L)** (Herb's call 2026-09-12 -
  no exact pump number, but a 20A relay covers the VW pump comfortably). Runs in drive AND charge
  (switched B+ hot + Zombie awake in both).
- Everything else = fuse-direct.

**Failure modes:**
- Master **fails open** mid-drive: box goes dark. EPAS drops (accepted - assist only matters at
  parking speed) and brakes degrade to manual pedal. Single point, but bounded consequence.
- Master **welds closed**: box never sleeps -> battery drain over days. **Add a box-hot sense
  line to CM3** to alarm (CM3 reads it as state; it does not act on power).

**Relays in use: O (rad fan) + one coolant relay** (socket TBD by VW-pump current). **Freed:** the
rest of K/N/M/L/R/V - muscle now fuse-direct, R was the old internal wake relay, V dropped, P dead.
The ML350 is now mostly a fused distribution block + two relays (fan, coolant), with the external
master contactor doing all power-state gating.

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
- [ ] **F-Main final size:** needs EPAS worst-case current -> pick the ~100A MEGA/ANL slow-blow value
  and the feed cable gauge (4-6 AWG); keep <= 120A.
- [ ] **Master-contactor drive:** size the low-side FET for AEV14012 coil pull-in + ~0.35A hold; pick the
  two signal diodes for the (IGN OR Pin-B) trigger; confirm coil-hi tap is on **permanent** Bat+
  (pre-contactor). Verify AEV14012 main-terminal polarity/orientation for mounting.
- [ ] **Box-hot sense line to CM3** (weld-closed / stuck-on detection). CM3 reads it as state only.
- [DECIDED 2026-09-12] EPB enable = **BOX-AWAKE (IGN OR Pin-B)** - toggleable while charging, dead in
  sleep. CM3 is a state consumer, not the EPB driver.
- [ ] **Inverter (traction) enable:** hard-gate to drive-only in wiring (charge interlock), or leave it
  to Zombie's charge/drive mutual-exclusion + HVIL? If wiring-gated, it's the one enable that keeps a
  drive-only path.
- [ ] **Freed relays K/N/M/L/R/V:** decide leave-seated-unused vs. pull vs. repurpose. Only O stays in use.
