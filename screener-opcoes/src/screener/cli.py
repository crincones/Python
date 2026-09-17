"""Interface de linha de comando."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer

from screener.logging_setup import setup_logging
from screener.settings import DEFAULT_SETTINGS_PATH, Settings, load_settings

app = typer.Typer(help="Screener de travas de débito (B3 via MetaTrader 5 / XP)")
log = logging.getLogger("screener")

ConfigOption = Annotated[Path, typer.Option("--config", help="Caminho do settings.yaml")]
TOP_UNDERLYINGS_SHOWN = 15
BRL_MILLION = 1e6


@app.callback()
def main() -> None:
    """Screener de travas de débito."""


def _init(config: Path) -> Settings:
    settings = load_settings(config)
    setup_logging(settings.logging, settings.paths)
    return settings


@app.command()
def check(config: ConfigOption = DEFAULT_SETTINGS_PATH) -> None:
    """Valida a conexão com o MT5 e informa quais campos de opção a corretora preenche."""
    from screener.collector.field_audit import run_check
    from screener.collector.mt5_client import MT5Client, MT5Error

    settings = _init(config)
    try:
        with MT5Client(settings.mt5) as client:
            report = run_check(client, settings)
    except MT5Error as exc:
        log.error("Falha no check: %s", exc)
        raise typer.Exit(code=1) from exc

    t = report.terminal
    log.info(
        "Terminal build %s | conectado=%s | conta %s @ %s (%s)",
        t["build"],
        t["connected"],
        t["login"],
        t["server"],
        t["company"],
    )
    log.info(
        "Símbolos no servidor: %d | opções (option_strike > 0): %d",
        report.total_symbols,
        report.total_options,
    )
    log.info("\nTipo x estilo de exercício:\n%s", report.right_mode_counts.to_string(index=False))
    log.info(
        "\nAtivos-objeto com mais séries listadas (%d no total):\n%s",
        len(report.underlyings),
        report.underlyings.head(TOP_UNDERLYINGS_SHOWN).to_string(index=False),
    )

    rates = report.fill_rates.assign(fill_rate=lambda d: (d["fill_rate"] * 100).round(1))
    log.info(
        "\nCampos preenchidos na amostra (%d séries próximas do ATM, vencimento mais curto):\n%s",
        report.sample_size,
        rates.to_string(index=False),
    )
    missing = rates.loc[rates["filled"] == 0, "field"].tolist()
    if missing:
        log.warning("Campos sempre zerados/ausentes (calcular localmente): %s", ", ".join(missing))
    log.info(
        "Idade mediana da cotação na amostra (relógio do servidor): %.0f s",
        report.median_quote_age_seconds,
    )
    log.info(
        "Relógio do PC − tick mais recente do servidor: %.0f s (atraso do feed ou do relógio "
        "do servidor)",
        report.pc_minus_server_seconds,
    )


KeepTerminalOption = Annotated[
    bool,
    typer.Option(
        "--keep-terminal", help="Não fecha o terminal MT5 mesmo que o screener o tenha aberto"
    ),
]


def _keep_terminal(settings: Settings, keep: bool) -> Settings:
    if not keep:
        return settings
    mt5 = settings.mt5.model_copy(update={"close_if_launched": False})
    return settings.model_copy(update={"mt5": mt5})


@app.command()
def collect(
    config: ConfigOption = DEFAULT_SETTINGS_PATH, keep_terminal: KeepTerminalOption = False
) -> None:
    """Filtra ativos-objeto e séries candidatas e grava um snapshot em data/snapshots/."""
    from screener.collector.mt5_client import MT5Client, MT5Error
    from screener.collector.snapshot import collect_snapshot
    from screener.data.schema import UNDERLYINGS_TABLE
    from screener.data.store import read_table

    settings = _keep_terminal(_init(config), keep_terminal)
    try:
        with MT5Client(settings.mt5) as client:
            path = collect_snapshot(client, settings)
    except MT5Error as exc:
        log.error("Falha na coleta: %s", exc)
        raise typer.Exit(code=1) from exc

    underlyings = read_table(path, UNDERLYINGS_TABLE)
    shown = underlyings.assign(
        turnover_mi=(underlyings["avg_daily_turnover_brl"] / BRL_MILLION).round(1)
    )[
        [
            "underlying",
            "price",
            "turnover_mi",
            "liquidity_rank",
            "candidate_series",
            "history_complete",
            "reject_reason",
        ]
    ]
    log.info(
        "\nAtivos-objeto (volume financeiro médio diário em R$ mi):\n%s",
        shown.to_string(index=False),
    )


SnapshotOption = Annotated[
    str, typer.Option("--snapshot", help="'latest' ou nome AAAAMMDD_HHMMSS do snapshot")
]


@app.command()
def fixture(
    snapshot: SnapshotOption = "latest", config: ConfigOption = DEFAULT_SETTINGS_PATH
) -> None:
    """Copia um snapshot para tests/fixtures/ sem dados da conta nem caminhos locais."""
    from screener.data.fixtures import export_fixture
    from screener.data.store import resolve_snapshot
    from screener.settings import PROJECT_ROOT

    settings = _init(config)
    source = resolve_snapshot(settings.paths.snapshots_dir, snapshot)
    target = export_fixture(source, PROJECT_ROOT / "tests" / "fixtures")
    log.info("Fixture criada em %s", target)


@app.command()
def analyze(
    snapshot: SnapshotOption = "latest", config: ConfigOption = DEFAULT_SETTINGS_PATH
) -> None:
    """Calcula IV, liquidez, travas, viés e score; grava no próprio snapshot."""
    settings = _init(config)
    _analyze(settings, snapshot)


def _analyze(settings: Settings, snapshot: str) -> Path:
    import pandas as pd

    from screener.analysis import analyze as run_analysis
    from screener.data import store
    from screener.data.dividends import load_dividends
    from screener.data.schema import (
        ANALYSIS_META_FILE,
        BARS_COLUMNS,
        BARS_TABLE,
        BIAS_TABLE,
        OPTIONS_TABLE,
        SERIES_TABLE,
        SPREADS_TABLE,
    )
    from screener.timeutils import LOCAL_TIMEZONE

    path = store.resolve_snapshot(settings.paths.snapshots_dir, snapshot)
    rate = snapshot_rate(store.read_meta(path), settings)
    settings = settings.model_copy(
        update={
            "market": settings.market.model_copy(update={"risk_free_rate_annual": rate["annual"]})
        }
    )
    log.info("Taxa livre de risco: %.2f%% a.a. (%s)", rate["annual"] * 100, rate["source"])
    options = store.read_table(path, OPTIONS_TABLE)
    dividends = load_dividends(settings.paths.dividends_file)
    try:
        bars = store.read_table(path, BARS_TABLE)
    except store.SnapshotNotFoundError:
        log.warning("Snapshot %s sem barras (coletado antes do sinal automático)", path.name)
        bars = pd.DataFrame(columns=list(BARS_COLUMNS))
    result = run_analysis(options, dividends, bars, settings)
    meta = {
        "analyzed_at": pd.Timestamp.now(tz=LOCAL_TIMEZONE).isoformat(),
        "snapshot": path.name,
        **result.summary,
        "risk_free_rate": rate,
        "settings": settings.model_dump(mode="json"),
    }
    store.write_derived(
        path,
        {SERIES_TABLE: result.series, SPREADS_TABLE: result.spreads, BIAS_TABLE: result.bias},
        ANALYSIS_META_FILE,
        meta,
    )
    log.info("Análise gravada em %s", path)
    log.info("IV: %s", result.summary["series_iv_status"])
    log.info("Reprovações de liquidez: %s", result.summary["series_liquidity_rejections"])
    log.info("Pares inválidos: %s", result.summary["pairs_invalid"])
    log.info("Travas válidas por estratégia: %s", result.summary["spreads_by_strategy"])
    shown_bias = result.bias[["underlying", "bias", "bias_source", "auto_bias", "manual_bias"]]
    log.info("\nViés por ativo:\n%s", shown_bias.to_string(index=False))
    log.info("Ranqueadas: %s", result.summary["spreads_ranked"])
    return path


def snapshot_rate(meta: dict, settings: Settings) -> dict:
    """Taxa gravada na coleta; snapshots antigos (sem taxa) usam o YAML."""
    from screener.market_data.b3_indicators import SOURCE_YAML, RiskFreeRate

    if "risk_free_rate" in meta:
        return meta["risk_free_rate"]
    return RiskFreeRate(
        annual=settings.market.risk_free_rate_annual,
        source=SOURCE_YAML,
        reference_date=None,
        note="snapshot coletado antes da busca do CDI na B3",
    ).to_dict()


@app.command()
def report(
    snapshot: SnapshotOption = "latest", config: ConfigOption = DEFAULT_SETTINGS_PATH
) -> None:
    """Gera output/relatorio_AAAAMMDD_HHMM.html a partir de um snapshot analisado."""
    settings = _init(config)
    _report(settings, snapshot)


def _report(settings: Settings, snapshot: str) -> Path:
    from screener.data.store import resolve_snapshot
    from screener.report.render import write_report

    path = resolve_snapshot(settings.paths.snapshots_dir, snapshot)
    target = write_report(path, settings.paths.output_dir)
    log.info("Relatório gerado: %s", target)
    return target


ForceOption = Annotated[
    bool, typer.Option("--force", help="Executa mesmo fora de dia de pregão da B3")
]


@app.command()
def run(
    config: ConfigOption = DEFAULT_SETTINGS_PATH,
    force: ForceOption = False,
    keep_terminal: KeepTerminalOption = False,
) -> None:
    """collect + analyze + report. Em dia sem pregão (fim de semana/feriado B3) não faz nada."""
    import pandas as pd

    from screener.calendar_b3 import B3Calendar
    from screener.collector.mt5_client import MT5Client, MT5Error
    from screener.collector.snapshot import collect_snapshot
    from screener.timeutils import LOCAL_TIMEZONE

    settings = _keep_terminal(_init(config), keep_terminal)
    today = pd.Timestamp.now(tz=LOCAL_TIMEZONE).date()
    if not force and not B3Calendar.from_csv(settings.paths.holidays_file).is_session(today):
        log.info("%s não é dia de pregão da B3; nada a fazer (use --force para forçar)", today)
        return
    try:
        with MT5Client(settings.mt5) as client:
            path = collect_snapshot(client, settings)
    except MT5Error as exc:
        log.error("Falha na coleta: %s", exc)
        raise typer.Exit(code=1) from exc
    _analyze(settings, path.name)
    _report(settings, path.name)
