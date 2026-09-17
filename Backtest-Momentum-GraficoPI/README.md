# Backtest -- momentum de continuacao no grafico de 20 PI (WINFUT)

Retracao seguida de candle de continuacao, com **Hull 50**, **EMA 21** e
**canal de Keltner**, no grafico de Pontos de Inversao da Nelogica.
Especificacao original em [CLAUDE.md](CLAUDE.md).

**Base atual:** `WINFUT/WINFUT_20PI_Robo.csv` -- 50.611 candles, 132 pregoes,
06/03 a 14/09/2026. Ela contem inteira a base do primeiro estudo
(`WINFUT_20PI.csv`, 26 pregoes, 06/08 a 11/09), e por isso permite o teste que
faltava: medir as regras nos meses que **nao** participaram da escolha delas.

    python rodar.py && python candidato.py && python relatorio.py && python plano.py
    python pavio_contra.py && python relatorio_pavio.py
    python hull_contra.py && python hull_inclinacao.py && python hull_distancias.py && python relatorio_hull.py
    python osciladores.py && python relatorio_osciladores.py
    python ortogonais.py && python relatorio_ortogonais.py
    python volume_agressor.py && python relatorio_volume.py
    python saldo_agressor.py && python relatorio_saldo.py

(`WINFUT_BASE=WINFUT_20PI.csv python rodar.py` roda de novo sobre a base antiga.)

| Saida | O que e |
|:---|:---|
| **`relatorio.html`** / [`RESULTADOS.md`](RESULTADOS.md) | o estudo principal: estatisticas no padrao MT5, **fora da amostra**, curvas de patrimonio, MEP/MEN, duracao, cada filtro medido, grade stop x alvo, a entrada antecipada, a hipotese da retracao profunda e o **grafico trade a trade** (Kline Charts). |
| **`plano.html`** / [`PLANO.md`](PLANO.md) | o plano anterior **suspenso** e o protocolo de teste em simulador da unica hipotese que sobrou. |
| **`hull_contra.html`** / [`HULL_CONTRA.md`](HULL_CONTRA.md) | Hull a favor + 2 a 4 candles contra ela, com inclinacao e distancias da Hull. Plano provisorio em `plano_hull.html` / [`PLANO_HULL.md`](PLANO_HULL.md). |
| **`pavio_contra.html`** / [`PAVIO_CONTRA.md`](PAVIO_CONTRA.md) | o indicador magenta: os pavios fazem sentido? |
| **`osciladores.html`** / [`OSCILADORES.md`](OSCILADORES.md) | MACD, estocastico lento e IFR como filtro do Hull + pavios: 16 regras, busca contra ruido, escolha fora da amostra, vizinhanca de parametros e trade a trade com os osciladores. Resposta: nenhum passa. |
| **`ortogonais.html`** / [`ORTOGONAIS.md`](ORTOGONAIS.md) | filtros ortogonais a Hull: velocidade (ritmo de candles), horario e posicao no dia (VWAP e abertura), com a ortogonalidade medida. Nenhum passa no controle; o horario (nao operar antes das 10h) e o candidato mais consistente. |
| **`volume_agressor.html`** / [`VOLUME_AGRESSOR.md`](VOLUME_AGRESSOR.md) | volume agressor (compra + venda) como filtro do Hull + pavios: nivel das ultimas 1/2/3/5 barras, variacao % com lag, variacao contra a media; 66 filtros com busca contra ruido. Resposta: nao. |
| **`saldo_agressor.html`** / [`SALDO_AGRESSOR.md`](SALDO_AGRESSOR.md) | saldo de agressao (compra - venda, no sentido do trade): saldo do sinal, lag 1 e 2, soma das ultimas barras, variacao % e contra a media; 72 filtros. Resposta: nao -- o sinal do saldo no par e imposto pelo candle de PI. |
| [`ESTRATEGIA.md`](ESTRATEGIA.md) | a especificacao do que o codigo faz e por que. |
| `periodos.py` | os blocos antes / janela original / depois do teste fora da amostra. |
| `candidato.py` | a hipotese da retracao de 3+ candles, com controle de busca em dados embaralhados. |
| `ntsl/`, `Robo-NTSL/` | indicadores e robo para o Profit; `valida_ntsl.py` e `valida_robo.py` conferem a traducao contra a engine. |
| `saida/` | trade a trade em csv, os json que os relatorios consomem e o console de cada estudo. |

## O resultado, em cinco linhas

| Recorte (fechamento, 1:3 com parcial) | Antes (06/03 a 05/08) | Janela original (06/08 a 11/09) | Base inteira |
|:---|---:|---:|---:|
| **Ouro** | **-7,4** pts/sinal (678) | +34,8 (181) | +1,6 |
| Prata | -0,7 (1.016) | +28,3 (258) | +5,1 |
| Bronze (regra do CLAUDE.md) | -0,2 (2.819) | +11,4 (679) | +1,7 |
| Hull a favor + 2 a 4 contra (hull_contra) | **+6,5** (3.686) | +11,3 (958) | +7,5 |
| Retracao de 3+ candles (hipotese) | +15,3 (334) | +14,8 (81) | +15,0 |

Pontos do WINFUT por sinal, brutos, um contrato; entre parenteses, sinais.

1. **O padrao Ouro nao sobreviveu.** Os filtros que o criaram (veto de exaustao,
   retracao de 2+ candles, pavio 25-90) descreviam agosto e setembro de 2026. Na
   base inteira ele nao paga 2 pontos de custo. **Nao operar Ouro nem Prata e nao
   ligar o robo em conta real.**
2. **A Hull 50 a favor e real, e pequena.** Era hipotese previa e passou fora da
   amostra, sem mes negativo, mas com ~33 operacoes por pregao e +7,5 pts brutos o
   custo real decide se existe setup.
3. **O pavio magenta segue reprovado** -- agora abaixo do acaso (percentil 2 a 8).
4. **A entrada antecipada so parece boa por convencao.** Em 33% dos trades o
   resultado depende da ordem dos precos dentro do candle; com um caminho aleatorio
   o valor vai a zero. Precisa de dado intra-candle.
5. **A retracao profunda** (3+ candles) mede bem nos dois blocos e nos tres tercos,
   mas foi achada olhando esta base e nao passa no controle de busca ampla (p = 0,17).
   E hipotese, com protocolo de teste em `PLANO.md`.

## Os limites, sem rodeio

Um instrumento, um contrato, resultados **brutos**, sem slippage. Caminho dentro do
candle por convencao (OHLC). A base do robo nao tem segundos (duracao dos trades em
resolucao de minuto), nem volume total e numero de negocios (o estudo de fluxo usa o
volume agressor). Ver RESULTADOS.md secao 10.
