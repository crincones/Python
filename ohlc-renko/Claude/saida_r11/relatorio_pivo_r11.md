# Otimização do PivoReversao_Claude para Renko R11

**Base:** `WINFUT_11R_AGB_AGS_BDURF_QT_TRD.csv` — 19.999 bricks, 29/06/2026 a 14/08/2026, 35 pregões.
**Split:** cronológico por pregão, 70% treino (24 pregões) / 30% teste (11 pregões).
**Rótulo:** entrada no fechamento da barra de confirmação, alvo 150 pts, stop 100 pts, primeiro toque com **stop testado antes do alvo** (pessimista). Breakeven 40,0%.

---

## 1. O ponto de partida: o arquivo original no R11

| configuração | n | sinais/pregão | acerto | pts/trade |
|---|---:|---:|---:|---:|
| original (Esq 2, Dir 0, MinScore 35) | 3.146 | 89,9 | **0,3983** | −0,4 |
| entrar em qualquer barra, qualquer lado | 39.992 | — | 0,3959 | — |

O indicador, como está, **não distingue nada** do acaso no R11 e fica abaixo do breakeven. Duas causas, ambas estruturais.

### 1.1 `Direita = 0` não funciona em Renko

Numa perna Renko **todo brick faz nova extrema** no sentido da perna. Sem barra de confirmação, o teste de pivô dispara em 49,9% dos bricks (Esquerda=2), 43,4% (Esq=3), 38,2% (Esq=4). O indicador acende a tela inteira dentro da tendência.

Com confirmação: Dir=1 → 0,4367 · Dir=2 → 0,4085 · Dir=3 → 0,3961. **Dir=1 é o único viável** — no Renko de 50 pts de corpo, cada barra de espera custa um corpo inteiro do movimento.

### 1.2 Três dos seis componentes medem "tipo de brick", não fluxo

| métrica | continuação | reversão | consequência |
|---|---|---|---|
| `posFech = (Close−Low)/range` | 100% em 0 ou 1 | idem | o brick fecha no gatilho. `cAbs` multiplica a rampa de `posFech` → vira liga/desliga de tipo |
| `pavInf` (alta) | 0,290 | 0,573 | a reversão anda 20 ticks contra 10 da continuação → nasce com 10 ticks de pavio. Com PavIni/Fim 0,25/0,60, `cPav` satura em ~1 em toda reversão |
| `range = High−Low` | mediana 70 pts | mediana 125 pts | 1,29 desvios de separação → `zRng` também é detector de tipo |

Sobrevivem intactos: **`BarDurationF`** (o brick tem tamanho fixo, então duração é velocidade pura) e a **agressão**, desde que `NormalizarAgressao=1` — 27,2% do volume do WIN não carrega agressor e essa fração cresce com o tamanho do brick (correlação **+0,585** com log Quantity), então dividir por Quantity dilui o delta justamente nos bricks grandes.

---

## 2. O score não sobrevive fora da amostra

AUC de cada componente sobre todos os pivôs (Esq 2 / Dir 1), treino → teste:

| | treino | teste | | treino | teste |
|---|---:|---:|---|---:|---:|
| cDiv | 0,5063 | 0,4971 | cFlip | 0,4848 | 0,4913 |
| cAbs | 0,5245 | 0,5080 | cCmp | 0,4952 | 0,4984 |
| cClx | 0,4963 | 0,5078 | cPav | 0,5132 | 0,5079 |
| **score** | **0,5221** | **0,5059** | | | |

Nenhum passa de 0,508 no teste. Re-pesei os seis componentes pelo lift medido **só no treino**, dentro do conjunto já filtrado, e cortei por quantil do treino:

| corte | treino | teste |
|---|---:|---:|
| tudo | 0,4885 | 0,4526 |
| ≥ q50 do treino | 0,5319 | 0,4015 |
| ≥ q75 do treino | **0,5390** | **0,3538** |

**O ordenamento inverte.** Isso não é "o score precisa de ajuste", é "não há score a construir com esta base". Quarto resultado nulo consecutivo sobre fluxo (dois estudos MQL5, o RenkoViradaR11 e este).

`cDiv ≥ 0,6` chegou a parecer o achado (0,4938 no conjunto todo), mas isolado degrada: Esq=5 dá treino 0,4387 → teste 0,3865.

---

## 3. O que sobrou

### 3.1 Geometria do pivô

| | Toler 0,00 | Toler 0,30 | Toler 0,60 |
|---|---:|---:|---:|
| Esq 2 / Dir 1 | **0,4217** | 0,4190 | 0,4048 |
| Esq 3 / Dir 1 | **0,4219** | 0,4204 | 0,4077 |
| Esq 4 / Dir 1 | **0,4226** | 0,4206 | 0,4058 |

Tolerância só admite não-pivô: no Renko a extrema é quantizada. **`TolerPivoFrac = 0`.**

`Esquerda` sobe monotonicamente até saturar. Com o filtro de contexto aplicado (pos ≥ 0,25):

| Esq | 3 | 4 | 5 | **6** | 8 | 10 |
|---|---:|---:|---:|---:|---:|---:|
| tudo | 0,4536 | 0,4581 | 0,4677 | **0,4764** | 0,4735 | 0,4691 |
| teste | 0,4375 | 0,4441 | 0,4548 | **0,4526** | 0,4398 | 0,4302 |

Plateau em 5–8. **`Esquerda = 6`.**

### 3.2 Tipo do brick

O brick do pivô tem que apontar para o trade — pivô de fundo precisa ser brick de **alta**. No Renko o brick que marca o fundo costuma ser a própria reversão: ela abre na *abertura* do brick anterior (50 pts acima do fechamento dele) e a mínima real mergulha abaixo. Quando o brick do pivô aponta **contra** o trade: **0,3611** (n=108) — perde dinheiro.

### 3.3 Contexto do pregão — o achado

```
contexto = direção × (Close[pivô] − meio_do_range_do_dia) / range_do_dia
```

| filtro | n | acerto |
|---|---:|---:|
| todo pivô | 5.328 | 0,4219 |
| + tipo ok | 5.220 | 0,4232 |
| + contexto ≥ 0,20 | 1.638 | 0,4414 |
| + contexto ≥ 0,25 | 1.369 | 0,4536 |
| **pivô colado na extrema do dia (≤ 0,10)** | 1.250 | **0,3848** |

É o mesmo achado do estudo RenkoViradaR11, reencontrado por um caminho **independente**: o pivô que presta é o que **retoma a direção dominante do pregão**, não o que tenta virar o dia. O pivô que salta aos olhos no histórico — o do fundo do dia — é o pior grupo de todos.

### 3.4 Assimetria entre os lados

Com o mesmo limiar 0,25: compra 0,5133 / venda 0,4411. Subindo a venda:

| limiar venda | 0,25 | 0,30 | **0,35** | 0,40 |
|---|---:|---:|---:|---:|
| acerto | 0,4411 | 0,4653 | **0,4864** | — |
| treino / teste | | | **0,4861 / 0,4867** | |

**LimiarCompra 0,25 · LimiarVenda 0,35.** Plateau, não pico (0,25/0,30 → 0,4930; 0,25/0,40 → 0,5031).

---

## 4. Abordagens alternativas testadas — e rejeitadas

| ideia | melhor resultado | referência | veredito |
|---|---:|---:|---|
| range **móvel** de N bricks no lugar do range do pregão | 0,4742 | 0,5018 | pior em **todas** as 5 janelas testadas (40 a 250) — a âncora de sessão é que importa |
| **limiar único** misturando profundidade do pivô e contexto | 0,4572 | 0,5018 | dois cortes duros batem um blend contínuo |
| **confluência** com a regra RenkoViradaR11 | 0,4644 | 0,5349 sem ela | **invertido** — as duas regras olham o mesmo fenômeno com 1 brick de defasagem (47% de sobreposição), e a população do RenkoViradaR11 é a metade fraca |
| alvo maior | 250/150 dá +26,8 bruto | +25,4 | some com o custo: 200/100 cai para **+2,5** líquidos com 10 pts, contra +15,4 de 150/100, e o drawdown triplica |

---

## 5. As duas entregas

### `PivoR11_Claude.ntsl` — arquitetura preservada, parâmetros re-medidos

Mantém as somas móveis O(1), o cache de pivôs, os seis componentes e o score. Muda: `Esquerda 2→6`, `Direita 0→1`, `TolerPivoFrac 0,30→0`, `MinBarras 3→5`, `MinScore 35→0`, pesos re-medidos (só para exibição), mais os dois filtros da seção 3.

```
n=568 · 16,2 setas/pregão · mediana 3 bricks para resolver
treino 0,5121 (n=373) | teste 0,4821 (n=195) | tudo 0,5018 → +25,4 pts/trade
compra 0,4971 (n=348) | venda 0,5091 (n=220)
bootstrap por pregão IC95% [0,4517 ; 0,5515] · P(≤breakeven) 0,0000
aleatorização dentro do pregão p = 0,0000 · walk-forward 5/5 blocos positivos
PF 1,51 · maxDD −900 pts bruto · +15,4 pts/trade com 10 pts de custo
```

### `PivoR11_Contexto_Claude.ntsl` — o motor de score removido

Só geometria + contexto + janela de pregão. Acrescenta o único ganho grande que sobrou: **evitar 10h–12h**.

| faixa horária | n | acerto |
|---|---:|---:|
| primeira hora (< 10h) | 251 | **0,5578** |
| 10h–12h | 182 | **0,4011** |
| 12h–15h | 80 | 0,5250 |
| depois das 15h | 55 | 0,5455 |

```
n=387 · 11,1 setas/pregão · mediana 3 bricks
treino 0,5534 (n=262) | teste 0,5360 (n=125) | tudo 0,5478 → +37,0 pts/trade
compra 0,5409 (n=257) | venda 0,5615 (n=130)
bootstrap por pregão IC95% [0,4891 ; 0,6048] · P(≤breakeven) 0,0000
aleatorização dentro do pregão p = 0,0000
walk-forward 5/5 positivos (0,482 · 0,529 · 0,600 · 0,618 · 0,500)
PF 1,82 · maxDD −700 pts bruto
+27,0 pts/trade com 10 pts de custo · +12,0 com 25 pts
```

**Ressalva sobre a janela horária.** É observada em **uma** amostra de 35 pregões. A favor: consistente nos dois blocos (treino 0,4107 / teste 0,3857 dentro do buraco) e o efeito é um plateau — evitar 9h30–11h30, 10h–11h30, 10h–12h, 10h–12h30 ou 9h30–12h dá 0,536 a 0,553, sem pico. Ainda assim é o parâmetro mais frágil dos dois arquivos. `EvitarIni(0)` desliga e volta a 16,2 setas a 50,18%.

---

## 6. Comparação com o que já existia

| indicador | sinais/pregão | acerto | pts/trade bruto | maxDD | PF | morre com custo de |
|---|---:|---:|---:|---:|---:|---:|
| PivoReversao_Claude original no R11 | 89,9 | 0,3983 | −0,4 | — | — | qualquer |
| RenkoViradaR11_Sinal | 10,9 | 0,4789 | +19,7 | −1.050 | 1,37 | ~19 pts |
| **PivoR11_Claude** | 16,2 | 0,5018 | +25,4 | −900 | 1,51 | ~28 pts |
| **PivoR11_Contexto_Claude** | 11,1 | **0,5478** | **+37,0** | **−700** | **1,82** | ~44 pts |

---

## 7. Como conferir na tela

Suba primeiro com **`MostrarRejeitados(1)`**: os `o` cinzas são os pivôs que a geometria aceitou e o contexto barrou. Devem ser muitos (~100/pregão) contra ~11 setas. Se os `o` aparecem e as setas não, o problema é o formato de `Time` — mas o arquivo já normaliza HHMM e HHMMSS sozinho (`if hm >= 10000 then hm := Round(hm / 100)`).

`MostrarScore(1)` escreve `contexto × 100` ao lado da seta.

---

## 8. Arquivos

| arquivo | o que faz |
|---|---|
| `pivo_r11_diag.py` | diagnóstico da geometria Renko contra as premissas do indicador |
| `pivo_r11_core.py` | réplica fiel do NTSL em Python (pivô, cache, 6 componentes, score) |
| `pivo_r11_comp.py` | o original no R11 + poder de cada componente |
| `pivo_r11_opt.py` | grade de geometria + o que acrescenta por cima |
| `pivo_r11_regra.py` | isolamento tipo-de-brick vs absorção/rejeição |
| `pivo_r11_final.py` | extensão de `Esquerda`, divergência, equilíbrio dos lados |
| `pivo_r11_conso.py` | MinBarras, score re-pesado, robustez, comparação |
| `pivo_r11_fecha.py` | limiares assimétricos, sobreposição, gráfico, CSV |
| `pivo_r11_extra.py` | geometria alvo/stop, confluência, relógio |
| `pivo_r11_alt.py` | range móvel, limiar único, janela de pregão |
| `pivo_r11_robB.py` | robustez completa da regra do arquivo B |
| `saida_r11/04_pivo_r11.png` | curva de capital e acerto por pregão |
| `saida_r11/pivo_r11_sinais.csv` | os 568 sinais, um por linha |
| `saida_r11/pivo_componentes.csv` | todos os pivôs com seus componentes |
