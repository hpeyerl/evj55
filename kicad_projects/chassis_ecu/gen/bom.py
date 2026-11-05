"""Write a JLCPCB assembly BOM (../chassis_ecu_bom_jlc.csv) from the definition.

Columns: Comment, Designator, Footprint, LCSC.  Excludes DNP parts, power flags,
test points, solder jumpers and parts marked JLC = hand-solder.
"""
import collections
import csv
import os

import chassis_ecu

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'chassis_ecu_bom_jlc.csv')


def main():
    b = chassis_ecu.build()
    rows = collections.OrderedDict()
    skipped, missing = [], []
    for s in b.sheets:
        for p in s.parts:
            if isinstance(p, tuple) or p.ref.startswith('#'):
                continue
            if p.dnp or 'JLC' in p.fields or p.lib_id.split(':')[1] in ('TestPoint', 'SolderJumper_2_Open') \
                    or p.lib_id.startswith('Connector_Generic:'):
                skipped.append(p.ref)
                continue
            lc = p.fields.get('LCSC', '')
            if not lc:
                missing.append('%s (%s)' % (p.ref, p.value))
            fp = p.footprint.split(':')[-1] if p.footprint else ''
            k = (p.value, fp, lc)
            rows.setdefault(k, []).append(p.ref)
    with open(OUT, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC'])
        for (v, fp, lc), refs in rows.items():
            w.writerow([v, ','.join(refs), fp, lc])
    n = sum(len(r) for r in rows.values())
    print('%d BOM lines, %d placements; not assembled: %s' % (len(rows), n, ' '.join(skipped)))
    print('no LCSC: %s' % (', '.join(missing) or 'none'))


if __name__ == '__main__':
    main()
