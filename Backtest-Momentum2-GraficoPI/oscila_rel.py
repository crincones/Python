# -*- coding: utf-8 -*-
"""Relatorio: oscilacao em torno da EMA 21 -> oscila.html + OSCILA.md
(rodar depois de oscila.py)."""
import json
import os

import engine as E
from relatorio import CSS
from textos import n, rs, cls

BASE = E.BASE
T = json.load(open(os.path.join(BASE, 'saida', 'oscila.json'), encoding='utf-8'))
M = T['meta']
GS = [('r400', 'Stop 100 / alvo 400'), ('claude', 'Gestao CLAUDE.md')]
NOME_G = {'r400': 'Stop 100 / alvo 400 sem parcial', 'claude': 'Gestao do CLAUDE.md (stop 100, parcial +100, alvo 300)'}
MENU = [('resumo', 'Resposta'), ('defs', 'Medidas'), ('dist', 'Distribuicao'), ('faixas', 'Faixas'),
        ('mapa', 'Mapas'), ('hip', 'Hipoteses'), ('cart', 'Carteira'), ('comb', 'Combinado'),
        ('estab', 'Estabilidade'), ('corr', 'Correlacao')]


# ------------------------------------------------------------------ acesso
def bloco(col):
    for F in T['familias']:
        for b in F['blocos']:
            if b['col'] == col:
                return b
    raise KeyError(col)


def faixa(col, gk, i):
    return bloco(col)['tabs'][gk][i]


def hip(nome, gk):
    return next(r for r in T['hipoteses'] if r['gestao'] == gk and r['nome'].startswith(nome))


def cart(nome, gk, fonte='carteiras'):
    return next(l for l in T[fonte][gk] if l['nome'].startswith(nome))


def est(nome):
    return next(l for l in T['estabilidade'] if l['nome'].startswith(nome))


def mapa(cx, cy, gk):
    return next(m for m in T['mapas'] if m['dir_col'] == cx and m['cons_col'] == cy and m['gestao'] == gk)


def dist(col):
    return next(r for r in T['dist'] if r['col'] == col)


def tag(r):
    if r.get('resto_is') is None or r.get('resto_oos') is None:
        return ''
    a = r['ev_is'] - r['resto_is']; b = r['ev_oos'] - r['resto_oos']
    if a > 0 and b > 0:
        return '<span class="tag pos">melhor nos dois</span>'
    if a < 0 and b < 0:
        return '<span class="tag neg">pior nos dois</span>'
    return '<span class="tag">inverte</span>'


def tercos(l, gk):
    """Celula de estabilidade: 3 tercos, dentro x fora."""
    return ' &middot; '.join(f"{b['bloco'][:2]} <span class=\"{cls(b[gk]['ev'])}\">{rs(b[gk]['ev'], 0)}</span>"
                             f" <span class=\"nota\">({rs(b[gk]['resto'], 0)})</span>" for b in l['blocos'])


# ------------------------------------------------------------------ tabelas
def tab_faixa(col, gk):
    b = bloco(col)
    h = (f'<div class="tab"><table><thead><tr><th>{b["rotulo"]}</th><th>Sinais</th><th>R$/trade</th><th>Acerto</th>'
         '<th>Treino</th><th>Teste</th><th>Compra</th><th>Venda</th></tr></thead><tbody>')
    for l in b['tabs'][gk]:
        h += (f"<tr><td>{l['faixa']}</td><td>{n(l['n'])}</td><td class=\"{cls(l['ev'])}\">{rs(l['ev'], 1)}</td><td>{n(l['wr'], 0)}%</td>"
              f"<td class=\"{cls(l['ev_is'])}\">{rs(l['ev_is'], 1)} <span class=\"nota\">({n(l['n_is'])})</span></td>"
              f"<td class=\"{cls(l['ev_oos'])}\">{rs(l['ev_oos'], 1)} <span class=\"nota\">({n(l['n_oos'])})</span></td>"
              f"<td class=\"{cls(l['compra'])}\">{rs(l['compra'], 1)}</td><td class=\"{cls(l['venda'])}\">{rs(l['venda'], 1)}</td></tr>")
    return h + '</tbody></table></div>'


def tab_dist():
    h = ('<div class="tab"><table><thead><tr><th>Medida</th><th>Janela</th><th>Ancora</th><th>p5</th><th>p25</th><th>Mediana</th>'
         '<th>p75</th><th>p95</th></tr></thead><tbody>')
    RM = dict(nfav='Candles a favor menos contra', lado='Fracao no lado dominante', soma='Somatoria / W (pts)',
              soman='Somatoria / W (ranges medios)', abs='Distancia media ate a EMA (pts)',
              pureza='Pureza', cruz='Cruzamentos da EMA', toca='Fracao de candles cortados pela EMA')
    for r in T['dist']:
        c = 2 if r['met'] in ('lado', 'pureza', 'soman', 'toca') else 0
        h += (f"<tr class=\"{'dest' if r['col'] in ('pureza_5p', 'cruz_20p', 'abs_20p') else ''}\"><td>{RM[r['met']]}</td><td>{r['W']}</td>"
              f"<td>{'antes do recuo' if r['anc'] == 'p' else 'ate o trigger'}</td>"
              + ''.join(f"<td>{n(r[k], c)}</td>" for k in ('p5', 'p25', 'p50', 'p75', 'p95')) + '</tr>')
    return h + '</tbody></table></div>'


def tab_hip(gk):
    H = sorted([r for r in T['hipoteses'] if r['gestao'] == gk], key=lambda r: r['ev'] - r['resto'])
    h = ('<div class="tab"><table><thead><tr><th>Grupo</th><th>Sinais</th><th>R$/trade</th><th>Resto</th><th>Treino (resto)</th>'
         '<th>Teste (resto)</th><th>Stop cheio (resto)</th><th>t</th><th>Percentil</th><th>Treino x teste</th></tr></thead><tbody>')
    for r in H:
        h += (f"<tr><td>{r['nome']}</td><td>{n(r['n'])} <span class=\"nota\">({n(r['frac'] * 100, 0)}%)</span></td>"
              f"<td class=\"{cls(r['ev'])}\">{rs(r['ev'], 1)}</td><td class=\"{cls(r['resto'])}\">{rs(r['resto'], 1)}</td>"
              f"<td><span class=\"{cls(r['ev_is'])}\">{rs(r['ev_is'], 1)}</span> <span class=\"nota\">({rs(r['resto_is'], 1)})</span></td>"
              f"<td><span class=\"{cls(r['ev_oos'])}\">{rs(r['ev_oos'], 1)}</span> <span class=\"nota\">({rs(r['resto_oos'], 1)})</span></td>"
              f"<td>{n(r['falha'], 0)}% <span class=\"nota\">({n(r['falha_resto'], 0)}%)</span></td>"
              f"<td>{n(r.get('t'), 2)}</td><td>{n(r.get('pct'), 0)}</td><td>{tag(r)}</td></tr>")
    return h + '</tbody></table></div>'


def tab_cart(linhas, gid):
    h = ('<div class="tab"><table><thead><tr><th>Filtro</th><th>Sinais</th><th>Trades</th><th>Liquido</th><th>Fator</th>'
         '<th>Rebaixamento</th><th>Recuperacao</th><th>Treino</th><th>Teste</th><th>Atravessar 5 pts</th></tr></thead><tbody>')
    for i, l in enumerate(linhas):
        s = l['stats']
        h += (f"<tr class=\"{'dest' if i == 0 else ''}\"><td>{l['nome']}</td><td>{n(l['frac'] * 100, 0)}%</td><td>{n(s['trades'])}</td>"
              f"<td class=\"{cls(s['liquido'])}\">{rs(s['liquido'])}</td><td>{n(s['fator_lucro'], 2)}</td><td>{rs(-s['dd_max'])}</td>"
              f"<td>{n(s['recovery'], 2)}</td><td class=\"{cls(l['is_']['liquido'])}\">{rs(l['is_']['liquido'])}</td>"
              f"<td class=\"{cls(l['oos']['liquido'])}\">{rs(l['oos']['liquido'])}</td>"
              f"<td class=\"{cls(l['atravessa'])}\">{rs(l['atravessa'])}</td></tr>")
    return h + f'</tbody></table></div><div class="card"><div class="graf" id="{gid}"></div></div>'


def tab_estab(gk):
    h = ('<div class="tab"><table><thead><tr><th>Grupo</th><th>Sinais</th>'
         + ''.join(f"<th>{t['rot']}<br><span class=\"nota\">{t['ini'][8:10]}/{t['ini'][5:7]} a {t['fim'][8:10]}/{t['fim'][5:7]}</span></th>" for t in M['tercos'])
         + '<th>Sinal</th></tr></thead><tbody>')
    for l in T['estabilidade']:
        sg = [b[gk]['ev'] - b[gk]['resto'] for b in l['blocos']]
        marca = ('<span class="tag pos">3 de 3</span>' if all(x > 0 for x in sg) else
                 '<span class="tag neg">3 de 3 pior</span>' if all(x < 0 for x in sg) else
                 f'<span class="tag">{sum(x > 0 for x in sg)} de 3</span>')
        h += f"<tr><td>{l['nome']}</td><td>{n(l['frac'] * 100, 0)}%</td>"
        for b in l['blocos']:
            h += (f"<td><span class=\"{cls(b[gk]['ev'])}\">{rs(b[gk]['ev'], 1)}</span> <span class=\"nota\">({rs(b[gk]['resto'], 1)})</span><br>"
                  f"<span class=\"nota\">{n(b['n'])} x {n(b['n_fora'])} sinais</span></td>")
        h += f'<td>{marca}</td></tr>'
    return h + ('</tbody></table></div><p class="nota">Em cada celula: R$/trade do grupo e, entre parenteses, dos sinais de fora. '
                'O periodo vai partido em tres blocos de 44 pregoes. "3 de 3" = o grupo ficou acima do resto nos tres blocos.</p>')


def tab_mapa(cx, cy, gk, rot_x, rot_y):
    m = mapa(cx, cy, gk)
    qd = m['qd']; qc = m['qc']
    rx = [f'ate {n(qd[0], 2)}', f'{n(qd[0], 2)} a {n(qd[1], 2)}', f'acima de {n(qd[1], 2)}']
    ry = [f'ate {n(qc[0], 2)}', f'{n(qc[0], 2)} a {n(qc[1], 2)}', f'acima de {n(qc[1], 2)}']
    cel = {(c['dir'], c['cons']): c for c in m['celulas']}
    h = (f'<div class="tab"><table><thead><tr><th>{rot_y} \\ {rot_x}</th>' + ''.join(f'<th>{r}</th>' for r in rx) +
         '</tr></thead><tbody>')
    for b in (2, 1, 0):
        h += f'<tr><td><b>{ry[b]}</b></td>'
        for a in range(3):
            c = cel[(a, b)]
            h += (f"<td><span class=\"{cls(c['ev'])}\"><b>{rs(c['ev'], 1)}</b></span><br>"
                  f"<span class=\"nota\">{n(c['n'])} sinais &middot; treino {rs(c['ev_is'], 0)} &middot; teste {rs(c['ev_oos'], 0)}</span></td>")
        h += '</tr>'
    return h + '</tbody></table></div>'


# ------------------------------------------------------------------ selector
def sel(alvo, itens, ini=None):
    ini = ini or itens[0][0]
    return ('<div class="abas" data-alvo="%s">' % alvo +
            ''.join(f'<button data-k="{k}" class="{"on" if k == ini else ""}">{r}</button>' for k, r in itens) + '</div>')


def blocos(alvo, itens, render, ini=None):
    ini = ini or itens[0][0]
    return ''.join(f'<div class="bl" data-alvo="{alvo}" data-k="{k}"{"" if k == ini else " hidden"}>{render(k)}</div>' for k, _ in itens)


def por_gestao(render):
    """Mesmo conteudo nas duas gestoes, comandado pelo seletor global."""
    return ''.join(f'<div class="gest" data-g="{gk}"{"" if gk == "r400" else " hidden"}>{render(gk)}</div>' for gk, _ in GS)


MET_PT = dict(nfav='a favor menos contra', lado='lado dominante', soma='somatoria (pts)',
              soman='somatoria (ranges)', abs='distancia media', pureza='pureza',
              cruz='cruzamentos', toca='toques')
COLS_FAM = {}
for F in T['familias']:
    COLS_FAM[F['familia']] = [(b['col'], f"{MET_PT[b['met']]} &middot; {b['W']} {'antes' if b['anc'] == 'p' else 'ate o trigger'}")
                              for b in F['blocos']]


def corpo():
    b400 = M['base']['r400']; bcl = M['base']['claude']
    c0 = {g: cart('sem filtro', g) for g, _ in GS}
    ccz = {g: cart('2 a 4 cruzamentos', g) for g, _ in GS}
    cfo = {g: cart('fora de: 0-1', g) for g, _ in GS}
    cp5 = {g: cart('pureza 5 (antes do recuo) >= 0,7', g) for g, _ in GS}
    cab = {g: cart('distancia media ate a EMA em 20 < 211', g) for g, _ in GS}
    kcons = {g: cart('fora do canto ruim E consolidacao 100', g, 'combina') for g, _ in GS}
    kcons0 = {g: cart('fora da consolidacao 100', g, 'combina') for g, _ in GS}
    h0 = {g: hip('Sem nenhum cruzamento da EMA em 20 (antes do recuo)', g) for g, _ in GS}
    e_canto = est('0-1 cruzamento'); e_p5 = est('pureza 5'); e_cz = est('2 a 4 cruzamentos')
    f_p5 = {g: (faixa('pureza_5p', g, 0), faixa('pureza_5p', g, 1)) for g, _ in GS}
    f_cz = {g: bloco('cruz_20p')['tabs'][g] for g, _ in GS}
    f_ab = {g: bloco('abs_20p')['tabs'][g] for g, _ in GS}
    d5 = dist('pureza_5p'); d20 = dist('pureza_20p'); dcz = dist('cruz_20p')
    mcz = mapa('cruz_20p', 'abs_20p', 'r400')
    cruim = next(c for c in mcz['celulas'] if c['dir'] == 0 and c['cons'] == 2)
    cbom = next(c for c in mcz['celulas'] if c['dir'] == 1 and c['cons'] == 1)

    return f"""
<h1>Oscilacao do preco em torno da EMA 21</h1>
<p class="sub">Setup EMA 21 + HullRetracao_Azul + MACD &middot; WINFUT PI 20, {M['pregoes']} pregoes ({M['inicio']} a {M['fim']}) &middot;
{n(M['sinais'])} sinais &middot; entrada seca no fechamento &middot; 6 contratos, R$ 0,50 por contrato &middot;
treino ate {M['corte']} ({n(M['n_is'])} sinais), teste depois ({n(M['n_oos'])})</p>

<div class="abas" id="gest"><button data-g="r400" class="on">Stop 100 / alvo 400</button><button data-g="claude">Gestao CLAUDE.md</button></div>

<section id="resumo"><h2>Resposta curta</h2>
{por_gestao(lambda g: f'''
<div class="kpis">
<div class="kpi"><div class="r">Carteira sem filtro</div><div class="v {cls(c0[g]['stats']['liquido'])}">{rs(c0[g]['stats']['liquido'])}</div></div>
<div class="kpi"><div class="r">Tirando o canto ruim (23% dos sinais)</div><div class="v {cls(cfo[g]['stats']['liquido'])}">{rs(cfo[g]['stats']['liquido'])}</div></div>
<div class="kpi"><div class="r">So 2 a 4 cruzamentos da EMA em 20</div><div class="v {cls(ccz[g]['stats']['liquido'])}">{rs(ccz[g]['stats']['liquido'])}</div></div>
<div class="kpi"><div class="r">Sem oscilar nos 5 candles (pureza &ge; 0,7)</div><div class="v {cls(cp5[g]['stats']['liquido'])}">{rs(cp5[g]['stats']['liquido'])}</div></div>
</div>''')}

<div class="card ruim"><b>1. Na janela de 20 candles a sua leitura se inverte: quem oscila em torno da EMA ganha, quem fica so de um lado perde.</b>
Os sinais em que o preco <b>nao cruzou nenhuma vez</b> a EMA 21 nos 20 candles antes do recuo &mdash; ou seja, os 20 fechamentos do mesmo lado,
pureza 1,00, o caso extremo de "ficar mais de um lado do que do outro" &mdash; sao {n(h0['r400']['n'])} ({n(h0['r400']['frac'] * 100, 0)}% do total) e deram
<span class="neg">{rs(h0['r400']['ev'], 1)}</span> por trade contra {rs(h0['r400']['resto'], 1)} do resto (alvo 400; treino {rs(h0['r400']['ev_is'], 1)}, teste {rs(h0['r400']['ev_oos'], 1)}).
Na gestao do CLAUDE.md, {rs(h0['claude']['ev'], 1)} contra {rs(h0['claude']['resto'], 1)}. A faixa de <b>2 a 4 cruzamentos</b> (o miolo da distribuicao, {n(f_cz['r400'][2]['n'])} sinais)
e a melhor de todas: {rs(f_cz['r400'][2]['ev'], 1)} por trade (treino {rs(f_cz['r400'][2]['ev_is'], 1)}, teste {rs(f_cz['r400'][2]['ev_oos'], 1)}) e
{rs(f_cz['claude'][2]['ev'], 1)} no CLAUDE.md. Em carteira: {rs(c0['r400']['stats']['liquido'])} &rarr; <b>{rs(ccz['r400']['stats']['liquido'])}</b> com o rebaixamento caindo de
{rs(-c0['r400']['stats']['dd_max'])} para {rs(-ccz['r400']['stats']['dd_max'])}.</div>

<div class="card ok"><b>2. Na janela curta de 5 candles a sua leitura vale.</b> Ai a oscilacao e um problema: os {n(f_p5['r400'][0]['n'])} sinais do quintil
de baixo da pureza de 5 (abaixo de 0,74, isto e, os 5 candles repartidos entre os dois lados) deram <span class="neg">{rs(f_p5['r400'][0]['ev'], 1)}</span> por trade
contra {rs(f_p5['r400'][1]['ev'], 1)} dos demais, e ficaram negativos no treino ({rs(f_p5['r400'][0]['ev_is'], 1)}) e no teste ({rs(f_p5['r400'][0]['ev_oos'], 1)}).
No CLAUDE.md o mesmo: {rs(f_p5['claude'][0]['ev'], 1)} contra {rs(f_p5['claude'][1]['ev'], 1)}, negativo nas duas metades. E o unico corte do estudo que aponta
para o mesmo lado nas duas gestoes E nas duas metades. Em carteira ele custa pouco (corta {n((1 - cp5['r400']['frac']) * 100, 0)}% dos sinais) e melhora as duas:
{rs(c0['r400']['stats']['liquido'])} &rarr; {rs(cp5['r400']['stats']['liquido'])} e {rs(c0['claude']['stats']['liquido'])} &rarr; {rs(cp5['claude']['stats']['liquido'])}.</div>

<div class="card ok"><b>3. O achado mais firme do estudo e o cruzamento das duas coisas: poucos cruzamentos <i>e</i> preco longe da media.</b>
Os sinais com 0 ou 1 cruzamento da EMA em 20 candles <b>e</b> distancia media ao EMA acima de {n(176.56, 0)} pts sao {n(cruim['n'])} ({n(e_canto['frac'] * 100, 0)}% do total) e deram
<span class="neg">{rs(cruim['ev'], 1)}</span> por trade, com treino {rs(cruim['ev_is'], 1)} e teste {rs(cruim['ev_oos'], 1)} &mdash; praticamente o mesmo numero nas duas metades.
Partindo o periodo em tres blocos de 44 pregoes, esse grupo fica negativo nos <b>tres</b> e nas <b>duas</b> gestoes: {tercos(e_canto, 'r400')} (alvo 400) e {tercos(e_canto, 'claude')} (CLAUDE.md).
Descartar so esse canto: {rs(c0['r400']['stats']['liquido'])} &rarr; <b>{rs(cfo['r400']['stats']['liquido'])}</b> e {rs(c0['claude']['stats']['liquido'])} &rarr; <b>{rs(cfo['claude']['stats']['liquido'])}</b>.
No outro extremo, 2 a 4 cruzamentos com distancia intermediaria: {rs(cbom['ev'], 1)} por trade em {n(cbom['n'])} sinais.</div>

<div class="card alerta"><b>4. A somatoria com sinal (positivo acima, negativo abaixo) nao separa nada.</b> Nem em 5, nem em 10, nem em 20 candles.
Exigir a somatoria a favor do trade (o preco tendo ficado mais do lado "certo" da media) piora a carteira nas duas gestoes:
{rs(c0['r400']['stats']['liquido'])} &rarr; {rs(cart('somatoria 20 a favor', 'r400')['stats']['liquido'])} e
{rs(c0['claude']['stats']['liquido'])} &rarr; {rs(cart('somatoria 20 a favor', 'claude')['stats']['liquido'])}; por terco, o grupo fica acima do resto em so 1 dos 3 blocos.
O que importa e o <b>formato</b> do caminho (quantas vezes cruzou, a que distancia), nao de que lado ele ficou.</div>

<div class="card"><b>5. Cuidado: boa parte disso ja estava medido com outro nome.</b> "Poucos cruzamentos" e "longe da media" tem correlacao de posto
{n(T['corr']['cruz_20p']['kc_10'], 2)} e {n(T['corr']['abs_20p']['kc_10'], 2)} com o quanto o preco passou da banda de Keltner &mdash; o achado do <code>impulso.html</code>
de que movimento esticado rende menos. Somado a consolidacao de 100 candles do <code>tendencia.html</code> o ganho fica pequeno:
{rs(kcons0['r400']['stats']['liquido'])} (so consolidacao) &rarr; {rs(kcons['r400']['stats']['liquido'])} (consolidacao + canto ruim fora), e
{rs(kcons0['claude']['stats']['liquido'])} &rarr; {rs(kcons['claude']['stats']['liquido'])}. E um reforco da mesma ideia, nao um filtro independente.</div>
</section>

<section id="defs"><h2>Como foi medido</h2>
<div class="card"><ul>
<li>Para cada sinal se olha uma janela de <b>5, 10 ou 20 candles</b>, e em cada candle a distancia <code>fechamento &minus; EMA 21</code>.
Tudo orientado pelo lado do trade: na compra, acima da EMA e positivo; na venda, abaixo da EMA e positivo.</li>
<li><b>Ancora "antes do recuo"</b>: a janela termina no candle anterior ao primeiro candle contra (j = v0 &minus; 1), para que os 2-3 candles do proprio
recuo &mdash; que por construcao encostam na EMA &mdash; nao entrem na conta. <b>Ancora "ate o trigger"</b>: termina no proprio candle do trigger. As duas
aparecem em todas as tabelas; a leitura principal e a primeira, igual ao resto do projeto.</li>
<li><b>Candles de cada lado</b>: quantos fecharam do lado favoravel menos quantos do lado contrario ({n(-20)} a +20 na janela de 20).
E a <b>fracao no lado dominante</b> = maior das duas contagens / W: 0,5 = metade de cada lado, 1 = todos do mesmo lado.</li>
<li><b>Somatoria</b> = soma das distancias dividida pela janela, em pontos. Tambem em ranges medios de 21 candles (o range mediano do periodo e
{n(M['rng_med'], 0)} pts), para comparar dias calmos com dias agitados.</li>
<li><b>Pureza</b> = |soma das distancias| / soma dos valores absolutos. E a medida direta da sua pergunta: 1 = a somatoria nao se cancelou nada
(todos os candles do mesmo lado); perto de 0 = o que ficou acima foi cancelado pelo que ficou abaixo, preco oscilando em torno da media.</li>
<li><b>Distancia media absoluta</b> = soma de |fechamento &minus; EMA| / W: separa oscilacao larga (preco indo longe dos dois lados) de oscilacao
apertada (preco colado na media).</li>
<li><b>Cruzamentos</b> = quantas vezes o fechamento trocou de lado da EMA dentro da janela. <b>Toques</b> = fracao de candles cujo range contem a EMA.</li>
<li>As janelas nao atravessam o fechamento do pregao (o gap distorceria a distancia ate a media). Nos {n(dist('pureza_20p')['nan'])} sinais do
comeco do dia com menos de 3 candles disponiveis as medidas ficam vazias.</li>
<li>Nada posterior ao fechamento do candle do trigger entra na conta. "Stop cheio" = saida no stop de &minus;100 sem parcial.
Treino = os primeiros 60% dos pregoes; teste = os 40% finais.</li>
</ul></div>
</section>

<section id="dist"><h2>Como as medidas se distribuem</h2>
<p class="nota">Antes de qualquer resultado, o tamanho de cada medida. Repare que em 5 candles a pureza mediana ja e {n(d5['p50'], 2)} e a fracao no lado
dominante mediana e 1,00: com 5 candles o normal e o preco estar todo de um lado. Em 20 candles a pureza mediana cai para {n(d20['p50'], 2)} e a
mediana de cruzamentos e {n(dcz['p50'], 0)}. Por isso a mesma pergunta responde coisas diferentes em cada janela.</p>
{tab_dist()}
</section>

<section id="faixas"><h2>Faixas de cada medida</h2>
<p class="nota">Quintis calculados no treino (quando a medida tem poucos valores distintos, as faixas se juntam). R$/trade com 6 contratos e custo incluido.</p>
{''.join(f'<h3>{F["familia"]}</h3><p class="nota">{F["desc"]}</p>' + sel(f'fa{i}', COLS_FAM[F["familia"]]) + por_gestao(lambda g, i=i, F=F: blocos(f'fa{i}', COLS_FAM[F['familia']], lambda k, g=g: tab_faixa(k, g))) for i, F in enumerate(T['familias']))}
</section>

<section id="mapa"><h2>Mapas cruzados</h2>
<p class="nota">Tercos calculados no treino. Em cada celula, R$/trade, numero de sinais e o resultado no treino e no teste.</p>
<h3>Cruzamentos da EMA (20, antes do recuo) x distancia media ate a EMA</h3>
<p class="nota">O canto de cima a esquerda &mdash; poucos cruzamentos e preco longe da media, ou seja, o movimento de mao unica esticado &mdash; e o unico
com treino e teste praticamente iguais e negativos.</p>
{por_gestao(lambda g: tab_mapa('cruz_20p', 'abs_20p', g, 'Cruzamentos em 20', 'Distancia media ate a EMA'))}
<h3>Somatoria x pureza (20, antes do recuo)</h3>
<p class="nota">O par que voce descreveu. As duas medidas sao quase a mesma coisa (correlacao de posto {n(T['corr_internas']['soma_20p']['pureza_20p'], 2)}):
somatoria grande implica pureza alta, entao as celulas ficam vazias nas diagonais e o mapa nao separa.</p>
{por_gestao(lambda g: tab_mapa('soma_20p', 'pureza_20p', g, 'Somatoria / W', 'Pureza'))}
<h3>Cruzamentos x consolidacao de 100 candles</h3>
<p class="nota">Contra o filtro que ja existia (<code>tendencia.html</code>). As duas medidas nao sao redundantes: as melhores celulas exigem as duas coisas.</p>
{por_gestao(lambda g: tab_mapa('cruz_20p', 'er_100', g, 'Cruzamentos em 20', 'Eficiencia em 100'))}
</section>

<section id="hip"><h2>Hipoteses, uma a uma</h2>
<p class="nota">Cada linha compara o grupo com todos os outros sinais. "t" e a estatistica de Welch; "percentil" e a posicao da media do grupo
entre 1.500 subconjuntos sorteados do mesmo tamanho &mdash; abaixo de 5 ou acima de 95 seria forte, e quase nada chega la.
A tabela vai do pior para o melhor grupo.</p>
{por_gestao(tab_hip)}
</section>

<section id="cart"><h2>Carteira</h2>
<p class="nota">Uma posicao por vez, sinais durante um trade aberto sao ignorados. "Atravessar 5 pts" refaz a conta exigindo que o preco passe 5 pts
do alvo/parcial antes de executar, como teste de execucao pessimista.</p>
{por_gestao(lambda g: tab_cart(T['carteiras'][g], 'g_ca_' + g))}
</section>

<section id="comb"><h2>Com os filtros dos outros estudos</h2>
<p class="nota">Consolidacao 100 = eficiencia &ge; 0,08 nos 100 candles antes do recuo (<code>tendencia.html</code>).
Keltner = o preco nao passou da banda de 2,5 nos 10 candles antes do recuo (<code>impulso.html</code>).</p>
{por_gestao(lambda g: tab_cart(T['combina'][g], 'g_co_' + g))}
</section>

<section id="estab"><h2>Estabilidade por terco do periodo</h2>
<p class="nota">O teste mais duro: em vez de uma so divisao treino/teste, o periodo vai partido em tres blocos iguais.
Um filtro que presta fica do mesmo lado nos tres blocos e nas duas gestoes.</p>
{por_gestao(tab_estab)}
</section>

<section id="corr"><h2>Correlacao com o que ja estava medido</h2>
<p class="nota">Correlacao de posto (Spearman) entre as medidas novas e as dos estudos anteriores. Valores altos significam que a medida nova
esta contando de novo a mesma historia.</p>
<div class="tab"><table><thead><tr><th>Medida nova</th>
<th>Eficiencia 100 (consolidacao)</th><th>Inversoes (picado)</th><th>Passou da Keltner 2,5</th><th>Impulso 20</th><th>Recuo / impulso</th>
<th>Barras no regime do MACD</th><th>Recuos anteriores a EMA</th></tr></thead><tbody>
{''.join(f"<tr><td>{c}</td>" + ''.join(f"<td class=\"{'pos' if abs(v[k]) >= 0.5 else ''}\">{n(v[k], 2)}</td>" for k in ('er_100', 'inversoes', 'kc_10', 'imp_20', 'ret_20', 'barras_regime', 'n_rec')) + '</tr>' for c, v in T['corr'].items())}
</tbody></table></div>
</section>
"""


JS = r"""
const T=__T__;
const $=s=>document.querySelector(s);
function cv(k){return getComputedStyle(document.documentElement).getPropertyValue('--'+k).trim();}
function fmt(v,c=0){if(v===null||v===undefined||Number.isNaN(v))return '-';return Number(v).toLocaleString('pt-BR',{minimumFractionDigits:c,maximumFractionDigits:c});}
function linhas(el,series){
  const W=Math.max(300,el.clientWidth||600), H=300, m={e:64,d:12,t:10,b:24};
  let ys=[0];series.forEach(s=>s.y.forEach(v=>ys.push(v)));
  let y0=Math.min(...ys),y1=Math.max(...ys); if(y1===y0)y1+=1; const pad=(y1-y0)*.06; y0-=pad; y1+=pad;
  const X=(i,L)=>m.e+(W-m.e-m.d)*(L<=1?0:i/(L-1)), Y=v=>m.t+(H-m.t-m.b)*(1-(v-y0)/(y1-y0));
  let s=`<svg viewBox="0 0 ${W} ${H}" role="img">`;
  for(let k=0;k<=4;k++){const v=y0+(y1-y0)*k/4;s+=`<line x1="${m.e}" x2="${W-m.d}" y1="${Y(v)}" y2="${Y(v)}" stroke="${cv('grade')}"/><text x="${m.e-6}" y="${Y(v)+4}" text-anchor="end" font-size="11" fill="${cv('mudo')}">${fmt(v)}</text>`;}
  s+=`<line x1="${m.e}" x2="${W-m.d}" y1="${Y(0)}" y2="${Y(0)}" stroke="${cv('eixo')}"/>`;
  s+=`<text x="${W-m.d}" y="${H-6}" text-anchor="end" font-size="11" fill="${cv('mudo')}">trades (cada curva na propria escala) &rarr;</text>`;
  series.forEach(se=>{const L=se.y.length;s+=`<polyline fill="none" stroke="${se.cor}" stroke-width="${se.larg||1.5}" points="${se.y.map((v,i)=>X(i,L).toFixed(1)+','+Y(v).toFixed(1)).join(' ')}"/>`;});
  el.innerHTML=`<div class="leg">${series.map(se=>`<span><i style="background:${se.cor}"></i>${se.nome}</span>`).join('')}</div>`+s+'</svg>';
}
const CORES=()=>[cv('tinta'),cv('azul'),cv('ganho'),cv('ouro'),cv('perda'),cv('alerta'),'#8e44ad','#16a085','#d35400'];
const PICK={g_ca_:[0,1,9,12,13],g_co_:null};
function curvas(){['r400','claude'].forEach(gk=>{
  [['g_ca_',T.carteiras[gk]],['g_co_',T.combina[gk]]].forEach(([pre,dados])=>{
    const el=document.getElementById(pre+gk); if(!el||!el.offsetParent) return;
    const cs=CORES(); const sel=PICK[pre]?dados.filter((l,i)=>PICK[pre].includes(i)):dados;
    linhas(el,sel.map((l,i)=>({nome:l.nome,cor:cs[i%cs.length],y:l.eq,larg:i===0?2.6:1.5})));});});}
document.querySelectorAll('.abas[data-alvo]').forEach(el=>el.addEventListener('click',e=>{const b=e.target.closest('button'); if(!b) return;
  el.querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b));
  document.querySelectorAll(`.bl[data-alvo="${el.dataset.alvo}"]`).forEach(x=>x.hidden=x.dataset.k!==b.dataset.k); curvas();}));
$('#gest').addEventListener('click',e=>{const b=e.target.closest('button'); if(!b) return;
  $('#gest').querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b));
  document.querySelectorAll('.gest').forEach(x=>x.hidden=x.dataset.g!==b.dataset.g); curvas();});
curvas();
let rz; addEventListener('resize',()=>{clearTimeout(rz);rz=setTimeout(curvas,200);});
$('#btema').addEventListener('click',()=>{const r=document.documentElement;
  const escuro=r.dataset.theme?r.dataset.theme==='dark':matchMedia('(prefers-color-scheme: dark)').matches;
  r.dataset.theme=escuro?'light':'dark'; curvas();});
"""

CSS_EXTRA = """
.card ul{margin:8px 0 4px;padding-left:20px}
.card li{margin:4px 0}
#gest{position:sticky;top:44px;z-index:5;background:var(--fundo);padding:6px 0}
h3{margin:22px 0 6px;font-size:1.02rem}
"""


def markdown():
    c0 = {g: cart('sem filtro', g) for g, _ in GS}
    ccz = {g: cart('2 a 4 cruzamentos', g) for g, _ in GS}
    cfo = {g: cart('fora de: 0-1', g) for g, _ in GS}
    cp5 = {g: cart('pureza 5 (antes do recuo) >= 0,7', g) for g, _ in GS}
    h0 = {g: hip('Sem nenhum cruzamento da EMA em 20 (antes do recuo)', g) for g, _ in GS}
    e_canto = est('0-1 cruzamento')
    L = ['# Oscilacao do preco em torno da EMA 21', '',
         f"Setup EMA 21 + HullRetracao_Azul + MACD, WINFUT PI 20, {M['pregoes']} pregoes ({M['inicio']} a {M['fim']}), {n(M['sinais'])} sinais. "
         f"Entrada seca no fechamento, 6 contratos, R$ 0,50 por contrato. Treino ate {M['corte']}. Graficos e tabelas completas em `oscila.html`.", '',
         '## O que foi medido', '',
         'Em janelas de 5, 10 e 20 candles, a distancia `fechamento - EMA 21` de cada candle, orientada pelo lado do trade '
         '(compra: acima da EMA e positivo; venda: espelho). Duas ancoras: janela terminando no candle anterior ao recuo (principal) '
         'e no candle do trigger. Daí saem:', '',
         '- **candles de cada lado**: a favor menos contra, e a fracao no lado dominante (0,5 = metade de cada lado, 1 = todos do mesmo lado);',
         '- **somatoria** das distancias / W, em pontos e em ranges medios;',
         '- **pureza** = |soma| / soma dos valores absolutos: 1 = nada se cancelou (um lado so), perto de 0 = oscilacao em torno da media;',
         '- **distancia media absoluta** ate a EMA;', '- **cruzamentos** do fechamento pela EMA e fracao de candles cortados por ela.', '']
    for gk, _ in GS:
        L += [f'## {NOME_G[gk]}', '', '**Cruzamentos da EMA em 20 candles (antes do recuo)**', '',
              '| Cruzamentos | Sinais | R$/trade | Treino | Teste |', '|:--|--:|--:|--:|--:|']
        for l in bloco('cruz_20p')['tabs'][gk]:
            L.append(f"| {l['faixa']} | {n(l['n'])} | {rs(l['ev'], 1)} | {rs(l['ev_is'], 1)} | {rs(l['ev_oos'], 1)} |")
        L += ['', '**Pureza em 5 candles (antes do recuo)**', '', '| Pureza | Sinais | R$/trade | Treino | Teste |', '|:--|--:|--:|--:|--:|']
        for l in bloco('pureza_5p')['tabs'][gk]:
            L.append(f"| {l['faixa']} | {n(l['n'])} | {rs(l['ev'], 1)} | {rs(l['ev_is'], 1)} | {rs(l['ev_oos'], 1)} |")
        L += ['', '**Pureza em 20 candles (antes do recuo)**', '', '| Pureza | Sinais | R$/trade | Treino | Teste |', '|:--|--:|--:|--:|--:|']
        for l in bloco('pureza_20p')['tabs'][gk]:
            L.append(f"| {l['faixa']} | {n(l['n'])} | {rs(l['ev'], 1)} | {rs(l['ev_is'], 1)} | {rs(l['ev_oos'], 1)} |")
        L += ['', '**Carteira**', '', '| Filtro | Sinais | Trades | Liquido | Fator | Rebaix. | Treino | Teste |', '|:--|--:|--:|--:|--:|--:|--:|--:|']
        for l in T['carteiras'][gk] + T['combina'][gk][1:]:
            s = l['stats']
            L.append(f"| {l['nome']} | {n(l['frac'] * 100, 0)}% | {n(s['trades'])} | {rs(s['liquido'])} | {n(s['fator_lucro'], 2)} | "
                     f"{rs(-s['dd_max'])} | {rs(l['is_']['liquido'])} | {rs(l['oos']['liquido'])} |")
        L += ['', '**Estabilidade por terco do periodo** (R$/trade do grupo, entre parenteses o resto)', '',
              '| Grupo | Sinais | ' + ' | '.join(t['rot'] for t in M['tercos']) + ' |', '|:--|--:|--:|--:|--:|']
        for l in T['estabilidade']:
            L.append(f"| {l['nome']} | {n(l['frac'] * 100, 0)}% | " +
                     ' | '.join(f"{rs(b[gk]['ev'], 1)} ({rs(b[gk]['resto'], 1)})" for b in l['blocos']) + ' |')
        L.append('')
    L += ['## Conclusoes', '',
          f"1. **Em 20 candles a hipotese se inverte.** Os sinais em que o preco ficou todo de um lado da EMA (nenhum cruzamento) sao "
          f"{n(h0['r400']['n'])} ({n(h0['r400']['frac'] * 100, 0)}%) e deram {rs(h0['r400']['ev'], 1)} por trade contra {rs(h0['r400']['resto'], 1)} do resto no alvo 400 "
          f"({rs(h0['claude']['ev'], 1)} x {rs(h0['claude']['resto'], 1)} no CLAUDE.md), negativos no treino e no teste. A faixa de 2 a 4 cruzamentos e a melhor; "
          f"em carteira {rs(c0['r400']['stats']['liquido'])} -> {rs(ccz['r400']['stats']['liquido'])}.",
          f"2. **Em 5 candles a hipotese vale.** O quintil de baixo da pureza de 5 (candles repartidos entre os dois lados) e negativo no treino e no teste "
          f"nas duas gestoes. Filtrar por pureza 5 >= 0,7 corta {n((1 - cp5['r400']['frac']) * 100, 0)}% dos sinais e melhora as duas carteiras "
          f"({rs(c0['r400']['stats']['liquido'])} -> {rs(cp5['r400']['stats']['liquido'])}, {rs(c0['claude']['stats']['liquido'])} -> {rs(cp5['claude']['stats']['liquido'])}).",
          f"3. **O corte mais firme e o cruzamento das duas coisas**: 0 ou 1 cruzamento da EMA em 20 candles E distancia media acima de 177 pts. "
          f"{n(e_canto['frac'] * 100, 0)}% dos sinais, negativo nos tres tercos do periodo e nas duas gestoes. Descartando so esse canto: "
          f"{rs(c0['r400']['stats']['liquido'])} -> {rs(cfo['r400']['stats']['liquido'])} e {rs(c0['claude']['stats']['liquido'])} -> {rs(cfo['claude']['stats']['liquido'])}.",
          '4. **A somatoria com sinal nao separa nada.** De que lado da media o preco ficou e indiferente; o que importa e o formato do caminho '
          '(quantos cruzamentos, a que distancia).',
          f"5. **Nao e um filtro independente.** \"Poucos cruzamentos\" e \"longe da media\" tem correlacao de posto {n(T['corr']['cruz_20p']['kc_10'], 2)} e "
          f"{n(T['corr']['abs_20p']['kc_10'], 2)} com o quanto o preco passou da Keltner 2,5: e outra forma de medir movimento esticado, que o `impulso.html` "
          'ja tinha apontado. Somado a consolidacao de 100 candles o ganho fica pequeno.',
          '', 'Reproduzir: `python oscila.py && python oscila_rel.py`.', '']
    return '\n'.join(L)


def main():
    dados = dict(carteiras={g: [dict(nome=l['nome'], eq=l['eq']) for l in T['carteiras'][g]] for g in T['carteiras']},
                 combina={g: [dict(nome=l['nome'], eq=l['eq']) for l in T['combina'][g]] for g in T['combina']})
    html = ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Oscilacao na EMA 21</title><style>{CSS}{CSS_EXTRA}</style></head><body>'
            '<nav class="indice"><div class="wrap"><ul>' + ''.join(f'<li><a href="#{a}">{r}</a></li>' for a, r in MENU) +
            '</ul></div></nav><div class="wrap">' + corpo() + '</div>'
            '<button class="tema" id="btema" title="Alternar tema" aria-label="Alternar tema">&#9681;</button>'
            '<script>' + JS.replace('__T__', json.dumps(dados, ensure_ascii=False)) + '</script></body></html>')
    open(os.path.join(BASE, 'oscila.html'), 'w', encoding='utf-8').write(html)
    open(os.path.join(BASE, 'OSCILA.md'), 'w', encoding='utf-8').write(markdown())
    print('oscila.html', round(len(html) / 1e6, 2), 'MB')


if __name__ == '__main__':
    main()
