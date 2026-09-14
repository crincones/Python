# Plano de trading -- Hull a favor, retracao curta (provisorio)

WINFUT, grafico de 20 PI. Backteste de 26 pregoes (06/08/2026 a 11/09/2026), bruto, mercado de alta. A Hull a favor era hipotese previa; os passos 2 e 4 foram ajustados nesta amostra. **Rode em simulador antes de dinheiro real.**

## O setup

- Por operacao: +17,6 pts brutos (R$ +3,53 por contrato); com 10 pts de custo, +6,7 por sinal
- Acerto: 30,8%
- Frequencia: 25,7 operacoes por pregao
- Rebaixamento maximo: 1.400 pts (Monte Carlo p95: 2.500)

## Qual pavio olhar

COMPRA (Hull 50 subindo, 2 ou 3 candles de baixa antes):

```
      |     <- AVALIADO: pavio de CIMA = maxima - fechamento <= 10% do corpo
    +---+   <- fechamento = entrada
    |   |
    |   |      candle de sinal, de ALTA (corpo 100)
    +---+   <- abertura
      |
      |     <- NAO avaliado: pavio de baixo (lado da abertura), qualquer tamanho
```

VENDA (Hull 50 descendo, 2 ou 3 candles de alta antes):

```
      |
      |     <- NAO avaliado: pavio de cima (lado da abertura), qualquer tamanho
    +---+   <- abertura
    |   |
    |   |      candle de sinal, de BAIXA (corpo 100)
    +---+   <- fechamento = entrada
      |     <- AVALIADO: pavio de BAIXO = fechamento - minima <= 10% do corpo
```

O pavio avaliado e sempre o do lado do **fechamento** do candle de sinal: o de cima na compra, o
de baixo na venda. O pavio do lado da abertura nao entra na regra.

## As 4 perguntas (compra; venda e o espelho)

### 1. A Hull 50 esta inclinada a favor do trade?

Para **comprar**, a Hull 50 tem de estar **subindo** no fechamento do candle de sinal (valor atual maior que o do candle anterior). Para **vender**, descendo. Nao importa se o preco esta acima ou abaixo dela.

> E o filtro que sustenta o setup: com a Hull contra, o mesmo padrao mede +1,7 pts por sinal; a favor, +11,4.

**Nao vale se:** Hull plana ou inclinada contra.

### 2. Vieram 2 ou 3 candles seguidos CONTRA a Hull?

Na compra: 2 ou 3 candles seguidos de **baixa**, no mesmo pregao, imediatamente antes do candle de sinal. Na venda: 2 ou 3 de alta.

> 3 antes mediu +20,1, 2 antes +11,2; 1 so e fraco (+7,1) e 4 perde (-9,2).

**Nao vale se:** 1 candle, ou 4 ou mais. Retracao que atravessa a virada do dia.

### 3. O candle de sinal fechou A FAVOR da Hull?

O candle atual fecha no sentido da Hull: **alta** na compra, **baixa** na venda. Espere o candle **fechar**: antes disso o lado dele nao esta definido.

> E o primeiro candle que devolve o movimento para o lado da Hull.

**Nao vale se:** Candle ainda aberto.

### 4. O pavio do lado do fechamento e pequeno?

Na compra, o pavio de **cima** do candle de sinal (maxima menos fechamento) ate **10 pontos** (10% do corpo). Na venda, o de **baixo** (fechamento menos minima). O pavio do outro lado (o da abertura) nao importa.

> Ate 10% mediu +14,6 pts por sinal; acima, -6,4. Pavio grande alem do fechamento e o preco rejeitado justamente no sentido do trade.

**Nao vale se:** Pavio do lado do fechamento acima de 10 pontos.

## Gestao

- **Entrada:** a mercado, no fechamento do candle de sinal (nao usar limitada no meio do corpo).
- **Stop:** 100 pontos, junto com a entrada.
- **+100:** sai metade; o stop do restante fica na media da operacao (= stop inicial: se voltar, zero a zero).
- **Alvo:** 300 pontos no restante.
- **Fim do dia:** zera no ultimo candle do pregao. Uma posicao por vez.

## Checklist

- [ ] Hull 50 inclinada a favor do trade
- [ ] 2 ou 3 candles seguidos contra a Hull, no mesmo pregao
- [ ] Candle de sinal FECHADO a favor da Hull
- [ ] Pavio do lado do fechamento ate 10 pontos
- [ ] Nenhuma posicao aberta agora
- [ ] Stop de 100 pontos definido ANTES de entrar

## Quando parar

- Rebaixamento acima de 2.500 pts (p95 do Monte Carlo)
- Mais de 7 perdas seguidas
- Acerto abaixo de 25% depois de 100 operacoes (medido: 30,8%)
- Valor por operacao abaixo do custo real depois de 100 operacoes

## O que nao fazer

- Entrar antes do candle fechar.
- Filtrar pelo pavio da abertura (efeito so na compra, se inverte na limitada).
- Aceitar 4 candles de retracao.
- Operar com a Hull plana ou contra.
