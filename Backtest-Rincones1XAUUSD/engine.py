# -*- coding: utf-8 -*-
"""
Engine de backtest - Rincones1 XAUUSD (ouro, grafico de 521 ticks)

E o porte de Python/Backtest-Rincones1 (WIN, 10.000 ticks) para o ouro. A
ESTRUTURA e a mesma -- mesmo gatilho de esforco, mesmos tres setups
separados por regime de media, mesma gestao de parcial e stop, mesma regra
da barra seguinte. O que muda esta todo documentado em ESTRATEGIA.md 1 e
resumido aqui:

  [X1] O ATIVO NAO PUBLICA VOLUME POR NEGOCIO. O XAUUSD e CFD: o gerador
       de barras conta 1 lote por tick, entao V_buy + V_sell == T em
       99,75% das barras. O eixo [E1] do indice e uma CONSTANTE, o
       percentil dele da 0,000 em toda barra, e um indice de tres eixos
       que o inclua fica preso abaixo de 0,667 -- com corte em 0,80, nao
       acende nunca. O indicador() detecta eixo sem variacao e o tira da
       soma, renormalizando os pesos. E a mesma defesa do [D1] de
       Ticks_Esforco_v2.mqh.

  [X2] O DELTA AQUI NAO E O DELTA DA B3. Na B3 a bolsa publica a flag de
       agressor; no ouro ela e INFERIDA pela tick rule, e o delta
       resultante concorda com o sinal do proprio candle em so 63,2% das
       barras. Nao e a mesma variavel. Medido, a leitura util e a do
       CANDLE, nao a do delta -- ver ESTRATEGIA.md 2 e RESULTADOS.md 3.
       Dai REFERENCIA.

  [X3] ENTROU O EIXO [E4] RANGE. Ele nao existe no backtest do WIN. No
       ouro e o eixo que mais mede sozinho, e sem ele so sobrariam dois.

  [X4] AS DISTANCIAS SAO EM USD, E FORAM ESCALADAS PELO RANGE MEDIO. O
       WIN usa stop 150 com range medio de 20 barras de ~127 pontos, ou
       seja 1,18 range medio. O ouro tem range medio de 2,98 USD, entao
       1,18 range medio = 3,50 USD. Todos os cortes do CONTEXTO (leque,
       toque, afastamento) ja eram normalizados pelo range medio no
       projeto do WIN e atravessaram sem mudanca.

O eixo [E2] e o VAIVEM do Ticks_Esforco_Hist_v2.ntsl / Ticks_Esforco_v2.mqh:
(|delta|/esforco) x (1 - |C-O|/percurso), com percurso = 2*(H-L) - |C-O|.
Para voltar a formula antiga: METRICA_E2 = 0.
"""
import os

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(BASE, 'dados')

CSV = os.path.join(DADOS, 'XAUUSD_521_TK_M1_202605040103_202608282354.csv')

# As tres "bases" do relatorio. NAO sao tres instrumentos: sao a amostra
# inteira e as duas metades CRONOLOGICAS dela. No projeto do WIN havia dois
# contratos independentes e a pergunta era "mede nos dois?"; aqui so ha um
# historico, e a mesma pergunta vira "mede nas duas metades?". E uma
# evidencia MAIS FRACA, e o relatorio diz isso onde importa.
BASES = ('COMPLETO', 'METADE_1', 'METADE_2')

# ---------------------------------------------------------------- parametros
TICK = 0.01            # tick do XAUUSD, em USD
VAL_PONTO = 100.0      # USD por 1,00 USD de movimento, contrato de 100 oz
                       # (1 lote padrao). Para 0,01 lote, divida por 100.

# --- gestao
#
# [X5] O STOP EQUIVALENTE AO DO WIN NAO E O MELHOR AQUI. Escalar o stop de
#      150 pontos do WIN pelo range medio da barra da 3,50 USD, e esse valor
#      mede POSITIVO -- mas o dobro dele mede muito melhor, nas duas metades
#      e em toda a linha de alvos (RESULTADOS.md 6). O motivo esta na forma
#      do sinal: a barra do gatilho e, por construcao, uma barra de range
#      EXTREMO (percentil >= 0,90 do range), e o stop tem de caber fora
#      dela. Um stop de 1,17 range medio cabe DENTRO da propria barra que
#      disparou o trade. No WIN o gatilho nao era o range, entao a barra do
#      sinal nao era grande e o problema nao aparecia.
STOP = 7.00            # stop inicial, em USD  (~2,35 range medio)
PARCIAL_EM = None      # onde sai a parcial | None = na MESMA distancia do stop
FRAC_PARCIAL = 0.50    # fracao da posicao vendida na parcial
ALVO = 10.50           # alvo do restante    (1,5x o stop)
CUSTO_PTS = 0.0        # custo de ida e volta em USD (0 = bruto). O spread
                       # tipico do XAUUSD e de 0,20 a 0,40 -- ver
                       # RESULTADOS.md 8 antes de dimensionar posicao.

# Onde fica o stop do RESTANTE depois que a parcial sai. Identico ao WIN.
#
#   'media'    na MEDIA DA OPERACAO: o preco em que o que ja foi realizado
#              na parcial cancela exatamente a perda do restante. Com meia
#              posicao e a parcial na distancia do stop, esse preco E o
#              stop inicial: o stop nao anda, e o desfecho 'zero' e zero.
#   'entrada'  no preco de ENTRADA. Otimista -- o desfecho 'zero' pagaria
#              FRAC_PARCIAL x parcial e ainda se chamaria zero a zero.
#              Fica so para reproduzir o modelo antigo.
STOP_APOS_PARCIAL = 'media'

# --- gatilho de esforco
PERIODO_REF = 20       # janela do percentil, em barras validas
PISO_DUR_MS = 1.0      # duracao zero vira velocidade maxima
METRICA_E2 = 2         # qual formula alimenta o eixo [E2]:
                       #   2 = (|delta|/esforco) * (1 - |C-O|/percurso) <- v2
                       #   0 = |delta| / |C-O|                          <- v1
                       #   1 = esforco / range                          <- v1 variante
                       #   3 = |delta| * volta   |  4 = volta pura
                       # ver Ticks_Esforco_v2.mqh

# Quais eixos entram no indice.
#
# [X6] O INDICE DO OURO E DE UM EIXO SO. Medido, [E4] sozinho mede melhor
#      que qualquer combinacao (RESULTADOS.md 4). [E1] esta fora porque o
#      ativo nao o publica [X1] -- e ele fica LIGADO na lista abaixo de
#      proposito, para que quem o derrube seja a medicao de degenerescencia
#      e nao uma opcao do usuario: assim o mesmo arquivo roda num ativo que
#      publique volume de verdade sem nenhuma edicao.
EIXOS = ('E4',)
MIN_VARIACAO = 0.10    # [X1] fracao minima de barras em que o eixo precisa
                       # MUDAR de valor para entrar na soma

NIVEL_MIN = 0.90       # indice minimo para o gatilho
REFERENCIA = 'candle'  # [X2] 'candle' | 'delta' -- de quem e a direcao lida

# [X7] A GEOMETRIA DE REJEICAO E INVERTIDA NO OURO. A regra do WIN e a
#      CLASSICA: candle de alta com o corpo na metade de BAIXO do range
#      (pavio superior grande, exaustao) e se vende. No ouro isso mede
#      NEGATIVO; quem mede e o lado oposto -- candle de alta com o corpo em
#      CIMA, pavio inferior grande, e se vende. Nao e achado novo: o
#      Delta_Fraqueza.mqh e o [D4] de Ticks_Esforco_v2.mqh ja tinham
#      registrado a mesma inversao em dois outros graficos sinteticos do
#      mesmo ativo. Ver RESULTADOS.md 5.
GEOMETRIA = 'inversa'  # 'off' | 'corpo' | 'classica' | 'inversa'
CORTE_POSICAO = 60.0   # posicao do meio do corpo dentro do range, em %
CORPO_MAX = 50.0       # corpo/range maximo, em %
DESCARTA_E2 = False    # descarta barras em que [E2] e o eixo dominante. No
                       # WIN era True; aqui e INERTE, porque [E2] nao entra
                       # no indice [X6]. Volta a valer se EIXOS mudar.

# --- medias e regimes -- os cortes sao em RANGES MEDIOS, entao atravessaram
#     do WIN sem mudanca [X4]
REGIME_MA = 'ema3'     # 'ema3' | 'kama' | 'hma' | 't3' | 'jma'
MA_PER = 21            # periodo da media unica (nao usado no ema3)
MA_SLOPE = 5           # barras do lookback da inclinacao (nao usado no ema3)
INCL_MIN = 0.25        # media unica: |inclinacao|/rangeMedio para "tendencia"
INCL_CONSOL = 0.12     # media unica: abaixo disso e consolidacao
EMA_R, EMA_M, EMA_L = 21, 42, 72
PERIODO_RANGE = 20     # janela do range medio (unidade de todas as distancias)
LEQUE_MIN = 0.30       # setup A: (EMA21-EMA72)/rangeMedio minimo
TOL_TOQUE = 1.00       # setup A: tolerancia do toque na media, em ranges medios
CONSOL_MAX = 0.35      # setup C: (EMA21-EMA72)/rangeMedio abaixo disso
AFAST_MIN_B = 1.00     # setup B: |Close-EMA21|/rangeMedio minimo
AFAST_MIN_C = 0.80     # setup C: |Close-EMA21|/rangeMedio minimo
VEL_MIN_B = 0.00       # setup B: percentil de velocidade minimo (inerte)

# --- execucao
#
# [X8] A ORDEM LIMITADA NO MEIO DO CANDLE NAO SOBREVIVE A INVERSAO DA
#      GEOMETRIA, e essa e a diferenca de execucao mais cara do porte. No
#      WIN a geometria e CLASSICA: numa barra de alta o corpo esta EMBAIXO,
#      entao o meio do candle fica ACIMA do fechamento e uma venda limitada
#      ali e um preco MELHOR -- espera-se um repique para vender mais caro.
#      Com a geometria INVERSA o corpo esta EM CIMA, o meio do candle fica
#      ABAIXO do fechamento, e a mesma ordem vira um preco PIOR: vende-se
#      meio range abaixo de onde daria para vender a mercado, e a ordem
#      preenche quase sempre, porque o preco ja esta acima dela. Medido, a
#      regra tira ~1,8 USD por trade e inverte o sinal do resultado
#      (RESULTADOS.md 7). Por isso o default aqui e A MERCADO.
ENTRADA = 'fecha'      # 'fecha' = a mercado no fechamento | 'meio' = limitada
MAX_BARRAS_FILL = 1    # A REGRA DA BARRA SEGUINTE, so vale para 'meio': a
                       # limitada vale por UMA barra. 99999 = ate o fim do
                       # pregao.

# 'L' (livre) e o sinal que nenhum regime reivindicou. Ele existe porque,
# medido, o filtro de regime SUBTRAI neste ativo: a carteira que pega todo
# gatilho mede melhor que qualquer subconjunto A/B/C, e nas duas metades
# (RESULTADOS.md 9). Manter as tres marcas mesmo assim e o que permite
# QUEBRAR o resultado por regime no relatorio em vez de so afirmar isso.
PRIORIDADE = ('A', 'B', 'C', 'L')
SETUPS_ATIVOS = ('A', 'B', 'C', 'L')


# ============================================================ carga de dados
def carrega(caminho=None, base='COMPLETO'):
    """Le a exportacao do MT5 do simbolo sintetico de ticks.

    A convencao dos campos e a [R6] do gerador Ticks_Claude_v1, a mesma que
    Ticks_Esforco_v2.mqh consome:

        <TICKVOL> -> agressao COMPRADORA da barra
        <VOL>     -> agressao VENDEDORA  da barra
        <SPREAD>  -> duracao da barra em MILISSEGUNDOS

    (No WIN o CSV vinha do Profit, separado por tab com virgula decimal e do
    mais NOVO para o mais antigo. Aqui vem do MT5, com ponto decimal e ja em
    ordem cronologica.)

    `base` recorta a amostra: 'COMPLETO', 'METADE_1' ou 'METADE_2'. O corte e
    por PREGAO, nao por barra, para que nenhum pregao apareca partido nas
    duas metades -- as metricas diarias contariam o mesmo dia duas vezes.
    """
    caminho = CSV if caminho is None else caminho
    df = pd.read_csv(caminho, sep='\t')
    df.columns = [c.strip('<>').lower() for c in df.columns]
    df['Data'] = pd.to_datetime(df['date'] + ' ' + df['time'],
                                format='%Y.%m.%d %H:%M:%S')
    df = df.rename(columns={'open': 'O', 'high': 'H', 'low': 'L', 'close': 'C',
                            'tickvol': 'Buy', 'vol': 'Sell', 'spread': 'DurMs'})
    df = df[['Data', 'O', 'H', 'L', 'C', 'Buy', 'Sell', 'DurMs']]
    df = df.sort_values('Data').reset_index(drop=True)
    df['dia'] = df['Data'].dt.date
    df = df[(df.Buy + df.Sell) > 0].reset_index(drop=True)   # barra valida

    if base != 'COMPLETO':
        dias = sorted(df.dia.unique())
        corte = dias[len(dias) // 2]
        df = (df[df.dia < corte] if base == 'METADE_1'
              else df[df.dia >= corte]).reset_index(drop=True)
    return df


ARQUIVOS = {b: CSV for b in BASES}   # a interface que rodar.py espera


# ====================================================== indicador de esforco
def _pct_rank(a, n):
    """Fracao das n barras anteriores (exclui a atual) com valor MENOR.

    Percentil CAUSAL: le so o passado. E o mesmo de CEsforcoTicks::Percentil,
    e conta ESTRITAMENTE menores pela mesma razao -- e o empate que denuncia
    o eixo degenerado [X1].

    Escrito com janela deslizante em vez do laco barra a barra: com 68 mil
    barras e as varreduras do rodar.py, o laco levava minutos.
    """
    a = np.asarray(a, float)
    out = np.full(len(a), np.nan)
    if n <= 0 or len(a) <= n:
        return out
    # janelas a[j:j+n] para j = 0 .. len(a)-1-n; a janela de i = n+j
    jan = np.lib.stride_tricks.sliding_window_view(a[:-1], n)
    out[n:] = (jan < a[n:, None]).sum(axis=1) / n
    return out


def _degenerado(a):
    """[X1] O eixo varia neste ativo?

    Fracao de barras em que o valor MUDOU em relacao a anterior. Nao e
    desvio-padrao de proposito: o que quebra o percentil e o EMPATE, nao a
    dispersao. Um eixo que assume dois valores muito distantes em metade das
    barras cada tem desvio enorme e percentil perfeitamente utilizavel; um
    que vale sempre 521 tem desvio quase zero e percentil sempre 0,000.
    """
    a = np.asarray(a, float)
    if len(a) < 2:
        return False
    return float((np.diff(a) != 0).mean()) < MIN_VARIACAO


def indicador(df):
    """Devolve o dataframe com o indice de esforco e seus quatro eixos."""
    esf = (df.Buy + df.Sell).to_numpy(float)
    dlt = (df.Buy - df.Sell).to_numpy(float)

    adl = np.abs(dlt).copy()
    adl[adl < 1] = 1.0
    res = np.abs(df.C - df.O).to_numpy(float) / TICK
    res[res < 1] = 1.0
    rng_t = (df.H - df.L).to_numpy(float) / TICK
    rng_t[rng_t < 1] = 1.0
    dur = df.DurMs.to_numpy(float).copy()
    dur[dur < PISO_DUR_MS] = PISO_DUR_MS

    # PERCURSO MINIMO compativel com o OHLC: a ida E a volta.
    # |C-O| e o saldo e H-L e a maior distancia alcancada; nenhum dos dois
    # ve o caminho. 2*range - corpo e o menor caminho que passa pelos dois
    # extremos e termina no fechamento. Piso em res: com H=L nao houve
    # caminho, entao nao houve vaivem.
    perc = (2.0 * (df.H - df.L).to_numpy(float)
            - np.abs(df.C - df.O).to_numpy(float)) / TICK
    perc = np.maximum(perc, res)
    volta = 1.0 - res / perc                      # fracao do caminho desfeita
    desq = np.where(esf < 1, 0.0, adl / np.maximum(esf, 1e-12))

    m_e2 = {0: adl / res,                         # v1
            1: esf / rng_t,                       # v1, variante
            2: desq * volta,                      # v2  <- default
            3: adl * volta,
            4: volta}[METRICA_E2]

    cru = {'E1': esf, 'E2': m_e2, 'E3': 1.0 / dur, 'E4': rng_t}
    pct = {k: _pct_rank(v, PERIODO_REF) for k, v in cru.items()}

    d = df.copy()
    for k in ('E1', 'E2', 'E3', 'E4'):
        d['p' + k] = pct[k]
        # a fracao de barras em que o eixo MUDOU: e o que decide se ele
        # entra no indice [X1], e o relatorio publica o numero
        d.attrs['muda_' + k] = float((np.diff(cru[k]) != 0).mean())
        d.attrs['degen_' + k] = _degenerado(cru[k])
    d['volta'] = volta
    d['dlt'] = dlt
    d['dirDelta'] = np.where(dlt > 0, 1, np.where(dlt < 0, -1, 0))

    O, H, L, C = (df[c].to_numpy(float) for c in ('O', 'H', 'L', 'C'))
    d['dirCandle'] = np.where(C > O, 1, np.where(C < O, -1, 0))
    rng = (H - L).copy()
    rng[rng <= 0] = TICK
    d['posMediaCorpo'] = ((O + C) / 2.0 - L) / rng * 100.0
    d['porcCorpoWick'] = np.abs(C - O) / rng * 100.0
    d['rangeOk'] = (H - L) > 0
    return combina(d)


def combina(d):
    """Monta o indice a partir dos percentis ja calculados e de EIXOS.

    Esta separada de indicador() porque o percentil e a parte cara e NAO
    depende de EIXOS: as varreduras do rodar.py trocam o conjunto de eixos
    dezenas de vezes sobre os mesmos percentis.
    """
    # [X1] eixo que este ativo nao publica sai da soma E do divisor. Deixa-lo
    # entrar valendo 0,000 nao seria "esforco minimo": seria um teto
    # artificial no indice, e foi exatamente o que impediria o gatilho de
    # acender no ouro.
    vivos = [k for k in EIXOS if not d.attrs.get('degen_' + k, False)]
    mortos = [k for k in EIXOS if k not in vivos]

    d = d.copy()
    d['idx'] = (np.nanmean(np.vstack([d['p' + k].to_numpy() for k in vivos]),
                           axis=0)
                if vivos else np.full(len(d), np.nan))
    d.attrs['eixos_vivos'] = vivos
    d.attrs['eixos_mortos'] = mortos

    # [E2] e o eixo dominante nesta barra? So faz sentido entre os VIVOS.
    outros = [k for k in vivos if k != 'E2']
    d['e2Manda'] = (np.all(np.vstack([d.pE2.to_numpy() >= d['p' + k].to_numpy()
                                      for k in outros]), axis=0)
                    if ('E2' in vivos and outros) else np.zeros(len(d), bool))
    return d


def gatilho(d, referencia=None, geometria=None):
    """Sinal do indice de esforco: +1 compra, -1 venda, 0 nada.

    A leitura e sempre CONTRA a direcao de referencia da barra: esforco
    grande que nao paga e absorcao, e absorcao se desfaz.

    [X2] `referencia` decide de quem e essa direcao. No WIN e o DELTA, que a
    B3 publica. No ouro o delta vem da tick rule e nao mede -- ali a direcao
    util e a do proprio CANDLE.

    `geometria` e o filtro de forma da barra:
        off       so o esforco decide
        corpo     so exige corpo pequeno em relacao ao range
        classica  corpo pequeno E do lado da rejeicao classica (referencia
                  de alta com o corpo na metade de BAIXO do range: subiu
                  dentro da barra e voltou). E a regra do NTSL.
        inversa   corpo pequeno E do lado OPOSTO. Mede MAIS no ouro -- ver
                  RESULTADOS.md 5 e o [D4] de Ticks_Esforco_v2.mqh.
    """
    ref = REFERENCIA if referencia is None else referencia
    geo = GEOMETRIA if geometria is None else geometria

    dirRef = d.dirDelta.to_numpy() if ref == 'delta' else d.dirCandle.to_numpy()
    # doji exato (ou delta zero) nao tem lado; conta como comprador, para que
    # as duas referencias tenham sempre um lado, como no .mqh.
    dirRef = np.where(dirRef == 0, 1, dirRef)

    idx = d.idx.to_numpy()
    ok = (idx >= NIVEL_MIN) & ~np.isnan(idx)

    if geo != 'off':
        ok &= d.rangeOk.to_numpy()        # range zero: geometria indefinida
        ok &= d.porcCorpoWick.to_numpy() <= CORPO_MAX
    if geo in ('classica', 'inversa'):
        pos = d.posMediaCorpo.to_numpy()
        espelho = 100.0 - CORTE_POSICAO
        if geo == 'classica':
            ok &= np.where(dirRef >= 0, pos <= espelho, pos >= CORTE_POSICAO)
        else:
            ok &= np.where(dirRef >= 0, pos >= CORTE_POSICAO, pos <= espelho)

    if DESCARTA_E2:
        ok &= ~d.e2Manda.to_numpy()
    return np.where(ok, -dirRef, 0)


# ================================================== medias, regime e contexto
def _ema(x, n):
    return pd.Series(x).ewm(span=n, adjust=False).mean().to_numpy()


def _wma(x, n):
    w = np.arange(1, n + 1, dtype=float)
    return (pd.Series(x).rolling(n)
            .apply(lambda v: np.dot(v, w) / w.sum(), raw=True).to_numpy())


def kama(x, n=10, rapida=2, lenta=30):
    """Kaufman Adaptive Moving Average. Acelera quando o movimento e
    direcional e trava quando e ruido."""
    x = np.asarray(x, float)
    mudanca = np.abs(x - np.roll(x, n))
    vol = pd.Series(np.abs(np.diff(x, prepend=x[0]))).rolling(n).sum().to_numpy()
    er = np.divide(mudanca, vol, out=np.zeros_like(x), where=(vol > 0))
    er[:n] = 0.0
    sc = (er * (2.0 / (rapida + 1) - 2.0 / (lenta + 1)) + 2.0 / (lenta + 1)) ** 2
    out = np.empty_like(x)
    out[0] = x[0]
    for i in range(1, len(x)):
        out[i] = out[i - 1] + sc[i] * (x[i] - out[i - 1])
    return out


def hma(x, n=21):
    """Hull Moving Average: WMA(2*WMA(n/2) - WMA(n), sqrt(n))."""
    meia = max(2, int(round(n / 2)))
    raiz = max(2, int(round(np.sqrt(n))))
    return _wma(2 * _wma(x, meia) - _wma(x, n), raiz)


def t3(x, n=21, v=0.7):
    """T3 de Tim Tillson: seis EMAs encadeadas com fator de volume."""
    e = [None] * 7
    e[1] = _ema(x, n)
    for k in range(2, 7):
        e[k] = _ema(e[k - 1], n)
    c1 = -v ** 3
    c2 = 3 * v ** 2 + 3 * v ** 3
    c3 = -6 * v ** 2 - 3 * v - 3 * v ** 3
    c4 = 1 + 3 * v + v ** 3 + 3 * v ** 2
    return c1 * e[6] + c2 * e[5] + c3 * e[4] + c4 * e[3]


def jma_aprox(x, n=21, fase=0.0, power=2):
    """APROXIMACAO PUBLICA do estilo Jurik -- NAO e o JMA do Jurik Research,
    que e proprietario e nao publicado. Ler como "media adaptativa muito
    suavizada", nunca como "o JMA".
    """
    x = np.asarray(x, float)
    m = len(x)
    beta = 0.45 * (n - 1) / (0.45 * (n - 1) + 2.0)
    alpha = beta ** power
    pr = 0.5 if fase < -100 else (2.5 if fase > 100 else fase / 100.0 + 1.5)
    ma1 = np.empty(m); det0 = np.zeros(m); det1 = np.zeros(m); jm = np.empty(m)
    ma1[0] = jm[0] = x[0]
    for i in range(1, m):
        ma1[i] = (1 - alpha) * x[i] + alpha * ma1[i - 1]
        det0[i] = (x[i] - ma1[i]) * (1 - beta) + beta * det0[i - 1]
        ma2 = ma1[i] + pr * det0[i]
        det1[i] = (ma2 - jm[i - 1]) * (1 - alpha) ** 2 + alpha ** 2 * det1[i - 1]
        jm[i] = jm[i - 1] + det1[i]
    return jm


MEDIAS = {'kama': kama, 'hma': hma, 't3': t3, 'jma': jma_aprox}

# Parametros por familia. Vieram calibrados do projeto do WIN e NAO foram
# recalibrados aqui: todos os cortes que eles governam sao razoes contra o
# range medio, entao a escala do ativo ja saiu da conta. Recalibrar por
# ativo sobre uma amostra so seria ajustar ao ruido dela.
PARAMS_MA = {
    'ema3': {},
    'kama': dict(MA_PER=13, INCL_MIN=0.30, INCL_CONSOL=0.15),
    'hma':  dict(MA_PER=13, INCL_MIN=0.10, INCL_CONSOL=0.05),
    't3':   dict(MA_PER=13, INCL_MIN=0.10, INCL_CONSOL=0.05),
    'jma':  dict(MA_PER=21, INCL_MIN=0.10, INCL_CONSOL=0.05),
}


def aplica_ma(regime):
    """Poe os parametros calibrados da familia nas globais do modulo."""
    for k, v in PARAMS_MA.get(regime, {}).items():
        globals()[k] = v


ROT_MA = {
    'ema3': 'três EMAs 21/42/72 (empilhamento)',
    'kama': 'KAMA (inclinação)',
    'hma': 'Hull (inclinação)',
    't3': 'T3 Tillson (inclinação)',
    'jma': 'estilo Jurik, aproximação (inclinação)',
}


def contexto(d, regime=None):
    """Contexto de direcao, regime e distancias.

    REGIME_MA = 'ema3' usa o empilhamento das EMAs 21/42/72: direcao = ordem
    das tres, forca = leque entre a rapida e a lenta, toque = encostar em
    qualquer uma delas.

    REGIME_MA = 'kama'|'hma'|'t3'|'jma' usa UMA media so: direcao = sinal da
    INCLINACAO dela nas MA_SLOPE barras anteriores, forca = modulo dessa
    inclinacao, toque = encostar nela.

    Todas as distancias sao normalizadas pelo range medio, entao os cortes
    valem em qualquer regime de volatilidade -- e foi por isso que
    atravessaram do WIN para o ouro sem mudanca [X4].
    """
    regime = REGIME_MA if regime is None else regime
    C = d.C.to_numpy(float)
    H = d.H.to_numpy(float)
    L = d.L.to_numpy(float)

    mrng = pd.Series(H - L).rolling(PERIODO_RANGE).mean().to_numpy()
    mrng = np.where((mrng > 0) & ~np.isnan(mrng), mrng, np.nan)

    d = d.copy()
    d['mrng'] = mrng

    if regime == 'ema3':
        er, em, el = _ema(C, EMA_R), _ema(C, EMA_M), _ema(C, EMA_L)
        medias = (er, em, el)
        d['er'], d['em'], d['el'] = er, em, el
        forca = (er - el) / mrng                     # leque assinado
        d['alinhado'] = np.where((er > em) & (em > el), 1,
                                 np.where((er < em) & (em < el), -1, 0))
        d['tendencia'] = (d.alinhado.to_numpy() != 0) & (np.abs(forca) >= LEQUE_MIN)
        d['consolida'] = np.abs(forca) < CONSOL_MAX
        ref = er
        d['extCacho'] = (C - (er + em + el) / 3.0) / mrng
    else:
        ma = MEDIAS[regime](C, MA_PER)
        medias = (ma,)
        d['er'] = d['em'] = d['el'] = ma
        ant = pd.Series(ma).shift(MA_SLOPE).to_numpy()
        forca = (ma - ant) / mrng                    # inclinacao assinada
        sinal = np.where(forca > 0, 1, np.where(forca < 0, -1, 0))
        d['alinhado'] = np.where(np.abs(forca) >= INCL_MIN, sinal, 0)
        d['tendencia'] = d.alinhado.to_numpy() != 0
        d['consolida'] = np.abs(forca) < INCL_CONSOL
        ref = ma
        d['extCacho'] = (C - ma) / mrng

    d['forca'] = forca
    d['ext'] = (C - ref) / mrng

    tol = TOL_TOQUE * mrng
    toca = np.zeros(len(d), bool)
    for mm in medias:
        toca |= (L - tol <= mm) & (mm <= H + tol)
    d['toca'] = toca
    return d


# ==================================================================== setups
def setups(d, sig, ativos=None):
    """Marca, para cada barra, qual setup disparou. '' = nenhum."""
    ativos = SETUPS_ATIVOS if ativos is None else ativos
    n = len(d)
    alin = d.alinhado.to_numpy()
    tend = d.tendencia.to_numpy()
    cons = d.consolida.to_numpy()
    toca = d.toca.to_numpy()
    ext = d.ext.to_numpy()
    extC = d.extCacho.to_numpy()
    pT = d.pE3.to_numpy()
    ok_ctx = ~np.isnan(d.mrng.to_numpy())

    # A - TENDENCIA: alinhada e aberta, pullback tocando uma media,
    #     gatilho A FAVOR do empilhamento.
    A = ok_ctx & tend & toca & (sig != 0) & (sig == alin)

    # B - REVERSAO RAPIDA: fora de consolidacao, preco longe da rapida,
    #     gatilho CONTRA o afastamento.
    B = (ok_ctx & ~cons & (np.abs(ext) >= AFAST_MIN_B) & (pT >= VEL_MIN_B)
         & (sig != 0) & (sig == -np.sign(ext)))

    # C - REVERSAO EM CONSOLIDACAO: medias emboladas, preco longe do cacho,
    #     gatilho CONTRA o afastamento.
    C = (ok_ctx & cons & (np.abs(extC) >= AFAST_MIN_C)
         & (sig != 0) & (sig == -np.sign(extC)))

    # L - LIVRE: o gatilho sem nenhuma exigencia de regime. Vem por ultimo na
    #     PRIORIDADE, entao so fica com o que A, B e C nao reivindicaram --
    #     ('A','B','C','L') marca TODO sinal, cada um pelo regime em que caiu.
    Lv = ok_ctx & (sig != 0)

    marca = np.array([''] * n, dtype=object)
    mapa = {'A': A, 'B': B, 'C': C, 'L': Lv}
    for nome in reversed(PRIORIDADE):          # o primeiro da tupla sobrescreve
        if nome in ativos:
            marca = np.where(mapa[nome], nome, marca)
    return marca


# ================================================================== execucao
def parcial_pts():
    """A distancia da parcial, em USD.

    PARCIAL_EM = None significa "na mesma distancia do stop". So ai a media
    da operacao cai exatamente em cima do stop inicial, e o desfecho 'zero'
    e zero de verdade.
    """
    return float(STOP if PARCIAL_EM is None else PARCIAL_EM)


def stop_pos_parcial(ent, s, parcial, stop_ini):
    """Onde vai o stop do restante depois da parcial. Ver STOP_APOS_PARCIAL."""
    if STOP_APOS_PARCIAL == 'entrada':
        alvo_stop = ent
    else:
        alvo_stop = ent - s * (FRAC_PARCIAL * parcial) / (1.0 - FRAC_PARCIAL)
    return max(stop_ini, alvo_stop) if s == 1 else min(stop_ini, alvo_stop)


def _simula_trade(H, L, C, dia, n, i, s, entrada, max_fill):
    """Um trade. Devolve dict ou None se a ordem nao foi preenchida.

    Gestao SEMPRE a partir da barra SEGUINTE a da entrada -- nem a barra do
    sinal (cujo H/L ocorreu antes do fechamento) nem a barra do fill (cujo
    H/L em parte ocorreu antes do toque) sao usadas para stop/alvo. Quando
    stop e alvo cabem na mesma barra, assume-se o STOP.
    """
    if entrada == 'fecha':
        ent = C[i]
        jf = i
    else:
        ent = (H[i] + L[i]) / 2.0
        jf = -1
        for j in range(i + 1, n):
            if dia[j] != dia[i] or (j - i) > max_fill:
                break
            if (s == 1 and L[j] <= ent) or (s == -1 and H[j] >= ent):
                jf = j
                break
        if jf < 0:
            return None

    parcial = parcial_pts()
    stop_ini = ent - s * STOP
    stop_p = stop_ini
    parc_p = ent + s * parcial
    alvo_p = ent + s * ALVO

    fase = 1          # 1 = posicao cheia | 2 = depois da parcial
    pnl = 0.0
    res = 'fim'
    k = jf
    ult = jf          # ultima barra VISTA DENTRO do pregao -- ver [B1]
    barras = 0
    for k in range(jf + 1, n):
        if dia[k] != dia[i]:
            k = ult   # [B1] o laco quebrou na 1a barra do pregao SEGUINTE;
            break     #      a saida por fim de pregao e a ultima barra DESTE
        ult = k
        barras += 1
        hit_s = (L[k] <= stop_p) if s == 1 else (H[k] >= stop_p)
        if fase == 1:
            hit_p = (H[k] >= parc_p) if s == 1 else (L[k] <= parc_p)
            if hit_s:                                  # pessimista: stop primeiro
                pnl = -STOP
                res = 'stop'
                break
            if hit_p:
                pnl = FRAC_PARCIAL * parcial
                fase = 2
                stop_p = stop_pos_parcial(ent, s, parcial, stop_ini)
                hit_a = (H[k] >= alvo_p) if s == 1 else (L[k] <= alvo_p)
                if hit_a:
                    pnl += (1 - FRAC_PARCIAL) * ALVO
                    res = 'alvo'
                    break
                continue
        else:
            hit_a = (H[k] >= alvo_p) if s == 1 else (L[k] <= alvo_p)
            if hit_s:                                  # media da operacao
                pnl += (1 - FRAC_PARCIAL) * s * (stop_p - ent)
                res = 'zero'
                break
            if hit_a:
                pnl += (1 - FRAC_PARCIAL) * ALVO
                res = 'alvo'
                break

    if res == 'fim':
        if k <= jf:
            return None                                # sinal na ultima barra do dia
        saida = C[k]
        if fase == 1:
            pnl = s * (saida - ent)
        else:
            pnl += (1 - FRAC_PARCIAL) * s * (saida - ent)

    return dict(i=i, jf=jf, saiu=k, s=s, ent=ent, res=res,
                pnl=pnl - CUSTO_PTS, dia=dia[i], barras=barras)


def roda(d, marca, sig, entrada=ENTRADA, carteira=True, setup=None,
         max_fill=MAX_BARRAS_FILL):
    """Roda os trades.

    carteira=True  -> uma posicao por vez; sinal que chega com posicao
                      aberta e ignorado (o realista).
    carteira=False -> cada sinal e medido isoladamente.
    """
    H, L, C = (d[c].to_numpy(float) for c in ('H', 'L', 'C'))
    dia = d.dia.to_numpy()
    n = len(d)

    alvos = np.flatnonzero((marca != '') if setup is None else (marca == setup))
    trades = []
    livre_em = -1
    for i in alvos:
        if carteira and i < livre_em:
            continue
        t = _simula_trade(H, L, C, dia, n, i, int(sig[i]), entrada, max_fill)
        if t is None:
            continue
        t['setup'] = marca[i]
        trades.append(t)
        if carteira:
            livre_em = t['saiu'] + 1
    return pd.DataFrame(trades)


# ================================================================== metricas
def metricas(tr, n_pregoes=None):
    if tr is None or len(tr) == 0:
        return None
    g = tr.groupby('dia').pnl.sum()
    pregoes = len(g)
    ev = tr.pnl.mean()
    somat = tr.pnl.sum()
    t = g.mean() / (g.std() / np.sqrt(len(g))) if len(g) > 2 and g.std() > 0 else np.nan

    eq = tr.pnl.cumsum().to_numpy()
    dd = float((np.maximum.accumulate(eq) - eq).max()) if len(eq) else 0.0

    ganhos = tr.pnl[tr.pnl > 0].sum()
    perdas = -tr.pnl[tr.pnl < 0].sum()
    return dict(
        n=len(tr),
        pregoes=pregoes,
        por_pregao=len(tr) / pregoes,
        ev=ev,
        total=somat,
        total_rs=somat * VAL_PONTO,
        acerto=100.0 * (tr.pnl > 0).mean(),
        t=t,
        dias_pos=100.0 * (g > 0).mean(),
        dd=dd,
        pf=(ganhos / perdas) if perdas > 0 else np.inf,
        p_alvo=100.0 * (tr.res == 'alvo').mean(),
        p_stop=100.0 * (tr.res == 'stop').mean(),
        p_zero=100.0 * (tr.res == 'zero').mean(),
        p_fim=100.0 * (tr.res == 'fim').mean(),
        barras=tr.barras.mean(),
    )


def prepara(nome, ativos=None, regime=None):
    """Carga + indicador + contexto + gatilho + setups, de uma vez."""
    d = contexto(indicador(carrega(base=nome)), regime)
    sig = gatilho(d)
    marca = setups(d, sig, ativos)
    return d, sig, marca
