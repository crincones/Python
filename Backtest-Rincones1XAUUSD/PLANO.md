# Plano operacional — XAUUSD, gráfico de 521 ticks

> **Este arquivo é gerado.** Rode `python rodar.py && python plano.py`.
> Os números saem de `saida/resumo.json`, os mesmos do
> [relatorio.html](relatorio.html). O texto do procedimento é fixo; se
> você mudar uma regra, mude aqui **e** em [ESTRATEGIA.md](ESTRATEGIA.md).

Companheiro operacional de [RESULTADOS.md](RESULTADOS.md). O relatório diz
**o que foi medido**; este arquivo diz **o que eu faço na frente da tela**.

Todos os valores em **USD por onça**. Um movimento de 1,00 vale 100 USD num
lote padrão de 100 oz; num lote de 0,01 vale 1 USD. Os números abaixo já
descontam **0,20 USD de custo por trade**.

---

## 0. O contrato

Eu opero **um** gatilho, com **um** tamanho de risco, seguindo as regras 1 a
6 deste arquivo. As regras não mudam durante o pregão. Não mudam depois de
uma perda. Não mudam depois de um ganho. Mudam apenas na **revisão mensal**
da § 9, com os dados na mão.

A única coisa que eu avalio ao fim do dia é **se segui o plano** — não quanto
ganhei. A § 7 explica por quê, com os números que tornam isso não uma frase
bonita, mas a leitura correta dos dados.

Assinado: ____________________   Data: __ / __ / ____

---

## 1. O que eu opero — e o que eu não opero

| | |
|---|---|
| **Ativo** | XAUUSD (ouro à vista) |
| **Gráfico** | candle de **521 ticks** |
| **Gatilho** | índice de esforço `[E4] ≥ 0,90`, lido **contra o candle** |
| **Filtro de forma** | corpo ≤ 50% do range, meio do corpo **do lado oposto ao pavio** |
| **Lado** | compra e venda |
| **Posições** | **uma por vez**. Sinal que chega com posição aberta é ignorado |

**O que eu NÃO faço:**

- **Não filtro por regime de média.** Medido, o filtro subtrai neste ativo:
  a carteira que pega todo gatilho mede mais que qualquer subconjunto A/B/C,
  e nas duas metades da amostra. Se o gatilho saiu, eu opero.
- **Não uso a geometria clássica.** No WIN a barra de exaustão tem o pavio em
  cima numa alta. **No ouro é o contrário**, e operar a forma clássica aqui
  mede negativo. Se eu me pegar procurando o shooting star, parei de operar
  este plano.
- **Não uso ordem limitada.** Ver § 3 — é o erro mais caro possível aqui, e é
  exatamente o hábito que vem do plano do WIN.
- **Qualquer coisa que o indicador não marcou.** Se não saiu a seta, não
  existe trade — por mais óbvio que o gráfico pareça.

> São **6,7 trades por pregão**, mais que o dobro do plano do WIN. O gráfico
> de 521 ticks do ouro faz cerca de 800 barras por pregão e roda quase 24
> horas: **escolha uma janela de horário fixa** e opere só dentro dela. O
> backtest não a impõe, e por isso ela é uma decisão sua — mas operar 24h à
> mão não é o mesmo procedimento que foi medido.

---

## 2. O gatilho — quando existe trade

O indicador faz a conta; eu confiro o contexto. **Todos os cinco** têm de
estar verdadeiros. Um único "não" e não há trade.

| # | Verificação | |
|---|---|---|
| 1 | O indicador marcou a seta | ☐ |
| 2 | A barra do gatilho é visivelmente **larga** para o trecho recente | ☐ |
| 3 | O **corpo é pequeno** e está do lado do fechamento, com o pavio grande do lado oposto | ☐ |
| 4 | A seta aponta **contra** a direção do candle | ☐ |
| 5 | Estou dentro do horário e **sem posição aberta** | ☐ |

Os itens 1 a 4 já embutem o que o indicador mede: percentil de range ≥ 0,90
nas últimas 20 barras válidas, corpo ≤ 50% do range, e meio do corpo além
de 60% do range no lado do fechamento.

**A leitura econômica, em uma frase:** a barra andou muito para o tamanho
recente, fechou colada no extremo, e o caminho todo foi feito de um lado só —
e é justamente essa barra que o ouro devolve. Eu entro contra ela.

> **Por que a forma é invertida aqui, e não no WIN.** Não há explicação
> confirmada, e o plano não finge que há. O que existe é a medição, repetida
> três vezes em gráficos sintéticos diferentes do mesmo ativo
> (`Delta_Fraqueza.mqh`, `Ticks_Esforco_v2.mqh` e este backtest). Eu opero o
> que mede.

---

## 3. A entrada — a mercado, e só

```
barra t      o gatilho fecha. Eu entro A MERCADO, imediatamente.
             Sem ordem limitada. Sem esperar repique.
barra t+1    se eu não entrei na barra t, o sinal morreu.
```

**Esta é a regra que eu mais vou querer quebrar**, porque o plano do WIN faz
o contrário: lá a entrada é uma limitada no meio do candle, válida por uma
barra. Aqui essa mesma ordem custa **+1,85 por trade** e vira o resultado de
positivo para negativo.

O motivo é geométrico, não estatístico. A barra do gatilho fecha colada num
extremo (é o filtro da § 2). O meio dela fica, portanto, do lado **errado** do
fechamento: numa barra de alta, o meio está **abaixo** do fechamento, e uma
venda limitada ali é meio range de desconto entregue de graça. E a ordem
preenche quase sempre — o preço já está do lado dela. Não é uma ordem que
espera um preço melhor: é uma ordem que garante um preço pior.

> No plano do WIN a mesma regra é boa, pela mesma geometria de cabeça para
> baixo: lá o corpo está embaixo numa barra de alta, o meio fica **acima** do
> fechamento, e a limitada de fato espera um repique. **A regra não é boa nem
> ruim — ela depende de onde o candle fecha.**

---

## 4. A gestão — o que já está decidido antes de entrar

| | valor | por lote de 100 oz |
|---|---:|---:|
| **Stop inicial** | 7,00 | USD 700,00 |
| **Parcial** (50% da posição) | +7,00 | — |
| **Alvo** (restante) | +10,50 | — |
| **Limite do dia** | 3 stops = 21,00 | USD 2100,00 |

A parcial sai na **mesma distância do stop**. Isso não é gosto: com meia
posição realizada a essa distância, a **média da operação** cai exatamente em
cima do stop inicial. O stop **não anda** — a operação é que passou a valer
zero ali. Se o preço voltar e pegar o stop depois da parcial, o trade fecha
em **zero de verdade**, não em "zero a zero" que paga alguma coisa.

**O stop nunca se afasta e nunca se move para fora.** Se eu estiver com
vontade de dar mais espaço, a operação já acabou.

> **Por que 7,00 e não 3,50.** Os dois foram medidos com todo o resto igual.
> O escolhido é o que soma a maior média diária nas duas metades da
> amostra. O motivo estrutural: a barra do gatilho é, por construção, uma
> barra de range extremo — um stop pequeno demais **cabe dentro dela** e
> é acionado pelo próprio ruído da barra que gerou o sinal.

---

## 5. Os limites do dia

| Disjuntor | Ação |
|---|---|
| **3 stops no dia** | Fecho a plataforma. Não há "recuperar". |
| **1 violação de regra** | Fecho a plataforma, mesmo no lucro. |
| **Pior pregão medido: -37,70** | Se o dia passar disso, algo está errado com a execução, não com o mercado. |

O pior pregão da amostra foi **-37,70** (USD -3770,00 por lote) e o maior rebaixamento
acumulado foi **78,20** (USD 7820,00). Dimensione a posição por esse número, não pela
média.

---

## 6. O registro — cinco linhas por trade

```
data / hora     __________     lado  compra / venda
entrada         __________     stop  __________   alvo __________
desfecho        alvo / stop / zero a zero / fim do pregão
resultado       __________ USD
aderência       segui as 5 verificações?   sim / não
```

**Um trade vencedor tomado fora das regras conta como falha.** Ele vale zero
na nota de aderência e entra em vermelho no diário. Sem esta regra a nota vira
enfeite, e o resultado volta a mandar justamente nos dias em que o plano mais
importa.

---

## 7. O que esperar — a forma do desempenho

| | amostra inteira | 1ª metade | 2ª metade |
|---|---:|---:|---:|
| trades por pregão | 6,7 | 6,7 | 6,7 |
| acerto | 47,8% | 47,0% | 48,6% |
| resultado médio por trade | +1,00 | +0,79 | +1,20 |
| resultado médio por pregão | +6,73 | +5,30 | +8,12 |
| pregões positivos | 64% | 57% | 70% |
| pior pregão | -37,70 | -34,90 | -37,70 |
| maior sequência sem ganhar | 9 trades | 6 trades | 9 trades |
| maior sequência de pregões negativos | 3 pregões | 3 pregões | 3 pregões |
| chance de uma semana negativa | 22% | 28% | 16% |
| chance de um mês negativo | 6% | 11% | 3% |

**Leia a linha do acerto antes de operar.** São 47,8%: a maioria das operações
**perde**, e o resultado vem do tamanho dos ganhos, não da frequência deles.
Já houve **9 trades seguidos sem ganhar** e **3 pregões negativos seguidos**
dentro de uma amostra em que a vantagem estava intacta o tempo todo. Uma
semana fecha no vermelho em 22% das vezes e um mês em 6%.

Se eu abandonar o plano depois de 9 perdas seguidas, eu vou abandoná-lo num
intervalo que o próprio backtest previa que aconteceria.

Desfechos: **45,7%** batem o alvo, **40,5%** morrem no stop, **9,3%** saem em zero a
zero e **4,6%** fecham no fim do pregão.

---

## 8. O que este plano NÃO tem

- **Confirmação fora da amostra.** As duas metades são o mesmo histórico de
  85 pregões partido ao meio, não dois instrumentos. No plano do WIN havia
  dois contratos, e a concordância entre eles valia como evidência; aqui não
  vale — vale só como evidência de que o resultado não vem de um pedaço do
  período.
- **Um corte validado.** O nível 0,90 e o corte de posição 60 saíram de uma
  varredura sobre esta mesma amostra. A região é larga (§ 10 do relatório),
  mas larga não é validada.
- **Margem folgada para custo.** Com 0,20 USD por trade a vantagem sobrevive;
  com o dobro ela encolhe muito. **Meça o seu spread real** antes de
  dimensionar, e não opere isto em horário de spread alargado.
- **Uma janela de horário.** O ouro roda quase 24 horas e o backtest opera o
  pregão inteiro. Escolher a janela é decisão sua, e ela muda os números.

---

## 9. A revisão mensal

Uma vez por mês, com o diário na mão, e **nunca** durante o pregão:

1. Rodar `python rodar.py && python relatorio.py && python plano.py` com o
   histórico atualizado.
2. Comparar a **nota de aderência** do mês com a do anterior. Ela vem antes
   do resultado.
3. Comparar o acerto e o EV medidos com os da § 7. Divergência grande com
   aderência alta é sinal de que o mercado mudou; divergência grande com
   aderência baixa é sinal de que **eu** mudei.
4. Só então decidir se alguma regra muda — e escrever a mudança aqui e em
   `ESTRATEGIA.md` antes do próximo pregão.

> Sem custo nenhum a estratégia mede +1,20 por trade; com 0,20 de custo, +1,00. A
> diferença entre esses dois números é o que a execução decide, e é a única
> parte do resultado que está sob meu controle.

