"""Linha de comando: `travas serve` (aplicativo), `travas check` (viabilidade dos dados) e, no
servidor com MT5, `travas snapshot` / `travas b3-archive` (snapshots para a fonte "servidor")."""

from __future__ import annotations

import argparse
import logging
import logging.handlers
import sys
import webbrowser
from pathlib import Path

from travas.settings import PROJECT_ROOT, Settings, load_settings

log = logging.getLogger("travas")


def setup_logging(settings: Settings) -> None:
    logs_dir = settings.paths.logs_dir
    logs_dir.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        logs_dir / "travas.log",
        maxBytes=settings.logging.max_bytes,
        backupCount=settings.logging.backup_count,
        encoding="utf-8",
    )
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(fmt)
    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(fmt)
    root = logging.getLogger()
    root.setLevel(settings.logging.level)
    root.handlers[:] = [handler, console]


def cmd_check(settings: Settings, underlying: str) -> int:
    from travas.data.feasibility import build_report
    from travas.data.mt5_client import MT5Error
    from travas.data.service import MarketDataService

    service = MarketDataService(settings)
    try:
        service.connect()
    except (MT5Error, OSError) as exc:
        log.error("Sem conexão com o MT5: %s", exc)
        return 1
    try:
        report = build_report(service, underlying)
    finally:
        service.close()
    out = PROJECT_ROOT / "docs" / "viabilidade_dados.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(report, encoding="utf-8")
    log.info("Relatório gravado em %s", out)
    sys.stdout.buffer.write((report + "\n").encode("utf-8"))
    return 0


def cmd_serve(settings: Settings, open_browser: bool, port: int | None = None) -> int:
    import uvicorn

    from travas.api.app import create_app

    port = port or settings.server.port
    url = f"http://{settings.server.host}:{port}/"
    if open_browser:
        webbrowser.open(url)
    log.info("Dash CIRP Opções em %s", url)
    uvicorn.run(create_app(settings), host=settings.server.host, port=port, log_level="info")
    return 0


def cmd_snapshot(settings: Settings, out: Path, slot: str | None, wait_minutes: float) -> int:
    from travas.data.snapshot_collector import collect_snapshot

    manifest = collect_snapshot(settings, out, slot, wait_minutes)
    return 0 if manifest is None or manifest["status"] != "falhou" else 1


def cmd_b3_archive(settings: Settings, out: Path) -> int:
    import pandas as pd

    from travas.calendar_b3 import B3Calendar
    from travas.data.snapshots import archive_b3_trades
    from travas.timeutils import LOCAL_TIMEZONE

    calendar = B3Calendar.from_csv(settings.paths.holidays_file)
    archive_b3_trades(out, pd.Timestamp.now(tz=LOCAL_TIMEZONE).date(), calendar)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="travas", description="Dash CIRP Opções (travas B3)")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser(
        "check", help="audita dados disponíveis no MT5 e grava docs/viabilidade_dados.md"
    )
    check.add_argument("--underlying", default="PETR4")
    serve = sub.add_parser("serve", help="inicia o aplicativo local")
    serve.add_argument("--no-browser", action="store_true")
    serve.add_argument("--port", type=int, default=None, help="porta (padrão: settings.yaml)")
    snap = sub.add_parser("snapshot", help="grava um snapshot da cadeia (servidor com MT5)")
    snap.add_argument("--out", type=Path, required=True, help="pasta raiz dos snapshots")
    snap.add_argument("--slot", default=None, help="rótulo HHMM (padrão: hora atual)")
    snap.add_argument("--terminal", default=None, help="terminal64.exe (padrão: settings.yaml)")
    snap.add_argument("--wait-minutes", type=float, default=15.0)
    archive = sub.add_parser("b3-archive", help="arquiva o fechamento oficial da B3 por pregão")
    archive.add_argument("--out", type=Path, required=True, help="pasta raiz dos snapshots")
    args = parser.parse_args()

    settings = load_settings()
    if getattr(args, "terminal", None):
        mt5 = settings.mt5.model_copy(update={"terminal_path": Path(args.terminal)})
        settings = settings.model_copy(update={"mt5": mt5})
    setup_logging(settings)
    if args.command == "check":
        sys.exit(cmd_check(settings, args.underlying))
    if args.command == "snapshot":
        sys.exit(cmd_snapshot(settings, args.out, args.slot, args.wait_minutes))
    if args.command == "b3-archive":
        sys.exit(cmd_b3_archive(settings, args.out))
    sys.exit(cmd_serve(settings, settings.server.open_browser and not args.no_browser, args.port))


if __name__ == "__main__":
    main()
