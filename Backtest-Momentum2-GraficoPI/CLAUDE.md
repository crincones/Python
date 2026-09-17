# Estratégia com EMA21

Grafico PI 20 ticks

## Indicadores:
Nesta estratégia, utilizo os seguintes indicadores:

- EMA21 periodos.

- Hull 50 periodos.

- MACD 9 rápida, 14 lenta, EMA 9, Bollinger Bands aplicada ao MACD (1000 periodos, 1.0 de desvio).

- HullRetracao_Azul.ntsl

- Keltner aplicado a close, segundo exatamente a EMA21, com 2.5 desvios (fator 2.5)

## Entradas:

Ponto de Virada sempre em contato com a EMA21.

### Compras:

- MACD Acima de zero.
- Hull a favor
- Trigger disparado
- Caso Hull esteja em contato com os candles de virada, ou abaixo deles, classifica-se como um trade T1.
- Caso Hull esteja acima dos candles de virada, classifica-se como um trade T2.

### Vendas:

- MACD Abaixo de zero.
- Hull a favor
- Trigger disparado
- Caso Hull esteja em contato com os candles de virada, ou acima deles, classifica-se como um trade T1.
- Caso Hull esteja abaixo dos candles de virada, classifica-se como um trade T2.

Analisar os exemplos (prints) inseridos na pasta Exemplos.

### Sistema de entradas:

- Entrada seca no fechamento do candle que deu origem ao trigger, A partir do ponto de entrada, temos:
  - Stop de -100 pontos.
  - Parcial de 50% da posição em +100 pontos a partir da entrada (A execução da parcial joga o preço médio da operação para -100 a partir do ponto de entrada, e a ordem STOP LOSS fica nesse nível, caso a operação volte, consome o lucro da parcial e a operação sai no 0x0), saída final em +300 pontos a partir da entrada original.
- Aguardar entrar no recuo até a metade do corpo do candle que deu origem ao trigger, como ordem Limit, mesmos stops e limits do parágrafo anterior.
- Colocar o Stop no extremo oposto ao fechamento do candle que deu origem ao trigger, mesmo manejamento de stops/takes do primeiro parágrafo

## Otimizações/Tarefas

- Analisar performance deste operacional no histórico OHLC da pasta WINFUT
  
Avaliar filtros adicionais como:
- tendência geral do ativo;
- Segundos recuos;
- Frazqueza de continuação;
- Segundas entradas no mesmo nível;
- Horário de operação;
- Proximidade com horário de abertura das ações brasileiras (10:00 até 10:10);
- Proximidade com horário da abertura do Dow Jones (mecado americano);
- Presença de movimentos picados antes do sinal (sequência de várias inversões);
- Utilização adicional de Volume (Agressão de Compra + Agressão de venda);
- Tempo de formação das barras do gatilho, e anteriores.

Propor distintas formas de gerenciamento, variação dos stops, take profit, utilização de parciais, para encontrar uma configuração ótima.

Elaborar relatório em HTML, incluindo trade a trade por meio da utilização de KLine Charts, desenha os indicadores e os triggers. assim como ponto de entrada e saída.

Elabora testes de robustez nos resultados.

Entrega curvas de patrimônio utilizando 6 contratos de mini índice, considera o custo round turn de 0,50 R$ por contrato.