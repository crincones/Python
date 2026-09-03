# Resultados — Rincones1 XAUUSD

> **Gerado por `python rodar.py && python relatorio.py`. Não edite à mão.** Todos os números saem de `saida/resumo.json`, os mesmos do `relatorio.html`.

68.286 barras de 521 ticks do XAUUSD, 85 pregões, 2026-05-04 a 2026-08-28. Valores em **USD por onça** — 1,00 de movimento vale 100 USD num lote padrão de 100 oz. Tudo **bruto**, exceto a § 8.

Configuração padrão: gatilho `[E4] ≥ 0,90` lido contra a direção do **candle**, geometria **inversa** com corte de posição 60, corpo ≤ 50% do range · entrada **a mercado no fechamento** · stop 7,00, parcial de 50% na distância do stop, alvo 10,50 · uma posição por vez.

## 1. O resultado

|  | n | EV | total | acerto | t | dias+ | PF | DD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **amostra inteira** · 708 gatilhos |  |  |  |  |  |  |  |  |
| carteira completa (A+B+C+L) ← | 571 | +1,202 | +686,1 | 48,3% | +3,89 | 65% | 1,42 | 73,6 |
| só A + B + C | 327 | +0,806 | +263,4 | 46,5% | +1,97 | 62% | 1,26 | 80,7 |
| só A + B | 291 | +0,837 | +243,5 | 46,7% | +1,92 | 65% | 1,27 | 98,5 |
| só A | 180 | +0,539 | +97,0 | 45,0% | +1,09 | 54% | 1,17 | 68,2 |
| **1ª metade** · 337 gatilhos |  |  |  |  |  |  |  |  |
| carteira completa (A+B+C+L) ← | 281 | +0,993 | +278,9 | 47,3% | +2,15 | 57% | 1,33 | 60,2 |
| só A + B + C | 165 | +0,188 | +31,0 | 43,0% | +0,31 | 52% | 1,06 | 80,7 |
| só A + B | 146 | -0,043 | -6,3 | 41,8% | -0,07 | 55% | 0,99 | 98,5 |
| só A | 79 | +0,136 | +10,8 | 43,0% | +0,18 | 50% | 1,04 | 68,2 |
| **2ª metade** · 371 gatilhos |  |  |  |  |  |  |  |  |
| carteira completa (A+B+C+L) ← | 290 | +1,404 | +407,1 | 49,3% | +3,38 | 72% | 1,51 | 73,6 |
| só A + B + C | 162 | +1,434 | +232,4 | 50,0% | +2,68 | 72% | 1,50 | 46,6 |
| só A + B | 145 | +1,723 | +249,9 | 51,7% | +3,23 | 76% | 1,64 | 32,6 |
| só A | 101 | +0,854 | +86,2 | 46,5% | +1,33 | 58% | 1,28 | 49,1 |

As duas metades **não são duas amostras independentes**: são o mesmo histórico de 85 pregões partido ao meio. No projeto do WIN havia dois contratos diferentes e a concordância entre eles era evidência de verdade; aqui ela é só evidência de que o resultado não vem de um pedaço do período. É mais fraco, e o número tem de ser lido assim. Metades: +0,993 e +1,404 por trade.

## 2. O que o porte teve de mudar

Quatro peças. Em cada linha, só a coluna muda; todo o resto fica congelado. EV por trade em USD, amostra inteira, stop 7,00.

| o que | no WIN | EV | no ouro | EV | diferença |
| --- | ---: | ---: | ---: | ---: | ---: |
| eixo do índice | E2+E3+E4 | +0,507 | **E4** | +1,202 | +0,695 |
| direção lida | delta | +0,483 | **candle** | +1,202 | +0,719 |
| geometria | classica | -0,075 | **inversa** | +1,202 | +1,277 |
| entrada | meio | -0,649 | **fecha** | +1,202 | +1,851 |

As quatro trocas medem melhor na coluna da direita, e em 4 das 4 a diferença troca o *sinal* do resultado. As duas mais caras são a geometria (-0,075 contra +1,202 por trade) e a entrada (-0,649 contra +1,202) — e as duas estão ligadas: é a inversão da geometria que estraga a ordem limitada, porque muda de que lado do fechamento cai o meio do candle.

## 3. A direção é do candle, não do delta

|  | n | EV | total | acerto | t | dias+ | PF | DD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **amostra inteira** |  |  |  |  |  |  |  |  |
| direção do próprio candle ← | 571 | +1,202 | +686,1 | 48,3% | +3,89 | 65% | 1,42 | 73,6 |
| direção do delta (tick rule) | 701 | +0,483 | +338,2 | 43,4% | +1,81 | 58% | 1,15 | 96,2 |
| **1ª metade** |  |  |  |  |  |  |  |  |
| direção do próprio candle ← | 281 | +0,993 | +278,9 | 47,3% | +2,15 | 57% | 1,33 | 60,2 |
| direção do delta (tick rule) | 343 | +0,444 | +152,2 | 43,1% | +1,36 | 60% | 1,14 | 61,1 |
| **2ª metade** |  |  |  |  |  |  |  |  |
| direção do próprio candle ← | 290 | +1,404 | +407,1 | 49,3% | +3,38 | 72% | 1,51 | 73,6 |
| direção do delta (tick rule) | 357 | +0,541 | +193,0 | 43,7% | +1,28 | 56% | 1,17 | 96,2 |

Na B3 a bolsa publica a flag de agressor de cada negócio. No XAUUSD ela é **inferida** pela tick rule, e o delta resultante concorda com o sinal do próprio candle em só 63,2% das barras — não é a mesma variável. Medido, a direção que serve para ler o esforço é a do candle.

## 4. De que eixo é o índice

O XAUUSD é CFD: não há volume por negócio, o gerador de barras conta 1 lote por tick, e a agressão total fica igual ao número de negócios em quase toda barra. Com o eixo constante o percentil dá 0,000 sempre, e um índice de três eixos que o inclua fica preso abaixo de 0,667 — com corte em 0,80 ele nunca acenderia. A engine detecta eixo sem variação e o tira da soma, renormalizando os pesos. Eixo derrubado neste ativo: **E1**. É a mesma defesa do `[D1]` de `Ticks_Esforco_v2.mqh`, e não é um remendo para o ouro: é o que impede qualquer eixo que o ativo não publique de virar um teto silencioso no índice.

|  | n | EV | total | acerto | t | dias+ | PF | DD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **amostra inteira** |  |  |  |  |  |  |  |  |
| E4 (nível 0,90) ← | 571 | +1,202 | +686,1 | 48,3% | +3,89 | 65% | 1,42 | 73,6 |
| E2 + E3 + E4 (nível 0,80) | 579 | +0,507 | +293,5 | 44,2% | +1,80 | 58% | 1,16 | 115,1 |
| E2 + E4 (nível 0,85) | 504 | +0,268 | +135,0 | 42,7% | +0,77 | 49% | 1,08 | 178,7 |
| E3 + E4 (nível 0,85) | 582 | +0,427 | +248,6 | 42,6% | +1,63 | 53% | 1,13 | 133,2 |
| E2 + E3 (nível 0,80) | 1114 | +0,336 | +374,0 | 43,1% | +1,28 | 53% | 1,10 | 436,6 |
| **1ª metade** |  |  |  |  |  |  |  |  |
| E4 (nível 0,90) ← | 281 | +0,993 | +278,9 | 47,3% | +2,15 | 57% | 1,33 | 60,2 |
| E2 + E3 + E4 (nível 0,80) | 290 | +0,242 | +70,2 | 43,1% | +0,58 | 60% | 1,07 | 115,1 |
| E2 + E4 (nível 0,85) | 245 | -0,320 | -78,3 | 38,8% | -0,68 | 45% | 0,91 | 178,7 |
| E3 + E4 (nível 0,85) | 299 | +0,437 | +130,7 | 43,1% | +1,24 | 52% | 1,14 | 76,8 |
| E2 + E3 (nível 0,80) | 570 | -0,103 | -58,5 | 40,0% | -0,24 | 45% | 0,97 | 436,6 |
| **2ª metade** |  |  |  |  |  |  |  |  |
| E4 (nível 0,90) ← | 290 | +1,404 | +407,1 | 49,3% | +3,38 | 72% | 1,51 | 73,6 |
| E2 + E3 + E4 (nível 0,80) | 289 | +0,772 | +223,2 | 45,3% | +2,06 | 56% | 1,25 | 87,5 |
| E2 + E4 (nível 0,85) | 259 | +0,824 | +213,3 | 46,3% | +1,64 | 53% | 1,27 | 57,7 |
| E3 + E4 (nível 0,85) | 283 | +0,417 | +118,0 | 42,0% | +1,06 | 53% | 1,13 | 112,2 |
| E2 + E3 (nível 0,80) | 544 | +0,795 | +432,5 | 46,3% | +2,73 | 60% | 1,25 | 91,0 |

**E4** mede melhor, e é o único conjunto que mede positivo em todas as três colunas com folga: +1,202 por trade contra +0,507 do índice de três eixos (t +3,89 contra +1,80). Somar eixos aqui *dilui* — cada eixo que entra puxa o índice para a média e o corte deixa de selecionar a barra de range extremo, que é a única coisa que este ativo publica com sinal. Conjuntos positivos nas três colunas: E4, E2+E3+E4, E3+E4.

## 5. O eixo [E2]: fórmula antiga contra a nova

O índice padrão daqui não usa `[E2]` (§ 4), então a comparação roda sobre o índice de três eixos `E2+E3+E4` no nível 0,80 — a configuração mais próxima do backtest do WIN que este ativo aceita.

|  | n | EV | total | acerto | t | dias+ | PF | DD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **amostra inteira** |  |  |  |  |  |  |  |  |
| v1 · \|delta\| / \|Close-Open\| | 419 | +0,017 | +7,0 | 40,8% | +0,05 | 52% | 1,00 | 211,6 |
| v2 · (\|delta\|/esforço) × volta ← | 579 | +0,507 | +293,5 | 44,2% | +1,80 | 58% | 1,16 | 115,1 |
| **1ª metade** |  |  |  |  |  |  |  |  |
| v1 · \|delta\| / \|Close-Open\| | 238 | -0,507 | -120,6 | 38,2% | -1,13 | 41% | 0,86 | 211,6 |
| v2 · (\|delta\|/esforço) × volta ← | 290 | +0,242 | +70,2 | 43,1% | +0,58 | 60% | 1,07 | 115,1 |
| **2ª metade** |  |  |  |  |  |  |  |  |
| v1 · \|delta\| / \|Close-Open\| | 181 | +0,705 | +127,5 | 44,2% | +1,51 | 63% | 1,23 | 52,5 |
| v2 · (\|delta\|/esforço) × volta ← | 289 | +0,772 | +223,2 | 45,3% | +2,06 | 56% | 1,25 | 87,5 |

O eixo novo mede melhor em 3 das 3 colunas: +0,507 contra +0,017 por trade na amostra inteira, com t +1,80 contra +0,05. E o que mais importa não é a diferença de tamanho: com a fórmula antiga a 1ª metade mede -0,507 — as duas metades **discordam de sinal**; com a nova elas **concordam**. O eixo saiu de “atrapalha” para “soma”, que é exatamente o que a medição por barra de `Ticks_Esforco_v2.mqh` tinha previsto para este ativo.

## 6. A geometria de rejeição está invertida

|  | n | EV | total | acerto | t | dias+ | PF | DD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **amostra inteira** |  |  |  |  |  |  |  |  |
| sem filtro de forma | 2550 | -0,041 | -103,3 | 39,8% | -0,31 | 48% | 0,99 | 466,4 |
| só corpo pequeno | 1347 | +0,390 | +524,7 | 43,2% | +1,73 | 56% | 1,12 | 154,9 |
| clássica (corpo do lado da rejeição) — a regra do WIN | 743 | -0,075 | -55,8 | 40,5% | -0,32 | 49% | 0,98 | 272,5 |
| inversa (corpo do lado oposto) ← | 571 | +1,202 | +686,1 | 48,3% | +3,89 | 65% | 1,42 | 73,6 |
| **1ª metade** |  |  |  |  |  |  |  |  |
| sem filtro de forma | 1383 | -0,141 | -195,1 | 39,3% | -0,84 | 43% | 0,96 | 466,4 |
| só corpo pequeno | 672 | +0,180 | +120,7 | 41,8% | +0,58 | 50% | 1,05 | 140,6 |
| clássica (corpo do lado da rejeição) — a regra do WIN | 342 | +0,453 | +154,9 | 43,6% | +1,42 | 60% | 1,14 | 64,4 |
| inversa (corpo do lado oposto) ← | 281 | +0,993 | +278,9 | 47,3% | +2,15 | 57% | 1,33 | 60,2 |
| **2ª metade** |  |  |  |  |  |  |  |  |
| sem filtro de forma | 1166 | +0,058 | +67,3 | 40,1% | +0,27 | 53% | 1,02 | 222,9 |
| só corpo pequeno | 674 | +0,586 | +395,2 | 44,5% | +1,78 | 63% | 1,18 | 154,9 |
| clássica (corpo do lado da rejeição) — a regra do WIN | 400 | -0,549 | -219,5 | 37,8% | -1,68 | 40% | 0,85 | 258,4 |
| inversa (corpo do lado oposto) ← | 290 | +1,404 | +407,1 | 49,3% | +3,38 | 72% | 1,51 | 73,6 |

A inversa mede +1,202 por trade contra -0,075 da clássica — e a distância entre as duas (+1,277) é maior que o EV inteiro da estratégia. Nas metades a inversa dá +0,99 e +1,40, as duas positivas; a clássica dá +0,45 e -0,55, que discordam de sinal. Sem nenhum filtro de forma o gatilho mede -0,041: o filtro não é enfeite, é metade do sinal. Com n = 571 e t = +3,89, é o resultado mais firme deste backtest.

> Não é achado novo. O `Delta_Fraqueza.mqh` registrou a mesma inversão no `XAUUSD_19_DT`, e o `[D4]` de `Ticks_Esforco_v2.mqh` a remediu no `XAUUSD_521_TK`. Esta é a terceira vez que o mesmo sinal aparece trocado no ouro, agora no nível do trade.

## 7. A entrada

|  | n | EV | total | acerto | t | dias+ | PF | DD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **amostra inteira** |  |  |  |  |  |  |  |  |
| a mercado no fechamento do candle ← | 571 | +1,202 | +686,1 | 48,3% | +3,89 | 65% | 1,42 | 73,6 |
| limitada no meio do candle, válida por 1 barra | 577 | -0,649 | -374,7 | 36,7% | -2,10 | 44% | 0,83 | 417,6 |
| **1ª metade** |  |  |  |  |  |  |  |  |
| a mercado no fechamento do candle ← | 281 | +0,993 | +278,9 | 47,3% | +2,15 | 57% | 1,33 | 60,2 |
| limitada no meio do candle, válida por 1 barra | 284 | -0,638 | -181,1 | 35,9% | -1,39 | 40% | 0,83 | 205,6 |
| **2ª metade** |  |  |  |  |  |  |  |  |
| a mercado no fechamento do candle ← | 290 | +1,404 | +407,1 | 49,3% | +3,38 | 72% | 1,51 | 73,6 |
| limitada no meio do candle, válida por 1 barra | 293 | -0,661 | -193,6 | 37,5% | -1,57 | 47% | 0,83 | 231,4 |

A mercado: +1,202 por trade, t +3,89. Limitada no meio do candle: -0,649, t -2,10. A regra custa **+1,851 por trade** e inverte o sinal do resultado. E ela nem sequer aborta operações que compensem a diferença — dos 708 sinais, 706 preenchem na barra seguinte (100%), porque o preço já está do lado errado da ordem. No WIN essa mesma regra custava quase nada e comprava disciplina; aqui ela só compra desconto para o outro lado.

## 8. Stop, alvo e custo

EV por trade em USD, amostra inteira. Linha = stop, coluna = alvo.

| stop \ alvo | 7,0 | 10,5 | 14,0 | 21,0 | 28,0 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 3,5 | +0,33 | +0,42 | +0,38 | +0,41 | +0,42 |
| 5,0 | +0,48 | +0,60 | +0,59 | +0,59 | +0,62 |
| 7,0 | +0,97 | **+1,20** | +1,12 | +1,06 | +0,99 |
| 9,0 | +0,74 | +1,18 | +1,19 | +1,02 | +1,18 |
| 12,0 | +0,16 | +1,08 | +1,43 | +1,05 | +1,25 |

O par escolhido é **stop 7,0, alvo 10,5** — a melhor célula da amostra inteira (+1,202 por trade). O stop equivalente do WIN, 3,5, mede +0,425 no mesmo alvo: positivo, mas menos da metade. Nas duas metades o melhor stop é 7,0 e 9,0, o que mantém a escolha. Das 25 células da grade, 25 medem positivo — a região é larga, não é um pico.

### O custo

|  | n | EV | total | acerto | t | dias+ | PF | DD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **amostra inteira** |  |  |  |  |  |  |  |  |
| custo 0,00 USD | 571 | +1,202 | +686,1 | 48,3% | +3,89 | 65% | 1,42 | 73,6 |
| custo 0,10 USD | 571 | +1,102 | +629,0 | 48,2% | +3,56 | 64% | 1,38 | 75,9 |
| custo 0,20 USD | 571 | +1,002 | +571,9 | 47,8% | +3,23 | 64% | 1,34 | 78,2 |
| custo 0,50 USD | 571 | +0,702 | +400,6 | 47,6% | +2,25 | 62% | 1,22 | 85,1 |
| **1ª metade** |  |  |  |  |  |  |  |  |
| custo 0,00 USD | 281 | +0,993 | +278,9 | 47,3% | +2,15 | 57% | 1,33 | 60,2 |
| custo 0,10 USD | 281 | +0,893 | +250,8 | 47,0% | +1,93 | 57% | 1,29 | 63,5 |
| custo 0,20 USD | 281 | +0,793 | +222,7 | 47,0% | +1,71 | 57% | 1,26 | 66,8 |
| custo 0,50 USD | 281 | +0,493 | +138,4 | 46,6% | +1,06 | 55% | 1,15 | 76,7 |
| **2ª metade** |  |  |  |  |  |  |  |  |
| custo 0,00 USD | 290 | +1,404 | +407,1 | 49,3% | +3,38 | 72% | 1,51 | 73,6 |
| custo 0,10 USD | 290 | +1,304 | +378,1 | 49,3% | +3,14 | 70% | 1,46 | 75,9 |
| custo 0,20 USD | 290 | +1,204 | +349,1 | 48,6% | +2,89 | 70% | 1,42 | 78,2 |
| custo 0,50 USD | 290 | +0,904 | +262,1 | 48,6% | +2,16 | 70% | 1,30 | 85,1 |

Com 0,20 de custo o EV cai de +1,202 para +1,002 por trade e o t de +3,89 para +3,23 — a vantagem sobrevive ao spread típico. Com 0,50 ela cai para +0,702. O custo que zeraria a estratégia é de cerca de **1,20 USD** por trade, e o spread do ouro alarga em notícia: a margem existe, mas não é grande, e quem opera com spread variável precisa medir o próprio.

### A regra da parcial

|  | n | EV | total | acerto | t | dias+ | PF | DD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **amostra inteira** |  |  |  |  |  |  |  |  |
| parcial na distância do stop · stop na média da operação ← | 571 | +1,202 | +686,1 | 48,3% | +3,89 | 65% | 1,42 | 73,6 |
| parcial em metade do stop · stop na média da operação | 594 | +0,834 | +495,7 | 40,6% | +3,63 | 61% | 1,44 | 49,0 |
| parcial em metade do stop · stop na entrada (o modelo antigo) | 615 | +0,792 | +487,2 | 72,4% | +3,99 | 68% | 1,42 | 61,6 |
| **1ª metade** |  |  |  |  |  |  |  |  |
| parcial na distância do stop · stop na média da operação ← | 281 | +0,993 | +278,9 | 47,3% | +2,15 | 57% | 1,33 | 60,2 |
| parcial em metade do stop · stop na média da operação | 290 | +0,811 | +235,2 | 40,7% | +2,18 | 57% | 1,42 | 39,4 |
| parcial em metade do stop · stop na entrada (o modelo antigo) | 298 | +0,789 | +235,0 | 71,8% | +2,43 | 67% | 1,41 | 61,6 |
| **2ª metade** |  |  |  |  |  |  |  |  |
| parcial na distância do stop · stop na média da operação ← | 290 | +1,404 | +407,1 | 49,3% | +3,38 | 72% | 1,51 | 73,6 |
| parcial em metade do stop · stop na média da operação | 304 | +0,857 | +260,5 | 40,5% | +3,05 | 65% | 1,47 | 49,0 |
| parcial em metade do stop · stop na entrada (o modelo antigo) | 317 | +0,796 | +252,2 | 72,9% | +3,31 | 70% | 1,43 | 43,8 |

Aqui a regra certa também mede **melhor**: +1,202 contra +0,792 por trade. É o contrário do que aconteceu no WIN, onde o modelo antigo inflava o resultado — e é uma coincidência feliz, não um argumento: a regra certa continuaria sendo a certa se medisse pior, porque a outra conta dinheiro que não existe.

## 9. Os setups e as médias de regime

|  | n | EV | total | acerto | t | dias+ | PF | DD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **amostra inteira** |  |  |  |  |  |  |  |  |
| setup A isolado (190 sinais) | 190 | +0,515 | +97,8 | 44,7% | +1,05 | 56% | 1,16 | 74,2 |
| setup B isolado (133 sinais) | 133 | +1,125 | +149,7 | 48,9% | +1,64 | 54% | 1,38 | 99,2 |
| setup C isolado (43 sinais) | 43 | +0,713 | +30,7 | 44,2% | +0,62 | 49% | 1,23 | 59,5 |
| setup L isolado (342 sinais) | 342 | +1,499 | +512,7 | 49,1% | +3,27 | 63% | 1,56 | 74,8 |
| carteira A | 180 | +0,539 | +97,0 | 45,0% | +1,09 | 54% | 1,17 | 68,2 |
| carteira A+B | 291 | +0,837 | +243,5 | 46,7% | +1,92 | 65% | 1,27 | 98,5 |
| carteira A+B+C | 327 | +0,806 | +263,4 | 46,5% | +1,97 | 62% | 1,26 | 80,7 |
| carteira completa ← | 571 | +1,202 | +686,1 | 48,3% | +3,89 | 65% | 1,42 | 73,6 |
| **1ª metade** |  |  |  |  |  |  |  |  |
| setup A isolado (84 sinais) | 84 | +0,096 | +8,0 | 42,9% | +0,13 | 53% | 1,03 | 74,2 |
| setup B isolado (74 sinais) | 74 | -0,061 | -4,5 | 41,9% | -0,06 | 42% | 0,98 | 99,2 |
| setup C isolado (22 sinais) | 22 | +2,030 | +44,7 | 50,0% | +1,53 | 61% | 1,87 | 15,5 |
| setup L isolado (157 sinais) | 157 | +1,670 | +262,1 | 49,7% | +2,39 | 62% | 1,65 | 43,2 |
| carteira A | 79 | +0,136 | +10,8 | 43,0% | +0,18 | 50% | 1,04 | 68,2 |
| carteira A+B | 146 | -0,043 | -6,3 | 41,8% | -0,07 | 55% | 0,99 | 98,5 |
| carteira A+B+C | 165 | +0,188 | +31,0 | 43,0% | +0,31 | 52% | 1,06 | 80,7 |
| carteira completa ← | 281 | +0,993 | +278,9 | 47,3% | +2,15 | 57% | 1,33 | 60,2 |
| **2ª metade** |  |  |  |  |  |  |  |  |
| setup A isolado (106 sinais) | 106 | +0,847 | +89,8 | 46,2% | +1,31 | 58% | 1,28 | 40,4 |
| setup B isolado (59 sinais) | 59 | +2,614 | +154,2 | 57,6% | +2,83 | 69% | 2,08 | 22,2 |
| setup C isolado (21 sinais) | 21 | -0,667 | -14,0 | 38,1% | -0,36 | 37% | 0,83 | 59,5 |
| setup L isolado (185 sinais) | 185 | +1,355 | +250,6 | 48,6% | +2,21 | 64% | 1,49 | 73,0 |
| carteira A | 101 | +0,854 | +86,2 | 46,5% | +1,33 | 58% | 1,28 | 49,1 |
| carteira A+B | 145 | +1,723 | +249,9 | 51,7% | +3,23 | 76% | 1,64 | 32,6 |
| carteira A+B+C | 162 | +1,434 | +232,4 | 50,0% | +2,68 | 72% | 1,50 | 46,6 |
| carteira completa ← | 290 | +1,404 | +407,1 | 49,3% | +3,38 | 72% | 1,51 | 73,6 |

**O filtro de regime subtrai neste ativo.** A carteira que pega todo gatilho mede +1,202 por trade com t +3,89; a de só A mede +0,539, A+B mede +0,837 e A+B+C mede +0,806 — todas abaixo, e com menos operações. O setup isolado mais forte é o **L** (+1,499), e o único que mede positivo nas três colunas é A, L. A leitura é que, no ouro, a barra de range extremo com o pavio do lado certo já carrega o sinal inteiro: exigir que ela apareça num regime específico só joga fora amostra.

### As médias adaptativas

| média de regime | % em tendência | n (setup A) | EV do A | t do A |
| --- | ---: | ---: | ---: | ---: |
| **amostra inteira** |  |  |  |  |
| três EMAs 21/42/72 (empilhamento) | 80% | 190 | +0,515 | +1,05 |
| KAMA (inclinação) | 46% | 123 | +1,851 | +2,77 |
| Hull (inclinação) | 95% | 339 | +1,276 | +3,15 |
| T3 Tillson (inclinação) | 90% | 214 | +0,856 | +1,67 |
| estilo Jurik, aproximação (inclinação) | 92% | 295 | +1,486 | +3,27 |
| **1ª metade** |  |  |  |  |
| três EMAs 21/42/72 (empilhamento) | 80% | 84 | +0,096 | +0,13 |
| KAMA (inclinação) | 45% | 52 | +1,467 | +1,29 |
| Hull (inclinação) | 94% | 153 | +1,115 | +1,92 |
| T3 Tillson (inclinação) | 90% | 100 | +0,520 | +0,65 |
| estilo Jurik, aproximação (inclinação) | 92% | 128 | +1,231 | +1,83 |
| **2ª metade** |  |  |  |  |
| três EMAs 21/42/72 (empilhamento) | 81% | 106 | +0,847 | +1,31 |
| KAMA (inclinação) | 46% | 71 | +2,133 | +2,63 |
| Hull (inclinação) | 95% | 186 | +1,409 | +2,48 |
| T3 Tillson (inclinação) | 91% | 114 | +1,152 | +1,74 |
| estilo Jurik, aproximação (inclinação) | 92% | 167 | +1,682 | +2,72 |

A média **não muda a carteira completa** — ela só decide o regime, e o regime não está sendo usado como filtro (§ 8). O que ela muda é o setup A, e ali quem mede melhor somando as duas metades é a **estilo Jurik, aproximação (inclinação)**. Vale mais como diagnóstico: as EMAs empilhadas veem tendência em 80% das barras e a KAMA em 46%, e nenhuma das duas leituras melhora o resultado da carteira. Num ativo em que o regime não filtra, trocar a média é trocar a etiqueta.

## 10. Estabilidade do corte

EV por trade em USD, carteira completa, stop 7,00. Linha = nível do índice, coluna = corte de posição do corpo. O padrão está em negrito.

**amostra inteira**

| nível \ pos | 50 | 55 | 60 | 65 | 70 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0,80 | +0,26 | +0,27 | +0,37 | +0,53 | +0,21 |
| 0,85 | +0,51 | +0,46 | +0,59 | +0,69 | +0,40 |
| 0,90 | +0,81 | +0,89 | **+1,20** | +1,14 | +0,91 |
| 0,95 | +0,57 | +0,56 | +0,73 | +0,70 | +0,66 |

**1ª metade**

| nível \ pos | 50 | 55 | 60 | 65 | 70 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0,80 | +0,14 | +0,24 | +0,44 | +0,67 | +0,53 |
| 0,85 | +0,27 | +0,36 | +0,53 | +0,59 | +0,35 |
| 0,90 | +0,28 | +0,56 | **+0,99** | +0,94 | +0,87 |
| 0,95 | -0,26 | +0,04 | +0,29 | +0,19 | +0,14 |

**2ª metade**

| nível \ pos | 50 | 55 | 60 | 65 | 70 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0,80 | +0,38 | +0,29 | +0,28 | +0,36 | -0,13 |
| 0,85 | +0,76 | +0,57 | +0,66 | +0,79 | +0,46 |
| 0,90 | +1,34 | +1,22 | **+1,40** | +1,33 | +0,94 |
| 0,95 | +1,39 | +1,06 | +1,14 | +1,16 | +1,17 |

Das 20 células, 20 medem positivo na amostra inteira, 19 na 1ª metade e 19 na 2ª. As negativas são 2, todas nas bordas da varredura. A célula escolhida (0.90 / 60) não é a melhor da amostra inteira — a melhor é 0.90 / 60 — e foi mantida porque é a que mede bem nas *duas* metades. A região é larga: subir ou descer um degrau em qualquer direção não muda o sinal do resultado. Isso não faz do corte um número validado fora da amostra; faz dele um número que não depende de acertar a casa decimal.

## 11. A forma do desempenho

Carteira completa, stop 7,00, **com 0,20 USD de custo por trade**.

|  | amostra inteira | 1ª metade | 2ª metade |
| --- | ---: | ---: | ---: |
| trades | 571 | 281 | 290 |
| por pregão | 6,7 | 6,7 | 6,7 |
| acerto (%) | 47,8 | 47,0 | 48,6 |
| EV por trade | 1,002 | 0,793 | 1,204 |
| média por pregão | 6,73 | 5,3 | 8,12 |
| desvio por pregão | 19,22 | 20,12 | 18,42 |
| pregões positivos (%) | 64,0 | 57,0 | 70,0 |
| pior pregão | -37,7 | -34,9 | -37,7 |
| melhor pregão | 51,3 | 51,3 | 35,6 |
| rebaixamento máximo | 78,2 | 66,8 | 78,2 |
| maior sequência sem ganhar | 9 | 6 | 9 |
| maior sequência de pregões negativos | 3 | 3 | 3 |
| chance de semana negativa (%) | 22 | 28 | 16 |
| chance de mês negativo (%) | 6 | 11 | 3 |
| terminam no alvo (%) | 45,7 | 44,5 | 46,9 |
| terminam no stop (%) | 40,5 | 42,0 | 39,0 |
| terminam em zero a zero (%) | 9,3 | 9,3 | 9,3 |
| terminam no fim do pregão (%) | 4,6 | 4,3 | 4,8 |

São 6,7 trades por pregão com 47,8% de acerto: a maioria das operações perde, e o resultado vem do tamanho dos ganhos. Já houve **9 trades seguidos sem ganhar** e **3 pregões negativos seguidos**, com a vantagem intacta. Uma semana fecha negativa em 22% das vezes e um mês em 6%. Quem não espera isso vai abandonar a estratégia num intervalo que o próprio backtest previa.

## 12. Limites

- **Uma amostra, não duas.** Um instrumento, um histórico. As duas “metades” são o mesmo arquivo partido ao meio — concordância entre elas é evidência fraca, não confirmação fora da amostra.
- **85 pregões, 2026-05-04 a 2026-08-28.** O ouro passou por um regime só nesse intervalo.
- **O corte foi varrido.** O nível 0,90 e o corte de posição 60 vieram da varredura da § 10 sobre esta mesma amostra.
- **Números brutos**, exceto a § 8 e a § 11.
- **Preenchimento otimista** na entrada (a mercado, sem slippage) e **pessimista** na saída (stop antes do alvo quando cabem na mesma barra).
- **O delta é inferido** pela tick rule, não publicado. Ele não é usado como direção, mas entra no eixo `[E2]` da § 5.

## 13. O que fazer com isto

1. **Operar o gatilho inteiro, sem filtro de regime.** A carteira completa mede +1,202 por trade com t +3,89; qualquer subconjunto A/B/C mede menos. São 6,7 operações por pregão — mais que o dobro do que o WIN dava.
2. **Entrar a mercado no fechamento da barra, nunca com limitada no meio do candle.** É a diferença de +1,851 por trade da § 6, e é a única mudança do porte que um operador pode errar sozinho, por hábito vindo do WIN.
3. **Stop 7,0, alvo 10,5, parcial de 50% na distância do stop.** O stop tem de caber FORA da barra do gatilho, que é uma barra de range extremo por construção — o stop escalado do WIN (3,5) fica dentro dela e mede +0,425.
4. **Medir o próprio spread antes de dimensionar.** Com 0,20 USD por trade a vantagem cai para +1,002 e continua de pé; o custo que a zera é 1,20. Todos os números das outras seções são brutos.

