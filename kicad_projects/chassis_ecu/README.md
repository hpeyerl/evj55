# chassis_ecu

ESP32-S3 + 2x CAN board for the parking pawl, EPB (2 calipers), J1772 pilot and contactor-weld
sense. Spec: `evj55_contexts/CHASSIS_ECU_CONTEXT.md`.

The schematic is generated. Edit `gen/chassis_ecu.py`, then:

    cd gen && /usr/bin/python3 build.py

`build.py` rewrites the `*.kicad_sch` files, runs `kicad-cli` ERC, and checks the exported
netlist against the definition (every pin on its intended net). Use the system python: KiCad's
libraries and `pcbnew` are installed there.

Every pin is drawn as a short stub with a net label (or power symbol); connectivity is by label
name. Layout is one functional block per row.

## Status
- Done: Power (12V in, protection, LM5164 3.3V buck, 12V sense), MCU (ESP32-S3, USB-C, reset/boot),
  CAN (CAN1 native, CAN2 MCP2518FD).
- To do: connector (32-pin ECU header, footprint pending), I/O (MCP23017, opto inputs, FET
  outputs), EPB H-bridges, pawl output, J1772 CP/PP, sensors (ADS1115, LSM6DSO, INA226).

## ESP32-S3 pin map
| GPIO | Net | GPIO | Net |
|---|---|---|---|
| IO0 | ESP_BOOT | IO21 | CAN2_INT |
| IO1 | HB_L_IS (ADC1) | IO35 | HB_L_IN1 |
| IO2 | HB_R_IS (ADC1) | IO36 | HB_L_IN2 |
| IO4 | ANA1 (ADC1) | IO37 | HB_R_IN1 |
| IO5 | ANA2 (ADC1) | IO38 | HB_R_IN2 |
| IO7 | VSENSE_12V (ADC1) | IO39 | HB_L_INH |
| IO10 | IOX_INT | IO40 | HB_R_INH |
| IO11 | SPI_MOSI | IO41 | CP_DUTY |
| IO12 | SPI_SCK | IO42 | CP_S2_OPEN |
| IO13 | SPI_MISO | IO48 | PAWL_DRV |
| IO14 | CAN2_CS | IO19/20 | USB D-/D+ |
| IO15 | I2C_SDA | IO43/44 | UART TX/RX (debug) |
| IO16 | I2C_SCL | spare | IO6, IO8, IO9, IO47 |
| IO17 | CAN1_TXD | unused (strapping) | IO3, IO45, IO46 |
| IO18 | CAN1_RXD | | |
