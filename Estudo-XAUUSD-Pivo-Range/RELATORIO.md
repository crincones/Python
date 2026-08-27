# Relatório — Padrões de Reversão em Range Bars (XAUUSD, range 3.27)

**Conclusão principal: a investigação NÃO encontrou evidência estatística suficiente.**
Nenhum dos dois padrões, nem isolados nem condicionados por agressão, tempo de formação
ou qualquer combinação de features, apresentou vantagem que sobreviva ao teste
out-of-sample e ao custo de transação. A recomendação é **não** implementar um
indicador de score/probabilidade.

Base: `OHLC/XAUUSD_327_N_M1_202511041815_202608212148.csv` — 100.528 barras,
2025-11-04 18:15 a 2026-08-21 21:48.

---

## 0. Validação empírica dos dados (feita antes da análise)

| Verificação | Resultado |
|---|---|
| `Range = HIGH-LOW` constante | **3.27** em 100.380 barras (99,85%) |
| Barras "incompletas" (range < 3.27) | 145 barras (0,14%); mínimo 0.21 |
| Barras com range > 3.27 | **zero** |
| Barra de alta fecha na máxima | 99,85% |
| Barra de baixa fecha na mínima | 99,87% |
| Wick no lado do fechamento | 0,15% (apenas barras anômalas) |
| Continuidade `OPEN[t] == CLOSE[t-1]` | 99,85% |
| Dojis (`CLOSE == OPEN`) | zero |
| `SPREAD` = duração | corr(`SPREAD/1000`, `DT[t]-DT[t-1]`) = **0,99999** |
| Semântica de `DT` | **timestamp de FECHAMENTO** da barra |
| `TICKVOL` como agressão compradora | barras de alta têm `TICKVOL>VOL` em 71,3% dos casos |

Todas as premissas do CLAUDE.md foram confirmadas empiricamente. Dois pontos importantes:

1. **`DT` é o fechamento da barra**, não a abertura. Isso foi determinado pela correlação
   quase perfeita entre `SPREAD` e o delta temporal *anterior*. Features de horário usam
   essa convenção.
2. `corr(TICKVOL, VOL) = 0,992`. As duas séries são quase idênticas em nível; toda a
   informação útil está no **desbalanço** (`TICKVOL - VOL`), não nos níveis.

### Limitação grave da base: buraco de 82 dias

Há um vazio entre **2025-12-31 21:54** e **2026-03-23 22:56** (1.969 horas).
**Janeiro e fevereiro de 2026 estão inteiramente ausentes.** Os demais 30 gaps são
fins de semana normais (~49h). Apenas 39 eventos (0,28%) têm trades atravessando um gap
maior que 6h; excluí-los não altera nenhum resultado (P1: 0,3132 → 0,3122; P2: 0,3110 → 0,3113).

---

## 1. Definição exata dos padrões (como implementados)

Com `t` = barra de reversão, `DIR = sign(CLOSE - OPEN)`, `BodyRatio = |CLOSE-OPEN| / (HIGH-LOW)`:

**Padrão 1 — 2 + reversão fraca**

```
DIR[t-2] == DIR[t-1]  E  DIR[t] == -DIR[t-1]  E  BodyRatio[t] <= 0,50
```

**Padrão 2 — impulso + reversão forte**

```
DIR[t-2] == DIR[t-1]  E  DIR[t] == -DIR[t-1]
E  BodyRatio[t-1] >= 0,70  E  BodyRatio[t] >= 0,70
```

O lado do trade é `DIR[t]` (direção da barra de reversão). Entrada conceitual em `CLOSE[t]`.
`R = HIGH[t] - LOW[t]`. Alvo `C + 3R·lado`, limite adverso `C - 1,3R·lado`.

**Regra conservadora para alvo e stop na mesma barra:** conta-se como **falha (stop)**.
Na prática isso é irrelevante: como as barras são contíguas e têm range 3.27, e a
distância entre alvo e stop é `4,3R = 14,06 USD` (4,3× o tamanho de uma barra), a
ambiguidade é geometricamente quase impossível. Ocorreu em **0 de 14.013 eventos**
(e em 1 de 100.515 no baseline, sobre um gap de preço).

Os dois padrões são **mutuamente exclusivos** por construção (0 sobreposições):
P1 exige `BodyRatio[t] <= 0,50` e P2 exige `BodyRatio[t] >= 0,70`.

---

## 2. Ocorrências e 3. Taxa de sucesso

**Breakeven teórico** para 3R contra 1,3R: `p* = 1,3 / 4,3 = 30,23%`.

| Grupo | n | Sucesso | IC95% (Wilson) | Expectativa (R) | vs breakeven |
|---|---:|---:|---|---:|---:|
| **Baseline — toda barra, na direção dela** | 100.515 | 30,82% | [30,54%; 31,11%] | +0,0253 | +0,59 pp |
| **Padrão 1** | 7.119 | **31,32%** | [30,26%; 32,41%] | +0,0470 | +1,09 pp |
| **Padrão 2** | 6.894 | **31,10%** | [30,02%; 32,20%] | +0,0373 | +0,87 pp |
| Controle aleatório (n=7.000 × 20 seeds) | — | 30,29% ± 0,57pp | [29,15%; 31,14%] | — | +0,06 pp |

**Testes de significância:**

| Comparação | Resultado |
|---|---|
| P1 vs baseline | OR = 1,024 · Fisher **p = 0,374** — não significativo |
| P2 vs baseline | OR = 1,013 · Fisher **p = 0,628** — não significativo |
| P1 vs controle aleatório | z = **+1,81** — não significativo (5%) |
| P2 vs controle aleatório | z = **+1,41** — não significativo (5%) |
| P1 vs breakeven | binomial p = 0,023 |
| P2 vs breakeven | binomial p = 0,060 |

**Leitura correta:** os padrões estão marginalmente acima do breakeven, mas **não estão
acima do baseline**. Ou seja, o pouco que existe *não vem do padrão* — vem de uma
persistência genérica presente em qualquer barra deste instrumento (ver §7).
Detectar o padrão não agrega nada sobre simplesmente operar a direção da última barra.

**Direção contrária (fade):** operar contra a reversão é claramente pior
(P1: 28,95%, exp −0,055; P2: 29,39%, exp −0,036). O lado da reversão é o lado melhor —
apenas não é bom o suficiente.

**Deduplicação de eventos sobrepostos** (mantendo só o primeiro sinal enquanto um trade
está aberto): P1 cai para 31,16% (n=4.855) e **P2 cai para 30,26% (n=4.875) — exatamente
o breakeven**. Cerca de 30% dos eventos são dependentes de outro já em curso.

---

## 4. Distribuição MAE / MFE

Valores em múltiplos de `R` (1R = 3.27 USD).

| Métrica | P1 | P2 |
|---|---|---|
| MFE mediana | 1,38 R | 1,37 R |
| MFE p75 / p90 | 3,10 / 3,43 R | 3,09 / 3,42 R |
| MAE mediana | 1,44 R | 1,44 R |
| MAE p75 / p90 | 1,68 / 1,90 R | 1,69 / 1,91 R |
| Barras até saída (mediana / p90) | 6 / 17 | 6 / 17 |

**Vencedores:**

| | P1 | P2 |
|---|---|---|
| Barras até 3R (mediana / p90) | 9 / 20 | 9 / 19 |
| Tempo até 3R (mediana / p90) | 12,1 min / 54,8 min | 12,2 min / 53,5 min |
| **MAE dos vencedores (mediana / p90)** | **0,51 R / 1,13 R** | **0,49 R / 1,12 R** |

**Perdedores:** MFE mediana 0,73 R (p90 = 2,23 R) em ambos; saída em 4 barras (mediana).

**Observação operacional relevante (o único achado com valor prático):** os trades
vencedores raramente sofrem drawdown — MAE mediana de ~0,50 R e p90 de ~1,13 R.
O stop de 1,3 R é **generoso**: apenas ~10% dos vencedores chegam perto dele. Um stop de
1,2 R preservaria quase todos os vencedores. Isso não cria vantagem, mas indica que a
geometria proposta não está sacrificando trades bons — o problema é a frequência de acerto.

---

## 5. Expectativa e o efeito do custo de transação

Este é o ponto que encerra a discussão. Expectativa por trade, em R, com custo `c`
aplicado na entrada e na saída:

| Custo | Custo em USD | p breakeven | Exp. P1 | Exp. P2 | Exp. baseline |
|---|---:|---:|---:|---:|---:|
| 0,00 R | 0,00 | 30,23% | +0,047 | +0,037 | +0,025 |
| 0,02 R | 0,07 | 30,70% | +0,027 | +0,017 | +0,005 |
| **0,05 R** | **0,16** | **31,40%** | **−0,003** | **−0,013** | **−0,025** |
| 0,10 R | 0,33 | 32,56% | −0,053 | −0,063 | −0,075 |
| 0,15 R | 0,49 | 33,72% | −0,103 | −0,113 | −0,125 |

O spread típico do XAUUSD (0,15–0,35 USD) equivale a **0,05–0,11 R**. Com um custo de
apenas 0,05 R o breakeven sobe para 31,40%, **acima da taxa de acerto dos dois padrões**.

> **Toda a vantagem medida cabe dentro do spread.** Mesmo aceitando os números brutos
> pelo valor de face e ignorando a não-significância, os padrões são negativos na prática.

---

## 6. Melhores features — nenhuma sobrevive

57 features foram construídas (estrutura de preço, agressão, tempo, regime, lags),
todas estritamente causais. Análise univariada por quintis + Spearman, **apenas no
período de treino** (primeiras 50.264 barras), com correção de Benjamini-Hochberg:

| Universo | n | Features com BH < 0,05 |
|---|---:|---:|
| Padrão 1 | 3.583 | **0 de 56** |
| Padrão 2 | 3.519 | **0 de 56** |
| Todas as barras | 50.264 | 15 de 56 |

Dentro dos padrões, **nenhuma feature** sobrevive à correção de múltiplos testes.
As melhores p-values brutas (0,008–0,05) desaparecem completamente ao corrigir.

No universo completo (n=50k) sobrevivem 15 features — mas **todas são de regime, não de
reversão**: `aggt0`, `agg_per_R`, `regime_aggt`, `regime_dur`, `dur0`, `hour`, `hour_sin`.
O efeito é minúsculo (spread entre quintis extremos de ~2,5–3,5 pp) e a direção é
"regime calmo/pouco volume → maior taxa de sucesso" — um efeito de *trendiness*
que se aplica a qualquer barra e nada tem a ver com reversão.

**Instabilidade das features:** a correlação de Spearman entre os rankings de
importância CatBoost do 1º e do 3º terço da amostra é **0,42** — os "melhores"
preditores mudam completamente entre períodos, assinatura clássica de ruído.

---

## 7. Importância das agressões

**Praticamente nula.** Detalhamento (amostra completa, exploratório):

Saldo de agressão alinhado ao trade (`aggdn0`), por quartil:

| Quartil | P1 | P2 |
|---|---:|---:|
| Q1 (contra o trade) | 30,96% | 29,58% |
| Q2 | 31,84% | 29,14% |
| Q3 | 31,55% | 32,19% |
| Q4 (a favor do trade) | 30,96% | **33,49%** |

Em P2 há um gradiente aparentemente limpo (29,6% → 33,5%). Em P1 o mesmo corte é
**plano** (30,96% em ambos os extremos). Duas amostras do mesmo fenômeno discordando é
diagnóstico de ruído — e o teste out-of-sample confirma (§10).

A hipótese de **exaustão/absorção** (agressão incompatível com a direção da barra,
`diverg0 < 0`) foi testada explicitamente: é a mesma variável que `aggdn0` com sinal
trocado, e não sobrevive à correção de múltiplos testes em nenhum dos padrões.

Intensidade de agressão (`AGGT` / mediana das 20 anteriores):

| Quartil | P1 | P2 |
|---|---:|---:|
| Q1 (baixa) | 31,44% | **33,57%** |
| Q4 (alta) | 31,52% | 30,12% |

Novamente, P1 plano e P2 com gradiente. Sinais opostos entre os padrões.

---

## 8. Importância do tempo de formação

**Também nula, e igualmente contraditória entre os padrões.**

Tempo de formação relativo da barra de reversão (`dur_rel0`):

| Quartil | P1 | P2 |
|---|---:|---:|
| Q1 (barra rápida) | 31,18% | **33,29%** |
| Q4 (barra lenta) | **31,69%** | 30,12% |

P1 diz "barra lenta é melhor", P2 diz "barra rápida é melhor". Os dois efeitos são
menores que o erro amostral e se contradizem.

Regime de volatilidade (mediana da duração das 20 barras anteriores):

| Quartil | P1 | P2 |
|---|---:|---:|
| Q1 (rápido/volátil) | 33,03% | 33,35% |
| Q4 (lento/calmo) | 31,35% | 29,77% |

Aqui os dois concordam (regime volátil melhor), mas o efeito de ~2–3,5 pp não sobrevive
à validação out-of-sample (§10).

Horário e dia da semana também foram cortados: o melhor horário de P1 (12h–14h, 35,25%)
é o **pior** de P2 (29,15%), e o pior dia de P2 (sexta, 29,16%) é positivo em P1 (31,54%).

---

## 9. Melhores combinações de features

Regras compostas selecionadas no treino, testadas em VAL e TEST:

| Regra | TRAIN n / p | VAL n / p | TEST n / p |
|---|---|---|---|
| P2 & `aggdn0 > 0` | 2.767 / 31,80% | 1.043 / 32,69% | 1.679 / **30,91%** |
| P2 & `dur_rel0 < 1` | 2.091 / 31,85% | 792 / 33,08% | 1.216 / **30,51%** |
| P2 & `aggt_rel0 < 0,8` | 1.649 / 31,35% | 601 / 33,28% | 956 / **31,38%** |
| P2 & `aggdn0>0` & `dur_rel0<1` | 1.762 / 32,69% | 663 / 32,88% | 1.059 / **31,35%** |
| P1 & `dur_rel50 < 1` | 1.564 / **29,16%** | 638 / 32,76% | 843 / 32,98% |
| P1 ou P2 & `run_prev == 4` | 915 / 32,13% | 362 / 31,49% | 512 / 31,64% |

Referência: breakeven sem custo 30,23%, **com custo de 0,05 R: 31,40%**.

Nenhuma regra fica de forma consistente acima de 31,40% nos três períodos. A única com
TEST alto (P1 & regime volátil, 32,98%) tinha TRAIN de **29,16%** — abaixo até do
breakeven sem custo. É uma inversão de sinal, isto é, ruído.

---

## 10. Performance out-of-sample

### 10.1 Walk-forward (5 folds expansivos, embargo de 100 barras)

CatBoost (`depth=4, lr=0,03, l2=10`) e LightGBM, todas as 57 features:

| Universo | Modelo | n OOF | Taxa base | **ROC-AUC** | PR-AUC | Brier | Brier constante |
|---|---|---:|---:|---:|---:|---:|---:|
| P1 | CatBoost | 4.272 | 31,58% | **0,4951** | 0,3237 | 0,2180 | 0,2161 |
| P1 | LightGBM | 4.272 | 31,58% | **0,4925** | 0,3208 | 0,2244 | 0,2161 |
| P2 | CatBoost | 4.137 | 30,89% | **0,5073** | 0,3106 | 0,2157 | 0,2135 |
| P2 | LightGBM | 4.137 | 30,89% | **0,4994** | 0,3103 | 0,2226 | 0,2135 |
| P1+P2 | CatBoost | 8.408 | 31,22% | **0,5062** | 0,3253 | 0,2153 | 0,2147 |
| P1+P2 | LightGBM | 8.408 | 31,22% | **0,4977** | 0,3174 | 0,2189 | 0,2147 |
| Todas as barras | CatBoost | 60.309 | 30,61% | **0,5086** | 0,3123 | 0,2126 | 0,2124 |
| Todas as barras | LightGBM | 60.309 | 30,61% | **0,5002** | 0,3058 | 0,2135 | 0,2124 |

**AUC entre 0,49 e 0,51 em todas as 8 configurações.** O PR-AUC é igual à prevalência.
E o **Brier score é pior que o do preditor constante em todos os casos** — os modelos
são não só inúteis como mal calibrados. Por fold, a AUC oscila entre 0,46 e 0,55 sem
qualquer tendência.

### 10.2 Teste final no período reservado

Modelo treinado até 70% das barras (com embargo), avaliado nos 30% finais
(2026-06-11 a 2026-08-21), threshold escolhido **apenas na validação**:

```
TEST: n=4.064   base=30,73%   AUC=0,4908   PR-AUC=0,3104
      Brier=0,2144  (constante=0,2129)
threshold p80 da VAL = 0,3339
  selecionados:      n=789   sucesso=32,07%
  nao-selecionados:  n=3.275 sucesso=30,41%
  binomial p(>breakeven sem custo) = 0,140
  binomial p(>breakeven com 0,05R) = 0,355
```

Bootstrap em blocos (blocos de 50 eventos, respeitando a dependência entre sinais vizinhos):

| Conjunto | p | IC95% em blocos | P(p > breakeven) | P(p > breakeven c/ custo) |
|---|---:|---|---:|---:|
| TEST completo | 30,73% | [29,45%; 32,14%] | 0,787 | **0,189** |
| TEST selecionados | 32,07% | [29,91%; 34,85%] | 0,948 | **0,751** |

**AUC abaixo de 0,50 no período reservado.** A seleção por threshold não é significativa.

### 10.3 A hipótese "regime calmo" colapsa fora da amostra

A única hipótese que sobreviveu à univariada no treino (`regime_aggt` e `aggt0` baixos):

| Universo | TRAIN | VAL | TEST |
|---|---|---|---|
| P1 | n=624 / 34,13% | n=18 / 50,00% | n=71 / 40,85% |
| P2 | n=600 / 34,50% | n=17 / **23,53%** | n=73 / 31,51% |
| P1+P2 | n=1.207 / 34,80% (p=0,005) | n=37 / 37,84% (p=0,48) | n=144 / 36,81% (p=0,12) |
| Todas | n=8.487 / 31,84% (p=0,034) | n=352 / **28,69%** (p=0,48) | n=970 / 32,27% (p=0,36) |

Além da inconsistência (P2 inverte, "Todas" inverte), há um problema mais grave:
o threshold calibrado no treino selecionava 17% dos eventos no treino e apenas
**1,2% na validação**. O nível absoluto de agressão sofreu drift estrutural — features
de nível não são transportáveis no tempo neste dataset.

---

## 11. Threshold de probabilidade recomendado

**Nenhum.** Não há threshold recomendável.

Para registro, a curva de expectativa por threshold nos dados OOF walk-forward:

| Quantil | p mínimo | n | Sucesso | Exp. (R) | binom p |
|---|---:|---:|---:|---:|---:|
| ≥ 0,00 | 0,1775 | 8.408 | 31,22% | +0,043 | 0,025 |
| ≥ 0,70 | 0,3210 | 2.523 | 31,71% | +0,064 | 0,056 |
| ≥ 0,80 | 0,3316 | 1.682 | 33,00% | +0,119 | 0,008 |
| ≥ 0,90 | 0,3474 | 841 | 33,65% | +0,147 | 0,018 |
| ≥ 0,95 | 0,3638 | 421 | 34,68% | +0,191 | 0,028 |

Essa monotonicidade é tentadora e **deve ser rejeitada**, por quatro razões:

1. É calculada sobre folds walk-forward que incluem o período de treino inicial;
   no TEST reservado a mesma seleção entrega 32,07% com **p = 0,14**.
2. A AUC agregada é 0,506 — matematicamente, uma AUC dessas não sustenta um lift real
   de 2 pp no decil superior; o padrão vem de poucos folds.
3. Os p-values ignoram a dependência entre eventos sobrepostos (~30% da amostra).
   O bootstrap em blocos devolve IC de [29,9%; 34,9%].
4. Com custo de 0,05 R o breakeven é 31,40%; os intervalos de confiança cobrem esse
   valor em todos os cortes.

---

## 12. Condições em que o sinal deve ser ignorado

Como não há sinal utilizável, a resposta rigorosa é: **em todas**. Os filtros que a
amostra sugere (regime calmo, agressão alinhada, barra rápida) invertem de sinal entre
P1 e P2 e entre períodos, e portanto não constituem condições de descarte confiáveis.

Se o usuário optar por operar assim mesmo, as restrições que **pioraram** os resultados
de forma minimamente consistente foram:

- `run_prev >= 5` em P1 (5+ barras consecutivas antes da reversão): 29,19%, abaixo do
  breakeven — mas em P2 o mesmo corte dá 32,42%. Inconsistente.
- Trades que atravessam fim de semana (0,28% dos casos, amostra pequena demais).

Nenhuma dessas atinge significância estatística.

---

## 13. Estatística vs Machine Learning

| Abordagem | Melhor resultado | Veredicto |
|---|---|---|
| Regra pura (padrão isolado) | P1: 31,32%, exp +0,047 R | Não supera baseline (p=0,37) |
| Regra + filtro univariado | ~33% no treino | Colapsa para ~31% no TEST |
| CatBoost 57 features | AUC OOF 0,506 / TEST 0,491 | Sem poder preditivo |
| LightGBM 57 features | AUC OOF 0,498 | Sem poder preditivo |

**As duas abordagens concordam: não há sinal.** O ML não superou a estatística simples,
e a estatística simples não superou o acaso. Isso é o resultado esperado quando o alvo
é genuinamente imprevisível — e é uma concordância tranquilizadora quanto à corretude
do pipeline.

### Os padrões têm alguma informação direcional, em qualquer geometria?

Dois testes adicionais para descartar a hipótese de que 3R/1,3R seja apenas uma geometria
ruim:

**(a) Retorno futuro médio bruto** (em R, alinhado ao lado da reversão):

| Barras à frente | Todas as barras | P1 | p | P2 | p |
|---:|---:|---:|---:|---:|---:|
| 1 | +0,0288 | +0,0414 | 0,17 | +0,0394 | 0,24 |
| 3 | +0,0255 | +0,0500 | 0,14 | +0,0315 | 0,72 |
| 5 | +0,0232 | +0,0511 | 0,19 | +0,0212 | 0,93 |
| 10 | +0,0246 | +0,0327 | 0,79 | +0,0408 | 0,59 |
| 20 | +0,0227 | +0,0250 | 0,96 | +0,0671 | 0,29 |
| 50 | +0,0418 | +0,0035 | 0,57 | +0,0469 | 0,94 |

Nenhum horizonte apresenta diferença significativa (todos p > 0,14). Note que **todas as
barras** têm retorno futuro positivo de ~+0,025 R na sua própria direção: é essa
persistência estrutural genérica — e não os padrões — que produz a taxa base de 30,8%.

**(b) Grid de 25 geometrias alvo/stop.** Vantagem do padrão sobre o baseline, em pontos
percentuais (células: P1 / P2):

| Alvo \ Stop | 0,5 R | 0,8 R | 1,0 R | 1,3 R | 2,0 R |
|---|---|---|---|---|---|
| 1,0 R | +0,40 / +0,23 | +0,27 / +0,40 | +0,89 / +0,32 | +0,75 / +0,58 | +0,42 / +0,78 |
| 1,5 R | +0,14 / +0,01 | −0,04 / +0,21 | +0,62 / +0,13 | +0,56 / +0,38 | +0,68 / +0,25 |
| 2,0 R | −0,07 / +0,54 | −0,37 / +0,49 | +0,51 / +0,48 | +0,62 / +0,64 | +0,73 / +0,61 |
| 3,0 R | +0,09 / +0,30 | −0,39 / +0,11 | +0,18 / +0,21 | **+0,50 / +0,28** | +0,64 / +0,14 |
| 4,0 R | −0,23 / +0,12 | −0,67 / +0,13 | −0,23 / +0,19 | +0,11 / +0,40 | +0,00 / +0,05 |

Em 25 geometrias, a vantagem sobre o baseline fica entre **−0,67 e +0,89 pp**, com
sinais alternados. Não existe geometria em que os padrões carreguem informação.
**A conclusão não é um artefato da escolha 3R/1,3R.**

---

## 14. Limitações e controles de viés

### Controles executados

| Controle | Resultado |
|---|---|
| **Look-ahead nas features** | Todas as features usam apenas barras ≤ t; rollings causais |
| **Leakage (labels embaralhados)** | AUC = **0,5011** OK (esperado 0,50) |
| **Controle positivo (MFE injetado)** | AUC = **1,0000** OK (pipeline detecta sinal quando existe) |
| **Split temporal** | Nunca aleatório; walk-forward expansivo |
| **Embargo** | 100 barras entre treino e teste (trade máximo = 70 barras) |
| **Sobreposição de eventos** | Quantificada: ~30%; deduplicação derruba P2 ao breakeven |
| **Candles consecutivos** | Impossível por construção — dois sinais nunca são adjacentes |
| **Dependência entre amostras** | Bootstrap em blocos de 50 eventos |
| **Múltiplos testes** | Correção Benjamini-Hochberg em 56 features × 3 universos |
| **Estabilidade temporal** | Taxa mensal 28,8%–33,6% (ambos), sem tendência |
| **Grupo de controle** | 20 seeds × 7.000 eventos aleatórios |
| **Ambiguidade alvo/stop** | 0 ocorrências nos padrões (regra conservadora documentada) |
| **Custo de transação** | Modelado explicitamente (§5) |

### Riscos e limitações remanescentes

1. **Buraco de 82 dias** (jan–fev/2026) na base. Reduz a diversidade de regimes cobertos.
2. **Amostra de 9,5 meses.** Um único ciclo macro do ouro. Um padrão poderia funcionar
   em regimes não representados aqui.
3. **`TICKVOL`/`VOL` como agressão compra/venda** é a interpretação dada pelo CLAUDE.md.
   A correlação de 0,992 entre as séries sugere que elas podem ser proxies do mesmo
   agregado, e não um verdadeiro delta de fluxo. **Se houver acesso a order flow real
   (delta por nível, imbalance de book), a conclusão poderia mudar** — esse é o teste
   que eu recomendaria antes de abandonar a linha de pesquisa.
4. **Sem modelagem de slippage** além do custo linear.
5. Todo o backtest é sobre `HIGH`/`LOW` de barras, sem tick data — a ordem intrabarra é
   desconhecida. Isso é mitigado pela geometria (alvo e stop distam 4,3 R, mais que uma barra).

### Overfitting

O relatório não sofre de overfitting porque **não há modelo a superajustar**: nenhuma
configuração passou do estágio de validação. O risco real aqui era o oposto — continuar
buscando até produzir um resultado positivo. Os pontos onde isso quase aconteceu estão
documentados (§10.3 e §11) precisamente para registrar que foram rejeitados.

---

## 15. Implementação MQL5

**Recomendação: Opção A, e apenas o detector — sem score de probabilidade.**

A Opção B (exportar CatBoost via ONNX) **não se justifica**: exportar um modelo com
AUC 0,49 out-of-sample apenas transferiria ruído para produção com uma aparência de
sofisticação. O trabalho de garantir paridade numérica Python↔MQL5 seria gasto para
reproduzir fielmente um preditor sem informação.

A Opção A na sua forma completa (regras estatísticas com filtros) também não se
justifica, porque nenhuma regra sobreviveu ao out-of-sample (§9).

O que **é** entregável e útil:

`MQL5/Indicators/RangeReversalScanner.mq5` — um indicador que:

1. Detecta P1 e P2 em tempo real, marcando as reversões de alta e de baixa com setas.
2. Calcula todas as features do estudo com **exatamente** as mesmas fórmulas do Python.
3. Produz sinal **somente após o fechamento** da barra de reversão (nunca a barra em
   formação) e não usa dado futuro.
4. Grava um CSV com features + timestamp para permitir **validação forward genuína**:
   coletar 6–12 meses de sinais novos e reexecutar `src/04_stats.py` sobre eles.
5. Expõe thresholds configuráveis (`BodyRatio` de P1 e P2), para o caso de o usuário
   querer explorar variações.

O indicador **não emite score de probabilidade**, por decisão deliberada e documentada.

**Validação de paridade:** `src/11_parity.py` gera `out/parity_reference.csv` com as
features das últimas barras calculadas em Python. Rodando o indicador sobre o mesmo
CSV no MetaTrader e comparando os dois arquivos, verifica-se a fidelidade da
implementação antes de qualquer uso.

---

## Veredicto

> Nos 100.528 range bars de XAUUSD analisados, os Padrões 1 e 2 ocorrem com frequência
> adequada (7.119 e 6.894 eventos) mas **não apresentam vantagem estatisticamente
> robusta**. Suas taxas de acerto (31,32% e 31,10%) não diferem significativamente do
> baseline de qualquer barra na sua própria direção (30,82%; p = 0,37 e p = 0,63) nem
> de eventos aleatórios (z = +1,81 e +1,41). Nenhuma feature de agressão, tempo de
> formação, estrutura ou regime sobrevive à correção de múltiplos testes dentro dos
> padrões. Modelos de gradient boosting atingem AUC de 0,491 a 0,507 out-of-sample,
> com Brier score pior que o preditor constante. A pequena margem bruta sobre o
> breakeven é integralmente consumida por um custo de transação de 0,05 R (0,16 USD),
> abaixo do spread típico do instrumento. A ausência de sinal persiste em 25 geometrias
> alvo/stop distintas e em todos os horizontes de retorno testados.
>
> **A investigação não encontrou evidência suficiente para construir um indicador
> preditivo.** Recomenda-se não operar estes padrões e não exportar modelo para MQL5.

### Se o usuário quiser continuar

Em ordem de retorno esperado sobre o esforço:

1. **Order flow real** — delta por preço, imbalance de book, absorção medida em nível.
   A limitação nº 3 é a mais provável de estar escondendo sinal.
2. **Contexto de estrutura** — os padrões foram testados isoladamente. Testá-los apenas
   em suportes/resistências, VWAP, ou extremos de sessão muda a população de eventos.
   (O repositório já contém trabalho prévio de S/R automático.)
3. **Ranges maiores** — 3.27 USD é granular; o ruído de microestrutura domina.
   Ranges de 10–20 USD reduziriam a amostra mas aumentariam a razão sinal/ruído.
4. **Validação forward** com o scanner MQL5, acumulando dados fora desta amostra.

---

### Reprodução

```
python src/00_validate.py    # validação empírica dos dados
python src/03_features.py    # 57 features causais
python src/02_build.py       # detecção de padrões + rotulagem de caminhos
python src/04_stats.py       # baseline estatístico
python src/05_uni.py         # univariada + Benjamini-Hochberg
python src/06_ml.py          # walk-forward CatBoost + LightGBM
python src/07_break.py       # cortes por regime/horário/agressão
python src/08_bias.py        # controles de viés e vazamento
python src/09_final.py       # teste final OOS + custo
python src/10_grid.py        # viés direcional + grid de geometrias
python src/11_parity.py      # referência de paridade Python <-> MQL5
```
