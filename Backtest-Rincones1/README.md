# Backtest-Rincones1

Backtest de **três setups de esforço filtrados por regime de média** no WIN, sobre barras de **10.000 ticks** (WINV26 e WINFUT, jun–ago/2026).

O gatilho é o índice de esforço já validado em `ProfitChart/Indicadores/Grafico-Ticks/Ticks_Esforco_Reversao.ntsl`; aqui ele é reimplementado idêntico e cruzado com uma média de regime para decidir se o trade vai a favor ou contra o movimento.

> **Esta rodada trocou o eixo E2 do gatilho.** Ele media `|delta| / |Close−Open|` — agressão por ponto de *saldo*, cego ao caminho que o preço fez dentro da barra. Agora mede **vaivém**: `(|delta|/esforço) × (1 − |Close−Open|/percurso)`, com `percurso = 2·(High−Low) − |Close−Open|`. A derivação está em `Ticks_Esforco_Hist_v2.ntsl` e o efeito no backtest, medido com todo o resto congelado, está na **§ 2 de [RESULTADOS.md](RESULTADOS.md)**. Para voltar à fórmula antiga: `METRICA_E2 = 0` em `engine.py`.

## Conteúdo

| Arquivo | O que é |
|---|---|
| **[PLANO.md](PLANO.md)** · **[plano.html](plano.html)** | **O plano operacional manual.** O que fazer na frente da tela, os limites do dia, a nota de aderência e o cartão de pregão. **Gerado.** |
| [ESTRATEGIA.md](ESTRATEGIA.md) | Especificação formal: gatilho, regimes, os três setups, execução e gestão. É o contrato que a engine implementa. |
| **[relatorio.html](relatorio.html)** | **O relatório.** Resultados, variantes de média, variante de stop, curvas de capital e o **visualizador de trades** — o gráfico de candles é interativo (zoom, arrasto e cruzamento) e carrega o pregão inteiro. Tudo num arquivo só, inclusive a biblioteca do gráfico: abre offline. |
| [RESULTADOS.md](RESULTADOS.md) | Os mesmos números em markdown. **Gerado** — não edite à mão. |
| `engine.py` | Motor: carga, indicador de esforço, as cinco médias de regime, os 3 setups, simulação de trade, métricas. |
| `rodar.py` | Roda tudo e grava `saida/`. |
| `relatorio.py` + `molde.py` + `resultados_md.py` | Geram `relatorio.html` e `RESULTADOS.md` a partir de `saida/resumo.json`. |
| `plano.py` + `molde_plano.py` | Geram `PLANO.md` e `plano.html` — do mesmo `resumo.json`, e o HTML sai do próprio markdown. |
| `vendor/` | [KLineCharts](https://klinecharts.com) 9.8.10 (Apache 2.0), embutido no HTML pelo `relatorio.py`. É a única dependência de front-end e não vai a CDN. |
| `dados/` | Os dois CSV de 10.000 ticks exportados do Profit. |
| `saida/` | `resumo.json` (fonte única dos números), `console.txt` e `trades_*.csv`. |

## Como rodar

```bash
python rodar.py       # mede tudo -> saida/resumo.json
python relatorio.py   # gera relatorio.html e RESULTADOS.md
python plano.py       # gera PLANO.md e plano.html
```

Requer `numpy` e `pandas`. Tudo é configurável no topo de `engine.py` — mexeu ali, rode os dois de novo.

> **Nenhum número é escrito à mão nos documentos.** Relatório e markdown saem os dois de `saida/resumo.json`. Foi assim que a versão anterior ficou defasada duas vezes quando a engine mudou.

## Os três setups

Mesmo gatilho (índice de esforço ≥ 0,80, corpo pequeno, eixo de deslocamento não dominante). O que muda é o **regime da média**:

- **A — tendência.** Média apontando para um lado, preço volta e a toca, gatilho a favor. **Prioritário** por EV e drawdown.
- **B — reversão rápida.** Fora de consolidação, preço a 1+ range médio da média, gatilho contra o afastamento.
- **C — reversão em consolidação.** Média sem inclinação, preço afastado. **Desligado: mede negativo nas duas bases.**

**Variante do leque (`FILTRO_LEQUE`, desligada).** Só vale o gatilho que **toca o leque ou fica atrás dele** — o que dispara com o preço esticado à frente das médias é descartado. Não mexe no A (que já exige o toque) e reescreve o B: EV sobe nas quatro células medidas e o drawdown do WINFUT cai de 1.575 para 525 pontos, ao custo de metade dos trades. Fica desligada porque o `t` cai onde a amostra encolhe. § 6 de [RESULTADOS.md](RESULTADOS.md).

Gestão: **stop 150 (padrão) ou 100 · parcial de 50% na mesma distância do stop · alvo 300**. Quando a parcial sai, o stop do restante fica na **média da operação** — que, com meia posição e a parcial na distância do stop, é o próprio stop inicial. O stop não anda, e o trade que volta morre em **zero de verdade** (o modelo anterior pagava +50 nesse desfecho e ainda o chamava de "zero a zero").

Entrada: **ordem limitada no meio do candle do gatilho, válida por UMA barra.** Não
preencheu na barra seguinte, o trade é abortado. Cerca de um sinal em dez morre assim,
e todo número deste projeto já está sob essa regra.

## As respostas

> As frases de conclusão do relatório e do markdown são **calculadas** a partir de
> `saida/resumo.json`, como os números. As de baixo são o resumo desta rodada; se a
> engine mudar, valem as dos documentos gerados, não estas.

1. **A regra da parcial estava modelada errado — e o conserto vale mais que a troca do indicador.** O backtest punha o stop do restante na *entrada* e tirava a parcial em +100 com stop de 150: o desfecho chamado "zero a zero" pagava **+50 pontos**. Na regra de verdade a parcial sai na **mesma distância do stop** e o stop do restante fica na **média da operação** — que, com meia posição, é o próprio stop inicial. O stop não anda e o "zero a zero" é zero. Carteira A + B, stop 150: `+48,3 → +77,5` no WINV26 e `+36,5 → +43,0` no WINFUT.
2. **A troca do eixo E2 melhora a reversão, não a tendência.** O setup B sai de `+25,0` / `t +0,86` para `+68,6` / `t +2,86` no WINV26 e de `+15,7` / `t +0,95` para `+21,0` / `t +1,21` no WINFUT. O setup A não melhora em nenhuma das quatro células. Faz sentido: o eixo novo mede exaustão, que é o que a reversão procura.
3. **A prioridade em tendência continua certa** — o setup A lidera a maioria das colunas nas duas bases, mas não mais todas: o B passou a medir `t` melhor no WINV26.
4. **O stop de 100 deixou de ser a escolha limpa.** O de 150 mede melhor em 3 das 4 comparações; o de 100 só ganha no WINV26 · só A. O plano operacional passou a usar 150, e o motivo está escrito nele.
5. **As três EMAs seguem como padrão**, com o melhor `t` em 3 das 4 combinações de base e stop; perdem só no WINFUT com stop 100, para a aproximação de Jurik — que não é o JMA de verdade.
6. **A regra da barra seguinte custa quase nada** — cerca de um sinal em dez é abortado. O ganho dela é de disciplina, não de estatística.

Leia a § 11 de [RESULTADOS.md](RESULTADOS.md) antes de dimensionar posição — os números são brutos.

## O visualizador

Está dentro do relatório, na seção 13. Navega **trade a trade** (setas ← →, ou clique na lista): candles do pregão, as médias, linhas de entrada/stop/parcial/alvo, marcas do gatilho, do preenchimento e da saída, o índice de esforço embaixo com a linha de corte, e ficha com desfecho e R$ por contrato. Filtros por base, **stop (150 ou 100 — os sinais são os mesmos, muda onde o trade morre, e a parcial acompanha)**, setup (A/B/C — inclusive o C desligado, para ver por que falha), **posição em relação ao leque (toca/atrás × na frente)** e desfecho.
