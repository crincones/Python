"""Monta os blocos do heatmap a partir das barras do MT5 e do cadastro da B3. Função pura."""

from __future__ import annotations

from travas.heatmap.metrics import compute

# Ativos com opções que não entram no heatmap de ativos.
EXCLUDED = {"IBOV11"}  # opções sobre o índice: não é um ativo negociado à vista


def build_items(
    daily: dict[str, tuple],
    profiles: dict[str, dict],
    shares: dict[str, float | None],
) -> list[dict]:
    items = []
    for ticker, (bars, info) in sorted(daily.items()):
        if ticker in EXCLUDED:
            continue
        m = compute(bars, info.get("session_deals"))
        if not m["available"]:
            continue
        prof = profiles.get(ticker) or {}
        total_shares = shares.get(ticker)
        items.append(
            {
                "ticker": ticker,
                "name": prof.get("trading_name") or info.get("description") or ticker,
                "sector": prof.get("sector") or "Sem classificação",
                "subsector": prof.get("subsector"),
                "price": m["price"],
                "last_bar_date": m["last_bar_date"],
                "last_bar_forming": m["last_bar_forming"],
                "changes": m["changes"],
                "turnover_today": m["turnover_today"],
                "turnover_avg20": m["turnover_avg20"],
                "turnover_ratio": m["turnover_ratio"],
                "deals_session": m["deals_session"],
                "hv20": m["hv"]["20"],
                # Aproximação: preço DESTE ticker × total de ações (todas as classes).
                "market_cap_approx": m["price"] * total_shares
                if total_shares and m["price"]
                else None,
            }
        )
    return items
