# Estratégia do Ajuste — WINFUT

Especificação formal das regras testadas. Tudo que está aqui está implementado em
`engine.py`; nada foi deixado a critério de interpretação em tempo de execução.

---

## 1. Premissa

O ajuste do dia anterior (*Prior Cote Ajuste*) funciona como preço de referência.
A hipótese é que o preço tende a voltar para ele durante o pregão.

Disso sai o **viés direcional*, definido uma única vez na abertura:

| Condição na abertura | Viés       | Direção do alvo            |
| -------------------- | ---------- | -------------------------- |
| `abertura < ajuste`  | **COMPRA** | para cima, rumo ao ajuste  |
| `abertura > ajuste`  | **VENDA**  | para baixo, rumo ao ajuste |

Viés muda durante o dia quando o preço ultrapassa 600 pontos a partir do ajuste, neste caso fica habilitada a operação em direção ao ajuste porém no sentido contrário ao inicial.

Existe uma premissa adicional de que preço longe das médias de 21 exponencial, tende voltar à média, isto é particularmente positivo para o tempo gráfico de 60 minutos, geralmente a de 5 minutos é usada como "alvo" da operação.

---

## 2. Universo de dados

| Item               | Valor                                                                                  |
| ------------------ | -------------------------------------------------------------------------------------- |
| Barras             | `dados/WIN_N_M1.csv` — WIN$N, M1, 2021-08-23 a 2026-08-21                              |
| Ajustes            | `dados/Ajustes-WINFUT-NoDiv-NoSplits.2026-08-28.csv` — D1 + coluna *Prior Cote Ajuste* |
| Tick               | 5 pontos (100% dos preços da base são múltiplos de 5)                                  |
| Valor do ponto     | R$ 0,20 por contrato (WIN)                                                             |
| Pregões no arquivo | 1248                                                                                   |
| Pregões válidos    | **1205**                                                                               |

### 2.1 Validação cruzada das duas bases

O OHLC diário agregado a partir do M1 foi comparado com o OHLC do arquivo de
ajustes nos 1248 dias em comum: **abertura, máxima, mínima e fechamento batem em
1248/1248 dias, diferença máxima 0 pontos**. As duas bases são a mesma série de
preços, então a coluna de ajuste pode ser colada nas barras M1 sem reescala.

### 2.2 Filtros de descarte (43 dias)

| Filtro               | Dias | Motivo                                                                                                                                                                                                                                      |
| -------------------- | ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Vencimento / rolagem | 27   | WIN$N não é ajustado por rolagem. No vencimento (quarta-feira mais próxima do dia 15 dos meses pares) a série salta para o contrato novo enquanto o ajuste ainda é do contrato velho — gap artificial de +1700 a +4200 pts contra o ajuste. |
| Abertura ausente     | 11   | Primeira barra do dia depois das 09:05, ou menos de 60 barras no pregão. Sem a abertura não há viés nem âncora de pivô.                                                                                                                     |
| Ajuste inconsistente | 4    | `\|abertura − ajuste\| > 1500` **e** `\|abertura − fech. anterior\| < 1000`: o preço é contínuo mas o ajuste não, logo o furo está no ajuste.                                                                                               |
| Sem D1 anterior      | 1    | Primeiro dia da base, sem OHLC anterior para calcular pivô.                                                                                                                                                                                 |

Dias de gap grande **genuíno** (24/02/2022, 03/03/2026 etc., onde o preço também
gapeou contra o fechamento anterior) foram **mantidos** — são pregões legítimos.

Como validação adicional, o ajuste do dia anterior, por definição, deve ficar no range contido dentro do horário das 17:00 e 17:15 desse dia.

**Resultado da checagem** (implementada em `desvio_ajuste`): a janela 17:00–17:15
é estreita demais — contém o ajuste em apenas **78,9%** dos dias. Alargando:

| Janela do dia anterior | Ajuste cai dentro | Desvio mediano das falhas |
| ---------------------- | ----------------- | ------------------------- |
| 17:00–17:15            | 78,9% (984)       | 136 pts                   |
| 17:00–17:30            | 84,2% (1050)      | 115 pts                   |
| **17:00–18:00**        | **96,7% (1206)**  | **30 pts**                |

Com 17:00–18:00 restam 41 dias fora, 40 deles por ≤ 124 pts — folga normal de um
ajuste que é média ponderada do call, não um negócio único. O único desvio
material (2025-12-17, 616 pts) já era dia de vencimento. **A coluna de ajuste
está consistente.** O filtro aplicado descarta o dia se o desvio passar de 300 pts,
o que na prática não remove nenhum dia além dos já descartados.

---

## 3. Níveis operáveis

### 3.1 Pivôs — `Pivot_Points_Pro.mq5`

Réplica exata da função `CalculateAndDraw` do indicador, com os parâmetros
default (`UseDailyOpen = true`, `ShowPP = false`, fibs 0.618 / 1.000 / 1.618 / 2.000).

Do **D1 do pregão anterior** (`H`, `L`, `C`):

```
PP   = (H + L + C) / 3
ampR = |L − PP|
ampS = |H − PP|
```

Ancorado na **abertura de hoje** (`Open`), com `fib = [0.618, 1.000, 1.618, 2.000]`:

```
R1..R4 = Open + ampR × fib[k]
S1..S4 = Open − ampS × fib[k]
```

São 8 níveis por dia. Note que **não são pivôs clássicos**: a âncora é a abertura
de hoje, e só as amplitudes vêm do dia anterior. `PP` não é usado (o indicador
vem com `ShowPP = false`).

o nível de pivó em si não é utilizado, apenas os níveis fibonacci.

### 3.2 Bolas

Todo múltiplo de **1000** dentro da faixa do dia (mínima e máxima do pregão,
ajuste e pivôs, com uma bola de folga em cada ponta).

### 3.3 Fusão pivô × bola (setup CD)

Quando um pivô e uma bola estão a **menos de 300 pontos** um do outro, fica só
**o mais afastado do ajuste**. Implementação: ordena todos os níveis por
distância decrescente do ajuste e varre a lista aceitando um nível só se ainda
não houver vizinho aceito a menos de 300 pts. O primeiro a ser aceito num
agrupamento é sempre o mais distante, então o critério é satisfeito por
construção.

---

## 4. Regras de entrada

### 4.1 Filtro de distância mínima

Só é operável o nível que estiver a **600 pontos ou mais do ajuste**. Isso
garante espaço até o ajuste maior que o alvo de 500 e descarta os níveis colados
nele.

> Consequência importante: no lado da abertura, isso só existe se o gap do dia
> for ≥ 600 pts. Na base, **apenas 24% dos pregões abrem tão longe do ajuste**
> (gap mediano: 327 pts).

### 4.2 Primeiro toque, e o toque tem que ser novo extremo

Um nível entra **uma única vez por dia**, no primeiro toque, e apenas se nenhum
preço anterior do pregão já tiver passado por ele — é a regra dos *"pivôs que não
têm preços do lado esquerdo"*: o toque tem que ser **nova máxima ou nova mínima
do dia**.

Na prática isso significa que o nível é alcançado enquanto o preço se **afasta**
do ajuste, e a entrada é a aposta na volta. Um nível alcançado no caminho de
*volta* ao ajuste não é novo extremo e não gera entrada.

Formalmente, mantendo `ext` = extremo do dia no lado afastado (monotônico):

```
entra em L  ⟺  L ainda não foi tocado
              ∧ L não foi invalidado (4.4)
              ∧ L está além de ext          (novo extremo)
              ∧ mínima ≤ L ≤ máxima da barra (toque)
```

### 4.3 Habilitação do lado oposto

No início do dia, só o **lado da abertura** está habilitado:

- viés COMPRA → operam-se os níveis **abaixo** de `ajuste − 600`, comprando;
- viés VENDA → operam-se os níveis **acima** de `ajuste + 600`, vendendo.

Quando o preço **ultrapassa o ajuste em 600 pontos**, o outro lado é habilitado:
passa a valer a operação *do outro lado do ajuste de volta para ele*. O extremo
`ext` desse novo lado começa no próprio ponto de cruzamento (`ajuste ± 600`), de
modo que só níveis ainda não alcançados valem — de novo, "sem preços do lado
esquerdo".

No range entre -600 e +600 pontos a partir do ajuste não pode haver mudança de regime, apenas quando é violado um destes níveis, exemplo: se abre em -100 é compra até ultrapassar +600 que poderia ser habilitada a venda. e se abrir em +500 é venda até ultrapassar -600 onde ficaria habilitada a compra.

### 4.4 Invalidação por retração de 500 pontos

Se o preço avança se afastando do ajuste, **não toca** o próximo nível, e depois
**retrai 500 pontos** a partir do extremo do dia, esse nível morre. A entrada
seguinte só pode ser no **próximo nível mais afastado**.

```
se (houve novo extremo desde a última invalidação)
   ∧ (a barra atual NÃO é a que criou o extremo)
   ∧ (retração desde ext ≥ 500 pts)
então
   invalida o nível não tocado mais próximo além de ext
   exige um novo extremo antes de poder invalidar outro
```

Duas travas importantes, que decidem o comportamento da regra:

1. **A barra que cria o extremo não conta.** Dentro de uma barra de 1 minuto não
   se sabe a ordem dos preços; usar máxima e mínima da mesma barra faria a
   abertura volátil matar níveis sem que o preço tivesse ido a lugar nenhum.
2. **Uma invalidação por perna.** Depois de matar um nível, é preciso um **novo
   extremo do dia** antes que outro possa ser invalidado. Sem essa trava, um
   mercado lateral de 500 pts mata a lista inteira de níveis em cadeia num dia
   que ainda vai andar 3000 pontos — foi exatamente o bug encontrado na primeira
   versão da engine, corrigido antes de rodar os números finais.

---

## 5. Gestão da posição

| Item                 | Regra                                                                                                       |
| -------------------- | ----------------------------------------------------------------------------------------------------------- |
| Lote                 | **6 contratos** — o mínimo que realiza parcial de 1/2 (3) e de 2/3 (4) com contratos inteiros               |
| Entrada              | ordem limite no preço do nível; preenche no toque                                                           |
| Stop                 | **100 pontos** contra                                                                                       |
| Parcial              | em **+45 pontos** sai **2/3** da posição, e o stop do restante vai para o **preço médio da operação** (−90) |
| Alvo                 | **500 pontos fixos** em todos os setups (o ajuste dá a direção, não o alvo)                                 |
| Saída forçada        | a mercado, no fechamento da última barra do pregão                                                          |
| Posições simultâneas | permitidas por padrão (cada nível é um trade independente); variante "uma posição por vez" também reportada |
| Custos               | resultados **brutos**, sem corretagem/emolumentos                                                           |

A fração de 2/3 é o que produz o **2:1** citado no enunciado:

```
ganho = 2/3 × 45 + 1/3 × 500 = 196,7 pts   contra risco de 100 pts  →  1,97:1
```

(1/2 daria 2,7:1 e 3/4 daria 1,6:1; 2/3 é a única fração que fecha em 2:1.)

**O breakeven é no médio da operação, não no preço de entrada.** Depois da
parcial, o terço que sobra tem o stop movido para o preço em que ele devolve
exatamente o que a parcial ganhou — o total da operação fica zerado:

```
lote de 6: saem 4 contratos em +45       -> realizado 4 × 45 = 180 pts
sobram 2:  médio = entrada − 180 ÷ 2     =  entrada − 90
se o stop do resto for pego: 180 + 2 × (−90) = 0
```

O stop do resto fica, portanto, **10 pontos** mais perto que o stop original —
não na entrada nem no lucro. Com a parcial de 50% (3 de 6), o médio fica a
3 × 45 ÷ 3 = **45** pontos. O médio é arredondado ao tick para o lado da entrada
(com 6 contratos, nas duas frações, a conta já cai exata). Se ele cair além do
stop original, o stop não é afastado: fica onde estava — é o caso das parciais
em +100, que só aparecem na grade de sensibilidade.

Os resultados em pontos são **por contrato** (o total do lote dividido por 6); os
R$ são do lote inteiro.

Resultados possíveis de um trade: **−100** (stop), **0** (parcial e stop no
médio), ou **+196,7** (parcial e alvo, com alvo de 500).

### 5.1 Resolução intrabarra

Barra de 1 minuto não diz a ordem dos preços dentro dela. Três convenções são
reportadas, e a diferença entre elas **decide o sinal do resultado** — ver
RESULTADOS.md §2.

1. **Conservadora (principal).** Na barra de entrada só resolve o lado
   **adverso**: o stop vale, a parcial e o alvo não. Motivo: a entrada é sempre
   num extremo novo do dia (regra 4.2), então a extremidade favorável dessa
   barra é o próprio movimento que gerou o toque. Creditá-la equivale a assumir
   preenchimento no tick extremo de uma barra cuja amplitude mediana é de
   **160 pontos** — e ainda supor que a reversão veio depois do preenchimento.
   Nas barras seguintes, o adverso resolve antes do favorável.
2. **Creditando a barra de entrada.** Idem, mas parcial e alvo podem sair já na
   barra do toque. **93% das parciais caem nesse caso**, o que torna essa
   convenção o principal determinante do resultado.
3. **Teto absoluto.** Barra de entrada creditada e o alvo ganha todo empate.

O stop movido para o médio só passa a valer **na barra seguinte** à da parcial: para
disparar a parcial o preço teve de subir 45 pontos, logo a extremidade adversa
daquela barra é anterior a ela.

---

## 6. Os cinco setups

| Tag    | Nome                 | Entrada                                                                                                                                    | Alvo                             |
| ------ | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------- |
| **A**  | Retorno à abertura   | Preço se afasta 1 tick (5 pts) da abertura no sentido contrário ao ajuste; ordem limite na abertura preenche quando o preço volta ao nível | 500 pts fixos                    |
| **B**  | Trade seco no ajuste | Ordem no próprio ajuste, no viés do dia; preenche no primeiro toque do ajuste                                                              | 500 pts fixos                    |
| **C**  | Pivôs → ajuste       | Regras 3.1 + 4.x sobre os 8 pivôs                                                                                                          | 500 pts fixos                    |
| **D**  | Bolas → ajuste       | Regras 3.2 + 4.x sobre os múltiplos de 1000                                                                                                | 500 pts fixos                    |
| **CD** | Pivôs + bolas        | Regras 3.1 + 3.2 + **3.3 (fusão 300)** + 4.x                                                                                               | 500 pts fixos                    |

Todos com stop de 100 pontos. As variantes com saída no ajuste (C/D/CD, e A) são
reportadas em paralelo, para comparação com o spec anterior.

---

## 7. Parâmetros

Todos no topo de `engine.py`:

```python
TICK        = 5.0      # tick do WIN
STOP        = 100.0    # stop em pontos
ALVO_FIXO   = 500.0    # alvo fixo, em todos os setups
ALVO_NO_AJUSTE = False # True = C/D/CD saem no ajuste (spec anterior)
TICKS_AFAST = 1        # setup A: ticks de afastamento que armam o gatilho
DIST_MIN    = 600.0    # distância mínima nível <-> ajuste
CRUZA_AJ    = 600.0    # ultrapassagem do ajuste que libera o outro lado
RETRACAO    = 500.0    # retração que invalida o próximo nível
FUSAO       = 300.0    # bola x pivô: fica o mais afastado do ajuste
BOLA_PASSO  = 1000.0   # "bolas"
FIBS        = (0.618, 1.000, 1.618, 2.000)
VAL_PONTO   = 0.20     # R$/ponto, por contrato
CONTRATOS   = 6        # lote: realiza parcial de 1/2 e de 2/3
CUSTO_PTS   = 0.0      # custo de ida e volta em pontos

USA_PARCIAL  = True    # saída parcial (5)
PARCIAL_PTS  = 45.0    # onde sai a parcial
PARCIAL_FRAC = 2/3     # fração que sai na parcial (4 de 6) -> resultado 2:1
PARCIAL_STOP = 'medio' # stop do restante: no preço médio da operação (−90);
                       # um número = pts a favor da entrada (0 = na entrada)

REGIME_EXCLUSIVO     = True   # ao cruzar o ajuste, o lado inicial desliga (4.3)
FAVORAVEL_NA_ENTRADA = False  # a barra de entrada só resolve o lado adverso (5.1)

EMA_PER   = 21                # premissa das médias (1)
AJ_JANELA = ('17:00','18:00') # janela do call para validar o ajuste (2.2)
AJ_TOL    = 300.0             # desvio que reprova o dia
```

---

## 8. Como rodar

```bash
python valida_dados.py           # confere o alinhamento das duas bases
python rodar.py                  # backtest completo -> saida/ + console
python auditoria.py 2026-08-21   # dump de um pregão: níveis, status, trades
python auditoria.py premissa     # teste da premissa (retorno ao ajuste sem stop)
```

Saídas em `saida/`: `resumo.json` e um `trades_*.csv` por setup, com data, nível,
lado, preço de entrada, horários e resultado de cada operação.

---

## 9. Decisões de interpretação

Pontos onde o enunciado admitia mais de uma leitura, e o que foi adotado:

1. **"Compra nos pivôs abaixo do ajuste"** — combinado com *"operar a reversão
   até o ajuste"* e com a regra da retração (que fala em *"o preço avança... e
   afastando-se do ajuste"*), a leitura adotada é que o nível precisa ser
   alcançado **enquanto o preço se afasta** do ajuste (novo extremo do dia). Um
   pivô que fique entre a abertura e o ajuste, alcançado na subida rumo ao
   ajuste, não gera entrada — seria compra de rompimento, não de reversão.
2. **Alvo dos setups C/D/CD** — o ajuste dá a **direção** da operação, mas o
   alvo é de **500 pts fixos**, como em A e B (definição do autor da estratégia,
   que substituiu a leitura anterior de sair no próprio ajuste). A variante com
   saída no ajuste segue reportada em paralelo.
3. **Um trade por nível** — "sempre no primeiro toque" foi lido como: cada nível
   vale uma entrada por pregão. Um dia pode gerar várias entradas (média de 1,78
   nos dias que operam, máximo de 6).
4. **`PP` fora do conjunto de níveis** — o indicador vem com `ShowPP = false`, e
   `PP` não é ancorado na abertura como os demais.
