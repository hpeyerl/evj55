# chassis_ecu

ESP32-S3 CAN board for the parking pawl, J1772 pilot and contactor-weld sense.
The EPB stays on the Revus controller. Spec: `evj55_contexts/CHASSIS_ECU_CONTEXT.md`.

The schematic is generated. Edit `gen/chassis_ecu.py`, then:

    cd gen && /usr/bin/python3 build.py

`build.py` rewrites the `*.kicad_sch` files, runs `kicad-cli` ERC, and checks the exported
netlist against the definition (every pin on its intended net). Use the system python: KiCad's
libraries and `pcbnew` are installed there.

Parts are hand-placed in the generator and wired; the generator is the master copy (do not save
schematic edits made in KiCad).

## Requirements
What the schematic must satisfy. Review against these.

**Jobs:** parking-pawl drive, J1772 car-side pilot (CP) and proximity (PP), contactor-weld sense,
brake / P-position inputs, 2 analog inputs, 6-axis IMU, one CAN bus. The EPB is NOT on this board.

**Supply (J20 A2, switched 12V):**
- Steady state <= 15 V (DC-DC fed, no alternator). Spikes from inductive kickback, wiring ring and
  terminal let-go (microseconds) must be clamped; no sustained overvoltage.
- Reverse battery must not damage the logic side and must not blow the board fuse.
- Starts at about 6 V (UVLO). 3.3 V rail >= 1 A (ESP32 + CAN + sensors, ~0.6 A peak estimate).
- Low sleep current is wanted (an optional harness change feeds the board from permanent B+).

**Opto inputs x4 (J20 B2-B5: P_SENSE, BRAKE, WELD1, WELD2):** 12V-active, isolated, active-low at
the GPIO, filtered. P_SENSE taps a sense line shared with other loads, so it must draw little current.

**Pawl output (J20 A1/B1 feed, A8/B8 out):** high-side 12 V switch to the actuator (the actuator's
other lead grounds at the motor). Current sense for stall detection; firmware enforces a run
timeout. Design stall current 20 A (actual stall current not yet measured). No reverse protection on
the motor feed: the external harness fuse protects it.

**J1772 (J20 C2 CP, C3 CP_GND, C4 PP), car side - the board never generates the pilot:**
- CP -> diode -> 2.74 k to GND (state B); + 1.3 k switched in parallel (state C).
- The state-C switch must be CLOSED when the board is unpowered (12V box dead before AC arrives,
  so a dead board must still request charge). Firmware opens it to hold state B (pause / stop).
- Read CP duty (1 kHz, 10-96 %) and CP high level (+12 / +9 / +6 V = state A / B / C).
- Survive the +/-12 V CP swing; load on CP >= 100 k.
- Read PP: open / plug inserted / latch button pressed must be distinguishable.

**CAN:** one classic CAN bus (truck CAN1), in and out pins on J20 for daisy-chaining. 120R
terminator selectable, default off (mid-bus). Bus TVS. Firmware emulates the Zombie CPC (TX 0x357,
RX 0x358).

**Analog inputs AIN1/AIN2 (J20 B6/B7):** 0-15 V into the ESP32 ADC1, survive reverse / overvoltage
spikes. Coarse accuracy is fine. 12 V logic supply sensed on ADC1 as well.

**IMU:** 6-axis accel + gyro on I2C, no magnetometer. The board mounts square to the vehicle axes.

**MCU / debug:** ESP32-S3 module with PCB antenna (plastic case). USB for programming (data only;
the board runs from 12 V). UART header (DNP) as a fallback console. BOOT / RESET as jumper pads.
Expansion header J10 (DNP): I2C, 3 raw ADC1, 2 GPIO.

**Mechanical / manufacture:**
- PCB 82 x 101 mm in the case; J20 centred on an 82 mm edge.
- Case height 33 mm only over the third nearest J20: tall parts go there.
- JLC assembly with LCSC parts; J20 and test points are hand-soldered.
- A labelled GND test point for scope / logic-analyser clips.
- Automotive: conformal coat.

## PCB
`chassis_ecu.kicad_pcb` was created once by `gen/make_pcb.py`: 82 x 101 mm outline (3 mm corners,
J20 key notch), 4 layers, J20 centred on the top edge, ESP32 antenna flush with the bottom edge
(copper keep-out under it), case holes, first-pass block placement (tall parts in the top third).
The script refuses to overwrite an existing board (`--force` discards it). From here: edit in KiCad,
"Update PCB from Schematic" after schematic changes. Expected DRC items: U2 courtyard (on-board
antenna keep-out, not used here) and the paired case holes H1/H2, H3/H4 overlap.

## Parts / BOM
- `gen/jlc_select.py <cache.sqlite3>` picks LCSC parts from the jlcparts database
  (yaqwsx.github.io/jlcparts/data/cache.zip + cache.z01..z05, a split zip of one 2.1 GB sqlite file;
  the concatenated parts start with a 4-byte split marker) and writes `gen/lcsc_parts.json`.
  Preference: in stock, JLC basic > preferred > extended.
- `gen/bom.py` writes `chassis_ecu_bom_jlc.csv` (JLCPCB assembly format).
- U2 = ESP32-S3-WROOM-1-N4 (LCSC C2913197), JLC-assembled; 4 MB = 2 x ~1.9 MB OTA slots (min_spiffs).
  Not assembled by JLC: connectors (J20 = through-hole), BOOT/RESET jumper pads,
  solder jumpers, test points.
- 55 BOM lines, 114 placements. Low JLC stock (< 5000) on the
  BTN8982TA, CPC1117N, FDD4685, LSM6DSOX, SMCJ22A, TLV3201 - recheck at order time.

## Status
- Drawn (0 ERC errors, netlist self-check OK): Power, MCU, CAN (1 bus, native TWAI), IO (4 opto
  inputs, status LEDs, J10 expansion), Motors (pawl high-side, BTN8982TA), J1772 (CP state + read,
  PP read), Sensors (LSM6DSO, 2x 12V-tolerant AIN), Connector.
- Main connector J20 = Aptiv/FCI HCCPHPE24BKA90F (24-way 90 deg, key A), mates 211PC249S0005.
  Footprint from FCI drawing FSC 308654: `lib/` (generated by `gen/make_lib.py`). Footprint
  confirmed with a 1:1 printout against a real header.
- Case (listing drawing, to verify on the real part): PCB 82 x 101 mm; J20 centred on an 82 mm edge;
  4x 2.5 mm mounting holes = 2 slotted pairs (6 mm apart) at 62.2 mm centres, lower holes 7.4 mm from
  the edge opposite J20. Case outside 120 x 121 x 33 mm.
- 3D model: vendor STEP is not redistributable; put `HCCPHPE24BKA90F.stp` in `lib/3d/` (git-ignored).
- 4 ERC warnings: the SparkFun LSM6DSOX symbol types its strap pins bidirectional (benign).
- Design stall current 20 A.  PP is read on this board
  (Zombie `interface=CPC`).  Open: routing.

## ESP32-S3 pin map
| GPIO | Net | GPIO | Net |
|---|---|---|---|
| IO0 | ESP_BOOT (JP4 pad) | IO35-38 | OPTO_IN1-4 (P_SENSE, BRAKE, WELD1, WELD2; active-low) |
| IO1 | CP_LVL (ADC1) | IO39 | PAWL_INH |
| IO2 | PP_SENSE (ADC1) | IO40 | LED_STAT1 |
| IO4 / IO5 / IO10 | ANA1-3 (ADC1, J10) | IO21 | LED_STAT2 |
| IO6 | PAWL_IS (ADC1) | IO41 | CP_DUTY |
| IO7 | VSENSE_12V (ADC1) | IO42 | CP_S2_OPEN |
| IO8 / IO9 | AIN1 / AIN2 (ADC1, J20) | IO47 | IMU_INT1 |
| IO11 / IO12 | EXP_GPIO1 / 2 (J10) | IO48 | PAWL_DRV |
| IO15 / IO16 | I2C_SDA / I2C_SCL | IO17 / IO18 | CAN1_TXD / CAN1_RXD |
| IO19 / IO20 | USB D- / D+ | IO43 / IO44 | UART TX / RX (J2, DNP) |
| unused | IO13, IO14 | strapping, NC | IO3, IO45, IO46 |

## I2C
0x6A LSM6DSO. J10 brings the bus out for add-ons.

## J10 expansion (DNP)
1 GND, 2 3V3, 3 SDA, 4 SCL, 5-7 ANA1-3 (raw ADC1, 0-3.1 V), 8-9 EXP_GPIO1/2, 10 GND.

## J20 pinout (columns 1 and 8 = high-current cavities)
| Pin | Net | Pin | Net | Pin | Net |
|---|---|---|---|---|---|
| A1 | PAWL_12V | B1 | PAWL_12V | C1 | GND |
| A2 | VIN_12V | B2 | IN_P_SENSE | C2 | CP |
| A3 | CAN1_H in | B3 | IN_BRAKE | C3 | CP_GND |
| A4 | CAN1_L in | B4 | IN_WELD1 | C4 | PP |
| A5 | CAN1_H out | B5 | IN_WELD2 | C5 | spare |
| A6 | CAN1_L out | B6 | AIN1 (0-15 V) | C6 | spare |
| A7 | GND | B7 | AIN2 (0-15 V) | C7 | spare |
| A8 | MOT_OUT | B8 | MOT_OUT | C8 | GND |
