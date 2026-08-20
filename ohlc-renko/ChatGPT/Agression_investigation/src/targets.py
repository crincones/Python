"""
Construcao dos targets (secoes 12-15 do CLAUDE.md).

ESTE E O UNICO MODULO AUTORIZADO A USAR t+1, t+2, t+3.
Nada daqui pode virar feature. As colunas produzidas aqui recebem prefixo
``y_`` ou ``fwd_`` justamente para que o filtro de features possa
rejeita-las mecanicamente.

Vocabulario:
  - EVENTO / candidato   : padrao estrutural observavel em t
                           (pre_seq candles numa direcao + virada em t).
                           Usa somente t e passado.
  - TARGET               : o candidato teve continuacao de cont candles?
                           Usa t+1 .. t+cont-1 (a barra t ja e a 1a da nova
                           direcao, entao "continuacao de N candles"
                           significa N-1 barras futuras alem de t...
                           ver nota abaixo).

NOTA sobre contagem de continuacao
----------------------------------
O CLAUDE.md descreve o padrao:

    DOWN DOWN | UP | UP UP        (pre_seq=2, cont=2)

isto e, apos a barra de virada t (que ja e UP), exigem-se mais ``cont``
barras UP: t+1 .. t+cont. Adotamos essa leitura literal. Portanto
cont=2 usa t+1,t+2 e cont=3 usa t+1,t+2,t+3.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import BRICK_SIZE

TARGET_PREFIXES = ("y_", "fwd_", "evt_", "cand_")


def direction(df: pd.DataFrame) -> pd.Series:
    return np.sign(df["Close"] - df["Open"]).astype(int)


# ---------------------------------------------------------------- candidato
def candidate_mask(df: pd.DataFrame, pre_seq: int, exact: bool = False
                   ) -> tuple[pd.Series, pd.Series]:
    """Candidatos a virada em t. CAUSAL — usa apenas t-pre_seq .. t.

    Retorna (mask, side) onde side = +1 virada para cima, -1 para baixo,
    0 quando nao ha candidato.

    ``exact=False`` (padrao): exige PELO MENOS ``pre_seq`` candles na
    direcao oposta antes de t. ``exact=True``: exige exatamente ``pre_seq``
    (a barra t-pre_seq-1 precisa ser da direcao contraria).
    """
    d = direction(df)
    prev_run = d.shift(1)
    run_id = (d != d.shift(1)).cumsum()
    run_len = d.groupby(run_id).cumcount() + 1
    prev_run_len = run_len.shift(1)

    is_turn = (d != prev_run) & prev_run.notna()
    long_enough = prev_run_len >= pre_seq
    if exact:
        long_enough = prev_run_len == pre_seq

    mask = is_turn & long_enough & (d != 0)
    side = np.where(mask, d, 0)
    return mask.fillna(False), pd.Series(side, index=df.index, dtype=int)


# ------------------------------------------------------------------ target
def continuation_mask(df: pd.DataFrame, cont: int) -> pd.Series:
    """As ``cont`` barras SEGUINTES a t seguem a direcao de t?

    USA FUTURO. Somente para construcao de target.
    """
    d = direction(df)
    ok = pd.Series(True, index=df.index)
    for k in range(1, cont + 1):
        ok &= (d.shift(-k) == d)
    # nas ultimas barras o futuro nao existe -> indefinido
    ok = ok.where(d.shift(-cont).notna())
    return ok


def build_target(df: pd.DataFrame, pre_seq: int, cont: int,
                 exact: bool = False, name: str | None = None) -> pd.DataFrame:
    """Monta um target completo.

    Colunas produzidas (para um dado sufixo S = f"p{pre_seq}c{cont}"):
      cand_S   : 1 se a barra t e candidato estrutural (CAUSAL)
      side_S   : +1/-1 direcao da virada candidata (CAUSAL)
      y_S      : 1 se candidato E teve continuacao (USA FUTURO)
      y3_S     : 0 = nao candidato, 1 = virada p/ cima valida,
                 2 = virada p/ baixo valida (USA FUTURO)
    """
    suf = name or f"p{pre_seq}c{cont}" + ("e" if exact else "")
    mask, side = candidate_mask(df, pre_seq, exact)
    cont_ok = continuation_mask(df, cont)

    out = pd.DataFrame(index=df.index)
    out[f"cand_{suf}"] = mask.astype(int)
    out[f"side_{suf}"] = side
    y = (mask & cont_ok.fillna(False)).astype(int)
    y = y.where(~(mask & cont_ok.isna()))          # sem futuro => NaN
    out[f"y_{suf}"] = y
    out[f"y3_{suf}"] = np.select(
        [y.eq(1) & side.eq(1), y.eq(1) & side.eq(-1)],
        [1, 2],
        default=0,
    )
    return out


# ------------------------------------------------------- excursao economica
def forward_excursions(df: pd.DataFrame, horizon: int = 12) -> pd.DataFrame:
    """MFE/MAE e tempos ate +2/+3 bricks apos entrada no fechamento de t.

    USA FUTURO. Somente para avaliacao economica, nunca como feature.
    A direcao usada e a da propria barra t (sinal operacional).
    """
    d = direction(df).to_numpy()
    c = df["Close"].to_numpy(float)
    hi = df["High"].to_numpy(float)
    lo = df["Low"].to_numpy(float)
    n = len(df)

    mfe = np.full(n, np.nan)
    mae = np.full(n, np.nan)
    t2 = np.full(n, np.nan)
    t3 = np.full(n, np.nan)
    mae_before_2 = np.full(n, np.nan)
    fwd_close = np.full(n, np.nan)

    for i in range(n):
        j_end = min(i + horizon, n - 1)
        if j_end <= i:
            continue
        s = d[i]
        best = -np.inf
        worst = np.inf
        hit2 = hit3 = np.nan
        worst_before2 = 0.0
        for j in range(i + 1, j_end + 1):
            # excursao favoravel/adversa em pontos, na direcao do sinal
            fav = (hi[j] - c[i]) if s > 0 else (c[i] - lo[j])
            adv = (c[i] - lo[j]) if s > 0 else (hi[j] - c[i])
            best = max(best, fav)
            worst = min(worst, -adv)
            if np.isnan(hit2) and fav >= 2 * BRICK_SIZE:
                hit2 = j - i
                worst_before2 = -worst
            if np.isnan(hit3) and fav >= 3 * BRICK_SIZE:
                hit3 = j - i
        mfe[i] = best
        mae[i] = -worst
        t2[i] = hit2
        t3[i] = hit3
        mae_before_2[i] = worst_before2 if not np.isnan(hit2) else -worst
        fwd_close[i] = (c[j_end] - c[i]) * s

    return pd.DataFrame({
        "fwd_mfe_pts": mfe,
        "fwd_mae_pts": mae,
        "fwd_mfe_bricks": mfe / BRICK_SIZE,
        "fwd_mae_bricks": mae / BRICK_SIZE,
        "fwd_bars_to_2bricks": t2,
        "fwd_bars_to_3bricks": t3,
        "fwd_hit2": (~np.isnan(t2)).astype(int),
        "fwd_hit3": (~np.isnan(t3)).astype(int),
        "fwd_mae_before_2bricks": mae_before_2,
        f"fwd_close_move_{horizon}b": fwd_close,
    }, index=df.index)


# ------------------------------------------------------- target em PONTOS
def build_points_target(df: pd.DataFrame, pre_seq: int = 2,
                        target_pts: float = None, horizon: int = None,
                        pessimistic: bool = None, name: str | None = None
                        ) -> pd.DataFrame:
    """Sucesso = +target_pts a favor ANTES de tocar o extremo oposto da
    propria barra de virada.

    USA FUTURO. Somente para construcao de target.

    Definicao operacional
    ---------------------
    Entrada no fechamento da barra de virada ``t``, na direcao dela.

        virada de ALTA  : alvo = Close[t] + P   ;  stop = Low[t]
        virada de BAIXA : alvo = Close[t] - P   ;  stop = High[t]

    Como neste export o fechamento fica sempre no extremo do range, a
    distancia ate o stop e exatamente ``Range[t]`` (50 a 150 pontos),
    enquanto o alvo e fixo. O risco portanto VARIA por evento e o
    R-multiplo do acerto e ``P / Range[t]``.

    Resolucao
    ---------
    Percorre t+1, t+2, ... ate ``horizon``:
      - toca so o alvo   -> 1
      - toca so o stop   -> 0
      - toca os dois na MESMA barra -> ambiguo; com ``pessimistic=True``
        (padrao) conta como stop. A coluna ``ambig_`` marca esses casos
        para que o efeito da convencao seja mensuravel.
      - nao resolve dentro do horizonte -> 0 (timeout), marcado em
        ``outcome_``
      - futuro insuficiente (fim da serie) -> NaN, fora do estudo
    """
    from config import POINTS_HORIZON, POINTS_PESSIMISTIC, TARGET_POINTS

    target_pts = TARGET_POINTS if target_pts is None else target_pts
    horizon = POINTS_HORIZON if horizon is None else horizon
    pessimistic = POINTS_PESSIMISTIC if pessimistic is None else pessimistic
    suf = name or f"pts{int(target_pts)}p{pre_seq}"

    mask, side = candidate_mask(df, pre_seq)
    c = df["Close"].to_numpy(float)
    hi = df["High"].to_numpy(float)
    lo = df["Low"].to_numpy(float)
    m = mask.to_numpy()
    s_all = side.to_numpy()
    n = len(df)

    y = np.full(n, np.nan)
    bars = np.full(n, np.nan)
    stop_lvl = np.full(n, np.nan)
    tgt_lvl = np.full(n, np.nan)
    risk = np.full(n, np.nan)
    ambig = np.zeros(n, dtype=int)
    outcome = np.array([""] * n, dtype=object)

    for i in range(n):
        if not m[i]:
            continue
        s = s_all[i]
        entry = c[i]
        if s > 0:
            tgt, stop = entry + target_pts, lo[i]
        else:
            tgt, stop = entry - target_pts, hi[i]
        tgt_lvl[i], stop_lvl[i] = tgt, stop
        risk[i] = abs(entry - stop)

        res, k_hit = None, None
        for k in range(1, horizon + 1):
            j = i + k
            if j >= n:
                break
            if s > 0:
                hit_t, hit_s = hi[j] >= tgt, lo[j] <= stop
            else:
                hit_t, hit_s = lo[j] <= tgt, hi[j] >= stop
            if hit_t and hit_s:
                ambig[i] = 1
                res, k_hit = (0 if pessimistic else 1), k
                break
            if hit_s:
                res, k_hit = 0, k
                break
            if hit_t:
                res, k_hit = 1, k
                break

        if res is None:
            if i + horizon >= n:
                continue                    # futuro insuficiente -> NaN
            res, k_hit = 0, horizon
            outcome[i] = "timeout"
        else:
            outcome[i] = "target" if res == 1 else "stop"
        y[i], bars[i] = res, k_hit

    out = pd.DataFrame(index=df.index)
    out[f"cand_{suf}"] = mask.astype(int)
    out[f"side_{suf}"] = side
    out[f"y_{suf}"] = y
    out[f"y3_{suf}"] = np.select(
        [(y == 1) & (side == 1), (y == 1) & (side == -1)], [1, 2], default=0)
    out[f"fwd_bars_to_resolution_{suf}"] = bars
    out[f"fwd_stop_level_{suf}"] = stop_lvl
    out[f"fwd_target_level_{suf}"] = tgt_lvl
    out[f"fwd_risk_pts_{suf}"] = risk
    out[f"fwd_rmultiple_{suf}"] = np.where(y == 1, target_pts / np.where(
        risk > 0, risk, np.nan), -1.0)
    out[f"fwd_ambiguous_{suf}"] = ambig
    out[f"fwd_outcome_{suf}"] = outcome
    return out


POINTS_VARIANTS = [
    dict(pre_seq=2),
    dict(pre_seq=3),
]


TARGET_VARIANTS = [
    dict(pre_seq=2, cont=2),
    dict(pre_seq=2, cont=3),
    dict(pre_seq=3, cont=2),
    dict(pre_seq=3, cont=3),
    dict(pre_seq=2, cont=2, exact=True),
    dict(pre_seq=3, cont=2, exact=True),
]


def build_all_targets(df: pd.DataFrame) -> pd.DataFrame:
    parts = [build_target(df, **v) for v in TARGET_VARIANTS]
    parts += [build_points_target(df, **v) for v in POINTS_VARIANTS]
    return pd.concat(parts, axis=1)


def points_suffix(pre_seq: int, target_pts: float = None) -> str:
    from config import TARGET_POINTS
    p = TARGET_POINTS if target_pts is None else target_pts
    return f"pts{int(p)}p{pre_seq}"


def target_suffix(pre_seq: int, cont: int, exact: bool = False) -> str:
    return f"p{pre_seq}c{cont}" + ("e" if exact else "")
