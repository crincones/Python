# Backtest-Rincones1

Backtest de **três setups de esforço filtrados por regime de média** no WIN, sobre barras de **10.000 ticks** (WINFUT abr–set/2026 e WINV26 até ago/2026).

O gatilho é o índice de esforço já validado em `ProfitChart/Indicadores/Grafico-Ticks/Ticks_Esforco_Reversao.ntsl`; aqui ele é reimplementado idêntico e cruzado com uma média de regime para decidir se o trade vai a favor ou contra o movimento.

> **Esta rodada trocou o eixo E2 do gatilho.** Ele media `|delta| / |Close−Open|` — agressão por ponto de *saldo*, cego ao caminho que o preço fez dentro da barra. Agora mede **vaivém**: `(|delta|/esforço) × (1 − |Close−Open|/percurso)`, com `percurso = 2·(High−Low) − |Close−Open|`. A derivação está em `Ticks_Esforco_Hist_v2.ntsl` e o efeito no backtest, medido com todo o resto congelado, está na **§ 2 de [RESULTADOS.md](RESULTADOS.md)**. Para voltar à fórmula antiga: `METRICA_E2 = 0` em `engine.py`.

> **Esta rodada trocou a base do WINFUT** para `dados/WINFUT_10K_Ticks_Robo.csv`, exportado pelo robô: 102 pregões, de 17/04 a 11/09/2026 (o pregão de 14/09, ainda aberto na gravação, é descartado). Ele contém o WINFUT antigo barra a barra — no período antigo reproduz os mesmos 148 trades — e acrescenta **58 pregões fora da janela em que os parâmetros foram escolhidos** (30/06–28/08). Esses pregões são o primeiro teste fora da amostra do projeto, e **a vantagem não se repetiu neles**. § 10 de [RESULTADOS.md](RESULTADOS.md).

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
| `dados/` | `WINFUT_10K_Ticks_Robo.csv` (exportado pelo robô, a base do WINFUT) e `WINV26_10000T_28-08-26.csv` (exportado do Profit). `WIFNUT_10000T_28-28-26.csv` é o WINFUT antigo, mantido só como referência. `carrega()` lê os dois formatos. |
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

**Variante do leque (`FILTRO_LEQUE`, desligada).** Só vale o gatilho que **toca o leque ou fica atrás dele** — o que dispara com o preço esticado à frente das médias é descartado. Não mexe no A (que já exige o toque) e reescreve o B: corta boa parte dos trades e melhora o EV da carteira A + B, mas fora da janela de calibração o B que sobra mede negativo. § 6 de [RESULTADOS.md](RESULTADOS.md).

Gestão: **stop 150 (padrão) ou 100 · parcial de 50% na mesma distância do stop · alvo 300**. Quando a parcial sai, o stop do restante fica na **média da operação** — que, com meia posição e a parcial na distância do stop, é o próprio stop inicial. O stop não anda, e o trade que volta morre em **zero de verdade** (o modelo anterior pagava +50 nesse desfecho e ainda o chamava de "zero a zero").

Entrada: **ordem limitada no meio do candle do gatilho, válida por UMA barra.** Não
preencheu na barra seguinte, o trade é abortado. Cerca de um sinal em dez morre assim,
e todo número deste projeto já está sob essa regra.

## As respostas

> As frases de conclusão do relatório e do markdown são **calculadas** a partir de
> `saida/resumo.json`, como os números. As de baixo são o resumo desta rodada; se a
> engine mudar, valem as dos documentos gerados, não estas.

Carteira A + B, stop 150, sem custo, salvo indicação.

1. **Fora da amostra a vantagem não se repetiu.** Dentro da janela de calibração o WINFUT mede `+44,1` / `t +2,97` (A + B) e `+80,6` / `t +3,12` (só A). Nos 58 pregões fora dela: `−5,3` / `t −0,45` e `+9,9` / `t +0,51`. Com 5 pontos de custo o só A fora da janela vai a `+4,9`.
2. **O estrago está antes da janela.** Abr–jun: só A `−10,5` em 57 trades, A + B `−10,9` em 152. Depois da janela (9 pregões de setembro) o só A volta a `+71,1` em 19 trades — curto demais para desempatar.
3. **O setup B é o que mais sofre.** Isolado, fora da janela: `−15,2` / `t −0,98` em 128 trades. Na base inteira do WINFUT ele fica em `+1,2`. O A isolado na base inteira ainda mede `+38,9` / `t +2,45`, mas quase tudo vem da janela de calibração.
4. **Na base inteira do WINFUT o resultado cai pela metade ou mais:** A + B `+43,0 → +16,1` (`t +2,84 → +1,68`), drawdown `1.575 → 2.475` pontos; só A `+77,8 → +39,2`. Com 20 pontos de custo a carteira A + B fica negativa. O WINV26 não mudou — e está inteiro dentro da janela.
5. **Os ajustes finos continuam onde estavam**, mas perderam peso: stop 150 melhor em 3 de 4 comparações, alvo 300 melhor em 5 de 6 linhas, três EMAs com o melhor `t` em 2 de 4 (a aproximação de Jurik passa à frente no WINFUT). Afinar parâmetro de uma estratégia que não passou no teste fora da amostra é o passo errado.
6. **O plano operacional agora abre com o aviso**: procedimento sim, dinheiro não — simulador ou tamanho mínimo até registros novos.

Leia a § 10 (fora da amostra) e a § 11 de [RESULTADOS.md](RESULTADOS.md) antes de dimensionar posição — os números são brutos.

## O visualizador

Está dentro do relatório, na seção 13. Navega **trade a trade** (setas ← →, ou clique na lista): candles do pregão, as médias, linhas de entrada/stop/parcial/alvo, marcas do gatilho, do preenchimento e da saída, o índice de esforço embaixo com a linha de corte, e ficha com desfecho e R$ por contrato. Filtros por base, **stop (150 ou 100 — os sinais são os mesmos, muda onde o trade morre, e a parcial acompanha)**, setup (A/B/C — inclusive o C desligado, para ver por que falha), **posição em relação ao leque (toca/atrás × na frente)** e desfecho.
