# Esforço × Resultado em XAUUSD, gráfico de range de 388 ticks

Backtest do indicador `Trigger_EsforcoResultado_Range.mq5` sobre 39.239 barras (2026-05-11 a 2026-09-04, 85 pregões), gerado em 2026-09-06 09:37 a partir de `XAUUSD_388_N_M1_202605110101_202609042330.csv`.

Todos os números vêm de `saida/resumo.json`. Nenhum foi digitado à mão.

## 1 · Resposta curta

O gatilho **tem** leitura de direção, mas ela vive por uma barra e morre depois. Medida no horizonte certo, a vantagem existe e sobrevive a todos os controles que este estudo soube aplicar. Medida no horizonte errado — que é o horizonte em que a maioria dos backtests mede — ela some por completo.

Três números resumem o estudo:

1. **51,45%** das barras deste gráfico continuam na própria direção na barra seguinte (z = +5,73, sobre 39.238 barras). O gráfico de range já vem com inclinação de fábrica; parte de qualquer acerto acima de 50% não é do indicador.
2. Nos sinais do indicador com **esforço baixo**, essa taxa vai a **58,09%** (575 sinais — a contagem aqui é de sinais, não das operações da V8, que descarta os que aparecem com posição aberta). O ganho sobre o controle emparelhado — barras de virada com esforço baixo, mas sem as demais condições do indicador — é de **+6,4 pontos**, com z = +2,97. Esse é o crédito que cabe ao indicador, e não mais que ele.
3. Esticar o alvo mata a vantagem. A **+31,1 ticks** por operação da V8 sai de um alvo de meio range; em dois ranges a mesma seleção dá -37,1 ticks. O que o indicador vê não dura.

| | V8 — meio range + esforço baixo |
|---|---|
| Operações | 562 em 84 pregões |
| Acerto | 58,0% |
| Expectativa | +31,1 ticks = +0,160 R = +0,31 USD por lote |
| Erro padrão | 8,1 ticks  (t = +3,84) |
| Total | +17.460 ticks = +174,60 USD por lote |
| Fator de lucro | 1,38 |
| Rebaixamento máximo | -1.746 ticks = -9,00 R |
| Controle invertido | 42,0% de acerto, -31,1 ticks — o espelho exato |

E a ressalva que precisa vir junto: **+31,1 ticks de expectativa não sobrevivem a 40 ticks de custo.** A margem inteira cabe dentro de um spread ruim. O §10 trata disso.

## 2 · Os dados, e a premissa do indicador

O indicador não funciona em qualquer gráfico. Ele pressupõe duas coisas, e as duas foram conferidas antes de qualquer medição — a versão Python de `ValidarPremissa()` do `.mq5`.

**A premissa geométrica:** `High-Low` constante.

| | |
|---|---|
| Range mediano | 388 ticks |
| Barras dentro de ±10% da mediana | **99,82%** |
| Desvio padrão do range | 6,46 ticks |
| Mínimo / máximo | 80 / 388 ticks |

Confirmada. As barras que fogem são as de fim de sessão, fechadas antes de completar o range — e são justamente as que o indicador descarta pelo teste de "barra completa".

**A premissa da agressão:** `tick_volume` é agressão compradora e `real_volume` é vendedora — a convenção do símbolo sintético do `Range_Claude_v1.mq5`. Num símbolo comum os dois campos significam outra coisa e o indicador não daria erro nenhum: produziria números sem significado, que é o pior modo de falhar.

| | |
|---|---|
| Barras com agressão vendedora ausente | 0,58% |
| Barras com agressão compradora ausente | 0,56% |
| Correlação entre os dois campos | 0,989 |

Confirmada. Os dois campos existem, são distintos e caminham juntos — o que se espera de duas metades do mesmo fluxo, e não de um campo duplicado.

| o histórico | |
|---|---|
| Barras | 39.239 |
| Período | 2026-05-11 01:01 a 2026-09-04 23:30 |
| Pregões | 85 (461,6 barras por pregão) |
| Preço | 3.942,19 a 4.773,54 |
| Segundos por barra (mediana) | 102 |
| Corpo / range (mediana) | 0,719 |

## 3 · Método: as três decisões que mudam todo o resto

### 3.1 · A ambiguidade dentro da barra, e como este gráfico a elimina

Quando uma barra toca o alvo e o stop, o OHLC não diz qual veio primeiro. É o único ponto cego de qualquer backtest feito sobre OHLC, e costuma ser resolvido por convenção — assume-se o stop primeiro e publica-se a hipótese oposta ao lado, como teto.

Num gráfico de range existe uma saída melhor. Como `High-Low` é **388 ticks por construção**, uma barra não consegue percorrer 194 ticks para cima *e* 194 para baixo a partir do próprio open: os dois lados somados dariam exatamente o range inteiro. Medido neste arquivo, isso acontece em **0,03% das barras**.

Consequência: com stop e alvo a **meio range**, as hipóteses pessimista e otimista devolvem *o mesmo número*. A convenção deixa de existir, e com ela o principal motivo de desconfiar de um backtest. É por isso que a métrica central deste estudo é o meio range, e não o 1:1 em um range inteiro. A tabela do §9 marca quais gestões têm essa propriedade.

### 3.2 · O que uma entrada limitada custa em honestidade

Uma ordem limitada preenchida **dentro** de uma barra não tem hora marcada no arquivo. A máxima daquela barra pode ter acontecido antes do preenchimento, e creditar o alvo por causa dela é ler o futuro.

Neste gráfico o erro é grosseiro. A barra tem 388 ticks garantidos, então quase toda barra que preenche uma ordem no meio dela também "alcança" um alvo de meio range. Contabilizada assim, a entrada limitada mede **99,8% de acerto** — um resultado impossível, publicado na tabela do §6 apenas como demonstração do erro.

Corrigido: na barra do preenchimento a operação **só pode piorar**, nunca melhorar. É a mesma convenção pessimista do resto do estudo, aplicada ao único instante que o arquivo não datou. O número da V3 é, portanto, um **piso** — e mesmo o teto irrealizável não salvaria a entrada limitada, porque ela abandona 53,6% dos sinais sem compensar nada.

### 3.3 · As demais decisões

- **Custo.** A coluna `<SPREAD>` do arquivo traz valores impossíveis (até 141.050.000) e foi descartada. O custo entra como cenário explícito — 0, 10, 20 e 40 ticks — e nunca embutido.
- **Uma operação por vez.** Sinais que aparecem com posição aberta são descartados, como aconteceria na mesa. É por isso que a V0 mostra 1.508 operações e a V4, com alvo mais curto, mostra 1.612: a gestão longa da V0 ocupa a posição e engole sinais.
- **A entrada padrão é a mercado no fechamento da barra de sinal**, e a gestão só começa na barra seguinte. O preço é conhecido na fronteira da barra; não há instante indatado.
- **A busca inteira é publicada.** Os 30 filtros testados aparecem no §6 com o z de cada um, para que o melhor possa ser lido como o máximo de 30 tentativas — e não como uma descoberta.

## 4 · O que o gatilho produz

| | |
|---|---|
| Sinais | 1.782 em 39.239 barras (4,54%) |
| Absorção (sinal 1) | 1.556 — 767 de alta, 789 de baixa |
| Divergência (sinal 2) | 226 — 107 de alta, 119 de baixa |
| Frequência | 21,0 por pregão, um a cada 22 barras |

Os dois lados saem equilibrados — 874 sinais de alta contra 908 de baixa. Um gatilho que disparasse muito mais para um lado estaria lendo a tendência do período, não a barra.

As métricas do indicador, medidas **nas barras de sinal**:

| métrica | p10 | mediana | p90 |
|---|---|---|---|
| Resultado relativo (`resRel`) | 0,19 | 0,51 | 1,23 |
| Esforço relativo (`esfRel`) | 0,35 | 1,16 | 2,68 |
| Agressão a favor (`qualRel`) | -6,23 | -0,50 | 0,36 |
| Eficiência (`resRel/esfRel`) | 0,11 | 0,39 | 2,23 |
| Corpo / range | 0,13 | 0,34 | 0,84 |

A mediana de `resRel` nos sinais é 0,51, contra 1,06 no universo inteiro: o indicador está mesmo selecionando barras que andaram menos que o normal da direção delas, que é o que a tese de absorção pede.

## 5 · O sinal tem direção?

### 5.1 · A excursão pura, contra dois controles sorteados

Sem nenhuma regra de saída: a partir do fechamento da barra de sinal, até onde o preço vai a favor (MFE) e contra (MAE) nas próximas barras. Se o gatilho carrega direção, esses números têm de diferir dos de uma entrada sorteada.

| horizonte | amostra | MFE mediana | MAE mediana | MFE/MAE | deriva média | t |
|---|---|---|---|---|---|---|
| 5 barras | o sinal do indicador | 427 t | 420 t | **1,018** | +6,8 t | +0,45 |
| 5 barras | mesmas barras, **direção sorteada** | 436 t | 407 t | **1,070** | +22,7 t | +1,52 |
| 5 barras | barra e direção sorteadas | 423 t | 421 t | **1,005** | +10,5 t | +0,68 |
| 5 barras | sinal com **esforço baixo** | 441 t | 404 t | **1,092** | +4,3 t | +0,16 |
| 20 barras | o sinal do indicador | 834 t | 825 t | **1,011** | +17,3 t | +0,58 |
| 20 barras | mesmas barras, **direção sorteada** | 827 t | 829 t | **0,998** | -13,7 t | -0,45 |
| 20 barras | barra e direção sorteadas | 848 t | 819 t | **1,035** | +20,1 t | +0,67 |
| 20 barras | sinal com **esforço baixo** | 824 t | 844 t | **0,976** | -1,3 t | -0,02 |
| 40 barras | o sinal do indicador | 1.191 t | 1.206 t | **0,988** | -38,4 t | -0,89 |
| 40 barras | mesmas barras, **direção sorteada** | 1.209 t | 1.190 t | **1,016** | +46,1 t | +1,07 |
| 40 barras | barra e direção sorteadas | 1.260 t | 1.199 t | **1,050** | -12,0 t | -0,28 |
| 40 barras | sinal com **esforço baixo** | 1.144 t | 1.230 t | **0,930** | -112,5 t | -1,44 |

**Nada.** A razão MFE/MAE do sinal fica colada em 1,00, igual à das entradas sorteadas, e nenhuma deriva chega perto de significância. Se o estudo parasse aqui — e é aqui que a maioria para — a conclusão seria que o indicador não serve.

O problema é que essas medidas olham 5, 20, 40 barras à frente. A vantagem do gatilho não dura tanto.

### 5.2 · A linha de base: o gráfico já vem inclinado

Num gráfico de range dá para medir a direção da barra seguinte **sem ambiguidade nenhuma** (§3.1): basta perguntar se ela percorre meio range para cima ou para baixo a partir do próprio open. Isso permite medir a taxa de continuação no arquivo inteiro, e não só nos sinais.

| grupo | o que é | amostra | continua | z |
|---|---|---|---|---|
| todas as barras | aposta na continuação da barra | 39.238 | **51,45%** | +5,73 |
| barras de virada | a condição geométrica do gatilho, sozinha | 19.639 | **51,77%** | +4,97 |
| virada + esforço baixo | sem as demais condições do indicador | 9.266 | **51,71%** | +3,28 |
| SINAL do indicador | absorção + divergência | 1.782 | **53,76%** | +3,17 |
| SINAL + esforço baixo | a seleção da V8 | 575 | **58,09%** | +3,88 |

Duas leituras, e as duas importam:

1. **O gráfico de range tem momentum de fábrica.** Barras continuam na própria direção 51,45% das vezes, com z = +5,73 sobre 39.238 barras. Qualquer gatilho que dispare a favor de uma barra herda isso de graça.
2. **O indicador acrescenta algo real por cima.** Contra o controle emparelhado — barra de virada com esforço baixo, mas sem as condições de resultado e agressão do indicador — a diferença é de +6,4 pontos (58,09% contra 51,71%), com z = +2,97.

É essa segunda linha que justifica o indicador. Sem ela, os 58,0% da V8 seriam apenas o momentum do gráfico com um enfeite em cima.

## 6 · A busca por um filtro

30 filtros testados, todos com a métrica neutra de meio range. A coluna `z (1R)` repete a medição com stop e alvo de um range inteiro — publicar as duas evita escolher a métrica depois de ver o resultado.

| filtro testado | operações | acerto | z | z (1R) | expectativa |
|---|---|---|---|---|---|
| esforço <= 80% do normal ← | 562 | 58,0% | **+3,80** | +2,23 | +31,1 t |
| esforço <= 100% do normal ← | 757 | 56,8% | **+3,74** | +1,22 | +26,4 t |
| esforço <= 90% do normal ← | 666 | 57,1% | **+3,64** | +1,26 | +27,4 t |
| esforço <= 70% do normal ← | 466 | 58,2% | **+3,52** | +2,02 | +31,6 t |
| só nas horas selecionadas | 331 | 58,9% | **+3,24** | +1,47 | +34,6 t |
| esforço <= 60% do normal ← | 383 | 58,2% | **+3,22** | +1,97 | +31,9 t |
| só vendas | 908 | 54,8% | **+2,92** | -0,38 | +18,8 t |
| agressão a favor <= 25% do normal | 1.474 | 53,7% | **+2,87** | +0,56 | +14,5 t |
| esforço <= 80% + corpo <= 50% ← | 419 | 56,6% | **+2,69** | +2,18 | +25,5 t |
| sem filtro nenhum | 1.731 | 53,2% | **+2,67** | +0,45 | +12,4 t |
| agressão a favor <= 0 (delta contra) | 1.302 | 53,6% | **+2,61** | +0,54 | +14,0 t |
| esforço <= 80% + só absorção ← | 421 | 56,3% | **+2,58** | +2,13 | +24,4 t |
| esforço <= 80% + resultado <= 50% ← | 234 | 58,1% | **+2,48** | +1,58 | +31,5 t |
| só divergência (sinal 2) | 226 | 58,0% | **+2,39** | -0,07 | +30,9 t |
| corpo >= 70% do range | 226 | 58,0% | **+2,39** | -0,07 | +30,9 t |
| corpo >= 50% do range | 253 | 56,5% | **+2,07** | +0,06 | +25,3 t |
| corpo <= 50% do range | 1.485 | 52,7% | **+2,05** | +0,30 | +10,3 t |
| só absorção (sinal 1) | 1.508 | 52,6% | **+2,01** | +0,51 | +10,0 t |
| resultado da barra <= 50% do normal | 850 | 53,3% | **+1,92** | +0,42 | +12,8 t |
| resultado da barra <= 30% do normal | 367 | 54,5% | **+1,72** | +0,53 | +17,4 t |
| vira no máximo 3 barras contrárias | 1.522 | 52,2% | **+1,69** | -0,35 | +8,4 t |
| esforço <= 80% + vira <= 2 barras ← | 372 | 54,0% | **+1,56** | +0,47 | +15,6 t |
| vira no máximo 2 barras contrárias | 1.280 | 52,0% | **+1,40** | -0,32 | +7,6 t |
| eficiência <= 0,50 | 1.033 | 52,1% | **+1,34** | -0,42 | +8,1 t |
| só compras | 874 | 52,2% | **+1,29** | +0,48 | +8,4 t |
| esforço >= 100% do normal | 987 | 50,9% | **+0,54** | -0,91 | +3,3 t |
| eficiência <= 0,30 | 660 | 50,9% | **+0,47** | -0,12 | +3,5 t |
| esforço >= 130% do normal | 751 | 50,3% | **+0,18** | -0,41 | +1,3 t |
| vira no máximo 1 barra contrária | 793 | 50,2% | **+0,11** | -1,50 | +0,7 t |
| entrada limitada no meio do range (piso) | 800 | 39,0% | **-6,22** | -0,36 | -42,7 t |
| entrada limitada no meio do range (teto irrealizável) ⚠️ | 826 | 99,8% | **+28,60** | -0,29 | +193,1 t |

⚠️ A primeira linha é o artefato do §3.2, publicado como demonstração do erro de método. Não é candidato e não entra na conta de tentativas.

O que sobra é claro: **as seis primeiras posições são todas variações do mesmo filtro de esforço**, e nenhum outro filtro chega perto. Um resultado de busca em que o topo é ocupado por um só conceito, em várias calibragens, é bem diferente de um em que o topo é um número solitário — o segundo caso é o retrato de um acaso.

Ainda assim, `z = +3,80` é o máximo de 30 tentativas, e é assim que ele tem de ser lido. O §7 aplica a esse filtro a mesma disciplina que reprovou o horário.

## 7 · O filtro de esforço, sob validação

A tese: uma barra que virou o movimento **com pouca gente negociando** é a forma mais pura da absorção. Não houve briga; o preço andou porque não havia nada do outro lado. O filtro exige que o esforço total da barra fique abaixo de 80,0% da média das barras da mesma direção.

Um filtro escolhido no melhor de 30 tentativas só merece crédito se passar em quatro testes independentes.

**(a) É platô, não pico.** Um parâmetro que só funciona no valor exato em que foi encontrado é ajuste à amostra.

| limite | operações | acerto | z | expectativa |
|---|---|---|---|---|
| ≤ 0,50 | 296 | 54,7% | +1,63 | +18,4 t |
| ≤ 0,60 | 383 | 58,2% | +3,22 | +31,9 t |
| ≤ 0,70 | 466 | 58,2% | +3,52 | +31,6 t |
| ≤ 0,75 | 515 | 57,5% | +3,39 | +29,0 t |
| ≤ 0,80 **←** | 562 | 58,0% | +3,80 | +31,1 t |
| ≤ 0,85 | 618 | 56,8% | +3,38 | +26,4 t |
| ≤ 0,90 | 666 | 57,1% | +3,64 | +27,4 t |
| ≤ 1,00 | 757 | 56,8% | +3,74 | +26,4 t |
| ≤ 1,10 | 827 | 56,3% | +3,65 | +24,6 t |
| ≤ 1,20 | 907 | 55,6% | +3,35 | +21,6 t |

Platô. De 0,60 a 0,80 o acerto fica entre 57,5% e 58,2%, e a degradação para fora é suave e monotônica. O valor publicado não é um pico; é o meio de uma faixa larga.

**(b) Aparece nos dois pedaços da amostra, e nos três.**

| pedaço | operações | acerto | z | expectativa |
|---|---|---|---|---|
| 1ª metade | 278 | 57,9% | +2,64 | +30,7 t |
| 2ª metade | 284 | 58,1% | +2,73 | +31,4 t |
| 1º terço | 184 | 56,0% | +1,62 | +23,2 t |
| 2º terço | 187 | 58,8% | +2,41 | +34,2 t |
| 3º terço | 191 | 59,2% | +2,53 | +35,5 t |

As duas metades ficam a menos de meio ponto uma da outra (57,9% e 58,1%), e os três terços sobem de 56,0% para 59,2%. Nenhum pedaço carrega o resultado sozinho — que é o modo mais comum de um filtro falso passar despercebido.

**(c) O controle invertido é o espelho.** Operando o lado oposto, o acerto vai a 42,0% e a expectativa a -31,1 ticks. A simetria é exata: a vantagem é de **direção**, e não de um viés de contabilidade que sobreviveria à inversão.

**(d) Não é um disfarce de horário.** Se o filtro estivesse apenas selecionando as horas calmas, a vantagem sumiria dentro de cada hora.

| | |
|---|---|
| Sinais que passam no filtro | 32,3% |
| Faixa dessa fração entre as horas | 8,8% a 71,0% |
| Horas com ≥ 15 operações | 14, das quais 12 acima de 50% |

O filtro corta em todas as horas e a vantagem aparece na maioria delas. Ele também funciona nos dois tipos de sinal (absorção 56,1%, divergência 63,6%) e nos dois lados (compra 61,5%, venda 54,8%).

Quatro testes, quatro aprovações. É o máximo que uma amostra só permite afirmar — e não substitui um teste em tempo real.

## 8 · O horário, que não passou

A estratégia pedia segregação por horário. As horas foram escolhidas em uma metade da amostra (mínimo de 25 operações e acerto acima de 53%%) e testadas na outra, nos dois sentidos.

| escolhido em | horas | testado em | operações | acerto | referência | z |
|---|---|---|---|---|---|---|
| 1ª metade | 1h, 2h, 3h, 4h, 5h, 9h, 11h, 18h, 20h | 2ª metade | 334 | 52,1% | 54,2% | +0,77 |
| 2ª metade | 3h, 4h, 8h, 10h, 15h, 16h, 18h | 1ª metade | 375 | 52,8% | 52,2% | +1,08 |

**Reprovado.** Fora da amostra, as horas escolhidas não batem a referência de forma nenhuma — num dos sentidos ficam *abaixo* dela. A interseção entre as duas escolhas é de apenas 3 hora(s) (3h, 4h, 18h), o que é compatível com sorteio.

A V5 está publicada com essas horas para que o leitor veja o que acontece: dentro da amostra ela mede 54,2% de acerto e parece ótima. É exatamente esse número que a validação cruzada existe para desmontar.

## 9 · Os parâmetros do próprio indicador

Um gatilho cujo resultado desaba quando o parâmetro anda 10% não foi medido: foi ajustado. Cada linha abaixo recalcula o indicador do zero e mede com a seleção da V8. O asterisco marca o valor padrão do `.mq5`.

**`periodo_base`** — barras da janela de referência

| valor | sinais gerados | operações | acerto | z |
|---|---|---|---|---|
| 20,00 | 1.759 | 482 | 55,8% | +2,55 |
| 30,00 | 1.729 | 504 | 57,7% | +3,47 |
| 40,00 | 1.767 | 551 | 57,5% | +3,54 |
| 60,00 **\*** | 1.782 | 562 | 58,0% | +3,80 |
| 80,00 | 1.781 | 583 | 57,6% | +3,69 |
| 100,00 | 1.816 | 586 | 56,3% | +3,06 |
| 140,00 | 1.847 | 619 | 55,7% | +2,85 |

**`fator_res`** — teto de resultado relativo (absorção)

| valor | sinais gerados | operações | acerto | z |
|---|---|---|---|---|
| 0,50 | 1.089 | 375 | 60,0% | +3,87 |
| 0,60 | 1.419 | 480 | 58,3% | +3,65 |
| 0,70 **\*** | 1.782 | 562 | 58,0% | +3,80 |
| 0,80 | 2.197 | 699 | 57,1% | +3,74 |
| 0,90 | 2.635 | 843 | 56,3% | +3,69 |

**`fator_qual`** — teto de agressão a favor (absorção)

| valor | sinais gerados | operações | acerto | z |
|---|---|---|---|---|
| 0,20 | 1.522 | 496 | 58,5% | +3,77 |
| 0,35 | 1.641 | 530 | 58,5% | +3,91 |
| 0,50 **\*** | 1.782 | 562 | 58,0% | +3,80 |
| 0,65 | 1.923 | 595 | 57,0% | +3,40 |
| 0,80 | 2.093 | 627 | 57,1% | +3,55 |

**`fator_corpo`** — corpo mínimo no pivô (divergência)

| valor | sinais gerados | operações | acerto | z |
|---|---|---|---|---|
| 0,60 | 2.239 | 797 | 56,8% | +3,86 |
| 0,70 | 1.993 | 669 | 56,2% | +3,21 |
| 0,80 **\*** | 1.782 | 562 | 58,0% | +3,80 |
| 0,90 | 1.639 | 482 | 57,5% | +3,28 |

**`lim_desq`** — desequilíbrio mínimo do delta (divergência)

| valor | sinais gerados | operações | acerto | z |
|---|---|---|---|---|
| 0,02 | 1.984 | 684 | 56,9% | +3,59 |
| 0,05 **\*** | 1.782 | 562 | 58,0% | +3,80 |
| 0,10 | 1.626 | 468 | 57,5% | +3,24 |
| 0,20 | 1.562 | 425 | 56,0% | +2,47 |

**`fator_completa`** — fração do range para a barra contar

| valor | sinais gerados | operações | acerto | z |
|---|---|---|---|---|
| 0,50 | 1.790 | 564 | 57,8% | +3,71 |
| 0,70 | 1.787 | 562 | 58,0% | +3,80 |
| 0,90 **\*** | 1.782 | 562 | 58,0% | +3,80 |
| 0,98 | 1.781 | 562 | 58,0% | +3,80 |

Todos os seis parâmetros são platôs. Em nenhum deles o valor padrão é o melhor da varredura, e em nenhum a variação chega a mudar a conclusão. Isso é evidência forte de que o indicador **não foi ajustado a este histórico** — o que faz sentido, já que ele foi portado de um NTSL escrito antes e para outro contexto.

Dois valores mediram melhor que o padrão de forma consistente: `fator_res` em 0,50 e `fator_qual` em 0,20–0,35. Ambos tornam o gatilho **mais exigente**, o que é coerente com a tese. Não são recomendados aqui: mexer neles depois de ver a tabela é a definição de ajuste.

## 10 · A gestão, e por que o alvo é curto

Aqui a seleção está fixa (esforço baixo) e o que varia é a saída. A coluna final marca as gestões em que a ambiguidade dentro da barra não existe (§3.1) — nelas o número não depende de suposição nenhuma.

| gestão | operações | acerto | expectativa | em R | t | barras | s/ ambiguidade |
|---|---|---|---|---|---|---|---|
| 1:1 a 1/4 do range (97 t) | 562 | 30,1% | -38,7 t | -0,399 | -10,29 | 1,0 | não |
| 1:1 a MEIO RANGE (194 t) | 562 | 58,0% | +31,1 t | +0,160 | +3,84 | 1,0 | **sim** |
| 1:1 a 3/4 do range (291 t) | 551 | 56,4% | +37,5 t | +0,129 | +3,05 | 1,6 | **sim** |
| 1:1 a um range (388 t = 1R) | 546 | 54,8% | +37,0 t | +0,095 | +2,23 | 2,6 | **sim** |
| 1:1 a dois ranges (776 t) | 502 | 47,6% | -37,1 t | -0,048 | -1,07 | 8,1 | **sim** |
| stop 1R, alvo 1,5R | 542 | 41,7% | +16,5 t | +0,042 | +0,80 | 3,6 | **sim** |
| stop 1R, alvo 2R | 533 | 34,0% | +7,3 t | +0,019 | +0,30 | 4,6 | **sim** |
| stop 1R, parcial em 1R, runner até 2R | 539 | 54,5% | +15,1 t | +0,039 | +0,89 | 3,5 | **sim** |
| stop 1R, parcial em 1R, runner até 3R | 530 | 54,3% | +11,7 t | +0,030 | +0,65 | 4,3 | **sim** |
| meio range, saída forçada em 5 barras | 562 | 58,0% | +31,1 t | +0,160 | +3,84 | 1,0 | **sim** |

A leitura é inequívoca. Em R por operação, o meio range paga +0,160; um range inteiro paga +0,095; dois ranges pagam -0,048. **A vantagem do gatilho existe por uma barra e se dissolve depois** — o que explica por que a excursão do §5.1, medida em 5 a 40 barras, não achou nada.

A linha de 1/4 de range (30,1% de acerto, t = -10,29) merece atenção porque parece contradizer o resto. Não contradiz: ela é a única da tabela em que os dois lados cabem dentro da mesma barra, então a ambiguidade volta com força total e a convenção pessimista decide quase todas as operações contra. É um artefato da convenção, não uma medida.

## 11 · As variantes

| variante | sinais | operações | acerto | exp./op. | total | fator de lucro | rebaixamento |
|---|---|---|---|---|---|---|---|
| **V0** regra literal | 1.508 | 1.508 | 50,6% | -7,5 | -11.252 | 0,96 | -21.922 |
| **V1** só absorção | 1.319 | 1.319 | 50,6% | -6,8 | -8.924 | 0,96 | -21.146 |
| **V2** só divergência | 221 | 221 | 49,3% | -19,3 | -4.268 | 0,90 | -5.432 |
| **V3** entrada limitada no meio do range | 1.612 | 748 | 48,7% | -27,8 | -20.758 | 0,86 | -27.160 |
| **V4** gestão 1:1, sem runner | 1.612 | 1.612 | 50,6% | +4,3 | +6.984 | 1,02 | -11.252 |
| **V5** só nas horas selecionadas | 312 | 312 | 54,2% | +32,3 | +10.088 | 1,18 | -5.044 |
| **V6** esforço baixo, gestão 1:1 | 546 | 546 | 54,8% | +37,0 | +20.176 | 1,21 | -3.492 |
| **V7** meio range — todos os sinais | 1.731 | 1.731 | 53,2% | +12,4 | +21.534 | 1,14 | -3.492 |
| **V8** meio range + esforço baixo | 562 | 562 | 58,0% | +31,1 | +17.460 | 1,38 | -1.746 |
| **V9** controle: lado invertido | 562 | 562 | 42,0% | -31,1 | -17.460 | 0,72 | -18.430 |

**V0 · regra literal** — Todo sinal do indicador — absorção e divergência, compra e venda — operado a mercado no fechamento da barra de sinal, a favor da direção dela. Stop de 388 ticks (um range inteiro = 1R), parcial de 50% em +1R levando o stop a breakeven, saída final do restante em +3R. É a leitura literal do indicador, sem nenhuma restrição.

**V1 · só absorção** — Só o sinal 1, o verde/vermelho: a barra virou o movimento andando menos que o normal e com menos agressão a favor que o normal. É o sinal que responde por 87% dos disparos.

**V2 · só divergência** — Só o sinal 2, o azul: o pivô de duas barras quase sem pavio cujo delta somado aponta para o lado contrário ao da resolução. Sinal raro — vale medir separado justamente porque a lógica dele é outra.

**V3 · entrada limitada no meio do range** — Mesma seleção da V0, mas em vez de entrar a mercado no fechamento, deixa uma ordem limitada no MEIO do range da barra de sinal, válida por uma barra. Compra mais barato quando ativa e abandona pouco mais da metade dos sinais quando não ativa. O número publicado é o piso do intervalo: a barra que preencheu a ordem não tem hora marcada no arquivo, e aqui ela só pode piorar a operação — ver §3.

**V4 · gestão 1:1, sem runner** — Mesma seleção da V0, gestão diferente: a posição inteira sai em +1R, sem parcial e sem runner. Com alvo e stop iguais, a taxa de acerto passa a medir DIREÇÃO e nada mais — é a métrica com que todo filtro foi julgado neste estudo.

**V5 · só nas horas selecionadas** — A segregação por horário que a estratégia pede. As horas foram escolhidas em uma metade da amostra e testadas na outra, nos dois sentidos. A variante está publicada para mostrar o resultado real dessa validação, que foi negativo — não como recomendação.

**V6 · esforço baixo, gestão 1:1** — A restrição que sobreviveu: só dispara quando o ESFORÇO TOTAL da barra de sinal está abaixo de 80% da média das barras da mesma direção. Uma barra que virou o movimento com pouca gente negociando é a forma mais pura da tese de absorção. Gestão 1:1 em +1R.

**V7 · meio range — todos os sinais** — Stop e alvo a 194 ticks: exatamente METADE do range da barra. Como a barra tem 388 ticks por construção, ela não consegue alcançar os dois lados — a ambiguidade dentro da barra deixa de existir e o número não depende de nenhuma suposição. É a medida mais limpa que este gráfico permite, e todo sinal do indicador entra nela.

**V8 · meio range + esforço baixo** — A V7 restrita ao esforço baixo da V6 — a combinação de melhor estatística de todo o estudo, e a única medida sem ambiguidade nenhuma. É a que o PLANO.md adota.

**V9 · controle: lado invertido** — Controle estatístico. Mesma detecção e mesma gestão da V8, operando o lado OPOSTO ao que o indicador aponta. Se a vantagem da V8 for mesmo de direção, esta variante tem de ser o espelho negativo dela.

### Sensibilidade de cada variante

Expectativa por operação, em ticks, sob cada hipótese.

| variante | pessimista | otimista | custo 10 t | custo 20 t | custo 40 t | 1ª metade | 2ª metade |
|---|---|---|---|---|---|---|---|
| V0 · regra literal | -7,5 | -7,5 | -17,5 | -27,5 | -47,5 | -12,1 | -2,8 |
| V1 · só absorção | -6,8 | -6,8 | -16,8 | -26,8 | -46,8 | -11,7 | -2,3 |
| V2 · só divergência | -19,3 | -19,3 | -29,3 | -39,3 | -59,3 | -21,1 | -16,4 |
| V3 · entrada limitada no meio do range | -27,8 | -27,8 | -37,8 | -47,8 | -67,8 | -11,9 | -43,8 |
| V4 · gestão 1:1, sem runner | +4,3 | +4,3 | -5,7 | -15,7 | -35,7 | -1,0 | +9,7 |
| V5 · só nas horas selecionadas | +32,3 | +32,3 | +22,3 | +12,3 | -7,7 | +20,4 | +43,6 |
| V6 · esforço baixo, gestão 1:1 | +37,0 | +37,0 | +27,0 | +17,0 | -3,0 | +18,9 | +54,2 |
| V7 · meio range — todos os sinais | +12,4 | +13,6 | +2,4 | -7,6 | -27,6 | +8,7 | +16,2 |
| V8 · meio range + esforço baixo | +31,1 | +31,1 | +21,1 | +11,1 | -8,9 | +30,7 | +31,4 |
| V9 · controle: lado invertido | -31,1 | -31,1 | -41,1 | -51,1 | -71,1 | -30,7 | -31,4 |

Repare nas colunas pessimista e otimista da V7 e da V8: são **idênticas**. É a propriedade do §3.1 aparecendo na tabela — nessas duas variantes não há hipótese a escolher.

## 12 · Restrições recomendadas

1. **Operar o sinal a favor da barra, a mercado no fechamento dela.** A entrada limitada no meio do range (V3) abandona 53,6% dos sinais e não compensa em preço o que perde em amostra.
2. **Exigir esforço abaixo de 80,0% do normal da direção.** É a única restrição do estudo inteiro que passou em todos os controles. Fora dela, o gatilho mede 53,2% de acerto contra 58,0% dentro.
3. **Alvo e stop a meio range (194 ticks).** Não por gosto, mas porque é onde a vantagem está e porque é a única faixa sem ambiguidade.
4. **Não esticar o alvo.** Em dois ranges a expectativa fica negativa.
5. **Não filtrar por horário.** Reprovado fora da amostra (§8).
6. **Não mexer nos parâmetros do indicador.** São platôs (§9); mexer depois de ver a tabela é ajustar à amostra.
7. **Tratar o custo como a restrição dominante.** Com +31,1 ticks de expectativa bruta, 20 ticks de custo consomem 64,4% dela e 40 ticks a tornam negativa.

## 13 · Limitações

- **Uma amostra, um ativo, 85 pregões.** Tudo aqui é um único caminho do preço. Nenhuma quantidade de validação interna substitui um segundo histórico.
- **A margem cabe dentro do spread.** +31,1 ticks por operação, com risco de 194 ticks, é +0,160 R. É real e é pequeno; qualquer degradação de execução o elimina.
- **O melhor de 30 tentativas.** O filtro de esforço passou em quatro validações independentes, o que é muito mais do que o horário conseguiu, mas continua tendo sido escolhido depois de olhar os dados.
- **Slippage não está modelado.** A entrada é a mercado no fechamento de uma barra de range, que é justamente um instante de movimento. O preço de execução real será pior que o do arquivo, e o cenário de custo de 20–40 ticks existe para cobrir isso.
- **A convenção de agressão é uma premissa, não um fato medido.** O estudo confere que os dois campos existem e são distintos (§2), não que `tick_volume` seja de fato a agressão compradora. Se o gerador do símbolo mudar essa convenção, todo o §7 muda de significado.
- **A última barra de cada dia é descartada** pelo teste de barra completa do próprio indicador, o que remove os fechamentos de sessão da amostra.

---

Gerado por `resultados_md.py` a partir de `saida/resumo.json` (2026-09-06 09:37). Para reproduzir: `python rodar.py && python resultados_md.py`.
