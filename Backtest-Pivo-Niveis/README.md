# Backtest-Pivo-Niveis

Estudo de uma hipótese de leitura de tela no WIN, sobre barras de **10.000 ticks**
(WINFUT e WINV26, abr–ago/2026):

> *Barras grandes que pivotam ao redor das médias, da VWAP ou dos pontos de pivô
> costumam **andar**, ou ser **pontos de reversão** relativamente confiáveis.*

São **duas** afirmações, e elas foram medidas separadamente — sempre contra
controle, porque sem controle o que se mede é "barra grande", não "barra grande
no nível".

## A resposta, em uma linha

**"Andar" é falso** — a continuação fica abaixo de 50% nas quatro medidas.
**"Reverter" tem alguma coisa**, mas quem reverte é a barra que **falha** (o preço
rompe o extremo oposto ao corpo dela), e **o nível não é o que qualifica**: exigir
que a barra alcance uma média, a VWAP ou um pivô *piora* o resultado nas duas
bases. O melhor arranjo não chega a `t = 2` e **não passa** como setup.

Os números, os vereditos calculados e os trades um a um estão em
**[relatorio.html](relatorio.html)**.

## Conteúdo

| Arquivo | O que é |
|---|---|
| **[relatorio.html](relatorio.html)** | **O relatório.** A medida, o controle, as duas metades da hipótese, o peso do acaso e o **visualizador de trades** — candles interativos com as médias, a VWAP e os pivôs do dia desenhados. Arquivo único, com a biblioteca do gráfico embutida: abre offline. |
| `nucleo.py` | Carga, níveis de referência, geometria da barra, a corrida simétrica e a simulação de trade. |
| `estudo.py` | Roda a grade inteira e grava `saida/resumo.json`. |
| `relatorio.py` + `molde.py` | Geram `relatorio.html` a partir de `saida/resumo.json`. |
| `vendor/` | [KLineCharts](https://klinecharts.com) 9.8.10 (Apache 2.0), embutido no HTML pelo `relatorio.py`. Não vai a CDN. |
| `dados/` | Os dois CSV de 10.000 ticks exportados do Profit. |
| `saida/` | `resumo.json` (fonte única dos números) e `trades_*.csv`. |

## Como rodar

```bash
python estudo.py      # mede tudo -> saida/resumo.json
python relatorio.py   # gera relatorio.html
```

Requer `numpy`, `pandas` e `scipy`. Os parâmetros da grade estão no topo de
`estudo.py`; os do gatilho e da gestão, no topo de `nucleo.py`.

> **Nenhum número é escrito à mão no relatório** — nem os números, nem as frases
> de veredito. As duas coisas são calculadas a partir de `saida/resumo.json`. Se a
> medida mudar de sinal, o texto muda junto.

## Como a hipótese foi medida

**Barra grande** é `range ≥ 1,50 × range médio de 20 barras` — grande *para o
momento*, e não um número fixo de pontos, para o corte acompanhar a volatilidade.

**Os níveis** são EMA 21/42/72, a **VWAP** ancorada na abertura do pregão, os
**pontos de pivô** clássicos (PP, R1, S1, R2, S2) e as **pontas do dia anterior**.
Todos causais: os pivôs e as pontas saem do pregão *anterior* inteiro; médias e
VWAP usam só o que já aconteceu.

**A medida** é uma corrida simétrica `±150` pontos a partir do preço de entrada: o
que chegar primeiro decide, e stop ganha o empate dentro da barra. Simétrica de
propósito — alvo assimétrico, parcial e breakeven inventam vantagem sozinhos, e aí
se mede a gestão, não a ideia. Em barra sem informação isso dá **50%**, e é contra
esse 50% que tudo é lido.

**O controle** aparece em três camadas: todas as barras do período, as barras
grandes sem olhar nível, e as barras grandes **sem nível nenhum** dentro. É a
terceira que responde à pergunta de verdade.

## O que este estudo fecha

A pergunta *"filtrar barra grande por média, VWAP ou pivô melhora alguma coisa?"*
está respondida: **não** — em ~2.000 células, nas duas bases, com o toque literal
e com folga de um quarto de range, com o nível centrado ou não, com um nível ou
com confluência de dois ou mais.

O motivo é geométrico, e o relatório o desenha: com três EMAs, a VWAP, cinco pivôs
e as pontas do dia anterior, **algum** nível cai dentro de quase toda barra grande.
O nível não seleciona nada porque quase nunca está ausente.

## O que fica em aberto

1. Medir a **falha da barra grande** com mais período — é o que falta para o `t`
   decidir; 44 pregões não bastam.
2. Trocar o stop fixo por um **proporcional ao tamanho da barra**: a barra grande
   define a estrutura, e 150 pontos é arbitrário em cima dela.
3. Checar se isso não é o **setup B do [Backtest-Rincones1](../Backtest-Rincones1)**
   com outra roupa — os dois pedem exaustão depois de um movimento rápido, e se
   forem o mesmo trade não somam.
