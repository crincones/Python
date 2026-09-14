# Resultados — Backtest-Rincones1-DTA

> **Gerado por `python rodar.py && python relatorio.py`.** Não edite à mão: todo número aqui sai de `saida/resumo.json`, e as conclusões são calculadas a partir dele. A mesma medição em HTML, com o visualizador de trades, está em [relatorio.html](relatorio.html).

Contexto: **EMA 21** (tendência) · **Hull 50** (força) · **Keltner 2,0 e 3,0 ATRs** (esticamento). Gatilho: `Ticks_Esforco_Hist_v2.ntsl` nas configurações padrão dele, índice ≥ **0,80**. Gestão: stop **0,75 × ATR**, parcial de **50%** na mesma distância do stop, stop do restante na média da operação, alvo **300 pontos**. Entrada limitada no meio do candle do gatilho, válida por **1** barra.

## 1. O resultado

**WINV26** — 6367 barras · 95 pregões no arquivo (14 com pregão cheio) · 2026-04-15 a 2026-08-28 · ATR mediano 130 pontos

| | n | /pregão | EV | R | total | acerto | t | dias+ | PF | DD |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| só D | 71 | 5,5 | +59,5 | +0,56 | +4.221 | 54,9% | +2,52 | 69% | 2,90 | 605 |
| **D + T** — padrão | 82 | 6,3 | +58,4 | +0,57 | +4.785 | 56,1% | +3,04 | 85% | 2,82 | 669 |
| D + T + K | 102 | 7,8 | +46,9 | +0,45 | +4.780 | 52,9% | +2,60 | 77% | 2,32 | 1.036 |
| D + T + K + KB | 130 | 10,0 | +41,7 | +0,42 | +5.425 | 51,5% | +2,44 | 54% | 2,09 | 1.014 |

**WINFUT** — 19993 barras · 44 pregões no arquivo (44 com pregão cheio) · 2026-06-30 a 2026-08-28 · ATR mediano 122 pontos

| | n | /pregão | EV | R | total | acerto | t | dias+ | PF | DD |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| só D | 184 | 4,3 | +33,8 | +0,33 | +6.211 | 48,4% | +2,58 | 60% | 1,90 | 856 |
| **D + T** — padrão | 206 | 4,8 | +32,8 | +0,33 | +6.750 | 48,1% | +2,89 | 63% | 1,85 | 823 |
| D + T + K | 262 | 6,0 | +24,3 | +0,25 | +6.373 | 45,4% | +2,38 | 59% | 1,61 | 1.393 |
| D + T + K + KB | 332 | 7,5 | +18,5 | +0,18 | +6.130 | 44,0% | +1,99 | 55% | 1,45 | 1.700 |

## 2. De que lado da Hull vale entrar

Duas distâncias, assinadas pelo lado do trade:

```
dh = sinal × (close − Hull 50) / ATR      dh < 0 = lado oposto ao da Hull
de = sinal × (close − EMA 21) / ATR
```

### Os baldes

| | n · V26 | EV | t | n · FUT | EV | t |
|---|--:|--:|--:|--:|--:|--:|
| close do lado OPOSTO da Hull  (o setup D) | 139 | +43,8 | +2,50 | 364 | +18,4 | +1,95 |
| close do lado da Hull  (a leitura clássica) | 37 | +2,5 | +0,08 | 103 | +3,6 | +0,27 |
| lado oposto + Hull não plana | 131 | +50,3 | +2,86 | 340 | +21,6 | +2,26 |
| lado da Hull + Hull não plana | 37 | +2,5 | +0,08 | 95 | +9,1 | +0,62 |
| Hull PLANA — sem intensidade | 8 | -62,3 | -1,14 | 32 | -35,1 | -1,85 |
| Hull não plana | 168 | +39,8 | +2,39 | 435 | +18,8 | +2,25 |
| lado oposto + não plana + mergulho até 1,5 ATR | 79 | +67,0 | +2,87 | 198 | +35,4 | +2,65 |

### Por faixa de dh

| | n · V26 | EV | t | n · FUT | EV | t |
|---|--:|--:|--:|--:|--:|--:|
| dh < −2 | 39 | +48,9 | +1,97 | 91 | +21,5 | +1,54 |
| −2 ≤ dh < −1 | 55 | +26,3 | +1,35 | 153 | +8,0 | +0,76 |
| −1 ≤ dh < −0,3 | 33 | +68,3 | +2,59 | 93 | +28,2 | +1,72 |
| −0,3 ≤ dh < +0,3 | 19 | +18,2 | +0,55 | 49 | +33,3 | +1,73 |
| +0,3 ≤ dh < +1 | 18 | +8,4 | +0,19 | 47 | +6,2 | +0,29 |
| +1 ≤ dh < +2 | 11 | +17,3 | +0,39 | 25 | -14,6 | -0,64 |
| dh ≥ +2 | 1 | — | — | 9 | -32,3 | -0,76 |

### Pela inclinação da Hull

| | n · V26 | EV | t | n · FUT | EV | t |
|---|--:|--:|--:|--:|--:|--:|
| Hull contra o trade, forte | 91 | +49,5 | +2,50 | 238 | +20,2 | +1,99 |
| Hull contra o trade, fraca | 13 | +35,3 | +1,87 | 32 | +33,6 | +1,51 |
| Hull PLANA | 8 | -62,3 | -1,14 | 32 | -35,1 | -1,85 |
| Hull a favor, fraca | 12 | +6,2 | +0,18 | 27 | +21,1 | +0,92 |
| Hull a favor, forte | 52 | +31,8 | +1,33 | 138 | +12,7 | +1,12 |

Com a Hull inclinada, entrar pelo lado **oposto** mede +50,3 por trade contra +2,5 do lado clássico no WINV26 — **48 pontos** de diferença — e +21,6 contra +9,1 no WINFUT, **13 pontos**. O sinal do `t` concorda nos dois: +2,86 e +2,26 do lado oposto, +0,08 e +0,62 do lado clássico.

A *direção* da Hull importa muito menos que o fato de ela estar inclinada. Contra o trade e forte: +49,5 / +20,2. A favor e forte: +31,8 / +12,7. Plana: **-62,3** / **-35,1**. O veto é a inclinação, não o sentido dela — e é por isso que o setup D não exige que a Hull aponte para lado nenhum.

## 3. Os setups

| setup | | sinais V26 | n | EV | t | sinais FUT | n | EV | t |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|
| **D** | descolamento da Hull (ligado) | 89 | 79 | +67,0 | +2,87 | 229 | 198 | +35,4 | +2,65 |
| **T** | tendencia com forca (ligado) | 14 | 14 | +19,2 | +0,37 | 28 | 26 | +9,4 | +0,30 |
| **K** | rejeicao da banda (desligado) | 24 | 21 | +9,7 | +0,32 | 74 | 63 | +2,7 | +0,21 |
| **KB** | banda classica (desligado) | 33 | 30 | +15,8 | +0,64 | 92 | 78 | -1,1 | -0,08 |

- **D · descolamento da Hull** — O close no lado *oposto* ao da Hull, a Hull com inclinação, o preço dentro do canal e o mergulho limitado. Alguém agrediu a favor do movimento e falhou; o trade vai contra quem agrediu.
- **T · tendência com força** — A leitura clássica, restrita ao pullback: Hull e EMA no sentido do trade, close do lado certo da Hull e preço ainda não esticado. Raro, e positivo.
- **K · rejeição da banda** — O pavio fura a banda de 2 ATRs e o candle fecha de volta para dentro. Mede positivo sozinho — e mesmo assim piora a carteira.
- **KB · banda clássica** — Preço parado na zona de esticamento, entrada contra. É o uso de manual do canal, e mede negativo no WINFUT em toda configuração testada.

O **K** é o caso que vale entender: isolado ele mede +9,7 / +2,7 — positivo nos dois — e mesmo assim, entrando na carteira, o EV cai de +58,4 para +46,9 no WINV26 e de +32,8 para +24,3 no WINFUT. Ele não perde dinheiro: ele *ocupa a vaga* de um trade melhor, porque só uma posição fica aberta por vez.

## 4. O nível do gatilho

| nível | gatilhos V26 | n | /pregão | EV | R | t | gatilhos FUT | n | /pregão | EV | R | t |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 0,55 | 755 | 219 | 16,9 | +25,8 | +0,25 | +2,60 | 2342 | 684 | 15,6 | +8,4 | +0,08 | +1,70 |
| 0,60 | 663 | 198 | 15,2 | +24,1 | +0,24 | +2,06 | 2008 | 615 | 14,0 | +8,0 | +0,07 | +1,39 |
| 0,70 | 389 | 134 | 10,3 | +30,5 | +0,30 | +2,29 | 1135 | 385 | 8,8 | +18,3 | +0,19 | +2,73 |
| 0,75 | 296 | 106 | 8,2 | +42,6 | +0,41 | +2,74 | 850 | 300 | 6,8 | +20,7 | +0,21 | +2,64 |
| 0,80 ← | 202 | 82 | 6,3 | +58,4 | +0,57 | +3,04 | 547 | 206 | 4,8 | +32,8 | +0,33 | +2,89 |
| 0,85 | 144 | 66 | 5,1 | +70,3 | +0,71 | +4,09 | 404 | 155 | 3,6 | +41,7 | +0,44 | +3,17 |
| 0,90 | 86 | 40 | 3,1 | +71,1 | +0,71 | +3,57 | 229 | 88 | 2,2 | +38,2 | +0,39 | +2,45 |

No corte de cor do indicador (0,55) a carteira mede +25,8 / +8,4 por trade, com 16,9 e 15,6 trades por pregão — positivo, mas fraco e cansativo. No nível adotado (0,80) mede +58,4 / +32,8 com 6,3 e 4,8 por pregão. Em 0,90, +71,1 / +38,2 — melhor ainda por trade, e com metade dos sinais. A vantagem cresce com o nível em *todas* as células, nos dois arquivos: é o padrão que o próprio indicador prevê, já que ele mede absorção e absorção fraca não se desfaz.

## 5. O canal de Keltner

| zona | barras V26 | gatilhos V26 | barras FUT | gatilhos FUT |
|---|--:|--:|--:|--:|
| dentro do canal | 83,7% | 81,7% | 84,8% | 81,2% |
| entre 2,0 e 3,0 ATR | 13,5% | 13,9% | 12,7% | 16,6% |
| além de 3,0 ATR | 2,8% | 4,5% | 2,4% | 2,2% |

O veto de zona, ligado e desligado:

| | n | /pregão | EV | R | total | acerto | t | dias+ | PF | DD |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| WINV26 · com o veto — o padrão | 82 | 6,3 | +58,4 | +0,57 | +4.785 | 56,1% | +3,04 | 85% | 2,82 | 669 |
| WINV26 · sem o veto | 82 | 6,3 | +58,4 | +0,57 | +4.785 | 56,1% | +3,04 | 85% | 2,82 | 669 |
| WINFUT · com o veto — o padrão | 206 | 4,8 | +32,8 | +0,33 | +6.750 | 48,1% | +2,89 | 63% | 1,85 | 823 |
| WINFUT · sem o veto | 206 | 4,8 | +32,8 | +0,33 | +6.750 | 48,1% | +2,89 | 63% | 1,85 | 823 |

O veto de zona é inerte: a carteira mede +58,4 / +32,8 com ele e +58,4 / +32,8 sem ele. E a leitura clássica da banda — preço esticado, entrada contra — mede +15,8 no WINV26 e **-1,1** no WINFUT. A faixa de 2 a 3 ATRs, que era a aposta inicial, é *onde o operacional não opera*, não onde ele ganha.

## 6. A gestão

| | n | /pregão | EV | R | total | acerto | t | dias+ | PF | DD |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| WINV26 · stop 150 fixo · alvo 300 — a herdada do Rincones1 | 79 | 6,1 | +69,3 | +0,46 | +5.475 | 54,4% | +2,75 | 77% | 2,30 | 975 |
| WINV26 · stop 100 fixo · alvo 300 | 81 | 6,2 | +56,8 | +0,57 | +4.600 | 46,9% | +2,66 | 77% | 2,53 | 800 |
| WINV26 · stop 0,75 × ATR · alvo 300 — o padrão daqui | 82 | 6,3 | +58,4 | +0,57 | +4.785 | 56,1% | +3,04 | 85% | 2,82 | 669 |
| WINV26 · stop 1,50 × ATR · alvo 300 | 76 | 5,8 | +104,6 | +0,52 | +7.950 | 68,4% | +3,48 | 77% | 2,85 | 710 |
| WINV26 · stop 0,75 × ATR · alvo 3 R | 83 | 6,4 | +54,2 | +0,53 | +4.498 | 56,6% | +2,81 | 85% | 2,71 | 691 |
| WINFUT · stop 150 fixo · alvo 300 — a herdada do Rincones1 | 200 | 4,7 | +30,6 | +0,20 | +6.124 | 43,5% | +2,09 | 65% | 1,46 | 1.725 |
| WINFUT · stop 100 fixo · alvo 300 | 205 | 4,8 | +27,8 | +0,28 | +5.699 | 36,1% | +2,26 | 51% | 1,63 | 1.101 |
| WINFUT · stop 0,75 × ATR · alvo 300 — o padrão daqui | 206 | 4,8 | +32,8 | +0,33 | +6.750 | 48,1% | +2,89 | 63% | 1,85 | 823 |
| WINFUT · stop 1,50 × ATR · alvo 300 | 196 | 4,6 | +49,9 | +0,25 | +9.780 | 54,6% | +2,81 | 70% | 1,69 | 1.491 |
| WINFUT · stop 0,75 × ATR · alvo 3 R | 208 | 4,8 | +31,9 | +0,33 | +6.634 | 49,5% | +2,93 | 67% | 1,84 | 742 |

Em pontos, o stop largo parece melhor — +104,6 contra +69,3 no WINV26. Em **R**, que é o que dá para comparar, o quadro inverte: +0,57 contra +0,52 no WINV26 e +0,33 contra +0,25 no WINFUT, com o *drawdown* caindo de 710 para 669 e de 1.491 para 823 pontos. Stop maior ganha mais por trade porque arrisca mais por trade; por unidade de risco, o stop curto dimensionado pelo ATR mede melhor nos dois arquivos, e o `t` acompanha (+3,04 / +2,89 contra +2,75 / +2,09).

### Grade de stop × alvo, em pontos fixos (EV por trade)

**WINV26**

| stop | alvo 200 | alvo 250 | alvo 300 | alvo 450 |
|---|--:|--:|--:|--:|
| 75 | +31,5 | +38,8 | +41,1 | +25,8 |
| 100 | +48,2 | +54,5 | +56,8 | +39,7 |
| 150 | +61,9 | +69,1 | +69,3 | +44,8 |
| 200 | +88,6 | +103,2 | +104,0 | +77,8 |

**WINFUT**

| stop | alvo 200 | alvo 250 | alvo 300 | alvo 450 |
|---|--:|--:|--:|--:|
| 75 | +14,0 | +18,3 | +20,4 | +13,6 |
| 100 | +22,1 | +25,4 | +27,8 | +19,4 |
| 150 | +24,6 | +27,7 | +30,6 | +18,5 |
| 200 | +34,3 | +39,9 | +40,8 | +33,4 |

### Grade com o stop pelo ATR (EV em R)

**WINV26**

| stop | alvo 200 | alvo 250 | alvo 300 | alvo 450 |
|---|--:|--:|--:|--:|
| 0,6 × ATR | +0,44 (t +2,63) | +0,54 (t +2,86) | +0,59 (t +3,03) | +0,33 (t +1,80) |
| 0,75 × ATR | +0,48 (t +3,16) | +0,55 (t +2,86) | +0,57 (t +3,04) | +0,39 (t +1,97) |
| 1,0 × ATR | +0,45 (t +2,96) | +0,51 (t +2,73) | +0,51 (t +2,71) | +0,35 (t +1,98) |
| 1,25 × ATR | +0,40 (t +3,12) | +0,48 (t +3,30) | +0,48 (t +3,53) | +0,34 (t +2,55) |
| 1,5 × ATR | +0,38 (t +2,99) | +0,48 (t +3,31) | +0,52 (t +3,48) | +0,39 (t +2,93) |

**WINFUT**

| stop | alvo 200 | alvo 250 | alvo 300 | alvo 450 |
|---|--:|--:|--:|--:|
| 0,6 × ATR | +0,19 (t +1,72) | +0,23 (t +1,95) | +0,27 (t +2,11) | +0,17 (t +1,46) |
| 0,75 × ATR | +0,27 (t +2,85) | +0,31 (t +2,83) | +0,33 (t +2,89) | +0,25 (t +2,28) |
| 1,0 × ATR | +0,19 (t +2,10) | +0,22 (t +2,13) | +0,23 (t +2,24) | +0,13 (t +1,35) |
| 1,25 × ATR | +0,19 (t +2,41) | +0,21 (t +2,49) | +0,22 (t +2,58) | +0,14 (t +1,64) |
| 1,5 × ATR | +0,19 (t +2,54) | +0,24 (t +2,84) | +0,25 (t +2,81) | +0,20 (t +2,18) |

## 7. A entrada

| | n | /pregão | EV | R | total | acerto | t | dias+ | PF | DD |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| WINV26 · **limitada no meio do candle** | 82 | 6,3 | +58,4 | +0,57 | +4.785 | 56,1% | +3,04 | 85% | 2,82 | 669 |
| WINV26 · a mercado no fechamento | 90 | 6,4 | +45,0 | +0,44 | +4.049 | 51,1% | +2,74 | 79% | 2,25 | 574 |
| WINV26 · limitada válida até o fim do pregão | 89 | 6,8 | +51,4 | +0,51 | +4.575 | 53,9% | +3,00 | 85% | 2,51 | 669 |
| WINFUT · **limitada no meio do candle** | 206 | 4,8 | +32,8 | +0,33 | +6.750 | 48,1% | +2,89 | 63% | 1,85 | 823 |
| WINFUT · a mercado no fechamento | 230 | 5,3 | +19,7 | +0,21 | +4.539 | 43,5% | +2,11 | 56% | 1,45 | 1.108 |
| WINFUT · limitada válida até o fim do pregão | 226 | 5,3 | +29,3 | +0,29 | +6.614 | 46,5% | +3,00 | 58% | 1,75 | 790 |

A limitada mede +58,4 contra +45,0 a mercado no WINV26, e +32,8 contra +19,7 no WINFUT — a diferença é o preço: entrar no meio do candle do gatilho é melhor que entrar no fechamento dele. Deixar a ordem viva até o fim do pregão mede +51,4 e +29,3: pior nos dois, apesar de dar mais trades. O sinal que não volta ao meio do candle na barra seguinte já não vale.

## 8. O eixo [E2] e o filtro dele

| | n | /pregão | EV | R | total | acerto | t | dias+ | PF | DD |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| WINV26 · v1 · |delta| / |Close-Open| (217 gatilhos) | 79 | 6,1 | +73,9 | +0,73 | +5.839 | 62,0% | +3,49 | 85% | 3,65 | 369 |
| WINV26 · v2 · (|delta|/esforço) × volta (202 gatilhos) | 82 | 6,3 | +58,4 | +0,57 | +4.785 | 56,1% | +3,04 | 85% | 2,82 | 669 |
| WINFUT · v1 · |delta| / |Close-Open| (621 gatilhos) | 214 | 4,9 | +33,9 | +0,33 | +7.263 | 48,1% | +2,90 | 61% | 1,93 | 947 |
| WINFUT · v2 · (|delta|/esforço) × volta (547 gatilhos) | 206 | 4,8 | +32,8 | +0,33 | +6.750 | 48,1% | +2,89 | 63% | 1,85 | 823 |

Com todo o resto congelado, a fórmula **antiga** mede melhor nas duas bases (+73,9 / +33,9 contra +58,4 / +32,8). Fica a do indicador — é a configuração padrão dele, e a diferença está dentro do ruído de uma amostra deste tamanho —, mas registrada: o ganho do v2 medido no Rincones1 *não* se repete neste operacional.

| | n | /pregão | EV | R | total | acerto | t | dias+ | PF | DD |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| WINV26 · sem `DESCARTA_E2` — o padrão (202 gatilhos) | 82 | 6,3 | +58,4 | +0,57 | +4.785 | 56,1% | +3,04 | 85% | 2,82 | 669 |
| WINV26 · com `DESCARTA_E2` (94 gatilhos) | 38 | 2,9 | +67,6 | +0,69 | +2.570 | 60,5% | +2,77 | 85% | 3,12 | 516 |
| WINFUT · sem `DESCARTA_E2` — o padrão (547 gatilhos) | 206 | 4,8 | +32,8 | +0,33 | +6.750 | 48,1% | +2,89 | 63% | 1,85 | 823 |
| WINFUT · com `DESCARTA_E2` (246 gatilhos) | 87 | 2,3 | +54,5 | +0,56 | +4.738 | 56,3% | +3,26 | 68% | 2,71 | 516 |

O filtro corta o número de gatilhos de 202 para 94 no WINV26 e de 547 para 246 no WINFUT, e o que sobra mede melhor por trade: +67,6 contra +58,4, e +54,5 contra +32,8. O total cai — menos trades — mas o EV e o `t` do WINFUT sobem. Fica **desligado** por padrão, porque não é parte do indicador; é a primeira alavanca a puxar quem quiser menos sinais e mais seletividade.

## 9. Sensibilidade dos cortes

| corte | valor | EV · V26 | t | EV · FUT | t |
|---|---|--:|--:|--:|--:|
| HMA_PER | 20 | +41,7 | +2,17 | +21,4 | +2,14 |
| HMA_PER | 34 | +39,9 | +2,00 | +24,1 | +2,31 |
| HMA_PER | 50 ← | +58,4 | +3,04 | +32,8 | +2,89 |
| HMA_PER | 80 | +58,9 | +2,51 | +38,0 | +3,02 |
| HMA_PER | 100 | +56,5 | +2,53 | +39,6 | +3,02 |
| EMA_PER | 9 | +43,0 | +2,31 | +17,8 | +1,90 |
| EMA_PER | 13 | +49,7 | +2,77 | +21,8 | +2,18 |
| EMA_PER | 21 ← | +58,4 | +3,04 | +32,8 | +2,89 |
| EMA_PER | 34 | +51,9 | +2,56 | +28,4 | +2,31 |
| HMA_PLANA | 0,02 | +58,4 | +3,10 | +33,4 | +2,97 |
| HMA_PLANA | 0,03 | +60,0 | +3,18 | +34,4 | +3,00 |
| HMA_PLANA | 0,05 ← | +58,4 | +3,04 | +32,8 | +2,89 |
| HMA_PLANA | 0,08 | +61,4 | +2,85 | +33,7 | +2,79 |
| HMA_PLANA | 0,12 | +68,4 | +3,08 | +33,4 | +2,61 |
| HMA_SLOPE | 1 | +60,4 | +2,79 | +32,5 | +2,48 |
| HMA_SLOPE | 3 ← | +58,4 | +3,04 | +32,8 | +2,89 |
| HMA_SLOPE | 5 | +51,0 | +2,45 | +27,6 | +2,43 |
| HMA_SLOPE | 8 | +47,5 | +2,37 | +27,1 | +2,41 |
| PROF_MAX | 1,0 | +52,1 | +2,45 | +25,9 | +2,11 |
| PROF_MAX | 1,5 ← | +58,4 | +3,04 | +32,8 | +2,89 |
| PROF_MAX | 2,0 | +52,4 | +3,07 | +25,4 | +2,50 |
| PROF_MAX | None | +52,4 | +3,07 | +25,4 | +2,50 |
| ATR_PER | 10 | +53,9 | +2,80 | +27,1 | +2,50 |
| ATR_PER | 20 ← | +58,4 | +3,04 | +32,8 | +2,89 |
| ATR_PER | 40 | +59,5 | +3,18 | +31,8 | +2,81 |
| EXT_MAX_T | 0,0 | +53,9 | +2,49 | +31,1 | +2,56 |
| EXT_MAX_T | 0,5 ← | +58,4 | +3,04 | +32,8 | +2,89 |
| EXT_MAX_T | 1,0 | +50,7 | +2,69 | +30,2 | +2,85 |

7 dos 7 cortes ficam positivos nas duas bases em *todos* os valores varridos (`HMA_PER`, `EMA_PER`, `HMA_PLANA`, `HMA_SLOPE`, `PROF_MAX`, `ATR_PER`, `EXT_MAX_T`) — são platôs, não pontas. Nenhum tem valor perdedor. **Uma exceção incômoda:** a Hull de **80** mede melhor que a de 50 nas duas bases (+58,9 / +38,0 contra +58,4 / +32,8). O período 50 foi mantido porque é o que estava especificado, e trocá-lo com base nesta mesma amostra seria mais sobreajuste, não menos.

## 10. O custo

| custo | EV · V26 | R | t | EV · FUT | R | t |
|---|--:|--:|--:|--:|--:|--:|
| 0 pts | +58,4 | +0,57 | +3,04 | +32,8 | +0,33 | +2,89 |
| 5 pts | +53,4 | +0,52 | +2,80 | +27,8 | +0,28 | +2,47 |
| 10 pts | +48,4 | +0,46 | +2,56 | +22,8 | +0,22 | +2,04 |
| 20 pts | +38,4 | +0,36 | +2,05 | +12,8 | +0,11 | +1,16 |

## 11. Mês a mês

| base | mês | n | EV | total | acerto |
|---|---|--:|--:|--:|--:|
| WINV26 | 2026-08 | 82 | +58,4 | +4.785 | 56,1% |
| WINFUT | 2026-06 | 3 | -57,5 | -172 | 0,0% |
| WINFUT | 2026-07 | 93 | +28,1 | +2.617 | 48,4% |
| WINFUT | 2026-08 | 110 | +39,1 | +4.306 | 49,1% |

WINV26: 1 de 1 meses positivos · WINFUT: 2 de 3 meses positivos. Com dois meses de dados por arquivo, isto é descrição, não evidência — serve para ver se o resultado veio de um dia só.

## 12. A forma do desempenho

O que o operador precisa saber para não confundir variância normal com estratégia quebrada. Com custo de 5 pontos por trade, que é o cenário realista — o de custo zero é piso otimista.

| | WINV26 | WINFUT |
|---|--:|--:|
| trades | 82 | 206 |
| trades por pregão | 6,3 | 4,8 |
| EV por trade | 53,4 pts | 27,8 pts |
| EV em R | 0,52 | 0,28 |
| stop médio | 98 pts | 93 pts |
| acerto | 45,1% | 35,9% |
| média por pregão | 336,6 pts | 133,0 pts |
| desvio por pregão | 433,6 pts | 353,0 pts |
| pregões positivos | 85% | 60% |
| pior pregão | -462 pts | -629 pts |
| melhor pregão | 1109 pts | 1109 pts |
| maior sequência de trades sem ganho | 8 | 10 |
| maior sequência de pregões negativos | 2 | 5 |
| chance de 3 perdas seguidas | 16,5% | 26,3% |
| chance de 5 perdas seguidas | 5,0% | 10,8% |
| chance de semana negativa | 4% | 21% |
| chance de mês negativo | 0% | 4% |
| drawdown máximo | 739 pts | 953 pts |

| desfecho | WINV26 | WINFUT |
|---|--:|--:|
| alvo | 45,1% | 35,9% |
| stop | 34,1% | 41,7% |
| zero a zero | 20,7% | 22,3% |
| fim do pregão | 0,0% | 0,0% |

## 13. O que eu faria

1. **Operar no nível 0,80, e considerar 0,85.** Em 0,85 a carteira mede +70,3 / +41,7 por trade com 5,1 e 3,6 trades por pregão, contra +58,4 / +32,8 no nível adotado. Menos sinais, mais qualidade — a escolha é de temperamento, não de medição.
1. **Dimensionar o stop pelo ATR, não em pontos fixos.** stop 0,75 × ATR · alvo 300, com a parcial acompanhando. O stop médio fica em torno de 98 pontos — bem abaixo dos 150 herdados — e o drawdown cai junto.
1. **Rodar D + T e mais nada.** D + T mede +58,4 / +32,8; somar o K derruba para +46,9 / +24,3 e somar os dois de banda derruba para +41,7 / +18,5.
1. **Nunca operar com a Hull plana.** É o único veto que mede forte nos dois arquivos: -62,3 no WINV26 e -35,1 no WINFUT, contra +39,8 e +18,8 do resto. Se só uma regra deste relatório sobreviver, que seja esta.
1. **Não ligar os setups de banda.** O K mede positivo sozinho e mesmo assim piora a carteira; o KB mede negativo no WINFUT.
1. **Medir o custo real da corretora** e refazer a seção 10 com o número verdadeiro antes de dimensionar posição.

## 14. Ressalvas

- **Amostra pequena.** 44 pregões no WINFUT e 14 pregões cheios no WINV26 — dois meses, um regime só.
- **As bases não são independentes.** WINFUT contém WINV26.
- **As regras saíram destes mesmos dados.** Não há corte de validação fora da amostra neste projeto. A seção 9 mostra platôs, mas platô medido na mesma amostra continua sendo sobreajuste.
- **O canal quase não trabalha.** O veto dele é inerte e os setups de banda estão desligados; ele ficou por medir bem *o que não fazer*.
- **O preenchimento é otimista.** A limitada preenche a preço exato ao primeiro toque, sem fila.
- **Sem filtro de horário, rolagem ou vencimento.**

