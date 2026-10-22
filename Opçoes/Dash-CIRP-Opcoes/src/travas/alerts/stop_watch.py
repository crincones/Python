"""Alerta de stop 1:1: o ativo chegou ao preço em que o prejuízo da estrutura iguala o lucro
máximo (só biblioteca padrão; usado pelo app local e pela checagem do servidor).

O app calcula, para cada pregão até o vencimento, o preço do ativo que aciona o stop (modelo
Black-Scholes com a IV das pernas no momento do cálculo; no vencimento, exato) e envia essa tabela
ao servidor. A checagem compara o preço atual do ativo com o stop do dia. Cada alerta é enviado
uma vez por "armação" (marcar o checkbox de novo arma outra vez).
"""

from __future__ import annotations

import datetime as dt
import json
import os
import threading
from pathlib import Path


def brl(value: float | None, prefix: str = "R$ ") -> str:
    if value is None:
        return "—"
    text = f"{abs(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{'-' if value < 0 else ''}{prefix}{text}"


def _date_br(iso: str) -> str:
    return dt.date.fromisoformat(iso).strftime("%d/%m/%Y")


def watch_entry(evaluated: dict, armed_at: str) -> dict | None:
    """Item da lista vigiada a partir de uma estrutura avaliada (`evaluate_position`)."""
    stop = evaluated.get("stop") or {}
    if evaluated.get("status") != "aberta" or not stop.get("available"):
        return None
    by_date = {d: p for d, p in (stop.get("by_date") or {}).items() if p is not None}
    if stop.get("expiry_price") is not None:
        by_date[evaluated["first_expiration"]] = stop["expiry_price"]
    if not by_date:
        return None
    legs = [
        f"{'Compra' if lg['side'] == 'compra' else 'Venda'} {lg['quantity']} {lg['symbol']} "
        f"({lg['option_type']} {lg['strike']:.2f})".replace(".", ",")
        for lg in evaluated.get("legs", [])
    ]
    return {
        "key": f"{evaluated['id']}:{armed_at}",
        "position_id": evaluated["id"],
        "name": evaluated.get("name"),
        "kind_label": evaluated.get("kind_label"),
        "underlying": evaluated["underlying"],
        "legs": legs,
        "expiration": evaluated["first_expiration"],
        "down": bool(stop.get("down")),
        "loss_multiple": stop.get("loss_multiple", 1.0),
        "stop_loss_total": -float(stop["pnl_total"]),
        "max_profit": evaluated.get("max_profit"),
        "entry_net_per_unit": evaluated.get("entry_net_per_unit"),
        "entry_flow": evaluated.get("entry_flow"),
        "by_date": dict(sorted(by_date.items())),
        "computed_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
    }


def stop_price_on(entry: dict, day: dt.date) -> float | None:
    return entry["by_date"].get(day.isoformat())


def triggered(entry: dict, spot: float | None, day: dt.date) -> float | None:
    """Preço do stop do dia se o ativo já o alcançou; senão None."""
    price = stop_price_on(entry, day)
    if spot is None or price is None or day.isoformat() > entry["expiration"]:
        return None
    hit = spot <= price if entry["down"] else spot >= price
    return price if hit else None


def message(entry: dict, spot: float, price: float, origin: str, pnl_now: float | None = None):
    """(assunto, texto) do alerta."""
    side = "caiu até" if entry["down"] else "subiu até"
    lines = [
        f"⚠️ STOP 1:1 atingido — {entry['name']}",
        f"{entry['kind_label']} · {entry['underlying']} · vence {_date_br(entry['expiration'])}",
        "",
        f"{entry['underlying']} {side} {brl(spot, '')} (stop de hoje: {brl(price, '')}).",
        f"Prejuízo no stop ≈ lucro máximo: {brl(entry['stop_loss_total'])}.",
    ]
    if pnl_now is not None:
        lines.append(f"Resultado agora (zerando pelo natural): {brl(pnl_now)}.")
    lines += [
        "",
        *entry["legs"],
        "",
        f"Origem: {origin}. Preço do stop estimado pelo modelo (Black-Scholes, IV das pernas); "
        "confira as cotações antes de agir. Nenhuma ordem foi enviada.",
    ]
    subject = f"Stop 1:1 atingido: {entry['name']} ({entry['underlying']} {brl(spot, '')})"
    return subject, "\n".join(lines)


class JsonFile:
    """JSON gravado de forma atômica, com trava no processo."""

    def __init__(self, path: Path, default: dict) -> None:
        self.path = path
        self._default = default
        self.lock = threading.Lock()

    def read(self) -> dict:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except ValueError:  # JSON corrompido
            pass
        except FileNotFoundError:
            pass
        return json.loads(json.dumps(self._default))

    def write(self, data: dict, private: bool = False) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        if private:
            os.chmod(tmp, 0o600)
        os.replace(tmp, self.path)


class SentLog:
    """Alertas já enviados (chave → quando, por quem, canais)."""

    def __init__(self, path: Path) -> None:
        self._file = JsonFile(path, {"sent": {}})

    def all(self) -> dict:
        return self._file.read()["sent"]

    def has(self, key: str) -> bool:
        return key in self.all()

    def add(self, key: str, info: dict) -> bool:
        """Registra; False se a chave já estava lá (outro processo enviou antes)."""
        with self._file.lock:
            data = self._file.read()
            if key in data["sent"]:
                return False
            data["sent"][key] = info
            self._file.write(data)
            return True

    def merge(self, sent: dict) -> None:
        with self._file.lock:
            data = self._file.read()
            for key, info in sent.items():
                data["sent"].setdefault(key, info)
            self._file.write(data)

    def update(self, key: str, info: dict) -> None:
        with self._file.lock:
            data = self._file.read()
            data["sent"][key] = {**data["sent"].get(key, {}), **info}
            self._file.write(data)

    def remove(self, key: str) -> None:
        """Desfaz a reserva de um envio que falhou (será tentado de novo)."""
        with self._file.lock:
            data = self._file.read()
            if data["sent"].pop(key, None) is not None:
                self._file.write(data)
