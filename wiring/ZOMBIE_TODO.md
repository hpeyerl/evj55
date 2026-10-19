# ZombieVerter (VCU) - Firmware / Config TODO

Working checklist of ZombieVerter (Stm32-vcu) config + CAN items. Hardware/box items live in
`BENCH_TODO.md`; charging detail in `charging-j1772-notes.md`; signal pinout in
`EVJ55_ML350_powerdist.md` (section 3). Detail/rationale for the private items is in the
`evj55_contexts` repo (noted inline).

Status is best-effort from the docs - some may already be set in the live VCU; verify against the
running config.

---

## IOMatrix / IO pin assignments
- [ ] **`PWM3 = HvActive`** (func 15) - gates the Dilong DCDC enable (S) on HV-active. (powerdist s3/s4)
- [ ] **PP input: `GPA1Func = PILOT_PROX`** - J1772 proximity on GP Analog 1 (conn pin 9, GPIOC2).
      (charging-j1772-notes "ZombieVerter side")
- [ ] **Inverter-enable output** - pick the Zombie low-side output that drives the inverter-enable relay
      coil (MR1 K=coil-low). Not yet assigned. (BENCH_TODO / powerdist s7)
- Already assigned (reference): CoolingFan=PWM1, BrakeLight=PWM2, CoolantPump=GP Out 3,
  NegContactor=GP Out 2, oil-pump PWM=pin 30, SL1/SL2=trans solenoids. GP Out 1 abandoned.

## Charging
- [ ] **`chargemodes = Elcon` (6), `ChgSet = 1`, SAVED.** (charging-j1772-notes "DIY plan")
- [ ] **`Voltspnt` = target charge voltage** (per-session SoC-target lever; CM3 may set it).
- [ ] **Verify `selectedBMS` receives the BMS charge limit over CAN** - a low-but-nonzero limit with
      `udc < Voltspnt` fires neither voltage-term nor BMS-shutdown -> "contactors stay closed / trickle
      forever" gotcha. (charging-j1772-notes - BMS charge-end)
- [ ] **`ChgLck` behavior** - auto-term sets it, clears only in MOD_RUN -> no parked top-up. Decide if
      the regular-EV maintenance loop is wanted (firmware feature).
- [ ] **CP handshake** - home resistor-spoof now (2.74k + 1.3k/diode for state C) vs ESP32 CP reader
      later (the AVC2 role on the universal carrier board, see evj55_contexts/ECU_CARRIER_CONTEXT.md).
- [x] **DCDC not CAN-enabled** - CONFIRMED 2026-10-19 (firmware doesn't CAN-enable the DCDC, so the
      hardware S-gate on HvActive is sufficient).

## CAN mappings (oic)
- [ ] **Apply the oic CAN mappings** - `scripts/setup_can_mappings.sh`. (system_diagram)
- [ ] **Assign real CAN IDs for Cruise speed + Cruise state** (currently `0xDEAD` placeholders).
- [ ] **Confirm bus map applied:** HAT_CAN1 <-> X1 27/28, HAT_CAN2 <-> X1 2 (rev 4.2).
      (evj55_contexts/HAT_CONTEXT.md)

## Shifter / gear / drive
- [ ] **SDO poll/write for VCU gear-change confirmation.** (evj55_contexts Shifter_M5Dial.md)
- [ ] **`dir_confirmed` cross-check** - Zombie dir vs M5Dial gear request. (system_diagram)
- [ ] **L110 dual-motor** - VCU must account for the gearset coupling or the motors fight.
      (evj55_contexts/L110_CONTEXT.md)

## Telemetry (confirm specific params)
- [ ] **Which SDO param is the charge target/threshold?** (confirm via oic / CAN map)
- [ ] **Which param is regen?** (confirm via oic)
      (both: evj55_contexts/REMOTE_TELEMETRY_CONTEXT.md)
