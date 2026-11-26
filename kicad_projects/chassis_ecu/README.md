# chassis_ecu

ESP32-S3 + 2x CAN board for the parking pawl, J1772 pilot and contactor-weld sense.
The EPB stays on the Revus controller. Spec: `evj55_contexts/CHASSIS_ECU_CONTEXT.md`.

The schematic is generated. Edit `gen/chassis_ecu.py`, then:

    cd gen && /usr/bin/python3 build.py

`build.py` rewrites the `*.kicad_sch` files, runs `kicad-cli` ERC, and checks the exported
netlist against the definition (every pin on its intended net). Use the system python: KiCad's
libraries and `pcbnew` are installed there.

Every pin is drawn as a short stub with a net label (or power symbol); connectivity is by label
name. Layout is one functional block per row.

## Parts / BOM
- `gen/jlc_select.py <cache.sqlite3>` picks LCSC parts from the jlcparts database
  (yaqwsx.github.io/jlcparts/data/cache.zip + cache.z01..z05, a split zip of one 2.1 GB sqlite file;
  the concatenated parts start with a 4-byte split marker) and writes `gen/lcsc_parts.json`.
  Preference: in stock, JLC basic > preferred > extended.
- `gen/bom.py` writes `chassis_ecu_bom_jlc.csv` (JLCPCB assembly format).
- Not assembled by JLC: U2 ESP32 module (hand-solder; N8, or N4 = LCSC C2913197), connectors,
  solder jumpers, test points.
- 63 BOM lines, 151 placements. Low JLC stock (< 5000) on the crystal,
  BTN8982TA, CPC1117N, FDD4685, LSM6DSOX, MCP23017, SMCJ22A, TLV3201 - recheck at order time.

## Status
- Drawn (0 ERC errors, netlist self-check OK): Power, MCU, CAN, IO (MCP23017, 6 opto inputs,
  4 light outputs, status LEDs), Motors (pawl high-side, BTN8982TA), J1772 (CP state + read,
  PP read), Sensors (ADS1115, LSM6DSO), Connector.
- Connector pin numbers are PROVISIONAL until the 32-pin header drawing arrives.
  Pins 4-13 and 29-31 are spare (NC).
- 4 ERC warnings: the SparkFun LSM6DSOX symbol types its strap pins bidirectional (benign).
- Design stall current 20 A.  PP is read on this board
  (Zombie `interface=CPC`).  Open: connector drawing.

## ESP32-S3 pin map
| GPIO | Net | GPIO | Net |
|---|---|---|---|
| IO0 | ESP_BOOT | IO21 | CAN2_INT |
| IO4 | ANA1 (ADC1, test pad) | IO41 | CP_DUTY |
| IO5 | ANA2 (ADC1, test pad) | IO42 | CP_S2_OPEN |
| IO6 | PAWL_IS (ADC1) | IO47 | IMU_INT1 |
| IO7 | VSENSE_12V (ADC1) | IO48 | PAWL_DRV |
| IO10 | IOX_INT | IO19/20 | USB D-/D+ |
| IO11 | SPI_MOSI | IO43/44 | UART TX/RX (debug) |
| IO12 | SPI_SCK | IO17 / IO18 | CAN1_TXD / CAN1_RXD |
| IO13 | SPI_MISO | IO15 / IO16 | I2C_SDA / I2C_SCL |
| IO14 | CAN2_CS | unused (strapping) | IO3, IO45, IO46 |
| spare (ADC1) | IO1, IO2, IO8, IO9 | spare | IO35-IO40 |

## I2C
0x20 MCP23017, 0x48 ADS1115, 0x6A LSM6DSO.

## MCP23017
GPA0-5 opto IN1-6 (P_SENSE, BRAKE, WELD1, WELD2, IN5, IN6; active-low), GPA7 STAT1 LED,
GPB0-3 light OUT1-4, GPB6 PAWL_INH, GPB7 STAT2 LED. GPA6, GPB4, GPB5 spare.
