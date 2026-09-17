# -*- coding: utf-8 -*-
"""Relatorio: MACD x Bollinger 1000 no trigger -> macd_bb.html + MACD_BB.md
(rodar depois de macd_bb.py)."""
import json
import os

import engine as E
from relatorio import CSS
from textos import n, rs, cls

BASE = E.BASE
T = json.load(open(os.path.join(BASE, 'saida', 'macd_bb.json'), encoding='utf-8'))
for _l in T['faixas']:
    _l['faixa'] = {'a 0,0': 'abaixo de 0 (MACD abaixo da media 1000)', '1,0 a': '1,0 ou mais (alem da banda)'}.get(_l['faixa'], _l['faixa'])
NOME_G = {'claude': 'Gestao do CLAUDE.md (stop 100, parcial +100, alvo 300)', 'r400': 'Stop 100 / alvo 400 sem parcial'}
G2 = [('r400', 'Stop 100 / alvo 400'), ('claude', 'Gestao CLAUDE.md')]


def v(k, gk):
    return next(r for r in T['varredura'] if r['k'] == k and r['gestao'] == gk)


def cart(gk, ini, fonte='carteiras'):
    return next(l for l in T[fonte][gk] if l['nome'].startswith(ini))


def fx(ini):
    return next(l for l in T['faixas'] if l['faixa'].startswith(ini))


def tag(r):
    if r.get('resto_is') is None or r.get('resto_oos') is None:
        return ''
    a = r['ev_is'] - r['resto_is']; b = r['ev_oos'] - r['resto_oos']
    if a > 0 and b > 0:
        return '<span class="tag pos">melhor nos dois</span>'
    if a < 0 and b < 0:
        return '<span class="tag neg">pior nos dois</span>'
    return '<span class="tag">inverte</span>'


def tab_varr(gk):
    h = ('<div class="tab"><table><thead><tr><th>Exigir MACD &ge;</th><th>Sinais mantidos</th><th>R$/trade</th><th>Cortados</th><th>Treino (cortados)</th>'
         '<th>Teste (cortados)</th><th>Stop cheio (cortados)</th><th>t</th><th>Percentil</th><th>Treino x teste</th></tr></thead><tbody>')
    for r in [r for r in T['varredura'] if r['gestao'] == gk]:
        dest = r['k'] == 0.5
        h += (f"<tr class=\"{'dest' if dest else ''}\"><td>{n(r['k'], 2)} desvio</td><td>{n(r['n'])} <span class=\"nota\">({n(r['frac'] * 100, 0)}%)</span></td>"
              f"<td class=\"{cls(r['ev'])}\">{rs(r['ev'], 1)}</td><td class=\"{cls(r.get('resto'))}\">{rs(r.get('resto'), 1)}</td>"
              f"<td><span class=\"{cls(r['ev_is'])}\">{rs(r['ev_is'], 1)}</span> <span class=\"nota\">({rs(r.get('resto_is'), 1)})</span></td>"
              f"<td><span class=\"{cls(r['ev_oos'])}\">{rs(r['ev_oos'], 1)}</span> <span class=\"nota\">({rs(r.get('resto_oos'), 1)})</span></td>"
              f"<td>{n(r['falha'], 0)}% <span class=\"nota\">({n(r['falha_resto'], 0)}%)</span></td><td>{n(r.get('t'), 2)}</td><td>{n(r.get('pct'), 0)}</td><td>{tag(r)}</td></tr>")
    return h + '</tbody></table></div>'


def tab_faixas(gk):
    h = ('<div class="tab"><table><thead><tr><th>MACD no trigger (desvios)</th><th>Sinais</th><th>R$/trade</th><th>Treino</th><th>Teste</th><th>Stop cheio</th>'
         '<th>Compra</th><th>Venda</th><th>T1</th><th>T2</th></tr></thead><tbody>')
    for l in T['faixas']:
        x = l[gk]
        h += (f"<tr><td>{l['faixa']}</td><td>{n(l['n'])}</td><td class=\"{cls(x['ev'])}\">{rs(x['ev'], 1)}</td>"
              f"<td class=\"{cls(x['ev_is'])}\">{rs(x['ev_is'], 1)} <span class=\"nota\">({n(l['n_is'])})</span></td>"
              f"<td class=\"{cls(x['ev_oos'])}\">{rs(x['ev_oos'], 1)} <span class=\"nota\">({n(l['n_oos'])})</span></td><td>{n(x['falha'], 0)}%</td>"
              f"<td class=\"{cls(x['compra'])}\">{rs(x['compra'], 1)}</td><td class=\"{cls(x['venda'])}\">{rs(x['venda'], 1)}</td>"
              f"<td class=\"{cls(x['t1'])}\">{rs(x['t1'], 1)}</td><td class=\"{cls(x['t2'])}\">{rs(x['t2'], 1)}</td></tr>")
    return h + '</tbody></table></div>'


def tab_cart(linhas, gid):
    h = ('<div class="tab"><table><thead><tr><th>Filtro</th><th>Trades</th><th>Liquido</th><th>Fator</th><th>Rebaixamento</th><th>Treino</th><th>Teste</th>'
         '<th>Atravessar 5 pts</th><th>Pregoes +</th></tr></thead><tbody>')
    for i, l in enumerate(linhas):
        s = l['stats']
        h += (f"<tr class=\"{'dest' if i == 0 else ''}\"><td>{l['nome']} <span class=\"nota\">({n(l['frac'] * 100, 0)}%)</span></td><td>{n(s['trades'])}</td>"
              f"<td class=\"{cls(s['liquido'])}\">{rs(s['liquido'])}</td><td>{n(s['fator_lucro'], 2)}</td><td>{rs(-s['dd_max'])}</td>"
              f"<td class=\"{cls(l['is_']['liquido'])}\">{rs(l['is_']['liquido'])}</td><td class=\"{cls(l['oos']['liquido'])}\">{rs(l['oos']['liquido'])}</td>"
              f"<td class=\"{cls(l['atravessa'])}\">{rs(l['atravessa'])}</td><td>{n(s['dias_pos'], 0)}%</td></tr>")
    return h + f'</tbody></table></div><div class="card"><div class="graf" id="{gid}"></div></div>'


def tab_sub(gk):
    ref = T['meta']['ref_macd0'][gk]
    h = ('<div class="tab"><table><thead><tr><th>Regra do MACD</th><th>Sinais</th><th>R$/trade</th><th>Treino</th><th>Teste</th>'
         '<th>Entram com MACD do lado errado de zero</th><th>Saem com MACD do lado certo</th></tr></thead><tbody>'
         f"<tr class=\"dest\"><td>MACD &gt; 0 (regra atual)</td><td>{n(ref['n'])}</td><td class=\"{cls(ref['ev'])}\">{rs(ref['ev'], 1)}</td>"
         f"<td class=\"{cls(ref['ev_is'])}\">{rs(ref['ev_is'], 1)}</td><td class=\"{cls(ref['ev_oos'])}\">{rs(ref['ev_oos'], 1)}</td><td>-</td><td>-</td></tr>")
    for r in [r for r in T['substituto'] if r['gestao'] == gk]:
        h += (f"<tr><td>MACD &ge; {n(r['k'], 2)} desvio, sem exigir &gt; 0</td><td>{n(r['n'])}</td><td class=\"{cls(r['ev'])}\">{rs(r['ev'], 1)}</td>"
              f"<td class=\"{cls(r['ev_is'])}\">{rs(r['ev_is'], 1)}</td><td class=\"{cls(r['ev_oos'])}\">{rs(r['ev_oos'], 1)}</td>"
              f"<td>{n(r['so_macd_contra'])} <span class=\"nota\">({rs(r['ev_macd_contra'], 1)})</span></td><td>{n(r['perdidos_macd_pos'])}</td></tr>")
    mc = T['meta']['macd_contra'][gk]
    return h + (f'</tbody></table></div><p class="nota">Sem nenhum filtro de MACD, os {n(mc["n"])} sinais com MACD do lado errado de zero deram {rs(mc["ev"], 1)} por trade '
                f'(com o MACD do lado certo, {rs(ref["ev"], 1)}).</p>')


def abas(alvo, itens, ini='r400'):
    return (f'<div class="abas" data-alvo="{alvo}">' + ''.join(f'<button data-k="{k}" class="{"on" if k == ini else ""}">{r}</button>' for k, r in itens) + '</div>')


def blocos(alvo, render):
    return ''.join(f'<div class="bl" data-alvo="{alvo}" data-k="{k}"{"" if k == "r400" else " hidden"}>{render(k)}</div>' for k, _ in G2)


def corpo():
    M = T['meta']; zp = M['z_pct']
    k5 = {gk: v(0.5, gk) for gk in ('r400', 'claude')}
    k3 = {gk: v(0.3, gk) for gk in ('r400', 'claude')}
    k10 = {gk: v(1.0, gk) for gk in ('r400', 'claude')}
    c0 = {gk: cart(gk, 'sem exigencia') for gk in ('r400', 'claude')}
    c5 = {gk: cart(gk, 'MACD >= 0,50') for gk in ('r400', 'claude')}
    c3 = {gk: cart(gk, 'MACD >= 0,30') for gk in ('r400', 'claude')}
    cb = {gk: cart(gk, 'consolidacao 100 E Keltner', 'combina') for gk in ('r400', 'claude')}
    cb5 = {gk: cart(gk, 'consolidacao 100 E Keltner E MACD', 'combina') for gk in ('r400', 'claude')}
    f02 = fx('0,0 a 0,2'); f24 = fx('0,2 a 0,4'); f46 = fx('0,4 a 0,6'); fneg = T['faixas'][0]
    return f"""
<h1>MACD x Bollinger 1000 no trigger</h1>
<p class="sub">Setup EMA 21 + HullRetracao_Azul + MACD &middot; WINFUT PI 20, {M['pregoes']} pregoes ({M['inicio']} a {M['fim']}) &middot; {n(M['com_bb'])} sinais com Bollinger calculada
(de {n(M['sinais'])}) &middot; entrada seca no fechamento &middot; 6 contratos, R$ 0,50 por contrato &middot; treino ate {M['corte']}, teste depois</p>

<section id="resumo"><h2>Resposta curta</h2>
<div class="kpis">
<div class="kpi"><div class="r">Carteira sem exigencia (alvo 400)</div><div class="v {cls(c0['r400']['stats']['liquido'])}">{rs(c0['r400']['stats']['liquido'])}</div></div>
<div class="kpi"><div class="r">Exigindo MACD &ge; 0,5 desvio</div><div class="v {cls(c5['r400']['stats']['liquido'])}">{rs(c5['r400']['stats']['liquido'])}</div></div>
<div class="kpi"><div class="r">Sinais mantidos com 0,5</div><div class="v">{n(k5['r400']['frac'] * 100, 0)}%</div></div>
<div class="kpi"><div class="r">MACD no trigger: mediana (p10 a p90)</div><div class="v">{n(zp['50'], 2)} ({n(zp['10'], 2)} a {n(zp['90'], 2)})</div></div>
</div>

<div class="card ruim"><b>1. Exigir o MACD alem de 0,5 desvio nao melhora: piora no treino, empata no teste e corta a maior parte do lucro.</b> No fechamento do trigger o MACD ja voltou parte do caminho: a mediana fica em {n(zp['50'], 2)} desvio,
entao 0,5 corta {n((1 - k5['r400']['frac']) * 100, 0)}% dos sinais. Os mantidos deram {rs(k5['r400']['ev'], 1)} por trade contra {rs(k5['r400']['resto'], 1)} dos cortados
(treino {rs(k5['r400']['ev_is'], 1)} x {rs(k5['r400']['resto_is'], 1)}, teste {rs(k5['r400']['ev_oos'], 1)} x {rs(k5['r400']['resto_oos'], 1)};
CLAUDE.md {rs(k5['claude']['ev'], 1)} x {rs(k5['claude']['resto'], 1)}). Em carteira: {rs(c0['r400']['stats']['liquido'])} &rarr; <b>{rs(c5['r400']['stats']['liquido'])}</b>
(CLAUDE.md {rs(c0['claude']['stats']['liquido'])} &rarr; {rs(c5['claude']['stats']['liquido'])}). Somado aos candidatos anteriores (consolidacao 100 + Keltner) tambem so tira lucro:
{rs(cb['r400']['stats']['liquido'])} &rarr; {rs(cb5['r400']['stats']['liquido'])}.</div>

<div class="card alerta"><b>2. Nenhum limiar forma uma escada.</b> A varredura sobe e desce:
0,2-0,3 desvio melhora um pouco (0,3: {rs(k3['r400']['ev'], 1)} x {rs(k3['r400']['resto'], 1)}, melhor no treino e no teste; carteira {rs(c3['r400']['stats']['liquido'])} com rebaixamento
{rs(-c3['r400']['stats']['dd_max'])} contra {rs(-c0['r400']['stats']['dd_max'])}), 0,4-0,5 piora, 0,6 volta a melhorar.
Por faixa: 0 a 0,2 desvio {rs(f02['r400']['ev'], 1)} (negativo no treino e no teste); 0,2 a 0,4 {rs(f24['r400']['ev'], 1)} (positivo nos dois); 0,4 a 0,6 {rs(f46['r400']['ev'], 1)}
(treino {rs(f46['r400']['ev_is'], 1)}, teste {rs(f46['r400']['ev_oos'], 1)}); abaixo da media {rs(fneg['r400']['ev'], 1)} ({n(fneg['n'])} sinais, bom so no treino).
Esse vai-e-vem e o desenho do acaso. O ganho com 0,2-0,3 vem de cortar a faixa 0-0,2, e nao ha razao previa para ela ser pior que a faixa logo abaixo.</div>

<div class="card ok"><b>3. O que se repete: MACD ja alem da banda (1,0 desvio) no trigger e ruim.</b> Sao so {n(k10['r400']['n'])} sinais: {rs(k10['r400']['ev'], 1)} por trade,
negativo no treino ({rs(k10['r400']['ev_is'], 1)}) e no teste ({rs(k10['r400']['ev_oos'], 1)}); CLAUDE.md {rs(k10['claude']['ev'], 1)}. E o mesmo achado do relatorio principal
e do estudo de impulso (preco alem da Keltner 2,5): o setup rende menos quando o movimento ja esta esticado. Correlacao de posto do MACD no trigger com "passou da Keltner" = {n(M['corr_z']['kc_10'], 2)}.</div>

<div class="card"><b>4. Trocar "MACD &gt; 0" por "MACD acima de k desvios"</b> muda pouco (secao <a href="#sub">Substituto</a>). A propria exigencia de MACD &gt; 0 separa pouco:
sem ela, os sinais com MACD do lado errado deram {rs(M['macd_contra']['r400']['ev'], 1)} por trade, contra {rs(M['ref_macd0']['r400']['ev'], 1)} com o MACD do lado certo.</div>
</section>

<section id="defs"><h2>Como foi medido</h2>
<div class="card"><ul>
<li>MACD 9/14 no fechamento do candle do trigger. Bollinger 1000 sobre o MACD: media e desvio-padrao dos ultimos 1000 valores do MACD.</li>
<li><b>Desvios</b> = (MACD &minus; media 1000) / desvio 1000, com sinal do trade (compra: positivo acima da media; venda: positivo abaixo). A banda desenhada no grafico (1,0) e o desvio 1.
Desvio mediano no periodo: {n(M['desvio_mediano'], 0)} pts de MACD; media 1000 mediana: {n(M['media_mediana'], 1)}, praticamente zero.</li>
<li>"Exigir &ge; k" mantem so os sinais com desvios &ge; k, alem das regras atuais (inclusive MACD &gt; 0). "Cortados" = os outros sinais.</li>
<li>Os {n(M['sinais'] - M['com_bb'])} sinais dos primeiros 1000 candles (sem Bollinger) ficam fora; por isso a carteira sem exigencia difere um pouco do relatorio principal.</li>
<li>Stop cheio = stop de &minus;100 sem parcial.</li>
</ul></div>
</section>

<section id="varr"><h2>Varredura de limiares</h2>
{abas('va', G2)}{blocos('va', tab_varr)}
</section>

<section id="faixas"><h2>Faixas</h2>
{abas('fa', G2)}{blocos('fa', tab_faixas)}
</section>

<section id="cart"><h2>Carteira por limiar</h2>
{abas('ca', G2)}{blocos('ca', lambda gk: tab_cart(T['carteiras'][gk], 'g_ca_' + gk))}
</section>

<section id="comb"><h2>Com os candidatos dos outros estudos</h2>
<p class="nota">Consolidacao 100 = eficiencia &ge; 0,08 (<code>tendencia.html</code>). Keltner = preco nao passou da Keltner 2,5 nos 10 candles antes do recuo (<code>impulso.html</code>).</p>
{abas('co', G2)}{blocos('co', lambda gk: tab_cart(T['combina'][gk], 'g_co_' + gk))}
</section>

<section id="sub"><h2>Substituto: desvios no lugar de MACD &gt; 0</h2>
{abas('su', G2)}{blocos('su', tab_sub)}
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
function curvas(){['r400','claude'].forEach(gk=>{const cs=CORES();
  const a=document.getElementById('g_ca_'+gk); if(a&&a.offsetParent) linhas(a,T.carteiras[gk].filter((l,i)=>[0,3,4,6,10].includes(i)).map((l,i)=>({nome:l.nome,cor:cs[i],y:l.eq,larg:i===0?2.6:1.5})));
  const b=document.getElementById('g_co_'+gk); if(b&&b.offsetParent) linhas(b,T.combina[gk].map((l,i)=>({nome:l.nome,cor:cs[i%cs.length],y:l.eq,larg:i===0?2.6:1.4})));});}
document.querySelectorAll('.abas[data-alvo]').forEach(el=>el.addEventListener('click',e=>{const b=e.target.closest('button'); if(!b) return;
  el.querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b));
  document.querySelectorAll(`.bl[data-alvo="${el.dataset.alvo}"]`).forEach(x=>x.hidden=x.dataset.k!==b.dataset.k); curvas();}));
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
MENU = [('resumo', 'Resposta'), ('defs', 'Medidas'), ('varr', 'Varredura'), ('faixas', 'Faixas'), ('cart', 'Carteira'), ('comb', 'Combinado'), ('sub', 'Substituto')]


def markdown():
    M = T['meta']
    L = ['# MACD x Bollinger 1000 no trigger', '',
         f"Setup EMA 21 + HullRetracao_Azul + MACD, WINFUT PI 20, {M['pregoes']} pregoes ({M['inicio']} a {M['fim']}), {n(M['com_bb'])} sinais com Bollinger. "
         f"Entrada seca no fechamento, 6 contratos, R$ 0,50 por contrato. Treino ate {M['corte']}. Graficos em `macd_bb.html`.", '',
         'Desvios = (MACD - media 1000) / desvio 1000, com o sinal do trade. A banda do grafico (1,0) e o desvio 1. '
         f"No trigger: mediana {n(M['z_pct']['50'], 2)}, p10 {n(M['z_pct']['10'], 2)}, p90 {n(M['z_pct']['90'], 2)}.", '']
    for gk in ('r400', 'claude'):
        L += [f'## {NOME_G[gk]}', '', '**Exigir MACD >= k desvios**', '',
              '| k | Mantidos | R$/trade | Cortados | Treino (cortados) | Teste (cortados) | Stop cheio (cortados) | t |', '|--:|--:|--:|--:|--:|--:|--:|--:|']
        for r in [r for r in T['varredura'] if r['gestao'] == gk]:
            L.append(f"| {n(r['k'], 2)} | {n(r['n'])} ({n(r['frac'] * 100, 0)}%) | {rs(r['ev'], 1)} | {rs(r.get('resto'), 1)} | {rs(r['ev_is'], 1)} ({rs(r.get('resto_is'), 1)}) | "
                     f"{rs(r['ev_oos'], 1)} ({rs(r.get('resto_oos'), 1)}) | {n(r['falha'], 0)}% ({n(r['falha_resto'], 0)}%) | {n(r.get('t'), 2)} |")
        L += ['', '**Faixas**', '', '| Desvios | Sinais | R$/trade | Treino | Teste | Stop cheio |', '|:--|--:|--:|--:|--:|--:|']
        for l in T['faixas']:
            x = l[gk]
            L.append(f"| {l['faixa']} | {n(l['n'])} | {rs(x['ev'], 1)} | {rs(x['ev_is'], 1)} | {rs(x['ev_oos'], 1)} | {n(x['falha'], 0)}% |")
        L += ['', '**Carteira**', '', '| Filtro | Trades | Liquido | Fator | Rebaix. | Treino | Teste |', '|:--|--:|--:|--:|--:|--:|--:|']
        for l in T['carteiras'][gk] + T['combina'][gk][1:]:
            s = l['stats']
            L.append(f"| {l['nome']} | {n(s['trades'])} | {rs(s['liquido'])} | {n(s['fator_lucro'], 2)} | {rs(-s['dd_max'])} | {rs(l['is_']['liquido'])} | {rs(l['oos']['liquido'])} |")
        L.append('')
    k5 = v(0.5, 'r400'); k10 = v(1.0, 'r400'); c0 = cart('r400', 'sem exigencia'); c5 = cart('r400', 'MACD >= 0,50')
    L += ['## Conclusoes', '',
          f"1. **Exigir MACD >= 0,5 desvio piora**: corta {n((1 - k5['frac']) * 100, 0)}% dos sinais; mantidos {rs(k5['ev'], 1)} x cortados {rs(k5['resto'], 1)} por trade; "
          f"carteira {rs(c0['stats']['liquido'])} -> {rs(c5['stats']['liquido'])} (alvo 400). Somado aos outros filtros, tambem piora.",
          '2. **Nenhum limiar forma escada**: 0,2-0,3 melhora um pouco, 0,4-0,5 piora, 0,6 melhora. Padrao de acaso.',
          f"3. **MACD ja alem da banda (>= 1,0) no trigger e ruim** nos dois periodos ({n(k10['n'])} sinais, {rs(k10['ev'], 1)} por trade): mesmo achado do preco esticado alem da Keltner.",
          '4. Trocar MACD > 0 por desvios muda pouco.', '',
          'Reproduzir: `python macd_bb.py && python macd_bb_rel.py`.', '']
    return '\n'.join(L)


def main():
    dados = dict(carteiras={gk: [dict(nome=l['nome'], eq=l['eq']) for l in T['carteiras'][gk]] for gk in T['carteiras']},
                 combina={gk: [dict(nome=l['nome'], eq=l['eq']) for l in T['combina'][gk]] for gk in T['combina']})
    html = ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>MACD na Bollinger</title><style>{CSS}{CSS_EXTRA}</style></head><body>'
            '<nav class="indice"><div class="wrap"><ul>' + ''.join(f'<li><a href="#{a}">{r}</a></li>' for a, r in MENU) +
            '</ul></div></nav><div class="wrap">' + corpo() + '</div>'
            '<button class="tema" id="btema" title="Alternar tema" aria-label="Alternar tema">&#9681;</button>'
            '<script>' + JS.replace('__T__', json.dumps(dados, ensure_ascii=False)) + '</script></body></html>')
    open(os.path.join(BASE, 'macd_bb.html'), 'w', encoding='utf-8').write(html)
    open(os.path.join(BASE, 'MACD_BB.md'), 'w', encoding='utf-8').write(markdown())
    print('macd_bb.html', round(len(html) / 1e6, 2), 'MB')


if __name__ == '__main__':
    main()
