# -*- coding: utf-8 -*-
"""
Filtros de TENDENCIA GERAL e CONSOLIDACAO -> tendencia.html / TENDENCIA.md

Pergunta: o contexto maior (ultimos 10-100 candles, medias longas, o dia,
o dia anterior, lateralidade) melhora o setup EMA21?

Todas as medidas sao ORIENTADAS PELO LADO DO TRADE (positivo = a favor) e
tomadas no candle ANTERIOR AO RECUO (j = v0 - 1), para que os 2-3 candles
contra do proprio setup nao contaminem a leitura da tendencia. As medidas
de nivel (preco x media, dia) usam o candle do trigger.

Preco sintetico sem gaps: no grafico PI cada candle anda exatamente 100 pts,
entao o caminho "soma dos sentidos x 100" e o preco sem os saltos entre
pregoes. Janelas atravessam dias (o grafico tambem atravessa).

Duas gestoes:
  'claude' stop 100, parcial 50% em +100 (stop na media), alvo 300
  'r400'   stop 100, alvo 400, sem parcial   (a recomendada no relatorio)
Dois conjuntos: todos os sinais / so os com filtro picado (inversoes >= 11).
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
RNG = np.random.default_rng(7)
GESTOES = {'claude': {}, 'r400': dict(stop=100.0, alvo=400.0, parcial=False)}
NOME_G = {'claude': 'Stop 100 / parcial +100 / alvo 300', 'r400': 'Stop 100 / alvo 400 sem parcial'}
CONJ = {'todos': 'Todos os sinais', 'picado': 'So sinais com filtro picado'}
JANELAS = [10, 20, 30, 50, 100, 150, 200]


def log(*a):
    print(f'[{time.time() - T0:5.1f}s]', *a, flush=True)


# ================================================================ atributos
REG = [5, 10, 20, 30]


def regressao(y, N):
    """Inclinacao (pts por candle) e R2 da regressao linear dos ultimos N
    valores, terminando em cada candle (inclusive)."""
    y = pd.Series(y)
    t = pd.Series(np.arange(len(y), dtype=float))
    cov = t.rolling(N).cov(y)
    var_t = t.rolling(N).var()
    incl = (cov / var_t).to_numpy()
    r = t.rolling(N).corr(y).to_numpy()
    return incl, r ** 2


def atributos(d, S):
    o = d['o'].to_numpy(); c = d['c'].to_numpy()
    h = d['h'].to_numpy(); l = d['l'].to_numpy()
    em = d['ema'].to_numpy(); hu = d['hma'].to_numpy()
    sent = np.sign(c - o)
    P = np.cumsum(sent) * 100.0                       # preco sintetico sem gaps
    ema50 = E.ema(c, 50); ema100 = E.ema(c, 100); ema200 = E.ema(c, 200)
    ema200_P = E.ema(P, 200)
    larg = (d['kc_sup'] - d['kc_inf']).to_numpy()
    larg_med = pd.Series(larg).rolling(500, min_periods=100).median().to_numpy()
    acima = np.sign(c - em)
    cruza = np.r_[0, (acima[1:] != acima[:-1]).astype(int)]
    cum_cruza = np.cumsum(cruza)

    # contexto diario
    dia = d['dia']
    g_dia = d.groupby('dia')
    abre = g_dia['o'].transform('first').to_numpy()
    max_ate = g_dia['h'].cummax().to_numpy()
    min_ate = g_dia['l'].cummin().to_numpy()
    resumo_dia = g_dia.agg(o=('o', 'first'), c=('c', 'last'), h=('h', 'max'), l=('l', 'min'))
    ant = resumo_dia.shift(1)
    ontem_mov = (ant['c'] - ant['o']).reindex(dia).to_numpy()
    ontem_fech = ant['c'].reindex(dia).to_numpy()
    ontem_pos = ((ant['c'] - ant['l']) / (ant['h'] - ant['l'])).reindex(dia).to_numpy()

    X = S.copy()
    j = (X['v0'] - 1).to_numpy()
    g = X['i'].to_numpy()
    lado = X['lado'].to_numpy()
    for N in JANELAS:
        a = np.clip(j - N, 0, None)
        net = (P[j] - P[a]) / 100.0 * lado              # candles a favor - contra
        X[f'mov_{N}'] = net
        X[f'er_{N}'] = np.abs(net) / N                   # eficiencia 0 = lateral, 1 = reta
        rng_ = np.array([P[a_:j_ + 1].max() - P[a_:j_ + 1].min() for a_, j_ in zip(a, j)]) / 100.0
        X[f'amp_{N}'] = rng_ / N                         # amplitude em candles / N
        X[f'cruz_{N}'] = cum_cruza[j] - cum_cruza[a]     # cruzamentos do preco pela EMA21
        X[f'incl_ema_{N}'] = (em[j] - em[a]) * lado
        X[f'incl_hull_{N}'] = (hu[j] - hu[a]) * lado
    for N in REG:
        inc, r2 = regressao(em, N)
        X[f'reg_{N}'] = inc[g] * lado          # a favor do trade, pts por candle
        X[f'reg_abs_{N}'] = np.abs(inc[g])     # planitude, qualquer lado
        X[f'reg_r2_{N}'] = r2[g]               # 1 = EMA reta; baixo = ondulando
        if N in (5, 10, 20):
            dif = (em[g] - em[np.clip(g - N, 0, None)]) / N   # medida direta, pts por candle
            X[f'dir_{N}'] = dif * lado
            X[f'dir_abs_{N}'] = np.abs(dif)
    X['pos_ema50'] = (c[g] - ema50[g]) * lado
    X['pos_ema100'] = (c[g] - ema100[g]) * lado
    X['pos_ema200'] = (c[g] - ema200[g]) * lado
    X['ema21_x_200'] = (em[g] - ema200[g]) * lado
    X['incl_ema200_50'] = (ema200_P[g] - ema200_P[np.clip(g - 50, 0, None)]) * lado
    X['dia_mov'] = (c[g] - abre[g]) * lado
    faixa = max_ate[g] - min_ate[g]
    pos = np.where(faixa > 0, (c[g] - min_ate[g]) / np.where(faixa > 0, faixa, 1), 0.5)
    X['dia_pos'] = np.where(lado > 0, pos, 1 - pos)      # 1 = no extremo a favor do dia
    X['ontem_mov'] = ontem_mov[g] * lado
    X['gap'] = (abre[g] - ontem_fech[g]) * lado
    X['ontem_pos'] = np.where(lado > 0, ontem_pos[g], 1 - ontem_pos[g])
    X['kc_rel'] = larg[g] / larg_med[g]
    return X


FAMILIAS = [
    ('Direcao dos ultimos candles (antes do recuo)', 'Candles a favor menos contra. Negativo = mercado vinha contra o trade.',
     [f'mov_{N}' for N in JANELAS]),
    ('Consolidacao: eficiencia do movimento', '|a favor - contra| / N. Perto de 0 = lateral (ia e voltava); perto de 1 = tendencia limpa.',
     [f'er_{N}' for N in JANELAS]),
    ('Consolidacao: amplitude', 'Distancia entre maxima e minima do caminho, em candles, dividida por N. Baixa = preco preso numa faixa.',
     [f'amp_{N}' for N in JANELAS]),
    ('Consolidacao: cruzamentos da EMA 21', 'Quantas vezes o preco trocou de lado da EMA 21 na janela.',
     [f'cruz_{N}' for N in JANELAS]),
    ('Inclinacao das medias na janela', 'Quanto a EMA 21 / a Hull 50 andaram a favor do trade (pts).',
     [f'incl_ema_{N}' for N in (20, 50, 100)] + [f'incl_hull_{N}' for N in (20, 50, 100)]),
    ('Regressao linear da EMA 21', 'Inclinacao da reta ajustada a EMA 21 nos ultimos N candles ate o trigger, em pts por candle. '
     'A favor = no sentido do trade; absoluta = plana ou nao, qualquer lado; R2 = quao reta (1) ou ondulada (0) esta a EMA.',
     [f'reg_{N}' for N in REG] + [f'reg_abs_{N}' for N in REG] + [f'reg_r2_{N}' for N in (10, 20)]),
    ('Variacao direta da EMA 21', '(EMA 21 agora - EMA 21 de N candles atras) / N, em pts por candle, ate o trigger. '
     'Mesma unidade da regressao, para comparar as duas formas de medir.',
     [f'dir_{N}' for N in (5, 10, 20)] + [f'dir_abs_{N}' for N in (5, 10, 20)]),
    ('Medias longas', 'Preco e EMA 21 contra medias de 50/100/200 candles, orientado pelo lado (positivo = a favor).',
     ['pos_ema50', 'pos_ema100', 'pos_ema200', 'ema21_x_200', 'incl_ema200_50']),
    ('Contexto do dia', 'Movimento desde a abertura, posicao na faixa do dia (1 = no extremo a favor), dia anterior, gap e largura do Keltner (volatilidade).',
     ['dia_mov', 'dia_pos', 'ontem_mov', 'ontem_pos', 'gap', 'kc_rel']),
]
ROTULO = {
    **{f'mov_{N}': f'Direcao {N} candles' for N in JANELAS},
    **{f'er_{N}': f'Eficiencia {N} candles' for N in JANELAS},
    **{f'amp_{N}': f'Amplitude {N} candles' for N in JANELAS},
    **{f'cruz_{N}': f'Cruzamentos EMA {N} candles' for N in JANELAS},
    **{f'incl_ema_{N}': f'Inclinacao EMA21 {N} candles' for N in JANELAS},
    **{f'incl_hull_{N}': f'Inclinacao Hull {N} candles' for N in JANELAS},
    **{f'reg_{N}': f'Regressao EMA21 {N} candles (a favor)' for N in REG},
    **{f'reg_abs_{N}': f'Regressao EMA21 {N} candles (absoluta)' for N in REG},
    **{f'reg_r2_{N}': f'R2 da EMA21 {N} candles' for N in REG},
    **{f'dir_{N}': f'Variacao direta EMA21 {N} candles (a favor)' for N in (5, 10, 20)},
    **{f'dir_abs_{N}': f'Variacao direta EMA21 {N} candles (absoluta)' for N in (5, 10, 20)},
    'pos_ema50': 'Preco x EMA 50', 'pos_ema100': 'Preco x EMA 100', 'pos_ema200': 'Preco x EMA 200',
    'ema21_x_200': 'EMA 21 x EMA 200', 'incl_ema200_50': 'Inclinacao da EMA 200 (50 candles)',
    'dia_mov': 'Movimento desde a abertura do dia', 'dia_pos': 'Posicao na faixa do dia',
    'ontem_mov': 'Dia anterior (fech - abert)', 'ontem_pos': 'Fechamento de ontem na faixa de ontem',
    'gap': 'Gap de abertura', 'kc_rel': 'Largura do Keltner / mediana 500',
}


def fmt_c(v):
    if np.isinf(v):
        return '-inf' if v < 0 else '+inf'
    return f'{v:.2f}'.rstrip('0').rstrip('.')


def cortes_treino(x_is, q=5):
    cs = np.unique(np.quantile(x_is.dropna(), np.linspace(0, 1, q + 1)))
    cs[0] = -np.inf; cs[-1] = np.inf
    return cs


def tabela(X, col, cs):
    fa = pd.cut(X[col], cs, right=False)
    out = []
    for k, (a, b) in enumerate(zip(cs[:-1], cs[1:])):
        m = (fa.cat.codes == k).to_numpy()
        g = X[m]
        gi = g[g['treino']]; go = g[~g['treino']]
        out.append(dict(faixa=f'{fmt_c(a)} a {fmt_c(b)}', n=int(m.sum()),
                        ev=float(g['rs'].mean()) if len(g) else None,
                        wr=float((g['pts'] > 0).mean() * 100) if len(g) else None,
                        ev_is=float(gi['rs'].mean()) if len(gi) else None, n_is=len(gi),
                        ev_oos=float(go['rs'].mean()) if len(go) else None, n_oos=len(go),
                        compra=float(g.loc[g.lado > 0, 'rs'].mean()) if (g.lado > 0).any() else None,
                        venda=float(g.loc[g.lado < 0, 'rs'].mean()) if (g.lado < 0).any() else None))
    return out


def tstat(x):
    x = np.asarray(x, float)
    if len(x) < 3 or x.std(ddof=1) == 0:
        return 0.0
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x)))


def candidatos(X, cols):
    """Filtros binarios 'manter acima/abaixo do quintil do treino'."""
    res = []
    rs = X['rs'].to_numpy(); tr = X['treino'].to_numpy()
    base_is = rs[tr].mean(); base_oos = rs[~tr].mean()
    for col in cols:
        x = X[col].to_numpy()
        qs = np.unique(np.quantile(x[tr & ~np.isnan(x)], [0.2, 0.4, 0.6, 0.8]))
        for q in qs:
            for sinal, mk in (('>=', x >= q), ('<', x < q)):
                mk = mk & ~np.isnan(x)
                if (mk & tr).sum() < 0.3 * tr.sum():
                    continue
                res.append(dict(col=col, nome=f'{ROTULO[col]} {sinal} {fmt_c(q)}', op=sinal, q=float(q),
                                frac=float(mk.mean()), n_is=int((mk & tr).sum()), n_oos=int((mk & ~tr).sum()),
                                ev_is=float(rs[mk & tr].mean()), ev_oos=float(rs[mk & ~tr].mean()),
                                t_is=tstat(rs[mk & tr]), ganho_is=float(rs[mk & tr].mean() - base_is),
                                ganho_oos=float(rs[mk & ~tr].mean() - base_oos)))
    return res


def mapa(X, dir_col, cons_col):
    """Direcao (tercos) x consolidacao (tercos), cortes no treino."""
    tr = X['treino']
    qd = np.quantile(X.loc[tr, dir_col], [1 / 3, 2 / 3])
    qc = np.quantile(X.loc[tr, cons_col], [1 / 3, 2 / 3])
    di = np.digitize(X[dir_col], qd); ci = np.digitize(X[cons_col], qc)
    cel = []
    for a in range(3):
        for b in range(3):
            g = X[(di == a) & (ci == b)]
            cel.append(dict(dir=a, cons=b, n=len(g), ev=float(g['rs'].mean()) if len(g) else None,
                            ev_is=float(g.loc[g['treino'], 'rs'].mean()) if g['treino'].any() else None,
                            ev_oos=float(g.loc[~g['treino'], 'rs'].mean()) if (~g['treino']).any() else None))
    return dict(dir_col=dir_col, cons_col=cons_col, qd=qd.tolist(), qc=qc.tolist(), celulas=cel)


def stats_cart(d, sig, G, corte):
    t = E.executa(d, sig, 'fecha', G)
    c = E.carteira(t)
    st = E.estatisticas(c)
    Ga = dict(G); Ga['atravessa'] = 5.0
    ca = E.carteira(E.executa(d, sig, 'fecha', Ga))
    rs = E.reais(c)
    return dict(stats=st, is_=E.estatisticas(c[c['data'] < corte]), oos=E.estatisticas(c[c['data'] >= corte]),
                atravessa=E.estatisticas(ca).get('liquido', 0.0),
                eq=np.round(np.cumsum(rs), 1).tolist(), dt=c['data'].dt.strftime('%d/%m').tolist())


# ================================================================== main
def main():
    d = E.indicadores(E.carrega())
    dias = sorted(d['dia'].unique())
    corte = dias[int(len(dias) * 0.6)]
    S = E.sinais(d)
    S['treino'] = S['data'] < corte
    X0 = atributos(d, S)
    log('sinais', len(X0), 'corte', str(corte)[:10])

    OUT = dict(meta=dict(sinais=len(X0), corte=str(corte)[:10], inicio=str(dias[0])[:10], fim=str(dias[-1])[:10],
                         pregoes=len(dias)), familias=[], mapas={}, candidatos={}, carteiras={}, placebo={})
    cols_todas = [c for _, _, cs in FAMILIAS for c in cs]

    XS = {}
    for gk, G in GESTOES.items():
        t = E.executa(d, X0, 'fecha', G)
        X = X0.copy()
        X['pts'] = t['pts'].to_numpy(); X['rs'] = E.reais(t)
        for ck in CONJ:
            XS[(gk, ck)] = X if ck == 'todos' else X[X['inversoes'] >= 11].copy()

    # ---- tabelas por familia (cortes definidos no treino de TODOS os sinais)
    cortes = {col: cortes_treino(X0.loc[X0['treino'], col]) for col in cols_todas}
    for fam, desc, cols in FAMILIAS:
        blocos = []
        for col in cols:
            tabs = {f'{gk}|{ck}': tabela(XS[(gk, ck)], col, cortes[col]) for gk in GESTOES for ck in CONJ}
            geral = {f'{gk}|{ck}': dict(ev=float(XS[(gk, ck)]['rs'].mean()),
                                        ev_is=float(XS[(gk, ck)].loc[XS[(gk, ck)]['treino'], 'rs'].mean()),
                                        ev_oos=float(XS[(gk, ck)].loc[~XS[(gk, ck)]['treino'], 'rs'].mean()))
                     for gk in GESTOES for ck in CONJ}
            blocos.append(dict(col=col, rotulo=ROTULO[col], tabs=tabs, geral=geral))
        OUT['familias'].append(dict(familia=fam, desc=desc, blocos=blocos))
    log('tabelas')

    # ---- mapas direcao x consolidacao
    for gk in GESTOES:
        for ck in CONJ:
            for N in (20, 30, 50):
                OUT['mapas'][f'{gk}|{ck}|{N}'] = mapa(XS[(gk, ck)], f'mov_{N}', f'er_{N}')
    log('mapas')

    # ---- candidatos (escolha no treino) + placebo
    for gk in GESTOES:
        for ck in CONJ:
            X = XS[(gk, ck)]
            cand = candidatos(X, cols_todas)
            cand.sort(key=lambda r: r['t_is'], reverse=True)
            base_t = tstat(X.loc[X['treino'], 'rs'])
            OUT['candidatos'][f'{gk}|{ck}'] = dict(base_t=base_t, lista=cand,
                                                   base_is=float(X.loc[X['treino'], 'rs'].mean()),
                                                   base_oos=float(X.loc[~X['treino'], 'rs'].mean()))
            # placebo: filtros aleatorios que mantem a mesma fracao dos sinais
            melhores = cand[:10]
            rs = X['rs'].to_numpy(); tr = X['treino'].to_numpy()
            plac = []
            for _ in range(2000):
                fr = RNG.uniform(0.3, 0.8)
                mk = RNG.random(len(X)) < fr
                plac.append((tstat(rs[mk & tr]), rs[mk & ~tr].mean() - rs[~tr].mean()))
            plac = np.array(plac)
            melhor_t = np.array([c['t_is'] for c in cand])
            OUT['placebo'][f'{gk}|{ck}'] = dict(
                p95_t=float(np.percentile(plac[:, 0], 95)), p99_t=float(np.percentile(plac[:, 0], 99)),
                max_t_real=float(melhor_t.max()) if len(melhor_t) else None,
                frac_melhora_oos_top10=float(np.mean([c['ganho_oos'] > 0 for c in melhores])) if melhores else None,
                frac_melhora_oos_todos=float(np.mean([c['ganho_oos'] > 0 for c in cand])) if cand else None,
                frac_melhora_oos_bons_is=float(np.mean([c['ganho_oos'] > 0 for c in cand if c['ganho_is'] > 0])) if cand else None,
                n_cand=len(cand))
    log('candidatos')

    # ---- carteiras: base e os 3 melhores do treino de cada combinacao
    def aplica(X, c):
        x = X[c['col']]
        return X[(x >= c['q']) if c['op'] == '>=' else (x < c['q'])]

    for gk, G in GESTOES.items():
        for ck in CONJ:
            X = XS[(gk, ck)]
            linhas = [dict(nome='sem filtro de tendencia', **stats_cart(d, X, G, corte))]
            vistos = set()
            for c in OUT['candidatos'][f'{gk}|{ck}']['lista']:
                if c['col'] in vistos:
                    continue
                vistos.add(c['col'])
                linhas.append(dict(nome=c['nome'], cand=c, **stats_cart(d, aplica(X, c), G, corte)))
                if len(linhas) >= 6:
                    break
            OUT['carteiras'][f'{gk}|{ck}'] = linhas
            log('carteira', gk, ck, [round(l['stats']['liquido']) for l in linhas])

    # ---- hipoteses do usuario, definidas a priori (sem escolher corte)
    hip = []
    Q = {k: float(np.nanquantile(X0.loc[X0['treino'], k], 0.2)) for k in ('reg_abs_10', 'reg_abs_20', 'reg_r2_10', 'dir_abs_10')}
    Q2 = {k: float(np.nanquantile(X0.loc[X0['treino'], k], 0.5)) for k in ('reg_10', 'dir_10')}
    OUT['limiares_hip'] = dict(Q=Q, Q2=Q2)
    for gk, G in GESTOES.items():
        for ck in CONJ:
            X = XS[(gk, ck)]
            for nome, mk in [
                ('20 candles vinham contra o trade (mov_20 < 0)', X['mov_20'] < 0),
                ('20 candles vinham a favor (mov_20 > 0)', X['mov_20'] > 0),
                ('30 candles vinham contra (mov_30 < 0)', X['mov_30'] < 0),
                ('30 candles vinham a favor (mov_30 > 0)', X['mov_30'] > 0),
                ('Consolidado: eficiencia 30 < 0,2', X['er_30'] < 0.2),
                ('Em tendencia: eficiencia 30 >= 0,4', X['er_30'] >= 0.4),
                ('Consolidado: 4+ cruzamentos da EMA em 30', X['cruz_30'] >= 4),
                ('Tendencia a favor e limpa: mov_30 >= 12 (er >= 0,4)', X['mov_30'] >= 12),
                ('Tendencia contra e limpa: mov_30 <= -12', X['mov_30'] <= -12),
                ('EMA 21 plana: |regressao 10| no 1o quintil do treino', X['reg_abs_10'] < Q['reg_abs_10']),
                ('EMA 21 plana: |regressao 20| no 1o quintil do treino', X['reg_abs_20'] < Q['reg_abs_20']),
                ('EMA 21 inclinada a favor: regressao 10 acima da mediana', X['reg_10'] >= Q2['reg_10']),
                ('EMA 21 plana: |variacao direta 10| no 1o quintil do treino', X['dir_abs_10'] < Q['dir_abs_10']),
                ('EMA 21 inclinada a favor: variacao direta 10 acima da mediana', X['dir_10'] >= Q2['dir_10']),
                ('EMA 21 ondulada: R2 10 no 1o quintil', X['reg_r2_10'] < Q['reg_r2_10']),
                ('Preco a favor da EMA 200', X['pos_ema200'] > 0),
                ('Dia a favor (preco x abertura)', X['dia_mov'] > 0),
            ]:
                g = X[mk.to_numpy()]
                r_ = X.loc[~mk.to_numpy(), 'rs']
                if len(g) < 20 or len(r_) < 20:
                    continue
                hip.append(dict(gestao=gk, conj=ck, nome=nome, n=len(g), frac=len(g) / len(X),
                                ev=float(g['rs'].mean()), ev_is=float(g.loc[g['treino'], 'rs'].mean()),
                                ev_oos=float(g.loc[~g['treino'], 'rs'].mean()),
                                resto=float(X.loc[~mk.to_numpy(), 'rs'].mean()),
                                n_is=int(g['treino'].sum()), n_oos=int((~g['treino']).sum()),
                                t_dif=float((g['rs'].mean() - r_.mean()) / np.sqrt(g['rs'].var() / len(g) + r_.var() / len(r_)))))
    OUT['hipoteses'] = hip

    # ---- filtros a priori em carteira (evitar EMA plana / ondulada / consolidado)
    Qe = {k: float(np.nanquantile(X0.loc[X0['treino'], k], 0.2)) for k in ('dir_abs_10', 'reg_abs_10', 'reg_r2_10')}
    FILT = [
        ('sem filtro de tendencia', lambda X: np.ones(len(X), bool)),
        (f"evitar EMA 21 plana: variacao direta 10 >= {Qe['dir_abs_10']:.1f} pts/candle", lambda X: X['dir_abs_10'] >= Qe['dir_abs_10']),
        (f"evitar EMA 21 plana: regressao 10 >= {Qe['reg_abs_10']:.1f} pts/candle", lambda X: X['reg_abs_10'] >= Qe['reg_abs_10']),
        (f"evitar EMA 21 ondulada: R2 10 >= {Qe['reg_r2_10']:.2f}", lambda X: X['reg_r2_10'] >= Qe['reg_r2_10']),
        ('evitar consolidado em 100 candles: eficiencia 100 >= 0,08', lambda X: X['er_100'] >= 0.08),
        ('evitar mercado vindo contra: direcao 30 > 0', lambda X: X['mov_30'] > 0),
        ('EMA plana (direta) + ondulada + consolidado 100', lambda X: (X['dir_abs_10'] >= Qe['dir_abs_10']) &
         (X['reg_r2_10'] >= Qe['reg_r2_10']) & (X['er_100'] >= 0.08)),
    ]
    OUT['filtros_apriori'] = {}
    for gk, G in GESTOES.items():
        for ck in CONJ:
            X = XS[(gk, ck)]
            linhas = []
            for nome, f in FILT:
                mk = np.asarray(f(X), bool)
                linhas.append(dict(nome=nome, frac=float(mk.mean()), **stats_cart(d, X[mk], G, corte)))
            OUT['filtros_apriori'][f'{gk}|{ck}'] = linhas
            log('apriori', gk, ck, [round(l['stats']['liquido']) for l in linhas], [round(l['oos']['liquido']) for l in linhas])

    # ---- consolidacao em escala longa: janela x limiar, direcao, combinacao com picado
    cons = dict(grade=[], direcao=[], combina=[])
    X = XS[('r400', 'todos')]; Xc = XS[('claude', 'todos')]
    for N in (30, 50, 100, 150, 200):
        for thr in (0.04, 0.06, 0.08, 0.10, 0.12, 0.15):
            for gk, XX in (('r400', X), ('claude', Xc)):
                sc = stats_cart(d, XX[XX[f'er_{N}'] >= thr], GESTOES[gk], corte)
                cons['grade'].append(dict(gestao=gk, N=N, thr=thr, n=sc['stats']['trades'], liq=sc['stats']['liquido'],
                                          fl=sc['stats']['fator_lucro'], dd=sc['stats']['dd_max'],
                                          is_=sc['is_'].get('liquido', 0.0), oos=sc['oos'].get('liquido', 0.0)))
    log('grade consolidacao')
    for gk, XX in (('r400', X), ('claude', Xc)):
        for nome, mk in [('sem filtro', np.ones(len(XX), bool)),
                         ('consolidado 100 (eficiencia < 0,08)', XX['er_100'] < 0.08),
                         ('fora da consolidacao 100 (eficiencia >= 0,08)', XX['er_100'] >= 0.08),
                         ('  tendencia de 100 candles A FAVOR do trade', XX['mov_100'] >= 8),
                         ('  tendencia de 100 candles CONTRA o trade', XX['mov_100'] <= -8),
                         ('so picado', XX['inversoes'] >= 11),
                         ('fora da consolidacao 100 E picado', (XX['er_100'] >= 0.08) & (XX['inversoes'] >= 11)),
                         ('fora da consolidacao 100 OU picado', (XX['er_100'] >= 0.08) | (XX['inversoes'] >= 11))]:
            sc = stats_cart(d, XX[np.asarray(mk, bool)], GESTOES[gk], corte)
            alvo = 'combina' if 'picado' in nome else 'direcao'
            cons[alvo].append(dict(gestao=gk, nome=nome, **sc))
    # contexto do dia: trade CONTRA o movimento desde a abertura (achado da busca)
    dia_l = []
    for gk, G in GESTOES.items():
        for ck in CONJ:
            XX = XS[(gk, ck)]
            for nome, mk in [('sem filtro', np.ones(len(XX), bool)),
                             ('dia contra o trade: preco > 100 pts contra a abertura', XX['dia_mov'] < -100),
                             ('dia a favor ou neutro', XX['dia_mov'] >= -100),
                             ('dia contra + fora da consolidacao 100', (XX['dia_mov'] < -100) & (XX['er_100'] >= 0.08))]:
                dia_l.append(dict(gestao=gk, conj=ck, nome=nome, **stats_cart(d, XX[np.asarray(mk, bool)], G, corte)))
    cons['dia'] = dia_l
    OUT['consolidacao'] = cons
    log('consolidacao')

    # ---- varredura de limiar: manter sinais com atributo >= decil
    VARR = ['dir_abs_10', 'reg_abs_10', 'reg_r2_10', 'dir_10', 'reg_10', 'er_100', 'er_30', 'mov_30', 'amp_50', 'cruz_30', 'dia_mov']
    OUT['varredura'] = {}
    for gk in GESTOES:
        for ck in CONJ:
            X = XS[(gk, ck)]
            for col in VARR:
                qs = np.nanquantile(X0.loc[X0['treino'], col], np.linspace(0, 0.8, 9))
                pts_ = []
                for k, q in enumerate(qs):
                    mk = (X[col] >= q).to_numpy()
                    g = X[mk]
                    pts_.append(dict(pct_corte=int(k * 10), limiar=float(q), n=len(g),
                                     ev_is=float(g.loc[g['treino'], 'rs'].mean()) if g['treino'].any() else None,
                                     ev_oos=float(g.loc[~g['treino'], 'rs'].mean()) if (~g['treino']).any() else None))
                OUT['varredura'][f'{gk}|{ck}|{col}'] = pts_
    OUT['varredura_cols'] = VARR

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

    with open(os.path.join(SAIDA, 'tendencia.json'), 'w', encoding='utf-8') as f:
        json.dump(limpa(OUT), f, ensure_ascii=False)
    log('ok')


if __name__ == '__main__':
    main()
