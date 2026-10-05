# Pesquisa multi-timeframe — tendência D1/H4 + retração H1 (B3)

Pipeline mínimo da seção 43 do `CLAUDE.md`: MT5 → universo → D1/H4/H1 → tendência → retração →
referência MM21 D1 → gatilho → backtest → CSV/Parquet → HTML com KLineCharts.

## Comandos (PowerShell, na pasta do projeto)

```powershell
uv sync
uv run mtf download            # universo + barras D1/H4/H1 do MT5 (piloto: pilot_assets do YAML)
uv run mtf download --pilot 0  # todos os ativos elegíveis
uv run mtf run                 # offline: setups → backtest → estatísticas → reports/
uv run mtf all                 # download + run
uv run pytest ; uv run ruff check .
```

O terminal da XP é aberto minimizado com `/portable` se estiver fechado e fechado ao final
(só o processo que o projeto abriu). Somente leitura: nenhuma função de trading do MT5 é usada.

## Saídas

- `data/raw/{ATIVO}_{D1|H4|H1}.parquet` — barras fechadas (barra em formação é descartada),
  horário America/Sao_Paulo, com `close_time`.
- `data/metadata/universe.parquet`, `download.json` — ações com opções, liquidez, seleção.
- `results/AAAAMMDD_HHMMSS/` — `trades.parquet/csv` (log por trade), `comparison.csv`,
  `increments.csv`, `distance_buckets.csv`, `by_asset.csv`, `by_year.csv`,
  `liquidity_robustness.csv`, `quality.csv`, `universe.csv`, `warnings.json`, `run_meta.json`
  (timestamp, commit, hash da config, período, parâmetros) e `reports/`.
- `reports/` — cópia do relatório da última execução: `index.html`, `universe.html`,
  `comparison.html`, `examples.html` (KLineCharts embutido, funciona offline).

## Configuração

- `config/universe.yaml` — MT5, período, universo, liquidez, qualidade.
- `config/strategy.yaml` — tendência, retração, referência, stop/alvo e variantes (A–F e benchmarks).
- `config/backtest.yaml` — custos, benchmark aleatório, alertas, buckets, incrementos, exemplos.

## Regras contra look-ahead

Cada barra H1 é decidida no fechamento. D1/H4 entram via `merge_asof` pelo `close_time`: durante o
pregão vale o D1 da véspera; o H4 das 12:00 só vale após o fechamento da H1 das 15:00. A entrada é
ordem stop na barra seguinte ao sinal. `tests/test_lookahead.py` trunca os dados em vários
instantes e exige que features e setups passados não mudem.

## Arquitetura

```
src/mtf/
  mt5/          ÚNICO pacote que importa MetaTrader5 (client, terminal, download)
  data/         store (Parquet), quality, timeutils
  universe/     liquidez e seleção
  indicators/   MM, ATR (Wilder)
  trend/        modelo A (MM + inclinação)
  pullback/     candles consecutivos contra a tendência
  signals/      alinhamento D1/H4→H1 e tabela de setups (descoberta de sinais)
  backtest/     simulação de execução (separada dos sinais)
  statistics/   métricas, bootstrap, alertas de concentração, buckets de distância
  reports/      exemplos + Jinja2 → HTML
  pipeline.py   orquestra uma execução
  cli.py        Typer
```

## Ainda não implementado (próximas etapas da pesquisa)

Modelos de tendência B/C (estrutura, score), outras referências (H4, swing, Fibonacci), gatilhos
B–F, stops ATR, trailing, walk-forward, sensibilidade de parâmetros, Monte Carlo, cenários de custo.
