# Relatório final — predição de pontos de virada no Renko do mini índice (WIN)

> **ATUALIZAÇÃO — rodada 2.** Este documento cobre a rodada 1, com rótulo de *sequência de cores*. Uma segunda rodada trocou o rótulo para **pontos** (+100 antes do extremo oposto do candle de virada) e adicionou as relações `t > t-1` / `t < t-1` para todas as features normalizadas. Resultados em **[`round2_points_label.md`](round2_points_label.md)**. Resumo: o novo rótulo é bem melhor (taxa-base 57,6%, expectativa bruta positiva), as novas features passam no teste nulo em desenvolvimento (p = 0,00, contra p = 0,05 aqui), mas **a AUC out-of-sample cai para 0,4775** — o sinal existe em julho e some em agosto.
>
> **Correção:** a seção 2.5 abaixo afirma que `BarDurationF` não é tempo de relógio. **Está errada.** A coluna é *minutos × 1000* (confirmado pelo usuário e verificado com erro de 0,16 s no intervalo de fim de semana). Nenhum resultado de modelo muda — a unidade é um multiplicador constante.

**Base:** `WINFUT_11R_AGB_AGS_BDURF_QT_TRD.csv` — 20.000 bricks fechados, 35 pregões, 29/06/2026 a 14/08/2026.
**Pipeline:** `src/run_pipeline.py` · **Seed:** 42 · **Data de execução:** 16/08/2026

---

## 0. Resposta à pergunta de pesquisa (seção 40)

> *As características de agressão, volume, negócios, duração e estrutura do candle no próprio candle de virada permitem identificar, antes de qualquer confirmação futura, quais reversões terão continuação de pelo menos 2 ou 3 candles?*

### **Não.**

Com esta base e com este alvo, não foi encontrado sinal preditivo que sobreviva a validação honesta. O melhor resultado de toda a investigação — AUC **0,5357** em walk-forward — **não é distinguível do que o mesmo procedimento de busca produz sobre rótulos embaralhados** (teste nulo: média 0,5157, p95 0,5311, **máximo 0,5368**, p = 0,05). Ou seja, o melhor modelo é estatisticamente indistinguível do melhor ruído.

A seção 41 do CLAUDE.md exige nove condições simultâneas. **Cinco falharam.** O detalhamento está na seção 9 deste relatório.

Seguindo a instrução explícita da seção 40 — *"Se a resposta for não, não forçar um modelo"* — o indicador NTSL foi gerado (é entregável obrigatório da seção 42) mas está marcado como **não recomendado para operação**, com os números da validação impressos no próprio cabeçalho do arquivo.

---

## 1. Metodologia

Ordem de execução conforme seção 44, sem pular etapas:

```
CSV → validação → features → targets → EDA → baselines → walk-forward
    → CatBoost → importância → robustez → threshold → economia → NTSL
```

### Separação temporal

| bloco | barras | uso |
|---|---|---|
| **DEV** | 0 – 15.999 (80%) | features finais, hiperparâmetros, threshold |
| *embargo* | 16.000 – 16.002 | 3 barras (= horizonte máximo do target) |
| **HOLDOUT** | 16.003 – 19.999 (7 pregões) | **avaliado uma única vez, no fim** |

Dentro do DEV: walk-forward expansivo de 6 folds, com embargo de 3 barras entre treino e validação em cada fold. Nenhum embaralhamento em lugar nenhum (verificado por teste automatizado).

---

## 2. Integridade dos dados — o que a base realmente é

Relatório completo: `reports/01_data_validation.md`. Achados que mudaram o desenho do estudo:

### 2.1 O arquivo vem em ordem decrescente

19.178 passos para trás no tempo, 0 para frente. O arquivo é invertido explicitamente (`load_data.to_chronological`), **não** com `sort_values` — 1.163 linhas têm timestamp duplicado (vários bricks fechando no mesmo tick) e uma ordenação cega destruiria a ordem correta delas.

### 2.2 O brick tem 50 pontos, não 55

`|Close − Open| = 50,0` em **20.000 de 20.000** barras completas. O "11R" do nome do arquivo não corresponde ao tamanho efetivo do brick. `BRICK_SIZE` foi corrigido para 50 e todas as métricas em bricks usam esse valor.

### 2.3 Uma barra parcial foi excluída (registrada)

| BarIndex | Data | motivo |
|---|---|---|
| 20000 | 14/08/2026 18:22:56.914 | `\|Close−Open\| = 25 ≠ 50` — brick ainda em formação |

Única exclusão do estudo. Está registrada em `results/01_data_validation.json` e em `results/03_dataset_manifest.json`.

### 2.4 A estrutura do candle tem apenas 2 graus de liberdade

Descoberta relevante e não antecipada pelo CLAUDE.md. Neste export:

```
CloseLocation ∈ {0, 1}   exatamente — nunca um valor intermediário
```

O fechamento está **sempre** no extremo do range: brick de alta fecha na máxima, brick de baixa fecha na mínima. Consequências, todas identidades exatas verificadas numericamente:

| identidade | consequência |
|---|---|
| `CloseLocation ≡ (Direction+1)/2` | r = 1,000000 — é a mesma feature |
| `BodyNorm + WickTotalNorm ≡ 1` | r = −1,000000 — uma é o complemento da outra |
| `OpenLocation ≡ 1 − BodyNorm` | redundante |
| brick de alta ⇒ `UpperWick ≡ 0` | só existe pavio contra a direção |
| brick de baixa ⇒ `LowerWick ≡ 0` | idem |

**Toda a "estrutura do candle" pedida na seção 7 se reduz a duas quantidades: `Range` e `Direction`.** As demais foram mantidas no dataset para auditoria, mas não carregam informação adicional — o que explica por que o grupo `STRUCT+CANDLE` nunca superou o baseline.

Range varia de 50 a 150 pontos (mediana 95), então a normalização pedida na seção 4 **é** significativa — a seção 36 estava certa em levantar a questão.

### 2.5 `BarDurationF` não é tempo de relógio

| medida | valor |
|---|---|
| correlação com Δt do timestamp | **0,00098** |
| correlação em logs (Δt > 0) | 0,408 |
| zeros | 3.607 (18%) |
| máximo | 3.752.167 (barras de fim de pregão) |

A coluna não mede o tempo decorrido entre barras. As barras de fim de sessão têm valores 4 ordens de grandeza acima da mediana (217), o que **contamina a média móvel e o resíduo**. Isso produziu um artefato instrutivo na EDA:

| grupo | média de `DurationResidual` | **mediana** |
|---|---|---|
| reversão vencedora | **+5.032,7** | **+43,2** |
| reversão falsa | −128,4 | +39,5 |

A diferença de médias é ~5.161 e some completamente na mediana (43,2 vs 39,5). É produzida por um punhado de barras extremas, não por sinal. Por isso `DurationResidual` foi mantida (a seção 5 exige) mas acompanhada de `LogDurationResidual20`, robusta a esses outliers.

### 2.6 Bricks sintéticos

420 barras com `Quantity = 0`, `Trades = 0` e `Duration = 0` — bricks de preenchimento criados quando o preço salta vários bricks num único tick. Foram **mantidos** (são estrutura de preço real) e marcados com `IsSyntheticBrick`, nunca removidos em silêncio.

---

## 3. Features

121 features candidatas. Construção em `src/features.py`, com a regra de que **nenhuma função daquele módulo pode usar `shift(-k)`** — verificada por teste automatizado.

- **Seção 4** (obrigatórias): `AggBuyNorm`, `AggSellNorm`, `AggBalanceNorm`, `AggTotalNorm`, `QuantityNorm`, `TradesNorm`, todas ÷ `RangeSafe = max(High−Low, 1,0)`.
- **ε = 1,0**: o WIN negocia em passos de 5 pontos e o range mínimo observado é 50, então ε fica abaixo de qualquer range real e só age em barras degeneradas.
- **Seção 5**: `DurationResidual = BarDurationF − SMA20`, mantida como pedido, mais `DurationRatio20`, `DurationResidualPct` e as versões log.
- **Seção 6**: 5 lags para as 7 famílias principais; 3/5/8/10 testados na seção 7 deste relatório.
- **Seções 7–11**: estrutura do candle, wicks, imbalance, `QuantityPerTrade`, resíduos e razões contra média 20, contagens de sequência, divergência direção × agressão.

---

## 4. Targets

`src/targets.py` — **único módulo autorizado a usar futuro**. Colunas de target usam prefixo `y_`/`fwd_` para que o filtro de features possa rejeitá-las mecanicamente.

Convenção adotada: após a barra de virada `t` (que já é a 1ª da nova direção), exigem-se mais `cont` barras. `p2c2` = 2 candles antes, virada em `t`, mais `t+1` e `t+2`.

### O achado mais importante do estudo

| target | candidatos | por pregão | taxa-base | **P incondicional comparável** | **ganho** |
|---|---|---|---|---|---|
| `p2c2` | 4.343 | 124,1 | **0,4611** | `P(2 barras na mesma direção)` = **0,4631** | **−0,0020** |
| `p2c3` | 4.343 | 124,1 | **0,3118** | `P(3 barras na mesma direção)` = **0,3182** | **−0,0064** |
| `p3c2` | 2.898 | 82,8 | 0,4805 | 0,4631 | +0,0174 |
| `p3c3` | 2.898 | 82,8 | 0,3186 | 0,3182 | +0,0004 |
| `p2c2e` (exato) | 1.445 | 41,3 | 0,4221 | 0,4631 | −0,0410 |
| `p3c2e` (exato) | 929 | 26,5 | 0,4790 | 0,4631 | +0,0159 |

**O padrão estrutural pedido — "2 ou 3 candles numa direção seguidos de uma virada" — não tem, por si só, nenhum poder preditivo.** A probabilidade de continuação após uma virada assim é igual à probabilidade de continuação a partir de uma barra qualquer. Em `p2c2` e `p2c3` é levemente *pior*.

Isso é consistente com o comportamento do Renko: os runs de direção têm distribuição próxima de geométrica (comprimento médio 3,13; `P(mudança de direção) = 0,3198` praticamente constante em qualquer ponto do run), ou seja, o processo é quase sem memória na dimensão que o target explora.

O baseline da seção 39 (`EXP000_ALWAYS_SIGNAL`) tem, por construção, AUC = 0,5000 e precision = taxa-base. **Todo o resto do estudo é a pergunta: alguma feature bate isso?**

---

## 5. Baselines por grupo de informação (seção 39)

Walk-forward em DEV, target `p2c2`. Tabela completa: `reports/05_baselines_p2c2.md`.

| experimento | modelo | AUC | IC95% | precision@0,5 | folds AUC>0,5 | p vs baseline |
|---|---|---|---|---|---|---|
| `EXP000_ALWAYS_SIGNAL` | — | 0,5000 | — | 0,4537 (=base) | 0/6 | — |
| `EXP011_STRUCT+VOL` | CatBoost | **0,5347** | [0,510; 0,559] | 0,5061 | 5/6 | 0,081 |
| `EXP010_STRUCT+AGG` | CatBoost | 0,5330 | [0,509; 0,555] | 0,4678 | 5/6 | 0,084 |
| `EXP101_EXTENDED` | RandomForest | 0,5295 | [0,506; 0,554] | 0,4658 | 4/6 | 0,141 |
| `EXP014_BASE` | CatBoost | 0,5286 | [0,505; 0,552] | 0,4806 | 4/6 | 0,169 |
| `EXP100_EXTENDED` | Árvore | 0,5277 | [0,503; 0,551] | 0,4825 | 5/6 | 0,181 |
| `EXP009_STRUCT` | CatBoost | 0,5155 | [0,491; 0,539] | 0,5114 | 3/6 | 0,206 |
| `EXP008_EXTENDED` | Logística | 0,5127 | [0,489; 0,536] | 0,4459 | 3/6 | — |
| `EXP012_STRUCT+TIME` | CatBoost | 0,4918 | [0,466; 0,514] | 0,4475 | 2/6 | 0,656 |

**Nenhum experimento atinge p < 0,05 contra o baseline estrutural.** O melhor é p = 0,081.

### Nada é estável entre targets

O mesmo conjunto de experimentos rodado nos 4 targets (`reports/05_baselines_*.md`):

| feature set + CatBoost | `p2c2` | `p3c2` | `p2c3` | `p3c3` |
|---|---|---|---|---|
| STRUCT+VOL | **0,5347** | 0,5059 | 0,5090 | 0,5246 |
| STRUCT+AGG | 0,5330 | 0,5025 | **0,5368** | 0,5048 |
| BASE | 0,5286 | 0,5061 | 0,5249 | 0,5085 |
| EXTENDED | 0,5109 | 0,4966 | 0,5312 | 0,5232 |
| STRUCT+TIME | 0,4918 | 0,5021 | 0,5037 | 0,5126 |

O vencedor muda a cada coluna, e a diferença entre o melhor e o pior de cada linha (~0,03) é da ordem do erro padrão da própria estimativa (~0,009–0,012). Isso é a assinatura de ruído, não de sinal.

---

## 6. Análise condicional (seção 38)

`results/04_conditional_p2c2.csv` — 121 features × 3 lags = 363 testes de `P(feature | reversão válida)` vs `P(feature | reversão falsa)`.

| feature | lag | AUC | Cohen *d* |
|---|---|---|---|
| `RangeRatio20` | 1 | 0,5264 | +0,072 |
| `RunLength` | 1 | 0,5253 | +0,067 |
| `AggTotalPerTrade` | 2 | 0,5252 | +0,079 |
| `BodyNorm` | 2 | 0,5238 | +0,085 |
| `AggTotalRatio20` | 1 | 0,5220 | +0,097 |

O maior |AUC − 0,5| de **todas as 363 comparações** é 0,026, e todos os tamanhos de efeito são |*d*| < 0,10 (desprezível pela convenção usual). Com n = 4.343 o erro padrão de uma AUC é ≈ 0,0088, então 0,026 é ~3σ — mas em 363 testes espera-se por acaso cerca de um resultado a 3σ. **Nenhuma feature isolada distingue reversão vencedora de reversão falsa.**

Comparação direta dos grupos (seção 36):

| grupo | Range | BodyNorm | UpperWickNorm | LowerWickNorm | AggTotalNorm | AggBalanceNorm |
|---|---|---|---|---|---|---|
| continuidade | 78,72 | 0,7120 | 0,1483 | 0,1398 | 191,92 | −1,99 |
| reversão | 125,81 | 0,4025 | 0,2988 | 0,2987 | 201,49 | −0,22 |
| **reversão vencedora** | **125,79** | **0,4027** | **0,3000** | **0,2973** | **214,89** | **−0,05** |
| **reversão falsa** | **126,06** | **0,4017** | **0,3025** | **0,2959** | **208,50** | **−0,16** |

Continuidade e reversão são muito diferentes (o brick de reversão tem range 60% maior — mas isso é geometria do Renko, é a definição do brick de reversão, e é conhecido *antes* da barra). **Vencedora e falsa são indistinguíveis** em todas as colunas.

Respondendo às perguntas da seção 37:

| pergunta | resposta |
|---|---|
| Qual a frequência real do evento? | 124 candidatos/pregão em `p2c2`; 46,1% continuam |
| Diferença entre reversões p/ cima e p/ baixo? | Nenhuma relevante (0,4633 vs 0,4589) |
| As reversões possuem maior range? | Sim, +60% — mas é geometria do brick, não previsão |
| As reversões possuem wicks maiores? | Sim (0,30 vs 0,14) — mesma razão geométrica |
| Existe mudança de agressão antes da virada? | Não mensurável (\|*d*\| < 0,10 em todos os lags) |
| Existe alteração de duração? | Não (mediana 43,2 vs 39,5 — a diferença de médias é outlier) |
| Existe alteração de quantidade/trades? | Não (\|*d*\| < 0,10) |

---

## 7. CatBoost: busca de hiperparâmetros e estabilidade

`reports/06_catboost_tuning.md`. 96 configurações (4 conjuntos × 4 profundidades × 3 taxas × 2 regularizações) por target, com early stopping num recorte temporal final do próprio treino — **nunca** no conjunto de validação.

| target | melhor conjunto | depth | lr | AUC OOF | AUC/fold | desvio | folds>0,5 |
|---|---|---|---|---|---|---|---|
| `p2c2` | STRUCT+AGG | 4 | 0,02 | 0,5357 | 0,5391 | 0,0351 | **6/6** |
| `p3c2` | STRUCT+AGG | 5 | 0,10 | 0,5268 | 0,5320 | 0,0243 | 5/6 |

Dispersão do AUC OOF entre as 96 configurações de `p2c2`: **mín 0,4864, máx 0,5519, desvio 0,0134**. O desvio entre configurações (0,0134) é apenas ligeiramente maior que o erro padrão de uma única estimativa (~0,009) — quase toda a diferença aparente entre configurações é ruído amostral, e o "melhor" é um máximo amostral, não uma estimativa não enviesada.

### Sensibilidade a lags (seções 6 e 24)

| lags | BASE | EXTENDED |
|---|---|---|
| 3 | 0,5104 | 0,5249 |
| 5 | **0,5286** | 0,5109 |
| 8 | 0,5015 | **0,5333** |
| 10 | 0,5180 | 0,4973 |

Sem tendência. O ótimo de BASE (5) é o pior de EXTENDED e vice-versa. Trocar o número de lags altera o resultado em ±0,03 de forma errática — exatamente o critério da seção 24 para declarar superajuste.

### Sensibilidade ao período da média

| período | AUC |
|---|---|
| 10 | 0,5437 |
| 20 | 0,5286 |
| 40 | 0,5143 |

Um parâmetro que o CLAUDE.md fixou em 20 por convenção move o resultado em 0,029 — mais do que a suposta vantagem do modelo sobre o baseline.

---

## 8. Importância das features (seção 22)

`reports/07_feature_importance.md`. Critério: estar no top-15 em ≥80% dos folds.

| configuração | features "estáveis" |
|---|---|
| `p2c2` / BASE | `AggBalanceNorm_lag3`, `AggBalanceNorm_lag2`, `AggBalanceNorm`, `QuantityNorm_lag2`, `DurationResidual_lag5`, `DurationResidual` |
| `p2c2` / EXTENDED | `AggTotalPerQuantity`, `LogDuration` |
| `p3c2` / BASE | `AggBalanceNorm_lag4` |
| `p3c2` / EXTENDED | `QuantityNorm_lag2`, `AggBuyNorm_lag4`, `AggBalanceChange` |

**Os quatro conjuntos não têm uma única feature em comum.** Mudar o target ou o pool de features troca completamente a lista. Pela própria seção 22 — *"uma feature que aparece como importante em apenas um período e desaparece nos demais deve ser tratada como suspeita"* — **nenhuma feature passa no critério**.

O único tema recorrente é `AggBalanceNorm` defasada, mas em lags diferentes a cada configuração (2, 3, 4), o que é o padrão esperado quando o modelo escolhe entre variáveis correlacionadas e equivalentemente inúteis.

Colinearidades exatas encontradas (`results/04_feature_correlation.csv`) que ajudam a explicar a instabilidade: `Direction ≡ CloseLocation` (r = 1,000), `BodyNorm ≡ 1 − WickTotalNorm` (r = −1,000), `AggTotalPerQuantity ≡ AggShareOfQuantity` (r = 1,000), `QuantityResidual20 ~ AggTotalResidual20` (r = 0,993).

---

## 9. Robustez (seção 23)

`reports/09_robustness_p2c2.md`.

### Por mês — o modelo inverte de sinal

| mês | n | taxa-base | AUC | precision | edge |
|---|---|---|---|---|---|
| 2026-07 | 1.903 | 0,4535 | 0,5438 | 0,4944 | +0,041 |
| 2026-08 | 345 | 0,4551 | **0,4403** | 0,4078 | **−0,047** |

Em agosto o modelo é **pior que o acaso**.

### Por regime de duração

| regime | n | AUC | edge |
|---|---|---|---|
| lenta | 1.104 | 0,4837 | −0,006 |
| normal | 923 | **0,5965** | +0,080 |
| rápida | 221 | 0,4600 | −0,002 |

Concentração total num único regime, com os outros dois abaixo de 0,5. Isso é o oposto do exigido pela seção 23 ("o modelo precisa funcionar em múltiplos regimes").

### Por volatilidade e por direção

Volatilidade: 0,5302 (alta) / 0,5415 (baixa) / 0,5158 (média) — sem padrão interpretável.
Direção, em DEV: +1 → 0,5391 / −1 → 0,5155.

### Estabilidade do desenho do target (seção 24)

Walk-forward em DEV com o mesmo conjunto BASE. As taxas-base aqui são as do **conjunto de desenvolvimento**, por isso diferem levemente das da seção 4 (série completa).

| target | taxa-base (DEV) | AUC | folds>0,5 |
|---|---|---|---|
| `p2c2` | 0,4537 | 0,5286 | 4/6 |
| `p2c3` | 0,3172 | 0,5249 | 3/6 |
| `p3c2` | 0,4761 | 0,5061 | 2/6 |
| `p3c3` | 0,3253 | 0,5085 | 4/6 |
| `p2c2e` | 0,4102 | **0,5936** | 4/6 |
| `p3c2e` | 0,4892 | 0,5391 | 4/6 |

`p2c2e` chega a 0,5936 — o maior número do estudo inteiro. Mas é a variante com menos eventos (1.445), só 4/6 folds acima de 0,5, e trocar "≥2 candles" por "exatamente 2 candles" — uma mudança semanticamente mínima — move a AUC de 0,5286 para 0,5936. **Uma alteração pequena no desenho muda o resultado drasticamente, que é a definição de superajuste dada na seção 24.**

### Teste nulo do procedimento de seleção — o resultado decisivo

Teste adicional, não pedido explicitamente, mas necessário para responder a seção 41.1 com honestidade. O "melhor AUC de uma busca" é um **máximo amostral**. Para saber quanto disso é ruído, os rótulos foram embaralhados em blocos contíguos de 40 eventos (preservando taxa-base e autocorrelação) e **o procedimento inteiro de busca foi repetido 20 vezes**.

| | valor |
|---|---|
| melhor AUC **observado** | **0,5357** |
| melhor AUC sob H₀ — média | 0,5157 |
| melhor AUC sob H₀ — desvio | 0,0099 |
| melhor AUC sob H₀ — p95 | 0,5311 |
| melhor AUC sob H₀ — **máximo** | **0,5368** |
| **p-valor** | **0,05** |

Distribuição nula completa dos 20 melhores-de-8:

```
0,4981  0,4999  0,5010  0,5094  0,5101  0,5106  0,5112  0,5114  0,5115  0,5152
0,5158  0,5175  0,5178  0,5187  0,5193  0,5244  0,5244  0,5295  0,5308  0,5368
```

**Com rótulos completamente destruídos, a mesma busca ainda entrega AUC 0,516 em média e chega a 0,537 no melhor caso — acima do 0,5357 observado com os rótulos verdadeiros.** O p-valor de 0,05 é limítrofe e, com 20 permutações, ele próprio é impreciso (IC95% binomial para p = 1/20 vai de ~0,001 a ~0,25).

Conclusão: **o ganho aparente do modelo é integralmente explicável pela busca sobre ruído.**

---

## 10. Threshold e teste final out-of-sample (seções 25 e 20)

Threshold escolhido **exclusivamente** nas predições out-of-fold de DEV, maximizando precision sujeito a ≥1 sinal/pregão. Curva completa em `results/08_final_p2c2.json` e `reports/figures/08_threshold_p2c2.png`. Escolhido: **0,50**.

### Holdout — 7 pregões, 851 eventos, avaliado uma única vez

| métrica | valor |
|---|---|
| taxa-base | 0,4536 |
| ROC AUC | 0,5158 |
| **IC95% da AUC** | **[0,4774 ; 0,5554]** — contém 0,5 |
| PR AUC | 0,4621 |
| precision @ 0,50 | 0,4673 |
| **ganho sobre a taxa-base** | **+0,0137** |
| lift | 1,03 |
| recall | 0,1295 |
| F1 | 0,2028 |
| matriz de confusão | TP 50 · FP 57 · TN 408 · FN 336 |
| taxa de falsos positivos | 0,1226 |
| taxa de falsos negativos | 0,8705 |
| sinais | 107 (15,3/pregão) |

### Métrica econômica — o modelo seleciona trades *piores*

Entrada no fechamento da barra de virada, horizonte de 12 barras:

| medida | **sinais do modelo** (n=107) | **todos os candidatos** (n=851) |
|---|---|---|
| **deslocamento médio 12 barras** | **−41,1 pts** | **+2,2 pts** |
| expectativa em bricks | **−0,82** | +0,04 |
| atingiu +2 bricks | **66,4%** | **72,0%** |
| atingiu +3 bricks | 53,3% | 55,3% |
| MFE médio | 3,67 bricks | 4,00 bricks |
| MAE médio | **4,33 bricks** | 3,96 bricks |
| barras até +2 bricks (mediana) | 2,0 | 2,0 |
| MAE antes de +2 bricks (mediana) | 90 pts | 90 pts |

**Filtrar os candidatos com o modelo é pior do que não filtrar.** Os sinais selecionados têm MFE menor, MAE maior, atingem +2 bricks com menos frequência e têm expectativa negativa, enquanto o conjunto não filtrado é aproximadamente neutro. Isto é mais forte do que "AUC insuficiente": a ordenação produzida pelo modelo é economicamente contraproducente nesta amostra.

### Assimetria por direção no holdout

| lado | n | taxa-base | AUC | precision | sinais |
|---|---|---|---|---|---|
| −1 (venda) | 410 | 0,4878 | 0,5283 | **1,0000** | **11** |
| +1 (compra) | 441 | 0,4218 | 0,5156 | 0,4062 | 96 |

Precision de 100% em 11 sinais é irrelevante estatisticamente (IC95% de Wilson: [0,74; 1,00]) e serve apenas para ilustrar o quanto números de precision são instáveis com poucos eventos. Este é exatamente o tipo de resultado que seria fácil apresentar como sucesso e que não sobrevive a mais dados.

---

## 11. Indicador NTSL (seções 27–29 e 42.5)

**Arquivo:** `ntsl/ReversalDetectorClaude.ntsl` — 743 linhas, gerado por `src/model_to_ntsl.py`.

### Como o CatBoost virou NTSL

O CatBoost usa árvores **oblívias** (simétricas): todos os nós de um nível testam a mesma condição. Uma árvore de profundidade *d* tem portanto apenas *d* comparações e 2^*d* folhas, e o índice da folha é um número binário de *d* bits:

```pascal
idx := 0;
if agrS[3] / rngSafe[3] > 3.586057662964 then idx := idx + 1;   // AggSellNorm_lag3
if agrB[3] / rngSafe[3] > 38.76025390625 then idx := idx + 2;   // AggBuyNorm_lag3
if totAgr / mTot > 0.971371650696 then idx := idx + 4;          // AggTotalRatio20
if idx = 0 then raw := raw - 0.050380474798
else if idx = 1 then raw := raw - 0.008877080174
...
```

Modelo exportado: 40 árvores × profundidade 3, deliberadamente pequeno para ser auditável a olho, como pede a seção 29.

### Duas decisões forçadas pela realidade do NTSL

**1. Sem `Trades`.** Foram levantadas as funções efetivamente usadas nos indicadores já compilados do usuário em `ProfitChart/Indicadores`. Existe `QuantityVol(false,false)` para contratos, mas **nenhuma função verificada devolve o número de negócios da barra**. Todas as features derivadas de `Trades` ficaram fora do modelo exportado (elas continuam na pesquisa — a pergunta da seção 40 inclui "número de negócios", e a resposta para elas foi a mesma: |*d*| < 0,10).

**2. Sem `Exp()`.** Nenhum indicador do repositório usa `Exp(`, então a sigmoide não foi inventada. Como ela é estritamente crescente:

```
prob ≥ T   ⟺   raw ≥ ln(T/(1−T))
```

O indicador compara o score bruto contra o logito do threshold (input `LimiarRaw`), o que dá **exatamente** o mesmo sinal sem depender de função não verificada. Também foram evitadas notação científica (`1e-05`) e a forma `raw + -0.5`, ambas de parsing duvidoso.

### Auditoria do indicador (seção 44.19)

Três camadas, todas exatas:

| verificação | resultado |
|---|---|
| aritmética de árvores reproduz `predict(RawFormulaVal)` do CatBoost | **max \|Δ\| = 0,0** em 851 barras |
| features recalculadas com a semântica do NTSL == features do pipeline | **max \|Δ\| = 0,0** |
| probabilidade NTSL == probabilidade pipeline | **max \|Δ\| = 0,0** |
| **sinais idênticos barra a barra** | **0 divergências** (41 vs 41) |
| não-repintura: corromper t+1.. altera algum sinal em t'≤t? | **0 mudanças** em 3 pontos de corte |

A camada de features foi escrita **de forma independente** de `features.py` (`export_ntsl.ntsl_recompute_features`), partindo de OHLC/agressão brutos com as mesmas operações que o indicador executa — não é uma tautologia.

### Desempenho do modelo exportado

| métrica | valor |
|---|---|
| AUC walk-forward (DEV) | 0,5145 |
| **AUC holdout** | **0,5164** |
| precision @ 0,50 | 0,5854 (24 TP / 41 sinais) |
| ganho sobre a taxa-base | +0,1318 |
| sinais | 41 (5,9/pregão) |
| deslocamento médio 12 barras | +45,1 pts |

**Este número aparentemente melhor não deve ser lido como sucesso.** A AUC do modelo exportado (0,5164) é indistinguível da do modelo de pesquisa (0,5158) — a qualidade de ordenação é a mesma. A diferença de precision vem só de o threshold cair num ponto diferente da distribuição, produzindo 41 sinais em vez de 107. Com 41 sinais, o IC95% da precision é ≈ [0,43; 0,74], que **contém a taxa-base de 0,4536**. Reportar 0,5854 como edge seria escolher, depois de ver o holdout, o corte mais favorável — exatamente o que a seção 34 proíbe. Ambos os modelos estão reportados aqui justamente para que essa escolha não seja feita em silêncio.

---

## 12. Convergência com investigação anterior

O arquivo `ProfitChart/Indicadores/Grafico-PI/PivoR11_Absorcao_Claude.ntsl`, no repositório do usuário, documenta um estudo independente sobre **esta mesma base** e chegou ao mesmo teto:

> *"Teto honesto do fluxo: logística regularizada com 97 features chega a 0,538 de AUC no teste. GBM decora (treino 0,78 / teste 0,53). Não há modelo grande a construir aqui."*

Dois caminhos metodológicos distintos, mesmo limite: **AUC ≈ 0,53–0,54, sem significância**. Isso reforça que o resultado é uma propriedade da base, não um artefato deste pipeline.

Aquele estudo obteve algum resultado operacional com um alvo **diferente** (150 pts / stop 100 pts, primeiro toque) e um evento **diferente** (pivô geométrico de 4 barras + absorção), não com o evento "2–3 candles + virada + continuação" desta investigação. Isso sugere que o caminho promissor não é melhorar o modelo, e sim **trocar a definição do evento** — ver seção 14.

---

## 13. Limitações

1. **Amostra curta.** 35 pregões, 20.000 bricks, e apenas ~4.300 eventos em `p2c2`. Um edge real de 2–3 pontos percentuais precisaria de ~5–10× mais dados para ser detectável. **Este estudo não prova que não existe edge; prova que, com esta amostra, não é possível demonstrar nenhum.**
2. **Holdout de 7 pregões.** 851 eventos dão IC95% de AUC com ±0,04 de largura. Insuficiente para separar 0,52 de 0,50.
3. **`BarDurationF` de semântica desconhecida.** Não corresponde a tempo de relógio (r = 0,001). Se a intenção era medir velocidade de formação, a coluna pode estar medindo outra coisa, e a família inteira de features temporais fica comprometida. **Vale confirmar o significado dessa coluna no ProfitChart.**
4. **Estrutura do candle degenerada.** Com o fechamento sempre no extremo do range, metade das features da seção 7 são identidades e não podiam ter ajudado.
5. **Um único ativo, um único tamanho de brick, um único regime de mercado** (julho–agosto de 2026).
6. **O NTSL não foi compilado no Profit.** A sintaxe foi restringida a construções verificadas nos indicadores já compilados do usuário, mas a compilação final não pôde ser executada aqui — é o único item da seção 29 pendente.
7. **Custos operacionais não modelados.** Dado que a expectativa bruta já é negativa nos sinais, incluir custos só pioraria.

---

## 14. Recomendações

**Não operar este indicador.** Não porque seja mal construído, mas porque a evidência diz que ele não seleciona nada.

Se a investigação continuar, em ordem de retorno esperado:

1. **Confirmar o que é `BarDurationF`.** É a única variável do conjunto cuja semântica não fecha com os dados. Se ela realmente mede velocidade de formação numa unidade diferente, a família temporal precisa ser refeita.
2. **Trocar o evento, não o modelo.** O padrão "2–3 candles + virada" tem taxa-base *idêntica* à probabilidade incondicional — ele não seleciona nada antes mesmo de qualquer feature entrar. Nenhum modelo conserta um evento que não é um evento. O estudo anterior do usuário obteve resultado com pivô geométrico + absorção, um evento diferente.
3. **Trocar o alvo.** "Continuação de 2–3 candles" é uma condição sobre a *sequência de cores*, não sobre dinheiro. Um alvo em pontos (atingir +X antes de −Y) é mais próximo do objetivo e tem menos ruído combinatório.
4. **Ampliar a amostra** para 6–12 meses antes de qualquer nova busca de modelo. Com 35 pregões, qualquer busca com dezenas de configurações encontra 0,53 por acaso — é literalmente o que o teste nulo mostrou.
5. **Manter o arcabouço.** O pipeline, os testes de vazamento e o exportador NTSL são reutilizáveis e estão validados. O que falta é dado e um evento melhor definido, não infraestrutura.

---

## 15. Critério de sucesso (seção 41) — avaliação item a item

| # | critério | veredito | evidência |
|---|---|---|---|
| 1 | melhora estatisticamente significativa sobre o baseline | **NÃO** | melhor p = 0,081 vs baseline; teste nulo p = 0,05 com máximo nulo (0,5368) acima do observado (0,5357) |
| 2 | estabilidade em walk-forward | **NÃO** | AUC por fold de 0,4878 a 0,5229; desvio 0,035 |
| 3 | estabilidade temporal | **NÃO** | julho 0,5438 · agosto 0,4403 |
| 4 | estabilidade entre direções | parcial | DEV +1 = 0,5391 / −1 = 0,5155; holdout 96 vs 11 sinais |
| 5 | ausência de look-ahead | **SIM** | teste de perturbação com controle positivo; 11 testes automatizados |
| 6 | quantidade operacionalmente útil de sinais | **SIM** | 5,9–15,3 sinais/pregão |
| 7 | precision suficiente | **NÃO** | +0,0137 sobre a taxa-base; IC contém a taxa-base |
| 8 | comportamento econômico plausível | **NÃO** | sinais −41,1 pts vs candidatos +2,2 pts |
| 9 | implementável sem repaint no NTSL | **SIM** | indicador gerado e auditado com 0 divergências |

**5 de 9 critérios falharam. O projeto não atinge o critério de sucesso da seção 41.**

---

## 16. Auditoria final obrigatória (seção 45)

| verificação | resposta | evidência |
|---|---|---|
| Features usam somente passado + candle atual? | **SIM** | `leakage_test.py`: 120 features × 5 cortes, 0 divergências, com controle positivo detectando vazamento injetado |
| Target usa futuro somente na fase de treinamento? | **SIM** | `targets.py` é o único módulo com `shift(-k)`; prefixos `y_`/`fwd_` barram target virar feature; teste `test_only_whitelisted_modules_use_future` |
| Nenhum scaler foi ajustado usando teste? | **SIM** | scaler/imputer dentro do `Pipeline` sklearn, ajustados por fold; CatBoost não usa scaler |
| Nenhum split aleatório foi utilizado? | **SIM** | teste `test_no_shuffling_anywhere` proíbe `shuffle=True` e `train_test_split` no código-fonte |
| Existe embargo temporal? | **SIM** | 3 barras (= horizonte máximo do target), parametrizável em `config.EMBARGO_BARS`; testado |
| Walk-forward foi realizado? | **SIM** | 6 folds expansivos; testado que o treino só cresce e não há sobreposição |
| Baseline foi comparado? | **SIM** | `EXP000_ALWAYS_SIGNAL` + 5 grupos de informação × 2 modelos, em 4 targets |
| CatBoost foi comparado fora da amostra? | **SIM** | vs logística, árvore e Random Forest, em walk-forward e no holdout |
| Feature importance é estável? | **NÃO** | nenhuma feature comum às 4 configurações testadas |
| Threshold foi escolhido sem usar o teste final? | **SIM** | escolhido nas predições out-of-fold de DEV |
| O teste final é realmente out-of-sample? | **SIM** | últimos 20% das barras, com embargo, avaliados uma vez |
| O modelo foi convertido para NTSL? | **SIM** | `ntsl/ReversalDetectorClaude.ntsl`, 40 árvores, 743 linhas |
| O NTSL usa somente dados até a barra atual? | **SIM** | todos os índices ≥ 0; teste de perturbação do futuro: 0 sinais alterados |
| O sinal aparece no fechamento da barra de virada? | **SIM** | `PlotText` na barra corrente, sem deslocamento |
| O NTSL não espera t+1? | **SIM** | nenhuma barra de confirmação na regra |
| O NTSL não repinta? | **SIM** | barra fechada nunca muda de sinal (ressalva sobre a barra *em formação* documentada no cabeçalho do indicador) |
| O NTSL foi comparado com as previsões Python? | **SIM** | 0 divergências em 851 barras; max \|Δ\| de probabilidade = 0,0 |

**Dois itens não são "SIM": a estabilidade da importância das features e — pela seção 29 — a compilação no Profit, que não pôde ser executada neste ambiente.** O primeiro é um resultado da pesquisa, não uma falha de execução, e é justamente parte da conclusão negativa. O segundo é o único passo pendente de verificação externa.

---

## 17. Entregáveis

| item | caminho |
|---|---|
| Relatório | `reports/final_report.md` (este arquivo) |
| Relatórios por etapa | `reports/01_data_validation.md` … `reports/09_robustness_p2c2.md` |
| Modelo de pesquisa | `models/catboost_p2c2.cbm` |
| Modelo exportável | `models/catboost_ntsl_export.cbm` |
| Dataset processado | `data/processed/dataset.parquet` (20.000 × 158) |
| Manifesto do dataset | `results/03_dataset_manifest.json` |
| Predições out-of-sample | `results/08_predictions_p2c2.csv` (`timestamp, prediction, probability, target, fold`) |
| Indicador NTSL | `ntsl/ReversalDetectorClaude.ntsl` |
| Auditoria do NTSL | `results/12_ntsl_export_audit.json` |
| Testes automatizados | `tests/test_no_lookahead.py` (11 testes, todos passam) |
| Figuras | `reports/figures/*.png` |

### Reprodutibilidade

```bash
cd src
python run_pipeline.py              # pipeline completo
python run_pipeline.py --skip-slow  # sem grid search nem teste nulo
python -m pytest ../tests -q        # testes de vazamento
```

Ambiente: Python 3.14.4 · pandas 3.0.3 · numpy 2.4.6 · scikit-learn 1.9.0 · catboost 1.2.10 · shap 0.52.0. Seed 42 fixa. Configuração completa em `src/config.py`; log de execução em `results/00_pipeline_run.json`.
