# Pesquisa Multi-Timeframe — Tendência D1/H4 + Retração H1

## 1. Objetivo

Construir um projeto quantitativo para investigar se uma estratégia de:

1. identificação de tendência em timeframes superiores;
2. identificação de retração em timeframe inferior;
3. entrada próxima a regiões relevantes do timeframe superior;
4. confirmação da retomada da tendência;

possui vantagem estatística em ações brasileiras líquidas.

O projeto deve ser capaz de:

* obter dados históricos do MetaTrader 5;
* selecionar automaticamente ações brasileiras líquidas;
* restringir o universo a ativos com opções negociadas;
* testar pelo menos 2 anos de histórico quando disponível;
* testar diversas definições de tendência;
* testar diversas definições de retração;
* testar diversas médias e referências de preço;
* testar diferentes gatilhos de entrada;
* realizar backtests sem look-ahead bias;
* gerar estatísticas detalhadas;
* gerar gráficos de operações;
* gerar relatórios HTML navegáveis;
* incluir exemplos visuais usando KLine Charts;
* comparar diferentes versões do filtro de retração;
* identificar se a proximidade de uma referência do D1/H4 melhora estatisticamente a entrada.

O objetivo NÃO é encontrar uma estratégia perfeita por otimização excessiva.

O objetivo principal é responder:

> "Existe evidência estatística de que, dentro de uma tendência estabelecida em D1/H4, esperar uma retração do H1 até determinadas regiões aumenta a qualidade das entradas para continuação da tendência?"

---

# 2. Universo de ativos

Utilizar inicialmente ações brasileiras negociadas na B3 que satisfaçam:

* liquidez média diária >= R$ 5.000.000;
* existência de opções negociadas;
* histórico suficiente para o período de teste;
* dados OHLCV disponíveis no MetaTrader 5.

A seleção de liquidez deve ser calculada usando o próprio histórico.

Preferir:

```text
volume financeiro diário = volume × preço
```

e não apenas número de ações negociadas.

Sempre que possível utilizar média móvel de liquidez, por exemplo:

* média 20 dias;
* média 60 dias;
* média 120 dias.

A regra padrão inicial:

```text
average_daily_value_60 >= R$ 5.000.000
```

Mas deixar o parâmetro configurável.

Testar também:

```text
R$ 5 milhões
R$ 10 milhões
R$ 20 milhões
R$ 50 milhões
```

para verificar a robustez.

## Opções

O ativo deve possuir opções negociadas na B3.

A existência de opções deve ser utilizada apenas como filtro do universo.

Não é necessário realizar operações com opções nesta primeira etapa.

---

# 3. Dados

A fonte primária dos preços deve ser o MetaTrader 5.

Utilizar dados históricos de:

```text
D1
H4
H1
```

Sempre que possível baixar dados brutos de período maior que o período efetivamente usado no backtest.

O projeto deve permitir:

```text
START_DATE
END_DATE
```

e utilizar pelo menos 2 anos quando houver histórico disponível.

Se o ativo tiver somente 18 meses:

* testar os 18 meses;
* registrar explicitamente a limitação;
* não inventar dados.

Registrar para cada ativo:

```text
symbol
first_available_date
last_available_date
number_of_bars
average_daily_value
options_available
```

---

# 4. Cuidado com dados do MetaTrader 5

O código deve verificar:

* timezone;
* horário de negociação;
* feriados;
* gaps;
* candles incompletos;
* candles duplicados;
* mudanças de ticker;
* corporate actions quando identificáveis;
* splits;
* ajustes.

Não utilizar o candle atual/incompleto em nenhuma decisão de backtest.

Todos os indicadores devem ser calculados somente com informação disponível naquele instante.

---

# 5. Estrutura geral da estratégia

A arquitetura conceitual é:

```text
D1
 ↓
Determina regime/tendência principal

H4
 ↓
Confirma ou contradiz tendência D1

H1
 ↓
Procura retração

H1 + referências D1/H4
 ↓
Identifica zona de possível término da retração

H1
 ↓
Confirma retomada

Entrada
 ↓
Gerenciamento
 ↓
Resultado
```

Não assumir inicialmente que essa estrutura funciona.

O backtest deve comparar contra benchmarks.

---

# 6. Definição de tendência D1

Implementar várias definições.

## D1 Trend Model A — média

Alta:

```text
close > SMA21
SMA21[t] > SMA21[t-n]
```

Baixa:

```text
close < SMA21
SMA21[t] < SMA21[t-n]
```

Testar:

```text
SMA 10
SMA 20
SMA 21
SMA 30
SMA 50
EMA 20
EMA 21
EMA 50
```

## D1 Trend Model B — estrutura

Alta:

```text
Higher High
Higher Low
```

Baixa:

```text
Lower High
Lower Low
```

Criar algoritmo configurável para identificação de pivôs.

Testar diferentes tamanhos de pivô.

## D1 Trend Model C — combinação

Exemplo:

```text
close > MA21
MA21 inclinada positivamente
estrutura HH/HL
```

Criar score de tendência.

Exemplo:

```text
MA_position       +1
MA_slope          +1
structure         +2
MA_fast > MA_slow +1
```

Não considerar os pesos como definitivos.

Eles devem ser parâmetros pesquisáveis.

---

# 7. Definição de tendência H4

Implementar os mesmos modelos:

* média;
* inclinação;
* estrutura;
* combinação.

A estratégia principal deve inicialmente exigir:

```text
D1 trend == H4 trend
```

Exemplo:

```text
D1 = bullish
H4 = bullish
→ procurar long
```

ou:

```text
D1 = bearish
H4 = bearish
→ procurar short
```

Mas também testar:

```text
D1 bullish + H4 neutral
D1 bullish + H4 bearish
```

para verificar se esperar a confirmação H4 realmente melhora os resultados.

---

# 8. Identificação da retração H1

Implementar várias definições.

## Retração por direção

Para tendência bullish:

```text
H1 candles contra a tendência
```

Para tendência bearish:

```text
H1 candles contra a tendência
```

Testar:

```text
1 candle
2 candles
3 candles
4 candles
5 candles
```

consecutivos.

## Retração por estrutura

Detectar:

```text
impulse
pullback
potential continuation
```

Exemplo bullish:

```text
HH → HL → HH
```

durante o impulso.

Depois:

```text
queda H1
```

até uma região de suporte.

---

# 9. Referências para a retração

NÃO assumir que MM21 D1 é a melhor referência.

Testar:

### Médias D1

```text
SMA10
SMA20
SMA21
SMA30
SMA50
SMA100
EMA10
EMA20
EMA21
EMA30
EMA50
```

### Médias H4

```text
SMA20
SMA21
SMA50
EMA20
EMA21
EMA50
```

### Estrutura

```text
previous D1 high
previous D1 low
previous H4 high
previous H4 low
previous swing high
previous swing low
```

### Fibonacci

Testar retrações:

```text
23.6%
38.2%
50%
61.8%
78.6%
```

do último impulso identificável.

### Volatilidade

Utilizar ATR:

```text
ATR D1
ATR H4
```

para normalizar distância.

---

# 10. Distância da referência

Nunca utilizar apenas distância absoluta.

Calcular:

```text
distance = abs(price - reference)
```

e também:

```text
distance / ATR_D1
distance / ATR_H4
```

Criar zonas:

```text
0.10 ATR
0.20 ATR
0.30 ATR
0.50 ATR
0.75 ATR
1.00 ATR
```

Exemplo:

```text
price within 0.30 ATR_D1 of SMA21_D1
```

significa que o preço está dentro da zona de interesse.

---

# 11. Teste específico da hipótese MM21 D1

Este é um teste prioritário.

Hipótese:

> Quando D1 e H4 estão alinhados em tendência e o H1 está em retração, entradas próximas da MM21 D1 apresentam melhor comportamento que entradas realizadas sem esse filtro.

Criar grupos:

```text
A = tendência + retração, sem filtro de distância

B = preço <= 1.0 ATR da MM21 D1

C = preço <= 0.75 ATR da MM21 D1

D = preço <= 0.50 ATR da MM21 D1

E = preço <= 0.30 ATR da MM21 D1

F = toque da MM21 D1
```

Comparar:

* taxa de acerto;
* retorno médio;
* retorno mediano;
* MAE;
* MFE;
* expectativa;
* profit factor;
* drawdown;
* duração;
* distribuição dos resultados.

---

# 12. Gatilhos de entrada

Não assumir um único gatilho.

Implementar:

## Trigger A

Rompimento da máxima do candle H1 anterior.

Para short:

```text
rompimento da mínima
```

## Trigger B

Candle de rejeição.

Exemplo:

```text
long wick inferior
close próximo da máxima
```

## Trigger C

Retomada de estrutura:

```text
higher low
+
rompimento do último lower high
```

## Trigger D

Rompimento da máxima do pullback.

## Trigger E

Retomada da média H1.

## Trigger F

Combinação:

```text
zona de interesse
+
rejeição
+
rompimento
```

---

# 13. Entrada sem confirmação

Criar também um benchmark:

```text
entrar imediatamente quando preço entra na zona
```

Isso é importante.

A comparação deve responder:

> Esperar confirmação realmente melhora a operação ou apenas reduz o número de operações?

---

# 14. Stop loss

Testar diferentes métodos.

## Stop estrutural

Abaixo do fundo do pullback para long.

Acima do topo para short.

## ATR

```text
0.5 ATR_H1
0.75 ATR_H1
1.0 ATR_H1
1.5 ATR_H1
2.0 ATR_H1
```

## Estrutura + buffer

```text
swing_low - 0.1 ATR
```

---

# 15. Saídas

Para permitir comparação objetiva, implementar inicialmente targets fixos em R:

```text
0.5R
1R
1.5R
2R
2.5R
3R
4R
```

Também testar:

```text
trailing stop
```

e:

```text
saída na perda da estrutura H1
```

O relatório deve separar claramente:

```text
entry edge
```

de:

```text
exit edge
```

---

# 16. Não otimizar tudo simultaneamente

Muito importante.

Evitar brute-force indiscriminado.

Dividir a pesquisa em etapas:

### Etapa 1

Verificar se:

```text
D1 + H4 trend
```

possui comportamento diferente de aleatoriedade.

### Etapa 2

Adicionar:

```text
H1 pullback
```

### Etapa 3

Adicionar:

```text
reference zone
```

### Etapa 4

Adicionar:

```text
entry trigger
```

### Etapa 5

Testar gerenciamento.

Assim será possível saber qual componente realmente adiciona valor.

---

# 17. Benchmark obrigatório

Criar pelo menos estes benchmarks:

### Benchmark 1

Entrada aleatória dentro do mesmo universo temporal.

### Benchmark 2

Tendência D1/H4 sem filtro de retração.

### Benchmark 3

Tendência + retração H1 sem referência.

### Benchmark 4

Tendência + retração + referência.

### Benchmark 5

Tendência + retração + referência + confirmação.

O objetivo é medir o incremento de cada filtro.

---

# 18. Métricas

Para cada estratégia e ativo:

```text
number_of_trades
win_rate
loss_rate
average_return
median_return
expectancy
profit_factor
gross_profit
gross_loss
max_drawdown
average_R
median_R
best_trade
worst_trade
average_trade_duration
MAE
MFE
```

Também calcular:

```text
return_after_5_bars
return_after_10_bars
return_after_20_bars
```

quando aplicável.

---

# 19. Métricas específicas para validar a retração

Este é um objetivo central do projeto.

Para cada entrada registrar:

```text
distance_to_D1_MA
distance_to_H4_MA
distance_to_support
distance_to_resistance
pullback_depth
pullback_duration
impulse_size
ATR_D1
ATR_H4
ATR_H1
```

Depois analisar:

```text
MAE
MFE
future_return
```

em função dessas variáveis.

Criar buckets:

```text
0-0.25 ATR
0.25-0.50 ATR
0.50-0.75 ATR
0.75-1.00 ATR
1.00+ ATR
```

---

# 20. Out-of-sample

Não utilizar todo o histórico para escolher parâmetros.

Utilizar:

```text
60% train
20% validation
20% test
```

ou:

```text
walk-forward analysis
```

Preferir walk-forward.

Exemplo:

```text
Train: 12 meses
Test: 3 meses

Train: 12 meses
Test: próximos 3 meses

...
```

Registrar todos os resultados.

---

# 21. Robustez entre ativos

Uma estratégia NÃO deve ser considerada validada apenas porque funciona em um ativo.

Calcular:

```text
median expectancy across assets
```

e:

```text
percentage of assets profitable
```

Também separar:

```text
large caps
mid caps
```

quando possível.

---

# 22. Robustez temporal

Separar resultados por:

```text
ano
trimestre
mês
```

e, se possível:

```text
regime de volatilidade
```

---

# 23. Controle de overfitting

O projeto deve alertar quando:

* uma configuração possui poucas operações;
* resultado depende de poucos trades;
* um único ativo gera grande parte do lucro;
* um único período gera grande parte do resultado;
* pequenas mudanças de parâmetro destroem o resultado.

Implementar análise de sensibilidade.

Exemplo:

Se SMA21 funcionar:

```text
SMA18
SMA19
SMA20
SMA21
SMA22
SMA23
SMA24
```

deve ser testado.

Uma região ampla de bons resultados é preferível a um pico isolado.

---

# 24. Permutação / Monte Carlo

Quando possível implementar:

* randomização da ordem dos trades;
* bootstrap dos retornos;
* Monte Carlo de equity curves.

Estimar:

```text
drawdown distribution
probability of negative outcome
expected range of equity curves
```

---

# 25. Visualização

Utilizar KLine Charts nos relatórios HTML.

Cada exemplo deve mostrar:

* candles;
* médias;
* referência D1/H4;
* entrada;
* stop;
* target;
* região de retração;
* indicação visual do motivo da entrada.

Criar gráficos multi-timeframe quando possível.

Exemplo:

```text
┌─────────────────────────────┐
│ D1                          │
│ tendência + MM21            │
└─────────────────────────────┘

┌─────────────────────────────┐
│ H4                          │
│ confirmação da tendência    │
└─────────────────────────────┘

┌─────────────────────────────┐
│ H1                          │
│ retração → zona → entrada   │
└─────────────────────────────┘
```

---

# 26. Relatórios HTML

Gerar:

```text
reports/
    index.html
    universe.html
    summary.html
    comparison.html
    robustness.html
    walk_forward.html
    monte_carlo.html
    examples/
```

## index.html

Deve apresentar:

* objetivo;
* período analisado;
* universo;
* quantidade de ativos;
* quantidade de operações;
* principais conclusões quantitativas;
* links para os demais relatórios.

## comparison.html

Comparar:

```text
sem filtro
MM10
MM20
MM21
MM30
MM50
estrutura
Fibonacci
ATR
```

Não ordenar automaticamente apenas pelo maior lucro.

Mostrar múltiplas métricas.

---

# 27. Exemplos de operações

Selecionar automaticamente exemplos:

### Bons exemplos

* trade com grande MFE;
* trade que respeitou a zona;
* trade com retração limpa.

### Maus exemplos

* stop;
* falso rompimento;
* retração que continuou contra a tendência.

### Casos ambíguos

* preço tocou referência mas não confirmou;
* tendência perdeu força;
* múltiplas referências próximas.

Cada exemplo deve conter uma explicação textual gerada pelo código:

```text
D1 trend: bullish
H4 trend: bullish
H1 pullback: 4 candles
Reference: D1 SMA21
Distance: 0.27 ATR_D1
Trigger: previous high breakout
Stop: structural
Result: +2.1R
```

---

# 28. Estrutura de projeto

Criar arquitetura semelhante a:

```text
project/
│
├── CLAUDE.md
├── README.md
├── requirements.txt
│
├── config/
│   ├── universe.yaml
│   ├── strategy.yaml
│   └── backtest.yaml
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── metadata/
│
├── src/
│   ├── mt5/
│   ├── universe/
│   ├── indicators/
│   ├── trend/
│   ├── pullback/
│   ├── signals/
│   ├── backtest/
│   ├── statistics/
│   ├── robustness/
│   └── reports/
│
├── tests/
│
├── reports/
│
└── notebooks/
```

---

# 29. Separação entre pesquisa e backtest

Não misturar:

```text
signal discovery
```

com:

```text
execution simulation
```

Criar objetos/estruturas para:

```text
MarketData
TrendState
PullbackState
Setup
Trade
BacktestResult
```

---

# 30. Logs

Registrar detalhadamente:

```text
asset
date
D1 state
H4 state
H1 state
reference
distance
trigger
entry
stop
target
exit
R
MFE
MAE
```

Salvar em formato facilmente analisável:

```text
CSV
Parquet
```

---

# 31. Reprodutibilidade

Toda execução deve registrar:

```text
timestamp
git commit
config hash
data range
parameters
number of assets
```

Nunca sobrescrever resultados anteriores.

Utilizar:

```text
results/YYYYMMDD_HHMMSS/
```

---

# 32. Configuração

Todos os parâmetros importantes devem ficar fora do código.

Exemplo:

```yaml
trend:
  daily:
    ma_type: SMA
    ma_period: 21
    slope_period: 5

  h4:
    ma_type: SMA
    ma_period: 21

pullback:
  min_bars: 2
  max_bars: 5

reference:
  type: daily_ma
  period: 21
  max_distance_atr: 0.5

entry:
  trigger: previous_high_break

risk:
  stop: structural
  target_r: 2.0
```

---

# 33. Primeira bateria de testes

Antes de qualquer otimização, executar:

### Teste A

```text
D1 trend
+
H4 trend
+
H1 pullback
```

sem referência.

### Teste B

Adicionar:

```text
MM21 D1
distance <= 1 ATR
```

### Teste C

Testar:

```text
distance <= 0.75 ATR
distance <= 0.50 ATR
distance <= 0.30 ATR
```

### Teste D

Comparar:

```text
MM10
MM20
MM21
MM30
MM50
```

### Teste E

Comparar referência:

```text
D1 MA
H4 MA
swing
Fibonacci
ATR
```

### Teste F

Adicionar confirmação H1.

---

# 34. Pergunta principal do relatório

O relatório final deve responder explicitamente:

> "O filtro de esperar uma retração próxima a uma referência do D1/H4 melhora a qualidade das entradas?"

Mas não responder apenas com win rate.

Mostrar:

```text
Número de trades
Expectancy
Profit Factor
Average R
Median R
MFE
MAE
Drawdown
Resultado por ativo
Resultado por período
Resultado out-of-sample
```

---

# 35. Conclusão estatística

Separar:

## Evidência favorável

Quando houver:

* melhora consistente;
* número suficiente de trades;
* robustez entre ativos;
* robustez temporal;
* resultado fora da amostra;
* ausência de dependência excessiva de um único parâmetro.

## Evidência fraca

Quando:

* poucas operações;
* resultado concentrado;
* grande sensibilidade aos parâmetros.

## Evidência contra

Quando adicionar o filtro piora consistentemente:

```text
expectancy
MFE
MAE
drawdown
```

ou não produz melhoria estatisticamente relevante.

Não declarar que uma estratégia "funciona" apenas porque apresentou lucro no backtest.

---

# 36. Regras contra look-ahead bias

OBRIGATÓRIO.

Nunca utilizar:

* fechamento futuro;
* máxima futura;
* mínima futura;
* pivô confirmado usando dados futuros sem atraso;
* informação de opções conhecida posteriormente;
* dados revisados posteriormente.

Quando um pivô precisar de candles futuros para confirmação, o sinal só poderá existir após o número necessário de candles ter fechado.

Documentar isso no código.

---

# 37. Custos

O backtest deve permitir:

```text
brokerage
exchange fees
slippage
```

Mesmo que inicialmente configurados como zero.

Testar posteriormente cenários de:

```text
zero cost
low cost
realistic cost
high cost
```

---

# 38. Slippage

Permitir:

```text
0
1 tick
2 ticks
3 ticks
```

ou percentual configurável.

---

# 39. Performance

O projeto deve evitar recalcular indicadores para cada combinação.

Preferir:

* pandas/polars;
* numpy;
* armazenamento parquet;
* cache de indicadores;
* processamento incremental;
* multiprocessing quando apropriado.

Se a combinação de parâmetros ficar muito grande, utilizar uma arquitetura de experimentos.

---

# 40. Critério de sucesso da pesquisa

O projeto não precisa encontrar uma estratégia lucrativa.

O projeto será considerado bem-sucedido se conseguir responder de forma confiável:

1. Se D1/H4 realmente identificam um contexto diferente de aleatoriedade.
2. Se o H1 pullback melhora as entradas.
3. Se esperar proximidade de uma referência melhora o resultado.
4. Qual referência apresenta maior robustez.
5. Qual distância da referência é mais interessante.
6. Se confirmação H1 adiciona valor.
7. Se os resultados permanecem fora da amostra.
8. Se o efeito aparece em vários ativos.
9. Se o efeito permanece depois dos custos.
10. Quais condições parecem não funcionar.

---

# 41. Entrega final

Ao terminar uma execução completa, gerar:

```text
reports/index.html
```

com:

### Universo

Lista dos ativos analisados.

### Dados

Período disponível por ativo.

### Estratégias

Todas as configurações testadas.

### Resultados

Tabela comparativa.

### Robustez

Sensibilidade aos parâmetros.

### Walk-forward

Resultados out-of-sample.

### Monte Carlo

Distribuição das equity curves.

### Exemplos

Pelo menos:

* 10 bons exemplos;
* 10 exemplos ruins;
* 10 exemplos intermediários.

Quando houver dados suficientes.

### Conclusão

Resumo quantitativo da hipótese:

```text
Trend filter
Pullback filter
Reference filter
Entry confirmation
```

indicando quanto cada componente alterou as métricas.

---

# 42. Filosofia do projeto

Não procurar:

> "qual combinação de parâmetros ganhou mais?"

Procurar:

> "qual fenômeno de mercado aparece de forma consistente?"

Uma estratégia com:

```text
55% win rate
```

não é necessariamente melhor que uma com:

```text
45% win rate
```

A análise deve considerar distribuição dos retornos, expectativa, risco, drawdown, robustez e estabilidade.

Priorizar:

```text
robustez > resultado máximo
```

e:

```text
simplicidade > complexidade
```

---

# 43. Próximo passo

Primeiro construir o pipeline mínimo:

```text
MT5
 ↓
universo
 ↓
D1/H4/H1
 ↓
trend detector
 ↓
pullback detector
 ↓
MM21 D1 reference
 ↓
entry
 ↓
backtest
 ↓
CSV/Parquet
 ↓
HTML + KLine Charts
```

Executar esse pipeline em poucos ativos para validar toda a infraestrutura.

Somente depois executar a pesquisa completa em todos os ativos e combinações.

Nunca começar com uma otimização gigantesca antes de validar a qualidade dos dados e a ausência de look-ahead bias.
