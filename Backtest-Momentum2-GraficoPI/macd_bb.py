# -*- coding: utf-8 -*-
"""
MACD x Bollinger 1000 NO TRIGGER -> macd_bb.html / MACD_BB.md

Pergunta: exigir o MACD alem de k desvios da Bollinger 1000 no fechamento do
trigger (compra: MACD >= media + k x desvio; venda: MACD <= media - k x desvio)
melhora o setup?

z = (MACD - media 1000) / desvio 1000, x lado do trade (positivo = a favor).
A Bollinger do grafico e 1000 / 1,0: z = 1 e a banda desenhada.

Dois modos:
  adicional   a regra continua exigindo MACD > 0 e acrescenta z >= k
  substituto  troca "MACD > 0" por "z >= k" (sinais gerados sem o filtro do MACD)
Os primeiros 1000 candles nao tem Bollinger: esses sinais ficam fora das comparacoes.
"""
import json
import os
import time
import numpy as np
import pandas as pd

import engine as E
from impulso import compara, eficiencia, impulso, media

BASE = E.BASE
SAIDA = os.path.join(BASE, 'saida')
T0 = time.time()
GESTOES = {'claude': {}, 'r400': dict(stop=100.0, alvo=400.0, parcial=False)}
KS = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.75, 0.9, 1.0]
KS_SUB = [-0.5, -0.25, 0.0, 0.25, 0.5]
FAIXAS = [(-np.inf, 0.0), (0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0), (1.0, np.inf)]


def log(*a):
    print(f'[{time.time() - T0:5.1f}s]', *a, flush=True)


def zscore(d, S):
    bm = ((d['bb_sup'] + d['bb_inf']) / 2).to_numpy()
    bw = ((d['bb_sup'] - d['bb_inf']) / 2).to_numpy() / E.BB_DESV
    g = S['i'].to_numpy()
    return (d['macd'].to_numpy()[g] - bm[g]) / bw[g] * S['lado'].to_numpy()


def prepara(d, S, corte):
    X = S.copy()
    X['treino'] = X['data'] < corte
    X['z'] = zscore(d, X)
    for gk, G in GESTOES.items():
        t = E.executa(d, X, 'fecha', G)
        X[f'rs_{gk}'] = E.reais(t); X[f'mot_{gk}'] = t['motivo'].to_numpy()
    return X[X['z'].notna()].reset_index(drop=True)


def main():
    import tendencia as TD
    d = E.indicadores(E.carrega())
    dias = sorted(d['dia'].unique())
    corte = dias[int(len(dias) * 0.6)]
    S0 = E.sinais(d)
    X = prepara(d, S0, corte)
    X = impulso(d, X)
    X['er_100'] = eficiencia(d, X)
    U = prepara(d, E.sinais(d, exige_macd=False), corte)
    tr = X['treino'].to_numpy()
    log('sinais', len(S0), 'com Bollinger', len(X), 'sem filtro MACD', len(U))
    OUT = dict(meta=dict(corte=str(corte)[:10], inicio=str(dias[0])[:10], fim=str(dias[-1])[:10], pregoes=len(dias),
                         sinais=len(S0), com_bb=len(X), universo_sub=len(U),
                         z_pct={str(p): float(np.percentile(X['z'], p)) for p in (5, 10, 25, 50, 75, 90, 95)},
                         desvio_mediano=float(np.nanmedian((d['bb_sup'] - d['bb_inf']) / 2)),
                         media_mediana=float(np.nanmedian((d['bb_sup'] + d['bb_inf']) / 2))),
               varredura=[], faixas=[], substituto=[], carteiras={}, combina={})

    # ---- varredura: manter z >= k (modo adicional)
    for k in KS:
        mk = (X['z'] >= k).to_numpy()
        for gk in GESTOES:
            rs_ = X[f'rs_{gk}'].to_numpy(); falha = (X[f'mot_{gk}'] == 'stop').to_numpy()
            c = compara(rs_, tr, mk, n_sort=1500) if 0 < mk.sum() < len(mk) else dict(n=int(mk.sum()), frac=float(mk.mean()), ev=media(rs_[mk]),
                                                                                      ev_is=media(rs_[mk & tr]), ev_oos=media(rs_[mk & ~tr]))
            c.update(k=k, gestao=gk, falha=float(falha[mk].mean() * 100), falha_resto=float(falha[~mk].mean() * 100) if (~mk).any() else None)
            OUT['varredura'].append(c)
    log('varredura')

    # ---- faixas de z
    for a, b in FAIXAS:
        mk = ((X['z'] >= a) & (X['z'] < b)).to_numpy()
        lin = dict(faixa=f"{'' if np.isinf(a) else f'{a:.1f}'.replace('.', ',')} a {'' if np.isinf(b) else f'{b:.1f}'.replace('.', ',')}".strip(),
                   a=None if np.isinf(a) else a, b=None if np.isinf(b) else b, n=int(mk.sum()), n_is=int((mk & tr).sum()), n_oos=int((mk & ~tr).sum()))
        for gk in GESTOES:
            rs_ = X[f'rs_{gk}'].to_numpy(); g = X[mk]
            lin[gk] = dict(ev=media(rs_[mk]), ev_is=media(rs_[mk & tr]), ev_oos=media(rs_[mk & ~tr]),
                           falha=float((g[f'mot_{gk}'] == 'stop').mean() * 100) if len(g) else None,
                           compra=media(g.loc[g.lado > 0, f'rs_{gk}']), venda=media(g.loc[g.lado < 0, f'rs_{gk}']),
                           t1=media(g.loc[g.tipo == 'T1', f'rs_{gk}']), t2=media(g.loc[g.tipo == 'T2', f'rs_{gk}']))
        OUT['faixas'].append(lin)

    # ---- modo substituto: z >= k no lugar de MACD > 0
    tru = U['treino'].to_numpy()
    for k in KS_SUB:
        mk = (U['z'] >= k).to_numpy()
        for gk in GESTOES:
            rs_ = U[f'rs_{gk}'].to_numpy()
            macd_pos = (U['macd'] * U['lado'] > 0).to_numpy()
            OUT['substituto'].append(dict(k=k, gestao=gk, n=int(mk.sum()), ev=media(rs_[mk]), ev_is=media(rs_[mk & tru]), ev_oos=media(rs_[mk & ~tru]),
                                          so_macd_contra=int((mk & ~macd_pos).sum()), ev_macd_contra=media(rs_[mk & ~macd_pos]) if (mk & ~macd_pos).any() else None,
                                          perdidos_macd_pos=int((~mk & macd_pos).sum())))
    ref = (U['macd'] * U['lado'] > 0).to_numpy()
    OUT['meta']['ref_macd0'] = {gk: dict(n=int(ref.sum()), ev=media(U.loc[ref, f'rs_{gk}']), ev_is=media(U.loc[ref & tru, f'rs_{gk}']),
                                         ev_oos=media(U.loc[ref & ~tru, f'rs_{gk}'])) for gk in GESTOES}
    OUT['meta']['macd_contra'] = {gk: dict(n=int((~ref).sum()), ev=media(U.loc[~ref, f'rs_{gk}'])) for gk in GESTOES}
    log('substituto')

    # ---- carteiras por limiar
    for gk, G in GESTOES.items():
        lin = [dict(nome='sem exigencia extra (so MACD > 0)', k=None, frac=1.0, **TD.stats_cart(d, X, G, corte))]
        for k in KS:
            mk = (X['z'] >= k).to_numpy()
            lin.append(dict(nome=f'MACD >= {k:.2f} desvios'.replace('.', ',') + (' (acima da media 1000)' if k == 0 else ''), k=k,
                            frac=float(mk.mean()), **TD.stats_cart(d, X[mk], G, corte)))
        OUT['carteiras'][gk] = lin
        log('carteira', gk, [round(l['stats']['liquido']) for l in lin])

    # ---- combinacao com os candidatos dos estudos anteriores
    nao_kc = (X['kc_10'] < 1).to_numpy(); cons = (X['er_100'] >= 0.08).to_numpy()
    for gk, G in GESTOES.items():
        lin = []
        for nome, mk in [('sem filtro', np.ones(len(X), bool)),
                         ('MACD >= 0,5 desvios', (X['z'] >= 0.5).to_numpy()),
                         ('MACD < 0,5 desvios', (X['z'] < 0.5).to_numpy()),
                         ('fora da consolidacao 100', cons),
                         ('fora da consolidacao 100 E MACD >= 0,5', cons & (X['z'] >= 0.5).to_numpy()),
                         ('nao passou da Keltner 2,5', nao_kc),
                         ('nao passou da Keltner 2,5 E MACD >= 0,5', nao_kc & (X['z'] >= 0.5).to_numpy()),
                         ('consolidacao 100 E Keltner', cons & nao_kc),
                         ('consolidacao 100 E Keltner E MACD >= 0,5', cons & nao_kc & (X['z'] >= 0.5).to_numpy())]:
            lin.append(dict(nome=nome, frac=float(mk.mean()), **TD.stats_cart(d, X[mk], G, corte)))
        OUT['combina'][gk] = lin
        log('combina', gk, [round(l['stats']['liquido']) for l in lin])
    OUT['meta']['corr_z'] = {c: float(X[[c, 'z']].corr(method='spearman').iloc[0, 1]) for c in ('kc_10', 'er_100', 'imp_20', 'bb_20')}

    def limpa(o):
        if isinstance(o, dict):
            return {str(k): limpa(v) for k, v in o.items()}
        if isinstance(o, (list, tuple, np.ndarray)):
            return [limpa(v) for v in (o.tolist() if isinstance(o, np.ndarray) else o)]
        if isinstance(o, (np.floating, float)):
            return None if (np.isnan(o) or np.isinf(o)) else round(float(o), 3)
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.bool_):
            return bool(o)
        return o

    with open(os.path.join(SAIDA, 'macd_bb.json'), 'w', encoding='utf-8') as f:
        json.dump(limpa(OUT), f, ensure_ascii=False)
    log('ok')


if __name__ == '__main__':
    main()
