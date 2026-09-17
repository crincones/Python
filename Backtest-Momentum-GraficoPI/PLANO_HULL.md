# Plano de trading -- Hull a favor, retracao curta (provisorio)

WINFUT, grafico de 20 PI. Backteste de 132 pregoes (06/03/2026 a 14/09/2026), bruto. A regra e a que passou no teste fora da amostra (os cortes de pavio e de contagem do plano anterior sairam). **O custo real decide:** so continue se ficar abaixo de 3,7 pts por operacao. **Rode em simulador antes de dinheiro real.**

## O setup

- Por operacao: +8,1 pts brutos (R$ +1,61 por contrato); com 5 pts de custo, +2,5 por sinal; com 10, -2,5
- Acerto: 27,4%
- Frequencia: 33,1 operacoes por pregao
- Rebaixamento maximo: 4.700 pts (Monte Carlo p95: 6.000)

## As 3 perguntas (compra; venda e o espelho)

### 1. A Hull 50 esta inclinada a favor do trade?

Para **comprar**, a Hull 50 tem de estar **subindo** no fechamento do candle de sinal (valor atual maior que o do candle anterior). Para **vender**, descendo. Nao importa se o preco esta acima ou abaixo dela.

> E o filtro que passou no teste fora da amostra: nos meses que nao participaram de nenhuma escolha, +6,5 pts por sinal com a Hull a favor; -2,2 com ela contra.

**Nao vale se:** Hull plana ou inclinada contra.

### 2. Vieram de 2 a 4 candles seguidos CONTRA a Hull?

Na compra: 2, 3 ou 4 candles seguidos de **baixa**, no mesmo pregao, imediatamente antes do candle de sinal. Na venda: 2 a 4 de alta.

> 2, 3 e 4 antes mediram parecido (+7,7, +7,0, +7,1); 1 so (+1,3) e 5 ou mais (-0,8) nao pagam.

**Nao vale se:** 1 candle, ou 5 ou mais. Retracao que atravessa a virada do dia.

### 3. O candle de sinal fechou A FAVOR da Hull?

O candle atual fecha no sentido da Hull: **alta** na compra, **baixa** na venda. Espere o candle **fechar**.

> E o primeiro candle que devolve o movimento para o lado da Hull. A entrada e no fechamento dele.

**Nao vale se:** Candle ainda aberto.

## Gestao

- **Entrada:** a mercado, no fechamento do candle de sinal (nao usar limitada no meio do corpo).
- **Stop:** 100 pontos, junto com a entrada.
- **+100:** sai metade; o stop do restante fica na media da operacao (= stop inicial: se voltar, zero a zero).
- **Alvo:** 300 pontos no restante.
- **Fim do dia:** zera no ultimo candle do pregao. Uma posicao por vez.

## Checklist

- [ ] Hull 50 inclinada a favor do trade
- [ ] 2 a 4 candles seguidos contra a Hull, no mesmo pregao
- [ ] Candle de sinal FECHADO a favor da Hull
- [ ] Nenhuma posicao aberta agora
- [ ] Stop de 100 pontos definido ANTES de entrar
- [ ] Custo real da operacao anotado

## Quando parar

- Custo real medio acima de 3,7 pts por operacao
- Rebaixamento acima de 6.000 pts (p95 do Monte Carlo)
- Mais de 20 perdas seguidas
- Valor por operacao abaixo do custo real depois de 300 operacoes

## O que nao fazer

- Entrar antes do candle fechar.
- Filtrar pelo pavio (nenhum corte passou fora da amostra).
- Exigir a Hull longe da banda ou do lado oposto da EMA (mediu ao contrario).
- Operar com a Hull plana ou contra.
