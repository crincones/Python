"""Opções baratas ou caras: IV ATM contra a volatilidade histórica do ativo (aba Liquidez de
Opções). Funções puras.

- IV ATM por vencimento: a mesma da análise (`atm_implied_vol`: Black-Scholes europeu sobre o mid,
  média call/put do strike mais próximo do spot, só séries com spread aceitável).
- HV: desvio-padrão dos log-retornos diários × √252, só barras fechadas, numa janela do tamanho
  do prazo até o vencimento (em pregões; mínimo `min_hv_window`).
- Razão IV/HV: abaixo de `cheap_below` = barata, acima de `expensive_above` = cara, entre = neutra.
  A IV costuma ficar acima da HV (prêmio de risco), por isso o limite de "cara" fica acima de 1.
- Liquidez como filtro de confiança: com o book perto do dinheiro fraco (spread mediano alto ou
  poucas séries com bid/ask), o indicador é marcado como pouco confiável.

Indicativo: a HV olha para trás e eventos (balanço, dividendos) podem justificar IV alta.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd

from travas.calendar_b3 import B3Calendar
from travas.data.normalize import INDEX_OPTION_UNDERLYINGS
from travas.heatmap.metrics import historical_vol
from travas.options.implied_vol import atm_implied_vol, options_implied_vol
from travas.settings import PricingSettings, VolPremiumSettings

ATM_COLUMNS = [
    "underlying",
    "expiration_date",
    "dte_business_days",
    "spot",
    "atm_iv",
    "atm_strike_distance_pct",
    "monthly",
]


def is_monthly(calendar: B3Calendar, underlying: str, day: dt.date) -> bool:
    if underlying.upper() in INDEX_OPTION_UNDERLYINGS:
        return calendar.is_index_monthly_expiration(day)
    return calendar.is_monthly_expiration(day)


def atm_iv_table(
    frame: pd.DataFrame, rate_annual: float, pricing: PricingSettings, calendar: B3Calendar
) -> pd.DataFrame:
    """IV ATM por (ativo, vencimento) de uma cadeia/snapshot (colunas de CHAIN_COLUMNS). Só as
    séries perto do dinheiro com mid passam pelo cálculo da IV."""
    near = frame[
        frame["mid"].notna()
        & frame["underlying_price"].notna()
        & (
            (frame["strike"] / frame["underlying_price"] - 1).abs()
            <= pricing.atm_max_strike_distance_pct
        )
        & (frame["dte_business_days"] > 0)
    ]
    if near.empty:
        return pd.DataFrame(columns=ATM_COLUMNS)
    near = near.join(options_implied_vol(near, rate_annual, pricing))
    atm = atm_implied_vol(near, pricing)
    if atm.empty:
        return pd.DataFrame(columns=ATM_COLUMNS)
    keys = ["underlying", "expiration_date"]
    info = near.groupby(keys).agg(
        dte_business_days=("dte_business_days", "first"), spot=("underlying_price", "median")
    )
    atm = atm.join(info, on=keys)
    atm["monthly"] = [
        is_monthly(calendar, u, d)
        for u, d in zip(atm["underlying"], atm["expiration_date"], strict=True)
    ]
    return atm[ATM_COLUMNS].sort_values(keys).reset_index(drop=True)


def classify(ratio: float | None, s: VolPremiumSettings) -> str | None:
    if ratio is None:
        return None
    if ratio < s.cheap_below:
        return "barata"
    if ratio > s.expensive_above:
        return "cara"
    return "neutra"


def hv_window(dte_business_days: int, s: VolPremiumSettings) -> int:
    return max(int(dte_business_days), s.min_hv_window)


def weak_book(book: dict | None, s: VolPremiumSettings) -> str | None:
    """Motivo de o book perto do dinheiro não sustentar a IV (None = book aceitável)."""
    if not book or book.get("book_spread") is None:
        return "sem book perto do dinheiro no snapshot"
    if (book.get("book_with_quotes") or 0) < s.min_book_quotes:
        return f"só {book['book_with_quotes']} séries com bid e ask perto do dinheiro"
    if book["book_spread"] > s.weak_book_spread:
        return f"spread mediano de {book['book_spread']:.0%} perto do dinheiro".replace(".", ",")
    return None


def monthly_listings(frame: pd.DataFrame, calendar: B3Calendar) -> pd.DataFrame:
    """Vencimentos mensais presentes na cadeia/snapshot, com ou sem IV ATM calculável."""
    listed = (
        frame[frame["dte_business_days"] > 0]
        .groupby(["underlying", "expiration_date"], as_index=False)["dte_business_days"]
        .first()
    )
    keep = [
        is_monthly(calendar, u, d)
        for u, d in zip(listed["underlying"], listed["expiration_date"], strict=True)
    ]
    return listed[keep].reset_index(drop=True)


def vol_premium(
    atm: pd.DataFrame,
    listed: pd.DataFrame,
    closes: dict[str, pd.Series],
    books: dict[str, dict],
    s: VolPremiumSettings,
    hv_problem: str | None = None,
) -> dict[str, dict]:
    """IV/HV dos `s.expirations` próximos vencimentos mensais (`listed`, de
    `monthly_listings`) de cada ativo; IV ATM de `atm` (`atm_iv_table`).

    `closes`: fechamentos diários (só barras fechadas, ordem cronológica) por ativo;
    `hv_problem`: por que não há fechamentos (ex.: MT5 desconectado). Devolve, por ativo:
    `ivhv` (razão do 1º mensal que a tem, para ordenar), `ivhv_label`, `ivhv_weak` (motivo de
    pouca confiança ou None), `ivhv_reason` (por que não há razão) e `ivhv_items` (um por
    mensal; sem IV ATM quando o book perto do dinheiro não tem bid e ask aceitáveis).
    """
    iv = {
        (str(u), d): float(v)
        for u, d, v in zip(atm["underlying"], atm["expiration_date"], atm["atm_iv"], strict=True)
    }
    out: dict[str, dict] = {}
    for underlying, rows in listed.groupby("underlying"):
        underlying = str(underlying)
        series = closes.get(underlying)
        items = []
        for r in rows.sort_values("expiration_date").head(s.expirations).itertuples():
            window = hv_window(r.dte_business_days, s)
            hv = historical_vol(series, window) if series is not None else None
            atm_iv = iv.get((underlying, r.expiration_date))
            ratio = atm_iv / hv if hv and atm_iv is not None else None
            items.append(
                {
                    "expiration": r.expiration_date.isoformat(),
                    "dte_business_days": int(r.dte_business_days),
                    "atm_iv": atm_iv,
                    "hv": hv,
                    "hv_window": window,
                    "ratio": ratio,
                    "label": classify(ratio, s),
                }
            )
        head = next((i for i in items if i["ratio"] is not None), None)
        with_iv = next((i for i in items if i["atm_iv"] is not None), None)
        reason = None
        if head is None:
            if with_iv is None:
                reason = "sem IV ATM nos vencimentos mensais (book sem bid e ask aceitáveis)"
            else:
                reason = hv_problem or (
                    f"menos de {with_iv['hv_window'] + 1} fechamentos diários para a vol histórica"
                )
        out[underlying] = {
            "ivhv": head["ratio"] if head else None,
            "ivhv_label": head["label"] if head else None,
            "ivhv_expiration": head["expiration"] if head else None,
            "ivhv_weak": weak_book(books.get(underlying), s),
            "ivhv_reason": reason,
            "ivhv_items": items,
        }
    return out
