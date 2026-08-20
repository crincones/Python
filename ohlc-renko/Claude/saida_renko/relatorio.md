# Estudo de pontos de virada em Renko

Gerado em 14/08/2026 14:37 | rotulo `rev_next` | formulacao B (antecipar a virada)

## 1. Base

- bricks validos: **20000**
- pregoes: **33** (01/07/2026 a 14/08/2026)
- box detectado: **140 pontos** (corpo constante em 100.0% dos bricks)
- reversao no Renko custa **280 pontos** de deslocamento real
- eventos com run >= 2: **9571** (47.9% dos bricks)
- taxa base de `rev_next` nesses eventos: **0.327**
- probabilidade de breakeven (alvo 2 box / stop 1 box, custo 0 pts): **0.333**

## 2. Taxa base por comprimento da sequencia

| run_len | n | P(reversao) | IC95% |
|---|---|---|---|
| 1 | 6794 | 0.369 | 0.358 – 0.381 |
| 2 | 4285 | 0.338 | 0.324 – 0.352 |
| 3 | 2837 | 0.346 | 0.329 – 0.364 |
| 4 | 1855 | 0.337 | 0.316 – 0.359 |
| 5 | 1229 | 0.329 | 0.303 – 0.355 |
| 6 | 825 | 0.302 | 0.271 – 0.334 |
| 7 | 576 | 0.307 | 0.271 – 0.346 |
| 8 | 399 | 0.316 | 0.272 – 0.363 |
| 9 | 273 | 0.319 | 0.266 – 0.376 |
| 10 | 186 | 0.317 | 0.254 – 0.387 |
| 11 | 127 | 0.228 | 0.162 – 0.307 |
| 12 | 98 | 0.255 | 0.177 – 0.348 |
| 13 | 73 | 0.178 | 0.104 – 0.277 |
| 14 | 60 | 0.267 | 0.168 – 0.388 |
| 15 | 44 | 0.159 | 0.074 – 0.287 |
| 16 | 37 | 0.054 | 0.011 – 0.162 |
| 17 | 35 | 0.086 | 0.025 – 0.211 |
| 18 | 32 | 0.125 | 0.044 – 0.270 |

## 3. Poder discriminante de cada feature (amostra completa)

Mann-Whitney entre os grupos reverte / continua. p pequeno = separa.

| feature | media (continua) | media (reverte) | p |
|---|---|---|---|
| `hora_dec` | 12.9687 | 13.2458 | 1.65e-04 |
| `absorcao` | 1.9710 | 1.8803 | 2.66e-04 |
| `dur_rel` | 1.0657 | 1.0080 | 5.76e-04 |
| `vol_rel` | 1.0811 | 1.0254 | 1.26e-03 |
| `trades_rel` | 1.0956 | 1.0480 | 8.38e-03 |
| `delta_sig_p1` | 0.3118 | 0.3286 | 1.07e-02 |
| `delta_sig` | 0.4608 | 0.4715 | 1.67e-02 |
| `wick_cnt_run` | 0.8838 | 0.8719 | 6.48e-02 |
| `avgtrade_rel` | 0.9681 | 0.9538 | 8.33e-02 |
| `run_delta_sum` | 1.3877 | 1.4047 | 1.30e-01 |
| `speed_rel` | 1.0139 | 1.0273 | 1.34e-01 |
| `rng_p1` | 1.8927 | 1.8733 | 1.99e-01 |
| `wick_cnt` | 0.6132 | 0.6019 | 3.09e-01 |
| `rng` | 1.6132 | 1.6019 | 3.09e-01 |
| `delta_vs_run` | 0.2442 | 0.2502 | 3.27e-01 |
| `run_len` | 3.9098 | 3.9399 | 5.51e-01 |
| `dur_vs_run` | -0.3469 | -0.3883 | 5.59e-01 |
| `extremo_run` | 0.5684 | 0.5653 | 6.44e-01 |
| `vol_vs_run` | -0.1115 | -0.1491 | 9.75e-01 |
| `wick_adv` | 0.0000 | 0.0000 | 1.00e+00 |

## 4. Modelos (out-of-sample)

Treino: 23 pregoes / 7131 eventos. Teste: 10 pregoes / 2440 eventos.

| modelo | AUC | Brier | exportavel p/ NTSL |
|---|---|---|---|
| logistica | 0.5369 | 0.2479 | sim (soma linear) |
| arvore | 0.5281 | 0.2502 | sim (if/else) |
| gbm | 0.5139 | 0.2210 | nao |

O GBM serve so de teto de referencia: se ele nao supera a logistica com folga, nao ha nao-linearidade relevante a capturar e a logistica e a escolha certa.

## 5. Coeficientes da logistica (features padronizadas)

intercepto = -0.003981

| feature | coef | importancia (perm.) |
|---|---|---|
| `absorcao` | +0.1701 | +0.0065 |
| `vol_rel` | -0.1114 | +0.0127 |
| `hora_dec` | +0.0992 | +0.0140 |
| `delta_sig_p1` | +0.0988 | +0.0129 |
| `dur_rel` | -0.0963 | +0.0138 |
| `run_delta_sum` | -0.0939 | +0.0049 |
| `wick_cnt_run` | -0.0875 | +0.0156 |
| `run_len` | +0.0754 | +0.0082 |
| `rng_p1` | +0.0520 | -0.0007 |
| `wick_cnt` | +0.0465 | +0.0021 |
| `rng` | +0.0465 | +0.0021 |
| `vol_vs_run` | -0.0272 | +0.0003 |
| `delta_vs_run` | +0.0271 | +0.0007 |
| `delta_sig` | +0.0233 | +0.0011 |
| `dur_vs_run` | -0.0220 | -0.0001 |
| `trades_rel` | -0.0090 | +0.0003 |
| `avgtrade_rel` | -0.0060 | +0.0003 |
| `speed_rel` | +0.0043 | +0.0003 |
| `extremo_run` | -0.0031 | +0.0003 |
| `wick_adv` | +0.0000 | +0.0000 |

Coeficiente positivo = valor alto da feature **aumenta** a chance de reversao.

## 6. Arvore de decisao (profundidade 3)

```
|--- hora_dec <= 18.408
|   |--- delta_sig <= 0.725
|   |   |--- delta_sig_p1 <= 0.329
|   |   |   |--- class: 0.0
|   |   |--- delta_sig_p1 >  0.329
|   |   |   |--- class: 0.0
|   |--- delta_sig >  0.725
|   |   |--- delta_sig <= 0.774
|   |   |   |--- class: 1.0
|   |   |--- delta_sig >  0.774
|   |   |   |--- class: 1.0
|--- hora_dec >  18.408
|   |--- absorcao <= 0.162
|   |   |--- class: 1.0
|   |--- absorcao >  0.162
|   |   |--- class: 1.0

```

## 7. Desempenho por decil do score

| decil | n | p media | acerto real | lift | expectativa (pts) | bricks pos-virada (mediana) |
|---|---|---|---|---|---|---|
| 1 | 244 | 0.432 | 0.320 | 0.98x | -5.7 | 0.0 |
| 2 | 244 | 0.461 | 0.295 | 0.90x | -16.1 | 0.0 |
| 3 | 244 | 0.474 | 0.262 | 0.80x | -29.8 | 0.0 |
| 4 | 244 | 0.484 | 0.307 | 0.94x | -10.9 | 0.0 |
| 5 | 244 | 0.492 | 0.357 | 1.09x | +9.8 | 0.0 |
| 6 | 244 | 0.500 | 0.303 | 0.93x | -12.6 | 0.0 |
| 7 | 244 | 0.508 | 0.324 | 0.99x | -4.0 | 0.0 |
| 8 | 244 | 0.518 | 0.361 | 1.10x | +11.5 | 0.0 |
| 9 | 244 | 0.532 | 0.348 | 1.06x | +6.3 | 0.0 |
| 10 | 244 | 0.568 | 0.398 | 1.21x | +27.0 | 0.0 |

## 8. Escolha do threshold

| threshold | sinais | cobertura | acerto | pts/trade | pts totais |
|---|---|---|---|---|---|
| 0.050 | 2440 | 100.0% | 0.327 | -2.5 | -6020 |
| 0.075 | 2440 | 100.0% | 0.327 | -2.5 | -6020 |
| 0.100 | 2440 | 100.0% | 0.327 | -2.5 | -6020 |
| 0.125 | 2440 | 100.0% | 0.327 | -2.5 | -6020 |
| 0.150 | 2440 | 100.0% | 0.327 | -2.5 | -6020 |
| 0.175 | 2440 | 100.0% | 0.327 | -2.5 | -6020 |
| 0.200 | 2440 | 100.0% | 0.327 | -2.5 | -6020 |
| 0.225 | 2440 | 100.0% | 0.327 | -2.5 | -6020 |
| 0.250 | 2440 | 100.0% | 0.327 | -2.5 | -6020 |
| 0.275 | 2440 | 100.0% | 0.327 | -2.5 | -6020 |
| 0.300 | 2440 | 100.0% | 0.327 | -2.5 | -6020 |
| 0.325 | 2440 | 100.0% | 0.327 | -2.5 | -6020 |
| 0.350 | 2438 | 99.9% | 0.328 | -2.4 | -5740 |
| 0.375 | 2431 | 99.6% | 0.328 | -2.1 | -5180 |
| 0.400 | 2419 | 99.1% | 0.328 | -2.1 | -5180 |
| 0.425 | 2383 | 97.7% | 0.329 | -2.0 | -4760 |
| 0.450 | 2220 | 91.0% | 0.328 | -2.1 | -4620 |
| 0.475 | 1825 | 74.8% | 0.338 | +2.0 | +3640 |
| 0.500 | 1082 | 44.3% | 0.351 | +7.5 | +8120 |
| 0.525 | 470 | 19.3% | 0.379 | +19.1 | +8960 |
| 0.550 | 191 | 7.8% | 0.398 | +27.1 | +5180 |
| 0.575 | 84 | 3.4% | 0.488 | +65.0 | +5460 |

Threshold que maximiza pontos totais no out-of-sample: **0.525**

## 9. Leitura critica

- Se a AUC out-of-sample estiver abaixo de ~0.55, o sinal nao existe nas features agregadas por brick e nao adianta insistir no modelo.
- O que decide nao e a AUC e sim se algum decil superior fica acima de 33.3% de acerto com cobertura utilizavel.
- Todas as estatisticas moveis usam janela de 50 bricks com `shift(1)`: nenhuma feature enxerga o proprio brick nem o futuro.
- A padronizacao usa media/desvio do **treino** e esta exportada em `modelo_ntsl.txt`; o NTSL precisa usar exatamente esses numeros.
- Limite conhecido: o CSV agregado nao guarda a ORDEM da agressao dentro do brick. Exaustao (compra no inicio, venda no fim) e continuacao tem o mesmo `AgressionVolBuy`.
