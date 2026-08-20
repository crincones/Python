"""
Motor de geracao de candles Renko "11R" (padrao ProfitChart / Nelogica)
a partir de ticks do MetaTrader 5.

Implementacao de REFERENCIA: foi com ela que as regras abaixo foram deduzidas
e validadas contra a base do ProfitChart. A geracao de producao roda em MQL5,
dentro do terminal (MQL5\\Scripts\\Tick Recorder\\GerarRenko11R.mq5), que le os
ticks direto do banco do MT5. Este modulo continua util para reconferir o
algoritmo sobre um lote de ticks ja em maos.

Regras do Renko do ProfitChart (obtidas por engenharia reversa da base
profitpro-ohlc-11R.csv, exportada do ProfitPro):

  * Tijolo (brick) = 50 pontos para o WIN no ajuste "11R"
    (o rotulo "11R" corresponde a 11 niveis de preco de 5 pontos =
     10 intervalos x 5 = 50 pontos).

  * A grade e global: todas as aberturas/fechamentos sao multiplos de 50.
    Nao ha reinicio diario -- a serie atravessa a virada de dia e o gap
    de abertura e preenchido com varios tijolos de mesmo timestamp.

  * Sendo `base` o fechamento do ultimo tijolo e `dir` o seu sentido:
        dir = +1  ->  sobe se  preco >  base + B      (tijolo [base, base+B])
                      inverte  se preco <  base - 2B  (tijolo [base-B, base-2B])
        dir = -1  ->  cai   se  preco <  base - B     (tijolo [base, base-B])
                      inverte  se preco >  base + 2B  (tijolo [base+B, base+2B])
    A comparacao e ESTRITA (`>` / `<`). Encostar exatamente no nivel nao
    gera tijolo -- confirmado em 397 barras da base em que a maxima toca
    o limiar sem virar o tijolo.

  * O tick que dispara o tijolo NAO pertence a barra que fecha: ele e o
    primeiro tick da barra seguinte (e define o timestamp dela).

  * Maxima/minima: o extremo do lado do tijolo e travado no fechamento
        tijolo de alta  ->  Maxima = Fechamento, Minima = min(minima real, Abertura)
        tijolo de baixa ->  Minima = Fechamento, Maxima = max(maxima real, Abertura)

  * Um unico tick pode gerar varios tijolos; os intermediarios saem com
    volume zero, duracao zero e o mesmo timestamp.

  * Quantity = soma de volume_real de TODOS os ticks de negocio, inclusive
    os de agressor indefinido (flags BUY e SELL simultaneas, tipicamente
    negocios diretos/leilao).

Validado contra a base do ProfitChart em 13/08/2026: 321 barras,
100% de acerto em Data / Abertura / Maxima / Minima / Fechamento e
98,4% em Quantity (as 5 divergencias vem de ticks perdidos na coleta em
tempo real do proprio MT5; o total do dia fecha com 0,06% de diferenca).
"""

from __future__ import annotations

import numpy as np

# Flags de tick do MT5
TICK_FLAG_BID = 2
TICK_FLAG_ASK = 4
TICK_FLAG_LAST = 8
TICK_FLAG_VOLUME = 16
TICK_FLAG_BUY = 32
TICK_FLAG_SELL = 64

BRICK_11R = 50.0


def extrair_negocios(ticks):
    """Filtra o array de ticks do MT5 deixando so os negocios (LAST+VOLUME).

    Devolve um dicionario de arrays numpy paralelos.
    """
    if ticks is None or len(ticks) == 0:
        return None
    flags = ticks["flags"]
    negocio = ((flags & TICK_FLAG_LAST) != 0) & ((flags & TICK_FLAG_VOLUME) != 0)
    if not negocio.any():
        return None
    t = ticks[negocio]
    f = t["flags"]
    tem_compra = (f & TICK_FLAG_BUY) != 0
    tem_venda = (f & TICK_FLAG_SELL) != 0
    indefinido = tem_compra & tem_venda          # negocio direto / leilao
    return {
        "ms": t["time_msc"].astype(np.int64),
        "preco": t["last"].astype(np.float64),
        "vol": t["volume_real"].astype(np.float64),
        "compra": tem_compra & ~indefinido,
        "venda": tem_venda & ~indefinido,
        "indef": indefinido,
    }


def _barra_nova(ms0, preco):
    return {
        "t0": int(ms0), "tf": int(ms0),
        "max": float(preco), "min": float(preco),
        "vol": 0.0, "vcompra": 0.0, "vvenda": 0.0, "vindef": 0.0,
        "n": 0,
    }


def _acumular(barra, d, a, b):
    """Acumula os ticks [a, b) na barra (cria se necessario)."""
    if b <= a:
        return barra
    preco = d["preco"][a:b]
    vol = d["vol"][a:b]
    if barra is None:
        barra = _barra_nova(d["ms"][a], preco[0])
    hi = float(preco.max())
    lo = float(preco.min())
    if hi > barra["max"]:
        barra["max"] = hi
    if lo < barra["min"]:
        barra["min"] = lo
    barra["tf"] = int(d["ms"][b - 1])
    barra["vol"] += float(vol.sum())
    barra["vcompra"] += float(vol[d["compra"][a:b]].sum())
    barra["vvenda"] += float(vol[d["venda"][a:b]].sum())
    barra["vindef"] += float(vol[d["indef"][a:b]].sum())
    barra["n"] += int(b - a)
    return barra


def _primeiro_cruzamento(preco, i, teto, piso):
    """Indice do primeiro tick >= i com preco > teto ou preco < piso."""
    n = len(preco)
    passo = 1 << 15
    a = i
    while a < n:
        b = min(a + passo, n)
        janela = preco[a:b]
        marca = (janela > teto) | (janela < piso)
        k = int(marca.argmax())
        if marca[k]:
            return a + k
        a = b
        if passo < (1 << 21):
            passo <<= 1
    return None


def gerar_renko(d, base, direcao, brick=BRICK_11R, barra=None):
    """Gera os tijolos Renko de um lote de negocios.

    d        : dicionario devolvido por extrair_negocios()
    base     : fechamento do ultimo tijolo concluido (float, na grade)
    direcao  : +1 / -1 do ultimo tijolo concluido
    barra    : estado da barra em formacao (dict) ou None

    Devolve (lista_de_barras, base, direcao, barra_em_formacao).
    Cada barra e uma tupla:
      (ms_abertura, o, h, l, c, vcompra, vvenda, vindef, vol, n_ticks, ms_fim)
    """
    saida = []
    if d is None:
        return saida, base, direcao, barra
    preco = d["preco"]
    ms = d["ms"]
    n = len(preco)
    i = 0
    while i < n:
        teto = base + brick if direcao > 0 else base + 2 * brick
        piso = base - 2 * brick if direcao > 0 else base - brick
        j = _primeiro_cruzamento(preco, i, teto, piso)
        if j is None:
            barra = _acumular(barra, d, i, n)
            break
        barra = _acumular(barra, d, i, j)
        px = float(preco[j])
        while True:
            teto = base + brick if direcao > 0 else base + 2 * brick
            piso = base - 2 * brick if direcao > 0 else base - brick
            if px > teto:
                abre, fecha = teto - brick, teto
                base, direcao = teto, 1
            elif px < piso:
                abre, fecha = piso + brick, piso
                base, direcao = piso, -1
            else:
                break
            if barra is None:
                barra = _barra_nova(ms[j], px)
            if fecha > abre:                       # tijolo de alta
                maxima = fecha
                minima = min(barra["min"], abre)
            else:                                  # tijolo de baixa
                minima = fecha
                maxima = max(barra["max"], abre)
            saida.append((
                barra["t0"], abre, maxima, minima, fecha,
                barra["vcompra"], barra["vvenda"], barra["vindef"],
                barra["vol"], barra["n"], barra["tf"],
            ))
            barra = None
        barra = _acumular(barra, d, j, j + 1)
        i = j + 1
    return saida, base, direcao, barra


def ancorar_base(preco_inicial, brick=BRICK_11R):
    """Define (base, direcao) iniciais quando nao ha estado anterior."""
    base = float(np.floor(preco_inicial / brick) * brick)
    return base, 1
