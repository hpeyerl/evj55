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


# --- schematic model ----------------------------------------------------------

class Part:
    def __init__(self, ref, lib_id, value, nets, footprint='', unit=1,
                 fields=None, dnp=False, nc=(), rot=0):
        self.ref, self.lib_id, self.value = ref, lib_id, value
        self.nets = dict(nets)          # pin number or name -> net
        self.footprint = footprint
        self.unit = unit
        self.fields = fields or {}
        self.dnp = dnp
        self.nc = set(nc)               # pin numbers/names left unconnected
        self.rot = rot


class Sheet:
    def __init__(self, name, filename, page):
        self.name, self.filename, self.page = name, filename, page
        self.parts = []
        self.notes = []                 # (text, x, y)
        self.uuid = uid('sheet', filename)
        self.paper = 'A2'

    def add(self, *a, **k):
        p = Part(*a, **k)
        self.parts.append(p)
        return p

    def note(self, text, x=20.32, y=15.24):
        self.notes.append((text, x, y))

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
        # simple row packing
        lines = sum(t.count('\n') + 1 for t, _, _ in s.notes)
        x0, y0 = 25.4, snap(20.32 + 3.0 * lines)
        xmax = {'A2': 560.0, 'A1': 800.0}[s.paper]
        cx, cy, rowh = x0, y0, 0.0
        heads = []
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
            bx0, by0, bx1, by1 = sym_bbox(ls, p.unit)
            w = (bx1 - bx0) + 2 * 22.86
            h = (by1 - by0) + 2 * 10.16
            if cx + w > xmax:
                cx, cy, rowh = x0, cy + rowh, 0.0
            sx = snap(cx + 22.86 - bx0)
            sy = snap(cy + 10.16 - by0)
            items += self._place(p, ls, sx, sy, path, s)
            cx += w
            rowh = max(rowh, h)
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

    def _place(self, p, ls, sx, sy, path, s):
        out = []
        pins = sym_pins(ls, p.unit)
        props = [('Reference', p.ref), ('Value', p.value), ('Footprint', p.footprint),
                 ('Datasheet', '~')] + list(p.fields.items())
        bx0, by0, bx1, by1 = sym_bbox(ls, p.unit)
        sym = [Sym('symbol'), [Sym('lib_id'), p.lib_id], [Sym('at'), sx, sy, 0],
               [Sym('unit'), p.unit], [Sym('in_bom'), Sym('yes')], [Sym('on_board'), Sym('yes')],
               [Sym('dnp'), Sym('yes' if p.dnp else 'no')], [Sym('uuid'), uid(s.filename, p.ref, p.unit)]]
        for i, (k, v) in enumerate(props):
            hide = i >= 2
            if i == 0:
                at = [Sym('at'), snap(sx + bx0), snap(sy + by0 - 1.27), 0]
            elif i == 1:
                at = [Sym('at'), snap(sx + bx0), snap(sy + by1 + 1.27), 0]
            else:
                at = [Sym('at'), sx, sy, 0]
            eff = [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]], [Sym('justify'), Sym('left')]]
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

        used = set()
        for pin in pins:
            key = None
            for k in (pin['number'], pin['name']):
                if k in p.nets:
                    key = k
                    break
            px, py = snap(sx + pin['x']), snap(sy - pin['y'])
            if key is None:
                if pin['number'] in p.nc or pin['name'] in p.nc or pin['type'] == 'no_connect':
                    out.append([Sym('no_connect'), [Sym('at'), px, py],
                                [Sym('uuid'), uid(s.filename, p.ref, 'nc', pin['number'])]])
                    continue
                raise ValueError('%s: pin %s (%s) has no net' % (p.ref, pin['number'], pin['name']))
            used.add(key)
            net = p.nets[key]
            # stub points away from the body: opposite of the pin direction
            dx, dy = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}[pin['rot'] % 360]
            ex, ey = snap(px + dx * STUB), snap(py + dy * STUB)
            tag = (s.filename, p.ref, pin['number'])
            out.append([Sym('wire'), [Sym('pts'), [Sym('xy'), px, py], [Sym('xy'), ex, ey]],
                        [Sym('stroke'), [Sym('width'), 0], [Sym('type'), Sym('default')]],
                        [Sym('uuid'), uid(*tag, 'w')]])
            if net in POWER_NETS:
                out += self._power(net, ex, ey, dx, dy, path, tag)
            else:
                ang = {(-1, 0): 180, (1, 0): 0, (0, 1): 270, (0, -1): 90}[(dx, dy)]
                just = Sym('right') if ang in (180, 270) else Sym('left')
                kind = 'global_label' if net in self.global_nets else 'label'
                lab = [Sym(kind), net]
                if kind == 'global_label':
                    lab.append([Sym('shape'), Sym('passive')])
                lab += [[Sym('at'), ex, ey, ang], [Sym('fields_autoplaced'), Sym('yes')],
                        [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]], [Sym('justify'), just]],
                        [Sym('uuid'), uid(*tag, 'l')]]
                out.append(lab)
        missing = set(p.nets) - used
        if missing:
            raise ValueError('%s: net map names unknown pins %s' % (p.ref, sorted(missing)))
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
        return [[Sym('symbol'), [Sym('lib_id'), lid], [Sym('at'), x, y, rot], [Sym('unit'), 1],
                 [Sym('in_bom'), Sym('yes')], [Sym('on_board'), Sym('yes')], [Sym('dnp'), Sym('no')],
                 [Sym('uuid'), uid(*tag, 'pwr')],
                 [Sym('property'), 'Reference', ref, [Sym('at'), x, y, 0],
                  [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]], Sym('hide')]],
                 [Sym('property'), 'Value', net, [Sym('at'), x, y + 3.81, 0],
                  [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]]]],
                 [Sym('property'), 'Footprint', '', [Sym('at'), x, y, 0],
                  [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]], Sym('hide')]],
                 [Sym('property'), 'Datasheet', '', [Sym('at'), x, y, 0],
                  [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]], Sym('hide')]],
                 [Sym('pin'), '1', [Sym('uuid'), uid(*tag, 'pwrpin')]],
                 [Sym('instances'), [Sym('project'), PROJECT,
                                     [Sym('path'), path, [Sym('reference'), ref], [Sym('unit'), 1]]]]]]
