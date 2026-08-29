# Charging: J1772 + Dilong + ZombieVerter — Reference

How AC charging works on the FJ-55 EV, why the Dilong needs help, and the DIY plan to skip the
AVC2. Reference doc — ask for "the charging explanation" and this is it. (2026-08-28)

## The hardware
- **Charger:** Dilong `DA8KM22A-400C-14RC` — combo **6.6 kW OBC + 1.5 kW DCDC**. Speaks the
  **Elcon CAN protocol**. LV signal connector = ECO MATE-RM / AQUARIUS `MS20M23F`, 22 AWG; HV ground = M8.
  - **"Elcon" = a charger brand AND a CAN protocol.** The real Elcon (TC Charger) is a dumb air-cooled
    charger that needs a **CAN charge controller (EVCC, sold separately)** to set V/I. Our Dilong is a
    *different* charger that speaks the *same* Elcon CAN language — so `chargemodes=Elcon` in Zombie
    means "command it via the Elcon protocol," with **Zombie playing the EVCC role** (we don't buy an
    EVCC). The J1772 handshake a full EVCC would also do = the piece we DIY (Dilong has no pilot logic).
  - ⚠ **"Elcon2"** (the contactor gotcha) is NOT the charger — it's a Zombie-side chargemode/config
    variant, likely newer firmware than the local source. Still to pin down.
- **Inlet:** J1772 (Type 1).
- **VCU:** ZombieVerter (Stm32-vcu) — coordinates charging over CAN.
- **BMS:** Lilygo T-CAN485 (ESP32) — sets the charge-current ceiling.

## Charger connector pinout (Dilong — matches openinverter wiki)
| Pin | Function |
|-----|----------|
| A / G | CAN Bus High / Low (VCU ↔ charger) |
| **B** | **BMS/VCU Power +, 12V+ when AC applied** ← the charge-wake source |
| **C** | BMS/VCU Power − (12V−) |
| E / F | HVIL interlock loop (HV safety, series — NOT power) |
| T | DCDC logic power (apply 9–16V) |
| S | DCDC enable (9–16V) — OR'd with the CAN enable command |
> Cascadia variant pinout differs slightly (per wiki, unspecified).

## The core problem: it's THREE things, not one
Getting a pack to actually charge requires all three, and they're independent:

1. **EVSE handshake (CP)** → makes the wall/station *deliver AC*.
2. **Plug detect (PP)** → tells ZombieVerter a plug is in, so it enters charge mode.
3. **Charger command (Elcon CAN)** → tells the Dilong to actually push current.

**The Dilong does NONE of #1 or #2 — it leaves CP and PP unconnected (no pilot intelligence).**
So you must supply the CP handshake and route PP to Zombie yourself. Skipping #1 is the classic
trap: you can fool Zombie into "charge mode," but with no CP handshake the EVSE never closes its
contactor → no AC → **pack voltage never rises** even though everything *looks* like it's charging.

## J1772 basics (CP & PP)
- **CP (Control Pilot):** the **EVSE drives** a ±12V, 1 kHz PWM. The **car responds by switching
  resistance to ground**: 2.74 kΩ = state B ("connected"); add 1.3 kΩ + series diode = state C
  ("ready — deliver power"). The PWM **duty cycle advertises the max current** the circuit allows
  (roughly Amps = duty% × 0.6). CP is *not* a clean car output — it's a modulated-resistance
  interface (+ optional duty reader). The resistor spoof, the AVC2, and Zombie's `CpSpoof` are all
  just ways to do this.
- **PP (Proximity Pilot):** a **resistor-coded** signal (different resistances for cable rating and
  for latch-button pressed). The car reads it as an **analog voltage** to know a plug is inserted.

### Why the car cares about advertised current
A J1772 EVSE does **not physically limit current** — it advertises a max via CP duty and *trusts the
car to comply*. Draw more and you trip the station's breaker.
- **Home / known EVSE:** *you* control both ends — the EVSE's limit and the Dilong's fixed output.
  Set the Dilong ≤ your circuit rating and you can **ignore CP duty entirely** → a dumb resistor
  spoof is safe.
- **Public stations:** the advertised limit **varies and you don't control it** (16A here, 32A
  there). A fixed 30A Dilong into a 16A post = overdraw = trip. So the car **must read CP duty and
  throttle the Dilong to match.** That's the *only* reason to read CP.

## ZombieVerter side (from Stm32-vcu source)
- **PP input:** read via `IOMatrix::PILOT_PROX`, assigned to **GP Analog 1 (conn pin 9, GPIOC2)** or
  **GP Analog 2 (conn pin 8, GPIOC3)** by setting **`GPA1Func` / `GPA2Func` = PILOT_PROX**
  (`stm32_vcu.cpp:248`). Analog, because PP is resistor-coded.
- **Charge trigger** (`stm32_vcu.cpp:255,266`): `RunChg=true` when `ppValue ≤ ppThresh` (plug
  detected) **and** `ChgSet==1` **and** `!ChgLck`. Then `chargeMode=true` when
  `ControlCharge(RunChg, ACrequest)` is true and not in RUN.
- **Charger select:** `chargemodes` param (`param_prj.h:367`), **Elcon = 6**. **Set it and `cmd
  save`** so it persists — that kills "select Elcon every time."
- **Elcon CAN** (`ElconCharger.cpp`):
  - TX **`0x1806E5F4`** @200ms: `[0:1]`=Voltspnt×10, `[2:3]`=current setpoint×10, `[4:7]`=0.
  - RX **`0x18FF50E5`**: `[0:1]`=out V×0.1, `[2:3]`=out A×0.1, `[4]`=status.
  - Current setpoint is capped by **`BMS_ChargeLim`** (BMS sets the ceiling). No CP-limit input here
    → public charging must impose the station limit separately (via the CP reader).
- **Wake:** the Dilong's **pin B (12V when AC applied)** wakes Zombie (see `charge-wake-arch`), which
  boots into this logic.
- **★Charge termination (→ opens HV contactors).** MOD_CHARGE→MOD_OFF when `chargeMode` goes false
  (`stm32_vcu.cpp:692`) ← `RunChg`=false, which falls in **three** places, all → contactors open:
  1. **Unplug** — `ppValue > ppThresh` (line 259)
  2. **Voltage term** — `udc ≥ Voltspnt && idc ≤ IdcTerm` (line 295) → also sets `ChgLck`
  3. **BMS shutdown** — `selectedBMS->MaxChargeCurrent()==0` (line 301) → also sets `ChgLck`
  - So the **BMS CAN end a charge** — but only if it reports **exactly 0** *and* Zombie's configured
    `selectedBMS` actually receives your BMS's charge limit over CAN. A **low-but-nonzero** BMS limit
    with `udc < Voltspnt` fires *neither* #2 nor #3 → Zombie trickles in **MOD_CHARGE, contactors
    CLOSED** = the "contactors stay closed" gotcha.
  - **SoC target:** two clean levers — set **`Voltspnt`** to the target voltage (CM3 per session), OR
    have the BMS report **exactly 0** at target. Either opens contactors AND sets `ChgLck`.
- **★`ChgLck` lockout — blocks plugged-in "maintenance" charging.** Auto-termination (#2 or #3) sets
  `ChgLck=true`, which **only clears in `MOD_RUN`** (`line 309`: "reset when we drive off"). So once
  full, Zombie **will NOT re-charge while parked+plugged** until you drive. Timer mode (`ChgSet==2`)
  is also gated by `!ChgLck`. ⇒ **NOT like a regular EV** (no periodic top-up while plugged); plus
  contactors are open post-charge so the DCDC can't maintain the 12V aux either. Regular-EV behavior
  = a firmware feature (clear `ChgLck` on HV/aux sag + a parked-maintenance loop).

## The DIY plan (skip the AVC2 — $45 part but ~$93 shipping + Canada duty)
The AVC2 = CP handshake + PP/latch + a relay. All DIY-able:

- **Home-only (now):** a **resistor spoof** — 2.74 kΩ CP→GND always, switch in 1.3 kΩ + diode for
  state C. ~$3. No duty reading (you've pre-set the Dilong ≤ your circuit).
- **Public (soon — "not much later"):** a tiny **ESP32/RP2040 J1772 car-side controller** that reads
  the CP PWM duty and throttles the Dilong to the station limit. ~$15, open-source designs exist.
  **Since public is coming soon, building this from the start (it does home too) likely beats a
  throwaway resistor spoof.**
- **Both cases:** wire inlet **PROX → Zombie PP analog input**; set **`chargemodes=Elcon`,
  `ChgSet=1`, saved.**

### Expected auto-charge sequence
plug in → CP circuit signals state C → EVSE delivers AC → Dilong pin B goes hot → wakes Zombie →
Zombie sees PP + Elcon-saved → commands Dilong over `0x1806E5F4` → current flows (capped by
`BMS_ChargeLim`, and by CP-advertised limit once the public reader exists).

## BMS cell voltage & SoC during charge (for the BMS + dashboard code)
Q: if the cells read the *charging* voltage, how does the BMS know real cell voltage / SoC?

The BMS measures each cell's **actual terminal voltage** (sense wires). Under charge that's
`true_OCV + I·R_internal + polarization` — genuinely elevated vs the resting voltage for that SoC.
Two independent uses:

1. **Cell protection / charge termination** — the *loaded* terminal voltage is exactly what to
   limit. Stop when **any cell terminal hits its max charge voltage** (~4.15V for i3 NCM). That
   correctly includes the I·R rise; no correction needed. So protection works fine off the raw
   measured voltage.
2. **SoC (the 80/100 target)** — you CANNOT read SoC from the loaded voltage (inflated). SoC =
   **coulomb counting** (integrate pack current) as primary, **recalibrated against OCV at rest**
   (current off → terminal V relaxes to OCV → SoC via the cell OCV-curve; drift correction). The
   dated rested module-spread readings are exactly this OCV data. Optional: **I·R subtraction**
   (estimate R_int from ΔV/ΔI, subtract → approximate live OCV) — advanced, not required.

⇒ Not cell-resistance-conversion, not black-box. **TODO (BMS firmware):** SoC estimation
(coulomb count + rest-OCV recal) — currently the BMS reads per-cell V (good for protect/balance) but
SoC estimation is the piece to build for accurate SoC-target charging. **Dashboard:** shows SoC, so
it consumes whatever the BMS derives — coordinate the SoC source with the BMS chat.

## ⚠ Known gotcha: contactors stay closed (Elcon2)
Report (2026-08-28): with **"Elcon2" configured, the HV contactors STAY CLOSED** → manual
intervention required every charge. Two issues:
- **"Elcon2" is NOT in the ChargeModes enum** in the source read here (`Off/EXT_DIGI/Volt_Ampera/
  Leaf_PDM/TeslaOI/Out_lander/Elcon`) → likely a **newer firmware** than local, or shorthand. Pin
  down what Elcon2 actually is.
- **Root points to firmware not returning to `MOD_OFF` after charge** — that's where
  `NEGCONTACTOR/dcsw/prec` are cleared (contactors open). So the **auto-STOP** side of charging needs
  solving just like auto-start. Leaving HV live post-charge is a safety issue. Candidate owner: the
  BMS/CM3 automation (command charge-end → contactors open) — bench investigation needed.

## Open / to-verify
- ⚠ **`ACrequest` for a dumb Elcon with `targetChgint=Unused`** — what supplies it? The one link not
  resolved from a static source read; confirm on the bench.
- **Auto-charge-on-plug vs manual gate:** with Elcon saved + PP wired, *any* plug-in auto-charges.
  If that's unwanted sometimes, `ChgSet` (or leaving Elcon unset) is the manual interlock — a
  possible reason to NOT save Elcon permanently.
- Elcon TX frame sends uninitialized bytes when `ChRun==false` (firmware quirk; harmless-ish).

## Sources
- openinverter wiki: https://openinverter.org/wiki/Dilong/Cascadia_Chargers (pinout; no Elcon/CAN)
- ZombieVerter firmware: `~/GitHub/Stm32-vcu/src/{stm32_vcu.cpp, ElconCharger.cpp}`,
  `include/param_prj.h`
- EVWest AVC2 (for reference): https://evwest.com/j1772-active-vehicle-control-module-avc2-for-public-charge-stations
