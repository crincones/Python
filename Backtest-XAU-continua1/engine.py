# -*- coding: utf-8 -*-
"""
Motor do backtest da estrategia "leque de EMAs 21/42/72" em XAUUSD, grafico
de 521 ticks.

Regra (ESTRATEGIA.md), traduzida para codigo:

  1. LEQUE      as tres EMAs exponenciais do fechamento (21, 42, 72) estao
                ordenadas -- 21>42>72 (alta) ou 21<42<72 (baixa). A largura
                do leque |EMA21-EMA72| mede o quanto ele esta aberto; leque
                estreito = medias "emboladas" = consolidacao/reversao.
  2. AFASTAMENTO  nas ultimas `afast_janela` barras o preco se descolou do
                leque no sentido da tendencia por pelo menos `afast_min`
                ticks (a barra inteira ficou alem da EMA21).
  3. VOLTA      o preco retorna ao leque: a barra toca a EMA21 pelo lado de
                dentro.
  4. PULLBACK   a volta e feita por uma sequencia de `pull_min`..`pull_max`
                candles consecutivos da MESMA cor, contraria a tendencia.
  5. GATILHO    logo depois aparece um candle CONTRARIO ao pullback (ou seja,
                a favor da tendencia), tocando o leque, com range de no
                maximo `range_max` ticks.
  6. ENTRADA    ordem limitada no MEIO do range do candle de gatilho, valida
                por UMA barra. Se a barra seguinte nao toca o preco, aborta.
  7. GESTAO     stop de `stop_ticks`; parcial de 50% em `parcial_ticks`, que
                leva o stop do restante para o breakeven; saida final do
                restante em `alvo_ticks`.

Tudo e medido em TICKS de 0.01 dolar. 300 ticks = 3.00 dolares = 1R.

Unico ponto onde OHLC nao decide sozinho: quando a mesma barra toca alvo e
stop. Isso e resolvido por `ordem_intrabar`:
    'pessimista'  o stop acontece primeiro (padrao de todos os numeros
                  publicados nos relatorios)
    'otimista'    o alvo acontece primeiro
Rodar as duas da um intervalo honesto para cada estatistica.
"""
import os
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd

TICK = 0.01
BASE = os.path.dirname(os.path.abspath(__file__))
ARQUIVO = os.path.join(BASE, 'XAUUSD-521T',
                       'XAUUSD_521_TK_M1_202605051927_202609021325.csv')


# --------------------------------------------------------------------------
# configuracao
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Config:
    nome: str = 'base'
    rotulo: str = 'regra literal'

    # medias
    ema_curta: int = 21
    ema_media: int = 42
    ema_longa: int = 72

    # gatilho
    pull_min: int = 2
    pull_max: int = 3
    afast_min: float = 0.0      # ticks de descolamento exigidos
    afast_janela: int = 12      # barras olhadas para tras
    leque_min: float = 0.0      # ticks de |EMA21-EMA72| exigidos
    leque_max: float = 1e9      # teto do leque (leque exagerado = climax)
    range_max: float = 1e9      # ticks: teto do range do candle de gatilho
    range_min: float = 0.0      # ticks: piso do range do candle de gatilho
    exige_dentro: bool = False  # a barra nao pode furar a EMA72
    fecha_alem: bool = False    # o gatilho fecha alem da EMA21 (reconquista)
    inclin_min: float = 0.0     # ticks: avanco da EMA21 em `inclin_jan` barras
    inclin_jan: int = 10
    corpo_min: float = 0.0      # fracao minima corpo/range do gatilho
    horas: tuple = ()           # () = todas; senao horas permitidas (do CSV)
    lados: tuple = ('long', 'short')
    inverter: bool = False      # controle: opera o lado OPOSTO ao do gatilho
    entrada: str = 'meio'       # 'meio' = limitada no meio do range do gatilho
                                # 'fecha' = a mercado no fechamento do gatilho

    # gestao
    stop_ticks: float = 300.0
    parcial_ticks: float = 300.0
    parcial_frac: float = 0.5
    alvo_ticks: float = 900.0
    max_barras: int = 0         # 0 = sem stop por tempo
    custo_ticks: float = 0.0    # custo total ida+volta, em ticks de 1 lote

    ordem_intrabar: str = 'pessimista'


# --------------------------------------------------------------------------
# dados
# --------------------------------------------------------------------------
def carregar(caminho=ARQUIVO):
    """Le o CSV exportado do MetaTrader (tab-separated, cabecalho <CAMPO>)."""
    df = pd.read_csv(caminho, sep='\t')
    df.columns = [c.strip('<>').lower() for c in df.columns]
    df['dt'] = pd.to_datetime(df['date'] + ' ' + df['time'],
                              format='%Y.%m.%d %H:%M:%S')
    df = df.sort_values('dt').reset_index(drop=True)
    return df[['dt', 'open', 'high', 'low', 'close', 'tickvol', 'vol']]


def _runlen(mask):
    """Comprimento da sequencia de True terminando em cada posicao."""
    m = np.asarray(mask, dtype=bool)
    r = np.zeros(len(m), dtype=np.int64)
    acc = 0
    for i in range(len(m)):
        acc = acc + 1 if m[i] else 0
        r[i] = acc
    return r


def indicadores(df, cfg=Config()):
    """Acrescenta EMAs, leque, cor, sequencia de cor e distancias."""
    d = df.copy()
    c = d['close']
    d['ema1'] = c.ewm(span=cfg.ema_curta, adjust=False).mean()
    d['ema2'] = c.ewm(span=cfg.ema_media, adjust=False).mean()
    d['ema3'] = c.ewm(span=cfg.ema_longa, adjust=False).mean()

    d['up'] = (d.ema1 > d.ema2) & (d.ema2 > d.ema3)
    d['dn'] = (d.ema1 < d.ema2) & (d.ema2 < d.ema3)
    d['leque'] = (d.ema1 - d.ema3).abs() / TICK
    d['range'] = (d.high - d.low) / TICK
    d['corpo'] = (d.close - d.open).abs() / TICK

    d['alta'] = d.close > d.open
    d['baixa'] = d.close < d.open
    d['run_alta'] = _runlen(d.alta.to_numpy())
    d['run_baixa'] = _runlen(d.baixa.to_numpy())

    # descolamento: a barra INTEIRA alem da EMA21, no sentido da tendencia
    d['dist_up'] = (d.low - d.ema1) / TICK
    d['dist_dn'] = (d.ema1 - d.high) / TICK
    d['hora'] = d.dt.dt.hour
    d['data'] = d.dt.dt.date
    return d


# --------------------------------------------------------------------------
# gatilhos
# --------------------------------------------------------------------------
def sinais(d, cfg):
    """Marca as barras de gatilho. Devolve dois arrays booleanos (long, short)."""
    n = len(d)
    afast_up = d.dist_up.rolling(cfg.afast_janela, min_periods=1).max().to_numpy()
    afast_dn = d.dist_dn.rolling(cfg.afast_janela, min_periods=1).max().to_numpy()

    run_b = np.roll(d.run_baixa.to_numpy(), 1); run_b[0] = 0
    run_a = np.roll(d.run_alta.to_numpy(), 1); run_a[0] = 0

    lq = d.leque.to_numpy()
    rg = d['range'].to_numpy()
    leque_ok = (lq >= cfg.leque_min) & (lq <= cfg.leque_max)
    range_ok = (rg <= cfg.range_max) & (rg >= cfg.range_min)
    hora_ok = (d.hora.isin(cfg.horas).to_numpy() if cfg.horas
               else np.ones(n, dtype=bool))
    corpo_ok = (d.corpo.to_numpy() / np.maximum(rg, 1e-9)) >= cfg.corpo_min
    base = leque_ok & range_ok & hora_ok & corpo_ok

    lo, hi = d.low.to_numpy(), d.high.to_numpy()
    cl = d.close.to_numpy()
    e1, e3 = d.ema1.to_numpy(), d.ema3.to_numpy()

    toca_up = lo <= e1                      # voltou ao leque por cima
    toca_dn = hi >= e1
    if cfg.exige_dentro:
        toca_up = toca_up & (lo >= e3)      # sem furar o leque inteiro
        toca_dn = toca_dn & (hi <= e3)
    if cfg.fecha_alem:
        toca_up = toca_up & (cl > e1)       # reconquistou a EMA21 no fecha
        toca_dn = toca_dn & (cl < e1)

    if cfg.inclin_min > 0:
        av = (e1 - np.roll(e1, cfg.inclin_jan)) / TICK
        av[:cfg.inclin_jan] = 0.0
        inc_up = av >= cfg.inclin_min
        inc_dn = -av >= cfg.inclin_min
    else:
        inc_up = inc_dn = np.ones(n, dtype=bool)

    sl = (d.up.to_numpy() & d.alta.to_numpy() & toca_up & base & inc_up &
          (run_b >= cfg.pull_min) & (run_b <= cfg.pull_max) &
          (afast_up >= cfg.afast_min))
    ss = (d.dn.to_numpy() & d.baixa.to_numpy() & toca_dn & base & inc_dn &
          (run_a >= cfg.pull_min) & (run_a <= cfg.pull_max) &
          (afast_dn >= cfg.afast_min))

    if 'long' not in cfg.lados:
        sl = np.zeros(n, dtype=bool)
    if 'short' not in cfg.lados:
        ss = np.zeros(n, dtype=bool)

    # a ultima barra nao tem barra seguinte para ativar a ordem
    sl[-1] = False
    ss[-1] = False
    return sl, ss


# --------------------------------------------------------------------------
# simulacao
# --------------------------------------------------------------------------
def _percorre(sinal, ent, h, l, c, cfg, i0, n):
    """Roda a gestao a partir da barra de entrada i0."""
    stop = ent - sinal * cfg.stop_ticks * TICK
    parc = ent + sinal * cfg.parcial_ticks * TICK
    alvo = ent + sinal * cfg.alvo_ticks * TICK

    pess = cfg.ordem_intrabar == 'pessimista'
    frac = cfg.parcial_frac
    feito_parcial = False
    res = 0.0                      # resultado acumulado em ticks (1 lote)
    lim = n if not cfg.max_barras else min(n, i0 + cfg.max_barras)

    for i in range(i0, lim):
        hi, lo = h[i], l[i]
        bate_stop = (lo <= stop) if sinal > 0 else (hi >= stop)
        bate_parc = (hi >= parc) if sinal > 0 else (lo <= parc)
        bate_alvo = (hi >= alvo) if sinal > 0 else (lo <= alvo)

        if not feito_parcial:
            if bate_stop and (pess or not bate_parc):
                return dict(saida_i=i, motivo='stop', ticks=-cfg.stop_ticks,
                            parcial=False, barras=i - i0 + 1)
            if bate_parc:
                res += frac * cfg.parcial_ticks
                feito_parcial = True
                stop = ent                     # breakeven
                bate_stop = (lo <= stop) if sinal > 0 else (hi >= stop)
                if bate_alvo and (not pess or not bate_stop):
                    res += (1 - frac) * cfg.alvo_ticks
                    return dict(saida_i=i, motivo='alvo', ticks=res,
                                parcial=True, barras=i - i0 + 1)
                if bate_stop:
                    return dict(saida_i=i, motivo='breakeven', ticks=res,
                                parcial=True, barras=i - i0 + 1)
                continue
            if bate_stop:                      # otimista, e o alvo nao bateu
                return dict(saida_i=i, motivo='stop', ticks=-cfg.stop_ticks,
                            parcial=False, barras=i - i0 + 1)
        else:
            if bate_stop and (pess or not bate_alvo):
                return dict(saida_i=i, motivo='breakeven', ticks=res,
                            parcial=True, barras=i - i0 + 1)
            if bate_alvo:
                res += (1 - frac) * cfg.alvo_ticks
                return dict(saida_i=i, motivo='alvo', ticks=res,
                            parcial=True, barras=i - i0 + 1)
            if bate_stop:
                return dict(saida_i=i, motivo='breakeven', ticks=res,
                            parcial=True, barras=i - i0 + 1)

    # acabou o historico (ou estourou o stop por tempo) com posicao aberta
    i = lim - 1
    aberto = (1 - frac) if feito_parcial else 1.0
    res += aberto * sinal * (c[i] - ent) / TICK
    return dict(saida_i=i, motivo='tempo', ticks=res,
                parcial=feito_parcial, barras=i - i0 + 1)


def rodar(d, cfg):
    """Executa a estrategia. Devolve DataFrame de sinais/operacoes."""
    sl, ss = sinais(d, cfg)
    o = d.open.to_numpy(); h = d.high.to_numpy()
    l = d.low.to_numpy(); c = d.close.to_numpy()
    n = len(d)
    idx = np.where(sl | ss)[0]
    dts = d.dt.to_numpy()
    horas = d.hora.to_numpy()
    lqs = d.leque.to_numpy()
    rgs = d['range'].to_numpy()

    ops = []
    ocupado_ate = -1
    for i in idx:
        if i <= ocupado_ate:
            continue                          # uma operacao por vez
        sinal = 1 if sl[i] else -1
        if cfg.inverter:
            sinal = -sinal
        meio = (h[i] + l[i]) / 2
        j = i + 1
        if cfg.entrada == 'fecha':
            ativou, ent = True, c[i]
        elif sinal > 0:
            ativou = l[j] <= meio
            ent = min(meio, o[j])
        else:
            ativou = h[j] >= meio
            ent = max(meio, o[j])

        comum = dict(sinal_i=int(i), dt=dts[i],
                     lado='long' if sinal > 0 else 'short',
                     preco_ordem=float(meio), hora=int(horas[i]),
                     leque=float(lqs[i]), range_gatilho=float(rgs[i]))
        if not ativou:
            ops.append(dict(comum, ativou=False, entrada=np.nan, saida_i=-1,
                            motivo='abortada', ticks=0.0, ticks_bruto=0.0,
                            parcial=False, barras=0))
            continue
        r = _percorre(sinal, ent, h, l, c, cfg, j, n)
        ops.append(dict(comum, ativou=True, entrada=float(ent),
                        saida_i=int(r['saida_i']), motivo=r['motivo'],
                        ticks=r['ticks'] - cfg.custo_ticks,
                        ticks_bruto=r['ticks'], parcial=bool(r['parcial']),
                        barras=int(r['barras'])))
        ocupado_ate = r['saida_i']

    t = pd.DataFrame(ops)
    if len(t):
        t['R'] = t.ticks / cfg.stop_ticks
        t['usd'] = t.ticks * TICK
        t['data'] = pd.to_datetime(t.dt).dt.date
    return t


# --------------------------------------------------------------------------
# estatisticas
# --------------------------------------------------------------------------
def _dd(curva):
    if not len(curva):
        return 0.0
    pico = np.maximum.accumulate(curva)
    return float((curva - pico).min())


def estatisticas(t, cfg):
    """Resumo de uma corrida. Tudo em ticks/R; usd = ticks * 0.01 por lote."""
    vazio = dict(sinais=0, abortadas=0, taxa_ativacao=0.0, operacoes=0)
    if not len(t):
        return vazio
    ativ = t[t.ativou].copy()
    n = len(ativ)
    if n == 0:
        return dict(vazio, sinais=int(len(t)), abortadas=int(len(t)))

    g = ativ[ativ.ticks > 0]; p = ativ[ativ.ticks < 0]; z = ativ[ativ.ticks == 0]
    soma_g = float(g.ticks.sum()); soma_p = float(-p.ticks.sum())
    curva = ativ.ticks.cumsum().to_numpy()
    R = ativ.R.to_numpy()

    por_dia = ativ.groupby('data').ticks.sum()
    exp = float(ativ.ticks.mean())
    dp = float(ativ.ticks.std(ddof=1)) if n > 1 else 0.0
    return dict(
        sinais=int(len(t)),
        abortadas=int((~t.ativou).sum()),
        taxa_ativacao=float(t.ativou.mean()),
        operacoes=n,
        vitorias=int(len(g)), perdas=int(len(p)), neutras=int(len(z)),
        acerto=len(g) / n,
        ticks_total=float(ativ.ticks.sum()),
        usd_total=float(ativ.ticks.sum() * TICK),
        R_total=float(R.sum()),
        expectativa_ticks=exp,
        expectativa_R=float(R.mean()),
        expectativa_usd=exp * TICK,
        desvio_ticks=dp,
        ganho_medio=float(g.ticks.mean()) if len(g) else 0.0,
        perda_media=float(p.ticks.mean()) if len(p) else 0.0,
        fator_lucro=(soma_g / soma_p) if soma_p > 0 else float('inf'),
        payoff=(float(g.ticks.mean()) / abs(float(p.ticks.mean()))
                if len(g) and len(p) else 0.0),
        drawdown_ticks=_dd(curva),
        drawdown_R=_dd(curva) / cfg.stop_ticks,
        sqn=(exp / dp * np.sqrt(n)) if dp > 0 else 0.0,
        motivos={str(k): int(v) for k, v in ativ.motivo.value_counts().items()},
        parciais=int(ativ.parcial.sum()),
        barras_media=float(ativ.barras.mean()),
        dias=int(ativ.data.nunique()),
        ops_por_dia=n / max(1, ativ.data.nunique()),
        melhor_dia=float(por_dia.max()), pior_dia=float(por_dia.min()),
        dias_positivos=int((por_dia > 0).sum()),
        dias_negativos=int((por_dia < 0).sum()),
        long=int((ativ.lado == 'long').sum()),
        short=int((ativ.lado == 'short').sum()),
        ticks_long=float(ativ[ativ.lado == 'long'].ticks.sum()),
        ticks_short=float(ativ[ativ.lado == 'short'].ticks.sum()),
    )


def resumo_cfg(cfg):
    d = asdict(cfg)
    d['horas'] = list(cfg.horas)
    d['lados'] = list(cfg.lados)
    return d
