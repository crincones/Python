# -*- coding: utf-8 -*-
"""
Engine de backtest - Estrategia do Ajuste (WINFUT)
Ver ESTRATEGIA.md para a especificacao completa das regras.

Setups:
  A  - afastamento de N ticks + entrada limite na abertura
  B  - trade seco no proprio ajuste
  C  - pivos (Pivot_Points_Pro: Open-ancorado, amplitude do D1 anterior)
  D  - bolas (multiplos de 1000)
  CD - pivos + bolas com regra de fusao de 300 pts

Gestao (ESTRATEGIA.md 5): stop 100, saida parcial de 2/3 em +45 que zera o risco
e move o stop do restante para o preco medio da operacao (-90 da entrada, onde o
total zera), alvo final de 500 pts fixos em todos os setups.
"""
import csv
import os
import datetime
import collections

BASE = os.path.dirname(os.path.abspath(__file__))
M1_CSV = os.path.join(BASE, 'dados', 'WIN_N_M1.csv')
AJ_CSV = os.path.join(BASE, 'dados', 'Ajustes-WINFUT-NoDiv-NoSplits.2026-08-28.csv')

# ---------------------------------------------------------------- parametros
TICK        = 5.0      # tick do WIN, em pontos
STOP        = 100.0    # stop em pontos
ALVO_FIXO   = 500.0    # alvo fixo em pontos, em todos os setups
ALVO_NO_AJUSTE = False  # True = setups C/D/CD saem no ajuste em vez de ALVO_FIXO (spec anterior)
TICKS_AFAST = 1        # setup A: ticks de afastamento que armam o gatilho
DIST_MIN    = 600.0    # distancia minima nivel <-> ajuste
CRUZA_AJ    = 600.0    # quanto o preco precisa ultrapassar o ajuste p/ virar o regime
RETRACAO    = 500.0    # retracao que invalida o proximo nivel nao tocado
FUSAO       = 300.0    # bola e pivo mais proximos que isso: fica o mais afastado do ajuste
BOLA_PASSO  = 1000.0   # "bolas" = multiplos de 1000
FIBS        = (0.618, 1.000, 1.618, 2.000)   # niveis do Pivot_Points_Pro
VAL_PONTO   = 0.20     # R$ por ponto, 1 contrato WIN
CONTRATOS   = 6        # lote: o minimo que realiza parcial de 1/2 (3) e de 2/3 (4) e
                       # deixa o preco medio num preco real; pts sao por contrato do lote
CUSTO_PTS   = 0.0      # custo de ida e volta em pontos (0 = bruto)

# --- saida parcial (ESTRATEGIA.md 5)
USA_PARCIAL  = True
PARCIAL_PTS  = 45.0    # onde sai a parcial
PARCIAL_FRAC = 2.0 / 3  # fracao da posicao que sai na parcial (2/3 -> resultado 2:1)
PARCIAL_STOP = 'medio'  # stop do restante depois da parcial: 'medio' = preco medio
                        # da operacao (o total zera); ou pts a favor da entrada (0 = na entrada)

# --- regime
REGIME_EXCLUSIVO = True   # ao cruzar o ajuste em CRUZA_AJ pts o lado inicial e desligado

# --- resolucao intrabarra
# A entrada e sempre num extremo novo do dia, entao a barra de entrada tem a
# extremidade favoravel colada no proprio nivel. Creditar parcial/alvo nela
# equivale a assumir preenchimento no tick extremo de uma barra cuja amplitude
# mediana e de 160 pts - e o artefato responde por 93% das parciais.
# False (padrao) = a barra de entrada so resolve stop; favoravel so a partir da seguinte.
FAVORAVEL_NA_ENTRADA = False

# --- medias exponenciais (premissa adicional, ESTRATEGIA.md 1)
EMA_PER = 21

GAP_GLITCH  = 1500.0   # |open-ajuste| acima disso + prev close proximo => ajuste furado
GAP_GLITCH_PC = 1000.0
AJ_JANELA   = ('17:00', '18:00')   # janela do call de fechamento p/ validar o ajuste
AJ_TOL      = 300.0    # desvio do ajuste vs essa janela que reprova o dia


# ---------------------------------------------------------------- carga
def _n(s):
    return float(s.replace('.', '').replace(',', '.'))


def carrega():
    """Devolve (barras, diario, ordem) - barras M1 por dia e o contexto diario."""
    barras = collections.defaultdict(list)
    with open(M1_CSV, encoding='utf-8') as f:
        rd = csv.reader(f, delimiter='\t')
        next(rd)
        for r in rd:
            if len(r) < 6:
                continue
            d = r[0].replace('.', '-')
            barras[d].append((r[1][:5], float(r[2]), float(r[3]), float(r[4]), float(r[5])))
    for d in barras:
        barras[d].sort(key=lambda x: x[0])

    diario = {}
    with open(AJ_CSV, encoding='utf-8-sig') as f:
        rd = csv.reader(f, delimiter='\t')
        next(rd)
        for r in rd:
            if len(r) < 6:
                continue
            dd, mm, yy = r[0].split(' ')[0].split('/')
            diario['%s-%s-%s' % (yy, mm, dd)] = dict(o=_n(r[1]), h=_n(r[2]), l=_n(r[3]),
                                                     c=_n(r[4]), ajuste=_n(r[5]))
    ordem = sorted(set(barras) & set(diario))
    return barras, diario, ordem


def vencimentos(y0=2020, y1=2027):
    """Vencimento do WIN: quarta-feira mais proxima do dia 15 dos meses pares."""
    v = set()
    for y in range(y0, y1):
        for mth in (2, 4, 6, 8, 10, 12):
            melhor = None
            for day in range(11, 20):
                try:
                    dt = datetime.date(y, mth, day)
                except ValueError:
                    continue
                if dt.weekday() == 2 and (melhor is None or abs(day - 15) < abs(melhor.day - 15)):
                    melhor = dt
            if melhor:
                v.add(melhor.isoformat())
    return v


def desvio_ajuste(barras, dia_ant, ajuste, janela=AJ_JANELA):
    """
    ESTRATEGIA.md 2.2: o ajuste tem que cair no range do call de fechamento do dia
    anterior. Devolve 0.0 se cai dentro, senao a distancia ate a borda mais
    proxima; None quando nao ha barras na janela.
    """
    b = [x for x in barras[dia_ant] if janela[0] <= x[0] <= janela[1]]
    if not b:
        return None
    lo = min(x[3] for x in b)
    hi = max(x[2] for x in b)
    if lo <= ajuste <= hi:
        return 0.0
    return min(abs(ajuste - lo), abs(ajuste - hi))


def dias_validos(barras, diario, ordem):
    """Aplica os filtros de qualidade. Devolve (validos, motivos_descarte)."""
    venc = vencimentos()
    validos, desc = [], []
    prev_close = None
    prev_dia = None
    for d in ordem:
        b = barras[d]
        aj = diario[d]['ajuste']
        ab = b[0][1]
        motivo = None
        if len(b) < 60:
            motivo = 'pregao curto (%d barras)' % len(b)
        elif b[0][0] > '09:05':
            motivo = 'abertura ausente (1a barra %s)' % b[0][0]
        elif d in venc:
            motivo = 'vencimento/rolagem (gap %+.0f vs ajuste)' % (ab - aj)
        elif prev_close is not None and abs(ab - aj) > GAP_GLITCH and abs(ab - prev_close) < GAP_GLITCH_PC:
            motivo = 'ajuste inconsistente (gap %+.0f vs ajuste, %+.0f vs fech. anterior)' % (ab - aj, ab - prev_close)
        elif prev_dia is None:
            motivo = 'sem D1 anterior para os pivos'
        else:
            dv = desvio_ajuste(barras, prev_dia, aj)
            if dv is not None and dv > AJ_TOL:
                motivo = 'ajuste fora do call de fechamento (desvio %.0f pts)' % dv
        if motivo:
            desc.append((d, motivo))
        else:
            validos.append(d)
        prev_close = b[-1][4]
        prev_dia = d
    return validos, desc


# ---------------------------------------------------------------- medias
def _ema(vals, per):
    k = 2.0 / (per + 1)
    out = []
    e = None
    for v in vals:
        e = v if e is None else (v - e) * k + e
        out.append(e)
    return out


def _bucket5(hm):
    return (int(hm[:2]) * 60 + int(hm[3:])) // 5


def _bucket60(hm):
    return hm[:2]


def medias(barras, ordem, per=EMA_PER):
    """
    EMA de `per` periodos em M5 e M60, sem look-ahead: para cada barra M1 devolve
    o valor da EMA da ultima barra do TF superior JA FECHADA.
    Devolve {dia: [(ema5, ema60), ...]} alinhado com barras[dia].
    """
    def constroi(chave):
        seq, atual = [], None
        for d in ordem:
            for hm, o, h, l, c in barras[d]:
                k = (d, chave(hm))
                if atual is None or atual[0] != k:
                    if atual is not None:
                        seq.append(atual)
                    atual = [k, c]
                else:
                    atual[1] = c
        if atual is not None:
            seq.append(atual)
        ev = _ema([c for _, c in seq], per)
        idx = {k: i for i, (k, _) in enumerate(seq)}
        return idx, ev

    i5, e5 = constroi(_bucket5)
    i60, e60 = constroi(_bucket60)

    out = {}
    for d in ordem:
        linha = []
        for hm, o, h, l, c in barras[d]:
            a = i5.get((d, _bucket5(hm)))
            b = i60.get((d, _bucket60(hm)))
            linha.append((e5[a - 1] if (a is not None and a > 0) else None,
                          e60[b - 1] if (b is not None and b > 0) else None))
        out[d] = linha
    return out


# ---------------------------------------------------------------- niveis
def pivos(diario, dia_ant, abertura):
    """Pivot_Points_Pro: PP e amplitudes do D1 anterior, ancorados na abertura de
    hoje. O PP em si nao entra no conjunto operavel (ESTRATEGIA.md 3.1)."""
    p = diario[dia_ant]
    pp = (p['h'] + p['l'] + p['c']) / 3.0
    ampR = abs(p['l'] - pp)
    ampS = abs(p['h'] - pp)
    niveis = []
    for i, fb in enumerate(FIBS, start=1):
        niveis.append(('R%d' % i, abertura + ampR * fb))
        niveis.append(('S%d' % i, abertura - ampS * fb))
    return niveis


def bolas(lo, hi):
    """Multiplos de BOLA_PASSO na faixa dada, com folga de uma bola em cada ponta."""
    ini = int((lo - BOLA_PASSO) // BOLA_PASSO) * int(BOLA_PASSO)
    fim = int((hi + BOLA_PASSO) // BOLA_PASSO) * int(BOLA_PASSO)
    return [('B%d' % (x // 1000), float(x)) for x in range(ini, fim + 1, int(BOLA_PASSO))]


def funde(niveis, ajuste, dist=FUSAO):
    """Bola e pivo a menos de `dist`: fica o mais AFASTADO do ajuste."""
    ordenados = sorted(niveis, key=lambda x: abs(x[1] - ajuste), reverse=True)
    mantidos = []
    for nome, px in ordenados:
        if any(abs(px - q) < dist for _, q in mantidos):
            continue
        mantidos.append((nome, px))
    return sorted(mantidos, key=lambda x: x[1])


# ---------------------------------------------------------------- simulacao
def contratos_parcial(pfrac=None, lote=None):
    """Quantos contratos do lote saem na parcial. A fracao tem de ser realizavel
    com contratos inteiros: com 6, servem 1/2 (3) e 2/3 (4); 3/4 nao."""
    pfrac = PARCIAL_FRAC if pfrac is None else pfrac
    lote = CONTRATOS if lote is None else lote
    n = pfrac * lote
    if abs(n - round(n)) > 1e-9 or not 0 < round(n) < lote:
        raise ValueError('parcial de %.4f nao cabe num lote de %d contratos' % (pfrac, lote))
    return int(round(n))


def stop_resto(pstop=None, pfrac=None, ppts=None, stop=None):
    """
    Stop do restante depois da parcial, em pts a favor da entrada (negativo =
    contra). 'medio' e o preco medio da operacao depois de realizar a parcial:
    o ponto em que o restante devolve exatamente o que a parcial ganhou, e o
    total da operacao zera. Com 6 contratos e 2/3 em +45: saem 4 x 45 = 180,
    sobram 2 -> medio a 90 pts contra a entrada. Arredondado ao tick, para o
    lado da entrada (o total nunca fica negativo). O stop nunca e afastado: se
    o medio cair alem do stop original, fica o stop.
    """
    pstop = PARCIAL_STOP if pstop is None else pstop
    pfrac = PARCIAL_FRAC if pfrac is None else pfrac
    ppts = PARCIAL_PTS if ppts is None else ppts
    stop = STOP if stop is None else stop
    if pstop != 'medio':
        return float(pstop)
    n = contratos_parcial(pfrac)
    dist = n * ppts / (CONTRATOS - n)
    dist = int(dist / TICK + 1e-9) * TICK
    return -min(dist, stop)


def _liq(pts):
    """Resultado liquido, sem o ruido de ponto flutuante: 2/3*45 + 1/3*(-90)
    daria -7e-15, e o zero a zero passaria a contar como perda."""
    return round(pts - CUSTO_PTS, 6) + 0.0


def fecha(barras, i0, entrada, lado, stop=None, alvo_px=None, otimista=False,
          parcial=None, ema=None, alvo_ema5=False, favoravel_na_entrada=None):
    """
    Percorre da barra i0 (inclusive) ate o fim do pregao.

    Gestao com parcial (ESTRATEGIA.md 5): ao atingir +PARCIAL_PTS sai PARCIAL_FRAC
    da posicao e o stop do restante vai para o preco medio da operacao (ver
    stop_resto); antes disso vale o stop cheio. Resultado em pontos por 1
    contrato inteiro.

    Empate intrabarra: o pior caso ganha (stop antes do alvo), salvo `otimista`.
    `alvo_ema5` troca o alvo pela EMA21 de M5 corrente.

    Devolve (pts, motivo, hora_saida, indice_saida, indice_parcial ou None).
    """
    stop = STOP if stop is None else stop
    if parcial is None:
        parcial = USA_PARCIAL
    if favoravel_na_entrada is None:
        favoravel_na_entrada = FAVORAVEL_NA_ENTRADA
    ppts = PARCIAL_PTS
    # a parcial sai em contratos inteiros do lote (e o medio sai deles)
    pfrac = contratos_parcial() / float(CONTRATOS) if parcial else 0.0
    pstop = stop_resto(stop=stop) if parcial else 0.0

    px_stop = entrada - stop * lado
    px_parc = entrada + ppts * lado
    px_pstop = entrada + pstop * lado
    feita = False
    jp = None              # barra em que a parcial saiu
    ganho = 0.0            # ja realizado na parcial
    tam = 1.0              # fracao ainda aberta

    for j in range(i0, len(barras)):
        hm, o, h, l, c = barras[j]
        alvo = alvo_px
        if alvo_ema5:
            if ema is None or ema[j][0] is None:
                continue
            alvo = ema[j][0]
        # A entrada acontece num extremo novo do dia, entao a barra de entrada tem
        # a extremidade favoravel indistinguivel do proprio range que gerou o toque:
        # creditar saida favoravel nela e assumir preenchimento no tick extremo.
        # Por padrao a barra de entrada so resolve o lado ADVERSO.
        favoravel = favoravel_na_entrada or j > i0
        alvo_ok = favoravel and alvo is not None and ((h >= alvo) if lado > 0 else (l <= alvo))
        parc_ok = favoravel and ((h >= px_parc) if lado > 0 else (l <= px_parc))
        stop_ok = lambda px: (l <= px) if lado > 0 else (h >= px)

        if otimista:
            # a parcial fica entre a entrada e o alvo, entao e atravessada antes
            if parcial and not feita and parc_ok:
                ganho += pfrac * ppts
                tam -= pfrac
                feita = True
                jp = j
            if alvo_ok:
                return _liq(ganho + tam * lado * (alvo - entrada)), 'ALVO', hm, j, jp
            if stop_ok(px_pstop if feita else px_stop):
                s = px_pstop if feita else px_stop
                return _liq(ganho + tam * lado * (s - entrada)), \
                       ('STOP+' if feita else 'STOP'), hm, j, jp
        else:
            # conservador: o adverso resolve antes do favoravel, na ordem em que o
            # preco teria de atravessar os niveis (stop -> parcial -> stop+ -> alvo)
            if stop_ok(px_pstop if feita else px_stop):
                s = px_pstop if feita else px_stop
                return _liq(ganho + tam * lado * (s - entrada)), \
                       ('STOP+' if feita else 'STOP'), hm, j, jp
            if parcial and not feita and parc_ok:
                # o stop+ so passa a valer na barra seguinte: para disparar a
                # parcial o preco teve de subir ate +PARCIAL_PTS, entao a extremidade
                # adversa desta barra e anterior a ela.
                ganho += pfrac * ppts
                tam -= pfrac
                feita = True
                jp = j
            if alvo_ok:
                return _liq(ganho + tam * lado * (alvo - entrada)), 'ALVO', hm, j, jp

    hm, o, h, l, c = barras[-1]
    return _liq(ganho + tam * lado * (c - entrada)), 'FECHAMENTO', hm, len(barras) - 1, jp


# ---------------------------------------------------------------- setup A
def setup_A(barras, ajuste, ticks=None, stop=None, alvo=None, otimista=False,
            alvo_ajuste=False, parcial=None, ema=None, alvo_ema5=False):
    ticks = TICKS_AFAST if ticks is None else ticks
    stop = STOP if stop is None else stop
    alvo = ALVO_FIXO if alvo is None else alvo
    ab = barras[0][1]
    if ab == ajuste:
        return []
    lado = 1 if ab < ajuste else -1
    gat = ab - ticks * TICK if lado > 0 else ab + ticks * TICK
    armado = False
    for i, (hm, o, h, l, c) in enumerate(barras):
        if not armado:
            armado = (l <= gat) if lado > 0 else (h >= gat)
            if not armado:
                continue
        if (h >= ab) if lado > 0 else (l <= ab):
            alvo_px = ajuste if alvo_ajuste else (ab + alvo * lado)
            pts, motivo, hs, k, jp = fecha(barras, i, ab, lado, stop, alvo_px, otimista,
                                           parcial, ema, alvo_ema5)
            return [dict(setup='A', nivel='ABERTURA', lado=lado, entrada=ab,
                         hora=hm, pts=pts, motivo=motivo, hora_saida=hs,
                         dist_ajuste=abs(ab - ajuste), i=i, k=k, jp=jp, alvo=alvo_px)]
    return []


# ---------------------------------------------------------------- setup B
def setup_B(barras, ajuste, stop=None, alvo=None, otimista=False, parcial=None,
            ema=None, alvo_ema5=False):
    stop = STOP if stop is None else stop
    alvo = ALVO_FIXO if alvo is None else alvo
    ab = barras[0][1]
    if ab == ajuste:
        return []
    lado = 1 if ab < ajuste else -1
    for i, (hm, o, h, l, c) in enumerate(barras):
        if (h >= ajuste) if lado > 0 else (l <= ajuste):
            pts, motivo, hs, k, jp = fecha(barras, i, ajuste, lado, stop,
                                           ajuste + alvo * lado, otimista, parcial,
                                           ema, alvo_ema5)
            return [dict(setup='B', nivel='AJUSTE', lado=lado, entrada=ajuste,
                         hora=hm, pts=pts, motivo=motivo, hora_saida=hs,
                         dist_ajuste=0.0, i=i, k=k, jp=jp, alvo=ajuste + alvo * lado)]
    return []


# ---------------------------------------------------------------- setups C / D / CD
def setup_niveis(barras, ajuste, niveis, tag, stop=None, alvo_ajuste=None,
                 alvo_fixo=None, dist_min=None, retracao=None, cruza=None,
                 otimista=False, uma_posicao=False, parcial=None,
                 regime_exclusivo=None, ema=None, alvo_ema5=False):
    """
    Motor comum dos setups baseados em niveis. Ver ESTRATEGIA.md 4.

      - vies do dia: abriu abaixo do ajuste -> compra; acima -> venda
      - so operam niveis a >= dist_min do ajuste, do lado habilitado
      - entrada no PRIMEIRO TOQUE, e o toque tem que ser novo extremo do dia
      - ao ultrapassar o ajuste em `cruza` o regime VIRA: o outro lado e habilitado
        e, com regime_exclusivo, o lado inicial e desligado (ESTRATEGIA.md 4.3)
      - retracao de `retracao` pts sem tocar o nivel invalida o proximo nivel
      - alvo fixo de ALVO_FIXO pts (ou o ajuste, ou EMA21 de M5), stop de `stop` pts + parcial
    """
    stop = STOP if stop is None else stop
    if alvo_ajuste is None:
        alvo_ajuste = ALVO_NO_AJUSTE
    dist_min = DIST_MIN if dist_min is None else dist_min
    retracao = RETRACAO if retracao is None else retracao
    cruza = CRUZA_AJ if cruza is None else cruza
    if regime_exclusivo is None:
        regime_exclusivo = REGIME_EXCLUSIVO
    ab = barras[0][1]
    if ab == ajuste:
        return []
    lado_ini = 1 if ab < ajuste else -1

    est = {}
    for lado in (1, -1):
        if lado > 0:
            cand = [(nm, px) for nm, px in niveis if px <= ajuste - dist_min]
            cand.sort(key=lambda x: -x[1])
        else:
            cand = [(nm, px) for nm, px in niveis if px >= ajuste + dist_min]
            cand.sort(key=lambda x: x[1])
        est[lado] = dict(cand=cand, morto=set(), tocado=set(),
                         habil=(lado == lado_ini), ext=ab, perna=False)

    trades = []
    ocupado_ate = -1
    virou = False

    for i, (hm, o, h, l, c) in enumerate(barras):
        # 1) virada de regime ao ultrapassar o ajuste em `cruza`
        oposto = -lado_ini
        if not virou:
            passou = (h >= ajuste + cruza) if oposto < 0 else (l <= ajuste - cruza)
            if passou:
                virou = True
                est[oposto]['habil'] = True
                est[oposto]['ext'] = ajuste + cruza if oposto < 0 else ajuste - cruza
                est[oposto]['perna'] = False
                if regime_exclusivo:
                    est[lado_ini]['habil'] = False

        for lado in (1, -1):
            e = est[lado]
            if not e['habil']:
                continue

            # 2) entradas
            for nome, px in e['cand']:
                if nome in e['tocado'] or nome in e['morto']:
                    continue
                novo_extremo = (px < e['ext']) if lado > 0 else (px > e['ext'])
                if not (novo_extremo and l <= px <= h):
                    continue
                e['tocado'].add(nome)
                if uma_posicao and i <= ocupado_ate:
                    continue
                alvo_px = ajuste if alvo_ajuste else (px + (alvo_fixo or ALVO_FIXO) * lado)
                pts, motivo, hs, j_sai, jp = fecha(barras, i, px, lado, stop, alvo_px,
                                                   otimista, parcial, ema, alvo_ema5)
                trades.append(dict(setup=tag, nivel=nome, lado=lado, entrada=px,
                                   hora=hm, pts=pts, motivo=motivo, hora_saida=hs,
                                   dist_ajuste=abs(px - ajuste), i=i, k=j_sai, jp=jp,
                                   alvo=alvo_px))
                if uma_posicao:
                    ocupado_ate = j_sai

            # 3) extremo do dia nesse lado (monotonico)
            if lado > 0:
                novo_ext = l < e['ext']
                if novo_ext:
                    e['ext'] = l
                    e['perna'] = True
                recuo = h - e['ext']
            else:
                novo_ext = h > e['ext']
                if novo_ext:
                    e['ext'] = h
                    e['perna'] = True
                recuo = e['ext'] - l

            # 4) invalidacao por retracao
            if e['perna'] and not novo_ext and recuo >= retracao:
                for nome, px in e['cand']:
                    if nome in e['tocado'] or nome in e['morto']:
                        continue
                    if (px < e['ext']) if lado > 0 else (px > e['ext']):
                        e['morto'].add(nome)
                        break
                e['perna'] = False

    return trades


# ---------------------------------------------------------------- metricas
def metricas(trades, ndias):
    if not trades:
        return None
    pts = [t['pts'] for t in trades]
    tot = sum(pts)
    g = [p for p in pts if p > 0]
    pr = [p for p in pts if p < 0]
    eq = pico = dd = 0.0
    for p in pts:
        eq += p
        pico = max(pico, eq)
        dd = min(dd, eq - pico)
    return dict(
        n=len(trades), total=tot, media=tot / len(trades), por_dia=tot / ndias,
        zerados=100.0 * sum(1 for p in pts if p == 0) / len(trades),
        alvos=sum(1 for t in trades if t['motivo'] == 'ALVO'),
        stops=sum(1 for t in trades if t['motivo'] == 'STOP'),
        stops_p=sum(1 for t in trades if t['motivo'] == 'STOP+'),
        fech=sum(1 for t in trades if t['motivo'] == 'FECHAMENTO'),
        acerto=100.0 * len(g) / len(trades),
        pf=(sum(g) / abs(sum(pr))) if pr else float('inf'),
        dd=dd, maxg=max(pts), maxp=min(pts), reais=tot * VAL_PONTO * CONTRATOS,
        ndias=ndias,
        longs=sum(1 for t in trades if t['lado'] > 0),
        shorts=sum(1 for t in trades if t['lado'] < 0),
        pts_long=sum(t['pts'] for t in trades if t['lado'] > 0),
        pts_short=sum(t['pts'] for t in trades if t['lado'] < 0),
    )


def linha_metricas(nome, m):
    if m is None:
        return '%-34s  sem trades' % nome
    return ('%-34s %6d %+9.0f %+8.1f %6.1f%% %6d %6d %6d %6d %7.2f %+9.0f'
            % (nome, m['n'], m['total'], m['media'], m['acerto'],
               m['alvos'], m['stops'], m['stops_p'], m['fech'], m['pf'], m['dd']))


CAB = ('%-34s %6s %9s %8s %7s %6s %6s %6s %6s %7s %9s'
       % ('SETUP', 'TRADES', 'PTS', 'PTS/TR', 'ACERTO', 'ALVO', 'STOP', 'STOP+', 'FECH', 'PF', 'DD'))
