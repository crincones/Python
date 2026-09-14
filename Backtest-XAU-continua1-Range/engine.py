# -*- coding: utf-8 -*-
"""
Motor do backtest do gatilho "Esforco x Resultado" em XAUUSD, grafico de RANGE
de 388 ticks.

O gatilho e o indicador MQL5

    MQL5/Indicators/Triggers/Trigger_EsforcoResultado_Range.mq5

portado para Python neste arquivo. A funcao `esforco_resultado` e transcricao
linha a linha do laco de `OnCalculate`, com os mesmos nomes de variavel, para
que a conferencia entre os dois seja possivel a olho.

    res  = (close - open) em ticks        RESULTADO liquido da barra
    esf  = tickvol + vol                  ESFORCO total (agressao dos dois lados)
    dlt  = tickvol - vol                  agressao liquida
    qual = (dlt * dir) / esf              fracao do esforco A FAVOR da barra

`tickvol` e a agressao COMPRADORA e `vol` a VENDEDORA -- convencao [R6] do
simbolo sintetico gerado pelo Range_Claude_v1.mq5. Num simbolo comum esses
campos significam outra coisa e o estudo inteiro perde o sentido; por isso
`conferir_premissa` roda antes de tudo.

Sinais devolvidos em `d.sinal`:
    +1 absorcao a favor da alta      -1 absorcao a favor da baixa
    +2 divergencia resolvida na alta -2 divergencia resolvida na baixa
     0 nenhum

Tudo e medido em TICKS de 0.01 dolar. O range da barra e 388 ticks = 3.88 USD,
e e a unidade natural de risco deste grafico.

Unico ponto onde OHLC nao decide sozinho: quando a mesma barra toca alvo e stop.
Isso e resolvido por `ordem_intrabar`:
    'pessimista'  o stop acontece primeiro (padrao de todos os numeros
                  publicados nos relatorios)
    'otimista'    o alvo acontece primeiro
"""
import os
from dataclasses import dataclass, asdict, replace

import numpy as np
import pandas as pd

TICK = 0.01
RANGE_NOMINAL = 388.0          # ticks; o range do simbolo, e a unidade de risco
BASE = os.path.dirname(os.path.abspath(__file__))
ARQUIVO = os.path.join(BASE, 'XAUUSD-388N',
                       'XAUUSD_388_N_M1_202605110101_202609042330.csv')


# --------------------------------------------------------------------------
# configuracao do INDICADOR (os inputs do .mq5, com os mesmos padroes)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Ind:
    periodo_base: int = 60          # InpPeriodoBase
    fator_completa: float = 0.90    # InpFatorCompleta
    fator_res: float = 0.70         # InpFatorRes
    fator_qual: float = 0.50        # InpFatorQual
    usar_divergen: bool = True      # InpUsarDivergen
    fator_corpo: float = 0.80       # InpFatorCorpo
    lim_desq: float = 0.05          # InpLimDesq
    prioridade_azul: bool = True    # InpPrioridadeAzul


# --------------------------------------------------------------------------
# configuracao da ESTRATEGIA (o que se faz com o sinal)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Config:
    nome: str = 'base'
    rotulo: str = 'regra literal'
    ind: Ind = Ind()

    # quais sinais operar: 1 = absorcao, 2 = divergencia
    tipos: tuple = (1, 2)
    lados: tuple = ('long', 'short')
    inverter: bool = False          # controle: opera o lado OPOSTO ao do sinal

    # filtros de contexto medidos NA BARRA DE SINAL
    horas: tuple = ()               # () = todas
    efic_max: float = 1e9           # teto de eficiencia (resRel/esfRel)
    qual_max: float = 1e9           # teto de qualRel
    res_max: float = 1e9            # teto de resRel
    esf_min: float = 0.0            # piso de esfRel (esforco relativo)
    esf_max: float = 1e9            # teto de esfRel
    corpo_min: float = 0.0          # piso de corpo/range da barra de sinal
    corpo_max: float = 1e9          # teto de corpo/range da barra de sinal
    contra_max: int = 0             # 0 = livre; senao teto de barras seguidas
                                    # na direcao contraria antes do sinal

    # entrada
    entrada: str = 'fecha'          # 'fecha'   a mercado no fechamento do sinal
                                    # 'meio'    limitada no meio do range do
                                    #           sinal, valida por UMA barra
                                    # 'extremo' limitada no extremo contrario
                                    #           do sinal, valida por UMA barra

    # gestao, em ticks
    stop_ticks: float = 388.0       # 1 range = 1R
    parcial_ticks: float = 388.0
    parcial_frac: float = 0.5
    alvo_ticks: float = 1164.0      # 3R
    max_barras: int = 0             # 0 = sem stop por tempo
    custo_ticks: float = 0.0        # custo total ida+volta, em ticks de 1 lote

    ordem_intrabar: str = 'pessimista'
    # Entradas LIMITADAS: travar a barra do preenchimento para que ela so possa
    # piorar a operacao (ver _percorre). Desligar produz o limite SUPERIOR do
    # intervalo -- e um numero impossivel de realizar, publicado so como teto.
    trava_barra_fill: bool = True


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


def conferir_premissa(d):
    """A versao Python de `ValidarPremissa` do .mq5.

    O indicador so faz sentido onde High-Low e constante e onde tickvol/vol
    carregam agressao compradora/vendedora. Aplicado a um grafico de tempo ele
    nao da erro nenhum -- so produz numeros sem significado, que e o pior modo
    de falhar. Daqui saem os numeros que o relatorio publica como prova de que
    o arquivo e mesmo de range.
    """
    rng = ((d.high - d.low) / TICK).to_numpy()
    mediana = float(np.median(rng))
    dentro = float(np.mean(np.abs(rng - mediana) <= 0.10 * mediana))
    return dict(
        range_mediana=mediana,
        range_dentro_10pct=dentro,
        range_min=float(rng.min()), range_max=float(rng.max()),
        range_desvio=float(rng.std(ddof=1)),
        pct_vol_zero=float((d.vol == 0).mean()),
        pct_tickvol_zero=float((d.tickvol == 0).mean()),
        correlacao_agressoes=float(np.corrcoef(d.tickvol, d.vol)[0, 1]),
        e_range=bool(dentro > 0.75),
        tem_agressao=bool((d.vol == 0).mean() < 0.80),
    )


# --------------------------------------------------------------------------
# O INDICADOR
# --------------------------------------------------------------------------
def _div(a, b):
    """a/b com zero onde b <= 0. E o `if (x > 0)` do .mq5, vetorizado."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return np.divide(a, b, out=np.zeros(np.broadcast(a, b).shape, dtype=float),
                     where=b > 0)


def esforco_resultado(df, ind=Ind()):
    """Porte de `OnCalculate`. Acrescenta ao DataFrame:

        sinal    +-1 absorcao, +-2 divergencia, 0 nada
        efic     resRel / esfRel
        res_rel  resultado da barra / media da MESMA direcao
        esf_rel  esforco da barra  / media da MESMA direcao
        qual_rel qualDir da barra  / media ponderada da MESMA direcao
        rng_ref  media do range das `periodo_base` barras anteriores

    O laco `for k = 1..PeriodoBase` do .mq5 vira uma janela deslizante: a
    linha j da matriz cobre exatamente as barras idx-P .. idx-1 de idx = j+P.
    Mesmo resultado, sem 2,4 milhoes de iteracoes em Python.
    """
    d = df.copy()
    P = ind.periodo_base
    n = len(d)
    if n <= P + 2:
        raise ValueError('historico curto demais para periodo_base=%d' % P)

    rng = ((d.high - d.low) / TICK).to_numpy()
    res = ((d.close - d.open) / TICK).to_numpy()
    corpo = np.abs(res)
    esf = (d.tickvol.to_numpy() + d.vol.to_numpy()).astype(float)
    dlt = (d.tickvol.to_numpy() - d.vol.to_numpy()).astype(float)

    swv = np.lib.stride_tricks.sliding_window_view
    W_rng = swv(rng, P)[:n - P]     # linha j <-> idx = j+P, cobre idx-P..idx-1
    W_res = swv(res, P)[:n - P]
    W_esf = swv(esf, P)[:n - P]
    W_dlt = swv(dlt, P)[:n - P]

    # --- range de referencia: MEDIA, nao maximo. Uma unica barra que estourou
    #     o range nominal inflaria a referencia e desligaria os sinais na
    #     janela inteira.
    rng_ref = np.ones(n)
    rng_ref[P:] = W_rng.mean(axis=1)
    rng_ref[rng_ref <= 0] = 1.0

    # --- so barras completas entram nas medias de referencia
    compl = W_rng >= ind.fator_completa * rng_ref[P:, None]
    mUp = compl & (W_res > 0) & (W_esf > 0)
    mDn = compl & (W_res < 0) & (W_esf > 0)      # doji (res==0) fica de fora

    nUp = mUp.sum(1).astype(float)
    nDn = mDn.sum(1).astype(float)
    sResUp = np.where(mUp, W_res, 0.0).sum(1)
    sEsfUp = np.where(mUp, W_esf, 0.0).sum(1)
    sDltUp = np.where(mUp, W_dlt, 0.0).sum(1)
    sResDn = np.where(mDn, -W_res, 0.0).sum(1)   # guardados positivos
    sEsfDn = np.where(mDn, W_esf, 0.0).sum(1)
    sDltDn = np.where(mDn, -W_dlt, 0.0).sum(1)   # positivo se a favor da baixa

    medResUp, medEsfUp = _div(sResUp, nUp), _div(sEsfUp, nUp)
    medResDn, medEsfDn = _div(sResDn, nDn), _div(sEsfDn, nDn)
    # soma(dlt)/soma(esf), nao media das razoes: pondera cada barra pelo esforco
    medQualUp, medQualDn = _div(sDltUp, sEsfUp), _div(sDltDn, sEsfDn)

    # --- a barra em estudo
    dirs = np.sign(res).astype(int)
    dir1 = np.roll(dirs, 1); dir1[0] = 0
    dir2 = np.roll(dirs, 2); dir2[:2] = 0
    virada = (dirs != 0) & (dir1 != 0) & (dirs == -dir1)
    completa = np.zeros(n, dtype=bool)
    completa[P:] = rng[P:] >= ind.fator_completa * rng_ref[P:]

    medRes = np.zeros(n); medEsf = np.zeros(n); medQual = np.zeros(n)
    for m, mr, me, mq in ((dirs == 1, medResUp, medEsfUp, medQualUp),
                          (dirs == -1, medResDn, medEsfDn, medQualDn)):
        sel = m[P:]
        medRes[P:] = np.where(sel, mr, medRes[P:])
        medEsf[P:] = np.where(sel, me, medEsf[P:])
        medQual[P:] = np.where(sel, mq, medQual[P:])

    res_dir = res * dirs
    qual_dir = _div(dlt * dirs, esf)

    res_rel = _div(res_dir, medRes)
    esf_rel = _div(esf, medEsf)
    qual_rel = _div(qual_dir, medQual)
    efic = _div(res_rel, esf_rel)

    # --- SINAL 1: absorcao
    s_abs = (completa & virada & (medRes > 0) & (medQual > 0) &
             (res_rel < ind.fator_res) & (qual_rel < ind.fator_qual))

    # --- SINAL 2: divergencia no pivo N-1 / N
    rng1 = np.roll(rng, 1); rng1[0] = 0.0
    corpo1 = np.roll(corpo, 1); corpo1[0] = 0.0
    dlt1 = np.roll(dlt, 1); dlt1[0] = 0.0
    esf1 = np.roll(esf, 1); esf1[0] = 0.0

    # O pivo e N-1 + N: sao essas duas que precisam ser quase cheias. N-2 so da
    # o contexto de direcao -- garante que o pivo esta virando um movimento.
    par_cheio = ((rng1 > 0) & (rng > 0) &
                 (_div(corpo1, rng1) >= ind.fator_corpo) &
                 (_div(corpo, rng) >= ind.fator_corpo))
    soma_dlt = dlt + dlt1
    soma_esf = esf + esf1
    desq = _div(np.abs(soma_dlt), soma_esf)
    s_div = (ind.usar_divergen & completa & virada & (dir2 == dir1) &
             par_cheio & (soma_dlt * dirs < 0) & (desq >= ind.lim_desq))

    if ind.prioridade_azul:
        s_abs = s_abs & ~s_div

    sinal = np.zeros(n, dtype=int)
    sinal[s_abs] = dirs[s_abs]
    sinal[s_div] = 2 * dirs[s_div]
    sinal[:P + 2] = 0               # g_primeira do .mq5
    sinal[-1] = 0                   # a ultima barra nao tem futuro para medir

    d['sinal'] = sinal
    d['dir'] = dirs
    d['res_ticks'] = res
    d['range'] = rng
    d['rng_ref'] = rng_ref
    d['corpo_frac'] = _div(corpo, rng)
    d['esf'] = esf
    d['dlt'] = dlt
    d['res_rel'] = res_rel
    d['esf_rel'] = esf_rel
    d['qual_rel'] = qual_rel
    d['efic'] = efic
    d['desq'] = desq
    d['hora'] = d.dt.dt.hour
    d['data'] = d.dt.dt.date
    d['contra'] = _runlen_contra(dirs)
    return d


def _runlen_contra(dirs):
    """Quantas barras seguidas ANTES de cada barra vinham na direcao contraria
    a ela. E o tamanho do movimento que o sinal esta tentando virar."""
    n = len(dirs)
    out = np.zeros(n, dtype=np.int64)
    # run[i] = comprimento da sequencia de mesma direcao terminando em i
    run = np.zeros(n, dtype=np.int64)
    for i in range(n):
        if dirs[i] == 0:
            run[i] = 0
        elif i and dirs[i - 1] == dirs[i]:
            run[i] = run[i - 1] + 1
        else:
            run[i] = 1
    for i in range(1, n):
        if dirs[i] != 0 and dirs[i - 1] == -dirs[i]:
            out[i] = run[i - 1]
    return out


# --------------------------------------------------------------------------
# selecao dos sinais que viram operacao
# --------------------------------------------------------------------------
def sinais(d, cfg):
    """Aplica os filtros de contexto. Devolve o array de lado (+1/-1/0)."""
    s = d.sinal.to_numpy()
    lado = np.sign(s).astype(int)
    tipo = np.abs(s)

    ok = np.isin(tipo, np.array(cfg.tipos, dtype=int)) & (lado != 0)
    if cfg.horas:
        ok &= d.hora.isin(cfg.horas).to_numpy()
    ok &= d.efic.to_numpy() <= cfg.efic_max
    ok &= d.qual_rel.to_numpy() <= cfg.qual_max
    ok &= d.res_rel.to_numpy() <= cfg.res_max
    ok &= d.esf_rel.to_numpy() >= cfg.esf_min
    ok &= d.esf_rel.to_numpy() <= cfg.esf_max
    cf = d.corpo_frac.to_numpy()
    ok &= (cf >= cfg.corpo_min) & (cf <= cfg.corpo_max)
    if cfg.contra_max:
        ok &= d.contra.to_numpy() <= cfg.contra_max

    lado = np.where(ok, lado, 0)
    if 'long' not in cfg.lados:
        lado = np.where(lado > 0, 0, lado)
    if 'short' not in cfg.lados:
        lado = np.where(lado < 0, 0, lado)
    lado[-1] = 0
    return lado


# --------------------------------------------------------------------------
# simulacao
# --------------------------------------------------------------------------
def _percorre(sinal, ent, h, l, c, cfg, i0, n, so_stop_na_primeira=False):
    """Roda a gestao a partir da barra i0 (a primeira barra ja com posicao).

    `so_stop_na_primeira` existe para as entradas LIMITADAS. Quando a ordem e
    preenchida DENTRO da barra i0, o OHLC nao diz em que momento isso
    aconteceu: a maxima da barra pode ter sido feita ANTES do preenchimento, e
    creditar o alvo por causa dela e ler o futuro. Num grafico de range o erro
    e grosseiro -- a barra tem 388 ticks garantidos, entao quase toda barra que
    preenche uma ordem no meio dela tambem "alcanca" um alvo de meio range, e a
    taxa de acerto sobe para 99%. Com a trava, a barra do preenchimento so pode
    piorar a operacao, nunca melhorar: e a mesma convencao pessimista usada no
    resto do estudo, aplicada ao unico instante que o arquivo nao datou.
    """
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
        if so_stop_na_primeira and i == i0:
            bate_parc = bate_alvo = False

        if not feito_parcial:
            if bate_stop and (pess or not bate_parc):
                return dict(saida_i=i, motivo='stop', ticks=-cfg.stop_ticks,
                            parcial=False, barras=i - i0 + 1)
            if bate_parc:
                res += frac * cfg.parcial_ticks
                if frac >= 1.0:
                    # a "parcial" fechou a posicao inteira: nao sobra runner
                    # para levar a breakeven, e o desfecho e o alvo. Sem isto a
                    # operacao sai rotulada 'breakeven' com o resultado cheio,
                    # e o filtro de desfecho do relatorio mente.
                    return dict(saida_i=i, motivo='alvo', ticks=res,
                                parcial=False, barras=i - i0 + 1)
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
            if bate_stop:                      # otimista, e a parcial nao bateu
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
    lados = sinais(d, cfg)
    o = d.open.to_numpy(); h = d.high.to_numpy()
    l = d.low.to_numpy(); c = d.close.to_numpy()
    n = len(d)
    idx = np.where(lados != 0)[0]
    dts = d.dt.to_numpy()
    horas = d.hora.to_numpy()
    tipos = np.abs(d.sinal.to_numpy())
    efics = d.efic.to_numpy(); resr = d.res_rel.to_numpy()
    qualr = d.qual_rel.to_numpy(); esfr = d.esf_rel.to_numpy()
    cfrac = d.corpo_frac.to_numpy(); rgs = d['range'].to_numpy()
    contras = d.contra.to_numpy()

    ops = []
    ocupado_ate = -1
    for i in idx:
        if i <= ocupado_ate:
            continue                          # uma operacao por vez
        sinal = int(lados[i])
        if cfg.inverter:
            sinal = -sinal
        meio = (h[i] + l[i]) / 2
        extremo = l[i] if sinal > 0 else h[i]
        j = i + 1

        # entrada no fechamento: o preco e conhecido na fronteira da barra e a
        # gestao so comeca na barra seguinte -- nao ha instante indatado.
        # entrada limitada: o preenchimento acontece DENTRO da barra j, e a
        # barra j fica travada para so poder piorar a operacao (ver _percorre).
        limitada = cfg.entrada in ('meio', 'extremo')
        if cfg.entrada == 'fecha':
            ativou, ent, ordem = True, c[i], c[i]
        elif cfg.entrada == 'meio':
            ordem = meio
            if sinal > 0:
                ativou, ent = l[j] <= meio, min(meio, o[j])
            else:
                ativou, ent = h[j] >= meio, max(meio, o[j])
        elif cfg.entrada == 'extremo':
            ordem = extremo
            if sinal > 0:
                ativou, ent = l[j] <= extremo, min(extremo, o[j])
            else:
                ativou, ent = h[j] >= extremo, max(extremo, o[j])
        else:
            raise ValueError('entrada desconhecida: %s' % cfg.entrada)

        comum = dict(sinal_i=int(i), dt=dts[i],
                     lado='long' if sinal > 0 else 'short',
                     tipo=int(tipos[i]),
                     preco_ordem=float(ordem), hora=int(horas[i]),
                     efic=float(efics[i]), res_rel=float(resr[i]),
                     qual_rel=float(qualr[i]), esf_rel=float(esfr[i]),
                     corpo_frac=float(cfrac[i]), range_sinal=float(rgs[i]),
                     contra=int(contras[i]))
        if not ativou:
            ops.append(dict(comum, ativou=False, entrada=np.nan, saida_i=-1,
                            motivo='abortada', ticks=0.0, ticks_bruto=0.0,
                            parcial=False, barras=0))
            continue
        r = _percorre(sinal, ent, h, l, c, cfg, j, n,
                      so_stop_na_primeira=limitada and cfg.trava_barra_fill)
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
    ep = dp / np.sqrt(n) if n else 0.0
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
        erro_padrao_ticks=float(ep),
        # sem o erro padrao ao lado, a tabela de variantes vira um ranking de ruido
        t_stat=float(exp / ep) if ep > 0 else 0.0,
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
        absorcao=int((ativ.tipo == 1).sum()),
        divergencia=int((ativ.tipo == 2).sum()),
        ticks_absorcao=float(ativ[ativ.tipo == 1].ticks.sum()),
        ticks_divergencia=float(ativ[ativ.tipo == 2].ticks.sum()),
    )


def resumo_cfg(cfg):
    d = asdict(cfg)
    d['ind'] = asdict(cfg.ind)
    d['tipos'] = list(cfg.tipos)
    d['lados'] = list(cfg.lados)
    d['horas'] = list(cfg.horas)
    return d


def com(cfg, **kw):
    """Copia de cfg com campos trocados, preservando os campos-tupla."""
    return replace(cfg, **kw)
