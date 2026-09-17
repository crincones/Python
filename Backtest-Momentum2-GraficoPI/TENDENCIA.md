# Filtros de tendencia geral e consolidacao

Complemento de `RESULTADOS.md`. 2.141 sinais, 132 pregoes (2026-03-06 a 2026-09-14), entrada seca no fechamento, 6 contratos, R$ 0,50 por contrato. Treino ate 2026-07-01. Graficos e todas as tabelas em `tendencia.html`.

## Consolidacao em 100 candles (eficiencia = |alta - baixa| / 100 antes do recuo)

**Stop 100 / alvo 400 sem parcial**

| Filtro | Trades | Liquido | Fator | Rebaixamento | Treino | Teste | Atravessar 5 pts |
|:--|--:|--:|--:|--:|--:|--:|--:|
| sem filtro | 1.947 | +R$ 11.199 | 1,06 | −R$ 7.089 | +R$ 2.121 | +R$ 9.078 | +R$ 10.605 |
| consolidado 100 (eficiencia < 0,08) | 1.083 | −R$ 9.249 | 0,91 | −R$ 14.247 | −R$ 10.071 | +R$ 822 | −R$ 9.966 |
| fora da consolidacao 100 (eficiencia >= 0,08) | 894 | +R$ 21.798 | 1,26 | −R$ 3.354 | +R$ 12.138 | +R$ 9.660 | +R$ 21.921 |
| tendencia de 100 candles A FAVOR do trade | 641 | +R$ 12.357 | 1,21 | −R$ 5.136 | +R$ 9.030 | +R$ 3.327 | +R$ 12.480 |
| tendencia de 100 candles CONTRA o trade | 254 | +R$ 9.318 | 1,41 | −R$ 1.845 | +R$ 2.985 | +R$ 6.333 | +R$ 9.318 |
| so picado | 571 | +R$ 16.167 | 1,31 | −R$ 3.288 | +R$ 8.664 | +R$ 7.503 | +R$ 15.927 |
| fora da consolidacao 100 E picado | 256 | +R$ 11.952 | 1,54 | −R$ 1.230 | +R$ 6.822 | +R$ 5.130 | +R$ 11.952 |
| fora da consolidacao 100 OU picado | 1.205 | +R$ 26.505 | 1,24 | −R$ 3.477 | +R$ 14.226 | +R$ 12.279 | +R$ 26.388 |

**Gestao do CLAUDE.md (stop 100, parcial +100, alvo 300)**

| Filtro | Trades | Liquido | Fator | Rebaixamento | Treino | Teste | Atravessar 5 pts |
|:--|--:|--:|--:|--:|--:|--:|--:|
| sem filtro | 2.037 | +R$ 9.849 | 1,08 | −R$ 5.868 | +R$ 1.581 | +R$ 8.268 | +R$ 4.584 |
| consolidado 100 (eficiencia < 0,08) | 1.126 | −R$ 4.938 | 0,93 | −R$ 9.303 | −R$ 7.875 | +R$ 2.937 | −R$ 7.695 |
| fora da consolidacao 100 (eficiencia >= 0,08) | 925 | +R$ 14.625 | 1,28 | −R$ 1.959 | +R$ 9.675 | +R$ 4.950 | +R$ 12.114 |
| tendencia de 100 candles A FAVOR do trade | 663 | +R$ 9.171 | 1,25 | −R$ 2.592 | +R$ 7.299 | +R$ 1.872 | +R$ 7.497 |
| tendencia de 100 candles CONTRA o trade | 262 | +R$ 5.454 | 1,38 | −R$ 1.023 | +R$ 2.376 | +R$ 3.078 | +R$ 4.617 |
| so picado | 585 | +R$ 10.845 | 1,33 | −R$ 2.043 | +R$ 5.028 | +R$ 5.817 | +R$ 9.045 |
| fora da consolidacao 100 E picado | 260 | +R$ 8.340 | 1,62 | −R$ 1.134 | +R$ 5.013 | +R$ 3.327 | +R$ 7.860 |
| fora da consolidacao 100 OU picado | 1.247 | +R$ 17.379 | 1,25 | −R$ 2.652 | +R$ 9.693 | +R$ 7.686 | +R$ 13.548 |

Grade janela x limiar (liquido, stop 100 / alvo 400):

| Janela | >= 0.04 | >= 0.06 | >= 0.08 | >= 0.1 | >= 0.12 | >= 0.15 |
|:--|--:|--:|--:|--:|--:|--:|
| 30 | +R$ 13.614 | +R$ 13.614 | +R$ 5.988 | +R$ 5.988 | +R$ 5.988 | +R$ 1.371 |
| 50 | +R$ 12.870 | +R$ 6.759 | +R$ 6.759 | +R$ 858 | +R$ 858 | −R$ 162 |
| 100 | +R$ 14.400 | +R$ 15.717 | +R$ 21.798 | +R$ 14.877 | +R$ 8.040 | +R$ 6.849 |
| 150 | +R$ 16.017 | +R$ 17.073 | +R$ 12.147 | +R$ 3.723 | +R$ 90 | +R$ 1.332 |
| 200 | +R$ 17.055 | +R$ 6.525 | +R$ 5.424 | −R$ 2.049 | −R$ 3.015 | −R$ 1.224 |

## Contexto do dia (carteira)

| Gestao | Conjunto | Filtro | Trades | Liquido | Fator | Rebaix. | Treino | Teste |
|:--|:--|:--|--:|--:|--:|--:|--:|--:|
| claude | todos | sem filtro | 2.037 | +R$ 9.849 | 1,08 | −R$ 5.868 | +R$ 1.581 | +R$ 8.268 |
| claude | todos | dia contra o trade: preco > 100 pts contra a abertura | 760 | +R$ 10.800 | 1,25 | −R$ 2.439 | +R$ 5.679 | +R$ 5.121 |
| claude | todos | dia a favor ou neutro | 1.281 | −R$ 1.323 | 0,98 | −R$ 8.217 | −R$ 4.347 | +R$ 3.024 |
| claude | todos | dia contra + fora da consolidacao 100 | 272 | +R$ 8.304 | 1,60 | −R$ 1.149 | +R$ 4.611 | +R$ 3.693 |
| claude | picado | sem filtro | 585 | +R$ 10.845 | 1,33 | −R$ 2.043 | +R$ 5.028 | +R$ 5.817 |
| claude | picado | dia contra o trade: preco > 100 pts contra a abertura | 221 | +R$ 5.337 | 1,45 | −R$ 1.122 | +R$ 1.914 | +R$ 3.423 |
| claude | picado | dia a favor ou neutro | 364 | +R$ 5.508 | 1,27 | −R$ 1.356 | +R$ 3.114 | +R$ 2.394 |
| claude | picado | dia contra + fora da consolidacao 100 | 80 | +R$ 4.200 | 2,12 | −R$ 501 | +R$ 2.358 | +R$ 1.842 |
| r400 | todos | sem filtro | 1.947 | +R$ 11.199 | 1,06 | −R$ 7.089 | +R$ 2.121 | +R$ 9.078 |
| r400 | todos | dia contra o trade: preco > 100 pts contra a abertura | 728 | +R$ 13.536 | 1,20 | −R$ 4.461 | +R$ 6.699 | +R$ 6.837 |
| r400 | todos | dia a favor ou neutro | 1.231 | −R$ 3.213 | 0,97 | −R$ 10.839 | −R$ 4.962 | +R$ 1.749 |
| r400 | todos | dia contra + fora da consolidacao 100 | 268 | +R$ 11.916 | 1,50 | −R$ 2.229 | +R$ 4.980 | +R$ 6.936 |
| r400 | picado | sem filtro | 571 | +R$ 16.167 | 1,31 | −R$ 3.288 | +R$ 8.664 | +R$ 7.503 |
| r400 | picado | dia contra o trade: preco > 100 pts contra a abertura | 216 | +R$ 9.192 | 1,48 | −R$ 1.758 | +R$ 5.649 | +R$ 3.543 |
| r400 | picado | dia a favor ou neutro | 357 | +R$ 7.329 | 1,22 | −R$ 2.229 | +R$ 3.369 | +R$ 3.960 |
| r400 | picado | dia contra + fora da consolidacao 100 | 80 | +R$ 8.280 | 2,37 | −R$ 630 | +R$ 4.878 | +R$ 3.402 |

## Filtros definidos a priori (carteira)

**Gestao do CLAUDE.md (stop 100, parcial +100, alvo 300), todos os sinais**

| Filtro | % sinais | Trades | Liquido | Fator | Rebaix. | Treino | Teste |
|:--|--:|--:|--:|--:|--:|--:|--:|
| sem filtro de tendencia | 100% | 2.037 | +R$ 9.849 | 1,08 | −R$ 5.868 | +R$ 1.581 | +R$ 8.268 |
| evitar EMA 21 plana: variacao direta 10 >= 4.5 pts/candle | 80% | 1.642 | +R$ 12.834 | 1,14 | −R$ 4.038 | +R$ 3.684 | +R$ 9.150 |
| evitar EMA 21 plana: regressao 10 >= 5.6 pts/candle | 81% | 1.655 | +R$ 8.355 | 1,09 | −R$ 3.894 | +R$ 318 | +R$ 8.037 |
| evitar EMA 21 ondulada: R2 10 >= 0.71 | 80% | 1.638 | +R$ 13.446 | 1,14 | −R$ 3.918 | +R$ 3.450 | +R$ 9.996 |
| evitar consolidado em 100 candles: eficiencia 100 >= 0,08 | 46% | 925 | +R$ 14.625 | 1,28 | −R$ 1.959 | +R$ 9.675 | +R$ 4.950 |
| evitar mercado vindo contra: direcao 30 > 0 | 73% | 1.480 | +R$ 12.720 | 1,15 | −R$ 3.456 | +R$ 5.850 | +R$ 6.870 |
| EMA plana (direta) + ondulada + consolidado 100 | 36% | 729 | +R$ 11.373 | 1,28 | −R$ 1.875 | +R$ 6.939 | +R$ 4.434 |

**Gestao do CLAUDE.md (stop 100, parcial +100, alvo 300), so sinais com filtro picado**

| Filtro | % sinais | Trades | Liquido | Fator | Rebaix. | Treino | Teste |
|:--|--:|--:|--:|--:|--:|--:|--:|
| sem filtro de tendencia | 100% | 585 | +R$ 10.845 | 1,33 | −R$ 2.043 | +R$ 5.028 | +R$ 5.817 |
| evitar EMA 21 plana: variacao direta 10 >= 4.5 pts/candle | 79% | 461 | +R$ 9.057 | 1,35 | −R$ 1.650 | +R$ 4.197 | +R$ 4.860 |
| evitar EMA 21 plana: regressao 10 >= 5.6 pts/candle | 78% | 456 | +R$ 7.512 | 1,29 | −R$ 1.494 | +R$ 2.547 | +R$ 4.965 |
| evitar EMA 21 ondulada: R2 10 >= 0.71 | 81% | 471 | +R$ 10.707 | 1,42 | −R$ 1.767 | +R$ 5.622 | +R$ 5.085 |
| evitar consolidado em 100 candles: eficiencia 100 >= 0,08 | 45% | 260 | +R$ 8.340 | 1,62 | −R$ 1.134 | +R$ 5.013 | +R$ 3.327 |
| evitar mercado vindo contra: direcao 30 > 0 | 72% | 421 | +R$ 10.977 | 1,51 | −R$ 1.407 | +R$ 6.567 | +R$ 4.410 |
| EMA plana (direta) + ondulada + consolidado 100 | 35% | 204 | +R$ 6.588 | 1,61 | −R$ 1.053 | +R$ 3.681 | +R$ 2.907 |

**Stop 100 / alvo 400 sem parcial, todos os sinais**

| Filtro | % sinais | Trades | Liquido | Fator | Rebaix. | Treino | Teste |
|:--|--:|--:|--:|--:|--:|--:|--:|
| sem filtro de tendencia | 100% | 1.947 | +R$ 11.199 | 1,06 | −R$ 7.089 | +R$ 2.121 | +R$ 9.078 |
| evitar EMA 21 plana: variacao direta 10 >= 4.5 pts/candle | 80% | 1.573 | +R$ 12.921 | 1,09 | −R$ 6.096 | +R$ 3.813 | +R$ 9.108 |
| evitar EMA 21 plana: regressao 10 >= 5.6 pts/candle | 81% | 1.590 | +R$ 7.830 | 1,05 | −R$ 5.886 | −R$ 525 | +R$ 8.355 |
| evitar EMA 21 ondulada: R2 10 >= 0.71 | 80% | 1.569 | +R$ 12.093 | 1,08 | −R$ 5.811 | +R$ 1.539 | +R$ 10.554 |
| evitar consolidado em 100 candles: eficiencia 100 >= 0,08 | 46% | 894 | +R$ 21.798 | 1,26 | −R$ 3.354 | +R$ 12.138 | +R$ 9.660 |
| evitar mercado vindo contra: direcao 30 > 0 | 73% | 1.423 | +R$ 11.571 | 1,08 | −R$ 5.700 | +R$ 5.118 | +R$ 6.453 |
| EMA plana (direta) + ondulada + consolidado 100 | 36% | 710 | +R$ 17.310 | 1,26 | −R$ 3.672 | +R$ 9.855 | +R$ 7.455 |

**Stop 100 / alvo 400 sem parcial, so sinais com filtro picado**

| Filtro | % sinais | Trades | Liquido | Fator | Rebaix. | Treino | Teste |
|:--|--:|--:|--:|--:|--:|--:|--:|
| sem filtro de tendencia | 100% | 571 | +R$ 16.167 | 1,31 | −R$ 3.288 | +R$ 8.664 | +R$ 7.503 |
| evitar EMA 21 plana: variacao direta 10 >= 4.5 pts/candle | 79% | 452 | +R$ 14.004 | 1,34 | −R$ 2.748 | +R$ 7.101 | +R$ 6.903 |
| evitar EMA 21 plana: regressao 10 >= 5.6 pts/candle | 78% | 449 | +R$ 11.973 | 1,29 | −R$ 2.799 | +R$ 5.085 | +R$ 6.888 |
| evitar EMA 21 ondulada: R2 10 >= 0.71 | 81% | 464 | +R$ 14.208 | 1,34 | −R$ 2.367 | +R$ 7.920 | +R$ 6.288 |
| evitar consolidado em 100 candles: eficiencia 100 >= 0,08 | 45% | 256 | +R$ 11.952 | 1,54 | −R$ 1.230 | +R$ 6.822 | +R$ 5.130 |
| evitar mercado vindo contra: direcao 30 > 0 | 72% | 413 | +R$ 14.601 | 1,39 | −R$ 2.091 | +R$ 9.468 | +R$ 5.133 |
| EMA plana (direta) + ondulada + consolidado 100 | 35% | 202 | +R$ 9.114 | 1,52 | −R$ 1.758 | +R$ 4.524 | +R$ 4.590 |

## Hipoteses sinal a sinal (stop 100 / alvo 400, todos os sinais)

| Condicao | % sinais | R$/trade | Treino | Teste | Resto | t |
|:--|--:|--:|--:|--:|--:|--:|
| 20 candles vinham contra o trade (mov_20 < 0) | 2% | +R$ 48,4 | +R$ 59,6 | +R$ 34,9 | +R$ 4,3 | 1,03 |
| 20 candles vinham a favor (mov_20 > 0) | 87% | +R$ 3,7 | −R$ 0,1 | +R$ 11,0 | +R$ 14,7 | −0,69 |
| 30 candles vinham contra (mov_30 < 0) | 12% | +R$ 3,0 | −R$ 10,5 | +R$ 32,6 | +R$ 5,5 | −0,15 |
| 30 candles vinham a favor (mov_30 > 0) | 73% | +R$ 8,4 | +R$ 6,8 | +R$ 11,4 | −R$ 3,4 | 1,01 |
| Consolidado: eficiencia 30 < 0,2 | 67% | +R$ 6,1 | +R$ 3,8 | +R$ 10,7 | +R$ 3,4 | 0,24 |
| Em tendencia: eficiencia 30 >= 0,4 | 2% | +R$ 28,3 | +R$ 27,0 | +R$ 31,3 | +R$ 4,7 | 0,61 |
| Consolidado: 4+ cruzamentos da EMA em 30 | 66% | +R$ 5,0 | −R$ 1,4 | +R$ 18,1 | +R$ 5,5 | −0,05 |
| Tendencia a favor e limpa: mov_30 >= 12 (er >= 0,4) | 2% | +R$ 28,3 | +R$ 27,0 | +R$ 31,3 | +R$ 4,7 | 0,61 |
| EMA 21 plana: |regressao 10| no 1o quintil do treino | 19% | +R$ 6,3 | +R$ 8,0 | +R$ 2,5 | +R$ 4,9 | 0,10 |
| EMA 21 plana: |regressao 20| no 1o quintil do treino | 20% | +R$ 12,1 | +R$ 5,9 | +R$ 24,5 | +R$ 3,4 | 0,65 |
| EMA 21 inclinada a favor: regressao 10 acima da mediana | 50% | +R$ 10,9 | +R$ 4,6 | +R$ 23,1 | −R$ 0,6 | 1,09 |
| EMA 21 plana: |variacao direta 10| no 1o quintil do treino | 20% | −R$ 2,4 | −R$ 2,6 | −R$ 2,1 | +R$ 7,1 | −0,73 |
| EMA 21 inclinada a favor: variacao direta 10 acima da mediana | 50% | +R$ 7,5 | +R$ 1,2 | +R$ 19,7 | +R$ 2,9 | 0,44 |
| EMA 21 ondulada: R2 10 no 1o quintil | 20% | −R$ 4,7 | −R$ 0,9 | −R$ 12,2 | +R$ 7,6 | −0,95 |
| Preco a favor da EMA 200 | 61% | +R$ 4,0 | −R$ 0,9 | +R$ 13,8 | +R$ 7,0 | −0,27 |
| Dia a favor (preco x abertura) | 55% | +R$ 1,1 | +R$ 1,6 | −R$ 0,0 | +R$ 10,3 | −0,86 |

## Controle de acaso

| Gestao / conjunto | Cortes | Melhor t treino | Placebo p99 | Bons no treino que melhoram no teste |
|:--|--:|--:|--:|--:|
| Gestao do CLAUDE.md (stop 100, parcial +100, alvo 300), todos os sinais | 351 | 2,63 | 1,93 | 54% |
| Gestao do CLAUDE.md (stop 100, parcial +100, alvo 300), so sinais com filtro picado | 347 | 2,59 | 2,66 | 41% |
| Stop 100 / alvo 400 sem parcial, todos os sinais | 351 | 1,92 | 1,70 | 54% |
| Stop 100 / alvo 400 sem parcial, so sinais com filtro picado | 347 | 2,75 | 2,88 | 45% |

## Conclusoes

1. **Consolidacao em ~100 candles e o filtro de contexto que funciona**: sinais com |alta - baixa| < 8 nos 100 candles antes do recuo perderam no treino e ficaram perto de zero no teste; fora disso o resultado quase dobra e o rebaixamento cai pela metade. Vale com a tendencia longa a favor ou contra. O limiar 0,08 e pico de grade: use a faixa 0,06-0,10.
2. **EMA 21 plana**: medir pela variacao direta (EMA - EMA[10]) ajuda pouco; a regressao linear de 10 candles nao ajuda. EMA "ondulada" (R2 baixo) tem efeito pequeno parecido.
3. **Ultimos 20/30 candles contra o trade**: raro com a Hull a favor (2% / 12% dos sinais) e inverte entre treino e teste. Nao usar.
4. **Dia**: os trades na direcao do dia (ou com o preco perto da abertura) perderam; os com o preco mais de 100 pts contra a abertura ganharam, nas duas metades. Achado na busca: candidato, nao regra.
5. **Medias longas, gap, dia anterior, Keltner**: nada consistente; os cortes bons no treino melhoram o teste so ~metade das vezes.
6. **Com o filtro picado**: E = mais estavel e menos lucro; OU = mais lucro, montado olhando os dados e ainda a confirmar.
