"""Duas perguntas que sobraram das reversoes.

(1) O stop. Entrar na reversao custa caro: o extremo contrario fica a ~125 pts
    do fechamento, porque o tijolo de reversao ja nasce com o pavio grande. Mede
    aqui um stop alternativo -- a ABERTURA do tijolo de reversao, que fica
    sempre a 50 pts do fechamento e e o nivel que, se perdido, desfaz a propria
    reversao. Mesmo criterio do usuario (o extremo contrario nao ser violado em
    4 tijolos), so que ancorado no nivel que define a reversao.

(2) A agressao a favor. Nos decis controlados por pavio ela nao mexeu o 'ok'
    (amplitude 0.05, dentro do ruido) mas mexeu o pnl. Testa fora da amostra,
    com e sem tijolo fantasma no caminho, e com intervalo de confianca por
    bootstrap de PREGAO (nao de sinal -- sinais do mesmo dia sao correlacionados).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from dados import carregar
from features import preparar
from ml_lift import limpar, split
from reversao_fluxo import extras

BRICK = 50.0
H = 4


def montar(h: int = H) -> pd.DataFrame:
    d = extras(preparar(carregar()))
    d = d[(d.c - d.o).abs() == BRICK].reset_index(drop=True)
    hh, ll, cc, oo = (d[k].to_numpy(float) for k in "hlco")
    dur = d["dur_s"].to_numpy(float)
    qtd = d["qtd"].to_numpy(float)
    dirn = d["dir"].to_numpy(int)
    n = len(d)

    ok_pavio = np.full(n, np.nan)
    ok_abert = np.full(n, np.nan)
    mfe = np.full(n, np.nan)
    net = np.full(n, np.nan)
    fant = np.zeros(n)
    for i in range(n - h):
        f = slice(i + 1, i + h + 1)
        if dirn[i] < 0:
            ok_pavio[i] = float(hh[f].max() <= hh[i])
            ok_abert[i] = float(hh[f].max() <= oo[i])
            mfe[i] = cc[i] - ll[f].min()
            net[i] = cc[i] - cc[i + h]
        else:
            ok_pavio[i] = float(ll[f].min() >= ll[i])
            ok_abert[i] = float(ll[f].min() >= oo[i])
            mfe[i] = hh[f].max() - cc[i]
            net[i] = cc[i + h] - cc[i]
        fant[i] = float(((dur[f] == 0) | (qtd[f] == 0)).any())

    d["ok"] = ok_pavio
    d["ok_ab"] = ok_abert
    d["mfe"] = mfe
    d["net"] = net
    d["fant_caminho"] = fant
    d["risco"] = np.where(dirn < 0, hh - cc, cc - ll)
    d["risco_ab"] = np.abs(oo - cc)                      # sempre 50
    d["pnl"] = np.where(d.ok == 1, d.net, -d.risco)
    d["pnl_ab"] = np.where(d.ok_ab == 1, d.net, -d.risco_ab)
    d["R"] = d.pnl / d.risco
    d["R_ab"] = d.pnl_ab / d.risco_ab
    return d.dropna(subset=["ok"])


def rev(d: pd.DataFrame) -> pd.DataFrame:
    return limpar(d[d.virou == 1].copy())


def boot_dia(x: pd.DataFrame, col: str, n: int = 4000, seed: int = 0):
    """IC95 por bootstrap de pregao: sinais do mesmo dia andam juntos."""
    rng = np.random.default_rng(seed)
    g = [v[col].to_numpy(float) for _, v in x.groupby("dia")]
    if len(g) < 5:
        return np.nan, np.nan
    m = np.empty(n)
    for i in range(n):
        pick = rng.integers(0, len(g), len(g))
        m[i] = np.concatenate([g[j] for j in pick]).mean()
    return np.percentile(m, 2.5), np.percentile(m, 97.5)


def linha(x: pd.DataFrame, nome: str, col_ok="ok", col_pnl="pnl", col_risco="risco") -> dict:
    lo, hi = boot_dia(x, col_pnl)
    return dict(regra=nome, n=len(x), ok=x[col_ok].mean(), risco=x[col_risco].mean(),
                mfe=x.mfe.mean(), pnl=x[col_pnl].mean(), ic_lo=lo, ic_hi=hi,
                pnl_limpo=x[x.fant_caminho == 0][col_pnl].mean())


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    d = montar()
    r = rev(d)
    c = limpar(d[d.virou == 0].copy())
    print(f"reversoes executaveis: {len(r)}   continuacoes: {len(c)}")

    print("\n" + "=" * 84)
    print("PERGUNTA 1 -- o stop: extremo do pavio (~125 pts) x abertura do tijolo (50 pts)")
    print("=" * 84)
    t = []
    for nome, x in (("REVERSAO", r), ("continuacao", c)):
        t.append(dict(grupo=nome, n=len(x),
                      ok_pavio=x.ok.mean(), risco_pavio=x.risco.mean(),
                      pnl_pavio=x.pnl.mean(), R_pavio=x.R.mean(),
                      ok_abert=x.ok_ab.mean(), risco_ab=x.risco_ab.mean(),
                      pnl_abert=x.pnl_ab.mean(), R_abert=x.R_ab.mean()))
    print(pd.DataFrame(t).set_index("grupo").round(4).to_string())
    print("\n  (ok_abert = a abertura do tijolo de reversao nao foi violada em 4 tijolos)")

    for col_ok, col_pnl, col_r, tag in (("ok", "pnl", "risco", "stop no pavio"),
                                        ("ok_ab", "pnl_ab", "risco_ab", "stop na abertura")):
        lo, hi = boot_dia(r, col_pnl)
        print(f"\n  REVERSAO, {tag:<18} pnl = {r[col_pnl].mean():+7.3f} pts  "
              f"IC95[{lo:+.2f}, {hi:+.2f}]  ok={r[col_ok].mean():.3f}  "
              f"limpo={r[r.fant_caminho==0][col_pnl].mean():+.3f}")

    print("\n" + "=" * 84)
    print("PERGUNTA 2 -- agressao a favor da reversao, fora da amostra")
    print("=" * 84)
    tr, te, corte = split(r)
    print(f"treino: {len(tr)} sinais (< {pd.Timestamp(corte).date()})   teste: {len(te)}")
    regras = {
        "todas as reversoes": lambda x: np.ones(len(x), bool),
        "a_favor > 0": lambda x: x.a_favor > 0,
        "a_favor > 0.15": lambda x: x.a_favor > 0.15,
        "a_favor > 0.25": lambda x: x.a_favor > 0.25,
        "a_favor top20% (>0.22)": lambda x: x.a_favor > 0.22,
        "contraste > 0.10": lambda x: x.contraste > 0.10,
        "a_favor>0.15 & risco<=125": lambda x: (x.a_favor > 0.15) & (x.risco <= 125),
        "a_favor>0.15 & perna>=3": lambda x: (x.a_favor > 0.15) & (x.perna >= 3),
    }
    for col_ok, col_pnl, col_r, tag in (("ok", "pnl", "risco", "STOP NO PAVIO"),
                                        ("ok_ab", "pnl_ab", "risco_ab", "STOP NA ABERTURA")):
        print(f"\n--- {tag} ---")
        linhas = []
        for nome, f in regras.items():
            a, b = tr[f(tr)], te[f(te)]
            if len(b) < 60:
                continue
            lo, hi = boot_dia(b, col_pnl)
            linhas.append(dict(regra=nome, n_tr=len(a), pnl_tr=a[col_pnl].mean(),
                               ok_tr=a[col_ok].mean(), n_te=len(b),
                               pnl_te=b[col_pnl].mean(), ok_te=b[col_ok].mean(),
                               ic_lo=lo, ic_hi=hi,
                               pnl_te_limpo=b[b.fant_caminho == 0][col_pnl].mean()))
        print(pd.DataFrame(linhas).set_index("regra").round(3).to_string())
