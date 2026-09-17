# Especificacao da estrategia

> **Atualizacao 14/09/2026.** Todos os estudos agora rodam sobre `WINFUT/WINFUT_20PI_Robo.csv`
> (50.611 candles, 132 pregoes, 06/03 a 14/09/2026), carregada por `engine.carrega()`; a base antiga
> continua disponivel com `WINFUT_BASE=WINFUT_20PI.csv`. As regras e a engine descritas abaixo nao
> mudaram. Os **numeros** citados neste documento sao da base antiga (26 pregoes); os atuais estao em
> `RESULTADOS.md`, que tambem traz o teste fora da amostra (`periodos.py`), a sensibilidade da entrada
> antecipada ao caminho dentro do candle e a hipotese da retracao profunda (`candidato.py`). Diferencas
> de formato da base nova: hora so ate o minuto, sem a EMA da Nelogica, e agressao/duracao na propria
> linha do candle (sem volume total e sem numero de negocios -- `fluxo.py` usa o volume agressor).

O que o codigo faz, em detalhe, e **por que** cada decisao de medicao foi
tomada assim. Os resultados estao em [RESULTADOS.md](RESULTADOS.md); o que
fazer na frente da tela esta em [PLANO.md](PLANO.md).

---

## 1. A base

`WINFUT/WINFUT_20PI.csv` -- exportacao do ProfitChart, 10.000 candles de
**20 PI** (Pontos de Inversao) do WINFUT, 26 pregoes, 06/08/2026 a
11/09/2026. Vem do mais novo para o mais antigo, separado por TAB, com
virgula decimal.

**O que e um grafico de 20 PI.** Nao e grafico de tempo. Um candle novo
nasce quando o preco anda 20 ticks (= 100 pontos no WIN) na direcao do
candle em formacao. Consequencias, todas verificadas na base:

| Fato | Medido |
|:---|---:|
| corpo = exatamente 100 pontos | 99,99% dos candles |
| abertura = fechamento do candle anterior | 99,52% (o resto e virada de dia) |
| range mediano | 145 pontos |
| candles por pregao | 385 em media |

O unico candle com corpo diferente de 100 e o ultimo de um pregao, que
fecha incompleto.

**A segunda base.** `WINFUT/WINFUT_20PI_Agr_Tempo.csv` e a *mesma* serie
com quatro colunas a mais: volume agressor comprador, volume agressor
vendedor, duracao da barra e numero de negocios. `fluxo.py` a anexa a base
principal. Duas armadilhas, as duas tratadas la:

- **43 timestamps se repetem** (barras fechadas no mesmo milissegundo) e os
  dois arquivos listam as mesmas barras em **ordem diferente** dentro de um
  grupo desses. Casar por timestamp faria produto cartesiano e grudaria a
  agressao na barra errada; o alinhamento e posicional, com permutacao
  dentro de cada grupo para casar o OHLC.
- **`BarDurationF*1000` esta em minutos x 1000**, nao em segundos --
  conferido contra o intervalo real ate a barra seguinte (correlacao
  1,0000). `dur_s = dur_f * 0,06`.

A ultima barra da base antiga estava **em formacao** na hora da exportacao
(fecha a 40 pontos da abertura, nao a 100); e a unica divergencia tolerada
no alinhamento.

**Esforco x resultado, e o que o PI faz com a conta.** No grafico de ticks
essa razao precisa da divisao porque o resultado varia. Aqui o resultado
esta **fixo por construcao** -- todo corpo vale 100 pontos -- entao o
esforco sozinho ja *e* a razao, sem normalizar nada. E a leitura
geometrica dela, `100 / range`, **ja e o filtro de pavio do Ouro** escrito
ao contrario: `range = 100 + pavio`, entao `100/range` e monotonico em
pavio (correlacao de posto medida: -1,0000; `engine.sinais()` devolve isso
como `corpo_r`). Ver `esforco.py`.

**A consequencia que muda o estudo:** com o corpo fixo, o candle nao tem
relacao corpo/pavio -- ela seria so o inverso do range. **A unica forma que
um candle de PI carrega e o tamanho do pavio.** Por isso o estudo da
"geometria do candle que retoma a tendencia" (pedido no CLAUDE.md) olha o
**pavio total** em pontos, que e `range - 100`.

---

## 2. Indicadores

| Indicador | Formula | Conferencia |
|:---|:---|:---|
| **EMA 21** | EMA sobre o fechamento, semente = media aritmetica dos 21 primeiros | conferida contra a coluna `Media Movel E [21]` do proprio csv: erro maximo 0,944 ponto em 9.980 candles, e 57 divergencias reais (falhas do arquivo) |
| **Hull 50** | `WMA(2*WMA(25) - WMA(50), 7)` sobre o fechamento | -- |
| **ATR 21** | media **exponencial** do range verdadeiro | mediana 148 pontos |
| **Keltner** | EMA 21 +/- 2,0 x ATR 21 | a media do canal **e** a media de tendencia, como exige o CLAUDE.md |

A restricao do CLAUDE.md -- "a EMA deve ser a media do keltner sempre" --
amarra os tres: mexer no periodo da EMA mexe no canal junto. O estudo de
periodos em RESULTADOS.md respeita isso (a EMA e o ATR andam juntos; so a
Hull varia livre).

---

## 3. O padrao, na forma em que foi medido

Compra (venda e o espelho exato). Avaliado no fechamento do candle `g`,
que e o candle de **continuacao**:

```
g      fecha a favor  (alta)
g-1    fecha contra   (baixa)          <- ultimo candle da retracao
       hma[g] > hma[g-1]                  Hull ascendente
       hma[g] < high[g]                   Hull atras do extremo
       high[g]   > hma[g]                 os DOIS extremos do par
       high[g-1] > hma[g-1]               do lado de fora da Hull
       min(low) <= ema[g] <= max(high)    EMA 21 atravessando o par
```

Isso da **655 sinais** (333 de compra, 322 de venda) em 26 pregoes.

Tudo o mais -- concavidade, tamanho da retracao, pavio, distancia da Hull
as bandas, hora -- e **medido e guardado como coluna**, nunca filtrado na
geracao. Os filtros sao aplicados depois, sobre a tabela pronta. Essa
separacao e o que permite comparar filtros sem refazer o backteste e sem
que um filtro esconda o outro.

### Os tres niveis

Encaixados: todo Ouro e Prata, todo Prata e Bronze.

| Nivel | Regra | Sinais |
|:---|:---|---:|
| **Bronze** | a regra-base acima, nada mais | 655 |
| **Prata** | Bronze + retracao de 2+ candles + **nao** exaustao | 248 |
| **Ouro** | Prata + pavio total do candle de continuacao entre 25 e 90 pontos | 173 |

**Veto de exaustao:** descarta quando as duas coisas valem ao mesmo tempo
-- a Hull esta abrindo a curva a favor do trade (segunda derivada positiva
numa compra) **e** o fechamento esta a mais de 0,45 ATR da EMA 21. Ver
RESULTADOS.md secao 2 para a tabela 2x2 que sustenta isso.

---

## 4. Execucao

### Tres modos de entrada, todos sem olhar o futuro

O CLAUDE.md pede duas alternativas -- "no meio do corpo" ou "no
fechamento". "No meio do corpo" e ambiguo, e as duas leituras nao custam a
mesma coisa, entao foram medidas as duas:

| Modo | O que e | Preenchimento |
|:---|:---|---:|
| `fecha` | a mercado no fechamento do candle de continuacao | 100% |
| `meio_lim` | ordem **limitada** no meio do corpo, colocada **depois** que ele fecha, valida por 1 barra | 65% |
| `antecipa` | ordem **stop** no meio do corpo, colocada assim que a **retracao** fecha | 64% |

> **Armadilha evitada.** A versao ingenua do `antecipa` -- pegar os 655
> sinais confirmados e so trocar o preco de entrada pelo meio do corpo --
> mede fator de lucro 3,8 e e **falsa**. Ela so antecipa em candles que ja
> se sabe que fecharam a favor, e por isso nunca e stopada na barra de
> entrada. O `antecipa` de verdade tem um **conjunto proprio de sinais**,
> gerado com `sinais(d, antecipado=True)` e avaliado no fechamento da
> retracao, com o que existia naquele momento. Ele entra tambem nos
> candles que sobem 50 pontos e desabam -- que e exatamente o custo de
> antecipar.

No modo `antecipa` o nivel **Ouro nao existe**: ele depende da forma do
candle de continuacao, que na hora da decisao ainda nao terminou de se
formar. O teto la e o Prata, e no grafico trade a trade o botao Ouro
aparece desligado nesse modo.

Foi testado se a geometria do candle da **retracao** -- essa sim conhecida
no momento da ordem -- serviria de substituta. Nao serve: as faixas nao
ficam em ordem (25-45 mede +27,7, a seguinte +4,5, a seguinte +46,7) e o
primeiro terco do periodo zera. E ruido com cara de filtro, exatamente o
que o resto deste estudo recusa.

### Caminho dentro do candle

So existe OHLC, entao a ordem em que os extremos foram visitados e uma
**convencao**, escolhida do lado conservador e coerente com a construcao
do PI: o pavio **contra** o sentido do candle se forma antes.

```
candle de alta:   abertura -> minima -> maxima -> fechamento
candle de baixa:  abertura -> maxima -> minima -> fechamento
```

Num candle que encosta no stop e no alvo, e isso que decide qual vale.

Na entrada antecipada, a ordem stop dispara **dentro** da barra: se o
candle fechou a favor, o pavio contra ja passou antes da entrada e so
sobra `maxima -> fechamento`; se fechou contra, o resto do caminho vem por
cima e o trade toma o stop na propria barra.

### Gestao

Tres gestoes sao medidas lado a lado, todas sobre o mesmo conjunto de
sinais:

| Nome | Stop | Alvo | Parcial |
|:---|---:|---:|:---|
| `parcial` | 100 | 300 (1:3) | 50% em +100, stop do restante na media |
| `puro` | 100 | 300 (1:3) | nenhuma |
| `r2` | 100 | 200 (1:2) | nenhuma |

- **Timeout** de 120 candles; zera no ultimo candle do pregao.
- **Uma posicao por vez** -- sinal que aparece com posicao aberta e
  descartado.

> **Sobre "levar o stop para a media da operacao".** Com meia posicao e a
> parcial na **mesma distancia** do stop, o preco em que o lucro ja
> realizado cancela exatamente a perda do restante *e* o stop inicial. O
> stop, portanto, **nao anda**. O que muda e que so metade da posicao
> ainda corre risco. Por isso o desfecho "zero a zero" aqui vale zero de
> verdade -- e nao, como e comum em backteste, um ganho de +50 disfarcado
> de empate. A alternativa otimista (stop no preco de entrada) esta
> implementada em `STOP_APOS_PARCIAL = 'entrada'` e existe so para
> reproduzir esse numero mais generoso quando se quiser compara-lo.

> **Sobre o 1:2 (`r2`).** Alvo em pontos nao quer dizer nada sem o stop
> ao lado, entao a comparacao e feita na **diagonal**: o mesmo alvo
> relativo em oito tamanhos de stop, de 50 a 300 pontos, e a metrica que
> compara linhas diferentes e o resultado **por ponto de risco**. O 1:2
> mede positivo em todas as linhas, mas ao mesmo stop entrega perto da
> metade da expectativa do 1:3 e cobra rebaixamento maior; o que ele
> compra sao cinco pontos percentuais de acerto. Ver RESULTADOS.md secao 5.

### Custos

`CUSTO_PTS = 0` por padrao: todos os numeros publicados sao **brutos**. A
escala de sensibilidade a custo (0 a 20 pontos de ida e volta) esta em
RESULTADOS.md secao 6.

---

## 5. Como o resultado e apurado

1. `sinais()` gera os candidatos e mede os atributos.
2. `executa()` resolve **cada candidato isoladamente** -- inclusive os que
   se sobrepoem. Isso da o valor esperado limpo de cada tipo de sinal, que
   e o que permite comparar filtros sem o ruido de quem roubou a vaga de
   quem. **Todo estudo de filtro usa esta tabela.**
3. `carteira()` monta a sequencia real, uma posicao por vez, com o filtro
   ja escolhido. **Toda estatistica publicada e curva de capital sai
   daqui.**

Os dois numeros nao batem de proposito, e a diferenca e informativa: o
Ouro tem 173 sinais isolados e 170 trades na carteira -- quase nao ha
sobreposicao. O Bronze tem 655 e 569: 86 sinais foram engolidos por
posicoes ja abertas.

### Como a robustez foi testada

Com 26 pregoes nao da para fazer walk-forward de verdade. O que da:

- **Tercos do periodo.** Todo estudo de filtro publica o valor esperado
  quebrado em tres pedacos do periodo. Faixa que so paga num terco nao e
  filtro, e sorte -- e nao entrou em nenhum nivel.
- **Sensibilidade dos cortes.** Os cortes do Ouro e do Prata foram
  variados em volta do valor escolhido; todos ficam num **plato**, nao num
  pico. Um corte que so funciona no valor exato e um corte ajustado ao
  ruido.
- **Grade stop x alvo inteira.** 36 combinacoes, todas medidas. O
  resultado nao depende de ter acertado o stop e o alvo -- a grade inteira
  mede positivo.
- **Monte Carlo.** 4.000 reamostragens dos trades com reposicao. Responde
  "quanto disso foi a ordem de chegada". Nao responde se o padrao continua
  valendo depois.
- **Custo.** Escala de 0 a 20 pontos por operacao.

### A galeria de exemplos

`rodar.py:galeria()` escolhe seis exemplos de cada nivel para o relatorio.
A escolha e deliberadamente **desfavoravel a propaganda**: os exemplos sao
espalhados uniformemente pelo periodo e a funcao garante os dois lados
(compra e venda) e pelo menos um trade perdedor e um vencedor em cada
nivel. Com acerto de 36%, a maioria dos exemplos de qualquer nivel acaba
sendo de perda -- e e assim que tem de ser: uma galeria so de acertos
ensina a reconhecer sorte, nao padrao. Cada exemplo de Prata e de Bronze
vem rotulado com **qual filtro ele falhou**, que e a parte que ensina.

### A peneira de busca (`estudo_fluxo.py`)

Os tercos sao um teste duro, mas **nao bastam quando se olha muita coisa**.
Dezessete atributos em cinco cortes e dois sentidos sao 170 comparacoes; em
173 sinais Ouro, alguma passa nos tres tercos por acaso. Para o estudo de
agressao e forca de tendencia foi preciso um terceiro degrau:

- **Busca em ruido.** A busca inteira -- espaco fechado e declarado *antes*
  de olhar -- e repetida 400 vezes sobre versoes **embaralhadas** dos mesmos
  atributos. O embaralhamento preserva a distribuicao e destroi a ligacao
  com o resultado, entao tudo o que a busca achar ali e, por construcao,
  sorte. O p-valor e a fracao das rodadas em ruido que empatam ou superam o
  achado real.
- **Fora da amostra.** O corte e escolhido usando **so** os dois primeiros
  tercos e depois aplicado ao terceiro, que ele nunca viu.

Nenhum atributo novo passou. O melhor filtro real do Ouro mede t = +3,58; a
mesma busca em ruido acha t = +4,10 na **mediana**. E fora da amostra o
corte escolhido em T1+T2 entrega EV **negativo** em T3, contra +30 sem
filtro nenhum.

**Esforco x resultado.** A mesma peneira foi aplicada a familia de Wyckoff
adaptada ao PI. As tres razoes de esforco **do par** (volume, negocios e
agressao da continuacao sobre os da retracao) sao informacao genuinamente
nova -- correlacao abaixo de 0,05 em modulo com pavio, volume e duracao. A
formulacao mais fiel, "a continuacao custou menos volume que a retracao",
da +15,9 pontos no Ouro e e positiva nos tres tercos. Ainda assim nao
entrou, por tres motivos somados:

- **nao ha monotonicidade.** A correlacao de posto entre esforco e
  resultado e -0,073 (p = 0,18, unicaudal no sentido esperado). A tese
  exige uma relacao; nao ha.
- **o quintil de MENOR esforco e o segundo pior** (+28,6 contra base de
  +34,1). Se menos esforco fosse melhor, ele seria o melhor. Quem carrega
  o corte binario e o segundo quintil, sozinho.
- **o ganho esta abaixo do detectavel.** Um filtro que mantem 42% dos
  sinais so seria visivel acima de 33 pontos; este alega 16.

**Poder.** O contraponto honesto: com 173 sinais e desvio de ~131 pontos por
trade, um filtro que corte dois tercos dos sinais so seria detectavel se
valesse **mais de 40 pontos por trade** -- mais que o proprio salto de
Bronze para Ouro. O resultado negativo mede o tamanho da base, nao a
inutilidade do fluxo.

### O teste que mais importou

Empilhar os quatro melhores filtros ao mesmo tempo deixa **16 sinais** e
valor esperado **negativo**. E o motivo de os niveis usarem tres filtros e
nao os oito que mediram alguma coisa: a partir de certo ponto, cada corte
so esta escolhendo ruido.

---

## 6. Os arquivos

| Arquivo | O que faz |
|:---|:---|
| `engine.py` | carga, indicadores, geracao de sinais, simulacao, estatisticas |
| `estrategia.py` | os filtros e a classificacao Ouro / Prata / Bronze |
| `fluxo.py` | anexa agressao, volume e duracao da barra a base principal |
| `features.py` | atributos de fluxo e de forca de tendencia, todos medidos ate a barra da decisao |
| `estudo_fluxo.py` | a peneira de busca: permutacao, fora-da-amostra e poder |
| `esforco.py` | esforco x resultado: o que o PI ja responde de graca e o que sobra para medir |
| `rodar.py` | roda tudo e escreve `saida/` |
| `relatorio.py` + `molde.py` | `relatorio.html` e `RESULTADOS.md`, incluindo a galeria de exemplos e o grafico trade a trade com filtros |
| `plano.py` + `molde_plano.py` | `plano.html` e `PLANO.md` |
| `resultados_md.py` | o texto do RESULTADOS.md |
| `vendor/` | klinecharts 9.8.10, embutido no html |
| `ntsl/MomentumPI_OuroPrata.ntsl` | o mesmo gatilho em NTSL, para o ProfitChart |
| `ntsl/valida_ntsl.py` | transcreve o NTSL de volta para Python e confere barra a barra contra a engine |

```
python rodar.py && python relatorio.py && python plano.py
python ntsl/valida_ntsl.py          # confere o indicador contra a engine
```

## 7. O indicador NTSL

`ntsl/MomentumPI_OuroPrata.ntsl` marca na tela do ProfitChart os mesmos
sinais que a engine classifica como **Ouro** e **Prata** -- seta abaixo da
minima na compra, acima da maxima na venda, ambar para Ouro e prata para
Prata. O Bronze nao recebe seta.

`ntsl/valida_ntsl.py` transcreve o `.ntsl` de volta para Python, linha a
linha e com os mesmos `[p+j]`, e compara barra a barra com
`estrategia.anota()`. O resultado atual: **248 barras marcadas nos dois,
173 Ouro e 75 Prata, zero divergencia de conjunto e zero de nivel**, e o
modo `Defasar(1)` marca exatamente as mesmas barras.

Duas diferencas propositais em relacao a engine, as duas documentadas no
cabecalho do proprio `.ntsl`:

- **A contagem da retracao para no fim do pregao.** A engine conta
  corridas sem olhar a virada de dia; o indicador para. Na base atual
  isso nao muda nenhum sinal, mas e o comportamento correto ao vivo.
- **O indicador e um trigger, nao um simulador.** Ele marca toda barra
  que cumpre a regra; o backteste opera uma posicao por vez e descarta o
  sinal que aparece com posicao aberta. Por isso 173 sinais Ouro viram
  170 trades -- na tela aparecem mais setas do que o backteste operou.

`Diagnostico(1)` existe porque a primeira versao do arquivo saiu **muda**
no ProfitChart. Duas construcoes compilavam e devolviam lixo em silencio,
as duas agora trocadas pelo idioma comprovado no acervo de indicadores:
guardar `h := HullMovingAverage(n)` e ler `h[1]` (o acervo chama a funcao
uma vez por deslocamento) e por `atrV > 0` no mesmo portao que
`CurrentBar`, o que fazia um ATR zerado apagar o indicador inteiro em vez
de so degradar um filtro. O modo de diagnostico plota um ponto em toda
barra e, nas barras que formam par, o numero do ultimo filtro que passou
-- uma tela responde onde a regra para, inclusive o caso mais comum de
todos, que e o indicador ter sido inserido num painel proprio em vez do
painel de precos.

A repintura esta tratada por parametro: `Defasar(0)` poe a seta na
propria barra do gatilho (que e onde ela serve) ao custo de a
classificacao so se firmar quando a barra fecha -- num grafico PI o lado
da barra e o pavio so sao definitivos no fechamento. `Defasar(1)` le a
barra `[1]` e nunca repinta, em troca de a seta sair uma barra a
frente.
