# CLAUDE.md — Dash CIRP Opções (travas de opções B3)

## 1. Objetivo do projeto

Construir um aplicativo local para analisar e comparar operações de opções da B3, inicialmente com foco em **travas verticais de alta e de baixa**, tanto de **crédito** quanto de **débito**.

O aplicativo deve ajudar o usuário a identificar e ranquear estruturas candidatas, visualizar o payoff no vencimento e ao longo do tempo, comparar vencimentos e fornecer um **preço-limite indicativo** para o usuário inserir manualmente no ProfitChart.

O sistema é uma ferramenta de análise e apoio à decisão. **Não envia ordens, não opera automaticamente e não deve prometer lucro ou probabilidade de sucesso garantida.**

## 2. Stack e arquitetura

- **Captura e processamento de dados:** Python.
- **Ponte com a B3:** MetaTrader 5 (MT5), usando a integração Python disponível no terminal instalado.
- **Interface:** escolher a solução que melhor atenda aos requisitos. Preferência inicial por **HTML/JavaScript com KLineCharts** para os gráficos, com backend Python (por exemplo, FastAPI). Streamlit pode ser usado se a integração do KLineCharts e o layout lateral puderem ser mantidos sem soluções frágeis.
- **Gráfico de candles:** KLineCharts.
- **Execução:** aplicação local no computador do usuário.
- **Idioma da interface:** português brasileiro (pt-BR).
- **Tema:** claro, consistente em todas as telas.
- **Fuso horário:** America/Sao_Paulo. Tratar explicitamente o calendário e os horários do mercado brasileiro.

Antes de escolher definitivamente a arquitetura, examine o exemplo existente em:

`C:\Users\Carlos\Documents\GitHub\Python\screener-opcoes`

Reutilize código e padrões úteis desse projeto, especialmente conexão MT5, descoberta de símbolos, coleta de cotações e tratamento de opções. Não presuma que o caminho existe em outros ambientes: se estiver indisponível, informe isso e solicite acesso ou configure o caminho local.

## 3. Fluxo principal do usuário

O usuário deve conseguir:

1. Escolher a direção: **trava de alta** ou **trava de baixa**.
2. Escolher o tipo de estrutura: **débito** ou **crédito**.
3. Selecionar o ativo subjacente (por exemplo, ações ou ETFs negociados na B3).
4. Informar a expectativa de movimento do subjacente:
   - preço-alvo esperado e/ou variação percentual;
   - horizonte esperado para o movimento;
   - opcionalmente, cenário conservador, base e otimista.
5. Definir preferências e restrições, como:
   - vencimentos permitidos;
   - faixa de strikes;
   - orçamento ou risco máximo por operação;
   - liquidez mínima;
   - spread bid-ask máximo;
   - quantidade de contratos para simulação.
6. Solicitar análise e receber uma lista ranqueada das estruturas candidatas.
7. Abrir qualquer estrutura para examinar seus números, payoff, gráfico e hipóteses.
8. Consultar um preço-limite sugerido e inserir esse preço manualmente no ProfitChart.

Não obrigue o usuário a preencher todos os filtros avançados. Forneça valores padrão sensatos e permita uma análise inicial com o mínimo de entradas necessárias.

## 4. Conceitos de estruturas

Implementar inicialmente travas verticais simples com opções da mesma classe e do mesmo subjacente, com strikes distintos e, por padrão, mesmo vencimento:

- **Trava de alta com débito:** compra de call de strike menor e venda de call de strike maior; permitir também a construção equivalente com puts quando fizer sentido e a estrutura estiver corretamente definida.
- **Trava de baixa com débito:** compra de put de strike maior e venda de put de strike menor.
- **Trava de alta com crédito:** venda de put de strike maior e compra de put de strike menor.
- **Trava de baixa com crédito:** venda de call de strike menor e compra de call de strike maior.

Validar cada estrutura por suas pernas, não apenas pelo rótulo escolhido. Confirmar que os sinais, strikes, multiplicadores e quantidades geram o perfil de risco esperado. Não misturar calls e puts indiscriminadamente nem permitir que uma estrutura inválida seja apresentada como válida.

A primeira versão deve priorizar travas verticais com vencimento coincidente. Se forem avaliadas estruturas com vencimentos diferentes, classificá-las como estrutura distinta (calendário/diagonal), com cálculo e avisos específicos; não tratá-las como trava vertical simples.

## 5. Coleta de dados via Python + MT5

### 5.1 Regras gerais

- Usar o MT5 como fonte/ponte de dados conforme o exemplo existente.
- Verificar se o terminal está aberto, conectado e com os símbolos necessários disponíveis.
- Descobrir os símbolos reais dos ativos e opções no terminal; **não inventar nem presumir a convenção de nomenclatura dos tickers de opções**.
- Tratar explicitamente dados ausentes, atrasados, inválidos ou sem liquidez.
- Exibir a hora da última atualização e o estado da conexão.
- Manter uma camada de acesso a dados isolada da lógica de payoff e da interface.
- Registrar erros úteis para diagnóstico, sem despejar segredos ou informações sensíveis em logs.
- Não declarar que os dados são em tempo real sem verificar a atualização efetiva do MT5.
- Não presumir que o MT5 disponibiliza toda a cadeia de opções ou todas as métricas da B3. Identificar as limitações do feed e informar ao usuário.
- Não fabricar cotações, volatilidades, volume, bid, ask ou preços históricos para preencher lacunas.

### 5.2 Cotações e liquidez

Sempre que os dados estiverem disponíveis, coletar por opção:

- bid e ask;
- último negócio e horário, se fornecidos;
- volume financeiro e/ou quantidade negociada;
- número de negócios;
- vencimento;
- tipo (call/put);
- strike;
- ativo subjacente;
- multiplicador/lote, quando aplicável;
- status/validade do símbolo.

Calcular o midpoint `(bid + ask) / 2` somente quando bid e ask forem válidos. Marcar explicitamente preços indicativos, negócios antigos e mercados sem bid/ask útil.

A liquidez deve influenciar o ranking. Penalizar spreads percentuais elevados, cotações antigas, ausência de negócios e volume insuficiente. Não confundir volume de negócios com open interest; só exibir open interest se a fonte realmente o fornecer.

### 5.3 Histórico do subjacente

Obter candles diário, semanal e de 240 minutos (4h), quando disponíveis no MT5. Verificar alinhamento temporal, timezone, candles incompletos e divergências entre timeframes. Não fabricar candles faltantes.

Para o gráfico, distinguir candle fechado de candle em formação e indicar a hora da última barra. A EMA deve ser calculada de forma consistente e documentada.

## 6. Análise e ranking de operações

Para cada estrutura válida, calcular e mostrar, quando aplicável:

- débito ou crédito líquido por ação/unidade e por contrato;
- perda máxima;
- lucro máximo;
- ponto(s) de breakeven no vencimento;
- relação lucro máximo/perda máxima e perda máxima/lucro máximo, deixando claro qual definição está sendo exibida;
- retorno máximo sobre o risco máximo;
- POP (probabilidade de lucro), com metodologia explicitada;
- probabilidade de atingir o preço-alvo, se estimável;
- resultado estimado no preço-alvo informado;
- payoff em diferentes preços do subjacente;
- dias corridos e dias úteis até o vencimento;
- efeito do theta e exposição a delta, gamma, vega e rho, quando for possível estimá-los;
- volatilidade implícita e grega por perna, somente se houver dados e modelo adequados;
- qualidade dos dados, liquidez e custo estimado de execução;
- risco de exercício antecipado/atribuição e detalhes de liquidação relevantes para opções americanas, quando aplicável.

### 6.1 Probabilidade de lucro (POP)

- Nunca apresentar POP como uma verdade objetiva ou garantia.
- Documentar o modelo e as hipóteses usadas.
- Se a volatilidade implícita for confiável, permitir estimativa baseada nela; se não for, oferecer cenário paramétrico com volatilidade informada pelo usuário ou marcar POP como **indisponível**.
- Considerar o horizonte temporal correto, o preço atual do subjacente, o payoff e os custos quando relevantes.
- Diferenciar probabilidade de terminar com lucro no vencimento de probabilidade de obter lucro antes do vencimento.
- Não apresentar um número de POP sem mostrar a metodologia, as premissas e a qualidade dos dados.

### 6.2 Critérios de ranking

Exibir uma pontuação total e também os critérios individuais, evitando uma “caixa-preta”. Permitir ordenar por diferentes objetivos, por exemplo:

- maior lucro esperado no cenário do usuário;
- maior retorno máximo sobre risco;
- melhor relação lucro/perda;
- melhor POP estimada;
- menor perda máxima;
- melhor liquidez e menor custo de execução;
- melhor combinação risco-retorno.

A pontuação padrão deve ponderar o resultado no cenário esperado, o risco máximo, a liquidez e a qualidade dos dados. Os pesos precisam ser visíveis e configuráveis. Não ranquear como excelente uma estrutura cuja cotação esteja obsoleta ou cuja liquidez seja inadequada.

Não comparar estruturas com premissas diferentes sem indicar claramente a diferença de vencimento, volatilidade, risco e horizonte.

## 7. Preço justo e preço-limite

O aplicativo deve fornecer um **preço indicativo**, para o usuário inserir manualmente no ProfitChart. Distinguir claramente:

1. **Preço de mercado:** bid/ask observados nas pernas e na estrutura, quando calculável.
2. **Preço teórico:** resultado de um modelo, com premissas explícitas.
3. **Preço-limite sugerido:** preço de entrada indicativo que respeita o limite de risco/retorno definido pelo usuário.

Para spreads, calcular o preço líquido coerente com o lado de cada perna e com o sentido crédito/débito. Usar midpoint apenas como referência, nunca como garantia de execução. Considerar bid/ask, tamanho dos spreads, liquidez e custos. Se faltar dado suficiente, mostrar “não estimável” e explicar o motivo.

O preço-limite sugerido deve ser acompanhado de:
- faixa indicativa de preço;
- preço usado no cálculo;
- premissas e horário dos dados;
- impacto do preço de entrada sobre lucro máximo, perda máxima, breakeven e retorno/risco.

**Não enviar ordens ao ProfitChart nem ao MT5.** A inserção será sempre manual pelo usuário.

## 8. Gráficos e interface

### 8.1 Layout principal

- Tema claro, legível e consistente.
- Painel principal para filtros, ranking e análise da estrutura.
- Gráfico da estrutura/payoff em destaque.
- Gráfico do ativo subjacente em painel lateral direito, que possa ser minimizado/retraído e restaurado.
- Layout responsivo para telas de computador. Priorizar a experiência desktop.

### 8.2 Gráfico da estrutura

Mostrar o payoff da estrutura no vencimento em função do preço do subjacente, incluindo:

- linha de lucro/prejuízo zero;
- breakeven(s);
- perda máxima e lucro máximo;
- preço atual do subjacente;
- preço-alvo informado;
- strikes de todas as pernas;
- regiões de lucro e prejuízo, com legenda clara.

Permitir simular a passagem do tempo. O usuário deve conseguir avançar/recuar a data ou usar um controle de tempo, observando a mudança estimada do valor da estrutura antes do vencimento. Essa simulação precisa distinguir:
- **payoff no vencimento**, que é calculável diretamente;
- **valor teórico antes do vencimento**, que depende de um modelo, volatilidade, juros, dividendos e demais premissas.

Não representar o payoff no vencimento como se fosse a avaliação mark-to-market antes do vencimento. Mostrar as premissas usadas na simulação temporal e permitir alterá-las quando fizer sentido.

### 8.3 Gráfico do subjacente — KLineCharts

Usar KLineCharts para candles do ativo subjacente, com seleção entre:

- diário;
- semanal;
- 240 minutos (4h).

Estilo dos candles:
- candles de alta: corpo branco, borda preta e, quando aplicável, pavio preto;
- candles de baixa: corpo preto, borda preta e pavio preto.

Médias móveis exponenciais:
- **EMA 17:** magenta;
- **EMA 34:** laranja;
- espessura visivelmente superior à espessura mínima padrão;
- legenda que indique período e cor.

Sobrepor linhas/níveis relevantes para a operação:
- preço atual;
- breakeven(s) no vencimento;
- preço(s) de equilíbrio estimado(s) para a data simulada, se calculável;
- preço-alvo;
- strikes e outros níveis úteis, sem poluir o gráfico.

Deixar claro que breakevens de uma estrutura de opções se referem ao payoff no vencimento, a menos que sejam explicitamente calculados para outro horizonte. Não confundir strikes com preços de breakeven.

O painel lateral deve poder ser retraído sem perder a seleção do ativo, timeframe ou estado da análise.

### 8.4 Acessibilidade e usabilidade

- Números em formato brasileiro (vírgula decimal, separador de milhar e moeda BRL quando apropriado).
- Cores acompanhadas de rótulos; não depender apenas da cor para transmitir lucro/prejuízo.
- Estados claros de carregamento, erro, ausência de dados e desconexão do MT5.
- Tooltips curtos para POP, gregas, breakeven, risco máximo e preço justo.
- Evitar dashboards sobrecarregados. Priorizar a leitura rápida e permitir abrir detalhes.

## 9. Modelo de cálculo e validação

Implementar os cálculos financeiros em funções Python puras, separadas da interface e da integração MT5. Usar testes unitários para todos os tipos de trava.

Para cada estrutura:
- representar cada perna com tipo (call/put), lado (compra/venda), strike, vencimento, quantidade, multiplicador e preço;
- calcular o payoff por perna e agregado;
- aplicar custos somente quando forem conhecidos/configuráveis;
- validar strikes, vencimentos, quantidades, multiplicadores e sinais;
- tratar arredondamentos de acordo com as regras do mercado e do ativo;
- testar cenários abaixo, entre e acima dos strikes, além de breakeven e limites.

Criar testes para garantir que:
- débito inicial reduz o resultado líquido e crédito inicial aumenta o resultado líquido;
- perda máxima e lucro máximo correspondem aos extremos teóricos da estrutura;
- breakevens estejam corretos para as quatro estruturas;
- trocar compra/venda ou inverter strikes mude o perfil como esperado;
- valores de POP sejam omitidos quando as premissas forem insuficientes;
- cotações antigas ou inválidas sejam sinalizadas e não tratadas como atuais.

Não usar apenas exemplos visuais para validar fórmulas. Os testes automatizados devem verificar numericamente os resultados.

## 10. Persistência e configuração

Guardar preferências locais de interface e análise quando for simples e seguro, por exemplo:
- último subjacente selecionado;
- filtros de vencimento e strikes;
- pesos do ranking;
- premissas de volatilidade e juros;
- painel lateral aberto/retraído.

Não guardar credenciais em texto puro. Não introduzir dependências de serviços pagos ou APIs externas sem autorização explícita.

## 11. Segurança, transparência e limitações

- O aplicativo é uma ferramenta de análise, não recomendação financeira personalizada.
- Informar que opções podem resultar em perda relevante e que a liquidez pode impedir execução pelo preço teórico.
- Não afirmar que uma operação é “segura” ou que sua POP garante resultado.
- Exibir a origem, o horário e a qualidade dos dados.
- Não ocultar dados ausentes nem preencher lacunas com valores inventados.
- Não executar operações, enviar ordens ou acessar contas do usuário para negociar.
- Evitar dependências externas desnecessárias e fixar versões das dependências no arquivo de configuração do projeto.

## 12. Organização sugerida do código

Adapte a estrutura ao projeto existente, mas mantenha separação clara de responsabilidades. Uma organização possível:

```text
project/
├── app/                  # Interface web
├── backend/              # API e serviços
├── data/
│   ├── mt5_client.py     # Integração com MT5
│   ├── symbols.py        # Descoberta e normalização de símbolos
│   └── market_data.py    # Cotações e candles
├── options/
│   ├── models.py         # Modelos de pernas e estruturas
│   ├── payoff.py         # Payoff, risco, lucro e breakeven
│   ├── pricing.py        # Precificação teórica
│   ├── probability.py    # POP e cenários
│   ├── ranking.py        # Pontuação e classificação
│   └── validation.py     # Validações
├── tests/
├── config/
├── README.md
├── CLAUDE.md
└── requirements.txt ou pyproject.toml
```

Esta estrutura é sugestiva, não obrigatória. Prefira uma implementação simples, testável e sustentável a uma arquitetura excessivamente complexa.

## 13. Plano de implementação

Trabalhe em etapas pequenas e verificáveis:

1. **Inspecionar o projeto existente** `screener-opcoes`, mapear como o MT5 é conectado e identificar formatos reais de símbolos e dados.
2. **Relatório de viabilidade dos dados:** documentar quais opções, cotações, candles e campos estão realmente disponíveis no terminal/feed.
3. **Motor de payoff:** implementar e testar as quatro travas verticais básicas com dados fictícios apenas nos testes unitários, nunca na tela como se fossem dados reais.
4. **Camada MT5:** conexão, descoberta de símbolos, atualização, normalização e estados de erro.
5. **Análise e ranking:** métricas, filtros de liquidez e transparência dos critérios.
6. **Preço indicativo:** mercado, preço teórico e preço-limite sugerido claramente separados.
7. **Interface:** filtros, tabela ranqueada, detalhes e gráfico de payoff.
8. **KLineCharts:** candles, EMA 17/34, timeframes e níveis da operação.
9. **Simulação temporal:** modelo de avaliação pré-vencimento, premissas visíveis e controle de tempo.
10. **Testes integrados e documentação:** instruções de instalação, configuração, execução e limitações conhecidas.

Ao concluir cada etapa:
- executar os testes relevantes;
- documentar o que funciona e o que ainda não funciona;
- não simular sucesso de integração se o MT5 ou os dados reais não estiverem disponíveis;
- não implementar todas as funcionalidades de uma vez sem uma versão mínima funcional.

## 14. Critérios de aceitação da primeira versão

A primeira versão será considerada utilizável quando:

- [ ] O aplicativo conectar ao MT5 ou apresentar uma mensagem de diagnóstico clara.
- [ ] O usuário selecionar alta/baixa, crédito/débito e ativo subjacente.
- [ ] O aplicativo descobrir e filtrar opções reais disponíveis no feed, sem inventar símbolos.
- [ ] A lista ranqueada mostrar vencimento, strikes, preços, risco máximo, lucro máximo, breakeven, relação risco-retorno e estado da liquidez.
- [ ] A POP só aparecer quando houver premissas suficientes e sua metodologia estiver explicada.
- [ ] O preço-limite indicativo tiver premissas e timestamp, sem prometer execução.
- [ ] O gráfico de payoff mostrar lucro/prejuízo, breakeven, strikes, preço atual e preço-alvo.
- [ ] O gráfico KLineCharts mostrar candles diários, semanais e de 240 minutos, com EMA 17 magenta e EMA 34 laranja.
- [ ] Candles de alta forem brancos com borda preta e candles de baixa pretos.
- [ ] O gráfico do subjacente puder ser retraído/restaurado.
- [ ] O tema claro estiver aplicado.
- [ ] A simulação temporal diferenciar valor teórico pré-vencimento de payoff no vencimento.
- [ ] Os cálculos centrais tiverem testes automatizados.
- [ ] Houver documentação de instalação e execução local.

## 15. Instrução para Claude Code

Comece inspecionando o repositório existente e o exemplo `screener-opcoes`. Antes de modificar arquivos, apresente um resumo curto da estrutura encontrada, da estratégia de implementação e dos riscos/limitações da fonte de dados.

Em seguida, implemente a primeira fatia funcional: **descoberta real de símbolos/dados via MT5 + motor testado de payoff para as quatro travas verticais + interface mínima para analisar uma estrutura**. Não comece por uma interface visual elaborada enquanto a viabilidade dos dados e os cálculos não estiverem validados.

Não assuma disponibilidade de dados que não foi verificada. Faça perguntas apenas quando faltar uma decisão realmente bloqueante; para as demais escolhas, adote padrões simples, documente-os e avance.
