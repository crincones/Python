# -*- coding: utf-8 -*-
"""
REVERSOES NAS VWAP BANDS -> saida/vwap.json + saida/vwap_trades.json
(depois: vwap_rel.py -> vwap.html + VWAP.md)

Perguntas:
  1. quais padroes de reversao nas bandas funcionam melhor
  2. o angulo da VWAP muda o resultado
  3. os primeiros toques na banda sao melhores
  4. a VWAP serve como ponto de entrada, ou so como alvo
Saidas: alvo seco de 300 e de 500, alvo na VWAP e a gestao do CLAUDE.md
(parcial), todas com stop de 100. Treino = primeiros 60% dos pregoes.
"""
import json
import os
import time
import numpy as np
import pandas as pd

import vbase as V

BASE = V.BASE
SAIDA = os.path.join(BASE, 'saida')
T0 = time.time()
RNG = np.random.default_rng(31)

G_BANDA = {k: V.GESTOES[k] for k in ('r300', 'r500', 'vw', 'claude')}
G_VWAP = {'r300': V.GESTOES['r300'], 'r500': V.GESTOES['r500'],
          'b1': dict(nome='Stop 100 / alvo na banda 1 a favor', stop=100.0, alvo='b1'),
          'claude': V.GESTOES['claude']}


def log(*a):
    print(f'[{time.time() - T0:5.1f}s]', *a, flush=True)


def media(x):
    x = np.asarray(x, float)
    return float(x.mean()) if len(x) else None


def limpa(o):
    if isinstance(o, dict):
        return {str(k): limpa(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, np.ndarray)):
        return [limpa(v) for v in (o.tolist() if isinstance(o, np.ndarray) else o)]
    if isinstance(o, (np.floating, float)):
        return None if (np.isnan(o) or np.isinf(o)) else round(float(o), 4)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


# ================================================================ helpers
class Ctx:
    def __init__(self, d):
        self.d = d
        self.A = V.Arr(d)
        self.dias = sorted(d['dia'].unique())
        self.corte = self.dias[int(len(self.dias) * 0.6)]
        t3 = np.array_split(np.array(self.dias), 3)
        self.lim3 = (t3[0][-1], t3[1][-1])
        self.tercos = [(str(pd.Timestamp(b[0]))[:10], str(pd.Timestamp(b[-1]))[:10]) for b in t3]

    def marca(self, S):
        S = S.copy()
        S['treino'] = S['data'] < self.corte
        dt = S['data'].to_numpy()
        S['terco'] = np.where(dt <= self.lim3[0], 1, np.where(dt <= self.lim3[1], 2, 3))
        return S

    def roda(self, S, GS):
        for gk, G in GS.items():
            t = V.executa(self.A, S, G)
            S[f'rs_{gk}'] = V.reais(t); S[f'pts_{gk}'] = t['pts'].to_numpy()
            S[f'mot_{gk}'] = t['motivo'].to_numpy()
        return S

    def cart(self, S, G, extra=True):
        t = V.executa(self.A, S, G)
        c = V.carteira(t)
        st = V.estatisticas(c)
        out = dict(stats=st, is_=V.estatisticas(c[c['data'] < self.corte]),
                   oos=V.estatisticas(c[c['data'] >= self.corte]))
        if extra:
            Ga = dict(G); Ga['atravessa'] = 5.0
            out['atravessa'] = V.estatisticas(V.carteira(V.executa(self.A, S, Ga))).get('liquido', 0.0)
            rs = V.reais(c)
            out['eq'] = np.round(np.cumsum(rs), 1).tolist()
            out['dt'] = c['data'].dt.strftime('%d/%m').tolist()
            pd_ = pd.Series(rs, index=c['data'].dt.normalize().to_numpy()).groupby(level=0).sum()
            out['eq_dia'] = np.round(pd_.reindex(pd.DatetimeIndex(self.dias), fill_value=0.0).cumsum().to_numpy(), 1).tolist()
        return out, c


def linha(X, m, gks):
    g = X[m]
    r = dict(n=int(m.sum()))
    for gk in gks:
        rs = g[f'rs_{gk}']
        r[gk] = dict(ev=media(rs), wr=float((g[f'pts_{gk}'] > 0).mean() * 100) if len(g) else None,
                     ev_is=media(rs[g['treino']]), ev_oos=media(rs[~g['treino']]),
                     t=[media(rs[g['terco'] == i]) for i in (1, 2, 3)],
                     compra=media(rs[g['lado'] > 0]), venda=media(rs[g['lado'] < 0]))
    r['n_is'] = int(g['treino'].sum()); r['n_oos'] = int((~g['treino']).sum())
    r['nt'] = [int((g['terco'] == i).sum()) for i in (1, 2, 3)]
    return r


def faixas(X, rotulos, gks):
    """rotulos: lista de (texto, mascara)."""
    return [dict(faixa=r, **linha(X, np.asarray(m, bool), gks)) for r, m in rotulos]


def cortes(x, bordas, fmt='{:g}'):
    out = []
    for a, b in zip(bordas[:-1], bordas[1:]):
        if a == -np.inf:
            r = f'abaixo de {fmt.format(b)}'
        elif b == np.inf:
            r = f'{fmt.format(a)} ou mais'
        else:
            r = f'{fmt.format(a)} a {fmt.format(b)}'
        out.append((r, (x >= a) & (x < b)))
    return out


def compara(X, gk, mk, n_sort=2000):
    rs = X[f'rs_{gk}'].to_numpy(); tr = X['treino'].to_numpy(); te = X['terco'].to_numpy()
    mk = np.asarray(mk, bool)
    a = rs[mk]; b = rs[~mk]
    t = float((a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))) \
        if len(a) > 2 and len(b) > 2 else None
    k = int(mk.sum())
    sim = np.array([rs[RNG.permutation(len(rs))[:k]].mean() for _ in range(n_sort)]) if 0 < k < len(rs) else np.array([np.nan])
    return dict(n=k, frac=k / len(rs), ev=media(a), resto=media(b),
                ev_is=media(rs[mk & tr]), ev_oos=media(rs[mk & ~tr]),
                resto_is=media(rs[~mk & tr]), resto_oos=media(rs[~mk & ~tr]),
                ter=[media(rs[mk & (te == i)]) for i in (1, 2, 3)],
                ter_resto=[media(rs[~mk & (te == i)]) for i in (1, 2, 3)],
                t=t, pct=float((sim < a.mean()).mean() * 100) if k else None)


# ================================================================== main
def main():
    d = V.carrega()
    T = V.prepara_toques(d)
    C = Ctx(d)
    log('dados', len(d), 'corte', str(C.corte)[:10])
    OUT = dict(meta=dict(inicio=str(C.dias[0])[:10], fim=str(C.dias[-1])[:10], pregoes=len(C.dias),
                         corte=str(C.corte)[:10], tercos=C.tercos, candles=len(d), inicio_sinais=V.INICIO,
                         ang_n=V.ANG_N, sd_med=float(np.nanmedian(d.loc[~d['frio'], 'sd'])),
                         gest_banda={k: G['nome'] for k, G in G_BANDA.items()},
                         gest_vwap={k: G['nome'] for k, G in G_VWAP.items()},
                         dias=[str(pd.Timestamp(x))[:10] for x in C.dias]))

    # ---------------------------------------------------------- sinais
    SG = {}
    for g in ('c1', 'c2', 'hull'):
        SG[g] = C.roda(C.marca(V.sinais(d, T, g, 'banda')), G_BANDA)
        log('sinais', g, len(SG[g]))
    X = SG['c1']
    X['emp4'] = X['n_emp'] >= 4
    X['E'] = X['emp4'] & ~X['rej']                   # exaustao limpa: o candidato
    CT = C.roda(C.marca(V.sinais(d, T, 'c1', 'banda', z_min=-99.0)), G_BANDA)   # controle sem banda
    CT['E'] = (CT['n_emp'] >= 4) & ~CT['rej']
    VW = {g: C.roda(C.marca(V.sinais(d, T, g, 'vwap')), G_VWAP) for g in ('c1', 'c2')}
    log('controle', len(CT), 'vwap', {g: len(v) for g, v in VW.items()})

    # linha de base aleatoria: todo candle do pregao, lado sorteado
    ok = (~d['frio']).to_numpy() & (d['sd'].to_numpy() > 0)
    idx = np.flatnonzero(ok)
    R = pd.DataFrame(dict(i=idx, lado=RNG.choice([-1, 1], len(idx)), preco=d['c'].to_numpy()[idx],
                          data=d['data'].to_numpy()[idx]))
    R['ext'] = R['preco']
    R = C.roda(C.marca(R), G_BANDA)
    OUT['aleatorio'] = {gk: media(R[f'rs_{gk}']) for gk in G_BANDA}
    log('aleatorio', OUT['aleatorio'])

    # ---------------------------------------------------------- base por gatilho
    base = []
    for g, S in SG.items():
        lin = dict(gat=g, nome=V.GATILHOS[g], n=len(S), dia=len(S) / len(C.dias), g={})
        for gk, G in G_BANDA.items():
            cs, _ = C.cart(S, G, extra=False)
            lin['g'][gk] = dict(ev=media(S[f'rs_{gk}']), ev_is=media(S.loc[S.treino, f'rs_{gk}']),
                                ev_oos=media(S.loc[~S.treino, f'rs_{gk}']),
                                wr=float((S[f'pts_{gk}'] > 0).mean() * 100),
                                cart=cs['stats'], cart_is=cs['is_']['liquido'], cart_oos=cs['oos']['liquido'])
        base.append(lin)
    OUT['base'] = base
    log('base')

    GK = list(G_BANDA)
    # ---------------------------------------------------------- faixas (c1)
    F = {}
    F['nivel'] = dict(rot='Banda mais distante alcancada pelo movimento', lin=faixas(X, [
        ('banda 1 (ate a banda 2)', X.nivel == 1), ('banda 2 (ate a banda 3)', X.nivel == 2),
        ('banda 3 ou alem', X.nivel == 3)], GK))
    F['emp'] = dict(rot='Candles seguidos do empurrao ate a banda', lin=faixas(X, [
        (f'{k}', X.n_emp == k) for k in (1, 2, 3, 4, 5, 6)] + [('7 ou mais', X.n_emp >= 7)], GK))
    F['pav'] = dict(rot='Pavio de rejeicao do candle de virada (pts alem da abertura)', lin=faixas(X, [
        ('sem pavio (0)', X.pav_rej <= 0), ('1 a 10', (X.pav_rej > 0) & (X.pav_rej <= 10)),
        ('11 a 20', (X.pav_rej > 10) & (X.pav_rej <= 20)), ('21 a 30', (X.pav_rej > 20) & (X.pav_rej <= 30)),
        ('31 a 50', (X.pav_rej > 30) & (X.pav_rej <= 50)), ('mais de 50', X.pav_rej > 50)], GK))
    F['padrao'] = dict(rot='Padrao da virada (classificacao exclusiva, na ordem de prioridade)', lin=faixas(X, [
        ('falso rompimento', X.padrao == 'falso'), ('topo/fundo duplo', X.padrao == 'duplo'),
        ('pavio de rejeicao', X.padrao == 'rejeicao'), ('exaustao (4+ candles)', X.padrao == 'exaustao'),
        ('virada simples', X.padrao == 'simples')], GK))
    F['toque1'] = dict(rot='Numero do toque na banda 1, naquele lado, no dia', lin=faixas(X, [
        ('1o toque', X.n_toque1 == 1), ('2o toque', X.n_toque1 == 2), ('3o toque', X.n_toque1 == 3),
        ('4o toque', X.n_toque1 == 4), ('5o ou mais', X.n_toque1 >= 5)], GK))
    F['toque'] = dict(rot='Numero do toque na banda do sinal (1, 2 ou 3), naquele lado, no dia', lin=faixas(X, [
        ('1o toque', X.n_toque == 1), ('2o toque', X.n_toque == 2), ('3o toque', X.n_toque == 3),
        ('4o ou mais', X.n_toque >= 4)], GK))
    F['nsinal'] = dict(rot='Ordem do sinal no dia, naquele lado', lin=faixas(X, [
        ('1o sinal', X.n_sinal_dia == 0), ('2o a 5o', (X.n_sinal_dia >= 1) & (X.n_sinal_dia <= 4)),
        ('6o a 15o', (X.n_sinal_dia >= 5) & (X.n_sinal_dia <= 14)), ('16o ou mais', X.n_sinal_dia >= 15)], GK))
    F['ang'] = dict(rot=f'Angulo da VWAP: pts por candle nos ultimos {V.ANG_N} (negativo = VWAP andando contra o trade)',
                    lin=faixas(X, cortes(X.ang, [-np.inf, -15, -8, -4, -2, np.inf]), GK))
    qa = np.quantile(X.loc[X.treino, 'ang_sd'], [0.2, 0.4, 0.6, 0.8])
    F['ang_sd'] = dict(rot='Angulo da VWAP em passos de banda (1/3 % da VWAP) por 10 candles (quintis do treino)',
                       lin=faixas(X, cortes(X.ang_sd, [-np.inf, *qa, np.inf], '{:.2f}'), GK))
    F['ang20'] = dict(rot='Angulo da VWAP: pts por candle nos ultimos 20',
                      lin=faixas(X, cortes(X.ang20, [-np.inf, -15, -8, -4, -2, np.inf]), GK))
    F['hora'] = dict(rot='Horario do sinal', lin=faixas(X, [
        (f'{h}h', (X.hora >= h) & (X.hora < h + 1)) for h in range(9, 18)] + [('18h', X.hora >= 18)], GK))
    F['dist'] = dict(rot='Distancia da entrada ate a VWAP (pts)',
                     lin=faixas(X, cortes(X.dist_vwap, [-np.inf, 600, 800, 1000, 1300, 1700, np.inf]), GK))
    F['lado'] = dict(rot='Lado', lin=faixas(X, [('venda na banda de cima', X.lado < 0),
                                                 ('compra na banda de baixo', X.lado > 0)], GK))
    OUT['faixas'] = F
    # dentro do candidato (exaustao limpa)
    E = X[X.E]
    FE = {}
    FE['toque1'] = dict(rot='Exaustao limpa: toque na banda 1', lin=faixas(E, [
        ('1o toque', E.n_toque1 == 1), ('2o toque', E.n_toque1 == 2), ('3o toque', E.n_toque1 == 3),
        ('4o ou mais', E.n_toque1 >= 4)], GK))
    FE['ang'] = dict(rot='Exaustao limpa: angulo da VWAP (pts/candle)',
                     lin=faixas(E, cortes(E.ang, [-np.inf, -8, -4, -2, np.inf]), GK))
    FE['nivel'] = dict(rot='Exaustao limpa: banda alcancada', lin=faixas(E, [
        ('banda 1', E.nivel == 1), ('banda 2', E.nivel == 2), ('banda 3', E.nivel == 3)], GK))
    FE['emp'] = dict(rot='Exaustao limpa: candles do empurrao', lin=faixas(E, [
        ('4', E.n_emp == 4), ('5', E.n_emp == 5), ('6', E.n_emp == 6), ('7 ou mais', E.n_emp >= 7)], GK))
    OUT['faixas_E'] = FE
    # controle: a banda importa?
    OUT['controle'] = dict(
        todos=faixas(CT, cortes(CT.zext, [-np.inf, 0, 1, 2, np.inf]), GK),
        exaust=faixas(CT[CT.E], cortes(CT.loc[CT.E, 'zext'], [-np.inf, 0, 1, 2, np.inf]), GK),
        n=len(CT))
    log('faixas')

    # ---------------------------------------------------------- hipoteses (com x sem)
    HIP = [
        ('Exaustao: empurrao de 4+ candles', X.emp4),
        ('Pavio de rejeicao (>= 30 pts, o candle de virada fez o extremo)', X.rej),
        ('Falso rompimento (fechou fora da banda e voltou)', X.falso),
        ('Topo/fundo duplo na banda', X.duplo),
        ('Exaustao limpa (4+ candles, sem pavio de rejeicao)', X.E),
        ('Banda 2 ou 3', X.nivel >= 2),
        ('Banda 3', X.nivel == 3),
        ('1o toque na banda 1 do dia', X.n_toque1 == 1),
        ('1o ou 2o toque na banda 1', X.n_toque1 <= 2),
        ('1o toque na banda do sinal', X.n_toque == 1),
        ('1o sinal do dia naquele lado', X.n_sinal_dia == 0),
        ('VWAP plana (|angulo| < 2 pts/candle)', X.ang.abs() < 2),
        ('VWAP inclinada contra o trade (< -8 pts/candle)', X.ang < -8),
        ('VWAP a favor do trade (angulo > 0)', X.ang > 0),
        ('Hull 50 ja virou a favor', X.hull_fav),
        ('MACD do lado do trade', X.macd_fav),
        ('Longe da VWAP (> 800 pts)', X.dist_vwap > 800),
        ('Perto da VWAP (< 700 pts)', X.dist_vwap < 700),
        ('Exaustao limpa E 1o/2o toque', X.E & (X.n_toque1 <= 2)),
        ('Exaustao limpa E VWAP plana', X.E & (X.ang > -2)),
        ('Exaustao limpa E banda 2+', X.E & (X.nivel >= 2)),
    ]
    OUT['hip'] = {gk: [dict(nome=nm, **compara(X, gk, mk.to_numpy())) for nm, mk in HIP] for gk in GK}
    log('hipoteses')

    # ---------------------------------------------------------- VWAP como entrada
    vwe = {}
    for g, S in VW.items():
        gv = list(G_VWAP)
        vwe[g] = dict(n=len(S), lin=faixas(S, [
            ('todos', np.ones(len(S), bool)),
            ('pullback: o preco ja tinha ido a banda a favor no dia', S.ja_banda_fav),
            ('sem banda a favor antes', ~S.ja_banda_fav),
            ('VWAP a favor (> 1 pt/candle)', S.ang > 1), ('VWAP plana (-1 a 1)', S.ang.abs() <= 1),
            ('VWAP contra (< -1)', S.ang < -1),
            ('pullback E VWAP a favor', S.ja_banda_fav & (S.ang > 1)),
            ('empurrao de 4+ candles ate a VWAP', S.n_emp >= 4),
            ('topo/fundo duplo na VWAP', S.duplo),
            ('pavio de rejeicao', S.rej),
            ('1o sinal do dia naquele lado', S.n_sinal_dia == 0)], gv),
            cart={gk: C.cart(S, G, extra=False)[0] for gk, G in G_VWAP.items()})
    OUT['vwap_entrada'] = vwe
    # comparacao direta: mesma gestao (r300) banda x VWAP
    log('vwap entrada')

    # ---------------------------------------------------------- VWAP como alvo
    sa = []
    for st in (100.0, 150.0, 200.0, 300.0, ('ext', 300.0), 1e6):
        t = V.executa(C.A, X, dict(stop=st, alvo='vwap'))
        rs = V.reais(t)
        sa.append(dict(stop='sem stop' if st == 1e6 else 'extremo + 10 (max 300)' if isinstance(st, tuple) else f'{st:.0f}',
                       hit=float((t.motivo == 'alvo').mean() * 100), ev=media(rs) if st != 1e6 else None,
                       ev_is=media(rs[X.treino]) if st != 1e6 else None, ev_oos=media(rs[~X.treino]) if st != 1e6 else None,
                       fim_dia=float((t.motivo == 'fim_dia').mean() * 100)))
    t0 = V.executa(C.A, X, dict(stop=100.0, alvo=None))
    mfe = t0['mfe'].to_numpy(); dv = X['dist_vwap'].to_numpy()
    tns = V.executa(C.A, X, dict(stop=1e6, alvo=None))
    OUT['vwap_alvo'] = dict(
        stops=sa,
        p_mfe={k: float((mfe >= k).mean() * 100) for k in (100, 200, 300, 400, 500, 800)},
        p_vwap=float((mfe >= dv).mean() * 100),
        p_vwap_sem_stop=float((tns['mfe'].to_numpy() >= dv).mean() * 100),
        mae_sem_stop=[float(np.percentile(tns['mae'], p)) for p in (50, 25, 10)],
        dist_q=[float(np.percentile(dv, p)) for p in (10, 25, 50, 75, 90)],
        por_dist=F['dist']['lin'])
    log('vwap alvo')

    # ---------------------------------------------------------- carteiras
    FIL = [
        ('c1: todos os sinais nas bandas', X, np.ones(len(X), bool)),
        ('c1: exaustao (4+ candles)', X, X.emp4),
        ('c1: sem pavio de rejeicao', X, ~X.rej),
        ('c1: exaustao limpa (4+ candles, sem pavio de rejeicao)', X, X.E),
        ('c1: exaustao limpa E 1o/2o toque na banda 1', X, X.E & (X.n_toque1 <= 2)),
        ('c1: exaustao limpa E VWAP nao inclinada contra (> -2)', X, X.E & (X.ang > -2)),
        ('c1: exaustao limpa E banda 2 ou 3', X, X.E & (X.nivel >= 2)),
        ('c1: 1o toque na banda 1', X, X.n_toque1 == 1),
        ('c1: banda 2 ou 3', X, X.nivel >= 2),
        ('c2: todos', SG['c2'], np.ones(len(SG['c2']), bool)),
        ('Hull vira: todos', SG['hull'], np.ones(len(SG['hull']), bool)),
    ]
    carts = {}
    for gk, G in G_BANDA.items():
        lin = []
        for nm, S, mk in FIL:
            r, _ = C.cart(S[np.asarray(mk, bool)], G)
            lin.append(dict(nome=nm, frac=float(np.mean(mk)), n_sinais=int(np.sum(mk)), **r))
        carts[gk] = lin
        log('carteira', gk, [round(l['stats']['liquido']) for l in lin])
    OUT['carteiras'] = carts

    # ---------------------------------------------------------- robustez do candidato
    rob = {}
    grade = []
    for ne in (3, 4, 5, 6):
        for pm in (10, 20, 30, 50, 999):
            # 30 = a propria regra do candidato (sem pavio de rejeicao >= 30 no candle que fez o extremo)
            mk = (X.n_emp >= ne) & (~X.rej if pm == 30 else X.pav_rej < pm)
            r = dict(n_emp=ne, pav=('sem limite' if pm == 999 else ('sem rejeicao (regra)' if pm == 30 else f'< {pm}')),
                     n=int(mk.sum()))
            for gk in GK:
                rr = X.loc[mk, f'rs_{gk}']
                r[gk] = dict(ev=media(rr), ev_is=media(rr[X.loc[mk, 'treino']]), ev_oos=media(rr[~X.loc[mk, 'treino']]))
            grade.append(r)
    rob['grade'] = grade
    sg = []
    for st in (100.0, 150.0, 200.0, ('ext', 300.0)):
        for al in (300.0, 500.0, 'vwap'):
            G = dict(stop=st, alvo=al)
            r, _ = C.cart(E, G, extra=False)
            t = V.executa(C.A, E, G); rs = V.reais(t)
            sg.append(dict(stop='extremo + 10' if isinstance(st, tuple) else f'{st:.0f}',
                           alvo='VWAP' if al == 'vwap' else f'{al:.0f}', ev=media(rs),
                           ev_is=media(rs[E.treino]), ev_oos=media(rs[~E.treino]),
                           liq=r['stats'].get('liquido'), dd=r['stats'].get('dd_max'), fl=r['stats'].get('fator_lucro')))
    rob['stops'] = sg
    # bootstrap de dias (carteira do candidato)
    bs = {}
    for gk, G in G_BANDA.items():
        _, c = C.cart(E, G, extra=False)
        rs = V.reais(c)
        dd = c['data'].dt.normalize().to_numpy()
        ud = np.unique(dd)
        pdia = np.array([rs[dd == u].sum() for u in ud])
        sims = np.array([pdia[RNG.integers(0, len(pdia), len(pdia))].sum() for _ in range(4000)])
        bs[gk] = dict(p_prejuizo=float((sims <= 0).mean() * 100), p5=float(np.percentile(sims, 5)),
                      p50=float(np.percentile(sims, 50)), p95=float(np.percentile(sims, 95)), dias=int(len(ud)))
    rob['bootstrap'] = bs
    log('robustez')
    OUT['robustez'] = rob
    OUT['contagem'] = dict(c1=len(X), E=int(X.E.sum()), emp4=int(X.emp4.sum()), rej=int(X.rej.sum()))

    with open(os.path.join(SAIDA, 'vwap.json'), 'w', encoding='utf-8') as f:
        json.dump(limpa(OUT), f, ensure_ascii=False)

    # ---------------------------------------------------------- trade a trade
    VAR = [('E_r300', 'Exaustao limpa, alvo 300', X[X.E], 'r300'),
           ('E_r500', 'Exaustao limpa, alvo 500', X[X.E], 'r500'),
           ('E_vw', 'Exaustao limpa, alvo VWAP', X[X.E], 'vw'),
           ('E_claude', 'Exaustao limpa, gestao CLAUDE.md', X[X.E], 'claude'),
           ('E2_r300', 'Exaustao limpa na banda 2 ou 3, alvo 300', X[X.E & (X.nivel >= 2)], 'r300'),
           ('c1_r300', 'Todos c1 nas bandas, alvo 300', X, 'r300'),
           ('vw_r300', 'Entrada na VWAP (c1), alvo 300', VW['c1'], 'r300')]
    TR = {}
    for k, nome, S, gk in VAR:
        G = (G_BANDA.get(gk) or G_VWAP[gk])
        c = V.carteira(V.executa(C.A, S, G))
        c = c.assign(rs=V.reais(c))
        TR[k] = dict(nome=nome, gk=gk, alvo=G['alvo'], parcial=G.get('parcial'), trades=[dict(
            i=int(r.i), v0=int(r.v0), j=int(r.j_ext), i_sai=int(r.i_sai), lado=int(r.lado),
            data=r.data.strftime('%d/%m/%y %H:%M'), pe=float(r.preco), ps=float(r.preco_sai),
            stop=float(r.stop_pts), mot=r.motivo, pts=float(r.pts), rs=float(r.rs),
            mfe=float(r.mfe), mae=float(r.mae), nivel=int(r.nivel), emp=int(r.n_emp),
            toque=int(r.n_toque1), ang=round(float(r.ang), 1), pad=r.padrao, pav=float(r.pav_rej),
            dv=round(float(r.dist_vwap))) for r in c.itertuples()])
    with open(os.path.join(SAIDA, 'vwap_trades.json'), 'w', encoding='utf-8') as f:
        json.dump(limpa(TR), f, ensure_ascii=False)
    log('ok')


if __name__ == '__main__':
    main()
