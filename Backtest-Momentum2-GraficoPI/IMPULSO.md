# Impulso antes do recuo e pavios do trigger

Setup EMA 21 + HullRetracao_Azul + MACD, WINFUT PI 20, 132 pregoes (2026-03-06 a 2026-09-14). Entrada seca no fechamento, 6 contratos, R$ 0,50 por contrato. Treino ate 2026-07-01. Tabelas completas e curvas em `impulso.html`.

## 1. Movimento amplo a favor antes do recuo / perto das bandas

Impulso = perna a favor ate o candle antes do recuo. Keltner Nelogica (EMA 21 +- 2,5 x range medio 21): 27% dos sinais passaram da banda nos 10 candles antes do recuo. MACD na Bollinger 1000 / 1,0: 41% tocaram nos 20 candles.

| Gestao | Conjunto | Condicao | Sinais | R$/trade | Resto | Treino (resto) | Teste (resto) | t | Percentil |
|:--|:--|:--|--:|--:|--:|--:|--:|--:|--:|
| CLAUDE.md | todos | Preco tocou a banda de Keltner nos 10 candles antes do recuo | 587 | +R$ 0,9 | +R$ 5,6 | −R$ 1,1 (+R$ 2,8) | +R$ 4,6 (+R$ 11,4) | −0,67 | 26 |
| CLAUDE.md | todos | Preco chegou perto da banda de Keltner (>= 80% do caminho) em 10 | 1.133 | +R$ 5,5 | +R$ 3,1 | +R$ 3,7 (−R$ 0,5) | +R$ 8,9 (+R$ 10,1) | 0,37 | 65 |
| CLAUDE.md | todos | Preco longe da banda (< 60% do caminho) em 10 | 410 | +R$ 2,9 | +R$ 4,7 | −R$ 4,7 (+R$ 3,3) | +R$ 19,3 (+R$ 7,3) | −0,22 | 39 |
| CLAUDE.md | todos | Preco tocou a banda de Keltner nos 20 candles antes do recuo | 729 | +R$ 0,6 | +R$ 6,3 | −R$ 1,0 (+R$ 3,1) | +R$ 3,6 (+R$ 12,7) | −0,84 | 18 |
| CLAUDE.md | todos | 3+ candles alem da banda de Keltner em 10 (esticou e ficou) | 280 | −R$ 2,6 | +R$ 5,4 | −R$ 0,9 (+R$ 2,1) | −R$ 5,2 (+R$ 12,1) | −0,86 | 20 |
| CLAUDE.md | todos | MACD tocou a Bollinger 1000 nos 10 candles antes do recuo | 767 | +R$ 0,3 | +R$ 6,6 | −R$ 5,4 (+R$ 5,6) | +R$ 10,6 (+R$ 8,8) | −0,95 | 18 |
| CLAUDE.md | todos | MACD tocou a Bollinger 1000 nos 20 candles antes do recuo | 879 | +R$ 2,3 | +R$ 5,7 | −R$ 2,2 (+R$ 4,3) | +R$ 10,4 (+R$ 8,7) | −0,53 | 28 |
| CLAUDE.md | todos | MACD longe da banda (< 50%) em 20 | 460 | +R$ 7,4 | +R$ 3,5 | +R$ 9,5 (−R$ 0,3) | +R$ 3,6 (+R$ 11,2) | 0,49 | 65 |
| CLAUDE.md | todos | Impulso amplo em 20: terco superior do treino (>= 720 pts) | 725 | −R$ 0,2 | +R$ 6,7 | −R$ 2,8 (+R$ 4,1) | +R$ 5,0 (+R$ 11,7) | −1,02 | 16 |
| CLAUDE.md | todos | Impulso curto em 20: terco inferior do treino (< 565 pts) | 704 | +R$ 3,1 | +R$ 4,9 | +R$ 1,4 (+R$ 1,9) | +R$ 6,5 (+R$ 10,9) | −0,26 | 38 |
| CLAUDE.md | todos | Impulso amplo em 30 (>= 815 pts) | 726 | +R$ 3,3 | +R$ 4,9 | +R$ 0,0 (+R$ 2,6) | +R$ 9,5 (+R$ 9,5) | −0,24 | 40 |
| CLAUDE.md | todos | Impulso amplo em 20 E tocou Keltner E MACD na Bollinger | 452 | −R$ 2,2 | +R$ 6,1 | −R$ 5,1 (+R$ 3,5) | +R$ 2,9 (+R$ 11,4) | −1,08 | 16 |
| CLAUDE.md | todos | Recuo comecou no pico (0-1 candle depois do pico de 20) | 983 | +R$ 4,0 | +R$ 4,7 | −R$ 0,2 (+R$ 3,3) | +R$ 11,7 (+R$ 7,5) | −0,11 | 46 |
| CLAUDE.md | todos | Recuo profundo: mais de 400 pts desde o pico de 20 (achado na exploracao) | 488 | −R$ 2,0 | +R$ 6,2 | −R$ 2,6 (+R$ 3,0) | −R$ 1,0 (+R$ 12,9) | −1,09 | 15 |
| Stop 100 / alvo 400 | todos | Preco tocou a banda de Keltner nos 10 candles antes do recuo | 587 | −R$ 2,8 | +R$ 8,2 | −R$ 3,0 (+R$ 4,3) | −R$ 2,4 (+R$ 16,0) | −0,94 | 17 |
| Stop 100 / alvo 400 | todos | Preco chegou perto da banda de Keltner (>= 80% do caminho) em 10 | 1.133 | +R$ 2,9 | +R$ 7,7 | +R$ 1,2 (+R$ 3,6) | +R$ 6,4 (+R$ 15,8) | −0,45 | 34 |
| Stop 100 / alvo 400 | todos | Preco longe da banda (< 60% do caminho) em 10 | 410 | +R$ 12,8 | +R$ 3,4 | −R$ 0,4 (+R$ 3,0) | +R$ 41,7 (+R$ 4,1) | 0,69 | 76 |
| Stop 100 / alvo 400 | todos | Preco tocou a banda de Keltner nos 20 candles antes do recuo | 729 | −R$ 2,8 | +R$ 9,3 | −R$ 2,0 (+R$ 4,5) | −R$ 4,4 (+R$ 19,1) | −1,10 | 11 |
| Stop 100 / alvo 400 | todos | 3+ candles alem da banda de Keltner em 10 (esticou e ficou) | 280 | −R$ 7,3 | +R$ 7,1 | −R$ 2,3 (+R$ 3,0) | −R$ 15,1 (+R$ 15,4) | −0,94 | 18 |
| Stop 100 / alvo 400 | todos | MACD tocou a Bollinger 1000 nos 10 candles antes do recuo | 767 | −R$ 1,7 | +R$ 9,1 | −R$ 9,6 (+R$ 8,7) | +R$ 12,4 (+R$ 9,8) | −0,99 | 16 |
| Stop 100 / alvo 400 | todos | MACD tocou a Bollinger 1000 nos 20 candles antes do recuo | 879 | +R$ 1,2 | +R$ 7,9 | −R$ 4,9 (+R$ 7,1) | +R$ 12,3 (+R$ 9,6) | −0,63 | 27 |
| Stop 100 / alvo 400 | todos | MACD longe da banda (< 50%) em 20 | 460 | +R$ 18,7 | +R$ 1,5 | +R$ 20,4 (−R$ 2,5) | +R$ 15,4 (+R$ 9,5) | 1,30 | 90 |
| Stop 100 / alvo 400 | todos | Impulso amplo em 20: terco superior do treino (>= 720 pts) | 725 | −R$ 3,2 | +R$ 9,5 | −R$ 8,5 (+R$ 7,9) | +R$ 7,5 (+R$ 12,5) | −1,14 | 14 |
| Stop 100 / alvo 400 | todos | Impulso curto em 20: terco inferior do treino (< 565 pts) | 704 | +R$ 10,3 | +R$ 2,7 | +R$ 8,9 (−R$ 0,9) | +R$ 13,0 (+R$ 9,7) | 0,67 | 75 |
| Stop 100 / alvo 400 | todos | Impulso amplo em 30 (>= 815 pts) | 726 | +R$ 0,5 | +R$ 7,6 | −R$ 4,8 (+R$ 5,9) | +R$ 10,4 (+R$ 11,0) | −0,64 | 28 |
| Stop 100 / alvo 400 | todos | Impulso amplo em 20 E tocou Keltner E MACD na Bollinger | 452 | −R$ 6,2 | +R$ 8,2 | −R$ 9,6 (+R$ 5,4) | −R$ 0,1 (+R$ 14,0) | −1,14 | 12 |
| Stop 100 / alvo 400 | todos | Recuo comecou no pico (0-1 candle depois do pico de 20) | 983 | +R$ 3,6 | +R$ 6,5 | −R$ 0,9 (+R$ 5,0) | +R$ 12,0 (+R$ 9,7) | −0,28 | 41 |
| Stop 100 / alvo 400 | todos | Recuo profundo: mais de 400 pts desde o pico de 20 (achado na exploracao) | 488 | −R$ 9,1 | +R$ 9,4 | −R$ 5,3 (+R$ 4,5) | −R$ 15,9 (+R$ 19,5) | −1,52 | 7 |

**Largura da banda** (sinais em que o preco passou da banda antes do recuo)

| Gestao | Banda | Janela | Sinais | R$/trade | Resto | Treino (resto) | Teste (resto) | t |
|:--|:--|--:|--:|--:|--:|--:|--:|--:|
| CLAUDE.md | Keltner 1,5 | 10 | 1.731 | +R$ 4,7 | +R$ 2,9 | +R$ 3,3 (−R$ 4,7) | +R$ 7,3 (+R$ 19,3) | 0,22 |
| Stop 100 / alvo 400 | Keltner 1,5 | 10 | 1.731 | +R$ 3,4 | +R$ 12,8 | +R$ 3,0 (−R$ 0,4) | +R$ 4,1 (+R$ 41,7) | −0,69 |
| CLAUDE.md | Keltner 2,0 | 10 | 1.133 | +R$ 5,5 | +R$ 3,1 | +R$ 3,7 (−R$ 0,5) | +R$ 8,9 (+R$ 10,1) | 0,37 |
| Stop 100 / alvo 400 | Keltner 2,0 | 10 | 1.133 | +R$ 2,9 | +R$ 7,7 | +R$ 1,2 (+R$ 3,6) | +R$ 6,4 (+R$ 15,8) | −0,45 |
| CLAUDE.md | Keltner 2,5 | 10 | 587 | +R$ 0,9 | +R$ 5,6 | −R$ 1,1 (+R$ 2,8) | +R$ 4,6 (+R$ 11,4) | −0,67 |
| Stop 100 / alvo 400 | Keltner 2,5 | 10 | 587 | −R$ 2,8 | +R$ 8,2 | −R$ 3,0 (+R$ 4,3) | −R$ 2,4 (+R$ 16,0) | −0,94 |
| CLAUDE.md | Keltner 3,0 | 10 | 255 | −R$ 2,1 | +R$ 5,2 | −R$ 3,7 (+R$ 2,4) | +R$ 0,9 (+R$ 10,7) | −0,75 |
| Stop 100 / alvo 400 | Keltner 3,0 | 10 | 255 | −R$ 3,0 | +R$ 6,3 | +R$ 0,7 (+R$ 2,5) | −R$ 9,5 (+R$ 13,8) | −0,58 |
| CLAUDE.md | Keltner 3,5 | 10 | 99 | −R$ 11,5 | +R$ 5,1 | −R$ 13,7 (+R$ 2,5) | −R$ 6,8 (+R$ 10,2) | −1,18 |
| Stop 100 / alvo 400 | Keltner 3,5 | 10 | 99 | −R$ 22,4 | +R$ 6,5 | −R$ 24,5 (+R$ 3,7) | −R$ 18,0 (+R$ 12,1) | −1,25 |
| CLAUDE.md | Keltner 1,5 | 20 | 1.811 | +R$ 3,9 | +R$ 6,8 | +R$ 2,1 (−R$ 0,3) | +R$ 7,3 (+R$ 21,9) | −0,32 |
| Stop 100 / alvo 400 | Keltner 1,5 | 20 | 1.811 | +R$ 3,2 | +R$ 15,9 | +R$ 2,2 (+R$ 2,9) | +R$ 5,2 (+R$ 43,4) | −0,85 |
| CLAUDE.md | Keltner 2,0 | 20 | 1.285 | +R$ 6,0 | +R$ 1,9 | +R$ 3,9 (−R$ 1,5) | +R$ 10,1 (+R$ 8,5) | 0,61 |
| Stop 100 / alvo 400 | Keltner 2,0 | 20 | 1.285 | +R$ 3,9 | +R$ 7,1 | +R$ 2,2 (+R$ 2,5) | +R$ 7,3 (+R$ 16,0) | −0,29 |
| CLAUDE.md | Keltner 2,5 | 20 | 729 | +R$ 0,6 | +R$ 6,3 | −R$ 1,0 (+R$ 3,1) | +R$ 3,6 (+R$ 12,7) | −0,84 |
| Stop 100 / alvo 400 | Keltner 2,5 | 20 | 729 | −R$ 2,8 | +R$ 9,3 | −R$ 2,0 (+R$ 4,5) | −R$ 4,4 (+R$ 19,1) | −1,10 |
| CLAUDE.md | Keltner 3,0 | 20 | 354 | −R$ 3,3 | +R$ 5,9 | −R$ 2,5 (+R$ 2,5) | −R$ 4,8 (+R$ 12,7) | −1,09 |
| Stop 100 / alvo 400 | Keltner 3,0 | 20 | 354 | −R$ 4,4 | +R$ 7,1 | +R$ 3,0 (+R$ 2,2) | −R$ 16,5 (+R$ 17,0) | −0,82 |
| CLAUDE.md | Keltner 3,5 | 20 | 146 | −R$ 10,4 | +R$ 5,4 | −R$ 11,6 (+R$ 2,7) | −R$ 8,0 (+R$ 10,7) | −1,32 |
| Stop 100 / alvo 400 | Keltner 3,5 | 20 | 146 | −R$ 21,9 | +R$ 7,2 | −R$ 12,8 (+R$ 3,5) | −R$ 40,5 (+R$ 14,4) | −1,50 |
| CLAUDE.md | Desvio-padrao 1,5 | 10 | 1.725 | +R$ 6,6 | −R$ 5,0 | +R$ 4,2 (−R$ 8,0) | +R$ 11,1 (+R$ 1,7) | 1,44 |
| Stop 100 / alvo 400 | Desvio-padrao 1,5 | 10 | 1.725 | +R$ 6,1 | +R$ 1,3 | +R$ 4,2 (−R$ 5,1) | +R$ 9,7 (+R$ 15,9) | 0,36 |
| CLAUDE.md | Desvio-padrao 2,0 | 10 | 926 | +R$ 5,2 | +R$ 3,7 | +R$ 2,1 (+R$ 1,5) | +R$ 10,7 (+R$ 8,4) | 0,22 |
| Stop 100 / alvo 400 | Desvio-padrao 2,0 | 10 | 926 | +R$ 4,5 | +R$ 5,7 | +R$ 4,3 (+R$ 0,9) | +R$ 5,0 (+R$ 15,8) | −0,11 |
| CLAUDE.md | Desvio-padrao 2,5 | 10 | 247 | +R$ 10,6 | +R$ 3,5 | +R$ 11,4 (+R$ 0,5) | +R$ 9,1 (+R$ 9,5) | 0,69 |
| Stop 100 / alvo 400 | Desvio-padrao 2,5 | 10 | 247 | +R$ 16,4 | +R$ 3,7 | +R$ 25,9 (−R$ 0,6) | −R$ 0,3 (+R$ 12,4) | 0,75 |
| CLAUDE.md | Desvio-padrao 3,0 | 10 | 39 | −R$ 3,0 | +R$ 4,5 | −R$ 30,7 (+R$ 2,3) | +R$ 52,4 (+R$ 8,7) | −0,31 |
| Stop 100 / alvo 400 | Desvio-padrao 3,0 | 10 | 39 | +R$ 3,2 | +R$ 5,2 | −R$ 26,1 (+R$ 2,9) | +R$ 61,6 (+R$ 9,9) | −0,05 |
| CLAUDE.md | Desvio-padrao 1,5 | 20 | 1.859 | +R$ 5,8 | −R$ 5,1 | +R$ 3,6 (−R$ 9,5) | +R$ 9,9 (+R$ 6,0) | 1,16 |
| Stop 100 / alvo 400 | Desvio-padrao 1,5 | 20 | 1.859 | +R$ 6,3 | −R$ 2,1 | +R$ 4,2 (−R$ 8,9) | +R$ 10,3 (+R$ 15,0) | 0,55 |
| CLAUDE.md | Desvio-padrao 2,0 | 20 | 1.202 | +R$ 4,3 | +R$ 4,4 | +R$ 2,0 (+R$ 1,5) | +R$ 8,5 (+R$ 10,9) | −0,02 |
| Stop 100 / alvo 400 | Desvio-padrao 2,0 | 20 | 1.202 | +R$ 5,3 | +R$ 5,1 | +R$ 4,8 (−R$ 0,6) | +R$ 6,3 (+R$ 17,4) | 0,02 |
| CLAUDE.md | Desvio-padrao 2,5 | 20 | 387 | +R$ 6,9 | +R$ 3,8 | +R$ 8,5 (+R$ 0,3) | +R$ 4,0 (+R$ 10,7) | 0,38 |
| Stop 100 / alvo 400 | Desvio-padrao 2,5 | 20 | 387 | +R$ 7,9 | +R$ 4,6 | +R$ 11,9 (+R$ 0,3) | +R$ 0,5 (+R$ 13,2) | 0,23 |
| CLAUDE.md | Desvio-padrao 3,0 | 20 | 65 | +R$ 9,9 | +R$ 4,2 | −R$ 13,7 (+R$ 2,2) | +R$ 63,0 (+R$ 7,9) | 0,30 |
| Stop 100 / alvo 400 | Desvio-padrao 3,0 | 20 | 65 | +R$ 8,1 | +R$ 5,1 | −R$ 27,0 (+R$ 3,3) | +R$ 87,0 (+R$ 8,6) | 0,10 |

**Carteira**

_Stop 100 / alvo 400 sem parcial_

| Filtro | Trades | Liquido | Fator | Rebaix. | Treino | Teste | Atravessar 5 |
|:--|--:|--:|--:|--:|--:|--:|--:|
| sem filtro | 1.947 | +R$ 11.199 | 1,06 | −R$ 7.089 | +R$ 2.121 | +R$ 9.078 | +R$ 10.605 |
| tocou Keltner em 10 | 567 | −R$ 3.381 | 0,94 | −R$ 7.827 | −R$ 1.473 | −R$ 1.908 | −R$ 3.381 |
| nao tocou Keltner em 10 | 1.412 | +R$ 15.444 | 1,11 | −R$ 4.605 | +R$ 4.488 | +R$ 10.956 | +R$ 14.727 |
| MACD tocou a Bollinger em 20 | 823 | −R$ 1.029 | 0,99 | −R$ 9.162 | −R$ 3.642 | +R$ 2.613 | −R$ 1.629 |
| MACD nao tocou a Bollinger em 20 | 1.094 | +R$ 11.718 | 1,11 | −R$ 5.337 | +R$ 6.237 | +R$ 5.481 | +R$ 11.601 |
| impulso amplo em 20 (terco superior) | 704 | −R$ 1.512 | 0,98 | −R$ 7.011 | −R$ 2.970 | +R$ 1.458 | −R$ 1.512 |
| impulso nao amplo em 20 | 1.292 | +R$ 15.684 | 1,13 | −R$ 3.474 | +R$ 6.909 | +R$ 8.775 | +R$ 14.967 |
| evitar recuo > 400 pts (post hoc) | 1.511 | +R$ 14.427 | 1,10 | −R$ 5.742 | +R$ 3.906 | +R$ 10.521 | +R$ 14.310 |
| fora da consolidacao 100 (estudo anterior) | 894 | +R$ 21.798 | 1,26 | −R$ 3.354 | +R$ 12.138 | +R$ 9.660 | +R$ 21.921 |
| fora da consolidacao 100 E tocou Keltner em 10 | 312 | +R$ 2.904 | 1,10 | −R$ 4.689 | +R$ 2.874 | +R$ 30 | +R$ 2.904 |
| fora da consolidacao 100 E nao tocou Keltner em 10 | 598 | +R$ 18.726 | 1,34 | −R$ 2.229 | +R$ 9.111 | +R$ 9.615 | +R$ 18.726 |

_Gestao do CLAUDE.md (stop 100, parcial +100, alvo 300)_

| Filtro | Trades | Liquido | Fator | Rebaix. | Treino | Teste | Atravessar 5 |
|:--|--:|--:|--:|--:|--:|--:|--:|
| sem filtro | 2.037 | +R$ 9.849 | 1,08 | −R$ 5.868 | +R$ 1.581 | +R$ 8.268 | +R$ 4.584 |
| tocou Keltner em 10 | 576 | +R$ 432 | 1,01 | −R$ 3.534 | −R$ 525 | +R$ 957 | −R$ 1.245 |
| nao tocou Keltner em 10 | 1.478 | +R$ 9.486 | 1,11 | −R$ 4.806 | +R$ 2.070 | +R$ 7.416 | +R$ 5.772 |
| MACD tocou a Bollinger em 20 | 844 | +R$ 1.308 | 1,03 | −R$ 4.044 | −R$ 2.109 | +R$ 3.417 | −R$ 366 |
| MACD nao tocou a Bollinger em 20 | 1.152 | +R$ 9.264 | 1,14 | −R$ 4.533 | +R$ 4.545 | +R$ 4.719 | +R$ 5.913 |
| impulso amplo em 20 (terco superior) | 711 | +R$ 147 | 1,00 | −R$ 3.300 | −R$ 1.059 | +R$ 1.206 | −R$ 2.253 |
| impulso nao amplo em 20 | 1.351 | +R$ 10.227 | 1,13 | −R$ 3.615 | +R$ 3.306 | +R$ 6.921 | +R$ 7.236 |
| evitar recuo > 400 pts (post hoc) | 1.572 | +R$ 10.764 | 1,12 | −R$ 5.238 | +R$ 2.457 | +R$ 8.307 | +R$ 6.576 |
| fora da consolidacao 100 (estudo anterior) | 925 | +R$ 14.625 | 1,28 | −R$ 1.959 | +R$ 9.675 | +R$ 4.950 | +R$ 12.114 |
| fora da consolidacao 100 E tocou Keltner em 10 | 316 | +R$ 2.292 | 1,12 | −R$ 2.046 | +R$ 2.265 | +R$ 27 | +R$ 1.095 |
| fora da consolidacao 100 E nao tocou Keltner em 10 | 619 | +R$ 11.943 | 1,35 | −R$ 1.458 | +R$ 7.029 | +R$ 4.914 | +R$ 10.503 |

Busca automatica: 168 cortes; melhor t no treino 1,70 (placebo p99 1,67) com alvo 400, 1,45 (p99 1,84) no CLAUDE.md. Os melhores cortes: MACD na Bollinger: posicao maxima 30 < 1.13; MACD na Bollinger: posicao maxima 30 < 0.86; MACD na Bollinger: posicao maxima 10 < 0.95; Pico do MACD / ATR (30) < 0.44.

## 2. Pavios do trigger com toque na EMA 21

Universo sem o corte de pavio: 2.442 sinais; setup atual (fechamento ate 10%): 2.141; pavio do fechamento zero: 746.

| Padrao | Universo | Antes | Gestao | Sinais | R$/trade | Resto | Treino (resto) | Teste (resto) | Percentil |
|:--|:--|:--|:--|--:|--:|--:|--:|--:|--:|
| Pavio do fechamento ate 10% do corpo (corte do HullRetracao_Azul) | sem corte de pavio | melhor que acima de 10%: +7,9 contra +4,4 pts | CLAUDE.md | 2.141 | +R$ 4,3 | −R$ 3,2 | +R$ 1,7 (−R$ 7,3) | +R$ 9,5 (+R$ 3,0) | 80 |
| Pavio do fechamento ate 10% do corpo (corte do HullRetracao_Azul) | sem corte de pavio | melhor que acima de 10%: +7,9 contra +4,4 pts | Stop 100 / alvo 400 | 2.141 | +R$ 5,2 | −R$ 16,6 | +R$ 2,3 (−R$ 34,0) | +R$ 10,8 (+R$ 10,1) | 94 |
| Pavio do fechamento ate 10% do corpo (corte do HullRetracao_Azul) | sem corte de pavio | melhor que acima de 10%: +7,9 contra +4,4 pts | CLAUDE.md, stop no extremo | 2.141 | +R$ 2,5 | −R$ 6,3 | −R$ 0,5 (−R$ 15,9) | +R$ 8,5 (+R$ 8,4) | 81 |
| Pavio do fechamento = 0 (fecha na maxima da compra / minima da venda) | sem corte de pavio | nao medido separado | CLAUDE.md | 746 | +R$ 8,1 | +R$ 1,4 | +R$ 6,5 (−R$ 2,1) | +R$ 11,7 (+R$ 7,4) | 84 |
| Pavio do fechamento = 0 (fecha na maxima da compra / minima da venda) | sem corte de pavio | nao medido separado | Stop 100 / alvo 400 | 746 | +R$ 16,1 | −R$ 3,5 | +R$ 14,4 (−R$ 9,5) | +R$ 20,1 (+R$ 7,2) | 97 |
| Pavio do fechamento = 0 (fecha na maxima da compra / minima da venda) | sem corte de pavio | nao medido separado | CLAUDE.md, stop no extremo | 746 | +R$ 7,3 | −R$ 1,1 | +R$ 5,6 (−R$ 6,0) | +R$ 11,0 (+R$ 7,6) | 87 |
| Pavio do fechamento = 0, dentro do setup (contra 5-10 pts) | setup (fechamento ate 10%) | nao medido | CLAUDE.md | 746 | +R$ 8,1 | +R$ 2,3 | +R$ 6,5 (−R$ 1,0) | +R$ 11,7 (+R$ 8,4) | 80 |
| Pavio do fechamento = 0, dentro do setup (contra 5-10 pts) | setup (fechamento ate 10%) | nao medido | Stop 100 / alvo 400 | 746 | +R$ 16,1 | −R$ 0,7 | +R$ 14,4 (−R$ 4,6) | +R$ 20,1 (+R$ 6,5) | 94 |
| Pavio do fechamento = 0, dentro do setup (contra 5-10 pts) | setup (fechamento ate 10%) | nao medido | CLAUDE.md, stop no extremo | 746 | +R$ 7,3 | −R$ 0,0 | +R$ 5,6 (−R$ 4,1) | +R$ 11,0 (+R$ 7,4) | 82 |
| Pavio da abertura 25-90% (PavioContra_Magenta) | setup (fechamento ate 10%) | anti-filtro: percentil 2 a 8 do sorteio | CLAUDE.md | 1.424 | +R$ 3,2 | +R$ 6,5 | −R$ 1,3 (+R$ 7,4) | +R$ 11,6 (+R$ 4,7) | 31 |
| Pavio da abertura 25-90% (PavioContra_Magenta) | setup (fechamento ate 10%) | anti-filtro: percentil 2 a 8 do sorteio | Stop 100 / alvo 400 | 1.424 | +R$ 0,9 | +R$ 13,7 | −R$ 4,2 (+R$ 14,3) | +R$ 10,1 (+R$ 12,3) | 12 |
| Pavio da abertura 25-90% (PavioContra_Magenta) | setup (fechamento ate 10%) | anti-filtro: percentil 2 a 8 do sorteio | CLAUDE.md, stop no extremo | 1.424 | +R$ 0,0 | +R$ 7,5 | −R$ 4,5 (+R$ 6,8) | +R$ 8,3 (+R$ 9,1) | 17 |
| Pavio da abertura 5-25% (PavioFavor_Verde) | setup (fechamento ate 10%) | com Hull a favor nao separa (percentil 58) | CLAUDE.md | 652 | +R$ 3,4 | +R$ 4,7 | +R$ 3,4 (+R$ 1,0) | +R$ 3,6 (+R$ 11,7) | 43 |
| Pavio da abertura 5-25% (PavioFavor_Verde) | setup (fechamento ate 10%) | com Hull a favor nao separa (percentil 58) | Stop 100 / alvo 400 | 652 | +R$ 9,5 | +R$ 3,3 | +R$ 8,2 (−R$ 0,4) | +R$ 12,5 (+R$ 10,1) | 70 |
| Pavio da abertura 5-25% (PavioFavor_Verde) | setup (fechamento ate 10%) | com Hull a favor nao separa (percentil 58) | CLAUDE.md, stop no extremo | 652 | +R$ 4,6 | +R$ 1,6 | +R$ 3,1 (−R$ 2,2) | +R$ 7,9 (+R$ 8,8) | 64 |
| Pavio da abertura ate 25% (quanto menor, melhor) | setup (fechamento ate 10%) | pequenos melhores: 0-10% de +6,5 a +8,6 pts; 65-90% -2,3 | CLAUDE.md | 691 | +R$ 2,9 | +R$ 5,0 | +R$ 3,5 (+R$ 0,8) | +R$ 1,5 (+R$ 12,8) | 36 |
| Pavio da abertura ate 25% (quanto menor, melhor) | setup (fechamento ate 10%) | pequenos melhores: 0-10% de +6,5 a +8,6 pts; 65-90% -2,3 | Stop 100 / alvo 400 | 691 | +R$ 9,0 | +R$ 3,4 | +R$ 9,6 (−R$ 1,3) | +R$ 7,7 (+R$ 12,1) | 69 |
| Pavio da abertura ate 25% (quanto menor, melhor) | setup (fechamento ate 10%) | pequenos melhores: 0-10% de +6,5 a +8,6 pts; 65-90% -2,3 | CLAUDE.md, stop no extremo | 691 | +R$ 4,0 | +R$ 1,8 | +R$ 3,3 (−R$ 2,4) | +R$ 5,6 (+R$ 9,8) | 62 |
| Pavio da abertura acima de 90% (martelo) | setup (fechamento ate 10%) | faixa 90-100% boa: +5,8 pts | CLAUDE.md | 148 | +R$ 26,2 | +R$ 2,7 | +R$ 24,2 (+R$ 0,1) | +R$ 29,9 (+R$ 7,9) | 96 |
| Pavio da abertura acima de 90% (martelo) | setup (fechamento ate 10%) | faixa 90-100% boa: +5,8 pts | Stop 100 / alvo 400 | 148 | +R$ 16,5 | +R$ 4,3 | +R$ 3,2 (+R$ 2,3) | +R$ 41,7 (+R$ 8,4) | 71 |
| Pavio da abertura acima de 90% (martelo) | setup (fechamento ate 10%) | faixa 90-100% boa: +5,8 pts | CLAUDE.md, stop no extremo | 148 | +R$ 26,9 | +R$ 0,7 | +R$ 20,3 (−R$ 2,1) | +R$ 39,6 (+R$ 6,2) | 96 |

Correlacao de posto pavio da abertura (ate 90) x resultado, no setup: alvo 400 −0,025 (p 0,27), CLAUDE.md −0,015 (p 0,52).

**Pavio do fechamento (sem corte)**, R$/trade

| Pavio | Sinais | Alvo 400 | treino / teste | CLAUDE.md | treino / teste |
|:--|--:|--:|--:|--:|--:|
| 0 | 746 | +R$ 16,1 | +R$ 14,4 / +R$ 20,1 | +R$ 8,1 | +R$ 6,5 / +R$ 11,7 |
| 5-10 | 1.395 | −R$ 0,7 | −R$ 4,6 / +R$ 6,5 | +R$ 2,3 | −R$ 1,0 / +R$ 8,4 |
| 15-25 | 242 | −R$ 21,8 | −R$ 40,3 / +R$ 7,2 | −R$ 5,5 | −R$ 7,9 / −R$ 1,7 |
| 30-45 | 31 | +R$ 82,2 | +R$ 39,4 / +R$ 134,1 | +R$ 49,3 | +R$ 14,6 / +R$ 91,3 |
| 50-65 | 7 | −R$ 123,0 | −R$ 123,0 / −R$ 123,0 | −R$ 88,7 | −R$ 123,0 / −R$ 63,0 |
| 70-90 | 8 | −R$ 123,0 | −R$ 123,0 / −R$ 123,0 | −R$ 93,0 | −R$ 75,0 / −R$ 123,0 |
| 95+ | 13 | −R$ 30,7 | +R$ 10,3 / −R$ 123,0 | +R$ 15,5 | +R$ 37,0 / −R$ 33,0 |

**Pavio da abertura (setup atual)**, R$/trade

| Pavio | Sinais | Alvo 400 | treino / teste | CLAUDE.md | treino / teste |
|:--|--:|--:|--:|--:|--:|
| 0 | 39 | +R$ 0,1 | +R$ 32,6 / −R$ 73,0 | −R$ 6,1 | +R$ 5,9 / −R$ 33,0 |
| 5-10 | 259 | +R$ 24,8 | +R$ 25,0 / +R$ 24,2 | +R$ 4,4 | +R$ 3,5 / +R$ 6,6 |
| 15-25 | 393 | −R$ 0,6 | −R$ 3,4 / +R$ 5,6 | +R$ 2,8 | +R$ 3,3 / +R$ 1,8 |
| 30-45 | 484 | +R$ 7,4 | +R$ 8,5 / +R$ 5,4 | +R$ 4,4 | +R$ 3,5 / +R$ 6,1 |
| 50-65 | 398 | −R$ 1,2 | −R$ 3,0 / +R$ 1,9 | +R$ 5,1 | +R$ 0,8 / +R$ 12,5 |
| 70-90 | 420 | −R$ 1,6 | −R$ 12,4 / +R$ 20,1 | −R$ 1,9 | −R$ 10,3 / +R$ 15,0 |
| 95+ | 148 | +R$ 16,5 | +R$ 3,2 / +R$ 41,7 | +R$ 26,2 | +R$ 24,2 / +R$ 29,9 |

**Pavio do fechamento zero x 5-10, mes a mes (R$/trade, alvo 400)**

| Mes | 0 | 5-10 | acima de 10 |
|:--|--:|--:|--:|
| 03/2026 | +R$ 18,4 | −R$ 8,4 | −R$ 48,0 |
| 04/2026 | +R$ 10,0 | +R$ 3,3 | −R$ 10,7 |
| 05/2026 | −R$ 9,9 | +R$ 7,3 | −R$ 72,8 |
| 06/2026 | +R$ 39,3 | −R$ 17,8 | −R$ 5,7 |
| 07/2026 | +R$ 40,1 | −R$ 31,5 | +R$ 13,8 |
| 08/2026 | −R$ 9,4 | +R$ 44,3 | +R$ 34,1 |
| 09/2026 | +R$ 41,2 | +R$ 8,5 | −R$ 34,1 |

**Carteira**

_Stop 100 / alvo 400 sem parcial_

| Filtro | Trades | Liquido | Fator | Rebaix. | Treino | Teste | Slippage 5 | Slippage 10 |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|
| sem corte de pavio (universo) | 2.209 | +R$ 7.533 | 1,03 | −R$ 10.071 | −R$ 2.655 | +R$ 10.188 | −R$ 5.721 | −R$ 18.975 |
| setup atual: pavio do fechamento ate 10% | 1.947 | +R$ 11.199 | 1,06 | −R$ 7.089 | +R$ 2.121 | +R$ 9.078 | −R$ 483 | −R$ 12.165 |
| pavio do fechamento = 0 | 720 | +R$ 9.840 | 1,15 | −R$ 3.501 | +R$ 5.940 | +R$ 3.900 | +R$ 5.520 | +R$ 1.200 |
| pavio do fechamento 5-10 | 1.312 | +R$ 864 | 1,01 | −R$ 10.446 | −R$ 3.750 | +R$ 4.614 | −R$ 7.008 | −R$ 14.880 |
| pavio do fechamento acima de 10 | 300 | −R$ 5.340 | 0,82 | −R$ 7.806 | −R$ 6.543 | +R$ 1.203 | −R$ 7.140 | −R$ 8.940 |
| setup sem a faixa magenta (abertura fora de 25-90%) | 690 | +R$ 9.570 | 1,15 | −R$ 5.082 | +R$ 7.452 | +R$ 2.118 | +R$ 5.430 | +R$ 1.290 |
| pavio do fechamento = 0 E picado | 217 | +R$ 12.429 | 1,67 | −R$ 1.722 | +R$ 8.670 | +R$ 3.759 | +R$ 11.127 | +R$ 9.825 |
| pavio do fechamento = 0 E fora da consolidacao 100 | 340 | +R$ 9.780 | 1,31 | −R$ 1.689 | +R$ 6.126 | +R$ 3.654 | +R$ 7.740 | +R$ 5.700 |
| setup E fora da consolidacao 100 | 894 | +R$ 21.798 | 1,26 | −R$ 3.354 | +R$ 12.138 | +R$ 9.660 | +R$ 16.434 | +R$ 11.070 |

_Gestao do CLAUDE.md (stop 100, parcial +100, alvo 300)_

| Filtro | Trades | Liquido | Fator | Rebaix. | Treino | Teste | Slippage 5 | Slippage 10 |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|
| sem corte de pavio (universo) | 2.322 | +R$ 8.934 | 1,07 | −R$ 7.287 | +R$ 1.014 | +R$ 7.920 | −R$ 4.998 | −R$ 18.930 |
| setup atual: pavio do fechamento ate 10% | 2.037 | +R$ 9.849 | 1,08 | −R$ 5.868 | +R$ 1.581 | +R$ 8.268 | −R$ 2.373 | −R$ 14.595 |
| pavio do fechamento = 0 | 733 | +R$ 5.241 | 1,12 | −R$ 2.619 | +R$ 2.793 | +R$ 2.448 | +R$ 843 | −R$ 3.555 |
| pavio do fechamento 5-10 | 1.349 | +R$ 4.833 | 1,06 | −R$ 5.688 | −R$ 333 | +R$ 5.166 | −R$ 3.261 | −R$ 11.355 |
| pavio do fechamento acima de 10 | 301 | −R$ 963 | 0,94 | −R$ 2.475 | −R$ 1.326 | +R$ 363 | −R$ 2.769 | −R$ 4.575 |
| setup sem a faixa magenta (abertura fora de 25-90%) | 702 | +R$ 4.374 | 1,10 | −R$ 3.288 | +R$ 3.576 | +R$ 798 | +R$ 162 | −R$ 4.050 |
| pavio do fechamento = 0 E picado | 220 | +R$ 5.340 | 1,42 | −R$ 891 | +R$ 3.381 | +R$ 1.959 | +R$ 4.020 | +R$ 2.700 |
| pavio do fechamento = 0 E fora da consolidacao 100 | 342 | +R$ 6.054 | 1,31 | −R$ 1.569 | +R$ 4.323 | +R$ 1.731 | +R$ 4.002 | +R$ 1.950 |
| setup E fora da consolidacao 100 | 925 | +R$ 14.625 | 1,28 | −R$ 1.959 | +R$ 9.675 | +R$ 4.950 | +R$ 9.075 | +R$ 3.525 |

## Conclusoes

1. **Movimento amplo a favor / alem das bandas nao melhora o acerto; os mais esticados foram piores.** Preco alem da Keltner Nelogica 2,5 nos 10 candles antes do recuo: pior no treino e no teste, nas duas gestoes, e piorando com banda 3,0 e 3,5 (1,5 e 2,0 nao separam). Impulso no terco superior e MACD na Bollinger tambem abaixo do resto. t de -0,5 a -1,5: candidato a filtro "evitar esticado", nao regra.
2. **O corte de pavio do fechamento do HullRetracao_Azul continua valendo**: acima de 10 pts perde em carteira nas duas gestoes.
3. **Novo: pavio do fechamento zero concentra a vantagem.** Melhor que 5-10 no treino e no teste, em T1 e T2, 5 de 7 meses. Carteira alvo 400: +R$ 9.840 (rebaix. −R$ 3.501) contra +R$ 11.199 (rebaix. −R$ 7.089); com 5 pts de slippage +R$ 5.520 x −R$ 483. Separacao 0 x 5-10 feita depois de ver os dados: candidato forte, `PavioFechMaxPct(0)`.
4. **Pavio da abertura: nao filtrar.** Magenta ainda pior no treino, mas nao no teste; verde nao separa; "menor e melhor" nao aparece (correlacao ~0). Martelo (acima de 90 pts) bom nos dois periodos na gestao do CLAUDE.md, com poucos sinais: observar.

Reproduzir: `python impulso.py && python impulso_rel.py`.
