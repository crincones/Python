# 13 — Teste de regras isoladas (`pts100p2`)

Universo: 3489 candidatos em 29 pregoes (apenas DESENVOLVIMENTO).  
Taxa-base: **0.5758** · expectativa base: **+0.0372 R**

## Hipotese do usuario, isolada

| regra | n | /dia | precision | IC95 Wilson | taxa-base | edge | expectativa R | Δ vs base | bate a base? |
|---|---|---|---|---|---|---|---|---|---|
| HIPOTESE: AggTotalNorm[t] > [t-1] | 1955 | 67.41 | 0.5719 | [0.5498, 0.5936] | 0.5758 | -0.0039 | +0.0157 | -0.0215 | nao |
| controle: AggTotalNorm[t] < [t-1] | 1520 | 52.41 | 0.5829 | [0.5579, 0.6074] | 0.5758 | +0.0071 | +0.0683 | +0.0312 | nao |
| AggTotalNorm_ratio1 > q50 (1.11) | 1697 | 58.52 | 0.5946 | [0.5710, 0.6177] | 0.5758 | +0.0188 | +0.0553 | +0.0181 | nao |
| AggTotalNorm_ratio1 > q70 (1.60) | 1018 | 35.1 | 0.5982 | [0.5678, 0.6279] | 0.5758 | +0.0224 | +0.0550 | +0.0178 | nao |
| AggTotalNorm_ratio1 > q90 (2.69) | 340 | 11.72 | 0.5912 | [0.5382, 0.6421] | 0.5758 | +0.0154 | +0.0385 | +0.0013 | nao |

## Varredura de todas as comparacoes t vs t-1

- regras testadas (n >= 100): **138**
- regras cujo IC95 fica acima da taxa-base: **9**
- falsos positivos esperados por acaso a 95%: **6.9**

| regra | n | precision | IC95 | edge | expectativa R | Δ vs base |
|---|---|---|---|---|---|---|
| `UpperWickNorm_lt_prev` | 1310 | 0.6153 | [0.5886, 0.6412] | +0.0395 | +0.1075 | +0.0703 |
| `BuyShare_ratio1 > mediana` | 1662 | 0.6089 | [0.5852, 0.6321] | +0.0331 | +0.0959 | +0.0587 |
| `SellShare_lt_prev` | 1652 | 0.6065 | [0.5828, 0.6298] | +0.0307 | +0.0924 | +0.0552 |
| `SellShare_ratio1 < mediana` | 1668 | 0.6055 | [0.5818, 0.6287] | +0.0297 | +0.0905 | +0.0533 |
| `AggBuyNorm_chg1 > mediana` | 1744 | 0.6021 | [0.5789, 0.6248] | +0.0263 | +0.0721 | +0.0350 |
| `WickTotalNorm_ratio1 < mediana` | 1336 | 0.6018 | [0.5753, 0.6277] | +0.0260 | +0.0905 | +0.0534 |
| `AggImbalance_gt_prev` | 1685 | 0.6018 | [0.5782, 0.6249] | +0.0260 | +0.0840 | +0.0468 |
| `AggBuyNorm_ratio1 > mediana` | 1662 | 0.6011 | [0.5773, 0.6244] | +0.0253 | +0.0702 | +0.0331 |
| `AggBalanceNorm_gt_prev` | 1692 | 0.6011 | [0.5775, 0.6241] | +0.0253 | +0.0833 | +0.0461 |
| `SellShare_chg1 < mediana` | 1744 | 0.6009 | [0.5777, 0.6237] | +0.0251 | +0.0819 | +0.0448 |
| `BuyShare_chg1 > mediana` | 1706 | 0.5991 | [0.5756, 0.6221] | +0.0233 | +0.0788 | +0.0416 |
| `BuyShare_gt_prev` | 1706 | 0.5991 | [0.5756, 0.6221] | +0.0233 | +0.0788 | +0.0416 |
| `AggImbalance_chg1 > mediana` | 1744 | 0.5986 | [0.5754, 0.6214] | +0.0228 | +0.0781 | +0.0409 |
| `QuantityNorm_chg1 > mediana` | 1744 | 0.5975 | [0.5743, 0.6203] | +0.0217 | +0.0610 | +0.0238 |
| `LowerWickNorm_gt_prev` | 1710 | 0.5947 | [0.5713, 0.6178] | +0.0189 | +0.0714 | +0.0343 |