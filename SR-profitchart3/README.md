# Detector automático de níveis importantes

Implementação do `descritivo.md`: analisa ~5 anos de candles de 1 minuto e
produz uma lista curta de **preços** historicamente relevantes, cada um com um
**score**, e gera o código NTSL para o ProfitChart.

Um nível é sempre **uma linha, um preço**. Não existe classificação
suporte/resistência e não existe zona — a tolerância de agrupamento é interna e
não aparece no resultado.

## Instalação e execução

```bash
pip install -r requirements.txt

python main.py                                   # Renko 50R, CSV padrão da pasta
python main.py --sep 200 --ref 172000            # linhas em torno de 172.000
python main.py --box-ticks 40 --ref 172000       # caixa menor = linhas mais próximas
python main.py --modo mtf --sep 400 --top 15     # análise multi-timeframe
python main.py --ate 2025-12-31 --walk-forward
python main.py --cor 200 0 0 --espessura 2 --estilo 0
python explore.py --meses 12                     # script exploratório (seção 40)
```

Saídas em `output/`:

| arquivo | conteúdo |
| --- | --- |
| `niveis.ntsl` | **saída principal** — `HorizontalLineCustom()` por nível, com cabeçalho documentando a rodada |
| `niveis.csv` | preço, score, estatísticas de suporte e decomposição do score |
| `eventos.csv.gz` | todos os eventos detectados, com cluster e peso (auditoria) |
| `niveis.png` | candles + linhas horizontais + curva de densidade |
| `walk_forward.csv` | resultado da validação fora da amostra (com `--walk-forward`) |

## Entrada

Aceita o export do MetaTrader (`<DATE>\t<TIME>\t<OPEN>…`, que é o formato do
`WIN$N_M1_202108120900_202608111824.csv`) e também CSV genérico
`datetime,open,high,low,close[,volume]`. Volume é opcional em todo o pipeline.

## Modo padrão: um único gráfico Renko

O detector analisa **um só gráfico**: um Renko construído a partir dos candles
de 1 minuto. A especificação foi conferida contra um export 50R do próprio
ProfitChart:

* `50R` no WIN = caixa de **245 pontos** = (50 − 1) ticks de 5 pts;
* a grade é ancorada em **zero** — toda abertura e todo fechamento de tijolo é
  múltiplo exato da caixa (171.500 = 245 × 700). Por isso as linhas geradas
  caem exatamente sobre as linhas que você vê no seu gráfico;
* continuação anda 1 caixa, reversão exige 2;
* cada tijolo guarda a máxima e a mínima reais do trecho que cobre.

Como não há hierarquia de tempos gráficos, o que mede a importância estrutural
de um giro é a sua **profundidade**:

```text
profundidade = min(tijolos antes do giro, tijolos depois do giro)
```

`d1` é ruído de 1 tijolo; `d8` é um giro de 8 ou mais. Tudo o mais (reação,
tolerância, independência) é medido em **caixas**, não em pontos nem em ATR —
a caixa já é a unidade de volatilidade do gráfico.

A análise multi-timeframe original (5m → semanal + níveis diários/semanais/
mensais) continua disponível em `--modo mtf`.

### A caixa define o espaçamento das linhas

Num Renko os níveis só podem cair sobre a grade, então **a distância mínima
entre duas linhas é uma caixa**. Se você quer linhas a cada ~200 pontos, é a
caixa que precisa mudar:

| gráfico | caixa | separação média obtida (20 linhas, ref. 172.000) |
| --- | ---: | ---: |
| 50R | 245 pts | 280 pts |
| 40R | 195 pts | 195 pts |

E há um efeito colateral honesto: quando a separação pedida é ~1 caixa, a
seleção deixa de selecionar — ela pega praticamente todas as linhas da grade na
janela. A escolha só volta a ser exigente quando a separação vale 2 caixas ou
mais (`--sep 490`, `--sep 980`), e é aí que o score faz diferença.

## Como o nível é construído

1. **Normalização** — ordena, remove duplicatas, descarta candles incoerentes,
   infere o **tick size** pelo MDC das diferenças de preço (5 pts no WIN) e
   arredonda tudo à grade do ativo. Nunca `round(price, 2)`.
2. **Volatilidade** — no Renko a unidade é a **caixa**. No modo `mtf` é o ATR
   de Wilder, projetado minuto a minuto **com shift de 1 barra** (sem
   look-ahead). Em nenhum dos dois os limiares são pontos fixos.
3. **Eventos** — os giros do Renko (no modo `mtf`, swings de cada timeframe
   mais os níveis diários/semanais/mensais). Giros no mesmo preço só viram
   eventos distintos depois que o mercado se afasta 2 caixas — um repique
   dentro da mesma região é **um** evento, não vários.
4. **Reação** — direcionalmente neutra: `max(quanto subiu acima, quanto caiu
   abaixo)` em 5/10/20/40 tijolos, dividida pelo deslocamento típico de uma
   caminhada aleatória de mesmo tamanho (`caixa × √h`). Sem essa normalização o
   horizonte longo domina e a métrica não distingue nada: força ~1 significa
   "foi tão longe quanto o acaso levaria".
5. **Clustering** — em preço **linear** no modo Renko (a caixa é fixa em
   pontos) e em **log-preço** no modo `mtf` (tolerância relativa, coerente com
   o ativo saindo de 100k para 200k). Três métodos comparáveis via `--metodo`:
   - `kde` (padrão): densidade gaussiana **ponderada pela importância** dos
     eventos; os máximos locais são os candidatos. Atenção: o filtro de
     proeminência é **global**, então uma zona muito mais densa que as outras
     pode apagar candidatos legítimos em outro patamar de preço;
   - `grade` (só no Renko): cada linha da grade com pelo menos `--min-eventos`
     giros vira um candidato. Sem suavização e sem filtro global — é a leitura
     mais direta do gráfico e a que dá melhor cobertura;
   - `dbscan`: DBSCAN exato em 1-D (O(n log n), sem matriz de distâncias);
   - `hierarchical`: aglomeração de diâmetro limitado (complete-linkage 1-D).
6. **Preço final** — mediana ponderada dos eventos do cluster (também há média,
   mediana, média ponderada e pico de densidade), arredondada ao tick.
7. **Score** — combinação de `touch`, `reaction`, `temporal`, `scale`
   (profundidade do giro no Renko; timeframe no modo `mtf`), `volume`,
   `recency` e `confluence`. Cada fator entra como **percentil** entre
   os candidatos, e a contagem de eventos entra em escala logarítmica: 30
   toques no mesmo pregão não valem 30 vezes mais que um. Persistência
   (dias/meses distintos, span) pesa mais que quantidade bruta.
8. **Seleção** — top N respeitando a separação mínima pedida.

## Parâmetros do usuário (seção 39.1)

| CLI | efeito |
| --- | --- |
| `--sep 400` | separação mínima entre linhas, em pontos (padrão: 1 caixa no Renko) |
| `--ref 172000` | preço de referência que centra as linhas (padrão: último fechamento) |
| `--faixa 6000` | janela de desenho `±X` pontos em torno da referência (padrão: `top × sep / 2`; `0` desliga) |
| `--box-ticks 40` | tamanho da caixa do Renko, na notação do ProfitChart |
| `--vao-max 500` | vão máximo tolerado entre linhas vizinhas; vãos maiores são preenchidos com o melhor candidato disponível, **mesmo passando de `--top`** |
| `--desde` / `--ate` | limites do histórico analisado |
| `--top` / `--min-score` | quantidade e corte de qualidade das linhas |
| `--cor R G B`, `--espessura`, `--estilo` | valores **padrão** dos inputs do NTSL |

No próprio NTSL o usuário ainda pode mudar `CorR/CorG/CorB`, `Espessura`,
`TipoLinha` (0=sólida, 1=tracejada, 2=pontilhada, 3=traço-ponto,
4=traço-ponto-ponto), `TamanhoTexto` e `LocalTexto` sem regerar nada.

> Se a sua versão do ProfitChart não aceitar `RGB()`, troque
> `Cor := RGB( CorR, CorG, CorB );` por `Cor := clBlue;` — o arquivo gerado traz
> essa observação no cabeçalho.

## Buracos na cobertura

Se faltam linhas em alguma faixa, a causa quase nunca é falta de histórico —
o detector já usa todo o arquivo. As três causas reais, em ordem de frequência:

1. **O orçamento de linhas foi gasto em outro lugar.** Sem `--faixa`, as `top_n`
   linhas competem em toda a faixa histórica de preços, e uma consolidação
   antiga (dezenas de giros por linha da grade) ganha das regiões recentes.
   Medido neste histórico: sem janela, 32 das 50 linhas ficaram em 2023 e só 7
   sobraram acima de 175.000. Mexer na `--meia-vida` quase não muda isso (com
   90 dias ainda são 34 linhas em 2023) — quem resolve é `--ref` + `--faixa`.
2. **O candidato existia mas foi filtrado.** `--min-eventos` alto corta linhas
   da grade com poucos giros, e o KDE ainda aplica um corte global de
   proeminência. Use `--metodo grade --min-eventos 3`.
3. **Não há giro nenhum ali.** Numa perna de impulso o Renko imprime tijolos
   seguidos sem reversão: a faixa 153.125 → 156.065 (nov–dez/25) tem 11 linhas
   de grade com 0 ou 1 giro cada. O preço passou uma vez e não voltou. Nesse
   caso não existe nível a detectar, e inventar um seria mentir.

Receita para cobertura contínua em torno de um preço:

```bash
python main.py --ref 176000 --faixa 8000 --sep 245 --top 40                --vao-max 500 --metodo grade --min-eventos 3
# 47 linhas, vão médio 304 pts, maior vão 490 pts (2 caixas), nenhum buraco
```

## Validação (seções 27–29)

`--walk-forward` treina de forma expansiva e mede o ano seguinte, que o
algoritmo nunca viu. Para cada nível fora da amostra são medidos retornos
independentes, reação média/mediana/máxima e minutos até o próximo movimento
significativo.

O grupo de controle são preços **realmente negociados** no período de treino,
dentro da faixa do período de teste — e não preços uniformes na faixa, que
seriam um controle artificialmente fraco (preços pouco visitados quase nunca
são tocados e, quando são, é no extremo de um movimento).

Resultado medido neste histórico do WIN (5 anos), variando a densidade das
linhas no modo Renko 50R:

| separação pedida | níveis/dobra | razão níveis ÷ controle |
| ---: | ---: | ---: |
| 200 pts (~1 caixa) | 11 | 0,95 |
| 490 pts (2 caixas) | 14 | 1,00 |
| 980 pts (4 caixas) | 8 | 1,01 |
| 1.960 pts (8 caixas) | 4 | 0,95 |

O modo `mtf`, medido do mesmo jeito, dá razão média **1,08**.

Leitura honesta: **nenhuma das configurações mostra vantagem estatística
relevante fora da amostra.** Os níveis do Renko reagem praticamente como
qualquer preço que o mercado já negociou por ali, e a correlação entre o score
e a força fora da amostra muda de sinal entre as dobras (−0,40 a +0,12), ou
seja, o score ordena o passado mas ainda não demonstrou ordenar o futuro.

Isso não invalida o uso das linhas como referência visual — é o mesmo que
qualquer S/R desenhado à mão entrega — mas desaconselha tratá-las como sinal
com expectativa positiva sem mais trabalho de calibração. Quem quiser tentar
melhorar: mexer nos pesos de `score_weights` e reavaliar sempre com
`--walk-forward`, nunca pela aparência do gráfico.

## Estrutura

```
config.py           parâmetros (nada hard-coded no meio do código)
pipeline.py         orquestração: dados -> eventos -> clustering -> score
main.py             CLI e geração das saídas
explore.py          script exploratório passo a passo (seção 40)

data/               loader, validação/tick size, resampling/ATR e Renko
detection/          giros do Renko, swings, reações, níveis de referência, KDE
clustering/         DBSCAN 1-D, aglomerativo 1-D e interface comum
scoring/            score, recência, confluência, seleção
validation/         backtest fora da amostra e walk-forward
visualization/      gráfico de inspeção
export/             gerador do código NTSL
models/             `Level` (price, score, evidências) — neutro por construção
```

## Desempenho

690.950 candles de 1 minuto → 21.036 tijolos → 6.495 giros: **~4 s** do CSV ao
NTSL (≈2 s reaproveitando o cache de eventos em `.cache/`). Tudo é vetorizado em NumPy/Pandas; os únicos
laços Python percorrem eventos (dezenas de milhares), não candles. A fase 4 do
descritivo (Numba/Polars) não foi necessária até aqui.

## Limitações conhecidas

- O Renko é construído a partir do OHLC de 1 minuto, sem o caminho percorrido
  dentro da barra; usa-se a convenção de processar a mínima antes da máxima em
  minuto de alta (e o contrário em minuto de baixa). Sobre o mesmo período, o
  resultado bate com o export do ProfitChart (21.036 tijolos aqui contra 20.001
  em ~2 meses a menos de histórico).
- Horizontes de reação contam **tijolos/barras contíguos**: perto do fim do
  pregão a janela avança para o dia seguinte.
- O score é **relativo à rodada** (reescalado para 25–99); serve para ordenar
  candidatos, não como medida absoluta comparável entre execuções diferentes.
- Com separação de ~1 caixa a seleção degenera em "toda linha da grade na
  janela"; o score continua ordenando, mas não está descartando quase nada.
