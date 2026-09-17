# -*- coding: utf-8 -*-
"""
Engine de backtest - Estrategia EMA21 (ponto de virada na EMA 21) no grafico PI.

Base: WINFUT/WINFUT_20PI_Robo.csv -- grafico de 20 PI da Nelogica,
      06/03 a 14/09/2026, 132 pregoes, 50.611 candles. Todo candle tem
      corpo de exatamente 100 pontos; o que varia sao os pavios e o tempo
      de formacao.

Indicadores (CLAUDE.md):
  EMA 21                      tendencia de curto prazo / nivel do recuo
  Hull 50                     sentido do movimento (a favor = inclinada)
  MACD 9/14, sinal 9          regime: acima de zero compra, abaixo vende
  Bollinger 1000 / 1,0 desvio sobre o MACD (so desenho e filtro testado)
  Keltner 21 / 2,5            EMA 21 +- 2,5 x media (EMA 21) do range maxima-minima,
                              como o KeltnerCH da Nelogica; so desenho e estudo de impulso
  HullRetracao_Azul.ntsl      o TRIGGER

Regra (compra; venda e o espelho):
  g = candle do trigger, avaliado no FECHAMENTO.
  1. trigger HullRetracao_Azul: hma[g] > hma[g-1], g fecha em alta, e
     antes dele N candles seguidos de baixa no mesmo pregao
     (N entre BARRAS_MIN e BARRAS_MAX); opcionalmente pavio do fechamento
     <= PAVIO_FECH_PCT do corpo.
  2. ponto de virada em contato com a EMA 21: algum dos candles da virada
     (os N contra + o trigger) tem minima <= EMA21 <= maxima, com
     tolerancia TOL_EMA (15 pts: o T1 rotulado de 14/09 09:53 ficou a 12).
  3. MACD > 0 no fechamento de g.
  4. Classificacao (Hull x candle do trigger):
       T1 -> a Hull toca o candle, ou esta ABAIXO dele
       T2 -> a Hull esta ACIMA da maxima do candle

Tudo o que nao e regra (filtros candidatos do CLAUDE.md) e MEDIDO e
devolvido como coluna. Nada posterior ao fechamento de g entra na decisao.
"""
import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
ARQUIVO = os.path.join(BASE, 'WINFUT', 'WINFUT_20PI_Robo.csv')

VAL_PONTO = 0.20        # R$ por ponto, 1 contrato WIN
CONTRATOS = 6
CUSTO_CONTRATO = 0.50   # R$ round turn por contrato
PI = 100.0

EMA_PER = 21
HMA_PER = 50
MACD_R, MACD_L, MACD_S = 9, 14, 9
BB_PER, BB_DESV = 1000, 1.0
KC_PER, KC_DESV = 21, 2.5


# ================================================================== dados
def carrega(caminho=ARQUIVO):
    r = pd.read_csv(caminho)
    d = pd.DataFrame({
        'data': pd.to_datetime(r['data_hora'], format='%Y-%m-%d %H:%M'),
        'o': r['abertura'].astype(float), 'h': r['maxima'].astype(float),
        'l': r['minima'].astype(float), 'c': r['fechamento'].astype(float),
        'agr_c': r['agr_compra'].astype(float),
        'agr_v': r['agr_venda'].astype(float),
        'dur_s': r['duracao_s'].astype(float),
    })
    d['dia'] = d['data'].dt.normalize()
    return d


# ============================================================ indicadores
def _wma(x, n):
    x = np.asarray(x, dtype=float)
    w = np.arange(1, n + 1, dtype=float)
    w /= w.sum()
    out = np.full(len(x), np.nan)
    ok = ~np.isnan(x)
    if ok.sum() >= n:
        i0 = int(np.argmax(ok))
        out[i0 + n - 1:] = np.convolve(x[i0:], w[::-1], mode='valid')
    return out


def hma(x, n=HMA_PER):
    return _wma(2 * _wma(x, n // 2) - _wma(x, n), int(round(np.sqrt(n))))


def ema(x, n):
    """EMA com semente de media aritmetica (padrao Nelogica)."""
    x = np.asarray(x, dtype=float)
    out = np.full(len(x), np.nan)
    ok = ~np.isnan(x)
    if ok.sum() < n:
        return out
    i0 = int(np.argmax(ok))
    k = 2.0 / (n + 1.0)
    out[i0 + n - 1] = x[i0:i0 + n].mean()
    for i in range(i0 + n, len(x)):
        out[i] = x[i] * k + out[i - 1] * (1 - k)
    return out


def indicadores(d):
    d = d.copy()
    c = d['c'].to_numpy()
    d['ema'] = ema(c, EMA_PER)
    d['hma'] = hma(c, HMA_PER)
    m = ema(c, MACD_R) - ema(c, MACD_L)
    d['macd'] = m
    d['macd_sig'] = ema(m, MACD_S)
    s = pd.Series(m)
    mm = s.rolling(BB_PER, min_periods=BB_PER).mean()
    sd = s.rolling(BB_PER, min_periods=BB_PER).std(ddof=0)
    d['bb_sup'] = (mm + BB_DESV * sd).to_numpy()
    d['bb_inf'] = (mm - BB_DESV * sd).to_numpy()
    pc = np.r_[c[0], c[:-1]]
    h = d['h'].to_numpy(); l = d['l'].to_numpy()
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    d['atr'] = ema(tr, KC_PER)
    # Keltner da Nelogica: media movel +- desvio x MEDIA DO RANGE (maxima - minima)
    d['rng_med'] = ema(h - l, KC_PER)
    d['kc_sup'] = d['ema'] + KC_DESV * d['rng_med']
    d['kc_inf'] = d['ema'] - KC_DESV * d['rng_med']
    d['vol'] = d['agr_c'] + d['agr_v']
    return d


# ================================================================ sinais
def _hora_dow(ts):
    """Abertura da NYSE (9:30 ET) em horario de Brasilia.
    EUA em horario de verao de 08/03 a 01/11/2026 -> 10:30; fora -> 11:30."""
    t = pd.Timestamp(ts)
    verao = pd.Timestamp('2026-03-08') <= t.normalize() < pd.Timestamp('2026-11-01')
    return 10.5 if verao else 11.5


def sinais(d, barras_min=2, barras_max=3, pavio_fech_pct=10, tol_ema=15.0,
           exige_ema=True, exige_macd=True):
    """Todos os triggers + atributos. `pavio_fech_pct=None` desliga o corte
    de pavio do indicador. `tol_ema` aceita 'quase toque' (pontos)."""
    o = d['o'].to_numpy(); h = d['h'].to_numpy()
    l = d['l'].to_numpy(); c = d['c'].to_numpy()
    em = d['ema'].to_numpy(); hu = d['hma'].to_numpy()
    mc = d['macd'].to_numpy(); ms = d['macd_sig'].to_numpy()
    bs = d['bb_sup'].to_numpy(); bi = d['bb_inf'].to_numpy()
    at = d['atr'].to_numpy()
    vol = d['vol'].to_numpy(); sal = (d['agr_c'] - d['agr_v']).to_numpy()
    dur = d['dur_s'].to_numpy()
    dia = d['dia'].to_numpy()
    dat = d['data']
    sent = np.sign(c - o).astype(int)
    n = len(d)

    # referencias moveis (so passado)
    vol_med = pd.Series(vol).rolling(200, min_periods=50).median().shift(1).to_numpy()
    dur_med = pd.Series(dur).rolling(200, min_periods=50).median().shift(1).to_numpy()
    ema200 = ema(c, 200)
    # abertura do pregao
    abre_dia = d.groupby('dia')['o'].transform('first').to_numpy()
    idx_dia = d.groupby('dia').cumcount().to_numpy()

    linhas = []
    ini = HMA_PER + 10
    ult_trig = {1: [], -1: []}          # (i, preco) dos triggers validos do dia
    dia_atual = None
    for g in range(ini, n):
        if dia[g] != dia_atual:
            dia_atual = dia[g]
            ult_trig = {1: [], -1: []}
        if np.isnan(hu[g - 1]) or np.isnan(mc[g]):
            continue
        lado = sent[g]
        if (hu[g] - hu[g - 1]) * lado <= 0:
            continue
        # candles contra, seguidos, no mesmo pregao
        k = 0
        while (g - k - 1 >= 0 and dia[g - k - 1] == dia[g]
               and sent[g - k - 1] == -lado and k <= barras_max):
            k += 1
        if k < barras_min or k > barras_max:
            continue
        corpo = abs(c[g] - o[g])
        pav_fech = (h[g] - c[g]) if lado > 0 else (c[g] - l[g])
        pav_abre = (o[g] - l[g]) if lado > 0 else (h[g] - o[g])
        if pavio_fech_pct is not None and pav_fech * 100 > pavio_fech_pct * corpo:
            continue
        v0 = g - k                          # primeiro candle da virada
        js = np.arange(v0, g + 1)
        # contato com a EMA21: distancia do candle a EMA (0 = toca)
        dist_ema = np.where(em[js] > h[js], em[js] - h[js],
                            np.where(em[js] < l[js], l[js] - em[js], 0.0))
        toque = dist_ema.min()
        if exige_ema and toque > tol_ema:
            continue
        macd_ok = mc[g] * lado > 0
        if exige_macd and not macd_ok:
            continue
        # T1 / T2 -- pela Hull no candle do TRIGGER (calibrado nos 7 rotulos
        # de 14/09: e a leitura que reproduz todos). Compra: Hull acima da
        # maxima -> T2; tocando ou abaixo -> T1. Venda: espelho.
        if lado > 0:
            hull_dist = hu[g] - h[g]          # >0: Hull alem do candle (T2)
        else:
            hull_dist = l[g] - hu[g]
        tipo = 'T2' if hull_dist > 0 else 'T1'
        if lado > 0:
            hull_vir_t2 = bool(np.all(hu[js] > h[js]))
        else:
            hull_vir_t2 = bool(np.all(hu[js] < l[js]))
        a = at[g]

        # ----- atributos para filtros ------------------------------------
        ts = dat.iat[g]
        hora = ts.hour + ts.minute / 60.0
        # extremo do recuo
        ext_rec = l[js].min() if lado > 0 else h[js].max()
        # impulso antes do recuo: extremo favoravel nos 30 candles antes de v0
        j0 = max(0, v0 - 30)
        while dia[j0] != dia[g]:
            j0 += 1
        if v0 > j0:
            pico = h[j0:v0].max() if lado > 0 else l[j0:v0].min()
            impulso = (pico - ext_rec) * lado
            # novo extremo no impulso? pico recente (10 candles) vs anterior
            rec = slice(max(j0, v0 - 10), v0)
            ant = slice(j0, max(j0, v0 - 10))
            if ant.stop > ant.start:
                p_rec = h[rec].max() if lado > 0 else l[rec].min()
                p_ant = h[ant].max() if lado > 0 else l[ant].min()
                novo_ext = bool((p_rec - p_ant) * lado > 0)
            else:
                novo_ext = True
        else:
            impulso = np.nan; novo_ext = True
        # recuos anteriores a EMA no mesmo movimento (desde que o MACD
        # mudou de sinal ou desde o inicio do dia)
        m0 = g
        while m0 - 1 >= 0 and dia[m0 - 1] == dia[g] and mc[m0 - 1] * lado > 0:
            m0 -= 1
        # conta episodios de toque na EMA antes de v0 (cada sequencia de
        # candles que tocam conta como 1)
        toca = (l[m0:v0] <= em[m0:v0]) & (em[m0:v0] <= h[m0:v0])
        n_rec = int(np.sum(toca & ~np.r_[False, toca[:-1]])) if len(toca) else 0
        barras_regime = g - m0
        # picado: inversoes de sentido nos 20 candles antes do recuo
        w0 = max(idx_dia_ini := g - idx_dia[g], v0 - 20)
        ss = sent[w0:v0]
        inversoes = int(np.sum(ss[1:] != ss[:-1])) if len(ss) > 1 else 0
        jan = v0 - w0
        # segunda entrada no mesmo nivel: trigger anterior valido do dia,
        # mesmo lado, a <= 100 pts do preco
        mesmo_nivel = any(abs(p - c[g]) <= 100 and g - i <= 60
                          for i, p in ult_trig[lado])
        n_trig_dia = len(ult_trig[lado])
        ult_trig[lado].append((g, c[g]))

        linhas.append(dict(
            i=g, data=ts, lado=int(lado), tipo=tipo, n_contra=int(k), v0=int(v0),
            hora=hora, preco=c[g], o=o[g], h=h[g], l=l[g],
            ema=em[g], hma=hu[g], macd=mc[g], atr=a,
            toque_ema=float(toque),
            hull_dist=float(hull_dist), hull_vir_t2=hull_vir_t2,
            pav_fech=pav_fech, pav_abre=pav_abre, rng=h[g] - l[g],
            macd_acima_sig=bool((mc[g] - ms[g]) * lado > 0),
            macd_fora_bb=bool((mc[g] - bs[g]) > 0) if lado > 0 else bool((mc[g] - bi[g]) < 0),
            macd_norm=float(mc[g] * lado / a) if a else np.nan,
            incl_hma=float((hu[g] - hu[g - 1]) * lado),
            incl_ema=float((em[g] - em[g - 5]) * lado),
            tend_ema200=float((c[g] - ema200[g]) * lado) if not np.isnan(ema200[g]) else np.nan,
            tend_dia=float((c[g] - abre_dia[g]) * lado),
            impulso=float(impulso), novo_ext=novo_ext,
            n_rec=n_rec, barras_regime=int(barras_regime),
            inversoes=inversoes, inv_rate=inversoes / (jan - 1) if jan > 1 else np.nan,
            mesmo_nivel=bool(mesmo_nivel), n_trig_dia=n_trig_dia,
            vol_rel=float(vol[g] / vol_med[g]) if vol_med[g] else np.nan,
            vol_rec_rel=float(vol[v0:g].mean() / vol_med[g]) if vol_med[g] else np.nan,
            saldo_fav=float(sal[g] * lado),
            saldo_fav_rel=float(sal[g] * lado / vol[g]) if vol[g] else 0.0,
            saldo_rec_fav=float(sal[v0:g].sum() * lado / max(1.0, vol[v0:g].sum())),
            dur_rel=float(dur[g] / dur_med[g]) if dur_med[g] else np.nan,
            dur_rec_rel=float(dur[v0:g].mean() / dur_med[g]) if dur_med[g] else np.nan,
            dur_s_trig=float(dur[g]),
            idx_dia=int(idx_dia[g]), dow_open=_hora_dow(ts),
        ))
    s = pd.DataFrame(linhas)
    if len(s):
        s['min_dow'] = (s['hora'] - s['dow_open']) * 60
    return s


# ============================================================= simulacao
_CACHE = {}


def _arr(d):
    k = id(d)
    if k not in _CACHE:
        _CACHE.clear()
        _CACHE[k] = (d['o'].to_numpy(), d['h'].to_numpy(), d['l'].to_numpy(),
                     d['c'].to_numpy(), d['dia'].to_numpy())
    return _CACHE[k]


def _pontos(o, h, l, c):
    """Caminho dentro do candle: pavio contra primeiro."""
    return (o, l, h, c) if c >= o else (o, h, l, c)


GESTAO_PADRAO = dict(stop=100.0, alvo=300.0, parcial=True, parcial_em=100.0,
                     frac=0.5, apos='media', be_em=None, max_barras=400,
                     fecha_dia=True, atravessa=0.0)


def simula(d, i_ini, lado, p_ent, stop_pts, gestao, meio_barra=False):
    """Resolve um trade a partir do candle i_ini.

    meio_barra=False: entrada no fechamento de i_ini (nada de i_ini resta).
    meio_barra=True : entrada limitada DENTRO de i_ini; o caminho do candle
                      e percorrido a partir do ponto em que a ordem executa.
    Resultado em pontos por contrato medio (posicao inteira = 1).
    """
    G = dict(GESTAO_PADRAO); G.update(gestao or {})
    o, h, l, c, dia = _arr(d)
    n = len(o)

    p_stop = p_ent - lado * stop_pts
    p_alvo = p_ent + lado * G['alvo']
    p_parc = p_ent + lado * G['parcial_em']
    frac = G['frac']
    if G['apos'] == 'entrada':
        p_stop2 = p_ent
    else:
        p_stop2 = p_ent - lado * (frac * G['parcial_em'] / (1 - frac))
        if (p_stop2 - p_stop) * lado < 0:
            p_stop2 = p_stop
    be_em = G.get('be_em')
    atr_ = G.get('atravessa', 0.0)   # ordens limitadas: exigir o preco ALEM do nivel

    pos = 1.0; pts = 0.0; mfe = 0.0; mae = 0.0
    parc = False; s_vig = p_stop
    motivo = None; i_sai = i_ini; p_sai = p_ent
    fim = min(n - 1, i_ini + G['max_barras'])
    i = i_ini
    while i <= fim and motivo is None:
        if i > i_ini and G['fecha_dia'] and dia[i] != dia[i_ini]:
            i_sai = i - 1; p_sai = c[i - 1]; motivo = 'fim_dia'
            pts += pos * (p_sai - p_ent) * lado; pos = 0.0
            break
        pp = _pontos(o[i], h[i], l[i], c[i])
        if i == i_ini:
            if not meio_barra:
                i += 1; continue
            # a partir do primeiro ponto que alcancou o preco de entrada
            seq = []
            ativo = False
            prev = pp[0]
            for p in pp:
                if not ativo:
                    if (lado > 0 and p <= p_ent) or (lado < 0 and p >= p_ent):
                        ativo = True
                        seq.append(p)
                else:
                    seq.append(p)
                prev = p
        else:
            seq = pp[1:] if i > 0 and o[i] == c[i - 1] else pp
        prev = None
        for p in seq:
            exc = (p - p_ent) * lado
            mfe = max(mfe, exc)
            mae = min(mae, max(exc, (s_vig - p_ent) * lado))   # MEN para no stop
            if (p - s_vig) * lado <= 0:
                pts += pos * (s_vig - p_ent) * lado; pos = 0.0
                i_sai = i; p_sai = s_vig
                motivo = 'stop_zero' if parc else ('stop_be' if s_vig == p_ent else 'stop')
                break
            if G['parcial'] and not parc and (p - p_parc) * lado >= atr_:
                pts += frac * G['parcial_em']; pos -= frac; parc = True
                if (p_stop2 - s_vig) * lado > 0:
                    s_vig = p_stop2
            if be_em is not None and (p - (p_ent + lado * be_em)) * lado >= 0:
                if (p_ent - s_vig) * lado > 0:
                    s_vig = p_ent
            if (p - p_alvo) * lado >= atr_:
                pts += pos * G['alvo']; pos = 0.0
                i_sai = i; p_sai = p_alvo; motivo = 'alvo'
                break
        i += 1
    if pos > 0:
        i_sai = min(i, fim); p_sai = c[i_sai]
        pts += pos * (p_sai - p_ent) * lado
        motivo = motivo or 'tempo'
    return dict(pts=pts, mfe=mfe, mae=mae, i_sai=int(i_sai), preco_sai=p_sai,
                motivo=motivo, parcial=parc, barras=int(i_sai - i_ini))


def executa(d, sig, modo='fecha', gestao=None, validade=3):
    """Modos de entrada (CLAUDE.md, 'Sistema de entradas'):
      'fecha'   a mercado no fechamento do trigger, stop fixo (gestao['stop'])
      'meio'    limitada no meio do corpo do trigger (50 pts de recuo),
                valida por `validade` candles; stop fixo
      'extremo' a mercado no fechamento, stop no extremo oposto do trigger
    """
    G = dict(GESTAO_PADRAO); G.update(gestao or {})
    o = d['o'].to_numpy(); h = d['h'].to_numpy()
    l = d['l'].to_numpy(); c = d['c'].to_numpy()
    dia = d['dia'].to_numpy(); dat = d['data'].to_numpy()
    out = []
    for r in sig.itertuples(index=False):
        g = r.i; lado = r.lado
        base = r._asdict()
        if modo in ('fecha', 'extremo'):
            i_ent = g; p_ent = c[g]; meio = False
            stop = G['stop'] if modo == 'fecha' else \
                ((c[g] - l[g]) if lado > 0 else (h[g] - c[g]))
        elif modo == 'meio':
            p_ent = (o[g] + c[g]) / 2.0
            i_ent = None; meio = True
            for k in range(g + 1, min(len(d), g + 1 + validade)):
                if dia[k] != dia[g]:
                    break
                if (lado > 0 and l[k] <= p_ent - G['atravessa']) or                         (lado < 0 and h[k] >= p_ent + G['atravessa']):
                    i_ent = k
                    break
            stop = G['stop']
            if i_ent is None:
                base.update(aceito=False)
                out.append(base)
                continue
        else:
            raise ValueError(modo)
        res = simula(d, i_ent, lado, p_ent, stop, G, meio_barra=meio)
        base.update(aceito=True, i_ent=int(i_ent), preco_ent=float(p_ent),
                    stop_pts=float(stop), **res)
        base['dur_s'] = float((dat[res['i_sai']] - dat[i_ent]) / np.timedelta64(1, 's'))
        out.append(base)
    t = pd.DataFrame(out)
    if 'aceito' in t:
        t['aceito'] = t['aceito'].fillna(False).astype(bool)
    return t


def carteira(t):
    """Uma posicao por vez: sinais durante um trade aberto sao ignorados."""
    t = t[t['aceito']].sort_values(['i_ent', 'i']).reset_index(drop=True)
    manter = []; livre = -1
    for r in t.itertuples():
        if r.i_ent <= livre:
            continue
        manter.append(r.Index); livre = r.i_sai
    return t.loc[manter].reset_index(drop=True)


# ========================================================== financeiro
def reais(t, contratos=CONTRATOS, custo=CUSTO_CONTRATO):
    """R$ por trade com `contratos` e custo round turn por contrato.
    A parcial nao muda o custo: cada contrato faz uma ida e uma volta."""
    return t['pts'].to_numpy() * VAL_PONTO * contratos - custo * contratos


def estatisticas(t, contratos=CONTRATOS, custo=CUSTO_CONTRATO):
    n = len(t)
    if n == 0:
        return dict(trades=0)
    p = t['pts'].to_numpy(float)
    rs = reais(t, contratos, custo)
    eq = np.cumsum(rs)
    pico = np.maximum.accumulate(np.r_[0.0, eq])
    dd = pico - np.r_[0.0, eq]
    g = rs[rs > 0]; pr = rs[rs < 0]
    seq_g = seq_p = mx_g = mx_p = 0
    for x in rs:
        if x > 0:
            seq_g += 1; seq_p = 0
        else:
            seq_p += 1; seq_g = 0
        mx_g = max(mx_g, seq_g); mx_p = max(mx_p, seq_p)
    dias = t['data'].dt.normalize().nunique()
    x = np.arange(n)
    lr = float(np.corrcoef(x, eq)[0, 1]) if n > 2 and eq.std() > 0 else np.nan
    por_dia = pd.Series(rs).groupby(t['data'].dt.normalize().to_numpy()).sum()
    return dict(
        trades=n, dias=int(dias), trades_dia=n / dias,
        pts_brutos=float(p.sum()), pts_trade=float(p.mean()),
        liquido=float(rs.sum()), bruto_ganho=float(g.sum()), bruto_perda=float(pr.sum()),
        custo=float(custo * contratos * n),
        fator_lucro=float(g.sum() / -pr.sum()) if len(pr) else float('inf'),
        payoff=float(g.mean() / -pr.mean()) if len(g) and len(pr) else np.nan,
        exp_rs=float(rs.mean()),
        winrate=float((p > 0).mean() * 100),
        zeros=int((p == 0).sum()),
        acerto_liq=float((rs > 0).mean() * 100),
        maior_ganho=float(rs.max()), maior_perda=float(rs.min()),
        media_ganho=float(g.mean()) if len(g) else 0.0,
        media_perda=float(pr.mean()) if len(pr) else 0.0,
        max_seq_ganho=mx_g, max_seq_perda=mx_p,
        dd_max=float(dd.max()),
        recovery=float(rs.sum() / dd.max()) if dd.max() > 0 else np.inf,
        sharpe=float(rs.mean() / rs.std(ddof=1)) if n > 1 and rs.std(ddof=1) > 0 else np.nan,
        lr_corr=lr,
        dias_pos=float((por_dia > 0).mean() * 100),
        pior_dia=float(por_dia.min()), melhor_dia=float(por_dia.max()),
        longs=int((t['lado'] > 0).sum()), shorts=int((t['lado'] < 0).sum()),
        longs_rs=float(rs[t['lado'].to_numpy() > 0].sum()),
        shorts_rs=float(rs[t['lado'].to_numpy() < 0].sum()),
        alvos=int((t['motivo'] == 'alvo').sum()),
        stops=int((t['motivo'] == 'stop').sum()),
        zeros_parc=int((t['motivo'] == 'stop_zero').sum()),
        fim_dia=int((t['motivo'] == 'fim_dia').sum()),
    )
