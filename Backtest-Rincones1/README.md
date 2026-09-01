# Backtest-Rincones1

Backtest de **três setups de esforço filtrados por regime de média** no WIN, sobre barras de **10.000 ticks** (WINV26 e WINFUT, jun–ago/2026).

O gatilho é o índice de esforço já validado em `ProfitChart/Indicadores/Grafico-Ticks/Ticks_Esforco_Reversao.ntsl`; aqui ele é reimplementado idêntico e cruzado com uma média de regime para decidir se o trade vai a favor ou contra o movimento.

## Conteúdo

| Arquivo | O que é |
|---|---|
| **[PLANO.md](PLANO.md)** · **[plano.html](plano.html)** | **O plano operacional manual.** O que fazer na frente da tela, os limites do dia, a nota de aderência e o cartão de pregão. **Gerado.** |
| [ESTRATEGIA.md](ESTRATEGIA.md) | Especificação formal: gatilho, regimes, os três setups, execução e gestão. É o contrato que a engine implementa. |
| **[relatorio.html](relatorio.html)** | **O relatório.** Resultados, variantes de média, variante de stop, curvas de capital e o **visualizador de trades** — tudo num arquivo só. Abra no navegador. |
| [RESULTADOS.md](RESULTADOS.md) | Os mesmos números em markdown. **Gerado** — não edite à mão. |
| `engine.py` | Motor: carga, indicador de esforço, as cinco médias de regime, os 3 setups, simulação de trade, métricas. |
| `rodar.py` | Roda tudo e grava `saida/`. |
| `relatorio.py` + `molde.py` + `resultados_md.py` | Geram `relatorio.html` e `RESULTADOS.md` a partir de `saida/resumo.json`. |
| `plano.py` + `molde_plano.py` | Geram `PLANO.md` e `plano.html` — do mesmo `resumo.json`, e o HTML sai do próprio markdown. |
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

- **A — tendência.** Média apontando para um lado, preço volta e a toca, gatilho a favor. **Prioritário.**
- **B — reversão rápida.** Fora de consolidação, preço a 1+ range médio da média, gatilho contra o afastamento.
- **C — reversão em consolidação.** Média sem inclinação, preço afastado. **Desligado: mede negativo nas duas bases.**

Gestão: **stop 150 ou 100 · parcial de 50% em +100 (zera o risco) · alvo 300**.

Entrada: **ordem limitada no meio do candle do gatilho, válida por UMA barra.** Não
preencheu na barra seguinte, o trade é abortado. Cerca de um sinal em dez morre assim,
e todo número deste projeto já está sob essa regra.

## As quatro respostas

1. **A prioridade em tendência está certa.** O setup A é o melhor dos três nas duas bases, em todas as colunas.
2. **O stop de 100 bate o de 150** — melhor `t` e melhor fator de lucro nas duas bases, nas duas carteiras, com um terço menos de risco por trade.
3. **As três EMAs continuam ganhando — com stop 100.** É a única configuração em que o empilhamento bate KAMA, Hull, T3 e a aproximação de Jurik nas *duas* bases. Com stop 150 a KAMA passa à frente no WINFUT.
4. **A regra da barra seguinte custa quase nada.** Melhora o WINFUT, piora o WINV26, pouco dos dois lados — porque 91% dos preenchimentos já aconteciam ali. O ganho dela é de disciplina, não de estatística.

Leia a § 7 de [RESULTADOS.md](RESULTADOS.md) antes de dimensionar posição — os números são brutos.

## O visualizador

Está dentro do relatório, na seção 10. Navega **trade a trade** (setas ← →, ou clique na lista): candles do pregão, as médias, linhas de entrada/stop/parcial/alvo, marcas do gatilho, do preenchimento e da saída, o índice de esforço embaixo com a linha de corte, e ficha com desfecho e R$ por contrato. Filtros por base, setup (A/B/C — inclusive o C desligado, para ver por que falha) e desfecho.
