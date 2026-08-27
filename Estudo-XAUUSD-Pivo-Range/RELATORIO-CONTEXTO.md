# Relatório II — S/R, VWAP e contexto

Segunda rodada da investigação. Objetivo: verificar se o **contexto** — níveis de
suporte/resistência do `SR-metatrader5` e VWAP ponderado pela agressão — separa os
sinais bons dos ruins, e qual dos dois padrões tem mais sucesso.

**Conclusão: não separa.** O contexto produz efeitos fortes e consistentes em TRAIN e
VAL que desaparecem por completo no período reservado. A melhor regra encontrada
entrega 37,76% no desenvolvimento e **29,15%** no teste.

---

## 1. Como os níveis foram calculados

Reusei o motor do `SR-metatrader5` (Renko → giros → clustering → score), com os
parâmetros já calibrados em `XAUUSD.ps1`:

```
box = 1640 ticks = 16,40 USD (~5 range bars)   metodo = dbscan   min_eventos = 2
sep = 4,00   faixa = ±800   vao_max = 15,00   top = 50
```

### Causalidade

O ponto crítico. O `main.py` calcula níveis sobre uma janela fixa de histórico — usar
isso num backtest seria look-ahead puro. A solução aproveita uma propriedade do motor:

> **O Renko é uma construção incremental.** O tijolo `i` depende apenas de barras
> `<= pos[i]`, e a lista é append-only.

Então construí o Renko **uma vez** sobre todo o histórico (1.137 tijolos) e, a cada
virada de dia de pregão, fatiei os tijolos até aquele instante e rodei
eventos → clustering → score somente sobre o passado. Um sinal na barra `t` só enxerga
o snapshot cuja âncora é anterior a `t`.

- 115 snapshots (após aquecimento de 15.000 barras)
- mediana de 48 níveis por snapshot
- `maior_cluster` entre 0,04 e 0,13 — sem encadeamento de DBSCAN

### Duas variantes

| variante | preço do nível | espaçamento mediano |
|---|---|---|
| `renko` (padrão do motor) | fechamento do tijolo do giro | **exatamente 16,40** |
| `extreme` | ponta do pavio, preço real do giro | 16,27 |

A variante padrão coloca todos os níveis sobre a grade de 16,40 — os preços são
múltiplos exatos da caixa. Isso importa para a interpretação (§4). Usei as duas em
paralelo; os resultados são indistinguíveis.

---

## 2. VWAP

Volume = `TICKVOL + VOL` (agressão de compra + agressão de venda), conforme pedido.

- Preço típico `(H+L+C)/3`, acumulado dentro da sessão.
- Sessão = trecho entre gaps temporais maiores que 1h → **150 sessões**, mediana de
  592 barras cada.
- Bandas a partir do desvio-padrão ponderado por volume: **σ mediano = 15,06 USD = 4,61 R**.

Features derivadas: distância ao VWAP em R e em σ, se o trade aponta para o VWAP ou se
afasta dele, inclinação do VWAP nas últimas 20 barras, posição na sessão, distância aos
extremos da sessão, e distância a números redondos de 10 e 50.

Total: **34 features de contexto**, todas causais.

---

## 3. Qual padrão tem mais sucesso

Resposta direta: **estatisticamente empatados.**

| | n | acerto | TRAIN | VAL | TEST |
|---|---:|---:|---:|---:|---:|
| Padrão 1 | 7.119 | 31,32% | 31,29% | 31,84% | 31,01% |
| Padrão 2 | 6.894 | 31,10% | 31,37% | 31,36% | 30,45% |

Fisher exato: OR = 1,011, **p = 0,78**. Os dois trocam de lugar entre períodos.

No contexto mais favorável (reversão sobre um nível, distância ≤ 0,5R) a suposta
diferença entre eles também troca de sinal:

| | TRAIN | VAL | TEST |
|---|---:|---:|---:|
| Padrão 1 | 35,15% (n=239) | 33,23% (n=313) | 32,42% (n=330) |
| Padrão 2 | 32,47% (n=231) | **38,52%** (n=244) | **29,28%** (n=345) |

P2 é o melhor na validação e o pior no teste, com amostras equivalentes. Isso é ruído.

---

## 4. O que pareceu funcionar — e por que não funciona

### 4.1 `room_R` — espaço livre até o alvo

A hipótese com melhor lógica econômica de toda a investigação: se existe uma
resistência a 1,5R de distância, o preço trava lá e o alvo de 3R não é atingido. Foi a
feature de contexto mais forte no treino (ρ = +0,030, p = 0,034 bruto).

**Controle decisivo:** substituí os níveis reais por uma **grade falsa** com o mesmo
espaçamento e deslocamento aleatório, 12 seeds.

```
grade FALSA (12 seeds):  [room>=3R] - [room<2R] = +0,0046 ± 0,0146
niveis REAIS          :                          = +0,0084
z do efeito real contra a grade falsa            = +0,26
```

Uma grade arbitrária produz o mesmo efeito. `room_R` estava medindo posição dentro de
uma grade de 16,40, não estrutura de mercado. Os decis confirmam — a relação não é
monotônica (0,320 → 0,302 → 0,331 → 0,302 → 0,330).

Fora da amostra a regra inverte: TRAIN 32,69%, VAL 31,61%, **TEST 29,94%**.

### 4.2 Stop no nível em vez de 1,3R fixo

Ideia: numa reversão de alta sobre um suporte, o stop natural fica logo abaixo do
nível — normalmente mais perto que 1,3R. Um stop mais curto derruba o breakeven de
30,23% para ~28,9%.

Restringindo aos 4.995 eventos (35,6%) com stop de nível utilizável entre 0,6R e 1,6R:

| cenário | n | acerto | stop médio | breakeven | exp. (R) | margem |
|---|---:|---:|---:|---:|---:|---:|
| A) 3R / 1,3R fixo | 4.995 | 32,83% | 1,300 R | 30,23% | +0,112 | **+0,0260** |
| B) 3R / 1,1R fixo | 4.995 | 28,97% | 1,100 R | 26,83% | +0,088 | +0,0214 |
| C) 3R / stop no nível | 4.995 | 31,49% | 1,219 R | 28,90% | +0,109 | **+0,0259** |
| D) controle: distâncias permutadas (15 seeds) | 4.995 | 31,22% | — | — | +0,098 ± 0,005 | +0,0232 ± 0,0012 |

O cenário C bate o controle permutado com **z = +2,30** — a posição do nível carrega
alguma informação além da mera distribuição de distâncias. Mas C **empata com A**
(+0,0259 contra +0,0260): o stop derivado do nível apenas recupera o que o 1,3R fixo já
entregava. A geometria não adiciona nada.

O que sobra de A nesse subconjunto (32,83% contra 31,22% do total) é **efeito de
seleção**, não de geometria — e é isso que a seção seguinte testa.

### 4.3 Proximidade do nível — o efeito que quebra no tempo

| distância ≤ | TRAIN | VAL | **TEST** |
|---|---:|---:|---:|
| 0,25 R | 37,99% (n=229) | 36,29% (n=259) | **29,47%** (n=319) |
| 0,50 R | 33,83% (n=470) | 35,55% (n=557) | **30,81%** (n=675) |
| 0,75 R | 33,70% (n=721) | 33,49% (n=842) | **30,74%** (n=1.041) |
| 1,00 R | 33,40% (n=967) | 33,00% (n=1.088) | **30,92%** (n=1.410) |
| 1,50 R | 33,79% (n=1.462) | 33,04% (n=1.601) | **31,83%** (n=2.130) |
| 2,00 R | 33,49% (n=1.953) | 32,43% (n=2.143) | **31,76%** (n=2.824) |

O padrão é inequívoco: **em todos os seis limiares, TRAIN e VAL ficam entre 32,4% e
38,0%, e o TEST fica entre 29,5% e 31,8%.** E o efeito é mais forte justamente onde a
amostra é menor. Não é um filtro — é uma quebra de regime entre os primeiros 70% e os
últimos 30% da base.

Referência: breakeven com custo de 0,05 R = **31,40%**.

---

## 5. Machine Learning com o contexto

CatBoost, walk-forward com 5 folds e embargo de 100 barras.

| grupo | conjunto de features | AUC OOF | Brier | Brier constante |
|---|---|---:|---:|---:|
| P1+P2 | base (57) | 0,5062 | 0,2153 | 0,2147 |
| P1+P2 | só contexto (34) | 0,5098 | 0,2162 | 0,2147 |
| P1+P2 | base + contexto (91) | **0,5101** | 0,2153 | 0,2147 |
| P1 | base + contexto | 0,5097 | 0,2173 | 0,2161 |
| P2 | base + contexto | **0,5175** | 0,2149 | 0,2135 |

Teste final no período reservado:

| conjunto | AUC | PR-AUC | Brier | Brier constante |
|---|---:|---:|---:|---:|
| base | 0,4908 | 0,3104 | 0,2144 | 0,2129 |
| só contexto | **0,5051** | 0,3071 | 0,2140 | 0,2129 |
| base + contexto | 0,5037 | 0,3168 | 0,2138 | 0,2129 |

O contexto tira a AUC de 0,4908 para 0,5051 — ou seja, de "abaixo do acaso" para "o
acaso". O Brier continua praticamente igual ao do preditor constante.

As features de contexto **dominam** a importância do modelo final (7 das 12 primeiras:
`vwap_z_aligned`, `sess_pos_aligned`, `round50_R`, `ren_behind_R`, `ren_room_R`,
`ext_room_R`, `vwap_slope_aligned`) — o modelo se apoia nelas e mesmo assim não prevê
nada. Importância alta sem poder preditivo é exatamente o que se espera de features
ricas em variância e pobres em sinal.

---

## 6. Teste de tiro único

Para evitar mais um ciclo de garimpo, escolhi a melhor regra usando **apenas TRAIN+VAL**
e a avaliei **uma única vez** no período reservado.

Candidatas no desenvolvimento (TRAIN+VAL):

| regra | n | acerto |
|---|---:|---:|
| nível tocado (≤ 0,5R) | 1.027 | 34,76% |
| **nível tocado & extremo de sessão** | **339** | **37,76%** |
| nível tocado & P1 | 552 | 34,06% |
| nível tocado & room ≥ 3R | 601 | 35,44% |
| extremo de sessão a favor | 3.163 | 33,04% |
| perfurou nível & extremo de sessão | 1.251 | 35,41% |

Resultado no teste:

```
regra escolhida: "nivel tocado & extremo de sessao"   (DEV: 37,76%)

  >>> TESTE  n=247   acerto=29,15%   exp=-0,0466 R
      binom p (> breakeven)             = 0,667
      binom p (> breakeven com custo)   = 0,796
      IC95 em blocos = [23,89% ; 34,82%]
      P(> breakeven) = 0,380     P(> breakeven com custo) = 0,225
```

Uma regra de 37,76% no desenvolvimento entrega **29,15%** no teste — abaixo do baseline
de 30,8% e abaixo do breakeven simples.

---

## 7. Controle de múltiplos testes

Hipóteses avaliadas nesta rodada:

| bloco | contagem |
|---|---:|
| 27 features de contexto × 3 grupos (univariada) | 81 |
| 12 cortes de contexto × 2 direções | 24 |
| 6 limiares de proximidade × 3 períodos | 18 |
| 8 regras combinadas × 3 períodos | 24 |
| 3 conjuntos de features × 3 grupos (ML) | 9 |
| **total** | **~156** |

A 5% de significância, cerca de **8 falsos positivos são esperados por puro acaso**.
Nenhuma feature de contexto sobreviveu à correção de Benjamini-Hochberg em nenhum dos
três grupos (0 de 27 × 3).

Também verifiquei explicitamente se a **direção se inverte** em algum contexto — se em
resistência a reversão de alta seria uma armadilha e o fade venceria. Em todos os 12
contextos testados a reversão bate o fade, com diferenças de −0,004 a −0,053. Não há
inversão.

---

## 8. Veredicto da segunda rodada

> Níveis de suporte/resistência calculados causalmente com o motor do `SR-metatrader5`
> e VWAP ponderado pela agressão total **não separam** os sinais bons dos ruins.
>
> A feature com melhor lógica econômica (`room_R`, espaço livre até o alvo) reproduz-se
> integralmente com uma grade de preços falsa (z = +0,26) e inverte fora da amostra.
> O stop ancorado no nível bate o controle permutado (z = +2,30) mas empata com o stop
> fixo de 1,3R, sem ganho líquido. A proximidade do nível produz 33–38% em TRAIN e VAL
> e 29–32% no período reservado, em todos os seis limiares testados — o comportamento
> de uma quebra de regime, não de um filtro.
>
> Modelos com as 91 features atingem AUC de 0,504 no período reservado. A melhor regra
> selecionada no desenvolvimento entrega 29,15% no teste contra 37,76% no
> desenvolvimento.
>
> **Os dois padrões continuam estatisticamente empatados entre si (p = 0,78) e nenhum
> deles supera o baseline.** A segunda rodada não alterou a conclusão da primeira.

### O que eu tentaria a seguir

O contexto de preço foi testado e não é o que falta. As duas hipóteses vivas continuam
sendo as da primeira rodada, e nesta ordem:

1. **Order flow real.** `corr(TICKVOL, VOL) = 0,992` — as duas séries provavelmente são
   proxies do mesmo agregado, não um delta de fluxo. Delta por nível de preço e
   imbalance de book são informação que esta base simplesmente não contém.
2. **Ranges maiores.** Em 3,27 USD o ruído de microestrutura domina. O σ do VWAP é
   4,61 R — o preço oscila mais de quatro ranges dentro da própria banda, o que sugere
   que o range escolhido é pequeno demais para a estrutura que se quer capturar.

---

### Reprodução

```
python src/20_sr_levels.py renko      # snapshots causais de niveis (variante padrao)
python src/20_sr_levels.py extreme    # variante com preco real do giro
python src/21_context.py              # VWAP + 34 features de contexto
python src/22_explore.py              # varredura univariada no TRAIN
python src/23_room.py                 # room_R + controle de grade falsa
python src/24_ml_ctx.py               # walk-forward com contexto
python src/25_geom.py                 # stop no nivel + controle permutado
python src/26_final.py                # teste de tiro unico
```
