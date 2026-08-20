# 05 — Baselines e grupos de informacao (target `p3c3`)

Walk-forward expansivo no conjunto de desenvolvimento (holdout final excluido).

| experimento | modelo | features | n | AUC | IC95 | PR-AUC | prec@0.5 | base | edge | folds AUC>0.5 |
|---|---|---|---|---|---|---|---|---|---|---|
| `EXP011_STRUCT+VOL_CATBOOST` | catboost | STRUCT+VOL (28) | 1485 | 0.5246 | [0.495, 0.554] | 0.3438 | 0.5000 | 0.3253 | +0.1747 | 5/6 |
| `EXP100_EXTENDED_TREE` | tree | EXTENDED (97) | 1485 | 0.5242 | [0.495, 0.558] | 0.3425 | 0.3547 | 0.3253 | +0.0294 | 4/6 |
| `EXP015_EXTENDED_CATBOOST` | catboost | EXTENDED (97) | 1485 | 0.5232 | [0.490, 0.554] | 0.3659 | 0.4302 | 0.3253 | +0.1050 | 5/6 |
| `EXP012_STRUCT+TIME_CATBOOST` | catboost | STRUCT+TIME (18) | 1485 | 0.5126 | [0.483, 0.545] | 0.3446 | nan | 0.3253 | +nan | 3/6 |
| `EXP101_EXTENDED_RF` | random_forest | EXTENDED (97) | 1485 | 0.5101 | [0.481, 0.542] | 0.3351 | nan | 0.3253 | +nan | 5/6 |
| `EXP014_BASE_CATBOOST` | catboost | BASE (42) | 1485 | 0.5085 | [0.477, 0.539] | 0.3327 | 0.5000 | 0.3253 | +0.1747 | 4/6 |
| `EXP010_STRUCT+AGG_CATBOOST` | catboost | STRUCT+AGG (41) | 1485 | 0.5048 | [0.474, 0.539] | 0.3265 | 0.1724 | 0.3253 | -0.1528 | 4/6 |
| `EXP013_STRUCT+CANDLE_CATBOOST` | catboost | STRUCT+CANDLE (18) | 1485 | 0.5025 | [0.470, 0.534] | 0.3272 | 0.4286 | 0.3253 | +0.1033 | 3/6 |
| `EXP003_STRUCT+AGG_LOGISTIC` | logistic | STRUCT+AGG (41) | 1485 | 0.5012 | [0.471, 0.533] | 0.3393 | 0.4286 | 0.3253 | +0.1033 | 2/6 |
| `EXP004_STRUCT+VOL_LOGISTIC` | logistic | STRUCT+VOL (28) | 1485 | 0.5010 | [0.471, 0.534] | 0.3301 | 0.5000 | 0.3253 | +0.1747 | 2/6 |
| `EXP002_STRUCT_LOGISTIC` | logistic | STRUCT (5) | 1485 | 0.5007 | [0.470, 0.533] | 0.3219 | nan | 0.3253 | +nan | 3/6 |
| `EXP001_STRUCT_LOGISTIC` | logistic | STRUCT (5) | 1485 | 0.5007 | [0.470, 0.533] | 0.3219 | nan | 0.3253 | +nan | 3/6 |
| `EXP000_ALWAYS_SIGNAL` | always_signal | STRUCT (5) | 1485 | 0.5000 | [0.500, 0.500] | 0.3253 | 0.3253 | 0.3253 | +0.0000 | 0/6 |
| `EXP007_BASE_LOGISTIC` | logistic | BASE (42) | 1485 | 0.4965 | [0.465, 0.529] | 0.3373 | 0.4444 | 0.3253 | +0.1192 | 3/6 |
| `EXP006_STRUCT+CANDLE_LOGISTIC` | logistic | STRUCT+CANDLE (18) | 1485 | 0.4965 | [0.465, 0.528] | 0.3371 | 1.0000 | 0.3253 | +0.6747 | 4/6 |
| `EXP009_STRUCT_CATBOOST` | catboost | STRUCT (5) | 1485 | 0.4948 | [0.464, 0.527] | 0.3196 | nan | 0.3253 | +nan | 3/6 |
| `EXP008_EXTENDED_LOGISTIC` | logistic | EXTENDED (97) | 1485 | 0.4877 | [0.458, 0.518] | 0.3296 | 0.3469 | 0.3253 | +0.0217 | 2/6 |
| `EXP005_STRUCT+TIME_LOGISTIC` | logistic | STRUCT+TIME (18) | 1485 | 0.4721 | [0.440, 0.506] | 0.3135 | 0.5000 | 0.3253 | +0.1747 | 2/6 |

## p-valor bootstrap vs baseline estrutural (AUC pareado)

- `EXP005_STRUCT+TIME_LOGISTIC`: p = 0.0060
- `EXP100_EXTENDED_TREE`: p = 0.2260
- `EXP009_STRUCT_CATBOOST`: p = 0.2960
- `EXP011_STRUCT+VOL_CATBOOST`: p = 0.2960
- `EXP015_EXTENDED_CATBOOST`: p = 0.3030
- `EXP008_EXTENDED_LOGISTIC`: p = 0.4910
- `EXP012_STRUCT+TIME_CATBOOST`: p = 0.5840
- `EXP101_EXTENDED_RF`: p = 0.5900
- `EXP006_STRUCT+CANDLE_LOGISTIC`: p = 0.6990
- `EXP014_BASE_CATBOOST`: p = 0.7460
- `EXP007_BASE_LOGISTIC`: p = 0.8310
- `EXP010_STRUCT+AGG_CATBOOST`: p = 0.8470
- `EXP000_ALWAYS_SIGNAL`: p = 0.9360
- `EXP003_STRUCT+AGG_LOGISTIC`: p = 0.9620
- `EXP013_STRUCT+CANDLE_CATBOOST`: p = 0.9640
- `EXP004_STRUCT+VOL_LOGISTIC`: p = 0.9900
- `EXP002_STRUCT_LOGISTIC`: p = 1.0000