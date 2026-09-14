# ESTRATEGIA

No ativo XAUUSD, usando o **gráfico de range de 388 ticks** (símbolo sintético
gerado pelo `Range_Claude_v1.mq5`), o gatilho a estudar não é geométrico — é de
**esforço × resultado**, e está implementado no indicador

```
MQL5\Indicators\Triggers\Trigger_EsforcoResultado_Range.mq5
```

## A ideia

Num gráfico de range o `High-Low` é constante por construção. Corpo e pavio são,
portanto, complementares: tudo que virou pavio foi caminho andado e devolvido. O
corpo (`Close-Open`) é o **resultado líquido** real do trabalho feito dentro da
barra, e não uma escolha de escala.

Do outro lado está o **esforço**: no símbolo sintético, `tick_volume` carrega a
agressão compradora e `real_volume` a vendedora. Então

```
res  = (Close - Open) em ticks      -> RESULTADO
esf  = AgrCompra + AgrVenda         -> ESFORÇO total
dlt  = AgrCompra - AgrVenda         -> agressão líquida
qual = (dlt * dir) / esf            -> fração do esforço A FAVOR da barra
```

Cada barra é comparada com a **média das barras da sua própria direção** nas
últimas 60 — nunca com a média geral. Em janela de alta o delta médio é positivo
mesmo em barra irrelevante; comparar só contra o próprio lado cancela esse viés.

## Os dois sinais

**SINAL 1 — ABSORÇÃO.** A barra N vira o movimento (N-1 era contrária), o
resultado de N está abaixo do normal da direção (`resRel < 0,70`) e o esforço a
favor de N está abaixo do normal (`qualRel < 0,50`). A barra andou sem que a
agressão a empurrasse: quem venceu foi a passiva do lado da barra. Opera-se **a
favor de N**.

**SINAL 2 — DIVERGÊNCIA NO PIVÔ.** N-2 e N-1 na mesma direção, N na contrária;
N-1 e N quase sem pavio (corpo ≥ 80% do range nas duas — são elas que formam o
pivô); e o delta somado de N-1+N é **contrário** à direção de N. O pivô é um
round trip: anda R e devolve R, o deslocamento líquido é ~zero e o viés
geométrico do delta se cancela entre as duas barras — por isso aqui o zero é
referência legítima, sem precisar de média. Opera-se **a favor de N**.

## O que se quer medir

O indicador diz *quando*. Ele não diz *quanto*, nem *até onde*. As perguntas do
estudo são:

- O sinal tem leitura de direção, ou a excursão depois dele é igual à de uma
  entrada sorteada?
- Absorção e divergência são a mesma coisa, ou dois sinais com estatísticas
  diferentes que só dividem um buffer?
- Qual gestão cabe num gráfico onde o range é fixo em 388 ticks?
- Os parâmetros do indicador (60 barras, 0,70, 0,50, 0,80, 0,05) são um platô ou
  um pico? Um pico é ajuste à amostra.
- Filtros de horário, de contexto e de qualidade do próprio sinal sobrevivem a
  uma validação fora da amostra?

## TAREFAS

• Fazer um backtest bem documentado do gatilho, baseado no histórico desta pasta
  (`XAUUSD-388N\XAUUSD_388_N_M1_202605110101_202609042330.csv`), com o indicador
  portado fielmente para Python — a matemática linha a linha do `.mq5`.

• Elaborar um relatório em .md

• Elaborar um relatório em html: com as variantes sugeridas, restrições
  recomendadas, estatísticas relevantes, explicação de cada termo utilizado, e
  gráfico de candles operação a operação (intercalável entre as variantes), com
  o painel de agressão embaixo — que é o que o indicador lê.

• Um plano para trading manual em .md e em html.
