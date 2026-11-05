"""LCSC lookup via jlcsearch.tscircuit.com (public JLC parts index), cached.

Usage: /usr/bin/python3 lcsc.py "<search text>" [package]
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lcsc_cache.json')


def _load():
    try:
        with open(CACHE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def search(text, limit=30):
    cache = _load()
    if text in cache:
        return cache[text]
    url = 'https://jlcsearch.tscircuit.com/components/list.json?' + urllib.parse.urlencode(
        {'search': text, 'limit': limit})
    for attempt in range(8):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                d = json.load(r)
        except Exception as e:      # noqa: BLE001 - network, retry
            d = {'error': str(e)}
        if 'components' in d:
            cache[text] = d['components']
            with open(CACHE, 'w') as f:
                json.dump(cache, f, indent=0, sort_keys=True)
            time.sleep(1.5)
            return d['components']
        time.sleep(5 + 5 * attempt)
    raise RuntimeError('lookup failed: %s (%s)' % (text, d))


def best(text, package=None, must=(), avoid=()):
    rows = search(text)
    out = []
    for c in rows:
        desc = (c.get('description') or '') + ' ' + c.get('mfr', '')
        if package and c.get('package') != package:
            continue
        if any(m not in desc for m in must) or any(a in desc for a in avoid):
            continue
        if not c.get('stock'):
            continue
        out.append(c)
    out.sort(key=lambda c: (not c.get('is_basic'), not c.get('is_preferred'), -c.get('stock', 0)))
    return out


if __name__ == '__main__':
    for c in best(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)[:8]:
        print('C%-9s %-28s %-12s stock %-8s %s %s' % (c['lcsc'], c['mfr'][:28], c['package'], c['stock'],
              'BASIC' if c.get('is_basic') else ('pref' if c.get('is_preferred') else ''), c['description'][:70]))
