r"""
Compara a base 11R gerada pelo script MQL5 GerarRenko11R.mq5 com a base
exportada do ProfitChart (profitpro-ohlc-11R.csv).

    python comparar_11r.py
    python comparar_11r.py --gerada "C:\...\MQL5\Files\Renko11R.csv"
    python comparar_11r.py --divergencias divergencias.csv
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

RAIZ = os.path.dirname(os.path.abspath(__file__))
MQL5_FILES = r"C:\Users\Carlos\Documents\GitHub\MQL5\MQL5\Files"
COLS = ["data", "o", "h", "l", "c", "buy", "sell", "dur", "qty", "trades"]


def ler(caminho: str) -> pd.DataFrame:
    df = pd.read_csv(caminho, sep=";", encoding="utf-8-sig", decimal=",")
    n = len(df.columns)
    cabecalho = list(df.columns)
    df.columns = COLS + [f"extra{i}" for i in range(n - len(COLS))]
    df["ts"] = pd.to_datetime(df["data"], format="%d/%m/%Y %H:%M:%S.%f")
    # o script MQL5 grava a duracao em ms; o ProfitChart, em minutos
    if any("DuracaoMs" in c for c in cabecalho):
        df["dur"] = np.floor(df["dur"].astype(float) / 600.0) / 100.0
    # o export do ProfitChart vem do mais novo para o mais antigo
    if len(df) > 1 and df["ts"].iloc[0] > df["ts"].iloc[-1]:
        df = df.iloc[::-1]
    return df.reset_index(drop=True)


def pct(x: float) -> str:
    return f"{100 * x:6.2f}%"


def main() -> int:
    p = argparse.ArgumentParser(description="Compara a base 11R gerada com a do ProfitChart.")
    p.add_argument("--gerada", default=os.path.join(MQL5_FILES, "Renko11R.csv"),
                   help="CSV produzido pelo GerarRenko11R.mq5 (fica em MQL5\\Files)")
    p.add_argument("--base", default=os.path.join(RAIZ, "profitpro-ohlc-11R.csv"))
    p.add_argument("--divergencias", default=None,
                   help="grava as barras divergentes num CSV")
    p.add_argument("--tolerancia-qty", type=float, default=0.005,
                   help="diferenca relativa de Quantity aceita por barra")
    args = p.parse_args()

    for caminho in (args.gerada, args.base):
        if not os.path.exists(caminho):
            sys.exit(f"Arquivo nao encontrado: {caminho}")

    g = ler(args.gerada)
    b = ler(args.base)

    print(f"gerada    : {len(g):7d} barras  {g.ts.min()}  ->  {g.ts.max()}")
    print(f"ProfitChart: {len(b):6d} barras  {b.ts.min()}  ->  {b.ts.max()}")

    ini = max(g.ts.min(), b.ts.min())
    fim = min(g.ts.max(), b.ts.max())
    if ini > fim:
        sys.exit("As duas bases nao se sobrepoem no tempo.")
    print(f"sobreposicao: {ini}  ->  {fim}")

    gs = g[(g.ts >= ini) & (g.ts <= fim)].reset_index(drop=True)
    bs = b[(b.ts >= ini) & (b.ts <= fim)].reset_index(drop=True)
    print(f"barras na sobreposicao: gerada {len(gs)}  ProfitChart {len(bs)}")

    n = min(len(gs), len(bs))
    if n == 0:
        sys.exit("Nada a comparar.")
    gs, bs = gs.iloc[:n], bs.iloc[:n]

    igual_ts = gs.ts.values == bs.ts.values
    print(f"\n--- alinhamento posicional (primeiras {n} barras) ---")
    print(f"Data identica          : {pct(igual_ts.mean())}  ({int(igual_ts.sum())}/{n})")
    for col, rot in (("o", "Abertura "), ("h", "Maxima   "),
                     ("l", "Minima   "), ("c", "Fechament")):
        ok = gs[col].values == bs[col].values
        print(f"{rot} identico  : {pct(ok.mean())}  ({int(ok.sum())}/{n})")

    prim = np.where(~(igual_ts & (gs.o.values == bs.o.values) & (gs.c.values == bs.c.values)))[0]
    if len(prim):
        k = int(prim[0])
        print(f"\nprimeira divergencia estrutural na posicao {k}:")
        print("  gerada     :", gs.iloc[k][["data", "o", "h", "l", "c", "qty"]].to_dict())
        print("  ProfitChart:", bs.iloc[k][["data", "o", "h", "l", "c", "qty"]].to_dict())
    else:
        print("\nnenhuma divergencia estrutural (Data + OHLC) nas barras comparadas.")

    print("\n--- volume e agressao ---")
    qty_g, qty_b = gs.qty.values.astype(float), bs.qty.values.astype(float)
    iguais = qty_g == qty_b
    rel = np.abs(qty_g - qty_b) / np.maximum(qty_b, 1)
    print(f"Quantity identica      : {pct(iguais.mean())}  ({int(iguais.sum())}/{n})")
    print(f"Quantity dentro de {args.tolerancia_qty:.1%}: {pct((rel <= args.tolerancia_qty).mean())}")
    print(f"Quantity total         : gerada {qty_g.sum():,.0f}  "
          f"ProfitChart {qty_b.sum():,.0f}  "
          f"dif {100 * (qty_g.sum() / max(qty_b.sum(), 1) - 1):+.3f}%")

    gb, gv = gs.buy.values.astype(float), gs.sell.values.astype(float)
    bb, bv = bs.buy.values.astype(float), bs.sell.values.astype(float)
    if np.isnan(gb).all():
        # historico do WIN$N: o feed do simbolo continuo nao traz o lado agressor
        print("AgressionVol*   : VAZIAS na base gerada -- o historico do simbolo continuo")
        print("                  nao traz o lado agressor. Baixe pelo contrato (WINV26...)")
        print("                  para ter agressao; ver LEIA-ME-11R.md.")
    else:
        # A agressao do MT5 esta noutra escala (ver LEIA-ME-11R.md), mas o que se
        # usa dela -- desequilibrio e delta -- acompanha o ProfitChart de perto.
        for col, rot in (("buy", "AgressionVolBuy "), ("sell", "AgressionVolSell")):
            a, c = gs[col].values.astype(float), bs[col].values.astype(float)
            print(f"{rot}: gerada/ProfitChart = {a.sum() / max(c.sum(), 1):5.3f}  (escalas diferentes)")

        som_g, som_b = np.maximum(gb + gv, 1), np.maximum(bb + bv, 1)
        des_g, des_b = (gb - gv) / som_g, (bb - bv) / som_b
        del_g, del_b = gb - gv, bb - bv
        print(f"  desequilibrio (buy-sell)/(buy+sell): correlacao {np.corrcoef(des_g, des_b)[0, 1]:.4f}, "
              f"mesmo sinal {pct((np.sign(des_g) == np.sign(des_b)).mean())}")
        print(f"  delta (buy-sell)                   : correlacao {np.corrcoef(del_g, del_b)[0, 1]:.4f}, "
              f"mesmo sinal {pct((np.sign(del_g) == np.sign(del_b)).mean())}")

    t_g, t_b = gs.trades.values.astype(float), bs.trades.values.astype(float)
    print(f"Trades          : gerada/ProfitChart = {t_g.sum() / max(t_b.sum(), 1):5.3f}, "
          f"correlacao {np.corrcoef(t_g, t_b)[0, 1]:.4f}  (MT5 agrega negocios no mesmo tick)")

    d = np.abs(gs.dur.values - bs.dur.values)
    print(f"BarDurationF    : |dif| <= 0,02 min em {pct((d <= 0.0201).mean())}")

    if args.divergencias:
        ruim = ~(igual_ts & (gs.o.values == bs.o.values) & (gs.h.values == bs.h.values)
                 & (gs.l.values == bs.l.values) & (gs.c.values == bs.c.values)
                 & (rel <= args.tolerancia_qty))
        saida = pd.concat([
            gs.loc[ruim, ["data", "o", "h", "l", "c", "qty", "trades"]].add_prefix("ger_").reset_index(drop=True),
            bs.loc[ruim, ["data", "o", "h", "l", "c", "qty", "trades"]].add_prefix("pc_").reset_index(drop=True),
        ], axis=1)
        os.makedirs(os.path.dirname(os.path.abspath(args.divergencias)), exist_ok=True)
        saida.to_csv(args.divergencias, sep=";", index=False, encoding="utf-8-sig")
        print(f"\n{len(saida)} barra(s) divergente(s) gravada(s) em {args.divergencias}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
