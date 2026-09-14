# Backtest-Rincones1-DTA

Backtest de um operacional de **esforço filtrado por Hull, EMA e canal de Keltner**
no WIN, sobre barras de **10.000 ticks** (WINV26 e WINFUT, abr–ago/2026).

Mesma carcaça do [Backtest-Rincones1](../Backtest-Rincones1) — carga, gatilho,
execução e gestão —, com **outra leitura de contexto**. O gatilho é o indicador
`ProfitChart/Indicadores/Grafico-Ticks/Ticks_Esforco_Hist_v2.ntsl` com as
**configurações padrão dele**; o que muda é o que decide se aquele sinal vira
trade e para que lado.

> **A medição contrariou a hipótese de partida, e o operacional seguiu a
> medição.** A ideia era comprar com a Hull subindo e o preço acima dela, vender
> com a Hull descendo e o preço abaixo. Isso mede **negativo ou neutro** nas duas
> bases, em todos os níveis do gatilho e nos dois stops. O que mede é o
> **contrário**: entrar do lado *oposto* ao da Hull, com ela inclinada. A
> derivação, com as tabelas, está na **§ 3 de [RESULTADOS.md](RESULTADOS.md)**.

## Conteúdo

| Arquivo | O que é |
|---|---|
| **[PLANO.md](PLANO.md)** · **[plano.html](plano.html)** | **O plano operacional manual.** O que fazer na frente da tela, a tabela de conversão do ATR para o stop, os limites do dia e a nota de aderência. **Gerado.** |
| [ESTRATEGIA.md](ESTRATEGIA.md) | Especificação formal: gatilho, contexto, os quatro setups, execução e gestão. É o contrato que a engine implementa. |
| **[relatorio.html](relatorio.html)** | **O relatório.** A medição inteira, com o **visualizador de trades** — candles, EMA, Hull, canal, gatilho e desfecho, navegável trade a trade. Arquivo único, abre offline. |
| [RESULTADOS.md](RESULTADOS.md) | Os mesmos números em markdown. **Gerado** — não edite à mão. |
| `engine.py` | Motor: carga, indicador de esforço, contexto (EMA/Hull/Keltner/ATR), os 4 setups, simulação de trade, métricas. |
| `rodar.py` | Roda tudo e grava `saida/`. |
| `relatorio.py` + `molde.py` + `resultados_md.py` | Geram `relatorio.html` e `RESULTADOS.md` a partir de `saida/resumo.json`. |
| `plano.py` + `molde_plano.py` | Geram `PLANO.md` e `plano.html` — do mesmo `resumo.json`, e o HTML sai do próprio markdown. |
| `vendor/` | [KLineCharts](https://klinecharts.com) 9.8.10 (Apache 2.0), embutido no HTML pelo `relatorio.py`. Única dependência de front-end, e não vai a CDN. |
| `dados/` | Os dois CSV de 10.000 ticks exportados do Profit. |
| `saida/` | `resumo.json` (fonte única dos números), `console.txt` e `trades_*.csv`. |

## Como rodar

```bash
python rodar.py       # mede tudo -> saida/resumo.json
python relatorio.py   # gera relatorio.html e RESULTADOS.md
python plano.py       # gera PLANO.md e plano.html
```

Requer `numpy` e `pandas`. Tudo é configurável no topo de `engine.py` — mexeu
ali, rode os três de novo.

> **Nenhum número é escrito à mão nos documentos gerados.** Relatório, markdown
> e plano saem todos de `saida/resumo.json`, e até as frases de conclusão são
> calculadas a partir dele.

## As três peças

- **EMA 21 — tendência e régua.** Linha do meio do canal e origem de todas as
  distâncias. A profundidade do mergulho a partir dela limita o setup principal.
- **Hull 50 — intensidade, e lado.** Faz duas coisas, e as duas medem. *Veto:*
  Hull plana é o pior contexto dos dois arquivos — sem intensidade, o gatilho não
  paga. *Lado:* o trade entra do lado **oposto** ao que o preço ocupa em relação
  a ela.
- **Keltner 2–3 ATR — esticamento.** Mede onde o preço está esticado. Não veta
  nada que a Hull já não vete, e a reversão na banda — o uso de manual — mede
  negativo. Sobra dele o aviso: **onde o preço está esticado, este operacional
  não opera.**

## Os quatro setups

Mesmo gatilho. O que muda é o contexto que o valida.

- **D — descolamento da Hull.** *Principal.* Close do lado oposto ao da Hull,
  Hull inclinada, preço dentro do canal, mergulho de no máximo 1,5 ATR.
- **T — tendência com força.** *Ativo.* A leitura clássica, restrita ao pullback:
  Hull e EMA no sentido do trade, close do lado certo da Hull, preço ainda não
  esticado. Raro, e positivo.
- **K — rejeição da banda.** *Desligado.* Pavio fora da banda de 2 ATR,
  fechamento de volta para dentro. Mede positivo sozinho e mesmo assim piora a
  carteira: só há uma posição por vez, e ele ocupa a vaga de um trade melhor.
- **KB — banda clássica.** *Desligado.* Preço esticado, entrada contra. Mede
  negativo no WINFUT em toda configuração testada.

**Gestão:** stop de **0,75 × ATR** da barra do sinal · parcial de 50% na mesma
distância do stop · alvo de 300 pontos. Quando a parcial sai, o stop do restante
fica na média da operação — que, com meia posição, é o próprio stop inicial. O
stop não anda, e o trade que volta morre em **zero de verdade**.

**Entrada:** ordem limitada no meio do candle do gatilho, válida por **uma
barra**. Não preencheu na barra seguinte, o trade é abortado. Cerca de um sinal
em cinco morre assim, e todo número deste projeto já está sob essa regra.

## As respostas

> As frases de conclusão do relatório e do markdown são **calculadas** a partir
> de `saida/resumo.json`. As de baixo são o resumo desta rodada; se a engine
> mudar, valem as dos documentos gerados, não estas.

1. **A leitura clássica da Hull está invertida para este gatilho.** Com a Hull
   inclinada, entrar do lado *oposto* mede +50,3 por trade no WINV26 e +21,6 no
   WINFUT; do lado *clássico*, +2,5 e +9,1. O gatilho é um sinal de falha, não de
   continuação — entrar "a favor do movimento" é entrar do lado de quem acabou de
   falhar.
2. **O veto da Hull plana é a regra mais forte do projeto.** É o pior balde dos
   dois arquivos (−62,3 e −35,1 pontos por trade). Sem intensidade no movimento,
   não há nada para se desfazer.
3. **O canal de Keltner mede o que NÃO fazer.** O veto de zona é *inerte* — a
   regra da Hull já exclui a banda — e a reversão na banda mede negativo no
   WINFUT. A faixa de 2 a 3 ATR, que era a aposta inicial, é onde o operacional
   não opera.
4. **O nível do gatilho é o parâmetro mais forte.** No corte de cor do indicador
   (0,55) a carteira mede +25,8 / +8,4 por trade com ~16 trades por pregão; em
   0,80, +58,4 / +32,8 com ~5. A vantagem cresce com o nível em todas as células
   das duas bases.
5. **O stop de 150 herdado é largo demais.** Medido em R — a única forma de
   comparar stops diferentes —, 0,75 × ATR (≈ 95 pontos) mede melhor nas duas
   bases e corta o rebaixamento pela metade.
6. **A troca do eixo [E2] do indicador não ajuda aqui.** A fórmula antiga mede
   igual ou melhor neste operacional; fica a do indicador porque é o padrão dele
   e a diferença está dentro do ruído. O ganho medido no Rincones1 não se repete.

Leia a **§ 14 de [RESULTADOS.md](RESULTADOS.md)** antes de dimensionar posição —
a amostra é de dois meses, as regras saíram destes mesmos dados e o preenchimento
da limitada é otimista.

## O visualizador

Está dentro do relatório, na seção 13. Navega **trade a trade** (setas ← →, ou
clique na lista): candles do pregão, EMA 21, Hull 50, as bandas de 2 ATR, linhas
de entrada/stop/parcial/alvo, marcas do gatilho, do preenchimento e da saída, o
índice de esforço embaixo com a linha de corte, e ficha com `dh`, `de`, desfecho
e R$ por contrato. Filtros por base, **gestão** (as cinco variantes de stop e
alvo — os sinais são os mesmos, muda onde o trade morre), setup (inclusive os
desligados, para ver por que falham), **lado da Hull** e desfecho.
