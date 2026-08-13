# Detector Automático de Níveis Importantes

## 1. Objetivo

Desenvolver um projeto Python capaz de analisar um histórico de aproximadamente 5 anos de candles de 1 minuto e identificar automaticamente **níveis de preço importantes**.

O resultado principal deve ser uma lista de **linhas horizontais de preço**, cada uma acompanhada de um score que represente sua relevância histórica.

O sistema **não deve classificar os níveis como suporte ou resistência**.

O sistema **não deve criar zonas de preço**.

Cada nível deve ser representado por **um único preço**, correspondente ao preço central estimado pelo algoritmo.

---

## 2. Premissas fundamentais

Estas premissas são obrigatórias:

### 2.1 Não diferenciar suporte e resistência

O algoritmo deve considerar simplesmente:

> "Este preço é historicamente importante?"

Não deve existir uma classificação:

```text
SUPORTE
RESISTÊNCIA
```

Um mesmo nível pode ser relevante independentemente da direção do movimento.

O nível deve ser tratado como uma entidade neutra:

```text
Level(price=...)
```

---

### 2.2 Não utilizar zonas

Não utilizar:

```text
price_low
price_high
zone_width
```

nem representar um nível como:

```text
129800 - 129900
```

O resultado deve ser sempre uma linha:

```text
129850
```

A tolerância utilizada internamente para determinar se diferentes eventos pertencem ao mesmo nível é permitida e necessária, mas ela **não deve fazer parte da representação final do nível**.

Exemplo:

```text
Eventos detectados:

129840
129850
129860
129850
129855
```

podem resultar em:

```text
129852
```

Esse valor é o nível final.

---

# 3. Conceito de nível importante

Um nível importante é um preço no qual o mercado apresentou, ao longo do histórico, evidências de comportamento não aleatório.

Essas evidências podem incluir:

* múltiplos testes;
* rejeições significativas;
* movimentos relevantes após o teste;
* ocorrência em diferentes dias;
* ocorrência em diferentes períodos;
* persistência temporal;
* grande volume;
* associação com swings importantes;
* confluência com níveis derivados de outras escalas temporais;
* reincidência após longos períodos.

O objetivo não é simplesmente encontrar máximas e mínimas.

O objetivo é encontrar preços que possuem **importância estatística/estrutural para o mercado**.

---

# 4. Dados de entrada

O projeto deve aceitar candles de 1 minuto contendo, no mínimo:

```text
datetime
open
high
low
close
```

Idealmente:

```text
datetime
open
high
low
close
volume
```

O código deve ser preparado para trabalhar com volume ausente.

Exemplo:

```csv
datetime,open,high,low,close,volume
2021-01-04 09:00:00,120000,120050,119950,120025,1532
...
```

---

# 5. Normalização

Antes da análise:

1. ordenar por datetime;
2. remover duplicatas;
3. verificar gaps;
4. verificar candles inválidos;
5. normalizar timezone quando necessário;
6. determinar tick size;
7. trabalhar internamente com preços normalizados ao tick.

Não assumir que:

```python
round(price, 2)
```

é uma forma válida de normalização.

Usar o tick size do ativo.

Exemplo:

```python
normalized_price = round(price / tick_size) * tick_size
```

---

# 6. Volatilidade

O algoritmo não deve utilizar somente distâncias fixas em pontos.

Uma distância de 100 pontos pode ser enorme em um período e pequena em outro.

Calcular pelo menos:

```text
ATR
```

em uma ou mais escalas temporais.

A volatilidade deve ser utilizada para:

* determinar o que constitui uma reação significativa;
* determinar a distância mínima entre eventos;
* evitar considerar microvariações como eventos independentes;
* parametrizar clustering.

Exemplo conceitual:

```python
reaction_threshold = ATR * 0.25
```

Os valores devem ser parâmetros configuráveis, não hard-coded.

---

# 7. Detecção de eventos

A primeira etapa da detecção deve gerar **eventos candidatos**.

Um evento representa uma região temporal em que o mercado interagiu de maneira significativa com determinado preço.

Não considerar cada candle como um evento.

Por exemplo:

```text
09:30
09:31
09:32
09:33
09:34
```

com o preço oscilando próximo do mesmo nível deve ser tratado como **um único evento**, e não cinco testes.

---

# 8. Eventos independentes

Dois eventos próximos no tempo somente devem ser considerados independentes quando o mercado tiver se afastado suficientemente do preço.

Criar um mecanismo para definir:

```text
minimum_event_separation
```

preferencialmente relacionado ao ATR.

Exemplo conceitual:

```python
minimum_separation = 0.5 * ATR
```

Isso deve ser configurável.

---

# 9. Preço representativo do evento

Cada evento deve possuir um preço representativo.

Avaliar pelo menos:

* high;
* low;
* close;
* preço médio;
* preço do candle de maior reação.

A implementação deve permitir experimentar diferentes métodos.

O método escolhido deve ser configurável.

Exemplo:

```python
event_price_method = "reaction_price"
```

---

# 10. Reação

Um evento deve receber uma medida de reação posterior.

Para cada evento, calcular:

```text
maximum favorable excursion
```

durante diferentes horizontes:

```text
5 minutos
15 minutos
30 minutos
60 minutos
```

ou outros horizontes configuráveis.

Não existe conceito de compra/venda.

Portanto, a reação deve ser **direcionalmente neutra**.

O algoritmo deve medir simplesmente:

> quanto o preço se afastou do nível após interagir com ele?

Exemplo:

```text
evento = 130000

preço posteriormente se deslocou:

+500 pontos
```

ou:

```text
-500 pontos
```

Ambos representam uma reação de:

```text
500 pontos
```

Portanto:

```python
reaction = abs(max_excursion)
```

ou uma medida equivalente que não dependa de suporte/resistência.

---

# 11. Intensidade da reação

Normalizar a reação pela volatilidade.

Exemplo:

```python
normalized_reaction = reaction / ATR
```

Assim podemos comparar eventos de períodos com diferentes regimes de volatilidade.

Exemplo:

```text
Reação A = 300 pontos
ATR = 100

normalized = 3.0 ATR

Reação B = 300 pontos
ATR = 500

normalized = 0.6 ATR
```

O primeiro evento é muito mais relevante.

---

# 12. Swing points

Detectar swing highs e swing lows como fontes adicionais de eventos.

Porém:

**não transformar swing high e swing low em tipos diferentes de nível.**

Ambos são simplesmente:

```text
candidate level
```

Exemplo:

```text
swing high  → evento em 130500
swing low   → evento em 130500
```

ambos contribuem para o mesmo nível:

```text
130500
```

---

# 13. Múltiplas escalas temporais

O sistema deve considerar diferentes escalas.

No mínimo:

```text
1 minuto
5 minutos
15 minutos
1 hora
1 dia
1 semana
```

As séries maiores podem ser derivadas dos candles de 1 minuto.

O objetivo é permitir que um preço seja identificado como importante em diferentes escalas.

Por exemplo:

```text
130000

evento intraday
+ swing de 15m
+ swing de 1h
+ máxima diária
```

Isso deve aumentar a relevância do nível.

---

# 14. Clustering dos eventos

Depois de gerar os eventos, agrupá-los por proximidade de preço.

O objetivo é transformar:

```text
129980
130000
130020
130005
129995
130015
```

em um único nível:

```text
130003
```

O algoritmo deve inicialmente avaliar:

* DBSCAN;
* clustering hierárquico;
* KDE.

A primeira implementação pode utilizar DBSCAN.

---

# 15. Distância do clustering

A distância utilizada pelo clustering deve ser adaptativa.

Não utilizar simplesmente:

```python
eps = 50
```

sem considerar o ativo.

Idealmente:

```python
eps = ATR * clustering_factor
```

com posterior normalização ao tick size.

O parâmetro deve ser configurável.

---

# 16. Preço final do nível

Cada cluster representa um único nível.

Testar pelo menos:

```text
média
mediana
média ponderada
mediana ponderada
preço de maior densidade
```

A ponderação pode considerar:

* intensidade da reação;
* volume;
* timeframe;
* recência.

O resultado final deve ser:

```python
level.price
```

um único valor.

Nunca uma zona.

---

# 17. Score do nível

Cada nível deve possuir um score.

Exemplo:

```python
Level(
    price=130000,
    score=87.4
)
```

O score deve considerar múltiplos fatores.

Sugestão inicial:

```text
score =
    touch_score
    + reaction_score
    + temporal_score
    + timeframe_score
    + volume_score
    + recency_score
    + confluence_score
```

Os pesos devem ser configuráveis.

Não assumir que esses pesos são definitivos.

---

# 18. Número de eventos

Mais eventos independentes devem aumentar o score.

Porém, não usar simplesmente:

```python
score += number_of_events
```

pois isso pode favorecer níveis muito antigos ou períodos de alta atividade.

Considerar:

```text
número de eventos
número de dias diferentes
número de semanas diferentes
número de meses diferentes
```

Um nível que aparece em 30 candles consecutivos não deve ser considerado 30 vezes mais importante.

---

# 19. Distribuição temporal

A persistência histórica deve ser valorizada.

Exemplo:

### Nível A

```text
20 eventos
todos em 2024-03-15
```

### Nível B

```text
15 eventos

2022
2023
2024
2025
2026
```

O nível B pode ser mais relevante apesar de possuir menos eventos.

Criar métricas como:

```text
unique_days
unique_weeks
unique_months
historical_span
```

---

# 20. Recência

A recência deve influenciar o score, mas não apagar níveis antigos.

Utilizar decay configurável.

Exemplo:

```python
recency_weight = exp(-age / half_life)
```

Importante:

Um nível antigo que continua recebendo novos testes deve recuperar relevância.

---

# 21. Volume

Se volume estiver disponível, utilizá-lo como informação adicional.

Não fazer com que volume seja obrigatório.

Possíveis métricas:

```text
volume no evento
volume relativo
volume / média do período
volume profile associado
```

Normalizar volume para evitar que anos diferentes tenham pesos incompatíveis.

---

# 22. Confluência

Confluência não significa criar múltiplas linhas.

Se diferentes métodos apontarem para aproximadamente o mesmo preço:

```text
swing 15m        → 130000
swing 1h         → 130010
máxima diária    → 129995
KDE              → 130005
```

o resultado deve continuar sendo:

```text
130002
```

mas o score deve aumentar.

Confluência é uma propriedade do nível, não uma nova linha.

---

# 23. KDE

Implementar posteriormente uma alternativa baseada em Kernel Density Estimation.

A ideia é construir uma distribuição de densidade dos preços associados a eventos relevantes.

Exemplo conceitual:

```text
densidade
   ^
   |
   |          /\
   |         /  \              /\
   |   /\   /    \            /  \
   |__/  \_/      \__________/    \____
   +--------------------------------------> preço
```

Os máximos locais da densidade são candidatos a níveis.

O KDE não deve necessariamente substituir o clustering.

Permitir comparar os dois métodos.

---

# 24. Níveis conhecidos

Além dos níveis estatísticos, criar uma categoria de eventos baseada em referências de mercado:

```text
máxima diária
mínima diária
fechamento diário
abertura diária

máxima semanal
mínima semanal
fechamento semanal

máxima mensal
mínima mensal
fechamento mensal
```

Esses eventos também devem alimentar o mesmo sistema de clustering.

Não criar uma linha separada para cada categoria.

Se:

```text
máxima semanal = 130000
```

e:

```text
swing = 130005
```

o resultado deve ser um único nível.

---

# 25. Não usar suporte/resistência

O código não deve conter uma arquitetura baseada em:

```python
SupportLevel
ResistanceLevel
```

Nem:

```python
level.type = "support"
```

ou:

```python
level.type = "resistance"
```

O objeto deve ser neutro:

```python
class Level:
    price
    score
    events
    ...
```

---

# 26. Não utilizar zonas

Não implementar:

```python
zone_low
zone_high
```

como representação do nível.

Uma tolerância interna pode existir para:

* clustering;
* comparação;
* identificação de eventos;
* cálculo de confluência.

Porém o resultado final deve ser:

```python
price = 130000
```

e não:

```python
low = 129950
high = 130050
```

---

# 27. Validação estatística

O algoritmo deve ser validado.

Não basta gerar um gráfico visualmente convincente.

Para cada nível histórico, medir posteriormente:

```text
quantas vezes o preço voltou ao nível?
qual foi a reação média?
qual foi a reação mediana?
qual foi a maior reação?
qual foi a distância média até o próximo movimento significativo?
```

Essas métricas devem ser calculadas sem utilizar informações futuras na criação do nível.

---

# 28. Look-ahead bias

Esta é uma exigência crítica.

Quando o algoritmo estiver avaliando:

```text
2024-05-10 10:30
```

ele só pode utilizar informações disponíveis até:

```text
2024-05-10 10:30
```

Não pode utilizar:

```text
2024-05-10 15:00
2024-05-11
2025
2026
```

para decidir que o nível era importante naquele momento.

O backtest deve ser feito cronologicamente.

---

# 29. Walk-forward

Implementar validação walk-forward.

Exemplo:

```text
Treino:
2021 → 2023

Teste:
2024

Treino:
2021 → 2024

Teste:
2025

Treino:
2021 → 2025

Teste:
2026
```

O objetivo é verificar se os níveis identificados possuem poder preditivo fora da amostra utilizada para sua construção.

---

# 30. Visualização

Criar gráficos para inspeção.

O gráfico deve mostrar:

```text
candles
+
linhas horizontais
```

Exemplo:

```text
              ───────────── 130500  score 82
       /\    / 
      /  \__/       /\

              ───────────── 130000  score 94

             /\      /\
            /  \____/  \

              ───────────── 129500  score 77
```

As linhas devem ser horizontais.

Não desenhar retângulos ou zonas.

A espessura/transparência da linha pode representar o score, mas isso é apenas visualização.

---

# 31. Quantidade de linhas

Não desenhar todos os níveis encontrados.

Criar uma seleção dos:

```text
Top N levels
```

onde:

```python
N = configurable
```

Por exemplo:

```python
top_n = 20
```

Também permitir filtrar por:

```python
minimum_score
```

---

# 32. Saída final — código NTSL

A saída principal do projeto deve ser um arquivo de código NTSL
compatível com o ProfitChart.

O Python deve analisar todo o histórico e, ao final, gerar chamadas
`HorizontalLineCustom()` para os níveis selecionados.

A função a ser utilizada é:

HorizontalLineCustom(
    preço,
    clAzul,
    1,
    psDash,
    "R70 T29",
    TamanhoTexto,
    LocalTexto,
    0,
    0,
    0
);

---

## 32.1 Exemplo de saída

Supondo que o algoritmo tenha encontrado:

|  Preço | Score | Eventos |
| -----: | ----: | ------: |
| 130000 |    94 |      31 |
| 129500 |    82 |      18 |
| 128750 |    76 |      14 |

O Python deverá gerar:

```ntsl
HorizontalLineCustom(130000, clAzul, 1, psDash, "R94 T31", TamanhoTexto, LocalTexto, 0, 0, 0);
HorizontalLineCustom(129500, clAzul, 1, psDash, "R82 T18", TamanhoTexto, LocalTexto, 0, 0, 0);
HorizontalLineCustom(128750, clAzul, 1, psDash, "R76 T14", TamanhoTexto, LocalTexto, 0, 0, 0);
```
---

# 33. Estrutura de código sugerida

```text
project/
│
├── data/
│   ├── loader.py
│   ├── validation.py
│   └── resampling.py
│
├── detection/
│   ├── events.py
│   ├── swings.py
│   ├── reactions.py
│   ├── reference_levels.py
│   └── kde.py
│
├── clustering/
│   ├── dbscan.py
│   └── hierarchical.py
│
├── scoring/
│   ├── score.py
│   ├── recency.py
│   └── confluence.py
│
├── validation/
│   ├── backtest.py
│   └── walk_forward.py
│
├── visualization/
│   └── charts.py
│
├── models/
│   └── level.py
│
├── config.py
└── main.py
```

---

# 34. Bibliotecas

Avaliar:

```text
numpy
pandas
scipy
scikit-learn
numba
plotly
```

Se o volume de dados justificar:

```text
polars
```

O código deve evitar loops Python desnecessários sobre milhões de candles.

Priorizar:

* NumPy;
* Pandas/Polars;
* SciPy;
* Numba quando necessário.

---

# 35. Performance

Cinco anos de candles de 1 minuto podem representar milhões de registros.

O projeto deve ser desenhado para:

* carregar dados eficientemente;
* evitar recalcular indicadores;
* evitar loops candle-a-candle quando não forem necessários;
* armazenar resultados intermediários;
* permitir execução incremental.

Idealmente, separar:

```text
preprocessing
→ event detection
→ clustering
→ scoring
```

para que uma mudança no score não exija reprocessar todos os candles.

---

# 36. Configuração

Todos os parâmetros relevantes devem estar em um único arquivo/configuração.

Exemplo:

```python
TIMEFRAMES = ["1m", "5m", "15m", "1h", "1D", "1W"]

ATR_PERIOD = 14

REACTION_HORIZONS = [5, 15, 30, 60]

REACTION_ATR_THRESHOLD = 0.25

CLUSTER_ATR_FACTOR = 0.15

MIN_EVENTS = 3

TOP_N_LEVELS = 20

RECENCY_HALF_LIFE_DAYS = 180
```

Os valores acima são apenas exemplos iniciais.

Não assumir que sejam valores ótimos.

---

# 37. Desenvolvimento em fases

Não implementar tudo de uma vez.

## Fase 1 — MVP

Implementar somente:

```text
1. carregar candles
2. calcular ATR
3. detectar swing points
4. detectar eventos de reação
5. agrupar eventos por preço
6. gerar níveis
7. calcular score básico
8. desenhar linhas
```

Objetivo:

**ter uma primeira versão funcional e visualmente auditável.**

---

## Fase 2

Adicionar:

```text
1. múltiplos timeframes
2. níveis diários/semanais/mensais
3. confluência
4. recência
5. volume
6. score mais sofisticado
```

---

## Fase 3

Adicionar:

```text
1. KDE
2. comparação KDE × clustering
3. métricas estatísticas
4. walk-forward
5. análise de robustez
```

---

## Fase 4

Otimizar:

```text
Numba
Polars
cache
processamento incremental
```

somente depois de validar a metodologia.

---

# 38. Critério de sucesso

O objetivo NÃO é maximizar a quantidade de linhas detectadas.

O objetivo é encontrar um conjunto pequeno de preços que tenham evidência histórica de importância.

Uma boa saída seria algo como:

```text
130500    score 92
130000    score 88
129750    score 81
129400    score 76
129000    score 71
```

e não:

```text
130500
130450
130425
130400
130375
130350
...
```

O algoritmo deve ser conservador.

---

# 39. Princípio central

A pergunta que o algoritmo deve responder é:

> **"Quais preços, ao longo do histórico, demonstraram repetidamente capacidade de gerar movimentos relevantes no mercado?"**

Não perguntar:

> "Isso é suporte ou resistência?"

Não perguntar:

> "Qual é a largura dessa zona?"

Não perguntar:

> "Qual direção o mercado tomou?"

A saída final é simplesmente:

```text
PREÇO + RELEVÂNCIA
```

representada graficamente por:

```text
────────────────────────────
          130000
────────────────────────────
```

# 39.1 Inputs do usuário

o usuario deve poder especificar a separação desejada (em média) entre linhas

o usuário poderá especificar um limite de data histórico (data final mais recente limite, a partir do início do histórico)

o NTSL deverá ter:
    Parâmetros configuráveis R G B, para definir a cor das linhas, caso o usuário assim o decida
    Parâmetro de espessura de linha
    Parâmetro de tipo de linha (integer)

---

# 40. Próximo passo de implementação

Antes de implementar todos os módulos, criar um notebook ou script exploratório que permita:

1. carregar uma amostra dos dados;
2. calcular ATR;
3. detectar eventos;
4. visualizar os eventos sobre candles;
5. fazer clustering;
6. visualizar as linhas resultantes;
7. inspecionar manualmente os níveis;
8. medir estatisticamente as reações posteriores.

Somente depois dessa validação implementar a arquitetura definitiva.

A prioridade deve ser **validar a definição matemática de "nível importante" antes de otimizar o código**.
