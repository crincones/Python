# Backtest-Rincones1XAUUSD

Backtest do setup de esforço no **XAUUSD**, sobre barras de **521 ticks**
(68.286 barras, 85 pregões, maio a agosto/2026).

É o porte de [`Backtest-Rincones1`](../Backtest-Rincones1) (WIN, 10.000 ticks)
para o ouro. O gatilho vem do índice de esforço de
`MQL5/Indicators/Ticks/Ticks_Esforco_v2.mqh`, reimplementado aqui idêntico.

> **O porte não é uma recalibração.** Quatro peças tiveram de mudar, e **três
> delas mudam o sinal do resultado, não o tamanho**: o eixo do índice, a
> geometria de rejeição e a regra de entrada. Rodar a configuração do WIN no
> ouro mede **negativo**. Cada troca está medida com todo o resto congelado na
> § 2 de [RESULTADOS.md](RESULTADOS.md).

## Conteúdo

| Arquivo | O que é |
|---|---|
| **[PLANO.md](PLANO.md)** · **[plano.html](plano.html)** | **O plano operacional manual.** O que fazer na frente da tela, os limites do dia e o cartão de pregão. **Gerado.** |
| [ESTRATEGIA.md](ESTRATEGIA.md) | Especificação formal: gatilho, eixos, geometria, setups, execução e gestão. É o contrato que a engine implementa. **Escrito à mão.** |
| **[relatorio.html](relatorio.html)** | **O relatório.** Resultados, as quatro trocas do porte, grades de stop/alvo, estabilidade do corte, curvas de capital e o **visualizador de trades** — tudo num arquivo só. Abra no navegador. |
| [RESULTADOS.md](RESULTADOS.md) | Os mesmos números em markdown. **Gerado** — não edite à mão. |
| `engine.py` | Motor: carga, indicador de esforço, as cinco médias de regime, os setups, simulação de trade, métricas. |
| `rodar.py` | Roda tudo e grava `saida/`. |
| `relatorio.py` + `molde.py` + `resultados_md.py` | Geram `relatorio.html` e `RESULTADOS.md` a partir de `saida/resumo.json`. |
| `plano.py` + `molde_plano.py` | Geram `PLANO.md` e `plano.html` — do mesmo `resumo.json`, e o HTML sai do próprio markdown. |
| `dados/` | O CSV exportado do MT5 do símbolo sintético de 521 ticks. |
| `saida/` | `resumo.json` (fonte única dos números), `console.txt` e `trades_*.csv`. |

## Como rodar

```bash
python rodar.py       # mede tudo -> saida/resumo.json   (~50 s)
python relatorio.py   # gera relatorio.html e RESULTADOS.md
python plano.py       # gera PLANO.md e plano.html
```

Requer `numpy` e `pandas`. Tudo é configurável no topo de `engine.py` — mexeu
ali, rode os três de novo.

> **Nenhum número é escrito à mão nos documentos**, e nem as frases de
> conclusão: relatório, markdown e plano saem todos de `saida/resumo.json`.

## As três "bases"

`COMPLETO`, `METADE_1` e `METADE_2` **não são três instrumentos**: são a amostra
inteira e as duas metades cronológicas dela, cortadas por pregão.

No projeto do WIN havia dois contratos independentes e a concordância entre eles
era evidência de verdade. Aqui há um histórico só, e a concordância entre as
metades é só evidência de que o resultado não vem de um pedaço do período. **É
mais fraco**, e todo documento gerado repete isso onde o número aparece.

## O que mudou do WIN

| | WIN · 10.000 ticks | XAUUSD · 521 ticks |
|---|---|---|
| eixos do índice | `[E1]+[E2]+[E3]` | `[E4]` range sozinho |
| direção lida | delta (flags da B3) | candle |
| geometria de rejeição | clássica | **invertida** |
| entrada | limitada no meio do candle | **a mercado no fechamento** |
| filtro de regime | setups A e B | **nenhum** |
| stop / alvo | 150 / 300 pontos | 7,00 / 10,50 USD |

## As respostas

> As frases de conclusão do relatório e do markdown são **calculadas** a partir
> de `saida/resumo.json`. As de baixo são o resumo desta rodada; se a engine
> mudar, valem as dos documentos gerados, não estas.

1. **O ativo não publica `[E1]`.** O XAUUSD é CFD: o gerador conta 1 lote por
   tick e a agressão total muda em só 0,37% das barras. A engine detecta eixo
   sem variação e o tira da soma — sem isso o índice ficaria preso abaixo de
   0,667 e o gatilho nunca acenderia.
2. **O índice do ouro é de um eixo só, e é o `[E4]` range.** Ele mede `+1,202`
   USD por trade contra `+0,507` do índice de três eixos. Somar eixos aqui
   dilui: o corte deixa de selecionar a barra de range extremo, que é a única
   coisa que este ativo publica com sinal.
3. **A geometria de rejeição está invertida.** A regra do WIN (corpo do lado da
   rejeição clássica) mede `−0,075`; o lado oposto mede `+1,202`. É a terceira
   vez que a mesma inversão aparece neste ativo — `Delta_Fraqueza.mqh` e o
   `[D4]` de `Ticks_Esforco_v2.mqh` já a tinham registrado por barra, e agora
   ela aparece no nível do trade.
4. **A entrada limitada não sobrevive à inversão, e é o erro mais caro
   possível.** Com o corpo em cima, o meio do candle fica abaixo do fechamento e
   a venda limitada ali vira meio range de desconto — que preenche quase sempre.
   A regra tira `−1,85` USD por trade e vira o resultado de positivo para
   negativo. **A entrada aqui é a mercado.**
5. **A troca do eixo `[E2]` (v1 → vaivém) vale aqui também.** No índice de três
   eixos ela vai de `+0,017` para `+0,507`, e — o que importa mais — as duas
   metades saem de discordar de sinal para concordar.
6. **O filtro de regime subtrai.** A carteira que pega todo gatilho mede
   `+1,202`; só A mede `+0,539`, A+B mede `+0,837`, A+B+C mede `+0,806`. No
   ouro a barra de range extremo com o pavio do lado certo já carrega o sinal
   inteiro.
7. **O stop tem de caber FORA da barra do gatilho.** O equivalente escalado do
   WIN (3,50 ≈ 1,17 range médio) mede positivo mas fraco; 7,00 ≈ 2,35 ranges
   mede o dobro. A barra do gatilho é uma barra de range extremo por
   construção — um stop pequeno é acionado pelo ruído da própria barra que gerou
   o sinal.

Resultado da configuração padrão, **bruto**: `+1,202` USD por trade, `t +3,89`,
571 trades em 85 pregões, PF 1,42, rebaixamento máximo 73,6 USD por onça.
Positivo nas duas metades (`+0,993` e `+1,404`). Com 0,20 USD de custo por
trade cai para `+1,002` e continua de pé.

Leia a § 12 de [RESULTADOS.md](RESULTADOS.md) antes de dimensionar posição — a
amostra é **uma**, o período é de quatro meses, e o corte do gatilho saiu de uma
varredura sobre esta mesma amostra.

## O visualizador

Está dentro do relatório, na seção 15. Navega **trade a trade** (setas ← →, ou
clique na lista): candles do pregão, as três EMAs, linhas de entrada, stop,
parcial e alvo, marcas do gatilho e da saída, o índice de esforço embaixo com a
linha de corte, e ficha com desfecho e USD por lote. Filtros por stop (7,00 ou
3,50 — os sinais são os mesmos, muda onde o trade morre), por regime (A/B/C/L) e
por desfecho.
