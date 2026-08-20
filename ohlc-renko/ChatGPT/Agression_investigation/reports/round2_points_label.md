# Rodada 2 — alvo em PONTOS e relações t vs t−1

**Mudanças pedidas:**
1. adicionar explicitamente as relações `t > t-1` e `t < t-1` para **todas** as features normalizadas;
2. trocar o rótulo para **pontos**: atingir +100 pontos antes de tocar o extremo oposto do candle de virada.

Rodada 1 (rótulo de sequência de cores) está em `final_report.md` e continua válida como registro. Esta rodada não a sobrescreve.

---

## 1. O novo rótulo

```
entrada  = Close[t] do brick de virada, na direção dele
alvo     = Close[t] ± 100 pontos
stop     = extremo oposto do PRÓPRIO brick de virada
           (Low[t] numa virada de alta, High[t] numa de baixa)
sucesso  = alvo tocado ANTES do stop
```

Como o fechamento fica sempre no extremo do range neste export, **a distância até o stop é exatamente `Range[t]`**. O risco portanto varia por evento e o prêmio é fixo:

| | `pts100p2` | `pts100p3` |
|---|---|---|
| candidatos rotulados | 4.342 (124,1/pregão) | 2.897 (82,8/pregão) |
| **taxa-base** | **0,5762** | **0,5989** |
| desfecho alvo / stop | 2.502 / 1.840 | 1.735 / 1.162 |
| barras até resolver (mediana / p90 / máx) | 2 / 4 / **42** | 2 / 4 / 12 |
| risco (mediana / mín / máx) | 125 / 105 / 150 pts | idem |
| **ambíguos** (toca alvo e stop na mesma barra) | **0** | **0** |
| taxa-base up / down | 0,5850 / 0,5676 | 0,6187 / 0,5795 |
| **expectativa em R** | **+0,0377** | **+0,0798** |

Três observações de método:

- **Zero eventos ambíguos.** A convenção pessimista (empate = stop) nunca precisou ser aplicada, então o resultado não depende dela.
- **O embargo teve de crescer de 3 para 50 barras.** Um evento leva até 42 bricks para resolver; manter o embargo antigo faria treino e validação compartilharem eventos. `EMBARGO_BARS_POINTS = 50`.
- **R = 100/125 ≈ 0,8.** Com taxa-base 0,576 a expectativa bruta é `0,576×0,8 − 0,424×1 = +0,037 R ≈ +4,7 pontos por trade`, **antes de custos**.

Este rótulo é melhor que o da rodada 1 em todos os aspectos: taxa-base acima de 50%, resolução rápida, sem ambiguidade e — ao contrário do rótulo de cores — corresponde a uma operação real.

---

## 2. As novas features

Para cada uma das **25 features normalizadas** foram criadas:

```
X_gt_prev   = 1 se X[t] >  X[t-1]
X_lt_prev   = 1 se X[t] <  X[t-1]
X_chg1      = X[t] - X[t-1]
X_ratio1    = X[t] / X[t-1]      (apenas para X que nunca troca de sinal)
```

`gt` e `lt` **não** são complementares — ambos são 0 no empate, o que é frequente em barras de agressão zero. Para `AggBalanceNorm`, `WickAsym`, `AggImbalance` e `LogDurationResidual20` a razão foi omitida: dividir por número negativo inverte a ordem e explode perto de zero.

Total: **96 novas colunas**, dataset de 222 features. `src/features.py::add_prev_comparisons`.

---

## 3. A hipótese, isolada

> *"quando `(AggBuy+AggSell)/(High−Low)` é maior no brick de virada do que no anterior, tende a dar bons resultados"*

Testada como regra pura sobre os candidatos, apenas em DESENVOLVIMENTO:

| regra | n | precision | IC95 Wilson | taxa-base | **edge** | expect. R |
|---|---|---|---|---|---|---|
| **`AggTotalNorm[t] > [t-1]`** (`pts100p2`) | 1.955 | 0,5719 | [0,5498; 0,5936] | 0,5758 | **−0,0039** | +0,0157 |
| **`AggTotalNorm[t] > [t-1]`** (`pts100p3`) | 1.284 | 0,5888 | [0,5616; 0,6154] | 0,6026 | **−0,0138** | +0,0472 |
| `AggTotalNorm[t] < [t-1]` (`pts100p2`) | 1.520 | 0,5829 | [0,5579; 0,6074] | 0,5758 | +0,0071 | +0,0683 |
| `AggTotalNorm[t] < [t-1]` (`pts100p3`) | 1.035 | 0,6193 | [0,5894; 0,6484] | 0,6026 | +0,0167 | **+0,1343** |

**A hipótese não se confirma.** O edge é ligeiramente **negativo** nos dois alvos, e o IC95 contém a taxa-base. O controle — a relação **inversa** — é consistentemente positivo, embora também sem significância.

Dentro de cada direção, que é onde a comparação é limpa:

| regra | UP | DOWN |
|---|---|---|
| `AggTotalNorm >` (`p2`) | edge −0,0094 | edge +0,0017 |
| `AggTotalNorm >` (`p3`) | edge −0,0186 | edge −0,0087 |
| `AggTotalNorm <` (`p2`) | edge +0,0145 | edge −0,0010 |
| `AggTotalNorm <` (`p3`) | edge +0,0224 | edge +0,0102 |

Nenhum IC95 exclui a taxa-base da própria direção. A leitura honesta: **a relação existe no sinal que você descreveu, mas com o sentido invertido e magnitude dentro do ruído.**

---

## 4. Varredura das 138 regras — e a armadilha que ela revelou

Varrendo todas as comparações `t` vs `t−1`:

| | `pts100p2` | `pts100p3` |
|---|---|---|
| regras testadas (n ≥ 100) | 138 | 138 |
| regras cujo IC95 fica acima da taxa-base | 9 | 16 |
| esperadas por acaso a 95% | 6,9 | 6,9 |

Sete regras sobrevivem nos **dois** alvos:

| regra | edge `p2` | edge `p3` |
|---|---|---|
| `UpperWickNorm_lt_prev` | +0,0395 | +0,0347 |
| `BuyShare_ratio1 > mediana` | +0,0331 | +0,0345 |
| `SellShare_lt_prev` | +0,0307 | +0,0297 |
| `SellShare_ratio1 < mediana` | +0,0297 | +0,0311 |
| `AggImbalance_gt_prev` | +0,0260 | +0,0313 |
| `AggBalanceNorm_gt_prev` | +0,0253 | +0,0337 |
| `SellShare_chg1 < mediana` | +0,0251 | +0,0328 |

Parece forte. **Não é.** Duas razões:

**(a) São uma regra só.** `BuyShare + SellShare ≡ 1` e `AggImbalance ≡ 2·BuyShare − 1`. "BuyShare sobe", "SellShare cai" e "imbalance sobe" são a mesma afirmação escrita de três jeitos.

**(b) São um seletor de direção disfarçado.** Verificando quantos dos eventos selecionados são viradas de alta:

| regra | n | % viradas de ALTA |
|---|---|---|
| `UpperWickNorm_lt_prev` | 1.310 | **100,0%** |
| `SellShare_lt_prev` | 1.652 | 99,2% |
| `AggImbalance_gt_prev` | 1.685 | 97,7% |
| `AggBalanceNorm_gt_prev` | 1.692 | 97,5% |
| `BuyShare_gt_prev` | 1.706 | 96,8% |

`UpperWickNorm_lt_prev` é **exatamente** o indicador de virada de alta: num brick de alta o pavio superior é identicamente 0 (o fechamento é a máxima), então ele é sempre menor que o do brick de baixa anterior.

E as viradas de alta têm taxa-base maior: **0,5947 contra 0,5576** das de baixa, num universo cuja base agregada é 0,5758. Selecionar só altas rende ~+0,019 de edge sem nenhuma informação — que é praticamente todo o edge medido.

Dentro da direção, o que sobra:

| regra | UP: edge vs base da direção | DOWN |
|---|---|---|
| `UpperWickNorm_lt_prev` | +0,0205 | *não existe* |
| `AggImbalance_gt_prev` | +0,0118 | n=38, insuficiente |
| `BuyShare_gt_prev` | +0,0100 | n=54, edge −0,1317 |

**Nenhuma regra, uma vez controlada a direção, bate a taxa-base da própria direção com IC95.**

### A versão direcionalmente simétrica

A formulação correta da sua intuição — "a parcela de agressão do lado da NOVA direção está subindo" (BuyShare numa virada de alta, SellShare numa de baixa) — também foi construída e testada:

| | UP | DOWN |
|---|---|---|
| `pts100p2` | edge +0,0100 | edge +0,0042 |
| `pts100p3` | edge −0,0019 | edge −0,0012 |

Zero, e troca de sinal entre os alvos.

---

## 5. Modelo com o novo rótulo e as novas features

Walk-forward em DEV, embargo de 50 barras:

| feature set | modelo | n feat | AUC | IC95 | precision | base | folds>0,5 |
|---|---|---|---|---|---|---|---|
| **EXTENDED+PREVCMP** | **CatBoost** | 193 | **0,5428** | [0,519; 0,566] | 0,5767 | 0,5696 | **6/6** |
| EXTENDED+PREVCMP | Logística | 193 | 0,5413 | [0,517; 0,567] | 0,5903 | 0,5696 | **6/6** |
| EXTENDED | Logística | 97 | 0,5374 | [0,512; 0,561] | 0,5835 | 0,5696 | 5/6 |
| BASE | CatBoost | 42 | 0,5357 | [0,512; 0,561] | 0,5695 | 0,5696 | 6/6 |
| PREVCMP (só as novas) | Logística | 96 | 0,5332 | [0,509; 0,556] | 0,5860 | 0,5696 | 5/6 |
| STRUCT+VOL | Logística | 28 | 0,5306 | [0,506; 0,555] | 0,5798 | 0,5696 | 5/6 |
| PREVCMP | CatBoost | 96 | 0,5110 | [0,488; 0,535] | 0,5700 | 0,5696 | 4/6 |

As features novas ajudam: `EXTENDED+PREVCMP` supera `EXTENDED` sozinho e é o único conjunto com 6/6 folds nos dois modelos.

### O edge sobrevive dentro da direção — em DEV

| | n | taxa-base | AUC | IC95 |
|---|---|---|---|---|
| agrupado | 2.240 | 0,5696 | 0,5428 | — |
| **só UP** | 1.094 | 0,5841 | **0,5467** | [0,5132; 0,5831] |
| **só DOWN** | 1.146 | 0,5558 | **0,5361** | [0,5008; 0,5695] |
| *usando apenas o lado como score* | — | — | *0,5144* | — |

Correlação entre a probabilidade do modelo e o lado: apenas 0,12. **Desta vez o edge não é confundimento de direção** — ambos os ICs excluem 0,5.

### Teste nulo em DEV: passa

| | valor |
|---|---|
| melhor AUC observado | **0,5428** |
| melhor AUC sob H₀ — média | 0,5158 |
| melhor AUC sob H₀ — máximo em 20 permutações | 0,5368 |
| **p-valor** | **0,00** (0 de 20) |

Ao contrário da rodada 1 (p = 0,05, com o máximo nulo *acima* do observado), aqui **nenhuma** permutação alcançou o valor observado. A estrutura em DEV é estatisticamente real.

---

## 6. O teste final — e onde tudo se desfaz

Threshold escolhido **só em DEV** (0,65; precision 0,7407 em DEV, 2,8 sinais/pregão). Holdout de 7 pregões, avaliado uma vez:

| métrica | DEV | **HOLDOUT** |
|---|---|---|
| AUC | 0,5428 | **0,4775** |
| IC95 da AUC | [0,519; 0,566] | **[0,4403; 0,5161]** |
| AUC só UP | 0,5467 | **0,5029** |
| AUC só DOWN | 0,5361 | **0,4674** |
| taxa-base | 0,5696 | 0,5798 |
| precision no threshold | 0,7407 | 0,6038 |
| edge | +0,171 | +0,0240 |
| sinais | 2,8/pregão | 7,6/pregão |

Economia no holdout:

| | sinais do modelo (n=53) | todos os candidatos (n=840) |
|---|---|---|
| expectativa em R | **+0,0485** | **+0,0432** |
| pontos por trade (risco mediano 125) | **+6,1** | **+5,4** |

**A AUC out-of-sample fica abaixo de 0,5**, e a vantagem econômica do filtro sobre não filtrar é de 0,7 ponto por trade — ruído.

Por direção no holdout: UP precision 0,5152 em 33 sinais (expect. **−0,0899 R**); DOWN precision 0,7500 em 20 sinais (expect. +0,2770 R). Vinte sinais não sustentam conclusão nenhuma, e a AUC de 0,4674 desse mesmo lado mostra que a ordenação está invertida — a precisão alta é onde o corte caiu, não capacidade de ordenar.

---

## 7. Conclusão da rodada 2

O quadro mudou de "ruído" para algo mais específico e mais interessante:

1. **A hipótese, como enunciada, não se confirma.** `AggTotalNorm[t] > AggTotalNorm[t-1]` tem edge ligeiramente negativo nos dois alvos e nas duas direções. O sentido inverso é levemente positivo, sem significância.
2. **O que parecia funcionar na varredura era confundimento de direção.** Sete regras "vencedoras" eram uma só, e essa uma era um seletor de viradas de alta.
3. **O novo rótulo é muito melhor** — taxa-base 57,6%, resolução em 2 barras, zero ambiguidade, expectativa bruta positiva (+4,7 a +5,4 pts/trade) só por tomar todos os candidatos.
4. **As novas features t vs t−1 têm valor real em DEV.** `EXTENDED+PREVCMP` chega a AUC 0,5428 com 6/6 folds, sobrevive dentro de cada direção e **passa no teste nulo (p = 0,00)** — coisa que nada na rodada 1 conseguiu.
5. **Mas não generaliza.** No holdout a AUC cai para 0,4775 e as duas direções vão a 0,50 e 0,47.

O ponto (4) combinado com o (5) é o achado central desta rodada: **a estrutura em julho é real e some em agosto.** Isso é deriva de regime, não ruído puro — e é coerente com a rodada 1, onde o corte por mês já dava AUC 0,544 em julho contra 0,440 em agosto.

Isso muda a natureza do problema. Não é "não há sinal"; é **"o sinal não é estacionário na escala de semanas"**. Um modelo treinado uma vez e congelado — que é o que um indicador NTSL é — não sobrevive a isso.

## 8. O que fazer com isso

- **O ganho maior não está no filtro, está no rótulo.** Tomar todos os candidatos rende +5,4 pts/trade brutos no holdout. Com 124 candidatos/pregão isso é volume alto e margem fina: custos de 10–25 pts por trade (a faixa que o seu estudo anterior mediu) matam a operação. A pergunta útil passa a ser **como reduzir custo ou aumentar o alvo**, não como filtrar melhor.
- **Testar re-treino deslizante.** Se o sinal dura semanas, um modelo re-treinado a cada N pregões pode capturá-lo onde um modelo fixo falha. É o teste natural a partir daqui, e é barato.
- **Mais dados antes de qualquer conclusão definitiva.** 35 pregões dão um único DEV e um único holdout. A afirmação "julho sim, agosto não" precisa de mais meses para virar "não é estacionário" em vez de "esses 7 pregões foram atípicos".
- **Não regenerar o indicador NTSL com este modelo.** A AUC out-of-sample está abaixo de 0,5.

## 9. Correção da rodada 1 — `BarDurationF`

Você informou que a coluna é **minutos × 1000**. Confere exatamente: a barra de 24/07 18:31 tem `Duration = 3.752.167`; ×0,06 = **225.130 s**, e o intervalo medido até a barra seguinte foi **225.130,18 s** — o fim de semana, com erro de 0,16 s.

Portanto:
- a seção 2.5 do `final_report.md` está **errada** ao dizer que a coluna não é tempo de relógio; o `r = 0,001` foi destruído pelos valores de fim de pregão;
- os valores gigantes são **legítimos**: a última barra de cada pregão só fecha quando o pregão seguinte se move;
- **nenhum resultado de modelo muda** — a unidade é um multiplicador constante e divisões de árvore são invariantes a escala;
- `DurationSec = BarDurationF × 0,06` e a constante `DURATION_TO_SECONDS` foram adicionadas ao código.
