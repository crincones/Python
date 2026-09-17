# EMA 21 + Hull + MACD no grafico PI: resultados

WINFUT, grafico de 20 PI, 50.611 candles, 132 pregoes (2026-03-06 a 2026-09-14). 6 contratos de mini indice, custo R$ 0,50 por contrato ida e volta. Treino ate 2026-07-01, teste depois. Graficos, filtros, grade de gestao, Monte Carlo e trade a trade (KLineCharts) em `relatorio.html`.

## Regras programadas

- **Trigger**: `HullRetracao_Azul.ntsl` como esta na pasta (Hull 50 a favor, 2-3 candles contra no mesmo pregao, pavio do fechamento ate 10% do corpo).
- **Virada tocando a EMA 21**: algum candle da virada (contra + trigger) com minima <= EMA <= maxima, tolerancia 15 pts.
- **MACD 9/14/9** acima de zero na compra, abaixo na venda.
- **T1/T2** pela Hull em relacao ao candle do trigger (compra: Hull acima da maxima = T2). Bate com os 7 rotulos de 14/09.
- Uma posicao por vez, zera no fim do pregao.

| Calibracao 14/09 | Lado | Print | Motor | Obs. |
|:--|:--|:-:|:-:|:--|
| 09:05 | venda | T2 | T2 | Hull abaixo do candle |
| 09:06 | venda | T2 | T2 | Hull abaixo do candle |
| 09:38 | venda | T1 | T1 | Hull corta o candle |
| 09:53 | compra | T1 | T1 | quase toque: EMA 12 pts abaixo da minima |
| 10:25 | venda | T1 | T1 | Hull corta o candle |
| 10:27 | venda | T2 | T2 | Hull 16 pts abaixo da minima |
| 10:43 | compra | T1 | T1 | Hull corta o candle |

## Resultado base (gestao do CLAUDE.md: stop 100, parcial 50% em +100 com stop na media, alvo +300)

| Entrada | Bloco | Trades | Liquido | Fator | Winrate | Rebaixamento |
|:--|:--|--:|--:|--:|--:|--:|
| Seca no fechamento | todos | 2.037 | +R$ 9.849 | 1,08 | 27,1% | −R$ 5.868 |
|  | T1 | 1.236 | +R$ 4.092 | 1,05 | 27,2% | −R$ 5.238 |
|  | T2 | 819 | +R$ 6.183 | 1,13 | 27,1% | −R$ 2.700 |
| Limitada no meio do corpo | todos | 1.591 | −R$ 9.423 | 0,91 | 26,7% | −R$ 12.189 |
|  | T1 | 957 | −R$ 6.621 | 0,90 | 26,6% | −R$ 8.832 |
|  | T2 | 648 | −R$ 2.604 | 0,94 | 26,9% | −R$ 4.530 |
| Stop no extremo do candle | todos | 2.024 | +R$ 4.326 | 1,03 | 30,9% | −R$ 6.972 |
|  | T1 | 1.225 | +R$ 933 | 1,01 | 31,4% | −R$ 7.113 |
|  | T2 | 819 | +R$ 4.527 | 1,08 | 30,4% | −R$ 2.487 |

## Filtros (entrada seca, R$ por sinal: base / treino / teste)

Media geral por sinal: +R$ 4,34. Faixas com pelo menos 30 sinais no treino.

| Grupo | Filtro | Faixa | Sinais | R$/sinal | Treino | Teste |
|:--|:--|:--|--:|--:|--:|--:|
| Classificacao | T1 x T2 | T1 | 1.287 | +R$ 2,9 | −R$ 2,2 | +R$ 13,1 |
| Classificacao | T1 x T2 | T2 | 854 | +R$ 6,6 | +R$ 7,8 | +R$ 4,3 |
| Classificacao | Compra x venda | compra | 1.084 | +R$ 9,2 | +R$ 3,0 | +R$ 21,1 |
| Classificacao | Compra x venda | venda | 1.057 | −R$ 0,6 | +R$ 0,4 | −R$ 2,7 |
| Classificacao | Candles contra no recuo | 2 | 1.480 | +R$ 6,8 | +R$ 4,3 | +R$ 11,7 |
| Classificacao | Candles contra no recuo | 3 | 661 | −R$ 1,2 | −R$ 4,1 | +R$ 4,5 |
| Tendencia geral | Preco x abertura do dia (a favor do trade) | a favor | 1.183 | +R$ 1,0 | −R$ 1,1 | +R$ 5,0 |
| Tendencia geral | Preco x abertura do dia (a favor do trade) | contra | 958 | +R$ 8,5 | +R$ 5,2 | +R$ 15,2 |
| Tendencia geral | Preco x EMA 200 (a favor do trade) | a favor | 1.298 | +R$ 3,8 | +R$ 0,3 | +R$ 10,8 |
| Tendencia geral | Preco x EMA 200 (a favor do trade) | contra | 843 | +R$ 5,1 | +R$ 3,9 | +R$ 7,5 |
| Tendencia geral | Inclinacao da EMA 21 (5 candles, pts, a favor) | -inf a 20.61 | 405 | +R$ 5,3 | +R$ 7,6 | −R$ 0,0 |
| Tendencia geral | Inclinacao da EMA 21 (5 candles, pts, a favor) | 20.61 a 39.09 | 427 | +R$ 0,9 | −R$ 3,0 | +R$ 8,8 |
| Tendencia geral | Inclinacao da EMA 21 (5 candles, pts, a favor) | 39.09 a 56.28 | 451 | +R$ 4,7 | +R$ 1,2 | +R$ 10,6 |
| Tendencia geral | Inclinacao da EMA 21 (5 candles, pts, a favor) | 56.28 a 74.58 | 430 | +R$ 3,1 | +R$ 2,5 | +R$ 4,4 |
| Tendencia geral | Inclinacao da EMA 21 (5 candles, pts, a favor) | 74.58 a +inf | 428 | +R$ 7,7 | +R$ 0,4 | +R$ 22,0 |
| Tendencia geral | MACD alem da Bollinger 1000 no sentido do trade | dentro | 2.079 | +R$ 5,1 | +R$ 2,7 | +R$ 9,9 |
| Tendencia geral | MACD alem da Bollinger 1000 no sentido do trade | fora da banda | 62 | −R$ 22,4 | −R$ 33,8 | −R$ 3,0 |
| Tendencia geral | MACD acima do sinal (a favor) | nao | 1.283 | +R$ 4,6 | +R$ 1,9 | +R$ 9,6 |
| Tendencia geral | MACD acima do sinal (a favor) | sim | 858 | +R$ 4,0 | +R$ 1,5 | +R$ 9,3 |
| Segundos recuos | Toques anteriores na EMA desde que o MACD virou | 0 | 625 | +R$ 3,0 | +R$ 1,0 | +R$ 7,0 |
| Segundos recuos | Toques anteriores na EMA desde que o MACD virou | 1 | 737 | +R$ 1,9 | −R$ 4,8 | +R$ 14,1 |
| Segundos recuos | Toques anteriores na EMA desde que o MACD virou | 2 | 371 | −R$ 4,3 | −R$ 8,0 | +R$ 2,5 |
| Segundos recuos | Toques anteriores na EMA desde que o MACD virou | 3+ | 408 | +R$ 18,8 | +R$ 22,4 | +R$ 10,9 |
| Fraqueza de continuacao | Impulso anterior fez novo extremo? | fez novo extremo | 1.348 | +R$ 3,2 | +R$ 1,6 | +R$ 6,3 |
| Fraqueza de continuacao | Impulso anterior fez novo extremo? | nao fez (fraco) | 793 | +R$ 6,2 | +R$ 1,9 | +R$ 15,0 |
| Fraqueza de continuacao | Tamanho do impulso antes do recuo (pts) | -inf a 305 | 412 | +R$ 5,2 | +R$ 4,5 | +R$ 6,6 |
| Fraqueza de continuacao | Tamanho do impulso antes do recuo (pts) | 305 a 350 | 408 | +R$ 2,9 | −R$ 2,6 | +R$ 14,5 |
| Fraqueza de continuacao | Tamanho do impulso antes do recuo (pts) | 350 a 395 | 443 | +R$ 9,5 | +R$ 6,9 | +R$ 14,2 |
| Fraqueza de continuacao | Tamanho do impulso antes do recuo (pts) | 395 a 475 | 442 | +R$ 3,5 | −R$ 6,8 | +R$ 22,2 |
| Fraqueza de continuacao | Tamanho do impulso antes do recuo (pts) | 475 a +inf | 433 | +R$ 0,3 | +R$ 5,7 | −R$ 10,6 |
| Segundas entradas | Trigger anterior no mesmo nivel (<=100 pts, 60 candles) | primeira | 1.315 | +R$ 4,4 | −R$ 0,8 | +R$ 14,6 |
| Segundas entradas | Trigger anterior no mesmo nivel (<=100 pts, 60 candles) | segunda no nivel | 826 | +R$ 4,3 | +R$ 5,8 | +R$ 1,3 |
| Segundas entradas | Ordem do trigger no dia (mesmo lado) | 1a | 262 | +R$ 2,0 | −R$ 9,1 | +R$ 18,9 |
| Segundas entradas | Ordem do trigger no dia (mesmo lado) | 2a | 258 | −R$ 3,9 | −R$ 16,2 | +R$ 14,5 |
| Segundas entradas | Ordem do trigger no dia (mesmo lado) | 3a | 246 | +R$ 7,7 | +R$ 15,4 | −R$ 4,2 |
| Segundas entradas | Ordem do trigger no dia (mesmo lado) | 4a | 230 | +R$ 3,3 | +R$ 7,9 | −R$ 4,4 |
| Segundas entradas | Ordem do trigger no dia (mesmo lado) | 5a+ | 1.145 | +R$ 6,2 | +R$ 3,6 | +R$ 12,5 |
| Horario | Hora do trigger | 09h | 475 | −R$ 8,8 | −R$ 11,2 | −R$ 5,4 |
| Horario | Hora do trigger | 10h | 554 | +R$ 11,3 | +R$ 9,3 | +R$ 14,3 |
| Horario | Hora do trigger | 11h | 345 | −R$ 1,6 | −R$ 2,5 | +R$ 0,5 |
| Horario | Hora do trigger | 12h | 183 | +R$ 17,3 | +R$ 9,0 | +R$ 37,8 |
| Horario | Hora do trigger | 13h | 132 | +R$ 23,4 | +R$ 17,6 | +R$ 37,0 |
| Horario | Hora do trigger | 14h | 118 | +R$ 9,2 | +R$ 5,4 | +R$ 19,5 |
| Horario | Hora do trigger | 15h | 115 | +R$ 1,2 | −R$ 6,9 | +R$ 33,5 |
| Horario | Hora do trigger | 16h | 120 | +R$ 19,0 | +R$ 20,7 | +R$ 13,6 |
| Horario | Hora do trigger | 17h+ | 99 | −R$ 20,0 | −R$ 19,0 | −R$ 23,0 |
| Horario | Abertura das acoes (10:00) | 09:45-10:00 | 81 | −R$ 23,7 | −R$ 31,2 | −R$ 11,0 |
| Horario | Abertura das acoes (10:00) | 10:00-10:10 | 108 | −R$ 9,7 | +R$ 1,2 | −R$ 21,8 |
| Horario | Abertura das acoes (10:00) | 10:10-10:30 | 149 | +R$ 26,0 | +R$ 37,0 | +R$ 10,6 |
| Horario | Abertura das acoes (10:00) | resto | 1.803 | +R$ 4,7 | +R$ 0,6 | +R$ 13,2 |
| Horario | Abertura do Dow Jones (10:30 no horario de verao dos EUA) | > 30 min antes | 483 | −R$ 7,5 | −R$ 8,9 | −R$ 5,4 |
| Horario | Abertura do Dow Jones (10:30 no horario de verao dos EUA) | 30-5 min antes | 238 | +R$ 14,1 | +R$ 27,4 | −R$ 3,0 |
| Horario | Abertura do Dow Jones (10:30 no horario de verao dos EUA) | 5 antes a 15 depois | 199 | −R$ 2,4 | −R$ 17,3 | +R$ 23,3 |
| Horario | Abertura do Dow Jones (10:30 no horario de verao dos EUA) | 15-60 min depois | 307 | +R$ 7,9 | +R$ 4,2 | +R$ 14,8 |
| Horario | Abertura do Dow Jones (10:30 no horario de verao dos EUA) | mais de 1h depois | 914 | +R$ 8,3 | +R$ 3,9 | +R$ 20,5 |
| Movimento picado | Inversoes nos 20 candles antes do recuo | -inf a 8 | 428 | −R$ 4,7 | −R$ 2,1 | −R$ 9,6 |
| Movimento picado | Inversoes nos 20 candles antes do recuo | 8 a 9 | 333 | +R$ 0,2 | +R$ 7,9 | −R$ 14,7 |
| Movimento picado | Inversoes nos 20 candles antes do recuo | 9 a 11 | 775 | +R$ 0,4 | −R$ 8,0 | +R$ 15,9 |
| Movimento picado | Inversoes nos 20 candles antes do recuo | 11 a +inf | 605 | +R$ 18,0 | +R$ 12,9 | +R$ 29,2 |
| Volume (agressao) | Volume do trigger / mediana 200 | -inf a 0.55 | 427 | −R$ 0,8 | −R$ 7,7 | +R$ 12,9 |
| Volume (agressao) | Volume do trigger / mediana 200 | 0.55 a 0.91 | 419 | +R$ 2,7 | +R$ 8,0 | −R$ 8,3 |
| Volume (agressao) | Volume do trigger / mediana 200 | 0.91 a 1.41 | 400 | −R$ 3,0 | −R$ 0,9 | −R$ 8,1 |
| Volume (agressao) | Volume do trigger / mediana 200 | 1.41 a 2.31 | 459 | +R$ 18,7 | +R$ 17,3 | +R$ 21,0 |
| Volume (agressao) | Volume do trigger / mediana 200 | 2.31 a +inf | 436 | +R$ 2,5 | −R$ 8,1 | +R$ 22,3 |
| Volume (agressao) | Volume medio do recuo / mediana 200 | -inf a 0.71 | 436 | −R$ 6,6 | −R$ 14,0 | +R$ 7,3 |
| Volume (agressao) | Volume medio do recuo / mediana 200 | 0.71 a 1.03 | 413 | −R$ 5,6 | −R$ 9,3 | +R$ 2,6 |
| Volume (agressao) | Volume medio do recuo / mediana 200 | 1.03 a 1.4 | 402 | +R$ 23,9 | +R$ 24,1 | +R$ 23,2 |
| Volume (agressao) | Volume medio do recuo / mediana 200 | 1.4 a 1.98 | 447 | +R$ 7,5 | +R$ 6,7 | +R$ 8,8 |
| Volume (agressao) | Volume medio do recuo / mediana 200 | 1.98 a +inf | 443 | +R$ 3,5 | +R$ 1,2 | +R$ 7,6 |
| Volume (agressao) | Saldo agressor do trigger a favor (% do volume) | -inf a 0.02 | 407 | +R$ 3,5 | −R$ 0,5 | +R$ 12,6 |
| Volume (agressao) | Saldo agressor do trigger a favor (% do volume) | 0.02 a 0.07 | 424 | +R$ 6,3 | +R$ 3,3 | +R$ 12,4 |
| Volume (agressao) | Saldo agressor do trigger a favor (% do volume) | 0.07 a 0.12 | 447 | +R$ 10,4 | +R$ 6,8 | +R$ 16,8 |
| Volume (agressao) | Saldo agressor do trigger a favor (% do volume) | 0.12 a 0.2 | 443 | −R$ 0,0 | −R$ 3,9 | +R$ 6,8 |
| Volume (agressao) | Saldo agressor do trigger a favor (% do volume) | 0.2 a +inf | 420 | +R$ 1,3 | +R$ 2,9 | −R$ 2,1 |
| Volume (agressao) | Saldo agressor do recuo a favor do trade | -inf a -0.27 | 467 | +R$ 3,7 | +R$ 0,8 | +R$ 8,2 |
| Volume (agressao) | Saldo agressor do recuo a favor do trade | -0.27 a -0.2 | 445 | −R$ 5,4 | −R$ 18,2 | +R$ 17,1 |
| Volume (agressao) | Saldo agressor do recuo a favor do trade | -0.2 a -0.15 | 439 | +R$ 14,8 | +R$ 16,5 | +R$ 11,6 |
| Volume (agressao) | Saldo agressor do recuo a favor do trade | -0.15 a -0.11 | 404 | +R$ 0,3 | +R$ 1,2 | −R$ 2,0 |
| Volume (agressao) | Saldo agressor do recuo a favor do trade | -0.11 a +inf | 386 | +R$ 8,8 | +R$ 8,4 | +R$ 9,9 |
| Tempo das barras | Tempo do trigger / mediana 200 | -inf a 0.48 | 440 | +R$ 1,9 | −R$ 5,1 | +R$ 14,5 |
| Tempo das barras | Tempo do trigger / mediana 200 | 0.48 a 1.05 | 404 | −R$ 6,3 | −R$ 6,8 | −R$ 5,0 |
| Tempo das barras | Tempo do trigger / mediana 200 | 1.05 a 1.95 | 388 | +R$ 8,1 | +R$ 14,0 | −R$ 7,5 |
| Tempo das barras | Tempo do trigger / mediana 200 | 1.95 a 3.94 | 433 | +R$ 13,3 | +R$ 15,7 | +R$ 8,9 |
| Tempo das barras | Tempo do trigger / mediana 200 | 3.94 a +inf | 461 | +R$ 6,1 | −R$ 7,3 | +R$ 27,2 |
| Tempo das barras | Tempo medio do recuo / mediana 200 | -inf a 0.62 | 442 | +R$ 1,6 | −R$ 5,1 | +R$ 13,5 |
| Tempo das barras | Tempo medio do recuo / mediana 200 | 0.62 a 1.18 | 403 | −R$ 11,0 | −R$ 10,2 | −R$ 12,9 |
| Tempo das barras | Tempo medio do recuo / mediana 200 | 1.18 a 1.92 | 387 | +R$ 20,9 | +R$ 11,5 | +R$ 46,1 |
| Tempo das barras | Tempo medio do recuo / mediana 200 | 1.92 a 3.42 | 419 | +R$ 5,6 | +R$ 9,8 | −R$ 3,0 |
| Tempo das barras | Tempo medio do recuo / mediana 200 | 3.42 a +inf | 475 | +R$ 7,1 | +R$ 4,7 | +R$ 10,7 |
| Geometria | Pavio da abertura do trigger (pts) | -inf a 15 | 298 | +R$ 3,0 | +R$ 3,8 | +R$ 1,1 |
| Geometria | Pavio da abertura do trigger (pts) | 15 a 35 | 526 | +R$ 0,4 | +R$ 0,7 | −R$ 0,2 |
| Geometria | Pavio da abertura do trigger (pts) | 35 a 50 | 351 | +R$ 8,6 | +R$ 7,7 | +R$ 10,3 |
| Geometria | Pavio da abertura do trigger (pts) | 50 a 75 | 496 | +R$ 5,2 | +R$ 0,7 | +R$ 13,6 |
| Geometria | Pavio da abertura do trigger (pts) | 75 a +inf | 470 | +R$ 5,4 | −R$ 1,8 | +R$ 18,9 |
| Geometria | Hull alem do candle (pts; >0 = T2) | -inf a -153.28 | 424 | +R$ 3,8 | +R$ 8,8 | −R$ 6,4 |
| Geometria | Hull alem do candle (pts; >0 = T2) | -153.28 a -75.87 | 408 | +R$ 9,7 | −R$ 3,0 | +R$ 38,6 |
| Geometria | Hull alem do candle (pts; >0 = T2) | -75.87 a -2.75 | 437 | −R$ 3,8 | −R$ 12,3 | +R$ 11,8 |
| Geometria | Hull alem do candle (pts; >0 = T2) | -2.75 a 77.43 | 434 | +R$ 8,3 | +R$ 5,0 | +R$ 14,6 |
| Geometria | Hull alem do candle (pts; >0 = T2) | 77.43 a +inf | 438 | +R$ 4,1 | +R$ 10,1 | −R$ 6,9 |
| Geometria | Toque na EMA | quase toque (1-15) | 155 | +R$ 12,5 | +R$ 10,6 | +R$ 16,6 |
| Geometria | Toque na EMA | toca | 1.986 | +R$ 3,7 | +R$ 1,0 | +R$ 8,9 |
| Tendencia geral | Forca do MACD (/ATR) | -inf a 0.06 | 402 | +R$ 10,1 | +R$ 16,4 | −R$ 5,0 |
| Tendencia geral | Forca do MACD (/ATR) | 0.06 a 0.12 | 456 | +R$ 1,5 | −R$ 6,4 | +R$ 14,4 |
| Tendencia geral | Forca do MACD (/ATR) | 0.12 a 0.18 | 424 | −R$ 4,4 | −R$ 7,7 | +R$ 2,1 |
| Tendencia geral | Forca do MACD (/ATR) | 0.18 a 0.24 | 440 | +R$ 8,2 | +R$ 3,8 | +R$ 16,2 |
| Tendencia geral | Forca do MACD (/ATR) | 0.24 a +inf | 419 | +R$ 6,7 | +R$ 2,5 | +R$ 15,7 |
| Horario | Candles desde a abertura do pregao | 100+ | 1.656 | +R$ 8,0 | +R$ 5,2 | +R$ 13,8 |
| Horario | Candles desde a abertura do pregao | 40-100 | 363 | −R$ 9,9 | −R$ 7,9 | −R$ 13,1 |
| Horario | Candles desde a abertura do pregao | < 40 | 122 | −R$ 3,0 | −R$ 21,7 | +R$ 29,0 |

## Selecao de filtros so no treino

**Seca no fechamento**

| Passo | R$/sinal treino | R$/sinal teste | Sinais teste |
|:--|--:|--:|--:|
| (sem filtro) | +R$ 1,74 | +R$ 9,47 | 722 |
| inversoes = 11 a +inf | +R$ 12,90 | +R$ 29,21 | 190 |
| dow != 5 antes a 15 depois | +R$ 16,73 | +R$ 27,34 | 178 |

**Limitada no meio do corpo**

| Passo | R$/sinal treino | R$/sinal teste | Sinais teste |
|:--|--:|--:|--:|
| (sem filtro) | −R$ 5,58 | −R$ 2,26 | 566 |
| mesmo_nivel != primeira | +R$ 5,66 | −R$ 1,53 | 225 |
| macd_acima_sig = nao | +R$ 15,45 | −R$ 0,15 | 158 |
| incl_ema != 74.58 a +inf | +R$ 18,61 | +R$ 3,20 | 150 |

**Stop no extremo do candle**

| Passo | R$/sinal treino | R$/sinal teste | Sinais teste |
|:--|--:|--:|--:|
| (sem filtro) | −R$ 0,53 | +R$ 8,53 | 722 |
| inversoes = 11 a +inf | +R$ 11,37 | +R$ 19,48 | 190 |
| n_trig_dia != 2a | +R$ 14,92 | +R$ 12,98 | 163 |

## Variantes (carteira, 6 contratos, liquido)

| Variante | Gestao | Trades | Liquido | Fator | Rebaix. | Treino | Teste | MC p(prej.) | Percentil vs aleatorio | Atravessar 5 pts | 1 tick antes | Escorreg. 10 pts |
|:--|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| Seca no fechamento - regra pura | stop 100, parcial 50% em +100 (stop do restante na media), alvo +300 | 2.037 | +R$ 9.849 | 1,08 | −R$ 5.868 | +R$ 1.581 | +R$ 8.268 | 7,1% | 99 | +R$ 4.584 | +R$ 4.791 | −R$ 14.595 |
| Seca no fechamento - gestao do treino | stop 200, alvo +500, parcial 50% em +50 (stop do restante na entrada) | 2.053 | +R$ 35.391 | 1,39 | −R$ 2.535 | +R$ 23.529 | +R$ 11.862 | 0,0% | 91 | +R$ 25.617 | +R$ 29.580 | +R$ 10.755 |
| Seca no fechamento - filtros do treino | stop 100, parcial 50% em +100 (stop do restante na media), alvo +300 | 530 | +R$ 10.890 | 1,38 | −R$ 1.653 | +R$ 5.757 | +R$ 5.133 | 0,1% | 100 | +R$ 9.210 | +R$ 9.411 | +R$ 4.530 |
| **Seca no fechamento - filtros + gestao do treino** | stop 100, alvo +400, sem parcial | 517 | +R$ 16.209 | 1,35 | −R$ 2.658 | +R$ 10.230 | +R$ 5.979 | 0,2% | 100 | +R$ 15.969 | +R$ 15.429 | +R$ 10.005 |
| Limitada no meio do corpo - regra pura | stop 100, parcial 50% em +100 (stop do restante na media), alvo +300 | 1.591 | −R$ 9.423 | 0,91 | −R$ 12.189 | −R$ 7.872 | −R$ 1.551 | 93,6% | 89 | −R$ 21.750 | −R$ 22.842 | −R$ 28.515 |
| Limitada no meio do corpo - gestao do treino | stop 200, alvo +300, sem parcial | 1.414 | +R$ 12.318 | 1,06 | −R$ 8.052 | +R$ 10.293 | +R$ 2.025 | 13,7% | 95 | −R$ 3.930 | −R$ 4.365 | −R$ 4.650 |
| Limitada no meio do corpo - filtros do treino | stop 100, parcial 50% em +100 (stop do restante na media), alvo +300 | 422 | +R$ 5.724 | 1,22 | −R$ 2.487 | +R$ 5.112 | +R$ 612 | 4,3% | 100 | +R$ 2.280 | +R$ 2.025 | +R$ 660 |
| Limitada no meio do corpo - filtros + gestao do treino | stop 200, alvo +300, sem parcial | 401 | +R$ 13.857 | 1,27 | −R$ 3.633 | +R$ 12.480 | +R$ 1.377 | 1,1% | 100 | +R$ 8.130 | +R$ 8.904 | +R$ 9.045 |
| Stop no extremo do candle - regra pura | stop 100, parcial 50% em +100 (stop do restante na media), alvo +300 | 2.024 | +R$ 4.326 | 1,03 | −R$ 6.972 | −R$ 2.085 | +R$ 6.411 | 30,0% | 97 | −R$ 1.164 | −R$ 1.176 | −R$ 19.962 |
| Stop no extremo do candle - gestao do treino | stop no extremo do candle, alvo +500, parcial 50% em +50 (stop do restante na entrada) | 2.062 | +R$ 33.186 | 1,39 | −R$ 2.622 | +R$ 19.335 | +R$ 13.851 | 0,0% | 92 | +R$ 23.373 | +R$ 27.750 | +R$ 8.442 |
| Stop no extremo do candle - filtros do treino | stop 100, parcial 50% em +100 (stop do restante na media), alvo +300 | 512 | +R$ 6.516 | 1,19 | −R$ 2.547 | +R$ 4.428 | +R$ 2.088 | 4,9% | 99 | +R$ 4.767 | +R$ 5.250 | +R$ 372 |
| Stop no extremo do candle - filtros + gestao do treino | stop no extremo do candle, alvo +500, sem parcial | 475 | +R$ 14.451 | 1,24 | −R$ 3.303 | +R$ 7.662 | +R$ 6.789 | 2,5% | 99 | +R$ 12.783 | +R$ 13.719 | +R$ 8.751 |
| Seca no fechamento - so filtro picado | stop 100, parcial 50% em +100 (stop do restante na media), alvo +300 | 585 | +R$ 10.845 | 1,33 | −R$ 2.043 | +R$ 5.028 | +R$ 5.817 | 0,2% | 100 | +R$ 9.045 | +R$ 9.282 | +R$ 3.825 |
| Seca no fechamento - so filtro picado, stop 100 / alvo 400 | stop 100, alvo +400, sem parcial | 571 | +R$ 16.167 | 1,31 | −R$ 3.288 | +R$ 8.664 | +R$ 7.503 | 0,6% | 100 | +R$ 15.927 | +R$ 15.321 | +R$ 9.315 |

## Recomendada: Seca no fechamento - filtros + gestao do treino

Filtros: inversoes = 11 a +inf, dow != 5 antes a 15 depois. Gestao: stop 100, alvo +400, sem parcial.

| Estatistica | Base | Treino | Teste |
|:--|--:|--:|--:|
| Trades | 517 | 350 | 167 |
| Liquido | +R$ 16.209 | +R$ 10.230 | +R$ 5.979 |
| Fator de lucro | 1,35 | 1,32 | 1,40 |
| Payoff | 3,81 | 3,76 | 3,91 |
| R$ por trade | +R$ 31,35 | +R$ 29,23 | +R$ 35,80 |
| Winrate | 26,1% | 26,0% | 26,4% |
| Maior ganho | +R$ 477 | +R$ 477 | +R$ 477 |
| Maior perda | −R$ 123 | −R$ 123 | −R$ 123 |
| Max. perdas seguidas | 15 | 15 | 13 |
| Rebaixamento maximo | −R$ 2.658 | −R$ 2.658 | −R$ 1.752 |
| Fator de recuperacao | 6,10 | 3,85 | 3,41 |
| Sharpe por trade | 0,120 | 0,110 | 0,140 |
| Pregoes positivos | 49% | 52% | 45% |
| Compras R$ | +R$ 5.073 | +R$ 3.270 | +R$ 1.803 |
| Vendas R$ | +R$ 11.136 | +R$ 6.960 | +R$ 4.176 |

Monte Carlo (5.000 reamostragens): resultado p5 +R$ 6.603, mediana +R$ 16.089; rebaixamento p95 −R$ 5.256; prejuizo em 0,2% dos sorteios. Contra entradas aleatorias com a mesma gestao: percentil 100,0.

Mes a mes: 2026-03 +R$ 3.312 (136); 2026-04 +R$ 5.820 (60); 2026-05 +R$ 510 (70); 2026-06 +R$ 588 (84); 2026-07 +R$ 543 (59); 2026-08 +R$ 2.328 (64); 2026-09 +R$ 3.108 (44).

Versao so com o filtro picado (Seca no fechamento - so filtro picado, stop 100 / alvo 400): 571 trades, +R$ 16.167, fator 1,31, treino +R$ 8.664 / teste +R$ 7.503.

## Conclusoes

1. **A regra pura tem vantagem fina demais**: +R$ 9.849 em 2.037 trades, e o resultado depende de a parcial e o alvo executarem no toque exato: atravessando 5 pts cai para +R$ 4.584; com 10 pts de escorregamento, −R$ 14.595.
2. **T1 x T2 nao separa** de forma consistente (T2 melhor no treino, T1 no teste).
3. **Movimento picado antes do recuo (11+ inversoes em 20 candles) e o unico filtro que se confirmou fora da amostra**, ao contrario da hipotese. Pequenos e consistentes: evitar 09h e 17h+, e MACD ja alem da Bollinger 1000.
4. **Entrada seca no fechamento** e a melhor; a limitada no meio do corpo so executa nos sinais piores.
5. **Gestao**: nos sinais filtrados, stop 100 / alvo +400 sem parcial. A parcial em +50 com stop na entrada "funciona" ate com entradas aleatorias: e efeito da reconstrucao dos pavios do grafico PI, nao do setup.
6. **Limites**: 132 pregoes de um so regime (alta), caminho dentro do candle reconstruido. Validar em replay ou simulador antes de operar.
