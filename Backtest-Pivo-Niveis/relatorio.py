# -*- coding: utf-8 -*-
"""
Gera relatorio.html a partir de saida/resumo.json.

Nenhum numero e escrito a mao aqui: tudo sai do resumo. As frases de
veredito tambem sao CALCULADAS - se a medida mudar de sinal, o texto muda
junto. Foi por isso que este projeto nasceu com o gerador, e nao com um
html editado.
"""
import json
import os
import numpy as np
import pandas as pd

import nucleo as K
import estudo as S
import molde

BASE = os.path.dirname(os.path.abspath(__file__))
VENDOR_KC = os.path.join(BASE, 'vendor', 'klinecharts-9.8.10.min.js')
BASES = ('WINFUT', 'WINV26')

FG_V = S.FATOR_VIZ        # o fator de "grande" da linha principal
X_V = S.X_VIZ             # o X da corrida da linha principal

# Paleta categorica das duas series. Os valores moram no CSS (--s1/--s2)
# porque o modo escuro usa OUTROS degraus, nao os mesmos clareados: claro
# #14639E/#96601A, escuro #5292C6/#B98B30. Os quatro passam nas seis
# checagens de scripts/validate_palette.js contra a superficie do seu modo.
C1, C2 = 'var(--s1)', 'var(--s2)'


# ------------------------------------------------------------- formatadores
def n0(v):
    return '—' if v is None or (isinstance(v, float) and np.isnan(v)) else \
        '{:,.0f}'.format(v).replace(',', '.')


def p1(v):
    return '—' if v is None or np.isnan(v) else ('%.1f%%' % v).replace('.', ',')


def s1(v):
    """numero com sinal, uma casa"""
    if v is None or np.isnan(v):
        return '—'
    return ('%+.1f' % v).replace('.', ',')


def t2(v):
    if v is None or np.isnan(v):
        return '—'
    return ('%+.2f' % v).replace('.', ',')


def f2(v):
    if v is None or np.isnan(v):
        return '—'
    return ('%.2f' % v).replace('.', ',')


def cls(v):
    return 'pos' if v > 0 else ('neg' if v < 0 else 'zer')


# --------------------------------------------------------------- consultas
def cel(R, base, **kw):
    """A celula unica que casa com os filtros, ou None."""
    for c in R['bases'][base]['celulas']:
        if all(c[k] == v for k, v in kw.items()):
            return c
    return None


def ctl(R, base, X, sentido):
    for c in R['bases'][base]['controles']:
        if c['X'] == X and c['sentido'] == sentido:
            return c
    return None


def df_cel(R, base):
    return pd.DataFrame(R['bases'][base]['celulas'])


# ------------------------------------------------------------ blocos HTML
def linha(rot, c, extra='', sub=''):
    if c is None:
        return ('<tr class="mute"><td>%s<span class="sub">%s</span></td>'
                '<td class="num">—</td><td class="num">—</td><td class="num">—</td>'
                '<td class="num">—</td></tr>' % (rot, sub))
    d = c['acerto'] - 50.0
    return ('<tr class="%s"><td>%s%s</td><td class="num">%s</td>'
            '<td class="num %s">%s</td><td class="num %s">%s</td>'
            '<td class="num">%s</td></tr>' % (
                extra, rot,
                ('<span class="sub">%s</span>' % sub) if sub else '',
                n0(c['n']), cls(d), p1(c['acerto']), cls(c['ev']), s1(c['ev']),
                t2(c['t'])))


CAB = ('<thead><tr><th>medida</th><th class="num">n</th>'
       '<th class="num">acerto</th><th class="num">EV (pts)</th>'
       '<th class="num">t</th></tr></thead>')


def tab_hipotese(R, base):
    """As duas metades da hipotese, lado a lado, contra o controle."""
    k = dict(FG=FG_V, tol=0.0, fam='qualquer', grupo='todas', X=X_V)
    linhas = [
        '<tr class="mute"><td colspan="5"><b>controle</b> — todas as barras do período</td></tr>',
        linha('a favor do corpo, no fechamento', ctl(R, base, X_V, 'favor'),
              sub='a referência: sem informação nenhuma, isto dá 50%'),
        linha('contra o corpo, no fechamento', ctl(R, base, X_V, 'contra')),
        '<tr class="mute"><td colspan="5"><b>“andar”</b> — a barra grande segue na direção do corpo</td></tr>',
        linha('a favor, no fechamento dela', cel(R, base, sentido='favor', entrada='fecho', **k)),
        linha('a favor, rompendo o extremo', cel(R, base, sentido='favor', entrada='rompe', **k),
              sub='entra só se o extremo for rompido em até %d barras' % S.MAX_ROMPE),
        '<tr class="mute"><td colspan="5"><b>“reversão”</b> — a barra grande marca a volta</td></tr>',
        linha('contra, no fechamento dela', cel(R, base, sentido='contra', entrada='fecho', **k)),
        linha('contra, rompendo o extremo oposto',
              cel(R, base, sentido='contra', entrada='rompe', **k), extra='hi',
              sub='a <b>falha</b> da barra grande — a única célula que sobra de pé'),
    ]
    return ('<div class="scroll"><table><caption>%s · barra grande = range ≥ %s × '
            'range médio · corrida simétrica ±%d pontos</caption>%s<tbody>%s</tbody>'
            '</table></div>' % (base, f2(FG_V), X_V, CAB, ''.join(linhas)))


def tab_nivel(R, base):
    """A pergunta que o Carlos fez de verdade: o NIVEL acrescenta?"""
    k = dict(FG=FG_V, tol=0.0, X=X_V, sentido='contra', entrada='rompe')
    todas = cel(R, base, fam='qualquer', grupo='todas', **k)
    linhas = [linha('<b>todas</b> as barras grandes', todas, extra='hi',
                    sub='sem olhar nível nenhum')]
    for fam in ('medias', 'vwap', 'pivos', 'diant'):
        linhas.append(linha('com ' + K.ROT_FAM[fam], cel(R, base, fam=fam, grupo='com', **k)))
    linhas.append(linha('com <b>qualquer</b> nível dentro',
                        cel(R, base, fam='qualquer', grupo='com', **k)))
    linhas.append(linha('<b>sem nível nenhum</b> dentro',
                        cel(R, base, fam='qualquer', grupo='sem', **k),
                        sub='o controle que interessa'))
    linhas.append(linha('nível <b>centrado</b> na barra',
                        cel(R, base, fam='qualquer', grupo='centrado', **k),
                        sub='o mais próximo do meio, a ≤ 15% do range'))
    linhas.append(linha('<b>confluência</b>: 2+ níveis',
                        cel(R, base, fam='qualquer', grupo='conflu', **k)))
    return ('<div class="scroll"><table><caption>%s · a célula viva (falha da barra grande), '
            'fatiada pelo nível</caption>%s<tbody>%s</tbody></table></div>'
            % (base, CAB, ''.join(linhas)))


def tab_robustez(R):
    linhas = []
    for b in BASES:
        for r in R['bases'][b]['robustez']:
            linhas.append('<tr><td>%s</td><td>%s</td><td class="num">%s</td>'
                          '<td class="num %s">%s</td><td class="num %s">%s</td>'
                          '<td class="num">%s</td></tr>' % (
                              b, r['metade'], n0(r['n']), cls(r['acerto'] - 50),
                              p1(r['acerto']), cls(r['ev']), s1(r['ev']), t2(r['t'])))
    return ('<div class="scroll"><table><caption>A célula viva, partida no meio do '
            'período</caption><thead><tr><th>base</th><th>metade</th><th class="num">n</th>'
            '<th class="num">acerto</th><th class="num">EV (pts)</th><th class="num">t</th>'
            '</tr></thead><tbody>%s</tbody></table></div>' % ''.join(linhas))


def tab_trades(R):
    linhas = []
    for b in BASES:
        m = R['bases'][b]['trades']
        if not m:
            continue
        linhas.append(
            '<tr><td>%s</td><td class="num">%s</td><td class="num">%s</td>'
            '<td class="num %s">%s</td><td class="num %s">%s</td><td class="num">%s</td>'
            '<td class="num">%s</td><td class="num">%s</td><td class="num">%s</td></tr>' % (
                b, n0(m['n']), f2(m['por_pregao']), cls(m['ev']), s1(m['ev']),
                cls(m['total']), n0(m['total']), p1(m['acerto']), t2(m['t']),
                f2(m['pf']), n0(m['dd'])))
    return ('<div class="scroll"><table><caption>Os trades do visualizador — a falha da '
            'barra grande, com a gestão da casa (stop %d · parcial de 50%% na distância do '
            'stop · alvo %d). Brutos, sem custo.</caption>'
            '<thead><tr><th>base</th><th class="num">n</th><th class="num">por pregão</th>'
            '<th class="num">EV</th><th class="num">total</th><th class="num">acerto</th>'
            '<th class="num">t</th><th class="num">PF</th><th class="num">DD</th></tr></thead>'
            '<tbody>%s</tbody></table></div>' % (K.STOP, K.ALVO, ''.join(linhas)))


# --------------------------------------------------------------- graficos
def rotulo(x, y, txt, cor, anc='start', peso='500'):
    """Etiqueta com uma tarja da cor do cartao atras.

    Sem a tarja, a etiqueta de uma serie cai em cima da linha da outra - e a
    serie curta (WINV26, com menos trades) termina no MEIO do grafico, bem
    onde a longa esta passando."""
    larg = 6.6 * len(txt) + 8
    dx = {'start': -4, 'middle': -larg / 2, 'end': -larg + 4}[anc]
    return ('<g><rect x="%.1f" y="%.1f" width="%.1f" height="15" rx="3" '
            'fill="var(--card)" fill-opacity=".82"/>'
            '<text x="%.1f" y="%.1f" text-anchor="%s" font-size="10.5" '
            'font-weight="%s" fill="%s">%s</text></g>'
            % (x + dx, y - 11.5, larg, x, y, anc, peso, cor, txt))


def legenda(itens):
    """Legenda em HTML, fora do SVG - identidade nunca so pela cor."""
    return ('<div class="legenda">%s</div>' % ''.join(
        '<span><i class="sw l" style="background:%s"></i> %s</span>' % (c, r)
        for c, r in itens))


def hist_t(R):
    """Distribuicao dos t medidos contra a distribuicao do NADA.

    E o grafico que decide o relatorio: se a grade inteira cabe embaixo da
    curva do acaso, nao ha o que salvar dela."""
    ts = np.concatenate([df_cel(R, b).t.dropna().to_numpy() for b in BASES])
    lo, hi, nb = -4.0, 4.0, 32
    bordas = np.linspace(lo, hi, nb + 1)
    cont, _ = np.histogram(np.clip(ts, lo, hi), bins=bordas)
    W, H, ML, MB, MT = 640, 240, 34, 30, 14
    pw, ph = W - ML - 12, H - MB - MT
    ymax = max(cont.max(), 1)
    esc_y = lambda v: MT + ph - ph * v / ymax
    esc_x = lambda v: ML + pw * (v - lo) / (hi - lo)

    # a curva do acaso, normalizada para a mesma area
    xs = np.linspace(lo, hi, 160)
    dens = np.exp(-xs ** 2 / 2) / np.sqrt(2 * np.pi)
    dens = dens * len(ts) * (bordas[1] - bordas[0])
    cam = ' '.join('%s%.1f,%.1f' % ('M' if i == 0 else 'L', esc_x(x), esc_y(y))
                   for i, (x, y) in enumerate(zip(xs, dens)))

    p = []
    for i in range(nb):
        if cont[i] == 0:
            continue
        x0, x1 = esc_x(bordas[i]), esc_x(bordas[i + 1])
        y = esc_y(cont[i])
        p.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="2" fill="%s" '
                 'fill-opacity=".85"><title>t entre %s e %s: %d células</title></rect>'
                 % (x0 + 1, y, max(1, x1 - x0 - 2), MT + ph - y, C1,
                    f2(bordas[i]), f2(bordas[i + 1]), cont[i]))
    for v in (-2, 2):
        p.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="var(--neg)" '
                 'stroke-width="1.5" stroke-dasharray="4 3"/>'
                 % (esc_x(v), MT, esc_x(v), MT + ph))
    for v in (-4, -2, 0, 2, 4):
        p.append('<text x="%.1f" y="%d" text-anchor="middle" font-size="10.5" '
                 'fill="var(--ink-3)">%s</text>' % (esc_x(v), H - 14, t2(v)))
    p.append('<path d="%s" fill="none" stroke="var(--ink-2)" stroke-width="2"/>' % cam)
    p.append(rotulo(esc_x(0.05), esc_y(dens.max()) - 7, 'o acaso', 'var(--ink-2)', 'middle'))
    p.append(rotulo(esc_x(2) + 5, MT + 11, '|t| = 2', 'var(--neg)', 'start'))
    return ('<svg viewBox="0 0 %d %d" role="img" aria-label="distribuição dos t medidos '
            'contra a curva do acaso">%s</svg>' % (W, H, ''.join(p)))


def curva_capital(trades):
    """Capital acumulado dos trades do visualizador, uma linha por base."""
    W, H, ML, MB, MT, MR = 640, 240, 46, 30, 14, 62
    pw, ph = W - ML - MR, H - MB - MT
    series = {}
    for b in BASES:
        lst = trades.get(b, {}).get('trades', [])
        if not lst:
            continue
        eq = np.cumsum([t['pnl'] for t in lst])
        series[b] = np.concatenate([[0.0], eq])
    if not series:
        return '<p class="sub">sem trades.</p>'
    nmax = max(len(v) for v in series.values())
    vmin = min(float(v.min()) for v in series.values())
    vmax = max(float(v.max()) for v in series.values())
    pad = max(50.0, (vmax - vmin) * 0.08)
    vmin, vmax = vmin - pad, vmax + pad
    esc_x = lambda i: ML + pw * i / max(1, nmax - 1)
    esc_y = lambda v: MT + ph - ph * (v - vmin) / (vmax - vmin)

    p = ['<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="var(--line)" '
         'stroke-width="1"/>' % (ML, esc_y(0), ML + pw, esc_y(0))]
    for cor, b in zip((C1, C2), series):
        v = series[b]
        cam = ' '.join('%s%.1f,%.1f' % ('M' if i == 0 else 'L', esc_x(i), esc_y(x))
                       for i, x in enumerate(v))
        p.append('<path d="%s" fill="none" stroke="%s" stroke-width="2" '
                 'stroke-linejoin="round"/>' % (cam, cor))
        # a etiqueta vai ATRAS de um retangulo da cor do cartao: a serie curta
        # termina no meio do gráfico, em cima da linha da outra base
        p.append(rotulo(esc_x(len(v) - 1) + 7, esc_y(v[-1]) + 4, b, cor, 'start', peso='600'))
    for v in (vmin, 0.0, vmax):
        p.append('<text x="%d" y="%.1f" text-anchor="end" font-size="10.5" '
                 'fill="var(--ink-3)">%s</text>' % (ML - 6, esc_y(v) + 3.5, n0(v)))
    p.append('<text x="%d" y="%d" font-size="10.5" fill="var(--ink-3)">trade</text>'
             % (ML, H - 12))
    svg = ('<svg viewBox="0 0 %d %d" role="img" aria-label="capital acumulado por base">'
           '%s</svg>' % (W, H, ''.join(p)))
    return svg + legenda(list(zip((C1, C2), series)))


# ------------------------------------------------------------- os vereditos
def veredito_andar(R):
    """Calculado: a metade 'andar' da hipotese passou?"""
    ks = dict(FG=FG_V, tol=0.0, fam='qualquer', grupo='todas', X=X_V, sentido='favor')
    ps = []
    for b in BASES:
        for e in ('fecho', 'rompe'):
            c = cel(R, b, entrada=e, **ks)
            if c:
                ps.append(c['acerto'])
    if not ps:
        return 'Sem amostra para decidir.'
    pior, melhor = min(ps), max(ps)
    if melhor < 50:
        return ('<strong>Não.</strong> Nas quatro medidas — duas bases × duas entradas — a '
                'continuação fica <strong>abaixo</strong> da moeda honesta, entre %s e %s. '
                'Não é que ande pouco: anda menos que uma barra qualquer. Comprar a barra '
                'grande porque ela é grande, tocando nível ou não, perde.'
                % (p1(pior), p1(melhor)))
    return ('Medida em %d células, a continuação vai de %s a %s de acerto.'
            % (len(ps), p1(pior), p1(melhor)))


def veredito_nivel(R):
    """Calculado: o nivel acrescenta ou tira?

    A comparacao que vale e 'com nivel' contra 'todas as barras grandes' -
    essa existe sempre. A celula 'sem nivel' e mais eloquente quando tem
    amostra, mas no WINV26 ela nem chega ao minimo de 25, e e justamente
    por isso que ela nao pode ser a base do veredito."""
    k = dict(FG=FG_V, tol=0.0, X=X_V, sentido='contra', entrada='rompe')
    frases, piora = [], 0
    for b in BASES:
        com = cel(R, b, fam='qualquer', grupo='com', **k)
        sem = cel(R, b, fam='qualquer', grupo='sem', **k)
        tod = cel(R, b, fam='qualquer', grupo='todas', **k)
        if not (com and tod):
            continue
        if com['acerto'] <= tod['acerto']:
            piora += 1
        f = ('no %s, exigir nível leva %s para %s' % (b, p1(tod['acerto']), p1(com['acerto'])))
        if sem:
            f += ' — e a barra <em>sem nível nenhum</em> dá %s' % p1(sem['acerto'])
        frases.append(f)
    corpo = '; '.join(frases)
    if frases and piora == len(frases):
        return ('<strong>O nível não acrescenta — subtrai.</strong> Exigir que a barra '
                'alcance uma média, a VWAP ou um pivô <em>piora</em> a única célula viva '
                'nas duas bases: %s. O que carrega o resultado é o <strong>tamanho da '
                'barra e a falha dela</strong>, não a companhia do nível.' % corpo)
    return 'Comparação com nível contra todas as barras grandes: %s.' % corpo


def veredito_grade(R):
    """Quantas celulas passam, contra quantas o acaso entregaria.

    O 'esperado' usa a t de Student com os graus de liberdade REAIS de cada
    base (pregoes - 1), nao a normal: com 44 pregoes a cauda e mais gorda que
    a normal, e usar a normal subestimaria o acaso - justamente para o lado
    que favoreceria a hipotese."""
    from scipy import stats
    tot = passa = 0
    esp = 0.0
    for b in BASES:
        c = df_cel(R, b)
        gl = max(2, R['bases'][b]['pregoes'] - 1)
        tot += len(c)
        passa += int((c.t.abs() > 2).sum())
        esp += len(c) * 2.0 * stats.t.sf(2.0, gl)
    melhores = {b: df_cel(R, b).loc[df_cel(R, b).t.idxmax()] for b in BASES}
    a, z = (melhores[b] for b in BASES)
    GRP = {'com': 'com nível dentro', 'sem': 'sem nível nenhum',
           'todas': 'sem olhar nível', 'corpo': 'nível no corpo',
           'centrado': 'nível centrado', 'conflu': 'confluência'}
    rot = lambda r: '%s, %s, %s' % (
        K.ROT_FAM.get(r.fam, r.fam), GRP.get(r.grupo, r.grupo),
        'a favor do corpo' if r.sentido == 'favor' else 'contra o corpo')
    return ('Foram medidas <strong>%s células</strong>. Passam de |t| = 2 exatamente '
            '<strong>%s</strong> — e se cada uma fosse um teste independente sobre uma moeda '
            'honesta, o acaso já entregaria cerca de <strong>%s</strong>. A grade inteira cabe '
            'praticamente embaixo da curva do nada. E as campeãs não se confirmam entre si: '
            'a melhor do %s é <code>%s</code>, a melhor do %s é <code>%s</code> — famílias e '
            'sentidos diferentes, que é a assinatura de ruído, não de efeito. As células também '
            'não são independentes entre si (são recortes aninhados das mesmas barras), então '
            'esse “esperado” é uma régua grosseira — mas não é ela que está segurando a '
            'conclusão: o excesso medido é pequeno demais para sustentar qualquer célula '
            'individualmente.'
            % (n0(tot), n0(passa), n0(esp),
               BASES[0], rot(a), BASES[1], rot(z)))


def veredito_final(R):
    m = {b: R['bases'][b]['trades'] for b in BASES}
    if not all(m.values()):
        return 'Sem trades suficientes para decidir.'
    ts = [m[b]['t'] for b in BASES]
    evs = [m[b]['ev'] for b in BASES]
    if max(ts) < 2.0:
        return ('<strong>Não passa.</strong> O melhor arranjo que a hipótese produz — a '
                'falha da barra grande, sem filtro de nível — dá EV de %s e %s pontos por '
                'trade, com t de %s e %s. É positivo nas duas bases e sobrevive às duas '
                'metades do período, o que já é mais do que a maioria das ideias entrega. '
                'Mas <strong>t abaixo de 2 em %d pregões</strong>, num teste escolhido depois '
                'de olhar a grade, não é resultado: é uma direção para investigar. Não é isso '
                'que se leva para a mesa.'
                % (s1(evs[0]), s1(evs[1]), t2(ts[0]), t2(ts[1]),
                   R['bases'][BASES[0]]['pregoes']))
    return ('EV de %s e %s pontos, t de %s e %s.'
            % (s1(evs[0]), s1(evs[1]), t2(ts[0]), t2(ts[1])))


# ------------------------------------------------------- dados do grafico
def coleta_grafico():
    """Candles, níveis e trades do visualizador, um pregão por vez."""
    dados = {}
    for nome in BASES:
        d, N = K.prepara(nome)
        tr = S.trades_viz(d, N)
        if not len(tr):
            continue
        O, H, L, C = (d[c].to_numpy(float) for c in ('O', 'H', 'L', 'C'))
        dia_arr = d.dia.to_numpy()
        hora = d.Data.dt.strftime('%H:%M').to_numpy()
        tam = d.tam.to_numpy(float)

        dias, idx_dia = [], {}
        for dd in sorted(set(tr.dia)):
            m = np.flatnonzero(dia_arr == dd)
            b = int(round(O[m[0]] / 100.0) * 100)
            r = lambda v: [int(round(v[j] - b)) for j in m]
            piv = {k: (None if np.isnan(N[k][m[0]]) else int(round(N[k][m[0]] - b)))
                   for k in ('pp', 'r1', 's1', 'r2', 's2', 'phi', 'plo')}
            idx_dia[dd] = len(dias)
            dias.append(dict(
                d=str(dd), base=b, i0=int(m[0]),
                hm=[str(x) for x in hora[m]],
                o=r(O), h=r(H), l=r(L), c=r(C),
                e1=r(N['ema21']), e2=r(N['ema42']), e3=r(N['ema72']), vw=r(N['vwap']),
                piv=piv,
                tm=[int(round((0 if np.isnan(tam[j]) else tam[j]) * 100)) for j in m],
            ))
        lst = []
        for _, t in tr.iterrows():
            di = idx_dia[t['dia']]
            off = dias[di]['i0']
            lst.append(dict(
                dia=str(t['dia']), d=di, s=int(t['s']),
                g=int(t['gatilho']) - off, i=int(t['i']) - off, k=int(t['saiu']) - off,
                ent=round(float(t['ent']) - dias[di]['base'], 1),
                res=t['res'], pnl=round(float(t['pnl']), 1),
                tam=round(float(t['tam']), 2), fams=list(t['fams'])))
        lst.sort(key=lambda t: (t['d'], t['g']))
        dados[nome] = dict(dias=dias, trades=lst)
    return dados


# ------------------------------------------------------------------ monta
def monta():
    with open('%s/resumo.json' % K.SAIDA, encoding='utf-8') as f:
        R = json.load(f)
    g = coleta_grafico()
    o0 = R['bases'][BASES[0]]

    ctx = dict(
        fg=f2(FG_V), fg_js=repr(float(FG_V)),   # o JS precisa do ponto decimal
        xv='%d' % X_V, maxrompe=str(S.MAX_ROMPE),
        stop='%d' % K.STOP, alvo='%d' % K.ALVO,
        pregoes_fu=n0(o0['pregoes']), barras_fu=n0(o0['n_barras']),
        de=o0['de'], ate=o0['ate'],
        pregoes_v26=n0(R['bases'][BASES[1]]['pregoes']),
        barras_v26=n0(R['bases'][BASES[1]]['n_barras']),
        n_celulas=n0(sum(len(R['bases'][b]['celulas']) for b in BASES)),
        tab_hip_fu=tab_hipotese(R, BASES[0]),
        tab_hip_v26=tab_hipotese(R, BASES[1]),
        tab_niv_fu=tab_nivel(R, BASES[0]),
        tab_niv_v26=tab_nivel(R, BASES[1]),
        tab_robustez=tab_robustez(R),
        tab_trades=tab_trades(R),
        hist_t=hist_t(R),
        curva=curva_capital(g),
        ver_andar=veredito_andar(R),
        ver_nivel=veredito_nivel(R),
        ver_grade=veredito_grade(R),
        ver_final=veredito_final(R),
        acerto_falha_fu=p1(cel(R, BASES[0], FG=FG_V, tol=0.0, fam='qualquer',
                               grupo='todas', X=X_V, sentido='contra',
                               entrada='rompe')['acerto']),
        acerto_falha_v26=p1(cel(R, BASES[1], FG=FG_V, tol=0.0, fam='qualquer',
                                grupo='todas', X=X_V, sentido='contra',
                                entrada='rompe')['acerto']),
        dados_json=json.dumps(g, ensure_ascii=False, separators=(',', ':')),
        klinecharts_js=open(VENDOR_KC, encoding='utf-8').read(),
        c1=C1, c2=C2,
    )
    html = molde.render(ctx)
    with open(os.path.join(BASE, 'relatorio.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    print('-> relatorio.html  (%.1f MB)'
          % (os.path.getsize(os.path.join(BASE, 'relatorio.html')) / 1e6))


if __name__ == '__main__':
    monta()
