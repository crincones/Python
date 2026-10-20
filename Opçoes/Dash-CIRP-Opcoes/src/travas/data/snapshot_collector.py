"""Coletor de snapshots (`travas snapshot`): roda no servidor com o MT5, em horários fixos.

Para os `snapshots.max_underlyings` ativos com opções mais líquidas (volume financeiro médio das
opções nos últimos pregões, pelo fechamento oficial da B3 arquivado em `b3-archive`) que tenham
opções no MT5 da conta logada, do mais líquido ao menos: cotação do ativo, séries dos N
próximos vencimentos com strike a até `collection.strike_range_pct_spot` do spot, lidas pelo
mesmo caminho da coleta do app (`market_data.fetch_chain`: lotes no Market Watch, heartbeat,
normalização e correção pela referência da B3). O resultado vai para `snapshots.write_snapshot`.

Somente leitura no MT5: nenhuma ordem é enviada. O terminal não é aberto nem fechado aqui (no
servidor ele é um serviço do systemd); sem terminal conectado ou com o feed parado até o prazo,
o snapshot é registrado como "falhou", sem dados.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

import pandas as pd

from travas.calendar_b3 import B3Calendar
from travas.data import market_data
from travas.data.b3_instruments import B3Instruments
from travas.data.mt5_client import MT5Client, MT5Error
from travas.data.normalize import option_catalog
from travas.data.snapshots import options_liquidity, write_snapshot
from travas.settings import Settings
from travas.timeutils import LOCAL_TIMEZONE

log = logging.getLogger(__name__)

RETRY_SECONDS = 60
OPEN_ENDED_DTE = 10_000  # o limite é o nº de vencimentos mensais, não o prazo


def _now() -> pd.Timestamp:
    return pd.Timestamp.now(tz=LOCAL_TIMEZONE)


def _connect(settings: Settings, deadline: float) -> tuple[MT5Client, dict]:
    """Conecta ao terminal já aberto; tenta de novo até o prazo (terminal reiniciando etc.)."""
    mt5_settings = settings.mt5.model_copy(
        update={"launch_if_closed": False, "close_if_launched": False}
    )
    while True:
        client = MT5Client(mt5_settings)
        try:
            client.__enter__()
            return client, client.terminal_summary()
        except (MT5Error, OSError) as exc:
            client.close()
            if time.monotonic() + RETRY_SECONDS > deadline:
                raise MT5Error(f"terminal indisponível até o prazo: {exc}") from exc
            log.warning("MT5 indisponível (%s); nova tentativa em %d s", exc, RETRY_SECONDS)
            time.sleep(RETRY_SECONDS)


def _fresh_feed(
    client: MT5Client, heartbeat: str, settings: Settings, deadline: float
) -> market_data.UnderlyingQuote:
    """Espera o tick do ativo de referência ficar recente (feed vivo) até o prazo."""
    limit = settings.collection.stale_feed_minutes * 60
    while True:
        quote = market_data.underlying_quote(client, heartbeat, settings.mt5.server_timezone)
        if quote.pc_lag_seconds is not None and quote.pc_lag_seconds <= limit:
            return quote
        if time.monotonic() + RETRY_SECONDS > deadline:
            lag = "sem tick" if quote.pc_lag_seconds is None else f"{quote.pc_lag_seconds:.0f} s"
            raise MT5Error(f"feed parado: último tick de {heartbeat} há {lag}")
        log.warning("Feed parado em %s; nova tentativa em %d s", heartbeat, RETRY_SECONDS)
        time.sleep(RETRY_SECONDS)


def _select_underlyings(
    root: Path,
    reference: pd.DataFrame | None,
    counts: pd.Series,
    settings: Settings,
    manifest: dict,
) -> list[str]:
    """Os N ativos mais líquidos com opções no MT5, do mais líquido ao menos. Sem arquivos da B3
    arquivados, ordena pelo nº de séries vigentes no MT5 (registrado no manifesto)."""
    s = settings.snapshots
    liquidity, days = options_liquidity(root, reference, s.liquidity_sessions)
    liquidity = liquidity[liquidity.index.isin(counts.index)]
    if liquidity.empty:
        ranked = list(counts.index)
        manifest["selection"] = "nº de séries no MT5 (sem fechamento da B3 arquivado)"
    else:
        rest = [u for u in counts.index if u not in liquidity.index]
        ranked = list(liquidity.index) + rest
        manifest["selection"] = (
            f"volume financeiro médio das opções na B3 ({len(days)} pregões: "
            f"{days[0]} a {days[-1]})"
        )
    selected = [str(u) for u in ranked[: s.max_underlyings]]
    manifest["selected_underlyings"] = selected
    manifest["liquidity_brl_day"] = {u: round(float(liquidity.get(u, 0.0))) for u in selected}
    log.info("Ativos (%d): %s", len(selected), ", ".join(selected))
    return selected


def collect_snapshot(
    settings: Settings, root: Path, slot: str | None = None, wait_minutes: float = 15.0
) -> dict | None:
    """Grava o snapshot do momento. None se hoje não é pregão (nada é gravado)."""
    calendar = B3Calendar.from_csv(settings.paths.holidays_file)
    started = _now()
    today = started.date()
    slot = slot or f"{started:%H%M}"
    if not calendar.is_session(today):
        log.info("%s não é pregão: snapshot %s não coletado", today, slot)
        return None
    deadline = time.monotonic() + wait_minutes * 60
    tz = settings.mt5.server_timezone
    manifest: dict = {
        "status": "falhou",
        "captured_at": started.isoformat(),
        "expirations": settings.snapshots.expirations,
        "expiration_rule": (
            f"{settings.snapshots.expirations} próximos vencimentos mensais + semanais com até "
            f"{settings.snapshots.weekly_max_business_days} du"
        ),
        "strike_range_pct_spot": settings.collection.strike_range_pct_spot,
    }
    frames: list[pd.DataFrame] = []
    per_underlying: dict[str, dict] = {}
    errors: dict[str, str] = {}
    client = None
    try:
        client, terminal = _connect(settings, deadline)
        manifest["terminal"] = {
            k: terminal[k] for k in ("build", "server", "company", "connected")
        }
        reference = B3Instruments(root / "_b3_cache", calendar).reference(today)
        catalog = option_catalog(client.symbols(), tz, reference)
        alive = catalog[catalog["expiration_date"] >= today]
        counts = alive["underlying"].value_counts()
        if counts.empty:
            raise MT5Error("nenhuma opção vigente no catálogo do MT5")
        selected = _select_underlyings(root, reference, counts, settings, manifest)
        _fresh_feed(client, selected[0], settings, deadline)
        for underlying in selected:
            began = _now()
            try:
                quote = market_data.underlying_quote(client, underlying, tz)
                if quote.price is None:
                    raise MT5Error("ativo sem cotação")
                r = settings.collection.strike_range_pct_spot
                scope = market_data.ChainScope(
                    ("call", "put"),
                    OPEN_ENDED_DTE,
                    quote.price * (1 - r),
                    quote.price * (1 + r),
                    settings.snapshots.expirations,
                    settings.snapshots.weekly_max_business_days,
                )
                # XP preenche negócios/volume da sessão: sem a barra D1 por série (lenta).
                chain = market_data.fetch_chain(
                    client, catalog, underlying, scope, calendar, settings, reference, False
                )
            except MT5Error as exc:
                errors[underlying] = str(exc)
                log.warning("%s: %s", underlying, exc)
                continue
            frames.append(chain.assign(captured_at=began))
            per_underlying[underlying] = {
                "series": len(chain),
                "series_with_book": int(chain["mid"].notna().sum()),
                "spot": quote.price,
                "spot_time": quote.quote_time.isoformat() if quote.quote_time else None,
                "expirations": sorted(d.isoformat() for d in chain["expiration_date"].unique()),
                "seconds": round((_now() - began).total_seconds(), 1),
            }
            log.info(
                "%s: %d séries (%d com book)",
                underlying,
                len(chain),
                per_underlying[underlying]["series_with_book"],
            )
    except MT5Error as exc:
        manifest["error"] = str(exc)
        log.error("Snapshot %s falhou: %s", slot, exc)
    finally:
        if client is not None:
            client.close()
    chain = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    finished = _now()
    if frames:
        manifest["status"] = "parcial" if errors else "completo"
    manifest.update(
        finished_at=finished.isoformat(),
        duration_seconds=round((finished - started).total_seconds(), 1),
        series=len(chain),
        series_with_book=int(chain["mid"].notna().sum()) if len(chain) else 0,
        underlyings=len(per_underlying),
        failed=sorted(errors),
        errors=errors,
        per_underlying=per_underlying,
    )
    manifest = write_snapshot(root, today, slot, chain, manifest)
    log.info(
        "Snapshot %s %s: %s, %d séries de %d ativos em %.0f s",
        today,
        slot,
        manifest["status"],
        manifest["series"],
        manifest["underlyings"],
        manifest["duration_seconds"],
    )
    return manifest
