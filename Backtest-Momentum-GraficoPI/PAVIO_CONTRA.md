# Pavio contra -- o indicador magenta

Backteste do `ntsl/PavioContra_Magenta.ntsl` no WINFUT, grafico de 20 PI, 10.000 candles, 26 pregoes (06/08/2026 a 11/09/2026). Resultado bruto. Graficos, curvas de patrimonio, MEP/MEN, duracao e trade a trade em `pavio_contra.html`.

**O padrao** (venda; compra e o espelho): 2 a 4 candles de alta, depois 1 de baixa com pavio superior de 25% a 90% do corpo. Sinal a favor do candle contra.

## Resposta curta: nao

O filtro de pavio 25-90% **piora** o sinal. Entrada no fechamento, 1:3 com parcial:

| Conjunto | Sinais | Pts por sinal |
|:--|--:|--:|
| Padrao (pavio 25-90%) | 1.354 | +4,5 |
| Mesmo universo (2-4 barras), sem filtro | 2.171 | +5,8 |
| O que o filtro descarta | 817 | +7,9 |
| Padrao invertido (a favor do movimento anterior) | 1.354 | -8,1 |

- **Contra o sorteio:** entre 4.000 subconjuntos sorteados do mesmo universo, com o mesmo tamanho, o padrao cai no percentil 27 a 33 nas quatro gestoes com entrada no fechamento. Um filtro util ficaria acima de 95.
- **As faixas andam ao contrario:** pavios de 1-25% rendem, em geral, mais que os de 25-90%, e nenhuma faixa se sustenta nos tres tercos do periodo.
- **Compra e venda discordam:** na compra o pavio grande ajuda, na venda atrapalha.
- **Nao paga custo:** o melhor valor esperado bruto entre todas as variantes e +9,5 pts; a 10 pts de custo a variante principal vai a -5,5.

Nenhuma variante e viavel, entao nao ha plano de trading.

## 1. Controles

| Entrada | Gestao | Padrao | 2-4 sem filtro | Fora da faixa | Invertido | Percentil |
|:--|:--|--:|--:|--:|--:|--:|
| Fechamento | 1:3 com parcial | +4,5 (1.354) | +5,8 (2.171) | +7,9 (817) | -8,1 (1.354) | 27 |
| Fechamento | 1:3 sem parcial | +4,2 (1.354) | +5,9 (2.171) | +8,7 (817) | -11,4 (1.354) | 28 |
| Fechamento | 1:2 sem parcial | +3,2 (1.354) | +4,2 (2.171) | +5,9 (817) | -7,2 (1.354) | 33 |
| Fechamento | 1:1 sem parcial | +4,8 (1.354) | +5,7 (2.171) | +7,1 (817) | -4,8 (1.354) | 30 |
| Limitada no meio do corpo | 1:3 com parcial | -2,1 (885) | -1,1 (1.441) | +0,6 (556) | n/a | 34 |
| Limitada no meio do corpo | 1:3 sem parcial | +9,5 (885) | +9,2 (1.441) | +8,5 (556) | n/a | 53 |
| Limitada no meio do corpo | 1:2 sem parcial | +8,9 (885) | +8,0 (1.441) | +6,7 (556) | n/a | 61 |
| Limitada no meio do corpo | 1:1 sem parcial | -13,8 (885) | -11,3 (1.441) | -7,4 (556) | n/a | 11 |

Pts por sinal, cada sinal resolvido isoladamente; entre parenteses, o numero de sinais. Na limitada o invertido nao existe (a ordem ficaria acima do mercado).

## 2. Faixas de pavio (2-4 barras antes, fechamento)

**1:3 com parcial**

| Pavio | Sinais | Pts/sinal | Acerto | T1 | T2 | T3 | Compra | Venda |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|
| 0% | 47 | -8,5 | 21,3% | +33,3 | -14,3 | -20,8 | +22,2 | -27,6 |
| 1-10% | 306 | +11,3 | 28,8% | +29,4 | +1,4 | +9,8 | +6,8 | +15,5 |
| 10-25% | 477 | +9,0 | 27,9% | +4,4 | +17,5 | +5,2 | +6,2 | +12,1 |
| 25-45% * | 486 | +5,1 | 26,5% | -14,0 | +7,3 | +12,2 | +16,1 | -6,3 |
| 45-65% * | 381 | +4,5 | 25,7% | +4,9 | -7,4 | +12,4 | +13,1 | -2,9 |
| 65-90% * | 349 | +3,9 | 26,1% | +20,1 | +0,9 | -0,6 | +9,2 | -1,4 |
| 90-100% | 113 | -2,2 | 24,8% | 0,0 | +10,8 | -13,8 | +10,7 | -14,9 |

**1:1 sem parcial**

| Pavio | Sinais | Pts/sinal | Acerto | T1 | T2 | T3 | Compra | Venda |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|
| 0% | 47 | -2,1 | 48,9% | +33,3 | -14,3 | -8,3 | +11,1 | -10,3 |
| 1-10% | 306 | +8,5 | 54,2% | +23,5 | -3,8 | +10,6 | +5,4 | +11,4 |
| 10-25% | 477 | +8,6 | 54,3% | +8,9 | +16,9 | +3,0 | +7,6 | +9,6 |
| 25-45% * | 486 | +3,9 | 51,4% | -16,0 | +6,1 | +11,3 | +14,5 | -7,1 |
| 45-65% * | 381 | +7,1 | 53,5% | +4,9 | -0,8 | +13,5 | +8,6 | +5,8 |
| 65-90% * | 349 | +4,3 | 52,1% | +7,5 | +6,0 | +1,8 | +8,0 | +0,6 |
| 90-100% | 113 | -1,8 | 48,7% | +17,2 | 0,0 | -14,9 | +5,4 | -8,8 |

`*` = faixa aceita pelo indicador.

## 3. Barras antes (pavio 25-90%, fechamento, 1:3 com parcial)

| Barras | Sinais | Pts/sinal | Acerto |
|:--|--:|--:|--:|
| 1 | 1.376 | +4,3 | 25,7% |
| 2 | 729 | +7,4 | 27,4% |
| 3 | 390 | +10,3 | 27,9% |
| 4 | 235 | -14,0 | 19,6% |
| 5+ | 208 | -4,6 | 23,1% |

## 4. Carteira, uma posicao por vez (padrao)

| Entrada | Gestao | Trades | Pts | R$ | Pts/trade | Acerto | Fator | Rebaix. | Sem filtro: pts |
|:--|:--|--:|--:|--:|--:|--:|--:|--:|--:|
| Fechamento | 1:3 com parcial | 1.059 | +1.800 | +360,00 | +1,7 | 25,1% | 1,04 | 2.950 | +11.100 |
| Fechamento | 1:3 sem parcial | 1.059 | 0 | 0,00 | 0,0 | 25,0% | 1,00 | 4.300 | +11.700 |
| Fechamento | 1:2 sem parcial | 1.190 | +2.700 | +540,00 | +2,3 | 34,0% | 1,03 | 3.100 | +9.400 |
| Fechamento | 1:1 sem parcial | 1.354 | +6.500 | +1.300,00 | +4,8 | 52,2% | 1,10 | 2.400 | +12.300 |
| Limitada no meio do corpo | 1:3 com parcial | 780 | -1.450 | -290,00 | -1,9 | 27,8% | 0,97 | 4.300 | -2.550 |
| Limitada no meio do corpo | 1:3 sem parcial | 780 | +7.900 | +1.580,00 | +10,1 | 27,6% | 1,14 | 2.600 | +8.600 |
| Limitada no meio do corpo | 1:2 sem parcial | 855 | +7.300 | +1.460,00 | +8,5 | 36,1% | 1,13 | 1.900 | +9.650 |
| Limitada no meio do corpo | 1:1 sem parcial | 885 | -12.250 | -2.450,00 | -13,8 | 42,9% | 0,76 | 12.600 | -16.150 |

## 5. Custo (pts por sinal, padrao)

| Entrada | Gestao | Bruto | 5 pts | 10 pts |
|:--|:--|--:|--:|--:|
| Fechamento | 1:3 com parcial | +4,5 | -0,5 | -5,5 |
| Fechamento | 1:3 sem parcial | +4,2 | -0,8 | -5,8 |
| Fechamento | 1:2 sem parcial | +3,2 | -1,8 | -6,8 |
| Fechamento | 1:1 sem parcial | +4,8 | -0,2 | -5,2 |
| Limitada no meio do corpo | 1:3 com parcial | -2,1 | -7,1 | -12,1 |
| Limitada no meio do corpo | 1:3 sem parcial | +9,5 | +4,5 | -0,5 |
| Limitada no meio do corpo | 1:2 sem parcial | +8,9 | +3,9 | -1,1 |
| Limitada no meio do corpo | 1:1 sem parcial | -13,8 | -18,8 | -23,8 |

## Conclusao

- **O pavio de 25-90% nao e filtro.** Ele seleciona candles que rendem um pouco menos que o conjunto de onde sairam, e nenhuma faixa e estavel nos tres tercos.
- **No PI, esse pavio e o normal.** O lado da abertura tem pavio em quase todo candle; a faixa 25-90% aceita 62% dos candles contra depois de 2-4 barras, e descarta sobretudo os pavios pequenos, que mediram melhor.
- **A contagem merece mais atencao que o pavio:** com 4 barras antes o sinal mede -14,0 pts. Nao confirmado fora desta base.
- **Compra x venda e o mercado:** periodo de alta. Compra +13,0, venda -3,7; sem filtro, +10,5 e +1,1.
- **Nenhuma variante paga custo.** A 1:1 faz 1.354 operacoes em 26 pregoes (~52 por dia).

> 26 pregoes, um instrumento, um regime de mercado, resultado bruto. O estudo diz que o filtro nao funcionou aqui; nao prova que nenhum filtro de pavio funcione.

Reproduzir: `python pavio_contra.py && python relatorio_pavio.py`.
