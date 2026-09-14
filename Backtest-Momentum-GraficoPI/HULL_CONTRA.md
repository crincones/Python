# Hull 50 a favor + 2 a 4 candles + 1 contra

WINFUT, grafico de 20 PI, 10.000 candles, 26 pregoes (06/08/2026 a 11/09/2026). Resultado bruto. Graficos, curvas, MEP/MEN, duracao e trade a trade em `hull_contra.html`; plano em `PLANO_HULL.md`.

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

## Resposta curta: a Hull muda o jogo

| Entrada no fechamento, 1:3 com parcial | Sinais | Pts/sinal |
|:--|--:|--:|
| Hull a favor | 922 | +11,4 |
| Sem olhar a Hull | 2.150 | +5,8 |
| Hull contra | 1.228 | +1,7 |
| Invertido | 922 | -12,7 |
| **Candidato: Hull + 2-3 barras + pavio do fechamento ate 10%** | 707 | **+16,7** |

- **Hull a favor:** percentil 87 a 96 contra o sorteio nas 4 gestoes; dois lados (compra +15,9, venda +6,8).
- **Barras:** 3 antes +20,1, 4 antes -9,2.
- **Pavio do lado da abertura:** a faixa do magenta so funciona na compra (+28,0 contra +2,7 na venda) e perde na limitada; a do verde nao separa.
- **Pavio do lado do fechamento ate 10%:** +14,6 contra -6,4 acima disso; percentil 84 a 98.
- **Carteira do candidato** (1:3 com parcial): 669 trades, +11.800 pts (R$ +2.360,00), fator 1,40, acerto 30,8%, rebaixamento 1.400 pts.

## 1. Hull contra os controles

| Entrada | Gestao | Hull a favor | Tercos | Sem Hull | Hull contra | Invertido | Percentil |
|:--|:--|--:|:--|--:|--:|--:|--:|
| Fechamento | 1:3 com parcial | +11,4 (922) | +16 / +7 / +13 | +5,8 (2.150) | +1,7 (1.228) | -12,7 (922) | 96 |
| Fechamento | 1:3 sem parcial | +13,4 (922) | +22 / +8 / +14 | +5,8 (2.150) | +0,1 (1.228) | -16,1 (922) | 96 |
| Fechamento | 1:2 sem parcial | +8,4 (922) | +14 / +7 / +7 | +4,3 (2.150) | +1,2 (1.228) | -11,3 (922) | 87 |
| Fechamento | 1:1 sem parcial | +9,3 (922) | +9 / +6 / +12 | +5,9 (2.150) | +3,3 (1.228) | -9,3 (922) | 92 |
| Limitada no meio do corpo | 1:3 com parcial | +5,2 (599) | -16 / +10 / +10 | -1,0 (1.426) | -5,4 (827) | n/a | 94 |
| Limitada no meio do corpo | 1:3 sem parcial | +15,7 (599) | -13 / +22 / +23 | +9,2 (1.426) | +4,5 (827) | n/a | 88 |
| Limitada no meio do corpo | 1:2 sem parcial | +13,1 (599) | -6 / +21 / +15 | +8,1 (1.426) | +4,5 (827) | n/a | 86 |
| Limitada no meio do corpo | 1:1 sem parcial | -5,3 (599) | -18 / -2 / -2 | -11,1 (1.426) | -15,4 (827) | n/a | 97 |

**Periodo da Hull** (fechamento, 1:3 com parcial, 2-4 barras):

| Hull | A favor | Contra |
|:--|--:|--:|
| Hull 21 | +7,0 (657) | +5,3 (1.493) |
| Hull 34 | +13,2 (821) | +1,3 (1.329) |
| Hull 50 | +11,4 (922) | +1,7 (1.228) |
| Hull 80 | +6,5 (997) | +5,2 (1.153) |

## 2. Barras antes (Hull a favor, fechamento, 1:3 com parcial)

| Barras | Sinais | Pts/sinal | T1 | T2 | T3 |
|:--|--:|--:|--:|--:|--:|
| 1 | 1.278 | +7,1 | +8,0 | +11,7 | +3,5 |
| 2 | 580 | +11,2 | +17,4 | -1,0 | +17,4 |
| 3 | 244 | +20,1 | +27,5 | +26,3 | +12,8 |
| 4 | 98 | -9,2 | -26,3 | +7,7 | -17,5 |
| 5+ | 20 | -5,0 | +50,0 | +22,2 | -44,4 |

## 3a. Pavio do lado da abertura do candle contra (Hull, 2-4, fechamento, 1:3 com parcial)

| Pavio | Sinais | Pts/sinal | T1 | T2 | T3 | Compra | Venda |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 0% | 18 | -5,6 | +25,0 | 0,0 | -22,2 | +14,3 | -18,2 |
| 5-10% | 135 | +17,0 | +48,1 | -6,0 | +22,4 | +7,1 | +27,7 |
| 10-25% | 192 | +6,2 | +2,2 | +25,8 | -5,9 | 0,0 | +12,8 |
| 25-45% | 200 | +14,0 | -2,5 | +13,7 | +21,8 | +34,3 | -9,8 |
| 45-65% | 174 | +11,5 | +6,1 | -2,0 | +21,1 | +22,9 | +1,1 |
| 65-90% | 148 | +19,6 | +37,0 | +7,4 | +22,4 | +18,3 | +20,8 |
| 90%+ | 49 | -6,1 | +26,7 | -28,6 | -15,0 | +8,0 | -20,8 |

## 3b. Pavio do lado do fechamento do candle contra (Hull, 2-4, fechamento, 1:3 com parcial)

| Pavio | Sinais | Pts/sinal | T1 | T2 | T3 | Compra | Venda |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 0% | 248 | +6,9 | +3,6 | +8,4 | +7,3 | +8,1 | +5,6 |
| 5-10% | 534 | +18,2 | +25,7 | +14,8 | +17,6 | +24,4 | +11,9 |
| 10-25% | 108 | -8,3 | +13,8 | -36,1 | 0,0 | -3,7 | -13,0 |
| 25%+ | 29 | +3,4 | -40,0 | 0,0 | +18,8 | +4,8 | 0,0 |

**Regras de pavio que ja existiam** (dentro de Hull + 2-4):

| Entrada | Gestao | Pavio da abertura 25-90% (magenta) | Pavio da abertura 5-25% (verde) | Pavio do fechamento ate 10% |
|:--|:--|--:|--:|--:|
| Fechamento | 1:3 com parcial | +15,3 (fora +4,7, pct 89) | +10,7 (fora +11,8, pct 43) | +14,6 (fora -6,4, pct 97) |
| Fechamento | 1:3 sem parcial | +20,8 (fora +0,9, pct 95) | +9,5 (fora +15,6, pct 30) | +18,4 (fora -14,3, pct 98) |
| Fechamento | 1:2 sem parcial | +12,6 (fora +1,2, pct 88) | +8,0 (fora +8,6, pct 47) | +11,6 (fora -10,0, pct 94) |
| Fechamento | 1:1 sem parcial | +9,8 (fora +8,5, pct 57) | +11,9 (fora +7,9, pct 71) | +10,7 (fora +1,4, pct 84) |
| Limitada no meio do corpo | 1:3 com parcial | -0,1 (fora +14,0, pct 10) | +6,3 (fora +4,6, pct 58) | +9,0 (fora -15,5, pct 95) |
| Limitada no meio do corpo | 1:3 sem parcial | +9,5 (fora +25,8, pct 15) | +16,7 (fora +15,1, pct 55) | +21,5 (fora -16,3, pct 97) |
| Limitada no meio do corpo | 1:2 sem parcial | +11,4 (fora +15,9, pct 37) | +11,2 (fora +14,1, pct 41) | +15,7 (fora -1,1, pct 83) |
| Limitada no meio do corpo | 1:1 sem parcial | -9,8 (fora +2,2, pct 8) | -4,1 (fora -5,9, pct 57) | -3,6 (fora -14,7, pct 82) |

## 4. Combinacoes (fechamento)

| Gestao | Regra | Sinais | Pts/sinal | Tercos | Compra | Venda | Pct | -10 custo |
|:--|:--|--:|--:|:--|--:|--:|--:|--:|
| 1:3 com parcial | Hull + 2 a 4 barras | 922 | +11,4 | +16 / +7 / +13 | +15,9 | +6,8 | - | +1,4 |
| 1:3 com parcial | Hull + 2 a 3 barras | 824 | +13,8 | +20 / +7 / +16 | +19,2 | +8,2 | 95 | +3,8 |
| 1:3 com parcial | Hull + 2 a 4 + fechamento ate 10% | 782 | +14,6 | +18 / +13 / +14 | +19,3 | +9,9 | 97 | +4,6 |
| 1:3 com parcial | Hull + 2 a 3 + fechamento ate 10% | 707 | +16,7 | +22 / +12 / +18 | +21,8 | +11,4 | 99 | +6,7 |
| 1:3 sem parcial | Hull + 2 a 4 barras | 922 | +13,4 | +22 / +8 / +14 | +20,9 | +5,9 | - | +3,4 |
| 1:3 sem parcial | Hull + 2 a 3 barras | 824 | +17,7 | +31 / +8 / +18 | +26,8 | +8,2 | 98 | +7,7 |
| 1:3 sem parcial | Hull + 2 a 4 + fechamento ate 10% | 782 | +18,4 | +25 / +17 / +17 | +27,0 | +9,9 | 98 | +8,4 |
| 1:3 sem parcial | Hull + 2 a 3 + fechamento ate 10% | 707 | +21,9 | +32 / +16 / +22 | +31,7 | +12,0 | 100 | +11,9 |
| 1:2 sem parcial | Hull + 2 a 4 barras | 922 | +8,4 | +14 / +7 / +7 | +11,4 | +5,3 | - | -1,6 |
| 1:2 sem parcial | Hull + 2 a 3 barras | 824 | +11,4 | +21 / +7 / +10 | +15,2 | +7,4 | 96 | +1,4 |
| 1:2 sem parcial | Hull + 2 a 4 + fechamento ate 10% | 782 | +11,6 | +17 / +11 / +9 | +15,4 | +7,9 | 94 | +1,6 |
| 1:2 sem parcial | Hull + 2 a 3 + fechamento ate 10% | 707 | +14,6 | +22 / +12 / +13 | +19,0 | +10,0 | 99 | +4,6 |
| 1:1 sem parcial | Hull + 2 a 4 barras | 922 | +9,3 | +9 / +6 / +12 | +11,0 | +7,7 | - | -0,7 |
| 1:1 sem parcial | Hull + 2 a 3 barras | 824 | +10,0 | +10 / +5 / +14 | +11,6 | +8,2 | 67 | -0,0 |
| 1:1 sem parcial | Hull + 2 a 4 + fechamento ate 10% | 782 | +10,7 | +10 / +9 / +12 | +11,6 | +9,9 | 84 | +0,7 |
| 1:1 sem parcial | Hull + 2 a 3 + fechamento ate 10% | 707 | +11,5 | +11 / +7 / +15 | +12,0 | +10,9 | 88 | +1,5 |

**Vizinhanca do candidato** (fechamento, 1:3 com parcial):

| Eixo | Valor | Sinais | Pts/sinal | T1 | T2 | T3 |
|:--|:--|--:|--:|--:|--:|--:|
| pavio do fechamento | fech <= 0% | 229 | +7,4 | +5,5 | +2,7 | +12,0 |
| pavio do fechamento | fech <= 5% | 565 | +17,3 | +22,0 | +14,3 | +17,4 |
| pavio do fechamento | fech <= 10% | 707 | +16,7 | +21,7 | +11,6 | +18,1 |
| pavio do fechamento | fech <= 15% | 758 | +15,0 | +21,8 | +8,7 | +16,6 |
| pavio do fechamento | fech <= 25% | 797 | +14,3 | +22,2 | +6,4 | +16,4 |
| pavio do fechamento | fech <= 100% | 821 | +14,0 | +20,3 | +6,6 | +16,4 |
| barras antes | 1 a 3 barras | 1.823 | +10,9 | +12,3 | +11,9 | +9,5 |
| barras antes | 2 a 2 barras | 498 | +15,5 | +20,4 | +4,2 | +21,3 |
| barras antes | 2 a 3 barras | 707 | +16,7 | +21,7 | +11,6 | +18,1 |
| barras antes | 2 a 4 barras | 782 | +14,6 | +17,8 | +12,8 | +14,5 |
| barras antes | 3 a 3 barras | 209 | +19,6 | +25,0 | +29,4 | +10,9 |
| barras antes | 1 a 4 barras | 1.898 | +10,2 | +11,0 | +12,4 | +8,3 |
| periodo da Hull | Hull 21 | 553 | +7,6 | +10,4 | -0,5 | +12,6 |
| periodo da Hull | Hull 34 | 642 | +18,7 | +25,0 | +4,8 | +25,7 |
| periodo da Hull | Hull 50 | 707 | +16,7 | +21,7 | +11,6 | +18,1 |
| periodo da Hull | Hull 80 | 740 | +11,1 | +17,2 | +9,3 | +9,5 |

## 5. O grau de inclinacao da Hull

**Resposta: o tamanho da inclinacao nao e filtro.** Vale o sentido (subindo/descendo), nao o grau. Inclinacao medida em pontos por barra, no sentido do trade; faixas = quintis (20% dos sinais cada).

**Hull + 2-4 -- 1 barra** (fechamento; pts por sinal por gestao; compra/venda no 1:3 com parcial)

| Quintil | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct (parcial) |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (mais plana) | 185 | +14,6 | +22,7 | +8,6 | +6,5 | +37 / -2 / +16 | +2,2 | +26,9 | 64 |
| Q2 | 184 | +9,2 | +10,9 | +9,2 | +7,6 | -5 / +2 / +22 | +21,7 | -3,3 | 39 |
| Q3 | 184 | +6,0 | +2,2 | -2,2 | +9,8 | 0 / +11 / +5 | +3,1 | +9,2 | 24 |
| Q4 | 184 | +17,4 | +20,7 | +18,5 | +14,1 | +24 / +5 / +24 | +27,0 | +8,4 | 76 |
| Q5 (mais inclinada) | 185 | +9,7 | +10,8 | +7,6 | +8,6 | +22 / +18 / -2 | +26,3 | -7,8 | 41 |

**Hull + 2-4 -- media de 5 barras** (fechamento; pts por sinal por gestao; compra/venda no 1:3 com parcial)

| Quintil | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct (parcial) |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (mais plana) | 185 | +3,8 | +5,4 | -4,3 | +2,2 | 0 / -9 / +15 | -3,1 | +11,4 | 18 |
| Q2 | 184 | +20,7 | +28,3 | +22,3 | +13,0 | +51 / -3 / +24 | +21,1 | +20,2 | 87 |
| Q3 | 184 | +12,5 | +14,1 | +10,3 | +10,9 | -20 / +23 / +21 | +14,3 | +10,8 | 55 |
| Q4 | 184 | +8,7 | +11,4 | +1,6 | +6,0 | +30 / +5 / +3 | +20,5 | -2,1 | 36 |
| Q5 (mais inclinada) | 185 | +11,4 | +8,1 | +11,9 | +14,6 | +17 / +21 / +1 | +27,7 | -5,5 | 49 |

**Hull + 2-4 -- 1 barra / ATR** (fechamento; pts por sinal por gestao; compra/venda no 1:3 com parcial)

| Quintil | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct (parcial) |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (mais plana) | 185 | +18,4 | +29,2 | +11,9 | +7,6 | +32 / 0 / +25 | +7,7 | +28,7 | 80 |
| Q2 | 184 | +6,5 | +6,5 | +9,2 | +6,5 | -2 / +2 / +15 | +15,2 | -2,2 | 26 |
| Q3 | 184 | +5,4 | 0,0 | -3,8 | +10,9 | +3 / +15 / -1 | +8,1 | +2,4 | 22 |
| Q4 | 184 | +10,3 | +12,0 | +10,3 | +8,7 | +25 / -9 / +16 | +24,2 | -3,2 | 44 |
| Q5 (mais inclinada) | 185 | +16,2 | +19,5 | +14,1 | +13,0 | +19 / +24 / +9 | +25,0 | +7,5 | 71 |

**Candidato -- 1 barra** (fechamento; pts por sinal por gestao; compra/venda no 1:3 com parcial)

| Quintil | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct (parcial) |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (mais plana) | 142 | +15,5 | +20,4 | +12,0 | +10,6 | +36 / -12 / +23 | +8,7 | +21,9 | 45 |
| Q2 | 141 | +17,0 | +24,8 | +12,8 | +9,2 | +7 / +17 / +21 | +36,6 | -2,9 | 50 |
| Q3 | 141 | +12,1 | +10,6 | +6,4 | +13,5 | -7 / +20 / +14 | +3,9 | +21,9 | 30 |
| Q4 | 141 | +22,0 | +31,9 | +24,8 | +12,1 | +40 / +13 / +20 | +29,2 | +14,5 | 70 |
| Q5 (mais inclinada) | 142 | +16,9 | +21,8 | +16,9 | +12,0 | +30 / +16 / +11 | +32,4 | +2,7 | 50 |

**Candidato -- media de 5 barras** (fechamento; pts por sinal por gestao; compra/venda no 1:3 com parcial)

| Quintil | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct (parcial) |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (mais plana) | 142 | +8,5 | +11,3 | +0,7 | +5,6 | -4 / -9 / +24 | 0,0 | +16,0 | 19 |
| Q2 | 141 | +14,9 | +19,9 | +17,7 | +9,9 | +44 / -9 / +19 | +22,0 | +5,1 | 42 |
| Q3 | 141 | +24,8 | +34,8 | +22,7 | +14,9 | 0 / +40 / +27 | +33,3 | +16,7 | 79 |
| Q4 | 141 | +13,5 | +17,0 | +5,0 | +9,9 | +29 / +17 / +5 | +20,0 | +7,0 | 36 |
| Q5 (mais inclinada) | 142 | +21,8 | +26,8 | +26,8 | +16,9 | +36 / +20 / +15 | +33,3 | +11,0 | 70 |

**Candidato -- 1 barra / ATR** (fechamento; pts por sinal por gestao; compra/venda no 1:3 com parcial)

| Quintil | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct (parcial) |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (mais plana) | 142 | +16,9 | +23,2 | +12,0 | +10,6 | +30 / -9 / +28 | +16,2 | +17,6 | 50 |
| Q2 | 141 | +13,5 | +22,0 | +12,8 | +5,0 | +10 / +16 / +14 | +28,6 | -1,4 | 36 |
| Q3 | 141 | +14,9 | +13,5 | +8,5 | +16,3 | 0 / +22 / +15 | +9,0 | +22,2 | 42 |
| Q4 | 141 | +18,4 | +26,2 | +20,6 | +10,6 | +36 / +2 / +22 | +26,7 | +9,1 | 56 |
| Q5 (mais inclinada) | 142 | +19,7 | +24,6 | +19,0 | +14,8 | +29 / +24 / +10 | +30,3 | +10,5 | 62 |

**Cortando pela inclinacao** (candidato, fechamento, 1:3 com parcial):

| Medida | Todos | Sem os 20% mais planos | Sem os 40% | Sem os 60% |
|:--|--:|--:|--:|--:|
| 1 barra | +16,7 (707) | +17,0 (565) | +17,0 (424) | +19,4 (283) |
| media de 5 barras | +16,7 (707) | +18,8 (565) | +20,0 (424) | +17,7 (283) |
| 1 barra / ATR | +16,7 (707) | +16,6 (565) | +17,7 (424) | +19,1 (283) |

- As faixas nao seguem ordem, e compra e venda discordam (Hull muito inclinada: compra +26,3, venda -7,8).
- Unico indicio: Hull quase plana na media de 5 barras (menos de ~10 pts/barra) e a faixa mais fraca em todas as gestoes (percentil 9-21), mas oscila nos tercos e so tem 142 sinais. Hipotese para testar fora da amostra, nao regra.


## 6. A separacao da Hull: EMA 21 e bandas de Keltner

> As bandas sao EMA 21 +/- 2 ATR. Em ATR e no sentido do trade, distancia da Hull a banda a favor = 2 - distancia da Hull a EMA (conferido em todos os sinais): "perto da banda" e "longe da EMA" sao a mesma variavel. So diferem em pontos ou sem sinal.

**Hull + 2-4 -- Hull - EMA em ATR, zonas do canal** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Hull do lado errado da EMA | 343 | +18,4 | +25,1 | +10,8 | +11,7 | +23 / +12 / +21 | +27,2 | +9,4 | 90 |
| EMA ate meio canal (0-1 ATR) | 299 | +9,7 | +10,0 | +14,7 | +9,4 | -14 / +21 / +12 | +12,6 | +6,8 | 38 |
| meio canal ate banda (1-2 ATR) | 205 | +7,3 | +5,4 | +3,9 | +9,3 | +45 / -23 / +9 | +9,6 | +5,0 | 28 |
| alem da banda (> 2 ATR) | 75 | -2,7 | -4,0 | -16,0 | -1,3 | +5 / +4 / -13 | -5,4 | 0,0 | 14 |

**Hull + 2-4 -- Hull - EMA em ATR, faixas finas** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| < -1 ATR | 98 | +27,6 | +30,6 | +19,4 | +24,5 | +30 / +21 / +32 | +26,9 | +28,3 | 90 |
| -1 a -0,5 | 103 | +11,7 | +12,6 | +1,9 | +10,7 | -16 / +11 / +22 | +26,9 | -3,9 | 49 |
| -0,5 a 0 | 142 | +16,9 | +30,3 | +11,3 | +3,5 | +48 / +6 / +14 | +27,5 | +6,8 | 70 |
| 0 a 0,5 | 148 | +5,4 | +10,8 | +11,5 | 0,0 | 0 / +2 / +10 | 0,0 | +9,6 | 25 |
| 0,5 a 1 | 151 | +13,9 | +9,3 | +17,9 | +18,5 | -28 / +36 / +14 | +22,1 | +3,1 | 59 |
| 1 a 2 | 205 | +7,3 | +5,4 | +3,9 | +9,3 | +45 / -23 / +9 | +9,6 | +5,0 | 28 |
| > 2 ATR | 75 | -2,7 | -4,0 | -16,0 | -1,3 | +5 / +4 / -13 | -5,4 | 0,0 | 14 |

**Hull + 2-4 -- Hull - EMA em pontos (quintis)** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (menor) | 185 | +23,8 | +27,6 | +15,1 | +20,0 | +8 / +22 / +33 | +25,0 | +22,4 | 93 |
| Q2 | 184 | +15,8 | +26,6 | +8,7 | +4,9 | +42 / +8 / +14 | +30,6 | +3,0 | 70 |
| Q3 | 184 | 0,0 | +0,5 | +4,9 | -0,5 | -12 / -5 / +9 | 0,0 | 0,0 | 8 |
| Q4 | 184 | +16,3 | +13,0 | +19,0 | +19,6 | +38 / +17 / +5 | +21,1 | +11,2 | 71 |
| Q5 (maior) | 185 | +1,1 | -0,5 | -5,9 | +2,7 | +14 / -13 / +2 | +3,1 | -1,1 | 10 |

**Hull + 2-4 -- Hull - banda a favor em pontos (quintis)** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (menor) | 185 | +1,6 | -0,5 | -7,6 | +3,8 | +19 / -12 / 0 | +3,1 | 0,0 | 11 |
| Q2 | 184 | +20,1 | +19,6 | +22,3 | +20,7 | +35 / +18 / +15 | +24,0 | +15,5 | 86 |
| Q3 | 184 | -9,8 | -14,7 | -3,3 | -4,9 | -20 / -12 / -3 | -15,1 | -5,1 | 0 |
| Q4 | 184 | +21,7 | +33,2 | +15,2 | +10,3 | +57 / +15 / +16 | +40,0 | +7,7 | 90 |
| Q5 (maior) | 185 | +23,2 | +29,7 | +15,1 | +16,8 | 0 / +20 / +36 | +27,5 | +18,1 | 92 |

**Hull + 2-4 -- |Hull - EMA| em ATR, sem sinal (quintis)** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (menor) | 185 | +17,3 | +30,8 | +13,0 | +3,8 | +36 / +23 / +7 | +18,9 | +15,6 | 75 |
| Q2 | 184 | +8,7 | +13,0 | +11,4 | +4,3 | -3 / -15 / +29 | +21,5 | -1,0 | 36 |
| Q3 | 184 | +15,2 | +10,9 | +14,1 | +19,6 | -21 / +37 / +13 | +22,3 | +6,2 | 67 |
| Q4 | 184 | +8,7 | +6,5 | +4,3 | +10,9 | +62 / -15 / +4 | +10,8 | +6,6 | 36 |
| Q5 (maior) | 185 | +7,0 | +5,9 | -1,1 | +8,1 | +8 / 0 / +11 | +6,3 | +7,8 | 30 |

**Hull + 2-4 -- Barras seguidas com Hull colada na EMA** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| 0 (nao colada) | 778 | +9,9 | +9,5 | +6,9 | +10,3 | +12 / +5 / +13 | +13,8 | +6,0 | 19 |
| 1-2 barras | 68 | +41,2 | +67,6 | +30,9 | +14,7 | +91 / +43 / +24 | +61,8 | +20,6 | 97 |
| 3-5 barras | 40 | +10,0 | +10,0 | +12,5 | +10,0 | +67 / 0 / 0 | -21,7 | +52,9 | 45 |
| 6-10 barras | 26 | -26,9 | -23,1 | -19,2 | -30,8 | -100 / 0 / -8 | +27,3 | -66,7 | 5 |
| 11+ barras | 10 | +30,0 | +60,0 | +20,0 | 0,0 | +100 / -100 / +17 | +20,0 | +40,0 | 64 |

**Candidato -- Hull - EMA em ATR, zonas do canal** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Hull do lado errado da EMA | 277 | +23,5 | +31,8 | +15,5 | +15,2 | +25 / +14 / +29 | +35,7 | +10,9 | 86 |
| EMA ate meio canal (0-1 ATR) | 219 | +13,2 | +19,2 | +21,0 | +7,3 | -13 / +23 / +16 | +16,1 | +10,3 | 31 |
| meio canal ate banda (1-2 ATR) | 163 | +8,6 | +8,0 | +6,7 | +9,2 | +51 / -17 / +5 | +9,5 | +7,6 | 17 |
| alem da banda (> 2 ATR) | 48 | +20,8 | +25,0 | +6,2 | +16,7 | +27 / +35 / 0 | +9,5 | +29,6 | 57 |

**Candidato -- Hull - EMA em ATR, faixas finas** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| < -1 ATR | 83 | +28,9 | +34,9 | +15,7 | +22,9 | +29 / +28 / +29 | +37,2 | +20,0 | 81 |
| -1 a -0,5 | 83 | +15,7 | +15,7 | +8,4 | +15,7 | -19 / +4 / +37 | +35,0 | -2,3 | 45 |
| -0,5 a 0 | 111 | +25,2 | +41,4 | +20,7 | +9,0 | +55 / +13 / +23 | +35,1 | +14,8 | 77 |
| 0 a 0,5 | 109 | +1,8 | +10,1 | +12,8 | -6,4 | +5 / +3 / 0 | -6,2 | +8,2 | 8 |
| 0,5 a 1 | 110 | +24,5 | +28,2 | +29,1 | +20,9 | -32 / +39 / +34 | +32,8 | +13,0 | 75 |
| 1 a 2 | 163 | +8,6 | +8,0 | +6,7 | +9,2 | +51 / -17 / +5 | +9,5 | +7,6 | 17 |
| > 2 ATR | 48 | +20,8 | +25,0 | +6,2 | +16,7 | +27 / +35 / 0 | +9,5 | +29,6 | 57 |

**Candidato -- Hull - EMA em pontos (quintis)** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (menor) | 142 | +21,8 | +26,8 | +12,0 | +16,9 | +3 / +16 / +34 | +32,4 | +10,3 | 70 |
| Q2 | 141 | +29,1 | +42,6 | +22,7 | +15,6 | +50 / +21 / +27 | +41,2 | +17,8 | 89 |
| Q3 | 141 | +3,5 | +11,3 | +13,5 | -4,3 | -12 / 0 / +11 | +5,8 | +1,4 | 8 |
| Q4 | 141 | +19,9 | +22,0 | +21,3 | +17,7 | +46 / +14 / +12 | +18,4 | +21,5 | 61 |
| Q5 (maior) | 142 | +9,2 | +7,0 | +3,5 | +11,3 | +21 / +5 / +5 | +11,4 | +6,9 | 21 |

**Candidato -- Hull - banda a favor em pontos (quintis)** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (menor) | 142 | +11,3 | +9,9 | +5,6 | +12,7 | +29 / +2 / +5 | +10,1 | +12,3 | 27 |
| Q2 | 141 | +24,1 | +30,5 | +25,5 | +17,7 | +41 / +20 / +22 | +29,5 | +17,5 | 77 |
| Q3 | 141 | -3,5 | -2,8 | +5,0 | -4,3 | -19 / -5 / +3 | -10,1 | +2,8 | 2 |
| Q4 | 141 | +27,0 | +39,7 | +22,7 | +14,2 | +65 / +19 / +20 | +40,9 | +14,7 | 85 |
| Q5 (maior) | 142 | +24,6 | +32,4 | +14,1 | +16,9 | 0 / +18 / +40 | +37,3 | +10,4 | 79 |

**Candidato -- |Hull - EMA| em ATR, sem sinal (quintis)** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| Q1 (menor) | 142 | +12,0 | +25,4 | +11,3 | -1,4 | +41 / +25 / -6 | +13,3 | +10,4 | 30 |
| Q2 | 141 | +20,6 | +30,5 | +24,1 | +10,6 | 0 / -9 / +45 | +36,9 | +6,6 | 64 |
| Q3 | 141 | +23,4 | +24,8 | +23,4 | +22,0 | -10 / +29 / +35 | +32,4 | +13,4 | 75 |
| Q4 | 141 | +11,3 | +10,6 | +6,4 | +12,1 | +73 / -8 / +2 | +13,5 | +9,0 | 27 |
| Q5 (maior) | 142 | +16,2 | +18,3 | +7,7 | +14,1 | +15 / +21 / +14 | +14,5 | +17,8 | 48 |

**Candidato -- Barras seguidas com Hull colada na EMA** (fechamento)

| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |
|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|
| 0 (nao colada) | 598 | +17,7 | +21,7 | +15,1 | +13,7 | +19 / +10 / +23 | +22,4 | +13,0 | 69 |
| 1-2 barras | 53 | +41,5 | +69,8 | +34,0 | +13,2 | +100 / +59 / +14 | +55,2 | +25,0 | 92 |
| 3-5 barras | 27 | -11,1 | -25,9 | 0,0 | +3,7 | -50 / 0 / -13 | -35,3 | +30,0 | 11 |
| 6-10 barras | 20 | -40,0 | -40,0 | -25,0 | -40,0 | -100 / -33 / -27 | +25,0 | -83,3 | 1 |
| 11+ barras | 9 | +11,1 | +33,3 | 0,0 | -11,1 | +100 / -100 / -20 | -25,0 | +40,0 | 41 |

- **Hull alem da banda a favor** (8% dos sinais): negativa nas 4 gestoes no conjunto base (-2,7, -4,0, -16,0, -1,3); no candidato, +20,8. Confirma exaustao no conjunto base, mas o efeito some dentro do candidato.
- **Hull ainda do lado oposto da EMA** (37% dos sinais): a melhor zona (+18,4). A faixa mais extrema (< -1 ATR) mede +28,9, +34,9, +15,7, +22,9 no candidato, mas o gradiente fino vai e volta e na limitada inverte (-13,3). Hipotese, nao regra.
- **Em pontos:** sem ordem (zigue-zague).
- **Consolidacao:** nao confirmada; Hull mais proxima da EMA mede +17,3, mais afastada +7,0; tempo colada tem poucos casos.


## 7. Carteira, uma posicao por vez

| Entrada | Gestao | Regra | Trades | Pts | Fator | Acerto | Rebaix. | MC lucro | MC rebaix. p95 |
|:--|:--|:--|--:|--:|--:|--:|--:|--:|--:|
| Fechamento | 1:3 com parcial | Candidato | 669 | +11.800 | 1,40 | 30,8% | 1.400 | 100% | 2.500 |
| Fechamento | 1:3 com parcial | Hull 2-4 | 868 | +10.400 | 1,27 | 28,6% | 1.900 | 100% | 3.400 |
| Fechamento | 1:3 com parcial | Sem Hull | 1.451 | +10.900 | 1,16 | 27,2% | 4.050 | 99% | 4.900 |
| Fechamento | 1:3 sem parcial | Candidato | 669 | +15.300 | 1,33 | 30,8% | 2.200 | 100% | 3.800 |
| Fechamento | 1:3 sem parcial | Hull 2-4 | 868 | +12.200 | 1,20 | 28,6% | 2.900 | 99% | 5.600 |
| Fechamento | 1:3 sem parcial | Sem Hull | 1.451 | +11.200 | 1,11 | 26,9% | 6.300 | 95% | 8.400 |
| Fechamento | 1:2 sem parcial | Candidato | 703 | +10.100 | 1,23 | 38,1% | 2.300 | 100% | 3.700 |
| Fechamento | 1:2 sem parcial | Hull 2-4 | 915 | +7.500 | 1,13 | 36,1% | 2.700 | 96% | 5.300 |
| Fechamento | 1:2 sem parcial | Sem Hull | 1.729 | +9.600 | 1,09 | 35,2% | 4.700 | 95% | 7.600 |
| Fechamento | 1:1 sem parcial | Candidato | 707 | +8.100 | 1,26 | 55,6% | 1.200 | 100% | 2.400 |
| Fechamento | 1:1 sem parcial | Hull 2-4 | 922 | +8.600 | 1,21 | 54,6% | 1.800 | 100% | 2.800 |
| Fechamento | 1:1 sem parcial | Sem Hull | 2.150 | +12.600 | 1,12 | 52,8% | 2.100 | 99% | 4.600 |
| Limitada no meio do corpo | 1:3 com parcial | Candidato | 439 | +4.950 | 1,22 | 31,2% | 1.900 | 96% | 3.250 |
| Limitada no meio do corpo | 1:3 com parcial | Hull 2-4 | 563 | +1.925 | 1,06 | 28,6% | 2.900 | 73% | 5.500 |
| Limitada no meio do corpo | 1:3 com parcial | Sem Hull | 1.145 | -2.550 | 0,96 | 27,2% | 6.275 | 28% | 11.476 |
| Limitada no meio do corpo | 1:3 sem parcial | Candidato | 439 | +10.500 | 1,35 | 31,2% | 1.700 | 100% | 3.450 |
| Limitada no meio do corpo | 1:3 sem parcial | Hull 2-4 | 563 | +7.400 | 1,18 | 28,4% | 2.850 | 96% | 5.200 |
| Limitada no meio do corpo | 1:3 sem parcial | Sem Hull | 1.145 | +8.400 | 1,10 | 27,0% | 4.900 | 91% | 8.100 |
| Limitada no meio do corpo | 1:2 sem parcial | Candidato | 458 | +8.050 | 1,29 | 39,3% | 2.300 | 100% | 3.050 |
| Limitada no meio do corpo | 1:2 sem parcial | Hull 2-4 | 592 | +7.350 | 1,20 | 37,5% | 2.000 | 98% | 3.850 |
| Limitada no meio do corpo | 1:2 sem parcial | Sem Hull | 1.301 | +9.450 | 1,11 | 35,7% | 3.150 | 96% | 6.300 |
| Limitada no meio do corpo | 1:1 sem parcial | Candidato | 462 | -300 | 0,99 | 49,6% | 2.400 | 43% | 4.900 |
| Limitada no meio do corpo | 1:1 sem parcial | Hull 2-4 | 598 | -3.050 | 0,90 | 47,3% | 4.550 | 10% | 7.902 |
| Limitada no meio do corpo | 1:1 sem parcial | Sem Hull | 1.424 | -15.650 | 0,80 | 44,4% | 17.400 | 0% | 22.550 |

## Conclusao

- **A Hull 50 a favor e o filtro que faltava:** praticamente dobra o valor por sinal, em todas as entradas e gestoes e nos dois lados (no fechamento, tambem nos tres tercos); com a Hull contra o resultado quase zera.
- **Pavio do lado da abertura:** sem regra confiavel; a faixa do magenta so funciona na compra e se inverte na limitada.
- **Pavio do lado do fechamento ate 10%:** serve, nos dois lados.
- **Candidato** (Hull + 2-3 + fechamento ate 10%, entrada no fechamento): +16,7 pts por sinal no 1:3 com parcial, +11,5 no 1:1; cortes em plato.
- **Vale o sentido da Hull, nao o grau:** o tamanho da inclinacao nao ordena os resultados.
- **EMA 21 e Keltner nao acrescentam regra ao candidato:** exaustao (alem da banda) some dentro do candidato; consolidacao nao confirmada; hipotese aberta: Hull ainda do lado oposto da EMA.
- **Entrada no fechamento**, nao na limitada (que perde o primeiro terco).

> 26 pregoes, um instrumento, periodo de alta, resultado bruto. Os dois cortes a mais foram escolhidos nesta amostra; a Hull a favor, hipotese definida antes de medir, e a parte mais confiavel.

Reproduzir: `python hull_contra.py && python relatorio_hull.py`.
