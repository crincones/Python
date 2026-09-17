# -*- coding: utf-8 -*-
"""Relatorio dos filtros de tendencia geral: tendencia.html + TENDENCIA.md
(rodar depois de tendencia.py)."""
import json
import os

import engine as E
from relatorio import CSS
from textos import n, rs, cls

BASE = E.BASE
T = json.load(open(os.path.join(BASE, 'saida', 'tendencia.json'), encoding='utf-8'))

NOME_G = {'claude': 'Gestao do CLAUDE.md (stop 100, parcial +100, alvo 300)', 'r400': 'Stop 100 / alvo 400 sem parcial'}
NOME_C = {'todos': 'todos os sinais', 'picado': 'so sinais com filtro picado'}


def apr(gk, ck, i):
    return T['filtros_apriori'][f'{gk}|{ck}'][i]


def dirc(gk, nome_ini):
    for l in T['consolidacao']['direcao'] + T['consolidacao']['combina']:
        if l['gestao'] == gk and l['nome'].strip().startswith(nome_ini):
            return l
    raise KeyError(nome_ini)


def linha_cart(l, dest=False, nome=None):
    s = l['stats']; o = l['oos']; i = l['is_']
    return (f"<tr class=\"{'dest' if dest else ''}\"><td>{nome or l['nome']}</td><td>{n(s['trades'])}</td>"
            f"<td class=\"{cls(s['liquido'])}\">{rs(s['liquido'])}</td><td>{n(s['fator_lucro'], 2)}</td><td>{rs(-s['dd_max'])}</td>"
            f"<td class=\"{cls(i.get('liquido'))}\">{rs(i.get('liquido'))}</td><td class=\"{cls(o.get('liquido'))}\">{rs(o.get('liquido'))}</td>"
            f"<td class=\"{cls(o.get('exp_rs'))}\">{rs(o.get('exp_rs'), 1)}</td><td class=\"{cls(l['atravessa'])}\">{rs(l['atravessa'])}</td>"
            f"<td>{n(s['dias_pos'], 0)}%</td></tr>")


CAB_CART = ('<div class="tab"><table><thead><tr><th>Filtro</th><th>Trades</th><th>Liquido</th><th>Fator</th><th>Rebaixamento</th>'
            '<th>Treino</th><th>Teste</th><th>Teste R$/trade</th><th>Atravessar 5 pts</th><th>Pregoes +</th></tr></thead><tbody>')


def corpo():
    M = T['meta']
    r_sem = dirc('r400', 'sem filtro'); r_con = dirc('r400', 'consolidado 100'); r_fora = dirc('r400', 'fora da consolidacao 100 (')
    r_fav = dirc('r400', 'tendencia de 100 candles A FAVOR'); r_contra = dirc('r400', 'tendencia de 100 candles CONTRA')
    r_pic = dirc('r400', 'so picado'); r_e = dirc('r400', 'fora da consolidacao 100 E'); r_ou = dirc('r400', 'fora da consolidacao 100 OU')
    c_sem = dirc('claude', 'sem filtro'); c_con = dirc('claude', 'consolidado 100'); c_fora = dirc('claude', 'fora da consolidacao 100 (')
    pl = T['placebo']
    hip = {(h['gestao'], h['conj'], h['nome']): h for h in T['hipoteses']}

    def h_(gk, ck, ini):
        for (g, c, nm), v in hip.items():
            if g == gk and c == ck and nm.startswith(ini):
                return v
        return None

    def dia(gk, ck, ini):
        return next(l for l in T['consolidacao']['dia'] if l['gestao'] == gk and l['conj'] == ck and l['nome'].startswith(ini))

    m20 = h_('r400', 'todos', '20 candles vinham contra'); m30 = h_('r400', 'todos', '30 candles vinham contra')
    H = [f"""
<h1>Filtros de tendencia geral e consolidacao</h1>
<p class="sub">Setup EMA 21 + HullRetracao_Azul + MACD &middot; WINFUT PI 20, {M['pregoes']} pregoes ({M['inicio']} a {M['fim']}) &middot; {n(M['sinais'])} sinais &middot;
entrada seca no fechamento &middot; 6 contratos, R$ 0,50 por contrato &middot; treino ate {M['corte']}, teste depois &middot; complemento de <code>relatorio.html</code></p>

<section id="resumo"><h2>Resposta curta</h2>
<div class="kpis">
<div class="kpi"><div class="r">Sem filtro (stop 100 / alvo 400)</div><div class="v {cls(r_sem['stats']['liquido'])}">{rs(r_sem['stats']['liquido'])}</div></div>
<div class="kpi"><div class="r">Sinais em consolidacao (100 candles)</div><div class="v neg">{rs(r_con['stats']['liquido'])}</div></div>
<div class="kpi"><div class="r">Sinais fora da consolidacao</div><div class="v pos">{rs(r_fora['stats']['liquido'])}</div></div>
<div class="kpi"><div class="r">Rebaixamento: sem filtro &rarr; com filtro</div><div class="v">{rs(-r_sem['stats']['dd_max'])} &rarr; {rs(-r_fora['stats']['dd_max'])}</div></div>
</div>
<div class="card ok"><b>1. Consolidacao funciona como filtro, mas na escala de ~100 candles.</b> Mede-se quanto o preco realmente saiu do lugar nos 100 candles antes do recuo:
|candles de alta &minus; candles de baixa| / 100 (<b>eficiencia</b>). Abaixo de 0,08 (menos de 8 candles liquidos de deslocamento em 100) o mercado esta andando de lado.
Com stop 100 / alvo 400, os {n(r_con['stats']['trades'])} trades nessa condicao deram <b>{rs(r_con['stats']['liquido'])}</b> (treino {rs(r_con['is_']['liquido'])}, teste {rs(r_con['oos']['liquido'])});
os {n(r_fora['stats']['trades'])} fora dela deram <b>{rs(r_fora['stats']['liquido'])}</b>, fator {n(r_fora['stats']['fator_lucro'], 2)}, rebaixamento {rs(-r_fora['stats']['dd_max'])}
(treino {rs(r_fora['is_']['liquido'])}, teste {rs(r_fora['oos']['liquido'])}). Com a gestao do CLAUDE.md: {rs(c_con['stats']['liquido'])} contra {rs(c_fora['stats']['liquido'])}.
Vale com a tendencia de 100 candles a favor ({rs(r_fav['stats']['liquido'])}) e contra o trade ({rs(r_contra['stats']['liquido'])}): o que atrapalha e o mercado <i>sem direcao</i>, nao a direcao.</div>
<div class="card alerta"><b>O limiar exato tem sorte.</b> 100 candles / 0,08 e o pico da grade. Os vizinhos (janela 100 com limiar 0,04-0,10, janela 150 com 0,04-0,08) ficam entre R$ 12 e 17 mil,
todos acima do sem filtro e com rebaixamento de R$ 2,2 a 5,1 mil (sem filtro: {rs(-r_sem['stats']['dd_max'])}). Com 150 / 0,10 ja cai para ~R$ 3,7 mil.
Em 30-50 candles so os cortes leves ficam acima do sem filtro, e sem reduzir o rebaixamento; em 200, so o limiar mais baixo.
No teste, os sinais em consolidacao ficaram perto de zero ({rs(r_con['oos']['liquido'])}), nao negativos: o filtro corta um regime que perdeu muito no treino e nao ganhou no teste.</div>
<div class="card"><b>2. EMA 21 plana: a medida direta ajuda pouco; a regressao nao ajuda.</b>
Evitando os 20% de sinais com a EMA mais plana, pela variacao direta em 10 candles (menos de {n(T['limiares_hip']['Q']['dir_abs_10'], 1)} pts por candle, ~{n(T['limiares_hip']['Q']['dir_abs_10'] * 10)} pts em 10 candles):
{rs(apr('claude', 'todos', 0)['stats']['liquido'])} &rarr; <b>{rs(apr('claude', 'todos', 1)['stats']['liquido'])}</b> na gestao do CLAUDE.md (os sinais com EMA plana foram piores no treino e no teste).
Pela regressao linear de 10 candles o mesmo corte <i>piora</i> ({rs(apr('claude', 'todos', 2)['stats']['liquido'])}), porque a regressao suaviza a EMA, que ja e suave, e junta EMAs que acabaram de virar com EMAs realmente paradas.
EMA "ondulada" (R2 da regressao 10 abaixo de {n(T['limiares_hip']['Q']['reg_r2_10'], 2)}) tem efeito parecido com a medida direta ({rs(apr('claude', 'todos', 3)['stats']['liquido'])}).
Nos sinais ja filtrados pelo picado, nenhum dos tres melhora o total.</div>
<div class="card ruim"><b>3. "Ultimos 20 ou 30 candles em baixa" nao serve como filtro.</b> Com a Hull 50 a favor e o MACD do lado do trade, o mercado quase nunca vem contra:
so {n(m20['frac'] * 100, 0)}% dos sinais tinham os 20 candles anteriores ao recuo contra o trade, e {n(m30['frac'] * 100, 0)}% nos 30.
Nos 30 candles, esses sinais foram {rs(m30['ev_is'], 1)} por trade no treino e {rs(m30['ev_oos'], 1)} no teste: o sinal inverte.
A regra ja embute a tendencia de curto prazo; a informacao nova esta na escala longa.</div>
<div class="card alerta"><b>4. O dia: operar CONTRA o movimento desde a abertura foi melhor.</b> E o contrario de "seguir a expectativa do dia".
Em todos os sinais (stop 100 / alvo 400), os trades na direcao do dia, ou com o preco perto da abertura, deram <b>{rs(dia('r400', 'todos', 'dia a favor')['stats']['liquido'])}</b>
(treino {rs(dia('r400', 'todos', 'dia a favor')['is_']['liquido'])}, teste {rs(dia('r400', 'todos', 'dia a favor')['oos']['liquido'])}).
Os trades com o preco mais de 100 pts contra a abertura deram <b>{rs(dia('r400', 'todos', 'dia contra o trade')['stats']['liquido'])}</b>
(treino {rs(dia('r400', 'todos', 'dia contra o trade')['is_']['liquido'])}, teste {rs(dia('r400', 'todos', 'dia contra o trade')['oos']['liquido'])}),
fator {n(dia('r400', 'todos', 'dia contra o trade')['stats']['fator_lucro'], 2)}. Ou seja, num dia de baixa as <i>compras</i> do setup foram melhores que as vendas.
Com a gestao do CLAUDE.md o padrao se repete. Nos sinais picados a diferenca e menor e so aparece por trade, nao no total.
Foi achado na busca (t de 1,1 a 1,8, abaixo do p99 do placebo): tratar como candidato.</div>
<div class="card"><b>5. Medias longas, gap, dia anterior e Keltner nao se sustentaram.</b> Dos {pl['r400|todos']['n_cand']} cortes testados, os que melhoraram o treino melhoraram o teste em
{n(pl['r400|todos']['frac_melhora_oos_bons_is'] * 100, 0)}% das vezes, quase cara ou coroa: a maior parte das "melhoras" na busca e ruido.</div>
<div class="card"><b>6. Junto com o filtro picado.</b> Os dois filtros sao quase independentes (~28% de picado dentro e fora da consolidacao).
<b>Os dois juntos (E)</b>: {n(r_e['stats']['trades'])} trades, {rs(r_e['stats']['liquido'])}, fator {n(r_e['stats']['fator_lucro'], 2)}, rebaixamento {rs(-r_e['stats']['dd_max'])}.
Menos lucro que so o picado ({rs(r_pic['stats']['liquido'])}, rebaixamento {rs(-r_pic['stats']['dd_max'])}), mas bem mais estavel.
<b>Qualquer um dos dois (OU)</b>: {n(r_ou['stats']['trades'])} trades, {rs(r_ou['stats']['liquido'])}, fator {n(r_ou['stats']['fator_lucro'], 2)}, rebaixamento {rs(-r_ou['stats']['dd_max'])},
teste {rs(r_ou['oos']['liquido'])}, {n(r_ou['stats']['dias_pos'], 0)}% dos pregoes positivos. Essa combinacao foi montada depois de olhar os dados: trate como candidata a confirmar.</div>
</section>

<section id="defs"><h2>Como cada medida foi feita</h2>
<div class="card"><ul>
<li>Tudo <b>orientado pelo lado do trade</b>: positivo = a favor. Medidas de janela terminam no candle <b>antes do recuo</b>, para os 2-3 candles contra do setup nao entrarem na conta.
As medidas da EMA 21 (regressao e variacao direta) e as de nivel terminam no candle do trigger.</li>
<li><b>Direcao N</b>: candles de alta &minus; candles de baixa nos N candles (no PI cada candle anda 100 pts, entao x100 = deslocamento sem os gaps entre pregoes).</li>
<li><b>Eficiencia N</b>: |direcao N| / N. 0 = foi e voltou; 1 = reta.</li>
<li><b>Amplitude N</b>: faixa entre o ponto mais alto e o mais baixo desse caminho, em candles, / N.</li>
<li><b>Cruzamentos EMA N</b>: quantas vezes o fechamento trocou de lado da EMA 21.</li>
<li><b>Regressao EMA21 N</b>: inclinacao da reta de minimos quadrados sobre os ultimos N valores da EMA 21, em pts por candle. Absoluta = plana ou nao; R2 = quao reta.</li>
<li><b>Variacao direta EMA21 N</b>: (EMA agora &minus; EMA N candles atras) / N, na mesma unidade.</li>
<li>Duas gestoes: {NOME_G['claude']} e {NOME_G['r400']}. Dois conjuntos: todos os sinais e so os com filtro picado (11+ inversoes em 20 candles).</li>
<li>Quintis e limiares definidos <b>no treino</b>. "Atravessar 5 pts": parcial e alvo so executam se o preco passar 1 tick alem do nivel.</li>
</ul></div>
</section>

<section id="consol"><h2>Consolidacao em escala longa</h2>
<div class="abas" id="ab_cg"></div>
<div class="card"><h3>Liquido por janela x limiar de eficiencia (manter sinais com eficiencia &ge; limiar)</h3><div id="t_grade"></div>
<h3>So o periodo de teste</h3><div id="t_grade_oos"></div><h3>Rebaixamento maximo</h3><div id="t_grade_dd"></div>
<p class="nota">Sem filtro: R$ {n(r_sem['stats']['liquido'])} (stop 100 / alvo 400) e R$ {n(c_sem['stats']['liquido'])} (CLAUDE.md). Com 30 candles a eficiencia so assume valores de 1/15 em 1/15, por isso as colunas repetem.</p></div>
<div id="t_dir"></div>
<div class="card"><div id="g_dir" class="graf"></div></div>
</section>

<section id="dia"><h2>Contexto do dia</h2>
<div class="abas" id="ab_d_g"></div><div class="abas" id="ab_d_c"></div>
<div id="t_dia"></div><div class="card"><div id="g_dia" class="graf"></div></div>
</section>

<section id="apriori"><h2>Filtros definidos a priori, em carteira</h2>
<p>EMA plana e ondulada cortam os 20% de sinais mais planos / menos retos do treino; consolidacao e direcao usam limiares fixos.</p>
<div class="abas" id="ab_ap_g"></div><div class="abas" id="ab_ap_c"></div>
<div id="t_ap"></div>
<div class="card"><div id="g_ap" class="graf"></div></div>
</section>

<section id="hipoteses"><h2>Hipoteses sinal a sinal</h2>
<p>Cada sinal resolvido isoladamente. R$ por trade com 6 contratos e custo; "resto" = os sinais fora da condicao; t = diferenca / erro padrao.</p>
<div class="abas" id="ab_h_g"></div><div class="abas" id="ab_h_c"></div>
<div id="t_hip"></div>
</section>

<section id="varredura"><h2>Varredura de limiar</h2>
<p>Mantendo so os sinais com o atributo acima do decil 0%, 10%, ..., 80% do treino: R$ por trade no treino (linha cheia) e no teste (tracejada).
Um filtro bom sobe de forma regular nas duas linhas.</p>
<div class="abas" id="ab_v_g"></div><div class="abas" id="ab_v_c"></div>
<div class="grid2" id="g_varr"></div>
</section>

<section id="mapa"><h2>Direcao x consolidacao</h2>
<p>Tercos do treino. Linhas: direcao dos N candles antes do recuo (contra &rarr; a favor). Colunas: eficiencia (lateral &rarr; tendencia). R$ por trade: base (treino / teste).</p>
<div class="abas" id="ab_m_g"></div><div class="abas" id="ab_m_c"></div><div class="abas" id="ab_m_n"></div>
<div id="t_mapa"></div>
</section>

<section id="familias"><h2>Todas as faixas, por familia</h2>
<div class="abas" id="ab_f_g"></div><div class="abas" id="ab_f_c"></div>
<div id="t_fam"></div>
</section>

<section id="selecao"><h2>Busca no treino e controle de acaso</h2>
<p>Mais de 300 cortes (acima/abaixo dos quintis do treino, mantendo 30% ou mais dos sinais), ordenados pela estatistica t no treino. O <b>placebo</b> sorteia
2.000 filtros aleatorios do mesmo tamanho: se o melhor t real nao passa do p99 do placebo, o "melhor filtro" pode ser so o maior dos acasos.</p>
<div class="abas" id="ab_s_g"></div><div class="abas" id="ab_s_c"></div>
<div id="t_plac"></div><div id="t_sel"></div>
</section>

<section id="conclusao"><h2>Como aplicar</h2>
<div class="card ok"><ul>
<li><b>Regra:</b> no candle antes do recuo, contar os candles de alta e de baixa dos 100 anteriores. Se a diferenca, em modulo, for <b>menor que 8</b>, nao operar o sinal.
No Profit, pode ser um contador de <code>Close &gt; Open</code> / <code>Close &lt; Open</code> numa janela de 100 barras (<code>Close &minus; Close[100]</code> inclui os gaps entre pregoes e nao e a mesma medida).</li>
<li>Por ser pico de grade, prefira uma faixa conservadora (diferenca de 6 a 10 em 100 candles) e acompanhe em simulador.</li>
<li>EMA 21 plana: se quiser usar, meca pela variacao direta ((EMA &minus; EMA[10]) / 10 abaixo de ~4,5 pts por candle = nao operar), nao pela regressao. O ganho e pequeno.</li>
<li>Nao filtrar por "ultimos 20/30 candles em baixa" nem por medias longas.</li>
<li>Candidato a acompanhar: nao operar a favor do dia. So entrar quando o preco estiver mais de 100 pts <i>contra</i> o trade em relacao a abertura
(compra com o dia em baixa, venda com o dia em alta). Com consolidacao 100 junto: poucos trades (~2 por pregao), fator 1,5 a 2,4.</li>
<li>Com o filtro picado: usar os dois juntos para estabilidade (fator 1,5, rebaixamento ~R$ 1,2 mil) ou qualquer um dos dois para mais trades, o que ainda precisa de confirmacao.</li>
</ul></div>
</section>
"""]
    return ''.join(H)


JS = r"""
const T=__T__;
const $=s=>document.querySelector(s);
function cv(k){return getComputedStyle(document.documentElement).getPropertyValue('--'+k).trim();}
function fmt(v,c=0){if(v===null||v===undefined||Number.isNaN(v))return '-';return Number(v).toLocaleString('pt-BR',{minimumFractionDigits:c,maximumFractionDigits:c});}
function rs(v,c=0){if(v===null||v===undefined)return '-';return (v>0?'+':v<0?'−':'')+'R$ '+fmt(Math.abs(v),c);}
function cls(v){return v>0?'pos':v<0?'neg':'mudo';}
function alfa(hex,a){const h=hex.replace('#','');const x=h.length===3?h.split('').map(y=>y+y).join(''):h;const i=parseInt(x,16);return `rgba(${(i>>16)&255},${(i>>8)&255},${i&255},${a})`;}
function cor(v,mx){if(v===null||v===undefined)return 'transparent';return alfa(v>=0?cv('ganho'):cv('perda'),Math.min(.8,.08+Math.abs(v)/mx*.7));}
function abas(id,itens,ini,cb){const el=document.getElementById(id);
  el.innerHTML=itens.map(([k,r])=>`<button data-k="${k}" class="${k===ini?'on':''}">${r}</button>`).join('');
  el.addEventListener('click',e=>{const b=e.target.closest('button'); if(!b) return;
    el.querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b)); cb(b.dataset.k);});}
function linhas(el,series,op={}){
  const W=Math.max(300,el.clientWidth||600), H=op.alt||240, m={e:64,d:12,t:10,b:24};
  let ys=[0];series.forEach(s=>s.y.forEach(v=>{if(v!==null)ys.push(v);}));
  let y0=Math.min(...ys),y1=Math.max(...ys); if(y1===y0)y1+=1; const pad=(y1-y0)*.06; y0-=pad; y1+=pad;
  const nx=Math.max(...series.map(s=>s.y.length));
  const X=i=>m.e+(W-m.e-m.d)*(nx<=1?0:i/(nx-1)), Y=v=>m.t+(H-m.t-m.b)*(1-(v-y0)/(y1-y0));
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  for(let k=0;k<=4;k++){const v=y0+(y1-y0)*k/4;s+=`<line x1="${m.e}" x2="${W-m.d}" y1="${Y(v)}" y2="${Y(v)}" stroke="${cv('grade')}"/><text x="${m.e-6}" y="${Y(v)+4}" text-anchor="end" font-size="11" fill="${cv('mudo')}">${fmt(v)}</text>`;}
  s+=`<line x1="${m.e}" x2="${W-m.d}" y1="${Y(0)}" y2="${Y(0)}" stroke="${cv('eixo')}"/>`;
  const rot=op.rotX||[]; if(rot.length){const k_=Math.min(rot.length,op.nrot||6); for(let k=0;k<k_;k++){const i=Math.round((rot.length-1)*k/Math.max(1,k_-1));
    s+=`<text x="${X(i)}" y="${H-6}" text-anchor="middle" font-size="11" fill="${cv('mudo')}">${rot[i]}</text>`;}}
  series.forEach(se=>{const p=se.y.map((v,i)=>v===null?null:`${X(i).toFixed(1)},${Y(v).toFixed(1)}`).filter(Boolean).join(' ');
    s+=`<polyline fill="none" stroke="${se.cor}" stroke-width="${se.larg||1.8}" points="${p}" ${se.tr?'stroke-dasharray="5 4"':''}/>`;});
  s+='</svg>';
  el.innerHTML=`<div class="leg">${series.map(se=>`<span><i style="background:${se.cor}"></i>${se.nome}</span>`).join('')}</div>`+s;
}
const G2=[['r400','Stop 100 / alvo 400'],['claude','Gestao CLAUDE.md']], C2=[['todos','Todos os sinais'],['picado','So picado']];
const CORES=()=>[cv('tinta'),cv('azul'),cv('ganho'),cv('ouro'),cv('perda'),cv('alerta'),cv('prata'),'#8e44ad','#16a085'];
const CAB='<div class="tab"><table><thead><tr><th>Filtro</th><th>Trades</th><th>Liquido</th><th>Fator</th><th>Rebaixamento</th><th>Treino</th><th>Teste</th><th>Teste R$/trade</th><th>Atravessar 5 pts</th><th>Pregoes +</th></tr></thead><tbody>';
function lin(l,dest){const s=l.stats,o=l.oos,i=l.is_;
  return `<tr class="${dest?'dest':''}"><td>${l.nome}</td><td>${fmt(s.trades)}</td><td class="${cls(s.liquido)}">${rs(s.liquido)}</td><td>${fmt(s.fator_lucro,2)}</td><td>${rs(-s.dd_max)}</td>`+
    `<td class="${cls(i.liquido)}">${rs(i.liquido)}</td><td class="${cls(o.liquido)}">${rs(o.liquido)}</td><td class="${cls(o.exp_rs)}">${rs(o.exp_rs,1)}</td><td class="${cls(l.atravessa)}">${rs(l.atravessa)}</td><td>${fmt(s.dias_pos,0)}%</td></tr>`;}

/* consolidacao */
let cg='r400';
function desCons(){
  const Gd=T.consolidacao.grade.filter(x=>x.gestao===cg); const Ns=[...new Set(Gd.map(x=>x.N))], th=[...new Set(Gd.map(x=>x.thr))];
  const tab=(campo,neg)=>{const mx=Math.max(...Gd.map(x=>Math.abs(x[campo])));
    let h='<div class="tab"><table><thead><tr><th>Janela \\ limiar</th>'+th.map(t=>`<th>&ge; ${fmt(t,2)}</th>`).join('')+'</tr></thead><tbody>';
    Ns.forEach(N=>{h+=`<tr><td>${N} candles</td>`+th.map(t=>{const x=Gd.find(y=>y.N===N&&y.thr===t); const v=neg?-x[campo]:x[campo];
      return `<td style="background:${neg?alfa(cv('perda'),Math.min(.7,.05+x[campo]/mx*.6)):cor(v,mx)}" title="${fmt(x.n)} trades, fator ${fmt(x.fl,2)}">${rs(v)}</td>`;}).join('')+'</tr>';});
    return h+'</tbody></table></div>';};
  $('#t_grade').innerHTML=tab('liq'); $('#t_grade_oos').innerHTML=tab('oos'); $('#t_grade_dd').innerHTML=tab('dd',true);
  const L=T.consolidacao.direcao.filter(x=>x.gestao===cg).concat(T.consolidacao.combina.filter(x=>x.gestao===cg));
  $('#t_dir').innerHTML='<h3>Direcao da tendencia longa e combinacao com o filtro picado</h3>'+CAB+L.map((l,i)=>lin(l,l.nome.startsWith('fora da consolidacao 100 ('))).join('')+'</tbody></table></div>';
  const cs=CORES(); linhas($('#g_dir'),L.filter(l=>!l.nome.startsWith('  ')).map((l,i)=>({nome:l.nome,cor:cs[i%cs.length],y:l.eq,larg:l.nome.startsWith('fora da consolidacao 100 (')?2.6:1.4})),{alt:320});
}
abas('ab_cg',G2,cg,k=>{cg=k;desCons();});

/* dia */
let dg='r400',dc='todos';
function desDia(){const L=T.consolidacao.dia.filter(l=>l.gestao===dg&&l.conj===dc);
  $('#t_dia').innerHTML=CAB+L.map((l,i)=>lin(l,i===0)).join('')+'</tbody></table></div>';
  const cs=CORES(); linhas($('#g_dia'),L.map((l,i)=>({nome:l.nome,cor:cs[i%cs.length],y:l.eq,larg:i===0?2.4:1.5})),{alt:300});}
abas('ab_d_g',G2,dg,k=>{dg=k;desDia();}); abas('ab_d_c',C2,dc,k=>{dc=k;desDia();});

/* a priori */
let apg='r400',apc='todos';
function desAp(){const L=T.filtros_apriori[apg+'|'+apc];
  $('#t_ap').innerHTML=CAB+L.map((l,i)=>lin(Object.assign({},l,{nome:l.nome+` <span class="nota">(${fmt(l.frac*100,0)}% dos sinais)</span>`}),i===0)).join('')+'</tbody></table></div>';
  const cs=CORES(); linhas($('#g_ap'),L.map((l,i)=>({nome:l.nome,cor:cs[i%cs.length],y:l.eq,larg:i===0?2.4:1.4})),{alt:320});}
abas('ab_ap_g',G2,apg,k=>{apg=k;desAp();}); abas('ab_ap_c',C2,apc,k=>{apc=k;desAp();});

/* hipoteses */
let hg='r400',hc='todos';
function desHip(){const L=T.hipoteses.filter(h=>h.gestao===hg&&h.conj===hc); const mx=Math.max(...L.map(h=>Math.abs(h.ev)));
  let h='<div class="tab"><table><thead><tr><th>Condicao</th><th>Sinais</th><th>% dos sinais</th><th>R$/trade</th><th>Treino</th><th>Teste</th><th>Resto</th><th>t</th></tr></thead><tbody>';
  L.forEach(x=>h+=`<tr><td>${x.nome}</td><td>${fmt(x.n)}</td><td>${fmt(x.frac*100,0)}%</td><td class="${cls(x.ev)}">${rs(x.ev,1)}</td><td class="${cls(x.ev_is)}">${rs(x.ev_is,1)} <span class="nota">(${fmt(x.n_is)})</span></td><td class="${cls(x.ev_oos)}">${rs(x.ev_oos,1)} <span class="nota">(${fmt(x.n_oos)})</span></td><td class="${cls(x.resto)}">${rs(x.resto,1)}</td><td>${fmt(x.t_dif,2)}</td></tr>`);
  $('#t_hip').innerHTML=h+'</tbody></table></div>';}
abas('ab_h_g',G2,hg,k=>{hg=k;desHip();}); abas('ab_h_c',C2,hc,k=>{hc=k;desHip();});

/* varredura */
const NV={dir_abs_10:'EMA 21 variacao direta 10 (absoluta)',reg_abs_10:'EMA 21 regressao 10 (absoluta)',reg_r2_10:'R2 da EMA 21 em 10',dir_10:'EMA 21 variacao direta 10 (a favor)',
  reg_10:'EMA 21 regressao 10 (a favor)',er_100:'Eficiencia 100 candles',er_30:'Eficiencia 30 candles',mov_30:'Direcao 30 candles',amp_50:'Amplitude 50 candles',cruz_30:'Cruzamentos EMA 30',dia_mov:'Movimento desde a abertura'};
let vg='r400',vc='todos';
function desVarr(){const box=$('#g_varr'); box.innerHTML=T.varredura_cols.map(c=>`<div class="card"><b>${NV[c]||c}</b><div class="graf" id="v_${c}"></div></div>`).join('');
  T.varredura_cols.forEach(c=>{const P=T.varredura[vg+'|'+vc+'|'+c];
    linhas(document.getElementById('v_'+c),[{nome:'treino',cor:cv('azul'),y:P.map(p=>p.ev_is)},{nome:'teste',cor:cv('ouro'),y:P.map(p=>p.ev_oos),tr:1}],
      {alt:200,rotX:P.map(p=>p.pct_corte+'% ('+fmt(p.limiar,2)+')'),nrot:5});});}
abas('ab_v_g',G2,vg,k=>{vg=k;desVarr();}); abas('ab_v_c',C2,vc,k=>{vc=k;desVarr();});

/* mapa */
let mg='r400',mc='todos',mn='30';
function desMapa(){const Mp=T.mapas[mg+'|'+mc+'|'+mn]; const mx=Math.max(...Mp.celulas.map(c=>Math.abs(c.ev||0)));
  const rd=['contra','meio','a favor'], rc=['lateral','meio','tendencia'];
  let h=`<div class="tab"><table><thead><tr><th>Direcao ${mn} \\ eficiencia ${mn}</th>`+rc.map((r,i)=>`<th>${r}</th>`).join('')+'</tr></thead><tbody>';
  for(let a=0;a<3;a++){h+=`<tr><td>${rd[a]}</td>`; for(let b=0;b<3;b++){const c=Mp.celulas.find(x=>x.dir===a&&x.cons===b);
    h+=`<td style="background:${cor(c.ev,mx)}">${rs(c.ev,1)}<br><span class="nota">${rs(c.ev_is,0)} / ${rs(c.ev_oos,0)} &middot; ${fmt(c.n)}</span></td>`;} h+='</tr>';}
  $('#t_mapa').innerHTML=h+'</tbody></table></div><p class="nota">Cortes de direcao: '+Mp.qd.map(v=>fmt(v,0)).join(' / ')+' candles; eficiencia: '+Mp.qc.map(v=>fmt(v,2)).join(' / ')+'.</p>';}
abas('ab_m_g',G2,mg,k=>{mg=k;desMapa();}); abas('ab_m_c',C2,mc,k=>{mc=k;desMapa();}); abas('ab_m_n',[['20','20 candles'],['30','30 candles'],['50','50 candles']],mn,k=>{mn=k;desMapa();});

/* familias */
let fg='r400',fc='todos';
function desFam(){let h='';const key=fg+'|'+fc;
  T.familias.forEach(F=>{h+=`<h3>${F.familia}</h3><p class="nota">${F.desc}</p>`;
    F.blocos.forEach(B=>{const L=B.tabs[key], g=B.geral[key]; const mx=Math.max(1,...L.map(l=>Math.abs(l.ev||0)));
      h+=`<div class="card"><b>${B.rotulo}</b> <span class="nota">&middot; geral ${rs(g.ev,1)} (treino ${rs(g.ev_is,1)} / teste ${rs(g.ev_oos,1)})</span><div class="tab"><table><thead><tr><th>Faixa (quintis do treino)</th><th>Sinais</th><th>R$/trade</th><th>Winrate</th><th>Treino</th><th>Teste</th><th>Compra</th><th>Venda</th><th>Consistente?</th></tr></thead><tbody>`;
      L.forEach(l=>{const ok=(l.n_is>=25&&l.n_oos>=15)?((l.ev_is>g.ev_is)===(l.ev_oos>g.ev_oos)?(l.ev_is>g.ev_is?'<span class="tag pos">melhor nos dois</span>':'<span class="tag neg">pior nos dois</span>'):'<span class="tag">inverte</span>'):'<span class="nota">poucos</span>';
        h+=`<tr><td>${l.faixa}</td><td>${fmt(l.n)}</td><td class="${cls(l.ev)}">${rs(l.ev,1)}</td><td>${fmt(l.wr,1)}%</td><td class="${cls(l.ev_is)}">${rs(l.ev_is,1)} <span class="nota">(${fmt(l.n_is)})</span></td><td class="${cls(l.ev_oos)}">${rs(l.ev_oos,1)} <span class="nota">(${fmt(l.n_oos)})</span></td><td class="${cls(l.compra)}">${rs(l.compra,1)}</td><td class="${cls(l.venda)}">${rs(l.venda,1)}</td><td>${ok}</td></tr>`;});
      h+='</tbody></table></div></div>';});});
  $('#t_fam').innerHTML=h;}
abas('ab_f_g',G2,fg,k=>{fg=k;desFam();}); abas('ab_f_c',C2,fc,k=>{fc=k;desFam();});

/* selecao */
let sg='r400',sc='todos';
function desSel(){const key=sg+'|'+sc, P=T.placebo[key], Cd=T.candidatos[key];
  $('#t_plac').innerHTML=`<div class="kpis"><div class="kpi"><div class="r">Melhor t real no treino</div><div class="v">${fmt(P.max_t_real,2)}</div></div>`+
   `<div class="kpi"><div class="r">Placebo p95 / p99</div><div class="v">${fmt(P.p95_t,2)} / ${fmt(P.p99_t,2)}</div></div>`+
   `<div class="kpi"><div class="r">Bons no treino que melhoram no teste</div><div class="v">${fmt(P.frac_melhora_oos_bons_is*100,0)}%</div></div>`+
   `<div class="kpi"><div class="r">Top 10 que melhoram no teste</div><div class="v">${fmt(P.frac_melhora_oos_top10*100,0)}%</div></div></div>`+
   `<p class="nota">Sem filtro: ${rs(Cd.base_is,1)} por trade no treino, ${rs(Cd.base_oos,1)} no teste.</p>`;
  const Ct=T.carteiras[key];
  let h='<h3>Os 25 melhores cortes do treino</h3><div class="tab"><table><thead><tr><th>Corte</th><th>% sinais</th><th>R$/trade treino</th><th>t treino</th><th>R$/trade teste</th><th>Ganho no teste vs sem filtro</th></tr></thead><tbody>';
  Cd.lista.slice(0,25).forEach(c=>h+=`<tr><td>${c.nome}</td><td>${fmt(c.frac*100,0)}%</td><td class="${cls(c.ev_is)}">${rs(c.ev_is,1)}</td><td>${fmt(c.t_is,2)}</td><td class="${cls(c.ev_oos)}">${rs(c.ev_oos,1)}</td><td class="${cls(c.ganho_oos)}">${rs(c.ganho_oos,1)}</td></tr>`);
  h+='</tbody></table></div><h3>Em carteira: sem filtro e os 5 melhores do treino (um por atributo)</h3>'+CAB+Ct.map((l,i)=>lin(l,i===0)).join('')+'</tbody></table></div>';
  $('#t_sel').innerHTML=h;}
abas('ab_s_g',G2,sg,k=>{sg=k;desSel();}); abas('ab_s_c',C2,sc,k=>{sc=k;desSel();});

function tudo(){desCons();desDia();desAp();desHip();desVarr();desMapa();desFam();desSel();}
tudo();
let rz; addEventListener('resize',()=>{clearTimeout(rz);rz=setTimeout(tudo,200);});
$('#btema').addEventListener('click',()=>{const r=document.documentElement;
  const escuro=r.dataset.theme?r.dataset.theme==='dark':matchMedia('(prefers-color-scheme: dark)').matches;
  r.dataset.theme=escuro?'light':'dark'; tudo();});
"""

MENU = [('resumo', 'Resposta'), ('defs', 'Medidas'), ('consol', 'Consolidacao'), ('dia', 'Dia'), ('apriori', 'A priori'), ('hipoteses', 'Hipoteses'),
        ('varredura', 'Varredura'), ('mapa', 'Mapa'), ('familias', 'Faixas'), ('selecao', 'Acaso'), ('conclusao', 'Aplicar')]


def markdown():
    M = T['meta']
    L = ['# Filtros de tendencia geral e consolidacao', '',
         f"Complemento de `RESULTADOS.md`. {n(M['sinais'])} sinais, {M['pregoes']} pregoes ({M['inicio']} a {M['fim']}), entrada seca no fechamento, "
         f"6 contratos, R$ 0,50 por contrato. Treino ate {M['corte']}. Graficos e todas as tabelas em `tendencia.html`.", '',
         '## Consolidacao em 100 candles (eficiencia = |alta - baixa| / 100 antes do recuo)', '']
    for gk in ('r400', 'claude'):
        L += [f'**{NOME_G[gk]}**', '', '| Filtro | Trades | Liquido | Fator | Rebaixamento | Treino | Teste | Atravessar 5 pts |', '|:--|--:|--:|--:|--:|--:|--:|--:|']
        for l in [x for x in T['consolidacao']['direcao'] + T['consolidacao']['combina'] if x['gestao'] == gk]:
            s = l['stats']
            L.append(f"| {l['nome'].strip()} | {n(s['trades'])} | {rs(s['liquido'])} | {n(s['fator_lucro'], 2)} | {rs(-s['dd_max'])} | "
                     f"{rs(l['is_']['liquido'])} | {rs(l['oos']['liquido'])} | {rs(l['atravessa'])} |")
        L.append('')
    L += ['Grade janela x limiar (liquido, stop 100 / alvo 400):', '']
    g = [x for x in T['consolidacao']['grade'] if x['gestao'] == 'r400']
    ths = sorted({x['thr'] for x in g}); Ns = sorted({x['N'] for x in g})
    L += ['| Janela | ' + ' | '.join(f'>= {t}' for t in ths) + ' |', '|:--|' + '--:|' * len(ths)]
    for N in Ns:
        L.append(f'| {N} | ' + ' | '.join(rs(next(x['liq'] for x in g if x['N'] == N and x['thr'] == t)) for t in ths) + ' |')
    L += ['', '## Contexto do dia (carteira)', '', '| Gestao | Conjunto | Filtro | Trades | Liquido | Fator | Rebaix. | Treino | Teste |', '|:--|:--|:--|--:|--:|--:|--:|--:|--:|']
    for l in T['consolidacao']['dia']:
        s_ = l['stats']
        L.append(f"| {l['gestao']} | {l['conj']} | {l['nome']} | {n(s_['trades'])} | {rs(s_['liquido'])} | {n(s_['fator_lucro'], 2)} | {rs(-s_['dd_max'])} | "
                 f"{rs(l['is_']['liquido'])} | {rs(l['oos']['liquido'])} |")
    L += ['', '## Filtros definidos a priori (carteira)', '']
    for key, lin in T['filtros_apriori'].items():
        gk, ck = key.split('|')
        L += [f'**{NOME_G[gk]}, {NOME_C[ck]}**', '', '| Filtro | % sinais | Trades | Liquido | Fator | Rebaix. | Treino | Teste |', '|:--|--:|--:|--:|--:|--:|--:|--:|']
        for l in lin:
            s = l['stats']
            L.append(f"| {l['nome']} | {n(l['frac'] * 100, 0)}% | {n(s['trades'])} | {rs(s['liquido'])} | {n(s['fator_lucro'], 2)} | {rs(-s['dd_max'])} | "
                     f"{rs(l['is_']['liquido'])} | {rs(l['oos']['liquido'])} |")
        L.append('')
    L += ['## Hipoteses sinal a sinal (stop 100 / alvo 400, todos os sinais)', '',
          '| Condicao | % sinais | R$/trade | Treino | Teste | Resto | t |', '|:--|--:|--:|--:|--:|--:|--:|']
    for h in T['hipoteses']:
        if h['gestao'] == 'r400' and h['conj'] == 'todos':
            L.append(f"| {h['nome']} | {n(h['frac'] * 100, 0)}% | {rs(h['ev'], 1)} | {rs(h['ev_is'], 1)} | {rs(h['ev_oos'], 1)} | {rs(h['resto'], 1)} | {n(h['t_dif'], 2)} |")
    pl = T['placebo']
    L += ['', '## Controle de acaso', '', '| Gestao / conjunto | Cortes | Melhor t treino | Placebo p99 | Bons no treino que melhoram no teste |', '|:--|--:|--:|--:|--:|']
    for k, p in pl.items():
        gk, ck = k.split('|')
        L.append(f"| {NOME_G[gk]}, {NOME_C[ck]} | {p['n_cand']} | {n(p['max_t_real'], 2)} | {n(p['p99_t'], 2)} | {n(p['frac_melhora_oos_bons_is'] * 100, 0)}% |")
    L += ['', '## Conclusoes', '',
          '1. **Consolidacao em ~100 candles e o filtro de contexto que funciona**: sinais com |alta - baixa| < 8 nos 100 candles antes do recuo perderam no treino e ficaram perto de zero no teste; '
          'fora disso o resultado quase dobra e o rebaixamento cai pela metade. Vale com a tendencia longa a favor ou contra. O limiar 0,08 e pico de grade: use a faixa 0,06-0,10.',
          '2. **EMA 21 plana**: medir pela variacao direta (EMA - EMA[10]) ajuda pouco; a regressao linear de 10 candles nao ajuda. EMA "ondulada" (R2 baixo) tem efeito pequeno parecido.',
          '3. **Ultimos 20/30 candles contra o trade**: raro com a Hull a favor (2% / 12% dos sinais) e inverte entre treino e teste. Nao usar.',
          '4. **Dia**: os trades na direcao do dia (ou com o preco perto da abertura) perderam; os com o preco mais de 100 pts contra a abertura ganharam, nas duas metades. '
          'Achado na busca: candidato, nao regra.',
          '5. **Medias longas, gap, dia anterior, Keltner**: nada consistente; os cortes bons no treino melhoram o teste so ~metade das vezes.',
          '6. **Com o filtro picado**: E = mais estavel e menos lucro; OU = mais lucro, montado olhando os dados e ainda a confirmar.', '']
    return '\n'.join(L)


def main():
    html = ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Tendencia geral - filtros</title><style>{CSS}</style></head><body>'
            '<nav class="indice"><div class="wrap"><ul>' + ''.join(f'<li><a href="#{a}">{r}</a></li>' for a, r in MENU) +
            '</ul></div></nav><div class="wrap">' + corpo() + '</div>'
            '<button class="tema" id="btema" title="Alternar tema" aria-label="Alternar tema">&#9681;</button>'
            '<script>' + JS.replace('__T__', json.dumps(T, ensure_ascii=False)) + '</script></body></html>')
    open(os.path.join(BASE, 'tendencia.html'), 'w', encoding='utf-8').write(html)
    open(os.path.join(BASE, 'TENDENCIA.md'), 'w', encoding='utf-8').write(markdown())
    print('tendencia.html', round(len(html) / 1e6, 2), 'MB')


if __name__ == '__main__':
    main()
