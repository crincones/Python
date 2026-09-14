# -*- coding: utf-8 -*-
"""
Atributos novos para os sinais: FLUXO (agressao/tempo) e FORCA DE TENDENCIA.

Tudo aqui e medido ate a barra `g` -- a barra em cujo fechamento a decisao
e tomada -- e nada depois dela entra. E a mesma disciplina de engine.sinais().

--------------------------------------------------------------------- FLUXO
Vem de WINFUT_20PI_Agr_Tempo.csv (ver fluxo.py):

  agr_des   desequilibrio agressor da barra, (compra-venda)/(compra+venda).
            Em [-1,+1]. Medido NA barra de continuacao e na de retracao.
  absorcao  a barra fechou a favor mas quem agrediu foi o outro lado.
            Num grafico PI isso e comprador batendo em oferta que aguenta:
            o preco anda os 100 pts obrigatorios, mas o fluxo nao confirma.
  vel       pontos por segundo. O corpo do PI e sempre 100 pts, entao
            100/duracao e diretamente comparavel entre barras -- e a unica
            medida de PRESSA que um grafico de PI aceita.
  vel_r     velocidade da continuacao dividida pela da retracao.
  vol_r     volume da barra sobre a mediana das 50 anteriores.

------------------------------------------------------- FORCA DE TENDENCIA
O grafico de PI da uma medida de eficiencia quase de graca. Toda barra
fecha exatamente 100 pontos da sua abertura, entao a soma dos deslocamentos
absolutos de N barras e sempre N*100, e a razao de eficiencia de Kaufman

    ER = |c[g] - c[g-N]| / soma|dc|   vira   |c[g] - c[g-N]| / (N*100)

com sinal, na direcao do trade:

  er_N      (c[g] - c[g-N]) * lado / (N*100),  em [-1, +1]
            +1 = N barras seguidas a favor, sem uma unica contra
             0 = vaivem, preco no mesmo lugar
            -1 = N barras seguidas CONTRA -- e o trade contra-tendencia

  barras_cruz   ha quantas barras o fechamento esta do mesmo lado da EMA 21
  cruz_favor    esse lado e o lado do trade?
  forca_cruz    deslocamento, em ATRs, desde a barra do cruzamento. E o
                "atravessou de forma contundente" -- cruzamento que anda
                pouco e ruido, cruzamento que anda muito e mudanca de mao.
  lado_ema      o fechamento esta do lado do trade em relacao a EMA 21?
"""
import numpy as np
import pandas as pd

JAN_ER = (10, 20, 30, 50)      # janelas da razao de eficiencia
JAN_VOL = 50                   # janela da mediana de volume


def contexto(d):
    """Series por BARRA (independem do lado do trade). Devolve um dict."""
    c = d['c'].to_numpy(dtype=float)
    em = d['ema'].to_numpy(dtype=float)
    at = d['atr'].to_numpy(dtype=float)
    n = len(d)

    ctx = {}

    # --- razao de eficiencia, sem sinal ainda -------------------------
    for N in JAN_ER:
        desl = np.full(n, np.nan)
        desl[N:] = (c[N:] - c[:-N]) / (N * 100.0)
        ctx['er%d' % N] = desl

    # --- de que lado da EMA 21 esta o fechamento, e ha quanto tempo ---
    lado_ema = np.sign(c - em)
    lado_ema[np.isnan(em)] = 0
    idade = np.zeros(n, dtype=int)
    i_cruz = np.zeros(n, dtype=int)
    for i in range(1, n):
        if lado_ema[i] != 0 and lado_ema[i] == lado_ema[i - 1]:
            idade[i] = idade[i - 1] + 1
            i_cruz[i] = i_cruz[i - 1]
        else:
            idade[i] = 0
            i_cruz[i] = i
    ctx['lado_ema'] = lado_ema
    ctx['barras_cruz'] = idade
    ctx['i_cruz'] = i_cruz

    # --- o quanto o preco andou desde o cruzamento, em ATRs -----------
    #  Medido do fechamento da barra ANTERIOR ao cruzamento ate agora: e o
    #  tamanho da perna nova. Nada do futuro entra -- i_cruz <= i sempre.
    base = c[np.maximum(i_cruz - 1, 0)]
    with np.errstate(invalid='ignore', divide='ignore'):
        ctx['forca_cruz'] = (c - base) / at
    return ctx


def fluxo_barra(d):
    """Series de fluxo por barra, ja normalizadas."""
    f = {}
    f['agr_des'] = d['agr_des'].to_numpy(dtype=float)
    f['vel'] = d['vel'].to_numpy(dtype=float)
    f['dur_s'] = d['dur_s'].to_numpy(dtype=float)
    q = d['qtd'].astype(float)
    med = q.rolling(JAN_VOL, min_periods=10).median()
    f['vol_r'] = (q / med.replace(0, np.nan)).to_numpy()
    return f


def anexa_sinais(sig, d, antecipado=False):
    """Acrescenta as colunas novas a tabela de sinais.

    `i` na tabela e a barra `g` da engine: a de CONTINUACAO no modo
    confirmado, a ultima da RETRACAO no antecipado. A barra de retracao
    e, portanto, i-1 no confirmado e o proprio i no antecipado.
    """
    ctx = contexto(d)
    fl = fluxo_barra(d)
    sig = sig.copy()
    i = sig['i'].to_numpy(dtype=int)
    lado = sig['lado'].to_numpy(dtype=int)
    i_ret = i if antecipado else i - 1

    # ---------------------------------------------------------- tendencia
    for N in JAN_ER:
        sig['er%d' % N] = ctx['er%d' % N][i] * lado
    sig['lado_ema'] = ctx['lado_ema'][i] * lado          # +1 = a favor
    sig['barras_cruz'] = ctx['barras_cruz'][i]
    sig['forca_cruz'] = ctx['forca_cruz'][i] * lado
    sig['cruz_favor'] = sig['lado_ema'] > 0

    # -------------------------------------------------------------- fluxo
    sig['agr_cont'] = fl['agr_des'][i] * lado            # +1 = a favor
    sig['agr_ret'] = fl['agr_des'][i_ret] * lado         # <0 = retracao vendida
    sig['vel_cont'] = fl['vel'][i]
    sig['vel_ret'] = fl['vel'][i_ret]
    with np.errstate(invalid='ignore', divide='ignore'):
        sig['vel_r'] = np.where(fl['vel'][i_ret] > 0,
                                fl['vel'][i] / fl['vel'][i_ret], np.nan)
    sig['dur_cont'] = fl['dur_s'][i]
    sig['dur_ret'] = fl['dur_s'][i_ret]
    sig['vol_cont'] = fl['vol_r'][i]
    sig['vol_ret'] = fl['vol_r'][i_ret]
    # absorcao: a barra andou a favor mas o fluxo agrediu contra
    sig['absorcao'] = sig['agr_cont'] < 0

    # agressao acumulada da RETRACAO inteira (n_ret barras ate i_ret)
    acu = np.full(len(sig), np.nan)
    ag = d['agr_liq'].to_numpy(dtype=float)
    tot = (d['agr_c'] + d['agr_v']).to_numpy(dtype=float)
    n_ret = sig['n_ret'].to_numpy(dtype=int)
    for k in range(len(sig)):
        a = i_ret[k] - n_ret[k] + 1
        if a < 0:
            continue
        s_liq = ag[a:i_ret[k] + 1].sum()
        s_tot = tot[a:i_ret[k] + 1].sum()
        acu[k] = (s_liq / s_tot * lado[k]) if s_tot > 0 else 0.0
    sig['agr_ret_acu'] = acu
    return sig


# colunas medidas NO CANDLE DE CONTINUACAO -- nao existem ainda na hora da
# decisao do modo antecipado, entao nao podem virar filtro la.
SO_CONFIRMADO = ('agr_cont', 'vel_cont', 'dur_cont', 'vol_cont',
                 'absorcao', 'vel_r')
