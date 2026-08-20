# CLAUDE.md — Investigação de Predição de Pontos de Virada no Renko 11R

## 1. Objetivo do projeto

Investigar, desenvolver, validar e eventualmente transformar em um indicador NTSL uma estratégia de **predição de pontos de virada no Renko 11R do mini índice (WIN)**.

A base possui:

- OHLC;
- wicks;
- agressão de compra;
- agressão de venda;
- duração da barra;
- quantidade;
- número de negócios.

O objetivo não é prever qualquer mudança de direção. O evento de interesse é especificamente:

> **2 ou 3 candles consecutivos em uma direção, seguidos por um candle de virada, e posteriormente pelo menos 2 ou 3 candles na nova direção.**

O indicador final deverá:

1. não repintar;
2. não utilizar nenhuma informação futura para gerar o sinal;
3. sinalizar no próprio candle de virada;
4. não esperar candle de confirmação;
5. desenhar/sinalizar a barra de virada somente depois que ela estiver fechada;
6. utilizar exclusivamente informações disponíveis até o fechamento da própria barra.

---

## 2. Arquivo de entrada

Path = C:\Users\Carlos\Documents\GitHub\Python\ohlc-renko\WINFUT\WINFUT_11R_AGB_AGS_BDURF_QT_TRD.csv

O CSV utiliza `;` como separador:

```text
Data;Abertura;Máxima;Mínima;Fechamento;AgressionVolBuy;AgressionVolSell;BarDurationF;Quantity;Trades
14/08/2026 18:22:56.914;170000;170010;169945;169975;1607;1496;2050;23406;2409
14/08/2026 18:21:24.449;169950;170000;169875;170000;3140;2151;1533;5291;1525
14/08/2026 18:21:24.449;169950;169950;169900;169900;0;1351;0;1351;201
```

### Regras de ingestão

- Detectar automaticamente encoding quando possível.
- Separador: `;`.
- Decimal numérico: ponto.
- `Data`: `dd/mm/yyyy HH:MM:SS.mmm`.
- Não ordenar cegamente pelo timestamp sem investigar duplicidades.
- Renko pode possuir timestamps iguais ou não estritamente crescentes.
- A **ordem das linhas é potencialmente a ordem correta das barras** e deve ser preservada/investigada.
- Antes de qualquer modelagem, produzir relatório de:
  - número de linhas;
  - timestamps duplicados;
  - timestamps fora de ordem;
  - valores nulos;
  - valores negativos/impossíveis;
  - range zero;
  - duração zero;
  - agressão total zero;
  - quantidade zero;
  - trades zero;
  - possíveis gaps.

Não remover dados silenciosamente. Toda exclusão deve ser registrada.

---

# 3. Princípio fundamental: evitar vazamento temporal

Este é um projeto de séries temporais.

**Nunca utilizar informação futura como feature.**

Para uma barra `t`, todas as features usadas para gerar a previsão precisam ser calculadas exclusivamente com:

```text
t, t-1, t-2, ...
```

Nunca usar:

```text
t+1, t+2, ...
```

nas features.

Informação futura pode ser usada **somente para construir o target durante o treinamento**, pois ela define se o evento que ocorreu em `t` realmente teve continuação.

O código deve manter claramente separados:

```text
FEATURES
TARGET
LIVE PREDICTION
```

---

# 4. Definição matemática das features principais

Para cada barra:

```text
Range = High - Low
```

Como o Renko pode eventualmente apresentar range zero, utilizar proteção numérica:

```text
RangeSafe = max(High - Low, epsilon)
```

O `epsilon` deve ser pequeno e documentado.

## 4.1 Agressão de compra normalizada

```text
AggBuyNorm = AgressionVolBuy / RangeSafe
```

## 4.2 Agressão de venda normalizada

```text
AggSellNorm = AgressionVolSell / RangeSafe
```

## 4.3 Saldo de agressão normalizado

```text
AggBalanceNorm =
    (AgressionVolBuy - AgressionVolSell) / RangeSafe
```

## 4.4 Soma das agressões normalizada

```text
AggTotalNorm =
    (AgressionVolBuy + AgressionVolSell) / RangeSafe
```

## 4.5 Quantidade normalizada

```text
QuantityNorm = Quantity / RangeSafe
```

## 4.6 Negócios normalizados

```text
TradesNorm = Trades / RangeSafe
```

Essas seis famílias são obrigatórias.

---

# 5. Informação temporal

Calcular uma média móvel aritmética simples de 20 períodos da duração da barra:

```text
DurationMA20 = SMA(BarDurationF, 20)
```

Feature temporal principal:

```text
DurationResidual = BarDurationF - DurationMA20
```

Esta é a feature de tempo solicitada.

Não substituir essa feature por uma razão ou z-score sem antes manter a feature original.

Também estudar versões adicionais, mas separadas:

```text
DurationRatio20 = BarDurationF / DurationMA20
```

e, se fizer sentido:

```text
DurationResidualPct =
    (BarDurationF - DurationMA20) / DurationMA20
```

Somente utilizar versões adicionais se a análise demonstrar valor.

---

# 6. Lags obrigatórios

Todas as features principais devem possuir versões defasadas.

Feature contemporânea:

```text
X_t
```

Lags:

```text
X_t-1
X_t-2
X_t-3
X_t-4
X_t-5
```

Começar com 5 lags.

Depois testar de forma controlada:

- 3 lags;
- 5 lags;
- 8 lags;
- 10 lags.

Não criar dezenas de lags indiscriminadamente sem medir custo, importância e overfitting.

Aplicar lags para:

- AggBuyNorm;
- AggSellNorm;
- AggBalanceNorm;
- AggTotalNorm;
- QuantityNorm;
- TradesNorm;
- DurationResidual.

A feature original da barra `t` também deve permanecer.

---

# 7. Features adicionais a investigar

Além das features solicitadas, investigar as seguintes.

## 7.1 Estrutura do candle

Todas preferencialmente normalizadas pelo range.

### Corpo

```text
Body = abs(Close - Open)
BodyNorm = Body / RangeSafe
```

### Direção

```text
Direction = sign(Close - Open)
```

Codificar de forma apropriada para o modelo.

### Posição do fechamento no range

```text
CloseLocation =
    (Close - Low) / RangeSafe
```

### Posição da abertura

```text
OpenLocation =
    (Open - Low) / RangeSafe
```

### Wick superior

```text
UpperWick =
    High - max(Open, Close)

UpperWickNorm =
    UpperWick / RangeSafe
```

### Wick inferior

```text
LowerWick =
    min(Open, Close) - Low

LowerWickNorm =
    LowerWick / RangeSafe
```

Essas features são especialmente importantes porque o objetivo envolve reversão.

---

# 8. Features de agressão adicionais

Investigar:

```text
AggImbalance =
    (Buy - Sell) / max(Buy + Sell, epsilon)
```

Isso é diferente de `AggBalanceNorm`.

Também:

```text
BuyShare =
    Buy / max(Buy + Sell, epsilon)

SellShare =
    Sell / max(Buy + Sell, epsilon)
```

E:

```text
AggBalanceChange =
    AggBalanceNorm_t - AggBalanceNorm_t-1
```

Possíveis acelerações:

```text
AggBalanceAcceleration =
    AggBalanceChange_t - AggBalanceChange_t-1
```

Testar essas features somente depois das features-base.

---

# 9. Features de volume e atividade

Investigar:

```text
Quantity / Trades
Trades / Quantity
AggTotal / Quantity
AggTotal / Trades
QuantityNorm / TradesNorm
```

Especial atenção para:

```text
QuantityPerTrade = Quantity / max(Trades, 1)
```

Isso pode representar uma mudança na intensidade média das negociações.

Também investigar desvios em relação à média móvel:

```text
QuantityResidual20
TradesResidual20
AggTotalResidual20
```

e versões relativas:

```text
QuantityRatio20
TradesRatio20
AggTotalRatio20
```

Não incluir todas simultaneamente no modelo final sem validação.

---

# 10. Features de contexto das últimas barras

Como o objetivo é detectar reversões após 2 ou 3 candles na mesma direção, estudar explicitamente a estrutura da sequência.

Exemplos:

```text
ConsecutiveUpCount
ConsecutiveDownCount
```

Essas features devem ser calculadas apenas até `t`.

Também investigar:

```text
BodyNormMean3
BodyNormMean5
AggBalanceNormMean3
AggBalanceNormMean5
AggTotalNormMean3
AggTotalNormMean5
DurationResidualMean3
DurationResidualMean5
```

E mudanças:

```text
CloseChange1
CloseChange2
CloseChange3
```

preferencialmente expressas em número de bricks ou normalizadas quando apropriado.

---

# 11. Features específicas de reversão

Investigar sinais de exaustão:

### Wick contra a tendência

Exemplo para tendência de alta:

```text
UpperWickNorm
AggBalanceNorm
AggBalanceChange
CloseLocation
```

Para tendência de baixa:

```text
LowerWickNorm
AggBalanceNorm
AggBalanceChange
CloseLocation
```

Não assumir antecipadamente que uma feature é boa. Medir.

Também testar:

- divergência entre direção do candle e saldo de agressão;
- aumento de agressão sem progresso de preço;
- queda de agressão durante sequência direcional;
- aumento anormal da duração;
- redução anormal da duração;
- aumento de volume sem aumento proporcional do deslocamento.

---

# 12. Definição do target

O target precisa representar exatamente o evento operacional.

Devem ser investigadas pelo menos estas versões.

## Target A — reversão após 2 candles

Para uma barra `t`:

### Reversão para cima

Condição prévia:

```text
Direction[t-2] = DOWN
Direction[t-1] = DOWN
```

e barra `t` representa a virada:

```text
Direction[t] = UP
```

Depois, exigir continuação futura:

```text
Direction[t+1] = UP
Direction[t+2] = UP
```

Target:

```text
1 = reversão para cima confirmada pela continuação
0 = caso contrário
```

### Reversão para baixo

Analogamente:

```text
UP
UP
DOWN
DOWN
DOWN
```

ou, conforme a definição operacional, estudar:

```text
UP
UP
DOWN
DOWN
```

O importante é testar explicitamente as variantes e comparar.

---

# 13. Target B — reversão após 3 candles

Investigar:

```text
DOWN
DOWN
DOWN
UP
UP
UP
```

e:

```text
UP
UP
UP
DOWN
DOWN
DOWN
```

Também testar continuação mínima de 2 candles:

```text
DOWN DOWN DOWN UP UP
```

e:

```text
UP UP UP DOWN DOWN
```

---

# 14. Não confundir target de pesquisa com sinal operacional

O target pode utilizar:

```text
t+1
t+2
t+3
```

para saber se uma reversão ocorrida em `t` foi realmente válida.

Entretanto, o indicador NTSL **não poderá utilizar essas barras futuras para emitir o sinal**.

Fluxo correto:

```text
                    TREINAMENTO
                         |
              target usa t+1/t+2/t+3
                         |
                         v
                  modelo treinado
                         |
                         v
                    LIVE / NTSL
                         |
             features somente até t
                         |
                         v
             sinal no fechamento de t
```

---

# 15. Definir claramente o que é "virada"

Não assumir que qualquer candle de cor oposta seja uma virada.

Criar pelo menos três classes de investigação:

### Classe 0
Não é virada relevante.

### Classe 1
Virada para cima.

### Classe 2
Virada para baixo.

Inicialmente também pode ser estudado um problema binário:

```text
REVERSAO = 0/1
```

e posteriormente:

```text
DIRECAO = UP/DOWN
```

Comparar os dois desenhos.

---

# 16. Modelo estatístico antes de ML

Antes de utilizar CatBoost, construir modelos baseline.

Obrigatórios:

1. regra simples baseada apenas na sequência de candles;
2. regressão logística;
3. árvore simples;
4. Random Forest ou equivalente;
5. CatBoost.

O objetivo é descobrir quanto ganho real vem das features.

Se CatBoost não superar significativamente os baselines fora da amostra, não utilizar CatBoost apenas por ser mais sofisticado.

---

# 17. CatBoost

Se ML for necessário, utilizar **CatBoost** como candidato principal.

Motivos:

- bom desempenho em dados tabulares;
- capacidade de capturar interações não lineares;
- regularização;
- menor necessidade de engenharia manual de interações;
- possibilidade de limitar profundidade das árvores.

Começar conservadoramente.

Exemplo inicial de busca:

```text
depth: 3, 4, 5, 6
learning_rate: 0.02, 0.05, 0.10
iterations: controlado por early stopping
l2_leaf_reg: valores moderados
loss_function: Logloss
eval_metric: AUC
```

Não realizar uma busca gigantesca.

O principal objetivo é **generalização fora da amostra**, não maximização do score in-sample.

---

# 18. Validação temporal obrigatória

Nunca usar:

```text
train_test_split(..., shuffle=True)
```

Nunca embaralhar as barras.

Usar validação temporal.

Exemplo:

```text
TRAIN 1 -> VALIDATION 1
TRAIN 2 -> VALIDATION 2
TRAIN 3 -> VALIDATION 3
...
```

Preferir walk-forward / expanding window.

Como os targets utilizam até 3 candles futuros, inserir um **embargo temporal mínimo de 3 barras** entre treino e validação quando necessário para evitar sobreposição dos eventos.

Exemplo conceitual:

```text
TRAIN TRAIN TRAIN TRAIN TRAIN
                         GAP GAP GAP
                                     TEST TEST TEST
```

O gap deve ser parametrizável.

---

# 19. Métricas

Não avaliar apenas accuracy.

Obrigatório calcular:

- precision;
- recall;
- F1;
- ROC AUC;
- PR AUC;
- matriz de confusão;
- taxa de falsos positivos;
- taxa de falsos negativos;
- quantidade de sinais;
- sinais por dia;
- distribuição dos sinais;
- performance por horário;
- performance por regime de mercado.

Para o uso operacional, precision e expectativa por sinal são especialmente importantes.

---

# 20. Métrica econômica

Depois da avaliação estatística, simular uma operação simples.

Para cada sinal:

- entrada no fechamento da barra de virada;
- verificar deslocamento futuro;
- medir se atingiu +2 bricks;
- medir se atingiu +3 bricks;
- medir MFE;
- medir MAE;
- medir tempo até +2/+3 bricks;
- medir excursão adversa antes do objetivo.

Não otimizar diretamente para uma única regra de stop/target antes de entender o comportamento estatístico.

---

# 21. Evitar overfitting de features

Criar três conjuntos:

```text
BASE
EXTENDED
FINAL
```

### BASE

Somente:

- AggBuyNorm
- AggSellNorm
- AggBalanceNorm
- AggTotalNorm
- QuantityNorm
- TradesNorm
- DurationResidual
- lags dessas features

### EXTENDED

Adicionar:

- candle structure;
- wick;
- close location;
- imbalance;
- volume/trade relationships;
- sequence/context features.

### FINAL

Somente features que demonstrarem valor consistente no walk-forward.

Não selecionar features apenas pelo feature importance de um único treinamento.

---

# 22. Feature importance

Para CatBoost analisar:

- Feature Importance;
- SHAP, se viável;
- importância por fold;
- estabilidade da importância.

Uma feature que aparece como importante em apenas um período e desaparece nos demais deve ser tratada como suspeita.

Procurar features que sejam:

```text
importantes
+
estáveis
+
causalmente disponíveis
+
úteis fora da amostra
```

---

# 23. Teste de robustez

Depois de encontrar um modelo promissor, executar:

### Teste por período

Separar por:

- meses;
- semanas;
- horários.

### Teste por direção

Separar:

- reversões para cima;
- reversões para baixo.

### Teste por duração

Separar barras:

- muito rápidas;
- normais;
- muito lentas.

### Teste por volatilidade

Criar regimes com base em medidas disponíveis somente até `t`.

O modelo precisa funcionar em múltiplos regimes.

---

# 24. Teste de estabilidade

Variar deliberadamente:

- 2 versus 3 candles de pré-sequência;
- 2 versus 3 candles de continuação;
- número de lags;
- limiar de probabilidade;
- período da média de duração;
- parâmetros do CatBoost.

Se uma pequena alteração destruir o resultado, considerar o modelo superajustado.

---

# 25. Threshold do modelo

Não assumir:

```text
probability > 0.5
```

como regra final.

Estudar:

```text
0.50
0.55
0.60
0.65
0.70
0.75
0.80
```

e construir uma curva:

```text
threshold
x
precision
x
number of signals
x
expected excursion
```

O threshold final deve ser escolhido com dados de validação, nunca com o conjunto de teste final.

---

# 26. Controle rigoroso de look-ahead

O projeto deve possuir testes automatizados para detectar vazamento.

Criar uma função conceitual:

```python
assert_no_future_dependency()
```

Uma forma de testar:

1. calcular a previsão da barra `t`;
2. alterar artificialmente os dados das barras `t+1` em diante;
3. recalcular a previsão de `t`;
4. verificar que a previsão não mudou.

Se mudar, existe vazamento.

Esse teste é obrigatório antes da exportação para NTSL.

---

# 27. Geração do indicador NTSL

O objetivo final é gerar um indicador NTSL para ProfitChart.

Requisitos absolutos:

### Não repintar

Depois que a barra `t` fechar, o sinal de `t` não pode mudar.

### Não esperar confirmação

Não usar:

```text
t+1
```

para desenhar o sinal de `t`.

### Sinal no próprio candle

O indicador deve identificar a oportunidade no fechamento da barra de virada.

Conceitualmente:

```text
barra t fecha
      |
      +--> calcula features usando t e passado
      |
      +--> calcula probabilidade
      |
      +--> aplica threshold
      |
      +--> desenha sinal em t
```

Nunca:

```text
barra t fecha
barra t+1 fecha
barra t+2 fecha
      |
      +--> desenha sinal em t
```

---

# 28. Exportação CatBoost -> NTSL

O CatBoost não deve ser simplesmente abandonado por não existir runtime CatBoost no NTSL.

Investigar uma destas estratégias:

1. exportar as árvores do CatBoost;
2. converter cada árvore em regras NTSL;
3. somar os outputs das árvores;
4. reproduzir a transformação final do modelo;
5. calcular a probabilidade final dentro do NTSL.

Se a conversão automática for possível, criar:

```text
model_to_ntsl.py
```

que recebe o modelo treinado e gera:

```text
model_generated.ntsl
```

ou um arquivo `.txt` contendo o bloco NTSL gerado.

---

# 29. Não inventar sintaxe NTSL

Antes de gerar o código final:

- verificar a sintaxe NTSL efetivamente suportada;
- compilar no Profit quando possível;
- corrigir erros de compilação;
- evitar funções ou recursos que não estejam disponíveis.

O código final deve ser simples o suficiente para auditoria.

---

# 30. Arquitetura esperada do projeto

Criar uma estrutura semelhante a:

```text
project/
│
├── CLAUDE.md
│
├── data/
│   ├── raw/
│   └── processed/
│
├── src/
│   ├── load_data.py
│   ├── validate_data.py
│   ├── features.py
│   ├── targets.py
│   ├── baselines.py
│   ├── train_catboost.py
│   ├── walk_forward.py
│   ├── evaluate.py
│   ├── robustness.py
│   ├── explain.py
│   └── model_to_ntsl.py
│
├── models/
│
├── reports/
│
├── results/
│
└── ntsl/
    └── reversal_detector.ntsl
```

---

# 31. Pipeline obrigatório

O pipeline deve ser reproduzível:

```text
CSV
 |
 v
VALIDAÇÃO
 |
 v
FEATURE ENGINEERING
 |
 v
TARGET GENERATION
 |
 v
BASELINES
 |
 v
WALK-FORWARD
 |
 v
CATBOOST
 |
 v
ROBUSTEZ
 |
 v
THRESHOLD
 |
 v
ECONOMIC SIMULATION
 |
 v
MODEL EXPORT
 |
 v
NTSL
```

Cada etapa deve salvar resultados.

---

# 32. Reprodutibilidade

Fixar seeds quando aplicável.

Salvar:

- configuração;
- features utilizadas;
- número de lags;
- período das médias;
- parâmetros do modelo;
- threshold;
- períodos de treino;
- períodos de validação;
- métricas;
- versão das bibliotecas.

Nunca sobrescrever resultados importantes sem criar versão.

---

# 33. Experimentos

Criar um identificador para cada experimento.

Exemplo:

```text
EXP001_BASE_LOGISTIC
EXP002_BASE_CATBOOST
EXP003_EXTENDED_CATBOOST
EXP004_LAGS10_CATBOOST
EXP005_WALKFORWARD
```

Cada experimento deve possuir:

```text
config
metrics
feature_importance
predictions
```

---

# 34. O que NÃO fazer

Não:

- embaralhar a série;
- usar dados futuros nas features;
- usar confirmação posterior no indicador;
- otimizar threshold no teste final;
- selecionar features somente por resultado in-sample;
- criar centenas de features sem controle;
- remover outliers sem justificativa;
- substituir zeros silenciosamente;
- normalizar utilizando estatísticas calculadas sobre todo o dataset;
- calcular médias móveis usando dados futuros;
- utilizar scaler ajustado no dataset completo;
- usar target futuro como feature;
- desenhar retroativamente sinais históricos que dependeriam de confirmação futura.

---

# 35. Normalização e escalonamento

As features principais já são normalizadas por:

```text
Range = High - Low
```

Não aplicar automaticamente StandardScaler/MinMaxScaler.

CatBoost geralmente não necessita disso.

Se outro modelo exigir scaling:

- ajustar o scaler apenas no treino;
- aplicar ao validation/test;
- nunca ajustar no dataset inteiro.

---

# 36. Questão importante sobre Renko

Não assumir que:

```text
Range = tamanho do brick
```

para todas as barras.

A presença de wicks faz com que:

```text
High - Low
```

possa variar significativamente entre:

- bricks de continuidade;
- bricks de reversão;
- barras com wick grande.

Isso é precisamente uma razão para estudar a normalização solicitada.

O projeto deve produzir estatísticas comparando:

```text
Range
BodyNorm
UpperWickNorm
LowerWickNorm
```

entre:

- continuidade;
- reversão;
- reversão vencedora;
- reversão falsa.

---

# 37. Primeira análise exploratória obrigatória

Antes de qualquer ML, produzir:

1. distribuição do range;
2. distribuição de duração;
3. distribuição de agressão de compra;
4. distribuição de agressão de venda;
5. distribuição do saldo;
6. distribuição da quantidade;
7. distribuição de trades;
8. correlação entre features;
9. distribuição das features normalizadas;
10. taxa-base dos eventos de reversão.

Depois responder:

```text
Qual a frequência real do evento?
Qual a diferença entre reversões para cima e para baixo?
As reversões possuem maior range?
As reversões possuem wicks maiores?
Existe mudança de agressão antes da virada?
Existe alteração de duração?
Existe alteração de quantidade/trades?
```

---

# 38. Análise condicional

Para cada target, comparar:

```text
P(feature | reversão)
vs
P(feature | não reversão)
```

E principalmente:

```text
feature[t]
feature[t-1]
feature[t-2]
```

A pergunta central é:

> Existe informação disponível ANTES ou NO PRÓPRIO candle de virada que diferencie uma reversão válida de uma falsa?

Não usar informação posterior para responder essa pergunta.

---

# 39. Baseline extremamente importante

Criar um baseline puramente estrutural:

```text
Se houver 2 ou 3 candles consecutivos em uma direção
e o candle atual inverter a direção,
gerar sinal.
```

Depois comparar:

```text
Baseline
vs
Baseline + agressão
vs
Baseline + volume
vs
Baseline + tempo
vs
Baseline + todas as features
vs
CatBoost
```

Isso permitirá descobrir qual grupo de informação realmente acrescenta poder preditivo.

---

# 40. Pergunta de pesquisa principal

A investigação deve responder objetivamente:

> **As características de agressão, volume, negócios, duração e estrutura do candle no próprio candle de virada permitem identificar, antes de qualquer confirmação futura, quais reversões terão continuação de pelo menos 2 ou 3 candles?**

Se a resposta for não, não forçar um modelo.

Se a resposta for sim, determinar:

- quais features;
- em quais regimes;
- com qual threshold;
- com qual precisão;
- com qual frequência;
- com qual expectativa de deslocamento.

---

# 41. Critério de sucesso

Não considerar sucesso simplesmente:

```text
AUC > 0.5
```

O resultado precisa demonstrar simultaneamente:

1. melhora estatisticamente significativa sobre o baseline;
2. estabilidade em walk-forward;
3. estabilidade temporal;
4. estabilidade entre direções;
5. ausência de look-ahead;
6. quantidade operacionalmente útil de sinais;
7. precision suficiente para o objetivo;
8. comportamento econômico plausível;
9. possibilidade de implementação sem repaint no NTSL.

---

# 42. Entregáveis finais

Ao terminar a investigação, entregar:

### 1. Relatório

```text
reports/final_report.md
```

Contendo:

- metodologia;
- definição dos targets;
- features;
- resultados;
- métricas;
- importância das features;
- testes de robustez;
- limitações;
- conclusão.

### 2. Modelo

Salvar modelo CatBoost final, se aplicável.

### 3. Dataset de features

Salvar dataset processado para auditoria.

### 4. Predições out-of-sample

Salvar:

```text
timestamp
prediction
probability
target
fold
```

### 5. Indicador NTSL

Entregar:

```text
ntsl/ReversalDetectorClaude.ntsl
```

O indicador precisa ser explicitamente identificado como:

```text
NON-REPAINT
NO-CONFIRMATION
SIGNAL-ON-CLOSED-BAR
```

O indicador irá desenhar uma seta acima do candle de virada descendente. Exemplo : PlotText("▼", vermelho, 2, TamFonte, High[p] + OffsetFrac * mRng);

O indicador irá desenhar uma seta abaixo do candle de virada ascendente. Exemplo : PlotText("▲", verde, 0, TamFonte, Low[p] - OffsetFrac * mRng);
---

# 43. Regra operacional final

O indicador deve funcionar conceitualmente assim:

```text
Candle t ainda aberto
        |
        | nenhuma decisão final
        v
Candle t fecha
        |
        v
calcula OHLC + agressão + volume + tempo
        |
        v
calcula features de t e lags
        |
        v
modelo
        |
        v
probabilidade
        |
        v
threshold
        |
   +----+----+
   |         |
 não       sim
   |         |
   v         v
 nada    desenha sinal em t
```

**Não existe etapa de confirmação.**

As barras `t+1`, `t+2` e `t+3` existem somente no dataset histórico para determinar o target durante pesquisa/treinamento. Elas nunca podem participar da decisão do indicador em tempo real.

---

# 44. Ordem de execução para Claude Code

Executar nesta ordem:

1. inspecionar o CSV real;
2. validar integridade e ordenação;
3. criar pipeline de ingestão;
4. criar features BASE;
5. criar lags;
6. criar targets 2/3 candles;
7. fazer análise exploratória;
8. executar baselines;
9. executar CatBoost;
10. executar walk-forward;
11. analisar feature importance/SHAP;
12. testar robustez;
13. escolher features estáveis;
14. escolher threshold usando validação;
15. executar teste final completamente fora da amostra;
16. simular comportamento econômico;
17. somente então criar o exportador NTSL;
18. gerar o indicador NTSL;
19. auditar o indicador contra as previsões Python;
20. documentar tudo.

**Não pular diretamente para o NTSL.**

O NTSL é o último estágio de uma investigação quantitativa, não o ponto de partida.

---

# 45. Auditoria final obrigatória

Antes de considerar o projeto concluído, responder explicitamente:

```text
[ ] Features usam somente passado + candle atual?
[ ] Target usa futuro somente na fase de treinamento?
[ ] Nenhum scaler foi ajustado usando teste?
[ ] Nenhum split aleatório foi utilizado?
[ ] Existe embargo temporal?
[ ] Walk-forward foi realizado?
[ ] Baseline foi comparado?
[ ] CatBoost foi comparado fora da amostra?
[ ] Feature importance é estável?
[ ] Threshold foi escolhido sem usar o teste final?
[ ] O teste final é realmente out-of-sample?
[ ] O modelo foi convertido para NTSL?
[ ] O NTSL usa somente dados até a barra atual?
[ ] O sinal aparece no fechamento da barra de virada?
[ ] O NTSL não espera t+1?
[ ] O NTSL não repinta?
[ ] O NTSL foi comparado com as previsões Python?
```

Se qualquer resposta for `não`, o projeto não deve ser considerado finalizado.
