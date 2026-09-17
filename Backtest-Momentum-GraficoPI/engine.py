# -*- coding: utf-8 -*-
"""
Engine de backtest - Momentum no grafico PI (Pontos de Inversao).

Base: WINFUT/WINFUT_20PI_Robo.csv, grafico de 20 PI da Nelogica
      (06/03 a 14/09/2026, 132 pregoes; a base antiga WINFUT_20PI.csv,
      26 pregoes de ago-set, e o trecho final dela).
      20 PI = 20 ticks = 100 pontos. TODO candle fecha exatamente 100
      pontos acima ou abaixo da sua abertura, e a abertura de um candle
      e o fechamento do anterior (salvo virada de dia). O corpo, portanto,
      nao carrega informacao: o que varia de candle para candle sao os
      PAVIOS e o tempo que ele levou para se formar.

Indicadores (ver CLAUDE.md):
  Hull 50      - forca/inclinacao do movimento
  EMA 21       - tendencia; e tambem a linha do meio do Keltner
  Keltner 21   - EMA 21 +/- 2.0 ATR(21), ATR exponencial (padrao Nelogica)

Padrao procurado (compra; venda e espelho):
  uma RETRACAO (um ou mais candles contra a tendencia) seguida de um
  candle de CONTINUACAO a favor. O par retracao+continuacao precisa ter
  os dois topos acima da Hull e a EMA 21 atravessando o par.

Arquitetura
-----------
1. `sinais()` gera TODOS os candidatos com a regra-base, e mede em cada um
   uma bateria de atributos (geometria do pavio, concavidade da Hull,
   tamanho da retracao, distancia da Hull as bandas, hora, ...).
2. `simula_trade()` resolve cada candidato ISOLADAMENTE. Isso da o valor
   esperado limpo de cada sinal, que e o que permite comparar filtros sem
   o ruido de quem roubou a vaga de quem.
3. `carteira()` monta a sequencia real, uma posicao por vez, ja com o
   filtro escolhido. E dela que saem a curva de capital e as estatisticas
   no padrao MetaTrader 5.
"""
import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(BASE, 'WINFUT')
ARQUIVO = os.path.join(DADOS, 'WINFUT_20PI_Robo.csv')
ARQUIVO_ANTIGO = os.path.join(DADOS, 'WINFUT_20PI.csv')   # 26 pregoes, ago-set/2026

# ------------------------------------------------------------- instrumento
TICK = 5.0             # tick do WIN, em pontos
VAL_PONTO = 0.20       # R$ por ponto, 1 contrato WIN
PI_PONTOS = 100.0      # corpo do candle no grafico de 20 PI

# ------------------------------------------------------------- indicadores
EMA_PER = 21           # media do meio do Keltner -- restricao do CLAUDE.md
HMA_PER = 50           # Hull
ATR_PER = 21           # janela do ATR que dimensiona o canal
KELT_DESV = 2.0        # largura do canal, em ATRs

# --------------------------------------------------------------- execucao
# As duas alternativas do CLAUDE.md -- "no meio do corpo" ou "no
# fechamento" -- viram TRES modos, porque "no meio do corpo" e ambiguo e
# as duas leituras possiveis nao custam a mesma coisa:
#
# 'fecha'     entrada a mercado no fechamento do candle de continuacao.
#             Sinal 100% confirmado.
# 'meio_lim'  ordem LIMITADA no meio do corpo do candle de continuacao,
#             colocada DEPOIS que ele fecha, valida por MAX_BARRAS_FILL
#             barras. Mesmo sinal do 'fecha', 50 pontos mais barato, mas
#             so entra se o preco voltar -- e quando nao volta, perde o
#             movimento inteiro.
# 'antecipa'  ordem STOP no meio do corpo, colocada assim que a RETRACAO
#             fecha, 50 pontos acima dela. Dispara antes de existir candle
#             de continuacao. Tem preco de entrada igual ao do 'meio_lim'
#             e preenche quase sempre -- em troca entra tambem nos candles
#             que sobem 50 pontos e desabam, que os outros dois modos nem
#             chegam a ver. Exige um conjunto PROPRIO de sinais, medido
#             so com o que existia no fechamento da retracao.
#
# ATENCAO: a versao ingenua de 'antecipa' -- pegar os sinais confirmados e
# so trocar o preco de entrada pelo meio do corpo -- mede lucro enorme e e
# FALSA: antecipa apenas nos candles que ja se sabe que deram certo.
ENTRADA = 'fecha'
MAX_BARRAS_FILL = 1

# ---------------------------------------------------------------- gestao
STOP = 100.0           # stop inicial, em pontos
ALVO = 300.0           # alvo final, em pontos
PARCIAL = True         # sai 50% em +100 levando o stop para a media
PARCIAL_EM = 100.0
FRAC_PARCIAL = 0.50
# Onde fica o stop do RESTANTE depois da parcial:
#   'media'    no preco em que o lucro ja realizado na parcial cancela
#              exatamente a perda do restante -- a "media da operacao".
#              Com meia posicao e a parcial a 100 pontos, esse preco fica
#              100 pontos atras da entrada, ou seja, E o stop inicial: o
#              stop nao anda, a operacao e que passou a valer ZERO ali.
#   'entrada'  no preco de entrada (leitura otimista: o desfecho "zero"
#              ainda paga metade da parcial).
STOP_APOS_PARCIAL = 'media'
CUSTO_PTS = 0.0        # custo de ida e volta, em pontos (0 = bruto)

# ------------------------------------------------------------- horizonte
MAX_BARRAS = 120       # timeout do trade, em candles
FECHA_NO_DIA = True    # zera no ultimo candle do dia (day trade)


# ============================================================ carga de dados
def carrega(caminho=None):
    """Le a base e devolve em ordem cronologica.

    Dois formatos:

    * WINFUT_20PI_Robo.csv (padrao) -- gerado por Robo-NTSL/estrutura_export.py
      a partir do log do robo. Uma linha por candle, ja em ordem de
      CurrentBar, com agressao e duracao. A hora vem so ate o minuto (o
      NTSL nao da segundos). Nao traz a EMA da Nelogica: `ema_nl` sai NaN.
    * WINFUT_20PI.csv (base antiga) -- exportacao direta do Profit, do mais
      novo para o mais antigo, TAB, virgula decimal, com a EMA 21 da propria
      Nelogica para conferencia.

    A variavel de ambiente WINFUT_BASE troca o arquivo sem mexer no codigo.
    """
    caminho = caminho or os.environ.get('WINFUT_BASE') or ARQUIVO
    if not os.path.isabs(caminho):
        caminho = os.path.join(DADOS, caminho)
    with open(caminho, encoding='utf-8', errors='replace') as f:
        cab = f.readline()
    if cab.startswith('barra,'):
        r = pd.read_csv(caminho)
        d = pd.DataFrame({
            'data': pd.to_datetime(r['data_hora'], format='%Y-%m-%d %H:%M'),
            'o': r['abertura'].astype(float), 'h': r['maxima'].astype(float),
            'l': r['minima'].astype(float), 'c': r['fechamento'].astype(float),
            'vwap': np.nan, 'ema_nl': np.nan,
            'agr_c': r['agr_compra'].astype(float),
            'agr_v': r['agr_venda'].astype(float),
            'dur_barra_s': r['duracao_s'].astype(float),
            'barra': r['barra'].astype(int),
        })
        # a ordem do arquivo E a cronologica (CurrentBar); ordenar por hora
        # embaralharia os candles fechados no mesmo minuto
        d = d.reset_index(drop=True)
    else:
        d = pd.read_csv(caminho, sep='\t', decimal=',', thousands='.')
        d.columns = ['data', 'o', 'h', 'l', 'c', 'vwap', 'ema_nl']
        d['data'] = pd.to_datetime(d['data'], format='%d/%m/%Y %H:%M:%S.%f')
        d = d.sort_values('data').reset_index(drop=True)
    d['dia'] = d['data'].dt.normalize()
    return d


# ============================================================== indicadores
def _wma(x, n):
    """Media movel ponderada linearmente."""
    x = np.asarray(x, dtype=float)
    w = np.arange(1, n + 1, dtype=float)
    w /= w.sum()
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        out[n - 1:] = np.convolve(x, w[::-1], mode='valid')
    return out


def hma(x, n=HMA_PER):
    """Hull Moving Average: WMA(2*WMA(n/2) - WMA(n), sqrt(n))."""
    meia = max(2, int(round(n / 2)))
    raiz = max(2, int(round(np.sqrt(n))))
    return _wma(2 * _wma(x, meia) - _wma(x, n), raiz)


def _ema(x, n):
    """EMA com semente de media aritmetica -- identica a da Nelogica.

    Conferido contra a coluna 'Media Movel E [21]' do proprio arquivo:
    bate em 9.976 dos 9.980 candles com EMA publicada, com erro maximo de
    0,004 ponto (arredondamento das duas casas do csv).
    """
    x = np.asarray(x, dtype=float)
    n_ = len(x)
    out = np.full(n_, np.nan)
    if n_ < n:
        return out
    k = 2.0 / (n + 1.0)
    out[n - 1] = x[:n].mean()
    for i in range(n, n_):
        out[i] = x[i] * k + out[i - 1] * (1 - k)
    return out


def atr(h, l, c, n=ATR_PER):
    """ATR exponencial sobre o range verdadeiro.

    No grafico PI o candle abre no fechamento do anterior, entao o range
    verdadeiro so difere do h-l na virada de dia -- mas cobre esse caso.
    """
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    return _ema(tr, n)


def indicadores(d):
    """Anexa Hull 50, EMA 21, ATR 21 e as bandas de Keltner."""
    d = d.copy()
    c = d['c'].to_numpy()
    d['hma'] = hma(c, HMA_PER)
    d['ema'] = _ema(c, EMA_PER)
    d['atr'] = atr(d['h'].to_numpy(), d['l'].to_numpy(), c, ATR_PER)
    d['kc_sup'] = d['ema'] + KELT_DESV * d['atr']
    d['kc_inf'] = d['ema'] - KELT_DESV * d['atr']
    return d


# ============================================================ geracao dos sinais
def _corridas(sentido):
    """Para cada candle, quantos candles consecutivos do MESMO sentido vem
    se fechando ate ele (inclusive)."""
    n = len(sentido)
    r = np.ones(n, dtype=int)
    for i in range(1, n):
        if sentido[i] == sentido[i - 1]:
            r[i] = r[i - 1] + 1
    return r


def sinais(d, antecipado=False):
    """Gera todos os candidatos da regra-base e mede seus atributos.

    `g` e sempre a barra em cujo FECHAMENTO a decisao e tomada, e todo
    atributo e medido ate ela. Nada que venha depois de `g` entra na
    decisao -- e o que garante que o backteste nao esta lendo o futuro.

    CONFIRMADO (antecipado=False) -- g e o candle de CONTINUACAO:

      g    fecha a favor (alta, para compra)
      g-1  fecha contra                     <- ultimo candle da retracao
      Hull ascendente        hma[g] > hma[g-1]
      Hull abaixo da maxima  hma[g] < h[g]
      os DOIS topos acima da Hull           h[g] > hma[g] e h[g-1] > hma[g-1]
      EMA 21 dentro do par   min(l) <= ema[g] <= max(h)

    ANTECIPADO (antecipado=True) -- g e o ultimo candle da RETRACAO. O
    candle de continuacao ainda nao existe; a ordem stop vai 50 pontos
    adiante do fechamento de g. Do par, so o lado da retracao e conhecido;
    do outro lado usa-se o que a ordem garante: se ela disparar, o candle
    seguinte ja tera ido de c[g] ate pelo menos c[g]+50, e so fecha a
    favor em c[g]+100.

      g    fecha contra (baixa, para compra)
      Hull ascendente        hma[g] > hma[g-1]
      topo da retracao acima da Hull        h[g] > hma[g]
      o preco da ordem tambem acima dela    c[g] + 50 > hma[g]
      EMA 21 dentro do par projetado
                             min(l[g], c[g]) <= ema[g] <= max(h[g], c[g]+100)

    Tudo o mais -- concavidade, tamanho da retracao, pavio, distancia da
    Hull as bandas, hora -- e MEDIDO e devolvido como coluna, nao filtrado.
    Os filtros sao aplicados depois, sobre a tabela pronta.
    """
    o = d['o'].to_numpy(); h = d['h'].to_numpy()
    l = d['l'].to_numpy(); c = d['c'].to_numpy()
    hu = d['hma'].to_numpy(); em = d['ema'].to_numpy()
    at = d['atr'].to_numpy()
    ks = d['kc_sup'].to_numpy(); ki = d['kc_inf'].to_numpy()
    dia = d['dia'].to_numpy()
    sent = np.sign(c - o).astype(int)
    corr = _corridas(sent)
    n = len(d)

    linhas = []
    ini = max(HMA_PER + 8, EMA_PER + 2, ATR_PER + 2)
    fim = n - 1 if antecipado else n
    for g in range(ini, fim):
        if np.isnan(hu[g]) or np.isnan(hu[g - 2]) or np.isnan(at[g]):
            continue
        for lado in (1, -1):
            meio = c[g] + lado * PI_PONTOS / 2.0

            if antecipado:
                # g e a retracao; a ordem vale para g+1
                if dia[g + 1] != dia[g]:
                    continue
                if sent[g] != -lado:
                    continue
                ext_ret = h[g] if lado > 0 else l[g]
                if (ext_ret - hu[g]) * lado <= 0:
                    continue
                if (meio - hu[g]) * lado <= 0:
                    continue
                topo = max(h[g], c[g] + lado * PI_PONTOS) if lado > 0 else \
                    max(h[g], c[g])
                fundo = min(l[g], c[g]) if lado > 0 else \
                    min(l[g], c[g] + lado * PI_PONTOS)
                if not (fundo <= em[g] <= topo):
                    continue
                i_ret = g               # candle da retracao
            else:
                # g e a continuacao; g-1 e a retracao
                if dia[g] != dia[g - 1]:
                    continue
                if sent[g] != lado or sent[g - 1] != -lado:
                    continue
                extremo = h[g] if lado > 0 else l[g]
                if (extremo - hu[g]) * lado <= 0:
                    continue
                ext_ret = h[g - 1] if lado > 0 else l[g - 1]
                if (ext_ret - hu[g - 1]) * lado <= 0:
                    continue
                topo = max(h[g], h[g - 1]); fundo = min(l[g], l[g - 1])
                if not (fundo <= em[g] <= topo):
                    continue
                i_ret = g - 1

            # --- Hull no sentido do trade (comum aos dois modos)
            incl = (hu[g] - hu[g - 1]) * lado
            if incl <= 0:
                continue

            a = at[g]
            # --- retracao: candles contra + profundidade em pontos
            n_ret = corr[i_ret]
            j = i_ret - n_ret            # ultimo candle a favor antes dela
            if j < 0:
                continue
            pico = (np.max(h[j:i_ret + 1]) if lado > 0 else
                    np.min(l[j:i_ret + 1]))
            vale = (np.min(l[i_ret - n_ret + 1:i_ret + 1]) if lado > 0 else
                    np.max(h[i_ret - n_ret + 1:i_ret + 1]))
            ret_pts = (pico - vale) * lado

            # --- geometria do candle de RETRACAO (conhecida nos dois modos)
            rng_ret = h[i_ret] - l[i_ret]
            pav_ret_con = ((h[i_ret] - o[i_ret]) if lado > 0 else
                           (o[i_ret] - l[i_ret]))

            # --- geometria do candle de CONTINUACAO (so no modo confirmado)
            if antecipado:
                rng = np.nan; pav_fav = np.nan; pav_con = np.nan
                pav_fav_r = np.nan; pav_con_r = np.nan; corpo_r = np.nan
            else:
                rng = h[g] - l[g]
                pav_fav = (h[g] - c[g]) if lado > 0 else (c[g] - l[g])
                pav_con = (o[g] - l[g]) if lado > 0 else (h[g] - o[g])
                pav_fav_r = pav_fav / rng if rng else 0.0
                pav_con_r = pav_con / rng if rng else 0.0
                corpo_r = PI_PONTOS / rng if rng else 0.0

            # --- Hull no canal (exaustao) e colada na EMA (consolidacao)
            banda = ks[g] if lado > 0 else ki[g]
            folga_banda = (banda - hu[g]) * lado / a
            dist_hma_ema = (hu[g] - em[g]) * lado / a
            colada = 0
            for k in range(g, max(ini, g - 30) - 1, -1):
                if abs(hu[k] - em[k]) / at[k] < 0.25:
                    colada += 1
                else:
                    break

            incl_ema = (em[g] - em[g - 5]) * lado / a
            incl_hma = incl / a
            curva = (hu[g] - 2 * hu[g - 1] + hu[g - 2]) * lado / a
            estic = (c[g] - em[g]) * lado / a

            ts = d['data'].iat[g]
            linhas.append(dict(
                i=g, data=ts, lado=lado,
                hora=ts.hour + ts.minute / 60.0,
                preco_fecha=c[g], preco_meio=meio,
                atr=a,
                incl_hma=incl_hma, curva=curva, concava=bool(curva > 0),
                incl_ema=incl_ema,
                folga_banda=folga_banda, dist_hma_ema=dist_hma_ema,
                barras_colada=colada, estic=estic,
                n_ret=int(n_ret), ret_pts=ret_pts, ret_atr=ret_pts / a,
                rng=rng, pav_fav=pav_fav, pav_con=pav_con,
                pav_fav_r=pav_fav_r, pav_con_r=pav_con_r, corpo_r=corpo_r,
                rng_ret=rng_ret,
                pav_ret_con_r=pav_ret_con / rng_ret if rng_ret else 0.0,
            ))
    return pd.DataFrame(linhas)


# ============================================================ simulacao
def _caminho(o, h, l, c):
    """Ordem em que os extremos do candle foram visitados.

    Convencao conservadora e coerente com a construcao do PI: o pavio
    CONTRA o sentido do candle se forma antes. Candle de alta anda
    abertura -> minima -> maxima -> fechamento; de baixa, o espelho.
    """
    return (l, h) if c >= o else (h, l)


def simula_trade(d, i_ent, lado, preco_ent, gestao=None):
    """Resolve um trade isolado, candle a candle, a partir de i_ent.

    i_ent e o candle em que a posicao foi aberta. `meio_da_barra` diz se a
    entrada aconteceu DENTRO dele (ordem stop antecipada) -- nesse caso a
    parte de tras do candle ainda vale e e percorrida. Senao a entrada foi
    no fechamento e o candio de entrada nao sobra preco nenhum.

    Devolve pontos por contrato (posicao inteira = 1), MFE/MAE, o candle e
    o preco de saida, e o motivo.
    """
    g = gestao or {}
    stop = g.get('stop', STOP); alvo = g.get('alvo', ALVO)
    parcial = g.get('parcial', PARCIAL)
    parc_em = g.get('parcial_em', PARCIAL_EM)
    frac = g.get('frac', FRAC_PARCIAL)
    apos = g.get('apos', STOP_APOS_PARCIAL)
    custo = g.get('custo', CUSTO_PTS)
    max_b = g.get('max_barras', MAX_BARRAS)
    fecha_dia = g.get('fecha_dia', FECHA_NO_DIA)
    meio_da_barra = g.get('meio_da_barra', False)

    o = d['o'].to_numpy(); h = d['h'].to_numpy()
    l = d['l'].to_numpy(); c = d['c'].to_numpy()
    dia = d['dia'].to_numpy()
    n = len(d)

    p_stop = preco_ent - lado * stop
    p_alvo = preco_ent + lado * alvo
    p_parc = preco_ent + lado * parc_em
    # stop do restante depois da parcial
    if apos == 'entrada':
        p_stop2 = preco_ent
    else:                      # 'media': o lucro da parcial zera a perda
        p_stop2 = preco_ent - lado * (frac * parc_em / (1 - frac))
        if (p_stop2 - p_stop) * lado < 0:   # nunca se afasta do stop inicial
            p_stop2 = p_stop

    pos = 1.0
    pts = 0.0
    mfe = 0.0; mae = 0.0
    saiu_parcial = False
    motivo = 'timeout'
    i_sai = i_ent; p_sai = preco_ent

    i = i_ent
    fim = min(n - 1, i_ent + max_b)
    while i <= fim:
        if i > i_ent and fecha_dia and dia[i] != dia[i_ent]:
            i_sai = i - 1; p_sai = c[i - 1]; motivo = 'fim_dia'
            pts += pos * ((p_sai - preco_ent) * lado)
            pos = 0.0
            break

        a, b = _caminho(o[i], h[i], l[i], c[i])
        if i == i_ent and meio_da_barra:
            # A ordem stop disparou na perna que vai ate o extremo A FAVOR
            # do trade. Se o candle fechou a favor, esse extremo e `b` e o
            # `a` (o pavio contra) ja tinha passado ANTES da entrada. Se o
            # candle fechou contra -- a continuacao falhou --, o extremo a
            # favor e o proprio `a`, e o resto do candio ainda vem por cima.
            visitas = [b, c[i]] if np.sign(c[i] - o[i]) == lado \
                else [a, b, c[i]]
        elif i == i_ent:
            visitas = []                     # entrou no fechamento
        else:
            visitas = [a, b, c[i]]

        for p in visitas:
            exc = (p - preco_ent) * lado
            mfe = max(mfe, exc); mae = min(mae, exc)
            s_vig = p_stop2 if saiu_parcial else p_stop
            if (p - s_vig) * lado <= 0:
                pts += pos * ((s_vig - preco_ent) * lado)
                pos = 0.0
                i_sai = i; p_sai = s_vig
                motivo = 'stop_zero' if saiu_parcial else 'stop'
                break
            if parcial and not saiu_parcial and (p - p_parc) * lado >= 0:
                pts += frac * parc_em
                pos -= frac
                saiu_parcial = True
            if (p - p_alvo) * lado >= 0:
                pts += pos * alvo
                pos = 0.0
                i_sai = i; p_sai = p_alvo; motivo = 'alvo'
                break
        if pos == 0.0:
            break
        i += 1

    if pos > 0.0:                     # timeout: zera no fechamento
        i_sai = min(i, fim); p_sai = c[i_sai]
        pts += pos * ((p_sai - preco_ent) * lado)
        motivo = 'timeout'

    return dict(i_sai=i_sai, preco_sai=p_sai, pts=pts - custo,
                mfe=mfe, mae=mae, barras=i_sai - i_ent + 1,
                motivo=motivo, parcial=saiu_parcial)


def executa(d, sig, entrada=ENTRADA, gestao=None):
    """Resolve TODOS os candidatos isoladamente, com o modo de entrada dado.

    Devolve a tabela de sinais acrescida do desfecho. Sinais que nao
    chegaram a virar posicao -- a limitada do 'meio_lim' que nao preencheu,
    a stop do 'antecipa' que o candle seguinte nao alcancou -- saem com
    aceito=False.

    O `sig` precisa ser coerente com o modo: 'fecha' e 'meio_lim' pedem
    sinais(d, antecipado=False); 'antecipa' pede sinais(d, antecipado=True).
    """
    o = d['o'].to_numpy(); h = d['h'].to_numpy()
    l = d['l'].to_numpy(); c = d['c'].to_numpy()
    dat = d['data'].to_numpy(); dia = d['dia'].to_numpy()
    g = dict(gestao or {})
    out = []
    for r in sig.itertuples(index=False):
        i = r.i; lado = r.lado
        aceito = True; meio_da_barra = False
        if entrada == 'fecha':
            i_ent = i; p_ent = c[i]
        elif entrada == 'meio_lim':
            # limitada no meio do corpo do candle de continuacao (= i),
            # colocada depois que ele fecha, valida pelas proximas barras
            p_ent = o[i] + lado * PI_PONTOS / 2.0
            i_ent = None
            for k in range(i + 1, min(len(d), i + 1 + MAX_BARRAS_FILL)):
                if dia[k] != dia[i]:
                    break
                if (lado > 0 and l[k] <= p_ent) or (lado < 0 and h[k] >= p_ent):
                    i_ent = k
                    break
            if i_ent is None:
                aceito = False
        elif entrada == 'antecipa':
            # ordem stop 50 pontos adiante do fechamento da retracao (= i),
            # valida para o candle seguinte
            i_ent = i + 1
            p_ent = c[i] + lado * PI_PONTOS / 2.0
            alcancou = (h[i_ent] >= p_ent) if lado > 0 else (l[i_ent] <= p_ent)
            if not alcancou:
                aceito = False
            meio_da_barra = True
        else:
            raise ValueError(entrada)

        base = r._asdict()
        if not aceito:
            base.update(aceito=False, i_ent=-1, preco_ent=np.nan,
                        i_sai=-1, preco_sai=np.nan, pts=np.nan,
                        mfe=np.nan, mae=np.nan, barras=np.nan,
                        motivo='sem_fill', parcial=False, dur_s=np.nan)
            out.append(base)
            continue

        gg = dict(g); gg['meio_da_barra'] = meio_da_barra
        res = simula_trade(d, i_ent, lado, p_ent, gg)
        dur = (dat[res['i_sai']] - dat[i_ent]) / np.timedelta64(1, 's')
        base.update(aceito=True, i_ent=i_ent, preco_ent=p_ent,
                    dur_s=float(dur), **res)
        out.append(base)
    t = pd.DataFrame(out)
    if len(t):
        t['data_sai'] = d['data'].to_numpy()[t['i_sai'].clip(lower=0)]
    return t

def carteira(trades, uma_por_vez=True):
    """Sequencia real: uma posicao por vez, na ordem do tempo.

    `trades` ja vem filtrado. Enquanto um trade esta aberto, os sinais que
    aparecem sao descartados -- e o que acontece de verdade na mesa.
    """
    t = trades[trades['aceito']].sort_values(['i_ent', 'i']).reset_index(drop=True)
    if not uma_por_vez or len(t) == 0:
        return t.reset_index(drop=True)
    manter = []
    livre_em = -1
    for r in t.itertuples():
        if r.i_ent <= livre_em:
            continue
        manter.append(r.Index)
        livre_em = r.i_sai
    return t.loc[manter].reset_index(drop=True)


# ============================================================ estatisticas
def _drawdown(eq):
    pico = np.maximum.accumulate(eq)
    dd = pico - eq
    return dd


def estatisticas(t, capital=0.0):
    """Bloco de estatisticas no padrao do relatorio do MetaTrader 5,
    com winrate, em PONTOS e em R$ (1 contrato WIN)."""
    n = len(t)
    if n == 0:
        return dict(trades=0)
    p = t['pts'].to_numpy(dtype=float)
    eq = np.cumsum(p)
    g = p[p > 0]; pr = p[p < 0]; z = p[p == 0]
    lucro_b = g.sum(); prej_b = pr.sum()
    dd = _drawdown(np.r_[0.0, eq])
    dd_max = dd.max()
    i_dd = int(dd.argmax())
    # drawdown relativo (em % do pico), so faz sentido com capital
    eq_rel = capital + np.r_[0.0, eq] * VAL_PONTO if capital else None

    # sequencias
    seq_g = seq_p = mx_g = mx_p = 0
    som_g = som_p = msom_g = msom_p = 0.0
    for x in p:
        if x > 0:
            seq_g += 1; som_g += x; seq_p = 0; som_p = 0.0
        elif x < 0:
            seq_p += 1; som_p += x; seq_g = 0; som_g = 0.0
        else:
            seq_g = seq_p = 0; som_g = som_p = 0.0
        mx_g = max(mx_g, seq_g); mx_p = max(mx_p, seq_p)
        msom_g = max(msom_g, som_g); msom_p = min(msom_p, som_p)

    longs = t[t['lado'] > 0]; shorts = t[t['lado'] < 0]
    def _wr(x):
        return float((x['pts'] > 0).mean() * 100) if len(x) else float('nan')

    fat = (lucro_b / abs(prej_b)) if prej_b < 0 else float('inf')
    exp_ = p.mean()
    # Sharpe por trade (padrao MT5: retorno medio / desvio, por operacao)
    sharpe = exp_ / p.std(ddof=1) if n > 1 and p.std(ddof=1) > 0 else float('nan')
    # LR correlation: aderencia da curva de capital a uma reta
    x = np.arange(1, n + 1, dtype=float)
    if n > 2 and eq.std() > 0:
        lr_corr = float(np.corrcoef(x, eq)[0, 1])
        a, b = np.polyfit(x, eq, 1)
        lr_erro = float(np.abs(eq - (a * x + b)).max())
    else:
        lr_corr = float('nan'); lr_erro = float('nan')

    dias = t['data'].dt.normalize().nunique()
    return dict(
        trades=n,
        lucro_liq=float(p.sum()), lucro_bruto=float(lucro_b),
        prej_bruto=float(prej_b),
        lucro_liq_rs=float(p.sum() * VAL_PONTO),
        fator_lucro=float(fat), exp_pts=float(exp_),
        exp_rs=float(exp_ * VAL_PONTO),
        sharpe=float(sharpe), lr_corr=lr_corr, lr_erro=lr_erro,
        winrate=float((p > 0).mean() * 100),
        zeros=int(len(z)), zeros_pct=float(len(z) / n * 100),
        vitorias=int(len(g)), derrotas=int(len(pr)),
        maior_ganho=float(g.max()) if len(g) else 0.0,
        maior_perda=float(pr.min()) if len(pr) else 0.0,
        media_ganho=float(g.mean()) if len(g) else 0.0,
        media_perda=float(pr.mean()) if len(pr) else 0.0,
        max_seq_ganho=int(mx_g), max_seq_perda=int(mx_p),
        max_soma_ganho=float(msom_g), max_soma_perda=float(msom_p),
        dd_max=float(dd_max), dd_max_rs=float(dd_max * VAL_PONTO),
        dd_idx=i_dd,
        recovery=float(p.sum() / dd_max) if dd_max > 0 else float('inf'),
        longs=int(len(longs)), longs_wr=_wr(longs),
        shorts=int(len(shorts)), shorts_wr=_wr(shorts),
        longs_pts=float(longs['pts'].sum()) if len(longs) else 0.0,
        shorts_pts=float(shorts['pts'].sum()) if len(shorts) else 0.0,
        dias=int(dias), trades_dia=float(n / dias) if dias else float('nan'),
        pts_dia=float(p.sum() / dias) if dias else float('nan'),
        dur_mediana=float(t['dur_s'].median()),
        dur_media=float(t['dur_s'].mean()),
        barras_mediana=float(t['barras'].median()),
        mfe_media=float(t['mfe'].mean()), mae_media=float(t['mae'].mean()),
        alvos=int((t['motivo'] == 'alvo').sum()),
        stops=int((t['motivo'] == 'stop').sum()),
        stops_zero=int((t['motivo'] == 'stop_zero').sum()),
        timeouts=int((t['motivo'] == 'timeout').sum()),
        fins_dia=int((t['motivo'] == 'fim_dia').sum()),
        equity=eq.tolist(),
    )
