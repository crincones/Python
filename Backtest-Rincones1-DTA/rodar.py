# -*- coding: utf-8 -*-
"""
Roda o backtest Rincones1-DTA e grava saida/.

    python rodar.py

Gera:
    saida/resumo.json   TUDO que o relatorio precisa -- e a unica fonte de
                        numeros. relatorio.py e plano.py leem daqui, entao
                        numero de documento nunca fica defasado.
    saida/trades_*.csv  operacao a operacao, da configuracao padrao
    saida/console.txt   o mesmo que sai na tela

Depois: `python relatorio.py` e `python plano.py`.
"""
import contextlib
import io
import json
import os

import numpy as np
import pandas as pd

import engine as E

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')
BASES = ('WINV26', 'WINFUT')

NIVEIS = (0.55, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90)
SETUPS = ('D', 'T', 'K', 'KB')
CARTEIRAS = (('cD', ('D',)), ('cDT', ('D', 'T')),
             ('cDTK', ('D', 'T', 'K')), ('cDTKKB', ('D', 'T', 'K', 'KB')))

ROT_SETUP = {
    'D': 'descolamento da Hull',
    'T': 'tendencia com forca',
    'K': 'rejeicao da banda',
    'KB': 'banda classica',
}

# As variantes de gestao. A primeira e a herdada do Rincones1; a ultima e a
# que este projeto adotou. Cada uma e (chave, dict de parametros, rotulo).
GESTOES = (
    ('p150', dict(STOP_MODO='pontos', STOP=150.0, ALVO_MODO='pontos', ALVO=300.0),
     'stop 150 fixo · alvo 300 — a herdada do Rincones1'),
    ('p100', dict(STOP_MODO='pontos', STOP=100.0, ALVO_MODO='pontos', ALVO=300.0),
     'stop 100 fixo · alvo 300'),
    ('atr075', dict(STOP_MODO='atr', STOP_ATR=0.75, ALVO_MODO='pontos', ALVO=300.0),
     'stop 0,75 × ATR · alvo 300 — o padrão daqui'),
    ('atr150', dict(STOP_MODO='atr', STOP_ATR=1.50, ALVO_MODO='pontos', ALVO=300.0),
     'stop 1,50 × ATR · alvo 300'),
    ('atr075R3', dict(STOP_MODO='atr', STOP_ATR=0.75, ALVO_MODO='R', ALVO_R=3.0),
     'stop 0,75 × ATR · alvo 3 R'),
)
GESTAO_PADRAO = 'atr075'

ROT_E2 = {0: 'v1 · |delta| / |Close-Open|',
          1: 'v1 · esforço / range',
          2: 'v2 · (|delta|/esforço) × volta',
          3: 'v2 · |delta| × volta',
          4: 'volta pura'}
METRICAS_E2 = (0, 2)

_IND = {}
_CTX = {}


def ind(nome):
    chave = (nome, E.METRICA_E2)
    if chave not in _IND:
        _IND[chave] = E.indicador(E.carrega(E.ARQUIVOS[nome]))
    return _IND[chave]


def ctx(nome):
    """Contexto com os parametros ATUAIS -- a chave inclui todos eles."""
    chave = (nome, E.METRICA_E2, E.EMA_PER, E.HMA_PER, E.ATR_PER,
             E.KELT_INT, E.KELT_EXT, E.EMA_SLOPE, E.HMA_SLOPE,
             E.INCL_EMA, E.HMA_PLANA)
    if chave not in _CTX:
        _CTX[chave] = E.contexto(ind(nome))
    return _CTX[chave]


class com(object):
    """Roda um bloco com outros parametros e devolve os antigos no fim."""

    def __init__(self, **kw):
        self.kw = kw

    def __enter__(self):
        self.old = {k: getattr(E, k) for k in self.kw}
        for k, v in self.kw.items():
            setattr(E, k, v)
        return self

    def __exit__(self, *a):
        for k, v in self.old.items():
            setattr(E, k, v)
        return False


def metr(tr):
    """Metricas + o EV em R e o stop medio -- com o stop dimensionado pelo ATR,
    EV em pontos nao compara duas gestoes, e EV/stop compara."""
    m = E.metricas(tr)
    if m and len(tr):
        m['ev_r'] = float((tr.pnl / tr.stop_pts).mean())
        m['stop_medio'] = float(tr.stop_pts.mean())
    return m


def mede(nome, ativos=('D', 'T'), nivel=None, carteira=True, setup=None):
    d = ctx(nome)
    sig = E.gatilho(d, nivel)
    marca = E.setups(d, sig, ativos=ativos)
    return metr(E.roda(d, marca, sig, carteira=carteira, setup=setup))


def _r(m, casas=1):
    """Arredonda um dict de metricas para o json nao virar dizimas."""
    if not m:
        return None
    return {k: (round(v, casas) if isinstance(v, float) and np.isfinite(v)
                else (None if isinstance(v, float) and not np.isfinite(v) else v))
            for k, v in m.items()}


# ==================================================== o nivel do gatilho
def varre_nivel():
    """O nivel minimo do indice, de 0,55 (o corte de cor do .ntsl) a 0,90.

    E o parametro mais forte do projeto: o gatilho e uma leitura de
    absorcao, e absorcao fraca nao se desfaz. A tabela mostra a troca --
    nivel alto mede muito melhor por trade e da menos trades.
    """
    out = {'niveis': [str(n) for n in NIVEIS], 'atual': str(E.NIVEL_MIN),
           'grid': {}}
    for base in BASES:
        d = ctx(base)
        out['grid'][base] = {}
        for nv in NIVEIS:
            sig = E.gatilho(d, nv)
            g = {'gatilhos': int((sig != 0).sum())}
            for rot, ativos in CARTEIRAS[:2]:
                marca = E.setups(d, sig, ativos=ativos)
                g[rot] = _r(metr(E.roda(d, marca, sig, carteira=True)), 2)
            mk4 = E.setups(d, sig, ativos=SETUPS)
            for su in SETUPS:
                g['setup_' + su] = _r(metr(
                    E.roda(d, mk4, sig, carteira=False, setup=su)), 2)
                g['sinais_' + su] = int((mk4 == su).sum())
            out['grid'][base][str(nv)] = g
    return out


# ======================================================== a leitura da Hull
def estudo_hull():
    """A medicao central: de que lado da Hull vale entrar.

    Para cada gatilho, duas distancias ASSINADAS PELO LADO DO TRADE:
        dh = sig x (close - Hull50) / ATR      dh < 0 = entrar do lado oposto
        de = sig x (close - EMA21)  / ATR
    Os baldes sao medidos com cada sinal ISOLADO (carteira=False), que e
    como se compara balde com balde sem um roubar a vaga do outro.
    """
    out = {'baldes': {}, 'faixas': {}, 'inclinacao': {}}
    for base in BASES:
        d = ctx(base)
        sig = E.gatilho(d)
        tr = E.roda(d, np.where(sig != 0, 'X', ''), sig, carteira=False)
        i = tr.i.to_numpy()
        s = tr.s.to_numpy()
        a = d['atr'].to_numpy()[i]
        C = d.C.to_numpy()[i]
        dh = s * (C - d['hma'].to_numpy()[i]) / a
        de = s * (C - d.ema.to_numpy()[i]) / a
        inch = s * np.nan_to_num(d.inc_hma.to_numpy())[i]
        plana = d.hma_plana.to_numpy()[i]
        pnl = tr.pnl.to_numpy()

        def cel(m, rot):
            if m.sum() < 3:
                return dict(rot=rot, n=int(m.sum()), ev=None, t=None, acerto=None)
            x = tr[m]
            g = x.groupby('dia').pnl.sum()
            t = (g.mean() / (g.std() / np.sqrt(len(g)))
                 if len(g) > 2 and g.std() > 0 else None)
            return dict(rot=rot, n=int(m.sum()), ev=round(float(pnl[m].mean()), 1),
                        t=None if t is None else round(float(t), 2),
                        acerto=round(100.0 * float((pnl[m] > 0).mean()), 1))

        out['baldes'][base] = [
            cel(dh < 0, 'close do lado OPOSTO da Hull  (o setup D)'),
            cel(dh > 0, 'close do lado da Hull  (a leitura clássica)'),
            cel((dh < 0) & ~plana, 'lado oposto + Hull não plana'),
            cel((dh > 0) & ~plana, 'lado da Hull + Hull não plana'),
            cel(plana, 'Hull PLANA — sem intensidade'),
            cel(~plana, 'Hull não plana'),
            cel((dh < 0) & ~plana & (de >= -E.PROF_MAX),
                'lado oposto + não plana + mergulho até %s ATR'
                % str(E.PROF_MAX).replace('.', ',')),
        ]
        out['faixas'][base] = [
            cel((dh >= lo) & (dh < hi), rot) for lo, hi, rot in (
                (-99, -2, 'dh < −2'), (-2, -1, '−2 ≤ dh < −1'),
                (-1, -0.3, '−1 ≤ dh < −0,3'), (-0.3, 0.3, '−0,3 ≤ dh < +0,3'),
                (0.3, 1, '+0,3 ≤ dh < +1'), (1, 2, '+1 ≤ dh < +2'),
                (2, 99, 'dh ≥ +2'))]
        out['inclinacao'][base] = [
            cel((inch >= lo) & (inch < hi), rot) for lo, hi, rot in (
                (-99, -0.15, 'Hull contra o trade, forte'),
                (-0.15, -0.05, 'Hull contra o trade, fraca'),
                (-0.05, 0.05, 'Hull PLANA'),
                (0.05, 0.15, 'Hull a favor, fraca'),
                (0.15, 99, 'Hull a favor, forte'))]
        out['n'] = out.get('n', {})
        out['n'][base] = int(len(tr))
    return out


# ==================================================== o canal de Keltner
def estudo_canal():
    """O que o canal acrescenta -- e o que nao acrescenta.

    Tres medicoes: onde as barras ficam, o que a restricao de zona muda no
    setup D (praticamente nada: a regra da Hull ja excluiu a banda), e as
    duas leituras de banda como setup (K = rejeicao, KB = classica).
    """
    out = {'zonas': {}, 'veto': {}, 'setups': {}}
    for base in BASES:
        d = ctx(base)
        ok = d.ok_ctx.to_numpy()
        z = d.zona.to_numpy()[ok]
        sig = E.gatilho(d)
        zg = d.zona.to_numpy()[sig != 0]
        out['zonas'][base] = {
            str(k): {'barras': round(100 * float((z == k).mean()), 1),
                     'gatilhos': round(100 * float((zg == k).mean()), 1)}
            for k in (0, 1, 2)}

        # o veto do canal: KELT_INT = 99 desliga a exigencia de zona
        out['veto'][base] = {}
        for rot, kv in (('com', E.KELT_INT), ('sem', 99.0)):
            with com(KELT_INT=kv):
                _CTX.clear()
                out['veto'][base][rot] = _r(mede(base, ativos=('D', 'T')), 2)
        _CTX.clear()

        out['setups'][base] = {}
        for su in ('K', 'KB'):
            d2 = ctx(base)
            sig2 = E.gatilho(d2)
            mk = E.setups(d2, sig2, ativos=SETUPS)
            out['setups'][base]['iso_' + su] = _r(metr(
                E.roda(d2, mk, sig2, carteira=False, setup=su)), 2)
        for rot, ativos in CARTEIRAS:
            out['setups'][base][rot] = _r(mede(base, ativos=ativos), 2)
    return out


# ============================================================= a gestao
def estudo_gestao():
    """As variantes de stop e alvo, e a grade inteira.

    A carteira e a mesma em todas as linhas -- os SINAIS nao dependem da
    gestao. O que muda e onde o trade morre e quanto ele paga.
    """
    out = {'rotulos': {k: rot for k, _, rot in GESTOES},
           'ordem': [k for k, _, _ in GESTOES], 'atual': GESTAO_PADRAO,
           'grid': {}, 'grade': {}, 'grade_atr': {}}
    for base in BASES:
        out['grid'][base] = {}
        for chave, par, _rot in GESTOES:
            with com(**par):
                d = ctx(base)
                sig = E.gatilho(d)
                marca = E.setups(d, sig, ativos=('D', 'T'))
                out['grid'][base][chave] = _r(
                    metr(E.roda(d, marca, sig, carteira=True)), 2)

        g = {}
        for st in (75, 100, 150, 200):
            for al in (200, 250, 300, 450):
                with com(STOP_MODO='pontos', STOP=float(st),
                         ALVO_MODO='pontos', ALVO=float(al)):
                    m = mede(base)
                g['%d_%d' % (st, al)] = None if not m else round(m['ev'], 1)
        out['grade'][base] = g

        g = {}
        for sa in (0.6, 0.75, 1.0, 1.25, 1.5):
            for al in (200, 250, 300, 450):
                with com(STOP_MODO='atr', STOP_ATR=sa,
                         ALVO_MODO='pontos', ALVO=float(al)):
                    d = ctx(base)
                    sig = E.gatilho(d)
                    marca = E.setups(d, sig, ativos=('D', 'T'))
                    m = metr(E.roda(d, marca, sig, carteira=True))
                    ev_r = None if not m else round(m['ev_r'], 2)
                g['%s_%d' % (sa, al)] = None if not m else {
                    'ev': round(m['ev'], 1), 'ev_r': ev_r, 't': round(m['t'], 2),
                    'dd': round(m['dd'])}
        out['grade_atr'][base] = g
    return out


# ================================================ o eixo E2 e o filtro dele
def estudo_e2():
    """A formula do eixo [E2] e o filtro DESCARTA_E2.

    O v2 do indicador trocou o eixo do deslocamento por vaivem. Aqui a
    troca e remedida com TODO o resto congelado. O filtro DESCARTA_E2
    (jogar fora a barra em que [E2] e o maior dos tres eixos) nao existe no
    .ntsl -- vinha do Rincones1 -- e tambem e medido.
    """
    out = {'rotulos': {str(k): ROT_E2[k] for k in METRICAS_E2},
           'metricas': [str(m) for m in METRICAS_E2],
           'atual': str(E.METRICA_E2), 'grid': {}, 'filtro': {}}
    met0 = E.METRICA_E2
    for base in BASES:
        out['grid'][base] = {}
        for met in METRICAS_E2:
            E.METRICA_E2 = met
            d = ctx(base)
            sig = E.gatilho(d)
            g = {'gatilhos': int((sig != 0).sum())}
            for rot, ativos in CARTEIRAS[:2]:
                marca = E.setups(d, sig, ativos=ativos)
                g[rot] = _r(metr(E.roda(d, marca, sig, carteira=True)), 2)
            out['grid'][base][str(met)] = g
        E.METRICA_E2 = met0

        out['filtro'][base] = {}
        for rot, val in (('sem', False), ('com', True)):
            with com(DESCARTA_E2=val):
                d = ctx(base)
                sig = E.gatilho(d)
                marca = E.setups(d, sig, ativos=('D', 'T'))
                out['filtro'][base][rot] = _r(
                    metr(E.roda(d, marca, sig, carteira=True)), 2)
                out['filtro'][base]['gatilhos_' + rot] = int((sig != 0).sum())
    return out


# ================================================== sensibilidade dos cortes
SENS = (
    ('HMA_PER', 'período da Hull', (20, 34, 50, 80, 100)),
    ('EMA_PER', 'período da EMA', (9, 13, 21, 34)),
    ('HMA_PLANA', 'corte da Hull plana', (0.02, 0.03, 0.05, 0.08, 0.12)),
    ('HMA_SLOPE', 'lookback da inclinação da Hull', (1, 3, 5, 8)),
    ('PROF_MAX', 'mergulho máximo, em ATRs', (1.0, 1.5, 2.0, None)),
    ('ATR_PER', 'janela do ATR', (10, 20, 40)),
    ('EXT_MAX_T', 'esticamento máximo do setup T', (0.0, 0.5, 1.0)),
)


def estudo_sensibilidade():
    """Cada corte, um de cada vez, com o resto congelado.

    Serve para separar "a regra mede" de "o numero foi escolhido a dedo":
    se o desempenho desaba ao lado do valor adotado, o valor esta ajustado
    demais.
    """
    out = {'ordem': [k for k, _, _ in SENS],
           'rotulos': {k: rot for k, rot, _ in SENS},
           'valores': {k: [str(v) for v in vs] for k, _, vs in SENS},
           'atual': {k: str(getattr(E, k)) for k, _, _ in SENS},
           'grid': {}}
    for base in BASES:
        out['grid'][base] = {}
        for par, _rot, valores in SENS:
            out['grid'][base][par] = {}
            for v in valores:
                with com(**{par: v}):
                    _CTX.clear()
                    out['grid'][base][par][str(v)] = _r(mede(base), 2)
            _CTX.clear()
    return out


# ============================================================ o detalhe
def psicologia(base, custo=0.0):
    """A FORMA do desempenho, nao o desempenho: o que o operador manual
    precisa saber para nao confundir variancia normal com estrategia
    quebrada."""
    with com(CUSTO_PTS=float(custo)):
        d = ctx(base)
        sig = E.gatilho(d)
        marca = E.setups(d, sig, ativos=('D', 'T'))
        tr = E.roda(d, marca, sig, carteira=True)
    if not len(tr):
        return None

    g = tr.groupby('dia').pnl.sum()
    dia = g.to_numpy(float)

    def maior_seq(mask):
        b = c = 0
        for v in mask:
            c = c + 1 if v else 0
            b = max(b, c)
        return int(b)

    rng = np.random.default_rng(20260908)
    if len(dia) >= 3:
        p_sem = float((rng.choice(dia, size=(20000, 5), replace=True)
                       .sum(axis=1) < 0).mean())
        p_mes = float((rng.choice(dia, size=(20000, 20), replace=True)
                       .sum(axis=1) < 0).mean())
    else:
        p_sem = p_mes = None

    q = 1.0 - float((tr.pnl > 0).mean())
    return dict(
        custo=float(custo), n=int(len(tr)), pregoes=int(len(g)),
        por_pregao=round(len(tr) / len(g), 1),
        acerto=round(100 * float((tr.pnl > 0).mean()), 1),
        ev=round(float(tr.pnl.mean()), 1),
        ev_r=round(float((tr.pnl / tr.stop_pts).mean()), 2),
        stop_medio=round(float(tr.stop_pts.mean())),
        stop_min=round(float(tr.stop_pts.min())),
        stop_max=round(float(tr.stop_pts.max())),
        sd_trade=round(float(tr.pnl.std()), 1),
        media_dia=round(float(g.mean()), 1), sd_dia=round(float(g.std()), 1),
        dias_pos=round(100 * float((g > 0).mean())),
        pior_dia=round(float(g.min())), melhor_dia=round(float(g.max())),
        seq_trades=maior_seq(tr.pnl.to_numpy() <= 0),
        seq_dias=maior_seq(dia < 0),
        p_alvo=round(100 * float((tr.res == 'alvo').mean()), 1),
        p_stop=round(100 * float((tr.res == 'stop').mean()), 1),
        p_zero=round(100 * float((tr.res == 'zero').mean()), 1),
        p_fim=round(100 * float((tr.res == 'fim').mean()), 1),
        p3=round(100 * q ** 3, 1), p4=round(100 * q ** 4, 1),
        p5=round(100 * q ** 5, 1),
        p_semana_neg=None if p_sem is None else round(100 * p_sem),
        p_mes_neg=None if p_mes is None else round(100 * p_mes),
        dd=round(float((np.maximum.accumulate(tr.pnl.cumsum().to_numpy())
                        - tr.pnl.cumsum().to_numpy()).max())),
    )


def detalhe(base):
    d = ctx(base)
    sig = E.gatilho(d)
    marca = E.setups(d, sig, ativos=('D', 'T'))
    r = {'barras': int(len(d)), 'pregoes': int(d.dia.nunique()),
         'ini': str(d.Data.min().date()), 'fim': str(d.Data.max().date()),
         'gatilhos': int((sig != 0).sum()),
         'atr_mediano': round(float(np.nanmedian(d['atr'])))}
    # pregoes de verdade: o WINV26 tem meses de 1 barra por dia, de quando o
    # contrato ainda era distante. Contar esses como pregao mente na media.
    porte = d.groupby('dia').size()
    r['pregoes_cheios'] = int((porte >= 20).sum())

    for modo in ('meio', 'fecha'):
        r['entrada_' + modo] = _r(metr(
            E.roda(d, marca, sig, entrada=modo, carteira=True)), 2)
    for mf, rot in ((E.MAX_BARRAS_FILL, 'regra'), (99999, 'livre')):
        r['fill_' + rot] = _r(metr(
            E.roda(d, marca, sig, carteira=True, max_fill=mf)), 2)
    r['sinais'] = int((marca != '').sum())

    for c in (0, 5, 10, 20):
        with com(CUSTO_PTS=float(c)):
            r['custo_%d' % c] = _r(mede(base), 2)

    r['psico'] = {'c0': psicologia(base), 'c5': psicologia(base, 5.0)}

    tr = E.roda(d, marca, sig, carteira=True)
    if len(tr):
        tt = tr.copy()
        tt['mes'] = pd.to_datetime(tt.dia).dt.to_period('M').astype(str)
        r['mes'] = [dict(mes=k, n=len(g), ev=round(g.pnl.mean(), 1),
                         total=round(float(g.pnl.sum())),
                         acerto=round(100 * float((g.pnl > 0).mean()), 1))
                    for k, g in tt.groupby('mes')]
        r['equity'] = [round(x) for x in tr.pnl.cumsum().tolist()]
        r['equity_setup'] = tr.setup.tolist()

        tt = tr.copy()
        tt['data'] = d.Data.to_numpy()[tt.i.to_numpy()]
        tt['lado'] = np.where(tt.s == 1, 'compra', 'venda')
        tt['pnl_rs'] = tt.pnl * E.VAL_PONTO
        tt[['data', 'dia', 'setup', 'lado', 'ent', 'stop_pts', 'alvo_pts',
            'res', 'pnl', 'pnl_rs', 'barras']].to_csv(
            os.path.join(SAIDA, 'trades_%s.csv' % base),
            index=False, sep=';', decimal=',')
    return r


# ================================================================ impressao
def _l(rot, m, larg=34):
    if not m:
        return '  %-*s  sem trades' % (larg, rot)
    return ('  %-*s %4d %5.1f %+8.1f %+9.0f %5.1f%% %+6.2f %4.0f%% %5.2f %6.0f'
            % (larg, rot, m['n'], m['por_pregao'], m['ev'], m['total'],
               m['acerto'], m['t'] or 0, m['dias_pos'], min(m['pf'] or 0, 99),
               m['dd']))


def _cab(larg=34):
    return ('  %-*s %4s %5s %8s %9s %6s %6s %5s %5s %6s'
            % (larg, '', 'n', '/preg', 'EV', 'total', 'acerto', 't',
               'dias+', 'PF', 'DD'))


def principal():
    resumo = {'parametros': {k: getattr(E, k) for k in (
        'NIVEL_MIN', 'CORTE_POSICAO', 'CORPO_MAX', 'DESCARTA_E2', 'PERIODO_REF',
        'METRICA_E2', 'EMA_PER', 'HMA_PER', 'ATR_PER', 'KELT_INT', 'KELT_EXT',
        'EMA_SLOPE', 'HMA_SLOPE', 'INCL_EMA', 'HMA_PLANA', 'DIST_HMA_MIN',
        'PROF_MAX', 'EXT_MAX_T', 'BANDA_K',
        'STOP_MODO', 'STOP', 'STOP_ATR', 'STOP_MIN', 'STOP_MAX',
        'ALVO_MODO', 'ALVO', 'ALVO_R', 'ALVO_ATR',
        'PARCIAL_EM', 'FRAC_PARCIAL', 'STOP_APOS_PARCIAL', 'CUSTO_PTS',
        'ENTRADA', 'MAX_BARRAS_FILL', 'SETUPS_ATIVOS', 'PRIORIDADE')},
        'rot_setup': ROT_SETUP, 'setups': list(SETUPS),
        'gestao_padrao': GESTAO_PADRAO, 'bases': {}}

    print('=' * 108)
    print('BACKTEST RINCONES1-DTA  -  WIN, barras de 10.000 ticks')
    print('contexto: EMA %d (tendencia) | Hull %d (forca) | Keltner %g e %g ATRs'
          % (E.EMA_PER, E.HMA_PER, E.KELT_INT, E.KELT_EXT))
    print('gatilho:  Ticks_Esforco_Hist_v2 (padrao do .ntsl), indice >= %.2f'
          % E.NIVEL_MIN)
    print('gestao:   stop %s | parcial %.0f%% na distancia do stop | alvo %s'
          % ('%.2f x ATR' % E.STOP_ATR if E.STOP_MODO == 'atr' else '%.0f pts' % E.STOP,
             100 * E.FRAC_PARCIAL,
             '%.0f pts' % E.ALVO if E.ALVO_MODO == 'pontos' else '%.1f R' % E.ALVO_R))
    print('entrada:  limitada no meio do candle, valida por %d barra(s)'
          % E.MAX_BARRAS_FILL)
    print('=' * 108)

    resumo['nivel'] = varre_nivel()
    print('\n  O NIVEL DO GATILHO  (carteira D + T)')
    for base in BASES:
        for nv in NIVEIS:
            g = resumo['nivel']['grid'][base][str(nv)]
            m = g['cDT']
            print('    %-7s nivel %.2f  gatilhos=%5d | %s'
                  % (base, nv, g['gatilhos'],
                     'sem trades' if not m else
                     'n=%4d %4.1f/preg EV %+7.1f (%+.2fR) t %+5.2f DD %5.0f'
                     % (m['n'], m['por_pregao'], m['ev'], m['ev_r'], m['t'],
                        m['dd'])))

    resumo['hull'] = estudo_hull()
    print('\n  DE QUE LADO DA HULL VALE ENTRAR  (sinais isolados)')
    for base in BASES:
        print('    %s  (%d sinais)' % (base, resumo['hull']['n'][base]))
        for b in resumo['hull']['baldes'][base]:
            print('      %-48s n=%4d EV %s t %s'
                  % (b['rot'], b['n'],
                     '   --' if b['ev'] is None else '%+7.1f' % b['ev'],
                     '  --' if b['t'] is None else '%+5.2f' % b['t']))

    resumo['canal'] = estudo_canal()
    print('\n  O CANAL DE KELTNER')
    for base in BASES:
        z = resumo['canal']['zonas'][base]
        print('    %-7s barras por zona: dentro %.1f%% · 2-3 ATR %.1f%% · >3 ATR %.1f%%'
              % (base, z['0']['barras'], z['1']['barras'], z['2']['barras']))
        v = resumo['canal']['veto'][base]
        print('    %-7s carteira D+T com o veto de zona: EV %+.1f t %+.2f | sem: EV %+.1f t %+.2f'
              % (base, v['com']['ev'], v['com']['t'], v['sem']['ev'], v['sem']['t']))
        for su in ('K', 'KB'):
            m = resumo['canal']['setups'][base]['iso_' + su]
            print('    %-7s setup %-2s isolado: %s'
                  % (base, su, 'sem trades' if not m else
                     'n=%4d EV %+7.1f t %+5.2f' % (m['n'], m['ev'], m['t'])))

    resumo['gestao'] = estudo_gestao()
    print('\n  A GESTAO  (carteira D + T, mesmos sinais em todas as linhas)')
    for base in BASES:
        for chave, _par, rot in GESTOES:
            m = resumo['gestao']['grid'][base][chave]
            print('    %-7s %-48s %s' % (base, rot,
                  'sem trades' if not m else
                  'n=%4d EV %+7.1f (%+.2fR) t %+5.2f tot %+7.0f DD %5.0f'
                  % (m['n'], m['ev'], m['ev_r'], m['t'], m['total'], m['dd'])))

    resumo['e2'] = estudo_e2()
    print('\n  O EIXO [E2] E O FILTRO DELE')
    for base in BASES:
        for met in METRICAS_E2:
            g = resumo['e2']['grid'][base][str(met)]
            m = g['cDT']
            print('    %-7s %-32s gatilhos=%5d | %s'
                  % (base, ROT_E2[met], g['gatilhos'],
                     'sem trades' if not m else 'EV %+7.1f t %+5.2f n=%4d'
                     % (m['ev'], m['t'], m['n'])))
        f = resumo['e2']['filtro'][base]
        for rot in ('sem', 'com'):
            m = f[rot]
            print('    %-7s DESCARTA_E2 %-4s gatilhos=%5d | EV %+7.1f t %+5.2f n=%4d'
                  % (base, rot, f['gatilhos_' + rot], m['ev'], m['t'], m['n']))

    resumo['sens'] = estudo_sensibilidade()
    print('\n  SENSIBILIDADE DOS CORTES  (carteira D + T)')
    for par, rot, valores in SENS:
        print('    %s (%s), adotado %s' % (par, rot, getattr(E, par)))
        for base in BASES:
            cels = []
            for v in valores:
                m = resumo['sens']['grid'][base][par][str(v)]
                cels.append('%s: %s' % (v, 'sem trades' if not m else
                                        'EV %+6.1f t%+5.2f' % (m['ev'], m['t'])))
            print('      %-7s %s' % (base, ' | '.join(cels)))

    for base in BASES:
        print('\n' + '#' * 108)
        print('# %s' % base)
        print('#' * 108)
        det = detalhe(base)
        resumo['bases'][base] = det
        print('  %d barras · %d pregoes (%d com pregao cheio) · %s a %s · ATR mediano %d'
              % (det['barras'], det['pregoes'], det['pregoes_cheios'],
                 det['ini'], det['fim'], det['atr_mediano']))
        print(_cab())
        niv = resumo['nivel']['grid'][base][str(E.NIVEL_MIN)]
        for rot, chave in (('so D', 'cD'), ('D + T  (padrao)', 'cDT'),
                           ('D + T + K', 'cDTK'), ('D + T + K + KB', 'cDTKKB')):
            m = (niv[chave] if chave in niv
                 else resumo['canal']['setups'][base][chave])
            print(_l(rot, m))
        for su in SETUPS:
            print(_l('setup %s isolado (%s)' % (su, ROT_SETUP[su]),
                     niv['setup_' + su]))
        print('\n  entrada')
        print(_l('limitada no meio do candle', det['entrada_meio']))
        print(_l('a mercado no fechamento', det['entrada_fecha']))
        print(_l('limitada valida ate o fim do pregao', det['fill_livre']))
        print('\n  custo por trade')
        for c in (0, 5, 10, 20):
            print(_l('custo de %d pts' % c, det['custo_%d' % c]))

    print('\n' + '=' * 108)
    print('Rode `python relatorio.py` e `python plano.py` para regerar os '
          'documentos a partir destes numeros.')
    print('=' * 108)
    return resumo


if __name__ == '__main__':
    # o console do Windows abre em cp1252 e engasga nos sinais tipograficos
    try:
        import sys
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    os.makedirs(SAIDA, exist_ok=True)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        resumo = principal()
    texto = buf.getvalue()
    print(texto)
    with open(os.path.join(SAIDA, 'console.txt'), 'w', encoding='utf-8') as f:
        f.write(texto)
    with open(os.path.join(SAIDA, 'resumo.json'), 'w', encoding='utf-8') as f:
        json.dump(resumo, f, indent=1, default=str, ensure_ascii=False)
