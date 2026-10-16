"""Exportação das estruturas acompanhadas em CSV no padrão do Excel em pt-BR.

Separador `;`, vírgula decimal, datas dd/mm/aaaa e UTF-8 com BOM (o Excel reconhece os acentos).
Campos sem dado ficam vazios: nada é preenchido por estimativa.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import math

from travas.tracking.report import REASON_LABELS

STATUS_LABELS = {"aberta": "Aberta", "encerrada": "Encerrada"}
FLOW_LABELS = {"debito": "Débito", "credito": "Crédito"}


def _num(v: object, decimals: int = 2) -> str:
    if v is None:
        return ""
    try:
        x = float(v)  # type: ignore[arg-type]
    except TypeError, ValueError:
        return ""
    if not math.isfinite(x):
        return ""
    return f"{x:.{decimals}f}".replace(".", ",")


def _date(v: object) -> str:
    if not v:
        return ""
    try:
        return dt.date.fromisoformat(str(v)[:10]).strftime("%d/%m/%Y")
    except ValueError:
        return ""


def _legs_text(p: dict) -> str:
    return " | ".join(
        f"{'C' if lg['side'] == 'compra' else 'V'} {lg['quantity']} {lg['symbol']}"
        + (f" @ {_num(lg.get('entry_price'))}" if lg.get("entry_price") is not None else "")
        for lg in p["legs"]
    )


STRUCTURE_HEADER = [
    "ID", "Nome", "Grupo", "Ativo", "Estrutura", "Status", "Data entrada", "Data saída",
    "Dias", "Motivo saída", "Pernas", "Unidades", "Entrada por unidade", "Sentido entrada",
    "Caixa entrada (R$)", "Custos entrada (R$)", "Saída por unidade", "Sentido saída",
    "Custos saída (R$)", "Perda máx. (R$)", "Lucro máx. (R$)", "Breakevens", "1º vencimento",
    "P&L realizado (R$)", "R (P&L/perda máx.)", "P&L aberto natural (R$)", "P&L aberto mid (R$)",
    "Observações",
]  # fmt: skip

LEG_HEADER = [
    "ID estrutura", "Nome", "Grupo", "Ativo", "Status", "Data entrada", "Data saída", "Opção",
    "Tipo", "Estilo", "Strike", "Vencimento", "Lado", "Quantidade", "Multiplicador",
    "Preço entrada", "Preço saída", "Bid", "Ask", "P&L natural perna (R$)",
]  # fmt: skip


def structures_csv(evaluated: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";", lineterminator="\r\n")
    w.writerow(STRUCTURE_HEADER)
    for p in evaluated:
        ex = p.get("exit") or {}
        closed = p["status"] == "encerrada"
        entry, exit_ = p.get("entry_date"), ex.get("exit_date")
        days = ""
        if entry and exit_:
            days = str((dt.date.fromisoformat(exit_[:10]) - dt.date.fromisoformat(entry[:10])).days)
        exit_net, exit_flow = ex.get("exit_net"), ex.get("exit_flow")
        if closed and ex.get("leg_prices") and p.get("units"):
            # Saída informada por perna: líquido por unidade derivado do caixa de saída.
            cash = (p.get("realized_pnl") or 0.0) - (p.get("entry_cash_total") or 0.0)
            cash += (p.get("costs_entry") or 0.0) + (ex.get("costs_exit") or 0.0)
            exit_net, exit_flow = abs(cash) / p["units"], "credito" if cash >= 0 else "debito"
        risk = p.get("max_loss")
        realized = p.get("realized_pnl")
        w.writerow(
            [
                p["id"],
                p.get("name", ""),
                p.get("group", ""),
                p.get("underlying", ""),
                p.get("kind_label", ""),
                STATUS_LABELS.get(p["status"], p["status"]),
                _date(entry),
                _date(exit_),
                days,
                REASON_LABELS.get(ex.get("reason"), "") if closed else "",
                _legs_text(p),
                _num(p.get("units"), 0),
                _num(p.get("entry_net_per_unit"), 4),
                FLOW_LABELS.get(p.get("entry_flow"), ""),
                _num(p.get("entry_cash_total")),
                _num(p.get("costs_entry")),
                _num(exit_net, 4) if closed else "",
                FLOW_LABELS.get(exit_flow, "") if closed else "",
                _num(ex.get("costs_exit")) if closed else "",
                _num(risk),
                _num(p.get("max_profit")),
                " / ".join(_num(b) for b in p.get("breakevens") or []),
                _date(p.get("first_expiration")),
                _num(realized) if closed else "",
                _num(realized / risk, 3) if closed and realized is not None and risk else "",
                "" if closed else _num(p.get("pnl_natural")),
                "" if closed else _num(p.get("pnl_mid")),
                (p.get("notes") or "").replace("\r", " ").replace("\n", " "),
            ]
        )
    return "﻿" + buf.getvalue()


def legs_csv(evaluated: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";", lineterminator="\r\n")
    w.writerow(LEG_HEADER)
    for p in evaluated:
        ex = p.get("exit") or {}
        closed = p["status"] == "encerrada"
        exit_prices = ex.get("leg_prices") or [None] * len(p["legs"])
        for lg, exit_px in zip(p["legs"], exit_prices, strict=False):
            w.writerow(
                [
                    p["id"],
                    p.get("name", ""),
                    p.get("group", ""),
                    p.get("underlying", ""),
                    STATUS_LABELS.get(p["status"], p["status"]),
                    _date(p.get("entry_date")),
                    _date(ex.get("exit_date")),
                    lg["symbol"],
                    lg.get("option_type", ""),
                    {"american": "Americana", "european": "Europeia"}.get(
                        lg.get("exercise_style"), ""
                    ),
                    _num(lg.get("strike")),
                    _date(lg.get("expiration")),
                    "Compra" if lg["side"] == "compra" else "Venda",
                    lg["quantity"],
                    _num(lg.get("multiplier"), 0),
                    _num(lg.get("entry_price"), 4),
                    _num(exit_px, 4) if closed else "",
                    "" if closed else _num(lg.get("bid"), 4),
                    "" if closed else _num(lg.get("ask"), 4),
                    "" if closed else _num(lg.get("pnl_natural")),
                ]
            )
    return "﻿" + buf.getvalue()
