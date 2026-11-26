"""Write the project-local library: symbol + footprint for the main connector.

Connector = Aptiv/FCI HCCPHPE24BKA90F (24-way 90 deg PCB header, key A, black),
mates with housing 211PC249S0005.  Pins A1-A8 / B1-B8 / C1-C8 as moulded on the
housing; columns 1 and 8 are the large (high-current) cavities.

Footprint from FCI drawing FSC 308654 (PCB layout, black), components side:
  rows 4.20 apart; columns 4.15 / 5 x 3.33 / 4.15 (24.95 overall); holes 1.3 +0.2/-0;
  slots 2.2 wide, 5.0 long (col-8 side) and 3.5 long (col-1 side), both ending 0.4 past
  row C; 38.4 between slot inner edges; board edge 7.5 from row C; edge notch 2.0 wide x
  2.2 deep, 16.0 from the connector centreline (col-8 side); board 1.6 mm.
Origin = A1.  Column n at x = -X[n], row A/B/C at y = 0 / 4.2 / 8.4.

3D model: vendor STEP, not redistributable -> lib/3d/ is git-ignored; place
HCCPHPE24BKA90F.stp there locally.
"""

import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, '..', 'lib')
NAME = 'FCI_HCCPHPE24BKA90F'

X = [0.0, 4.15, 7.48, 10.81, 14.14, 17.47, 20.80, 24.95]
ROWS = 'ABC'
PITCH_Y = 4.2
DRILL = 1.4
PAD = 2.2
EDGE_Y = 8.4 + 7.5
CX = -24.95 / 2
SLOT_W = 2.2
SLOT_DX = 38.4 / 2 + SLOT_W / 2
SLOT_BOT = 8.4 + 0.4
NOTCH_X = CX - 16.0


def pins():
    return ['%s%d' % (r, c) for r in ROWS for c in range(1, 9)]


def symbol():
    src = open('/usr/share/kicad/symbols/Connector_Generic.kicad_sym').read()
    a = src.index('\t(symbol "Conn_01x24"')
    b = src.index('\n\t(symbol "', a + 1)
    s = src[a:b]
    labels = pins()
    s = s.replace('"Conn_01x24', '"' + NAME)
    s = re.sub(r'\(name "Pin_(\d+)"', lambda m: '(name "%s"' % labels[int(m.group(1)) - 1], s)
    s = re.sub(r'\(number "(\d+)"', lambda m: '(number "%s"' % labels[int(m.group(1)) - 1], s)
    s = re.sub(r'\(property "Value" "[^"]*"', '(property "Value" "%s"' % NAME, s)
    s = re.sub(r'\(property "Footprint" "[^"]*"', '(property "Footprint" "chassis_ecu:%s"' % NAME, s)
    s = re.sub(r'\(property "Description" "[^"]*"',
           '(property "Description" "Aptiv/FCI 24-way 90deg PCB header, key A"', s)
    s = s.replace('(hide yes)\n\t\t)\n\t\t(exclude_from_sim', '(hide no)\n\t\t)\n\t\t(exclude_from_sim', 1)
    return ('(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "chassis_ecu_make_lib")\n'
        + s + '\n)\n')


def footprint():
    o = []
    o.append('(footprint "%s"' % NAME)
    o.append('\t(version 20260206)\n\t(generator "chassis_ecu_make_lib")\n\t(layer "F.Cu")')
    o.append('\t(descr "Aptiv/FCI HCCPHPE24BKA90F 24-way 90deg header, key A; FCI FSC 308654")')
    o.append('\t(attr through_hole)')
    o.append('\t(property "Reference" "REF**" (at %.3f %.3f 0) (layer "F.SilkS")'
         ' (effects (font (size 1 1) (thickness 0.15))))' % (CX, -3.5))
    o.append('\t(property "Value" "%s" (at %.3f %.3f 0) (layer "F.Fab")'
         ' (effects (font (size 1 1) (thickness 0.15))))' % (NAME, CX, 12.0))
    for n, p in enumerate(pins()):
        r, c = ROWS.index(p[0]), int(p[1:]) - 1
        shape = 'rect' if p == 'A1' else 'circle'
        o.append('\t(pad "%s" thru_hole %s (at %.3f %.3f) (size %.2f %.2f) (drill %.2f)'
             ' (layers "*.Cu" "*.Mask"))' % (p, shape, -X[c], r * PITCH_Y, PAD, PAD, DRILL))
    for x, ln in ((CX - SLOT_DX, 5.0), (CX + SLOT_DX, 3.5)):
        y = SLOT_BOT - ln / 2
        o.append('\t(pad "" np_thru_hole oval (at %.3f %.3f) (size %.2f %.2f) (drill oval %.2f %.2f)'
             ' (layers "*.Cu" "*.Mask"))' % (x, y, SLOT_W, ln, SLOT_W, ln))
    # Body outline (on board), board edge line, notch (cut it into Edge.Cuts at layout).
    x0, x1, y0 = CX - SLOT_DX - 2.3, CX + SLOT_DX + 2.3, -1.2
    for lay, w in (('F.Fab', 0.1), ('F.SilkS', 0.12)):
        o.append('\t(fp_rect (start %.3f %.3f) (end %.3f %.3f) (stroke (width %.2f) (type solid))'
             ' (fill no) (layer "%s"))' % (x0, y0, x1, EDGE_Y, w, lay))
    o.append('\t(fp_rect (start %.3f %.3f) (end %.3f %.3f) (stroke (width 0.05) (type solid))'
         ' (fill no) (layer "F.CrtYd"))' % (x0 - 1, y0 - 1.6, x1 + 1, EDGE_Y))
    nx0, nx1 = NOTCH_X - 1.0, NOTCH_X + 1.0
    o.append('\t(fp_poly (pts (xy %.3f %.3f) (xy %.3f %.3f) (xy %.3f %.3f) (xy %.3f %.3f))'
         ' (stroke (width 0.1) (type solid)) (fill no) (layer "Dwgs.User"))'
         % (nx0, EDGE_Y, nx0, EDGE_Y - 2.2, nx1, EDGE_Y - 2.2, nx1, EDGE_Y))
    o.append('\t(fp_text user "BOARD EDGE; notch 2.0x2.2 -> Edge.Cuts" (at %.3f %.3f 0) (layer "Dwgs.User")'
         ' (effects (font (size 0.8 0.8) (thickness 0.1))))' % (CX, EDGE_Y + 1.2))
    o.append('\t(model "${KIPRJMOD}/lib/3d/HCCPHPE24BKA90F.stp"'
         ' (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))')
    o.append(')')
    return '\n'.join(o) + '\n'


def main():
    os.makedirs(os.path.join(LIB, 'chassis_ecu.pretty'), exist_ok=True)
    with open(os.path.join(LIB, 'chassis_ecu.kicad_sym'), 'w') as f:
        f.write(symbol())
    with open(os.path.join(LIB, 'chassis_ecu.pretty', NAME + '.kicad_mod'), 'w') as f:
        f.write(footprint())


if __name__ == '__main__':
    main()
