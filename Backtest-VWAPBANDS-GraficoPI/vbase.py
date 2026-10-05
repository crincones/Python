# -*- coding: utf-8 -*-
"""
Motor do estudo de reversoes nas VWAP BANDS (grafico PI 20, WINFUT).

Historico: WINFUT_20PI/WINFUT_20PI.csv, exportado pelo Robo-NTSL/LogVWAP_Console.ntsl
(decodificado por Robo-NTSL/decodifica_vwap.py em WINFUT_20PI_decod.csv). Mesmos candles
da base do Backtest-Momentum2-GraficoPI (conferidos 1 a 1 nos 127 pregoes em comum),
mais volume financeiro e quantidade de cada candle. Pregao em andamento (ultimo dia,
incompleto) e o candle solto do dia anterior ao primeiro pregao ficam fora.
Indicadores (EMA 21, Hull 50, MACD) vem do engine.py de la, sem copia.

VWAP Band da Nelogica (periodo Diario, preco tipico "Media financeira"):
  preco         Media financeira do candle = Volume / Quantity / 0,20 (R$ por ponto do WIN)
  peso          Quantity (contratos negociados; ~1,34x a agressao compra + venda)
  VWAP          soma(preco * qtd) / soma(qtd), zerada todo pregao
  bandas        ENVELOPES PERCENTUAIS da VWAP: VWAP * (1 +- k/300), k = 1, 2, 3
                (1/3 %, 2/3 % e 1 %; o artigo da Nelogica arredonda para 0,33 / 0,66 / 0,99 %)
  passo         PASSO = VWAP / 300 (~625 pts no WIN a 187.000), guardado na coluna 'sd'
                para o resto do codigo: banda k = VWAP +- k * sd

Conferido: artigo da Nelogica (WDO 24/04, VWAP 5.013,592 -> bandas 5.030,30 / 5.047,01 /
5.063,73 e 4.996,88 / 4.980,17 / 4.963,46, exatamente VWAP*(1 +- k/300)) e print do Profit
de 16/09 no WIN (exemplo.md: VWAP 187.746, +1 188.371, -1 187.120; aqui 187.746 / 188.372 /
187.120). As bandas sao paralelas a VWAP porque sao percentuais, nao por redesenho.
BANDA = 'desvio' (desvio-padrao ponderado acumulado no dia, a versao anterior e errada deste
estudo) ficou so para comparacao.
O valor do candle i inclui o proprio candle (e o que o grafico mostra no
fechamento dele). Nada posterior ao fechamento do sinal entra na decisao.

Distancia em passos de banda:  z = (preco - VWAP) / passo  (z = 1 esta na banda 1).
Venda nas bandas de cima (z >= 1, 2, 3), compra nas de baixo -- espelho.
"""
import os
import sys
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
ORIGEM = os.path.join(os.path.dirname(BASE), 'Backtest-Momentum2-GraficoPI')
sys.path.insert(0, ORIGEM)
import engine as E  # noqa: E402

VAL_PONTO = E.VAL_PONTO
CONTRATOS = E.CONTRATOS
CUSTO_CONTRATO = E.CUSTO_CONTRATO

INICIO = 9.0            # sinais e toques desde a abertura (com o envelope a banda ja vale no 1o candle;
                        # o aquecimento de 09:15 so existia para o desvio-padrao, que comecava em zero)
ANG_N = 10              # janela do angulo da VWAP (candles)
BANDA = 'envelope'     # 'envelope' (VWAP Band do Profit) | 'desvio' (so comparacao)
PASSO = 1.0 / 300.0    # distancia entre bandas, em fracao da VWAP
ARQ = os.path.join(BASE, 'WINFUT_20PI', 'WINFUT_20PI_decod.csv')


# ================================================================== dados
def carrega(banda=None):
    r = pd.read_csv(ARQ)
    dias = r.groupby('data').size()
    fora = [dias.index[0]] if dias.iloc[0] < 50 else []          # candle solto antes do 1o pregao
    if r['hora'].iloc[-1] < '18:00':
        fora.append(dias.index[-1])                                # pregao em andamento
    r = r[~r['data'].isin(fora)].reset_index(drop=True)
    d = pd.DataFrame({
        'data': pd.to_datetime(r['data_hora'], format='%Y-%m-%d %H:%M'),
        'o': r['abertura'].astype(float), 'h': r['maxima'].astype(float),
        'l': r['minima'].astype(float), 'c': r['fechamento'].astype(float),
        'agr_c': r['agr_compra'].astype(float), 'agr_v': r['agr_venda'].astype(float),
        'dur_s': r['duracao_s'].astype(float),
        'qtd': r['quantidade'].astype(float), 'pm': r['preco_medio'].astype(float) / VAL_PONTO,
    })
    d['dia'] = d['data'].dt.normalize()
    d = E.indicadores(d)
    return vwap(d, banda or BANDA)


def vwap(d, banda='envelope'):
    d = d.copy()
    ok = (d['qtd'] > 0) & (d['pm'] >= d['l'] - 1) & (d['pm'] <= d['h'] + 1)
    tp = d['pm'].where(ok, (d['h'] + d['l'] + d['c']) / 3.0)      # candle sem negocio: (H+L+C)/3
    v = d['qtd'].clip(lower=1.0)
    g = d['dia']
    sv = v.groupby(g).cumsum()
    vw = (tp * v).groupby(g).cumsum() / sv
    if banda == 'envelope':
        sd = vw * PASSO
    elif banda == 'desvio':
        var = (tp * tp * v).groupby(g).cumsum() / sv - vw * vw
        sd = np.sqrt(var.clip(lower=0.0))
    else:
        raise ValueError(banda)
    d['vwap'] = vw.to_numpy()
    d['sd'] = sd.to_numpy()
    d.attrs['banda'] = banda
    for k in (1, 2, 3):
        d[f'up{k}'] = d['vwap'] + k * d['sd']
        d[f'dn{k}'] = d['vwap'] - k * d['sd']
    d['idx_dia'] = d.groupby('dia').cumcount()
    d['frio'] = (d['data'].dt.hour + d['data'].dt.minute / 60.0) < INICIO
    return d


# ======================================================== toques nas bandas
def prepara_toques(d, reset='interna'):
    """z do candle nas duas direcoes + episodios. lado da operacao:
    -1 = venda na banda de cima (preco subiu ate ela), +1 = compra na de baixo.
    reset: 'interna' = o toque na banda k termina quando o preco volta ate a
    banda k-1 (banda 1: ate a VWAP); 'vwap' = so termina quando volta a VWAP."""
    vw = d['vwap'].to_numpy(); sd = d['sd'].to_numpy()
    sdx = np.where(sd > 0, sd, np.nan)
    z_up = (d['h'].to_numpy() - vw) / sdx      # excursao para cima
    z_dn = (vw - d['l'].to_numpy()) / sdx      # excursao para baixo
    # "voltar para dentro" e medido pela minima (topo) / maxima (fundo) do candle
    z_up_min = (d['l'].to_numpy() - vw) / sdx
    z_dn_min = (vw - d['h'].to_numpy()) / sdx
    dia = d['dia'].to_numpy()
    # candles antes de INICIO nao abrem episodio (INICIO = abertura: nenhum fica de fora)
    frio = d['frio'].to_numpy()
    z_up = np.where(frio, np.nan, z_up); z_dn = np.where(frio, np.nan, z_dn)
    T = {}
    for lado, ze, zr in ((-1, z_up, z_up_min), (1, z_dn, z_dn_min)):
        for k in (1, 2, 3):
            T[(lado, k)] = _ep2(ze, zr, dia, k, 0.0 if reset == 'vwap' else k - 1.0)
    return dict(z_up=z_up, z_dn=z_dn, ep=T)


def _ep2(z_ext, z_rec, dia, k, volta):
    n = len(z_ext)
    ep = np.zeros(n, int)
    cont = 0; ativo = False; d0 = None
    for i in range(n):
        if dia[i] != d0:
            d0 = dia[i]; cont = 0; ativo = False
        if np.isnan(z_ext[i]):
            continue
        if ativo and z_rec[i] <= volta:
            ativo = False
        if not ativo and z_ext[i] >= k:
            ativo = True; cont += 1
        ep[i] = cont if ativo else 0
    return ep


# ================================================================ sinais
GATILHOS = {
    'c1': '1o candle contra',
    'c2': '2o candle contra (confirmacao)',
    'hull': 'Hull 50 vira contra',
}


def sinais(d, T, gatilho='c1', alvo='banda', janela_hull=8, z_min=1.0):
    """Reversoes nas bandas (alvo='banda') ou na propria VWAP (alvo='vwap').

    gatilho, avaliado no FECHAMENTO do candle g (venda; compra e espelho):
      c1   g fecha em baixa e g-1 fechou em alta: primeiro candle contra
           depois de um empurrao de k >= 1 candles de alta
      c2   g e g-1 fecham em baixa e g-2 em alta
      hull a Hull 50 vira para baixo em g (hma[g] < hma[g-1] >= hma[g-2])
           com a maxima dos ultimos `janela_hull` candles na banda

    Empurrao = candles de alta seguidos antes do(s) contra; o extremo do
    movimento e a maior maxima do empurrao + candles contra. Para as bandas
    o extremo tem de ter chegado a banda 1 (z >= z_min = 1; o controle sem
    banda usa z_min = -inf); para a VWAP o empurrao
    tem de ter comecado do lado de fora e o extremo encostado na VWAP
    (venda: preco vindo de baixo toca a VWAP por baixo e vira para baixo).
    """
    o = d['o'].to_numpy(); h = d['h'].to_numpy(); l = d['l'].to_numpy(); c = d['c'].to_numpy()
    vw = d['vwap'].to_numpy(); sd = d['sd'].to_numpy()
    hu = d['hma'].to_numpy(); mc = d['macd'].to_numpy(); em = d['ema'].to_numpy()
    vol = d['vol'].to_numpy(); sal = (d['agr_c'] - d['agr_v']).to_numpy(); dur = d['dur_s'].to_numpy()
    dia = d['dia'].to_numpy(); idd = d['idx_dia'].to_numpy(); dat = d['data']
    sent = np.sign(c - o).astype(int)
    n = len(d)
    abre = d.groupby('dia')['o'].transform('first').to_numpy()
    vol_med = pd.Series(vol).rolling(200, min_periods=50).median().shift(1).to_numpy()
    dur_med = pd.Series(dur).rolling(200, min_periods=50).median().shift(1).to_numpy()
    zx = {-1: T['z_up'], 1: T['z_dn']}          # excursao na direcao da banda (venda: para cima)
    linhas = []
    hist = {}                                  # (dia, lado) -> sinais anteriores (g, j_ext, extremo, z)
    frio = d['frio'].to_numpy()
    for g in range(3, n):
        if frio[g] or not sd[g] > 0:
            continue
        for lado in (-1, 1):
            # lado = direcao da OPERACAO. Venda (lado -1): preco subiu ate a banda.
            contra = lado            # sentido dos candles do gatilho (venda: candles de baixa = -1)
            fav = -lado              # sentido do empurrao
            if gatilho == 'c1':
                if not (sent[g] == contra and sent[g - 1] == fav):
                    continue
                fim_emp = g - 1; nc = 1
            elif gatilho == 'c2':
                if not (sent[g] == contra and sent[g - 1] == contra and sent[g - 2] == fav):
                    continue
                if dia[g - 2] != dia[g]:
                    continue
                fim_emp = g - 2; nc = 2
            else:
                if np.isnan(hu[g - 2]):
                    continue
                if not ((hu[g] - hu[g - 1]) * lado > 0 and (hu[g - 1] - hu[g - 2]) * lado <= 0):
                    continue
                fim_emp = None; nc = 0
            if gatilho in ('c1', 'c2'):
                k = 0
                while fim_emp - k >= 0 and dia[fim_emp - k] == dia[g] and sent[fim_emp - k] == fav:
                    k += 1
                v0 = fim_emp - k + 1
            else:
                v0 = max(g - janela_hull + 1, g - idd[g]); k = 0
            js = np.arange(v0, g + 1)
            if lado < 0:
                j = js[np.argmax(h[js])]; ext = h[j]
            else:
                j = js[np.argmin(l[js])]; ext = l[j]
            if not sd[j] > 0:
                continue
            zext = (ext - vw[j]) / sd[j] * (-lado)          # >0: alem da VWAP no lado da banda
            if alvo == 'banda':
                if zext < z_min:
                    continue
                nivel = int(min(3, max(0, np.floor(zext))))   # 0 = nao chegou na banda 1 (so no controle)
                if gatilho == 'hull':
                    k = int(np.sum(sent[v0:g + 1] == fav))
            else:
                # VWAP: empurrao comecou do lado de fora (lado da operacao) e o extremo
                # encostou na VWAP sem chegar na banda 1 do outro lado
                ini = v0 - 1 if v0 - 1 >= 0 and dia[v0 - 1] == dia[g] else v0
                z_ini = (c[ini] - vw[ini]) / sd[ini] * lado if sd[ini] > 0 else np.nan
                if not (z_ini > 0.0):
                    continue
                if not (zext >= 0.0 and zext < 1.0):      # tocou a VWAP e nao chegou na banda oposta
                    continue
                nivel = 0
            # ---------------- padrao da virada
            pav_rej = (h[g] - max(o[g], c[g])) if lado < 0 else (min(o[g], c[g]) - l[g])
            rej = bool(j == g and pav_rej >= 30)             # o proprio candle contra fez o extremo e rejeitou
            if alvo == 'banda':
                emp = js[:len(js) - max(nc, 1)]               # candles do empurrao
                bk = vw[emp] + (-lado) * nivel * sd[emp]
                fech_fora = bool(np.any((c[emp] - bk) * (-lado) > 0))
                banda_g = vw[g] + (-lado) * nivel * sd[g]
                volta_dentro = bool((c[g] - banda_g) * (-lado) < 0)
                falso = fech_fora and volta_dentro
            else:
                falso = bool((c[j] - vw[j]) * lado < 0 and (c[g] - vw[g]) * lado > 0)
            # topo/fundo duplo: sinal anterior do mesmo lado no pregao, 5 a 40 candles
            # antes, com recuo de pelo menos 200 pts entre os dois extremos, e o
            # extremo atual entre 100 pts aquem e 30 pts alem do anterior
            ant = hist.get((dia[g], lado), [])
            duplo = False; n_ant = len(ant)
            for (ga, ja, ea, za) in ant[::-1]:
                if g - ga > 40:
                    break
                if j - ja < 5 or za < (1.0 if alvo == 'banda' else 0.0):
                    continue
                rec = (ea - (l[ja:j].min() if lado < 0 else h[ja:j].max())) * (-lado)
                dif = (ext - ea) * (-lado)
                if rec >= 200 and -100 <= dif <= 30:
                    duplo = True
                    break
            hist.setdefault((dia[g], lado), []).append((g, j, ext, zext))
            exaust = k >= 4
            if falso:
                padrao = 'falso'
            elif duplo:
                padrao = 'duplo'
            elif rej:
                padrao = 'rejeicao'
            elif exaust:
                padrao = 'exaustao'
            else:
                padrao = 'simples'
            # ---------------- toques
            if alvo == 'banda':
                n_toque = int(T['ep'][(lado, nivel)][j]) if nivel else 0   # j atingiu o nivel: episodio >= 1
                n_toque1 = int(T['ep'][(lado, 1)][j]) if nivel else 0
            else:
                n_toque = n_toque1 = 0
            # ---------------- VWAP: angulo
            a0 = max(g - ANG_N, g - idd[g])
            ang = (vw[g] - vw[a0]) / max(1, g - a0)                  # pts por candle
            ang20_0 = max(g - 20, g - idd[g])
            ang20 = (vw[g] - vw[ang20_0]) / max(1, g - ang20_0)
            ts = dat.iat[g]
            # banda oposta tocada antes no dia (para as entradas na VWAP:
            # compra na VWAP depois de o preco ter ido a banda de cima = pullback)
            zf = zx[-lado][g - idd[g]:g + 1]
            ja_banda_fav = bool(np.nanmax(zf) >= 1.0) if len(zf) else False
            zc = zx[lado][g - idd[g]:g + 1]
            ja_banda_contra = bool(np.nanmax(zc) >= 1.0) if len(zc) else False
            linhas.append(dict(
                i=g, data=ts, lado=int(lado), gatilho=gatilho, alvo_sinal=alvo,
                v0=int(v0), j_ext=int(j), ext=float(ext), n_emp=int(k), nc=nc,
                preco=c[g], o=o[g], h=h[g], l=l[g], hora=ts.hour + ts.minute / 60.0,
                idx_dia=int(idd[g]),
                vwap=vw[g], sd=sd[g], zext=float(zext), nivel=nivel,
                z_ent=float((c[g] - vw[g]) / sd[g] * (-lado)),
                dist_vwap=float((vw[g] - c[g]) * lado),          # pts ate a VWAP na direcao do trade
                ang=float(ang * lado), ang20=float(ang20 * lado),  # >0: VWAP andando a favor do trade
                ang_sd=float(ang * ANG_N / sd[g] * lado),
                padrao=padrao, rej=rej, falso=bool(falso), duplo=duplo, exaust=bool(exaust),
                pav_rej=float(pav_rej),
                n_toque=n_toque, n_toque1=n_toque1, n_sinal_dia=n_ant,
                ja_banda_fav=ja_banda_fav, ja_banda_contra=ja_banda_contra,
                hull_fav=bool((hu[g] - hu[g - 1]) * lado > 0) if not np.isnan(hu[g - 1]) else False,
                macd_fav=bool(mc[g] * lado > 0),
                ema_fav=bool((c[g] - em[g]) * lado > 0),
                tend_dia=float((c[g] - abre[g]) * lado),
                vol_rel=float(vol[g] / vol_med[g]) if vol_med[g] else np.nan,
                vol_emp_rel=float(vol[v0:g + 1].mean() / vol_med[g]) if vol_med[g] else np.nan,
                saldo_emp=float(sal[v0:g + 1].sum() * -lado / max(1.0, vol[v0:g + 1].sum())),
                saldo_g=float(sal[g] * lado / max(1.0, vol[g])),
                dur_emp_rel=float(dur[v0:fim_emp + 1].mean() / dur_med[g]) if (gatilho != 'hull' and dur_med[g]) else np.nan,
            ))
    S = pd.DataFrame(linhas)
    if len(S):
        S = S.sort_values(['i', 'lado']).reset_index(drop=True)
    return S


# ============================================================= simulacao
from numba import njit  # noqa: E402

MOTIVOS = {0: 'alvo', 1: 'stop', 2: 'stop_zero', 3: 'fim_dia', 4: 'tempo'}


class Arr:
    def __init__(self, d):
        self.o = d['o'].to_numpy(float); self.h = d['h'].to_numpy(float)
        self.l = d['l'].to_numpy(float); self.c = d['c'].to_numpy(float)
        self.dia = d['dia'].to_numpy().view('i8').astype(np.int64)
        self.vw = d['vwap'].to_numpy(float); self.sd = d['sd'].to_numpy(float)
        self.n = len(self.o)


GESTOES = {
    'r300': dict(nome='Stop 100 / alvo 300 seco', stop=100.0, alvo=300.0),
    'r500': dict(nome='Stop 100 / alvo 500 seco', stop=100.0, alvo=500.0),
    'vw': dict(nome='Stop 100 / alvo na VWAP', stop=100.0, alvo='vwap'),
    'claude': dict(nome='CLAUDE.md: stop 100, parcial +100, alvo 300', stop=100.0, alvo=300.0,
                   parcial=100.0, frac=0.5),
}


@njit(cache=True)
def _sim(o, h, l, c, dia, vw, sd, G, LADO, PENT, EXT,
         st_modo, st_val, st_cap, al_modo, al_val, parc_em, frac, max_barras, atr):
    """Entrada no fechamento de G[k]; caminho do candle com o pavio contra
    primeiro (o, l, h, c na alta; o, h, l, c na baixa), igual ao engine.py."""
    m = len(G); n = len(o)
    PTS = np.zeros(m); MFE = np.zeros(m); MAE = np.zeros(m)
    ISAI = np.zeros(m, np.int64); PSAI = np.zeros(m); MOT = np.zeros(m, np.int64); STP = np.zeros(m)
    seq = np.zeros(4)
    for k in range(m):
        g = G[k]; lado = LADO[k]; pe = PENT[k]
        if st_modo == 0:
            sp = st_val
        else:
            sp = max(20.0, (EXT[k] - pe) * -lado + 10.0)
            if sp > st_cap:
                sp = st_cap
        s_vig = pe - lado * sp
        pos = 1.0; pts = 0.0; mfe = 0.0; mae = 0.0; parc = False
        mot = -1; isai = g; psai = pe
        fim = min(n - 1, g + max_barras)
        i = g + 1
        while i <= fim:
            if dia[i] != dia[g]:
                isai = i - 1; psai = c[i - 1]; mot = 3
                pts += pos * (psai - pe) * lado; pos = 0.0
                break
            tem_alvo = True
            if al_modo == 0:
                pa = pe + lado * al_val
            elif al_modo == 1:
                pa = vw[i - 1]
            elif al_modo == 2:
                pa = vw[i - 1] + lado * sd[i - 1]
            else:
                pa = 0.0; tem_alvo = False
            if c[i] >= o[i]:
                seq[0] = o[i]; seq[1] = l[i]; seq[2] = h[i]; seq[3] = c[i]
            else:
                seq[0] = o[i]; seq[1] = h[i]; seq[2] = l[i]; seq[3] = c[i]
            q0 = 1 if o[i] == c[i - 1] else 0
            for q in range(q0, 4):
                p = seq[q]
                exc = (p - pe) * lado
                if exc > mfe:
                    mfe = exc
                m2 = max(exc, (s_vig - pe) * lado)
                if m2 < mae:
                    mae = m2
                if (p - s_vig) * lado <= 0:
                    pts += pos * (s_vig - pe) * lado; pos = 0.0
                    isai = i; psai = s_vig; mot = 2 if parc else 1
                    break
                if parc_em > 0 and not parc and exc >= parc_em + atr:
                    pts += frac * parc_em; pos -= frac; parc = True
                    s2 = pe - lado * (frac * parc_em / (1 - frac))
                    if (s2 - s_vig) * lado > 0:
                        s_vig = s2
                if tem_alvo and (p - pa) * lado >= atr:
                    pts += pos * (pa - pe) * lado; pos = 0.0
                    isai = i; psai = pa; mot = 0
                    break
            if pos == 0.0:
                break
            i += 1
        if pos > 0:
            isai = min(i, fim); psai = c[isai]
            pts += pos * (psai - pe) * lado
            if mot < 0:
                mot = 4
        PTS[k] = pts; MFE[k] = mfe; MAE[k] = mae; ISAI[k] = isai; PSAI[k] = psai; MOT[k] = mot; STP[k] = sp
    return PTS, MFE, MAE, ISAI, PSAI, MOT, STP


def executa(A, S, G):
    """Uma linha por sinal, na ordem de S. G:
      stop   pontos fixos | ('ext', teto): alem do extremo do movimento + 10, limitado ao teto
      alvo   pontos fixos | 'vwap' (VWAP do candle anterior, reposicionada a cada
             candle) | 'b1' (banda 1 a favor, idem) | None (so stop / fim do dia)
      parcial, frac  parcial fixa; o stop do resto vai para a media (gestao do CLAUDE.md)
      atravessa  ordens limitadas (alvo, parcial) so executam com o preco N pts alem
    Resultado em pontos por contrato (posicao inteira = 1)."""
    st = G.get('stop', 100.0); al = G.get('alvo', 300.0)
    st_modo, st_val, st_cap = (1, 0.0, float(st[1])) if isinstance(st, tuple) else (0, float(st), 0.0)
    al_modo, al_val = ((1, 0.0) if al == 'vwap' else (2, 0.0) if al == 'b1' else (3, 0.0) if al is None
                       else (0, float(al)))
    r = _sim(A.o, A.h, A.l, A.c, A.dia, A.vw, A.sd,
             S['i'].to_numpy(np.int64), S['lado'].to_numpy(np.int64), S['preco'].to_numpy(float),
             S['ext'].to_numpy(float), st_modo, st_val, st_cap, al_modo, al_val,
             float(G.get('parcial') or 0.0), float(G.get('frac', 0.5)), int(G.get('max_barras', 400)),
             float(G.get('atravessa', 0.0)))
    t = S.copy()
    for k, v in zip(('pts', 'mfe', 'mae', 'i_sai', 'preco_sai', 'mot', 'stop_pts'), r):
        t[k] = v
    t['motivo'] = t['mot'].map(MOTIVOS)
    t['barras'] = t['i_sai'] - t['i']
    t['i_ent'] = t['i']; t['preco_ent'] = t['preco']; t['aceito'] = True
    return t


def reais(t, contratos=CONTRATOS, custo=CUSTO_CONTRATO):
    return t['pts'].to_numpy() * VAL_PONTO * contratos - custo * contratos


def carteira(t):
    return E.carteira(t)


def estatisticas(t):
    return E.estatisticas(t)
