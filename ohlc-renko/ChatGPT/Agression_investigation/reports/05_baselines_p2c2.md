# 05 — Baselines e grupos de informacao (target `p2c2`)

Walk-forward expansivo no conjunto de desenvolvimento (holdout final excluido).

| experimento | modelo | features | n | AUC | IC95 | PR-AUC | prec@0.5 | base | edge | folds AUC>0.5 |
|---|---|---|---|---|---|---|---|---|---|---|
| `EXP011_STRUCT+VOL_CATBOOST` | catboost | STRUCT+VOL (28) | 2248 | 0.5347 | [0.510, 0.559] | 0.4819 | 0.5061 | 0.4537 | +0.0524 | 5/6 |
| `EXP010_STRUCT+AGG_CATBOOST` | catboost | STRUCT+AGG (41) | 2248 | 0.5330 | [0.509, 0.555] | 0.4658 | 0.4678 | 0.4537 | +0.0141 | 5/6 |
| `EXP101_EXTENDED_RF` | random_forest | EXTENDED (97) | 2248 | 0.5295 | [0.506, 0.554] | 0.4799 | 0.4658 | 0.4537 | +0.0120 | 4/6 |
| `EXP014_BASE_CATBOOST` | catboost | BASE (42) | 2248 | 0.5286 | [0.505, 0.552] | 0.4744 | 0.4806 | 0.4537 | +0.0268 | 4/6 |
| `EXP100_EXTENDED_TREE` | tree | EXTENDED (97) | 2248 | 0.5277 | [0.503, 0.551] | 0.4691 | 0.4825 | 0.4537 | +0.0288 | 5/6 |
| `EXP004_STRUCT+VOL_LOGISTIC` | logistic | STRUCT+VOL (28) | 2248 | 0.5215 | [0.497, 0.546] | 0.4672 | 0.4837 | 0.4537 | +0.0299 | 5/6 |
| `EXP006_STRUCT+CANDLE_LOGISTIC` | logistic | STRUCT+CANDLE (18) | 2248 | 0.5177 | [0.495, 0.540] | 0.4677 | 0.4741 | 0.4537 | +0.0204 | 4/6 |
| `EXP009_STRUCT_CATBOOST` | catboost | STRUCT (5) | 2248 | 0.5155 | [0.491, 0.539] | 0.4677 | 0.5114 | 0.4537 | +0.0576 | 3/6 |
| `EXP008_EXTENDED_LOGISTIC` | logistic | EXTENDED (97) | 2248 | 0.5127 | [0.489, 0.535] | 0.4641 | 0.4459 | 0.4537 | -0.0078 | 3/6 |
| `EXP015_EXTENDED_CATBOOST` | catboost | EXTENDED (97) | 2248 | 0.5109 | [0.488, 0.536] | 0.4649 | 0.4686 | 0.4537 | +0.0149 | 5/6 |
| `EXP013_STRUCT+CANDLE_CATBOOST` | catboost | STRUCT+CANDLE (18) | 2248 | 0.5090 | [0.485, 0.532] | 0.4633 | 0.4692 | 0.4537 | +0.0154 | 3/6 |
| `EXP007_BASE_LOGISTIC` | logistic | BASE (42) | 2248 | 0.5079 | [0.483, 0.533] | 0.4702 | 0.4600 | 0.4537 | +0.0063 | 4/6 |
| `EXP002_STRUCT_LOGISTIC` | logistic | STRUCT (5) | 2248 | 0.5076 | [0.482, 0.532] | 0.4595 | nan | 0.4537 | +nan | 3/6 |
| `EXP001_STRUCT_LOGISTIC` | logistic | STRUCT (5) | 2248 | 0.5076 | [0.482, 0.532] | 0.4595 | nan | 0.4537 | +nan | 3/6 |
| `EXP000_ALWAYS_SIGNAL` | always_signal | STRUCT (5) | 2248 | 0.5000 | [0.500, 0.500] | 0.4537 | 0.4537 | 0.4537 | +0.0000 | 0/6 |
| `EXP003_STRUCT+AGG_LOGISTIC` | logistic | STRUCT+AGG (41) | 2248 | 0.4988 | [0.474, 0.525] | 0.4541 | 0.4470 | 0.4537 | -0.0067 | 3/6 |
| `EXP005_STRUCT+TIME_LOGISTIC` | logistic | STRUCT+TIME (18) | 2248 | 0.4964 | [0.471, 0.520] | 0.4592 | 0.4741 | 0.4537 | +0.0203 | 3/6 |
| `EXP012_STRUCT+TIME_CATBOOST` | catboost | STRUCT+TIME (18) | 2248 | 0.4918 | [0.466, 0.514] | 0.4511 | 0.4475 | 0.4537 | -0.0063 | 2/6 |

## p-valor bootstrap vs baseline estrutural (AUC pareado)

- `EXP011_STRUCT+VOL_CATBOOST`: p = 0.0810
- `EXP010_STRUCT+AGG_CATBOOST`: p = 0.0840
- `EXP101_EXTENDED_RF`: p = 0.1410
- `EXP014_BASE_CATBOOST`: p = 0.1690
- `EXP100_EXTENDED_TREE`: p = 0.1810
- `EXP009_STRUCT_CATBOOST`: p = 0.2060
- `EXP004_STRUCT+VOL_LOGISTIC`: p = 0.3070
- `EXP005_STRUCT+TIME_LOGISTIC`: p = 0.3400
- `EXP012_STRUCT+TIME_CATBOOST`: p = 0.3460
- `EXP006_STRUCT+CANDLE_LOGISTIC`: p = 0.4290
- `EXP003_STRUCT+AGG_LOGISTIC`: p = 0.5580
- `EXP000_ALWAYS_SIGNAL`: p = 0.5610
- `EXP008_EXTENDED_LOGISTIC`: p = 0.6910
- `EXP015_EXTENDED_CATBOOST`: p = 0.7910
- `EXP013_STRUCT+CANDLE_CATBOOST`: p = 0.9220
- `EXP007_BASE_LOGISTIC`: p = 0.9460
- `EXP002_STRUCT_LOGISTIC`: p = 1.0000