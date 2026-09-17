# -*- coding: utf-8 -*-
"""
IMPULSO antes do recuo e PAVIOS do trigger -> impulso.html / IMPULSO.md

Pergunta 1: movimentos amplos A FAVOR do trade antes da retracao (o preco
  chegando perto da banda de Keltner, o MACD chegando na Bollinger 1000)
  melhoram o setup EMA21?
Pergunta 2: o padrao de pavios medido no projeto anterior
  (Backtest-Momentum-GraficoPI: PAVIO_CONTRA.md / HULL_CONTRA.md)
  continua valendo quando o trigger toca a EMA 21?
    a) pavio do lado do FECHAMENTO <= 10% do corpo melhor que > 10%
       (o corte do HullRetracao_Azul)
    b) pavio do lado da ABERTURA: quanto menor, melhor; a faixa 25-90%
       (PavioContra_Magenta) piora; a faixa 5-25% (PavioFavor_Verde)
       nao separa dentro da Hull a favor.

Impulso: medido na perna a favor que termina no candle ANTERIOR ao recuo
(j = v0 - 1), no mesmo pregao. Orientado pelo lado do trade.
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
RNG = np.random.default_rng(11)
GESTOES = {'claude': {}, 'r400': dict(stop=100.0, alvo=400.0, parcial=False)}
JAN = [10, 20, 30]


def log(*a):
    print(f'[{time.time() - T0:5.1f}s]', *a, flush=True)


# ================================================================ atributos
def impulso(d, S):
    o = d['o'].to_numpy(); c = d['c'].to_numpy()
    h = d['h'].to_numpy(); l = d['l'].to_numpy()
    em = d['ema'].to_numpy(); at = d['atr'].to_numpy(); rg = d['rng_med'].to_numpy()
    sd = pd.Series(c).rolling(E.EMA_PER).std(ddof=0).to_numpy()
    mc = d['macd'].to_numpy()
    bs = d['bb_sup'].to_numpy(); bi = d['bb_inf'].to_numpy()
    bm = (bs + bi) / 2; bw = (bs - bi) / 2
    dia = d['dia'].to_numpy()
    X = S.copy()
    cols = {}
    for r in X.itertuples(index=False):
        lado = r.lado; v0 = r.v0; g = r.i; j = v0 - 1
        js = np.arange(v0, g + 1)
        ext_rec = l[js].min() if lado > 0 else h[js].max()
        ini_dia = j
        while ini_dia - 1 >= 0 and dia[ini_dia - 1] == dia[g]:
            ini_dia -= 1
        for W in JAN:
            a = max(ini_dia, j - W + 1)
            if j < a:
                vals = dict.fromkeys(['imp', 'recuo', 'ret', 'pico_dist', 'kc', 'kc_toques', 'zatr', 'zsd', 'bb', 'macd_pico'], np.nan)
            else:
                w = np.arange(a, j + 1)
                if lado > 0:
                    k = w[np.argmax(h[w][::-1]) * -1 - 1]          # ultima ocorrencia do pico
                    pico = h[k]; base = l[a:k + 1].min()
                    afa = h[w] - em[w]
                    bb = (mc[w] - bm[w]) / bw[w]
                else:
                    k = w[np.argmin(l[w][::-1]) * -1 - 1]
                    pico = l[k]; base = h[a:k + 1].max()
                    afa = em[w] - l[w]
                    bb = (bm[w] - mc[w]) / bw[w]
                imp = (pico - base) * lado
                recuo = (pico - ext_rec) * lado
                vals = dict(imp=imp, recuo=recuo, ret=recuo / imp if imp > 0 else np.nan,
                            pico_dist=j - k, kc=np.nanmax(afa / (E.KC_DESV * rg[w])), kc_toques=int(np.sum(afa >= E.KC_DESV * rg[w])),
                            zatr=np.nanmax(afa / rg[w]), zsd=np.nanmax(afa / sd[w]),
                            bb=np.nanmax(bb) if np.isfinite(bb).any() else np.nan,
                            macd_pico=np.nanmax(mc[w] * lado) / at[g])
            for kk, v in vals.items():
                cols.setdefault(f'{kk}_{W}', []).append(v)
    for kk, v in cols.items():
        X[kk] = v
    return X


def eficiencia(d, S, N=100):
    """|candles a favor - contra| / N nos N candles antes do recuo (tendencia.py)."""
    sent = np.sign(d['c'].to_numpy() - d['o'].to_numpy())
    P = np.cumsum(sent) * 100.0
    j = (S['v0'] - 1).to_numpy(); a = np.clip(j - N, 0, None)
    return np.abs((P[j] - P[a]) / 100.0) / N


FAMILIAS = [
    ('Tamanho do impulso', 'Perna a favor que termina no candle antes do recuo: do extremo contra ao pico, em pts, dentro da janela e do pregao.',
     [f'imp_{W}' for W in JAN]),
    ('Distancia ate a banda de Keltner (EMA 21 +- 2,5 x range medio 21, padrao Nelogica)', 'Maior (maxima - EMA21) / (Keltner superior - EMA21) na janela, na compra (venda: espelho). '
     '1 = encostou na banda, acima de 1 = passou. E quantos candles passaram da banda.',
     [f'kc_{W}' for W in JAN] + [f'kc_toques_{W}' for W in JAN] + [f'zatr_{W}' for W in JAN] + [f'zsd_{W}' for W in JAN]),
    ('MACD x Bollinger 1000 / 1,0', 'Maior (MACD - media da Bollinger) / meia largura da banda na janela, a favor do trade. 1 = MACD tocou a banda. '
     'E o pico do MACD em ATRs.',
     [f'bb_{W}' for W in JAN] + [f'macd_pico_{W}' for W in JAN]),
    ('Recuo', 'Profundidade do recuo desde o pico (pts), recuo / impulso e candles entre o pico e o inicio do recuo.',
     [f'recuo_{W}' for W in JAN] + [f'ret_{W}' for W in JAN] + [f'pico_dist_{W}' for W in JAN]),
]
ROT = {}
for W in JAN:
    ROT.update({f'imp_{W}': f'Impulso {W} (pts)', f'kc_{W}': f'Keltner: posicao maxima {W}', f'kc_toques_{W}': f'Keltner: candles alem da banda ({W})', f'zatr_{W}': f'Maior afastamento da EMA 21 em ranges medios ({W})',
                f'zsd_{W}': f'Maior afastamento da EMA 21 em desvios-padrao 21 ({W})',
                f'bb_{W}': f'MACD na Bollinger: posicao maxima {W}', f'macd_pico_{W}': f'Pico do MACD / ATR ({W})',
                f'recuo_{W}': f'Recuo desde o pico {W} (pts)', f'ret_{W}': f'Recuo / impulso ({W})', f'pico_dist_{W}': f'Candles desde o pico ({W})'})

FAIXAS_PAV = [(-1, 0.1, '0'), (0.1, 10.1, '5-10'), (10.1, 25.1, '15-25'), (25.1, 45.1, '30-45'),
              (45.1, 65.1, '50-65'), (65.1, 90.1, '70-90'), (90.1, 1e9, '95+')]


def media(x):
    x = np.asarray(x, float)
    return float(x.mean()) if len(x) else None


def compara(rs, tr, mk, n_sort=4000):
    """Grupo mk contra o resto e contra subconjuntos sorteados do mesmo tamanho."""
    mk = np.asarray(mk, bool); tr = np.asarray(tr, bool)
    a = rs[mk]; b = rs[~mk]
    t = float((a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))) if len(a) > 2 and len(b) > 2 else None
    k = int(mk.sum())
    sim = np.array([rs[RNG.permutation(len(rs))[:k]].mean() for _ in range(n_sort)]) if 0 < k < len(rs) else np.array([np.nan])
    return dict(n=k, frac=k / len(rs), ev=media(a), resto=media(b), ev_is=media(rs[mk & tr]), ev_oos=media(rs[mk & ~tr]),
                resto_is=media(rs[~mk & tr]), resto_oos=media(rs[~mk & ~tr]), n_is=int((mk & tr).sum()), n_oos=int((mk & ~tr).sum()),
                t=t, pct=float((sim < a.mean()).mean() * 100) if k else None)


def faixas_pavio(X, col, keys):
    out = []
    for a, b, rot in FAIXAS_PAV:
        g = X[(X[col] > a) & (X[col] <= b)]
        lin = dict(faixa=rot, n=len(g), n_is=int(g['treino'].sum()), n_oos=int((~g['treino']).sum()))
        for k in keys:
            lin[k] = dict(ev=media(g[k]), wr=float((g[k] > 0).mean() * 100) if len(g) else None,
                          ev_is=media(g.loc[g['treino'], k]), ev_oos=media(g.loc[~g['treino'], k]),
                          compra=media(g.loc[g.lado > 0, k]), venda=media(g.loc[g.lado < 0, k]),
                          t1=media(g.loc[g.tipo == 'T1', k]), t2=media(g.loc[g.tipo == 'T2', k]))
        out.append(lin)
    return out


def main():
    import tendencia as TD
    TD.ROTULO.update(ROT)
    d = E.indicadores(E.carrega())
    dias = sorted(d['dia'].unique())
    corte = dias[int(len(dias) * 0.6)]
    OUT = dict(meta=dict(corte=str(corte)[:10], inicio=str(dias[0])[:10], fim=str(dias[-1])[:10], pregoes=len(dias)))

    # ===================================================== parte 1: impulso
    S = E.sinais(d)
    S['treino'] = S['data'] < corte
    X = impulso(d, S)
    X['er_100'] = eficiencia(d, X)
    for gk, G in GESTOES.items():
        t = E.executa(d, X, 'fecha', G)
        X[f'rs_{gk}'] = E.reais(t); X[f'pts_{gk}'] = t['pts'].to_numpy()
    OUT['meta'].update(sinais=len(X), kc10_toca=float((X['kc_10'] >= 1).mean()), bb20_toca=float((X['bb_20'] >= 1).mean()),
                       imp20_med=float(X['imp_20'].median()), recuo20_med=float(X['recuo_20'].median()))
    log('impulso: sinais', len(X))

    cols = [c for _, _, cs in FAMILIAS for c in cs]
    cortes = {c: TD.cortes_treino(X.loc[X['treino'], c]) for c in cols}
    fam = []
    for nome, desc, cs in FAMILIAS:
        bl = []
        for c in cs:
            tabs = {}; geral = {}
            for gk in GESTOES:
                Xg = X.assign(rs=X[f'rs_{gk}'], pts=X[f'pts_{gk}'])
                tabs[gk] = TD.tabela(Xg, c, cortes[c])
                geral[gk] = dict(ev=float(Xg['rs'].mean()), ev_is=float(Xg.loc[Xg.treino, 'rs'].mean()),
                                 ev_oos=float(Xg.loc[~Xg.treino, 'rs'].mean()))
            bl.append(dict(col=c, rotulo=ROT[c], tabs=tabs, geral=geral))
        fam.append(dict(familia=nome, desc=desc, blocos=bl))
    OUT['imp_familias'] = fam

    q_imp = {W: float(np.nanquantile(X.loc[X.treino, f'imp_{W}'], 2 / 3)) for W in JAN}
    q_imp_b = {W: float(np.nanquantile(X.loc[X.treino, f'imp_{W}'], 1 / 3)) for W in JAN}
    OUT['q_imp'] = dict(alto=q_imp, baixo=q_imp_b)
    HIP = [
        ('Preco tocou a banda de Keltner nos 10 candles antes do recuo', lambda Z: Z['kc_10'] >= 1),
        ('Preco chegou perto da banda de Keltner (>= 80% do caminho) em 10', lambda Z: Z['kc_10'] >= 0.8),
        ('Preco longe da banda (< 60% do caminho) em 10', lambda Z: Z['kc_10'] < 0.6),
        ('Preco tocou a banda de Keltner nos 20 candles antes do recuo', lambda Z: Z['kc_20'] >= 1),
        ('3+ candles alem da banda de Keltner em 10 (esticou e ficou)', lambda Z: Z['kc_toques_10'] >= 3),
        ('MACD tocou a Bollinger 1000 nos 10 candles antes do recuo', lambda Z: Z['bb_10'] >= 1),
        ('MACD tocou a Bollinger 1000 nos 20 candles antes do recuo', lambda Z: Z['bb_20'] >= 1),
        ('MACD longe da banda (< 50%) em 20', lambda Z: Z['bb_20'] < 0.5),
        (f'Impulso amplo em 20: terco superior do treino (>= {q_imp[20]:.0f} pts)', lambda Z: Z['imp_20'] >= q_imp[20]),
        (f'Impulso curto em 20: terco inferior do treino (< {q_imp_b[20]:.0f} pts)', lambda Z: Z['imp_20'] < q_imp_b[20]),
        (f'Impulso amplo em 30 (>= {q_imp[30]:.0f} pts)', lambda Z: Z['imp_30'] >= q_imp[30]),
        ('Impulso amplo em 20 E tocou Keltner E MACD na Bollinger', lambda Z: (Z['imp_20'] >= q_imp[20]) & (Z['kc_20'] >= 1) & (Z['bb_20'] >= 1)),
        ('Recuo comecou no pico (0-1 candle depois do pico de 20)', lambda Z: Z['pico_dist_20'] <= 1),
        ('Recuo profundo: mais de 400 pts desde o pico de 20 (achado na exploracao)', lambda Z: Z['recuo_20'] > 400),
    ]
    hip = []
    for gk in GESTOES:
        for ck, Z in (('todos', X), ('picado', X[X['inversoes'] >= 11])):
            rs_ = Z[f'rs_{gk}'].to_numpy(); tr = Z['treino'].to_numpy()
            for nome, f in HIP:
                mk = np.asarray(f(Z), bool)
                if mk.sum() < 20 or (~mk).sum() < 20:
                    continue
                hip.append(dict(gestao=gk, conj=ck, nome=nome, **compara(rs_, tr, mk, n_sort=1000)))
    OUT['imp_hipoteses'] = hip

    # grade de larguras de banda: EMA 21 +- m x range medio 21 (Keltner Nelogica) e +- m x desvio-padrao 21
    grade = []
    for tipo, col, mults in (('range', 'zatr', (1.5, 2.0, 2.5, 3.0, 3.5)), ('desvio', 'zsd', (1.5, 2.0, 2.5, 3.0))):
        for W in (10, 20):
            for m in mults:
                for gk in GESTOES:
                    mk = (X[f'{col}_{W}'] >= m).to_numpy()
                    rs_ = X[f'rs_{gk}'].to_numpy(); tr = X['treino'].to_numpy()
                    grade.append(dict(tipo=tipo, W=W, m=m, gestao=gk, **compara(rs_, tr, mk, n_sort=1000),
                                      pts_banda=float(m * np.nanmedian(d['rng_med'] if tipo == 'range' else pd.Series(d['c']).rolling(E.EMA_PER).std(ddof=0)))))
    OUT['kc_grade'] = grade
    log('grade keltner')
    log('hipoteses impulso')

    busca = {}
    for gk in GESTOES:
        Xg = X.assign(rs=X[f'rs_{gk}'], pts=X[f'pts_{gk}'])
        cand = TD.candidatos(Xg, cols)
        cand.sort(key=lambda r: r['t_is'], reverse=True)
        rs_ = Xg['rs'].to_numpy(); tr = Xg['treino'].to_numpy()
        plac = []
        for _ in range(2000):
            mk = RNG.random(len(Xg)) < RNG.uniform(0.3, 0.8)
            plac.append(TD.tstat(rs_[mk & tr]))
        bons = [c for c in cand if c['ganho_is'] > 0]
        busca[gk] = dict(lista=cand[:20], n_cand=len(cand), p95=float(np.percentile(plac, 95)), p99=float(np.percentile(plac, 99)),
                         max_t=float(cand[0]['t_is']) if cand else None,
                         frac_bons=float(np.mean([c['ganho_oos'] > 0 for c in bons])) if bons else None,
                         base_is=float(rs_[tr].mean()), base_oos=float(rs_[~tr].mean()))
    OUT['imp_busca'] = busca
    log('busca impulso')

    CART_IMP = [
        ('sem filtro', lambda Z: np.ones(len(Z), bool)),
        ('tocou Keltner em 10', lambda Z: Z['kc_10'] >= 1),
        ('nao tocou Keltner em 10', lambda Z: Z['kc_10'] < 1),
        ('MACD tocou a Bollinger em 20', lambda Z: Z['bb_20'] >= 1),
        ('MACD nao tocou a Bollinger em 20', lambda Z: Z['bb_20'] < 1),
        ('impulso amplo em 20 (terco superior)', lambda Z: Z['imp_20'] >= q_imp[20]),
        ('impulso nao amplo em 20', lambda Z: Z['imp_20'] < q_imp[20]),
        ('evitar recuo > 400 pts (post hoc)', lambda Z: ~(Z['recuo_20'] > 400)),
        ('fora da consolidacao 100 (estudo anterior)', lambda Z: Z['er_100'] >= 0.08),
        ('fora da consolidacao 100 E tocou Keltner em 10', lambda Z: (Z['er_100'] >= 0.08) & (Z['kc_10'] >= 1)),
        ('fora da consolidacao 100 E nao tocou Keltner em 10', lambda Z: (Z['er_100'] >= 0.08) & (Z['kc_10'] < 1)),
    ]
    OUT['imp_carteiras'] = {}
    for gk, G in GESTOES.items():
        lin = []
        for nome, f in CART_IMP:
            mk = np.asarray(f(X), bool)
            lin.append(dict(nome=nome, frac=float(mk.mean()), **TD.stats_cart(d, X[mk], G, corte)))
        OUT['imp_carteiras'][gk] = lin
        log('carteiras impulso', gk, [round(l['stats']['liquido']) for l in lin])
    OUT['imp_corr'] = {c: float(X[[c, 'er_100']].corr(method='spearman').iloc[0, 1]) for c in ('imp_20', 'kc_10', 'bb_20', 'recuo_20')}

    # ====================================================== parte 2: pavios
    U = E.sinais(d, pavio_fech_pct=None)
    U['treino'] = U['data'] < corte
    U['er_100'] = eficiencia(d, U)
    keys = []
    for gk, G in GESTOES.items():
        for modo in ('fecha', 'extremo'):
            t = E.executa(d, U, modo, G)
            U[f'{gk}_{modo}'] = E.reais(t)
            keys.append(f'{gk}_{modo}')
    setup = U['pav_fech'] <= 10
    OUT['pav_meta'] = dict(universo=len(U), setup=int(setup.sum()), fech0=int((U['pav_fech'] == 0).sum()))
    OUT['pav_faixas'] = dict(fech=faixas_pavio(U, 'pav_fech', keys), abre_setup=faixas_pavio(U[setup], 'pav_abre', keys),
                             abre_todos=faixas_pavio(U, 'pav_abre', keys))
    log('faixas pavio')

    Us = U[setup]
    PAD = [
        ('fech', 'Pavio do fechamento ate 10% do corpo (corte do HullRetracao_Azul)', 'melhor que acima de 10%: +7,9 contra +4,4 pts',
         U, lambda Z: Z['pav_fech'] <= 10),
        ('fech0', 'Pavio do fechamento = 0 (fecha na maxima da compra / minima da venda)', 'nao medido separado',
         U, lambda Z: Z['pav_fech'] == 0),
        ('fech0s', 'Pavio do fechamento = 0, dentro do setup (contra 5-10 pts)', 'nao medido', Us, lambda Z: Z['pav_fech'] == 0),
        ('mag', 'Pavio da abertura 25-90% (PavioContra_Magenta)', 'anti-filtro: percentil 2 a 8 do sorteio', Us,
         lambda Z: (Z['pav_abre'] >= 25) & (Z['pav_abre'] <= 90)),
        ('verde', 'Pavio da abertura 5-25% (PavioFavor_Verde)', 'com Hull a favor nao separa (percentil 58)', Us,
         lambda Z: (Z['pav_abre'] >= 5) & (Z['pav_abre'] <= 25)),
        ('peq', 'Pavio da abertura ate 25% (quanto menor, melhor)', 'pequenos melhores: 0-10% de +6,5 a +8,6 pts; 65-90% -2,3', Us,
         lambda Z: Z['pav_abre'] <= 25),
        ('mart', 'Pavio da abertura acima de 90% (martelo)', 'faixa 90-100% boa: +5,8 pts', Us, lambda Z: Z['pav_abre'] > 90),
    ]
    pad = []
    for k, nome, antes, Z, f in PAD:
        mk = np.asarray(f(Z), bool)
        tr = Z['treino'].to_numpy()
        lin = dict(k=k, nome=nome, antes=antes, univ='sem corte de pavio' if Z is U else 'setup (fechamento ate 10%)')
        for gk in ('claude_fecha', 'r400_fecha', 'claude_extremo'):
            lin[gk] = compara(Z[gk].to_numpy(), tr, mk)
        pad.append(lin)
    OUT['pav_padroes'] = pad
    from scipy.stats import spearmanr
    ab = Us[Us['pav_abre'] <= 90]
    OUT['pav_spearman'] = {}
    for k in keys:
        r_, p_ = spearmanr(ab['pav_abre'], ab[k])
        OUT['pav_spearman'][k] = dict(rho=float(r_), p=float(p_))
    log('padroes pavio')

    U['fb'] = np.select([U['pav_fech'] == 0, U['pav_fech'] <= 10], ['0', '5-10'], '>10')
    U['mes'] = U['data'].dt.strftime('%m/%Y')
    OUT['pav_mensal'] = {gk: {m: {fb: dict(ev=media(z[f'{gk}_fecha']), n=len(z)) for fb, z in g.groupby('fb')}
                              for m, g in U.groupby('mes')} for gk in GESTOES}
    lt = {}
    for gk in GESTOES:
        dd_ = {}
        for rot, chave in (('lado', U['lado'].map({1: 'Compra', -1: 'Venda'})), ('tipo', U['tipo']),
                           ('barras', U['n_contra'].map(lambda v: f'{v} contra'))):
            for (a, b), z in U.groupby([chave, 'fb']):
                dd_[f'{a}|{b}'] = dict(ev=media(z[f'{gk}_fecha']), n=len(z))
        lt[gk] = dd_
    OUT['pav_lado_tipo'] = lt

    CART_PAV = [
        ('sem corte de pavio (universo)', lambda Z: np.ones(len(Z), bool)),
        ('setup atual: pavio do fechamento ate 10%', lambda Z: Z['pav_fech'] <= 10),
        ('pavio do fechamento = 0', lambda Z: Z['pav_fech'] == 0),
        ('pavio do fechamento 5-10', lambda Z: (Z['pav_fech'] > 0) & (Z['pav_fech'] <= 10)),
        ('pavio do fechamento acima de 10', lambda Z: Z['pav_fech'] > 10),
        ('setup sem a faixa magenta (abertura fora de 25-90%)', lambda Z: (Z['pav_fech'] <= 10) & ~((Z['pav_abre'] >= 25) & (Z['pav_abre'] <= 90))),
        ('pavio do fechamento = 0 E picado', lambda Z: (Z['pav_fech'] == 0) & (Z['inversoes'] >= 11)),
        ('pavio do fechamento = 0 E fora da consolidacao 100', lambda Z: (Z['pav_fech'] == 0) & (Z['er_100'] >= 0.08)),
        ('setup E fora da consolidacao 100', lambda Z: (Z['pav_fech'] <= 10) & (Z['er_100'] >= 0.08)),
    ]
    OUT['pav_carteiras'] = {}
    for gk, G in GESTOES.items():
        lin = []
        for nome, f in CART_PAV:
            mk = np.asarray(f(U), bool)
            sc = TD.stats_cart(d, U[mk], G, corte)
            n_ = sc['stats']['trades']
            sc['slip5'] = sc['stats']['liquido'] - 5 * E.VAL_PONTO * E.CONTRATOS * n_
            sc['slip10'] = sc['stats']['liquido'] - 10 * E.VAL_PONTO * E.CONTRATOS * n_
            lin.append(dict(nome=nome, frac=float(mk.mean()), **sc))
        OUT['pav_carteiras'][gk] = lin
        log('carteiras pavio', gk, [round(l['stats']['liquido']) for l in lin])

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

    with open(os.path.join(SAIDA, 'impulso.json'), 'w', encoding='utf-8') as f:
        json.dump(limpa(OUT), f, ensure_ascii=False)
    log('ok')


if __name__ == '__main__':
    main()
