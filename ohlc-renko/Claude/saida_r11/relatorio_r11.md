# Pontos de virada em Renko R11 — estudo preditivo para NTSL

**Base:** `WINFUT_11R_AGB_AGS_BDURF_QT_TRD.csv` — 20.000 bricks, 35 pregões, 29/06/2026 a 14/08/2026.
**Escopo:** somente o que o ProfitChart entrega por barra. Sem footprint, sem book, sem ordem intra-barra.
**Antecedentes:** `RenkoFeat_Features.md` §7.6 (MQL5, AUC 0,54) e `saida_renko/relatorio.md` (ProfitChart, AUC 0,537).

---

## Resumo

O modelo estatístico voltou a falhar — AUC 0,512 fora de amostra, com 20 features e um GBM como teto. É o terceiro resultado nulo consecutivo sobre a mesma pergunta, e agora com dados de agressão que o estudo anterior não tinha.

Mas a busca por um recorte estável encontrou **uma** coisa que sobrevive à divisão treino/teste, ao bootstrap e ao walk-forward, e ela não estava em nenhuma feature de fluxo: **onde o brick contrário está dentro do range do pregão**. Um brick que contraria a sequência local mas *retoma* a direção dominante do dia acerta 47,8% de uma perna de 4 tijolos, contra um breakeven de 40,0% — 362 sinais, +19,5 pts/trade bruto, e treino e teste concordam em 1,8 p.p.

Isso confirma o suspeito nº 2 da §7.6 do estudo MQL5 (*"contexto de mercado ausente"*) e derruba o nº 1 (*resolução espacial*) como prioridade: a informação que faltava não estava dentro do tijolo, estava fora dele.

---

## 1. A base: o que o ProfitChart entrega, e o que ele esconde

### 1.1. Geometria — confirmada

| Verificação | Resultado |
|---|---|
| corpo constante | 50 pts = 10 ticks, em 100% dos bricks fechados (R−1, padrão Nelogica) |
| continuação abre no `Close` anterior | 94,0% |
| reversão abre no `Open` anterior | 96,2% |
| `Data` | instante de **abertura** da barra (corr. com `t[i+1]−t[i]`: erro mediano 0,44 s) |
| `BarDurationF` | **minutos**, quantizado em 0,01 (0,6 s) |

O resíduo de 4–6% no encadeamento não é ruído de medição: são **884 bricks (4,42%)** cujo `Open` não bate nem com o `Close` nem com o `Open` do anterior. Deles, 853 são intradiários, o deslocamento modal é de ±20 ticks (dois corpos), e **89% têm `BarDurationF = 0` no brick anterior e no próprio**, com 63% compartilhando o timestamp. É rajada de preenchimento de gap — o mesmo fenômeno que o estudo MQL5 mediu em 4,45% (§7.1 de `RenkoFeat_Features.md`), agora visto do lado do ProfitChart. Duas implementações independentes chegando ao mesmo 4,4% é a melhor validação cruzada que esta base vai ter.

Esses bricks são descartados. O filtro completo (`sujo`) remove: quebra de encadeamento, primeiro brick do pregão, `Quantity = 0` e `BarDurationF > 60 min` (18 bricks, máximo de 62,5 h — fronteira de fim de semana, a mesma armadilha que a §11 do `RenkoFeat2_Arquitetura.md` sinaliza).

### 1.2. `BarDurationF` tem chão

**18,0% dos bricks marcam 0,00 min.** Não são todos sintéticos — só 11,7% deles têm `Quantity = 0`. A quantização de 0,01 min (0,6 s) contra uma duração mediana de 13 s significa que quase um quinto da base perde a medida de tempo por arredondamento. Entre os bricks **elegíveis**, porém, isso cai para 7,9%, e `Quantity = 0` para 0,3% — o brick de reversão após sequência é naturalmente lento. A feature é utilizável no recorte que interessa, e inútil fora dele.

### 1.3. O achado que muda a normalização do delta

```
Quantity − (AgressionVolBuy + AgressionVolSell)  =  27,15% do volume total
correlação dessa fração com log(Quantity)        =  +0,55
```

Mais de um quarto do volume do WIN não carrega agressor no ProfitChart — é negócio direto / RLP. O estudo MQL5 mediu a mesma coisa por outro caminho: `vol_direct` 18,10% + `vol_unknown` 1,84% (§11 de `RenkoFeat2_Arquitetura.md`).

A correlação de **+0,55 com o tamanho do brick** é o que importa. Ela significa que `(AgB − AgS) / Quantity` — a definição natural, e a que ambos os estudos anteriores usaram — vem **sistematicamente diluída nos bricks grandes**, que são justamente os informativos. Este estudo usa:

```
delta = direção × (AgB − AgS) / (AgB + AgS)
```

normalizando pelo volume *classificado*. A fração não classificada vira feature separada. É uma correção de graça que o ProfitChart permitia desde sempre, e ela é a razão pela qual o sinal do delta aqui sai **oposto** ao do estudo MQL5 (§7).

### 1.4. Reversão e continuação continuam sendo duas populações

| | n | duração | Quantity | Trades | pavio |
|---|---|---|---|---|---|
| continuação | 10.698 | 0,25 min | 18.578 | 5.563 | 5 ticks |
| reversão | 5.696 | 0,62 min | 30.571 | 9.095 | 15 ticks |
| **razão** | | **2,48×** | **1,65×** | **1,63×** | **3,00×** |

O consenso do `RenkoFeat2_Arquitetura.md` §5 vale aqui inteiro: toda janela de referência deste estudo contém **apenas bricks do mesmo tipo**. Um brick de reversão comparado contra uma janela dominada por continuações produz razão inflada por construção.

---

## 2. A taxa base — o número a bater

| condição | P(próximo brick na mesma direção) | n |
|---|---|---|
| qualquer brick | 67,19% | 19.999 |
| brick contrário a qualquer sequência | 67,3% | 6.316 |
| brick contrário a seq ≥ 3 (**elegível**) | **67,87%** | 2.860 |

A pré-condição inteira vale **+0,7 p.p.** É o mesmo diagnóstico da §7.4 do `RenkoFeat_Features.md`, reproduzido em base independente: os 67,9% são a assimetria mecânica do Renko (reverter custa 20 ticks, continuar custa 10), não informação de fluxo.

Elegíveis: **14,05%** dos bricks. O estudo MQL5 mediu 14,53%. Novamente, duas implementações independentes no mesmo lugar.

### Escolha do alvo

Entrada no fechamento do brick elegível, na direção dele. Alvo de `(K−1)` corpos a favor, stop de 2 corpos contra — o stop de 2 corpos é exatamente o brick de reversão fechando, que é o primeiro momento em que a tese morre. **Stop testado antes do alvo dentro da mesma barra** (pessimista).

| K | alvo | stop | breakeven | taxa base | expectativa na taxa base |
|---|---|---|---|---|---|
| 2 | 50 | 100 | 0,667 | 0,6722 | +0,8 pts |
| 3 | 100 | 100 | 0,500 | 0,5356 | +7,1 pts |
| **4** | **150** | **100** | **0,400** | **0,4128** | **+3,2 pts** |
| 5 | 200 | 100 | 0,333 | 0,3395 | +1,9 pts |
| 6 | 250 | 100 | 0,286 | 0,2979 | +4,3 pts |

Todo K é marginalmente positivo na taxa base — a assimetria do Renko paga alguma coisa em qualquer horizonte, e nenhum K paga o suficiente para cobrir custo. **K = 4 é o alvo do estudo**, pelo mesmo motivo que o MQL5 escolheu K = 4 (§7.4): é o mais próximo do breakeven, portanto o que mais depende do modelo, e uma perna de 4 tijolos é o que "virada" significa na prática.

---

## 3. O modelo estatístico — terceiro resultado nulo

20 features, todas causais e todas recalculáveis em NTSL: custo, duração, trades, tamanho de lote e velocidade normalizados contra janela de 20 reversões anteriores; delta limpo e delta bruto; fração sem agressor; pavio líquido; comprimento da sequência; e **seis features de regime** que nenhum estudo anterior tinha (densidade de reversões, razão de eficiência, posição no range, posição no dia, ritmo relativo, hora).

Split cronológico por pregão: 1.962 eventos de treino (24 pregões), 835 de teste (11 pregões).

| modelo | AUC teste | log-loss | Brier |
|---|---|---|---|
| logística L2 | 0,5119 | 0,6821 | 0,2444 |
| logística L1 | 0,4992 | 0,6808 | 0,2438 |
| **GBM (teto)** | **0,5326** | 0,6853 | 0,2457 |
| constante = taxa base do treino | 0,5000 | **0,6772** | **0,2420** |

Validação cruzada temporal: logística **0,501 ± 0,036**, GBM **0,511 ± 0,030**. Ambos os intervalos cobrem 0,50.

**Fora de amostra os dois modelos têm log-loss e Brier piores que simplesmente prever a taxa base.** O GBM não supera a logística com folga, o que significa que não há não-linearidade relevante a capturar — só ruído.

Nenhuma feature isolada passa de AUC 0,523. A tabela de decis do score é indistinguível de aleatória (o decil 8 acerta 58,3% e o decil 10 acerta 40,5%).

**Comparação com os antecessores:** MQL5 AUC 0,5416 com 9 features de footprint por nível; ProfitChart anterior AUC 0,5369 com 20 features agregadas; este AUC 0,5119 com 20 features incluindo regime. Três desenhos diferentes, três bases diferentes, mesma resposta.

---

## 4. Onde o sinal estava

Se nenhum modelo separa, resta perguntar se algum **recorte** desloca a taxa base de forma estável. Testei nove cortes por quintil, cada um comparando treino contra teste. Oito flipam:

| recorte | treino | teste |
|---|---|---|
| `seq_len` ∈ (7,5 ; 40] | 0,506 | 0,317 |
| `cost_nz` ∈ (−0,283 ; −0,056] | 0,422 | 0,483 |
| `rev_dens` ∈ (0,275 ; 0,325] | 0,456 | 0,384 |
| `pace_nz` ∈ (−0,668 ; −0,449] | 0,458 | 0,373 |

Isso é o que sobreajuste parece de perto. Dois cortes **não** flipam:

### 4.1. A primeira hora não é operável

| hora ≥ | treino | teste | TUDO | n |
|---|---|---|---|---|
| 9,0 (sem filtro) | 0,4134 | 0,4108 | 0,4126 | 2.797 |
| 9,5 | 0,4224 | 0,4264 | 0,4236 | 2.127 |
| **10,0** | **0,4278** | **0,4281** | **0,4279** | **1.900** |
| 10,5 | 0,4187 | 0,4315 | 0,4228 | 1.528 |

E o que sai: **hora < 10 → 0,3848 treino / 0,3671 teste**, os dois abaixo do breakeven de 0,400. 32% dos eventos elegíveis estão na primeira hora e são, em conjunto, negativos. Faz sentido mecanicamente: 63% de todos os bricks R11 acontecem entre 9h e 11h, o ritmo mediano é de 52 bricks por 15 min contra 7 à tarde, e nessa velocidade o brick contrário é chicote, não virada.

### 4.2. A posição no pregão — o achado

```
dpos = direção_do_brick × (Close − meio_do_range_do_dia) / range_do_dia
```

O brick elegível contraria a sequência **local**. `dpos` alto significa que, apesar disso, o preço está no lado do range do dia para onde **este** brick aponta — ou seja, a sequência contrariada era um *pullback*, e o brick elegível **retoma a direção dominante do pregão**.

Não é um sinal de reversão. É um sinal de fim de correção.

| dpos ≥ (com hora ≥ 10) | treino | teste | TUDO | n | expectativa |
|---|---|---|---|---|---|
| −0,10 | 0,4342 | 0,4345 | 0,4343 | 1.020 | +8,6 |
| 0,00 | 0,4341 | 0,4357 | 0,4346 | 849 | +8,7 |
| 0,10 | 0,4374 | 0,4426 | 0,4392 | 674 | +9,8 |
| 0,20 | 0,4626 | 0,4500 | 0,4578 | 474 | +14,5 |
| **0,25** | **0,4737** | **0,4834** | **0,4776** | **379** | **+19,4** |
| 0,30 | 0,5056 | 0,5207 | 0,5117 | 299 | +27,9 |
| 0,35 | 0,4773 | 0,5517 | 0,5068 | 219 | +26,7 |

**Monotônico, e treino e teste concordam em todos os degraus.** É um platô, não um pico — a assinatura de efeito real. Um limiar sobreajustado produziria uma célula boa cercada de células ruins.

E funciona sozinho, sem o filtro de hora (0,4524 / 0,4651 em `dpos ≥ 0,25`): os dois filtros são parcialmente independentes.

### 4.3. De onde vem cada ponto percentual

| etapa | n | acerto | expectativa |
|---|---|---|---|
| qualquer brick limpo | 18.994 | 0,4018 | +0,5 pts |
| contrário a **qualquer** sequência | 6.316 | **0,3925** | **−1,9 pts** |
| contrário a seq ≥ 3 (elegível) | 2.797 | 0,4126 | +3,1 pts |
| + hora ≥ 10 | 1.900 | 0,4279 | +7,0 pts |
| + dpos ≥ 0,25 (**regra final**) | 379 | 0,4776 | +19,4 pts |

A segunda linha merece atenção: **um brick contrário a uma sequência qualquer é pior que um brick sorteado ao acaso.** A intuição de "operar o brick de virada" é ativamente errada. Só a partir de `seq ≥ 3` a pré-condição começa a pagar, e mesmo aí paga pouco. O grosso do ganho vem das duas linhas de contexto.

---

## 5. Robustez da regra final

Regra reproduzida usando **apenas** o que o NTSL calcula — sem janela de referência, sem features de regime, e com `minutos desde o 1º brick do pregão ≥ 60` no lugar do relógio (as duas formulações são estatisticamente idênticas: 0,4709/0,4892 contra 0,4737/0,4834, e a versão por duração acumulada não depende do formato de `Time`).

```
brick contrário a seq ≥ 3  •  ≥ 60 min após a abertura  •  dpos ≥ 0,25
alvo 150 pts / stop 100 pts / breakeven 40,0%
```

| | n | acerto | expectativa |
|---|---|---|---|
| treino (24 pregões) | 223 | 0,4709 | +17,7 pts |
| **teste (11 pregões)** | **139** | **0,4892** | **+22,3 pts** |
| tudo | 362 | 0,4779 | +19,5 pts |

**Bootstrap por pregão** (não por trade — trades do mesmo dia são dependentes), 5.000 reamostragens:
IC95% do acerto **[0,4359 ; 0,5205]**, breakeven 0,400, **P(acerto ≤ breakeven) < 0,001**.
IC95% da expectativa: **[+9,0 ; +30,1] pts/trade**.

**Teste de aleatorização**, 2.000 permutações do rótulo dentro de cada pregão: **p = 0,0020**. O filtro seleciona bricks melhores que o acaso *do mesmo dia* — ou seja, o ganho não é um efeito de calendário.

**Walk-forward**, 5 blocos cronológicos com a regra fixa:

| período | n | acerto | pts |
|---|---|---|---|
| 29/06 – 07/07 | 79 | 0,4810 | +1.600 |
| 08/07 – 16/07 | 53 | 0,4717 | +950 |
| 17/07 – 27/07 | 51 | 0,4314 | +400 |
| 28/07 – 05/08 | 100 | 0,5300 | +3.250 |
| 06/08 – 14/08 | 96 | 0,4479 | +1.150 |

Nenhum bloco negativo. O pior (+7,8 pts/trade) ainda cobre custo baixo.

**Platô de parâmetros** — todas as 9 combinações de `seq ∈ {3}` × `min ∈ {30,60,90}` × `dpos ∈ {0,25 ; 0,35}` ficam entre +17 e +26 pts, com treino e teste do mesmo lado. `seq ≥ 4` e `seq ≥ 5` degradam e flipam no teste: **3 é o valor certo, e não por acaso — é o mesmo `MinSeqLen` que a spec MQL5 fixou.**

**Simetria direcional:** alta 0,481 (n=131), baixa 0,476 (n=248). Sem viés de lado.

---

## 6. Economia

362 trades em 35 pregões = **10,3 sinais por pregão**, resolvidos em 3 bricks (mediana), 5 no p90.

| custo total/trade | total | pts/trade | max drawdown | fator de lucro |
|---|---|---|---|---|
| 0 pts | +7.050 | +19,5 | −1.050 | 1,37 |
| 2 pts | +6.326 | +17,5 | −1.136 | 1,33 |
| 5 pts | +5.240 | +14,5 | −1.275 | 1,26 |
| 10 pts | +3.430 | +9,5 | −1.550 | 1,16 |
| 15 pts | +1.620 | +4,5 | −1.965 | 1,07 |
| ~19 pts | ≈ 0 | ≈ 0 | — | 1,00 |

**Este é o número que decide.** No WIN, o spread é de 1 tick (5 pts) e a entrada é a mercado; ida e volta com slippage realista fica entre 5 e 15 pts, mais corretagem. A margem bruta de 19,5 pts é da mesma ordem de grandeza que o custo de operar. A regra tem expectativa positiva demonstrada — e uma folga fina.

Antes de qualquer coisa em conta real: **meça o seu custo médio por trade** em 20 operações manuais seguindo o indicador, e compare com a tabela.

---

## 7. A agressão acrescenta — com o sinal invertido em relação ao estudo MQL5

Aplicada **por cima** da regra final:

| filtro extra | treino | teste |
|---|---|---|
| (nenhum) | 0,4709 (n=223) | 0,4892 (n=139) |
| `delta ≥ 0,10` | 0,4867 (n=150) | **0,5392** (n=102) |
| `delta ≥ 0,20` | 0,5316 (n=79) | 0,5610 (n=41) |
| `delta < 0,10` | 0,4384 (n=73) | **0,3514** (n=37) |

O corte separa nos dois blocos e na mesma direção: **um brick contrário com agressão a favor da nova direção inicia perna; um sem agressão, não.**

Isso contradiz o achado da §7.6 do `RenkoFeat_Features.md`, onde `delta_ratio` saiu com AUC 0,466 — sinal invertido, com a leitura de que "um brick contrário agressivo e caro tende a *não* iniciar perna". A diferença é a normalização da §1.3: lá o delta era dividido por `volume_total`, que inclui os ~20% de negócio direto, e essa fração cresce com o tamanho do brick. O denominador estava carregando o sinal.

**Mas o n é pequeno** (37 casos no bloco de teste que decide) e este é um quarto corte escolhido sobre os mesmos dados. Por isso `UsarFiltroDelta` entra no indicador **desligado por padrão**. Trate-o como hipótese a confirmar em base nova, não como parte da regra.

---

## 8. O que ficou provado que não funciona

Registrado para não ser testado de novo:

- **Regressão logística, L1 ou L2, sobre features agregadas por brick.** Três estudos, três AUC entre 0,51 e 0,54. O teto do GBM confirma que não é escolha de modelo.
- **Features de custo e duração normalizadas.** `cost_nz` AUC 0,4906, `dur_nz` 0,4928. A intuição de "tijolo caro = tijolo que encontrou resistência" não se mede nesta agregação.
- **`seq_len` como preditor.** AUC 0,5096 na amostra completa, 0,4759 no teste. Confirma a §7.4 do MQL5: a persistência do Renko é praticamente sem memória.
- **Exaustão da perna** (`cost_seq`, `dur_seq`, `delta_seq`): AUC entre 0,487 e 0,512. A inclinação de custo/duração ao longo da sequência contrariada não carrega nada.
- **Filtro adaptativo por ritmo** (bricks nos últimos 15 min) como substituto do filtro de horário: 0,4184 contra 0,4279 do relógio. Pior e menos estável.
- **Operar o lado contrário** (a favor da sequência original): expectativa entre −3 e −10 pts em toda a grade de alvo/stop. A assimetria do Renko favorece o brick contrário, não a continuação.

---

## 9. Os arquivos

```
saida_r11/
  RenkoViradaR11_Sinal.src        indicador -- GRAFICO DE PRECO (entregavel principal)
  RenkoViradaR11_Contexto.src     painel auxiliar -- JANELA SEPARADA
  RenkoViradaR11_Estrategia.src   automacao (secao 4 precisa de compilacao/ajuste)
  relatorio_r11.md                este documento
  relatorio.md                    saida bruta do modelo estatistico
  01_diagnostico.png              ROC, calibracao, decis, expectativa x limiar
  02_features.png                 distribuicao das 20 features por classe
  03_regra_ntsl.png               curva de capital e acerto por pregao
  features.csv / sinais_ntsl.csv  datasets

Claude/
  r11_diag.py  r11_diag2.py       diagnostico da base
  r11_virada.py                   modelo estatistico (o resultado nulo)
  r11_cond.py  r11_filtro.py      busca de recorte estavel
  r11_final.py r11_robust.py      robustez
  r11_ntsl_check.py               regra reproduzida com o que o NTSL calcula
```

### Como usar

1. Aplicar `RenkoViradaR11_Sinal.src` no gráfico Renko R11 do WINFUT. Bricks marcados em verde (compra) ou vermelho (venda) são os sinais; as três linhas são entrada, alvo e stop do último sinal.
2. Aplicar `RenkoViradaR11_Contexto.src` em janela separada para ver `dpos` contra o limiar.
3. Rodar 20 operações em simulador contando o custo real. Comparar com a tabela da §6.
4. Só depois considerar `RenkoViradaR11_Estrategia.src`.

**O indicador não repinta.** Tudo é calculado com a barra fechada e barras anteriores. A varredura do pregão substitui acumuladores persistentes de propósito: um acumulador reexecutado na barra em formação contaria a mesma duração várias vezes.

---

## 10. O que fazer a seguir

1. **Regerar a base em outro período** e reaplicar a regra fixa, sem reajustar nada. 35 pregões e 362 trades é pouco, e é a única forma de saber se `dpos ≥ 0,25` é estrutura ou coincidência de dois meses.
2. **Confirmar o filtro de delta** (§7) nessa base nova. Se sobreviver, ele quase dobra a margem.
3. **Testar `dpos` no R5 e no R21.** Se o efeito for do mercado e não do tempo gráfico, ele deve aparecer nos três — e isso é a evidência mais barata de que existe.
4. **Não voltar ao footprint por nível.** A §5.5 do `RenkoFeat_Features.md` propõe perfil intra-brick como candidato nº 1 para explicar a falta de sinal. Este estudo desloca essa prioridade: o que faltava era contexto de pregão, que custa três linhas de NTSL, não uma mudança de layout de sidecar. O footprint continua sendo a opção B — depois de esgotar o contexto, não antes.
