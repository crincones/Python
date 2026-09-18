# CLAUDE.md — Screener de Travas de Débito (B3 via MetaTrader 5 / XP)

## Visão geral

Aplicação Python que roda no **Windows**, lê a grade de opções de ações da B3 pelo terminal
MetaTrader 5 da XP Investimentos, filtra as séries mais líquidas e ranqueia oportunidades de
**trava de débito de alta (bull call spread)** e **trava de débito de baixa (bear put spread)**.
A saída é um **relatório HTML estático** (arquivo único, abre com duplo clique, funciona offline).

O viés direcional de cada ativo-objeto vem de leitura em gráfico diário/4h: um sinal automático
por tendência em D1/H4 sugere o viés e o viés manual do YAML sempre prevalece. O screener só
ranqueia travas de alta em ativos com viés comprador e travas de baixa em ativos com viés vendedor.

Isto é uma ferramenta de apoio à decisão. **Nunca** enviar ordens. Não usar `order_send`,
`order_check` ou qualquer função de trading da API do MT5 neste projeto.

## Stack e ambiente

- Windows 10/11, PowerShell
- Python 64 bits (mesma arquitetura do terminal MT5). Antes de subir a versão do Python,
  confirmar no PyPI que o pacote `MetaTrader5` já suporta a versão
- Gerenciador: `uv` (`pyproject.toml` + `uv.lock`)
- Bibliotecas: `MetaTrader5`, `pandas`, `pyarrow`, `duckdb`, `numpy`, `scipy`, `jinja2`,
  `pyyaml`, `pydantic`, `typer`, `plotly`, `paramiko`
- Testes: `pytest`. Lint/format: `ruff`

## Comandos

```powershell
uv sync                                   # instala dependências
uv run screener check                     # valida conexão e campos de opção expostos pela XP
uv run screener collect                   # grava snapshot em data/snapshots/
uv run screener analyze --snapshot latest # calcula IV, métricas, score
uv run screener report  --snapshot latest # gera output/relatorio_YYYYMMDD_HHMM.html e publica
uv run screener publish --snapshot latest # só envia o relatório para o servidor (ou --file <html>)
uv run screener run [--force]             # collect + analyze + report + publish (sai fora de pregão)
#   report/run aceitam --no-publish para não enviar nada ao servidor
uv run screener fixture --snapshot <nome> # copia snapshot p/ tests/fixtures/ sem dados da conta
uv run pytest                             # testes offline (sem MT5)
uv run pytest -m mt5                      # testes que exigem terminal aberto e logado
uv run pytest -m network                  # testes que acessam a API da B3
uv run ruff check . ; uv run ruff format .
```

Scripts Windows (ASCII puro; PowerShell 5.1 lê .ps1 sem BOM como ANSI):

```powershell
executar_screener.bat [-Forcar] [-Etapa report] [-SemPublicar]   # duplo clique: roda e abre
.\scripts\executar_screener.ps1 [-Etapa run|collect|analyze|report|publish|check] [-Forcar]
                                 [-SemPublicar] [-ManterTerminal] [-AbrirRelatorio]
.\scripts\agendar_tarefas.ps1 [-Horarios 10:30,13:00,16:30] [-Remover]   # tarefa "Screener Opcoes B3"
.\scripts\criar_atalho.ps1                         # atalho "Relatorio-Opcoes" (Área de Trabalho → output\)
```

Os caminhos devem sempre usar `pathlib.Path`. Nunca concatenar strings com `\` ou `/`.

## Arquitetura

```
config/settings.yaml          ativos-objeto, viés direcional, filtros, janela de DTE, pesos, taxa livre de risco, publicação
config/feriados_b3.csv        feriados B3 (2023–2026 conferidos no D1 do MT5; futuros a confirmar)
config/proventos.csv          datas ex de proventos (manual): underlying,ex_date(AAAA-MM-DD),description
src/screener/
  collector/                  ÚNICO pacote que importa MetaTrader5
    mt5_client.py             initialize/shutdown, retry, symbol_select em lotes com heartbeat
    field_audit.py            comando check
    universe.py               estatísticas dos ativos-objeto e cotações das séries
    snapshot.py               grava spot + cotações das opções em Parquet
  calendar_b3.py              pregões / dias úteis
  universe_rules.py           filtro do ativo-objeto, pré-filtro de séries, detecção de feed parado
  timeutils.py                conversão do relógio do servidor MT5
  data/schema.py              colunas de todas as tabelas (fonte de verdade)
  data/normalize.py           symbol_info bruto → tabela options
  data/store.py               leitura/gravação dos snapshots (DuckDB sobre Parquet)
  data/dividends.py           leitura de config/proventos.csv
  data/fixtures.py            exporta snapshot para tests/fixtures sem dados da conta
  pricing/black_scholes.py    preço, gregas, probabilidade ITM
  pricing/implied_vol.py      IV a partir do mid (scipy.optimize.brentq) e IV ATM por vencimento
  liquidity.py                filtros e score de liquidez por série
  spreads/builder.py          gera pares válidos de trava
  spreads/metrics.py          débito, ganho máximo, breakeven, R/R, POP
  spreads/alerts.py           alerta de exercício antecipado
  analysis.py                 orquestra a etapa de análise (IV → liquidez → travas → alertas)
  market_data/b3_indicators.py  CDI oficial da API dos Indicadores Financeiros da B3
  signals/direction.py        viés por ativo: sinal automático D1/H4 (EMAs) + viés manual do YAML
  scoring.py                  faixa de POP, score ponderado por percentis e ranking pelo viés
  report/render.py            Jinja2 → HTML
  report/templates/
  publish.py                  envio do HTML por SFTP para o servidor da tailnet (ÚNICO com paramiko)
  cli.py                      Typer
tests/fixtures/               snapshots reais salvos para testes offline
data/snapshots/AAAAMMDD_HHMMSS/  saída do coletor e da análise (não versionar):
                              underlyings/options.parquet + meta.json (collect);
                              + bars.parquet (collect, barras D1/H4);
                              series/spreads/bias.parquet + analysis_meta.json (analyze)
output/                       relatórios HTML (não versionar)
```

### Regras de arquitetura

- `import paramiko` só pode existir em `src/screener/publish.py`; a lógica de envio é escrita
  contra o protocolo `RemoteFiles` e testada offline com um dublê (`tests/test_publish.py`).
- `import MetaTrader5` só pode existir dentro de `src/screener/collector/`. Todos os outros módulos
  recebem e devolvem `pandas.DataFrame` ou modelos pydantic, e devem ser testáveis sem o terminal.
- O pipeline é por etapas com artefato em disco entre elas: coleta → Parquet → análise → Parquet
  → relatório → publicação. Qualquer etapa pode ser reexecutada a partir do snapshot, fora do horário de pregão.
- Parâmetros de negócio (filtros, pesos, DTE, largura máxima, taxa) ficam em `settings.yaml`,
  validados por pydantic. Nada de números mágicos no código.
- Funções de pricing são puras e vetorizadas com numpy.

## API MetaTrader5: cuidados

- Checar o retorno de toda chamada. Em falha, a API retorna `None`/`False`; logar `mt5.last_error()`.
- `mt5.initialize(path=..., portable=True, timeout=...)` recebe o caminho do `terminal64.exe` da XP,
  que vem de `settings.yaml`. O terminal da XP roda com **`/portable`** (dados na própria pasta
  `Metatrader5B3`); abrir sem essa flag usa outra pasta de dados, sem o login salvo. Não guardar
  senha em código ou YAML versionado; o login vem do perfil salvo no próprio terminal.
- **Ciclo de vida do terminal** (`collector/terminal_process.py`, `MT5Client` como contexto):
  se não houver `terminal64.exe` rodando a partir desse caminho, o screener abre com `/portable`
  minimizado sem foco, espera conexão + conta + lista de símbolos estável
  (`startup_timeout_seconds`) e, ao sair (com sucesso ou erro), fecha **só os processos que ele
  abriu** (diferença de PIDs antes/depois, cobre reinício por atualização): primeiro
  `CloseMainWindow` e, após `shutdown_timeout_seconds`, encerramento forçado. Terminal aberto
  pelo usuário (gráficos, robôs, serviços) **nunca** é fechado. `--keep-terminal` (CLI) ou
  `-ManterTerminal` (script) mantém aberto o terminal que o screener abriu.
- A API não é thread-safe: uma conexão, um processo, sem multiprocessing sobre o MT5.
- `symbols_get(group=...)` lista símbolos do servidor, mas bid/ask/último só são confiáveis para
  símbolos selecionados no Market Watch. Selecionar em lotes, coletar e depois
  `symbol_select(name, False)` para não sobrecarregar o terminal.
- Um padrão como `"PETR*"` também traz o próprio ativo e outros instrumentos. Identificar opções por
  `option_right`/`option_mode`/`option_strike`/`expiration_time`/`basis`, nunca só pelo nome.
- Campos como `price_volatility`, `price_theoretical`, `price_delta` e demais gregas, além de
  `session_interest`, podem vir zerados na XP. O comando `screener check` deve reportar quais
  campos vêm preenchidos. Tratar zero como "ausente" e calcular localmente.
- Timestamps do MT5 estão no horário do servidor da corretora, não necessariamente em UTC.
  Converter explicitamente e armazenar com timezone `America/Sao_Paulo`.
- Cotação velha: descartar séries com bid ou ask igual a 0, ask < bid, ou último tick mais antigo
  que o limite configurado.

### O que a XP entrega (medido com `screener check` em 2026-09-17, build 6182, XPMT5-PRD)

- ~50 mil opções em 48 ativos-objeto, todas em `BOVESPA\OPCOES`. `option_strike > 0` identifica opção.
- `option_right`: 0 = call, 1 = put. `option_mode`: 0 = europeia, 1 = americana. Todas as puts
  vieram europeias; calls vêm misturadas (americanas e europeias).
- Preenchidos: bid, ask, last, time, `expiration_time`, `basis`, `session_deals`,
  `session_volume` (quantidade), `session_aw` (preço médio), `session_close`.
- **Zerados**: `session_turnover`, `session_interest` (open interest), `session_price_settlement`,
  `price_volatility`, `price_theoretical` e todas as gregas.
- Volume financeiro da série = `session_volume × session_aw × trade_contract_size`.
- Open interest não está disponível no MT5 da XP; o filtro de OI fica desativado
  (`min_open_interest: null`) até existir outra fonte.
- `expiration_time` vem 23:59:59 do dia de vencimento; há vencimentos em dias que não são sexta
  (ex.: quinta antes de feriado), por isso usar sempre o campo.
- Timestamps: o epoch é o relógio de parede de Brasília codificado como se fosse UTC
  (`screener.timeutils.server_epoch_to_local`).
- Os ticks chegam atrasados em relação ao relógio do PC (conferido com hora da internet), e o
  atraso **varia** (16 s a 80 s no mesmo dia): é atraso do feed/fila do terminal, não fuso ou
  relógio fixo. O `check` reporta esse atraso. A idade da cotação é medida contra o tick mais
  recente lido no mesmo lote, nunca contra o relógio do PC.
- IBOV11 (opções de índice) aparece em `BOVESPA\A VISTA`, não em `INDICES`. **Exposição a índice
  é via BOVA11**; IBOV11 fica sempre fora do universo (`underlying_filter.excluded_underlyings`).

### Coleta: comportamento do terminal sob carga (medido em 2026-09-17)

- Muitas assinaturas seguidas (`symbol_select`) congelam o terminal inteiro por alguns segundos:
  até símbolos fixos no Market Watch param de atualizar, e `symbol_info` devolve cotação zerada.
  Uma vez o servidor chegou a derrubar a conexão (diário do terminal: "connection lost").
- Reconectar a API Python (`shutdown`/`initialize`) não resolve; esperar ~10–15 s resolve.
- Por isso o coletor: seleciona em lotes de 100; só libera o lote quando o tick do ativo-objeto
  avança (heartbeat) e a contagem de séries com tick estabiliza; valida cada ativo com
  `feed_problem` e, se o feed parecer parado, pausa e repete; se persistir, **aborta sem gravar**.
- Coleta completa (20 ativos, ~11 mil séries, strikes ±30% do spot): ~6,5 min.

## Regras de domínio (B3)

- Lote padrão de opções de ações: 100. Valores do relatório por lote e por opção.
- Ticker: 4 letras do ativo + letra de série + número. Letras A–L = calls de jan–dez;
  M–X = puts de jan–dez. Séries semanais podem ter sufixo (ex.: `W1`–`W5`). A convenção do ticker
  é **apenas fallback**; a fonte de verdade são os campos do `symbol_info`.
- Vencimento mensal na 3ª sexta-feira do mês; semanais também vencem na sexta. Usar
  `expiration_time` quando disponível.
- Estilo de exercício via `option_mode` (americana x europeia). Na prática, as calls de ações
  costumam ser americanas e as puts europeias, mas nunca assumir: ler o campo.
- Strikes de opções de ações são ajustados pela B3 por proventos em dinheiro. Portanto, **não
  cachear strike entre snapshots**: sempre regravar a partir do `symbol_info`. (Confirmar a regra
  vigente no manual de procedimentos da B3 antes de depender dela em cálculos.)
- Prazo em **dias úteis / 252** (convenção brasileira). Feriados B3 em `config/feriados_b3.csv`.
- Taxa livre de risco: CDI anual ("TAXA CDI CETIP") buscado na B3 **na coleta** e gravado em
  `meta.json` (`risk_free_rate`: annual, source, reference_date, note), convertido para contínua.
  A análise usa a taxa do snapshot (reprodutível); falha na B3 ou `risk_free_rate_source: yaml` →
  `market.risk_free_rate_annual`, com o motivo registrado e exibido no relatório. A API devolve o
  JSON codificado duas vezes quando chamada com `Accept: application/json`.

## Seleção do universo (duas etapas)

1. **Filtro inicial pelo ativo-objeto**: volume financeiro médio diário do à vista nos últimos
   N pregões (D1) acima do mínimo, com número mínimo de séries listadas; mantém os N mais
   líquidos (`underlying_filter` no YAML). Serve só como porta de entrada.
2. **Decisão pela liquidez da própria série** (critério principal): spread bid/ask reduzido,
   volume financeiro elevado, número de negócios elevado e open interest relevante (quando houver
   fonte). Séries com baixo volume, poucos negócios ou book muito aberto são descartadas pelos
   mínimos de `series_liquidity`; as restantes recebem score de liquidez ponderado pelos pesos do
   YAML (peso de OI redistribuído enquanto não houver fonte).

## Definições de métricas (fonte de verdade)

Para trava com perna comprada L e vendida S, largura W = |K_S − K_L|:

- **Débito realista** = ask(L) − bid(S). É o valor usado no score.
- **Débito mid** = mid(L) − mid(S). Só informativo.
- **Custo de execução** = débito realista − débito mid; também em % de W (usado no score).
- **Ganho máximo** = W − débito realista. **Perda máxima** = débito realista.
- **R/R** = ganho máximo / débito realista. **Débito/largura** = débito realista / W.
- **Breakeven**: alta = K_L + débito; baixa = K_L − débito.
- **Distância ao breakeven**: em % do spot e em desvios padrão (σ = IV × √T × spot).
- **POP**: probabilidade de o ativo terminar além do breakeven no vencimento (lognormal com IV do
  ATM do vencimento). Aproximação: documentar na UI que é Black-Scholes europeu.
- **IV**: calculada sobre o mid de cada série (Black-Scholes europeu, sem dividendos, `brentq`
  na faixa `pricing.iv_lower_bound`–`iv_upper_bound`). Se o mid estiver fora dos limites de
  não-arbitragem, fora da faixa ou não convergir, marcar NaN com `iv_status` e excluir a série.
- **Convenções de pricing**: T = dias úteis / 252; r contínua = ln(1 + CDI anual), de modo que
  e^(rT) = (1 + CDI)^(du/252); spot = `underlying_price` lido junto com a série. Calls americanas
  sem dividendos = europeias; com proventos antes do vencimento o preço é aproximação.
- **Taxa**: CDI oficial vem da B3 (Indicadores financeiros, "TAXA CDI CETIP"; 13,90% em
  16/09/2026). A paridade put-call dos pares europeus ATM de BOVA11 embute ~1 p.p. a menos,
  ~12,9% a.a. (VALE3/PETR4/PRIO3 ~12,7–13,6%). Ativos com taxa implícita bem menor (ABEV3, BBSE3,
  UGPA3, CYRE3) indicam provento antes do vencimento — insumo para o alerta de exercício antecipado.
- **Liquidez da série**: spread bid/ask % do mid, volume financeiro, número de negócios no dia e
  open interest (quando houver fonte). Reprova quem falha em qualquer mínimo de `series_liquidity`
  (sem book, cotação velha, prêmio mínimo, spread, volume, negócios, OI). **Score** 0–1 = média
  ponderada dos percentis de cada componente entre as séries aprovadas **do mesmo ativo-objeto**
  (sem OI configurado/disponível, o peso de OI é redistribuído).
  A trava herda a **pior** liquidez entre as duas pernas.
- **IV ATM do vencimento** (usada em σ e POP): média da IV da call e da put de strike mais próximo
  do spot, entre séries com spread ≤ `pricing.atm_max_spread_pct_mid` e strike a até
  `pricing.atm_max_strike_distance_pct` do spot. Sem candidata → travas do vencimento invalidadas.
- **POP** usa a medida neutra ao risco (drift r) e o spot lido junto com a perna comprada.
  Distâncias ao breakeven são positivas quando o ativo precisa andar a favor da trava.
- **Travas inválidas** (descartadas): débito realista ≤ 0, débito realista ≥ W, ou sem IV ATM.
- Pares válidos: mesmo ativo-objeto, mesmo vencimento, mesmo tipo (call com call, put com put),
  strike da vendida acima (alta) ou abaixo (baixa) da comprada, W ≤ largura máxima do YAML.

## Score e ranking (decisão de 2026-09-17)

- Nos dados reais, R/R, débito/largura, POP e distância em σ medem o **mesmo trade-off** (|ρ| ≥ 0,97
  entre percentis; R/R e débito/largura são função um do outro). Somá-los fazia o score virar só
  liquidez. Por isso:
- **Perfil** = filtro `scoring.pop_min` ≤ POP ≤ `scoring.pop_max` (padrão 35%–60%).
- **Score** 0–100 = Σ peso × percentil, com percentis calculados **por estratégia** entre as travas
  dentro da faixa: custo de execução % W (menor é melhor), liquidez da trava (maior), R/R (maior).
  Pesos em `scoring.weights`.
- **Ranking**: trava dentro da faixa e com direção igual ao viés final do ativo; `rank` 1 = maior
  score na estratégia. Fora da faixa: score NaN. Viés neutro: nada ranqueado para o ativo.

## Viés direcional

- **Sinal automático** (`signals`, sugestão): em cada timeframe, alta se fechamento > EMA lenta e
  EMA rápida > EMA lenta; baixa no espelho; senão neutro; menos de `min_bars` barras → neutro.
  Viés automático = tendência comum a D1 e H4; se discordarem, neutro. A última barra pode estar
  em formação (reflete o preço do momento da coleta).
- **Viés manual** (`bias` no YAML: alta/baixa/neutro) sempre prevalece. Fonte registrada em
  `bias_source` (manual, automático, sem sinal).

## Risco de exercício antecipado (alerta obrigatório)

Toda trava cuja perna vendida seja **americana** recebe um alerta no relatório quando a vendida
estiver ITM com valor extrínseco abaixo do limite do YAML (ex.: < 2% do prêmio ou < R$ 0,02),
ou quando houver data ex de provento antes do vencimento (datas informadas manualmente em
`config/proventos.csv`; o MT5 não fornece). Travas com vendida europeia não recebem o alerta.
O alerta **não** remove a trava do ranking: só sinaliza.

## Relatório HTML

- Arquivo único, CSS e JS inline, sem dependência de rede. Plotly embutido uma única vez.
- Cabeçalho: horário do snapshot, spot de cada ativo e viés direcional usado.
- Uma tabela para travas de alta e outra para baixa, ordenáveis, com: ativo, vencimento, DTE,
  strikes, débito realista e mid, débito/largura, R/R, breakeven, distância em σ, POP, IV das
  pernas, liquidez, alertas, score.
- Clicar na linha abre o gráfico de payoff no vencimento com spot e breakeven marcados.
- Textos da interface em português do Brasil. Números no formato brasileiro (vírgula decimal).
- Implementação (`report/render.py` + `report/templates/relatorio.html.j2`): dados num
  `<script type="application/json">` (NaN proibido, `</` escapado); tabelas e gráfico montados em
  JS; tema claro/escuro por `prefers-color-scheme` (tokens em `:root`); ~6,7 MB por causa do
  Plotly embutido.
- Visão padrão "melhor por ativo e vencimento" (maior score do grupo, demais expansíveis) para o
  topo não repetir variações da mesma trava; alternativa "Todas". Filtro por ativo e opção de
  incluir travas da faixa de POP fora do viés (só consulta, sem posição no ranking).
- Só travas dentro da faixa de POP vão para o HTML.
- Payoff por lote: área de ganho azul e de perda vermelha (par divergente), rótulos de ganho e
  perda máximos em texto, spot tracejado e breakeven pontilhado.

## Publicação do relatório (decisão de 2026-09-17)

- O relatório fica em **http://100.113.24.44/screening.html** (IP Tailscale do `debian-server`),
  acessível de qualquer dispositivo da tailnet. Histórico navegável em `/relatorios/`.
- Windows → servidor por **SFTP** (`src/screener/publish.py`, bloco `publish` do YAML):
  - envia para `/srv/screener/relatorios/relatorio_AAAAMMDD_HHMM.html` com sufixo `.partial` e
    só então renomeia (`posix_rename`), para o navegador nunca pegar um HTML pela metade;
  - `screening.html` é um **link simbólico relativo** para o relatório da execução, trocado de
    uma vez por rename atômico (funciona mesmo se hoje for arquivo comum);
  - retenção: mantém os `keep_reports` mais recentes (padrão 20, ~6,7 MB cada) e apaga restos
    `.partial`; nunca apaga o alvo do link recém-criado.
- Autenticação por chave **ed25519 sem passphrase** (`~/.ssh/screener_deploy`, pública em
  `~carlos/.ssh/authorized_keys` no servidor). Nenhuma senha em código, YAML ou disco. Host key
  conferida em `~/.ssh/known_hosts` (`strict_host_key: true` → recusa conexão se não bater).
- Falha na publicação **não** derruba a execução: o HTML em `output\` continua válido e o motivo
  vai para o log. O comando `screener publish` isolado sai com código 1 em caso de falha.
- Servidor (Debian 13 trixie, configurado em 17/09/2026):
  - `nginx` em `/etc/nginx/sites-available/screener` com `listen 100.113.24.44:80` — **só** o IP
    Tailscale; site `default` desabilitado. Com gzip, os 6,7 MB descem em ~1,7 MB.
  - `net.ipv4.ip_nonlocal_bind = 1` (`/etc/sysctl.d/99-screener-nonlocal-bind.conf`) e drop-in
    `nginx.service.d/tailscale.conf` (`After=tailscaled.service`): o nginx sobe no boot mesmo
    antes de o IP da tailnet existir.
  - `ufw` está ativo e liberava só a 22: regra `allow in on tailscale0 to any port 80 proto tcp`.
    A porta 80 continua fechada na LAN 192.168.0.x.
  - `/srv/screener` e `/srv/screener/relatorios` pertencem a `carlos` (envio sem sudo).
  - Disco raiz pequeno (13 GB, ~2 GB livres em 17/09/2026) — daí a retenção obrigatória.

## Agendamento (decisão de 2026-09-17)

- Tarefa "Screener Opcoes B3" no Agendador do Windows: seg–sex às 10:30, 13:00 e 16:30, usuário
  logado (LogonType Interactive, o MT5 precisa estar aberto na sessão), sem instâncias
  simultâneas, limite de 1 h, execuções perdidas não são repetidas.
- Feriados B3: `screener run` consulta `config/feriados_b3.csv` e encerra sem coletar.
- Cada execução publica o relatório no servidor (http://100.113.24.44/screening.html); se o
  servidor estiver fora do ar, a execução termina normalmente com o erro no log.
- Saída: relatórios em `output\` (atalho "Relatorio-Opcoes" na Área de Trabalho); logs em
  `logs\screener.log` (aplicação) e `logs\execucao_AAAAMMDD.log` (script, inclui erros do uv).

## Convenções de código

- Identificadores em inglês; textos de interface, logs voltados ao usuário e docstrings podem
  ser em português.
- Type hints em tudo; `from __future__ import annotations`.
- Colunas de DataFrame em `snake_case` e documentadas em `src/screener/data/schema.py`.
- `logging` padrão (nada de `print`), log em `logs/` com rotação.
- Nenhuma exceção silenciosa: `except Exception: pass` é proibido.

## Testes

- `tests/fixtures/` guarda snapshots reais capturados com `screener collect` e exportados com
  `screener fixture` (remove login e caminhos locais do `meta.json`). Fixtures atuais, expostas em
  `tests/conftest.py`:
  - `snapshot_20260917_112013` (17/09/2026 11:20, 20 ativos, 10.954 séries):
    `fixture_options` / `fixture_underlyings`.
  - `snapshot_20260917_122706` (17/09/2026 12:27, com barras D1/H4): `bars_fixture_options` /
    `fixture_bars`. Regressão do sinal: VALE3 baixa, BOVA11 alta, PETR4 neutro.
  Todo teste de pricing, spreads, scoring e report roda sobre fixtures, sem o MT5.
- `tests/test_publish.py` roda sem rede: `FakeRemote` implementa o protocolo `RemoteFiles` e
  cobre ordem do envio, troca do link público e retenção.
- Pricing testado contra valores de referência conhecidos (put-call parity, preço BS tabelado,
  recuperação de IV a partir de preço gerado com IV conhecida).
- Testes que exigem o terminal levam `@pytest.mark.mt5` e ficam fora da execução padrão.
- Ao alterar uma fórmula da seção "Definições de métricas", atualizar esta seção e os testes juntos.

## Fluxo de trabalho esperado

- Antes de mudanças grandes, apresentar plano e aguardar confirmação.
- Implementar em fases, na ordem: `check` → coletor → fixture → pricing → builder/métricas →
  scoring (+ sinais automáticos, antecipados a pedido do usuário) → relatório → agendamento
  (Agendador de Tarefas do Windows). Todas as fases implementadas em 2026-09-17.
- Rodar `uv run pytest` e `uv run ruff check .` antes de declarar uma tarefa concluída.
- Na dúvida sobre um campo do MT5 ou uma regra da B3, perguntar em vez de supor.
