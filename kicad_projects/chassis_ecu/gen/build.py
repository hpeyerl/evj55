"""Regenerate the chassis_ecu schematic, then check it with kicad-cli.

Usage: /usr/bin/python3 build.py        (system python: KiCad's pcbnew lives there)
Writes ../*.kicad_sch, runs ERC, exports a netlist and checks that every
pin landed on the net the definition asked for.
"""
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

import chassis_ecu
import schgen

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
ROOT = os.path.join(OUT, schgen.PROJECT + '.kicad_sch')


def main():
    board = chassis_ecu.build()
    board.write(OUT)
    pro = os.path.join(OUT, schgen.PROJECT + '.kicad_pro')
    if not os.path.exists(pro):
        with open(pro, 'w') as f:
            f.write('{}\n')
    erc = os.path.join(HERE, 'erc.rpt')
    subprocess.run(['kicad-cli', 'sch', 'erc', '-o', erc, ROOT], check=True, capture_output=True)
    rpt = open(erc).read()
    m = re.search(r'ERC messages: (\d+)\s+Errors (\d+)\s+Warnings (\d+)', rpt)
    print('ERC: %s messages, %s errors, %s warnings' % m.groups())
    net = os.path.join(HERE, 'netlist.xml')
    subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadxml', '-o', net, ROOT],
                   check=True, capture_output=True)
    got = {}
    for n in ET.parse(net).getroot().iter('net'):
        name = n.get('name').split('/')[-1]
        for node in n.iter('node'):
            got[(node.get('ref'), node.get('pin'))] = name
    bad = 0
    for s in board.sheets:
        for p in s.parts:
            if isinstance(p, tuple):
                continue
            ls = schgen.lib_symbol(p.lib_id)
            for pin in schgen.sym_pins(ls, p.unit):
                want = p.nets.get(pin['number'], p.nets.get(pin['name']))
                if want is None:
                    continue
                have = got.get((p.ref, pin['number']))
                if p.ref.startswith('#'):
                    continue
                if have != want:
                    print('NET MISMATCH %s.%s (%s): want %s, got %s' % (p.ref, pin['number'], pin['name'], want, have))
                    bad += 1
    print('netlist check: %s' % ('OK' if not bad else '%d mismatches' % bad))
    if '-v' in sys.argv:
        print(rpt)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
