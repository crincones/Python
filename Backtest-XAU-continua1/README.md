# Backtest — leque de EMAs em XAUUSD, gráfico de 521 ticks

Backtest documentado da estratégia descrita em [`ESTRATEGIA.md`](ESTRATEGIA.md):
médias exponenciais de 21, 42 e 72 em forma de leque, afastamento e volta do
preço ao leque, pullback de 2 ou 3 candles, candle contrário como gatilho,
ordem limitada no meio do range, stop de 300 ticks, parcial de 50% em 300 e
saída final em 900.

## Comece por aqui

| documento | o que é |
|---|---|
| **[`relatorio.html`](relatorio.html)** | o relatório completo, com o navegador de **operação a operação** em gráfico de candles, trocável entre as variantes, mais o glossário de todos os termos. Abre com dois cliques, não precisa de internet nem de servidor. |
| **[`RESULTADOS.md`](RESULTADOS.md)** | o mesmo conteúdo em texto, para ler no editor ou no GitHub. |
| **[`PLANO.md`](PLANO.md)** · [`plano.html`](plano.html) | o plano de operação manual que sai das conclusões. Mesmo conteúdo nos dois formatos. |

## O que o backtest concluiu, em três linhas

1. A regra como está escrita **perde dinheiro** neste histórico.
2. O motivo não é o alvo mal escolhido: o gatilho **não tem leitura de
   direção** — a excursão do preço depois da entrada é estatisticamente igual
   à de uma entrada sorteada.
3. De 31 filtros testados, **só o horário** sobreviveu a uma validação fora da
   amostra. Combinado com um gatilho mais exigente e um alvo curto, ele produz
   a única configuração que continua positiva depois de descontar custo — com
   uma margem que cabe dentro do spread.

Os números estão em `RESULTADOS.md` § 1 e no `relatorio.html` § 1.

## Como reproduzir

```
python rodar.py           # roda tudo e grava saida/
python resultados_md.py   # escreve RESULTADOS.md
python relatorio.py       # escreve relatorio.html
python plano.py           # escreve PLANO.md e plano.html
```

Leva menos de um minuto. Requer `pandas` e `numpy`; nada além disso.

## Os arquivos

```
ESTRATEGIA.md        a estratégia como foi descrita, e as tarefas pedidas
XAUUSD-521T/         o histórico usado (CSV exportado do MetaTrader)

engine.py            o motor: indicadores, detecção de gatilho, simulação
                     das operações e estatísticas. É onde a regra vira código.
rodar.py             executa tudo e grava saida/resumo.json
resultados_md.py     resumo.json -> RESULTADOS.md
relatorio.py         resumo.json + barras.json -> relatorio.html
plano.py             resumo.json -> PLANO.md e plano.html

saida/resumo.json    TODOS os números do estudo, num arquivo só
saida/barras.json    OHLC comprimido, usado pelos gráficos do relatório
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
| **V0** | a regra literal de `ESTRATEGIA.md` |
| **V1** | + leque aberto (médias não emboladas), quantificado em 400 ticks |
| **V2** | + teto de 350 ticks no range do candle de gatilho |
| **V3** | + o gatilho tem de fechar além da EMA21 |
| **V4** | + só nas horas validadas fora da amostra |
| **V5** | horário + reconquista, mantendo parcial e runner até 900 |
| **V6** | horário, com a posição inteira saindo em +1R |
| **V7** | horário + reconquista + saída inteira em +1R — a que mediu melhor, e a que o plano adota |
| **V8** | controle estatístico: o mesmo gatilho operado do lado oposto |

Cada uma é medida também na hipótese otimista de ambiguidade dentro da barra,
com custo de 10, 20 e 40 ticks, e em cada metade da amostra separadamente.

## Decisões de método que valem conhecer

- **Ambiguidade dentro da barra.** Quando uma barra toca alvo e stop, o OHLC
  não diz qual veio primeiro. Todos os números publicados assumem o **stop
  primeiro**; a hipótese oposta é publicada ao lado, como limite superior.
- **Custo.** A coluna `<SPREAD>` do arquivo traz valores impossíveis e foi
  descartada. O custo entra como cenário explícito, nunca embutido.
- **Uma operação por vez.** Sinais que aparecem com posição aberta são
  descartados, como aconteceria na mesa.
- **A busca inteira é publicada.** Os 31 filtros testados aparecem na tabela,
  com o `z` de cada um, para que o melhor possa ser lido como o máximo de 31
  tentativas — e não como uma descoberta.
