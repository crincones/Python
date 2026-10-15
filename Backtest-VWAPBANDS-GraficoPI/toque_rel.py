# -*- coding: utf-8 -*-
"""Relatorio: 1o/2o toque na VWAP band -> toque.html + TOQUE.md
(rodar depois de toque_estudo.py). Visual e trade a trade vem do vwap_rel.py."""
import json
import os

import vbase as V
from relatorio import CSS
from textos import n, rs, cls
from vwap_rel import (CSS_EXTRA, JS, VENDOR, GS, candles, ev, pc, por_gestao, tab_faixa, terco_tag, trad_lin, txt)

BASE = V.BASE
SAIDA = os.path.join(BASE, 'saida')
T = json.load(open(os.path.join(SAIDA, 'toque.json'), encoding='utf-8'))
TR = json.load(open(os.path.join(SAIDA, 'toque_trades.json'), encoding='utf-8'))
M = T['meta']
MENU = [('resposta', 'Resposta'), ('regra', 'A regra'), ('grade', 'Banda x toque'), ('variantes', 'Variantes'),
        ('dentro', 'Dentro do 1º/2º toque'), ('carteira', 'Carteira'), ('robustez', 'Robustez'),
        ('kline', 'Trade a trade'), ('conclusao', 'Conclusão')]


def g(k, fk, toque):
    return next(l for l in T['grade'][f'{k}_{fk}']['lin'] if l['faixa'].startswith(toque))


def cart(ck, gk):
    return next(l for l in T['carteiras'][gk] if l['k'] == ck)


def hip(nome, gk='r300'):
    return next(r for r in T['hip'][gk] if r['nome'].startswith(nome))


def boot(nome_ini, gk):
    return next(r for r in T['bootstrap'] if r['cand'].startswith(nome_ini) and r['gk'] == gk)


def fx(chave, faixa):
    return next(l for l in T['dentro'][chave]['lin'] if l['faixa'].startswith(faixa))


def lista(chave):
    """linhas de 'regra', 'comb', 'reset' -> formato de faixa."""
    return [dict(l, faixa=txt(l['faixa'])) for l in T[chave]]


def tab_hip(gk):
    H = sorted(T['hip'][gk], key=lambda r: -(r['ev'] - r['resto']))
    h = ('<div class="tab"><table><thead><tr><th>Grupo</th><th>Sinais</th><th>R$/trade</th><th>Resto</th>'
         '<th>Treino (resto)</th><th>Teste (resto)</th><th>Terços: grupo (resto)</th><th>t</th><th>Percentil</th>'
         '</tr></thead><tbody>')
    for r in H:
        ter = ' · '.join(f"{ev(a, 0)} <span class=\"nota\">({rs(b, 0)})</span>" for a, b in zip(r['ter'], r['ter_resto']))
        h += (f"<tr><td>{txt(r['nome'])}</td><td>{n(r['n'])}</td><td><b>{ev(r['ev'])}</b></td><td>{ev(r['resto'])}</td>"
              f"<td>{ev(r['ev_is'])} <span class=\"nota\">({rs(r['resto_is'], 1)})</span></td>"
              f"<td>{ev(r['ev_oos'])} <span class=\"nota\">({rs(r['resto_oos'], 1)})</span></td>"
              f"<td>{ter} {terco_tag(r['ter'], r['ter_resto'])}</td><td>{n(r['t'], 2)}</td><td>{n(r['pct'], 0)}</td></tr>")
    return h + '</tbody></table></div>'


def tab_cart(gk, gid):
    h = ('<div class="tab"><table><thead><tr><th>Regra</th><th>Trades</th><th>Pregões com trade</th><th>Líquido</th>'
         '<th>Fator</th><th>Rebaixamento</th><th>Treino</th><th>Teste</th><th>Alvo atravessando 5 pts</th></tr></thead><tbody>')
    for l in T['carteiras'][gk]:
        s = l['stats']
        h += (f"<tr class=\"{'dest' if l['k'] in ('b1e', 'b2e') else ''}\"><td>{txt(l['nome'])}</td><td>{n(s['trades'])}</td>"
              f"<td>{n(s['dias'])}</td><td>{ev(s['liquido'], 0)}</td><td>{n(s['fator_lucro'], 2)}</td><td>{rs(-s['dd_max'])}</td>"
              f"<td>{ev(l['is_'].get('liquido'), 0)}</td><td>{ev(l['oos'].get('liquido'), 0)}</td><td>{ev(l['atravessa'], 0)}</td></tr>")
    return (h + f'</tbody></table></div><div class="card"><div class="leg" id="{gid}_leg"></div>'
            f'<div class="graf" id="{gid}"></div></div>')


def tab_stops():
    h = ('<div class="tab"><table><thead><tr><th>Regra</th><th>Stop</th><th>Alvo</th><th>R$/trade</th><th>Treino</th>'
         '<th>Teste</th><th>Carteira</th><th>Fator</th></tr></thead><tbody>')
    ult = None
    for r in T['stops']:
        nm = txt(r['cand']) if r['cand'] != ult else ''
        ult = r['cand']
        h += (f"<tr><td>{nm}</td><td>{r['stop']}</td><td>{r['alvo']}</td><td><b>{ev(r['ev'])}</b></td><td>{ev(r['ev_is'])}</td>"
              f"<td>{ev(r['ev_oos'])}</td><td>{ev(r['liq'], 0)}</td><td>{n(r['fl'], 2)}</td></tr>")
    return h + '</tbody></table></div>'


def tab_boot():
    cands = []
    for r in T['bootstrap']:
        if r['cand'] not in cands:
            cands.append(r['cand'])
    h = ('<div class="tab"><table><thead><tr><th>Regra</th>' + ''.join(f'<th>{r}</th>' for _, r in GS)
         + '</tr></thead><tbody>')
    for c in cands:
        h += f'<tr><td>{txt(c)}</td>'
        for gk, _ in GS:
            b = next(r for r in T['bootstrap'] if r['cand'] == c and r['gk'] == gk)
            h += f"<td>{pc(b['p_prejuizo'], 1)} <span class=\"nota\">(mediana {rs(b['p50'])})</span></td>"
        h += '</tr>'
    return h + ('</tbody></table></div><p class="nota">Chance de terminar no prejuízo sorteando os pregões com reposição '
                '(4.000 sorteios), e entre parênteses o líquido mediano.</p>')


def bloco(chave):
    F = T['dentro'][chave]
    return f'<h3>{txt(F["rot"])}</h3>' + por_gestao(lambda gk: tab_faixa(trad_lin(F['lin']), gk))


def grade_banda(k):
    out = f'<h3>Banda {k}</h3>'
    for fk in ('qualquer', 'semrej', 'exaust', 'E', 'rej'):
        out += (f'<p class="nota" style="margin:10px 0 0"><b>{txt(M["filtros"][fk])}</b> (primeira do toque)</p>'
                + por_gestao(lambda gk, fk=fk: tab_faixa(trad_lin(T['grade'][f'{k}_{fk}']['lin']), gk, 'Toque do dia')))
    return out


def corpo():
    ref = T['ref'][0]
    q12 = g(1, 'qualquer', '1o ou'); q3 = g(1, 'qualquer', '3o'); q1 = g(1, 'qualquer', '1o toque'); q2 = g(1, 'qualquer', '2o toque')
    e12 = g(1, 'E', '1o ou'); e3 = g(1, 'E', '3o'); e1 = g(1, 'E', '1o toque'); e2 = g(1, 'E', '2o toque')
    b2 = g(2, 'qualquer', '1o ou'); b2E = g(2, 'E', '1o ou')
    cq = {gk: cart('b1q', gk) for gk, _ in GS}; ce = {gk: cart('b1e', gk) for gk, _ in GS}
    ce1 = {gk: cart('b1e1', gk) for gk, _ in GS}; cb2 = {gk: cart('b2e', gk) for gk, _ in GS}
    cp = {gk: cart('b1p', gk) for gk, _ in GS}
    c2 = {gk: cart('b1c2', gk) for gk, _ in GS}
    hp50 = hip('Pavio > 50'); hfr = hip('Falso'); hemp = hip('Empurrao de 4+')
    h = [f'''
<h1>1º e 2º toque na VWAP Band</h1>
<p class="sub">Continuação do estudo de reversões nas VWAP Bands · WINFUT PI 20 · {M['pregoes']} pregões ({M['inicio'][8:]}/{M['inicio'][5:7]} a {M['fim'][8:]}/{M['fim'][5:7]}) ·
bandas da VWAP Band do Profit (1/3 %, 2/3 % e 1 % da VWAP) · 6 contratos, R$ 0,50 por contrato · treino até {M['corte'][8:]}/{M['corte'][5:7]} ·
uma entrada por toque, só a primeira virada formada encostada na banda</p>

<h2 id="resposta">Resposta</h2>
<div class="kpis">
<div class="kpi"><div class="r">Banda 1, 1º/2º toque, 1ª virada · alvo 300</div><div class="v {cls(q12['r300']['ev'])}">{rs(q12['r300']['ev'], 1)}<span class="nota"> /trade</span></div></div>
<div class="kpi"><div class="r">Todas as viradas nas bandas</div><div class="v {cls(ref['r300']['ev'])}">{rs(ref['r300']['ev'], 1)}<span class="nota"> /trade</span></div></div>
<div class="kpi"><div class="r">Banda 1, 1ª exaustão limpa · CLAUDE.md</div><div class="v {cls(e12['claude']['ev'])}">{rs(e12['claude']['ev'], 1)}<span class="nota"> /trade</span></div></div>
<div class="kpi"><div class="r">Banda 2, 1ª exaustão limpa · alvo 300</div><div class="v {cls(b2E['r300']['ev'])}">{rs(b2E['r300']['ev'], 1)}<span class="nota"> /trade</span></div></div>
<div class="kpi"><div class="r">Banda 2, 1ª virada qualquer</div><div class="v {cls(b2['r300']['ev'])}">{rs(b2['r300']['ev'], 1)}<span class="nota"> /trade</span></div></div>
</div>
<div class="card ruim"><b>Só limitar ao 1º/2º toque não dá vantagem.</b> A 1ª virada encostada na banda 1, no 1º ou 2º toque do dia, com uma entrada por toque,
dá {n(q12['n'])} trades e {rs(q12['r300']['ev'], 1)} por trade com alvo 300 (treino {rs(q12['r300']['ev_is'], 1)}, teste {rs(q12['r300']['ev_oos'], 1)}).
O número do toque, sozinho, não ordena: o 1º toque dá {rs(q1['r300']['ev'], 1)}, o 2º {rs(q2['r300']['ev'], 1)}. Com a banda a 1/3 % da VWAP o preço raramente
volta a ela no mesmo dia: do 3º toque em diante são só {n(q3['n'])} casos.</div>
<div class="card ok"><b>O que separa é o padrão da virada.</b> Dentro dos 1º/2º toques da banda 1:
<ul>
<li><b>Empurrão longo</b>: a virada que vem depois de 4 ou mais candles seguidos até a banda dá {rs(hemp['ev'], 1)} por trade, contra {rs(hemp['resto'], 1)}
das que vêm depois de empurrão curto.</li>
<li><b>Pavio grande no candle de virada é ruim</b>: acima de 50 pontos dá {rs(hp50['ev'], 1)} contra {rs(hp50['resto'], 1)} dos demais, negativo nos três terços.</li>
<li><b>Esperar a exaustão limpa dentro do toque</b> (4+ candles e virada sem pavio de rejeição): {n(e12['n'])} trades, {rs(e12['r300']['ev'], 1)} por trade com alvo 300
e {rs(e12['claude']['ev'], 1)} com a gestão do CLAUDE.md, positiva no treino e no teste. Na carteira com a gestão do CLAUDE.md: {rs(ce['claude']['stats']['liquido'])},
fator {n(ce['claude']['stats']['fator_lucro'], 2)}, rebaixamento {rs(-ce['claude']['stats']['dd_max'])}. Com alvo 300 o fator cai para {n(ce['r300']['stats']['fator_lucro'], 2)}.</li>
<li>O falso rompimento (fechou fora da banda e voltou) não se destaca ({rs(hfr['ev'], 1)}).</li>
</ul></div>
<div class="card ok"><b>Na banda 2 a exaustão limpa é o melhor caso.</b> A 1ª exaustão limpa do 1º/2º toque da banda 2 dá {rs(b2E['r300']['ev'], 1)} por trade
em {n(b2E['n'])} trades, positiva nos três terços. Na carteira fica positiva nas quatro saídas, no treino e no teste: fator {n(cb2['r300']['stats']['fator_lucro'], 2)}
com alvo 300, {n(cb2['r500']['stats']['fator_lucro'], 2)} com alvo 500, {n(cb2['vw']['stats']['fator_lucro'], 2)} com alvo na VWAP. É a mesma conclusão do estudo geral
(exaustão limpa mais forte da banda 2 em diante), com pouca amostra: cerca de um trade a cada dois pregões. Sem o filtro de exaustão, a 1ª virada na
banda 2 é negativa ({rs(b2['r300']['ev'], 1)}).</div>
<div class="card"><b>Saída.</b> Na banda 1, a gestão do CLAUDE.md é a única que deixa as regras claramente positivas; alvo 500 e alvo na VWAP ficam negativos.
Na banda 2 é o contrário: o preço vai mais longe e o alvo 500 ({rs(cb2['r500']['stats']['liquido'])}) e o alvo na VWAP ({rs(cb2['vw']['stats']['liquido'])}) superam
o alvo 300 ({rs(cb2['r300']['stats']['liquido'])}).</div>
''']

    h.append(f'''
<h2 id="regra">A regra testada</h2>
<div class="card">
<p><b>Toque.</b> O 1º toque da banda k no pregão começa quando o preço chega nela, e o toque só termina quando o preço volta até a banda de dentro
(para a banda 1, até a VWAP). Contado por banda e por lado: a banda de cima e a de baixo têm contagens separadas.
Sinais e toques valem desde a abertura.</p>
<p><b>Uma entrada por toque.</b> Dentro do 1º ou do 2º toque, entra na primeira virada formada <b>encostada na banda</b>. Encostada quer dizer que
algum candle do padrão (último candle do empurrão ou o candle contra) tem a máxima (venda) ou a mínima (compra) na banda ou além. Se o trade dá stop,
não há nova entrada no mesmo toque; a próxima chance é o toque seguinte.</p>
<p><b>Duas formas de exigir um padrão:</b> <b>esperar o padrão</b> (entra na primeira virada do toque que tenha o padrão; é o principal) ou
<b>só a 1ª virada</b> (se a 1ª virada do toque não tiver o padrão, perde o toque).</p>
<p class="nota">Encostar na banda quase não restringe nada. Em mais de 99% dos sinais de 1º candle contra do estudo anterior, o próprio candle de virada
já encostava na banda 1: ele abre onde o último candle de alta fechou, colado na máxima. As três definições de "tocando" (só o candle do gatilho;
qualquer candle do padrão; só o empurrão) deram os mesmos trades (tabela em Variantes). O que muda de fato em relação ao estudo anterior é entrar
<b>uma vez por toque</b> e <b>só no 1º/2º toque</b>.</p>
</div>
<div class="leg"><span>Seletor de saída das tabelas:</span></div>
<div class="abas" id="gsel">''' + ''.join(f'<button data-g="{gk}" class="{"on" if gk == "r300" else ""}">{r}</button>' for gk, r in GS) + '</div>')

    h.append(f'''
<h2 id="grade">Banda x número do toque x padrão</h2>
<p>Gatilho de 1º candle contra, primeira virada com o padrão dentro de cada toque. Referência, todas as viradas nas bandas do estudo anterior:
{rs(ref['r300']['ev'], 1)} por trade com alvo 300.</p>
{grade_banda(1)}{grade_banda(2)}{grade_banda(3)}''')

    h.append(f'''
<h2 id="variantes">Variantes da regra (banda 1 salvo indicação, 1º/2º toque)</h2>
<h3>O que é "tocar a banda"</h3>
{por_gestao(lambda gk: tab_faixa(lista('regra'), gk, 'Regra'))}
<h3>Esperar o padrão, ou só a 1ª virada · 1º ou 2º candle contra · banda 1 ou 2</h3>
{por_gestao(lambda gk: tab_faixa(lista('comb'), gk, 'Variante'))}
<p class="nota">A virada de 2 candles na banda 1 fica negativa ({rs(c2['r300']['stats']['liquido'])} na carteira com alvo 300).</p>
<h3>Quando termina um toque nas bandas 2 e 3</h3>
{por_gestao(lambda gk: tab_faixa(lista('reset'), gk, 'Definição'))}''')

    h.append(f'''
<h2 id="dentro">Dentro do 1º/2º toque da banda 1: o que separa as viradas</h2>
<p>Os {n(q12['n'])} trades da 1ª virada encostada, separados por característica. Cada grupo contra o resto:</p>
{por_gestao(tab_hip)}
{bloco('padrao')}{bloco('pav')}{bloco('emp')}{bloco('ang')}{bloco('nivel')}{bloco('hora')}{bloco('dist')}{bloco('lado')}
<p class="nota">São amostras pequenas: grupos com menos de 50 trades podem mudar de sinal com poucos trades a mais.</p>''')

    h.append(f'''
<h2 id="carteira">Carteira</h2>
<p>Uma posição por vez, 6 contratos, custo incluído. O gráfico mostra o patrimônio por pregão das quatro regras principais.</p>
{por_gestao(lambda gk: tab_cart(gk, 'eq_' + gk))}''')

    h.append(f'''
<h2 id="robustez">Robustez</h2>
<h3>Stop e alvo</h3>
{tab_stops()}
<h3>Sorteio de pregões</h3>
{tab_boot()}
<div class="card alerta"><b>Limites.</b> As regras que sobraram têm de {n(cb2['r300']['stats']['trades'])} a {n(ce['r300']['stats']['trades'])} trades em
{M['pregoes']} pregões, e os filtros foram escolhidos olhando esses mesmos dados. Na banda 1 o resultado depende da gestão (só a do CLAUDE.md fica bem positiva).
Na banda 2 a exaustão limpa passou em todas as saídas, mas são {n(cb2['r300']['stats']['trades'])} trades. A direção é consistente com o estudo geral; o
tamanho do ganho é incerto.</div>''')

    h.append('''
<h2 id="kline">Trade a trade</h2>
<p>VWAP (linha cheia) e bandas a 1/3 %, 2/3 % e 1 % da VWAP (tracejadas). Faixa azul: empurrão até a banda e candle de virada. Setas ← → navegam.</p>
<div class="card">
<div class="kbar"><select id="kvar"></select><select id="kfiltro"><option value="todos">Todos</option><option value="ganho">Ganhos</option>
<option value="perda">Perdas</option><option value="t12">1º/2º toque</option></select>
<button class="btn" id="kant">&larr;</button><select id="ksel"></select><button class="btn" id="kprox">&rarr;</button></div>
<div class="kinfo" id="kinfo"></div>
<div id="kchart"></div>
</div>''')

    h.append(f'''
<h2 id="conclusao">Conclusão</h2>
<div class="card ok"><ol>
<li><b>Limitar ao 1º/2º toque, sozinho, não dá vantagem</b> ({rs(q12['r300']['ev'], 1)} por trade na banda 1). O número do toque não ordena o resultado.</li>
<li><b>O que funciona é esperar a exaustão limpa dentro do toque</b>: 4+ candles até a banda e virada sem pavio de rejeição.
<ul><li>Banda 1: {n(ce['r300']['stats']['trades'])} trades, bom só com a gestão do CLAUDE.md ({rs(ce['claude']['stats']['liquido'])}, fator
{n(ce['claude']['stats']['fator_lucro'], 2)}).</li>
<li>Banda 2: {n(cb2['r300']['stats']['trades'])} trades, positiva em todas as saídas, melhor com alvo 500 ou na VWAP (fator {n(cb2['r500']['stats']['fator_lucro'], 2)} e
{n(cb2['vw']['stats']['fator_lucro'], 2)}).</li></ul></li>
<li><b>Evitar</b> a virada com pavio acima de 50 pontos e a que vem depois de empurrão curto (menos de 4 candles).</li>
<li><b>Descartar:</b> a 1ª virada sem filtro, em qualquer banda; a virada de 2 candles; alvo 500 e alvo na VWAP na banda 1.</li>
</ol></div>
<p class="nota">Arquivos: toque_estudo.py (estudo → saida/toque.json), toque_rel.py (este relatório e TOQUE.md). Usa o vbase.py e o vwap_estudo.py.</p>''')
    return '\n'.join(h)


def markdown():
    ref = T['ref'][0]
    s = f"""# 1º e 2º toque na VWAP Band

Continuação de `VWAP.md`. WINFUT PI 20, {M['pregoes']} pregões, 6 contratos, R$ 0,50 por contrato, stop 100. Treino até {M['corte']}.
Regra: dentro do 1º ou 2º toque do dia na banda (o toque termina quando o preço volta à banda de dentro; na banda 1, à VWAP), entra
na primeira virada formada encostada na banda; uma entrada por toque. Detalhes, gráficos e trade a trade em `toque.html`.

Referência (todas as viradas nas bandas, estudo anterior): {rs(ref['r300']['ev'], 1)} por trade com alvo 300.

## Banda x toque x padrão (R$/trade)

"""
    for k in (1, 2, 3):
        for fk in ('qualquer', 'semrej', 'E', 'rej'):
            s += f"**Banda {k} · {txt(M['filtros'][fk])}**\n\n| Toque | Trades | Alvo 300 | Alvo 500 | Alvo VWAP | CLAUDE.md | Treino (300) | Teste (300) |\n|:--|--:|--:|--:|--:|--:|--:|--:|\n"
            for l in T['grade'][f'{k}_{fk}']['lin']:
                s += (f"| {txt(l['faixa'])} | {n(l['n'])} | " + ' | '.join(rs(l[gk]['ev'], 1) for gk, _ in GS)
                      + f" | {rs(l['r300']['ev_is'], 1)} | {rs(l['r300']['ev_oos'], 1)} |\n")
            s += '\n'
    s += '## Dentro do 1º/2º toque da banda 1 (1ª virada, alvo 300)\n\n| Grupo | Trades | R$/trade | Resto | Treino | Teste | Percentil |\n|:--|--:|--:|--:|--:|--:|--:|\n'
    for r in sorted(T['hip']['r300'], key=lambda r: -(r['ev'] - r['resto'])):
        s += (f"| {txt(r['nome'])} | {n(r['n'])} | {rs(r['ev'], 1)} | {rs(r['resto'], 1)} | {rs(r['ev_is'], 1)} | "
              f"{rs(r['ev_oos'], 1)} | {n(r['pct'], 0)} |\n")
    for gk, r in GS:
        s += f'\n## Carteira: {r}\n\n| Regra | Trades | Líquido | Fator | Rebaix. | Treino | Teste |\n|:--|--:|--:|--:|--:|--:|--:|\n'
        for l in T['carteiras'][gk]:
            st = l['stats']
            s += (f"| {txt(l['nome'])} | {n(st['trades'])} | {rs(st['liquido'])} | {n(st['fator_lucro'], 2)} | {rs(-st['dd_max'])} | "
                  f"{rs(l['is_'].get('liquido'))} | {rs(l['oos'].get('liquido'))} |\n")
    s += '\n## Stops\n\n| Regra | Stop | Alvo | R$/trade | Treino | Teste | Carteira |\n|:--|:--|:--|--:|--:|--:|--:|\n'
    for r in T['stops']:
        s += f"| {txt(r['cand'])} | {r['stop']} | {r['alvo']} | {rs(r['ev'], 1)} | {rs(r['ev_is'], 1)} | {rs(r['ev_oos'], 1)} | {rs(r['liq'])} |\n"
    s += ('\n**Limites**: poucas dezenas a poucas centenas de trades por regra; filtros escolhidos nos mesmos dados. Na banda 1 só a gestão do '
          'CLAUDE.md deixa a exaustão limpa bem positiva; na banda 2 ela passou em todas as saídas, com 74 trades. O tamanho do ganho é incerto.\n')
    return s


def main():
    pick = [('b1q', '1ª virada, banda 1'), ('b1p', 'Pavio ≤ 50, banda 1'), ('b1e', 'Exaustão limpa, banda 1'), ('b2e', 'Exaustão limpa, banda 2')]
    EQ = {gk: [dict(nome=nm, y=cart(ck, gk)['eq_dia']) for ck, nm in pick] for gk, _ in GS}
    TRn = {k: dict(v, nome=txt(v['nome'])) for k, v in TR.items()}
    with open(VENDOR, encoding='utf-8') as f:
        kc = f.read()
    js = (JS.replace('__TRADES__', json.dumps(TRn, ensure_ascii=False))
          .replace('__CANDLES__', json.dumps(candles(), separators=(',', ':')))
          .replace('__EQ__', json.dumps(EQ)).replace('__DIAS__', json.dumps(M['dias'])))
    html = ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Primeiros toques na VWAP Band</title>'
            f'<style>{CSS}{CSS_EXTRA}</style></head><body>'
            '<nav class="indice"><div class="wrap"><ul>'
            + ''.join(f'<li><a href="#{a}">{r}</a></li>' for a, r in MENU) +
            '</ul></div></nav><div class="wrap">' + corpo() + '</div>'
            '<button class="tema" id="btema" title="Alternar tema" aria-label="Alternar tema">&#9681;</button>'
            f'<script>{kc}</script><script>{js}</script></body></html>')
    with open(os.path.join(BASE, 'toque.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    with open(os.path.join(BASE, 'TOQUE.md'), 'w', encoding='utf-8') as f:
        f.write(markdown())
    print('toque.html', round(len(html) / 1e6, 1), 'MB')


if __name__ == '__main__':
    main()
