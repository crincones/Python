# Pavio contra -- o indicador magenta

Backteste do `ntsl/PavioContra_Magenta.ntsl` no WINFUT, grafico de 20 PI, 50.611 candles, 132 pregoes (06/03/2026 a 14/09/2026). Resultado bruto. Graficos, curvas de patrimonio, MEP/MEN, duracao e trade a trade em `pavio_contra.html`.

**O padrao** (venda; compra e o espelho): 2 a 4 candles de alta, depois 1 de baixa com pavio superior de 25% a 90% do corpo. Sinal a favor do candle contra.

## Resposta curta: nao

O filtro de pavio 25-90% **piora** o sinal. Entrada no fechamento, 1:3 com parcial:

| Conjunto | Sinais | Pts por sinal |
|:--|--:|--:|
| Padrao (pavio 25-90%) | 6.933 | +0,9 |
| Mesmo universo (2-4 barras), sem filtro | 11.083 | +2,5 |
| O que o filtro descarta | 4.150 | +5,3 |
| Padrao invertido (a favor do movimento anterior) | 6.933 | -3,9 |

- **Contra o sorteio:** entre 4.000 subconjuntos sorteados do mesmo universo, com o mesmo tamanho, o padrao cai no percentil 2 a 8 nas quatro gestoes com entrada no fechamento: ele escolhe os candles piores.
- **Fora do primeiro estudo** (06/03 a 05/08): padrao -0,5, sem filtro +1,4, descartado +4,7.
- **As faixas andam ao contrario:** ate 90% do corpo, quanto menor o pavio do lado da abertura, melhor.
- **Nao paga custo:** o melhor valor esperado bruto entre todas as variantes e +2,3 pts; a 10 pts de custo a variante principal vai a -9,1.

Nenhuma variante e viavel, entao nao ha plano de trading.

## 1. Controles

| Entrada | Gestao | Padrao | 2-4 sem filtro | Fora da faixa | Invertido | Percentil |
|:--|:--|--:|--:|--:|--:|--:|
| Fechamento | 1:3 com parcial | +0,9 (6.933) | +2,5 (11.083) | +5,3 (4.150) | -3,9 (6.933) | 3 |
| Fechamento | 1:3 sem parcial | -0,1 (6.933) | +1,7 (11.083) | +4,7 (4.150) | -6,0 (6.933) | 8 |
| Fechamento | 1:2 sem parcial | +0,3 (6.933) | +2,3 (11.083) | +5,6 (4.150) | -3,2 (6.933) | 3 |
| Fechamento | 1:1 sem parcial | +1,8 (6.933) | +3,3 (11.083) | +5,9 (4.150) | -1,8 (6.933) | 2 |
| Limitada no meio do corpo | 1:3 com parcial | -5,6 (4.686) | -5,2 (7.466) | -4,5 (2.780) | n/a | 34 |
| Limitada no meio do corpo | 1:3 sem parcial | +2,1 (4.686) | +2,1 (7.466) | +2,1 (2.780) | n/a | 50 |
| Limitada no meio do corpo | 1:2 sem parcial | +2,3 (4.686) | +2,6 (7.466) | +3,2 (2.780) | n/a | 39 |
| Limitada no meio do corpo | 1:1 sem parcial | -13,4 (4.686) | -12,5 (7.466) | -11,0 (2.780) | n/a | 16 |

Pts por sinal, cada sinal resolvido isoladamente; entre parenteses, o numero de sinais. Na limitada o invertido nao existe (a ordem ficaria acima do mercado).

## 2. Faixas de pavio (2-4 barras antes, fechamento)

**1:3 com parcial**

| Pavio | Sinais | Pts/sinal | Acerto | T1 | T2 | T3 | Compra | Venda |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|
| 0% | 290 | +8,6 | 28,6% | +22,0 | -21,5 | +16,5 | +6,6 | +10,6 |
| 1-10% | 1.628 | +6,5 | 27,0% | +5,6 | +1,8 | +12,3 | +4,4 | +8,6 |
| 10-25% | 2.308 | +3,7 | 25,7% | +2,3 | +3,7 | +5,8 | +5,8 | +1,8 |
| 25-45% * | 2.452 | +2,4 | 25,7% | +0,4 | -0,1 | +7,4 | +4,5 | +0,2 |
| 45-65% * | 1.895 | +0,8 | 25,1% | -2,3 | -0,7 | +6,1 | +5,2 | -3,9 |
| 65-90% * | 1.870 | -2,3 | 24,0% | -1,6 | -9,8 | +4,3 | -4,0 | -0,6 |
| 90-100% | 576 | +5,8 | 26,6% | +5,5 | +3,9 | +8,0 | -4,0 | +16,7 |

**1:1 sem parcial**

| Pavio | Sinais | Pts/sinal | Acerto | T1 | T2 | T3 | Compra | Venda |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|
| 0% | 290 | +4,8 | 52,4% | +18,2 | -24,1 | +11,4 | +1,4 | +8,2 |
| 1-10% | 1.628 | +6,0 | 52,9% | +3,6 | +4,8 | +10,7 | +3,0 | +8,8 |
| 10-25% | 2.308 | +6,1 | 52,9% | +7,8 | +3,5 | +6,2 | +8,5 | +3,8 |
| 25-45% * | 2.452 | +2,0 | 50,8% | +0,1 | +1,3 | +5,1 | +4,2 | -0,3 |
| 45-65% * | 1.895 | +2,0 | 50,9% | -2,2 | -0,4 | +9,6 | +5,1 | -1,3 |
| 65-90% * | 1.870 | +0,1 | 49,9% | -2,0 | -2,5 | +5,6 | -2,0 | +2,2 |
| 90-100% | 576 | +6,1 | 53,0% | +5,9 | +9,1 | +3,6 | +1,3 | +11,4 |

`*` = faixa aceita pelo indicador.

## 3. Barras antes (pavio 25-90%, fechamento, 1:3 com parcial)

| Barras | Sinais | Pts/sinal | Acerto |
|:--|--:|--:|--:|
| 1 | 7.319 | +1,4 | 25,0% |
| 2 | 3.915 | +3,0 | 25,8% |
| 3 | 1.999 | -1,6 | 24,1% |
| 4 | 1.019 | -2,4 | 24,4% |
| 5+ | 1.013 | +5,0 | 26,0% |

## 4. Carteira, uma posicao por vez (padrao)

| Entrada | Gestao | Trades | Pts | R$ | Pts/trade | Acerto | Fator | Rebaix. | Sem filtro: pts |
|:--|:--|--:|--:|--:|--:|--:|--:|--:|--:|
| Fechamento | 1:3 com parcial | 5.357 | +6.000 | +1.200,00 | +1,1 | 25,1% | 1,02 | 12.350 | +19.950 |
| Fechamento | 1:3 sem parcial | 5.357 | -300 | -60,00 | -0,1 | 25,0% | 1,00 | 18.500 | +12.900 |
| Fechamento | 1:2 sem parcial | 6.032 | +5.900 | +1.180,00 | +1,0 | 33,6% | 1,01 | 13.700 | +24.400 |
| Fechamento | 1:1 sem parcial | 6.933 | +12.800 | +2.560,00 | +1,8 | 50,8% | 1,04 | 8.400 | +37.100 |
| Limitada no meio do corpo | 1:3 com parcial | 4.113 | -25.475 | -5.095,00 | -6,2 | 25,6% | 0,89 | 29.725 | -40.025 |
| Limitada no meio do corpo | 1:3 sem parcial | 4.113 | +6.250 | +1.250,00 | +1,5 | 25,5% | 1,02 | 7.000 | +1.100 |
| Limitada no meio do corpo | 1:2 sem parcial | 4.476 | +8.700 | +1.740,00 | +1,9 | 34,0% | 1,03 | 6.100 | +15.550 |
| Limitada no meio do corpo | 1:1 sem parcial | 4.686 | -62.750 | -12.550,00 | -13,4 | 43,2% | 0,76 | 64.200 | -93.250 |

## 5. Custo (pts por sinal, padrao)

| Entrada | Gestao | Bruto | 5 pts | 10 pts |
|:--|:--|--:|--:|--:|
| Fechamento | 1:3 com parcial | +0,9 | -4,1 | -9,1 |
| Fechamento | 1:3 sem parcial | -0,1 | -5,1 | -10,1 |
| Fechamento | 1:2 sem parcial | +0,3 | -4,7 | -9,7 |
| Fechamento | 1:1 sem parcial | +1,8 | -3,2 | -8,2 |
| Limitada no meio do corpo | 1:3 com parcial | -5,6 | -10,6 | -15,6 |
| Limitada no meio do corpo | 1:3 sem parcial | +2,1 | -2,9 | -7,9 |
| Limitada no meio do corpo | 1:2 sem parcial | +2,3 | -2,7 | -7,7 |
| Limitada no meio do corpo | 1:1 sem parcial | -13,4 | -18,4 | -23,4 |

## Conclusao

- **O pavio de 25-90% nao e filtro -- e anti-filtro.** Seleciona candles que rendem menos que o conjunto de onde sairam, percentil 2 a 8 do sorteio.
- **No PI, esse pavio e o normal.** A faixa aceita 63% dos candles contra depois de 2-4 barras e descarta sobretudo os pavios pequenos, que medem melhor.
- **A contagem tambem nao se sustentou:** 4 barras antes mede -2,4 na base nova.
- **O universo inteiro esta perto de zero:** +2,5 pts por sinal sem filtro nenhum.
- **Nenhuma variante paga custo.** A 1:1 faz 6.933 operacoes em 132 pregoes (~53 por dia).

> 132 pregoes, um instrumento, resultado bruto. O estudo diz que este filtro nao funciona; nao prova que nenhum filtro de pavio funcione.

Reproduzir: `python pavio_contra.py && python relatorio_pavio.py`.
