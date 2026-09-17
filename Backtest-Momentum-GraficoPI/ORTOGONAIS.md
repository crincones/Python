# Filtros ortogonais a Hull: velocidade, horario e posicao no dia

WINFUT, grafico de 20 PI, 50.611 candles, 132 pregoes (06/03/2026 a 14/09/2026). Resultado bruto. Graficos, curvas, MEP/MEN, duracao e trade a trade em `ortogonais.html`.

**Sinais**: Hull + 2 a 4 (4.477) e Hull + pavios (3.508).

## Resposta curta: nenhum passa no controle; o horario chega perto

- **Ortogonais de fato:** horario e ritmo (|corr| < 0,1 com Hull, Hull-EMA e MACD). **Nao ortogonal:** posicao no dia (VWAP x MACD 0,50).
- **Horario 10h-15h** (H1): +8,9 -> +11,8 pts por sinal no Hull + pavios; a favor nos tres tercos, antes de 06/08, nos dois lados, nas 4 gestoes, com plato; escolhido fora da amostra e confirmado. Mas busca contra ruido: p = 0,47 (Hull + 2 a 4: 0,28).
- **Ritmo:** hipotese ao contrario -- mercado lento nao atrapalha (V1 -1,6, V2 -0,4); o mais rapido mede pior.
- **Posicao no dia:** P1 -0,3, P2 -2,4.

## Ortogonalidade (correlacao de posto, Hull + pavios)

| Regra / leitura | Inclinacao da Hull (ATR) | Hull - EMA 21 (ATR) | MACD (ATR) |
|:--|--:|--:|--:|
| V1 | -0,01 | +0,02 | -0,01 |
| V2 | +0,00 | +0,01 | -0,01 |
| H1 | +0,01 | +0,01 | +0,02 |
| H2 | -0,03 | +0,01 | -0,01 |
| P1 | +0,18 | +0,44 | +0,50 |
| P2 | +0,06 | +0,29 | +0,31 |
| ritmo_r | -0,02 | +0,02 | -0,01 |
| hora | -0,06 | -0,00 | -0,04 |
| vwap_atr | +0,19 | +0,53 | +0,59 |
| abre_atr | +0,09 | +0,35 | +0,38 |

## Cada regra (fechamento)

**Hull + pavios (2-3 + fech ate 10%) -- 1:3 com parcial** (sem filtro: +8,9)

| | Regra | Sinais | Com | Sem | Ganho | p | T1 / T2 / T3 (sem filtro) | Antes (sem filtro) | Compra | Venda | Pct |
|:--|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|--:|
| V1 | Ritmo da ultima hora acima da mediana | 1696 (48%) | +7,3 | +10,4 | **-1,6** | 0,466 | +2 / +8 / +13 (+4 / +9 / +15) | +5,0 (+7,0) | +10,2 | +4,7 | 24 |
| V2 | Ritmo fora do quartil mais baixo | 2614 (75%) | +8,5 | +10,1 | **-0,4** | 0,761 | +5 / +9 / +12 (+4 / +9 / +15) | +7,2 (+7,0) | +10,2 | +7,0 | 38 |
| H1 | Sinal entre 10:00 e 15:00 | 2171 (62%) | +11,8 | +4,2 | **+2,9** | 0,073 | +6 / +11 / +20 (+4 / +9 / +15) | +8,8 (+7,0) | +11,9 | +11,8 | 96 |
| H2 | Sinal a partir das 10:00 | 2679 (76%) | +11,1 | +1,9 | **+2,2** | 0,064 | +5 / +11 / +19 (+4 / +9 / +15) | +8,7 (+7,0) | +11,1 | +11,1 | 96 |
| P1 | Fechamento do lado do trade na VWAP do dia | 2319 (66%) | +8,6 | +9,5 | **-0,3** | 0,843 | +3 / +11 / +14 (+4 / +9 / +15) | +7,0 (+7,0) | +12,2 | +5,1 | 42 |
| P2 | Fechamento do lado do trade na abertura do pregao | 1969 (56%) | +6,5 | +12,0 | **-2,4** | 0,188 | +1 / +9 / +12 (+4 / +9 / +15) | +5,9 (+7,0) | +8,8 | +4,6 | 10 |

**Hull + pavios (2-3 + fech ate 10%) -- 1:3 sem parcial** (sem filtro: +11,6)

| | Regra | Sinais | Com | Sem | Ganho | p | T1 / T2 / T3 (sem filtro) | Antes (sem filtro) | Compra | Venda | Pct |
|:--|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|--:|
| V1 | Ritmo da ultima hora acima da mediana | 1696 (48%) | +9,5 | +13,6 | **-2,1** | 0,528 | +1 / +11 / +17 (+5 / +13 / +19) | +5,9 (+8,9) | +15,2 | +4,4 | 25 |
| V2 | Ritmo fora do quartil mais baixo | 2614 (75%) | +11,7 | +11,2 | **+0,1** | 0,941 | +6 / +14 / +16 (+5 / +13 / +19) | +9,7 (+8,9) | +15,1 | +8,6 | 53 |
| H1 | Sinal entre 10:00 e 15:00 | 2171 (62%) | +16,9 | +3,0 | **+5,3** | 0,027 | +8 / +18 / +28 (+5 / +13 / +19) | +12,5 (+8,9) | +18,5 | +15,3 | 99 |
| H2 | Sinal a partir das 10:00 | 2679 (76%) | +15,2 | -0,1 | **+3,6** | 0,037 | +6 / +18 / +25 (+5 / +13 / +19) | +11,8 (+8,9) | +16,5 | +14,0 | 98 |
| P1 | Fechamento do lado do trade na VWAP do dia | 2319 (66%) | +11,9 | +11,1 | **+0,3** | 0,919 | +1 / +17 / +20 (+5 / +13 / +19) | +9,0 (+8,9) | +18,3 | +5,7 | 54 |
| P2 | Fechamento do lado do trade na abertura do pregao | 1969 (56%) | +8,3 | +15,8 | **-3,3** | 0,214 | -1 / +15 / +15 (+5 / +13 / +19) | +7,1 (+8,9) | +11,6 | +5,6 | 11 |

**Hull + pavios (2-3 + fech ate 10%) -- 1:2 sem parcial** (sem filtro: +9,0)

| | Regra | Sinais | Com | Sem | Ganho | p | T1 / T2 / T3 (sem filtro) | Antes (sem filtro) | Compra | Venda | Pct |
|:--|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|--:|
| V1 | Ritmo da ultima hora acima da mediana | 1696 (48%) | +8,3 | +9,7 | **-0,7** | 0,792 | +9 / +2 / +14 (+9 / +4 / +14) | +6,4 (+7,7) | +10,7 | +6,2 | 39 |
| V2 | Ritmo fora do quartil mais baixo | 2614 (75%) | +9,9 | +6,6 | **+0,8** | 0,547 | +9 / +6 / +15 (+9 / +4 / +14) | +8,6 (+7,7) | +12,5 | +7,4 | 72 |
| H1 | Sinal entre 10:00 e 15:00 | 2171 (62%) | +11,9 | +4,3 | **+2,9** | 0,129 | +10 / +7 / +19 (+9 / +4 / +14) | +9,6 (+7,7) | +10,9 | +12,9 | 93 |
| H2 | Sinal a partir das 10:00 | 2679 (76%) | +10,6 | +3,9 | **+1,6** | 0,237 | +8 / +8 / +17 (+9 / +4 / +14) | +9,1 (+7,7) | +9,9 | +11,4 | 88 |
| P1 | Fechamento do lado do trade na VWAP do dia | 2319 (66%) | +10,7 | +5,8 | **+1,7** | 0,342 | +9 / +5 / +18 (+9 / +4 / +14) | +9,1 (+7,7) | +14,1 | +7,4 | 83 |
| P2 | Fechamento do lado do trade na abertura do pregao | 1969 (56%) | +6,9 | +11,8 | **-2,1** | 0,330 | +5 / +4 / +11 (+9 / +4 / +14) | +7,3 (+7,7) | +6,5 | +7,2 | 16 |

**Hull + pavios (2-3 + fech ate 10%) -- 1:1 sem parcial** (sem filtro: +6,2)

| | Regra | Sinais | Com | Sem | Ganho | p | T1 / T2 / T3 (sem filtro) | Antes (sem filtro) | Compra | Venda | Pct |
|:--|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|--:|
| V1 | Ritmo da ultima hora acima da mediana | 1696 (48%) | +5,1 | +7,3 | **-1,1** | 0,509 | +3 / +5 / +8 (+4 / +5 / +10) | +4,1 (+5,1) | +5,2 | +5,0 | 26 |
| V2 | Ritmo fora do quartil mais baixo | 2614 (75%) | +5,3 | +8,9 | **-0,9** | 0,345 | +4 / +4 / +8 (+4 / +5 / +10) | +4,7 (+5,1) | +5,2 | +5,4 | 17 |
| H1 | Sinal entre 10:00 e 15:00 | 2171 (62%) | +6,8 | +5,4 | **+0,5** | 0,689 | +5 / +3 / +12 (+4 / +5 / +10) | +5,1 (+5,1) | +5,2 | +8,3 | 65 |
| H2 | Sinal a partir das 10:00 | 2679 (76%) | +6,9 | +4,0 | **+0,7** | 0,451 | +4 / +5 / +12 (+4 / +5 / +10) | +5,5 (+5,1) | +5,7 | +8,1 | 76 |
| P1 | Fechamento do lado do trade na VWAP do dia | 2319 (66%) | +5,3 | +8,0 | **-0,9** | 0,456 | +4 / +4 / +8 (+4 / +5 / +10) | +5,0 (+5,1) | +6,2 | +4,5 | 24 |
| P2 | Fechamento do lado do trade na abertura do pregao | 1969 (56%) | +4,7 | +8,3 | **-1,6** | 0,302 | +2 / +4 / +8 (+4 / +5 / +10) | +4,7 (+5,1) | +6,0 | +3,6 | 14 |

**Hull + 2 a 4 -- 1:3 com parcial** (sem filtro: +7,7)

| | Regra | Sinais | Com | Sem | Ganho | p | T1 / T2 / T3 (sem filtro) | Antes (sem filtro) | Compra | Venda | Pct |
|:--|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|--:|
| V1 | Ritmo da ultima hora acima da mediana | 2224 (50%) | +6,9 | +8,5 | **-0,8** | 0,658 | +5 / +5 / +11 (+6 / +6 / +11) | +5,9 (+6,7) | +7,4 | +6,5 | 34 |
| V2 | Ritmo fora do quartil mais baixo | 3357 (75%) | +7,7 | +7,7 | **+0,0** | 0,993 | +7 / +7 / +9 (+6 / +6 / +11) | +7,5 (+6,7) | +7,7 | +7,7 | 50 |
| H1 | Sinal entre 10:00 e 15:00 | 2639 (59%) | +11,0 | +3,0 | **+3,3** | 0,037 | +9 / +9 / +15 (+6 / +6 / +11) | +9,5 (+6,7) | +9,7 | +12,2 | 98 |
| H2 | Sinal a partir das 10:00 | 3273 (73%) | +10,2 | +0,9 | **+2,5** | 0,030 | +7 / +9 / +15 (+6 / +6 / +11) | +8,9 (+6,7) | +9,5 | +10,9 | 98 |
| P1 | Fechamento do lado do trade na VWAP do dia | 2919 (65%) | +8,4 | +6,4 | **+0,7** | 0,623 | +7 / +7 / +11 (+6 / +6 / +11) | +8,2 (+6,7) | +11,3 | +5,6 | 70 |
| P2 | Fechamento do lado do trade na abertura do pregao | 2480 (55%) | +6,0 | +9,8 | **-1,7** | 0,326 | +4 / +8 / +7 (+6 / +6 / +11) | +6,9 (+6,7) | +6,9 | +5,3 | 15 |

**Hull + 2 a 4 -- 1:3 sem parcial** (sem filtro: +8,8)

| | Regra | Sinais | Com | Sem | Ganho | p | T1 / T2 / T3 (sem filtro) | Antes (sem filtro) | Compra | Venda | Pct |
|:--|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|--:|
| V1 | Ritmo da ultima hora acima da mediana | 2224 (50%) | +8,1 | +9,5 | **-0,7** | 0,790 | +4 / +6 / +14 (+6 / +8 / +13) | +5,9 (+7,4) | +8,9 | +7,5 | 40 |
| V2 | Ritmo fora do quartil mais baixo | 3357 (75%) | +9,5 | +6,7 | **+0,7** | 0,642 | +8 / +9 / +11 (+6 / +8 / +13) | +9,0 (+7,4) | +9,8 | +9,3 | 67 |
| H1 | Sinal entre 10:00 e 15:00 | 2639 (59%) | +14,5 | +0,7 | **+5,7** | 0,009 | +11 / +13 / +20 (+6 / +8 / +13) | +12,4 (+7,4) | +13,6 | +15,4 | 99 |
| H2 | Sinal a partir das 10:00 | 3273 (73%) | +12,7 | -1,7 | **+3,9** | 0,017 | +8 / +13 / +18 (+6 / +8 / +13) | +10,9 (+7,4) | +12,3 | +13,1 | 99 |
| P1 | Fechamento do lado do trade na VWAP do dia | 2919 (65%) | +9,5 | +7,5 | **+0,7** | 0,707 | +6 / +10 / +13 (+6 / +8 / +13) | +8,9 (+7,4) | +13,9 | +5,3 | 64 |
| P2 | Fechamento do lado do trade na abertura do pregao | 2480 (55%) | +5,8 | +12,6 | **-3,0** | 0,205 | +2 / +10 / +7 (+6 / +8 / +13) | +6,5 (+7,4) | +6,9 | +4,9 | 10 |

**Hull + 2 a 4 -- 1:2 sem parcial** (sem filtro: +8,4)

| | Regra | Sinais | Com | Sem | Ganho | p | T1 / T2 / T3 (sem filtro) | Antes (sem filtro) | Compra | Venda | Pct |
|:--|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|--:|
| V1 | Ritmo da ultima hora acima da mediana | 2224 (50%) | +8,0 | +8,7 | **-0,4** | 0,855 | +13 / +1 / +10 (+12 / +3 / +9) | +7,5 (+8,4) | +8,3 | +7,6 | 42 |
| V2 | Ritmo fora do quartil mais baixo | 3357 (75%) | +9,2 | +5,7 | **+0,9** | 0,458 | +12 / +5 / +10 (+12 / +3 / +9) | +9,5 (+8,4) | +10,1 | +8,4 | 76 |
| H1 | Sinal entre 10:00 e 15:00 | 2639 (59%) | +12,1 | +3,0 | **+3,7** | 0,037 | +14 / +8 / +14 (+12 / +3 / +9) | +11,7 (+8,4) | +9,4 | +14,7 | 98 |
| H2 | Sinal a partir das 10:00 | 3273 (73%) | +10,8 | +1,7 | **+2,5** | 0,066 | +12 / +8 / +12 (+12 / +3 / +9) | +11,0 (+8,4) | +9,3 | +12,3 | 97 |
| P1 | Fechamento do lado do trade na VWAP do dia | 2919 (65%) | +10,4 | +4,5 | **+2,1** | 0,179 | +16 / +3 / +11 (+12 / +3 / +9) | +11,0 (+8,4) | +13,7 | +7,2 | 90 |
| P2 | Fechamento do lado do trade na abertura do pregao | 2480 (55%) | +7,0 | +10,1 | **-1,4** | 0,458 | +11 / +5 / +4 (+12 / +3 / +9) | +9,5 (+8,4) | +5,8 | +8,0 | 22 |

**Hull + 2 a 4 -- 1:1 sem parcial** (sem filtro: +6,6)

| | Regra | Sinais | Com | Sem | Ganho | p | T1 / T2 / T3 (sem filtro) | Antes (sem filtro) | Compra | Venda | Pct |
|:--|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|--:|
| V1 | Ritmo da ultima hora acima da mediana | 2224 (50%) | +5,7 | +7,5 | **-0,9** | 0,555 | +5 / +5 / +7 (+6 / +4 / +9) | +5,9 (+6,0) | +5,9 | +5,5 | 28 |
| V2 | Ritmo fora do quartil mais baixo | 3357 (75%) | +5,9 | +8,7 | **-0,7** | 0,448 | +6 / +4 / +7 (+6 / +4 / +9) | +6,0 (+6,0) | +5,6 | +6,2 | 21 |
| H1 | Sinal entre 10:00 e 15:00 | 2639 (59%) | +7,5 | +5,3 | **+0,9** | 0,506 | +7 / +4 / +11 (+6 / +4 / +9) | +6,5 (+6,0) | +5,8 | +9,0 | 74 |
| H2 | Sinal a partir das 10:00 | 3273 (73%) | +7,7 | +3,5 | **+1,1** | 0,213 | +6 / +5 / +12 (+6 / +4 / +9) | +6,9 (+6,0) | +6,7 | +8,7 | 89 |
| P1 | Fechamento do lado do trade na VWAP do dia | 2919 (65%) | +7,3 | +5,3 | **+0,7** | 0,542 | +9 / +5 / +8 (+6 / +4 / +9) | +7,6 (+6,0) | +8,8 | +5,8 | 73 |
| P2 | Fechamento do lado do trade na abertura do pregao | 2480 (55%) | +6,2 | +7,0 | **-0,3** | 0,823 | +7 / +6 / +6 (+6 / +4 / +9) | +7,4 (+6,0) | +6,9 | +5,7 | 40 |

## Faixas (Hull + pavios, 1:3 com parcial)

Hora: 9h-10h +1,9 (829) / 10h-11h +12,8 (936) / 11h-12h +8,5 (555) / 12h-13h +11,9 (294) / 13h-14h +18,8 (202) / 14h-15h +9,2 (184) / 15h-16h +8,0 (176) / 16h em diante +7,8 (332)

- Ritmo da ultima hora / mediana: limites 0,41 / 0,84 / 1,14 / 1,61 -> +11,0 / +10,1 / +9,3 / +12,2 / +2,0
- Hora do sinal: limites 9,73 / 10,57 / 11,55 / 13,95 -> +4,6 / +1,8 / +18,9 / +11,2 / +7,8
- Distancia a VWAP do dia, em ATR (a favor): limites -1,74 / 0,38 / 2,02 / 4,93 -> +11,3 / +7,3 / +3,5 / +14,1 / +8,4
- Distancia a abertura do pregao, em ATR (a favor): limites -5,52 / 0,00 / 3,36 / 8,58 -> +20,7 / +7,7 / -0,1 / +6,0 / +10,4

**Horario x ritmo** (ritmo rapido = quintil de cima):

| Conjunto | Horario | Ritmo normal | Ritmo rapido |
|:--|:--|--:|--:|
| cand | antes das 10h | +4,4 (316) | +0,4 (513) |
| cand | a partir das 10h | +11,4 (2490) | +6,3 (189) |
| h | antes das 10h | +2,5 (516) | -0,3 (688) |
| h | a partir das 10h | +10,4 (3065) | +7,2 (208) |

## Busca contra ruido e escolha fora

| Conjunto | Gestao | Melhor | t | ruido med | ruido p95 | p | Escolhida antes, medida depois | Escolhida T1+T2, medida T3 |
|:--|:--|:--|--:|--:|--:|--:|:--|:--|
| cand | 1:3 com parcial | H1 | +1,07 | +1,04 | +1,88 | 0,47 | H2 +20,0 (sem filtro +15,8) | P2 (nao) +18,8 (sem filtro +14,6) |
| cand | 1:3 sem parcial | H1 | +1,36 | +1,03 | +1,84 | 0,24 | H1 +31,3 (sem filtro +21,2) | H1 +27,8 (sem filtro +18,8) |
| cand | 1:2 sem parcial | H1 | +0,93 | +1,05 | +1,92 | 0,61 | H1 +19,6 (sem filtro +13,6) | P2 (nao) +17,9 (sem filtro +14,1) |
| cand | 1:1 sem parcial | V2 (nao) | +0,81 | +1,06 | +1,93 | 0,72 | V1 (nao) +13,8 (sem filtro +10,4) | P2 (nao) +13,2 (sem filtro +10,4) |
| h | 1:3 com parcial | H1 | +1,33 | +1,07 | +1,89 | 0,28 | H1 +16,0 (sem filtro +11,0) | H1 +15,5 (sem filtro +11,0) |
| h | 1:3 sem parcial | H1 | +1,62 | +1,07 | +1,87 | 0,12 | H1 +21,4 (sem filtro +13,6) | H1 +19,6 (sem filtro +13,0) |
| h | 1:2 sem parcial | H1 | +1,32 | +1,05 | +1,88 | 0,28 | H1 +13,4 (sem filtro +8,3) | H1 +13,8 (sem filtro +9,0) |
| h | 1:1 sem parcial | V2 (nao) | +0,70 | +1,06 | +1,87 | 0,85 | P1 +5,9 (sem filtro +8,5) | P1 +8,1 (sem filtro +9,0) |

## Vizinhanca (ganho, Hull + pavios, 1:3 com parcial)

| Regra | Parametro | Sinais | Ganho |
|:--|:--|--:|--:|
| V1 | janela 30 min | 1634 | +0,4 |
| V2 | janela 30 min | 2611 | -1,2 |
| V1 | janela 60 min (declarado) | 1696 | -1,6 |
| V2 | janela 60 min (declarado) | 2614 | -0,4 |
| V1 | janela 120 min | 1736 | -2,5 |
| V2 | janela 120 min | 2626 | -1,1 |
| H1 | 10h a 14h | 1987 | +3,2 |
| H1 | 10h a 15h (declarado) | 2171 | +2,9 |
| H1 | 10h a 16h | 2347 | +2,6 |
| H2 | a partir de 9h30 | 2943 | +0,9 |
| H2 | a partir de 10h (declarado) | 2679 | +2,2 |
| H2 | a partir de 10h30 | 2239 | +2,6 |

## Carteira, uma posicao por vez

| Conjunto | Gestao | Regra | Trades | Pts | Pts/trade | Acerto | Fator | Rebaix. | Antes (pts/trade) |
|:--|:--|:--|--:|--:|--:|--:|--:|--:|--:|
| cand | 1:3 com parcial | sem filtro | 3.296 | +30.800 | +9,3 | 28,2% | 1,20 | 5.100 | +7,2 |
| cand | 1:3 com parcial | V1 | 1.596 | +13.100 | +8,2 | 27,6% | 1,17 | 3.200 | +5,6 |
| cand | 1:3 com parcial | V2 | 2.466 | +23.300 | +9,4 | 28,2% | 1,20 | 3.800 | +7,9 |
| cand | 1:3 com parcial | H1 | 2.051 | +24.600 | +12,0 | 29,4% | 1,26 | 3.600 | +8,7 |
| cand | 1:3 com parcial | H2 | 2.520 | +28.500 | +11,3 | 29,1% | 1,24 | 5.300 | +8,7 |
| cand | 1:3 com parcial | P1 | 2.201 | +19.450 | +8,8 | 28,0% | 1,19 | 5.100 | +6,9 |
| cand | 1:3 com parcial | P2 | 1.872 | +13.100 | +7,0 | 27,2% | 1,15 | 5.600 | +6,3 |
| cand | 1:3 sem parcial | sem filtro | 3.296 | +40.100 | +12,2 | 28,2% | 1,17 | 6.600 | +9,3 |
| cand | 1:3 sem parcial | V1 | 1.596 | +16.900 | +10,6 | 27,6% | 1,15 | 4.600 | +6,8 |
| cand | 1:3 sem parcial | V2 | 2.466 | +31.500 | +12,8 | 28,2% | 1,18 | 5.300 | +10,6 |
| cand | 1:3 sem parcial | H1 | 2.051 | +35.500 | +17,3 | 29,4% | 1,25 | 4.900 | +12,7 |
| cand | 1:3 sem parcial | H2 | 2.520 | +39.700 | +15,8 | 29,1% | 1,22 | 6.500 | +12,1 |
| cand | 1:3 sem parcial | P1 | 2.201 | +26.300 | +11,9 | 28,0% | 1,17 | 6.300 | +8,7 |
| cand | 1:3 sem parcial | P2 | 1.872 | +16.500 | +8,8 | 27,2% | 1,12 | 7.300 | +7,5 |
| cand | 1:2 sem parcial | sem filtro | 3.478 | +32.000 | +9,2 | 36,4% | 1,15 | 5.800 | +8,0 |
| cand | 1:2 sem parcial | V1 | 1.684 | +14.400 | +8,6 | 36,2% | 1,13 | 3.900 | +6,7 |
| cand | 1:2 sem parcial | V2 | 2.593 | +26.400 | +10,2 | 36,7% | 1,16 | 3.700 | +9,1 |
| cand | 1:2 sem parcial | H1 | 2.152 | +25.700 | +11,9 | 37,3% | 1,19 | 4.400 | +9,8 |
| cand | 1:2 sem parcial | H2 | 2.652 | +28.500 | +10,7 | 36,9% | 1,17 | 5.600 | +9,4 |
| cand | 1:2 sem parcial | P1 | 2.319 | +24.800 | +10,7 | 36,9% | 1,17 | 4.500 | +9,1 |
| cand | 1:2 sem parcial | P2 | 1.969 | +13.600 | +6,9 | 35,6% | 1,11 | 5.000 | +7,3 |
| cand | 1:1 sem parcial | sem filtro | 3.508 | +21.900 | +6,2 | 53,0% | 1,13 | 4.900 | +5,1 |
| cand | 1:1 sem parcial | V1 | 1.696 | +8.700 | +5,1 | 52,5% | 1,11 | 2.700 | +4,1 |
| cand | 1:1 sem parcial | V2 | 2.614 | +13.900 | +5,3 | 52,6% | 1,11 | 4.400 | +4,7 |
| cand | 1:1 sem parcial | H1 | 2.171 | +14.700 | +6,8 | 53,4% | 1,15 | 3.400 | +5,1 |
| cand | 1:1 sem parcial | H2 | 2.679 | +18.600 | +6,9 | 53,3% | 1,15 | 4.900 | +5,5 |
| cand | 1:1 sem parcial | P1 | 2.319 | +12.400 | +5,3 | 52,6% | 1,11 | 5.100 | +5,0 |
| cand | 1:1 sem parcial | P2 | 1.969 | +9.200 | +4,7 | 52,2% | 1,10 | 4.600 | +4,7 |
| h | 1:3 com parcial | sem filtro | 4.168 | +34.200 | +8,2 | 27,5% | 1,18 | 4.700 | +7,1 |
| h | 1:3 com parcial | V1 | 2.077 | +16.800 | +8,1 | 27,3% | 1,17 | 3.100 | +6,8 |
| h | 1:3 com parcial | V2 | 3.130 | +26.900 | +8,6 | 27,6% | 1,18 | 4.800 | +8,2 |
| h | 1:3 com parcial | H1 | 2.466 | +27.600 | +11,2 | 28,8% | 1,24 | 3.400 | +9,5 |
| h | 1:3 com parcial | H2 | 3.047 | +32.200 | +10,6 | 28,5% | 1,23 | 4.400 | +9,1 |
| h | 1:3 com parcial | P1 | 2.758 | +23.700 | +8,6 | 27,4% | 1,19 | 4.700 | +8,4 |
| h | 1:3 com parcial | P2 | 2.345 | +15.250 | +6,5 | 26,6% | 1,14 | 5.800 | +7,5 |
| h | 1:3 sem parcial | sem filtro | 4.168 | +39.200 | +9,4 | 27,5% | 1,13 | 6.200 | +7,9 |
| h | 1:3 sem parcial | V1 | 2.077 | +19.600 | +9,4 | 27,3% | 1,13 | 3.400 | +6,9 |
| h | 1:3 sem parcial | V2 | 3.130 | +32.700 | +10,4 | 27,6% | 1,14 | 7.400 | +9,7 |
| h | 1:3 sem parcial | H1 | 2.466 | +36.800 | +14,9 | 28,8% | 1,21 | 4.200 | +12,6 |
| h | 1:3 sem parcial | H2 | 3.047 | +40.500 | +13,3 | 28,5% | 1,19 | 5.300 | +11,3 |
| h | 1:3 sem parcial | P1 | 2.758 | +25.900 | +9,4 | 27,4% | 1,13 | 6.200 | +8,8 |
| h | 1:3 sem parcial | P2 | 2.345 | +14.500 | +6,2 | 26,6% | 1,08 | 7.600 | +6,9 |
| h | 1:2 sem parcial | sem filtro | 4.426 | +38.300 | +8,7 | 36,2% | 1,14 | 6.900 | +8,8 |
| h | 1:2 sem parcial | V1 | 2.201 | +18.500 | +8,4 | 36,1% | 1,13 | 4.400 | +7,9 |
| h | 1:2 sem parcial | V2 | 3.320 | +32.000 | +9,6 | 36,5% | 1,15 | 5.300 | +9,9 |
| h | 1:2 sem parcial | H1 | 2.610 | +32.100 | +12,3 | 37,4% | 1,20 | 4.300 | +12,1 |
| h | 1:2 sem parcial | H2 | 3.232 | +35.900 | +11,1 | 37,0% | 1,18 | 5.300 | +11,4 |
| h | 1:2 sem parcial | P1 | 2.918 | +30.500 | +10,5 | 36,8% | 1,17 | 4.900 | +11,0 |
| h | 1:2 sem parcial | P2 | 2.480 | +17.300 | +7,0 | 35,6% | 1,11 | 4.400 | +9,5 |
| h | 1:1 sem parcial | sem filtro | 4.477 | +29.500 | +6,6 | 53,2% | 1,14 | 4.500 | +6,0 |
| h | 1:1 sem parcial | V1 | 2.224 | +12.700 | +5,7 | 52,8% | 1,12 | 3.500 | +5,9 |
| h | 1:1 sem parcial | V2 | 3.357 | +19.800 | +5,9 | 52,9% | 1,13 | 5.300 | +6,0 |
| h | 1:1 sem parcial | H1 | 2.639 | +19.700 | +7,5 | 53,7% | 1,16 | 3.300 | +6,5 |
| h | 1:1 sem parcial | H2 | 3.273 | +25.300 | +7,7 | 53,7% | 1,17 | 4.700 | +6,9 |
| h | 1:1 sem parcial | P1 | 2.919 | +21.200 | +7,3 | 53,5% | 1,16 | 4.200 | +7,6 |
| h | 1:1 sem parcial | P2 | 2.480 | +15.500 | +6,2 | 53,0% | 1,13 | 4.800 | +7,4 |

## Conclusao

- **Nenhum filtro passa no controle de busca.**
- **Posicao no dia nao e ortogonal** a Hull e nao acrescenta nada.
- **Ritmo e ortogonal, mas a hipotese estava ao contrario**: o mercado mais rapido e que mede pior. Hipotese nova, no sentido oposto ao declarado.
- **Horario e o melhor candidato de todos os estudos do Hull**: declarado antes, ortogonal, a favor em todos os recortes, com plato e confirmado na escolha fora da amostra, mas com +2,9 pts de ganho, pequeno demais para esta base provar. Regra mais barata para o simulador: nao operar antes das 10h.

> Resultado bruto, um instrumento. VWAP com volume agressor. Nenhum plano foi alterado.

Reproduzir: `python ortogonais.py && python relatorio_ortogonais.py`.
