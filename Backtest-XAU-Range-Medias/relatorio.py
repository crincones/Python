# -*- coding: utf-8 -*-
"""
saida/resumo.json + saida/barras.json -> relatorio.html

Um arquivo so, sem internet e sem servidor.

Tipografia: ao contrario do relatorio do estudo anterior (serifada, Georgia),
este usa uma pilha sans-serif moderna -- Inter / Segoe UI Variable / system-ui.
Tudo instalado no sistema, nada baixado: o arquivo continua abrindo offline.
Numeros em `font-variant-numeric: tabular-nums`, para as colunas alinharem.
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')


# --------------------------------------------------------------------------
def n(x, casas=0):
    if x == float('inf'):
        return '∞'
    s = ('%.*f' % (casas, x)).replace('.', ',')
    inteiro, _, dec = s.partition(',')
    neg = inteiro.startswith('-')
    inteiro = inteiro.lstrip('-')
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    out = ('-' if neg else '') + '.'.join(grupos)
    return out + (',' + dec if dec else '')


def fmt(x, casas=0):
    return ('+' if x > 0 else '') + n(x, casas)


def pct(x, casas=1):
    return n(100 * x, casas) + '%'


def cls(x):
    return 'pos' if x > 0 else ('neg' if x < 0 else 'nul')


CSS = """
:root{
  --tinta:#12161c; --tinta2:#5d6874; --tinta3:#8d97a3;
  --fundo:#f7f8fa; --papel:#ffffff; --linha:#e3e7ec; --grade:#eef1f5;
  --caixa:#f2f4f7; --realce:#3b5bdb; --alta:#0f9d76; --baixa:#e03131;
  --aviso:#f59f00;
  --sans:"Inter","Segoe UI Variable Text","Segoe UI",system-ui,
         -apple-system,BlinkMacSystemFont,"Helvetica Neue",Arial,sans-serif;
  --mono:ui-monospace,"Cascadia Code","JetBrains Mono","SF Mono",
         Consolas,monospace;
}
@media (prefers-color-scheme: dark){
  :root{
    --tinta:#e6e9ee; --tinta2:#98a2b0; --tinta3:#6b7686;
    --fundo:#0e1116; --papel:#161a21; --linha:#252b34; --grade:#1d222a;
    --caixa:#1b2027; --realce:#748ffc; --alta:#38d9a9; --baixa:#ff6b6b;
    --aviso:#ffd43b;
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--fundo);color:var(--tinta);
  font:15.5px/1.65 var(--sans);letter-spacing:-0.005em;
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
.env{max-width:960px;margin:0 auto;padding:0 24px 100px}
header{padding:72px 0 32px}
.eyebrow{font-size:12px;font-weight:600;letter-spacing:.1em;
  text-transform:uppercase;color:var(--realce);margin:0 0 14px}
h1{font-size:40px;line-height:1.12;margin:0 0 14px;letter-spacing:-0.028em;
  font-weight:700}
.sub{color:var(--tinta2);font-size:14.5px;margin:0;line-height:1.7}
h2{font-size:25px;margin:64px 0 8px;letter-spacing:-0.02em;font-weight:650;
  padding-top:22px;border-top:1px solid var(--linha)}
h3{font-size:18px;margin:34px 0 4px;font-weight:640;letter-spacing:-0.012em}
h4{font-size:12px;margin:26px 0 6px;text-transform:uppercase;
  letter-spacing:.09em;color:var(--tinta2);font-weight:650}
p{margin:13px 0}
a{color:var(--realce);text-decoration:none;border-bottom:1px solid transparent}
a:hover{border-bottom-color:var(--realce)}
code{font:12.5px/1.5 var(--mono);background:var(--caixa);padding:2px 6px;
  border-radius:5px;letter-spacing:0}
pre{background:var(--caixa);border:1px solid var(--linha);border-radius:10px;
  padding:16px 18px;overflow-x:auto;margin:20px 0}
pre code{background:none;padding:0;font-size:12.5px;line-height:1.65}
.lead{font-size:19.5px;line-height:1.55;color:var(--tinta);letter-spacing:-0.015em}
.destaque{background:var(--caixa);border-left:3px solid var(--realce);
  padding:16px 20px;margin:24px 0;border-radius:0 8px 8px 0}
.destaque p:first-child{margin-top:0}.destaque p:last-child{margin-bottom:0}
.aviso{border:1px solid var(--baixa);border-radius:10px;padding:16px 20px;
  margin:24px 0;background:color-mix(in srgb,var(--baixa) 6%,transparent)}
.aviso p:first-child{margin-top:0}.aviso p:last-child{margin-bottom:0}
.ok{border:1px solid var(--alta);border-radius:10px;padding:16px 20px;
  margin:24px 0;background:color-mix(in srgb,var(--alta) 6%,transparent)}
.ok p:first-child{margin-top:0}.ok p:last-child{margin-bottom:0}
table{border-collapse:collapse;width:100%;margin:20px 0;font-size:13px;
  font-variant-numeric:tabular-nums;letter-spacing:0}
th,td{padding:8px 11px;text-align:right;border-bottom:1px solid var(--linha)}
th:first-child,td:first-child{text-align:left}
thead th{border-bottom:1.5px solid var(--tinta2);font-weight:650;
  color:var(--tinta2);text-transform:uppercase;font-size:10.5px;
  letter-spacing:.07em;padding-bottom:7px}
tbody tr:hover{background:var(--caixa)}
tr.realce td{background:color-mix(in srgb,var(--realce) 9%,transparent);
  font-weight:600}
tr.risca td{color:var(--tinta3)}
.pos{color:var(--alta)}.neg{color:var(--baixa)}.nul{color:var(--tinta3)}
.rolagem{overflow-x:auto;margin:20px 0;
  -webkit-overflow-scrolling:touch}
.rolagem table{margin:0;min-width:560px}
.cartoes{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));
  gap:13px;margin:26px 0}
.cartao{background:var(--papel);border:1px solid var(--linha);
  border-radius:12px;padding:15px 17px}
.cartao .r{font-size:10.5px;color:var(--tinta2);text-transform:uppercase;
  letter-spacing:.08em;font-weight:600}
.cartao .v{font-size:28px;font-variant-numeric:tabular-nums;margin-top:5px;
  font-weight:680;letter-spacing:-0.03em;line-height:1.15}
.cartao .n{font-size:12px;color:var(--tinta2);margin-top:4px;line-height:1.45}
.painel{background:var(--papel);border:1px solid var(--linha);
  border-radius:14px;padding:18px;margin:26px 0}
.barras{display:flex;gap:14px;flex-wrap:wrap;align-items:center;
  font-size:13px;margin-bottom:14px}
label{display:flex;gap:6px;align-items:center;color:var(--tinta2);
  font-size:12px;font-weight:550}
select,button{font:13px var(--sans);padding:7px 11px;border:1px solid var(--linha);
  border-radius:8px;background:var(--papel);color:var(--tinta);cursor:pointer;
  font-weight:550}
select:hover,button:hover{border-color:var(--realce)}
button:disabled{opacity:.35;cursor:default}
canvas{display:block;width:100%;border-radius:8px}
.dica{position:fixed;pointer-events:none;visibility:hidden;z-index:9;
  background:var(--papel);border:1px solid var(--linha);border-radius:9px;
  padding:9px 12px;font-size:12px;line-height:1.6;
  box-shadow:0 8px 26px rgba(0,0,0,.15);max-width:360px;
  font-variant-numeric:tabular-nums}
.legenda{font-size:12px;color:var(--tinta2);display:flex;gap:18px;
  flex-wrap:wrap;margin-top:11px}
.legenda i{display:inline-block;width:14px;height:3px;vertical-align:middle;
  margin-right:6px;border-radius:2px}
.ficha{display:grid;grid-template-columns:repeat(auto-fit,minmax(112px,1fr));
  gap:12px;font-size:13px;margin-top:14px}
.ficha div span{display:block;color:var(--tinta2);font-size:10.5px;
  text-transform:uppercase;letter-spacing:.06em;font-weight:600}
.ficha b{font-variant-numeric:tabular-nums;font-weight:650;font-size:15px}
.conta{font-size:12px;color:var(--tinta2);font-variant-numeric:tabular-nums}
dl.glos{margin:20px 0}
dl.glos dt{font-weight:660;margin-top:18px;letter-spacing:-0.01em}
dl.glos dd{margin:3px 0 0;color:var(--tinta2)}
.sumario{font-size:13.5px;line-height:2;columns:2;column-gap:36px;
  margin:28px 0 0;padding:20px 0;border-top:1px solid var(--linha);
  border-bottom:1px solid var(--linha)}
.sumario a{color:var(--tinta2);font-weight:550}
.sumario a:hover{color:var(--realce)}
.selo{display:inline-block;font-size:10.5px;font-weight:650;padding:2px 7px;
  border-radius:5px;letter-spacing:.03em;vertical-align:middle}
.selo.sim{background:color-mix(in srgb,var(--alta) 16%,transparent);
  color:var(--alta)}
.selo.nao{background:color-mix(in srgb,var(--baixa) 16%,transparent);
  color:var(--baixa)}
footer{margin-top:70px;padding-top:22px;border-top:1px solid var(--linha);
  font-size:12.5px;color:var(--tinta2)}
@media(max-width:640px){.sumario{columns:1}h1{font-size:30px}
  .env{padding:0 16px 60px}header{padding:44px 0 24px}}
"""

JS = r"""
(function(){
'use strict';
var R = window.__RESUMO__, B = window.__BARRAS__;
var TICK = 0.01;

var N = B.c.length;
var close=new Float64Array(N),open=new Float64Array(N),
    high=new Float64Array(N),low=new Float64Array(N),tempo=new Float64Array(N);
var acc=B.t0;
for (var i=0;i<N;i++){
  var c=B.c[i];
  close[i]=c*TICK; open[i]=(c+B.o[i])*TICK;
  high[i]=(c+B.h[i])*TICK; low[i]=(c+B.l[i])*TICK;
  acc += (i? B.dt[i]:0); tempo[i]=acc;
}
var agrC=B.cv, agrV=B.vv;
var marca={}; B.sinais.forEach(function(p){ marca[p[0]]=p[1]; });

/* ---- medias: calculadas aqui para nao dobrar o tamanho do arquivo ------ */
function ema(span){
  var a=2/(span+1), out=new Float64Array(N), v=close[0]; out[0]=v;
  for (var i=1;i<N;i++){ v=close[i]*a+v*(1-a); out[i]=v; }
  return out;
}
function wma(src,n){
  n=Math.max(1,Math.round(n));
  var out=new Float64Array(N); out.fill(NaN);
  var den=n*(n+1)/2;
  for (var i=n-1;i<N;i++){
    var s=0, ok=true;
    for (var k=0;k<n;k++){
      var x=src[i-n+1+k];
      if (isNaN(x)){ ok=false; break; }
      s += x*(k+1);
    }
    out[i] = ok ? s/den : NaN;
  }
  return out;
}
function hull(n){
  var a=wma(close,n/2), b=wma(close,n);
  var bruto=new Float64Array(N);
  for (var i=0;i<N;i++) bruto[i]=2*a[i]-b[i];
  return wma(bruto,Math.sqrt(n));
}
var MA={};
MA.ema=[ema(21),ema(42),ema(72)];
MA.hull=[hull(21),hull(42),hull(72)];

/* ---- utilitarios ------------------------------------------------------- */
function num(x,d){ d=d||0;
  return x.toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d}); }
function sgn(x,d){ return (x>0?'+':'')+num(x,d||0); }
function classe(x){ return x>0?'pos':(x<0?'neg':'nul'); }
function data(ts){
  var d=new Date(ts*1000);
  function p(x){ return (x<10?'0':'')+x; }
  return d.getUTCFullYear()+'-'+p(d.getUTCMonth()+1)+'-'+p(d.getUTCDate())+
    ' '+p(d.getUTCHours())+':'+p(d.getUTCMinutes());
}
function cor(v){ return getComputedStyle(document.documentElement)
  .getPropertyValue(v).trim(); }

/* ---- grafico: preco + medias em cima, esforco e delta embaixo ---------- */
function Kline(cv,dica){
  this.cv=cv; this.dica=dica; this.ctx=cv.getContext('2d');
  this.win=null; this.op=null; this.cfg=null;
  var self=this;
  cv.addEventListener('mousemove',function(e){ self.hover(e); });
  cv.addEventListener('mouseleave',function(){ dica.style.visibility='hidden'; });
  window.addEventListener('resize',function(){ self.pinta(); });
}
Kline.prototype.mostra=function(op,cfg){
  this.op=op; this.cfg=cfg;
  var a=Math.max(0,op.sinal_i-26);
  var fim=op.saida_i>=0?op.saida_i:op.sinal_i+8;
  var b=Math.min(N-1,fim+8);
  if (b-a<42) b=Math.min(N-1,a+42);
  this.win=[a,b]; this.pinta();
};
Kline.prototype.geo=function(){
  var cv=this.cv,w=cv.clientWidth,h=520;
  var dpr=window.devicePixelRatio||1;
  if (cv.width!==Math.round(w*dpr)||cv.height!==Math.round(h*dpr)){
    cv.width=Math.round(w*dpr); cv.height=Math.round(h*dpr);
    cv.style.height=h+'px';
  }
  this.ctx.setTransform(dpr,0,0,dpr,0,0);
  return {w:w,h:h,ml:8,mr:76,mt:12,mb:34,hp:320,gap:20};
};
Kline.prototype.escala=function(){
  var a=this.win[0],b=this.win[1],op=this.op,cfg=this.cfg;
  var lo=Infinity,hi=-Infinity;
  var mm=MA[cfg.ma_tipo]||MA.ema;
  for (var i=a;i<=b;i++){
    if (low[i]<lo) lo=low[i]; if (high[i]>hi) hi=high[i];
    for (var k=0;k<3;k++){ var v=mm[k][i];
      if (!isNaN(v)){ if(v<lo)lo=v; if(v>hi)hi=v; } }
  }
  var s=op.lado==='long'?1:-1;
  [op.entrada-s*cfg.stop_ticks*TICK,
   op.entrada+s*cfg.alvo_ticks*TICK,
   op.entrada+s*cfg.gatilho_ticks*TICK,
   op.entrada].forEach(function(p){ if(p<lo)lo=p; if(p>hi)hi=p; });
  var pad=(hi-lo)*0.06||1;
  return {lo:lo-pad,hi:hi+pad};
};
Kline.prototype.pinta=function(){
  if (!this.op) return;
  var g=this.geo(),ctx=this.ctx,a=this.win[0],b=this.win[1];
  var op=this.op,cfg=this.cfg,es=this.escala();
  var cnt=b-a+1, pw=(g.w-g.ml-g.mr)/cnt;
  var cw=Math.max(1.4,Math.min(pw*0.64,13));
  function X(i){ return g.ml+(i-a+0.5)*pw; }
  function Y(p){ return g.mt+(es.hi-p)/(es.hi-es.lo)*(g.hp-g.mt); }
  this.X=X; this.Y=Y; this.pw=pw;

  ctx.clearRect(0,0,g.w,g.h);
  ctx.fillStyle=cor('--papel'); ctx.fillRect(0,0,g.w,g.h);

  var passo=Math.pow(10,Math.floor(Math.log10((es.hi-es.lo)/5)));
  [1,2,2.5,5,10].some(function(m){ if((es.hi-es.lo)/(passo*m)<=7){passo*=m;return true;} });
  ctx.strokeStyle=cor('--grade'); ctx.lineWidth=1;
  ctx.fillStyle=cor('--tinta2');
  ctx.font='11px '+cor('--sans').split(',')[0].replace(/"/g,'')+',sans-serif';
  ctx.textAlign='left';
  for (var p=Math.ceil(es.lo/passo)*passo;p<=es.hi;p+=passo){
    var y=Math.round(Y(p))+0.5;
    ctx.beginPath(); ctx.moveTo(g.ml,y); ctx.lineTo(g.w-g.mr,y); ctx.stroke();
    ctx.fillText(num(p,2),g.w-g.mr+7,y+3.5);
  }

  var i0=op.sinal_i+1,i1=op.saida_i>=0?op.saida_i:i0;
  ctx.fillStyle=cor('--realce'); ctx.globalAlpha=0.09;
  ctx.fillRect(X(i0)-pw/2,g.mt,(i1-i0+1)*pw,g.hp-g.mt);
  ctx.globalAlpha=1;

  /* niveis da operacao */
  var s=op.lado==='long'?1:-1;
  var linhas=[[op.entrada,cor('--tinta'),'entrada '+num(op.entrada,2),[]],
    [op.entrada-s*cfg.stop_ticks*TICK,cor('--baixa'),
     'stop −'+num(cfg.stop_ticks)+'t',[5,4]],
    [op.entrada+s*cfg.alvo_ticks*TICK,cor('--alta'),
     'alvo +'+num(cfg.alvo_ticks)+'t',[5,4]]];
  if (cfg.modo!=='fixo')
    linhas.push([op.entrada+s*cfg.gatilho_ticks*TICK,cor('--aviso'),
                 (cfg.modo==='breakeven'?'breakeven':'parcial')+' +'+
                 num(cfg.gatilho_ticks)+'t',[2,3]]);
  ctx.font='10.5px '+cor('--sans').split(',')[0].replace(/"/g,'')+',sans-serif';
  var usados=[];
  linhas.sort(function(p,q){ return Y(p[0])-Y(q[0]); }).forEach(function(L){
    var y=Math.round(Y(L[0]))+0.5;
    if (y<g.mt+6||y>g.hp-6) return;
    ctx.save(); ctx.setLineDash(L[3]); ctx.strokeStyle=L[1]; ctx.lineWidth=1.2;
    ctx.beginPath(); ctx.moveTo(g.ml,y); ctx.lineTo(g.w-g.mr,y); ctx.stroke();
    ctx.restore();
    var ye=y-2;
    usados.forEach(function(u){ if(Math.abs(ye-u)<12) ye=u+12; });
    usados.push(ye);
    var lg=ctx.measureText(L[2]).width;
    ctx.fillStyle=cor('--papel'); ctx.fillRect(g.ml+2,ye-9,lg+8,12);
    ctx.fillStyle=L[1]; ctx.fillText(L[2],g.ml+5,ye);
  });

  /* as medias da variante em exibicao */
  var mm=MA[cfg.ma_tipo]||MA.ema;
  [[mm[2],'#9775fa',1.3],[mm[1],'#4dabf7',1.4],[mm[0],'#f59f00',1.9]]
   .forEach(function(M){
    ctx.strokeStyle=M[1]; ctx.lineWidth=M[2]; ctx.beginPath();
    var iniciou=false;
    for (var i=a;i<=b;i++){
      var v=M[0][i]; if (isNaN(v)){ iniciou=false; continue; }
      var x=X(i),y=Y(v);
      if(!iniciou){ ctx.moveTo(x,y); iniciou=true; } else ctx.lineTo(x,y);
    }
    ctx.stroke();
  });

  /* candles */
  for (var i=a;i<=b;i++){
    var sobe=close[i]>=open[i];
    var c=sobe?cor('--alta'):cor('--baixa');
    var x=X(i);
    ctx.strokeStyle=c; ctx.lineWidth=1;
    ctx.beginPath();
    ctx.moveTo(Math.round(x)+0.5,Y(high[i]));
    ctx.lineTo(Math.round(x)+0.5,Y(low[i])); ctx.stroke();
    var yo=Y(open[i]),yc=Y(close[i]);
    ctx.fillStyle=c;
    ctx.fillRect(x-cw/2,Math.min(yo,yc),cw,Math.max(1,Math.abs(yc-yo)));
  }

  /* setas do indicador, como no .mq5 */
  for (var i=a;i<=b;i++){
    var m=marca[i]; if(!m) continue;
    var alta=m>0, div=Math.abs(m)===2;
    var cc=div?cor('--realce'):(alta?cor('--alta'):cor('--baixa'));
    var yy=alta?Y(low[i])+11:Y(high[i])-11, d=alta?-1:1;
    ctx.fillStyle=cc; ctx.globalAlpha=(i===op.sinal_i)?1:0.42;
    ctx.beginPath();
    ctx.moveTo(X(i),yy+d*6); ctx.lineTo(X(i)-4.5,yy-d*1.5);
    ctx.lineTo(X(i)+4.5,yy-d*1.5); ctx.closePath(); ctx.fill();
    ctx.globalAlpha=1;
  }

  /* painel de esforco e de delta, em duas faixas com escalas proprias */
  var ya=g.hp+g.gap, ha=g.h-g.mb-ya;
  var hA=ha*0.52, hB=ha-hA-8;
  var baseA=ya+hA, midB=ya+hA+8+hB/2;
  var mxE=1,mxD=1;
  for (var i=a;i<=b;i++){
    mxE=Math.max(mxE,agrC[i]+agrV[i]);
    mxD=Math.max(mxD,Math.abs(agrC[i]-agrV[i]));
  }
  for (var i=a;i<=b;i++){
    var x=X(i),bw=Math.max(1.4,Math.min(pw*0.64,13));
    var esf=agrC[i]+agrV[i], dlt=agrC[i]-agrV[i];
    var atual=(i===op.sinal_i);
    ctx.globalAlpha=atual?0.8:0.26;
    ctx.fillStyle=cor('--tinta2');
    var he=(esf/mxE)*hA; ctx.fillRect(x-bw/2,baseA-he,bw,he);
    ctx.globalAlpha=atual?1:0.5;
    ctx.fillStyle=dlt>=0?cor('--alta'):cor('--baixa');
    var hd=(Math.abs(dlt)/mxD)*(hB/2);
    ctx.fillRect(x-bw/2,dlt>=0?midB-hd:midB,bw,hd);
    ctx.globalAlpha=1;
  }
  ctx.strokeStyle=cor('--linha'); ctx.lineWidth=1;
  ctx.beginPath(); ctx.moveTo(g.ml,Math.round(baseA)+0.5);
  ctx.lineTo(g.w-g.mr,Math.round(baseA)+0.5); ctx.stroke();
  ctx.strokeStyle=cor('--tinta3');
  ctx.beginPath(); ctx.moveTo(g.ml,Math.round(midB)+0.5);
  ctx.lineTo(g.w-g.mr,Math.round(midB)+0.5); ctx.stroke();
  ctx.fillStyle=cor('--tinta2');
  ctx.font='10.5px '+cor('--sans').split(',')[0].replace(/"/g,'')+',sans-serif';
  ctx.textAlign='left';
  ctx.fillText('esforço',g.ml+4,ya+10);
  ctx.fillText(num(mxE),g.w-g.mr+7,ya+10);
  ctx.fillText('delta',g.ml+4,midB-hB/2+10);
  ctx.fillText('±'+num(mxD),g.w-g.mr+7,midB+3.5);

  function vert(i,txt,c,cima){
    if (i<a||i>b) return;
    var x=X(i);
    ctx.save(); ctx.setLineDash([2,3]); ctx.strokeStyle=c; ctx.lineWidth=1.2;
    ctx.beginPath(); ctx.moveTo(x,g.mt); ctx.lineTo(x,g.h-g.mb); ctx.stroke();
    ctx.restore();
    var y=cima?g.mt+10:g.h-g.mb+12;
    ctx.font='10px '+cor('--sans').split(',')[0].replace(/"/g,'')+',sans-serif';
    ctx.textAlign='center';
    var lg=ctx.measureText(txt).width;
    ctx.fillStyle=cor('--papel'); ctx.fillRect(x-lg/2-3,y-9,lg+6,12);
    ctx.fillStyle=c; ctx.fillText(txt,x,y);
  }
  vert(op.sinal_i,'sinal',cor('--realce'),true);
  vert(op.sinal_i+1,'entrada',cor('--tinta2'),false);
  if (op.saida_i>op.sinal_i+1) vert(op.saida_i,'saída',cor('--tinta2'),true);

  ctx.strokeStyle=cor('--linha'); ctx.lineWidth=1;
  ctx.strokeRect(0.5,0.5,g.w-1,g.h-1);
};
Kline.prototype.hover=function(e){
  if (!this.win) return;
  var r=this.cv.getBoundingClientRect();
  var i=Math.round(this.win[0]+(e.clientX-r.left-8)/this.pw-0.5);
  if (i<this.win[0]||i>this.win[1]){ this.dica.style.visibility='hidden'; return; }
  var mm=MA[this.cfg.ma_tipo]||MA.ema;
  var lq=(!isNaN(mm[0][i])&&!isNaN(mm[2][i]))
    ? num(Math.abs(mm[0][i]-mm[2][i])/TICK)+' t' : '—';
  this.dica.innerHTML='<b>'+data(tempo[i])+'</b><br>'+
    'A '+num(open[i],2)+' · M '+num(high[i],2)+' · m '+num(low[i],2)+
    ' · F '+num(close[i],2)+
    '<br>corpo '+num((close[i]-open[i])/TICK)+' t · leque '+lq+
    '<br>esforço '+num(agrC[i]+agrV[i])+' · delta '+sgn(agrC[i]-agrV[i]);
  this.dica.style.left=Math.min(e.clientX+14,innerWidth-370)+'px';
  this.dica.style.top=(e.clientY+14)+'px';
  this.dica.style.visibility='visible';
};

/* ---- curva ------------------------------------------------------------- */
function curva(cv,pontos){
  var ctx=cv.getContext('2d'),w=cv.clientWidth,h=200;
  var dpr=window.devicePixelRatio||1;
  cv.width=Math.round(w*dpr); cv.height=Math.round(h*dpr);
  cv.style.height=h+'px'; ctx.setTransform(dpr,0,0,dpr,0,0);
  ctx.fillStyle=cor('--papel'); ctx.fillRect(0,0,w,h);
  if(!pontos.length) return;
  var lo=0,hi=0;
  pontos.forEach(function(p){ if(p[1]<lo)lo=p[1]; if(p[1]>hi)hi=p[1]; });
  var pad=(hi-lo)*0.08||1; lo-=pad; hi+=pad;
  var ml=8,mr=68,mt=10,mb=18;
  function X(i){ return ml+i/(pontos.length-1||1)*(w-ml-mr); }
  function Y(v){ return mt+(hi-v)/(hi-lo)*(h-mt-mb); }
  ctx.strokeStyle=cor('--grade'); ctx.fillStyle=cor('--tinta2');
  ctx.font='10.5px system-ui,sans-serif'; ctx.textAlign='left';
  [lo,(lo+hi)/2,hi].forEach(function(v){
    var y=Math.round(Y(v))+0.5;
    ctx.beginPath(); ctx.moveTo(ml,y); ctx.lineTo(w-mr,y); ctx.stroke();
    ctx.fillText(sgn(v,0)+' t',w-mr+6,y+3.5);
  });
  ctx.strokeStyle=cor('--tinta3'); ctx.lineWidth=1;
  var y0=Math.round(Y(0))+0.5;
  ctx.beginPath(); ctx.moveTo(ml,y0); ctx.lineTo(w-mr,y0); ctx.stroke();
  var fim=pontos[pontos.length-1][1];
  ctx.strokeStyle=fim>=0?cor('--alta'):cor('--baixa'); ctx.lineWidth=1.8;
  ctx.beginPath();
  pontos.forEach(function(p,i){ var x=X(i),y=Y(p[1]);
    if(!i) ctx.moveTo(x,y); else ctx.lineTo(x,y); });
  ctx.stroke();
  ctx.strokeStyle=cor('--linha'); ctx.lineWidth=1; ctx.strokeRect(.5,.5,w-1,h-1);
}

/* ---- navegador --------------------------------------------------------- */
var selVar=document.getElementById('selVar');
var selMot=document.getElementById('selMot');
var selLado=document.getElementById('selLado');
var btPrev=document.getElementById('btPrev');
var btProx=document.getElementById('btProx');
var conta=document.getElementById('conta');
var ficha=document.getElementById('ficha');
var desc=document.getElementById('descVar');
var kl=new Kline(document.getElementById('cvKline'),
                 document.getElementById('dica'));
var lista=[],pos=0;

function opDe(v,linha){
  var o={}; v.trades.colunas.forEach(function(c,i){ o[c]=linha[i]; }); return o;
}
function variante(){ return R.variantes[+selVar.value]; }

function opcoesMotivo(v){
  var vistos={};
  v.trades.linhas.forEach(function(L){ vistos[L[v.trades.colunas.indexOf('motivo')]]=1; });
  var rot={alvo:'alvo',stop:'stop',breakeven:'breakeven',
           empate:'empate (breakeven da operação)',tempo:'aberta no fim'};
  var h='<option value="*">todos</option>';
  Object.keys(vistos).forEach(function(k){
    h+='<option value="'+k+'">'+(rot[k]||k)+'</option>'; });
  selMot.innerHTML=h;
}

function filtra(){
  var v=variante();
  lista=v.trades.linhas.map(function(L){ return opDe(v,L); })
    .filter(function(o){
      if (selMot.value!=='*'&&o.motivo!==selMot.value) return false;
      if (selLado.value!=='*'&&o.lado!==selLado.value) return false;
      return true;
    });
  pos=0;
  desc.textContent=v.descricao;
  curva(document.getElementById('cvCurva'),v.curva);
  mostra();
}
function trocaVar(){ opcoesMotivo(variante()); filtra(); }

function mostra(){
  if (!lista.length){
    conta.textContent='nenhuma operação com esse filtro';
    ficha.innerHTML=''; btPrev.disabled=btProx.disabled=true; return;
  }
  var v=variante(),o=lista[pos];
  kl.mostra(o,v.cfg);
  var tot=v.trades.total,mostradas=v.trades.linhas.length;
  conta.textContent='operação '+(pos+1)+' de '+lista.length+
    (mostradas<tot?'  (amostra de '+num(mostradas)+' das '+num(tot)+')':'');
  var rot={alvo:'alvo',stop:'stop',breakeven:'breakeven',
           empate:'empate (breakeven da operação)',
           tempo:'aberta no fim do histórico'};
  ficha.innerHTML=
    '<div><span>quando</span><b>'+data(tempo[o.sinal_i])+'</b></div>'+
    '<div><span>sinal</span><b>'+(o.tipo===2?'divergência':'absorção')+'</b></div>'+
    '<div><span>lado</span><b>'+(o.lado==='long'?'compra':'venda')+'</b></div>'+
    '<div><span>entrada</span><b>'+num(o.entrada,2)+'</b></div>'+
    '<div><span>desfecho</span><b>'+(rot[o.motivo]||o.motivo)+'</b></div>'+
    '<div><span>resultado</span><b class="'+classe(o.ticks)+'">'+
      sgn(o.ticks,0)+' t</b></div>'+
    '<div><span>em R</span><b class="'+classe(o.ticks)+'">'+
      sgn(o.ticks/v.cfg.stop_ticks,2)+'R</b></div>'+
    '<div><span>barras</span><b>'+o.barras+'</b></div>'+
    '<div><span>leque</span><b>'+num(o.leque)+' t</b></div>'+
    '<div><span>dist. da MA21</span><b>'+sgn(o.dist_ma1)+' t</b></div>'+
    '<div><span>esforço rel.</span><b>'+num(o.esf_rel,2)+'</b></div>';
  btPrev.disabled=pos<=0; btProx.disabled=pos>=lista.length-1;
}
selVar.onchange=trocaVar; selMot.onchange=filtra; selLado.onchange=filtra;
btPrev.onclick=function(){ if(pos>0){pos--;mostra();} };
btProx.onclick=function(){ if(pos<lista.length-1){pos++;mostra();} };
document.addEventListener('keydown',function(e){
  if (e.key==='ArrowLeft') btPrev.click();
  if (e.key==='ArrowRight') btProx.click();
});
trocaVar();
})();
"""


# --------------------------------------------------------------------------
def selo(ok):
    return ('<span class="selo sim">mensurável</span>' if ok
            else '<span class="selo nao">indeterminado</span>')


def tab_variantes(r):
    L = ['<div class="rolagem"><table><thead><tr><th>variante</th>'
         '<th>ops</th><th>acerto</th><th>payoff</th><th>fator de lucro</th>'
         '<th>expectativa</th><th>t</th><th>rebaixamento</th>'
         '<th>seq. perdas</th><th>seq. ganhos</th><th></th>'
         '</tr></thead><tbody>']
    for v in r['variantes']:
        s = v['stats']
        L.append('<tr%s><td><b>%s</b> · %s</td><td>%s</td><td>%s</td>'
                 '<td>%s</td><td>%s</td><td class="%s">%s R</td>'
                 '<td class="%s">%s</td><td class="neg">%s R</td>'
                 '<td>%s</td><td>%s</td><td>%s</td></tr>'
                 % (' class="realce"' if v['nome'] == 'V2' else '',
                    v['nome'], v['rotulo'], n(s.get('operacoes', 0)),
                    pct(s.get('acerto', 0)), n(s.get('payoff', 0), 2),
                    n(s.get('fator_lucro', 0), 2),
                    cls(s.get('expectativa_R', 0)),
                    fmt(s.get('expectativa_R', 0), 3),
                    cls(s.get('t_stat', 0)), fmt(s.get('t_stat', 0), 2),
                    n(s.get('drawdown_R', 0), 1),
                    n(s.get('max_perdas_seguidas', 0)),
                    n(s.get('max_ganhos_seguidos', 0)),
                    selo(v['mensuravel'])))
    L.append('</tbody></table></div>')
    return '\n'.join(L)


def tab_completa(r):
    vv = [v for v in r['variantes'] if v['mensuravel']]
    campos = [
        ('Operações', 'operacoes', lambda x: n(x)),
        ('Vitórias / perdas / neutras', None, None),
        ('Acerto', 'acerto', lambda x: pct(x)),
        ('Ganho médio', 'ganho_medio', lambda x: '%s t' % fmt(x, 1)),
        ('Perda média', 'perda_media', lambda x: '%s t' % fmt(x, 1)),
        ('Payoff', 'payoff', lambda x: n(x, 2)),
        ('Fator de lucro', 'fator_lucro', lambda x: n(x, 2)),
        ('Fator de recuperação', 'fator_recuperacao', lambda x: n(x, 2)),
        ('Expectativa (R)', 'expectativa_R', lambda x: fmt(x, 3)),
        ('Expectativa (ticks)', 'expectativa_ticks', lambda x: fmt(x, 1)),
        ('Desvio (ticks)', 'desvio_ticks', lambda x: n(x, 1)),
        ('t', 't_stat', lambda x: fmt(x, 2)),
        ('SQN', 'sqn', lambda x: n(x, 2)),
        ('Rebaixamento (R)', 'drawdown_R', lambda x: n(x, 1)),
        ('Rebaixamento (operações)', 'drawdown_operacoes', lambda x: n(x)),
        ('Máx. perdas seguidas', 'max_perdas_seguidas', lambda x: n(x)),
        ('Máx. ganhos seguidos', 'max_ganhos_seguidos', lambda x: n(x)),
        ('Máx. sem ganho seguidas', 'max_sem_ganho_seguidas', lambda x: n(x)),
        ('Média de perdas seguidas', 'media_perdas_seguidas', lambda x: n(x, 2)),
        ('Barras por operação', 'barras_media', lambda x: n(x, 1)),
        ('Operações por pregão', 'ops_por_dia', lambda x: n(x, 1)),
        ('Dias positivos / negativos', None, None),
    ]
    L = ['<div class="rolagem"><table><thead><tr><th></th>%s</tr></thead><tbody>'
         % ''.join('<th>%s</th>' % v['nome'] for v in vv)]
    for rot, k, f in campos:
        if k is None:
            if 'Vitórias' in rot:
                cel = ''.join('<td>%s / %s / %s</td>'
                              % (n(v['stats'].get('vitorias', 0)),
                                 n(v['stats'].get('perdas', 0)),
                                 n(v['stats'].get('neutras', 0))) for v in vv)
            else:
                cel = ''.join('<td>%s / %s</td>'
                              % (n(v['stats'].get('dias_positivos', 0)),
                                 n(v['stats'].get('dias_negativos', 0)))
                              for v in vv)
        else:
            cel = ''.join('<td>%s</td>' % f(v['stats'].get(k, 0)) for v in vv)
        L.append('<tr><td>%s</td>%s</tr>' % (rot, cel))
    L.append('</tbody></table></div>')
    return '\n'.join(L)


def tab_ambiguidade(r):
    L = ['<div class="rolagem"><table><thead><tr><th>stop</th><th>alvo</th>'
         '<th>modo</th><th>piso</th><th>padrão</th><th>teto</th>'
         '<th>largura</th><th></th></tr></thead><tbody>']
    for x in r['ambiguidade']:
        if x['stop_ticks'] not in (194.0, 388.0, 450.0):
            continue
        L.append('<tr%s><td>%s t</td><td>%s t</td><td><code>%s</code></td>'
                 '<td class="%s">%s</td><td class="%s">%s</td>'
                 '<td class="%s">%s</td><td>%s R</td><td>%s</td></tr>'
                 % (' class="realce"' if x['mensuravel'] else '',
                    n(x['stop_ticks']), n(x['alvo_ticks']), x['modo'],
                    cls(x['piso']), fmt(x['piso'], 3),
                    cls(x['padrao']), fmt(x['padrao'], 3),
                    cls(x['teto']), fmt(x['teto'], 3),
                    n(x['largura'], 3), selo(x['mensuravel'])))
    L.append('</tbody></table></div>')
    return '\n'.join(L)


def tab_sweep(r):
    SW = r['sweep_stop']
    L = ['<div class="rolagem"><table><thead><tr><th>stop</th><th>alvo</th>'
         '<th>ops</th><th>acerto</th><th>expectativa</th><th>t</th>'
         '<th>largura</th><th>1ª metade</th><th>2ª metade</th><th></th>'
         '</tr></thead><tbody>']
    for g in SW['linhas']:
        L.append('<tr%s><td>%s t</td><td>%s t</td><td>%s</td><td>%s</td>'
                 '<td class="%s">%s R</td><td class="%s">%s</td><td>%s</td>'
                 '<td class="%s">%s</td><td class="%s">%s</td><td>%s</td></tr>'
                 % (' class="realce"' if g['stop_ticks'] == 194.0 else '',
                    n(g['stop_ticks']), n(g['alvo_ticks']), n(g['n']),
                    pct(g['acerto']), cls(g['expectativa_R']),
                    fmt(g['expectativa_R'], 3), cls(g['t_stat']),
                    fmt(g['t_stat'], 2), n(g['largura'], 3),
                    cls(g['metade_1a']), fmt(g['metade_1a'], 3),
                    cls(g['metade_2a']), fmt(g['metade_2a'], 3),
                    selo(g['mensuravel'])))
    L.append('</tbody></table></div>')
    return '\n'.join(L)


def tab_grid(r, mensuraveis_apenas, limite=10):
    G = [g for g in r['grid'] if (g['mensuravel'] or not mensuraveis_apenas)]
    G = sorted(G, key=lambda x: -x['expectativa_R'])[:limite]
    L = ['<div class="rolagem"><table><thead><tr><th>média</th><th>leque</th>'
         '<th>modo</th><th>stop</th><th>ops</th><th>acerto</th><th>payoff</th>'
         '<th>fator de lucro</th><th>expectativa</th><th>t</th><th></th>'
         '</tr></thead><tbody>']
    for g in G:
        L.append('<tr><td>%s</td><td>≥%s t</td><td><code>%s</code></td>'
                 '<td>%s t</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>'
                 '<td class="%s">%s R</td><td class="%s">%s</td><td>%s</td></tr>'
                 % (g['ma_tipo'].upper(), n(g['leque_min']), g['modo'],
                    n(g['stop_ticks']), n(g['n']), pct(g['acerto']),
                    n(g['payoff'], 2), n(g['fator_lucro'], 2),
                    cls(g['expectativa_R']), fmt(g['expectativa_R'], 3),
                    cls(g['t_stat']), fmt(g['t_stat'], 2),
                    selo(g['mensuravel'])))
    L.append('</tbody></table></div>')
    return '\n'.join(L)


def tab_medias(r):
    M = r['medias']
    campos = [('Barras de aquecimento', 'aquecimento', lambda x: n(x)),
              ('Tempo com leque ordenado', 'pct_ordenado', lambda x: pct(x)),
              ('Tempo embolado', 'pct_embolado', lambda x: pct(x)),
              ('Trocas de lado do leque', 'trocas_de_lado', lambda x: n(x)),
              ('Barras entre trocas', 'barras_por_troca', lambda x: n(x)),
              ('Duração mediana da tendência', 'duracao_mediana_tendencia',
               lambda x: '%s barras' % n(x)),
              ('Leque mediano', 'leque', lambda x: '%s t' % n(x['50%'])),
              ('Tempo com leque ≥ 400 t', 'pct_leque_400', lambda x: pct(x))]
    L = ['<div class="rolagem"><table><thead><tr><th></th><th>EMA</th>'
         '<th>Hull</th></tr></thead><tbody>']
    for rot, k, f in campos:
        L.append('<tr><td>%s</td><td>%s</td><td>%s</td></tr>'
                 % (rot, f(M['ema'][k]), f(M['hull'][k])))
    L.append('</tbody></table></div>')
    return '\n'.join(L)


def tab_validacao(r):
    VA = r['validacao']
    L = ['<div class="rolagem"><table><thead><tr><th>pedaço da amostra</th>'
         '<th>ops</th><th>acerto</th><th>expectativa</th><th>fator de lucro</th>'
         '<th>t</th></tr></thead><tbody>']
    linhas = [('amostra inteira', VA['geral'], True)]
    linhas += [('%sª metade' % nm[0], VA['metades'][nm], False)
               for nm in ('1a', '2a')]
    linhas += [('%sº terço' % v['terco'], v, False) for v in VA['tercos']]
    for rot, v, forte in linhas:
        L.append('<tr><td>%s%s%s</td><td>%s</td><td>%s</td>'
                 '<td class="%s">%s R</td><td>%s</td><td class="%s">%s</td></tr>'
                 % ('<b>' if forte else '', rot, '</b>' if forte else '',
                    n(v['n']), pct(v['acerto']), cls(v['expectativa_R']),
                    fmt(v['expectativa_R'], 3), n(v['fator_lucro'], 2),
                    cls(v['t_stat']), fmt(v['t_stat'], 2)))
    L.append('</tbody></table></div>')
    return '\n'.join(L)


def tab_controles(r):
    VA = r['validacao']
    rot = {'invertido': 'a mesma coisa, operando o lado oposto',
           'sem_leque': 'sem exigir contexto de médias',
           'leque_contra': 'só sinais CONTRA a tendência das médias',
           'direcao_sorteada': 'mesmas barras, direção sorteada, mesma gestão'}
    L = ['<div class="rolagem"><table><thead><tr><th>controle</th>'
         '<th>o que é</th><th>ops</th><th>acerto</th><th>expectativa</th>'
         '<th>t</th></tr></thead><tbody>']
    for k, v in VA['controles'].items():
        L.append('<tr><td><code>%s</code></td><td>%s</td><td>%s</td><td>%s</td>'
                 '<td class="%s">%s R</td><td class="%s">%s</td></tr>'
                 % (k, rot.get(k, ''), n(v['n']), pct(v['acerto']),
                    cls(v['expectativa_R']), fmt(v['expectativa_R'], 3),
                    cls(v['t_stat']), fmt(v['t_stat'], 2)))
    L.append('</tbody></table></div>')
    return '\n'.join(L)


def tab_sensibilidade(r):
    L = ['<div class="rolagem"><table><thead><tr><th>variante</th><th>piso</th>'
         '<th>padrão</th><th>teto</th><th>custo 10 t</th><th>custo 20 t</th>'
         '<th>custo 40 t</th><th>1ª metade</th><th>2ª metade</th>'
         '</tr></thead><tbody>']
    for v in r['variantes']:
        vals = [v['stats_piso'].get('expectativa_R', 0),
                v['stats'].get('expectativa_R', 0),
                v['stats_otimista'].get('expectativa_R', 0),
                v['custo']['10'].get('expectativa_R', 0),
                v['custo']['20'].get('expectativa_R', 0),
                v['custo']['40'].get('expectativa_R', 0),
                v['metades']['1a'].get('expectativa_R', 0),
                v['metades']['2a'].get('expectativa_R', 0)]
        L.append('<tr%s><td>%s · %s</td>%s</tr>'
                 % (' class="realce"' if v['nome'] == 'V2' else '',
                    v['nome'], v['rotulo'],
                    ''.join('<td class="%s">%s</td>' % (cls(x), fmt(x, 3))
                            for x in vals)))
    L.append('</tbody></table></div>')
    return '\n'.join(L)


GLOSSARIO = [
    ('Gráfico de range', 'Gráfico em que a barra fecha quando o preço percorre '
     'uma distância fixa — aqui, <b>388 ticks</b>. O tempo não conta. Como '
     '<code>High−Low</code> é constante por construção, valem regras '
     'geométricas exatas sobre o que cabe dentro de uma barra.'),
    ('Tick', 'A menor variação de preço. No XAUUSD vale <b>0,01 dólar</b>: '
     '388 ticks = 3,88 USD.'),
    ('R', 'A unidade de risco: quanto se perde num stop. Resultados em R são '
     'comparáveis entre gestões diferentes; em ticks, não.'),
    ('Leque', 'A distância entre a média mais curta e a mais longa, em ticks. '
     'Leque estreito = médias "emboladas" = consolidação. Leque aberto = '
     'tendência estabelecida.'),
    ('EMA', 'Média móvel exponencial: peso decai geometricamente para trás. '
     'Mais lenta que a Hull, e neste estudo é a que serve.'),
    ('Hull (HMA)', 'Média construída de três médias ponderadas encadeadas, '
     'desenhada para reduzir o atraso: <code>WMA(2·WMA(n/2) − WMA(n), √n)</code>. '
     'Persegue o preço de perto e vira antes — inclusive quando não devia.'),
    ('Esforço', 'A agressão total da barra: compradora + vendedora. Mede '
     'quanta gente negociou, independentemente de quem venceu.'),
    ('Delta', 'A agressão líquida: compradora − vendedora.'),
    ('Absorção (sinal 1)', 'A barra vira o movimento andando menos que o '
     'normal da direção dela e com menos agressão a favor que o normal.'),
    ('Divergência no pivô (sinal 2)', 'Duas barras quase sem pavio formam um '
     'pivô, e o delta somado das duas aponta para o lado contrário ao da '
     'resolução.'),
    ('Payoff', 'Ganho médio dividido pela perda média. Com alvo de 2R e stop '
     'de 1R sem gestão intermediária, o payoff é exatamente 2,00.'),
    ('Fator de lucro', 'Soma dos ganhos dividida pela soma das perdas. Acima '
     'de 1 a estratégia ganha dinheiro no período.'),
    ('Fator de recuperação', 'Resultado total dividido pelo maior '
     'rebaixamento. Quanto se ganhou por unidade de sofrimento.'),
    ('Rebaixamento', 'A maior queda acumulada desde um pico da curva. É o que '
     'se teria de aguentar sem desistir.'),
    ('Sequência de perdas', 'O maior número de operações perdedoras seguidas. '
     'É o número que decide se o plano é executável por uma pessoa.'),
    ('SQN', '<i>System Quality Number</i>: expectativa dividida pelo desvio, '
     'vezes a raiz do número de operações. Mede qualidade ajustada por '
     'amostra.'),
    ('t', 'Quantos erros padrão a expectativa está longe de zero. Acima de 2 é '
     'o mínimo convencional — e, quando é o melhor de N tentativas, precisa '
     'de validação independente.'),
    ('Mensurável', 'Uma configuração é mensurável quando as hipóteses '
     'pessimista e otimista devolvem o mesmo número. Nesse caso o resultado '
     'não depende de nenhuma suposição sobre a ordem dos eventos dentro da '
     'barra — que é o único ponto cego de um backtest feito sobre OHLC.'),
    ('Escolha fora da amostra', 'Escolher a configuração numa metade do '
     'histórico e medi-la na outra. É a única forma honesta de estimar o que '
     'esperar de uma busca em grid.'),
]


def escrever():
    with open(os.path.join(SAIDA, 'resumo.json'), encoding='utf-8') as f:
        r = json.load(f)
    with open(os.path.join(SAIDA, 'barras.json'), encoding='utf-8') as f:
        barras = f.read()

    D, I, P = r['dados'], r['indicador'], r['dados']['premissa']
    M, SW, EC = r['medias'], r['sweep_stop'], r['escolha_cruzada']
    VA, G, CM = r['validacao'], r['grid'], r['comparacao_medias']
    V = {v['nome']: v for v in r['variantes']}
    RNG = r['range_nominal']
    s2 = V['V2']['stats']
    mens = [g for g in G if g['mensuravel']]
    amb = r['ambiguidade']
    fora = EC['escolhe_2a_testa_1a']

    opcoes_var = '\n'.join(
        '<option value="%d"%s>%s · %s</option>'
        % (i, ' selected' if v['nome'] == 'V2' else '', v['nome'], v['rotulo'])
        for i, v in enumerate(r['variantes']))
    glos = '\n'.join('<dt>%s</dt><dd>%s</dd>' % (x, y) for x, y in GLOSSARIO)

    H = []
    a = H.append
    a('<!doctype html>')
    a('<html lang="pt-BR"><head>')
    a('<meta charset="utf-8">')
    a('<meta name="viewport" content="width=device-width,initial-scale=1">')
    a('<title>Médias + Esforço × Resultado em range — backtest</title>')
    a('<style>%s</style>' % CSS)
    a('</head><body>')
    a('<div class="env">')

    a('<header>')
    a('<p class="eyebrow">XAUUSD · range de %s ticks · risco:retorno 1:2</p>'
      % n(RNG))
    a('<h1>Seguir a tendência com médias<br>e um gatilho de esforço</h1>')
    a('<p class="sub">EMA e Hull de 21/42/72 como contexto · '
      '<code>Trigger_EsforcoResultado_Range.mq5</code> como gatilho · '
      'três formas de gestão<br>'
      '%s barras · %s a %s · %s pregões<br>'
      'Gerado em %s a partir de <code>%s</code></p>'
      % (n(D['barras']), D['inicio'][:10], D['fim'][:10], n(D['dias']),
         r['gerado_em'], r['arquivo']))
    a('</header>')

    a('<nav class="sumario">'
      '<a href="#s1">1 · Resposta curta</a><br>'
      '<a href="#s2">2 · Os dados e a premissa</a><br>'
      '<a href="#s3">3 · A estratégia em três peças</a><br>'
      '<a href="#s4">4 · EMA contra Hull</a><br>'
      '<a href="#s5">5 · Quais gestões dá para medir</a><br>'
      '<a href="#s6">6 · A varredura do stop</a><br>'
      '<a href="#s7">7 · O grid completo</a><br>'
      '<a href="#s8">8 · A escolha fora da amostra</a><br>'
      '<a href="#s9">9 · Validação e controles</a><br>'
      '<a href="#s10">10 · As variantes</a><br>'
      '<a href="#s11">11 · Operação a operação</a><br>'
      '<a href="#s12">12 · Restrições recomendadas</a><br>'
      '<a href="#s13">13 · Glossário</a><br>'
      '<a href="#s14">14 · Limitações</a>'
      '</nav>')

    # ---------------------------------------------------------------------- 1
    a('<h2 id="s1">1 · Resposta curta</h2>')
    a('<p class="lead">A ideia está certa na direção: o leque de médias '
      'realmente melhora o gatilho, e a EMA faz isso muito melhor que a Hull. '
      'Mas duas das três gestões pedidas não são mensuráveis neste tipo de '
      'arquivo, e a configuração campeã não sobrevive a uma escolha fora da '
      'amostra.</p>')
    a('<div class="cartoes">')
    for rot, val, nota, k in (
            ('EMA vence Hull', '%s / %s' % (n(CM['todos']['ema_vence']),
                                            n(CM['todos']['pares'])),
             'pares do grid, comparados um a um', 'pos'),
            ('Acerto da V2', pct(s2['acerto']),
             '%s operações, payoff %s' % (n(s2['operacoes']),
                                          n(s2['payoff'], 2)), ''),
            ('Expectativa', fmt(s2['expectativa_R'], 3) + ' R',
             'dentro da amostra (t = %s)' % fmt(s2['t_stat'], 2), 'pos'),
            ('Fora da amostra', fmt(fora['fora']['expectativa_R'], 3) + ' R',
             'é este o número em que acreditar', 'nul')):
        a('<div class="cartao"><div class="r">%s</div><div class="v %s">%s</div>'
          '<div class="n">%s</div></div>' % (rot, k, val, nota))
    a('</div>')

    a('<p><b>1 · A EMA vence a Hull.</b> Na mesma seleção e na mesma gestão, a '
      'EMA entrega %s R contra %s R da Hull. Comparando <b>par a par</b> — '
      'mesma largura de leque, mesmo modo, mesmo stop — a EMA vence em <b>%s '
      'dos %s pares</b>, com diferença mediana de %s R. É a conclusão mais '
      'sólida do estudo, porque é comparação estrutural e não um máximo '
      'escolhido.</p>'
      % (fmt(s2['expectativa_R'], 3),
         fmt(V['V7']['stats']['expectativa_R'], 3),
         n(CM['todos']['ema_vence']), n(CM['todos']['pares']),
         fmt(CM['todos']['diferenca_mediana'], 3)))
    a('<p><b>2 · O leque ajuda, e ajuda progressivamente.</b> Sem contexto de '
      'médias, %s R. Com o leque ordenado, %s R. Com o leque ordenado <i>e</i> '
      'aberto, %s R. Cada exigência acrescenta, na ordem esperada — que é o '
      'que se quer ver quando uma ideia está certa.</p>'
      % (fmt(V['V0']['stats']['expectativa_R'], 3),
         fmt(V['V1']['stats']['expectativa_R'], 3),
         fmt(s2['expectativa_R'], 3)))
    a('<p><b>3 · Duas das três gestões não são mensuráveis aqui.</b> As que '
      'movem o stop para a entrada dão os melhores números da tabela, e '
      'nenhum deles significa coisa alguma: dependem de uma ordem de eventos '
      'dentro da barra que o arquivo não registra. O intervalo da V5 vai de '
      '%s R a %s R — mais largo que o próprio resultado. O §5 explica por que, '
      'e mostra que a leitura literal de "breakeven na média da operação" é '
      'justamente a que escapa do problema.</p>'
      % (fmt(V['V5']['stats_piso']['expectativa_R'], 3),
         fmt(V['V5']['stats_otimista']['expectativa_R'], 3)))
    a('<p><b>4 · A campeã do grid não valida.</b> Escolhendo a melhor das %s '
      'configurações mensuráveis numa metade e medindo na outra, o resultado '
      'cai de %s R para <b>%s R</b> (t = %s).</p>'
      % (n(len(mens)), fmt(fora['dentro']['expectativa_R'], 3),
         fmt(fora['fora']['expectativa_R'], 3),
         fmt(fora['fora']['t_stat'], 2)))
    a('<div class="aviso"><p><b>A ressalva que decide tudo.</b> %s R sobre um '
      'stop de %s ticks são %s ticks por operação. Com 20 ticks de custo a V2 '
      'entrega %s R; com 40 ticks, %s R. Fora da amostra, com custo, não sobra '
      'nada. Isto é um estudo, não um sistema pronto.</p></div>'
      % (fmt(s2['expectativa_R'], 3), n(V['V2']['cfg']['stop_ticks']),
         fmt(s2['expectativa_ticks'], 1),
         fmt(V['V2']['custo']['20']['expectativa_R'], 3),
         fmt(V['V2']['custo']['40']['expectativa_R'], 3)))

    # ---------------------------------------------------------------------- 2
    a('<h2 id="s2">2 · Os dados e a premissa</h2>')
    a('<p>O indicador pressupõe range constante e a convenção de agressão do '
      'símbolo sintético do <code>Range_Claude_v1.mq5</code>. Aplicado onde '
      'elas não valem, ele não dá erro: desenha setas sem significado. As duas '
      'foram conferidas antes de medir qualquer coisa.</p>')
    a('<div class="rolagem"><table><tbody>')
    for rot, val in (('Range mediano', '%s ticks' % n(P['range_mediana'])),
                     ('Barras dentro de ±10% da mediana',
                      '<b>%s</b>' % pct(P['range_dentro_10pct'], 2)),
                     ('Desvio padrão do range',
                      '%s ticks' % n(P['range_desvio'], 2)),
                     ('Barras sem agressão vendedora',
                      pct(P['pct_vol_zero'], 2)),
                     ('Correlação entre as duas agressões',
                      n(P['correlacao_agressoes'], 3)),
                     ('Barras', '%s em %s pregões'
                      % (n(D['barras']), n(D['dias']))),
                     ('Período', '%s a %s' % (D['inicio'][:16], D['fim'][:16])),
                     ('Preço', '%s a %s'
                      % (n(D['preco_min'], 2), n(D['preco_max'], 2)))):
        a('<tr><td>%s</td><td>%s</td></tr>' % (rot, val))
    a('</tbody></table></div>')
    a('<p>Premissa confirmada nos dois pontos. O gatilho produz <b>%s sinais</b> '
      '(%s das barras, %s por pregão): %s de absorção e %s de divergência.</p>'
      % (n(I['total']), pct(I['pct_barras'], 2), n(I['sinais_por_dia'], 1),
         n(I['absorcao']), n(I['divergencia'])))

    # ---------------------------------------------------------------------- 3
    a('<h2 id="s3">3 · A estratégia, em três peças</h2>')
    a('<h3>O contexto — as médias</h3>')
    a('<p>As três médias (21/42/72) têm de estar <b>ordenadas</b> na direção do '
      'sinal: 21 &gt; 42 &gt; 72 para compra. E o leque tem de estar '
      '<b>aberto</b>: <code>|MA21 − MA72|</code> acima de um piso em ticks. '
      'Essa é a tradução numérica de "médias não emboladas" — leque estreito é '
      'consolidação, e é onde este tipo de entrada morre.</p>')
    a('<h3>O gatilho — o indicador</h3>')
    a('<p>O sinal do <code>Trigger_EsforcoResultado_Range.mq5</code>, portado '
      'linha a linha para <code>engine.py</code>. Ele é um sinal de '
      '<i>virada</i>: a barra N reverte a barra N−1 e se opera a favor de N. '
      'Combinado com o leque, deixa de ser reversão e vira <b>retomada</b> — '
      'só entra quando a virada aponta para o mesmo lado da tendência.</p>')
    a('<h3>A gestão — sempre 1:2</h3>')
    a('<div class="rolagem"><table><thead><tr><th>modo</th><th>o que faz</th>'
      '<th>desfechos possíveis</th></tr></thead><tbody>'
      '<tr><td><code>fixo</code></td><td>stop em −S, alvo em +2S, nada se move</td>'
      '<td>−1R ou +2R</td></tr>'
      '<tr><td><code>parcial</code></td><td>a +S vende 50% e leva o stop para a '
      '<b>entrada</b></td><td>−1R, +0,5R, +1,5R</td></tr>'
      '<tr><td><code>parcial_op</code></td><td>a +S vende 50% e o stop '
      '<b>fica onde está</b></td><td>−1R, 0, +1,5R</td></tr>'
      '<tr><td><code>breakeven</code></td><td>a +S o stop vai para a '
      '<b>entrada</b>, sem parcial</td><td>−1R, 0, +2R</td></tr>'
      '</tbody></table></div>')
    a('<div class="destaque"><p><b>Por que existem dois modos com parcial.</b> '
      '"Parcial que ativa o breakeven na média da operação" admite duas '
      'leituras, e a diferença entre elas é aritmética. Com metade realizada '
      'em +S, o resultado da operação inteira num stop em −S é</p>'
      '<pre><code>0,5 × (+S)  +  0,5 × (−S)  =  0</code></pre>'
      '<p>ou seja: <b>o breakeven da operação já está no stop inicial</b>. '
      'Levar o stop para a entrada não é breakeven — é travar +0,5R. Os dois '
      'estão implementados e publicados porque a diferença é material.</p>'
      '</div>')

    # ---------------------------------------------------------------------- 4
    a('<h2 id="s4">4 · As médias como contexto: EMA contra Hull</h2>')
    a('<p>Antes de qualquer operação, vale olhar o que cada família faz com '
      'este gráfico.</p>')
    a(tab_medias(r))
    a('<p>A Hull faz exatamente o que promete: persegue o preço de perto e '
      'vira antes. O preço disso é trocar de lado <b>%s vezes</b> contra %s da '
      'EMA — %s trocas a mais no mesmo histórico. Cada troca é uma tendência '
      'que a Hull declarou e desfez.</p>'
      % (n(M['hull']['trocas_de_lado']), n(M['ema']['trocas_de_lado']),
         n(M['hull']['trocas_de_lado'] - M['ema']['trocas_de_lado'])))
    a('<p>E o resultado operacional segue a estrutura. Par a par, a EMA vence '
      'em %s dos %s pares (entre os mensuráveis, %s de %s), com diferença '
      'mediana de %s R. <b>Sensibilidade a virada não é a mesma coisa que '
      'leitura de tendência</b> — para esta estratégia, a média mais lenta é a '
      'que serve.</p>'
      % (n(CM['todos']['ema_vence']), n(CM['todos']['pares']),
         n(CM['mensuraveis']['ema_vence']), n(CM['mensuraveis']['pares']),
         fmt(CM['todos']['diferenca_mediana'], 3)))
    if CM['excecoes']:
        a('<p>As %s exceções em que a Hull vence estão quase todas em stops '
          'grandes, onde as duas famílias já rendem perto de zero:</p>'
          % n(len(CM['excecoes'])))
        a('<div class="rolagem"><table><thead><tr><th>leque</th><th>modo</th>'
          '<th>stop</th><th>EMA</th><th>Hull</th></tr></thead><tbody>')
        for e in CM['excecoes']:
            a('<tr><td>≥%s t</td><td><code>%s</code></td><td>%s t</td>'
              '<td class="%s">%s R</td><td class="%s">%s R</td></tr>'
              % (n(e['leque_min']), e['modo'], n(e['stop_ticks']),
                 cls(e['ema']), fmt(e['ema'], 3),
                 cls(e['hull']), fmt(e['hull'], 3)))
        a('</tbody></table></div>')

    # ---------------------------------------------------------------------- 5
    a('<h2 id="s5">5 · Quais gestões este gráfico consegue medir</h2>')
    a('<p>Esta é a seção que muda a resposta à pergunta original.</p>')
    a('<p>Num gráfico de range vale uma regra geométrica exata: a barra '
      'percorre <b>no máximo %s ticks</b>, logo não consegue tocar dois níveis '
      'separados por mais que isso. Duas consequências.</p>' % n(RNG))
    a('<div class="ok"><p><b>[1] Stop e alvo.</b> Eles distam '
      '<code>S + 2S = 3S</code>. Se <code>3S &gt; %s</code>, nunca são tocados '
      'na mesma barra e a hipótese pessimista/otimista deixa de importar. O '
      'limite é exato:</p>'
      '<pre><code>S &gt; range / 3 = %s ticks</code></pre></div>'
      % (n(RNG), n(SW['limite_teorico'], 1)))
    a('<div class="aviso"><p><b>[2] O gatilho de 1R, nos modos que movem o '
      'stop para a entrada.</b> Há um segundo instante que o arquivo não data: '
      'a barra que arma o gatilho. Ela <b>abre exatamente no preço de '
      'entrada</b> — a entrada é o fechamento da barra de sinal — então '
      'qualquer pavio contrário faz o preço "voltar ao breakeven" no papel. '
      'Como a barra percorre %s ticks garantidos, isso acontece em '
      'praticamente toda barra que arma o gatilho. Só para de acontecer '
      'quando o gatilho fica a mais de um range inteiro da entrada.</p></div>'
      % n(RNG))
    a('<p>A tabela mede a largura do intervalo (piso a teto) de cada '
      'combinação. <b>Largura zero é a prova de que o número não depende de '
      'convenção nenhuma.</b></p>')
    a(tab_ambiguidade(r))
    a('<p>Leia de baixo para cima. Com stop de 450 ticks — mais que um range '
      'inteiro — <b>os quatro modos ficam mensuráveis</b>, exatamente como a '
      'geometria previa. E aí a vantagem já evaporou: os quatro convergem para '
      'perto de %s R. Com stop de 194, ao contrário, os dois modos que movem o '
      'stop para a entrada têm intervalos de %s R e %s R de largura — o número '
      'deles é indeterminado. E são justamente eles que aparecem no topo de '
      'qualquer ranking.</p>'
      % (fmt(sorted(x['padrao'] for x in amb if x['stop_ticks'] == 450.0)[2], 2),
         n([x['largura'] for x in amb
            if x['stop_ticks'] == 194.0 and x['modo'] == 'parcial'][0], 3),
         n([x['largura'] for x in amb
            if x['stop_ticks'] == 194.0 and x['modo'] == 'breakeven'][0], 3)))
    a('<div class="destaque"><p><b>Conclusão de método.</b> Dos três modos '
      'pedidos, o <code>fixo</code> e o <code>parcial_op</code> — a leitura '
      'literal de "breakeven na média da operação" — são mensuráveis neste '
      'gráfico. O <code>parcial</code> com stop na entrada e o '
      '<code>breakeven</code> puro não são: não porque a estratégia seja ruim, '
      'mas porque este histórico não contém a informação necessária para '
      'julgá-la. Para medi-los seria preciso um arquivo de ticks, não de '
      'barras.</p></div>')

    # ---------------------------------------------------------------------- 6
    a('<h2 id="s6">6 · A varredura do stop</h2>')
    a('<p>Com a gestão fixa e a seleção da V2, variando só o tamanho do stop '
      '(o alvo acompanha, sempre 2×).</p>')
    a(tab_sweep(r))
    a('<p><b>O limite geométrico aparece na régua.</b> A largura do intervalo '
      'cai de %s em S=120 para exatamente <b>zero</b> em S=130. O limite '
      'teórico era %s. A previsão e a medição batem.</p>'
      % (n([g['largura'] for g in SW['linhas'] if g['stop_ticks'] == 120.0][0], 3),
         n(SW['limite_teorico'], 1)))
    a('<p><b>Há platô, não pico.</b> De 130 a 220 ticks a expectativa desce '
      'suavemente de %s para %s. Um parâmetro que só funcionasse num valor '
      'exato seria ajuste; não é o caso. <b>Mas as duas metades não se '
      'parecem</b>: em toda linha da tabela a 1ª fica perto de zero e a 2ª '
      'carrega o resultado. Isso não é propriedade do parâmetro — é '
      'propriedade do período.</p>'
      % (fmt([g['expectativa_R'] for g in SW['linhas']
              if g['stop_ticks'] == 130.0][0], 3),
         fmt([g['expectativa_R'] for g in SW['linhas']
              if g['stop_ticks'] == 220.0][0], 3)))

    # ---------------------------------------------------------------------- 7
    a('<h2 id="s7">7 · O grid completo</h2>')
    a('<p><b>%s configurações medidas</b>: 2 famílias de média × 4 larguras de '
      'leque × 4 modos de gestão × 5 tamanhos de stop. Publicar o grid inteiro '
      'é o que permite ler o melhor número como o máximo de %s tentativas.</p>'
      % (n(len(G)), n(len(G))))
    a('<h3>As dez melhores por expectativa</h3>')
    a(tab_grid(r, False, 10))
    a('<p>Das %s configurações, apenas <b>%s são mensuráveis</b> sem depender '
      'de convenção. E o topo do ranking geral é dominado justamente pelas '
      'indeterminadas.</p>' % (n(len(G)), n(len(mens))))
    a('<h3>As dez melhores entre as mensuráveis</h3>')
    a(tab_grid(r, True, 10))
    a('<p>Note que as primeiras posições são todas EMA.</p>')

    # ---------------------------------------------------------------------- 8
    a('<h2 id="s8">8 · A escolha fora da amostra — o teste que reprova</h2>')
    a('<p>Com %s configurações mensuráveis, o melhor número da tabela é o '
      'máximo de %s tentativas e não serve de estimativa. A única leitura '
      'honesta é escolher onde não se vai medir, e medir onde não se '
      'escolheu.</p>' % (n(len(mens)), n(len(mens))))
    a('<div class="rolagem"><table><thead><tr><th>escolhido em</th>'
      '<th>configuração escolhida</th><th>dentro da amostra</th>'
      '<th>fora da amostra</th><th>mediana das candidatas fora</th>'
      '</tr></thead><tbody>')
    for k, rot in (('escolhe_1a_testa_2a', '1ª metade'),
                   ('escolhe_2a_testa_1a', '2ª metade')):
        e = EC[k]['escolhida']
        a('<tr><td>%s</td><td>%s, leque ≥%s, <code>%s</code>, stop %s t</td>'
          '<td class="%s">%s R (t %s)</td>'
          '<td class="%s"><b>%s R</b> (t %s, n=%s)</td>'
          '<td class="%s">%s R</td></tr>'
          % (rot, e['ma_tipo'].upper(), n(e['leque_min']), e['modo'],
             n(e['stop_ticks']),
             cls(EC[k]['dentro']['expectativa_R']),
             fmt(EC[k]['dentro']['expectativa_R'], 3),
             fmt(EC[k]['dentro']['t_stat'], 2),
             cls(EC[k]['fora']['expectativa_R']),
             fmt(EC[k]['fora']['expectativa_R'], 3),
             fmt(EC[k]['fora']['t_stat'], 2), n(EC[k]['fora']['n']),
             cls(EC[k]['mediana_fora']), fmt(EC[k]['mediana_fora'], 3)))
    a('</tbody></table></div>')
    a('<p><b>Reprovado.</b> Escolhendo na 2ª metade, a campeã mede %s R lá '
      'dentro e entrega %s R na 1ª — praticamente nada, com t = %s. Escolhendo '
      'na 1ª metade, a campeã entrega %s R na 2ª, <i>abaixo</i> da mediana das '
      'candidatas (%s R): a seleção foi pior que escolher ao acaso entre as '
      'concorrentes.</p>'
      % (fmt(fora['dentro']['expectativa_R'], 3),
         fmt(fora['fora']['expectativa_R'], 3),
         fmt(fora['fora']['t_stat'], 2),
         fmt(EC['escolhe_1a_testa_2a']['fora']['expectativa_R'], 3),
         fmt(EC['escolhe_1a_testa_2a']['mediana_fora'], 3)))
    a('<p>É por isso que este relatório recomenda a V2 e não a campeã do grid. '
      'A V2 não foi escolhida por ser a melhor: foi escolhida por ser a mais '
      'simples que respeita a geometria — leque aberto, gestão fixa, stop em '
      'meio range. O número que se deve esperar dela é o de <b>fora</b> da '
      'amostra.</p>')

    # ---------------------------------------------------------------------- 9
    a('<h2 id="s9">9 · Validação e controles</h2>')
    a(tab_validacao(r))
    a('<div class="aviso"><p><b>O resultado está concentrado no fim do '
      'histórico.</b> Os dois primeiros terços rendem %s R e %s R — '
      'indistinguíveis de zero. O terceiro rende %s R e responde sozinho por '
      'quase todo o resultado. Esse é o padrão de uma estratégia que funcionou '
      'num regime de mercado, não de uma que funciona.</p></div>'
      % (fmt(VA['tercos'][0]['expectativa_R'], 3),
         fmt(VA['tercos'][1]['expectativa_R'], 3),
         fmt(VA['tercos'][2]['expectativa_R'], 3)))
    a('<p>Os controles, por outro lado, se comportam como deveriam:</p>')
    a(tab_controles(r))
    a('<p>O invertido é claramente negativo (%s R, t = %s): a vantagem é de '
      '<b>direção</b>, e não um artefato de contabilidade. A direção sorteada '
      'nas mesmas barras dá %s R — a gestão 1:2 sozinha não produz vantagem '
      'nenhuma, o que existe vem do gatilho. E operar <i>contra</i> o leque '
      'rende %s R, contra %s R a favor: o contexto das médias está do lado '
      'certo.</p>'
      % (fmt(VA['controles']['invertido']['expectativa_R'], 3),
         fmt(VA['controles']['invertido']['t_stat'], 2),
         fmt(VA['controles']['direcao_sorteada']['expectativa_R'], 3),
         fmt(VA['controles']['leque_contra']['expectativa_R'], 3),
         fmt(s2['expectativa_R'], 3)))
    a('<div class="painel"><h4>curva de resultado acumulado da variante '
      'selecionada no §11</h4><canvas id="cvCurva"></canvas></div>')

    # --------------------------------------------------------------------- 10
    a('<h2 id="s10">10 · As variantes</h2>')
    a(tab_variantes(r))
    for v in r['variantes']:
        a('<p><b>%s · %s</b> — %s</p>' % (v['nome'], v['rotulo'], v['descricao']))
    a('<h3>Estatística completa das variantes mensuráveis</h3>')
    a(tab_completa(r))
    a('<h3>Sensibilidade</h3>')
    a('<p>Expectativa em R por operação, sob cada hipótese e com cada custo. '
      'As colunas <i>piso</i> e <i>teto</i> coincidem nas variantes '
      'mensuráveis e se afastam nas outras — é a propriedade do §5 aparecendo '
      'na tabela.</p>')
    a(tab_sensibilidade(r))

    # --------------------------------------------------------------------- 11
    a('<h2 id="s11">11 · Operação a operação</h2>')
    a('<p>O painel de cima traz o preço, as três médias da variante '
      'selecionada e os níveis da operação. O de baixo traz o que o indicador '
      'lê: a <b>barra cinza</b> é o esforço (agressão somada) e a <b>barra '
      'colorida</b> é o delta (agressão líquida), cada um com a sua escala — '
      'juntos na mesma escala o delta desaparece.</p>')
    a('<p>As setas repetem as do <code>.mq5</code>: verde e vermelha para '
      'absorção, azul para divergência. A seta cheia é o sinal da operação em '
      'exibição. Use as setas do teclado para navegar.</p>')
    a('<div class="painel">')
    a('<div class="barras">')
    a('<label>variante <select id="selVar">%s</select></label>' % opcoes_var)
    a('<label>desfecho <select id="selMot"></select></label>')
    a('<label>lado <select id="selLado">'
      '<option value="*">ambos</option><option value="long">compra</option>'
      '<option value="short">venda</option></select></label>')
    a('<span style="display:flex;gap:8px;align-items:center">'
      '<button id="btPrev">←</button><button id="btProx">→</button>'
      '<span class="conta" id="conta"></span></span>')
    a('</div>')
    a('<p class="conta" id="descVar" style="margin:0 0 12px"></p>')
    a('<canvas id="cvKline"></canvas>')
    a('<div class="ficha" id="ficha"></div>')
    a('<div class="legenda">'
      '<span><i style="background:#f59f00"></i>MA 21</span>'
      '<span><i style="background:#4dabf7"></i>MA 42</span>'
      '<span><i style="background:#9775fa"></i>MA 72</span>'
      '<span><i style="background:#868e96"></i>esforço</span>'
      '<span><i style="background:#0f9d76"></i>delta comprador</span>'
      '<span><i style="background:#e03131"></i>delta vendedor</span>'
      '</div>')
    a('</div>')

    # --------------------------------------------------------------------- 12
    a('<h2 id="s12">12 · Restrições recomendadas</h2>')
    a('<ol>')
    a('<li><b>Usar EMA, não Hull.</b> A conclusão mais sólida do estudo, e a '
      'única que vale independentemente de qualquer escolha de parâmetro.</li>')
    a('<li><b>Exigir o leque ordenado e aberto</b> (≥ %s ticks entre a EMA21 e '
      'a EMA72). Cada exigência acrescentou, na ordem esperada.</li>'
      % n(V['V2']['cfg']['leque_min']))
    a('<li><b>Preferir a gestão fixa, ou a parcial com breakeven da '
      'operação.</b> São as duas mensuráveis. As outras duas podem até ser '
      'melhores na prática — este histórico não permite saber.</li>')
    a('<li><b>Stop entre 130 e 220 ticks.</b> Abaixo de %s o resultado deixa '
      'de ser mensurável; acima de 250 a vantagem some.</li>'
      % n(SW['limite_teorico'], 0))
    a('<li><b>Não operar contra o leque.</b> Rende %s R contra %s R a '
      'favor.</li>'
      % (fmt(VA['controles']['leque_contra']['expectativa_R'], 3),
         fmt(s2['expectativa_R'], 3)))
    a('<li><b>Esperar %s R, não %s R.</b> O primeiro é o número fora da '
      'amostra; o segundo é o de dentro.</li>'
      % (fmt(fora['fora']['expectativa_R'], 3), fmt(s2['expectativa_R'], 3)))
    a('<li><b>Tratar o custo como a restrição dominante.</b></li>')
    a('</ol>')

    # --------------------------------------------------------------------- 13
    a('<h2 id="s13">13 · Glossário</h2>')
    a('<dl class="glos">%s</dl>' % glos)

    # --------------------------------------------------------------------- 14
    a('<h2 id="s14">14 · Limitações</h2>')
    a('<ul>')
    a('<li><b>O resultado vive no último terço do histórico.</b> Os dois '
      'primeiros terços são indistinguíveis de zero. É a limitação mais séria, '
      'e nenhuma outra a compensa.</li>')
    a('<li><b>A escolha de configuração não validou fora da amostra</b> (§8). '
      'O grid descreve o passado; não mostrou capacidade de prever.</li>')
    a('<li><b>Duas das três gestões pedidas não são mensuráveis</b> neste tipo '
      'de arquivo (§5). Para julgá-las é preciso histórico de ticks.</li>')
    a('<li><b>Uma amostra, um ativo, %s pregões.</b> Nenhuma validação interna '
      'substitui um segundo histórico.</li>' % n(D['dias']))
    a('<li><b>Slippage não está modelado.</b> A entrada é a mercado no '
      'fechamento de uma barra de range — um instante de movimento.</li>')
    a('<li><b>A convenção de agressão é premissa, não fato medido.</b></li>')
    a('<li><b>O leque de %s ticks foi escolhido olhando os dados.</b> Fica num '
      'platô e a progressão V0→V1→V2 é monotônica, o que ajuda — mas continua '
      'sendo um número escolhido depois de ver o resultado.</li>'
      % n(V['V2']['cfg']['leque_min']))
    a('</ul>')

    a('<footer>Gerado por <code>relatorio.py</code> a partir de '
      '<code>saida/resumo.json</code> e <code>saida/barras.json</code> (%s). '
      'Para reproduzir: <code>python rodar.py &amp;&amp; python relatorio.py'
      '</code>.</footer>' % r['gerado_em'])
    a('</div>')
    a('<div class="dica" id="dica"></div>')
    a('<script>window.__RESUMO__=%s;</script>'
      % json.dumps(r, ensure_ascii=False, separators=(',', ':')))
    a('<script>window.__BARRAS__=%s;</script>' % barras)
    a('<script>%s</script>' % JS)
    a('</body></html>')

    caminho = os.path.join(BASE, 'relatorio.html')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write('\n'.join(H))
    print('relatorio.html gravado (%s KB).'
          % n(os.path.getsize(caminho) / 1024))


if __name__ == '__main__':
    escrever()
