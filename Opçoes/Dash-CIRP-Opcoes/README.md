# Dash CIRP Opções — travas de opções B3 via MetaTrader 5

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
mercado **fechado** (pré-abertura, após o fechamento, sem pregão), a fonte é escolhida no
indicador de mercado do topo (padrão em `collection.off_hours_source`, a escolha fica salva):

- **Fechamento oficial (B3)** — padrão. Arquivo público "TradeInformationConsolidatedFile" do
  último pregão publicado (`data/b3/negocios_<data>.csv`): cada série pelo **último negócio do
  dia** e o ativo pelo **fechamento** — o mesmo que o ProfitChart mostra com o mercado fechado
  (conferido em 16/10/2026: 82 de 82 séries de BBAS3 iguais). Negócios e volume são os do dia
  inteiro. O arquivo **não traz bid/ask nem horário**: o preço é indicativo (natural = mid =
  último, marcado "B3" nas pernas), não há spread nem idade de cotação para avaliar, e os
  negócios de cada perna podem ter sido em horários diferentes. Série sem negócio no dia fica
  sem preço ("sem negócio no dia (B3)"). Se o arquivo do último pregão ainda não saiu (a B3
  publica à noite) ou estiver inacessível, vale a opção abaixo, com aviso.
- **Capturas do pregão (bid/ask)** — últimas cotações salvas pelo app durante o pregão, com
  prazos recalculados para hoje. Séries nunca capturadas no pregão são lidas do MT5 e marcadas
  como "lida fora do pregão" (podem estar zeradas ou distorcidas).
- **Snapshot do servidor (bid/ask)** — o snapshot mais recente gravado pelo coletor do servidor
  (seção abaixo): bid/ask de todas as séries **no mesmo horário** (11:00 ou 16:30), 3 próximos
  vencimentos mensais (mais semanais até 15 du) e strikes a até 30% do spot. O indicador mostra o horário do snapshot. Sem acesso
  ao servidor, usa o último já baixado (`data/snapshots/`, avisado como "offline"); ativo fora do
  snapshot ou capturas locais mais novas que ele: valem as capturas, com aviso.

Cada coleta salva só as séries do seu escopo, então o arquivo do ativo mistura capturas de
horários diferentes. Ao ler as cotações salvas, a **idade de cada série é medida contra a captura
principal do recorte usado** (a com mais séries; o preço do ativo da análise é o dessa captura),
não contra a última do arquivo — que pode ser uma atualização de 2 pernas do Acompanhamento e
deixaria a cadeia inteira como "cotação antiga" (score limitado a 40*). Uma perna de horas antes vira
"cotação antiga" e não é combinada com outra perna como se fossem do mesmo momento (caso real:
put 21,54 das 11:10 + put 22,04 das 14:06 davam um crédito inflado). Vale para Análise de travas, Ativo
protegido, Acompanhamento e Simulador. O spot de cada análise é o da captura de referência (fora
do pregão) ou o lido junto com o lote mais recente da coleta (pregão aberto).

## Snapshots no servidor (MT5 no Linux)

Um servidor Debian com o MT5 rodando sem tela (Wine + Xvfb, serviços `mt5-xvfb` e
`mt5-terminal` do systemd do usuário) grava snapshots da cadeia em horários fixos. O pacote
`MetaTrader5` só existe para Windows, então o coletor roda num **Python 3.14 para Windows dentro
do mesmo prefixo Wine** (`C:\Python314`), com o código deste repositório em `~/travas`:

```
~/travas/travas.sh snapshot --slot 1100     # coleta agora, rótulo 1100
~/travas/travas.sh b3-archive               # arquiva o fechamento oficial da B3
```

| Unidade (systemd --user) | Quando | O quê |
|---|---|---|
| `travas-snapshot-1100.timer`, `-1630.timer` | seg–sex 11:00 e 16:30 (America/Sao_Paulo) | `travas snapshot`: os 30 ativos com opções mais líquidas (volume financeiro médio das opções nos 5 últimos fechamentos da B3 arquivados) que tenham opções no MT5, do mais líquido ao menos; 3 próximos vencimentos **mensais** (3ª sexta-feira, ou o pregão anterior se for feriado) mais os semanais com até 15 dias úteis, strikes a ±30% do spot |
| `travas-b3-archive.timer` | 22:00 e 07:30 | `travas b3-archive`: `TradeInformationConsolidatedFile` dos últimos 5 pregões que faltarem |
| `snapshots-http.service` | sempre | `python3 -m http.server 8766` só no IP do Tailscale (100.113.24.44), somente leitura |

Feriados da B3 são pulados pelo coletor (calendário do projeto), e horário perdido não é
recuperado (um snapshot das 11:00 nunca é gravado às 13:00). O coletor espera até 15 min pelo
terminal conectado e pelo feed vivo; se não conseguir, grava só o manifesto com status
"falhou". Arquivos em `~/snapshots/<data>/`: `<HHMM>.csv.gz` (colunas da cadeia + `captured_at`),
`<HHMM>.json` (status completo/parcial/falhou, contagens por ativo, erros, terminal) e
`negocios_b3.csv`; `index.json` lista tudo. São imutáveis e formam um histórico (~1–2 MB por
snapshot). O app lê `snapshots.server_url` (`config/settings.yaml`) por qualquer máquina na
mesma rede Tailscale.

A CPU do servidor (AMD A6, sem SSE4.1/AVX) não roda o NumPy ≥ 2.4: lá é instalado o
`numpy==2.3.5` (base SSE3); o restante segue as versões do `pyproject.toml`.

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

## Uso (aba Análise de travas)

1. Escolha direção (alta/baixa), estrutura (débito/crédito) e o ativo.
2. Informe o preço-alvo **ou** a variação esperada (%), e opcionalmente o horizonte (data).
3. "Analisar": o app coleta no MT5 só as séries necessárias (classe de opção da trava, prazo
   máximo e faixa de strikes) — tipicamente 15–30 s; a cadeia fica em cache por 60 s.
4. Clique numa linha do ranking para ver pernas, métricas, payoff, simulação temporal,
   preço-limite e composição do score. O painel do ativo (KLineCharts) mostra os níveis.

**Quantidade ou valor a investir**: depois de analisar, mudar "Opções por perna" ou "valor a
investir (R$)" refaz na hora todos os totais do ranking e do detalhe (perda/lucro máximos,
cenários, garantia, capital, curvas do payoff, saída na data simulada, gregas, preço-limite), sem
nova coleta nem nova análise. Com valor a investir, cada trava usa a maior quantidade múltipla do
lote (`analysis.lot_size`, padrão 100) cujo capital (débito pago ou garantia estimada) cabe no
valor. Com custos fixos > 0, o score continua o da quantidade analisada; travas que passam do
orçamento de perda nessa quantidade recebem o alerta "acima do orçamento".

**Garantia** (coluna "Garantia est." e bloco no detalhe): estimativa pelo risco no vencimento —
obrigação das pernas vendidas não coberta pelas compradas (pior caso, sem prêmios) menos o
crédito recebido. Trava de crédito: largura × quantidade − crédito (= perda máxima); a
"conservadora" é a largura inteira, para corretora que não aceita o crédito como garantia. Trava
de débito: em geral zero (vendida coberta pela comprada; o capital é o débito). Vendida americana
coberta por comprada europeia recebe aviso. O valor real é calculado pela B3 (CORE) e pela
corretora e não vem pelo MT5: confira antes de operar.

**Sair na data simulada** (abaixo do controle de tempo, também no Ativo protegido e no
Simulador): para a data escolhida, quanto custa zerar (recebe/paga, total e por unidade) e o
saldo da operação, no preço atual do ativo, no alvo e num preço digitado. Antes do vencimento é
valor teórico (Black-Scholes, premissas exibidas); no vencimento, o intrínseco. "Saldo pelo
natural" desconta meia largura do book atual de cada perna (spread de saída estimado). A dica do
gráfico de payoff também mostra o valor para zerar em cada preço.

Os gráficos de payoff e de candles têm o botão **⤢ Maximizar** (Esc ou "Restaurar" volta). A
largura do gráfico do ativo é ajustável arrastando a divisória à esquerda dele (setas ←/→ com a
divisória em foco; duplo clique volta ao padrão); a largura fica salva nas preferências.

Gráfico do ativo: tempos **mensal** (100 barras), **semanal**, **diário**, **240 min** e **60 min**
(400 barras cada; configurável em `candles` no `config/settings.yaml`). Ao carregar, todas as barras
ficam visíveis (até 0,25 px por barra); a roda do mouse dá zoom e **⇔ Tudo** volta a mostrar todas.
Se o MT5 tiver menos histórico que o pedido, a nota abaixo do gráfico informa.

### Aba Heatmap

Mapa de calor (treemap) dos ativos com opções listadas (IBOV11 fica fora: é índice).
- **Cor**: Dia / Semana / Mês / Ano (variação em 1, 5, 21 e 252 pregões, janela móvel), Volume
  (volume financeiro do dia ÷ média de 20 pregões; durante o pregão o dia é parcial) ou Negócios
  (da sessão; o MT5 não tem histórico de negócios). Cada bloco mostra ícone, ticker, % e valor bruto.
- **Tamanho**: volume médio de 20 pregões, valor de mercado aproximado (preço do ticker × total
  de ações da B3) ou igual. **Agrupamento** pela classificação setorial da B3.
- **Clique num ativo**: setor/atividade/listagem (B3); variações; volatilidade histórica 20/60/252
  × IV ATM por vencimento (mesma metodologia da análise); resumo técnico calculado com as barras
  do MT5 (RSI 14, EMA rápida × lenta do gráfico, SMA 50/200, máx./mín. 52 semanas); proventos em dinheiro (data-com,
  pagamento, valor, soma e % dos últimos 12 meses) e eventos em ações (desdobramento, grupamento,
  bonificação, subscrição). Fusões/aquisições não constam da fonte. "Analisar travas" abre a
  Análise de travas com o ativo.
- **Seguimento**: a ☆ ao lado do nome no gráfico do ativo (qualquer aba) marca o ativo para
  acompanhar. A lista fica num painel à esquerda do heatmap, recolhido por padrão: preço, variação
  no dia (D), em 21 pregões (M) e desde a estrela (★, comparada ao fechamento exibido no gráfico ao
  marcar), com ordenação; clicar abre o ativo no gráfico e o resumo; × deixa de seguir. Os ativos
  marcados ganham ★ no mapa. Dados em `data/favoritos.json` (fora do git).
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

### Stop 1:1 — Credit Spread Investing (travas de crédito)

Opção no formulário, habilitada só para crédito. Manejo ativo do canal Credit Spread Investing:
a trava é **encerrada quando o prejuízo atinge o lucro máximo**, isto é, quando o custo para
desmontá-la chega a 2 × o crédito (`credit_stop.loss_multiple` = 1 em `config/settings.yaml`).
Com o filtro ligado, cada trava ganha:

- **Fronteira do stop**: preço do ativo que aciona o stop em cada pregão até o vencimento, pelo
  valor teórico de desmontar (Black-Scholes com a IV de cada perna). No vencimento é exata
  (strike vendido ∓ 2 × crédito). A coluna "Stop (ativo)" mostra a mais próxima do spot e a
  distância; o gráfico do ativo ganha a linha "Stop 1:1".
- **Monte Carlo do manejo** (4.000 caminhos lognormais, drift = juros, σ do POP, passo diário
  com ponte browniana para o stop dentro do dia; os mesmos sorteios para todas as travas):
  probabilidade de acionar o stop, de ficar com o crédito inteiro, de lucro com o manejo, e o
  **resultado esperado com o stop** (stop: −crédito − custo de saída; sem stop: crédito − valor
  no vencimento). Custo de saída = natural − mid da trava hoje.
- **Ranking próprio** (pesos em `credit_stop.weights`): resultado esperado com o stop ÷ perda no
  stop (30%), probabilidade de **não** acionar o stop (30%), crédito ÷ garantia (10%), liquidez da
  pior perna (20%: a saída no stop precisa de book) e custo de saída ÷ crédito (10%).
- Ficam fora: crédito ≥ metade da largura (perda máxima ≤ crédito, o stop não se aplica), travas
  em que o preço atual já acionaria o stop (em geral book largo: 2 × crédito natural abaixo do
  valor de desmontar) e travas sem IV para o modelo.

**Leitura importante**: com o crédito igual ao valor teórico, o stop 1:1 tem ~50% de chance em
**qualquer** distância — travas longe do dinheiro pagam pouco, e dobrar um crédito pequeno exige
um movimento pequeno, sobretudo no início (muito valor de tempo). Distância do strike não é, por
si, proteção. O que dá vantagem ao manejo é crédito **acima** do modelo (IV da opção vendida
acima da IV ATM — o skew das puts), custo de saída baixo e liquidez para sair no stop; o ranking
mede exatamente isso. Resultado esperado e probabilidades são de modelo, não garantia.

### Aba Acompanhamento

Registra estruturas já montadas — travas ou qualquer combinação de opções do mesmo ativo
(borboleta, calendário, diagonal, perna isolada, até 8 pernas) — organizadas em **grupos**.

- Entrada: "+ Nova estrutura" (tickers reais do MT5, validados no catálogo) ou, no detalhe de uma
  trava da Análise de travas, "+ Adicionar ao acompanhamento" (pré-preenche pernas e preço sugerido; ajuste
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
- **Totais da carteira** (acima dos grupos): total = P&L aberto pelo natural + realizado; também
  aberto pelo natural e pelo mid, realizado, total pelo mid, risco máximo aberto e custos. Estrutura
  aberta sem cotação fica fora do total aberto e é sinalizada (−n).
- **Relatório das encerradas** (painel expansível abaixo das posições), filtrável por período da
  saída e por grupo: P&L líquido, lucro/prejuízo bruto, taxa de acerto, fator de lucro, payoff,
  expectativa, maior ganho/perda, sequências, drawdown máximo (com datas), fator de recuperação,
  retorno sobre o risco, R médio, SQN, dias médios na operação; gráficos de P&L acumulado com
  drawdown, P&L por mês, por operação, distribuição do R e por ativo; quebras por estrutura,
  sentido (débito/crédito), motivo de saída, grupo e ativo; tabela ordenável das operações.
  R = P&L ÷ perda máxima da estrutura na entrada. Calculado só com os registros (não usa o MT5).
- **Exportar CSV**: todas, abertas ou encerradas (uma linha por estrutura) ou uma linha por perna;
  o relatório exporta as encerradas do período. Formato do Excel pt-BR (`;`, vírgula decimal,
  dd/mm/aaaa, UTF-8 com BOM). Abertas levam o P&L com as cotações do MT5 no momento.
- Dados em `data/acompanhamento.json` (fora do git), com cópia `.bak` da versão anterior.

Filtros avançados (opcionais): cenários conservador/otimista, prazo, strikes, largura, perda
máxima por operação, liquidez mínima por perna, volatilidade própria, juros, custos,
agressividade do preço-limite, lucro/perda mínimo e pesos do ranking. As preferências ficam em
`config/preferencias.json` (sem credenciais; fora do git).

### Google Agenda (vencimentos das estruturas abertas)

Na aba Acompanhamento, **Conectar Google Agenda** cria a agenda "Dash CIRP – Vencimentos" e
mantém nela **um evento por vencimento de cada estrutura aberta** (12:00 do dia do vencimento,
com lembretes ao meio-dia em D-5, D-1 e no próprio dia; pregões pelo calendário da B3). Criar ou
editar uma estrutura cria/atualiza o evento; **encerrar ou excluir apaga o evento**. A
sincronização roda a cada mudança no Acompanhamento, ao abrir o app e a cada 30 min
(`google_calendar` no `config/settings.yaml`: horários, lembretes, intervalo, `enabled`).

- Permissão mínima (`calendar.app.created`): o app só enxerga e altera agendas criadas por ele.
- Credencial: OAuth "App para computador" do Google Cloud (Calendar API ativada), arquivo
  `client_secret*.json` na raiz do projeto (no `.gitignore`). O login e a autorização são feitos
  por você na página do Google; o app recebe o retorno em 127.0.0.1 (PKCE) e nunca vê a senha.
- O token de acesso fica **cifrado pela DPAPI do Windows** (só a sua conta de usuário decifra) em
  `data/google_agenda.json`, com o id da agenda. "Desconectar" revoga o acesso no Google e apaga
  o token (a agenda e os eventos ficam; apague a agenda no Google se quiser).
- Reconciliação: cada evento guarda o id da estrutura e o vencimento em propriedades privadas; a
  agenda é a fonte da verdade (duplicados e eventos de estruturas encerradas são apagados).
- Os testes automáticos rodam com a agenda desligada e nunca acessam a sua conta.

## Aba Ativo protegido (estruturas do Rafael Nobre)

Varre, com **só o ativo como entrada**, duas estruturas de mesmo vencimento por ação comprada:

- **Collar**: compra o ativo, compra 1 put Kp, vende 1 call Kc (Kp < Kc). Vale Kp abaixo da put,
  acompanha o ativo entre os strikes e fica travado em Kc acima.
- **Collar + borboleta**: compra o ativo e 1 put Kp, vende **2** calls K1 e compra 1 call K2
  (Kp < K1 < K2). Vale Kp abaixo da put, acompanha o ativo até K1 (máximo), cai até 2·K1 − K2 em K2
  e fica plano acima. Exemplo do vídeo (BOVA11, put 183, calls 190/195, custo 178,81): queda
  +2,34%, alta forte +3,46%, máximo +6,26% em 190 (o vídeo arredonda para 6,24%) — coberto em
  `tests/test_protected.py`.

Só entram estruturas cujo **piso no vencimento** (menor valor possível) cobre o custo natural de
montagem mais os custos informados — o "risco zero" do vídeo. O piso vale só no vencimento, com
todas as pernas mantidas, sem exercício antecipado das calls vendidas e sem proventos no período.
Pela paridade put-call, com preços justos o piso rende no máximo cerca do CDI; o ganho acima vem
de o ativo terminar entre os strikes.

Ranking (pesos visíveis e editáveis; padrão em `protected` no `config/settings.yaml`): piso,
ativo parado e máximo como % do CDI do período, probabilidade de superar o CDI no vencimento
(lognormal, IV ATM; omitida sem IV confiável), liquidez da pior perna e custo de execução. O
detalhe mostra payoff, simulação temporal, custo-limite indicativo e as pernas para digitar no
ProfitChart. Estruturas com ação ainda não podem ser enviadas ao Acompanhamento.

**Quantidade ou valor a investir** (antes ou depois do scan, sem nova coleta): os dois campos são
ligados — digitar a quantidade (ações = puts) mostra o investimento; digitar o valor mostra a
quantidade, arredondada para baixo a múltiplos de `protected.lot_size` (100). No modo valor, cada
estrutura usa a maior quantidade que cabe no valor (custo diferente por estrutura). Lista,
detalhe, gráfico e pernas são recalculados no navegador a partir dos valores por ação; com custos
fixos informados, os retornos mudam com a quantidade, mas a ordem do score continua a do scan.

**Call vendida só europeia**: checkbox que só filtra a lista já calculada (sem novo scan). A API
devolve as `max_results` melhores no geral e as `max_results` melhores com call vendida europeia,
então o filtro mostra até 200 europeias mesmo quando elas não estão entre as 200 melhores gerais.

**Débito ou crédito**: a operação completa é sempre débito (compra do ativo). A coluna "Opções" e
o alerta no detalhe mostram se o **pacote de opções** (put comprada − calls vendidas + call
comprada), sozinho, sai a débito (você paga além do ativo) ou a crédito (as calls vendidas pagam a
put e sobra caixa), pelo natural; ⚠ indica que pelo mid o sentido é outro.

## Aba Simulador

Monta qualquer estrutura de um ativo: opções de qualquer vencimento (calendário/diagonal
incluídos) e o próprio ativo (venda coberta, collar…), até 12 pernas.

- **Grade do vencimento**: calls e puts com bid/ask/IV (strikes a ±30% do spot, ATM centralizado,
  ITM com fundo leve); **C** compra e **V** vende a série na "quantidade por clique". Clicar de
  novo soma; o lado oposto reduz (zerou, a perna sai). A grade marca a posição montada.
- Ou digite o ticker (Enter = compra, Shift+Enter = venda) e use **+ Ativo (compra/venda)**.
- Na tabela de pernas: lado, quantidade, **preço** (vazio = natural do book: compra no ask, venda
  no bid; sem book, último negócio sinalizado) e **vol.** (vazia = vol. geral ou IV da série).
  Tudo é recalculado ao editar; "Inverter lados" troca compra ↔ venda.
- Resultado: payoff no vencimento (exato; com vencimentos diferentes, no 1º vencimento com as
  pernas posteriores pelo modelo), valor teórico na data simulada, sair na data simulada, zerar
  agora (natural e mid), POP (só com um vencimento; σ = média das σ das opções), gregas e garantia
  (não estimável com call vendida a descoberto ou vencimentos diferentes).
- Avisos: cotação antiga/sem book, pernas capturadas em momentos diferentes, preço digitado
  manualmente, risco de exercício antecipado em vendida americana ITM.
- Pernas, vencimento e premissas ficam salvos nas preferências.

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
    b3_trades.py              fechamento oficial da B3 (último negócio do dia) com o mercado fechado
    snapshots.py              snapshots do servidor: gravação, índice, cliente HTTP, cadeia por ativo
    snapshot_collector.py     `travas snapshot` (servidor com MT5): coleta de todos os ativos
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
    credit_stop.py            stop 1:1 das travas de crédito: fronteira do stop e Monte Carlo do manejo
    margin.py                 garantia estimada pelo risco no vencimento e spread de saída
    simulator.py              aba Simulador: pernas livres (opções e o próprio ativo)
  tracking/                   acompanhamento: modelos, avaliação (P&L, alertas, grupos), store JSON;
                              gcal.py (Google Agenda: OAuth, API, reconciliação), secure_store.py (DPAPI)
  api/app.py                  FastAPI (nenhuma rota de ordem); api/*_routes.py por aba
  web/static/                 HTML/JS, payoff em SVG, KLineCharts 10.0.4 (empacotado localmente)
tests/                        223 testes: 4 travas, extremos, breakevens, POP, preço-limite, garantia, simulador, API…
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
- **EMA** (candles): α = 2/(n+1), semente no 1º fechamento das barras coletadas, primeiros n
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
