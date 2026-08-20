# 13 — Teste de regras isoladas (`pts100p3`)

Universo: 2320 candidatos em 29 pregoes (apenas DESENVOLVIMENTO).  
Taxa-base: **0.6026** · expectativa base: **+0.0864 R**

## Hipotese do usuario, isolada

| regra | n | /dia | precision | IC95 Wilson | taxa-base | edge | expectativa R | Δ vs base | bate a base? |
|---|---|---|---|---|---|---|---|---|---|
| HIPOTESE: AggTotalNorm[t] > [t-1] | 1284 | 44.28 | 0.5888 | [0.5616, 0.6154] | 0.6026 | -0.0138 | +0.0472 | -0.0392 | nao |
| controle: AggTotalNorm[t] < [t-1] | 1035 | 35.69 | 0.6193 | [0.5894, 0.6484] | 0.6026 | +0.0167 | +0.1343 | +0.0479 | nao |
| AggTotalNorm_ratio1 > q50 (1.11) | 1151 | 39.69 | 0.5882 | [0.5595, 0.6163] | 0.6026 | -0.0144 | +0.0460 | -0.0404 | nao |
| AggTotalNorm_ratio1 > q70 (1.59) | 691 | 23.83 | 0.5890 | [0.5519, 0.6251] | 0.6026 | -0.0136 | +0.0401 | -0.0463 | nao |
| AggTotalNorm_ratio1 > q90 (2.58) | 231 | 7.97 | 0.5801 | [0.5156, 0.6419] | 0.6026 | -0.0225 | +0.0223 | -0.0641 | nao |

## Varredura de todas as comparacoes t vs t-1

- regras testadas (n >= 100): **138**
- regras cujo IC95 fica acima da taxa-base: **16**
- falsos positivos esperados por acaso a 95%: **6.9**

| regra | n | precision | IC95 | edge | expectativa R | Δ vs base |
|---|---|---|---|---|---|---|
| `LogDurationResidual20_lt_prev` | 525 | 0.6400 | [0.5981, 0.6799] | +0.0374 | +0.1730 | +0.0866 |
| `BuyShare_chg1 > mediana` | 1160 | 0.6397 | [0.6116, 0.6668] | +0.0371 | +0.1522 | +0.0658 |
| `UpperWickNorm_lt_prev` | 874 | 0.6373 | [0.6049, 0.6685] | +0.0347 | +0.1476 | +0.0612 |
| `BuyShare_ratio1 > mediana` | 1127 | 0.6371 | [0.6086, 0.6647] | +0.0345 | +0.1474 | +0.0610 |
| `AggBalanceNorm_chg1 > mediana` | 1160 | 0.6371 | [0.6090, 0.6642] | +0.0345 | +0.1488 | +0.0624 |
| `AggImbalance_chg1 > mediana` | 1160 | 0.6371 | [0.6090, 0.6642] | +0.0345 | +0.1477 | +0.0613 |
| `AggTotalRatio20_lt_prev` | 625 | 0.6368 | [0.5984, 0.6736] | +0.0342 | +0.1746 | +0.0882 |
| `UpperWickNorm_chg1 < mediana` | 1125 | 0.6364 | [0.6079, 0.6640] | +0.0339 | +0.1472 | +0.0608 |
| `LowerWickNorm_chg1 > mediana` | 1125 | 0.6364 | [0.6079, 0.6640] | +0.0339 | +0.1472 | +0.0608 |
| `WickAsym_lt_prev` | 1125 | 0.6364 | [0.6079, 0.6640] | +0.0339 | +0.1472 | +0.0608 |
| `LowerWickNorm_gt_prev` | 1125 | 0.6364 | [0.6079, 0.6640] | +0.0339 | +0.1472 | +0.0608 |
| `AggBalanceNorm_gt_prev` | 1119 | 0.6363 | [0.6077, 0.6640] | +0.0337 | +0.1474 | +0.0610 |
| `WickAsym_chg1 < mediana` | 1157 | 0.6361 | [0.6080, 0.6634] | +0.0335 | +0.1492 | +0.0628 |
| `BuyShare_gt_prev` | 1129 | 0.6360 | [0.6075, 0.6635] | +0.0334 | +0.1457 | +0.0593 |
| `SellShare_chg1 < mediana` | 1160 | 0.6353 | [0.6072, 0.6626] | +0.0328 | +0.1444 | +0.0580 |