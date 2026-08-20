"""So os tijolos de REVERSAO: o tijolo anterior tem sentido oposto.

Num Renko 11R a reversao nao e um recorte, e outra geometria. Para nascer um
tijolo de baixa depois de um de alta o preco precisa percorrer 100 pontos contra
a base (nao 50), e o tijolo se abre em base-50 e fecha em base-100. Como a
maxima corrente desde o fechamento anterior comeca perto da base, o pavio
contrario de um tijolo de reversao ja nasce >= ~100 pontos.

Isso significa que "so reversao" e, geometricamente, quase um filtro de pavio
largo -- e a pergunta certa e se sobra alguma coisa DEPOIS de controlar o pavio.

Paineis:
  A  reversao x continuacao, cru
  B  o mesmo, estratificado por faixa de pavio (o controle que importa)
  C  a regua: o mesmo corte no Renko sintetico de passeio aleatorio
  D  fluxo (agressao/tempo/volume) DENTRO das reversoes
  E  features especificas de reversao (tamanho da perna quebrada etc.)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from universo import universo
from ml_lift import limpar

FAIXAS = [(50, 65), (70, 90), (95, 115), (120, 145), (150, 150)]
NOMES = ["50-65", "70-90", "95-115", "120-145", "150"]


def marcar(x: pd.DataFrame) -> pd.DataFrame:
    """virou==1 -> tijolo de reversao (o anterior era do sentido oposto)."""
    x = x.copy()
    x["rev"] = x["virou"].astype(int)
    return x


def bloco(x: pd.DataFrame) -> dict:
    return dict(n=len(x), ok=x.ok.mean(), risco=x.risco.mean(),
                mfe=x.mfe.mean(), mfeR=x.mfeR.mean(),
                net=x.net.mean(), R=x.R.mean(), pnl=x.pnl.mean())


def por_faixa(x: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for (lo, hi), nome in zip(FAIXAS, NOMES):
        s = x[(x.risco >= lo) & (x.risco <= hi)]
        if len(s) < 30:
            continue
        linhas.append(dict(faixa=nome, **bloco(s)))
    return pd.DataFrame(linhas).set_index("faixa") if linhas else pd.DataFrame()


def sintetico_rev() -> pd.DataFrame:
    s = pd.read_pickle("sintetico.pkl")
    s = s.copy()
    s["rev"] = (s.dir != s.dir.shift(1)).astype(int)
    s["mfeR"] = s.mfe / s.risco
    s["net"] = s.net_fav * 50
    return s.iloc[1:]


if __name__ == "__main__":
    pd.set_option("display.width", 240)
    dn, up = universo()
    dn, up = marcar(limpar(dn)), marcar(limpar(up))
    tudo = pd.concat([dn, up])

    print("=" * 78)
    print("PAINEL A -- reversao x continuacao, cru")
    print("=" * 78)
    a = pd.DataFrame([dict(grupo="REVERSAO", **bloco(tudo[tudo.rev == 1])),
                      dict(grupo="continuacao", **bloco(tudo[tudo.rev == 0])),
                      dict(grupo="tudo", **bloco(tudo))]).set_index("grupo")
    print(a.round(4).to_string())

    print("\ndistribuicao do pavio contrario (% dentro do grupo):")
    fx = pd.cut(tudo.risco, [49, 65, 90, 115, 145, 151],
                labels=["50-65", "70-90", "95-115", "120-145", "150"])
    dist = pd.crosstab(fx, tudo.rev, normalize="columns") * 100
    dist.columns = ["continuacao_%", "REVERSAO_%"]
    print(dist.round(2).to_string())

    print("\n" + "=" * 78)
    print("PAINEL B -- estratificado por pavio (o controle que importa)")
    print("=" * 78)
    tr_ = por_faixa(tudo[tudo.rev == 1])
    tc_ = por_faixa(tudo[tudo.rev == 0])
    cmp = pd.DataFrame({"n_rev": tr_.n, "ok_rev": tr_.ok, "n_cont": tc_.n,
                        "ok_cont": tc_.ok, "d_ok": tr_.ok - tc_.ok,
                        "R_rev": tr_.R, "R_cont": tc_.R,
                        "mfe_rev": tr_.mfe, "mfe_cont": tc_.mfe})
    print(cmp.round(4).to_string())

    print("\n" + "=" * 78)
    print("PAINEL C -- a regua: mesmo corte no passeio aleatorio")
    print("=" * 78)
    s = sintetico_rev()
    sa = pd.DataFrame([dict(grupo="REVERSAO", **bloco(s[s.rev == 1])),
                       dict(grupo="continuacao", **bloco(s[s.rev == 0]))]).set_index("grupo")
    print(sa.round(4).to_string())
    print("\nreal x acaso, so reversoes, por faixa de pavio:")
    sr = por_faixa(s[s.rev == 1])
    rr = por_faixa(tudo[tudo.rev == 1])
    print(pd.DataFrame({"n_real": rr.n, "ok_real": rr.ok, "ok_acaso": sr.ok,
                        "lift": rr.ok - sr.ok,
                        "R_real": rr.R, "R_acaso": sr.R,
                        "mfe_real": rr.mfe, "mfe_acaso": sr.mfe}).round(4).to_string())

    print("\n=== por lado (a reversao de alta e a de baixa se comportam igual?) ===")
    print(pd.DataFrame([
        dict(lado="BAIXA rev (seta acima)", **bloco(dn[dn.rev == 1])),
        dict(lado="ALTA  rev (seta abaixo)", **bloco(up[up.rev == 1])),
    ]).set_index("lado").round(4).to_string())
