# Investigação de Padrões de Reversão em Range Bars

## Objetivo

Investigar uma base CSV de candlesticks do tipo **Range**, buscando identificar padrões que antecipem reversões com movimento posterior mínimo de **3 ranges**, mantendo o risco de retorno contra a reversão limitado a **1,3 × o range** a partir do fechamento do candle de reversão.

O objetivo final é:

1. Identificar padrões estatisticamente relevantes.
2. Determinar quais características aumentam a previsibilidade da reversão.
3. Validar os resultados fora da amostra.
4. Propor a melhor forma de transformar os achados em um indicador **MQL5** utilizável em tempo real.

---

## Estrutura dos dados

O CSV contém:

* `DATA`: data/hora da barra.
* `OPEN`
* `HIGH`
* `LOW`
* `CLOSE`
* `TICKVOL`: interpretar como **agressão de compra**.
* `VOL`: interpretar como **agressão de venda**.
* `SPREAD`: interpretar como **tempo de formação da barra, em milissegundos**.

O tamanho do range deve ser calculado por:

`Range = HIGH - LOW`

Os ranges deveriam ser iguais nas barras, com a exceção de barras de fechamento que podem fechar "incompletas". As barras contêm wicks. Caso considere necessário, valide empiricamente essa característica antes da análise.

---

## Definição das barras

As barras são direcionais:

* Barra de alta: `CLOSE > OPEN`
* Barra de baixa: `CLOSE < OPEN`

Como as barras fecham na extremidade correspondente à direção:

* Candle de alta: fechamento na máxima, podendo existir wick apenas abaixo.
* Candle de baixa: fechamento na mínima, podendo existir wick apenas acima.

Calcular também:

`Body = abs(CLOSE - OPEN)`

`BodyRatio = Body / Range`

e o tamanho do wick oposto à direção do fechamento.

---

# Padrões de reversão

## Padrão 1 — 2 + reversão fraca

Procurar:

* duas barras consecutivas na mesma direção;
* terceira barra, mais recente, na direção contrária;
* a terceira barra deve possuir `BodyRatio <= 0,50`.

Exemplo:

`↑ ↑ ↓`

ou

`↓ ↓ ↑`

A terceira barra é o **candle de reversão**.

Investigar se características internas da terceira barra, especialmente agressões e tempo de formação, aumentam significativamente a probabilidade de continuação da reversão.

---

## Padrão 2 — impulso + reversão forte

Procurar:

* três barras consecutivas;
* as duas primeiras na mesma direção;
* a segunda barra deve possuir `BodyRatio >= 0,70`;
* a terceira barra deve ser contrária e possuir `BodyRatio >= 0,70`.

Exemplo:

`↑ ↑ ↓`

ou

`↓ ↓ ↑`

Neste padrão, a análise do sinal deve considerar principalmente os **dois últimos candles**, sendo obrigatório que exista o terceiro candle mais antigo e que ele tenha a mesma direção do segundo.

A terceira barra (mais recente) é o candle de reversão.

---

# Definição objetiva de sucesso

Para cada candle de reversão, avaliar exclusivamente o comportamento **posterior ao fechamento desse candle**.

A reversão será considerada bem-sucedida quando o preço:

1. atingir pelo menos **3 × Range** na direção da reversão;
2. antes disso, não retornar mais que **1,3 × Range** contra a direção da reversão, a partir do fechamento do candle de reversão.

Formalizar:

### Reversão de alta

Entrada conceitual no fechamento `C`.

* Alvo: `C + 3R`
* Limite adverso: `C - 1,3R`

### Reversão de baixa

* Alvo: `C - 3R`
* Limite adverso: `C + 1,3R`

onde `R` é o range do candle de reversão.

Determinar também:

* tempo até atingir 3R;
* número de barras até 3R;
* máxima excursão favorável (MFE);
* máxima excursão adversa (MAE);
* se alvo e limite adverso ocorrerem na mesma barra, estabelecer uma regra conservadora e documentá-la.

Não utilizar informações futuras na construção das features do candle de sinal.

---

# Features a investigar

Para cada padrão, investigar pelo menos:

### Preço / estrutura

* `BodyRatio`
* tamanho do wick / range
* posição do OPEN dentro do range
* tamanho relativo das três barras
* sequência de ranges
* expansão/contração do range
* distância entre fechamentos
* aceleração do movimento
* número de barras anteriores na mesma direção

### Agressão

Como:

* `BuyAggression = TICKVOL`
* `SellAggression = VOL`

calcular:

* saldo: `TICKVOL - VOL`
* agressão total: `TICKVOL + VOL`
* razão compra/venda
* saldo normalizado
* agressão de compra normalizada
* agressão de venda normalizada
* agressão relativa às barras anteriores
* variação da agressão entre candles
* divergência entre direção do candle e agressão

Testar especialmente se ocorre **exaustão ou absorção**, por exemplo, candle de reversão com agressão aparentemente incompatível com sua direção.

### Tempo

Usar `SPREAD` como duração da barra em milissegundos.

Investigar:

* duração absoluta;
* duração normalizada;
* mudança de duração entre candles;
* aceleração/desaceleração do tempo de formação;
* relação entre duração e range;
* relação entre duração e agressão.

---

# Features temporais / Lags

Testar lags das principais features, especialmente:

* agressão de compra;
* agressão de venda;
* saldo;
* agressão total;
* BodyRatio;
* range;
* duração;
* relação agressão/range;
* relação agressão/tempo.

Avaliar janelas anteriores suficientes para capturar contexto, sem criar dimensionalidade excessiva.

Evitar gerar centenas de features indiscriminadamente. Priorizar features economicamente interpretáveis e posteriormente eliminar redundâncias/correlações.

---

# Metodologia estatística

Antes de utilizar Machine Learning, estabelecer um **baseline puramente estatístico**.

Para cada padrão calcular:

* quantidade de ocorrências;
* taxa de sucesso;
* taxa de falha;
* expectativa;
* distribuição de MAE;
* distribuição de MFE;
* mediana e percentis do movimento posterior;
* tempo médio/mediano até 3R;
* resultado por horário;
* resultado por direção;
* resultado por regime de volatilidade;
* resultado por intensidade de agressão.

Comparar os padrões entre si e contra um conjunto de candles aleatórios/controlados.

Evitar conclusões baseadas apenas em poucas ocorrências.

---

# Machine Learning

É permitido utilizar Machine Learning quando houver justificativa estatística.

Priorizar modelos tabulares, especialmente:

* CatBoost;
* LightGBM/XGBoost;
* Random Forest como baseline.

CatBoost é uma opção preferencial caso apresente desempenho competitivo.

O target principal deve ser algo equivalente a:

`SUCCESS = 1` se atingir +3R antes de -1,3R.

Investigar também modelos/regressões para:

* probabilidade de sucesso;
* MFE;
* MAE;
* tempo até o alvo.

Não utilizar somente acurácia. Avaliar:

* ROC-AUC;
* PR-AUC;
* precision;
* recall;
* F1;
* Brier score/calibração;
* expectativa por trade;
* distribuição de resultados;
* performance por threshold de probabilidade.

---

# Validação e prevenção de overfitting

A série é temporal. **Nunca utilizar split aleatório tradicional.**

Utilizar:

* treinamento em período passado;
* validação em período posterior;
* teste final completamente fora da amostra.

Preferencialmente utilizar walk-forward validation.

Toda transformação, normalização, seleção de features ou treinamento deve ser realizada respeitando a ordem temporal.

Investigar estabilidade dos resultados em diferentes períodos e regimes.

Um resultado só deve ser considerado relevante se permanecer razoavelmente estável fora da amostra.

---

# Feature Importance e explicabilidade

Identificar quais variáveis realmente contribuem para a previsão.

Utilizar, quando apropriado:

* CatBoost feature importance;
* SHAP;
* permutation importance;
* análise univariada/bivariada.

Procurar padrões interpretáveis, por exemplo:

> "A reversão tem maior probabilidade quando a agressão de venda aumenta, mas o candle fecha em alta, enquanto o tempo de formação aumenta."

Não aceitar um modelo simplesmente porque apresenta bom backtest. Buscar uma explicação operacional que possa ser implementada no indicador.

---

# Controle contra viés

Investigar explicitamente:

* look-ahead bias;
* leakage;
* duplicação de eventos;
* sobreposição de sinais;
* efeito de candles consecutivos;
* dependência entre amostras;
* diferenças de regime;
* quantidade mínima de ocorrências.

Se vários candles consecutivos forem classificados como sinais, avaliar se devem ser tratados como um único evento.

---

# Resultado esperado da investigação

Ao final, produzir um relatório contendo:

1. Definição exata dos dois padrões.
2. Quantidade de ocorrências.
3. Taxa de sucesso de cada padrão.
4. Distribuição MAE/MFE.
5. Expectativa.
6. Melhores features.
7. Importância das agressões.
8. Importância do tempo de formação.
9. Melhores combinações de features.
10. Performance out-of-sample.
11. Threshold de probabilidade recomendado.
12. Condições em que o sinal deve ser ignorado.
13. Comparação entre abordagem estatística e Machine Learning.
14. Limitações e riscos de overfitting.

---

# Implementação MQL5

Com base nos resultados, propor a arquitetura mais simples possível para um indicador MQL5.

O indicador deverá:

1. Detectar os dois padrões em tempo real.
2. Calcular as mesmas features utilizadas pelo modelo.
3. Gerar um score/probabilidade de reversão.
4. Diferenciar reversão de alta e de baixa.
5. Permitir configuração de thresholds.
6. Não utilizar dados futuros.
7. Produzir sinal somente após o fechamento da barra de reversão.

Avaliar duas arquiteturas:

### Opção A — regras estatísticas

Implementar diretamente as condições que apresentarem maior significância.

Preferir esta opção se poucas regras explicarem a maior parte da previsibilidade.

### Opção B — modelo Machine Learning

Caso o ML apresente ganho robusto out-of-sample:

* treinar o modelo externamente;
* exportá-lo para um formato compatível com MQL5, preferencialmente ONNX se adequado;
* implementar no indicador exatamente o mesmo pipeline de features utilizado no treinamento;
* validar numericamente que MQL5 e Python produzem as mesmas features e previsões.

O indicador não deve depender de recalcular ou consultar dados futuros.

---

# Critério final de sucesso

A investigação deve buscar **previsibilidade real e operacional**, não simplesmente encontrar padrões visualmente interessantes.

O padrão/modelo final deve demonstrar:

* vantagem estatística;
* número suficiente de ocorrências;
* estabilidade temporal;
* resultado consistente out-of-sample;
* relação clara entre features e probabilidade de reversão;
* possibilidade de implementação fiel em MQL5.

Se nenhum padrão apresentar vantagem estatisticamente robusta, declarar explicitamente que a investigação não encontrou evidência suficiente, em vez de otimizar excessivamente o modelo até produzir um resultado aparentemente positivo.


o arquivo csv com as barras se encontra em:
OHLC\XAUUSD_327_N_M1_202511041815_202608212148.csv