# -*- coding: utf-8 -*-
"""
PRIMEIROS TOQUES NA VWAP BAND -> saida/toque.json + saida/toque_trades.json
(depois: toque_rel.py -> toque.html + TOQUE.md)

Pergunta (do usuario): operar so no 1o ou, no maximo, no 2o toque da banda no
dia, quando se forma um padrao de reversao TOCANDO a banda.

Diferenca para o vwap_estudo.py: la bastava o empurrao ter chegado na banda e
todo sinal dentro do toque contava. Aqui:
  - o padrao tem de se formar encostado na banda k (regra de toque abaixo);
  - UMA entrada por toque: a primeira que aparece dentro dele;
  - o toque e numerado por banda, lado e pregao (vbase.prepara_toques).

Regras de "tocando" (venda; compra e espelho):
  gatilho    o candle do gatilho tem maxima >= banda k
  padrao     algum candle do padrao (ultimo candle do empurrao + candles
             contra) tem maxima >= banda k                 <- principal
  movimento  o extremo do empurrao chegou na banda k (como no estudo anterior)

Modos de selecao dentro do toque, para um filtro de padrao F:
  B  a primeira virada do toque que tenha F       <- principal ("esperar o padrao")
  A  a primeira virada do toque, e so se ela tiver F (se nao tiver, perde o toque)
"""
import json
import os
import numpy as np
import pandas as pd

import vbase as V
from vwap_estudo import Ctx, faixas, cortes, compara, limpa, media, log, G_BANDA, RNG

BASE = V.BASE
SAIDA = os.path.join(BASE, 'saida')
GK = list(G_BANDA)

FILTROS = {
    'qualquer': ('Qualquer virada', lambda X: np.ones(len(X), bool)),
    'semrej': ('Sem pavio de rejeicao', lambda X: ~X['rej'].to_numpy()),
    'exaust': ('Exaustao (4+ candles)', lambda X: (X['n_emp'] >= 4).to_numpy()),
    'E': ('Exaustao limpa', lambda X: ((X['n_emp'] >= 4) & ~X['rej']).to_numpy()),
    'rej': ('Com pavio de rejeicao', lambda X: X['rej'].to_numpy()),
    'pav50': ('Pavio do candle de virada ate 50 pts', lambda X: (X['pav_rej'] <= 50).to_numpy()),
    'plana': ('VWAP plana (angulo >= -2 pts/candle)', lambda X: (X['ang'] >= -2).to_numpy()),
    'pav50plana': ('Pavio ate 50 e VWAP plana', lambda X: ((X['pav_rej'] <= 50) & (X['ang'] >= -2)).to_numpy()),
}
GRADE_F = ['qualquer', 'semrej', 'exaust', 'E', 'rej']
TOQUES = [('1o toque', lambda e: e == 1), ('2o toque', lambda e: e == 2),
          ('1o ou 2o', lambda e: (e == 1) | (e == 2)), ('3o em diante', lambda e: e >= 3)]


def um(Y, m):
    r = faixas(Y, [('', m)], GK)[0]
    r.pop('faixa')
    return r


def eventos(d, T, S, k, regra):
    """Sinais de S que se formaram tocando a banda k, com o numero do toque."""
    h = d['h'].to_numpy(); l = d['l'].to_numpy()
    up = d[f'up{k}'].to_numpy(); dn = d[f'dn{k}'].to_numpy()
    i = S['i'].to_numpy(); lado = S['lado'].to_numpy(); nc = S['nc'].to_numpy()
    j = S['j_ext'].to_numpy()
    ep_c = T['ep'][(-1, k)]; ep_v = T['ep'][(1, k)]
    ok = np.zeros(len(S), bool); ep = np.zeros(len(S), int)
    for q in range(len(S)):
        e_arr = ep_c if lado[q] < 0 else ep_v
        if regra == 'movimento':
            jj = [j[q]]
        elif regra == 'gatilho':
            jj = [i[q]]
        else:
            jj = list(range(i[q] - max(nc[q], 1), i[q] + 1))
        toca = [(h[x] >= up[x]) if lado[q] < 0 else (l[x] <= dn[x]) for x in jj]
        if any(toca):
            ok[q] = True
            ep[q] = max(e_arr[x] for x, t in zip(jj, toca) if t)
    X = S[ok].copy()
    X['ep'] = ep[ok]
    X['banda'] = k
    X['dia'] = X['data'].dt.normalize()
    return X[X['ep'] > 0]


def seleciona(X, filtro, modo='B'):
    """Uma entrada por toque (dia, lado, numero do toque)."""
    f = FILTROS[filtro][1]
    X = X.sort_values('i')
    if modo == 'B':
        Y = X[f(X)]
        return Y.groupby(['dia', 'lado', 'ep'], sort=False).head(1)
    Y = X.groupby(['dia', 'lado', 'ep'], sort=False).head(1)
    return Y[f(Y)]


def main():
    d = V.carrega()
    C = Ctx(d)
    TI = V.prepara_toques(d, 'interna')
    TV = V.prepara_toques(d, 'vwap')
    SG = {g: V.sinais(d, TI, g, 'banda') for g in ('c1', 'c2')}
    log('sinais', {g: len(s) for g, s in SG.items()})
    cache = {}

    def ev_(gat, k, regra, reset='interna'):
        key = (gat, k, regra, reset)
        if key not in cache:
            cache[key] = eventos(d, TI if reset == 'interna' else TV, SG[gat], k, regra)
        return cache[key]

    def roda(X):
        return C.roda(C.marca(X), G_BANDA)

    OUT = dict(meta=dict(inicio=str(C.dias[0])[:10], fim=str(C.dias[-1])[:10], pregoes=len(C.dias),
                         corte=str(C.corte)[:10], tercos=C.tercos, dias=[str(pd.Timestamp(x))[:10] for x in C.dias],
                         filtros={k: v[0] for k, v in FILTROS.items()}))

    # --------------------------------------------------- grade principal: banda x toque x filtro (c1, padrao, modo B)
    grade = {}
    for k in (1, 2, 3):
        X = ev_('c1', k, 'padrao')
        for fk in GRADE_F:
            Y = roda(seleciona(X, fk, 'B'))
            grade[f'{k}_{fk}'] = dict(banda=k, filtro=fk, lin=faixas(Y, [(r, f(Y['ep'])) for r, f in TOQUES], GK))
    OUT['grade'] = grade
    log('grade')

    # referencia: todos os sinais c1 do estudo anterior (sem 1 por toque, sem exigir encostar)
    X0 = roda(SG['c1'].copy())
    X0['E'] = (X0['n_emp'] >= 4) & ~X0['rej']
    OUT['ref'] = faixas(X0, [('todos os sinais c1 (estudo anterior)', np.ones(len(X0), bool)),
                             ('exaustao limpa, todos (estudo anterior)', X0['E'].to_numpy())], GK)

    # --------------------------------------------------- regra de toque
    rg = []
    for regra, nome in (('gatilho', 'o candle do gatilho encosta na banda'),
                        ('padrao', 'algum candle do padrao encosta na banda'),
                        ('movimento', 'so o empurrao chegou na banda')):
        X = ev_('c1', 1, regra)
        for fk in ('qualquer', 'semrej', 'E'):
            Y = roda(seleciona(X, fk, 'B'))
            m = Y['ep'].isin([1, 2]).to_numpy()
            rg.append(dict(faixa=f'{nome} · {FILTROS[fk][0]}', regra=regra, filtro=fk, **um(Y, m)))
    OUT['regra'] = rg

    # --------------------------------------------------- gatilho c1 x c2, modo A x B, reset
    cm = []
    for gat in ('c1', 'c2'):
        for k in (1, 2):
            X = ev_(gat, k, 'padrao')
            for fk in ('qualquer', 'semrej', 'E'):
                for modo in ('B', 'A'):
                    if gat == 'c2' and fk == 'semrej':
                        continue
                    Y = roda(seleciona(X, fk, modo))
                    m = Y['ep'].isin([1, 2]).to_numpy()
                    cm.append(dict(faixa=f"{V.GATILHOS[gat]} · banda {k} · {FILTROS[fk][0]} · "
                                         f"{'1o padrao do toque' if modo == 'B' else '1a virada, se tiver o padrao'}",
                                   gat=gat, banda=k, filtro=fk, modo=modo, **um(Y, m)))
    OUT['comb'] = cm
    rs_ = []
    for k in (2, 3):
        for reset in ('interna', 'vwap'):
            Y = roda(seleciona(ev_('c1', k, 'padrao', reset), 'qualquer', 'B'))
            rs_.append(dict(faixa=f"banda {k} · toque termina na {'banda de dentro' if reset == 'interna' else 'VWAP'}",
                            **um(Y, Y['ep'].isin([1, 2]).to_numpy())))
    OUT['reset'] = rs_
    log('comparacoes')

    # --------------------------------------------------- dentro do caso principal
    P = roda(seleciona(ev_('c1', 1, 'padrao'), 'qualquer', 'B'))
    P = P[P['ep'].isin([1, 2])].copy()
    P['E'] = (P['n_emp'] >= 4) & ~P['rej']
    F = {}
    F['pav'] = dict(rot='Pavio de rejeicao do candle de virada (pts)', lin=faixas(P, [
        ('sem pavio (0)', P.pav_rej <= 0), ('1 a 20', (P.pav_rej > 0) & (P.pav_rej <= 20)),
        ('21 a 50', (P.pav_rej > 20) & (P.pav_rej <= 50)), ('mais de 50', P.pav_rej > 50)], GK))
    F['emp'] = dict(rot='Candles seguidos do empurrao', lin=faixas(P, [
        ('1', P.n_emp == 1), ('2', P.n_emp == 2), ('3', P.n_emp == 3), ('4 ou 5', P.n_emp.isin([4, 5])),
        ('6 ou mais', P.n_emp >= 6)], GK))
    F['padrao'] = dict(rot='Padrao da virada', lin=faixas(P, [
        ('exaustao limpa', P.E), ('exaustao com pavio de rejeicao', (P.n_emp >= 4) & P.rej),
        ('falso rompimento', P.falso), ('pavio de rejeicao', P.rej), ('topo/fundo duplo', P.duplo),
        ('virada seca (sem rejeicao, empurrao < 4)', (P.n_emp < 4) & ~P.rej)], GK))
    F['nivel'] = dict(rot='Ate onde o movimento foi', lin=faixas(P, [
        ('so a banda 1', P.nivel == 1), ('chegou na banda 2', P.nivel == 2), ('chegou na banda 3', P.nivel == 3)], GK))
    F['ang'] = dict(rot='Angulo da VWAP (pts por candle, 10 candles)',
                    lin=faixas(P, cortes(P.ang, [-np.inf, -8, -4, -2, np.inf]), GK))
    F['hora'] = dict(rot='Horario', lin=faixas(P, [
        ('09:00 a 10h', P.hora < 10), ('10h a 11h', (P.hora >= 10) & (P.hora < 11)),
        ('11h a 13h', (P.hora >= 11) & (P.hora < 13)), ('13h a 15h', (P.hora >= 13) & (P.hora < 15)),
        ('15h em diante', P.hora >= 15)], GK))
    F['lado'] = dict(rot='Lado', lin=faixas(P, [('venda na banda de cima', P.lado < 0),
                                                 ('compra na banda de baixo', P.lado > 0)], GK))
    F['dist'] = dict(rot='Distancia ate a VWAP na entrada (pts)',
                     lin=faixas(P, cortes(P.dist_vwap, [-np.inf, 700, 900, 1200, np.inf]), GK))
    OUT['dentro'] = F
    HIP = [('Exaustao limpa', P.E), ('Sem pavio de rejeicao', ~P.rej), ('Pavio > 50', P.pav_rej > 50),
           ('Empurrao de 4+', P.n_emp >= 4), ('Falso rompimento', P.falso), ('Topo/fundo duplo', P.duplo),
           ('Chegou na banda 2+', P.nivel >= 2), ('1o toque (x 2o)', P.ep == 1),
           ('VWAP plana (angulo >= -2)', P.ang >= -2), ('VWAP -8 a -4 pts/candle', (P.ang >= -8) & (P.ang < -4)),
           ('Pavio ate 50 e VWAP plana', (P.pav_rej <= 50) & (P.ang >= -2))]
    OUT['hip'] = {gk: [dict(nome=nm, **compara(P, gk, np.asarray(mk, bool))) for nm, mk in HIP] for gk in GK}
    log('dentro')

    # --------------------------------------------------- candidatos: carteira, stops, bootstrap
    def cand(gat, k, fk, toq=(1, 2), regra='padrao', modo='B'):
        Y = seleciona(ev_(gat, k, regra), fk, modo)
        Y = Y[Y['ep'].isin(list(toq))]
        return C.marca(Y)

    CAND = [
        ('ref', 'Todos os sinais c1 nas bandas (estudo anterior)', C.marca(SG['c1'].copy())),
        ('b1q', 'Banda 1, 1o/2o toque: 1a virada encostada', cand('c1', 1, 'qualquer')),
        ('b1s', 'Banda 1, 1o/2o toque: 1a virada sem pavio de rejeicao', cand('c1', 1, 'semrej')),
        ('b1e', 'Banda 1, 1o/2o toque: 1a exaustao limpa', cand('c1', 1, 'E')),
        ('b1e1', 'Banda 1, so 1o toque: 1a exaustao limpa', cand('c1', 1, 'E', (1,))),
        ('b1p', 'Banda 1, 1o/2o toque: 1a virada, se pavio ate 50', cand('c1', 1, 'pav50', modo='A')),
        ('b1pp', 'Banda 1, 1o/2o toque: 1a virada, se pavio ate 50 e VWAP plana', cand('c1', 1, 'pav50plana', modo='A')),
        ('b1c2', 'Banda 1, 1o/2o toque: 1a virada de 2 candles', cand('c2', 1, 'qualquer')),
        ('b2q', 'Banda 2, 1o/2o toque: 1a virada encostada', cand('c1', 2, 'qualquer')),
        ('b2e', 'Banda 2, 1o/2o toque: 1a exaustao limpa', cand('c1', 2, 'E')),
        ('b1q3', 'Banda 1, 3o toque em diante: 1a virada encostada', cand('c1', 1, 'qualquer', range(3, 99))),
    ]
    carts = {}
    for gk, G in G_BANDA.items():
        lin = []
        for ck, nm, S in CAND:
            r, _ = C.cart(S, G)
            lin.append(dict(k=ck, nome=nm, n_sinais=len(S), **r))
        carts[gk] = lin
        log('carteira', gk, [round(l['stats']['liquido']) for l in lin])
    OUT['carteiras'] = carts
    stp = []
    for ck, nm, S in [c for c in CAND if c[0] in ('b1q', 'b1e', 'b1p', 'b2e')]:
        for st in (100.0, 150.0, ('ext', 300.0)):
            for al in (300.0, 500.0, 'vwap'):
                G = dict(stop=st, alvo=al)
                t = V.executa(C.A, S, G); rr = V.reais(t); tr = S['treino'].to_numpy()
                r, _ = C.cart(S, G, extra=False)
                stp.append(dict(cand=nm, stop='extremo + 10' if isinstance(st, tuple) else f'{st:.0f}',
                                alvo='VWAP' if al == 'vwap' else f'{al:.0f}', ev=media(rr), ev_is=media(rr[tr]),
                                ev_oos=media(rr[~tr]), liq=r['stats'].get('liquido'), fl=r['stats'].get('fator_lucro'),
                                dd=r['stats'].get('dd_max')))
    OUT['stops'] = stp
    bs = []
    for ck, nm, S in [c for c in CAND if c[0] in ('b1q', 'b1s', 'b1e', 'b1e1', 'b1p', 'b1pp', 'b1c2', 'b2e')]:
        for gk, G in G_BANDA.items():
            _, c = C.cart(S, G, extra=False)
            rr = V.reais(c); dd = c['data'].dt.normalize().to_numpy()
            ud = np.unique(dd); pdia = np.array([rr[dd == u].sum() for u in ud])
            sims = np.array([pdia[RNG.integers(0, len(pdia), len(pdia))].sum() for _ in range(4000)])
            bs.append(dict(cand=nm, gk=gk, p_prejuizo=float((sims <= 0).mean() * 100),
                           p5=float(np.percentile(sims, 5)), p50=float(np.percentile(sims, 50)),
                           dias=int(len(ud)), trades=len(c)))
    OUT['bootstrap'] = bs
    log('robustez')
    with open(os.path.join(SAIDA, 'toque.json'), 'w', encoding='utf-8') as f:
        json.dump(limpa(OUT), f, ensure_ascii=False)

    # --------------------------------------------------- trade a trade
    TR = {}
    for ck, nm, S in [c for c in CAND if c[0] in ('b1q', 'b1p', 'b1e1', 'b1e', 'b2e')]:
        for gk in ('r300', 'claude'):
            G = G_BANDA[gk]
            c = V.carteira(V.executa(C.A, S, G))
            c = c.assign(rs=V.reais(c))
            TR[f'{ck}_{gk}'] = dict(nome=f"{nm} · {'alvo 300' if gk == 'r300' else 'gestao CLAUDE.md'}", gk=gk,
                                    alvo=G['alvo'], parcial=G.get('parcial'), trades=[dict(
                i=int(r.i), v0=int(r.v0), j=int(r.j_ext), i_sai=int(r.i_sai), lado=int(r.lado),
                data=r.data.strftime('%d/%m/%y %H:%M'), pe=float(r.preco), ps=float(r.preco_sai),
                stop=float(r.stop_pts), mot=r.motivo, pts=float(r.pts), rs=float(r.rs),
                mfe=float(r.mfe), mae=float(r.mae), nivel=int(r.banda), tb=int(r.banda), emp=int(r.n_emp),
                toque=int(r.ep), ang=round(float(r.ang), 1), pad=r.padrao, pav=float(r.pav_rej),
                dv=round(float(r.dist_vwap))) for r in c.itertuples()])
    with open(os.path.join(SAIDA, 'toque_trades.json'), 'w', encoding='utf-8') as f:
        json.dump(limpa(TR), f, ensure_ascii=False)
    log('ok')


if __name__ == '__main__':
    main()
