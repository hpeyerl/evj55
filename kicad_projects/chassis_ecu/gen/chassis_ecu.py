"""chassis_ecu schematic definition.  Run build.py to regenerate."""
from schgen import Board

R0603 = 'Resistor_SMD:R_0603_1608Metric'
C0603 = 'Capacitor_SMD:C_0603_1608Metric'
C1206 = 'Capacitor_SMD:C_1206_3216Metric'
C1210 = 'Capacitor_SMD:C_1210_3225Metric'
SOT23 = 'Package_TO_SOT_SMD:SOT-23'
BTN = 'Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A'


def R(s, ref, val, a, b, fp=R0603, **k):
    return s.add(ref, 'Device:R', val, {'1': a, '2': b}, fp, **k)


def C(s, ref, val, a, b, fp=C0603, **k):
    return s.add(ref, 'Device:C', val, {'1': a, '2': b}, fp, **k)


def flag(s, ref, net):
    return s.add(ref, 'power:PWR_FLAG', 'PWR_FLAG', {'1': net})


# Manufacturer part numbers by Value.  LCSC numbers are filled only once verified
# against the JLC parts index; JLCPCB's BOM matcher can also resolve from MPN.
MPN = {
    'LM5164DDAR': 'LM5164DDAR', 'FDD4685': 'FDD4685', 'SMAJ33CA': 'SMAJ33CA', 'BZT52C15': 'BZT52C15',
    'BAT54S': 'BAT54S', 'ESP32-S3-WROOM-1-N8': 'ESP32-S3-WROOM-1-N8', 'USBLC6-2SC6': 'USBLC6-2SC6',
    'SN65HVD230': 'SN65HVD230DR', 'NUP2105L': 'NUP2105LT1G', 'MCP2518FD': 'MCP2518FDT-E/QBB',
    '40MHz 12pF': '7B040000M01', 'MCP23017-E/SS': 'MCP23017-E/SS', 'LTV-357T': 'LTV-357T',
    '1N4148W': '1N4148W', 'DMN6075S': 'DMN6075S-7', 'B5819W': 'B5819W', '2N7002': '2N7002',
    'AO3401A': 'AO3401A', 'BTN8982TA': 'BTN8982TA', 'SMCJ22A': 'SMCJ22A', 'SMAJ15CA': 'SMAJ15CA',
    'CPC1117N': 'CPC1117NTR', 'TLV3201AIDBV': 'TLV3201AIDBVR', 'ADS1115IDGS': 'ADS1115IDGSR',
    'LSM6DSOX': 'LSM6DSOXTR', 'INA226AIDGSR': 'INA226AIDGSR', 'SMAJ24CA': 'SMAJ24CA',
    'BSS84': 'LBSS84LT1G', 'MCP23017-E/SO': 'MCP23017-E/SO', 'TYPE-C-31-M-12': 'TYPE-C-31-M-12',
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
    s.row('Input protection: fuse, TVS, reverse-polarity P-FET')
    s.add('F1', 'Device:Fuse', '1A 63V', {'1': 'VIN_12V', '2': 'VIN_F'}, 'Fuse:Fuse_1206_3216Metric')
    s.add('D1', 'Device:D_TVS', 'SMAJ24CA', {'1': 'VIN_F', '2': 'GND'}, 'Diode_SMD:D_SMA')
    s.add('Q1', 'PCM_Transistor_MOSFET_AKL:FDD4685', 'FDD4685',
          {'G': 'QREV_G', 'D': 'VIN_F', 'S': '+12V_LOGIC'}, 'Package_TO_SOT_SMD:TO-252-2')
    R(s, 'R1', '10k', 'QREV_G', 'GND')
    s.add('D2', 'Device:D_Zener', 'BZT52C15', {'K': '+12V_LOGIC', 'A': 'QREV_G'}, 'Diode_SMD:D_SOD-123')
    s.row('Buck input capacitors')
    s.add('C1', 'Device:C_Polarized', '47uF 63V', {'1': '+12V_LOGIC', '2': 'GND'},
          'Capacitor_SMD:CP_Elec_6.3x7.7')
    C(s, 'C2', '2.2uF 100V X7R', '+12V_LOGIC', 'GND', C1210)
    C(s, 'C3', '2.2uF 100V X7R', '+12V_LOGIC', 'GND', C1210)
    s.row('LM5164 buck, 3.3V')
    s.add('U1', 'Regulator_Switching:LM5164DDA', 'LM5164DDAR',
          {'GND': 'GND', 'EP': 'GND', 'VIN': '+12V_LOGIC', 'EN/UVLO': 'BUCK_EN', 'RON': 'BUCK_RON',
           'FB': 'BUCK_FB', 'BST': 'BUCK_BST', 'SW': 'BUCK_SW'}, nc=['PGOOD'])
    R(s, 'R2', '301k', '+12V_LOGIC', 'BUCK_EN')
    R(s, 'R3', '100k', 'BUCK_EN', 'GND')
    R(s, 'R4', '27.4k', 'BUCK_RON', 'GND')
    C(s, 'C4', '2.2nF 50V X7R', 'BUCK_BST', 'BUCK_SW')
    s.row('Inductor, ripple injection, feedback, output caps')
    s.add('L1', 'Device:L', '22uH 2.2A', {'1': 'BUCK_SW', '2': '+3V3'},
          'Inductor_SMD:L_Changjiang_FNR6045S')
    R(s, 'R5', '124k', 'BUCK_SW', 'BUCK_RIP')
    C(s, 'C5', '3.3nF', 'BUCK_RIP', '+3V3')
    C(s, 'C6', '100pF', 'BUCK_RIP', 'BUCK_FB')
    R(s, 'R6', '174k', '+3V3', 'BUCK_FB')
    R(s, 'R7', '100k', 'BUCK_FB', 'GND')
    C(s, 'C7', '22uF 10V X7R', '+3V3', 'GND', C1206)
    C(s, 'C8', '22uF 10V X7R', '+3V3', 'GND', C1206)
    s.row('12V sense for the ADC')
    R(s, 'R8', '100k', '+12V_LOGIC', 'VSENSE_12V')
    R(s, 'R9', '10k', 'VSENSE_12V', 'GND')
    C(s, 'C9', '100nF', 'VSENSE_12V', 'GND')
    s.add('D3', 'Diode:BAT54S', 'BAT54S', {'1': 'GND', '2': '+3V3', '3': 'VSENSE_12V'}, SOT23)
    s.row('Power flags')
    flag(s, '#FLG01', '+12V_LOGIC')
    flag(s, '#FLG02', '+3V3')
    flag(s, '#FLG03', 'GND')

    # --- MCU --------------------------------------------------------------------
    s = b.sheet('MCU', 'mcu.kicad_sch')
    s.note('ESP32-S3-WROOM-1-N8 (plastic case, PCB antenna) or -1U-N8 (metal case, u.FL).\n'
           'Same pad pattern; the -1 footprint outline covers both.  Keep the antenna end clear of copper.\n'
           'Strapping: IO0 = BOOT (button), IO3 / IO45 / IO46 left unconnected.\n'
           'USB: data only (native USB-Serial-JTAG).  VBUS feeds only the ESD part; the board\n'
           'runs from 12V, so bench programming needs the 12V supply.\n'
           'ADC1 (IO1-10) for analog; ADC2 is unusable with WiFi.  No spare GPIO; ANA1/ANA2 (IO4/IO5) go to test pads.',
           20, 15)
    s.row('ESP32-S3 module')
    s.add('U2', 'RF_Module:ESP32-S3-WROOM-1', 'ESP32-S3-WROOM-1-N8', {
        'GND': 'GND', '3V3': '+3V3', 'EN': 'ESP_EN', 'IO0': 'ESP_BOOT',
        'IO1': 'HB_LA_IS', 'IO8': 'HB_LB_IS', 'IO2': 'HB_RA_IS', 'IO9': 'HB_RB_IS', 'IO4': 'ANA1', 'IO5': 'ANA2', 'IO6': 'PAWL_IS',
        'IO7': 'VSENSE_12V', 'IO47': 'IMU_INT1',
        'IO10': 'IOX_INT', 'IO11': 'SPI_MOSI', 'IO12': 'SPI_SCK', 'IO13': 'SPI_MISO',
        'IO14': 'CAN2_CS', 'IO21': 'CAN2_INT', 'IO15': 'I2C_SDA', 'IO16': 'I2C_SCL',
        'IO17': 'CAN1_TXD', 'IO18': 'CAN1_RXD',
        'IO35': 'HB_L_IN1', 'IO36': 'HB_L_IN2', 'IO37': 'HB_R_IN1', 'IO38': 'HB_R_IN2',
        'IO39': 'HB_L_INH', 'IO40': 'HB_R_INH',
        'IO41': 'CP_DUTY', 'IO42': 'CP_S2_OPEN', 'IO48': 'PAWL_DRV',
        'TXD0': 'UART_TX', 'RXD0': 'UART_RX', 'USB_D-': 'USB_DM', 'USB_D+': 'USB_DP',
    }, 'RF_Module:ESP32-S3-WROOM-1', nc=['IO3', 'IO45', 'IO46'],
        fields={'JLC': 'not assembled - hand-solder (N8, or N4 = LCSC C2913197)'})
    s.row('Decoupling, reset, boot, I2C pull-ups')
    C(s, 'C10', '22uF 10V X7R', '+3V3', 'GND', C1206)
    C(s, 'C11', '100nF', '+3V3', 'GND')
    R(s, 'R10', '10k', '+3V3', 'ESP_EN')
    C(s, 'C12', '1uF', 'ESP_EN', 'GND')
    s.add('SW1', 'Switch:SW_Push', 'RESET', {'1': 'ESP_EN', '2': 'GND'}, BTN)
    R(s, 'R11', '10k', '+3V3', 'ESP_BOOT')
    s.add('SW2', 'Switch:SW_Push', 'BOOT', {'1': 'ESP_BOOT', '2': 'GND'}, BTN)
    R(s, 'R12', '4.7k', '+3V3', 'I2C_SDA')
    R(s, 'R13', '4.7k', '+3V3', 'I2C_SCL')
    s.row('USB-C (data only) and debug UART')
    s.add('J1', 'Connector:USB_C_Receptacle_USB2.0_16P', 'TYPE-C-31-M-12',
          {'GND': 'GND', 'VBUS': 'USB_VBUS', 'CC1': 'USB_CC1', 'CC2': 'USB_CC2',
           'D+': 'USB_DP', 'D-': 'USB_DM', 'SHIELD': 'GND'},
          'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12',
          nc=['SBU1', 'SBU2'])
    R(s, 'R14', '5.1k', 'USB_CC1', 'GND')
    R(s, 'R15', '5.1k', 'USB_CC2', 'GND')
    s.add('U3', 'Power_Protection:USBLC6-2SC6', 'USBLC6-2SC6',
          {'1': 'USB_DM', '6': 'USB_DM', '3': 'USB_DP', '4': 'USB_DP', '5': 'USB_VBUS', '2': 'GND'},
          'Package_TO_SOT_SMD:SOT-23-6')
    s.add('J2', 'Connector_Generic:Conn_01x04', 'UART debug',
          {'1': 'GND', '2': 'UART_TX', '3': 'UART_RX', '4': '+3V3'},
          'Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical', dnp=True)

    # --- CAN --------------------------------------------------------------------
    s = b.sheet('CAN', 'can.kicad_sch')
    s.note('CAN1 = native TWAI (vehicle bus).  CAN2 = MCP2518FD on SPI (CAN-FD capable).\n'
           'Rs tied to GND = high-speed mode.  120R terminators on solder jumpers, default OPEN (mid-bus).\n'
           'Y1: 40 MHz, CL 12 pF (7B040000M01) -> C16/C17 = 2 x (12 - ~3 pF stray) = 18 pF.',
           20, 15)
    s.row('CAN1: native TWAI, vehicle bus')
    s.add('U4', 'Interface_CAN_LIN:SN65HVD230', 'SN65HVD230',
          {'D': 'CAN1_TXD', 'R': 'CAN1_RXD', 'VCC': '+3V3', 'GND': 'GND', 'Rs': 'GND',
           'CANH': 'CAN1_H', 'CANL': 'CAN1_L'}, 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', nc=['Vref'])
    C(s, 'C13', '100nF', '+3V3', 'GND')
    s.add('D4', 'Power_Protection:NUP2105L', 'NUP2105L', {'1': 'CAN1_H', '2': 'CAN1_L', '3': 'GND'}, SOT23)
    s.add('JP1', 'Jumper:SolderJumper_2_Open', 'CAN1 TERM', {'A': 'CAN1_H', 'B': 'CAN1_TERM'},
          'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm')
    R(s, 'R16', '120R', 'CAN1_TERM', 'CAN1_L', 'Resistor_SMD:R_1206_3216Metric')

    s.row('CAN2: MCP2518FD on SPI')
    s.add('U5', 'Interface_CAN_LIN:MCP2518FD-xQBB', 'MCP2518FD',
          {'VDD': '+3V3', 'VSS': 'GND', 'OSC1': 'CAN2_OSC1', 'OSC2': 'CAN2_OSC2',
           '~{INT}': 'CAN2_INT', 'TXCAN': 'CAN2_TXD', 'RXCAN': 'CAN2_RXD',
           '~{CS}': 'CAN2_CS', 'SCK': 'SPI_SCK', 'SDI': 'SPI_MOSI', 'SDO': 'SPI_MISO'},
          'Package_DFN_QFN:DFN-14-1EP_3x4.5mm_P0.65mm_EP1.65x4.25mm',
          nc=['CLKO/SOF', '~{INT0}/GPIO0/XSTBY', '~{INT1}/GPIO1'])
    C(s, 'C14', '100nF', '+3V3', 'GND')
    C(s, 'C15', '1uF', '+3V3', 'GND')
    R(s, 'R17', '10k', '+3V3', 'CAN2_INT')
    R(s, 'R18', '10k', '+3V3', 'CAN2_CS')
    s.add('Y1', 'Device:Crystal_GND24', '40MHz 12pF', {'1': 'CAN2_OSC1', '3': 'CAN2_OSC2', 'G': 'GND'},
          'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm')
    C(s, 'C16', '18pF', 'CAN2_OSC1', 'GND')
    C(s, 'C17', '18pF', 'CAN2_OSC2', 'GND')
    s.row('CAN2 transceiver')
    s.add('U6', 'Interface_CAN_LIN:SN65HVD230', 'SN65HVD230',
          {'D': 'CAN2_TXD', 'R': 'CAN2_RXD', 'VCC': '+3V3', 'GND': 'GND', 'Rs': 'GND',
           'CANH': 'CAN2_H', 'CANL': 'CAN2_L'}, 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', nc=['Vref'])
    C(s, 'C18', '100nF', '+3V3', 'GND')
    s.add('D5', 'Power_Protection:NUP2105L', 'NUP2105L', {'1': 'CAN2_H', '2': 'CAN2_L', '3': 'GND'}, SOT23)
    s.add('JP2', 'Jumper:SolderJumper_2_Open', 'CAN2 TERM', {'A': 'CAN2_H', 'B': 'CAN2_TERM'},
          'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm')
    R(s, 'R19', '120R', 'CAN2_TERM', 'CAN2_L', 'Resistor_SMD:R_1206_3216Metric')
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


def opto_in(s, n, net, rser):
    """12V-active input: series R -> opto LED (reverse diode across it) -> GND.
    Collector pulled up to 3V3 = ACTIVE-LOW at the expander."""
    s.add('R%d' % (100 + n), 'Device:R', rser, {'1': net, '2': 'OPTO%d_A' % n},
          'Resistor_SMD:R_0805_2012Metric')
    s.add('D%d' % (100 + n), 'Device:D', '1N4148W', {'K': 'OPTO%d_A' % n, 'A': 'GND'}, 'Diode_SMD:D_SOD-123')
    s.add('U%d' % (100 + n), 'Isolator:PC817', 'LTV-357T', {'1': 'OPTO%d_A' % n, '2': 'GND',
          '3': 'GND', '4': 'IOX_IN%d' % n}, 'Package_SO:SO-4_4.4x3.6mm_P2.54mm')
    R(s, 'R%d' % (110 + n), '10k', '+3V3', 'IOX_IN%d' % n)
    C(s, 'C%d' % (100 + n), '10nF', 'IOX_IN%d' % n, 'GND')


def lowside_out(s, n):
    """Light low-side output (small relay / LED / lamp), flyback to +12V_LOGIC."""
    R(s, 'R%d' % (120 + n), '100R', 'IOX_OUT%d' % n, 'OUT%d_G' % n)
    R(s, 'R%d' % (130 + n), '100k', 'OUT%d_G' % n, 'GND')
    s.add('Q%d' % (100 + n), 'Transistor_FET:DMN6075S', 'DMN6075S',
          {'G': 'OUT%d_G' % n, 'S': 'GND', 'D': 'OUT%d' % n})
    s.add('D%d' % (110 + n), 'Device:D_Schottky', 'B5819W', {'K': '+12V_LOGIC', 'A': 'OUT%d' % n},
          'Diode_SMD:D_SOD-123')


def highside_led(s, n, ctl, out):
    """12V high-side drive for an EPB button LED (P-FET, N-FET level shift)."""
    R(s, 'R%d' % (140 + n), '1k', ctl, 'HSL%d_G' % n)
    R(s, 'R%d' % (145 + n), '100k', 'HSL%d_G' % n, 'GND')
    s.add('Q%d' % (110 + n), 'Transistor_FET:2N7002', '2N7002',
          {'G': 'HSL%d_G' % n, 'S': 'GND', 'D': 'HSL%d_PG' % n})
    R(s, 'R%d' % (150 + n), '10k', '+12V_LOGIC', 'HSL%d_PG' % n)
    s.add('Q%d' % (115 + n), 'Transistor_FET:BSS84', 'BSS84',
          {'G': 'HSL%d_PG' % n, 'S': '+12V_LOGIC', 'D': 'HSL%d_D' % n})
    R(s, 'R%d' % (155 + n), '0R', 'HSL%d_D' % n, out, 'Resistor_SMD:R_0805_2012Metric',
      fields={'Note': 'LED series R if the button LED has none'})


def io_sheet(b):
    s = b.sheet('IO', 'io.kicad_sch')
    s.paper = 'A1'
    s.note('MCP23017 at 0x20 (A2..A0 = GND).  GPA7 / GPB7 are OUTPUT-only on current silicon -> status LEDs.\n'
           'GPA0-5 = opto inputs (ACTIVE-LOW), GPA6 = EPB button, GPB0-3 = light outputs, GPB4/5 = EPB LEDs,\n'
           'GPB6 = PAWL_INH.  INTA -> IOX_INT (configure open-drain, mirrored).\n'
           'Opto inputs: 12V -> 2.2k (IN1 P_SENSE 4.7k: light tap on a shared sense line) -> LTV-357T.\n'
           'Light outputs: DMN6075S 60V low-side, B5819W flyback to +12V_LOGIC.\n'
           'EPB LEDs: high-side 12V (BSS84 50V +-20V Vgs, + 2N7002).  The HAT reads the same lines (EPB_GRN / EPB_RED).',
           20, 15)
    s.row('MCP23017 I/O expander')
    s.add('U10', 'Interface_Expansion:MCP23017x-x-SO', 'MCP23017-E/SO', {
        'V_{DD}': '+3V3', 'V_{SS}': 'GND', 'SCK': 'I2C_SCL', 'SDA': 'I2C_SDA',
        'A0': 'GND', 'A1': 'GND', 'A2': 'GND', '~{RESET}': 'IOX_RST', 'INTA': 'IOX_INT',
        'GPA0': 'IOX_IN1', 'GPA1': 'IOX_IN2', 'GPA2': 'IOX_IN3', 'GPA3': 'IOX_IN4',
        'GPA4': 'IOX_IN5', 'GPA5': 'IOX_IN6', 'GPA6': 'EPB_BTN_IN', 'GPA7': 'LED_STAT1',
        'GPB0': 'IOX_OUT1', 'GPB1': 'IOX_OUT2', 'GPB2': 'IOX_OUT3', 'GPB3': 'IOX_OUT4',
        'GPB4': 'EPB_LEDG_CTL', 'GPB5': 'EPB_LEDR_CTL', 'GPB6': 'PAWL_INH', 'GPB7': 'LED_STAT2',
    }, 'Package_SO:SOIC-28W_7.5x17.9mm_P1.27mm', nc=['INTB'])
    C(s, 'C110', '100nF', '+3V3', 'GND')
    R(s, 'R160', '10k', '+3V3', 'IOX_RST')
    R(s, 'R161', '10k', '+3V3', 'IOX_INT')
    s.row('Opto inputs (12V active)')
    for n, (net, rr) in enumerate([('IN_P_SENSE', '4.7k'), ('IN_BRAKE', '2.2k'), ('IN_WELD1', '2.2k'),
                                   ('IN_WELD2', '2.2k'), ('IN5', '2.2k'), ('IN6', '2.2k')], 1):
        opto_in(s, n, net, rr)
    s.row('EPB button input (to GND, normally open)')
    R(s, 'R162', '4.7k', '+3V3', 'EPB_BTN_IN')
    R(s, 'R163', '1k', 'EPB_BTN', 'EPB_BTN_IN')
    C(s, 'C111', '100nF', 'EPB_BTN_IN', 'GND')
    s.add('D120', 'Diode:BAT54S', 'BAT54S', {'1': 'GND', '2': '+3V3', '3': 'EPB_BTN_IN'}, SOT23)
    s.row('Light low-side outputs')
    for n in range(1, 5):
        lowside_out(s, n)
    s.row('EPB button LEDs (12V high-side)')
    highside_led(s, 1, 'EPB_LEDG_CTL', 'EPB_LED_G')
    highside_led(s, 2, 'EPB_LEDR_CTL', 'EPB_LED_R')
    s.row('Status LEDs')
    R(s, 'R164', '1k', '+3V3', 'LED_PWR_A')
    s.add('D121', 'Device:LED', 'LED green', {'A': 'LED_PWR_A', 'K': 'GND'}, 'LED_SMD:LED_0603_1608Metric')
    R(s, 'R165', '1k', 'LED_STAT1', 'LED1_A')
    s.add('D122', 'Device:LED', 'LED green', {'A': 'LED1_A', 'K': 'GND'}, 'LED_SMD:LED_0603_1608Metric')
    R(s, 'R166', '1k', 'LED_STAT2', 'LED2_A')
    s.add('D123', 'Device:LED', 'LED green', {'A': 'LED2_A', 'K': 'GND'}, 'LED_SMD:LED_0603_1608Metric')
    s.row('Expansion header (DNP): spare I/O not on the main connector')
    s.add('J10', 'Connector_Generic:Conn_01x10', 'EXP', {
        '1': 'GND', '2': '+3V3', '3': 'I2C_SDA', '4': 'I2C_SCL', '5': 'IN5', '6': 'IN6',
        '7': 'OUT1', '8': 'OUT2', '9': 'OUT3', '10': 'OUT4'},
        'Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical', dnp=True)


def half_bridge(s, ref, n, vs, out, inp, inh, isn):
    """One BTN8982TA.  1k series on IN/INH (input current up to 150 uA; 10k would
    drop below VIH from 3.3V logic).  SR 5.1k to GND (slew), 220nF on OUT."""
    s.add(ref, 'Power_Management:BTN8982TA', 'BTN8982TA',
          {'1': 'GND', '2': 'BR%d_IN' % n, '3': 'BR%d_INH' % n, '4': out, '8': out,
           '5': 'BR%d_SR' % n, '6': isn, '7': vs})
    R(s, 'R%d' % (200 + n), '1k', inp, 'BR%d_IN' % n)
    R(s, 'R%d' % (210 + n), '1k', inh, 'BR%d_INH' % n)
    R(s, 'R%d' % (220 + n), '5.1k', 'BR%d_SR' % n, 'GND')
    C(s, 'C%d' % (200 + n), '100nF 50V', vs, 'GND')
    C(s, 'C%d' % (210 + n), '220nF 50V', out, 'GND', 'Capacitor_SMD:C_0805_2012Metric')


def is_sense(s, n, raw, adc):
    """IS -> 1k + 1nF (19.5 mV/A typ per chip at 1k, dkILIS 14k..25k), then 4.7k +
    BAT54S clamp: fault current 4-6.5 mA would put ~6.5 V on 1k."""
    R(s, 'R%d' % (230 + n), '1k', raw, 'GND')
    C(s, 'C%d' % (220 + n), '1nF', raw, 'GND')
    R(s, 'R%d' % (240 + n), '4.7k', raw, adc)
    C(s, 'C%d' % (230 + n), '10nF', adc, 'GND')
    s.add('D%d' % (200 + n), 'Diode:BAT54S', 'BAT54S', {'1': 'GND', '2': '+3V3', '3': adc}, SOT23)


def motor_sheet(b):
    s = b.sheet('Motors', 'motors.kicad_sch')
    s.note('EPB: 2 H-bridges (2x BTN8982TA each), left + right caliper.  Pawl: 1 BTN8982TA used as a\n'
           'high-side switch (single direction; actuator - grounds at the motor).  IN=1 drives OUT to VS.\n'
           'BTN8982 VS abs max 40 V -> SMCJ22A on each motor feed (Vc ~35.5 V).  No reverse protection on the\n'
           'motor feeds: reverse battery conducts through the body diodes -> the EXTERNAL fuse must blow.\n'
           'Each half-bridge IS has its own 1k sense resistor and ADC1 pin (per-side, per-direction current).\n'
           'INA226 measures total EPB supply current on a 2 mOhm Kelvin shunt (sheet Sensors).\n'
           'Bulk: 2x 470uF 35V on EPB_VS, 220uF 35V on PAWL_12V.  Caliper / pawl stall current: TBD (measure).',
           20, 15)
    s.row('EPB supply: TVS, current shunt, bulk')
    s.add('D210', 'Device:D_TVS', 'SMCJ22A', {'1': 'EPB_12V', '2': 'GND'}, 'Diode_SMD:D_SMC')
    s.add('R250', 'Device:R', '2mR 3W', {'1': 'EPB_12V', '2': 'EPB_VS'}, 'Resistor_SMD:R_2512_6332Metric',
          fields={'Note': 'Kelvin: route INA226 sense traces from the inner pad edges'})
    s.add('C240', 'Device:C_Polarized', '470uF 35V', {'1': 'EPB_VS', '2': 'GND'}, 'Capacitor_SMD:CP_Elec_10x10')
    s.add('C241', 'Device:C_Polarized', '470uF 35V', {'1': 'EPB_VS', '2': 'GND'}, 'Capacitor_SMD:CP_Elec_10x10')
    s.row('Left caliper H-bridge')
    half_bridge(s, 'U20', 1, 'EPB_VS', 'CAL_L_A', 'HB_L_IN1', 'HB_L_INH', 'HB_LA_ISRAW')
    half_bridge(s, 'U21', 2, 'EPB_VS', 'CAL_L_B', 'HB_L_IN2', 'HB_L_INH', 'HB_LB_ISRAW')
    is_sense(s, 1, 'HB_LA_ISRAW', 'HB_LA_IS')
    is_sense(s, 2, 'HB_LB_ISRAW', 'HB_LB_IS')
    s.row('Right caliper H-bridge')
    half_bridge(s, 'U22', 3, 'EPB_VS', 'CAL_R_A', 'HB_R_IN1', 'HB_R_INH', 'HB_RA_ISRAW')
    half_bridge(s, 'U23', 4, 'EPB_VS', 'CAL_R_B', 'HB_R_IN2', 'HB_R_INH', 'HB_RB_ISRAW')
    is_sense(s, 3, 'HB_RA_ISRAW', 'HB_RA_IS')
    is_sense(s, 4, 'HB_RB_ISRAW', 'HB_RB_IS')
    s.row('Pawl motor (high-side switch)')
    s.add('D211', 'Device:D_TVS', 'SMCJ22A', {'1': 'PAWL_12V', '2': 'GND'}, 'Diode_SMD:D_SMC')
    s.add('C242', 'Device:C_Polarized', '220uF 35V', {'1': 'PAWL_12V', '2': 'GND'}, 'Capacitor_SMD:CP_Elec_8x10.5')
    half_bridge(s, 'U24', 5, 'PAWL_12V', 'MOT_OUT', 'PAWL_DRV', 'PAWL_INH', 'PAWL_ISRAW')
    is_sense(s, 5, 'PAWL_ISRAW', 'PAWL_IS')
    s.row('Power flags')
    flag(s, '#FLG04', 'EPB_VS')
    flag(s, '#FLG05', 'PAWL_12V')


def j1772_sheet(b):
    s = b.sheet('J1772', 'j1772.kicad_sch')
    s.note('Car-side pilot.  CP -> diode -> 2.74k to GND (state B, always) ; 1.3k via K1 to GND (state C).\n'
           'K1 = CPC1117N, form-B (CLOSED when unpowered): a dead board presents state C, so the EVSE delivers\n'
           'AC and Pin-B wakes the truck.  CP_S2_OPEN high = LED on = K1 open = state B (pause / stop).\n'
           'CP read: 200k / 45.3k to 3V3 / 57.6k to GND maps CP -12..+12 V to 0.3..3.0 V (CP 0 V = 1.65 V),\n'
           'load on CP >= 200k.  TLV3201 vs 1.65 V, 1M hysteresis (~0.7 V at CP) -> CP_DUTY (MCPWM capture).\n'
           'Same node -> ADS1115 AIN0 for the high level (+12 / +9 / +6 V = state A / B / C).\n'
           'PP: this board owns PP (Zombie interface=CPC, plug state in 0x357).  4.7k pull-up to 3V3:\n'
           'open 3.3 V, plug 150R ~0.10 V, latch pressed (150R+330R) ~0.31 V -> ADS1115 AIN1.',
           20, 15)
    s.row('Pilot state circuit')
    s.add('D300', 'Device:D_TVS', 'SMAJ15CA', {'1': 'CP', '2': 'GND'}, 'Diode_SMD:D_SMA')
    s.add('D301', 'Device:D', '1N4148W', {'A': 'CP', 'K': 'CP_D'}, 'Diode_SMD:D_SOD-123')
    R(s, 'R300', '2.74k 1%', 'CP_D', 'GND', 'Resistor_SMD:R_0805_2012Metric')
    R(s, 'R301', '1.3k 1%', 'CP_D', 'CP_S2', 'Resistor_SMD:R_0805_2012Metric')
    s.add('K1', 'Relay_SolidState:CPC1117N', 'CPC1117N', {'1': 'K1_LED', '2': 'GND', '3': 'CP_S2', '4': 'GND'})
    R(s, 'R302', '330R', 'CP_S2_OPEN', 'K1_LED')
    s.row('CP read: level shift, comparator, ADC')
    R(s, 'R303', '200k', 'CP', 'CP_SENSE')
    R(s, 'R304', '45.3k', '+3V3', 'CP_SENSE')
    R(s, 'R305', '57.6k', 'CP_SENSE', 'GND')
    C(s, 'C300', '100pF', 'CP_SENSE', 'GND')
    R(s, 'R306', '10k', '+3V3', 'CP_REF')
    R(s, 'R307', '10k', 'CP_REF', 'GND')
    C(s, 'C301', '100nF', 'CP_REF', 'GND')
    s.add('U30', 'PCM_Analog_Comparator_AKL:TLV3201AIDBV', 'TLV3201AIDBV',
          {'1': 'CP_DUTY', '2': 'GND', '3': 'CP_SENSE', '4': 'CP_REF', '5': '+3V3'})
    R(s, 'R308', '1M', 'CP_DUTY', 'CP_SENSE')
    C(s, 'C302', '100nF', '+3V3', 'GND')
    R(s, 'R309', '1k', 'CP_SENSE', 'CP_LVL')
    C(s, 'C303', '1nF', 'CP_LVL', 'GND')
    R(s, 'R310', '0R', 'CP_GND', 'GND', 'Resistor_SMD:R_0805_2012Metric',
      fields={'Note': 'CP return to the inlet PE'})
    s.row('PP read')
    s.add('D302', 'Device:D_TVS', 'SMAJ15CA', {'1': 'PP', '2': 'GND'}, 'Diode_SMD:D_SMA')
    R(s, 'R311', '4.7k', '+3V3', 'PP')
    R(s, 'R312', '1k', 'PP', 'PP_SENSE')
    C(s, 'C304', '10nF', 'PP_SENSE', 'GND')


def sensor_sheet(b):
    s = b.sheet('Sensors', 'sensors.kicad_sch')
    s.note('I2C bus (IO15 SDA / IO16 SCL, 4.7k pull-ups on sheet MCU):\n'
           '  0x20 MCP23017, 0x40 INA226 (A1 = A0 = GND), 0x48 ADS1115 (ADDR = GND), 0x6A LSM6DSO (SA0 = GND).\n'
           'ADS1115: AIN0 CP level, AIN1 PP, AIN2 / AIN3 spare analog (ANA3 / ANA4).\n'
           'LSM6DSO: I2C mode (CS = 3V3); aux SPI pins unused (SDx / SCx to GND).  INT1 -> IO47.\n'
           'Mount the board square to the vehicle axes.\n'
           'INA226: EPB supply shunt 2 mOhm -> 81.92 mV full scale = 40 A; 10R + 100nF input filter.',
           20, 15)
    s.row('ADS1115 16-bit ADC')
    s.add('U40', 'Analog_ADC:ADS1115IDGS', 'ADS1115IDGS',
          {'VDD': '+3V3', 'GND': 'GND', 'SDA': 'I2C_SDA', 'SCL': 'I2C_SCL', 'ADDR': 'GND',
           'AIN0': 'CP_LVL', 'AIN1': 'PP_SENSE', 'AIN2': 'ANA3', 'AIN3': 'ANA4'}, nc=['ALERT/RDY'])
    C(s, 'C400', '100nF', '+3V3', 'GND')
    s.row('LSM6DSO IMU')
    s.add('U41', 'PCM_SparkFun-Sensor:LSM6DSOX', 'LSM6DSOX',
          {'VDD': '+3V3', 'VDDIO': '+3V3', 'GND': 'GND', 'SDA': 'I2C_SDA', 'SCL': 'I2C_SCL',
           '~{CS}': '+3V3', 'SDO/SA0': 'GND', 'SDx': 'GND', 'SCx': 'GND', 'INT1': 'IMU_INT1'},
          nc=['INT2', 'OCS_Aux', 'SDO_Aux'])
    C(s, 'C401', '100nF', '+3V3', 'GND')
    C(s, 'C402', '100nF', '+3V3', 'GND')
    s.row('INA226 EPB supply current')
    s.add('U42', 'Sensor_Energy:INA226', 'INA226AIDGSR',
          {'VS': '+3V3', 'GND': 'GND', 'SDA': 'I2C_SDA', 'SCL': 'I2C_SCL', 'A0': 'GND', 'A1': 'GND',
           'Vin+': 'INA_INP', 'Vin-': 'INA_INN', 'Vbus': 'EPB_VS'}, nc=['~{Alert}'])
    R(s, 'R400', '10R', 'EPB_12V', 'INA_INP')
    R(s, 'R401', '10R', 'EPB_VS', 'INA_INN')
    C(s, 'C403', '100nF 50V', 'INA_INP', 'INA_INN')
    C(s, 'C404', '100nF', '+3V3', 'GND')


def connector_sheet(b):
    s = b.sheet('Connector', 'connector.kicad_sch')
    s.note('32-pin ECU header.  PIN NUMBERS ARE PROVISIONAL until the header drawing arrives.\n'
           'Heavy nets doubled (GND, EPB_12V, caliper and pawl leads); per-pin current rating TBD.\n'
           'H-bridge current returns through the board GND pins (not at the motor) -> GND x3.',
           20, 15)
    s.row('Main connector')
    pins = ['VIN_12V', 'GND', 'GND', 'EPB_12V', 'EPB_12V', 'CAL_L_A', 'CAL_L_A', 'CAL_L_B', 'CAL_L_B',
            'CAL_R_A', 'CAL_R_A', 'CAL_R_B', 'CAL_R_B', 'PAWL_12V', 'PAWL_12V', 'MOT_OUT', 'MOT_OUT',
            'CAN1_H', 'CAN1_L', 'CAN2_H', 'CAN2_L', 'IN_P_SENSE', 'IN_BRAKE', 'IN_WELD1', 'IN_WELD2',
            'CP', 'CP_GND', 'PP', 'EPB_BTN', 'EPB_LED_G', 'EPB_LED_R', 'GND']
    s.add('J20', 'Connector_Generic:Conn_01x32', '32-pin ECU header',
          {str(i + 1): n for i, n in enumerate(pins)})
    s.row('Spare analog (test pads until a connector pin is free)')
    for i, n in enumerate(['ANA1', 'ANA2', 'ANA3', 'ANA4'], 1):
        s.add('TP%d' % i, 'Connector:TestPoint', n, {'1': n}, 'TestPoint:TestPoint_Pad_1.5x1.5mm')
