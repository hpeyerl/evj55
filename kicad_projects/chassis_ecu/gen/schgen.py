"""Generate KiCad schematics with real library symbols.

Every symbol pin gets a short wire stub ending in a net label (or a power
symbol, or a no-connect).  Connectivity is by label name, so the layout only
has to be readable, not routed.  Verify the result with kicad-cli (ERC and
netlist export); see build.py.
"""
import copy
import os
import uuid as _uuid

from sexp import Sym, dump, find, findall, head, parse

PROJECT = 'chassis_ecu'
STUB = 2.54
GRID = 1.27
LIB_DIRS = [
    '/usr/share/kicad/symbols',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'),
]
PCM_DIR = os.path.expanduser('~/.local/share/kicad/10.0/3rdparty/symbols')
POWER_NETS = {
    'GND': 'power:GND',
    '+3V3': 'power:+3V3',
}

_ns = _uuid.UUID('6b1f3c2e-2f0b-4d7e-9a51-0c3a6e1d9b7a')


def uid(*parts):
    """Deterministic UUID, so regenerating does not churn the files."""
    return str(_uuid.uuid5(_ns, '/'.join(str(p) for p in parts)))


def snap(v):
    return round(round(v / GRID) * GRID, 4)


# --- library access ---------------------------------------------------------

_lib_cache = {}


def _lib_path(lib):
    for d in LIB_DIRS:
        p = os.path.join(d, lib + '.kicad_sym')
        if os.path.exists(p):
            return p
    if lib.startswith('PCM_'):
        name = lib[4:] + '.kicad_sym'
        for sub in os.listdir(PCM_DIR):
            p = os.path.join(PCM_DIR, sub, name)
            if os.path.exists(p):
                return p
    raise FileNotFoundError(lib)


def _load_lib(lib):
    if lib not in _lib_cache:
        with open(_lib_path(lib)) as f:
            tree = parse(f.read())[0]
        _lib_cache[lib] = {x[1]: x for x in findall(tree, 'symbol')}
    return _lib_cache[lib]


def lib_symbol(lib_id):
    """Return a flattened copy of the library symbol, renamed to lib_id."""
    lib, name = lib_id.split(':', 1)
    syms = _load_lib(lib)
    s = copy.deepcopy(syms[name])
    ext = find(s, 'extends')
    if ext:
        parent = copy.deepcopy(syms[ext[1]])
        pname = parent[1]
        props = [x for x in s if head(x) == 'property']
        keep = [x for x in parent[2:] if head(x) not in ('property',)]
        for sub in keep:
            if head(sub) == 'symbol':
                sub[1] = sub[1].replace(pname, name, 1)
        s = [Sym('symbol'), name] + [x for x in s[2:] if head(x) != 'extends' and head(x) != 'property'] \
            + props + [x for x in keep if head(x) == 'symbol' or head(x) not in [head(y) for y in s]]
    s[1] = lib_id
    return s


def sym_pins(libsym, unit=1):
    """List of dicts: number, name, x, y, rot, type, hidden; for one unit."""
    base = libsym[1].split(':', 1)[1]
    pins = []
    for sub in findall(libsym, 'symbol'):
        sname = sub[1]
        u, style = sname.rsplit('_', 2)[-2:]
        if int(style) not in (0, 1) or int(u) not in (0, unit):
            continue
        for p in findall(sub, 'pin'):
            at = find(p, 'at')
            pins.append({
                'type': str(p[1]),
                'number': find(p, 'number')[1],
                'name': find(p, 'name')[1],
                'x': float(at[1]), 'y': float(at[2]),
                'rot': int(float(at[3])) if len(at) > 3 else 0,
                'hidden': any(x == Sym('hide') for x in p) or
                          any(head(x) == 'hide' and x[1] == Sym('yes') for x in p if isinstance(x, list)),
            })
    return pins


def sym_bbox(libsym, unit=1):
    xs, ys = [], []
    for p in sym_pins(libsym, unit):
        xs.append(p['x'])
        ys.append(p['y'])
    base = libsym[1].split(':', 1)[1]
    for sub in findall(libsym, 'symbol'):
        for r in findall(sub, 'rectangle'):
            st, en = find(r, 'start'), find(r, 'end')
            xs += [float(st[1]), float(en[1])]
            ys += [float(st[2]), float(en[2])]
    if not xs:
        return (-2.54, -2.54, 2.54, 2.54)
    return (min(xs), -max(ys), max(xs), -min(ys))   # schematic coords (y down)


def anchor(lib_id, pin, pt, rot=0, mirror=False, unit=1):
    """Symbol position that puts the end of pin's stub at pt."""
    for p in sym_pins(lib_symbol(lib_id), unit):
        if pin in (p['number'], p['name']):
            ox, oy = Board._xf(p['x'], p['y'], rot, mirror)
            dx, dy = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}[(p['rot'] + rot) % 360]
            if mirror == 'y':
                dx = -dx
            elif mirror:
                dy = -dy
            return (snap(pt[0] - ox - dx * STUB), snap(pt[1] - oy - dy * STUB))
    raise KeyError('%s has no pin %s' % (lib_id, pin))


# --- schematic model ----------------------------------------------------------

class Part:
    def __init__(self, ref, lib_id, value, nets, footprint='', unit=1,
                 fields=None, dnp=False, nc=(), rot=0, at=None, mirror=False, text=None):
        self.ref, self.lib_id, self.value = ref, lib_id, value
        self.nets = dict(nets)          # pin number or name -> net
        self.footprint = footprint
        self.unit = unit
        self.fields = fields or {}
        self.dnp = dnp
        self.nc = set(nc)               # pin numbers/names left unconnected
        self.rot = rot                  # degrees CCW, used with at=
        self.at = at                    # (x, y) sheet mm: hand-placed, nets drawn as wires
        self.mirror = mirror            # flip top-bottom (KiCad 'mirror x'), after rotation
        self.text = text                # 'above': ref + value stacked above the body


class Sheet:
    def __init__(self, name, filename, page):
        self.name, self.filename, self.page = name, filename, page
        self.parts = []
        self.notes = []                 # (text, x, y)
        self.heads = []                 # (text, x, y)
        self.taps = []                  # (net, x, y, d)
        self.uuid = uid('sheet', filename)
        self.paper = 'A2'

    def add(self, *a, **k):
        p = Part(*a, **k)
        self.parts.append(p)
        return p

    def note(self, text, x=20.32, y=15.24):
        self.notes.append((text, x, y))

    def head(self, text, x, y):
        """Block title at a fixed position (hand-placed sheets)."""
        self.heads.append((text, x, y))

    def tap(self, net, x, y, d=(-1, 0)):
        """Where a hand-placed sheet shows the net's label; d = direction the label faces."""
        self.taps.append((net, snap(x), snap(y), d))

    def row(self, title=None):
        """Start a new row of parts (one functional block per row)."""
        self.parts.append(('ROW', title))


class Board:
    def __init__(self, title, rev):
        self.title, self.rev = title, rev
        self.sheets = []
        self.root_uuid = uid('root')
        self._pwr = 0

    def sheet(self, name, filename):
        s = Sheet(name, filename, len(self.sheets) + 2)
        self.sheets.append(s)
        return s

    # -- writing --
    def write(self, outdir):
        net_sheets = {}
        for s in self.sheets:
            for p in s.parts:
                if isinstance(p, tuple):
                    continue
                for n in p.nets.values():
                    if n not in POWER_NETS:
                        net_sheets.setdefault(n, set()).add(s.filename)
        self.global_nets = {n for n, ss in net_sheets.items() if len(ss) > 1}
        self._write_root(outdir)
        for s in self.sheets:
            self._write_sheet(outdir, s)

    def _title_block(self, sub=''):
        return [Sym('title_block'), [Sym('title'), self.title + (' - ' + sub if sub else '')],
                [Sym('rev'), self.rev], [Sym('company'), 'EVJ55']]

    def _write_root(self, outdir):
        e = [Sym('kicad_sch'), [Sym('version'), Sym('20230121')], [Sym('generator'), 'eeschema'],
             [Sym('generator_version'), '7.0'], [Sym('uuid'), self.root_uuid],
             [Sym('paper'), 'A4'], self._title_block(), [Sym('lib_symbols')]]
        x, y = 25.4, 30.48
        for s in self.sheets:
            e.append([Sym('sheet'), [Sym('at'), x, y], [Sym('size'), 50.8, 12.7],
                      [Sym('fields_autoplaced'), Sym('yes')],
                      [Sym('stroke'), [Sym('width'), 0.1524], [Sym('type'), Sym('solid')]],
                      [Sym('fill'), [Sym('color'), 0, 0, 0, 0.0]],
                      [Sym('uuid'), s.uuid],
                      [Sym('property'), 'Sheetname', s.name, [Sym('at'), x, y - 0.7116, 0],
                       [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]],
                        [Sym('justify'), Sym('left'), Sym('bottom')]]],
                      [Sym('property'), 'Sheetfile', s.filename, [Sym('at'), x, y + 13.2846, 0],
                       [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]],
                        [Sym('justify'), Sym('left'), Sym('top')]]],
                      [Sym('instances'), [Sym('project'), PROJECT,
                                          [Sym('path'), '/' + self.root_uuid, [Sym('page'), str(s.page)]]]]])
            x += 63.5
            if x > 230:
                x, y = 25.4, y + 25.4
        e.append([Sym('sheet_instances'), [Sym('path'), '/', [Sym('page'), '1']]])
        with open(os.path.join(outdir, PROJECT + '.kicad_sch'), 'w') as f:
            f.write(dump(e) + '\n')

    def _write_sheet(self, outdir, s):
        path = '/%s/%s' % (self.root_uuid, s.uuid)
        libs = {}
        items = []
        conns = []                      # pins of hand-placed parts, wired after placement
        placed = []                     # (symbol, body box, x, y) of hand-placed parts
        boxes = []                      # symbol bodies of hand-placed parts
        # simple row packing for parts without at=
        lines = sum(t.count('\n') + 1 for t, _, _ in s.notes)
        x0, y0 = 25.4, snap(20.32 + 3.0 * lines)
        xmax = {'A3': 400.0, 'A2': 560.0, 'A1': 800.0}[s.paper]
        cx, cy, rowh = x0, y0, 0.0
        heads = list(s.heads)
        for p in s.parts:
            if isinstance(p, tuple):
                if cx > x0:
                    cx, cy, rowh = x0, cy + rowh, 0.0
                if p[1]:
                    heads.append((p[1], cx, cy))
                    cy += 7.62
                continue
            if p.lib_id not in libs:
                libs[p.lib_id] = lib_symbol(p.lib_id)
            ls = libs[p.lib_id]
            if p.at is not None:
                sx, sy = snap(p.at[0]), snap(p.at[1])
                syms, cs, box = self._place(p, ls, sx, sy, path, s)
                items += syms
                conns += cs
                boxes.append(box)
                placed.append((syms[0], box, sx, sy, p.text))
                continue
            bx0, by0, bx1, by1 = sym_bbox(ls, p.unit)
            w = (bx1 - bx0) + 2 * 22.86
            h = (by1 - by0) + 2 * 10.16
            if cx + w > xmax:
                cx, cy, rowh = x0, cy + rowh, 0.0
            sx = snap(cx + 22.86 - bx0)
            sy = snap(cy + 10.16 - by0)
            syms, cs, box = self._place(p, ls, sx, sy, path, s)
            items += syms
            for c in cs:
                items += self._stub(c, path, s)
                items += self._end(c, c['end'], c['d'], path)
            cx += w
            rowh = max(rowh, h)
        for i, (net, x, y, d) in enumerate(s.taps):
            conns.append({'net': net, 'pin': (x, y), 'end': (x, y), 'd': d, 'tap': True,
                          'tag': (s.filename, 'tap', i)})
        items += self._route(conns, boxes, path, s)
        self._text_side(placed)
        for i, (t, x, y) in enumerate(heads):
            items.append([Sym('text'), t, [Sym('at'), x, y, 0],
                          [Sym('effects'), [Sym('font'), [Sym('size'), 2.54, 2.54], Sym('bold')],
                           [Sym('justify'), Sym('left'), Sym('top')]],
                          [Sym('uuid'), uid(s.filename, 'head', i)]])
        for i, (t, x, y) in enumerate(s.notes):
            items.append([Sym('text'), t.replace('"', "'"), [Sym('at'), x, y, 0],
                          [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]],
                           [Sym('justify'), Sym('left'), Sym('top')]],
                          [Sym('uuid'), uid(s.filename, 'note', i)]])
        if self._pwr_libs:
            for lid in self._pwr_libs:
                if lid not in libs:
                    libs[lid] = lib_symbol(lid)
        e = [Sym('kicad_sch'), [Sym('version'), Sym('20230121')], [Sym('generator'), 'eeschema'],
             [Sym('generator_version'), '7.0'], [Sym('uuid'), s.uuid],
             [Sym('paper'), s.paper], self._title_block(s.name),
             [Sym('lib_symbols')] + list(libs.values())] + items
        with open(os.path.join(outdir, s.filename), 'w') as f:
            f.write(dump(e) + '\n')
        self._pwr_libs = set()

    _pwr_libs = set()

    @staticmethod
    def _xf(x, y, rot, mirror=False):
        """Library point (y up) -> sheet offset (y down) for a symbol rotated rot deg CCW."""
        vx, vy = x, -y
        c, sn = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}[rot % 360]
        ox, oy = vx * c + vy * sn, -vx * sn + vy * c
        if mirror == 'y':
            return (-ox, oy)
        return (ox, -oy) if mirror else (ox, oy)

    def _place(self, p, ls, sx, sy, path, s):
        """Symbol s-expr, pin connection records, and body box (sheet coords)."""
        out = []
        pins = sym_pins(ls, p.unit)
        rot = p.rot if p.at is not None else 0
        fp = p.footprint
        if not fp:
            d = [x for x in ls if head(x) == 'property' and x[1] == 'Footprint']
            fp = d[0][2] if d else ''
        props = [('Reference', p.ref), ('Value', p.value), ('Footprint', fp),
                 ('Datasheet', '~')] + list(p.fields.items())
        bx0, by0, bx1, by1 = sym_bbox(ls, p.unit)
        mir = p.mirror if p.at is not None else False
        cs = [self._xf(bx0, -by0, rot, mir), self._xf(bx1, -by1, rot, mir)]
        box = (sx + min(c[0] for c in cs), sy + min(c[1] for c in cs),
               sx + max(c[0] for c in cs), sy + max(c[1] for c in cs))
        sym = [Sym('symbol'), [Sym('lib_id'), p.lib_id], [Sym('at'), sx, sy, rot]] + \
              ([[Sym('mirror'), Sym('y' if mir == 'y' else 'x')]] if mir else []) + [
               [Sym('unit'), p.unit], [Sym('in_bom'), Sym('yes')], [Sym('on_board'), Sym('yes')],
               [Sym('dnp'), Sym('yes' if p.dnp else 'no')], [Sym('uuid'), uid(s.filename, p.ref, p.unit)]]
        vert = box[3] - box[1] > box[2] - box[0]
        for i, (k, v) in enumerate(props):
            hide = i >= 2
            if p.at is None:
                if i == 0:
                    at = [Sym('at'), snap(sx + bx0), snap(sy + by0 - 1.27), 0]
                elif i == 1:
                    at = [Sym('at'), snap(sx + bx0), snap(sy + by1 + 1.27), 0]
                else:
                    at = [Sym('at'), sx, sy, 0]
            elif p.text == 'above':
                at = [Sym('at'), sx, snap(sy - (8.89 if i == 0 else 6.35)), rot % 180]
            elif vert:
                # ref above value, right of the body
                at = [Sym('at'), snap(max(box[2], sx + 3.81) + 1.27), snap(sy + (-1.27 if i == 0 else 1.27)), rot % 180]
            else:
                # ref above the body, value below
                at = [Sym('at'), sx, snap(min(box[1], sy - 1.27) - 1.27 if i == 0 else max(box[3], sy + 1.27) + 1.905), rot % 180]
            if i >= 2:
                at = [Sym('at'), sx, sy, rot % 180]
            jl = Sym('right') if (p.at is not None and rot % 360 == 180) else Sym('left')
            just = [Sym('justify'), jl] if (p.at is None or (vert and not p.text)) else []
            eff = [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]]] + ([just] if just else [])
            if hide:
                eff.append(Sym('hide'))
            sym.append([Sym('property'), k, v, at, eff])
        seen = set()
        for pin in pins:
            if pin['number'] in seen:
                continue
            seen.add(pin['number'])
            sym.append([Sym('pin'), pin['number'], [Sym('uuid'), uid(s.filename, p.ref, 'pin', pin['number'])]])
        sym.append([Sym('instances'), [Sym('project'), PROJECT,
                                       [Sym('path'), path, [Sym('reference'), p.ref], [Sym('unit'), p.unit]]]])
        out.append(sym)

        conns = []
        used = set()
        for pin in pins:
            key = None
            for k in (pin['number'], pin['name']):
                if k in p.nets:
                    key = k
                    break
            ox, oy = self._xf(pin['x'], pin['y'], rot, mir)
            px, py = snap(sx + ox), snap(sy + oy)
            if key is None:
                if pin['number'] in p.nc or pin['name'] in p.nc or pin['type'] == 'no_connect':
                    out.append([Sym('no_connect'), [Sym('at'), px, py],
                                [Sym('uuid'), uid(s.filename, p.ref, 'nc', pin['number'])]])
                    continue
                raise ValueError('%s: pin %s (%s) has no net' % (p.ref, pin['number'], pin['name']))
            used.add(key)
            # stub points away from the body: opposite of the pin direction
            dx, dy = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}[(pin['rot'] + rot) % 360]
            if mir == 'y':
                dx = -dx
            elif mir:
                dy = -dy
            if any(c['pin'] == (px, py) for c in conns):
                continue                # stacked pins (several GND on one point)
            conns.append({'net': p.nets[key], 'pin': (px, py), 'd': (dx, dy),
                          'end': (snap(px + dx * STUB), snap(py + dy * STUB)),
                          'tag': (s.filename, p.ref, pin['number'])})
        missing = set(p.nets) - used
        if missing:
            raise ValueError('%s: net map names unknown pins %s' % (p.ref, sorted(missing)))
        return out, conns, box

    def _text_side(self, placed):
        """Ref/value of a vertical part go on whichever side has no wires next to it."""
        def busy(x0, x1, y0, y1):
            for (u, v, n, _) in self._segs:
                if (max(min(u[0], v[0]), x0) <= min(max(u[0], v[0]), x1) and
                        max(min(u[1], v[1]), y0) <= min(max(u[1], v[1]), y1)):
                    return True
            return False
        for sym, box, sx, sy, txt in placed:
            if txt:
                continue
            props = [x for x in sym if head(x) == 'property' and x[1] in ('Reference', 'Value')]
            if box[3] - box[1] <= box[2] - box[0]:
                continue
            right = max(box[2], sx + 3.81) + 1.27
            if not busy(right - 0.6, right + 8.0, sy - 2.54, sy + 2.54):
                continue
            left = min(box[0], sx - 2.54) - 1.27
            if busy(left - 8.0, left + 0.6, sy - 2.54, sy + 2.54):
                continue
            flip = find(sym, 'at')[3] % 360 == 180
            for pr in props:
                at = find(pr, 'at')
                at[1] = snap(left)
                eff = find(pr, 'effects')
                find(eff, 'justify')[1] = Sym('left' if flip else 'right')

    @staticmethod
    def _wire(a, b, tag):
        return [Sym('wire'), [Sym('pts'), [Sym('xy'), a[0], a[1]], [Sym('xy'), b[0], b[1]]],
                [Sym('stroke'), [Sym('width'), 0], [Sym('type'), Sym('default')]],
                [Sym('uuid'), uid(*tag)]]

    def _stub(self, c, path, s):
        return [self._wire(c['pin'], c['end'], c['tag'] + ('w',))]

    def _end(self, c, pt, d, path, label=True):
        """Power symbol or net label at pt, facing d."""
        net, tag = c['net'], c['tag']
        if net in POWER_NETS:
            return self._power(net, pt[0], pt[1], d[0], d[1], path, tag)
        if not label:
            return []
        ang = {(-1, 0): 180, (1, 0): 0, (0, 1): 270, (0, -1): 90}[d]
        just = Sym('right') if ang in (180, 270) else Sym('left')
        kind = 'global_label' if net in self.global_nets else 'label'
        lab = [Sym(kind), net]
        if kind == 'global_label':
            lab.append([Sym('shape'), Sym('passive')])
        lab += [[Sym('at'), pt[0], pt[1], ang], [Sym('fields_autoplaced'), Sym('yes')],
                [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]], [Sym('justify'), just]],
                [Sym('uuid'), uid(*tag, 'l')]]
        return [lab]

    def _route(self, conns, boxes, path, s):
        """Wire together the pins of each net on hand-placed parts.

        Every pin gets a stub.  Each net grows a tree from its tap (or left-most pin):
        the nearest unconnected stub is joined to the nearest point of the tree with an
        L-shaped wire that touches nothing of another net and avoids symbol bodies.
        A stub that cannot be wired cleanly gets its own label.  Power nets keep a
        power symbol per pin.  Each wired net carries one label, at the tap.
        """
        out = []
        segs = []                       # [a, b, net], wires and stubs
        pts = {}                        # point -> set of nets
        for c in conns:
            if not c.get('tap'):
                segs.append([c['pin'], c['end'], c['net'], 'stub'])
                out += self._stub(c, path, s)
            for q in (c['pin'], c['end']):
                pts.setdefault(q, set()).add(c['net'])
        bynet = {}
        power = []
        for c in conns:
            if c['net'] in POWER_NETS:
                power.append(c)
            else:
                bynet.setdefault(c['net'], []).append(c)

        def on(q, a, b):
            return (min(a[0], b[0]) - 1e-6 <= q[0] <= max(a[0], b[0]) + 1e-6 and
                    min(a[1], b[1]) - 1e-6 <= q[1] <= max(a[1], b[1]) + 1e-6 and
                    abs((b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0])) < 1e-6)

        def clean(a, b, net):
            for q, ns in pts.items():
                if ns - {net} and on(q, a, b):
                    return False
            for (u, v, n, _) in segs:
                if n != net and (on(a, u, v) or on(b, u, v)):
                    return False
            return True

        def hits_body(a, b):
            for (x0, y0, x1, y1) in boxes:
                lo = (max(min(a[0], b[0]), x0 + 0.1), max(min(a[1], b[1]), y0 + 0.1))
                hi = (min(max(a[0], b[0]), x1 - 0.1), min(max(a[1], b[1]), y1 - 0.1))
                if lo[0] <= hi[0] and lo[1] <= hi[1]:
                    return True
            return False

        def psym_box(q, up):
            # symbol plus its value text
            return (q[0] - 1.905, min(q[1], q[1] + up[1] * 5.08) - 0.5,
                    q[0] + 1.905, max(q[1], q[1] + up[1] * 5.08) + 0.5)

        def free(box, net):
            x0, y0, x1, y1 = box
            for q, ns in pts.items():
                if ns - {net} and x0 <= q[0] <= x1 and y0 <= q[1] <= y1:
                    return False
            for (u, v, n, _) in segs:
                if n != net and hits_box(u, v, box):
                    return False
            return True

        def hits_box(a, b, box):
            x0, y0, x1, y1 = box
            return (max(min(a[0], b[0]), x0) <= min(max(a[0], b[0]), x1) and
                    max(min(a[1], b[1]), y0) <= min(max(a[1], b[1]), y1))

        def shapes(e, q):
            # L both ways, then Z (H-V-H and V-H-V) with the jog anywhere on the grid between
            yield [e, (q[0], e[1]), q]
            yield [e, (e[0], q[1]), q]
            for lo, hi, k in ((e[0], q[0], 0), (e[1], q[1], 1)):
                a, b = min(lo, hi), max(lo, hi)
                m = snap(a + 2.54)
                while m < b - 1e-6:
                    if k == 0:
                        yield [e, (m, e[1]), (m, q[1]), q]
                    else:
                        yield [e, (e[0], m), (q[0], m), q]
                    m = snap(m + 2.54)

        def dist(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        def nearest_on(q, a, b):
            return (snap(min(max(q[0], min(a[0], b[0])), max(a[0], b[0]))),
                    snap(min(max(q[1], min(a[1], b[1])), max(a[1], b[1]))))

        wires = []                      # [a, b, net], routed
        # label text: keep power symbols and wires off it
        def lbox(pt, d, net):
            n = 1.05 * len(net) + (3.5 if net in self.global_nets else 1.0)
            x, y = pt
            return {(-1, 0): (x - n, y - 1.2, x, y + 1.2), (1, 0): (x, y - 1.2, x + n, y + 1.2),
                    (0, -1): (x - 1.2, y - n, x + 1.2, y), (0, 1): (x - 1.2, y, x + 1.2, y + n)}[d]
        lboxes = []
        for net, cs in bynet.items():
            for c in cs:
                if c.get('tap') or len(cs) == 1:
                    lboxes.append(lbox(c['end'], c['d'], net))
        bodies = list(boxes)
        boxes += lboxes

        def roomy(box, net):
            if not free(box, net):
                return False
            for (x0, y0, x1, y1) in boxes:
                if x0 < box[2] and box[0] < x1 and y0 < box[3] and box[1] < y1:
                    return False
            return True

        # several same-side pins of one part on one supply: a short bus, one symbol at its end
        byside = {}
        for c in power:
            if c['d'][1] == 0:
                byside.setdefault((c['net'], c['tag'][1], c['d']), []).append(c)
        for (net, ref, d), grp in sorted(byside.items()):
            if len(grp) < 2:
                continue
            grp.sort(key=lambda c: c['end'][1])
            down = net == 'GND'
            done = False
            for k in range(1, 6):
                bx = snap(grp[0]['end'][0] + d[0] * STUB * k)
                legs = [(c['end'], (bx, c['end'][1])) for c in grp]
                y0, y1 = grp[0]['end'][1], grp[-1]['end'][1]
                tip = (bx, snap((y1 + STUB) if down else (y0 - STUB)))
                ys = [c['end'][1] for c in grp]
                legs += [((bx, ya), (bx, yb)) for ya, yb in zip(ys, ys[1:]) if ya != yb]
                legs += [((bx, y1) if down else (bx, y0), tip)]
                if all(clean(u, v, net) and not hits_body(u, v) for u, v in legs) and \
                        roomy(psym_box(tip, (0, 1) if down else (0, -1)), net):
                    done = True
                    break
            if not done:
                continue
            for u, v in legs:
                out.append(self._wire(u, v, grp[0]['tag'] + ('bus', u, v)))
                segs.append([u, v, net, 'w'])
                for pq in (u, v):
                    pts.setdefault(pq, set()).add(net)
            out += self._power(net, tip[0], tip[1], 0, 1 if down else -1, path, grp[0]['tag'])
            boxes.append(psym_box(tip, (0, 1) if down else (0, -1)))
            power = [c for c in power if c not in grp]

        # GND always hangs down, supplies always point up: jog the wire if the pin faces elsewhere
        for c in power:
            net, e, d = c['net'], c['end'], c['d']
            up = (0, 1) if net == 'GND' else (0, -1)
            if d == up:
                legs = []
            else:
                opts = []
                side = [d] if d[1] == 0 else [(1, 0), (-1, 0)]
                for sd in side:
                    for n in (1, 0, 2, 3, 4, 5, 6, 7, 8, 9, 10) if d[1] == 0 else (1, 2, 3):
                        a = (snap(e[0] + sd[0] * STUB * n), e[1])
                        b = (a[0], snap(a[1] + up[1] * STUB))
                        opts.append([(u, v) for u, v in ((e, a), (a, b)) if u != v])
                legs = next((o for o in opts if all(clean(u, v, net) and not hits_body(u, v) for u, v in o)
                             and roomy(psym_box(o[-1][1], up), net)), None)
                if legs is None:
                    # no clean way to turn it upright: symbol in line with the pin
                    out += self._power(net, e[0], e[1], d[0], d[1], path, c['tag'])
                    pts.setdefault(e, set()).add(net)
                    continue
            q = legs[-1][1] if legs else e
            for u, v in legs:
                out.append(self._wire(u, v, c['tag'] + ('jog', u)))
                segs.append([u, v, net, 'w'])
                for pq in (u, v):
                    pts.setdefault(pq, set()).add(net)
            pts.setdefault(q, set()).add(net)
            out += self._power(net, q[0], q[1], up[0], up[1], path, c['tag'])
            boxes.append(psym_box(q, up))
        groups = []
        for net in sorted(bynet, key=lambda n: (-len(bynet[n]), n)):
            taps = [c for c in bynet[net] if c.get('tap')]
            if len(taps) < 2:
                groups.append((net, bynet[net]))
                continue
            isl = {id(t): [t] for t in taps}
            for c in bynet[net]:
                if not c.get('tap'):
                    t = min(taps, key=lambda t: dist(c['end'], t['end']))
                    isl[id(t)].append(c)
            groups += [(net, isl[id(t)]) for t in taps]
        for net, cs in groups:
            taps = [c for c in cs if c.get('tap')]
            root = taps[0] if taps else min(cs, key=lambda c: (c['end'][0], c['end'][1]))
            tree = [root['end']]        # vertices
            progress = False
            tsegs = []                  # indexes into wires
            todo = [c for c in cs if c is not root]
            alone = []
            waiting = []
            while todo or waiting:
                if not todo:
                    if not progress:
                        waiting.sort(key=lambda c: min(dist(c['end'], t) for t in tree))
                        alone.append(waiting.pop(0))
                        tree, tsegs = [alone[-1]['end']], []
                    todo, waiting, progress = waiting, [], False
                    if not todo:
                        break
                def cands(c):
                    e = c['end']
                    qs = set(tree)
                    for i in tsegs:
                        qs.add(nearest_on(e, wires[i][0], wires[i][1]))
                    return sorted(qs, key=lambda q: (dist(e, q), q))
                todo.sort(key=lambda c: (dist(c['end'], cands(c)[0]), c['end']))
                c = todo.pop(0)
                e = c['end']
                done = False
                for q in cands(c):
                    best = None
                    for way in shapes(e, q):
                        legs = [(u, v) for u, v in zip(way, way[1:]) if u != v]
                        if not all(clean(u, v, net) for u, v in legs):
                            continue
                        if any(hits_body(u, v) for u, v in legs):
                            continue
                        score = (len(legs), sum(dist(u, v) for u, v in legs))
                        if best is None or score < best[0]:
                            best = (score, legs)
                    if best is None:
                        continue
                    # split a tree wire that the new branch tees into
                    for i in list(tsegs):
                        u, v = wires[i][0], wires[i][1]
                        if q not in (u, v) and on(q, u, v):
                            wires[i][1] = q
                            wires.append([q, v, net])
                            segs.append([q, v, net, 'w'])
                            tsegs.append(len(wires) - 1)
                            for sg in segs:
                                if sg[0] == u and sg[1] == v and sg[2] == net:
                                    sg[1] = q
                                    break
                            break
                    for u, v in best[1]:
                        wires.append([u, v, net])
                        segs.append([u, v, net, 'w'])
                        tsegs.append(len(wires) - 1)
                        tree += [u, v]
                        for pq in (u, v):
                            pts.setdefault(pq, set()).add(net)
                    done = True
                    break
                if done:
                    progress = True
                else:
                    waiting.append(c)
            hz = [(abs(u[0] - v[0]), min(u[0], v[0]), u[1]) for (u, v, n, _) in segs
                  if n == net and u[1] == v[1] and abs(u[0] - v[0]) >= 5.08]
            if root.get('tap') or alone or (not hz and (net in self.global_nets or len(cs) == 1)):
                out += self._end(root, root['end'], root['d'], path)
            elif not hz:
                pass                    # wired local net, no good spot for its name
            else:
                ln, x0, y0 = max(hz, key=lambda h: (h[0], -h[2], -h[1]))
                kind = 'global_label' if net in self.global_nets else 'label'
                if kind == 'global_label':
                    out += self._end(root, root['end'], root['d'], path)
                else:
                    out.append([Sym('label'), net, [Sym('at'), snap(x0 + 1.27), y0, 0],
                                [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]],
                                 [Sym('justify'), Sym('left'), Sym('bottom')]],
                                [Sym('uuid'), uid(*root['tag'], 'l')]])
            for c in alone:
                out += self._end(c, c['end'], c['d'], path)
        self._segs = segs
        for k, (u, v, net) in enumerate(wires):
            out.append(self._wire(u, v, (s.filename, 'route', net, u, v)))
        # junction dots where three or more wire ends meet
        ends = {}
        for (u, v, n, _) in segs:
            for q in (u, v):
                ends[q] = ends.get(q, 0) + 1
        for q, nn in sorted(ends.items()):
            if nn >= 3:
                out.append([Sym('junction'), [Sym('at'), q[0], q[1]], [Sym('diameter'), 0],
                            [Sym('color'), 0, 0, 0, 0], [Sym('uuid'), uid(s.filename, 'junc', q)]])
        return out

    def _power(self, net, x, y, dx, dy, path, tag):
        lid = POWER_NETS[net]
        self._pwr_libs.add(lid)
        self._pwr += 1
        ref = '#PWR%03d' % self._pwr
        # GND hangs down, +3V3 points up; rotate so the symbol sits beyond the stub
        if net == 'GND':
            rot = {(0, 1): 0, (0, -1): 180, (-1, 0): 270, (1, 0): 90}[(dx, dy)]
        else:
            rot = {(0, -1): 0, (0, 1): 180, (-1, 0): 90, (1, 0): 270}[(dx, dy)]
        vo = 3.81 if net == 'GND' else 5.08
        vj = {(-1, 0): [[Sym('justify'), Sym('right')]], (1, 0): [[Sym('justify'), Sym('left')]]}.get((dx, dy), [])
        return [[Sym('symbol'), [Sym('lib_id'), lid], [Sym('at'), x, y, rot], [Sym('unit'), 1],
                 [Sym('in_bom'), Sym('yes')], [Sym('on_board'), Sym('yes')], [Sym('dnp'), Sym('no')],
                 [Sym('uuid'), uid(*tag, 'pwr')],
                 [Sym('property'), 'Reference', ref, [Sym('at'), x, y, 0],
                  [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]], Sym('hide')]],
                 [Sym('property'), 'Value', net,
                  [Sym('at'), snap(x + dx * vo), snap(y + dy * vo), rot % 180],
                  [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]]] + vj],
                 [Sym('property'), 'Footprint', '', [Sym('at'), x, y, 0],
                  [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]], Sym('hide')]],
                 [Sym('property'), 'Datasheet', '', [Sym('at'), x, y, 0],
                  [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]], Sym('hide')]],
                 [Sym('pin'), '1', [Sym('uuid'), uid(*tag, 'pwrpin')]],
                 [Sym('instances'), [Sym('project'), PROJECT,
                                     [Sym('path'), path, [Sym('reference'), ref], [Sym('unit'), 1]]]]]]
