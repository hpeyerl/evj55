"""Create ../chassis_ecu.kicad_pcb: outline, fixed parts, first-pass block placement.

Starting point for hand layout, NOT re-runnable over a routed board: refuses to
overwrite an existing .kicad_pcb unless --force.  After this, edit in KiCad and
use "Update PCB from Schematic" (footprints carry the symbol paths).

Board coords: origin = top-left of the outline, x right, y down, mm.  The J20 edge
is the top (y = 0); the case is full height (33 mm) only over y < ~34, so tall
parts go there.  ESP32 antenna flush with the bottom edge.
Case drawing (to verify on the real case): PCB 82 x 101, holes 62.2 apart at
y = 101 - 7.4 and 101 - 13.4.

Run with the system python (pcbnew):  /usr/bin/python3 make_pcb.py [--force]
"""

import glob
import os
import re
import sys

import pcbnew

import chassis_ecu

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'chassis_ecu.kicad_pcb')
NETLIST = os.path.join(HERE, 'netlist.xml')
FPDIR = '/usr/share/kicad/footprints'
PCMDIR = os.path.expanduser('~/.local/share/kicad/10.0/3rdparty/footprints')
PROJLIB = os.path.join(HERE, '..', 'lib')

W, H = 82.0, 101.0
RADIUS = 3.0
OX, OY = 100.0, 50.0            # page offset of the board origin
J20_CX = W / 2
NOTCH_W, NOTCH_D = 2.0, 2.2
HOLE_X = (W / 2 - 31.1, W / 2 + 31.1)
HOLE_Y = (H - 13.4, H - 7.4)
GAP = 0.4                       # between courtyards when packing

# Block regions (x0, y0, x1, y1), filled in schematic order.  Several rects per sheet.
REGIONS = {
    'Power':     [(1, 19, 40, 40), (1, 1, 15, 19)],
    'Motors':    [(40, 19, 81, 40), (67, 1, 81, 19)],
    'J1772':     [(1, 40, 30, 62)],
    'CAN':       [(30, 40, 50, 52)],
    'Sensors':   [(50, 40, 81, 56)],
    'MCU':       [(25, 56, 57, 74)],
    'IO':        [(57, 56, 81, 100), (1, 62, 25, 100)],
    'Connector': [(1, 1, 81, 19)],
}
FIXED = ('J20', 'U2', 'H1', 'H2', 'H3', 'H4', 'J1')
FIRST = ('C1', 'C242')          # tallest: pack first, top of their regions


def mm(v):
    return pcbnew.FromMM(v)


def pt(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


def fp_dir(lib):
    if lib == 'chassis_ecu':
        return os.path.join(PROJLIB, 'chassis_ecu.pretty')
    if lib.startswith('PCM_'):
        g = glob.glob(os.path.join(PCMDIR, '*', lib[4:] + '.pretty'))
        return g[0]
    return os.path.join(FPDIR, lib + '.pretty')


def read_netlist():
    x = open(NETLIST).read()
    comps = {}
    for ref, body in re.findall(r'<comp ref="([^"]+)">(.*?)</comp>', x, re.S):
        fp = re.search(r'<footprint>([^<]*)', body).group(1)
        val = re.search(r'<value>([^<]*)', body).group(1)
        sp = re.search(r'<sheetpath names="([^"]*)" tstamps="([^"]*)"', body)
        ts = re.search(r'<tstamps>([^<]*)', body).group(1)
        comps[ref] = dict(fp=fp, val=val, sheet=sp.group(1).strip('/'), path=sp.group(2) + ts)
    pads = {}
    for name, body in re.findall(r'<net code="\d+" name="([^"]*)"[^>]*>(.*?)</net>', x, re.S):
        for ref, pin in re.findall(r'<node ref="([^"]+)" pin="([^"]+)"', body):
            pads[(ref, pin)] = name
    return comps, pads


def seg(board, a, b):
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pt(*a))
    s.SetEnd(pt(*b))
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(mm(0.1))
    board.Add(s)


def arc(board, a, m, b):
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
    s.SetArcGeometry(pt(*a), pt(*m), pt(*b))
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(mm(0.1))
    board.Add(s)


def outline(board, notch_x):
    r, k = RADIUS, RADIUS * (1 - 0.70710678)
    n0, n1 = notch_x - NOTCH_W / 2, notch_x + NOTCH_W / 2
    seg(board, (r, 0), (n0, 0))
    seg(board, (n0, 0), (n0, NOTCH_D))
    seg(board, (n0, NOTCH_D), (n1, NOTCH_D))
    seg(board, (n1, NOTCH_D), (n1, 0))
    seg(board, (n1, 0), (W - r, 0))
    arc(board, (W - r, 0), (W - k, k), (W, r))
    seg(board, (W, r), (W, H - r))
    arc(board, (W, H - r), (W - k, H - k), (W - r, H))
    seg(board, (W - r, H), (r, H))
    arc(board, (r, H), (k, H - k), (0, H - r))
    seg(board, (0, H - r), (0, r))
    arc(board, (0, r), (k, k), (r, 0))


def courtyard(fp):
    c = fp.GetCourtyard(pcbnew.F_CrtYd)
    if c.OutlineCount():
        return c.BBox()
    return fp.GetBoundingBox(False)


def place_at(fp, x, y, rot=0):
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(pt(x, y))


def pack(fps, rects, obstacles):
    """Shelf-pack footprints (in order) into rects; returns the ones that did not fit."""
    left = list(fps)
    for (x0, y0, x1, y1) in rects:
        cx, cy, shelf = x0, y0, 0.0
        rest = []
        for fp in left:
            bb = courtyard(fp)
            w, h = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
            placed = False
            while not placed:
                if cx + w > x1:
                    cx, cy, shelf = x0, cy + shelf + GAP, 0.0
                if cy + h > y1:
                    break
                box = (cx, cy, cx + w, cy + h)
                hit = [o for o in obstacles if not (box[2] <= o[0] or box[0] >= o[2] or
                                                    box[3] <= o[1] or box[1] >= o[3])]
                if hit:
                    cx = max(o[2] for o in hit) + GAP
                    continue
                pos = fp.GetPosition()
                dx = pcbnew.ToMM(pos.x - bb.GetX())
                dy = pcbnew.ToMM(pos.y - bb.GetY())
                fp.SetPosition(pcbnew.VECTOR2I(mm(OX + cx + dx), mm(OY + cy + dy)))
                obstacles.append(box)
                cx += w + GAP
                shelf = max(shelf, h)
                placed = True
            if not placed:
                rest.append(fp)
        left = rest
    return left


def box_of(fp):
    bb = courtyard(fp)
    return (pcbnew.ToMM(bb.GetX()) - OX, pcbnew.ToMM(bb.GetY()) - OY,
            pcbnew.ToMM(bb.GetRight()) - OX, pcbnew.ToMM(bb.GetBottom()) - OY)


def main():
    if os.path.exists(OUT) and '--force' not in sys.argv:
        sys.exit('%s exists; not overwriting (use --force to discard it)' % OUT)
    comps, pads = read_netlist()
    board = pcbnew.NewBoard(OUT)
    board.SetCopperLayerCount(4)
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = mm(0.127)
    ds.m_MinClearance = mm(0.127)
    ds.m_ViasMinSize = mm(0.45)
    ds.m_MinThroughDrill = mm(0.2)       # module / LM5164 thermal vias; JLC 4-layer OK
    ds.m_CopperEdgeClearance = mm(0.3)

    nets = {}
    for n in sorted(set(pads.values())):
        nets[n] = pcbnew.NETINFO_ITEM(board, n)
        board.Add(nets[n])

    fps = {}
    for ref, c in comps.items():
        lib, name = c['fp'].split(':', 1)
        fp = pcbnew.FootprintLoad(fp_dir(lib), name)
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.SetValue(c['val'])
        fp.SetPath(pcbnew.KIID_PATH(c['path']))
        board.Add(fp)
        for p in fp.Pads():
            n = pads.get((ref, p.GetNumber()))
            if n:
                p.SetNet(nets[n])
        fps[ref] = fp

    # J20: mating face at the top edge (footprint edge is +y at 0 deg -> rotate 180).
    a1x = J20_CX - 24.95 / 2
    place_at(fps['J20'], a1x, 8.4 + 7.5, 180)
    notch_x = a1x + 24.95 / 2 + 16.0
    outline(board, notch_x)

    # ESP32: antenna (-y end at 0 deg) flush with the bottom edge -> rotate 180.
    place_at(fps['U2'], W / 2, H - 12.8, 180)
    for i, (x, y) in enumerate([(HOLE_X[0], HOLE_Y[0]), (HOLE_X[0], HOLE_Y[1]),
                                (HOLE_X[1], HOLE_Y[0]), (HOLE_X[1], HOLE_Y[1])], 1):
        place_at(fps['H%d' % i], x, y)
    # USB-C on the left edge, opening facing out, shell front 0.5 mm past the edge.
    place_at(fps['J1'], 10.0, 70.0, 270)
    bb = courtyard(fps['J1'])
    fps['J1'].Move(pcbnew.VECTOR2I(mm(OX - 0.5) - bb.GetX(), 0))

    # U2 courtyard includes the on-board-antenna keep-out; the antenna overhangs the
    # edge here, so block only the module body.
    obstacles = [box_of(fps[r]) for r in FIXED if r != 'U2']
    obstacles.append((W / 2 - 9.1, H - 25.6 - GAP, W / 2 + 9.1, H))
    obstacles.append((W / 2 - 9.1, H - 6.2, W / 2 + 9.1, H))
    obstacles.append((notch_x - 2, 0, notch_x + 2, 3))

    # Antenna keep-out: no copper under the antenna, all layers.
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowPads(True)
    z.SetDoNotAllowFootprints(False)
    z.SetLayerSet(pcbnew.LSET.AllCuMask())
    z.SetZoneName('ESP32 antenna keep-out')
    o = z.Outline()
    o.NewOutline()
    for x, y in ((W / 2 - 9.1, H - 6.2), (W / 2 + 9.1, H - 6.2), (W / 2 + 9.1, H), (W / 2 - 9.1, H)):
        o.Append(mm(OX + x), mm(OY + y))
    board.Add(z)

    b = chassis_ecu.build()
    spill = []
    for s in b.sheets:
        order = [p.ref for p in s.parts if not isinstance(p, tuple) and not p.ref.startswith('#')
                 and p.ref in fps and p.ref not in FIXED]
        order = [r for r in FIRST if r in order] + [r for r in order if r not in FIRST]
        spill += pack([fps[r] for r in order], REGIONS.get(s.name, []), obstacles)

    # Second chance: any free space on the board.
    spill = pack(spill, [(1, 1, W - 1, H - 1)], obstacles)

    # Anything that did not fit: park it right of the board for hand placement.
    y = 0.0
    for fp in spill:
        bb = courtyard(fp)
        pos = fp.GetPosition()
        dx, dy = pcbnew.ToMM(pos.x - bb.GetX()), pcbnew.ToMM(pos.y - bb.GetY())
        fp.SetPosition(pcbnew.VECTOR2I(mm(OX + W + 10 + dx), mm(OY + y + dy)))
        y += pcbnew.ToMM(bb.GetHeight()) + GAP

    board.Save(OUT)
    print('wrote %s: %d footprints, %d nets; did not fit (parked right of board): %s'
          % (OUT, len(fps), len(nets), ' '.join(f.GetReference() for f in spill) or 'none'))


if __name__ == '__main__':
    main()
