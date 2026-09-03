# Estratégia — Rincones1 XAUUSD

Especificação formal do que `engine.py` implementa. É o **contrato**: se um
número do relatório não bate com uma regra daqui, um dos dois está errado.

Este documento é **escrito à mão**. `RESULTADOS.md`, `relatorio.html`,
`PLANO.md` e `plano.html` são **gerados** — não edite aqueles.

---

## 1. O que este projeto é

O porte de [`Backtest-Rincones1`](../Backtest-Rincones1) (WIN, barras de 10.000
ticks) para o **XAUUSD em barras de 521 ticks**.

A estrutura não mudou: o mesmo índice de esforço em percentil causal, os mesmos
três regimes de média, a mesma gestão de parcial e stop, a mesma simulação de
trade. O que mudou está todo listado aqui, e **cada mudança foi medida**, com
todo o resto congelado, antes de virar default.

| | WIN · 10.000 ticks | XAUUSD · 521 ticks |
|---|---|---|
| eixos do índice | `[E1]+[E2]+[E3]` | `[E4]` sozinho |
| direção lida | delta (flags da B3) | candle |
| geometria de rejeição | clássica | **invertida** |
| entrada | limitada no meio do candle | **a mercado no fechamento** |
| filtro de regime | setups A e B | **nenhum** (todo gatilho vira trade) |
| stop / alvo | 150 / 300 pontos | 7,00 / 10,50 USD |
| unidade | pontos do WIN | USD por onça |

As três primeiras linhas trocam o **sinal** do resultado, não a calibração. A
§ 2 de `RESULTADOS.md` mede cada uma.

### 1.1 Os dados

Exportação do MT5 do símbolo sintético gerado por `Ticks_Claude_v1`, com a
convenção de campos `[R6]` — a mesma que `Ticks_Esforco_v2.mqh` consome:

```
<TICKVOL> -> agressão COMPRADORA da barra (V_buy)
<VOL>     -> agressão VENDEDORA  da barra (V_sell)
<SPREAD>  -> duração da barra em MILISSEGUNDOS
```

`dados/XAUUSD_521_TK_M1_202605040103_202608282354.csv` — 68.286 barras,
85 pregões, 04/05 a 28/08/2026.

### 1.2 As três "bases"

`COMPLETO`, `METADE_1` e `METADE_2`. **Não são três instrumentos**: são a
amostra inteira e as duas metades cronológicas dela, cortadas **por pregão**
para que nenhum dia apareça partido nos dois lados.

No projeto do WIN havia dois contratos independentes e a pergunta era "mede nos
dois?". Aqui há um histórico só, e a mesma pergunta vira "mede nas duas
metades?" — que é **evidência mais fraca**. Todo documento gerado repete isso
onde o número aparece.

---

## 2. O gatilho

### 2.1 Os quatro eixos

Cada eixo vira **percentil causal** nas `PERIODO_REF = 20` barras válidas
anteriores (conta valores estritamente menores; lê só o passado). Barra válida
é `V_buy + V_sell > 0`.

| eixo | fórmula | o que mede |
|---|---|---|
| `[E1]` volume | `V_buy + V_sell` | tamanho médio do lote |
| `[E2]` vaivém | `(\|delta\|/esforço) × (1 − \|C−O\|/percurso)` | agressão de um lado só que terminou desfeita |
| `[E3]` tempo | `1 / duração` | velocidade de formação da barra |
| `[E4]` range | `(High − Low) / tick` | ineficiência da barra |

com `percurso = 2·(High − Low) − |Close − Open|`, com piso em `|C−O|`.

`[E2]` é o **vaivém** de `Ticks_Esforco_v2.mqh`, não a fórmula v1
`|delta| / |Close−Open|`. `METRICA_E2 = 0` volta à antiga.

### 2.2 Eixo degenerado

**Um eixo que não varia sai da soma e do divisor**, e os pesos são
renormalizados. O critério é a fração de barras em que o valor **mudou** em
relação à anterior, contra `MIN_VARIACAO = 0,10` — não é desvio-padrão, porque
o que quebra o percentil é o **empate**, não a dispersão.

No XAUUSD isso derruba `[E1]`: o ativo é CFD, não há volume por negócio, o
gerador conta 1 lote por tick, e a agressão total muda em só **0,37%** das
barras. Sem essa defesa, um índice de três eixos que o incluísse ficaria preso
abaixo de 0,667 e nunca acenderia com corte em 0,80.

É a mesma defesa do `[D1]` de `Ticks_Esforco_v2.mqh`, e **não é um remendo para
o ouro**: é o que impede qualquer eixo que o ativo não publique de virar um teto
silencioso no índice.

> **Isto é a única decisão do backtest que olha a amostra inteira**, e por isso
> tem de ser declarada. Ela é uma propriedade estrutural do instrumento ("este
> ativo publica volume por negócio?"), não um sinal — mas ainda assim é
> tomada com todos os dados na mão, e o `.mqh` faz o mesmo sobre o histórico
> carregado. **No padrão daqui ela é inerte**: `EIXOS = ('E4',)`, `[E4]` não é
> degenerado, e o índice é exatamente `pE4`. Ela só passa a agir se alguém ligar
> `[E1]`, e é aí que a declaração importa. Nenhuma outra parte do motor lê o
> futuro: o percentil, as médias e a inclinação são todos causais, e a gestão só
> olha barras posteriores à entrada.

### 2.3 O índice

Média simples dos percentis dos eixos **vivos** listados em `EIXOS`. O padrão é
`EIXOS = ('E4',)` — medido, o range sozinho mede melhor que qualquer combinação
(§ 4 de `RESULTADOS.md`).

`EIXOS` lista `'E1'` mesmo sabendo que ele morre neste ativo, de propósito:
quem o derruba tem de ser a medição de degenerescência, não uma edição manual.
Assim o mesmo arquivo roda num ativo que publique volume de verdade.

### 2.4 A direção de referência

`REFERENCIA = 'candle'`. A leitura é sempre **contra** essa direção.

Na B3 a bolsa publica a flag de agressor de cada negócio; no XAUUSD ela é
**inferida** pela tick rule, e o delta resultante concorda com o sinal do
próprio candle em **63,2%** das barras. Não é a mesma variável, e medido a
direção que serve é a do candle (§ 3 de `RESULTADOS.md`).

Doji exato (ou delta zero) conta como lado comprador, para que as duas
referências tenham sempre um lado — igual ao `.mqh`.

### 2.5 A geometria

Duas medidas sobre a barra do gatilho:

```
pos_corpo  = onde o MEIO DO CORPO cai dentro do range, em %
             (0 = colado na mínima, 100 = colado na máxima)
corpo_pct  = |Close − Open| / range, em %
```

Quatro modos, em `GEOMETRIA`:

| modo | regra |
|---|---|
| `off` | só o índice decide |
| `corpo` | só exige `corpo_pct ≤ CORPO_MAX` |
| `classica` | corpo pequeno **e** do lado da rejeição clássica — referência de alta com o corpo na metade de baixo (pavio superior grande). É a regra do WIN. |
| `inversa` | corpo pequeno **e** do lado oposto — referência de alta com o corpo em cima (pavio inferior grande). |

O padrão é **`inversa` com `CORTE_POSICAO = 60`**. A clássica mede negativo
neste ativo (§ 6 de `RESULTADOS.md`).

Barra de range zero tem geometria indefinida e **não gera sinal**.

### 2.6 O sinal

```
sinal = −direção_de_referência,   se índice ≥ NIVEL_MIN
                                  e a geometria passar
        0                         caso contrário
```

Padrão: `NIVEL_MIN = 0,90`, `CORPO_MAX = 50`, `CORTE_POSICAO = 60`.

`DESCARTA_E2` (descartar a barra quando `[E2]` é o eixo dominante) existe, vem
do projeto do WIN, e é **inerte** no padrão daqui porque `[E2]` não entra no
índice. Volta a valer se `EIXOS` mudar.

---

## 3. Os regimes de média

Cinco famílias, em `REGIME_MA`:

- **`ema3`** (padrão) — EMAs 21/42/72. Direção pelo **empilhamento** das três,
  força pelo **leque** entre a rápida e a lenta, toque = encostar em qualquer
  uma delas.
- **`kama`**, **`hma`**, **`t3`**, **`jma`** — uma média só. Direção pelo
  **sinal da inclinação** nas `MA_SLOPE` barras anteriores, força pelo módulo
  dela, toque = encostar nela.

> `jma_aprox` é uma **aproximação pública** do estilo Jurik. **Não é** o JMA da
> Jurik Research, que é proprietário e não publicado. Leia como "média
> adaptativa muito suavizada", nunca como "o JMA".

**Todas as distâncias são normalizadas pelo range médio de `PERIODO_RANGE = 20`
barras.** É por isso que `LEQUE_MIN`, `TOL_TOQUE`, `CONSOL_MAX`, `AFAST_MIN_B`
e `AFAST_MIN_C` atravessaram do WIN para o ouro **sem recalibração**: a escala
do ativo já saiu da conta. Recalibrá-los por ativo, sobre uma amostra só, seria
ajustar ao ruído dela.

---

## 4. Os quatro setups

| | condição | direção do gatilho |
|---|---|---|
| **A** tendência | médias alinhadas e abertas (`\|leque\| ≥ LEQUE_MIN`), a barra toca uma delas | **a favor** do empilhamento |
| **B** reversão rápida | fora de consolidação, `\|Close − EMA21\| / rangeMédio ≥ AFAST_MIN_B` | **contra** o afastamento |
| **C** consolidação | médias emboladas, `\|Close − cacho\| / rangeMédio ≥ AFAST_MIN_C` | **contra** o afastamento |
| **L** livre | o gatilho disparou e nenhum dos três reivindicou a barra | — |

Prioridade `A > B > C > L`: `L` só fica com o que sobrou, então
`SETUPS_ATIVOS = ('A','B','C','L')` marca **todo** sinal, cada um pelo regime em
que caiu.

**O padrão opera os quatro**, isto é, não filtra por regime. Medido, o filtro
**subtrai** neste ativo: a carteira completa mede mais que qualquer subconjunto
A/B/C, nas duas metades (§ 9 de `RESULTADOS.md`). As três marcas continuam
existindo para que o relatório possa **quebrar** o resultado por regime em vez
de só afirmar isso.

---

## 5. Execução e gestão

### 5.1 Entrada

**A mercado, no fechamento da barra do gatilho** (`ENTRADA = 'fecha'`).

A alternativa `'meio'` — ordem limitada no meio do candle, válida por
`MAX_BARRAS_FILL = 1` barra — é a regra do WIN, e **não sobrevive à inversão da
geometria**. Com a geometria clássica o corpo está embaixo numa barra de alta,
o meio do candle fica **acima** do fechamento, e a venda limitada ali é um preço
melhor. Com a geometria invertida o corpo está em cima, o meio fica **abaixo**
do fechamento, e a mesma ordem vira meio range de desconto — que ainda por cima
preenche quase sempre, porque o preço já está do lado dela.

Medido: a regra custa ~1,85 USD por trade e inverte o sinal do resultado
(§ 7 de `RESULTADOS.md`).

### 5.2 Gestão

```
stop inicial     STOP = 7,00 USD
parcial          FRAC_PARCIAL = 50% da posição, na MESMA distância do stop
stop do restante na MÉDIA DA OPERAÇÃO
alvo             ALVO = 10,50 USD, no restante
```

A parcial na mesma distância do stop é o que faz a **média da operação** cair
exatamente em cima do stop inicial: o stop **não anda**, e o trade que volta
morre em **zero de verdade**. `STOP_APOS_PARCIAL = 'entrada'` reproduz o modelo
antigo, que pagava `FRAC_PARCIAL × parcial` no desfecho que chamava de zero a
zero. **O stop nunca se afasta.**

O stop de 7,00 é ~2,35 ranges médios, quase o dobro do equivalente escalado do
WIN (3,50 ≈ 1,17 range médio). O motivo é estrutural: a barra do gatilho é, por
construção, uma barra de range extremo, e um stop de pouco mais de um range
médio **cabe dentro dela**.

### 5.3 Regras da simulação

- **A gestão começa na barra SEGUINTE à da entrada.** Nem a barra do sinal
  (cujo H/L ocorreu antes do fechamento) nem a barra do fill entram no teste de
  stop/alvo.
- **Quando stop e alvo cabem na mesma barra, assume-se o STOP.** Pessimista, de
  propósito.
- **Não há posição overnight.** O trade que chega ao fim do pregão fecha no
  fechamento da última barra **daquele** dia.
- **Carteira = uma posição por vez.** Sinal que chega com posição aberta é
  ignorado. `carteira=False` mede cada sinal isolado, para comparar setups sem
  que um roube trade do outro.
- **Custo.** `CUSTO_PTS` é descontado de cada trade. O padrão é **0** — todos os
  números são brutos exceto onde o documento diz o contrário.

---

## 6. Unidades

| | |
|---|---|
| `TICK` | 0,01 USD |
| `VAL_PONTO` | 100 USD por 1,00 USD de movimento (lote padrão de 100 oz) |
| stop 7,00 | 700 USD por lote padrão · 7 USD por 0,01 lote |

Todos os valores dos documentos são em **USD por onça**, não em USD de conta.

---

## 7. O que muda o resultado, e onde está medido

| parâmetro | onde a medição está |
|---|---|
| `EIXOS`, `NIVEL_MIN` | RESULTADOS.md § 4 e § 10 |
| `METRICA_E2` | RESULTADOS.md § 5 |
| `REFERENCIA` | RESULTADOS.md § 3 |
| `GEOMETRIA`, `CORTE_POSICAO` | RESULTADOS.md § 6 e § 10 |
| `ENTRADA` | RESULTADOS.md § 7 |
| `STOP`, `ALVO` | RESULTADOS.md § 8 |
| `SETUPS_ATIVOS`, `REGIME_MA` | RESULTADOS.md § 9 |
| `CUSTO_PTS` | RESULTADOS.md § 8 |

Mexeu em qualquer um: rode `python rodar.py && python relatorio.py && python
plano.py`. Os documentos gerados se atualizam sozinhos, **inclusive as frases de
conclusão** — elas são calculadas, não escritas.
