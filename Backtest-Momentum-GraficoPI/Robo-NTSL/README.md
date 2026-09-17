# Robo-NTSL

Estrategia NTSL (robo) da estrategia principal de `relatorio.html`: **Momentum PI, padrao Ouro,
entrada no fechamento, 1:3 com parcial**, no WINFUT em grafico de **20 PI**.

| Arquivo | O que e |
|:--|:--|
| `MomentumPI_OuroPrata_Robo.ntsl` | a estrategia, para o Editor de Estrategias / Automacao do Profit |
| `valida_robo.py` | confere a traducao contra a engine do backteste |
| `LogCandles_Console.ntsl` | estrategia sem ordens: registra data/hora, OHLC, agressao e duracao de cada candle com `ConsoleLog`; modo compacto empilha varios candles por linha |
| `estrutura_export.py` | converte `WINFUT/WINFUT_20PI_Robo-Export` em `WINFUT/WINFUT_20PI_Robo.csv` (ISO, um candle por linha) e confere contra a exportacao direta do Profit. Esse csv e hoje a base de todos os estudos |
| `decodifica_log.py` | le a exportacao do console (qualquer modo, blocos concatenados) e grava um CSV por candle, acusando linhas cortadas e buracos |

## O que o robo faz

- **Sinal:** o mesmo do indicador `ntsl/MomentumPI_OuroPrata.ntsl` (retracao + candle de continuacao,
  Hull 50 no sentido e atras dos dois extremos, EMA 21 dentro do par, retracao de 2+ candles, veto de
  exaustao, pavio total 25-90 pts). `NivelMinimo(2)` opera so Ouro; `NivelMinimo(1)`, Ouro e Prata.
- **Entrada:** a mercado, no fechamento do candle de sinal, `nLote` contratos (padrao 2).
- **Gestao:** stop 100; parcial de 50% em +100 por ordem limitada; stop do restante na media da
  operacao (com 50% em +100, e o proprio stop inicial); alvo 300; uma posicao por vez; encerra depois
  de 120 candles; nao abre depois de 18:15 e zera a partir de 18:20.

## Numeros medidos

> **Atualizacao 14/09/2026 -- nao ligar em conta real.** Remedido na base `WINFUT_20PI_Robo.csv`
> (132 pregoes, 06/03 a 14/09). Os filtros do Ouro foram escolhidos na base antiga (06/08 a 11/09);
> nos meses que nao participaram dessa escolha o setup nao se sustenta. Ver `RESULTADOS.md` e `PLANO.md`.

| Nivel (carteira, bruto) | Base antiga, 26 pregoes | Base nova, 132 pregoes | Antes de 06/08 (por sinal) |
|:--|--:|--:|--:|
| Ouro | 170 trades, +34,1 pts/trade, FL 1,89 | 854 trades, +2,0 pts/trade, FL 1,04 | -7,4 |
| Ouro + Prata | 243 trades, +28,0 pts/trade, FL 1,70 | 1.252 trades, +5,9 pts/trade, FL 1,13 | -0,7 |

## Validacao

```
python Robo-NTSL/valida_robo.py
```

- Sinal (base de 132 pregoes): 1.286 de 1.286 barras iguais a engine (869 Ouro), sem nenhuma
  diferenca de nivel. Na base antiga: 248 de 248.
- Sequenciamento: a maquina de estados do robo escolhe exatamente os 854 trades (Ouro) e os 1.252
  (Ouro + Prata) da carteira do relatorio.

## Antes de ligar

1. **Modo de execucao:** "ordens no fechamento do candle", executando apenas no fechamento.
2. **Sem OCO** nas opcoes de saida da automacao: ela anula o stop, a parcial e o alvo do codigo.
3. **Quantidade maxima da posicao** >= `nLote`.
4. **Zerar posicao** no fim do intervalo de execucao da automacao, como reforco do `nHoraZera`.
5. **Conta simulada primeiro.** Diferencas esperadas em relacao ao backteste estao no cabecalho do
   `.ntsl`, secao [R4]: a primeira barra do trade fica sem stop (no PI custa pouco), stop-limite com
   folga, fila na parcial, zeragem por relogio, custo.
