# Plano de operação manual — Esforço × Resultado em range de 388 ticks

> Este plano opera a variante **V8** do backtest: sinal do indicador, filtro de esforço baixo, alvo e stop a meio range. É a única configuração do estudo que passou em todos os controles — e ainda assim a margem dela cabe dentro de um spread ruim. Leia o §8 antes de mandar a primeira ordem.

| o que o backtest mediu |  |
|---|---|
| Operações | 562 em 84 pregões (6,7 por pregão) |
| Acerto | 58,0% |
| Expectativa bruta | +31,1 ticks = +0,160 R = +0,31 USD por lote |
| Significância | t = +3,84 (erro padrão de 8,1 ticks) |
| Fator de lucro | 1,38 |
| Pior rebaixamento | -1.746 ticks = -9,00 R |
| Duração típica | 1,0 barra(s) |

## 1 · O gráfico, antes de qualquer coisa

O indicador só significa alguma coisa num gráfico onde `High-Low` é constante **e** onde `tick_volume` e `real_volume` carregam agressão compradora e vendedora. Aplicado em qualquer outro lugar ele não dá erro: desenha setas sem significado, que é o pior modo de falhar.

- Símbolo sintético de range gerado pelo `Range_Claude_v1.mq5`, com **388 ticks** de range.
- Indicador `Trigger_EsforcoResultado_Range.mq5` aplicado ao gráfico.
- Confira o log ao anexar: se ele avisar que o range foge da mediana ou que `real_volume` está zerado, **pare**. A premissa não vale e o resto deste plano não se aplica.

> **Não mexa nos parâmetros do indicador.** Os seis foram varridos no backtest e todos são platôs — nenhum valor testado muda a conclusão, e o padrão nunca foi o melhor da varredura. Isso é o que mostra que o indicador não foi ajustado a este histórico. Mexer neles agora, depois de ver as tabelas, é a definição de ajuste à amostra.

| parâmetro | valor | não mexer porque |
|---|---|---|
| `PeriodoBase` | 60 | de 40 a 100 o resultado é o mesmo |
| `FatorRes` | 0,70 | de 0,50 a 0,70 o resultado é o mesmo ou melhor |
| `FatorQual` | 0,50 | de 0,20 a 0,50 o resultado é o mesmo |
| `FatorCorpo` | 0,80 | só afeta a divergência |
| `LimDesq` | 0,05 | só afeta a divergência |
| `FatorCompleta` | 0,90 | praticamente inerte neste símbolo |

## 2 · O filtro que decide tudo, e que o indicador ainda não mostra

O gatilho sozinho não paga. Todo sinal do indicador, operado a meio range, mede **53,2%** de acerto — positivo, mas magro. Com o filtro de esforço, sobe para **58,0%**. É esse filtro que separa o plano de uma aposta.

**A regra:** o *esforço relativo* da barra de sinal tem de ser **≤ 0,80**. Esforço relativo é a agressão total da barra (compradora + vendedora) dividida pela média das barras da **mesma direção** nas últimas 60. Abaixo de 0,80 significa: a barra virou o movimento com pouca gente negociando.

A tese é a própria absorção, na forma mais pura: não houve briga. O preço andou porque não havia nada do outro lado — e não porque um lado venceu o outro. Só **32,3%** dos sinais passam nesse corte, então espere descartar dois de cada três.

> ⚠️ **O indicador não publica esse número.** Os buffers de estudo do `.mq5` são `Sinal`, `Eficiência`, `ResRel` e `QualRel`. O esforço relativo não está entre eles — mas é **derivável dos dois que estão**.

Como `Eficiência = ResRel / EsfRel` por definição, vale a volta:

```
EsfRel = ResRel / Eficiência
```

Conferido nos 1.782 sinais do histórico: a identidade vale em **100%** deles. Na Janela de Dados, portanto, basta dividir `ResRel` por `Eficiência` e comparar com 0,80.

Fazer essa conta de cabeça no instante do sinal é pedir erro. A correção definitiva é publicar o valor como um nono buffer. Dentro do `.mq5`, a variável `esfRel` **já existe e já está calculada** no laço de `OnCalculate` — só não é gravada em lugar nenhum:

```cpp
// no cabecalho, ao lado dos outros DRAW_NONE:
#property indicator_buffers 9
#property indicator_plots   9
#property indicator_label9  "EsfRel"
#property indicator_type9   DRAW_NONE

double BufEsfRel[];                       // junto dos demais buffers

// em OnInit(), depois de SetIndexBuffer(7, ...):
SetIndexBuffer(8, BufEsfRel, INDICATOR_DATA);
PlotIndexSetDouble(8, PLOT_EMPTY_VALUE, 0.0);
PlotIndexSetInteger(8, PLOT_DRAW_BEGIN, g_primeira);

// em OnCalculate(), na limpeza do inicio do laco:
BufEsfRel[idx] = 0.0;

// e ao lado de BufEfic[idx] = efic;
BufEsfRel[idx] = esfRel;
```

Com o buffer no lugar, o filtro vira leitura direta na Janela de Dados — e um EA que consuma o indicador por `iCustom` passa a ter a condição inteira sem recalcular nada.

## 3 · A entrada

1. **Espere a barra de sinal FECHAR.** A seta do indicador aparece na barra em formação e pode sumir quando ela fecha, porque `resRel`, `qualRel` e o próprio corpo mudam até o último tick. Sinal em barra aberta não é sinal.
2. **Confira o esforço relativo** (§2). Se `ResRel / Eficiência` for maior que 0,80, **não opere**. Este é o passo que a maioria vai querer pular, e é o único que o backtest mostrou que importa.
3. **Entre a mercado, no fechamento da barra**, a favor da direção da barra de sinal — para cima se ela fechou de alta, para baixo se fechou de baixa. Vale igual para a seta verde/vermelha (absorção) e para a azul (divergência): as duas mediram parecido dentro do filtro (56,1% e 63,6%).
4. **Uma posição por vez.** Sinal que aparecer com posição aberta é ignorado, não acumulado.

> **Por que a mercado, e não uma ordem limitada melhor?** Foi testado. A ordem limitada no meio do range da barra de sinal abandona 53,6% dos sinais e o preço melhor não compensa a amostra perdida — a variante V3 é a pior do estudo inteiro. Num gráfico onde a vantagem dura uma barra, esperar por preço é esperar a vantagem passar.

## 4 · A saída

Alvo e stop na mesma distância: **194 ticks = 1,94 dólares = meio range**, os dois montados junto com a entrada e não tocados depois.

|  | valor | por quê |
|---|---|---|
| Stop | 194 ticks abaixo (compra) ou acima (venda) da entrada | é 1R |
| Alvo | 194 ticks, a posição inteira | é onde a vantagem está |
| Parcial | nenhuma | com alvo de uma barra não há o que parcelar |
| Stop móvel | nenhum | a operação dura 1,0 barra(s) |
| Tempo máximo | nenhum necessário | a barra seguinte resolve quase sempre |

> **Meio range não é um número escolhido por gosto.** É o único alvo deste gráfico em que a ambiguidade dentro da barra não existe. Como a barra tem 388 ticks por construção, ela não consegue percorrer 194 para cima *e* 194 para baixo: um dos dois lados é sempre decidido primeiro, e o backtest não precisou supor nada. Em qualquer outro alvo o número medido depende de uma convenção.

**Não estique o alvo.** Está medido: em meio range a expectativa é de +0,160 R por operação; em um range inteiro cai para +0,095 R; em dois ranges vira -0,048 R. A vantagem que o indicador enxerga vive uma barra e se dissolve.

## 5 · Tamanho e risco

O risco por operação é **194 ticks = 1,94 dólares por lote**. Com 6,7 operações por pregão, o risco diário bruto é de cerca de 6,7 R.

- Arbitre o lote para que **1R fique em 0,25% a 0,5% do capital**. O pior rebaixamento medido foi de 9,0 R — com 0,5% por operação isso seria uma queda de 4,5% no capital, e ele pode ser pior fora da amostra.
- **Limite diário de perda: 3R.** Atingiu, fecha a plataforma.
- **Limite de 13 operações por dia**, que é o dobro da média medida. Passar disso significa que você está vendo sinal onde não tem.

## 6 · O que não fazer

| tentação | o que o backtest diz |
|---|---|
| Filtrar por horário | Reprovado. As horas boas escolhidas em metade da amostra não se confirmam na outra — a interseção é de 3 hora(s), compatível com sorteio. |
| Operar só absorção, ou só divergência | Dentro do filtro de esforço as duas medem parecido (56,1% e 63,6%). Separar só reduz a amostra. |
| Operar só um lado | Compra mede 61,5% e venda 54,8%. A diferença está dentro do ruído para esta amostra. |
| Apertar o alvo para 1/4 de range | Parece melhor no backtest e não é: nessa distância os dois lados cabem na mesma barra e o número vira artefato da convenção. |
| Deixar correr quando “está indo bem” | Cada barra além da primeira devolve vantagem. É a medida mais consistente do estudo. |
| Aumentar o lote depois de uma sequência boa | Com t = +3,84, sequências boas e ruins de 10 operações são esperadas sem que nada tenha mudado. |
| Operar sem conferir o esforço | Sem o filtro a expectativa cai de +31,1 para +12,4 ticks — e o custo come a diferença inteira. |

## 7 · Como saber se parou de funcionar

Defina os critérios **agora**, enquanto não há dinheiro em jogo. Depois de uma sequência ruim ninguém escreve regra de parada honesta.

- **Registre toda operação** com: data e hora, tipo de sinal (absorção ou divergência), lado, `ResRel`, `Eficiência`, o esforço relativo calculado, preço de entrada, preço de saída, resultado em ticks e o slippage observado contra o fechamento da barra.
- **Depois de 50 operações**, compare o acerto com 58,0%. Abaixo de 50% com 50 operações ainda é ruído — mas já é hora de reler o registro.
- **Depois de 100 operações**, some o slippage médio. Se ele passar de 20 ticks por operação, a estratégia não tem margem: +31,1 ticks de expectativa bruta não paga isso.
- **Pare em -15R acumulados.** É 1,7 vezes o pior rebaixamento medido, e a essa altura a hipótese de que a vantagem sumiu é mais simples que a de azar.
- **Refaça o backtest a cada trimestre** com o histórico novo: `python rodar.py`. O número que mais importa acompanhar não é o acerto da estratégia, e sim a **linha de base** do §5.2 do relatório — a taxa de continuação do próprio gráfico, hoje em 51,45%. Boa parte da vantagem vem dali; se ela cair para 50%, o resto cai junto.

## 8 · Expectativa realista

> ⚠️ **A margem inteira cabe dentro de um spread ruim.** A expectativa bruta é de +31,1 ticks por operação. Com 20 ticks de custo ida-e-volta ela cai para +11,1; com 40 ticks fica **negativa** (-8,9). E a entrada é a mercado no fechamento de uma barra de range — que é exatamente um instante de movimento, onde o slippage é pior que a média.

| custo ida+volta | expectativa por operação | por pregão |
|---|---|---|
| 0 ticks | +31,1 ticks | +2,08 USD por lote |
| 10 ticks | +21,1 ticks | +1,41 USD por lote |
| 20 ticks | +11,1 ticks | +0,74 USD por lote |
| 40 ticks | -8,9 ticks | -0,60 USD por lote |

O que este plano é: uma vantagem pequena, real dentro da amostra, que passou em quatro validações independentes (platô, metades, terços e controle invertido) e que ainda assim foi escolhida como o melhor de 30 tentativas, num único histórico de 85 pregões.

O que ele não é: uma fonte de renda. **Comece com lote mínimo e trate os três primeiros meses como coleta de dados**, não como operação. O objetivo dessa fase é medir o seu slippage real — que é a única variável desconhecida que decide se sobra alguma coisa.

> **O teste mais honesto que você pode fazer.** Opere em conta demo e em conta real ao mesmo tempo, com o mesmo lote mínimo, durante 100 operações. A diferença entre as duas curvas é o seu custo real de execução. Se ela for maior que 31 ticks por operação, o plano não tem margem — e é melhor descobrir isso com lote mínimo.

---

Gerado por `plano.py` a partir de `saida/resumo.json` (2026-09-06 09:37). Os números vêm todos do backtest; nenhum foi digitado à mão. Para refazer: `python rodar.py && python plano.py`.
