# -*- coding: utf-8 -*-
"""
Engine de backtest - Rincones1 (WIN, grafico de 10.000 ticks)
Ver ESTRATEGIA.md para a especificacao completa das regras.

O gatilho e o indice de esforco validado em
  ProfitChart/Indicadores/Grafico-Ticks/Ticks_Esforco_Reversao.ntsl
reimplementado aqui identico (mesmos eixos, mesma janela, mesmos filtros).

Tres setups, separados pelo REGIME das medias 21/42/72:
  A  - TENDENCIA: medias alinhadas e abertas, pullback ate uma delas,
       gatilho a favor da tendencia.
  B  - REVERSAO RAPIDA: fora de consolidacao, preco afastado das medias,
       movimento rapido, gatilho contra o afastamento.
  C  - REVERSAO EM CONSOLIDACAO: medias emboladas, preco afastado do
       cacho, gatilho contra o afastamento.

Gestao (ESTRATEGIA.md 5): stop 150, parcial de 50% em +100 que zera o
risco (stop do restante vai para a entrada), alvo final 300.

Execucao (ESTRATEGIA.md 5): ordem limitada no meio do candle do gatilho,
valida por UMA BARRA. Nao preencheu na barra seguinte, o trade e
abortado (MAX_BARRAS_FILL = 1).
"""
import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(BASE, 'dados')

ARQUIVOS = {
    'WINFUT': os.path.join(DADOS, 'WIFNUT_10000T_28-28-26.csv'),
    'WINV26': os.path.join(DADOS, 'WINV26_10000T_28-08-26.csv'),
}

# ---------------------------------------------------------------- parametros
TICK = 5.0             # tick do WIN, em pontos
VAL_PONTO = 0.20       # R$ por ponto, 1 contrato WIN

# --- gestao (o que o Carlos pediu)
STOP = 150.0           # stop inicial, em pontos
PARCIAL_EM = None      # onde sai a parcial | None = na MESMA distancia do stop
FRAC_PARCIAL = 0.50    # fracao da posicao vendida na parcial
ALVO = 300.0           # alvo do restante
CUSTO_PTS = 0.0        # custo de ida e volta em pontos (0 = bruto)

# Onde fica o stop do RESTANTE depois que a parcial sai.
#
#   'media'    na MEDIA DA OPERACAO: o preco em que o que ja foi realizado
#              na parcial cancela exatamente a perda do restante. Com meia
#              posicao e a parcial a P pontos, isso e P pontos ABAIXO da
#              entrada (numa compra) -- e se a parcial sai na mesma
#              distancia do stop, esse preco E o stop inicial: o stop nao
#              anda, a operacao e que passou a valer zero ali.
#              Desfecho 'zero' = 0 pontos, de verdade.
#
#   'entrada'  no preco de ENTRADA. Era o que este backtest fazia antes, e
#              e otimista: o desfecho 'zero' pagava FRAC_PARCIAL x PARCIAL
#              (+50 pontos com a parcial em 100) e mesmo assim aparecia
#              como "zero a zero". Fica disponivel so para reproduzir os
#              numeros antigos.
#
# O stop NUNCA se afasta: se a media da operacao ficar mais longe que o
# stop inicial, vale o stop inicial.
STOP_APOS_PARCIAL = 'media'

# --- gatilho de esforco (identico ao .ntsl validado)
PERIODO_REF = 20       # janela do percentil, em barras validas
PISO_DUR = 0.001       # minuto: duracao zero vira velocidade maxima
METRICA_E2 = 2         # qual formula alimenta o eixo [E2]:
                       #   2 = (|delta|/esforco) * (1 - |C-O|/percurso)  <- v2
                       #   0 = |delta| / |C-O|                           <- v1
                       #   1 = esforco / range                           <- v1 variante
                       #   3 = |delta| * volta   |  4 = volta pura
                       # ver Ticks_Esforco_Hist_v2.ntsl
NIVEL_MIN = 0.80       # indice minimo
CORTE_POSICAO = 50.0   # posMediaCorpo <= isto (delta comprador)
CORPO_MAX = 50.0       # corpo/range maximo, em %  -- exigido pela entrada limitada
DESCARTA_E2 = True     # descarta barras em que [E2] e o eixo dominante

# --- medias e regimes
REGIME_MA = 'ema3'     # 'ema3' | 'kama' | 'hma' | 't3' | 'jma'  -- ver ESTRATEGIA.md 3
MA_PER = 21            # periodo da media unica (nao usado no ema3)
MA_SLOPE = 5           # barras do lookback da inclinacao (nao usado no ema3)
INCL_MIN = 0.25        # media unica: |inclinacao|/rangeMedio minimo para "tendencia"
INCL_CONSOL = 0.12     # media unica: abaixo disso e consolidacao
EMA_R, EMA_M, EMA_L = 21, 42, 72
PERIODO_RANGE = 20     # janela do range medio (unidade de todas as distancias)
LEQUE_MIN = 0.30       # setup A: (EMA21-EMA72)/rangeMedio minimo para "tendencia"
TOL_TOQUE = 1.00       # setup A: tolerancia do toque na media, em ranges medios
CONSOL_MAX = 0.35      # setup C: (EMA21-EMA72)/rangeMedio abaixo disso = consolidacao
AFAST_MIN_B = 1.00     # setup B: |Close-EMA21|/rangeMedio minimo
AFAST_MIN_C = 0.80     # setup C: |Close-EMA21|/rangeMedio minimo
VEL_MIN_B = 0.00       # setup B: percentil de velocidade minimo -- INERTE, ver ESTRATEGIA.md

# --- execucao
ENTRADA = 'meio'       # 'meio' = ordem limitada no meio do candle | 'fecha' = a mercado
MAX_BARRAS_FILL = 1    # A REGRA DA BARRA SEGUINTE. A limitada vale por UMA
                       # barra: ou preenche na barra seguinte a do gatilho, ou
                       # a operacao e ABORTADA. Ver ESTRATEGIA.md 5.
                       # 99999 = o comportamento antigo (valida ate o fim do
                       # pregao), mantido so para reproduzir a comparacao.
PRIORIDADE = ('A', 'B', 'C')   # quem ganha quando mais de um setup dispara
SETUPS_ATIVOS = ('A', 'B')     # C mede negativo nos dois arquivos -- ver ESTRATEGIA.md


# ============================================================ carga de dados
def carrega(caminho):
    """Le o csv exportado do Profit, em ordem cronologica.

    A coluna BarDurationF*1000 e MILESIMO DE MINUTO -- dividida por 1000
    vira minutos, que e o que BarDurationF() devolve no NTSL.
    """
    df = pd.read_csv(caminho, sep='\t', decimal=',', thousands='.')
    df.columns = ['Data', 'O', 'H', 'L', 'C',
                  'Buy', 'Sell', 'DurX1000', 'Qtd', 'Trades']
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y %H:%M')
    df = df.iloc[::-1].reset_index(drop=True)      # csv vem do mais novo p/ o antigo
    df['Dur'] = df['DurX1000'].astype(float) / 1000.0
    df['dia'] = df['Data'].dt.date
    df = df[(df.Buy + df.Sell) > 0].reset_index(drop=True)   # barra valida
    return df


# ====================================================== indicador de esforco
def _pct_rank(a, n):
    """Fracao das n barras anteriores (exclui a atual) com valor MENOR."""
    a = np.asarray(a, float)
    out = np.full(len(a), np.nan)
    for i in range(n, len(a)):
        out[i] = (a[i - n:i] < a[i]).sum() / n
    return out


def indicador(df):
    """Devolve o dataframe com o indice de esforco e seus tres eixos."""
    esf = (df.Buy + df.Sell).to_numpy(float)
    dlt = (df.Buy - df.Sell).to_numpy(float)

    adl = np.abs(dlt).copy()
    adl[adl < 1] = 1.0
    res = np.abs(df.C - df.O).to_numpy(float) / TICK
    res[res < 1] = 1.0
    rng_t = (df.H - df.L).to_numpy(float) / TICK
    rng_t[rng_t < 1] = 1.0
    dur = df.Dur.to_numpy(float).copy()
    dur[dur < PISO_DUR] = PISO_DUR

    # PERCURSO MINIMO compativel com o OHLC: a ida E a volta.
    # |C-O| e o saldo e H-L e a maior distancia alcancada; nenhum dos dois
    # ve o caminho. 2*range - corpo e o menor caminho que passa pelos dois
    # extremos e termina no fechamento.  Piso em res: com H=L nao houve
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

    pV = _pct_rank(esf, PERIODO_REF)              # [E1] volume
    pD = _pct_rank(m_e2, PERIODO_REF)             # [E2] vaivem (ver METRICA_E2)
    pT = _pct_rank(1.0 / dur, PERIODO_REF)        # [E3] tempo
    idx = (pV + pD + pT) / 3.0

    d = df.copy()
    d['pV'], d['pD'], d['pT'], d['idx'] = pV, pD, pT, idx
    d['volta'] = volta
    d['dlt'] = dlt
    d['dirC'] = np.where(dlt > 0, 1, np.where(dlt < 0, -1, 0))
    d['e2Manda'] = (pD >= pV) & (pD >= pT)

    O, H, L, C = (df[c].to_numpy(float) for c in ('O', 'H', 'L', 'C'))
    rng = (H - L).copy()
    rng[rng <= 0] = TICK
    d['posMediaCorpo'] = ((O + C) / 2.0 - L) / rng * 100.0
    d['porcCorpoWick'] = np.abs(C - O) / rng * 100.0
    return d


def gatilho(d):
    """Sinal do Ticks_Esforco_Reversao: +1 compra, -1 venda, 0 nada.

    A seta sai sempre CONTRA quem agrediu.
    """
    pos = d.posMediaCorpo.to_numpy()
    dirC = d.dirC.to_numpy()
    ok = (d.idx.to_numpy() >= NIVEL_MIN) & (dirC != 0) & ~np.isnan(d.idx.to_numpy())
    ok &= np.where(dirC == 1, pos <= CORTE_POSICAO, pos >= (100 - CORTE_POSICAO))
    ok &= d.porcCorpoWick.to_numpy() <= CORPO_MAX
    if DESCARTA_E2:
        ok &= ~d.e2Manda.to_numpy()
    return np.where(ok, -dirC, 0)


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
    suavizada", nunca como "o JMA". Ver ESTRATEGIA.md 3.
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

# Parametros calibrados por familia (varredura em RESULTADOS.md 10).
# Cada um foi escolhido por medir bem nos DOIS arquivos, nao no melhor de um.
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
    'ema3': 'tres EMAs 21/42/72 (empilhamento)',
    'kama': 'KAMA (inclinação)',
    'hma': 'Hull (inclinação)',
    't3': 'T3 Tillson (inclinação)',
    'jma': 'estilo Jurik, aproximação (inclinação)',
}


def contexto(d, regime=None):
    """Contexto de direcao, regime e distancias.

    REGIME_MA = 'ema3'  usa o empilhamento das EMAs 21/42/72 (a versao
    original): direcao = ordem das tres, forca = leque entre a rapida e a
    lenta, toque = encostar em qualquer uma delas.

    REGIME_MA = 'kama'|'hma'|'t3'|'jma' usa UMA media so: direcao = sinal
    da INCLINACAO dela nas MA_SLOPE barras anteriores, forca = modulo
    dessa inclinacao, toque = encostar nela. Todas as distancias sao
    normalizadas pelo range medio, entao os cortes valem em qualquer
    regime de volatilidade.
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
        ref = er                                     # a media de referencia
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

    # toque: a barra encosta em alguma das medias do regime?
    tol = TOL_TOQUE * mrng
    toca = np.zeros(len(d), bool)
    for mm in medias:
        toca |= (L - tol <= mm) & (mm <= H + tol)
    d['toca'] = toca
    return d


# ==================================================================== setups
def setups(d, sig, ativos=None):
    """Marca, para cada barra, qual setup disparou. '' = nenhum.

    Prioridade em PRIORIDADE (default: tendencia primeiro, como pedido).
    `ativos` limita quais setups entram (default SETUPS_ATIVOS).
    """
    ativos = SETUPS_ATIVOS if ativos is None else ativos
    n = len(d)
    alin = d.alinhado.to_numpy()
    tend = d.tendencia.to_numpy()
    cons = d.consolida.to_numpy()
    toca = d.toca.to_numpy()
    ext = d.ext.to_numpy()
    extC = d.extCacho.to_numpy()
    pT = d.pT.to_numpy()
    ok_ctx = ~np.isnan(d.mrng.to_numpy())

    # A - TENDENCIA: alinhada e aberta, pullback tocando uma media,
    #     gatilho A FAVOR do empilhamento.
    A = ok_ctx & tend & toca & (sig != 0) & (sig == alin)

    # B - REVERSAO RAPIDA: fora de consolidacao, preco longe da rapida,
    #     barra rapida, gatilho CONTRA o afastamento.
    B = (ok_ctx & ~cons & (np.abs(ext) >= AFAST_MIN_B) & (pT >= VEL_MIN_B)
         & (sig != 0) & (sig == -np.sign(ext)))

    # C - REVERSAO EM CONSOLIDACAO: medias emboladas, preco longe do cacho,
    #     gatilho CONTRA o afastamento.
    C = (ok_ctx & cons & (np.abs(extC) >= AFAST_MIN_C)
         & (sig != 0) & (sig == -np.sign(extC)))

    marca = np.array([''] * n, dtype=object)
    mapa = {'A': A, 'B': B, 'C': C}
    for nome in reversed(PRIORIDADE):          # o primeiro da tupla sobrescreve
        if nome in ativos:
            marca = np.where(mapa[nome], nome, marca)
    return marca


# ================================================================== execucao
def parcial_pts():
    """A distancia da parcial, em pontos.

    PARCIAL_EM = None significa "na mesma distancia do stop". E o caso
    normal: com meia posicao, so quando a parcial sai na distancia do
    stop e que a media da operacao cai exatamente em cima do stop
    inicial, e a operacao fica em zero a zero de verdade se o stop pegar
    depois. Com a parcial mais perto que o stop, o stop tem de andar para
    dentro para chegar no zero a zero -- e ai a proteccao vem mais cedo,
    mas o trade morre mais vezes antes do alvo.
    """
    return float(STOP if PARCIAL_EM is None else PARCIAL_EM)


def stop_pos_parcial(ent, s, parcial, stop_ini):
    """Onde vai o stop do restante depois da parcial. Ver STOP_APOS_PARCIAL."""
    if STOP_APOS_PARCIAL == 'entrada':
        alvo_stop = ent
    else:
        # media da operacao: FRAC x parcial ja realizado tem de cancelar
        # (1 - FRAC) x (perda do restante)
        alvo_stop = ent - s * (FRAC_PARCIAL * parcial) / (1.0 - FRAC_PARCIAL)
    # o stop nunca se AFASTA
    return max(stop_ini, alvo_stop) if s == 1 else min(stop_ini, alvo_stop)


def _simula_trade(H, L, C, dia, n, i, s, entrada, max_fill):
    """Um trade. Devolve dict ou None se a ordem nao foi preenchida.

    Gestao SEMPRE a partir da barra SEGUINTE a da entrada -- nem a barra
    do sinal (cujo H/L ocorreu antes do fechamento) nem a barra do fill
    (cujo H/L em parte ocorreu antes do toque) sao usadas para stop/alvo.
    Quando stop e alvo cabem na mesma barra, assume-se o STOP.
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

    fase = 1          # 1 = posicao cheia | 2 = depois da parcial, stop no zero a zero
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
        saida = C[k]                                   # C[ult], ja corrigido em [B1]
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
    carteira=False -> cada sinal e medido isoladamente (para comparar
                      setups sem que um roube trade do outro).
    setup=None     -> todos; ou 'A' / 'B' / 'C'.
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
    d = contexto(indicador(carrega(ARQUIVOS[nome])), regime)
    sig = gatilho(d)
    marca = setups(d, sig, ativos)
    return d, sig, marca
