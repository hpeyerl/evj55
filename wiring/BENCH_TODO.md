# EVJ55 Fuse/Relay Box - Bench TODO

Working checklist for the ML350/Hammond box build. Design detail lives in
`EVJ55_ML350_powerdist.md`; box hardware in `ML350_box_reference.md`; mil-round pinout +
conductor list in `box-conductors.md`.

---

## Physical build

- [ ] **Extend all populated Px pigtails** to reach the Altech strip - even the unused ones, so the
      box never has to come back out. Lineman/Western-Union splice + Raychem heat-shrink, staggered
      so the bundle stays flat. Full populated-pin list = `ML350_box_reference.md`.
- [ ] **Mount the Altech HE1WPR/12** (20A) terminal strip under the FR box.
- [ ] **Wire Px -> mil-round** per the chart below (sz16 mil contacts = **16 AWG max**).
- [ ] **Heavy loads out via panel-mount XT60E-1** (DECIDED - ordered): one per load (EPAS, iBooster,
      oil), bolted to the box wall, mate from outside - **no gland**. **Fused in-box** (F24=EPAS -> P1:2,
      F29=iBooster -> P1:1, ~20A MAXI oil -> **F40/P3:1** heavy spade). EPAS/iBooster XT60 = **power +
      dedicated ground** (return to GND stud); oil XT60 = **power only** (chassis-grounds locally, 12AWG).
      EPAS/iBooster **~40A / 10AWG class**.
      Seal the flange (thin gasket/RTV) + cap when unmated - worst case is indirect car-wash spray, so IP
      is a non-issue.
- [ ] **EPAS + iBooster dedicated ground returns** - run the ground (10AWG black) back to the **GND
      stud**, NOT a local chassis bolt. They're precision steering/brake actuators; a ground offset
      degrades them (Toyota ran EPAS 10AWG red+black). Fan/pumps still ground locally.
- [ ] **CM3/HAT feed -> battery post** directly (its own ~15-20A fuse at the post), out of the box -
      it's permanent-B+, doesn't belong in the switched box. Keep only the **OR'd-wakeup signal wire**
      (mil-round P) running from the box to the CM3 wake pin.
- [ ] **Build the protoboard** (in the Hammond box next to the ML350): 2 signal diodes (IGN, charge
      Pin-B) -> OR node -> low-side FET -> AEV14012 coil-lo; coil-hi = Perm B+ via F-Coil ~5A; expose
      the OR'd-wakeup. Size the FET for the AEV14012 coil (~0.35A hold).
- [ ] **Install F-Main** - 100A automotive MEGA (slow) on the Perm B+ -> contactor feed.
- [ ] **J1772 home resistor-spoof** (permanent State-C) so the EVSE energizes AC on plug-in
      -> charger Pin-B goes 12V -> box wakes. (Smart/public CP reader = separate, needs its own power.)

## Verify / meter (before buttoning up)

- [ ] **Meter P5:14 and P5:1** (M/rad-fan and R/coolant coil-low taps): each must be **isolated /
      continuous to its relay coil pin, NOT continuous to Bat+.** The box CSV disagrees with the later
      buzz-out here - trust the buzz-out but confirm, because a Bat+ pin here = dead short the moment
      you try to fire the relay.
- [ ] **Confirm AEV14012 main-terminal polarity/orientation** before mounting (magnetic blowout).

## Design-open (decide / wire later)

- [ ] **Inside-feed side of mil-round F (BMS 12V) and M (Charger Pin-C)** - box fuse / protoboard ->
      MR1-F. Only the outside (MR1-M) side is wired so far.
- [ ] **Controls-accessory (P2:6) + Status (P2:9) box-crossing** bulkhead path - TBD.
- [ ] **Box-hot sense line to CM3** - weld-closed / stuck-on-contactor alarm (CM3 reads state only).
- [ ] **Inverter (traction) enable** - hard-wire-gate to drive-only, or rely on Zombie charge/drive
      mutual-exclusion + HVIL?
- [ ] **Rad-fan failsafe** - dumb overtemp switch in parallel on M's coil-low.

---

## Spare-HAT reuse (optional - 5 EVJ55 Vehicle Interface HATs were made, ~4 spare)

Use a spare HAT as a bare **carrier** (its power front-end, AOD4184A low-side FETs, sealed connectors)
- **NOT plugged onto a CM3**, no MCU driving anything.

- [ ] **OR/wake on a spare HAT:** the AOD4184A MagneRide FETs are already low-side N-FETs (source->GND,
      drain->MR_SW connector) = the config the contactor drive needs. Wire the 2 signal diodes (IGN +
      charge Pin-B) -> OR node -> the FET **gate** (reach it at its header pin); **drain -> AEV14012
      coil-lo**; source already GND. A 12V OR-node fully turns it on (within Vgs). Check the HAT
      schematic: (a) the OR node reaches the gate at >~4-5V (watch for a pulldown divider), (b) a gate
      pulldown exists so it's off when both inputs are cold. Works **passively** - the HAT needn't even
      be powered.
- [ ] **AVC2 emulator on a spare HAT + ESP32:** logic needed here -> add an ESP32. Use the HAT's sealed
      connectors for the J1772 inlet, a spare MOSFET channel to switch the CP-state resistor, and build
      the CP-read front-end (pilot = +/-12V 1kHz PWM -> divider/clamp to an ESP32 ADC/GPIO; a Block-A
      front-end may cover most of it). Public-charging path; home path = the resistor-spoof above.

---

## Px -> mil-round chart (for the strip)

Currents ~ (from `box-conductors.md` where known, else est.); AWGs are sizing recs - sz16 mil
contacts cap at **16 AWG**, so nothing bigger on the mil-round side.

| MR pin | Circuit | From Px | ~A | AWG |
|--|--|--|--|--|
| A | Rad fan power | P4:13 (was H1:1; f49 bussed there) | ~4-8 | 16 |
| E | Coolant pump (VW) | P6:5 | ~2-5 | 16 |
| H | EPB power | P3:4 | few | 18 |
| L | Bat boxes | P2:3 | ~10 | 16 |
| R | CDL | P2:4 | small | 18 |
| S | Zombie logic | P2:7 | ~10 | 16 |
| D | CoolingFan ctrl (M coil-low) | P5:14 | <1 | 18-20 |
| J | CoolantPump ctrl (R coil-low) | P5:1 | <1 | 18-20 |

**Not on the strip** (land on the protoboard, not a Px pigtail): mil-round **B** (IGN+), **C**
(Charger Pin-B), **M** (Charger Pin-C), **P** (OR'd-wakeup). **F** (BMS 12V) inside-feed TBD.
**G / K / N** = spare.
