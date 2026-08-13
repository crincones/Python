#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gerar_sr.py
===========
Detecta niveis de suporte/resistencia a partir de OHLCV de 1 minuto (export MT5)
e gera o codigo NTSL para desenhar as linhas no ProfitChart.

Pipeline
--------
1. GERACAO DE CANDIDATOS (3 fontes independentes)
     a) perfil de volume reconstruido do M1 (HVNs)
     b) tempo-no-preco / TPO (minutos que cada faixa foi negociada)
     c) pivos multi-timeframe (M15/H1/H4/D1) reamostrados do proprio M1
     d) numeros redondos (opcional)
2. FUSAO  -> clusteriza candidatos proximos em espaco de preco
3. MEDICAO -> toques independentes, rejeicoes, rompimentos, flip, recencia
4. SCORE   -> combinacao de rankings percentuais (escala-livre)
5. SELECAO -> guloso por score com separacao minima; N acima / N abaixo da ref
6. SAIDA   -> arquivo .src (NTSL) + .csv com todas as metricas

Uso minimo:
    python gerar_sr.py --csv WIN_M1.csv

Exemplo completo:
    python gerar_sr.py --csv WIN_M1.csv --preco-ref 172000 --linhas 20 \
        --dist-media 250 --data-limite 2026-08-06 --saida SR_Automatico.src --validar
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd
from scipy.signal import find_peaks


# ======================================================================
# 1. CARGA DE DADOS
# ======================================================================

def carregar(path: str, data_inicio=None, data_limite=None) -> pd.DataFrame:
    """Le o export M1 do MT5 (<DATE> <TIME> <OPEN> ... <SPREAD>)."""
    with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
        cabecalho = f.readline()

    if "\t" in cabecalho:
        sep = "\t"
    elif ";" in cabecalho:
        sep = ";"
    elif "," in cabecalho:
        sep = ","
    else:
        sep = r"\s+"

    # engine C quando o separador e um caractere simples: ~5x mais rapido
    # num export de 40 MB. So cai no engine python para o regex de espacos.
    if sep == r"\s+":
        df = pd.read_csv(path, sep=sep, engine="python")
    else:
        df = pd.read_csv(path, sep=sep, engine="c")
    df.columns = [c.strip().strip("<>").upper() for c in df.columns]

    faltando = {"DATE", "OPEN", "HIGH", "LOW", "CLOSE"} - set(df.columns)
    if faltando:
        raise ValueError(f"Colunas ausentes no CSV: {sorted(faltando)}")

    if "TIME" in df.columns:
        bruto = df["DATE"].astype(str).str.strip() + " " + df["TIME"].astype(str).str.strip()
    else:
        bruto = df["DATE"].astype(str).str.strip()

    dt = pd.to_datetime(bruto, format="%Y.%m.%d %H:%M:%S", errors="coerce")
    if dt.isna().mean() > 0.5:
        dt = pd.to_datetime(bruto, errors="coerce", format="mixed")
    df["DT"] = dt
    df = df.dropna(subset=["DT"]).sort_values("DT").reset_index(drop=True)

    # Id inteiro da sessao (pregao). O M1 e uma serie CONCATENADA: entre a
    # ultima barra de um dia e a primeira do seguinte ha um salto que no WIN
    # tem mediana de ~300 pts (p90 ~1000). Medir o desfecho de um toque
    # atravessando essa fronteira e medir o gap, nao o nivel -- por isso toda
    # janela de avaliacao e cortada no fim da sessao.
    df["SESSAO"] = (df["DT"].dt.normalize().diff() > pd.Timedelta(0)).cumsum().astype(np.int64)

    # volume real quando existir e for utilizavel; senao volume de ticks
    if "VOL" in df.columns and pd.to_numeric(df["VOL"], errors="coerce").fillna(0).sum() > 0:
        df["VOLUME"] = pd.to_numeric(df["VOL"], errors="coerce").fillna(0.0)
    elif "TICKVOL" in df.columns:
        df["VOLUME"] = pd.to_numeric(df["TICKVOL"], errors="coerce").fillna(0.0)
    else:
        df["VOLUME"] = 1.0

    if data_inicio:
        df = df[df["DT"] >= pd.Timestamp(data_inicio)]
    if data_limite:
        # limite inclusivo no dia inteiro
        lim = pd.Timestamp(data_limite)
        if lim.hour == 0 and lim.minute == 0:
            lim = lim + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df = df[df["DT"] <= lim]

    df = df.reset_index(drop=True)
    if len(df) < 500:
        raise ValueError(f"Poucas barras apos o filtro de datas: {len(df)}")
    return df


def escala_ruido(df: pd.DataFrame, dias_recentes: int = 120) -> dict:
    """
    Mede o "piso de ruido" do ativo, em pontos, na janela mais recente.

    Serve para dimensionar zona e movimento minimo em vez de fixa-los em
    pontos: numa serie que vai de 122k a 177k, um valor fixo significa coisas
    diferentes no inicio e no fim. Usa a fatia recente porque e a volatilidade
    que vale na hora de operar.
    """
    corte = df["DT"].iloc[-1] - pd.Timedelta(days=dias_recentes)
    rec = df[df["DT"] >= corte]
    if len(rec) < 2000:
        rec = df

    amp_m1 = float((rec["HIGH"] - rec["LOW"]).median())
    por_dia = rec.groupby(rec["DT"].dt.normalize()).agg(h=("HIGH", "max"), l=("LOW", "min"))
    amp_dia = float((por_dia["h"] - por_dia["l"]).median()) if len(por_dia) else amp_m1 * 30
    barras_dia = float(rec.groupby(rec["DT"].dt.normalize()).size().median())
    return {"amp_m1": amp_m1, "amp_dia": amp_dia, "barras_dia": barras_dia}


# ======================================================================
# 2. PERFIL DE PRECO (volume + tempo) RECONSTRUIDO DO M1
# ======================================================================

@dataclass
class Perfil:
    p_min: float
    tick: float
    volume: np.ndarray   # volume estimado por faixa de preco
    tempo: np.ndarray    # minutos-no-preco por faixa (TPO)

    def precos(self) -> np.ndarray:
        return self.p_min + np.arange(len(self.volume)) * self.tick

    def _fatia(self, lo: float, hi: float):
        i0 = max(0, int(np.floor((lo - self.p_min) / self.tick)))
        i1 = min(len(self.volume) - 1, int(np.ceil((hi - self.p_min) / self.tick)))
        if i1 < i0:
            return 0.0, 0.0
        return float(self.volume[i0:i1 + 1].sum()), float(self.tempo[i0:i1 + 1].sum())

    def na_zona(self, preco: float, meia_zona: float):
        return self._fatia(preco - meia_zona, preco + meia_zona)


def construir_perfil(df: pd.DataFrame, tick: float, peso_recencia: np.ndarray | None = None) -> Perfil:
    """
    Distribui o volume de cada barra M1 uniformemente entre LOW e HIGH.
    Usa truque de array de diferencas + cumsum -> O(n) em vez de O(n * range).
    """
    lo = df["LOW"].to_numpy(dtype=float)
    hi = df["HIGH"].to_numpy(dtype=float)
    vol = df["VOLUME"].to_numpy(dtype=float)
    if peso_recencia is not None:
        vol = vol * peso_recencia

    p_min = float(np.floor(lo.min() / tick) * tick)
    p_max = float(np.ceil(hi.max() / tick) * tick)
    n = int(round((p_max - p_min) / tick)) + 1

    i0 = np.clip(np.floor((lo - p_min) / tick).astype(np.int64), 0, n - 1)
    i1 = np.clip(np.ceil((hi - p_min) / tick).astype(np.int64), 0, n - 1)
    nbins = (i1 - i0 + 1).astype(float)

    w_vol = vol / nbins
    w_tpo = (peso_recencia if peso_recencia is not None else np.ones(len(lo))) / nbins

    d_vol = (np.bincount(i0, weights=w_vol, minlength=n + 1)
             - np.bincount(i1 + 1, weights=w_vol, minlength=n + 1))
    d_tpo = (np.bincount(i0, weights=w_tpo, minlength=n + 1)
             - np.bincount(i1 + 1, weights=w_tpo, minlength=n + 1))

    return Perfil(p_min, tick, np.cumsum(d_vol)[:n], np.cumsum(d_tpo)[:n])


# ======================================================================
# 3. GERACAO DE CANDIDATOS
# ======================================================================

@dataclass
class Candidato:
    preco: float
    fonte: str
    peso: float = 1.0


def _picos(valores: np.ndarray, precos: np.ndarray, dist_bins: int, fonte: str,
           prominencia_pct: float = 60.0) -> list[Candidato]:
    if valores.size == 0 or valores.max() <= 0:
        return []
    suave = pd.Series(valores).rolling(max(3, dist_bins // 3), center=True,
                                       min_periods=1).mean().to_numpy()
    prom = np.percentile(suave[suave > 0], prominencia_pct) if (suave > 0).any() else 0.0
    idx, props = find_peaks(suave, distance=max(1, dist_bins), prominence=max(prom * 0.15, 1e-9))
    if idx.size == 0:
        return []
    forca = props["prominences"]
    forca = forca / forca.max()
    return [Candidato(float(precos[i]), fonte, float(f)) for i, f in zip(idx, forca)]


def candidatos_perfil(perfil: Perfil, dist_media: float) -> list[Candidato]:
    precos = perfil.precos()
    dist_bins = max(1, int(dist_media * 0.40 / perfil.tick))
    c = _picos(perfil.volume, precos, dist_bins, "volume")
    c += _picos(perfil.tempo, precos, dist_bins, "tempo")
    return c


def candidatos_pivos(df: pd.DataFrame, timeframes: dict[str, int], n_lados: int = 3) -> list[Candidato]:
    """Pivos (fractais) detectados em varios tempos graficos reamostrados do M1."""
    base = df.set_index("DT")
    saida: list[Candidato] = []
    for regra, peso in timeframes.items():
        ohlc = base.resample(regra).agg(
            {"OPEN": "first", "HIGH": "max", "LOW": "min", "CLOSE": "last"}
        ).dropna()
        if len(ohlc) < 2 * n_lados + 5:
            continue
        h = ohlc["HIGH"].to_numpy()
        l = ohlc["LOW"].to_numpy()
        jan = 2 * n_lados + 1
        max_rol = pd.Series(h).rolling(jan, center=True).max().to_numpy()
        min_rol = pd.Series(l).rolling(jan, center=True).min().to_numpy()
        topos = np.flatnonzero((h == max_rol) & ~np.isnan(max_rol))
        fundos = np.flatnonzero((l == min_rol) & ~np.isnan(min_rol))
        for i in topos:
            saida.append(Candidato(float(h[i]), f"pivo_{regra}", peso))
        for i in fundos:
            saida.append(Candidato(float(l[i]), f"pivo_{regra}", peso))
    return saida


def candidatos_redondos(p_lo: float, p_hi: float, passo: float, peso: float = 0.8) -> list[Candidato]:
    inicio = np.ceil(p_lo / passo) * passo
    return [Candidato(float(p), "redondo", peso) for p in np.arange(inicio, p_hi + 1, passo)]


# ======================================================================
# 4. FUSAO EM CLUSTERES
# ======================================================================

@dataclass
class Nivel:
    preco: float
    fontes: set = field(default_factory=set)
    peso_fontes: float = 0.0
    # metricas preenchidas na medicao
    toques: int = 0
    rejeicoes: int = 0
    rompimentos: int = 0
    resolvidos: int = 0
    rej_pond: float = 0.0
    taxa_rej: float = 0.0
    vol_zona: float = 0.0
    tpo_zona: float = 0.0
    flip: bool = False
    ultimo_toque: pd.Timestamp | None = None
    idade_dias: float = 9e9
    recencia: float = 0.0
    relevancia: float = 0.0


def fundir(cands: list[Candidato], tolerancia: float, tick: float,
           dist_media: float) -> list[Nivel]:
    """
    Funde candidatos proximos em niveis.

    NAO usa aglomeracao por encadeamento (single-linkage): com candidatos densos
    ela encadeia tudo num punhado de grupos gigantes. Em vez disso, monta uma
    densidade ponderada no eixo de preco, suaviza com um kernel gaussiano de
    largura `tolerancia` e extrai os picos com separacao minima. O preco final de
    cada nivel e o centroide ponderado dos candidatos dentro da tolerancia.
    """
    if not cands:
        return []

    precos = np.array([c.preco for c in cands], dtype=float)
    pesos = np.array([c.peso for c in cands], dtype=float)

    p_min = float(precos.min() - 5 * tolerancia)
    p_max = float(precos.max() + 5 * tolerancia)
    n_bins = int(round((p_max - p_min) / tick)) + 1
    idx = np.clip(((precos - p_min) / tick).round().astype(np.int64), 0, n_bins - 1)
    dens = np.bincount(idx, weights=pesos, minlength=n_bins).astype(float)

    # kernel gaussiano
    sigma_bins = max(1.0, tolerancia / tick)
    raio = int(np.ceil(3 * sigma_bins))
    x = np.arange(-raio, raio + 1)
    kern = np.exp(-0.5 * (x / sigma_bins) ** 2)
    kern /= kern.sum()
    suave = np.convolve(dens, kern, mode="same")

    dist_bins = max(1, int(round(dist_media * 0.5 / tick)))
    picos, _ = find_peaks(suave, distance=dist_bins)
    if picos.size == 0:
        picos = np.array([int(np.argmax(suave))])

    ordem = np.argsort(precos)
    p_ord, w_ord = precos[ordem], pesos[ordem]
    fontes_ord = [cands[i].fonte for i in ordem]

    niveis: list[Nivel] = []
    for b in picos:
        centro = p_min + b * tick
        a = np.searchsorted(p_ord, centro - tolerancia, side="left")
        z = np.searchsorted(p_ord, centro + tolerancia, side="right")
        if z <= a:
            continue
        w = w_ord[a:z]
        p = p_ord[a:z]
        preco = float((p * w).sum() / w.sum()) if w.sum() > 0 else float(p.mean())
        nv = Nivel(preco=round(preco / tick) * tick)
        # mantem o tempo grafico do pivo: colapsar tudo em "pivo" limitava
        # n_fontes a 4 e jogava fora a confirmacao multi-timeframe, que e um
        # dos poucos sinais realmente independentes do perfil de volume.
        nv.fontes = set(fontes_ord[a:z])
        nv.peso_fontes = float(w.sum())
        niveis.append(nv)

    # remove duplicatas de preco geradas por picos vizinhos
    niveis.sort(key=lambda n: n.preco)
    limpos: list[Nivel] = []
    for n in niveis:
        if limpos and abs(n.preco - limpos[-1].preco) < tick:
            if n.peso_fontes > limpos[-1].peso_fontes:
                limpos[-1] = n
        else:
            limpos.append(n)
    return limpos


# ======================================================================
# 5. MEDICAO DE TOQUES / REJEICOES
# ======================================================================

def indice_fim_sessao(df: pd.DataFrame) -> np.ndarray:
    """Para cada barra, o indice da ULTIMA barra da sua sessao."""
    if "SESSAO" in df.columns:
        ses = df["SESSAO"].to_numpy()
    else:
        ses = df["DT"].dt.normalize().to_numpy()
    n = len(ses)
    fim = np.empty(n, np.int64)
    trocas = np.flatnonzero(ses[1:] != ses[:-1])
    ini = 0
    for t in trocas:
        fim[ini:t + 1] = t
        ini = t + 1
    fim[ini:] = n - 1
    return fim


def _incursoes(hi: np.ndarray, lo: np.ndarray, cl: np.ndarray,
               z_lo: float, z_hi: float, sep_barras: int):
    """
    Segmenta as visitas do preco a zona [z_lo, z_hi].

    Devolve (inicios, fins, de_baixo) ja filtrado: descarta a incursao que
    abre o historico (sem barra anterior para definir o sentido de chegada) e
    as entradas ambiguas (a barra anterior fechou DENTRO da zona).
    """
    idx = np.flatnonzero((hi >= z_lo) & (lo <= z_hi))
    if idx.size == 0:
        return np.empty(0, np.int64), np.empty(0, np.int64), np.empty(0, bool)

    cortes = np.flatnonzero(np.diff(idx) > sep_barras)
    inicios = np.concatenate(([idx[0]], idx[cortes + 1]))
    fins = np.concatenate((idx[cortes], [idx[-1]]))

    ant = inicios - 1
    ok = ant >= 0
    inicios, fins, ant = inicios[ok], fins[ok], ant[ok]
    if inicios.size == 0:
        return inicios, fins, np.empty(0, bool)

    c_ant = cl[ant]
    de_baixo = c_ant < z_lo
    de_cima = c_ant > z_hi
    val = de_baixo | de_cima          # descarta chegada ambigua
    return inicios[val], fins[val], de_baixo[val]


def _desfecho(b: int, de_baixo: bool, preco: float, mov_min: float,
              janela: int, fim_sessao: np.ndarray, ref: np.ndarray):
    """
    Resolve UM toque por barreira ORDENADA: o que o preco alcanca primeiro,
    `mov_min` a favor da rejeicao ou `mov_min` a favor do rompimento.

    Duas escolhas deliberadas, ambas medidas como decisivas no diagnostico:
      * a janela e cortada no fim da sessao (`fim_sessao`), senao o desfecho
        passa a ser decidido pelo gap noturno;
      * `ref` e a serie de FECHAMENTOS, nao maxima/minima. 30% das barras M1
        do WIN sao mais largas que a zona inteira, entao usar pavio faz as
        duas barreiras dispararem na mesma barra e o resultado vira ruido.

    Retorna +1 rejeitou, -1 rompeu, 0 indefinido (janela/sessao acabou antes).
    """
    f0 = b + 1
    f1 = min(fim_sessao[b] + 1, f0 + janela)
    if f1 <= f0:
        return 0

    trecho = ref[f0:f1]
    acima = np.flatnonzero(trecho >= preco + mov_min)
    abaixo = np.flatnonzero(trecho <= preco - mov_min)
    i_cima = acima[0] if acima.size else np.inf
    i_baixo = abaixo[0] if abaixo.size else np.inf
    if i_cima == np.inf and i_baixo == np.inf:
        return 0
    # rejeicao = anda contra o sentido de chegada
    if de_baixo:
        return 1 if i_baixo < i_cima else -1
    return 1 if i_cima < i_baixo else -1


def medir(nivel: Nivel, hi: np.ndarray, lo: np.ndarray, cl: np.ndarray,
          dias: np.ndarray, dt: np.ndarray, meia_zona: float, mov_min: float,
          janela: int, sep_barras: int, meia_vida: float, dia_final: float,
          fim_sessao: np.ndarray, ref: np.ndarray | None = None) -> None:
    """
    Um toque = incursao do preco na zona [P-z, P+z], separada da anterior por
    pelo menos `sep_barras` barras fora da zona.
    Rejeicao = apos sair, o preco anda `mov_min` CONTRA o sentido de chegada
    antes de andar `mov_min` a favor (ver `_desfecho`).

    `taxa_rej` usa como denominador apenas os toques RESOLVIDOS. Contar no
    denominador os toques cuja janela foi truncada (fim do historico ou da
    sessao) penalizava justamente os niveis mais recentes, que sao os que
    importam para operar.
    """
    p = nivel.preco
    z_lo, z_hi = p - meia_zona, p + meia_zona
    if ref is None:
        ref = cl

    inicios, fins, sentidos = _incursoes(hi, lo, cl, z_lo, z_hi, sep_barras)
    if inicios.size == 0:
        return

    rej_de_baixo = rej_de_cima = 0
    toques = rejeicoes = rompimentos = resolvidos = 0
    rej_pond = 0.0
    i_ultimo = None

    for a, b, de_baixo in zip(inicios, fins, sentidos):
        toques += 1
        i_ultimo = b

        r = _desfecho(b, bool(de_baixo), p, mov_min, janela, fim_sessao, ref)
        if r == 0:
            continue
        resolvidos += 1
        if r > 0:
            rejeicoes += 1
            rej_pond += 0.5 ** ((dia_final - dias[b]) / meia_vida)
            if de_baixo:
                rej_de_baixo += 1
            else:
                rej_de_cima += 1
        else:
            rompimentos += 1

    nivel.toques = toques
    nivel.rejeicoes = rejeicoes
    nivel.rompimentos = rompimentos
    nivel.resolvidos = resolvidos
    nivel.rej_pond = rej_pond
    nivel.taxa_rej = (rejeicoes + 1.0) / (resolvidos + 2.0)  # suavizacao de Laplace
    # flip exige lastro nos DOIS sentidos e algum equilibrio: com o criterio
    # antigo (>=2 de cada lado) 93% dos niveis eram flip, ou seja, a feature
    # nao separava nada e a cor do grafico virava enfeite.
    menor, maior = sorted((rej_de_baixo, rej_de_cima))
    nivel.flip = menor >= 3 and menor >= 0.40 * maior
    if i_ultimo is not None:
        nivel.ultimo_toque = pd.Timestamp(dt[i_ultimo])
        nivel.idade_dias = float(dia_final - dias[i_ultimo])
        nivel.recencia = 0.5 ** (nivel.idade_dias / meia_vida)


def eventos_toque(preco: float, hi: np.ndarray, lo: np.ndarray, cl: np.ndarray,
                  dt: np.ndarray, meia_zona: float, janela: int,
                  sep_barras: int, fim_sessao: np.ndarray,
                  mov_min: float = 0.0) -> list[dict]:
    """
    Devolve UM registro por toque. O lado da operacao e o fade (vende
    resistencia tocada por baixo, compra suporte tocado por cima).

    MFE/MAE aqui sao ORDENADOS: o MAE e o pior movimento ATE o instante em que
    o MFE maximo ocorreu. A versao anterior tirava max e min da mesma janela
    sem ordem nenhuma, o que reduzia `edge` a `2*(nivel - meio da faixa)` --
    um artefato de condicionar no sentido de chegada, identico para niveis
    reais e para precos sorteados (medido: +76 pts nos dois casos, t = -0.19).
    """
    z_lo, z_hi = preco - meia_zona, preco + meia_zona
    inicios, fins, sentidos = _incursoes(hi, lo, cl, z_lo, z_hi, sep_barras)
    saida: list[dict] = []

    for a, b, de_baixo in zip(inicios, fins, sentidos):
        f0 = b + 1
        f1 = min(fim_sessao[b] + 1, f0 + janela)   # nao atravessa a sessao
        if f1 <= f0:
            continue

        H, L = hi[f0:f1], lo[f0:f1]
        if de_baixo:                      # fade vendedor: ganha caindo
            fav, contra = preco - L, H - preco
        else:                             # fade comprador: ganha subindo
            fav, contra = H - preco, preco - L

        # excursao favoravel maxima e o pior contra ATE aquele momento
        i_mfe = int(np.argmax(fav))
        mfe = float(fav[i_mfe])
        mae = float(np.maximum.accumulate(contra)[i_mfe])

        ts = pd.Timestamp(dt[b])
        reg = {
            "dt": ts, "hora": ts.hour, "dow": ts.dayofweek,
            "de_baixo": bool(de_baixo),
            "mfe": max(0.0, mfe), "mae": max(0.0, mae),
            "edge": float(mfe - mae),
            "barras": int(f1 - f0),
        }
        if mov_min > 0:
            reg["res"] = _desfecho(b, bool(de_baixo), preco, mov_min,
                                   janela, fim_sessao, cl)
        saida.append(reg)
    return saida


# ======================================================================
# 6. SCORE
# ======================================================================

PESOS_PADRAO = {
    "rej_pond": 0.28,    # rejeicoes recentes (nao toques brutos)
    "taxa_rej": 0.22,    # qualidade: rejeitou mais do que rompeu?
    "vol_zona": 0.18,    # lastro de negocio na faixa
    "tpo_zona": 0.10,    # tempo-no-preco
    "n_fontes": 0.10,    # confirmacao por detectores independentes
    "flip": 0.07,        # ja inverteu polaridade
    "recencia": 0.05,    # quao recente foi o ultimo toque
}


def _rank_pct(v: np.ndarray) -> np.ndarray:
    if v.size == 0:
        return v
    s = pd.Series(v).rank(pct=True, method="average").to_numpy()
    return np.nan_to_num(s, nan=0.0)


def pontuar(niveis: list[Nivel], pesos: dict[str, float] = None) -> None:
    if not niveis:
        return
    pesos = pesos or PESOS_PADRAO
    cols = {
        "rej_pond": np.array([n.rej_pond for n in niveis]),
        "taxa_rej": np.array([n.taxa_rej for n in niveis]),
        "vol_zona": np.array([n.vol_zona for n in niveis]),
        "tpo_zona": np.array([n.tpo_zona for n in niveis]),
        "n_fontes": np.array([len(n.fontes) for n in niveis], dtype=float),
        "flip": np.array([1.0 if n.flip else 0.0 for n in niveis]),
        "recencia": np.array([n.recencia for n in niveis]),
    }
    score = np.zeros(len(niveis))
    for k, w in pesos.items():
        r = cols[k] if k == "flip" else _rank_pct(cols[k])
        score += w * r
    score = 100.0 * score / sum(pesos.values())
    for n, s in zip(niveis, score):
        n.relevancia = float(round(s, 1))


# ======================================================================
# 7. SELECAO
# ======================================================================

def selecionar(niveis: list[Nivel], preco_ref: float, n_lado: int,
               sep_min: float, min_toques: int, relev_min: float,
               min_resolvidos: int = 0) -> list[Nivel]:
    """
    Guloso por relevancia com separacao minima, N por lado.

    `n_lado` e um TETO, nao uma cota: com relev_min > 0 a saida pode ter menos
    linhas de um lado. Antes o corte de qualidade era inofensivo porque o
    fatiamento [:n_lado] enchia a lista com o que sobrasse -- por isso o .ntsl
    anterior colocava lado a lado niveis de relevancia 86 e de relevancia 9.
    """
    aptos = [n for n in niveis
             if n.toques >= min_toques
             and n.resolvidos >= min_resolvidos
             and n.relevancia >= relev_min]
    aptos.sort(key=lambda n: -n.relevancia)

    aceitos: list[Nivel] = []
    for n in aptos:
        if all(abs(n.preco - a.preco) >= sep_min for a in aceitos):
            aceitos.append(n)

    # dentro de cada lado fica com os mais PROXIMOS entre os que passaram no
    # corte de qualidade: para desenhar no grafico vale uma escada densa em
    # volta do preco, nao niveis otimos a milhares de pontos de distancia.
    acima = sorted([n for n in aceitos if n.preco > preco_ref],
                   key=lambda n: n.preco)[:n_lado]
    abaixo = sorted([n for n in aceitos if n.preco <= preco_ref],
                    key=lambda n: -n.preco)[:n_lado]
    return sorted(acima + abaixo, key=lambda n: -n.preco)


# ======================================================================
# 8. GERACAO DO NTSL
# ======================================================================

def cor_ntsl(n: Nivel, preco_ref: float) -> tuple[str, int, str]:
    """(cor, espessura, estilo) conforme lado e forca."""
    if n.relevancia >= 70:
        esp, estilo = 2, "psSolid"
    elif n.relevancia >= 50:
        esp, estilo = 1, "psSolid"
    else:
        esp, estilo = 1, "psDash"
    cor = "clRed" if n.preco > preco_ref else "clBlue"
    if n.flip:
        cor = "clFuchsia" if n.preco > preco_ref else "clTeal"
    return cor, esp, estilo


def gerar_ntsl(niveis: list[Nivel], preco_ref: float, args, info: dict) -> str:
    L: list[str] = []
    A = L.append
    A("//" + "=" * 70)
    A("// SR Automatico")
    A(f"// Gerado por gerar_sr.py em {datetime.now():%d/%m/%Y %H:%M}")
    A(f"// Janela analisada : {info['ini']:%d/%m/%Y %H:%M}  ->  {info['fim']:%d/%m/%Y %H:%M}")
    A(f"// Base             : {info['n_barras']} barras M1 | tick {args.tick:g} pts")
    A(f"// Criterios        : >= {args.min_toques} toques ({args.min_resolvidos} resolvidos) | "
      f"relevancia >= {args.relev_min:g} | zona +-{info['meia_zona']:.0f} pts | "
      f"mov. min {info['mov_min']:.0f} pts")
    A(f"// Escala medida    : barra M1 mediana {info['amp_m1']:.0f} pts | "
      f"amplitude diaria {info['amp_dia']:.0f} pts")
    A("// Desfecho         : barreira ordenada sobre FECHAMENTOS, cortada no fim da sessao")
    A(f"// Recencia         : meia-vida de {args.meia_vida:g} dias corridos")
    A(f"// Referencia       : {preco_ref:,.0f} ({sum(1 for n in niveis if n.preco > preco_ref)} acima / "
      f"{sum(1 for n in niveis if n.preco <= preco_ref)} abaixo)")
    espac = np.diff(sorted(n.preco for n in niveis))
    med = float(np.mean(espac)) if espac.size else 0.0
    A(f"// Niveis           : {len(niveis)} | separacao min. {info['sep_min']:.0f} pts | "
      f"espacamento medio obtido {med:.0f} pts")
    A("//" + "-" * 70)
    A("// #   Preco        Zona                    Toq  Res  Rej  Rom  TxRej  Flip  Relev")
    for i, n in enumerate(niveis, 1):
        zona = f"{n.preco - info['meia_zona']:,.0f} - {n.preco + info['meia_zona']:,.0f}"
        A(f"// {i:<3} {n.preco:<12,.0f} {zona:<23} {n.toques:<4} {n.resolvidos:<4} "
          f"{n.rejeicoes:<4} {n.rompimentos:<4} {n.taxa_rej:<6.2f} "
          f"{'S' if n.flip else '-':<5} {n.relevancia:.1f}")
    A("//" + "=" * 70)
    A("")
    A("input")
    A("  TamanhoTexto ( 9 );")
    A("  LocalTexto   ( 0 );  // posicao do rotulo sobre a linha")
    A("")
    A("begin")
    A("")
    A("  // Desenha UMA unica vez, na ultima barra do grafico.")
    A("  if LastBarOnChart then")
    A("  begin")
    A("")
    for i, n in enumerate(niveis, 1):
        cor, esp, estilo = cor_ntsl(n, preco_ref)
        dt_txt = n.ultimo_toque.strftime("%d/%m/%Y") if n.ultimo_toque is not None else "-"
        rot = f"R{n.relevancia:.0f} T{n.toques}" + ("*" if n.flip else "")
        A(f"    // Nivel {i}: toques={n.toques} | rejeicoes={n.rejeicoes} | "
          f"rompimentos={n.rompimentos} | relev={n.relevancia:.1f} | ultimo toque {dt_txt}")
        A(f'    HorizontalLineCustom( {n.preco:.2f}, {cor}, {esp}, {estilo}, "{rot}", '
          f"TamanhoTexto, LocalTexto, 0, 0, 0 );")
        A("")
    A("  end;")
    A("")
    A("end;")
    return "\n".join(L)


# ======================================================================
# 9. VALIDACAO OUT-OF-SAMPLE
# ======================================================================

def validar(df: pd.DataFrame, niveis_oos: list[Nivel], args, meia_zona: float,
            mov_min: float, n_aleatorios: int = 20) -> str:
    """
    Mede a taxa de rejeicao dos niveis num periodo NAO usado para constru-los,
    e compara com niveis sorteados na mesma faixa de precos (baseline).
    Se nao bater o baseline, o metodo e decorativo.
    """
    hi = df["HIGH"].to_numpy(float)
    lo = df["LOW"].to_numpy(float)
    cl = df["CLOSE"].to_numpy(float)
    dias = (df["DT"] - df["DT"].iloc[0]).dt.total_seconds().to_numpy() / 86400.0
    dt = df["DT"].to_numpy()

    fim_sessao = indice_fim_sessao(df)

    def taxa(precos: list[float]) -> tuple[float, int]:
        tot_t = tot_r = 0
        for p in precos:
            n = Nivel(preco=p)
            medir(n, hi, lo, cl, dias, dt, meia_zona, mov_min, args.janela,
                  args.sep_barras, args.meia_vida, dias[-1], fim_sessao)
            tot_t += n.resolvidos
            tot_r += n.rejeicoes
        return (tot_r / tot_t if tot_t else 0.0), tot_t

    precos_niveis = [n.preco for n in niveis_oos]
    if not precos_niveis:
        return "// Validacao: nenhum nivel para validar.\n"

    t_niv, n_toques = taxa(precos_niveis)

    p_lo, p_hi = min(precos_niveis), max(precos_niveis)
    rng = np.random.default_rng(42)
    amostras = []
    for _ in range(n_aleatorios):
        rnd = rng.uniform(p_lo, p_hi, size=len(precos_niveis))
        rnd = np.round(rnd / args.tick) * args.tick
        t, _ = taxa(list(rnd))
        amostras.append(t)
    base_m = float(np.mean(amostras))
    base_s = float(np.std(amostras))
    z = (t_niv - base_m) / base_s if base_s > 0 else float("nan")

    out = [
        "",
        "=" * 62,
        "VALIDACAO OUT-OF-SAMPLE",
        "=" * 62,
        f"Periodo             : {df['DT'].iloc[0]:%d/%m/%Y} -> {df['DT'].iloc[-1]:%d/%m/%Y}",
        f"Niveis testados     : {len(precos_niveis)}   (toques observados: {n_toques})",
        f"Taxa de rejeicao    : {t_niv:.3f}",
        f"Baseline aleatorio  : {base_m:.3f} +- {base_s:.3f}  (n={n_aleatorios})",
        f"Vantagem            : {(t_niv - base_m):+.3f}  |  z = {z:.2f}",
        "",
        "Leitura: z > 2 sugere que os niveis carregam informacao real.",
        "z proximo de 0 = os niveis nao sao melhores que precos sorteados.",
        "=" * 62,
    ]
    return "\n".join(out)


# ======================================================================
# 10. PIPELINE
# ======================================================================

def construir_niveis(df: pd.DataFrame, args, preco_ref: float) -> tuple[list[Nivel], dict]:
    tick = args.tick
    dist = args.dist_media
    meia_zona = dist * args.zona_frac
    mov_min = dist * args.mov_frac
    sep_min = dist * args.sep_frac

    esc = escala_ruido(df)
    if getattr(args, "auto_escala", True):
        # A zona precisa ser maior que o pavio tipico, senao "toque" vira ruido
        # intrabar. E o movimento minimo precisa ser grande em relacao ao que o
        # preco anda sozinho dentro da janela, senao rejeicao x rompimento e
        # cara-ou-coroa -- que era exatamente o caso (mov 160 pts para uma
        # variacao mediana de 265 pts em 90 barras).
        piso_zona = args.zona_atr * esc["amp_m1"]
        piso_mov = args.mov_atr * esc["amp_m1"] * np.sqrt(args.janela)
        meia_zona = max(meia_zona, piso_zona)
        mov_min = max(mov_min, piso_mov)
        sep_min = max(sep_min, 2.2 * meia_zona)

    dias = (df["DT"] - df["DT"].iloc[0]).dt.total_seconds().to_numpy() / 86400.0
    dia_final = float(dias[-1])
    # o perfil usa uma meia-vida MAIS LONGA: ele representa memoria estrutural
    # do mercado, nao a atualidade do nivel (essa entra como feature separada)
    peso_perfil = 0.5 ** ((dia_final - dias) / args.meia_vida_perfil)

    perfil = construir_perfil(df, tick, peso_recencia=peso_perfil)

    cands: list[Candidato] = []
    cands += candidatos_perfil(perfil, dist)
    cands += candidatos_pivos(df, {"15min": 0.6, "1h": 0.9, "4h": 1.2, "1D": 1.6},
                              n_lados=args.pivo_n)
    if args.redondos > 0:
        cands += candidatos_redondos(float(df["LOW"].min()), float(df["HIGH"].max()), args.redondos)

    # so interessa a vizinhanca da referencia
    alcance = args.linhas * dist * 1.8
    cands = [c for c in cands if abs(c.preco - preco_ref) <= alcance]

    niveis = fundir(cands, tolerancia=dist * args.fusao_frac, tick=tick, dist_media=dist)

    hi = df["HIGH"].to_numpy(float)
    lo = df["LOW"].to_numpy(float)
    cl = df["CLOSE"].to_numpy(float)
    dt = df["DT"].to_numpy()
    fim_sessao = indice_fim_sessao(df)

    for n in niveis:
        medir(n, hi, lo, cl, dias, dt, meia_zona, mov_min, args.janela,
              args.sep_barras, args.meia_vida, dia_final, fim_sessao)
        n.vol_zona, n.tpo_zona = perfil.na_zona(n.preco, meia_zona)

    pontuar(niveis)

    info = {
        "meia_zona": meia_zona, "mov_min": mov_min, "sep_min": sep_min,
        "n_barras": len(df), "ini": df["DT"].iloc[0], "fim": df["DT"].iloc[-1],
        "n_candidatos": len(cands), "n_clusters": len(niveis),
        "amp_m1": esc["amp_m1"], "amp_dia": esc["amp_dia"],
        "fim_sessao": fim_sessao,
    }
    return niveis, info


def main() -> int:
    ap = argparse.ArgumentParser(description="Gera niveis de S/R do WIN e o codigo NTSL.")
    ap.add_argument("--csv", required=True, help="Export M1 do MT5 (tsv/csv)")
    ap.add_argument("--saida", default="SR_Automatico.src", help="Arquivo .src de saida")

    # --- os 4 parametros pedidos ---
    ap.add_argument("--preco-ref", type=float, default=None,
                    help="Preco de referencia (padrao: fechamento na data-limite)")
    ap.add_argument("--linhas", type=int, default=20,
                    help="Numero de linhas acima E abaixo da referencia")
    ap.add_argument("--dist-media", type=float, default=250.0,
                    help="Distancia media esperada entre niveis, em pontos")
    ap.add_argument("--data-limite", default=None,
                    help="Data final a considerar (AAAA-MM-DD)")
    ap.add_argument("--data-inicio", default=None, help="Data inicial (padrao: inicio do arquivo)")

    # --- ajustes finos ---
    ap.add_argument("--tick", type=float, default=5.0, help="Tamanho do tick (WIN=5)")
    ap.add_argument("--zona-frac", type=float, default=0.22,
                    help="Meia-largura da zona como fracao de dist-media")
    ap.add_argument("--sep-frac", type=float, default=0.85,
                    help="Separacao minima entre niveis como fracao de dist-media")
    ap.add_argument("--fusao-frac", type=float, default=0.18,
                    help="Tolerancia de fusao de candidatos como fracao de dist-media")
    ap.add_argument("--mov-frac", type=float, default=0.80,
                    help="Movimento minimo p/ caracterizar rejeicao/rompimento (fracao de dist-media)")
    ap.add_argument("--janela", type=int, default=90, help="Barras M1 para avaliar o desfecho do toque")
    ap.add_argument("--sep-barras", type=int, default=30, help="Barras fora da zona p/ novo toque")
    ap.add_argument("--meia-vida", type=float, default=90.0,
                    help="Meia-vida da recencia do ultimo toque, em dias")
    ap.add_argument("--meia-vida-perfil", type=float, default=365.0,
                    help="Meia-vida do perfil de volume/tempo, em dias")
    ap.add_argument("--pivo-n", type=int, default=3, help="Barras de cada lado para pivo")
    ap.add_argument("--redondos", type=float, default=1000.0,
                    help="Passo dos numeros redondos (0 desativa)")
    ap.add_argument("--min-toques", type=int, default=3)
    ap.add_argument("--min-resolvidos", type=int, default=3,
                    help="Toques com desfecho conhecido exigidos por nivel")
    ap.add_argument("--relev-min", type=float, default=45.0,
                    help="Relevancia minima; corta a cauda fraca (0 desativa)")
    ap.add_argument("--auto-escala", dest="auto_escala", action="store_true", default=True,
                    help="Dimensiona zona/movimento pela volatilidade medida (padrao)")
    ap.add_argument("--sem-auto-escala", dest="auto_escala", action="store_false",
                    help="Usa apenas as fracoes de dist-media, sem piso de ruido")
    ap.add_argument("--zona-atr", type=float, default=1.2,
                    help="Piso da meia-zona em amplitudes M1 medianas")
    ap.add_argument("--mov-atr", type=float, default=0.55,
                    help="Piso do movimento minimo em amplitudes M1 * sqrt(janela)")
    ap.add_argument("--csv-saida", default=None, help="CSV com as metricas de todos os niveis")
    ap.add_argument("--validar", action="store_true", help="Roda validacao out-of-sample")
    ap.add_argument("--meses-holdout", type=int, default=12)
    args = ap.parse_args()

    print(f"Lendo {args.csv} ...")
    df = carregar(args.csv, args.data_inicio, args.data_limite)
    print(f"  {len(df):,} barras  |  {df['DT'].iloc[0]:%d/%m/%Y} -> {df['DT'].iloc[-1]:%d/%m/%Y}")

    preco_ref = args.preco_ref if args.preco_ref is not None else float(df["CLOSE"].iloc[-1])
    print(f"  Referencia: {preco_ref:,.0f}")

    niveis, info = construir_niveis(df, args, preco_ref)
    print(f"  Candidatos: {info['n_candidatos']}  ->  clusteres: {info['n_clusters']}")

    print(f"  Escala: barra M1 mediana {info['amp_m1']:.0f} pts | "
          f"amplitude diaria {info['amp_dia']:.0f} pts")
    print(f"  Zona +-{info['meia_zona']:.0f} | mov. min {info['mov_min']:.0f} | "
          f"separacao {info['sep_min']:.0f} pts")

    escolhidos = selecionar(niveis, preco_ref, args.linhas, info["sep_min"],
                            args.min_toques, args.relev_min, args.min_resolvidos)
    print(f"  Selecionados: {len(escolhidos)} niveis "
          f"({sum(1 for n in escolhidos if n.preco > preco_ref)} acima / "
          f"{sum(1 for n in escolhidos if n.preco <= preco_ref)} abaixo)")

    src = gerar_ntsl(escolhidos, preco_ref, args, info)
    with open(args.saida, "w", encoding="utf-8") as f:
        f.write(src)
    print(f"  NTSL gravado em {args.saida}")

    if args.csv_saida:
        pd.DataFrame([{
            "preco": n.preco, "relevancia": n.relevancia, "toques": n.toques,
            "resolvidos": n.resolvidos,
            "rejeicoes": n.rejeicoes, "rompimentos": n.rompimentos,
            "taxa_rej": round(n.taxa_rej, 4), "rej_pond": round(n.rej_pond, 3),
            "vol_zona": n.vol_zona, "tpo_zona": n.tpo_zona,
            "n_fontes": len(n.fontes), "fontes": "|".join(sorted(n.fontes)),
            "flip": n.flip, "idade_dias": round(n.idade_dias, 1),
            "ultimo_toque": n.ultimo_toque,
            "selecionado": any(abs(n.preco - e.preco) < 1e-6 for e in escolhidos),
        } for n in sorted(niveis, key=lambda x: -x.relevancia)]).to_csv(
            args.csv_saida, index=False)
        print(f"  Metricas gravadas em {args.csv_saida}")

    if args.validar:
        corte = df["DT"].iloc[-1] - pd.DateOffset(months=args.meses_holdout)
        treino = df[df["DT"] <= corte].reset_index(drop=True)
        teste = df[df["DT"] > corte].reset_index(drop=True)
        if len(treino) < 5000 or len(teste) < 2000:
            print("  Historico insuficiente para validar.")
        else:
            ref_treino = float(treino["CLOSE"].iloc[-1])
            niv_t, info_t = construir_niveis(treino, args, ref_treino)
            esc_t = selecionar(niv_t, ref_treino, args.linhas, info_t["sep_min"],
                               args.min_toques, args.relev_min, args.min_resolvidos)
            print(validar(teste, esc_t, args, info_t["meia_zona"], info_t["mov_min"]))

    return 0


if __name__ == "__main__":
    sys.exit(main())