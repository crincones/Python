"""Lista dos ativos com opções mais líquidas da B3 (top N por volume financeiro das opções).

Fonte: arquivos públicos da B3 (sem login), baixados na hora:
  - InstrumentsConsolidatedFile: cadastro, para saber o ativo-objeto de cada opção;
  - TradeInformationConsolidatedFile: negócios do dia, dos últimos N pregões publicados.

Liquidez = volume financeiro médio por pregão somando todas as séries (calls e puts) de cada
ativo-objeto. Saída: lista_opcoes_liquidez.csv nesta pasta (';' e vírgula decimal, para Excel).

Uso: gerar_lista.bat (ou: python gerar_lista.py [--top 20] [--pregoes 5]). Só biblioteca padrão.
"""

from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import io
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://arquivos.b3.com.br/api/download"
OPTION_SEGMENTS = {"EQUITY CALL", "EQUITY PUT"}
OPTION_CATEGORIES = {"OPTION ON EQUITIES", "OPTION ON INDEX"}
MAX_DAYS_BACK = 30
OUT = Path(__file__).resolve().parent / "lista_opcoes_liquidez.csv"


def download(file_name: str, day: dt.date) -> str | None:
    """Arquivo da B3 de um dia (texto) ou None se não publicado."""
    url = f"{BASE}/requestname?fileName={file_name}&date={day.isoformat()}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            token = json.loads(resp.read().decode("utf-8")).get("token")
        if not token:
            return None
        with urllib.request.urlopen(f"{BASE}/?token={token}", timeout=120) as resp:
            data = resp.read()
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None
    if len(data) < 1000:
        return None
    return data.decode("latin-1")


def rows(text: str) -> csv.DictReader:
    status, _, body = text.partition("\n")  # 1ª linha: "Status do Arquivo: …"
    if "final" not in status.lower():
        raise ValueError(f"arquivo não final: {status.strip()}")
    return csv.DictReader(io.StringIO(body), delimiter=";")


def number(value: str | None) -> float:
    if not value:
        return 0.0
    return float(value.replace(".", "").replace(",", "."))


def weekdays_back(today: dt.date):
    day = today
    for _ in range(MAX_DAYS_BACK):
        if day.weekday() < 5:
            yield day
        day -= dt.timedelta(days=1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--top", type=int, default=20, help="quantos ativos (padrão 20)")
    parser.add_argument("--pregoes", type=int, default=5, help="pregões na média (padrão 5)")
    args = parser.parse_args()
    today = dt.date.today()

    print("Baixando o cadastro de instrumentos da B3...")
    instrument_rows = None
    for day in weekdays_back(today):
        text = download("InstrumentsConsolidatedFile", day)
        try:
            instrument_rows = rows(text) if text else None
        except ValueError:  # arquivo do dia ainda parcial: usa o anterior
            continue
        if instrument_rows:
            break
    if not instrument_rows:
        print("ERRO: cadastro de instrumentos da B3 indisponível.")
        return 1
    underlying_of: dict[str, str] = {}
    series = collections.Counter()
    for r in instrument_rows:
        if r.get("SctyCtgyNm") not in OPTION_CATEGORIES:
            continue
        underlying_of[r["TckrSymb"]] = r["Asst"]
        if (r.get("XprtnDt") or "") >= today.isoformat():
            series[r["Asst"]] += 1
    # Opções já vencidas saem do cadastro: usa a raiz do ticker (4 letras) → ativo mais comum.
    by_root: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for symbol, underlying in underlying_of.items():
        by_root[symbol[:4]][underlying] += 1
    root_map = {root: c.most_common(1)[0][0] for root, c in by_root.items()}

    turnover = collections.Counter()
    deals = collections.Counter()
    sessions = []
    for day in weekdays_back(today):
        if len(sessions) == args.pregoes:
            break
        text = download("TradeInformationConsolidatedFile", day)
        if not text:
            continue
        try:
            reader = rows(text)
        except ValueError:
            continue
        for r in reader:
            if r.get("SgmtNm") not in OPTION_SEGMENTS:
                continue
            symbol = r["TckrSymb"]
            underlying = underlying_of.get(symbol) or root_map.get(symbol[:4])
            if underlying:
                turnover[underlying] += number(r.get("NtlFinVol"))
                deals[underlying] += number(r.get("TradQty"))
        sessions.append(day)
        print(f"  pregão {day:%d/%m/%Y} lido")
    if not sessions:
        print("ERRO: nenhum arquivo de negócios da B3 disponível.")
        return 1

    n = len(sessions)
    ranking = sorted(turnover, key=lambda u: (turnover[u], deals[u]), reverse=True)[: args.top]
    with OUT.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(
            ["posicao", "ticker", "giro_medio_opcoes_rs_dia", "negocios_medios_opcoes_dia",
             "series_vigentes_b3"]
        )
        for i, u in enumerate(ranking, 1):
            w.writerow(
                [i, u, f"{turnover[u] / n:.0f}", f"{deals[u] / n:.0f}", series.get(u, 0)]
            )
    period = f"{min(sessions):%d/%m/%Y} a {max(sessions):%d/%m/%Y}"
    print(f"\nTop {len(ranking)} por volume financeiro médio das opções ({n} pregões, {period}):")
    for i, u in enumerate(ranking, 1):
        giro = f"{turnover[u] / n / 1e6:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
        print(f"  {i:2d}. {u:<7} R$ {giro} mi/dia")
    print(f"\nGravado em {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
