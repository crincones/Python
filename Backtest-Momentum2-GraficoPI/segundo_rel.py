# -*- coding: utf-8 -*-
"""Relatorio dos segundos toques na EMA 21: segundo.html + SEGUNDO_TOQUE.md
(rodar depois de segundo.py)."""
import json
import os

import engine as E
from relatorio import CSS
from textos import n, rs, cls

BASE = E.BASE
T = json.load(open(os.path.join(BASE, 'saida', 'segundo.json'), encoding='utf-8'))
NOME_G = {'claude': 'Gestao do CLAUDE.md (stop 100, parcial +100, alvo 300)', 'r400': 'Stop 100 / alvo 400 sem parcial'}
CURTO = {'claude': 'CLAUDE.md', 'r400': 'Stop 100 / alvo 400'}
FAMS = [('ordem', 'Ordem do recuo na perna do MACD'), ('nivel', 'Nivel do recuo contra o recuo anterior'),
        ('sinal', 'O recuo anterior teve sinal?'), ('perto', 'Distancia entre a entrada atual e a do sinal anterior'),
        ('res', 'Resultado do sinal anterior (se ja tinha fechado)')]
IMP0 = int(T['meta']['imp_padrao'])


def g(imp, gk, ini):
    return next(r for r in T['grupos'][f'{imp}|{gk}'] if r['nome'].startswith(ini))


def cart(gk, ini):
    return next(l for l in T['carteiras'][gk] if l['nome'].startswith(ini))


def tag(r):
    if r.get('resto_is') is None or r.get('resto_oos') is None or r['n_is'] < 25 or r['n_oos'] < 15:
        return '<span class="nota">poucos</span>'
    a = r['ev_is'] - r['resto_is']; b = r['ev_oos'] - r['resto_oos']
    if a > 0 and b > 0:
        return '<span class="tag pos">melhor nos dois</span>'
    if a < 0 and b < 0:
        return '<span class="tag neg">pior nos dois</span>'
    return '<span class="tag">inverte</span>'


def tab_grupos(imp, gk):
    L = T['grupos'][f'{imp}|{gk}']
    h = ''
    for fam, tit in FAMS:
        rows = [r for r in L if r['fam'] == fam]
        if not rows:
            continue
        h += (f'<h3>{tit}</h3><p class="nota">Comparado com: {rows[0]["base"]}.</p><div class="tab"><table><thead><tr><th>Grupo</th><th>Sinais</th>'
              '<th>R$/trade</th><th>Resto</th><th>Treino (resto)</th><th>Teste (resto)</th><th>Stop cheio %</th><th>Stop % treino / teste (resto)</th>'
              '<th>t</th><th>Percentil</th><th>Treino x teste</th></tr></thead><tbody>')
        for r in rows:
            h += (f"<tr><td>{r['nome']}</td><td>{n(r['n'])}</td><td class=\"{cls(r['ev'])}\">{rs(r['ev'], 1)}</td><td class=\"{cls(r['resto'])}\">{rs(r['resto'], 1)}</td>"
                  f"<td><span class=\"{cls(r['ev_is'])}\">{rs(r['ev_is'], 1)}</span> <span class=\"nota\">({rs(r['resto_is'], 1)})</span></td>"
                  f"<td><span class=\"{cls(r['ev_oos'])}\">{rs(r['ev_oos'], 1)}</span> <span class=\"nota\">({rs(r['resto_oos'], 1)})</span></td>"
                  f"<td>{n(r['falha'], 0)}% <span class=\"nota\">({n(r['falha_resto'], 0)}%)</span></td>"
                  f"<td>{n(r['falha_is'], 0)}% / {n(r['falha_oos'], 0)}% <span class=\"nota\">({n(r['falha_resto_is'], 0)}% / {n(r['falha_resto_oos'], 0)}%)</span></td>"
                  f"<td>{n(r['t'], 2)}</td><td>{n(r['pct'], 0)}</td><td>{tag(r)}</td></tr>")
        h += '</tbody></table></div>'
    return h


def tab_sens():
    chaves = ['2o recuo da perna', 'Sinal anterior perto', 'Entrada 1 tijolo', 'Entrada no MESMO', 'Recuo passou', 'Sinal anterior ainda aberto', 'Sinal anterior tomou STOP']
    h = ('<div class="tab"><table><thead><tr><th>Grupo</th><th>Gestao</th>' +
         ''.join(f'<th>Impulso &ge; {int(i)} pts<br><span class="nota">treino / teste (resto)</span></th>' for i in T['meta']['imps']) + '</tr></thead><tbody>')
    for ch in chaves:
        for gk in ('r400', 'claude'):
            h += f'<tr><td>{g(IMP0, gk, ch)["nome"]}</td><td>{CURTO[gk]}</td>'
            for imp in T['meta']['imps']:
                try:
                    r = g(int(imp), gk, ch)
                    h += (f"<td><span class=\"{cls(r['ev_is'] - (r['resto_is'] or 0))}\">{rs(r['ev_is'], 1)}</span> <span class=\"nota\">({rs(r['resto_is'], 1)})</span> / "
                          f"<span class=\"{cls(r['ev_oos'] - (r['resto_oos'] or 0))}\">{rs(r['ev_oos'], 1)}</span> <span class=\"nota\">({rs(r['resto_oos'], 1)})</span>"
                          f"<br><span class=\"nota\">{n(r['n'])} sinais</span></td>")
                except StopIteration:
                    h += '<td>-</td>'
            h += '</tr>'
    return h + ('</tbody></table></div><p class="nota">Verde / vermelho = melhor / pior que o resto naquele periodo. '
                'A classificacao muda com o impulso minimo, entao as colunas nao sao amostras independentes.</p>')


def tab_cart(gk):
    h = ('<div class="tab"><table><thead><tr><th>Filtro</th><th>Trades</th><th>Liquido</th><th>Fator</th><th>Rebaixamento</th><th>Treino</th><th>Teste</th>'
         '<th>Atravessar 5 pts</th><th>Pregoes +</th></tr></thead><tbody>')
    for i, l in enumerate(T['carteiras'][gk]):
        s = l['stats']
        h += (f"<tr class=\"{'dest' if i == 0 else ''}\"><td>{l['nome']} <span class=\"nota\">({n(l['frac'] * 100, 0)}%)</span></td><td>{n(s['trades'])}</td>"
              f"<td class=\"{cls(s['liquido'])}\">{rs(s['liquido'])}</td><td>{n(s['fator_lucro'], 2)}</td><td>{rs(-s['dd_max'])}</td>"
              f"<td class=\"{cls(l['is_']['liquido'])}\">{rs(l['is_']['liquido'])}</td><td class=\"{cls(l['oos']['liquido'])}\">{rs(l['oos']['liquido'])}</td>"
              f"<td class=\"{cls(l['atravessa'])}\">{rs(l['atravessa'])}</td><td>{n(s['dias_pos'], 0)}%</td></tr>")
    return h + f'</tbody></table></div><div class="card"><div class="graf" id="g_{gk}"></div></div>'


def abas(alvo, itens, ini):
    return (f'<div class="abas" data-alvo="{alvo}">' +
            ''.join(f'<button data-k="{k}" class="{"on" if k == ini else ""}">{r}</button>' for k, r in itens) + '</div>')


def corpo():
    M = T['meta']; D = T['dist'][str(IMP0)]
    s2 = {gk: g(IMP0, gk, '2o recuo da perna') for gk in ('r400', 'claude')}
    pt = {gk: g(IMP0, gk, 'Sinal anterior perto') for gk in ('r400', 'claude')}
    t1 = {gk: g(IMP0, gk, 'Entrada 1 tijolo') for gk in ('r400', 'claude')}
    mp = {gk: g(IMP0, gk, 'Entrada no MESMO') for gk in ('r400', 'claude')}
    ab = {gk: g(IMP0, gk, 'Sinal anterior ainda aberto') for gk in ('r400', 'claude')}
    c0 = {gk: cart(gk, 'sem filtro') for gk in ('r400', 'claude')}
    c2 = {gk: cart(gk, 'sem o 2o recuo') for gk in ('r400', 'claude')}
    cp = {gk: cart(gk, 'sem o sinal perto') for gk in ('r400', 'claude')}
    t1_200 = g(200, 'r400', 'Entrada 1 tijolo'); t1_400 = g(400, 'r400', 'Entrada 1 tijolo')
    GI = [(str(int(i)), f'Impulso &ge; {int(i)} pts') for i in M['imps']]
    G2 = [('r400', 'Stop 100 / alvo 400'), ('claude', 'Gestao CLAUDE.md')]
    blocos = ''.join(f'<div class="bl" data-imp="{int(i)}" data-g="{gk}"{"" if (int(i), gk) == (IMP0, "r400") else " hidden"}>{tab_grupos(int(i), gk)}</div>'
                     for i in M['imps'] for gk in ('r400', 'claude'))
    return f"""
<h1>Segundo toque na EMA 21</h1>
<p class="sub">Setup EMA 21 + HullRetracao_Azul + MACD &middot; WINFUT PI 20, {M['pregoes']} pregoes ({M['inicio']} a {M['fim']}) &middot; {n(M['sinais'])} sinais &middot;
entrada seca no fechamento &middot; 6 contratos, R$ 0,50 por contrato &middot; treino ate {M['corte']}, teste depois</p>

<section id="resumo"><h2>Resposta curta</h2>
<div class="kpis">
<div class="kpi"><div class="r">1o / 2o / 3o+ recuo da perna &middot; sem impulso entre</div><div class="v">{n(D.get('1o recuo da perna', 0))} / {n(D.get('2o recuo da perna', 0))} / {n(D.get('3o+ recuo da perna', 0))} &middot; {n(D.get('sem impulso desde o toque anterior', 0))}</div></div>
<div class="kpi"><div class="r">2o recuo, R$/trade treino &rarr; teste (alvo 400)</div><div class="v"><span class="neg">{rs(s2['r400']['ev_is'], 1)}</span> &rarr; <span class="pos">{rs(s2['r400']['ev_oos'], 1)}</span></div></div>
<div class="kpi"><div class="r">Stop cheio: sinal perto do anterior x resto (alvo 400)</div><div class="v">{n(pt['r400']['falha'], 0)}% x {n(pt['r400']['falha_resto'], 0)}%</div></div>
<div class="kpi"><div class="r">Carteira sem filtro (alvo 400)</div><div class="v {cls(c0['r400']['stats']['liquido'])}">{rs(c0['r400']['stats']['liquido'])}</div></div>
</div>

<div class="card alerta"><b>1. Nao ha correlacao negativa estavel no segundo toque.</b> O 2o recuo da perna do MACD (houve recuo antes, depois um impulso de {n(M['imp_padrao'])} pts ou mais)
foi o pior grupo no conjunto: {rs(s2['r400']['ev'], 1)} por trade contra {rs(s2['r400']['resto'], 1)} (t = {n(s2['r400']['t'], 2)}; CLAUDE.md {rs(s2['claude']['ev'], 1)} x {rs(s2['claude']['resto'], 1)}).
Mas isso vem todo do treino ({rs(s2['r400']['ev_is'], 1)} x {rs(s2['r400']['resto_is'], 1)}). <b>No teste inverteu</b>: {rs(s2['r400']['ev_oos'], 1)} x {rs(s2['r400']['resto_oos'], 1)}
(CLAUDE.md {rs(s2['claude']['ev_oos'], 1)} x {rs(s2['claude']['resto_oos'], 1)}). A mesma inversao aparece com impulso minimo de 200 e de 400 pts.
Em carteira, tirar o 2o recuo melhora o total ({rs(c0['r400']['stats']['liquido'])} &rarr; {rs(c2['r400']['stats']['liquido'])}), mas so no treino;
no teste piora ({rs(c0['r400']['oos']['liquido'])} &rarr; {rs(c2['r400']['oos']['liquido'])}). E regime de mercado, nao regra.
O 3o recuo ou mais fez o contrario: melhor no treino, empate ou pior no teste.</div>

<div class="card alerta"><b>2. Sinal perto do anterior: um pouco pior, mas fraco e instavel.</b> Entre os recuos cujo recuo anterior teve sinal, os {n(pt['r400']['n'])} com entrada a ate 100 pts
da entrada anterior deram {rs(pt['r400']['ev'], 1)} por trade contra {rs(pt['r400']['resto'], 1)} dos mais longe (CLAUDE.md {rs(pt['claude']['ev'], 1)} x {rs(pt['claude']['resto'], 1)}).
Com alvo 400 ficou abaixo nos dois periodos; na gestao do CLAUDE.md, so no teste; com impulso minimo de 200 pts a diferenca some. Stop cheio {n(pt['r400']['falha'], 0)}% x {n(pt['r400']['falha_resto'], 0)}% (CLAUDE.md {n(pt['claude']['falha'], 0)}% x {n(pt['claude']['falha_resto'], 0)}%): falha um pouco mais, mas pouco.
<ul>
<li><b>No mesmo preco</b> da entrada anterior (dupla na EMA): nao e pior ({rs(mp['r400']['ev'], 1)} x {rs(mp['r400']['resto'], 1)}).</li>
<li><b>1 tijolo (100 pts) a favor</b> da anterior, o fundo "um pouco mais alto" na compra: o grupo que mais pesa. {rs(t1['r400']['ev'], 1)} x {rs(t1['r400']['resto'], 1)},
treino empatado ({rs(t1['r400']['ev_is'], 1)} x {rs(t1['r400']['resto_is'], 1)}) e teste bem pior ({rs(t1['r400']['ev_oos'], 1)} x {rs(t1['r400']['resto_oos'], 1)}), com stop cheio de
{n(t1['r400']['falha_oos'], 0)}% no teste. Pior no total com impulso minimo de 200 e 400 ({rs(t1_200['ev'], 1)} e {rs(t1_400['ev'], 1)}), principalmente pelo teste. t entre &minus;0,6 e &minus;1,4.</li>
<li><b>Sinal anterior ainda aberto</b> quando o novo aparece: {rs(ab['r400']['ev'], 1)} x {rs(ab['r400']['resto'], 1)}; bom no treino, muito ruim no teste. Poucos sinais ({n(ab['r400']['n'])}).</li>
</ul>
Em carteira, sem os sinais perto do anterior: {rs(c0['r400']['stats']['liquido'])} &rarr; {rs(cp['r400']['stats']['liquido'])} (CLAUDE.md {rs(c0['claude']['stats']['liquido'])} &rarr; {rs(cp['claude']['stats']['liquido'])}),
pouca mudanca no rebaixamento.</div>

<div class="card"><b>3. O que isso quer dizer na pratica.</b> O setup nao piora de forma consistente por ser o segundo toque, nem por estar perto do sinal anterior.
O unico padrao que se repete e o segundo sinal <i>um tijolo acima</i> do anterior (na compra) render menos nos meses recentes. E um candidato a acompanhar, nao um filtro:
o efeito so aparece no teste, entao pode ser do periodo. O estudo anterior (<code>relatorio.html</code>, "Segundas entradas no mesmo nivel") ja tinha dado empate: +R$ 4,4 x +R$ 4,3 por trade.</div>
</section>

<section id="defs"><h2>Como foi medido</h2>
<div class="card"><ul>
<li><b>Perna</b>: candles desde que o MACD ficou do lado do trade, sem sair do pregao.</li>
<li><b>Recuo</b>: candles que tocam a EMA 21 (tolerancia {n(M['tol'])} pts, a mesma da regra). Um toque so conta como <b>novo recuo</b> se, desde o extremo do recuo anterior, o preco andou a favor
pelo menos o <b>impulso minimo</b> ({n(M['imp_padrao'])} pts no padrao; 200 e 400 como sensibilidade). Sem isso e o <b>mesmo recuo</b> (preco preso na EMA).</li>
<li><b>1o, 2o, 3o+ recuo</b>: ordem dentro da perna. O sinal atual e sempre o recuo mais recente.</li>
<li><b>Nivel</b>: extremo do recuo atual &minus; extremo do anterior, a favor do trade (na compra: positivo = fundo mais alto).</li>
<li><b>Sinal anterior</b>: sinal do setup (mesmo lado) no recuo anterior. <b>Distancia</b> = entrada atual &minus; entrada anterior, a favor do trade; no PI anda de 100 em 100.
<b>Resultado</b>: so conhecido se o trade anterior ja tinha fechado quando o novo sinal apareceu; senao, "aberto".</li>
<li><b>Stop cheio</b> = trade que tomou o stop de &minus;100 sem fazer parcial (a "falha").</li>
</ul></div>
</section>

<section id="grupos"><h2>Grupos</h2>
{abas('imp', GI, str(IMP0))}{abas('gg', G2, 'r400')}
{blocos}
</section>

<section id="sens"><h2>Sensibilidade ao impulso minimo</h2>
{tab_sens()}
</section>

<section id="cart"><h2>Carteira</h2>
<p class="nota">Impulso minimo de {n(M['imp_padrao'])} pts. Uma posicao por vez.</p>
{abas('cg', G2, 'r400')}
<div class="bc" data-g="r400">{tab_cart('r400')}</div><div class="bc" data-g="claude" hidden>{tab_cart('claude')}</div>
</section>
"""


JS = r"""
const T=__T__;
const $=s=>document.querySelector(s);
function cv(k){return getComputedStyle(document.documentElement).getPropertyValue('--'+k).trim();}
function fmt(v,c=0){if(v===null||v===undefined||Number.isNaN(v))return '-';return Number(v).toLocaleString('pt-BR',{minimumFractionDigits:c,maximumFractionDigits:c});}
function linhas(el,series,op={}){
  const W=Math.max(300,el.clientWidth||600), H=op.alt||280, m={e:64,d:12,t:10,b:24};
  let ys=[0];series.forEach(s=>s.y.forEach(v=>ys.push(v)));
  let y0=Math.min(...ys),y1=Math.max(...ys); if(y1===y0)y1+=1; const pad=(y1-y0)*.06; y0-=pad; y1+=pad;
  const X=(i,L)=>m.e+(W-m.e-m.d)*(L<=1?0:i/(L-1)), Y=v=>m.t+(H-m.t-m.b)*(1-(v-y0)/(y1-y0));
  let s=`<svg viewBox="0 0 ${W} ${H}" role="img">`;
  for(let k=0;k<=4;k++){const v=y0+(y1-y0)*k/4;s+=`<line x1="${m.e}" x2="${W-m.d}" y1="${Y(v)}" y2="${Y(v)}" stroke="${cv('grade')}"/><text x="${m.e-6}" y="${Y(v)+4}" text-anchor="end" font-size="11" fill="${cv('mudo')}">${fmt(v)}</text>`;}
  s+=`<line x1="${m.e}" x2="${W-m.d}" y1="${Y(0)}" y2="${Y(0)}" stroke="${cv('eixo')}"/>`;
  s+=`<text x="${W-m.d}" y="${H-6}" text-anchor="end" font-size="11" fill="${cv('mudo')}">trades (cada curva na propria escala) &rarr;</text>`;
  series.forEach(se=>{const L=se.y.length;s+=`<polyline fill="none" stroke="${se.cor}" stroke-width="${se.larg||1.6}" points="${se.y.map((v,i)=>X(i,L).toFixed(1)+','+Y(v).toFixed(1)).join(' ')}"/>`;});
  el.innerHTML=`<div class="leg">${series.map(se=>`<span><i style="background:${se.cor}"></i>${se.nome}</span>`).join('')}</div>`+s+'</svg>';
}
const CORES=()=>[cv('tinta'),cv('azul'),cv('ganho'),cv('ouro'),cv('perda'),cv('alerta'),'#8e44ad'];
function curvas(){['r400','claude'].forEach(gk=>{const el=document.getElementById('g_'+gk); if(!el||!el.offsetParent) return; const cs=CORES();
  linhas(el,T[gk].map((l,i)=>({nome:l.nome,cor:cs[i%cs.length],y:l.eq,larg:i===0?2.6:1.5})));});}
function atualiza(){
  const imp=$('.abas[data-alvo="imp"] .on').dataset.k, gk=$('.abas[data-alvo="gg"] .on').dataset.k, cg=$('.abas[data-alvo="cg"] .on').dataset.k;
  document.querySelectorAll('.bl').forEach(x=>x.hidden=!(x.dataset.imp===imp&&x.dataset.g===gk));
  document.querySelectorAll('.bc').forEach(x=>x.hidden=x.dataset.g!==cg);
  curvas();
}
document.querySelectorAll('.abas[data-alvo]').forEach(el=>el.addEventListener('click',e=>{const b=e.target.closest('button'); if(!b) return;
  el.querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b)); atualiza();}));
curvas();
let rz; addEventListener('resize',()=>{clearTimeout(rz);rz=setTimeout(curvas,200);});
$('#btema').addEventListener('click',()=>{const r=document.documentElement;
  const escuro=r.dataset.theme?r.dataset.theme==='dark':matchMedia('(prefers-color-scheme: dark)').matches;
  r.dataset.theme=escuro?'light':'dark'; curvas();});
"""

CSS_EXTRA = """
.card ul{margin:8px 0 4px;padding-left:20px}
.card li{margin:4px 0}
"""
MENU = [('resumo', 'Resposta'), ('defs', 'Medidas'), ('grupos', 'Grupos'), ('sens', 'Sensibilidade'), ('cart', 'Carteira')]


def markdown():
    M = T['meta']
    L = ['# Segundo toque na EMA 21', '',
         f"Setup EMA 21 + HullRetracao_Azul + MACD, WINFUT PI 20, {M['pregoes']} pregoes ({M['inicio']} a {M['fim']}), {n(M['sinais'])} sinais. "
         f"Entrada seca no fechamento, 6 contratos, R$ 0,50 por contrato. Treino ate {M['corte']}. Tabelas completas em `segundo.html`.", '',
         f"Recuo = candles tocando a EMA 21 (tolerancia {n(M['tol'])} pts). Um toque e novo recuo se o preco andou a favor pelo menos o impulso minimo "
         f"({n(M['imp_padrao'])} pts; 200 e 400 como sensibilidade) desde o extremo do recuo anterior, dentro da perna do MACD e do pregao. "
         'Stop cheio = stop de -100 sem parcial.', '']
    for gk in ('r400', 'claude'):
        L += [f'## {NOME_G[gk]} (impulso minimo {n(M["imp_padrao"])})', '',
              '| Grupo | Sinais | R$/trade | Resto | Treino (resto) | Teste (resto) | Stop cheio (resto) | t |', '|:--|--:|--:|--:|--:|--:|--:|--:|']
        for r in T['grupos'][f'{IMP0}|{gk}']:
            L.append(f"| {r['nome']} | {n(r['n'])} | {rs(r['ev'], 1)} | {rs(r['resto'], 1)} | {rs(r['ev_is'], 1)} ({rs(r['resto_is'], 1)}) | "
                     f"{rs(r['ev_oos'], 1)} ({rs(r['resto_oos'], 1)}) | {n(r['falha'], 0)}% ({n(r['falha_resto'], 0)}%) | {n(r['t'], 2)} |")
        L += ['', '| Carteira | Trades | Liquido | Fator | Rebaix. | Treino | Teste |', '|:--|--:|--:|--:|--:|--:|--:|']
        for l in T['carteiras'][gk]:
            s = l['stats']
            L.append(f"| {l['nome']} | {n(s['trades'])} | {rs(s['liquido'])} | {n(s['fator_lucro'], 2)} | {rs(-s['dd_max'])} | {rs(l['is_']['liquido'])} | {rs(l['oos']['liquido'])} |")
        L.append('')
    L += ['## Sensibilidade (stop 100 / alvo 400): R$/trade treino / teste, resto entre parenteses', '',
          '| Grupo | ' + ' | '.join(f'Impulso >= {int(i)}' for i in M['imps']) + ' |', '|:--|' + '--:|' * len(M['imps'])]
    for ch in ['2o recuo da perna', 'Sinal anterior perto', 'Entrada 1 tijolo', 'Entrada no MESMO', 'Sinal anterior ainda aberto', 'Sinal anterior tomou STOP']:
        cel = []
        for imp in M['imps']:
            try:
                r = g(int(imp), 'r400', ch)
                cel.append(f"{rs(r['ev_is'], 1)} ({rs(r['resto_is'], 1)}) / {rs(r['ev_oos'], 1)} ({rs(r['resto_oos'], 1)})")
            except StopIteration:
                cel.append('-')
        L.append(f"| {g(IMP0, 'r400', ch)['nome']} | " + ' | '.join(cel) + ' |')
    s2 = g(IMP0, 'r400', '2o recuo da perna'); t1 = g(IMP0, 'r400', 'Entrada 1 tijolo')
    L += ['', '## Conclusoes', '',
          f"1. **Nao ha correlacao negativa estavel no segundo toque.** O 2o recuo da perna foi pior no treino ({rs(s2['ev_is'], 1)} x {rs(s2['resto_is'], 1)}) "
          f"e melhor no teste ({rs(s2['ev_oos'], 1)} x {rs(s2['resto_oos'], 1)}), com impulso minimo de 200, 300 e 400 pts. Regime, nao regra.",
          '2. **Sinal perto do anterior (ate 100 pts)**: um pouco pior e com stop cheio um pouco mais frequente; instavel (some com impulso minimo de 200). No mesmo preco nao e pior.',
          f"3. **Candidato a acompanhar**: segundo sinal 1 tijolo a favor do anterior ({rs(t1['ev'], 1)} x {rs(t1['resto'], 1)}; teste {rs(t1['ev_oos'], 1)}). "
          'Treino empatado: nao usar como filtro ainda.', '',
          'Reproduzir: `python segundo.py && python segundo_rel.py`.', '']
    return '\n'.join(L)


def main():
    dados = {gk: [dict(nome=l['nome'], eq=l['eq']) for l in T['carteiras'][gk]] for gk in T['carteiras']}
    html = ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Segundo toque</title><style>{CSS}{CSS_EXTRA}</style></head><body>'
            '<nav class="indice"><div class="wrap"><ul>' + ''.join(f'<li><a href="#{a}">{r}</a></li>' for a, r in MENU) +
            '</ul></div></nav><div class="wrap">' + corpo() + '</div>'
            '<button class="tema" id="btema" title="Alternar tema" aria-label="Alternar tema">&#9681;</button>'
            '<script>' + JS.replace('__T__', json.dumps(dados, ensure_ascii=False)) + '</script></body></html>')
    open(os.path.join(BASE, 'segundo.html'), 'w', encoding='utf-8').write(html)
    open(os.path.join(BASE, 'SEGUNDO_TOQUE.md'), 'w', encoding='utf-8').write(markdown())
    print('segundo.html', round(len(html) / 1e6, 2), 'MB')


if __name__ == '__main__':
    main()
