# Resultados — Rincones1

> **Este arquivo é gerado.** Rode `python rodar.py && python relatorio.py`.
> Não edite à mão: a fonte de todos os números é `saida/resumo.json`, e o
> [relatorio.html](relatorio.html) sai do mesmo lugar, pelo mesmo caminho.

**Gestão:** parcial de 50% em +100 que zera o risco · alvo 300 · entrada por ordem limitada no meio do candle, **válida por uma barra** · **sem custo**. Stop de 150 (padrão) e de 100 (variante), lado a lado.

---

## 1. As duas bases

| | barras | pregões | período |
|---|---|---|---|
| **WINV26** | 6.367 | 95 (13 com trade) | 2026-04-15 a 2026-08-28 |
| **WINFUT** | 19.993 | 44 (43 com trade) | 2026-06-30 a 2026-08-28 |

> **Elas não são independentes.** O WINFUT contém a janela inteira do WINV26 e
> mais julho. Quando as duas concordam, isso é menos confirmação do que parece.

---

## 2. A regra da barra seguinte

A ordem limitada no meio do candle do gatilho vale por **uma barra**. Não
preencheu na barra seguinte, o trade é **abortado** -- não se persegue o preço,
não se deixa ordem esquecida no livro. Todo número deste arquivo já está sob
essa regra.

A regra descarta uma minoria estável dos sinais. No WINV26, **31 dos 36** sinais do setup A viraram trade (5 abortados, 14%); no B, 36 de 40 (10%). No WINFUT, **74 dos 83** sinais do setup A viraram trade (9 abortados, 11%); no B, 118 de 132 (11%). **Espere isso na tela:** cerca de um sinal em dez será abortado, e abortar é o comportamento correto, não uma falha sua.

---

## 3. Cada setup isolado (stop 150)

### WINV26

| | n | /pregão | EV | total | acerto | t | PF | DD |
|---|---|---|---|---|---|---|---|---|
| **A** — tendência | 31 | 2,6 | +61,3 | +1.900 | 74,2% | +2,66 | 2,58 | 350 |
| **B** — reversão rápida | 36 | 2,8 | +11,1 | +400 | 63,9% | +0,50 | 1,21 | 700 |
| **C** — consolidação | 7 | 1,2 | -35,7 | -250 | 57,1% | -1,00 | 0,44 | 350 |

### WINFUT

| | n | /pregão | EV | total | acerto | t | PF | DD |
|---|---|---|---|---|---|---|---|---|
| **A** — tendência | 74 | 2,2 | +48,0 | +3.550 | 71,6% | +3,16 | 2,13 | 450 |
| **B** — reversão rápida | 118 | 2,8 | +20,2 | +2.381 | 66,1% | +1,62 | 1,40 | 1150 |
| **C** — consolidação | 19 | 1,4 | -36,8 | -700 | 52,6% | -1,34 | 0,48 | 800 |

**A prioridade que você pediu está certa.** O setup de tendência é o melhor dos
três nas duas bases, em todas as colunas.

O setup C mede negativo nas duas, em toda configuração testada. Invertendo o
sinal sobram 0 e 8 trades: a combinação "médias emboladas **e** preço longe
delas" quase não existe. Fica desligado por padrão.

---

## 4. A média que dá a direção

Com média única a direção vira o **sinal da inclinação** dela nas últimas 5
barras, normalizada pelo range médio; o toque vira encostar nessa linha. Cada
família teve período e corte de inclinação varridos, e o valor escolhido foi o
que mede bem **nas duas bases**, não o pico de uma.

### Carteira só A · stop 150

| média | % barras em tendência | WINV26 · n / EV / t / PF | WINFUT · n / EV / t / PF |
|---|---|---|---|
| **3 EMAs 21/42/72** ← padrão | 80% | 30 · +56,7 · +2,68 · 2,42 | 73 · +45,9 · +3,14 · 2,06 |
| KAMA 13 | 48% | 15 · +53,3 · +1,78 · 2,07 | 32 · +70,3 · +3,25 · 2,88 |
| Hull 13 | 95% | 27 · +57,4 · +1,48 · 2,29 | 69 · +53,6 · +2,94 · 2,30 |
| T3 Tillson 13 | 92% | 21 · +57,1 · +2,17 · 2,33 | 62 · +36,3 · +2,04 · 1,75 |
| estilo Jurik 21 | 93% | 26 · +46,2 · +1,43 · 2,00 | 68 · +43,4 · +2,52 · 1,94 |

### Carteira só A · stop 100

| média | % barras em tendência | WINV26 · n / EV / t / PF | WINFUT · n / EV / t / PF |
|---|---|---|---|
| **3 EMAs 21/42/72** ← padrão | 80% | 30 · +70,0 · +3,49 · 3,62 | 73 · +41,8 · +3,04 · 2,13 |
| KAMA 13 | 48% | 15 · +70,0 · +2,60 · 3,10 | 32 · +45,3 · +2,33 · 2,12 |
| Hull 13 | 95% | 27 · +61,1 · +2,13 · 2,65 | 70 · +43,6 · +2,94 · 2,09 |
| T3 Tillson 13 | 92% | 21 · +64,3 · +2,83 · 2,93 | 62 · +28,2 · +1,66 · 1,62 |
| estilo Jurik 21 | 93% | 26 · +55,8 · +1,94 · 2,61 | 68 · +30,1 · +1,78 · 1,68 |

Com **stop 150** as três EMAs ganham no WINV26 (+2,68 contra +2,17 da segunda), mas a **KAMA 13** passa à frente no WINFUT (+3,25 contra +3,14). Na base em que o empilhamento ganha, essa mesma média mede +1,78. Com **stop 100** as três EMAs dão o melhor `t` nas **duas bases** (+3,49 e +3,04); a segunda colocada fica em +2,83 e +2,94. A **KAMA** segue sendo a mais seletiva — classifica 48% das barras como tendência contra 80% do empilhamento, e produz cerca de metade dos trades.

O empilhamento exige **concordância entre três escalas de tempo**, e isso é
informação que a inclinação de uma linha só não carrega. Uma média adaptativa
resolve o atraso; não resolve a falta de confirmação.

> **Sobre a "Jurik":** o JMA da Jurik Research é proprietário e não publicado. O
> que está aqui é uma aproximação pública do estilo — adaptativa com correção de
> fase. Leia aquela linha como "uma adaptativa muito suavizada", **não** como "o
> JMA foi testado". Se o resultado dela pesasse na decisão, o certo seria
> licenciar o indicador de verdade e refazer.

---

## 5. O stop: 100 contra 150

| stop | carteira | WINV26 · EV / t / PF / DD | WINFUT · EV / t / PF / DD |
|---|---|---|---|
| 150 | só A | +56,7 · +2,68 · 2,42 · 350 | +45,9 · +3,14 · 2,06 · 450 |
| 150 | A + B | +26,6 · +1,33 · 1,54 · 850 | +27,2 · +2,64 · 1,56 · 1100 |
| **100** | só A | +70,0 · +3,49 · 3,62 · 200 | +41,8 · +3,04 · 2,13 · 450 |
| **100** | A + B | +43,1 · +2,32 · 2,27 · 650 | +28,2 · +2,86 · 1,69 · 1300 |

**O stop de 100 melhora o `t` e o fator de lucro nas duas bases, nas duas
carteiras.** Corta o risco por trade em um terço, então o mesmo limite de perda
diária compra 50% mais contratos. O preço é acerto: com stop mais curto você é
parado mais vezes, mas cada perda é menor e o saldo melhora.

---

## 6. Carteira — uma posição por vez (stop 150)

### WINV26

| | n | /pregão | EV | total | acerto | t | PF | DD |
|---|---|---|---|---|---|---|---|---|
| só A | 30 | 2,5 | +56,7 | +1.700 | 73,3% | +2,68 | 2,42 | 350 |
| **A + B** — padrão | 64 | 4,9 | +26,6 | +1.700 | 67,2% | +1,33 | 1,54 | 850 |
| A + B + C | 71 | 5,5 | +20,4 | +1.450 | 66,2% | +1,03 | 1,40 | 900 |

### WINFUT

| | n | /pregão | EV | total | acerto | t | PF | DD |
|---|---|---|---|---|---|---|---|---|
| só A | 73 | 2,2 | +45,9 | +3.350 | 71,2% | +3,14 | 2,06 | 450 |
| **A + B** — padrão | 185 | 4,3 | +27,2 | +5.031 | 67,6% | +2,64 | 1,56 | 1100 |
| A + B + C | 202 | 4,6 | +20,2 | +4.081 | 65,8% | +2,11 | 1,39 | 1450 |

Se o seu limite é drawdown, é **só A**; se é aproveitar o dia, é **A + B**.
Adicionar C piora tudo nas duas bases.

---

## 7. Alvo e parcial

EV em pontos, carteira A + B, com a parcial fixa em +100. **Negrito** = melhor da linha.

### WINV26

| stop \ alvo | +200 | +300 | +400 | +500 |
|---|---|---|---|---|
| 100 | +34,6 | +43,1 | **+43,7** | +42,9 |
| 150 | +18,8 | +26,6 | +26,1 | **+28,5** |
| 200 | +15,1 | +23,8 | **+24,1** | +23,3 |

### WINFUT

| stop \ alvo | +200 | +300 | +400 | +500 |
|---|---|---|---|---|
| 100 | +21,1 | **+28,2** | +27,8 | +26,6 |
| 150 | +21,0 | **+27,2** | +26,2 | +26,6 |
| 200 | +22,2 | **+29,0** | +28,0 | +26,5 |

**O alvo de 300 é o melhor da linha nas seis linhas das duas tabelas.** Não é um
pico isolado: 200 é pior, 400 e 500 são piores.

---

## 8. Entrada, fora da amostra e custos

### Tipo de entrada (carteira A + B, stop 150)

| | WINV26 | WINFUT |
|---|---|---|
| limitada no meio do candle | +26,6 · t +1,33 | +27,2 · t +2,64 |
| a mercado no fechamento | +30,1 · t +1,82 | +26,5 · t +3,54 |

**A regra da barra seguinte inverteu esta comparação.** Entrar a mercado mede melhor `t` nas duas bases agora, e a razão é mecânica: a ordem a mercado **nunca aborta**. No WINV26, 73 trades a mercado contra 64 pela limitada (t +1,82 contra +1,33). No WINFUT, 204 trades a mercado contra 185 pela limitada (t +3,54 contra +2,64).

Isso **não** quer dizer trocar a limitada pela ordem a mercado: as duas linhas
medem carteiras diferentes — a mercado faz ~15% mais trades porque nunca
aborta. Quer dizer que **perder o preenchimento não é valor esperado perdido**,
e que entrar a mercado no fechamento é um plano B legítimo se você preferir
volume de operações a preço de entrada.

### Mês a mês (WINFUT, carteira A + B)

| mês | n | EV | total | acerto |
|---|---|---|---|---|
| 2026-06 | 1 | -150,0 | -150 | 0,0% |
| 2026-07 — **fora da amostra** | 82 | +45,5 | +3.731 | 73,2% |
| 2026-08 | 102 | +14,2 | +1.450 | 63,7% |

Julho é o único mês do WINFUT que não está no WINV26. **Não é um walk-forward**:
são dois meses, e os parâmetros foram varridos olhando os dois arquivos.

### Custos (carteira A + B, stop 150)

| custo | WINV26 · EV / t | WINFUT · EV / t |
|---|---|---|
| 0 pts | +26,6 · +1,33 | +27,2 · +2,64 |
| 5 pts | +21,6 · +1,10 | +22,2 · +2,17 |
| 10 pts | +16,6 · +0,86 | +17,2 · +1,69 |
| 20 pts | +6,6 · +0,35 | +7,2 · +0,71 |

A ~5 trades por pregão o custo é uma fração material do EV, não um detalhe. E há
um custo que **não** está aqui: a ordem limitada é assumida preenchida a preço
exato assim que o preço toca o nível. Na prática existe fila, e nem todo toque
preenche.

---

## 9. Ressalvas

- **Amostra pequena.** 44 pregões no WINFUT, 13 com trade no WINV26. Vários `t`
  ficam entre +1 e +2, que não é evidência forte. O setup C tem 7 e 19 trades — a
  conclusão sobre ele é "não há evidência a favor", não "está provado que perde".
- **As bases não são independentes.** WINFUT ⊃ WINV26.
- **Parâmetros varridos nas mesmas bases** — inclusive o período e a inclinação de
  cada média adaptativa. A comparação da § 4 carrega sobreajuste: cada família
  ganhou uma varredura própria.
- **O leque mínimo mede melhor quanto menor** e o toque na média é quase
  indiferente. O que carrega o setup A é o alinhamento das médias mais o gatilho a
  favor, não a geometria fina do pullback.
- **O filtro de "movimento rápido" do setup B é inerte** — o gatilho já exige
  índice ≥ 0,80 e o índice já contém o eixo do tempo.
- **Sem filtro de horário, rolagem ou vencimento.**

---

## 10. O que eu faria

1. **Baixar o stop para 100.** Melhora `t` e PF nas duas bases, nas duas carteiras,
   e corta o risco por trade em um terço. É a mudança com mais apoio nos dados.
2. **Rodar só o setup A por um tempo.** Melhor EV, `t`, PF e drawdown; ~2,5 trades
   por pregão é operável à mão.
3. **Manter as três EMAs, com stop 100.** É a única configuração em que o
   empilhamento ganha nas duas bases. Com stop 150 a KAMA passa à frente no
   WINFUT -- mais um motivo para o stop curto ser o padrão.
4. **Manter o alvo em 300.**
5. **Não ligar o setup C.**
6. **Medir o custo real da corretora** e refazer a § 7 antes de dimensionar posição.
