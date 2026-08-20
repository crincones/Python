# 05 — Baselines e grupos de informacao (target `p2c3`)

Walk-forward expansivo no conjunto de desenvolvimento (holdout final excluido).

| experimento | modelo | features | n | AUC | IC95 | PR-AUC | prec@0.5 | base | edge | folds AUC>0.5 |
|---|---|---|---|---|---|---|---|---|---|---|
| `EXP010_STRUCT+AGG_CATBOOST` | catboost | STRUCT+AGG (41) | 2248 | 0.5368 | [0.512, 0.562] | 0.3315 | 0.3455 | 0.3172 | +0.0283 | 4/6 |
| `EXP015_EXTENDED_CATBOOST` | catboost | EXTENDED (97) | 2248 | 0.5312 | [0.504, 0.558] | 0.3468 | 0.5000 | 0.3172 | +0.1828 | 5/6 |
| `EXP101_EXTENDED_RF` | random_forest | EXTENDED (97) | 2248 | 0.5295 | [0.506, 0.554] | 0.3269 | nan | 0.3172 | +nan | 3/6 |
| `EXP100_EXTENDED_TREE` | tree | EXTENDED (97) | 2248 | 0.5262 | [0.499, 0.550] | 0.3258 | 0.3121 | 0.3172 | -0.0051 | 4/6 |
| `EXP007_BASE_LOGISTIC` | logistic | BASE (42) | 2248 | 0.5254 | [0.499, 0.551] | 0.3416 | 0.6667 | 0.3172 | +0.3495 | 4/6 |
| `EXP014_BASE_CATBOOST` | catboost | BASE (42) | 2248 | 0.5249 | [0.501, 0.550] | 0.3443 | 0.5556 | 0.3172 | +0.2384 | 3/6 |
| `EXP004_STRUCT+VOL_LOGISTIC` | logistic | STRUCT+VOL (28) | 2248 | 0.5127 | [0.488, 0.537] | 0.3182 | 0.5000 | 0.3172 | +0.1828 | 2/6 |
| `EXP008_EXTENDED_LOGISTIC` | logistic | EXTENDED (97) | 2248 | 0.5105 | [0.485, 0.536] | 0.3259 | 0.4348 | 0.3172 | +0.1176 | 3/6 |
| `EXP011_STRUCT+VOL_CATBOOST` | catboost | STRUCT+VOL (28) | 2248 | 0.5090 | [0.483, 0.535] | 0.3301 | 0.5000 | 0.3172 | +0.1828 | 3/6 |
| `EXP005_STRUCT+TIME_LOGISTIC` | logistic | STRUCT+TIME (18) | 2248 | 0.5040 | [0.478, 0.530] | 0.3204 | 0.7143 | 0.3172 | +0.3971 | 2/6 |
| `EXP012_STRUCT+TIME_CATBOOST` | catboost | STRUCT+TIME (18) | 2248 | 0.5037 | [0.479, 0.530] | 0.3338 | 0.5000 | 0.3172 | +0.1828 | 5/6 |
| `EXP000_ALWAYS_SIGNAL` | always_signal | STRUCT (5) | 2248 | 0.5000 | [0.500, 0.500] | 0.3172 | 0.3172 | 0.3172 | +0.0000 | 0/6 |
| `EXP003_STRUCT+AGG_LOGISTIC` | logistic | STRUCT+AGG (41) | 2248 | 0.4969 | [0.470, 0.523] | 0.3208 | 0.3913 | 0.3172 | +0.0741 | 4/6 |
| `EXP006_STRUCT+CANDLE_LOGISTIC` | logistic | STRUCT+CANDLE (18) | 2248 | 0.4957 | [0.471, 0.522] | 0.3241 | 1.0000 | 0.3172 | +0.6828 | 2/6 |
| `EXP001_STRUCT_LOGISTIC` | logistic | STRUCT (5) | 2248 | 0.4916 | [0.467, 0.518] | 0.3136 | nan | 0.3172 | +nan | 4/6 |
| `EXP002_STRUCT_LOGISTIC` | logistic | STRUCT (5) | 2248 | 0.4916 | [0.467, 0.518] | 0.3136 | nan | 0.3172 | +nan | 4/6 |
| `EXP009_STRUCT_CATBOOST` | catboost | STRUCT (5) | 2248 | 0.4900 | [0.465, 0.517] | 0.3132 | nan | 0.3172 | +nan | 4/6 |
| `EXP013_STRUCT+CANDLE_CATBOOST` | catboost | STRUCT+CANDLE (18) | 2248 | 0.4895 | [0.464, 0.513] | 0.3125 | nan | 0.3172 | +nan | 2/6 |

## p-valor bootstrap vs baseline estrutural (AUC pareado)

- `EXP010_STRUCT+AGG_CATBOOST`: p = 0.0050
- `EXP015_EXTENDED_CATBOOST`: p = 0.0190
- `EXP101_EXTENDED_RF`: p = 0.0190
- `EXP100_EXTENDED_TREE`: p = 0.0380
- `EXP007_BASE_LOGISTIC`: p = 0.0400
- `EXP014_BASE_CATBOOST`: p = 0.0510
- `EXP004_STRUCT+VOL_LOGISTIC`: p = 0.1730
- `EXP008_EXTENDED_LOGISTIC`: p = 0.2590
- `EXP011_STRUCT+VOL_CATBOOST`: p = 0.3080
- `EXP005_STRUCT+TIME_LOGISTIC`: p = 0.3930
- `EXP012_STRUCT+TIME_CATBOOST`: p = 0.4920
- `EXP000_ALWAYS_SIGNAL`: p = 0.5120
- `EXP009_STRUCT_CATBOOST`: p = 0.7410
- `EXP003_STRUCT+AGG_LOGISTIC`: p = 0.7520
- `EXP006_STRUCT+CANDLE_LOGISTIC`: p = 0.7790
- `EXP013_STRUCT+CANDLE_CATBOOST`: p = 0.8680
- `EXP002_STRUCT_LOGISTIC`: p = 1.0000