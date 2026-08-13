#!/usr/bin/env python
"""Atualiza o CSV de candles de 1 minuto do WIN$N a partir do MetaTrader 5.

Le o arquivo existente, baixa o historico do terminal MT5, funde os dois
(o MT5 tem prioridade nas barras coincidentes, o CSV preserva o que o
terminal ja nao serve mais) e regrava no mesmo formato de export do MT5:

    <DATE>\\t<TIME>\\t<OPEN>\\t<HIGH>\\t<LOW>\\t<CLOSE>\\t<TICKVOL>\\t<VOL>\\t<SPREAD>

Cada execucao imprime um resumo e acrescenta um bloco ao log.

Uso tipico:
    python atualiza-historico.py
    python atualiza-historico.py --dry-run
    python atualiza-historico.py --desde 2021-01-01 --symbol WIN$N
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import traceback
from datetime import datetime, timedelta, timezone

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

# copy_rates_range devolve (-2, 'Invalid params') acima de ~200k barras por
# chamada; 150 dias de WIN dao ~57k barras, com folga confortavel.
CHUNK_DIAS = 150

# Colunas do arquivo, na ordem do export do MT5.
COLS = ["open", "high", "low", "close", "tickvol", "vol", "spread"]
HEADER = "<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>"
UTC = timezone.utc


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
def ler_csv(path: str) -> pd.DataFrame:
    """Le o export do MT5 e devolve DataFrame indexado por datetime."""
    if not os.path.exists(path):
        return pd.DataFrame(columns=COLS, index=pd.DatetimeIndex([], name="datetime"))

    df = pd.read_csv(path, sep="\t", dtype={"<DATE>": "string", "<TIME>": "string"}, engine="c")
    df.columns = [c.strip().strip("<>").lower() for c in df.columns]
    dt = pd.to_datetime(df["date"] + " " + df["time"], format="%Y.%m.%d %H:%M:%S")

    out = pd.DataFrame(index=pd.DatetimeIndex(dt, name="datetime"))
    for c in COLS:
        # .to_numpy() e obrigatorio: atribuir a Series (RangeIndex) a um frame
        # com DatetimeIndex faria o pandas alinhar por indice e zerar tudo.
        out[c] = (
            pd.to_numeric(df[c], errors="coerce").fillna(0).astype("int64").to_numpy()
            if c in df.columns
            else 0
        )
    out = out.sort_index()
    return out[~out.index.duplicated(keep="last")]


def escrever_csv(df: pd.DataFrame, path: str) -> None:
    """Regrava no formato do MT5 (tab, CRLF), de forma atomica."""
    saida = pd.DataFrame(index=df.index)
    saida.insert(0, "<DATE>", df.index.strftime("%Y.%m.%d"))
    saida.insert(1, "<TIME>", df.index.strftime("%H:%M:%S"))
    for nome, c in zip(
        ["<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>", "<TICKVOL>", "<VOL>", "<SPREAD>"], COLS
    ):
        saida[nome] = df[c].astype("int64")

    tmp = path + ".tmp"
    saida.to_csv(tmp, sep="\t", index=False, lineterminator="\r\n")
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
    if not ti.connected:
        raise RuntimeError("terminal sem conexao com o servidor de dados")


def baixar(symbol: str, desde: datetime, ate: datetime, chunk_dias: int, log: Log) -> pd.DataFrame:
    """Baixa candles M1 em blocos e devolve DataFrame indexado por datetime.

    Os timestamps do MT5 sao segundos na timezone do servidor; mantemos o
    horario do servidor (mesma referencia do export manual do terminal).
    """
    info = mt5.symbol_info(symbol)
    if info is None:
        raise RuntimeError(f"simbolo {symbol} nao existe neste terminal")
    if not info.visible and not mt5.symbol_select(symbol, True):
        raise RuntimeError(f"nao consegui habilitar o simbolo {symbol}: {mt5.last_error()}")

    partes: list[pd.DataFrame] = []
    inicio = desde
    passo = timedelta(days=chunk_dias)
    while inicio < ate:
        fim = min(inicio + passo, ate)
        rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, inicio, fim)
        if rates is None:
            raise RuntimeError(
                f"copy_rates_range falhou em {inicio:%Y-%m-%d}..{fim:%Y-%m-%d}: {mt5.last_error()}"
            )
        if len(rates):
            partes.append(pd.DataFrame(rates))
        inicio = fim

    if not partes:
        return pd.DataFrame(columns=COLS, index=pd.DatetimeIndex([], name="datetime"))

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

    # WIN tem digits=0; arredonda para o tick antes de virar inteiro.
    escala = 10 ** info.digits
    for c in ["open", "high", "low", "close"]:
        out[c] = (out[c] * escala).round().astype("int64")
    for c in ["tickvol", "vol", "spread"]:
        out[c] = out[c].astype("int64")

    out = out.sort_index()
    out = out[~out.index.duplicated(keep="last")]
    log(f"MT5      : {len(out):,} barras baixadas em {len(partes)} blocos".replace(",", "."))
    return out


# --------------------------------------------------------------------------
# principal
# --------------------------------------------------------------------------
def periodo(df: pd.DataFrame) -> str:
    if df.empty:
        return "vazio"
    return f"{df.index[0]:%Y-%m-%d %H:%M} -> {df.index[-1]:%Y-%m-%d %H:%M}"


def main() -> int:
    p = argparse.ArgumentParser(description="Atualiza o CSV de 1 minuto do WIN$N via MetaTrader 5.")
    p.add_argument("--symbol", default=SYMBOL, help=f"simbolo no MT5 (padrao: {SYMBOL})")
    p.add_argument("--csv", default=CSV_PATH, help="arquivo CSV a atualizar")
    p.add_argument("--log", default=LOG_PATH, help="arquivo de log (append)")
    p.add_argument("--desde", default=DESDE, help=f"data inicial do download (padrao: {DESDE})")
    p.add_argument("--chunk-dias", type=int, default=CHUNK_DIAS, help="dias por requisicao ao MT5")
    p.add_argument("--terminal", default=None, help="caminho do terminal64.exe (opcional)")
    p.add_argument("--sem-backup", action="store_true", help="nao gerar o .bak do arquivo anterior")
    p.add_argument("--sem-barra-atual", action="store_true",
                   help="descarta a ultima barra (util se o pregao estiver aberto)")
    p.add_argument("--dry-run", action="store_true", help="mostra o que mudaria sem gravar")
    args = p.parse_args()

    log = Log(args.log)
    conectado = False
    try:
        desde = datetime.fromisoformat(args.desde).replace(tzinfo=UTC)
        agora = datetime.now(UTC)

        log(f"Simbolo  : {args.symbol} M1 | desde {desde:%Y-%m-%d}")
        log(f"Arquivo  : {args.csv}")

        antigo = ler_csv(args.csv)
        log(f"Atual    : {len(antigo):,} barras | {periodo(antigo)}".replace(",", "."))

        conectar(args.terminal, log)
        conectado = True
        novo = baixar(args.symbol, desde, agora, args.chunk_dias, log)

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
            dif = (novo.loc[comuns, COLS].to_numpy() != antigo.loc[comuns, COLS].to_numpy())
            alteradas = int(dif.any(axis=1).sum())

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

        if not args.sem_backup and os.path.exists(args.csv):
            bak = args.csv + ".bak"
            shutil.copy2(args.csv, bak)
            log(f"Backup   : {bak}")

        escrever_csv(fundido, args.csv)
        mb = os.path.getsize(args.csv) / (1024 * 1024)
        log(f"Gravado  : {args.csv} ({mb:.1f} MB)")
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
