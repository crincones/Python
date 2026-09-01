# -*- coding: utf-8 -*-
"""Valida alinhamento entre WIN$N M1 e o arquivo de ajustes."""
import csv
import collections
import os

BASE = os.path.dirname(os.path.abspath(__file__))
M1 = os.path.join(BASE, 'dados', 'WIN_N_M1.csv')
AJ = os.path.join(BASE, 'dados', 'Ajustes-WINFUT-NoDiv-NoSplits.2026-08-28.csv')


def carrega_m1():
    dias = collections.defaultdict(list)
    horas = collections.Counter()
    with open(M1, encoding='utf-8') as f:
        rd = csv.reader(f, delimiter='\t')
        next(rd)
        for r in rd:
            if len(r) < 6:
                continue
            d = r[0].replace('.', '-')
            hm = r[1][:5]
            horas[hm[:2]] += 1
            dias[d].append((hm, float(r[2]), float(r[3]), float(r[4]), float(r[5])))
    return dias, horas


def carrega_aj():
    aj = {}
    with open(AJ, encoding='utf-8-sig') as f:
        rd = csv.reader(f, delimiter='\t')
        next(rd)
        for r in rd:
            if len(r) < 6:
                continue
            dd, mm, yy = r[0].split(' ')[0].split('/')
            n = lambda s: float(s.replace('.', '').replace(',', '.'))
            aj['%s-%s-%s' % (yy, mm, dd)] = dict(o=n(r[1]), h=n(r[2]), l=n(r[3]),
                                                 c=n(r[4]), ajuste=n(r[5]))
    return aj


def main():
    m1, horas = carrega_m1()
    aj = carrega_aj()
    print('M1: %d dias, %s a %s' % (len(m1), min(m1), max(m1)))
    print('Ajustes: %d dias, %s a %s' % (len(aj), min(aj), max(aj)))
    print('Distribuicao por hora:', sorted(horas.items()))

    comuns = sorted(set(m1) & set(aj))
    print('Dias em comum: %d (%s a %s)' % (len(comuns), comuns[0], comuns[-1]))

    difs_o, difs_h, difs_l, difs_c = [], [], [], []
    piores = []
    for d in comuns:
        b = sorted(m1[d])
        o = b[0][1]
        h = max(x[2] for x in b)
        l = min(x[3] for x in b)
        c = b[-1][4]
        a = aj[d]
        do, dh, dl, dc = o - a['o'], h - a['h'], l - a['l'], c - a['c']
        difs_o.append(do); difs_h.append(dh); difs_l.append(dl); difs_c.append(dc)
        piores.append((max(abs(do), abs(dh), abs(dl), abs(dc)), d, do, dh, dl, dc))

    def stat(nome, v):
        z = sum(1 for x in v if x == 0)
        print('  %s: iguais %d/%d (%.1f%%) | media %.1f | max abs %.0f'
              % (nome, z, len(v), 100.0 * z / len(v), sum(v) / len(v), max(abs(x) for x in v)))

    print('Diferencas M1-agregado vs arquivo de ajustes:')
    stat('open ', difs_o)
    stat('high ', difs_h)
    stat('low  ', difs_l)
    stat('close', difs_c)

    piores.sort(reverse=True)
    print('10 maiores divergencias:')
    for p, d, do, dh, dl, dc in piores[:10]:
        print('   %s  dO=%+.0f dH=%+.0f dL=%+.0f dC=%+.0f' % (d, do, dh, dl, dc))

    # tick size
    mult = set()
    for d in comuns[-200:]:
        for hm, o, h, l, c in m1[d]:
            for p in (o, h, l, c):
                mult.add(p % 5)
    print('Residuos mod 5 (ultimos 200 dias):', sorted(mult)[:5])

    # gaps abertura x ajuste
    gaps = []
    for d in comuns:
        b = sorted(m1[d])
        gaps.append((abs(b[0][1] - aj[d]['ajuste']), d, b[0][1] - aj[d]['ajuste']))
    gaps.sort(reverse=True)
    print('Maiores |abertura - ajuste| (candidatos a rolagem):')
    for g, d, s in gaps[:12]:
        print('   %s  %+.0f' % (d, s))
    n2000 = sum(1 for g, d, s in gaps if g > 2000)
    print('Dias com |gap| > 2000: %d de %d' % (n2000, len(gaps)))


if __name__ == '__main__':
    main()
