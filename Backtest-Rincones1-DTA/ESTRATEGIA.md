# Estratégia — Rincones1-DTA

Especificação formal do operacional. É o **contrato que `engine.py` implementa**:
se uma regra está aqui, ela está no código; se mudou no código, muda aqui.
Números de desempenho **não** moram neste arquivo — eles estão em
[RESULTADOS.md](RESULTADOS.md) e em [relatorio.html](relatorio.html), que são
gerados. Aqui só ficam as regras e o porquê delas.

---

## 1. O universo

| | |
|---|---|
| Ativo | WIN (mini índice, B3) |
| Gráfico | candle de **10.000 ticks** |
| Bases | `WINV26` (contrato) e `WINFUT` (contínuo), exportadas do Profit |
| Tick | 5 pontos · R$ 0,20 por ponto por contrato |

A barra de tick tem **número de negócios constante**. O que varia de barra
para barra é o volume, o percurso do preço e o tempo — e é exatamente sobre
esses três eixos que o gatilho é construído.

---

## 2. O gatilho — `Ticks_Esforco_Hist_v2.ntsl`

O sinal vem do indicador
`ProfitChart/Indicadores/Grafico-Ticks/Ticks_Esforco_Hist_v2.ntsl`,
reimplementado em `engine.indicador()` com as **configurações padrão dele**:

| entrada do .ntsl | valor | o que é |
|---|---|---|
| `UsarVolume` | ligado | **[E1]** agressão total (compra + venda) |
| `UsarDeslocamento` | ligado | **[E2]** vaivém |
| `MetricaDesloc` | 2 | `(|delta|/esforço) × (1 − |C−O|/percurso)` |
| `UsarTempo` | ligado | **[E3]** velocidade de formação da barra |
| `PeriodoRef` | 20 | janela do percentil, em barras válidas |
| `TickSize` | 5 | WIN |
| pesos | 1 / 1 / 1 | os três eixos entram com o mesmo peso |

Cada eixo vira **percentil dentro das 20 barras válidas anteriores**; o índice
é a média dos três, de 0 a 1. Barra válida é agressão total > 0.

### 2.1 A seta

O indicador desenha a seta **contra quem agrediu**, e as três condições são
as do `.ntsl`:

```
índice        >= NIVEL_MIN
corpo/range   <= 50%                       (porcCorpoWick)
posição do meio do corpo:
    delta comprador  ->  meio do corpo na metade INFERIOR  -> sinal de VENDA
    delta vendedor   ->  meio do corpo na metade SUPERIOR  -> sinal de COMPRA
```

**A leitura econômica.** O índice alto diz que alguém gastou muito — volume
grande, agressão de um lado só, barra rápida — e **não** levou o preço. Isso é
absorção, e absorção se desfaz. O sinal é de **falha**, não de continuação.

### 2.2 O que não é padrão do indicador

Duas coisas deste projeto **não** vêm do `.ntsl`, e por isso são parâmetros
medidos, não verdades herdadas:

- **`NIVEL_MIN`.** O indicador colore a partir de 0,55 e chama 0,60 de extremo;
  isso é escala de cor, não regra de entrada. O nível de entrada foi varrido de
  0,55 a 0,90 (seção 05 do relatório) e o adotado saiu daí.
- **`DESCARTA_E2`.** Filtro herdado do Backtest-Rincones1 que joga fora a barra
  em que [E2] é o maior dos três eixos. **Desligado** por padrão aqui, porque
  não é parte do indicador. Medido na seção 09 do relatório.

---

## 3. O contexto — três peças

Todas as distâncias saem **em ATR**, então os cortes valem igual em pregão
parado e em pregão violento.

```
EMA 21     tendência, e linha do meio do canal
Hull 50    força / intensidade do movimento
ATR 20     unidade de todas as distâncias
Keltner    EMA 21 ± 2 ATR  (banda interna)  e  ± 3 ATR  (banda externa)
```

Grandezas derivadas, todas em `engine.contexto()`:

| símbolo | definição | o que mede |
|---|---|---|
| `pos` | `(close − EMA21) / ATR` | esticamento, com sinal |
| `zona` | 0 dentro, 1 entre 2 e 3 ATR, 2 além de 3 | em que faixa do canal a barra fechou |
| `inc_ema` | `(EMA21 − EMA21[5]) / ATR` | inclinação da tendência |
| `inc_hma` | `(Hull50 − Hull50[3]) / ATR` | inclinação da força |
| `dist_hma` | `(close − Hull50) / ATR` | de que lado da Hull o preço fechou |
| `hma_plana` | `\|inc_hma\| < 0,05` | **o veto**: movimento sem intensidade |

E as duas grandezas **assinadas pelo lado do trade**, que são as que os setups
usam — `sig` é +1 na compra e −1 na venda:

```
dh = sig × dist_hma      dh < 0  =  entrar do lado OPOSTO ao da Hull
de = sig × pos           de < 0  =  entrar contra o esticamento atual
```

---

## 4. Os setups

Prioridade `D → T → K → KB`: quando mais de um marca a mesma barra, o
primeiro da lista fica com ela. **Ativos: D e T.**

### 4.1 D — descolamento da Hull *(principal)*

```
sinal do gatilho existe
dh  <= 0          o close está do lado oposto ao da Hull
Hull NÃO plana    |inc_hma| >= 0,05
zona == 0         o preço está dentro do canal de 2 ATR
de  >= −1,5       o mergulho a partir da EMA 21 é de no máximo 1,5 ATR
```

**Por que assim, e não ao contrário.** A hipótese de partida era a leitura
clássica — comprar com a Hull subindo e o preço acima dela. Medida nas duas
bases, em todos os níveis do gatilho e nos dois stops, ela mede **negativo ou
neutro**; o lado oposto mede positivo em todas as células. Faz sentido com o
que o gatilho é: se ele marca uma agressão que falhou, entrar "a favor do
movimento" é entrar do lado de quem acabou de falhar. A Hull não diz a
direção do trade — ela diz **se há movimento** (inclinação) e **onde o preço
está** em relação a ele (lado).

O veto da Hull plana é a condição mais forte do projeto: é o pior balde
medido nos dois arquivos, com folga.

### 4.2 T — tendência com força *(secundário)*

```
sinal do gatilho existe
dh  > 0                   close do lado da Hull
sig × inc_hma >= 0,05     Hull apontando para o lado do trade
sig × inc_ema >= 0,05     EMA 21 no mesmo sentido
de  < 0,5                 o preço ainda NÃO esticou a favor
```

É a leitura clássica, mas **restrita ao pullback**: só vale quando o preço
ainda não correu a favor. Dá poucos trades e mede positivo nas duas bases.
Ele fica ligado porque acrescenta ao conjunto, não porque é forte sozinho.

### 4.3 K — rejeição da banda *(desligado)*

```
o pavio da barra FURA a banda de 2 ATR do lado contrário ao trade
o candle FECHA de volta para dentro do canal  (zona == 0)
de < 0, Hull não plana
```

É o único uso do canal que mede positivo nas duas bases. Mesmo assim fica
**fora**: entrando na carteira ele derruba o EV, porque só existe uma posição
por vez e ele ocupa a vaga de um trade melhor.

### 4.4 KB — banda clássica *(desligado)*

```
zona >= 1  (o preço está na faixa de 2 a 3 ATR ou além)
de < 0     entrada contra o esticamento
```

O uso de manual do canal de Keltner. Mede **negativo no WINFUT** em toda
configuração testada. Fica no código para que a medição continue visível a
cada rodada, não para ser operado.

---

## 5. A execução

**Entrada.** Ordem **limitada no meio do candle do gatilho**, `(H+L)/2`,
válida por **uma barra**. Ou preenche na barra seguinte, ou a operação é
abortada (`MAX_BARRAS_FILL = 1`). Cerca de um sinal em cinco morre assim, e
todos os números do projeto já estão sob essa regra.

**Uma posição por vez.** Sinal que chega com posição aberta é ignorado. É o
modo `carteira=True`; o modo `carteira=False` existe só para comparar setups
sem que um roube a vaga do outro.

**Gestão.**

| | |
|---|---|
| Stop inicial | **0,75 × ATR** da barra do sinal, com piso de 50 e teto de 400 pontos |
| Parcial | **50% da posição na mesma distância do stop** |
| Stop do restante | na **média da operação** — que, com meia posição e a parcial nessa distância, é o próprio stop inicial |
| Alvo do restante | **300 pontos** |
| Saída forçada | fechamento do pregão |

O stop **não anda**. Com a parcial saindo na distância do stop, o stop inicial
já é o ponto em que a operação vale zero: o desfecho `zero` é zero de verdade,
não um lucro disfarçado.

**Por que o stop deixou de ser fixo.** O Backtest-Rincones1 usava 150 pontos.
Medido em **R** (EV dividido pelo próprio stop do trade, que é a única forma
de comparar stops de tamanhos diferentes), 150 é largo demais para este
gatilho: o stop curto dimensionado pelo ATR mede melhor nas duas bases, com
metade do rebaixamento. A grade inteira está na seção 07 do relatório.

**Pessimismo do simulador.** Quando stop e alvo cabem na mesma barra, assume-se
o **stop**. A gestão só começa a valer na barra **seguinte** à do
preenchimento — nem a barra do sinal nem a do fill entram, porque parte do
range delas aconteceu antes do preço estar lá.

---

## 6. O que ficou de fora, e por quê

- **Filtro de horário.** Não existe. Abertura e fechamento têm dinâmica
  própria e certamente contaminam os números.
- **Rolagem e vencimento.** Não tratados.
- **Custo.** Os números principais são **brutos**; o efeito de 5, 10 e 20
  pontos por trade está medido na seção 11 do relatório, e o plano operacional
  usa a leitura com 5 pontos.
- **Fila na ordem limitada.** A limitada é dada por preenchida ao primeiro
  toque no preço. É a hipótese mais frágil de todo o backtest.

---

## 7. Os parâmetros, e onde mexer

Tudo mora no topo de `engine.py`. Mexeu, rode os três de novo:

```bash
python rodar.py       # mede tudo -> saida/resumo.json
python relatorio.py   # gera relatorio.html e RESULTADOS.md
python plano.py       # gera PLANO.md e plano.html
```

| parâmetro | padrão | o que muda |
|---|---|---|
| `NIVEL_MIN` | 0,80 | seletividade do gatilho — o parâmetro mais forte |
| `DESCARTA_E2` | desligado | filtro extra de seletividade |
| `EMA_PER` / `HMA_PER` / `ATR_PER` | 21 / 50 / 20 | as três peças do contexto |
| `HMA_PLANA` | 0,05 | onde começa "a Hull tem inclinação" |
| `PROF_MAX` | 1,5 | mergulho máximo aceito no setup D |
| `KELT_INT` / `KELT_EXT` | 2 / 3 | as bandas |
| `STOP_MODO` / `STOP_ATR` | `atr` / 0,75 | tamanho do stop |
| `ALVO_MODO` / `ALVO` | `pontos` / 300 | tamanho do alvo |
| `SETUPS_ATIVOS` | `('D','T')` | quais setups entram na carteira |

A sensibilidade de cada um está na seção 10 do relatório — e ela é a resposta
honesta à pergunta “esses números foram escolhidos a dedo?”.
