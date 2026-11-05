"""Pick LCSC parts from a local jlcparts database (yaqwsx/jlcparts cache.sqlite3).

Usage: /usr/bin/python3 jlc_select.py /path/to/cache.sqlite3
Writes lcsc_parts.json: {value|footprint: {lcsc, mfr, package, type, stock, desc}}.
Preference: in stock (>= 100), basic > preferred > extended, then stock.
"""
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = 'Chip Resistor - Surface Mount'
MLCC = 'Multilayer Ceramic Capacitors MLCC - SMD/SMT'

# key -> (where-clauses on mfr/package/description/subcategory)
SPECS = {}


def res(key, val, pkg, tol='±1%'):
    SPECS[key] = dict(sub=RES, pkg=pkg, desc=[val, tol])


def cap(key, val, pkg, volt, diel):
    SPECS[key] = dict(sub=MLCC, pkg=pkg, desc=[val, volt, diel])


def mpn(key, m, pkg=None):
    SPECS[key] = dict(mfr=m, pkg=pkg)


for v, t in [('0R', '0Ω'), ('10R', '10Ω'), ('100R', '100Ω'), ('330R', '330Ω'), ('1k', '1kΩ'),
             ('4.7k', '4.7kΩ'), ('5.1k', '5.1kΩ'), ('10k', '10kΩ'), ('27.4k', '27.4kΩ'),
             ('45.3k', '45.3kΩ'), ('57.6k', '57.6kΩ'), ('100k', '100kΩ'), ('124k', '124kΩ'),
             ('174k', '174kΩ'), ('200k', '200kΩ'), ('301k', '301kΩ'), ('1M', '1MΩ')]:
    res(v + '|R_0603_1608Metric', t, '0603')
res('0R|R_0805_2012Metric', '0Ω', '0805')
res('1.3k 1%|R_0805_2012Metric', '1.3kΩ', '0805')
res('2.74k 1%|R_0805_2012Metric', '2.74kΩ', '0805')
res('2.2k|R_0805_2012Metric', '2.2kΩ', '0805')
res('4.7k|R_0805_2012Metric', '4.7kΩ', '0805')
res('120R|R_1206_3216Metric', '120Ω', '1206')
for k, v, volt, d in [('100nF', '100nF', '50V', 'X7R'), ('100nF 50V', '100nF', '50V', 'X7R'),
                      ('100pF', '100pF', '50V', 'C0G'), ('10nF', '10nF', '50V', 'X7R'),
                      ('18pF', '18pF', '50V', 'C0G'), ('1nF', '1nF', '50V', 'X7R'),
                      ('1uF', '1uF', '50V', 'X5R'), ('2.2nF 50V X7R', '2.2nF', '50V', 'X7R'),
                      ('3.3nF', '3.3nF', '50V', 'X7R')]:
    cap(k + '|C_0603_1608Metric', v, '0603', volt, d)
cap('220nF 50V|C_0805_2012Metric', '220nF', '0805', '50V', 'X7R')
cap('22uF 10V X7R|C_1206_3216Metric', '22uF', '1206', '25V', 'X5R')
cap('2.2uF 100V X7R|C_1210_3225Metric', '2.2uF', '1210', '100V', 'X7R')
SPECS['47uF 63V|CP_Elec_6.3x7.7'] = dict(sub='Aluminum Electrolytic Capacitors - SMD', desc=['47uF', '63V'],
                                      pkg_like='D6.3xL7.7')
SPECS['470uF 35V|CP_Elec_10x10'] = dict(sub='Aluminum Electrolytic Capacitors - SMD', desc=['470uF', '35V'],
                                          pkg_like='D10xL10.2')
SPECS['220uF 35V|CP_Elec_8x10.5'] = dict(sub='Aluminum Electrolytic Capacitors - SMD', desc=['220uF', '35V'],
                                          pkg_like='D8xL10')
SPECS['2mR 3W|R_2512_6332Metric'] = dict(desc=['2mΩ'], pkg='2512',
                                                                  sub='Current Sense Resistors / Shunt Resistors')


SPECS['LED green|LED_0603_1608Metric'] = dict(desc=['Green'], pkg='0603', sub='LED Indication - Discrete')
for k, m in [('LM5164DDAR', 'LM5164DDAR'), ('FDD4685', 'FDD4685'), ('SMAJ24CA', 'SMAJ24CA'),
             ('BZT52C15', 'BZT52C15'), ('BAT54S', 'BAT54S%'), ('ESP32-S3-WROOM-1-N8', 'ESP32-S3-WROOM-1-N8'),
             ('ESP32-S3-WROOM-1U-N8', 'ESP32-S3-WROOM-1U-N8'), ('USBLC6-2SC6', 'USBLC6-2SC6'),
             ('SN65HVD230', 'SN65HVD230DR'), ('NUP2105L', 'NUP2105L%'), ('MCP2518FD', 'MCP2518FD%QBB'),
             ('LTV-357T', 'LTV-357T%'), ('1N4148W', '1N4148W'),
             ('DMN6075S', 'DMN6075S%'), ('B5819W', 'B5819W%'), ('2N7002', '2N7002'), 
             ('BTN8982TA', 'BTN8982TA%'), ('SMCJ22A', 'SMCJ22A'), ('SMAJ15CA', 'SMAJ15CA'),
             ('CPC1117N', 'CPC1117N%'), ('TLV3201AIDBV', 'TLV3201AIDBVR'), ('ADS1115IDGS', 'ADS1115IDGSR'),
             ('INA226AIDGSR', 'INA226AIDGSR'), ('40MHz 12pF', '7B040000M01'),
             ('TYPE-C-31-M-12', 'TYPE-C-31-M-12'), ('22uH 2.2A', 'FNR6045S220MT'),
             ('1A 63V', '0466001.NRHF'), ('BSS84', 'LBSS84LT1G'), ('LSM6DSOX', 'LSM6DSOXTR'),
             ('MCP23017-E/SO', 'MCP23017-E/SO'), ('RESET', 'TS-1187A-B-A-B'), ('BOOT', 'TS-1187A-B-A-B')]:
    mpn(k, m)


def pick(c, spec):
    q = 'select lcsc, mfr, package, library_type, preferred, stock, description, subcategory ' \
        'from jlc_components where present = 1 and stock >= 100'
    a = []
    if 'mfr' in spec:
        q += ' and mfr like ?'
        a.append(spec['mfr'])
    if spec.get('sub'):
        q += ' and subcategory = ?'
        a.append(spec['sub'])
    if spec.get('sub_like'):
        q += ' and subcategory like ?'
        a.append('%' + spec['sub_like'] + '%')
    if spec.get('pkg'):
        q += ' and package = ?'
        a.append(spec['pkg'])
    if spec.get('pkg_like'):
        q += ' and package like ?'
        a.append('%' + spec['pkg_like'] + '%')
    for d in spec.get('desc', []):
        q += ' and (" " || description || " ") like ?'
        a.append('% ' + d + ' %')
    q += " order by (library_type = 'base') desc, preferred desc, stock desc limit 5"
    return c.execute(q, a).fetchall()


def main():
    c = sqlite3.connect(sys.argv[1])
    out = {}
    for k, spec in SPECS.items():
        rows = pick(c, spec)
        if not rows:
            print('NONE  %s' % k)
            continue
        r = rows[0]
        typ = 'basic' if r[3] == 'base' else ('pref' if r[4] else 'ext')
        out[k] = dict(lcsc='C%d' % r[0], mfr=r[1], package=r[2], type=typ, stock=r[5], desc=r[6][:90])
        print('%-40s C%-8d %-28s %-14s %-5s %7d' % (k[:40], r[0], r[1][:28], r[2][:14], typ, r[5]))
    with open(os.path.join(HERE, 'lcsc_parts.json'), 'w') as f:
        json.dump(out, f, indent=1, sort_keys=True, ensure_ascii=False)


if __name__ == '__main__':
    main()
