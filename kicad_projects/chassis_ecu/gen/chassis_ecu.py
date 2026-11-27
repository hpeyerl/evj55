"""chassis_ecu schematic definition.  Run build.py to regenerate."""
from schgen import Board, anchor

R0603 = 'Resistor_SMD:R_0603_1608Metric'
C0603 = 'Capacitor_SMD:C_0603_1608Metric'
C1206 = 'Capacitor_SMD:C_1206_3216Metric'
C1210 = 'Capacitor_SMD:C_1210_3225Metric'
SOT23 = 'Package_TO_SOT_SMD:SOT-23'


def R(s, ref, val, a, b, fp=R0603, **k):
    return s.add(ref, 'Device:R', val, {'1': a, '2': b}, fp, **k)


def C(s, ref, val, a, b, fp=C0603, **k):
    return s.add(ref, 'Device:C', val, {'1': a, '2': b}, fp, **k)


def flag(s, ref, net, **k):
    return s.add(ref, 'power:PWR_FLAG', 'PWR_FLAG', {'1': net}, **k)


# Hand placement: pt = where the pin's stub ends (the wiring point), mm.
def RV(s, ref, val, a, b, top, fp=R0603, **k):
    """Vertical R, pin 1 (net a) on top."""
    return R(s, ref, val, a, b, fp, at=anchor('Device:R', '1', top), **k)


def RH(s, ref, val, a, b, left, fp=R0603, **k):
    """Horizontal R, pin 1 (net a) on the left."""
    return R(s, ref, val, a, b, fp, at=anchor('Device:R', '1', left, 90), rot=90, **k)


def RHr(s, ref, val, a, b, right, fp=R0603, **k):
    """Horizontal R, pin 1 (net a) on the right."""
    return R(s, ref, val, a, b, fp, at=anchor('Device:R', '1', right, 270), rot=270, **k)


def CV(s, ref, val, a, b, top, fp=C0603, **k):
    """Vertical C, pin 1 (net a) on top."""
    return C(s, ref, val, a, b, fp, at=anchor('Device:C', '1', top), **k)


def CVr(s, ref, val, a, b, top, fp=C0603, **k):
    """Vertical C, pin 2 (net b) on top."""
    return C(s, ref, val, a, b, fp, at=anchor('Device:C', '2', top, 180), rot=180, **k)


def put(s, ref, lib, val, nets, fp, pin, pt, rot=0, mirror=False, **k):
    """Any part, placed so that pin's stub ends at pt."""
    return s.add(ref, lib, val, nets, fp, at=anchor(lib, pin, pt, rot, mirror), rot=rot, mirror=mirror, **k)


# Manufacturer part numbers by Value.  LCSC numbers are filled only once verified
# against the JLC parts index; JLCPCB's BOM matcher can also resolve from MPN.
MPN = {
    'LM5164DDAR': 'LM5164DDAR', 'FDD4685': 'FDD4685', 'SMAJ33CA': 'SMAJ33CA', 'BZT52C15': 'BZT52C15',
    'BAT54S': 'BAT54S', 'ESP32-S3-WROOM-1-N8': 'ESP32-S3-WROOM-1-N8', 'USBLC6-2SC6': 'USBLC6-2SC6',
    'SN65HVD230': 'SN65HVD230DR', 'NUP2105L': 'NUP2105LT1G', 'MCP2518FD': 'MCP2518FDT-E/QBB',
    'LTV-357T': 'LTV-357T',
    '1N4148W': '1N4148W', 'DMN6075S': 'DMN6075S-7', 'B5819W': 'B5819W', '2N7002': '2N7002',
    'AO3401A': 'AO3401A', 'BTN8982TA': 'BTN8982TA', 'SMCJ22A': 'SMCJ22A', 'SMAJ15CA': 'SMAJ15CA',
    'CPC1117N': 'CPC1117NTR', 'TLV3201AIDBV': 'TLV3201AIDBVR',
    'LSM6DSOX': 'LSM6DSOXTR', 'SMAJ24CA': 'SMAJ24CA',
    'BSS84': 'LBSS84LT1G', 'TYPE-C-31-M-12': 'TYPE-C-31-M-12',
    '22uH 2.2A': 'FNR6045S220MT', '1A 63V': '0466001.NRHF', 'LTV-357T': 'LTV-357T-C',
}
# LCSC numbers: gen/lcsc_parts.json, written by jlc_select.py from the jlcparts database
# (keys 'value|footprint' for passives, 'value' for parts chosen by MPN).
import json as _json
import os as _os
with open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'lcsc_parts.json')) as _f:
    LCSC = _json.load(_f)


def build():
    b = Board('chassis_ecu', 'A')

    # --- Power ----------------------------------------------------------------
    s = b.sheet('Power', 'power.kicad_sch')
    s.note('12V logic input (steady <= 15 V; TVS is for spikes) -> fuse -> SMAJ24CA bidirectional TVS -> P-FET reverse protection (same as the HAT)\n'
           '-> LM5164 buck, 3.3V 1A, 300 kHz, Type-3 ripple injection (datasheet SNVSAU4D 7.2.2).\n'
           'VOUT = 1.2 x (1 + 174k/100k) = 3.29 V.  RON = 3.3 x 2500 / 300 kHz = 27.4k.\n'
           'EN/UVLO: start 1.5 x (1 + 301k/100k) = 6.0 V, stop 5.6 V.\n'
           'L1: FNR6045S220MT 22uH, 2.2 A (LM5164 peak limit 1.75 A max), 116 mR, 6x6 shielded.\n'
           'Ripple 0.46 A p-p at 40 V in.  Type 3: CA >= 525 pF -> 3.3 nF, RA 124k -> 16 mV (8 V) .. 25 mV (40 V) at FB.\n'
           'VSENSE_12V: 100k/10k divider (12 V -> 1.09 V), BAT54S clamp to the rails.',
           20, 15)
    s.paper = 'A3'
    s.head('Input: fuse, TVS, reverse-polarity P-FET', 30.48, 48.26)
    y = 66.04                           # 12V rail
    s.tap('VIN_12V', 30.48, y)
    put(s, 'F1', 'Device:Fuse', '1A 63V', {'1': 'VIN_12V', '2': 'VIN_F'}, 'Fuse:Fuse_1206_3216Metric',
        '1', (38.1, y), 90)
    put(s, 'D1', 'Device:D_TVS', 'SMAJ24CA', {'1': 'VIN_F', '2': 'GND'}, 'Diode_SMD:D_SMA', '1', (58.42, y), 270)
    put(s, 'Q1', 'PCM_Transistor_MOSFET_AKL:FDD4685', 'FDD4685',
        {'G': 'QREV_G', 'D': 'VIN_F', 'S': '+12V_LOGIC'}, 'Package_TO_SOT_SMD:TO-252-2', 'D', (68.58, y), 270, True, text='above')
    RV(s, 'R1', '10k', 'QREV_G', 'GND', (77.47, 74.93))
    put(s, 'D2', 'Device:D_Zener', 'BZT52C15', {'K': '+12V_LOGIC', 'A': 'QREV_G'}, 'Diode_SMD:D_SOD-123',
        'K', (96.52, y), 270)
    put(s, 'C1', 'Device:C_Polarized', '47uF 63V', {'1': '+12V_LOGIC', '2': 'GND'},
        'Capacitor_SMD:CP_Elec_6.3x7.7', '1', (114.3, y))
    CV(s, 'C2', '2.2uF 100V X7R', '+12V_LOGIC', 'GND', (129.54, y), C1210)
    CV(s, 'C3', '2.2uF 100V X7R', '+12V_LOGIC', 'GND', (152.4, y), C1210)
    flag(s, '#FLG01', '+12V_LOGIC', at=anchor('power:PWR_FLAG', '1', (170.18, y)))

    s.head('LM5164 buck, 3.3 V', 180.34, 48.26)
    RV(s, 'R2', '301k', '+12V_LOGIC', 'BUCK_EN', (182.88, y))
    RV(s, 'R3', '100k', 'BUCK_EN', 'GND', (182.88, y + 12.7))
    put(s, 'U1', 'Regulator_Switching:LM5164DDA', 'LM5164DDAR',
        {'GND': 'GND', 'EP': 'GND', 'VIN': '+12V_LOGIC', 'EN/UVLO': 'BUCK_EN', 'RON': 'BUCK_RON',
         'FB': 'BUCK_FB', 'BST': 'BUCK_BST', 'SW': 'BUCK_SW'}, '', 'VIN', (205.74, y), nc=['PGOOD'])
    RV(s, 'R4', '27.4k', 'BUCK_RON', 'GND', (205.74, 78.74))
    CV(s, 'C4', '2.2nF 50V X7R', 'BUCK_BST', 'BUCK_SW', (246.38, 58.42))
    put(s, 'L1', 'Device:L', '22uH 2.2A', {'1': 'BUCK_SW', '2': '+3V3'}, 'Inductor_SMD:L_Changjiang_FNR6045S',
        '1', (259.08, 71.12), 90)
    CV(s, 'C7', '22uF 10V X7R', '+3V3', 'GND', (297.18, 76.2), C1206)
    CV(s, 'C8', '22uF 10V X7R', '+3V3', 'GND', (317.5, 76.2), C1206)
    s.add('C6', 'Device:C', '100pF', {'1': 'BUCK_RIP', '2': 'BUCK_FB'}, C0603,
          at=anchor('Device:C', '2', (246.38, 86.36), 180), rot=180)
    RV(s, 'R5', '124k', 'BUCK_SW', 'BUCK_RIP', (264.16, 86.36))
    s.add('C5', 'Device:C', '3.3nF', {'1': 'BUCK_RIP', '2': '+3V3'}, C0603,
          at=anchor('Device:C', '1', (279.4, 99.06), 180), rot=180)
    RV(s, 'R6', '174k', '+3V3', 'BUCK_FB', (226.06, 101.6))
    RV(s, 'R7', '100k', 'BUCK_FB', 'GND', (236.22, 114.3))

    s.head('12V sense for the ADC', 30.48, 96.52)
    s.tap('VSENSE_12V', 73.66, 116.84)
    RV(s, 'R8', '100k', '+12V_LOGIC', 'VSENSE_12V', (88.9, 104.14))
    RV(s, 'R9', '10k', 'VSENSE_12V', 'GND', (88.9, 116.84))
    CV(s, 'C9', '100nF', 'VSENSE_12V', 'GND', (109.22, 116.84))
    put(s, 'D3', 'Diode:BAT54S', 'BAT54S', {'1': 'GND', '2': '+3V3', '3': 'VSENSE_12V'}, SOT23,
        '3', (137.16, 116.84), 0, True)

    s.head('Scope / logic-analyser ground', 91.44, 142.24)
    s.add('TP1', 'Connector:TestPoint', 'GND', {'1': 'GND'}, 'TestPoint:TestPoint_Keystone_5000-5004_Miniature',
          fields={'MPN': 'Keystone 5001 (black)', 'JLC': 'not assembled - hand-solder (through-hole)',
                  'Note': 'silkscreen GND next to it'}, at=anchor('Connector:TestPoint', '1', (101.6, 157.48)))
    s.head('Power flags', 30.48, 142.24)
    flag(s, '#FLG02', '+3V3', at=anchor('power:PWR_FLAG', '1', (40.64, 157.48)))
    flag(s, '#FLG03', 'GND', at=anchor('power:PWR_FLAG', '1', (58.42, 157.48)))

    # --- MCU --------------------------------------------------------------------
    s = b.sheet('MCU', 'mcu.kicad_sch')
    s.note('ESP32-S3-WROOM-1-N4 (4 MB flash, no PSRAM; PCB antenna).  JLC-assembled (bottom GND pad).\n'
           '4 MB = 2 x ~1.9 MB OTA slots (min_spiffs).  -1-N8 is a drop-in if more flash is ever needed.\n'
           'Same pad pattern; the -1 footprint outline covers both.  Keep the antenna end clear of copper.\n'
           'Strapping: IO0 = BOOT (button), IO3 / IO45 / IO46 left unconnected.\n'
           'USB: data only (native USB-Serial-JTAG).  VBUS feeds only the ESD part; the board\n'
           'runs from 12V, so bench programming needs the 12V supply.\n'
           'ADC1 (IO1-10) for analog; ADC2 is unusable with WiFi.\n'
           'ADC1: IO1 CP_LVL, IO2 PP_SENSE, IO4/5/10 ANA1-3 (J10), IO6 PAWL_IS, IO7 VSENSE_12V, IO8/9 AIN1/2.\n'
           'Opto inputs IO35-38 (active-low), PAWL_INH IO39, status LEDs IO40 / IO21, J10 GPIO IO11 / IO12.\n'
           'BOOT / RESET = solder-jumper pads (short with tweezers); USB auto-reset covers normal flashing.\n'
           'Spare (unconnected): IO13, IO14.',
           20, 15)
    s.paper = 'A3'
    s.head('ESP32-S3 module', 152.4, 172.72)
    s.add('U2', 'RF_Module:ESP32-S3-WROOM-1', 'ESP32-S3-WROOM-1-N4', {
        'GND': 'GND', '3V3': '+3V3', 'EN': 'ESP_EN', 'IO0': 'ESP_BOOT',
        'IO1': 'CP_LVL', 'IO2': 'PP_SENSE', 'IO4': 'ANA1', 'IO5': 'ANA2', 'IO6': 'PAWL_IS',
        'IO7': 'VSENSE_12V', 'IO8': 'AIN1_ADC', 'IO9': 'AIN2_ADC', 'IO10': 'ANA3', 'IO47': 'IMU_INT1',
        'IO11': 'EXP_GPIO1', 'IO12': 'EXP_GPIO2', 'IO21': 'LED_STAT2',
        'IO15': 'I2C_SDA', 'IO16': 'I2C_SCL',
        'IO35': 'OPTO_IN1', 'IO36': 'OPTO_IN2', 'IO37': 'OPTO_IN3', 'IO38': 'OPTO_IN4',
        'IO39': 'PAWL_INH', 'IO40': 'LED_STAT1',
        'IO17': 'CAN1_TXD', 'IO18': 'CAN1_RXD',
        'IO41': 'CP_DUTY', 'IO42': 'CP_S2_OPEN', 'IO48': 'PAWL_DRV',
        'TXD0': 'UART_TX', 'RXD0': 'UART_RX', 'USB_D-': 'USB_DM', 'USB_D+': 'USB_DP',
    }, 'RF_Module:ESP32-S3-WROOM-1', nc=['IO3', 'IO45', 'IO46', 'IO13', 'IO14'],
        fields={'LCSC': 'C2913197'}, at=(165.1, 127.0), text='below-left')
    CV(s, 'C10', '22uF 10V X7R', '+3V3', 'GND', (172.72, 66.04), C1206)
    CV(s, 'C11', '100nF', '+3V3', 'GND', (154.94, 66.04))
    s.tap('I2C_SDA', 147.32, 147.32)
    s.tap('I2C_SCL', 147.32, 149.86)

    s.head('Reset / boot (solder-jumper pads)', 76.2, 55.88)
    RV(s, 'R10', '10k', '+3V3', 'ESP_EN', (139.7, 73.66))
    CV(s, 'C12', '1uF', 'ESP_EN', 'GND', (127.0, 86.36))
    put(s, 'JP3', 'Jumper:SolderJumper_2_Open', 'RESET', {'A': 'ESP_EN', 'B': 'GND'},
        'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm', 'A', (106.68, 86.36), 270)
    RV(s, 'R11', '10k', '+3V3', 'ESP_BOOT', (96.52, 96.52))
    put(s, 'JP4', 'Jumper:SolderJumper_2_Open', 'BOOT', {'A': 'ESP_BOOT', 'B': 'GND'},
        'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm', 'A', (83.82, 109.22), 270)

    s.head('I2C pull-ups', 91.44, 152.4)
    RV(s, 'R12', '4.7k', '+3V3', 'I2C_SDA', (114.3, 167.64))
    RV(s, 'R13', '4.7k', '+3V3', 'I2C_SCL', (127.0, 172.72))
    s.tap('I2C_SDA', 101.6, 180.34)
    s.tap('I2C_SCL', 101.6, 185.42)

    s.head('USB-C (data only)', 215.9, 55.88)
    s.add('J1', 'Connector:USB_C_Receptacle_USB2.0_16P', 'TYPE-C-31-M-12',
          {'GND': 'GND', 'VBUS': 'USB_VBUS', 'CC1': 'USB_CC1', 'CC2': 'USB_CC2',
           'D+': 'USB_DP', 'D-': 'USB_DM', 'SHIELD': 'GND'},
          'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12',
          nc=['SBU1', 'SBU2'], at=(254.0, 76.2), rot=270, mirror='y')
    RHr(s, 'R14', '5.1k', 'USB_CC1', 'GND', (243.84, 99.06))
    RHr(s, 'R15', '5.1k', 'USB_CC2', 'GND', (246.38, 106.68))
    put(s, 'U3', 'Power_Protection:USBLC6-2SC6', 'USBLC6-2SC6',
        {'1': 'USB_DM', '6': 'USB_DM', '3': 'USB_DP', '4': 'USB_DP', '5': 'USB_VBUS', '2': 'GND'},
        'Package_TO_SOT_SMD:SOT-23-6', '1', (208.28, 114.3))

    s.head('Debug UART (DNP)', 190.5, 60.96)
    put(s, 'J2', 'Connector_Generic:Conn_01x04', 'UART debug',
        {'1': 'GND', '2': 'UART_TX', '3': 'UART_RX', '4': '+3V3'},
        'Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical', '2', (198.12, 91.44), 90, dnp=True)

    s = b.sheet('CAN', 'can.kicad_sch')
    s.note('CAN1 = native TWAI (vehicle bus), in + out pins on J20 (daisy chain).\n'
           'Rs tied to GND = high-speed mode.  120R terminator on a solder jumper, default OPEN (mid-bus).',
           20, 15)
    s.paper = 'A3'
    s.head('CAN1: native TWAI, vehicle bus', 30.48, 40.64)
    s.add('U4', 'Interface_CAN_LIN:SN65HVD230', 'SN65HVD230',
          {'D': 'CAN1_TXD', 'R': 'CAN1_RXD', 'VCC': '+3V3', 'GND': 'GND', 'Rs': 'GND',
           'CANH': 'CAN1_H', 'CANL': 'CAN1_L'}, 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', nc=['Vref'],
          at=(88.9, 76.2))
    CV(s, 'C13', '100nF', '+3V3', 'GND', (63.5, 50.8))
    put(s, 'D4', 'Power_Protection:NUP2105L', 'NUP2105L', {'1': 'CAN1_H', '2': 'CAN1_L', '3': 'GND'}, SOT23,
        '2', (114.3, 88.9), 0, 'y')
    put(s, 'JP1', 'Jumper:SolderJumper_2_Open', 'CAN1 TERM', {'A': 'CAN1_H', 'B': 'CAN1_TERM'},
        'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm', 'A', (134.62, 76.2), 90)
    RV(s, 'R16', '120R', 'CAN1_TERM', 'CAN1_L', (144.78, 60.96), 'Resistor_SMD:R_1206_3216Metric')
    s.tap('CAN1_H', 157.48, 76.2, (1, 0))
    s.tap('CAN1_L', 157.48, 78.74, (1, 0))

    io_sheet(b)
    motor_sheet(b)
    j1772_sheet(b)
    sensor_sheet(b)
    connector_sheet(b)
    for sh in b.sheets:
        for p in sh.parts:
            if isinstance(p, tuple):
                continue
            if p.value in MPN:
                p.fields.setdefault('MPN', MPN[p.value])
            k = p.value + '|' + p.footprint.split(':')[-1]
            hit = LCSC.get(k) or LCSC.get(p.value)
            if hit and 'JLC' not in p.fields:
                p.fields.setdefault('LCSC', hit['lcsc'])
                p.fields.setdefault('MPN', hit['mfr'])
    return b


def opto_in(s, n, net, rser, x0, y):
    """12V-active input: series R -> opto LED (reverse diode across it) -> GND.
    Collector pulled up to 3V3 = ACTIVE-LOW at the GPIO."""
    s.tap(net, x0, y)
    RH(s, 'R%d' % (100 + n), rser, net, 'OPTO%d_A' % n, (x0 + 7.62, y), 'Resistor_SMD:R_0805_2012Metric')
    put(s, 'D%d' % (100 + n), 'Device:D', '1N4148W', {'K': 'OPTO%d_A' % n, 'A': 'GND'}, 'Diode_SMD:D_SOD-123',
        'K', (x0 + 27.94, y), 270)
    put(s, 'U%d' % (100 + n), 'Isolator:PC817', 'LTV-357T', {'1': 'OPTO%d_A' % n, '2': 'GND',
        '3': 'GND', '4': 'OPTO_IN%d' % n}, 'Package_SO:SO-4_4.4x3.6mm_P2.54mm', '1', (x0 + 38.1, y))
    RV(s, 'R%d' % (110 + n), '10k', '+3V3', 'OPTO_IN%d' % n, (x0 + 68.58, y - 12.7))
    CV(s, 'C%d' % (100 + n), '10nF', 'OPTO_IN%d' % n, 'GND', (x0 + 78.74, y))
    s.tap('OPTO_IN%d' % n, x0 + 88.9, y, (1, 0))


def status_led(s, rref, dref, net, anode, x, tap):
    """Series R from net (top) -> LED -> GND."""
    if tap:
        s.tap(net, x - 7.62, 55.88)
    RV(s, rref, '1k', net, anode, (x, 55.88))
    put(s, dref, 'Device:LED', 'LED green', {'A': anode, 'K': 'GND'}, 'LED_SMD:LED_0603_1608Metric',
        'A', (x, 68.58), 90)


def io_sheet(b):
    s = b.sheet('IO', 'io.kicad_sch')
    s.note('Opto inputs -> native GPIO IO35-38, ACTIVE-LOW (collector pulled up to 3V3).\n'
           'Opto inputs: 12V -> 2.2k (IN1 P_SENSE 4.7k: light tap on a shared sense line) -> LTV-357T.\n'
           'J10 (DNP) expansion: I2C, ANA1-3 (raw ESP32 ADC1, 0-3.1 V), 2 GPIO.',
           20, 15)
    s.paper = 'A3'
    s.head('Opto inputs (12V active)', 30.48, 33.02)
    for n, (net, rr) in enumerate([('IN_P_SENSE', '4.7k'), ('IN_BRAKE', '2.2k'), ('IN_WELD1', '2.2k'),
                                   ('IN_WELD2', '2.2k')], 1):
        opto_in(s, n, net, rr, 45.72, 25.4 + 30.48 * n)
    s.head('Status LEDs', 180.34, 33.02)
    status_led(s, 'R164', 'D121', '+3V3', 'LED_PWR_A', 185.42, False)
    status_led(s, 'R165', 'D122', 'LED_STAT1', 'LED1_A', 223.52, True)
    status_led(s, 'R166', 'D123', 'LED_STAT2', 'LED2_A', 261.62, True)
    s.head('Expansion header (DNP)', 30.48, 167.64)
    s.add('J10', 'Connector_Generic:Conn_01x10', 'EXP', {
        '1': 'GND', '2': '+3V3', '3': 'I2C_SDA', '4': 'I2C_SCL', '5': 'ANA1', '6': 'ANA2',
        '7': 'ANA3', '8': 'EXP_GPIO1', '9': 'EXP_GPIO2', '10': 'GND'},
        'Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical', dnp=True, at=(101.6, 205.74), rot=270)


def half_bridge(s, ref, n, vs, out, inp, inh, isn, at):
    """One BTN8982TA.  1k series on IN/INH (input current up to 150 uA; 10k would
    drop below VIH from 3.3V logic).  SR 5.1k to GND (slew), 220nF on OUT."""
    x, y = at
    s.add(ref, 'Power_Management:BTN8982TA', 'BTN8982TA',
          {'1': 'GND', '2': 'BR%d_IN' % n, '3': 'BR%d_INH' % n, '4': out, '8': out,
           '5': 'BR%d_SR' % n, '6': isn, '7': vs}, at=at)
    s.tap(inh, x - 38.1, y - 12.7)
    RH(s, 'R%d' % (210 + n), '1k', inh, 'BR%d_INH' % n, (x - 30.48, y - 12.7))
    s.tap(inp, x - 38.1, y - 2.54)
    RH(s, 'R%d' % (200 + n), '1k', inp, 'BR%d_IN' % n, (x - 30.48, y - 2.54))
    RV(s, 'R%d' % (220 + n), '5.1k', 'BR%d_SR' % n, 'GND', (x - 15.24, y + 10.16))
    CV(s, 'C%d' % (200 + n), '100nF 50V', vs, 'GND', (x + 45.72, y - 24.13))
    CV(s, 'C%d' % (210 + n), '220nF 50V', out, 'GND', (x + 17.78, y), 'Capacitor_SMD:C_0805_2012Metric')
    s.tap(out, x + 30.48, y, (1, 0))


def is_sense(s, n, raw, adc, x, y):
    """IS -> 1k + 1nF (19.5 mV/A typ per chip at 1k, dkILIS 14k..25k), then 4.7k +
    BAT54S clamp: fault current 4-6.5 mA would put ~6.5 V on 1k.  x, y = IS pin stub end."""
    RV(s, 'R%d' % (230 + n), '1k', raw, 'GND', (x - 12.7, y))
    CV(s, 'C%d' % (220 + n), '1nF', raw, 'GND', (x - 33.02, y))
    RHr(s, 'R%d' % (240 + n), '4.7k', raw, adc, (x - 43.18, y))
    CV(s, 'C%d' % (230 + n), '10nF', adc, 'GND', (x - 63.5, y))
    put(s, 'D%d' % (200 + n), 'Diode:BAT54S', 'BAT54S', {'1': 'GND', '2': '+3V3', '3': adc}, SOT23,
        '3', (x - 86.36, y + 5.08), 0, True)
    s.tap(adc, x - 99.06, y)


def motor_sheet(b):
    s = b.sheet('Motors', 'motors.kicad_sch')
    s.note('Pawl: 1 BTN8982TA used as a\n'
           'high-side switch (single direction; actuator - grounds at the motor).  IN=1 drives OUT to VS.\n'
           'BTN8982 VS abs max 40 V -> SMCJ22A on the motor feed (Vc ~35.5 V).  No reverse protection on the\n'
           'motor feeds: reverse battery conducts through the body diodes -> the EXTERNAL fuse must blow.\n'
           'IS -> 1k sense resistor -> ADC1 (PAWL_IS).\n'
           'Bulk: 220uF 35V on PAWL_12V.  Pawl stall current: TBD (measure).',
           20, 15)
    s.paper = 'A3'
    s.head('Pawl motor: BTN8982TA as a high-side switch', 30.48, 38.1)
    y = 48.26                           # PAWL_12V rail
    s.tap('PAWL_12V', 139.7, y)
    flag(s, '#FLG05', 'PAWL_12V', at=anchor('power:PWR_FLAG', '1', (147.32, y)))
    put(s, 'D211', 'Device:D_TVS', 'SMCJ22A', {'1': 'PAWL_12V', '2': 'GND'}, 'Diode_SMD:D_SMC', '1', (165.1, y), 270)
    put(s, 'C242', 'Device:C_Polarized', '220uF 35V', {'1': 'PAWL_12V', '2': 'GND'},
        'Capacitor_SMD:CP_Elec_8x10.5', '1', (180.34, y))
    half_bridge(s, 'U24', 5, 'PAWL_12V', 'MOT_OUT', 'PAWL_DRV', 'PAWL_INH', 'PAWL_ISRAW', (149.86, 72.39))
    is_sense(s, 5, 'PAWL_ISRAW', 'PAWL_IS', 139.7, 74.93)


def j1772_sheet(b):
    s = b.sheet('J1772', 'j1772.kicad_sch')
    s.note('Car-side pilot.  CP -> diode -> 2.74k to GND (state B, always) ; 1.3k via K1 to GND (state C).\n'
           'K1 = CPC1117N, form-B (CLOSED when unpowered): a dead board presents state C, so the EVSE delivers\n'
           'AC and Pin-B wakes the truck.  CP_S2_OPEN high = LED on = K1 open = state B (pause / stop).\n'
           'CP read: 200k / 45.3k to 3V3 / 57.6k to GND maps CP -12..+12 V to 0.3..3.0 V (CP 0 V = 1.65 V),\n'
           'load on CP >= 200k.  TLV3201 vs 1.65 V, 1M hysteresis (~0.7 V at CP) -> CP_DUTY (MCPWM capture).\n'
           'CP_SENSE -> 1k/1nF -> CP_LVL -> ESP32 ADC1 IO1: +12 / +9 / +6 V = 3.0 / 2.66 / 2.33 V (state A / B / C).\n'
           'PP: this board owns PP (Zombie interface=CPC, plug state in 0x357).  4.7k pull-up to 3V3:\n'
           'open 3.3 V (ADC full scale), plug 150R ~0.10 V, latch pressed (150R+330R) ~0.31 V -> ESP32 ADC1 IO2.',
           20, 15)
    s.paper = 'A3'
    s.head('Pilot: vehicle-side state resistors', 30.48, 43.18)
    s.tap('CP', 38.1, 57.15)
    s.add('D300', 'Device:D_TVS', 'SMAJ15CA', {'1': 'CP', '2': 'GND'}, 'Diode_SMD:D_SMA',
          at=(50.8, 63.5), rot=270)
    s.add('D301', 'Device:D', '1N4148W', {'A': 'CP', 'K': 'CP_D'}, 'Diode_SMD:D_SOD-123',
          at=(66.04, 57.15), rot=180)
    R(s, 'R300', '2.74k 1%', 'CP_D', 'GND', 'Resistor_SMD:R_0805_2012Metric', at=(78.74, 63.5))
    R(s, 'R301', '1.3k 1%', 'CP_D', 'CP_S2', 'Resistor_SMD:R_0805_2012Metric', at=(91.44, 63.5))
    s.add('K1', 'Relay_SolidState:CPC1117N', 'CPC1117N', {'1': 'K1_LED', '2': 'GND', '3': 'CP_S2', '4': 'GND'},
          at=(116.84, 71.12), rot=180)
    R(s, 'R302', '330R', 'CP_S2_OPEN', 'K1_LED', at=(142.24, 78.74), rot=270)
    R(s, 'R310', '0R', 'CP_GND', 'GND', 'Resistor_SMD:R_0805_2012Metric', at=(160.02, 63.5),
      fields={'Note': 'CP return to the inlet PE'})

    s.head('CP read', 30.48, 91.44)
    R(s, 'R303', '200k', 'CP', 'CP_SENSE', at=(62.23, 106.68), rot=90)
    R(s, 'R304', '45.3k', '+3V3', 'CP_SENSE', at=(73.66, 100.33))
    R(s, 'R305', '57.6k', 'CP_SENSE', 'GND', at=(78.74, 113.03))
    C(s, 'C300', '100pF', 'CP_SENSE', 'GND', at=(91.44, 113.03))
    R(s, 'R309', '1k', 'CP_SENSE', 'CP_LVL', at=(104.14, 113.03))
    C(s, 'C303', '1nF', 'CP_LVL', 'GND', at=(104.14, 133.35))
    s.tap('CP_LVL', 71.12, 124.46)
    s.add('U30', 'PCM_Analog_Comparator_AKL:TLV3201AIDBV', 'TLV3201AIDBV',
          {'1': 'CP_DUTY', '2': 'GND', '3': 'CP_SENSE', '4': 'CP_REF', '5': '+3V3'}, at=(129.54, 109.22))
    R(s, 'R308', '1M', 'CP_DUTY', 'CP_SENSE', at=(127.0, 88.9), rot=270)
    s.tap('CP_DUTY', 151.13, 109.22, (1, 0))
    R(s, 'R306', '10k', '+3V3', 'CP_REF', at=(124.46, 130.81))
    R(s, 'R307', '10k', 'CP_REF', 'GND', at=(129.54, 143.51))
    C(s, 'C301', '100nF', 'CP_REF', 'GND', at=(142.24, 143.51))
    C(s, 'C302', '100nF', '+3V3', 'GND', at=(172.72, 109.22))

    s.head('PP read', 30.48, 160.02)
    s.tap('PP', 38.1, 175.26)
    s.add('D302', 'Device:D_TVS', 'SMAJ15CA', {'1': 'PP', '2': 'GND'}, 'Diode_SMD:D_SMA',
          at=(50.8, 181.61), rot=270)
    R(s, 'R311', '4.7k', '+3V3', 'PP', at=(60.96, 168.91))
    R(s, 'R312', '1k', 'PP', 'PP_SENSE', at=(73.66, 175.26), rot=90)
    C(s, 'C304', '10nF', 'PP_SENSE', 'GND', at=(86.36, 181.61))
    s.tap('PP_SENSE', 96.52, 175.26, (1, 0))


def ain(s, n, x0, y):
    """12V-tolerant analog input: 100k / 22k (15 V -> 2.7 V), 100nF, BAT54S clamp."""
    s.tap('AIN%d' % n, x0, y)
    RH(s, 'R%d' % (410 + n), '100k', 'AIN%d' % n, 'AIN%d_ADC' % n, (x0 + 7.62, y))
    RV(s, 'R%d' % (420 + n), '22k', 'AIN%d_ADC' % n, 'GND', (x0 + 27.94, y))
    CV(s, 'C%d' % (410 + n), '100nF', 'AIN%d_ADC' % n, 'GND', (x0 + 38.1, y))
    put(s, 'D%d' % (410 + n), 'Diode:BAT54S', 'BAT54S', {'1': 'GND', '2': '+3V3', '3': 'AIN%d_ADC' % n}, SOT23,
        '3', (x0 + 53.34, y + 5.08), 0, True)
    s.tap('AIN%d_ADC' % n, x0 + 71.12, y, (1, 0))


def sensor_sheet(b):
    s = b.sheet('Sensors', 'sensors.kicad_sch')
    s.note('I2C bus (IO15 SDA / IO16 SCL, 4.7k pull-ups on sheet MCU): 0x6A LSM6DSO (SA0 = GND).\n'
           'LSM6DSO: I2C mode (CS = 3V3); aux SPI pins unused (SDx / SCx to GND).  INT1 -> IO47.\n'
           'Mount the board square to the vehicle axes.\n'
           'AIN1 / AIN2 (J20): 0-15 V -> 0-2.7 V into ESP32 ADC1 (IO8 / IO9), 122k input load.',
           20, 15)
    s.paper = 'A3'
    s.head('LSM6DSO IMU', 30.48, 40.64)
    s.add('U41', 'PCM_SparkFun-Sensor:LSM6DSOX', 'LSM6DSOX',
          {'VDD': '+3V3', 'VDDIO': '+3V3', 'GND': 'GND', 'SDA': 'I2C_SDA', 'SCL': 'I2C_SCL',
           '~{CS}': '+3V3', 'SDO/SA0': 'GND', 'SDx': 'GND', 'SCx': 'GND', 'INT1': 'IMU_INT1'},
          nc=['INT2', 'OCS_Aux', 'SDO_Aux'], at=(101.6, 76.2))
    CV(s, 'C401', '100nF', '+3V3', 'GND', (50.8, 55.88))
    CV(s, 'C402', '100nF', '+3V3', 'GND', (66.04, 55.88))
    s.head('Analog inputs (12V-tolerant)', 30.48, 106.68)
    ain(s, 1, 45.72, 124.46)
    ain(s, 2, 45.72, 154.94)


def connector_sheet(b):
    s = b.sheet('Connector', 'connector.kicad_sch')
    s.note('Main connector: Aptiv/FCI HCCPHPE24BKA90F (24-way 90 deg header, key A), mates 211PC249S0005.\n'
           'Columns 1 and 8 (A1-C1, A8-C8) = large high-current cavities.  Footprint: lib/ (gen/make_lib.py).\n'
           'Pawl feed and lead doubled on the large pins.  CAN1 in (A3/A4) and out (A5/A6) joined on the board.\n'
           'Pins marked NC: spare.',
           20, 15)
    s.paper = 'A3'
    s.head('Main connector', 30.48, 58.42)
    pins = {
        'A1': 'PAWL_12V', 'B1': 'PAWL_12V', 'C1': 'GND',
        'A8': 'MOT_OUT', 'B8': 'MOT_OUT', 'C8': 'GND',
        'A2': 'VIN_12V', 'A3': 'CAN1_H', 'A4': 'CAN1_L', 'A5': 'CAN1_H', 'A6': 'CAN1_L', 'A7': 'GND',
        'B2': 'IN_P_SENSE', 'B3': 'IN_BRAKE', 'B4': 'IN_WELD1', 'B5': 'IN_WELD2', 'B6': 'AIN1', 'B7': 'AIN2',
        'C2': 'CP', 'C3': 'CP_GND', 'C4': 'PP',
    }
    allp = ['%s%d' % (r, c) for r in 'ABC' for c in range(1, 9)]
    cx, cy = 139.7, 114.3
    s.add('J20', 'chassis_ecu:FCI_HCCPHPE24BKA90F', 'HCCPHPE24BKA90F', pins,
          'chassis_ecu:FCI_HCCPHPE24BKA90F', nc=[p for p in allp if p not in pins],
          fields={'JLC': 'not assembled - hand-solder (through-hole)'}, at=(cx, cy))
    # every pin leaves the sheet: one label per pin
    for k, (pin, net) in enumerate(sorted(pins.items(), key=lambda kv: allp.index(kv[0]))):
        if net != 'GND':
            s.tap(net, cx - 7.62, cy - 27.94 + 2.54 * allp.index(pin))
    s.head('Case mounting holes', 190.5, 58.42)
    s.note('3.2 mm holes: fit M3 / ST2.9 / smaller screws; the case bosses are 2.5 mm.', 190.5, 66.04)
    for i in range(1, 5):
        s.add('H%d' % i, 'Mechanical:MountingHole', 'MountingHole', {}, 'MountingHole:MountingHole_3.2mm_M3',
              fields={'JLC': 'not a part'}, at=(172.72 + 25.4 * i, 81.28))
