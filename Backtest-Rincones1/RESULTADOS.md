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
| **WINFUT** | 19.993 | 44 (41 com trade) | 2026-06-30 a 2026-08-28 |

> **Elas não são independentes.** O WINFUT contém a janela inteira do WINV26 e
> mais julho. Quando as duas concordam, isso é menos confirmação do que parece.

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
| v1 · \|delta\| / \|Close-Open\| | 150 | setup A isolado | 31 · +89,5 · +3,17 · 2,85 | 74 · +65,9 · +3,42 · 2,25 |
|  | 150 | setup B isolado | 36 · +25,0 · +0,86 · 1,40 | 118 · +15,7 · +0,95 · 1,22 |
|  | 150 | carteira só A | 29 · +80,2 · +3,43 · 2,55 | 72 · +61,5 · +3,41 · 2,13 |
|  | 150 | carteira A + B | 63 · +44,0 · +1,81 · 1,74 | 184 · +28,8 · +2,14 · 1,44 |
|  | 100 | setup A isolado | 31 · +90,3 · +3,69 · 4,50 | 74 · +47,3 · +2,85 · 2,30 |
|  | 100 | setup B isolado | 36 · +25,0 · +1,24 · 1,60 | 118 · +22,2 · +2,05 · 1,51 |
|  | 100 | carteira só A | 29 · +82,8 · +4,20 · 4,00 | 72 · +43,1 · +2,86 · 2,15 |
|  | 100 | carteira A + B | 64 · +53,1 · +2,79 · 2,55 | 185 · +28,8 · +2,75 · 1,70 |
| v2 · (\|delta\|/esforço) × volta | 150 | setup A isolado | 26 · +86,5 · +2,42 · 2,67 | 54 · +80,6 · +3,11 · 2,53 |
|  | 150 | setup B isolado | 35 · +68,6 · +2,86 · 2,45 | 103 · +21,0 · +1,21 · 1,31 |
|  | 150 | carteira só A | 25 · +81,0 · +2,18 · 2,50 | 53 · +77,8 · +2,97 · 2,45 |
|  | 150 | **carteira A + B** | 59 · +77,5 · +3,39 · 2,61 | 148 · +43,0 · +2,84 · 1,71 |
|  | 100 | setup A isolado | 26 · +73,1 · +2,66 · 3,11 | 54 · +46,3 · +2,21 · 2,09 |
|  | 100 | setup B isolado | 35 · +40,0 · +2,10 · 2,00 | 103 · +22,3 · +1,89 · 1,53 |
|  | 100 | carteira só A | 25 · +68,0 · +2,43 · 2,89 | 53 · +43,4 · +2,08 · 2,00 |
|  | 100 | carteira A + B | 60 · +51,7 · +2,73 · 2,35 | 149 · +28,2 · +2,27 · 1,66 |

**A troca não melhora tudo: ela melhora a reversão.** A fórmula nova corta gatilhos (-11% e -17%) e mede melhor no **setup B em 3 das 4** células (duas bases × dois stops), no **setup A em 0 de 4** e na **carteira A + B em 2 de 4**. No WINV26 o setup B sai de +25,0 de EV e t +0,86 para +68,6 e t +2,86, e o A de +89,5 e t +3,17 para +86,5 e t +2,42 (stop 150). No WINFUT o setup B sai de +15,7 de EV e t +0,95 para +21,0 e t +1,21, e o A de +65,9 e t +3,42 para +80,6 e t +3,11 (stop 150). Faz sentido: o eixo novo mede **vaivém**, que é exaustão — e exaustão é exatamente o que o setup de reversão procura. O setup A é continuação: ali o vaivém informa menos, e o que a fórmula nova faz é sobretudo tirar sinal.

**O filtro continua valendo com a fórmula nova.** Ele existia porque a antiga media negativo quando o eixo do deslocamento mandava; não era óbvio que sobreviveria à troca, e sobreviveu. No WINV26, com o filtro: +77,5 de EV e t +3,39 em 59 trades; sem ele: +33,3 e t +1,53 em 115. No WINFUT, com o filtro: +43,0 de EV e t +2,84 em 148 trades; sem ele: +20,0 e t +1,62 em 299.

---

## 3. A regra da barra seguinte

A ordem limitada no meio do candle do gatilho vale por **uma barra**. Não
preencheu na barra seguinte, o trade é **abortado** -- não se persegue o preço,
não se deixa ordem esquecida no livro. Todo número deste arquivo já está sob
essa regra.

A regra descarta uma minoria estável dos sinais. No WINV26, **26 dos 29** sinais do setup A viraram trade (3 abortados, 10%); no B, 35 de 41 (15%). No WINFUT, **54 dos 60** sinais do setup A viraram trade (6 abortados, 10%); no B, 103 de 121 (15%). **Espere isso na tela:** cerca de um sinal em dez será abortado, e abortar é o comportamento correto, não uma falha sua.

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
| **A** — tendência | 54 | 1,7 | +80,6 | +4.350 | 59,3% | +3,11 | 2,53 | 300 |
| **B** — reversão rápida | 103 | 2,6 | +21,0 | +2.165 | 39,8% | +1,21 | 1,31 | 1725 |
| **C** — consolidação | 15 | 1,5 | -70,0 | -1.050 | 13,3% | -2,58 | 0,30 | 1125 |

**A prioridade que você pediu continua certa**: o setup de tendência lidera a maioria das colunas nas duas bases. Não todas — no WINV26 o setup B mede +2,86 de t contra +2,42 do A. Com esse número de trades uma coluna trocada é ruído, não hierarquia; o A segue prioritário por EV, fator de lucro e drawdown.

O setup C mede negativo nas duas, em toda configuração testada. Invertendo o
sinal sobram 0 e 8 trades: a combinação "médias emboladas **e** preço longe
delas" quase não existe. Fica desligado por padrão.

---

## 5. A média que dá a direção

Com média única a direção vira o **sinal da inclinação** dela nas últimas 5
barras, normalizada pelo range médio; o toque vira encostar nessa linha. Cada
família teve período e corte de inclinação varridos, e o valor escolhido foi o
que mede bem **nas duas bases**, não o pico de uma.

### Carteira só A · stop 150

| média | % barras em tendência | WINV26 · n / EV / t / PF | WINFUT · n / EV / t / PF |
|---|---|---|---|
| **3 EMAs 21/42/72** ← padrão | 80% | 25 · +81,0 · +2,18 · 2,50 | 53 · +77,8 · +2,97 · 2,45 |
| KAMA 13 | 48% | 14 · +64,3 · +1,00 · 2,00 | 30 · +55,0 · +1,39 · 1,85 |
| Hull 13 | 95% | 22 · +10,2 · +0,19 · 1,12 | 56 · +24,1 · +0,97 · 1,33 |
| T3 Tillson 13 | 92% | 23 · +45,7 · +1,01 · 1,64 | 51 · +42,6 · +1,62 · 1,63 |
| estilo Jurik 21 | 93% | 24 · +43,8 · +0,88 · 1,64 | 56 · +68,3 · +2,64 · 2,21 |

### Carteira só A · stop 100

| média | % barras em tendência | WINV26 · n / EV / t / PF | WINFUT · n / EV / t / PF |
|---|---|---|---|
| **3 EMAs 21/42/72** ← padrão | 80% | 25 · +68,0 · +2,43 · 2,89 | 53 · +43,4 · +2,08 · 2,00 |
| KAMA 13 | 48% | 14 · +64,3 · +1,38 · 2,80 | 30 · +33,3 · +1,19 · 1,71 |
| Hull 13 | 95% | 22 · +22,7 · +0,63 · 1,45 | 56 · +25,0 · +1,45 · 1,54 |
| T3 Tillson 13 | 92% | 23 · +43,5 · +1,39 · 2,00 | 51 · +25,5 · +1,31 · 1,52 |
| estilo Jurik 21 | 93% | 24 · +45,8 · +1,40 · 2,22 | 56 · +44,6 · +2,31 · 2,09 |

Com **stop 150** as três EMAs dão o melhor `t` nas **duas bases** (+2,18 e +2,97); a segunda colocada fica em +1,01 e +2,64. Com **stop 100** as três EMAs ganham no WINV26 (+2,43 contra +1,40 da segunda), mas a **estilo Jurik 21** passa à frente no WINFUT (+2,31 contra +2,08). Na base em que o empilhamento ganha, essa mesma média mede +1,40. A **KAMA** segue sendo a mais seletiva — classifica 48% das barras como tendência contra 80% do empilhamento, e produz cerca de metade dos trades.

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
| tocando alguma das três | 75,0% / 61,7% | 76,0% / 53,3% |
| **atrás** do leque, fora da tolerância | 1,7% / 4,3% | 1,6% / 3,3% |
| na frente — *exatamente o que a restrição corta* | 23,3% / 34,0% | 22,4% / 43,5% |

### Sem restrição — qualquer posição em relação às médias

| | gatilhos | stop | n | EV | t | PF | DD |
|---|---|---|---|---|---|---|---|
| WINV26 · setup B isolado | 94 | 150 | 35 | +68,6 | +2,86 | 2,45 | 450 |
| WINV26 · **carteira A + B** | 94 | 150 | 59 | +77,5 | +3,39 | 2,61 | 450 |
| WINV26 · setup B isolado | 94 | 100 | 35 | +40,0 | +2,10 | 2,00 | 300 |
| WINV26 · **carteira A + B** | 94 | 100 | 60 | +51,7 | +2,73 | 2,35 | 300 |
| WINFUT · setup B isolado | 246 | 150 | 103 | +21,0 | +1,21 | 1,31 | 1725 |
| WINFUT · **carteira A + B** | 246 | 150 | 148 | +43,0 | +2,84 | 1,71 | 1575 |
| WINFUT · setup B isolado | 246 | 100 | 103 | +22,3 | +1,89 | 1,53 | 900 |
| WINFUT · **carteira A + B** | 246 | 100 | 149 | +28,2 | +2,27 | 1,66 | 1500 |

### Só gatilho que toca ou fica atrás do leque

| | gatilhos | stop | n | EV | t | PF | DD |
|---|---|---|---|---|---|---|---|
| WINV26 · setup B isolado | 62 | 150 | 13 | +103,8 | +2,25 | 4,00 | 150 |
| WINV26 · **carteira A + B** | 62 | 150 | 38 | +88,8 | +2,61 | 2,88 | 450 |
| WINV26 · setup B isolado | 62 | 100 | 13 | +76,9 | +1,86 | 3,50 | 200 |
| WINV26 · **carteira A + B** | 62 | 100 | 38 | +71,1 | +2,44 | 3,08 | 300 |
| WINFUT · setup B isolado | 139 | 150 | 26 | +54,8 | +1,53 | 1,95 | 525 |
| WINFUT · **carteira A + B** | 139 | 150 | 78 | +73,1 | +3,29 | 2,36 | 525 |
| WINFUT · setup B isolado | 139 | 100 | 26 | +61,5 | +2,24 | 3,00 | 200 |
| WINFUT · **carteira A + B** | 139 | 100 | 78 | +50,0 | +2,61 | 2,26 | 400 |

**A restrição não mexe no A: ela reescreve o B.** Cortando 34,0% e 43,5% dos gatilhos, ela melhora o EV da carteira A + B em **4 das 4** células (duas bases × dois stops), o `t` em **2 de 4** e o drawdown em **2 de 4** (sem piorar em nenhuma). O setup A sai **idêntico** nas quatro — ele já exigia o toque, então já estava inteiro dentro da restrição. No WINV26 o setup B cai de 35 para 13 trades e o EV vai de +68,6 para +103,8 (t +2,86 → +2,25); a carteira A + B vai de +77,5 para +88,8 de EV, com o drawdown parado em 450 pontos. No WINFUT o setup B cai de 103 para 26 trades e o EV vai de +21,0 para +54,8 (t +1,21 → +1,53); a carteira A + B vai de +43,0 para +73,1 de EV, com o drawdown de 1575 para 525 pontos. O que sobra do B é o afastamento medido **no leque ou atrás dele**: mesmo lugar do A, direção oposta — quem decide é de que lado veio a agressão que falhou. O que ela joga fora é a esticada à frente das médias, que é exatamente onde a reversão é mais cara. A ressalva é de amostra: onde o `t` piora, ele piora porque a restrição tirou trade, não porque tirou vantagem — o EV sobe e o `t` cai junto com o n.

> **Por que ela não é o padrão.** Não é uma peneira nova de qualidade: é uma
> troca de carteira. Corta uma fatia grande dos gatilhos e quase todo o
> setup B, e o que sobra do B é pequeno demais para medir sozinho — o `t`
> cai onde o EV sobe, e isso é aritmética de amostra, não vantagem perdida.
> Com dois arquivos que se sobrepõem na maior parte da janela, promovê-la a
> padrão seria escolher a curva mais bonita de uma amostra pequena.

### As duas metades da restrição, separadas (carteira A + B)

| gatilhos aceitos | stop | WINV26 · gat / n / EV / t / DD | WINFUT · gat / n / EV / t / DD |
|---|---|---|---|
| sem restrição | 150 | 94 · 59 · +77,5 · +3,39 · 450 | 246 · 148 · +43,0 · +2,84 · 1575 |
| sem restrição | 100 | 94 · 60 · +51,7 · +2,73 · 300 | 246 · 149 · +28,2 · +2,27 · 1500 |
| só o toque no leque | 150 | 58 · 36 · +81,2 · +2,26 · 450 | 131 · 76 · +69,1 · +3,08 · 525 |
| só o toque no leque | 100 | 58 · 36 · +72,2 · +2,42 · 300 | 131 · 76 · +50,0 · +2,60 · 400 |
| só o que fica atrás do leque | 150 | 4 · 2 · +225,0 · — · 0 | 8 · 2 · +225,0 · — · 0 |
| só o que fica atrás do leque | 100 | 4 · 2 · +50,0 · — · 0 | 8 · 2 · +50,0 · — · 0 |
| **os dois — a variante** | 150 | 62 · 38 · +88,8 · +2,61 · 450 | 139 · 78 · +73,1 · +3,29 · 525 |
| **os dois — a variante** | 100 | 62 · 38 · +71,1 · +2,44 · 300 | 139 · 78 · +50,0 · +2,61 · 400 |

**A metade de trás do leque ajuda, mas não sempre.** Ela vale 4,3% e 3,3% dos gatilhos e melhora o EV em 2 das 4 células. WINV26: só o toque dá +81,2 de EV, com o de trás junto dá +88,8; WINFUT: só o toque dá +69,1 de EV, com o de trás junto dá +73,1. Nenhuma das duas leituras aguenta peso: sozinha, a metade de trás rende **2 e 2 trades** nas duas bases. O que a decomposição mostra com segurança é outra coisa — a restrição é, na prática, **quase toda** o toque. Com tolerância de um range médio, o preço que se afastou o bastante para deixar o leque inteiro para trás quase não acontece.

### A restrição nas cinco médias de regime (carteira A + B, stop 150)

| média | % barras tocando | WINV26 · sem / com | WINFUT · sem / com |
|---|---|---|---|
| **3 EMAs 21/42/72** ← padrão | 76,0% | 59 · +77,5 · +3,39 / 38 · +88,8 · +2,61 | 148 · +43,0 · +2,84 / 78 · +73,1 · +3,29 |
| KAMA 13 | 74,0% | 46 · +75,0 · +2,61 / 18 · +66,7 · +1,16 | 122 · +25,1 · +1,45 / 48 · +26,6 · +0,92 |
| Hull 13 | 99,0% | 31 · +36,3 · +0,82 / 31 · +36,3 · +0,82 | 78 · +25,0 · +1,11 / 78 · +25,0 · +1,11 |
| T3 Tillson 13 | 68,3% | 63 · +64,3 · +2,61 / 36 · +35,4 · +1,00 | 160 · +27,1 · +1,75 / 86 · +29,7 · +1,55 |
| estilo Jurik 21 | 90,0% | 62 · +46,0 · +1,62 / 36 · +20,8 · +0,59 | 151 · +24,3 · +1,52 / 102 · +13,9 · +0,82 |

**A restrição é uma propriedade do leque, não das médias em geral.** Em nenhuma família ela melhora o `t` nas duas bases ao mesmo tempo. Com as três EMAs — WINV26: +77,5 → +88,8 de EV (t +3,39 → +2,61); WINFUT: +43,0 → +73,1 de EV (t +2,84 → +3,29). Em Hull 13 a restrição é **inerte**: com média única e tolerância de um range médio, o preço encosta na linha quase sempre, e não sobra nada para cortar. “Atrás do leque” pressupõe um leque: três linhas separadas o bastante para haver um lado de cá e um de lá. Uma linha só não tem espessura, e a restrição vira outra coisa — um filtro do preço contra a inclinação.

---

## 7. O stop: 100 contra 150

| stop | carteira | WINV26 · EV / t / PF / DD | WINFUT · EV / t / PF / DD |
|---|---|---|---|
| 150 | só A | +81,0 · +2,18 · 2,50 · 300 | +77,8 · +2,97 · 2,45 · 300 |
| 150 | A + B | +77,5 · +3,39 · 2,61 · 450 | +43,0 · +2,84 · 1,71 · 1575 |
| **100** | só A | +68,0 · +2,43 · 2,89 · 200 | +43,4 · +2,08 · 2,00 · 400 |
| **100** | A + B | +51,7 · +2,73 · 2,35 · 300 | +28,2 · +2,27 · 1,66 · 1500 |

**Não há mais um stop que ganhe em tudo:** o de 150 mede melhor em 3 das 4 comparações (duas bases × duas carteiras) e o de 100 na outra. WINV26 · só A: t +2,18 com stop 150 contra +2,43 com 100. WINV26 · A + B: t +3,39 com stop 150 contra +2,73 com 100. WINFUT · só A: t +2,97 com stop 150 contra +2,08 com 100. WINFUT · A + B: t +2,84 com stop 150 contra +2,27 com 100.

O preço do stop curto é acerto: você é parado mais vezes, mas cada perda é menor.
E como a parcial acompanha o stop, trocar o stop troca as duas linhas de uma vez:
com stop 150 a parcial sai em +150 e o alvo cheio paga +225 por contrato de lote
cheio; com stop 100 a parcial sai em +100 e o alvo paga +200.

### A regra da parcial

| regra | stop | carteira | WINV26 · n / EV / t / zero | WINFUT · n / EV / t / zero |
|---|---|---|---|---|
| parcial na distância do stop · stop na média da operação | 150 | só A | 25 · +81,0 · +2,18 · 4% | 53 · +77,8 · +2,97 · 6% |
|  | 150 | **A + B** | 59 · +77,5 · +3,39 · 12% | 148 · +43,0 · +2,84 · 13% |
|  | 100 | só A | 25 · +68,0 · +2,43 · 12% | 53 · +43,4 · +2,08 · 13% |
|  | 100 | A + B | 60 · +51,7 · +2,73 · 17% | 149 · +28,2 · +2,27 · 21% |
| parcial em +100 · stop na média da operação | 150 | só A | 25 · +64,0 · +2,13 · 12% | 53 · +61,3 · +2,74 · 13% |
|  | 150 | A + B | 59 · +65,3 · +3,25 · 17% | 148 · +41,1 · +3,21 · 25% |
|  | 100 | só A | 25 · +68,0 · +2,43 · 12% | 53 · +43,4 · +2,08 · 13% |
|  | 100 | A + B | 60 · +51,7 · +2,73 · 17% | 149 · +28,2 · +2,27 · 21% |
| parcial em +100 · stop na entrada (o modelo antigo) | 150 | só A | 25 · +52,0 · +1,71 · 24% | 53 · +53,8 · +2,39 · 23% |
|  | 150 | A + B | 59 · +48,3 · +2,48 · 34% | 149 · +36,5 · +2,89 · 37% |
|  | 100 | só A | 25 · +56,0 · +2,05 · 24% | 53 · +38,7 · +1,91 · 21% |
|  | 100 | A + B | 60 · +40,0 · +2,33 · 30% | 150 · +26,0 · +2,33 · 31% |

**A regra da parcial estava modelada errado, e o conserto muda os números.** Com a parcial na distância do stop e o stop do restante na média da operação, o stop **nunca anda** e o trade que volta morre em zero — não em +50. No WINV26, com stop 150: +77,5 de EV e t +3,39 pela regra certa, contra +48,3 e t +2,48 pelo modelo antigo — e o desfecho "zero a zero" cai de 34% para 12% dos trades, porque agora ele é zero de verdade e não +50 pontos. No WINFUT, com stop 150: +43,0 de EV e t +2,84 pela regra certa, contra +36,5 e t +2,89 pelo modelo antigo — e o desfecho "zero a zero" cai de 37% para 13% dos trades, porque agora ele é zero de verdade e não +50 pontos.

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
| só A | 53 | 1,7 | +77,8 | +4.125 | 58,5% | +2,97 | 2,45 | 300 |
| **A + B** — padrão | 148 | 3,6 | +43,0 | +6.365 | 46,6% | +2,84 | 1,71 | 1575 |
| A + B + C | 163 | 3,8 | +32,6 | +5.315 | 43,6% | +2,34 | 1,51 | 1941 |

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
| 100 | +23,3 | **+28,2** | +21,1 | +16,1 |
| 150 | +33,7 | **+43,0** | +35,9 | +26,0 |
| 200 | +51,4 | **+63,3** | +61,0 | +46,6 |

**O alvo de 300 é o melhor da linha nas seis linhas das duas tabelas.** Não é um
pico isolado: 200 é pior, 400 e 500 são piores.

---

## 10. Entrada, fora da amostra e custos

### Tipo de entrada (carteira A + B, stop 150)

| | WINV26 | WINFUT |
|---|---|---|
| limitada no meio do candle | +77,5 · t +3,39 | +43,0 · t +2,84 |
| a mercado no fechamento | +56,8 · t +2,57 | +36,7 · t +2,72 |

**A limitada continua à frente** nas duas bases. No WINV26, 66 trades a mercado contra 59 pela limitada (t +2,57 contra +3,39). No WINFUT, 168 trades a mercado contra 148 pela limitada (t +2,72 contra +2,84).

Isso **não** quer dizer trocar a limitada pela ordem a mercado: as duas linhas
medem carteiras diferentes — a mercado faz ~15% mais trades porque nunca
aborta. Quer dizer que **perder o preenchimento não é valor esperado perdido**,
e que entrar a mercado no fechamento é um plano B legítimo se você preferir
volume de operações a preço de entrada.

### Mês a mês (WINFUT, carteira A + B)

| mês | n | EV | total | acerto |
|---|---|---|---|---|
| 2026-07 — **fora da amostra** | 65 | +45,9 | +2.981 | 46,2% |
| 2026-08 | 83 | +40,8 | +3.384 | 47,0% |

Julho é o único mês do WINFUT que não está no WINV26. **Não é um walk-forward**:
são dois meses, e os parâmetros foram varridos olhando os dois arquivos.

### Custos (carteira A + B, stop 150)

| custo | WINV26 · EV / t | WINFUT · EV / t |
|---|---|---|
| 0 pts | +77,5 · +3,39 | +43,0 · +2,84 |
| 5 pts | +72,5 · +3,21 | +38,0 · +2,53 |
| 10 pts | +67,5 · +3,02 | +33,0 · +2,22 |
| 20 pts | +57,5 · +2,63 | +23,0 · +1,57 |

A ~5 trades por pregão o custo é uma fração material do EV, não um detalhe. E há
um custo que **não** está aqui: a ordem limitada é assumida preenchida a preço
exato assim que o preço toca o nível. Na prática existe fila, e nem todo toque
preenche.

---

## 11. Ressalvas

- **Amostra pequena.** 44 pregões no WINFUT, 13 com trade no WINV26. Vários `t`
  ficam entre +1 e +2, que não é evidência forte. O setup C tem 7 e 19 trades — a
  conclusão sobre ele é "não há evidência a favor", não "está provado que perde".
- **As bases não são independentes.** WINFUT ⊃ WINV26.
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

1. **Manter o stop em 150.** O de 100 só mede melhor em 1 das 4 comparações (WINV26 · só A); nas outras o de 150 fica na frente. Com a fórmula nova do eixo [E2] o stop curto deixou de ser a escolha limpa que era com a antiga — e o ganho dele em risco por trade continua valendo, então é uma troca, não uma decisão óbvia.
2. **Só A tem o melhor EV por trade; A + B tem o melhor t.** O A entrega mais por operação e um drawdown menor; a carteira com B entrega mais no total e um resultado diário mais estável. No WINV26: só A dá +81,0 de EV com t +2,18 e DD 300; A + B dá +77,5 com t +3,39 e DD 450. No WINFUT: só A dá +77,8 de EV com t +2,97 e DD 300; A + B dá +43,0 com t +2,84 e DD 1575.
3. **Manter as três EMAs como padrão.** Elas dão o melhor t em 3 das 4 combinações de base e stop; ficam atrás em WINFUT com stop 100 (ganha estilo Jurik 21). E onde o empilhamento perde, quem aparece na frente é a aproximação de Jurik — que não é o JMA de verdade, então trocar o padrão por causa dela seria trocar por um indicador que não existe aqui.
4. **Manter o alvo em 300.**
5. **Não ligar o setup C.**
6. **Medir o custo real da corretora** e refazer a § 10 antes de dimensionar posição.
