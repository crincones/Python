# -*- coding: utf-8 -*-
"""
Gera relatorio.html (e os dados do trade a trade) a partir de saida/estudo.json
e saida/trades.json. Rodar depois de estudo.py.
"""
import json
import os
import numpy as np

import engine as E
import textos as TX

BASE = E.BASE
SAIDA = os.path.join(BASE, 'saida')
VENDOR = os.path.join(BASE, 'vendor', 'klinecharts-9.8.10.min.js')


def carrega_json(nome):
    with open(os.path.join(SAIDA, nome), encoding='utf-8') as f:
        return json.load(f)


def candles():
    d = E.indicadores(E.carrega())
    bruto = E.sinais(d, exige_ema=False, exige_macd=False)
    regra = E.sinais(d)
    r0 = lambda x: [None if np.isnan(v) else int(round(v)) for v in x]
    r1 = lambda x: [None if np.isnan(v) else round(float(v), 1) for v in x]
    C = dict(o=r0(d['o']), h=r0(d['h']), l=r0(d['l']), c=r0(d['c']),
             ema=r0(d['ema']), hma=r1(d['hma']), ks=r0(d['kc_sup']), ki=r0(d['kc_inf']),
             macd=r1(d['macd']), sig=r1(d['macd_sig']), bs=r1(d['bb_sup']), bi=r1(d['bb_inf']),
             dt=d['data'].dt.strftime('%d/%m/%y %H:%M').tolist())
    reg = {int(i): t for i, t in zip(regra['i'], regra['tipo'])}
    C['trig'] = [[int(i), int(l), reg.get(int(i), '')] for i, l in zip(bruto['i'], bruto['lado'])]
    return C


CSS = r"""
:root{--fundo:#f6f7f9;--card:#ffffff;--tinta:#16181d;--tinta2:#3d434d;--mudo:#6b7280;--grade:#e8eaee;
--eixo:#c9ced6;--ganho:#0f9d58;--perda:#d93025;--ouro:#c48a00;--prata:#7b8794;--azul:#1a73e8;
--alerta:#e37400;--ema:#f29900;--hull1:#1a56db;--hull2:#d93025;--kc:#a0a7b1;--linha:#e3e6eb;--realce:#eef4ff}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--fundo:#0f1115;--card:#171a20;--tinta:#e8eaed;
--tinta2:#c3c7cf;--mudo:#8b929c;--grade:#232730;--eixo:#3a404b;--ganho:#34c27a;--perda:#f26b5e;--ouro:#e0ad2e;
--prata:#9aa5b1;--azul:#6ea8fe;--alerta:#f5a524;--ema:#f5b43c;--hull1:#6ea8fe;--hull2:#f26b5e;--kc:#5d6570;
--linha:#262a33;--realce:#1b2433}}
:root[data-theme="dark"]{--fundo:#0f1115;--card:#171a20;--tinta:#e8eaed;--tinta2:#c3c7cf;--mudo:#8b929c;
--grade:#232730;--eixo:#3a404b;--ganho:#34c27a;--perda:#f26b5e;--ouro:#e0ad2e;--prata:#9aa5b1;--azul:#6ea8fe;
--alerta:#f5a524;--ema:#f5b43c;--hull1:#6ea8fe;--hull2:#f26b5e;--kc:#5d6570;--linha:#262a33;--realce:#1b2433}
*{box-sizing:border-box}
body{margin:0;background:var(--fundo);color:var(--tinta);font:15px/1.6 Inter,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding-inline:20px}
nav.indice{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--fundo) 88%,transparent);
backdrop-filter:blur(8px);border-bottom:1px solid var(--linha)}
nav.indice ul{list-style:none;margin:0;padding:8px 0;display:flex;gap:4px;flex-wrap:wrap}
nav.indice a{color:var(--tinta2);text-decoration:none;font-size:13px;padding:4px 10px;border-radius:999px}
nav.indice a:hover{background:var(--realce);color:var(--tinta)}
h1{font-size:30px;line-height:1.2;margin:34px 0 6px;letter-spacing:-.02em}
h2{font-size:22px;margin:44px 0 10px;letter-spacing:-.01em;padding-top:10px}
h3{font-size:16px;margin:24px 0 8px}
p,li{color:var(--tinta2)} b,strong{color:var(--tinta)}
.sub{color:var(--mudo);margin:0 0 20px}
.card{background:var(--card);border:1px solid var(--linha);border-radius:12px;padding:18px 20px;margin:14px 0}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin:14px 0}
.kpi{background:var(--card);border:1px solid var(--linha);border-radius:12px;padding:12px 14px}
.kpi .r{font-size:12px;color:var(--mudo);text-transform:uppercase;letter-spacing:.04em}
.kpi .v{font-size:22px;font-weight:650;margin-top:2px;font-variant-numeric:tabular-nums}
.pos{color:var(--ganho)} .neg{color:var(--perda)} .mudo{color:var(--mudo)}
.tab{overflow-x:auto;margin:10px 0}
table{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}
th,td{padding:6px 9px;border-bottom:1px solid var(--linha);text-align:right;white-space:nowrap}
th{color:var(--mudo);font-weight:600;font-size:12px;background:var(--card);position:sticky;top:0}
td:first-child,th:first-child{text-align:left}
td.l,th.l{text-align:left}
tr.dest td{background:var(--realce);font-weight:600}
.barra{display:inline-block;height:9px;border-radius:2px;vertical-align:middle;margin-right:6px}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:14px}
.graf{width:100%;min-height:120px}
.graf svg{display:block;width:100%;height:auto}
.leg{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--tinta2);margin:4px 0}
.leg i{display:inline-block;width:14px;height:3px;border-radius:2px;margin-right:5px;vertical-align:middle}
.abas{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}
.abas button,.btn{font:inherit;font-size:13px;border:1px solid var(--linha);background:var(--card);color:var(--tinta2);
padding:5px 12px;border-radius:999px;cursor:pointer}
.abas button.on{background:var(--tinta);color:var(--card);border-color:var(--tinta)}
select{font:inherit;font-size:13px;padding:5px 8px;border-radius:8px;border:1px solid var(--linha);background:var(--card);color:var(--tinta);max-width:100%}
.nota{font-size:13px;color:var(--mudo)}
.tag{display:inline-block;font-size:11px;font-weight:650;padding:1px 7px;border-radius:999px;background:var(--realce);color:var(--tinta2)}
.alerta{border-left:3px solid var(--alerta)} .ok{border-left:3px solid var(--ganho)} .ruim{border-left:3px solid var(--perda)}
#kchart{width:100%;height:620px}
.kinfo{display:flex;gap:14px;flex-wrap:wrap;font-size:13px;color:var(--tinta2);margin:8px 0}
.kbar{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
button.tema{position:fixed;right:16px;bottom:16px;width:40px;height:40px;border-radius:50%;border:1px solid var(--linha);
background:var(--card);color:var(--tinta);font-size:18px;cursor:pointer;z-index:9}
code{font-size:13px;background:var(--realce);padding:1px 5px;border-radius:4px}
@media (max-width:600px){h1{font-size:24px} #kchart{height:520px}}
"""

JS = r"""
const D=__DADOS__, TRD=__TRADES__, C=__CANDLES__;
const $=s=>document.querySelector(s);
function cv(k){return getComputedStyle(document.documentElement).getPropertyValue('--'+k).trim();}
function fmt(v,c=0){if(v===null||v===undefined||Number.isNaN(v))return '-';
  return Number(v).toLocaleString('pt-BR',{minimumFractionDigits:c,maximumFractionDigits:c});}
function rs(v,c=0){if(v===null||v===undefined)return '-';return (v>0?'+':v<0?'−':'')+'R$ '+fmt(Math.abs(v),c);}
function sn(v,c=0){if(v===null||v===undefined)return '-';return (v>0?'+':v<0?'−':'')+fmt(Math.abs(v),c);}
function cls(v){return v>0?'pos':v<0?'neg':'mudo';}
function alfa(hex,a){const h=hex.replace('#','');const x=h.length===3?h.split('').map(y=>y+y).join(''):h;
  const i=parseInt(x,16);return `rgba(${(i>>16)&255},${(i>>8)&255},${i&255},${a})`;}
const NS='http://www.w3.org/2000/svg';

/* ---------------------------------------------------------- linhas */
function linhas(sel,series,op={}){
  const el=$(sel); if(!el) return; const W=Math.max(320,el.clientWidth||700), H=op.alt||260;
  const m={e:64,d:14,t:12,b:26};
  let ys=[];series.forEach(s=>ys=ys.concat(s.y)); ys.push(0);
  let y0=Math.min(...ys), y1=Math.max(...ys); if(y1===y0){y1+=1;}
  const pad=(y1-y0)*.06; y0-=pad; y1+=pad;
  const nx=Math.max(...series.map(s=>s.y.length));
  const X=i=>m.e+(W-m.e-m.d)*(nx<=1?0:i/(nx-1)), Y=v=>m.t+(H-m.t-m.b)*(1-(v-y0)/(y1-y0));
  let s=`<svg viewBox="0 0 ${W} ${H}" role="img">`;
  const tk=5; for(let k=0;k<=tk;k++){const v=y0+(y1-y0)*k/tk;
    s+=`<line x1="${m.e}" x2="${W-m.d}" y1="${Y(v)}" y2="${Y(v)}" stroke="${cv('grade')}"/>`+
       `<text x="${m.e-6}" y="${Y(v)+4}" text-anchor="end" font-size="11" fill="${cv('mudo')}">${op.fy?op.fy(v):fmt(v)}</text>`;}
  s+=`<line x1="${m.e}" x2="${W-m.d}" y1="${Y(0)}" y2="${Y(0)}" stroke="${cv('eixo')}"/>`;
  const rot=op.rotX||[]; if(rot.length){const n=6; for(let k=0;k<n;k++){const i=Math.round((rot.length-1)*k/(n-1));
    s+=`<text x="${X(i)}" y="${H-8}" text-anchor="middle" font-size="11" fill="${cv('mudo')}">${rot[i]||''}</text>`;}}
  series.forEach(se=>{const p=se.y.map((v,i)=>`${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join(' ');
    s+=`<polyline fill="none" stroke="${se.cor}" stroke-width="${se.larg||1.8}" points="${p}" ${se.tr?'stroke-dasharray="4 3"':''}/>`;});
  s+='</svg>';
  const lg=series.map(se=>`<span><i style="background:${se.cor}"></i>${se.nome}</span>`).join('');
  el.innerHTML=(series.length>1||op.leg?`<div class="leg">${lg}</div>`:'')+s;
}
/* ---------------------------------------------------------- colunas */
function colunas(sel,bins,op={}){
  const el=$(sel); if(!el) return; const W=Math.max(320,el.clientWidth||600), H=op.alt||220;
  const m={e:44,d:10,t:14,b:34}; const n=bins.length; const vmax=Math.max(1,...bins.map(b=>b.v));
  const bw=(W-m.e-m.d)/n;
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  for(let k=0;k<=4;k++){const v=vmax*k/4,y=m.t+(H-m.t-m.b)*(1-k/4);
    s+=`<line x1="${m.e}" x2="${W-m.d}" y1="${y}" y2="${y}" stroke="${cv('grade')}"/><text x="${m.e-6}" y="${y+4}" text-anchor="end" font-size="11" fill="${cv('mudo')}">${fmt(v)}</text>`;}
  const passo=Math.ceil(n/12);
  bins.forEach((b,i)=>{const h=(H-m.t-m.b)*b.v/vmax, x=m.e+i*bw;
    s+=`<rect x="${x+1}" y="${H-m.b-h}" width="${Math.max(1,bw-2)}" height="${h}" fill="${b.cor||cv('azul')}" rx="1"><title>${b.rot}: ${fmt(b.v)}</title></rect>`;
    if(i%passo===0) s+=`<text x="${x+bw/2}" y="${H-m.b+14}" text-anchor="middle" font-size="10" fill="${cv('mudo')}">${b.rot}</text>`;});
  s+='</svg>'; el.innerHTML=s;
}
function histo(vals,passo,op={}){
  if(!vals.length) return [];
  const lo=Math.floor(Math.min(...vals)/passo)*passo, hi=Math.floor(Math.max(...vals)/passo)*passo;
  const out=[]; for(let v=lo;v<=hi;v+=passo) out.push({rot:fmt(v),v:0,cor:op.cor||(v+passo/2>0?cv('ganho'):v+passo/2<0?cv('perda'):cv('prata')),x:v});
  vals.forEach(x=>{const k=Math.floor((x-lo)/passo); if(out[k]) out[k].v++;}); return out;
}
function duracao(ds){const cs=[[0,60,'<1min'],[60,180,'1-3'],[180,300,'3-5'],[300,600,'5-10'],[600,1200,'10-20'],
  [1200,1800,'20-30'],[1800,3600,'30-60'],[3600,7200,'1-2h'],[7200,1e9,'>2h']];
  return cs.map(([a,b,r])=>({rot:r,v:ds.filter(x=>x>=a&&x<b).length,cor:cv('azul')}));}

/* ---------------------------------------------------------- tabelas */
function tabStats(sel,cols){
  const R=[['Trades','trades',s=>fmt(s.trades)],['Pregoes','dias',s=>fmt(s.dias)],['Trades por pregao','trades_dia',s=>fmt(s.trades_dia,1)],
   ['Lucro liquido','liquido',s=>rs(s.liquido),1],['Lucro bruto (ganhos)','bruto_ganho',s=>rs(s.bruto_ganho)],
   ['Perda bruta','bruto_perda',s=>rs(s.bruto_perda)],['Custos (R$ 0,50 x 6 por trade)','custo',s=>rs(-s.custo)],
   ['Fator de lucro','fator_lucro',s=>fmt(s.fator_lucro,2)],['Payoff (ganho medio / perda media)','payoff',s=>fmt(s.payoff,2)],
   ['Resultado esperado por trade','exp_rs',s=>rs(s.exp_rs,2),1],['Pontos por trade (bruto, por contrato)','pts_trade',s=>sn(s.pts_trade,1),1],
   ['Winrate (trades com lucro)','winrate',s=>fmt(s.winrate,1)+'%'],['Trades zerados (parcial + stop na media)','zeros',s=>fmt(s.zeros)],
   ['Maior ganho','maior_ganho',s=>rs(s.maior_ganho)],['Maior perda','maior_perda',s=>rs(s.maior_perda)],
   ['Ganho medio','media_ganho',s=>rs(s.media_ganho)],['Perda media','media_perda',s=>rs(s.media_perda)],
   ['Max. ganhos seguidos','max_seq_ganho',s=>fmt(s.max_seq_ganho)],['Max. perdas/zeros seguidos','max_seq_perda',s=>fmt(s.max_seq_perda)],
   ['Rebaixamento maximo','dd_max',s=>rs(-s.dd_max)],['Fator de recuperacao','recovery',s=>fmt(s.recovery,2)],
   ['Sharpe por trade','sharpe',s=>fmt(s.sharpe,3)],['Correlacao LR da curva','lr_corr',s=>fmt(s.lr_corr,2)],
   ['Pregoes positivos','dias_pos',s=>fmt(s.dias_pos,0)+'%'],['Pior pregao','pior_dia',s=>rs(s.pior_dia)],['Melhor pregao','melhor_dia',s=>rs(s.melhor_dia)],
   ['Compras (trades / R$)','longs',s=>fmt(s.longs)+' / '+rs(s.longs_rs)],['Vendas (trades / R$)','shorts',s=>fmt(s.shorts)+' / '+rs(s.shorts_rs)],
   ['Saidas: alvo / stop / zero / fim do dia','alvos',s=>`${fmt(s.alvos)} / ${fmt(s.stops)} / ${fmt(s.zeros_parc)} / ${fmt(s.fim_dia)}`]];
  let h='<div class="tab"><table><thead><tr><th>Estatistica</th>'+cols.map(c=>`<th>${c.nome}</th>`).join('')+'</tr></thead><tbody>';
  R.forEach(r=>{h+=`<tr><td>${r[0]}</td>`+cols.map(c=>{const s=c.s; if(!s||!s.trades) return '<td>-</td>';
    const v=s[r[1]]; return `<td class="${r[3]?cls(v):''}">${r[2](s)}</td>`;}).join('')+'</tr>';});
  $(sel).innerHTML=h+'</tbody></table></div>';
}
function barraRs(v,mx){const w=Math.min(60,Math.abs(v||0)/mx*60);
  return `<span class="barra" style="width:${w}px;background:${(v||0)>=0?cv('ganho'):cv('perda')}"></span>`;}

/* ---------------------------------------------------------- abas */
function abas(id,itens,ini,cb){const el=document.getElementById(id); if(!el) return;
  el.innerHTML=itens.map(([k,r])=>`<button data-k="${k}" class="${k===ini?'on':''}">${r}</button>`).join('');
  el.addEventListener('click',e=>{const b=e.target.closest('button'); if(!b) return;
    el.querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b)); cb(b.dataset.k);});}

const MODOS=[['fecha','Seca no fechamento'],['meio','Limitada no meio'],['extremo','Stop no extremo']];

/* ---------------------------------------------------------- base */
let bModo='fecha';
function desenhaBase(){
  const B=D.base[bModo].blocos;
  linhas('#g_base',[['todos','Todos',cv('tinta')],['T1','T1',cv('azul')],['T2','T2',cv('ouro')]].filter(([k])=>B[k].stats.trades)
    .map(([k,n,c])=>({nome:n+' ('+fmt(B[k].stats.trades)+' trades)',cor:c,y:B[k].curva.eq})),{alt:300,fy:v=>'R$ '+fmt(v),rotX:B.todos.curva.dt,leg:1});
  tabStats('#t_base',[{nome:'Todos',s:B.todos.stats},{nome:'T1',s:B.T1.stats},{nome:'T2',s:B.T2.stats}]);
}
function tabelaModos(){
  let h='<div class="tab"><table><thead><tr><th>Sistema de entrada</th><th>Bloco</th><th>Sinais executados</th><th>R$/sinal (isolado)</th><th>Winrate</th><th>Carteira: trades</th><th>Liquido</th><th>Fator</th><th>Rebaixamento</th></tr></thead><tbody>';
  MODOS.forEach(([m,nm])=>['todos','T1','T2'].forEach(k=>{const b=D.base[m].blocos[k],i=b.isolado,s=b.stats;
    h+=`<tr class="${k==='todos'?'dest':''}"><td>${k==='todos'?nm:''}</td><td class="l">${k}</td><td>${fmt(i.n)}</td><td class="${cls(i.ev_rs)}">${rs(i.ev_rs,2)}</td><td>${fmt(i.wr,1)}%</td>`+
       `<td>${fmt(s.trades)}</td><td class="${cls(s.liquido)}">${rs(s.liquido)}</td><td>${fmt(s.fator_lucro,2)}</td><td>${rs(-s.dd_max)}</td></tr>`;}));
  $('#t_modos').innerHTML=h+'</tbody></table></div>';
}

/* ---------------------------------------------------------- filtros */
let fModo='fecha';
function desenhaFiltros(){
  const F=D.filtros[fModo]; let grupos={}; F.forEach(f=>(grupos[f.grupo]=grupos[f.grupo]||[]).push(f));
  let h='';
  Object.entries(grupos).forEach(([g,fs])=>{h+=`<h3>${g}</h3>`;
    fs.forEach(f=>{const mx=Math.max(1,...f.linhas.map(l=>Math.abs(l.ev||0)));
      h+=`<div class="card"><b>${f.desc}</b> <span class="nota">&middot; media geral ${rs(f.geral,2)} por sinal</span><div class="tab"><table><thead><tr><th>Faixa</th><th>Sinais</th><th>R$/sinal</th><th>Winrate</th><th>Total</th><th>Treino</th><th>Teste</th><th>Compra</th><th>Venda</th><th>Consistente?</th></tr></thead><tbody>`;
      f.linhas.forEach(l=>{const melhor_is=l.ev_is>f.geral, melhor_oos=l.ev_oos>f.geral;
        const cons=(l.n_is>=30&&l.n_oos>=20)?(melhor_is===melhor_oos?(melhor_is?'<span class="tag pos">melhor nos dois</span>':'<span class="tag neg">pior nos dois</span>'):'<span class="tag">inverte</span>'):'<span class="nota">poucos</span>';
        h+=`<tr><td>${l.faixa}</td><td>${fmt(l.n)}</td><td class="${cls(l.ev)}">${barraRs(l.ev,mx)}${rs(l.ev,2)}</td><td>${fmt(l.wr,1)}%</td><td class="${cls(l.total)}">${rs(l.total)}</td>`+
           `<td class="${cls(l.ev_is)}">${rs(l.ev_is,2)} <span class="nota">(${fmt(l.n_is)})</span></td><td class="${cls(l.ev_oos)}">${rs(l.ev_oos,2)} <span class="nota">(${fmt(l.n_oos)})</span></td>`+
           `<td class="${cls(l.compra)}">${rs(l.compra,2)}</td><td class="${cls(l.venda)}">${rs(l.venda,2)}</td><td>${cons}</td></tr>`;});
      h+='</tbody></table></div></div>';});});
  $('#filtros_corpo').innerHTML=h;
}
function tabelaSelecao(){
  let h='';
  MODOS.forEach(([m,nm])=>{const P=D.selecao[m].passos;
    h+=`<h3>${nm}</h3><div class="tab"><table><thead><tr><th>Passo (escolhido so no treino)</th><th>Sinais treino</th><th>R$/sinal treino</th><th>t treino</th><th>Sinais teste</th><th>R$/sinal teste</th></tr></thead><tbody>`;
    P.forEach((p,i)=>h+=`<tr class="${i===P.length-1?'dest':''}"><td>${i?'+ ':''}${p.filtro}</td><td>${fmt(p.n_is)}</td><td class="${cls(p.ev_is)}">${rs(p.ev_is,2)}</td><td>${fmt(p.t_is,2)}</td><td>${fmt(p.n_oos)}</td><td class="${cls(p.ev_oos)}">${rs(p.ev_oos,2)}</td></tr>`);
    h+='</tbody></table></div>';});
  $('#t_selecao').innerHTML=h;
}

/* ---------------------------------------------------------- gestao */
let gModo='fecha', gConj='todos', gMetr='ev';
function desenhaGestao(){
  const L=D.gestao[gModo][gConj];
  const parciais=[...new Set(L.map(l=>l.parcial+'|'+l.apos))];
  const stops=[...new Set(L.map(l=>l.stop))], alvos=[...new Set(L.map(l=>l.alvo))].sort((a,b)=>a-b);
  const vals=L.map(l=>l[gMetr]).filter(v=>v!==null); const mx=Math.max(...vals.map(Math.abs),1);
  const cor=v=>v===null||v===undefined?'transparent':alfa(v>=0?cv('ganho'):cv('perda'),Math.min(.85,.08+Math.abs(v)/mx*.75));
  const f=v=>gMetr==='cart_liq'?rs(v):gMetr==='wr'?fmt(v,0)+'%':rs(v,1);
  let h='';
  parciais.forEach(pk=>{const [pc,ap]=pk.split('|');
    h+=`<div class="card"><b>Parcial: ${pc}</b>${ap!=='-'?` <span class="nota">&middot; stop do restante na ${ap==='media'?'media da operacao (zero a zero)':'entrada'}</span>`:''}<div class="tab"><table><thead><tr><th>Stop \\ Alvo</th>`+
      alvos.map(a=>`<th>+${a}</th>`).join('')+'</tr></thead><tbody>';
    stops.forEach(st=>{h+=`<tr><td>${st===null?'extremo do candle':st+' pts'}</td>`;
      alvos.forEach(a=>{const l=L.find(x=>x.stop===st&&x.alvo===a&&x.parcial===pc&&x.apos===ap);
        h+=l?`<td style="background:${cor(l[gMetr])}" title="treino ${rs(l.ev_is,1)} / teste ${rs(l.ev_oos,1)} / carteira ${rs(l.cart_liq)} / DD ${rs(-l.cart_dd)}">${f(l[gMetr])}</td>`:'<td class="mudo">-</td>';});
      h+='</tr>';});
    h+='</tbody></table></div></div>';});
  $('#gestao_corpo').innerHTML=h;
  const top=[...L].filter(l=>l.n>=100).sort((a,b)=>b.ev_is-a.ev_is).slice(0,12);
  let t='<div class="tab"><table><thead><tr><th>Stop</th><th>Alvo</th><th>Parcial</th><th>Stop apos parcial</th><th>Sinais</th><th>R$/sinal treino</th><th>R$/sinal teste</th><th>Winrate</th><th>Carteira liquido</th><th>Rebaixamento</th><th>Fator</th></tr></thead><tbody>';
  top.forEach((l,i)=>t+=`<tr class="${i===0?'dest':''}"><td>${l.stop===null?'extremo':l.stop}</td><td>+${l.alvo}</td><td class="l">${l.parcial}</td><td class="l">${l.apos}</td><td>${fmt(l.n)}</td><td class="${cls(l.ev_is)}">${rs(l.ev_is,2)}</td><td class="${cls(l.ev_oos)}">${rs(l.ev_oos,2)}</td><td>${fmt(l.wr,1)}%</td><td class="${cls(l.cart_liq)}">${rs(l.cart_liq)}</td><td>${rs(-l.cart_dd)}</td><td>${fmt(l.cart_fl,2)}</td></tr>`);
  $('#gestao_top').innerHTML=t+'</tbody></table></div>';
}

/* ---------------------------------------------------------- robustez / carteira */
const VARS=Object.keys(D.robustez);
let rVar=D.escolhida||VARS[0];
function desenhaCarteira(){
  const R=D.robustez[rVar];
  $('#r_nome').innerHTML=`<b>${R.nome}</b>`+(R.filtros.length?` <span class="nota">&middot; filtros: ${R.filtros.join(' &middot; ')}</span>`:'')+
    (R.gestao?` <span class="nota">&middot; gestao: stop ${R.gestao.stop===null?'extremo':R.gestao.stop}, alvo +${R.gestao.alvo}, parcial ${R.gestao.parcial}${R.gestao.apos!=='-'?' (stop '+R.gestao.apos+')':''}</span>`:' <span class="nota">&middot; gestao do CLAUDE.md: stop 100, parcial 50% em +100, alvo +300</span>');
  const s=R.stats;
  $('#r_kpis').innerHTML=[['Liquido',rs(s.liquido),cls(s.liquido)],['Trades',fmt(s.trades),''],['Fator de lucro',fmt(s.fator_lucro,2),''],
    ['Winrate',fmt(s.winrate,1)+'%',''],['Rebaixamento max.',rs(-s.dd_max),'neg'],['Treino / Teste',rs(R.stats_is.liquido)+' / '+rs(R.stats_oos.liquido),cls(R.stats_oos.liquido)]]
    .map(([r,v,c])=>`<div class="kpi"><div class="r">${r}</div><div class="v ${c}">${v}</div></div>`).join('');
  linhas('#g_eq',[{nome:'Patrimonio (6 contratos, liquido)',cor:cv('azul'),y:R.curva.eq,larg:2}],{alt:300,fy:v=>'R$ '+fmt(v),rotX:R.curva.dt});
  const pico=[];let p=0;R.curva.eq.forEach(v=>{p=Math.max(p,v);pico.push(v-p);});
  linhas('#g_dd',[{nome:'Rebaixamento',cor:cv('perda'),y:pico}],{alt:160,fy:v=>'R$ '+fmt(v),rotX:R.curva.dt});
  tabStats('#t_mt5',[{nome:'Base inteira',s:R.stats},{nome:'Treino (ate '+D.meta.corte+')',s:R.stats_is},{nome:'Teste (fora da amostra)',s:R.stats_oos}]);
  const pv=D.val_ponto*D.meta.contratos;
  colunas('#g_res',histo(R.rs,30),{alt:220});
  colunas('#g_mep',histo(R.mfe,25,{cor:cv('ganho')}),{alt:220});
  colunas('#g_men',histo(R.mae,25,{cor:cv('perda')}),{alt:220});
  colunas('#g_dur',duracao(R.dur),{alt:220});
  colunas('#g_hora',R.hora.map(h=>({rot:h.hora+'h',v:Math.abs(h.sum),cor:h.sum>=0?cv('ganho'):cv('perda')})),{alt:200});
  $('#t_hora').innerHTML='<div class="tab"><table><thead><tr><th>Hora</th>'+R.hora.map(h=>`<th>${h.hora}h</th>`).join('')+'</tr></thead><tbody><tr><td>Trades</td>'+
    R.hora.map(h=>`<td>${fmt(h.count)}</td>`).join('')+'</tr><tr><td>Liquido</td>'+R.hora.map(h=>`<td class="${cls(h.sum)}">${rs(h.sum)}</td>`).join('')+'</tr></tbody></table></div>';
  // meses
  let m='<div class="tab"><table><thead><tr><th>Mes</th><th>Trades</th><th>Liquido</th><th>R$/trade</th></tr></thead><tbody>';
  R.meses.forEach(x=>m+=`<tr><td>${x.data}</td><td>${fmt(x.count)}</td><td class="${cls(x.sum)}">${barraRs(x.sum,Math.max(...R.meses.map(y=>Math.abs(y.sum))))}${rs(x.sum)}</td><td class="${cls(x.mean)}">${rs(x.mean,2)}</td></tr>`);
  $('#t_meses').innerHTML=m+'</tbody></table></div>';
  // monte carlo
  const M=R.mc;
  $('#t_mc').innerHTML=`<div class="tab"><table><thead><tr><th>Monte Carlo (5.000 reamostragens dos trades)</th><th>p5</th><th>p25</th><th>mediana</th><th>p75</th><th>p95</th></tr></thead><tbody>`+
    `<tr><td>Resultado final</td>${[5,25,50,75,95].map(q=>`<td class="${cls(M.final[q])}">${rs(M.final[q])}</td>`).join('')}</tr>`+
    `<tr><td>Rebaixamento maximo</td>${[5,25,50,75,95].map(q=>`<td>${rs(-M.dd[q])}</td>`).join('')}</tr></tbody></table></div>`+
    `<p class="nota">Probabilidade de terminar no prejuizo: <b>${fmt(M.p_prejuizo,1)}%</b>.</p>`;
  colunas('#g_mc',M.hist_final.map((v,i)=>({rot:fmt(M.bins_final[i]/1000,0)+'k',v:v,cor:M.bins_final[i]+ (M.bins_final[1]-M.bins_final[0])/2>=0?cv('ganho'):cv('perda')})),{alt:200});
  colunas('#g_mcdd',M.hist_dd.map((v,i)=>({rot:fmt(M.bins_dd[i]/1000,1)+'k',v:v,cor:cv('perda')})),{alt:200});
  const A=R.aleatorio;
  $('#t_aleat').innerHTML=`<div class="tab"><table><thead><tr><th>Entradas aleatorias com a mesma gestao</th><th>R$/trade</th></tr></thead><tbody>`+
    `<tr><td>Estrategia</td><td class="${cls(A.ev_real)}">${rs(A.ev_real,2)}</td></tr><tr><td>Aleatorio (media)</td><td class="${cls(A.ev_aleat)}">${rs(A.ev_aleat,2)}</td></tr>`+
    `<tr><td>Aleatorio, faixa p5-p95 com o mesmo numero de trades</td><td>${rs(A.p5,2)} a ${rs(A.p95,2)}</td></tr>`+
    `<tr class="dest"><td>Percentil da estrategia contra o aleatorio</td><td>${fmt(A.percentil,1)}</td></tr></tbody></table></div>`;
  $('#t_estresse').innerHTML='<div class="tab"><table><thead><tr><th>Escorregamento extra (pts por contrato, por trade)</th><th>Liquido</th><th>R$/trade</th></tr></thead><tbody>'+
    R.estresse.map(e=>`<tr><td>${e.slip} pts</td><td class="${cls(e.liquido)}">${rs(e.liquido)}</td><td class="${cls(e.ev)}">${rs(e.ev,2)}</td></tr>`).join('')+
    '</tbody></table></div><div class="tab"><table><thead><tr><th>Sem os melhores trades</th><th>Liquido</th></tr></thead><tbody>'+
    R.sem_top.map(e=>`<tr><td>${e.pct?'sem os '+e.pct+'% melhores':'todos'}</td><td class="${cls(e.liquido)}">${rs(e.liquido)}</td></tr>`).join('')+'</tbody></table></div>';
}
function tabelaVariantes(){
  let h='<div class="tab"><table><thead><tr><th>Variante</th><th>Trades</th><th>Liquido</th><th>Fator</th><th>Rebaix.</th><th>Treino</th><th>Teste</th><th>Teste R$/trade</th><th>MC p(prejuizo)</th><th>Percentil vs aleatorio</th></tr></thead><tbody>';
  VARS.forEach(k=>{const R=D.robustez[k],s=R.stats,o=R.stats_oos;
    h+=`<tr class="${k===D.escolhida?'dest':''}"><td>${R.nome}</td><td>${fmt(s.trades)}</td><td class="${cls(s.liquido)}">${rs(s.liquido)}</td><td>${fmt(s.fator_lucro,2)}</td><td>${rs(-s.dd_max)}</td>`+
      `<td class="${cls(R.stats_is.liquido)}">${rs(R.stats_is.liquido)}</td><td class="${cls(o.liquido)}">${rs(o.liquido)}</td><td class="${cls(o.exp_rs)}">${rs(o.exp_rs,2)}</td><td>${fmt(R.mc.p_prejuizo,1)}%</td><td>${fmt(R.aleatorio.percentil,0)}</td></tr>`;});
  $('#t_variantes').innerHTML=h+'</tbody></table></div>';
  const cores=[cv('tinta'),cv('azul'),cv('ouro'),cv('ganho'),cv('perda'),cv('alerta'),cv('prata'),'#8e44ad','#16a085'];
  linhas('#g_variantes',VARS.map((k,i)=>({nome:D.robustez[k].nome,cor:cores[i%cores.length],y:D.robustez[k].curva.eq,larg:k===D.escolhida?2.6:1.3})),{alt:340,fy:v=>'R$ '+fmt(v)});
}
function tabelaViz(){
  let h='<div class="tab"><table><thead><tr><th>Candles contra</th><th>Pavio fech.</th><th>Tolerancia EMA</th><th>MACD</th><th>Sinais</th><th>R$/sinal</th><th>Treino</th><th>Teste</th><th>Carteira</th><th>Rebaix.</th><th>Fator</th></tr></thead><tbody>';
  D.vizinhanca.forEach((v,i)=>h+=`<tr class="${i===0?'dest':''}"><td>${v.barras}</td><td>${v.pavio}</td><td>${v.tol_ema}</td><td>${v.macd}</td><td>${fmt(v.n)}</td><td class="${cls(v.ev)}">${rs(v.ev,2)}</td><td class="${cls(v.ev_is)}">${rs(v.ev_is,2)}</td><td class="${cls(v.ev_oos)}">${rs(v.ev_oos,2)}</td><td class="${cls(v.cart_liq)}">${rs(v.cart_liq)}</td><td>${rs(-v.cart_dd)}</td><td>${fmt(v.cart_fl,2)}</td></tr>`);
  $('#t_viz').innerHTML=h+'</tbody></table></div>';
}

/* ================================================================ kline */
const SANS='Inter,system-ui,-apple-system,"Segoe UI",sans-serif';
const T0=Date.UTC(2000,0,1), TB=60000;
let kchart=null, KL=[], KTR=[], kidx=0, kVar=D.escolhida||VARS[0];
const TRIG={}; C.trig.forEach(([i,l,t])=>{TRIG[i]=TRIG[i]||[];TRIG[i].push([l,t]);});

klinecharts.registerIndicator({name:'EMA21H50',shortName:'',series:'price',precision:0,
  figures:[{key:'ks',title:'Keltner+: ',type:'line'},{key:'ki',title:'Keltner-: ',type:'line'},
    {key:'ema',title:'EMA21: ',type:'line'},
    {key:'hma',title:'Hull50: ',type:'line',styles:(dd)=>{const a=dd.prev&&dd.prev.indicatorData,b=dd.current&&dd.current.indicatorData;
      if(!a||!b||a.hma==null||b.hma==null) return {color:cv('hull1')};
      return {color:b.hma>=a.hma?cv('hull1'):cv('hull2')};}}],
  calc:dl=>dl.map(k=>({ks:k.ks,ki:k.ki,ema:k.ema,hma:k.hma}))});
klinecharts.registerIndicator({name:'MACDBB',shortName:'MACD 9/14/9 + BB1000',precision:1,
  figures:[{key:'bs',title:'BB+: ',type:'line'},{key:'bi',title:'BB-: ',type:'line'},{key:'z',title:'',type:'line'},
    {key:'sig',title:'Sinal: ',type:'line'},{key:'macd',title:'MACD: ',type:'line',
     styles:(dd)=>{const b=dd.current&&dd.current.indicatorData; return {color:(b&&b.macd>=0)?cv('ganho'):cv('perda')};}}],
  calc:dl=>dl.map(k=>({bs:k.bs,bi:k.bi,z:0,sig:k.sig,macd:k.macd}))});
klinecharts.registerOverlay({name:'seta',totalStep:2,lock:true,needDefaultPointFigure:false,needDefaultXAxisFigure:false,needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates})=>{const e=overlay.extendData,x=coordinates[0].x,y=coordinates[0].y,s=e.tam||6;
    const pts=e.lado>0?[{x:x,y:y},{x:x-s,y:y+s*1.4},{x:x+s,y:y+s*1.4}]:[{x:x,y:y},{x:x-s,y:y-s*1.4},{x:x+s,y:y-s*1.4}];
    const f=[{type:'polygon',ignoreEvent:true,attrs:{coordinates:pts},styles:{style:e.cheio?'fill':'stroke',color:e.cor,borderColor:e.cor,borderSize:1}}];
    if(e.rot) f.push({type:'text',ignoreEvent:true,attrs:{x:x,y:e.lado>0?y+s*1.4+3:y-s*1.4-3,text:e.rot,align:'center',baseline:e.lado>0?'top':'bottom'},
      styles:{color:e.cor,size:10,family:SANS,weight:'700',backgroundColor:'transparent'}});
    return f;}});
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
  const lin=(c,tr)=>({color:c,size:tr?1:1.6,style:tr?'dashed':'solid',dashedValue:[4,3],smooth:false});
  return {grid:{horizontal:{color:g},vertical:{color:g}},
    candle:{bar:{upColor:cv('card'),downColor:cv('prata'),noChangeColor:m,upBorderColor:cv('tinta2'),downBorderColor:cv('tinta2'),
      noChangeBorderColor:m,upWickColor:cv('tinta2'),downWickColor:cv('tinta2'),noChangeWickColor:m},priceMark:{last:{show:false},high:{show:false},low:{show:false}},
      tooltip:{showRule:'follow_cross',text:{color:cv('tinta'),family:SANS,size:11}}},
    indicator:{lines:[lin(cv('kc'),1),lin(cv('kc'),1),lin(cv('ema'),1),lin(cv('hull1')),lin(cv('perda'))],
      tooltip:{showRule:'follow_cross',showName:false,showParams:false,text:{color:cv('tinta2'),family:SANS,size:11}}},
    xAxis:{axisLine:{color:cv('eixo')},tickText:{color:m,family:SANS,size:11}},
    yAxis:{axisLine:{color:cv('eixo')},tickText:{color:m,family:SANS,size:11}},
    separator:{color:cv('linha')},
    crosshair:{horizontal:{line:{color:m},text:{backgroundColor:cv('tinta2')}},vertical:{line:{color:m},text:{backgroundColor:cv('tinta2')}}}};}
function estiloMacd(){const lin=(c,tr,s)=>({color:c,size:s||1,style:tr?'dashed':'solid',dashedValue:[4,3],smooth:false});
  return {lines:[lin(cv('prata'),1),lin(cv('prata'),1),lin(cv('eixo'),0),lin(cv('alerta'),0,1.2),lin(cv('ganho'),0,1.8)]};}
function iniciaK(){
  const N=C.o.length;
  for(let i=0;i<N;i++) KL.push({timestamp:T0+i*TB,open:C.o[i],high:C.h[i],low:C.l[i],close:C.c[i],volume:0,
    ema:C.ema[i],hma:C.hma[i],ks:C.ks[i],ki:C.ki[i],macd:C.macd[i],sig:C.sig[i],bs:C.bs[i],bi:C.bi[i]});
  kchart=klinecharts.init('kchart',{styles:estiloK(),customApi:{formatDate:(f,ts,fm,tipo)=>{const i=Math.round((ts-T0)/TB);
    const s=(i>=0&&i<N)?C.dt[i]:''; return tipo===2?s.slice(9):s;}}});
  kchart.setPriceVolumePrecision(0,0);
  kchart.createIndicator('EMA21H50',true,{id:'candle_pane'});
  kchart.createIndicator('MACDBB',false,{id:'macd_pane',height:150});
  kchart.overrideIndicator({name:'MACDBB',styles:estiloMacd()},'macd_pane');
  kchart.applyNewData(KL);
  listaK(); mostraK(0);
}
function listaK(){
  KTR=TRD[kVar]||[];
  const ft=$('#kfiltro').value;
  KTR=KTR.filter(t=>ft==='todos'||(ft==='T1'&&t.tipo==='T1')||(ft==='T2'&&t.tipo==='T2')||(ft==='ganho'&&t.rs>0)||(ft==='perda'&&t.rs<0)||(ft==='zero'&&t.pts===0));
  $('#ksel').innerHTML=KTR.map((t,i)=>`<option value="${i}">#${i+1} · ${t.data} · ${t.lado>0?'compra':'venda'} ${t.tipo} · ${rs(t.rs)}</option>`).join('');
}
function mostraK(i){
  if(!kchart||!KTR.length){ $('#kinfo').innerHTML='<span>Nenhum trade neste filtro.</span>'; return;}
  kidx=Math.max(0,Math.min(KTR.length-1,i)); const t=KTR[kidx], ld=t.lado, R=D.robustez[kVar], G=Object.assign({alvo:300,parcial:true,parcial_em:100,frac:.5,apos:'media'},R.G);
  kchart.removeOverlay();
  let de=Math.max(0,t.v0-45); while(de<t.v0&&C.dt[de].slice(0,8)!==C.dt[t.v0].slice(0,8)) de++; const ate=Math.min(KL.length-1,t.i_sai+15), jan=ate-de+1;
  const larg=(kchart.getSize('candle_pane','main')||{}).width||900;
  const esp=Math.max(2,Math.min(28,larg/(jan+8))); kchart.setBarSpace(esp); kchart.scrollToDataIndex(ate+4);
  const ts=k=>KL[k].timestamp;
  kchart.createOverlay({name:'zona',points:[{timestamp:ts(t.v0)},{timestamp:ts(t.i)}],extendData:{cor:alfa(cv('azul'),.10),meia:esp/2}});
  kchart.createOverlay({name:'zona',points:[{timestamp:ts(t.i_ent)},{timestamp:ts(t.i_sai)}],extendData:{cor:alfa(t.rs>=0?cv('ganho'):cv('perda'),.07),meia:esp/2}});
  for(let k=de;k<=ate;k++){(TRIG[k]||[]).forEach(([l,tp])=>{
    kchart.createOverlay({name:'seta',points:[{timestamp:ts(k),value:l>0?KL[k].low-25:KL[k].high+25}],
      extendData:{lado:l,cor:tp?cv('azul'):cv('prata'),cheio:!!tp,tam:k===t.i?7:5,rot:k===t.i?tp:''}});});}
  const pe=t.preco_ent, fim=ts(Math.min(KL.length-1,t.i_sai+3));
  const niv=[{v:pe-ld*t.stop_pts,rot:'stop −'+fmt(t.stop_pts),cor:cv('perda')},{v:pe+ld*G.alvo,rot:'alvo +'+G.alvo,cor:cv('ganho')}];
  if(G.parcial!==false) niv.push({v:pe+ld*G.parcial_em,rot:'parcial +'+G.parcial_em,cor:cv('ganho'),tr:1});
  niv.forEach(n=>kchart.createOverlay({name:'nivel',points:[{timestamp:ts(t.i_ent),value:n.v},{timestamp:fim,value:n.v}],extendData:n}));
  kchart.createOverlay({name:'marca',points:[{timestamp:ts(t.i_ent),value:pe}],extendData:{cor:cv('azul'),rot:(ld>0?'C ':'V ')+fmt(pe)}});
  kchart.createOverlay({name:'marca',points:[{timestamp:ts(t.i_sai),value:t.preco_sai}],extendData:{cor:t.rs>=0?cv('ganho'):cv('perda'),rot:'saida '+fmt(t.preco_sai)}});
  $('#ksel').value=String(kidx);
  const MOT={alvo:'alvo',stop:'stop',stop_zero:'parcial + stop na media',stop_be:'stop na entrada',fim_dia:'fim do pregao',tempo:'tempo'};
  $('#kinfo').innerHTML=`<span><b>#${kidx+1}</b> de ${fmt(KTR.length)}</span><span>${t.data}</span><span><b>${ld>0?'▲ compra':'▼ venda'} ${t.tipo}</b> (${t.n_contra} contra)</span>`+
    `<span>entrada <b>${fmt(pe)}</b></span><span>stop ${fmt(t.stop_pts)} pts</span><span>saida <b>${fmt(t.preco_sai)}</b> (${MOT[t.motivo]||t.motivo})</span>`+
    `<span>${sn(t.pts,0)} pts/contrato</span><span>resultado <b class="${cls(t.rs)}">${rs(t.rs)}</b></span><span>MEP ${sn(t.mfe)} · MEN ${sn(t.mae)}</span>`;
}
function trocaK(){listaK(); mostraK(0);}

/* ================================================================ init */
function desenhaTudo(){desenhaBase(); tabelaModos(); desenhaFiltros(); tabelaSelecao(); desenhaGestao(); desenhaCarteira(); tabelaVariantes(); tabelaViz();}
abas('abas_base',MODOS,bModo,k=>{bModo=k;desenhaBase();});
abas('abas_filtro',MODOS,fModo,k=>{fModo=k;desenhaFiltros();});
abas('abas_gmodo',MODOS,gModo,k=>{gModo=k;desenhaGestao();});
abas('abas_gconj',[['todos','Todos os sinais'],['filtrados','Sinais filtrados']],gConj,k=>{gConj=k;desenhaGestao();});
abas('abas_gmetr',[['ev','R$/sinal (base inteira)'],['ev_is','R$/sinal treino'],['ev_oos','R$/sinal teste'],['cart_liq','Carteira liquido'],['wr','Winrate']],gMetr,k=>{gMetr=k;desenhaGestao();});
const selV=v=>VARS.map(k=>`<option value="${k}" ${k===v?'selected':''}>${D.robustez[k].nome}</option>`).join('');
$('#rsel').innerHTML=selV(rVar); $('#rsel').addEventListener('change',e=>{rVar=e.target.value;desenhaCarteira();});
$('#kvar').innerHTML=selV(kVar); $('#kvar').addEventListener('change',e=>{kVar=e.target.value;trocaK();});
$('#kfiltro').addEventListener('change',trocaK);
$('#ksel').addEventListener('change',e=>mostraK(+e.target.value));
$('#kant').addEventListener('click',()=>mostraK(kidx-1)); $('#kprox').addEventListener('click',()=>mostraK(kidx+1));
addEventListener('keydown',ev=>{if(['SELECT','INPUT'].includes(ev.target.tagName))return;
  if(ev.key==='ArrowLeft')mostraK(kidx-1); if(ev.key==='ArrowRight')mostraK(kidx+1);});
desenhaTudo(); iniciaK();
let rz; addEventListener('resize',()=>{clearTimeout(rz);rz=setTimeout(()=>{desenhaTudo();kchart&&kchart.resize();},200);});
$('#btema').addEventListener('click',()=>{const r=document.documentElement;
  const escuro=r.dataset.theme?r.dataset.theme==='dark':matchMedia('(prefers-color-scheme: dark)').matches;
  r.dataset.theme=escuro?'light':'dark'; desenhaTudo(); if(kchart){kchart.setStyles(estiloK());
  kchart.overrideIndicator({name:'MACDBB',styles:estiloMacd()},'macd_pane'); mostraK(kidx);}});
"""

MENU = [('resumo', 'Resumo'), ('regras', 'Regras'), ('base', 'Resultado base'), ('filtros', 'Filtros'),
        ('selecao', 'Selecao'), ('gestao', 'Gestao'), ('variantes', 'Variantes'), ('carteira', 'Carteira'),
        ('robustez', 'Robustez'), ('kline', 'Trade a trade'), ('conclusao', 'Conclusao')]


def monta():
    D = carrega_json('estudo.json')
    T = carrega_json('trades.json')
    D['escolhida'] = TX.ESCOLHIDA
    D['val_ponto'] = E.VAL_PONTO
    Cd = candles()
    with open(VENDOR, encoding='utf-8') as f:
        kc = f.read()
    corpo = TX.corpo_html(D)
    js = (JS.replace('__DADOS__', json.dumps(D, ensure_ascii=False))
          .replace('__TRADES__', json.dumps(T, ensure_ascii=False))
          .replace('__CANDLES__', json.dumps(Cd, separators=(',', ':'))))
    html = ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>EMA21 no grafico PI - backtest</title>'
            f'<style>{CSS}</style></head><body>'
            '<nav class="indice"><div class="wrap"><ul>'
            + ''.join(f'<li><a href="#{a}">{r}</a></li>' for a, r in MENU) +
            '</ul></div></nav><div class="wrap">' + corpo + '</div>'
            '<button class="tema" id="btema" title="Alternar tema" aria-label="Alternar tema">&#9681;</button>'
            f'<script>{kc}</script><script>{js}</script></body></html>')
    with open(os.path.join(BASE, 'relatorio.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    with open(os.path.join(BASE, 'RESULTADOS.md'), 'w', encoding='utf-8') as f:
        f.write(TX.markdown(D))
    print('relatorio.html', round(len(html) / 1e6, 1), 'MB')


if __name__ == '__main__':
    monta()
