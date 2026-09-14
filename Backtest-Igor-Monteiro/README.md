# Backtest-Igor-Monteiro

Backtest da **estratégia de reversão ao ajuste** no WINFUT, sobre 5 anos de barras
de 1 minuto (2021-08-23 a 2026-08-21, 1 205 pregões válidos).

## Conteúdo

| Arquivo | O que é |
|---|---|
| [ESTRATEGIA.md](ESTRATEGIA.md) | Especificação formal das regras: viés, níveis, entradas, invalidação, gestão. É o contrato que a engine implementa. |
| [RESULTADOS.md](RESULTADOS.md) | Resultados completos, grades de sensibilidade e conclusões. |
| [relatorio.html](relatorio.html) | Versão visual e explicativa dos resultados, com o navegador trade a trade. |
| `engine.py` | Motor: carga, filtros de dia, cálculo de níveis, os 5 setups, métricas. |
| `rodar.py` | Roda tudo e grava `saida/`. |
| `auditoria.py` | Inspeção pregão a pregão e teste da premissa. |
| `navegador.py` | Gera a seção “trade a trade” do relatório: candles M1 com cada operação desenhada, nas duas convenções da barra de entrada. |
| `vendor/` | KLineCharts 9.8.10, embutido no relatório pelo `navegador.py`. |
| `valida_dados.py` | Confere que as duas bases são a mesma série de preços. |
| `dados/` | Barras M1, ajustes e o indicador de pivôs de origem. |
| `saida/` | `resumo.json` + `trades_*.csv`, operação a operação. |

## Os cinco setups

Todos partem do mesmo viés: **abriu abaixo do ajuste → compra; acima → vende**.

- **A** — o preço se afasta 1 tick da abertura; entra na abertura quando ele volta. Alvo 500 pts.
- **B** — entra no próprio ajuste, no primeiro toque. Alvo 500 pts.
- **C** — entra nos pivôs do `Pivot_Points_Pro` a 600+ pts do ajuste, rumo ao ajuste.
- **D** — o mesmo, nas bolas (múltiplos de 1 000).
- **CD** — pivôs + bolas, com fusão de 300 pts (fica o mais afastado do ajuste).

Em todos: lote de **6 contratos**, stop de 100 pontos, alvo de **500 pontos fixos**, e
saída parcial de 2/3 (4 contratos) em +45 — o que produz o 2:1 do enunciado — com o stop
dos 2 que sobram indo para o **preço médio da operação**: 90 pontos contra a entrada,
onde o total zera. A parcial de 50% (3 de 6, médio a −45) roda em paralelo. Pontos são
por contrato.

## Resultado

| Setup | Trades | Pontos | Ganham | Zeram | PF |
|---|---:|---:|---:|---:|---:|
| A | 1 189 | −49 433 | 13,5% | 18,5% | 0,39 |
| B | 894 | −53 230 | 7,4% | 18,8% | 0,19 |
| C | 1 368 | −11 908 | 15,9% | 45,2% | 0,78 |
| D | 726 | −16 252 | 12,7% | 41,2% | 0,51 |
| CD | 1 361 | −21 107 | 15,1% | 41,2% | 0,64 |

Nenhum tem borda, em nenhum ano — e o breakeven no médio com 2/3 é a pior variante de
parcial testada (com 50% o CD vai a −18 741, ainda negativo). **O achado central desta rodada é metodológico:** com alvo parcial de 45
pontos, 92,6% das entradas têm a parcial ao alcance na mesma barra de 1 minuto — numa
barra de 160 pontos de amplitude mediana, e num nível que por construção é sempre um
extremo novo do dia. Conforme a convenção adotada para essa barra, o setup C vale
**−11 908, +20 459 ou +42 982 pontos**.

A 1 minuto não dá para decidir qual. Resolver exige dado de tick. Detalhes em
[RESULTADOS.md](RESULTADOS.md) §2.

## Rodar

```bash
python valida_dados.py           # confere o alinhamento das bases
python rodar.py                  # backtest completo
python auditoria.py 2026-08-21   # dump de um pregão
python auditoria.py premissa     # teste da premissa
python navegador.py              # (re)gera a seção trade a trade do relatorio.html
```

Sem dependências além da biblioteca padrão do Python. O `navegador.py` só reescreve o
trecho entre `<!-- navegador:inicio -->` e `<!-- navegador:fim -->`; o resto do
relatório é editado à mão.
