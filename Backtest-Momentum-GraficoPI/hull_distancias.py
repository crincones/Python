# -*- coding: utf-8 -*-
"""
A separacao entre a Hull 50 e (1) a EMA 21, (2) as bandas de Keltner,
serve de filtro?

    python hull_distancias.py        -> saida/hull_distancias.json + console

Parte do mesmo conjunto de sinais de hull_contra.py e hull_inclinacao.py.

AVISO QUE MUDA A LEITURA: as bandas de Keltner do projeto sao
EMA 21 +/- 2 ATR 21. Entao, medida em ATR e no sentido do trade,

    distancia da Hull a banda a favor  =  2  -  distancia da Hull a EMA

-- conferido numericamente, igual em todos os sinais. "Hull perto da
banda" e "Hull longe da EMA" sao a MESMA variavel. As duas perguntas so
se separam quando a distancia e medida em PONTOS (o ATR muda ao longo do
dia) ou sem sinal (so a proximidade, de qualquer lado). Por isso o estudo
mede:

  sep_atr     (Hull - EMA) no sentido do trade, em ATR.
              Positivo = Hull do lado do trade (acima da EMA na compra).
              Faixas FIXAS, com leitura de canal:
                < 0      Hull do lado errado da EMA
                0 a 1    Hull entre a EMA e o meio do canal
                1 a 2    Hull entre o meio do canal e a banda a favor
                > 2      Hull alem da banda a favor
  sep_pts     o mesmo em pontos, quintis
  sep_abs     |Hull - EMA| em ATR, sem sinal (a hipotese "colada = consolidacao")
  banda_pts   distancia da Hull a banda a favor, em pontos, quintis
              (pequena = Hull perto da banda = hipotese de exaustao)
  colada      barras seguidas, ate o sinal, com |Hull - EMA| < 0,25 ATR
              (a hipotese "Hull muito tempo perto da EMA"), faixas fixas
"""
import io
import json
import os
import sys

import numpy as np
import pandas as pd

import engine as E
import pavio_contra as P
import hull_contra as HC

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')

Q5 = ['Q1 (menor)', 'Q2', 'Q3', 'Q4', 'Q5 (maior)']
MEDIDAS = {
    'sep_atr': dict(rot='Hull - EMA 21, em ATR, no sentido do trade (= 2 - distancia a banda)',
                    cortes=[0, 1, 2],
                    rotulos=['Hull do lado errado da EMA', 'EMA ate meio canal (0-1 ATR)',
                             'meio canal ate banda (1-2 ATR)', 'alem da banda (> 2 ATR)']),
    'sep_fino': dict(rot='Hull - EMA 21, em ATR, faixas finas (gradiente)',
                     cortes=[-1, -0.5, 0, 0.5, 1, 2],
                     rotulos=['< -1 ATR', '-1 a -0,5', '-0,5 a 0', '0 a 0,5', '0,5 a 1', '1 a 2', '> 2 ATR']),
    'sep_pts': dict(rot='Hull - EMA 21, em pontos, no sentido do trade', cortes=None, rotulos=Q5),
    'sep_abs': dict(rot='|Hull - EMA 21| em ATR, sem sinal', cortes=None, rotulos=Q5),
    'banda_pts': dict(rot='Distancia da Hull a banda a favor, em pontos', cortes=None, rotulos=Q5),
    'colada': dict(rot='Barras seguidas com Hull colada na EMA (< 0,25 ATR)',
                   cortes=[0.5, 2.5, 5.5, 10.5],
                   rotulos=['0 (nao colada)', '1-2 barras', '3-5 barras', '6-10 barras', '11+ barras']),
}
CONTINUAS = ('sep_atr', 'sep_pts', 'sep_abs', 'banda_pts')

_buf = io.StringIO()


def p(*a, **k):
    print(*a, **k)
    print(*a, **k, file=_buf)


def linha(b):
    if not b['n']:
        return 'n=   0'
    tt = ' / '.join('   -  ' if v is None else f'{v:+6.1f}' for v in b['ev_terco'])
    c = '  -  ' if b['compra'] is None else f"{b['compra']:+6.1f}"
    v = '  -  ' if b['venda'] is None else f"{b['venda']:+6.1f}"
    pc = '' if not b.get('sorteio') else f"pct {b['sorteio']['percentil']:3.0f}"
    return (f"n={b['n']:4d}  EV {b['ev']:+6.1f}  acerto {b['wr']:4.1f}%  tercos {tt}  "
            f"C {c} V {v}  {pc}")


def main():
    d = E.indicadores(E.carrega())
    dias = sorted(d['dia'].unique())
    hu, em, at, ks, ki = (d[k].to_numpy() for k in ('hma', 'ema', 'atr', 'kc_sup', 'kc_inf'))

    u = P.universo(d)
    for per in HC.HULL_TESTE:
        u = HC.anexa_hull(u, d, per, f'hull{per}')
    u = u[u['hull80_valida'] & u['hull50'] & u['n_fav'].between(2, 4)].reset_index(drop=True)
    i = u['i'].to_numpy(); ld = u['lado'].to_numpy()
    u['sep_pts'] = (hu[i] - em[i]) * ld
    u['sep_atr'] = u['sep_pts'] / at[i]
    u['sep_fino'] = u['sep_atr']
    u['sep_abs'] = u['sep_atr'].abs()
    banda = np.where(ld > 0, ks[i], ki[i])
    u['banda_pts'] = (banda - hu[i]) * ld
    col = np.zeros(len(u), dtype=int)
    colado = np.abs(hu - em) / at < 0.25
    for k, ii in enumerate(i):
        c = 0
        while ii - c >= 0 and c < 60 and colado[ii - c]:
            c += 1
        col[k] = c
    u['colada'] = col
    u['cand'] = (u['n_fav'] <= 3) & (u['pav_outro_pct'] <= 10)

    folga_atr = u['banda_pts'] / at[i]
    identidade = float(np.abs(folga_atr + u['sep_atr'] - 2).max())

    p('=' * 74)
    p('HULL 50 x EMA 21 e x BANDAS DE KELTNER')
    p('=' * 74)
    p(f"sinais Hull + 2-4: {len(u)}   candidato: {int(u['cand'].sum())}")
    p(f"identidade folga_banda_atr = 2 - sep_atr: erro maximo {identidade:.2e}")
    p(f"Hull do lado errado da EMA: {(u['sep_atr'] < 0).mean() * 100:.0f}% dos sinais;  "
      f"alem da banda: {(u['sep_atr'] > 2).mean() * 100:.0f}%;  colada >= 1 barra: "
      f"{(u['colada'] > 0).mean() * 100:.0f}%")
    p(f"correlacoes: sep_pts x sep_atr {np.corrcoef(u['sep_pts'], u['sep_atr'])[0, 1]:.2f}  "
      f"banda_pts x sep_pts {np.corrcoef(u['banda_pts'], u['sep_pts'])[0, 1]:.2f}  "
      f"sep_abs x colada {np.corrcoef(u['sep_abs'], u['colada'])[0, 1]:.2f}")

    res = {}
    for ent in HC.ENTRADAS:
        for ges, gg in HC.GESTOES.items():
            t = E.executa(d, u, ent, gg)
            t, c1, c2 = P.marca_tercos(t, dias)
            res[(ent, ges)] = t

    S = dict(medidas={k: v['rot'] for k, v in MEDIDAS.items()}, continuas=list(CONTINUAS),
             rot_gestao=HC.ROT_GESTAO, rot_entrada=HC.ROT_ENTRADA,
             quintis={}, cortes_min={}, cortes_max={}, limites={},
             base=dict(c1=c1, c2=c2, n_h=int(len(u)), n_cand=int(u['cand'].sum()),
                       identidade=identidade,
                       pct_errado=float((u['sep_atr'] < 0).mean() * 100),
                       pct_alem=float((u['sep_atr'] > 2).mean() * 100),
                       pct_colada=float((u['colada'] > 0).mean() * 100)))

    for conj in ('h', 'cand'):
        base0 = u if conj == 'h' else u[u['cand']]
        for m, spec in MEDIDAS.items():
            cortes = spec['cortes'] if spec['cortes'] is not None else \
                list(np.percentile(base0[m], [20, 40, 60, 80]))
            S['limites'][f'{conj}|{m}'] = [float(x) for x in cortes]
            for ent in HC.ENTRADAS:
                for ges in HC.GESTOES:
                    t = res[(ent, ges)]
                    x = (t if conj == 'h' else t[t['cand']]).reset_index(drop=True)
                    q = np.digitize(x[m], cortes)
                    linhas = []
                    for k, rot in enumerate(spec['rotulos']):
                        mk = q == k
                        b = P.resumo_grupo(x[mk]); b['faixa'] = rot
                        b['compra'] = P.resumo_grupo(x[mk & (x['lado'] > 0)])['ev']
                        b['venda'] = P.resumo_grupo(x[mk & (x['lado'] < 0)])['ev']
                        b['sorteio'] = P.sorteio(x, pd.Series(mk)) if mk.sum() >= 5 else None
                        linhas.append(b)
                    S['quintis'][f'{conj}|{m}|{ent}|{ges}'] = linhas
                    if m in CONTINUAS:
                        mins = []; maxs = []
                        for pc in (0, 20, 40, 60):
                            b = P.resumo_grupo(x[x[m] >= np.percentile(x[m], pc)])
                            b['faixa'] = f'sem os {pc}% menores'; mins.append(b)
                            b = P.resumo_grupo(x[x[m] <= np.percentile(x[m], 100 - pc)])
                            b['faixa'] = f'sem os {pc}% maiores'; maxs.append(b)
                        S['cortes_min'][f'{conj}|{m}|{ent}|{ges}'] = mins
                        S['cortes_max'][f'{conj}|{m}|{ent}|{ges}'] = maxs

    for conj, rot in (('h', 'HULL + 2-4'), ('cand', 'CANDIDATO')):
        for m, spec in MEDIDAS.items():
            p(f"\n--- {rot} | {spec['rot']} ---")
            p('    limites: ' + '  '.join(f'{v:.2f}' for v in S['limites'][f'{conj}|{m}']))
            for ent in HC.ENTRADAS:
                for ges in HC.GESTOES:
                    if ent == 'meio_lim' and ges != 'parcial':
                        continue
                    p(f"  [{ent} {HC.ROT_GESTAO[ges]}]")
                    for b in S['quintis'][f'{conj}|{m}|{ent}|{ges}']:
                        p(f"    {b['faixa'][:30]:30s} {linha(b)}")
            if m in CONTINUAS:
                for key, nome in (('cortes_min', 'descarta menores'), ('cortes_max', 'descarta maiores')):
                    p(f"  {nome} (fecha parcial): " + ' | '.join(
                        f"{b['faixa'].split(' ')[2]} {b['ev']:+.1f}({b['n']})"
                        for b in S[key][f'{conj}|{m}|fecha|parcial']))

    with open(os.path.join(SAIDA, 'hull_distancias.json'), 'w', encoding='utf-8') as f:
        json.dump(P._lim(S), f, ensure_ascii=False)
    with open(os.path.join(SAIDA, 'hull_distancias_console.txt'), 'w', encoding='utf-8') as f:
        f.write(_buf.getvalue())
    p('\ngravado: saida/hull_distancias.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
