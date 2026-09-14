# -*- coding: utf-8 -*-
"""
Motor do backtest "medias + Esforco x Resultado" em XAUUSD, grafico de RANGE
de 388 ticks.

A ideia da estrategia: SEGUIR A TENDENCIA. As medias (21/42/72) em leque
ordenado dizem que existe tendencia; a largura do leque diz que ela nao esta
"embolada" -- medias emboladas sao consolidacao, e e la que este tipo de
entrada morre. Dentro desse contexto, o gatilho de entrada e o indicador

    MQL5/Indicators/Triggers/Trigger_EsforcoResultado_Range.mq5

portado para Python em `esforco_resultado` -- transcricao linha a linha do laco
de `OnCalculate`, com os mesmos nomes de variavel do .mq5.

O gatilho e um sinal de VIRADA: a barra N reverte a barra N-1 e se opera a
favor de N. Combinado com o leque, ele deixa de ser "reversao" e vira
"retomada": so entra quando a virada aponta para o mesmo lado da tendencia.

    res  = (close - open) em ticks        RESULTADO liquido da barra
    esf  = tickvol + vol                  ESFORCO total (agressao dos dois lados)
    dlt  = tickvol - vol                  agressao liquida

`tickvol` e a agressao COMPRADORA e `vol` a VENDEDORA -- convencao do simbolo
sintetico gerado pelo Range_Claude_v1.mq5.

GESTAO -- todas com risco:retorno de 1:2
-----------------------------------------------------------------------------
Chamando S a distancia do stop e 2S a do alvo:

  'fixo'      stop em E-S, alvo em E+2S. Nada se move.
              desfechos:  -1R  ou  +2R

  'parcial'   a +1S vende 50% (embolsa +0.5S) e o stop vai para a ENTRADA.
              desfechos:  -1R,  +0.5R (parcial e volta),  +1.5R (alvo)

  'parcial_op' a +1S vende 50% (embolsa +0.5S) e o stop FICA ONDE ESTA.
              O nome vem da aritmetica: com metade realizada em +S, a operacao
              INTEIRA empata exatamente no stop inicial --
                  0.5*S + 0.5*(E-S - E) = 0
              entao "breakeven na media da operacao" e, literalmente, nao
              mexer no stop. E a leitura literal de ESTRATEGIA.md.
              desfechos:  -1R,  0R (parcial e stop),  +1.5R (alvo)

  'breakeven' a +1S o stop vai para a ENTRADA, sem parcial nenhuma.
              desfechos:  -1R,  0R,  +2R

As duas leituras de "breakeven na media" ('parcial' e 'parcial_op') estao
implementadas porque a diferenca entre elas e material e o texto admite as
duas. O estudo publica as duas e deixa os numeros decidirem.

Unico ponto onde OHLC nao decide sozinho: quando a mesma barra toca dois
niveis. Resolvido por `ordem_intrabar`:
    'pessimista'  o pior nivel acontece primeiro (padrao dos numeros publicados)
    'otimista'    o melhor acontece primeiro
Ao contrario do estudo de 1:1 em meio range, aqui a ambiguidade EXISTE: um
alvo de 2R esta longe demais para caber na garantia geometrica da barra. Por
isso toda tabela traz as duas hipoteses.
"""
import os
from dataclasses import dataclass, asdict, replace

import numpy as np
import pandas as pd

TICK = 0.01
RANGE_NOMINAL = 388.0          # ticks; o range do simbolo
BASE = os.path.dirname(os.path.abspath(__file__))
ARQUIVO = os.path.join(BASE, 'XAUUSD-388N',
                       'XAUUSD_388_N_M1_202605110101_202609042330.csv')

MODOS = ('fixo', 'parcial', 'parcial_op', 'breakeven')
MODO_ROTULO = {
    'fixo': 'stop e alvo fixos',
    'parcial': 'parcial 50% em 1R + stop na entrada',
    'parcial_op': 'parcial 50% em 1R + breakeven da operação',
    'breakeven': 'breakeven na entrada em 1R, sem parcial',
}


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
# configuracao da ESTRATEGIA
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Config:
    nome: str = 'base'
    rotulo: str = 'base'
    ind: Ind = Ind()

    # --- contexto: as medias
    ma_tipo: str = 'ema'            # 'ema' ou 'hull'
    ma_curta: int = 21
    ma_media: int = 42
    ma_longa: int = 72
    exige_leque: bool = True        # as tres medias ordenadas na direcao
    leque_min: float = 0.0          # ticks de |MA curta - MA longa| exigidos
    leque_max: float = 1e9          # teto do leque (leque exagerado = climax)
    inclin_min: float = 0.0         # ticks de avanco da MA curta em inclin_jan
    inclin_jan: int = 10
    exige_lado_leque: bool = False  # a barra de sinal fecha do lado certo da
                                    # MA curta (retomada confirmada)
    dist_max: float = 1e9           # ticks: teto de |close - MA curta|, para
                                    # nao entrar esticado

    # --- gatilho
    tipos: tuple = (1, 2)           # 1 = absorcao, 2 = divergencia
    lados: tuple = ('long', 'short')
    inverter: bool = False          # controle: opera o lado OPOSTO
    esf_max: float = 1e9            # teto de esforco relativo (o filtro que
                                    # sobreviveu no estudo anterior)
    horas: tuple = ()               # () = todas

    # --- gestao (sempre 1:2)
    modo: str = 'fixo'
    stop_ticks: float = 194.0       # 1R
    rr: float = 2.0                 # alvo = rr * stop
    parcial_frac: float = 0.5
    max_barras: int = 0             # 0 = sem stop por tempo
    custo_ticks: float = 0.0        # custo total ida+volta, em ticks de 1 lote

    ordem_intrabar: str = 'pessimista'
    # O stop movido para a entrada passa a valer SO NA BARRA SEGUINTE.
    #
    # Sem isto o alvo fica inalcancavel por construcao. A entrada e o
    # fechamento da barra de sinal, ou seja, a barra seguinte ABRE exatamente
    # no preco de entrada; qualquer barra que suba 1R e tenha qualquer pavio
    # inferior "volta ao breakeven" no papel. Como a barra de range percorre
    # 388 ticks garantidos, isso acontece em praticamente toda barra que arma
    # o gatilho -- e o backtest devolve ZERO saidas no alvo nos modos com
    # breakeven, o que e artefato de contabilidade e nao resultado.
    #
    # O OHLC nao diz se a minima veio antes ou depois do toque em 1R, entao
    # nenhuma das duas leituras e demonstravel. Esta e a convencao padrao;
    # a oposta e publicada ao lado, como piso.
    be_proxima_barra: bool = True

    @property
    def alvo_ticks(self):
        return self.rr * self.stop_ticks

    @property
    def gatilho_ticks(self):
        """A distancia onde a parcial / o breakeven sao acionados: 1R."""
        return self.stop_ticks


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
    """A versao Python de `ValidarPremissa` do .mq5: o indicador so significa
    alguma coisa onde High-Low e constante e onde tickvol/vol carregam
    agressao compradora/vendedora."""
    rng = ((d.high - d.low) / TICK).to_numpy()
    mediana = float(np.median(rng))
    dentro = float(np.mean(np.abs(rng - mediana) <= 0.10 * mediana))
    return dict(
        range_mediana=mediana,
        range_dentro_10pct=dentro,
        range_min=float(rng.min()), range_max=float(rng.max()),
        range_desvio=float(rng.std(ddof=1)),
        pct_vol_zero=float((d.vol == 0).mean()),
        correlacao_agressoes=float(np.corrcoef(d.tickvol, d.vol)[0, 1]),
        e_range=bool(dentro > 0.75),
        tem_agressao=bool((d.vol == 0).mean() < 0.80),
    )


# --------------------------------------------------------------------------
# MEDIAS
# --------------------------------------------------------------------------
def _wma(x, n):
    """Media movel ponderada linearmente (peso cresce com a recencia).

    Por convolucao, e nao por `rolling().apply()`: sao tres WMAs encadeadas
    por Hull, em 39 mil barras, e a versao com apply leva minutos.
    """
    n = int(max(1, round(n)))
    x = np.asarray(x, dtype=float)
    pesos = np.arange(1, n + 1, dtype=float)
    pesos /= pesos.sum()
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        # kernel invertido: convolve casa kernel[n-1-k] com x[j+k]
        out[n - 1:] = np.convolve(x, pesos[::-1], mode='valid')
    return out


def hull(x, n):
    """Hull Moving Average.

        HMA(n) = WMA( 2*WMA(x, n/2) - WMA(x, n),  sqrt(n) )

    A Hull persegue o preco muito mais de perto que a exponencial de mesmo
    periodo: ela vira antes, e por isso o leque dela abre e fecha muito mais
    vezes. Se a tese "leque aberto = tendencia" valer, a Hull deveria
    identificar a tendencia mais cedo -- e tambem se enganar mais vezes. E
    exatamente isso que o estudo mede.
    """
    n = int(n)
    metade = _wma(x, n / 2.0)
    cheia = _wma(x, n)
    bruto = 2.0 * metade - cheia
    return _wma(bruto, np.sqrt(n))


def medias(d, cfg):
    """Acrescenta ma1/ma2/ma3, o leque e as distancias. Devolve uma copia."""
    c = d.close.to_numpy()
    per = (cfg.ma_curta, cfg.ma_media, cfg.ma_longa)
    if cfg.ma_tipo == 'ema':
        m = [pd.Series(c).ewm(span=p, adjust=False).mean().to_numpy()
             for p in per]
    elif cfg.ma_tipo == 'hull':
        m = [np.asarray(hull(c, p), dtype=float) for p in per]
    else:
        raise ValueError('ma_tipo desconhecido: %s' % cfg.ma_tipo)

    d = d.copy()
    d['ma1'], d['ma2'], d['ma3'] = m
    # O aquecimento da Hull e mais longo que o da exponencial (tres WMAs
    # encadeadas). Onde a media ainda e NaN, nao ha contexto e nao ha sinal.
    d['ma_ok'] = ~(np.isnan(m[0]) | np.isnan(m[1]) | np.isnan(m[2]))
    d['leque_up'] = (m[0] > m[1]) & (m[1] > m[2])
    d['leque_dn'] = (m[0] < m[1]) & (m[1] < m[2])
    d['leque'] = np.abs(m[0] - m[2]) / TICK
    d['dist_ma1'] = (d.close.to_numpy() - m[0]) / TICK

    av = np.full(len(d), 0.0)
    if cfg.inclin_jan > 0:
        av[cfg.inclin_jan:] = (m[0][cfg.inclin_jan:] -
                               m[0][:-cfg.inclin_jan]) / TICK
    d['inclin'] = av
    return d


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
    """Porte de `OnCalculate`. Ver o modulo homonimo do estudo anterior --
    esta funcao e identica, e foi conferida contra o .mq5 linha a linha."""
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

    rng_ref = np.ones(n)
    rng_ref[P:] = W_rng.mean(axis=1)
    rng_ref[rng_ref <= 0] = 1.0

    compl = W_rng >= ind.fator_completa * rng_ref[P:, None]
    mUp = compl & (W_res > 0) & (W_esf > 0)
    mDn = compl & (W_res < 0) & (W_esf > 0)

    nUp = mUp.sum(1).astype(float)
    nDn = mDn.sum(1).astype(float)
    sResUp = np.where(mUp, W_res, 0.0).sum(1)
    sEsfUp = np.where(mUp, W_esf, 0.0).sum(1)
    sDltUp = np.where(mUp, W_dlt, 0.0).sum(1)
    sResDn = np.where(mDn, -W_res, 0.0).sum(1)
    sEsfDn = np.where(mDn, W_esf, 0.0).sum(1)
    sDltDn = np.where(mDn, -W_dlt, 0.0).sum(1)

    medResUp, medEsfUp = _div(sResUp, nUp), _div(sEsfUp, nUp)
    medResDn, medEsfDn = _div(sResDn, nDn), _div(sEsfDn, nDn)
    medQualUp, medQualDn = _div(sDltUp, sEsfUp), _div(sDltDn, sEsfDn)

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

    s_abs = (completa & virada & (medRes > 0) & (medQual > 0) &
             (res_rel < ind.fator_res) & (qual_rel < ind.fator_qual))

    rng1 = np.roll(rng, 1); rng1[0] = 0.0
    corpo1 = np.roll(corpo, 1); corpo1[0] = 0.0
    dlt1 = np.roll(dlt, 1); dlt1[0] = 0.0
    esf1 = np.roll(esf, 1); esf1[0] = 0.0
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
    sinal[:P + 2] = 0
    sinal[-1] = 0

    d['sinal'] = sinal
    d['dir'] = dirs
    d['range'] = rng
    d['corpo_frac'] = _div(corpo, rng)
    d['res_rel'] = res_rel
    d['esf_rel'] = esf_rel
    d['qual_rel'] = qual_rel
    d['efic'] = efic
    d['hora'] = d.dt.dt.hour
    d['data'] = d.dt.dt.date
    return d


def preparar(df, cfg):
    """Indicador + medias, na ordem. Devolve o DataFrame pronto para `rodar`."""
    return medias(esforco_resultado(df, cfg.ind), cfg)


# --------------------------------------------------------------------------
# selecao dos sinais
# --------------------------------------------------------------------------
def sinais(d, cfg):
    """Aplica o contexto das medias e os filtros do gatilho.
    Devolve o array de lado (+1/-1/0)."""
    s = d.sinal.to_numpy()
    lado = np.sign(s).astype(int)
    tipo = np.abs(s)

    ok = np.isin(tipo, np.array(cfg.tipos, dtype=int)) & (lado != 0)
    ok &= d.ma_ok.to_numpy()

    # --- o contexto: tendencia na MESMA direcao do sinal
    up, dn = d.leque_up.to_numpy(), d.leque_dn.to_numpy()
    if cfg.exige_leque:
        ok &= np.where(lado > 0, up, np.where(lado < 0, dn, False))

    # --- leque aberto: medias emboladas sao consolidacao
    lq = d.leque.to_numpy()
    ok &= (lq >= cfg.leque_min) & (lq <= cfg.leque_max)

    if cfg.inclin_min > 0:
        inc = d.inclin.to_numpy()
        ok &= np.where(lado > 0, inc >= cfg.inclin_min,
                       -inc >= cfg.inclin_min)

    if cfg.exige_lado_leque:
        dm = d.dist_ma1.to_numpy()
        ok &= np.where(lado > 0, dm > 0, dm < 0)

    ok &= np.abs(d.dist_ma1.to_numpy()) <= cfg.dist_max
    ok &= d.esf_rel.to_numpy() <= cfg.esf_max
    if cfg.horas:
        ok &= d.hora.isin(cfg.horas).to_numpy()

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
def _percorre(sinal, ent, h, l, c, cfg, i0, n):
    """Roda a gestao a partir da barra i0 (a primeira barra ja com posicao).

    Um so laco atende os quatro modos. O que muda entre eles e apenas:
      - se ha parcial no gatilho de 1R  (`frac_parcial`)
      - para onde vai o stop depois do gatilho  (`stop_apos`)
    """
    S = cfg.stop_ticks * TICK
    stop = ent - sinal * S
    gat = ent + sinal * cfg.gatilho_ticks * TICK
    alvo = ent + sinal * cfg.alvo_ticks * TICK

    if cfg.modo == 'fixo':
        usa_gatilho, frac_parcial, stop_apos = False, 0.0, stop
    elif cfg.modo == 'parcial':
        usa_gatilho, frac_parcial, stop_apos = True, cfg.parcial_frac, ent
    elif cfg.modo == 'parcial_op':
        # "breakeven na media da operacao": com metade realizada em +1R, a
        # operacao inteira empata no stop INICIAL. Nao mexer no stop e,
        # literalmente, colocar o breakeven na media da operacao.
        usa_gatilho, frac_parcial, stop_apos = True, cfg.parcial_frac, stop
    elif cfg.modo == 'breakeven':
        usa_gatilho, frac_parcial, stop_apos = True, 0.0, ent
    else:
        raise ValueError('modo desconhecido: %s' % cfg.modo)

    pess = cfg.ordem_intrabar == 'pessimista'
    armado = False
    res = 0.0                      # ticks ja realizados (posicao de 1 lote)
    aberto = 1.0                   # fracao ainda em aberto
    lim = n if not cfg.max_barras else min(n, i0 + cfg.max_barras)

    for i in range(i0, lim):
        hi, lo = h[i], l[i]
        b_stop = (lo <= stop) if sinal > 0 else (hi >= stop)
        b_alvo = (hi >= alvo) if sinal > 0 else (lo <= alvo)
        b_gat = ((hi >= gat) if sinal > 0 else (lo <= gat)) if usa_gatilho else False

        if not armado:
            # o stop so perde para o gatilho/alvo se a hipotese for otimista
            if b_stop and (pess or not (b_gat or b_alvo)):
                return dict(saida_i=i, motivo='stop',
                            ticks=res - aberto * cfg.stop_ticks,
                            parcial=False, barras=i - i0 + 1)
            if b_gat:
                res += frac_parcial * cfg.gatilho_ticks
                aberto -= frac_parcial
                armado = True
                stop = stop_apos
                b_stop = (lo <= stop) if sinal > 0 else (hi >= stop)
                if cfg.be_proxima_barra:
                    # o stop novo so vale a partir da proxima barra
                    b_stop = False
                if b_alvo and (not pess or not b_stop):
                    res += aberto * cfg.alvo_ticks
                    return dict(saida_i=i, motivo='alvo', ticks=res,
                                parcial=frac_parcial > 0, barras=i - i0 + 1)
                if b_stop:
                    return dict(saida_i=i, motivo=_motivo_stop(cfg),
                                ticks=res + aberto * (stop - ent) * sinal / TICK,
                                parcial=frac_parcial > 0, barras=i - i0 + 1)
                continue
            if b_alvo:
                res += aberto * cfg.alvo_ticks
                return dict(saida_i=i, motivo='alvo', ticks=res,
                            parcial=False, barras=i - i0 + 1)
            if b_stop:
                return dict(saida_i=i, motivo='stop',
                            ticks=res - aberto * cfg.stop_ticks,
                            parcial=False, barras=i - i0 + 1)
        else:
            if b_stop and (pess or not b_alvo):
                return dict(saida_i=i, motivo=_motivo_stop(cfg),
                            ticks=res + aberto * (stop - ent) * sinal / TICK,
                            parcial=frac_parcial > 0, barras=i - i0 + 1)
            if b_alvo:
                res += aberto * cfg.alvo_ticks
                return dict(saida_i=i, motivo='alvo', ticks=res,
                            parcial=frac_parcial > 0, barras=i - i0 + 1)
            if b_stop:
                return dict(saida_i=i, motivo=_motivo_stop(cfg),
                            ticks=res + aberto * (stop - ent) * sinal / TICK,
                            parcial=frac_parcial > 0, barras=i - i0 + 1)

    # acabou o historico (ou estourou o stop por tempo) com posicao aberta
    i = lim - 1
    res += aberto * sinal * (c[i] - ent) / TICK
    return dict(saida_i=i, motivo='tempo', ticks=res,
                parcial=armado and frac_parcial > 0, barras=i - i0 + 1)


def _motivo_stop(cfg):
    """Nome do desfecho quando o stop ja foi movido/armado."""
    if cfg.modo == 'parcial_op':
        return 'empate'         # a operacao inteira zera no stop inicial
    return 'breakeven'


def rodar(d, cfg):
    """Executa a estrategia. Devolve DataFrame de sinais/operacoes."""
    lados = sinais(d, cfg)
    h = d.high.to_numpy(); l = d.low.to_numpy(); c = d.close.to_numpy()
    n = len(d)
    idx = np.where(lados != 0)[0]
    dts = d.dt.to_numpy()
    horas = d.hora.to_numpy()
    tipos = np.abs(d.sinal.to_numpy())
    lqs = d.leque.to_numpy(); dms = d.dist_ma1.to_numpy()
    esfr = d.esf_rel.to_numpy(); resr = d.res_rel.to_numpy()
    incs = d.inclin.to_numpy()

    ops = []
    ocupado_ate = -1
    for i in idx:
        if i <= ocupado_ate:
            continue                          # uma operacao por vez
        sinal = int(lados[i])
        if cfg.inverter:
            sinal = -sinal
        j = i + 1
        # entrada a mercado no fechamento da barra de sinal: o preco e
        # conhecido na fronteira da barra e a gestao so comeca na seguinte
        ent = c[i]
        r = _percorre(sinal, ent, h, l, c, cfg, j, n)
        ops.append(dict(
            sinal_i=int(i), dt=dts[i],
            lado='long' if sinal > 0 else 'short',
            tipo=int(tipos[i]), hora=int(horas[i]),
            entrada=float(ent), leque=float(lqs[i]),
            dist_ma1=float(dms[i]), inclin=float(incs[i]),
            esf_rel=float(esfr[i]), res_rel=float(resr[i]),
            saida_i=int(r['saida_i']), motivo=r['motivo'],
            ticks=r['ticks'] - cfg.custo_ticks, ticks_bruto=r['ticks'],
            parcial=bool(r['parcial']), barras=int(r['barras'])))
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
    """Rebaixamento maximo e a duracao dele, em operacoes."""
    if not len(curva):
        return 0.0, 0
    pico = np.maximum.accumulate(curva)
    fundo = curva - pico
    i = int(np.argmin(fundo))
    if fundo[i] >= 0:
        return 0.0, 0
    # quantas operacoes desde o pico que originou este fundo
    j = int(np.argmax(pico[:i + 1] == pico[i]))
    return float(fundo[i]), int(i - j + 1)


def _sequencias(v):
    """Maior sequencia de True, e a lista de todas as sequencias."""
    maior, atual, todas = 0, 0, []
    for x in v:
        if x:
            atual += 1
        else:
            if atual:
                todas.append(atual)
            atual = 0
        maior = max(maior, atual)
    if atual:
        todas.append(atual)
    return int(maior), todas


def estatisticas(t, cfg):
    """Resumo de uma corrida. Tudo em ticks/R; usd = ticks * 0.01 por lote."""
    vazio = dict(operacoes=0)
    if not len(t):
        return vazio
    a = t.copy()
    n = len(a)

    tk = a.ticks.to_numpy()
    g = a[a.ticks > 0]; p = a[a.ticks < 0]; z = a[a.ticks == 0]
    soma_g = float(g.ticks.sum()); soma_p = float(-p.ticks.sum())
    curva = np.cumsum(tk)
    dd, dd_len = _dd(curva)

    exp = float(tk.mean())
    dp = float(tk.std(ddof=1)) if n > 1 else 0.0
    ep = dp / np.sqrt(n) if n else 0.0

    max_g, seq_g = _sequencias(tk > 0)
    max_p, seq_p = _sequencias(tk < 0)
    # sem-ganho inclui os empates: e a sequencia que de fato pesa na cabeca
    max_sg, seq_sg = _sequencias(tk <= 0)

    por_dia = a.groupby('data').ticks.sum()
    ganho_medio = float(g.ticks.mean()) if len(g) else 0.0
    perda_media = float(p.ticks.mean()) if len(p) else 0.0

    return dict(
        operacoes=n,
        vitorias=int(len(g)), perdas=int(len(p)), neutras=int(len(z)),
        acerto=len(g) / n,
        acerto_sem_neutras=(len(g) / (len(g) + len(p))
                            if (len(g) + len(p)) else 0.0),
        ticks_total=float(tk.sum()),
        usd_total=float(tk.sum() * TICK),
        R_total=float(a.R.sum()),
        expectativa_ticks=exp,
        expectativa_R=float(a.R.mean()),
        expectativa_usd=exp * TICK,
        desvio_ticks=dp,
        erro_padrao_ticks=float(ep),
        t_stat=float(exp / ep) if ep > 0 else 0.0,
        ganho_medio=ganho_medio, perda_media=perda_media,
        maior_ganho=float(g.ticks.max()) if len(g) else 0.0,
        maior_perda=float(p.ticks.min()) if len(p) else 0.0,
        payoff=(ganho_medio / abs(perda_media)) if perda_media else 0.0,
        fator_lucro=(soma_g / soma_p) if soma_p > 0 else float('inf'),
        drawdown_ticks=dd,
        drawdown_R=dd / cfg.stop_ticks,
        drawdown_operacoes=dd_len,
        fator_recuperacao=(float(tk.sum()) / abs(dd)) if dd else float('inf'),
        sqn=(exp / dp * np.sqrt(n)) if dp > 0 else 0.0,
        max_ganhos_seguidos=max_g,
        max_perdas_seguidas=max_p,
        max_sem_ganho_seguidas=max_sg,
        media_ganhos_seguidos=float(np.mean(seq_g)) if seq_g else 0.0,
        media_perdas_seguidas=float(np.mean(seq_p)) if seq_p else 0.0,
        motivos={str(k): int(v) for k, v in a.motivo.value_counts().items()},
        parciais=int(a.parcial.sum()),
        barras_media=float(a.barras.mean()),
        barras_max=int(a.barras.max()),
        dias=int(a.data.nunique()),
        ops_por_dia=n / max(1, a.data.nunique()),
        melhor_dia=float(por_dia.max()), pior_dia=float(por_dia.min()),
        dias_positivos=int((por_dia > 0).sum()),
        dias_negativos=int((por_dia < 0).sum()),
        long=int((a.lado == 'long').sum()),
        short=int((a.lado == 'short').sum()),
        ticks_long=float(a[a.lado == 'long'].ticks.sum()),
        ticks_short=float(a[a.lado == 'short'].ticks.sum()),
        absorcao=int((a.tipo == 1).sum()),
        divergencia=int((a.tipo == 2).sum()),
    )


def resumo_cfg(cfg):
    d = asdict(cfg)
    d['ind'] = asdict(cfg.ind)
    d['tipos'] = list(cfg.tipos)
    d['lados'] = list(cfg.lados)
    d['horas'] = list(cfg.horas)
    d['alvo_ticks'] = cfg.alvo_ticks
    d['gatilho_ticks'] = cfg.gatilho_ticks
    d['modo_rotulo'] = MODO_ROTULO[cfg.modo]
    return d


def com(cfg, **kw):
    """Copia de cfg com campos trocados, preservando os campos-tupla."""
    return replace(cfg, **kw)
