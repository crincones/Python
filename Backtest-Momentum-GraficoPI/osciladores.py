# -*- coding: utf-8 -*-
"""
MACD, estocastico lento e IFR ajudam a filtrar o Hull + pavios?

    python osciladores.py            -> saida/osciladores.json + console
    python relatorio_osciladores.py  -> osciladores.html + OSCILADORES.md

Parte dos mesmos sinais de hull_contra.py (compra; venda e o espelho):

  h      Hull 50 subindo + 2 a 4 candles de baixa + 1 candle de alta.
         Compra no fechamento dele. E a regra que passou no teste fora da
         amostra.
  cand   h + 2 a 3 candles + pavio do lado do fechamento ate 10% do corpo
         ("Hull + pavios", o candidato do primeiro estudo).

Os tres osciladores, com os parametros PADRAO do Profit, declarados antes
de olhar qualquer resultado:

  MACD              EMA 12 - EMA 26 do fechamento; sinal = EMA 9 da linha;
                    histograma = linha - sinal.
  Estocastico lento %K rapido de 14 (fechamento contra a faixa de 14
                    maximas/minimas), %K lento = media simples de 3 do
                    rapido, %D = media simples de 3 do %K lento.
  IFR               14, suavizacao de Wilder.

Tudo e lido NO FECHAMENTO do candle de sinal (a barra da entrada) ou nas
barras da retracao, que ja fecharam -- nada do futuro. Na venda, as leituras
sao espelhadas (MACD com sinal trocado, 100 - %K, 100 - IFR), entao toda
regra abaixo se le "do ponto de vista da compra".

As regras, fechadas ANTES de medir (11):

  M1  MACD acima de zero                  (tendencia a favor)
  M2  MACD acima da linha de sinal        (momento a favor)
  M3  histograma subindo na barra do sinal (momento virando a favor)
  M4  M1 e M3
  E1  %K acima de %D
  E2  %K cruzou %D para cima NA barra do sinal
  E3  %K abaixo de 20 em alguma barra da retracao (sobrevenda no recuo)
  E4  %K abaixo de 80 no sinal            (nao sobrecomprado)
  I1  IFR acima de 50
  I2  IFR abaixo de 40 em alguma barra da retracao
  I3  IFR abaixo de 70 no sinal

Depois de ver a FREQUENCIA (nao o resultado) -- E1, E2, E3, I2 e I3 aceitam
menos de 5% ou mais de 95% dos sinais --, cinco regras por quintil da
propria distribuicao: M5 histograma no quintil de cima, E5 menor %K da
retracao no de baixo, E6 %K-%D no de cima, I4 menor IFR da retracao no de
baixo, I5 IFR no de cima. Total: 16.

Aviso que muda a leitura do IFR: no grafico de 20 PI todo fechamento anda
exatamente 100 pontos (salvo virada de dia). O IFR, que divide a media das
altas pela media das variacoes, vira a PROPORCAO SUAVIZADA DE CANDLES DE
ALTA. Nao e defeito; e o que o IFR mede neste grafico.

Controles, os mesmos dos estudos anteriores e mais um:
  . EV dentro x fora da regra, e teste de permutacao do ganho;
  . tercos, compra x venda, sorteio de subconjuntos do mesmo tamanho;
  . blocos antes / janela original / depois (periodos.py);
  . BUSCA: 16 regras x 2 sentidos (a regra e o seu complemento) = 32
    candidatos por conjunto. O melhor e comparado com o melhor que a mesma
    busca acha com os resultados embaralhados;
  . ESCOLHA FORA: a regra escolhida so com o bloco "antes" e medida no resto,
    e a escolhida em T1+T2 e medida em T3;
  . PODER: o menor ganho que a amostra enxerga;
  . VIZINHANCA dos parametros (MACD 8/17 e 19/39, estocastico 8 e 21, IFR 9
    e 21) -- nao para escolher, para ver se ha plato.
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
import periodos as PR

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')

MACD_P = (12, 26, 9)
ESTOC_P = (14, 3, 3)
IFR_P = 14
VIZ = dict(macd=[(8, 17, 9), (12, 26, 9), (19, 39, 9)],
           estoc=[(8, 3, 3), (14, 3, 3), (21, 3, 3)],
           ifr=[9, 14, 21])

REGRAS = {
    'M1': ('MACD', 'MACD acima de zero'),
    'M2': ('MACD', 'MACD acima da linha de sinal'),
    'M3': ('MACD', 'Histograma do MACD subindo'),
    'M4': ('MACD', 'MACD acima de zero e histograma subindo'),
    'E1': ('Estocastico', '%K acima de %D'),
    'E2': ('Estocastico', '%K cruzou %D para cima no sinal'),
    'E3': ('Estocastico', '%K abaixo de 20 na retracao'),
    'E4': ('Estocastico', '%K abaixo de 80 no sinal'),
    'I1': ('IFR', 'IFR acima de 50'),
    'I2': ('IFR', 'IFR abaixo de 40 na retracao'),
    'I3': ('IFR', 'IFR abaixo de 70 no sinal'),
    # por QUANTIL da propria distribuicao (definidas pela frequencia, sem olhar
    # resultado): as regras classicas acima quase nunca disparam neste padrao
    'M5': ('MACD', 'Histograma no quintil mais alto'),
    'E5': ('Estocastico', 'Menor %K da retracao no quintil mais baixo'),
    'E6': ('Estocastico', '%K - %D no quintil mais alto'),
    'I4': ('IFR', 'Menor IFR da retracao no quintil mais baixo'),
    'I5': ('IFR', 'IFR no quintil mais alto'),
}
CLASSICAS = ('M1', 'M2', 'M3', 'M4', 'E1', 'E2', 'E3', 'E4', 'I1', 'I2', 'I3')
CONJ = {'h': 'Hull + 2 a 4', 'cand': 'Hull + pavios (2-3 + fech ate 10%)'}
CONTINUAS = {
    'macd_atr': 'MACD / ATR (a favor)',
    'hist_atr': 'Histograma / ATR (a favor)',
    'k': '%K lento no sinal (a favor)',
    'kd': '%K - %D (a favor)',
    'k_min': 'Menor %K da retracao (a favor)',
    'ifr': 'IFR no sinal (a favor)',
    'ifr_min': 'Menor IFR da retracao (a favor)',
}
N_PERM = 2000

_buf = io.StringIO()


def p(*a, **k):
    print(*a, **k)
    print(*a, **k, file=_buf)


# ============================================================== indicadores
def _ema_nan(x, n):
    """EMA com semente aritmetica que comeca no primeiro valor valido."""
    x = np.asarray(x, float)
    out = np.full(len(x), np.nan)
    ok = np.nonzero(~np.isnan(x))[0]
    if len(ok) < n:
        return out
    a = ok[0]
    out[a:] = E._ema(x[a:], n)
    return out


def macd(c, rapida, lenta, sinal):
    linha = E._ema(c, rapida) - E._ema(c, lenta)
    sig = _ema_nan(linha, sinal)
    return linha, sig, linha - sig


def estoc_lento(h, l, c, n, suav, media):
    hh = pd.Series(h).rolling(n).max().to_numpy()
    ll = pd.Series(l).rolling(n).min().to_numpy()
    faixa = hh - ll
    with np.errstate(invalid='ignore', divide='ignore'):
        kr = np.where(faixa > 0, 100 * (c - ll) / faixa, 50.0)
    kr[np.isnan(hh)] = np.nan
    k = pd.Series(kr).rolling(suav).mean().to_numpy()
    d = pd.Series(k).rolling(media).mean().to_numpy()
    return k, d


def ifr(c, n):
    dc = np.diff(c, prepend=np.nan)
    alta = np.where(dc > 0, dc, 0.0)
    baixa = np.where(dc < 0, -dc, 0.0)
    alta[0] = baixa[0] = np.nan
    out = np.full(len(c), np.nan)
    if len(c) <= n:
        return out
    ma = np.nanmean(alta[1:n + 1]); mb = np.nanmean(baixa[1:n + 1])
    for i in range(n, len(c)):
        if i > n:
            ma = (ma * (n - 1) + alta[i]) / n
            mb = (mb * (n - 1) + baixa[i]) / n
        out[i] = 100.0 if mb == 0 else 100 - 100 / (1 + ma / mb)
    return out


def osciladores(d, mp=MACD_P, ep=ESTOC_P, ip=IFR_P):
    c = d['c'].to_numpy(float)
    lin, sig, hist = macd(c, *mp)
    k, dd = estoc_lento(d['h'].to_numpy(float), d['l'].to_numpy(float), c, *ep)
    return dict(macd=lin, sinal=sig, hist=hist, k=k, d=dd, ifr=ifr(c, ip))


# ============================================================== atributos
def atributos(u, d, osc, limites=None):
    """Leituras espelhadas no sentido do trade, e as 16 regras."""
    i = u['i'].to_numpy(int)
    ld = u['lado'].to_numpy(int)
    nf = u['n_fav'].to_numpy(int)
    at = d['atr'].to_numpy(float)
    espelho = lambda x, idx: np.where(ld > 0, x[idx], 100 - x[idx])
    u = u.copy()
    u['macd_atr'] = osc['macd'][i] * ld / at[i]
    u['hist_atr'] = osc['hist'][i] * ld / at[i]
    u['macd_sig'] = (osc['macd'][i] - osc['sinal'][i]) * ld
    u['hist_sobe'] = (osc['hist'][i] - osc['hist'][i - 1]) * ld > 0
    u['k'] = espelho(osc['k'], i)
    u['dd'] = espelho(osc['d'], i)
    u['kd'] = u['k'] - u['dd']
    k_ant = espelho(osc['k'], i - 1); d_ant = espelho(osc['d'], i - 1)
    u['cruz_kd'] = (u['kd'] > 0) & ((k_ant - d_ant) <= 0)
    u['ifr'] = espelho(osc['ifr'], i)
    kmin = np.full(len(u), np.nan); imin = np.full(len(u), np.nan)
    for j in range(len(u)):
        a, b = i[j] - nf[j], i[j]                  # barras da retracao: [i-n, i-1]
        kk = osc['k'][a:b]; ii = osc['ifr'][a:b]
        if ld[j] < 0:
            kk = 100 - kk; ii = 100 - ii
        kmin[j] = np.nanmin(kk) if np.isfinite(kk).any() else np.nan
        imin[j] = np.nanmin(ii) if np.isfinite(ii).any() else np.nan
    u['k_min'] = kmin; u['ifr_min'] = imin
    u['M1'] = u['macd_atr'] > 0
    u['M2'] = u['macd_sig'] > 0
    u['M3'] = u['hist_sobe']
    u['M4'] = u['M1'] & u['M3']
    u['E1'] = u['kd'] > 0
    u['E2'] = u['cruz_kd']
    u['E3'] = u['k_min'] < 20
    u['E4'] = u['k'] < 80
    u['I1'] = u['ifr'] > 50
    u['I2'] = u['ifr_min'] < 40
    u['I3'] = u['ifr'] < 70
    if limites is None:
        limites = dict(hist_atr=float(np.nanpercentile(u['hist_atr'], 80)),
                       k_min=float(np.nanpercentile(u['k_min'], 20)),
                       kd=float(np.nanpercentile(u['kd'], 80)),
                       ifr_min=float(np.nanpercentile(u['ifr_min'], 20)),
                       ifr=float(np.nanpercentile(u['ifr'], 80)))
    u['M5'] = u['hist_atr'] > limites['hist_atr']
    u['E5'] = u['k_min'] < limites['k_min']
    u['E6'] = u['kd'] > limites['kd']
    u['I4'] = u['ifr_min'] < limites['ifr_min']
    u['I5'] = u['ifr'] > limites['ifr']
    u.attrs['limites'] = limites
    u['osc_ok'] = np.isfinite(u[['macd_atr', 'hist_atr', 'k', 'dd', 'ifr']].to_numpy(float)).all(axis=1)
    return u


def universo(d):
    """Os sinais de hull_contra: Hull 50 a favor + 2 a 4 candles contra."""
    u = P.universo(d)
    for per in HC.HULL_TESTE:
        u = HC.anexa_hull(u, d, per, f'hull{per}')
    u = u[u['hull80_valida'] & u['hull50'] & u['n_fav'].between(2, 4)].reset_index(drop=True)
    u['cand'] = (u['n_fav'] <= 3) & (u['pav_outro_pct'] <= 10)
    return u


# ================================================================ medicoes
def _t(x):
    x = np.asarray(x, float)
    if len(x) < 2 or x.std(ddof=1) == 0:
        return float('nan')
    return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x))))


def mede_regra(x, m, rng, n_perm=N_PERM):
    """Uma regra num conjunto ja resolvido (x = sinais aceitos)."""
    pts = x['pts'].to_numpy(float)
    m = np.asarray(m, bool)
    base = float(pts.mean())
    r = dict(n=int(m.sum()), frac=float(m.mean() * 100), base=base)
    if m.sum() < 20 or (~m).sum() < 20:
        r.update(ev=None)
        return r
    ev_d = float(pts[m].mean()); ev_f = float(pts[~m].mean())
    obs = ev_d - base
    nulo = np.array([pts[rng.permutation(m)].mean() - base for _ in range(n_perm)])
    ter = x['terco'].to_numpy(); bl = PR.bloco(x['data']); ld = x['lado'].to_numpy()
    r.update(
        ev=ev_d, ev_fora=ev_f, ganho=obs, t=_t(pts[m]),
        wr=float((pts[m] > 0).mean() * 100),
        p_maior=float((nulo >= obs).mean()), p_menor=float((nulo <= obs).mean()),
        p_bi=float((np.abs(nulo) >= abs(obs)).mean()),
        tercos=[float(pts[m & (ter == k)].mean()) if (m & (ter == k)).any() else None
                for k in ('T1', 'T2', 'T3')],
        tercos_base=[float(pts[ter == k].mean()) for k in ('T1', 'T2', 'T3')],
        blocos={k: (float(pts[m & (bl == k)].mean()) if (m & (bl == k)).any() else None)
                for k in ('antes', 'original', 'depois')},
        blocos_base={k: (float(pts[bl == k].mean()) if (bl == k).any() else None)
                     for k in ('antes', 'original', 'depois')},
        n_blocos={k: int((m & (bl == k)).sum()) for k in ('antes', 'original', 'depois')},
        compra=float(pts[m & (ld > 0)].mean()) if (m & (ld > 0)).any() else None,
        venda=float(pts[m & (ld < 0)].mean()) if (m & (ld < 0)).any() else None,
        compra_base=float(pts[ld > 0].mean()), venda_base=float(pts[ld < 0].mean()),
    )
    return r


def busca(x, rng=None, subset=None, regras=None):
    """Melhor candidato entre as 16 regras e seus complementos, pelo ganho em t.

    Criterio: t da diferenca entre o EV dentro e o EV do conjunto (erro padrao
    do subconjunto). Com rng, os RESULTADOS sao embaralhados antes -- o que
    preserva o formato de todas as regras e destroi a ligacao com o desfecho.
    """
    pts = x['pts'].to_numpy(float)
    if rng is not None:
        pts = rng.permutation(pts)
    idx = np.ones(len(x), bool) if subset is None else np.asarray(subset, bool)
    base = pts[idx].mean()
    melhor = (-9e9, None)
    for k in (regras or REGRAS):
        mk = x[k].to_numpy(bool)
        for sent, m in ((+1, mk), (-1, ~mk)):
            mm = m & idx
            if mm.sum() < max(30, 0.15 * idx.sum()) or (idx & ~m).sum() < 30:
                continue
            s = pts[mm].std(ddof=1)
            if s == 0:
                continue
            t = (pts[mm].mean() - base) / (s / np.sqrt(mm.sum()))
            if t > melhor[0]:
                melhor = (t, (k, sent))
    return melhor


def poder(x, fracs=(0.5, 0.33)):
    pts = x['pts'].to_numpy(float); s = pts.std(ddof=1)
    return [dict(mantem=f, n=int(len(pts) * f),
                 min_ganho=float(2.8 * s * np.sqrt(1 / (len(pts) * f) - 1 / len(pts)))) for f in fracs]


def quintis(x, col):
    v = x[col].to_numpy(float)
    ok = np.isfinite(v)
    lim = np.nanpercentile(v, [20, 40, 60, 80])
    q = np.digitize(v, lim)
    pts = x['pts'].to_numpy(float); ter = x['terco'].to_numpy()
    out = []
    for k in range(5):
        m = ok & (q == k)
        out.append(dict(faixa=['Q1 (menor)', 'Q2', 'Q3', 'Q4', 'Q5 (maior)'][k], n=int(m.sum()),
                        ev=float(pts[m].mean()) if m.any() else None,
                        tercos=[float(pts[m & (ter == z)].mean()) if (m & (ter == z)).any() else None
                                for z in ('T1', 'T2', 'T3')]))
    return dict(limites=[float(z) for z in lim], faixas=out)


def compacta(c, d):
    """Trades da carteira em lista de listas (o html fica menor)."""
    mot = {'alvo': 0, 'stop': 1, 'stop_zero': 2, 'timeout': 3, 'fim_dia': 4}
    return [[int(r.i), int(r.i_ent), int(r.i_sai), int(r.lado), float(r.preco_ent),
             float(r.preco_sai), float(r.pts), float(r.mfe), float(r.mae), mot.get(r.motivo, 3),
             int(r.n_fav), round(float(r.pav_outro_pct), 1), f'{r.data:%d/%m/%Y %H:%M}']
            for r in c.itertuples()]


def stats_cart(c, d):
    st = E.estatisticas(c)
    if not len(c):
        return st
    ini = d['data'].iat[0]; fim = d['data'].iat[-1]
    st['xs'] = [round(v, 5) for v in ((c['data_sai'] - ini) / (fim - ini)).tolist()]
    st['dt'] = [f'{x:%d/%m/%y}' for x in c['data_sai']]
    st['mc'] = P.monte_carlo(c['pts'].to_numpy())
    st['pts'] = c['pts'].tolist(); st['mfe'] = c['mfe'].tolist()
    st['mae'] = c['mae'].tolist(); st['dur_s'] = c['dur_s'].tolist()
    st['barras'] = c['barras'].tolist()
    return st


# ==================================================================== main
def main():
    d = E.indicadores(E.carrega())
    dias = sorted(d['dia'].unique())
    osc = osciladores(d)
    u = universo(d)
    u = atributos(u, d, osc)
    limites = u.attrs['limites']
    u = u[u['osc_ok']].reset_index(drop=True)

    p('=' * 74)
    p('MACD, ESTOCASTICO LENTO E IFR COMO FILTRO DO HULL + PAVIOS')
    p('=' * 74)
    p(f"base: {len(d)} barras, {len(dias)} pregoes; sinais Hull + 2-4: {len(u)}; "
      f"Hull + pavios: {int(u['cand'].sum())}")
    p(f"MACD {MACD_P}  estocastico lento {ESTOC_P}  IFR {IFR_P}")
    dc = np.abs(np.diff(d['c'].to_numpy()))
    mesmo = d['dia'].to_numpy()[1:] == d['dia'].to_numpy()[:-1]
    p(f"fechamento anda exatamente 100 pts em {np.mean(dc[mesmo] == 100) * 100:.2f}% das barras do mesmo "
      f"pregao -> o IFR e a proporcao suavizada de candles de alta")

    res = {}
    for gn, gg in HC.GESTOES.items():
        t = E.executa(d, u, 'fecha', gg)
        t, c1, c2 = P.marca_tercos(t, dias)
        res[gn] = t

    S = dict(parametros=dict(macd=MACD_P, estoc=ESTOC_P, ifr=IFR_P), regras=REGRAS, conj=CONJ,
             limites=limites, classicas=list(CLASSICAS),
             continuas=CONTINUAS, rot_gestao=HC.ROT_GESTAO, rot_bloco=PR.ROT_BLOCO,
             base=dict(barras=len(d), dias=len(dias), ini=f"{d['data'].iat[0]:%d/%m/%Y}",
                       fim=f"{d['data'].iat[-1]:%d/%m/%Y}", c1=c1, c2=c2, n_h=int(len(u)),
                       n_cand=int(u['cand'].sum())))

    # ------------------------------------------------ 1. frequencia das regras
    freq = {}
    for cj in CONJ:
        x = u if cj == 'h' else u[u['cand']]
        freq[cj] = {k: float(x[k].mean() * 100) for k in REGRAS}
    S['freq'] = freq
    p('\n--- 1. quanto de cada conjunto a regra deixa passar (%) ---')
    for cj in CONJ:
        p(f"  {cj:5s} " + '  '.join(f"{k} {v:4.0f}" for k, v in freq[cj].items()))
    cor = u[list(REGRAS)].astype(float).corr()
    S['correl'] = {a: {b: float(cor.loc[a, b]) for b in cor.columns} for a in cor.index}
    p(f"  limites por quantil: " + '  '.join(f"{k} {v:.2f}" for k, v in limites.items()))
    p(f"  correlacoes: M1 x I1 {cor.loc['M1', 'I1']:.2f}  M5 x E6 {cor.loc['M5', 'E6']:.2f}  "
      f"E5 x I4 {cor.loc['E5', 'I4']:.2f}  I5 x M1 {cor.loc['I5', 'M1']:.2f}")

    # ------------------------------------------------ 2. cada regra
    rng = np.random.default_rng(20260915)
    regras = {}
    for gn in HC.GESTOES:
        t = res[gn]
        for cj in CONJ:
            x = t[t['aceito'] & (t['cand'] if cj == 'cand' else True)].reset_index(drop=True)
            for k in REGRAS:
                regras[f'{cj}|{gn}|{k}'] = mede_regra(x, x[k], rng)
                regras[f'{cj}|{gn}|{k}']['sorteio_pct'] = P.sorteio(
                    x.assign(aceito=True), x[k])['percentil'] if 20 <= x[k].sum() < len(x) else None
    S['regras_res'] = regras
    for cj in CONJ:
        p(f"\n--- 2. {CONJ[cj]}  (fechamento, 1:3 com parcial) ---")
        b = regras[f'{cj}|parcial|M1']['base']
        p(f"  base: EV {b:+.1f}")
        for k, (fam, rot) in REGRAS.items():
            r = regras[f'{cj}|parcial|{k}']
            if r['ev'] is None:
                p(f"  {k} {rot:42s} n={r['n']}  -")
                continue
            p(f"  {k} {rot:42s} n={r['n']:5d} ({r['frac']:3.0f}%)  dentro {r['ev']:+6.1f}  fora {r['ev_fora']:+6.1f}  "
              f"ganho {r['ganho']:+5.1f}  p {r['p_bi']:.3f}  tercos " +
              '/'.join(f"{v:+.0f}" for v in r['tercos']) +
              f"  antes {r['blocos']['antes']:+.1f} (base {r['blocos_base']['antes']:+.1f})  "
              f"C {r['compra']:+.1f} V {r['venda']:+.1f}  pct {r['sorteio_pct']:.0f}")
        p('  ganho nas 4 gestoes: ' + '  '.join(
            f"{k} " + '/'.join(f"{regras[f'{cj}|{g}|{k}'].get('ganho') or 0:+.1f}" for g in HC.GESTOES)
            for k in REGRAS if regras[f'{cj}|parcial|{k}']['ev'] is not None))

    # ------------------------------------------------ 3. busca contra ruido
    p('\n--- 3. a busca: 16 regras x 2 sentidos, contra resultados embaralhados ---')
    buscas = {}
    for gn in HC.GESTOES:
        t = res[gn]
        for cj in CONJ:
            x = t[t['aceito'] & (t['cand'] if cj == 'cand' else True)].reset_index(drop=True)
            bt, bk = busca(x)
            rr = np.random.default_rng(7)
            nulo = np.array([busca(x, rr)[0] for _ in range(500)])
            nulo = nulo[nulo > -9e8]
            # escolha fora: no bloco antes, medida no resto; em T1+T2, medida em T3
            bl = PR.bloco(x['data'])
            fora = {}
            for rot, dentro, teste in (('antes -> original+depois', bl == 'antes', bl != 'antes'),
                                       ('T1+T2 -> T3', x['terco'].to_numpy() != 'T3',
                                        x['terco'].to_numpy() == 'T3')):
                _, kk = busca(x, subset=dentro)
                if kk is None:
                    fora[rot] = None
                    continue
                m = x[kk[0]].to_numpy(bool)
                m = m if kk[1] > 0 else ~m
                pts = x['pts'].to_numpy(float)
                fora[rot] = dict(regra=kk[0], sentido=kk[1],
                                 ev_teste=float(pts[m & teste].mean()), n_teste=int((m & teste).sum()),
                                 ev_teste_base=float(pts[teste].mean()), n_teste_base=int(teste.sum()),
                                 ev_escolha=float(pts[m & dentro].mean()),
                                 ev_escolha_base=float(pts[dentro].mean()))
            buscas[f'{cj}|{gn}'] = dict(regra=bk[0], sentido=bk[1], t=float(bt),
                                        ruido_mediana=float(np.median(nulo)),
                                        ruido_p95=float(np.quantile(nulo, .95)),
                                        p_valor=float((nulo >= bt).mean()), fora=fora,
                                        poder=poder(x))
            b = buscas[f'{cj}|{gn}']
            p(f"  {cj:5s} {HC.ROT_GESTAO[gn]:16s} melhor {b['regra']}{'' if b['sentido'] > 0 else ' (complemento)'} "
              f"t={b['t']:+.2f}  ruido med {b['ruido_mediana']:+.2f} p95 {b['ruido_p95']:+.2f}  p={b['p_valor']:.3f}")
            for rot, f_ in fora.items():
                if f_:
                    p(f"        escolha {rot:26s}: {f_['regra']}{'' if f_['sentido'] > 0 else '~'} "
                      f"teste {f_['ev_teste']:+.1f} (n={f_['n_teste']}) x sem filtro {f_['ev_teste_base']:+.1f}")
            p(f"        poder: filtro que mantem 50% so aparece acima de {b['poder'][0]['min_ganho']:+.1f} pts")
    S['busca'] = buscas

    # ------------------------------------------------ 4. quintis das leituras
    qt = {}
    for cj in CONJ:
        x = res['parcial']
        x = x[x['aceito'] & (x['cand'] if cj == 'cand' else True)].reset_index(drop=True)
        for col in CONTINUAS:
            qt[f'{cj}|{col}'] = quintis(x, col)
    S['quintis'] = qt
    p('\n--- 4. quintis das leituras (Hull + pavios, 1:3 com parcial) ---')
    for col, rot in CONTINUAS.items():
        q = qt[f'cand|{col}']
        p(f"  {rot:34s} lim " + ' '.join(f"{v:.2f}" for v in q['limites']) + ' | ' +
          '  '.join(f"{f['ev']:+5.1f}" for f in q['faixas']))

    # ------------------------------------------------ 5. vizinhanca de parametros
    p('\n--- 5. vizinhanca de parametros (ganho no Hull + pavios, 1:3 com parcial) ---')
    viz = {}
    tp = res['parcial']
    base_cols = ['i', 'lado', 'pts', 'aceito', 'cand', 'n_fav', 'data', 'terco']
    for fam, lista in VIZ.items():
        for par in lista:
            kw = dict(mp=par) if fam == 'macd' else (dict(ep=par) if fam == 'estoc' else dict(ip=par))
            o2 = osciladores(d, **kw)
            x2 = atributos(tp[base_cols].assign(pav_outro_pct=0), d, o2)
            x2 = atributos(tp[base_cols].assign(pav_outro_pct=0), d, o2, None)
            x2 = x2[x2['aceito'] & x2['cand'] & x2['osc_ok']].reset_index(drop=True)
            pts = x2['pts'].to_numpy(float)
            for k in REGRAS:
                if REGRAS[k][0][0] != {'macd': 'M', 'estoc': 'E', 'ifr': 'I'}[fam]:
                    continue
                m = x2[k].to_numpy(bool)
                viz[f'{k}|{par}'] = dict(regra=k, par=str(par), n=int(m.sum()),
                                         ganho=float(pts[m].mean() - pts.mean()) if m.sum() >= 20 else None,
                                         padrao=(par == {'macd': MACD_P, 'estoc': ESTOC_P, 'ifr': IFR_P}[fam]))
        p('  ' + fam + ': ' + '  '.join(
            f"{v['regra']}@{v['par']} {v['ganho']:+.1f}" for v in viz.values()
            if v['regra'][0] == {'macd': 'M', 'estoc': 'E', 'ifr': 'I'}[fam] and v['ganho'] is not None))
    S['vizinhanca'] = viz

    # ------------------------------------------------ 6. carteiras
    p('\n--- 6. carteira, uma posicao por vez ---')
    cart = {}; trades = {}
    for gn in HC.GESTOES:
        t = res[gn]
        for cj in CONJ:
            x = t[t['aceito'] & (t['cand'] if cj == 'cand' else True)]
            for k in ['base'] + list(REGRAS):
                sel = x if k == 'base' else x[x[k]]
                c = E.carteira(sel)
                st = stats_cart(c, d)
                if gn != 'parcial':
                    for campo in ('pts', 'mfe', 'mae', 'dur_s', 'barras'):
                        st.pop(campo, None)
                st['blocos'] = PR.por_bloco(c)
                cart[f'{cj}|{gn}|{k}'] = st
                if gn in ('parcial', 'puro'):
                    trades[f'{cj}|{gn}|{k}'] = compacta(c, d)
        for cj in CONJ:
            b = cart[f'{cj}|{gn}|base']
            melhor = max(REGRAS, key=lambda k: cart[f'{cj}|{gn}|{k}'].get('exp_pts', -99))
            m = cart[f'{cj}|{gn}|{melhor}']
            p(f"  {cj:5s} {HC.ROT_GESTAO[gn]:16s} base {b['trades']:5d} tr {b['lucro_liq']:+8.0f} FL {b['fator_lucro']:.2f} "
              f"DD {b['dd_max']:5.0f} | maior EV: {melhor} {m['trades']:5d} tr {m['exp_pts']:+5.1f}/tr "
              f"{m['lucro_liq']:+8.0f} FL {m['fator_lucro']:.2f} DD {m['dd_max']:5.0f}")
    S['carteira'] = cart; S['trades'] = trades

    # ------------------------------------------------ candles com os osciladores
    rd = lambda arr, c=1: [None if not np.isfinite(v) else round(float(v), c) for v in arr]
    S['candles'] = dict(o=d['o'].tolist(), h=d['h'].tolist(), l=d['l'].tolist(), c=d['c'].tolist(),
                        hma=rd(d['hma']), macd=rd(osc['macd']), sinal=rd(osc['sinal']),
                        hist=rd(osc['hist']), k=rd(osc['k']), d=rd(osc['d']), ifr=rd(osc['ifr']),
                        dt=d['data'].dt.strftime('%d/%m %H:%M').tolist())

    with open(os.path.join(SAIDA, 'osciladores.json'), 'w', encoding='utf-8') as f:
        json.dump(P._lim(S), f, ensure_ascii=False, separators=(',', ':'))
    with open(os.path.join(SAIDA, 'osciladores_console.txt'), 'w', encoding='utf-8') as f:
        f.write(_buf.getvalue())
    p('\ngravado: saida/osciladores.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
