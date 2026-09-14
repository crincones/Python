# Resultados -- momentum no grafico de 20 PI (WINFUT)

Base: `WINFUT/WINFUT_20PI.csv`, 10.000 candles de 20 PI, 26 pregoes, de 2026-08-06 a 2026-09-11.  
Resultados em **pontos do WINFUT**, brutos, com um contrato (R$ 0,20 por ponto).

> **O resumo em tres linhas.** A regra do CLAUDE.md, medida exatamente como esta escrita, ja mede positivo: +12,7 pontos por trade em 569 operacoes. Tres filtros levam isso a +34,1 pontos por trade em 170 operacoes -- o **padrao Ouro**. Um dos filtros que o CLAUDE.md pedia (a Hull concava) mede **ao contrario** e nao entrou.

## 1. A base, e o que ela e de fato

O grafico de **20 PI** da Nelogica nao e grafico de tempo. Cada candle fecha exatamente **100 pontos** (20 ticks x 5) acima ou abaixo da sua abertura, e abre no fechamento do anterior.

| Conferencia | Resultado |
| :--- | ---: |
| Candles / pregoes | 10.000 / 26 (385 por pregao) |
| Corpo de exatamente 100 pontos | 99,99% |
| Abre no fechamento anterior | 99,52% |
| ATR 21 mediano | 148 pts |
| Range mediano do candle | 145 pts |
| EMA 21 conferida contra a da Nelogica | 9.980 candles, erro max 0,944 pt, 57 divergencias reais |

**Consequencia que muda o estudo:** o corpo nao carrega informacao nenhuma. A unica forma que um candle de PI tem e o **pavio**. Por isso o estudo da "geometria do candle que retoma a tendencia" olha o pavio total, e nao a relacao corpo/pavio, que aqui seria so o inverso do range.

## 2. O padrao e os tres niveis

**Regra-base** (compra; venda e o espelho), avaliada no fechamento do candle de continuacao:

- o candle fecha a favor e o anterior fechou contra (a retracao);
- a Hull 50 esta no sentido do trade e **atras** do extremo do candle;
- os **dois** extremos do par ficam do lado de fora da Hull;
- a EMA 21 passa entre os topos e os fundos do par.

Isso da **655 sinais** em 26 pregoes. Os tres niveis sao encaixados -- todo Ouro e Prata, todo Prata e Bronze:

| Nivel | O que acrescenta | Sinais | Por trade | Acerto |
| :--- | :--- | ---: | ---: | ---: |
| **Bronze** | Regra-base: retracao + candle de continuacao, os dois extremos fora da Hull, Hull no sentido do trade e EMA 21 atravessando o par. Sem nenhum filtro extra. | 655 | +11,5 pts | 29,0% |
| **Prata** | Bronze mais duas exigencias: a retracao tem 2 ou mais candles, e o sinal NAO esta em exaustao (Hull abrindo a curva a favor com o preco a mais de 0,45 ATR da EMA 21). | 248 | +27,4 pts | 33,9% |
| **Ouro** | Prata com o candle de continuacao na forma certa: pavio total entre 25 e 90 pontos. Nem o candle liso demais, nem o candle de briga. | 173 | +34,1 pts | 36,4% |

### O veto de exaustao

O CLAUDE.md desconfiava: *"quando a HULL se encontra perto da banda superior, indica exaustao"*. A banda, sozinha, nao separa nada (secao 4). A intuicao estava certa no alvo errado: o que separa e a **combinacao** de uma Hull abrindo a curva a favor do trade com um preco que **ja** se afastou da EMA 21.

|  | preco perto da EMA (ate 0,45 ATR) | preco esticado da EMA |
| :--- | ---: | ---: |
| Hull fechando a curva | +8,5 pts (106 sinais) | +27,2 pts (112 sinais) |
| Hull abrindo a curva | +24,2 pts (165 sinais) | -1,5 pts (272 sinais) |

A celula de baixo a direita -- Hull abrindo a curva **e** preco esticado -- e o que o veto joga fora. Cada metade isolada quase nao diz nada; juntas marcam 272 dos 655 sinais, e esses 272 nao pagam.

## 3. Estatisticas da variante escolhida

**Ouro / entrada no fechamento / 1:3 com parcial** -- no formato do relatorio do MetaTrader 5, com o winrate acrescentado.

| Metrica | Valor |
| :--- | ---: |
| Lucro liquido total | +5.800 pts (R$ +1.160) |
| Lucro bruto | +12.300 pts |
| Prejuizo bruto | -6.500 pts |
| Fator de lucro | 1,89 |
| Payoff esperado | +34,12 pts (R$ +6,82) |
| Indice de Sharpe (por trade) | 0,260 |
| Correlacao LR | 0,975 |
| Rebaixamento maximo | 800 pts (R$ 160) |
| Fator de recuperacao | 7,25 |
| Total de negocios | 170 |
| **Taxa de acerto (winrate)** | **36,47%** |
| Vencedores / zerados / perdedores | 62 / 43 / 65 |
| Compras (acerto) | 79 (40,5%) |
| Vendas (acerto) | 91 (33,0%) |
| Maior ganho / maior perda | +200 / -100 pts |
| Ganho medio / perda media | +198,4 / -100,0 pts |
| Max. vitorias consecutivas | 6 (+1.200 pts) |
| Max. perdas consecutivas | 6 (-600 pts) |
| Saidas: alvo / stop / zero a zero / tempo | 61 / 65 / 43 / 1 |
| MEP media / MEN media | +168,3 / -82,1 pts |
| Duracao mediana | 1,9 min (4 candles) |
| Negocios por pregao | 6,8 |
| Pontos por pregao | +232,0 |

### A matriz inteira

| Entrada | Gestao | Nivel | Trades | Pontos | Por trade | Acerto | Fator | Rebaix. |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| fechamento | 1:3 com parcial | Ouro | 170 | +5.800 | +34,1 | 36,5% | 1,89 | 800 |
| fechamento | 1:3 com parcial | Prata | 243 | +6.800 | +28,0 | 34,2% | 1,70 | 600 |
| fechamento | 1:3 com parcial | Bronze | 569 | +7.200 | +12,7 | 29,3% | 1,28 | 1.700 |
| fechamento | 1:3 sem parcial | Ouro | 170 | +7.600 | +44,7 | 36,5% | 1,70 | 1.200 |
| fechamento | 1:3 sem parcial | Prata | 243 | +8.700 | +35,8 | 34,2% | 1,54 | 1.600 |
| fechamento | 1:3 sem parcial | Bronze | 569 | +9.000 | +15,8 | 29,3% | 1,22 | 2.100 |
| fechamento | 1:2 sem parcial | Ouro | 173 | +4.200 | +24,3 | 41,6% | 1,42 | 1.400 |
| fechamento | 1:2 sem parcial | Prata | 248 | +4.800 | +19,4 | 39,9% | 1,32 | 1.900 |
| fechamento | 1:2 sem parcial | Bronze | 607 | +4.400 | +7,2 | 35,9% | 1,11 | 2.200 |
| limitada no meio | 1:3 com parcial | Ouro | 99 | +1.500 | +15,2 | 34,3% | 1,30 | 800 |
| limitada no meio | 1:3 com parcial | Prata | 151 | +2.600 | +17,2 | 35,1% | 1,34 | 1.100 |
| limitada no meio | 1:3 com parcial | Bronze | 342 | -175 | -0,5 | 28,1% | 0,99 | 2.875 |
| limitada no meio | 1:3 sem parcial | Ouro | 99 | +3.100 | +31,3 | 33,3% | 1,47 | 800 |
| limitada no meio | 1:3 sem parcial | Prata | 151 | +5.500 | +36,4 | 34,4% | 1,56 | 1.000 |
| limitada no meio | 1:3 sem parcial | Bronze | 342 | +3.400 | +9,9 | 27,8% | 1,14 | 2.650 |
| limitada no meio | 1:2 sem parcial | Ouro | 99 | +1.700 | +17,2 | 39,4% | 1,29 | 1.100 |
| limitada no meio | 1:2 sem parcial | Prata | 152 | +3.300 | +21,7 | 40,8% | 1,37 | 1.500 |
| limitada no meio | 1:2 sem parcial | Bronze | 360 | +1.750 | +4,9 | 35,0% | 1,08 | 3.000 |
| stop no meio (antecipada) | 1:3 com parcial | Prata | 216 | +4.750 | +22,0 | 31,5% | 1,55 | 1.200 |
| stop no meio (antecipada) | 1:3 com parcial | Bronze | 308 | +4.575 | +14,9 | 28,2% | 1,37 | 975 |
| stop no meio (antecipada) | 1:3 sem parcial | Prata | 216 | +5.100 | +23,6 | 31,0% | 1,34 | 1.600 |
| stop no meio (antecipada) | 1:3 sem parcial | Bronze | 308 | +3.350 | +10,9 | 27,9% | 1,15 | 1.750 |
| stop no meio (antecipada) | 1:2 sem parcial | Prata | 225 | +4.500 | +20,0 | 40,0% | 1,33 | 1.100 |
| stop no meio (antecipada) | 1:2 sem parcial | Bronze | 335 | +4.300 | +12,8 | 37,6% | 1,21 | 1.200 |

O nivel Ouro nao existe na entrada antecipada: ele depende da forma do candle de continuacao, que nessa entrada ainda nao terminou de se formar na hora da decisao.

## 4. Cada filtro, medido

Tudo medido no conjunto **sem filtro nenhum** -- os 655 sinais da regra-base, entrada no fechamento, com parcial. A coluna dos tercos e o teste mais duro que 26 pregoes permitem: faixa que so paga num terco nao e filtro, e sorte.

### Concavidade da Hull -- **mede ao contrario do pedido**

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| Hull fechando a curva | 218 | +18,1 | 31,2% | +31,4 | +19,0 | +13,4 |
| Hull abrindo a curva (concava) | 437 | +8,2 | 27,9% | +9,4 | +10,3 | +6,2 |

### Distancia do preco a EMA 21 -- **entrou** (metade do veto)

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| ate 0,15 ATR | 129 | +26,4 | 33,3% | +35,5 | +22,0 | +24,6 |
| 0,15 a 0,45 | 142 | +10,6 | 28,2% | +50,0 | +8,3 | -1,4 |
| 0,45 a 0,80 | 251 | +4,4 | 26,3% | -12,2 | +26,4 | -6,3 |
| acima de 0,80 | 133 | +11,7 | 30,8% | +11,1 | -23,0 | +30,4 |

### Pavio total do candle de continuacao -- **entrou** (separa o Ouro)

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| ate 25 pts | 145 | -2,8 | 23,4% | +7,7 | +10,5 | -19,4 |
| 25 a 45 | 144 | +25,0 | 32,6% | +24,1 | +34,5 | +16,7 |
| 45 a 65 | 107 | +18,7 | 31,8% | -4,8 | 0,0 | +35,6 |
| 65 a 90 | 144 | +17,4 | 33,3% | +47,8 | +13,5 | +10,1 |
| acima de 90 | 115 | -1,3 | 23,5% | +3,1 | -13,5 | +1,8 |

### Pavio a favor do movimento

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| ate 3% do range | 274 | +7,8 | 28,8% | -4,2 | +8,1 | +12,0 |
| 3 a 6% | 240 | +22,5 | 32,5% | +33,3 | +24,4 | +15,7 |
| 6 a 10% | 85 | -1,2 | 24,7% | +12,5 | +6,2 | -13,5 |
| acima de 10% | 56 | +1,8 | 21,4% | +15,4 | 0,0 | -3,4 |

### Pavio contra o movimento -- nao sobrevive aos tercos

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| ate 15% do range | 124 | +3,2 | 25,8% | +16,7 | +20,0 | -16,4 |
| 15 a 30% | 191 | +14,1 | 28,3% | +20,5 | +17,9 | +8,2 |
| 30 a 45% | 243 | +14,8 | 31,7% | +15,9 | +7,1 | +20,2 |
| acima de 45% | 97 | +8,8 | 27,8% | +4,2 | +7,5 | +11,3 |

### Tamanho da retracao em candles -- **entrou** (nivel Prata)

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 candle | 349 | +5,3 | 26,9% | +10,3 | +19,1 | -7,8 |
| 2 candles | 226 | +20,8 | 32,3% | +23,8 | -1,4 | +33,6 |
| 3 candles | 66 | +16,7 | 31,8% | +20,0 | +26,1 | +9,1 |
| 4 ou mais | 14 | -7,1 | 14,3% | 0,0 | +20,0 | -25,0 |

### Tamanho da retracao em ATRs -- diz o mesmo, forma menos pratica

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| ate 1,0 ATR | 192 | +9,1 | 28,1% | +8,9 | +30,3 | -5,8 |
| 1,0 a 1,5 | 183 | +3,8 | 26,8% | +5,0 | +6,1 | +1,3 |
| 1,5 a 2,0 | 181 | +21,5 | 32,6% | +33,3 | +5,3 | +27,8 |
| acima de 2,0 | 99 | +12,1 | 28,3% | +26,3 | +9,1 | +8,5 |

### Inclinacao da Hull -- ganho pequeno, some no conjunto

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| ate 0,05 ATR | 200 | +5,5 | 27,5% | +14,3 | +23,1 | -10,8 |
| 0,05 a 0,10 | 158 | +13,9 | 29,1% | -4,9 | +30,0 | +13,4 |
| 0,10 a 0,16 | 178 | +15,4 | 29,8% | +29,2 | -4,8 | +29,6 |
| acima de 0,16 | 119 | +12,6 | 30,3% | +37,5 | +6,9 | +6,1 |

### Inclinacao da EMA 21 -- separa **ao contrario**, e e a mesma informacao do esticamento

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| EMA contra | 129 | +21,7 | 31,0% | +36,4 | +11,6 | +20,8 |
| 0 a 0,13 ATR | 134 | +20,9 | 32,1% | +15,4 | +53,2 | -1,6 |
| 0,13 a 0,30 | 198 | +5,3 | 27,3% | +14,3 | +6,8 | +1,0 |
| acima de 0,30 | 194 | +4,6 | 27,3% | -2,7 | -9,8 | +16,7 |

### Distancia da Hull a banda de Keltner -- **nao separa nada**

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| Hull a menos de 1,8 ATR da banda | 125 | +8,4 | 28,0% | -20,0 | +17,6 | +14,3 |
| 1,8 a 2,3 | 157 | +13,4 | 29,9% | +12,0 | +23,6 | +6,5 |
| 2,3 a 2,9 | 187 | +13,4 | 30,5% | +22,7 | +10,6 | +10,4 |
| acima de 2,9 | 186 | +10,2 | 27,4% | +32,4 | +3,4 | +5,6 |

### Hull colada na EMA -- **confirma a intuicao**, amostra pequena

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| solta da EMA | 509 | +12,9 | 29,5% | +17,6 | +12,9 | +10,7 |
| 1 a 3 candles colada | 73 | +23,3 | 34,2% | +27,3 | +33,3 | +12,5 |
| 4 a 8 | 42 | +7,1 | 23,8% | +40,0 | -33,3 | +20,0 |
| mais de 8 | 31 | -32,3 | 16,1% | -57,1 | +12,5 | -43,8 |

### Horario -- nenhuma faixa e estavel nos tres tercos

| Faixa | Sinais | Por trade | Acerto | 1o terco | 2o terco | 3o terco |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| 9h-10h (pre-abertura a vista) | 220 | +9,1 | 27,7% | +36,4 | +7,7 | -0,9 |
| 10h-11h | 200 | +18,0 | 31,5% | +16,2 | +10,0 | +24,7 |
| 11h-12h | 72 | +11,1 | 29,2% | -6,2 | +50,0 | -17,9 |
| 12h-13h | 32 | -6,2 | 28,1% | -50,0 | -36,4 | +46,2 |
| 13h-15h | 58 | +6,9 | 24,1% | +45,5 | +5,3 | -7,1 |
| depois das 15h | 73 | +13,0 | 30,1% | -13,3 | +22,9 | +17,6 |

Sobre a **inclinacao da EMA 21**, que o CLAUDE.md pede para avaliar: ela separa, mas ao contrario do que um filtro de tendencia faria esperar -- a EMA menos inclinada mede melhor. E nao ha o que ganhar ai: essa inclinacao tem correlacao de **0,78** com o esticamento do preco, e a mesma informacao dita de outro jeito. Aplicado o veto de exaustao, o efeito some (as quatro faixas passam a +23,6 / +14,3 / +19,2 / +23,7, sem ordem nenhuma). Nao entrou.

> **Por que os filtros nao se somam.** Empilhar os quatro melhores ao mesmo tempo deixa 16 sinais e valor esperado **negativo**. Cada corte tira sinais, e a partir de certo ponto o que sobra e uma amostra pequena demais para significar qualquer coisa. Os niveis usam tres filtros, nao os oito que mediram algo.

## 5. Stop, alvo, parcial e medias

### Grade stop x alvo (nivel Ouro, sem parcial)

Valor esperado por trade, em pontos. Entre parenteses, o resultado por **ponto de risco** -- que e o que compara stops diferentes de forma justa.

| stop \ alvo | 100 pts | 150 pts | 200 pts | 250 pts | 300 pts | 400 pts | 500 pts | 600 pts |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **50** | +16,8 (0.34) | +22,5 (0.45) | +20,2 (0.40) | +22,0 (0.44) | +31,8 (0.64) | +21,1 (0.42) | +30,3 (0.61) | +26,0 (0.52) |
| **75** | +17,1 (0.23) | +19,7 (0.26) | +18,2 (0.24) | +19,9 (0.27) | +32,2 (0.43) | +13,9 (0.18) | +29,0 (0.39) | +29,6 (0.39) |
| **100** | +23,7 (0.24) | +26,9 (0.27) | +24,3 (0.24) | +28,6 (0.29) | +44,5 (0.45)  <- | +27,7 (0.28) | +43,9 (0.44) | +41,0 (0.41) |
| **125** | +24,6 (0.20) | +25,9 (0.21) | +26,7 (0.21) | +28,2 (0.23) | +46,0 (0.37) | +27,6 (0.22) | +47,0 (0.38) | +44,9 (0.36) |
| **150** | +26,3 (0.18) | +27,7 (0.18) | +28,6 (0.19) | +30,6 (0.20) | +50,3 (0.34) | +26,9 (0.18) | +48,8 (0.33) | +44,5 (0.30) |
| **200** | +30,1 (0.15) | +35,3 (0.18) | +31,2 (0.16) | +28,3 (0.14) | +44,5 (0.22) | +22,5 (0.11) | +44,5 (0.22) | +42,2 (0.21) |
| **250** | +30,6 (0.12) | +30,9 (0.12) | +26,3 (0.11) | +26,6 (0.11) | +34,4 (0.14) | +13,0 (0.05) | +36,4 (0.15) | +34,4 (0.14) |
| **300** | +39,3 (0.13) | +39,9 (0.13) | +33,5 (0.11) | +20,8 (0.07) | +24,9 (0.08) | +4,6 (0.02) | +25,4 (0.08) | +23,7 (0.08) |

A combinacao do CLAUDE.md (100 / 300) esta marcada. Ela nao e o maior numero da grade -- stops mais largos medem mais em valor absoluto -- mas e um **topo local em alvo** (300 mede melhor que 250 e que 400) e e a melhor da coluna quando o resultado e dividido pelo risco. Vale registrar que a grade inteira mede positivo, inclusive nos stops de 250 e 300 pontos: o resultado nao depende de ter acertado o stop e o alvo.

### Relacao risco : retorno -- o 1:2 sem parcial

Alvo em pontos nao quer dizer nada sem o stop ao lado: 300 pontos com stop de 100 e 300 com stop de 300 sao apostas completamente diferentes. A tabela mede o alvo **relativo** ao stop, e a linha que compara stops diferentes e o resultado **por ponto de risco**.

| Com stop de 100 pts | 1:1 (alvo 100) | 1:2 (alvo 200) | 1:3 (alvo 300) | 1:4 (alvo 400) |
| :--- | ---: | ---: | ---: | ---: |
| Por operacao | +23,7 pts | +24,3 pts | +44,5 pts | +27,7 pts |
| Acerto | 61,8% | 41,6% | 36,4% | 26,0% |
| **Por ponto de risco** | **0,24** | **0,24** | **0,45** | **0,28** |

O **1:2 mede positivo** -- nao e uma opcao ruim. Mas ao mesmo stop ele entrega +24,3 pontos por operacao contra +44,5 do 1:3, quase a metade, e o que compra com isso e 5,2 pontos percentuais de acerto. Na carteira inteira: +4.200 pts contra +7.600 do 1:3 puro, com rebaixamento **maior** (1.400 contra 1.200 pontos) e fator de lucro menor (1,42 contra 1,70).

A diagonal inteira, em oito tamanhos de stop. Cada celula e o resultado **por ponto de risco** e, entre parenteses, o valor esperado por operacao:

| stop | 1:1 | 1:2 | 1:3 | 1:4 |
| :--- | ---: | ---: | ---: | ---: |
| **50** | 0,13 (+7) | 0,34 (+17) | 0,45 (+23) | 0,40 (+20) |
| **75** | 0,18 (+13) | 0,26 (+20) | 0,26 (+20) | 0,43 (+32) |
| **100** | 0,24 (+24) | 0,24 (+24) | 0,45 (+45)  <- | 0,28 (+28) |
| **125** | 0,20 (+25) | 0,23 (+28) | 0,26 (+32) | 0,38 (+47) |
| **150** | 0,18 (+28) | 0,34 (+50) | 0,25 (+38) | 0,30 (+45) |
| **200** | 0,16 (+31) | 0,11 (+23) | 0,21 (+42) | 0,35 (+70) |
| **250** | 0,11 (+27) | 0,15 (+36) | 0,20 (+51) | 0,20 (+49) |
| **300** | 0,08 (+25) | 0,08 (+24) | 0,10 (+31) | 0,13 (+38) |

Tres leituras:

1. **Nenhuma celula e negativa.** O setup nao depende de acertar a relacao risco:retorno -- ele paga nas trinta e duas.
2. **O 1:3 com stop curto e o melhor por unidade de risco** de toda a tabela. Stops largos rendem mais em pontos absolutos e menos por ponto arriscado, e ainda exigem mais capital para o mesmo numero de contratos.
3. **O 1:1 tem o melhor acerto e o pior resultado por risco** em quase toda a tabela. Taxa de acerto alta nao e o objetivo: e o que se compra vendendo expectativa.

### A parcial

Com a parcial em +100 e o stop do restante na **media da operacao**, o stop na verdade **nao anda**: com meia posicao e a parcial na mesma distancia do stop, o preco em que o lucro ja realizado cancela a perda do restante *e* o stop inicial. O que muda nao e o preco, e o fato de que so metade da posicao ainda corre risco. Por isso o desfecho "zero a zero" aqui e zero de verdade, e nao um ganho disfarcado de empate.

|  | Com parcial | Sem parcial |
| :--- | ---: | ---: |
| Total | +5.800 pts | +7.600 pts |
| Por trade | +34,1 | +44,7 |
| Fator de lucro | 1,89 | 1,70 |
| Rebaixamento maximo | 800 pts | 1.200 pts |
| Fator de recuperacao | 7,25 | 6,33 |
| Operacoes zeradas | 43 | 0 |

A parcial entrega 24% do lucro em troca de um rebaixamento 33% menor e de um fator de lucro melhor. E uma troca de conforto -- escolha de quem opera, nao resultado do backteste.

### Periodos de media

A EMA e sempre a linha do meio do Keltner, como manda o CLAUDE.md -- entao ela e o ATR andam juntos.

| EMA / ATR | Hull | Sinais base | Por trade (base) | Sinais Ouro | Por trade (Ouro) |
| :--- | ---: | ---: | ---: | ---: | ---: |
| 14 | 21 | 902 | -0,4 | 151 | +13,2 |
| 14 | 34 | 869 | +4,5 | 180 | +21,1 |
| 14 | 50 | 860 | +9,7 | 225 | +25,3 |
| 14 | 80 | 874 | +1,8 | 254 | +5,5 |
| 21 | 21 | 670 | +0,3 | 104 | +21,2 |
| 21 | 34 | 673 | +7,6 | 134 | +29,1 |
| 21 | 50 | 655 | +11,5 | 173 | +34,1  <- CLAUDE.md |
| 21 | 80 | 618 | +1,8 | 196 | +6,6 |
| 34 | 21 | 482 | -0,9 | 64 | +31,2 |
| 34 | 34 | 496 | +1,1 | 89 | +19,1 |
| 34 | 50 | 501 | +7,1 | 116 | +21,6 |
| 34 | 80 | 475 | +0,2 | 135 | +9,6 |

**A Hull 50 ganha de 21, 34 e 80 em todas as EMAs testadas.** O pico nao e uma celula sortuda, e uma crista -- o tipo de evidencia que mais tranquiliza num estudo de parametro.

## 6. Robustez

### Terco a terco

| Nivel | 1o terco | 2o terco | 3o terco | Periodo |
| :--- | ---: | ---: | ---: | ---: |
| Ouro | +48,3 (29) | +25,5 (55) | +34,8 (89) | **+34,1** |
| Prata | +38,6 (44) | +22,7 (75) | +26,4 (129) | **+27,4** |
| Bronze | +15,3 (131) | +13,1 (217) | +8,8 (307) | **+11,5** |

Os tres niveis medem positivo nos tres tercos. O Ouro e o mais parelho dos tres, apesar de ser o de menor amostra.

### Monte Carlo (4.000 reamostragens com reposicao)

| Nivel | p05 | mediana | p95 | prob. de lucro | rebaix. p95 |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Ouro | +3.000 | +5.800 | +8.600 | 100,0% | 1.200 |
| Prata | +3.600 | +6.800 | +10.100 | 100,0% | 1.500 |
| Bronze | +2.400 | +7.200 | +12.200 | 99,1% | 3.000 |

Isso responde "quanto do resultado foi a ordem de chegada dos trades". **Nao** responde se o padrao continua valendo no mes que vem.

### Custo operacional

Todos os numeros deste documento sao **brutos**.

| Custo ida e volta | Por trade | Total | Fator de lucro |
| :--- | ---: | ---: | ---: |
| 0 pts (R$ 0,00) | +34,1 | +5.800 | 1,89 |
| 2 pts (R$ 0,40) | +32,1 | +5.460 | 1,81 |
| 5 pts (R$ 1,00) | +29,1 | +4.950 | 1,70 |
| 10 pts (R$ 2,00) | +24,1 | +4.100 | 1,54 |
| 15 pts (R$ 3,00) | +19,1 | +3.250 | 1,40 |
| 20 pts (R$ 4,00) | +14,1 | +2.400 | 1,28 |

### O que este backteste NAO mediu

- **Slippage.** Entradas saem no preco exato do fechamento do candle, saidas no preco exato do stop ou do alvo. No stop, na pratica, escorrega.
- **Caminho dentro do candle.** So existe OHLC; assume-se que o pavio contra o sentido do candle se forma antes (convencao conservadora). Num candle que bate stop e alvo, isso decide qual vale.
- **Outros regimes.** Agosto e setembro de 2026 no WINFUT foram periodo de alta. O padrao e de continuacao; e de esperar que sofra em mercado lateral, e a base nao tem lateral suficiente para medir.
- **Um instrumento, um contrato.** Sem variacao de tamanho de posicao e sem outro ativo para confirmar.

## 6b. Agressao, tempo de barra e forca de tendencia

A base ganhou quatro colunas: volume agressor comprador e vendedor, duracao da barra, volume e numero de negocios. Num grafico de PI a duracao e a unica medida de *pressa* que existe -- todo corpo vale 100 pontos, entao 100/duracao compara barra com barra direto (mediana 27 s, quartil de cima 82 s).

**Nenhum dos atributos novos entrou em nenhum nivel.** O que da valor a esse "nao" e o controle da busca.

Foram 17 atributos x 5 cortes x 2 sentidos = **170 comparacoes**. Nesse tamanho de amostra alguma sempre parece boa -- inclusive passando no teste dos tercos, que e o mais duro usado nas outras secoes. Entao a busca inteira foi repetida 400 vezes sobre versoes **embaralhadas** dos mesmos atributos: o embaralhamento preserva a distribuicao e destroi a ligacao com o resultado, de modo que tudo o que a busca achar ali e, por construcao, sorte.

| Nivel | Melhor filtro do espaco | n | EV | t | t em ruido (mediana) | t em ruido (p90) | p | 3o terco com filtro | 3o terco sem filtro |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Ouro | velocidade da continuacao <= | 57 | +63,2 | +3,58 | +4,10 | +4,50 | 1,00 | -29,4 | +30,0 |
| Prata | deriva de 10 barras >= | 240 | +28,3 | +3,39 | +4,02 | +4,38 | 1,00 | -38,5 | +25,3 |
| Bronze | volume da continuacao >= | 328 | +21,5 | +3,01 | +3,26 | +3,66 | 0,85 | +8,8 | +11,5 |

O melhor filtro real do Ouro mede t = +3,58. A busca em ruido acha t = +4,10 na **mediana**. O achado real e *pior* que o achado tipico em ruido puro.

As duas ultimas colunas sao a prova mais direta: o corte foi escolhido usando **so** os dois primeiros tercos e depois aplicado ao terceiro, que ele nunca viu. Nos dois niveis que importam ele transforma um terco lucrativo em prejuizo. Um filtro inutil seria inofensivo; estes atrapalham.

### As duas hipoteses, uma a uma, no Ouro

Sem busca: cada linha e **um** teste, declarado antes de olhar, com o seu proprio p por permutacao.

| Hipotese | n | EV | ganho | 1o | 2o | 3o | p |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| H1 a favor da deriva de 20 barras | 99 | +30,3 | -3,8 | +4 | +58 | +23 | 0,70 |
| H1 a favor da deriva de 50 barras | 41 | +46,3 | +12,2 | 0 | +53 | +71 | 0,27 |
| H1 fechamento do lado do trade na EMA 21 | 132 | +30,3 | -3,8 | +26 | +54 | +5 | 0,77 |
| H1- contra uma deriva grande de 50 barras | 48 | +62,5 | +28,4 | +54 | +56 | +74 | 0,04 |
| H2 primeiro sinal depois do cruzamento | 115 | +35,7 | +1,5 | +23 | +62 | +12 | 0,43 |
| H2 primeiro sinal e cruzamento contundente | 37 | +45,9 | +11,8 | 0 | +83 | +22 | 0,29 |
| fluxo confirma a continuacao (sem absorcao) | 158 | +34,2 | +0,1 | +18 | +47 | +36 | 0,54 |
| fluxo: retracao vendida (agressao contra < -0,23) | 113 | +24,8 | -9,3 | 0 | +50 | +19 | 0,92 |
| fluxo: continuacao com volume acima da mediana | 111 | +39,6 | +5,5 | +30 | +50 | +39 | 0,24 |

- **"Operacao contra a tendencia forte falha"** nao se confirma. Exigir o trade a favor da deriva de 20 ou de 50 barras nao paga; o unico corte com p baixo aponta para o lado **contrario**, o que com 170 comparacoes ja feitas e exatamente o que o acaso produz. Vale lembrar que a regra-base **ja** exige a Hull 50 no sentido do trade: boa parte do filtro de tendencia que faltaria ja esta dentro dela.
- **"A retracao logo depois de um cruzamento contundente da EMA 21 funciona bem"** tambem nao. O primeiro sinal apos o cruzamento mede praticamente igual a base, e exigir alem disso um cruzamento forte nao muda nada.
- **A agressao tem o sinal certo, so nao tem tamanho.** O candle de continuacao tem desequilibrio agressor medio de +0,108 a favor e o de retracao -0,225 contra -- as colunas medem o que deviam medir, e o efeito simplesmente nao sobrevive a peneira.

### O que esta base conseguiria enxergar

| Nivel | n | Desvio por trade | Filtro que mantem 50% | mantem 33% | mantem 25% |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Bronze | 655 | 126 | +14 | +20 | +24 |
| Prata | 248 | 129 | +23 | +33 | +40 |
| Ouro | 173 | 131 | +28 | +40 | +48 |

Menor ganho de valor esperado, em pontos por trade, que esta amostra distingue de zero com 80% de poder a 5%. No Ouro, um filtro que corte dois tercos dos sinais precisaria valer mais de 40 pontos por trade para aparecer -- mais que o proprio salto de Bronze para Ouro.

> O resultado negativo desta secao nao e "fluxo nao importa"; e "26 pregoes nao respondem". Com alguns meses de agressao a pergunta volta a valer a pena, e o codigo que a responde ja esta pronto em `estudo_fluxo.py`.

### Esforco x resultado, na versao que o PI permite

No grafico de ticks a razao esforco/resultado precisa da divisao porque o resultado varia. **No PI o resultado esta fixo por construcao** -- todo corpo vale 100 pontos -- entao o esforco sozinho ja *e* a razao.

**Metade da pergunta ja estava respondida.** A leitura geometrica -- resultado util sobre deslocamento total, `100 / range` -- e exatamente o filtro de pavio do Ouro, escrito ao contrario: `range = 100 + pavio`, entao `100/range` e monotonico em pavio. Correlacao de posto medida entre os dois: **-1,0000** -- a mesma informacao. Esse pedaco ja paga e ja e o degrau que separa Ouro de Prata. O que restava testar era o esforco em volume, negocios e tempo.

| Variavel | corr. pavio | corr. volume | corr. duracao |  |
| :--- | ---: | ---: | ---: | ---: |
| esforco do par, em volume | -0,04 | -0,03 | -0,02 | **nova** |
| esforco do par, em negocios | -0,03 | -0,03 | -0,01 | **nova** |
| esforco do par, em agressao | -0,04 | -0,03 | -0,01 | **nova** |
| volume por ponto percorrido | +0,19 | +0,56 | +0,84 | ja medida |
| tamanho medio do negocio | -0,12 | +0,01 | +0,30 | ja medida |
| tamanho do negocio, continuacao / retracao | +0,20 | -0,01 | -0,05 | **nova** |
| volume da continuacao (x mediana) | +0,42 | +1,00 | +0,41 | ja medida |
| volume do par inteiro (x mediana) | +0,25 | +0,79 | +0,25 | ja medida |

"Esforco do par" e sempre **continuacao dividida pela retracao**: acima de 1, andar a favor saiu mais caro que andar contra. As tres razoes do par sao ortogonais a tudo que a estrategia ja usa. Valia medir.

**A pergunta que decide a historia.** Se menos esforco fosse melhor, o quintil de menor esforco seria o maior:

| Faixa de esforco do par (Ouro) | Sinais | EV |
| :--- | ---: | ---: |
| (0.125, 0.527] <- menor esforco | 35 | +28,6 |
| (0.527, 0.967] | 34 | +58,8 |
| (0.967, 1.381] | 35 | +34,3 |
| (1.381, 2.295] | 34 | +29,4 |
| (2.295, 451.5] <- maior esforco | 35 | +20,0 |

Ele mede +28,6 -- **abaixo** da base do Ouro, que e +34,1. Quem carrega o resultado e o segundo quintil, sozinho.

| Nivel | Sinais | Correlacao de posto esforco x resultado | p (unicaudal) |
| :--- | ---: | ---: | ---: |
| Bronze | 655 | -0,023 | 0,28 |
| Prata | 248 | -0,059 | 0,16 |
| Ouro | 173 | -0,073 | 0,18 |

A tese de Wyckoff exige relacao monotonica. Nao ha.

**O corte mais fiel:** a continuacao custou menos volume que a retracao (as duas produziram o mesmo resultado de 100 pontos, entao a comparacao e limpa).

| Nivel | Gestao | n | EV | base | ganho | 1o | 2o | 3o | p |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Prata | 1:3 com parcial | 104 | +37,5 | +27,4 | +10,1 | +29 | +53 | +30 | 0,17 |
| Ouro | 1:3 com parcial | 72 | +50,0 | +34,1 | +15,9 | +29 | +95 | +31 | 0,10 |
| Ouro | 1:3 sem parcial | 72 | +61,1 | +44,5 | +16,6 | +33 | +136 | +24 | 0,19 |
| Ouro | 1:2 sem parcial | 72 | +29,2 | +24,3 | +4,9 | +29 | +77 | -7 | 0,38 |

E o achado mais bonito de tres rodadas de investigacao: no Ouro com parcial da +15,9 pontos, positivo nos tres tercos. Mesmo assim **nao entra**. Um filtro que mantem 42% dos sinais so seria detectavel acima de +33 pontos e este alega +16 -- metade do limiar. Somado a ausencia de monotonicidade e ao quintil mais eficiente ser o segundo PIOR, e um balde sortudo, nao um efeito. E ele **depende da gestao**: trocar o alvo 1:3 pelo 1:2 derruba o ganho para +4,9 pontos -- e uma leitura de fluxo nao pode depender de qual alvo se usa.

## 7. Conclusao

Ha um setup. Ele nao e exatamente o que o CLAUDE.md descreve -- um dos filtros pedidos mede ao contrario -- mas o esqueleto da ideia mede positivo **antes** de qualquer ajuste, e e esse o achado mais importante aqui.

> Compra quando a Hull 50 esta subindo e atras do preco, depois de uma retracao de **dois ou mais** candles cujos topos ficaram acima da Hull, com a EMA 21 cortando o par, no fechamento do candle de continuacao -- desde que o preco **nao** esteja esticado da EMA com a Hull acelerando, e que esse candle tenha pavio total entre 25 e 90 pontos. Stop 100, parcial de 50% em +100, alvo 300. Venda e o espelho.

+34,1 pontos por operacao, 170 operacoes em 25 pregoes (6,8 por dia), acerto de 36,5%, rebaixamento maximo de 800 pontos, probabilidade de lucro no Monte Carlo de 100,0%.

O plano operacional esta em [PLANO.md](PLANO.md) e em `plano.html`. O relatorio completo, com os graficos e a navegacao trade a trade, esta em `relatorio.html`.

---

*Gerado por `python rodar.py && python relatorio.py`. Base: 10.000 candles, 26 pregoes. Backteste nao e promessa.*