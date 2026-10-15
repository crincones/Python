# Reversões nas VWAP Bands

WINFUT PI 20, 132 pregões (2026-03-12 a 2026-09-18), mesmos candles do Backtest-Momentum2-GraficoPI com volume financeiro e quantidade. VWAP Band do Profit: VWAP com preço "Média financeira" e bandas em envelope de 1/3 %, 2/3 % e 1 % da VWAP, conferidas contra o Profit.
6 contratos, R$ 0,50 por contrato. Treino até 2026-07-07. Stop de 100 em todas as saídas. Gráficos, tabelas completas e trade a trade em `vwap.html`.

## Resposta

- **Reverter toda virada na banda só empata**: −R$ 1,0 por trade (alvo 300). Melhor que entrar ao acaso (−R$ 7,0), mas sem lucro, e rende o mesmo fora das bandas. A banda 1, 2 ou 3 não muda isso.
- **Padrão que funciona: exaustão limpa** — 4+ candles seguidos até a banda e virada no 1º candle contra **sem pavio de rejeição**. 445 sinais, +R$ 15,1 por trade, treino +R$ 13,3, teste +R$ 17,4, positivo nos 3 terços. **Na banda 2 ou além**: 159 sinais, +R$ 30,2 por trade, positiva nas 4 saídas. Na banda 1 ela rende menos que fora das bandas.
- **Pavio de rejeição grande e topo/fundo duplo são piores** que a média, e o falso rompimento também fica abaixo; 2º candle contra e virada da Hull pioram.
- **Primeiros toques, contando todo sinal do toque, ajudam pouco**: 1º toque na banda 1 +R$ 1,3 contra −R$ 3,5, negativo no último terço. Com uma entrada por toque, ver `TOQUE.md`.
- **Ângulo da VWAP não ordena os resultados** em nenhuma medida (pts/candle em 10 e 20 candles, passos de banda).
- **VWAP não é ponto de entrada** (repique na VWAP negativo em quase todas as saídas e recortes) e é **alvo longe demais**: mediana de 870 pts; só 9% chegam antes do stop 100.
- **Alvo 300 > alvo 500**: só 16% andam 500 antes do stop, 25% andam 300.

## Base

| Gatilho | Sinais | Alvo 300 seco | Alvo 500 seco | Alvo na VWAP | Gestão CLAUDE.md |
|:--|--:|--:|--:|--:|--:|
| 1º candle contra | 5.500 | −R$ 1,0 | −R$ 3,3 | −R$ 13,9 | +R$ 1,4 |
| 2º candle contra (confirmação) | 2.874 | −R$ 5,8 | −R$ 8,0 | −R$ 13,9 | −R$ 2,4 |
| Hull 50 vira contra | 809 | −R$ 13,1 | −R$ 8,2 | −R$ 16,6 | −R$ 9,8 |
| Entrada aleatória | | −R$ 7,0 | −R$ 7,9 | - | −R$ 5,3 |

## Padrões (alvo 300, grupo x resto)

| Grupo | Sinais | R$/trade | Resto | Treino | Teste | t | Percentil |
|:--|--:|--:|--:|--:|--:|--:|--:|
| VWAP a favor do trade (ângulo > 0) | 1 | +R$ 357,0 | −R$ 1,0 | +R$ 357,0 | - | - | 74 |
| Exaustão limpa e VWAP plana | 55 | +R$ 45,0 | −R$ 1,4 | +R$ 22,9 | +R$ 90,3 | 1,50 | 95 |
| Exaustão limpa e banda 2+ | 159 | +R$ 30,2 | −R$ 1,9 | +R$ 45,0 | +R$ 13,2 | 1,79 | 97 |
| Exaustão limpa e 1º/2º toque | 390 | +R$ 19,5 | −R$ 2,5 | +R$ 10,4 | +R$ 32,9 | 1,92 | 98 |
| Exaustão limpa (4+ candles, sem pavio de rejeição) | 445 | +R$ 15,1 | −R$ 2,4 | +R$ 13,3 | +R$ 17,4 | 1,63 | 96 |
| Exaustão: empurrão de 4+ candles | 1.145 | +R$ 3,4 | −R$ 2,1 | +R$ 8,9 | −R$ 5,4 | 0,79 | 78 |
| 1º ou 2º toque na banda 1 | 4.689 | −R$ 0,2 | −R$ 5,7 | +R$ 3,1 | −R$ 6,4 | 0,71 | 77 |
| 1º toque na banda 1 do dia | 2.903 | +R$ 1,3 | −R$ 3,5 | +R$ 6,3 | −R$ 9,1 | 0,86 | 80 |
| Banda 3 | 617 | +R$ 3,2 | −R$ 1,5 | +R$ 14,9 | −R$ 14,1 | 0,53 | 71 |
| 1º sinal do dia naquele lado | 220 | +R$ 3,5 | −R$ 1,2 | +R$ 15,2 | −R$ 13,9 | 0,32 | 62 |
| Hull 50 já virou a favor | 1.495 | +R$ 2,2 | −R$ 2,2 | +R$ 3,6 | −R$ 0,4 | 0,69 | 75 |
| Longe da VWAP (> 800 pts) | 3.078 | +R$ 0,3 | −R$ 2,6 | +R$ 0,9 | −R$ 1,0 | 0,50 | 68 |
| Banda 2 ou 3 | 1.916 | −R$ 2,0 | −R$ 0,4 | +R$ 0,3 | −R$ 6,2 | −0,27 | 40 |
| Falso rompimento (fechou fora da banda e voltou) | 1.351 | −R$ 3,2 | −R$ 0,3 | −R$ 0,1 | −R$ 8,7 | −0,45 | 31 |
| VWAP inclinada contra o trade (< -8 pts/candle) | 1.318 | −R$ 5,0 | +R$ 0,3 | +R$ 0,6 | −R$ 11,5 | −0,81 | 21 |
| MACD do lado do trade | 1.153 | −R$ 5,6 | +R$ 0,3 | −R$ 5,6 | −R$ 5,5 | −0,86 | 18 |
| Perto da VWAP (< 700 pts) | 1.854 | −R$ 5,3 | +R$ 1,2 | −R$ 0,3 | −R$ 13,5 | −1,12 | 13 |
| Pavio de rejeição (>= 30 pts, o candle de virada fez o extremo) | 3.406 | −R$ 3,5 | +R$ 3,2 | +R$ 0,4 | −R$ 10,7 | −1,16 | 12 |
| 1º toque na banda do sinal | 3.260 | −R$ 4,4 | +R$ 4,0 | +R$ 1,0 | −R$ 14,4 | −1,46 | 7 |
| VWAP plana (|ângulo| < 2 pts/candle) | 615 | −R$ 8,5 | −R$ 0,0 | −R$ 10,9 | +R$ 2,2 | −0,97 | 17 |
| Topo/fundo duplo na banda | 2.346 | −R$ 6,3 | +R$ 3,0 | −R$ 5,1 | −R$ 8,7 | −1,66 | 5 |

**Pavio do candle de virada**

| Pavio do candle de virada | Sinais | Alvo 300 seco | Alvo 500 seco | Alvo na VWAP | Gestão CLAUDE.md | Treino (300) | Teste (300) |
|:--|--:|--:|--:|--:|--:|--:|--:|
| sem pavio (0) | 125 | −R$ 7,8 | −R$ 2,0 | −R$ 43,1 | −R$ 7,8 | +R$ 24,7 | −R$ 61,7 |
| 1 a 10 | 815 | +R$ 5,1 | −R$ 4,6 | −R$ 19,2 | +R$ 7,7 | +R$ 3,5 | +R$ 8,3 |
| 11 a 20 | 732 | −R$ 0,2 | −R$ 6,4 | −R$ 13,6 | +R$ 5,6 | +R$ 2,2 | −R$ 4,3 |
| 21 a 30 | 684 | +R$ 6,3 | +R$ 10,0 | +R$ 8,9 | +R$ 5,6 | +R$ 6,5 | +R$ 6,0 |
| 31 a 50 | 1.109 | −R$ 0,9 | −R$ 4,4 | −R$ 11,4 | −R$ 1,2 | +R$ 3,7 | −R$ 8,9 |
| mais de 50 | 2.035 | −R$ 5,7 | −R$ 5,5 | −R$ 19,0 | −R$ 2,1 | −R$ 1,0 | −R$ 14,3 |

**Candles do empurrão**

| Candles do empurrão | Sinais | Alvo 300 seco | Alvo 500 seco | Alvo na VWAP | Gestão CLAUDE.md | Treino (300) | Teste (300) |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 1 | 2.186 | +R$ 0,4 | −R$ 1,1 | −R$ 18,0 | +R$ 1,9 | +R$ 1,4 | −R$ 1,4 |
| 2 | 1.361 | −R$ 0,2 | −R$ 1,9 | −R$ 13,6 | −R$ 0,2 | +R$ 4,4 | −R$ 9,4 |
| 3 | 808 | −R$ 12,2 | −R$ 12,2 | −R$ 16,5 | −R$ 7,3 | −R$ 6,6 | −R$ 21,7 |
| 4 | 475 | −R$ 3,0 | −R$ 8,6 | −R$ 22,4 | +R$ 4,2 | +R$ 2,7 | −R$ 12,4 |
| 5 | 287 | +R$ 10,4 | −R$ 0,9 | +R$ 7,4 | +R$ 8,9 | +R$ 7,9 | +R$ 14,3 |
| 6 | 166 | +R$ 15,8 | +R$ 5,7 | +R$ 27,2 | +R$ 23,0 | +R$ 15,9 | +R$ 15,6 |
| 7 ou mais | 217 | −R$ 1,3 | +R$ 2,0 | −R$ 5,2 | +R$ 7,0 | +R$ 19,2 | −R$ 35,2 |

**Banda alcançada**

| Banda alcançada | Sinais | Alvo 300 seco | Alvo 500 seco | Alvo na VWAP | Gestão CLAUDE.md | Treino (300) | Teste (300) |
|:--|--:|--:|--:|--:|--:|--:|--:|
| banda 1 (até a banda 2) | 3.584 | −R$ 0,4 | −R$ 4,1 | −R$ 8,1 | +R$ 2,1 | +R$ 3,8 | −R$ 7,8 |
| banda 2 (até a banda 3) | 1.299 | −R$ 4,5 | −R$ 7,2 | −R$ 28,9 | −R$ 2,0 | −R$ 5,9 | −R$ 1,6 |
| banda 3 ou alem | 617 | +R$ 3,2 | +R$ 10,0 | −R$ 15,6 | +R$ 4,8 | +R$ 14,9 | −R$ 14,1 |

**Toque na banda 1**

| Toque na banda 1 | Sinais | Alvo 300 seco | Alvo 500 seco | Alvo na VWAP | Gestão CLAUDE.md | Treino (300) | Teste (300) |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 1º toque | 2.903 | +R$ 1,3 | −R$ 3,7 | −R$ 16,6 | +R$ 2,4 | +R$ 6,3 | −R$ 9,1 |
| 2º toque | 1.786 | −R$ 2,5 | −R$ 3,1 | −R$ 10,2 | +R$ 0,9 | −R$ 2,5 | −R$ 2,6 |
| 3º toque | 524 | −R$ 2,5 | +R$ 8,0 | +R$ 7,0 | +R$ 0,8 | +R$ 0,2 | −R$ 5,3 |
| 4º toque | 200 | −R$ 10,8 | −R$ 7,2 | −R$ 28,8 | R$ 0,0 | +R$ 4,0 | −R$ 26,5 |
| 5º ou mais | 87 | −R$ 12,7 | −R$ 51,3 | −R$ 90,1 | −R$ 12,7 | −R$ 12,7 | - |

**Exaustão limpa: toque na banda 1**

| Exaustão limpa: toque na banda 1 | Sinais | Alvo 300 seco | Alvo 500 seco | Alvo na VWAP | Gestão CLAUDE.md | Treino (300) | Teste (300) |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 1º toque | 253 | +R$ 14,1 | −R$ 10,1 | −R$ 15,7 | +R$ 18,8 | +R$ 6,4 | +R$ 25,8 |
| 2º toque | 137 | +R$ 29,4 | +R$ 42,5 | +R$ 48,7 | +R$ 28,5 | +R$ 18,0 | +R$ 45,4 |
| 3º toque | 38 | −R$ 21,9 | −R$ 28,3 | +R$ 19,2 | −R$ 15,6 | +R$ 24,7 | −R$ 46,2 |
| 4º ou mais | 17 | −R$ 3,0 | −R$ 31,2 | −R$ 25,8 | +R$ 7,6 | +R$ 62,5 | −R$ 123,0 |

**Ângulo VWAP (pts/candle, 10)**

| Ângulo VWAP (pts/candle, 10) | Sinais | Alvo 300 seco | Alvo 500 seco | Alvo na VWAP | Gestão CLAUDE.md | Treino (300) | Teste (300) |
|:--|--:|--:|--:|--:|--:|--:|--:|
| abaixo de -15 | 331 | −R$ 9,5 | −R$ 31,6 | −R$ 31,8 | −R$ 3,0 | −R$ 3,0 | −R$ 16,0 |
| -15 a -8 | 987 | −R$ 3,5 | +R$ 3,3 | +R$ 3,7 | +R$ 0,5 | +R$ 1,6 | −R$ 9,8 |
| -8 a -4 | 2.046 | +R$ 8,1 | +R$ 8,6 | −R$ 4,1 | +R$ 6,6 | +R$ 16,0 | −R$ 4,4 |
| -4 a -2 | 1.521 | −R$ 6,7 | −R$ 9,3 | −R$ 22,8 | −R$ 2,9 | −R$ 5,7 | −R$ 9,1 |
| -2 ou mais | 615 | −R$ 8,5 | −R$ 23,1 | −R$ 43,0 | −R$ 1,5 | −R$ 10,9 | +R$ 2,2 |

**Exaustão limpa: ângulo VWAP**

| Exaustão limpa: ângulo VWAP | Sinais | Alvo 300 seco | Alvo 500 seco | Alvo na VWAP | Gestão CLAUDE.md | Treino (300) | Teste (300) |
|:--|--:|--:|--:|--:|--:|--:|--:|
| abaixo de -8 | 132 | +R$ 18,8 | −R$ 8,5 | +R$ 12,4 | +R$ 21,5 | +R$ 26,0 | +R$ 13,2 |
| -8 a -4 | 138 | −R$ 15,2 | −R$ 13,4 | −R$ 26,2 | −R$ 3,9 | −R$ 10,4 | −R$ 21,9 |
| -4 a -2 | 120 | +R$ 32,0 | +R$ 36,0 | +R$ 40,2 | +R$ 26,0 | +R$ 23,7 | +R$ 49,3 |
| -2 ou mais | 55 | +R$ 45,0 | +R$ 5,7 | +R$ 2,6 | +R$ 50,5 | +R$ 22,9 | +R$ 90,3 |

**A banda importa? Exaustão limpa em qualquer lugar, pela distância do extremo à VWAP (em bandas)**

| Extremo | Sinais | Alvo 300 seco | Alvo 500 seco | Alvo na VWAP | Gestão CLAUDE.md | Treino (300) | Teste (300) |
|:--|--:|--:|--:|--:|--:|--:|--:|
| abaixo de 0 | 319 | +R$ 19,2 | +R$ 14,7 | −R$ 789,6 | +R$ 12,4 | +R$ 21,2 | +R$ 14,8 |
| 0 a 1 | 538 | +R$ 10,8 | +R$ 6,1 | −R$ 0,6 | +R$ 7,3 | +R$ 12,6 | +R$ 8,3 |
| 1 a 2 | 286 | +R$ 6,7 | −R$ 10,1 | −R$ 8,5 | +R$ 14,8 | −R$ 2,3 | +R$ 20,2 |
| 2 ou mais | 159 | +R$ 30,2 | +R$ 28,7 | +R$ 34,1 | +R$ 24,9 | +R$ 45,0 | +R$ 13,2 |

## VWAP como entrada (1º candle contra)

| Grupo | Sinais | Alvo 300 | Alvo 500 | Alvo banda 1 | CLAUDE.md |
|:--|--:|--:|--:|--:|--:|
| todos | 4.248 | −R$ 2,3 | −R$ 5,1 | −R$ 4,1 | −R$ 1,6 |
| pullback: o preco já tinha ido a banda a favor no dia | 1.915 | −R$ 6,4 | −R$ 10,5 | −R$ 10,3 | −R$ 5,0 |
| sem banda a favor antes | 2.333 | +R$ 1,1 | −R$ 0,7 | +R$ 1,0 | +R$ 1,1 |
| VWAP a favor (> 1 pt/candle) | 1.211 | −R$ 0,9 | −R$ 10,6 | −R$ 5,2 | −R$ 0,1 |
| VWAP plana (-1 a 1) | 2.153 | −R$ 1,6 | +R$ 1,1 | −R$ 2,4 | −R$ 0,3 |
| VWAP contra (< -1) | 884 | −R$ 5,9 | −R$ 12,6 | −R$ 7,0 | −R$ 6,9 |
| pullback e VWAP a favor | 483 | −R$ 10,7 | −R$ 26,1 | −R$ 29,8 | −R$ 7,8 |
| empurrão de 4+ candles até a VWAP | 1.041 | +R$ 1,1 | −R$ 4,2 | −R$ 11,6 | +R$ 1,7 |
| topo/fundo duplo na VWAP | 1.868 | −R$ 7,8 | −R$ 5,0 | −R$ 3,3 | −R$ 5,7 |
| pavio de rejeição | 2.661 | −R$ 3,1 | −R$ 7,4 | −R$ 4,1 | −R$ 1,8 |
| 1º sinal do dia naquele lado | 264 | +R$ 11,5 | +R$ 10,6 | +R$ 31,2 | +R$ 7,5 |

## VWAP como alvo (todos os sinais c1)

| Stop | Chegou na VWAP | R$/trade |
|:--|--:|--:|
| 100 | 9,5% | −R$ 13,9 |
| 150 | 13,0% | −R$ 23,9 |
| 200 | 16,5% | −R$ 29,2 |
| 300 | 22,6% | −R$ 35,7 |
| extremo + 10 (max 300) | 13,3% | −R$ 23,7 |
| sem stop | 49,7% | - |

## Carteira: Alvo 300 seco (stop 100 / alvo 300 seco)

| Filtro | Trades | Líquido | Fator | Rebaix. | Treino | Teste | Atravessar 5 |
|:--|--:|--:|--:|--:|--:|--:|--:|
| c1: todos os sinais nas bandas | 4.352 | +R$ 504 | 1,00 | −R$ 17.064 | +R$ 13.101 | −R$ 12.597 | −R$ 6.996 |
| c1: exaustão (4+ candles) | 1.145 | +R$ 3.885 | 1,04 | −R$ 8.256 | +R$ 6.291 | −R$ 2.406 | +R$ 1.965 |
| c1: sem pavio de rejeição | 1.897 | +R$ 5.949 | 1,03 | −R$ 4.899 | +R$ 6.720 | −R$ 771 | +R$ 3.807 |
| c1: exaustão limpa (4+ candles, sem pavio de rejeição) | 445 | +R$ 6.705 | 1,17 | −R$ 4.836 | +R$ 3.429 | +R$ 3.276 | +R$ 6.225 |
| c1: exaustão limpa e 1º/2º toque na banda 1 | 390 | +R$ 7.590 | 1,23 | −R$ 4.455 | +R$ 2.421 | +R$ 5.169 | +R$ 7.110 |
| c1: exaustão limpa e VWAP não inclinada contra (> -2) | 55 | +R$ 2.475 | 1,57 | −R$ 1.230 | +R$ 849 | +R$ 1.626 | +R$ 2.475 |
| c1: exaustão limpa e banda 2 ou 3 | 159 | +R$ 4.803 | 1,36 | −R$ 1.389 | +R$ 3.825 | +R$ 978 | +R$ 4.323 |
| c1: 1º toque na banda 1 | 2.309 | +R$ 5.913 | 1,03 | −R$ 7.887 | +R$ 11.640 | −R$ 5.727 | +R$ 2.463 |
| c1: banda 2 ou 3 | 1.539 | +R$ 303 | 1,00 | −R$ 9.318 | +R$ 3.393 | −R$ 3.090 | −R$ 4.698 |
| c2: todos | 2.596 | −R$ 16.308 | 0,93 | −R$ 17.589 | −R$ 11.337 | −R$ 4.971 | −R$ 21.933 |
| Hull vira: todos | 809 | −R$ 10.587 | 0,86 | −R$ 11.865 | −R$ 8.778 | −R$ 1.809 | −R$ 11.067 |

## Carteira: Alvo 500 seco (stop 100 / alvo 500 seco)

| Filtro | Trades | Líquido | Fator | Rebaix. | Treino | Teste | Atravessar 5 |
|:--|--:|--:|--:|--:|--:|--:|--:|
| c1: todos os sinais nas bandas | 3.617 | −R$ 8.091 | 0,98 | −R$ 21.063 | +R$ 3.984 | −R$ 12.075 | −R$ 10.602 |
| c1: exaustão (4+ candles) | 1.135 | −R$ 2.445 | 0,98 | −R$ 10.413 | +R$ 1.275 | −R$ 3.720 | −R$ 4.605 |
| c1: sem pavio de rejeição | 1.740 | −R$ 900 | 0,99 | −R$ 9.870 | −R$ 36 | −R$ 864 | −R$ 777 |
| c1: exaustão limpa (4+ candles, sem pavio de rejeição) | 442 | +R$ 2.034 | 1,05 | −R$ 5.190 | −R$ 402 | +R$ 2.436 | +R$ 2.034 |
| c1: exaustão limpa e 1º/2º toque na banda 1 | 387 | +R$ 3.639 | 1,09 | −R$ 4.575 | −R$ 450 | +R$ 4.089 | +R$ 3.639 |
| c1: exaustão limpa e VWAP não inclinada contra (> -2) | 55 | +R$ 315 | 1,06 | −R$ 1.371 | +R$ 369 | −R$ 54 | +R$ 315 |
| c1: exaustão limpa e banda 2 ou 3 | 158 | +R$ 4.686 | 1,31 | −R$ 1.635 | +R$ 2.628 | +R$ 2.058 | +R$ 4.686 |
| c1: 1º toque na banda 1 | 1.904 | −R$ 2.952 | 0,98 | −R$ 12.543 | +R$ 1.383 | −R$ 4.335 | −R$ 4.989 |
| c1: banda 2 ou 3 | 1.261 | +R$ 3.657 | 1,03 | −R$ 8.715 | +R$ 3.261 | +R$ 396 | +R$ 3.903 |
| c2: todos | 2.365 | −R$ 19.455 | 0,92 | −R$ 25.038 | −R$ 12.573 | −R$ 6.882 | −R$ 20.415 |
| Hull vira: todos | 807 | −R$ 6.381 | 0,92 | −R$ 10.686 | −R$ 7.452 | +R$ 1.071 | −R$ 7.101 |

## Carteira: Alvo na VWAP (stop 100 / alvo na VWAP)

| Filtro | Trades | Líquido | Fator | Rebaix. | Treino | Teste | Atravessar 5 |
|:--|--:|--:|--:|--:|--:|--:|--:|
| c1: todos os sinais nas bandas | 2.643 | −R$ 14.695 | 0,95 | −R$ 21.486 | −R$ 6.157 | −R$ 8.538 | −R$ 15.402 |
| c1: exaustão (4+ candles) | 1.019 | −R$ 5.855 | 0,95 | −R$ 14.085 | −R$ 7.662 | +R$ 1.807 | −R$ 5.881 |
| c1: sem pavio de rejeição | 1.438 | +R$ 80 | 1,00 | −R$ 15.114 | −R$ 7.366 | +R$ 7.446 | +R$ 46 |
| c1: exaustão limpa (4+ candles, sem pavio de rejeição) | 420 | +R$ 3.897 | 1,09 | −R$ 6.692 | −R$ 1.883 | +R$ 5.781 | +R$ 3.895 |
| c1: exaustão limpa e 1º/2º toque na banda 1 | 368 | +R$ 3.237 | 1,08 | −R$ 6.183 | −R$ 2.924 | +R$ 6.162 | +R$ 3.235 |
| c1: exaustão limpa e VWAP não inclinada contra (> -2) | 55 | +R$ 142 | 1,02 | −R$ 2.442 | +R$ 563 | −R$ 421 | +R$ 142 |
| c1: exaustão limpa e banda 2 ou 3 | 147 | +R$ 5.937 | 1,39 | −R$ 3.591 | +R$ 3.732 | +R$ 2.205 | +R$ 5.937 |
| c1: 1º toque na banda 1 | 1.396 | −R$ 11.180 | 0,93 | −R$ 17.249 | −R$ 8.947 | −R$ 2.234 | −R$ 11.873 |
| c1: banda 2 ou 3 | 880 | −R$ 78 | 1,00 | −R$ 12.627 | −R$ 3.093 | +R$ 3.015 | −R$ 82 |
| c2: todos | 1.960 | −R$ 17.599 | 0,91 | −R$ 21.635 | −R$ 16.358 | −R$ 1.241 | −R$ 17.628 |
| Hull vira: todos | 783 | −R$ 11.932 | 0,85 | −R$ 16.141 | −R$ 12.305 | +R$ 373 | −R$ 12.698 |

## Carteira: Gestão CLAUDE.md (stop 100, parcial 50% em +100, alvo 300)

| Filtro | Trades | Líquido | Fator | Rebaix. | Treino | Teste | Atravessar 5 |
|:--|--:|--:|--:|--:|--:|--:|--:|
| c1: todos os sinais nas bandas | 4.352 | +R$ 9.264 | 1,04 | −R$ 6.828 | +R$ 10.161 | −R$ 897 | −R$ 1.236 |
| c1: exaustão (4+ candles) | 1.145 | +R$ 9.885 | 1,16 | −R$ 3.531 | +R$ 8.631 | +R$ 1.254 | +R$ 7.245 |
| c1: sem pavio de rejeição | 1.897 | +R$ 9.729 | 1,09 | −R$ 3.225 | +R$ 8.040 | +R$ 1.689 | +R$ 5.547 |
| c1: exaustão limpa (4+ candles, sem pavio de rejeição) | 445 | +R$ 8.205 | 1,37 | −R$ 1.950 | +R$ 4.449 | +R$ 3.756 | +R$ 7.485 |
| c1: exaustão limpa e 1º/2º toque na banda 1 | 390 | +R$ 8.670 | 1,46 | −R$ 1.569 | +R$ 3.741 | +R$ 4.929 | +R$ 8.070 |
| c1: exaustão limpa e VWAP não inclinada contra (> -2) | 55 | +R$ 2.775 | 2,55 | −R$ 750 | +R$ 1.269 | +R$ 1.506 | +R$ 2.655 |
| c1: exaustão limpa e banda 2 ou 3 | 159 | +R$ 3.963 | 1,50 | −R$ 678 | +R$ 2.865 | +R$ 1.098 | +R$ 3.723 |
| c1: 1º toque na banda 1 | 2.309 | +R$ 8.073 | 1,06 | −R$ 5.454 | +R$ 7.140 | +R$ 933 | +R$ 2.823 |
| c1: banda 2 ou 3 | 1.539 | +R$ 1.083 | 1,01 | −R$ 5.976 | +R$ 1.533 | −R$ 450 | −R$ 3.558 |
| c2: todos | 2.596 | −R$ 6.528 | 0,96 | −R$ 10.242 | −R$ 4.317 | −R$ 2.211 | −R$ 13.833 |
| Hull vira: todos | 809 | −R$ 7.947 | 0,85 | −R$ 8.472 | −R$ 6.798 | −R$ 1.149 | −R$ 10.347 |

## Robustez da exaustão limpa

| Stop | Alvo | R$/sinal | Treino | Teste | Carteira | Fator |
|:--|:--|--:|--:|--:|--:|--:|
| 100 | 300 | +R$ 15,1 | +R$ 13,3 | +R$ 17,4 | +R$ 6.705 | 1,17 |
| 100 | 500 | +R$ 3,7 | −R$ 3,0 | +R$ 13,0 | +R$ 2.034 | 1,05 |
| 100 | VWAP | +R$ 6,7 | −R$ 7,1 | +R$ 25,5 | +R$ 3.897 | 1,09 |
| 150 | 300 | +R$ 4,4 | +R$ 0,5 | +R$ 9,8 | +R$ 1.965 | 1,04 |
| 150 | 500 | −R$ 8,1 | −R$ 19,3 | +R$ 7,2 | −R$ 2.151 | 0,96 |
| 150 | VWAP | −R$ 10,5 | −R$ 29,5 | +R$ 15,5 | −R$ 2.468 | 0,96 |
| 200 | 300 | +R$ 5,6 | −R$ 2,1 | +R$ 16,1 | +R$ 2.505 | 1,04 |
| 200 | 500 | −R$ 2,5 | −R$ 18,4 | +R$ 19,3 | +R$ 738 | 1,01 |
| 200 | VWAP | −R$ 9,2 | −R$ 28,4 | +R$ 17,2 | +R$ 1.455 | 1,02 |
| extremo + 10 | 300 | +R$ 14,5 | +R$ 11,7 | +R$ 18,4 | +R$ 6.453 | 1,14 |
| extremo + 10 | 500 | +R$ 0,2 | −R$ 9,4 | +R$ 13,4 | +R$ 1.359 | 1,03 |
| extremo + 10 | VWAP | +R$ 4,2 | −R$ 13,1 | +R$ 27,8 | +R$ 3.996 | 1,08 |

Bootstrap de pregões (4.000 sorteios): chance de prejuízo Alvo 300 seco 6,2%, Alvo 500 seco 37,8%, Alvo na VWAP 30,3%, Gestão CLAUDE.md 0,3%.

**Limites**: 130 pregões de um regime; ~4 sinais/pregão na exaustão limpa e ~2 no recorte de 1º/2º toque; 21 hipóteses testadas. O que sustenta o candidato é a consistência (treino, teste, 3 terços, 4 saídas), não o tamanho do número.
