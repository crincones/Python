# SR-metatrader5

Detector automatico de niveis importantes com saida para o **MetaTrader 5**.

E o mesmo motor do `SR-profitchart3` (Renko -> giros -> clustering -> score),
ligado ao historico de 1 minuto mantido pelo `baixar-ohlc-fx` e com a saida
trocada: em vez de codigo NTSL, um **CSV por simbolo** na pasta `MQL5\Files`,
lido pelo indicador `SR_Levels.mq5`.

```
baixar-ohlc-fx/USDJPY_M1.csv   ->   main.py   ->   MQL5\Files\SR_USDJPY.csv   ->   SR_Levels.mq5
     (MetaTrader 5)                 (Python)            (pasta do terminal)         (grafico)
```

Um nivel e SEMPRE um unico preco com um score de relevancia. Nao existe
classificacao suporte/resistencia e nao existe zona -- o mesmo preco funciona
como suporte ou resistencia dependendo de onde o mercado esta.

---

## 1. Instalacao

```powershell
pip install -r requirements.txt
```

Os caminhos fixos desta maquina ficam no topo do `config.py`:

| constante             | valor                                                        |
|-----------------------|--------------------------------------------------------------|
| `HISTORICO_DIR`       | `C:\Users\Carlos\Dev\Python\baixar-ohlc-fx`                   |
| `MT5_DATA_DIR`        | `...\MetaQuotes\Terminal\Metatrader5FX`                       |
| `MQL5_FILES_DIR`      | `<MT5_DATA_DIR>\MQL5\Files`                                   |
| `MQL5_INDICATORS_DIR` | `<MT5_DATA_DIR>\MQL5\Indicators`                              |

Para descobrir o `MT5_DATA_DIR` de outro terminal: **Arquivo > Abrir pasta de
dados** dentro do MetaTrader.

Instale e compile o indicador uma unica vez:

```powershell
python main.py --instalar        # copia SR_Levels.mq5 para MQL5\Indicators
```

Depois abra o MetaEditor e compile com **F7** (ou, pela linha de comando:
`MetaEditor64.exe /compile:"...\MQL5\Indicators\SR_Levels.mq5"`).

---

## 2. Uso

```powershell
# atualizar o historico primeiro (no projeto baixar-ohlc-fx)
python atualiza-historico.py --symbol USDJPY

# gerar os niveis
python main.py
python main.py --symbol USDJPY --box-ticks 50 --sep 100 --top 25
python main.py --desde 2026-06-01 --vao-max 400 --faixa 4000
python main.py --sem-mt5         # grava so em output/, nao toca na pasta do terminal
```

Em seguida, no MetaTrader: arraste **SR_Levels** para o grafico do simbolo.
O indicador recarrega sozinho a cada 30 s quando o Python regrava o arquivo --
nao e preciso remover e readicionar.

### Distancias em pontos do MT5

`--sep`, `--vao-max`, `--faixa` e `--box-ticks` sao dados em **pontos**
(1 ponto = 1 tick = `10^-digits`), nunca em unidades de preco. No USDJPY
(`digits=3`) 1 ponto = 0.001, ou seja **10 pontos = 1 pip**:

| voce escreve   | no USDJPY significa            |
|----------------|--------------------------------|
| `--box-ticks 50` | caixa de 0.050 (5 pips)      |
| `--sep 100`      | linhas a pelo menos 0.100    |
| `--vao-max 400`  | nenhum vao maior que 0.400   |
| `--faixa 4000`   | +-4.000 em torno do preco    |

Assim os mesmos numeros valem para qualquer par -- so `--ref` fica em preco
(ex.: `--ref 159.30`).

### Parametros principais

| flag              | o que faz                                                              |
|-------------------|------------------------------------------------------------------------|
| `--symbol`        | simbolo do MT5; define o CSV de entrada e o de saida                    |
| `--modo`          | `renko` (padrao) ou `mtf` (multi-timeframe)                             |
| `--box-ticks`     | tamanho da caixa do Renko, em pontos                                    |
| `--sep`           | separacao minima entre linhas (padrao: a propria caixa)                 |
| `--top`           | numero maximo de linhas                                                 |
| `--faixa`         | janela de desenho em torno da referencia; `0` = sem limite               |
| `--vao-max`       | preenche vaos maiores que X, mesmo passando de `--top`                  |
| `--metodo`        | `kde` (padrao), `grade`, `dbscan`, `hierarchical`                       |
| `--min-eventos`   | minimo de eventos para um cluster virar nivel                           |
| `--forca-min`     | reacao minima do giro, em caixas                                        |
| `--desde/--ate`   | recorte do historico                                                    |
| `--walk-forward`  | validacao fora da amostra (mais lento)                                  |
| `--instalar`      | copia o `SR_Levels.mq5` para a pasta Indicators                         |
| `--sem-mt5`       | nao copia o CSV para a pasta Files                                      |

`python main.py --help` lista o resto.

### Exploracao

```powershell
python explore.py --symbol USDJPY --meses 3
```

Imprime o diagnostico passo a passo (ATR por timeframe, eventos por escala,
clusters, comparacao contra precos aleatorios) e grava dois PNG em
`output/explore/`.

---

## 3. O arquivo lido pelo indicador

`MQL5\Files\SR_USDJPY.csv` -- texto ANSI, `;` como separador, `.` como decimal:

```
symbol;price;score;n_events;unique_days;unique_months;span_days;first_event;last_event
USDJPY;159.750;81.0;9;6;2;60.0;2026.06.01 17:00;2026.07.31 16:25
USDJPY;159.650;69.1;7;4;3;64.4;2026.05.28 06:49;2026.07.31 16:28
```

* uma linha por nivel, do preco mais alto para o mais baixo;
* a coluna `symbol` e redundante (ja esta no nome do arquivo) de proposito:
  e ela que o indicador confere contra o `_Symbol` do grafico;
* as datas usam o formato que o `StringToTime()` do MQL5 le direto;
* a gravacao e atomica (`.tmp` + `os.replace`), entao o indicador nunca le um
  arquivo pela metade.

Os metadados da rodada (periodo analisado, caixa, banda, n. de eventos) vao
para `output/SR_USDJPY_meta.json` -- **fora** da pasta do terminal, para nao
poluir a sandbox com arquivo que o indicador nao usa.

---

## 4. O indicador `SR_Levels.mq5`

Desenha uma `OBJ_HLINE` por nivel, todas com a mesma cor, espessura e estilo.

| input               | padrao           | o que faz                                              |
|---------------------|------------------|--------------------------------------------------------|
| `InpPrefixo`        | `SR_`            | prefixo do arquivo: `SR_` + simbolo + `.csv`            |
| `InpArquivo`        | vazio            | forca um arquivo especifico                             |
| `InpSimbolo`        | vazio            | usa outro simbolo para montar o nome (vazio = `_Symbol`)|
| `InpPastaComum`     | falso            | ler de `Common\Files` em vez de `MQL5\Files`            |
| `InpConferirSimbolo`| verdadeiro       | recusa arquivo cuja coluna `symbol` nao bate            |
| `InpRecarregarSeg`  | 30               | recarrega quando o arquivo muda; `0` desliga            |
| `InpScoreMinimo`    | 0                | filtra por score                                        |
| `InpMaxLinhas`      | 0                | mantem so as N de maior score; `0` = todas              |
| `InpCor`            | `clrDodgerBlue`  | cor das linhas                                          |
| `InpEspessura`      | 1                | espessura                                               |
| `InpEstilo`         | `STYLE_DASH`     | estilo                                                  |
| `InpAoFundo`        | verdadeiro       | desenha atras dos candles                               |
| `InpRotulo`         | verdadeiro       | texto `SR 159.350 R99 T17` no fim da linha              |
| `InpSelecion`       | falso            | permite selecionar/arrastar as linhas                   |

Detalhes de comportamento:

* **sufixo do broker** -- se `SR_USDJPY.m.csv` nao existir, o indicador tenta
  `SR_USDJPY.csv`. Cobre os `.m`, `c`, `-ECN` que os brokers de FX acrescentam,
  sem precisar renomear nada;
* **conferencia de simbolo** -- se o arquivo for de outro ativo, nada e
  desenhado e o motivo aparece no *Experts*. Desligue `InpConferirSimbolo`
  para forcar;
* **rotulo** -- o texto so aparece se o grafico estiver com *Mostrar descricoes
  dos objetos* ligado (`Ctrl+O` > Comum). O tooltip funciona sempre;
* **limpeza** -- ao remover o indicador todas as linhas somem (elas tem o
  prefixo `SRL_` e sao apagadas no `OnDeinit`).

---

## 5. Diferencas em relacao ao SR-profitchart3

| | SR-profitchart3 | SR-metatrader5 |
|---|---|---|
| entrada | export manual do WIN | `baixar-ohlc-fx/<SYMBOL>_M1.csv` |
| saida | `niveis.ntsl` (codigo NTSL) | `SR_<SYMBOL>.csv` + indicador MQL5 |
| caixa do Renko | `NR` = `(N-1)` ticks (convencao ProfitChart) | `N` ticks exatos |
| precos | inteiros (WIN) | fracionarios (`digits` do simbolo) |
| distancias na CLI | pontos do WIN | pontos do MT5 (`10^-digits`) |
| dia (`TF_MINUTES`) | 375 min (pregao da B3) | 1440 min (FX roda 24h) |

O resto -- deteccao de giros, clustering, score, selecao, walk-forward -- e
identico.

---

## 6. Estrutura

```
main.py                  ponto de entrada
config.py                parametros + caminhos fixos desta maquina
explore.py               diagnostico passo a passo
pipeline.py              orquestracao das etapas
data/                    carga, validacao, tick, resample, Renko
detection/               giros do Renko, swings, niveis de referencia, reacoes
clustering/              KDE, grade, DBSCAN, hierarquico
scoring/                 score, recencia, confluencia, selecao
validation/              backtest e walk-forward
visualization/           PNG de inspecao
export/mql5.py           gravacao do CSV na pasta Files
mql5/SR_Levels.mq5       indicador
output/                  saidas (niveis.csv, eventos.csv.gz, niveis.png, meta)
```

---

## 7. Limitacao conhecida do historico

O `copy_rates_range` do MT5 recusa periodos longos quando o terminal esta com
*Ferramentas > Opcoes > Graficos > Max. barras no grafico* em um valor baixo --
por isso o `USDJPY_M1.csv` pode comecar poucos meses atras. Quanto mais fundo o
historico, mais confiaveis os niveis (mais dias e meses distintos por nivel).
Ponha **Unlimited** e rode o `atualiza-historico.py --desde 2021-01-01` de novo.
