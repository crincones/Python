# -*- coding: utf-8 -*-
"""
Nucleo do estudo "barra grande que pivota num nivel" - WIN, 10.000 ticks.

A pergunta, na forma em que foi feita: barras GRANDES que pivotam ao redor
das MEDIAS, da VWAP ou dos PONTOS DE PIVO costumam (a) andar - o movimento
segue - ou (b) marcar reversao confiavel?

As duas metades sao afirmacoes DIFERENTES e sao medidas separadamente. E as
duas so significam alguma coisa contra um CONTROLE: a mesma medida em barras
grandes SEM nivel nenhum, e em todas as barras. Sem isso, o que se mede e
"barra grande", nao "barra grande no nivel".

A carga, o range medio e a simulacao de trade sao os mesmos do projeto
Backtest-Rincones1, reimplantados aqui para o estudo ficar de pe sozinho.
"""
import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(BASE, 'dados')
SAIDA = os.path.join(BASE, 'saida')

ARQUIVOS = {
    'WINFUT': os.path.join(DADOS, 'WIFNUT_10000T_28-28-26.csv'),
    'WINV26': os.path.join(DADOS, 'WINV26_10000T_28-08-26.csv'),
}

TICK = 5.0             # tick do WIN, em pontos
VAL_PONTO = 0.20       # R$ por ponto, 1 contrato
PERIODO_RANGE = 20     # janela do range medio - a unidade de "grande"

# --- gestao, identica a do Backtest-Rincones1 (para os numeros conversarem)
STOP = 150.0
FRAC_PARCIAL = 0.50    # a parcial sai na MESMA distancia do stop
ALVO = 300.0


# ============================================================ carga de dados
def carrega(caminho):
    """Le o csv exportado do Profit, em ordem cronologica."""
    df = pd.read_csv(caminho, sep='\t', decimal=',', thousands='.')
    df.columns = ['Data', 'O', 'H', 'L', 'C',
                  'Buy', 'Sell', 'DurX1000', 'Qtd', 'Trades']
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y %H:%M')
    df = df.iloc[::-1].reset_index(drop=True)      # o csv vem do mais novo p/ o antigo
    df['dia'] = df['Data'].dt.date
    df = df[(df.Buy + df.Sell) > 0].reset_index(drop=True)
    return df


def _ema(x, n):
    return pd.Series(x).ewm(span=n, adjust=False).mean().to_numpy()


# =================================================== os niveis de referencia
#
# Todos causais: cada nivel na barra i so usa informacao ate a barra i. Os
# pivos usam o pregao ANTERIOR inteiro, que e como se calculam de verdade.
#
FAMILIAS = {
    'medias': ['ema21', 'ema42', 'ema72'],
    'vwap':   ['vwap'],
    'pivos':  ['pp', 'r1', 's1', 'r2', 's2'],
    'diant':  ['phi', 'plo'],
}
ROT_FAM = {'medias': 'médias 21/42/72', 'vwap': 'VWAP da sessão',
           'pivos': 'pontos de pivô', 'diant': 'máx/mín do dia anterior',
           'qualquer': 'qualquer nível'}


def niveis(d):
    """Dicionario nome -> vetor de precos, alinhado com as barras."""
    C = d.C.to_numpy(float); H = d.H.to_numpy(float); L = d.L.to_numpy(float)
    q = d.Qtd.to_numpy(float); dia = d.dia.to_numpy()
    N = {'ema21': _ema(C, 21), 'ema42': _ema(C, 42), 'ema72': _ema(C, 72)}

    # VWAP ancorada na abertura do pregao
    tp = (H + L + C) / 3.0
    vw = np.empty(len(d)); cv = cq = 0.0; ant = None
    for i in range(len(d)):
        if dia[i] != ant:
            cv = cq = 0.0; ant = dia[i]
        cv += tp[i] * q[i]; cq += q[i]
        vw[i] = cv / cq if cq > 0 else np.nan
    N['vwap'] = vw

    # pivos classicos, do pregao anterior
    g = d.groupby('dia').agg(hh=('H', 'max'), ll=('L', 'min'), cc=('C', 'last')).shift(1)
    pp = (g.hh + g.ll + g.cc) / 3.0
    for k, v in {'pp': pp, 'r1': 2 * pp - g.ll, 's1': 2 * pp - g.hh,
                 'r2': pp + (g.hh - g.ll), 's2': pp - (g.hh - g.ll),
                 'phi': g.hh, 'plo': g.ll}.items():
        N[k] = d.dia.map(v).to_numpy(float)
    return N


def contexto(d):
    """range medio, tamanho relativo da barra e a direcao do corpo."""
    d = d.copy()
    H = d.H.to_numpy(float); L = d.L.to_numpy(float)
    mrng = pd.Series(H - L).rolling(PERIODO_RANGE).mean().to_numpy()
    d['mrng'] = np.where((mrng > 0) & ~np.isnan(mrng), mrng, np.nan)
    d['tam'] = (H - L) / d.mrng                       # "grande" = tam >= FATOR
    d['sb'] = np.sign(d.C - d.O).astype(int)          # direcao do corpo
    return d


def toca(d, N, familia, tol_rng=0.0):
    """Quantos niveis da familia a barra alcanca, e o mais CENTRADO deles.

    tol_rng estica a barra em fracoes do proprio range para os dois lados:
    0 = o nivel tem de estar DENTRO da barra; 0.25 = vale tambem o nivel a
    ate um quarto de range de distancia. E a folga do "pivotar ao redor" -
    sem ela, so conta o toque literal.
    """
    H = d.H.to_numpy(float); L = d.L.to_numpy(float)
    O = d.O.to_numpy(float); C = d.C.to_numpy(float)
    rng = H - L; meio = (H + L) / 2.0
    lo = L - tol_rng * rng; hi = H + tol_rng * rng
    lo_c = np.minimum(O, C); hi_c = np.maximum(O, C)

    chaves = (FAMILIAS[familia] if familia in FAMILIAS
              else [k for ks in FAMILIAS.values() for k in ks])
    n = len(d)
    conta = np.zeros(n, int)          # quantos niveis a barra alcanca
    no_corpo = np.zeros(n, bool)      # algum nivel cortado pelo CORPO
    pav_b = np.zeros(n, bool)         # nivel no pavio de baixo
    pav_c = np.zeros(n, bool)         # nivel no pavio de cima
    cent = np.full(n, 9.9)            # |nivel - meio| / range, do mais centrado
    for k in chaves:
        lvl = N[k]; ok = ~np.isnan(lvl)
        dentro = ok & (lo <= lvl) & (lvl <= hi)
        conta += dentro.astype(int)
        no_corpo |= dentro & (lo_c <= lvl) & (lvl <= hi_c)
        pav_b |= dentro & (lvl < lo_c)
        pav_c |= dentro & (lvl > hi_c)
        with np.errstate(invalid='ignore'):
            dd = np.abs(lvl - meio) / np.where(rng > 0, rng, np.nan)
        cent = np.where(dentro & (dd < cent), dd, cent)
    return dict(conta=conta, no_corpo=no_corpo, cent=cent,
                pavio_b=pav_b & ~pav_c & ~no_corpo,
                pavio_c=pav_c & ~pav_b & ~no_corpo)


# ================================================= a medida sem pressupostos
#
# Uma corrida SIMETRICA +X / -X a partir de um preco de entrada. Simetrica de
# proposito: sem alvo maior que stop, sem parcial, sem nada que possa criar
# ou esconder vantagem. Em barra sem informacao nenhuma ela da 50%, e e esse
# o unico numero contra o qual vale comparar. Quando alvo e stop cabem na
# mesma barra, conta STOP - o lado pessimista.
#
def corrida(H, L, dia, n, i, s, ent, X):
    for j in range(i + 1, n):
        if dia[j] != dia[i]:
            break
        if (s == 1 and L[j] <= ent - X) or (s == -1 and H[j] >= ent + X):
            return -1
        if (s == 1 and H[j] >= ent + X) or (s == -1 and L[j] <= ent - X):
            return +1
    return 0


def rompe_extremo(H, L, dia, n, i, s, max_barras=5):
    """Primeira barra, em ate max_barras do mesmo pregao, que rompe o extremo
    da barra i no lado s. Devolve (barra, preco do gatilho) ou (-1, 0)."""
    gat = (H[i] + TICK) if s == 1 else (L[i] - TICK)
    c = 0
    for j in range(i + 1, n):
        if dia[j] != dia[i] or c >= max_barras:
            break
        c += 1
        if (s == 1 and H[j] >= gat) or (s == -1 and L[j] <= gat):
            return j, gat
    return -1, 0.0


def tstat(pnl, dias):
    """t do PnL POR PREGAO - a unidade independente. Por trade, trades do
    mesmo dia sao correlacionados e o t sai inflado."""
    g = pd.Series(pnl).groupby(pd.Series(dias)).sum()
    if len(g) < 3 or g.std() == 0:
        return float('nan')
    return float(g.mean() / (g.std() / np.sqrt(len(g))))


def celula(H, L, dia, n, idx, lados, ents, X):
    """Mede uma celula: n, acerto, EV em pontos, t por pregao."""
    res, dd = [], []
    for i, s, e in zip(idx, lados, ents):
        r = corrida(H, L, dia, n, int(i), int(s), float(e), X)
        if r != 0:
            res.append(r); dd.append(dia[int(i)])
    if not res:
        return None
    r = np.array(res, float)
    pnl = X * r
    return dict(n=len(r), acerto=100.0 * float((r > 0).mean()),
                ev=float(pnl.mean()), t=tstat(pnl, np.array(dd)))


# ======================================================= simulacao de trade
#
# A gestao da casa, para o visualizador: entrada a mercado no gatilho, stop
# 150, parcial de 50% na mesma distancia do stop, stop do restante na MEDIA
# DA OPERACAO (que ali e o proprio stop inicial: o trade que volta morre em
# zero de verdade), alvo 300.
#
def simula(H, L, C, dia, n, i, s, ent):
    stop_ini = ent - s * STOP
    parc_p = ent + s * STOP
    alvo_p = ent + s * ALVO
    stop_p = stop_ini
    fase, pnl, res, ult, barras = 1, 0.0, 'fim', i, 0
    k = i
    for k in range(i + 1, n):
        if dia[k] != dia[i]:
            k = ult
            break
        ult = k; barras += 1
        hit_s = (L[k] <= stop_p) if s == 1 else (H[k] >= stop_p)
        if fase == 1:
            if hit_s:
                pnl = -STOP; res = 'stop'; break
            hit_p = (H[k] >= parc_p) if s == 1 else (L[k] <= parc_p)
            if hit_p:
                pnl = FRAC_PARCIAL * STOP
                fase = 2
                stop_p = stop_ini          # = media da operacao, com meia posicao
                hit_a = (H[k] >= alvo_p) if s == 1 else (L[k] <= alvo_p)
                if hit_a:
                    pnl += (1 - FRAC_PARCIAL) * ALVO; res = 'alvo'; break
                continue
        else:
            if hit_s:
                pnl += (1 - FRAC_PARCIAL) * s * (stop_p - ent); res = 'zero'; break
            hit_a = (H[k] >= alvo_p) if s == 1 else (L[k] <= alvo_p)
            if hit_a:
                pnl += (1 - FRAC_PARCIAL) * ALVO; res = 'alvo'; break
    if res == 'fim':
        if k <= i:
            return None
        saida = C[k]
        pnl = (s * (saida - ent) if fase == 1
               else pnl + (1 - FRAC_PARCIAL) * s * (saida - ent))
    return dict(i=int(i), saiu=int(k), s=int(s), ent=float(ent), res=res,
                pnl=float(pnl), dia=dia[i], barras=barras)


def metricas(tr):
    if tr is None or len(tr) == 0:
        return None
    g = tr.groupby('dia').pnl.sum()
    eq = tr.pnl.cumsum().to_numpy()
    ganhos = tr.pnl[tr.pnl > 0].sum(); perdas = -tr.pnl[tr.pnl < 0].sum()
    return dict(
        n=len(tr), pregoes=len(g), por_pregao=len(tr) / len(g),
        ev=float(tr.pnl.mean()), total=float(tr.pnl.sum()),
        total_rs=float(tr.pnl.sum() * VAL_PONTO),
        acerto=100.0 * float((tr.pnl > 0).mean()),
        t=tstat(tr.pnl.to_numpy(), tr.dia.to_numpy()),
        dias_pos=100.0 * float((g > 0).mean()),
        dd=float((np.maximum.accumulate(eq) - eq).max()) if len(eq) else 0.0,
        pf=float(ganhos / perdas) if perdas > 0 else float('inf'),
        p_alvo=100.0 * float((tr.res == 'alvo').mean()),
        p_stop=100.0 * float((tr.res == 'stop').mean()),
        p_zero=100.0 * float((tr.res == 'zero').mean()),
        p_fim=100.0 * float((tr.res == 'fim').mean()),
        barras=float(tr.barras.mean()),
    )


def prepara(nome):
    d = contexto(carrega(ARQUIVOS[nome]))
    return d, niveis(d)
