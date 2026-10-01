# Electrical Box - Conductor List

Every conductor crossing the boundary of the electrical box (ML350 fusebox + protoboard) in the
12x12 cast-aluminum waterproof Hammond enclosure. Bench reference - facts only.
Rationale, history, and superseded schemes live in the private `evj55_contexts/FUSEBOX_CONTEXT.md`.
Fuse/pin detail: `EVJ55_ML350_powerdist.md` + `ML350 fuse box - Pinout.csv`.

**Tiers:** FAT >25A -> M6/M8 stud (or HD30) / MED 5-25A -> Deutsch DTP (25A) / SIG <5A -> Deutsch DT (13A).
**MIL-5015 contact ratings:** sz16=13A, sz12=23A, sz8=46A, sz4=80A, sz0=150A. `~`=estimate, TBD=unknown.

---

## Conductors crossing the box

### Power / ground IN
| # | Conductor | Dir | Far end | ~A | Tier | Connector |
|--|--|--|--|--|--|--|
| 1 | Main +Bat feed | IN | battery / main disconnect | 100+ | FAT | stud M8 |
| 2 | Chassis Gnd | IN | chassis | heavy | FAT | stud/strap (case bond) |
| 3 | IGN+ | IN | key / ign relay | <1 | SIG | DT |
| 4 | Charger Pin-B (+wake) | IN | charger | 0.16 | SIG | DT |
| 5 | Charger Pin-C (-wake) | IN | charger | 0.16 | SIG | DT |

### Heavy loads OUT (peak, not continuous)
| # | Conductor | Dir | Far end | ~A | Tier | Connector |
|--|--|--|--|--|--|--|
| 6 | EPAS power | OUT | EPAS | ~40-80 pk | MED-peak | size-8 / Anderson / stud |
| 7 | iBooster power | OUT | iBooster | ~50-60 pk | MED-peak | size-8 / Anderson / stud |
| 8 | HAT +Bat (CM3 + MagneRide) | OUT | HAT (cabin) | ~20-25 | MED-hi | DTP or gland; permanent, firewall crossing |

### Cooling / pumps OUT
| # | Conductor | Dir | Far end | ~A | Tier | Connector |
|--|--|--|--|--|--|--|
| 9 | Trans oil pump | OUT | trans | ~10-20 | MED | DTP |
| 10 | Rad fan | OUT | fan | ~4-8 | MED | DT/DTP |
| 11 | Coolant pump (single VW) | OUT | pump | ~0.5 | SIG | DT |
| 14 | EPB power | OUT | park brake | TBD | MED | DTP/DT |

### Electronics feeds OUT
| # | Conductor | Dir | Far end | ~A | Tier | Connector |
|--|--|--|--|--|--|--|
| 15 | Zombie sw12 | OUT | Zombie VCU | TBD | SIG-MED | DT; live in drive AND charge |
| 16 | BMS 12V | OUT | BMS (pack) | ~0.15 | SIG | DT; rides sw12 rail |
| 17 | ign_sense -> HAT | OUT | HAT | uA | SIG | DT; = OR(IGN, Pin-B) |

### Control / signal (Zombie <-> box)
| # | Conductor | Dir | Far end | ~A | Tier | Connector |
|--|--|--|--|--|--|--|
| 19 | Zombie -> M coil (rad-fan ctrl) | IN | Zombie CoolingFan (PWM1/X1.7) | <1 | SIG | DT |
| 20 | Zombie -> R coil (coolant ctrl) | IN | Zombie CoolantPump (GP Out 3/X1.3) | <1 | SIG | DT |
| 22 | Zombie enable (gang S) | OUT | Zombie | <1 | SIG | DT |
| 23 | Inverter enable (gang T) | OUT | inverter | <1 | SIG | DT |
| 24 | Bat-boxes enable | OUT | bat boxes | <1 | SIG | DT; rides sw12 (drive OR charge) |

### Charge-port / interlock (routing TBD - may not cross this box)
| # | Conductor | Dir | Far end | ~A | Tier | Connector |
|--|--|--|--|--|--|--|
| 29 | Park-pawl feed (sw12 -> HSDN "B") | OUT | trans HSDN | tiny | SIG | DT; dry SPST, 12V present = in Park |
| 30 | AVC2 +12V | OUT | AVC2 | <0.02 | SIG | DT; if AVC2 used |
| 31 | AVC2 relay -> Zombie | - | Zombie/charger | <1 | SIG | DT; charge-enable / motor-inhibit |

### Accessory (above-factory only; all '76 FJ-55 factory loads stay on the OEM fusebox)
| # | Conductor | Dir | Far end | ~A | Tier | Connector |
|--|--|--|--|--|--|--|
| 25 | Webasto 12V | OUT | Webasto | ~10 | MED | DT; FUTURE, V socket, CM3-driven coil |

List closed 2026-08-28. (CAN bypasses this box.)

---

## Relay + fuse-direct map (box internals)

**Relays (2):** everything else is fuse-direct off Switched B+ (external master contactor gates the box).
| Relay | Load | Fuse | Out pins | Coil driven by |
|--|--|--|--|--|
| M | Rad fan | f49 | P4:13,14 | Zombie CoolingFan = PWM1 (X1.7) |
| R | Coolant | f59 | P6:5,6 | Zombie CoolantPump = GP Out 3 (X1.3) |

**Fuse-direct (no relay):** EPAS=F24->P1:2, iBooster=F29->P1:1, oil pump=F40->P3:1, EPB=f39->P3:4,
Zombie logic=f26->X1.50/P2:7, Bat Boxes=sw12->P2:3, CDL=f34->P2:4, Inverter=f27->P2:5 (5A),
Tcase-Status=f25->P2:9 (IGN-fed), ~~Controls-acc=f33->P2:6~~ (moved to OEM fuse behind firewall - P2:6/f33 now
FREE), BMS 12V=f31->P2:10 (5A; **may change - BMS-inside proposal, see below**).
Slot<->P-pin map = factory-fixed per the CSV.
**F20-F23 = empty** (contacts robbed for relay V; CDL/Status relocated F23/F21 -> f34/f25). **P1:3-10 are DEAD**
(f20-f23 slots robbed = no contacts) - future spare fuses must come from P2/P3/P4/P6 slots, not P1.

**Tcase-Status (P2:9, f25)** = ignition-switched 12V to the dash **"EB2" status connector**. All its signals
(**4WD light, reverse light, VSS**) originate at the **transfer case** - hence the name. Box-fed, ign-gated;
cabin crossing route still TBD.

**Controls-acc (P2:6)** = switched 12V for the EV control gear (dashboard DD-*, M5Dial/PRNDL, EPB, CDL switch).
**RESOLVED 2026-10-01: fed from an existing OEM fuse behind the firewall (low current), NOT via this box**
-> **P2:6 / f33 now FREE.** (Use an ignition/accessory-switched OEM fuse so the controls sleep.) NB this is
distinct from CDL, whose external split rides the OEM harness too (Herb: "all the CDL stuff has its own OEM harness").

**PROPOSED (pending BMS packaging + open CAN1 harness) - BMS inside the box:** mount the BMS ESP32 in the
Hammond box, power it internally off f31 (sw12), and re-task **MR1 F -> CANH, K -> CANL** so the pack CAN exits
via MR1 instead of BMS 12V. Removes the f31->P2:10->MR1-F.F feed; routes BMS CAN THROUGH the box (reverses
"CAN bypasses box" for this leg). **Topology (Herb's plan):** F carries **2x CANH**, K carries **2x CANL**
(bus passes through = in + out), with a **~6in spur** to the BMS hardware; **disable the BMS onboard
termination** (it sits mid-bus, not an end). Verify thermal fit in the sealed box + reconcile where the
120R termination actually lives (one is at the truck's rear; exact BMS-end TBD). Drops spares to G, M. NOT DONE.

---

## Signal bulkhead - MS3102A24-5S mil-round (MR1) pinout

Insert 24-5, 16x sz16, pins A B C D E F G H J K L M N P R S. Physical rows from keyway down:
(A B)(C)(D E)(F G H)(J K)(L M N)(P R)(S); higher-current (*) on outer positions. **SOURCE OF TRUTH for MR1.**

| Pin | Signal | ~A | Box-side source |
|--|--|--|--|
| A | Rad fan power * | ~4-8 | P4:13,14 paralleled in-connector -> one wire to strip |
| B | IGN+ | <1 | protoboard |
| C | Charger Pin-B (wake) | 0.16 | protoboard OR-wake (12V when AC present) |
| D | Zombie -> M coil (fan ctrl) | <1 | M.86 coil, x-page (phys P5:14) |
| E | Coolant pump (single VW) | ~0.5 | P6:5 |
| F | BMS 12V | 0.15 | f31 -> P2:10 (Switched B+ / sw12; alive drive+charge) |
| G | SPARE | - | - |
| H | EPB power * | brief pk | P3:4 |
| J | Zombie -> R coil (coolant ctrl) | <1 | R.86 coil, x-page (phys P5:1) |
| K | SPARE | - | - |
| L | Bat boxes feed * | med | P2:3 |
| M | SPARE | - | (was Charger Pin-C; moved to N to avoid a center-of-connector solder joint) |
| N | Charger Pin-C (wake rtn) | 0.16 | Hammond ground stud (return ref for Pin-B) |
| P | ign_sense / Sw12v+ wake -> HAT | uA | protoboard |
| R | CDL | small | P2:4 |
| S | Zombie logic 12V * | ~1-3 | P2:7 |

**3 spare pins = G, K, M** (expansion bounded to +3 circuits). Leave P2:5/P2:6/P2:9 earmarked.
G and M are the two center-of-connector pins (hardest to solder) - keep them spare where possible.
**Charger B/C** ride MR1 (C=Pin-B, N=Pin-C) and break out on the MR1-M vehicle side to a **DT-2 pigtail**
(no extra box perforation). Pin-B -> protoboard OR-wake; Pin-C -> Hammond ground stud.

**VCU control (D, J, S)** break out on the MR1-M vehicle side to a **3-pin DT**, pins alphabetical:
DT-1 = D (Zombie CoolingFan ctrl, M coil-low), DT-2 = J (Zombie CoolantPump ctrl, R coil-low),
DT-3 = S (Zombie logic 12V) -> Zombie VCU (X1). These are the ONLY MR1-M pins that reach the VCU.

---

## On-hand connectors + role

| Connector | Type | Contacts | A/contact | Role |
|--|--|--|--|--|
| 3x Amphenol/DDK MS3102A24-5S | MIL-5015 threaded, box recept. | 16x sz16 socket, pigtailed | 13A | primary sealed SIGNAL bulkhead (MR1); 2 spare pairs |
| TE CPC 206150-1 + bulkheads | Circular plastic, IP65, threaded | 37 pos, sz16 | 13A | big internal harness / 2nd bulkhead (need male crimp pins) |
| Bernier CMA 1N14 / 5N14 | Push-pull circular, harsh-env | 14 pos | ~few A | quick-disconnect SIGNAL group (cabin/service) |
| Studs (main +Bat/GND) or 1x Anderson SB | sealed stud feed-throughs / SB 2-pole | 2 | total box draw | FAT: main +Bat + main GND (SB = optional main disconnect) |

**Rules:** >13A stays off sz16 (studs); rad fan/EPB fine on sz16. Waterproof walls -> sealed bulkheads
(MS3102 metal+gasket best) or sealed glands; studs need sealed feed-throughs. Case = ground plane.
