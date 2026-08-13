#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validar_sr.py
=============
Validacao walk-forward rolante dos niveis produzidos por gerar_sr.py.

Corrige os tres defeitos do validador embutido:
  1. HORIZONTE  - reconstroi os niveis a cada mes e mede so o mes seguinte,
                  em vez de construir uma vez e medir 12 meses. Assim o nivel
                  e testado na idade em que ele e realmente usado.
  2. METRICA    - alvo continuo (MFE / MAE / edge em pontos) em vez de um
                  binario ancorado em ~0,55, que quase nao tem poder.
  3. PLACEBO    - baseline PAREADO: cada nivel real ganha um gemeo deslocado
                  lateralmente, no mesmo regime de preco e no mesmo mes.
Alem disso, reporta a CURVA POR DECIL de relevancia: a pergunta util nao e
"os niveis batem o acaso?", e sim "o score discrimina?".

Efeito colateral util: grava eventos_toque.csv, que e exatamente o dataset
por evento (nao por nivel) que alimentaria um CatBoost depois.

Uso:
    python validar_sr.py --csv WIN_M1.csv --dist-media 250 --linhas 20 \\
        --inicio-teste 2023-01-01 --eventos eventos_toque.csv
"""

from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

import gerar_sr as g


def montar_args(ns) -> object:
    """Reaproveita o namespace de parametros esperado por gerar_sr."""
    class A:
        pass
    a = A()
    for k, v in vars(ns).items():
        setattr(a, k.replace("-", "_"), v)
    return a


def deslocar_placebo(preco: float, ocupados: np.ndarray, desloc: float,
                     meia_zona: float, rng) -> float | None:
    """
    Gemeo lateral do nivel: mesmo mes, mesmo regime de preco, mesma distancia
    da referencia -- so nao e um nivel. Nao pode encostar em OUTRO nivel real
    (o proprio e excluido da checagem) nem sobrepor zona com ele.
    """
    outros = ocupados[np.abs(ocupados - preco) > 1e-6]
    for cand in rng.permutation([preco + desloc, preco - desloc]):
        if outros.size == 0 or np.all(np.abs(outros - cand) >= 2.5 * meia_zona):
            return float(cand)
    return None


def rodar(ns) -> int:
    args = montar_args(ns)
    print(f"Lendo {ns.csv} ...")
    df = g.carregar(ns.csv, ns.data_inicio, ns.data_limite)
    print(f"  {len(df):,} barras | {df['DT'].iloc[0]:%d/%m/%Y} -> {df['DT'].iloc[-1]:%d/%m/%Y}")

    rng = np.random.default_rng(11)
    ini_teste = pd.Timestamp(ns.inicio_teste) if ns.inicio_teste else \
        df["DT"].iloc[0] + pd.DateOffset(months=ns.hist_min)
    bordas = pd.date_range(ini_teste, df["DT"].iloc[-1], freq=f"{ns.passo_meses}MS")
    if len(bordas) < 3:
        print("Historico insuficiente para walk-forward.")
        return 1

    registros: list[dict] = []
    print(f"  {len(bordas) - 1} janelas de {ns.passo_meses} mes(es)\n")

    for k in range(len(bordas) - 1):
        corte, fim = bordas[k], bordas[k + 1]
        treino = df[df["DT"] < corte]
        if ns.hist_meses > 0:
            treino = treino[treino["DT"] >= corte - pd.DateOffset(months=ns.hist_meses)]
        teste = df[(df["DT"] >= corte) & (df["DT"] < fim)]
        if len(treino) < 20000 or len(teste) < 1000:
            continue

        treino = treino.reset_index(drop=True)
        teste = teste.reset_index(drop=True)
        ref = float(treino["CLOSE"].iloc[-1])

        niveis, info = g.construir_niveis(treino, args, ref)
        escolhidos = g.selecionar(niveis, ref, ns.linhas, info["sep_min"],
                                  ns.min_toques, ns.relev_min, ns.min_resolvidos)
        if not escolhidos:
            continue

        hi = teste["HIGH"].to_numpy(float)
        lo = teste["LOW"].to_numpy(float)
        cl = teste["CLOSE"].to_numpy(float)
        dt = teste["DT"].to_numpy()
        mz = info["meia_zona"]
        mov = info["mov_min"]
        fs = g.indice_fim_sessao(teste)
        ocupados = np.array([n.preco for n in escolhidos])

        for n in escolhidos:
            comuns = {
                "janela": f"{corte:%Y-%m}", "preco": n.preco,
                "relevancia": n.relevancia, "toques_hist": n.toques,
                "resolvidos_hist": n.resolvidos,
                "rejeicoes_hist": n.rejeicoes, "taxa_rej": round(n.taxa_rej, 4),
                "rej_pond": round(n.rej_pond, 3), "n_fontes": len(n.fontes),
                "fontes": "|".join(sorted(n.fontes)), "flip": n.flip,
                "idade_dias": round(n.idade_dias, 1),
                "vol_zona": n.vol_zona, "tpo_zona": n.tpo_zona,
                "dist_ref": round(n.preco - ref, 1),
                "acima_ref": n.preco > ref,
            }
            for ev in g.eventos_toque(n.preco, hi, lo, cl, dt, mz,
                                      ns.janela, ns.sep_barras, fs, mov):
                registros.append({**comuns, **ev, "tipo": "real"})

            p_pl = deslocar_placebo(n.preco, ocupados, mz * ns.desloc_zonas,
                                    mz, rng)
            if p_pl is None:
                continue
            for ev in g.eventos_toque(p_pl, hi, lo, cl, dt, mz,
                                      ns.janela, ns.sep_barras, fs, mov):
                registros.append({**comuns, "preco": p_pl, "relevancia": np.nan,
                                  **ev, "tipo": "placebo"})

        print(f"  [{k + 1:>3}/{len(bordas) - 1}] {corte:%Y-%m}  "
              f"niveis={len(escolhidos):>3}  eventos={len(registros):>6}", flush=True)

    if not registros:
        print("Nenhum evento coletado.")
        return 1

    ev = pd.DataFrame(registros)
    if ns.eventos:
        ev.to_csv(ns.eventos, index=False)
        print(f"\n  Eventos gravados em {ns.eventos}  ({len(ev):,} linhas)")

    relatorio(ev, ns)
    return 0


def relatorio(ev: pd.DataFrame, ns) -> None:
    real = ev[ev["tipo"] == "real"]
    plac = ev[ev["tipo"] == "placebo"]

    L = ["", "=" * 74, "VALIDACAO WALK-FORWARD ROLANTE", "=" * 74,
         f"Janelas            : {ev['janela'].nunique()}  "
         f"({ev['janela'].min()} -> {ev['janela'].max()})",
         f"Eventos reais      : {len(real):,}   placebo: {len(plac):,}", ""]

    def bloco(nome, d):
        if d.empty:
            return f"  {nome:<10} (sem eventos)"
        return (f"  {nome:<10} MFE {d['mfe'].mean():7.1f}   MAE {d['mae'].mean():7.1f}   "
                f"edge {d['edge'].mean():+7.1f}   n={len(d):,}")

    L += ["MEDIAS (pontos, janela de %d barras apos o toque)" % ns.janela,
          bloco("real", real), bloco("placebo", plac)]

    # desfecho ORDENADO: quem chegou primeiro, alvo ou stop
    if "res" in ev.columns:
        L += ["", "TAXA DE REJEICAO (barreira ordenada, so toques resolvidos)"]
        for nome, d in [("real", real), ("placebo", plac)]:
            r = d[d["res"] != 0]
            if r.empty:
                L.append(f"  {nome:<10} (sem toques resolvidos)")
                continue
            v = (r["res"] > 0).mean()
            se = np.sqrt(v * (1 - v) / len(r))
            L.append(f"  {nome:<10} {v:.4f} +- {se:.4f}   n={len(r):,}   "
                     f"(indefinidos: {(d['res'] == 0).mean() * 100:.0f}%)")
        a, b = real[real["res"] != 0], plac[plac["res"] != 0]
        if len(a) > 30 and len(b) > 30:
            va, vb = (a["res"] > 0).mean(), (b["res"] > 0).mean()
            se = np.sqrt(va * (1 - va) / len(a) + vb * (1 - vb) / len(b))
            L.append(f"  diferenca  {va - vb:+.4f}   z = {(va - vb) / se:.2f}")

    # teste de diferenca (Welch)
    if len(plac) > 30 and len(real) > 30:
        a, b = real["edge"], plac["edge"]
        se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
        t = (a.mean() - b.mean()) / se if se > 0 else np.nan
        L += ["", f"  Diferenca real - placebo : {a.mean() - b.mean():+.1f} pts   t = {t:.2f}"]

    # ---- a pergunta que interessa: o score discrimina? ----
    L += ["", "-" * 74, "CURVA POR DECIL DE RELEVANCIA (so eventos reais)", "-" * 74,
          "  decil   relev_med    MFE      MAE     edge      n"]
    r = real.dropna(subset=["relevancia"]).copy()
    if len(r) >= 100:
        r["decil"] = pd.qcut(r["relevancia"].rank(method="first"), 10,
                             labels=False, duplicates="drop") + 1
        gr = r.groupby("decil").agg(relev=("relevancia", "mean"), mfe=("mfe", "mean"),
                                    mae=("mae", "mean"), edge=("edge", "mean"),
                                    n=("edge", "size"))
        for d, row in gr.iterrows():
            L.append(f"  {int(d):>5}   {row['relev']:8.1f} {row['mfe']:8.1f} "
                     f"{row['mae']:8.1f} {row['edge']:+8.1f} {int(row['n']):>6}")
        rho = r["relevancia"].corr(r["edge"], method="spearman")
        L += ["", f"  Spearman(relevancia, edge) = {rho:+.4f}"]
        L += [f"  Edge decil 10 - decil 1    = {gr['edge'].iloc[-1] - gr['edge'].iloc[0]:+.1f} pts"]
    else:
        L.append("  (eventos insuficientes)")

    L += ["", "-" * 74, "COMO LER", "-" * 74,
          "  t > 2 na diferenca real-placebo : os niveis valem mais que precos vizinhos.",
          "  Spearman > 0 e curva de decil crescente : o SCORE discrimina -> vale treinar",
          "    um modelo, porque ha variacao de qualidade a explorar.",
          "  Curva plana com t alto : os niveis prestam, mas o score nao ordena;",
          "    o ganho esta em repesar features (ai o CatBoost entra bem).",
          "  Curva plana e t ~ 0 : as features estao erradas; trocar de modelo nao salva.",
          "=" * 74]
    print("\n".join(L))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validacao walk-forward dos niveis de S/R.")
    ap.add_argument("--csv", required=True)
    ap.add_argument("--eventos", default="eventos_toque.csv")
    ap.add_argument("--inicio-teste", default=None, help="AAAA-MM-DD do 1o mes testado")
    ap.add_argument("--hist-min", type=int, default=18, help="Meses minimos antes do 1o teste")
    ap.add_argument("--hist-meses", type=int, default=0,
                    help="Meses de historico por reconstrucao (0 = tudo)")
    ap.add_argument("--passo-meses", type=int, default=1)
    ap.add_argument("--desloc-zonas", type=float, default=3.0,
                    help="Deslocamento do placebo em multiplos da meia-zona "
                         "(precisa passar de 2 para nao encostar na zona real)")
    # espelham gerar_sr.py
    ap.add_argument("--data-inicio", default=None)
    ap.add_argument("--data-limite", default=None)
    ap.add_argument("--linhas", type=int, default=20)
    ap.add_argument("--dist-media", type=float, default=250.0)
    ap.add_argument("--tick", type=float, default=5.0)
    ap.add_argument("--zona-frac", type=float, default=0.22)
    ap.add_argument("--sep-frac", type=float, default=0.85)
    ap.add_argument("--fusao-frac", type=float, default=0.18)
    ap.add_argument("--mov-frac", type=float, default=0.80)
    ap.add_argument("--janela", type=int, default=90)
    ap.add_argument("--sep-barras", type=int, default=30)
    ap.add_argument("--meia-vida", type=float, default=90.0)
    ap.add_argument("--meia-vida-perfil", type=float, default=365.0)
    ap.add_argument("--pivo-n", type=int, default=3)
    ap.add_argument("--redondos", type=float, default=1000.0)
    ap.add_argument("--min-toques", type=int, default=3)
    ap.add_argument("--min-resolvidos", type=int, default=3)
    ap.add_argument("--relev-min", type=float, default=0.0)
    ap.add_argument("--auto-escala", dest="auto_escala", action="store_true", default=True)
    ap.add_argument("--sem-auto-escala", dest="auto_escala", action="store_false")
    ap.add_argument("--zona-atr", type=float, default=1.2)
    ap.add_argument("--mov-atr", type=float, default=0.55)
    return rodar(ap.parse_args())


if __name__ == "__main__":
    sys.exit(main())