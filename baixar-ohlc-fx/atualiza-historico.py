#!/usr/bin/env python
"""Atualiza o CSV de candles de 1 minuto de um simbolo a partir do MetaTrader 5.

Le o arquivo existente, baixa o historico do terminal MT5, funde os dois
(o MT5 tem prioridade nas barras coincidentes, o CSV preserva o que o
terminal ja nao serve mais) e regrava no mesmo formato de export do MT5:

    <DATE>\\t<TIME>\\t<OPEN>\\t<HIGH>\\t<LOW>\\t<CLOSE>\\t<TICKVOL>\\t<VOL>\\t<SPREAD>

Os precos saem com as casas decimais do simbolo (WIN tem digits=0, ou seja,
inteiro; USDJPY tem digits=3).

Cada execucao imprime um resumo e acrescenta um bloco ao log.

Uso tipico:
    python atualiza-historico.py
    python atualiza-historico.py --dry-run
    python atualiza-historico.py --desde 2021-01-01 --symbol WIN$N
    python atualiza-historico.py --symbol USDJPY --desde 2026-05-01
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import traceback
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

try:
    import MetaTrader5 as mt5
except ImportError:  # pragma: no cover
    sys.exit("MetaTrader5 nao instalado. Rode: pip install MetaTrader5")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SYMBOL = "WIN$N"
CSV_PATH = os.path.join(BASE_DIR, "WIN$N_M1_202108120900_202608111824.csv")
LOG_PATH = os.path.join(BASE_DIR, "atualiza-historico.log")
DESDE = "2021-01-01"

# Teto de dias por requisicao. E so um limite superior: o valor efetivo tambem
# respeita o "Max. barras no grafico" do terminal -- veja passo_inicial().
CHUNK_DIAS = 150
MINUTOS_DIA = 1440

# Margem para descartar a barra-sentinela que o MT5 devolve quando o periodo
# pedido esta fora do historico disponivel. Cobre a diferenca entre a hora do
# servidor e o UTC dos parametros, sem cortar barras legitimas da borda.
MARGEM = timedelta(days=2)

# Colunas do arquivo, na ordem do export do MT5.
PRECO_COLS = ["open", "high", "low", "close"]
INT_COLS = ["tickvol", "vol", "spread"]
COLS = PRECO_COLS + INT_COLS
NOMES = ["<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>", "<TICKVOL>", "<VOL>", "<SPREAD>"]
HEADER = "<DATE>\t<TIME>\t" + "\t".join(NOMES)
UTC = timezone.utc

# Caracteres proibidos em nome de arquivo no Windows (o $ do WIN$N e valido).
INVALIDOS = '<>:"/\\|?*'


# --------------------------------------------------------------------------
# log
# --------------------------------------------------------------------------
class Log:
    """Escreve na tela e acumula as linhas para gravar no arquivo de log."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.linhas: list[str] = []

    def __call__(self, msg: str = "") -> None:
        print(msg)
        self.linhas.append(msg)

    def gravar(self, status: str) -> None:
        carimbo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        bloco = [
            "=" * 72,
            f"[{carimbo}] {status}",
            "-" * 72,
            *self.linhas,
            "",
        ]
        try:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write("\n".join(bloco) + "\n")
        except OSError as exc:
            print(f"AVISO: nao consegui gravar o log em {self.path}: {exc}")


# --------------------------------------------------------------------------
# leitura / escrita do CSV
# --------------------------------------------------------------------------
def frame_vazio() -> pd.DataFrame:
    """DataFrame sem linhas, ja com o indice e os dtypes definitivos."""
    out = pd.DataFrame(index=pd.DatetimeIndex([], name="datetime"))
    for c in PRECO_COLS:
        out[c] = pd.Series(dtype="float64")
    for c in INT_COLS:
        out[c] = pd.Series(dtype="int64")
    return out


def ler_csv(path: str) -> pd.DataFrame:
    """Le o export do MT5 e devolve DataFrame indexado por datetime."""
    if not os.path.exists(path):
        return frame_vazio()

    df = pd.read_csv(path, sep="\t", dtype={"<DATE>": "string", "<TIME>": "string"}, engine="c")
    df.columns = [c.strip().strip("<>").lower() for c in df.columns]
    dt = pd.to_datetime(df["date"] + " " + df["time"], format="%Y.%m.%d %H:%M:%S")

    out = pd.DataFrame(index=pd.DatetimeIndex(dt, name="datetime"))
    for c in COLS:
        # .to_numpy() e obrigatorio: atribuir a Series (RangeIndex) a um frame
        # com DatetimeIndex faria o pandas alinhar por indice e zerar tudo.
        out[c] = (
            pd.to_numeric(df[c], errors="coerce").fillna(0).to_numpy()
            if c in df.columns
            else 0
        )
    # Preco fica em float (WIN grava com 0 casas, FX com as casas do simbolo).
    out[PRECO_COLS] = out[PRECO_COLS].astype("float64")
    out[INT_COLS] = out[INT_COLS].astype("int64")
    out = out.sort_index()
    return out[~out.index.duplicated(keep="last")]


def escrever_csv(df: pd.DataFrame, path: str, digits: int) -> None:
    """Regrava no formato do MT5 (tab, CRLF), de forma atomica."""
    saida = pd.DataFrame(index=df.index)
    saida.insert(0, "<DATE>", df.index.strftime("%Y.%m.%d"))
    saida.insert(1, "<TIME>", df.index.strftime("%H:%M:%S"))
    for nome, c in zip(NOMES, COLS):
        saida[nome] = df[c].to_numpy()

    tmp = path + ".tmp"
    # float_format so alcanca as colunas de preco; volume e spread sao int64.
    saida.to_csv(tmp, sep="\t", index=False, lineterminator="\r\n",
                 float_format=f"%.{digits}f")
    os.replace(tmp, path)


# --------------------------------------------------------------------------
# MetaTrader 5
# --------------------------------------------------------------------------
def conectar(terminal: str | None, log: Log) -> None:
    ok = mt5.initialize(terminal) if terminal else mt5.initialize()
    if not ok:
        raise RuntimeError(f"mt5.initialize() falhou: {mt5.last_error()}")

    ti = mt5.terminal_info()
    ai = mt5.account_info()
    log(f"Terminal : {ti.name} build {ti.build} ({ti.data_path})")
    log(f"Conta    : {ai.login if ai else '-'} @ {ai.server if ai else '-'} | conectado={ti.connected}")
    log(f"Max bars : {ti.maxbars:,}".replace(",", "."))
    if not ti.connected:
        raise RuntimeError("terminal sem conexao com o servidor de dados")


def preparar_simbolo(symbol: str):
    """Valida o simbolo, habilita no Market Watch e devolve o symbol_info."""
    info = mt5.symbol_info(symbol)
    if info is None:
        raise RuntimeError(f"simbolo {symbol} nao existe neste terminal")
    if not info.visible:
        if not mt5.symbol_select(symbol, True):
            raise RuntimeError(f"nao consegui habilitar o simbolo {symbol}: {mt5.last_error()}")
        info = mt5.symbol_info(symbol)
    return info


def passo_inicial(chunk_dias: int) -> timedelta:
    """Maior bloco aceito pelo terminal, em dias.

    copy_rates_range devolve (-2, 'Invalid params') quando o INTERVALO pedido,
    medido em barras do timeframe, alcanca o "Max. barras no grafico" do
    terminal (Ferramentas > Opcoes > Graficos). O que conta e o calendario, nao
    quantas barras existem la dentro: em M1 com maxbars=100.000 o teto e ~69
    dias, mesmo que o periodo so tenha 45k barras negociadas.
    """
    maxbars = mt5.terminal_info().maxbars
    if maxbars <= 0:  # "Unlimited"
        return timedelta(days=chunk_dias)
    teto = max(1, int(maxbars * 0.9) // MINUTOS_DIA)
    return timedelta(days=min(chunk_dias, teto))


def baixar(info, desde: datetime, ate: datetime, chunk_dias: int, log: Log) -> pd.DataFrame:
    """Baixa candles M1 em blocos e devolve DataFrame indexado por datetime.

    Os timestamps do MT5 sao segundos na timezone do servidor; mantemos o
    horario do servidor (mesma referencia do export manual do terminal).
    """
    symbol = info.name
    partes: list[pd.DataFrame] = []
    inicio = desde
    passo = passo_inicial(chunk_dias)
    if passo < timedelta(days=chunk_dias):
        log(f"Blocos   : {passo.days} dias por requisicao (limitado pelo Max bars do terminal)")

    while inicio < ate:
        fim = min(inicio + passo, ate)
        rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, inicio, fim)
        if rates is None:
            erro = mt5.last_error()
            # -2 aqui e quase sempre bloco grande demais: corta pela metade.
            if erro[0] == -2 and passo > timedelta(days=1):
                passo = timedelta(days=max(1, passo.days // 2))
                log(f"Ajuste   : {erro[1]} em {inicio:%Y-%m-%d}; bloco reduzido para {passo.days} dias")
                continue
            raise RuntimeError(
                f"copy_rates_range falhou em {inicio:%Y-%m-%d}..{fim:%Y-%m-%d}: {erro}"
            )
        if len(rates):
            bloco = pd.DataFrame(rates)
            # Fora do historico disponivel o MT5 devolve uma barra qualquer da
            # borda do que ele tem; ela nao pertence ao periodo pedido.
            dentro = bloco["time"].between(
                (inicio - MARGEM).timestamp(), (fim + MARGEM).timestamp()
            )
            if dentro.any():
                partes.append(bloco[dentro])
        inicio = fim

    if not partes:
        return frame_vazio()

    raw = pd.concat(partes, ignore_index=True)
    idx = pd.DatetimeIndex(pd.to_datetime(raw["time"], unit="s"), name="datetime")
    out = pd.DataFrame(index=idx)
    out["open"] = raw["open"].to_numpy()
    out["high"] = raw["high"].to_numpy()
    out["low"] = raw["low"].to_numpy()
    out["close"] = raw["close"].to_numpy()
    out["tickvol"] = raw["tick_volume"].to_numpy()
    out["vol"] = raw["real_volume"].to_numpy()
    out["spread"] = raw["spread"].to_numpy()

    # Arredonda ao tick do simbolo (WIN digits=0 -> inteiro; USDJPY -> 3 casas).
    out[PRECO_COLS] = out[PRECO_COLS].astype("float64").round(info.digits)
    out[INT_COLS] = out[INT_COLS].astype("int64")

    out = out.sort_index()
    out = out[~out.index.duplicated(keep="last")]
    log(f"MT5      : {len(out):,} barras baixadas em {len(partes)} blocos".replace(",", "."))

    faltando = out.index[0] - pd.Timestamp(desde.replace(tzinfo=None))
    if faltando > pd.Timedelta(days=3):
        log(f"AVISO    : o terminal so serve M1 de {symbol} a partir de {out.index[0]:%Y-%m-%d %H:%M} "
            f"({faltando.days} dias depois do --desde pedido).")
        log("           Para ir mais fundo, ponha Ferramentas > Opcoes > Graficos >"
            " 'Max. barras no grafico' em Unlimited e rode de novo.")
    return out


# --------------------------------------------------------------------------
# principal
# --------------------------------------------------------------------------
def periodo(df: pd.DataFrame) -> str:
    if df.empty:
        return "vazio"
    return f"{df.index[0]:%Y-%m-%d %H:%M} -> {df.index[-1]:%Y-%m-%d %H:%M}"


def caminho_csv(symbol: str) -> str:
    """Arquivo padrao do simbolo. O WIN mantem o nome do export original."""
    if symbol == SYMBOL:
        return CSV_PATH
    nome = "".join("_" if c in INVALIDOS else c for c in symbol)
    return os.path.join(BASE_DIR, f"{nome}_M1.csv")


def main() -> int:
    p = argparse.ArgumentParser(description="Atualiza o CSV de 1 minuto do WIN$N via MetaTrader 5.")
    p.add_argument("--symbol", default=SYMBOL, help=f"simbolo no MT5 (padrao: {SYMBOL})")
    p.add_argument("--csv", default=None,
                   help="arquivo CSV a atualizar (padrao: derivado do simbolo)")
    p.add_argument("--log", default=LOG_PATH, help="arquivo de log (append)")
    p.add_argument("--desde", default=DESDE, help=f"data inicial do download (padrao: {DESDE})")
    p.add_argument("--chunk-dias", type=int, default=CHUNK_DIAS,
                   help="teto de dias por requisicao ao MT5 (o Max bars do terminal pode reduzir)")
    p.add_argument("--terminal", default=None, help="caminho do terminal64.exe (opcional)")
    p.add_argument("--sem-backup", action="store_true", help="nao gerar o .bak do arquivo anterior")
    p.add_argument("--sem-barra-atual", action="store_true",
                   help="descarta a ultima barra (util se o pregao estiver aberto)")
    p.add_argument("--dry-run", action="store_true", help="mostra o que mudaria sem gravar")
    args = p.parse_args()

    log = Log(args.log)
    conectado = False
    csv_path = args.csv or caminho_csv(args.symbol)
    try:
        desde = datetime.fromisoformat(args.desde).replace(tzinfo=UTC)
        agora = datetime.now(UTC)

        log(f"Simbolo  : {args.symbol} M1 | desde {desde:%Y-%m-%d}")
        log(f"Arquivo  : {csv_path}")

        antigo = ler_csv(csv_path)
        log(f"Atual    : {len(antigo):,} barras | {periodo(antigo)}".replace(",", "."))

        conectar(args.terminal, log)
        conectado = True
        info = preparar_simbolo(args.symbol)
        novo = baixar(info, desde, agora, args.chunk_dias, log)

        # Com o pregao aberto a ultima barra ainda esta se formando. Ela e
        # mantida de proposito: a fusao da prioridade ao MT5, entao a proxima
        # execucao sobrescreve o valor parcial pelo fechado. Use
        # --sem-barra-atual para nunca gravar barra parcial.
        if args.sem_barra_atual and len(novo) > 1:
            descartada = novo.index[-1]
            novo = novo.iloc[:-1]
            log(f"Descarte : ultima barra {descartada:%Y-%m-%d %H:%M} removida")

        if novo.empty:
            raise RuntimeError("o MT5 nao devolveu nenhuma barra no periodo pedido")

        # --- funde: nas barras coincidentes vale o MT5 ---
        novas_idx = novo.index.difference(antigo.index)
        comuns = novo.index.intersection(antigo.index)
        alteradas = 0
        if len(comuns):
            # Meio tick de tolerancia: o preco vai e volta do arquivo em decimal,
            # entao comparacao exata de float acusaria diferenca inexistente.
            tol = 10.0 ** -info.digits / 2
            a = novo.loc[comuns, COLS].to_numpy(dtype="float64")
            b = antigo.loc[comuns, COLS].to_numpy(dtype="float64")
            alteradas = int((np.abs(a - b) > tol).any(axis=1).sum())

        fundido = pd.concat([antigo, novo])
        fundido = fundido[~fundido.index.duplicated(keep="last")].sort_index()

        log("")
        log(f"Novas    : {len(novas_idx):,} barras".replace(",", "."))
        if len(novas_idx):
            log(f"           de {novas_idx[0]:%Y-%m-%d %H:%M} ate {novas_idx[-1]:%Y-%m-%d %H:%M}")
        log(f"Corrigidas: {alteradas:,} barras ja existentes".replace(",", "."))
        log(f"Preservadas: {len(antigo.index.difference(novo.index)):,} barras que o MT5 nao serve mais"
            .replace(",", "."))
        log(f"Resultado : {len(fundido):,} barras | {periodo(fundido)}".replace(",", "."))

        if args.dry_run:
            log("")
            log("DRY-RUN: nada foi gravado.")
            log.gravar("DRY-RUN")
            return 0

        if len(novas_idx) == 0 and alteradas == 0:
            log("")
            log("Nada a fazer: o arquivo ja esta atualizado.")
            log.gravar("SEM MUDANCAS")
            return 0

        if not args.sem_backup and os.path.exists(csv_path):
            bak = csv_path + ".bak"
            shutil.copy2(csv_path, bak)
            log(f"Backup   : {bak}")

        escrever_csv(fundido, csv_path, info.digits)
        mb = os.path.getsize(csv_path) / (1024 * 1024)
        log(f"Gravado  : {csv_path} ({mb:.1f} MB)")
        log("")
        log("SUCESSO.")
        log.gravar("SUCESSO")
        return 0

    except Exception as exc:
        log("")
        log(f"FALHA: {exc}")
        log(traceback.format_exc().rstrip())
        log.gravar("FALHA")
        return 1
    finally:
        if conectado:
            mt5.shutdown()


if __name__ == "__main__":
    sys.exit(main())
