# -*- coding: utf-8 -*-
"""
Engine de backtest - Rincones1-DTA (WIN, grafico de 10.000 ticks)

Mesma carcaca do Backtest-Rincones1 -- carga, gatilho de esforco, execucao e
gestao --, com OUTRA leitura de contexto. Tres pecas:

  EMA 21      TENDENCIA e linha do meio do canal.
  HULL 50     FORCA / INTENSIDADE do movimento.
  KELTNER     ESTICAMENTO: bandas em 2 e 3 ATRs em volta da EMA 21.

O gatilho e o indicador
  ProfitChart/Indicadores/Grafico-Ticks/Ticks_Esforco_Hist_v2.ntsl
com as CONFIGURACOES PADRAO DELE: os tres eixos ligados, pesos 1/1/1,
MetricaDesloc = 2 (vaivem), PeriodoRef = 20, TickSize = 5. A seta do
indicador e o sinal, e ela sai CONTRA quem agrediu: exige corpo pequeno
(<= 50% do range) e a media do corpo na metade oposta a agressao.

O QUE A MEDICAO ACHOU -- e o motivo de os setups nao serem os obvios
-------------------------------------------------------------------
A hipotese de partida era a leitura classica: comprar com a Hull subindo e
o close ACIMA dela, vender com a Hull descendo e o close ABAIXO. Medida nas
duas bases, em todos os niveis do gatilho e nos dois stops, ela mede
NEGATIVO. O que mede positivo e o contrario:

  * o close no lado OPOSTO da Hull ao do trade -- comprar abaixo de uma
    Hull que esta subindo, vender acima de uma que esta descendo;
  * com a Hull NAO PLANA. A Hull sem inclinacao e o pior balde de todos
    (EV -20 a -100 pontos em todas as celulas medidas): sem intensidade,
    o gatilho nao paga.

Faz sentido com o que o proprio indicador diz de si: ele acende quando
alguem gastou muito e nao levou o preco -- absorcao. Absorcao se desfaz.
Entao ele nao e um sinal de CONTINUACAO, e um sinal de FALHA, e a Hull
entra medindo se ha movimento para falhar (nao plana) e de que lado o
preco esta em relacao a ele.

O canal de Keltner nao veta nada que a Hull ja nao vete -- com o close do
lado oposto da Hull e dentro da profundidade maxima, a barra praticamente
nunca esta na banda. E a leitura CLASSICA da banda (preco esticado, entrada
contra) mede negativo no WINFUT em toda configuracao testada. O unico uso do
canal que mede positivo nas duas bases e a REJEICAO: o pavio fura a banda de
2 ATRs e o candle fecha de volta para dentro -- e mesmo esse piora a
carteira quando entra, porque rouba a vaga de trades melhores.

Os setups
---------
  D  - DESCOLAMENTO DA HULL (principal). Close do lado oposto da Hull,
       Hull nao plana, preco dentro do canal e mergulho de no maximo
       PROF_MAX ATRs da EMA 21.
  T  - TENDENCIA COM FORCA (secundario). A leitura classica, restrita ao
       pullback: Hull e EMA no sentido do trade, close do lado certo da
       Hull e preco ainda nao esticado. Poucos trades, mas positivos.
  K  - REJEICAO DA BANDA (desligado). Pavio fora da banda de 2 ATRs,
       fechamento de volta para dentro.
  KB - BANDA CLASSICA (desligado). Preco parado na zona de esticamento.

Gestao
------
Stop de 0,75 x ATR da barra do sinal (a medicao da secao de gestao: o stop
fixo de 150 pontos herdado do Rincones1 e largo demais para este gatilho),
parcial de 50% na MESMA distancia do stop, stop do restante na MEDIA DA
OPERACAO -- que com meia posicao e o proprio stop inicial --, alvo de 300
pontos. Ordem limitada no meio do candle do gatilho, valida por UMA barra.
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

# --- gestao
STOP = 150.0           # stop fixo, em pontos (so com STOP_MODO = 'pontos')
PARCIAL_EM = None      # onde sai a parcial | None = na MESMA distancia do stop
FRAC_PARCIAL = 0.50    # fracao da posicao vendida na parcial
ALVO = 300.0           # alvo fixo, em pontos (so com ALVO_MODO = 'pontos')
CUSTO_PTS = 0.0        # custo de ida e volta em pontos (0 = bruto)
STOP_APOS_PARCIAL = 'media'    # 'media' = media da operacao | 'entrada'

# VARIANTE: stop e alvo em ATR em vez de pontos fixos. Com barras de tick a
# volatilidade por barra varia bastante ao longo do dia, e um stop fixo e ora
# largo ora apertado. 'atr' dimensiona os dois pelo ATR da barra do sinal.
STOP_MODO = 'atr'      # 'pontos' = STOP fixo | 'atr' = STOP_ATR x ATR
STOP_ATR = 0.75        # multiplo do ATR (so com STOP_MODO = 'atr')
STOP_MIN = 50.0        # piso e teto do stop em ATR, em pontos
STOP_MAX = 400.0
ALVO_MODO = 'pontos'   # 'pontos' = ALVO fixo | 'R' = ALVO_R x stop | 'atr'
ALVO_R = 2.0           # multiplo do stop   (so com ALVO_MODO = 'R')
ALVO_ATR = 2.40        # multiplo do ATR    (so com ALVO_MODO = 'atr')

# --- gatilho de esforco (Ticks_Esforco_Hist_v2, configuracoes padrao)
PERIODO_REF = 20       # janela do percentil, em barras validas
PISO_DUR = 0.001       # minuto: duracao zero vira velocidade maxima
METRICA_E2 = 2         # 2 = (|delta|/esforco) x (1 - |C-O|/percurso)  <- padrao v2
NIVEL_MIN = 0.80       # nivel minimo do indice. NAO e o corte de cor do
                       # .ntsl (0,55 / 0,60): esses foram medidos e ficam
                       # positivos, mas 0,80 mede muito melhor -- ver a
                       # secao do nivel no relatorio.
CORTE_POSICAO = 50.0   # posMediaCorpo <= isto (delta comprador), como no .ntsl
CORPO_MAX = 50.0       # corpo/range maximo, em % -- o porcCorpoWick do .ntsl
DESCARTA_E2 = False    # nao existe no .ntsl; medido como variante

# --- contexto: EMA de tendencia, Hull de forca, Keltner de esticamento
EMA_PER = 21           # a media de tendencia E a linha do meio do Keltner
HMA_PER = 50           # a Hull de forca
ATR_PER = 20           # janela do ATR que dimensiona o canal
KELT_INT = 2.0         # borda interna do canal, em ATRs  ("2 desvios")
KELT_EXT = 3.0         # borda externa do canal, em ATRs  ("3 desvios")
EMA_SLOPE = 5          # barras do lookback da inclinacao da EMA
HMA_SLOPE = 3          # barras do lookback da inclinacao da Hull -- ela ja e
                       # rapida, lookback longo so atrasa
INCL_EMA = 0.05        # |inclinacao da EMA| / ATR minimo para haver tendencia
HMA_PLANA = 0.05       # |inclinacao da Hull| / ATR abaixo disso a Hull esta
                       # PLANA -- sem intensidade. E o VETO do setup D.
DIST_HMA_MIN = 0.0     # setup D: quao longe do lado errado da Hull o close
                       # precisa estar, em ATRs (0 = so o lado)
PROF_MAX = 1.50        # setup D: profundidade maxima do mergulho, em ATRs
                       # medida da EMA 21 (None = sem limite)
EXT_MAX_T = 0.50       # setup T: esticamento maximo na hora de entrar, em ATRs
BANDA_K = 1            # setup K: 1 = da banda de 2 ATRs para fora
                       #          2 = so alem de 3 ATRs

# --- execucao
ENTRADA = 'meio'       # 'meio' = ordem limitada no meio do candle | 'fecha'
MAX_BARRAS_FILL = 1    # a limitada vale por UMA barra
PRIORIDADE = ('D', 'T', 'K', 'KB')  # quem ganha quando mais de um setup dispara
SETUPS_ATIVOS = ('D', 'T')     # K e KB medidos e desligados -- ver RESULTADOS.md


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
    """Indice de esforco e os tres eixos -- identico ao Ticks_Esforco_Hist_v2."""
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
    perc = (2.0 * (df.H - df.L).to_numpy(float)
            - np.abs(df.C - df.O).to_numpy(float)) / TICK
    perc = np.maximum(perc, res)
    volta = 1.0 - res / perc                      # fracao do caminho desfeita
    desq = np.where(esf < 1, 0.0, adl / np.maximum(esf, 1e-12))

    m_e2 = {0: adl / res,
            1: esf / rng_t,
            2: desq * volta,                      # padrao do v2
            3: adl * volta,
            4: volta}[METRICA_E2]

    pV = _pct_rank(esf, PERIODO_REF)              # [E1] volume
    pD = _pct_rank(m_e2, PERIODO_REF)             # [E2] vaivem
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


def gatilho(d, nivel=None):
    """A seta do Ticks_Esforco_Hist_v2: +1 compra, -1 venda, 0 nada.

    Sai sempre CONTRA quem agrediu -- esforco grande que nao pagou e
    absorcao, e absorcao se desfaz.
    """
    nivel = NIVEL_MIN if nivel is None else nivel
    pos = d.posMediaCorpo.to_numpy()
    dirC = d.dirC.to_numpy()
    idx = d.idx.to_numpy()
    ok = (idx >= nivel) & (dirC != 0) & ~np.isnan(idx)
    ok &= np.where(dirC == 1, pos <= CORTE_POSICAO, pos >= (100 - CORTE_POSICAO))
    ok &= d.porcCorpoWick.to_numpy() <= CORPO_MAX
    if DESCARTA_E2:
        ok &= ~d.e2Manda.to_numpy()
    return np.where(ok, -dirC, 0)


# ======================================================= medias e contexto
def _ema(x, n):
    return pd.Series(x).ewm(span=n, adjust=False).mean().to_numpy()


def _wma(x, n):
    w = np.arange(1, n + 1, dtype=float)
    return (pd.Series(x).rolling(n)
            .apply(lambda v: np.dot(v, w) / w.sum(), raw=True).to_numpy())


def hma(x, n=50):
    """Hull Moving Average: WMA(2*WMA(n/2) - WMA(n), sqrt(n))."""
    meia = max(2, int(round(n / 2)))
    raiz = max(2, int(round(np.sqrt(n))))
    return _wma(2 * _wma(x, meia) - _wma(x, n), raiz)


def atr(H, L, C, n=20):
    """ATR classico (media exponencial do range verdadeiro).

    Na barra de tick o gap entre barras e pequeno mas existe -- o range
    verdadeiro cobre isso, o H-L simples nao.
    """
    pc = pd.Series(C).shift(1).to_numpy()
    tr = np.maximum(H - L, np.maximum(np.abs(H - pc), np.abs(L - pc)))
    tr[0] = H[0] - L[0]
    return _ema(tr, n)


def contexto(d):
    """Tendencia (EMA 21), forca (Hull 50) e esticamento (Keltner).

    Todas as distancias saem em ATR, entao os cortes valem igual em pregao
    parado e em pregao violento.
    """
    d = d.copy()
    C = d.C.to_numpy(float)
    H = d.H.to_numpy(float)
    L = d.L.to_numpy(float)

    ema = _ema(C, EMA_PER)
    hul = hma(C, HMA_PER)
    a = atr(H, L, C, ATR_PER)
    a = np.where(a > 0, a, np.nan)

    d['ema'], d['hma'], d['atr'] = ema, hul, a

    # --- as bandas de Keltner: 2 e 3 ATRs em volta da EMA 21
    d['k2s'], d['k2i'] = ema + KELT_INT * a, ema - KELT_INT * a
    d['k3s'], d['k3i'] = ema + KELT_EXT * a, ema - KELT_EXT * a

    # --- ESTICAMENTO: onde o close esta, em ATRs, contado da EMA 21
    pos = (C - ema) / a
    d['pos'] = pos
    d['zona'] = np.where(np.abs(pos) >= KELT_EXT, 2,
                         np.where(np.abs(pos) >= KELT_INT, 1, 0))

    # --- TENDENCIA: inclinacao da EMA 21, normalizada pelo ATR
    inc_e = (ema - pd.Series(ema).shift(EMA_SLOPE).to_numpy()) / a
    d['inc_ema'] = inc_e
    d['dir_ema'] = np.where(inc_e >= INCL_EMA, 1,
                            np.where(inc_e <= -INCL_EMA, -1, 0))

    # --- FORCA: a Hull 50. Duas leituras, e elas sao independentes:
    #     inclinacao = para onde a intensidade aponta
    #     lado       = de que lado da Hull o preco fechou
    inc_h = (hul - pd.Series(hul).shift(HMA_SLOPE).to_numpy()) / a
    d['inc_hma'] = inc_h
    d['dist_hma'] = (C - hul) / a                 # assinada, em ATRs
    d['lado_hma'] = np.where(C > hul, 1, np.where(C < hul, -1, 0))
    # A LEITURA PEDIDA: forca de compra = Hull subindo E close acima dela.
    d['forca'] = np.where((inc_h >= HMA_PLANA) & (C > hul), 1,
                          np.where((inc_h <= -HMA_PLANA) & (C < hul), -1, 0))
    # O VETO: Hull sem inclinacao = movimento sem intensidade.
    d['hma_plana'] = np.abs(inc_h) < HMA_PLANA

    d['ok_ctx'] = ~np.isnan(a) & ~np.isnan(hul) & ~np.isnan(inc_e) & ~np.isnan(inc_h)
    return d


# ==================================================================== setups
def setups(d, sig, ativos=None):
    """Marca, para cada barra, qual setup disparou. '' = nenhum.

    As distancias entram ASSINADAS PELO LADO DO TRADE:

        dh = sig x (close - Hull50) / ATR
        de = sig x (close - EMA21)  / ATR

    dh < 0 significa "estou comprando ABAIXO da Hull" (ou vendendo acima
    dela) -- o lado oposto ao que a Hull ocupa. dh > 0 e o contrario: entrar
    do lado em que o preco ja esta, que e a leitura classica de forca.
    """
    ativos = SETUPS_ATIVOS if ativos is None else ativos
    n = len(d)
    ok = d.ok_ctx.to_numpy()
    pos = np.nan_to_num(d.pos.to_numpy())
    zona = d.zona.to_numpy()
    plana = d.hma_plana.to_numpy()
    dir_e = d.dir_ema.to_numpy()
    inc_h = np.nan_to_num(d.inc_hma.to_numpy())
    dist_h = np.nan_to_num(d.dist_hma.to_numpy())

    dh = sig * dist_h
    de = sig * pos
    inch = sig * inc_h              # inclinacao da Hull vista do lado do trade
    ince = sig * np.nan_to_num(d.inc_ema.to_numpy())

    # D - DESCOLAMENTO DA HULL. O setup principal, e o que a medicao achou.
    #     Tres condicoes:
    #       1. o close esta do lado OPOSTO da Hull ao do trade (dh < 0)
    #       2. a Hull NAO esta plana -- o movimento tem intensidade
    #       3. o preco esta DENTRO do canal de Keltner (|pos| < 2 ATRs)
    #     Mais a profundidade maxima: nao se compra um mergulho de mais de
    #     PROF_MAX ATRs abaixo da EMA 21.
    D = (ok & (sig != 0) & (dh <= -DIST_HMA_MIN) & ~plana & (zona == 0))
    if PROF_MAX is not None:
        D = D & (de >= -PROF_MAX)

    # T - TENDENCIA COM FORCA. A leitura classica, e a que o Carlos pediu:
    #     Hull apontando para o lado do trade, close do lado certo dela, EMA
    #     no mesmo sentido, e o preco AINDA NAO esticado (de < EXT_MAX_T) --
    #     ou seja, um pullback, nao uma perseguicao.
    T = (ok & (sig != 0) & (dh > 0) & (inch >= HMA_PLANA) & (ince >= INCL_EMA)
         & (de < EXT_MAX_T))

    # K - REJEICAO DA BANDA. O unico uso do canal que mede positivo nas duas
    #     bases: a barra FUROU a banda de 2 ATRs com o pavio e FECHOU DE VOLTA
    #     para dentro, com o gatilho contra o furo. Nao e "preco na banda"
    #     (isso mede negativo -- ver a secao do canal): e a banda REJEITADA.
    H = d.H.to_numpy(float)
    L = d.L.to_numpy(float)
    furou = np.where(sig == -1, H >= d.k2s.to_numpy(float),
                     np.where(sig == 1, L <= d.k2i.to_numpy(float), False))
    K = ok & (sig != 0) & furou & (zona == 0) & (de < 0) & ~plana

    # KB - a leitura CLASSICA da banda, so para a medicao: preco parado na
    #      zona de esticamento (BANDA_K = 1 da banda de 2 para fora, 2 = so
    #      alem de 3) e gatilho contra. Mede negativo -- ver o relatorio.
    KB = ok & (sig != 0) & (zona >= BANDA_K) & (de < 0)

    marca = np.array([''] * n, dtype=object)
    mapa = {'D': D, 'T': T, 'K': K, 'KB': KB}
    for nome in reversed(PRIORIDADE):          # o primeiro da tupla sobrescreve
        if nome in ativos:
            marca = np.where(mapa[nome], nome, marca)
    return marca


# ================================================================== execucao
def parcial_pts(stop_pts):
    """A distancia da parcial, em pontos. None = na distancia do stop."""
    return float(stop_pts if PARCIAL_EM is None else PARCIAL_EM)


def stop_pos_parcial(ent, s, parcial, stop_ini):
    """Onde vai o stop do restante depois da parcial.

    'media' = media da operacao: o que ja foi realizado na parcial cancela
    exatamente a perda do restante. Com meia posicao e a parcial na
    distancia do stop, esse preco E o stop inicial -- o stop nao anda, e o
    desfecho 'zero' e zero de verdade.
    """
    if STOP_APOS_PARCIAL == 'entrada':
        alvo_stop = ent
    else:
        alvo_stop = ent - s * (FRAC_PARCIAL * parcial) / (1.0 - FRAC_PARCIAL)
    return max(stop_ini, alvo_stop) if s == 1 else min(stop_ini, alvo_stop)


def dimensiona(atr_i):
    """Stop e alvo em pontos para o sinal desta barra.

    Duas escolhas independentes. O stop pode ser fixo em pontos ou um
    multiplo do ATR da barra do sinal; o alvo pode ser fixo, um multiplo do
    stop (R) ou um multiplo do ATR. A medicao da secao 9 do relatorio diz
    qual combinacao mede melhor -- e ela nao e a que este projeto herdou.
    """
    if STOP_MODO == 'atr':
        st = float(np.clip(STOP_ATR * atr_i, STOP_MIN, STOP_MAX))
    else:
        st = float(STOP)
    if ALVO_MODO == 'R':
        al = ALVO_R * st
    elif ALVO_MODO == 'atr':
        al = float(ALVO_ATR * atr_i)
    else:
        al = float(ALVO)
    return st, al


def _simula_trade(H, L, C, dia, n, i, s, entrada, max_fill, stop_pts, alvo_pts):
    """Um trade. Devolve dict ou None se a ordem nao foi preenchida.

    Gestao SEMPRE a partir da barra SEGUINTE a da entrada. Quando stop e
    alvo cabem na mesma barra, assume-se o STOP.
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

    parcial = parcial_pts(stop_pts)
    stop_ini = ent - s * stop_pts
    stop_p = stop_ini
    parc_p = ent + s * parcial
    alvo_p = ent + s * alvo_pts

    fase = 1          # 1 = posicao cheia | 2 = depois da parcial
    pnl = 0.0
    res = 'fim'
    k = jf
    ult = jf
    barras = 0
    for k in range(jf + 1, n):
        if dia[k] != dia[i]:
            k = ult   # o laco quebrou na 1a barra do pregao SEGUINTE
            break
        ult = k
        barras += 1
        hit_s = (L[k] <= stop_p) if s == 1 else (H[k] >= stop_p)
        if fase == 1:
            hit_p = (H[k] >= parc_p) if s == 1 else (L[k] <= parc_p)
            if hit_s:                                  # pessimista: stop primeiro
                pnl = -stop_pts
                res = 'stop'
                break
            if hit_p:
                pnl = FRAC_PARCIAL * parcial
                fase = 2
                stop_p = stop_pos_parcial(ent, s, parcial, stop_ini)
                hit_a = (H[k] >= alvo_p) if s == 1 else (L[k] <= alvo_p)
                if hit_a:
                    pnl += (1 - FRAC_PARCIAL) * alvo_pts
                    res = 'alvo'
                    break
                continue
        else:
            hit_a = (H[k] >= alvo_p) if s == 1 else (L[k] <= alvo_p)
            if hit_s:
                pnl += (1 - FRAC_PARCIAL) * s * (stop_p - ent)
                res = 'zero'
                break
            if hit_a:
                pnl += (1 - FRAC_PARCIAL) * alvo_pts
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
                pnl=pnl - CUSTO_PTS, dia=dia[i], barras=barras,
                stop_pts=round(stop_pts, 1), alvo_pts=round(alvo_pts, 1))


def roda(d, marca, sig, entrada=ENTRADA, carteira=True, setup=None,
         max_fill=MAX_BARRAS_FILL):
    """Roda os trades.

    carteira=True  -> uma posicao por vez (o realista).
    carteira=False -> cada sinal medido isoladamente.
    """
    H, L, C = (d[c].to_numpy(float) for c in ('H', 'L', 'C'))
    A = d['atr'].to_numpy(float)
    dia = d.dia.to_numpy()
    n = len(d)

    alvos = np.flatnonzero((marca != '') if setup is None else (marca == setup))
    trades = []
    livre_em = -1
    for i in alvos:
        if carteira and i < livre_em:
            continue
        st_pts, al_pts = dimensiona(A[i])
        t = _simula_trade(H, L, C, dia, n, i, int(sig[i]), entrada, max_fill,
                          st_pts, al_pts)
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


def prepara(nome, ativos=None, nivel=None):
    """Carga + indicador + contexto + gatilho + setups, de uma vez."""
    d = contexto(indicador(carrega(ARQUIVOS[nome])))
    sig = gatilho(d, nivel)
    marca = setups(d, sig, ativos)
    return d, sig, marca
