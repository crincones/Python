"""Linha de comando: mtf download | mtf run | mtf all."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from typing import Annotated

import typer

from mtf.config import PROJECT_ROOT, load_settings

app = typer.Typer(add_completion=False, help="Pesquisa tendência D1/H4 + retração H1 (B3)")
log = logging.getLogger("mtf")


def _setup_logging() -> None:
    logs = PROJECT_ROOT / "logs"
    logs.mkdir(exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    file_handler = RotatingFileHandler(
        logs / "mtf.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    console = logging.StreamHandler()
    for handler in (file_handler, console):
        handler.setFormatter(fmt)
    logging.basicConfig(level=logging.INFO, handlers=[file_handler, console])


@app.callback()
def main() -> None:
    _setup_logging()


@app.command()
def download(
    pilot: Annotated[int | None, typer.Option(help="N ativos mais líquidos (0 = todos)")] = None,
) -> None:
    """Baixa universo e barras D1/H4/H1 do MetaTrader 5 para data/raw/."""
    from mtf.mt5.download import download as run_download

    run_download(load_settings(), pilot=pilot)


@app.command()
def run() -> None:
    """Setups → backtest → estatísticas → relatório (offline, a partir de data/raw/)."""
    from mtf.pipeline import publish_reports, run_research
    from mtf.reports.render import render_reports

    settings = load_settings()
    result = run_research(settings)
    reports = render_reports(result, settings)
    latest = publish_reports(reports)
    log.info("Resultados em %s; relatório em %s", result.run_dir, latest / "index.html")


@app.command(name="all")
def run_all(
    pilot: Annotated[int | None, typer.Option(help="N ativos mais líquidos (0 = todos)")] = None,
) -> None:
    """download + run."""
    download(pilot)
    run()
