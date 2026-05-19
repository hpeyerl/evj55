# FJ55 EV — System Diagram

## CAN Bus (500 kbps) — all nodes on same bus

```
┌─────────────────────────────────────────────────────────────────┐
│                     CAN BUS 500 kbps                            │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   M5Dial     │  │ Zombieverter │  │     BMS      │          │
│  │ steering whl │  │motor control │  │ Lilygo T-CAN │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │clockspring      │                 │                   │
│  ┌──────┴───────┐         │                 │                   │
│  │   IS3050G    │         │                 │                   │
│  │ column fixed │         │                 │                   │
│  └──────┬───────┘         │                 │                   │
│         │                 │                 │                   │
│  ───────┴─────────────────┴─────────────────┴────────────────  │
│                              │                                  │
│                   ┌──────────┴──────────┐                       │
│                   │     Dashboard       │                       │
│                   │  ESP32-P4-NANO      │                       │
│                   │  Waveshare 10.1"    │                       │
│                   │  MIPI DSI           │                       │
│                   └──────────┬──────────┘                       │
└──────────────────────────────┼──────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
┌───────┴──────┐    ┌──────────┴───────┐   ┌──────────┴───────┐
│ Headlight pot│    │   VSS sensor     │   │  EPB controller  │
│ ADC→dimming  │    │  PCNT edge count │   │ GPIO LED+button  │
└──────────────┘    └──────────────────┘   └──────────────────┘
```

## WiFi Network

```
Home WiFi ←→ ESP32 NAT Router ←→ Zombieverter web UI
                               ←→ BMS web UI
                               ←→ Dashboard (Tab5 or P4-NANO)
                               ←→ Shifter (M5Dial) web UI
```

## Hardware Selection

| # | Component | Hardware | Status |
|---|-----------|----------|--------|
| 1 | Steering wheel shifter | M5Dial + IS3050G CAN unit | ✅ Done |
| 2 | BMS interface | Lilygo T-CAN485 | ✅ Done |
| 3 | NAT router | ESP32 (dedicated, esp32_nat_router) | ⏳ TBD |
| 4 | Dashboard (bench/dev) | M5Stack Tab5 (ESP32-P4) | ✅ Working |
| 5 | Dashboard (production) | Waveshare ESP32-P4-NANO + 10.1" DSI | ⏳ Next |
| 6 | Reverse camera | TBD (CSI too short for 14ft run) | 🔮 Future |
| 7 | EPB controller | Existing EPB + GPIO from dashboard | ⏳ Pending |

## CAN Signal Map

| Signal | CAN ID | Source | Notes |
|--------|--------|--------|-------|
| Motor temp | 0x125 | Zombieverter (tmpm) | oic mapping |
| Inverter temp | 0x126 | Zombieverter (tmphs) | oic mapping |
| Vehicle speed | 0x257 | Zombieverter (Veh_Speed) | oic, x10 gain |
| SOC | 0x355 | BMS (SOC) | oic mapping |
| Pack volts | 0x356 | Zombieverter (udc) | oic, x10 gain |
| Pack amps | 0x356 | Zombieverter (idc) | oic, x10 gain |
| Battery temp | 0x356 | BMS (BMS_Tmax) | oic, x10 gain |
| 12V aux | 0x210 | Zombieverter (uaux) | oic, x10 gain |
| Gear (PRND) | 0x312 | M5Dial shifter | direct, no oic needed |
| Cruise speed | 0xDEAD | Zombieverter (cruisespeed) | TODO: assign CAN ID |
| Cruise state | 0xDEAD | Zombieverter (cruisestt) | TODO: assign CAN ID |

## Dashboard GPIO (P4-NANO — to be assigned)

| Signal | Type | Notes |
|--------|------|-------|
| CAN TX | TWAI output | Any free GPIO + IS3050G |
| CAN RX | TWAI input | Any free GPIO + IS3050G |
| Headlight pot | ADC input | Backlight + CAN dimming master |
| VSS | PCNT input | Pulse counter, cross-check speed |
| EPB green LED | GPIO input | Active = brake released |
| EPB red LED | GPIO input | Active = brake applied |
| EPB button | GPIO output | Pulse low ~200ms to toggle |
| Backlight PWM | LEDC output | Already on P4-NANO board |

## Clockspring Wiring (M5Dial to column IS3050G)

| Clockspring pin | Signal | Notes |
|-----------------|--------|-------|
| 1 | GND | Common ground |
| 2 | 5V | Powers IS3050G on column |
| 3 | UART TX (ESP32 to IS3050G) | 3.3V logic, 500kbps |
| 4 | UART RX (IS3050G to ESP32) | 3.3V logic, 500kbps |
| 5-10 | Spare | Available for other signals |

## Pending Items

- [ ] Waveshare P4-NANO + 10.1" display bring-up (port tab5_display.c to waveshare_display.c)
- [ ] VSS pulse counter code (exists in another chat, needs integration)
- [ ] Headlight pot ADC + CAN dimming broadcast
- [ ] EPB GPIO task + auto-engage on P gear
- [ ] NAT router hardware selection and flash
- [ ] Zombieverter oic CAN mappings (script: scripts/setup_can_mappings.sh)
- [ ] Cruise control CAN IDs (currently 0xDEAD stubs)
- [ ] RFID immobilizer on M5Dial (hotel key card UID whitelist)
- [ ] dir_confirmed cross-check (Zombieverter dir vs M5Dial gear request)
- [ ] Montserrat 72pt font (working, gen script at scripts/gen_font.sh)
- [ ] Power arc regen direction fix (filled from center downward)
