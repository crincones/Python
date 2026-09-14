# Resultados — Estratégia do Ajuste (WINFUT)

Base: WIN$N M1, **2021-08-23 a 2026-08-21**, 1248 pregões no arquivo,
**1205 válidos** ([ESTRATEGIA.md](ESTRATEGIA.md) §2.2). Resultados **brutos**,
sem custos. **Lote de 6 contratos**: pontos por contrato, R$ do lote inteiro
(R$ 0,20 por ponto por contrato).

Rodada com o spec revisado: parcial de 2/3 (4 de 6 contratos) em +45 com **o
stop do restante no preço médio da operação** (−90 da entrada, onde o total
zera), **alvo de 500 pontos fixos em todos os setups** (ESTRATEGIA.md §5),
regime exclusivo ao cruzar o ajuste, validação do ajuste contra o call de
fechamento e a premissa das médias de 21. A parcial de 50% (3 de 6) roda em
paralelo.

---

## 1. Resumo executivo

**Nenhum setup tem borda.** E a rodada produziu um achado metodológico maior que
qualquer um dos resultados.

| Setup | Trades | Pontos | R$ (lote de 6) | Ganham | Zeram | PF | Drawdown |
|---|---:|---:|---:|---:|---:|---:|---:|
| A — retorno à abertura | 1 189 | −49 433 | −59 320 | 13,5% | 18,5% | 0,39 | −49 530 |
| B — trade seco no ajuste | 894 | −53 230 | −63 876 | 7,4% | 18,8% | 0,19 | −53 427 |
| **C — pivôs** | 1 368 | **−11 908** | −14 289 | 15,9% | 45,2% | 0,78 | −12 484 |
| D — bolas | 726 | −16 252 | −19 502 | 12,7% | 41,2% | 0,51 | −16 252 |
| **CD — pivôs + bolas** | 1 361 | **−21 107** | −25 328 | 15,1% | 41,2% | 0,64 | −21 570 |

"Zeram" são os trades que fazem a parcial e depois voltam ao médio: fecham em
exatamente 0. No setup C, **74% dos trades que fazem a parcial terminam assim**
(618 de 836); 24% chegam ao alvo de 500. A parcial transforma parte dos stops em
zero a zero — e paga por isso vendendo 2/3 de todo alvo a +45: um alvo cheio
rende 196,7 pts em vez de 500.

---

## 2. O achado desta rodada: a parcial de +45 torna o backtest indecidível

A saída parcial em +45 pontos é pequena demais para uma base de 1 minuto
resolver. Dependendo de uma única convenção sobre a barra de entrada, o setup C
vai de −11 908 a +42 982 pontos:

| Convenção da barra de entrada | A | B | **C** | D | **CD** |
|---|---:|---:|---:|---:|---:|
| **Conservadora** — a barra do toque só resolve o stop | −49 433 | −53 230 | **−11 908** | −16 252 | **−21 107** |
| Creditando a barra de entrada | −33 037 | −49 130 | **+20 459** | −433 | **+11 188** |
| Teto absoluto (+ alvo ganha empate) | +2 843 | −18 254 | **+42 982** | +22 063 | **+43 465** |

### Por que a versão otimista é artefato, não resultado

Medindo diretamente:

- **92,6%** das entradas do CD (1 260 de 1 361) têm a parcial de +45 ao alcance
  **na mesma barra de 1 minuto da entrada**;
- a barra de entrada tem amplitude mediana de **160 pontos**;
- pela regra 4.2, a entrada é sempre num **extremo novo do dia** — ou seja, o
  nível é tocado exatamente na ponta do movimento.

Juntando as três: creditar a parcial na barra de entrada é assumir que a ordem
limite foi preenchida no tick extremo de uma barra de 160 pontos **e** que a
reversão de 45 pontos veio depois do preenchimento. Nenhuma das duas coisas é
observável a 1 minuto, e as duas precisam ser verdade ao mesmo tempo.

Na prática a segunda é ainda mais frágil que a primeira: quando o preço só
encosta no nível e volta, sua ordem tipicamente **não** é preenchida — falta
alguém negociando através do seu preço. Os trades que "funcionam" na versão
creditada são desproporcionalmente aqueles em que você não teria entrado. Por
isso a coluna conservadora é a estimativa relevante, e a otimista é o teto
teórico.

Um sinal independente de que isso é artefato: na versão creditada, o setup C é
positivo em **todos os seis anos** (+957, +4 747, +4 617, +4 211, +4 290,
+1 637). Borda de mercado varia com o regime; artefato de preenchimento não.

> **Para decidir isso é preciso dado de tick**, não de 1 minuto. Enquanto isso
> não existir, qualquer número desta estratégia com alvo de 45 pontos é um
> intervalo que cruza o zero, não um resultado.

---

## 3. Efeito de cada mudança do spec

Referência: no spec anterior (stop do resto em +45, alvo no ajuste para C/D/CD),
o setup C dava −4 189 e o CD −10 417. As duas mudanças desta rodada custam, no
C, 6 775 pts (stop do resto no médio) + 944 pts (alvo de 500 no lugar do
ajuste); no CD, 8 387 + 2 303.

### 3.1 A parcial e o stop do restante

**Parcial de 50% contra 2/3, os dois com o stop do resto no médio**, em todos os
setups (lote de 6: 3 ou 4 contratos saem em +45; o médio fica a −45 ou −90):

| Setup | 2/3 (4 de 6), médio −90 | 50% (3 de 6), médio −45 | Ganham / zeram (50%) |
|---|---:|---:|---:|
| A | −49 433 | **−41 115** | 12,3% / 19,7% |
| B | −53 230 | **−51 600** | 6,0% / 20,1% |
| C | −11 908 | **−10 019** | 12,1% / 49,0% |
| D | −16 252 | **−13 702** | 10,3% / 43,5% |
| CD | −21 107 | **−18 741** | 11,5% / 44,8% |

A parcial de 50% é melhor nos cinco setups — vende menos da cauda e deixa mais
contratos correndo até o alvo —, mas nenhum fica positivo.

**A grade completa, no setup CD:**

| Configuração (setup CD) | Stop do resto | Pontos | Pts/trade | Ganham |
|---|---:|---:|---:|---:|
| Sem parcial | — | −15 060 | −11,1 | 15,5% |
| 3 de 6 em +45, stop no médio | −45 | −18 741 | −13,8 | 11,5% |
| **4 de 6 em +45, stop no médio** (spec) | −90 | **−21 107** | −15,5 | 15,1% |
| 4 de 6 em +45, stop na entrada | 0 | −16 880 | −12,4 | 56,4% |
| 4 de 6 em +45, stop em +45 (spec anterior) | +45 | −14 267 | −10,5 | 56,4% |
| 3 de 6 em +100, "no médio" | −100\* | −13 905 | −10,2 | 15,7% |
| 4 de 6 em +100, "no médio" | −100\* | **−13 520** | −9,9 | 45,3% |

\* o médio cairia no stop ou além dele (−100 e −200); o stop fica em −100 — na
prática, sem breakeven.

**O stop no médio é a pior versão de 2/3 em +45**, e pior que não fazer parcial
nenhuma. Contra o stop do resto em +45, custa **6 840 pontos no CD**: os trades
que antes saíam com +45 agora saem com 0, e o terço que sobra não chega ao alvo
vezes o bastante para compensar. O melhor arranjo da grade é 4 de 6 em +100 —
onde o médio cai além do stop e, portanto, não há breakeven. Nenhuma linha fica
positiva.

### 3.2 Alvo de 500 fixos contra o alvo no ajuste

| | C | D | CD |
|---|---:|---:|---:|
| **Alvo 500 fixos** (spec novo) | **−11 908** | **−16 252** | **−21 107** |
| Alvo no ajuste (spec anterior) | −10 964 | −16 127 | −18 804 |

O alvo fixo é um pouco pior nos três. Como todo nível operável fica a 600+ pts
do ajuste, o alvo de 500 sai antes dele: mais trades chegam ao alvo (204 contra
91 em C), mas cada um rende menos, e o saldo não compensa.

### 3.3 Regime exclusivo (o viés vira ao cruzar o ajuste)

| | C | D | CD |
|---|---:|---:|---:|
| **Exclusivo** (spec) | **−11 908** | **−16 252** | **−21 107** |
| Os dois lados ativos | −13 711 | −17 052 | −23 050 |

Desligar o lado inicial ao cruzar o ajuste **melhora** os três setups
(+1 803 pts em C, +1 943 em CD) e corta ~3% dos trades. A regra é boa; só não é
suficiente.

### 3.4 Setup A com saída no ajuste

| Alvo do setup A | Pontos | Ganham |
|---|---:|---:|
| 500 pts fixos (spec) | −49 433 | 13,5% |
| No ajuste | −53 117 | 20,8% |

Pior. O ajuste fica em média mais longe que 500 pts da abertura, então o alvo
raramente vem e mais trades morrem no stop do resto.

### 3.5 A premissa das médias de 21

Testada nas duas metades em que o enunciado a coloca.

**Como alvo (EMA21 de M5 no lugar dos 500 fixos):**

| Setup | Alvo 500 fixos | Alvo na EMA21 M5 |
|---|---:|---:|
| A | −49 433 | −53 892 |
| B | −53 230 | −85 910 |
| C | −11 908 | −10 284 |
| D | −16 252 | −16 135 |
| CD | −21 107 | −19 348 |

Melhor em C, D e CD (até 1 759 pts), bem pior em A e B — e negativa em todos. A
EMA de M5 fica perto do preço: o alvo vem cedo, o que ajuda os setups de nível
(que mais sofrem com o terço que devolve no médio), mas é pequeno demais para
cobrir os stops.

**Como filtro (distância da EMA21 de M60 na entrada), setup CD:**

| Distância da EMA21 M60 | Trades | Pontos | Pts/trade | Ganham |
|---|---:|---:|---:|---:|
| 0 – 300 | 136 | **−930** | −6,8 | 19,1% |
| 300 – 600 | 154 | −4 053 | −26,3 | 12,3% |
| 600 – 1 000 | 268 | −3 900 | −14,6 | 14,9% |
| 1 000 – 1 500 | 345 | −4 218 | −12,2 | 15,1% |
| 1 500 + | 458 | **−8 005** | −17,5 | 15,1% |

A premissa prevê que quanto mais longe da média, melhor. **Os dados dizem o
contrário**: a faixa mais próxima da média é a menos ruim, e a mais distante é
a que mais perde no total. Não há relação monotônica — assinatura de ruído.

### 3.6 Validação do ajuste contra o call de fechamento

A regra proposta (17:00–17:15) é estreita demais: contém o ajuste em apenas
78,9% dos dias. A janela correta é **17:00–18:00**, com 96,7%. Detalhe em
[ESTRATEGIA.md](ESTRATEGIA.md) §2.2.

**A validação passa**: dos 41 dias que sobram fora, 40 desviam ≤ 124 pts (mediana
30) — folga normal de um ajuste que é média ponderada do call. O único desvio
material já era vencimento. O filtro não removeu nenhum dia novo; os 43
descartados continuam sendo os mesmos de antes.

---

## 4. Estabilidade ano a ano (config. principal, pontos)

| Setup | 2021* | 2022 | 2023 | 2024 | 2025 | 2026* |
|---|---:|---:|---:|---:|---:|---:|
| A | −2 743 | −10 210 | −8 700 | −6 637 | −11 297 | −9 847 |
| B | −2 620 | −9 747 | −11 455 | −8 842 | −12 143 | −8 423 |
| C | −1 243 | −1 547 | −1 086 | −2 489 | −2 203 | −3 339 |
| D | −1 257 | −1 680 | −1 150 | −1 703 | −3 628 | −6 833 |
| CD | −2 297 | −3 462 | −1 549 | −3 386 | −2 480 | −7 933 |
| *(pregões)* | 84 | 244 | 240 | 244 | 239 | 154 |

\* anos parciais. **Os cinco setups perdem em todos os anos.** 2026, com pouco
mais de meio ano, já é o pior ano de C, D e CD.

---

## 5. Dissecação do setup CD

### 5.1 Por tipo de nível

| Tipo | Trades | Pontos | Pts/trade |
|---|---:|---:|---:|
| Bola (múltiplo de 1000) | 488 | **−12 602** | −25,8 |
| Pivô R1 | 127 | +461 | +3,6 |
| Pivô R2 | 139 | −1 182 | −8,5 |
| Pivô R3 | 84 | −1 292 | −15,4 |
| Pivô R4 | 88 | −1 809 | −20,6 |
| Pivô S1 | 104 | **−3 637** | −35,0 |
| Pivô S2 | 144 | −1 310 | −9,1 |
| Pivô S3 | 83 | −597 | −7,2 |
| Pivô S4 | 104 | +860 | +8,3 |

As bolas seguem sendo o lastro morto: 60% de todo o prejuízo do CD, com 36% dos
trades. Os oito pivôs somam −8 506, com só R1 e S4 positivos.

### 5.2 Por distância do ajuste

| Faixa | Trades | Pontos | Pts/trade | Ganham |
|---|---:|---:|---:|---:|
| 600 – 900 | 402 | −8 671 | −21,6 | 11,9% |
| 900 – 1 200 | 302 | −4 275 | −14,2 | 16,9% |
| 1 200 – 1 600 | 262 | −2 683 | −10,2 | 16,8% |
| 1 600 – 2 200 | 230 | **−1 012** | −4,4 | 17,0% |
| 2 200 + | 165 | −4 467 | −27,1 | 14,5% |

Nenhuma faixa fica positiva. Os níveis colados no limite de 600 pts são os
piores; o menos ruim é 1 600–2 200, a −4,4 pts/trade.

---

## 6. Sensibilidade

### 6.1 Stop

| Setup | 100 | 150 | 200 | 300 | 500 |
|---|---:|---:|---:|---:|---:|
| A | −49 433 | −48 513 | −49 607 | −47 017 | −49 713 |
| B | −53 230 | −43 644 | −33 567 | −19 351 | **−6 524** |
| C | −11 908 | **−11 316** | −11 644 | −17 991 | −19 241 |
| D | −16 252 | −21 515 | −22 533 | −19 798 | −23 652 |
| CD | −21 107 | −25 114 | −25 214 | −24 796 | −26 331 |

Com a parcial no lugar, **nenhuma combinação de stop fica positiva** — inclusive
o setup B, que na rodada sem parcial chegava a +41 873 com stop de 500. A
parcial destrói exatamente o que fazia o stop largo funcionar: a cauda.

### 6.2 Invalidação por retração

| Retração | Trades | Pontos | Pts/trade | Ganham |
|---|---:|---:|---:|---:|
| 300 pts | 804 | −17 900 | −22,3 | 12,8% |
| **500 pts** (spec) | 1 361 | **−21 107** | −15,5 | 15,1% |
| 800 pts | 1 848 | −28 737 | −15,6 | 14,9% |
| 1 200 pts | 2 086 | −29 441 | −14,1 | 15,4% |
| sem regra | 2 175 | −30 224 | −13,9 | 15,5% |

A regra segue valendo: contra não filtrar nada, corta 814 trades (37%) e melhora
o agregado em 9 117 pontos.

---

## 7. Conclusões

1. **Com alvo parcial de 45 pontos, 1 minuto não basta.** O resultado do setup
   C é −11 908 ou +20 459 conforme uma convenção intrabarra, e 92,6% das
   entradas têm a parcial ao alcance na própria barra do toque. A pergunta
   ficou sem resposta, e a resposta exige dado de tick.

2. **Sob a convenção defensável, tudo continua perdendo — em todos os anos.**
   −11 908 (C) e −21 107 (CD), antes de custos. Com o round-trip de 5 a 10
   pontos em 1 361 trades, some mais 7 000 a 14 000 pontos de prejuízo.

3. **O breakeven no médio é a pior versão da parcial.** Com 2/3 e o stop do
   resto no médio, o CD perde −21 107; no +45, −14 267; sem parcial, −15 060.
   74% dos trades de C que fazem a parcial voltam ao médio e fecham em zero. A
   parcial de 50% (médio a −45) é melhor que a de 2/3 nos cinco setups, mas
   também negativa.

4. **O alvo de 500 fixos é marginalmente pior que sair no ajuste** (−944 pts em
   C, −2 303 em CD). Não muda a conclusão.

5. **A premissa das médias não se confirma.** Como alvo, a EMA21 M5 melhora os
   setups de nível mas continua negativa; como filtro, a faixa mais distante da
   EMA21 de M60 é a que mais perde.

6. **Duas regras do spec se mostraram boas** e valem para outras estratégias: o
   **regime exclusivo** (+1 803 pts em C) e a **invalidação por retração de 500
   pts** (+9 117 pts no CD contra não filtrar).

7. **A validação do ajuste passa** — a coluna de *Prior Cote Ajuste* é
   consistente com o call de fechamento em 96,7% dos dias, e as exceções são
   folga de VWAP.

### O que investigar

- **Dado de tick** para o intervalo em que a estratégia inteira está indefinida.
  Sem isso não dá para decidir nada com alvo parcial de 45 pontos.
- **Rever a parcial**: 4 de 6 em +100 (−13 520), o stop do resto em +45
  (−14 267) e a parcial de 50% (−18 741) custam menos que 2/3 com breakeven no
  médio (−21 107).
- **Abandonar as bolas**: 60% do prejuízo do CD com 36% dos trades.
- **Filtro de contexto na abertura**, que segue sendo o problema de origem: o
  setup entra em todo dia de tendência forte contra o ajuste.

---

## 8. Ressalvas

- **Custos não incluídos** (5 a 10 pts por round-trip).
- **Sem slippage**, e assumindo preenchimento integral da ordem limite no toque
  exato do nível — premissa que §2 mostra ser o ponto mais frágil de todo o
  estudo.
- **Resolução de 1 minuto.** Ver §2.
- **27 dias de vencimento excluídos**; dias de gap genuíno mantidos.
- **Lote fixo de 6 contratos**, sem dimensionamento.
- As duas bases batem em **1 248 de 1 248 dias, diferença máxima 0 pontos**.
