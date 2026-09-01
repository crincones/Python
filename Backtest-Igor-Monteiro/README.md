# Backtest-Igor-Monteiro

Backtest da **estratégia de reversão ao ajuste** no WINFUT, sobre 5 anos de barras
de 1 minuto (2021-08-23 a 2026-08-21, 1 205 pregões válidos).

## Conteúdo

| Arquivo | O que é |
|---|---|
| [ESTRATEGIA.md](ESTRATEGIA.md) | Especificação formal das regras: viés, níveis, entradas, invalidação, gestão. É o contrato que a engine implementa. |
| [RESULTADOS.md](RESULTADOS.md) | Resultados completos, grades de sensibilidade e conclusões. |
| [relatorio.html](relatorio.html) | Versão visual e explicativa dos resultados. |
| `engine.py` | Motor: carga, filtros de dia, cálculo de níveis, os 5 setups, métricas. |
| `rodar.py` | Roda tudo e grava `saida/`. |
| `auditoria.py` | Inspeção pregão a pregão e teste da premissa. |
| `valida_dados.py` | Confere que as duas bases são a mesma série de preços. |
| `dados/` | Barras M1, ajustes e o indicador de pivôs de origem. |
| `saida/` | `resumo.json` + `trades_*.csv`, operação a operação. |

## Os cinco setups

Todos partem do mesmo viés: **abriu abaixo do ajuste → compra; acima → vende**.

- **A** — o preço se afasta 1 tick da abertura; entra na abertura quando ele volta. Alvo 500 pts.
- **B** — entra no próprio ajuste, no primeiro toque. Alvo 500 pts.
- **C** — entra nos pivôs do `Pivot_Points_Pro` a 600+ pts do ajuste. Alvo no ajuste.
- **D** — o mesmo, nas bolas (múltiplos de 1 000).
- **CD** — pivôs + bolas, com fusão de 300 pts (fica o mais afastado do ajuste).

Stop de 100 pontos em todos, com saída parcial de 2/3 em +45 (o que produz o 2:1 do
enunciado) e o stop do restante indo para +45.

## Resultado

| Setup | Trades | Pontos | Acerto | PF |
|---|---:|---:|---:|---:|
| A | 1 189 | −47 572 | 32,0% | 0,41 |
| B | 894 | −50 920 | 26,2% | 0,23 |
| C | 1 368 | −4 189 | 61,1% | 0,92 |
| D | 726 | −9 947 | 53,9% | 0,70 |
| CD | 1 361 | −10 417 | 56,4% | 0,82 |

Nenhum tem borda. **O achado central desta rodada é metodológico:** com alvo parcial de
45 pontos, 92,6% das parciais são atingidas na mesma barra de 1 minuto da entrada — numa
barra de 160 pontos de amplitude mediana, e num nível que por construção é sempre um
extremo novo do dia. Conforme a convenção adotada para essa barra, o setup C vale
**−4 189, +34 880 ou +55 104 pontos**.

A 1 minuto não dá para decidir qual. Resolver exige dado de tick. Detalhes em
[RESULTADOS.md](RESULTADOS.md) §2.

## Rodar

```bash
python valida_dados.py           # confere o alinhamento das bases
python rodar.py                  # backtest completo
python auditoria.py 2026-08-21   # dump de um pregão
python auditoria.py premissa     # teste da premissa
```

Sem dependências além da biblioteca padrão do Python.
