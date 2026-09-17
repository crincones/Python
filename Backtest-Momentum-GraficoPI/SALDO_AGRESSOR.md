# Saldo de agressao como filtro do Hull + pavios

WINFUT, grafico de 20 PI, 50.611 candles, 132 pregoes (06/03/2026 a 14/09/2026). Resultado bruto. Grade interativa, curvas, MEP/MEN, duracao e trade a trade em saldo_agressor.html.

**S = agressao compradora - vendedora, espelhada pelo lado do trade** (positivo = a favor). Leituras: s_lag0/1/2 (saldo do sinal e de 1 e 2 barras antes, / media |S| de 20 barras), des_0 (S / volume agressor), sk_2/3/5 (soma das ultimas k barras), spct_1/2 ((S[i]-S[i-k]) / |S[i-k]|), smed_2/3/5 (S do sinal menos a media das k anteriores). Cortes q20 / mediana / q80, nos dois sentidos: 72 filtros.

## Resposta curta: nao

- Melhor da busca: **sk_5 abaixo da mediana**, ganho +3,5 pts; busca contra ruido p = 0,91 -- abaixo do acaso tipico.
- **O PI impoe o sinal do saldo**: desequilibrio do sinal com quintil de baixo em +0,03, saldo do ultimo candle da retracao com quintil de cima em -0,93, variacao % contra 1 barra sempre acima de +111%.
- Desequilibrio forte a favor no sinal mede pior (-2,8), nas 4 gestoes e nos dois lados, mas sem tercos estaveis.
- Escolhido antes de 06/08, o filtro nao ajuda ou piora o periodo seguinte.

## 1. Grade de ganho (pts por sinal), Hull + pavios

**1:3 com parcial**

| Leitura | > q20 | <= q20 | > mediana | <= mediana | > q80 | <= q80 |
|:--|--:|--:|--:|--:|--:|--:|
| s_lag0 | +0,5 | -2,0 | -0,3 | +0,3 | -5,5 | +1,3 |
| s_lag1 | +1,4 | -5,5 | -2,3 | +2,1 | -4,8 | +0,9 |
| s_lag2 | -0,2 | +1,0 | -3,0 | +3,3 | +1,3 | -0,3 |
| des_0 | +0,6 | -2,3 | -2,8 | +2,7 | +1,0 | -0,2 |
| sk_2 | +1,1 | -4,2 | -1,9 | +1,7 | -2,2 | +0,4 |
| sk_3 | +1,1 | -4,5 | -1,7 | +1,6 | -6,4 | +1,4 |
| sk_5 | -0,7 | +4,7 | -3,0 | +3,5 | +1,6 | -0,4 |
| spct_1 | +1,0 | -4,0 | -0,2 | +0,2 | -1,9 | +0,4 |
| spct_2 | +1,0 | -4,3 | +0,7 | -0,7 | -3,7 | +0,9 |
| smed_2 | +0,3 | -1,3 | +1,5 | -1,4 | -3,1 | +0,7 |
| smed_3 | +1,6 | -6,3 | +2,0 | -1,8 | +1,8 | -0,3 |
| smed_5 | +1,7 | -6,2 | +2,4 | -2,1 | -6,8 | +1,4 |

**1:3 sem parcial**

| Leitura | > q20 | <= q20 | > mediana | <= mediana | > q80 | <= q80 |
|:--|--:|--:|--:|--:|--:|--:|
| s_lag0 | +0,5 | -2,1 | -2,0 | +2,1 | -10,7 | +2,5 |
| s_lag1 | +2,3 | -8,8 | -2,3 | +2,1 | -10,0 | +2,0 |
| s_lag2 | -0,6 | +2,7 | -5,0 | +5,3 | +0,6 | -0,2 |
| des_0 | +0,4 | -1,7 | -4,1 | +3,9 | -0,5 | +0,1 |
| sk_2 | +1,2 | -4,3 | -4,2 | +3,8 | -7,3 | +1,4 |
| sk_3 | +0,5 | -1,8 | -3,9 | +3,8 | -12,1 | +2,6 |
| sk_5 | -0,9 | +5,7 | -3,3 | +3,9 | +3,1 | -0,9 |
| spct_1 | +1,6 | -6,4 | -1,2 | +1,1 | -6,3 | +1,3 |
| spct_2 | +2,1 | -8,5 | -0,6 | +0,6 | -6,6 | +1,6 |
| smed_2 | -0,3 | +1,3 | +2,5 | -2,4 | -6,2 | +1,5 |
| smed_3 | +1,3 | -5,2 | +1,9 | -1,6 | +4,2 | -0,8 |
| smed_5 | +1,4 | -5,3 | +1,9 | -1,8 | -9,6 | +2,0 |

**1:2 sem parcial**

| Leitura | > q20 | <= q20 | > mediana | <= mediana | > q80 | <= q80 |
|:--|--:|--:|--:|--:|--:|--:|
| s_lag0 | +0,5 | -2,2 | -2,0 | +2,0 | -7,1 | +1,6 |
| s_lag1 | +1,2 | -4,6 | -0,7 | +0,7 | -1,1 | +0,2 |
| s_lag2 | +0,1 | -0,6 | -1,3 | +1,4 | +5,7 | -1,4 |
| des_0 | +1,3 | -5,3 | -2,5 | +2,4 | -0,1 | +0,0 |
| sk_2 | +1,2 | -4,4 | -0,9 | +0,8 | -2,3 | +0,4 |
| sk_3 | +1,2 | -4,7 | -0,1 | +0,1 | -1,8 | +0,4 |
| sk_5 | -0,9 | +5,9 | -2,2 | +2,6 | +3,0 | -0,9 |
| spct_1 | +1,2 | -4,8 | -0,3 | +0,2 | -4,1 | +0,8 |
| spct_2 | +1,1 | -4,6 | +0,8 | -0,8 | -2,1 | +0,5 |
| smed_2 | -0,3 | +1,3 | -1,2 | +1,2 | -4,5 | +1,1 |
| smed_3 | +1,0 | -3,9 | +0,6 | -0,6 | +1,8 | -0,4 |
| smed_5 | +1,2 | -4,4 | +1,1 | -1,0 | -4,7 | +1,0 |

**1:1 sem parcial**

| Leitura | > q20 | <= q20 | > mediana | <= mediana | > q80 | <= q80 |
|:--|--:|--:|--:|--:|--:|--:|
| s_lag0 | +0,5 | -1,9 | +1,5 | -1,5 | -0,3 | +0,1 |
| s_lag1 | +0,5 | -2,1 | -2,3 | +2,1 | +0,5 | -0,1 |
| s_lag2 | +0,2 | -0,8 | -1,1 | +1,2 | +1,9 | -0,4 |
| des_0 | +0,7 | -2,8 | -1,5 | +1,4 | +2,5 | -0,6 |
| sk_2 | +1,1 | -4,1 | +0,3 | -0,3 | +2,8 | -0,5 |
| sk_3 | +1,8 | -7,1 | +0,6 | -0,5 | -0,8 | +0,2 |
| sk_5 | -0,6 | +3,7 | -2,7 | +3,1 | +0,1 | -0,0 |
| spct_1 | +0,4 | -1,7 | +0,9 | -0,8 | +2,6 | -0,5 |
| spct_2 | +0,0 | -0,1 | +1,9 | -1,9 | -0,9 | +0,2 |
| smed_2 | +0,9 | -3,9 | +0,4 | -0,4 | +0,0 | -0,0 |
| smed_3 | +1,9 | -7,4 | +2,2 | -1,9 | -0,6 | +0,1 |
| smed_5 | +1,9 | -7,2 | +2,8 | -2,5 | -4,1 | +0,8 |

## 2. Acima da mediana (Hull + pavios, 1:3 com parcial)

| Leitura | Sinais | Com | Sem | Ganho | p | T1 / T2 / T3 | Antes (sem filtro) | Compra | Venda | Pct | So 10h-15h |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|--:|--:|
| s_lag0 | 1765 | +8,6 | +9,2 | **-0,3** | 0,905 | +8 / +4 / +14 | +6,9 (+7,0) | +10,9 | +6,3 | 44 | +0,9 |
| s_lag1 | 1671 | +6,6 | +11,0 | **-2,3** | 0,283 | +3 / +12 / +6 | +7,4 (+7,0) | +6,4 | +6,8 | 14 | -4,5 |
| s_lag2 | 1812 | +5,9 | +12,2 | **-3,0** | 0,133 | +2 / +8 / +10 | +5,1 (+7,0) | +6,8 | +5,0 | 7 | +0,1 |
| des_0 | 1715 | +6,2 | +11,6 | **-2,8** | 0,200 | +5 / +6 / +7 | +4,9 (+7,0) | +8,4 | +3,9 | 9 | -3,8 |
| sk_2 | 1654 | +7,0 | +10,7 | **-1,9** | 0,371 | +1 / +10 / +12 | +6,2 (+7,0) | +9,8 | +4,2 | 19 | -4,9 |
| sk_3 | 1719 | +7,2 | +10,5 | **-1,7** | 0,463 | +5 / +13 / +5 | +8,2 (+7,0) | +7,8 | +6,7 | 23 | -0,5 |
| sk_5 | 1895 | +5,9 | +12,4 | **-3,0** | 0,122 | +5 / +8 / +6 | +8,0 (+7,0) | +7,1 | +4,8 | 6 | -5,3 |
| spct_1 | 1685 | +8,8 | +9,1 | **-0,2** | 0,939 | +9 / +7 / +10 | +7,9 (+7,0) | +11,8 | +5,6 | 48 | +0,9 |
| spct_2 | 1775 | +9,6 | +8,3 | **+0,7** | 0,754 | +8 / +10 / +11 | +9,2 (+7,0) | +11,7 | +7,4 | 60 | +2,3 |
| smed_2 | 1730 | +10,4 | +7,5 | **+1,5** | 0,502 | +6 / +6 / +19 | +7,8 (+7,0) | +11,9 | +8,8 | 74 | +1,1 |
| smed_3 | 1642 | +10,9 | +7,2 | **+2,0** | 0,376 | +2 / +12 / +19 | +7,6 (+7,0) | +15,0 | +6,8 | 82 | +2,8 |
| smed_5 | 1670 | +11,3 | +6,8 | **+2,4** | 0,298 | +6 / +8 / +21 | +7,5 (+7,0) | +13,1 | +9,4 | 85 | +3,9 |

## 3. Quintis (Hull + pavios, 1:3 com parcial)

| Leitura | Limites | Q1 | Q2 | Q3 | Q4 | Q5 |
|:--|:--|--:|--:|--:|--:|--:|
| s_lag0 | 0,14 / 0,39 / 0,61 / 0,89 | +6,6 | +8,6 | +11,8 | +11,9 | +5,8 |
| s_lag1 | -1,91 / -1,56 / -1,30 / -1,00 | +3,3 | +17,0 | +6,2 | +13,3 | +4,8 |
| s_lag2 | -1,41 / -0,97 / -0,59 / -0,27 | +9,1 | +16,9 | +9,2 | -0,9 | +10,3 |
| des_0 | 0,03 / 0,08 / 0,13 / 0,21 | +6,3 | +10,7 | +20,4 | -0,4 | +7,6 |
| sk_2 | -0,73 / -0,52 / -0,35 / -0,16 | +5,6 | +11,6 | +10,3 | +10,1 | +7,1 |
| sk_3 | -0,85 / -0,64 / -0,48 / -0,32 | +4,6 | +11,2 | +15,5 | +11,8 | +1,5 |
| sk_5 | -0,42 / -0,21 / -0,00 / 0,21 | +8,8 | +14,3 | +9,7 | +1,2 | +10,7 |
| spct_1 | 1,11 / 1,28 / 1,46 / 1,69 | +4,1 | +14,3 | +7,1 | +11,1 | +8,1 |
| spct_2 | 1,14 / 1,45 / 1,75 / 2,42 | +3,6 | +14,3 | +12,0 | +10,3 | +4,4 |
| smed_2 | 1,07 / 1,45 / 1,80 / 2,23 | +9,5 | -0,1 | +12,7 | +17,1 | +5,4 |
| smed_3 | 0,44 / 0,84 / 1,22 / 1,70 | +2,5 | +11,4 | +11,3 | +9,0 | +10,4 |
| smed_5 | 0,07 / 0,46 / 0,82 / 1,22 | +2,7 | +4,6 | +16,5 | +14,1 | +6,7 |

## 4. Busca contra ruido e escolha fora

| Conjunto | Gestao | Melhor | Ganho | t | ruido med | ruido p95 | p | Escolhida antes, medida depois | Escolhida T1+T2, medida T3 |
|:--|:--|:--|--:|--:|--:|--:|--:|:--|:--|
| cand | 1:3 com parcial | sk_5 abaixo da mediana | +3,5 | +1,12 | +1,61 | +2,47 | 0,91 | sk_5 no quintil de cima: 0,0 (sem filtro +15,8, n=151) | sk_5 no quintil de cima: +2,8 (sem filtro +14,6, n=214) |
| cand | 1:3 sem parcial | s_lag2 abaixo da mediana | +5,3 | +1,21 | +1,58 | +2,40 | 0,84 | smed_2 no quintil de baixo: -6,0 (sem filtro +21,2, n=150) | smed_2 no quintil de baixo: -4,2 (sem filtro +18,8, n=189) |
| cand | 1:2 sem parcial | s_lag2 no quintil de cima | +5,7 | +1,02 | +1,62 | +2,45 | 0,96 | s_lag2 no quintil de cima: +14,7 (sem filtro +13,6, n=163) | s_lag2 no quintil de cima: +13,2 (sem filtro +14,1, n=205) |
| cand | 1:1 sem parcial | sk_5 abaixo da mediana | +3,1 | +1,26 | +1,63 | +2,59 | 0,84 | spct_2 acima da mediana: +4,8 (sem filtro +10,4, n=375) | spct_2 acima da mediana: +7,5 (sem filtro +10,4, n=570) |
| h | 1:3 com parcial | sk_5 abaixo da mediana | +2,8 | +1,07 | +1,61 | +2,48 | 0,93 | spct_2 acima do quintil de baixo: +10,1 (sem filtro +11,0, n=781) | smed_3 no quintil de cima: +6,5 (sem filtro +10,9, n=309) |
| h | 1:3 sem parcial | sk_2 abaixo da mediana | +5,0 | +1,30 | +1,59 | +2,39 | 0,76 | smed_2 no quintil de baixo: -17,1 (sem filtro +13,4, n=199) | smed_2 no quintil de baixo: -9,6 (sem filtro +12,8, n=271) |
| h | 1:2 sem parcial | sk_5 no quintil de baixo | +4,3 | +0,88 | +1,62 | +2,44 | 0,99 | spct_2 acima do quintil de baixo: +6,8 (sem filtro +8,2, n=781) | s_lag2 no quintil de cima: +2,9 (sem filtro +8,9, n=275) |
| h | 1:1 sem parcial | smed_5 acima do quintil de baixo | +1,9 | +1,15 | +1,65 | +2,55 | 0,90 | spct_2 acima da mediana: +2,5 (sem filtro +8,5, n=483) | spct_2 acima da mediana: +6,1 (sem filtro +9,1, n=727) |

## 5. Ortogonalidade (correlacao de posto, Hull + pavios)

| Leitura | Inclinacao da Hull (ATR) | Hull - EMA 21 (ATR) | MACD (ATR) | Hora do sinal | Duracao do candle de sinal | Ritmo da ultima hora |
|:--|--:|--:|--:|--:|--:|--:|
| s_lag0 | -0,13 | -0,06 | -0,13 | +0,31 | +0,49 | -0,28 |
| s_lag1 | +0,08 | -0,00 | +0,05 | +0,15 | -0,03 | -0,26 |
| s_lag2 | +0,02 | -0,05 | -0,03 | -0,10 | -0,15 | +0,05 |
| des_0 | -0,02 | -0,03 | -0,04 | +0,12 | -0,10 | -0,16 |
| sk_2 | -0,01 | -0,06 | -0,05 | +0,31 | +0,29 | -0,40 |
| sk_3 | -0,01 | -0,07 | -0,06 | +0,18 | +0,13 | -0,27 |
| sk_5 | +0,12 | -0,16 | -0,03 | +0,08 | +0,08 | -0,11 |
| spct_1 | -0,09 | -0,08 | -0,11 | +0,34 | +0,43 | -0,35 |
| spct_2 | -0,09 | -0,08 | -0,12 | +0,21 | +0,32 | -0,22 |
| smed_2 | -0,12 | -0,01 | -0,08 | +0,19 | +0,39 | -0,12 |
| smed_3 | -0,13 | +0,03 | -0,06 | +0,21 | +0,35 | -0,16 |
| smed_5 | -0,23 | +0,06 | -0,11 | +0,23 | +0,37 | -0,20 |

## 6. Carteira (Hull + pavios)

| Gestao | Leitura acima da mediana | Trades | Pts | Pts/trade | Acerto | Fator | Rebaix. |
|:--|:--|--:|--:|--:|--:|--:|--:|
| 1:3 com parcial | sem filtro | 3.296 | +30.800 | +9,3 | 28,2% | 1,20 | 5.100 |
| 1:3 com parcial | s_lag0 | 1.697 | +14.350 | +8,5 | 27,8% | 1,18 | 3.950 |
| 1:3 com parcial | s_lag1 | 1.617 | +10.850 | +6,7 | 27,6% | 1,14 | 5.300 |
| 1:3 com parcial | s_lag2 | 1.746 | +11.950 | +6,8 | 26,9% | 1,15 | 4.600 |
| 1:3 com parcial | des_0 | 1.655 | +9.850 | +6,0 | 27,1% | 1,12 | 3.550 |
| 1:3 com parcial | sk_2 | 1.600 | +11.150 | +7,0 | 27,1% | 1,15 | 3.300 |
| 1:3 com parcial | sk_3 | 1.662 | +13.450 | +8,1 | 27,4% | 1,18 | 1.700 |
| 1:3 com parcial | sk_5 | 1.811 | +11.050 | +6,1 | 27,3% | 1,13 | 4.100 |
| 1:3 com parcial | spct_1 | 1.627 | +13.750 | +8,5 | 27,8% | 1,18 | 2.650 |
| 1:3 com parcial | spct_2 | 1.708 | +17.400 | +10,2 | 28,2% | 1,22 | 2.500 |
| 1:3 com parcial | smed_2 | 1.671 | +16.450 | +9,8 | 28,7% | 1,21 | 3.250 |
| 1:3 com parcial | smed_3 | 1.599 | +17.250 | +10,8 | 28,8% | 1,23 | 2.700 |
| 1:3 com parcial | smed_5 | 1.626 | +18.250 | +11,2 | 28,7% | 1,25 | 2.600 |
| 1:3 sem parcial | sem filtro | 3.296 | +40.100 | +12,2 | 28,2% | 1,17 | 6.600 |
| 1:3 sem parcial | s_lag0 | 1.697 | +16.500 | +9,7 | 27,7% | 1,13 | 5.800 |
| 1:3 sem parcial | s_lag1 | 1.617 | +15.500 | +9,6 | 27,5% | 1,13 | 6.100 |
| 1:3 sem parcial | s_lag2 | 1.746 | +13.400 | +7,7 | 26,9% | 1,11 | 4.800 |
| 1:3 sem parcial | des_0 | 1.655 | +12.300 | +7,4 | 27,0% | 1,10 | 4.600 |
| 1:3 sem parcial | sk_2 | 1.600 | +12.200 | +7,6 | 27,1% | 1,11 | 3.900 |
| 1:3 sem parcial | sk_3 | 1.662 | +14.700 | +8,8 | 27,3% | 1,12 | 3.100 |
| 1:3 sem parcial | sk_5 | 1.811 | +15.500 | +8,6 | 27,3% | 1,12 | 5.900 |
| 1:3 sem parcial | spct_1 | 1.627 | +16.700 | +10,3 | 27,8% | 1,14 | 3.500 |
| 1:3 sem parcial | spct_2 | 1.708 | +20.300 | +11,9 | 28,1% | 1,17 | 3.900 |
| 1:3 sem parcial | smed_2 | 1.671 | +22.700 | +13,6 | 28,7% | 1,19 | 4.200 |
| 1:3 sem parcial | smed_3 | 1.599 | +22.000 | +13,8 | 28,7% | 1,19 | 3.700 |
| 1:3 sem parcial | smed_5 | 1.626 | +22.200 | +13,7 | 28,6% | 1,19 | 3.600 |
| 1:2 sem parcial | sem filtro | 3.478 | +32.000 | +9,2 | 36,4% | 1,15 | 5.800 |
| 1:2 sem parcial | s_lag0 | 1.755 | +12.200 | +7,0 | 35,7% | 1,11 | 5.400 |
| 1:2 sem parcial | s_lag1 | 1.661 | +14.300 | +8,6 | 36,2% | 1,14 | 5.200 |
| 1:2 sem parcial | s_lag2 | 1.805 | +14.100 | +7,8 | 35,8% | 1,12 | 4.300 |
| 1:2 sem parcial | des_0 | 1.705 | +11.600 | +6,8 | 35,6% | 1,11 | 4.700 |
| 1:2 sem parcial | sk_2 | 1.644 | +13.600 | +8,3 | 36,1% | 1,13 | 3.300 |
| 1:2 sem parcial | sk_3 | 1.712 | +16.000 | +9,3 | 36,4% | 1,15 | 2.000 |
| 1:2 sem parcial | sk_5 | 1.891 | +13.100 | +6,9 | 35,6% | 1,11 | 4.200 |
| 1:2 sem parcial | spct_1 | 1.678 | +14.600 | +8,7 | 36,3% | 1,14 | 4.400 |
| 1:2 sem parcial | spct_2 | 1.766 | +17.700 | +10,0 | 36,7% | 1,16 | 3.900 |
| 1:2 sem parcial | smed_2 | 1.720 | +13.300 | +7,7 | 36,0% | 1,12 | 3.500 |
| 1:2 sem parcial | smed_3 | 1.635 | +15.700 | +9,6 | 36,6% | 1,15 | 2.900 |
| 1:2 sem parcial | smed_5 | 1.665 | +16.900 | +10,2 | 36,8% | 1,16 | 3.600 |
| 1:1 sem parcial | sem filtro | 3.508 | +21.900 | +6,2 | 53,0% | 1,13 | 4.900 |
| 1:1 sem parcial | s_lag0 | 1.765 | +13.600 | +7,7 | 53,8% | 1,17 | 2.500 |
| 1:1 sem parcial | s_lag1 | 1.671 | +6.600 | +3,9 | 51,8% | 1,08 | 5.300 |
| 1:1 sem parcial | s_lag2 | 1.812 | +9.300 | +5,1 | 52,4% | 1,11 | 4.900 |
| 1:1 sem parcial | des_0 | 1.715 | +8.200 | +4,8 | 52,3% | 1,10 | 3.000 |
| 1:1 sem parcial | sk_2 | 1.654 | +10.900 | +6,6 | 53,1% | 1,14 | 3.300 |
| 1:1 sem parcial | sk_3 | 1.719 | +11.700 | +6,8 | 53,2% | 1,15 | 1.700 |
| 1:1 sem parcial | sk_5 | 1.895 | +6.800 | +3,6 | 51,7% | 1,07 | 3.000 |
| 1:1 sem parcial | spct_1 | 1.685 | +12.000 | +7,1 | 53,5% | 1,15 | 2.000 |
| 1:1 sem parcial | spct_2 | 1.775 | +14.400 | +8,1 | 54,0% | 1,18 | 1.700 |
| 1:1 sem parcial | smed_2 | 1.730 | +11.500 | +6,6 | 53,3% | 1,14 | 3.000 |
| 1:1 sem parcial | smed_3 | 1.642 | +13.800 | +8,4 | 54,2% | 1,18 | 2.400 |
| 1:1 sem parcial | smed_5 | 1.670 | +15.100 | +9,0 | 54,5% | 1,20 | 2.200 |
## Conclusao

- **O saldo de agressao nao filtra o Hull + pavios** em nenhuma das formas pedidas.
- **O sinal do saldo no par retracao + continuacao e imposto pelo candle de PI**; o resto nao carrega informacao.
- **Fluxo, no Hull, esta encerrado**: volume e saldo nao acrescentam. Candidato vivo: horario (nao operar antes das 10h).

> Resultado bruto, um instrumento. Agressao do log do robo.

Reproduzir: python saldo_agressor.py && python relatorio_saldo.py
