# Volume agressor como filtro do Hull + pavios

WINFUT, grafico de 20 PI, 50.611 candles, 132 pregoes (06/03/2026 a 14/09/2026). Resultado bruto. Graficos, grade interativa, curvas, MEP/MEN, duracao e trade a trade em `volume_agressor.html`.

**V = agressao compradora + vendedora.** Leituras no fechamento do candle de sinal: vrel_k (media das ultimas k barras / media das 20 anteriores), vpct_k (V[i]/V[i-k] - 1), vmed_k (V[i] / media das k barras anteriores - 1). Cortes q20 / mediana / q80, nos dois sentidos: 66 filtros.

## Resposta curta: nao

- Melhor da busca: **vpct_2 no quintil de baixo**, ganho +7,7 pts; busca contra ruido p = 0,45.
- O mesmo corte com lag de 1, 3 e 5 barras: -2,3, +1,4, -2,5 -- cara de ruido.
- 'Retomada com volume' (vmed_k acima da mediana): -1,7, -2,4, -3,4, e so na venda.
- Ortogonal a Hull e ao horario; correlacionado com a duracao do candle de sinal (ate 0,61).

## 1. Grade de ganho (pts por sinal), Hull + pavios

**1:3 com parcial**

| Leitura | > q20 | <= q20 | > mediana | <= mediana | > q80 | <= q80 |
|:--|--:|--:|--:|--:|--:|--:|
| vrel_1 | -1,0 | +4,5 | +0,9 | -0,9 | +1,3 | -0,3 |
| vrel_2 | +0,2 | -1,0 | -0,6 | +0,6 | -0,6 | +0,1 |
| vrel_3 | +1,2 | -5,2 | +2,0 | -2,0 | -2,4 | +0,6 |
| vrel_5 | +1,1 | -5,2 | +0,8 | -0,9 | +2,3 | -0,6 |
| vpct_1 | +0,6 | -2,3 | +0,8 | -0,8 | -4,2 | +1,0 |
| vpct_2 | -2,0 | +7,7 | -0,2 | +0,2 | -2,5 | +0,6 |
| vpct_3 | -0,4 | +1,4 | -1,5 | +1,4 | -8,3 | +1,9 |
| vpct_5 | +0,6 | -2,5 | -2,5 | +2,4 | -0,7 | +0,2 |
| vmed_2 | -1,3 | +5,1 | -1,7 | +1,6 | +1,0 | -0,2 |
| vmed_3 | -0,8 | +3,3 | -2,4 | +2,3 | -0,9 | +0,2 |
| vmed_5 | -0,8 | +3,3 | -3,4 | +3,3 | +3,3 | -0,8 |

**1:3 sem parcial**

| Leitura | > q20 | <= q20 | > mediana | <= mediana | > q80 | <= q80 |
|:--|--:|--:|--:|--:|--:|--:|
| vrel_1 | -1,4 | +6,3 | +2,4 | -2,4 | +3,6 | -0,8 |
| vrel_2 | +0,5 | -2,4 | -1,2 | +1,2 | +0,1 | -0,0 |
| vrel_3 | +1,6 | -6,7 | +2,9 | -2,9 | -2,9 | +0,7 |
| vrel_5 | +1,8 | -8,0 | +2,3 | -2,3 | +4,9 | -1,2 |
| vpct_1 | +0,7 | -2,8 | +1,8 | -1,7 | -6,4 | +1,5 |
| vpct_2 | -2,8 | +11,0 | +0,7 | -0,7 | +0,0 | -0,0 |
| vpct_3 | -0,5 | +1,8 | -3,0 | +2,8 | -10,1 | +2,3 |
| vpct_5 | +1,4 | -5,9 | -2,1 | +2,1 | +0,2 | -0,0 |
| vmed_2 | -1,8 | +7,0 | -1,1 | +1,0 | +2,4 | -0,6 |
| vmed_3 | -1,3 | +5,0 | -2,6 | +2,5 | -0,5 | +0,1 |
| vmed_5 | -1,4 | +5,5 | -4,7 | +4,5 | +7,4 | -1,7 |

**1:2 sem parcial**

| Leitura | > q20 | <= q20 | > mediana | <= mediana | > q80 | <= q80 |
|:--|--:|--:|--:|--:|--:|--:|
| vrel_1 | -2,4 | +10,6 | +0,3 | -0,3 | +0,2 | -0,0 |
| vrel_2 | -0,9 | +4,0 | -2,2 | +2,2 | -4,6 | +1,1 |
| vrel_3 | -0,6 | +2,5 | +0,9 | -0,9 | -4,1 | +1,0 |
| vrel_5 | +0,9 | -4,0 | -0,3 | +0,3 | +2,0 | -0,5 |
| vpct_1 | +1,1 | -4,4 | +1,9 | -1,9 | -4,0 | +0,9 |
| vpct_2 | -2,6 | +10,0 | -1,3 | +1,2 | -0,4 | +0,1 |
| vpct_3 | -0,3 | +1,2 | -2,6 | +2,5 | -12,6 | +2,9 |
| vpct_5 | +0,6 | -2,3 | -2,0 | +2,0 | -0,5 | +0,1 |
| vmed_2 | -1,6 | +6,0 | -2,2 | +2,1 | -0,9 | +0,2 |
| vmed_3 | -1,6 | +6,2 | -2,0 | +1,9 | -0,4 | +0,1 |
| vmed_5 | -1,5 | +6,1 | -4,5 | +4,3 | +3,8 | -0,9 |

**1:1 sem parcial**

| Leitura | > q20 | <= q20 | > mediana | <= mediana | > q80 | <= q80 |
|:--|--:|--:|--:|--:|--:|--:|
| vrel_1 | -0,6 | +2,7 | -0,6 | +0,6 | -0,9 | +0,2 |
| vrel_2 | -0,1 | +0,4 | -0,1 | +0,1 | -1,3 | +0,3 |
| vrel_3 | +0,8 | -3,7 | +1,1 | -1,1 | -1,9 | +0,5 |
| vrel_5 | +0,5 | -2,3 | -0,6 | +0,6 | -0,4 | +0,1 |
| vpct_1 | +0,4 | -1,7 | -0,2 | +0,2 | -2,0 | +0,5 |
| vpct_2 | -1,1 | +4,4 | -1,2 | +1,1 | -5,0 | +1,2 |
| vpct_3 | -0,3 | +1,0 | +0,0 | -0,0 | -6,5 | +1,5 |
| vpct_5 | -0,2 | +0,8 | -2,9 | +2,8 | -1,6 | +0,4 |
| vmed_2 | -0,8 | +3,1 | -2,4 | +2,3 | -0,4 | +0,1 |
| vmed_3 | -0,4 | +1,6 | -2,1 | +2,0 | -1,2 | +0,3 |
| vmed_5 | -0,3 | +1,2 | -2,1 | +2,0 | -0,8 | +0,2 |

## 2. Acima da mediana (Hull + pavios, 1:3 com parcial)

| Leitura | Sinais | Com | Sem | Ganho | p | T1 / T2 / T3 | Antes (sem filtro) | Compra | Venda | Pct | So 10h-15h |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|--:|--:|
| vrel_1 | 1743 | +9,8 | +8,0 | **+0,9** | 0,694 | +3 / +8 / +19 | +7,7 (+7,0) | +13,9 | +5,7 | 66 | +2,5 |
| vrel_2 | 1749 | +8,3 | +9,6 | **-0,6** | 0,758 | +2 / +6 / +18 | +6,0 (+7,0) | +9,0 | +7,6 | 36 | -0,3 |
| vrel_3 | 1768 | +10,9 | +6,9 | **+2,0** | 0,337 | +4 / +9 / +22 | +7,6 (+7,0) | +13,6 | +8,5 | 83 | +4,0 |
| vrel_5 | 1783 | +9,8 | +8,1 | **+0,8** | 0,687 | +9 / +5 / +15 | +7,4 (+7,0) | +10,1 | +9,4 | 66 | -0,3 |
| vpct_1 | 1735 | +9,7 | +8,2 | **+0,8** | 0,718 | +2 / +11 / +18 | +7,5 (+7,0) | +12,5 | +7,0 | 63 | +2,9 |
| vpct_2 | 1719 | +8,7 | +9,1 | **-0,2** | 0,916 | -0 / +11 / +17 | +5,5 (+7,0) | +10,3 | +7,0 | 45 | +0,5 |
| vpct_3 | 1706 | +7,4 | +10,3 | **-1,5** | 0,494 | -1 / +11 / +15 | +5,5 (+7,0) | +10,2 | +4,8 | 23 | +0,9 |
| vpct_5 | 1730 | +6,4 | +11,4 | **-2,5** | 0,243 | -2 / +8 / +16 | +4,3 (+7,0) | +9,7 | +3,2 | 12 | -1,8 |
| vmed_2 | 1725 | +7,2 | +10,6 | **-1,7** | 0,429 | -1 / +9 / +15 | +5,1 (+7,0) | +12,4 | +2,0 | 21 | -0,4 |
| vmed_3 | 1715 | +6,6 | +11,2 | **-2,4** | 0,290 | -2 / +7 / +15 | +3,9 (+7,0) | +11,3 | +1,9 | 13 | +0,2 |
| vmed_5 | 1710 | +5,5 | +12,2 | **-3,4** | 0,115 | -3 / +7 / +15 | +2,6 (+7,0) | +10,1 | +0,9 | 5 | -1,0 |

## 3. Quintis (Hull + pavios, 1:3 com parcial)

| Leitura | Limites | Q1 | Q2 | Q3 | Q4 | Q5 |
|:--|:--|--:|--:|--:|--:|--:|
| vrel_1 | 0,40 / 0,63 / 0,96 / 1,49 | +13,5 | +5,7 | +8,2 | +5,7 | +11,5 |
| vrel_2 | 0,55 / 0,76 / 1,03 / 1,42 | +8,8 | +12,6 | +4,1 | +10,6 | +8,5 |
| vrel_3 | 0,61 / 0,83 / 1,06 / 1,40 | +3,9 | +9,9 | +12,7 | +12,0 | +6,1 |
| vrel_5 | 0,69 / 0,89 / 1,10 / 1,41 | +5,3 | +6,8 | +15,1 | +6,4 | +11,0 |
| vpct_1 | -0,57 / -0,24 / 0,24 / 1,16 | +5,9 | +6,8 | +14,7 | +9,1 | +8,0 |
| vpct_2 | -0,59 / -0,26 / 0,23 / 1,21 | +16,5 | +9,7 | +4,1 | +8,6 | +5,6 |
| vpct_3 | -0,60 / -0,29 / 0,19 / 1,19 | +10,4 | +10,8 | +10,9 | +12,8 | -0,3 |
| vpct_5 | -0,59 / -0,27 / 0,26 / 1,21 | +6,1 | +13,6 | +11,9 | +6,1 | +7,0 |
| vmed_2 | -0,59 / -0,31 / 0,07 / 0,76 | +15,2 | +7,4 | +6,2 | +5,6 | +10,3 |
| vmed_3 | -0,59 / -0,33 / 0,01 / 0,67 | +12,0 | +15,0 | +4,8 | +5,8 | +7,0 |
| vmed_5 | -0,60 / -0,35 / -0,00 / 0,60 | +12,5 | +12,4 | +6,0 | +2,3 | +11,4 |

## 4. Busca contra ruido e escolha fora

| Conjunto | Gestao | Melhor | Ganho | t | ruido med | ruido p95 | p | Escolhida antes, medida depois | Escolhida T1+T2, medida T3 |
|:--|:--|:--|--:|--:|--:|--:|--:|:--|:--|
| cand | 1:3 com parcial | vpct_2 no quintil de baixo | +7,7 | +1,61 | +1,55 | +2,44 | 0,45 | vpct_2 no quintil de baixo: +22,9 (sem filtro +15,8, n=157) | vmed_5 abaixo da mediana: +14,6 (sem filtro +14,6, n=549) |
| cand | 1:3 sem parcial | vpct_2 no quintil de baixo | +11,0 | +1,61 | +1,55 | +2,40 | 0,44 | vpct_2 no quintil de baixo: +35,0 (sem filtro +21,2, n=157) | vmed_5 abaixo da mediana: +17,5 (sem filtro +18,8, n=549) |
| cand | 1:2 sem parcial | vrel_1 no quintil de baixo | +10,6 | +1,85 | +1,56 | +2,39 | 0,29 | vpct_2 no quintil de baixo: +21,7 (sem filtro +13,6, n=157) | vrel_1 no quintil de baixo: +19,6 (sem filtro +14,1, n=194) |
| cand | 1:1 sem parcial | vpct_5 abaixo da mediana | +2,8 | +1,19 | +1,58 | +2,44 | 0,82 | vpct_2 no quintil de baixo: +10,8 (sem filtro +10,4, n=157) | vpct_5 abaixo da mediana: +12,8 (sem filtro +10,4, n=553) |
| h | 1:3 com parcial | vpct_2 no quintil de baixo | +5,8 | +1,38 | +1,55 | +2,39 | 0,67 | vpct_2 no quintil de baixo: +17,7 (sem filtro +11,0, n=209) | vmed_5 abaixo da mediana: +14,7 (sem filtro +11,0, n=702) |
| h | 1:3 sem parcial | vpct_2 no quintil de baixo | +7,5 | +1,25 | +1,59 | +2,37 | 0,79 | vpct_2 no quintil de baixo: +22,5 (sem filtro +13,6, n=209) | vmed_5 abaixo da mediana: +17,0 (sem filtro +13,0, n=702) |
| h | 1:2 sem parcial | vrel_1 no quintil de baixo | +6,1 | +1,26 | +1,57 | +2,44 | 0,77 | vpct_2 no quintil de baixo: +11,5 (sem filtro +8,3, n=209) | vrel_1 no quintil de baixo: +8,8 (sem filtro +9,0, n=274) |
| h | 1:1 sem parcial | vpct_2 no quintil de baixo | +4,0 | +1,22 | +1,57 | +2,47 | 0,80 | vpct_2 no quintil de baixo: +12,9 (sem filtro +8,5, n=209) | vpct_5 abaixo da mediana: +11,5 (sem filtro +9,0, n=716) |

## 5. Ortogonalidade (correlacao de posto, Hull + pavios)

| Leitura | Inclinacao da Hull (ATR) | Hull - EMA 21 (ATR) | MACD (ATR) | Hora do sinal | Duracao do candle de sinal | Ritmo da ultima hora |
|:--|--:|--:|--:|--:|--:|--:|
| vrel_1 | -0,13 | -0,03 | -0,10 | +0,06 | +0,61 | +0,06 |
| vrel_2 | -0,11 | -0,02 | -0,08 | +0,05 | +0,49 | +0,08 |
| vrel_3 | -0,09 | -0,02 | -0,07 | +0,05 | +0,39 | +0,10 |
| vrel_5 | -0,06 | -0,04 | -0,06 | +0,01 | +0,29 | +0,14 |
| vpct_1 | -0,06 | -0,03 | -0,06 | +0,01 | +0,38 | -0,01 |
| vpct_2 | -0,08 | -0,03 | -0,07 | +0,03 | +0,42 | -0,03 |
| vpct_3 | -0,09 | +0,01 | -0,05 | +0,04 | +0,43 | -0,02 |
| vpct_5 | -0,09 | -0,02 | -0,07 | +0,05 | +0,46 | -0,02 |
| vmed_2 | -0,08 | -0,03 | -0,07 | +0,02 | +0,46 | -0,02 |
| vmed_3 | -0,10 | -0,01 | -0,07 | +0,03 | +0,51 | -0,02 |
| vmed_5 | -0,11 | -0,01 | -0,08 | +0,05 | +0,55 | -0,02 |

## 6. Carteira (Hull + pavios)

| Gestao | Leitura acima da mediana | Trades | Pts | Pts/trade | Acerto | Fator | Rebaix. |
|:--|:--|--:|--:|--:|--:|--:|--:|
| 1:3 com parcial | sem filtro | 3.296 | +30.800 | +9,3 | 28,2% | 1,20 | 5.100 |
| 1:3 com parcial | vrel_1 | 1.682 | +16.700 | +9,9 | 28,7% | 1,21 | 5.000 |
| 1:3 com parcial | vrel_2 | 1.688 | +14.500 | +8,6 | 27,9% | 1,18 | 4.700 |
| 1:3 com parcial | vrel_3 | 1.705 | +18.900 | +11,1 | 28,9% | 1,24 | 5.200 |
| 1:3 com parcial | vrel_5 | 1.718 | +15.800 | +9,2 | 28,5% | 1,19 | 2.700 |
| 1:3 com parcial | vpct_1 | 1.684 | +16.750 | +9,9 | 28,6% | 1,21 | 5.000 |
| 1:3 com parcial | vpct_2 | 1.667 | +15.350 | +9,2 | 28,4% | 1,20 | 4.900 |
| 1:3 com parcial | vpct_3 | 1.648 | +12.800 | +7,8 | 27,4% | 1,17 | 5.500 |
| 1:3 com parcial | vpct_5 | 1.688 | +10.500 | +6,2 | 27,5% | 1,13 | 6.200 |
| 1:3 com parcial | vmed_2 | 1.680 | +13.450 | +8,0 | 28,1% | 1,17 | 5.600 |
| 1:3 com parcial | vmed_3 | 1.660 | +11.550 | +7,0 | 27,6% | 1,15 | 5.600 |
| 1:3 com parcial | vmed_5 | 1.661 | +9.300 | +5,6 | 26,9% | 1,12 | 5.200 |
| 1:3 sem parcial | sem filtro | 3.296 | +40.100 | +12,2 | 28,2% | 1,17 | 6.600 |
| 1:3 sem parcial | vrel_1 | 1.682 | +24.100 | +14,3 | 28,7% | 1,20 | 6.000 |
| 1:3 sem parcial | vrel_2 | 1.688 | +18.300 | +10,8 | 27,9% | 1,15 | 7.000 |
| 1:3 sem parcial | vrel_3 | 1.705 | +25.100 | +14,7 | 28,9% | 1,21 | 7.000 |
| 1:3 sem parcial | vrel_5 | 1.718 | +23.200 | +13,5 | 28,5% | 1,19 | 2.900 |
| 1:3 sem parcial | vpct_1 | 1.684 | +23.500 | +14,0 | 28,6% | 1,20 | 5.800 |
| 1:3 sem parcial | vpct_2 | 1.667 | +21.600 | +13,0 | 28,3% | 1,18 | 5.600 |
| 1:3 sem parcial | vpct_3 | 1.648 | +14.900 | +9,0 | 27,4% | 1,12 | 7.100 |
| 1:3 sem parcial | vpct_5 | 1.688 | +15.800 | +9,4 | 27,5% | 1,13 | 7.200 |
| 1:3 sem parcial | vmed_2 | 1.680 | +19.900 | +11,8 | 28,0% | 1,17 | 6.700 |
| 1:3 sem parcial | vmed_3 | 1.660 | +16.300 | +9,8 | 27,5% | 1,14 | 6.500 |
| 1:3 sem parcial | vmed_5 | 1.661 | +11.900 | +7,2 | 26,9% | 1,10 | 6.400 |
| 1:2 sem parcial | sem filtro | 3.478 | +32.000 | +9,2 | 36,4% | 1,15 | 5.800 |
| 1:2 sem parcial | vrel_1 | 1.734 | +16.300 | +9,4 | 36,5% | 1,15 | 4.500 |
| 1:2 sem parcial | vrel_2 | 1.738 | +12.400 | +7,1 | 35,8% | 1,11 | 4.500 |
| 1:2 sem parcial | vrel_3 | 1.758 | +17.100 | +9,7 | 36,6% | 1,15 | 4.900 |
| 1:2 sem parcial | vrel_5 | 1.774 | +15.300 | +8,6 | 36,2% | 1,14 | 3.200 |
| 1:2 sem parcial | vpct_1 | 1.727 | +19.200 | +11,1 | 37,1% | 1,18 | 4.300 |
| 1:2 sem parcial | vpct_2 | 1.712 | +13.400 | +7,8 | 35,9% | 1,12 | 4.100 |
| 1:2 sem parcial | vpct_3 | 1.699 | +11.300 | +6,7 | 35,6% | 1,10 | 4.700 |
| 1:2 sem parcial | vpct_5 | 1.724 | +12.400 | +7,2 | 35,7% | 1,11 | 5.800 |
| 1:2 sem parcial | vmed_2 | 1.717 | +12.000 | +7,0 | 35,6% | 1,11 | 4.600 |
| 1:2 sem parcial | vmed_3 | 1.707 | +12.300 | +7,2 | 35,7% | 1,11 | 4.600 |
| 1:2 sem parcial | vmed_5 | 1.701 | +8.000 | +4,7 | 34,9% | 1,07 | 4.500 |
| 1:1 sem parcial | sem filtro | 3.508 | +21.900 | +6,2 | 53,0% | 1,13 | 4.900 |
| 1:1 sem parcial | vrel_1 | 1.743 | +9.800 | +5,6 | 52,8% | 1,12 | 3.800 |
| 1:1 sem parcial | vrel_2 | 1.749 | +10.800 | +6,2 | 53,1% | 1,13 | 3.200 |
| 1:1 sem parcial | vrel_3 | 1.768 | +13.000 | +7,4 | 53,6% | 1,16 | 4.100 |
| 1:1 sem parcial | vrel_5 | 1.783 | +10.100 | +5,7 | 52,8% | 1,12 | 3.100 |
| 1:1 sem parcial | vpct_1 | 1.735 | +10.500 | +6,1 | 53,0% | 1,13 | 4.300 |
| 1:1 sem parcial | vpct_2 | 1.719 | +8.700 | +5,1 | 52,5% | 1,11 | 4.400 |
| 1:1 sem parcial | vpct_3 | 1.706 | +10.700 | +6,3 | 53,1% | 1,13 | 4.000 |
| 1:1 sem parcial | vpct_5 | 1.730 | +5.800 | +3,4 | 51,6% | 1,07 | 5.000 |
| 1:1 sem parcial | vmed_2 | 1.725 | +6.700 | +3,9 | 51,9% | 1,08 | 4.800 |
| 1:1 sem parcial | vmed_3 | 1.715 | +7.100 | +4,1 | 52,0% | 1,09 | 4.900 |
| 1:1 sem parcial | vmed_5 | 1.710 | +7.000 | +4,1 | 52,0% | 1,09 | 4.300 |

## Conclusao

- **O volume agressor nao filtra o Hull + pavios** em nenhuma das formas pedidas.
- **Os melhores cortes nao conversam entre lags vizinhos** -- assinatura de acaso.
- **Retomada com volume mede ao contrario, e so na venda.**
- **No PI o volume por candle carrega tempo.** Proximo passo, se houver: saldo agressor na retracao ou volume por minuto.

> Resultado bruto, um instrumento. Volume agressor, sem volume total nem numero de negocios.

Reproduzir: `python volume_agressor.py && python relatorio_volume.py`.
