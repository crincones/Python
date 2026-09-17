# Resultados -- momentum no grafico de 20 PI (WINFUT)

Base: `WINFUT/WINFUT_20PI_Robo.csv`, 50.611 candles de 20 PI, 132 pregoes, de 2026-03-06 a 2026-09-14. Contem inteira a base do primeiro estudo (`WINFUT_20PI.csv`, 26 pregoes, 06/08 a 11/09/2026).  
Resultados em **pontos do WINFUT**, brutos, com um contrato (R$ 0,20 por ponto). Graficos e trade a trade em `relatorio.html`.

> **O resumo.** No primeiro estudo o padrao Ouro media +34 pontos por trade. Os filtros dele foram escolhidos em 06/08 a 11/09; nos 678 sinais de 06/03 a 05/08, que nunca tinham sido vistos, ele mede **-7,4** (t = -1,67). Na base inteira, +2,0 por trade -- nao paga custo. A regra-base do CLAUDE.md, sem filtros, mede +2,3. **Nao ha setup para operar.** Ha uma hipotese (retracao de 3+ candles) para medir em pregoes futuros.

## 1. Fora da amostra: o teste que faltava

A base nova se divide em tres blocos: **antes** (06/03 a 05/08, nunca visto quando as regras foram feitas), **original** (06/08 a 11/09, onde as regras nasceram) e **depois** (12/09 em diante, um pregao). Pontos por sinal, cada sinal resolvido isoladamente, com a estatistica t entre parenteses.

| Variante | Antes | Original | Depois | Base inteira |
| :--- | ---: | ---: | ---: | ---: |
| Ouro | -7,4 (-1,7; n=678) | +34,8 (+3,6; n=181) | +10,0 (+0,2; n=10) | **+1,6** |
| Prata | -0,7 (-0,2; n=1016) | +28,3 (+3,5; n=258) | 0,0 (0,0; n=12) | **+5,1** |
| Bronze (regra-base) | -0,2 (-0,1; n=2819) | +11,4 (+2,4; n=679) | -37,5 (-2,1; n=32) | **+1,7** |
| Ouro, 1:3 sem parcial | -14,3 (-2,3; n=678) | +47,0 (+3,3; n=181) | +20,0 (+0,3; n=10) | **-1,2** |
| Ouro, 1:2 | -7,5 (-1,4; n=678) | +25,4 (+2,3; n=181) | +20,0 (+0,4; n=10) | **-0,3** |
| Prata, limitada no meio | -3,8 (-0,8; n=707) | +12,7 (+1,2; n=158) | -57,1 (-1,3; n=7) | **-1,3** |
| Prata, antecipada (ver secao 7) | +16,2 (+4,0; n=923) | +19,3 (+2,4; n=236) | -44,4 (-1,3; n=9) | **+16,4** |

**Mes a mes** (fechamento, 1:3 com parcial, pontos por sinal):

| Nivel | 03/26 | 04/26 | 05/26 | 06/26 | 07/26 | 08/26 | 09/26 |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Ouro | -20,3 | 0,0 | +10,6 | -13,3 | -1,6 | +26,6 | +36,2 |
| Prata | -8,1 | +12,7 | +4,5 | -9,7 | +3,0 | +22,9 | +27,7 |
| Bronze | -4,5 | +2,2 | +0,7 | +1,3 | +0,7 | +10,7 | +9,1 |

Agosto e setembro -- os meses da base antiga -- sao os unicos em que o Ouro passa de +20. O mercado nos meses:

| Mes | Pregoes | Variacao | Amplitude |
| :--- | ---: | ---: | ---: |
| 2026-03 | 18 | +6.600 | 12.745 |
| 2026-04 | 20 | +175 | 18.165 |
| 2026-05 | 20 | -14.590 | 18.885 |
| 2026-06 | 21 | -770 | 8.815 |
| 2026-07 | 23 | +4.765 | 8.665 |
| 2026-08 | 21 | +435 | 14.365 |
| 2026-09 | 9 | +8.010 | 12.930 |

**Os filtros do Ouro medidos so fora da janela original** (regra-base inteira):

- Pavio do candle de continuacao: ate 25 pts +4,3 / 25 a 45 -1,7 / 45 a 65 -2,1 / 65 a 90 +0,4 / acima de 90 -6,3.
- Candles de retracao: 1 candle -1,8 / 2 candles -4,4 / 3 candles +9,6 / 4 ou mais +48,9.
- Veto de exaustao: vetados +1,1 (1139); os que ficam -1,8.

## 2. A base

| Conferencia | Resultado |
| :--- | ---: |
| Candles / pregoes | 50.611 / 132 (383 por pregao) |
| Corpo de exatamente 100 pontos | 100,00% |
| Abre no fechamento anterior | 99,74% |
| ATR 21 mediano | 147 pts |
| Range mediano do candle | 140 pts |

A base vem do log do robo `LogCandles_Console.ntsl`, na ordem do proprio Profit. Nos 10.000 candles em comum com a base antiga o OHLC e identico, a menos de 25 candles que a exportacao antiga listava em ordem trocada (mesmo carimbo de milissegundo). A hora vem so ate o minuto e nao ha a coluna de EMA da Nelogica: a EMA 21 usa a mesma formula conferida na base antiga (erro maximo de 0,004 ponto).

## 3. O padrao e os tres niveis

**Regra-base** (compra; venda e o espelho), no fechamento do candle de continuacao: o candle fecha a favor e o anterior fechou contra; a Hull 50 no sentido do trade e atras do extremo; os dois extremos do par fora da Hull; a EMA 21 entre os topos e os fundos do par.

3.530 sinais. Niveis encaixados, definidos no primeiro estudo e mantidos sem alteracao:

| Nivel | O que acrescenta | Sinais | Por trade | Acerto | T1 | T2 | T3 |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| **Bronze** | Regra-base: retracao + candle de continuacao, os dois extremos fora da Hull, Hull no sentido do trade e EMA 21 atravessando o par. Sem nenhum filtro extra. | 3530 | +1,7 | 25,5% | -2,3 | +1,3 | +8,3 |
| **Prata** | Bronze mais duas exigencias: a retracao tem 2 ou mais candles, e o sinal NAO esta em exaustao (Hull abrindo a curva a favor com o preco a mais de 0,45 ATR da EMA 21). | 1286 | +5,1 | 26,0% | -0,6 | -2,5 | +20,2 |
| **Ouro** | Prata com o candle de continuacao na forma certa: pavio total entre 25 e 90 pontos. Nem o candle liso demais, nem o candle de briga. | 869 | +1,6 | 24,9% | -9,7 | -6,0 | +22,2 |

**O veto de exaustao** (base inteira). Na base antiga a celula "abrindo a curva x esticado" media -1,5 contra +8 a +27 das outras:

|  | preco perto da EMA (ate 0,45 ATR) | preco esticado |
| :--- | ---: | ---: |
| Hull fechando a curva | -1,1 pts (578 sinais) | +3,1 pts (594 sinais) |
| Hull abrindo a curva | +4,4 pts (940 sinais) | +0,4 pts (1418 sinais) |

## 4. Estatisticas

**Ouro / entrada no fechamento / 1:3 com parcial** -- formato do relatorio do MetaTrader 5, com winrate.

| Metrica | Valor |
| :--- | ---: |
| Lucro liquido total | +1.750 pts (R$ +350) |
| Lucro bruto / prejuizo bruto | +42.450 / -40.700 pts |
| Fator de lucro | 1,04 |
| Payoff esperado | +2,05 pts (R$ +0,41) |
| Indice de Sharpe (por trade) | 0,017 |
| Correlacao LR | 0,149 |
| Rebaixamento maximo | 5.600 pts (R$ 1.120) |
| Fator de recuperacao | 0,31 |
| Total de negocios | 854 |
| **Taxa de acerto (winrate)** | **25,06%** |
| Vencedores / zerados / perdedores | 214 / 233 / 407 |
| Compras (acerto) | 428 (26,9%) |
| Vendas (acerto) | 426 (23,2%) |
| Maior ganho / maior perda | +200 / -100 pts |
| Max. vitorias / perdas consecutivas | 6 / 8 |
| Saidas: alvo / stop / zero a zero / tempo | 210 / 407 / 231 / 6 |
| MEP media / MEN media | +140,7 / -91,3 pts |
| Duracao mediana | 2,0 min (2 candles) |
| Negocios por pregao | 6,5 |
| Monte Carlo: probabilidade de lucro | 67,7% |

### A matriz inteira (base inteira, carteira de uma posicao por vez)

| Entrada | Gestao | Nivel | Trades | Pontos | Por trade | Acerto | Fator | Rebaix. |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| fechamento | 1:3 com parcial | Ouro | 854 | +1.750 | +2,0 | 25,1% | 1,04 | 5.600 |
| fechamento | 1:3 com parcial | Prata | 1252 | +7.400 | +5,9 | 26,2% | 1,13 | 3.650 |
| fechamento | 1:3 com parcial | Bronze | 2985 | +6.950 | +2,3 | 25,6% | 1,05 | 6.850 |
| fechamento | 1:3 sem parcial | Ouro | 854 | -300 | -0,4 | 25,1% | 1,00 | 9.300 |
| fechamento | 1:3 sem parcial | Prata | 1252 | +5.500 | +4,4 | 26,2% | 1,06 | 5.500 |
| fechamento | 1:3 sem parcial | Bronze | 2985 | +5.100 | +1,7 | 25,6% | 1,02 | 9.000 |
| fechamento | 1:2 sem parcial | Ouro | 869 | -300 | -0,3 | 33,3% | 0,99 | 6.100 |
| fechamento | 1:2 sem parcial | Prata | 1286 | +7.400 | +5,8 | 35,2% | 1,09 | 4.800 |
| fechamento | 1:2 sem parcial | Bronze | 3231 | +3.000 | +0,9 | 33,6% | 1,01 | 6.100 |
| limitada no meio | 1:3 com parcial | Ouro | 573 | -1.800 | -3,1 | 27,1% | 0,94 | 4.400 |
| limitada no meio | 1:3 com parcial | Prata | 845 | -850 | -1,0 | 27,6% | 0,98 | 4.975 |
| limitada no meio | 1:3 com parcial | Bronze | 1914 | -6.150 | -3,2 | 26,9% | 0,94 | 7.775 |
| limitada no meio | 1:3 sem parcial | Ouro | 573 | +2.250 | +3,9 | 26,5% | 1,05 | 4.900 |
| limitada no meio | 1:3 sem parcial | Prata | 845 | +6.100 | +7,2 | 27,2% | 1,10 | 5.000 |
| limitada no meio | 1:3 sem parcial | Bronze | 1914 | +9.250 | +4,8 | 26,6% | 1,07 | 5.900 |
| limitada no meio | 1:2 sem parcial | Ouro | 583 | +1.100 | +1,9 | 34,3% | 1,03 | 3.150 |
| limitada no meio | 1:2 sem parcial | Prata | 863 | +5.450 | +6,3 | 35,7% | 1,10 | 3.500 |
| limitada no meio | 1:2 sem parcial | Bronze | 2014 | +4.200 | +2,1 | 34,2% | 1,03 | 5.750 |
| stop no meio (antecipada) | 1:3 com parcial | Prata | 1084 | +20.900 | +19,3 | 30,4% | 1,48 | 1.200 |
| stop no meio (antecipada) | 1:3 com parcial | Bronze | 1602 | +22.300 | +13,9 | 28,7% | 1,33 | 2.000 |
| stop no meio (antecipada) | 1:3 sem parcial | Prata | 1084 | +21.250 | +19,6 | 30,3% | 1,28 | 1.600 |
| stop no meio (antecipada) | 1:3 sem parcial | Bronze | 1602 | +18.850 | +11,8 | 28,4% | 1,16 | 3.150 |
| stop no meio (antecipada) | 1:2 sem parcial | Prata | 1144 | +21.800 | +19,1 | 39,8% | 1,32 | 1.600 |
| stop no meio (antecipada) | 1:2 sem parcial | Bronze | 1716 | +18.600 | +10,8 | 37,1% | 1,17 | 3.350 |
| fechamento | 1:3 com parcial | Retracao 3+ | 419 | +6.300 | +15,0 | 29,4% | 1,35 | 1.100 |
| fechamento | 1:3 sem parcial | Retracao 3+ | 419 | +6.900 | +16,5 | 29,4% | 1,23 | 1.800 |
| fechamento | 1:2 sem parcial | Retracao 3+ | 419 | +7.400 | +17,7 | 39,4% | 1,29 | 1.700 |

## 5. Cada filtro, medido (base inteira)

Conjunto **sem filtro nenhum** -- os 3.530 sinais da regra-base, fechamento, com parcial. Cada terco tem ~44 pregoes. Atencao: na regra-base o 3o terco mede +8,3 contra -2,3 e +1,3 -- faixa que so e boa no 3o terco e o periodo, nao o filtro.

### Concavidade da Hull -- as duas metades medem quase igual

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| Hull fechando a curva | 1172 | +1,0 | 24,4% | -3,1 | -3,0 | +11,0 |
| Hull abrindo a curva (concava) | 2358 | +2,0 | 26,0% | -1,9 | +3,4 | +7,0 |

### Distancia do preco a EMA 21 -- sem ordem

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| ate 0,15 ATR | 664 | +4,2 | 24,8% | -3,0 | -1,4 | +19,1 |
| 0,15 a 0,45 | 854 | +0,8 | 26,1% | -1,6 | -4,6 | +10,9 |
| 0,45 a 0,80 | 1285 | +1,3 | 25,5% | -3,3 | +9,5 | +1,3 |
| acima de 0,80 | 727 | +1,0 | 25,2% | -0,9 | -2,5 | +7,8 |

### Pavio total do candle de continuacao -- so a ponta acima de 90 continua ruim

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| ate 25 pts | 801 | +2,6 | 26,0% | +0,5 | +13,6 | -3,1 |
| 25 a 45 | 714 | +4,0 | 26,3% | -7,2 | +7,0 | +18,7 |
| 45 a 65 | 682 | +1,0 | 25,5% | +0,9 | -8,6 | +11,1 |
| 65 a 90 | 779 | +4,0 | 26,6% | -6,2 | +7,6 | +16,2 |
| acima de 90 | 554 | -5,2 | 22,0% | +1,2 | -17,0 | -2,0 |

### Pavio a favor do movimento -- acima de 10% perde nos tres tercos

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| ate 3% do range | 1576 | +2,6 | 25,8% | -2,3 | +3,6 | +10,6 |
| 3 a 6% | 1182 | +3,8 | 26,6% | -2,5 | +2,1 | +14,6 |
| 6 a 10% | 484 | -0,6 | 24,4% | +3,5 | -6,3 | -0,7 |
| acima de 10% | 288 | -8,2 | 20,5% | -12,5 | -0,6 | -10,2 |

### Pavio contra o movimento -- some no ultimo terco

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| ate 15% do range | 665 | +5,7 | 27,2% | +7,1 | +9,2 | +0,5 |
| 15 a 30% | 1076 | +0,4 | 24,3% | -6,8 | +3,3 | +9,2 |
| 30 a 45% | 1357 | +1,3 | 25,7% | -4,4 | +0,6 | +11,1 |
| acima de 45% | 432 | -0,2 | 24,8% | +0,9 | -11,7 | +9,8 |

### Tamanho da retracao em candles -- **3+ paga nos tres tercos**

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 candle | 1914 | -0,6 | 24,9% | -4,7 | +4,2 | +1,6 |
| 2 candles | 1197 | +0,6 | 25,0% | -3,1 | -11,6 | +17,4 |
| 3 candles | 357 | +10,9 | 28,6% | +2,5 | +22,4 | +12,7 |
| 4 ou mais | 62 | +38,7 | 33,9% | +70,8 | +42,9 | +4,2 |

### Tamanho da retracao em ATRs -- acima de 2 ATR paga nos tres tercos

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| ate 1,0 ATR | 1062 | +3,5 | 26,2% | +0,4 | +5,6 | +6,6 |
| 1,0 a 1,5 | 1059 | -6,8 | 22,9% | -12,1 | -1,9 | -2,8 |
| 1,5 a 2,0 | 940 | +2,7 | 25,7% | -1,0 | -9,6 | +19,6 |
| acima de 2,0 | 469 | +14,5 | 29,2% | +11,9 | +21,7 | +12,2 |

### Inclinacao da Hull -- muito inclinada mede mal, sem estabilidade

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| ate 0,05 ATR | 1039 | +0,7 | 25,5% | -2,0 | +1,3 | +4,2 |
| 0,05 a 0,10 | 977 | +2,6 | 25,8% | -1,1 | +0,7 | +11,5 |
| 0,10 a 0,16 | 871 | +6,9 | 26,9% | +3,9 | +4,7 | +13,0 |
| acima de 0,16 | 643 | -5,1 | 23,0% | -13,1 | -2,3 | +4,4 |

### Inclinacao da EMA 21 -- sem ordem; e quase o esticamento (correlacao 0,79)

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| EMA contra | 700 | +1,1 | 24,3% | -6,1 | -0,8 | +14,7 |
| 0 a 0,13 ATR | 714 | +6,7 | 27,9% | -3,6 | +6,8 | +21,6 |
| 0,13 a 0,30 | 1061 | -1,7 | 24,5% | +0,4 | -4,6 | -2,5 |
| acima de 0,30 | 1055 | +2,1 | 25,6% | -1,7 | +4,5 | +5,8 |

### Distancia da Hull a banda de Keltner -- nao separa nada

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| Hull a menos de 1,8 ATR da banda | 683 | +2,6 | 25,2% | +3,9 | -4,2 | +7,3 |
| 1,8 a 2,3 | 923 | +2,9 | 26,3% | -4,8 | +5,9 | +12,1 |
| 2,3 a 2,9 | 1012 | +0,6 | 25,3% | +2,5 | -11,1 | +8,3 |
| acima de 2,9 | 912 | +0,9 | 25,0% | -10,2 | +13,6 | +5,3 |

### Hull colada na EMA -- nao se confirma

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| solta da EMA | 2643 | +1,5 | 25,3% | -1,3 | -1,6 | +8,7 |
| 1 a 3 candles colada | 433 | +3,6 | 27,0% | -3,2 | +2,9 | +14,2 |
| 4 a 8 | 285 | +0,7 | 24,9% | -8,5 | +8,1 | +8,6 |
| mais de 8 | 169 | +1,8 | 24,3% | -4,9 | +32,6 | -15,9 |

### Horario -- 10h-12h melhor, 9h-10h e depois das 15h piores; pequeno e instavel

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| 9h-10h (pre-abertura a vista) | 911 | -3,7 | 23,2% | -4,9 | -10,0 | +2,0 |
| 10h-11h | 894 | +7,6 | 27,4% | -5,9 | +21,7 | +13,8 |
| 11h-12h | 516 | +5,4 | 26,7% | +4,3 | +1,4 | +13,2 |
| 12h-13h | 291 | +3,1 | 27,1% | +2,1 | +2,4 | +6,2 |
| 13h-15h | 363 | +2,8 | 24,8% | +4,5 | -5,8 | +7,9 |
| depois das 15h | 555 | -4,0 | 24,5% | -7,5 | -7,1 | +11,2 |

## 6. Stop, alvo, parcial e medias (nivel Ouro)

Grade sem parcial -- valor esperado por trade e, entre parenteses, por **ponto de risco**:

| stop \ alvo | 100 pts | 150 pts | 200 pts | 250 pts | 300 pts | 400 pts | 500 pts | 600 pts |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **50** | +1,6 (0.03) | +1,6 (0.03) | -1,2 (-0.02) | -3,3 (-0.07) | -2,8 (-0.06) | -7,3 (-0.15) | -3,8 (-0.08) | -4,6 (-0.09) |
| **75** | +3,3 (0.04) | +2,0 (0.03) | -0,7 (-0.01) | -2,6 (-0.03) | -1,5 (-0.02) | -6,9 (-0.09) | -1,6 (-0.02) | +2,0 (0.03) |
| **100** | +4,3 (0.04) | +1,7 (0.02) | -0,3 (-0.00) | -0,8 (-0.01) | -1,2 (-0.01)  <- | -6,0 (-0.06) | -0,7 (-0.01) | +3,6 (0.04) |
| **125** | +7,4 (0.06) | +3,9 (0.03) | +1,6 (0.01) | +0,6 (0.00) | -0,5 (-0.00) | -5,0 (-0.04) | +3,1 (0.03) | +6,2 (0.05) |
| **150** | +5,6 (0.04) | +2,2 (0.01) | -0,9 (-0.01) | -2,6 (-0.02) | -2,2 (-0.01) | -9,4 (-0.06) | -1,6 (-0.01) | +0,3 (0.00) |
| **200** | +7,8 (0.04) | +4,9 (0.02) | +0,6 (0.00) | -2,0 (-0.01) | -1,7 (-0.01) | -10,5 (-0.05) | -4,5 (-0.02) | -1,3 (-0.01) |
| **250** | +7,3 (0.03) | +5,0 (0.02) | -2,0 (-0.01) | -7,1 (-0.03) | -8,2 (-0.03) | -18,3 (-0.07) | -12,0 (-0.05) | -8,2 (-0.03) |
| **300** | +9,4 (0.03) | +7,1 (0.02) | -2,5 (-0.01) | -10,0 (-0.03) | -8,5 (-0.03) | -17,8 (-0.06) | -15,3 (-0.05) | -10,7 (-0.04) |

Na base antiga toda a grade era positiva e o 300/100 era topo local. Agora a grade fica perto de zero e o que mede melhor e o alvo curto (100 pontos).

Diagonal risco:retorno (sem parcial) -- por ponto de risco (valor esperado):

| stop | 1:1 | 1:2 | 1:3 | 1:4 |
| :--- | ---: | ---: | ---: | ---: |
| **50** | -0,00 (-0) | 0,03 (+2) | 0,03 (+2) | -0,02 (-1) |
| **75** | 0,02 (+2) | 0,03 (+2) | -0,04 (-3) | -0,02 (-1) |
| **100** | 0,04 (+4) | -0,00 (-0) | -0,01 (-1)  <- | -0,06 (-6) |
| **125** | 0,04 (+5) | 0,00 (+1) | -0,04 (-5) | 0,03 (+3) |
| **150** | 0,01 (+2) | -0,01 (-2) | -0,04 (-6) | 0,00 (+0) |
| **200** | 0,00 (+1) | -0,05 (-10) | -0,01 (-1) | 0,01 (+1) |
| **250** | -0,03 (-7) | -0,05 (-12) | -0,03 (-7) | -0,05 (-13) |
| **300** | -0,03 (-9) | -0,04 (-11) | -0,07 (-21) | -0,07 (-21) |

| Ouro, carteira | 1:3 com parcial | 1:3 sem parcial | 1:2 sem parcial |
| :--- | ---: | ---: | ---: |
| Total | +1.750 | -300 | -300 |
| Por trade | +2,0 | -0,4 | -0,3 |
| Acerto | 25,1% | 25,1% | 33,3% |
| Fator de lucro | 1,04 | 1,00 | 0,99 |
| Rebaixamento | 5.600 | 9.300 | 6.100 |

**Periodos de media** (a EMA e sempre o meio do Keltner):

| EMA / ATR | Hull | Sinais base | Por trade (base) | Sinais Ouro | Por trade (Ouro) |
| :--- | ---: | ---: | ---: | ---: | ---: |
| 14 | 21 | 4776 | -2,4 | 779 | -5,0 |
| 14 | 34 | 4682 | -1,1 | 1015 | +2,9 |
| 14 | 50 | 4718 | +1,2 | 1171 | +2,3 |
| 14 | 80 | 4787 | +2,2 | 1277 | +3,7 |
| 21 | 21 | 3602 | -1,2 | 575 | -1,4 |
| 21 | 34 | 3621 | +0,6 | 743 | +4,2 |
| 21 | 50 | 3530 | +1,7 | 869 | +1,6  <- CLAUDE.md |
| 21 | 80 | 3399 | +1,1 | 954 | +0,6 |
| 34 | 21 | 2611 | -2,0 | 369 | -3,5 |
| 34 | 34 | 2675 | -0,6 | 490 | +2,6 |
| 34 | 50 | 2669 | +0,2 | 594 | +1,6 |
| 34 | 80 | 2558 | -1,3 | 688 | +2,8 |

A Hull 50 deixou de ser a melhor; a unica regularidade e a Hull 21 ser a pior em qualquer EMA.

**Custo por operacao** (Ouro, carteira):

| Custo ida e volta | Por trade | Total | Fator de lucro |
| :--- | ---: | ---: | ---: |
| 0 pts (R$ 0,00) | +2,0 | +1.750 | 1,04 |
| 2 pts (R$ 0,40) | +0,0 | +42 | 1,00 |
| 5 pts (R$ 1,00) | -3,0 | -2.520 | 0,94 |
| 10 pts (R$ 2,00) | -8,0 | -6.790 | 0,86 |
| 15 pts (R$ 3,00) | -13,0 | -11.060 | 0,78 |
| 20 pts (R$ 4,00) | -18,0 | -15.330 | 0,71 |

## 7. A entrada antecipada nao pode ser medida com OHLC

A ordem stop no meio do corpo dispara dentro do candle seguinte. Quando esse candle fecha a favor mas tem pavio contra que alcanca o stop, o OHLC nao diz se o pavio veio antes ou depois do disparo. A engine assume "antes" -- a leitura otimista para esta entrada.

| Gestao / nivel | Sinais | Ambiguos | Convencao | Caminho aleatorio | Todo ambiguo toma stop |
| :--- | ---: | ---: | ---: | ---: | ---: |
| 1:3 com parcial / Prata | 1168 | 33,1% | +16,4 | **-0,2** | -32,5 |
| 1:3 com parcial / Bronze | 2187 | 31,6% | +11,1 | **-5,0** | -36,5 |
| 1:3 sem parcial / Prata | 1168 | 33,1% | +14,8 | **-1,5** | -32,8 |
| 1:3 sem parcial / Bronze | 2187 | 31,6% | +8,7 | **-7,3** | -38,4 |
| 1:2 sem parcial / Prata | 1168 | 33,1% | +17,4 | **+0,8** | -31,5 |
| 1:2 sem parcial / Bronze | 2187 | 31,6% | +10,0 | **-6,0** | -37,1 |

"Caminho aleatorio": probabilidade de o stop ter vindo depois do disparo tirada de um passeio aleatorio de ticks condicionado a forma do candle (28% a 40%). O cenario neutro fica perto de zero. Decidir exige o caminho dentro do candle (tick a tick ou grafico de 1 PI).

## 8. Agressao, tempo de barra e forca de tendencia

A base do robo traz agressao compradora/vendedora e duracao da barra; nao traz volume total nem numero de negocios (o "volume" aqui e o agressor, correlacao 0,995 com o total na base antiga). 17 atributos x 5 cortes x 2 sentidos = 170 comparacoes, e a mesma busca repetida 400 vezes em dados embaralhados:

| Nivel | Melhor filtro | n | EV | t | t ruido (mediana) | p | 3o terco com filtro | 3o terco sem filtro |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Ouro | agressao na continuacao >= | 435 | +5,9 | +1,00 | +1,74 | 0,91 | +13,6 | +18,7 |
| Prata | agressao na continuacao >= | 258 | +17,8 | +2,30 | +2,66 | 0,85 | +39,2 | +16,9 |
| Bronze | deriva de 10 barras >= | 2.178 | +5,3 | +2,00 | +2,20 | 0,74 | +4,9 | +6,7 |

**Nenhum passa.** Hipoteses declaradas, no Ouro:

| Hipotese | n | EV | ganho | 1o | 2o | 3o | p |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| H1 a favor da deriva de 20 barras | 514 | -0,3 | -1,8 | -18 | -3 | +16 | 0,72 |
| H1 a favor da deriva de 50 barras | 247 | +11,3 | +9,8 | -6 | +11 | +27 | 0,07 |
| H1 fechamento do lado do trade na EMA 21 | 704 | +1,5 | -0,1 | -19 | +2 | +19 | 0,52 |
| H1- contra uma deriva grande de 50 barras | 216 | -1,2 | -2,7 | -35 | -2 | +24 | 0,65 |
| H2 primeiro sinal depois do cruzamento | 622 | +2,0 | +0,5 | -21 | +4 | +20 | 0,44 |
| H2 primeiro sinal e cruzamento contundente | 227 | +6,2 | +4,6 | -19 | +1 | +37 | 0,26 |
| fluxo confirma a continuacao (sem absorcao) | 769 | +3,2 | +1,6 | -14 | -1 | +20 | 0,14 |
| fluxo: retracao vendida (agressao contra < -0,23) | 515 | +2,4 | +0,9 | -21 | +6 | +18 | 0,41 |
| fluxo: continuacao com volume acima da mediana | 546 | +0,8 | -0,7 | -12 | -12 | +20 | 0,60 |

Poder (menor ganho detectavel, 80% de poder a 5%):

| Nivel | n | Mantem 50% | Mantem 33% | Mantem 25% |
| :--- | ---: | ---: | ---: | ---: |
| Bronze | 3.530 | +6 | +8 | +10 |
| Prata | 1.286 | +10 | +14 | +17 |
| Ouro | 869 | +11 | +16 | +20 |

Na base antiga o limiar do Ouro passava de 40 pontos; agora um filtro que mantenha metade do Bronze apareceria a partir de ~6. O "nao" ja nao e so falta de amostra.

**Esforco x resultado.** A leitura geometrica (`100/range`) e o filtro de pavio (correlacao de posto -1,0000). O esforco em volume nao tem relacao monotonica com o resultado (rho no Ouro -0,041); o corte 'continuacao mais barata que a retracao' da +2,1 pts no Ouro (p = 0,34), contra +15,9 na base antiga. Sem numero de negocios, as variaveis de tamanho de negocio ficaram de fora.

## 9. Uma hipotese: retracao de 3+ candles

O unico atributo da regra-base que mede bem nos tres tercos, nos dois blocos e nos dois lados. Recorte: **Bronze + retracao de 3 ou mais candles**, sem outro filtro.

| Gestao | Trades | Pontos | Por trade | Acerto | Fator | Rebaix. | Antes | Original | MC lucro | Com 5 pts de custo |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1:3 com parcial | 419 | +6.300 | +15,0 | 29,4% | 1,35 | 1.100 | +15,3 | +14,8 | 99,5% | +10,0 |
| 1:3 sem parcial | 419 | +6.900 | +16,5 | 29,4% | 1,23 | 1.800 | +16,2 | +18,5 | 97,3% | +11,5 |
| 1:2 sem parcial | 419 | +7.400 | +17,7 | 39,4% | 1,29 | 1.700 | +22,5 | -3,7 | 99,5% | +12,7 |
| 1:1 sem parcial | 419 | +5.700 | +13,6 | 56,8% | 1,31 | 1.100 | +14,4 | +11,1 | 99,8% | +8,6 |

Tercos (1:3 com parcial): T1 +11,6 (181) / T2 +25,0 (112) / T3 +11,1 (126). Meses: 03 -1,0 / 04 +36,8 / 05 +25,5 / 06 +21,7 / 07 +1,9 / 08 +16,7 / 09 +9,5.

**Por que e hipotese e nao setup.** O corte foi escolhido depois de ver a tabela de retracao nesta base.

- Busca so entre cortes de retracao: melhor t = +2,52; em ruido, mediana +1,14; p = 0,015. Passa.
- Busca entre todas as tabelas olhadas (12 atributos, 74 cortes): o melhor ainda e a retracao (t = +2,52), mas o ruido acha +2,10 na mediana e +2,87 no p95; p = 0,17. **Nao passa.**

O protocolo para medir a hipotese em pregoes futuros esta em [PLANO.md](PLANO.md).

## 10. O que este backteste nao mediu

- **Slippage.** Entradas no preco exato do fechamento, saidas no preco exato do stop/alvo.
- **Caminho dentro do candle.** So OHLC; convencao conservadora para a entrada no fechamento (e otimista para a antecipada, secao 7).
- **Duracao com resolucao de minuto.** A base do robo nao tem segundos.
- **Um instrumento, um contrato.**

## 11. Conclusao

O setup Ouro nao sobreviveu a base maior: -7,4 pts por trade nos pregoes que nao participaram da escolha dos filtros, +2,0 na base inteira. Os tercos de 26 pregoes eram tres pedacos do mesmo mes e meio de mercado, e nao robustez.

- **Nao operar o Ouro nem o Prata**, e nao ligar `Robo-NTSL/MomentumPI_OuroPrata_Robo.ntsl` em conta real.
- **A antecipada** so parece boa por uma convencao de caminho; precisa de dado intra-candle.
- **A retracao profunda** e a hipotese a medir daqui para frente, sem mexer em nada.
- **O estudo `hull_contra`** (Hull a favor + 2 a 4 candles contra) foi refeito e e o unico cuja hipotese previa passou no teste fora da amostra -- ver `HULL_CONTRA.md`.

---

*Gerado por `python rodar.py && python candidato.py && python relatorio.py`. Base: 50.611 candles, 132 pregoes. Backteste nao e promessa.*