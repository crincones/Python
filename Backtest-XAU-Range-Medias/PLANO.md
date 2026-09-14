# Plano de operação manual — médias + Esforço × Resultado em range de 388 ticks

> Este plano opera a variante **V2**: EMA de 21/42/72 em leque aberto define a tendência, o indicador dá o momento, e a gestão é **1:2 fixa**. Leia o §7 antes de mandar a primeira ordem — o estudo que gerou este plano tem uma reprovação importante nele.

| o que o backtest mediu (V2) |  |
|---|---|
| Operações | 548 em 83 pregões (6,6 por pregão) |
| Acerto | 37,8% |
| Payoff | 2,00 |
| Fator de lucro | 1,21 |
| Expectativa **dentro** da amostra | +0,133 R = +25,8 ticks |
| Expectativa **fora** da amostra | **+0,035 R** — é este o número em que acreditar |
| Significância | t = +2,14 |
| Pior rebaixamento | -20,0 R, 24 operações para recuperar |
| Maior sequência de perdas | 14 operações |
| Maior sequência de ganhos | 6 operações |
| Duração típica | 1,6 barras |

## 1 · O gráfico e as médias

- Símbolo sintético de range gerado pelo `Range_Claude_v1.mq5`, com **388 ticks** de range.
- Indicador `Trigger_EsforcoResultado_Range.mq5` aplicado ao gráfico, com os parâmetros de fábrica — não mexa neles.
- **Três médias exponenciais** do fechamento: **21, 42 e 72**.

> **Use EMA. Não use Hull.** É a conclusão mais sólida do estudo inteiro. Comparando par a par — mesma largura de leque, mesma gestão, mesmo stop — a EMA vence a Hull em **69 dos 80 pares** testados, com diferença mediana de +0,037 R. A Hull persegue o preço de perto e vira antes; o preço disso é trocar de lado 1.367 vezes contra 422 da EMA no mesmo histórico. Cada troca é uma tendência que ela declarou e desfez. Sensibilidade a virada não é a mesma coisa que leitura de tendência.

## 2 · O contexto: quando existe tendência

Duas condições, as duas medidas na barra de sinal. Se qualquer uma falhar, **não há operação** — não importa o quão bonito esteja o sinal do indicador.

1. **As três médias ordenadas** na direção que se vai operar: `EMA21 > EMA42 > EMA72` para comprar, o inverso para vender.
2. **O leque aberto:** a distância entre a EMA21 e a EMA72 tem de ser de pelo menos **400 ticks = 4,00 dólares**. É a tradução numérica de "médias não emboladas".

Na prática, medir os 400 ticks a olho é difícil e desnecessário: coloque a ferramenta de linha vertical entre as duas médias, ou apenas exija que dê para enxergar **4 dólares de separação** entre a mais rápida e a mais lenta. O estudo mostra platô, não pico — errar por 50 ticks não muda nada.

A progressão medida justifica as duas exigências, nesta ordem:

| contexto exigido | operações | expectativa |
|---|---|---|
| nenhum — só o sinal do indicador | 1.686 | +0,062 R |
| médias ordenadas | 730 | +0,097 R |
| **médias ordenadas + leque aberto** | 548 | **+0,133 R** |
| médias ordenadas CONTRA o sinal | 761 | +0,029 R |

A última linha é o controle que importa: operar *contra* o leque rende +0,029 R. O contexto não é decoração.

## 3 · A entrada

1. **Espere a barra de sinal FECHAR.** A seta aparece na barra em formação e pode sumir quando ela fecha — `resRel`, `qualRel` e o corpo mudam até o último tick. Sinal em barra aberta não é sinal.
2. **Confira o contexto** (§2): médias ordenadas *e* leque aberto, na direção da barra de sinal.
3. **Entre a mercado, no fechamento da barra**, a favor da direção da barra de sinal. Vale igual para a seta de absorção e para a de divergência.
4. **Uma posição por vez.** Sinal que aparecer com posição aberta é ignorado, não acumulado.

São cerca de **6,6 operações por pregão** — o filtro do leque descarta boa parte dos sinais, e é para isso que ele existe.

## 4 · A saída: qual das três gestões usar

As três formas pedidas foram testadas. Duas delas **não são mensuráveis neste gráfico** — e é importante entender por quê antes de escolher.

| gestão | desfechos | expectativa medida | confiável? |
|---|---|---|---|
| **fixo** — stop 194 t, alvo 388 t, nada se move | −1R ou +2R | +0,133 R | **sim** |
| **parcial + breakeven da operação** — 50% em +1R, stop não se move | −1R, 0, +1,5R | +0,123 R | **sim** |
| parcial + stop na entrada — 50% em +1R, stop vai para a entrada | −1R, +0,5R, +1,5R | +0,176 R | não — intervalo de 0,354 R |
| breakeven puro — stop vai para a entrada em +1R, sem parcial | −1R, 0, +2R | +0,240 R | não — intervalo de 0,697 R |

> ⚠️ **Por que as duas últimas não são mensuráveis.** A entrada é o fechamento da barra de sinal, então a barra seguinte **abre exatamente no preço de entrada**. Quando ela sobe 1R, qualquer pavio inferior faz o preço "voltar ao breakeven" no papel — e como a barra de range percorre 388 ticks garantidos, isso acontece em praticamente toda barra que arma o gatilho. O arquivo não diz se a mínima veio antes ou depois do toque em 1R, e as duas leituras dão resultados que diferem em até 0,70 R. Não é que a gestão seja ruim: é que este histórico não permite julgá-la.

> **"Breakeven na média da operação" é uma conta, não uma opinião.** Com metade da posição realizada em +1R, o resultado da operação inteira num stop em −1R é `0,5 × (+S) + 0,5 × (−S) = 0`. Ou seja: **o breakeven da operação já está no stop inicial** — não é preciso mexer em nada. Levar o stop para a entrada não é breakeven, é travar +0,5R. São coisas diferentes, e só a primeira é mensurável aqui.

**A recomendação:** use a gestão **fixa**. Ela mede +0,133 R contra +0,123 R da parcial com breakeven da operação, é a mais simples de executar, e não depende de nenhuma suposição. Se preferir a sensação de realizar metade no meio do caminho, use a `parcial_op` — mas **não mexa no stop** ao fazer a parcial.

### O tamanho do stop

Stop de **194 ticks**, alvo de **388 ticks**. Duas razões, e a primeira é geométrica.

Num gráfico de range a barra percorre no máximo 388 ticks, então ela não consegue tocar dois níveis separados por mais que isso. Como stop e alvo distam `S + 2S = 3S`, o resultado deixa de depender de qualquer convenção exatamente a partir de:

```
S > range / 3 = 129,3 ticks
```

Medido no arquivo, a largura do intervalo cai de 0,245 em S=120 para **exatamente zero** em S=130 — a previsão e a régua batem. A segunda razão é que de 130 a 220 ticks existe um platô: a expectativa desce suavemente e nenhum valor é um pico. 194 ticks fica no meio dele, com folga confortável acima do limite.

**Não use stop abaixo de 129 ticks.** Abaixo do limite o número que você viu no backtest não significa nada.

## 5 · Tamanho e risco

O risco por operação é **194 ticks = 1,94 dólares por lote**.

- Arbitre o lote para que **1R fique em 0,25% a 0,5% do capital**. O pior rebaixamento medido foi de 20,0 R; com 0,5% por operação isso seria uma queda de 10,0% no capital — e ele pode ser pior fora da amostra.
- **Prepare-se para 14 perdas seguidas.** Foi a maior sequência medida, e com 38% de acerto ela é esperada, não anormal. A média de perdas seguidas é 2,8.
- **Limite diário de perda: 3R.** Atingiu, fecha a plataforma.
- **Limite de 13 operações por dia**, o dobro da média medida.

> **O acerto é baixo por construção, e está tudo bem.** Com alvo de 2R e stop de 1R, o ponto de equilíbrio é 33,3% de acerto. A V2 acerta 37,8%. Isso significa que **duas em cada três operações são perdas** — quem não aguenta essa sequência não deve operar 1:2. A alternativa é a gestão com parcial, que sobe o acerto para 51,6% ao custo de expectativa menor.

## 6 · O que não fazer

| tentação | o que o backtest diz |
|---|---|
| Trocar a EMA pela Hull | A EMA vence em 69 dos 80 pares testados. A Hull vira antes e erra mais. |
| Operar sem exigir o leque aberto | Cai de +0,133 R para +0,097 R. |
| Operar sem contexto de médias nenhum | Cai para +0,062 R. |
| Apertar o stop para menos de 129 ticks | Abaixo do limite geométrico o resultado passa a depender de uma convenção — o número deixa de ser mensurável. |
| Adotar o breakeven puro porque mediu melhor | O intervalo dele vai de -0,444 R a +0,253 R. Ele *pode* ser melhor; o histórico não permite afirmar. |
| Usar a configuração campeã do grid | Ela mede +0,320 R dentro da amostra e entrega +0,035 R fora. Foi o máximo de 96 tentativas. |
| Aumentar o lote depois de uma sequência boa | Com t = +2,14, sequências boas e ruins de 6 operações são esperadas sem que nada tenha mudado. |
| Mexer nos parâmetros do indicador | Foram varridos no estudo anterior deste gráfico e são todos platôs. Mexer depois de ver os resultados é ajustar à amostra. |

## 7 · Expectativa realista — leia antes de operar

> ⚠️ **O estudo tem duas reprovações sérias, e elas mudam o que esperar.** Primeira: **o resultado vive no último terço do histórico**. Os dois primeiros terços rendem +0,075 R e +0,053 R, indistinguíveis de zero; o terceiro rende +0,250 R e carrega tudo. Segunda: **escolher a melhor configuração numa metade e testá-la na outra derruba o resultado de +0,320 R para +0,035 R**. O grid descreve o passado; ele não mostrou capacidade de prever.

E o custo decide o resto. +0,133 R sobre um stop de 194 ticks são +25,8 ticks por operação:

| custo ida+volta | expectativa por operação | por pregão |
|---|---|---|
| 0 ticks | +0,133 R = +25,8 ticks | +1,71 USD por lote |
| 10 ticks | +0,082 R = +15,8 ticks | +1,05 USD por lote |
| 20 ticks | +0,030 R = +5,8 ticks | +0,39 USD por lote |
| 40 ticks | -0,073 R = -14,2 ticks | -0,93 USD por lote |

Com 20 ticks de custo sobra +0,030 R; com 40, -0,073 R. E esse é o número *dentro* da amostra. Fora dela, com custo, não sobra nada.

> **O que fazer com isso.** O que sobreviveu ao estudo não foi um sistema: foram **duas escolhas de projeto**. Usar EMA em vez de Hull, e exigir o leque aberto. As duas melhoram o gatilho de forma consistente e por razões estruturais. O que não sobreviveu foi a calibragem fina — o stop exato, a largura exata do leque, a gestão exata.

**Comece com lote mínimo e trate os três primeiros meses como coleta de dados.** O objetivo dessa fase é medir duas coisas que o backtest não sabe: o seu slippage real e se o regime de mercado do último terço continua valendo.

## 8 · Como saber se parou de funcionar

Defina os critérios **agora**. Depois de uma sequência ruim ninguém escreve regra de parada honesta.

- **Registre toda operação** com: data e hora, tipo de sinal, lado, largura do leque na entrada, distância do preço à EMA21, preço de entrada e de saída, resultado em R e o slippage contra o fechamento da barra.
- **Depois de 50 operações**, compare o acerto com 37,8%. Abaixo de 33% a estratégia não paga o alvo de 2R.
- **Depois de 100 operações**, some o slippage médio. Se passar de 15 ticks por operação, não há margem: +25,8 ticks de expectativa bruta não pagam isso.
- **Pare em −20 R acumulados** — é o pior rebaixamento medido. A essa altura a hipótese de que a vantagem sumiu é mais simples que a de azar.
- **Refaça o backtest a cada trimestre** com o histórico novo: `python rodar.py`. Acompanhe menos o acerto e mais a **estabilidade entre os terços** — foi ali que este estudo falhou.

---

Gerado por `plano.py` a partir de `saida/resumo.json` (2026-09-06 10:13). Os números vêm todos do backtest; nenhum foi digitado à mão. Para refazer: `python rodar.py && python plano.py`.
