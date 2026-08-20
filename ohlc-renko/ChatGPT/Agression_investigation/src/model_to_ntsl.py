"""
Etapa 11 — exportador CatBoost -> NTSL (secao 28 do CLAUDE.md).

Por que da certo
----------------
O CatBoost usa arvores OBLIVIAS (simetricas): todos os nos de um mesmo
nivel testam a MESMA condicao. Uma arvore de profundidade d tem portanto
apenas d comparacoes e 2^d folhas, e o indice da folha e um numero
binario de d bits:

    idx = sum_i  2^i * [ feature_i > border_i ]

Isso se traduz em NTSL sem recursao e sem vetores:

    idx := 0;
    if f0 > b0 then idx := idx + 1;
    if f1 > b1 then idx := idx + 2;
    if f2 > b2 then idx := idx + 4;
    if idx = 0 then raw := raw + v0 else
    if idx = 1 then raw := raw + v1 else ...

A pontuacao final e

    raw  = escala * soma(folhas) + vies
    prob = 1 / (1 + exp(-raw))

Verificacao
-----------
``verify_python_reimplementation`` compara, barra a barra, a soma das
folhas calculada por este modulo com ``predict(prediction_type=
'RawFormulaVal')`` do proprio CatBoost. Se divergirem, o exportador
levanta erro e nada e gerado.
"""
from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd

from config import MA_PERIOD, NTSL_DIR, RESULTS_DIR
from ntsl_features import NTSL_EXPRESSIONS


# ------------------------------------------------------------------ parse
def parse_model(model) -> dict:
    """Extrai arvores oblivias, bordas e valores de folha do CatBoost."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "model.json"
        model.save_model(str(p), format="json")
        js = json.loads(p.read_text(encoding="utf-8"))

    ff = js["features_info"].get("float_features", [])
    feats = [f.get("feature_id", "") for f in ff]
    borders = [f.get("borders", []) for f in ff]
    flat_idx = [f["flat_feature_index"] for f in ff]
    nan_treat = [f.get("nan_value_treatment", "AsIs") for f in ff]

    trees = []
    for t in js["oblivious_trees"]:
        splits = []
        for s in t["splits"]:
            fi = s["float_feature_index"]
            splits.append({
                "float_feature_index": fi,
                "flat_feature_index": flat_idx[fi],
                "border": float(s["border"]),
                "nan_treatment": nan_treat[fi],
            })
        trees.append({"splits": splits,
                      "leaf_values": [float(v) for v in t["leaf_values"]]})

    sb = js.get("scale_and_bias", [1.0, [0.0]])
    scale = float(sb[0])
    bias = float(sb[1][0]) if isinstance(sb[1], list) else float(sb[1])

    return {"trees": trees, "scale": scale, "bias": bias,
            "float_feature_ids": feats, "flat_feature_index": flat_idx,
            "borders": borders}


# ------------------------------------------------- reimplementacao Python
def raw_score(spec: dict, x: np.ndarray) -> np.ndarray:
    """Soma das folhas para uma matriz X (n, n_features_flat)."""
    n = x.shape[0]
    total = np.zeros(n)
    for tree in spec["trees"]:
        idx = np.zeros(n, dtype=int)
        for bit, s in enumerate(tree["splits"]):
            col = x[:, s["flat_feature_index"]]
            # semantica de ausentes do proprio modelo: AsFalse trata NaN
            # como "nao passou"; AsTrue, como "passou". AsIs = sem NaN.
            nan_side = s.get("nan_treatment", "AsIs") == "AsTrue"
            cond = np.where(np.isnan(col), nan_side, col > s["border"])
            idx += (1 << bit) * cond.astype(int)
        total += np.asarray(tree["leaf_values"])[idx]
    return spec["scale"] * total + spec["bias"]


def probability(spec: dict, x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-raw_score(spec, x)))


def verify_python_reimplementation(model, spec: dict, X: pd.DataFrame,
                                   tol: float = 1e-6) -> dict:
    """Nossa reimplementacao == CatBoost? (pre-requisito da exportacao)"""
    xs = X.replace([np.inf, -np.inf], np.nan).to_numpy(float)
    ours = raw_score(spec, xs)
    theirs = model.predict(X.replace([np.inf, -np.inf], np.nan),
                           prediction_type="RawFormulaVal")
    theirs = np.asarray(theirs, float).ravel()
    diff = np.abs(ours - theirs)
    rep = {"n": int(len(diff)), "max_abs_diff": float(diff.max()),
           "mean_abs_diff": float(diff.mean()),
           "passed": bool(diff.max() < tol)}
    if not rep["passed"]:
        raise AssertionError(
            f"reimplementacao divergiu do CatBoost: max|d| = {diff.max():.3e}")
    return rep


# ------------------------------------------------------- geracao do NTSL
def _var_for(feature: str) -> tuple[str, int]:
    """Traduz 'AggBalanceNorm_lag2' -> (nome base, lag)."""
    if "_lag" in feature:
        base, lag = feature.split("_lag")
        return base, int(lag)
    return feature, 0


def _idx(lag: int) -> str:
    """Indice de serie NTSL: lag 0 fica implicito, como no resto do repo."""
    return "" if lag == 0 else f"[{lag}]"


def emit_feature_expression(feature: str) -> str:
    base, lag = _var_for(feature)
    if base not in NTSL_EXPRESSIONS:
        raise KeyError(f"feature sem expressao NTSL conhecida: {feature}")
    if base == "AggBalanceChange":
        return f"(balNorm{_idx(lag)} - balNorm[{lag + 1}])"
    return NTSL_EXPRESSIONS[base].format(lag=lag).replace("[0]", "")


def _num(v: float) -> str:
    """Literal decimal puro. NTSL nao aceita notacao cientifica (1e-05),
    entao nunca usamos '%g' aqui."""
    s = f"{v:.12f}".rstrip("0")
    return s + "0" if s.endswith(".") else s


def _addend(v: float) -> str:
    """Emite '+ x' ou '- |x|'. NTSL nao gosta de 'raw + -0.5'."""
    return f"- {_num(abs(v))}" if v < 0 else f"+ {_num(v)}"


def generate_ntsl_model_block(spec: dict, feature_names: list[str],
                              threshold: float) -> str:
    """Bloco NTSL que calcula ``raw`` somando as arvores."""
    L = []
    L.append("//=== MODELO CATBOOST GERADO AUTOMATICAMENTE ===============")
    L.append(f"//  arvores: {len(spec['trees'])}   "
             f"escala: {spec['scale']:.10g}   vies: {spec['bias']:.10g}")
    L.append(f"//  equivale a probabilidade >= {threshold:.4f}")
    L.append("//  NAO EDITAR A MAO — regenerar com src/model_to_ntsl.py")
    L.append("")
    L.append("raw := 0;")
    for ti, tree in enumerate(spec["trees"]):
        d = len(tree["splits"])
        L.append(f"//--- arvore {ti} (profundidade {d}) ---")
        L.append("idx := 0;")
        for bit, s in enumerate(tree["splits"]):
            fname = feature_names[s["flat_feature_index"]]
            expr = emit_feature_expression(fname)
            L.append(f"if {expr} > {_num(s['border'])} then "
                     f"idx := idx + {1 << bit};   // {fname}")
        vals = tree["leaf_values"]
        for li, v in enumerate(vals):
            kw = "if" if li == 0 else "else if"
            tail = ";" if li == len(vals) - 1 else ""
            L.append(f"{kw} idx = {li} then raw := raw {_addend(v)}{tail}")
        L.append("")
    if spec["scale"] != 1.0 or spec["bias"] != 0.0:
        L.append(f"raw := {_num(spec['scale'])} * raw "
                 f"{_addend(spec['bias'])};")
    return "\n".join(L)


HEADER = """//------------------------------------------------------------------
// {name}  —  Renko WIN  —  ProfitChart Pro / NTSL
//
//   NON-REPAINT           (uma barra fechada nunca muda de sinal)
//   NO-CONFIRMATION       (nao espera t+1)
//   SIGNAL-ON-CLOSED-BAR  (a seta sai no fechamento da barra da virada)
//
// Gerado automaticamente por src/model_to_ntsl.py a partir do modelo
// CatBoost treinado em data/processed/dataset.parquet.
//
// Modelo   : CatBoost, {n_trees} arvores oblivias de profundidade {depth}
// Features : {n_feats} (somente as calculaveis em NTSL — ver abaixo)
// Threshold: {threshold:.4f} de probabilidade, aplicado como
//            raw >= {raw_threshold:.10g}   (escolhido na validacao,
//            nunca no teste final)
//
// POR QUE NAO HA SIGMOIDE AQUI: a probabilidade do CatBoost e
// 1/(1+exp(-raw)), e nenhum dos indicadores ja compilados deste repo usa
// Exp(). Como a sigmoide e estritamente crescente,
//     prob >= T   <=>   raw >= ln(T/(1-T))
// entao comparar o score bruto contra o logito do threshold da EXATAMENTE
// o mesmo sinal, sem precisar de funcao nao verificada. O valor
// ln(T/(1-T)) foi calculado em Python e esta fixado no input LimiarRaw.
//
//==================================================================
// LEIA ANTES DE OPERAR
//==================================================================
{honesty}
//==================================================================
// AUSENCIA DE LOOK-AHEAD
//==================================================================
// Todas as expressoes abaixo usam indices >= 0 (barra corrente e
// passado). Nao existe nenhuma referencia a barras futuras — o NTSL
// nem sequer permite indice negativo. O sinal de uma barra depende
// exclusivamente de dados congelados no fechamento dela.
//
// REPINTURA DURANTE A FORMACAO: enquanto o brick corrente nao fecha,
// High, Low, AgressionVolBuy, AgressionVolSell e QuantityVol dele ainda
// crescem, entao a seta pode piscar. Assim que o brick FECHA os valores
// congelam e a seta fica definitiva. Nenhuma barra ja fechada muda de
// sinal depois — que e a definicao de nao repintar. Isso e consequencia
// direta de pedir sinal no proprio candle da virada (requisito 3 do
// CLAUDE.md), nao um defeito do codigo.
//
//==================================================================
// LIMITACAO DE FEATURES
//==================================================================
// O NTSL (funcoes verificadas nos indicadores ja compilados) NAO expoe
// o numero de negocios da barra. Todas as features derivadas de Trades
// ficaram de fora do modelo exportado. O CSV de pesquisa as contem e
// elas foram avaliadas — ver reports/final_report.md.
//
// Inserir no MESMO painel do grafico de precos.
//------------------------------------------------------------------
"""


def build_indicator(spec: dict, feature_names: list[str], threshold: float,
                    name: str = "ReversalDetectorClaude",
                    pre_seq: int = 2, ma_period: int = MA_PERIOD,
                    honesty_note: str = "") -> str:
    depth = len(spec["trees"][0]["splits"]) if spec["trees"] else 0
    max_lag = max(_var_for(f)[1] for f in feature_names) + 1
    t = min(max(threshold, 1e-9), 1 - 1e-9)
    raw_threshold = math.log(t / (1 - t))

    head = HEADER.format(name=name, n_trees=len(spec["trees"]), depth=depth,
                         n_feats=len(feature_names), threshold=threshold,
                         raw_threshold=raw_threshold, honesty=honesty_note)

    body = f"""
input
  LimiarRaw({raw_threshold:.10g});   // = ln(T/(1-T)) para T = {threshold:.4f}
  PreSeq({pre_seq});                 // candles consecutivos exigidos antes da virada
  PeriodoMedia({ma_period});         // janela das medias moveis das features
  MostrarScore(0);                   // 1 = escreve o score bruto x100 junto da seta
  MostrarCompras(1);
  MostrarVendas(1);
  MinBarras(0);                      // distancia minima entre setas do mesmo lado
  OffsetFrac(0.60);                  // afastamento da seta, em fracao do range medio
  TamFonte(10);

var
  minimo, idx                     : integer;
  dirn, runLen                    : integer;
  barrasC, barrasV                : integer;
  agrB, agrS, qtd, dur            : float;
  rng, rngSafe, corpo, totAgr     : float;
  balNorm, imbal                  : float;
  mDur, mRng, mTot, mQtd          : float;
  raw                             : float;
  ehVirada                        : boolean;
  cor                             : integer;

begin
  //--- grandezas brutas da barra (viram serie automaticamente) --------
  agrB   := AgressionVolBuy();
  agrS   := AgressionVolSell();
  qtd    := QuantityVol(false, false);
  dur    := BarDurationF();
  rng    := High - Low;
  corpo  := Abs(Close - Open);
  totAgr := agrB + agrS;

  //--- protecao numerica: RangeSafe = max(High-Low, epsilon) ----------
  rngSafe := rng;
  if rngSafe < 1 then rngSafe := 1;

  balNorm := (agrB - agrS) / rngSafe;
  if totAgr > 0 then imbal := (agrB - agrS) / totAgr else imbal := 0;

  //--- direcao e comprimento da sequencia corrente (somente ate t) ----
  if Close > Open then
    dirn := 1
  else if Close < Open then
    dirn := -1
  else
    dirn := 0;

  if CurrentBar <= 1 then
    runLen := 1
  else if dirn = dirn[1] then
    runLen := runLen[1] + 1
  else
    runLen := 1;

  //--- medias moveis causais (janela terminando na barra corrente) ----
  mDur := Media(PeriodoMedia, dur);
  mRng := Media(PeriodoMedia, rng);
  mTot := Media(PeriodoMedia, totAgr);
  mQtd := Media(PeriodoMedia, qtd);
  if mRng <= 0 then mRng := 1;
  if mTot <= 0 then mTot := 1;
  if mQtd <= 0 then mQtd := 1;

  barrasC := barrasC[1] + 1;
  barrasV := barrasV[1] + 1;

  minimo := PeriodoMedia + {max_lag} + PreSeq + 2;

  if CurrentBar >= minimo then
  begin
    //--- CANDIDATO ESTRUTURAL: PreSeq barras numa direcao e virada em t
    //    Usa apenas t-1..t-PreSeq. Nada de futuro.
    ehVirada := (dirn <> 0) and (dirn[1] <> 0) and (dirn[1] <> dirn)
                and (runLen[1] >= PreSeq);

    if ehVirada then
    begin
{{MODEL_BLOCK}}

      if raw >= LimiarRaw then
      begin
        if (dirn = 1) and (MostrarCompras = 1) and (barrasC >= MinBarras) then
        begin
          cor := RGB(0, 180, 90);
          if MostrarScore = 1 then
            PlotText("▲ " + Round(raw * 100), cor, 0, TamFonte, Low - OffsetFrac * mRng)
          else
            PlotText("▲", cor, 0, TamFonte, Low - OffsetFrac * mRng);
          barrasC := 0;
        end;

        if (dirn = -1) and (MostrarVendas = 1) and (barrasV >= MinBarras) then
        begin
          cor := RGB(220, 40, 40);
          if MostrarScore = 1 then
            PlotText("▼ " + Round(raw * 100), cor, 2, TamFonte, High + OffsetFrac * mRng)
          else
            PlotText("▼", cor, 2, TamFonte, High + OffsetFrac * mRng);
          barrasV := 0;
        end;
      end;
    end;
  end;
end;
"""
    block = generate_ntsl_model_block(spec, feature_names, threshold)
    block = "\n".join("    " + ln if ln.strip() else ln
                      for ln in block.split("\n"))
    return head + body.replace("{MODEL_BLOCK}", block)


def export(model, feature_names: list[str], threshold: float,
           X_verify: pd.DataFrame, name: str = "ReversalDetectorClaude",
           pre_seq: int = 2, honesty_note: str = "") -> dict:
    spec = parse_model(model)
    verif = verify_python_reimplementation(model, spec, X_verify)

    code = build_indicator(spec, feature_names, threshold, name, pre_seq,
                           honesty_note=honesty_note)
    path = NTSL_DIR / f"{name}.ntsl"
    path.write_text(code, encoding="utf-8")

    spec_out = {"n_trees": len(spec["trees"]),
                "depth": len(spec["trees"][0]["splits"]) if spec["trees"] else 0,
                "scale": spec["scale"], "bias": spec["bias"],
                "threshold": threshold, "features": feature_names,
                "verification": verif,
                "ntsl_file": str(path), "n_lines": code.count("\n") + 1}
    (RESULTS_DIR / "11_ntsl_export.json").write_text(
        json.dumps(spec_out, indent=2), encoding="utf-8")
    return spec_out
