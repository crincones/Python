# Reversões nas VWAP Bands

Gráfico PI 20 ticks, WINFUT.

## Dados

`WINFUT_20PI/WINFUT_20PI.csv`: exportação do console do robô `Robo-NTSL/LogVWAP_Console.ntsl`
(cópia do `LogCandles_Console.ntsl` do Backtest-Momentum-GraficoPI com volume financeiro e quantidade).
Decodificar com `python Robo-NTSL/decodifica_vwap.py WINFUT_20PI/WINFUT_20PI.csv WINFUT_20PI/WINFUT_20PI_decod.csv`.
O console do Profit corta em ~2.000 linhas: com 40 candles por linha cabe o período todo.
Os candles são os mesmos da base do `../Backtest-Momentum2-GraficoPI` (conferidos 1 a 1); EMA, Hull e MACD
vêm do `engine.py` de lá (importado, não copiado).

## VWAP Band (Profit, período Diário, preço típico Média financeira)

- VWAP: preço do candle = volume financeiro ÷ quantidade ÷ 0,20; peso = quantidade; zerada todo pregão.
- Bandas: ENVELOPES da VWAP a ±1/3 %, ±2/3 % e ±1 % (VWAP × (1 ± k/300)); o artigo arredonda para 0,33/0,66/0,99 %.
- Conferido: artigo da Nelogica (WDO 24/04) e print do Profit de 16/09 (`exemplo.md`), iguais ao ponto.
- Sinais e toques desde a abertura.
- A versão por desvio-padrão (errada) ficou em `vbase.vwap(d, 'desvio')` só para comparação.

## Perguntas do estudo

- Quais padrões de reversão nas bandas são melhores.
- Se o ângulo da VWAP e os primeiros toques melhoram o resultado.
- Se a VWAP é bom ponto de entrada, ou só de saída.
- Operar só o 1º ou 2º toque da banda no dia, uma entrada por toque (pedido depois).
- Saídas: alvo 300 seco, alvo 500 seco, alvo na VWAP e gestão do CLAUDE.md de origem (parcial +100, alvo 300). Stop 100.
- 6 contratos, custo round turn R$ 0,50 por contrato. Treino = primeiros 60% dos pregões.

## Arquivos

- `vbase.py`: dados, VWAP, bandas, episódios de toque, sinais (c1 / c2 / hull; reversão na banda ou na VWAP), simulação (numba).
- `vwap_estudo.py` / `vwap_rel.py`: estudo geral -> `vwap.html`, `VWAP.md`.
- `toque_estudo.py` / `toque_rel.py`: 1º/2º toque, uma entrada por toque -> `toque.html`, `TOQUE.md`.

Ordem: `python vwap_estudo.py`, `python vwap_rel.py`, `python toque_estudo.py`, `python toque_rel.py`.
