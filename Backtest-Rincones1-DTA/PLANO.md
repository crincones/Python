# Plano operacional — WIN, gráfico de 10.000 ticks (DTA)

> **Este arquivo é gerado.** Rode `python rodar.py && python plano.py`.
> Os números saem de `saida/resumo.json`, os mesmos do
> [relatorio.html](relatorio.html). Os números de desempenho das §§ 4, 7 e 10
> **descontam 5 pontos de custo por trade**; os de comparação entre regras são
> brutos, como no relatório. O texto do procedimento é fixo; se você mudar uma
> regra, mude aqui
> **e** em [ESTRATEGIA.md](ESTRATEGIA.md).

Companheiro operacional de [RESULTADOS.md](RESULTADOS.md). O relatório diz
**o que foi medido**; este arquivo diz **o que eu faço na frente da tela**.

---

## 0. O contrato

Eu opero **um** setup principal, com **um** tamanho de risco, seguindo as
regras 1 a 6 deste arquivo. As regras não mudam durante o pregão. Não mudam
depois de uma perda. Não mudam depois de um ganho. Mudam apenas na **revisão
mensal** da § 10, com os dados na mão.

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
| **Contexto na tela** | EMA 21 · Hull 50 · Keltner ±2 ATR(20) em volta da EMA |
| **Setup** | **D — descolamento da Hull**. O T entra pelas mesmas regras de gestão e é raro |
| **Lado** | compra e venda |
| **Posições** | **uma por vez**. Sinal que chega com posição aberta é ignorado |

**O que eu NÃO opero:**

- **Reversão na banda de Keltner.** É o uso de manual do canal e foi medido:
  negativo no WINFUT em toda configuração testada. Preço esticado é onde eu
  **não** opero, não onde eu vendo topo.
- **Rejeição de banda (setup K).** Mede positivo sozinho e mesmo assim piora a
  carteira, porque ocupa a vaga de um trade melhor. Fora até uma revisão
  decidir o contrário.
- **Qualquer coisa que o indicador não marcou.** Se não saiu a seta, não existe
  trade — por mais óbvio que o gráfico pareça.

> **A leitura econômica, em uma frase:** o indicador acende quando alguém
> gastou muito e não levou o preço. Isso é absorção, e absorção se desfaz. A
> Hull diz se havia movimento para desfazer (inclinada) e de que lado o preço
> está em relação a ele. Eu entro do lado de quem **não** falhou.

---

## 2. O gatilho — quando existe trade

O indicador faz a conta; eu confiro o contexto. **Todos os seis** têm de
estar verdadeiros. Um único "não" e não há trade.

| # | Verificação | |
|---|---|---|
| 1 | O indicador marcou a seta, com índice ≥ **0,80** | ☐ |
| 2 | A **Hull 50 está inclinada** — subindo ou descendo, mas nunca deitada | ☐ |
| 3 | O close está do lado **oposto** ao da Hull: eu compro **abaixo** dela, vendo **acima** | ☐ |
| 4 | O preço está **dentro do canal** — não encostou na banda de 2 ATR | ☐ |
| 5 | O mergulho até a EMA 21 é de no máximo **1,5 ATR** — não é queda livre | ☐ |
| 6 | Estou dentro do horário e **sem posição aberta** | ☐ |

O item 1 já embute o que o indicador mede e eu não preciso conferir a olho:
índice de esforço ≥ 0,80, corpo ≤ 50% do range, e o meio do corpo do lado certo.
Os itens 2 e 3 são a regra que o backtest achou e que **contraria a leitura de
manual**: não é "comprar acima de uma Hull que sobe", é comprar **abaixo** dela
quando ela está inclinada. Se isso soar errado na hora, releia a § 3 do
relatório antes de improvisar.

> **O item 2 é o mais importante da lista.** Hull deitada é o pior contexto
> medido: -62,3 pontos por trade no WINV26 e -35,1 no WINFUT. Se só uma linha deste
> plano sobreviver, que seja esta.

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

Cerca de **20% dos sinais serão abortados** — no WINV26, 21 de 103; no WINFUT,
51 de 257. Isso não é falha de execução: é **o plano funcionando**. Um sinal
abortado entra no diário como *aderência cumprida*, exatamente como um trade
vencedor.

> **Aqui a regra não é só disciplina — ela paga.** A limitada mede +32,8 por
> trade contra +19,7 da entrada a mercado, e contra +29,3 da limitada deixada viva
> até o fim do pregão. Entrar no meio do candle do gatilho **é** parte da
> vantagem.

---

## 4. A gestão — decidida antes, executada sem opinião

O stop **não é um número fixo**: ele é 0,75 × ATR da barra do sinal, com piso de 50 e
teto de 400 pontos. Em pregão parado ele encolhe, em pregão violento ele abre —
e é isso que faz o risco por trade ser o mesmo em regimes diferentes. Na
amostra medida ele ficou entre **62 e 164 pontos**, com média de **93**.

| | |
|---|---|
| **Stop inicial** | **0,75 × ATR** da barra do gatilho ≈ 95 pontos |
| **Parcial** | **50% da posição na MESMA distância do stop** |
| **No momento da parcial** | **nada a fazer.** O stop já está na média da operação: com meia posição realizada na distância do stop, o stop inicial **é** o zero a zero |
| **Alvo do restante** | **+300 pontos** |
| **Saída forçada** | fechamento do pregão |

**Tabela de conversão — leia o ATR e use a linha:**

| ATR na hora do sinal | stop e parcial | alvo |
|---|---|---|
| 80 | 60 pts (R$ 12,00) | +300 |
| 100 | 75 pts (R$ 15,00) | +300 |
| 120 | 90 pts (R$ 18,00) | +300 |
| 150 | 110 pts (R$ 22,00) | +300 |
| 200 | 150 pts (R$ 30,00) | +300 |

Resultado por trade, por contrato de lote cheio, com o stop típico de 95:

| desfecho | pontos | R$ | frequência medida |
|---|---|---|---|
| stop antes da parcial | −95 | −19,00 | 42% |
| parcial e depois o stop | 0 | R$ 0,00 | 22% |
| parcial e depois alvo | +198 | +39,50 | 36% |
| fim de pregão | o que estiver | — | 0% |

**O stop não anda — nunca.** Ele entra na distância do ATR e fica lá até o
trade acabar. Com a parcial saindo na **mesma distância**, o stop inicial **já
é** a média da operação, e o trade que volta depois da parcial morre em zero.
Não há nada para arrastar, e arrastar seria estragar.

**A parcial não é opcional.** Ela é o que compra o direito de deixar o resto
correr até +300 sem risco. Sem ela o plano é outro, e os números são outros.

---

## 5. Tamanho e limites do dia

**Risco por trade** = o stop do trade = **R$ 19,00 por contrato** no stop típico
de 95 pontos.

Regra de dimensionamento:

```
contratos = (1% do capital) / (stop do trade em pontos x R$ 0,20)

com o stop lido da tabela da § 4, ANTES de enviar a ordem
```

Como o stop varia, o **número de contratos varia junto** — é assim que o risco
em reais fica constante. Em pregão de ATR alto eu opero menos contratos, não
o mesmo lote com stop maior.

**Limites rígidos do pregão** — atingiu, o dia acabou, sem discussão:

| limite | valor | por quê |
|---|---|---|
| **3 stops no dia** | ≈ −285 pts (R$ 57,00 / contrato) | o pior pregão medido foi -629 pts |
| **1 violação de regra** | — | erro de processo fecha o dia, mesmo no lucro |

O segundo limite é o mais importante e o mais fácil de ignorar. Um erro de
processo num dia de lucro é **mais perigoso** que um num dia de prejuízo,
porque o resultado o recompensa.

---

## 6. A rotina do pregão

**Antes de abrir (5 minutos)**

- Gráfico em 10.000 ticks; EMA 21, Hull 50 e o canal de Keltner na tela;
  o histograma de esforço na subjanela
- **Ler o ATR(20) e anotar o stop do dia** pela tabela da § 4
- Definir o número de contratos **antes** do primeiro sinal
- Reler as regras 1 a 4 deste arquivo. Sim, todo dia.

**Durante**

- Só existe ação quando a seta imprime. O resto do tempo eu **espero**.
- Em ~4,8 trades por pregão, a maior parte do dia é espera. Isso é o trabalho,
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

Carteira D + T, gestão padrão, **descontando 5 pontos de custo por trade** —
a leitura honesta, não a bruta:

| | WINV26 | WINFUT |
|---|---|---|
| acerto por trade | 45% | 36% |
| valor esperado por trade | +53,4 pts | +27,8 pts |
| **desvio** por trade | 134 pts | 130 pts |
| pregões positivos | 85% | 60% |
| pior pregão | -462 pts | -629 pts |
| maior sequência de pregões negativos | 2 | 5 |
| chance de uma **semana** fechar negativa | 4% | 21% |
| rebaixamento máximo | 739 pts (R$ 147,80) | 953 pts (R$ 190,60) |

Olhe a linha do **desvio**: 130 pontos por trade, contra um valor esperado de
+27,8. O ruído é várias vezes maior que o sinal em cada operação isolada. Isso
não é um defeito da estratégia — é como toda vantagem pequena se parece de
perto.

As consequências, que eu preciso ter aceitado **antes** de elas acontecerem:

- **40% dos pregões fecham no vermelho.** Um dia negativo é o caso comum, não
  um sinal de nada.
- **5 pregões negativos seguidos já aconteceram** na amostra medida. Vão
  acontecer de novo.
- **21% de chance de uma semana inteira fechar negativa**, com a vantagem
  totalmente intacta.
- Duas perdas seguidas: 41% de chance. Três: 26%. Não é raro.

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
| 4 | O stop entrou na distância do ATR, imediatamente |
| 5 | A parcial saiu na mesma distância (e o stop ficou onde estava) |
| 6 | Não mexi em nada depois disso |

**Por pregão** — quatro itens, cada um vale 1:

| # | item |
|---|---|
| 7 | Não operei nenhum sinal fora dos setups D e T |
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

**1. Operar a Hull como manual manda.** Comprar acima de uma Hull que sobe é a
leitura natural, e é a que mede **pior** com este gatilho. Quando a mão coçar
para entrar "a favor", é exatamente o momento em que o backtest diz não.

**2. Perseguir o sinal abortado.** "Ele foi embora sem mim." Vai acontecer com
20% dos sinais, todo mês. A regra da barra seguinte existe para tirar essa
decisão da minha mão no momento em que eu estou menos apto a tomá-la.

**3. Afastar o stop.** É o erro que muda a distribuição inteira: troca uma
perda planejada por uma perda de tamanho desconhecido. Todos os números deste
arquivo deixam de valer no instante em que isso acontece uma vez.

**4. Vender topo na banda.** O canal de Keltner está na tela como **régua de
esticamento**, não como gatilho. Reversão na banda foi medida e perde. Se eu me
pegar operando a banda, eu estou operando outro plano — sem backtest.

**5. Mexer no lote pelo resultado.** Dobrar depois de perder é tentar
recuperar num trade o que a distribuição devolve em vinte. Aumentar depois de
ganhar é a mesma aposta, com o disfarce de confiança. O lote sai da conta da
§ 5, com o ATR do dia, e não muda dentro do pregão.

---

## 9. O diário

Uma linha por **sinal** — inclusive os abortados.

| campo | o que anotar |
|---|---|
| data / hora | do fechamento da barra do gatilho |
| lado | compra ou venda |
| ATR e stop usado | o que a tabela da § 4 mandou |
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
2. Quantos sinais foram abortados, e se isso ficou perto de 20%
3. O resultado, em pontos, contra o valor esperado de +27,8 por trade
4. O **custo real** cobrado pela corretora, comparado com os 5 pontos por
   trade que os números desta página já descontam
5. Se o ritmo está cansativo, **subir o nível do gatilho de 0,80 para 0,85** —
   é a alavanca medida para ter menos sinais e mais qualidade, e está na
   § 05 do relatório

**Disjuntores** — automáticos, não opinativos:

| gatilho | ação |
|---|---|
| rebaixamento de **953 pts** (R$ 190,60) | reduzir o lote à metade |
| rebaixamento de **1906 pts** (R$ 381,20) | parar de operar e reabrir o backtest |
| aderência < 90%% na semana | parar de operar; treinar em simulador |
| 5 pregões negativos seguidos | parar por um dia e reler este arquivo |

O primeiro disjuntor está no **pior rebaixamento já medido**. Chegar nele é
normal. O segundo é o dobro dele: chegar lá já é evidência de que alguma
coisa mudou — no mercado ou em mim — e merece medição, não persistência.

O último é sobre estado mental, não sobre estatística: 5 pregões negativos
seguidos já aconteceram na amostra, então 5 não prova nada. Mas depois de 5 eu
não sou a mesma pessoa na frente da tela, e é essa pessoa que o disjuntor
protege.

---

## 11. O que este plano herda de incerto

Ler antes de dimensionar posição. Está tudo em
[RESULTADOS.md § 14](RESULTADOS.md).

- **Amostra pequena.** 13 e 43 pregões com trade, dois meses de mercado.
- **As duas bases não são independentes** — o WINFUT contém o WINV26 inteiro.
  Concordarem é menos confirmação do que parece.
- **As regras saíram destas mesmas bases.** O lado da Hull, o veto da Hull
  plana, o nível do gatilho e o tamanho do stop foram escolhidos olhando estes
  dois arquivos. Há sobreajuste embutido, e o desempenho real tende a ser pior
  que o medido.
- **A ordem limitada é dada por preenchida assim que o preço toca o nível.** Na
  prática existe fila, e nem todo toque preenche — este é o otimismo que mais
  pesa contra os números acima.
- **Sem filtro de horário, rolagem ou vencimento.**

Nada disso é motivo para não operar o plano. É motivo para operá-lo **pequeno**
até que os seus próprios registros, e não os meus, digam que ele funciona.

