# -*- coding: utf-8 -*-
"""
Estudo completo da estrategia EMA21 (CLAUDE.md) -> saida/estudo.json

1. Base: os tres sistemas de entrada x T1/T2, carteira com 6 contratos.
2. Filtros: cada filtro do CLAUDE.md medido sinal a sinal (valor esperado
   isolado), dentro e fora da amostra.
3. Selecao de filtros SO na amostra de treino; conferencia fora dela.
4. Gestao: grade de stop / alvo / parcial por sistema de entrada.
5. Robustez: fora da amostra, mes a mes, Monte Carlo, entradas aleatorias,
   vizinhanca de parametros, custos/escorregamento, sem os melhores trades.
"""
import json
import os
import time
import itertools
import numpy as np
import pandas as pd

import engine as E

SAIDA = os.path.join(E.BASE, 'saida')
os.makedirs(SAIDA, exist_ok=True)
RNG = np.random.default_rng(20260916)
MODOS = ['fecha', 'meio', 'extremo']
NOME_MODO = {'fecha': 'Seca no fechamento', 'meio': 'Limitada no meio do corpo',
             'extremo': 'Stop no extremo do candle'}
T0 = time.time()


def log(*a):
    print(f'[{time.time() - T0:6.1f}s]', *a, flush=True)


def r2(x, n=2):
    if isinstance(x, (float, np.floating)):
        if np.isnan(x) or np.isinf(x):
            return None
        return round(float(x), n)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    return x


def limpa(o):
    if isinstance(o, dict):
        return {str(k): limpa(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [limpa(v) for v in o]
    if isinstance(o, np.ndarray):
        return [limpa(v) for v in o.tolist()]
    return r2(o)


def ev(t):
    """valor esperado liquido por trade, em R$ (6 contratos, com custo)."""
    return float(E.reais(t).mean()) if len(t) else float('nan')


def resumo(t):
    if len(t) == 0:
        return dict(n=0)
    rs = E.reais(t)
    return dict(n=len(t), ev_pts=float(t['pts'].mean()), ev_rs=float(rs.mean()),
                wr=float((t['pts'] > 0).mean() * 100), total=float(rs.sum()),
                t=float(rs.mean() / rs.std(ddof=1) * np.sqrt(len(t))) if len(t) > 2 and rs.std(ddof=1) > 0 else 0.0)


def curva(c):
    rs = E.reais(c)
    return dict(eq=np.round(np.cumsum(rs), 1).tolist(),
                dt=c['data'].dt.strftime('%d/%m').tolist())


# ============================================================ dados
d = E.indicadores(E.carrega())
dias = sorted(d['dia'].unique())
corte = dias[int(len(dias) * 0.6)]               # 60% treino / 40% teste
log('candles', len(d), 'pregoes', len(dias), 'corte', str(corte)[:10])

S = E.sinais(d)
S['treino'] = S['data'] < corte
log('sinais', len(S))

OUT = dict(meta=dict(candles=len(d), pregoes=len(dias),
                     inicio=str(dias[0])[:10], fim=str(dias[-1])[:10],
                     corte=str(corte)[:10], sinais=len(S),
                     contratos=E.CONTRATOS, custo=E.CUSTO_CONTRATO,
                     val_ponto=E.VAL_PONTO))

# ============================================================ 1. base
base = {}
TR = {}
for m in MODOS:
    t = E.executa(d, S, m)
    TR[m] = t
    a = t[t['aceito']]
    blocos = {}
    for nome, sel in [('todos', a), ('T1', a[a.tipo == 'T1']), ('T2', a[a.tipo == 'T2'])]:
        c = E.carteira(sel)
        blocos[nome] = dict(isolado=resumo(sel), stats=E.estatisticas(c), curva=curva(c))
    base[m] = dict(nome=NOME_MODO[m], aceitos=int(len(a)), sinais=int(len(t)),
                   blocos=blocos,
                   lado={'compra': resumo(a[a.lado > 0]), 'venda': resumo(a[a.lado < 0])})
    log('base', m, blocos['todos']['stats']['liquido'])
OUT['base'] = base

# ============================================================ 2. filtros
def faixas(col, cortes, rot):
    def f(t):
        x = pd.cut(t[col], cortes, labels=rot, right=False).astype(object)
        return x.where(x.notna(), 'n/d').astype(str)
    f.ordem = list(rot) + ['n/d']
    return f


def qfaixas(col, q=5):
    """quintis definidos NA AMOSTRA DE TREINO."""
    x = S.loc[S['treino'], col].dropna()
    cs = np.unique(np.quantile(x, np.linspace(0, 1, q + 1)))
    cs[0] = -np.inf; cs[-1] = np.inf
    rot = []
    for a_, b_ in zip(cs[:-1], cs[1:]):
        fa = '-inf' if np.isinf(a_) else f'{a_:.2f}'.rstrip('0').rstrip('.')
        fb = '+inf' if np.isinf(b_) else f'{b_:.2f}'.rstrip('0').rstrip('.')
        rot.append(f'{fa} a {fb}')
    return faixas(col, cs, rot)


def hora_faixa(t):
    h = np.floor(t['hora']).astype(int)
    return h.map(lambda x: f'{x:02d}h' if x < 17 else '17h+')


def abertura_acoes(t):
    return np.where((t['hora'] >= 10.0) & (t['hora'] < 10 + 10 / 60), '10:00-10:10',
                    np.where((t['hora'] >= 9.75) & (t['hora'] < 10.0), '09:45-10:00',
                             np.where((t['hora'] >= 10 + 10 / 60) & (t['hora'] < 10.5), '10:10-10:30', 'resto')))


hora_faixa.ordem = [f'{h:02d}h' for h in range(9, 17)] + ['17h+']
abertura_acoes.ordem = ['09:45-10:00', '10:00-10:10', '10:10-10:30', 'resto']


def dow(t):
    m_ = t['min_dow']
    return np.select([m_ < -30, m_ < -5, m_ < 15, m_ < 60],
                     ['> 30 min antes', '30-5 min antes', '5 antes a 15 depois', '15-60 min depois'],
                     'mais de 1h depois')


dow.ordem = ['> 30 min antes', '30-5 min antes', '5 antes a 15 depois', '15-60 min depois', 'mais de 1h depois']


FILTROS = [
    # (chave, grupo, descricao, funcao de faixa)
    ('tipo', 'Classificacao', 'T1 x T2', lambda t: t['tipo']),
    ('lado', 'Classificacao', 'Compra x venda', lambda t: np.where(t['lado'] > 0, 'compra', 'venda')),
    ('n_contra', 'Classificacao', 'Candles contra no recuo', lambda t: t['n_contra'].astype(str)),
    ('tend_dia', 'Tendencia geral', 'Preco x abertura do dia (a favor do trade)',
     lambda t: np.where(t['tend_dia'] > 0, 'a favor', 'contra')),
    ('tend_ema200', 'Tendencia geral', 'Preco x EMA 200 (a favor do trade)',
     lambda t: np.where(t['tend_ema200'] > 0, 'a favor', 'contra')),
    ('incl_ema', 'Tendencia geral', 'Inclinacao da EMA 21 (5 candles, pts, a favor)', qfaixas('incl_ema')),
    ('macd_fora_bb', 'Tendencia geral', 'MACD alem da Bollinger 1000 no sentido do trade',
     lambda t: np.where(t['macd_fora_bb'], 'fora da banda', 'dentro')),
    ('macd_acima_sig', 'Tendencia geral', 'MACD acima do sinal (a favor)',
     lambda t: np.where(t['macd_acima_sig'], 'sim', 'nao')),
    ('n_rec', 'Segundos recuos', 'Toques anteriores na EMA desde que o MACD virou',
     lambda t: np.where(t['n_rec'] >= 3, '3+', t['n_rec'].astype(str))),
    ('novo_ext', 'Fraqueza de continuacao', 'Impulso anterior fez novo extremo?',
     lambda t: np.where(t['novo_ext'], 'fez novo extremo', 'nao fez (fraco)')),
    ('impulso', 'Fraqueza de continuacao', 'Tamanho do impulso antes do recuo (pts)', qfaixas('impulso')),
    ('mesmo_nivel', 'Segundas entradas', 'Trigger anterior no mesmo nivel (<=100 pts, 60 candles)',
     lambda t: np.where(t['mesmo_nivel'], 'segunda no nivel', 'primeira')),
    ('n_trig_dia', 'Segundas entradas', 'Ordem do trigger no dia (mesmo lado)',
     lambda t: np.where(t['n_trig_dia'] >= 4, '5a+', (t['n_trig_dia'] + 1).astype(str) + 'a')),
    ('hora', 'Horario', 'Hora do trigger', hora_faixa),
    ('abertura', 'Horario', 'Abertura das acoes (10:00)', abertura_acoes),
    ('dow', 'Horario', 'Abertura do Dow Jones (10:30 no horario de verao dos EUA)', dow),
    ('inversoes', 'Movimento picado', 'Inversoes nos 20 candles antes do recuo', qfaixas('inversoes', 4)),
    ('vol_rel', 'Volume (agressao)', 'Volume do trigger / mediana 200', qfaixas('vol_rel')),
    ('vol_rec_rel', 'Volume (agressao)', 'Volume medio do recuo / mediana 200', qfaixas('vol_rec_rel')),
    ('saldo_fav_rel', 'Volume (agressao)', 'Saldo agressor do trigger a favor (% do volume)', qfaixas('saldo_fav_rel')),
    ('saldo_rec_fav', 'Volume (agressao)', 'Saldo agressor do recuo a favor do trade', qfaixas('saldo_rec_fav')),
    ('dur_rel', 'Tempo das barras', 'Tempo do trigger / mediana 200', qfaixas('dur_rel')),
    ('dur_rec_rel', 'Tempo das barras', 'Tempo medio do recuo / mediana 200', qfaixas('dur_rec_rel')),
    ('pav_abre', 'Geometria', 'Pavio da abertura do trigger (pts)', qfaixas('pav_abre')),
    ('hull_dist', 'Geometria', 'Hull alem do candle (pts; >0 = T2)', qfaixas('hull_dist')),
    ('toque_ema', 'Geometria', 'Toque na EMA', lambda t: np.where(t['toque_ema'] > 0, 'quase toque (1-15)', 'toca')),
    ('macd_norm', 'Tendencia geral', 'Forca do MACD (/ATR)', qfaixas('macd_norm')),
    ('idx_dia', 'Horario', 'Candles desde a abertura do pregao',
     lambda t: np.select([t['idx_dia'] < 40, t['idx_dia'] < 100], ['< 40', '40-100'], '100+')),
]


def tabela_filtro(t, fx):
    t = t.copy()
    t['faixa'] = fx(t)
    rs = E.reais(t)
    t['rs'] = rs
    linhas = []
    geral = t['rs'].mean()
    for fa, g in t.groupby('faixa', sort=True):
        gi = g[g['treino']]; go = g[~g['treino']]
        linhas.append(dict(faixa=fa, n=len(g), ev=g['rs'].mean(), wr=(g['pts'] > 0).mean() * 100,
                           total=g['rs'].sum(),
                           n_is=len(gi), ev_is=gi['rs'].mean() if len(gi) else np.nan,
                           n_oos=len(go), ev_oos=go['rs'].mean() if len(go) else np.nan,
                           compra=g.loc[g.lado > 0, 'rs'].mean(), venda=g.loc[g.lado < 0, 'rs'].mean()))
    ordem = getattr(fx, 'ordem', None)
    if ordem:
        linhas.sort(key=lambda r: ordem.index(r['faixa']) if r['faixa'] in ordem else 99)
    return dict(linhas=linhas, geral=geral)


filtros_out = {}
for m in MODOS:
    a = TR[m][TR[m]['aceito']].copy()
    filtros_out[m] = []
    for chave, grupo, desc, fx in FILTROS:
        filtros_out[m].append(dict(chave=chave, grupo=grupo, desc=desc, **tabela_filtro(a, fx)))
log('filtros medidos')
OUT['filtros'] = filtros_out

# ============================================================ 3. selecao (so treino)
def candidatos_mascaras(t):
    """Mascaras binarias 'manter' candidatas, a partir das faixas."""
    out = {}
    for chave, grupo, desc, fx in FILTROS:
        if chave in ('lado',):
            continue
        fa = pd.Series(fx(t), index=t.index).astype(str)
        for v in sorted(fa.unique()):
            out[f'{chave} = {v}'] = (fa == v).to_numpy()
            out[f'{chave} != {v}'] = (fa != v).to_numpy()
    return out


def selecao(m, max_f=3, min_frac=0.25):
    a = TR[m][TR[m]['aceito']].reset_index(drop=True)
    rs = E.reais(a)
    is_ = a['treino'].to_numpy()
    masks = candidatos_mascaras(a)
    atual = np.ones(len(a), bool)
    escolhidos = []
    passos = []
    n_is = is_.sum()

    def score(mk):
        x = rs[mk & is_]
        if len(x) < min_frac * n_is or len(x) < 30:
            return -np.inf
        return x.mean() / x.std(ddof=1) * np.sqrt(len(x))     # t do lucro total

    s0 = score(atual)
    passos.append(dict(filtro='(sem filtro)', t_is=s0, n_is=int((atual & is_).sum()),
                       ev_is=rs[atual & is_].mean(), n_oos=int((atual & ~is_).sum()),
                       ev_oos=rs[atual & ~is_].mean()))
    for _ in range(max_f):
        melhor = None
        for nome, mk in masks.items():
            if any(nome.split(' ')[0] == e.split(' ')[0] for e in escolhidos):
                continue
            s = score(atual & mk)
            if melhor is None or s > melhor[1]:
                melhor = (nome, s, mk)
        if melhor is None or melhor[1] <= s0 * 1.05:
            break
        escolhidos.append(melhor[0])
        atual = atual & melhor[2]
        s0 = melhor[1]
        passos.append(dict(filtro=melhor[0], t_is=s0, n_is=int((atual & is_).sum()),
                           ev_is=rs[atual & is_].mean(), n_oos=int((atual & ~is_).sum()),
                           ev_oos=rs[atual & ~is_].mean()))
    return escolhidos, atual, passos


selec = {}
MASC = {}
for m in MODOS:
    esc, mk, passos = selecao(m)
    selec[m] = dict(filtros=esc, passos=passos)
    MASC[m] = mk
    log('selecao', m, esc, [round(p['ev_oos'], 1) for p in passos])
OUT['selecao'] = selec

# ============================================================ 4. gestao
STOPS = [50, 75, 100, 150, 200]
ALVOS = [100, 150, 200, 300, 400, 500]
PARCS = [None, (0.5, 50), (0.5, 100), (0.5, 150), (0.5, 200)]
APOS = ['media', 'entrada']


def grade_gestao(m, sig):
    linhas = []
    stops = STOPS if m != 'extremo' else [None]
    for st, al, pc, ap in itertools.product(stops, ALVOS, PARCS, APOS):
        if pc is None and ap == 'entrada':
            continue
        if pc is not None and pc[1] >= al:
            continue
        G = dict(alvo=float(al), parcial=pc is not None,
                 parcial_em=float(pc[1]) if pc else 100.0,
                 frac=pc[0] if pc else 0.5, apos=ap)
        if st is not None:
            G['stop'] = float(st)
        t = E.executa(d, sig, m, G)
        a = t[t['aceito']]
        rs = E.reais(a)
        is_ = a['treino'].to_numpy()
        c = E.carteira(t)
        stc = E.estatisticas(c)
        linhas.append(dict(stop=st, alvo=al, parcial=(f'{int(pc[0]*100)}% em +{pc[1]}' if pc else 'sem'),
                           apos=ap if pc else '-', ev=rs.mean(), ev_is=rs[is_].mean(), ev_oos=rs[~is_].mean(),
                           wr=(a['pts'] > 0).mean() * 100, n=len(a),
                           cart_liq=stc['liquido'], cart_dd=stc['dd_max'], cart_fl=stc['fator_lucro'],
                           cart_n=stc['trades']))
    return linhas


gestao = {}
for m in MODOS:
    sig_f = S[MASC[m]] if False else None
    # grade sobre TODOS os sinais (a gestao nao pode ser escolhida sobre o
    # subconjunto que a propria gestao ajudou a selecionar) e sobre os filtrados
    a_ids = TR[m][TR[m]['aceito']]['i']
    sel_i = set(TR[m][TR[m]['aceito']].reset_index(drop=True)[MASC[m]]['i'].tolist()) if MASC[m].any() else set()
    Sf = S[S['i'].isin(sel_i)]
    gestao[m] = dict(todos=grade_gestao(m, S), filtrados=grade_gestao(m, Sf))
    log('gestao', m)
OUT['gestao'] = gestao

# ============================================================ 5. candidatos finais
def melhor_gestao(m, qual='todos'):
    g = pd.DataFrame(gestao[m][qual])
    g = g[g['n'] >= 100]
    # escolhida pelo treino
    return g.sort_values('ev_is', ascending=False).iloc[0].to_dict()


def G_de(linha):
    G = dict(alvo=float(linha['alvo']))
    if linha['stop'] is not None and not (isinstance(linha['stop'], float) and np.isnan(linha['stop'])):
        G['stop'] = float(linha['stop'])
    if linha['parcial'] == 'sem':
        G['parcial'] = False
    else:
        pct, em = linha['parcial'].split('% em +')
        G.update(parcial=True, frac=int(pct) / 100, parcial_em=float(em), apos=linha['apos'])
    return G


VARIANTES = {}
for m in MODOS:
    a = TR[m][TR[m]['aceito']].reset_index(drop=True)
    sel_i = set(a[MASC[m]]['i'])
    Sf = S[S['i'].isin(sel_i)]
    lg = melhor_gestao(m, 'filtrados')
    G = G_de(lg)
    VARIANTES[f'{m}|base'] = dict(modo=m, nome=f'{NOME_MODO[m]} - regra pura', sig=S, G={}, filtros=[])
    lg0 = melhor_gestao(m, 'todos')
    VARIANTES[f'{m}|gestao'] = dict(modo=m, nome=f'{NOME_MODO[m]} - gestao do treino', sig=S, G=G_de(lg0),
                                    filtros=[], gestao=lg0)
    VARIANTES[f'{m}|filtrado'] = dict(modo=m, nome=f'{NOME_MODO[m]} - filtros do treino', sig=Sf, G={},
                                      filtros=selec[m]['filtros'])
    VARIANTES[f'{m}|otimizado'] = dict(modo=m, nome=f'{NOME_MODO[m]} - filtros + gestao do treino', sig=Sf, G=G,
                                       filtros=selec[m]['filtros'], gestao=lg)

# so o 1o passo da selecao do modo 'fecha' (o 2o, horario do Dow, inverteu
# fora da amostra): regra mais simples, mostrada para comparacao
Sp = S[S['inversoes'] >= 11]
VARIANTES['fecha|picado'] = dict(modo='fecha', nome='Seca no fechamento - so filtro picado', sig=Sp, G={},
                                 filtros=['inversoes >= 11'])
VARIANTES['fecha|picado400'] = dict(modo='fecha', nome='Seca no fechamento - so filtro picado, stop 100 / alvo 400',
                                    sig=Sp, G=dict(stop=100.0, alvo=400.0, parcial=False),
                                    filtros=['inversoes >= 11'])

# ============================================================ 6. robustez
# pool de entradas aleatorias: todo candle, os dois lados, gestao padrao
def pool_aleatorio(m, G):
    idx = np.arange(E.HMA_PER + 10, len(d) - 1)
    amostra = RNG.choice(idx, size=min(12000, len(idx)), replace=False)
    # lado = sentido do proprio candle, como nos sinais (o trigger sempre fecha
    # a favor do trade); sem isso a limitada no meio do corpo ficaria do lado
    # errado do preco e executaria 'no passado'
    sent = np.sign(d['c'].to_numpy() - d['o'].to_numpy()).astype(int)
    ps = pd.DataFrame(dict(i=amostra, lado=sent[amostra]))
    ps['data'] = d['data'].to_numpy()[ps['i']]
    ps['tipo'] = 'X'
    t = E.executa(d, ps, m, G)
    return t[t['aceito']]


def monte_carlo(rs, n_sim=5000):
    n = len(rs)
    fins = np.empty(n_sim); dds = np.empty(n_sim)
    for k in range(n_sim):
        x = RNG.choice(rs, size=n, replace=True)
        eq = np.cumsum(x)
        pico = np.maximum.accumulate(np.r_[0, eq])
        fins[k] = eq[-1]; dds[k] = (pico - np.r_[0, eq]).max()
    q = lambda v: {p: float(np.percentile(v, p)) for p in (5, 25, 50, 75, 95)}
    return dict(final=q(fins), dd=q(dds), p_prejuizo=float((fins < 0).mean() * 100),
                hist_final=np.histogram(fins, 40)[0].tolist(),
                bins_final=np.histogram(fins, 40)[1].tolist(),
                hist_dd=np.histogram(dds, 40)[0].tolist(),
                bins_dd=np.histogram(dds, 40)[1].tolist())


rob = {}
trades_rel = {}
pools = {}
for chave, V in VARIANTES.items():
    m = V['modo']
    t = E.executa(d, V['sig'], m, V['G'])
    c = E.carteira(t)
    c['rs'] = E.reais(c)
    st = E.estatisticas(c)
    is_ = c['data'] < corte
    mes = c.groupby(c['data'].dt.strftime('%Y-%m'))['rs'].agg(['count', 'sum', 'mean']).reset_index()
    rs = c['rs'].to_numpy()
    # custos / escorregamento: pts a menos por contrato, por trade
    estresse = []
    for slip in (0, 5, 10, 20):
        x = rs - slip * E.VAL_PONTO * E.CONTRATOS
        estresse.append(dict(slip=slip, liquido=float(x.sum()), ev=float(x.mean())))
    # ordens limitadas (parcial, alvo, entrada no meio) so executam se o
    # preco passar 5 pts alem do nivel
    Ga = dict(V['G']); Ga['atravessa'] = 5.0
    ca = E.carteira(E.executa(d, V['sig'], m, Ga))
    sta = E.estatisticas(ca)
    atravessa = dict(liquido=sta.get('liquido', 0.0), trades=sta.get('trades', 0),
                     fator=sta.get('fator_lucro'), dd=sta.get('dd_max'),
                     oos=E.estatisticas(ca[ca['data'] >= corte]).get('liquido', 0.0))
    # contramedida: parcial e alvo 1 tick ANTES do nivel, ainda exigindo
    # atravessar 5 pts (= executa quando o preco toca o nivel original)
    Gt = dict(E.GESTAO_PADRAO); Gt.update(V['G'])
    Gt.update(atravessa=5.0, parcial_em=Gt['parcial_em'] - 5, alvo=Gt['alvo'] - 5)
    ct = E.carteira(E.executa(d, V['sig'], m, Gt))
    stt = E.estatisticas(ct)
    atravessa.update(tick_liq=stt.get('liquido', 0.0), tick_fator=stt.get('fator_lucro'),
                     tick_dd=stt.get('dd_max'), tick_oos=E.estatisticas(ct[ct['data'] >= corte]).get('liquido', 0.0))
    # sem os melhores
    ordem = np.sort(rs)[::-1]
    sem_top = [dict(pct=p, liquido=float(ordem[int(len(ordem) * p / 100):].sum())) for p in (0, 1, 5, 10)]
    # aleatorio
    gk = json.dumps(V['G'], sort_keys=True) + m
    if gk not in pools:
        pools[gk] = pool_aleatorio(m, V['G'])
    pool = pools[gk]
    prs = E.reais(pool)
    ev_real = rs.mean()
    sims = np.array([prs[RNG.integers(0, len(prs), len(rs))].mean() for _ in range(3000)])
    percentil = float((sims < ev_real).mean() * 100)
    rob[chave] = dict(
        nome=V['nome'], modo=m, filtros=V['filtros'], G=V['G'], gestao=V.get('gestao'),
        stats=st, stats_is=E.estatisticas(c[is_]), stats_oos=E.estatisticas(c[~is_]),
        curva=curva(c), meses=mes.to_dict('records'),
        mc=monte_carlo(rs), estresse=estresse, sem_top=sem_top, atravessa=atravessa,
        aleatorio=dict(ev_real=float(ev_real), ev_aleat=float(prs.mean()),
                       p5=float(np.percentile(sims, 5)), p95=float(np.percentile(sims, 95)),
                       percentil=percentil),
        mfe=c['mfe'].tolist(), mae=c['mae'].tolist(), rs=np.round(rs, 1).tolist(),
        dur=c['dur_s'].tolist(),
        hora=c.groupby(np.floor(c['hora']).astype(int))['rs'].agg(['count', 'sum']).reset_index().to_dict('records'),
    )
    trades_rel[chave] = c[['i', 'v0', 'i_ent', 'i_sai', 'lado', 'tipo', 'n_contra', 'preco_ent', 'preco_sai',
                           'stop_pts', 'pts', 'rs', 'motivo', 'mfe', 'mae', 'parcial']].assign(
        data=c['data'].dt.strftime('%d/%m %H:%M')).to_dict('records')
    log('robustez', chave, round(st['liquido']), 'OOS', round(rob[chave]['stats_oos'].get('liquido', 0)),
        'pct aleat', round(percentil))
OUT['robustez'] = rob

# vizinhanca de parametros da regra (modo fecha, gestao padrao)
viz = []
for bmin, bmax, pav, tol, em_, mc_ in [
    (2, 3, 10, 15, True, True), (2, 3, 10, 0, True, True), (2, 3, 10, 30, True, True),
    (2, 3, 10, 60, True, True), (2, 3, 10, 15, False, True), (2, 3, 10, 15, True, False),
    (2, 3, 10, 15, False, False), (2, 4, None, 15, True, True), (2, 4, 10, 15, True, True),
    (2, 3, None, 15, True, True), (2, 3, 20, 15, True, True), (1, 3, 10, 15, True, True),
    (3, 3, 10, 15, True, True), (2, 2, 10, 15, True, True)]:
    s_ = E.sinais(d, bmin, bmax, pav, tol, em_, mc_)
    s_['treino'] = s_['data'] < corte
    t = E.executa(d, s_, 'fecha')
    a = t[t['aceito']]
    rs = E.reais(a)
    c = E.carteira(t)
    st = E.estatisticas(c)
    viz.append(dict(barras=f'{bmin}-{bmax}', pavio='sem corte' if pav is None else f'<= {pav}%',
                    tol_ema=tol if em_ else 'sem EMA', macd='sim' if mc_ else 'nao',
                    n=len(a), ev=rs.mean(), ev_is=rs[a['treino'].to_numpy()].mean(),
                    ev_oos=rs[~a['treino'].to_numpy()].mean(),
                    cart_liq=st['liquido'], cart_dd=st['dd_max'], cart_fl=st['fator_lucro']))
    log('viz', viz[-1]['barras'], viz[-1]['pavio'], viz[-1]['tol_ema'], viz[-1]['macd'], round(rs.mean(), 2))
OUT['vizinhanca'] = viz

with open(os.path.join(SAIDA, 'estudo.json'), 'w', encoding='utf-8') as f:
    json.dump(limpa(OUT), f, ensure_ascii=False)
with open(os.path.join(SAIDA, 'trades.json'), 'w', encoding='utf-8') as f:
    json.dump(limpa(trades_rel), f, ensure_ascii=False)
log('ok')
