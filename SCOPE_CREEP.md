# FJ55 EV — Scope Creep Tracker

Items parked here are real, planned, and worth doing — just not on the critical path for the dashboard firmware.

---

## BLE auth / vehicle access system

**Summary:** M5Dial as auth arbiter, BLE phone presence as primary authorization method.

**Details:**
- M5Dial (dedicated unit, not the steering wheel one) runs BLE scanner + RFID reader + PIN entry
- BLE presence via bonded Android phones — up to 3 family phones whitelisted
  - Bonded pairing through Android system Bluetooth settings (no companion app required)
  - IRK-based MAC resolution handles Android MAC randomization
  - RSSI threshold gates "phone in cabin" vs "phone in garage" — needs tuning
- RFID hotel-key fallback — physical token for yard moves, guests, non-technical users
- PIN backstop via M5Dial rotary encoder — rotate to digit, press to confirm
- Auth state broadcast as CAN frame, consumed by dashboard and VCU enable / EPB logic
- Auth arbiter remains functional during dashboard OTA reboot

**Optional add-on (per phone, requires F-Droid):**
- Gadgetbridge on technical family phones → BLE notification forwarding to dashboard
- Implements Pebble protocol on ESP32 side
- Useful for incoming call display, SMS sender, nav prompts

**Open questions:**
- RSSI threshold value — empirical tuning needed in the actual vehicle
- Whether esp-hosted exposes BLE GATT client API (needed for Gadgetbridge/ANCS path)
- Lock/unlock CAN frame definition — coordinate with VCU enable line and EPB logic

---

## Air suspension — rear sag correction

**Summary:** 4-corner air suspension to compensate for added battery weight on the FJ55.

**Details:**
- VAG/Mopar valve block (7L0698014 / 68087233AA) — best donor: 2007 Touareg V8 (air suspension standard on 4.2L)
  - Touareg dryer housing needed alongside block (integrated N111 exhaust valve)
  - Source: Row52 Calgary
- Compressor: BMW E70 X5 Wabco
- Shocks: GM air shocks (84176675)
- Ride height sensors: VAG rotary (G76–G78/G289), 5V PWM output
- Controller: ESP32-P4 (dedicated)
- Solenoids: NC on common 12V rail, switched grounds — direct GPIO/MOSFET control

**Status:** Sourcing phase. Touareg V8 donors identified at Row52.

---

## RFID immobilizer (steering wheel M5Dial)

**Summary:** Static-UID hotel key card as ignition key, read by the steering wheel M5Dial.

**Note:** Superseded in scope by the auth arbiter design above — RFID now lives on the dedicated auth M5Dial. Steering wheel M5Dial retains shifter + display role only.

---
