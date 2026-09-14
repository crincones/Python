# -*- coding: utf-8 -*-
"""
A inclinacao da Hull 50 serve de filtro?

    python hull_inclinacao.py        -> saida/hull_inclinacao.json + console

Parte do estudo hull_contra.py, que ja usa o SINAL da inclinacao (Hull
subindo para comprar, descendo para vender). Aqui a pergunta e o TAMANHO:
Hull subindo forte e melhor que Hull subindo devagar? Ou o contrario --
Hull muito inclinada ja e exaustao?

"Grau" de inclinacao em angulo nao existe de forma objetiva: o angulo na
tela depende da escala do grafico. Por isso a inclinacao e medida em
PONTOS POR BARRA, de tres jeitos:

  incl1      hma[i] - hma[i-1]              a do indicador (1 barra)
  incl5      (hma[i] - hma[i-5]) / 5        media de 5 barras, menos ruido
  incl1_atr  incl1 / ATR 21                 relativa a volatilidade do dia

sempre no sentido do trade (positivo = a favor).

As faixas sao QUINTIS da propria distribuicao -- cortes definidos antes
de olhar o resultado, e com o mesmo numero de sinais em cada faixa.

Conjuntos:
  h        Hull a favor + 2 a 4 barras + candle contra   (a regra-base)
  h23f10   + 2 a 3 barras + pavio do fechamento ate 10%  (o candidato)
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

MEDIDAS = {'incl1': 'Inclinacao em 1 barra (pts)',
           'incl5': 'Inclinacao media em 5 barras (pts/barra)',
           'incl1_atr': 'Inclinacao em 1 barra / ATR 21'}
ROT_Q = ['Q1 (mais plana)', 'Q2', 'Q3', 'Q4', 'Q5 (mais inclinada)']

_buf = io.StringIO()


def p(*a, **k):
    print(*a, **k)
    print(*a, **k, file=_buf)


def linha(b):
    if not b['n']:
        return '-'
    tt = ' / '.join('   -  ' if v is None else f'{v:+6.1f}' for v in b['ev_terco'])
    return f"n={b['n']:4d}  EV {b['ev']:+6.1f}  acerto {b['wr']:4.1f}%  tercos {tt}"


def main():
    d = E.indicadores(E.carrega())
    dias = sorted(d['dia'].unique())
    hu = d['hma'].to_numpy(); at = d['atr'].to_numpy()

    u = P.universo(d)
    for per in HC.HULL_TESTE:
        u = HC.anexa_hull(u, d, per, f'hull{per}')
    u = u[u['hull80_valida']].reset_index(drop=True)
    u = u[u['hull50'] & u['n_fav'].between(2, 4)].reset_index(drop=True)
    i = u['i'].to_numpy(); ld = u['lado'].to_numpy()
    u['incl1'] = (hu[i] - hu[i - 1]) * ld
    u['incl5'] = (hu[i] - hu[i - 5]) * ld / 5
    u['incl1_atr'] = u['incl1'] / at[i]
    u['cand'] = (u['n_fav'] <= 3) & (u['pav_outro_pct'] <= 10)

    p('=' * 74)
    p('A INCLINACAO DA HULL 50 SERVE DE FILTRO?')
    p('=' * 74)
    p(f"sinais Hull a favor + 2-4: {len(u)}   candidato (2-3 + fech<=10%): {int(u['cand'].sum())}")
    for m in MEDIDAS:
        p(f"  {m:10s} quintis: " + '  '.join(f'{v:.2f}' for v in np.percentile(u[m], [20, 40, 60, 80])))
    p(f"  correlacao incl1 x incl5: {np.corrcoef(u['incl1'], u['incl5'])[0, 1]:.2f}   "
      f"incl1 x incl1_atr: {np.corrcoef(u['incl1'], u['incl1_atr'])[0, 1]:.2f}   "
      f"incl1 x barras antes: {np.corrcoef(u['incl1'], u['n_fav'])[0, 1]:.2f}")

    res = {}
    for ent in HC.ENTRADAS:
        for ges, gg in HC.GESTOES.items():
            t = E.executa(d, u, ent, gg)
            t, c1, c2 = P.marca_tercos(t, dias)
            res[(ent, ges)] = t

    S = dict(medidas=MEDIDAS, rot_q=ROT_Q, rot_gestao=HC.ROT_GESTAO,
             rot_entrada=HC.ROT_ENTRADA, quintis={}, cortes_min={}, cortes_max={},
             correl=dict(incl1_incl5=float(np.corrcoef(u['incl1'], u['incl5'])[0, 1]),
                         incl1_nfav=float(np.corrcoef(u['incl1'], u['n_fav'])[0, 1])))

    for conj in ('h', 'cand'):
        for m in MEDIDAS:
            # quintis definidos no conjunto (sem olhar resultado)
            base0 = u if conj == 'h' else u[u['cand']]
            qs = np.percentile(base0[m], [20, 40, 60, 80])
            S['quintis'][f'{conj}|{m}|limites'] = [float(x) for x in qs]
            for ent in HC.ENTRADAS:
                for ges in HC.GESTOES:
                    t = res[(ent, ges)]
                    x = (t if conj == 'h' else t[t['cand']]).reset_index(drop=True)
                    q = np.digitize(x[m], qs)          # 0..4
                    linhas = []
                    for k in range(5):
                        b = P.resumo_grupo(x[q == k]); b['faixa'] = ROT_Q[k]
                        b['compra'] = P.resumo_grupo(x[(q == k) & (x['lado'] > 0)])['ev']
                        b['venda'] = P.resumo_grupo(x[(q == k) & (x['lado'] < 0)])['ev']
                        b['sorteio'] = P.sorteio(x, pd.Series(q == k)) if (q == k).sum() else None
                        linhas.append(b)
                    S['quintis'][f'{conj}|{m}|{ent}|{ges}'] = linhas
                    # varredura: descarta os X% mais planos / os X% mais inclinados
                    mins = []; maxs = []
                    for pc in (0, 20, 40, 60):
                        lim = np.percentile(x[m], pc)
                        b = P.resumo_grupo(x[x[m] >= lim]); b['faixa'] = f'sem os {pc}% mais planos'
                        mins.append(b)
                        lim2 = np.percentile(x[m], 100 - pc)
                        b = P.resumo_grupo(x[x[m] <= lim2]); b['faixa'] = f'sem os {pc}% mais inclinados'
                        maxs.append(b)
                    S['cortes_min'][f'{conj}|{m}|{ent}|{ges}'] = mins
                    S['cortes_max'][f'{conj}|{m}|{ent}|{ges}'] = maxs

    # -------------------------------------------------------------- console
    for conj, rot in (('h', 'HULL A FAVOR + 2-4'), ('cand', 'CANDIDATO h23f10')):
        for m in MEDIDAS:
            p(f"\n--- {rot} | {MEDIDAS[m]} | fechamento ------------------")
            p('    limites dos quintis: ' + '  '.join(f'{v:.2f}' for v in S['quintis'][f'{conj}|{m}|limites']))
            for ges in HC.GESTOES:
                p(f"  [{HC.ROT_GESTAO[ges]}]")
                for b in S['quintis'][f'{conj}|{m}|fecha|{ges}']:
                    p(f"    {b['faixa']:20s} {linha(b)}  C {b['compra']:+6.1f} V {b['venda']:+6.1f}  "
                      f"pct {b['sorteio']['percentil']:3.0f}")
            p('  [limitada, 1:3 com parcial]')
            for b in S['quintis'][f'{conj}|{m}|meio_lim|parcial']:
                p(f"    {b['faixa']:20s} {linha(b)}")

    S['base'] = dict(c1=c1, c2=c2, n_h=int(len(u)), n_cand=int(u['cand'].sum()))
    with open(os.path.join(SAIDA, 'hull_inclinacao.json'), 'w', encoding='utf-8') as f:
        json.dump(P._lim(S), f, ensure_ascii=False)
    with open(os.path.join(SAIDA, 'hull_inclinacao_console.txt'), 'w', encoding='utf-8') as f:
        f.write(_buf.getvalue())
    p('\ngravado: saida/hull_inclinacao.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
