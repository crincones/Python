# -*- coding: utf-8 -*-
"""Relatorio: reversoes nas VWAP BANDS -> vwap.html + VWAP.md
(rodar depois de vwap_estudo.py)."""
import json
import os

import numpy as np

import vbase as V
from relatorio import CSS          # do projeto de origem (mesmo visual)
from textos import n, rs, cls

BASE = V.BASE
SAIDA = os.path.join(BASE, 'saida')
VENDOR = os.path.join(BASE, 'vendor', 'klinecharts-9.8.10.min.js')
T = json.load(open(os.path.join(SAIDA, 'vwap.json'), encoding='utf-8'))
TR = json.load(open(os.path.join(SAIDA, 'vwap_trades.json'), encoding='utf-8'))
M = T['meta']
GS = [('r300', 'Alvo 300 seco'), ('r500', 'Alvo 500 seco'), ('vw', 'Alvo na VWAP'), ('claude', 'Gestão CLAUDE.md')]
NOME_G = {'r300': 'stop 100 / alvo 300 seco', 'r500': 'stop 100 / alvo 500 seco',
          'vw': 'stop 100 / alvo na VWAP', 'claude': 'stop 100, parcial 50% em +100, alvo 300'}
MENU = [('resposta', 'Resposta'), ('medidas', 'Como foi medido'), ('base', 'Base'), ('padroes', 'Padrões'),
        ('banda', 'A banda importa?'), ('toques', 'Primeiros toques'), ('angulo', 'Ângulo da VWAP'),
        ('vwap', 'VWAP: entrada ou saída'), ('carteira', 'Carteira'), ('robustez', 'Robustez'),
        ('kline', 'Trade a trade'), ('conclusao', 'Conclusão')]


# ------------------------------------------------------------------ acesso
def hip(nome, gk):
    return next(r for r in T['hip'][gk] if r['nome'].startswith(nome))


def cart(nome, gk):
    return next(l for l in T['carteiras'][gk] if l['nome'].startswith(nome))


def fx(chave, faixa, fonte='faixas'):
    return next(l for l in T[fonte][chave]['lin'] if l['faixa'].startswith(faixa))


def base(gat):
    return next(b for b in T['base'] if b['gat'] == gat)


def ev(v, c=1):
    return f'<span class="{cls(v)}">{rs(v, c)}</span>'


def pc(v, c=0):
    return '-' if v is None else f'{n(v, c)}%'


# ------------------------------------------------------------------ tabelas
def por_gestao(render, gks=GS):
    return ''.join(f'<div class="gest" data-g="{gk}"{"" if gk == "r300" else " hidden"}>{render(gk)}</div>'
                   for gk, _ in gks)


def terco_tag(vals, resto=None):
    if resto is None:
        ok = [v for v in vals if v is not None]
        if len(ok) < 3:
            return ''
        k = sum(v > 0 for v in ok)
        return f'<span class="tag {"pos" if k == 3 else "neg" if k == 0 else ""}">{k} de 3 positivos</span>'
    k = sum(1 for a, b in zip(vals, resto) if a is not None and b is not None and a > b)
    return f'<span class="tag {"pos" if k == 3 else "neg" if k == 0 else ""}">{k} de 3 acima</span>'


def tab_faixa(lin, gk, rot='Faixa', outras=True):
    outros = [g for g, _ in GS if g != gk] if outras else []
    h = (f'<div class="tab"><table><thead><tr><th>{rot}</th><th>Sinais</th><th>R$/trade</th><th>Acerto</th>'
         '<th>Treino</th><th>Teste</th>'
         + ''.join(f'<th>{i}º terço</th>' for i in (1, 2, 3)) + '<th>Terços</th>'
         + ''.join(f'<th class="sec">{dict(GS)[g]}</th>' for g in outros) + '</tr></thead><tbody>')
    for l in lin:
        r = l[gk]
        h += (f"<tr><td>{l['faixa']}</td><td>{n(l['n'])}</td><td><b>{ev(r['ev'])}</b></td><td>{pc(r['wr'])}</td>"
              f"<td>{ev(r['ev_is'])} <span class=\"nota\">({n(l['n_is'])})</span></td>"
              f"<td>{ev(r['ev_oos'])} <span class=\"nota\">({n(l['n_oos'])})</span></td>"
              + ''.join(f"<td>{ev(v, 0)}</td>" for v in r['t']) + f"<td>{terco_tag(r['t'])}</td>"
              + ''.join(f"<td class=\"sec\">{ev(l[g]['ev'])}</td>" for g in outros) + '</tr>')
    return h + '</tbody></table></div>'


def tab_hip(gk):
    H = sorted(T['hip'][gk], key=lambda r: -(r['ev'] - r['resto']))
    h = ('<div class="tab"><table><thead><tr><th>Grupo</th><th>Sinais</th><th>R$/trade</th><th>Resto</th>'
         '<th>Treino (resto)</th><th>Teste (resto)</th><th>Terços: grupo (resto)</th><th>t</th><th>Percentil</th>'
         '</tr></thead><tbody>')
    for r in H:
        ter = ' · '.join(f"{ev(a, 0)} <span class=\"nota\">({rs(b, 0)})</span>" for a, b in zip(r['ter'], r['ter_resto']))
        h += (f"<tr><td>{txt(r['nome'])}</td><td>{n(r['n'])} <span class=\"nota\">({n(r['frac'] * 100, 0)}%)</span></td>"
              f"<td><b>{ev(r['ev'])}</b></td><td>{ev(r['resto'])}</td>"
              f"<td>{ev(r['ev_is'])} <span class=\"nota\">({rs(r['resto_is'], 1)})</span></td>"
              f"<td>{ev(r['ev_oos'])} <span class=\"nota\">({rs(r['resto_oos'], 1)})</span></td>"
              f"<td>{ter} {terco_tag(r['ter'], r['ter_resto'])}</td><td>{n(r['t'], 2)}</td><td>{n(r['pct'], 0)}</td></tr>")
    return h + ('</tbody></table></div><p class="nota">t: diferença grupo x resto em erros-padrão. Percentil: posição da '
                'média do grupo entre 2.000 subconjuntos sorteados do mesmo tamanho (95+ = raro por acaso). '
                'São 21 hipóteses testadas: espere uma ou outra com percentil alto só por sorte.</p>')


def tab_base():
    h = ('<div class="tab"><table><thead><tr><th>Gatilho</th><th>Sinais</th><th>Por dia</th>'
         + ''.join(f'<th>{r}<br><span class="nota">R$/sinal · treino · teste</span></th>' for _, r in GS)
         + '</tr></thead><tbody>')
    for b in T['base']:
        h += f"<tr><td>{txt(b['nome'])}</td><td>{n(b['n'])}</td><td>{n(b['dia'], 1)}</td>"
        for gk, _ in GS:
            g = b['g'][gk]
            h += f"<td><b>{ev(g['ev'])}</b> · {ev(g['ev_is'])} · {ev(g['ev_oos'])}</td>"
        h += '</tr>'
    h += '<tr class="dest"><td>Entrada aleatória (qualquer candle, lado sorteado)</td><td></td><td></td>'
    for gk, _ in GS:
        h += f"<td>{ev(T['aleatorio'][gk]) if gk != 'vw' else '<span class=nota>não se aplica</span>'}</td>"
    return h + '</tr></tbody></table></div>'


def tab_cart(gk, gid):
    h = ('<div class="tab"><table><thead><tr><th>Filtro</th><th>Sinais</th><th>Trades</th><th>Líquido</th><th>Fator</th>'
         '<th>Rebaixamento</th><th>Treino</th><th>Teste</th><th>Alvo precisa atravessar 5 pts</th></tr></thead><tbody>')
    for i, l in enumerate(T['carteiras'][gk]):
        s = l['stats']
        h += (f"<tr class=\"{'dest' if 'exaustao limpa (' in l['nome'] else ''}\"><td>{txt(l['nome'])}</td><td>{n(l['n_sinais'])}</td>"
              f"<td>{n(s['trades'])}</td><td>{ev(s['liquido'], 0)}</td><td>{n(s['fator_lucro'], 2)}</td>"
              f"<td>{rs(-s['dd_max'])}</td><td>{ev(l['is_'].get('liquido'), 0)}</td><td>{ev(l['oos'].get('liquido'), 0)}</td>"
              f"<td>{ev(l['atravessa'], 0)}</td></tr>")
    return (h + f'</tbody></table></div><div class="card"><div class="leg" id="{gid}_leg"></div>'
            f'<div class="graf" id="{gid}"></div></div>')


def tab_vwe(g):
    v = T['vwap_entrada'][g]
    gk4 = [('r300', 'Alvo 300'), ('r500', 'Alvo 500'), ('b1', 'Alvo banda 1'), ('claude', 'CLAUDE.md')]
    h = ('<div class="tab"><table><thead><tr><th>Grupo</th><th>Sinais</th>'
         + ''.join(f'<th>{r}</th>' for _, r in gk4) + '<th>Alvo 300: treino · teste</th><th>Alvo 300: terços</th></tr></thead><tbody>')
    for l in v['lin']:
        h += (f"<tr class=\"{'dest' if l['faixa'] == 'todos' else ''}\"><td>{txt(l['faixa'])}</td><td>{n(l['n'])}</td>"
              + ''.join(f"<td>{ev(l[k]['ev'])}</td>" for k, _ in gk4)
              + f"<td>{ev(l['r300']['ev_is'])} · {ev(l['r300']['ev_oos'])}</td>"
              + f"<td>{' · '.join(ev(x, 0) for x in l['r300']['t'])}</td></tr>")
    h += ('<tr><td><b>Carteira (1 posição por vez)</b></td><td></td>'
          + ''.join(f"<td>{ev(v['cart'][k]['stats']['liquido'], 0)}</td>" for k, _ in gk4) + '<td></td><td></td></tr>')
    return h + '</tbody></table></div>'


def tab_alvo():
    A = T['vwap_alvo']
    h = ('<div class="tab"><table><thead><tr><th>Stop</th><th>Chegou na VWAP antes do stop</th><th>Saiu no fim do pregão</th>'
         '<th>R$/trade</th><th>Treino</th><th>Teste</th></tr></thead><tbody>')
    for s in A['stops']:
        h += (f"<tr><td>{s['stop']}</td><td>{pc(s['hit'], 1)}</td><td>{pc(s['fim_dia'], 1)}</td>"
              f"<td>{ev(s['ev']) if s['ev'] is not None else '-'}</td><td>{ev(s['ev_is']) if s['ev_is'] is not None else '-'}</td>"
              f"<td>{ev(s['ev_oos']) if s['ev_oos'] is not None else '-'}</td></tr>")
    return h + '</tbody></table></div>'


def tab_grade(gk):
    G = T['robustez']['grade']
    pavs = []
    for r in G:
        if r['pav'] not in pavs:
            pavs.append(r['pav'])
    h = ('<div class="tab"><table><thead><tr><th>Empurrão mínimo \\ pavio do candle de virada</th>'
         + ''.join(f'<th>{txt(p)}</th>' for p in pavs) + '</tr></thead><tbody>')
    for ne in (3, 4, 5, 6):
        h += f'<tr><td><b>{ne}+ candles</b></td>'
        for p in pavs:
            r = next(x for x in G if x['n_emp'] == ne and x['pav'] == p)
            dest = ' style="outline:2px solid var(--azul);outline-offset:-2px"' if (ne == 4 and 'regra' in p) else ''
            h += (f"<td{dest}><b>{ev(r[gk]['ev'])}</b><br><span class=\"nota\">teste {rs(r[gk]['ev_oos'], 1)} · "
                  f"{n(r['n'])} sinais</span></td>")
        h += '</tr>'
    return h + '</tbody></table></div>'


def tab_stops():
    h = ('<div class="tab"><table><thead><tr><th>Stop</th><th>Alvo</th><th>R$/sinal</th><th>Treino</th><th>Teste</th>'
         '<th>Carteira</th><th>Fator</th><th>Rebaixamento</th></tr></thead><tbody>')
    for r in T['robustez']['stops']:
        h += (f"<tr class=\"{'dest' if r['stop'] == '100' and r['alvo'] == '300' else ''}\"><td>{r['stop']}</td><td>{r['alvo']}</td>"
              f"<td><b>{ev(r['ev'])}</b></td><td>{ev(r['ev_is'])}</td><td>{ev(r['ev_oos'])}</td>"
              f"<td>{ev(r['liq'], 0)}</td><td>{n(r['fl'], 2)}</td><td>{rs(-r['dd'])}</td></tr>")
    return h + '</tbody></table></div>'


def tab_boot():
    h = ('<div class="tab"><table><thead><tr><th>Saída</th><th>Chance de terminar no prejuízo</th><th>Pior 5%</th>'
         '<th>Mediana</th><th>Melhor 5%</th></tr></thead><tbody>')
    for gk, r in GS:
        b = T['robustez']['bootstrap'][gk]
        h += (f"<tr><td>{r}</td><td>{pc(b['p_prejuizo'], 1)}</td><td>{ev(b['p5'], 0)}</td><td>{ev(b['p50'], 0)}</td>"
              f"<td>{ev(b['p95'], 0)}</td></tr>")
    return h + '</tbody></table></div>'


# textos sem acento que vem do estudo -> com acento
TRAD = [('1o/2o', '1º/2º'), ('1o ou 2o', '1º ou 2º'), ('so 1o', 'só 1o'), ('so o empurrao', 'só o empurrão'), ('so a banda', 'só a banda'),
        ('1a ', '1ª '), ('Padrao', 'Padrão'), ('padrao', 'padrão'), ('Distancia', 'Distância'), ('confirmacao', 'confirmação'), ('Exaustao', 'Exaustão'), ('exaustao', 'exaustão'), ('rejeicao', 'rejeição'), ('Angulo', 'Ângulo'),
        ('angulo', 'ângulo'), ('Numero', 'Número'), ('Distancia', 'Distância'), ('Horario', 'Horário'),
        ('nao ', 'não '), ('sinal do dia', 'sinal do dia'), ('Padrao', 'Padrão'), ('padrao', 'padrão'),
        ('empurrao', 'empurrão'), ('Empurrao', 'Empurrão'), ('virada simples', 'virada simples'),
        ('1o ', '1º '), ('2o ', '2º '), ('3o ', '3º '), ('4o ', '4º '), ('5o ', '5º '), ('6o ', '6º '),
        ('16o ', '16º '), ('15o', '15º'), ('ultimos', 'últimos'), ('alcancada', 'alcançada'),
        ('prioridade', 'prioridade'), ('classificacao', 'classificação'), ('ja ', 'já '), ('regra', 'regra'),
        ('ate a', 'até a'), ('ate ', 'até '), ('pts por candle', 'pts por candle'), ('Hull vira', 'Hull vira'),
        ('desvios', 'desvios'), ('quintis', 'quintis'), (' E ', ' e ')]


def txt(s):
    for a, b in TRAD:
        s = s.replace(a, b)
    return s


def trad_lin(lin):
    return [dict(l, faixa=txt(l['faixa'])) for l in lin]


def bloco_faixa(chave, fonte='faixas', rot=None):
    F = T[fonte][chave]
    return (f'<h3>{txt(rot or F["rot"])}</h3>'
            + por_gestao(lambda gk: tab_faixa(trad_lin(F['lin']), gk)))


# ------------------------------------------------------------------ corpo
def corpo():
    c0 = {g: cart('c1: todos', g) for g, _ in GS}
    cE = {g: cart('c1: exaustao limpa (', g) for g, _ in GS}
    cET = {g: cart('c1: exaustao limpa E 1o/2o', g) for g, _ in GS}
    cR = {g: cart('c1: sem pavio', g) for g, _ in GS}
    hE = hip('Exaustao limpa (', 'r300'); hR = hip('Pavio de rejeicao', 'r300'); hD = hip('Topo/fundo duplo', 'r300')
    hF = hip('Falso rompimento', 'r300'); hT1 = hip('1o toque na banda 1', 'r300'); hET = hip('Exaustao limpa E 1o/2o', 'r300')
    hEx = hip('Exaustao: empurrao', 'r300'); hE2 = hip('Exaustao limpa E banda 2+', 'r300')
    cE2 = {g: cart('c1: exaustao limpa E banda 2 ou 3', g) for g, _ in GS}
    ET1 = fx('toque1', '1o toque', 'faixas_E'); ET2 = fx('toque1', '2o toque', 'faixas_E')
    ET3 = fx('toque1', '3o toque', 'faixas_E'); ET4 = fx('toque1', '4o', 'faixas_E')
    A = T['vwap_alvo']
    b1 = base('c1'); b2 = base('c2'); bh = base('hull')
    vwe = T['vwap_entrada']['c1']['lin'][0]
    ctl = T['controle']
    boot = T['robustez']['bootstrap']
    st = T['robustez']['stops']
    s_ext = next(r for r in st if r['stop'].startswith('extremo') and r['alvo'] == '300')
    s_vw = next(r for r in st if r['stop'] == '100' and r['alvo'] == 'VWAP')
    h = []
    h.append(f'''
<h1>Reversões nas VWAP Bands</h1>
<p class="sub">WINFUT, gráfico PI 20 · {n(M['pregoes'])} pregões ({M['inicio'][8:]}/{M['inicio'][5:7]} a {M['fim'][8:]}/{M['fim'][5:7]}/{M['fim'][:4]}) ·
VWAP e bandas conferidas contra o Profit · 6 contratos, R$ 0,50 por contrato · treino até {M['corte'][8:]}/{M['corte'][5:7]}, teste depois</p>

<h2 id="resposta">Resposta</h2>
<div class="kpis">
<div class="kpi"><div class="r">Sinais de reversão (1º candle contra)</div><div class="v">{n(b1['n'])}</div></div>
<div class="kpi"><div class="r">Todos, alvo 300</div><div class="v {cls(b1['g']['r300']['ev'])}">{rs(b1['g']['r300']['ev'], 1)}<span class="nota"> /trade</span></div></div>
<div class="kpi"><div class="r">Exaustão limpa, alvo 300</div><div class="v {cls(hE['ev'])}">{rs(hE['ev'], 1)}<span class="nota"> /trade</span></div></div>
<div class="kpi"><div class="r">Exaustão limpa, carteira alvo 300</div><div class="v {cls(cE['r300']['stats']['liquido'])}">{rs(cE['r300']['stats']['liquido'])}</div></div>
<div class="kpi"><div class="r">Chegam na VWAP antes do stop 100</div><div class="v">{n(A['stops'][0]['hit'], 0)}%</div></div>
</div>
<div class="card ok"><b>Quais padrões de reversão funcionam.</b> Reverter na banda "sempre que virar" só empata: os {n(b1['n'])} sinais
do primeiro candle contra dão {rs(b1['g']['r300']['ev'], 1)} por trade com alvo 300 (treino {rs(b1['g']['r300']['ev_is'], 1)}, teste {rs(b1['g']['r300']['ev_oos'], 1)}).
É melhor que entrar ao acaso ({rs(T['aleatorio']['r300'], 1)} com a mesma gestão), mas não paga mais que o custo; esperar o segundo candle
({rs(b2['g']['r300']['ev'], 1)}) ou a virada da Hull ({rs(bh['g']['r300']['ev'], 1)}) piora. O padrão que se sustenta é a <b>exaustão limpa</b>: o preço
chega na banda com <b>4 ou mais candles seguidos</b> e vira num candle <b>sem pavio de rejeição</b> (o candle contra não fez nova máxima de mais de 30 pontos).
São {n(hE['n'])} sinais ({n(hE['frac'] * 100, 0)}%), {rs(hE['ev'], 1)} por trade, treino {rs(hE['ev_is'], 1)} e teste {rs(hE['ev_oos'], 1)}, positivo nos três terços
e em média positivo nas quatro saídas. <b>Na banda 2 ou além ela fica mais forte</b>: {n(hE2['n'])} sinais, {rs(hE2['ev'], 1)} por trade, positiva nos três terços,
e na carteira positiva nas quatro saídas, no treino e no teste (fator {n(cE2['r300']['stats']['fator_lucro'], 2)} com alvo 300,
{n(cE2['claude']['stats']['fator_lucro'], 2)} com a gestão do CLAUDE.md). O <b>pavio de rejeição grande piora</b> ({rs(hR['ev'], 1)} contra
{rs(hR['resto'], 1)} sem ele), assim como o <b>topo/fundo duplo</b> ({rs(hD['ev'], 1)}); o falso rompimento (fechou fora e voltou) também fica abaixo
({rs(hF['ev'], 1)}). A exaustão sozinha, sem olhar o pavio, quase não ajuda ({rs(hEx['ev'], 1)}).</div>
<div class="card alerta"><b>Os primeiros toques ajudam pouco.</b> O 1º toque do dia na banda 1 rende {rs(hT1['ev'], 1)} por trade contra {rs(hT1['resto'], 1)}
dos demais, mas fica negativo no último terço do período. Com as bandas em envelope, os toques são raros: na exaustão limpa, 1º e 2º toque somam
{n(hET['n'])} dos {n(hE['n'])} sinais ({rs(ET1['r300']['ev'], 1)} no 1º, {rs(ET2['r300']['ev'], 1)} no 2º), e do 3º em diante sobram poucos casos. O número do
toque, sozinho, não separa bons e maus trades. Com uma entrada só por toque, veja o estudo <code>toque.html</code>.</div>
<div class="card alerta"><b>O ângulo da VWAP não separa bons e maus sinais.</b> Em pontos por candle (10 e 20 candles) ou em passos de banda, as faixas sobem e descem
sem ordem e trocam de sinal entre treino e teste. Quase todo sinal nas bandas é contra a inclinação da VWAP (o preço só chega na banda de cima
quando a VWAP está subindo), então "VWAP a favor" praticamente não acontece ({n(hip('VWAP a favor', 'r300')['n'])} sinais). Sozinho, nenhum corte de ângulo virou filtro. A única combinação que se repetiu foi
exaustão limpa com VWAP plana (≥ −2 pts/candle): {rs(hip('Exaustao limpa E VWAP plana', 'r300')['ev'], 1)} por trade em {n(hip('Exaustao limpa E VWAP plana', 'r300')['n'])} sinais,
positiva nos três terços. É candidata a confirmar, não regra.</div>
<div class="card ruim"><b>A VWAP não é boa entrada, e é um alvo fraco.</b> Repique na própria VWAP (o preço volta até ela e vira) dá {rs(vwe['r300']['ev'], 1)} por trade
com alvo 300 e negativo em quase todas as saídas e recortes, inclusive o pullback depois de o preço ter ido à banda. Como alvo, a VWAP fica longe: mediana de
{n(A['dist_q'][2])} pontos da entrada, e só {n(A['stops'][0]['hit'], 0)}% dos trades chegam nela antes de um stop de 100 ({n(A['p_vwap_sem_stop'], 0)}% sem stop nenhum, no mesmo pregão).
No conjunto todo, alvo na VWAP ({rs(b1['g']['vw']['ev'], 1)}) perde para o alvo 300 ({rs(b1['g']['r300']['ev'], 1)}).</div>
<div class="card"><b>300 ou 500 seco.</b> Alvo 300 ganha do 500 em quase todos os recortes: com stop de 100, só {n(A['p_mfe']['500'], 0)}% dos sinais andam 500 pontos a favor
antes do stop, contra {n(A['p_mfe']['300'], 0)}% que andam 300. Na exaustão limpa: alvo 300 {rs(cE['r300']['stats']['liquido'])} na carteira, alvo 500
{rs(cE['r500']['stats']['liquido'])}, alvo VWAP {rs(cE['vw']['stats']['liquido'])}, e a gestão do CLAUDE.md {rs(cE['claude']['stats']['liquido'])}, com o menor rebaixamento
({rs(-cE['claude']['stats']['dd_max'])}) e {n(boot['claude']['p_prejuizo'], 1)}% de chance de prejuízo no sorteio de dias.</div>
''')

    h.append(f'''
<h2 id="medidas">Como foi medido</h2>
<div class="card">
<p><b>VWAP Band do Profit</b> (período Diário, preço típico "Média financeira"). <b>VWAP</b> do pregão, zerada todo dia: o preço de cada candle
é o preço médio negociado (volume financeiro ÷ quantidade ÷ 0,20), ponderado pela quantidade de contratos. <b>Bandas</b>: envelopes percentuais da VWAP,
a <b>1/3 %, 2/3 % e 1 %</b> acima e abaixo (o artigo da Nelogica arredonda para 0,33 / 0,66 / 0,99 %); no WIN a 187.000, cerca de 625, 1.250 e 1.875 pontos.
Conferido com o artigo (WDO, VWAP 5.013,59 e bandas 5.030,30 / 5.047,01 / 5.063,73) e com o Profit em 16/09 às 15:00 (VWAP 187.746, +1 188.371,
−1 187.120, iguais aqui). O valor do candle inclui o próprio candle, como no gráfico. Sinais e toques desde a abertura. Passo mediano entre bandas:
{n(M['sd_med'])} pontos.</p>
<p><b>Gatilhos</b> (venda na banda de cima; compra é o espelho), sempre no fechamento: <b>1º candle contra</b> (candle de baixa logo depois de um ou mais de alta),
<b>2º candle contra</b> (dois de baixa) e <b>Hull 50 vira</b>. O movimento até a banda é o <b>empurrão</b>: os candles de alta seguidos antes da virada. O extremo do
movimento precisa ter chegado pelo menos à banda 1.</p>
<p><b>Padrões</b> (medidos em todos os sinais; um sinal pode ter mais de um):</p>
<ul>
<li><b>Exaustão</b>: empurrão de 4 ou mais candles seguidos.</li>
<li><b>Pavio de rejeição</b>: o próprio candle contra fez o extremo do movimento, com pavio de 30 pontos ou mais além da abertura (subiu, rejeitou e fechou em baixa).</li>
<li><b>Exaustão limpa</b>: exaustão sem pavio de rejeição. A virada é imediata: o preço não voltou a testar a máxima antes de cair.</li>
<li><b>Falso rompimento</b>: algum candle do empurrão fechou fora da banda e o candle contra fechou de volta dentro.</li>
<li><b>Topo/fundo duplo</b>: outro sinal no mesmo lado 5 a 40 candles antes, recuo de 200+ pontos entre os dois, e o extremo atual entre 100 pontos abaixo e 30 acima do anterior.</li>
</ul>
<p><b>Toques</b>: um episódio de toque na banda começa quando o preço chega nela e só termina quando o preço volta até a banda de dentro (para a banda 1, até a própria VWAP).
Encostar, afastar 50 pontos e encostar de novo continua sendo o mesmo toque. Contado por lado e por pregão.</p>
<p><b>Ângulo da VWAP</b>: variação da VWAP nos últimos {M['ang_n']} (e 20) candles, em pontos por candle, com o sinal do lado do trade: negativo = VWAP andando contra
o trade (subindo, numa venda). Também em passos de banda (1/3 % da VWAP).</p>
<p><b>Saídas</b>, todas com stop de 100 a partir da entrada, no fechamento do candle do gatilho: <b>alvo 300 seco</b>, <b>alvo 500 seco</b>, <b>alvo na VWAP</b>
(ordem limitada na VWAP do candle anterior, reposicionada a cada candle) e a <b>gestão do CLAUDE.md</b> (parcial de 50% em +100, stop do resto na média, alvo 300).
Zeragem no fim do pregão. Dentro do candle o preço percorre primeiro o pavio contra. A carteira abre uma posição por vez: sinal com trade aberto é ignorado.</p>
</div>
<div class="leg"><span>Seletor de saída das tabelas:</span></div>
<div class="abas" id="gsel">''' + ''.join(f'<button data-g="{gk}" class="{"on" if gk == "r300" else ""}">{r}</button>' for gk, r in GS) + '</div>')

    h.append(f'''
<h2 id="base">Base: reverter em qualquer virada na banda</h2>
<p>Cada sinal isolado (sem a restrição de uma posição por vez), em R$ por trade com 6 contratos e custo incluído.</p>
{tab_base()}
<p class="nota">O custo sozinho é R$ 3,00 por trade; a entrada aleatória fica em −R$ 5 a −R$ 7. O 1º candle contra na banda fica no zero: acima do acaso,
sem lucro. O 2º candle contra fica perto do acaso e a virada da Hull abaixo dele. E o controle mais abaixo mostra que o 1º candle contra rende o mesmo
dentro e fora das bandas.</p>''')

    h.append(f'''
<h2 id="padroes">Padrões de reversão</h2>
<p>Cada padrão contra o resto dos sinais do 1º candle contra. Ordenado pela diferença.</p>
{por_gestao(tab_hip)}
{bloco_faixa('padrao')}
<p class="nota">Na classificação exclusiva cada sinal fica num padrão só, na ordem falso rompimento, duplo, rejeição, exaustão, simples. A "exaustão" aqui já sai
sem os que tiveram rejeição, duplo ou falso rompimento; por isso é mais forte que a exaustão da tabela de cima.</p>
{bloco_faixa('pav')}
{bloco_faixa('emp')}
<div class="card">No pavio, só o grande separa: acima de 50 pontos de pavio no candle de virada o resultado é negativo em todas as saídas; abaixo disso
as faixas não seguem ordem. No gráfico PI todo candle tem corpo de 100; um pavio grande no candle
contra quer dizer que o preço ainda foi buscar nova máxima e só então virou.</div>''')

    h.append(f'''
<h2 id="banda">A banda importa?</h2>
<p>Controle: os mesmos gatilhos (1º candle contra), <b>em qualquer lugar do gráfico</b>, separados pela distância do extremo até a VWAP, em bandas (1 = chegou na banda 1).
Abaixo de 0 = o extremo nem passou da VWAP (reversão contra um repique, na verdade a favor da tendência do dia).</p>
<h3>Todos os sinais ({n(ctl['n'])})</h3>
{por_gestao(lambda gk: tab_faixa(ctl['todos'], gk, 'Extremo, em bandas da VWAP'))}
<h3>Só exaustão limpa</h3>
{por_gestao(lambda gk: tab_faixa(ctl['exaust'], gk, 'Extremo, em bandas da VWAP'))}
''')
    xz = ctl['exaust']
    h.append(f'''<div class="card alerta">Sem filtro, tocar a banda dá o mesmo que não tocar: o 1º candle contra rende perto de zero em todas as faixas. Com a exaustão limpa,
a banda 1 não ajuda: entre as bandas 1 e 2 rende {rs(xz[2]['r300']['ev'], 1)}, menos que longe das bandas ({rs(xz[0]['r300']['ev'], 1)} com o extremo abaixo da VWAP,
{rs(xz[1]['r300']['ev'], 1)} entre a VWAP e a banda 1). Além da banda 2 o resultado sobe ({rs(xz[3]['r300']['ev'], 1)}). A parte que a VWAP Band acrescenta é
essa: exaustão que vai até a banda 2 ou além.</div>
{bloco_faixa('nivel')}''')

    h.append(f'''
<h2 id="toques">Primeiros toques</h2>
{bloco_faixa('toque1')}
{bloco_faixa('toque')}
{bloco_faixa('nsinal')}
<h3>Dentro da exaustão limpa</h3>
{bloco_faixa('toque1', 'faixas_E', 'Exaustão limpa: número do toque na banda 1')}
<div class="card alerta">Contando todo sinal dentro de cada toque, o número do toque ordena pouco: o 1º toque na banda 1 fica acima do resto, mas negativo no
último terço. Com a banda a 1/3 % da VWAP, o 3º toque em diante é raro. A pergunta "só o 1º ou 2º toque, uma entrada por toque" está no estudo
<code>toque.html</code>.</div>''')

    h.append(f'''
<h2 id="angulo">Ângulo da VWAP</h2>
{bloco_faixa('ang')}
{bloco_faixa('ang20')}
{bloco_faixa('ang_sd')}
{bloco_faixa('ang', 'faixas_E', 'Exaustão limpa: ângulo da VWAP (pts por candle, 10 candles)')}
<div class="card alerta">Não há ordem: a faixa −8 a −4 é a melhor no conjunto todo e a pior dentro da exaustão limpa. Em passos de banda o quadro também é
serrilhado. VWAP inclinada a favor do trade quase não existe num sinal de reversão na banda ({n(hip('VWAP a favor', 'r300')['n'])} casos). Sozinho, o ângulo não virou regra. Dentro
da exaustão limpa, VWAP plana foi a melhor faixa nos três terços e −8 a −4 a pior: combinação candidata, a confirmar com mais histórico.</div>''')

    ve = T['vwap_entrada']
    h.append(f'''
<h2 id="vwap">VWAP: ponto de entrada ou só de saída?</h2>
<h3>Como entrada: repique na própria VWAP</h3>
<p>O preço vem de fora, encosta na VWAP (sem chegar na banda 1 do outro lado) e vira: compra quando vem de cima, venda quando vem de baixo. Mesmos gatilhos e padrões.
Como alvo, além de 300 e 500, a banda 1 a favor (a VWAP como entrada e a banda como saída).</p>
<h3>1º candle contra ({n(ve['c1']['n'])} sinais)</h3>{tab_vwe('c1')}
<h3>2º candle contra ({n(ve['c2']['n'])} sinais)</h3>{tab_vwe('c2')}
<div class="card ruim">Negativo na média e em quase todos os recortes. O pullback clássico (o preço já foi à banda a favor e volta na VWAP) é pior que a média:
{rs(ve['c1']['lin'][1]['r300']['ev'], 1)} por trade. VWAP contra o trade também é ruim. O único recorte positivo é o 1º sinal do dia naquele lado
({rs(ve['c1']['lin'][10]['r300']['ev'], 1)} no 1º candle contra, {rs(ve['c2']['lin'][10]['r300']['ev'], 1)} no 2º), com cerca de 260 sinais e resultado que oscila
entre os terços. A VWAP não se mostrou ponto de entrada neste histórico.</div>
<h3>Como alvo: quanto o preço anda depois da reversão na banda</h3>
{tab_alvo()}
<div class="card">Distância da entrada até a VWAP: mediana {n(A['dist_q'][2])} pontos (metade dos sinais entre {n(A['dist_q'][1])} e {n(A['dist_q'][3])}).
Com stop de 100, {n(A['p_mfe']['100'], 0)}% dos sinais andam 100 a favor, {n(A['p_mfe']['300'], 0)}% andam 300, {n(A['p_mfe']['500'], 0)}% andam 500 e só {n(A['p_vwap'], 0)}% alcançam a VWAP.
Sem stop, {n(A['p_vwap_sem_stop'], 0)}% chegam nela no mesmo pregão, mas no meio do caminho metade vai {n(-A['mae_sem_stop'][0])} pontos contra. Stop maior
para dar espaço até a VWAP piora o resultado em todos os tamanhos testados. A VWAP funciona como referência de destino, mas é longe demais para ser o alvo de
uma reversão com stop curto; o alvo fixo de 300 captura a parte do movimento que de fato acontece.</div>
<h3>Resultado pela distância até a VWAP</h3>
{por_gestao(lambda gk: tab_faixa(trad_lin(A['por_dist']), gk, 'Distância até a VWAP (pts)'))}
<p class="nota">O alvo na VWAP é negativo em todas as distâncias, e pior quanto mais longe ela está. O alvo 300 fica perto de zero em todas.</p>''')

    h.append(f'''
<h2 id="carteira">Carteira</h2>
<p>Uma posição por vez, 6 contratos, custo de R$ 0,50 por contrato. A última coluna refaz tudo exigindo que o alvo (e a parcial) seja atravessado em 5 pontos
para executar, que é o jeito conservador de tratar a ordem limitada.</p>
{por_gestao(lambda gk: tab_cart(gk, 'eq_' + gk))}
<div class="card">"Sem pavio de rejeição" (a parte mais ampla da regra) melhora a base, mas perde no teste. A exaustão limpa rende mais que ela, com um quarto
dos trades e rebaixamento menor: o fator de lucro sobe de {n(c0['r300']['stats']['fator_lucro'], 2)} para {n(cE['r300']['stats']['fator_lucro'], 2)} no alvo 300 e
para {n(cE['claude']['stats']['fator_lucro'], 2)} na gestão do CLAUDE.md. Só na banda 2 ou além: {n(cE2['r300']['stats']['trades'])} trades,
{rs(cE2['r300']['stats']['liquido'])} (alvo 300) e {rs(cE2['claude']['stats']['liquido'])} (CLAUDE.md), rebaixamento de {rs(-cE2['r300']['stats']['dd_max'])} e
{rs(-cE2['claude']['stats']['dd_max'])}. Exigir 5 pontos além do alvo custa pouco nos filtros bons.</div>''')

    h.append(f'''
<h2 id="robustez">Robustez da exaustão limpa</h2>
<h3>Vizinhança da regra</h3>
<p>Mudando o tamanho mínimo do empurrão e o limite de pavio. Em destaque, a regra escolhida. Embaixo de cada R$/trade, o resultado só no teste.</p>
{por_gestao(tab_grade)}
<p class="nota">A regra de 4 candles é o pico da vizinhança: com 3 candles o efeito quase some
({rs(next(r for r in T['robustez']['grade'] if r['n_emp'] == 3 and 'regra' in r['pav'])['r300']['ev'], 1)}, teste
{rs(next(r for r in T['robustez']['grade'] if r['n_emp'] == 3 and 'regra' in r['pav'])['r300']['ev_oos'], 1)}), com 5 fica positivo mas perto de zero no teste,
com 6 ou mais fica negativo no teste. Sem limite de pavio o efeito some em todos os tamanhos. Um pico isolado assim pede cautela com o número.</p>
<h3>Stop e alvo</h3>
{tab_stops()}
<p class="nota">Stop no extremo do movimento + 10 (limitado a 300) fica parecido com o stop fixo de 100 no alvo 300 ({rs(s_ext['ev'], 1)} contra {rs(hE['ev'], 1)}).
Alvo na VWAP ({rs(s_vw['ev'], 1)}) oscila muito entre treino ({rs(s_vw['ev_is'], 1)}) e teste ({rs(s_vw['ev_oos'], 1)}).</p>
<h3>Sorteio de pregões (bootstrap, 4.000 sorteios com reposição)</h3>
{tab_boot()}
<div class="card alerta"><b>Limites.</b> São {M['pregoes']} pregões de um mesmo regime; a exaustão limpa tem {n(hE['n'] / M['pregoes'], 1)} sinais por pregão e, na banda 2 ou além, {n(hE2['n'] / M['pregoes'], 1)}. Foram
testadas 21 hipóteses e várias saídas: o candidato foi escolhido olhando os dados, e o que sustenta a escolha é ter ficado positivo no treino, no teste, nos três
terços e nas quatro saídas, não o tamanho do número. Vale rodar de novo quando houver mais histórico, sem mexer na regra.</div>''')

    h.append('''
<h2 id="kline">Trade a trade</h2>
<p>VWAP (linha cheia) e bandas a 1/3 %, 2/3 % e 1 % da VWAP (tracejadas). Faixa azul: empurrão até a banda e candle de virada. Faixa verde/vermelha: duração do trade.
Setas ← → no teclado navegam.</p>
<div class="card">
<div class="kbar"><select id="kvar"></select><select id="kfiltro"><option value="todos">Todos</option><option value="ganho">Ganhos</option>
<option value="perda">Perdas</option><option value="t12">1º/2º toque</option></select>
<button class="btn" id="kant">&larr;</button><select id="ksel"></select><button class="btn" id="kprox">&rarr;</button></div>
<div class="kinfo" id="kinfo"></div>
<div id="kchart"></div>
</div>''')

    h.append(f'''
<h2 id="conclusao">Conclusão</h2>
<div class="card ok">
<ol>
<li><b>Reverter toda virada na banda não paga o custo.</b> O toque na VWAP Band sozinho não tem vantagem neste histórico, em nenhuma das três bandas.</li>
<li><b>Regra que se sustentou</b> (venda; compra é o espelho): preço chega na banda 1 ou além com <b>4+ candles de alta seguidos</b>; entra vendido no fechamento do
<b>primeiro candle de baixa</b>, desde que esse candle <b>não tenha feito nova máxima com pavio de 30+ pontos</b>. {rs(hE['ev'], 1)} por trade com alvo 300,
{rs(cE['r300']['stats']['liquido'])} na carteira, positivo em treino, teste e nos três terços.</li>
<li><b>Na banda 2 ou além a exaustão limpa fica mais forte</b>: {rs(hE2['ev'], 1)} por trade, positiva nas quatro saídas, no treino e no teste.
São {n(hE2['n'])} sinais: é o candidato mais forte e também o de menor amostra.</li>
<li><b>O número do toque, sozinho, pesa pouco</b> quando se conta todo sinal dentro do toque. Com uma entrada por toque, veja <code>toque.html</code>.</li>
<li><b>Ângulo da VWAP sozinho não ordena</b> os resultados. Exaustão limpa com VWAP plana ({rs(hip('Exaustao limpa E VWAP plana', 'r300')['ev'], 1)} por trade)
fica como candidata.</li>
<li><b>VWAP não é entrada</b> e, com stop de 100, é <b>alvo longe demais</b>. Entre as saídas testadas, <b>alvo 300 seco</b> e a <b>gestão do CLAUDE.md</b> ficam
à frente; o alvo 500 seco perde para o 300 porque só {n(A['p_mfe']['500'], 0)}% dos trades andam 500 antes do stop.</li>
<li>Evitar: segundo candle contra, virada da Hull, pavio de rejeição grande e topo/fundo duplo na banda.</li>
</ol></div>
<p class="nota">Arquivos: vbase.py (VWAP, bandas, sinais, simulação), vwap_estudo.py (estudo → saida/vwap.json), vwap_rel.py (este relatório e VWAP.md).</p>''')
    return '\n'.join(h)


# ------------------------------------------------------------------ candles
def candles():
    d = V.carrega()
    r0 = lambda x: [None if (v is None or np.isnan(v)) else int(round(v)) for v in x]
    fr = d['frio'].to_numpy()
    band = lambda col: r0(np.where(fr, np.nan, d[col].to_numpy()))
    return dict(o=r0(d['o']), h=r0(d['h']), l=r0(d['l']), c=r0(d['c']), vw=r0(d['vwap']),
                u1=band('up1'), u2=band('up2'), u3=band('up3'), d1=band('dn1'), d2=band('dn2'), d3=band('dn3'),
                dt=d['data'].dt.strftime('%d/%m/%y %H:%M').tolist())


CSS_EXTRA = r"""
:root{--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--s4:#eda100;--vw:#c48a00;--bd:#8b95a3}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--vw:#e0ad2e;--bd:#6d7682}}
:root[data-theme="dark"]{--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--vw:#e0ad2e;--bd:#6d7682}
th.sec,td.sec{color:var(--mudo);font-size:12px}
#gsel{position:sticky;top:44px;z-index:4;background:var(--fundo);padding:6px 0}
.tip{position:absolute;pointer-events:none;background:var(--card);border:1px solid var(--linha);border-radius:8px;padding:6px 9px;font-size:12px;
color:var(--tinta2);box-shadow:0 2px 8px rgba(0,0,0,.12);white-space:nowrap;z-index:3}
.graf{position:relative}
@media (max-width:600px){.wrap{padding-inline:16px}}
"""

JS = r"""
const TRD=__TRADES__, C=__CANDLES__, EQ=__EQ__, DIAS=__DIAS__;
const $=s=>document.querySelector(s);
const cv=k=>getComputedStyle(document.documentElement).getPropertyValue('--'+k).trim();
const fmt=(v,c=0)=>v==null?'-':(v<0?'−':'')+Math.abs(v).toLocaleString('pt-BR',{minimumFractionDigits:c,maximumFractionDigits:c});
const rs=(v,c=0)=>v==null?'-':(v>0?'+':v<0?'−':'')+'R$ '+fmt(Math.abs(v),c);
const cls=v=>v>0?'pos':v<0?'neg':'mudo';
const sn=(v,c=0)=>(v>0?'+':'')+fmt(v,c);
function alfa(c,a){const x=document.createElement('canvas').getContext('2d');x.fillStyle=c;const h=x.fillStyle;
  if(h[0]==='#'){const r=parseInt(h.slice(1,3),16),g=parseInt(h.slice(3,5),16),b=parseInt(h.slice(5,7),16);return `rgba(${r},${g},${b},${a})`;}return h;}

/* ------------------------------------------------ seletor de saida */
let GK='r300';
const fixaSel=()=>{$('#gsel').style.top=(document.querySelector('nav.indice').offsetHeight)+'px';}; fixaSel();
document.querySelectorAll('#gsel button').forEach(b=>b.addEventListener('click',()=>{GK=b.dataset.g;
  document.querySelectorAll('#gsel button').forEach(x=>x.classList.toggle('on',x===b));
  document.querySelectorAll('.gest').forEach(x=>x.hidden=x.dataset.g!==GK); desenhaEq();}));

/* ------------------------------------------------ curvas de patrimonio */
function linhas(el,series){
  const W=el.clientWidth||900,H=300,m={l:64,r:14,t:12,b:26};
  const N=DIAS.length; let lo=0,hi=0; series.forEach(s=>s.y.forEach(v=>{lo=Math.min(lo,v);hi=Math.max(hi,v);}));
  const pad=(hi-lo)*.06||1; lo-=pad; hi+=pad;
  const X=i=>m.l+(W-m.l-m.r)*i/(N-1), Y=v=>m.t+(H-m.t-m.b)*(1-(v-lo)/(hi-lo));
  const passo=Math.pow(10,Math.floor(Math.log10((hi-lo)/4))); const st=[1,2,5,10].map(k=>k*passo).find(k=>(hi-lo)/k<=6);
  let s=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Curvas de patrimônio">`;
  for(let v=Math.ceil(lo/st)*st;v<=hi;v+=st){s+=`<line x1="${m.l}" x2="${W-m.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="${v===0?cv('eixo'):cv('grade')}" stroke-width="1"/>`+
    `<text x="${m.l-8}" y="${Y(v)+4}" text-anchor="end" font-size="11" fill="${cv('mudo')}">${fmt(v)}</text>`;}
  const nt=Math.min(8,Math.floor((W-m.l-m.r)/80));
  for(let k=0;k<=nt;k++){const i=Math.round((N-1)*k/nt);s+=`<text x="${X(i)}" y="${H-8}" text-anchor="middle" font-size="11" fill="${cv('mudo')}">${DIAS[i].slice(8,10)}/${DIAS[i].slice(5,7)}</text>`;}
  series.forEach(se=>{s+=`<path d="${se.y.map((v,i)=>(i?'L':'M')+X(i).toFixed(1)+' '+Y(v).toFixed(1)).join('')}" fill="none" stroke="${se.cor}" stroke-width="${se.larg||2}" stroke-linejoin="round"/>`;});
  s+=`<line id="xh" x1="0" x2="0" y1="${m.t}" y2="${H-m.b}" stroke="${cv('mudo')}" stroke-dasharray="3 3" visibility="hidden"/>`;
  s+=series.map((se,k)=>`<circle class="pt" data-k="${k}" r="4.5" fill="${se.cor}" stroke="${cv('card')}" stroke-width="2" visibility="hidden"/>`).join('');
  s+=`<rect x="${m.l}" y="${m.t}" width="${W-m.l-m.r}" height="${H-m.t-m.b}" fill="transparent"/></svg><div class="tip" hidden></div>`;
  el.innerHTML=s;
  const svg=el.querySelector('svg'), tip=el.querySelector('.tip'), xh=el.querySelector('#xh');
  svg.addEventListener('mousemove',ev=>{const r=svg.getBoundingClientRect(), x=(ev.clientX-r.left)*W/r.width;
    const i=Math.max(0,Math.min(N-1,Math.round((x-m.l)/(W-m.l-m.r)*(N-1))));
    xh.setAttribute('x1',X(i));xh.setAttribute('x2',X(i));xh.setAttribute('visibility','visible');
    el.querySelectorAll('.pt').forEach(p=>{const se=series[+p.dataset.k];p.setAttribute('cx',X(i));p.setAttribute('cy',Y(se.y[i]));p.setAttribute('visibility','visible');});
    tip.hidden=false; tip.innerHTML=`<b>${DIAS[i].slice(8,10)}/${DIAS[i].slice(5,7)}/${DIAS[i].slice(0,4)}</b><br>`+
      series.map(se=>`<i style="display:inline-block;width:10px;height:3px;background:${se.cor};margin-right:5px;vertical-align:middle"></i>${se.nome}: <b>${rs(se.y[i])}</b>`).join('<br>');
    const px=X(i)*r.width/W; tip.style.left=(px>r.width*.6?px-tip.offsetWidth-12:px+12)+'px'; tip.style.top='8px';});
  svg.addEventListener('mouseleave',()=>{tip.hidden=true;xh.setAttribute('visibility','hidden');el.querySelectorAll('.pt').forEach(p=>p.setAttribute('visibility','hidden'));});
}
function desenhaEq(){
  const el=$('#eq_'+GK); if(!el||!el.offsetParent) return;
  const cores=['s1','s2','s3','s4'].map(cv);
  const se=EQ[GK].map((s,k)=>({nome:s.nome,y:s.y,cor:cores[k],larg:k===2?2.6:2}));
  linhas(el,se);
  $('#eq_'+GK+'_leg').innerHTML=se.map(s=>`<span><i style="background:${s.cor}"></i>${s.nome} <b>${rs(s.y[s.y.length-1])}</b></span>`).join('');
}

/* ------------------------------------------------ kline */
const SANS='Inter,system-ui,-apple-system,"Segoe UI",sans-serif';
const T0=Date.UTC(2000,0,1), TB=60000;
let kchart=null, KL=[], KTR=[], kidx=0, kVar=Object.keys(TRD)[0];
klinecharts.registerIndicator({name:'VWAPB',shortName:'VWAP',series:'price',precision:0,
  figures:[{key:'u3',title:'+3: ',type:'line'},{key:'u2',title:'+2: ',type:'line'},{key:'u1',title:'+1: ',type:'line'},
    {key:'vw',title:'VWAP: ',type:'line'},{key:'d1',title:'−1: ',type:'line'},{key:'d2',title:'−2: ',type:'line'},{key:'d3',title:'−3: ',type:'line'}],
  calc:dl=>dl.map(k=>({u3:k.u3,u2:k.u2,u1:k.u1,vw:k.vw,d1:k.d1,d2:k.d2,d3:k.d3}))});
klinecharts.registerOverlay({name:'marca',totalStep:2,lock:true,needDefaultPointFigure:false,needDefaultXAxisFigure:false,needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates})=>{const e=overlay.extendData,x=coordinates[0].x,y=coordinates[0].y;
    return [{type:'circle',ignoreEvent:true,attrs:{x:x,y:y,r:4.5},styles:{style:'stroke_fill',color:cv('card'),borderColor:e.cor,borderSize:2}},
      {type:'text',ignoreEvent:true,attrs:{x:x+8,y:y,text:e.rot,align:'left',baseline:'middle'},
       styles:{color:cv('card'),size:11,family:SANS,weight:'600',backgroundColor:e.cor,paddingLeft:4,paddingRight:4,paddingTop:2,paddingBottom:2,borderRadius:3}}];}});
klinecharts.registerOverlay({name:'nivel',totalStep:3,lock:true,needDefaultPointFigure:false,needDefaultXAxisFigure:false,needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates})=>{if(coordinates.length<2) return []; const e=overlay.extendData;
    const y=coordinates[0].y,a=coordinates[0].x,b=coordinates[1].x;
    return [{type:'line',ignoreEvent:true,attrs:{coordinates:[{x:a,y:y},{x:b,y:y}]},styles:{color:e.cor,size:1.5,style:e.tr?'dashed':'solid',dashedValue:[4,3]}},
      {type:'text',ignoreEvent:true,attrs:{x:b+4,y:y,text:e.rot,align:'left',baseline:'middle'},styles:{color:e.cor,size:10,family:SANS,weight:'600',backgroundColor:'transparent'}}];}});
klinecharts.registerOverlay({name:'zona',totalStep:3,lock:true,needDefaultPointFigure:false,needDefaultXAxisFigure:false,needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates,bounding})=>{if(coordinates.length<2) return [];const e=overlay.extendData;
    const a=Math.min(coordinates[0].x,coordinates[1].x)-e.meia,b=Math.max(coordinates[0].x,coordinates[1].x)+e.meia;
    return [{type:'rect',ignoreEvent:true,attrs:{x:a,y:0,width:Math.max(2,b-a),height:bounding.height},styles:{style:'fill',color:e.cor}}];}});
function estiloK(){const g=cv('grade'),m=cv('mudo');
  const lin=(c,tr,s)=>({color:c,size:s||1,style:tr?'dashed':'solid',dashedValue:[4,3],smooth:false});
  return {grid:{horizontal:{color:g},vertical:{color:g}},
    candle:{bar:{upColor:cv('card'),downColor:cv('prata'),noChangeColor:m,upBorderColor:cv('tinta2'),downBorderColor:cv('tinta2'),
      noChangeBorderColor:m,upWickColor:cv('tinta2'),downWickColor:cv('tinta2'),noChangeWickColor:m},priceMark:{last:{show:false},high:{show:false},low:{show:false}},
      tooltip:{showRule:'follow_cross',text:{color:cv('tinta'),family:SANS,size:11}}},
    indicator:{lines:[lin(cv('bd'),1),lin(cv('bd'),1),lin(cv('bd'),1),lin(cv('vw'),0,2),lin(cv('bd'),1),lin(cv('bd'),1),lin(cv('bd'),1)],
      tooltip:{showRule:'follow_cross',showName:false,showParams:false,text:{color:cv('tinta2'),family:SANS,size:11}}},
    xAxis:{axisLine:{color:cv('eixo')},tickText:{color:m,family:SANS,size:11}},
    yAxis:{axisLine:{color:cv('eixo')},tickText:{color:m,family:SANS,size:11}},
    separator:{color:cv('linha')},
    crosshair:{horizontal:{line:{color:m},text:{backgroundColor:cv('tinta2')}},vertical:{line:{color:m},text:{backgroundColor:cv('tinta2')}}}};}
function iniciaK(){
  const N=C.o.length;
  for(let i=0;i<N;i++) KL.push({timestamp:T0+i*TB,open:C.o[i],high:C.h[i],low:C.l[i],close:C.c[i],volume:0,
    vw:C.vw[i],u1:C.u1[i],u2:C.u2[i],u3:C.u3[i],d1:C.d1[i],d2:C.d2[i],d3:C.d3[i]});
  kchart=klinecharts.init('kchart',{styles:estiloK(),customApi:{formatDate:(f,ts,fm,tipo)=>{const i=Math.round((ts-T0)/TB);
    const s=(i>=0&&i<N)?C.dt[i]:''; return tipo===2?s.slice(9):s;}}});
  kchart.setPriceVolumePrecision(0,0);
  kchart.createIndicator('VWAPB',true,{id:'candle_pane'});
  kchart.applyNewData(KL);
  $('#kvar').innerHTML=Object.entries(TRD).map(([k,v])=>`<option value="${k}">${v.nome} (${v.trades.length})</option>`).join('');
  listaK(); mostraK(0);
}
function listaK(){
  const ft=$('#kfiltro').value;
  KTR=TRD[kVar].trades.filter(t=>ft==='todos'||(ft==='ganho'&&t.rs>0)||(ft==='perda'&&t.rs<0)||(ft==='t12'&&t.toque>=1&&t.toque<=2));
  $('#ksel').innerHTML=KTR.map((t,i)=>`<option value="${i}">#${i+1} · ${t.data} · ${t.lado>0?'compra':'venda'} · ${rs(t.rs)}</option>`).join('');
}
function mostraK(i){
  if(!kchart||!KTR.length){$('#kinfo').innerHTML='<span>Nenhum trade neste filtro.</span>';return;}
  kidx=Math.max(0,Math.min(KTR.length-1,i)); const t=KTR[kidx], ld=t.lado, V=TRD[kVar];
  kchart.removeOverlay();
  let de=Math.max(0,t.v0-40); while(de<t.v0&&C.dt[de].slice(0,8)!==C.dt[t.v0].slice(0,8)) de++;
  const ate=Math.min(KL.length-1,t.i_sai+15), jan=ate-de+1;
  const larg=(kchart.getSize('candle_pane','main')||{}).width||900;
  const esp=Math.max(2,Math.min(28,larg/(jan+8))); kchart.setBarSpace(esp); kchart.scrollToDataIndex(ate+4);
  const ts=k=>KL[k].timestamp;
  kchart.createOverlay({name:'zona',points:[{timestamp:ts(t.v0)},{timestamp:ts(t.i)}],extendData:{cor:alfa(cv('azul'),.10),meia:esp/2}});
  kchart.createOverlay({name:'zona',points:[{timestamp:ts(t.i)},{timestamp:ts(t.i_sai)}],extendData:{cor:alfa(t.rs>=0?cv('ganho'):cv('perda'),.07),meia:esp/2}});
  const pe=t.pe, fim=ts(Math.min(KL.length-1,t.i_sai+3));
  const niv=[{v:pe-ld*t.stop,rot:'stop −'+fmt(t.stop),cor:cv('perda')}];
  if(typeof V.alvo==='number') niv.push({v:pe+ld*V.alvo,rot:'alvo +'+V.alvo,cor:cv('ganho')});
  if(V.parcial) niv.push({v:pe+ld*V.parcial,rot:'parcial +'+V.parcial,cor:cv('ganho'),tr:1});
  niv.forEach(n=>kchart.createOverlay({name:'nivel',points:[{timestamp:ts(t.i),value:n.v},{timestamp:fim,value:n.v}],extendData:n}));
  kchart.createOverlay({name:'marca',points:[{timestamp:ts(t.i),value:pe}],extendData:{cor:cv('azul'),rot:(ld>0?'C ':'V ')+fmt(pe)}});
  kchart.createOverlay({name:'marca',points:[{timestamp:ts(t.i_sai),value:t.ps}],extendData:{cor:t.rs>=0?cv('ganho'):cv('perda'),rot:'saída '+fmt(t.ps)}});
  $('#ksel').value=String(kidx);
  const MOT={alvo:'alvo',stop:'stop',stop_zero:'parcial + stop na média',fim_dia:'fim do pregão',tempo:'tempo'};
  const PAD={falso:'falso rompimento',duplo:'topo/fundo duplo',rejeicao:'pavio de rejeição',exaustao:'exaustão',simples:'simples'};
  $('#kinfo').innerHTML=`<span><b>#${kidx+1}</b> de ${fmt(KTR.length)}</span><span>${t.data}</span><span><b>${ld>0?'▲ compra':'▼ venda'}</b></span>`+
    `<span>${t.nivel?'banda '+t.nivel+' · '+t.toque+'º toque na banda '+(t.tb||1):'VWAP'}</span><span>empurrão ${t.emp} candles · pavio ${fmt(t.pav)}</span>`+
    `<span>classe: ${PAD[t.pad]||t.pad}</span><span>ângulo VWAP ${sn(t.ang,1)} pts/candle</span><span>VWAP a ${fmt(t.dv)} pts</span>`+
    `<span>entrada <b>${fmt(pe)}</b></span><span>saída <b>${fmt(t.ps)}</b> (${MOT[t.mot]||t.mot})</span>`+
    `<span>${sn(t.pts,0)} pts</span><span>resultado <b class="${cls(t.rs)}">${rs(t.rs)}</b></span><span>MEP ${sn(t.mfe)} · MEN ${sn(t.mae)}</span>`;
}
function trocaK(){listaK(); mostraK(0);}
$('#kvar').addEventListener('change',e=>{kVar=e.target.value;trocaK();});
$('#kfiltro').addEventListener('change',trocaK);
$('#ksel').addEventListener('change',e=>mostraK(+e.target.value));
$('#kant').addEventListener('click',()=>mostraK(kidx-1)); $('#kprox').addEventListener('click',()=>mostraK(kidx+1));
addEventListener('keydown',ev=>{if(['SELECT','INPUT'].includes(ev.target.tagName))return;
  if(ev.key==='ArrowLeft')mostraK(kidx-1); if(ev.key==='ArrowRight')mostraK(kidx+1);});
desenhaEq(); iniciaK();
let rz; addEventListener('resize',()=>{clearTimeout(rz);rz=setTimeout(()=>{fixaSel();desenhaEq();kchart&&kchart.resize();},200);});
$('#btema').addEventListener('click',()=>{const r=document.documentElement;
  const escuro=r.dataset.theme?r.dataset.theme==='dark':matchMedia('(prefers-color-scheme: dark)').matches;
  r.dataset.theme=escuro?'light':'dark'; desenhaEq(); if(kchart){kchart.setStyles(estiloK()); mostraK(kidx);}});
"""


# ------------------------------------------------------------------ markdown
def md_faixa(lin, gks=('r300', 'r500', 'vw', 'claude'), rot='Faixa'):
    nm = dict(GS)
    s = f'| {rot} | Sinais | ' + ' | '.join(nm[g] for g in gks) + ' | Treino (300) | Teste (300) |\n'
    s += '|:--|--:|' + '--:|' * len(gks) + '--:|--:|\n'
    for l in lin:
        s += (f"| {txt(l['faixa'])} | {n(l['n'])} | " + ' | '.join(rs(l[g]['ev'], 1) for g in gks)
              + f" | {rs(l['r300']['ev_is'], 1)} | {rs(l['r300']['ev_oos'], 1)} |\n")
    return s


def markdown():
    hE = hip('Exaustao limpa (', 'r300'); hET = hip('Exaustao limpa E 1o/2o', 'r300')
    A = T['vwap_alvo']
    s = f"""# Reversões nas VWAP Bands

WINFUT PI 20, {M['pregoes']} pregões ({M['inicio']} a {M['fim']}), mesmos candles do Backtest-Momentum2-GraficoPI com volume financeiro e quantidade. VWAP Band do Profit: VWAP com preço "Média financeira" e bandas em envelope de 1/3 %, 2/3 % e 1 % da VWAP, conferidas contra o Profit.
6 contratos, R$ 0,50 por contrato. Treino até {M['corte']}. Stop de 100 em todas as saídas. Gráficos, tabelas completas e trade a trade em `vwap.html`.

## Resposta

- **Reverter toda virada na banda só empata**: {rs(base('c1')['g']['r300']['ev'], 1)} por trade (alvo 300). Melhor que entrar ao acaso ({rs(T['aleatorio']['r300'], 1)}), mas sem lucro, e rende o mesmo fora das bandas. A banda 1, 2 ou 3 não muda isso.
- **Padrão que funciona: exaustão limpa** — 4+ candles seguidos até a banda e virada no 1º candle contra **sem pavio de rejeição**. {n(hE['n'])} sinais, {rs(hE['ev'], 1)} por trade, treino {rs(hE['ev_is'], 1)}, teste {rs(hE['ev_oos'], 1)}, positivo nos 3 terços. **Na banda 2 ou além**: {n(hip('Exaustao limpa E banda 2+', 'r300')['n'])} sinais, {rs(hip('Exaustao limpa E banda 2+', 'r300')['ev'], 1)} por trade, positiva nas 4 saídas. Na banda 1 ela rende menos que fora das bandas.
- **Pavio de rejeição grande e topo/fundo duplo são piores** que a média, e o falso rompimento também fica abaixo; 2º candle contra e virada da Hull pioram.
- **Primeiros toques, contando todo sinal do toque, ajudam pouco**: 1º toque na banda 1 {rs(hip('1o toque na banda 1', 'r300')['ev'], 1)} contra {rs(hip('1o toque na banda 1', 'r300')['resto'], 1)}, negativo no último terço. Com uma entrada por toque, ver `TOQUE.md`.
- **Ângulo da VWAP não ordena os resultados** em nenhuma medida (pts/candle em 10 e 20 candles, passos de banda).
- **VWAP não é ponto de entrada** (repique na VWAP negativo em quase todas as saídas e recortes) e é **alvo longe demais**: mediana de {n(A['dist_q'][2])} pts; só {n(A['stops'][0]['hit'], 0)}% chegam antes do stop 100.
- **Alvo 300 > alvo 500**: só {n(A['p_mfe']['500'], 0)}% andam 500 antes do stop, {n(A['p_mfe']['300'], 0)}% andam 300.

## Base

| Gatilho | Sinais | """ + ' | '.join(r for _, r in GS) + ' |\n|:--|--:|' + '--:|' * 4 + '\n'
    for b in T['base']:
        s += f"| {txt(b['nome'])} | {n(b['n'])} | " + ' | '.join(rs(b['g'][g]['ev'], 1) for g, _ in GS) + ' |\n'
    s += '| Entrada aleatória | | ' + ' | '.join(rs(T['aleatorio'][g], 1) if g != 'vw' else '-' for g, _ in GS) + ' |\n'
    s += '\n## Padrões (alvo 300, grupo x resto)\n\n| Grupo | Sinais | R$/trade | Resto | Treino | Teste | t | Percentil |\n|:--|--:|--:|--:|--:|--:|--:|--:|\n'
    for r in sorted(T['hip']['r300'], key=lambda r: -(r['ev'] - r['resto'])):
        s += (f"| {txt(r['nome'])} | {n(r['n'])} | {rs(r['ev'], 1)} | {rs(r['resto'], 1)} | {rs(r['ev_is'], 1)} | "
              f"{rs(r['ev_oos'], 1)} | {n(r['t'], 2)} | {n(r['pct'], 0)} |\n")
    for k, fonte, rot in [('pav', 'faixas', 'Pavio do candle de virada'), ('emp', 'faixas', 'Candles do empurrão'),
                          ('nivel', 'faixas', 'Banda alcançada'), ('toque1', 'faixas', 'Toque na banda 1'),
                          ('toque1', 'faixas_E', 'Exaustão limpa: toque na banda 1'), ('ang', 'faixas', 'Ângulo VWAP (pts/candle, 10)'),
                          ('ang', 'faixas_E', 'Exaustão limpa: ângulo VWAP')]:
        s += f'\n**{rot}**\n\n' + md_faixa(T[fonte][k]['lin'], rot=rot)
    s += '\n**A banda importa? Exaustão limpa em qualquer lugar, pela distância do extremo à VWAP (em bandas)**\n\n' + md_faixa(T['controle']['exaust'], rot='Extremo')
    s += '\n## VWAP como entrada (1º candle contra)\n\n| Grupo | Sinais | Alvo 300 | Alvo 500 | Alvo banda 1 | CLAUDE.md |\n|:--|--:|--:|--:|--:|--:|\n'
    for l in T['vwap_entrada']['c1']['lin']:
        s += f"| {txt(l['faixa'])} | {n(l['n'])} | " + ' | '.join(rs(l[g]['ev'], 1) for g in ('r300', 'r500', 'b1', 'claude')) + ' |\n'
    s += '\n## VWAP como alvo (todos os sinais c1)\n\n| Stop | Chegou na VWAP | R$/trade |\n|:--|--:|--:|\n'
    for r in A['stops']:
        s += f"| {r['stop']} | {n(r['hit'], 1)}% | {rs(r['ev'], 1) if r['ev'] is not None else '-'} |\n"
    for gk, r in GS:
        s += f'\n## Carteira: {r} ({NOME_G[gk]})\n\n| Filtro | Trades | Líquido | Fator | Rebaix. | Treino | Teste | Atravessar 5 |\n|:--|--:|--:|--:|--:|--:|--:|--:|\n'
        for l in T['carteiras'][gk]:
            st = l['stats']
            s += (f"| {txt(l['nome'])} | {n(st['trades'])} | {rs(st['liquido'])} | {n(st['fator_lucro'], 2)} | {rs(-st['dd_max'])} | "
                  f"{rs(l['is_'].get('liquido'))} | {rs(l['oos'].get('liquido'))} | {rs(l['atravessa'])} |\n")
    s += '\n## Robustez da exaustão limpa\n\n| Stop | Alvo | R$/sinal | Treino | Teste | Carteira | Fator |\n|:--|:--|--:|--:|--:|--:|--:|\n'
    for r in T['robustez']['stops']:
        s += f"| {r['stop']} | {r['alvo']} | {rs(r['ev'], 1)} | {rs(r['ev_is'], 1)} | {rs(r['ev_oos'], 1)} | {rs(r['liq'])} | {n(r['fl'], 2)} |\n"
    s += '\nBootstrap de pregões (4.000 sorteios): chance de prejuízo ' + ', '.join(
        f"{r} {n(T['robustez']['bootstrap'][g]['p_prejuizo'], 1)}%" for g, r in GS) + '.\n'
    s += ('\n**Limites**: 130 pregões de um regime; ~4 sinais/pregão na exaustão limpa e ~2 no recorte de 1º/2º toque; 21 hipóteses testadas. '
          'O que sustenta o candidato é a consistência (treino, teste, 3 terços, 4 saídas), não o tamanho do número.\n')
    return s


def main():
    EQ = {}
    pick = ['c1: todos', 'c1: sem pavio', 'c1: exaustao limpa (', 'c1: exaustao limpa E 1o/2o']
    nomes = ['Todos os sinais', 'Sem pavio de rejeição', 'Exaustão limpa', 'Exaustão limpa, 1º/2º toque']
    for gk, _ in GS:
        EQ[gk] = [dict(nome=nm, y=cart(p, gk)['eq_dia']) for p, nm in zip(pick, nomes)]
    with open(VENDOR, encoding='utf-8') as f:
        kc = f.read()
    js = (JS.replace('__TRADES__', json.dumps(TR, ensure_ascii=False))
          .replace('__CANDLES__', json.dumps(candles(), separators=(',', ':')))
          .replace('__EQ__', json.dumps(EQ)).replace('__DIAS__', json.dumps(M['dias'])))
    html = ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Reversões nas VWAP Bands</title>'
            f'<style>{CSS}{CSS_EXTRA}</style></head><body>'
            '<nav class="indice"><div class="wrap"><ul>'
            + ''.join(f'<li><a href="#{a}">{r}</a></li>' for a, r in MENU) +
            '</ul></div></nav><div class="wrap">' + corpo() + '</div>'
            '<button class="tema" id="btema" title="Alternar tema" aria-label="Alternar tema">&#9681;</button>'
            f'<script>{kc}</script><script>{js}</script></body></html>')
    with open(os.path.join(BASE, 'vwap.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    with open(os.path.join(BASE, 'VWAP.md'), 'w', encoding='utf-8') as f:
        f.write(markdown())
    print('vwap.html', round(len(html) / 1e6, 1), 'MB')


if __name__ == '__main__':
    main()
