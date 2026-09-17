# MACD x Bollinger 1000 no trigger

Setup EMA 21 + HullRetracao_Azul + MACD, WINFUT PI 20, 132 pregoes (2026-03-06 a 2026-09-14), 2.087 sinais com Bollinger. Entrada seca no fechamento, 6 contratos, R$ 0,50 por contrato. Treino ate 2026-07-01. Graficos em `macd_bb.html`.

Desvios = (MACD - media 1000) / desvio 1000, com o sinal do trade. A banda do grafico (1,0) e o desvio 1. No trigger: mediana 0,39, p10 0,05, p90 0,79.

## Stop 100 / alvo 400 sem parcial

**Exigir MACD >= k desvios**

| k | Mantidos | R$/trade | Cortados | Treino (cortados) | Teste (cortados) | Stop cheio (cortados) | t |
|--:|--:|--:|--:|--:|--:|--:|--:|
| 0,00 | 1.951 (94%) | +R$ 5,3 | +R$ 19,1 | +R$ 1,4 (+R$ 39,4) | +R$ 12,7 (−R$ 14,8) | 78% (74%) | −0,62 |
| 0,10 | 1.770 (85%) | +R$ 6,1 | +R$ 6,8 | +R$ 1,7 (+R$ 15,7) | +R$ 14,5 (−R$ 9,4) | 78% (77%) | −0,05 |
| 0,20 | 1.507 (72%) | +R$ 8,8 | −R$ 0,5 | +R$ 4,2 (+R$ 2,6) | +R$ 17,2 (−R$ 6,8) | 78% (79%) | 0,79 |
| 0,30 | 1.284 (62%) | +R$ 11,9 | −R$ 2,9 | +R$ 4,8 (+R$ 2,2) | +R$ 25,1 (−R$ 12,7) | 77% (79%) | 1,35 |
| 0,40 | 1.006 (48%) | +R$ 2,8 | +R$ 9,3 | −R$ 6,2 (+R$ 12,7) | +R$ 19,0 (+R$ 2,6) | 79% (77%) | −0,60 |
| 0,50 | 748 (36%) | −R$ 2,8 | +R$ 11,2 | −R$ 10,7 (+R$ 11,7) | +R$ 11,4 (+R$ 10,4) | 80% (77%) | −1,27 |
| 0,60 | 528 (25%) | +R$ 12,0 | +R$ 4,2 | +R$ 6,7 (+R$ 2,8) | +R$ 21,1 (+R$ 7,0) | 77% (78%) | 0,62 |
| 0,75 | 257 (12%) | +R$ 6,3 | +R$ 6,2 | −R$ 1,6 (+R$ 4,6) | +R$ 23,3 (+R$ 9,2) | 78% (78%) | 0,01 |
| 0,90 | 104 (5%) | +R$ 3,9 | +R$ 6,3 | +R$ 31,3 (+R$ 2,3) | −R$ 52,4 (+R$ 13,9) | 79% (78%) | −0,10 |
| 1,00 | 62 (3%) | −R$ 35,9 | +R$ 7,5 | −R$ 30,7 (+R$ 4,8) | −R$ 44,7 (+R$ 12,6) | 85% (78%) | −1,57 |

**Faixas**

| Desvios | Sinais | R$/trade | Treino | Teste | Stop cheio |
|:--|--:|--:|--:|--:|--:|
| abaixo de 0 (MACD abaixo da media 1000) | 136 | +R$ 19,1 | +R$ 39,4 | −R$ 14,8 | 74% |
| 0,0 a 0,2 | 444 | −R$ 6,5 | −R$ 7,8 | −R$ 3,9 | 80% |
| 0,2 a 0,4 | 501 | +R$ 20,7 | +R$ 24,6 | +R$ 13,2 | 76% |
| 0,4 a 0,6 | 478 | −R$ 7,3 | −R$ 19,9 | +R$ 16,5 | 80% |
| 0,6 a 0,8 | 330 | +R$ 9,4 | +R$ 4,7 | +R$ 16,8 | 77% |
| 0,8 a 1,0 | 136 | +R$ 40,2 | +R$ 27,0 | +R$ 67,9 | 73% |
| 1,0 ou mais (alem da banda) | 62 | −R$ 35,9 | −R$ 30,7 | −R$ 44,7 | 85% |

**Carteira**

| Filtro | Trades | Liquido | Fator | Rebaix. | Treino | Teste |
|:--|--:|--:|--:|--:|--:|--:|
| sem exigencia extra (so MACD > 0) | 1.897 | +R$ 12.549 | 1,07 | −R$ 7.089 | +R$ 3.471 | +R$ 9.078 |
| MACD >= 0,00 desvios (acima da media 1000) | 1.786 | +R$ 9.642 | 1,06 | −R$ 8.382 | +R$ 69 | +R$ 9.573 |
| MACD >= 0,10 desvios | 1.627 | +R$ 9.759 | 1,06 | −R$ 6.969 | −R$ 333 | +R$ 10.092 |
| MACD >= 0,20 desvios | 1.382 | +R$ 11.214 | 1,08 | −R$ 5.646 | +R$ 774 | +R$ 10.440 |
| MACD >= 0,30 desvios | 1.189 | +R$ 12.513 | 1,11 | −R$ 5.190 | +R$ 894 | +R$ 11.619 |
| MACD >= 0,40 desvios | 949 | +R$ 3.873 | 1,04 | −R$ 6.606 | −R$ 3.288 | +R$ 7.161 |
| MACD >= 0,50 desvios | 711 | −R$ 2.373 | 0,97 | −R$ 8.166 | −R$ 5.583 | +R$ 3.210 |
| MACD >= 0,60 desvios | 507 | +R$ 4.719 | 1,10 | −R$ 2.628 | +R$ 1.191 | +R$ 3.528 |
| MACD >= 0,75 desvios | 252 | +R$ 1.644 | 1,07 | −R$ 3.072 | +R$ 207 | +R$ 1.437 |
| MACD >= 0,90 desvios | 103 | +R$ 531 | 1,05 | −R$ 2.151 | +R$ 2.313 | −R$ 1.782 |
| MACD >= 1,00 desvios | 61 | −R$ 2.103 | 0,67 | −R$ 2.106 | −R$ 1.074 | −R$ 1.029 |
| MACD >= 0,5 desvios | 711 | −R$ 2.373 | 0,97 | −R$ 8.166 | −R$ 5.583 | +R$ 3.210 |
| MACD < 0,5 desvios | 1.237 | +R$ 13.449 | 1,11 | −R$ 5.076 | +R$ 8.364 | +R$ 5.085 |
| fora da consolidacao 100 | 878 | +R$ 22.566 | 1,28 | −R$ 3.354 | +R$ 12.906 | +R$ 9.660 |
| fora da consolidacao 100 E MACD >= 0,5 | 347 | +R$ 4.239 | 1,13 | −R$ 4.002 | +R$ 414 | +R$ 3.825 |
| nao passou da Keltner 2,5 | 1.371 | +R$ 17.487 | 1,14 | −R$ 3.672 | +R$ 6.531 | +R$ 10.956 |
| nao passou da Keltner 2,5 E MACD >= 0,5 | 407 | +R$ 3.219 | 1,08 | −R$ 4.464 | −R$ 2.244 | +R$ 5.463 |
| consolidacao 100 E Keltner | 586 | +R$ 20.202 | 1,38 | −R$ 2.229 | +R$ 10.587 | +R$ 9.615 |
| consolidacao 100 E Keltner E MACD >= 0,5 | 182 | +R$ 4.734 | 1,28 | −R$ 2.034 | +R$ 483 | +R$ 4.251 |

## Gestao do CLAUDE.md (stop 100, parcial +100, alvo 300)

**Exigir MACD >= k desvios**

| k | Mantidos | R$/trade | Cortados | Treino (cortados) | Teste (cortados) | Stop cheio (cortados) | t |
|--:|--:|--:|--:|--:|--:|--:|--:|
| 0,00 | 1.951 (94%) | +R$ 4,0 | +R$ 18,2 | +R$ 0,5 (+R$ 33,7) | +R$ 10,8 (−R$ 7,7) | 48% (39%) | −1,09 |
| 0,10 | 1.770 (85%) | +R$ 4,1 | +R$ 9,5 | +R$ 0,5 (+R$ 14,0) | +R$ 11,0 (+R$ 1,3) | 47% (47%) | −0,58 |
| 0,20 | 1.507 (72%) | +R$ 6,6 | +R$ 0,5 | +R$ 2,6 (+R$ 2,3) | +R$ 14,0 (−R$ 3,0) | 46% (50%) | 0,84 |
| 0,30 | 1.284 (62%) | +R$ 8,0 | −R$ 0,0 | +R$ 1,6 (+R$ 4,0) | +R$ 20,0 (−R$ 7,8) | 46% (50%) | 1,20 |
| 0,40 | 1.006 (48%) | +R$ 3,0 | +R$ 6,8 | −R$ 3,7 (+R$ 8,2) | +R$ 15,0 (+R$ 4,0) | 47% (47%) | −0,58 |
| 0,50 | 748 (36%) | +R$ 1,8 | +R$ 6,7 | −R$ 3,2 (+R$ 5,7) | +R$ 11,0 (+R$ 8,6) | 47% (47%) | −0,72 |
| 0,60 | 528 (25%) | +R$ 8,1 | +R$ 3,9 | +R$ 3,5 (+R$ 2,2) | +R$ 16,2 (+R$ 7,0) | 46% (48%) | 0,57 |
| 0,75 | 257 (12%) | +R$ 4,0 | +R$ 5,1 | −R$ 3,7 (+R$ 3,5) | +R$ 20,4 (+R$ 8,1) | 46% (47%) | −0,11 |
| 0,90 | 104 (5%) | +R$ 5,1 | +R$ 4,9 | +R$ 9,0 (+R$ 2,2) | −R$ 3,0 (+R$ 10,1) | 45% (47%) | 0,01 |
| 1,00 | 62 (3%) | −R$ 22,4 | +R$ 5,8 | −R$ 33,8 (+R$ 3,6) | −R$ 3,0 (+R$ 9,9) | 52% (47%) | −1,64 |

**Faixas**

| Desvios | Sinais | R$/trade | Treino | Teste | Stop cheio |
|:--|--:|--:|--:|--:|--:|
| abaixo de 0 (MACD abaixo da media 1000) | 136 | +R$ 18,2 | +R$ 33,7 | −R$ 7,7 | 39% |
| 0,0 a 0,2 | 444 | −R$ 4,9 | −R$ 6,6 | −R$ 1,3 | 53% |
| 0,2 a 0,4 | 501 | +R$ 14,0 | +R$ 15,1 | +R$ 11,8 | 44% |
| 0,4 a 0,6 | 478 | −R$ 2,7 | −R$ 11,5 | +R$ 13,6 | 49% |
| 0,6 a 0,8 | 330 | +R$ 8,6 | +R$ 7,0 | +R$ 11,2 | 45% |
| 0,8 a 1,0 | 136 | +R$ 20,8 | +R$ 11,3 | +R$ 40,6 | 43% |
| 1,0 ou mais (alem da banda) | 62 | −R$ 22,4 | −R$ 33,8 | −R$ 3,0 | 52% |

**Carteira**

| Filtro | Trades | Liquido | Fator | Rebaix. | Treino | Teste |
|:--|--:|--:|--:|--:|--:|--:|
| sem exigencia extra (so MACD > 0) | 1.986 | +R$ 10.602 | 1,09 | −R$ 5.868 | +R$ 2.334 | +R$ 8.268 |
| MACD >= 0,00 desvios (acima da media 1000) | 1.858 | +R$ 7.866 | 1,07 | −R$ 6.441 | −R$ 549 | +R$ 8.415 |
| MACD >= 0,10 desvios | 1.687 | +R$ 7.779 | 1,08 | −R$ 4.893 | −R$ 204 | +R$ 7.983 |
| MACD >= 0,20 desvios | 1.433 | +R$ 9.981 | 1,12 | −R$ 3.423 | +R$ 1.287 | +R$ 8.694 |
| MACD >= 0,30 desvios | 1.226 | +R$ 10.242 | 1,15 | −R$ 3.873 | +R$ 360 | +R$ 9.882 |
| MACD >= 0,40 desvios | 972 | +R$ 3.804 | 1,07 | −R$ 4.503 | −R$ 2.001 | +R$ 5.805 |
| MACD >= 0,50 desvios | 725 | +R$ 1.905 | 1,04 | −R$ 2.901 | −R$ 1.404 | +R$ 3.309 |
| MACD >= 0,60 desvios | 515 | +R$ 4.575 | 1,16 | −R$ 1.743 | +R$ 1.302 | +R$ 3.273 |
| MACD >= 0,75 desvios | 253 | +R$ 1.401 | 1,10 | −R$ 1.410 | −R$ 273 | +R$ 1.674 |
| MACD >= 0,90 desvios | 103 | +R$ 651 | 1,11 | −R$ 1.197 | +R$ 753 | −R$ 102 |
| MACD >= 1,00 desvios | 61 | −R$ 1.263 | 0,67 | −R$ 1.590 | −R$ 1.194 | −R$ 69 |
| MACD >= 0,5 desvios | 725 | +R$ 1.905 | 1,04 | −R$ 2.901 | −R$ 1.404 | +R$ 3.309 |
| MACD < 0,5 desvios | 1.280 | +R$ 8.880 | 1,12 | −R$ 4.632 | +R$ 4.431 | +R$ 4.449 |
| fora da consolidacao 100 | 908 | +R$ 14.556 | 1,29 | −R$ 1.959 | +R$ 9.606 | +R$ 4.950 |
| fora da consolidacao 100 E MACD >= 0,5 | 354 | +R$ 3.858 | 1,19 | −R$ 1.482 | +R$ 1.122 | +R$ 2.736 |
| nao passou da Keltner 2,5 | 1.436 | +R$ 10.692 | 1,13 | −R$ 4.806 | +R$ 3.276 | +R$ 7.416 |
| nao passou da Keltner 2,5 E MACD >= 0,5 | 415 | +R$ 4.035 | 1,18 | −R$ 1.935 | +R$ 744 | +R$ 3.291 |
| consolidacao 100 E Keltner | 606 | +R$ 12.582 | 1,38 | −R$ 1.458 | +R$ 7.668 | +R$ 4.914 |
| consolidacao 100 E Keltner E MACD >= 0,5 | 185 | +R$ 4.365 | 1,46 | −R$ 816 | +R$ 1.560 | +R$ 2.805 |

## Conclusoes

1. **Exigir MACD >= 0,5 desvio piora**: corta 64% dos sinais; mantidos −R$ 2,8 x cortados +R$ 11,2 por trade; carteira +R$ 12.549 -> −R$ 2.373 (alvo 400). Somado aos outros filtros, tambem piora.
2. **Nenhum limiar forma escada**: 0,2-0,3 melhora um pouco, 0,4-0,5 piora, 0,6 melhora. Padrao de acaso.
3. **MACD ja alem da banda (>= 1,0) no trigger e ruim** nos dois periodos (62 sinais, −R$ 35,9 por trade): mesmo achado do preco esticado alem da Keltner.
4. Trocar MACD > 0 por desvios muda pouco.

Reproduzir: `python macd_bb.py && python macd_bb_rel.py`.
