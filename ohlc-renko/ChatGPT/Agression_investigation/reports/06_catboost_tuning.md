# 06 — CatBoost: busca de hiperparametros e estabilidade

Selecao feita **apenas** no conjunto de desenvolvimento, via walk-forward expansivo com embargo. O holdout final nao foi usado.

## Melhor configuracao por target (criterio de estabilidade)

| target | feature set | depth | lr | l2 | AUC OOF | AUC medio/fold | desvio | folds>0.5 | score |
|---|---|---|---|---|---|---|---|---|---|
| `p2c2` | STRUCT+AGG | 4 | 0.02 | 10.0 | 0.5357 | 0.5391 | 0.0351 | 6/6 | 0.5215 |
| `p3c2` | STRUCT+AGG | 5 | 0.1 | 10.0 | 0.5268 | 0.5320 | 0.0243 | 5/6 | 0.5199 |

### Top 10 configuracoes — `p2c2`

| feature set | depth | lr | l2 | AUC OOF | AUC/fold | desvio | folds>0.5 |
|---|---|---|---|---|---|---|---|
| STRUCT+AGG | 4 | 0.02 | 10.0 | 0.5357 | 0.5391 | 0.0351 | 6/6 |
| STRUCT+VOL | 3 | 0.1 | 3.0 | 0.5434 | 0.5441 | 0.0456 | 4/6 |
| BASE | 5 | 0.02 | 10.0 | 0.5265 | 0.5365 | 0.0306 | 6/6 |
| BASE | 4 | 0.02 | 10.0 | 0.5519 | 0.5480 | 0.0544 | 5/6 |
| STRUCT+VOL | 3 | 0.05 | 10.0 | 0.5286 | 0.5319 | 0.0289 | 5/6 |
| BASE | 4 | 0.1 | 10.0 | 0.5396 | 0.5406 | 0.0465 | 5/6 |
| BASE | 5 | 0.05 | 3.0 | 0.5394 | 0.5301 | 0.0258 | 5/6 |
| STRUCT+AGG | 6 | 0.05 | 3.0 | 0.5306 | 0.5424 | 0.0507 | 5/6 |
| STRUCT+AGG | 5 | 0.02 | 3.0 | 0.5392 | 0.5379 | 0.0460 | 5/6 |
| STRUCT+AGG | 6 | 0.02 | 10.0 | 0.5351 | 0.5367 | 0.0454 | 5/6 |

Dispersao do AUC OOF em `p2c2`: min=0.4864, max=0.5519, desvio=0.0134 sobre 96 configuracoes.

### Top 10 configuracoes — `p3c2`

| feature set | depth | lr | l2 | AUC OOF | AUC/fold | desvio | folds>0.5 |
|---|---|---|---|---|---|---|---|
| STRUCT+AGG | 5 | 0.1 | 10.0 | 0.5268 | 0.5320 | 0.0243 | 5/6 |
| STRUCT+AGG | 5 | 0.02 | 10.0 | 0.5252 | 0.5336 | 0.0320 | 5/6 |
| STRUCT+AGG | 5 | 0.05 | 10.0 | 0.5199 | 0.5223 | 0.0133 | 6/6 |
| STRUCT+AGG | 5 | 0.1 | 3.0 | 0.5316 | 0.5366 | 0.0431 | 5/6 |
| STRUCT+AGG | 5 | 0.02 | 3.0 | 0.5178 | 0.5260 | 0.0241 | 5/6 |
| STRUCT+AGG | 5 | 0.05 | 3.0 | 0.5143 | 0.5203 | 0.0258 | 4/6 |
| STRUCT+AGG | 4 | 0.02 | 10.0 | 0.5157 | 0.5158 | 0.0258 | 4/6 |
| STRUCT+VOL | 6 | 0.1 | 3.0 | 0.5168 | 0.5162 | 0.0308 | 4/6 |
| STRUCT+AGG | 3 | 0.02 | 3.0 | 0.5161 | 0.5185 | 0.0357 | 3/6 |
| EXTENDED | 3 | 0.05 | 3.0 | 0.5074 | 0.5134 | 0.0289 | 4/6 |

Dispersao do AUC OOF em `p3c2`: min=0.4806, max=0.5316, desvio=0.0102 sobre 96 configuracoes.

## Sensibilidade ao numero de lags

| target | feature set | lags | n feat | AUC OOF | AUC/fold | desvio | folds>0.5 |
|---|---|---|---|---|---|---|---|
| `p2c2` | BASE | 3 | 28 | 0.5104 | 0.5322 | 0.0499 | 4/6 |
| `p2c2` | EXTENDED | 3 | 83 | 0.5249 | 0.5071 | 0.0241 | 3/6 |
| `p2c2` | BASE | 5 | 42 | 0.5286 | 0.5332 | 0.0647 | 4/6 |
| `p2c2` | EXTENDED | 5 | 97 | 0.5109 | 0.5134 | 0.0432 | 5/6 |
| `p2c2` | BASE | 8 | 63 | 0.5015 | 0.4900 | 0.0448 | 3/6 |
| `p2c2` | EXTENDED | 8 | 118 | 0.5333 | 0.5435 | 0.0491 | 6/6 |
| `p2c2` | BASE | 10 | 77 | 0.5180 | 0.5109 | 0.0564 | 4/6 |
| `p2c2` | EXTENDED | 10 | 132 | 0.4973 | 0.4927 | 0.0297 | 2/6 |

## Sensibilidade ao periodo da media movel

| periodo | AUC OOF | AUC/fold | desvio | folds>0.5 |
|---|---|---|---|---|
| 10.0 | 0.5437 | 0.5409 | 0.0519 | 5.0/6.0 |
| 20.0 | 0.5286 | 0.5332 | 0.0647 | 4.0/6.0 |
| 40.0 | 0.5143 | 0.5148 | 0.0432 | 5.0/6.0 |