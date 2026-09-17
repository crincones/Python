# Oscilacao do preco em torno da EMA 21

Setup EMA 21 + HullRetracao_Azul + MACD, WINFUT PI 20, 132 pregoes (2026-03-06 a 2026-09-14), 2.141 sinais. Entrada seca no fechamento, 6 contratos, R$ 0,50 por contrato. Treino ate 2026-07-01. Graficos e tabelas completas em `oscila.html`.

## O que foi medido

Em janelas de 5, 10 e 20 candles, a distancia `fechamento - EMA 21` de cada candle, orientada pelo lado do trade (compra: acima da EMA e positivo; venda: espelho). Duas ancoras: janela terminando no candle anterior ao recuo (principal) e no candle do trigger. Daí saem:

- **candles de cada lado**: a favor menos contra, e a fracao no lado dominante (0,5 = metade de cada lado, 1 = todos do mesmo lado);
- **somatoria** das distancias / W, em pontos e em ranges medios;
- **pureza** = |soma| / soma dos valores absolutos: 1 = nada se cancelou (um lado so), perto de 0 = oscilacao em torno da media;
- **distancia media absoluta** ate a EMA;
- **cruzamentos** do fechamento pela EMA e fracao de candles cortados por ela.

## Stop 100 / alvo 400 sem parcial

**Cruzamentos da EMA em 20 candles (antes do recuo)**

| Cruzamentos | Sinais | R$/trade | Treino | Teste |
|:--|--:|--:|--:|--:|
| -inf a 1 | 289 | −R$ 10,1 | −R$ 1,1 | −R$ 28,3 |
| 1 a 2 | 340 | −R$ 9,0 | −R$ 8,3 | −R$ 10,4 |
| 2 a 4 | 612 | +R$ 27,8 | +R$ 28,9 | +R$ 25,7 |
| 4 a 5 | 254 | −R$ 1,1 | −R$ 21,6 | +R$ 34,4 |
| 5 a +inf | 643 | +R$ 1,1 | −R$ 5,5 | +R$ 14,6 |

**Pureza em 5 candles (antes do recuo)**

| Pureza | Sinais | R$/trade | Treino | Teste |
|:--|--:|--:|--:|--:|
| -inf a 0.74 | 431 | −R$ 5,8 | −R$ 6,8 | −R$ 3,8 |
| 0.74 a +inf | 1.707 | +R$ 8,2 | +R$ 4,9 | +R$ 14,6 |

**Pureza em 20 candles (antes do recuo)**

| Pureza | Sinais | R$/trade | Treino | Teste |
|:--|--:|--:|--:|--:|
| -inf a 0.3 | 420 | −R$ 0,1 | −R$ 0,0 | −R$ 0,4 |
| 0.3 a 0.58 | 418 | +R$ 6,2 | −R$ 6,8 | +R$ 33,4 |
| 0.58 a 0.8 | 443 | +R$ 8,4 | −R$ 1,7 | +R$ 26,4 |
| 0.8 a 0.97 | 420 | +R$ 7,0 | +R$ 10,6 | −R$ 0,4 |
| 0.97 a +inf | 437 | +R$ 5,2 | +R$ 10,9 | −R$ 5,4 |

**Carteira**

| Filtro | Sinais | Trades | Liquido | Fator | Rebaix. | Treino | Teste |
|:--|--:|--:|--:|--:|--:|--:|--:|
| sem filtro | 100% | 1.947 | +R$ 11.199 | 1,06 | −R$ 7.089 | +R$ 2.121 | +R$ 9.078 |
| pureza 5 (antes do recuo) >= 0,7 | 81% | 1.598 | +R$ 11.646 | 1,08 | −R$ 5.847 | +R$ 2.925 | +R$ 8.721 |
| pureza 5 (antes do recuo) >= 0,5 | 88% | 1.716 | +R$ 11.532 | 1,07 | −R$ 5.658 | +R$ 4.269 | +R$ 7.263 |
| 4 dos 5 fechamentos do mesmo lado | 84% | 1.661 | +R$ 9.177 | 1,06 | −R$ 6.081 | +R$ 2.577 | +R$ 6.600 |
| pureza 10 (antes do recuo) >= 0,5 | 76% | 1.485 | +R$ 9.345 | 1,07 | −R$ 8.928 | +R$ 2.562 | +R$ 6.783 |
| pureza 20 (antes do recuo) >= 0,3 | 81% | 1.588 | +R$ 10.836 | 1,07 | −R$ 8.595 | +R$ 3.444 | +R$ 7.392 |
| pureza 20 (antes do recuo) >= 0,5 | 67% | 1.325 | +R$ 11.145 | 1,09 | −R$ 6.414 | +R$ 6.138 | +R$ 5.007 |
| lado dominante 20 >= 0,7 | 65% | 1.272 | +R$ 8.664 | 1,07 | −R$ 7.515 | +R$ 3.705 | +R$ 4.959 |
| somatoria 20 a favor (>= 0) | 67% | 1.313 | +R$ 6.741 | 1,05 | −R$ 6.423 | +R$ 639 | +R$ 6.102 |
| 2 a 4 cruzamentos da EMA em 20 | 40% | 805 | +R$ 18.225 | 1,24 | −R$ 4.179 | +R$ 9.576 | +R$ 8.649 |
| pelo menos 2 cruzamentos da EMA em 20 | 70% | 1.374 | +R$ 17.838 | 1,14 | −R$ 4.449 | +R$ 6.273 | +R$ 11.565 |
| no maximo 2 cruzamentos da EMA em 20 | 42% | 846 | +R$ 1.782 | 1,02 | −R$ 6.078 | +R$ 2.874 | −R$ 1.092 |
| distancia media ate a EMA em 20 < 211 pts | 79% | 1.532 | +R$ 14.004 | 1,10 | −R$ 6.129 | +R$ 3.045 | +R$ 10.959 |
| fora de: 0-1 cruzamento E distancia media > 177 pts | 77% | 1.497 | +R$ 16.629 | 1,12 | −R$ 6.387 | +R$ 6.000 | +R$ 10.629 |
| EMA dentro do range em <= 40% dos candles de 20 | 78% | 1.536 | +R$ 9.312 | 1,06 | −R$ 7.878 | +R$ 1.404 | +R$ 7.908 |
| fora da consolidacao 100 (er >= 0,08) | 46% | 894 | +R$ 21.798 | 1,26 | −R$ 3.354 | +R$ 12.138 | +R$ 9.660 |
| nao passou da Keltner 2,5 | 73% | 1.412 | +R$ 15.444 | 1,12 | −R$ 4.605 | +R$ 4.488 | +R$ 10.956 |
| consolidacao 100 E Keltner | 30% | 598 | +R$ 18.726 | 1,35 | −R$ 2.229 | +R$ 9.111 | +R$ 9.615 |
| pureza 5 >= 0,7 | 81% | 1.598 | +R$ 11.646 | 1,08 | −R$ 5.847 | +R$ 2.925 | +R$ 8.721 |
| pureza 5 >= 0,7 E consolidacao 100 | 38% | 757 | +R$ 16.329 | 1,23 | −R$ 3.981 | +R$ 8.919 | +R$ 7.410 |
| pureza 5 >= 0,7 E consolidacao 100 E Keltner | 23% | 463 | +R$ 13.011 | 1,31 | −R$ 2.214 | +R$ 5.892 | +R$ 7.119 |
| 2 a 4 cruzamentos em 20 | 40% | 805 | +R$ 18.225 | 1,24 | −R$ 4.179 | +R$ 9.576 | +R$ 8.649 |
| 2 a 4 cruzamentos em 20 E consolidacao 100 E Keltner | 15% | 294 | +R$ 11.478 | 1,44 | −R$ 2.382 | +R$ 3.963 | +R$ 7.515 |
| pureza 5 E 2 a 4 cruzamentos E consolidacao 100 E Keltner | 12% | 242 | +R$ 9.234 | 1,43 | −R$ 2.427 | +R$ 2.982 | +R$ 6.252 |
| distancia media < 211 pts E consolidacao 100 E Keltner | 27% | 530 | +R$ 16.890 | 1,35 | −R$ 2.457 | +R$ 7.923 | +R$ 8.967 |
| fora do canto ruim (0-1 cruzamento E longe da EMA) | 77% | 1.497 | +R$ 16.629 | 1,12 | −R$ 6.387 | +R$ 6.000 | +R$ 10.629 |
| fora do canto ruim E consolidacao 100 | 33% | 648 | +R$ 22.896 | 1,39 | −R$ 2.493 | +R$ 12.357 | +R$ 10.539 |
| fora do canto ruim E consolidacao 100 E Keltner | 27% | 527 | +R$ 16.659 | 1,35 | −R$ 2.457 | +R$ 7.323 | +R$ 9.336 |

**Estabilidade por terco do periodo** (R$/trade do grupo, entre parenteses o resto)

| Grupo | Sinais | 1o terco | 2o terco | 3o terco |
|:--|--:|--:|--:|--:|
| pureza 5 >= 0,7 (nao oscilou nos 5 candles) | 81% | +R$ 7,6 (−R$ 10,5) | −R$ 2,2 (+R$ 13,2) | +R$ 17,3 (−R$ 16,9) |
| pureza 20 >= 0,3 | 81% | +R$ 2,5 (+R$ 11,1) | +R$ 8,5 (−R$ 36,9) | +R$ 12,6 (+R$ 3,6) |
| 2 a 4 cruzamentos da EMA em 20 | 40% | +R$ 21,2 (−R$ 8,4) | +R$ 0,4 (+R$ 0,7) | +R$ 31,6 (−R$ 3,6) |
| nenhum cruzamento da EMA em 20 | 14% | −R$ 3,0 (+R$ 5,1) | −R$ 10,3 (+R$ 2,8) | −R$ 19,3 (+R$ 15,2) |
| distancia media ate a EMA em 20 < 211 pts | 79% | +R$ 9,9 (−R$ 21,2) | −R$ 3,3 (+R$ 13,1) | +R$ 18,0 (−R$ 15,1) |
| somatoria 20 a favor (>= 0) | 67% | +R$ 2,8 (+R$ 6,8) | +R$ 2,0 (−R$ 2,4) | +R$ 10,0 (+R$ 12,5) |
| 0-1 cruzamento E distancia media > 177 pts (canto ruim) | 23% | −R$ 19,3 (+R$ 10,2) | −R$ 8,6 (+R$ 3,8) | −R$ 10,2 (+R$ 17,3) |

## Gestao do CLAUDE.md (stop 100, parcial +100, alvo 300)

**Cruzamentos da EMA em 20 candles (antes do recuo)**

| Cruzamentos | Sinais | R$/trade | Treino | Teste |
|:--|--:|--:|--:|--:|
| -inf a 1 | 289 | −R$ 4,2 | −R$ 0,5 | −R$ 11,8 |
| 1 a 2 | 340 | −R$ 2,3 | −R$ 5,1 | +R$ 3,3 |
| 2 a 4 | 612 | +R$ 18,8 | +R$ 18,1 | +R$ 20,0 |
| 4 a 5 | 254 | +R$ 3,1 | −R$ 1,5 | +R$ 11,2 |
| 5 a +inf | 643 | −R$ 1,1 | −R$ 7,2 | +R$ 11,2 |

**Pureza em 5 candles (antes do recuo)**

| Pureza | Sinais | R$/trade | Treino | Teste |
|:--|--:|--:|--:|--:|
| -inf a 0.74 | 431 | −R$ 6,3 | −R$ 5,1 | −R$ 8,7 |
| 0.74 a +inf | 1.707 | +R$ 7,2 | +R$ 3,7 | +R$ 14,1 |

**Pureza em 20 candles (antes do recuo)**

| Pureza | Sinais | R$/trade | Treino | Teste |
|:--|--:|--:|--:|--:|
| -inf a 0.3 | 420 | +R$ 4,4 | −R$ 2,2 | +R$ 18,0 |
| 0.3 a 0.58 | 418 | +R$ 2,2 | −R$ 2,2 | +R$ 11,2 |
| 0.58 a 0.8 | 443 | +R$ 0,8 | −R$ 3,8 | +R$ 9,1 |
| 0.8 a 0.97 | 420 | +R$ 9,9 | +R$ 12,3 | +R$ 4,8 |
| 0.97 a +inf | 437 | +R$ 5,2 | +R$ 5,5 | +R$ 4,8 |

**Carteira**

| Filtro | Sinais | Trades | Liquido | Fator | Rebaix. | Treino | Teste |
|:--|--:|--:|--:|--:|--:|--:|--:|
| sem filtro | 100% | 2.037 | +R$ 9.849 | 1,08 | −R$ 5.868 | +R$ 1.581 | +R$ 8.268 |
| pureza 5 (antes do recuo) >= 0,7 | 81% | 1.667 | +R$ 12.999 | 1,14 | −R$ 4.509 | +R$ 3.270 | +R$ 9.729 |
| pureza 5 (antes do recuo) >= 0,5 | 88% | 1.796 | +R$ 11.172 | 1,11 | −R$ 4.551 | +R$ 3.030 | +R$ 8.142 |
| 4 dos 5 fechamentos do mesmo lado | 84% | 1.734 | +R$ 10.638 | 1,11 | −R$ 4.149 | +R$ 2.553 | +R$ 8.085 |
| pureza 10 (antes do recuo) >= 0,5 | 76% | 1.547 | +R$ 12.159 | 1,14 | −R$ 5.598 | +R$ 4.368 | +R$ 7.791 |
| pureza 20 (antes do recuo) >= 0,3 | 81% | 1.648 | +R$ 8.736 | 1,09 | −R$ 6.282 | +R$ 3.084 | +R$ 5.652 |
| pureza 20 (antes do recuo) >= 0,5 | 67% | 1.375 | +R$ 8.955 | 1,11 | −R$ 4.878 | +R$ 4.365 | +R$ 4.590 |
| lado dominante 20 >= 0,7 | 65% | 1.320 | +R$ 7.800 | 1,10 | −R$ 5.730 | +R$ 3.135 | +R$ 4.665 |
| somatoria 20 a favor (>= 0) | 67% | 1.366 | +R$ 7.782 | 1,10 | −R$ 4.551 | +R$ 2.217 | +R$ 5.565 |
| 2 a 4 cruzamentos da EMA em 20 | 40% | 832 | +R$ 12.744 | 1,28 | −R$ 1.293 | +R$ 7.116 | +R$ 5.628 |
| pelo menos 2 cruzamentos da EMA em 20 | 70% | 1.433 | +R$ 11.061 | 1,13 | −R$ 4.188 | +R$ 2.793 | +R$ 8.268 |
| no maximo 2 cruzamentos da EMA em 20 | 42% | 865 | +R$ 5.085 | 1,10 | −R$ 4.878 | +R$ 2.961 | +R$ 2.124 |
| distancia media ate a EMA em 20 < 211 pts | 79% | 1.609 | +R$ 12.453 | 1,13 | −R$ 5.373 | +R$ 2.886 | +R$ 9.567 |
| fora de: 0-1 cruzamento E distancia media > 177 pts | 77% | 1.566 | +R$ 12.102 | 1,13 | −R$ 5.577 | +R$ 3.579 | +R$ 8.523 |
| EMA dentro do range em <= 40% dos candles de 20 | 78% | 1.599 | +R$ 12.363 | 1,13 | −R$ 5.028 | +R$ 4.038 | +R$ 8.325 |
| fora da consolidacao 100 (er >= 0,08) | 46% | 925 | +R$ 14.625 | 1,28 | −R$ 1.959 | +R$ 9.675 | +R$ 4.950 |
| nao passou da Keltner 2,5 | 73% | 1.478 | +R$ 9.486 | 1,11 | −R$ 4.806 | +R$ 2.070 | +R$ 7.416 |
| consolidacao 100 E Keltner | 30% | 619 | +R$ 11.943 | 1,35 | −R$ 1.458 | +R$ 7.029 | +R$ 4.914 |
| pureza 5 >= 0,7 | 81% | 1.667 | +R$ 12.999 | 1,14 | −R$ 4.509 | +R$ 3.270 | +R$ 9.729 |
| pureza 5 >= 0,7 E consolidacao 100 | 38% | 777 | +R$ 11.469 | 1,26 | −R$ 1.887 | +R$ 6.954 | +R$ 4.515 |
| pureza 5 >= 0,7 E consolidacao 100 E Keltner | 23% | 473 | +R$ 8.421 | 1,32 | −R$ 1.431 | +R$ 4.188 | +R$ 4.233 |
| 2 a 4 cruzamentos em 20 | 40% | 832 | +R$ 12.744 | 1,28 | −R$ 1.293 | +R$ 7.116 | +R$ 5.628 |
| 2 a 4 cruzamentos em 20 E consolidacao 100 E Keltner | 15% | 301 | +R$ 7.137 | 1,43 | −R$ 1.317 | +R$ 2.868 | +R$ 4.269 |
| pureza 5 E 2 a 4 cruzamentos E consolidacao 100 E Keltner | 12% | 248 | +R$ 6.336 | 1,48 | −R$ 1.140 | +R$ 1.650 | +R$ 4.686 |
| distancia media < 211 pts E consolidacao 100 E Keltner | 27% | 548 | +R$ 10.956 | 1,37 | −R$ 1.377 | +R$ 6.204 | +R$ 4.752 |
| fora do canto ruim (0-1 cruzamento E longe da EMA) | 77% | 1.566 | +R$ 12.102 | 1,13 | −R$ 5.577 | +R$ 3.579 | +R$ 8.523 |
| fora do canto ruim E consolidacao 100 | 33% | 670 | +R$ 13.590 | 1,37 | −R$ 1.746 | +R$ 8.109 | +R$ 5.481 |
| fora do canto ruim E consolidacao 100 E Keltner | 27% | 543 | +R$ 10.011 | 1,33 | −R$ 1.254 | +R$ 5.247 | +R$ 4.764 |

**Estabilidade por terco do periodo** (R$/trade do grupo, entre parenteses o resto)

| Grupo | Sinais | 1o terco | 2o terco | 3o terco |
|:--|--:|--:|--:|--:|
| pureza 5 >= 0,7 (nao oscilou nos 5 candles) | 81% | +R$ 4,6 (−R$ 6,4) | +R$ 1,4 (−R$ 1,8) | +R$ 16,8 (−R$ 17,9) |
| pureza 20 >= 0,3 | 81% | +R$ 2,1 (+R$ 4,1) | +R$ 5,9 (−R$ 23,6) | +R$ 7,4 (+R$ 21,4) |
| 2 a 4 cruzamentos da EMA em 20 | 40% | +R$ 14,2 (−R$ 6,1) | +R$ 5,6 (−R$ 2,0) | +R$ 21,0 (+R$ 2,7) |
| nenhum cruzamento da EMA em 20 | 14% | +R$ 4,6 (+R$ 2,2) | −R$ 10,3 (+R$ 3,1) | −R$ 8,9 (+R$ 13,0) |
| distancia media ate a EMA em 20 < 211 pts | 79% | +R$ 6,0 (−R$ 12,8) | +R$ 0,3 (+R$ 2,4) | +R$ 15,6 (−R$ 9,0) |
| somatoria 20 a favor (>= 0) | 67% | +R$ 3,8 (+R$ 0,0) | +R$ 3,0 (−R$ 3,6) | +R$ 8,6 (+R$ 13,7) |
| 0-1 cruzamento E distancia media > 177 pts (canto ruim) | 23% | −R$ 11,2 (+R$ 6,0) | −R$ 3,8 (+R$ 2,4) | −R$ 4,6 (+R$ 14,8) |

## Conclusoes

1. **Em 20 candles a hipotese se inverte.** Os sinais em que o preco ficou todo de um lado da EMA (nenhum cruzamento) sao 289 (14%) e deram −R$ 10,1 por trade contra +R$ 7,6 do resto no alvo 400 (−R$ 4,2 x +R$ 5,7 no CLAUDE.md), negativos no treino e no teste. A faixa de 2 a 4 cruzamentos e a melhor; em carteira +R$ 11.199 -> +R$ 18.225.
2. **Em 5 candles a hipotese vale.** O quintil de baixo da pureza de 5 (candles repartidos entre os dois lados) e negativo no treino e no teste nas duas gestoes. Filtrar por pureza 5 >= 0,7 corta 19% dos sinais e melhora as duas carteiras (+R$ 11.199 -> +R$ 11.646, +R$ 9.849 -> +R$ 12.999).
3. **O corte mais firme e o cruzamento das duas coisas**: 0 ou 1 cruzamento da EMA em 20 candles E distancia media acima de 177 pts. 23% dos sinais, negativo nos tres tercos do periodo e nas duas gestoes. Descartando so esse canto: +R$ 11.199 -> +R$ 16.629 e +R$ 9.849 -> +R$ 12.102.
4. **A somatoria com sinal nao separa nada.** De que lado da media o preco ficou e indiferente; o que importa e o formato do caminho (quantos cruzamentos, a que distancia).
5. **Nao e um filtro independente.** "Poucos cruzamentos" e "longe da media" tem correlacao de posto −0,45 e 0,52 com o quanto o preco passou da Keltner 2,5: e outra forma de medir movimento esticado, que o `impulso.html` ja tinha apontado. Somado a consolidacao de 100 candles o ganho fica pequeno.

Reproduzir: `python oscila.py && python oscila_rel.py`.
