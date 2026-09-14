## Backtest de estratégia de trading

# Informações gerais

Grafico tipo PI (Pontos de Inversão conforme o padrão Nelógica)

Usar base OHLC na pasta WINFUT

Indicadores utilizados:

- Média Móvel HULL de 50 periodos
- Média Móvel Exponencial de 21 periodos (usando Close)
- Keltner Channel (padrão Nelógica, Exponencial, usando Close, 21 períodos, Usando desvio de 2.0)
  
# Processo de entradas

Para Compras: 

- Hull deve estar ascendente
- Hull Preferívelmente cóncava
- Hull Abaixo da máxima do candle

O padrão procurado é um retracement ou retração da tendência geral, e posteriormente, um candle de continuação de tendência, sinalizando a entrada no trade. idealmente este padrâo de 2 candles deve estar:

- com os 2 highs acima da Hull (para compras)
- com a EMA 21 entre os highs e lows

é notado que quando a HULL se encontra perto da banda superior, indica exaustão ou fraqueza do movimento
da mesma forma, quando a hull passa muito tempo perto da EMA 21, também é sinal de consolidação, que não é interessante para operar.

A entrada pode se dar no meio do candle de inicio (meio do corpo), ou no fechamento, deve-se avaliar as 2 alternativas.

- Stop de 100 pontos
- Take Profit de 300 pontos
- Saída parcial a 100 pontos de 50 porcento, levando o stop na média da operação (não na entrada original)

- Alternativa sem parcial deve ser avaliada.

o padrão de venda é espelho.

# Processo

- Realizar o backteste, com teste de robustez na medida do possível com a base disponível
- Avaliar se a geometria do candle que retoma a tendência tem influência na sua efetividade (pavio)
- Avaliar se o filtro de concavidade/convexidade da hull é benêfico
- Avaliar se tamanho da retração pode ser usado como filtro
- Avaliar as alternativas sugeridas de Stop/Take
- Avaliar melhores horários de negociação (considerar que sempre as 10:00 é a abertura do mercado à vista)
- Avaliar e mostrar gráficamente (relatório, plano), quais são as melhores operações, conforme a forma encontrada, Padrão Ouro, Prata e Bronze, para simplificar
- Avaliar se necessário, outros períodos de médias móveis (com a restrição que a EMA deve ser a média do keltner sempre)
- Avaliar se filtros de inclinação da EMA e HULL, melhoram os resultados.

# Relatório

- Formato HTML para fácil visualização/entendimento
- Utilizar padrões de fontes modernas na escrita do relatório (nada de estilo Times New Roman ou similares)
- Incluir estatísticas similares às apresentadas pelo metatrader 5 nos backtestes, adicionando winrate.
- Incluir gráficos de evolução de patrimônio em cada variante
- Incluir MEP e MEN (gráficos de distribuição de lucros)
- Incluir gráfico de distribuição de duração dos trades
- Escrever também em formato .md
- Caso encontrar um setup viável, escrever um plano de trading (em HTML, e também em .md)
- Incluir gráfico trade a trade via Kline Charts