"""Search text per BOM line (value, footprint) for lcsc.py.  key -> (search, package, must)."""
R = 'Resistor_SMD:R_0603_1608Metric'
Q = {}
for v, t in [('0R', '0Ω'), ('10R', '10Ω'), ('100R', '100Ω'), ('330R', '330Ω'), ('1k', '1kΩ'),
             ('4.7k', '4.7kΩ'), ('5.1k', '5.1kΩ'), ('10k', '10kΩ'), ('27.4k', '27.4kΩ'),
             ('45.3k', '45.3kΩ'), ('57.6k', '57.6kΩ'), ('100k', '100kΩ'), ('124k', '124kΩ'),
             ('174k', '174kΩ'), ('200k', '200kΩ'), ('301k', '301kΩ'), ('1M', '1MΩ')]:
    Q[(v, 'R_0603_1608Metric')] = (t + ' 0603', '0603', ['Resistor'])
Q[('0R', 'R_0805_2012Metric')] = ('0Ω 0805', '0805', ['Resistor'])
Q[('1.3k 1%', 'R_0805_2012Metric')] = ('1.3kΩ 0805', '0805', ['±1%'])
Q[('2.74k 1%', 'R_0805_2012Metric')] = ('2.74kΩ 0805', '0805', ['±1%'])
Q[('120R', 'R_1206_3216Metric')] = ('120Ω 1206', '1206', ['Resistor'])
Q[('2.2k', 'R_1206_3216Metric')] = ('2.2kΩ 1206', '1206', ['Resistor'])
Q[('4.7k', 'R_1206_3216Metric')] = ('4.7kΩ 1206', '1206', ['Resistor'])
Q[('2mR 3W', 'R_Shunt_Vishay_WSK2512_6332Metric_T1.19mm')] = ('2mΩ 2512', '2512', [])
for v, t, pk in [('100nF', '100nF 50V 0603', '0603'), ('100nF 50V', '100nF 50V 0603', '0603'),
                 ('100pF', '100pF 50V 0603', '0603'), ('10nF', '10nF 50V 0603', '0603'),
                 ('18pF', '18pF 50V 0603', '0603'), ('1nF', '1nF 50V 0603', '0603'),
                 ('1uF', '1uF 0603', '0603'), ('2.2nF 50V X7R', '2.2nF 50V 0603', '0603'),
                 ('3.3nF', '3.3nF 50V 0603', '0603')]:
    Q[(v, 'C_0603_1608Metric')] = (t, pk, ['X7R'] if 'pF' not in v else [])
Q[('220nF 50V', 'C_0805_2012Metric')] = ('220nF 50V 0805', '0805', ['X7R'])
Q[('22uF 10V X7R', 'C_1206_3216Metric')] = ('22uF 1206', '1206', [])
Q[('2.2uF 100V X7R', 'C_1210_3225Metric')] = ('2.2uF 100V 1210', '1210', [])
Q[('47uF 63V', 'CP_Elec_8x10')] = ('47uF 63V aluminum', None, [])
Q[('470uF 35V', 'CP_Elec_10x10.5')] = ('470uF 35V aluminum', None, [])
Q[('220uF 35V', 'CP_Elec_10x10.5')] = ('220uF 35V aluminum', None, [])
for v in ['2N7002', 'AO3401A', 'BAT54S', 'BTN8982TA', 'CPC1117N', 'ADS1115IDGSR', 'INA226AIDGSR',
          'LM5164DDAR', 'MCP23017-E/SS', 'MCP2518FD', 'NUP2105L', 'SN65HVD230DR', 'TLV3201AIDBVR',
          'USBLC6-2SC6', 'FDD4685', 'LSM6DSOTR', 'ESP32-S3-WROOM-1-N8', 'ESP32-S3-WROOM-1U-N8',
          'DMN6075S', 'LTV-357T', '1N4148W', 'B5819W', 'BZT52C15', 'SMAJ33CA', 'SMAJ15CA', 'SMCJ22A',
          '7B040000M01']:
    Q[(v, None)] = (v, None, [])
Q[('22uH Isat>=2A', 'L_Bourns_SRN6045TA')] = ('22uH 6045', None, [])
Q[('1A >=50V', 'Fuse_1206_3216Metric')] = ('1206 fuse 1A', None, [])
Q[('LED', 'LED_0603_1608Metric')] = ('0603 LED green', '0603', [])
Q[('TL3342', None)] = ('TL3342', None, [])
Q[('USB4105', None)] = ('USB4105-GF-A', None, [])
