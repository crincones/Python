"""Linha de comando: `travas serve` (aplicativo) e `travas check` (viabilidade dos dados)."""

from __future__ import annotations

import argparse
import logging
import logging.handlers
import sys
import webbrowser

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
    log.info("Analisador em %s", url)
    uvicorn.run(create_app(settings), host=settings.server.host, port=port, log_level="info")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="travas", description="Analisador de travas B3")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser(
        "check", help="audita dados disponíveis no MT5 e grava docs/viabilidade_dados.md"
    )
    check.add_argument("--underlying", default="PETR4")
    serve = sub.add_parser("serve", help="inicia o aplicativo local")
    serve.add_argument("--no-browser", action="store_true")
    serve.add_argument("--port", type=int, default=None, help="porta (padrão: settings.yaml)")
    args = parser.parse_args()

    settings = load_settings()
    setup_logging(settings)
    if args.command == "check":
        sys.exit(cmd_check(settings, args.underlying))
    sys.exit(cmd_serve(settings, settings.server.open_browser and not args.no_browser, args.port))


if __name__ == "__main__":
    main()
