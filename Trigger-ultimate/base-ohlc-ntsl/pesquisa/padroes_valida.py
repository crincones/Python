"""O teste correto para um achado de varredura: o maximo de 438 regras contra o
maximo sob permutacao.

Uma regra com lift +0.033 e n=271 esta a ~1.1 desvio-padrao. Isso nao diz nada
sozinho -- foi a MELHOR de 438. A pergunta certa e: sob a hipotese nula, qual o
lift maximo que aparece quando se varrem 438 regras? Se o observado nao passa
desse maximo, nao ha achado.

Permutacao: embaralha o resultado DENTRO de cada pregao. Preserva o numero de
sinais por dia e a taxa de acerto do dia (portanto a deriva e o regime), destroi
apenas a ligacao entre o padrao e o desfecho.

Roda tambem os dois candidatos que passaram no controle por lado, com bootstrap
de pregao e walk-forward.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from padroes import bases, condicoes, split, G, B

CANDIDATOS = ["pav<=110 & dext50<=0.5", "pav<=110 & pos50>=0.8"]


def matriz(r, s, min_n=200, min_ac=300):
    """Matriz booleana regras x sinais, e o p do acaso de cada regra."""
    import itertools
    Cr, Cs = condicoes(r), condicoes(s)
    nomes = list(Cr)
    regras, linhas, p_ac = [], [], []
    for k in (1, 2):
        for combo in itertools.combinations(nomes, k):
            mr = np.logical_and.reduce([Cr[n].to_numpy() for n in combo])
            ms = np.logical_and.reduce([Cs[n].to_numpy() for n in combo])
            if mr.sum() < min_n or ms.sum() < min_ac:
                continue
            regras.append(" & ".join(combo))
            linhas.append(mr)
            p_ac.append(s.alvo.to_numpy()[ms].mean())
    return regras, np.array(linhas), np.array(p_ac)


def maxlift(M, n_por_regra, p_ac, y):
    return ((M @ y) / n_por_regra - p_ac).max()


def boot_dia(x, col, n=4000, seed=0):
    rng = np.random.default_rng(seed)
    g = [v[col].to_numpy(float) for _, v in x.groupby("dia")]
    if len(g) < 5:
        return np.nan, np.nan
    m = np.empty(n)
    for i in range(n):
        pick = rng.integers(0, len(g), len(g))
        m[i] = np.concatenate([g[j] for j in pick]).mean()
    return np.percentile(m, 2.5), np.percentile(m, 97.5)


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    r, s = bases()
    r = r.reset_index(drop=True)
    regras, M, p_ac = matriz(r, s)
    n_reg = M.sum(axis=1).astype(float)
    y = r.alvo.to_numpy(float)
    obs = (M @ y) / n_reg - p_ac
    print(f"{len(regras)} regras | {len(r)} sinais | lift observado maximo = {obs.max():+.4f}")
    print(f"  melhor regra: {regras[int(np.argmax(obs))]}")

    # --- permutacao intra-pregao, corrigida para a varredura -------------
    dia = r.dia.to_numpy()
    grupos = [np.where(dia == d)[0] for d in np.unique(dia)]
    rng = np.random.default_rng(0)
    NP = 400
    nulo = np.empty(NP)
    for i in range(NP):
        yp = y.copy()
        for idx in grupos:
            yp[idx] = rng.permutation(yp[idx])
        nulo[i] = maxlift(M, n_reg, p_ac, yp)
    p_val = (nulo >= obs.max()).mean()
    print(f"\n=== permutacao intra-pregao, {NP} sorteios ===")
    print(f"  lift maximo sob o nulo: media {nulo.mean():+.4f}  dp {nulo.std():.4f}  "
          f"p95 {np.percentile(nulo, 95):+.4f}  max {nulo.max():+.4f}")
    print(f"  lift maximo observado : {obs.max():+.4f}")
    print(f"  >>> p (corrigido para as {len(regras)} regras) = {p_val:.4f}")

    # --- os dois candidatos, individualmente -----------------------------
    print("\n=== os candidatos que passaram no controle por lado ===")
    Cr = condicoes(r)
    tr, te, corte = split(r)
    dias = np.sort(r.dia.unique())
    blocos = np.array_split(dias, 5)
    for regra in CANDIDATOS:
        m = np.logical_and.reduce([Cr[n].to_numpy() for n in regra.split(" & ")])
        a = r[m]
        j = regras.index(regra)
        lo, hi = boot_dia(a, "pts")
        plo, phi = boot_dia(a, "alvo")
        print(f"\n  {regra}")
        print(f"    n={len(a)} ({len(a)/r.dia.nunique():.1f}/pregao)  "
              f"P={a.alvo.mean():.4f} IC95[{plo:.4f}, {phi:.4f}]  acaso={p_ac[j]:.4f}  "
              f"breakeven={B/(G+B):.4f}")
        print(f"    pts/sinal={a.pts.mean():+.2f} IC95[{lo:+.2f}, {hi:+.2f}]")
        z = (obs[j] - nulo.mean()) / nulo.std()
        print(f"    lift={obs[j]:+.4f}  vs maximo do nulo {nulo.mean():+.4f}+-{nulo.std():.4f}"
              f"  -> z={z:+.2f}")
        wf = []
        for k, b in enumerate(blocos, 1):
            g = a[a.dia.isin(b)]
            wf.append(dict(dobra=k, n=len(g), P=g.alvo.mean(), pts=g.pts.mean()))
        w = pd.DataFrame(wf).set_index("dobra")
        print("    walk-forward:", " | ".join(
            f"d{i}: n={int(v.n)} P={v.P:.3f} pts={v.pts:+.1f}" for i, v in w.iterrows()))
        print(f"    dobras com pts>0: {(w.pts > 0).sum()}/5   "
              f"com P>breakeven: {(w.P > B/(G+B)).sum()}/5")
