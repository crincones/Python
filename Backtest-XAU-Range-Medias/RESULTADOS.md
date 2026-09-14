# Médias + Esforço × Resultado em XAUUSD, gráfico de range de 388 ticks

Backtest da ideia de **seguir a tendência**: as EMAs (ou Hull) de 21, 42 e 72 em leque ordenado e aberto definem o contexto; o indicador `Trigger_EsforcoResultado_Range.mq5` dá o momento de entrar; a gestão é sempre **1:2**, nas três formas pedidas.

39.239 barras (2026-05-11 a 2026-09-04, 85 pregões), gerado em 2026-09-06 10:13 a partir de `XAUUSD_388_N_M1_202605110101_202609042330.csv`. Todos os números vêm de `saida/resumo.json`.

## 1 · Resposta curta

Quatro conclusões, em ordem de quanto se pode confiar nelas.

**1. A EMA vence a Hull.** Na mesma seleção e na mesma gestão, a EMA entrega +0,133 R de expectativa por operação contra +0,030 R da Hull (V2 contra V7). Comparando **par a par** — mesma largura de leque, mesmo modo, mesmo stop — a EMA vence em **69 dos 80 pares** do grid, com diferença mediana de +0,037 R. Das 11 exceções, 9 estão em stops de 291 ou 388 ticks, faixa em que as duas famílias já rendem perto de zero. É a conclusão mais sólida do estudo, porque é uma comparação estrutural e não um máximo escolhido.

**2. O leque ajuda, e ajuda progressivamente.** Sem contexto de médias: +0,062 R. Com o leque ordenado: +0,097 R. Com o leque ordenado *e* aberto: +0,133 R. Cada exigência acrescenta, na ordem esperada — que é o que se quer ver quando uma ideia está certa.

**3. Das três gestões pedidas, duas não são mensuráveis neste gráfico.** As que movem o stop para a entrada — a parcial com stop na entrada e o breakeven puro — dão os melhores números da tabela e nenhum deles significa coisa alguma: dependem de uma ordem de eventos dentro da barra que o arquivo não registra. O intervalo da V5 vai de -0,444 R a +0,253 R. A leitura literal de "breakeven na média da operação" (V4) é a única das duas variantes com parcial que **não** depende de convenção — ver §5.

**4. A configuração campeã não sobrevive à escolha fora da amostra.** Escolhendo a melhor das 96 configurações mensuráveis numa metade do histórico e medindo na outra, o resultado cai de +0,320 R para **+0,035 R** (t = +0,39). O grid mede um passado; ele não previu o futuro dentro do próprio arquivo.

| V2 — a configuração recomendada | |
|---|---|
| Contexto | EMA 21/42/72 ordenadas, leque ≥ 400 ticks |
| Gatilho | sinal do indicador a favor da tendência |
| Gestão | stop 194 t, alvo 388 t — 1:2 fixo |
| Operações | 548 em 83 pregões |
| Acerto | 37,8% |
| Payoff | 2,00 |
| Fator de lucro | 1,21 |
| Expectativa | +0,133 R = +25,8 ticks por operação |
| Significância | t = +2,14 |
| Rebaixamento máximo | -20,0 R (24 operações para se recuperar) |
| Maior sequência de perdas | 14 operações |
| Maior sequência de ganhos | 6 operações |
| Expectativa fora da amostra | **+0,035 R** — é este o número em que acreditar |

> **A ressalva que decide tudo.** +0,133 R sobre um stop de 194 ticks são +25,8 ticks por operação. O custo de ida e volta em XAUUSD raramente fica abaixo disso. Com 20 ticks de custo a V2 entrega +0,030 R; com 40, -0,073 R. Fora da amostra, com custo, não sobra nada.

## 2 · Os dados e a premissa

O indicador pressupõe range constante e a convenção de agressão do símbolo sintético. As duas foram conferidas antes de medir qualquer coisa — é a versão Python de `ValidarPremissa()` do `.mq5`.

| | |
|---|---|
| Range mediano | 388 ticks |
| Barras dentro de ±10% da mediana | **99,82%** |
| Desvio padrão do range | 6,46 ticks |
| Barras sem agressão vendedora | 0,58% |
| Correlação entre as duas agressões | 0,989 |
| Barras | 39.239 em 85 pregões |
| Período | 2026-05-11 01:01 a 2026-09-04 23:30 |
| Preço | 3.942,19 a 4.773,54 |

Premissa confirmada nos dois pontos. O gatilho produz **1.782 sinais** (4,54% das barras, 21,0 por pregão): 1.556 de absorção e 226 de divergência.

## 3 · A estratégia, em três peças

**O contexto.** As três médias (21/42/72) têm de estar ordenadas na direção do sinal — 21 > 42 > 72 para compra. A largura do leque (`|MA21 − MA72|`, em ticks) é a tradução numérica de "não embolado": leque estreito é consolidação, e é onde este tipo de entrada morre.

**O gatilho.** O sinal do `Trigger_EsforcoResultado_Range.mq5`, portado linha a linha para `engine.py`. Ele é um sinal de *virada*: a barra N reverte a barra N−1 e se opera a favor de N. Combinado com o leque, deixa de ser reversão e vira **retomada** — só entra quando a virada aponta para o mesmo lado da tendência.

**A gestão.** Sempre 1:2. Chamando S a distância do stop:

| modo | o que faz | desfechos possíveis |
|---|---|---|
| `fixo` | stop em −S, alvo em +2S, nada se move | −1R ou +2R |
| `parcial` | a +S vende 50% e leva o stop para a **entrada** | −1R, +0,5R, +1,5R |
| `parcial_op` | a +S vende 50% e o stop **fica onde está** | −1R, 0, +1,5R |
| `breakeven` | a +S o stop vai para a **entrada**, sem parcial | −1R, 0, +2R |

Os modos `parcial` e `parcial_op` são as duas leituras possíveis de "parcial que ativa o breakeven na média da operação", e a diferença entre elas é aritmética, não semântica. Com metade realizada em +S, o resultado da operação inteira num stop em −S é

```
0,5 × (+S)  +  0,5 × (−S)  =  0
```

ou seja: **o breakeven da operação já está no stop inicial**. Levar o stop para a entrada (modo `parcial`) não é breakeven — é travar +0,5R. Os dois estão implementados e publicados porque a diferença é material e o enunciado admite as duas.

## 4 · As médias como contexto: EMA contra Hull

Antes de qualquer operação, vale olhar o que cada família de média faz com este gráfico.

| | EMA | Hull |
|---|---|---|
| Barras de aquecimento | 0 | 78 |
| Tempo com leque ordenado | 84,0% | 61,9% |
| Tempo embolado | 16,0% | 38,1% |
| Trocas de lado do leque | 422 | 1.367 |
| Barras entre trocas | 93 | 29 |
| Duração mediana da tendência | 38 barras | 11 barras |
| Leque mediano | 515 ticks | 494 ticks |
| Tempo com leque ≥ 400 t | 60,6% | 58,5% |

A Hull faz exatamente o que promete: persegue o preço de perto e vira antes. O preço disso é trocar de lado 1.367 vezes contra 422 da EMA — 945 trocas a mais no mesmo histórico. Cada troca é uma tendência que a Hull declarou e desfez.

E o resultado operacional segue a estrutura. Par a par — mesma largura de leque, mesmo modo, mesmo stop — a EMA vence em 69 dos 80 pares (entre os mensuráveis, 39 de 48), com diferença mediana de +0,037 R. Sensibilidade a virada não é a mesma coisa que leitura de tendência: para esta estratégia, a média mais lenta é a que serve.

As 11 exceções em que a Hull vence estão todas em stops grandes, onde as duas famílias já rendem perto de zero:

| leque | modo | stop | EMA | Hull |
|---|---|---|---|---|
| ≥600 | `fixo` | 145 t | +0,046 R | +0,075 R |
| ≥600 | `parcial_op` | 145 t | -0,072 R | -0,072 R |
| ≥0 | `fixo` | 291 t | +0,061 R | +0,094 R |
| ≥200 | `fixo` | 291 t | +0,057 R | +0,084 R |
| ≥400 | `fixo` | 291 t | +0,049 R | +0,098 R |
| ≥600 | `fixo` | 291 t | +0,058 R | +0,073 R |
| ≥0 | `fixo` | 388 t | +0,019 R | +0,046 R |
| ≥0 | `breakeven` | 388 t | +0,031 R | +0,033 R |
| ≥200 | `fixo` | 388 t | +0,016 R | +0,035 R |
| ≥200 | `breakeven` | 388 t | +0,023 R | +0,032 R |
| ≥600 | `fixo` | 388 t | +0,023 R | +0,044 R |

## 5 · Quais gestões este gráfico consegue medir

Esta é a seção mais importante do estudo, e a que muda a resposta à pergunta original.

Num gráfico de range vale uma regra geométrica exata: a barra percorre **no máximo 388 ticks**, logo ela não consegue tocar dois níveis separados por mais que isso. Duas consequências.

**[1] Stop e alvo.** Eles distam `S + 2S = 3S`. Se `3S > 388`, nunca são tocados na mesma barra e a hipótese pessimista/otimista deixa de importar. O limite é exato:

```
S > range / 3 = 129,3 ticks
```

**[2] O gatilho de 1R, nos modos que movem o stop para a entrada.** Há um segundo instante que o arquivo não data: a barra que arma o gatilho. Ela **abre exatamente no preço de entrada** (a entrada é o fechamento da barra de sinal), então qualquer pavio contrário faz o preço "voltar ao breakeven" no papel. Como a barra percorre 388 ticks garantidos, isso acontece em praticamente toda barra que arma o gatilho. Só para de acontecer quando o gatilho fica a mais de um range inteiro da entrada.

A tabela abaixo mede a largura do intervalo (piso a teto) de cada combinação. **Largura zero é a prova de que o número não depende de convenção nenhuma.**

| stop | alvo | modo | piso | padrão | teto | largura | mensurável |
|---|---|---|---|---|---|---|---|
| 194 t | 388 t | `fixo` | +0,133 | +0,133 | +0,133 | 0,000 R | **sim** |
| 194 t | 388 t | `parcial` | -0,166 | +0,176 | +0,188 | 0,354 R | não |
| 194 t | 388 t | `parcial_op` | +0,123 | +0,123 | +0,134 | 0,011 R | **sim** |
| 194 t | 388 t | `breakeven` | -0,444 | +0,240 | +0,253 | 0,697 R | não |
| 388 t | 776 t | `fixo` | +0,022 | +0,022 | +0,022 | 0,000 R | **sim** |
| 388 t | 776 t | `parcial` | +0,016 | +0,053 | +0,053 | 0,037 R | não |
| 388 t | 776 t | `parcial_op` | +0,043 | +0,043 | +0,043 | 0,000 R | **sim** |
| 388 t | 776 t | `breakeven` | -0,023 | +0,051 | +0,051 | 0,074 R | não |
| 450 t | 900 t | `fixo` | +0,033 | +0,033 | +0,033 | 0,000 R | **sim** |
| 450 t | 900 t | `parcial` | +0,058 | +0,058 | +0,058 | 0,000 R | **sim** |
| 450 t | 900 t | `parcial_op` | +0,052 | +0,052 | +0,052 | 0,000 R | **sim** |
| 450 t | 900 t | `breakeven` | +0,055 | +0,055 | +0,055 | 0,000 R | **sim** |

Leia a tabela de baixo para cima. Com stop de 450 ticks — mais que um range inteiro — **os quatro modos ficam mensuráveis**, exatamente como a geometria previa. E aí a vantagem já evaporou: os quatro convergem para perto de +0,05 R.

Com stop de 194 ticks, ao contrário, os dois modos que movem o stop para a entrada têm intervalos de 0,354 R e 0,697 R de largura — ou seja, o número deles é indeterminado. E são justamente eles que aparecem no topo de qualquer ranking.

> **Conclusão de método.** Dos três modos de gestão pedidos, o `fixo` e o `parcial_op` (a leitura literal de "breakeven na média da operação") são mensuráveis neste gráfico. O `parcial` com stop na entrada e o `breakeven` puro não são — não porque a estratégia seja ruim, mas porque este histórico não contém a informação necessária para julgá-la. Para medi-los seria preciso um arquivo de ticks, não de barras.

## 6 · A varredura do stop

Com a gestão fixa e a seleção da V2, variando só o tamanho do stop (o alvo acompanha, sempre 2×).

| stop | alvo | ops | acerto | expectativa | t | largura | 1ª metade | 2ª metade |
|---|---|---|---|---|---|---|---|---|
| 110 t | 220 t | 552 | 33,3% | 0,000 R | 0,00 | 0,505 ✗ | -0,088 R | +0,079 R |
| 120 t | 240 t | 552 | 37,0% | +0,109 R | +1,76 | 0,245 ✗ | +0,004 R | +0,202 R |
| 130 t | 260 t | 552 | 40,0% | +0,201 R | +3,21 | 0,000 ✔ | +0,062 R | +0,325 R |
| 135 t | 270 t | 551 | 40,1% | +0,203 R | +3,24 | 0,000 ✔ | +0,054 R | +0,336 R |
| 145 t | 290 t | 549 | 39,5% | +0,186 R | +2,97 | 0,000 ✔ | +0,035 R | +0,320 R |
| 160 t | 320 t | 549 | 39,0% | +0,169 R | +2,71 | 0,000 ✔ | 0,000 R | +0,320 R |
| 175 t | 350 t | 549 | 38,8% | +0,164 R | +2,63 | 0,000 ✔ | +0,012 R | +0,299 R |
| 194 t **←** | 388 t | 548 | 37,8% | +0,133 R | +2,14 | 0,000 ✔ | +0,058 R | +0,200 R |
| 220 t | 440 t | 544 | 37,5% | +0,125 R | +2,01 | 0,000 ✔ | +0,043 R | +0,198 R |
| 250 t | 500 t | 541 | 37,2% | +0,115 R | +1,84 | 0,000 ✔ | +0,039 R | +0,181 R |
| 291 t | 582 t | 532 | 35,0% | +0,049 R | +0,79 | 0,000 ✔ | -0,036 R | +0,124 R |
| 388 t | 776 t | 511 | 34,1% | +0,022 R | +0,34 | 0,000 ✔ | -0,013 R | +0,051 R |

Três leituras.

1. **O limite geométrico aparece na régua.** A largura do intervalo cai de 0,245 em S=120 para exatamente **zero** em S=130. O limite teórico era 129,3. A previsão e a medição batem.
2. **Há platô, não pico.** De 130 a 220 ticks a expectativa desce suavemente de +0,201 para +0,125. Um parâmetro que só funciona num valor exato seria ajuste; este não é o caso.
3. **Mas as duas metades não se parecem.** Em toda linha da tabela, a 1ª metade fica perto de zero e a 2ª carrega o resultado. Isso não é propriedade do parâmetro — é propriedade do período. O §8 trata disso.

## 7 · O grid completo

160 configurações medidas: 2 famílias de média × 4 larguras de leque × 4 modos de gestão × 5 tamanhos de stop. Publicar o grid inteiro é o que permite ler o melhor número como o máximo de 160 tentativas.

**As dez melhores por expectativa:**

| média | leque | modo | stop | ops | acerto | expectativa | PF | t | mensurável |
|---|---|---|---|---|---|---|---|---|---|
| EMA | ≥400 | `breakeven` | 194 t | 550 | 34,2% | +0,240 R | 1,54 | +4,25 | ✗ indeterminado |
| EMA | ≥0 | `breakeven` | 194 t | 733 | 32,9% | +0,213 R | 1,48 | +4,40 | ✗ indeterminado |
| EMA | ≥200 | `breakeven` | 194 t | 675 | 32,4% | +0,201 R | 1,45 | +4,01 | ✗ indeterminado |
| EMA | ≥400 | `fixo` | 145 t | 549 | 39,5% | +0,186 R | 1,31 | +2,97 | **sim** |
| EMA | ≥600 | `breakeven` | 194 t | 373 | 32,7% | +0,182 R | 1,39 | +2,66 | ✗ indeterminado |
| EMA | ≥400 | `breakeven` | 145 t | 550 | 36,7% | +0,180 R | 1,32 | +2,99 | ✗ indeterminado |
| EMA | ≥400 | `parcial` | 194 t | 550 | 55,6% | +0,176 R | 1,40 | +3,72 | ✗ indeterminado |
| EMA | ≥0 | `parcial` | 194 t | 733 | 55,5% | +0,162 R | 1,36 | +3,97 | ✗ indeterminado |
| EMA | ≥0 | `fixo` | 145 t | 733 | 38,6% | +0,158 R | 1,26 | +2,93 | **sim** |
| HULL | ≥0 | `breakeven` | 194 t | 511 | 30,3% | +0,155 R | 1,34 | +2,73 | ✗ indeterminado |

Das 160 configurações, apenas **96 são mensuráveis** sem depender de convenção. E o topo do ranking geral é dominado justamente pelas indeterminadas.

**As cinco melhores entre as mensuráveis:**

| média | leque | modo | stop | ops | acerto | expectativa | PF | payoff | t |
|---|---|---|---|---|---|---|---|---|---|
| EMA | ≥400 | `fixo` | 145 t | 549 | 39,5% | +0,186 R | 1,31 | 2,00 | +2,97 |
| EMA | ≥0 | `fixo` | 145 t | 733 | 38,6% | +0,158 R | 1,26 | 2,00 | +2,93 |
| EMA | ≥200 | `fixo` | 145 t | 674 | 38,4% | +0,153 R | 1,25 | 2,00 | +2,72 |
| EMA | ≥400 | `fixo` | 194 t | 548 | 37,8% | +0,133 R | 1,21 | 2,00 | +2,14 |
| EMA | ≥400 | `parcial_op` | 194 t | 548 | 51,6% | +0,123 R | 1,28 | 1,20 | +2,55 |

Note que **todas as cinco são EMA**. Nenhuma configuração com Hull entra no topo das mensuráveis.

## 8 · A escolha fora da amostra — o teste que reprova

Com 96 configurações mensuráveis, o melhor número da tabela é o máximo de 96 tentativas e não serve de estimativa de nada. A única leitura honesta é escolher onde não se vai medir, e medir onde não se escolheu.

| escolhido em | configuração escolhida | dentro da amostra | **fora da amostra** | mediana das candidatas fora |
|---|---|---|---|---|
| 1ª metade | EMA, leque ≥ 600, `parcial`, stop 450 t | +0,064 R (t = +0,80) | **+0,037 R** (t = +0,46, n = 177) | +0,104 R |
| 2ª metade | EMA, leque ≥ 400, `fixo`, stop 145 t | +0,320 R (t = +3,65) | **+0,035 R** (t = +0,39, n = 258) | -0,039 R |

**Reprovado.** Escolhendo na 2ª metade, a campeã mede +0,320 R lá dentro e entrega +0,035 R na 1ª metade — praticamente nada, com t = +0,39. Escolhendo na 1ª metade, a campeã escolhida entrega +0,037 R na 2ª, *abaixo* da mediana das candidatas (+0,104 R): a seleção foi pior que escolher ao acaso entre as concorrentes.

É por isso que este relatório recomenda a V2 e não a campeã do grid. A V2 não foi escolhida por ser a melhor: foi escolhida por ser a mais simples que respeita a geometria — leque aberto, gestão fixa, stop em meio range. O número que se deve esperar dela é o **fora da amostra**, não o de dentro.

## 9 · Validação e controles

| pedaço da amostra | ops | acerto | expectativa | t |
|---|---|---|---|---|
| **amostra inteira** | 548 | 37,8% | +0,133 R | +2,14 |
| 1ª metade | 258 | 35,3% | +0,058 R | +0,65 |
| 2ª metade | 290 | 40,0% | +0,200 R | +2,31 |
| 1º terço | 173 | 35,8% | +0,075 R | +0,69 |
| 2º terço | 171 | 35,1% | +0,053 R | +0,48 |
| 3º terço | 204 | 41,7% | +0,250 R | +2,41 |

**O resultado está concentrado no fim do histórico.** Os dois primeiros terços rendem +0,075 R e +0,053 R — indistinguíveis de zero. O terceiro rende +0,250 R e responde sozinho por quase todo o resultado. Isso é o padrão de uma estratégia que funcionou num regime de mercado, não de uma que funciona.

Os controles, por outro lado, se comportam como deveriam:

| controle | o que é | ops | acerto | expectativa | t |
|---|---|---|---|---|---|
| invertido | a mesma coisa, operando o lado oposto | 541 | 29,0% | -0,129 R | -2,21 |
| sem_leque | sem exigir contexto de médias | 1.686 | 35,4% | +0,062 R | +1,78 |
| leque_contra | só sinais CONTRA a tendência das médias | 761 | 34,3% | +0,029 R | +0,56 |
| direcao_sorteada | mesmas barras, direção sorteada, mesma gestão | 547 | 32,0% | -0,040 R | -0,67 |

O invertido é claramente negativo (-0,129 R, t = -2,21): a vantagem é de **direção**, e não um artefato de contabilidade. A direção sorteada nas mesmas barras dá -0,040 R, o que mostra que a gestão 1:2 sozinha não produz vantagem nenhuma — o que existe vem do gatilho. E operar *contra* o leque rende +0,029 R, contra +0,133 R a favor: o contexto das médias está do lado certo.

## 10 · As variantes

| variante | ops | acerto | payoff | PF | expectativa | t | DD | seq. perdas | seq. ganhos | mensurável |
|---|---|---|---|---|---|---|---|---|---|---|
| **V0** só o gatilho, sem contexto de médias | 1.686 | 35,4% | 2,00 | 1,10 | +0,062 R | +1,78 | -34,0 R | 18 | 7 | sim |
| **V1** EMA em leque ordenado | 730 | 36,6% | 2,00 | 1,15 | +0,097 R | +1,82 | -27,0 R | 15 | 6 | sim |
| **V2** EMA em leque aberto (≥400 t) | 548 | 37,8% | 2,00 | 1,21 | +0,133 R | +2,14 | -20,0 R | 14 | 6 | sim |
| **V3** EMA + parcial 50%, stop na entrada | 550 | 55,6% | 1,11 | 1,40 | +0,176 R | +3,72 | -11,5 R | 8 | 7 | **✗** |
| **V4** EMA + parcial 50%, breakeven da operação | 548 | 51,6% | 1,20 | 1,28 | +0,123 R | +2,55 | -13,5 R | 8 | 7 | sim |
| **V5** EMA + breakeven em 1R, sem parcial | 550 | 34,2% | 2,00 | 1,54 | +0,240 R | +4,25 | -13,0 R | 8 | 5 | **✗** |
| **V6** Hull em leque ordenado | 509 | 34,6% | 2,00 | 1,06 | +0,037 R | +0,59 | -45,0 R | 15 | 9 | sim |
| **V7** Hull em leque aberto (≥400 t) | 405 | 34,3% | 2,00 | 1,05 | +0,030 R | +0,42 | -39,0 R | 16 | 9 | sim |
| **V8** Hull + breakeven em 1R | 406 | 29,3% | 2,00 | 1,31 | +0,138 R | +2,19 | -19,0 R | 7 | 8 | **✗** |
| **V9** EMA + esforço baixo | 168 | 41,7% | 2,00 | 1,43 | +0,250 R | +2,18 | -9,0 R | 8 | 4 | sim |
| **V10** controle: lado invertido | 541 | 29,0% | 2,00 | 0,82 | -0,129 R | -2,21 | -79,0 R | 14 | 5 | sim |

Detalhe de cada uma:

**V0 · só o gatilho, sem contexto de médias** — O ponto de partida: o sinal do indicador operado a favor da barra, com stop de 194 ticks (meio range) e alvo de 388 (um range) — 1:2 fixo, sem nenhuma leitura de tendência. Serve de linha de base para medir o que as médias acrescentam.

**V1 · EMA em leque ordenado** — Acrescenta a primeira metade da ideia: só opera quando as três EMAs (21/42/72) estão ordenadas na mesma direção do sinal. O gatilho deixa de ser reversão e vira retomada de tendência.

**V2 · EMA em leque aberto (≥400 t)** — Acrescenta a segunda metade: o leque tem de estar ABERTO — a distância entre a EMA21 e a EMA72 de pelo menos 400 ticks (4 dólares). É a tradução numérica de "médias não emboladas". Gestão fixa 1:2. É a configuração recomendada.

**V3 · EMA + parcial 50%, stop na entrada** — A mesma seleção da V2 com a segunda gestão pedida: a +1R vende 50% e leva o stop para a entrada. Desfechos possíveis: −1R, +0,5R ou +1,5R. O número desta variante depende de uma convenção que o arquivo não resolve — ver §5.

**V4 · EMA + parcial 50%, breakeven da operação** — A leitura literal de "breakeven na média da operação": a +1R vende 50% e o stop FICA ONDE ESTÁ — porque, com metade realizada em +1R, a operação inteira já empata exatamente no stop inicial. Desfechos: −1R, 0 ou +1,5R. Não depende de convenção nenhuma.

**V5 · EMA + breakeven em 1R, sem parcial** — A terceira gestão pedida: a +1R o stop vai para a entrada, sem parcial. Desfechos: −1R, 0 ou +2R. É a que mede melhor de todas — e a que menos se pode acreditar, pelo motivo do §5.

**V6 · Hull em leque ordenado** — A V1 com médias de Hull no lugar das exponenciais, mesmos períodos. A Hull persegue o preço muito mais de perto: vira antes, e o leque dela abre e fecha muito mais vezes.

**V7 · Hull em leque aberto (≥400 t)** — A V2 com Hull. É a comparação direta que responde qual família de média serve melhor a esta estratégia.

**V8 · Hull + breakeven em 1R** — A melhor gestão aplicada à Hull, para checar se a desvantagem da Hull vem do contexto ou da gestão.

**V9 · EMA + esforço baixo** — A V2 mais o filtro que sobreviveu ao estudo anterior deste gráfico: esforço total da barra de sinal abaixo de 80% da média das barras da mesma direção. Testa se os dois filtros se somam ou se brigam.

**V10 · controle: lado invertido** — Controle estatístico. Mesma detecção e mesma gestão da V2, operando o lado OPOSTO. Se a vantagem da V2 for de direção, esta variante tem de ser claramente negativa.

### Estatística completa das variantes mensuráveis

| | V0 | V1 | V2 | V4 | V6 | V7 | V9 | V10 |
|---|---|---|---|---|---|---|---|---||
| Operações | 1.686 | 730 | 548 | 548 | 509 | 405 | 168 | 541 |
| Vitórias | 597 | 267 | 207 | 283 | 176 | 139 | 70 | 157 |
| Perdas | 1.089 | 463 | 341 | 265 | 333 | 266 | 98 | 384 |
| Neutras | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Acerto | 35,4% | 36,6% | 37,8% | 51,6% | 34,6% | 34,3% | 41,7% | 29,0% |
| Ganho médio | +388,0 t | +388,0 t | +388,0 t | +212,9 t | +388,0 t | +388,0 t | +388,0 t | +388,0 t |
| Perda média | -194,0 t | -194,0 t | -194,0 t | -177,9 t | -194,0 t | -194,0 t | -194,0 t | -194,0 t |
| Payoff | 2,00 | 2,00 | 2,00 | 1,20 | 2,00 | 2,00 | 2,00 | 2,00 |
| Fator de lucro | 1,10 | 1,15 | 1,21 | 1,28 | 1,06 | 1,05 | 1,43 | 0,82 |
| Fator de recuperação | 3,09 | 2,63 | 3,65 | 5,00 | 0,42 | 0,31 | 4,67 | -0,89 |
| Expectativa (R) | +0,062 | +0,097 | +0,133 | +0,123 | +0,037 | +0,030 | +0,250 | -0,129 |
| Expectativa (ticks) | +12,1 | +18,9 | +25,8 | +23,9 | +7,2 | +5,7 | +48,5 | -25,1 |
| Desvio (ticks) | 278,4 | 280,5 | 282,4 | 219,5 | 277,1 | 276,7 | 287,8 | 264,4 |
| t | +1,78 | +1,82 | +2,14 | +2,55 | +0,59 | +0,42 | +2,18 | -2,21 |
| SQN | 1,78 | 1,82 | 2,14 | 2,55 | 0,59 | 0,42 | 2,18 | -2,21 |
| Rebaixamento (R) | -34,0 | -27,0 | -20,0 | -13,5 | -45,0 | -39,0 | -9,0 | -79,0 |
| Rebaixamento (ops) | 140 | 61 | 24 | 24 | 220 | 172 | 19 | 500 |
| Máx. perdas seguidas | 18 | 15 | 14 | 8 | 15 | 16 | 8 | 14 |
| Máx. ganhos seguidos | 7 | 6 | 6 | 7 | 9 | 9 | 4 | 5 |
| Máx. sem ganho seguidas | 18 | 15 | 14 | 8 | 15 | 16 | 8 | 14 |
| Média de perdas seguidas | 2,90 | 2,82 | 2,80 | 1,99 | 3,14 | 3,06 | 2,45 | 3,52 |
| Barras por operação | 1,6 | 1,7 | 1,6 | 1,6 | 1,7 | 1,7 | 1,7 | 1,6 |
| Operações por pregão | 19,8 | 8,7 | 6,6 | 6,6 | 6,2 | 5,1 | 2,5 | 6,5 |
| Dias positivos | 42 | 43 | 43 | 52 | 30 | 32 | 31 | 27 |
| Dias negativos | 35 | 34 | 32 | 29 | 42 | 35 | 28 | 47 |

### Sensibilidade

Expectativa em R por operação, sob cada hipótese e com cada custo.

| variante | piso | padrão | teto | custo 10 t | custo 20 t | custo 40 t | 1ª metade | 2ª metade |
|---|---|---|---|---|---|---|---|---|
| V0 · só o gatilho, sem contexto de médias | +0,062 | +0,062 | +0,062 | +0,011 | -0,041 | -0,144 | +0,001 | +0,124 |
| V1 · EMA em leque ordenado | +0,097 | +0,097 | +0,097 | +0,046 | -0,006 | -0,109 | +0,028 | +0,163 |
| V2 · EMA em leque aberto (≥400 t) | +0,133 | +0,133 | +0,133 | +0,082 | +0,030 | -0,073 | +0,058 | +0,200 |
| V3 · EMA + parcial 50%, stop na entrada | -0,166 | +0,176 | +0,188 | +0,125 | +0,073 | -0,030 | +0,089 | +0,254 |
| V4 · EMA + parcial 50%, breakeven da operação | +0,123 | +0,123 | +0,134 | +0,072 | +0,020 | -0,083 | +0,048 | +0,190 |
| V5 · EMA + breakeven em 1R, sem parcial | -0,444 | +0,240 | +0,253 | +0,188 | +0,137 | +0,034 | +0,143 | +0,326 |
| V6 · Hull em leque ordenado | +0,037 | +0,037 | +0,037 | -0,014 | -0,066 | -0,169 | -0,160 | +0,228 |
| V7 · Hull em leque aberto (≥400 t) | +0,030 | +0,030 | +0,030 | -0,022 | -0,073 | -0,177 | -0,165 | +0,209 |
| V8 · Hull + breakeven em 1R | -0,447 | +0,138 | +0,143 | +0,086 | +0,035 | -0,068 | +0,036 | +0,232 |
| V9 · EMA + esforço baixo | +0,250 | +0,250 | +0,250 | +0,198 | +0,147 | +0,044 | +0,200 | +0,290 |
| V10 · controle: lado invertido | -0,129 | -0,129 | -0,129 | -0,181 | -0,232 | -0,336 | -0,071 | -0,182 |

As colunas *piso* e *teto* são a mesma coisa nas variantes mensuráveis e se afastam nas outras — é a propriedade do §5 aparecendo na tabela.

## 11 · Restrições recomendadas

1. **Usar EMA, não Hull.** A conclusão mais sólida do estudo, e a única que vale independentemente de qualquer escolha de parâmetro.
2. **Exigir o leque ordenado e aberto** (≥ 400 ticks entre a EMA21 e a EMA72). Cada exigência acrescentou, na ordem esperada.
3. **Preferir a gestão fixa, ou a parcial com breakeven da operação.** São as duas mensuráveis. As outras duas podem até ser melhores na prática — este histórico simplesmente não permite saber.
4. **Stop entre 130 e 220 ticks.** Abaixo de 129 ticks o resultado deixa de ser mensurável; acima de 250 a vantagem some.
5. **Não operar contra o leque.** Rende +0,029 R contra +0,133 R a favor.
6. **Esperar +0,035 R, não +0,133 R.** O primeiro é o número fora da amostra; o segundo é o de dentro.
7. **Tratar o custo como a restrição dominante.** Ver §1.

## 12 · Limitações

- **O resultado vive no último terço do histórico.** Os dois primeiros terços são indistinguíveis de zero. Essa é a limitação mais séria, e nenhuma outra a compensa.
- **A escolha de configuração não validou fora da amostra** (§8). O grid descreve o passado; não mostrou capacidade de prever.
- **Duas das três gestões pedidas não são mensuráveis** neste tipo de arquivo (§5). Para julgá-las é preciso histórico de ticks.
- **Uma amostra, um ativo, 85 pregões.** Nenhuma validação interna substitui um segundo histórico.
- **Slippage não está modelado.** A entrada é a mercado no fechamento de uma barra de range — um instante de movimento, onde a execução é pior que a média.
- **A convenção de agressão é premissa, não fato medido.** O estudo confere que os dois campos existem e são distintos, não que `tick_volume` seja de fato a agressão compradora.
- **O leque de 400 ticks foi escolhido olhando os dados.** Ele fica num platô e a progressão V0→V1→V2 é monotônica, o que ajuda — mas continua sendo um número escolhido depois de ver o resultado.

---

Gerado por `resultados_md.py` a partir de `saida/resumo.json` (2026-09-06 10:13). Para reproduzir: `python rodar.py && python resultados_md.py`.
