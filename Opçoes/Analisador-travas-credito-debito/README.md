# Analisador de Travas (B3 via MetaTrader 5)

Aplicativo local para gerar, ranquear e examinar **travas verticais** de opções de ações da B3:
alta/baixa × débito/crédito. Ferramenta de análise: **não envia ordens** nem acessa a conta para
negociar. O preço-limite sugerido é digitado manualmente pelo usuário no ProfitChart.

## Requisitos

- Windows, Python 3.14 (64 bits) e [uv](https://docs.astral.sh/uv/).
- Terminal MetaTrader 5 da XP instalado e logado (perfil salvo no terminal; nenhuma senha no
  projeto). Caminho em `config/settings.yaml` (`mt5.terminal_path`, roda com `/portable`).
- Se o terminal estiver fechado, o aplicativo o abre minimizado e o fecha ao sair. Terminal
  aberto pelo usuário nunca é fechado.

## Instalação e execução

```powershell
uv sync                         # instala as dependências (versões fixadas no pyproject.toml)
uv run travas serve             # inicia em http://127.0.0.1:8765 e abre o navegador
uv run travas serve --no-browser
uv run travas serve --port 8766  # outra porta
uv run travas check --underlying PETR4   # audita o feed e grava docs/viabilidade_dados.md
uv run pytest                   # testes offline (sem MT5)
uv run ruff check . ; uv run ruff format .
```

Ou dê duplo clique em `iniciar.bat`.

## Pregão aberto x fechado

O app confere o relógio de Brasília antes de buscar cotações (`market_hours` em
`config/settings.yaml`, padrão 10:00–17:55, conferir na B3; fins de semana e feriados pelo
calendário). Com o mercado **aberto**, lê o MT5 e salva as cotações em `data/cotacoes/`. Com o
mercado **fechado** (pré-abertura, após o fechamento, sem pregão), usa essas últimas cotações do
pregão, com prazos recalculados para hoje, e avisa na tela. Séries nunca capturadas no pregão
são lidas do MT5 e marcadas como "lida fora do pregão" (podem estar zeradas ou distorcidas).

## Corretoras (conta logada no MT5)

O app usa a conta que estiver logada no terminal — não pede nem guarda usuário/senha. Trocar de
conta no próprio terminal (ex.: XP → Genial) é detectado no status; os caches da conta anterior
são descartados e as mensagens passam a citar a corretora atual. Diferenças medidas em 15/10/2026:

| | XP (XPMT5-PRD) | Genial (GenialInvestimentos-PRD) |
|---|---|---|
| Ativos com opções no MT5 | 48 | 218 (de 243 na B3; inclui SMAL11, EMBJ3, BPAC11, PETR3…) |
| Séries por ativo | todas (PETR4: 3.246) | parte (PETR4: ~934) |
| Negócios/volume da sessão nas opções | preenchidos | zerados → usa a barra D1 de hoje da opção (marcado "barra D1") |
| Ativo-objeto (`basis`) | correto | parte das séries traz o próprio ticker da opção |
| Strike / vencimento | corretos | parte sem ajuste de provento; vencimento em feriado (20/11) |
| Relógio dos timestamps | Brasília codificado como UTC | igual |

Por isso o **arquivo de instrumentos da B3** é a referência de ativo-objeto, strike, vencimento e
estilo de cada opção: quando o MT5 diverge, vale a B3 e a perna recebe o aviso "dado corrigido
(B3)". A lista de ativos (campo Ativo) mostra todos os 243 com opções na B3, por nº de séries,
marcando os que a corretora logada não cota. Primeira carga do heatmap completo numa conta nova:
alguns minutos (o terminal baixa o histórico D1 de ~200 ativos); depois, ~40 s.

## Ícones dos ativos

Os ~3.000 ícones do repositório público thefintz/icones-b3 ficam em `data/icones/` (fora do
git; baixados em 15/10/2026). Ticker sem arquivo local é buscado sob demanda na mesma fonte. O repositório não declara licença e os logos são marcas das empresas: uso local, sem
redistribuição. Sem ícone (ex.: IBOV11), aparecem as iniciais. Desative em `icons.enabled`.

## Uso

1. Escolha direção (alta/baixa), estrutura (débito/crédito) e o ativo.
2. Informe o preço-alvo **ou** a variação esperada (%), e opcionalmente o horizonte (data).
3. "Analisar": o app coleta no MT5 só as séries necessárias (classe de opção da trava, prazo
   máximo e faixa de strikes) — tipicamente 15–30 s; a cadeia fica em cache por 60 s.
4. Clique numa linha do ranking para ver pernas, métricas, payoff, simulação temporal,
   preço-limite e composição do score. O painel do ativo (KLineCharts) mostra os níveis.

Os gráficos de payoff e de candles têm o botão **⤢ Maximizar** (Esc ou "Restaurar" volta). A
largura do gráfico do ativo é ajustável arrastando a divisória à esquerda dele (setas ←/→ com a
divisória em foco; duplo clique volta ao padrão); a largura fica salva nas preferências.

### Aba Heatmap

Mapa de calor (treemap) dos ativos com opções listadas (IBOV11 fica fora: é índice).
- **Cor**: Dia / Semana / Mês / Ano (variação em 1, 5, 21 e 252 pregões, janela móvel), Volume
  (volume financeiro do dia ÷ média de 20 pregões; durante o pregão o dia é parcial) ou Negócios
  (da sessão; o MT5 não tem histórico de negócios). Cada bloco mostra ícone, ticker, % e valor bruto.
- **Tamanho**: volume médio de 20 pregões, valor de mercado aproximado (preço do ticker × total
  de ações da B3) ou igual. **Agrupamento** pela classificação setorial da B3.
- **Clique num ativo**: setor/atividade/listagem (B3); variações; volatilidade histórica 20/60/252
  × IV ATM por vencimento (mesma metodologia da análise); resumo técnico calculado com as barras
  do MT5 (RSI 14, EMA 17×34, SMA 50/200, máx./mín. 52 semanas); proventos em dinheiro (data-com,
  pagamento, valor, soma e % dos últimos 12 meses) e eventos em ações (desdobramento, grupamento,
  bonificação, subscrição). Fusões/aquisições não constam da fonte. "Analisar travas" abre a
  Análise com o ativo.
- Fontes: MT5 (preços/volumes) e a API pública de empresas listadas da B3 (cadastro, proventos,
  eventos), com cache em `data/b3/`. A 1ª carga leva ~30 s; depois vem do cache.
- Fontes avaliadas e NÃO usadas: Investing.com (bloqueio anti-robô do Cloudflare), opcoes.net.br
  (termos de uso proíbem acesso automatizado e o robots.txt bloqueia os dados históricos),
  TradingView (só endpoint não oficial; termos restringem uso automatizado).

### Filtro Rafael Nobre (travas de débito)

Opção no formulário de análise, habilitada só para débito:
1. **Perna mais afastada antes do alvo**: com preço-alvo informado, a perna vendida deve ficar
   antes do alvo (alta: strike vendido ≤ alvo; baixa: strike vendido ≥ alvo). Por padrão é
   **preferência** — quem cumpre aparece primeiro no ranking; marque "exigir" para descartar as
   demais. Sem alvo, o critério não é aplicado (a tela avisa).
2. **Custo ≤ 1/4 da distância entre strikes**, medido pelo débito natural (compra no ask, venda
   no bid). Equivale a lucro máximo ≥ 3 × perda máxima. O preço-limite sugerido também respeita
   esse teto.

O ranking mostra a coluna "R. Nobre" (custo em % da largura e posição da vendida) e o detalhe
lista os dois critérios.

### Aba Acompanhamento

Registra estruturas já montadas — travas ou qualquer combinação de opções do mesmo ativo
(borboleta, calendário, diagonal, perna isolada, até 8 pernas) — organizadas em **grupos**.

- Entrada: "+ Nova estrutura" (tickers reais do MT5, validados no catálogo) ou, no detalhe de uma
  trava da Análise, "+ Adicionar ao acompanhamento" (pré-preenche pernas e preço sugerido; ajuste
  para o preço efetivamente executado).
- **Preço de entrada**: o preço líquido por unidade (débito pago ou crédito recebido) basta para
  o P&L total quando todas as pernas têm a mesma quantidade e entram/saem juntas. Informe o preço
  de **cada perna** quando montou as pernas em momentos diferentes, quando as quantidades diferem
  (ex.: 1×2 — nesse caso é obrigatório) ou para ver o P&L por perna. Informe também a data e os
  custos (corretagem/emolumentos), que entram no resultado.
- Clique numa estrutura para vê-la no gráfico do ativo: cada perna no seu strike (compra em
  verde, venda em vermelho) e o breakeven; a escala vertical se ajusta para incluí-los.
- Atualização: cotações das pernas no MT5 (botão ou a cada 60 s). Mostra quanto receberia/pagaria
  para zerar agora pelo **natural** (vende no bid, recompra no ask) e pelo **mid**, P&L não
  realizado (natural, mid e teórico), % do lucro máximo, perda/lucro máximos, breakeven, gregas.
- Alertas: alvo (% do lucro máx.) e stop (R$) opcionais, vencimento próximo/passado, cotação
  antiga ou ausente, exercício antecipado de vendida americana ITM, strike alterado (ajuste por
  provento).
- Grupos: totais de P&L, realizado e risco somado; "Payoff do grupo" junta as estruturas abertas
  do mesmo ativo num payoff agregado.
- Encerramento: preço líquido de saída ou por perna + custos → P&L realizado. Encerramento
  parcial não é suportado diretamente (edite a quantidade e registre a parte zerada como outra
  estrutura encerrada).
- Estruturas com vencimentos diferentes: a curva "no 1º vencimento" e os extremos dependem do
  modelo para as pernas posteriores e são marcados como estimados.
- Dados em `data/acompanhamento.json` (fora do git), com cópia `.bak` da versão anterior.

Filtros avançados (opcionais): cenários conservador/otimista, prazo, strikes, largura, perda
máxima por operação, liquidez mínima por perna, volatilidade própria, juros, custos,
agressividade do preço-limite, lucro/perda mínimo e pesos do ranking. As preferências ficam em
`config/preferencias.json` (sem credenciais; fora do git).

## Arquitetura

```
config/settings.yaml          padrões (MT5, liquidez, pricing, ranking, candles)
config/feriados_b3.csv        feriados B3 (copiado do screener-opcoes; 2027 a confirmar)
src/travas/
  data/                       ÚNICO pacote que importa MetaTrader5
    mt5_client.py             conexão (adaptado do screener-opcoes), somente leitura
    terminal_process.py       abre/fecha o terminal que o app abriu
    market_data.py            cotação, cadeia do ativo (escopo), candles
    normalize.py              symbol_info → tabelas; candles; EMA
    service.py                conexão única com trava (API MT5 não é thread-safe), cache, reconexão
    feasibility.py            relatório `travas check`
  options/                    cálculo puro, testado sem MT5
    models.py                 Leg, Structure, as 4 travas
    payoff.py                 payoff, perda/lucro máx., breakevens (exatos, por pontos de quebra)
    validation.py             valida a trava pelas pernas e pelos preços
    pricing.py, implied_vol.py  Black-Scholes, IV (brentq), IV ATM (do screener-opcoes)
    probability.py            POP, prob. de terminar além do alvo, prob. de toque
    valuation.py              valor teórico pré-vencimento e gregas da estrutura
    liquidity.py              qualidade de cotação e liquidez por perna
    limit_price.py            preço natural, mid, teórico e preço-limite sugerido
    analysis.py               geração, métricas, ranking e simulação temporal
    simulation.py             curvas de P&L de qualquer estrutura (inclusive vencimentos diferentes)
  tracking/                   acompanhamento: modelos, avaliação (P&L, alertas, grupos), store JSON
  api/app.py                  FastAPI (nenhuma rota de ordem); api/tracking_routes.py
  web/static/                 HTML/JS, payoff em SVG, KLineCharts 10.0.4 (empacotado localmente)
tests/                        122 testes: 4 travas, extremos, breakevens, POP, preço-limite, API…
```

## Definições (fonte de verdade: código em `src/travas/options`)

- **Entrada natural** (usada nas métricas): compra no ask, venda no bid. Débito = ask(C) − bid(V);
  crédito = bid(V) − ask(C). **Mid** é só referência.
- Débito: perda máx. = débito, lucro máx. = largura − débito. Crédito: lucro máx. = crédito,
  perda máx. = largura − crédito. Breakeven: alta débito = K_compra + débito; baixa débito =
  K_compra − débito; alta crédito = K_venda − crédito; baixa crédito = K_venda + crédito.
  O motor calcula isso genericamente a partir das pernas; os testes conferem com as fórmulas.
- Valores totais = por ação × opções por perna × `trade_contract_size` (1 na XP).
- **Lucro/Perda** = lucro máximo ÷ perda máxima (o detalhe também mostra perda ÷ lucro).
- **POP**: probabilidade de P&L > 0 **no vencimento**, lognormal neutra ao risco (drift = juros),
  σ = IV ATM do vencimento (calculada sobre o mid) ou volatilidade informada. Sem σ confiável:
  **indisponível**. Não é probabilidade de lucro antes do vencimento.
- **Probabilidade de toque**: princípio da reflexão (MBG contínuo), até o horizonte.
- **Resultado no alvo**: payoff exato no vencimento; com horizonte antes do vencimento, valor
  teórico Black-Scholes por perna (σ da série, ou IV ATM) nessa data.
- **Score** 0–100: Σ peso × percentil entre as travas da análise — resultado no alvo ÷ perda
  máx., lucro/perda, POP, liquidez da pior perna, custo de execução (natural − mid) ÷ largura.
  Componente indisponível tem o peso redistribuído. Perna reprovada (sem book, cotação antiga,
  spread largo, pouco volume/negócios) → excluída por padrão, ou score limitado a 40.
- **Preço-limite**: mid + agressividade × (natural − mid), arredondado ao tick a favor do usuário,
  limitado pela relação lucro/perda mínima e pelo orçamento de perda, com faixa mid↔natural e
  impacto em lucro, perda, breakeven e L/P. Sem bid/ask válido: "não estimável".
- **EMA** (candles): α = 2/(n+1), semente no 1º fechamento das 400 barras coletadas, primeiros n
  valores ocultos. Calculada no backend.

## Limitações conhecidas

- **Open interest indisponível** no MT5 da XP (vem zerado); volume e negócios não substituem OI.
- Gregas, IV e preço teórico da XP vêm zerados: tudo é calculado localmente (Black-Scholes
  europeu, sem dividendos). Calls americanas com provento antes do vencimento e puts americanas
  ficam aproximadas. Datas de proventos não são consideradas.
- Ticks chegam com atraso variável (dezenas de segundos). A idade da cotação é medida contra o
  tick mais recente do mesmo lote; o app avisa quando o último tick do ativo tem mais de 15 min
  (mercado fechado ou feed parado) — nesse caso os dados **não** estão em tempo real.
- `session_deals` de séries sem negócio hoje pode refletir a sessão anterior; a regra de
  cotação antiga (300 s) exclui essas séries do ranking por padrão.
- Candles de 240 min seguem o relógio do servidor (08h, 12h, 16h): a 1ª barra do dia cobre só
  parte do pregão. A barra D1 fica marcada "em formação" até a meia-noite.
- Níveis fora da faixa visível do gráfico de candles aparecem só na legenda abaixo dele.
- Percentis do score são relativos às travas de cada análise (não comparáveis entre análises).
- Somente travas verticais de mesmo vencimento; calendário/diagonal são rejeitadas.
- Feriados de 2027 em `config/feriados_b3.csv` estão marcados "a confirmar".

Opções podem causar perdas relevantes; liquidez pode impedir execução pelo preço indicado. POP e
valores teóricos dependem de modelo e não garantem resultado.
