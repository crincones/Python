# Backtest -- momentum de continuacao no grafico de 20 PI (WINFUT)

Retracao seguida de candle de continuacao, com **Hull 50**, **EMA 21** e
**canal de Keltner**, no grafico de Pontos de Inversao da Nelogica.
Especificacao original em [CLAUDE.md](CLAUDE.md).

    python rodar.py && python relatorio.py && python plano.py

| Saida | O que e |
|:---|:---|
| **`relatorio.html`** | o relatorio completo: estatisticas no padrao MT5, **galeria de exemplos** dos tres padroes, curvas de patrimonio, MEP/MEN, duracao, cada filtro medido, grade stop x alvo, risco:retorno, robustez e **grafico trade a trade** com filtros de padrao, entrada e gestao. Abre offline, num arquivo so. |
| **`plano.html`** / [`PLANO.md`](PLANO.md) | o plano operacional: seis perguntas de sim ou nao, os tres niveis, e a galeria do Ouro para decorar a forma. |
| [`RESULTADOS.md`](RESULTADOS.md) | os mesmos numeros do relatorio, em texto. |
| [`ESTRATEGIA.md`](ESTRATEGIA.md) | a especificacao do que o codigo faz, e por que cada decisao de medicao foi tomada assim. |
| **`ntsl/MomentumPI_OuroPrata.ntsl`** | o indicador para o ProfitChart: seta abaixo da minima (compra) ou acima da maxima (venda), em ambar no padrao **Ouro** e prata no **Prata**, com regra de coloracao opcional. Conferido barra a barra contra a engine por `ntsl/valida_ntsl.py`. |
| **`estudo_fluxo.py`** | a pergunta "agressao e forca de tendencia melhoram a filtragem?", com controle de busca: permutacao, fora-da-amostra e analise de poder. Resposta medida: **nao, nesta base**. |
| **`esforco.py`** | esforco x resultado no PI: por que metade da pergunta ja estava respondida pelo filtro de pavio, e por que a outra metade nao mede nada. |
| `saida/` | trade a trade em csv, `resumo.json` e o console da ultima rodada. |

## O resultado, em quatro linhas

A regra do CLAUDE.md, medida **exatamente como esta escrita**, ja mede
positivo: **+12.7 pontos por trade** em 569 operacoes.
Tres filtros levam isso a **+34.1 pontos por trade** em
170 operacoes -- o **padrao Ouro** --, com acerto de
36.5%, fator de lucro 1.89 e rebaixamento
maximo de 800 pontos. Monte Carlo: probabilidade de lucro
100.0%.

| Nivel | Trades | Pontos | Por trade | Acerto | Fator | Rebaix. |
|:---|---:|---:|---:|---:|---:|---:|
| **Ouro** | 170 | +5,800 | +34.1 | 36.5% | 1.89 | 800 |
| Prata | 243 | +6,800 | +28.0 | 34.2% | 1.70 | 600 |
| Bronze | 569 | +7,200 | +12.7 | 29.3% | 1.28 | 1700 |

Entrada no fechamento, 1:3 com parcial. Pontos do WINFUT, brutos, um contrato.

## Os seis achados que valem a leitura

1. **A concavidade da Hull mede ao contrario do esperado.** O CLAUDE.md
   pede a Hull "preferivelmente concava". Sozinha, a metade concava rende
   +8.2 pts e a outra
   +18.1 -- nos tres tercos do periodo. O que
   funciona nao e a concavidade, e a **combinacao** dela com o preco
   esticado da EMA, e como **veto**.

2. **O pavio e a unica forma que um candle de PI tem.** Com o corpo fixo em
   100 pontos, nao ha relacao corpo/pavio para estudar. O pavio total tem
   um miolo que paga e duas pontas que nao pagam.

3. **O 1:3 e o 1:2, medidos na diagonal.** Ao mesmo stop de 100, o 1:2 sem
   parcial entrega +24.3 pts por operacao contra
   +44.5 do 1:3 -- quase a metade -- e o que compra com isso
   sao 5.2 pontos percentuais de acerto.
   Nenhuma das 32 celulas da grade e negativa: o setup nao depende de
   acertar a relacao risco:retorno.

4. **Filtros nao se somam.** Empilhar os quatro melhores deixa 16 sinais e
   valor esperado negativo. Os niveis usam tres filtros, nao os oito que
   mediram algo.

5. **Agressao, tempo de barra e forca de tendencia nao filtram nada
   aqui.** Dezessete atributos novos, 170 comparacoes. O melhor filtro do
   Ouro mede t = +3,58; a **mesma busca rodada em dados embaralhados** acha
   t = +4,10 na mediana -- o achado real e pior que o achado tipico em ruido
   puro. Pior: o corte escolhido nos dois primeiros tercos entrega
   **-29 pts** no terceiro, contra +30 sem filtro nenhum. E a favor da
   honestidade do numero, a analise de poder diz que esta base so enxergaria
   um ganho maior que 40 pts por trade -- o "nao" mede o tamanho da amostra,
   nao a inutilidade do fluxo.

6. **Esforco x resultado: o PI ja responde metade de graca.** Como todo
   corpo vale 100 pontos, o resultado esta fixo e o esforco sozinho ja *e*
   a razao. E a leitura geometrica dela, `100/range`, e **exatamente o
   filtro de pavio do Ouro** -- correlacao de posto -1,0000 com `pav_tot`.
   O que sobrava (esforco em volume, negocios e tempo) nao mede: a
   correlacao de posto entre esforco e resultado e -0,07, e o quintil de
   **menor** esforco e o segundo pior.

## Os limites, sem rodeio

26 pregoes (2026-08-06 a 2026-09-11),
um instrumento, um contrato, tudo em mercado de alta. Resultados
**brutos** -- a 10 pontos de custo por operacao a expectativa do Ouro cai
para +24.1 pts. Sem slippage. O caminho dentro do
candle e uma convencao, nao um dado. Ver RESULTADOS.md secao 6.
