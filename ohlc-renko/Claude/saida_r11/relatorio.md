# Estudo preditivo de pontos de virada -- Renko R11 (WINFUT / ProfitChart)

Gerado em 16/08/2026 15:26 | K=4 | min_seq=3 | janela ref=20 bricks do mesmo tipo

## 1. Base e geometria

- bricks: **19999** | pregoes: **35** | 29/06/2026 a 14/08/2026
- corpo constante de **50 pts (10 ticks)** em 100.00% dos bricks
- continuacao abre no close anterior; reversao abre no **open** anterior (confirmado em 94.0% / 96.2%)
- `Data` e o instante de **abertura**; `BarDurationF` esta em **minutos**, quantizado em 0,01 min (0,6 s) -- 18.0% dos bricks marcam 0,00
- bricks descartados (`sujo`): **1002 (5.01%)** -- 883 quebras de encadeamento, 35 viradas de pregao, 420 sem volume, 18 com dur > 60 min

### Reversao e continuacao sao populacoes distintas

| | n | dur (min) | Quantity | Trades | pavio (ticks) | vol s/ agressor |
|---|---|---|---|---|---|---|
| continuacao | 12680 | 0.15 | 14898 | 4588 | 4 | 24.1% |
| reversao | 6317 | 0.53 | 27135 | 8210 | 15 | 27.3% |
| **razao rev/cont** | | **3.53x** | **1.82x** | **1.79x** | **3.75x** | |

E por isso que a janela de referencia so contem bricks do **mesmo tipo**. Comparar um brick de reversao contra uma janela dominada por continuacoes infla a razao por construcao, sem informacao dentro.

### O volume sem agressor

`Quantity - (AgressionVolBuy + AgressionVolSell)` responde por **27.2%** do volume total e correlaciona **+0.55** com `log(Quantity)`. E o negocio direto / RLP, que o ProfitChart nao classifica. Consequencia: `(agb-ags)/Quantity` vem diluido nos bricks grandes. O estudo usa **`(agb-ags)/(agb+ags)`** como delta, e trata a fracao sem agressor como feature separada (`unk_nz`).

## 2. A taxa base -- o numero a bater

| condicao | P(proximo brick na mesma direcao) | n |
|---|---|---|
| qualquer brick | 67.19% | 19998 |
| brick contrario a qualquer sequencia | 65.75% | 6561 |
| brick contrario a seq >= 3 (**elegivel**) | **68.19%** | 2810 |

A pre-condicao inteira vale **+1.00 p.p.** A assimetria vem da mecanica do Renko: reverter custa o corpo do tijolo anterior **mais** o novo (20 ticks), continuar custa so o novo (10). Depois de pagar uma reversao, continuar e mecanicamente duas vezes mais barato. Isso nao e informacao de fluxo.

### Escolha do alvo

Entrada no fechamento do brick elegivel, na direcao dele. Alvo (K-1) corpos a favor, stop 2 corpos contra (= o brick de reversao fechando). Stop testado **antes** do alvo dentro do mesmo brick (pessimista).

| K | alvo (pts) | stop (pts) | breakeven | taxa base | n | expectativa na taxa base |
|---|---|---|---|---|---|---|
| 2 | 50 | 100 | 0.667 | **0.6722** | 2810 | +0.8 pts |
| 3 | 100 | 100 | 0.500 | **0.5356** | 2810 | +7.1 pts |
| 4 | 150 | 100 | 0.400 | **0.4128** | 2810 | +3.2 pts |
| 5 | 200 | 100 | 0.333 | **0.3395** | 2810 | +1.9 pts |
| 6 | 250 | 100 | 0.286 | **0.2979** | 2810 | +4.3 pts |

K=4 e o alvo do estudo: e o mais proximo do breakeven, portanto o que mais depende do modelo, e uma perna de 4 tijolos = 150 pts no WIN.

## 3. Amostra

- elegiveis: **2810** (14.05% dos bricks)
- com janela de referencia completa e rotulo definido: **2797**
- taxa base na amostra: **0.4126**

Split cronologico por pregao: treino 1962 eventos (24 pregoes, ate 30/07), teste 835 eventos (11 pregoes, de 31/07/2026).

## 4. Poder discriminante isolado de cada feature

AUC sobre a amostra inteira. 0,50 = nada. Valor **abaixo** de 0,50 significa que a feature separa com o **sinal invertido** em relacao a intuicao.

| feature | AUC (tudo) | AUC (teste) | |AUC-0,5| |
|---|---|---|---|
| `day_pos` | 0.5222 | 0.5328 | 0.0222 |
| `delta_cl` | 0.5170 | 0.5159 | 0.0170 |
| `hora_dec` | 0.5164 | 0.5264 | 0.0164 |
| `wick_seq` | 0.5162 | 0.5116 | 0.0162 |
| `delta_raw` | 0.5159 | 0.5133 | 0.0159 |
| `pos_rng` | 0.5132 | 0.5486 | 0.0132 |
| `delta_seq` | 0.4870 | 0.5113 | 0.0130 |
| `dur_seq` | 0.5121 | 0.4973 | 0.0121 |
| `trd_nz` | 0.4898 | 0.4856 | 0.0102 |
| `rev_dens` | 0.4901 | 0.5156 | 0.0099 |
| `seq_len` | 0.5096 | 0.4759 | 0.0096 |
| `cost_nz` | 0.4906 | 0.4904 | 0.0094 |
| `pace_nz` | 0.5087 | 0.5192 | 0.0087 |
| `unk_nz` | 0.5080 | 0.5234 | 0.0080 |
| `eff_ratio` | 0.5079 | 0.4852 | 0.0079 |
| `dur_nz` | 0.4928 | 0.4969 | 0.0072 |
| `cost_seq` | 0.5054 | 0.4961 | 0.0054 |
| `wick_net_n` | 0.4947 | 0.4677 | 0.0053 |
| `size_nz` | 0.4971 | 0.4998 | 0.0029 |
| `pace_reg` | 0.4988 | 0.4988 | 0.0012 |

## 5. Modelos

| modelo | AUC teste | log-loss | Brier | exportavel NTSL |
|---|---|---|---|---|
| logistica L2 (C=0.1) | 0.5119 | 0.6821 | 0.2444 | sim |
| logistica L1 (C=0.1) | 0.4992 | 0.6808 | 0.2438 | sim |
| GBM (teto de referencia) | 0.5326 | 0.6853 | 0.2457 | nao |
| *constante = taxa base do treino* | 0.5000 | 0.6772 | 0.2420 | - |

Validacao cruzada temporal (5 dobras expansivas, so no treino): AUC **0.501 +/- 0.036**.

### Coeficientes da logistica L2 (features padronizadas)

intercepto = -0.355530

| feature | coef | AUC isolada | leitura |
|---|---|---|---|
| `delta_cl` | +0.2448 | 0.5170 | valor alto -> **mais** chance de perna |
| `delta_raw` | -0.1263 | 0.5159 | valor alto -> **menos** chance de perna |
| `dur_nz` | -0.0930 | 0.4928 | valor alto -> **menos** chance de perna |
| `wick_net_n` | +0.0867 | 0.4947 | valor alto -> **mais** chance de perna |
| `day_pos` | +0.0811 | 0.5222 | valor alto -> **mais** chance de perna |
| `seq_len` | +0.0802 | 0.5096 | valor alto -> **mais** chance de perna |
| `rev_dens` | -0.0766 | 0.4901 | valor alto -> **menos** chance de perna |
| `dur_seq` | +0.0759 | 0.5121 | valor alto -> **mais** chance de perna |
| `wick_seq` | +0.0579 | 0.5162 | valor alto -> **mais** chance de perna |
| `pace_nz` | +0.0565 | 0.5087 | valor alto -> **mais** chance de perna |
| `unk_nz` | +0.0499 | 0.5080 | valor alto -> **mais** chance de perna |
| `eff_ratio` | +0.0433 | 0.5079 | valor alto -> **mais** chance de perna |
| `trd_nz` | +0.0417 | 0.4898 | valor alto -> **mais** chance de perna |
| `cost_nz` | +0.0398 | 0.4906 | valor alto -> **mais** chance de perna |
| `pos_rng` | +0.0330 | 0.5132 | valor alto -> **mais** chance de perna |
| `cost_seq` | -0.0272 | 0.5054 | valor alto -> **menos** chance de perna |
| `delta_seq` | -0.0257 | 0.4870 | valor alto -> **menos** chance de perna |
| `size_nz` | +0.0235 | 0.4971 | valor alto -> **mais** chance de perna |
| `pace_reg` | -0.0147 | 0.4988 | valor alto -> **menos** chance de perna |
| `hora_dec` | -0.0097 | 0.5164 | valor alto -> **menos** chance de perna |

## 6. Desempenho por decil do score (out-of-sample)

| decil | n | p media | acerto real | lift | expectativa (pts/trade) |
|---|---|---|---|---|---|
| 1 | 84 | 0.328 | 0.429 | 1.04x | +7.1 |
| 2 | 83 | 0.361 | 0.301 | 0.73x | -24.7 |
| 3 | 84 | 0.378 | 0.440 | 1.07x | +10.1 |
| 4 | 83 | 0.393 | 0.422 | 1.03x | +5.4 |
| 5 | 84 | 0.406 | 0.429 | 1.04x | +7.1 |
| 6 | 83 | 0.420 | 0.337 | 0.82x | -15.7 |
| 7 | 83 | 0.434 | 0.398 | 0.97x | -0.6 |
| 8 | 84 | 0.451 | 0.583 | 1.42x | +45.8 |
| 9 | 83 | 0.471 | 0.361 | 0.88x | -9.6 |
| 10 | 84 | 0.515 | 0.405 | 0.99x | +1.2 |

## 7. Escolha do limiar (out-of-sample)

| p >= | z >= | sinais | por pregao | acerto | lift | pts/trade | pts totais |
|---|---|---|---|---|---|---|---|
| 0.300 | -0.8473 | 826 | 75.1 | 0.413 | 1.01x | +3.2 | +2650 |
| 0.325 | -0.7309 | 812 | 73.8 | 0.411 | 1.00x | +2.8 | +2300 |
| 0.350 | -0.6190 | 760 | 69.1 | 0.411 | 1.00x | +2.6 | +2000 |
| 0.375 | -0.5108 | 645 | 58.6 | 0.426 | 1.04x | +6.6 | +4250 |
| 0.400 | -0.4055 | 491 | 44.6 | 0.413 | 1.01x | +3.4 | +1650 |
| 0.425 | -0.3023 | 344 | 31.3 | 0.436 | 1.06x | +9.0 | +3100 |
| 0.450 | -0.2007 | 208 | 18.9 | 0.409 | 0.99x | +2.2 | +450 |
| 0.475 | -0.1001 | 111 | 10.1 | 0.387 | 0.94x | -3.2 | -350 |
| 0.500 | +0.0000 | 50 | 4.5 | 0.300 | 0.73x | -25.0 | -1250 |
| 0.525 | +0.1001 | 20 | 1.8 | 0.350 | 0.85x | -12.5 | -250 |
| 0.550 | +0.2007 | 11 | 1.0 | 0.455 | 1.11x | +13.6 | +150 |

