# Base 11R (Renko de 50 pontos) a partir dos ticks do MetaTrader 5

Reproduz o gráfico **11R do ProfitChart** a partir dos ticks do MT5 e compara
com a base exportada do ProfitPro (`profitpro-ohlc-11R.csv`).

A geração roda **dentro do terminal, em MQL5** — o `CopyTicksRange` nativo lê o
banco de ticks direto, sem os travamentos que a API Python do MT5 tem no
`WIN$N` (banco único de ~13 GB desde 2019).

## Arquivos

| arquivo | onde | função |
|---|---|---|
| `GerarRenko11R.mq5` | `MQL5\Scripts\Tick Recorder\` | baixa os ticks dia a dia e gera as barras 11R |
| `comparar_11r.py` | esta pasta | compara a base gerada com a do ProfitChart |
| `renko11r.py` | esta pasta | motor Renko em Python — implementação de referência usada para deduzir e validar as regras |
| `Export_OHLC.ntsl` | esta pasta | indicador NTSL que produziu a base de referência |

## Como rodar

1. No MetaTrader, abra um gráfico do **WIN$N**.
2. Navegador → Scripts → **GerarRenko11R** (arraste para o gráfico).
3. Preencha os parâmetros e confirme.

| parâmetro | padrão | o que faz |
|---|---|---|
| `DataInicial` / `DataFinal` | — | período a baixar (inclusive) |
| `_SymbolName` | `""` | vazio = símbolo do gráfico |
| `TamanhoTijolo` | `50` | pontos por tijolo (11R = 50) |
| `ArquivoSaida` | `Renko11R.csv` | gravado em `MQL5\Files` |
| `Recomecar` | `false` | ignora o checkpoint e refaz tudo (a saída antiga vira `.bak`) |
| `SalvarTicksDoDia` | `false` | grava também o CSV bruto de ticks do dia |
| `ApagarTicksDoDia` | `true` | apaga esse CSV bruto assim que o dia é processado |
| `HoraInicio` / `HoraFim` | `8` / `19` | janela varrida em cada dia |
| `TentativasChunk` | `10` | paciência enquanto o MT5 sincroniza um trecho |
| `CapAgressao` | `0` | >0: negócio acima disso não conta como agressão (ver abaixo) |

### Acompanhamento

Painel no canto do gráfico, atualizado **a cada trecho de 1 hora** (não a cada
dia), para nunca parecer travado:

```
Renko 50 pts   WIN$N   ->   Renko11R.csv
Dia 37/252  (14.7%)   2025.09.23
   lendo ticks de 14:00-14:59
   negocios no dia : 1843226
   barras no arquivo: 18754  (+412 no dia)
decorrido 12.4 min    ETA 71.2 min
```

Quando o terminal precisa baixar um trecho, a linha do meio vira
`baixando historico de 14:00-14:59 (tentativa 3/10)` e sai um aviso na aba
Especialistas — é o caso em que a espera é longa e sem isso pareceria travado.

No arquivo `MQL5\Files\Renko11R.csv.log` fica o rastro completo: uma linha ao
**começar** cada dia e outra ao **terminar**, com negócios, barras e tempo.

```
[37/252] 2025.09.23  iniciando...
[37/252] 2025.09.23  1843226 negocios  412 barras  (18754 no total)  8.3s
```

A linha "iniciando" é o que diz onde a execução parou, se o terminal for
fechado no meio de um dia.

**Retomada.** O checkpoint (`Renko11R.csv.estado.txt`) guarda o último dia
gravado, a base/direção do Renko e a barra em formação. Interrompeu — Ctrl+C no
script, queda de luz, terminal fechado — é só rodar de novo com os mesmos
parâmetros: continua exatamente de onde parou.

As barras de um dia só vão para o CSV quando o dia termina inteiro. Se a
execução for interrompida no meio do pregão, ou se algum trecho de ticks não
carregar, o dia é descartado e refeito na próxima rodada — nunca ficam barras
órfãs nem tijolos calculados com ticks faltando.

Para um histórico longo (1 ano ou mais) é só ampliar `DataInicial`. Os ticks são
consumidos direto da memória, hora a hora, então nada se acumula no HD. Ative
`SalvarTicksDoDia` só se quiser conferir o tick bruto de algum dia.

## Conferindo com o ProfitChart

```bash
cd C:\Users\Carlos\Dev\Python\Trigger-ultimate\base-ohlc-ntsl
python comparar_11r.py
python comparar_11r.py --divergencias divergencias.csv
```

Por padrão lê `MQL5\Files\Renko11R.csv` e `profitpro-ohlc-11R.csv`, recorta o
período em comum e reporta acerto de Data, OHLC, Quantity, agressão e duração.

## Saída

Mesmas colunas do export do ProfitChart, mais duas, em ordem cronológica:

```
Data;Abertura;Maxima;Minima;Fechamento;AgressionVolBuy;AgressionVolSell;DuracaoMs;Quantity;Trades;VolIndefinido;Simbolo
```

## Regras do Renko do ProfitChart (engenharia reversa)

Deduzidas das 20.001 barras da base de referência e conferidas contra os ticks.

1. **Tijolo = 50 pontos.** `Fechamento − Abertura` é sempre ±50 e todas as
   aberturas/fechamentos são múltiplos de 50. O rótulo "11R" corresponde a
   11 níveis de preço de 5 pontos (10 intervalos × 5 = 50 pontos).

2. **Grade global, sem reinício diário.** A barra aberta no fim do pregão
   continua acumulando na sessão seguinte — há barras com `BarDurationF` de até
   3.752 minutos, um fim de semana inteiro. O gap de abertura vira vários
   tijolos com o mesmo horário e duração zero.

3. **Limiar estrito.** Sendo `base` o fechamento do último tijolo:

   | direção | sobe se | inverte se |
   |---|---|---|
   | `+1` | preço **>** base + 50 | preço **<** base − 100 → tijolo `[base−50, base−100]` |
   | `−1` | preço **>** base + 100 → tijolo `[base+50, base+100]` | preço **<** base − 50 |

   Encostar exatamente no nível **não** vira o tijolo: 397 barras de baixa têm a
   máxima tocando o limiar de alta sem virar (e 384 no sentido oposto), e
   nenhuma barra da base o ultrapassa.

4. **O tick que dispara o tijolo pertence à barra seguinte**, e é ele quem
   define o horário dela. `Data` é a abertura da barra.

5. **Máxima/mínima travadas no fechamento** do lado do tijolo:
   - alta: `Maxima = Fechamento`, `Minima = min(mínima real, Abertura)`
   - baixa: `Minima = Fechamento`, `Maxima = max(máxima real, Abertura)`

   Vale em 100% das 20.000 barras completas da base.

6. **Quantity soma o volume de todos os negócios**, inclusive os de agressor
   indefinido. Testado incluindo e excluindo esses negócios — só a versão que os
   inclui bate exatamente com o ProfitChart.

## Validação

Contra 13/08/2026, 321 barras:

| campo | resultado |
|---|---|
| `Data` | **100%** idêntico |
| `Abertura` / `Maxima` / `Minima` / `Fechamento` | **100%** idêntico |
| `Quantity` | 98,4% idêntico por barra; **0,06%** de diferença no total do dia |
| `BarDurationF` | **100%** dentro de 0,02 min |
| desequilíbrio de agressão | correlação **0,996**, mesmo sinal em 99,1% |

As 5 barras com `Quantity` diferente vêm de ticks perdidos na coleta em tempo
real do próprio MT5 — aquele dia estava sendo capturado ao vivo. Em dias
baixados do histórico esse ruído não aparece.

## O que dá para usar de cada coluna

Todas as colunas são gravadas. O que muda é o quanto cada uma é comparável com
o ProfitChart:

| coluna | comparável? |
|---|---|
| `Data`, `Abertura`, `Maxima`, `Minima`, `Fechamento` | **idênticas** |
| `Quantity` | **idêntica** (volume real, mesmo número de contratos) |
| `DuracaoMs` | equivalente ao `BarDurationF` (ms em vez de minutos) |
| `AgressionVolBuy` / `AgressionVolSell` | só existem se baixar pelo **contrato**; vazias no `WIN$N`. Ver abaixo |
| `Trades` | **escala diferente** (contagem de ticks, não de negócios) |
| `VolIndefinido` | extra, não existe no ProfitChart; vazia junto com a agressão |

`DuracaoMs` é `(último tick − primeiro tick)` em **milissegundos**, inteiro. O
`BarDurationF` do NTSL é o mesmo número em minutos:
`BarDurationF = trunc(DuracaoMs / 600) / 100`. O `comparar_11r.py` faz essa
conversão sozinho ao comparar. Zero legítimo só nos tijolos intermediários,
quando um mesmo tick fecha vários de uma vez (gap de abertura) — em pregão
normal a mediana fica em torno de 60.000 ms (1 min).

### Agressão: quem tem o lado agressor é o CONTRATO, não o `WIN$N`

O símbolo contínuo **perde o lado agressor** no histórico. Mesmo dia, mesma
hora, exatamente os mesmos 89.776 ticks:

| símbolo | BUY | SELL | ambos |
|---|---|---|---|
| `WIN$N` (contínuo) | **100%** | 0% | 0% |
| `WINV26` (contrato) | 49,9% | 47,7% | 2,3% |

Preço, volume e timestamp em milissegundos são idênticos nos dois — só a flag do
agressor se perde ao montar a série contínua. Não dá para reconstruir pela regra
do tick: no histórico o `bid`/`ask` vem zerado e `COPY_TICKS_INFO` devolve
0 cotações para o WIN$N.

**Então: se você precisa de agressão, baixe pelo contrato** (`_SymbolName =
WINV26`), não pelo `WIN$N`.

O porém: o servidor da Genial **descarta os contratos vencidos**. A lista mudou
no meio deste trabalho — o WINQ26 venceu em 12/08/2026 e sumiu no dia seguinte,
junto com todos os anteriores. Hoje só há WINV26 em diante. Rode
`--listar-contratos` ou olhe a Observação de Mercado para ver o que sobrou.

Na prática:

| objetivo | símbolo | agressão |
|---|---|---|
| histórico longo de OHLC | `WIN$N` | não |
| do contrato vigente em diante, com agressão | `WINV26`, `WINZ26`… | sim |

Quando o dia vem sem lado agressor, o script grava `AgressionVolBuy`,
`AgressionVolSell` e `VolIndefinido` **vazios**, em vez de jogar todo o volume em
compra e fingir um dado que não existe. Sai aviso no log e um resumo no fim
("N de M dias vieram sem lado agressor"). `Quantity` continua correto — o volume
está lá, só não classificado.

### `CapAgressao`: a hipótese do teto por negócio

A ideia de que o ProfitChart não conta como agressão negócios acima de um certo
tamanho **explica o nível, mas não a barra a barra**. Testado nos ticks com
agressor de 13/08 (321 barras, alinhamento exato):

| cap | razão compra ger/PC | erro relativo médio | barras dentro de 5% | corr. desequilíbrio |
|---|---|---|---|---|
| sem cap | 1,316 | 0,307 | 6,2% | **0,986** |
| 60 | 0,969 | 0,123 | 30,5% | 0,980 |
| **65** | **0,998** | 0,121 | 32,1% | 0,981 |
| 68 | 1,013 | 0,120 | 32,4% | 0,981 |
| 100 | 1,170 | 0,203 | 16,3% | 0,982 |

Com cap 65 o total do dia bate quase exato, e o erro médio por barra cai pela
metade. Mas nenhuma barra bate exatamente, e o desequilíbrio — que é o que
melhor sobrevive — fica levemente **pior** com o cap.

A explicação provável: o MT5 agrega vários negócios num mesmo tick (o
ProfitChart conta ~2,2× mais negócios). Um tick de 120 contratos pode ser
4 negócios de 30, todos abaixo do teto; o filtro derruba o tick inteiro. Um teto
por negócio não é aplicável na granularidade agregada do MT5.

Deixei como parâmetro `CapAgressao` (0 = desligado) para você calibrar. Se o que
importa é direção, deixe desligado.

### Agressão em ticks coletados ao vivo: o nível não bate, a direção bate

Vale para os dias capturados em tempo real, não para o histórico baixado.

O MT5 traz ~28% mais volume agredido que o ProfitChart, de cada lado. Não é um
filtro simples: em algumas barras o ProfitChart reporta **mais** agressão que o
MT5, então não se trata de excluir um subconjunto de negócios. Foram testadas e
descartadas as hipóteses de excluir negócios diretos (flags BUY+SELL
simultâneas — apenas 2,8% do volume), lotes pequenos, negócios dentro do spread
e negócios fora da melhor oferta. O que resta é o ProfitChart classificar a
agressão com regra própria, provavelmente separando RLP e negócio direto —
informação que o feed do MT5 não expõe.

Só que o excesso é quase proporcional nos dois lados, então **o que se usa da
agressão sobrevive**. Medido nas 321 barras de 13/08/2026:

| medida | correlação com o ProfitChart | mesmo sinal |
|---|---|---|
| desequilíbrio `(buy−sell)/(buy+sell)` | **0,996** | 99,1% |
| delta `buy − sell` | **0,989** | 99,1% |

O erro absoluto médio no desequilíbrio é de 0,031 (numa escala de −1 a +1).

Ou seja: **não compare o valor absoluto** de `AgressionVolBuy` com o do
ProfitChart, nem reaproveite limiares calibrados lá (um filtro do tipo
"agressão de compra > 5.000" vai disparar mais cedo aqui). Mas desequilíbrio,
delta e delta acumulado podem ser usados normalmente.

### Trades: contagem de ticks, não de negócios

O ProfitChart conta ~2,2× mais negócios, porque o MT5 agrega vários negócios num
mesmo registro de tick. A correlação por barra é **0,996**, então serve bem como
medida relativa de atividade — só não é a contagem de negócios do ProfitChart.
Para "número de negócios" no sentido do ProfitChart, não há como obter do MT5.

O `comparar_11r.py` imprime todas essas métricas a cada rodada, então dá para
reconferir no seu próprio período em vez de confiar nos números acima.

## Sobre o histórico de ticks

* `WIN$N` tem ticks desde **23/08/2019** — mas num banco único de ~13 GB. Pela
  API Python, ler uma data no meio dele trava por muitos minutos; em MQL5, o
  `CopyTicksRange` hora a hora resolve isso, que é o motivo desta abordagem.
* Se algum trecho não carregar, o script insiste `TentativasChunk` vezes, avisa
  no log e para naquele dia, sem gravar nada dele. Rodar de novo retoma dali.
* Os contratos individuais (WINQ26, WINV26…) também respondem, mas o servidor da
  Genial só mantém alguns vencimentos antigos. Para histórico longo, `WIN$N` é o
  caminho — é ele que tem a série completa.

## Outros ativos / periodicidades

O script não tem nada específico de WIN: rode num gráfico do WDO, ou informe o
símbolo em `_SymbolName`, e ajuste `TamanhoTijolo`. Os dígitos de preço saem do
próprio símbolo.
