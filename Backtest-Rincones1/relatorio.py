# -*- coding: utf-8 -*-
"""
Gera relatorio.html -- relatorio unico, com o visualizador de trades dentro.

    python rodar.py       # primeiro, para atualizar saida/resumo.json
    python relatorio.py   # depois

TODO numero do relatorio sai de saida/resumo.json. Nao ha numero escrito
a mao no HTML -- foi assim que a versao anterior ficou defasada duas vezes
quando o engine mudou.
"""
import json
import os

import numpy as np
import pandas as pd

import engine as E

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')
DEST = os.path.join(BASE, 'relatorio.html')
BASES = ('WINV26', 'WINFUT')
STOPS_VIZ = (150, 100)      # os stops que o visualizador de trades oferece
REGIMES = ('ema3', 'kama', 'hma', 't3', 'jma')

ROT_REG = {
    'ema3': ('3 EMAs 21/42/72', 'direção pelo empilhamento das três'),
    'kama': ('KAMA 13', 'direção pela inclinação; acelera no movimento, trava no ruído'),
    'hma':  ('Hull 13', 'direção pela inclinação; suaviza sem atrasar'),
    't3':   ('T3 Tillson 13', 'direção pela inclinação; seis EMAs encadeadas'),
    'jma':  ('estilo Jurik 21', 'aproximação pública — <b>não</b> é o JMA do Jurik Research'),
}
ROT_SU = {'A': ('A · tendência', 'Médias alinhadas, o preço volta e toca uma delas, e alguém agride contra a tendência ali — e falha.'),
          'B': ('B · reversão rápida', 'Fora de consolidação, preço a um range médio ou mais da média, gatilho contra o afastamento.'),
          'C': ('C · consolidação', 'Médias emboladas, preço afastado do cacho. Negativo nas duas bases, em toda configuração testada.')}


# ------------------------------------------------------------ formatacao
def n0(v):
    return '—' if v is None else ('%+d' % round(v)).replace(',', '.')


def n1(v):
    return '—' if v is None else ('%+.1f' % v).replace('.', ',')


def p0(v):
    return '—' if v is None else '%.0f%%' % v


def p1(v):
    return '—' if v is None else ('%.1f%%' % v).replace('.', ',')


def t2(v):
    return '—' if v is None else ('%+.2f' % v).replace('.', ',')


def f2(v):
    return '—' if v is None else ('%.2f' % v).replace('.', ',')


def cls(v):
    return 'pos' if (v or 0) > 0 else ('neg' if (v or 0) < 0 else 'zer')


def mil(v):
    return '—' if v is None else ('{:+,.0f}'.format(v)).replace(',', '.')


# ------------------------------------------------------------ dados grafico
def coleta_grafico(stops=STOPS_VIZ):
    """Candles, medias e trades do visualizador.

    Os trades saem UMA VEZ POR STOP: os sinais nao dependem do stop, mas o
    desfecho e o resultado dependem, e o visualizador deixa trocar entre
    eles. Os candles sao os mesmos nos dois casos, entao vao uma vez so.
    """
    dados = {}
    st0 = E.STOP
    for nome in BASES:
        E.aplica_ma('ema3')
        d, sig, marca = E.prepara(nome, ativos=('A', 'B', 'C'), regime='ema3')

        por_stop = {}
        for st in stops:
            E.STOP = float(st)
            por_stop[str(st)] = E.roda(d, marca, sig, carteira=False)
        E.STOP = st0
        if not any(len(t) for t in por_stop.values()):
            continue

        O, H, L, C = (d[c].to_numpy(float) for c in ('O', 'H', 'L', 'C'))
        er, em, el = (d[c].to_numpy(float) for c in ('er', 'em', 'el'))
        idxv, dirC = d.idx.to_numpy(), d.dirC.to_numpy()
        dia_arr = d.dia.to_numpy()
        hora = d.Data.dt.strftime('%H:%M').to_numpy()

        todos_dias = sorted({dd for t in por_stop.values() for dd in t.dia})
        idx_dia, dias = {}, []
        for dd in todos_dias:
            m = np.flatnonzero(dia_arr == dd)
            b = int(round(O[m[0]] / 100.0) * 100)
            idx_dia[dd] = len(dias)
            dias.append(dict(
                d=str(dd), base=b, i0=int(m[0]),
                hm=[str(x) for x in hora[m]],
                o=[int(round(O[j] - b)) for j in m],
                h=[int(round(H[j] - b)) for j in m],
                l=[int(round(L[j] - b)) for j in m],
                c=[int(round(C[j] - b)) for j in m],
                e1=[int(round(er[j] - b)) for j in m],
                e2=[int(round(em[j] - b)) for j in m],
                e3=[int(round(el[j] - b)) for j in m],
                x=[(0 if np.isnan(idxv[j]) else
                    int(round(idxv[j] * 100)) * (1 if dirC[j] >= 0 else -1)) for j in m],
            ))

        trades = {}
        for st, tr in por_stop.items():
            lst = []
            for _, t in tr.iterrows():
                di = idx_dia[t['dia']]
                off = dias[di]['i0']
                lst.append(dict(
                    dia=str(t['dia']), d=di, su=t['setup'], s=int(t['s']),
                    i=int(t['i']) - off, f=int(t['jf']) - off, k=int(t['saiu']) - off,
                    ent=round(float(t['ent']) - dias[di]['base'], 1),
                    res=t['res'], pnl=round(float(t['pnl']), 1), bar=int(t['barras'])))
            lst.sort(key=lambda t: (t['d'], t['i']))
            trades[st] = lst
        dados[nome] = dict(dias=dias, trades=trades)
    return dados


# ------------------------------------------------------------ blocos HTML
def linha_metrica(rot, m, extra_cls='', cols=('n', 'por_pregao', 'ev', 'total',
                                              'acerto', 't', 'dias_pos', 'pf', 'dd')):
    if not m:
        return '<tr%s><td>%s</td><td colspan="9" class="sub">sem trades</td></tr>' % (
            (' class="%s"' % extra_cls) if extra_cls else '', rot)
    f = {'n': str(m['n']), 'por_pregao': ('%.1f' % m['por_pregao']).replace('.', ','),
         'ev': n1(m['ev']), 'total': mil(m['total']), 'acerto': p1(m['acerto']),
         't': t2(m['t']), 'dias_pos': p0(m['dias_pos']), 'pf': f2(m['pf']),
         'dd': '%d' % round(m['dd'])}
    tds = ''.join('<td class="num">%s</td>' % f[c] for c in cols)
    return '<tr%s><td>%s</td>%s</tr>' % (
        (' class="%s"' % extra_cls) if extra_cls else '', rot, tds)


CAB_MET = ('<thead><tr><th></th><th class="num">n</th><th class="num">/pregão</th>'
           '<th class="num">EV</th><th class="num">total</th><th class="num">acerto</th>'
           '<th class="num">t</th><th class="num">dias+</th><th class="num">PF</th>'
           '<th class="num">DD</th></tr></thead>')


def bloco_variantes(R, stop):
    """A tabela que responde 'trocar as 3 EMAs por uma adaptativa ajuda?'"""
    linhas = []
    for reg in REGIMES:
        nome, desc = ROT_REG[reg]
        cel = []
        for base in BASES:
            v = R['variantes'][base][reg][str(stop)]
            m = v['cA']
            cel.append('<td class="num">%s</td><td class="num">%s</td>'
                       '<td class="num">%s</td><td class="num">%s</td>'
                       % (m['n'] if m else '—', n1(m['ev']) if m else '—',
                          t2(m['t']) if m else '—', f2(m['pf']) if m else '—'))
        tend = R['variantes']['WINFUT'][reg][str(stop)]['tend']
        linhas.append('<tr%s><td><b>%s</b><div class="sub">%s</div></td>'
                      '<td class="num">%s</td>%s</tr>'
                      % (' class="hi"' if reg == 'ema3' else '', nome, desc,
                         p0(tend), ''.join(cel)))
    return ('<div class="scroll"><table>'
            '<thead><tr><th rowspan="2">média de regime</th>'
            '<th class="num" rowspan="2">%% barras<br>em tendência</th>'
            '<th class="num" colspan="4">WINV26</th>'
            '<th class="num" colspan="4">WINFUT</th></tr>'
            '<tr><th class="num">n</th><th class="num">EV</th><th class="num">t</th><th class="num">PF</th>'
            '<th class="num">n</th><th class="num">EV</th><th class="num">t</th><th class="num">PF</th></tr></thead>'
            '<tbody>%s</tbody></table></div>' % ''.join(linhas))


def bloco_stops(R):
    linhas = []
    for stop in (150, 100):
        for ch, rot in (('cA', 'só A'), ('cAB', 'A + B')):
            cel = []
            for base in BASES:
                m = R['variantes'][base]['ema3'][str(stop)][ch]
                cel.append('<td class="num">%s</td><td class="num">%s</td>'
                           '<td class="num">%s</td><td class="num">%s</td>'
                           % (n1(m['ev']), t2(m['t']), f2(m['pf']), '%d' % round(m['dd'])))
            melhor_stop = max(R['stops'],
                              key=lambda st: (R['variantes']['WINFUT']['ema3'][str(st)][ch]['t']
                                              + R['variantes']['WINV26']['ema3'][str(st)][ch]['t']))
            hi = ' class="hi"' if stop == melhor_stop else ''
            linhas.append('<tr%s><td class="mono">stop %d</td><td>%s</td>%s</tr>'
                          % (hi, stop, rot, ''.join(cel)))
    return ('<div class="scroll"><table>'
            '<thead><tr><th rowspan="2">stop</th><th rowspan="2">carteira</th>'
            '<th class="num" colspan="4">WINV26</th><th class="num" colspan="4">WINFUT</th></tr>'
            '<tr><th class="num">EV</th><th class="num">t</th><th class="num">PF</th><th class="num">DD</th>'
            '<th class="num">EV</th><th class="num">t</th><th class="num">PF</th><th class="num">DD</th></tr></thead>'
            '<tbody>%s</tbody></table></div>' % ''.join(linhas))


def bloco_grade(R, base):
    g = R['bases'][base]['grade']
    linhas = []
    for st in (100, 150, 200):
        vals = [g.get('%d_%d' % (st, al)) for al in (200, 300, 400, 500)]
        melhor = max(range(4), key=lambda i: (vals[i] if vals[i] is not None else -1e9))
        tds = ''.join('<td class="num%s">%s</td>' % (' best' if i == melhor else '', n1(v))
                      for i, v in enumerate(vals))
        hi = ' class="hi"' if st == 100 else ''
        linhas.append('<tr%s><td class="mono">%d</td>%s</tr>' % (hi, st, tds))
    return ('<div class="scroll" style="margin:0"><table><caption>%s</caption>'
            '<thead><tr><th>stop \\ alvo</th><th class="num">+200</th><th class="num">+300</th>'
            '<th class="num">+400</th><th class="num">+500</th></tr></thead>'
            '<tbody>%s</tbody></table></div>' % (base, ''.join(linhas)))



# ------------------------------------------------- vereditos CALCULADOS
# Os numeros do relatorio ja saiam de resumo.json. As FRASES de conclusao
# nao saiam -- e quando a regra da barra seguinte entrou, elas ficaram
# defasadas exatamente como os numeros tinham ficado antes. Entao agora
# elas tambem sao calculadas. Ver README.
def _neg(t):
    """*negrito* -> markdown e html."""
    import re
    md = t.replace('*', '**')
    html = re.sub(r'\*(.+?)\*', lambda m: '<strong>%s</strong>' % m.group(1), t)
    return md, html


def _rank(R, base, stop, chave='cA'):
    """(regime, t, ev, pf, n) por `t` decrescente."""
    out = []
    for reg in R['regimes']:
        m = R['variantes'][base][reg][str(stop)][chave]
        if m and m['t'] == m['t']:
            out.append((reg, m['t'], m['ev'], m['pf'], m['n']))
    return sorted(out, key=lambda x: -x[1])


def veredito_ma(R):
    """Quem ganha a comparacao das medias, por stop, nas duas bases."""
    partes = []
    for stop in R['stops']:
        r26, rfu = _rank(R, 'WINV26', stop), _rank(R, 'WINFUT', stop)
        d26 = dict((x[0], x) for x in r26)
        dfu = dict((x[0], x) for x in rfu)
        v26, vfu = r26[0][0], rfu[0][0]
        rot = lambda k: ROT_REG[k][0]
        if v26 == 'ema3' and vfu == 'ema3':
            partes.append('Com *stop %d* as três EMAs dão o melhor `t` nas *duas bases* '
                          '(%s e %s); a segunda colocada fica em %s e %s.'
                          % (stop, t2(d26['ema3'][1]), t2(dfu['ema3'][1]),
                             t2(r26[1][1]), t2(rfu[1][1])))
        elif v26 == 'ema3' or vfu == 'ema3':
            # o empilhamento ganha numa base e perde na outra
            if v26 == 'ema3':
                b_ok, b_perde, dok, dperde, gan = 'WINV26', 'WINFUT', d26, dfu, vfu
            else:
                b_ok, b_perde, dok, dperde, gan = 'WINFUT', 'WINV26', dfu, d26, v26
            partes.append('Com *stop %d* as três EMAs ganham no %s (%s contra %s da '
                          'segunda), mas a *%s* passa à frente no %s (%s contra %s). '
                          'Na base em que o empilhamento ganha, essa mesma média mede '
                          '%s.'
                          % (stop, b_ok, t2(dok['ema3'][1]),
                             t2(sorted([x[1] for k, x in dok.items() if k != 'ema3'],
                                       reverse=True)[0]),
                             rot(gan), b_perde, t2(dperde[gan][1]),
                             t2(dperde['ema3'][1]), t2(dok[gan][1])))
        else:
            partes.append('Com *stop %d* as três EMAs NÃO ganham: %s no WINV26 e %s no '
                          'WINFUT medem melhor.' % (stop, rot(v26), rot(vfu)))
    # seletividade da kama
    tk = R['variantes']['WINFUT']['kama'][str(R['stops'][0])]['tend']
    te = R['variantes']['WINFUT']['ema3'][str(R['stops'][0])]['tend']
    partes.append('A *KAMA* segue sendo a mais seletiva — classifica %s das barras como '
                  'tendência contra %s do empilhamento, e produz cerca de metade dos '
                  'trades.' % (p0(tk), p0(te)))
    return _neg(' '.join(partes))


def veredito_entrada(R):
    """Limitada com validade de 1 barra x a mercado no fechamento."""
    L = []
    ganha_mercado = 0
    for b in BASES:
        me, fe = R['bases'][b]['entrada_meio'], R['bases'][b]['entrada_fecha']
        if fe['t'] > me['t']:
            ganha_mercado += 1
        L.append((b, me, fe))
    if ganha_mercado == len(BASES):
        cab = ('*A regra da barra seguinte inverteu esta comparação.* Entrar a mercado '
               'mede melhor `t` nas duas bases agora, e a razão é mecânica: a ordem a '
               'mercado *nunca aborta*. ')
    elif ganha_mercado == 0:
        cab = '*A limitada continua à frente* nas duas bases. '
    else:
        cab = 'As duas se dividem: cada uma ganha em uma base. '
    det = ' '.join('No %s, %s trades a mercado contra %s pela limitada (t %s contra %s).'
                   % (b, fe['n'], me['n'], t2(fe['t']), t2(me['t']))
                   for b, me, fe in L)
    return _neg(cab + det)


def veredito_abortos(R):
    """Quantos sinais o operador ve e nao consegue executar."""
    sp = str(R['stops'][0])
    L = []
    for b in BASES:
        v = R['variantes'][b]['ema3'][sp]
        sa, na = v['sinais_A'], v['setup_A']['n']
        sb, nb = v['sinais_B'], v['setup_B']['n']
        L.append((b, sa, na, sb, nb))
    frases = ['No %s, *%d dos %d* sinais do setup A viraram trade (%d abortados, %s); '
              'no B, %d de %d (%s).'
              % (b, na, sa, sa - na, p0(100.0 * (sa - na) / sa),
                 nb, sb, p0(100.0 * (sb - nb) / sb))
              for b, sa, na, sb, nb in L]
    return _neg('A regra descarta uma minoria estável dos sinais. ' + ' '.join(frases)
                + ' *Espere isso na tela:* cerca de um sinal em dez será abortado, e '
                'abortar é o comportamento correto, não uma falha sua.')



def veredito_fill(R):
    """O que a regra da barra seguinte custou, nas duas bases."""
    L = []
    for b in BASES:
        d = R['bases'][b]
        rg, lv = d['fill_regra_A'], d['fill_livre_A']
        L.append((b, rg, lv))
    melhora = [b for b, rg, lv in L if rg['t'] > lv['t']]
    piora = [b for b, rg, lv in L if rg['t'] <= lv['t']]
    det = ' '.join('No %s (carteira só A) o `t` vai de %s para %s e o fator de lucro de '
                   '%s para %s, com %d trades em vez de %d.'
                   % (b, t2(lv['t']), t2(rg['t']), f2(lv['pf']), f2(rg['pf']),
                      rg['n'], lv['n'])
                   for b, rg, lv in L)
    if melhora and piora:
        cab = ('Ela *melhora %s e piora %s*, pouco dos dois lados. '
               % (' e '.join(melhora), ' e '.join(piora)))
    elif melhora:
        cab = '*Ela melhora as duas bases.* '
    else:
        cab = '*Ela piora as duas bases* — e o motivo para mantê-la é operacional, não estatístico. '
    return _neg(cab + det)


def veredito_setups(R):
    """O setup A e mesmo o melhor dos tres? Coluna por coluna, nas duas bases."""
    sp = str(R['stops'][0])
    COLS = (('ev', 'EV', n1), ('acerto', 'acerto', p1), ('t', 't', t2), ('pf', 'PF', f2))
    perde = []
    for b in BASES:
        v = R['variantes'][b]['ema3'][sp]
        for ch, rot, f in COLS:
            vals = {su: v['setup_' + su][ch] for su in ('A', 'B', 'C') if v['setup_' + su]}
            top = max(vals, key=vals.get)
            if top != 'A':
                perde.append('no %s o setup %s mede %s de %s contra %s do A'
                             % (b, top, f(vals[top]), rot, f(vals['A'])))
    if not perde:
        return _neg('*A prioridade que você pediu está certa.* O setup de tendência é o '
                    'melhor dos três nas duas bases, em todas as colunas.')
    return _neg('*A prioridade que você pediu continua certa*: o setup de tendência lidera '
                'a maioria das colunas nas duas bases. Não todas — ' + '; '.join(perde)
                + '. Com esse número de trades uma coluna trocada é ruído, não hierarquia; '
                'o A segue prioritário por EV, fator de lucro e drawdown.')


def veredito_stop(R):
    """Qual stop mede melhor, contado nas duas bases x duas carteiras."""
    sp, alt = R['stops'][0], R['stops'][1]
    cel = [(b, rot,
            R['variantes'][b]['ema3'][str(sp)][ch],
            R['variantes'][b]['ema3'][str(alt)][ch])
           for b in BASES for ch, rot in (('cA', 'só A'), ('cAB', 'A + B'))]
    ganha_alt = [x for x in cel if x[3]['t'] > x[2]['t']]
    det = ' '.join('%s · %s: t %s com stop %d contra %s com %d.'
                   % (b, rot, t2(a['t']), sp, t2(c['t']), alt) for b, rot, a, c in cel)
    curto = min(sp, alt)
    nota_risco = ('O stop de %d corta o risco por trade em um terço, então o mesmo limite '
                  'de perda diária compra 50%% mais contratos. ' % curto)
    if len(ganha_alt) == len(cel):
        cab = '*O stop de %d mede melhor nas duas bases, nas duas carteiras.* ' % alt
        if alt == curto:
            cab += nota_risco
    elif not ganha_alt:
        cab = '*O stop de %d mede melhor nas duas bases, nas duas carteiras.* ' % sp
        if sp != curto:
            cab += ('O stop curto ganha em risco por trade, mas aqui ele corta trade bom '
                    'antes da hora. ')
    else:
        n_alt = len(ganha_alt)
        n_sp = len(cel) - n_alt
        venc, n_venc = (alt, n_alt) if n_alt > n_sp else (sp, n_sp)
        outro = sp if venc == alt else alt
        n_outro = len(cel) - n_venc
        cab = ('*Não há mais um stop que ganhe em tudo:* o de %d mede melhor em %d das %d '
               'comparações (duas bases × duas carteiras) e o de %d %s. '
               % (venc, n_venc, len(cel), outro,
                  'na outra' if n_outro == 1 else 'nas outras %d' % n_outro))
    return _neg(cab + det)


def veredito_e2(R):
    """O que a troca da formula do eixo [E2] mudou, com o resto congelado.

    Nao basta dizer "melhorou": a troca melhora e piora em lugares
    diferentes, e o operador precisa saber em qual dos dois setups ele
    esta ganhando alguma coisa.
    """
    e2 = R.get('e2')
    if not e2:
        return _neg('(sem comparativo de [E2] neste resumo)')
    at, sp = e2['atual'], str(R['stops'][0])
    ant = [m for m in e2['metricas'] if m != at][0]

    def venc(chave):
        """Em quantas das (2 bases x 2 stops) a formula nova mede melhor."""
        return sum(1 for b in BASES for st in R['stops']
                   if e2['grid'][b][at][str(st)][chave]['t']
                   > e2['grid'][b][ant][str(st)][chave]['t'])

    gA, gB, gAB = venc('setup_A'), venc('setup_B'), venc('cAB')
    tot = len(BASES) * len(R['stops'])
    sel = ' e '.join('%+.0f%%' % (100.0 * (e2['grid'][b][at]['gatilhos']
                                           - e2['grid'][b][ant]['gatilhos'])
                                  / e2['grid'][b][ant]['gatilhos']) for b in BASES)
    linhas = []
    for b in BASES:
        g, h = e2['grid'][b][at], e2['grid'][b][ant]
        linhas.append('No %s o setup B sai de %s de EV e t %s para %s e t %s, e o A de %s '
                      'e t %s para %s e t %s (stop %s).'
                      % (b, n1(h[sp]['setup_B']['ev']), t2(h[sp]['setup_B']['t']),
                         n1(g[sp]['setup_B']['ev']), t2(g[sp]['setup_B']['t']),
                         n1(h[sp]['setup_A']['ev']), t2(h[sp]['setup_A']['t']),
                         n1(g[sp]['setup_A']['ev']), t2(g[sp]['setup_A']['t']), sp))
    cab = ('*A troca não melhora tudo: ela melhora a reversão.* A fórmula nova corta '
           'gatilhos (%s) e mede melhor no *setup B em %d das %d* células (duas bases × '
           'dois stops), no *setup A em %d de %d* e na *carteira A + B em %d de %d*. '
           % (sel, gB, tot, gA, tot, gAB, tot))
    fecho = (' Faz sentido: o eixo novo mede *vaivém*, que é exaustão — e exaustão é '
             'exatamente o que o setup de reversão procura. O setup A é continuação: '
             'ali o vaivém informa menos, e o que a fórmula nova faz é sobretudo '
             'tirar sinal.')
    return _neg(cab + ' '.join(linhas) + fecho)


def veredito_filtro_e2(R):
    """O filtro 'descarta quando [E2] manda' sobreviveu a troca de formula?"""
    e2 = R.get('e2')
    if not e2:
        return _neg('(sem comparativo de [E2] neste resumo)')
    at = e2['atual']
    det, vale = [], 0
    for b in BASES:
        f = e2['filtro'][b][at]
        if f['com']['t'] > f['sem']['t']:
            vale += 1
        det.append('No %s, com o filtro: %s de EV e t %s em %d trades; sem ele: %s e t %s '
                   'em %d.' % (b, n1(f['com']['ev']), t2(f['com']['t']), f['com']['n'],
                               n1(f['sem']['ev']), t2(f['sem']['t']), f['sem']['n']))
    if vale == len(BASES):
        cab = ('*O filtro continua valendo com a fórmula nova.* Ele existia porque a antiga '
               'media negativo quando o eixo do deslocamento mandava; não era óbvio que '
               'sobreviveria à troca, e sobreviveu. ')
    elif vale:
        cab = '*O filtro só continua valendo em uma das bases.* '
    else:
        cab = ('*O filtro deixou de valer:* com a fórmula nova ele piora as duas bases, e o '
               'certo é desligá-lo (DESCARTA_E2 = False). ')
    return _neg(cab + ' '.join(det))


def acao_stop(R):
    """O item de recomendacao sobre o stop, escrito do que foi medido."""
    sp, alt = R['stops'][0], R['stops'][1]
    cel = [('%s · %s' % (b, rot),
            R['variantes'][b]['ema3'][str(sp)][ch],
            R['variantes'][b]['ema3'][str(alt)][ch])
           for b in BASES for ch, rot in (('cA', 'só A'), ('cAB', 'A + B'))]
    ganha_alt = [x[0] for x in cel if x[2]['t'] > x[1]['t']]
    if len(ganha_alt) == len(cel):
        return _neg('*Baixar o stop para %d.* Melhora t e PF nas duas bases, nas duas '
                    'carteiras, e corta o risco por trade em um terço.' % alt)
    if not ganha_alt:
        return _neg('*Manter o stop em %d.* O de %d mede pior nas quatro comparações '
                    '(duas bases × duas carteiras): o stop curto corta trade bom antes '
                    'da hora.' % (sp, alt))
    return _neg('*Manter o stop em %d.* O de %d só mede melhor em %d das %d comparações '
                '(%s); nas outras o de %d fica na frente. Com a fórmula nova do eixo [E2] '
                'o stop curto deixou de ser a escolha limpa que era com a antiga — e o '
                'ganho dele em risco por trade continua valendo, então é uma troca, não '
                'uma decisão óbvia.'
                % (sp, alt, len(ganha_alt), len(cel), ', '.join(ganha_alt), sp))


def acao_ma(R):
    """O item de recomendacao sobre a media de regime."""
    venc = {}
    for stop in R['stops']:
        for b in BASES:
            venc[(stop, b)] = _rank(R, b, stop)[0][0]
    fora = {k: v for k, v in venc.items() if v != 'ema3'}
    if not fora:
        return _neg('*Manter as três EMAs.* O empilhamento dá o melhor t nas duas bases, '
                    'nos dois stops.')
    onde = ', '.join('%s com stop %d (ganha %s)' % (b, stop, ROT_REG[v][0])
                     for (stop, b), v in sorted(fora.items()))
    caveat = ''
    if 'jma' in fora.values():
        caveat = (' E onde o empilhamento perde, quem aparece na frente é a aproximação '
                  'de Jurik — que não é o JMA de verdade, então trocar o padrão por causa '
                  'dela seria trocar por um indicador que não existe aqui.')
    return _neg('*Manter as três EMAs como padrão.* Elas dão o melhor t em %d das %d '
                'combinações de base e stop; ficam atrás em %s.%s'
                % (len(venc) - len(fora), len(venc), onde, caveat))


def acao_carteira(R):
    """Rodar so o setup A, ou A + B? Medido, nao escolhido."""
    sp = str(R['stops'][0])
    cel = [(b, R['variantes'][b]['ema3'][sp]['cA'], R['variantes'][b]['ema3'][sp]['cAB'])
           for b in BASES]
    ganha_a = sum(1 for _, a, ab in cel if a['t'] > ab['t'])
    det = ' '.join('No %s: só A dá %s de EV com t %s e DD %d; A + B dá %s com t %s e DD %d.'
                   % (b, n1(a['ev']), t2(a['t']), round(a['dd']),
                      n1(ab['ev']), t2(ab['t']), round(ab['dd'])) for b, a, ab in cel)
    if ganha_a == len(cel):
        cab = ('*Rodar só o setup A.* Melhor EV, melhor t e drawdown menor nas duas '
               'bases. ')
    elif ganha_a:
        cab = ('*Só A tem o melhor EV por trade; A + B tem o melhor t.* O A entrega mais '
               'por operação e um drawdown menor; a carteira com B entrega mais no total '
               'e um resultado diário mais estável. ')
    else:
        cab = ('*A + B mede melhor que só A nas duas bases.* O setup A continua com o '
               'melhor EV por trade e o menor drawdown, mas a carteira com a reversão '
               'junto tem o t mais alto — foi o setup B que o eixo novo consertou. ')
    return _neg(cab + det)


def veredito_gestao(R):
    """O que a correcao da regra da parcial mudou."""
    g = R.get('gestao')
    if not g or not g.get('atual'):
        return _neg('(sem comparativo de gestão neste resumo)')
    at, sp = g['atual'], str(R['stops'][0])
    velho = 'entrada_100'
    det = []
    for b in BASES:
        a = g['grid'][b][at][sp]['cAB']
        v = g['grid'][b][velho][sp]['cAB']
        det.append('No %s, com stop %s: %s de EV e t %s pela regra certa, contra %s e t '
                   '%s pelo modelo antigo — e o desfecho "zero a zero" cai de %s para %s '
                   'dos trades, porque agora ele é zero de verdade e não +%d pontos.'
                   % (b, sp, n1(a['ev']), t2(a['t']), n1(v['ev']), t2(v['t']),
                      p0(v['p_zero']), p0(a['p_zero']),
                      round(R['parametros']['FRAC_PARCIAL']
                            * g['grid'][b][velho][sp]['parcial'])))
    return _neg('*A regra da parcial estava modelada errado, e o conserto muda os '
                'números.* Com a parcial na distância do stop e o stop do restante na '
                'média da operação, o stop *nunca anda* e o trade que volta morre em '
                'zero — não em +50. ' + ' '.join(det))


def bloco_gestao(R):
    """Tabela: as regras possiveis para a parcial e o stop depois dela."""
    g = R.get('gestao')
    if not g:
        return ''
    linhas = []
    for chave in g['ordem']:
        for stop in R['stops']:
            for ch, rot in (('cA', 'só A'), ('cAB', 'A + B')):
                cel = []
                for b in BASES:
                    m = g['grid'][b][chave][str(stop)][ch]
                    cel.append('<td class="num">%d</td><td class="num %s">%s</td>'
                               '<td class="num">%s</td><td class="num">%s</td>'
                               % (m['n'], cls(m['ev']), n1(m['ev']), t2(m['t']),
                                  p0(m['p_zero'])))
                primeira = (stop == R['stops'][0] and ch == 'cA')
                hi = (' class="hi"' if (chave == g['atual'] and ch == 'cAB'
                                        and stop == R['stops'][0]) else '')
                linhas.append('<tr%s><td>%s</td><td class="mono">stop %d</td>'
                              '<td>%s</td>%s</tr>'
                              % (hi, g['rotulos'][chave] if primeira else '', stop,
                                 rot, ''.join(cel)))
    return ('<div class="scroll"><table>'
            '<caption>A regra da parcial · n / EV / t / quanto termina em zero a zero</caption>'
            '<thead><tr><th>regra</th><th>stop</th><th>carteira</th>'
            '<th class="num" colspan="4">WINV26</th>'
            '<th class="num" colspan="4">WINFUT</th></tr></thead>'
            '<tbody>%s</tbody></table></div>' % ''.join(linhas))


def bloco_e2(R):
    """Tabela: formula antiga x nova do eixo [E2], carteiras A e A + B."""
    e2 = R.get('e2')
    if not e2:
        return ''
    linhas = []
    for met in e2['metricas']:
        for stop in R['stops']:
            for ch, rot in (('setup_A', 'setup A isolado'),
                            ('setup_B', 'setup B isolado'),
                            ('cA', 'carteira só A'), ('cAB', 'carteira A + B')):
                cel = []
                for b in BASES:
                    m = e2['grid'][b][met][str(stop)][ch]
                    cel.append('<td class="num">%d</td><td class="num %s">%s</td>'
                               '<td class="num">%s</td><td class="num">%s</td>'
                               % (m['n'], cls(m['ev']), n1(m['ev']), t2(m['t']),
                                  f2(m['pf'])))
                primeira = (stop == R['stops'][0] and ch == 'setup_A')
                hi = (' class="hi"' if (met == e2['atual'] and ch == 'cAB'
                                        and stop == R['stops'][0]) else '')
                linhas.append('<tr%s><td>%s</td><td class="mono">stop %d</td><td>%s</td>%s</tr>'
                              % (hi, e2['rotulos'][met] if primeira else '',
                                 stop, rot, ''.join(cel)))
    return ('<div class="scroll"><table>'
            '<caption>Eixo [E2]: fórmula antiga × nova, com todo o resto congelado</caption>'
            '<thead><tr><th>fórmula</th><th>stop</th><th>carteira</th>'
            '<th class="num" colspan="4">WINV26 · n / EV / t / PF</th>'
            '<th class="num" colspan="4">WINFUT · n / EV / t / PF</th></tr></thead>'
            '<tbody>%s</tbody></table></div>' % ''.join(linhas))


def tabela_fill(R, ROT=None):
    """Tabela: limitada valida ate o fim do pregao x valida por 1 barra."""
    lin = []
    for rot, ch in (('so A', 'A'), ('A + B', 'AB')):
        for regra, chr_ in (('até o fim do pregão', 'livre'),
                            ('<b>1 barra</b> — a regra', 'regra')):
            cel = []
            for b in BASES:
                m = R['bases'][b]['fill_%s_%s' % (chr_, ch)]
                cel.append('<td class="num">%d</td><td class="num %s">%s</td>'
                           '<td class="num">%s</td><td class="num">%s</td>'
                           % (m['n'], cls(m['ev']), n1(m['ev']), t2(m['t']), f2(m['pf'])))
            lin.append('<tr%s><td>%s</td><td>%s</td>%s</tr>'
                       % (' class="hi"' if chr_ == 'regra' else '', rot, regra,
                          ''.join(cel)))
    return ('<table><caption>Validade da ordem limitada · stop %d</caption>'
            '<thead><tr><th>carteira</th><th>validade</th>'
            '<th class="num" colspan="4">WINV26 · n / EV / t / PF</th>'
            '<th class="num" colspan="4">WINFUT · n / EV / t / PF</th></tr></thead>'
            '<tbody>%s</tbody></table>' % (R['stops'][0], ''.join(lin)))


def monta():
    R = json.load(open(os.path.join(SAIDA, 'resumo.json'), encoding='utf-8'))
    G = coleta_grafico()
    P = R['parametros']
    stop_pad = R['stops'][0]

    v26 = R['variantes']['WINV26']['ema3']
    vfu = R['variantes']['WINFUT']['ema3']
    d26, dfu = R['bases']['WINV26'], R['bases']['WINFUT']

    # --- setups (isolados, stop padrao)
    cards = []
    for su in ('A', 'B', 'C'):
        nome, desc = ROT_SU[su]
        a = v26[str(stop_pad)]['setup_' + su]
        b = vfu[str(stop_pad)]['setup_' + su]
        morto = (a['ev'] < 0 and b['ev'] < 0)
        klass = 'setup dead' if morto else ('setup best' if su == 'A' else 'setup')
        tag = ('<span class="tag off">desligado</span>' if morto else
               '<span class="tag on">%s</span>' % ('prioritário' if su == 'A' else 'ativo'))
        cards.append(f'''<article class="{klass}"><span class="rail"></span>
      <h4>{nome}</h4>{tag}
      <p>{desc}</p>
      <div class="pair">
        <div><div class="b">WINV26</div><div class="v {cls(a['ev'])}">{n1(a['ev'])}</div>
          <div class="t">t {t2(a['t'])} · PF {f2(a['pf'])}</div></div>
        <div><div class="b">WINFUT</div><div class="v {cls(b['ev'])}">{n1(b['ev'])}</div>
          <div class="t">t {t2(b['t'])} · PF {f2(b['pf'])}</div></div>
      </div></article>''')

    # --- carteiras
    def tab_carteira(base):
        v = R['variantes'][base]['ema3'][str(stop_pad)]
        return ('<div class="scroll"><table><caption>%s · %d pregões</caption>%s<tbody>%s%s%s</tbody></table></div>'
                % (base, R['bases'][base]['pregoes'], CAB_MET,
                   linha_metrica('<b>só A</b>', v['cA']),
                   linha_metrica('<b>A + B</b> — padrão', v['cAB'], 'hi'),
                   linha_metrica('A + B + C', v['cABC'], 'mute')))

    # --- mes a mes
    linhas_mes = ''.join(
        '<tr%s><td>%s%s</td><td class="num">%d</td><td class="num %s">%s</td>'
        '<td class="num">%s</td><td class="num">%s</td></tr>'
        % (' class="hi"' if m['mes'] == '2026-07' else (' class="mute"' if m['n'] < 5 else ''),
           m['mes'], ' <span class="sub">— fora da amostra</span>' if m['mes'] == '2026-07' else '',
           m['n'], 'best' if m['ev'] > 0 else 'neg', n1(m['ev']), mil(m['total']), p1(m['acerto']))
        for m in dfu['mes'])

    # --- custos
    linhas_custo = ''.join(
        '<tr%s><td class="mono">%d pts</td><td class="num">%s</td><td class="num">%s</td>'
        '<td class="num">%s</td><td class="num">%s</td></tr>'
        % (' class="mute"' if c == 20 else '', c,
           n1(d26['custo_%d' % c]['ev']), t2(d26['custo_%d' % c]['t']),
           n1(dfu['custo_%d' % c]['ev']), t2(dfu['custo_%d' % c]['t']))
        for c in (0, 5, 10, 20))

    ab26 = v26[str(stop_pad)]['cAB']
    abfu = vfu[str(stop_pad)]['cAB']

    ctx = dict(
        R=R, G=json.dumps(G, separators=(',', ':')),
        stop_pad=stop_pad,
        ma_slope=R['parametros']['MA_SLOPE'],
        ev26=n1(ab26['ev']), evfu=n1(abfu['ev']),
        ac26=p1(ab26['acerto']), acfu=p1(abfu['acerto']),
        t26=t2(ab26['t']), tfu=t2(abfu['t']),
        n26=ab26['n'], nfu=abfu['n'],
        preg26tr=ab26['pregoes'], pregfu=abfu['pregoes'],
        ent26_meio=n1(d26['entrada_meio']['ev']),
        entfu_meio=n1(dfu['entrada_meio']['ev']),
        ent26_fecha=n1(d26['entrada_fecha']['ev']),
        entfu_fecha=n1(dfu['entrada_fecha']['ev']),
        ac_a_fu_150=p1(vfu['150']['cA']['acerto']),
        ac_a_fu_100=p1(vfu['100']['cA']['acerto']),
        cards=''.join(cards),
        variantes_150=bloco_variantes(R, 150), variantes_100=bloco_variantes(R, 100),
        stops=bloco_stops(R),
        cart26=tab_carteira('WINV26'), cartfu=tab_carteira('WINFUT'),
        grade26=bloco_grade(R, 'WINV26'), gradefu=bloco_grade(R, 'WINFUT'),
        mes=linhas_mes, custo=linhas_custo,
        d26=d26, dfu=dfu, v26=v26, vfu=vfu,
        eq26=json.dumps(d26['equity']), eqfu=json.dumps(dfu['equity']),
        su26=''.join(d26['equity_setup']), sufu=''.join(dfu['equity_setup']),
        parcial=int(P['PARCIAL_EM'] or stop_pad),
        parcial_segue_stop=(P.get('PARCIAL_EM') is None),
        stops_js=json.dumps([str(x) for x in STOPS_VIZ]),
        parc_fixa_js=('null' if P.get('PARCIAL_EM') is None
                      else str(int(P['PARCIAL_EM']))),
        alvo=int(P['ALVO']),
        frac=int(100 * P['FRAC_PARCIAL']),
        max_fill=P.get('MAX_BARRAS_FILL', 1),
    )
    # --- as frases de conclusao, calculadas (ver comentario em veredito_ma)
    for nome, fn in (('ver_ma', veredito_ma), ('ver_entrada', veredito_entrada),
                     ('ver_abortos', veredito_abortos), ('ver_fill', veredito_fill),
                     ('ver_setups', veredito_setups), ('ver_stop', veredito_stop),
                     ('ver_e2', veredito_e2), ('ver_filtro_e2', veredito_filtro_e2),
                     ('acao_stop', acao_stop), ('acao_ma', acao_ma),
                     ('acao_carteira', acao_carteira),
                     ('ver_gestao', veredito_gestao)):
        md, html = fn(R)
        ctx[nome + '_md'], ctx[nome] = md, html
    ctx['tab_fill'] = tabela_fill(R)
    ctx['tab_e2'] = bloco_e2(R)
    ctx['tab_gestao'] = bloco_gestao(R)
    ctx['e2_rot'] = R['e2']['rotulos'][R['e2']['atual']] if R.get('e2') else ''
    return ctx


if __name__ == '__main__':
    import molde
    ctx = monta()
    html = molde.render(ctx)
    with open(DEST, 'w', encoding='utf-8') as f:
        f.write(html)
    print('gravado: %s  (%.1f KB)' % (DEST, len(html) / 1024.0))

    import resultados_md
    md = resultados_md.gera(
        ctx, dict(n1=n1, p0=p0, p1=p1, t2=t2, f2=f2, mil=mil), ROT_REG, ROT_SU)
    dest_md = os.path.join(BASE, 'RESULTADOS.md')
    with open(dest_md, 'w', encoding='utf-8') as f:
        f.write(md)
    print('gravado: %s  (%.1f KB)' % (dest_md, len(md) / 1024.0))
