# -*- coding: utf-8 -*-
"""
O teste fora da amostra que a base nova permite.

Todos os filtros, cortes e candidatos dos estudos anteriores foram
escolhidos olhando a base ANTIGA -- WINFUT_20PI.csv, 26 pregoes, de
06/08 a 11/09/2026. A base nova (WINFUT_20PI_Robo.csv) vai de 06/03 a
14/09/2026 e CONTEM a antiga. Entao ela se divide em tres blocos:

  antes     06/03 a 05/08   nunca visto quando as regras foram feitas
  original  06/08 a 11/09   a amostra em que as regras foram escolhidas
  depois    12/09 em diante tambem nunca visto (poucos pregoes)

"Fora da amostra" = antes + depois. E o unico teste de verdade das regras
antigas: se um corte so funciona no bloco original, ele era ajuste.
"""
import numpy as np
import pandas as pd

ORIG_INI = pd.Timestamp('2026-08-06')
ORIG_FIM = pd.Timestamp('2026-09-11')          # inclusive
BLOCOS = ('antes', 'original', 'depois')
ROT_BLOCO = {'antes': 'Antes (06/03 a 05/08)', 'original': 'Amostra original (06/08 a 11/09)',
             'depois': 'Depois (12/09 em diante)', 'fora': 'Fora da amostra original'}


def bloco(datas):
    """'antes' / 'original' / 'depois' para cada data."""
    dia = pd.to_datetime(pd.Series(datas)).dt.normalize().to_numpy()
    return np.where(dia < ORIG_INI.to_datetime64(), 'antes',
                    np.where(dia <= ORIG_FIM.to_datetime64(), 'original', 'depois'))


def _res(p):
    p = np.asarray(p, dtype=float)
    p = p[~np.isnan(p)]
    if len(p) == 0:
        return dict(n=0, ev=None, wr=None, pts=0.0, t=None)
    s = p.std(ddof=1) if len(p) > 1 else 0.0
    return dict(n=int(len(p)), ev=float(p.mean()), wr=float((p > 0).mean() * 100),
                pts=float(p.sum()),
                t=float(p.mean() / (s / np.sqrt(len(p)))) if s > 0 else None)


def por_bloco(t, col_data='data', col_pts='pts'):
    """Resumo (n, EV, acerto, total, t) em cada bloco e no 'fora' (antes+depois)."""
    if 'aceito' in t.columns:
        t = t[t['aceito']]
    b = bloco(t[col_data])
    p = t[col_pts].to_numpy(dtype=float)
    out = {k: _res(p[b == k]) for k in BLOCOS}
    out['fora'] = _res(p[b != 'original'])
    out['total'] = _res(p)
    return out


def por_mes(t, col_data='data', col_pts='pts'):
    """EV por mes-calendario: o periodo tem regimes diferentes."""
    if 'aceito' in t.columns:
        t = t[t['aceito']]
    m = pd.to_datetime(t[col_data]).dt.strftime('%Y-%m').to_numpy()
    p = t[col_pts].to_numpy(dtype=float)
    return [dict(mes=k, **_res(p[m == k])) for k in sorted(set(m))]


def regime(d):
    """Contexto de mercado de cada mes: variacao do fechamento, em pontos."""
    x = d.assign(mes=d['data'].dt.strftime('%Y-%m'))
    g = x.groupby('mes')
    return [dict(mes=k, abre=float(v['o'].iat[0]), fecha=float(v['c'].iat[-1]),
                 var=float(v['c'].iat[-1] - v['o'].iat[0]),
                 maxima=float(v['h'].max()), minima=float(v['l'].min()),
                 dias=int(v['dia'].nunique()), barras=int(len(v)))
            for k, v in g]


def linha_txt(r):
    if not r['n']:
        return '   -'
    t = '' if r['t'] is None else f"t {r['t']:+5.2f}"
    return f"n={r['n']:5d} EV {r['ev']:+6.1f} acerto {r['wr']:4.1f}% {t}"
