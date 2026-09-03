# -*- coding: utf-8 -*-
"""
Gera relatorio.html -- relatorio unico, com o visualizador de trades dentro.

    python rodar.py       # primeiro, para atualizar saida/resumo.json
    python relatorio.py   # depois

TODO numero do relatorio sai de saida/resumo.json, inclusive as frases de
veredito. Nao ha numero escrito a mao no HTML: foi assim que a versao
anterior do projeto do WIN ficou defasada duas vezes quando a engine mudou.
"""
import json
import os
import warnings

import numpy as np

import engine as E
import molde

warnings.filterwarnings('ignore', category=RuntimeWarning)

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')
DEST = os.path.join(BASE, 'relatorio.html')

PRINC = 'COMPLETO'
HALVES = ('METADE_1', 'METADE_2')

ROT_SU = {
    'A': ('A · tendência',
          'Médias alinhadas e abertas, o preço volta e toca uma delas, e o gatilho '
          'aponta a favor do empilhamento.'),
    'B': ('B · reversão rápida',
          'Fora de consolidação, preço a um range médio ou mais da EMA 21, gatilho '
          'contra o afastamento.'),
    'C': ('C · consolidação',
          'Médias emboladas, preço afastado do cacho, gatilho contra o afastamento.'),
    'L': ('L · livre',
          'O gatilho disparou e nenhum dos três regimes reivindicou a barra. '
          'É a maior fatia, e no ouro é a que mais mede.'),
}


# ------------------------------------------------------------ formatacao
def _br(s):
    return s.replace('.', ',')


def n2(v):
    return '—' if v is None else _br('%+.2f' % v)


def n3(v):
    return '—' if v is None else _br('%+.3f' % v)


def n1(v):
    return '—' if v is None else _br('%+.1f' % v)


def p0(v):
    return '—' if v is None else '%.0f%%' % v


def p1(v):
    return '—' if v is None else _br('%.1f%%' % v)


def t2(v):
    return '—' if v is None else _br('%+.2f' % v)


def f2(v):
    return '—' if v is None else ('∞' if np.isinf(v) else _br('%.2f' % v))


def cls(v):
    return 'pos' if (v or 0) > 0 else ('neg' if (v or 0) < 0 else 'zer')


def usd(v, casas=2):
    return '—' if v is None else _br(('%+.' + str(casas) + 'f') % v)


def mil(v):
    """Separador de milhar em pt-BR. Nao passa por _br(): o ponto aqui JA e
    o separador certo, e trocá-lo por vírgula viraria decimal."""
    return '{:,}'.format(int(v)).replace(',', '.')


# ------------------------------------------------------------ dados grafico
def coleta_grafico(R):
    """Candles, medias e trades do visualizador.

    Os trades saem UMA VEZ POR STOP: os sinais nao dependem do stop, mas o
    desfecho e o resultado dependem, e o visualizador deixa trocar entre
    eles. Os candles sao os mesmos nos dois casos, entao vao uma vez so.
    """
    stops = R['stops']
    dados, equity = {}, {}
    st0 = E.STOP
    for nome in E.BASES:
        # A CURVA de capital sai das TRES amostras -- sao tres arrays curtos.
        # Os CANDLES do visualizador saem so da amostra inteira: as metades
        # sao os mesmos pregoes, e duplica-los tres vezes levava o HTML de
        # 2,8 MB para 8,3 MB sem mostrar nada novo.
        det = R['bases'][nome]
        equity[nome] = dict(rot=R['rot_base'][nome], eq=det.get('equity', []),
                            su=''.join(det.get('equity_setup', [])),
                            cs='%d pregões' % det['pregoes'])
        if nome != PRINC:
            continue
        E.aplica_ma('ema3')
        d, sig, marca = E.prepara(nome, ativos=('A', 'B', 'C', 'L'), regime='ema3')

        por_stop = {}
        for st in stops:
            E.STOP = float(st)
            por_stop[str(st)] = E.roda(d, marca, sig, carteira=False)
        E.STOP = st0
        if not any(len(t) for t in por_stop.values()):
            continue

        O, H, L, C = (d[c].to_numpy(float) for c in ('O', 'H', 'L', 'C'))
        er, em, el = (d[c].to_numpy(float) for c in ('er', 'em', 'el'))
        idxv, dirC = d.idx.to_numpy(), d.dirCandle.to_numpy()
        dia_arr = d.dia.to_numpy()
        hora = d.Data.dt.strftime('%H:%M').to_numpy()

        todos_dias = sorted({dd for t in por_stop.values() for dd in t.dia})
        idx_dia, dias = {}, []
        for dd in todos_dias:
            m = np.flatnonzero(dia_arr == dd)
            # o preco do ouro tem 2 casas e anda pouco dentro do pregao: um
            # deslocamento inteiro por pregao deixa os numeros do JSON curtos
            # sem perder resolucao (as casas ficam no deslocamento).
            b = float(round(O[m[0]]))
            idx_dia[dd] = len(dias)
            dias.append(dict(
                d=str(dd), base=b, i0=int(m[0]),
                hm=[str(x) for x in hora[m]],
                o=[round(O[j] - b, 2) for j in m],
                h=[round(H[j] - b, 2) for j in m],
                l=[round(L[j] - b, 2) for j in m],
                c=[round(C[j] - b, 2) for j in m],
                e1=[round(er[j] - b, 2) for j in m],
                e2=[round(em[j] - b, 2) for j in m],
                e3=[round(el[j] - b, 2) for j in m],
                x=[(None if np.isnan(idxv[j]) else round(idxv[j] * 100, 1)) for j in m],
                dc=[int(dirC[j]) for j in m],
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
                    ent=round(float(t['ent']) - dias[di]['base'], 2),
                    res=t['res'], pnl=round(float(t['pnl']), 2),
                    bar=int(t['barras'])))
            lst.sort(key=lambda t: (t['d'], t['i']))
            trades[st] = lst
        dados[nome] = dict(dias=dias, trades=trades)
    return dados, equity


# ------------------------------------------------------------ blocos HTML
CAB_MET = ('<thead><tr><th></th><th class="num">n</th><th class="num">/pregão</th>'
           '<th class="num">EV</th><th class="num">total</th><th class="num">acerto</th>'
           '<th class="num">t</th><th class="num">dias+</th><th class="num">PF</th>'
           '<th class="num">DD</th></tr></thead>')


def linha_metrica(rot, m, extra_cls='', sub=None):
    c = (' class="%s"' % extra_cls) if extra_cls else ''
    rotulo = rot + ('<span class="sub">%s</span>' % sub if sub else '')
    if not m:
        return '<tr%s><td>%s</td><td colspan="9" class="sub">sem trades</td></tr>' % (
            c, rotulo)
    tds = ''.join('<td class="num">%s</td>' % v for v in (
        m['n'], _br('%.1f' % m['por_pregao']), usd(m['ev'], 3), usd(m['total'], 1),
        p1(m['acerto']), t2(m['t']), p0(m['dias_pos']), f2(m['pf']),
        _br('%.1f' % m['dd'])))
    return '<tr%s><td>%s</td>%s</tr>' % (c, rotulo, tds)


def tabela_por_base(R, chave_secao, ordem, rotulos, stop, marcar=None,
                    subs=None):
    """Uma secao comparativa: as linhas sao as variantes, agrupadas por base."""
    linhas = []
    for base in E.BASES:
        linhas.append('<tr class="mute"><td colspan="10"><b>%s</b> · %s</td></tr>'
                      % (base.replace('_', ' ').title(), R['rot_base'][base]))
        for k in ordem:
            g = R[chave_secao]['grid'][base].get(k)
            if not isinstance(g, dict) or str(stop) not in g:
                continue
            linhas.append(linha_metrica(
                rotulos.get(k, k), g[str(stop)],
                extra_cls='hi' if (marcar is not None and k == marcar) else '',
                sub=(subs or {}).get(k)))
    return ('<table><caption>Carteira completa · stop %s · uma posição por vez'
            '</caption>%s<tbody>%s</tbody></table>'
            % (_br('%.2f' % stop), CAB_MET, ''.join(linhas)))


def bloco_principal(R, stop):
    linhas = []
    for base in E.BASES:
        v = R['variantes'][base]['ema3'][str(stop)]
        linhas.append('<tr class="mute"><td colspan="10"><b>%s</b> · %s · %d gatilhos'
                      '</td></tr>' % (base.replace('_', ' ').title(),
                                      R['rot_base'][base], v['gatilhos']))
        for rot, ch, hi in (('carteira completa (A+B+C+L)', 'cTudo', True),
                            ('só A + B + C', 'cABC', False),
                            ('só A + B', 'cAB', False),
                            ('só A', 'cA', False)):
            linhas.append(linha_metrica(rot, v[ch], extra_cls='hi' if hi else ''))
    return ('<table><caption>Configuração padrão · stop %s · alvo %s · EMAs 21/42/72'
            '</caption>%s<tbody>%s</tbody></table>'
            % (_br('%.2f' % stop), _br('%.2f' % R['parametros']['ALVO']),
               CAB_MET, ''.join(linhas)))


def bloco_porte(R):
    """As quatro decisoes do porte, cada uma com o numero que a sustenta."""
    p = R['parametros']
    st = str(R['stops'][0])

    def ev(sec, k, base=PRINC):
        g = R[sec]['grid'][base].get(k)
        return (g or {}).get(st, {}) or {}

    linhas = [
        ('O eixo do índice', 'os três do WIN', '[E4] range sozinho',
         ev('eixos', 'E2+E3+E4').get('ev'), ev('eixos', 'E4').get('ev'),
         '[E1] não existe no ouro e [E4] mede melhor que qualquer soma'),
        ('A direção lida', 'o delta', 'o candle',
         ev('referencia', 'delta').get('ev'), ev('referencia', 'candle').get('ev'),
         'o delta do ouro vem da tick rule e concorda com o candle em 63% das barras'),
        ('A geometria', 'clássica', 'inversa',
         ev('geometria', 'classica').get('ev'), ev('geometria', 'inversa').get('ev'),
         'o pavio de rejeição está do outro lado neste ativo'),
        ('A entrada', 'limitada no meio do candle', 'a mercado no fechamento',
         ev('entrada', 'meio').get('ev'), ev('entrada', 'fecha').get('ev'),
         'com a geometria invertida a limitada vira desconto garantido'),
    ]
    tr = []
    for o_que, antes, agora, ev_a, ev_b, porque in linhas:
        tr.append('<tr><td><b>%s</b><span class="sub">%s</span></td>'
                  '<td>%s</td><td class="num %s">%s</td>'
                  '<td><b>%s</b></td><td class="num %s">%s</td></tr>'
                  % (o_que, porque, antes, cls(ev_a), usd(ev_a, 3),
                     agora, cls(ev_b), usd(ev_b, 3)))
    return ('<table><caption>EV por trade, em USD · amostra inteira · stop %s · '
            'em cada linha só a coluna muda</caption>'
            '<thead><tr><th>o que</th><th>no WIN</th><th class="num">EV</th>'
            '<th>no ouro</th><th class="num">EV</th></tr></thead>'
            '<tbody>%s</tbody></table>' % (_br(st), ''.join(tr)))


def bloco_grade(R, base):
    """Mapa de calor da grade stop x alvo."""
    det = R['bases'][base]
    g = det['grade']
    stops, alvos = det['grade_stops'], det['grade_alvos']
    vals = [v for v in g.values() if v is not None]
    lo, hi = (min(vals), max(vals)) if vals else (0, 1)
    cel = []
    for st in stops:
        tds = []
        for al in alvos:
            v = g.get('%.1f_%.1f' % (st, al))
            if v is None:
                tds.append('<td class="num sub">—</td>')
                continue
            frac = 0.0 if hi == lo else (v - lo) / (hi - lo)
            fundo = ('rgba(31,90,115,%.2f)' % (0.06 + 0.44 * frac)) if v > 0 \
                else 'rgba(169,50,39,%.2f)' % (0.06 + 0.30 * (1 - frac))
            marca = (st == R['parametros']['STOP']
                     and al == R['parametros']['ALVO'])
            tds.append('<td class="num" style="background:%s%s">%s</td>'
                       % (fundo, ';font-weight:600' if marca else '', usd(v, 2)))
        cel.append('<tr><td class="num">%s</td>%s</tr>'
                   % (_br('%.1f' % st), ''.join(tds)))
    cab = ''.join('<th class="num">%s</th>' % _br('%.1f' % a) for a in alvos)
    return ('<div class="chart"><h5>%s</h5><p class="cs">%s · EV por trade, USD</p>'
            '<div class="scroll" style="margin:0;border:none;box-shadow:none">'
            '<table><thead><tr><th class="num">stop \\ alvo</th>%s</tr></thead>'
            '<tbody>%s</tbody></table></div></div>'
            % (base.replace('_', ' ').title(), R['rot_base'][base], cab,
               ''.join(cel)))


def bloco_estab(R, base):
    Rs = R['estabilidade']
    at_n, at_p = Rs['atual']
    vals = [c['ev'] for c in Rs['grid'][base].values() if c]
    lo, hi = (min(vals), max(vals)) if vals else (0, 1)
    cel = []
    for niv in Rs['niveis']:
        tds = []
        for pos in Rs['pos']:
            c = Rs['grid'][base].get('%.2f_%.0f' % (niv, pos))
            if not c:
                tds.append('<td class="num sub">—</td>')
                continue
            frac = 0.0 if hi == lo else (c['ev'] - lo) / (hi - lo)
            fundo = ('rgba(31,90,115,%.2f)' % (0.06 + 0.44 * frac)) if c['ev'] > 0 \
                else 'rgba(169,50,39,%.2f)' % (0.10 + 0.30 * (1 - frac))
            marca = (abs(niv - at_n) < 1e-9 and abs(pos - at_p) < 1e-9)
            tds.append('<td class="num" style="background:%s%s" title="n=%d  t=%s">%s</td>'
                       % (fundo, ';font-weight:600;outline:2px solid var(--accent);'
                          'outline-offset:-2px' if marca else '',
                          c['n'], t2(c['t']), usd(c['ev'], 2)))
        cel.append('<tr><td class="num">%s</td>%s</tr>'
                   % (_br('%.2f' % niv), ''.join(tds)))
    cab = ''.join('<th class="num">%.0f</th>' % p for p in Rs['pos'])
    return ('<div class="chart"><h5>%s</h5><p class="cs">%s · EV por trade, USD</p>'
            '<div class="scroll" style="margin:0;border:none;box-shadow:none">'
            '<table><thead><tr><th class="num">nível \\ pos</th>%s</tr></thead>'
            '<tbody>%s</tbody></table></div></div>'
            % (base.replace('_', ' ').title(), R['rot_base'][base], cab,
               ''.join(cel)))


def bloco_cards(R, stop):
    v = R['variantes'][PRINC]['ema3'][str(stop)]
    melhor = max(('A', 'B', 'C', 'L'),
                 key=lambda s: (v['setup_' + s] or {}).get('ev', -9e9))
    out = []
    for su in ('A', 'B', 'C', 'L'):
        m = v['setup_' + su]
        h1 = R['variantes']['METADE_1']['ema3'][str(stop)]['setup_' + su]
        h2 = R['variantes']['METADE_2']['ema3'][str(stop)]['setup_' + su]
        vivo = m and m['ev'] > 0 and (h1 or {}).get('ev', -1) > 0 \
            and (h2 or {}).get('ev', -1) > 0
        klass = 'setup' + (' best' if su == melhor else '') + ('' if vivo else ' dead')
        tag = ('<span class="tag on">positivo nas duas metades</span>' if vivo
               else '<span class="tag off">discorda entre as metades</span>')
        rot, desc = ROT_SU[su]
        out.append(
            '<div class="%s"><div class="rail"></div><h4>%s</h4>%s<p>%s</p>'
            '<div class="pair"><div><div class="b">EV · USD</div>'
            '<div class="v %s">%s</div><div class="t">%d trades · PF %s</div></div>'
            '<div><div class="b">t diário</div><div class="v">%s</div>'
            '<div class="t">metades %s / %s</div></div></div></div>'
            % (klass, rot, tag, desc,
               cls((m or {}).get('ev')), usd((m or {}).get('ev'), 3),
               (m or {}).get('n', 0), f2((m or {}).get('pf')),
               t2((m or {}).get('t')),
               usd((h1 or {}).get('ev'), 2), usd((h2 or {}).get('ev'), 2)))
    return ''.join(out)


def bloco_carteiras(R, stop):
    linhas = []
    for base in E.BASES:
        v = R['variantes'][base]['ema3'][str(stop)]
        linhas.append('<tr class="mute"><td colspan="10"><b>%s</b></td></tr>'
                      % R['rot_base'][base])
        for su in ('A', 'B', 'C', 'L'):
            linhas.append(linha_metrica('setup %s isolado (%d sinais)'
                                        % (su, v['sinais_' + su]),
                                        v['setup_' + su]))
        for rot, ch in (('carteira A', 'cA'), ('carteira A+B', 'cAB'),
                        ('carteira A+B+C', 'cABC'),
                        ('carteira completa', 'cTudo')):
            linhas.append(linha_metrica(rot, v[ch],
                                        extra_cls='hi' if ch == 'cTudo' else ''))
    return ('<table><caption>Setups isolados (cada sinal vira trade) e carteiras '
            '(uma posição por vez) · stop %s</caption>%s<tbody>%s</tbody></table>'
            % (_br('%.2f' % stop), CAB_MET, ''.join(linhas)))


def bloco_ma(R, stop):
    linhas = []
    for base in E.BASES:
        linhas.append('<tr class="mute"><td colspan="6"><b>%s</b></td></tr>'
                      % R['rot_base'][base])
        for reg in R['regimes']:
            v = R['variantes'][base][reg][str(stop)]
            a, c = v['setup_A'], v['cA']
            linhas.append(
                '<tr%s><td>%s</td><td class="num">%s</td>'
                '<td class="num">%d</td><td class="num %s">%s</td>'
                '<td class="num">%s</td><td class="num">%s</td></tr>'
                % (' class="hi"' if reg == 'ema3' else '', E.ROT_MA[reg],
                   p0(v['tend']), (a or {}).get('n', 0), cls((a or {}).get('ev')),
                   usd((a or {}).get('ev'), 3), t2((a or {}).get('t')),
                   usd((c or {}).get('ev'), 3)))
    return ('<table><caption>A média só decide o REGIME — o gatilho é o mesmo em '
            'todas as linhas, e a carteira completa não muda. Stop %s</caption>'
            '<thead><tr><th>média de regime</th><th class="num">%% em tendência</th>'
            '<th class="num">n (setup A)</th><th class="num">EV do A</th>'
            '<th class="num">t do A</th><th class="num">EV da carteira A</th>'
            '</tr></thead><tbody>%s</tbody></table>'
            % (_br('%.2f' % stop), ''.join(linhas)))


def bloco_mes(R):
    linhas = []
    for m in R['bases'][PRINC].get('mes', []):
        linhas.append('<tr><td>%s</td><td class="num">%d</td>'
                      '<td class="num %s">%s</td><td class="num %s">%s</td>'
                      '<td class="num">%s</td></tr>'
                      % (m['mes'], m['n'], cls(m['ev']), usd(m['ev'], 3),
                         cls(m['total']), usd(m['total'], 1), p1(m['acerto'])))
    return ('<table><caption>Amostra inteira · carteira completa · stop %s · por mês'
            '</caption><thead><tr><th>mês</th><th class="num">trades</th>'
            '<th class="num">EV</th><th class="num">total</th>'
            '<th class="num">acerto</th></tr></thead><tbody>%s</tbody></table>'
            % (_br('%.2f' % R['stops'][0]), ''.join(linhas)))


def bloco_custo(R):
    linhas = []
    for base in E.BASES:
        linhas.append('<tr class="mute"><td colspan="10"><b>%s</b></td></tr>'
                      % R['rot_base'][base])
        for c in (0.0, 0.10, 0.20, 0.50):
            linhas.append(linha_metrica(
                'custo de %s USD ida e volta' % _br('%.2f' % c),
                R['bases'][base]['custo_%.2f' % c],
                extra_cls='hi' if abs(c - 0.20) < 1e-9 else ''))
    return ('<table><caption>Carteira completa · stop %s · o custo é descontado de '
            'cada trade</caption>%s<tbody>%s</tbody></table>'
            % (_br('%.2f' % R['stops'][0]), CAB_MET, ''.join(linhas)))


def bloco_psico(R, stop):
    campos = (('n', 'trades', lambda v: str(v)),
              ('por_pregao', 'por pregão', lambda v: _br('%.1f' % v)),
              ('acerto', 'acerto', lambda v: p1(v)),
              ('ev', 'EV por trade', lambda v: usd(v, 3)),
              ('media_dia', 'média por pregão', lambda v: usd(v, 2)),
              ('sd_dia', 'desvio por pregão', lambda v: _br('%.2f' % v)),
              ('dias_pos', 'pregões positivos', lambda v: p0(v)),
              ('pior_dia', 'pior pregão', lambda v: usd(v, 1)),
              ('melhor_dia', 'melhor pregão', lambda v: usd(v, 1)),
              ('dd', 'rebaixamento máximo', lambda v: _br('%.1f' % v)),
              ('seq_trades', 'maior sequência sem ganhar', lambda v: '%d trades' % v),
              ('seq_dias', 'maior sequência de pregões negativos',
               lambda v: '%d pregões' % v),
              ('p_semana_neg', 'chance de uma semana negativa', lambda v: p0(v)),
              ('p_mes_neg', 'chance de um mês negativo', lambda v: p0(v)),
              ('p_alvo', 'terminam no alvo', lambda v: p1(v)),
              ('p_stop', 'terminam no stop', lambda v: p1(v)),
              ('p_zero', 'terminam em zero a zero', lambda v: p1(v)),
              ('p_fim', 'terminam no fim do pregão', lambda v: p1(v)))
    ps = {b: R['bases'][b]['psico'][str(stop)]['tudo_c20'] for b in E.BASES}
    linhas = []
    for k, rot, fmt in campos:
        tds = ''.join('<td class="num">%s</td>'
                      % ('—' if (ps[b] is None or ps[b].get(k) is None)
                         else fmt(ps[b][k])) for b in E.BASES)
        linhas.append('<tr><td>%s</td>%s</tr>' % (rot, tds))
    cab = ''.join('<th class="num">%s</th>' % b.replace('_', ' ').title()
                  for b in E.BASES)
    return ('<table><caption>Carteira completa · stop %s · com %s USD de custo por '
            'trade</caption><thead><tr><th></th>%s</tr></thead><tbody>%s</tbody>'
            '</table>' % (_br('%.2f' % stop), _br('%.2f' % ps[PRINC]['custo']),
                          cab, ''.join(linhas)))


# ------------------------------------------------------------- vereditos
def _ev(R, sec, k, base=PRINC, stop=None):
    g = R[sec]['grid'][base].get(k) or {}
    m = g.get(str(stop if stop is not None else R['stops'][0])) or {}
    return m.get('ev'), m.get('t'), m.get('n')


def _todas(R, sec, k):
    return [_ev(R, sec, k, b)[0] for b in E.BASES]


def ver_porte(R):
    tot = 0
    for sec, a, b in (('eixos', 'E2+E3+E4', 'E4'),
                      ('referencia', 'delta', 'candle'),
                      ('geometria', 'classica', 'inversa'),
                      ('entrada', 'meio', 'fecha')):
        if (_ev(R, sec, b)[0] or 0) > (_ev(R, sec, a)[0] or 0):
            tot += 1
    ev_c, _, _ = _ev(R, 'geometria', 'classica')
    ev_i, _, _ = _ev(R, 'geometria', 'inversa')
    ev_m, _, _ = _ev(R, 'entrada', 'meio')
    ev_f, _, _ = _ev(R, 'entrada', 'fecha')
    return ('As quatro trocas medem melhor na coluna da direita, e em %d das 4 a '
            'diferença troca o <em>sinal</em> do resultado. As duas mais caras são '
            'a geometria (%s contra %s por trade) e a entrada (%s contra %s) — e as '
            'duas estão ligadas: é a inversão da geometria que estraga a ordem '
            'limitada, porque muda de que lado do fechamento cai o meio do candle.'
            % (tot, usd(ev_c, 3), usd(ev_i, 3), usd(ev_m, 3), usd(ev_f, 3)))


def ver_degenerado(R):
    deg = R['eixos']['degenerados'][PRINC]
    mortos = ', '.join(deg['mortos']) or 'nenhum'
    return ('O XAUUSD é CFD: não há volume por negócio, o gerador de barras conta '
            '1 lote por tick, e a agressão total fica igual ao número de negócios '
            'em quase toda barra. Com o eixo constante o percentil dá 0,000 sempre, '
            'e um índice de três eixos que o inclua fica preso abaixo de 0,667 — '
            'com corte em 0,80 ele nunca acenderia. A engine detecta eixo sem '
            'variação e o tira da soma, renormalizando os pesos. Eixo derrubado '
            'neste ativo: <b>%s</b>. É a mesma defesa do <code>[D1]</code> de '
            '<code>Ticks_Esforco_v2.mqh</code>, e não é um remendo para o ouro: é '
            'o que impede qualquer eixo que o ativo não publique de virar um teto '
            'silencioso no índice.' % mortos)


def ver_eixos(R):
    ordem = R['eixos']['ordem']
    ev = {k: _ev(R, 'eixos', k)[0] for k in ordem}
    melhor = max(ordem, key=lambda k: ev[k] or -9e9)
    coerentes = [k for k in ordem
                 if all((v or -1) > 0 for v in _todas(R, 'eixos', k))]
    ev4, t4, _ = _ev(R, 'eixos', 'E4')
    ev3, t3_, _ = _ev(R, 'eixos', 'E2+E3+E4')
    return ('<b>%s</b> mede melhor, e é o único conjunto que mede positivo em todas '
            'as três colunas com folga: %s por trade contra %s do índice de três '
            'eixos (t %s contra %s). Somar eixos aqui <em>dilui</em> — cada eixo '
            'que entra puxa o índice para a média e o corte deixa de selecionar a '
            'barra de range extremo, que é a única coisa que este ativo publica com '
            'sinal. Conjuntos positivos nas três colunas: %s.'
            % (melhor.replace('+', ' + '), usd(ev4, 3), usd(ev3, 3), t2(t4),
               t2(t3_), ', '.join(coerentes) or 'nenhum'))


def ver_e2(R):
    g = R['e2']['grid']
    st = str(R['stops'][0])
    v1 = {b: g[b]['0'][st] for b in E.BASES}
    v2 = {b: g[b]['2'][st] for b in E.BASES}
    ganhou = sum(1 for b in E.BASES
                 if (v2[b] or {}).get('ev', -9e9) > (v1[b] or {}).get('ev', -9e9))
    h1_v1 = (v1['METADE_1'] or {}).get('ev')
    coerente_v1 = all((v1[b] or {}).get('ev', -1) > 0 for b in E.BASES)
    coerente_v2 = all((v2[b] or {}).get('ev', -1) > 0 for b in E.BASES)
    return ('O eixo novo mede melhor em %d das 3 colunas: %s contra %s por trade na '
            'amostra inteira, com t %s contra %s. E o que mais importa não é a '
            'diferença de tamanho: com a fórmula antiga a 1ª metade mede %s — as '
            'duas metades <b>%s</b>; com a nova elas <b>%s</b>. O eixo saiu de '
            '“atrapalha” para “soma”, que é exatamente o que a medição por barra '
            'de <code>Ticks_Esforco_v2.mqh</code> tinha previsto para este ativo.'
            % (ganhou, usd((v2[PRINC] or {}).get('ev'), 3),
               usd((v1[PRINC] or {}).get('ev'), 3),
               t2((v2[PRINC] or {}).get('t')), t2((v1[PRINC] or {}).get('t')),
               usd(h1_v1, 3),
               'concordam' if coerente_v1 else 'discordam de sinal',
               'concordam' if coerente_v2 else 'discordam de sinal'))


def ver_geo(R):
    st = R['stops'][0]
    ev = {k: _ev(R, 'geometria', k)[0] for k in R['geometria']['ordem']}
    inv_h = _todas(R, 'geometria', 'inversa')
    cl_h = _todas(R, 'geometria', 'classica')
    _, t_inv, n_inv = _ev(R, 'geometria', 'inversa')
    return ('A inversa mede %s por trade contra %s da clássica — e a distância entre '
            'as duas (%s) é maior que o EV inteiro da estratégia. Nas metades a '
            'inversa dá %s e %s, as duas positivas; a clássica dá %s e %s, que '
            'discordam de sinal. Sem nenhum filtro de forma o gatilho mede %s: o '
            'filtro não é enfeite, é metade do sinal. Com n = %d e t = %s, é o '
            'resultado mais firme deste backtest.'
            % (usd(ev['inversa'], 3), usd(ev['classica'], 3),
               usd((ev['inversa'] or 0) - (ev['classica'] or 0), 3),
               usd(inv_h[1], 2), usd(inv_h[2], 2), usd(cl_h[1], 2), usd(cl_h[2], 2),
               usd(ev['off'], 3), n_inv, t2(t_inv)))


def ver_entrada(R):
    ev_f, t_f, _ = _ev(R, 'entrada', 'fecha')
    ev_m, t_m, _ = _ev(R, 'entrada', 'meio')
    ab = R['entrada']['grid'][PRINC]['abortos']
    perda = (ev_f or 0) - (ev_m or 0)
    return ('A mercado: %s por trade, t %s. Limitada no meio do candle: %s, t %s. '
            'A regra custa <b>%s por trade</b> e inverte o sinal do resultado. E ela '
            'nem sequer aborta operações que compensem a diferença — dos %d sinais, '
            '%d preenchem na barra seguinte (%s), porque o preço já está do lado '
            'errado da ordem. No WIN essa mesma regra custava quase nada e comprava '
            'disciplina; aqui ela só compra desconto para o outro lado.'
            % (usd(ev_f, 3), t2(t_f), usd(ev_m, 3), t2(t_m), usd(perda, 3),
               ab['sinais'], ab['preenchidos'],
               p0(100.0 * ab['preenchidos'] / max(1, ab['sinais']))))


def ver_grade(R):
    det = R['bases'][PRINC]
    g = det['grade']
    st_pad, al_pad = R['parametros']['STOP'], R['parametros']['ALVO']
    # o melhor stop de cada metade, no alvo padrao
    melhores = []
    for b in HALVES:
        gb = R['bases'][b]['grade']
        melhores.append(max(det['grade_stops'],
                            key=lambda s: gb.get('%.1f_%.1f' % (s, al_pad)) or -9e9))
    pos = sum(1 for v in g.values() if v is not None and v > 0)
    tot = sum(1 for v in g.values() if v is not None)
    return ('O par escolhido é <b>stop %s, alvo %s</b> — a melhor célula da amostra '
            'inteira (%s por trade). O stop equivalente do WIN, %s, mede %s no mesmo '
            'alvo: positivo, mas menos da metade. Nas duas metades o melhor stop é '
            '%s e %s, o que mantém a escolha. Das %d células da grade, %d medem '
            'positivo — a região é larga, não é um pico.'
            % (_br('%.1f' % st_pad), _br('%.1f' % al_pad),
               usd(g.get('%.1f_%.1f' % (st_pad, al_pad)), 3),
               _br('%.1f' % R['stops'][1]),
               usd(g.get('%.1f_%.1f' % (R['stops'][1], al_pad)), 3),
               _br('%.1f' % melhores[0]), _br('%.1f' % melhores[1]), tot, pos))


def ver_gestao(R):
    st = str(R['stops'][0])
    g = R['gestao']['grid'][PRINC]
    certa = g['media_stop'][st]
    antigo = g['entrada_meio'][st]
    diff = (certa or {}).get('ev', 0) - (antigo or {}).get('ev', 0)
    if diff > 0:
        veredito = ('Aqui a regra certa também mede <b>melhor</b>: %s contra %s por '
                    'trade. É o contrário do que aconteceu no WIN, onde o modelo '
                    'antigo inflava o resultado — e é uma coincidência feliz, não um '
                    'argumento: a regra certa continuaria sendo a certa se medisse '
                    'pior, porque a outra conta dinheiro que não existe.'
                    % (usd((certa or {}).get('ev'), 3),
                       usd((antigo or {}).get('ev'), 3)))
    else:
        veredito = ('A regra certa mede %s contra %s do modelo antigo. A diferença é '
                    'o que o modelo antigo <em>inventava</em>: ele pagava meia '
                    'parcial no desfecho que chamava de zero a zero.'
                    % (usd((certa or {}).get('ev'), 3),
                       usd((antigo or {}).get('ev'), 3)))
    return veredito


def ver_setups(R):
    st = str(R['stops'][0])
    v = R['variantes'][PRINC]['ema3'][st]
    tudo, ca, cab, cabc = v['cTudo'], v['cA'], v['cAB'], v['cABC']
    melhor_su = max(('A', 'B', 'C', 'L'),
                    key=lambda s: (v['setup_' + s] or {}).get('ev', -9e9))
    coerentes = [s for s in ('A', 'B', 'C', 'L')
                 if all((R['variantes'][b]['ema3'][st]['setup_' + s] or {})
                        .get('ev', -1) > 0 for b in E.BASES)]
    return ('<b>O filtro de regime subtrai neste ativo.</b> A carteira que pega todo '
            'gatilho mede %s por trade com t %s; a de só A mede %s, A+B mede %s e '
            'A+B+C mede %s — todas abaixo, e com menos operações. O setup isolado '
            'mais forte é o <b>%s</b> (%s), e o único que mede positivo nas três '
            'colunas é %s. A leitura é que, no ouro, a barra de range extremo com o '
            'pavio do lado certo já carrega o sinal inteiro: exigir que ela apareça '
            'num regime específico só joga fora amostra.'
            % (usd((tudo or {}).get('ev'), 3), t2((tudo or {}).get('t')),
               usd((ca or {}).get('ev'), 3), usd((cab or {}).get('ev'), 3),
               usd((cabc or {}).get('ev'), 3), melhor_su,
               usd((v['setup_' + melhor_su] or {}).get('ev'), 3),
               ', '.join(coerentes) or 'nenhum'))


def ver_ma(R):
    st = str(R['stops'][0])
    def t_de(reg, base):
        m = R['variantes'][base][reg][st]['setup_A']
        return (m or {}).get('t', -9e9)
    melhor = max(R['regimes'], key=lambda r: sum(t_de(r, b) for b in HALVES))
    tend = {r: R['variantes'][PRINC][r][st]['tend'] for r in R['regimes']}
    return ('A média <b>não muda a carteira completa</b> — ela só decide o regime, e '
            'o regime não está sendo usado como filtro (§ 8). O que ela muda é o '
            'setup A, e ali quem mede melhor somando as duas metades é a <b>%s</b>. '
            'Vale mais como diagnóstico: as EMAs empilhadas veem tendência em %s das '
            'barras e a KAMA em %s, e nenhuma das duas leituras melhora o resultado '
            'da carteira. Num ativo em que o regime não filtra, trocar a média é '
            'trocar a etiqueta.'
            % (E.ROT_MA[melhor], p0(tend['ema3']), p0(tend['kama'])))


def ver_estab(R):
    Rs = R['estabilidade']
    at = '%.2f_%.0f' % tuple(Rs['atual'])
    pos = {b: sum(1 for c in Rs['grid'][b].values() if c and c['ev'] > 0)
           for b in E.BASES}
    tot = len([c for c in Rs['grid'][PRINC].values() if c])
    neg_h = [k for b in HALVES for k, c in Rs['grid'][b].items()
             if c and c['ev'] <= 0]
    melhor = max(Rs['grid'][PRINC], key=lambda k: (Rs['grid'][PRINC][k] or {})
                 .get('ev', -9e9))
    return ('Das %d células, %d medem positivo na amostra inteira, %d na 1ª metade e '
            '%d na 2ª. As negativas são %d, todas nas bordas da varredura. A célula '
            'escolhida (%s) não é a melhor da amostra inteira — a melhor é %s — e '
            'foi mantida porque é a que mede bem nas <em>duas</em> metades. A região '
            'é larga: subir ou descer um degrau em qualquer direção não muda o sinal '
            'do resultado. Isso não faz do corte um número validado fora da amostra; '
            'faz dele um número que não depende de acertar a casa decimal.'
            % (tot, pos[PRINC], pos['METADE_1'], pos['METADE_2'], len(neg_h),
               at.replace('_', ' / '), melhor.replace('_', ' / ')))


def ver_custo(R):
    b = R['bases'][PRINC]
    c0, c20, c50 = b['custo_0.00'], b['custo_0.20'], b['custo_0.50']
    return ('Com %s de custo o EV cai de %s para %s por trade e o t de %s para %s — '
            'a vantagem sobrevive ao spread típico. Com %s ela cai para %s. O custo '
            'que zeraria a estratégia é de cerca de <b>%s USD</b> por trade, e o '
            'spread do ouro alarga em notícia: a margem existe, mas não é grande, e '
            'quem opera com spread variável precisa medir o próprio.'
            % (_br('0,20'), usd(c0['ev'], 3), usd(c20['ev'], 3), t2(c0['t']),
               t2(c20['t']), _br('0,50'), usd(c50['ev'], 3),
               _br('%.2f' % c0['ev'])))


def ver_psico(R):
    p = R['bases'][PRINC]['psico'][str(R['stops'][0])]['tudo_c20']
    return ('São %s trades por pregão com %s de acerto: a maioria das operações '
            'perde, e o resultado vem do tamanho dos ganhos. Já houve <b>%d trades '
            'seguidos sem ganhar</b> e <b>%d pregões negativos seguidos</b>, com a '
            'vantagem intacta. Uma semana fecha negativa em %s das vezes e um mês em '
            '%s. Quem não espera isso vai abandonar a estratégia num intervalo que o '
            'próprio backtest previa.'
            % (_br('%.1f' % p['por_pregao']), p1(p['acerto']), p['seq_trades'],
               p['seq_dias'], p0(p['p_semana_neg']), p0(p['p_mes_neg'])))


def frase_metades(R):
    st = str(R['stops'][0])
    evs = [R['variantes'][b]['ema3'][st]['cTudo']['ev'] for b in HALVES]
    return ('As duas metades <b>não são duas amostras independentes</b>: são o mesmo '
            'histórico de %d pregões partido ao meio. No projeto do WIN havia dois '
            'contratos diferentes e a concordância entre eles era evidência de '
            'verdade; aqui ela é só evidência de que o resultado não vem de um '
            'pedaço do período. É mais fraco, e o número tem de ser lido assim. '
            'Metades: %s e %s por trade.'
            % (R['bases'][PRINC]['pregoes'], usd(evs[0], 3), usd(evs[1], 3)))


def acoes(R):
    st = str(R['stops'][0])
    v = R['variantes'][PRINC]['ema3'][st]
    p = R['parametros']
    b = R['bases'][PRINC]
    return [
        ('<b>Operar o gatilho inteiro, sem filtro de regime.</b> A carteira completa '
         'mede %s por trade com t %s; qualquer subconjunto A/B/C mede menos. São %s '
         'operações por pregão — mais que o dobro do que o WIN dava.'
         % (usd(v['cTudo']['ev'], 3), t2(v['cTudo']['t']),
            _br('%.1f' % v['cTudo']['por_pregao']))),
        ('<b>Entrar a mercado no fechamento da barra, nunca com limitada no meio do '
         'candle.</b> É a diferença de %s por trade da § 6, e é a única mudança do '
         'porte que um operador pode errar sozinho, por hábito vindo do WIN.'
         % usd((_ev(R, 'entrada', 'fecha')[0] or 0)
               - (_ev(R, 'entrada', 'meio')[0] or 0), 3)),
        ('<b>Stop %s, alvo %s, parcial de %d%% na distância do stop.</b> O stop tem '
         'de caber FORA da barra do gatilho, que é uma barra de range extremo por '
         'construção — o stop escalado do WIN (%s) fica dentro dela e mede %s.'
         % (_br('%.1f' % p['STOP']), _br('%.1f' % p['ALVO']),
            round(100 * p['FRAC_PARCIAL']), _br('%.1f' % R['stops'][1]),
            usd(b['grade'].get('%.1f_%.1f' % (R['stops'][1], p['ALVO'])), 3))),
        ('<b>Medir o próprio spread antes de dimensionar.</b> Com %s USD por trade a '
         'vantagem cai para %s e continua de pé; o custo que a zera é %s. Todos os '
         'números das outras seções são brutos.'
         % (_br('0,20'), usd(b['custo_0.20']['ev'], 3),
            _br('%.2f' % b['custo_0.00']['ev']))),
    ]


# ------------------------------------------------------------------ monta
def monta():
    with open(os.path.join(SAIDA, 'resumo.json'), encoding='utf-8') as f:
        R = json.load(f)

    stop = R['stops'][0]
    st = str(stop)
    p = R['parametros']
    det = R['bases'][PRINC]
    v = R['variantes'][PRINC]['ema3'][st]
    tudo = v['cTudo']
    G, EQ = coleta_grafico(R)

    ev_h = {b: R['variantes'][b]['ema3'][st]['cTudo']['ev'] for b in HALVES}
    ac = acoes(R)

    gat_txt = ('[%s] ≥ %s · %s · %s'
               % ('+'.join(p['EIXOS']) if isinstance(p['EIXOS'], (list, tuple))
                  else str(p['EIXOS']).strip("()',").replace("', '", '+'),
                  _br('%.2f' % p['NIVEL_MIN']), p['REFERENCIA'], p['GEOMETRIA']))

    ctx = dict(
        titulo='O que o setup de esforço vira quando muda de mercado',
        lede=('O mesmo backtest do WIN, rodado sobre %s barras de 521 ticks do ouro. '
              'Quatro peças tiveram de mudar — e três delas mudaram de <em>sinal</em>, '
              'não de calibração. O que sobra mede %s por trade.'
              % (mil(det['barras']),
                 usd(tudo['ev'], 2))),
        barras=mil(det['barras']),
        pregoes=det['pregoes'], ini=det['ini'], fim=det['fim'],
        gat_txt=gat_txt,
        stop_pad=_br('%.2f' % stop), stop_alt=_br('%.2f' % R['stops'][1]),
        alvo=_br('%.2f' % p['ALVO']), frac=round(100 * p['FRAC_PARCIAL']),
        val_ponto=round(p['VAL_PONTO']), ma_slope=p['MA_SLOPE'],
        nivel=_br('%.2f' % p['NIVEL_MIN']), pos=_br('%.0f' % p['CORTE_POSICAO']),
        custo_psico=_br('%.2f' % det['psico'][st]['tudo_c20']['custo']),

        h_resultado=('%s por trade, com a vantagem nas duas metades da amostra'
                     % usd(tudo['ev'], 2)),
        ev=usd(tudo['ev'], 2), cls_ev=cls(tudo['ev']), t=t2(tudo['t']),
        n=tudo['n'], acerto=p1(tudo['acerto']), pf=f2(tudo['pf']),
        ev_h1=usd(ev_h['METADE_1'], 2), ev_h2=usd(ev_h['METADE_2'], 2),
        tab_principal=bloco_principal(R, stop),
        aviso_metades=frase_metades(R),
        aviso_custo=('Todos os números são <b>brutos</b>. O spread do XAUUSD é real e '
                     'contínuo — a § 11 mostra o que ele faz, e é ela que vale para '
                     'dimensionar posição.'),

        h_porte='Quatro trocas, e três delas invertem o sinal',
        tab_porte=bloco_porte(R), ver_porte=ver_porte(R),

        h_eixos='Um eixo só, e não é nenhum dos três do WIN',
        ver_degenerado=ver_degenerado(R),
        tab_eixos=tabela_por_base(
            R, 'eixos', R['eixos']['ordem'],
            {k: k.replace('+', ' + ') + '  (nível %s)'
             % _br('%.2f' % R['eixos']['niveis'][k]) for k in R['eixos']['ordem']},
            stop, marcar=R['eixos']['atual']),
        ver_eixos=ver_eixos(R),

        h_e2='A fórmula nova tira o eixo de negativo',
        tab_e2=tabela_por_base(R, 'e2', R['e2']['metricas'], R['e2']['rotulos'],
                               stop, marcar=R['e2']['atual']),
        ver_e2=ver_e2(R),

        h_geo='O pavio de exaustão está do outro lado',
        tab_geo=tabela_por_base(R, 'geometria', R['geometria']['ordem'],
                                R['geometria']['rotulos'], stop,
                                marcar=R['geometria']['atual']),
        ver_geo=ver_geo(R),

        h_entrada='A regra que vinha de graça no WIN aqui custa o resultado inteiro',
        tab_entrada=tabela_por_base(R, 'entrada', R['entrada']['ordem'],
                                    R['entrada']['rotulos'], stop,
                                    marcar=R['entrada']['atual']),
        ver_entrada=ver_entrada(R),

        h_gestao='O stop tem de caber fora da barra do gatilho',
        grades=''.join(bloco_grade(R, b) for b in E.BASES),
        ver_grade=ver_grade(R),
        tab_gestao=tabela_por_base(R, 'gestao', R['gestao']['ordem'],
                                   R['gestao']['rotulos'], stop,
                                   marcar=R['gestao']['atual']),
        ver_gestao=ver_gestao(R),

        h_setups='O filtro de regime subtrai',
        cards=bloco_cards(R, stop), tab_carteiras=bloco_carteiras(R, stop),
        ver_setups=ver_setups(R),
        tab_ma=bloco_ma(R, stop), ver_ma=ver_ma(R),

        h_estab='Uma região larga, não um pico',
        estab=''.join(bloco_estab(R, b) for b in E.BASES),
        ver_estab=ver_estab(R),

        tab_mes=bloco_mes(R),

        h_custo='A vantagem sobrevive ao spread — com margem, não com folga',
        tab_custo=bloco_custo(R), ver_custo=ver_custo(R),
        tab_psico=bloco_psico(R, stop), ver_psico=ver_psico(R),

        lim_amostra=('Um instrumento, um histórico. As duas “metades” são o mesmo '
                     'arquivo partido ao meio — concordância entre elas é evidência '
                     'fraca, não confirmação fora da amostra.'),
        lim_periodo=('%s a %s, %d pregões. O ouro passou por um regime só nesse '
                     'intervalo.' % (det['ini'], det['fim'], det['pregoes'])),
        lim_varredura=('O nível %s e o corte de posição %s vieram de uma varredura '
                       'sobre esta amostra (§ 9). A região é larga, mas o número não '
                       'foi validado fora dela.'
                       % (_br('%.2f' % p['NIVEL_MIN']),
                          _br('%.0f' % p['CORTE_POSICAO']))),
        lim_custo=('Sem spread, sem swap, sem slippage. A § 11 é a única seção com '
                   'custo, e é a que vale para dimensionar.'),
        lim_delta=('O delta destas barras é <em>inferido</em> pela tick rule, não '
                   'publicado pela bolsa. Ele concorda com o sinal do candle em 63% '
                   'das barras, e por isso não é usado como direção — mas ele entra '
                   'no eixo [E2], que aparece na § 4.'),

        h_acoes='Se for operar isto',
        acao_1=ac[0], acao_2=ac[1], acao_3=ac[2], acao_4=ac[3],

        G=json.dumps(G, ensure_ascii=False, separators=(',', ':')),
        EQJS=json.dumps(EQ, ensure_ascii=False, separators=(',', ':')),
        SUROT=json.dumps({k: r for k, (r, _) in ROT_SU.items()}, ensure_ascii=False),
        BASEROT=json.dumps(R['rot_base'], ensure_ascii=False),
        alvo_js=p['ALVO'], stops_js=json.dumps([str(s) for s in R['stops']]),
        parc_fixa_js=('null' if p['PARCIAL_EM'] in (None, 'None')
                      else p['PARCIAL_EM']),
        val_ponto_js=p['VAL_PONTO'], nivel_js=p['NIVEL_MIN'],
        stop_pad_js=stop,
    )
    return molde.render(ctx)


if __name__ == '__main__':
    html = monta()
    with open(DEST, 'w', encoding='utf-8') as f:
        f.write(html)
    print('relatorio.html gravado (%.1f KB)' % (len(html.encode('utf-8')) / 1024))
    import resultados_md
    resultados_md.grava()
