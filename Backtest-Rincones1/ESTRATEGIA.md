# Estratégia Rincones1 — Especificação

**Ativo:** WIN (mini índice) · **Gráfico:** candle de 10.000 ticks · **Lado:** compra e venda

Este documento é o **contrato** que `engine.py` implementa. Toda regra aqui é verificável no código; todo número em [RESULTADOS.md](RESULTADOS.md) sai de rodar `python rodar.py`.

---

## 1. A ideia

Um gatilho único de **esforço** decide *quando* algo aconteceu. As **três médias** decidem *que tipo* de coisa aconteceu — e, portanto, se o trade é a favor ou contra o movimento.

O gatilho sozinho não sabe distinguir "pullback numa tendência" de "esticada boa para desmanchar". As médias sabem. É por isso que a mesma barra vira compra num regime e venda em outro.

---

## 2. O gatilho de esforço

Reimplementação exata do indicador já validado em `ProfitChart/Indicadores/Grafico-Ticks/Ticks_Esforco_Reversao.ntsl`, com o eixo **E2 na versão nova** — a de `Ticks_Esforco_Hist_v2.ntsl`. Aqueles dois arquivos têm o histórico completo de como cada peça foi medida.

Em barra de tick o **número de negócios é constante** — toda barra tem 10.000. Então "esforço" não pode ser contagem de negócio. O que varia são três coisas, medidas **separadamente** e convertidas cada uma em **percentil das 20 barras válidas anteriores**:

| eixo | fórmula | o que captura |
|---|---|---|
| **E1 volume** | `AgrBuy + AgrSell` | tamanho médio do lote atravessando o livro |
| **E2 vaivém** | `(\|delta\|/esforço) × volta`, com `volta = 1 − \|Close−Open\|/percurso` e `percurso = 2·(High−Low) − \|Close−Open\|` | agressão de um lado só que terminou desfeita — o quanto do caminho andado dentro da barra foi refeito de volta |
| **E3 tempo** | `1 / BarDurationF()` | velocidade: quão rápido os 10.000 negócios saíram |

> **O eixo E2 mudou.** Ele era `|delta| / |Close−Open|`: agressão por ponto de *saldo*. Saldo não é caminho — uma barra que sobe 60, cai 65 e fecha 30 acima da abertura tem o mesmo `|Close−Open|` de uma que sobe 30 em linha reta. `percurso` é o menor caminho compatível com o OHLC, e `volta` é a fração dele que foi desfeita. As duas peças entram como **produto de frações entre 0 e 1, não como razão**: razão entre peças de dispersão muito diferente mede só a mais volátil das duas (é por isso que `|delta| / percurso`, a troca óbvia, não serve — vira `|delta|` disfarçado, ρ +0,93). Derivação e medição em `Ticks_Esforco_Hist_v2.ntsl`; o efeito no backtest está em [RESULTADOS.md § 2](RESULTADOS.md).

> `BarDurationF()` devolve **minutos**, não milissegundos. A coluna `BarDurationF*1000` do CSV exportado é milésimo de minuto. Conferido contra o relógio do pregão: razão 1,0032.

`índice = média dos três percentis`, de 0 a 1.

### Condições do gatilho

```
índice ≥ 0,80
delta ≠ 0
posMediaCorpo = ((Open+Close)/2 − Low) / (High−Low) × 100
    delta COMPRADOR  → exige posMediaCorpo ≤ 50   → sinal de VENDA
    delta VENDEDOR   → exige posMediaCorpo ≥ 50   → sinal de COMPRA
corpo/range ≤ 50%
E2 NÃO é o eixo dominante   (descarta se pD ≥ pV e pD ≥ pT)
```

**O sinal sai sempre contra quem agrediu.** Esforço alto que não comprou deslocamento é absorção, e absorção se desfaz.

Duas condições merecem nota porque foram medidas, não escolhidas:

- **`corpo ≤ 50%`** é obrigatório com entrada por ordem limitada. Sem ele, a distância entre o fechamento do sinal e o meio do candle sobe de ~20 para ~35 pontos, e você só é preenchido nos sinais que primeiro andaram contra — seleção adversa mecânica.
- **`E2 não dominante`** vem de uma medição independente: quando o eixo do deslocamento é o maior dos três, a leitura do indicador falha (mede negativo nos dois arquivos). É o filtro de maior ganho isolado. **Ele foi remedido com a fórmula nova de E2 e continua valendo** — ver [RESULTADOS.md § 2](RESULTADOS.md).

---

## 3. O contexto: a média de regime

O regime é **plugável** (`REGIME_MA` em `engine.py`). Cinco opções, todas medidas em [RESULTADOS.md § 3](RESULTADOS.md):

| `REGIME_MA` | direção vem de | parâmetros |
|---|---|---|
| **`ema3`** (padrão) | empilhamento das EMAs 21/42/72 | `LEQUE_MIN`, `TOL_TOQUE` |
| `kama` | inclinação da KAMA(13) | `MA_PER`, `INCL_MIN` |
| `hma` | inclinação da Hull(13) | idem |
| `t3` | inclinação da T3 Tillson(13, v=0,7) | idem |
| `jma` | inclinação de uma **aproximação** do estilo Jurik(21) | idem |

Com **média única**, a direção passa a ser o sinal da inclinação nas últimas `MA_SLOPE` barras, normalizada pelo range médio; "tendência" é `|inclinação| ≥ INCL_MIN`, consolidação é `< INCL_CONSOL`, e o toque é encostar naquela única linha. Os setups não mudam — só a definição de regime.

> **A `jma` não é o JMA.** O algoritmo da Jurik Research é proprietário e não publicado; o que está implementado é uma aproximação pública do estilo (adaptativa com correção de fase). Está aí porque você pediu, e rotulada assim para não virar uma afirmação falsa sobre um indicador comercial.

**Resultado: o padrão `ema3` continua sendo o melhor — com stop 100.** Essa é a única
configuração em que o empilhamento ganha nas **duas** bases. Com stop 150 a KAMA passa
à frente no WINFUT (t +3,25 contra +3,14), embora fique bem atrás no WINV26 (+1,78
contra +2,68). O empilhamento exige concordância entre três escalas de tempo, e a
inclinação de uma linha só não carrega isso.

> Os números desta seção mudaram quando a regra da barra seguinte entrou. Eles saem
> todos de [RESULTADOS.md § 4](RESULTADOS.md), que é gerado — se divergirem, o gerado
> é que vale.

### O padrão, em detalhe

EMAs de `Close`: **21 / 42 / 72**.

Todas as distâncias são normalizadas pelo **range médio das últimas 20 barras** (`mrng`), então a unidade é "barras de range" e os cortes valem em qualquer regime de volatilidade.

```
leque      = (EMA21 − EMA72) / mrng          assinado: + = empilhado p/ cima
alinhado   = +1 se EMA21>EMA42>EMA72 | −1 se EMA21<EMA42<EMA72 | 0
ext        = (Close − EMA21) / mrng          afastamento da rápida, assinado
extCacho   = (Close − média das três) / mrng
toca       = a barra encosta em alguma das três médias, com tolerância 1,0 × mrng
```

| regime | definição | frequência medida |
|---|---|---|
| **tendência** | `alinhado ≠ 0` **e** `\|leque\| ≥ 0,30` | 81% / 80% das barras |
| **consolidação** | `\|leque\| < 0,35` | 14% / 16% |
| nem um nem outro | o resto | 5% / 4% |

---

## 4. Os três setups

### A — Tendência (pullback na média) · **prioritário**

```
regime = tendência
a barra toca uma das três médias (tolerância 1,0 × mrng)
gatilho dispara A FAVOR do empilhamento   (sinal == alinhado)
```

O preço volta para as médias, alguém agride contra a tendência nesse ponto e falha. É o setup pedido como prioridade, e é o que mede melhor — nos dois arquivos, com folga.

### B — Reversão rápida no afastamento

```
regime ≠ consolidação
|ext| ≥ 1,00        (preço a um range médio ou mais da EMA21)
gatilho dispara CONTRA o afastamento
```

> **O filtro de "movimento rápido" existe mas é inerte** (`VEL_MIN_B = 0`). Exigir percentil de velocidade alto não muda nada, porque o gatilho já exige índice ≥ 0,80 e o índice já contém o eixo E3 — a barra do sinal **já é** rápida por construção. Testado em 0,0 / 0,4 / 0,6 / 0,8: resultado praticamente idêntico. O parâmetro fica no código para quem quiser apertar, mas não é o que faz o setup funcionar.

### C — Reversão em consolidação · **desligado por padrão**

```
regime = consolidação
|extCacho| ≥ 0,80
gatilho dispara CONTRA o afastamento
```

**Mede negativo nos dois arquivos, em toda configuração testada.** Ver [RESULTADOS.md § 4](RESULTADOS.md). Fica implementado e acessível (`SETUPS_ATIVOS = ('A','B','C')`) para quem quiser reexaminar com mais dados, mas está fora da carteira padrão.

### Prioridade

`A > B > C`. Quando mais de um setup marca a mesma barra, vale o primeiro — conforme pedido, tendência tem precedência.

---

## 4.1. A restrição do leque — variante, desligada por padrão

`FILTRO_LEQUE` em `engine.py`. **Só vale o gatilho que toca o leque ou fica atrás dele.**

O gatilho de esforço não olha *onde* o preço está — ele só mede que alguém agrediu e falhou. Esta restrição diz onde isso conta.

O leque **aponta** para um lado: para cima quando a EMA21 está acima da EMA72, para baixo no contrário. Daí saem três posições, todas normalizadas pelo mesmo `mrng`:

```
lado    = sinal de (EMA21 − EMA72)          para onde o leque aponta
topo    = maior das três médias
fundo   = menor das três
toca    = a barra encosta em alguma das três, tolerância TOL_TOQUE × mrng
atrás   = lado > 0 e High < fundo    |    lado < 0 e Low > topo
na frente = lado > 0 e Low > topo    |    lado < 0 e High < fundo
```

`atrás` e `na frente` são **sem tolerância** — a barra inteira do lado de lá da média extrema. Quem cai dentro da faixa de tolerância já é `toca`. A variante aceita `toca OU atrás`, e descarta o resto.

Com média única (`REGIME_MA` ≠ `ema3`) a definição degenera para uma linha só, e `lado` passa a ser o sinal da inclinação.

**O que ela faz, medido:**

- **O setup A não muda.** Ele já exige o toque, então já estava inteiro dentro da restrição — sai idêntico nas quatro células (duas bases × dois stops).
- **O setup B é reescrito.** Ele é por construção um setup de *afastamento*, e a maior parte dos afastamentos acontece à frente do leque. Sobram um terço a um quarto dos trades — os que se afastaram para **trás**, ou que ainda encostam em alguma das três.
- Números completos em [RESULTADOS.md § 6](RESULTADOS.md), com a distribuição das posições, as cinco médias de regime e o veredito calculado.

**Por que fica desligada.** Não é uma peneira nova de qualidade: é uma troca de carteira. O EV sobe nas quatro células e o drawdown não piora em nenhuma, mas o `t` cai onde a amostra encolhe — e com dois arquivos que se sobrepõem na maior parte da janela, promovê-la a padrão seria escolher a curva mais bonita de uma amostra pequena. Ela está medida, implementada e acessível; o que falta para decidir é mais pregão.

---

## 5. Execução e gestão

### Entrada — **a regra da barra seguinte**

**Ordem limitada no meio do candle do sinal**, `(High+Low)/2`, **válida por UMA barra**. Ou ela preenche na barra imediatamente seguinte à do gatilho, ou a operação é **abortada**. Não há terceira barra: o sinal morre.

```
barra t     o gatilho dispara; a ordem é enviada
barra t+1   ou preenche AQUI, ou o trade é cancelado
barra t+2   não existe
```

`MAX_BARRAS_FILL = 1` em `engine.py`. `99999` reproduz o comportamento anterior (limitada válida até o fim do pregão), mantido só para medir a diferença.

**O que a regra custa** — carteira só A, stop 150, medido nas duas bases:

| base | limitada livre | 1 barra |
|---|---|---|
| WINV26 | 32 · +60,9 · t +3,01 · PF 2,62 | 30 · +56,7 · t +2,68 · PF 2,42 |
| WINFUT | 79 · +40,5 · t +2,85 · PF 1,89 | 73 · +45,9 · t +3,14 · PF 2,06 |

Melhora o WINFUT, piora o WINV26, pouco dos dois lados. O motivo de ser barata: **91% dos preenchimentos já aconteciam na barra seguinte**, então a regra corta só a cauda — os sinais que o preço demorou a revisitar, que são os piores. A justificativa dela é operacional, não estatística: não deixa ordem esquecida no livro nem trade sendo negociado com dez minutos de atraso.

Cerca de **um sinal em dez é abortado**. Isso é o comportamento correto, não uma falha de execução.

Alternativa disponível: `ENTRADA = 'fecha'` (a mercado no fechamento da barra do sinal). Ela **nunca aborta**, e por isso passou a medir melhor `t` nas duas bases desde que a regra entrou — ver [RESULTADOS.md § 10](RESULTADOS.md). São carteiras diferentes, não uma troca óbvia.

### Gestão

```
stop inicial      150 pontos (padrao) ou 100 (variante medida)
parcial           50% da posição na MESMA DISTÂNCIA DO STOP (+150 com stop 150)
                  → o stop do restante vai para a MÉDIA DA OPERAÇÃO: o preço em que
                    o já realizado cancela a perda do resto. Com meia posição e a
                    parcial na distância do stop, esse preço É o stop inicial —
                    o stop NÃO ANDA, e o desfecho "zero a zero" é zero de verdade.
                  → o stop nunca se AFASTA: se a média cair mais longe que o stop
                    inicial, vale o stop inicial
alvo do restante  300 pontos
saída forçada     fechamento da última barra do pregão
```

Resultado por trade, em pontos, para 1 unidade de posição:

| desfecho | P&L |
|---|---|
| stop antes da parcial | **−150** |
| parcial e depois o stop | **+75 − 75 = 0** |
| parcial e depois alvo | **+75 + 150 = +225** |
| fim de pregão | parcial (se houve) + marcação a mercado do restante |

### Regras da simulação (o que evita enganar a si mesmo)

1. **A gestão começa sempre na barra SEGUINTE à da entrada.** Nem a barra do sinal (cujo High/Low ocorreu *antes* do fechamento) nem a barra do preenchimento (cujo High/Low em parte ocorreu *antes* do toque na limitada) são usadas para stop ou alvo. Sem isso o backtest lê preço que ainda não aconteceu.
2. **Quando stop e alvo cabem na mesma barra, assume-se o STOP.** Com barra de 10.000 ticks não dá para saber a ordem intrabarra; a hipótese é a pessimista.
3. **Uma posição por vez** (`carteira=True`). Sinal que chega com posição aberta é ignorado. O modo `carteira=False` mede cada sinal isolado e serve só para comparar setups entre si.
4. **Nada de custo por padrão** (`CUSTO_PTS = 0`). A sensibilidade a custo está medida em [RESULTADOS.md § 10](RESULTADOS.md) — e importa.
5. **A saída por fim de pregão é a última barra DAQUELE pregão** (`[B1]` no código). Vale a pena registrar porque a primeira versão errava aqui: o laço quebrava na primeira barra do pregão *seguinte* e marcava a saída no fechamento dela, embolsando o gap da abertura. Afetava 1 trade em 200 no WINFUT, mas valia 388 pontos — 8% do resultado total. Corrigido.

---

## 6. Parâmetros

Todos no topo de `engine.py`.

| grupo | parâmetro | valor | origem |
|---|---|---|---|
| gestão | `STOP` / `PARCIAL_EM` / `ALVO` | 150 / 100 / 300 | **pedido pelo Carlos**; stop 100 medido lado a lado — com o E2 novo o de 150 passou a medir melhor, ver § 6 |
| execução | `MAX_BARRAS_FILL` | 1 | **pedido pelo Carlos** — a regra da barra seguinte; custo medido em § 5 |
| | `FRAC_PARCIAL` | 0,50 | pedido |
| gatilho | `NIVEL_MIN` | 0,80 | medido (platô de 0,75 a 0,85) |
| | `CORTE_POSICAO` | 50 | do indicador original |
| | `CORPO_MAX` | 50 | medido — obrigatório com limitada |
| gatilho | `METRICA_E2` | 2 | medido — a fórmula do eixo E2; 0 é a antiga |
| | `DESCARTA_E2` | True | medido, e remedido com a fórmula nova |
| | `FILTRO_LEQUE` | False | **variante** — só gatilho que toca ou fica atrás do leque; medida em § 4.1 |
| | `PERIODO_REF` | 20 | medido (melhor nos dois) |
| regime | `REGIME_MA` | `ema3` | medido contra kama / hma / t3 / jma |
| médias | `EMA_R/M/L` | 21 / 42 / 72 | herdado do repositório |
| | `MA_PER` / `INCL_MIN` | por família | varridos, ver `PARAMS_MA` |
| | `MA_SLOPE` | 5 | barras do lookback da inclinação |
| | `PERIODO_RANGE` | 20 | herdado |
| regime | `LEQUE_MIN` | 0,30 | varrido: 0,0 / 0,15 / 0,30 / 0,45 |
| | `TOL_TOQUE` | 1,00 | varrido: 0,5 a "sem exigir toque" |
| | `CONSOL_MAX` | 0,35 | varrido |
| | `AFAST_MIN_B` | 1,00 | varrido: 0,6 a 1,2 |
| | `VEL_MIN_B` | 0,00 | **inerte** — ver § 4 |

---

## 7. O que esta especificação NÃO cobre

- **Horário.** Nenhum filtro de abertura, fechamento ou leilão. Abertura e fechamento têm dinâmica própria e certamente contaminam os números.
- **Rolagem e vencimento.** Sem tratamento especial.
- **Tamanho de posição.** Tudo é 1 unidade; não há dimensionamento por risco nem por volatilidade.
- **Custos e slippage.** Zero por padrão. A ordem limitada é assumida preenchida a preço exato quando tocada, o que é otimista — na limitada há fila.
- **Outros ativos e outros tamanhos de barra.** Calibrado só em WIN de 10.000 ticks.
