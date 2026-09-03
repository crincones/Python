# Plano de operação manual — leque de EMAs em XAUUSD 521 ticks

Versão de 2026-09-02. Baseado em `RESULTADOS.md`, que mede 70.010 barras em 87 pregões. Este plano descreve a variante **V7** do backtest — a única que continuou positiva depois de descontar custo.

## 0 · Leia isto antes de tudo

> ⚠️ A estratégia original, como está escrita em `ESTRATEGIA.md`, **perde dinheiro** neste histórico: -24,2 ticks por operação em 1.726 operações. E o gatilho não tem leitura de direção — a excursão do preço depois da entrada é estatisticamente igual à de uma entrada sorteada. Este plano não é a estratégia validada; é o **resto que sobrou** depois de tirar o que estava medindo negativo, e ele se sustenta sobre 257 operações apenas.

O que mudou em relação ao texto original, e por quê:

| no texto original | neste plano | por quê |
|---|---|---|
| opera a qualquer hora | só em 05h, 06h, 12h, 13h, 16h, 18h | é a única restrição que passou em validação fora da amostra, nos dois sentidos |
| o candle de gatilho só precisa aparecer no leque | ele tem de **fechar** além da EMA21 | elimina o caso ambíguo da barra que encosta na média e fecha do lado errado |
| parcial de 50% em 300 e o resto até 900 | **100% da posição sai em 300** | só 10,3% das operações chegavam aos 900; o runner era o que consumia o resultado |
| limitar o tamanho do candle de reversão | sem limite | medido: as barras grandes mediram melhor que as pequenas, não pior |

## 1 · A configuração da tela

- Ativo **XAUUSD**, gráfico de **521 ticks**.
- Três médias móveis **exponenciais** sobre o fechamento: **21**, **42** e **72**. Cores distintas; a de 21 é a que importa.
- Escala vertical em dólares. Marque no papel que **1 tick = 0,01 USD** e que **300 ticks = 3,00 USD = 1R**.
- Relógio do gráfico configurado no mesmo fuso do arquivo usado no backtest. **Confirme isso antes da primeira operação** — se o fuso for outro, todo o filtro de horário deste plano aponta para as horas erradas.

> Referência de tamanho, para calibrar o olho: a barra mediana deste gráfico anda **277 ticks**. O stop de 300 ticks é pouco mais de **uma** barra mediana. Se um candle de gatilho tem 600 ticks de range, o stop cabe dentro dele — isso não impede a operação, mas explica por que ela morre rápido.

## 2 · Quando olhar — a janela de operação

Opere **somente** dentro destas horas. Fora delas, o gráfico fica fechado: 05h, 06h, 12h, 13h, 16h, 18h.

| hora | sinais no histórico | acerto | expectativa |
|---|---|---|---|
| 05h | 74 | 58,1% | +49 t |
| 06h | 71 | 60,6% | +63 t |
| 12h | 77 | 63,6% | +82 t |
| 13h | 70 | 58,6% | +51 t |
| 16h | 128 | 57,0% | +42 t |
| 18h | 108 | 61,1% | +67 t |

_Medido sobre a regra literal com a métrica neutra de 1:1 — é o corte que define a janela, e não o desempenho da V7 hora a hora, que teria poucas operações por hora para significar algo._

São 6 horas de 23. Na prática isso significa **3,1 operações por pregão**, em média — e vários pregões sem nenhuma. A disciplina de não operar fora da janela é a parte mais valiosa e a mais difícil deste plano.

## 3 · O setup, passo a passo

As cinco condições abaixo têm de valer **todas**, na ordem. Se uma falhar, não há operação — não existe "quase".

1. **Leque formado.** As três EMAs ordenadas: 21 acima de 42 acima de 72 (vou comprar), ou 21 abaixo de 42 abaixo de 72 (vou vender). Se as médias estão cruzadas ou coladas, não há leque — passe.
2. **O preço se afastou.** Nas últimas ~12 barras houve pelo menos uma barra **inteira** do lado de fora da EMA21, no sentido da tendência. Se o preço está grudado nas médias há dez barras, não houve afastamento — passe.
3. **Voltou ao leque com 2 ou 3 candles da mesma cor.** O recuo é contrário à tendência: em leque de alta, 2 ou 3 candles vermelhos seguidos; em leque de baixa, 2 ou 3 verdes. **Nem 1, nem 4.** Quatro candles seguidos não é pullback, é reversão — passe.
4. **O candle de gatilho aparece.** O primeiro candle de cor contrária ao recuo (ou seja, da cor da tendência), que **toca a EMA21** e **fecha do lado da tendência** — acima da EMA21 para comprar, abaixo para vender. Se ele toca mas fecha do lado errado, não é gatilho.
5. **A hora está na janela** (§ 2). Este é o filtro que se esquece de checar; cheque.

> Nenhuma condição envolve o tamanho do candle de gatilho. Foi testado e medido: pôr teto no range da barra de reversão **piorou** o resultado. Deixe passar o candle grande.

## 4 · A ordem

1. Meça o **meio do range do candle de gatilho**: `(máxima + mínima) / 2`.
2. Coloque uma ordem **limitada** nesse preço — compra se o leque é de alta, venda se é de baixa.
3. A ordem vale por **uma barra**. Se a barra seguinte não tocar o preço, **cancele**. Não persiga, não role para a barra seguinte, não entre a mercado.
4. Se ela ativar, monte imediatamente o stop e o alvo da § 5.

No histórico, **32,0%** dos gatilhos não ativam e viram nada. Isso é o desenho funcionando, não uma oportunidade perdida: a ordem limitada é o que faz o preço de entrada ser melhor que o fechamento do gatilho.

## 5 · Stop e alvo

|  | distância | em dólares | em R |
|---|---|---|---|
| **Stop** | 300 ticks | 3,00 USD | −1R |
| **Alvo** | 300 ticks | 3,00 USD | +1R |

- **A posição inteira sai no alvo.** Sem parcial, sem runner, sem mover o stop para o breakeven.
- Stop e alvo entram na corretora **assim que a ordem ativa**, os dois juntos, como OCO. Depois disso a operação é da máquina, não sua.
- Não existe saída manual "porque o candle ficou feio". A vantagem medida é pequena; ela desaparece inteira se você fechar as vencedoras antes do alvo.

> Esta é a mudança mais importante em relação ao plano original, e a mais contraintuitiva: **o alvo de 900 ticks era o que quebrava a estratégia**. Ele exige 3,2 barras medianas de continuação, e só chegava lá em 10,3% das operações. A parcial em 300 com stop no breakeven, por sua vez, transformava a maioria das vencedoras em meio ganho. Sair inteiro em 300 é feio no papel — relação 1:1 — mas é o que mede positivo.

### Se quiser manter o 2:1 do plano original

A variante V5 mantém a parcial de 50% em 300 com stop no breakeven e o runner até 900. Ela também mede positivo, mas menos: +39,3 ticks por operação contra +71,2 da V7, e — o que mais importa — ela **fica negativa** (-0,7 ticks) com 40 ticks de custo, enquanto a V7 continua em +31,2. Se optar pela V5, saiba que está trocando expectativa por uma estética de relação risco/retorno.

## 6 · Tamanho da posição

Regra única: **arrisque 0,25% da conta por operação** enquanto este plano estiver em teste. Não 1%, não 2%. O motivo está na § 8: a vantagem medida é pequena e a amostra é curta, então o tamanho tem de ser o de um experimento, não o de uma convicção.

A conta é direta, porque o stop é fixo em 300 ticks: **cada onça de ouro na posição arrisca 3,00 USD**. Divida o risco da operação por esse número e terá o tamanho em onças.

| conta | risco por operação (0,25%) | tamanho em onças | em lotes padrão (100 oz) | resultado esperado por pregão |
|---|---|---|---|---|
| 1.000 USD | 2,50 USD | 0,83 | 0,008 | +1,84 USD |
| 5.000 USD | 12,50 USD | 4,17 | 0,042 | +9,19 USD |
| 10.000 USD | 25,00 USD | 8,33 | 0,083 | +18,37 USD |
| 25.000 USD | 62,50 USD | 20,83 | 0,208 | +45,93 USD |

> ⚠️ Confirme com a sua corretora quantas onças tem um lote. Em MetaTrader o lote padrão de XAUUSD costuma ser **100 onças** e o mínimo, 0,01 lote = 1 onça — mas há corretoras que usam 10. Errar essa conversão multiplica ou divide o risco por dez.

_A última coluna usa a expectativa medida de +71,2 ticks por operação, ou +0,237 de R, e 3,1 operações por pregão. É uma projeção da média, não uma promessa: a distribuição real tem desvio-padrão de 292 ticks por operação, dez vezes a média._

## 7 · Limites do dia e da semana

- **Três stops no mesmo pregão: encerra o dia.** Sem exceção, sem "recuperar".
- **Perda de 2R no dia: encerra o dia**, mesmo que sejam duas operações.
- **Perda de 6R na semana: encerra a semana.** Volta na segunda-feira seguinte.
- **Nenhuma operação nova a menos de 10 minutos do fim da janela** da hora — a operação típica dura 3,5 barras, e barra de 521 ticks não tem duração fixa.
- **Nada de operar em dia de dado macro de peso** (decisão de juros, payroll, CPI) na hora do anúncio. O backtest inclui esses dias e não os separa; o slippage real deles não está medido em lugar nenhum deste estudo.

No histórico o pior dia da variante foi de -1.200 ticks e o maior rebaixamento acumulado foi de -2.400 ticks, ou -8,0 R. Um rebaixamento dessa ordem **vai** acontecer; o limite acima existe para que ele aconteça com você ainda na cadeira.

## 8 · O que esperar — números honestos

|  | V7 (este plano) | V5 (com runner) | V0 (regra original) |
|---|---|---|---|
| Operações no histórico | 257 | 248 | 1.726 |
| Operações por pregão | 3,1 | 3,0 | 19,8 |
| Acerto | 61,9% | 61,3% | 51,0% |
| Expectativa por operação | +71,2 t | +39,3 t | -24,2 t |
| Expectativa em R | +0,237 | +0,131 | -0,081 |
| Fator de lucro | 1,62 | 1,34 | 0,84 |
| Rebaixamento máximo | -2.400 t | -2.550 t | -46.200 t |
| Com 20 ticks de custo | +51,2 t | +19,3 t | -44,2 t |
| Com 40 ticks de custo | +31,2 t | -0,7 t | -64,2 t |
| 1ª metade da amostra | +80,9 t | +48,6 t | -25,1 t |
| 2ª metade da amostra | +63,4 t | +31,8 t | -23,2 t |

Duas leituras que valem mais que a linha da expectativa:

- **O custo decide.** A vantagem inteira cabe dentro do spread. Antes de operar, meça o custo real da sua corretora em ouro: some spread médio e comissão, em ticks, ida e volta. Se der acima de 40, este plano não tem margem — não opere.
- **A amostra é curta.** 257 operações dão um erro-padrão de expectativa de cerca de 18 ticks por operação, sobre uma expectativa de 71. Ou seja: o intervalo de confiança encosta perto do zero.

## 9 · Rotina do pregão

### Antes (5 minutos)

- Confirmar o fuso do gráfico e escrever no papel as horas de hoje.
- Conferir a agenda de indicadores e riscar as horas que caem em cima de um anúncio.
- Escrever o risco em dólares por operação (0,25% da conta de hoje) e o tamanho em onças correspondente (§ 6).
- Escrever os limites: 3 stops, −2R no dia.

### Durante

- Fora da janela, o gráfico fica fechado. Literalmente: minimize.
- Dentro da janela, olhar só o fechamento das barras. A regra é toda de fechamento — não há decisão a tomar com a barra em formação.
- Ao ver um gatilho: conferir as cinco condições da § 3 **em voz alta** antes de mandar a ordem.
- Ordem enviada: anotar na planilha antes de qualquer outra coisa.
- Ordem não ativada na barra seguinte: cancelar e anotar como abortada. Elas contam.

### Depois (5 minutos)

- Fechar a linha de cada operação na planilha, inclusive as abortadas.
- Uma frase sobre qualquer momento em que a regra foi quebrada. Se não houve, escrever "nenhuma".
- Uma vez por semana: comparar acerto e expectativa acumulados com a tabela da § 8.

## 10 · A planilha

Uma linha por sinal — **inclusive os que não ativaram**, porque a taxa de ativação é uma das coisas que este plano precisa verificar em tempo real.

| data | hora | lado | preço da ordem | ativou? | entrada | saída | ticks | R | regra quebrada? |
|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |

Colunas calculadas ao fim de cada semana: número de sinais, taxa de ativação, acerto, expectativa em ticks e em R, e o acumulado em R.

## 11 · Critério de parada — escrito antes de começar

Este plano é um **teste**, e teste precisa de um critério de encerramento definido antes, quando ainda não dói. Os três abaixo valem simultaneamente:

1. **Ao fim de 100 operações**, comparar a expectativa medida com a do backtest (+71,2 ticks). Se estiver negativa, o teste terminou: a vantagem não existia. Se estiver positiva mas abaixo da metade, ela existe e é menor do que o custo de operar — o que dá no mesmo.
2. **Rebaixamento de 10R** desde o pico da curva: parar e revisar. É mais que o rebaixamento máximo do backtest (8,0 R), então indica que alguma coisa mudou ou que o backtest era otimista.
3. **Taxa de ativação muito diferente de 63%**: se as ordens estão ativando muito mais, você está entrando a mercado sem perceber; muito menos, e o preço da ordem está sendo calculado errado. Nos dois casos o que você opera não é o que foi medido.

---

_Gerado por `plano.py` a partir de `saida/resumo.json`. Os números vêm todos do backtest documentado em `RESULTADOS.md` e `relatorio.html`._

