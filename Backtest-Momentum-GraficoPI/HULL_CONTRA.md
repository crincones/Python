# Hull 50 a favor + 2 a 4 candles + 1 contra

WINFUT, grafico de 20 PI, 50.611 candles, 132 pregoes (06/03/2026 a 14/09/2026). Resultado bruto. Graficos, curvas, MEP/MEN, duracao e trade a trade em `hull_contra.html`; plano em `PLANO_HULL.md`.

**O padrao** (compra; venda e o espelho): Hull 50 subindo no fechamento do candle contra, 2 a 4 candles de baixa, depois 1 de alta. Compra no fechamento dele.

## Qual pavio e avaliado

COMPRA (Hull 50 subindo, 2 ou 3 candles de baixa antes):

```
      |     <- AVALIADO: pavio de CIMA = maxima - fechamento <= 10% do corpo
    +---+   <- fechamento = entrada
    |   |
    |   |      candle de sinal, de ALTA (corpo 100)
    +---+   <- abertura
      |
      |     <- NAO avaliado: pavio de baixo (lado da abertura), qualquer tamanho
```

VENDA (Hull 50 descendo, 2 ou 3 candles de alta antes):

```
      |
      |     <- NAO avaliado: pavio de cima (lado da abertura), qualquer tamanho
    +---+   <- abertura
    |   |
    |   |      candle de sinal, de BAIXA (corpo 100)
    +---+   <- fechamento = entrada
      |     <- AVALIADO: pavio de BAIXO = fechamento - minima <= 10% do corpo
```

O pavio avaliado e sempre o do lado do **fechamento** do candle de sinal: o de cima na compra, o
de baixo na venda. O pavio do lado da abertura nao entra na regra.

## Resposta curta: a Hull a favor passou no teste fora da amostra; o resto, nao

| Entrada no fechamento, 1:3 com parcial | Sinais | Pts/sinal |
|:--|--:|--:|
| Hull a favor | 4.700 | +7,5 |
| Sem olhar a Hull | 11.065 | +2,6 |
| Hull contra | 6.365 | -1,1 |
| Invertido | 4.700 | -6,7 |
| **Candidato: Hull + 2-3 barras + pavio do fechamento ate 10%** | 3.703 | **+8,7** |

- **Hull a favor:** percentil 100 a 100 contra o sorteio nas 4 gestoes; dois lados (compra +8,1, venda +6,8).
- **Barras:** 3 antes +7,0, 4 antes +7,1.
- **Pavio do lado da abertura:** a faixa do magenta so funciona na compra (+10,0 contra +1,8 na venda) e perde na limitada; a do verde nao separa.
- **Pavio do lado do fechamento ate 10%:** +7,9 contra +4,4 acima disso; percentil 13 a 94.
- **Carteira Hull + 2-4** (1:3 com parcial): 4.373 trades (~33 por pregao), +35.300 pts brutos, fator 1,17, rebaixamento 4.700. A 5 pts de custo sobram +2,5 por sinal; a 10, -2,5.

## Fora da amostra

A Hull a favor era hipotese previa; "2 a 3 barras" e "fechamento ate 10%" foram escolhidos na base antiga (06/08 a 11/09). Pts por sinal, fechamento (t entre parenteses):

| Gestao | Regra | Antes (06/03-05/08) | Original (06/08-11/09) | Depois | Base inteira |
|:--|:--|--:|--:|--:|--:|
| 1:3 com parcial | Sem Hull | +1,5 (+1,1) | +6,2 (+2,4) | +12,8 (+1,1) | +2,6 |
| 1:3 com parcial | Hull contra | -2,2 (-1,3) | +2,3 (+0,7) | +17,4 (+1,1) | -1,1 |
| 1:3 com parcial | Hull + 2-4 | +6,5 (+3,2) | +11,3 (+2,8) | +7,1 (+0,4) | +7,5 |
| 1:3 com parcial | Candidato | +6,8 (+2,9) | +16,4 (+3,5) | +6,5 (+0,4) | +8,7 |
| 1:3 sem parcial | Sem Hull | +0,3 (+0,2) | +6,5 (+1,7) | +16,8 (+1,0) | +1,7 |
| 1:3 sem parcial | Hull contra | -4,7 (-1,9) | +0,9 (+0,2) | +21,7 (+1,0) | -3,3 |
| 1:3 sem parcial | Hull + 2-4 | +7,0 (+2,4) | +13,8 (+2,4) | +10,7 (+0,4) | +8,4 |
| 1:3 sem parcial | Candidato | +8,6 (+2,6) | +22,0 (+3,2) | +8,7 (+0,3) | +11,2 |
| 1:2 sem parcial | Sem Hull | +1,6 (+1,1) | +4,8 (+1,6) | +8,0 (+0,6) | +2,3 |
| 1:2 sem parcial | Hull contra | -2,8 (-1,4) | +1,8 (+0,5) | +13,0 (+0,7) | -1,7 |
| 1:2 sem parcial | Hull + 2-4 | +7,7 (+3,3) | +8,7 (+1,9) | +1,8 (+0,1) | +7,8 |
| 1:2 sem parcial | Candidato | +7,2 (+2,7) | +14,6 (+2,7) | -2,2 (-0,1) | +8,6 |
| 1:1 sem parcial | Sem Hull | +2,7 (+2,5) | +5,9 (+2,8) | +8,8 (+1,0) | +3,4 |
| 1:1 sem parcial | Hull contra | +0,3 (+0,2) | +3,7 (+1,3) | +13,0 (+1,1) | +1,1 |
| 1:1 sem parcial | Hull + 2-4 | +5,9 (+3,6) | +8,8 (+2,7) | +3,6 (+0,3) | +6,5 |
| 1:1 sem parcial | Candidato | +5,0 (+2,7) | +10,8 (+2,9) | +4,3 (+0,3) | +6,1 |

Mes a mes (1:3 com parcial): Hull + 2-4 03 +0,1 / 04 +15,0 / 05 +11,8 / 06 +0,9 / 07 +6,7 / 08 +11,6 / 09 +12,6; Hull contra 03 -0,6 / 04 -1,9 / 05 -2,2 / 06 -8,9 / 07 +2,6 / 08 +0,7 / 09 +4,8.

## 1. Hull contra os controles

| Entrada | Gestao | Hull a favor | Tercos | Sem Hull | Hull contra | Invertido | Percentil |
|:--|:--|--:|:--|--:|--:|--:|--:|
| Fechamento | 1:3 com parcial | +7,5 (4.700) | +6 / +6 / +11 | +2,6 (11.065) | -1,1 (6.365) | -6,7 (4.700) | 100 |
| Fechamento | 1:3 sem parcial | +8,4 (4.700) | +6 / +8 / +13 | +1,7 (11.065) | -3,3 (6.365) | -6,9 (4.700) | 100 |
| Fechamento | 1:2 sem parcial | +7,8 (4.700) | +10 / +3 / +9 | +2,3 (11.065) | -1,7 (6.365) | -5,8 (4.700) | 100 |
| Fechamento | 1:1 sem parcial | +6,5 (4.700) | +6 / +4 / +9 | +3,4 (11.065) | +1,1 (6.365) | -6,5 (4.700) | 100 |
| Limitada no meio do corpo | 1:3 com parcial | -1,9 (3.116) | -2 / -3 / -0 | -5,1 (7.452) | -7,4 (4.336) | n/a | 97 |
| Limitada no meio do corpo | 1:3 sem parcial | +6,4 (3.116) | +5 / +6 / +9 | +2,2 (7.452) | -0,8 (4.336) | n/a | 96 |
| Limitada no meio do corpo | 1:2 sem parcial | +6,4 (3.116) | +7 / +4 / +7 | +2,7 (7.452) | +0,1 (4.336) | n/a | 97 |
| Limitada no meio do corpo | 1:1 sem parcial | -10,2 (3.116) | -9 / -12 / -10 | -12,4 (7.452) | -14,0 (4.336) | n/a | 95 |

**Periodo da Hull** (fechamento, 1:3 com parcial, 2-4 barras):

| Hull | A favor | Contra |
|:--|--:|--:|
| Hull 21 | +2,6 (3.365) | +2,6 (7.700) |
| Hull 34 | +5,6 (4.251) | +0,7 (6.814) |
| Hull 50 | +7,5 (4.700) | -1,1 (6.365) |
| Hull 80 | +8,0 (4.991) | -1,9 (6.074) |

## 2. Barras antes (Hull a favor, fechamento, 1:3 com parcial)

| Barras | Sinais | Pts/sinal | T1 | T2 | T3 |
|:--|--:|--:|--:|--:|--:|
| 1 | 6.710 | +1,3 | -2,3 | +3,9 | +3,8 |
| 2 | 3.075 | +7,7 | +5,5 | +5,1 | +13,1 |
| 3 | 1.190 | +7,0 | +0,8 | +9,7 | +13,1 |
| 4 | 435 | +7,1 | +22,6 | +1,8 | -7,5 |
| 5+ | 132 | -0,8 | -4,6 | +3,1 | +2,9 |

## 3a. Pavio do lado da abertura do candle contra (Hull, 2-4, fechamento, 1:3 com parcial)

| Pavio | Sinais | Pts/sinal | T1 | T2 | T3 | Compra | Venda |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 0% | 119 | +18,1 | +29,1 | +17,1 | -1,7 | +23,6 | +13,6 |
| 5-10% | 679 | +14,3 | +17,0 | +5,0 | +18,7 | +4,5 | +23,8 |
| 10-25% | 957 | +3,7 | +0,2 | +8,6 | +3,7 | +7,5 | 0,0 |
| 25-45% | 1.059 | +7,9 | +5,5 | +8,1 | +11,0 | +11,9 | +4,1 |
| 45-65% | 815 | +6,5 | +0,6 | +10,1 | +10,1 | +13,3 | -0,8 |
| 65-90% | 784 | +2,2 | -2,9 | -6,9 | +17,5 | +2,3 | +2,1 |
| 90%+ | 255 | +14,7 | +20,4 | +10,1 | +9,9 | -2,7 | +32,3 |

## 3b. Pavio do lado do fechamento do candle contra (Hull, 2-4, fechamento, 1:3 com parcial)

| Pavio | Sinais | Pts/sinal | T1 | T2 | T3 | Compra | Venda |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 0% | 1.387 | +9,2 | +8,9 | +9,0 | +10,1 | +6,3 | +11,9 |
| 5-10% | 2.676 | +7,3 | +3,0 | +6,3 | +13,8 | +9,6 | +4,9 |
| 10-25% | 503 | +6,5 | +9,1 | +5,6 | +4,7 | +7,8 | +5,2 |
| 25%+ | 111 | -12,2 | +5,3 | -33,8 | -10,3 | -8,3 | -17,8 |

**Regras de pavio que ja existiam** (dentro de Hull + 2-4):

| Entrada | Gestao | Pavio da abertura 25-90% (magenta) | Pavio da abertura 5-25% (verde) | Pavio do fechamento ate 10% |
|:--|:--|--:|--:|--:|
| Fechamento | 1:3 com parcial | +5,8 (fora +10,2, pct 12) | +8,1 (fora +7,1, pct 58) | +7,9 (fora +4,4, pct 74) |
| Fechamento | 1:3 sem parcial | +6,7 (fora +11,4, pct 19) | +7,2 (fora +9,1, pct 35) | +10,0 (fora -1,7, pct 94) |
| Fechamento | 1:2 sem parcial | +5,7 (fora +11,5, pct 9) | +10,1 (fora +6,6, pct 79) | +8,7 (fora +2,4, pct 85) |
| Fechamento | 1:1 sem parcial | +5,0 (fora +9,0, pct 9) | +9,0 (fora +5,2, pct 89) | +5,9 (fora +10,5, pct 13) |
| Limitada no meio do corpo | 1:3 com parcial | -5,4 (fora +3,9, pct 2) | +3,0 (fora -4,5, pct 94) | -0,7 (fora -9,9, pct 91) |
| Limitada no meio do corpo | 1:3 sem parcial | +2,6 (fora +12,6, pct 6) | +11,6 (fora +3,6, pct 89) | +8,4 (fora -7,4, pct 95) |
| Limitada no meio do corpo | 1:2 sem parcial | +2,3 (fora +13,3, pct 2) | +13,3 (fora +2,8, pct 97) | +7,4 (fora -0,5, pct 84) |
| Limitada no meio do corpo | 1:1 sem parcial | -13,3 (fora -4,9, pct 1) | -5,7 (fora -12,5, pct 96) | -9,8 (fora -12,5, pct 69) |

## 4. Combinacoes (fechamento)

| Gestao | Regra | Sinais | Pts/sinal | Tercos | Compra | Venda | Pct | -10 custo |
|:--|:--|--:|--:|:--|--:|--:|--:|--:|
| 1:3 com parcial | Hull + 2 a 4 barras | 4.700 | +7,5 | +6 / +6 / +11 | +8,1 | +6,8 | - | -2,5 |
| 1:3 com parcial | Hull + 2 a 3 barras | 4.265 | +7,5 | +4 / +6 / +13 | +8,6 | +6,4 | 52 | -2,5 |
| 1:3 com parcial | Hull + 2 a 4 + fechamento ate 10% | 4.063 | +7,9 | +5 / +7 / +13 | +8,6 | +7,4 | 74 | -2,1 |
| 1:3 com parcial | Hull + 2 a 3 + fechamento ate 10% | 3.703 | +8,7 | +4 / +9 / +15 | +9,8 | +7,6 | 89 | -1,3 |
| 1:3 sem parcial | Hull + 2 a 4 barras | 4.700 | +8,4 | +6 / +8 / +13 | +9,7 | +7,2 | - | -1,6 |
| 1:3 sem parcial | Hull + 2 a 3 barras | 4.265 | +8,5 | +3 / +8 / +16 | +10,8 | +6,3 | 51 | -1,5 |
| 1:3 sem parcial | Hull + 2 a 4 + fechamento ate 10% | 4.063 | +10,0 | +6 / +10 / +16 | +11,4 | +8,7 | 94 | +0,0 |
| 1:3 sem parcial | Hull + 2 a 3 + fechamento ate 10% | 3.703 | +11,2 | +5 / +13 / +19 | +13,7 | +8,8 | 98 | +1,2 |
| 1:2 sem parcial | Hull + 2 a 4 barras | 4.700 | +7,8 | +10 / +3 / +9 | +9,0 | +6,7 | - | -2,2 |
| 1:2 sem parcial | Hull + 2 a 3 barras | 4.265 | +7,0 | +8 / +1 / +11 | +8,4 | +5,6 | 11 | -3,0 |
| 1:2 sem parcial | Hull + 2 a 4 + fechamento ate 10% | 4.063 | +8,7 | +9 / +4 / +12 | +10,1 | +7,4 | 85 | -1,3 |
| 1:2 sem parcial | Hull + 2 a 3 + fechamento ate 10% | 3.703 | +8,6 | +8 / +4 / +14 | +10,4 | +6,8 | 74 | -1,4 |
| 1:1 sem parcial | Hull + 2 a 4 barras | 4.700 | +6,5 | +6 / +4 / +9 | +6,5 | +6,5 | - | -3,5 |
| 1:1 sem parcial | Hull + 2 a 3 barras | 4.265 | +6,5 | +5 / +5 / +10 | +6,5 | +6,5 | 52 | -3,5 |
| 1:1 sem parcial | Hull + 2 a 4 + fechamento ate 10% | 4.063 | +5,9 | +5 / +4 / +9 | +5,7 | +6,1 | 13 | -4,1 |
| 1:1 sem parcial | Hull + 2 a 3 + fechamento ate 10% | 3.703 | +6,1 | +4 / +5 / +10 | +5,8 | +6,4 | 30 | -3,9 |

**Vizinhanca do candidato** (fechamento, 1:3 com parcial):

| Eixo | Valor | Sinais | Pts/sinal | T1 | T2 | T3 |
|:--|:--|--:|--:|--:|--:|--:|
| pavio do fechamento | fech <= 0% | 1.274 | +8,6 | +6,5 | +11,0 | +9,9 |
| pavio do fechamento | fech <= 5% | 3.031 | +8,2 | +4,0 | +7,4 | +15,7 |
| pavio do fechamento | fech <= 10% | 3.703 | +8,7 | +4,3 | +9,1 | +14,6 |
| pavio do fechamento | fech <= 15% | 3.970 | +8,5 | +4,1 | +8,6 | +14,5 |
| pavio do fechamento | fech <= 25% | 4.146 | +7,9 | +4,0 | +7,8 | +13,7 |
| pavio do fechamento | fech <= 100% | 4.245 | +7,3 | +3,8 | +6,3 | +13,3 |
| barras antes | 1 a 3 barras | 9.634 | +3,6 | -1,0 | +5,7 | +8,3 |
| barras antes | 2 a 2 barras | 2.681 | +9,2 | +5,6 | +7,8 | +15,6 |
| barras antes | 2 a 3 barras | 3.703 | +8,7 | +4,3 | +9,1 | +14,6 |
| barras antes | 2 a 4 barras | 4.063 | +7,9 | +5,2 | +7,1 | +12,7 |
| barras antes | 3 a 3 barras | 1.022 | +7,3 | +0,9 | +12,4 | +12,0 |
| barras antes | 1 a 4 barras | 9.994 | +3,5 | -0,4 | +5,0 | +7,7 |
| periodo da Hull | Hull 21 | 2.893 | +3,3 | -1,0 | +4,8 | +8,0 |
| periodo da Hull | Hull 34 | 3.451 | +6,9 | +1,3 | +6,6 | +15,4 |
| periodo da Hull | Hull 50 | 3.703 | +8,7 | +4,3 | +9,1 | +14,6 |
| periodo da Hull | Hull 80 | 3.818 | +9,6 | +7,1 | +9,4 | +13,5 |

## 5. O grau de inclinacao da Hull

**Resposta: o tamanho da inclinacao nao e filtro.** Vale o sentido (subindo/descendo), nao o grau. Inclinacao medida em pontos por barra, no sentido do trade; faixas = quintis (20% dos sinais cada).

**Hull + 2-4 -- 1 barra** (fechamento; pts por sinal por gestao; compra/venda no 1:3 com parcial)

| Quintil | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct (parcial) |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (mais plana) | 940 | +7,1 | +11,1 | +6,4 | +3,2 | +9 / +2 / +9 | +6,1 | +8,1 | 46 |
| Q2 | 940 | +5,2 | +5,4 | +7,1 | +5,0 | +4 / +1 / +11 | +4,2 | +6,3 | 27 |
| Q3 | 940 | +7,9 | +6,5 | +7,2 | +9,3 | +8 / +4 / +10 | +6,5 | +9,3 | 54 |
| Q4 | 940 | +7,8 | +6,7 | +10,6 | +8,8 | +3 / +14 / +9 | +9,1 | +6,6 | 53 |
| Q5 (mais inclinada) | 940 | +9,4 | +12,6 | +7,8 | +6,2 | +5 / +8 / +16 | +14,7 | +3,9 | 70 |

**Hull + 2-4 -- media de 5 barras** (fechamento; pts por sinal por gestao; compra/venda no 1:3 com parcial)

| Quintil | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct (parcial) |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (mais plana) | 940 | +2,4 | +3,1 | +1,6 | +1,7 | -4 / +5 / +10 | -6,3 | +11,0 | 8 |
| Q2 | 940 | +10,5 | +15,2 | +11,7 | +5,7 | +13 / +3 / +14 | +17,3 | +3,7 | 80 |
| Q3 | 940 | +10,8 | +11,2 | +13,1 | +10,4 | +14 / +2 / +15 | +8,8 | +12,8 | 82 |
| Q4 | 940 | +1,9 | -1,6 | +1,0 | +5,3 | -3 / +8 / +2 | +6,1 | -2,0 | 6 |
| Q5 (mais inclinada) | 940 | +11,8 | +14,4 | +11,8 | +9,3 | +10 / +11 / +15 | +14,7 | +9,0 | 89 |

**Hull + 2-4 -- 1 barra / ATR** (fechamento; pts por sinal por gestao; compra/venda no 1:3 com parcial)

| Quintil | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct (parcial) |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (mais plana) | 940 | +7,3 | +11,2 | +6,8 | +3,5 | +8 / +2 / +11 | +5,6 | +8,9 | 49 |
| Q2 | 940 | +4,8 | +4,9 | +6,7 | +4,7 | +5 / +1 / +8 | +4,3 | +5,3 | 23 |
| Q3 | 940 | +6,7 | +4,9 | +7,3 | +8,5 | +5 / +7 / +9 | +4,4 | +9,2 | 42 |
| Q4 | 940 | +8,3 | +7,9 | +8,6 | +8,7 | +5 / +13 / +9 | +11,4 | +5,5 | 59 |
| Q5 (mais inclinada) | 940 | +10,2 | +13,4 | +9,7 | +7,0 | +6 / +7 / +18 | +15,1 | +5,3 | 77 |

**Candidato -- 1 barra** (fechamento; pts por sinal por gestao; compra/venda no 1:3 com parcial)

| Quintil | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct (parcial) |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (mais plana) | 741 | +6,8 | +11,1 | +4,6 | +2,6 | +7 / +3 / +9 | +7,0 | +6,6 | 32 |
| Q2 | 740 | +6,8 | +7,6 | +8,1 | +5,9 | +2 / +7 / +14 | +9,4 | +4,1 | 31 |
| Q3 | 741 | +13,4 | +14,4 | +11,7 | +12,4 | +8 / +14 / +20 | +11,6 | +15,3 | 87 |
| Q4 | 740 | +6,6 | +7,3 | +9,6 | +5,9 | -0 / +15 / +10 | +7,4 | +6,0 | 30 |
| Q5 (mais inclinada) | 741 | +9,7 | +15,8 | +8,8 | +3,6 | +4 / +7 / +19 | +13,0 | +6,4 | 60 |

**Candidato -- media de 5 barras** (fechamento; pts por sinal por gestao; compra/venda no 1:3 com parcial)

| Quintil | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct (parcial) |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (mais plana) | 741 | +3,8 | +6,5 | +2,4 | +1,2 | -3 / +7 / +12 | -2,5 | +10,4 | 11 |
| Q2 | 740 | +11,2 | +16,9 | +11,2 | +5,5 | +13 / +5 / +15 | +18,7 | +3,8 | 73 |
| Q3 | 741 | +13,2 | +14,6 | +15,9 | +11,7 | +12 / +7 / +21 | +12,1 | +14,2 | 86 |
| Q4 | 740 | +3,1 | +0,7 | +0,1 | +5,5 | -7 / +15 / +6 | +4,3 | +2,0 | 9 |
| Q5 (mais inclinada) | 741 | +12,0 | +17,5 | +13,1 | +6,5 | +7 / +11 / +19 | +16,3 | +8,0 | 79 |

**Candidato -- 1 barra / ATR** (fechamento; pts por sinal por gestao; compra/venda no 1:3 com parcial)

| Quintil | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct (parcial) |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (mais plana) | 741 | +7,2 | +11,2 | +5,5 | +3,2 | +6 / +5 / +11 | +8,6 | +5,9 | 35 |
| Q2 | 740 | +5,7 | +6,5 | +7,7 | +4,9 | +3 / +3 / +11 | +6,0 | +5,4 | 23 |
| Q3 | 741 | +13,7 | +15,4 | +11,6 | +12,0 | +6 / +17 / +22 | +11,6 | +15,9 | 89 |
| Q4 | 740 | +4,9 | +4,6 | +6,4 | +5,1 | -1 / +14 / +6 | +6,6 | +3,3 | 18 |
| Q5 (mais inclinada) | 741 | +11,9 | +18,5 | +11,6 | +5,3 | +7 / +7 / +23 | +15,9 | +8,1 | 78 |

**Cortando pela inclinacao** (candidato, fechamento, 1:3 com parcial):

| Medida | Todos | Sem os 20% mais planos | Sem os 40% | Sem os 60% |
|:--|--:|--:|--:|--:|
| 1 barra | +8,7 (3.703) | +9,1 (2.962) | +9,9 (2.222) | +8,2 (1.481) |
| media de 5 barras | +8,7 (3.703) | +9,9 (2.962) | +9,4 (2.222) | +7,6 (1.481) |
| 1 barra / ATR | +8,7 (3.703) | +9,0 (2.962) | +10,1 (2.222) | +8,4 (1.481) |

- As faixas nao seguem ordem, e compra e venda discordam (Hull muito inclinada: compra +14,7, venda +3,9).
- O indicio da base antiga (Hull quase plana na media de 5 barras e a pior faixa) nao se confirmou: percentil 7-20 no candidato, e as faixas de 5 barras vao e voltam.


## 6. A separacao da Hull: EMA 21 e bandas de Keltner

> As bandas sao EMA 21 +/- 2 ATR. Em ATR e no sentido do trade, distancia da Hull a banda a favor = 2 - distancia da Hull a EMA (conferido em todos os sinais): "perto da banda" e "longe da EMA" sao a mesma variavel. So diferem em pontos ou sem sinal.

**Hull + 2-4 -- Hull - EMA em ATR, zonas do canal** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Hull do lado errado da EMA | 1.782 | +3,3 | +4,3 | +4,1 | +2,3 | -2 / -1 / +16 | +3,5 | +3,1 | 4 |
| EMA ate meio canal (0-1 ATR) | 1.641 | +9,0 | +11,2 | +10,5 | +6,9 | +9 / +11 / +8 | +11,4 | +6,8 | 75 |
| meio canal ate banda (1-2 ATR) | 967 | +10,7 | +9,0 | +7,5 | +12,4 | +13 / +11 / +8 | +9,8 | +11,6 | 82 |
| alem da banda (> 2 ATR) | 310 | +12,9 | +16,1 | +16,1 | +9,7 | +24 / +5 / +10 | +13,2 | +12,7 | 78 |

**Hull + 2-4 -- Hull - EMA em ATR, faixas finas** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| < -1 ATR | 511 | -6,1 | -9,2 | -4,3 | -2,9 | -26 / -2 / +19 | -17,7 | +6,0 | 1 |
| -1 a -0,5 | 522 | +8,7 | +8,0 | +9,2 | +9,4 | +14 / -1 / +11 | +17,0 | 0,0 | 61 |
| -0,5 a 0 | 749 | +5,9 | +10,9 | +6,3 | +0,9 | +2 / -0 / +18 | +8,6 | +3,2 | 35 |
| 0 a 0,5 | 835 | +5,4 | +7,3 | +6,0 | +3,6 | +5 / +9 / +3 | +5,1 | +5,8 | 30 |
| 0,5 a 1 | 806 | +12,8 | +15,1 | +15,1 | +10,4 | +13 / +14 / +12 | +18,0 | +7,9 | 91 |
| 1 a 2 | 967 | +10,7 | +9,0 | +7,5 | +12,4 | +13 / +11 / +8 | +9,8 | +11,6 | 82 |
| > 2 ATR | 310 | +12,9 | +16,1 | +16,1 | +9,7 | +24 / +5 / +10 | +13,2 | +12,7 | 78 |

**Hull + 2-4 -- Hull - EMA em pontos (quintis)** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (menor) | 940 | +0,5 | -2,1 | +2,1 | +3,1 | -9 / -1 / +16 | -3,2 | +4,4 | 3 |
| Q2 | 940 | +5,1 | +10,5 | +6,1 | -0,4 | +3 / -6 / +18 | +9,4 | +0,6 | 26 |
| Q3 | 940 | +8,8 | +11,8 | +9,1 | +5,7 | +9 / +15 / +2 | +11,7 | +6,1 | 64 |
| Q4 | 940 | +12,1 | +10,5 | +10,7 | +13,7 | +13 / +13 / +10 | +14,6 | +9,8 | 90 |
| Q5 (maior) | 940 | +10,9 | +11,5 | +11,1 | +10,3 | +14 / +9 / +9 | +8,7 | +12,9 | 83 |

**Hull + 2-4 -- Hull - banda a favor em pontos (quintis)** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (menor) | 940 | +11,6 | +12,1 | +11,9 | +11,2 | +16 / +10 / +8 | +8,7 | +14,4 | 88 |
| Q2 | 940 | +12,9 | +13,3 | +11,2 | +12,4 | +14 / +11 / +13 | +16,8 | +9,1 | 93 |
| Q3 | 940 | +5,8 | +7,0 | +8,1 | +4,6 | +4 / +16 / -1 | +8,3 | +3,4 | 33 |
| Q4 | 940 | +5,5 | +10,2 | +3,3 | +0,7 | +4 / -5 / +19 | +8,6 | +2,5 | 30 |
| Q5 (maior) | 940 | +1,5 | -0,4 | +4,7 | +3,5 | -6 / -2 / +16 | -1,1 | +4,5 | 5 |

**Hull + 2-4 -- |Hull - EMA| em ATR, sem sinal (quintis)** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (menor) | 940 | +8,7 | +13,8 | +6,8 | +3,6 | +2 / +10 / +17 | +10,9 | +6,5 | 63 |
| Q2 | 940 | +2,3 | +3,8 | +6,2 | +0,9 | +6 / -5 / +3 | +5,0 | -0,1 | 8 |
| Q3 | 940 | +10,9 | +9,7 | +11,6 | +12,1 | +11 / +11 / +11 | +15,7 | +5,9 | 83 |
| Q4 | 940 | +8,2 | +8,3 | +7,6 | +8,1 | +3 / +9 / +15 | +4,2 | +11,9 | 58 |
| Q5 (maior) | 940 | +7,2 | +6,6 | +7,0 | +7,8 | +7 / +6 / +9 | +4,3 | +10,0 | 47 |

**Hull + 2-4 -- Barras seguidas com Hull colada na EMA** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| 0 (nao colada) | 3.928 | +8,2 | +8,6 | +8,5 | +7,8 | +7 / +6 / +11 | +8,9 | +7,5 | 79 |
| 1-2 barras | 338 | +5,5 | +8,9 | +1,8 | +2,1 | -6 / -7 / +34 | +11,5 | 0,0 | 38 |
| 3-5 barras | 224 | +3,3 | +9,4 | +12,5 | -2,7 | +3 / +11 / -3 | -3,8 | +11,4 | 29 |
| 6-10 barras | 144 | -5,6 | -5,6 | -6,2 | -5,6 | +9 / +4 / -34 | 0,0 | -11,0 | 10 |
| 11+ barras | 66 | +18,2 | +27,3 | +13,6 | +9,1 | +4 / +29 / +29 | +5,9 | +31,2 | 75 |

**Candidato -- Hull - EMA em ATR, zonas do canal** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Hull do lado errado da EMA | 1.453 | +4,6 | +7,2 | +4,3 | +2,1 | -2 / +1 / +19 | +4,4 | +4,9 | 6 |
| EMA ate meio canal (0-1 ATR) | 1.273 | +11,7 | +16,4 | +13,1 | +7,0 | +9 / +16 / +13 | +15,8 | +7,7 | 85 |
| meio canal ate banda (1-2 ATR) | 757 | +8,3 | +6,7 | +5,4 | +9,8 | +6 / +12 / +8 | +6,5 | +9,9 | 47 |
| alem da banda (> 2 ATR) | 220 | +19,1 | +23,6 | +21,4 | +14,5 | +22 / +15 / +21 | +22,8 | +16,0 | 90 |

**Candidato -- Hull - EMA em ATR, faixas finas** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| < -1 ATR | 427 | -4,2 | -6,3 | -4,4 | -2,1 | -27 / +5 / +20 | -11,6 | +3,3 | 1 |
| -1 a -0,5 | 431 | +10,1 | +10,7 | +11,1 | +9,5 | +17 / -4 / +14 | +17,1 | +2,8 | 61 |
| -0,5 a 0 | 595 | +7,1 | +14,3 | +5,5 | -0,2 | +1 / +1 / +22 | +6,7 | +7,4 | 37 |
| 0 a 0,5 | 641 | +6,7 | +10,1 | +7,0 | +3,3 | +3 / +15 / +4 | +8,5 | +5,0 | 33 |
| 0,5 a 1 | 632 | +16,8 | +22,8 | +19,3 | +10,8 | +14 / +17 / +22 | +23,5 | +10,5 | 96 |
| 1 a 2 | 757 | +8,3 | +6,7 | +5,4 | +9,8 | +6 / +12 / +8 | +6,5 | +9,9 | 47 |
| > 2 ATR | 220 | +19,1 | +23,6 | +21,4 | +14,5 | +22 / +15 / +21 | +22,8 | +16,0 | 90 |

**Candidato -- Hull - EMA em pontos (quintis)** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (menor) | 741 | +2,0 | +1,1 | +2,7 | +2,8 | -10 / +3 / +17 | +0,1 | +3,8 | 5 |
| Q2 | 740 | +8,1 | +14,6 | +7,2 | +1,6 | +6 / -4 / +24 | +8,8 | +7,4 | 44 |
| Q3 | 741 | +6,3 | +10,7 | +7,0 | +2,0 | +2 / +14 / +5 | +11,4 | +1,6 | 28 |
| Q4 | 740 | +17,3 | +20,8 | +16,6 | +13,8 | +15 / +17 / +22 | +23,5 | +11,4 | 98 |
| Q5 (maior) | 741 | +9,6 | +9,0 | +9,3 | +10,3 | +8 / +14 / +7 | +5,3 | +13,5 | 59 |

**Candidato -- Hull - banda a favor em pontos (quintis)** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (menor) | 741 | +9,0 | +8,0 | +8,5 | +10,0 | +8 / +13 / +6 | +5,6 | +12,0 | 52 |
| Q2 | 740 | +17,8 | +22,8 | +17,7 | +12,8 | +14 / +17 / +24 | +25,7 | +10,5 | 99 |
| Q3 | 741 | +4,3 | +7,0 | +5,5 | +1,6 | +2 / +10 / +2 | +5,3 | +3,3 | 14 |
| Q4 | 740 | +9,6 | +17,3 | +6,4 | +1,9 | +6 / +1 / +24 | +12,3 | +7,1 | 58 |
| Q5 (maior) | 741 | +2,6 | +1,1 | +4,7 | +4,2 | -8 / +4 / +17 | +0,7 | +4,7 | 7 |

**Candidato -- |Hull - EMA| em ATR, sem sinal (quintis)** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (menor) | 741 | +9,5 | +15,5 | +6,2 | +3,5 | +1 / +17 / +15 | +11,7 | +7,2 | 58 |
| Q2 | 740 | +4,3 | +8,2 | +7,7 | +0,3 | +6 / -5 / +11 | +6,3 | +2,3 | 14 |
| Q3 | 741 | +14,4 | +16,6 | +15,9 | +12,1 | +15 / +9 / +18 | +19,7 | +8,7 | 92 |
| Q4 | 740 | +8,2 | +9,2 | +5,9 | +7,3 | -4 / +12 / +22 | +5,9 | +10,4 | 46 |
| Q5 (maior) | 741 | +7,0 | +6,6 | +7,0 | +7,3 | +3 / +12 / +7 | +4,1 | +9,5 | 33 |

**Candidato -- Barras seguidas com Hull colada na EMA** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| 0 (nao colada) | 3.106 | +9,5 | +11,6 | +9,5 | +7,5 | +6 / +8 / +16 | +10,8 | +8,4 | 83 |
| 1-2 barras | 264 | +4,9 | +11,0 | -0,4 | -1,1 | -9 / -4 / +34 | +11,2 | -0,7 | 30 |
| 3-5 barras | 165 | +2,1 | +7,3 | +7,3 | -3,0 | -8 / +24 / -2 | -5,9 | +12,7 | 26 |
| 6-10 barras | 119 | -1,7 | +0,8 | +3,4 | -4,2 | +21 / +8 / -44 | +10,0 | -13,6 | 18 |
| 11+ barras | 49 | +20,4 | +30,6 | +16,3 | +10,2 | -5 / +71 / +8 | 0,0 | +45,5 | 73 |

- **Hull alem da banda a favor** (7% dos sinais): +12,9, +16,1, +16,1, +9,7 nas 4 gestoes -- a exaustao pela banda nao se confirma.
- **Hull ainda do lado oposto da EMA** (38% dos sinais): a PIOR zona (+3,3); a faixa mais extrema (< -1 ATR) mede -4,2, -6,3, -4,4, -2,1 no candidato. Na base antiga era a melhor: a hipotese se inverteu.
- **Em pontos:** quanto mais perto da banda a favor, melhor (+11,6 a +1,5).
- **Consolidacao:** nao confirmada; Hull mais proxima da EMA mede +8,7, mais afastada +7,2; tempo colada tem poucos casos.


## 7. Carteira, uma posicao por vez

| Entrada | Gestao | Regra | Trades | Pts | Fator | Acerto | Rebaix. | MC lucro | MC rebaix. p95 |
|:--|:--|:--|--:|--:|--:|--:|--:|--:|--:|
| Fechamento | 1:3 com parcial | Candidato | 3.479 | +31.700 | 1,20 | 28,1% | 5.100 | 100% | 5.200 |
| Fechamento | 1:3 com parcial | Hull 2-4 | 4.373 | +35.300 | 1,17 | 27,4% | 4.700 | 100% | 6.000 |
| Fechamento | 1:3 com parcial | Sem Hull | 7.500 | +20.150 | 1,06 | 25,6% | 14.200 | 98% | 12.750 |
| Fechamento | 1:3 sem parcial | Candidato | 3.479 | +41.400 | 1,17 | 28,1% | 6.600 | 100% | 7.800 |
| Fechamento | 1:3 sem parcial | Hull 2-4 | 4.373 | +40.400 | 1,13 | 27,4% | 6.200 | 100% | 9.900 |
| Fechamento | 1:3 sem parcial | Sem Hull | 7.500 | +12.800 | 1,02 | 25,5% | 23.700 | 80% | 24.900 |
| Fechamento | 1:2 sem parcial | Candidato | 3.673 | +32.000 | 1,14 | 36,2% | 5.800 | 100% | 7.100 |
| Fechamento | 1:2 sem parcial | Hull 2-4 | 4.646 | +38.000 | 1,13 | 36,1% | 6.900 | 100% | 7.600 |
| Fechamento | 1:2 sem parcial | Sem Hull | 8.929 | +24.900 | 1,04 | 34,2% | 19.900 | 97% | 16.900 |
| Fechamento | 1:1 sem parcial | Candidato | 3.703 | +22.600 | 1,13 | 53,0% | 4.900 | 100% | 4.900 |
| Fechamento | 1:1 sem parcial | Hull 2-4 | 4.700 | +30.500 | 1,14 | 53,1% | 4.500 | 100% | 4.900 |
| Fechamento | 1:1 sem parcial | Sem Hull | 11.065 | +37.700 | 1,07 | 51,6% | 8.800 | 100% | 8.900 |
| Limitada no meio do corpo | 1:3 com parcial | Candidato | 2.366 | -1.000 | 0,99 | 27,4% | 7.650 | 44% | 14.475 |
| Limitada no meio do corpo | 1:3 com parcial | Hull 2-4 | 2.939 | -8.400 | 0,95 | 26,7% | 12.425 | 12% | 22.052 |
| Limitada no meio do corpo | 1:3 com parcial | Sem Hull | 5.948 | -39.425 | 0,88 | 25,3% | 42.950 | 0% | 57.052 |
| Limitada no meio do corpo | 1:3 sem parcial | Candidato | 2.366 | +20.150 | 1,12 | 27,3% | 6.700 | 99% | 9.002 |
| Limitada no meio do corpo | 1:3 sem parcial | Hull 2-4 | 2.939 | +15.700 | 1,07 | 26,5% | 6.750 | 95% | 12.150 |
| Limitada no meio do corpo | 1:3 sem parcial | Sem Hull | 5.948 | +1.500 | 1,00 | 25,2% | 13.450 | 55% | 28.300 |
| Limitada no meio do corpo | 1:2 sem parcial | Candidato | 2.452 | +19.250 | 1,12 | 36,1% | 5.150 | 100% | 7.050 |
| Limitada no meio do corpo | 1:2 sem parcial | Hull 2-4 | 3.061 | +17.950 | 1,09 | 35,4% | 5.350 | 99% | 8.502 |
| Limitada no meio do corpo | 1:2 sem parcial | Sem Hull | 6.776 | +16.350 | 1,04 | 34,2% | 9.250 | 92% | 16.252 |
| Limitada no meio do corpo | 1:1 sem parcial | Candidato | 2.487 | -21.350 | 0,84 | 45,6% | 22.550 | 0% | 30.550 |
| Limitada no meio do corpo | 1:1 sem parcial | Hull 2-4 | 3.116 | -31.700 | 0,82 | 44,8% | 32.400 | 0% | 41.402 |
| Limitada no meio do corpo | 1:1 sem parcial | Sem Hull | 7.452 | -92.450 | 0,78 | 43,7% | 92.900 | 0% | 107.100 |

## Conclusao

- **A Hull 50 a favor e real:** hipotese previa, mede +6,5 pts por sinal (t = +3,18) nos meses que nunca participaram de nada, sem mes negativo, nos dois lados.
- **E pequena:** +7,5 pts brutos por sinal na base inteira (a janela antiga media +11,3), com ~33 operacoes por pregao. O custo real decide se ha setup.
- **Os cortes do candidato nao acrescentam nada fora da amostra:** +6,8 contra +6,5 sem eles.
- **Pavio da abertura, grau de inclinacao, distancia a banda:** nenhum e filtro. A distancia da Hull a EMA mede ao contrario do que a base antiga sugeria.
- **Entrada no fechamento**, nao na limitada.

> 132 pregoes, um instrumento, resultado bruto. O plano provisorio (`PLANO_HULL.md`) usa a regra que passou no teste -- Hull a favor + 2 a 4 candles -- e so vale com custo real bem abaixo do valor por sinal.

Reproduzir: `python hull_contra.py && python hull_inclinacao.py && python hull_distancias.py && python relatorio_hull.py`.
