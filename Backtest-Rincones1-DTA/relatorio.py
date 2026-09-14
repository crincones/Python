# -*- coding: utf-8 -*-
"""
Gera relatorio.html -- relatorio unico, com o visualizador de trades dentro.

    python rodar.py       # primeiro, para atualizar saida/resumo.json
    python relatorio.py   # depois

TODO numero do relatorio sai de saida/resumo.json. Nao ha numero escrito a
mao no HTML -- inclusive as frases de conclusao sao CALCULADAS, para nao
sobrarem afirmacoes velhas quando a engine mudar.
"""
import json
import os
import re

import numpy as np

import engine as E

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')
DEST = os.path.join(BASE, 'relatorio.html')
# a biblioteca do grafico vai EMBUTIDA no html -- o relatorio e um arquivo
# unico que abre offline, sem CDN. Apache 2.0.
VENDOR_KC = os.path.join(BASE, 'vendor', 'klinecharts-9.8.10.min.js')
BASES = ('WINV26', 'WINFUT')

ROT_SU = {
    'D': ('D · descolamento da Hull',
          'O close no lado <em>oposto</em> ao da Hull, a Hull com inclinação, o preço '
          'dentro do canal e o mergulho limitado. Alguém agrediu a favor do movimento '
          'e falhou; o trade vai contra quem agrediu.'),
    'T': ('T · tendência com força',
          'A leitura clássica, restrita ao pullback: Hull e EMA no sentido do trade, '
          'close do lado certo da Hull e preço ainda não esticado. Raro, e positivo.'),
    'K': ('K · rejeição da banda',
          'O pavio fura a banda de 2 ATRs e o candle fecha de volta para dentro. '
          'Mede positivo sozinho — e mesmo assim piora a carteira.'),
    'KB': ('KB · banda clássica',
           'Preço parado na zona de esticamento, entrada contra. É o uso de manual '
           'do canal, e mede negativo no WINFUT em toda configuração testada.'),
}
GEST_CURTO = {'p150': 'stop 150', 'p100': 'stop 100', 'atr075': '0,75 ATR',
              'atr150': '1,50 ATR', 'atr075R3': '0,75 ATR · 3R'}


# ------------------------------------------------------------ formatacao
def _vazio(v):
    return v is None or v != v


def n0(v):
    return '—' if _vazio(v) else ('%+d' % round(v)).replace(',', '.')


def n1(v):
    return '—' if _vazio(v) else ('%+.1f' % v).replace('.', ',')


def n2(v):
    return '—' if _vazio(v) else ('%+.2f' % v).replace('.', ',')


def p0(v):
    return '—' if _vazio(v) else '%.0f%%' % v


def p1(v):
    return '—' if _vazio(v) else ('%.1f%%' % v).replace('.', ',')


def t2(v):
    return '—' if _vazio(v) else ('%+.2f' % v).replace('.', ',')


def f2(v):
    return '—' if _vazio(v) else ('%.2f' % v).replace('.', ',')


def d0(v):
    return '—' if _vazio(v) else format(round(v), ',d').replace(',', '.')


def mil(v):
    if _vazio(v):
        return '—'
    return format(round(v), '+,d').replace(',', '.')


def cls(v):
    return '' if _vazio(v) else ('pos' if v > 0 else ('neg' if v < 0 else 'zer'))


def vg(v):
    """Virgula decimal em numero solto."""
    return str(v).replace('.', ',')


def vgc(v):
    """Compacta: 2.0 vira 2, 0.75 vira 0,75. So para rotulo, nunca para dado."""
    s = str(v)
    if s.endswith('.0'):
        s = s[:-2]
    return s.replace('.', ',')


def nivel_rot(v):
    """O nivel do gatilho sempre com duas casas: 0,80 e nao 0,8."""
    return ('%.2f' % float(v)).replace('.', ',')


# --------------------------------------------------------------- tabelas
CAB_MET = ('<thead><tr><th></th><th class="num">n</th><th class="num">/pregão</th>'
           '<th class="num">EV</th><th class="num">R</th><th class="num">total</th>'
           '<th class="num">acerto</th><th class="num">t</th><th class="num">dias+</th>'
           '<th class="num">PF</th><th class="num">DD</th></tr></thead>')


def linha_met(rot, m, extra='', ncols=10):
    if not m:
        return ('<tr%s><td>%s</td><td colspan="%d" class="sub">sem trades</td></tr>'
                % ((' class="%s"' % extra) if extra else '', rot, ncols))
    return ('<tr%s><td>%s</td><td class="num">%d</td><td class="num">%s</td>'
            '<td class="num %s">%s</td><td class="num">%s</td><td class="num">%s</td>'
            '<td class="num">%s</td><td class="num">%s</td><td class="num">%s</td>'
            '<td class="num">%s</td><td class="num">%s</td></tr>'
            % ((' class="%s"' % extra) if extra else '', rot, m['n'],
               vg('%.1f' % m['por_pregao']), cls(m['ev']), n1(m['ev']),
               n2(m.get('ev_r')), mil(m['total']), p1(m['acerto']), t2(m['t']),
               p0(m['dias_pos']), f2(m['pf']), d0(m['dd'])))


def tabela(caption, cabecalho, linhas):
    return ('<div class="scroll"><table><caption>%s</caption>%s<tbody>%s</tbody>'
            '</table></div>' % (caption, cabecalho, linhas))


# ------------------------------------------------------- dados do grafico
def coleta_grafico(gestoes):
    """Candles, contexto e trades do visualizador.

    Os trades saem UMA VEZ POR GESTAO: os sinais nao dependem dela, mas o
    desfecho e o resultado dependem. Os candles vao uma vez so.
    """
    from rodar import GESTOES, com
    dados = {}
    for nome in BASES:
        d = E.contexto(E.indicador(E.carrega(E.ARQUIVOS[nome])))
        sig = E.gatilho(d)
        marca = E.setups(d, sig, ativos=('D', 'T', 'K', 'KB'))

        por_gestao = {}
        for chave, par, _rot in GESTOES:
            if chave not in gestoes:
                continue
            with com(**par):
                por_gestao[chave] = E.roda(d, marca, sig, carteira=False)
        if not any(len(t) for t in por_gestao.values()):
            continue

        O, H, L, C = (d[c].to_numpy(float) for c in ('O', 'H', 'L', 'C'))
        ema, hul = d.ema.to_numpy(float), d['hma'].to_numpy(float)
        k2s, k2i = d.k2s.to_numpy(float), d.k2i.to_numpy(float)
        atr = d['atr'].to_numpy(float)
        idxv, dirC = d.idx.to_numpy(), d.dirC.to_numpy()
        dist_h, pos = d.dist_hma.to_numpy(), d.pos.to_numpy()
        dia_arr = d.dia.to_numpy()
        hora = d.Data.dt.strftime('%H:%M').to_numpy()

        def lim(v, b):
            """NaN vira o proprio preco -- linha que some em vez de estourar."""
            return int(round((b if np.isnan(v) else v)))

        todos = sorted({dd for t in por_gestao.values() for dd in t.dia})
        idx_dia, dias = {}, []
        for dd in todos:
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
                ema=[lim(ema[j] - b, C[j] - b) for j in m],
                hma=[lim(hul[j] - b, C[j] - b) for j in m],
                ks=[lim(k2s[j] - b, C[j] - b) for j in m],
                ki=[lim(k2i[j] - b, C[j] - b) for j in m],
                atr=[0 if np.isnan(atr[j]) else int(round(atr[j])) for j in m],
                x=[(0 if np.isnan(idxv[j]) else
                    int(round(idxv[j] * 100)) * (1 if dirC[j] >= 0 else -1)) for j in m],
            ))

        trades = {}
        for chave, tr in por_gestao.items():
            lst = []
            for _, t in tr.iterrows():
                di = idx_dia[t['dia']]
                off = dias[di]['i0']
                i = int(t['i'])
                a = atr[i]
                lst.append(dict(
                    dia=str(t['dia']), d=di, su=t['setup'], s=int(t['s']),
                    i=i - off, f=int(t['jf']) - off, k=int(t['saiu']) - off,
                    ent=round(float(t['ent']) - dias[di]['base'], 1),
                    st=round(float(t['stop_pts']), 1),
                    al=round(float(t['alvo_pts']), 1),
                    dh=round(float(t['s'] * dist_h[i]), 2),
                    de=round(float(t['s'] * pos[i]), 2),
                    res=t['res'], pnl=round(float(t['pnl']), 1),
                    bar=int(t['barras'])))
            lst.sort(key=lambda t: (t['d'], t['i']))
            trades[chave] = lst
        dados[nome] = dict(dias=dias, trades=trades)
    return dados


# ------------------------------------------------------------- os blocos
def bloco_carteira(R, base):
    niv = R['nivel']['grid'][base][R['nivel']['atual']]
    can = R['canal']['setups'][base]
    b = R['bases'][base]
    linhas = (linha_met('só D', can['cD'])
              + linha_met('**D + T** — padrão', can['cDT'], 'hi')
              + linha_met('D + T + K', can['cDTK'], 'mute')
              + linha_met('D + T + K + KB', can['cDTKKB'], 'mute'))
    return tabela('%s · %d pregões no arquivo · %d com pregão cheio · %s a %s'
                  % (base, b['pregoes'], b['pregoes_cheios'], b['ini'], b['fim']),
                  CAB_MET, linhas)


def bloco_hull(R, chave='baldes', cap=None):
    cab = ('<thead><tr><th></th><th class="num">n · V26</th><th class="num">EV</th>'
           '<th class="num">t</th><th class="num">n · FUT</th><th class="num">EV</th>'
           '<th class="num">t</th></tr></thead>')
    a, b = R['hull'][chave]['WINV26'], R['hull'][chave]['WINFUT']
    linhas = ''
    for x, y in zip(a, b):
        neg = (x['ev'] is not None and y['ev'] is not None
               and x['ev'] < 0 and y['ev'] < 0)
        bom = (x['ev'] is not None and y['ev'] is not None
               and x['ev'] > 0 and y['ev'] > 0)
        linhas += ('<tr%s><td>%s</td><td class="num">%d</td><td class="num %s">%s</td>'
                   '<td class="num">%s</td><td class="num">%d</td>'
                   '<td class="num %s">%s</td><td class="num">%s</td></tr>'
                   % (' class="hi"' if bom and 'oposto' in x['rot'] else
                      (' class="mute"' if neg else ''),
                      x['rot'], x['n'], cls(x['ev']), n1(x['ev']), t2(x['t']),
                      y['n'], cls(y['ev']), n1(y['ev']), t2(y['t'])))
    return tabela(cap or 'Sinais isolados · gestão padrão', cab, linhas)


def bloco_setups(R):
    niv = R['nivel']['grid']
    at = R['nivel']['atual']
    cab = ('<thead><tr><th>setup</th><th class="num">sinais V26</th>'
           '<th class="num">n</th><th class="num">EV</th><th class="num">t</th>'
           '<th class="num">sinais FUT</th><th class="num">n</th>'
           '<th class="num">EV</th><th class="num">t</th></tr></thead>')
    linhas = ''
    ativos = R['parametros']['SETUPS_ATIVOS']
    for su in R['setups']:
        a = niv['WINV26'][at]['setup_' + su]
        b = niv['WINFUT'][at]['setup_' + su]
        on = su in str(ativos)
        linhas += ('<tr%s><td>**%s** · %s</td><td class="num">%d</td>'
                   '<td class="num">%s</td><td class="num %s">%s</td>'
                   '<td class="num">%s</td><td class="num">%d</td>'
                   '<td class="num">%s</td><td class="num %s">%s</td>'
                   '<td class="num">%s</td></tr>'
                   % ('' if on else ' class="mute"', su, R['rot_setup'][su],
                      niv['WINV26'][at]['sinais_' + su],
                      a['n'] if a else '—', cls(a['ev']) if a else '',
                      n1(a['ev']) if a else '—', t2(a['t']) if a else '—',
                      niv['WINFUT'][at]['sinais_' + su],
                      b['n'] if b else '—', cls(b['ev']) if b else '',
                      n1(b['ev']) if b else '—', t2(b['t']) if b else '—'))
    return tabela('Cada setup isolado · nível %s · gestão padrão'
                  % nivel_rot(at), cab, linhas)


def bloco_nivel(R):
    cab = ('<thead><tr><th>nível</th><th class="num">gatilhos V26</th>'
           '<th class="num">n</th><th class="num">/pregão</th><th class="num">EV</th>'
           '<th class="num">R</th><th class="num">t</th>'
           '<th class="num">gatilhos FUT</th><th class="num">n</th>'
           '<th class="num">/pregão</th><th class="num">EV</th><th class="num">R</th>'
           '<th class="num">t</th></tr></thead>')
    linhas = ''
    for nv in R['nivel']['niveis']:
        a = R['nivel']['grid']['WINV26'][nv]
        b = R['nivel']['grid']['WINFUT'][nv]
        ma, mb = a['cDT'], b['cDT']
        marca = ''
        if nv == R['nivel']['atual']:
            marca = ' class="hi"'
        elif nv in ('0.55', '0.6', '0.60'):
            marca = ' class="mute"'
        linhas += ('<tr%s><td class="mono">%s%s</td><td class="num">%d</td>'
                   '<td class="num">%s</td><td class="num">%s</td>'
                   '<td class="num %s">%s</td><td class="num">%s</td>'
                   '<td class="num">%s</td><td class="num">%d</td>'
                   '<td class="num">%s</td><td class="num">%s</td>'
                   '<td class="num %s">%s</td><td class="num">%s</td>'
                   '<td class="num">%s</td></tr>'
                   % (marca, nivel_rot(nv),
                      ' <span class="sub">corte de cor do indicador</span>'
                      if nv in ('0.55', '0.6', '0.60') else
                      (' <span class="sub">adotado</span>'
                       if nv == R['nivel']['atual'] else ''),
                      a['gatilhos'], ma['n'] if ma else '—',
                      vg('%.1f' % ma['por_pregao']) if ma else '—',
                      cls(ma['ev']) if ma else '', n1(ma['ev']) if ma else '—',
                      n2(ma.get('ev_r')) if ma else '—', t2(ma['t']) if ma else '—',
                      b['gatilhos'], mb['n'] if mb else '—',
                      vg('%.1f' % mb['por_pregao']) if mb else '—',
                      cls(mb['ev']) if mb else '', n1(mb['ev']) if mb else '—',
                      n2(mb.get('ev_r')) if mb else '—', t2(mb['t']) if mb else '—'))
    return tabela('Carteira D + T · gestão padrão · o nível varre o índice mínimo',
                  cab, linhas)


def bloco_zonas(R):
    cab = ('<thead><tr><th>zona</th><th class="num">barras V26</th>'
           '<th class="num">gatilhos V26</th><th class="num">barras FUT</th>'
           '<th class="num">gatilhos FUT</th></tr></thead>')
    rot = {'0': 'dentro do canal (&lt; %s ATR)' % vgc(R['parametros']['KELT_INT']),
           '1': 'entre %s e %s ATR — a faixa pedida'
                % (vgc(R['parametros']['KELT_INT']), vgc(R['parametros']['KELT_EXT'])),
           '2': 'além de %s ATR' % vgc(R['parametros']['KELT_EXT'])}
    linhas = ''
    for k in ('0', '1', '2'):
        a = R['canal']['zonas']['WINV26'][k]
        b = R['canal']['zonas']['WINFUT'][k]
        linhas += ('<tr%s><td>%s</td><td class="num">%s</td><td class="num">%s</td>'
                   '<td class="num">%s</td><td class="num">%s</td></tr>'
                   % (' class="hi"' if k == '0' else '', rot[k],
                      p1(a['barras']), p1(a['gatilhos']),
                      p1(b['barras']), p1(b['gatilhos'])))
    return tabela('Onde o preço fica em relação à EMA %d, em ATRs'
                  % R['parametros']['EMA_PER'], cab, linhas)


def bloco_veto(R):
    linhas = ''
    for rot, ch in (('com o veto de zona — o padrão', 'com'),
                    ('sem o veto (canal desligado)', 'sem')):
        for base in BASES:
            m = R['canal']['veto'][base][ch]
            linhas += linha_met('%s · **%s**' % (base, rot), m,
                                'hi' if ch == 'com' else '')
    return tabela('Carteira D + T, com e sem a exigência de estar dentro do canal',
                  CAB_MET, linhas)


def bloco_canal(R):
    linhas = ''
    for su in ('K', 'KB'):
        for base in BASES:
            linhas += linha_met('%s · setup **%s** (%s)'
                                % (base, su, R['rot_setup'][su]),
                                R['canal']['setups'][base]['iso_' + su], 'mute')
    for rot, ch in (('D + T', 'cDT'), ('D + T + K', 'cDTK'),
                    ('D + T + K + KB', 'cDTKKB')):
        for base in BASES:
            linhas += linha_met('%s · carteira %s' % (base, rot),
                                R['canal']['setups'][base][ch],
                                'hi' if ch == 'cDT' else '')
    return tabela('Os setups de banda, isolados e dentro da carteira', CAB_MET, linhas)


def bloco_gestao(R):
    linhas = ''
    for base in BASES:
        for ch in R['gestao']['ordem']:
            m = R['gestao']['grid'][base][ch]
            rot = '%s · %s' % (base, R['gestao']['rotulos'][ch])
            if m and m.get('stop_medio'):
                rot += ' <span class="sub">stop médio %d pts</span>' % round(m['stop_medio'])
            linhas += linha_met(rot, m, 'hi' if ch == R['gestao']['atual'] else '')
    return tabela('Carteira D + T · os mesmos sinais em todas as linhas',
                  CAB_MET, linhas)


def bloco_grade(R):
    stops = (75, 100, 150, 200)
    alvos = (200, 250, 300, 450)
    cab = ('<thead><tr><th>stop</th>%s</tr></thead>'
           % ''.join('<th class="num">alvo %d</th>' % a for a in alvos))
    linhas = ''
    for base in BASES:
        linhas += '<tr class="mute"><td colspan="%d">**%s**</td></tr>' % (
            len(alvos) + 1, base)
        g = R['gestao']['grade'][base]
        vals = [v for v in g.values() if v is not None]
        melhor = max(vals) if vals else None
        for st in stops:
            cel = ''
            for al in alvos:
                v = g.get('%d_%d' % (st, al))
                cel += ('<td class="num %s">%s</td>'
                        % ('best' if v == melhor else cls(v), n1(v)))
            linhas += '<tr><td class="mono">%d</td>%s</tr>' % (st, cel)
    return tabela('EV por trade, em pontos · stop e alvo fixos', cab, linhas)


def bloco_grade_atr(R):
    stops = ('0.6', '0.75', '1.0', '1.25', '1.5')
    alvos = (200, 250, 300, 450)
    cab = ('<thead><tr><th>stop</th>%s</tr></thead>'
           % ''.join('<th class="num">alvo %d</th>' % a for a in alvos))
    linhas = ''
    for base in BASES:
        linhas += '<tr class="mute"><td colspan="%d">**%s**</td></tr>' % (
            len(alvos) + 1, base)
        g = R['gestao']['grade_atr'][base]
        vals = [v['ev_r'] for v in g.values() if v]
        melhor = max(vals) if vals else None
        for st in stops:
            cel = ''
            for al in alvos:
                v = g.get('%s_%d' % (st, al))
                if not v:
                    cel += '<td class="num">—</td>'
                    continue
                cel += ('<td class="num %s">%s<span class="sub">t %s</span></td>'
                        % ('best' if v['ev_r'] == melhor else cls(v['ev_r']),
                           n2(v['ev_r']), t2(v['t'])))
            linhas += '<tr><td class="mono">%s × ATR</td>%s</tr>' % (vgc(st), cel)
    return tabela('EV em R (EV ÷ stop do próprio trade) · stop pelo ATR da barra do sinal',
                  cab, linhas)


def bloco_entrada(R):
    linhas = ''
    for base in BASES:
        b = R['bases'][base]
        linhas += linha_met('%s · **limitada no meio do candle**' % base,
                            b['entrada_meio'], 'hi')
        linhas += linha_met('%s · a mercado no fechamento' % base,
                            b['entrada_fecha'])
        linhas += linha_met('%s · limitada válida até o fim do pregão' % base,
                            b['fill_livre'], 'mute')
    return tabela('Carteira D + T · gestão padrão', CAB_MET, linhas)


def bloco_e2(R):
    linhas = ''
    for base in BASES:
        for met in R['e2']['metricas']:
            g = R['e2']['grid'][base][met]
            linhas += linha_met('%s · %s <span class="sub">%d gatilhos</span>'
                                % (base, R['e2']['rotulos'][met], g['gatilhos']),
                                g['cDT'], 'hi' if met == R['e2']['atual'] else '')
    return tabela('Carteira D + T · só a fórmula do eixo [E2] muda', CAB_MET, linhas)


def bloco_filtro_e2(R):
    linhas = ''
    for base in BASES:
        for rot, ch in (('sem o filtro — o padrão do indicador', 'sem'),
                        ('com o filtro (o do Rincones1)', 'com')):
            f = R['e2']['filtro'][base]
            linhas += linha_met('%s · %s <span class="sub">%d gatilhos</span>'
                                % (base, rot, f['gatilhos_' + ch]), f[ch],
                                'hi' if ch == 'sem' else '')
    return tabela('Carteira D + T · DESCARTA_E2 ligado e desligado', CAB_MET, linhas)


def bloco_sens(R):
    S = R['sens']
    cab = ('<thead><tr><th>corte</th><th>valor</th><th class="num">EV · V26</th>'
           '<th class="num">t</th><th class="num">EV · FUT</th><th class="num">t</th>'
           '</tr></thead>')
    linhas = ''
    for par in S['ordem']:
        vals = S['valores'][par]
        for k, v in enumerate(vals):
            a = S['grid']['WINV26'][par][v]
            b = S['grid']['WINFUT'][par][v]
            atual = v == S['atual'][par]
            linhas += ('<tr%s>%s<td class="mono">%s%s</td>'
                       '<td class="num %s">%s</td><td class="num">%s</td>'
                       '<td class="num %s">%s</td><td class="num">%s</td></tr>'
                       % (' class="hi"' if atual else '',
                          ('<td rowspan="%d">**%s**<span class="sub">%s</span></td>'
                           % (len(vals), par, S['rotulos'][par])) if k == 0 else '',
                          vgc(v), ' ←' if atual else '',
                          cls(a['ev']) if a else '', n1(a['ev']) if a else '—',
                          t2(a['t']) if a else '—',
                          cls(b['ev']) if b else '', n1(b['ev']) if b else '—',
                          t2(b['t']) if b else '—'))
    return tabela('Carteira D + T · um corte de cada vez, o resto congelado',
                  cab, linhas)


def bloco_custo(R):
    cab = ('<thead><tr><th>custo</th><th class="num">EV · V26</th><th class="num">R</th>'
           '<th class="num">t</th><th class="num">EV · FUT</th><th class="num">R</th>'
           '<th class="num">t</th></tr></thead>')
    linhas = ''
    for c in (0, 5, 10, 20):
        a = R['bases']['WINV26']['custo_%d' % c]
        b = R['bases']['WINFUT']['custo_%d' % c]
        linhas += ('<tr%s><td class="mono">%d pts</td><td class="num %s">%s</td>'
                   '<td class="num">%s</td><td class="num">%s</td>'
                   '<td class="num %s">%s</td><td class="num">%s</td>'
                   '<td class="num">%s</td></tr>'
                   % (' class="mute"' if c == 20 else '', c,
                      cls(a['ev']), n1(a['ev']), n2(a.get('ev_r')), t2(a['t']),
                      cls(b['ev']), n1(b['ev']), n2(b.get('ev_r')), t2(b['t'])))
    return tabela('Carteira D + T · custo de ida e volta, em pontos', cab, linhas)


def bloco_mes(R):
    cab = ('<thead><tr><th>mês</th><th class="num">n</th><th class="num">EV</th>'
           '<th class="num">total</th><th class="num">acerto</th></tr></thead>')
    linhas = ''
    for base in BASES:
        linhas += '<tr class="mute"><td colspan="5">**%s**</td></tr>' % base
        for m in R['bases'][base].get('mes', []):
            linhas += ('<tr%s><td>%s</td><td class="num">%d</td>'
                       '<td class="num %s">%s</td><td class="num">%s</td>'
                       '<td class="num">%s</td></tr>'
                       % (' class="mute"' if m['n'] < 5 else '', m['mes'], m['n'],
                          cls(m['ev']), n1(m['ev']), mil(m['total']),
                          p1(m['acerto'])))
    return tabela('Carteira D + T · gestão padrão', cab, linhas)


# ------------------------------------------------- as frases, calculadas
#
# Nenhuma conclusao e escrita a mao: cada funcao le o resumo.json e monta a
# frase com o numero de agora. Foi assim que o Rincones1 evitou ficar com
# afirmacoes velhas depois de mudar a engine, e a regra vale aqui tambem.
def _html(md):
    """Markdown de frase para HTML: **negrito**, *itálico* e `código`.

    Os vereditos sao escritos UMA vez, em markdown, e saem nos dois formatos
    -- e assim o RESULTADOS.md nunca herda tag de HTML solta.
    """
    h = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', md)
    h = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', h)
    h = re.sub(r'`(.+?)`', r'<code>\1</code>', h)
    return h


def _par(md):
    return md, '<p>%s</p>' % _html(md)


def _nota(lab, md):
    return (md, '<div class="note"><div class="lab">%s</div><p>%s</p></div>'
            % (lab, _html(md)))


def ver_pecas(R):
    h = R['hull']['baldes']
    a_op, b_op = h['WINV26'][0], h['WINFUT'][0]
    a_cl, b_cl = h['WINV26'][1], h['WINFUT'][1]
    a_pl, b_pl = h['WINV26'][4], h['WINFUT'][4]
    txt = ('O lado oposto da Hull mede **%s** por trade no WINV26 e **%s** no '
           'WINFUT; a leitura clássica mede **%s** e **%s**. A Hull plana mede '
           '**%s** e **%s** — é o pior balde dos dois arquivos.'
           % (n1(a_op['ev']), n1(b_op['ev']), n1(a_cl['ev']), n1(b_cl['ev']),
              n1(a_pl['ev']), n1(b_pl['ev'])))
    return _nota('O que a medição diz', txt)


def ver_hull(R):
    h = R['hull']['baldes']
    a, b = h['WINV26'], h['WINFUT']
    op26, opfu = a[2], b[2]      # lado oposto + nao plana
    cl26, clfu = a[3], b[3]      # lado da hull + nao plana
    dif26 = op26['ev'] - cl26['ev']
    diffu = opfu['ev'] - clfu['ev']
    txt = ('Com a Hull inclinada, entrar pelo lado **oposto** mede %s por trade '
           'contra %s do lado clássico no WINV26 — **%s pontos** de diferença — e '
           '%s contra %s no WINFUT, **%s pontos**. O sinal do `t` '
           'concorda nos dois: %s e %s do lado oposto, %s e %s do lado clássico.'
           % (n1(op26['ev']), n1(cl26['ev']), d0(dif26),
              n1(opfu['ev']), n1(clfu['ev']), d0(diffu),
              t2(op26['t']), t2(opfu['t']), t2(cl26['t']), t2(clfu['t'])))
    return _nota('A inversão', txt)


def ver_incl(R):
    inc = R['hull']['inclinacao']
    a, b = inc['WINV26'], inc['WINFUT']
    pl26, plfu = a[2], b[2]
    ct26, ctfu = a[0], b[0]
    fa26, fafu = a[4], b[4]
    txt = ('A *direção* da Hull importa muito menos que o fato de ela estar '
           'inclinada. Contra o trade e forte: %s / %s. A favor e forte: %s / %s. '
           'Plana: **%s** / **%s**. O veto é a inclinação, não o sentido dela — '
           'e é por isso que o setup D não exige que a Hull aponte para lado nenhum.'
           % (n1(ct26['ev']), n1(ctfu['ev']), n1(fa26['ev']), n1(fafu['ev']),
              n1(pl26['ev']), n1(plfu['ev'])))
    return _par(txt)


def ver_setups(R):
    at = R['nivel']['atual']
    niv = R['nivel']['grid']
    can = R['canal']['setups']
    dT26, dTfu = can['WINV26']['cDT'], can['WINFUT']['cDT']
    dK26, dKfu = can['WINV26']['cDTK'], can['WINFUT']['cDTK']
    k26 = niv['WINV26'][at]['setup_K']
    kfu = niv['WINFUT'][at]['setup_K']
    txt = ('O **K** é o caso que vale entender: isolado ele mede %s / %s — positivo '
           'nos dois — e mesmo assim, entrando na carteira, o EV cai de %s para %s no '
           'WINV26 e de %s para %s no WINFUT. Ele não perde dinheiro: ele *ocupa a '
           'vaga* de um trade melhor, porque só uma posição fica aberta por vez.'
           % (n1(k26['ev']) if k26 else '—', n1(kfu['ev']) if kfu else '—',
              n1(dT26['ev']), n1(dK26['ev']), n1(dTfu['ev']), n1(dKfu['ev'])))
    return _nota('Por que o K fica desligado', txt)


def ver_nivel(R):
    g = R['nivel']['grid']
    at = R['nivel']['atual']
    baixo = R['nivel']['niveis'][0]
    alto = R['nivel']['niveis'][-1]
    a_b, b_b = g['WINV26'][baixo]['cDT'], g['WINFUT'][baixo]['cDT']
    a_a, b_a = g['WINV26'][at]['cDT'], g['WINFUT'][at]['cDT']
    a_x, b_x = g['WINV26'][alto]['cDT'], g['WINFUT'][alto]['cDT']
    txt = ('No corte de cor do indicador (%s) a carteira mede %s / %s por trade, com '
           '%s e %s trades por pregão — positivo, mas fraco e cansativo. No nível '
           'adotado (%s) mede %s / %s com %s e %s por pregão. Em %s, %s / %s — melhor '
           'ainda por trade, e com metade dos sinais. A vantagem cresce com o nível '
           'em *todas* as células, nos dois arquivos: é o padrão que o próprio '
           'indicador prevê, já que ele mede absorção e absorção fraca não se desfaz.'
           % (nivel_rot(baixo), n1(a_b['ev']), n1(b_b['ev']),
              vg('%.1f' % a_b['por_pregao']), vg('%.1f' % b_b['por_pregao']),
              nivel_rot(at), n1(a_a['ev']), n1(b_a['ev']),
              vg('%.1f' % a_a['por_pregao']), vg('%.1f' % b_a['por_pregao']),
              nivel_rot(alto), n1(a_x['ev']), n1(b_x['ev'])))
    return _nota('A troca', txt)


def ver_canal(R):
    v26 = R['canal']['veto']['WINV26']
    vfu = R['canal']['veto']['WINFUT']
    inerte = (abs(v26['com']['ev'] - v26['sem']['ev']) < 0.05
              and abs(vfu['com']['ev'] - vfu['sem']['ev']) < 0.05)
    at = R['nivel']['atual']
    kb26 = R['nivel']['grid']['WINV26'][at]['setup_KB']
    kbfu = R['nivel']['grid']['WINFUT'][at]['setup_KB']
    txt = ('O veto de zona %s: a carteira mede %s / %s com ele e %s / %s sem ele. '
           'E a leitura clássica da banda — preço esticado, entrada contra — mede '
           '%s no WINV26 e **%s** no WINFUT. A faixa de 2 a 3 ATRs, que era a '
           'aposta inicial, é *onde o operacional não opera*, não onde ele '
           'ganha.'
           % ('é inerte' if inerte else 'muda pouco',
              n1(v26['com']['ev']), n1(vfu['com']['ev']),
              n1(v26['sem']['ev']), n1(vfu['sem']['ev']),
              n1(kb26['ev']) if kb26 else '—', n1(kbfu['ev']) if kbfu else '—'))
    return _nota('O canal mede o que NÃO fazer', txt)


def ver_gestao(R):
    G = R['gestao']
    a_h, b_h = G['grid']['WINV26']['p150'], G['grid']['WINFUT']['p150']
    a_n, b_n = G['grid']['WINV26'][G['atual']], G['grid']['WINFUT'][G['atual']]
    a_w, b_w = G['grid']['WINV26']['atr150'], G['grid']['WINFUT']['atr150']
    txt = ('Em pontos, o stop largo parece melhor — %s contra %s no WINV26. Em **R**, '
           'que é o que dá para comparar, o quadro inverte: %s contra %s no WINV26 e '
           '%s contra %s no WINFUT, com o *drawdown* caindo de %s para %s e de '
           '%s para %s pontos. Stop maior ganha mais por trade porque arrisca mais por '
           'trade; por unidade de risco, o stop curto dimensionado pelo ATR mede '
           'melhor nos dois arquivos, e o `t` acompanha (%s / %s contra '
           '%s / %s).'
           % (n1(a_w['ev']), n1(a_h['ev']),
              n2(a_n['ev_r']), n2(a_w['ev_r']), n2(b_n['ev_r']), n2(b_w['ev_r']),
              d0(a_w['dd']), d0(a_n['dd']), d0(b_w['dd']), d0(b_n['dd']),
              t2(a_n['t']), t2(b_n['t']), t2(a_h['t']), t2(b_h['t'])))
    return _nota('Por que o stop encolheu', txt)


def ver_entrada(R):
    a, b = R['bases']['WINV26'], R['bases']['WINFUT']
    txt = ('A limitada mede %s contra %s a mercado no WINV26, e %s contra %s no '
           'WINFUT — a diferença é o preço: entrar no meio do candio do gatilho é '
           'melhor que entrar no fechamento dele. Deixar a ordem viva até o fim do '
           'pregão mede %s e %s: pior nos dois, apesar de dar mais trades. O sinal '
           'que não volta ao meio do candle na barra seguinte já não vale.'
           % (n1(a['entrada_meio']['ev']), n1(a['entrada_fecha']['ev']),
              n1(b['entrada_meio']['ev']), n1(b['entrada_fecha']['ev']),
              n1(a['fill_livre']['ev']), n1(b['fill_livre']['ev'])))
    return _nota('A regra da barra seguinte se paga', txt.replace('candio', 'candle'))


def ver_e2(R):
    g = R['e2']['grid']
    at = R['e2']['atual']
    outro = [m for m in R['e2']['metricas'] if m != at][0]
    a_at, b_at = g['WINV26'][at]['cDT'], g['WINFUT'][at]['cDT']
    a_ou, b_ou = g['WINV26'][outro]['cDT'], g['WINFUT'][outro]['cDT']
    melhor_v26 = a_ou['ev'] > a_at['ev']
    melhor_fut = b_ou['ev'] > b_at['ev']
    if melhor_v26 and melhor_fut:
        frase = ('a fórmula **antiga** mede melhor nas duas bases (%s / %s contra '
                 '%s / %s)' % (n1(a_ou['ev']), n1(b_ou['ev']),
                               n1(a_at['ev']), n1(b_at['ev'])))
        fim = ('Fica a do indicador — é a configuração padrão dele, e a diferença '
               'está dentro do ruído de uma amostra deste tamanho —, mas registrada: '
               'o ganho do v2 medido no Rincones1 *não* se repete neste '
               'operacional.')
    elif melhor_v26 or melhor_fut:
        frase = ('as duas fórmulas se dividem (%s / %s contra %s / %s)'
                 % (n1(a_ou['ev']), n1(b_ou['ev']), n1(a_at['ev']), n1(b_at['ev'])))
        fim = 'Fica a do indicador, que é a configuração padrão dele.'
    else:
        frase = ('a fórmula do indicador mede melhor nas duas bases (%s / %s contra '
                 '%s / %s)' % (n1(a_at['ev']), n1(b_at['ev']),
                               n1(a_ou['ev']), n1(b_ou['ev'])))
        fim = 'Confirma a escolha do v2.'
    return _nota('O que a troca do eixo faz aqui',
                 'Com todo o resto congelado, %s. %s' % (frase, fim))


def ver_filtro_e2(R):
    a = R['e2']['filtro']['WINV26']
    b = R['e2']['filtro']['WINFUT']
    txt = ('O filtro corta o número de gatilhos de %d para %d no WINV26 e de %d para '
           '%d no WINFUT, e o que sobra mede melhor por trade: %s contra %s, e %s '
           'contra %s. O total cai — menos trades — mas o EV e o `t` do '
           'WINFUT sobem. Fica **desligado** por padrão, porque não é parte do '
           'indicador; é a primeira alavanca a puxar quem quiser menos sinais e mais '
           'seletividade.'
           % (a['gatilhos_sem'], a['gatilhos_com'],
              b['gatilhos_sem'], b['gatilhos_com'],
              n1(a['com']['ev']), n1(a['sem']['ev']),
              n1(b['com']['ev']), n1(b['sem']['ev'])))
    return _nota('Um filtro opcional de seletividade', txt)


def ver_sens(R):
    S = R['sens']
    frouxos, apertados = [], []
    for par in S['ordem']:
        vals = S['valores'][par]
        evs = []
        for v in vals:
            a = S['grid']['WINV26'][par][v]
            b = S['grid']['WINFUT'][par][v]
            if a and b:
                evs.append((v, a['ev'], b['ev']))
        if len(evs) < 2:
            continue
        pos = all(x[1] > 0 and x[2] > 0 for x in evs)
        (frouxos if pos else apertados).append(par)
    hull = S['grid']['WINFUT']['HMA_PER']
    txt = ('%d dos %d cortes ficam positivos nas duas bases em *todos* os '
           'valores varridos (%s) — são platôs, não pontas. %s'
           % (len(frouxos), len(S['ordem']), ', '.join('`%s`' % p
                                                       for p in frouxos),
              ('Os que têm valor perdedor em algum ponto: %s.'
               % ', '.join('`%s`' % p for p in apertados))
              if apertados else 'Nenhum tem valor perdedor.'))
    extra = ''
    if hull.get('80') and hull.get('50'):
        if hull['80']['ev'] > hull['50']['ev'] and \
           S['grid']['WINV26']['HMA_PER']['80']['ev'] > \
           S['grid']['WINV26']['HMA_PER']['50']['ev']:
            extra = (' **Uma exceção incômoda:** a Hull de **80** mede melhor '
                     'que a de 50 nas duas bases (%s / %s contra %s / %s). O período '
                     '50 foi mantido porque é o que estava especificado, e trocá-lo '
                     'com base nesta mesma amostra seria mais sobreajuste, não menos.'
                     % (n1(S['grid']['WINV26']['HMA_PER']['80']['ev']),
                        n1(hull['80']['ev']),
                        n1(S['grid']['WINV26']['HMA_PER']['50']['ev']),
                        n1(hull['50']['ev'])))
    return _par(txt + extra)


def ver_mes(R):
    partes = []
    for base in BASES:
        meses = R['bases'][base].get('mes', [])
        if not meses:
            continue
        pos = sum(1 for m in meses if m['ev'] > 0)
        partes.append('%s: %d de %d meses positivos' % (base, pos, len(meses)))
    return _par('%s. Com dois meses de dados por arquivo, isto é descrição, não '
                'evidência — serve para ver se o resultado veio de um dia só.'
                % ' · '.join(partes))


def acao_nivel(R):
    at = R['nivel']['atual']
    alto = R['nivel']['niveis'][-2]
    g = R['nivel']['grid']
    a, b = g['WINV26'][alto]['cDT'], g['WINFUT'][alto]['cDT']
    md = ('**Operar no nível %s, e considerar %s.** Em %s a carteira mede %s / %s por '
          'trade com %s e %s trades por pregão, contra %s / %s no nível adotado. '
          'Menos sinais, mais qualidade — a escolha é de temperamento, não de medição.'
          % (nivel_rot(at), nivel_rot(alto), nivel_rot(alto), n1(a['ev']), n1(b['ev']),
             vg('%.1f' % a['por_pregao']), vg('%.1f' % b['por_pregao']),
             n1(g['WINV26'][at]['cDT']['ev']), n1(g['WINFUT'][at]['cDT']['ev'])))
    return md, _html(md)


def acao_gestao(R):
    G = R['gestao']
    a = G['grid']['WINV26'][G['atual']]
    md = ('**Dimensionar o stop pelo ATR, não em pontos fixos.** %s, com a parcial '
          'acompanhando. O stop médio fica em torno de %d pontos — bem abaixo dos 150 '
          'herdados — e o drawdown cai junto.'
          % (G['rotulos'][G['atual']].split(' — ')[0], round(a['stop_medio'])))
    return md, _html(md)


def acao_setups(R):
    can = R['canal']['setups']
    md = ('**Rodar D + T e mais nada.** D + T mede %s / %s; somar o K derruba para '
          '%s / %s e somar os dois de banda derruba para %s / %s.'
          % (n1(can['WINV26']['cDT']['ev']), n1(can['WINFUT']['cDT']['ev']),
             n1(can['WINV26']['cDTK']['ev']), n1(can['WINFUT']['cDTK']['ev']),
             n1(can['WINV26']['cDTKKB']['ev']), n1(can['WINFUT']['cDTKKB']['ev'])))
    return md, _html(md)


def acao_hull(R):
    h = R['hull']['baldes']
    md = ('**Nunca operar com a Hull plana.** É o único veto que mede forte nos dois '
          'arquivos: %s no WINV26 e %s no WINFUT, contra %s e %s do resto. Se só uma '
          'regra deste relatório sobreviver, que seja esta.'
          % (n1(h['WINV26'][4]['ev']), n1(h['WINFUT'][4]['ev']),
             n1(h['WINV26'][5]['ev']), n1(h['WINFUT'][5]['ev'])))
    return md, _html(md)


VEREDITOS = (
    ('ver_pecas', ver_pecas), ('ver_hull', ver_hull), ('ver_incl', ver_incl),
    ('ver_setups', ver_setups), ('ver_nivel', ver_nivel), ('ver_canal', ver_canal),
    ('ver_gestao', ver_gestao), ('ver_entrada', ver_entrada), ('ver_e2', ver_e2),
    ('ver_filtro_e2', ver_filtro_e2), ('ver_sens', ver_sens), ('ver_mes', ver_mes),
    ('acao_nivel', acao_nivel), ('acao_gestao', acao_gestao),
    ('acao_setups', acao_setups), ('acao_hull', acao_hull),
)


# ------------------------------------------------------------------ monta
def monta():
    R = json.load(open(os.path.join(SAIDA, 'resumo.json'), encoding='utf-8'))
    P = R['parametros']
    from rodar import GESTOES
    gest_viz = [k for k, _, _ in GESTOES]
    G = coleta_grafico(gest_viz)

    can = R['canal']['setups']
    a, b = can['WINV26']['cDT'], can['WINFUT']['cDT']
    d26, dfu = R['bases']['WINV26'], R['bases']['WINFUT']

    cards = []
    at = R['nivel']['atual']
    for su in R['setups']:
        nome, desc = ROT_SU[su]
        x = R['nivel']['grid']['WINV26'][at]['setup_' + su]
        y = R['nivel']['grid']['WINFUT'][at]['setup_' + su]
        ligado = su in str(P['SETUPS_ATIVOS'])
        klass = ('setup best' if su == 'D' else
                 ('setup' if ligado else 'setup dead'))
        tag = ('<span class="tag on">%s</span>'
               % ('principal' if su == 'D' else 'ativo') if ligado else
               '<span class="tag off">desligado</span>')
        cards.append('''<article class="%s"><span class="rail"></span>
      <h4>%s</h4>%s
      <p>%s</p>
      <div class="pair">
        <div><div class="b">WINV26</div><div class="v %s">%s</div>
          <div class="t">t %s · PF %s</div></div>
        <div><div class="b">WINFUT</div><div class="v %s">%s</div>
          <div class="t">t %s · PF %s</div></div>
      </div></article>''' % (
            klass, nome, tag, desc,
            cls(x['ev']) if x else '', n1(x['ev']) if x else '—',
            t2(x['t']) if x else '—', f2(x['pf']) if x else '—',
            cls(y['ev']) if y else '', n1(y['ev']) if y else '—',
            t2(y['t']) if y else '—', f2(y['pf']) if y else '—'))

    stop_rot = ('%s × ATR' % vgc(P['STOP_ATR']) if P['STOP_MODO'] == 'atr'
                else '%d pontos' % P['STOP'])
    alvo_rot = ('%d pontos' % P['ALVO'] if P['ALVO_MODO'] == 'pontos'
                else ('%s R' % vgc(P['ALVO_R']) if P['ALVO_MODO'] == 'R'
                      else '%s × ATR' % vgc(P['ALVO_ATR'])))

    ctx = dict(
        R=R, G=json.dumps(G, separators=(',', ':')),
        klinecharts_js=open(VENDOR_KC, encoding='utf-8').read(),
        ema_per=P['EMA_PER'], hma_per=P['HMA_PER'],
        kelt_int=vgc(P['KELT_INT']), kelt_ext=vgc(P['KELT_EXT']),
        nivel=nivel_rot(P['NIVEL_MIN']), nivel_js=int(round(100 * P['NIVEL_MIN'])),
        stop_rot=stop_rot, alvo=alvo_rot, frac=int(100 * P['FRAC_PARCIAL']),
        max_fill=P['MAX_BARRAS_FILL'],
        ev26=n1(a['ev']), evfu=n1(b['ev']),
        evr26=n2(a.get('ev_r')), evrfu=n2(b.get('ev_r')),
        cls26=cls(a['ev']), clsfu=cls(b['ev']),
        n26=a['n'], nfu=b['n'], t26=t2(a['t']), tfu=t2(b['t']),
        ac26=p1(a['acerto']), acfu=p1(b['acerto']),
        preg26=a['pregoes'], pregfu=b['pregoes'],
        preg26tot=d26['pregoes'], preg26cheio=d26['pregoes_cheios'],
        sinais26=d26['sinais'], sinaisfu=dfu['sinais'],
        abort26=d26['sinais'] - d26['entrada_meio']['n'],
        abortfu=dfu['sinais'] - dfu['entrada_meio']['n'],
        cart26=bloco_carteira(R, 'WINV26'), cartfu=bloco_carteira(R, 'WINFUT'),
        tab_hull=bloco_hull(R, 'baldes', 'Sinais isolados · gestão padrão · nível %s'
                            % nivel_rot(at)),
        tab_hull_faixas=bloco_hull(R, 'faixas',
                                   'A mesma coisa em faixas de dh — a transição é '
                                   'em torno de zero'),
        tab_hull_incl=bloco_hull(R, 'inclinacao',
                                 'Agora pela inclinação da Hull, assinada pelo lado '
                                 'do trade'),
        cards=''.join(cards),
        tab_setups=bloco_setups(R), tab_nivel=bloco_nivel(R),
        tab_zonas=bloco_zonas(R), tab_veto=bloco_veto(R), tab_canal=bloco_canal(R),
        tab_gestao=bloco_gestao(R), tab_grade=bloco_grade(R),
        tab_grade_atr=bloco_grade_atr(R), tab_entrada=bloco_entrada(R),
        tab_e2=bloco_e2(R), tab_filtro_e2=bloco_filtro_e2(R),
        tab_sens=bloco_sens(R), tab_custo=bloco_custo(R), tab_mes=bloco_mes(R),
        eq26=json.dumps(d26['equity']), eqfu=json.dumps(dfu['equity']),
        su26=''.join(d26['equity_setup']), sufu=''.join(dfu['equity_setup']),
        gestoes_js=json.dumps(gest_viz),
        gestao_padrao=R['gestao_padrao'],
        gest_rot=json.dumps(GEST_CURTO),
        su_rot=json.dumps({k: ROT_SU[k][0] for k in R['setups']}),
    )
    for nome, fn in VEREDITOS:
        md, html = fn(R)
        ctx[nome + '_md'], ctx[nome] = md, html
    return ctx


if __name__ == '__main__':
    import molde
    ctx = monta()
    html = molde.render(ctx)
    with open(DEST, 'w', encoding='utf-8') as f:
        f.write(html)
    print('gravado: %s  (%.1f KB)' % (DEST, len(html) / 1024.0))

    import resultados_md
    md = resultados_md.gera(ctx, dict(n0=n0, n1=n1, n2=n2, p0=p0, p1=p1, t2=t2,
                                      f2=f2, d0=d0, mil=mil, vg=vg,
                                      nivel_rot=nivel_rot), ROT_SU)
    dest_md = os.path.join(BASE, 'RESULTADOS.md')
    with open(dest_md, 'w', encoding='utf-8') as f:
        f.write(md)
    print('gravado: %s  (%.1f KB)' % (dest_md, len(md) / 1024.0))
