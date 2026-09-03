# RESULTADOS — backtest da estratégia do leque de EMAs (XAUUSD 521 ticks)

> Gerado por `rodar.py` em 2026-09-02 14:03 a partir de `XAUUSD_521_TK_M1_202605051927_202609021325.csv`.  
> Todos os números deste documento saem de `saida/resumo.json`. Nada aqui é digitado à mão.

---

## 1. Resposta curta

A regra como está escrita em `ESTRATEGIA.md` **perde dinheiro** neste histórico: 1.726 operações, 51,0% de acerto, -24,2 t (-0,24 USD) por operação, -41.700 t (-417,00 USD) no total, fator de lucro 0,84.

A causa não é o gatilho ser ruim de leitura — é que **ele não tem leitura nenhuma**. Medida sem qualquer regra de saída, a excursão do preço depois da entrada é estatisticamente igual à de uma entrada sorteada (§ 4). Sobre um sinal sem direção, o alvo final em 900 ticks com stop de 300 é uma aposta que precisa de 33% de acerto para empatar e entrega 10,3%.

**A única restrição que sobreviveu a uma validação fora da amostra foi o horário** — que é, das três hipóteses do documento original, justamente a que o autor listou por último. Filtrando as horas 5h, 6h, 12h, 13h, 16h, 18h, a mesma regra sai de -24,2 t (-0,24 USD) para +26,5 t (+0,26 USD) por operação (variante V4), e com o filtro de reconquista da EMA21 vai a +39,3 t (+0,39 USD) (V5). Trocando também o alvo de 900 pela saída inteira em +1R, chega a +71,2 t (+0,71 USD) (V7) — a única configuração que continua positiva depois de descontar 40 ticks de custo. É pouco, é frágil, e § 9 e § 10 explicam por quê.

## 2. Os dados

| | |
|---|---|
| Arquivo | `XAUUSD-521T/XAUUSD_521_TK_M1_202605051927_202609021325.csv` |
| Ativo / gráfico | XAUUSD, candles de 521 ticks |
| Barras | 70.010 |
| Período | 2026-05-05 19:27 → 2026-09-02 13:25 |
| Pregões | 87 (805 barras por dia, em média) |
| Faixa de preço | 3.942,19 → 4.773,54 |
| Tick | 0,01 USD |

**Tamanho das barras**, em ticks — é o número que decide se um stop de 300 é largo ou apertado:

| mín | 10% | 25% | mediana | 75% | 90% | 95% | 99% | máx |
|---|---|---|---|---|---|---|---|---|
| 5 | 166 | 210 | **277** | 372 | 492 | 589 | 864 | 6.280 |

A barra mediana anda **277 ticks**. O stop de 300 ticks vale portanto **1,08 barras medianas** — é um stop de pouco mais de uma barra. O alvo final em 900 ticks pede **3,2 barras medianas** de continuação depois da entrada. Guarde esses dois números: eles explicam quase tudo o que vem depois.

Sobre o leque: a EMA21 e a EMA72 ficam separadas por 328 ticks na mediana. As médias estão ordenadas (leque formado, para um lado ou para o outro) em 84,2% das barras; nos 15,8% restantes elas estão "emboladas" e a estratégia não olha.

> **Coluna `<SPREAD>` descartada.** O arquivo traz valores entre 149 e 655.942 nessa coluna, o que não é spread de ouro em ponto nenhum de escala. Ela foi ignorada e o custo entrou como parâmetro explícito (§ 8).

## 3. A regra, traduzida para código

O texto de `ESTRATEGIA.md` descreve o padrão em português. Backtest exige que cada palavra vire uma condição verificável. Foi assim:

| No texto | No código (`engine.py`) |
|---|---|
| "médias em forma de leque" | `EMA21 > EMA42 > EMA72` (alta) ou `EMA21 < EMA42 < EMA72` (baixa), sobre o fechamento |
| "o preço se afasta destas médias" | em alguma das 12 barras anteriores a barra **inteira** ficou além da EMA21, no sentido da tendência |
| "e volta ao leque" | a barra do gatilho toca a EMA21 |
| "sequência de 2 ou 3 candles da mesma cor" | 2 ou 3 candles consecutivos de cor **contrária** à tendência imediatamente antes do gatilho — nem 1, nem 4 |
| "aparece um candle contrário" | a barra do gatilho tem a cor da tendência |
| "ordem no meio do range deste candle" | limitada em `(máxima + mínima) / 2` da barra do gatilho |
| "aguardando a ativação no próximo candle" | preenche se a barra seguinte tocar o preço; senão a ordem é **cancelada** |
| "stop de 300 ticks" | 3,00 USD da entrada = **1R** |
| "saída parcial a 300 ticks (50%)" | metade sai em +1R e o stop do resto vai para o preço de entrada |
| "saída final a 900" | o resto sai em +3R |

Com isso, a operação vencedora completa rende `0,5 × 1R + 0,5 × 3R = 2R` — a relação 2:1 que o documento original menciona. Só existem três desfechos:

| desfecho | resultado | quanto vale |
|---|---|---|
| **stop** — cai 300 ticks antes de subir 300 | −1R | −300 t (−3,00 USD) |
| **breakeven** — pegou a parcial e voltou à entrada | +0,5R | +150 t (+1,50 USD) |
| **alvo** — pegou a parcial e chegou aos 900 | +2R | +600 t (+6,00 USD) |

Daí sai o ponto de equilíbrio da estratégia: chamando `a` a fração de alvos, `b` a de breakevens e `s` a de stops, é preciso `600a + 150b = 300s`. Guarde: **sem alvos, é preciso acertar a parcial em 2 de cada 3 tentativas só para empatar.**

## 4. Antes de qualquer resultado: o sinal tem direção?

Toda estatística de backtest mistura duas coisas — a qualidade do sinal e a aritmética da saída. Para separá-las, mediu-se o que o preço faz depois da entrada **sem regra de saída nenhuma**: a maior excursão a favor (MFE), a maior excursão contra (MAE) e a deriva ao fim de N barras. Depois o mesmo foi medido em dois controles aleatórios.

| horizonte | amostra | MFE mediana | MAE mediana | MFE/MAE | deriva média |
|---|---|---|---|---|---|
| 20 barras | o sinal da estratégia | 559 t | 529 t | **1,057** | +15,7 t |
| 20 barras | mesmas barras, **direção sorteada** | 556 t | 537 t | **1,036** | +20,8 t |
| 20 barras | barra e direção sorteadas | 548 t | 576 t | **0,951** | +7,8 t |
| 40 barras | o sinal da estratégia | 829 t | 761 t | **1,090** | +33,1 t |
| 40 barras | mesmas barras, **direção sorteada** | 813 t | 779 t | **1,043** | -5,2 t |
| 40 barras | barra e direção sorteadas | 787 t | 797 t | **0,987** | +32,9 t |

O sinal produz uma razão MFE/MAE de **1,057** em 20 barras. Sortear a direção nas **mesmas** barras produz **1,036**. A vantagem do sinal sobre a moeda sorteada é de 2,1 centésimos de razão — dentro do ruído de uma amostra de 1.985 entradas.

**Conclusão desta seção: o gatilho escolhe *quando* operar, não *para que lado*.** Todo o resultado das seções seguintes é consequência disso.

## 5. A regra literal (V0)

| | |
|---|---|
| Sinais detectados | 2.538 |
| Ordens que **não** ativaram na barra seguinte | 812 (32,0%) |
| Operações efetivas | **1.726** |
| Operações por pregão | 19,8 |
| Acerto | 51,0% |
| Expectativa por operação | **-24,2 t (-0,24 USD)** |
| Resultado total (1 lote) | **-41.700 t (-417,00 USD)** |
| Fator de lucro | 0,84 |
| Rebaixamento máximo | -46.200 t (-462,00 USD) |
| Barras dentro da operação (média) | 5,4 |
| Dias positivos / negativos | 35 / 50 |

E a distribuição dos desfechos, que é onde a estratégia se decide:

| desfecho | operações | fração | contribuição |
|---|---|---|---|
| alvo (+2R) | 178 | 10,3% | +106.800 t (+1.068,00 USD) |
| breakeven (+0,5R) | 702 | 40,7% | +105.300 t (+1.053,00 USD) |
| stop (−1R) | 846 | 49,0% | -253.800 t (-2.538,00 USD) |

**Só 10,3% das operações chegam aos 900 ticks.** O ponto de equilíbrio exigiria muito mais: com 40,7% de breakevens e 49,0% de stops, seriam necessários 14,3% de alvos, e há 10,3%.

### O que a parcial faz

A parcial em +1R com stop no breakeven é frequentemente vendida como "proteção". Neste histórico ela é o contrário: **transforma quase toda operação vencedora em meio ganho.** De cada 880 operações que chegam a tocar +300 ticks, 702 terminam voltando à entrada e saem valendo +150 em vez de +600. A parcial paga o seguro; o prêmio é caro porque o alvo que ela protege quase nunca chega.

## 6. A busca por uma restrição que salvasse a regra

31 filtros foram testados, incluindo os três que `ESTRATEGIA.md` sugere. Para medir cada um sem a distorção do alvo distante, usou-se uma métrica neutra: **stop 300 / alvo 300, posição inteira**, que responde só a uma pergunta — o preço anda 300 ticks a favor antes de andar 300 contra? Um sinal sem direção acerta 50%. A coluna `z` mede a distância de 50% em desvios-padrão.

| filtro | operações | acerto | z | expectativa |
|---|---|---|---|---|
| só nas horas selecionadas ⟵ horário | 529 | 59,5% | **+4,39** | +57,3 t |
| leque >= 400t | 762 | 53,7% | **+2,03** | +22,0 t |
| range do gatilho >= 350t | 418 | 54,3% | **+1,76** | +25,8 t |
| gatilho fecha além da EMA21 (reconquista) | 817 | 53,0% | **+1,71** | +18,0 t |
| reconquista + corpo 50% + sem furar a EMA72 | 342 | 54,4% | **+1,62** | +26,3 t |
| range do gatilho >= 250t | 970 | 52,6% | **+1,61** | +15,5 t |
| só operações de venda | 992 | 52,5% | **+1,59** | +15,1 t |
| leque >= 300t | 1.032 | 52,0% | **+1,31** | +12,2 t |
| EMA21 avança 30t ou mais em 10 barras | 1.197 | 51,6% | **+1,13** | +9,8 t |
| afastamento prévio >= 100t | 1.513 | 51,4% | **+1,05** | +8,1 t |
| afastamento prévio >= 200t | 1.188 | 51,5% | **+1,04** | +9,1 t |
| corpo do gatilho >= 60% do range | 444 | 52,5% | **+1,04** | +14,9 t |
| regra literal, sem filtro nenhum | 1.793 | 51,2% | **+1,02** | +7,2 t |
| reconquista + inclinação 100t + afastamento 200t | 517 | 52,2% | **+1,01** | +13,3 t |
| pullback de 4 a 6 candles | 753 | 51,8% | **+0,98** | +10,8 t |
| EMA21 avança 150t ou mais em 10 barras | 719 | 51,3% | **+0,71** | +7,9 t |
| pullback de exatamente 2 candles | 1.108 | 51,0% | **+0,66** | +6,0 t |
| corpo do gatilho >= 50% do range | 668 | 51,2% | **+0,62** | +7,2 t |
| EMA21 avança 60t ou mais em 10 barras | 1.070 | 50,9% | **+0,61** | +5,6 t |
| pullback de exatamente 3 candles | 757 | 51,0% | **+0,55** | +5,9 t |
| inclinação 150t + leque 300t + afastamento 300t | 427 | 51,3% | **+0,53** | +7,7 t |
| gatilho toca a EMA21 mas não fura a EMA72 | 1.256 | 50,4% | **+0,28** | +2,4 t |
| range do gatilho <= 350t | 1.411 | 50,3% | **+0,24** | +1,9 t |
| leque >= 200t | 1.341 | 50,3% | **+0,19** | +1,6 t |
| afastamento prévio >= 300t | 843 | 50,3% | **+0,17** | +1,8 t |
| EMA21 avança 100t ou mais em 10 barras | 930 | 50,2% | **+0,13** | +1,3 t |
| leque entre 150t e 600t | 1.112 | 50,1% | **+0,06** | +0,5 t |
| afastamento prévio >= 400t | 563 | 50,1% | **+0,04** | +0,5 t |
| leque <= 300t (médias emboladas) | 781 | 50,1% | **+0,04** | +0,4 t |
| range do gatilho <= 250t | 894 | 49,8% | **-0,13** | -1,3 t |
| só operações de compra | 801 | 49,6% | **-0,25** | -2,6 t |

**Como ler esta tabela.** Testar 31 filtros e ficar com o melhor é a definição de garimpo. Com 31 tentativas independentes sobre dados sem nenhuma vantagem, o maior `z` esperado por puro acaso fica em torno de **2,2**. O maior `z` obtido fora do horário foi **2,03** — ou seja, *exatamente* o que o acaso entrega. Nenhum filtro de forma, de leque, de inclinação, de corpo ou de tamanho de candle passou dessa linha.

Vale registrar dois resultados que **contradizem** as hipóteses do documento original:

- A estratégia supõe que **candles de reversão pequenos** são melhores (por causa do stop fixo). Medido: range ≤ 350 t dá 50,3% de acerto; range ≥ 350 t dá 54,3%. O sinal vai na direção **oposta** à hipótese — ainda que nenhum dos dois seja significativo.
- A estratégia supõe que **médias emboladas** atrapalham. Medido: leque ≥ 400 t dá 53,7% (z +2,03), leque ≤ 300 t dá 50,1%. Aqui a hipótese aponta para o lado certo, mas com força indistinguível de ruído.

## 7. O horário — a única coisa que sobreviveu

O horário foi o único filtro que não se comportou como ruído. Como ele também poderia ser garimpo (são 23 horas para escolher), foi submetido a uma **validação cruzada nos dois sentidos**: escolhe-se o conjunto de horas em metade da amostra, mede-se **na outra metade**, e depois inverte-se.

| seleção feita em | horas escolhidas | testado em | operações | acerto medido | acerto de referência | z |
|---|---|---|---|---|---|---|
| 1ª metade | 4h, 5h, 6h, 10h, 12h, 13h, 16h, 18h, 22h | 2ª metade | 403 | **55,6%** | 50,7% | **+2,24** |
| 2ª metade | 5h, 6h, 7h, 11h, 12h, 13h, 16h, 18h, 21h | 1ª metade | 347 | **56,8%** | 51,7% | **+2,52** |

Os dois sentidos concordam: fora da amostra em que foram escolhidas, essas horas rendem cerca de 5 pontos percentuais de acerto a mais que o conjunto completo. As horas que apareceram **nas duas** seleções independentes são **5h, 6h, 12h, 13h, 16h, 18h**, e são as usadas nas variantes V4, V5 e V6.

Perfil hora a hora da regra literal (métrica neutra 1:1):

| hora | operações | acerto | expectativa | |
|---|---|---|---|---|
| 01h | 44 | 54,5% | +27 t | ████████  |
| 02h | 38 | 50,0% | +0 t | ██████  |
| 03h | 95 | 40,0% | -60 t | ██  |
| 04h | 104 | 48,1% | -12 t | █████  |
| 05h | 74 | 58,1% | +49 t | █████████ ✅ |
| 06h | 71 | 60,6% | +63 t | ██████████ ✅ |
| 07h | 50 | 52,0% | +12 t | ███████  |
| 08h | 56 | 46,4% | -21 t | █████  |
| 09h | 85 | 50,6% | +4 t | ██████  |
| 10h | 84 | 53,6% | +21 t | ███████  |
| 11h | 82 | 52,4% | +15 t | ███████  |
| 12h | 77 | 63,6% | +82 t | ███████████ ✅ |
| 13h | 70 | 58,6% | +51 t | █████████ ✅ |
| 14h | 75 | 46,7% | -20 t | █████  |
| 15h | 88 | 45,5% | -27 t | ████  |
| 16h | 128 | 57,0% | +42 t | █████████ ✅ |
| 17h | 127 | 47,2% | -17 t | █████  |
| 18h | 108 | 61,1% | +67 t | ██████████ ✅ |
| 19h | 88 | 43,2% | -41 t | ███  |
| 20h | 74 | 36,5% | -81 t | █  |
| 21h | 74 | 56,8% | +41 t | █████████  |
| 22h | 67 | 50,7% | +4 t | ██████  |
| 23h | 34 | 38,2% | -71 t | █  |

> **O relógio é o do arquivo**, não necessariamente UTC nem o do seu terminal. Antes de usar, confirme qual fuso a corretora exporta: as horas boas caem sobre a abertura europeia, a sobreposição Londres–Nova York e a tarde americana, que é o que se esperaria — mas confirme.

## 8. As variantes

| variante | sinais | operações | acerto | exp./op. | total | FL | rebaixamento |
|---|---|---|---|---|---|---|---|
| **V0** · regra literal | 2.538 | 1.726 | 51,0% | -24,2 | -41.700 | 0,84 | -46.200 |
| **V1** · leque aberto | 1.126 | 742 | 53,2% | -13,7 | -10.200 | 0,90 | -14.100 |
| **V2** · teto de range no gatilho | 1.820 | 1.356 | 50,1% | -26,9 | -36.450 | 0,82 | -40.350 |
| **V3** · gatilho com reconquista | 1.324 | 792 | 52,7% | -19,3 | -15.300 | 0,86 | -17.400 |
| **V4** · só nas horas boas | 744 | 510 | 59,6% | +26,5 | +13.500 | 1,22 | -3.000 |
| **V5** · recomendada (horário + reconquista) | 399 | 248 | 61,3% | +39,3 | +9.750 | 1,34 | -2.550 |
| **V6** · 1:1, sem runner | 771 | 529 | 59,5% | +57,3 | +30.300 | 1,47 | -2.400 |
| **V7** · a que mediu melhor (V5 sem runner) | 411 | 257 | 61,9% | +71,2 | +18.300 | 1,62 | -2.400 |
| **V8** · controle: lado invertido | 2.360 | 2.305 | 49,4% | -32,7 | -75.450 | 0,78 | -75.600 |

**V0 · regra literal** — A regra exatamente como está escrita em ESTRATEGIA.md: leque de EMAs 21/42/72 ordenado, afastamento e volta ao leque, pullback de 2 ou 3 candles da mesma cor, candle contrário como gatilho, ordem limitada no meio do range válida por uma barra, stop de 300 ticks, parcial de 50% em 300 com stop no breakeven, saída final em 900.

**V1 · leque aberto** — Acrescenta a restrição que a própria estratégia sugere: só operar quando as médias NÃO estão emboladas. "Embolado" vira um número — a distância entre a EMA21 e a EMA72 tem de ser de pelo menos 400 ticks (4 dólares) na barra do gatilho.

**V2 · teto de range no gatilho** — Acrescenta a segunda restrição sugerida: o candle de reversão não pode ser grande demais para um stop fixo de 300 ticks. Teto de 350 ticks de range, pouco acima da mediana do ativo (277).

**V3 · gatilho com reconquista** — Exige que o candle de gatilho não apenas toque o leque, mas FECHE de volta além da EMA21, no sentido da tendência. É a versão mais exigente de "aparece um candle contrário no leque".

**V4 · só nas horas boas** — Aplica a terceira sugestão da estratégia: segregação por horário. As horas foram escolhidas por validação cruzada — selecionadas em uma metade da amostra e testadas na outra, nos dois sentidos.

**V5 · recomendada (horário + reconquista)** — A combinação dos dois filtros que mediram melhor — horário e reconquista da EMA21 no fechamento do gatilho — mantendo a gestão original de parcial mais runner até 900.

**V6 · 1:1, sem runner** — Mesma entrada da V4, gestão diferente: a posição inteira sai em 300 ticks, sem parcial e sem runner. Serve de medida limpa da DIREÇÃO do sinal, sem a distorção do alvo distante.

**V7 · a que mediu melhor (V5 sem runner)** — A entrada da V5 com a gestão da V6: horário, reconquista da EMA21, e a posição inteira saindo em +300 ticks. Foi a configuração de melhor expectativa e a única que continua positiva com 40 ticks de custo. É a que o PLANO.md usa como plano principal.

**V8 · controle: lado invertido** — Controle estatístico. Mesma detecção de gatilho, mas operando o lado OPOSTO. Se a estratégia tivesse leitura de direção, esta variante teria de ser o espelho negativo da V0.

### Sensibilidade

Três incertezas foram medidas em vez de assumidas.

**(a) Ambiguidade dentro da barra.** Quando a mesma barra toca o alvo e o stop, o OHLC não diz qual veio primeiro. Todos os números publicados usam a hipótese **pessimista** (stop primeiro). A coluna otimista mostra o outro extremo — o resultado verdadeiro está entre os dois.

**(b) Custo.** Spread mais comissão, ida e volta, em ticks.

**(c) Estabilidade no tempo.** A amostra partida ao meio.

| variante | pessimista | otimista | custo 10 t | custo 20 t | custo 40 t | 1ª metade | 2ª metade |
|---|---|---|---|---|---|---|---|
| V0 · regra literal | -24,2 | -20,8 | -34,2 | -44,2 | -64,2 | -25,1 | -23,2 |
| V1 · leque aberto | -13,7 | -9,5 | -23,7 | -33,7 | -53,7 | -18,6 | -8,2 |
| V2 · teto de range no gatilho | -26,9 | -26,2 | -36,9 | -46,9 | -66,9 | -37,2 | -18,1 |
| V3 · gatilho com reconquista | -19,3 | -17,0 | -29,3 | -39,3 | -59,3 | -19,3 | -19,3 |
| V4 · só nas horas boas | +26,5 | +27,4 | +16,5 | +6,5 | -13,5 | +23,8 | +29,0 |
| V5 · recomendada (horário + reconquista) | +39,3 | +39,3 | +29,3 | +19,3 | -0,7 | +48,6 | +31,8 |
| V6 · 1:1, sem runner | +57,3 | +57,3 | +47,3 | +37,3 | +17,3 | +59,1 | +55,6 |
| V7 · a que mediu melhor (V5 sem runner) | +71,2 | +71,2 | +61,2 | +51,2 | +31,2 | +80,9 | +63,4 |
| V8 · controle: lado invertido | -32,7 | -30,0 | -42,7 | -52,7 | -72,7 | -40,2 | -24,8 |

_Valores em ticks por operação._

Três leituras importam aqui:

1. **A V0 perde nas duas metades** (-25,1 e -23,2 ticks) e perde nas duas hipóteses de ambiguidade. O prejuízo é estrutural, não é azar de um trecho.
2. **O custo come a variante recomendada.** A V5 rende +39,3 ticks sem custo e -0,7 com 40 ticks de custo. Quarenta ticks são 0,40 USD de spread mais comissão — nada de exótico em ouro. A margem inteira da estratégia cabe dentro do spread.
3. **O controle invertido (V7) não é o espelho da V0.** As duas perdem (-24,2 e -32,7 ticks). Se houvesse leitura de direção, inverter o lado teria de produzir o simétrico. Não produz — porque não há o que inverter. (A V7 não é um espelho perfeito: ao trocar o lado, a ordem limitada no meio do range passa a ser um preço *pior* que o fechamento e enche em 97,7% dos casos, contra 68,0% da V0. Ainda assim o sentido da conclusão não muda.)

## 9. Restrições recomendadas

Em ordem de quanto o histórico as sustenta.

**1. Trocar o alvo final de 900 por uma saída mais próxima — ou por nada.**  
É a mudança de maior efeito e a mais bem sustentada, porque não depende de nenhuma descoberta estatística: depende só do tamanho das barras. Pedir 900 ticks (3,2 barras medianas) de continuação num sinal sem direção é pagar 49,0% de stops para colher 10,3% de alvos. A V6 (posição inteira em +1R) rende +57,3 t (+0,57 USD) por operação contra +26,5 t (+0,26 USD) da V4 com a mesma entrada.

**2. Operar só nas horas 5h, 6h, 12h, 13h, 16h, 18h.**  
É a única restrição validada fora da amostra, nos dois sentidos (§ 7). Também é a que mais reduz o número de operações: de 1.726 para 510, ou de 19,8 para 5,9 por pregão.

**3. Exigir que o gatilho FECHE além da EMA21.**  
Foi o melhor filtro de forma medido (z +1,71), embora sozinho não passe do ruído. Combinado com o horário produz a V5. A justificativa não é estatística — é que ele elimina o caso em que a barra apenas encosta na média e fecha do lado errado, que é ambíguo até de ler no gráfico.

**4. Não impor teto de tamanho ao candle de reversão.**  
A pergunta do documento original era se convinha limitar o range da barra de gatilho. A resposta medida é **não**: a V2 (teto de 350 t) piora a V0, e no corte por tamanho as barras *grandes* medem melhor que as pequenas (§ 6). O raciocínio "stop fixo + barra grande = risco maior" está certo sobre o risco, mas o retorno cresce junto.

**5. Se for operar, dimensione pela hipótese de custo alto.**  
Use 40 ticks de custo, não 0. Nessa hipótese a V5 cai para -0,7 t (-0,01 USD) por operação — praticamente zero. A única configuração que sobra em pé é a **V7** (horário + reconquista + saída inteira em +1R): +71,2 t (+0,71 USD) por operação sem custo, +31,2 t (+0,31 USD) com 40 ticks, fator de lucro 1,62. É ela que o `PLANO.md` adota — e ainda assim com a folga de uma amostra de 257 operações, não de uma certeza.

## 10. Limitações honestas deste backtest

- **87 pregões.** É pouco. Quatro meses de ouro num regime só; a V5 tem apenas 248 operações, o que dá um erro-padrão de expectativa da ordem de 20 ticks por operação.
- **Só existe OHLC.** Dentro da barra, o caminho é desconhecido. Isso foi tratado medindo os dois extremos (§ 8a), não escolhendo um.
- **Sem spread por barra.** A coluna do arquivo é inutilizável; o custo entrou como cenário.
- **Sem slippage no stop.** Ordens de stop em ouro escorregam, e escorregam mais nos momentos em que este backtest as aciona.
- **As horas foram escolhidas olhando estes dados.** A validação cruzada reduz o risco, não o elimina. Só o tempo real, para frente, decide.
- **Uma operação por vez.** Sinais que aparecem com uma posição aberta são descartados, o que é o comportamento real de quem opera, mas reduz a amostra.

## 11. O que fazer com isto

A estratégia descrita em `ESTRATEGIA.md` é um bom **gatilho de atenção** e não é uma vantagem. Ela marca o momento em que uma tendência acabou de absorver um pullback — um momento legítimo para olhar o gráfico. O que os dados não sustentam é a segunda metade da afirmação: que dali o preço siga a favor com frequência suficiente para pagar um alvo de 3R.

O caminho com alguma chance está em `PLANO.md`: horário estreito, gatilho exigente, alvo curto, tamanho pequeno, e um critério de parada escrito antes de começar. Não como uma estratégia validada — como um teste em tempo real, com dinheiro dimensionado para ser o custo do teste.

---

*Reproduzir: `python rodar.py && python resultados_md.py && python relatorio.py && python plano.py`. Operação a operação em `saida/trades_V*.csv`.*
