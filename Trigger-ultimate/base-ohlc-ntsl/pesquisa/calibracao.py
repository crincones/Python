"""Calibracao final: a unica variavel que carrega informacao e o pavio contrario.

Gera a tabela que vai embutida no indicador NTSL, com verificacao fora da
amostra (primeiros 60% dos pregoes x 40% finais) e contra o Renko sintetico de
passeio aleatorio, que serve de regua do que e puro acaso.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from universo import universo
from ml_lift import limpar
from sintetico import metricas, renko, caminho

FAIXAS = [(50, 50), (55, 65), (70, 90), (95, 115), (120, 150)]
NOMES = ["50", "55-65", "70-90", "95-115", "120-150"]


def bloco(x: pd.DataFrame) -> dict:
    return dict(n=len(x), ok=x.ok.mean(), mfe=x.mfe.mean(), mfeR=x.mfeR.mean(),
                net=x.net.mean(), R=x.R.mean(), risco=x.risco.mean())


def tabela(x: pd.DataFrame, col_risco="risco") -> pd.DataFrame:
    linhas = []
    for (lo, hi), nome in zip(FAIXAS, NOMES):
        s = x[(x[col_risco] >= lo) & (x[col_risco] <= hi)]
        if len(s) == 0:
            continue
        linhas.append(dict(faixa=nome, **bloco(s)))
    return pd.DataFrame(linhas).set_index("faixa")


def sintetica() -> pd.DataFrame:
    try:
        s = pd.read_pickle("sintetico.pkl")
    except FileNotFoundError:
        s = metricas(renko(caminho(40_000_000, seed=7)))
    s["mfeR"] = s.mfe / s.risco
    s["net"] = s.net_fav * 50
    linhas = []
    for (lo, hi), nome in zip(FAIXAS, NOMES):
        t = s[(s.risco >= lo) & (s.risco <= hi)]
        linhas.append(dict(faixa=nome, n=len(t), ok=t.ok.mean(), mfe=t.mfe.mean(),
                           mfeR=t.mfeR.mean(), net=t.net.mean(), R=t.R.mean(),
                           risco=t.risco.mean()))
    return pd.DataFrame(linhas).set_index("faixa")


def por_periodo(x: pd.DataFrame, frac=0.6):
    dias = np.sort(x.dia.unique())
    corte = dias[int(len(dias) * frac)]
    return tabela(x[x.dia < corte]), tabela(x[x.dia >= corte]), pd.Timestamp(corte)


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    dn, up = universo()
    dn, up = limpar(dn), limpar(up)
    tudo = pd.concat([dn, up])

    print("=== TABELA MESTRA (baixa + alta, universo executavel) ===")
    print(tabela(tudo).round(4).to_string())

    print("\n=== so BAIXA (seta acima) ===")
    print(tabela(dn).round(4).to_string())
    print("\n=== so ALTA (seta abaixo) ===")
    print(tabela(up).round(4).to_string())

    tr, te, corte = por_periodo(tudo)
    print(f"\n=== estabilidade: treino (< {corte.date()}) x teste (>= {corte.date()}) ===")
    cmp = pd.DataFrame({"ok_treino": tr.ok, "ok_teste": te.ok,
                        "mfeR_treino": tr.mfeR, "mfeR_teste": te.mfeR,
                        "n_treino": tr.n, "n_teste": te.n})
    print(cmp.round(4).to_string())

    print("\n=== regua: passeio aleatorio puro (mesma geometria) ===")
    print(sintetica().round(4).to_string())

    print("\n=== frequencia por pregao ===")
    nd = tudo.dia.nunique()
    for (lo, hi), nome in zip(FAIXAS, NOMES):
        s = tudo[(tudo.risco >= lo) & (tudo.risco <= hi)]
        print(f"  pavio {nome:<8} {len(s)/nd:6.1f} sinais/pregao   ({len(s)} em {nd} pregoes)")
