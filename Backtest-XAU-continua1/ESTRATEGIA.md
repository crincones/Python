# ESTRATEGIA

No ativo XAUSD, usando o gráfico de ticks de 521 ticks, tenho observado o seguinte:

•  usando as médias de 21, 42, e 72 periodos exponenciais: quando as médias estão em forma de leque, indicando uma tendência, e o preço se afasta destas médias, e volta ao leque, com uma sequência de 2 ou 3 candles da mesma cor, e aparece neste leque, um candle contrário, se coloca uma ordem de entrada no meio do range deste candle, aguardando a ativação no próximo candle (se não ativar no próximo candle, a operação é abortada).

• A entrada tem um stop de 300 ticks (lembrando que o tick é 0.01, então 300 ticks são 3 dólares), com uma saída parcial a 300 ticks também (50% da posição), esta saída parcial movimenta a média da operação até o ponto do stop los inicial, o stop loss fica em breakeven (breakeven na média da operação e não no ponto de entrada).

• A saída final fica a 900 pontos, desta forma, a relação risco/retorno de cada operação é de 2:1.

• foi observado que esta estratégia funciona melhor em momentos onde as médias não estão "emboladas", que geralmente são momentos de consolidação ou reversão de tendência, e também em momentos onde o range das barras não é muito grande.

• seria interessante também determinar um tamanho máximo de candle de reversão para considerar a entrada, pois ao termos um stop fixo, o range da barra de reversão pode ficar grande demais.

• Uma segregação por horário de operação pode ajudar a determinar horários de operação mais lucrativos.

# TAREFAS

• Fazer um backtest bem documentado da estratégia baseado no histórico nesta pasta (Backtest-XAU-continua1\XAUUSD-521T\XAUUSD_521_TK_M1_202605051927_202609021325.csv).

• Elaborar um relatório em .md

• Elaborar um relatório em html: Este relatório deve conter possíveis variantes sugeridas, restrições recomendadas, estatísticas relevantes da estratégia, explicação de cada termo utilizado, gráfico com cada operação usando Kline charts (com a possibilidade de intercalar entre as variantes caso existirem).

• Um plano para trading manual elaborado em .md e também em html