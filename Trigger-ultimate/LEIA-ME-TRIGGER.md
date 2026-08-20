# Trigger Ultimate 11R

Indicador de gatilho para Renko de 50 pts (ajuste **11R** do WIN) e a pesquisa
que o produziu, sobre `base-ohlc-ntsl/profitpro-ohlc-11R.csv` — 20.001 tijolos,
35 pregões, 26/06 a 13/08/2026, exportados do ProfitPro com agressão de compra e
venda, duração da barra, volume e número de negócios.

O indicador desenha **seta acima** do tijolo quando o viés é descendente e
**seta abaixo** quando é ascendente, e o placar simula o trade: entra no
fechamento do tijolo, stop na âncora, alvo em pontos, prazo em tijolos.

> **O resultado principal da pesquisa é negativo, e é o item mais valioso deste
> pacote.** Agressão, tempo, volume e número de negócios **não preveem** nem a
> direção do próximo tijolo nem a sobrevivência do extremo. Tudo que parecia
> sinal se dissolveu em geometria do Renko quando medido contra a régua certa.
> O indicador entrega o que de fato existe: uma calibração exata de
> probabilidade e risco, e um placar que se audita sozinho.
>
> O recorte só de **reversões** (seção 3) foi testado depois, e é o teste mais
> limpo da base — ali o pavio está quase congelado, então o confundidor sai de
> cena. O fluxo continua nulo (AUC 0,505 contra 0,509 do alvo embaralhado). O que
> a reversão dá de real é uma **âncora de stop 2,5× mais barata**.
>
> Os **padrões dos tijolos anteriores** (seção 4) foram a penúltima tentativa:
> 438 regras geométricas, cada uma com sua hipótese nula no Renko sintético. A
> melhor deu lift +0,0523; o máximo sob permutação numa varredura do mesmo
> tamanho é +0,0508 ± 0,0146. **p = 0,42.**
>
> O **score de agressão** (seção 5) é o único teste que passou: permutação dentro
> do pregão dá z = +2,6, **p = 0,004**. Dentro do dia, a agressão ordena os
> sinais. Mas o bootstrap de pregão inclui zero e o efeito é quase todo de um
> lado só — e é a mesma amostra onde ele já tinha dado p = 0,10. Leia a seção 5
> inteira antes de usar.

## Arquivos

| arquivo | função |
|---|---|
| `TriggerUltimate.ntsl` | o indicador, para colar no Editor de Estratégias |
| `base-ohlc-ntsl/pesquisa/` | a pesquisa completa, reproduzível |
| `base-ohlc-ntsl/pesquisa/reversao*.py` | o estudo do subconjunto de reversão (seção 3) |
| `base-ohlc-ntsl/pesquisa/alvo.py`, `padroes*.py` | alvo em pontos e a varredura de padrões (seção 4) |
| `base-ohlc-ntsl/pesquisa/espelho_ntsl.py` | espelho em Python da lógica exata do `.ntsl` |

---

## 1. Como usar

Cole `TriggerUltimate.ntsl` no Editor de Estratégias como **indicador** e aplique
num gráfico Renko 11R.

| input | padrão | o que faz |
|---|---|---|
| `Tijolo` | 50 | pontos por tijolo (11R = 50) |
| `Horizonte` | 8 | prazo em tijolos (máx. 8) |
| `AlvoPontos` | 100 | **andamento exigido em pontos**; 0 volta ao critério "extremo não violado" |
| `Reversao` | 1 | 0 = todos, **1 = só reversão**, 2 = só continuação |
| `Ancora` | 1 | onde fica o stop: 0 = extremo contrário (pavio), 1 = abertura do tijolo |
| **`MinScore`** | **60** | **o regulador de frequência** — ver a curva abaixo |
| `MinBarras` | 4 | **cooldown por lado, em tijolos**: depois de um sinal, o mesmo lado só volta a sinalizar 4 tijolos depois. 0 desliga |
| `PesoAgr` | 100 | peso da agressão a favor da reversão |
| `PesoPav` | 0 | peso do pavio contrário curto |
| `PesoLonge` | 0 | peso da reversão **longe** do topo/fundo recente |
| `PesoFuro`, `PesoPerna`, `PesoLimpa` | 0 | ver seção 4 — medidos como ruído ou invertidos |
| `AgrIni`, `AgrFim` | 0 / 0.30 | rampa da agressão |
| `PavIni`, `PavFim` | 150 / 95 | rampa do pavio |
| `LongeIni`, `LongeFim` | 0 / 3 | rampa da distância ao extremo |
| `JanelaExtremo` | 50 | barras para achar o topo/fundo recente |
| `PavioMaximo` | 0 | teto duro no pavio contrário; 0 desliga |
| `MostrarScore` | false | escreve o score junto da seta |
| `OffsetFrac` | 0.6 | afastamento da seta, em tijolos |
| `MostrarLinhas` | false | ligue **só** em painel separado — `PlotN` desenha em 0..100 |
| `MostrarSetas` | true | desenha ▼ acima e ▲ abaixo |
| `PintarBarra` | false | pinta também o corpo do tijolo |
| `MostrarPlacar` | true | linha de placar na última barra |
| `ExcluirFantasma` | true | ignora tijolo que fechou sem tempo ou sem volume |
| `AguardarFechamento` | true | não desenha no tijolo ainda em formação |
| `DuracaoHistorica` | true | se o compilador reclamar de `BarDurationF[n]`, ponha `false` |

### Sobre `Direita = 0`

**O trigger vem na barra em estudo.** Não há barra de confirmação nem
deslocamento: todo componente do score usa apenas a barra corrente e o passado.

E no Renko isso é melhor que num gráfico de tick. O tijolo fecha num nível
**predeterminado** (`base ± 50`), então o fechamento é conhecido no instante em
que o preço cruza — a seta nasce exatamente no preço de entrada. Com
`AguardarFechamento = true` você não espera barra nenhuma: espera o cruzamento,
que *é* o gatilho. Com `false` a seta aparece no tijolo ainda em formação, mas
repinta, porque o pavio contrário continua crescendo até o fechamento.

O placar mostra **duas** linhas de resultado: a bruta e a que descarta os sinais
cujo caminho até o desfecho passou por tijolo fantasma. **Acredite na segunda** —
seção 6 explica por quê.

### Presets

Medidos sobre as 20.001 barras. `pts/sinal` bruto e limpo (sem fantasma no
caminho); o limpo é o executável.

**A curva de `MinScore`** — é aqui que se regula a frequência. Com `PesoAgr=100`,
`AlvoPontos=100`, `Horizonte=8`, `Reversao=1`, `Ancora=1`, `MinBarras=4`:

| `MinScore` | sinais/pregão | P realizada (limpo) | **pts/sinal limpo** | lado baixa | lado alta |
|---|---|---|---|---|---|
| 0 *(sem filtro)* | 131,9 | 0,325 | **−1,31** | −3,16 | +0,54 |
| 50 | 57,0 | 0,340 | **+1,03** | −1,05 | +3,15 |
| **60** *(padrão)* | **44,5** | 0,349 | **+2,40** | −0,76 | +5,75 |
| 70 | 34,0 | 0,351 | **+2,58** | −0,09 | +5,42 |
| 80 | 25,7 | 0,353 | **+2,94** | 0,00 | +6,20 |

Monotônica, e é o que você pediu: **44,5 sinais por pregão** no padrão, contra os
7,7 da versão de filtros booleanos. Para comparação, com `MinScore=60` e o mesmo
cooldown:

| jogo de pesos | sinais/pregão | pts/sinal limpo |
|---|---|---|
| `PesoAgr=100` | 44,5 | **+2,40** |
| `PesoPav=100` | 51,8 | −0,65 |
| pesos da versão anterior (com `cExt`/`cFuro`) | 28,1 | **−3,12** |

Misturar geometria com agressão **piora** — `cAgr80+cPav20` dá +1,26 e
`cAgr50+cPav50` dá −0,65. É o mesmo achado 4 aparecendo de novo: geometria +
fluxo é pior que fluxo sozinho.

### O cooldown, e por que ele não faz o que parece

`MinBarras = 4` é o cooldown por lado, em **tijolos**: depois de um sinal, aquele
lado fica mudo por 4 tijolos.

Antes de medi-lo, uma correção: na versão anterior eu disse que `MinBarras` "não
melhora nada". Estava medindo errado — o espaçamento contava **sinais** em vez de
tijolos, porque eu tinha feito `reset_index` antes. Corrigido:

| cooldown | sinais/pregão | pts/sinal limpo |
|---|---|---|
| 0 | 47,7 | +1,97 |
| 3 | 46,5 | +2,40 |
| **4** | **44,5** | **+2,40** |
| 8 | 38,1 | +3,13 |

Melhora, mas dentro do ruído — foram 24 combinações de `MinScore` × cooldown
olhadas, e só uma tem IC95 sem o zero, que é exatamente o que se espera por
acaso a 95%. Fica em 4 como padrão porque **custa pouco** (3,2 sinais/pregão) e
espaça as entradas.

O que ele **não** faz é reduzir exposição correlacionada — porque esse problema
não existe aqui:

> **Toda operação resolve em 1 a 3 tijolos. Sempre.**
>
> Nas 5.698 reversões, com alvo 100 e âncora na abertura: 2.674 resolvem em 1
> tijolo, 2.069 em 2, 955 em 3. **Zero estouros de prazo.** O resultado é
> binário — +100 ou −50 — e **47% já se decide no tijolo seguinte ao sinal**.

Como sinais do mesmo lado ficam a 15 tijolos de mediana (mínimo 2) e a operação
dura no máximo 3, medi a fração de sinais que entram com o anterior do mesmo lado
ainda aberto: **0 de 1.671**. Não há trade sobreposto para o cooldown eliminar.

Isso também quer dizer que **`Horizonte = 8` nunca é atingido** na configuração
padrão; 3 bastaria. Deixei em 8 só por margem, porque com `AlvoPontos` maior — ou
com `AlvoPontos = 0`, o critério antigo — o prazo volta a importar.

**Critério antigo "extremo não violado"** (`AlvoPontos = 0`):

| preset | `Reversao` | `Ancora` | `Modo` | `ProbMinima` | `RetornoMinimo` | sinais/pregão | P → realizada | R |
|---|---|---|---|---|---|---|---|---|
| Retorno máximo | 0 | 0 | 1 | — | 2.19 | 36,8 | 0,389 → **0,360** | 2,20 |
| Equilíbrio | 0 | 0 | 2 | 50 | 1.1 | 38,6 | 0,520 → **0,517** | 1,16 |
| Probabilidade | 0 | 0 | 0 | 60 | — | 128,7 | 0,661 → **0,658** | 0,82 |
| Probabilidade forte | 0 | 0 | 0 | 75 | — | 20,1 | 0,794 → **0,803** | 0,76 |
| Reversão, stop na abertura | 1 | 1 | 1 | — | 2.0 | 162,9 | 0,362 → **0,363** | 2,23 |
| Reversão, stop no pavio | 1 | 0 | 0 | 0 | — | 162,9 | 0,620 → **0,621** | 0,90 |
| Reversão forte (pavio 150) | 1 | 0 | 0 | 75 | — | 14,1 | 0,794 → **0,801** | 0,78 |

A calibração acerta dentro de ~1,5 ponto percentual em toda a faixa, inclusive
nas reversões. É o que o indicador tem de sólido.

---

## 2. A regra valiosa

> **A excursão em 4 tijolos é ~110 pontos, sempre. Só o stop muda.**

Medido em todas as faixas de pavio, na base real e no sintético:

| pavio contrário | n | P(extremo sobrevive) | MFE médio | MFE / risco |
|---|---|---|---|---|
| 50 | 1.278 | 0,355 | 109,4 pts | **2,19** |
| 55–65 | 2.803 | 0,404 | 109,2 pts | 1,84 |
| 70–90 | 2.955 | 0,469 | 110,2 pts | 1,41 |
| 95–115 | 3.898 | 0,554 | 110,0 pts | 1,03 |
| 120–150 | 5.477 | 0,646 | 111,4 pts | **0,84** |

O pavio contrário do tijolo do sinal — a máxima num tijolo de baixa, a mínima num
tijolo de alta — é a **única** variável que carrega informação, e ela é uma
**troca, não um ganho**: probabilidade × retorno é constante. Pavio largo acerta
mais e ganha pouco; pavio curto, o contrário. A escolha é de gestão de risco, não
de previsão.

A fórmula embutida no indicador, com `u = pavio / tijolo` (entre 1 e 3):

```
P(extremo sobrevive 4 tijolos) = 0,2422 + 0,1465·u     para u < 3
                               = 0,7940                para u = 3
MFE esperado = 2,2 tijolos     →     R esperado = 2,2 / u
```

**O caso do pavio de 150.** É o teto: o tijolo encostou no limiar de reversão e
não passou. Sobrevive em **80,3%** dos casos — a maior probabilidade da base, ~20
sinais por pregão. O passeio aleatório dá 79,4% para o mesmo caso, então nem esse
é mercado; mas é a leitura de maior acerto disponível, e o indicador a marca com
`Modo=0, ProbMinima=75`.

## 3. O modo reversão

Só os tijolos cujo antecessor tem sentido oposto (`Reversao = 1`). São 5.698
sinais, 162,9 por pregão, 28% dos tijolos da base.

### A reversão não é um recorte, é outra geometria

Para nascer um tijolo contrário o preço precisa percorrer **100 pontos** contra a
base, não 50: o tijolo abre em `base∓50` e fecha em `base∓100`. Como a máxima
corrente desde o fechamento anterior começa perto da base, **o pavio contrário
de uma reversão já nasce grande**. Medido:

| pavio contrário | continuação | reversão |
|---|---|---|
| 50–65 | 38,1% | **0,00%** |
| 70–90 | 27,6% | 0,02% |
| 95–115 | 18,0% | 34,6% |
| 120–145 | 14,4% | 56,8% |
| 150 | 2,0% | 8,6% |

Ou seja: **"só reversão" é, geometricamente, quase um filtro de pavio largo.**
Por isso ela parece muito melhor — `ok` 0,620 contra 0,479 da continuação. Mas é
a mesma troca da seção 2 outra vez, não uma vantagem nova. Estratificando por
faixa de pavio, a diferença some:

| faixa | n reversão | ok reversão | n continuação | ok continuação | diferença |
|---|---|---|---|---|---|
| 95–115 | 1.970 | 0,5675 | 1.928 | 0,5394 | +0,028 |
| 120–145 | 3.236 | 0,6245 | 1.541 | 0,6204 | **+0,004** |
| 150 | 491 | 0,8004 | 209 | 0,8086 | −0,008 |

E contra o passeio aleatório o lift é praticamente zero (−0,007 / −0,002 /
+0,005). O subconjunto obedece à **mesma curva P(u)** já embutida no indicador —
2,15 → 0,557 previsto contra 0,559 real; 2,44 → 0,600 contra 0,602; 3,0 → 0,794
contra 0,800. Nenhuma constante nova foi necessária.

### O que muda de verdade: a âncora do stop

Esse é o ganho prático do modo reversão. Com o pavio nascendo em ~125 pts, o stop
no extremo contrário fica caríssimo. A alternativa é ancorar na **abertura do
tijolo de reversão** — o nível que, se perdido, desfaz a própria reversão — que
fica sempre a 1 tijolo do fechamento:

| âncora | risco | ok | R | pts/sinal | **pts/sinal sem fantasma** |
|---|---|---|---|---|---|
| pavio (`Ancora=0`) | 125,8 | 0,621 | 0,90 | +5,66 | **−1,19** |
| abertura (`Ancora=1`) | 50,0 | 0,363 | 2,23 | +5,19 | **+0,30** |

Praticamente o mesmo resultado bruto com **2,5× menos risco** — e é a única das
duas que continua positiva depois de descartar os caminhos com tijolo fantasma.
Para comparação, a continuação com a mesma âncora dá **−0,60**.

Com `Ancora=1` a probabilidade é **constante**: 0,3623 medida, e o ajuste linear
em `u` dá inclinação −0,0037, ou seja, zero. O pavio deixa de informar qualquer
coisa porque deixou de ser o risco. Não há o que filtrar — use `Modo=1`.

## 4. Alvo em pontos e padrões dos tijolos anteriores

O critério original — "o extremo contrário não é violado em 4 tijolos" — é fraco:
**ele não exige que o preço ande**. Um sinal parado 4 tijolos conta como acerto.
Por isso ele marcava praticamente toda reversão (162,8 por pregão). O critério
novo (`AlvoPontos > 0`) é explícito:

> alcançar **+G pontos** a favor **antes** de violar a âncora, em até `Horizonte`
> tijolos.

A ordem de eventos assume sempre o **pior caso**: se o tijolo violou a âncora, é
stop, mesmo que o fechamento já estivesse no alvo. O Renko não diz o que veio
primeiro dentro do tijolo, então o número é conservador por construção.

**A probabilidade de referência.** Com `j = risco / (alvo + risco)` — a
probabilidade "justa" —, ajustada sobre 56.683 reversões sintéticas:

```
P = j · (1,1894 − 0,187·j)
```

| alvo | j (justa) | fórmula | passeio aleatório |
|---|---|---|---|
| 50 | 0,500 | 0,548 | **0,548** |
| 100 | 0,333 | 0,376 | **0,378** |
| 150 | 0,250 | 0,286 | **0,286** |
| 200 | 0,200 | 0,230 | **0,230** |

O acaso fica **acima** da probabilidade justa — é o overshoot da discretização do
Renko. A base real dá 0,363 para o alvo de 100, ou seja **abaixo do acaso** de
novo, mas ainda acima do breakeven de 1/3. Daí os +4,47 pts/sinal brutos.

### A varredura de padrões

Montei 34 condições elementares sobre os tijolos anteriores, todas geométricas de
propósito, para poderem ser calculadas **identicamente** no Renko sintético — que
vira a hipótese nula de cada regra, com n grande:

- tamanho e deslocamento da perna quebrada, e o pavio médio dela (tendência
  limpa contra tendência com repique)
- pavio do próprio tijolo e dos dois anteriores
- eficiência (deslocamento / amplitude) em 10, 20 e 50 tijolos
- número de inversões em 10, 20 e 50 (choppiness)
- distância ao topo/fundo recente e furo do extremo (falso rompimento)
- posição no range, **sempre relativa ao sentido do sinal**

Combinadas 1 a 1 e 2 a 2: **438 regras**. O veredito:

| teste | resultado |
|---|---|
| correlação lift treino × lift teste | **−0,002** |
| regras acima do acaso | 95 de 438 (22%) |
| lift máximo observado | +0,0523 |
| **lift máximo sob permutação, varredura do mesmo tamanho** | **+0,0508 ± 0,0146** |
| **p corrigido para as 438 regras** | **0,42** |

A melhor de 438 regras é **exatamente o que uma varredura de 438 regras produz em
ruído**. Esse é o teste que quase ninguém faz e é o único que importa quando se
varre: comparar o máximo observado com o máximo do nulo, não com o nulo médio.

### O filtro que ficou

Duas condições passaram no controle por lado com simetria quase perfeita — o que
elimina a deriva do período — e 5/5 nas dobras de walk-forward:

- `PavioMaximo = 110` — o terço mais apertado das reversões
- `DistExtremo = 0.5` — a reversão acontecendo **no** topo/fundo das 50 barras
  anteriores, não no meio do range

Juntas levam a base de **162,8 para 7,7 sinais por pregão**:

| | P | pts/sinal | **limpo** |
|---|---|---|---|
| todas as reversões | 0,363 | +4,47 | **−2,29** |
| só `pavio ≤ 110` | 0,368 | +5,17 | **−0,51** |
| só no extremo | 0,356 | +3,43 | **−5,35** |
| **as duas** | **0,421** | +13,10 | **+4,72** |

O acaso dá 0,388 para a mesma condição, então o lift é +0,033 — e é justamente o
que a permutação diz não valer nada. O IC95 do pts/sinal limpo é
**[−4,15, +14,57]**: inclui o zero. E note as três primeiras linhas: **cada
condição sozinha é negativa**; só a interseção é positiva. Isso é o retrato de um
achado de varredura, não de uma regra.

> ### Correção: esse filtro estava invertido
>
> Ele foi o padrão de uma versão do indicador. **Estava errado.** Medindo cada
> componente em quartis sobre o conjunto limpo — que é o único executável — a
> condição "no extremo" anda **ao contrário**:
>
> | componente | P (1º quartil → último) | pts/sinal |
> |---|---|---|
> | `cExt` — reversão **no** topo/fundo | 0,326 → **0,297** | −1,11 → −5,49 |
> | `cFuro` — falso rompimento do extremo | 0,329 → **0,287** | −0,72 → −7,01 |
> | `cPav` — pavio curto | 0,309 → 0,330 | −3,64 → −0,51 |
> | `cAgr` — agressão a favor | 0,294 → **0,340** | −5,90 → **+1,04** |
>
> O `+4,72` da interseção era interação pura, sem apoio nas marginais — o que eu
> já tinha sinalizado ("cada condição sozinha é negativa") sem tirar a
> consequência. Com o jogo de pesos daquela versão, o resultado limpo é
> **−4,13 pts/sinal**, o pior de todos os presets. Os filtros `DistExtremo` e
> `PavioMaximo` obrigatórios saíram; quem quiser o efeito use `PesoLonge`, que
> aponta para o outro lado.

## 5. O score de agressão

É o que substituiu os filtros booleanos e o que regula a frequência. Cada
componente vira uma rampa 0..1 e entra com um peso, no molde do
`PivoReversao_Claude` — mas **os pesos vieram da tabela acima**, não de palpite:
só `cAgr` e `cPav` têm gradiente monotônico nos quartis, e como misturar os dois
piora, o padrão é agressão pura.

O componente é `aFavor = sentido × desequilíbrio de agressão`, com rampa de 0 a
0,30. Num tijolo de baixa isso é agressão **vendedora**; num de alta,
**compradora**. É a agressão empurrando no sentido da reversão que acabou de
nascer.

### O único teste da pesquisa que passou

Permutação de `aFavor` **dentro do pregão e do lado** — preserva a deriva, a
composição do dia e o número de sinais, destrói só a ligação entre agressão e
desfecho:

| `MinScore` | pts observado | nulo | z | **p** |
|---|---|---|---|---|
| 50 | +0,69 | −2,22 ± 1,22 | +2,39 | **0,0075** |
| 60 | +1,97 | −1,94 ± 1,48 | +2,63 | **0,0042** |
| 70 | +2,09 | −1,76 ± 1,81 | +2,13 | **0,0175** |
| 80 | +2,28 | −1,59 ± 2,20 | +1,76 | 0,0458 |

Depois de tudo que não passou, esse passou. **Dentro do dia, a agressão ordena os
sinais.**

### Por que ainda assim não é edge

Três coisas seguram a conclusão:

1. **O bootstrap de pregão inclui zero** em todos os limiares. Em `MinScore=60`:
   +1,97 pts com IC95 **[−0,65, +4,63]**. A permutação remove a variação entre
   pregões; o bootstrap não. O efeito é pequeno perto do que varia de um dia
   para o outro — e é essa variação que você enfrenta operando.
2. **A assimetria por lado.** Em `MinScore=60`: **+4,30 pts na alta contra −0,19
   na baixa.** É a mesma assimetria que apareceu na seção 6 e não sumiu. Num
   período em que o índice caiu 3.825 pontos, um efeito que só existe na compra
   é suspeito por construção.
3. **Walk-forward**: só 3 de 5 dobras positivas em `MinScore=60`.

E o mais importante: **é a mesma amostra**. Esse efeito já tinha aparecido com
p = 0,10–0,16 na seção 6; reencontrá-lo com um alvo melhor definido não é
evidência nova, é a mesma agressão medida de outro jeito. O que mudou foi a
qualidade da medição, não a quantidade de evidência.

## 6. A outra regra valiosa: o tijolo fantasma

**17,9% dos tijolos da base fecham com duração zero.** São gaps de abertura e
spikes em que um único negócio atravessa vários níveis de preço de uma vez.

Eles destroem qualquer backtest de Renko feito sem cuidado:

| | P(continuação) |
|---|---|
| quando o tijolo seguinte é fantasma (8,2% dos casos) | **0,966** |
| quando é um tijolo normal | 0,660 |

Seguir o sentido do tijolo parece render **+2,82 pts por tijolo** — um edge
enorme. Mas ele está inteiramente dentro dos 8,2% de casos em que o tijolo
seguinte é fantasma, e nesses **não existe execução no fechamento do tijolo do
sinal**: o preço saltou os dois níveis no mesmo negócio. Zerando só o ganho de
papel desses casos, o resultado vira **−1,14 pts por tijolo**.

No preset padrão, **25,9% dos sinais** têm um tijolo fantasma no caminho de 4
tijolos. Por isso o placar do indicador mostra **duas** linhas de resultado:
a bruta e a que descarta esses sinais. A segunda é a verdadeira. No padrão:
6,80 pts/sinal bruto contra **0,47** limpo.

O input `ExcluirFantasma` (padrão `true`) já impede o indicador de sinalizar
*sobre* um tijolo fantasma.

## 7. O que foi testado e não sobreviveu

Construí 60+ features causais a partir de agressão, tempo, volume e negócios:
desequilíbrio de agressão (`buy−sell`/`buy+sell`), delta acumulado em 5/10/20
tijolos e no dia, participação da agressão no volume, tamanho médio do negócio,
velocidade (pts/s), fluxo (contratos/s), intensidade (negócios/s), aceleração
contra o tijolo anterior, z-scores móveis de 100 tijolos, divergência entre
sentido do tijolo e sentido da agressão, absorção (divergência ponderada por
volume), sequência de tijolos no mesmo sentido, choppiness, posição no range,
hora e posição na sessão.

**Achado 1 — quase tudo era o pavio disfarçado.** Isolado, o desequilíbrio de
agressão parecia forte: num tijolo de baixa com agressão compradora dominante o
extremo sobrevivia em 60,5% dos casos contra 38,8% quando a venda dominava. Mas
tijolo lento e pesado *tem* pavio grande. Estratificando por faixa de pavio, o
efeito desaparece: as linhas ficam planas.

**Achado 2 — a régua do passeio aleatório.** Gerei um Renko sintético de 181.822
tijolos a partir de passeio aleatório puro, com as mesmas regras (tijolo de 50,
reversão em 100, tick de 5, extremos travados no fechamento). Ele reproduz a base
real quase exatamente:

| métrica | base real | passeio aleatório |
|---|---|---|
| P(continuação) | 0,6855 | **0,6882** |
| P(extremo sobrevive 4 tijolos) | 0,5163 | **0,5151** |
| ok, pavio 50–55 | 0,377 | **0,381** |
| ok, pavio 125–150 | 0,669 | **0,666** |
| MFE médio | 110,3 pts | **110,6 pts** |
| R médio | 0,077 | **0,089** |

O breakeven geométrico do Renko é exatamente **2/3**: continuar custa 50 pontos,
inverter custa 100, então um martingale continua em 100/150 dos casos. A base
real fica em 0,6855 — *abaixo* dos 0,6882 do sintético com a mesma discretização.
Não há momentum a extrair.

**Achado 3 — direção é imprevisível, mas "limpo ou picotado" não era.** Depois de
normalizar cada sinal pela expectativa do acaso, o resíduo de direção
(`lift_cont`) não sobrevive fora da amostra (correlação treino×teste **−0,15**),
mas o resíduo de sobrevivência do extremo (`lift_ok`) dava **+0,28**. Isso
sugeria que dá para prever se o movimento vai ser de mão única, mesmo sem saber
o lado. Testado a fundo, não se sustentou: em condições isoladas a correlação cai
para **0,072**, cada decil fica dentro do intervalo de confiança de zero, e a
persistência de picotamento é **exatamente nula** — o número de inversões nos
próximos 4 tijolos é ~1,39 independentemente do passado (corr **+0,002**), apesar
de volume e duração serem bem persistentes (corr 0,43 a 0,63). **O Renko
normaliza a volatilidade para fora**: regime de volatilidade vira tijolos por
minuto, não estrutura de caminho.

**Achado 4 — o teste final.** Gradient boosting com walk-forward de 5 dobras
sobre 43 features, contra alvo embaralhado:

| modelo | AUC fora da amostra |
|---|---|
| só geometria (pavio) | **0,6166** |
| geometria + fluxo | 0,6058 |
| só fluxo | 0,5853 |
| alvo embaralhado | 0,4981 |

Adicionar fluxo à geometria **piora**. O fluxo sozinho bate o acaso com z = 23,9,
mas só porque reconstrói o pavio — tijolo lento e pesado tem pavio grande. Não há
informação além da geometria.

**Achado 5 — agressão dentro das reversões: o teste mais limpo, e o que chegou
mais perto.** Nas reversões o pavio já nasce entre 95 e 150 (99,98% dos casos),
ou seja, **o confundidor que enterrou o fluxo nos achados 1 e 4 está quase
congelado**. É o melhor lugar da base para testar agressão. Refiz tudo aqui, com
features que só existem numa reversão: tamanho da perna quebrada, agressão
acumulada durante essa perna, contraste entre a agressão da perna e a do tijolo
que a quebrou, exaustão (volume por tijolo deslocado), velocidade e volume do
tijolo de reversão relativos à perna.

O ML fora da amostra, dentro das reversões:

| modelo | AUC |
|---|---|
| geometria (pavio + contexto) | 0,5436 |
| **fluxo** | **0,5047** |
| geometria + fluxo | 0,5210 |
| alvo embaralhado | 0,5086 |

O fluxo empata com o alvo embaralhado. Nos decis controlados por faixa de pavio,
nenhuma feature move o `ok` mais que 0,05 — dentro do ruído (IC95 = ±0,028 por
bucket).

**Mas o pnl mexeu.** `a_favor = sentido × desequilíbrio de agressão` acima de
0,15 rendia 6,1 pts no treino e 9,1 no teste, e — diferente de tudo que veio
antes — **continuava positivo depois de descartar os caminhos com fantasma**
(+5,6). Quatro controles depois:

- **Por lado**: o efeito vive quase todo no lado comprado (limpo +2,77 na alta
  contra −0,44 na baixa), e no lado vendido o treino dá −1,46 contra +13,7 no
  teste. Instabilidade total.
- **Permutação intra-pregão** (embaralha `a_favor` dentro de cada dia, preserva
  deriva e composição): excesso observado +1,81 a +2,29 pts, nulo −0,5 ± 2,2,
  **z = 1,0 a 1,25, p = 0,10 a 0,16**. Não passa.
- **Walk-forward** em 5 blocos de 7 pregões: excesso positivo em 4/5, mas o pnl
  limpo só em 3/5, oscilando de −2,9 a +7,3.
- **Sensibilidade ao limiar**: o efeito cresce monotonicamente até +23 pts/sinal
  em `a_favor > 0.35` — com n caindo para 269. Ganho implausível com amostra
  minguando é assinatura de sobreajuste, não de regra.

Corrigindo pelo número de regras varridas, não sobra nada. É o achado mais
próximo de sobreviver em toda a pesquisa, e ainda assim **não sobrevive**. Está
no indicador como `AgressaoMinima` (padrão −1, desligado) justamente para você
poder ligá-lo e deixar o placar julgar numa base maior que a minha. Não é uma
recomendação.

**Uma armadilha que evitei.** No recorte, sinais de baixa rendem bem mais que os
de alta (R 0,217 contra −0,002 no pavio de 50). É o índice ter caído 3.825 pontos
nos 35 pregões da amostra. Não está no indicador, e não deve estar.

## 8. Limites honestos

- **35 pregões é pouco** para descartar efeitos fracos. O que dá para afirmar é
  que não há nada forte o bastante para aparecer em 20.001 tijolos.
- A conclusão vale para o **fluxo agregado por tijolo**, que é o que o Renko
  entrega. Fluxo dentro do tijolo (fita, book, tempo×preço) não foi testado —
  não está nesta base, e é onde eu procuraria em seguida.
- Vale para **WIN em 11R**. Outro ativo ou outro tamanho de tijolo pede refazer.
- O indicador **não tem edge**. Ele mede risco e probabilidade com precisão. Com
  custo de ~5 pts por round-trip no WIN, nenhum preset fica positivo.
- O modo reversão com `Ancora=1` é o **menos ruim** (+0,30 pts/sinal limpo,
  contra −0,60 da continuação), mas +0,30 não paga corretagem. O que ele entrega
  de real é risco 2,5× menor pelo mesmo resultado bruto.
- O preset padrão (score de agressão, `MinScore=60`, cooldown 4) dá **+2,40
  pts/sinal limpo** em 44,5 sinais/pregão. É o melhor número honesto do pacote, e
  ainda assim com IC95 [−0,59, +5,30] e +5,75 na compra contra −0,76 na venda.
  Com ~5 pts de custo por round-trip, a expectativa realista continua sendo
  **zero ou negativa**. O que o score resolve é **frequência e ordenação**, não
  expectativa.

## 9. Reproduzir

```bash
cd base-ohlc-ntsl/pesquisa
python dados.py          # carga e sanidade da base
python universo.py       # universo de sinais e decis
python sintetico.py      # gera o Renko de passeio aleatorio (~3 min)
python lift.py           # varredura normalizada pela geometria
python ml_lift.py        # geometria x fluxo x tudo
python calibracao.py     # a tabela embutida no .ntsl
python reversao.py       # reversao x continuacao, controlado por pavio
python reversao_fluxo.py # agressao DENTRO das reversoes (o teste limpo)
python reversao_regra.py # ancora do stop + a regra de agressao
python reversao_valida.py# os 5 controles que derrubaram a regra (~2 min)
python reversao_calib.py # calibracao do modo reversao
python alvo.py           # alvo em pontos: real x acaso
python padroes.py        # varredura de 438 padroes de tijolos anteriores
python padroes_valida.py # o teste do maximo sob permutacao (~1 min)
python padroes_fantasma.py # o que sobra depois de descartar o fantasma
python score.py          # componentes em quartis + curva de MinScore
python score_valida.py   # permutacao e bootstrap do score (~2 min)
python cooldown.py       # cooldown em tijolos, sobreposicao e pts por pregao
python espelho_ntsl.py   # espelho da logica do indicador + placar dos presets
```

Só precisa de `numpy`, `pandas` e `scikit-learn`.

---

### Nota de construção

A base vem em ordem cronológica inversa e com o rótulo do `Plot2` trocado:
a coluna `Export_OHLC` é na verdade `AgressionVolSell` (ver `Export_OHLC.ntsl`).
`pesquisa/dados.py` corrige as duas coisas na carga.
