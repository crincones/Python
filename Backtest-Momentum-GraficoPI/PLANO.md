# Plano de trading -- momentum no grafico de 20 PI (WINFUT)

Seis perguntas de sim ou nao, na ordem em que se olha para a tela. Se qualquer uma der nao, o trade nao existe -- nao ha "quase".

> **Leia isto antes.** Este plano sai de um backteste de **26 pregoes** (2026-08-06 a 2026-09-11) -- pouco mais de um mes, todo em mercado de alta. Os numeros sao **brutos**, sem corretagem e sem slippage. Rode em simulador por pelo menos um mes antes de dinheiro real. Ver [RESULTADOS.md](RESULTADOS.md) para o que o teste nao mediu.

## O setup

No grafico de **20 PI** do WINFUT todo candle fecha exatamente 100 pontos acima ou abaixo da sua abertura. Procura-se uma **retracao** contra a tendencia seguida de um candle de **continuacao** a favor, com a Hull 50 atras do preco e a EMA 21 cortando o par. A venda e o espelho exato da compra.

| | |
| :--- | ---: |
| Por operacao | +34,1 pts (R$ +6,82) |
| Acerto | 36,5% |
| Operacoes por pregao | 6,8 |
| Rebaixamento maximo medido | 800 pts |
| Medido em | 170 operacoes, 25 pregoes |

## Os seis passos

### 1. A Hull 50 esta no sentido do trade?

Para comprar, a Hull tem de estar **subindo** e ficar **abaixo** do preco. Para vender, descendo e acima.

> *Por que:* E a unica coisa que define de que lado se opera. Sem ela nao ha "continuacao" de coisa nenhuma.

**Nao vale se:** Hull plana, ou preco do lado errado dela.

### 2. Houve uma retracao de 2 ou mais candles?

Conte os candles **contra** a tendencia antes do candle atual. Precisa de **2 ou mais**.

> *Por que:* Um candle so de retracao mede menos da metade de dois. Um candle contra e ruido; dois ja sao um movimento.

**Nao vale se:** Retracao de um candle so. Espere a proxima.

### 3. Os dois extremos do par estao fora da Hull?

O topo do ultimo candle da retracao **e** o topo do candle de continuacao, os dois acima da Hull (numa compra). Na venda, os dois fundos abaixo dela.

> *Por que:* E o que separa um pullback dentro da tendencia de uma virada que ja atravessou a media.

**Nao vale se:** Qualquer um dos dois extremos do lado de dentro da Hull.

### 4. A EMA 21 passa entre os topos e os fundos do par?

A EMA 21 tem de estar **dentro** da faixa que vai do menor fundo ao maior topo dos dois candles.

> *Por que:* E a forma de exigir que a retracao tenha ido ate a media -- nem menos (nao retraiu), nem mais (nao e mais retracao).

**Nao vale se:** EMA acima do par inteiro ou abaixo dele.

### VETO. NAO e exaustao?

Descarte se as **duas** coisas forem verdade ao mesmo tempo: a Hull esta **abrindo a curva** a favor do trade (acelerando) **e** o fechamento ja esta a mais de **0,45 ATR** da EMA 21 (com ATR perto de 150, isso e mais ou menos **68 pontos**).

> *Por que:* E o filtro que mais separa. Sozinha, nenhuma das duas metades diz quase nada; juntas marcam 4 de cada 10 sinais, e esses 4 nao pagam. E a intuicao da "Hull perto da banda", so que medida no lugar certo.

**Nao vale se:** Hull acelerando E preco ja esticado. E o unico veto obrigatorio.

### 6. O candle de continuacao tem a forma certa?

Pavio total (range menos os 100 pontos do corpo) entre **25** e **90** pontos. Na pratica: o range do candle entre 125 e 190 pontos.

> *Por que:* No grafico de PI o corpo e sempre 100 pontos, entao o pavio E a forma. Candle liso demais e fino demais para pagar; candle de pavio enorme e briga, nao continuacao.

**Nao vale se:** Este e o que separa Ouro de Prata. Falhando so ele, o sinal ainda e Prata -- opere menor, ou nao opere.

## Ouro, Prata e Bronze

Quando um passo falha, o sinal cai de nivel em vez de virar lixo.

| Nivel | Passos que cumpre | Por operacao | Acerto | Por dia | Rebaix. | O que fazer |
| :--- | :--- | ---: | ---: | ---: | ---: | :--- |
| **Ouro** | 1 a 6, todos | +34,1 pts | 36,5% | 6,8 | 800 pts | Opere. |
| **Prata** | 1 a 5 (falha so o 6) | +27,4 pts | 34,2% | 9,3 | 600 pts | Opere com metade do tamanho, ou deixe passar. |
| **Bronze** | 1 a 4 (falha o veto de exaustao) | +11,5 pts | 29,3% | 21,9 | 1.700 pts | Nao opere. |

O Bronze esta na tabela para deixar claro **quanto** se perde operando tudo: quatro vezes mais trades para ganhar o mesmo, com o dobro do rebaixamento -- e isso antes do custo, que multiplica por quatro tambem.

## Gestao da operacao

Fixa. Nao se negocia stop no meio do trade.

- **Entrada:** a mercado, no **fechamento** do candle de continuacao. Nao antecipe: entrar no meio do corpo com limitada mede pior, porque perde justamente os trades que nao voltam -- e sao eles que pagam.
- **Stop:** 100 pontos, posicionado **antes** de enviar a entrada. Um candle de PI inteiro e 100 pontos: o stop equivale a um candle contra.
- **Parcial:** metade da posicao em +100. O stop do restante **nao se move** -- com meia posicao e a parcial na mesma distancia do stop, o preco em que o lucro ja realizado cancela a perda do restante *e* o stop inicial. Mudou o risco, nao o preco.
- **Alvo:** o restante em +300. Nao mexa com a operacao aberta: a grade inteira foi medida e 300 e topo local (250 e 400 medem pior).
- **1:2, se quiser:** trocar o alvo de 300 por **200** sem parcial sobe o acerto de 36,5% para **41,6%** e derruba a expectativa de +34,1 para **+24,3** pontos por operacao, com rebaixamento **maior** (1.400 contra 800). Mede positivo, mas paga para errar menos. Se a sequencia de perdas do 1:3 for o que te tira do plano, e um preco honesto por isso; fora dessa razao, nao compensa.
- **Fim do pregao:** zera no ultimo candle do dia. Day trade, sem excecao.
- **Uma por vez:** enquanto houver posicao aberta, sinal novo e ignorado. Todos os numeros foram medidos assim.

## Regras de mesa

**O que o backteste apoia**

- Operar os dois lados (40,5% de acerto na compra, 33,0% na venda).
- Operar o dia inteiro: nenhuma faixa de horario se mostrou boa ou ruim de forma estavel, inclusive a hora seguinte a abertura do mercado a vista.
- Tamanho de posicao constante.

**O que fica a criterio, com medicao a favor**

- **Hull colada na EMA.** Mais de 8 candles colada na EMA 21 mediu muito mal -- e a consolidacao. Amostra pequena (31 sinais), por isso nao entrou na regra; mas se o cacho esta embolado na tela, ha medicao a favor de deixar passar.
- **Sem a parcial.** Rende mais (+44,7 contra +34,1 por trade) e balanca mais (1.200 contra 800 pontos de rebaixamento). Escolha de conforto.

## Como o Ouro se parece

Seis exemplos reais, espalhados pelo periodo do backteste, estao em `plano.html` (secao *Como se parece*) e no relatorio, que tem tambem as galerias do Prata e do Bronze com o motivo de cada um nao ter subido de nivel. Em texto nao da para desenhar candle; o que da para deixar escrito e o que procurar neles:

- a **Hull 50** passando por baixo do par inteiro (numa compra), ja inclinada;
- **dois ou tres** candles de retracao, nao um;
- a **EMA 21** cortando o par, nem acima nem abaixo dele;
- o candle de continuacao com pavio **visivel mas nao enorme** -- entre 25 e 90 pontos, num candle cujo corpo e sempre 100.

Com acerto de 36%, a maioria dos exemplos de qualquer amostra honesta vai ser de perda. O que ha para decorar e o desenho, nao o desfecho.

## Folha de checagem

Todas marcadas, envia. Uma so em branco, nao envia.

- [ ] Hull 50 no sentido do trade e atras do preco
- [ ] Retracao de 2 ou mais candles
- [ ] Os dois extremos do par fora da Hull
- [ ] EMA 21 entre os topos e os fundos do par
- [ ] NAO e exaustao (Hull acelerando + preco esticado)
- [ ] Pavio total do candle entre 25 e 90 pontos
- [ ] Stop de 100 pontos ja posicionado ANTES de entrar
- [ ] Nao ha posicao aberta neste momento

### Os tres erros que este plano tenta impedir

1. **Entrar esticado.** O passo 5 existe so para isso, e e o filtro que mais separa.
2. **Chamar um candle de retracao.** O passo 2 pede dois.
3. **Operar todo sinal que aparece.** O Bronze existe na tabela para mostrar o preco disso.

---

*Gerado de `relatorio.html` / `RESULTADOS.md`. Base: 10.000 candles de 20 PI, 26 pregoes. Backteste nao e promessa.*