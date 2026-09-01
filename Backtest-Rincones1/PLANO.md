# Plano operacional — WIN, gráfico de 10.000 ticks

> **Este arquivo é gerado.** Rode `python rodar.py && python plano.py`.
> Os números saem de `saida/resumo.json`, os mesmos do
> [relatorio.html](relatorio.html). O texto do procedimento é fixo; se
> você mudar uma regra, mude aqui **e** em [ESTRATEGIA.md](ESTRATEGIA.md).

Companheiro operacional de [RESULTADOS.md](RESULTADOS.md). O relatório diz
**o que foi medido**; este arquivo diz **o que eu faço na frente da tela**.

---

## 0. O contrato

Eu opero **um** setup, com **um** tamanho de risco, seguindo as regras 1 a 6
deste arquivo. As regras não mudam durante o pregão. Não mudam depois de uma
perda. Não mudam depois de um ganho. Mudam apenas na **revisão mensal** da
§ 10, com os dados na mão.

A única coisa que eu avalio ao fim do dia é **se segui o plano** — não quanto
ganhei. A § 7 explica por que, com os números que tornam isso não uma frase
bonita, mas a leitura correta dos dados.

Assinado: ____________________   Data: __ / __ / ____

---

## 1. O que eu opero — e o que eu não opero

| | |
|---|---|
| **Ativo** | WIN (mini índice) |
| **Gráfico** | candle de **10.000 ticks** |
| **Setup** | **A — tendência (pullback na média)**, e só ele |
| **Direção** | pelo empilhamento das EMAs 21 / 42 / 72 |
| **Lado** | compra e venda |
| **Posições** | **uma por vez**. Sinal que chega com posição aberta é ignorado |

**O que eu NÃO opero:**

- **Setup C (reversão em consolidação).** Mede negativo nas duas bases, em
  toda configuração testada. Não está no plano e não entra por exceção.
- **Setup B (reversão no afastamento).** É positivo, mas mais fraco e com o
  dobro de rebaixamento. Fica **fora** até uma revisão decidir promovê-lo. Se
  eu quiser operá-lo, é uma decisão de revisão mensal, não de pregão.
- **Qualquer coisa que o indicador não marcou.** Se não saiu a seta A, não
  existe trade — por mais óbvio que o gráfico pareça.

> Por que só o A: ele é o melhor dos três nas duas bases, em **todas** as
> colunas — valor esperado, `t`, fator de lucro e rebaixamento. E a 2.2
> trades por pregão ele é operável à mão sem pressa.

---

## 2. O gatilho — quando existe trade

O indicador faz a conta; eu confiro o contexto. **Todos os seis** têm de
estar verdadeiros. Um único "não" e não há trade.

| # | Verificação | |
|---|---|---|
| 1 | As três médias estão **empilhadas na ordem** (21 acima de 42 acima de 72, ou o inverso) | ☐ |
| 2 | O leque entre elas está **aberto** — não emboladas | ☐ |
| 3 | A barra do gatilho **toca** uma das três médias | ☐ |
| 4 | O indicador marcou a seta do **setup A** | ☐ |
| 5 | A seta aponta **a favor** do empilhamento | ☐ |
| 6 | Estou dentro do horário e **sem posição aberta** | ☐ |

Os itens 4 e 5 já embutem o que o indicador mede e eu não preciso conferir a
olho: índice de esforço ≥ 0,8, corpo ≤ 50% do range, meio do corpo do lado
certo, e o eixo do deslocamento não sendo o dominante.

**A leitura econômica, em uma frase:** o preço voltou para a média, alguém
agrediu contra a tendência exatamente ali, e **falhou**. Eu entro do lado de
quem não falhou.

---

## 3. A entrada — a regra da barra seguinte

```
barra t      o gatilho fecha. Eu envio a limitada no MEIO do candle,
             (máxima + mínima) / 2, arredondado ao tick.
barra t+1    ou ela preenche AQUI, ou eu CANCELO.
barra t+2    não existe. O sinal morreu.
```

**Não preencheu, acabou.** Não persigo o preço, não entro a mercado "para não
perder", não deixo a ordem no livro para ver no que dá. Cancelo e volto a
esperar.

Cerca de **12% dos sinais serão abortados** — no WINV26, 5 de 36 sinais do
setup A; no WINFUT, 9 de 83. Isso não é falha de execução: é **o plano
funcionando**. Um sinal abortado entra no diário como *aderência cumprida*,
exatamente como um trade vencedor.

> **Por que esta regra existe.** Medida, ela quase não muda o resultado —
> melhora uma base, piora a outra, pouco dos dois lados. Ela existe pelo que
> impede: que eu fique com uma ordem esquecida no livro, e que eu negocie um
> sinal de dez minutos atrás como se fosse de agora. Ela é uma **regra de
> disciplina que custa quase nada** — o melhor tipo de regra que existe.

---

## 4. A gestão — decidida antes, executada sem opinião

| | |
|---|---|
| **Stop inicial** | **100 pontos** da entrada |
| **Parcial** | **50% da posição em +100 pontos** |
| **No momento da parcial** | o stop do restante vai para a **entrada** (zero a zero) |
| **Alvo do restante** | **+300 pontos** |
| **Saída forçada** | fechamento do pregão |

Resultado por trade, por contrato de lote cheio:

| desfecho | pontos | R$ | frequência medida |
|---|---|---|---|
| stop antes da parcial | −100 | −20,00 | 37% |
| parcial e depois zero a zero | +50 | +10,00 | 32% |
| parcial e depois alvo | +200 | +40,00 | 32% |

**O stop nunca se afasta.** Ele anda **uma vez**, para o zero a zero, e só
depois que a parcial saiu. Mover o stop para longe é o erro que transforma
uma perda planejada de 100 pontos numa perda que não estava no plano.

**A parcial não é opcional.** Ela é o que compra o direito de deixar o resto
correr até +300 sem risco. Sem ela o plano é outro, e os números são outros.

---

## 5. Tamanho e limites do dia

**Risco por trade** = 100 pontos = **R$ 20,00 por contrato**.

Regra de dimensionamento:

```
contratos = (risco máximo por trade em R$) / R$ 20,00

com risco máximo por trade = 1% do capital da conta
```

**Limites rígidos do pregão** — atingiu, o dia acabou, sem discussão:

| limite | valor | por quê |
|---|---|---|
| **3 stops no dia** | −300 pts (R$ 60,00 / contrato) | o pior pregão medido foi -210 pts |
| **1 violação de regra** | — | erro de processo fecha o dia, mesmo no lucro |

O segundo limite é o mais importante e o mais fácil de ignorar. Um erro de
processo num dia de lucro é **mais perigoso** que um num dia de prejuízo,
porque o resultado o recompensa.

---

## 6. A rotina do pregão

**Antes de abrir (5 minutos)**

- Gráfico em 10.000 ticks, indicadores da família carregados, EMAs 21 / 42 / 72 visíveis
- Anotar no diário: o regime de ontem, e onde as médias estão hoje
- Reler as regras 1 a 4 deste arquivo. Sim, todo dia.
- Definir o número de contratos **antes** do primeiro sinal

**Durante**

- Só existe ação quando a seta A imprime. O resto do tempo eu **espero**.
- Em ~2.2 trades por pregão, a maior parte do dia é espera. Isso é o trabalho,
  não uma pausa dele.
- Enviada a ordem: uma barra. Preencheu ou cancelou.
- Aberta a posição: stop, parcial e alvo já estão definidos. Nada a decidir.

**Depois**

- Preencher o diário da § 9, **incluindo os sinais abortados**
- Calcular a **nota de aderência** do dia (§ 7)
- Não olhar o resultado acumulado. Ele é olhado uma vez por mês, na revisão.

---

## 7. Como eu meço sucesso: aderência, não resultado

### 7.1 A razão, com os números

Estes são os números do setup A, stop 100, **descontando 5 pontos de custo por
trade** — a leitura honesta, não a bruta:

| | WINV26 | WINFUT |
|---|---|---|
| acerto por trade | 73% | 63% |
| valor esperado por trade | +65,0 pts | +36,8 pts |
| **desvio** por trade | 123 pts | 125 pts |
| pregões positivos | 83% | 61% |
| pior pregão | -105 pts | -210 pts |
| maior sequência de pregões negativos | 1 | 4 |
| chance de uma **semana** fechar negativa | 1% | 13% |
| rebaixamento máximo | 225 pts (R$ 45,00) | 510 pts (R$ 102,00) |

Olhe a linha do **desvio**: 125 pontos por trade, contra um valor esperado de
+36,8. O ruído é **três vezes maior que o sinal** em cada operação isolada.
Isso não é um defeito da estratégia — é como toda vantagem pequena se parece
de perto.

As consequências, que eu preciso ter aceitado **antes** de elas acontecerem:

- **39% dos pregões fecham no vermelho.** Um dia negativo é o caso comum, não
  um sinal de nada.
- **4 pregões negativos seguidos já aconteceram** na amostra medida. Vão
  acontecer de novo.
- **13% de chance de uma semana inteira fechar negativa**, com a vantagem
  totalmente intacta.
- Duas perdas seguidas: 14% de chance. Três: 5%. Não é raro.

**Conclusão operacional:** o resultado de um dia, e mesmo de uma semana, **não
contém informação** sobre se eu operei bem. Julgar o processo pelo resultado
diário é ler ruído como se fosse mensagem — e a reação a esse ruído é o que
destrói planos que funcionavam.

A aderência, ao contrário, eu **observo diretamente**, todo dia, sem erro de
medição. É a única coisa que eu controlo. Então é a única coisa que eu meço.

### 7.2 A nota de aderência

**Por trade** — seis itens, cada um vale 1:

| # | item |
|---|---|
| 1 | O contexto tinha as seis marcas da § 2, todas |
| 2 | Entrei pela limitada no meio do candle, no preço certo |
| 3 | A ordem valeu **uma barra**, e eu cancelei quando não preencheu |
| 4 | O stop entrou a 100 pontos, imediatamente |
| 5 | A parcial saiu a +100 e o stop foi para o zero a zero |
| 6 | Não mexi em nada depois disso |

**Por pregão** — quatro itens, cada um vale 1:

| # | item |
|---|---|
| 7 | Não operei nenhum sinal fora do setup A |
| 8 | Respeitei o limite de perda do dia |
| 9 | Registrei tudo no diário, inclusive os abortados |
| 10 | Não mudei o tamanho da posição no meio do pregão |

```
nota do dia = (pontos obtidos) / (pontos possíveis) × 100
```

**A regra que dá sentido a tudo isto:**

> **Um trade vencedor tomado fora das regras conta como FALHA.**
> Ele vale 0 na nota, e vale um registro em vermelho no diário.

Se essa regra não valer, a nota de aderência vira um enfeite: o resultado
volta a mandar, e o plano deixa de existir nos dias em que ele mais importa.

**Metas:**

- **≥ 95% na semana** — é o padrão de operação
- **< 90% na semana** — parar de operar e reler o plano; o problema é de
  execução, e mexer em parâmetro nesse estado só troca um problema por dois
- **100% num dia de prejuízo** — isso é um **dia bem-sucedido**. Anotar como tal.

---

## 8. Os cinco erros que este plano existe para impedir

**1. Perseguir o sinal abortado.** "Ele foi embora sem mim." Vai acontecer com
12% dos sinais, todo mês. A regra da barra seguinte existe exatamente para
tirar essa decisão da minha mão no momento em que eu estou menos apto a
tomá-la.

**2. Afastar o stop.** É o erro que muda a distribuição inteira: troca uma
perda de 100 pontos, que estava no plano, por uma perda de tamanho
desconhecido. Todos os números deste arquivo deixam de valer no instante em
que isso acontece uma vez.

**3. "Este aqui é diferente."** Setup C, sinal contra a tendência, entrada
sem gatilho. O setup C foi medido e perde nas duas bases; a intuição de que
*este* é diferente não tem como ser distinguida, no momento, do desejo de
operar.

**4. Mexer no lote pelo resultado.** Dobrar depois de perder é tentar
recuperar num trade o que a distribuição devolve em vinte. Aumentar depois de
ganhar é a mesma aposta, com o disfarce de confiança. O lote é definido antes
do pregão e não muda dentro dele.

**5. Operar por tédio.** São ~2.2 trades por pregão. A maior parte do dia é
espera, e o tédio é uma sensação — não um sinal. Se eu não consigo esperar,
o problema não é a estratégia.

---

## 9. O diário

Uma linha por **sinal** — inclusive os abortados.

| campo | o que anotar |
|---|---|
| data / hora | do fechamento da barra do gatilho |
| lado | compra ou venda |
| preço da limitada | o meio do candle, arredondado |
| preencheu? | sim / **abortado** |
| desfecho | alvo / zero a zero / stop / fim de pregão |
| pontos | resultado, em pontos |
| **nota de aderência** | 0 a 6 |
| **o que eu senti** | uma linha, honesta |

A última coluna é a que descobre os padrões. "Entrei com pressa porque o
anterior tinha stopado" é a informação que nenhuma métrica de desempenho
captura, e é onde estão os erros repetidos.

No fim do mês: contar quantos trades tiveram **nota 6**. Essa contagem é o
placar do mês. O resultado em reais é uma consequência, e será olhado depois
dela.

---

## 10. Revisão e disjuntores

**A revisão é mensal, em data marcada.** Nunca no meio de uma sequência ruim,
nunca no meio de uma boa. Na revisão eu olho, nesta ordem:

1. A **nota de aderência** média do mês
2. Quantos sinais foram abortados, e se isso ficou perto de 12%
3. O resultado, em pontos, contra o valor esperado de +36,8 por trade
4. O **custo real** cobrado pela corretora, comparado com os 5 pontos por
   trade que os números desta página já descontam

**Disjuntores** — automáticos, não opinativos:

| gatilho | ação |
|---|---|
| rebaixamento de **510 pts** (R$ 102,00) | reduzir o lote à metade |
| rebaixamento de **1020 pts** (R$ 204,00) | parar de operar e reabrir o backtest |
| aderência < 90%% na semana | parar de operar; treinar em simulador |
| 5 pregões negativos seguidos | parar por um dia e reler este arquivo |

O primeiro disjuntor está no **pior rebaixamento já medido**. Chegar nele é
normal. O segundo é o dobro dele: chegar lá já é evidência de que alguma
coisa mudou — no mercado ou em mim — e merece medição, não persistência.

O último é sobre estado mental, não sobre estatística: 4 pregões negativos
seguidos já aconteceram na amostra, então 5 não prova nada. Mas depois de 5 eu
não sou a mesma pessoa na frente da tela, e é essa pessoa que o disjuntor
protege.

---

## 11. O que este plano herda de incerto

Ler antes de dimensionar posição. Está tudo em [RESULTADOS.md § 9](RESULTADOS.md).

- **Amostra pequena.** 12 e 33 pregões com trade. Os `t` medidos são bons, mas
  sobre poucas observações.
- **As duas bases não são independentes** — o WINFUT contém o WINV26 inteiro.
  Concordarem é menos confirmação do que parece.
- **Os parâmetros foram varridos nas mesmas bases** em que são avaliados. Há
  sobreajuste embutido, e o desempenho real tende a ser pior que o medido.
- **A ordem limitada é dada por preenchida assim que o preço toca o nível.** Na
  prática existe fila, e nem todo toque preenche — este é o otimismo que mais
  pesa contra os números acima.
- **Sem filtro de horário, rolagem ou vencimento.**

Nada disso é motivo para não operar o plano. É motivo para operá-lo **pequeno**
até que os seus próprios registros, e não os meus, digam que ele funciona.

