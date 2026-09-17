# Segundo toque na EMA 21

Setup EMA 21 + HullRetracao_Azul + MACD, WINFUT PI 20, 132 pregoes (2026-03-06 a 2026-09-14), 2.141 sinais. Entrada seca no fechamento, 6 contratos, R$ 0,50 por contrato. Treino ate 2026-07-01. Tabelas completas em `segundo.html`.

Recuo = candles tocando a EMA 21 (tolerancia 15 pts). Um toque e novo recuo se o preco andou a favor pelo menos o impulso minimo (300 pts; 200 e 400 como sensibilidade) desde o extremo do recuo anterior, dentro da perna do MACD e do pregao. Stop cheio = stop de -100 sem parcial.

## Stop 100 / alvo 400 sem parcial (impulso minimo 300)

| Grupo | Sinais | R$/trade | Resto | Treino (resto) | Teste (resto) | Stop cheio (resto) | t |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 1o recuo da perna do MACD | 479 | +R$ 6,8 | +R$ 4,7 | +R$ 9,8 (+R$ 0,2) | +R$ 0,8 (+R$ 13,7) | 78% (78%) | 0,16 |
| 2o recuo da perna (houve impulso depois do 1o) | 655 | −R$ 14,4 | +R$ 13,8 | −R$ 32,9 (+R$ 17,4) | +R$ 20,1 (+R$ 6,5) | 81% (77%) | −2,54 |
| 3o recuo ou mais | 466 | +R$ 17,1 | +R$ 1,9 | +R$ 20,5 (−R$ 2,8) | +R$ 10,2 (+R$ 11,0) | 76% (79%) | 1,16 |
| Toque sem impulso desde o anterior (preso na EMA) | 541 | +R$ 17,2 | +R$ 1,1 | +R$ 21,5 (−R$ 4,2) | +R$ 8,5 (+R$ 11,6) | 76% (79%) | 1,29 |
| Recuo passou do recuo anterior (> 15 pts alem) | 70 | −R$ 16,7 | −R$ 0,3 | −R$ 27,0 (−R$ 9,1) | +R$ 9,0 (+R$ 16,5) | 81% (79%) | −0,58 |
| Recuo no mesmo nivel do anterior (+-15 pts) | 58 | +R$ 11,5 | −R$ 2,0 | −R$ 37,3 (−R$ 9,0) | +R$ 85,7 (+R$ 11,6) | 78% (79%) | 0,40 |
| Recuo acima do anterior, ate 100 pts | 335 | −R$ 4,4 | +R$ 0,1 | −R$ 17,1 (−R$ 7,4) | +R$ 20,4 (+R$ 14,3) | 80% (79%) | −0,29 |
| Recuo acima do anterior, 101-200 pts | 283 | +R$ 0,4 | −R$ 1,9 | +R$ 6,9 (−R$ 16,5) | −R$ 13,8 (+R$ 25,1) | 79% (79%) | 0,14 |
| Recuo acima do anterior, mais de 200 pts | 375 | +R$ 1,2 | −R$ 2,5 | −R$ 10,6 (−R$ 10,2) | +R$ 21,2 (+R$ 13,2) | 79% (79%) | 0,24 |
| Recuo anterior SEM sinal | 631 | +R$ 5,0 | −R$ 9,4 | −R$ 15,1 (−R$ 4,1) | +R$ 44,1 (−R$ 19,2) | 78% (81%) | 1,00 |
| Recuo anterior COM sinal | 490 | −R$ 9,4 | +R$ 5,0 | −R$ 4,1 (−R$ 15,1) | −R$ 19,2 (+R$ 44,1) | 81% (78%) | −1,00 |
| Sinal anterior perto: entrada ate 100 pts do anterior | 266 | −R$ 13,8 | −R$ 4,1 | −R$ 9,8 (+R$ 2,9) | −R$ 21,9 (−R$ 16,3) | 82% (80%) | −0,46 |
| Sinal anterior longe: mais de 100 pts | 224 | −R$ 4,1 | −R$ 13,8 | +R$ 2,9 (−R$ 9,8) | −R$ 16,3 (−R$ 21,9) | 80% (82%) | 0,46 |
| Entrada 100+ pts PIOR que a anterior (abaixo na compra) | 8 | −R$ 48,0 | −R$ 8,7 | −R$ 23,0 (−R$ 3,8) | −R$ 123,0 (−R$ 18,0) | 88% (81%) | −0,52 |
| Entrada no MESMO preco da anterior | 95 | −R$ 4,3 | −R$ 10,6 | −R$ 17,3 (−R$ 0,6) | +R$ 27,0 (−R$ 28,4) | 80% (81%) | 0,23 |
| Entrada 1 tijolo (100 pts) acima na compra | 163 | −R$ 17,7 | −R$ 5,2 | −R$ 4,2 (−R$ 4,1) | −R$ 41,6 (−R$ 7,3) | 82% (80%) | −0,57 |
| Entrada 200 pts acima | 86 | +R$ 2,6 | −R$ 11,9 | +R$ 24,2 (−R$ 9,7) | −R$ 32,1 (−R$ 16,1) | 79% (81%) | 0,50 |
| Entrada 300+ pts acima | 138 | −R$ 8,2 | −R$ 9,8 | −R$ 9,7 (−R$ 2,0) | −R$ 5,5 (−R$ 24,6) | 80% (81%) | 0,07 |
| Sinal anterior tomou STOP | 102 | +R$ 4,1 | −R$ 12,9 | −R$ 8,1 (−R$ 3,0) | +R$ 31,8 (−R$ 30,6) | 78% (81%) | 0,63 |
| Sinal anterior fez parcial e zerou (0x0) | 88 | −R$ 13,9 | −R$ 8,4 | −R$ 44,3 (+R$ 5,3) | +R$ 54,8 (−R$ 33,2) | 82% (81%) | −0,20 |
| Sinal anterior bateu o ALVO | 212 | −R$ 12,1 | −R$ 7,3 | +R$ 11,4 (−R$ 15,2) | −R$ 51,6 (+R$ 8,9) | 81% (81%) | −0,22 |
| Sinal anterior ainda aberto | 88 | −R$ 13,9 | −R$ 8,4 | +R$ 7,9 (−R$ 6,6) | −R$ 50,3 (−R$ 11,8) | 82% (81%) | −0,20 |

| Carteira | Trades | Liquido | Fator | Rebaix. | Treino | Teste |
|:--|--:|--:|--:|--:|--:|--:|
| sem filtro | 1.947 | +R$ 11.199 | 1,06 | −R$ 7.089 | +R$ 2.121 | +R$ 9.078 |
| sem o 2o recuo da perna | 1.396 | +R$ 21.492 | 1,16 | −R$ 3.840 | +R$ 17.358 | +R$ 4.134 |
| sem 2o e 3o+ recuos | 1.006 | +R$ 11.982 | 1,13 | −R$ 4.023 | +R$ 10.944 | +R$ 1.038 |
| sem o sinal perto do anterior (ate 100 pts) | 1.814 | +R$ 13.998 | 1,08 | −R$ 6.645 | +R$ 4.431 | +R$ 9.567 |
| sem o sinal 1 tijolo acima do anterior | 1.905 | +R$ 12.885 | 1,07 | −R$ 7.428 | +R$ 3.762 | +R$ 9.123 |
| sem o sinal com o anterior ainda aberto | 1.943 | +R$ 11.691 | 1,06 | −R$ 7.089 | +R$ 2.244 | +R$ 9.447 |
| sem o sinal depois de STOP no anterior | 1.863 | +R$ 10.371 | 1,06 | −R$ 6.921 | +R$ 2.172 | +R$ 8.199 |

## Gestao do CLAUDE.md (stop 100, parcial +100, alvo 300) (impulso minimo 300)

| Grupo | Sinais | R$/trade | Resto | Treino (resto) | Teste (resto) | Stop cheio (resto) | t |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 1o recuo da perna do MACD | 479 | +R$ 3,5 | +R$ 4,6 | +R$ 4,9 (+R$ 0,8) | +R$ 0,8 (+R$ 11,9) | 48% (47%) | −0,14 |
| 2o recuo da perna (houve impulso depois do 1o) | 655 | −R$ 5,7 | +R$ 8,8 | −R$ 16,0 (+R$ 9,3) | +R$ 13,2 (+R$ 7,7) | 50% (46%) | −2,12 |
| 3o recuo ou mais | 466 | +R$ 10,1 | +R$ 2,7 | +R$ 13,6 (−R$ 1,6) | +R$ 3,2 (+R$ 11,2) | 45% (48%) | 0,95 |
| Toque sem impulso desde o anterior (preso na EMA) | 541 | +R$ 12,3 | +R$ 1,6 | +R$ 9,6 (−R$ 1,0) | +R$ 17,9 (+R$ 6,7) | 46% (48%) | 1,41 |
| Recuo passou do recuo anterior (> 15 pts alem) | 70 | −R$ 3,0 | +R$ 1,1 | −R$ 5,4 (−R$ 3,3) | +R$ 3,0 (+R$ 9,5) | 44% (48%) | −0,24 |
| Recuo no mesmo nivel do anterior (+-15 pts) | 58 | +R$ 3,2 | +R$ 0,7 | −R$ 33,9 (−R$ 2,0) | +R$ 59,6 (+R$ 6,0) | 43% (48%) | 0,13 |
| Recuo acima do anterior, ate 100 pts | 335 | +R$ 0,6 | +R$ 1,0 | −R$ 5,7 (−R$ 2,5) | +R$ 12,9 (+R$ 7,6) | 50% (46%) | −0,04 |
| Recuo acima do anterior, 101-200 pts | 283 | −R$ 0,5 | +R$ 1,3 | +R$ 6,3 (−R$ 7,0) | −R$ 15,1 (+R$ 16,5) | 49% (47%) | −0,17 |
| Recuo acima do anterior, mais de 200 pts | 375 | +R$ 2,4 | +R$ 0,1 | −R$ 4,5 (−R$ 3,0) | +R$ 14,3 (+R$ 6,3) | 45% (49%) | 0,26 |
| Recuo anterior SEM sinal | 631 | +R$ 2,9 | −R$ 1,8 | −R$ 5,9 (−R$ 0,4) | +R$ 20,0 (−R$ 4,4) | 47% (48%) | 0,53 |
| Recuo anterior COM sinal | 490 | −R$ 1,8 | +R$ 2,9 | −R$ 0,4 (−R$ 5,9) | −R$ 4,4 (+R$ 20,0) | 48% (47%) | −0,53 |
| Sinal anterior perto: entrada ate 100 pts do anterior | 266 | −R$ 8,4 | +R$ 6,1 | −R$ 0,3 (−R$ 0,5) | −R$ 24,6 (+R$ 17,7) | 50% (46%) | −1,10 |
| Sinal anterior longe: mais de 100 pts | 224 | +R$ 6,1 | −R$ 8,4 | −R$ 0,5 (−R$ 0,3) | +R$ 17,7 (−R$ 24,6) | 46% (50%) | 1,10 |
| Entrada 100+ pts PIOR que a anterior (abaixo na compra) | 8 | +R$ 12,0 | −R$ 2,0 | +R$ 37,0 (−R$ 1,1) | −R$ 63,0 (−R$ 3,7) | 38% (48%) | 0,26 |
| Entrada no MESMO preco da anterior | 95 | −R$ 8,1 | −R$ 0,3 | −R$ 4,8 (+R$ 0,8) | −R$ 15,9 (−R$ 2,2) | 51% (48%) | −0,47 |
| Entrada 1 tijolo (100 pts) acima na compra | 163 | −R$ 9,6 | +R$ 2,1 | +R$ 0,5 (−R$ 0,8) | −R$ 27,4 (+R$ 7,8) | 51% (47%) | −0,85 |
| Entrada 200 pts acima | 86 | +R$ 15,1 | −R$ 5,4 | +R$ 8,3 (−R$ 2,1) | +R$ 26,1 (−R$ 11,8) | 43% (49%) | 1,15 |
| Entrada 300+ pts acima | 138 | +R$ 0,5 | −R$ 2,7 | −R$ 5,7 (+R$ 1,7) | +R$ 12,0 (−R$ 10,9) | 47% (49%) | 0,21 |
| Sinal anterior tomou STOP | 102 | +R$ 1,7 | −R$ 2,7 | −R$ 13,1 (+R$ 3,3) | +R$ 35,7 (−R$ 13,4) | 49% (48%) | 0,27 |
| Sinal anterior fez parcial e zerou (0x0) | 88 | −R$ 7,1 | −R$ 0,6 | −R$ 12,8 (+R$ 2,6) | +R$ 5,9 (−R$ 6,4) | 47% (49%) | −0,39 |
| Sinal anterior bateu o ALVO | 212 | +R$ 2,7 | −R$ 5,2 | +R$ 8,7 (−R$ 6,8) | −R$ 7,6 (−R$ 1,7) | 47% (49%) | 0,59 |
| Sinal anterior ainda aberto | 88 | −R$ 11,2 | +R$ 0,3 | +R$ 7,9 (−R$ 2,1) | −R$ 43,0 (+R$ 4,9) | 52% (47%) | −0,67 |

| Carteira | Trades | Liquido | Fator | Rebaix. | Treino | Teste |
|:--|--:|--:|--:|--:|--:|--:|
| sem filtro | 2.037 | +R$ 9.849 | 1,08 | −R$ 5.868 | +R$ 1.581 | +R$ 8.268 |
| sem o 2o recuo da perna | 1.438 | +R$ 14.046 | 1,17 | −R$ 2.940 | +R$ 9.117 | +R$ 4.929 |
| sem 2o e 3o+ recuos | 1.015 | +R$ 8.235 | 1,14 | −R$ 2.571 | +R$ 4.929 | +R$ 3.306 |
| sem o sinal perto do anterior (ate 100 pts) | 1.862 | +R$ 11.574 | 1,11 | −R$ 5.058 | +R$ 2.301 | +R$ 9.273 |
| sem o sinal 1 tijolo acima do anterior | 1.961 | +R$ 10.437 | 1,09 | −R$ 5.958 | +R$ 1.971 | +R$ 8.466 |
| sem o sinal com o anterior ainda aberto | 2.036 | +R$ 9.852 | 1,08 | −R$ 5.868 | +R$ 1.584 | +R$ 8.268 |
| sem o sinal depois de STOP no anterior | 1.945 | +R$ 9.405 | 1,08 | −R$ 5.457 | +R$ 2.367 | +R$ 7.038 |

## Sensibilidade (stop 100 / alvo 400): R$/trade treino / teste, resto entre parenteses

| Grupo | Impulso >= 200 | Impulso >= 300 | Impulso >= 400 |
|:--|--:|--:|--:|
| 2o recuo da perna (houve impulso depois do 1o) | −R$ 18,1 (+R$ 11,9) / +R$ 33,3 (−R$ 1,0) | −R$ 32,9 (+R$ 17,4) / +R$ 20,1 (+R$ 6,5) | −R$ 21,2 (+R$ 9,8) / +R$ 24,3 (+R$ 6,5) |
| Sinal anterior perto: entrada ate 100 pts do anterior | +R$ 8,5 (+R$ 6,2) / −R$ 0,9 (−R$ 15,0) | −R$ 9,8 (+R$ 2,9) / −R$ 21,9 (−R$ 16,3) | +R$ 7,7 (+R$ 11,2) / −R$ 37,3 (+R$ 3,9) |
| Entrada 1 tijolo (100 pts) acima na compra | −R$ 6,6 (+R$ 12,6) / −R$ 33,0 (+R$ 5,1) | −R$ 4,2 (−R$ 4,1) / −R$ 41,6 (−R$ 7,3) | +R$ 12,4 (+R$ 8,7) / −R$ 51,6 (+R$ 7,2) |
| Entrada no MESMO preco da anterior | −R$ 11,8 (+R$ 15,3) / +R$ 53,8 (−R$ 21,5) | −R$ 17,3 (−R$ 0,6) / +R$ 27,0 (−R$ 28,4) | −R$ 23,0 (+R$ 11,6) / +R$ 48,4 (−R$ 14,2) |
| Sinal anterior ainda aberto | +R$ 7,9 (+R$ 7,5) / −R$ 52,4 (+R$ 3,0) | +R$ 7,9 (−R$ 6,6) / −R$ 50,3 (−R$ 11,8) | +R$ 31,8 (+R$ 6,7) / −R$ 83,0 (−R$ 2,0) |
| Sinal anterior tomou STOP | +R$ 35,4 (−R$ 1,8) / +R$ 27,0 (−R$ 16,6) | −R$ 8,1 (−R$ 3,0) / +R$ 31,8 (−R$ 30,6) | +R$ 5,7 (+R$ 11,1) / +R$ 104,6 (−R$ 42,3) |

## Conclusoes

1. **Nao ha correlacao negativa estavel no segundo toque.** O 2o recuo da perna foi pior no treino (−R$ 32,9 x +R$ 17,4) e melhor no teste (+R$ 20,1 x +R$ 6,5), com impulso minimo de 200, 300 e 400 pts. Regime, nao regra.
2. **Sinal perto do anterior (ate 100 pts)**: um pouco pior e com stop cheio um pouco mais frequente; instavel (some com impulso minimo de 200). No mesmo preco nao e pior.
3. **Candidato a acompanhar**: segundo sinal 1 tijolo a favor do anterior (−R$ 17,7 x −R$ 5,2; teste −R$ 41,6). Treino empatado: nao usar como filtro ainda.

Reproduzir: `python segundo.py && python segundo_rel.py`.
