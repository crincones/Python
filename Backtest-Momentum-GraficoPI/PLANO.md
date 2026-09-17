# Plano de trading -- SUSPENSO, hipotese em teste (WINFUT, 20 PI)

> **Status.** O padrao Ouro deste plano **nao passou** no teste fora da amostra da base de 132 pregoes. **Nao operar o Ouro nem o Prata**, e desligar o robo `Robo-NTSL/MomentumPI_OuroPrata_Robo.ntsl`. O que segue e o protocolo para testar, em simulador, a unica hipotese que sobrou.

## Por que o plano anterior parou

Os filtros do Ouro foram escolhidos em 26 pregoes (06/08 a 11/09). Nos cinco meses anteriores, que nunca participaram da escolha (pontos por sinal, fechamento, 1:3 com parcial):

| Nivel | Antes (06/03 a 05/08) | Janela original (06/08 a 11/09) |
| :--- | ---: | ---: |
| Ouro | -7,4 (678) | +34,8 (181) |
| Prata | -0,7 (1016) | +28,3 (258) |
| Bronze | -0,2 (2819) | +11,4 (679) |

## A hipotese

A regra-base do CLAUDE.md com **uma** exigencia a mais: retracao de **3 ou mais candles**. Sem veto de exaustao, sem filtro de pavio, sem horario.

- Medido: +15,0 pts por trade brutos, 419 trades em 132 pregoes, acerto 29,4%, fator de lucro 1,35, rebaixamento 1.100 pts (Monte Carlo p95 2.500).
- Antes: +15,3; janela original: +14,8.
- **Nao e setup ainda:** o corte foi escolhido olhando esta base; refeita a busca em dados embaralhados sobre todas as tabelas olhadas, algo tao bom aparece 17% das vezes.

## Os cinco passos (compra; venda e o espelho)

### 1. A Hull 50 esta no sentido do trade?

Para comprar, a Hull tem de estar **subindo** e **abaixo** da maxima do candle. Para vender, descendo e acima da minima.

> *Por que:* Define de que lado se opera. No estudo hull_contra, refeito na base nova, a Hull a favor foi a unica hipotese previa que passou no teste fora da amostra.

**Nao vale se:** Hull plana, ou do lado errado do preco.

### 2. Houve uma retracao de 3 ou mais candles?

Conte os candles **seguidos contra** a Hull, no mesmo pregao, antes do candle atual. Precisa de **3 ou mais**.

> *Por que:* E a hipotese em teste. Com 1 ou 2 candles de retracao a regra-base mediu perto de zero nos 132 pregoes; com 3 ou mais, positivo nos dois blocos e nos tres tercos.

**Nao vale se:** Retracao de 1 ou 2 candles, ou que atravessa a virada do dia.

### 3. O candle atual FECHOU a favor?

Espere o candle **fechar**: alta na compra, baixa na venda. E o candle de continuacao.

> *Por que:* Antes do fechamento o sinal nao existe, e a entrada antecipada nao pode ser medida com a base disponivel.

**Nao vale se:** Candle ainda aberto.

### 4. Os dois extremos do par estao fora da Hull?

O topo do ultimo candle da retracao **e** o topo do candle de continuacao acima da Hull (numa compra). Na venda, os dois fundos abaixo dela.

> *Por que:* Separa um recuo dentro da tendencia de uma virada que ja atravessou a media.

**Nao vale se:** Qualquer um dos dois extremos do lado de dentro da Hull.

### 5. A EMA 21 passa entre os topos e os fundos do par?

A EMA 21 tem de estar **dentro** da faixa do menor fundo ao maior topo dos dois candles.

> *Por que:* Exige que a retracao tenha ido ate a media.

**Nao vale se:** EMA acima do par inteiro ou abaixo dele.

## Gestao

- **Entrada:** a mercado, no fechamento do candle de continuacao (nao antecipar).
- **Stop:** 100 pontos, junto com a entrada.
- **+100:** sai metade; stop do restante na media da operacao (= stop inicial).
- **Alvo:** 300 no restante.
- **Fim do dia:** zera no ultimo candle do pregao. Uma posicao por vez.

## Protocolo de teste

Regras **congeladas** durante o teste.

- **Onde:** simulador, 1 contrato, a partir de 15/09/2026. Toda semana, exportar a base do robo e rodar `python rodar.py && python candidato.py` (bloco "depois").
- **Quanto:** 625 operacoes (~197 pregoes) -- onde um valor real de +10 pts por trade apareceria com t > 2 (desvio medido 125 pts).
- **Confirma:** apos 625 operacoes, valor por trade descontado o custo real > 0 com t >= 2.
- **Abandona:** valor por trade <= 0 depois de 100 operacoes (com a hipotese verdadeira, 12% de chance); rebaixamento > 2.500 pts; mais de 16 perdas seguidas.
- **Inconclusivo:** positivo com t < 2 -- continua ate 1250 operacoes.

## Folha de registro, por operacao

- [ ] Data, hora e lado
- [ ] Candles de retracao (3 ou mais)
- [ ] Hull 50 no sentido e atras do par
- [ ] EMA 21 entre o menor fundo e o maior topo do par
- [ ] Preco de entrada e de saida
- [ ] Motivo da saida
- [ ] Custo real
- [ ] Sinais ignorados por posicao aberta

---

*Gerado por `plano.py`. Base: 50.611 candles, 132 pregoes. Graficos e exemplos em `plano.html`.*