# Electrical Box - Conductor List

Every conductor crossing the boundary of the electrical box (which contains the ML350 fusebox
+ the wake diodes). Drives the connector plan. Started 2026-08-28, grows as gaps fill.

**Tiers:** FAT >25A -> M6/M8 feed-through stud (or HD30)  /  MED 5-25A -> Deutsch **DTP (25A)**  / 
SIG <5A -> Deutsch **DT (13A)**. `~` = estimate, **TBD** = unknown.

## Running tally - CLOSED (2026-08-28), ~24 conductors + case-ground
- **FAT (studs): 4** - main +Bat, EPAS, iBooster, **trans oil pump (>20A)**  /  (chassis Gnd = case bond, not a connector)
- **MED (DTP / Cannon sz12-16): 4** - HAT +Bat (~20-25A), rad fan, EPB, Webasto (future)
- **SIG (DT / Cannon sz16-20): ~16** - IGN+, Pin-B/C, Zombie sw12, BMS, ign_sense, M5Dial, 3x Zombie coil-lo controls, 3x enables (S/T/U), 3x pumps (coolantx2 + trans booster)
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
| 6 | EPAS power | OUT | EPAS unit | ~40-80 | **FAT** | stud/HD30 | relay N (5-gang); (!) confirm cont/peak |
| 7 | iBooster power | OUT | iBooster | ~50-100 pk | **FAT** | stud/HD30 | relay K or R; (!) confirm cont/peak |
| 8 | HAT +Bat (CM3 + MagneRide) | OUT | HAT (cabin) | ~20-25 | **MED-hi** | DTP or gland | **permanent**; firewall crossing; MR ~15-20A of it |

## Cooling / pumps OUT

| # | Conductor | Dir | Far end | ~A | Tier | Connector | Notes |
|--|-----------|-----|---------|----|------|-----------|-------|
| 9 | Trans oil pump | OUT | trans | **>20** | **MED-hi/FAT** | **HD30 / stud** | relay M; (!) Herb: exceeds 20A -> past DTP; get exact |
| 10 | Rad fan | OUT | fan | 4.25 | MED | DT/DTP | relay O; Zombie-controlled |
| 11 | Coolant pump 1 | OUT | pump | ~2-3 | SIG | DT | relay P; Denso 064100-1110, teeny |
| 12 | Coolant pump 2 | OUT | pump | ~2-3 | SIG | DT | 2nd Denso - TWO used because one may not flow enough |
| 13 | Trans booster pump | OUT | pump (far) | ~2-3 | SIG | DT | new; boosts trans leg of series loop |
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
| 20 | Zombie -> coolant coil-low | IN | Zombie | <1 | SIG | DT | = Zombie **CoolantPump** (precharge->drive+charge); P coil-high f50/Bat+ = OK |
| 21 | Zombie -> trans-pump coil-low | IN | Zombie | <1 | SIG | DT | **gang with #20 CoolantPump** (same cooling demand) -> NO extra Zombie pin |
| 22 | Zombie enable (gang S) | OUT | Zombie | <1 | SIG | DT | ignition-enable gang; (!) may merge with #15 |
| 23 | Inverter enable (gang T) | OUT | inverter | <1 | SIG | DT | gang |
| 24 | Bat-boxes enable (gang U) | OUT | bat boxes | <1 | SIG | DT | gang |

**(Oil-pump PWM `GS450pumpPwm` = Zombie->controller direct, NOT through this box - on Splice already.)**

### Zombie IOMatrix pin budget
Out2 = NegContactor (used). Allocation: **SL1 = CoolingFan** (box), **SL2 = CoolantPump** (box),
**Out1 = BrakeLight** (outside box), **Out3 = free** (HvActive if wanted), **PWM1-3 = free**
(CpSpoof NOT needed if AVC2 used). Trans-booster pump gangs onto CoolantPump. Comfortable - box = 2 pins.
Park-pawl interlock = a Zombie **INPUT** (separate budget), not an output.

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
7. **Cannon "millrounds"** (Herb has some) - DT pins won't reliably retain in Cannon MIL inserts (different contact/retention systems); use Cannon native contacts. BUT MIL rounds carry more A/contact (sz16 ~13A, 12 ~23A, 8 ~46A, 4 ~80A) -> could REPLACE the Deutsch bulkheads + absorb some heavy loads into one sealed shell. (!) get series/shell/contact layout -> map conductor list onto them.

## Enclosure
**12x12 cast-aluminum WATERPROOF Hammond box** houses: ML350 fusebox + 1-2 busbars + the wake-switch board + supporting bits (Herb 2026-08-28).
- Plenty of wall real estate (4x 12" walls) for bulkhead connectors + studs -> the ~25-40 conductor plan is physically fine.
- **Waterproof -> all penetrations must stay sealed:** sealed bulkhead connectors (Deutsch DT / Cannon MIL are sealed) or sealed glands; studs need sealed feed-throughs. Reinforces connectors over open terminals.
- **Cast-Al case = ground plane** -> chassis-ground stud to the case (covers conductor #2); box bonds to chassis.
- Room for the wake-switch small board (the "worst-case protoboard") is a non-issue here.
