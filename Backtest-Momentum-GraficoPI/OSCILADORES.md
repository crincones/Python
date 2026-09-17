# MACD, estocastico lento e IFR como filtro do Hull + pavios

WINFUT, grafico de 20 PI, 50.611 candles, 132 pregoes (06/03/2026 a 14/09/2026). Resultado bruto. Graficos, curvas, MEP/MEN, duracao e trade a trade (com os tres osciladores) em `osciladores.html`.

**Osciladores** (padrao do Profit): MACD 12/26/9, estocastico lento 14,3,3, IFR 14. Lidos no fechamento do candle de sinal; na venda, espelhados.

**Sinais**: Hull + 2 a 4 (4.700) e Hull + pavios -- 2 a 3 candles e pavio do fechamento ate 10% (3.703).

## Resposta curta: nao

- Hull + pavios sem filtro: +8,7 pts por sinal (1:3 com parcial).
- Busca (16 regras x 2 sentidos) contra resultados embaralhados: melhor t = +0,97, ruido mediana +1,12, p95 +2,11; p = 0,66.
- 5 das 11 regras classicas (E1, E2, E3, I2, I3) aceitam menos de 5% ou mais de 95% dos sinais: depois de 2 a 4 candles contra, o estocastico lento ainda esta caindo e os osciladores quase nunca chegam aos extremos.
- IFR no quintil mais alto (+4,5) melhora nos tres tercos, nos dois blocos e nos dois lados; MACD acima de zero (+1,6) so nos periodos fracos e na compra. Os dois abaixo do detectavel (+5,8 pts) e sem passar na busca.
- Histograma do MACD subindo no sinal mede pior (-8,9, p = 0,030 isolado), sem passar na busca.
- %K abaixo de 20 na retracao: +35,1 em 32 sinais, sem plato de parametro.
- Nao ha plano novo; o plano provisorio do Hull continua sem oscilador.

## 1. Cada regra (Hull + pavios, fechamento)

**1:3 com parcial** (sem filtro: +8,7)

| | Regra | Sinais | Com | Sem | Ganho | p | T1 / T2 / T3 | Antes (sem filtro) | Compra | Venda | Pct |
|:--|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|--:|
| M1 | MACD acima de zero | 2904 (78%) | +10,2 | +3,0 | **+1,6** | 0,167 | +7 / +10 / +14 | +9,3 (+6,8) | +13,1 | +7,5 | 93 |
| M2 | MACD acima da linha de sinal | 2437 (66%) | +7,8 | +10,4 | **-0,9** | 0,546 | +1 / +7 / +18 | +4,4 (+6,8) | +5,9 | +9,6 | 28 |
| M3 | Histograma do MACD subindo | 726 (20%) | -0,3 | +10,8 | **-8,9** | 0,030 | -6 / -2 / +10 | -1,4 (+6,8) | -0,3 | -0,3 | 1 |
| M4 | MACD acima de zero e histograma subindo | 388 (10%) | +1,7 | +9,5 | **-7,0** | 0,252 | -1 / +7 / +1 | +8,0 (+6,8) | +8,8 | -5,0 | 12 |
| E1 | %K acima de %D | 19 (1%) | - | - | - | - | - | - | - | - | - |
| E2 | %K cruzou %D para cima no sinal | 4 (0%) | - | - | - | - | - | - | - | - | - |
| E3 | %K abaixo de 20 na retracao | 32 (1%) | +43,8 | +8,4 | **+35,1** | 0,132 | +57 / +45 / +14 | +52,0 (+6,8) | +40,0 | +47,1 | 93 |
| E4 | %K abaixo de 80 no sinal | 3509 (95%) | +8,5 | +11,9 | **-0,2** | 0,727 | +5 / +9 / +13 | +7,0 (+6,8) | +9,5 | +7,5 | 35 |
| I1 | IFR acima de 50 | 3047 (82%) | +9,1 | +6,5 | **+0,5** | 0,648 | +7 / +10 / +12 | +8,5 (+6,8) | +11,9 | +6,5 | 69 |
| I2 | IFR abaixo de 40 na retracao | 35 (1%) | -17,1 | +8,9 | **-25,8** | 0,220 | -50 / -10 / +8 | -25,0 (+6,8) | -33,3 | -8,7 | 9 |
| I3 | IFR abaixo de 70 no sinal | 3678 (99%) | +8,5 | +36,0 | **-0,2** | 0,296 | +4 / +9 / +14 | +6,7 (+6,8) | +9,6 | +7,4 | 12 |
| M5 | Histograma no quintil mais alto | 797 (22%) | +4,6 | +9,8 | **-4,0** | 0,306 | -3 / +14 / +6 | +5,2 (+6,8) | +4,0 | +5,2 | 15 |
| E5 | Menor %K da retracao no quintil mais baixo | 597 (16%) | +2,7 | +9,8 | **-6,0** | 0,197 | +7 / +0 / -2 | +2,1 (+6,8) | +4,8 | +0,7 | 10 |
| E6 | %K - %D no quintil mais alto | 762 (21%) | +10,2 | +8,3 | **+1,6** | 0,679 | -1 / +7 / +26 | +2,4 (+6,8) | +11,7 | +8,7 | 64 |
| I4 | Menor IFR da retracao no quintil mais baixo | 679 (18%) | +5,8 | +9,3 | **-2,9** | 0,515 | -7 / +6 / +24 | -2,0 (+6,8) | +0,1 | +11,4 | 26 |
| I5 | IFR no quintil mais alto | 751 (20%) | +13,2 | +7,5 | **+4,5** | 0,294 | +8 / +13 / +21 | +9,6 (+6,8) | +14,4 | +12,1 | 86 |

**1:3 sem parcial** (sem filtro: +11,2)

| | Regra | Sinais | Com | Sem | Ganho | p | T1 / T2 / T3 | Antes (sem filtro) | Compra | Venda | Pct |
|:--|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|--:|
| M1 | MACD acima de zero | 2904 (78%) | +13,1 | +4,5 | **+1,9** | 0,212 | +8 / +15 / +18 | +11,7 (+8,6) | +17,1 | +9,3 | 89 |
| M2 | MACD acima da linha de sinal | 2437 (66%) | +11,2 | +11,4 | **-0,1** | 0,966 | +2 / +10 / +26 | +6,5 (+8,6) | +9,8 | +12,6 | 50 |
| M3 | Histograma do MACD subindo | 726 (20%) | -0,6 | +14,1 | **-11,8** | 0,046 | -12 / +1 / +15 | -2,6 (+8,6) | +1,4 | -2,5 | 2 |
| M4 | MACD acima de zero e histograma subindo | 388 (10%) | +2,8 | +12,2 | **-8,4** | 0,338 | -3 / +15 / +3 | +11,0 (+8,6) | +12,2 | -6,0 | 15 |
| E1 | %K acima de %D | 19 (1%) | - | - | - | - | - | - | - | - | - |
| E2 | %K cruzou %D para cima no sinal | 4 (0%) | - | - | - | - | - | - | - | - | - |
| E3 | %K abaixo de 20 na retracao | 32 (1%) | +37,5 | +11,0 | **+26,3** | 0,419 | +71 / +45 / -43 | +60,0 (+8,6) | +33,3 | +41,2 | 76 |
| E4 | %K abaixo de 80 no sinal | 3509 (95%) | +11,0 | +16,0 | **-0,3** | 0,702 | +6 / +13 / +17 | +8,9 (+8,6) | +13,0 | +9,0 | 34 |
| I1 | IFR acima de 50 | 3047 (82%) | +12,1 | +7,2 | **+0,9** | 0,531 | +8 / +14 / +16 | +11,1 (+8,6) | +16,0 | +8,4 | 73 |
| I2 | IFR abaixo de 40 na retracao | 35 (1%) | -31,4 | +11,6 | **-42,7** | 0,182 | -67 / -20 / -8 | -33,3 (+8,6) | -33,3 | -30,4 | 5 |
| I3 | IFR abaixo de 70 no sinal | 3678 (99%) | +11,0 | +44,0 | **-0,2** | 0,371 | +5 / +13 / +18 | +8,5 (+8,6) | +13,6 | +8,5 | 13 |
| M5 | Histograma no quintil mais alto | 797 (22%) | +7,5 | +12,3 | **-3,7** | 0,509 | +2 / +17 / +6 | +8,8 (+8,6) | +11,6 | +3,5 | 24 |
| E5 | Menor %K da retracao no quintil mais baixo | 597 (16%) | +2,8 | +12,8 | **-8,4** | 0,221 | +10 / +1 / -7 | +3,5 (+8,6) | +7,9 | -2,0 | 10 |
| E6 | %K - %D no quintil mais alto | 762 (21%) | +13,3 | +10,7 | **+2,0** | 0,736 | +0 / +8 / +33 | +1,9 (+8,6) | +17,8 | +8,7 | 62 |
| I4 | Menor IFR da retracao no quintil mais baixo | 679 (18%) | +5,9 | +12,4 | **-5,3** | 0,372 | -13 / +9 / +30 | -5,1 (+8,6) | +2,1 | +9,7 | 20 |
| I5 | IFR no quintil mais alto | 751 (20%) | +18,5 | +9,4 | **+7,3** | 0,223 | +8 / +22 / +28 | +14,8 (+8,6) | +24,1 | +13,6 | 88 |

**1:2 sem parcial** (sem filtro: +8,6)

| | Regra | Sinais | Com | Sem | Ganho | p | T1 / T2 / T3 | Antes (sem filtro) | Compra | Venda | Pct |
|:--|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|--:|
| M1 | MACD acima de zero | 2904 (78%) | +10,7 | +0,9 | **+2,1** | 0,087 | +11 / +5 / +16 | +10,0 (+7,2) | +14,3 | +7,3 | 96 |
| M2 | MACD acima da linha de sinal | 2437 (66%) | +6,7 | +12,1 | **-1,8** | 0,285 | +4 / +2 / +16 | +4,3 (+7,2) | +6,0 | +7,5 | 14 |
| M3 | Histograma do MACD subindo | 726 (20%) | -0,7 | +10,8 | **-9,2** | 0,058 | -2 / -9 / +9 | -1,9 (+7,2) | +0,8 | -2,2 | 2 |
| M4 | MACD acima de zero e histograma subindo | 388 (10%) | +5,4 | +8,9 | **-3,1** | 0,648 | +6 / -1 / +10 | +9,1 (+7,2) | +11,2 | 0,0 | 29 |
| E1 | %K acima de %D | 19 (1%) | - | - | - | - | - | - | - | - | - |
| E2 | %K cruzou %D para cima no sinal | 4 (0%) | - | - | - | - | - | - | - | - | - |
| E3 | %K abaixo de 20 na retracao | 32 (1%) | +12,5 | +8,5 | **+3,9** | 0,985 | +50 / +9 / -57 | +32,0 (+7,2) | +20,0 | +5,9 | 50 |
| E4 | %K abaixo de 80 no sinal | 3509 (95%) | +8,5 | +8,8 | **-0,0** | 1,000 | +8 / +5 / +13 | +7,5 (+7,2) | +10,0 | +7,1 | 48 |
| I1 | IFR acima de 50 | 3047 (82%) | +9,1 | +6,1 | **+0,5** | 0,634 | +10 / +5 / +13 | +8,8 (+7,2) | +11,8 | +6,5 | 68 |
| I2 | IFR abaixo de 40 na retracao | 35 (1%) | -40,0 | +9,0 | **-48,6** | 0,051 | -75 / -10 / -31 | -37,5 (+7,2) | -50,0 | -34,8 | 1 |
| I3 | IFR abaixo de 70 no sinal | 3678 (99%) | +8,3 | +44,0 | **-0,2** | 0,289 | +7 / +5 / +13 | +7,1 (+7,2) | +10,0 | +6,7 | 8 |
| M5 | Histograma no quintil mais alto | 797 (22%) | +5,3 | +9,5 | **-3,3** | 0,460 | +2 / +9 / +6 | +7,5 (+7,2) | +9,6 | +1,0 | 22 |
| E5 | Menor %K da retracao no quintil mais baixo | 597 (16%) | +2,2 | +9,8 | **-6,4** | 0,234 | +11 / -2 / -6 | +3,7 (+7,2) | +6,9 | -2,3 | 12 |
| E6 | %K - %D no quintil mais alto | 762 (21%) | +7,5 | +8,8 | **-1,1** | 0,821 | -1 / 0 / +24 | -0,5 (+7,2) | +13,6 | +1,3 | 40 |
| I4 | Menor IFR da retracao no quintil mais baixo | 679 (18%) | +5,6 | +9,2 | **-3,0** | 0,548 | -3 / +4 / +20 | -0,6 (+7,2) | +2,7 | +8,5 | 28 |
| I5 | IFR no quintil mais alto | 751 (20%) | +12,1 | +7,7 | **+3,6** | 0,454 | +8 / +5 / +23 | +7,2 (+7,2) | +17,0 | +7,8 | 76 |

**1:1 sem parcial** (sem filtro: +6,1)

| | Regra | Sinais | Com | Sem | Ganho | p | T1 / T2 / T3 | Antes (sem filtro) | Compra | Venda | Pct |
|:--|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|--:|
| M1 | MACD acima de zero | 2904 (78%) | +7,4 | +1,5 | **+1,3** | 0,135 | +6 / +6 / +11 | +7,0 (+5,0) | +9,2 | +5,6 | 93 |
| M2 | MACD acima da linha de sinal | 2437 (66%) | +4,3 | +9,5 | **-1,8** | 0,139 | +1 / +3 / +10 | +2,3 (+5,0) | +2,1 | +6,6 | 7 |
| M3 | Histograma do MACD subindo | 726 (20%) | 0,0 | +7,6 | **-6,1** | 0,068 | -1 / -4 / +5 | -0,2 (+5,0) | -1,9 | +1,9 | 3 |
| M4 | MACD acima de zero e histograma subindo | 388 (10%) | +0,5 | +6,8 | **-5,6** | 0,252 | +1 / 0 / 0 | +5,0 (+5,0) | +5,3 | -4,0 | 11 |
| E1 | %K acima de %D | 19 (1%) | - | - | - | - | - | - | - | - | - |
| E2 | %K cruzou %D para cima no sinal | 4 (0%) | - | - | - | - | - | - | - | - | - |
| E3 | %K abaixo de 20 na retracao | 32 (1%) | +50,0 | +5,7 | **+43,9** | 0,017 | +43 / +45 / +71 | +44,0 (+5,0) | +46,7 | +52,9 | 99 |
| E4 | %K abaixo de 80 no sinal | 3509 (95%) | +6,0 | +7,7 | **-0,1** | 0,819 | +4 / +5 / +10 | +5,0 (+5,0) | +6,0 | +6,0 | 39 |
| I1 | IFR acima de 50 | 3047 (82%) | +6,2 | +5,8 | **+0,1** | 0,933 | +5 / +5 / +9 | +5,8 (+5,0) | +7,7 | +4,6 | 52 |
| I2 | IFR abaixo de 40 na retracao | 35 (1%) | -2,9 | +6,2 | **-9,0** | 0,602 | -33 / 0 / +23 | -16,7 (+5,0) | -33,3 | +13,0 | 24 |
| I3 | IFR abaixo de 70 no sinal | 3678 (99%) | +6,0 | +28,0 | **-0,1** | 0,319 | +4 / +5 / +10 | +4,9 (+5,0) | +5,7 | +6,2 | 9 |
| M5 | Histograma no quintil mais alto | 797 (22%) | +1,8 | +7,3 | **-4,3** | 0,176 | -8 / +11 / +6 | +1,6 (+5,0) | -3,5 | +7,0 | 8 |
| E5 | Menor %K da retracao no quintil mais baixo | 597 (16%) | +2,5 | +6,8 | **-3,6** | 0,336 | +4 / -1 / +3 | +0,6 (+5,0) | +1,7 | +3,3 | 17 |
| E6 | %K - %D no quintil mais alto | 762 (21%) | +7,2 | +5,8 | **+1,1** | 0,727 | -2 / +7 / +19 | +2,9 (+5,0) | +5,7 | +8,7 | 63 |
| I4 | Menor IFR da retracao no quintil mais baixo | 679 (18%) | +5,7 | +6,2 | **-0,4** | 0,932 | -1 / +3 / +18 | +1,1 (+5,0) | -1,8 | +13,2 | 45 |
| I5 | IFR no quintil mais alto | 751 (20%) | +7,9 | +5,7 | **+1,8** | 0,576 | +7 / +3 / +13 | +4,5 (+5,0) | +4,8 | +10,6 | 70 |

**Hull + 2 a 4, 1:3 com parcial**

| | Sinais | Com | Ganho | p | T1 / T2 / T3 | Antes |
|:--|--:|--:|--:|--:|:--|--:|
| M1 | 3703 | +8,9 | +1,4 | 0,118 | +9 / +8 / +10 | +9,2 |
| M2 | 2923 | +7,0 | -0,4 | 0,763 | +1 / +6 / +17 | +3,9 |
| M3 | 825 | -2,1 | -9,6 | 0,015 | -8 / -4 / +8 | -2,3 |
| M4 | 448 | 0,0 | -7,5 | 0,191 | -3 / +6 / -1 | +7,4 |
| E1 | 25 | -8,0 | -15,5 | 0,568 | +8 / +29 / -100 | 0,0 |
| E3 | 70 | +37,1 | +29,7 | 0,050 | +52 / +32 / +20 | +40,4 |
| E4 | 4449 | +7,7 | +0,2 | 0,652 | +6 / +6 / +11 | +7,0 |
| I1 | 3784 | +8,1 | +0,6 | 0,513 | +8 / +7 / +9 | +8,3 |
| I2 | 56 | -10,7 | -18,2 | 0,294 | -50 / +12 / +17 | -20,0 |
| I3 | 4653 | +7,3 | -0,2 | 0,353 | +5 / +7 / +10 | +6,4 |
| M5 | 940 | +3,9 | -3,5 | 0,336 | -1 / +9 / +6 | +3,8 |
| E5 | 940 | +0,5 | -7,0 | 0,060 | +6 / -8 / -0 | -0,5 |
| E6 | 940 | +8,1 | +0,6 | 0,875 | -1 / +6 / +20 | +2,3 |
| I4 | 940 | +4,7 | -2,8 | 0,452 | -2 / +1 / +18 | -1,1 |
| I5 | 940 | +12,4 | +5,0 | 0,177 | +11 / +10 / +17 | +10,9 |

## 2. As leituras em quintis (Hull + pavios, 1:3 com parcial)

| Leitura | Limites | Q1 | Q2 | Q3 | Q4 | Q5 |
|:--|:--|--:|--:|--:|--:|--:|
| MACD / ATR (a favor) | -0,03 / 0,30 / 0,59 / 0,95 | +3,4 | +3,7 | +10,3 | +9,8 | +16,2 |
| Histograma / ATR (a favor) | -0,07 / 0,02 / 0,10 / 0,20 | +10,9 | +9,5 | +5,7 | +13,8 | +3,4 |
| %K lento no sinal (a favor) | 43,70 / 56,17 / 64,60 / 72,52 | +5,1 | +9,3 | +7,2 | +9,3 | +12,6 |
| %K - %D (a favor) | -11,01 / -9,25 / -7,84 / -6,41 | +9,0 | +4,7 | +9,9 | +9,7 | +10,0 |
| Menor %K da retracao (a favor) | 51,58 / 63,64 / 72,15 / 79,20 | +4,6 | +10,5 | +3,9 | +16,0 | +8,4 |
| IFR no sinal (a favor) | 50,36 / 53,16 / 55,60 / 58,99 | +5,6 | +3,8 | +5,5 | +15,9 | +12,6 |
| Menor IFR da retracao (a favor) | 46,56 / 49,57 / 52,21 / 55,85 | +5,7 | +4,1 | +4,7 | +15,9 | +13,0 |

## 3. Busca contra ruido e escolha fora

| Conjunto | Gestao | Melhor | t | ruido med | ruido p95 | p | Escolhida antes, medida depois | Escolhida T1+T2, medida T3 |
|:--|:--|:--|--:|--:|--:|--:|:--|:--|
| cand | 1:3 com parcial | I5 | +0,97 | +1,12 | +2,11 | 0,66 | M2 (nao) +7,0 (sem filtro +15,8) | M2 (nao) +8,4 (sem filtro +14,6) |
| cand | 1:3 sem parcial | I5 | +1,09 | +1,17 | +2,08 | 0,58 | I4 (nao) +15,5 (sem filtro +21,2) | M3 (nao) +19,7 (sem filtro +18,8) |
| cand | 1:2 sem parcial | M2 (nao) | +0,87 | +1,17 | +2,09 | 0,79 | M2 (nao) +9,3 (sem filtro +13,6) | M2 (nao) +10,4 (sem filtro +14,1) |
| cand | 1:1 sem parcial | M2 (nao) | +1,21 | +1,22 | +2,16 | 0,51 | M2 (nao) +7,0 (sem filtro +10,4) | M2 (nao) +10,4 (sem filtro +10,4) |
| h | 1:3 com parcial | I5 | +1,21 | +1,18 | +2,20 | 0,47 | M2 (nao) -0,8 (sem filtro +11,0) | M2 (nao) +2,3 (sem filtro +11,0) |
| h | 1:3 sem parcial | I5 | +1,20 | +1,22 | +2,12 | 0,52 | I5 +20,7 (sem filtro +13,6) | M2 (nao) -1,8 (sem filtro +13,0) |
| h | 1:2 sem parcial | M3 (nao) | +1,01 | +1,22 | +2,19 | 0,65 | M2 (nao) -1,3 (sem filtro +8,3) | M2 (nao) +1,4 (sem filtro +9,0) |
| h | 1:1 sem parcial | M3 (nao) | +1,02 | +1,18 | +2,24 | 0,63 | M2 (nao) +2,0 (sem filtro +8,5) | M2 (nao) +6,5 (sem filtro +9,0) |

## 4. Vizinhanca dos parametros (ganho, Hull + pavios, 1:3 com parcial)

| Regra | Parametros | Sinais | Ganho |
|:--|:--|--:|--:|
| M1 | (8, 17, 9) | 3158 | +0,5 |
| M2 | (8, 17, 9) | 1693 | -4,2 |
| M3 | (8, 17, 9) | 1241 | -3,4 |
| M4 | (8, 17, 9) | 897 | -1,6 |
| M5 | (8, 17, 9) | 801 | -5,4 |
| M1 | (12, 26, 9) (padrao) | 2904 | +1,6 |
| M2 | (12, 26, 9) (padrao) | 2437 | -0,9 |
| M3 | (12, 26, 9) (padrao) | 726 | -8,9 |
| M4 | (12, 26, 9) (padrao) | 388 | -7,0 |
| M5 | (12, 26, 9) (padrao) | 797 | -4,0 |
| M1 | (19, 39, 9) | 2568 | +3,6 |
| M2 | (19, 39, 9) | 2995 | -0,4 |
| M3 | (19, 39, 9) | 904 | -5,7 |
| M4 | (19, 39, 9) | 339 | -8,1 |
| M5 | (19, 39, 9) | 783 | +2,8 |
| E1 | (8, 3, 3) | 32 | +28,8 |
| E2 | (8, 3, 3) | 20 | +41,3 |
| E3 | (8, 3, 3) | 216 | -0,8 |
| E4 | (8, 3, 3) | 3690 | +0,0 |
| E5 | (8, 3, 3) | 554 | -4,5 |
| E6 | (8, 3, 3) | 685 | -2,0 |
| E1 | (14, 3, 3) (padrao) | 19 | - |
| E2 | (14, 3, 3) (padrao) | 4 | - |
| E3 | (14, 3, 3) (padrao) | 32 | +35,1 |
| E4 | (14, 3, 3) (padrao) | 3509 | -0,2 |
| E5 | (14, 3, 3) (padrao) | 597 | -6,0 |
| E6 | (14, 3, 3) (padrao) | 762 | +1,6 |
| E1 | (21, 3, 3) | 47 | +14,7 |
| E2 | (21, 3, 3) | 11 | - |
| E3 | (21, 3, 3) | 7 | - |
| E4 | (21, 3, 3) | 3238 | -0,3 |
| E5 | (21, 3, 3) | 622 | -0,5 |
| E6 | (21, 3, 3) | 749 | +4,9 |
| I1 | 9 | 3134 | +1,0 |
| I2 | 9 | 99 | +8,5 |
| I3 | 9 | 3669 | -0,0 |
| I4 | 9 | 584 | -7,4 |
| I5 | 9 | 774 | +3,5 |
| I1 | 14 (padrao) | 3047 | +0,5 |
| I2 | 14 (padrao) | 35 | -25,8 |
| I3 | 14 (padrao) | 3678 | -0,2 |
| I4 | 14 (padrao) | 679 | -2,9 |
| I5 | 14 (padrao) | 751 | +4,5 |
| I1 | 21 | 2862 | +1,7 |
| I2 | 21 | 39 | -26,6 |
| I3 | 21 | 3686 | -0,0 |
| I4 | 21 | 715 | -2,8 |
| I5 | 21 | 738 | +7,5 |

## 5. Carteira, uma posicao por vez (Hull + pavios)

| Gestao | Regra | Trades | Pts | Pts/trade | Acerto | Fator | Rebaix. | Antes (pts/trade) | MC lucro |
|:--|:--|--:|--:|--:|--:|--:|--:|--:|--:|
| 1:3 com parcial | sem filtro | 3.479 | +31.700 | +9,1 | 28,1% | 1,20 | 5.100 | +7,0 | 100% |
| 1:3 com parcial | M1 | 2.753 | +29.600 | +10,8 | 28,6% | 1,23 | 3.300 | +9,6 | 100% |
| 1:3 com parcial | M2 | 2.342 | +17.400 | +7,4 | 27,8% | 1,16 | 3.450 | +3,9 | 100% |
| 1:3 com parcial | M3 | 706 | +300 | +0,4 | 25,5% | 1,01 | 3.900 | -0,7 | 54% |
| 1:3 com parcial | M4 | 376 | +850 | +2,3 | 26,6% | 1,05 | 2.200 | +8,6 | 64% |
| 1:3 com parcial | E3 | 32 | +1.400 | +43,8 | 34,4% | 2,75 | 200 | +52,0 | 98% |
| 1:3 com parcial | E4 | 3.295 | +30.000 | +9,1 | 28,1% | 1,19 | 5.300 | +7,3 | 100% |
| 1:3 com parcial | I1 | 2.890 | +27.350 | +9,5 | 28,2% | 1,20 | 3.700 | +8,5 | 100% |
| 1:3 com parcial | I2 | 35 | -600 | -17,1 | 17,1% | 0,67 | 800 | -25,0 | 15% |
| 1:3 com parcial | I3 | 3.455 | +30.800 | +8,9 | 28,0% | 1,19 | 5.200 | +6,9 | 100% |
| 1:3 com parcial | M5 | 787 | +4.000 | +5,1 | 27,1% | 1,10 | 2.200 | +5,4 | 87% |
| 1:3 com parcial | E5 | 586 | +1.700 | +2,9 | 26,1% | 1,06 | 2.800 | +2,3 | 71% |
| 1:3 com parcial | E6 | 759 | +7.800 | +10,3 | 28,2% | 1,22 | 2.100 | +2,7 | 99% |
| 1:3 com parcial | I4 | 671 | +3.650 | +5,4 | 26,7% | 1,12 | 3.650 | -2,2 | 87% |
| 1:3 com parcial | I5 | 728 | +10.000 | +13,7 | 29,7% | 1,30 | 2.100 | +10,2 | 100% |
| 1:3 sem parcial | sem filtro | 3.479 | +41.400 | +11,9 | 28,1% | 1,17 | 6.600 | +9,2 | 100% |
| 1:3 sem parcial | M1 | 2.753 | +38.100 | +13,8 | 28,6% | 1,19 | 3.900 | +12,2 | 100% |
| 1:3 sem parcial | M2 | 2.342 | +25.100 | +10,7 | 27,8% | 1,15 | 4.600 | +6,1 | 100% |
| 1:3 sem parcial | M3 | 706 | +400 | +0,6 | 25,4% | 1,01 | 5.700 | -1,6 | 53% |
| 1:3 sem parcial | M4 | 376 | +1.500 | +4,0 | 26,3% | 1,05 | 3.200 | +12,0 | 67% |
| 1:3 sem parcial | E3 | 32 | +1.200 | +37,5 | 34,4% | 1,57 | 500 | +60,0 | 84% |
| 1:3 sem parcial | E4 | 3.295 | +39.300 | +11,9 | 28,1% | 1,17 | 7.100 | +9,7 | 100% |
| 1:3 sem parcial | I1 | 2.890 | +36.400 | +12,6 | 28,2% | 1,18 | 4.200 | +11,4 | 100% |
| 1:3 sem parcial | I2 | 35 | -1.100 | -31,4 | 17,1% | 0,62 | 1.400 | -33,3 | 12% |
| 1:3 sem parcial | I3 | 3.455 | +40.200 | +11,6 | 28,0% | 1,16 | 6.800 | +9,0 | 100% |
| 1:3 sem parcial | M5 | 787 | +6.200 | +7,9 | 27,1% | 1,11 | 2.700 | +8,9 | 89% |
| 1:3 sem parcial | E5 | 586 | +2.000 | +3,4 | 25,9% | 1,05 | 3.800 | +4,3 | 67% |
| 1:3 sem parcial | E6 | 759 | +10.000 | +13,2 | 28,2% | 1,18 | 3.800 | +2,2 | 98% |
| 1:3 sem parcial | I4 | 671 | +3.600 | +5,4 | 26,5% | 1,07 | 6.000 | -5,3 | 78% |
| 1:3 sem parcial | I5 | 728 | +13.800 | +19,0 | 29,7% | 1,27 | 2.700 | +15,2 | 100% |
| 1:2 sem parcial | sem filtro | 3.673 | +32.000 | +8,7 | 36,2% | 1,14 | 5.800 | +7,5 | 100% |
| 1:2 sem parcial | M1 | 2.904 | +31.000 | +10,7 | 36,9% | 1,17 | 5.000 | +10,0 | 100% |
| 1:2 sem parcial | M2 | 2.437 | +16.400 | +6,7 | 35,6% | 1,10 | 4.800 | +4,3 | 99% |
| 1:2 sem parcial | M3 | 720 | -200 | -0,3 | 33,3% | 1,00 | 4.600 | -1,4 | 47% |
| 1:2 sem parcial | M4 | 388 | +2.100 | +5,4 | 35,3% | 1,08 | 2.200 | +9,1 | 76% |
| 1:2 sem parcial | E3 | 32 | +400 | +12,5 | 37,5% | 1,20 | 500 | +32,0 | 71% |
| 1:2 sem parcial | E4 | 3.479 | +30.300 | +8,7 | 36,2% | 1,14 | 5.800 | +7,8 | 100% |
| 1:2 sem parcial | I1 | 3.046 | +27.500 | +9,0 | 36,3% | 1,14 | 5.200 | +8,7 | 100% |
| 1:2 sem parcial | I2 | 35 | -1.400 | -40,0 | 20,0% | 0,50 | 1.600 | -37,5 | 3% |
| 1:2 sem parcial | I3 | 3.648 | +30.900 | +8,5 | 36,2% | 1,13 | 5.300 | +7,3 | 100% |
| 1:2 sem parcial | M5 | 797 | +4.200 | +5,3 | 35,1% | 1,08 | 2.900 | +7,5 | 84% |
| 1:2 sem parcial | E5 | 596 | +1.400 | +2,3 | 34,1% | 1,04 | 3.000 | +4,0 | 66% |
| 1:2 sem parcial | E6 | 761 | +5.800 | +7,6 | 35,7% | 1,12 | 3.500 | -0,3 | 93% |
| 1:2 sem parcial | I4 | 679 | +3.800 | +5,6 | 35,2% | 1,09 | 3.600 | -0,6 | 84% |
| 1:2 sem parcial | I5 | 751 | +9.100 | +12,1 | 37,3% | 1,19 | 3.400 | +7,2 | 99% |
| 1:1 sem parcial | sem filtro | 3.703 | +22.600 | +6,1 | 53,0% | 1,13 | 4.900 | +5,0 | 100% |
| 1:1 sem parcial | M1 | 2.904 | +21.400 | +7,4 | 53,6% | 1,16 | 3.200 | +7,0 | 100% |
| 1:1 sem parcial | M2 | 2.437 | +10.600 | +4,3 | 52,1% | 1,09 | 3.600 | +2,3 | 98% |
| 1:1 sem parcial | M3 | 726 | 0 | 0,0 | 50,0% | 1,00 | 3.000 | -0,2 | 49% |
| 1:1 sem parcial | M4 | 388 | +200 | +0,5 | 50,3% | 1,01 | 2.100 | +5,0 | 52% |
| 1:1 sem parcial | E3 | 32 | +1.600 | +50,0 | 75,0% | 3,00 | 200 | +44,0 | 100% |
| 1:1 sem parcial | E4 | 3.509 | +21.100 | +6,0 | 52,9% | 1,13 | 4.400 | +5,0 | 100% |
| 1:1 sem parcial | I1 | 3.047 | +18.800 | +6,2 | 53,0% | 1,13 | 4.000 | +5,8 | 100% |
| 1:1 sem parcial | I2 | 35 | -100 | -2,9 | 48,6% | 0,94 | 500 | -16,7 | 43% |
| 1:1 sem parcial | I3 | 3.678 | +21.900 | +6,0 | 52,9% | 1,13 | 4.900 | +4,9 | 100% |
| 1:1 sem parcial | M5 | 797 | +1.400 | +1,8 | 50,8% | 1,04 | 3.500 | +1,6 | 69% |
| 1:1 sem parcial | E5 | 597 | +1.500 | +2,5 | 51,1% | 1,05 | 2.600 | +0,6 | 72% |
| 1:1 sem parcial | E6 | 762 | +5.500 | +7,2 | 53,4% | 1,16 | 1.600 | +2,9 | 97% |
| 1:1 sem parcial | I4 | 679 | +3.900 | +5,7 | 52,7% | 1,12 | 2.000 | +1,1 | 93% |
| 1:1 sem parcial | I5 | 751 | +5.900 | +7,9 | 53,8% | 1,17 | 2.400 | +4,5 | 98% |

## Conclusao

- **Nenhum oscilador melhora o Hull + pavios de forma demonstravel.**
- **Os cortes classicos nao conversam com este padrao:** a retracao de 2 a 4 candles e curta demais para os osciladores chegarem aos extremos, e o estocastico lento ainda esta virando no candle de sinal.
- **O que aparece de consistente e pequeno e e tendencia** (IFR alto; MACD acima de zero, menos) -- a mesma informacao que ja esta na Hull a favor.
- **Nao ha plano novo.** Candidato menos ruim para simulador, como hipotese: IFR acima de 59 no sinal.

> Osciladores calculados aqui, nao conferidos contra exportacao do Profit. Resultado bruto, um instrumento.

Reproduzir: `python osciladores.py && python relatorio_osciladores.py`.
