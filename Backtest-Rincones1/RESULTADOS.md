# Resultados — Rincones1

> **Este arquivo é gerado.** Rode `python rodar.py && python relatorio.py`.
> Não edite à mão: a fonte de todos os números é `saida/resumo.json`, e o
> [relatorio.html](relatorio.html) sai do mesmo lugar, pelo mesmo caminho.

**Gestão:** parcial de 50% **na mesma distância do stop** · o stop do restante vai para a **média da operação**, que com meia posição é o próprio stop inicial — então o stop **não anda** e o trade que volta morre em **zero de verdade** · alvo 300 · entrada por ordem limitada no meio do candle, **válida por uma barra** · **sem custo**. Stop de 150 (padrão) e de 100 (variante), lado a lado; a parcial acompanha os dois.

---

## 1. As duas bases

| | barras | pregões | período |
|---|---|---|---|
| **WINV26** | 6.367 | 95 (13 com trade) | 2026-04-15 a 2026-08-28 |
| **WINFUT** | 49.586 | 102 (95 com trade) | 2026-04-17 a 2026-09-11 |

> **Elas não são independentes.** O WINFUT contém a janela inteira do WINV26 e
> se estende antes e depois dela. Quando as duas concordam, isso é menos
> confirmação do que parece.

> **Fora da amostra (§ 10):** **A vantagem não se repetiu fora da amostra.** Todos os parâmetros foram escolhidos olhando os pregões de 30/06/2026 a 28/08/2026. O WINFUT novo tem **58 pregões fora dessa janela** — 49 antes e 9 depois — que nunca foram vistos ao calibrar. Com stop 150: dentro da janela, só A dá 54 trades, EV +80,6, t +3,12 e A + B dá 151 trades, EV +44,1, t +2,97; **fora dela, só A dá 76 trades, EV +9,9, t +0,51 e A + B dá 197 trades, EV -5,3, t -0,45**. O setup B isolado, fora: 128 trades, EV -15,2, t -0,98. O setup A se divide: 57 trades, EV -10,5, t -0,47 antes da janela (49 pregões) e 19 trades, EV +71,1, t +2,36 depois (9 pregões) — o trecho posterior é curto demais para desempatar.

---

## 2. O eixo [E2]: o deslocamento virou vaivém

O índice de esforço tem três eixos — volume, deslocamento e tempo. O eixo do
**deslocamento** era `|delta| / |Close−Open|`: agressão por ponto de *saldo*. Saldo
não é caminho — uma barra que sobe 60, cai 65 e fecha 30 acima da abertura tem o
mesmo `|Close−Open|` de uma que sobe 30 em linha reta, e as duas contavam igual.

O eixo novo é `v2 · (|delta|/esforço) × volta`, com `percurso = 2·(High−Low) − |Close−Open|` (o menor caminho
compatível com o OHLC) e `volta = 1 − |Close−Open|/percurso` (a fração dele que foi
desfeita). É **produto de duas frações entre 0 e 1, não razão**: razão entre peças
de dispersão muito diferente mede só a mais volátil das duas. A derivação e a
medição do eixo estão em `Ticks_Esforco_Hist_v2.ntsl`.

Com **todo o resto congelado** — mesma média, mesmos setups, mesma gestão:

| fórmula | stop | | WINV26 · n / EV / t / PF | WINFUT · n / EV / t / PF |
|---|---|---|---|---|
| v1 · \|delta\| / \|Close-Open\| | 150 | setup A isolado | 31 · +89,5 · +3,17 · 2,85 | 192 · +30,3 · +2,23 · 1,46 |
|  | 150 | setup B isolado | 36 · +25,0 · +0,86 · 1,40 | 259 · +8,3 · +0,73 · 1,11 |
|  | 150 | carteira só A | 29 · +80,2 · +3,43 · 2,55 | 186 · +28,1 · +2,11 · 1,42 |
|  | 150 | carteira A + B | 63 · +44,0 · +1,81 · 1,74 | 421 · +12,3 · +1,33 · 1,17 |
|  | 100 | setup A isolado | 31 · +90,3 · +3,69 · 4,50 | 192 · +27,6 · +2,73 · 1,61 |
|  | 100 | setup B isolado | 36 · +25,0 · +1,24 · 1,60 | 259 · +8,2 · +1,09 · 1,17 |
|  | 100 | carteira só A | 29 · +82,8 · +4,20 · 4,00 | 187 · +24,6 · +2,51 · 1,53 |
|  | 100 | carteira A + B | 64 · +53,1 · +2,79 · 2,55 | 427 · +13,4 · +2,04 · 1,28 |
| v2 · (\|delta\|/esforço) × volta | 150 | setup A isolado | 26 · +86,5 · +2,42 · 2,67 | 133 · +38,9 · +2,45 · 1,61 |
|  | 150 | setup B isolado | 35 · +68,6 · +2,86 · 2,45 | 233 · +1,2 · +0,11 · 1,02 |
|  | 150 | carteira só A | 25 · +81,0 · +2,18 · 2,50 | 130 · +39,2 · +2,46 · 1,61 |
|  | 150 | **carteira A + B** | 59 · +77,5 · +3,39 · 2,61 | 348 · +16,1 · +1,68 · 1,23 |
|  | 100 | setup A isolado | 26 · +73,1 · +2,66 · 3,11 | 133 · +21,8 · +1,85 · 1,46 |
|  | 100 | setup B isolado | 35 · +40,0 · +2,10 · 2,00 | 233 · +1,3 · +0,16 · 1,03 |
|  | 100 | carteira só A | 25 · +68,0 · +2,43 · 2,89 | 130 · +21,5 · +1,82 · 1,45 |
|  | 100 | carteira A + B | 60 · +51,7 · +2,73 · 2,35 | 352 · +8,2 · +1,10 · 1,17 |

**A troca não melhora tudo: ela melhora a reversão.** A fórmula nova corta gatilhos (-11% e -17%) e mede melhor no **setup B em 2 das 4** células (duas bases × dois stops), no **setup A em 1 de 4** e na **carteira A + B em 2 de 4**. No WINV26 o setup B sai de +25,0 de EV e t +0,86 para +68,6 e t +2,86, e o A de +89,5 e t +3,17 para +86,5 e t +2,42 (stop 150). No WINFUT o setup B sai de +8,3 de EV e t +0,73 para +1,2 e t +0,11, e o A de +30,3 e t +2,23 para +38,9 e t +2,45 (stop 150). Faz sentido: o eixo novo mede **vaivém**, que é exaustão — e exaustão é exatamente o que o setup de reversão procura. O setup A é continuação: ali o vaivém informa menos, e o que a fórmula nova faz é sobretudo tirar sinal.

**O filtro continua valendo com a fórmula nova.** Ele existia porque a antiga media negativo quando o eixo do deslocamento mandava; não era óbvio que sobreviveria à troca, e sobreviveu. No WINV26, com o filtro: +77,5 de EV e t +3,39 em 59 trades; sem ele: +33,3 e t +1,53 em 115. No WINFUT, com o filtro: +16,1 de EV e t +1,68 em 348 trades; sem ele: +9,2 e t +1,31 em 701.

---

## 3. A regra da barra seguinte

A ordem limitada no meio do candle do gatilho vale por **uma barra**. Não
preencheu na barra seguinte, o trade é **abortado** -- não se persegue o preço,
não se deixa ordem esquecida no livro. Todo número deste arquivo já está sob
essa regra.

A regra descarta uma minoria estável dos sinais. No WINV26, **26 dos 29** sinais do setup A viraram trade (3 abortados, 10%); no B, 35 de 41 (15%). No WINFUT, **133 dos 151** sinais do setup A viraram trade (18 abortados, 12%); no B, 233 de 274 (15%). **Espere isso na tela:** cerca de um sinal em dez será abortado, e abortar é o comportamento correto, não uma falha sua.

---

## 4. Cada setup isolado (stop 150)

### WINV26

| | n | /pregão | EV | total | acerto | t | PF | DD |
|---|---|---|---|---|---|---|---|---|
| **A** — tendência | 26 | 2,2 | +86,5 | +2.250 | 61,5% | +2,42 | 2,67 | 300 |
| **B** — reversão rápida | 35 | 2,7 | +68,6 | +2.400 | 51,4% | +2,86 | 2,45 | 450 |
| **C** — consolidação | 6 | 2,0 | -87,5 | -525 | 16,7% | -7,00 | 0,30 | 375 |

### WINFUT

| | n | /pregão | EV | total | acerto | t | PF | DD |
|---|---|---|---|---|---|---|---|---|
| **A** — tendência | 133 | 1,8 | +38,9 | +5.175 | 45,9% | +2,45 | 1,61 | 1125 |
| **B** — reversão rápida | 233 | 2,5 | +1,2 | +290 | 33,5% | +0,11 | 1,02 | 2485 |
| **C** — consolidação | 48 | 1,5 | -17,2 | -825 | 31,2% | -0,76 | 0,80 | 1575 |

**A prioridade que você pediu continua certa**: o setup de tendência lidera a maioria das colunas nas duas bases. Não todas — no WINV26 o setup B mede +2,86 de t contra +2,42 do A. Com esse número de trades uma coluna trocada é ruído, não hierarquia; o A segue prioritário por EV, fator de lucro e drawdown.

O setup C mede negativo nas duas bases. Fica desligado por padrão.

---

## 5. A média que dá a direção

Com média única a direção vira o **sinal da inclinação** dela nas últimas 5
barras, normalizada pelo range médio; o toque vira encostar nessa linha. Cada
família teve período e corte de inclinação varridos, e o valor escolhido foi o
que mede bem **nas duas bases**, não o pico de uma.

### Carteira só A · stop 150

| média | % barras em tendência | WINV26 · n / EV / t / PF | WINFUT · n / EV / t / PF |
|---|---|---|---|
| **3 EMAs 21/42/72** ← padrão | 81% | 25 · +81,0 · +2,18 · 2,50 | 130 · +39,2 · +2,46 · 1,61 |
| KAMA 13 | 48% | 14 · +64,3 · +1,00 · 2,00 | 71 · +19,0 · +0,87 · 1,27 |
| Hull 13 | 95% | 22 · +10,2 · +0,19 · 1,12 | 146 · +21,6 · +1,54 · 1,32 |
| T3 Tillson 13 | 92% | 23 · +45,7 · +1,01 · 1,64 | 134 · +25,7 · +1,70 · 1,38 |
| estilo Jurik 21 | 93% | 24 · +43,8 · +0,88 · 1,64 | 150 · +37,5 · +2,65 · 1,62 |

### Carteira só A · stop 100

| média | % barras em tendência | WINV26 · n / EV / t / PF | WINFUT · n / EV / t / PF |
|---|---|---|---|
| **3 EMAs 21/42/72** ← padrão | 81% | 25 · +68,0 · +2,43 · 2,89 | 130 · +21,5 · +1,82 · 1,45 |
| KAMA 13 | 48% | 14 · +64,3 · +1,38 · 2,80 | 72 · +5,6 · +0,34 · 1,11 |
| Hull 13 | 95% | 22 · +22,7 · +0,63 · 1,45 | 148 · +12,2 · +1,23 · 1,25 |
| T3 Tillson 13 | 92% | 23 · +43,5 · +1,39 · 2,00 | 135 · +11,1 · +1,08 · 1,22 |
| estilo Jurik 21 | 93% | 24 · +45,8 · +1,40 · 2,22 | 152 · +17,8 · +1,84 · 1,38 |

Com **stop 150** as três EMAs ganham no WINV26 (+2,18 contra +1,01 da segunda), mas a **estilo Jurik 21** passa à frente no WINFUT (+2,65 contra +2,46). Na base em que o empilhamento ganha, essa mesma média mede +0,88. Com **stop 100** as três EMAs ganham no WINV26 (+2,43 contra +1,40 da segunda), mas a **estilo Jurik 21** passa à frente no WINFUT (+1,84 contra +1,82). Na base em que o empilhamento ganha, essa mesma média mede +1,40. A **KAMA** segue sendo a mais seletiva — classifica 48% das barras como tendência contra 81% do empilhamento, e produz cerca de metade dos trades.

O empilhamento exige **concordância entre três escalas de tempo**, e isso é
informação que a inclinação de uma linha só não carrega. Uma média adaptativa
resolve o atraso; não resolve a falta de confirmação.

> **Sobre a "Jurik":** o JMA da Jurik Research é proprietário e não publicado. O
> que está aqui é uma aproximação pública do estilo — adaptativa com correção de
> fase. Leia aquela linha como "uma adaptativa muito suavizada", **não** como "o
> JMA foi testado". Se o resultado dela pesasse na decisão, o certo seria
> licenciar o indicador de verdade e refazer.

---

## 6. A restrição do leque

O gatilho de esforço não olha **onde** o preço está — ele só mede que alguém
agrediu e falhou. A restrição desta seção diz onde isso conta: a barra tem de
estar **encostada no leque** ou **do lado de trás dele**. O gatilho que dispara
com o preço esticado **na frente** do leque, fora da tolerância do toque, é
descartado. Liga-se com `FILTRO_LEQUE = True` em `engine.py`.

### Onde o preço está quando o gatilho dispara

| posição da barra | WINV26 · barras / gatilhos | WINFUT · barras / gatilhos |
|---|---|---|
| tocando alguma das três | 75,0% / 61,7% | 76,1% / 55,4% |
| **atrás** do leque, fora da tolerância | 1,7% / 4,3% | 1,6% / 4,2% |
| na frente — *exatamente o que a restrição corta* | 23,3% / 34,0% | 22,3% / 40,5% |

### Sem restrição — qualquer posição em relação às médias

| | gatilhos | stop | n | EV | t | PF | DD |
|---|---|---|---|---|---|---|---|
| WINV26 · setup B isolado | 94 | 150 | 35 | +68,6 | +2,86 | 2,45 | 450 |
| WINV26 · **carteira A + B** | 94 | 150 | 59 | +77,5 | +3,39 | 2,61 | 450 |
| WINV26 · setup B isolado | 94 | 100 | 35 | +40,0 | +2,10 | 2,00 | 300 |
| WINV26 · **carteira A + B** | 94 | 100 | 60 | +51,7 | +2,73 | 2,35 | 300 |
| WINFUT · setup B isolado | 625 | 150 | 233 | +1,2 | +0,11 | 1,02 | 2485 |
| WINFUT · **carteira A + B** | 625 | 150 | 348 | +16,1 | +1,68 | 1,23 | 2475 |
| WINFUT · setup B isolado | 625 | 100 | 233 | +1,3 | +0,16 | 1,03 | 2000 |
| WINFUT · **carteira A + B** | 625 | 100 | 352 | +8,2 | +1,10 | 1,17 | 2600 |

### Só gatilho que toca ou fica atrás do leque

| | gatilhos | stop | n | EV | t | PF | DD |
|---|---|---|---|---|---|---|---|
| WINV26 · setup B isolado | 62 | 150 | 13 | +103,8 | +2,25 | 4,00 | 150 |
| WINV26 · **carteira A + B** | 62 | 150 | 38 | +88,8 | +2,61 | 2,88 | 450 |
| WINV26 · setup B isolado | 62 | 100 | 13 | +76,9 | +1,86 | 3,50 | 200 |
| WINV26 · **carteira A + B** | 62 | 100 | 38 | +71,1 | +2,44 | 3,08 | 300 |
| WINFUT · setup B isolado | 372 | 150 | 50 | -7,5 | -0,29 | 0,91 | 1500 |
| WINFUT · **carteira A + B** | 372 | 150 | 179 | +27,2 | +1,98 | 1,39 | 1800 |
| WINFUT · setup B isolado | 372 | 100 | 50 | +16,0 | +0,81 | 1,33 | 700 |
| WINFUT · **carteira A + B** | 372 | 100 | 179 | +20,1 | +1,86 | 1,42 | 1400 |

**A restrição não mexe no A: ela reescreve o B.** Cortando 34,0% e 40,5% dos gatilhos, ela melhora o EV da carteira A + B em **4 das 4** células (duas bases × dois stops), o `t` em **2 de 4** e o drawdown em **2 de 4** (sem piorar em nenhuma). O setup A sai **idêntico** nas quatro — ele já exigia o toque, então já estava inteiro dentro da restrição. No WINV26 o setup B cai de 35 para 13 trades e o EV vai de +68,6 para +103,8 (t +2,86 → +2,25); a carteira A + B vai de +77,5 para +88,8 de EV, com o drawdown parado em 450 pontos. No WINFUT o setup B cai de 233 para 50 trades e o EV vai de +1,2 para -7,5 (t +0,11 → -0,29); a carteira A + B vai de +16,1 para +27,2 de EV, com o drawdown de 2475 para 1800 pontos. O que sobra do B é o afastamento medido **no leque ou atrás dele**: mesmo lugar do A, direção oposta — quem decide é de que lado veio a agressão que falhou. O que ela joga fora é a esticada à frente das médias, que é exatamente onde a reversão é mais cara. A ressalva é de amostra: onde o `t` piora, ele piora porque a restrição tirou trade, não porque tirou vantagem — o EV sobe e o `t` cai junto com o n.

> **Por que ela não é o padrão.** Não é uma peneira nova de qualidade: é uma
> troca de carteira. Corta uma fatia grande dos gatilhos e quase todo o
> setup B, e o que sobra do B é pequeno demais para medir sozinho — o `t`
> cai onde o EV sobe, e isso é aritmética de amostra, não vantagem perdida.
> Com dois arquivos que se sobrepõem na maior parte da janela, promovê-la a
> padrão seria escolher a curva mais bonita de uma amostra pequena.

### As duas metades da restrição, separadas (carteira A + B)

| gatilhos aceitos | stop | WINV26 · gat / n / EV / t / DD | WINFUT · gat / n / EV / t / DD |
|---|---|---|---|
| sem restrição | 150 | 94 · 59 · +77,5 · +3,39 · 450 | 625 · 348 · +16,1 · +1,68 · 2475 |
| sem restrição | 100 | 94 · 60 · +51,7 · +2,73 · 300 | 625 · 352 · +8,2 · +1,10 · 2600 |
| só o toque no leque | 150 | 58 · 36 · +81,2 · +2,26 · 450 | 346 · 172 · +27,9 · +1,99 · 1650 |
| só o toque no leque | 100 | 58 · 36 · +72,2 · +2,42 · 300 | 346 · 172 · +20,3 · +1,85 · 1300 |
| só o que fica atrás do leque | 150 | 4 · 2 · +225,0 · — · 0 | 26 · 7 · +10,7 · +0,14 · 300 |
| só o que fica atrás do leque | 100 | 4 · 2 · +50,0 · — · 0 | 26 · 7 · +14,3 · +0,28 · 300 |
| **os dois — a variante** | 150 | 62 · 38 · +88,8 · +2,61 · 450 | 372 · 179 · +27,2 · +1,98 · 1800 |
| **os dois — a variante** | 100 | 62 · 38 · +71,1 · +2,44 · 300 | 372 · 179 · +20,1 · +1,86 · 1400 |

**A metade de trás do leque ajuda, mas não sempre.** Ela vale 4,3% e 4,2% dos gatilhos e melhora o EV em 1 das 4 células. WINV26: só o toque dá +81,2 de EV, com o de trás junto dá +88,8; WINFUT: só o toque dá +27,9 de EV, com o de trás junto dá +27,2. Nenhuma das duas leituras aguenta peso: sozinha, a metade de trás rende **2 e 7 trades** nas duas bases. O que a decomposição mostra com segurança é outra coisa — a restrição é, na prática, **quase toda** o toque. Com tolerância de um range médio, o preço que se afastou o bastante para deixar o leque inteiro para trás quase não acontece.

### A restrição nas cinco médias de regime (carteira A + B, stop 150)

| média | % barras tocando | WINV26 · sem / com | WINFUT · sem / com |
|---|---|---|---|
| **3 EMAs 21/42/72** ← padrão | 76,1% | 59 · +77,5 · +3,39 / 38 · +88,8 · +2,61 | 348 · +16,1 · +1,68 / 179 · +27,2 · +1,98 |
| KAMA 13 | 74,3% | 46 · +75,0 · +2,61 / 18 · +66,7 · +1,16 | 309 · +6,0 · +0,58 / 114 · +7,2 · +0,43 |
| Hull 13 | 99,0% | 31 · +36,3 · +0,82 / 31 · +36,3 · +0,82 | 186 · +21,4 · +1,65 / 186 · +21,4 · +1,65 |
| T3 Tillson 13 | 68,1% | 63 · +64,3 · +2,61 / 36 · +35,4 · +1,00 | 410 · +13,5 · +1,46 / 217 · +15,2 · +1,33 |
| estilo Jurik 21 | 90,1% | 62 · +46,0 · +1,62 / 36 · +20,8 · +0,59 | 382 · +17,6 · +1,86 / 259 · +18,5 · +1,63 |

**A restrição é uma propriedade do leque, não das médias em geral.** Em nenhuma família ela melhora o `t` nas duas bases ao mesmo tempo. Com as três EMAs — WINV26: +77,5 → +88,8 de EV (t +3,39 → +2,61); WINFUT: +16,1 → +27,2 de EV (t +1,68 → +1,98). Em Hull 13 a restrição é **inerte**: com média única e tolerância de um range médio, o preço encosta na linha quase sempre, e não sobra nada para cortar. “Atrás do leque” pressupõe um leque: três linhas separadas o bastante para haver um lado de cá e um de lá. Uma linha só não tem espessura, e a restrição vira outra coisa — um filtro do preço contra a inclinação.

---

## 7. O stop: 100 contra 150

| stop | carteira | WINV26 · EV / t / PF / DD | WINFUT · EV / t / PF / DD |
|---|---|---|---|
| 150 | só A | +81,0 · +2,18 · 2,50 · 300 | +39,2 · +2,46 · 1,61 · 1125 |
| 150 | A + B | +77,5 · +3,39 · 2,61 · 450 | +16,1 · +1,68 · 1,23 · 2475 |
| **100** | só A | +68,0 · +2,43 · 2,89 · 200 | +21,5 · +1,82 · 1,45 · 1100 |
| **100** | A + B | +51,7 · +2,73 · 2,35 · 300 | +8,2 · +1,10 · 1,17 · 2600 |

**Não há mais um stop que ganhe em tudo:** o de 150 mede melhor em 3 das 4 comparações (duas bases × duas carteiras) e o de 100 na outra. WINV26 · só A: t +2,18 com stop 150 contra +2,43 com 100. WINV26 · A + B: t +3,39 com stop 150 contra +2,73 com 100. WINFUT · só A: t +2,46 com stop 150 contra +1,82 com 100. WINFUT · A + B: t +1,68 com stop 150 contra +1,10 com 100.

O preço do stop curto é acerto: você é parado mais vezes, mas cada perda é menor.
E como a parcial acompanha o stop, trocar o stop troca as duas linhas de uma vez:
com stop 150 a parcial sai em +150 e o alvo cheio paga +225 por contrato de lote
cheio; com stop 100 a parcial sai em +100 e o alvo paga +200.

### A regra da parcial

| regra | stop | carteira | WINV26 · n / EV / t / zero | WINFUT · n / EV / t / zero |
|---|---|---|---|---|
| parcial na distância do stop · stop na média da operação | 150 | só A | 25 · +81,0 · +2,18 · 4% | 130 · +39,2 · +2,46 · 11% |
|  | 150 | **A + B** | 59 · +77,5 · +3,39 · 12% | 348 · +16,1 · +1,68 · 16% |
|  | 100 | só A | 25 · +68,0 · +2,43 · 12% | 130 · +21,5 · +1,82 · 18% |
|  | 100 | A + B | 60 · +51,7 · +2,73 · 17% | 352 · +8,2 · +1,10 · 22% |
| parcial em +100 · stop na média da operação | 150 | só A | 25 · +64,0 · +2,13 · 12% | 130 · +25,0 · +1,89 · 22% |
|  | 150 | A + B | 59 · +65,3 · +3,25 · 17% | 349 · +13,0 · +1,52 · 28% |
|  | 100 | só A | 25 · +68,0 · +2,43 · 12% | 130 · +21,5 · +1,82 · 18% |
|  | 100 | A + B | 60 · +51,7 · +2,73 · 17% | 352 · +8,2 · +1,10 · 22% |
| parcial em +100 · stop na entrada (o modelo antigo) | 150 | só A | 25 · +52,0 · +1,71 · 24% | 130 · +20,8 · +1,59 · 32% |
|  | 150 | A + B | 59 · +48,3 · +2,48 · 34% | 351 · +12,1 · +1,49 · 38% |
|  | 100 | só A | 25 · +56,0 · +2,05 · 24% | 130 · +16,5 · +1,48 · 27% |
|  | 100 | A + B | 60 · +40,0 · +2,33 · 30% | 354 · +6,8 · +0,99 · 31% |

**A regra da parcial estava modelada errado, e o conserto muda os números.** Com a parcial na distância do stop e o stop do restante na média da operação, o stop **nunca anda** e o trade que volta morre em zero — não em +50. No WINV26, com stop 150: +77,5 de EV e t +3,39 pela regra certa, contra +48,3 e t +2,48 pelo modelo antigo — e o desfecho "zero a zero" cai de 34% para 12% dos trades, porque agora ele é zero de verdade e não +50 pontos. No WINFUT, com stop 150: +16,1 de EV e t +1,68 pela regra certa, contra +12,1 e t +1,49 pelo modelo antigo — e o desfecho "zero a zero" cai de 38% para 16% dos trades, porque agora ele é zero de verdade e não +50 pontos.

---

## 8. Carteira — uma posição por vez (stop 150)

### WINV26

| | n | /pregão | EV | total | acerto | t | PF | DD |
|---|---|---|---|---|---|---|---|---|
| só A | 25 | 2,1 | +81,0 | +2.025 | 60,0% | +2,18 | 2,50 | 300 |
| **A + B** — padrão | 59 | 4,5 | +77,5 | +4.575 | 55,9% | +3,39 | 2,61 | 450 |
| A + B + C | 65 | 5,0 | +62,3 | +4.050 | 52,3% | +2,87 | 2,12 | 450 |

### WINFUT

| | n | /pregão | EV | total | acerto | t | PF | DD |
|---|---|---|---|---|---|---|---|---|
| só A | 130 | 1,8 | +39,2 | +5.100 | 46,2% | +2,46 | 1,61 | 1125 |
| **A + B** — padrão | 348 | 3,7 | +16,1 | +5.615 | 38,2% | +1,68 | 1,23 | 2475 |
| A + B + C | 393 | 3,9 | +12,4 | +4.865 | 37,4% | +1,41 | 1,17 | 2625 |

Se o seu limite é drawdown, é **só A**; se é aproveitar o dia, é **A + B**.
Adicionar C piora tudo nas duas bases.

---

## 9. Alvo e parcial

EV em pontos, carteira A + B, com a **parcial acompanhando o stop de cada linha**.
**Negrito** = melhor da linha.

### WINV26

| stop \ alvo | +200 | +300 | +400 | +500 |
|---|---|---|---|---|
| 100 | +39,2 | **+51,7** | +37,9 | +34,1 |
| 150 | +61,4 | **+77,5** | +62,1 | +39,3 |
| 200 | +78,0 | **+91,5** | +83,1 | +55,9 |

### WINFUT

| stop \ alvo | +200 | +300 | +400 | +500 |
|---|---|---|---|---|
| 100 | **+8,3** | +8,2 | +3,5 | +2,1 |
| 150 | +15,6 | **+16,1** | +12,9 | +9,4 |
| 200 | +26,3 | **+31,2** | +30,7 | +29,5 |

**O alvo de 300 é o melhor da linha em 5 das 6 linhas.** Exceções: WINFUT · stop 100 prefere +200 (+8,3 contra +8,2) — diferenças pequenas perto do ruído desta amostra.

---

## 10. Entrada, fora da amostra e custos

### Tipo de entrada (carteira A + B, stop 150)

| | WINV26 | WINFUT |
|---|---|---|
| limitada no meio do candle | +77,5 · t +3,39 | +16,1 · t +1,68 |
| a mercado no fechamento | +56,8 · t +2,57 | +18,1 · t +2,20 |

As duas se dividem: cada uma ganha em uma base. No WINV26, 66 trades a mercado contra 59 pela limitada (t +2,57 contra +3,39). No WINFUT, 402 trades a mercado contra 348 pela limitada (t +2,20 contra +1,68).

Isso **não** quer dizer trocar a limitada pela ordem a mercado: as duas linhas
medem carteiras diferentes — a mercado faz ~15% mais trades porque nunca
aborta. Quer dizer que **perder o preenchimento não é valor esperado perdido**,
e que entrar a mercado no fechamento é um plano B legítimo se você preferir
volume de operações a preço de entrada.

### Fora da amostra (WINFUT)

Todo parâmetro foi escolhido olhando a janela de 30/06/2026 a 28/08/2026 — a do WINFUT antigo,
que contém o WINV26. O arquivo novo acrescenta pregões antes e depois dela, e
eles são o único teste fora da amostra que existe aqui. Os trades são simulados
na base inteira e só depois separados pelo pregão do sinal.

**A vantagem não se repetiu fora da amostra.** Todos os parâmetros foram escolhidos olhando os pregões de 30/06/2026 a 28/08/2026. O WINFUT novo tem **58 pregões fora dessa janela** — 49 antes e 9 depois — que nunca foram vistos ao calibrar. Com stop 150: dentro da janela, só A dá 54 trades, EV +80,6, t +3,12 e A + B dá 151 trades, EV +44,1, t +2,97; **fora dela, só A dá 76 trades, EV +9,9, t +0,51 e A + B dá 197 trades, EV -5,3, t -0,45**. O setup B isolado, fora: 128 trades, EV -15,2, t -0,98. O setup A se divide: 57 trades, EV -10,5, t -0,47 antes da janela (49 pregões) e 19 trades, EV +71,1, t +2,36 depois (9 pregões) — o trecho posterior é curto demais para desempatar.

#### Stop 150

| | n | /pregão | EV | total | acerto | t | PF | DD |
|---|---|---|---|---|---|---|---|---|
| só A · antes da janela (49 pregões) | 57 | 1,7 | -10,5 | -600 | 31,6% | -0,47 | 0,87 | 1125 |
| só A · dentro da janela (calibração) (44 pregões) | 54 | 1,6 | +80,6 | +4.350 | 59,3% | +3,12 | 2,53 | 300 |
| só A · depois da janela (9 pregões) | 19 | 2,7 | +71,1 | +1.350 | 52,6% | +2,36 | 2,50 | 300 |
| só A · **fora da janela — antes + depois** (58 pregões) | 76 | 1,9 | +9,9 | +750 | 36,8% | +0,51 | 1,14 | 1425 |
| A + B · antes da janela (49 pregões) | 152 | 3,5 | -10,9 | -1.650 | 30,3% | -0,90 | 0,86 | 2475 |
| A + B · dentro da janela (calibração) (44 pregões) | 151 | 3,6 | +44,1 | +6.665 | 47,0% | +2,97 | 1,73 | 1575 |
| A + B · depois da janela (9 pregões) | 45 | 5,0 | +13,3 | +600 | 35,6% | +0,40 | 1,20 | 1350 |
| A + B · **fora da janela — antes + depois** (58 pregões) | 197 | 3,7 | -5,3 | -1.050 | 31,5% | -0,45 | 0,93 | 2475 |
| só A · custo 5 · antes da janela (49 pregões) | 57 | 1,7 | -15,5 | -885 | 31,6% | -0,69 | 0,82 | 1275 |
| só A · custo 5 · dentro da janela (calibração) (44 pregões) | 54 | 1,6 | +75,6 | +4.080 | 59,3% | +2,95 | 2,38 | 335 |
| só A · custo 5 · depois da janela (9 pregões) | 19 | 2,7 | +66,1 | +1.255 | 52,6% | +2,15 | 2,33 | 315 |
| só A · custo 5 · **fora da janela — antes + depois** (58 pregões) | 76 | 1,9 | +4,9 | +370 | 36,8% | +0,25 | 1,06 | 1595 |
| setup B isolado · antes da janela (49 pregões) | 102 | 2,4 | -11,8 | -1.200 | 29,4% | -0,76 | 0,85 | 2325 |
| setup B isolado · dentro da janela (calibração) (44 pregões) | 105 | 2,6 | +21,3 | +2.240 | 40,0% | +1,24 | 1,32 | 1725 |
| setup B isolado · depois da janela (9 pregões) | 26 | 3,2 | -28,8 | -750 | 23,1% | -0,59 | 0,64 | 1575 |
| setup B isolado · **fora da janela — antes + depois** (58 pregões) | 128 | 2,5 | -15,2 | -1.950 | 28,1% | -0,98 | 0,81 | 2625 |

#### Stop 100

| | n | /pregão | EV | total | acerto | t | PF | DD |
|---|---|---|---|---|---|---|---|---|
| só A · antes da janela (49 pregões) | 57 | 1,7 | -8,8 | -500 | 22,8% | -0,57 | 0,84 | 1100 |
| só A · dentro da janela (calibração) (44 pregões) | 54 | 1,6 | +46,3 | +2.500 | 44,4% | +2,25 | 2,09 | 400 |
| só A · depois da janela (9 pregões) | 19 | 2,7 | +42,1 | +800 | 42,1% | +1,62 | 2,00 | 300 |
| só A · **fora da janela — antes + depois** (58 pregões) | 76 | 1,9 | +3,9 | +300 | 27,6% | +0,29 | 1,08 | 1300 |
| A + B · antes da janela (49 pregões) | 155 | 3,5 | -8,4 | -1.300 | 22,6% | -0,86 | 0,84 | 2600 |
| A + B · dentro da janela (calibração) (44 pregões) | 152 | 3,6 | +29,6 | +4.500 | 36,2% | +2,42 | 1,69 | 1500 |
| A + B · depois da janela (9 pregões) | 45 | 5,0 | -6,7 | -300 | 24,4% | -0,32 | 0,88 | 900 |
| A + B · **fora da janela — antes + depois** (58 pregões) | 200 | 3,8 | -8,0 | -1.600 | 23,0% | -0,92 | 0,85 | 3000 |
| só A · custo 5 · antes da janela (49 pregões) | 57 | 1,7 | -13,8 | -785 | 22,8% | -0,89 | 0,76 | 1240 |
| só A · custo 5 · dentro da janela (calibração) (44 pregões) | 54 | 1,6 | +41,3 | +2.230 | 44,4% | +2,02 | 1,91 | 450 |
| só A · custo 5 · depois da janela (9 pregões) | 19 | 2,7 | +37,1 | +705 | 42,1% | +1,41 | 1,82 | 315 |
| só A · custo 5 · **fora da janela — antes + depois** (58 pregões) | 76 | 1,9 | -1,1 | -80 | 27,6% | -0,08 | 0,98 | 1475 |
| setup B isolado · antes da janela (49 pregões) | 102 | 2,4 | -9,8 | -1.000 | 21,6% | -0,82 | 0,81 | 2000 |
| setup B isolado · dentro da janela (calibração) (44 pregões) | 105 | 2,6 | +22,9 | +2.400 | 32,4% | +1,95 | 1,55 | 900 |
| setup B isolado · depois da janela (9 pregões) | 26 | 3,2 | -42,3 | -1.100 | 11,5% | -1,82 | 0,35 | 1200 |
| setup B isolado · **fora da janela — antes + depois** (58 pregões) | 128 | 2,5 | -16,4 | -2.100 | 19,5% | -1,53 | 0,70 | 2700 |

#### Mês a mês (carteira A + B, stop 150)

| mês | n | EV | total | acerto |
|---|---|---|---|---|
| 2026-04 — **fora da amostra** | 28 | +2,7 | +75 | 32,1% |
| 2026-05 — **fora da amostra** | 51 | +5,9 | +300 | 35,3% |
| 2026-06 — **parte fora da amostra (73 de 75 trades)** | 75 | -26,0 | -1.950 | 26,7% |
| 2026-07 | 65 | +45,9 | +2.981 | 46,2% |
| 2026-08 — **parte fora da amostra (5 de 89 trades)** | 89 | +39,7 | +3.534 | 46,1% |
| 2026-09 — **fora da amostra** | 40 | +16,9 | +675 | 37,5% |

**Não é um walk-forward**: é um corte só, e o trecho depois da janela é curto.
Mas é a primeira vez que a estratégia encontra dados que não participaram de
nenhuma escolha — e é o número que deveria pesar mais.

### Custos (carteira A + B, stop 150)

| custo | WINV26 · EV / t | WINFUT · EV / t |
|---|---|---|
| 0 pts | +77,5 · +3,39 | +16,1 · +1,68 |
| 5 pts | +72,5 · +3,21 | +11,1 · +1,17 |
| 10 pts | +67,5 · +3,02 | +6,1 · +0,65 |
| 20 pts | +57,5 · +2,63 | -3,9 · -0,41 |

A ~5 trades por pregão o custo é uma fração material do EV, não um detalhe. E há
um custo que **não** está aqui: a ordem limitada é assumida preenchida a preço
exato assim que o preço toca o nível. Na prática existe fila, e nem todo toque
preenche.

---

## 11. Ressalvas

- **Amostra pequena.** 102 pregões no WINFUT, 13 com trade no WINV26. Vários `t`
  ficam entre +1 e +2, que não é evidência forte. O setup C tem 6 e 48 trades — a
  conclusão sobre ele é "não há evidência a favor", não "está provado que perde".
- **As bases não são independentes.** WINFUT ⊃ WINV26 — e a janela do WINV26 é a de calibração.
- **Parâmetros varridos nas mesmas bases** — inclusive o período e a inclinação de
  cada média adaptativa. A comparação da § 5 carrega sobreajuste: cada família
  ganhou uma varredura própria.
- **O leque mínimo mede melhor quanto menor** e o toque na média é quase
  indiferente. O que carrega o setup A é o alinhamento das médias mais o gatilho a
  favor, não a geometria fina do pullback.
- **O filtro de "movimento rápido" do setup B é inerte** — o gatilho já exige
  índice ≥ 0,80 e o índice já contém o eixo do tempo.
- **Sem filtro de horário, rolagem ou vencimento.**

---

## 12. O que eu faria

1. **Não operar com dinheiro ainda.** Fora da janela de calibração a carteira A + B mede -5,3 de EV e o só A +9,9 (t +0,51; +4,9 com 5 pontos de custo). O resto desta lista vale como ajuste **dentro** de uma estratégia que ainda não provou vantagem — o próximo passo é entender o que os pregões de antes da janela têm de diferente, não afinar parâmetros.
2. **Manter o stop em 150.** O de 100 só mede melhor em 1 das 4 comparações (WINV26 · só A); nas outras o de 150 fica na frente. Com a fórmula nova do eixo [E2] o stop curto deixou de ser a escolha limpa que era com a antiga — e o ganho dele em risco por trade continua valendo, então é uma troca, não uma decisão óbvia.
3. **Só A tem o melhor EV por trade; A + B tem o melhor t.** O A entrega mais por operação e um drawdown menor; a carteira com B entrega mais no total e um resultado diário mais estável. No WINV26: só A dá +81,0 de EV com t +2,18 e DD 300; A + B dá +77,5 com t +3,39 e DD 450. No WINFUT: só A dá +39,2 de EV com t +2,46 e DD 1125; A + B dá +16,1 com t +1,68 e DD 2475.
4. **Manter as três EMAs como padrão.** Elas dão o melhor t em 2 das 4 combinações de base e stop; ficam atrás em WINFUT com stop 100 (ganha estilo Jurik 21), WINFUT com stop 150 (ganha estilo Jurik 21). E onde o empilhamento perde, quem aparece na frente é a aproximação de Jurik — que não é o JMA de verdade, então trocar o padrão por causa dela seria trocar por um indicador que não existe aqui.
5. **Manter o alvo em 300.**
6. **Não ligar o setup C.**
7. **Medir o custo real da corretora** e refazer a § 10 antes de dimensionar posição.
