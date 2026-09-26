# EVJ55 - ML350 Power Distribution (design)

The EVJ55-specific power-distribution design built on a reused Mercedes ML350 fuse/relay box.

**Companion files:**
- `ML350_box_reference.md` - generic box hardware (relay roster, part #s, coil taps, connector pinout). Sanitized/shareable.
- `box-conductors.md` - every conductor crossing the box boundary + the **MS3102A24-5S mil-round bulkhead pinout** (A-S).
- `ML350 fuse box - Pinout.csv` / `ml350_annotated.png` - raw box pin map.

This file = the EVJ55 **architecture, load map, and the Splice/Hammond bulkhead build.**

---

## 1. Architecture - external master contactor

Power gating = **ONE external Panasonic AEV14012 master contactor** on the B+ feed:
Battery -> **F-Main (100A MEGA, slow)** -> contactor -> **Switched B+ bus** (feeds busbar B + the 5
MAXI slots + the M/R relay contacts). The contactor coil is driven by a **protoboard** in the Hammond
enclosure next to the ML350: `OR(IGN, charge Pin-B)` via 2 signal diodes -> low-side FET sinks
coil-lo; coil-hi = permanent Bat+ via **F-Coil (~5A)**.

=> the **entire box is dead in sleep** (zero parasitic). Three states:

| State | Trigger | Box |
|-------|---------|-----|
| Drive | ignition | hot |
| Charge | charger Pin-B (key off) | hot (steering/brakes/EPB available) |
| Sleep | neither | dark |

**Only two relays remain: M (rad fan) + R (coolant).** Everything else is **fuse-direct** off the
switched busbar. No V master relay, no S/T/U gang, no internal wake relay - the external contactor
does all gating. **CM3** runs on **permanent-B+ standby** (keep-alive fuse `f_ddkeep` 15A), independent
of the contactor; it wakes on switched-12V.

## 2. Load & fuse map

**Heavy loads -> the 5 MAXI slots** (heavy spades on P1/P2/P3, ~10/12 AWG):

| Load | Fuse -> pin | Note |
|------|-------------|------|
| EPAS | F24 -> P1:2 | **10AWG, ~40A class** (Toyota sizing; ~60A is only a brief stall peak). **Dedicated ground return to the GND stud, NOT chassis-local** |
| iBooster | F29 40A -> P1:1 | ~40A class; **dedicated ground return too** (not chassis-local) |
| (spare) | F40 -> P3:1 (pop.); F30/F35 (unpop.) | |

**Relays (2):**

| Relay | Load | Contact out | Coil-lo | Coil-hi |
|-------|------|-------------|---------|---------|
| M | Rad Fan | f49 -> H1:1 | P5:14 <- Zombie CoolingFan | Bat+ common (switched B+) |
| R | Coolant pump (single VW) | f59 -> P6:5,6 | P5:1 <- Zombie CoolantPump | Bat+ common |

Both coils energize only when the box is hot (coil-hi = switched B+). Coil-lo taps are populated
P-pins = no coil rework. Rad-fan failsafe = a dumb overtemp switch in parallel on M's coil-lo (TBD).

**Fuse-direct minis** (switched busbar B):

| Load | Fuse -> pin |
|------|-------------|
| Oil Pump | f37 -> P3:7 (busbar; Splice labels it f45) |
| EPB power | f39 -> P3:4 (enable = BOX-AWAKE signal) |
| Zombie logic | f26 -> P2:7 |
| Inverter | Inv-12V -> P2:5 |
| Bat Boxes | sw12 -> P2:3 |
| Controls accessory | f_acc -> P2:6 |
| CDL | F23 -> P2:4 |
| Status | F21 -> P2:9 (ignition-gated) |

Unused ML350 sockets: K, N, O, S, T, U, V.

## 3. Zombie IOMatrix (control-signal pins)

CoolingFan = **PWM1 (X1.7)**, CoolantPump = **GP Out 3 (X1.3)**, BrakeLight = **PWM2 (X1.6)**,
NegContactor = GP Out 2 (X1.4), oil-pump PWM = pin 30 (dedicated). **GP Out 1 abandoned** (suspect
hardware - rad fan + brake both moved to PWM). SL1/SL2 = trans solenoids; PWM3 = spare.
(X1 = the real Zombie 56-way harness connector.)

## 4. Charger connector + wake

| Pin | Function |
|-----|----------|
| A / G | CAN H / L (Zombie <-> charger) |
| B | 12V+ when AC applied = the **charge-wake** source (**0.16A - a signal, not a power bus**) |
| C | 12V- (wake return) |
| E / F | HVIL interlock loop (series, not power) |
| T / S | DCDC logic power / enable (Zombie is DCDC master) |

The protoboard OR's IGN and Pin-B (2 signal diodes, mA) -> FET fires the master contactor -> Switched
B+ hot -> CM3 sees 12V and wakes. Pin-B only drives the FET gate (uA), so its 0.16A rating is a non-issue.

## 5. Hammond bulkhead / mil-round harness (Splice)

The box lives in a 12x12 cast-Al waterproof Hammond enclosure. Signals cross the wall via a
**MS3102A24-5S mil-round** (16 pins A-S; pinout in `box-conductors.md`), modeled in Splice as a mated
pair **MR1-F** (bulkhead/inside) <-> **MR1-M** (plug/outside). Perm B+/GND cross on **studs**; the
heavy loads (EPAS/iBooster/oil) cross via **panel-mount XT60E-1 connectors** (one per load, bolted to
the box wall, mate from outside - no gland). Each XT60 = the load's power + its **dedicated ground** -
fused in-box (F24/F29 + oil), grounds land on the GND stud. **EPAS/iBooster get dedicated ground
returns, not chassis-local** (precision actuators; Toyota ran EPAS 10AWG red+black). None use the sz16
mil-round. (Env: worst case is indirect car-wash spray, so seal the flange + cap unmated = plenty.)

**Done** (Splice page `page_1790200000001_hammond`): every box-crossing SIG load routes
`fuse -> P-pin -> MR1-F -> [mate] -> MR1-M -> external` (rad fan, coolant, bat boxes, EPB, Zombie
logic, CDL); both Zombie coil-controls route through MR1 (CoolingFan = pin D, CoolantPump = pin J);
power studs (Perm B+, GND) + local ChassisGnd for the loads; MR1-M external connections (rad fan,
coolant pump, charger Pin-B/C, BMS +12V); BMS front/rear CSC chains joined to the BMWi3BMS master CAN.
Load grounds are **local chassis** (not through the mil-round; chassis/body lines run by hand). Full
mil-round pin assignment + Splice node IDs live in `box-conductors.md` and the Splice canvas.

## 6. Hardware notes

- **F-Main = 100A automotive MEGA** (slow-blow, rides EPAS+iBooster inrush; step to ~120A if it ever
  nuisance-blows, still under the AEV14012's 120A carry).
- Two spare **Sensata W23-X1A1G-50 50A resettable breakers** - do NOT parallel them for the main (poor
  current-share); one-per-load if wanted.
- Contactor coil ~0.35A hold; only burns in drive/charge (open in sleep).

## 7. Open items

- **Inside-feed side** of MR1-F pins F (BMS 12V) and M (Charger Pin-C) - box fuse/protoboard -> MR1-F.
- **Heavy/MED bulkheads not yet modeled:** EPAS/iBooster on studs (or paralleled 13.2A connectors);
  Oil Pump on a DTP. Still run direct in Splice; P1 / P3:7 pins unwired.
- **Controls-accessory (P2:6) + Status (P2:9)** box-crossing bulkhead path = TBD.
- **Protoboard build** (Hammond): 2 signal diodes + OR + low-side FET + contactor drive; size the FET
  for the AEV14012 coil; verify contactor main-terminal polarity before mounting.
- **Box-hot sense line to CM3** (weld-closed / stuck-on alarm; CM3 reads state only, does not act).
- **Inverter (traction) enable:** hard-wire-gate to drive-only, or rely on Zombie charge/drive
  mutual-exclusion + HVIL?
- Confirm `4RA 007 793-02` (K/R/M/N) contact rating; per-controller key-off quiescent draw.
- Cosmetic (Splice): orphan empty links from CDL deletes; drag MR1-F off MR1-M; reconcile BMS CAN net labels.

---

*History: this file previously carried the full design evolution - the V-master-relay coil scheme,
hybrid load-assignment iterations, a wake-relay-in-socket-K/R, and the dated Splice-rototill
play-by-play. All superseded by the master-contactor architecture above; see git history for the
detailed record.*
