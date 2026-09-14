# -*- coding: utf-8 -*-
"""
O molde do relatorio: CSS, o kit de graficos em SVG e o grafico de candles.

Tudo aqui e texto. `relatorio.py` troca os {{marcadores}} pelos dados e
grava relatorio.html. O arquivo final e OFFLINE: nao busca fonte, script
nem folha de estilo em lugar nenhum (o klinecharts vai embutido).

Paleta -- validada com scripts/validate_palette.js da skill dataviz:
  niveis Ouro/Prata/Bronze  rampa ORDINAL de um tom so (azul), do mais
                            escuro (Ouro) ao mais claro (Bronze), porque
                            os tres sao um mesmo eixo ordenado, nao tres
                            identidades diferentes. O nome do nivel vai
                            sempre escrito junto -- a cor nunca carrega a
                            informacao sozinha.
  ganho / perda             par divergente azul <-> vermelho, com o zero
                            em cinza neutro.
"""

CSS = r"""
:root{
  color-scheme: light;
  --plano:#f9f9f7; --card:#fcfcfb; --card2:#f3f2ee;
  --tinta:#0b0b0b; --tinta2:#52514e; --mudo:#898781;
  --grade:#e1e0d9; --eixo:#c3c2b7; --borda:rgba(11,11,11,.10);
  --ouro:#184f95; --prata:#2a78d6; --bronze:#86b6ef;
  --ganho:#2a78d6; --perda:#e34948; --neutro:#d9d8d2;
  --bom:#0ca30c; --alerta:#fab219; --grave:#ec835a; --critico:#d03b3b;
  --sombra:0 1px 2px rgba(11,11,11,.05), 0 1px 8px rgba(11,11,11,.04);
}
@media (prefers-color-scheme: dark){
  :root:not([data-tema="claro"]){
    color-scheme: dark;
    --plano:#0d0d0d; --card:#1a1a19; --card2:#222221;
    --tinta:#fff; --tinta2:#c3c2b7; --mudo:#898781;
    --grade:#2c2c2a; --eixo:#383835; --borda:rgba(255,255,255,.10);
    --ouro:#cde2fb; --prata:#5598e7; --bronze:#184f95;
    --ganho:#3987e5; --perda:#e66767; --neutro:#383835;
    --sombra:0 1px 2px rgba(0,0,0,.4), 0 1px 8px rgba(0,0,0,.3);
  }
}
:root[data-tema="escuro"]{
  color-scheme: dark;
  --plano:#0d0d0d; --card:#1a1a19; --card2:#222221;
  --tinta:#fff; --tinta2:#c3c2b7; --mudo:#898781;
  --grade:#2c2c2a; --eixo:#383835; --borda:rgba(255,255,255,.10);
  --ouro:#cde2fb; --prata:#5598e7; --bronze:#184f95;
  --ganho:#3987e5; --perda:#e66767; --neutro:#383835;
  --sombra:0 1px 2px rgba(0,0,0,.4), 0 1px 8px rgba(0,0,0,.3);
}

*{box-sizing:border-box}
body{
  margin:0; background:var(--plano); color:var(--tinta);
  font:15px/1.65 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;
  font-variant-numeric:tabular-nums;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1140px; margin:0 auto; padding-block:0 72px; padding-left:20px; padding-right:20px}
h1,h2,h3{line-height:1.2; letter-spacing:-.02em; margin:0}
h1{font-size:clamp(28px,4.4vw,44px); font-weight:680}
h2{font-size:clamp(21px,2.7vw,28px); font-weight:640; margin-top:8px}
h3{font-size:16px; font-weight:640; margin-bottom:8px}
p{margin:0 0 14px}
a{color:var(--prata)}
small{font-size:12.5px}
code,.mono{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
  font-size:.92em}

/* ------------------------------------------------------------ topo */
header.capa{padding:56px 0 32px; border-bottom:1px solid var(--borda)}
.chapeu{font-size:12px; font-weight:640; letter-spacing:.10em; text-transform:uppercase;
  color:var(--mudo); margin-bottom:12px}
.sub{color:var(--tinta2); font-size:17px; max-width:70ch; margin-top:14px}
.selo{display:inline-flex; align-items:center; gap:6px; font-size:12px; font-weight:600;
  color:var(--tinta2); background:var(--card2); border:1px solid var(--borda);
  border-radius:999px; padding:3px 10px; margin:2px 6px 2px 0}

/* --------------------------------------------------------- secoes */
section{padding-top:52px; scroll-margin-top:64px}
.olho{color:var(--tinta2); max-width:74ch; margin:10px 0 26px}
.nota{font-size:13.5px; color:var(--mudo); max-width:78ch; margin-top:10px}

/* ---------------------------------------------------------- cards */
.card{background:var(--card); border:1px solid var(--borda); border-radius:12px;
  padding:20px; box-shadow:var(--sombra)}
.grade{display:grid; gap:16px}
.g2{grid-template-columns:repeat(2,minmax(0,1fr))}
.g3{grid-template-columns:repeat(3,minmax(0,1fr))}
.g4{grid-template-columns:repeat(4,minmax(0,1fr))}
@media (max-width:860px){ .g3,.g4{grid-template-columns:repeat(2,minmax(0,1fr))} }
@media (max-width:560px){ .g2,.g3,.g4{grid-template-columns:1fr} }

/* ------------------------------------------------------- estatisticas */
.tile{background:var(--card); border:1px solid var(--borda); border-radius:12px;
  padding:16px 18px; box-shadow:var(--sombra)}
.tile .rot{font-size:12px; font-weight:600; color:var(--mudo); letter-spacing:.02em}
.tile .num{font-size:clamp(24px,3.2vw,32px); font-weight:660; letter-spacing:-.03em;
  margin-top:4px; line-height:1.1}
.tile .pe{font-size:12.5px; color:var(--tinta2); margin-top:3px}
.mini .tile{padding:12px 13px}
.mini .tile .num{font-size:clamp(19px,2.1vw,23px)}
.mini .tile .pe{font-size:11.5px}
.pos{color:var(--ganho)} .neg{color:var(--perda)}

/* ---------------------------------------------------------- tabelas */
.rolo{overflow-x:auto; -webkit-overflow-scrolling:touch}
table{border-collapse:collapse; width:100%; font-size:13.5px}
th,td{padding:7px 10px; text-align:right; white-space:nowrap;
  border-bottom:1px solid var(--grade)}
th{font-size:11.5px; font-weight:640; color:var(--mudo); text-transform:uppercase;
  letter-spacing:.05em; border-bottom:1px solid var(--eixo); position:sticky; top:0;
  background:var(--card)}
td:first-child,th:first-child{text-align:left}
tbody tr:hover{background:var(--card2)}
tr.destaque td{background:color-mix(in srgb, var(--prata) 9%, transparent); font-weight:620}
.tag{display:inline-flex; align-items:center; gap:5px; font-size:11.5px; font-weight:640;
  padding:2px 8px; border-radius:999px; border:1px solid var(--borda)}
.pt{width:8px; height:8px; border-radius:50%; flex:none}

/* ----------------------------------------------------------- abas */
.abas{display:flex; gap:4px; flex-wrap:wrap; margin-bottom:14px}
.aba{font:inherit; font-size:13px; font-weight:600; color:var(--tinta2);
  background:var(--card2); border:1px solid var(--borda); border-radius:8px;
  padding:6px 13px; cursor:pointer}
.aba:hover{color:var(--tinta)}
.aba[aria-pressed="true"]{background:var(--prata); border-color:var(--prata);
  color:var(--card); }

/* --------------------------------------------------------- graficos */
figure{margin:0}
figcaption{font-size:12.5px; color:var(--mudo); margin-top:8px}
.viz{width:100%; display:block; overflow:visible}
.viz text{font-family:system-ui,-apple-system,"Segoe UI",sans-serif}
.eixo-tx{font-size:11px; fill:var(--mudo)}
.grade-l{stroke:var(--grade); stroke-width:1}
.base-l{stroke:var(--eixo); stroke-width:1}
.legenda{display:flex; flex-wrap:wrap; gap:14px; font-size:12.5px; color:var(--tinta2);
  margin:2px 0 10px}
.legenda span{display:inline-flex; align-items:center; gap:6px}
.chave{width:12px; height:3px; border-radius:2px; flex:none}
.chave.q{height:10px; width:10px; border-radius:3px}

/* --------------------------------------------------------- tooltip */
.dica{position:fixed; z-index:40; pointer-events:none; opacity:0; transition:opacity .09s;
  background:var(--card); color:var(--tinta); border:1px solid var(--borda);
  border-radius:8px; padding:8px 11px; font-size:12.5px; box-shadow:var(--sombra);
  max-width:280px}
.dica b{font-weight:640}
.dica .l{color:var(--mudo)}

/* ------------------------------------------------------ diagrama padrao */
.diag{background:var(--card); border:1px solid var(--borda); border-radius:12px;
  padding:16px; box-shadow:var(--sombra)}
.diag h3{display:flex; align-items:center; gap:8px}

/* --------------------------------------------------------- galeria */
.galeria .ex{background:var(--card); border:1px solid var(--borda); border-radius:12px;
  padding:12px 12px 14px; box-shadow:var(--sombra)}
.ex-topo{display:flex; justify-content:space-between; align-items:baseline; gap:8px;
  font-size:12.5px; margin-bottom:6px}
.ex-data{color:var(--tinta2); font-weight:600}
.ex-res{font-weight:660}
.ex-viz{min-height:190px}
.galeria figcaption{font-size:12px; line-height:1.5; margin-top:6px}
@media (max-width:980px){ .galeria{grid-template-columns:repeat(2,minmax(0,1fr))} }
@media (max-width:620px){ .galeria{grid-template-columns:1fr} }

/* --------------------------------------------------------- kline */
#kwrap{background:var(--card); border:1px solid var(--borda); border-radius:12px;
  padding:14px; box-shadow:var(--sombra)}
#kchart{width:100%; height:480px}
@media (max-width:700px){ #kchart{height:360px} }
#kfiltros{margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid var(--grade)}
#kfiltros .linha-f{display:flex; align-items:center; gap:12px; flex-wrap:wrap;
  margin-bottom:6px}
#kfiltros .rot-f{font-size:11.5px; font-weight:640; color:var(--mudo);
  text-transform:uppercase; letter-spacing:.05em; min-width:66px}
#kfiltros .abas{margin-bottom:0}
#kfiltros .aba[disabled]{opacity:.38; cursor:not-allowed}
.kresumo{font-size:13px; color:var(--tinta2); margin:10px 0 0}
.knav{display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:12px}
.knav button{font:inherit; font-size:13px; font-weight:600; background:var(--card2);
  color:var(--tinta); border:1px solid var(--borda); border-radius:8px;
  padding:6px 12px; cursor:pointer}
.knav button:hover{border-color:var(--eixo)}
.knav select{font:inherit; font-size:13px; background:var(--card2); color:var(--tinta);
  border:1px solid var(--borda); border-radius:8px; padding:6px 10px; max-width:100%}
.kinfo{display:flex; gap:18px; flex-wrap:wrap; font-size:13px; color:var(--tinta2);
  margin-top:12px; padding-top:12px; border-top:1px solid var(--grade)}
.kinfo b{color:var(--tinta); font-weight:640}

/* ---------------------------------------------------------- rodape */
.bandeira{border-left:3px solid var(--alerta); background:var(--card2);
  border-radius:0 8px 8px 0; padding:14px 18px; margin:18px 0}
.bandeira h3{margin-bottom:6px}
ul.enx{margin:0 0 14px; padding-left:20px}
ul.enx li{margin-bottom:7px}
footer{margin-top:64px; padding-top:24px; border-top:1px solid var(--borda);
  color:var(--mudo); font-size:13px}

/* ------------------------------------------------------- navegacao */
nav.indice{position:sticky; top:0; z-index:30; background:color-mix(in srgb,var(--plano) 88%,transparent);
  backdrop-filter:blur(8px); border-bottom:1px solid var(--borda)}
nav.indice ul{display:flex; gap:2px; list-style:none; margin:0; padding:8px 0;
  overflow-x:auto; -webkit-overflow-scrolling:touch}
nav.indice a{display:block; font-size:12.5px; font-weight:600; color:var(--tinta2);
  text-decoration:none; padding:5px 10px; border-radius:7px; white-space:nowrap}
nav.indice a:hover{background:var(--card2); color:var(--tinta)}
.tema{position:fixed; right:16px; bottom:16px; z-index:50; width:40px; height:40px;
  border-radius:50%; border:1px solid var(--borda); background:var(--card);
  color:var(--tinta); cursor:pointer; box-shadow:var(--sombra); font-size:17px}
@media print{ nav.indice,.tema{display:none} }
"""


# ---------------------------------------------------------------- kit de graficos
JS_KIT = r"""
/* =====================================================================
   Kit de graficos em SVG puro. Nenhuma biblioteca: o arquivo precisa
   abrir offline, e as formas aqui sao poucas.

   Regras seguidas (skill dataviz):
     . marca fina, 2px na linha, ponta arredondada de 4px na barra
     . grade e eixo recuados, texto em tinta de texto e nunca na cor da serie
     . camada de hover em tudo o que tem marca
     . legenda sempre que ha 2 ou mais series, com rotulo escrito
   ===================================================================== */
const NS='http://www.w3.org/2000/svg';
const dica=document.createElement('div'); dica.className='dica'; document.body.appendChild(dica);

function el(t,a,pai){const e=document.createElementNS(NS,t);
  for(const k in a) e.setAttribute(k,a[k]); if(pai) pai.appendChild(e); return e;}
function cor(nome){return getComputedStyle(document.documentElement).getPropertyValue('--'+nome).trim();}
function fmt(v,c){ if(v===null||v===undefined||Number.isNaN(v)) return '-';
  return v.toLocaleString('pt-BR',{minimumFractionDigits:c===undefined?0:c,
                                  maximumFractionDigits:c===undefined?0:c}); }
function sinal(v,c){return (v>0?'+':'')+fmt(v,c);}
/* O rotulo de categoria fica a esquerda, num espaco que encolhe no celular.
   Texto em SVG nao quebra linha: quando nao cabe, corta. */
function corta(t,larg){
  const cabe=Math.floor(larg/5.6);      /* ~5,6 px por caractere a 11px */
  return t.length<=cabe?t:t.slice(0,Math.max(3,cabe-1))+'…';
}
/* margem esquerda dos graficos de categoria: 190px no desktop, mas nunca
   mais que 42% da largura -- senao no celular sobra sarjeta e nao grafico */
function margemRot(W,pedida){
  return Math.max(70,Math.min(pedida===undefined?190:pedida,W*0.42));
}

function mostra(ev,html){
  dica.innerHTML=html; dica.style.opacity='1';
  const r=dica.getBoundingClientRect();
  let x=ev.clientX+14, y=ev.clientY-r.height-12;
  if(x+r.width>innerWidth-8) x=ev.clientX-r.width-14;
  if(y<8) y=ev.clientY+18;
  dica.style.left=x+'px'; dica.style.top=y+'px';
}
function some(){dica.style.opacity='0';}

/* escala linear */
function esc(d0,d1,r0,r1){const k=(d1===d0)?0:(r1-r0)/(d1-d0);
  return v=>r0+(v-d0)*k;}

/* passos de eixo agradaveis */
function passos(min,max,n){
  if(min===max){min-=1;max+=1;}
  const bruto=(max-min)/n, m=Math.pow(10,Math.floor(Math.log10(bruto)));
  const cands=[1,2,2.5,5,10].map(x=>x*m);
  const p=cands.find(x=>x>=bruto)||cands[cands.length-1];
  const a=Math.floor(min/p)*p, b=Math.ceil(max/p)*p, out=[];
  for(let v=a; v<=b+p/2; v+=p) out.push(Math.abs(v)<p/1e6?0:v);
  return out;
}

/* ---------------------------------------------------- grafico de linhas */
function linhas(alvo,series,op){
  op=op||{}; const box=document.querySelector(alvo); if(!box) return;
  box.innerHTML='';
  const W=box.clientWidth||800, H=op.alt||300;
  const L=Math.min(op.esq===undefined?54:op.esq,W*0.16), R=14, T=12,
        B=op.base===undefined?28:op.base;
  const svg=el('svg',{class:'viz',viewBox:`0 0 ${W} ${H}`,width:W,height:H},box);
  const ativos=series.filter(s=>s.dados.length);
  if(!ativos.length) return;
  const nx=Math.max(...ativos.map(s=>s.dados.length));
  let y0=Math.min(0,...ativos.map(s=>Math.min(...s.dados)));
  let y1=Math.max(0,...ativos.map(s=>Math.max(...s.dados)));
  const ts=passos(y0,y1,4); y0=ts[0]; y1=ts[ts.length-1];
  const Y=esc(y0,y1,H-B,T);
  /* Se a serie traz `xs` (posicao no tempo, de 0 a 1), o eixo e o TEMPO --
     e e o unico jeito de comparar curvas com contagens de trade diferentes.
     Sem `xs`, cai no numero do trade. */
  const porTempo=ativos.every(s=>s.xs);
  const Xt=esc(0,1,L,W-R), Xn=esc(0,Math.max(1,nx-1),L,W-R);
  const px=(s,i)=>porTempo?Xt(s.xs[i]):Xn(i);

  ts.forEach(v=>{ el('line',{class:'grade-l',x1:L,x2:W-R,y1:Y(v),y2:Y(v)},svg);
    el('text',{class:'eixo-tx',x:L-8,y:Y(v)+4,'text-anchor':'end'},svg).textContent=fmt(v);});
  el('line',{class:'base-l',x1:L,x2:W-R,y1:Y(0),y2:Y(0)},svg);

  ativos.forEach(s=>{
    const d=s.dados.map((v,i)=>(i?'L':'M')+px(s,i).toFixed(1)+' '+Y(v).toFixed(1)).join(' ');
    if(s.area){
      const f=s.dados.length-1;
      el('path',{d:d+` L ${px(s,f)} ${Y(0)} L ${px(s,0)} ${Y(0)} Z`,
        fill:cor(s.cor),'fill-opacity':.10,stroke:'none'},svg);
    }
    el('path',{d:d,fill:'none',stroke:cor(s.cor),'stroke-width':2,
      'stroke-linejoin':'round','stroke-linecap':'round'},svg);
  });

  /* Rotulo direto na ponta de cada serie -- ate 4, como manda a skill. As
     pontas costumam cair na mesma altura; os rotulos sao afastados um do
     outro antes de desenhar, senao um cobre o outro. */
  if(ativos.length<=4 && op.rotulaPonta!==false){
    const alvo=ativos.map((s,k)=>({k,s,y:Y(s.dados[s.dados.length-1])}))
                     .sort((a,b)=>a.y-b.y);
    for(let i=1;i<alvo.length;i++)
      if(alvo[i].y-alvo[i-1].y<13) alvo[i].y=alvo[i-1].y+13;
    const excesso=alvo.length?alvo[alvo.length-1].y-(H-B):0;
    if(excesso>0) alvo.forEach(a=>a.y-=excesso);
    alvo.forEach(a=>{
      el('text',{class:'eixo-tx',x:W-R-2,y:a.y+4,'text-anchor':'end',
        fill:cor(a.s.cor),'font-weight':'640'},svg).textContent=a.s.nome;
    });
  }

  el('text',{class:'eixo-tx',x:L,y:H-8},svg)
    .textContent=op.x0||(porTempo?(ativos[0].dt?ativos[0].dt[0]:'') : '1');
  el('text',{class:'eixo-tx',x:W-R,y:H-8,'text-anchor':'end'},svg)
    .textContent=op.x1||(porTempo
      ? (ativos[0].dt?ativos[0].dt[ativos[0].dt.length-1]:'') : ('trade '+nx));

  /* cruz + tooltip */
  const cx=el('line',{class:'base-l',y1:T,y2:H-B,opacity:0},svg);
  const pts=ativos.map(s=>el('circle',{r:4,fill:cor(s.cor),stroke:cor('card'),
    'stroke-width':2,opacity:0},svg));
  el('rect',{x:L,y:T,width:W-R-L,height:H-B-T,fill:'transparent'},svg)
    .addEventListener('mousemove',ev=>{
      const bb=svg.getBoundingClientRect();
      const mx=(ev.clientX-bb.left)*(W/bb.width);
      cx.setAttribute('x1',mx); cx.setAttribute('x2',mx); cx.setAttribute('opacity',1);
      /* no eixo de tempo cada serie tem o SEU trade mais proximo do cursor */
      let rot='', h='';
      ativos.forEach((s,k)=>{
        let i;
        if(porTempo){
          const alvo=(mx-L)/(W-R-L);
          i=0; let melhor=Infinity;
          for(let j=0;j<s.xs.length;j++){
            const d=Math.abs(s.xs[j]-alvo);
            if(d<melhor){melhor=d; i=j;}
          }
          if(!rot&&s.dt) rot=s.dt[i];
        } else {
          i=Math.max(0,Math.min(s.dados.length-1,
            Math.round((mx-L)/((W-R-L)/Math.max(1,nx-1)))));
          if(!rot) rot='trade '+(i+1);
        }
        pts[k].setAttribute('cx',px(s,i)); pts[k].setAttribute('cy',Y(s.dados[i]));
        pts[k].setAttribute('opacity',1);
        h+=`<br><span class="l">${s.nome}</span> ${sinal(s.dados[i])} ${op.un||'pts'}`+
           (porTempo?` <span class="l">(${i+1})</span>`:'');
      });
      mostra(ev,`<b>${rot}</b>`+h);
    });
  svg.addEventListener('mouseleave',()=>{some(); cx.setAttribute('opacity',0);
    pts.forEach(p=>p.setAttribute('opacity',0));});
}

/* ------------------------------------------- barras (uma serie, horizontal) */
function barrasH(alvo,itens,op){
  op=op||{}; const box=document.querySelector(alvo); if(!box) return;
  box.innerHTML='';
  const W=box.clientWidth||800;
  const L=margemRot(W,op.esq), R=54, T=6, B=24, h=op.altBarra||26;
  const H=T+B+itens.length*h;
  const svg=el('svg',{class:'viz',viewBox:`0 0 ${W} ${H}`,width:W,height:H},box);
  let v0=Math.min(0,...itens.map(d=>d.v)), v1=Math.max(0,...itens.map(d=>d.v));
  const ts=passos(v0,v1,4); v0=ts[0]; v1=ts[ts.length-1];
  const X=esc(v0,v1,L,W-R);
  ts.forEach(v=>{ el('line',{class:'grade-l',x1:X(v),x2:X(v),y1:T,y2:H-B},svg);
    el('text',{class:'eixo-tx',x:X(v),y:H-8,'text-anchor':'middle'},svg).textContent=fmt(v);});
  el('line',{class:'base-l',x1:X(0),x2:X(0),y1:T,y2:H-B},svg);

  itens.forEach((d,i)=>{
    const y=T+i*h+3, ah=h-8;
    const a=Math.min(X(0),X(d.v)), b=Math.max(X(0),X(d.v));
    const c=cor(d.cor||(d.v>=0?'ganho':'perda'));
    el('rect',{x:a,y:y,width:Math.max(1.5,b-a),height:ah,rx:4,fill:c,'fill-opacity':d.fraco?.45:1},svg);
    el('text',{class:'eixo-tx',x:L-10,y:y+ah/2+4,'text-anchor':'end',
      fill:cor('tinta2')},svg).textContent=corta(d.nome,L-14);
    el('text',{class:'eixo-tx',x:(d.v>=0?b+6:a-6),y:y+ah/2+4,
      'text-anchor':d.v>=0?'start':'end',fill:cor('tinta2'),'font-weight':'620'},svg)
      .textContent=sinal(d.v,op.casas===undefined?1:op.casas);
    el('rect',{x:0,y:T+i*h,width:W,height:h,fill:'transparent'},svg)
      .addEventListener('mousemove',ev=>mostra(ev,
        `<b>${d.nome}</b><br><span class="l">${op.rotV||'valor'}</span> `+
        `${sinal(d.v,op.casas===undefined?1:op.casas)} ${op.un||'pts'}`+
        (d.extra?'<br>'+d.extra:'')));
  });
  svg.addEventListener('mouseleave',some);
}

/* ------------------------------------------ colunas (histograma / diario) */
function colunas(alvo,itens,op){
  op=op||{}; const box=document.querySelector(alvo); if(!box) return;
  box.innerHTML='';
  const W=box.clientWidth||800, H=op.alt||240;
  const L=Math.min(op.esq===undefined?48:op.esq,W*0.16), R=10, T=10, B=op.base||26;
  const svg=el('svg',{class:'viz',viewBox:`0 0 ${W} ${H}`,width:W,height:H},box);
  let v0=Math.min(0,...itens.map(d=>d.v)), v1=Math.max(0,...itens.map(d=>d.v));
  const ts=passos(v0,v1,4); v0=ts[0]; v1=ts[ts.length-1];
  const Y=esc(v0,v1,H-B,T), pas=(W-R-L)/itens.length;
  /* com poucas faixas a coluna viraria um bloco de 200px: fica limitada e
     centrada na sua fatia */
  const larg=Math.max(1,Math.min(pas-2,op.maxLarg||72)), folga=(pas-larg)/2;
  ts.forEach(v=>{ el('line',{class:'grade-l',x1:L,x2:W-R,y1:Y(v),y2:Y(v)},svg);
    el('text',{class:'eixo-tx',x:L-8,y:Y(v)+4,'text-anchor':'end'},svg).textContent=fmt(v);});
  el('line',{class:'base-l',x1:L,x2:W-R,y1:Y(0),y2:Y(0)},svg);

  itens.forEach((d,i)=>{
    const x=L+i*pas+folga, a=Math.min(Y(0),Y(d.v)), b=Math.max(Y(0),Y(d.v));
    el('rect',{x:x,y:a,width:larg,height:Math.max(1.5,b-a),rx:Math.min(4,larg/2),
      fill:cor(d.cor||(d.v>=0?'ganho':'perda')),'fill-opacity':d.fraco?.45:1},svg);
    el('rect',{x:L+i*pas,y:T,width:pas,height:H-B-T,fill:'transparent'},svg)
      .addEventListener('mousemove',ev=>mostra(ev,
        `<b>${d.nome}</b><br><span class="l">${op.rotV||'valor'}</span> `+
        `${sinal(d.v,op.casas===undefined?0:op.casas)} ${op.un||'pts'}`+
        (d.extra?'<br>'+d.extra:'')));
    if(op.rotula && itens.length<=14)
      el('text',{class:'eixo-tx',x:x+larg/2,y:H-8,'text-anchor':'middle'},svg)
        .textContent=d.nome;
  });
  if(op.x0) el('text',{class:'eixo-tx',x:L,y:H-8},svg).textContent=op.x0;
  if(op.x1) el('text',{class:'eixo-tx',x:W-R,y:H-8,'text-anchor':'end'},svg).textContent=op.x1;
  svg.addEventListener('mouseleave',some);
}

/* --------------------------------------------------------- mapa de calor */
function calor(alvo,m,op){
  op=op||{}; const box=document.querySelector(alvo); if(!box) return;
  box.innerHTML='';
  const W=box.clientWidth||800;
  const L=Math.max(46,Math.min(op.esq||68,W*0.22)), R=10, T=30, B=26, cel=op.cel||30;
  const nc=m.cols.length, nl=m.lins.length;
  const lc=Math.min(cel*2.2,(W-L-R)/nc), H=T+B+nl*cel;
  const svg=el('svg',{class:'viz',viewBox:`0 0 ${W} ${H}`,width:W,height:H},box);
  const vs=m.cel.flat().map(c=>c.v);
  const lo=Math.min(...vs), hi=Math.max(...vs);
  m.cols.forEach((c,j)=>el('text',{class:'eixo-tx',x:L+j*lc+lc/2,y:T-10,
    'text-anchor':'middle'},svg).textContent=c);
  m.lins.forEach((r,i)=>el('text',{class:'eixo-tx',x:L-8,y:T+i*cel+cel/2+4,
    'text-anchor':'end'},svg).textContent=corta(r,L-10));
  m.cel.forEach((linha,i)=>linha.forEach((d,j)=>{
    const t=(d.v-lo)/((hi-lo)||1);
    const g=el('g',{},svg);
    /* rampa sequencial de UM tom, do claro ao escuro. O teto de opacidade e
       0,55 de proposito: acima disso o numero dentro da celula deixa de ter
       contraste, e o numero e o que se le aqui -- a cor so ordena. */
    el('rect',{x:L+j*lc+1,y:T+i*cel+1,width:lc-2,height:cel-2,rx:4,
      fill:cor('prata'),'fill-opacity':(0.08+0.47*t).toFixed(3)},g);
    if(d.melhor) el('rect',{x:L+j*lc+1,y:T+i*cel+1,width:lc-2,height:cel-2,rx:4,
      fill:'none',stroke:cor('tinta'),'stroke-width':1.5},g);
    el('text',{class:'eixo-tx',x:L+j*lc+lc/2,y:T+i*cel+cel/2+4,'text-anchor':'middle',
      fill:cor('tinta'),'font-weight':d.melhor?'700':'500'},g)
      .textContent=fmt(d.v,op.casas===undefined?1:op.casas);
    g.addEventListener('mousemove',ev=>mostra(ev,d.dica));
  }));
  if(op.rotX) el('text',{class:'eixo-tx',x:L+(nc*lc)/2,y:H-8,'text-anchor':'middle'},svg)
    .textContent=op.rotX;
  svg.addEventListener('mouseleave',some);
}

/* ------------------------------------------- miniatura de um padrao
   Um candle de PI tem corpo fixo de 100 pontos, entao numa miniatura o
   que da para ler e a ESCADA dos corpos e o tamanho dos pavios -- que e
   justamente o que distingue Ouro de Prata. Por isso a miniatura desenha
   o candle inteiro e nao uma linha.

   Marca: a faixa clara e o par retracao + continuacao; a seta e a
   entrada; as linhas horizontais sao stop, parcial e alvo. */
function miniPadrao(alvo, ex, op){
  op=op||{}; const box=(typeof alvo==='string')?document.querySelector(alvo):alvo;
  if(!box) return;
  box.innerHTML='';
  const C=D.candles, P=D.parametros;
  const de=ex.de, ate=Math.min(C.dt.length-1,ex.ate), nb=ate-de+1;
  const W=box.clientWidth||320, H=op.alt||190;
  const L=4, R=44, T=8, B=16;
  const svg=el('svg',{class:'viz',viewBox:`0 0 ${W} ${H}`,width:W,height:H,
    role:'img','aria-label':op.rotulo||'exemplo do padrao'},box);

  const lado=ex.lado, ent=ex.preco_ent;
  const pStop=ent-lado*P.stop, pAlvo=ent+lado*P.alvo, pParc=ent+lado*P.parcial_em;
  let lo=Infinity, hi=-Infinity;
  for(let i=de;i<=ate;i++){
    lo=Math.min(lo,C.l[i],C.hma[i]??lo,C.ema[i]??lo);
    hi=Math.max(hi,C.h[i],C.hma[i]??hi,C.ema[i]??hi);
  }
  /* O stop entra sempre no enquadramento: ele esta perto e da a escala.
     O alvo, a 3x o stop, esprema as velas ate o padrao sumir -- por isso
     ele entra so ate 2/3 de faixa extra, e quando nao cabe a linha e
     desenhada na borda com o rotulo marcado. */
  lo=Math.min(lo,pStop); hi=Math.max(hi,pStop);
  const faixa=hi-lo;
  const cortado=(lado>0)?(pAlvo>hi+faixa*0.66):(pAlvo<lo-faixa*0.66);
  if(lado>0) hi=Math.min(pAlvo,hi+faixa*0.66); else lo=Math.max(pAlvo,lo-faixa*0.66);
  const folga=(hi-lo)*0.06; lo-=folga; hi+=folga;
  const pas=(W-L-R)/nb, larg=Math.max(2,Math.min(11,pas*0.62));
  const X=i=>L+(i-de+0.5)*pas, Y=esc(lo,hi,H-B,T);

  /* niveis da operacao, por tras de tudo */
  const yAlvo=cortado?(lado>0?T+2:H-B-2):Y(pAlvo);
  [[yAlvo,'ganho',cortado?(lado>0?'alvo ↑':'alvo ↓'):'alvo',cortado],
   [Y(pParc),'ganho','parcial',false],[Y(ent),'tinta','entrada',false],
   [Y(pStop),'perda','stop',false]].forEach(([y,c,rot,tracejar])=>{
    if(y<T-1||y>H-B+1) return;
    el('line',{x1:X(ex.i_sin),x2:W-R,y1:y,y2:y,stroke:cor(c),'stroke-width':1,
      'stroke-dasharray':(rot==='parcial'||tracejar)?'3 3':'none',opacity:.55},svg);
    el('text',{class:'eixo-tx',x:W-R+4,y:y+3.5,fill:cor(c)},svg).textContent=rot;
  });

  /* a faixa do par retracao + continuacao */
  el('rect',{x:X(ex.i_ret)-larg/2-2,y:T,
    width:(ex.i_sin-ex.i_ret)*pas+larg+4,height:H-B-T,rx:3,
    fill:cor('prata'),'fill-opacity':.13},svg);

  /* Hull 50 e EMA 21 */
  [['hma','alerta'],['ema','prata']].forEach(([k,c])=>{
    let d='';
    for(let i=de;i<=ate;i++){
      const v=C[k][i]; if(v===null||v===undefined) continue;
      d+=(d?'L':'M')+X(i).toFixed(1)+' '+Y(v).toFixed(1)+' ';
    }
    if(d) el('path',{d:d,fill:'none',stroke:cor(c),'stroke-width':1.6,
      'stroke-linejoin':'round','stroke-linecap':'round',opacity:.95},svg);
  });

  /* os candles */
  for(let i=de;i<=ate;i++){
    const alta=C.c[i]>=C.o[i], c=cor(alta?'ganho':'perda');
    const x=X(i), topo=Math.min(Y(C.o[i]),Y(C.c[i]));
    const alt=Math.max(1.5,Math.abs(Y(C.o[i])-Y(C.c[i])));
    const dentro=(i>=ex.i_ret&&i<=ex.i_sin);
    el('line',{x1:x,x2:x,y1:Y(C.h[i]),y2:Y(C.l[i]),stroke:c,'stroke-width':1.2,
      opacity:dentro?1:.5},svg);
    el('rect',{x:x-larg/2,y:topo,width:larg,height:alt,rx:1.5,fill:c,
      'fill-opacity':dentro?1:.5},svg);
  }

  /* a seta da entrada e a marca da saida */
  const xe=X(ex.i_ent), ye=Y(ent), d=lado>0?1:-1;
  el('polygon',{points:`${xe},${ye+d*5} ${xe-4.5},${ye+d*13} ${xe+4.5},${ye+d*13}`,
    fill:cor('tinta')},svg);
  el('circle',{cx:X(ex.i_sai),cy:Y(ex.pts>=0?(lado>0?C.h[ex.i_sai]:C.l[ex.i_sai])
    :(lado>0?C.l[ex.i_sai]:C.h[ex.i_sai])),r:3.5,fill:'none',
    stroke:cor(ex.pts>0?'ganho':(ex.pts<0?'perda':'mudo')),'stroke-width':1.6},svg);

  /* hover: a leitura completa do exemplo */
  el('rect',{x:0,y:0,width:W,height:H,fill:'transparent'},svg)
    .addEventListener('mousemove',ev=>mostra(ev,
      `<b>${ex.data} &middot; ${lado>0?'compra':'venda'}</b><br>`+
      `<span class="l">retracao</span> ${ex.n_ret} candle${ex.n_ret>1?'s':''}<br>`+
      `<span class="l">pavio do candle de continuacao</span> ${fmt(ex.pav_tot)} pts<br>`+
      `<span class="l">entrada</span> ${fmt(ex.preco_ent)}<br>`+
      `<span class="l">saida</span> ${ex.rot_saida}, ${sinal(ex.pts)} pts`));
  svg.addEventListener('mouseleave',some);
}

/* ------------------------------------------ barras agrupadas (por terco) */
function grupos(alvo,itens,nomes,op){
  op=op||{}; const box=document.querySelector(alvo); if(!box) return;
  box.innerHTML='';
  const W=box.clientWidth||800;
  const L=margemRot(W,op.esq), R=48, T=6, B=24, h=op.altBarra||34;
  const H=T+B+itens.length*h;
  const svg=el('svg',{class:'viz',viewBox:`0 0 ${W} ${H}`,width:W,height:H},box);
  const todos=itens.flatMap(d=>d.v);
  let v0=Math.min(0,...todos), v1=Math.max(0,...todos);
  const ts=passos(v0,v1,4); v0=ts[0]; v1=ts[ts.length-1];
  const X=esc(v0,v1,L,W-R);
  ts.forEach(v=>{ el('line',{class:'grade-l',x1:X(v),x2:X(v),y1:T,y2:H-B},svg);
    el('text',{class:'eixo-tx',x:X(v),y:H-8,'text-anchor':'middle'},svg).textContent=fmt(v);});
  el('line',{class:'base-l',x1:X(0),x2:X(0),y1:T,y2:H-B},svg);
  const nb=nomes.length, hb=(h-8)/nb;
  itens.forEach((d,i)=>{
    el('text',{class:'eixo-tx',x:L-10,y:T+i*h+h/2+4,'text-anchor':'end',
      fill:cor('tinta2')},svg).textContent=corta(d.nome,L-14);
    d.v.forEach((v,k)=>{
      if(v===null) return;
      const y=T+i*h+4+k*hb, a=Math.min(X(0),X(v)), b=Math.max(X(0),X(v));
      el('rect',{x:a,y:y,width:Math.max(1.5,b-a),height:Math.max(2,hb-2),rx:2,
        fill:cor(op.cores[k])},svg);
    });
    el('rect',{x:0,y:T+i*h,width:W,height:h,fill:'transparent'},svg)
      .addEventListener('mousemove',ev=>mostra(ev,`<b>${d.nome}</b><br>`+
        nomes.map((n,k)=>`<span class="l">${n}</span> ${d.v[k]===null?'-':sinal(d.v[k],1)} pts`+
          (d.n?` <span class="l">(n=${d.n[k]})</span>`:'')).join('<br>')));
  });
  svg.addEventListener('mouseleave',some);
}
"""


# ------------------------------------------------------------- esqueleto
HTML = r"""<!doctype html>
<html lang="pt-BR" data-tema="auto">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{titulo}}</title>
<style>__CSS__</style>
</head>
<body>
<nav class="indice"><div class="wrap"><ul>{{menu}}</ul></div></nav>
<div class="wrap">
{{corpo}}
</div>
<button class="tema" id="btema" title="Alternar tema" aria-label="Alternar tema">&#9681;</button>
<script>__KLINE__</script>
<script>const D=__DADOS__;</script>
<script>__KIT__</script>
<script>__PAG__</script>
<script>__KAPP__</script>
</body>
</html>
"""


# ------------------------------------------------- a pagina: desenho e abas
JS_PAG = r"""
/* ------------------------------------------------------------ tema */
const bt=document.getElementById('btema');
function temaAtual(){const t=document.documentElement.dataset.tema;
  if(t==='claro'||t==='escuro') return t;
  return matchMedia('(prefers-color-scheme: dark)').matches?'escuro':'claro';}
bt.addEventListener('click',()=>{
  document.documentElement.dataset.tema = temaAtual()==='escuro'?'claro':'escuro';
  desenha(); if(window.pintaKline) window.pintaKline();
});

/* ------------------------------------------------------------ abas */
document.querySelectorAll('[data-abas]').forEach(g=>{
  g.addEventListener('click',ev=>{
    const b=ev.target.closest('.aba'); if(!b) return;
    g.querySelectorAll('.aba').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));
    const alvo=g.dataset.abas;
    document.querySelectorAll('[data-painel="'+alvo+'"]').forEach(p=>{
      p.hidden = p.dataset.chave!==b.dataset.chave;});
    desenha();
  });
});

/* ------------------------------------------------------- os desenhos */
const CORNIV={ouro:'ouro',prata:'prata',bronze:'bronze'};

function desenha(){
  /* 1. curva de patrimonio dos tres niveis */
  const vis=['ouro','prata','bronze'].map(n=>{
    const v=D.variantes['fecha|parcial|'+n];
    return v?{nome:D.rotulo[n],cor:CORNIV[n],dados:v.stats.equity,
              xs:v.stats.eq_t,dt:v.stats.eq_d,area:n==='ouro'}:null;
  }).filter(Boolean);
  linhas('#eq_niveis',vis,{alt:320,un:'pts'});

  /* 2. curva por modo de entrada, no nivel Prata (o unico que os tres tem) */
  const modos=[['fecha','Fechamento','ouro'],['meio_lim','Limitada no meio','prata'],
               ['antecipa','Stop no meio','bronze']];
  linhas('#eq_modos',modos.map(function(m){
    const v=D.variantes[m[0]+'|parcial|prata'];
    return v?{nome:m[1],cor:m[2],dados:v.stats.equity,
              xs:v.stats.eq_t,dt:v.stats.eq_d}:null;
  }).filter(Boolean),{alt:300,un:'pts'});

  /* 3. com e sem parcial, nivel Ouro */
  const gp=D.variantes['fecha|parcial|ouro'].stats, gs=D.variantes['fecha|puro|ouro'].stats;
  linhas('#eq_gestao',[
    {nome:'Com parcial',cor:'ouro',dados:gp.equity,xs:gp.eq_t,dt:gp.eq_d,area:true},
    {nome:'Sem parcial',cor:'prata',dados:gs.equity,xs:gs.eq_t,dt:gs.eq_d}
  ],{alt:300,un:'pts'});

  /* 4. distribuicao do resultado por trade */
  const esc=D.variantes[D.escolhida];
  colunas('#hist_pnl',histo(esc.trades.map(t=>t.pts)),{alt:250,rotula:true,un:'trades',
    rotV:'trades',casas:0,x0:'perde',x1:'ganha'});

  /* 5. MEP e MEN */
  colunas('#hist_mep',histo(esc.trades.map(t=>t.mfe),'ganho'),
    {alt:230,rotula:true,un:'trades',rotV:'trades',casas:0});
  colunas('#hist_men',histo(esc.trades.map(t=>t.mae),'perda'),
    {alt:230,rotula:true,un:'trades',rotV:'trades',casas:0});

  /* 6. duracao */
  colunas('#hist_dur',duracao(esc.trades),{alt:230,rotula:true,un:'trades',
    rotV:'trades',casas:0});
  colunas('#hist_barras',histoBarras(esc.trades),{alt:230,rotula:true,un:'trades',
    rotV:'trades',casas:0});

  /* 7. dia a dia */
  colunas('#diario',D.diario.map(d=>({nome:d.dia.slice(8)+'/'+d.dia.slice(5,7),v:d.pts,
    extra:'<span class="l">trades</span> '+d.n})),
    {alt:240,rotula:false,x0:D.diario[0].dia,x1:D.diario[D.diario.length-1].dia});

  /* 8. os filtros, um a um */
  for(const k in D.estudos){
    if(k==='cruz_exaustao') continue;
    const bl=D.estudos[k];
    if(document.querySelector('#f_'+k))
      grupos('#f_'+k,bl.map(r=>({nome:r.faixa,v:r.ev_terco,n:r.n_terco})),
        ['1o terco','2o terco','3o terco'],{cores:['ouro','prata','bronze'],altBarra:38});
    if(document.querySelector('#t_'+k))
      barrasH('#t_'+k,bl.map(r=>({nome:r.faixa,v:r.ev,
        extra:'<span class="l">sinais</span> '+r.n+' &middot; <span class="l">acerto</span> '+
              r.wr.toFixed(1)+'%'})),{altBarra:28});
  }

  /* 9. grade stop x alvo */
  ['puro','parcial'].forEach(g=>{
    const G=D.grade[g];
    if(!document.querySelector('#grade_'+g)) return;
    calor('#grade_'+g,{
      cols:D.grade.alvos.map(a=>a+' pts'),
      lins:D.grade.stops.map(s=>'stop '+s),
      cel:G.map(l=>l.map(c=>({v:c.ev,
        melhor:(c.stop===D.parametros.stop&&c.alvo===D.parametros.alvo),
        dica:'<b>stop '+c.stop+' &middot; alvo '+c.alvo+'</b><br>'+
             '<span class="l">EV</span> '+sinal(c.ev,1)+' pts<br>'+
             '<span class="l">acerto</span> '+c.wr.toFixed(1)+'%<br>'+
             '<span class="l">por ponto de risco</span> '+c.ev_risco.toFixed(2)+'<br>'+
             '<span class="l">total</span> '+sinal(c.pts)+' pts em '+c.n+' trades'})))
    },{rotX:'alvo',casas:1});
  });

  /* 10. periodos de media */
  barrasH('#medias',D.medias.map(m=>({nome:'EMA '+m.ema+' / Hull '+m.hull,v:m.ev_ouro,
    cor:m.padrao?'ouro':'prata', fraco:!m.padrao,
    extra:'<span class="l">sinais Ouro</span> '+m.n_ouro+' &middot; '+
          '<span class="l">total</span> '+sinal(m.pts_ouro)+' pts'+
          (m.padrao?'<br><b>a combinacao do CLAUDE.md</b>':'')})),
    {altBarra:26,esq:150});

  /* 11. custos */
  barrasH('#custos',D.custos.map(c=>({
    nome:c.custo+' pts (R$ '+(c.custo*D.parametros.val_ponto).toFixed(2)+')',
    v:c.ev, cor:c.ev>0?'ganho':'perda',
    extra:'<span class="l">total</span> '+sinal(c.total)+' pts &middot; '+
          '<span class="l">fator de lucro</span> '+c.fl.toFixed(2)})),{altBarra:26,esq:170});

  /* 12. galeria de exemplos */
  for(const niv in D.galeria)
    D.galeria[niv].forEach((ex,k)=>miniPadrao('#gal_'+niv+'_'+k,ex));

  /* 13. diagonal risco : retorno -- a cor segue o resultado POR RISCO,
     que e o unico numero comparavel entre stops diferentes */
  if(document.querySelector('#rr_calor')){
    calor('#rr_calor',{
      cols:D.rr[0].map(c=>'1:'+c.razao),
      lins:D.rr.map(l=>'stop '+l[0].stop),
      cel:D.rr.map(l=>l.map(c=>({v:c.ev_risco,melhor:c.padrao,
        dica:'<b>stop '+c.stop+' &middot; alvo '+c.alvo+' (1:'+c.razao+')</b><br>'+
          '<span class="l">por ponto de risco</span> '+fmt(c.ev_risco,2)+'<br>'+
          '<span class="l">por trade</span> '+sinal(c.ev,1)+' pts<br>'+
          '<span class="l">acerto</span> '+fmt(c.wr,1)+'%<br>'+
          '<span class="l">total</span> '+sinal(c.pts)+' pts em '+c.n+' sinais<br>'+
          '<span class="l">rebaixamento</span> '+fmt(c.dd)+' pts<br>'+
          '<span class="l">por terco</span> '+
          c.por_terco.map(t=>t.terco+' '+sinal(t.ev,0)).join(' &middot; ')})))
    },{rotX:'alvo, em multiplos do stop',casas:2,cel:34});
  }

  /* 14. monte carlo */
  const mc=D.monte_carlo[D.escolhida];
  if(mc&&document.querySelector('#mc')){
    const b=mc.hist_total_bins;
    colunas('#mc',mc.hist_total.map((n,i)=>({nome:fmt(b[i])+' a '+fmt(b[i+1]),v:n,
      cor:b[i]>=0?'ganho':'perda'})),
      {alt:230,un:'simulacoes',rotV:'simulacoes',casas:0,
       x0:fmt(b[0])+' pts',x1:fmt(b[b.length-1])+' pts'});
  }

  /* 15. fluxo: o achado real contra o que a MESMA busca acha em ruido */
  if(D.fluxo){
    const ordem=['ouro','prata','bronze'];
    const pen={}; D.fluxo.peneira.forEach(r=>pen[r.nivel]=r);
    /* Duas barras por nivel. Se a clara (ruido) passa a escura (real),
       o achado e a busca, nao o atributo. */
    grupos('#fx_ruido',
      ordem.map(k=>({nome:D.rotulo[k],
                     v:[pen[k].melhor.t, pen[k].ruido_mediana],
                     n:[pen[k].melhor.n, null]})),
      ['melhor filtro real','melhor em ruido'],
      {cores:['ouro','bronze'],altBarra:40});
    /* fora da amostra: corte escolhido em T1+T2, medido em T3 */
    grupos('#fx_fora',
      ordem.map(k=>({nome:D.rotulo[k],
                     v:[pen[k].fora.ev_t3_base, pen[k].fora.ev_t3],
                     n:[pen[k].fora.n_t3_base, pen[k].fora.n_t3]})),
      ['sem filtro','com o filtro'],
      {cores:['prata','critico'],altBarra:40});
  }
}

/* histograma com faixa de 50 pontos */
function histo(vals,corFixa){
  if(!vals.length) return [];
  const p=50;
  const lo=Math.floor(Math.min.apply(null,vals)/p)*p;
  const hi=Math.ceil(Math.max.apply(null,vals)/p)*p;
  const n=Math.max(1,Math.round((hi-lo)/p)), c=new Array(n).fill(0);
  vals.forEach(v=>{let i=Math.floor((v-lo)/p); if(i>=n)i=n-1; if(i<0)i=0; c[i]++;});
  return c.map((q,i)=>({nome:fmt(lo+i*p),v:q,
    cor:corFixa||((lo+i*p)>=0?'ganho':'perda'),
    extra:'<span class="l">faixa</span> '+fmt(lo+i*p)+' a '+fmt(lo+(i+1)*p)+' pts'}));
}
function duracao(tr){
  const cortes=[0,60,180,300,600,1200,2400,1e9];
  const rot=['ate 1 min','1 a 3','3 a 5','5 a 10','10 a 20','20 a 40','mais de 40'];
  const c=new Array(rot.length).fill(0);
  tr.forEach(t=>{for(let i=0;i<cortes.length-1;i++)
    if(t.dur_s>=cortes[i]&&t.dur_s<cortes[i+1]){c[i]++;break;}});
  return c.map((q,i)=>({nome:rot[i],v:q,cor:'prata'}));
}
function histoBarras(tr){
  const cortes=[1,3,6,10,20,40,1e9], rot=['1-2','3-5','6-9','10-19','20-39','40+'];
  const c=new Array(rot.length).fill(0);
  tr.forEach(t=>{for(let i=0;i<cortes.length-1;i++)
    if(t.barras>=cortes[i]&&t.barras<cortes[i+1]){c[i]++;break;}});
  return c.map((q,i)=>({nome:rot[i],v:q,cor:'prata'}));
}

addEventListener('resize',()=>{clearTimeout(window._rz);
  window._rz=setTimeout(()=>{desenha(); if(window.kchart) window.kchart.resize();},180);});
desenha();
"""


# ------------------------------------------------- o grafico trade a trade
JS_KLINE_APP = r"""
/* =====================================================================
   Grafico trade a trade, em cima do klinecharts 9.8.10 (embutido no
   proprio arquivo). Mostra o par retracao + continuacao, as tres linhas
   de contexto e os niveis da operacao: entrada, stop, parcial e alvo.
   ===================================================================== */
const SANS='system-ui,-apple-system,"Segoe UI",sans-serif';
function c_(n){return getComputedStyle(document.documentElement).getPropertyValue('--'+n).trim();}
function alfa(hex,a){
  const h=hex.replace('#','').trim();
  const n=h.length===3?h.split('').map(x=>x+x).join(''):h;
  const i=parseInt(n,16);
  return 'rgba('+((i>>16)&255)+','+((i>>8)&255)+','+(i&255)+','+a+')';
}

klinecharts.registerOverlay({
  name:'mm-nivel', totalStep:2, lock:true,
  needDefaultPointFigure:false, needDefaultXAxisFigure:false, needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates,bounding})=>{
    const e=overlay.extendData, y=coordinates[0].y;
    return [
      {type:'line',ignoreEvent:true,
       attrs:{coordinates:[{x:0,y:y},{x:bounding.width,y:y}]},
       styles:{color:e.cor,size:1,style:e.cheia?'solid':'dashed',dashedValue:[4,4]}},
      {type:'text',ignoreEvent:true,
       attrs:{x:4,y:y-3,text:e.rot,align:'left',baseline:'bottom'},
       styles:{color:e.cor,size:10,family:SANS,weight:'600',
               backgroundColor:alfa(c_('card'),.78),
               paddingLeft:4,paddingRight:4,paddingTop:1,paddingBottom:1,borderRadius:3}}
    ];
  }
});
klinecharts.registerOverlay({
  name:'mm-marca', totalStep:2, lock:true,
  needDefaultPointFigure:false, needDefaultXAxisFigure:false, needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates,bounding})=>{
    const e=overlay.extendData, x=coordinates[0].x;
    return [
      {type:'line',ignoreEvent:true,attrs:{coordinates:[{x:x,y:0},{x:x,y:bounding.height}]},
       styles:{color:e.cor,size:1,style:'dashed',dashedValue:[2,4]}},
      {type:'text',ignoreEvent:true,
       attrs:{x:x,y:bounding.height-4-(e.degrau||0)*19,text:e.rot,align:'center',
              baseline:'bottom'},
       styles:{color:c_('card'),size:10,family:SANS,weight:'600',backgroundColor:e.cor,
               paddingLeft:5,paddingRight:5,paddingTop:2,paddingBottom:2,borderRadius:3}}
    ];
  }
});
klinecharts.registerOverlay({
  name:'mm-zona', totalStep:3, lock:true,
  needDefaultPointFigure:false, needDefaultXAxisFigure:false, needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates,bounding})=>{
    if(coordinates.length<2) return [];
    const a=Math.min(coordinates[0].x,coordinates[1].x);
    const b=Math.max(coordinates[0].x,coordinates[1].x);
    return [{type:'rect',ignoreEvent:true,
      attrs:{x:a,y:0,width:Math.max(2,b-a),height:bounding.height},
      styles:{style:'fill',color:overlay.extendData.cor}}];
  }
});

/* as medias vem prontas da engine, penduradas em cada barra */
klinecharts.registerIndicator({
  name:'MM_CTX', shortName:'Hull 50 / EMA 21 / Keltner', series:'price', precision:0,
  figures:[{key:'hma',title:'Hull 50: ',type:'line'},
           {key:'ema',title:'EMA 21: ',type:'line'},
           {key:'ks', title:'Keltner sup: ',type:'line'},
           {key:'ki', title:'Keltner inf: ',type:'line'}],
  calc:dl=>dl.map(k=>({hma:k.hma,ema:k.ema,ks:k.ks,ki:k.ki}))
});

let kchart=null, kidx=0, KTR=[], KLST=[];

function lin(cor,tam,tracejada){
  return {color:cor,size:tam,smooth:false,
          style:tracejada?'dashed':'solid',dashedValue:[3,4]};
}
function estiloKline(){
  const g=c_('grade'), m=c_('mudo'), tx=c_('tinta'), card=c_('card');
  const alta=c_('ganho'), baixa=c_('perda');
  return {
    grid:{horizontal:{color:g},vertical:{color:g}},
    candle:{
      bar:{upColor:alta,downColor:baixa,noChangeColor:m,
           upBorderColor:alta,downBorderColor:baixa,noChangeBorderColor:m,
           upWickColor:alta,downWickColor:baixa,noChangeWickColor:m},
      priceMark:{last:{text:{color:card},upColor:alta,downColor:baixa,noChangeColor:m}},
      /* sem a mira em cima, o klinecharts mostraria a ULTIMA barra da base,
         que nao e a que esta na tela -- so aparece no hover */
      tooltip:{showRule:'follow_cross',
        text:{color:tx,family:SANS,size:11},
        rect:{color:alfa(card,.94),borderColor:c_('eixo')}}
    },
    /* o klinecharts NAO mescla o array de linhas com o padrao de fabrica:
       ele troca o array inteiro, e cada item precisa vir COMPLETO. Faltando
       uma chave (style, smooth, dashedValue) a linha simplesmente nao sai. */
    indicator:{
      lines:[lin(c_('alerta'),2,false),      /* Hull 50 */
             lin(c_('prata'),1.5,false),     /* EMA 21 */
             lin(m,1,true), lin(m,1,true)],  /* bandas do Keltner */
      tooltip:{showRule:'follow_cross',showName:true,showParams:false,
        text:{color:c_('tinta2'),family:SANS,size:11}}
    },
    xAxis:{axisLine:{color:c_('eixo')},tickLine:{color:c_('eixo')},
      tickText:{color:m,family:SANS,size:11}},
    yAxis:{axisLine:{color:c_('eixo')},tickLine:{color:c_('eixo')},
      tickText:{color:m,family:SANS,size:11}},
    crosshair:{horizontal:{line:{color:m},text:{backgroundColor:c_('tinta2')}},
               vertical:{line:{color:m},text:{backgroundColor:c_('tinta2')}}},
    separator:{color:c_('eixo')}
  };
}
function pintaKline(){
  if(!kchart) return;
  const st=estiloKline();
  kchart.setStyles(st);
  /* o klinecharts NAO mescla o array de linhas com o padrao: troca inteiro */
  kchart.overrideIndicator({name:'MM_CTX',styles:st.indicator},'candle_pane');
  mostraTrade(kidx);
}
window.pintaKline=pintaKline;

/* O eixo e sintetico: uma barra por minuto. O grafico de PI nao tem passo
   de tempo -- duas barras podem fechar no mesmo instante, e o klinecharts
   exige carimbo crescente. O horario REAL vem em D.candles.dt e e o que o
   formatador devolve para o eixo, para a mira e para a dica. */
const T0=Date.UTC(2000,0,1), TB=60000;
function iBarra(ts){return Math.round((ts-T0)/TB);}

function iniciaKline(){
  const C=D.candles, n=C.dt.length;
  KLST=new Array(n);
  for(let i=0;i<n;i++) KLST[i]={timestamp:T0+i*TB,open:C.o[i],high:C.h[i],low:C.l[i],
    close:C.c[i],volume:0,hma:C.hma[i],ema:C.ema[i],ks:C.kc_sup[i],ki:C.kc_inf[i]};
  kchart=klinecharts.init('kchart',{
    styles:estiloKline(),
    /* tipo 2 e o eixo do tempo (medido no proprio klinecharts 9.8.10);
       la cabe so a hora, no resto cabe a data inteira */
    customApi:{formatDate:(fmtr,ts,formato,tipo)=>{
      const i=iBarra(ts);
      const s=(i>=0&&i<n)?C.dt[i]:'';
      return tipo===2?s.slice(6):s;
    }}
  });
  window.kchart=kchart;
  kchart.setPriceVolumePrecision(0,0);
  kchart.createIndicator({name:'MM_CTX',styles:estiloKline().indicator},true,{id:'candle_pane'});
  kchart.applyNewData(KLST,false,()=>mostraTrade(0));
}

function mostraTrade(i){
  if(!kchart||!KTR.length) return;
  kidx=Math.max(0,Math.min(KTR.length-1,i));
  const t=KTR[kidx];
  kchart.removeOverlay();

  const lado=t.lado>0?1:-1, ent=t.preco_ent, P=D.parametros;
  /* os niveis desenhados sao os da GESTAO escolhida nos botoes: o 1:2 nao
     tem parcial e tem o alvo na metade do caminho do 1:3 */
  const G=(D.gestoes||{})[kGestao]||{stop:P.stop,alvo:P.alvo,parcial:true,
                                     parcial_em:P.parcial_em};
  const niveis=[
    {v:ent, rot:'entrada '+fmt(ent), cor:c_('tinta'), cheia:true},
    {v:ent-lado*G.stop, rot:'stop '+fmt(ent-lado*G.stop), cor:c_('perda'), cheia:true},
    {v:ent+lado*G.alvo, rot:'alvo +'+fmt(G.alvo), cor:c_('ganho'), cheia:true}
  ];
  if(G.parcial) niveis.splice(2,0,{v:ent+lado*G.parcial_em,
    rot:'parcial +'+fmt(G.parcial_em), cor:c_('ganho'), cheia:false});
  niveis.forEach(L=>kchart.createOverlay({name:'mm-nivel',lock:true,
    points:[{timestamp:KLST[t.i_ent].timestamp,value:L.v}],extendData:L}));

  kchart.createOverlay({name:'mm-zona',lock:true,
    points:[{timestamp:KLST[t.i_ret].timestamp},{timestamp:KLST[t.i_sin].timestamp}],
    extendData:{cor:alfa(c_('prata'),.14)}});
  kchart.createOverlay({name:'mm-zona',lock:true,
    points:[{timestamp:KLST[t.i_ent].timestamp},{timestamp:KLST[t.i_sai].timestamp}],
    extendData:{cor:alfa(t.pts>=0?c_('ganho'):c_('perda'),.09)}});

  [{i:t.i_ret,rot:'retracao',cor:c_('mudo'),degrau:2},
   {i:t.i_sin,rot:t.lado>0?'continuacao (compra)':'continuacao (venda)',
    cor:c_('prata'),degrau:1},
   {i:t.i_sai,rot:t.rot_saida,cor:t.pts>=0?c_('ganho'):c_('perda'),degrau:0}
  ].forEach(m=>kchart.createOverlay({name:'mm-marca',lock:true,
    points:[{timestamp:KLST[m.i].timestamp}],extendData:m}));

  /* o klinecharts 9 nao tem setVisibleRange: posiciona-se pela largura da
     barra mais o scroll ate o indice da direita */
  const de=Math.max(0,t.i_ret-30), ate=Math.min(KLST.length-1,t.i_sai+12);
  const janela=Math.max(12,ate-de+1);
  const larg=(kchart.getSize('candle_pane','main')||{}).width||760;
  kchart.setBarSpace(Math.max(1.2,Math.min(40,larg/janela)));
  kchart.scrollToDataIndex(ate+2);

  document.getElementById('ksel').value=String(kidx);
  const zero=Math.abs(t.pts)<1e-9, ok=t.pts>0;
  document.getElementById('kinfo').innerHTML=
    '<span><b>#'+(kidx+1)+'</b> de '+KTR.length+'</span>'+
    '<span>'+t.data+'</span>'+
    '<span><span class="tag"><span class="pt" style="background:'+c_(t.nivel)+'"></span>'+
      D.rotulo[t.nivel]+'</span></span>'+
    '<span>'+(t.lado>0?'compra':'venda')+'</span>'+
    '<span>entrada <b>'+fmt(t.preco_ent)+'</b></span>'+
    '<span>saida <b>'+fmt(t.preco_sai)+'</b> ('+t.rot_saida+')</span>'+
    '<span>resultado <b class="'+(zero?'':(ok?'pos':'neg'))+'">'+sinal(t.pts)+' pts</b>'+
      ' &middot; R$ '+sinal(t.pts*P.val_ponto,2)+'</span>'+
    '<span>MEP <b>'+sinal(t.mfe)+'</b> &middot; MEN <b>'+sinal(t.mae)+'</b></span>'+
    '<span>durou <b>'+t.dur_txt+'</b> ('+t.barras+' candles)</span>';
}

/* ------------------------------------------------ os filtros do grafico
   Tres eixos independentes -- nivel, modo de entrada e gestao -- e cada
   combinacao e uma carteira de verdade, ja montada pelo backteste (uma
   posicao por vez), nao um recorte cosmetico da lista.

   A combinacao antecipada + Ouro NAO existe, e o botao fica desligado: o
   nivel Ouro depende do pavio do candle de continuacao, que na hora em
   que a ordem antecipada e colocada ainda nao terminou de se formar.
   Medir a geometria do candle da RETRACAO no lugar dele foi testado e
   nao substitui -- as faixas nao ficam em ordem e o primeiro terco do
   periodo zera. Ver RESULTADOS.md. */
let kNivel='ouro', kModo='fecha', kGestao='parcial';

function kChave(){ return kModo+'|'+kGestao+'|'+kNivel; }

function kDisponivel(modo,nivel){
  return !!(D.variantes[modo+'|'+kGestao+'|'+nivel]||{}).trades;
}

function pintaBotoes(){
  document.querySelectorAll('#kfiltros [data-k]').forEach(b=>{
    const eixo=b.dataset.k, v=b.dataset.v;
    const atual={nivel:kNivel,modo:kModo,gestao:kGestao}[eixo];
    b.setAttribute('aria-pressed',String(v===atual));
    if(eixo==='nivel'){
      const ok=kDisponivel(kModo,v);
      b.disabled=!ok;
      b.title=ok?'':'O nivel Ouro nao existe na entrada antecipada: ele depende '+
        'do pavio do candle de continuacao, que ainda nao se formou quando a '+
        'ordem e colocada.';
    }
    if(eixo==='modo'){
      b.disabled=false;
    }
  });
  const v=D.variantes[kChave()];
  const s=v?v.stats:null;
  document.getElementById('kresumo').innerHTML = s
    ? `<b>${s.trades}</b> operacoes &middot; <b class="${s.lucro_liq>0?'pos':'neg'}">`+
      `${sinal(s.lucro_liq)} pts</b> &middot; ${sinal(s.exp_pts,1)} por trade `+
      `&middot; acerto ${fmt(s.winrate,1)}% &middot; fator ${fmt(s.fator_lucro,2)} `+
      `&middot; rebaixamento ${fmt(s.dd_max)}`
    : '';
}

function trocaLista(desenhar){
  const v=D.variantes[kChave()];
  KTR=(v&&v.trades&&v.trades.length)?v.trades:[];
  const sel=document.getElementById('ksel');
  sel.innerHTML=KTR.map((t,i)=>
    '<option value="'+i+'">#'+(i+1)+' &middot; '+t.data+' &middot; '+
    (t.lado>0?'compra':'venda')+' &middot; '+D.rotulo[t.nivel]+' &middot; '+
    sinal(t.pts)+' pts</option>').join('');
  pintaBotoes();
  /* na primeira carga quem desenha e o callback do applyNewData: o
     klinecharts ainda nao tem barra nenhuma quando isto roda */
  if(desenhar!==false && KTR.length) mostraTrade(0);
}

function iniciaNav(){
  document.getElementById('kfiltros').addEventListener('click',ev=>{
    const b=ev.target.closest('[data-k]'); if(!b||b.disabled) return;
    if(b.dataset.k==='nivel') kNivel=b.dataset.v;
    if(b.dataset.k==='gestao') kGestao=b.dataset.v;
    if(b.dataset.k==='modo'){
      kModo=b.dataset.v;
      /* saindo para a antecipada, o Ouro nao existe: cai para o Prata */
      if(!kDisponivel(kModo,kNivel)) kNivel='prata';
    }
    trocaLista();
  });

  const sel=document.getElementById('ksel');
  sel.addEventListener('change',()=>mostraTrade(+sel.value));
  document.getElementById('kant').addEventListener('click',()=>mostraTrade(kidx-1));
  document.getElementById('kprox').addEventListener('click',()=>mostraTrade(kidx+1));
  document.getElementById('kganho').addEventListener('click',()=>{
    for(let k=kidx+1;k<KTR.length;k++) if(KTR[k].pts>0) return mostraTrade(k);
    for(let k=0;k<KTR.length;k++) if(KTR[k].pts>0) return mostraTrade(k);});
  document.getElementById('kperda').addEventListener('click',()=>{
    for(let k=kidx+1;k<KTR.length;k++) if(KTR[k].pts<0) return mostraTrade(k);
    for(let k=0;k<KTR.length;k++) if(KTR[k].pts<0) return mostraTrade(k);});
  addEventListener('keydown',ev=>{
    if(ev.target.tagName==='SELECT'||ev.target.tagName==='BUTTON') return;
    if(ev.key==='ArrowLeft') mostraTrade(kidx-1);
    if(ev.key==='ArrowRight') mostraTrade(kidx+1);});

  const esc=(D.escolhida||'fecha|parcial|ouro').split('|');
  kModo=esc[0]; kGestao=esc[1]; kNivel=esc[2];
  trocaLista(false);
  iniciaKline();
}
iniciaNav();
"""
