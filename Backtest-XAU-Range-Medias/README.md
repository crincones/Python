# Backtest — médias + Esforço × Resultado em XAUUSD, range de 388 ticks

Backtest da ideia de **seguir a tendência** num gráfico de range: as médias de
21, 42 e 72 em leque ordenado e aberto definem o contexto, o indicador
[`Trigger_EsforcoResultado_Range.mq5`](../../MQL5/MQL5/Indicators/Triggers/Trigger_EsforcoResultado_Range.mq5)
dá o momento de entrar, e a gestão é sempre **1:2** — nas três formas pedidas.

Duas famílias de média foram avaliadas (**exponencial** e **Hull**), e o
indicador foi portado linha a linha para Python em `engine.py`.

## Comece por aqui

| documento | o que é |
|---|---|
| **[`relatorio.html`](relatorio.html)** | o relatório completo, com o navegador de **operação a operação** — candles, as três médias da variante escolhida, e embaixo o painel de esforço e delta. Abre com dois cliques, sem internet e sem servidor. |
| **[`RESULTADOS.md`](RESULTADOS.md)** | o mesmo conteúdo em texto, para ler no editor ou no GitHub. |
| **[`PLANO.md`](PLANO.md)** · [`plano.html`](plano.html) | o plano de operação manual que sai das conclusões. |

## O que o backtest concluiu, em quatro linhas

1. **A EMA vence a Hull.** Comparando par a par — mesma largura de leque,
   mesma gestão, mesmo stop — a EMA vence em **69 dos 80 pares** do grid. A
   Hull vira antes e, por isso mesmo, troca de lado **1.367 vezes contra 422**
   da EMA no mesmo histórico: a tendência que ela enxerga dura 11 barras, a da
   EMA dura 38. Cada troca a mais é uma tendência que ela declarou e desfez.
   É a conclusão mais sólida do estudo.
2. **O leque ajuda, e ajuda progressivamente.** Sem contexto de médias:
   +0,062 R por operação. Com o leque ordenado: +0,097 R. Com o leque ordenado
   *e* aberto: +0,133 R. Cada exigência acrescenta, na ordem esperada.
3. **Das três gestões pedidas, duas não são mensuráveis neste gráfico** — e
   são justamente as que dão os melhores números. Ver abaixo.
4. **A configuração campeã não valida fora da amostra.** Escolhendo a melhor
   das 96 configurações mensuráveis numa metade do histórico e medindo na
   outra, o resultado cai de +0,320 R para **+0,035 R**.

E a limitação mais séria: **o resultado vive no último terço do histórico**.
Os dois primeiros terços rendem +0,075 R e +0,053 R — indistinguíveis de zero.

## As três gestões, e por que duas delas não dão para medir

Todas com risco:retorno de 1:2. Chamando S a distância do stop:

| modo | o que faz | desfechos | mensurável? |
|---|---|---|---|
| `fixo` | stop em −S, alvo em +2S, nada se move | −1R ou +2R | **sim** |
| `parcial` | a +S vende 50% e leva o stop para a **entrada** | −1R, +0,5R, +1,5R | não |
| `parcial_op` | a +S vende 50% e o stop **fica onde está** | −1R, 0, +1,5R | **sim** |
| `breakeven` | a +S o stop vai para a **entrada**, sem parcial | −1R, 0, +2R | não |

**Por que existem dois modos com parcial.** "Parcial que ativa o breakeven na
média da operação" admite duas leituras, e a diferença é aritmética. Com
metade realizada em +S, o resultado da operação inteira num stop em −S é

```
0,5 × (+S)  +  0,5 × (−S)  =  0
```

ou seja: **o breakeven da operação já está no stop inicial** — não é preciso
mexer em nada. Levar o stop para a entrada não é breakeven, é travar +0,5R.
Os dois estão implementados porque a diferença é material.

**Por que dois modos não são mensuráveis.** A entrada é o fechamento da barra
de sinal, então a barra seguinte abre exatamente no preço de entrada. Quando
ela sobe 1R, qualquer pavio contrário faz o preço "voltar ao breakeven" no
papel — e como a barra de range percorre 388 ticks garantidos, isso acontece
em praticamente toda barra que arma o gatilho. O arquivo não diz se a mínima
veio antes ou depois do toque em 1R. O intervalo do `breakeven` puro vai de
−0,444 R a +0,253 R: mais largo que o próprio resultado.

## A regra geométrica que o gráfico de range oferece

A barra percorre **no máximo 388 ticks**, então não consegue tocar dois níveis
separados por mais que isso. Como stop e alvo distam `S + 2S = 3S`, o
resultado deixa de depender de qualquer convenção exatamente a partir de

```
S > range / 3 = 129,3 ticks
```

Medido no arquivo: a largura do intervalo cai de 0,245 R em S=120 para
**exatamente zero** em S=130. A previsão e a régua batem. E com stop acima de
um range inteiro (450 ticks) até os modos com breakeven ficam mensuráveis — só
que aí a vantagem já evaporou.

## Como reproduzir

```
python rodar.py           # roda tudo e grava saida/
python resultados_md.py   # escreve RESULTADOS.md
python relatorio.py       # escreve relatorio.html
python plano.py           # escreve PLANO.md e plano.html
```

Leva cerca de dois minutos. Requer `pandas` e `numpy`; nada além disso.

## Os arquivos

```
XAUUSD-388N/         o histórico usado (CSV exportado do MetaTrader)

engine.py            o porte do indicador, as médias (EMA e Hull), os quatro
                     modos de gestão, a simulação e as estatísticas
rodar.py             executa tudo e grava saida/resumo.json
resultados_md.py     resumo.json -> RESULTADOS.md
relatorio.py         resumo.json + barras.json -> relatorio.html
plano.py             resumo.json -> PLANO.md e plano.html

saida/resumo.json    TODOS os números do estudo, num arquivo só
saida/barras.json    OHLC + agressão comprimidos, para os gráficos
saida/trades_V*.csv  operação a operação, de cada variante
saida/console.txt    o que rodar.py imprimiu na última execução
```

**`saida/resumo.json` é a única fonte de números.** Os quatro documentos leem
dele; nenhum valor é digitado à mão em documento nenhum.

## As variantes publicadas

| | |
|---|---|
| **V0** | só o gatilho, sem contexto de médias — a linha de base |
| **V1** | EMA em leque ordenado |
| **V2** | EMA em leque aberto (≥400 t), gestão fixa — **a recomendada** |
| **V3** | EMA + parcial 50% com stop na entrada |
| **V4** | EMA + parcial 50% com breakeven da operação |
| **V5** | EMA + breakeven na entrada em 1R, sem parcial |
| **V6** | Hull em leque ordenado |
| **V7** | Hull em leque aberto (≥400 t) — a comparação direta com a V2 |
| **V8** | Hull + breakeven em 1R |
| **V9** | EMA + o filtro de esforço que sobreviveu ao estudo anterior |
| **V10** | controle estatístico: o mesmo gatilho operado do lado oposto |

Cada uma é medida também no piso e no teto da ambiguidade dentro da barra, com
custo de 10, 20 e 40 ticks, e em cada metade da amostra separadamente. O
relatório traz acerto, payoff, fator de lucro, fator de recuperação,
rebaixamento (em R e em operações), sequência máxima de ganhos e de perdas,
SQN e desvio.

## Decisões de método que valem conhecer

- **O grid inteiro é publicado** — 160 configurações, com o `z` e a largura do
  intervalo de cada uma —, para que o melhor número seja lido como o máximo de
  160 tentativas e não como uma descoberta.
- **A escolha é feita fora da amostra.** Escolher na metade A e medir na
  metade B é o único jeito honesto de estimar o que esperar de uma busca em
  grid. Aqui, isso reprovou a busca.
- **Os controles são publicados**: lado invertido, sem leque, contra o leque, e
  direção sorteada nas mesmas barras com a mesma gestão. O último mostra que a
  gestão 1:2 sozinha não gera vantagem nenhuma.
- **A comparação EMA × Hull é pareada**, não entre campeões. Comparar dois
  máximos compararia sorte; o pareamento compara a família.
- **A premissa do indicador é conferida antes de tudo** — range constante e a
  convenção de agressão do símbolo sintético.
- **Custo.** A coluna `<SPREAD>` do arquivo traz valores impossíveis e foi
  descartada. O custo entra como cenário explícito, nunca embutido.
- **Uma operação por vez.** Sinais que aparecem com posição aberta são
  descartados, como aconteceria na mesa.

## Relação com os outros estudos desta pasta

Este é o terceiro estudo sobre o mesmo gatilho e o mesmo gráfico:

- `Backtest-XAU-continua1` — leque de EMAs em gráfico de 521 ticks, sem o
  indicador de esforço.
- `Backtest-XAU-continua1-Range` — o indicador de esforço sozinho, em 1:1 a
  meio range. Achou que a vantagem do gatilho **vive uma barra**.
- **este** — o indicador com contexto de médias e alvo de 2R, que é justamente
  a tentativa de esticar aquela vantagem para além de uma barra. O contexto
  ajuda; o alcance continua sendo o limite.
