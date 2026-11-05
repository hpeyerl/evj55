"""chassis_ecu schematic definition.  Run build.py to regenerate."""
from schgen import Board

R0603 = 'Resistor_SMD:R_0603_1608Metric'
C0603 = 'Capacitor_SMD:C_0603_1608Metric'
C1206 = 'Capacitor_SMD:C_1206_3216Metric'
C1210 = 'Capacitor_SMD:C_1210_3225Metric'
SOT23 = 'Package_TO_SOT_SMD:SOT-23'
BTN = 'Button_Switch_SMD:SW_SPST_TL3342'


def R(s, ref, val, a, b, fp=R0603, **k):
    return s.add(ref, 'Device:R', val, {'1': a, '2': b}, fp, **k)


def C(s, ref, val, a, b, fp=C0603, **k):
    return s.add(ref, 'Device:C', val, {'1': a, '2': b}, fp, **k)


def flag(s, ref, net):
    return s.add(ref, 'power:PWR_FLAG', 'PWR_FLAG', {'1': net})


def build():
    b = Board('chassis_ecu', 'A')

    # --- Power ----------------------------------------------------------------
    s = b.sheet('Power', 'power.kicad_sch')
    s.note('12V logic input -> fuse -> bidirectional TVS -> P-FET reverse protection (same as the HAT)\n'
           '-> LM5164 buck, 3.3V 1A, 300 kHz, Type-3 ripple injection (datasheet SNVSAU4D 7.2.2).\n'
           'VOUT = 1.2 x (1 + 174k/100k) = 3.29 V.  RON = 3.3 x 2500 / 300 kHz = 27.4k.\n'
           'EN/UVLO: start 1.5 x (1 + 301k/100k) = 6.0 V, stop 5.6 V.\n'
           'L1: 22uH, Isat >= 2 A (LM5164 peak limit 1.75 A max), DCR <= 0.15 R, 6x6 shielded.\n'
           'Ripple 0.46 A p-p at 40 V in.  Type 3: CA >= 525 pF -> 3.3 nF, RA 124k -> 16 mV (8 V) .. 25 mV (40 V) at FB.\n'
           'VSENSE_12V: 100k/10k divider (12 V -> 1.09 V), BAT54S clamp to the rails.',
           20, 15)
    s.row('Input protection: fuse, TVS, reverse-polarity P-FET')
    s.add('F1', 'Device:Fuse', '1A >=50V', {'1': 'VIN_12V', '2': 'VIN_F'}, 'Fuse:Fuse_1206_3216Metric')
    s.add('D1', 'Device:D_TVS', 'SMAJ33CA', {'1': 'VIN_F', '2': 'GND'}, 'Diode_SMD:D_SMA')
    s.add('Q1', 'PCM_Transistor_MOSFET_AKL:FDD4685', 'FDD4685',
          {'G': 'QREV_G', 'D': 'VIN_F', 'S': '+12V_LOGIC'}, 'Package_TO_SOT_SMD:TO-252-2')
    R(s, 'R1', '10k', 'QREV_G', 'GND')
    s.add('D2', 'Device:D_Zener', 'BZT52C15', {'K': '+12V_LOGIC', 'A': 'QREV_G'}, 'Diode_SMD:D_SOD-123')
    s.row('Buck input capacitors')
    s.add('C1', 'Device:C_Polarized', '47uF 63V', {'1': '+12V_LOGIC', '2': 'GND'},
          'Capacitor_SMD:CP_Elec_8x10')
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
    s.add('L1', 'Device:L', '22uH Isat>=2A', {'1': 'BUCK_SW', '2': '+3V3'},
          'Inductor_SMD:L_Bourns_SRN6045TA')
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
           'ADC1 (IO1-10) for analog; ADC2 is unusable with WiFi.  Spare: IO6, IO8, IO9, IO47.',
           20, 15)
    s.row('ESP32-S3 module')
    s.add('U2', 'RF_Module:ESP32-S3-WROOM-1', 'ESP32-S3-WROOM-1-N8', {
        'GND': 'GND', '3V3': '+3V3', 'EN': 'ESP_EN', 'IO0': 'ESP_BOOT',
        'IO1': 'HB_L_IS', 'IO2': 'HB_R_IS', 'IO4': 'ANA1', 'IO5': 'ANA2', 'IO7': 'VSENSE_12V',
        'IO10': 'IOX_INT', 'IO11': 'SPI_MOSI', 'IO12': 'SPI_SCK', 'IO13': 'SPI_MISO',
        'IO14': 'CAN2_CS', 'IO21': 'CAN2_INT', 'IO15': 'I2C_SDA', 'IO16': 'I2C_SCL',
        'IO17': 'CAN1_TXD', 'IO18': 'CAN1_RXD',
        'IO35': 'HB_L_IN1', 'IO36': 'HB_L_IN2', 'IO37': 'HB_R_IN1', 'IO38': 'HB_R_IN2',
        'IO39': 'HB_L_INH', 'IO40': 'HB_R_INH',
        'IO41': 'CP_DUTY', 'IO42': 'CP_S2_OPEN', 'IO48': 'PAWL_DRV',
        'TXD0': 'UART_TX', 'RXD0': 'UART_RX', 'USB_D-': 'USB_DM', 'USB_D+': 'USB_DP',
    }, 'RF_Module:ESP32-S3-WROOM-1', nc=['IO3', 'IO45', 'IO46', 'IO6', 'IO8', 'IO9', 'IO47'])
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
    s.add('J1', 'Connector:USB_C_Receptacle_USB2.0_16P', 'USB-C',
          {'GND': 'GND', 'VBUS': 'USB_VBUS', 'CC1': 'USB_CC1', 'CC2': 'USB_CC2',
           'D+': 'USB_DP', 'D-': 'USB_DM', 'SHIELD': 'GND'},
          'Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal',
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
           'Y1: 40 MHz; load caps C16/C17 depend on the crystal CL (12 pF placeholder).',
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
    s.add('Y1', 'Device:Crystal_GND24', '40MHz', {'1': 'CAN2_OSC1', '3': 'CAN2_OSC2', 'G': 'GND'},
          'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm')
    C(s, 'C16', '12pF', 'CAN2_OSC1', 'GND')
    C(s, 'C17', '12pF', 'CAN2_OSC2', 'GND')
    s.row('CAN2 transceiver')
    s.add('U6', 'Interface_CAN_LIN:SN65HVD230', 'SN65HVD230',
          {'D': 'CAN2_TXD', 'R': 'CAN2_RXD', 'VCC': '+3V3', 'GND': 'GND', 'Rs': 'GND',
           'CANH': 'CAN2_H', 'CANL': 'CAN2_L'}, 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', nc=['Vref'])
    C(s, 'C18', '100nF', '+3V3', 'GND')
    s.add('D5', 'Power_Protection:NUP2105L', 'NUP2105L', {'1': 'CAN2_H', '2': 'CAN2_L', '3': 'GND'}, SOT23)
    s.add('JP2', 'Jumper:SolderJumper_2_Open', 'CAN2 TERM', {'A': 'CAN2_H', 'B': 'CAN2_TERM'},
          'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm')
    R(s, 'R19', '120R', 'CAN2_TERM', 'CAN2_L', 'Resistor_SMD:R_1206_3216Metric')
    return b
