# Resultados — Estratégia do Ajuste (WINFUT)

Base: WIN$N M1, **2021-08-23 a 2026-08-21**, 1248 pregões no arquivo,
**1205 válidos** ([ESTRATEGIA.md](ESTRATEGIA.md) §2.2). Resultados **brutos**,
sem custos. 1 contrato. R$ 0,20 por ponto.

Rodada com o spec revisado: parcial de 2/3 em +45, regime exclusivo ao cruzar o
ajuste, validação do ajuste contra o call de fechamento, setup A com alvo no
ajuste e a premissa das médias de 21.

---

## 1. Resumo executivo

**A conclusão não mudou: nenhum setup tem borda.** Mas a rodada produziu um
achado metodológico maior que qualquer um dos resultados.

| Setup | Trades | Pontos | R$/contrato | Acerto | PF | Drawdown |
|---|---:|---:|---:|---:|---:|---:|
| A — retorno à abertura | 1 189 | −47 572 | −9 514 | 32,0% | 0,41 | −47 668 |
| B — trade seco no ajuste | 894 | −50 920 | −10 184 | 26,2% | 0,23 | −50 965 |
| **C — pivôs** | 1 368 | **−4 189** | −838 | 61,1% | 0,92 | −6 199 |
| D — bolas | 726 | −9 947 | −1 989 | 53,9% | 0,70 | −11 480 |
| **CD — pivôs + bolas** | 1 361 | **−10 417** | −2 083 | 56,4% | 0,82 | −11 776 |

A parcial elevou o acerto de ~10% para ~56%, como esperado — e não salvou
nenhum setup, porque troca alvos grandes por muitos +45 e mantém os −100.

---

## 2. O achado desta rodada: a parcial de +45 torna o backtest indecidível

A saída parcial em +45 pontos é pequena demais para uma base de 1 minuto
resolver. Dependendo de uma única convenção sobre a barra de entrada, o setup C
vai de −4 189 a +55 104 pontos:

| Convenção da barra de entrada | A | B | **C** | D | **CD** |
|---|---:|---:|---:|---:|---:|
| **Conservadora** — a barra do toque só resolve o stop | −47 572 | −50 920 | **−4 189** | −9 947 | **−10 417** |
| Creditando a barra de entrada | −31 058 | −46 037 | **+34 880** | +8 590 | **+25 950** |
| Teto absoluto (+ alvo ganha empate) | +12 887 | −4 778 | **+55 104** | +28 651 | **+54 354** |

### Por que a versão otimista é artefato, não resultado

Medindo diretamente:

- **92,6%** das parciais de +45 são atingidas **na mesma barra de 1 minuto da
  entrada**;
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
positivo em **todos os seis anos** (+3 173, +7 858, +7 835, +7 564, +7 130,
+1 320). Borda de mercado varia com o regime; artefato de preenchimento não.

> **Para decidir isso é preciso dado de tick**, não de 1 minuto. Enquanto isso
> não existir, qualquer número desta estratégia com alvo de 45 pontos é um
> intervalo que cruza o zero, não um resultado.

---

## 3. Efeito de cada mudança do spec

### 3.1 A parcial

| Configuração | Trades | Pontos | Pts/trade | Acerto |
|---|---:|---:|---:|---:|
| Sem parcial (spec anterior) | 1 361 | −9 233 | −6,8 | 10,2% |
| 50% em +45, stop → +45 | 1 361 | **−3 207** | −2,4 | 56,4% |
| **2/3 em +45, stop → +45** (spec) | 1 361 | −10 417 | −7,7 | 56,4% |
| 2/3 em +45, stop → zero a zero | 1 361 | −13 105 | −9,6 | 56,4% |
| 75% em +45, stop → +45 | 1 361 | −14 021 | −10,3 | 56,4% |
| 2/3 em +100, stop → +100 | 1 361 | −2 773 | −2,0 | 45,3% |

Nenhuma fração vira o jogo. Quanto maior a fração que sai em +45, pior — porque
a parcial financia o acerto alto vendendo justamente a cauda que pagaria os
stops. Note que a fração 2/3 exigida pelo "2:1" é **pior** que 1/2.

### 3.2 Regime exclusivo (o viés vira ao cruzar o ajuste)

| | C | D | CD |
|---|---:|---:|---:|
| **Exclusivo** (spec novo) | **−4 189** | **−9 947** | **−10 417** |
| Os dois lados ativos (spec antigo) | −5 637 | −10 522 | −12 152 |

Desligar o lado inicial ao cruzar o ajuste **melhora** os três setups
(+1 448 pts em C, +1 735 em CD) e corta ~3% dos trades. A regra é boa; só não é
suficiente.

### 3.3 Setup A com alvo no ajuste

| Alvo do setup A | Pontos | Acerto |
|---|---:|---:|
| 500 pts fixos | −47 572 | 32,0% |
| No ajuste | **−51 899** | 32,0% |

Pior. O ajuste fica em média mais longe que 500 pts da abertura, então o alvo
raramente vem e mais trades morrem no stop+.

### 3.4 A premissa das médias de 21

Testada nas duas metades em que o enunciado a coloca.

**Como alvo (EMA21 de M5 no lugar do ajuste):**

| Setup | Alvo no ajuste | Alvo na EMA21 M5 |
|---|---:|---:|
| A | −47 572 | −52 948 |
| B | −50 920 | −85 886 |
| C | −4 189 | −5 496 |
| D | −9 947 | −9 663 |
| CD | −10 417 | −12 060 |

Pior em 4 dos 5 setups. A EMA de M5 fica perto demais do preço: o alvo é
atingido cedo, com lucro pequeno, sem cobrir os stops.

**Como filtro (distância da EMA21 de M60 na entrada), setup CD:**

| Distância da EMA21 M60 | Trades | Pontos | Pts/trade | Acerto |
|---|---:|---:|---:|---:|
| 0 – 300 | 136 | −1 073 | −7,9 | 56,6% |
| 300 – 600 | 154 | −3 034 | −19,7 | 51,3% |
| 600 – 1 000 | 268 | −70 | −0,3 | 58,6% |
| 1 000 – 1 500 | 345 | −579 | −1,7 | 60,3% |
| 1 500 + | 458 | **−5 659** | −12,4 | 53,7% |

A premissa prevê que quanto mais longe da média, melhor. **Os dados dizem o
contrário**: a faixa mais distante é a pior de todas. Não há relação monotônica
— o melhor pedaço é o meio da distribuição, o que é assinatura de ruído.

### 3.5 Validação do ajuste contra o call de fechamento

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
| A | −2 585 | −9 275 | −8 185 | −6 937 | −11 148 | −9 442 |
| B | −2 912 | −9 357 | −10 443 | −7 823 | −11 973 | −8 412 |
| C | −17 | −302 | +1 564 | −1 252 | −309 | −3 872 |
| D | −745 | +1 170 | −346 | −1 893 | −1 742 | −6 390 |
| CD | −1 082 | −254 | +259 | −2 575 | −176 | −6 588 |
| *(pregões)* | 84 | 244 | 240 | 244 | 239 | 154 |

\* anos parciais. C e CD oscilam em torno de zero até 2025 e desabam em 2026.

---

## 5. Dissecação do setup CD

### 5.1 Por tipo de nível

| Tipo | Trades | Pontos | Pts/trade |
|---|---:|---:|---:|
| Bola (múltiplo de 1000) | 488 | **−7 718** | −15,8 |
| Pivô R1 | 127 | +885 | +7,0 |
| Pivô R2 | 139 | −298 | −2,1 |
| Pivô R3 | 84 | −988 | −11,8 |
| Pivô R4 | 88 | −1 315 | −14,9 |
| Pivô S1 | 104 | **−3 056** | −29,4 |
| Pivô S2 | 144 | +699 | +4,9 |
| Pivô S3 | 83 | +531 | +6,4 |
| Pivô S4 | 104 | +844 | +8,1 |

As bolas seguem sendo o lastro morto: 74% de todo o prejuízo do CD, com 36% dos
trades. Os pivôs somam −2 698 no conjunto — praticamente zero espalhado por oito
níveis.

### 5.2 Por distância do ajuste

| Faixa | Trades | Pontos | Pts/trade | Acerto |
|---|---:|---:|---:|---:|
| 600 – 900 | 402 | −4 875 | −12,1 | 56,0% |
| 900 – 1 200 | 302 | −2 547 | −8,4 | 54,0% |
| 1 200 – 1 600 | 262 | −125 | −0,5 | 58,4% |
| 1 600 – 2 200 | 230 | **+788** | +3,4 | 64,3% |
| 2 200 + | 165 | −3 656 | −22,2 | 47,3% |

O bolsão positivo que existia na rodada anterior (900–1600) desapareceu com a
parcial. Sobrou uma faixa marginal em 1 600–2 200, com 230 trades e +3,4
pts/trade — abaixo do custo operacional.

---

## 6. Sensibilidade

### 6.1 Stop

| Setup | 100 | 150 | 200 | 300 | 500 |
|---|---:|---:|---:|---:|---:|
| A | −47 572 | −43 193 | −42 360 | −37 280 | −39 005 |
| B | −50 920 | −41 128 | −30 097 | −14 521 | **−1 314** |
| C | −4 189 | −2 345 | **−1 247** | −6 181 | −7 017 |
| D | −9 947 | −14 767 | −15 133 | −12 012 | −14 559 |
| CD | −10 417 | −13 103 | −11 622 | −9 345 | −9 819 |

Com a parcial no lugar, **nenhuma combinação de stop fica positiva** — inclusive
o setup B, que na rodada sem parcial chegava a +41 873 com stop de 500. A
parcial destrói exatamente o que fazia o stop largo funcionar: a cauda.

### 6.2 Invalidação por retração

| Retração | Trades | Pontos | Pts/trade | Acerto |
|---|---:|---:|---:|---:|
| 300 pts | 804 | −9 182 | −11,4 | 53,2% |
| **500 pts** (spec) | 1 361 | **−10 417** | −7,7 | 56,4% |
| 800 pts | 1 848 | −15 165 | −8,2 | 57,3% |
| 1 200 pts | 2 086 | −15 550 | −7,5 | 57,7% |
| sem regra | 2 175 | −15 743 | −7,2 | 57,8% |

A regra segue valendo: contra não filtrar nada, corta 814 trades (37%) e melhora
o agregado em 5 326 pontos.

---

## 7. Conclusões

1. **Com alvo de 45 pontos, 1 minuto não basta.** O resultado do setup C é
   −4 189 ou +34 880 conforme uma convenção intrabarra, e 92,6% das parciais
   dependem dela. Esse é o resultado principal desta rodada: a pergunta ficou
   sem resposta, e a resposta exige dado de tick.

2. **Sob a convenção defensável, tudo continua perdendo.** −4 189 (C) e −10 417
   (CD), antes de custos. Com o round-trip de 5 a 10 pontos em 1 361 trades,
   some mais 7 000 a 14 000 pontos de prejuízo.

3. **A parcial melhora o acerto e piora o resultado.** De 10% para 56% de acerto,
   e de −9 233 para −10 417 pontos no CD. Vender 2/3 em +45 elimina a cauda que
   pagava os stops. E a fração exigida pelo "2:1" (2/3) é pior que 1/2.

4. **A premissa das médias não se confirma.** Nem como alvo (EMA21 M5 é pior que
   o ajuste em 4 dos 5 setups), nem como filtro (a faixa mais distante da EMA21
   de M60 é a que mais perde).

5. **Duas regras do spec se mostraram boas** e valem para outras estratégias: o
   **regime exclusivo** (+1 448 pts em C) e a **invalidação por retração de 500
   pts** (+5 326 pts no CD contra não filtrar).

6. **A validação do ajuste passa** — a coluna de *Prior Cote Ajuste* é
   consistente com o call de fechamento em 96,7% dos dias, e as exceções são
   folga de VWAP.

### O que investigar

- **Dado de tick** para o intervalo em que a estratégia inteira está indefinida.
  Sem isso não dá para decidir nada com alvo de 45 pontos.
- **Alvo maior que 45**: a variante 2/3 em +100 já é 4× melhor (−2 773 contra
  −10 417). Vale varrer 100–300.
- **Abandonar as bolas**: 74% do prejuízo do CD com 36% dos trades.
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
- **Um contrato fixo**, sem dimensionamento.
- As duas bases batem em **1 248 de 1 248 dias, diferença máxima 0 pontos**.
