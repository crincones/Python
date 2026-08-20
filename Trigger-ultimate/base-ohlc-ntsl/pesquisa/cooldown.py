"""Cooldown por lado, medido em TIJOLOS.

Motivo de existir: no Renko, dentro de um lateral TODO tijolo e uma reversao.
Os sinais nascem grudados e as janelas de 8 tijolos se sobrepoem, entao varias
"operacoes" sao na pratica a mesma aposta contada N vezes. Isso infla a
contagem, infla a confianca do placar e, operando, vira exposicao correlacionada
-- risco que nao aparece no pts/sinal.

Mede-se aqui:
    - sinais por pregao e pts por SINAL (o de sempre)
    - pts por PREGAO, que e o que o bolso sente
    - sobreposicao: fracao dos sinais que entram com o anterior do mesmo lado
      ainda aberto
    - IC95 por bootstrap de pregao nas duas metricas

Correcao importante em relacao a medicao anterior: `espacar` usa agora o indice
do TIJOLO (coluna ibar), nao o indice da lista filtrada de sinais. Contar
sinais em vez de tijolos dava um cooldown muito mais agressivo do que o
configurado, e foi o que produziu o "MinBarras nao melhora nada".
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from score import carregar_real, pontuar, espacar, G, B

AGR = dict(cAgr=100)


def boot_dia(x, col, n=4000, seed=0, soma=False):
    """IC95 por pregao. soma=True -> media da SOMA por pregao (pts/pregao)."""
    rng = np.random.default_rng(seed)
    g = [v[col].to_numpy(float) for _, v in x.groupby("dia")]
    if len(g) < 5:
        return np.nan, np.nan
    m = np.empty(n)
    for i in range(n):
        pick = rng.integers(0, len(g), len(g))
        sel = [g[j] for j in pick]
        m[i] = np.mean([s.sum() for s in sel]) if soma else np.concatenate(sel).mean()
    return np.percentile(m, 2.5), np.percentile(m, 97.5)


def sobreposicao(x: pd.DataFrame) -> float:
    """Fracao de sinais que entram com o anterior do MESMO lado ainda aberto."""
    if len(x) == 0:
        return np.nan
    n_ov = 0
    fim = {-1: -10**9, 1: -10**9}
    for ib, lado, ate in zip(x.ibar, x.dir, x.ate):
        if ib < fim[lado]:
            n_ov += 1
        fim[lado] = ib + ate
    return n_ov / len(x)


def avaliar(d, min_score, cd):
    x = d[pontuar(d, AGR) >= min_score]
    x = x[espacar(x, cd)]
    lim = x[x.fant_caminho == 0]
    nd = d.dia.nunique()
    lo, hi = boot_dia(lim, "pts")
    slo, shi = boot_dia(lim, "pts", soma=True)
    por_dia = lim.groupby("dia").pts.sum()
    return dict(cooldown=cd, n=len(x), por_dia=len(x) / nd,
                sobrep=sobreposicao(x),
                n_limpo=len(lim), P=lim.alvo.mean(), pts=lim.pts.mean(),
                ic_lo=lo, ic_hi=hi,
                pts_pregao=por_dia.sum() / nd,
                pp_lo=slo, pp_hi=shi,
                pregoes_pos=(por_dia > 0).mean())


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    d = carregar_real()
    nd = d.dia.nunique()
    print(f"base: {len(d)} reversoes executaveis, {nd} pregoes "
          f"({len(d)/nd:.1f}/pregao)")
    print(f"alvo {G:.0f} pts / risco {B:.0f} pts, horizonte 8 tijolos\n")

    for ms in (50, 60, 70):
        linhas = [avaliar(d, ms, cd) for cd in (0, 2, 3, 4, 5, 6, 8, 12)]
        t = pd.DataFrame(linhas).set_index("cooldown")
        print(f"=== MinScore = {ms} ===")
        print(t.round(3).to_string())
        print()

    print("=== o cooldown por lado tambem espaca o lado oposto? ===")
    x = d[pontuar(d, AGR) >= 60]
    for cd in (0, 4):
        y = x[espacar(x, cd)]
        dif = np.diff(np.sort(y.ibar.to_numpy()))
        print(f"  cooldown={cd}: {len(y)} sinais | distancia mediana entre sinais "
              f"consecutivos (qualquer lado) = {np.median(dif):.1f} tijolos | "
              f"colados (dist=1) = {(dif == 1).mean():.1%}")
