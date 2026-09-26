# Electrical Box - Conductor List

Every conductor crossing the boundary of the electrical box (which contains the ML350 fusebox
+ the wake diodes). Drives the connector plan. Started 2026-08-28, grows as gaps fill.

**Tiers:** FAT >25A -> M6/M8 feed-through stud (or HD30)  /  MED 5-25A -> Deutsch **DTP (25A)**  / 
SIG <5A -> Deutsch **DT (13A)**. `~` = estimate, **TBD** = unknown.

## ★2026-09-21 RECONCILE - master-contactor pivot (supersedes the V/relay-master + wake-relay scheme below)
The relay/coil/wake sections written 2026-08-28..09-02 are SUPERSEDED. Current design (from the Splice
rototill; authoritative detail in `EVJ55_ML350_powerdist.md` sec 0/8/9). **Read this banner as truth; the older
tables (V ign-master, N/K/O relays, wake=R) are HISTORICAL.**
- **Power gating = ONE external Panasonic AEV14012 master contactor** on the B+ bolt: Perm B+ -> F-Main
  (100A) -> contactor -> **Switched B+** bus. Coil driven by the **protoboard** (in the Hammond box next to
  the ML350): OR(IGN, charge Pin-B) via 2 signal diodes -> FET sinks coil-low; coil-hi = Perm B+ via
  **F-Coil 5A**. **NO V ign-master, NO internal wake relay.** Whole box is dead in sleep.
- **Only TWO relays remain: M (rad fan) + R (coolant).** Everything else = **fuse-direct off Switched B+**:
  EPAS=F24 MAXI 60A->P1:2; iBooster=F29 MAXI 40A->P1:1; oil pump=f37->P3:7; EPB=f39->P3:4; Zombie logic=
  f26->X1.50; Bat Boxes=sw12; CDL=F23; Inverter=Inv-12V fuse; Status=F21->EB2 (IGN-fed).
  - **M (rad fan):** contact SwB+ -> f49 -> H1:1; coil-low -> Zombie CoolingFan = **PWM1 (X1.7)**.
  - **R (coolant):** contact SwB+ -> f59 -> P6:5,6; coil-low -> Zombie CoolantPump = **GP Out 3 (X1.3)**.
- **Zombie IOMatrix (this session):** CoolingFan=**PWM1 (X1.7)**, BrakeLight=**PWM2 (X1.6)**, CoolantPump=
  **GP Out 3 (X1.3)**, NegContactor=GP Out 2 (X1.4), oil-pump PWM on **pin 30** (GS450HOIL). **GP Out 1
  ABANDONED (suspect HW).** SL1/SL2=trans solenoids, **PWM3=free spare**.
- **Rad-fan failsafe:** a dumb overtemp switch in parallel with M coil-low (additive, TBD).
- **X1 = the real Zombie 56-way F harness block** (the phantom J1 header + its mate/group were deleted).
- Bulkhead/mil-round connector inventory (MS3102A24-5S etc.) below is CURRENT; only the relay-coil/wake
  wiring is superseded.

## Running tally - CLOSED (2026-08-28), ~24 conductors + case-ground
- **FAT (true continuous): main +Bat (+ dedicated main GND)** - stud-pair OR one Anderson SB (2-pole =
  battery +/- disconnect, sized to total box draw). **RETIERED 2026-08-30:** EPAS / iBooster / trans-oil-pump
  moved OUT of FAT -> their big numbers are BRIEF PEAKS, not continuous (see MED-peak). Historically chassis
  Gnd = case bond, but a dedicated main GND return is preferred at high current.
- **MED (DTP / Cannon sz12-16): 4** - HAT +Bat (~20-25A), rad fan, EPB, Webasto (future)
- **MED-peak (high BRIEF peak, low continuous; size for fuse + voltage-drop-at-peak, NOT continuous heat):
  EPAS, iBooster, trans oil pump** - EPAS peak donor-dependent (~40-60A+ at stall, ~5-15A cruising), iBooster
  only during braking (fused ~50-60A, ~0 otherwise), oil pump likely ~10-20A. -> size-8 / Anderson PP45-75
  (or stud) once MEASURED at reassembly; likely NOT size-4 / 2AWG.
- **SIG (DT / Cannon sz16-20): ~16** - IGN+, Pin-B/C, Zombie sw12, BMS, ign_sense, M5Dial, 3x Zombie coil-lo controls, 2x enables (S=Zombie, T=inverter; bat-boxes moved to sw12, U freed), 3x pumps (coolantx2 + trans booster)
- Accessory feeds **closed** - only future Webasto.

---

## Power feeds IN

| # | Conductor | Dir | Far end | ~A | Tier | Connector | Notes |
|--|-----------|-----|---------|----|------|-----------|-------|
| 1 | Main +Bat feed | IN | battery / main disconnect | 100+ | **FAT** | stud M8 | feeds the whole box busbar; size to Sum  loads |
| 2 | Chassis Gnd | IN | chassis | heavy | **FAT** | stud/strap | box ground reference |
| 3 | IGN+ (ignition) | IN | key / ign relay | <1 | SIG | DT | feeds wake diodes + ignition-gate group |
| 4 | Charger Pin-B (+wake) | IN | charger | 0.16 | SIG | DT | 12V when AC present |
| 5 | Charger Pin-C (-wake) | IN | charger | 0.16 | SIG | DT | return for pin-B |

## Heavy loads OUT

| # | Conductor | Dir | Far end | ~A | Tier | Connector | Notes |
|--|-----------|-----|---------|----|------|-----------|-------|
| 6 | EPAS power | OUT | EPAS unit | ~40-80 **pk** | **MED-peak** | size-8 / Anderson / stud | relay N (5-gang); **PEAK not continuous** (~5-15A cruising); size for V-drop at peak; (!) MEASURE at reassembly |
| 7 | iBooster power | OUT | iBooster | ~50-60 **pk** | **MED-peak** | size-8 / Anderson / stud | relay K or R; only during braking, ~0 otherwise; fused ~50-60A; (!) MEASURE |
| 8 | HAT +Bat (CM3 + MagneRide) | OUT | HAT (cabin) | ~20-25 | **MED-hi** | DTP or gland | **permanent**; firewall crossing; MR ~15-20A of it |

## Cooling / pumps OUT

| # | Conductor | Dir | Far end | ~A | Tier | Connector | Notes |
|--|-----------|-----|---------|----|------|-----------|-------|
| 9 | Trans oil pump | OUT | trans | ~10-20 | **MED** | DTP / connector | relay M; likely <=20A (may fit paralleled sz16 or a sz12); (!) MEASURE - was assumed >20A |
| 10 | Rad fan | OUT | fan | 4.25 | MED | DT/DTP | relay O; Zombie-controlled |
| 11 | Coolant pump 1 | OUT | pump | **0.48 meas** | SIG | DT | Denso 064100-1110, teeny. **Measured ~480mA moving water** (clamp on 2A DC range - verify in series, clamps are weak <1A). Driven by Zombie low-side, NOT relay P (P is dead). (!) low draw -> flow may be marginal, MEASURE L/min |
| 12 | Coolant pump 2 | OUT | pump | ~0.48 | SIG | DT | 2nd Denso (assume ~same); TWO used because one may not flow enough - the 480mA draw supports that worry, so **verify FLOW (L/min), not current** |
| 13 | Trans booster pump | OUT | pump (far) | ~0.5? | SIG | DT | new; boosts trans leg; not yet measured (assume ~0.5A like the Densos) |
| 14 | EPB power | OUT | park brake | **TBD** | MED | DTP/DT | relay L; brief actuation peak |

## Electronics feeds OUT (wake-switched / permanent B+)

| # | Conductor | Dir | Far end | ~A | Tier | Connector | Notes |
|--|-----------|-----|---------|----|------|-----------|-------|
| 15 | Zombie **sw12** | OUT | Zombie VCU | TBD | SIG-MED | DT | **Zombie can't sleep -> needs sw12 live in drive AND charge**; power path decided by (Zombie+BMS draw) vs Pin-B 0.16A - see open Q4 |
| 16 | BMS 12V | OUT | BMS (pack) | ~0.15 | SIG | DT | ESP32 T-CAN485; rides the sw12 wake rail |
| 17 | ign_sense -> HAT | OUT | HAT | uA | SIG | DT | = OR(IGN, Pin-B) via the 2 inline diodes; wake/sleep |
| 18 | M5Dial 12V | OUT | M5Dial (cabin) | small | SIG | DT | shifter feed |

## Control / signal (Zombie <-> box)

| # | Conductor | Dir | Far end | ~A | Tier | Connector | Notes |
|--|-----------|-----|---------|----|------|-----------|-------|
| 19 | Zombie -> rad-fan coil-low | IN | Zombie | <1 | SIG | DT | = Zombie **CoolingFan** (thermostatic, CHARGE+RUN) -> assign to **SL1/SL2 or Out1/Out3**; **O coil-high MUST be live in charge (fix f52/N gating)** |
| 20 | Zombie -> coolant pumps | IN | Zombie | ~1.5 total | SIG | DT | Densos **measured ~480mA each** (verify in series); 2 coolant + trans booster ganged on one Zombie CoolantPump low-side = **~1.5A total** - (!) confirm the Zombie SL/Out output sinks 1.5A, else buffer with a small relay/FET. NO relay (P DEAD). |
| 21 | Zombie -> trans-pump coil-low | IN | Zombie | <1 | SIG | DT | **gang with #20 CoolantPump** (same cooling demand) -> NO extra Zombie pin |
| 22 | Zombie enable (gang S) | OUT | Zombie | <1 | SIG | DT | ignition-enable gang; (!) may merge with #15 |
| 23 | Inverter enable (gang T) | OUT | inverter | <1 | SIG | DT | gang |
| 24 | Bat-boxes enable | OUT | bat boxes | <1 | SIG | DT | **rides sw12 (drive OR charge) like #15/#16 - must be alive in charge too (BMS/contactor control); NOT the ignition gang. No relay: fused tap off the sw12 rail = R(Wake) output f59-61. Relay U FREED to spare. So it needs NO AddBrown holder. (2026-09-01)** |

**(Oil-pump PWM `GS450pumpPwm` = Zombie->controller direct, NOT through this box - on Splice already.)**

### Zombie IOMatrix pin budget  [SUPERSEDED 2026-09-21 - see top banner]
Current: **PWM1 = CoolingFan**, **PWM2 = BrakeLight**, **GP Out 3 = CoolantPump**, **GP Out 2 = NegContactor**,
oil-pump PWM on **pin 30**, **SL1/SL2 = trans solenoids**, **PWM3 = free spare**. **GP Out 1 ABANDONED**
(suspect HW - both rad-fan + brake moved to PWM). Park-pawl interlock = a Zombie **INPUT** (separate budget).
~~Old: SL1=CoolingFan, SL2=CoolantPump, Out1=BrakeLight, Out3=free, PWM1-3=free.~~

## Charge-port / interlock (routing TBD - may or may not cross THIS box)

| # | Conductor | Dir | Far end | ~A | Tier | Connector | Notes |
|--|-----------|-----|---------|----|------|-----------|-------|
| 29 | Park-pawl feed (sw12 -> HSDN "B" pin) | OUT | trans HSDN conn | tiny | SIG | DT | pawl = **DRY SPST lever switch**: passes B-pin->output pin when in Park (transmission does NOT source 12V - we feed it). Box feeds **sw12 to B**; **output pin -> Zombie GP12v Input (pin 50)** -> 12V present = in Park -> inhibit torque. (!)fail-safe: broken wire reads "not Park"->torque allowed; consider inverting (gnd on B + pullup, or gate torque-enable). Output->Zombie may not route thru box |
| 30 | AVC2 +12V | OUT | AVC2 module | <0.02 | SIG | DT | if AVC2 used (J1772 handshake); tiny; likely lives at charge port - may not cross box |
| 31 | AVC2 relay -> Zombie | - | Zombie/charger | <1 | SIG | DT | SPDT charge-enable / motor-inhibit; routing TBD |

**Splice to-dos (not this box):** BrakeLight (Zombie->brake lights); park-pawl interlock sense (HSDN->Zombie
input) + torque inhibit; AVC2 wiring (inlet CP/PP/GND + relay). J1772 handshake = **AVC2 (public) vs
Zombie CpSpoof (home/known EVSE) vs resistor spoof (crude)** - pick one; AVC2 offloads Zombie.

## Accessory feeds (above-factory only)

**SCOPE:** vehicle = **1976 FJ-55 Land Cruiser**. This box handles **only stuff ABOVE the factory
harness** (EV conversion + new tech). All the usual '76 accoutrements - headlights, tail/brake,
wipers, horn, blower, dome, etc. - are on the **factory harness/fusebox** (fed from the 12V battery
in parallel), NOT through this box. So the accessory list here is short - only genuinely-new feeds:

| # | Conductor | Dir | Far end | ~A | Tier | Connector | Notes |
|--|-----------|-----|---------|----|------|-----------|-------|
| 25 | Webasto 12V | OUT | Webasto | ~10 (20A relay) | MED | DT | **FUTURE**; populate empty **V socket**; **coil-lo = CM3-driven** (remote MQTT pre-heat) = the one CM3 relay |

**Ruled OUT of this box (2026-08-28):** air-ride compressor (none yet - Schrader valves), Sim7060
modem (off the HAT), aux lighting (none), lockers (none), **winch (its own 3/0 lug off 12V Aux)**.
=> accessory list is **closed** - Webasto is the only above-factory add, and it's future.

---

## Open questions (fill these and the count firms up)

1. **Accessory feeds** - what else leaves the box always-hot/fused? (lights, USB, aux, horn, etc.)
2. **EPAS + iBooster** actual continuous/peak amps -> stud vs HD30 connector.
3. **Trans oil pump / EPB / coolant pumps** amps -> DT vs DTP.
4. **Zombie power path** - RESOLVED (2026-08-28): Zombie can't sleep, gets **sw12**, needs 12V live in drive AND charge. Truck is dismantled -> can't measure draw -> **ASSUME >0.16A** -> **wake-switch REQUIRED** (pin-B can't power the rail, only triggers). Wake-switch = small high-side switch, Bat+->sw12 (~2A), fired by OR(IGN, pin-B). **HOME DECIDED (2026-08-28): the spare K/R ML350 socket** (the one iBooster doesn't take) - coil-hi = Bat+, contacts = Bat+->sw12; coil-lo sunk by a **small N-FET** (gate = OR(IGN,pin-B) via 2 signal diodes) on **a small board inside the box** (accepted worst-case; NO inline-in-harness). => both K and R now used (iBooster + wake); V stays the empty spare. (No cat-in-a-python inline blobs - Herb.)
5. **CAN** - CONFIRMED **bypasses this box** (Herb 2026-08-28); not listed. (ok)
6. **Grounds** - assumed loads ground to chassis locally (not back through box); confirm.
7. **Cannon "millrounds"** - **RESOLVED 2026-08-30:** inventoried what Herb actually has and mapped
   the conductor tiers onto them - see **On-hand connectors + role map** below. MIL-rounds DO replace
   the Deutsch bulkheads. (Original note: DT pins won't retain in MIL inserts - use native contacts;
   MIL A/contact = sz16 ~13A, 12 ~23A, 8 ~46A, 4 ~80A, 0 ~150A.)

## Enclosure
**12x12 cast-aluminum WATERPROOF Hammond box** houses: ML350 fusebox + 1-2 busbars + the wake-switch board + supporting bits (Herb 2026-08-28).
- Plenty of wall real estate (4x 12" walls) for bulkhead connectors + studs -> the ~25-40 conductor plan is physically fine.
- **Waterproof -> all penetrations must stay sealed:** sealed bulkhead connectors (Deutsch DT / Cannon MIL are sealed) or sealed glands; studs need sealed feed-throughs. Reinforces connectors over open terminals.
- **Cast-Al case = ground plane** -> chassis-ground stud to the case (covers conductor #2); box bonds to chassis.
- Room for the wake-switch small board (the "worst-case protoboard") is a non-issue here.

---

## On-hand connectors + role map (inventoried 2026-08-30)

Connectors Herb has in hand and where each lands. Tiers: **FAT** (studs / size-4), **MED** (>13A),
**SIG** (<5A). MIL-5015 contact ratings: sz16=13A, sz12=23A, sz8=46A, sz4=80A, sz0=150A.

| Connector (on hand) | Type / coupling | Contacts | A/contact | Mate status | Role |
|---|---|---|---|---|---|
| **3x Amphenol/DDK MS3102A24-5S** | MIL-5015, **threaded**, box-mount recept. | 16x size-16 socket, **populated w/ pigtails** | 13A | **complete pairs** (bulkhead + plug) | **primary sealed SIGNAL bulkhead** - the 16 SIG (16<->16 exact); 2 spare pairs |
| **TE CPC 206150-1 + bulkheads** | Circular plastic (CPC Sy1), threaded, **IP65** | 37 pos, size-16 | 13A | have plug + bulkhead housings; **need male crimp pins (buy)** | big **internal harness / 2nd bulkhead** where IP65 is enough; 37-way = all SIG+MED+spares |
| **Bernier CMA 1N14 / 5N14** | **Push-pull** circular, harsh-env | 14 pos, signal | ~few A (confirm) | **both halves** (1N14 recept + 5N14 plug) | **quick-disconnect SIGNAL** group (cabin / M5Dial / service) |
| **ITT Cannon CA3102E32-17P-B-F80** | MIL-5015 **CA-Bayonet (reverse-bayonet)**, box recept. | 4x size-4 (**4 AWG**), **PIN** | 80A | mate CA3106E32-17S-B on DigiKey = **$359 CAD, MOQ 100** (new-prod) -> **not economical for 1** | **SHELVED 2026-08-30.** Would've been the FAT bulkhead, but the mate isn't buyable as a single. Single mate, if ever wanted, = military **surplus/eBay** (cheap NOS singles), not DigiKey |
| **2-cond 32-5P plug (MS5049/41-20A shell)** | MIL-5015-family plug, 2x ~size-0 | 2x ~150A | orphan **plug**, no receptacle | **SHELVED** - redundant with the 4-way; only if a split heavy main-power inlet is later wanted |
| **Studs (main +Bat/GND) or 1x Anderson SB** | sealed stud feed-throughs / SB 2-pole | 2 (main +/-) | total box draw | n/a / SB single-unit | **true FAT only (RETIERED 2026-08-30):** main +Bat + main GND. EPAS/iBooster/oil-pump demoted to MED-peak (peak not continuous) -> their own MED connectors/studs, sized after measurement. SB = optional single-action main disconnect |

**Rules carried out of this:**
- **>13A stays off size-16:** HAT +Bat (~20-25A) + all FAT can't ride the MS3102 / CPC size-16 contacts
  -> **studs or the CA-B**. Small MED (rad fan ~8A, EPB brief) are fine on size-16.
- **Pin-doubling for current:** paralleling 2x size-16 ~= **~20A** (derate ~20% - contacts don't share
  50/50, plus a fan-out junction + bundle heat), **NOT a clean 26A**. Fine for something solidly <=20A;
  do NOT use it to promote HAT +Bat (25A, unmeasured) off the studs. FAT via paralleling = impractical.
- **Sealing fit:** MS3102 (metal + gasket) and CA-B = best for the waterproof-box walls; CPC = IP65
  (jets, not immersion); Bernier push-pull = sealed harsh-env (confirm IP rating).
- **Parts to buy:** CPC size-16 male crimp pins (only if CPC used). ~~CA3106E32-17S-B mate~~ **DROPPED** -
  DigiKey wants $359 CAD / MOQ 100, so **FAT stays on studs** (CA-B receptacle shelved; single mate only
  via surplus/eBay if ever revisited).

---

## Box external interface / connector map (consolidated - for the IP67-lid label)

Single at-a-glance view of everything crossing the box boundary. Detail lives in the
conductor list above, `EVJ55_ML350_powerdist.md`, and `ML350 fuse box - Pinout.csv`; this ties the
connector-facing side together. (Also mirrored into the Splice fuse descriptions.)

### Power / ground
- **Main Bat+ IN -> M8 busbar stud** (feeds constant Bat+ busbar, all relay coil-highs + contacts).
- **Chassis/case ground** (bond); a Gnd point for V coil-low, V contact, and the wake FET source.

### Relay outputs -> loads + how each coil is driven  [REPLACED 2026-09-21 - see top banner]
Only TWO relays now; everything else fuse-direct off Switched B+ (master contactor gates the box).
| Relay | Load | Fuse | Out pins | Coil driven by |
|---|---|---|---|---|
| **M** | Rad fan | f49 | H1:1 | Zombie **CoolingFan = PWM1 (X1.7)** (+ dumb overtemp switch parallel, TBD) |
| **R** | Coolant | f59 | P6:5,6 | Zombie **CoolantPump = GP Out 3 (X1.3)** |

Fuse-direct (no relay): EPAS=F24->P1:2, iBooster=F29->P1:1, oil pump=f37->P3:7, EPB=f39->P3:4,
Zombie logic=f26->X1.50, Bat Boxes=sw12, CDL=F23, Inverter=Inv-12V fuse, Status=F21->EB2.
~~Old relay roster (N EPAS / M oilpump / K iBooster / O radfan / L EPB / S,T,U gang / V ign-master / P dead)
= all gone; EPAS/iBooster/oil/EPB are fuse-direct, V/gang/wake-relay replaced by the external contactor.~~

### Control inputs (into the box)  [REPLACED 2026-09-21]
- **Master-contactor coil** <- protoboard FET, gated by **OR(IGN, charge Pin-B)** via 2 signal diodes.
- **Zombie CoolingFan (PWM1/X1.7)** -> M coil (rad fan).
- **Zombie CoolantPump (GP Out 3/X1.3)** -> R coil (coolant pumps, ~480mA ea).
- **Zombie BrakeLight (PWM2/X1.6)** -> brake lights (ties into OEM harness, outside box).

### sw12 rail (drive OR charge) out
- Zombie sw12, BMS 12V, bat-boxes enable - all on R's f59-61 rail.

### Signal bulkhead (MS3102A24-5S, 16x sz16 = the SIG tier) - ★PINOUT FINALIZED 2026-09-21
Insert 24-5, pins A B C D E F G H J K L M N P R S. Physical rows from keyway down: (A B)(C)(D E)
(F G H)(J K)(L M N)(P R)(S). Higher-current (★) placed on the outer positions, spread apart.

| Pin | Signal | ~A | Box-side source |
|--|--|--|--|
| A | Rad fan power ★ | ~4-8 | H1:1 (M relay out) |
| B | IGN+ | <1 | box input (vehicle IGN) |
| C | Charger Pin-B (wake) | 0.16 | charger input |
| D | Zombie->M coil (fan ctrl) | <1 | -> M.86 relay coil (FuseRelay, x-page) |
| E | Coolant pump 1 | 0.48 | P6:5 |
| F | BMS 12V | 0.15 | feed TBD |
| G | M5Dial 12V | small | feed TBD |
| H | EPB power ★ | brief pk | P3:4 |
| J | Zombie->R coil (coolant ctrl) | <1 | -> R.86 relay coil (FuseRelay, x-page) |
| K | Coolant pump 2 | 0.48 | P6:6 |
| L | Bat boxes feed ★ | med | P2:3 |
| M | Charger Pin-C (wake rtn) | 0.16 | charger input |
| N | Trans booster pump | ~0.5 | feed TBD (coolant rail?) |
| P | ign_sense / Sw12v+ wake -> HAT | uA | f_acc / accessory (TBD) |
| R | CDL | small | P2:4 |
| S | Zombie logic 12V ★ | ~1-3 | P2:7 |

**PENDING Splice build (NOT DONE - session limit 2026-09-21, resets 3:40pm Edmonton). Nothing created.**
Build on a NEW page **"Hammond"**: (1) mil-round node **MR1** (MS3102A24-5S, 16 pins A-S labeled per table);
(2) P-connector nodes P2(3,4,7) P3(4,7) P6(5,6) H1(1,3); (3) wire the 7 clean P->MR: H1:1->A, P6:5->E,
P6:6->K, P3:4->H, P2:3->L, P2:4->R, P2:7->S. The other 9 MR pins (B,C,D,F,G,J,M,N,P) = leave labeled,
box-side source TBD (inputs / Zombie coil x-page / unestablished feeds). P1/P4/P5/D1 connectors = add later.
Project 17410eef-ffcd-4a2a-adb7-dab94271a8f4.

### CAN - bypasses the box (not routed through it).

### Still TBD before the lid label is final
- F21/F23 real slots (after the cut/reroute); the 16-pin bulkhead assignments; measured currents.
