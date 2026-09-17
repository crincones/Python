# -*- coding: utf-8 -*-
"""
OSCILACAO EM TORNO DA EMA 21 -> oscila.html / OSCILA.md

Pergunta (do usuario): numa janela de 5, 10 e 20 candles antes do sinal,
quantos fecharam ACIMA e quantos ABAIXO da EMA 21, e qual a somatoria das
distancias fechamento - EMA (positiva acima, negativa abaixo). A hipotese e
que preco OSCILANDO em torno da media (metade de cada lado, somatoria perto
de zero) e ruim para o setup, e que ficar mais de um lado do que do outro e
melhor.

Medidas por janela W e por ancora (tudo orientado pelo LADO do trade:
positivo = lado favoravel; na compra e acima da EMA, na venda abaixo):

  nfav    fechamentos do lado favoravel MENOS do lado contrario (-W a +W)
  lado    max(acima, abaixo) / W  -> 0,5 = metade de cada lado; 1 = tudo de um lado
  soma    soma (fechamento - EMA21) / W, em pontos, orientada
  soman   a mesma soma dividida pelo range medio 21 (comparavel entre regimes)
  abs     soma |fechamento - EMA21| / W: o quanto o preco andou longe da media
  pureza  |soma(dif)| / soma(|dif|)  -> 1 = todos do mesmo lado; 0 = equilibrio
  cruz    quantas vezes o fechamento trocou de lado da EMA dentro da janela
  toca    fracao de candles cujo range contem a EMA 21 (minima <= EMA <= maxima)

Duas ancoras:
  p  janela terminando no candle ANTERIOR ao recuo (j = v0 - 1), sem os
     candles contra do proprio setup -- e a leitura principal, igual ao
     resto do projeto (tendencia.py, impulso.py)
  g  janela terminando no candle do TRIGGER (inclui o recuo, que por
     construcao encosta na EMA)

Janelas presas ao pregao: nao atravessam o fechamento (o gap distorceria a
distancia ate a media).

Duas gestoes: 'claude' (stop 100, parcial +100, alvo 300) e 'r400'
(stop 100, alvo 400, sem parcial). Treino = primeiros 60% dos pregoes.
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
RNG = np.random.default_rng(23)
GESTOES = {'claude': {}, 'r400': dict(stop=100.0, alvo=400.0, parcial=False)}
JAN = [5, 10, 20]
ANC = [('p', 'antes do recuo'), ('g', 'ate o trigger')]
MET = ['nfav', 'lado', 'soma', 'soman', 'abs', 'pureza', 'cruz', 'toca']


def log(*a):
    print(f'[{time.time() - T0:5.1f}s]', *a, flush=True)


# ================================================================ atributos
def oscilacao(d, S, jan=JAN):
    """Acrescenta as colunas {met}_{W}{ancora} a tabela de sinais."""
    c = d['c'].to_numpy(); h = d['h'].to_numpy(); l = d['l'].to_numpy()
    em = d['ema'].to_numpy(); rg = d['rng_med'].to_numpy()
    dif = c - em                                   # + = fechou acima da EMA
    dentro = (l <= em) & (em <= h)                 # candle cortado pela EMA
    idx_dia = d.groupby('dia').cumcount().to_numpy()
    X = S.copy()
    cols = {}
    for r in X.itertuples(index=False):
        lado = r.lado
        for anc, j in (('p', r.v0 - 1), ('g', r.i)):
            for W in jan:
                a = max(j - W + 1, j - idx_dia[j])     # nao atravessa o pregao
                x = dif[a:j + 1] * lado
                m = len(x)
                if m < 3:
                    vals = dict.fromkeys(MET, np.nan)
                    vals['n'] = m
                else:
                    sx = float(x.sum()); sa = float(np.abs(x).sum())
                    sg = np.sign(x); sg = sg[sg != 0]
                    vals = dict(
                        n=m,
                        nfav=int((x > 0).sum() - (x < 0).sum()),
                        lado=max((x > 0).sum(), (x < 0).sum()) / m,
                        soma=sx / m,
                        soman=sx / m / rg[j] if rg[j] > 0 else np.nan,
                        abs=sa / m,
                        pureza=abs(sx) / sa if sa > 0 else np.nan,
                        cruz=int((sg[1:] != sg[:-1]).sum()) if len(sg) > 1 else 0,
                        toca=float(dentro[a:j + 1].mean()),
                    )
                for k, v in vals.items():
                    cols.setdefault(f'{k}_{W}{anc}', []).append(v)
    for k, v in cols.items():
        X[k] = v
    return X


# ================================================================== rotulos
ROT = {'er_100': 'Eficiencia do movimento em 100 candles (tendencia.html)'}
NOME_ANC = dict(p='antes do recuo', g='ate o trigger')
for _W in JAN:
    for _a in 'pg':
        _s = f'{_W} {NOME_ANC[_a]}'
        ROT.update({
            f'nfav_{_W}{_a}': f'Candles a favor menos contra da EMA ({_s})',
            f'lado_{_W}{_a}': f'Fracao no lado dominante ({_s})',
            f'soma_{_W}{_a}': f'Soma (fechamento - EMA21) / W em pts ({_s})',
            f'soman_{_W}{_a}': f'A mesma soma em ranges medios ({_s})',
            f'abs_{_W}{_a}': f'Distancia media absoluta ate a EMA em pts ({_s})',
            f'pureza_{_W}{_a}': f'Pureza |soma| / soma|dif| ({_s})',
            f'cruz_{_W}{_a}': f'Cruzamentos da EMA pelo fechamento ({_s})',
            f'toca_{_W}{_a}': f'Fracao de candles cortados pela EMA ({_s})',
        })

FAMILIAS = [
    ('Quantos candles de cada lado da EMA 21',
     'Fechamentos do lado favoravel ao trade menos os do lado contrario (na compra, acima da EMA conta a favor). '
     'E a fracao que ficou no lado dominante, sem olhar a direcao: 0,5 = metade de cada lado (oscilando), 1 = todos do mesmo lado.',
     [f'nfav_{W}{a}' for W in JAN for a in 'pg'] + [f'lado_{W}{a}' for W in JAN for a in 'pg']),
    ('Somatoria das distancias ate a EMA 21',
     'Soma de (fechamento - EMA21) dividida pela janela, orientada pelo lado do trade (positiva = preco esteve mais do lado favoravel). '
     'Em pontos e em ranges medios de 21 candles.',
     [f'soma_{W}{a}' for W in JAN for a in 'pg'] + [f'soman_{W}{a}' for W in JAN for a in 'pg']),
    ('Pureza: quanto a somatoria se cancela',
     '|soma das distancias| / soma dos valores absolutos. 1 = todos os candles do mesmo lado da media; perto de 0 = o que ficou acima '
     'foi cancelado pelo que ficou abaixo, ou seja, preco oscilando em torno da media. E a distancia media absoluta ate a EMA, para separar '
     'oscilacao larga de oscilacao apertada.',
     [f'pureza_{W}{a}' for W in JAN for a in 'pg'] + [f'abs_{W}{a}' for W in JAN for a in 'pg']),
    ('Cruzamentos e toques',
     'Quantas vezes o fechamento trocou de lado da EMA dentro da janela e que fracao dos candles teve a EMA dentro do proprio range.',
     [f'cruz_{W}{a}' for W in JAN for a in 'pg'] + [f'toca_{W}{a}' for W in JAN for a in 'pg']),
]


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


def mascara(f, X):
    v = f(X)
    if isinstance(v, pd.Series):
        v = v.fillna(False)
    return np.asarray(v, bool)


def main():
    import tendencia as TD
    TD.ROTULO.update(ROT)
    d = E.indicadores(E.carrega())
    dias = sorted(d['dia'].unique())
    corte = dias[int(len(dias) * 0.6)]
    S = E.sinais(d)
    S['treino'] = S['data'] < corte
    X = oscilacao(d, S)
    X = impulso(d, X)
    X['er_100'] = eficiencia(d, X)
    for gk, G in GESTOES.items():
        t = E.executa(d, X, 'fecha', G)
        X[f'rs_{gk}'] = E.reais(t); X[f'pts_{gk}'] = t['pts'].to_numpy()
        X[f'mot_{gk}'] = t['motivo'].to_numpy()
    tr = X['treino'].to_numpy()
    log('sinais', len(X), 'treino', int(tr.sum()))

    OUT = dict(meta=dict(corte=str(corte)[:10], inicio=str(dias[0])[:10], fim=str(dias[-1])[:10],
                         pregoes=len(dias), sinais=len(X), n_is=int(tr.sum()), n_oos=int((~tr).sum()),
                         rng_med=float(np.nanmedian(d['rng_med'])),
                         base={gk: dict(ev=media(X[f'rs_{gk}']), ev_is=media(X.loc[tr, f'rs_{gk}']),
                                        ev_oos=media(X.loc[~tr, f'rs_{gk}'])) for gk in GESTOES}),
               dist=[], familias=[], hipoteses=[], varredura=[], carteiras={}, combina={}, mapas=[], corr={})

    # ------------------------------------------------ distribuicao das medidas
    for W in JAN:
        for a, _ in ANC:
            for m in MET:
                col = f'{m}_{W}{a}'
                x = X[col].to_numpy(float)
                OUT['dist'].append(dict(col=col, rotulo=ROT[col], met=m, W=W, anc=a,
                                        **{f'p{p}': float(np.nanpercentile(x, p)) for p in (5, 25, 50, 75, 95)},
                                        media=float(np.nanmean(x)), nan=int(np.isnan(x).sum())))
    log('distribuicoes')

    # ------------------------------------------------ tabelas por quintil
    cols = [c for _, _, cs in FAMILIAS for c in cs]
    cortes = {c: TD.cortes_treino(X.loc[X['treino'], c]) for c in cols}
    for nome, desc, cs in FAMILIAS:
        bl = []
        for c in cs:
            tabs = {}
            for gk in GESTOES:
                Xg = X.assign(rs=X[f'rs_{gk}'], pts=X[f'pts_{gk}'])
                tabs[gk] = TD.tabela(Xg, c, cortes[c])
            bl.append(dict(col=c, rotulo=ROT[c], met=c.split('_')[0], W=int(c.split('_')[1][:-1]),
                           anc=c[-1], tabs=tabs))
        OUT['familias'].append(dict(familia=nome, desc=desc, blocos=bl))
    log('familias')

    # ------------------------------------------------ hipoteses
    HIP = []
    for W in JAN:
        for a, ra in ANC:
            HIP += [
                (f'Oscilando: no maximo 60% dos {W} fechamentos do mesmo lado ({ra})', lambda Z, W=W, a=a: Z[f'lado_{W}{a}'] <= 0.6),
                (f'Um lado so: todos os {W} fechamentos do mesmo lado ({ra})', lambda Z, W=W, a=a: Z[f'lado_{W}{a}'] >= 1.0),
                (f'Pureza baixa (< 0,3) em {W} ({ra})', lambda Z, W=W, a=a: Z[f'pureza_{W}{a}'] < 0.3),
                (f'Pureza alta (>= 0,7) em {W} ({ra})', lambda Z, W=W, a=a: Z[f'pureza_{W}{a}'] >= 0.7),
                (f'Somatoria contra o trade em {W} ({ra})', lambda Z, W=W, a=a: Z[f'soma_{W}{a}'] < 0),
                (f'Somatoria a favor e forte (>= 1 range medio) em {W} ({ra})', lambda Z, W=W, a=a: Z[f'soman_{W}{a}'] >= 1),
                (f'Sem nenhum cruzamento da EMA em {W} ({ra})', lambda Z, W=W, a=a: Z[f'cruz_{W}{a}'] == 0),
                (f'3 ou mais cruzamentos da EMA em {W} ({ra})', lambda Z, W=W, a=a: Z[f'cruz_{W}{a}'] >= 3),
                (f'EMA dentro do range em mais de 40% dos candles de {W} ({ra})', lambda Z, W=W, a=a: Z[f'toca_{W}{a}'] > 0.4),
            ]
    HIP += [
        ('Oscilando em 20 E somatoria contra (antes do recuo)', lambda Z: (Z['pureza_20p'] < 0.3) & (Z['soma_20p'] < 0)),
        ('Oscilando em 20 E oscilacao apertada (distancia media < 50 pts)', lambda Z: (Z['pureza_20p'] < 0.3) & (Z['abs_20p'] < 50)),
        ('Pureza alta em 20 E somatoria a favor', lambda Z: (Z['pureza_20p'] >= 0.7) & (Z['soma_20p'] > 0)),
        ('Pureza alta em 20 E somatoria contra (preco preso do lado errado)', lambda Z: (Z['pureza_20p'] >= 0.7) & (Z['soma_20p'] < 0)),
        ('Pureza alta em 5, 10 e 20 ao mesmo tempo', lambda Z: (Z['pureza_5p'] >= 0.7) & (Z['pureza_10p'] >= 0.7) & (Z['pureza_20p'] >= 0.7)),
        ('Oscilando em 20 (pureza < 0,3) E fora da consolidacao 100', lambda Z: (Z['pureza_20p'] < 0.3) & (Z['er_100'] >= 0.08)),
    ]
    for gk in GESTOES:
        rs_ = X[f'rs_{gk}'].to_numpy(); falha = (X[f'mot_{gk}'] == 'stop').to_numpy()
        for nome, f in HIP:
            mk = mascara(f, X)
            if mk.sum() < 25 or (~mk).sum() < 25:
                continue
            r = compara(rs_, tr, mk, n_sort=1500)
            r.update(gestao=gk, nome=nome, falha=float(falha[mk].mean() * 100), falha_resto=float(falha[~mk].mean() * 100))
            OUT['hipoteses'].append(r)
    log('hipoteses', len(OUT['hipoteses']))

    # ------------------------------------------------ varredura de limiares
    GRADE = ([('pureza', W, a, k) for W in JAN for a in 'pg' for k in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7)] +
             [('lado', W, a, k) for W in JAN for a in 'pg' for k in (0.6, 0.7, 0.8, 0.9, 1.0)] +
             [('soman', W, a, k) for W in JAN for a in 'pg' for k in (-1.0, -0.5, 0.0, 0.5, 1.0)])
    for met, W, a, k in GRADE:
        col = f'{met}_{W}{a}'
        mk = (X[col] >= k).to_numpy()
        if mk.sum() < 25 or (~mk).sum() < 25:
            continue
        for gk in GESTOES:
            r = compara(X[f'rs_{gk}'].to_numpy(), tr, mk, n_sort=800)
            r.update(met=met, W=W, anc=a, k=k, gestao=gk, col=col)
            OUT['varredura'].append(r)
    log('varredura', len(OUT['varredura']))

    # ------------------------------------------------ mapas 2D
    PARES = [('soma_20p', 'pureza_20p'), ('cruz_20p', 'abs_20p'), ('cruz_20p', 'er_100')]
    for cx, cy in PARES:
        for gk in GESTOES:
            Xg = X.assign(rs=X[f'rs_{gk}'], pts=X[f'pts_{gk}'])
            Xg = Xg[Xg[cx].notna() & Xg[cy].notna()]     # 3 sinais no inicio do pregao
            mp = TD.mapa(Xg, cx, cy)
            mp.update(gestao=gk, rot_x=ROT.get(cx, cx), rot_y=ROT.get(cy, cy))
            OUT['mapas'].append(mp)
    log('mapas')

    # ------------------------------------------------ carteiras
    FILTROS = [('sem filtro', lambda Z: pd.Series(True, index=Z.index)),
               ('pureza 5 (antes do recuo) >= 0,7', lambda Z: Z['pureza_5p'] >= 0.7),
               ('pureza 5 (antes do recuo) >= 0,5', lambda Z: Z['pureza_5p'] >= 0.5),
               ('4 dos 5 fechamentos do mesmo lado', lambda Z: Z['lado_5p'] >= 0.8),
               ('pureza 10 (antes do recuo) >= 0,5', lambda Z: Z['pureza_10p'] >= 0.5),
               ('pureza 20 (antes do recuo) >= 0,3', lambda Z: Z['pureza_20p'] >= 0.3),
               ('pureza 20 (antes do recuo) >= 0,5', lambda Z: Z['pureza_20p'] >= 0.5),
               ('lado dominante 20 >= 0,7', lambda Z: Z['lado_20p'] >= 0.7),
               ('somatoria 20 a favor (>= 0)', lambda Z: Z['soman_20p'] >= 0),
               ('2 a 4 cruzamentos da EMA em 20', lambda Z: (Z['cruz_20p'] >= 2) & (Z['cruz_20p'] <= 4)),
               ('pelo menos 2 cruzamentos da EMA em 20', lambda Z: Z['cruz_20p'] >= 2),
               ('no maximo 2 cruzamentos da EMA em 20', lambda Z: Z['cruz_20p'] <= 2),
               ('distancia media ate a EMA em 20 < 211 pts', lambda Z: Z['abs_20p'] < 211.45),
               ('fora de: 0-1 cruzamento E distancia media > 177 pts', lambda Z: ~((Z['cruz_20p'] <= 1) & (Z['abs_20p'] > 176.56))),
               ('EMA dentro do range em <= 40% dos candles de 20', lambda Z: Z['toca_20p'] <= 0.4)]
    for gk, G in GESTOES.items():
        lin = []
        for nome, f in FILTROS:
            mk = mascara(f, X)
            lin.append(dict(nome=nome, frac=float(mk.mean()), **TD.stats_cart(d, X[mk], G, corte)))
        OUT['carteiras'][gk] = lin
        log('carteira', gk, [round(l['stats']['liquido']) for l in lin])

    # ------------------------------------------------ combinacao com os candidatos
    cons = (X['er_100'] >= 0.08).to_numpy(); nao_kc = (X['kc_10'] < 1).to_numpy()
    pur = (X['pureza_5p'] >= 0.7).to_numpy()
    cz = ((X['cruz_20p'] >= 2) & (X['cruz_20p'] <= 4)).to_numpy()
    perto = (X['abs_20p'] < 211.45).to_numpy()
    fora = ~((X['cruz_20p'] <= 1) & (X['abs_20p'] > 176.56)).to_numpy()
    for gk, G in GESTOES.items():
        lin = []
        for nome, mk in [('sem filtro', np.ones(len(X), bool)),
                         ('fora da consolidacao 100 (er >= 0,08)', cons),
                         ('nao passou da Keltner 2,5', nao_kc),
                         ('consolidacao 100 E Keltner', cons & nao_kc),
                         ('pureza 5 >= 0,7', pur),
                         ('pureza 5 >= 0,7 E consolidacao 100', pur & cons),
                         ('pureza 5 >= 0,7 E consolidacao 100 E Keltner', pur & cons & nao_kc),
                         ('2 a 4 cruzamentos em 20', cz),
                         ('2 a 4 cruzamentos em 20 E consolidacao 100 E Keltner', cz & cons & nao_kc),
                         ('pureza 5 E 2 a 4 cruzamentos E consolidacao 100 E Keltner', pur & cz & cons & nao_kc),
                         ('distancia media < 211 pts E consolidacao 100 E Keltner', perto & cons & nao_kc),
                         ('fora do canto ruim (0-1 cruzamento E longe da EMA)', fora),
                         ('fora do canto ruim E consolidacao 100', fora & cons),
                         ('fora do canto ruim E consolidacao 100 E Keltner', fora & cons & nao_kc)]:
            lin.append(dict(nome=nome, frac=float(mk.mean()), **TD.stats_cart(d, X[mk], G, corte)))
        OUT['combina'][gk] = lin
        log('combina', gk, [round(l['stats']['liquido']) for l in lin])

    # ------------------------------------------------ estabilidade por terco do periodo
    DESTAQUE = [('pureza 5 >= 0,7 (nao oscilou nos 5 candles)', (X['pureza_5p'] >= 0.7).to_numpy()),
                ('pureza 20 >= 0,3', (X['pureza_20p'] >= 0.3).to_numpy()),
                ('2 a 4 cruzamentos da EMA em 20', cz),
                ('nenhum cruzamento da EMA em 20', (X['cruz_20p'] == 0).to_numpy()),
                ('distancia media ate a EMA em 20 < 211 pts', perto),
                ('somatoria 20 a favor (>= 0)', (X['soman_20p'] >= 0).to_numpy()),
                ('0-1 cruzamento E distancia media > 177 pts (canto ruim)', ~fora)]
    t3 = np.array_split(np.array(dias), 3)
    blocos = [('1o terco', X['data'].to_numpy() <= t3[0][-1]),
              ('2o terco', (X['data'].to_numpy() > t3[0][-1]) & (X['data'].to_numpy() <= t3[1][-1])),
              ('3o terco', X['data'].to_numpy() > t3[1][-1])]
    est = []
    for nome, mk in DESTAQUE:
        lin = dict(nome=nome, frac=float(mk.mean()), blocos=[])
        for rot, bm in blocos:
            cel = dict(bloco=rot, n=int((mk & bm).sum()), n_fora=int((~mk & bm).sum()),
                       ini=str(pd.Timestamp(X['data'][bm].min()))[:10], fim=str(pd.Timestamp(X['data'][bm].max()))[:10])
            for gk in GESTOES:
                rs_ = X[f'rs_{gk}'].to_numpy()
                cel[gk] = dict(ev=media(rs_[mk & bm]), resto=media(rs_[~mk & bm]))
            lin['blocos'].append(cel)
        est.append(lin)
    OUT['estabilidade'] = est
    OUT['meta']['tercos'] = [dict(rot=r, ini=str(pd.Timestamp(X['data'][b].min()))[:10], fim=str(pd.Timestamp(X['data'][b].max()))[:10]) for r, b in blocos]
    log('estabilidade')

    # ------------------------------------------------ correlacoes
    ref = ['er_100', 'inversoes', 'kc_10', 'imp_20', 'ret_20', 'barras_regime', 'n_rec']
    novos = [f'{m}_20p' for m in MET] + ['pureza_10p', 'pureza_5p', 'pureza_20g']
    OUT['corr'] = {c: {r: float(X[[c, r]].corr(method='spearman').iloc[0, 1]) for r in ref} for c in novos}
    OUT['corr_internas'] = {c: {c2: float(X[[c, c2]].corr(method='spearman').iloc[0, 1]) for c2 in novos} for c in novos}
    OUT['rot'] = ROT

    with open(os.path.join(SAIDA, 'oscila.json'), 'w', encoding='utf-8') as f:
        json.dump(limpa(OUT), f, ensure_ascii=False)
    log('ok ->', os.path.join(SAIDA, 'oscila.json'))


if __name__ == '__main__':
    main()
