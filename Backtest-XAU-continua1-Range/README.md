# Backtest — Esforço × Resultado em XAUUSD, gráfico de range de 388 ticks

Backtest documentado do indicador
[`Trigger_EsforcoResultado_Range.mq5`](../../MQL5/MQL5/Indicators/Triggers/Trigger_EsforcoResultado_Range.mq5)
descrito em [`ESTRATEGIA.md`](ESTRATEGIA.md): num gráfico onde o range é fixo,
o corpo da barra é o **resultado líquido** e a agressão somada é o **esforço**.
Quando uma barra vira o movimento andando menos que o normal e com menos
agressão a favor que o normal, alguém do lado passivo venceu — e o indicador
marca a barra com uma seta.

O indicador foi **portado linha a linha para Python** em `engine.py`, com os
mesmos nomes de variável do `OnCalculate`, para que a conferência entre os dois
seja possível a olho.

## Comece por aqui

| documento | o que é |
|---|---|
| **[`relatorio.html`](relatorio.html)** | o relatório completo, com o navegador de **operação a operação** em candles e o **painel de agressão** embaixo — que é o que o indicador realmente lê. Trocável entre as variantes, com glossário de todos os termos. Abre com dois cliques, não precisa de internet nem de servidor. |
| **[`RESULTADOS.md`](RESULTADOS.md)** | o mesmo conteúdo em texto, para ler no editor ou no GitHub. |
| **[`PLANO.md`](PLANO.md)** · [`plano.html`](plano.html) | o plano de operação manual que sai das conclusões. Inclui o patch de MQL5 que falta no indicador (§2). |

## O que o backtest concluiu, em quatro linhas

1. O gatilho **tem** leitura de direção — mas ela vive por **uma barra** e
   morre depois. Medida em 5, 20 ou 40 barras, ela some por completo; medida em
   meio range, aparece.
2. **Este gráfico já vem inclinado.** 51,45% das barras de range continuam na
   própria direção na barra seguinte (z = +5,73). Parte de todo acerto acima de
   50% não é mérito do indicador, e o estudo desconta isso explicitamente.
3. Descontado o que é do gráfico, **o indicador acrescenta +6,4 pontos** sobre
   um controle emparelhado, com z = +2,97. A configuração recomendada mede
   **58,0% de acerto** em 562 operações.
4. De 30 filtros testados, **um só sobreviveu**: esforço total da barra abaixo
   de 80% do normal da direção. Ele passou em platô, nas duas metades, nos três
   terços e no controle invertido. O filtro de horário, que a estratégia pedia,
   **foi reprovado**.

E a ressalva que anda junto: **+31,1 ticks de expectativa não sobrevivem a 40
ticks de custo.** A margem cabe dentro de um spread ruim.

Os números estão em `RESULTADOS.md` § 1 e no `relatorio.html` § 1.

## A descoberta de método que vale para qualquer estudo de range

Todo backtest feito sobre OHLC tem um ponto cego: quando a barra toca alvo *e*
stop, o arquivo não diz qual veio primeiro. Normalmente se resolve por
convenção.

**Num gráfico de range dá para eliminar o problema.** Como `High−Low` é 388
ticks por construção, uma barra não consegue percorrer 194 para cima *e* 194
para baixo a partir do próprio open — os dois lados somados dariam o range
inteiro. Medido neste arquivo: acontece em **0,03% das barras**.

Com stop e alvo a meio range, portanto, as hipóteses pessimista e otimista
devolvem *o mesmo número*. É por isso que a métrica central do estudo é essa, e
por isso as colunas "pessimista" e "otimista" das variantes V7 e V8 são
idênticas. Ver `RESULTADOS.md` §3.1.

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
ESTRATEGIA.md        a estratégia como foi descrita, e as tarefas pedidas
XAUUSD-388N/         o histórico usado (CSV exportado do MetaTrader)

engine.py            o porte do indicador para Python, a detecção de sinal,
                     a simulação das operações e as estatísticas
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
dele; nenhum valor é digitado à mão em documento nenhum. Mudar um parâmetro em
`rodar.py` e reexecutar a sequência atualiza tudo de uma vez, sem risco de um
relatório ficar defasado em relação ao outro.

## As variantes publicadas

| | |
|---|---|
| **V0** | a leitura literal: todo sinal, stop de um range, parcial em 1R, alvo em 3R |
| **V1** | só absorção (o sinal verde/vermelho) |
| **V2** | só divergência no pivô (o sinal azul) |
| **V3** | entrada limitada no meio do range da barra de sinal |
| **V4** | gestão 1:1 em um range — a métrica neutra de direção |
| **V5** | só nas horas selecionadas — publicada para mostrar que **não** valida |
| **V6** | + esforço abaixo de 80% do normal, gestão 1:1 em um range |
| **V7** | **meio range**, todos os sinais — a medida sem ambiguidade |
| **V8** | meio range + esforço baixo — a que mediu melhor, e a que o plano adota |
| **V9** | controle estatístico: o mesmo gatilho operado do lado oposto |

Cada uma é medida também na hipótese otimista de ambiguidade dentro da barra,
com custo de 10, 20 e 40 ticks, e em cada metade da amostra separadamente.

## Decisões de método que valem conhecer

- **A premissa é conferida antes de tudo.** O indicador pressupõe range
  constante e a convenção de agressão do símbolo sintético. Aplicado onde elas
  não valem, ele não dá erro — desenha setas sem significado. `RESULTADOS.md`
  §2 publica as duas conferências.
- **A linha de base é publicada.** Antes de creditar qualquer acerto ao
  indicador, o estudo mede quanto o próprio gráfico já entrega. Sem esse
  controle, 58% pareceria todo mérito do gatilho.
- **Ordem limitada preenchida dentro da barra não ganha nada naquela barra.**
  O arquivo não diz em que instante a ordem foi preenchida; creditar o alvo
  pela máxima da mesma barra é ler o futuro, e neste gráfico produz um acerto
  de 99,8%. A tabela do §6 publica esse número marcado como artefato, para que
  o erro fique visível.
- **Os parâmetros do próprio indicador foram varridos.** Seis parâmetros, todos
  platôs — evidência de que o indicador não foi ajustado a este histórico.
- **Custo.** A coluna `<SPREAD>` do arquivo traz valores impossíveis e foi
  descartada. O custo entra como cenário explícito, nunca embutido.
- **Uma operação por vez.** Sinais que aparecem com posição aberta são
  descartados, como aconteceria na mesa.
- **A busca inteira é publicada**, com o `z` de cada tentativa, para que o
  melhor seja lido como o máximo de 30 tentativas — e não como uma descoberta.

## Uma coisa que falta no indicador

O filtro que decide o plano — o esforço relativo — **não é publicado por
nenhum buffer do `.mq5`**. Ele é derivável dos que existem, porque
`EsfRel = ResRel / Eficiência` (conferido: vale em 100% dos 1.782 sinais), mas
fazer essa divisão de cabeça no instante do sinal é pedir erro.

`PLANO.md` §2 traz o patch: a variável `esfRel` já existe e já está calculada
dentro do `OnCalculate`, só não é gravada em lugar nenhum. São nove linhas.
