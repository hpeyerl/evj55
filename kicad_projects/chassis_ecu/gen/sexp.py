"""Minimal S-expression reader/writer for KiCad files."""
import re

_TOK = re.compile(r'\s*(?:(\()|(\))|("(?:[^"\\]|\\.)*")|([^\s()"]+))')


class Sym(str):
    """Bare (unquoted) atom."""


def parse(text):
    stack = [[]]
    pos = 0
    n = len(text)
    while pos < n:
        m = _TOK.match(text, pos)
        if not m:
            if text[pos:].strip() == '':
                break
            raise ValueError('parse error at %d' % pos)
        pos = m.end()
        if m.group(1):
            stack.append([])
        elif m.group(2):
            e = stack.pop()
            stack[-1].append(e)
        elif m.group(3) is not None:
            stack[-1].append(m.group(3)[1:-1].replace('\\"', '"').replace('\\\\', '\\'))
        elif m.group(4) is not None:
            stack[-1].append(Sym(m.group(4)))
    return stack[0]


def q(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'


def dump(e, ind=0):
    if not isinstance(e, list):
        if isinstance(e, Sym):
            return str(e)
        if isinstance(e, (int, float)):
            return fmt_num(e)
        return q(e)
    if not e:
        return '()'
    simple = all(not isinstance(x, list) for x in e)
    if simple:
        return '(' + ' '.join(dump(x) for x in e) + ')'
    out = '(' + dump(e[0])
    for x in e[1:]:
        if isinstance(x, list):
            out += '\n' + '  ' * (ind + 1) + dump(x, ind + 1)
        else:
            out += ' ' + dump(x)
    return out + ')'


def fmt_num(v):
    if isinstance(v, int):
        return str(v)
    s = ('%.4f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def head(e):
    return e[0] if isinstance(e, list) and e else None


def find(e, name):
    for x in e:
        if head(x) == name:
            return x
    return None


def findall(e, name):
    return [x for x in e if head(x) == name]
