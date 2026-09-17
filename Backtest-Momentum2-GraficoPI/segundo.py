# -*- coding: utf-8 -*-
"""
SEGUNDO TOQUE na EMA 21 -> segundo.html / SEGUNDO_TOQUE.md

Pergunta: impulso -> recuo na EMA 21 (com ou sem sinal) -> novo impulso ->
segundo recuo com sinal PERTO do anterior. Esse segundo sinal falha mais?

Estrutura medida para cada sinal (so passado, mesmo pregao):
  perna            candles desde que o MACD ficou do lado do trade
  recuo            candles tocando a EMA 21 (tolerancia 15 pts, a da regra).
                   Toques sem impulso >= IMP_MIN pts desde o extremo do recuo
                   anterior sao o MESMO recuo (preco preso na EMA)
  ordem            1o, 2o, 3o+ recuo da perna
  nivel            (extremo do recuo atual - extremo do anterior) x lado:
                   > 0 fundo mais alto (compra); < 0 passou do anterior
  sinal anterior   sinal do setup no recuo anterior; distancia entre as
                   entradas; resultado dele, so se ja fechou antes do atual
"""
import json
import os
import time
import numpy as np
import pandas as pd

import engine as E

BASE = E.BASE
SAIDA = os.path.join(BASE, 'saida')
T0 = time.time()
RNG = np.random.default_rng(23)
GESTOES = {'claude': {}, 'r400': dict(stop=100.0, alvo=400.0, parcial=False)}
TOL = 15.0
IMP_MIN = 300.0          # impulso minimo (pts) depois de um recuo para contar o proximo como novo recuo
IMPS = [200.0, 300.0, 400.0]


def log(*a):
    print(f'[{time.time() - T0:5.1f}s]', *a, flush=True)


def toques(d, S, R, imp_min=None):
    """Recuos na EMA 21 dentro da perna do MACD (desde que ele ficou do lado do
    trade, no mesmo pregao). Toques sem impulso >= imp_min entre eles sao o
    MESMO recuo. R: resultado da gestao do CLAUDE.md alinhado a S."""
    imp_min = IMP_MIN if imp_min is None else imp_min
    h = d['h'].to_numpy(); l = d['l'].to_numpy(); em = d['ema'].to_numpy()
    mc = d['macd'].to_numpy(); dia = d['dia'].to_numpy()
    dist = np.where(em > h, em - h, np.where(em < l, l - em, 0.0))
    toca = dist <= TOL
    sig_lado = {1: S[S.lado > 0], -1: S[S.lado < 0]}
    res = dict(zip(S['i'], zip(R['motivo'], R['i_sai'])))
    out = []
    for r in S.itertuples(index=False):
        g = r.i; lado = r.lado; v0 = r.v0
        js = np.arange(v0, g + 1)
        k_t = js[toca[js]]
        e0 = int(k_t.min()) if len(k_t) else v0
        # inicio da perna: MACD do lado do trade, sem sair do pregao
        m0 = e0
        while m0 - 1 >= 0 and dia[m0 - 1] == dia[g] and mc[m0 - 1] * lado > 0:
            m0 -= 1
        eps = []                      # [inicio, fim, extremo, liberado]
        for k in range(m0, e0):
            if toca[k]:
                ext_k = l[k] if lado > 0 else h[k]
                if eps and not eps[-1][3]:
                    eps[-1][1] = k
                    eps[-1][2] = min(eps[-1][2], ext_k) if lado > 0 else max(eps[-1][2], ext_k)
                else:
                    eps.append([k, k, ext_k, False])
            if eps and not eps[-1][3]:
                fav = h[k] if lado > 0 else l[k]
                if (fav - eps[-1][2]) * lado >= imp_min and k > eps[-1][1]:
                    eps[-1][3] = True
        ext_at = l[e0:g + 1].min() if lado > 0 else h[e0:g + 1].max()
        lin = dict(i=g, perna_ini_dia=bool(m0 == 0 or dia[m0 - 1] != dia[g]), barras_perna=int(g - m0))
        if not eps:
            lin.update(classe='1o recuo da perna', ordem=1, tem_ant=False)
            out.append(lin); continue
        ult = eps[-1]
        if not ult[3]:
            # o ultimo toque nao foi seguido de impulso: o recuo atual e continuacao dele
            lin.update(classe='sem impulso desde o toque anterior', ordem=sum(e[3] for e in eps) + 1, tem_ant=True)
        else:
            lin.update(classe='2o recuo da perna' if len(eps) == 1 else '3o+ recuo da perna', ordem=len(eps) + 1, tem_ant=True)
        meio = np.arange(ult[1] + 1, e0)
        pico = (h[meio].max() if lado > 0 else l[meio].min()) if len(meio) else ext_at
        ant = sig_lado[lado]
        ant = ant[(ant['i'] >= ult[0] - 3) & (ant['v0'] <= ult[1] + 3) & (ant['i'] < v0)]
        if len(ant):
            ia = int(ant['i'].iloc[-1]); mot, isai = res[ia]
            res_ant = 'aberto' if isai >= g else {'stop': 'stop', 'stop_zero': '0x0', 'alvo': 'alvo'}.get(mot, 'outro')
            dist_sinal = float((r.preco - S.loc[S['i'] == ia, 'preco'].iloc[0]) * lado)
        else:
            res_ant = 'sem sinal'; dist_sinal = np.nan
        lin.update(imp_entre=float((pico - ult[2]) * lado), nivel=float((ext_at - ult[2]) * lado),
                   gap_barras=int(e0 - ult[1]), sinal_ant=bool(len(ant)), res_ant=res_ant, dist_sinal=dist_sinal)
        out.append(lin)
    return pd.DataFrame(out)


def media(x):
    x = np.asarray(x, float)
    return float(x.mean()) if len(x) else None


def resumo(Z, mk, gk):
    g = Z[mk]
    if len(g) == 0:
        return dict(n=0)
    rs_ = g[f'rs_{gk}'].to_numpy(); mot = g[f'mot_{gk}']
    return dict(n=len(g), frac=len(g) / len(Z), ev=media(rs_), ev_is=media(g.loc[g.treino, f'rs_{gk}']),
                ev_oos=media(g.loc[~g.treino, f'rs_{gk}']), n_is=int(g.treino.sum()), n_oos=int((~g.treino).sum()),
                falha=float((mot == 'stop').mean() * 100), falha_is=float((mot[g.treino] == 'stop').mean() * 100) if g.treino.any() else None,
                falha_oos=float((mot[~g.treino] == 'stop').mean() * 100) if (~g.treino).any() else None,
                parcial=float(g[f'parc_{gk}'].mean() * 100), alvo=float((mot == 'alvo').mean() * 100),
                compra=media(g.loc[g.lado > 0, f'rs_{gk}']), venda=media(g.loc[g.lado < 0, f'rs_{gk}']))


def pct_sorteio(rs_, mk, n_sort=3000):
    k = int(mk.sum())
    if k == 0 or k == len(rs_):
        return None
    alvo = rs_[mk].mean()
    sim = np.array([rs_[RNG.permutation(len(rs_))[:k]].mean() for _ in range(n_sort)])
    return float((sim < alvo).mean() * 100)


def t_dif(a, b):
    if len(a) < 3 or len(b) < 3:
        return None
    return float((a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b)))


def main():
    import tendencia as TD
    d = E.indicadores(E.carrega())
    dias = sorted(d['dia'].unique())
    corte = dias[int(len(dias) * 0.6)]
    S = E.sinais(d)
    S['treino'] = S['data'] < corte
    X0 = S.copy()
    for gk, G in GESTOES.items():
        t = E.executa(d, S, 'fecha', G)
        X0[f'rs_{gk}'] = E.reais(t); X0[f'mot_{gk}'] = t['motivo'].to_numpy(); X0[f'parc_{gk}'] = t['parcial'].to_numpy()
        if gk == 'claude':
            Rc = t
    OUT = dict(meta=dict(corte=str(corte)[:10], inicio=str(dias[0])[:10], fim=str(dias[-1])[:10], pregoes=len(dias), sinais=len(X0),
                         tol=TOL, imp_padrao=IMP_MIN, imps=IMPS),
               grupos={}, sens=[], carteiras={}, dist={})
    tr_all = X0['treino'].to_numpy()

    for imp in IMPS:
        F = toques(d, S, Rc, imp)
        X = X0.merge(F, on='i', how='left')
        cl = X['classe']
        rec = cl.isin(['2o recuo da perna', '3o+ recuo da perna']).to_numpy()   # recuo apos impulso, com recuo anterior na perna
        sa = X['sinal_ant'].fillna(False).astype(bool).to_numpy()
        ds = X['dist_sinal'].to_numpy(); nv = X['nivel'].to_numpy(); ra = X['res_ant'].to_numpy()
        OUT['dist'][str(int(imp))] = {k: int(v) for k, v in cl.value_counts().items()}
        GR = [
            ('ordem', '1o recuo da perna do MACD', (cl == '1o recuo da perna').to_numpy(), 'todos'),
            ('ordem', '2o recuo da perna (houve impulso depois do 1o)', (cl == '2o recuo da perna').to_numpy(), 'todos'),
            ('ordem', '3o recuo ou mais', (cl == '3o+ recuo da perna').to_numpy(), 'todos'),
            ('ordem', 'Toque sem impulso desde o anterior (preso na EMA)', (cl == 'sem impulso desde o toque anterior').to_numpy(), 'todos'),
            ('nivel', 'Recuo passou do recuo anterior (> 15 pts alem)', rec & (nv < -15), 'rec'),
            ('nivel', 'Recuo no mesmo nivel do anterior (+-15 pts)', rec & (np.abs(nv) <= 15), 'rec'),
            ('nivel', 'Recuo acima do anterior, ate 100 pts', rec & (nv > 15) & (nv <= 100), 'rec'),
            ('nivel', 'Recuo acima do anterior, 101-200 pts', rec & (nv > 100) & (nv <= 200), 'rec'),
            ('nivel', 'Recuo acima do anterior, mais de 200 pts', rec & (nv > 200), 'rec'),
            ('sinal', 'Recuo anterior SEM sinal', rec & ~sa, 'rec'),
            ('sinal', 'Recuo anterior COM sinal', rec & sa, 'rec'),
            ('perto', 'Sinal anterior perto: entrada ate 100 pts do anterior', rec & sa & (np.abs(ds) <= 100), 'rec_sa'),
            ('perto', 'Sinal anterior longe: mais de 100 pts', rec & sa & (np.abs(ds) > 100), 'rec_sa'),
            ('perto', 'Entrada 100+ pts PIOR que a anterior (abaixo na compra)', rec & sa & (ds <= -100), 'rec_sa'),
            ('perto', 'Entrada no MESMO preco da anterior', rec & sa & (ds == 0), 'rec_sa'),
            ('perto', 'Entrada 1 tijolo (100 pts) acima na compra', rec & sa & (ds > 0) & (ds <= 100), 'rec_sa'),
            ('perto', 'Entrada 200 pts acima', rec & sa & (ds > 100) & (ds <= 200), 'rec_sa'),
            ('perto', 'Entrada 300+ pts acima', rec & sa & (ds > 200), 'rec_sa'),
            ('res', 'Sinal anterior tomou STOP', rec & (ra == 'stop'), 'rec_sa'),
            ('res', 'Sinal anterior fez parcial e zerou (0x0)', rec & (ra == '0x0'), 'rec_sa'),
            ('res', 'Sinal anterior bateu o ALVO', rec & (ra == 'alvo'), 'rec_sa'),
            ('res', 'Sinal anterior ainda aberto', rec & (ra == 'aberto'), 'rec_sa'),
        ]
        bases = dict(todos=np.ones(len(X), bool), rec=rec, rec_sa=rec & sa)
        rotb = dict(todos='todos os sinais', rec='recuos com recuo anterior na perna', rec_sa='recuos cujo recuo anterior teve sinal')
        for gk in GESTOES:
            rs_all = X[f'rs_{gk}'].to_numpy(); falha = (X[f'mot_{gk}'] == 'stop').to_numpy()
            lin = []
            for fam, nome, mk, bk in GR:
                base = bases[bk]; mk = np.asarray(mk, bool) & base
                if mk.sum() == 0:
                    continue
                r = resumo(X, mk, gk)
                resto = base & ~mk
                r.update(fam=fam, nome=nome, base=rotb[bk],
                         resto=media(rs_all[resto]) if resto.any() else None,
                         resto_is=media(rs_all[resto & tr_all]) if resto.any() else None,
                         resto_oos=media(rs_all[resto & ~tr_all]) if resto.any() else None,
                         falha_resto=float(falha[resto].mean() * 100) if resto.any() else None,
                         falha_resto_is=float(falha[resto & tr_all].mean() * 100) if (resto & tr_all).any() else None,
                         falha_resto_oos=float(falha[resto & ~tr_all].mean() * 100) if (resto & ~tr_all).any() else None,
                         t=t_dif(rs_all[mk], rs_all[resto]) if resto.sum() > 2 else None,
                         pct=pct_sorteio(rs_all[base], mk[base], 1500) if 0 < mk.sum() < base.sum() else None)
                lin.append(r)
            OUT['grupos'][f'{int(imp)}|{gk}'] = lin
            for r in lin:
                OUT['sens'].append(dict(imp=int(imp), gestao=gk, nome=r['nome'], n=r['n'], ev=r['ev'], resto=r['resto'],
                                        ev_is=r['ev_is'], ev_oos=r['ev_oos'], resto_is=r['resto_is'], resto_oos=r['resto_oos'],
                                        falha=r['falha'], falha_resto=r['falha_resto'], t=r['t']))
        log('imp', imp, OUT['dist'][str(int(imp))])

        if imp == IMP_MIN:
            CART = [
                ('sem filtro', np.ones(len(X), bool)),
                ('sem o 2o recuo da perna', (cl != '2o recuo da perna').to_numpy()),
                ('sem 2o e 3o+ recuos', ~rec),
                ('sem o sinal perto do anterior (ate 100 pts)', ~(rec & sa & (np.abs(ds) <= 100))),
                ('sem o sinal 1 tijolo acima do anterior', ~(rec & sa & (ds > 0) & (ds <= 100))),
                ('sem o sinal com o anterior ainda aberto', ~(rec & (ra == 'aberto'))),
                ('sem o sinal depois de STOP no anterior', ~(rec & (ra == 'stop'))),
            ]
            for gk, G in GESTOES.items():
                OUT['carteiras'][gk] = [dict(nome=nome, frac=float(mk.mean()), **TD.stats_cart(d, X[np.asarray(mk, bool)], G, corte)) for nome, mk in CART]
                log('carteira', gk, [round(l['stats']['liquido']) for l in OUT['carteiras'][gk]])

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

    with open(os.path.join(SAIDA, 'segundo.json'), 'w', encoding='utf-8') as f:
        json.dump(limpa(OUT), f, ensure_ascii=False)
    log('ok')


if __name__ == '__main__':
    main()
