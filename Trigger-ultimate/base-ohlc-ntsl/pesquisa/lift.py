"""Lift ajustado pela geometria.

Para cada tijolo real calcula-se o que o ACASO produziria com a mesma geometria
(mesmo pavio contrario, mesmo sentido) e mede-se o residuo:

    lift_ok = ok_real - E[ok | pavio]_passeio_aleatorio

Assim o efeito mecanico -- pavio largo = extremo dificil de violar -- some, e o
que sobra e mercado. Uma regra so vale se o lift medio for != 0 fora da amostra.
"""

from __future__ import annotations

import itertools
import numpy as np
import pandas as pd

from sintetico import metricas, renko, caminho
from varredura import base, split, condicoes

BINS = list(range(45, 156, 5))


def tabela_acaso(cache="sintetico.pkl") -> pd.DataFrame:
    try:
        s = pd.read_pickle(cache)
    except FileNotFoundError:
        s = metricas(renko(caminho(40_000_000, seed=7)))
        s.to_pickle(cache)
    s["fx"] = pd.cut(s.risco, BINS)
    g = s.groupby("fx", observed=True).agg(n=("ok", "size"), ok=("ok", "mean"),
                                           cont=("cont", "mean"), R=("R", "mean"),
                                           net=("net_fav", "mean"), mfe=("mfe", "mean"))
    return g


def anexar_lift(d: pd.DataFrame, g: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["fx"] = pd.cut(d.risco, BINS)
    for col in ("ok", "cont", "net", "mfe"):
        d[f"e_{col}"] = d["fx"].map(g[col]).astype(float)
    d["ok_real"] = np.where(d.dir < 0, d.ok_baixa, d.ok_alta)
    d["net_fav"] = d.dir * (d.c.shift(-4) - d.c) / 50.0
    d["lift_ok"] = d.ok_real - d.e_ok
    d["lift_cont"] = d.cont - d.e_cont
    d["lift_net"] = d.net_fav - d.e_net
    return d.dropna(subset=["lift_ok", "lift_cont"])


def carregar_lift():
    g = tabela_acaso()
    d = anexar_lift(base(), g)
    return d, g


def ic95(x):
    x = np.asarray(x, float)
    return 1.96 * x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else np.nan


if __name__ == "__main__":
    pd.set_option("display.width", 240)
    d, g = carregar_lift()
    print("=== expectativa do acaso por faixa de pavio ===")
    print(g.round(4).to_string())

    print(f"\n=== lift global (n={len(d)}) ===")
    for c in ("lift_ok", "lift_cont", "lift_net"):
        print(f"  {c}: {d[c].mean():+.4f}  +-{ic95(d[c]):.4f}")

    print("\n=== distribuicao do pavio: real x acaso ===")
    real = d.groupby("fx", observed=True).size() / len(d) * 100
    aca = g.n / g.n.sum() * 100
    print(pd.DataFrame({"real_%": real.round(2), "acaso_%": aca.round(2)}).to_string())

    tr, te, corte = split(d)
    Ctr, Cte = condicoes(tr), condicoes(te)
    linhas = []
    for r in (1, 2):
        for combo in itertools.combinations(list(Ctr), r):
            mtr = np.logical_and.reduce([Ctr[c] for c in combo])
            mte = np.logical_and.reduce([Cte[c] for c in combo])
            if mtr.sum() < 200 or mte.sum() < 100:
                continue
            a, b = tr[mtr], te[mte]
            linhas.append(dict(regra=" & ".join(combo), n_tr=int(mtr.sum()), n_te=int(mte.sum()),
                               lok_tr=a.lift_ok.mean(), lok_te=b.lift_ok.mean(),
                               ic_te=ic95(b.lift_ok),
                               lcont_tr=a.lift_cont.mean(), lcont_te=b.lift_cont.mean(),
                               ok_te=b.ok_real.mean(), R_te=b.R.mean() if "R" in b else np.nan))
    t = pd.DataFrame(linhas)
    print(f"\n=== varredura sobre o LIFT ({len(t)} regras) ===")
    print("\ntop 12 lift_ok no TREINO, com o que deu no TESTE:")
    print(t.nlargest(12, "lok_tr")[["regra", "n_tr", "lok_tr", "n_te", "lok_te", "ic_te", "ok_te"]].round(4).to_string(index=False))
    print("\npiores 12 no TREINO:")
    print(t.nsmallest(12, "lok_tr")[["regra", "n_tr", "lok_tr", "n_te", "lok_te", "ic_te", "ok_te"]].round(4).to_string(index=False))
    print("\n>>> o teste que importa: o lift do treino sobrevive no teste?")
    print("   correlacao lok_tr x lok_te :", round(np.corrcoef(t.lok_tr, t.lok_te)[0, 1], 4))
    print("   mesmo sinal                :", round((np.sign(t.lok_tr) == np.sign(t.lok_te)).mean(), 4))
    print("   correlacao lcont_tr x _te  :", round(np.corrcoef(t.lcont_tr, t.lcont_te)[0, 1], 4))
    t.to_csv("varredura_lift.csv", index=False)
