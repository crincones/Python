# -*- coding: utf-8 -*-
"""
saida/resumo.json + saida/barras.json -> relatorio.html

Um arquivo so, sem internet e sem servidor. O navegador de operacoes desenha
os candles e, embaixo, o painel de AGRESSAO -- que e o que o indicador
realmente le. Sem esse painel o leitor ve a barra virar e nao ve por que.
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')


# --------------------------------------------------------------------------
def n(x, casas=0):
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
  --tinta:#1b1f24; --tinta2:#5b6570; --fundo:#fbfaf7; --papel:#ffffff;
  --linha:#e2ddd4; --realce:#8a6a2f; --alta:#1a7f5a; --baixa:#b3453a;
  --grade:#efece5; --caixa:#f5f2ec; --azul:#3d72b8;
}
@media (prefers-color-scheme: dark){
  :root{
    --tinta:#e8e6e1; --tinta2:#9aa2ab; --fundo:#14171a; --papel:#1b1f23;
    --linha:#2e343a; --realce:#d9ae5e; --alta:#3fbb8a; --baixa:#e0685c;
    --grade:#232930; --caixa:#20262c; --azul:#6fa3e0;
  }
}
*{box-sizing:border-box}
body{margin:0;background:var(--fundo);color:var(--tinta);
  font:16px/1.62 Georgia,'Times New Roman',serif;
  -webkit-font-smoothing:antialiased}
.env{max-width:940px;margin:0 auto;padding:0 22px 90px}
header{padding:64px 0 30px;border-bottom:2px solid var(--tinta)}
h1{font-size:34px;line-height:1.18;margin:0 0 10px;letter-spacing:-.4px}
.sub{color:var(--tinta2);font-size:15px;margin:0}
h2{font-size:24px;margin:52px 0 6px;letter-spacing:-.2px;
   padding-top:16px;border-top:1px solid var(--linha)}
h3{font-size:18px;margin:30px 0 4px}
h4{font-size:15px;margin:22px 0 2px;text-transform:uppercase;
   letter-spacing:.08em;color:var(--tinta2);font-family:system-ui,sans-serif}
p{margin:12px 0}
a{color:var(--realce)}
code{font:13px/1.5 ui-monospace,'Cascadia Mono',Consolas,monospace;
  background:var(--caixa);padding:1px 5px;border-radius:3px}
.lead{font-size:19px;line-height:1.55}
.destaque{background:var(--caixa);border-left:3px solid var(--realce);
  padding:14px 18px;margin:22px 0;border-radius:0 5px 5px 0}
.destaque p:first-child{margin-top:0}.destaque p:last-child{margin-bottom:0}
table{border-collapse:collapse;width:100%;margin:18px 0;
  font:13.5px/1.45 system-ui,-apple-system,sans-serif}
th,td{padding:7px 10px;text-align:right;border-bottom:1px solid var(--linha)}
th:first-child,td:first-child{text-align:left}
thead th{border-bottom:1.5px solid var(--tinta);font-weight:600;
  color:var(--tinta2);text-transform:uppercase;font-size:11px;
  letter-spacing:.06em}
tbody tr:hover{background:var(--caixa)}
tr.realce td{background:color-mix(in srgb,var(--realce) 10%,transparent)}
tr.risca td{opacity:.55}
.pos{color:var(--alta)}.neg{color:var(--baixa)}.nul{color:var(--tinta2)}
.num{font-variant-numeric:tabular-nums}
.rolagem{overflow-x:auto;margin:18px 0}
.rolagem table{margin:0;min-width:600px}
.cartoes{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
  gap:12px;margin:22px 0}
.cartao{background:var(--papel);border:1px solid var(--linha);
  border-radius:7px;padding:13px 15px}
.cartao .r{font:11px/1.3 system-ui,sans-serif;color:var(--tinta2);
  text-transform:uppercase;letter-spacing:.06em}
.cartao .v{font:26px/1.25 system-ui,sans-serif;font-variant-numeric:tabular-nums;
  margin-top:3px;font-weight:600}
.cartao .n{font:12px/1.4 system-ui,sans-serif;color:var(--tinta2);margin-top:2px}
.painel{background:var(--papel);border:1px solid var(--linha);
  border-radius:9px;padding:16px;margin:24px 0}
.barras{display:flex;gap:14px;flex-wrap:wrap;align-items:center;
  font:13px/1.4 system-ui,sans-serif;margin-bottom:12px}
select,button{font:13px system-ui,sans-serif;padding:6px 10px;
  border:1px solid var(--linha);border-radius:6px;background:var(--papel);
  color:var(--tinta);cursor:pointer}
button:hover{border-color:var(--realce)}
button:disabled{opacity:.4;cursor:default}
canvas{display:block;width:100%;border-radius:6px}
.dica{position:fixed;pointer-events:none;visibility:hidden;z-index:9;
  background:var(--papel);border:1px solid var(--linha);border-radius:6px;
  padding:6px 9px;font:12px/1.5 system-ui,sans-serif;
  box-shadow:0 3px 12px rgba(0,0,0,.14);max-width:340px}
.legenda{font:12px/1.5 system-ui,sans-serif;color:var(--tinta2);
  display:flex;gap:16px;flex-wrap:wrap;margin-top:9px}
.legenda i{display:inline-block;width:16px;height:2px;vertical-align:middle;
  margin-right:5px}
.ficha{display:grid;grid-template-columns:repeat(auto-fit,minmax(115px,1fr));
  gap:10px;font:13px/1.4 system-ui,sans-serif;margin-top:12px}
.ficha div span{display:block;color:var(--tinta2);font-size:11px;
  text-transform:uppercase;letter-spacing:.05em}
.ficha b{font-variant-numeric:tabular-nums;font-weight:600;font-size:15px}
.nav{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.conta{font:12px system-ui,sans-serif;color:var(--tinta2);
  font-variant-numeric:tabular-nums}
dl.glos{margin:18px 0}
dl.glos dt{font-weight:700;margin-top:16px}
dl.glos dd{margin:2px 0 0;color:var(--tinta)}
.sumario{font:14px/1.9 system-ui,sans-serif;columns:2;column-gap:34px;
  margin:24px 0 0;padding:16px 0;border-top:1px solid var(--linha);
  border-bottom:1px solid var(--linha)}
.sumario a{text-decoration:none;color:var(--tinta)}
.sumario a:hover{color:var(--realce)}
.aviso{border:1px solid var(--baixa);border-radius:7px;padding:14px 18px;
  margin:24px 0;background:color-mix(in srgb,var(--baixa) 7%,transparent)}
.aviso p:first-child{margin-top:0}.aviso p:last-child{margin-bottom:0}
.ok{border:1px solid var(--alta);border-radius:7px;padding:14px 18px;
  margin:24px 0;background:color-mix(in srgb,var(--alta) 7%,transparent)}
.ok p:first-child{margin-top:0}.ok p:last-child{margin-bottom:0}
footer{margin-top:60px;padding-top:20px;border-top:1px solid var(--linha);
  font:13px/1.6 system-ui,sans-serif;color:var(--tinta2)}
@media(max-width:640px){.sumario{columns:1}h1{font-size:27px}
  .env{padding:0 15px 60px}}
"""

JS = r"""
(function(){
'use strict';
var R = window.__RESUMO__, B = window.__BARRAS__;
var TICK = 0.01, RNG = R.range_nominal;

/* ---- reconstroi as barras ---------------------------------------------- */
var N = B.c.length;
var close = new Float64Array(N), open = new Float64Array(N),
    high = new Float64Array(N), low = new Float64Array(N),
    tempo = new Float64Array(N);
var acc = B.t0;
for (var i=0;i<N;i++){
  var c = B.c[i];
  close[i] = c*TICK; open[i] = (c+B.o[i])*TICK;
  high[i] = (c+B.h[i])*TICK; low[i] = (c+B.l[i])*TICK;
  acc += (i? B.dt[i] : 0); tempo[i] = acc;
}
/* agressao: compradora e vendedora, e o delta */
var agrC = B.cv, agrV = B.vv;
/* mapa esparso das setas do indicador */
var marca = {};
B.sinais.forEach(function(p){ marca[p[0]] = p[1]; });

/* ---- utilitarios ------------------------------------------------------- */
function num(x,d){ d=d||0;
  return x.toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d}); }
function sgn(x,d){ return (x>0?'+':'') + num(x,d||0); }
function classe(x){ return x>0?'pos':(x<0?'neg':'nul'); }
function data(ts){
  var d = new Date(ts*1000);
  function p(x){ return (x<10?'0':'')+x; }
  return d.getUTCFullYear()+'-'+p(d.getUTCMonth()+1)+'-'+p(d.getUTCDate())+
    ' '+p(d.getUTCHours())+':'+p(d.getUTCMinutes());
}
function cor(v){ return getComputedStyle(document.documentElement)
  .getPropertyValue(v).trim(); }

/* ---- o grafico: candles em cima, agressao embaixo ---------------------- */
function Kline(cv, dica){
  this.cv = cv; this.dica = dica; this.ctx = cv.getContext('2d');
  this.win = null; this.op = null; this.cfg = null;
  var self = this;
  cv.addEventListener('mousemove', function(e){ self.hover(e); });
  cv.addEventListener('mouseleave', function(){ dica.style.visibility='hidden'; });
  window.addEventListener('resize', function(){ self.pinta(); });
}
Kline.prototype.mostra = function(op, cfg){
  this.op = op; this.cfg = cfg;
  var a = Math.max(0, op.sinal_i - 22);
  var fim = op.saida_i >= 0 ? op.saida_i : op.sinal_i + 8;
  var b = Math.min(N-1, fim + 8);
  if (b - a < 38) b = Math.min(N-1, a + 38);
  this.win = [a, b];
  this.pinta();
};
Kline.prototype.geo = function(){
  var cv = this.cv, w = cv.clientWidth, h = 500;
  var dpr = window.devicePixelRatio || 1;
  if (cv.width !== Math.round(w*dpr) || cv.height !== Math.round(h*dpr)){
    cv.width = Math.round(w*dpr); cv.height = Math.round(h*dpr);
    cv.style.height = h+'px';
  }
  this.ctx.setTransform(dpr,0,0,dpr,0,0);
  /* hp = altura do painel de preco; ha = altura do painel de agressao */
  return {w:w, h:h, ml:8, mr:74, mt:12, mb:34, hp:300, gap:18};
};
Kline.prototype.escala = function(){
  var a=this.win[0], b=this.win[1], op=this.op, cfg=this.cfg;
  var lo=Infinity, hi=-Infinity;
  for (var i=a;i<=b;i++){
    if (low[i]<lo) lo=low[i]; if (high[i]>hi) hi=high[i];
  }
  var s = op.lado==='long'?1:-1;
  [op.entrada - s*cfg.stop_ticks*TICK,
   op.entrada + s*cfg.parcial_ticks*TICK,
   op.entrada + s*cfg.alvo_ticks*TICK,
   op.preco_ordem, op.entrada].forEach(function(p){
     if (p<lo) lo=p; if (p>hi) hi=p; });
  var pad = (hi-lo)*0.06 || 1;
  return {lo:lo-pad, hi:hi+pad};
};
Kline.prototype.pinta = function(){
  if (!this.op) return;
  var g = this.geo(), ctx = this.ctx, a=this.win[0], b=this.win[1];
  var op = this.op, cfg = this.cfg, es = this.escala();
  var cnt = b-a+1;
  var pw = (g.w - g.ml - g.mr) / cnt;
  var cw = Math.max(1.4, Math.min(pw*0.66, 13));
  function X(i){ return g.ml + (i-a+0.5)*pw; }
  function Y(p){ return g.mt + (es.hi-p)/(es.hi-es.lo)*(g.hp-g.mt); }
  this.X = X; this.Y = Y; this.pw = pw; this.g = g;

  ctx.clearRect(0,0,g.w,g.h);
  ctx.fillStyle = cor('--papel'); ctx.fillRect(0,0,g.w,g.h);

  /* grade e escala de preco */
  var passo = Math.pow(10, Math.floor(Math.log10((es.hi-es.lo)/5)));
  [1,2,2.5,5,10].some(function(m){ if ((es.hi-es.lo)/(passo*m) <= 7){ passo*=m; return true; } });
  ctx.strokeStyle = cor('--grade'); ctx.lineWidth = 1;
  ctx.fillStyle = cor('--tinta2');
  ctx.font = '11px system-ui,sans-serif'; ctx.textAlign='left';
  for (var p = Math.ceil(es.lo/passo)*passo; p<=es.hi; p+=passo){
    var y = Math.round(Y(p))+0.5;
    ctx.beginPath(); ctx.moveTo(g.ml,y); ctx.lineTo(g.w-g.mr,y); ctx.stroke();
    ctx.fillText(num(p,2), g.w-g.mr+6, y+3.5);
  }

  /* faixa da operacao */
  var i0 = op.sinal_i+1, i1 = op.saida_i>=0?op.saida_i:i0;
  ctx.fillStyle = cor('--realce'); ctx.globalAlpha = 0.10;
  ctx.fillRect(X(i0)-pw/2, g.mt, (i1-i0+1)*pw, g.hp-g.mt);
  ctx.globalAlpha = 1;

  /* linhas da operacao */
  var s = op.lado==='long'?1:-1;
  var linhas = [
    [op.entrada, cor('--tinta'), 'entrada ' + num(op.entrada,2), []],
    [op.entrada - s*cfg.stop_ticks*TICK, cor('--baixa'),
     'stop −' + num(cfg.stop_ticks) + 't', [5,4]],
    [op.entrada + s*cfg.parcial_ticks*TICK, cor('--alta'),
     (cfg.parcial_frac < 1 ? 'parcial +' : 'alvo +') +
       num(cfg.parcial_ticks) + 't', [5,4]]
  ];
  if (op.preco_ordem !== op.entrada)
    linhas.push([op.preco_ordem, cor('--realce'),
                 'ordem ' + num(op.preco_ordem,2), [2,3]]);
  if (cfg.parcial_frac < 1)
    linhas.push([op.entrada + s*cfg.alvo_ticks*TICK, cor('--alta'),
                 'alvo +' + num(cfg.alvo_ticks) + 't', [5,4]]);
  ctx.font = '10.5px system-ui,sans-serif'; ctx.textAlign='left';
  var usados = [];
  linhas.sort(function(p,q){ return Y(p[0]) - Y(q[0]); }).forEach(function(L){
    var y = Math.round(Y(L[0]))+0.5;
    if (y < g.mt+6 || y > g.hp-6) return;
    ctx.save(); ctx.setLineDash(L[3]); ctx.strokeStyle = L[1];
    ctx.lineWidth = 1.2; ctx.beginPath();
    ctx.moveTo(g.ml,y); ctx.lineTo(g.w-g.mr,y); ctx.stroke(); ctx.restore();
    /* a etiqueta desce ate achar espaco livre: sem isto, stop, entrada e
       alvo -- separados por 194 ticks -- imprimem uns por cima dos outros */
    var ye = y - 2;
    usados.forEach(function(u){ if (Math.abs(ye-u) < 12) ye = u + 12; });
    usados.push(ye);
    var lg = ctx.measureText(L[2]).width;
    ctx.fillStyle = cor('--papel'); ctx.fillRect(g.ml+2, ye-9, lg+7, 12);
    ctx.fillStyle = L[1]; ctx.fillText(L[2], g.ml+5, ye);
  });

  /* candles */
  for (var i=a;i<=b;i++){
    var sobe = close[i] >= open[i];
    var c = sobe ? cor('--alta') : cor('--baixa');
    var x = X(i);
    ctx.strokeStyle = c; ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(Math.round(x)+0.5, Y(high[i]));
    ctx.lineTo(Math.round(x)+0.5, Y(low[i])); ctx.stroke();
    var yo = Y(open[i]), yc = Y(close[i]);
    ctx.fillStyle = c;
    ctx.fillRect(x-cw/2, Math.min(yo,yc), cw, Math.max(1, Math.abs(yc-yo)));
  }

  /* setas do indicador, como no .mq5: verde/vermelho absorcao, azul divergencia */
  for (var i=a;i<=b;i++){
    var m = marca[i]; if (!m) continue;
    var alta = m > 0, div = Math.abs(m) === 2;
    var cc = div ? cor('--azul') : (alta ? cor('--alta') : cor('--baixa'));
    var yy = alta ? Y(low[i]) + 11 : Y(high[i]) - 11;
    var d = alta ? -1 : 1;
    ctx.fillStyle = cc; ctx.globalAlpha = (i===op.sinal_i)?1:0.5;
    ctx.beginPath();
    ctx.moveTo(X(i), yy + d*6);
    ctx.lineTo(X(i)-4.5, yy - d*1.5);
    ctx.lineTo(X(i)+4.5, yy - d*1.5);
    ctx.closePath(); ctx.fill();
    ctx.globalAlpha = 1;
  }

  /* -------- painel de esforco e de delta ---------------------------------
     Desenhar agressao compradora para cima e vendedora para baixo parece a
     escolha obvia, mas nao informa nada: as duas series tem correlacao de
     0,99 e o grafico vira um espelho quase perfeito em toda barra.

     O que o indicador le sao outras duas quantidades: o ESFORCO (a soma, que
     alimenta o filtro da V8) e o DELTA (a diferenca, que alimenta os dois
     sinais). Elas NAO cabem na mesma escala -- o delta tipico e uma fracao de
     poucos por cento do esforco, e desenhado junto some. Por isso duas faixas
     empilhadas, cada uma com a sua propria escala. */
  var ya = g.hp + g.gap, ha = g.h - g.mb - ya;
  var hA = ha*0.52, hB = ha - hA - 8;
  var baseA = ya + hA, midB = ya + hA + 8 + hB/2;
  var mxE = 1, mxD = 1;
  for (var i=a;i<=b;i++){
    mxE = Math.max(mxE, agrC[i]+agrV[i]);
    mxD = Math.max(mxD, Math.abs(agrC[i]-agrV[i]));
  }
  for (var i=a;i<=b;i++){
    var x = X(i), bw = Math.max(1.4, Math.min(pw*0.66, 13));
    var esf = agrC[i]+agrV[i], dlt = agrC[i]-agrV[i];
    var atual = (i===op.sinal_i);
    ctx.globalAlpha = atual?0.85:0.30;
    ctx.fillStyle = cor('--tinta2');
    var he = (esf/mxE)*hA;
    ctx.fillRect(x-bw/2, baseA-he, bw, he);
    ctx.globalAlpha = atual?1:0.55;
    ctx.fillStyle = dlt>=0 ? cor('--alta') : cor('--baixa');
    var hd = (Math.abs(dlt)/mxD)*(hB/2);
    ctx.fillRect(x-bw/2, dlt>=0 ? midB-hd : midB, bw, hd);
    ctx.globalAlpha = 1;
  }
  ctx.strokeStyle = cor('--linha'); ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(g.ml,Math.round(baseA)+0.5);
  ctx.lineTo(g.w-g.mr,Math.round(baseA)+0.5); ctx.stroke();
  ctx.strokeStyle = cor('--tinta2');
  ctx.beginPath(); ctx.moveTo(g.ml,Math.round(midB)+0.5);
  ctx.lineTo(g.w-g.mr,Math.round(midB)+0.5); ctx.stroke();
  ctx.fillStyle = cor('--tinta2'); ctx.font='10.5px system-ui,sans-serif';
  ctx.textAlign='left';
  ctx.fillText('esforço', g.ml+4, ya+9);
  ctx.fillText(num(mxE), g.w-g.mr+5, ya+9);
  ctx.fillText('delta', g.ml+4, midB-hB/2+9);
  ctx.fillText('±'+num(mxD), g.w-g.mr+5, midB+3.5);

  /* marcas verticais: gatilho, entrada, saida */
  function vert(i, txt, c, cima){
    if (i<a || i>b) return;
    var x = X(i);
    ctx.save(); ctx.setLineDash([2,3]); ctx.strokeStyle = c; ctx.lineWidth=1.2;
    ctx.beginPath(); ctx.moveTo(x, g.mt); ctx.lineTo(x, g.h-g.mb); ctx.stroke();
    ctx.restore();
    var y = cima ? g.mt+10 : g.h-g.mb+12;
    ctx.font='10px system-ui,sans-serif'; ctx.textAlign='center';
    var lg = ctx.measureText(txt).width;
    ctx.fillStyle = cor('--papel'); ctx.fillRect(x-lg/2-3, y-9, lg+6, 12);
    ctx.fillStyle = c; ctx.fillText(txt, x, y);
  }
  vert(op.sinal_i, 'sinal', cor('--realce'), true);
  vert(op.sinal_i+1, 'entrada', cor('--tinta2'), false);
  if (op.saida_i > op.sinal_i+1) vert(op.saida_i, 'saída', cor('--tinta2'), true);

  ctx.strokeStyle = cor('--linha'); ctx.lineWidth=1;
  ctx.strokeRect(0.5,0.5,g.w-1,g.h-1);
};
Kline.prototype.hover = function(e){
  if (!this.win) return;
  var r = this.cv.getBoundingClientRect();
  var i = Math.round(this.win[0] + (e.clientX-r.left-8)/this.pw - 0.5);
  if (i < this.win[0] || i > this.win[1]){ this.dica.style.visibility='hidden'; return; }
  var esf = agrC[i]+agrV[i], dlt = agrC[i]-agrV[i];
  this.dica.innerHTML = '<b>'+data(tempo[i])+'</b><br>A '+num(open[i],2)+
    ' · M '+num(high[i],2)+' · m '+num(low[i],2)+' · F '+num(close[i],2)+
    '<br>range '+num((high[i]-low[i])/TICK)+' t · corpo '+
    num((close[i]-open[i])/TICK)+' t'+
    '<br>agressão: compra '+num(agrC[i])+' · venda '+num(agrV[i])+
    '<br>esforço '+num(esf)+' · delta '+sgn(dlt);
  this.dica.style.left = Math.min(e.clientX+14, innerWidth-350)+'px';
  this.dica.style.top = (e.clientY+14)+'px';
  this.dica.style.visibility = 'visible';
};

/* ---- graficos auxiliares ----------------------------------------------- */
function curva(cv, pontos){
  var ctx = cv.getContext('2d'), w = cv.clientWidth, h = 190;
  var dpr = window.devicePixelRatio||1;
  cv.width = Math.round(w*dpr); cv.height = Math.round(h*dpr);
  cv.style.height = h+'px'; ctx.setTransform(dpr,0,0,dpr,0,0);
  ctx.fillStyle = cor('--papel'); ctx.fillRect(0,0,w,h);
  if (!pontos.length) return;
  var lo=0, hi=0;
  pontos.forEach(function(p){ if(p[1]<lo)lo=p[1]; if(p[1]>hi)hi=p[1]; });
  var pad=(hi-lo)*0.08||1; lo-=pad; hi+=pad;
  var ml=8, mr=66, mt=10, mb=18;
  function X(i){ return ml + i/(pontos.length-1||1)*(w-ml-mr); }
  function Y(v){ return mt + (hi-v)/(hi-lo)*(h-mt-mb); }
  ctx.strokeStyle=cor('--grade'); ctx.fillStyle=cor('--tinta2');
  ctx.font='10.5px system-ui,sans-serif'; ctx.textAlign='left';
  [lo,(lo+hi)/2,hi].forEach(function(v){
    var y=Math.round(Y(v))+0.5;
    ctx.beginPath(); ctx.moveTo(ml,y); ctx.lineTo(w-mr,y); ctx.stroke();
    ctx.fillText(sgn(v,0)+' t', w-mr+5, y+3.5);
  });
  ctx.strokeStyle=cor('--tinta2'); ctx.lineWidth=1;
  var y0=Math.round(Y(0))+0.5;
  ctx.beginPath(); ctx.moveTo(ml,y0); ctx.lineTo(w-mr,y0); ctx.stroke();
  var fim = pontos[pontos.length-1][1];
  ctx.strokeStyle = fim>=0?cor('--alta'):cor('--baixa'); ctx.lineWidth=1.6;
  ctx.beginPath();
  pontos.forEach(function(p,i){ var x=X(i), y=Y(p[1]);
    if(!i) ctx.moveTo(x,y); else ctx.lineTo(x,y); });
  ctx.stroke();
  ctx.strokeStyle=cor('--linha'); ctx.lineWidth=1; ctx.strokeRect(.5,.5,w-1,h-1);
}

function horas(cv, dados){
  var ctx=cv.getContext('2d'), w=cv.clientWidth, h=190;
  var dpr=window.devicePixelRatio||1;
  cv.width=Math.round(w*dpr); cv.height=Math.round(h*dpr);
  cv.style.height=h+'px'; ctx.setTransform(dpr,0,0,dpr,0,0);
  ctx.fillStyle=cor('--papel'); ctx.fillRect(0,0,w,h);
  if (!dados.length) return;
  var mx=1; dados.forEach(function(d){ mx=Math.max(mx,Math.abs(d.expectativa_ticks)); });
  var ml=8,mr=60,mt=10,mb=22, bw=(w-ml-mr)/dados.length;
  function Y(v){ return mt+(mx-v)/(2*mx)*(h-mt-mb); }
  ctx.strokeStyle=cor('--tinta2'); var y0=Math.round(Y(0))+0.5;
  ctx.beginPath(); ctx.moveTo(ml,y0); ctx.lineTo(w-mr,y0); ctx.stroke();
  ctx.fillStyle=cor('--tinta2'); ctx.font='10.5px system-ui,sans-serif';
  ctx.textAlign='left';
  ctx.fillText(sgn(mx,0)+' t', w-mr+5, Y(mx)+4);
  ctx.fillText(sgn(-mx,0)+' t', w-mr+5, Y(-mx)+4);
  dados.forEach(function(d,i){
    var v=d.expectativa_ticks, x=ml+i*bw;
    ctx.fillStyle = v>=0?cor('--alta'):cor('--baixa');
    ctx.globalAlpha = Math.min(1, 0.35 + d.n/60);
    ctx.fillRect(x+bw*0.13, Math.min(y0,Y(v)), bw*0.74, Math.abs(Y(v)-y0));
    ctx.globalAlpha=1;
    ctx.fillStyle = cor('--tinta2');
    ctx.font='10px system-ui,sans-serif'; ctx.textAlign='center';
    ctx.fillText(d.hora, x+bw/2, h-6);
  });
  ctx.strokeStyle=cor('--linha'); ctx.strokeRect(.5,.5,w-1,h-1);
}

/* ---- navegador de operacoes -------------------------------------------- */
var selVar = document.getElementById('selVar');
var selMot = document.getElementById('selMot');
var selLado = document.getElementById('selLado');
var selTipo = document.getElementById('selTipo');
var btPrev = document.getElementById('btPrev');
var btProx = document.getElementById('btProx');
var conta = document.getElementById('conta');
var ficha = document.getElementById('ficha');
var desc  = document.getElementById('descVar');
var kl = new Kline(document.getElementById('cvKline'),
                   document.getElementById('dica'));
var lista = [], pos = 0;

function opDe(v, linha){
  var o = {}; v.trades.colunas.forEach(function(c,i){ o[c]=linha[i]; });
  return o;
}
function variante(){ return R.variantes[+selVar.value]; }

function filtra(){
  var v = variante();
  lista = v.trades.linhas.map(function(L){ return opDe(v,L); })
    .filter(function(o){
      if (selMot.value!=='*' && o.motivo!==selMot.value) return false;
      if (selLado.value!=='*' && o.lado!==selLado.value) return false;
      if (selTipo.value!=='*' && String(o.tipo)!==selTipo.value) return false;
      return true;
    });
  pos = 0;
  desc.textContent = v.descricao;
  curva(document.getElementById('cvCurva'), v.curva);
  horas(document.getElementById('cvHoras'), v.por_hora);
  mostra();
}
function mostra(){
  if (!lista.length){
    conta.textContent = 'nenhuma operação com esse filtro';
    ficha.innerHTML = ''; btPrev.disabled = btProx.disabled = true; return;
  }
  var v = variante(), o = lista[pos];
  kl.mostra(o, v.cfg);
  var tot = v.trades.total, mostradas = v.trades.linhas.length;
  conta.textContent = 'operação ' + (pos+1) + ' de ' + lista.length +
    (mostradas < tot ? '  (amostra de ' + num(mostradas) + ' das ' + num(tot) + ')' : '');
  var motivo = {alvo:'alvo', breakeven:'breakeven após a parcial',
                stop:'stop', tempo:'aberta no fim do histórico'}[o.motivo] || o.motivo;
  ficha.innerHTML =
    '<div><span>quando</span><b>'+data(tempo[o.sinal_i])+'</b></div>' +
    '<div><span>sinal</span><b>'+(o.tipo===2?'divergência':'absorção')+'</b></div>' +
    '<div><span>lado</span><b>'+(o.lado==='long'?'compra':'venda')+'</b></div>' +
    '<div><span>entrada</span><b>'+num(o.entrada,2)+'</b></div>' +
    '<div><span>desfecho</span><b>'+motivo+'</b></div>' +
    '<div><span>resultado</span><b class="'+classe(o.ticks)+'">'+
      sgn(o.ticks,0)+' t</b></div>' +
    '<div><span>em R</span><b class="'+classe(o.ticks)+'">'+
      sgn(o.ticks/v.cfg.stop_ticks,2)+'R</b></div>' +
    '<div><span>barras</span><b>'+o.barras+'</b></div>' +
    '<div><span>resultado rel.</span><b>'+num(o.res_rel,2)+'</b></div>' +
    '<div><span>esforço rel.</span><b>'+num(o.esf_rel,2)+'</b></div>' +
    '<div><span>agressão a favor</span><b>'+num(o.qual_rel,2)+'</b></div>' +
    '<div><span>barras viradas</span><b>'+o.contra+'</b></div>';
  btPrev.disabled = pos<=0; btProx.disabled = pos>=lista.length-1;
}
selVar.onchange = filtra; selMot.onchange = filtra;
selLado.onchange = filtra; selTipo.onchange = filtra;
btPrev.onclick = function(){ if(pos>0){pos--;mostra();} };
btProx.onclick = function(){ if(pos<lista.length-1){pos++;mostra();} };
document.addEventListener('keydown', function(e){
  if (e.key==='ArrowLeft') btPrev.click();
  if (e.key==='ArrowRight') btProx.click();
});
filtra();
})();
"""


# --------------------------------------------------------------------------
def bloco_variantes(r):
    L = ['<div class="rolagem"><table><thead><tr>'
         '<th>variante</th><th>sinais</th><th>operações</th><th>acerto</th>'
         '<th>exp./op.</th><th>t</th><th>total</th><th>fator de lucro</th>'
         '<th>rebaixamento</th></tr></thead><tbody>']
    for v in r['variantes']:
        s = v['stats']
        destaque = ' class="realce"' if v['nome'] == 'V8' else ''
        L.append('<tr%s><td><b>%s</b> · %s</td><td class="num">%s</td>'
                 '<td class="num">%s</td><td class="num">%s</td>'
                 '<td class="num %s">%s</td><td class="num %s">%s</td>'
                 '<td class="num %s">%s</td>'
                 '<td class="num">%s</td><td class="num neg">%s</td></tr>'
                 % (destaque, v['nome'], v['rotulo'], n(s.get('sinais', 0)),
                    n(s.get('operacoes', 0)), pct(s.get('acerto', 0)),
                    cls(s.get('expectativa_ticks', 0)),
                    fmt(s.get('expectativa_ticks', 0), 1),
                    cls(s.get('t_stat', 0)), fmt(s.get('t_stat', 0), 2),
                    cls(s.get('ticks_total', 0)), fmt(s.get('ticks_total', 0)),
                    n(s.get('fator_lucro', 0), 2),
                    n(s.get('drawdown_ticks', 0))))
    L.append('</tbody></table></div>')
    return '\n'.join(L)


def bloco_sensibilidade(r):
    L = ['<div class="rolagem"><table><thead><tr><th>variante</th>'
         '<th>pessimista</th><th>otimista</th><th>custo 10 t</th>'
         '<th>custo 20 t</th><th>custo 40 t</th><th>1ª metade</th>'
         '<th>2ª metade</th></tr></thead><tbody>']
    for v in r['variantes']:
        vals = [v['stats'].get('expectativa_ticks', 0),
                v['stats_otimista'].get('expectativa_ticks', 0),
                v['custo']['10'].get('expectativa_ticks', 0),
                v['custo']['20'].get('expectativa_ticks', 0),
                v['custo']['40'].get('expectativa_ticks', 0),
                v['metades']['1a'].get('expectativa_ticks', 0),
                v['metades']['2a'].get('expectativa_ticks', 0)]
        L.append('<tr%s><td>%s · %s</td>%s</tr>'
                 % (' class="realce"' if v['nome'] == 'V8' else '',
                    v['nome'], v['rotulo'],
                    ''.join('<td class="num %s">%s</td>' % (cls(x), fmt(x, 1))
                            for x in vals)))
    L.append('</tbody></table></div>')
    return '\n'.join(L)


def bloco_busca(r):
    L = ['<div class="rolagem"><table><thead><tr><th>filtro testado</th>'
         '<th>operações</th><th>acerto</th><th>z</th><th>z (1R)</th>'
         '<th>expectativa</th></tr></thead><tbody>']
    for b in sorted(r['busca'], key=lambda x: (x['artefato'], -x['z'])):
        if b['poucas'] and not b['artefato']:
            L.append('<tr class="risca"><td>%s</td><td class="num">%s</td>'
                     '<td colspan="4">amostra insuficiente</td></tr>'
                     % (b['filtro'], n(b['n'])))
            continue
        marca, klass = '', ''
        if b['artefato']:
            marca, klass = ' &nbsp;⚠️ artefato de método', ' class="risca"'
        elif b['esforco']:
            marca = ' &nbsp;⟵'
        L.append('<tr%s><td>%s%s</td><td class="num">%s</td>'
                 '<td class="num">%s</td><td class="num %s"><b>%s</b></td>'
                 '<td class="num %s">%s</td><td class="num %s">%s t</td></tr>'
                 % (klass, b['filtro'], marca, n(b['n']), pct(b['acerto']),
                    cls(b['z']), fmt(b['z'], 2), cls(b['r1']['z']),
                    fmt(b['r1']['z'], 2), cls(b['expectativa_ticks']),
                    fmt(b['expectativa_ticks'], 1)))
    L.append('</tbody></table></div>')
    return '\n'.join(L)


def bloco_excursao(r):
    rot = {'sinal': 'o sinal do indicador',
           'direcao_sorteada': 'mesmas barras, <b>direção sorteada</b>',
           'barra_e_direcao_sorteadas': 'barra e direção sorteadas',
           'esforco_baixo': 'sinal com <b>esforço baixo</b>'}
    L = ['<div class="rolagem"><table><thead><tr><th>horizonte</th><th>amostra</th>'
         '<th>MFE mediana</th><th>MAE mediana</th><th>MFE/MAE</th>'
         '<th>deriva média</th><th>t</th></tr></thead><tbody>']
    for H in ('5', '20', '40'):
        for k in ('sinal', 'direcao_sorteada', 'barra_e_direcao_sorteadas',
                  'esforco_baixo'):
            b = r['excursao'][k][H]
            L.append('<tr><td>%s barras</td><td>%s</td><td class="num">%s t</td>'
                     '<td class="num">%s t</td><td class="num"><b>%s</b></td>'
                     '<td class="num %s">%s t</td><td class="num %s">%s</td></tr>'
                     % (H, rot[k], n(b['mfe_med']), n(b['mae_med']),
                        n(b['razao'], 3), cls(b['deriva_media']),
                        fmt(b['deriva_media'], 1), cls(b['deriva_t']),
                        fmt(b['deriva_t'], 2)))
    L.append('</tbody></table></div>')
    return '\n'.join(L)


def bloco_linha_base(r):
    L = ['<div class="rolagem"><table><thead><tr><th>grupo</th><th>o que é</th>'
         '<th>amostra</th><th>continua</th><th>z</th></tr></thead><tbody>']
    for g in r['linha_base']['grupos']:
        forte = 'SINAL' in g['grupo']
        L.append('<tr%s><td>%s%s%s</td><td>%s</td><td class="num">%s</td>'
                 '<td class="num %s"><b>%s</b></td><td class="num %s">%s</td></tr>'
                 % (' class="realce"' if g['grupo'] == 'SINAL + esforço baixo' else '',
                    '<b>' if forte else '', g['grupo'], '</b>' if forte else '',
                    g['nota'], n(g['n']), cls(g['acerto'] - 0.5),
                    pct(g['acerto'], 2), cls(g['z']), fmt(g['z'], 2)))
    L.append('</tbody></table></div>')
    return '\n'.join(L)


def bloco_plato(r):
    E = r['esforco']
    L = ['<div class="rolagem"><table><thead><tr><th>limite de esforço</th>'
         '<th>operações</th><th>acerto</th><th>z</th><th>expectativa</th>'
         '</tr></thead><tbody>']
    for p in E['plato']:
        eh = abs(p['limite'] - E['limite']) < 1e-9
        L.append('<tr%s><td>≤ %s%s</td><td class="num">%s</td>'
                 '<td class="num">%s</td><td class="num %s">%s</td>'
                 '<td class="num %s">%s t</td></tr>'
                 % (' class="realce"' if eh else '', n(p['limite'], 2),
                    ' &nbsp;⟵ publicado' if eh else '', n(p['n']),
                    pct(p['acerto']), cls(p['z']), fmt(p['z'], 2),
                    cls(p['expectativa_ticks']),
                    fmt(p['expectativa_ticks'], 1)))
    L.append('</tbody></table></div>')
    return '\n'.join(L)


def bloco_pedacos(r):
    E = r['esforco']
    L = ['<div class="rolagem"><table><thead><tr><th>pedaço da amostra</th>'
         '<th>operações</th><th>acerto</th><th>z</th><th>expectativa</th>'
         '</tr></thead><tbody>']
    linhas = [('%sª metade' % nm[0], E['metades'][nm]) for nm in ('1a', '2a')]
    linhas += [('%sº terço' % v['terco'], v) for v in E['tercos']]
    linhas += [('<b>controle invertido</b>', E['invertido'])]
    for rot, v in linhas:
        L.append('<tr><td>%s</td><td class="num">%s</td>'
                 '<td class="num %s">%s</td><td class="num %s">%s</td>'
                 '<td class="num %s">%s t</td></tr>'
                 % (rot, n(v['n']), cls(v['acerto'] - 0.5), pct(v['acerto']),
                    cls(v['z']), fmt(v['z'], 2), cls(v['expectativa_ticks']),
                    fmt(v['expectativa_ticks'], 1)))
    L.append('</tbody></table></div>')
    return '\n'.join(L)


def bloco_gestao(r):
    L = ['<div class="rolagem"><table><thead><tr><th>gestão</th>'
         '<th>operações</th><th>acerto</th><th>expectativa</th><th>em R</th>'
         '<th>t</th><th>barras</th><th>sem ambiguidade</th>'
         '</tr></thead><tbody>']
    for g in r['gestao']:
        eh = 'MEIO RANGE' in g['rotulo']
        L.append('<tr%s><td>%s</td><td class="num">%s</td><td class="num">%s</td>'
                 '<td class="num %s">%s t</td><td class="num %s">%s</td>'
                 '<td class="num %s">%s</td><td class="num">%s</td>'
                 '<td>%s</td></tr>'
                 % (' class="realce"' if eh else '', g['rotulo'],
                    n(g['operacoes']), pct(g['acerto']),
                    cls(g['expectativa_ticks']), fmt(g['expectativa_ticks'], 1),
                    cls(g['expectativa_R']), fmt(g['expectativa_R'], 3),
                    cls(g['t_stat']), fmt(g['t_stat'], 2),
                    n(g['barras_media'], 1),
                    '<b>sim</b>' if g['sem_ambiguidade'] else 'não'))
    L.append('</tbody></table></div>')
    return '\n'.join(L)


def bloco_sens_ind(r):
    L = []
    for g in r['sensibilidade']:
        L.append('<h4>%s — %s</h4>' % (g['campo'], g['rotulo']))
        L.append('<div class="rolagem"><table><thead><tr><th>valor</th>'
                 '<th>sinais gerados</th><th>operações</th><th>acerto</th>'
                 '<th>z</th></tr></thead><tbody>')
        for ln in g['linhas']:
            b = ln['esforco_baixo']
            L.append('<tr%s><td>%s%s</td><td class="num">%s</td>'
                     '<td class="num">%s</td><td class="num">%s</td>'
                     '<td class="num %s">%s</td></tr>'
                     % (' class="realce"' if ln['padrao'] else '',
                        n(ln['valor'], 2),
                        ' &nbsp;⟵ padrão do .mq5' if ln['padrao'] else '',
                        n(ln['sinais']), n(b['n']), pct(b['acerto']),
                        cls(b['z']), fmt(b['z'], 2)))
        L.append('</tbody></table></div>')
    return '\n'.join(L)


def bloco_horario(r):
    H = r['horario']
    L = ['<div class="rolagem"><table><thead><tr><th>escolhido em</th>'
         '<th>horas escolhidas</th><th>testado em</th><th>operações</th>'
         '<th>acerto</th><th>referência</th><th>z</th></tr></thead><tbody>']
    for k, e, t in (('escolhe_1a_testa_2a', '1ª metade', '2ª metade'),
                    ('escolhe_2a_testa_1a', '2ª metade', '1ª metade')):
        v = H[k]
        L.append('<tr><td>%s</td><td>%s</td><td>%s</td><td class="num">%s</td>'
                 '<td class="num">%s</td><td class="num">%s</td>'
                 '<td class="num %s"><b>%s</b></td></tr>'
                 % (e, ', '.join('%dh' % h for h in v['horas']) or '—', t,
                    n(v['n']), pct(v['acerto']), pct(v['acerto_referencia']),
                    cls(v['z']), fmt(v['z'], 2)))
    L.append('</tbody></table></div>')
    return '\n'.join(L)


GLOSSARIO = [
    ('Tick', 'A menor variação de preço do ativo. No XAUUSD vale <b>0,01 '
     'dólar</b>. Todo resultado deste relatório é medido em ticks: 388 ticks '
     '= 3,88 USD.'),
    ('Gráfico de range', 'Gráfico em que a barra fecha quando o preço percorre '
     'uma distância fixa — aqui, <b>388 ticks</b>. O tempo não conta: uma '
     'barra pode levar dez segundos ou dez minutos. Como <code>High−Low</code> '
     'é constante por construção, corpo e pavio são complementares.'),
    ('R', 'A unidade de risco: quanto se perde num stop. Neste estudo o R '
     'padrão é meio range (194 ticks). Resultados em R são comparáveis entre '
     'gestões diferentes; resultados em ticks não são.'),
    ('Esforço', 'A agressão total da barra: <code>agressão compradora + '
     'agressão vendedora</code>. Mede quanta gente negociou, '
     'independentemente de quem venceu.'),
    ('Resultado', 'O corpo da barra, <code>Close − Open</code>, em ticks. Num '
     'gráfico de range é o <b>deslocamento líquido</b> real: tudo que virou '
     'pavio foi caminho andado e devolvido.'),
    ('Delta', 'A agressão líquida: <code>compradora − vendedora</code>. '
     'Positivo quando quem atacou no book foi majoritariamente comprador.'),
    ('Eficiência', 'Resultado relativo dividido por esforço relativo. Quanto '
     'de deslocamento a barra conseguiu por unidade de briga.'),
    ('Absorção (sinal 1)', 'A barra vira o movimento andando <b>menos que o '
     'normal</b> da direção dela e com <b>menos agressão a favor</b> que o '
     'normal. Interpretação: a barra andou sem que a agressão a empurrasse — '
     'quem venceu foi a passiva do lado da barra. Seta verde ou vermelha.'),
    ('Divergência no pivô (sinal 2)', 'Duas barras quase sem pavio formam um '
     'pivô, e o delta somado das duas aponta para o lado <b>contrário</b> ao '
     'da resolução. Como o pivô é um round trip — anda R e devolve R — o viés '
     'geométrico do delta se cancela entre as duas barras, e o zero vira '
     'referência legítima. Seta azul.'),
    ('Relativo à direção', 'Toda métrica do indicador é comparada com a média '
     'das barras da <b>mesma direção</b> nas últimas 60, nunca com a média '
     'geral. Em janela de alta o delta médio é positivo mesmo em barra '
     'irrelevante; comparar só contra o próprio lado cancela esse viés.'),
    ('Barra completa', 'Barra cujo range alcançou pelo menos 90% do range '
     'médio recente. As barras cortadas no fim da sessão não entram nas '
     'médias de referência nem geram sinal.'),
    ('MFE / MAE', 'A maior excursão a favor e a maior excursão contra, depois '
     'da entrada, sem nenhuma regra de saída. A razão entre as duas mede se o '
     'gatilho tem leitura de direção antes de qualquer alvo ser escolhido.'),
    ('Expectativa', 'A média de ticks por operação. É o número que importa: '
     'taxa de acerto alta com expectativa negativa é uma estratégia que perde '
     'dinheiro devagar.'),
    ('z e t', 'Quantos erros padrão o resultado está longe do acaso. |z| '
     'acima de 2 é o mínimo convencional para levar a sério — e mesmo assim, '
     'quando é o melhor de 30 tentativas, precisa de validação independente.'),
    ('Fator de lucro', 'Soma dos ganhos dividida pela soma das perdas. Acima '
     'de 1 a estratégia ganha dinheiro no período; 1,38 significa 1,38 dólar '
     'ganho para cada dólar perdido.'),
    ('Rebaixamento', 'A maior queda acumulada desde um pico da curva de '
     'resultado. É o que se teria de aguentar sem desistir.'),
    ('Ambiguidade dentro da barra', 'Quando a mesma barra toca alvo e stop, o '
     'OHLC não diz qual veio primeiro. Neste gráfico, um alvo e um stop a '
     '<b>meio range</b> não podem ser tocados os dois na mesma barra — e a '
     'ambiguidade desaparece.'),
    ('Controle invertido', 'A mesma estratégia operando o lado oposto. Se a '
     'vantagem for de direção, o controle tem de ser o espelho negativo. Se '
     'não for, a vantagem vinha da contabilidade.'),
]


def escrever():
    with open(os.path.join(SAIDA, 'resumo.json'), encoding='utf-8') as f:
        r = json.load(f)
    with open(os.path.join(SAIDA, 'barras.json'), encoding='utf-8') as f:
        barras = f.read()

    D, I, P = r['dados'], r['indicador'], r['dados']['premissa']
    V = {v['nome']: v for v in r['variantes']}
    LB, EF, HR = r['linha_base'], r['esforco'], r['horario']
    s8, s7, s9 = V['V8']['stats'], V['V7']['stats'], V['V9']['stats']
    cands = [b for b in r['busca'] if not b['artefato'] and not b['poucas']]
    art = [b for b in r['busca'] if b['artefato']]
    g_meio = [g for g in r['gestao'] if 'MEIO RANGE' in g['rotulo']][0]
    g_um = [g for g in r['gestao'] if 'um range' in g['rotulo']][0]
    g_dois = [g for g in r['gestao'] if 'dois ranges' in g['rotulo']][0]

    opcoes_var = '\n'.join(
        '<option value="%d"%s>%s · %s</option>'
        % (i, ' selected' if v['nome'] == 'V8' else '', v['nome'], v['rotulo'])
        for i, v in enumerate(r['variantes']))
    glos = '\n'.join('<dt>%s</dt><dd>%s</dd>' % (a_, b_) for a_, b_ in GLOSSARIO)

    H = []
    a = H.append
    a('<!doctype html>')
    a('<html lang="pt-BR"><head>')
    a('<meta charset="utf-8">')
    a('<meta name="viewport" content="width=device-width,initial-scale=1">')
    a('<title>Esforço × Resultado em gráfico de range — backtest</title>')
    a('<style>%s</style>' % CSS)
    a('</head><body>')
    a('<div class="env">')

    # -------------------------------------------------------------- cabecalho
    a('<header>')
    a('<h1>Esforço × Resultado<br>em gráfico de range — o que o gatilho '
      'realmente vê</h1>')
    a('<p class="sub">XAUUSD · barras de %s ticks · %s barras · %s a %s · '
      '%s pregões<br>Backtest de <code>Trigger_EsforcoResultado_Range.mq5</code>'
      '<br>Gerado em %s a partir de <code>%s</code></p>'
      % (n(r['range_nominal']), n(D['barras']), D['inicio'][:10], D['fim'][:10],
         n(D['dias']), r['gerado_em'], r['arquivo']))
    a('</header>')

    a('<nav class="sumario">'
      '<a href="#s1">1 · Resposta curta</a><br>'
      '<a href="#s2">2 · Os dados e a premissa</a><br>'
      '<a href="#s3">3 · Método: as decisões que mudam tudo</a><br>'
      '<a href="#s4">4 · O que o gatilho produz</a><br>'
      '<a href="#s5">5 · O sinal tem direção?</a><br>'
      '<a href="#s6">6 · A busca por um filtro</a><br>'
      '<a href="#s7">7 · O filtro de esforço, validado</a><br>'
      '<a href="#s8">8 · O horário, que não passou</a><br>'
      '<a href="#s9">9 · Os parâmetros do indicador</a><br>'
      '<a href="#s10">10 · A gestão</a><br>'
      '<a href="#s11">11 · As variantes</a><br>'
      '<a href="#s12">12 · Operação a operação</a><br>'
      '<a href="#s13">13 · Restrições recomendadas</a><br>'
      '<a href="#s14">14 · Glossário</a><br>'
      '<a href="#s15">15 · Limitações</a>'
      '</nav>')

    # ---------------------------------------------------------------------- 1
    a('<h2 id="s1">1 · Resposta curta</h2>')
    a('<p class="lead">O gatilho <b>tem</b> leitura de direção — mas ela vive '
      'por uma barra e morre depois. Medida no horizonte certo, a vantagem '
      'existe e sobrevive a todos os controles que este estudo soube aplicar. '
      'Medida no horizonte errado, que é onde a maioria dos backtests mede, '
      'ela some por completo.</p>')
    a('<div class="cartoes">')
    for rot, val, nota, klass in (
            ('Acerto da V8', pct(s8['acerto']),
             '%s operações, alvo e stop a meio range' % n(s8['operacoes']), ''),
            ('Expectativa', fmt(s8['expectativa_ticks'], 1) + ' t',
             '%s R por operação (t = %s)'
             % (fmt(s8['expectativa_R'], 3), fmt(s8['t_stat'], 2)), 'pos'),
            ('Linha de base', pct(LB['grupos'][0]['acerto'], 1),
             'o gráfico já continua sozinho', ''),
            ('Ganho do indicador', fmt(100 * LB['ganho']['diferenca'], 1) + ' pt',
             'sobre o controle emparelhado (z %s)' % fmt(LB['ganho']['z'], 2),
             'pos')):
        a('<div class="cartao"><div class="r">%s</div><div class="v %s">%s</div>'
          '<div class="n">%s</div></div>' % (rot, klass, val, nota))
    a('</div>')
    a('<p>Três medidas contam a história inteira:</p>')
    a('<p><b>Um.</b> Este gráfico já vem inclinado. <b>%s</b> das barras '
      'continuam na própria direção na barra seguinte — z = %s sobre %s '
      'barras. Qualquer gatilho que dispare a favor de uma barra herda isso de '
      'graça, e parte de todo acerto acima de 50%% não é mérito dele.'
      % (pct(LB['grupos'][0]['acerto'], 2), fmt(LB['grupos'][0]['z'], 2),
         n(LB['grupos'][0]['n'])))
    a('<p><b>Dois.</b> O indicador acrescenta algo real por cima. Contra o '
      'controle emparelhado — barras de virada com esforço baixo, mas sem as '
      'condições de resultado e agressão — a diferença é de <b>%s pontos</b> '
      '(%s contra %s), com z = %s. É esse o crédito que cabe ao indicador, e '
      'não os %s inteiros.'
      % (fmt(100 * LB['ganho']['diferenca'], 1),
         pct(LB['ganho']['com_indicador'], 2), pct(LB['ganho']['base'], 2),
         fmt(LB['ganho']['z'], 2), pct(s8['acerto'])))
    a('<p><b>Três.</b> A vantagem não dura. Em meio range a expectativa é de '
      '%s por operação; em um range inteiro cai para %s; em dois ranges vira '
      '%s. O que o indicador enxerga se dissolve em poucas barras — e é '
      'exatamente por isso que a excursão medida em 5, 20 e 40 barras (§5.1) '
      'não acha nada.'
      % (fmt(g_meio['expectativa_R'], 3) + ' R',
         fmt(g_um['expectativa_R'], 3) + ' R',
         fmt(g_dois['expectativa_R'], 3) + ' R'))
    a('<div class="aviso"><p><b>A ressalva que não pode ficar no rodapé.</b> '
      '%s ticks de expectativa bruta não sobrevivem a 40 ticks de custo. A '
      'margem inteira cabe dentro de um spread ruim, e a entrada é a mercado '
      'no fechamento de uma barra de range — justamente um instante de '
      'movimento, onde o slippage é pior. Isto justifica um teste em tempo '
      'real com lote mínimo; não justifica confiança.</p></div>'
      % fmt(s8['expectativa_ticks'], 1))

    # ---------------------------------------------------------------------- 2
    a('<h2 id="s2">2 · Os dados, e a premissa do indicador</h2>')
    a('<p>Este indicador não funciona em qualquer gráfico. Ele pressupõe duas '
      'coisas — e o pior modo de falhar seria aplicá-lo onde elas não valem, '
      'porque ele não daria erro nenhum: produziria números sem significado. '
      'Por isso as duas foram conferidas antes de qualquer medição.</p>')
    a('<h3>A premissa geométrica: <code>High−Low</code> constante</h3>')
    a('<div class="rolagem"><table><tbody>')
    for rot, val in (('Range mediano', '%s ticks' % n(P['range_mediana'])),
                     ('Barras dentro de ±10% da mediana',
                      '<b>%s</b>' % pct(P['range_dentro_10pct'], 2)),
                     ('Desvio padrão do range',
                      '%s ticks' % n(P['range_desvio'], 2)),
                     ('Mínimo / máximo', '%s / %s ticks'
                      % (n(P['range_min']), n(P['range_max'])))):
        a('<tr><td>%s</td><td class="num">%s</td></tr>' % (rot, val))
    a('</tbody></table></div>')
    a('<p>Confirmada. As barras que fogem são as de fim de sessão, fechadas '
      'antes de completar o range — e são justamente as que o próprio '
      'indicador descarta pelo teste de barra completa.</p>')
    a('<h3>A premissa da agressão</h3>')
    a('<p><code>tick_volume</code> carrega a agressão <b>compradora</b> e '
      '<code>real_volume</code> a <b>vendedora</b> — a convenção do símbolo '
      'sintético gerado pelo <code>Range_Claude_v1.mq5</code>. Num símbolo '
      'comum esses campos significam outra coisa e o estudo inteiro perde o '
      'sentido.</p>')
    a('<div class="rolagem"><table><tbody>')
    for rot, val in (('Barras com agressão vendedora ausente',
                      pct(P['pct_vol_zero'], 2)),
                     ('Barras com agressão compradora ausente',
                      pct(P['pct_tickvol_zero'], 2)),
                     ('Correlação entre os dois campos',
                      n(P['correlacao_agressoes'], 3))):
        a('<tr><td>%s</td><td class="num">%s</td></tr>' % (rot, val))
    a('</tbody></table></div>')
    a('<p>Confirmada. Os dois campos existem, são distintos e caminham '
      'juntos — o que se espera de duas metades do mesmo fluxo, e não de um '
      'campo duplicado. Note porém o que isto <b>não</b> prova: que '
      '<code>tick_volume</code> seja de fato a agressão compradora. Isso '
      'continua sendo uma premissa herdada do gerador do símbolo.</p>')
    a('<div class="rolagem"><table><thead><tr><th>o histórico</th><th></th>'
      '</tr></thead><tbody>')
    for rot, val in (('Barras', n(D['barras'])),
                     ('Período', '%s a %s' % (D['inicio'][:16], D['fim'][:16])),
                     ('Pregões', '%s (%s barras por pregão)'
                      % (n(D['dias']), n(D['barras_por_dia'], 1))),
                     ('Preço', '%s a %s'
                      % (n(D['preco_min'], 2), n(D['preco_max'], 2))),
                     ('Segundos por barra (mediana)',
                      n(D['segundos_por_barra'].get('50%', 0))),
                     ('Corpo / range (mediana)',
                      n(D['corpo_frac'].get('50%', 0), 3))):
        a('<tr><td>%s</td><td class="num">%s</td></tr>' % (rot, val))
    a('</tbody></table></div>')

    # ---------------------------------------------------------------------- 3
    a('<h2 id="s3">3 · Método: as decisões que mudam todo o resto</h2>')
    a('<h3>3.1 · A ambiguidade dentro da barra, e como este gráfico a elimina</h3>')
    a('<p>Quando uma barra toca o alvo <i>e</i> o stop, o OHLC não diz qual '
      'veio primeiro. É o único ponto cego de qualquer backtest feito sobre '
      'OHLC, e normalmente se resolve por convenção: assume-se o stop e '
      'publica-se a hipótese oposta como teto.</p>')
    a('<div class="ok"><p><b>Num gráfico de range existe uma saída melhor.</b> '
      'Como <code>High−Low</code> é <b>%s ticks por construção</b>, uma barra '
      'não consegue percorrer %s ticks para cima <i>e</i> %s para baixo a '
      'partir do próprio open — os dois lados somados dariam exatamente o '
      'range inteiro. Medido neste arquivo, isso acontece em <b>0,03%% das '
      'barras</b>.</p>'
      '<p>Com stop e alvo a <b>meio range</b>, portanto, as hipóteses '
      'pessimista e otimista devolvem <i>o mesmo número</i>. A convenção deixa '
      'de existir, e com ela o principal motivo de desconfiar de um backtest. '
      'É por isso que a métrica central deste estudo é o meio range.</p></div>'
      % (n(r['range_nominal']), n(r['range_nominal'] / 2),
         n(r['range_nominal'] / 2)))
    a('<p>A tabela do §11 mostra a propriedade em ação: nas variantes V7 e V8, '
      'as colunas <i>pessimista</i> e <i>otimista</i> são idênticas.</p>')

    a('<h3>3.2 · O que uma entrada limitada custa em honestidade</h3>')
    a('<p>Uma ordem limitada preenchida <b>dentro</b> de uma barra não tem hora '
      'marcada no arquivo. A máxima daquela barra pode ter acontecido antes do '
      'preenchimento, e creditar o alvo por causa dela é ler o futuro.</p>')
    a('<p>Neste gráfico o erro é grosseiro: a barra tem %s ticks garantidos, '
      'então quase toda barra que preenche uma ordem no meio dela também '
      '“alcança” um alvo de meio range. Contabilizada assim, a entrada '
      'limitada mede <b>%s de acerto</b> — resultado impossível, que aparece '
      'na tabela do §6 marcado como artefato, apenas para mostrar o erro.</p>'
      % (n(r['range_nominal']), pct(art[0]['acerto']) if art else 'n/d'))
    a('<p>Corrigido: na barra do preenchimento a operação <b>só pode piorar</b>. '
      'É a convenção pessimista do resto do estudo, aplicada ao único instante '
      'que o arquivo não datou. O número da V3 é um <b>piso</b> — e nem o teto '
      'irrealizável salvaria a entrada limitada, que abandona %s dos sinais '
      'sem compensar nada em preço.</p>'
      % pct(1 - V['V3']['stats']['taxa_ativacao']))

    a('<h3>3.3 · As demais decisões</h3>')
    a('<ul>')
    a('<li><b>Custo.</b> A coluna <code>&lt;SPREAD&gt;</code> do arquivo traz '
      'valores impossíveis e foi descartada. O custo entra como cenário '
      'explícito — 0, 10, 20 e 40 ticks — nunca embutido.</li>')
    a('<li><b>Uma operação por vez.</b> Sinais que aparecem com posição aberta '
      'são descartados, como aconteceria na mesa. É por isso que a V0 mostra '
      '%s operações e a V4, de alvo mais curto, mostra %s.</li>'
      % (n(V['V0']['stats']['operacoes']), n(V['V4']['stats']['operacoes'])))
    a('<li><b>Entrada a mercado no fechamento da barra de sinal</b>, com a '
      'gestão começando na barra seguinte. O preço é conhecido na fronteira da '
      'barra; não há instante indatado.</li>')
    a('<li><b>A busca inteira é publicada.</b> Os %s filtros testados aparecem '
      'no §6 com o z de cada um, para que o melhor seja lido como o máximo de '
      '%s tentativas — e não como uma descoberta.</li>'
      % (n(len(cands)), n(len(cands))))
    a('</ul>')

    # ---------------------------------------------------------------------- 4
    a('<h2 id="s4">4 · O que o gatilho produz</h2>')
    a('<div class="cartoes">')
    for rot, val, nota in (
            ('Sinais', n(I['total']),
             '%s das barras' % pct(I['pct_barras'], 2)),
            ('Absorção', n(I['absorcao_alta'] + I['absorcao_baixa']),
             '%s de alta, %s de baixa'
             % (n(I['absorcao_alta']), n(I['absorcao_baixa']))),
            ('Divergência', n(I['divergencia_alta'] + I['divergencia_baixa']),
             '%s de alta, %s de baixa'
             % (n(I['divergencia_alta']), n(I['divergencia_baixa']))),
            ('Frequência', n(I['sinais_por_dia'], 1) + '/dia',
             'um a cada %s barras' % n(I['barras_entre_sinais']))):
        a('<div class="cartao"><div class="r">%s</div><div class="v">%s</div>'
          '<div class="n">%s</div></div>' % (rot, val, nota))
    a('</div>')
    a('<p>Os dois lados saem equilibrados — %s sinais de alta contra %s de '
      'baixa. Um gatilho que disparasse muito mais para um lado estaria lendo '
      'a tendência do período, não a barra.</p>'
      % (n(I['absorcao_alta'] + I['divergencia_alta']),
         n(I['absorcao_baixa'] + I['divergencia_baixa'])))
    a('<p>As métricas do indicador, medidas <b>nas barras de sinal</b>:</p>')
    a('<div class="rolagem"><table><thead><tr><th>métrica</th><th>p10</th>'
      '<th>mediana</th><th>p90</th></tr></thead><tbody>')
    for rot, k in (('Resultado relativo (<code>resRel</code>)', 'res_rel'),
                   ('Esforço relativo (<code>esfRel</code>)', 'esf_rel'),
                   ('Agressão a favor (<code>qualRel</code>)', 'qual_rel'),
                   ('Eficiência', 'efic'),
                   ('Corpo / range', 'corpo_frac')):
        b = I[k]
        a('<tr><td>%s</td><td class="num">%s</td><td class="num"><b>%s</b></td>'
          '<td class="num">%s</td></tr>'
          % (rot, n(b['10%'], 2), n(b['50%'], 2), n(b['90%'], 2)))
    a('</tbody></table></div>')
    a('<p>A mediana de <code>resRel</code> nos sinais é %s, contra %s no '
      'universo inteiro: o indicador está mesmo selecionando barras que '
      'andaram menos que o normal da direção delas — que é o que a tese de '
      'absorção pede.</p>'
      % (n(I['res_rel']['50%'], 2), n(I['res_rel_todas']['50%'], 2)))

    # ---------------------------------------------------------------------- 5
    a('<h2 id="s5">5 · O sinal tem direção?</h2>')
    a('<h3>5.1 · A excursão pura, contra dois controles sorteados</h3>')
    a('<p>Sem nenhuma regra de saída: a partir do fechamento da barra de '
      'sinal, até onde o preço vai a favor (MFE) e contra (MAE). Se o gatilho '
      'carrega direção, esses números têm de diferir dos de uma entrada '
      'sorteada.</p>')
    a(bloco_excursao(r))
    a('<p><b>Nada.</b> A razão MFE/MAE do sinal fica colada em 1,00, igual à '
      'das entradas sorteadas, e nenhuma deriva chega perto de significância. '
      'Se o estudo parasse aqui — e é aqui que a maioria para — a conclusão '
      'seria que o indicador não serve. O problema é que essas medidas olham '
      '5, 20 e 40 barras à frente, e a vantagem do gatilho não dura tanto.</p>')
    a('<h3>5.2 · A linha de base: o gráfico já vem inclinado</h3>')
    a('<p>Num gráfico de range dá para medir a direção da barra seguinte '
      '<b>sem ambiguidade nenhuma</b> (§3.1): basta perguntar se ela percorre '
      'meio range para cima ou para baixo a partir do próprio open. Isso '
      'permite medir a taxa de continuação no arquivo inteiro, e não só nos '
      'sinais — que é o controle que faltava.</p>')
    a(bloco_linha_base(r))
    a('<p>Duas leituras, e as duas importam. Primeiro: <b>o gráfico de range '
      'tem momentum de fábrica</b>, %s com z = %s. Segundo: <b>o indicador '
      'acrescenta %s pontos por cima do controle emparelhado</b>, com z = %s. '
      'É essa segunda linha que justifica o indicador — sem ela, os %s da V8 '
      'seriam apenas o momentum do gráfico com um enfeite.</p>'
      % (pct(LB['grupos'][0]['acerto'], 2), fmt(LB['grupos'][0]['z'], 2),
         fmt(100 * LB['ganho']['diferenca'], 1), fmt(LB['ganho']['z'], 2),
         pct(s8['acerto'])))

    # ---------------------------------------------------------------------- 6
    a('<h2 id="s6">6 · A busca por um filtro</h2>')
    a('<p>%s filtros testados, todos com a métrica neutra de meio range. A '
      'coluna <i>z (1R)</i> repete a medição com stop e alvo de um range '
      'inteiro — publicar as duas evita escolher a métrica depois de ver o '
      'resultado.</p>' % n(len(cands)))
    a(bloco_busca(r))
    a('<p>O que sobra é claro: <b>as primeiras posições são todas variações do '
      'mesmo filtro de esforço</b>, e nenhum outro conceito chega perto. Um '
      'resultado de busca em que o topo é ocupado por um só conceito, em '
      'várias calibragens, é bem diferente de um em que o topo é um número '
      'solitário — o segundo caso é o retrato de um acaso.</p>')
    a('<p>Ainda assim, <code>z = %s</code> é o máximo de %s tentativas, e é '
      'assim que tem de ser lido. O §7 aplica a esse filtro a mesma disciplina '
      'que reprovou o horário.</p>'
      % (fmt(max(b['z'] for b in cands), 2), n(len(cands))))

    # ---------------------------------------------------------------------- 7
    a('<h2 id="s7">7 · O filtro de esforço, sob validação</h2>')
    a('<p><b>A tese.</b> Uma barra que virou o movimento <b>com pouca gente '
      'negociando</b> é a forma mais pura da absorção: não houve briga, o '
      'preço andou porque não havia nada do outro lado. O filtro exige que o '
      'esforço total da barra fique abaixo de %s da média das barras da mesma '
      'direção. Repare que a tese vem <i>antes</i> do número — não é um limiar '
      'procurado às cegas.</p>' % pct(EF['limite']))
    a('<p>Um filtro escolhido no melhor de %s tentativas só merece crédito se '
      'passar em quatro testes independentes.</p>' % n(len(cands)))
    a('<h3>(a) É platô, não pico</h3>')
    a('<p>Um parâmetro que só funciona no valor exato em que foi encontrado é '
      'ajuste à amostra.</p>')
    a(bloco_plato(r))
    a('<p>Platô. De 0,60 a 0,80 o acerto fica numa faixa estreita e a '
      'degradação para fora é suave e monotônica. O valor publicado não é um '
      'pico; é o meio de uma faixa larga.</p>')
    a('<h3>(b) Aparece em todos os pedaços da amostra</h3>')
    a(bloco_pedacos(r))
    a('<p>As duas metades ficam a menos de meio ponto uma da outra, e os três '
      'terços sobem de %s para %s. Nenhum pedaço carrega o resultado sozinho — '
      'que é o modo mais comum de um filtro falso passar despercebido.</p>'
      % (pct(EF['tercos'][0]['acerto']), pct(EF['tercos'][2]['acerto'])))
    a('<p><b>(c) O controle invertido é o espelho exato.</b> Operando o lado '
      'oposto, o acerto vai a %s e a expectativa a %s ticks — a simetria '
      'perfeita da V8. A vantagem é de <b>direção</b>, e não de um viés de '
      'contabilidade que sobreviveria à inversão.</p>'
      % (pct(EF['invertido']['acerto']),
         fmt(EF['invertido']['expectativa_ticks'], 1)))
    a('<h3>(d) Não é um disfarce de horário</h3>')
    a('<p>Se o filtro estivesse apenas selecionando as horas calmas, a '
      'vantagem sumiria dentro de cada hora. Ele passa %s dos sinais, com a '
      'fração variando de %s a %s entre as horas, e a vantagem aparece em %s '
      'das %s horas com pelo menos 15 operações. Funciona também nos dois '
      'tipos de sinal (absorção %s, divergência %s) e nos dois lados '
      '(compra %s, venda %s).</p>'
      % (pct(I['pct_esforco_baixo']),
         pct(min(EF['fracao_por_hora'].values())),
         pct(max(EF['fracao_por_hora'].values())),
         n(sum(1 for h in EF['por_hora'] if h['acerto'] > 0.5)),
         n(len(EF['por_hora'])),
         pct(EF['por_tipo']['1']['acerto']), pct(EF['por_tipo']['2']['acerto']),
         pct(EF['por_lado']['long']['acerto']),
         pct(EF['por_lado']['short']['acerto'])))
    a('<div class="destaque"><p>Quatro testes, quatro aprovações. É o máximo '
      'que uma amostra só permite afirmar — e não substitui um teste em tempo '
      'real.</p></div>')

    # ---------------------------------------------------------------------- 8
    a('<h2 id="s8">8 · O horário, que não passou</h2>')
    a('<p>A estratégia pedia segregação por horário. As horas foram escolhidas '
      'em uma metade da amostra (mínimo de 25 operações e acerto acima de '
      '53%) e testadas na outra, nos dois sentidos.</p>')
    a(bloco_horario(r))
    a('<p><b>Reprovado.</b> Fora da amostra, as horas escolhidas não batem a '
      'referência — num dos sentidos ficam <i>abaixo</i> dela. A interseção '
      'entre as duas escolhas é de apenas %s hora(s), compatível com '
      'sorteio.</p>' % n(len(HR['intersecao'])))
    a('<p>A V5 está publicada com essas horas para que se veja o que acontece: '
      'dentro da amostra ela mede %s de acerto e parece ótima. É exatamente '
      'esse número que a validação cruzada existe para desmontar — e é o mesmo '
      'tipo de número que, no §7, sobreviveu.</p>'
      % pct(V['V5']['stats']['acerto']))
    a('<div class="painel">')
    a('<h4>expectativa por hora, na variante escolhida</h4>')
    a('<canvas id="cvHoras"></canvas>')
    a('<div class="legenda"><span>a opacidade da barra cresce com o número de '
      'operações naquela hora</span></div>')
    a('</div>')

    # ---------------------------------------------------------------------- 9
    a('<h2 id="s9">9 · Os parâmetros do próprio indicador</h2>')
    a('<p>Um gatilho cujo resultado desaba quando o parâmetro anda 10% não foi '
      'medido: foi ajustado. Cada linha abaixo recalcula o indicador do zero e '
      'mede com a seleção da V8.</p>')
    a(bloco_sens_ind(r))
    a('<div class="ok"><p>Todos os seis parâmetros são platôs. Em nenhum deles '
      'o valor padrão é o melhor da varredura, e em nenhum a variação chega a '
      'mudar a conclusão. Isso é evidência forte de que o indicador <b>não foi '
      'ajustado a este histórico</b> — o que faz sentido, já que ele foi '
      'portado de um NTSL escrito antes e para outro contexto.</p></div>')
    a('<p>Dois valores mediram melhor que o padrão de forma consistente: '
      '<code>fator_res</code> em 0,50 e <code>fator_qual</code> em 0,20–0,35. '
      'Ambos tornam o gatilho <b>mais exigente</b>, o que é coerente com a '
      'tese. Não são recomendados aqui: mexer neles depois de ver esta tabela '
      'é a definição de ajuste à amostra.</p>')

    # --------------------------------------------------------------------- 10
    a('<h2 id="s10">10 · A gestão, e por que o alvo é curto</h2>')
    a('<p>Aqui a seleção está fixa (esforço baixo) e o que varia é a saída. A '
      'última coluna marca as gestões em que a ambiguidade dentro da barra não '
      'existe (§3.1) — nelas o número não depende de suposição nenhuma.</p>')
    a(bloco_gestao(r))
    a('<p>A leitura é inequívoca. Em R por operação, o meio range paga %s, um '
      'range inteiro paga %s e dois ranges pagam %s. <b>A vantagem do gatilho '
      'existe por uma barra e se dissolve depois.</b></p>'
      % (fmt(g_meio['expectativa_R'], 3), fmt(g_um['expectativa_R'], 3),
         fmt(g_dois['expectativa_R'], 3)))
    a('<p>A linha de 1/4 de range (%s de acerto, t = %s) parece contradizer o '
      'resto, e não contradiz: ela é a única da tabela em que os dois lados '
      'cabem dentro da mesma barra, então a ambiguidade volta com força total '
      'e a convenção pessimista decide quase todas as operações contra. É um '
      'artefato da convenção, não uma medida — e serve para mostrar que a '
      'propriedade do §3.1 vale exatamente em meio range, não em qualquer '
      'alvo curto.</p>'
      % (pct(r['gestao'][0]['acerto']), fmt(r['gestao'][0]['t_stat'], 2)))

    # --------------------------------------------------------------------- 11
    a('<h2 id="s11">11 · As variantes</h2>')
    a(bloco_variantes(r))
    for v in r['variantes']:
        a('<p><b>%s · %s</b> — %s</p>' % (v['nome'], v['rotulo'], v['descricao']))
    a('<h3>Sensibilidade de cada variante</h3>')
    a('<p>Expectativa por operação, em ticks, sob cada hipótese.</p>')
    a(bloco_sensibilidade(r))
    a('<p>Repare nas colunas <i>pessimista</i> e <i>otimista</i> da V7 e da '
      'V8: são <b>idênticas</b>. É a propriedade do §3.1 aparecendo na '
      'tabela — nessas duas variantes não há hipótese a escolher.</p>')

    # --------------------------------------------------------------------- 12
    a('<h2 id="s12">12 · Operação a operação</h2>')
    a('<p>O painel de cima é o preço; o de baixo é o que o indicador '
      'realmente lê. A <b>barra cinza</b> é o <b>esforço</b> — a agressão '
      'somada dos dois lados, que alimenta o filtro da V8. A <b>barra '
      'colorida por dentro</b> é o <b>delta</b>, a agressão líquida, que '
      'alimenta os dois sinais. As duas cabem na mesma escala porque o delta '
      'nunca passa do esforço.</p>')
    a('<p>Desenhar compradora para cima e vendedora para baixo seria o '
      'óbvio, e não informaria nada: as duas séries têm correlação de %s '
      'neste arquivo e o gráfico viraria um espelho quase perfeito em toda '
      'barra. Numa barra de sinal da V8, procure a <b>barra cinza baixa</b> — '
      'é o filtro de esforço aparecendo a olho.</p>'
      % n(P['correlacao_agressoes'], 3))
    a('<p>As setas repetem as do <code>.mq5</code>: verde e vermelha para '
      'absorção, azul para divergência. A seta cheia é o sinal da operação em '
      'exibição; as esmaecidas são outros sinais da janela. Use as setas do '
      'teclado para navegar.</p>')
    a('<div class="painel">')
    a('<div class="barras">')
    a('<label>variante <select id="selVar">%s</select></label>' % opcoes_var)
    a('<label>desfecho <select id="selMot">'
      '<option value="*">todos</option><option value="alvo">alvo</option>'
      '<option value="stop">stop</option>'
      '<option value="breakeven">breakeven</option>'
      '<option value="tempo">aberta no fim</option></select></label>')
    a('<label>lado <select id="selLado">'
      '<option value="*">ambos</option><option value="long">compra</option>'
      '<option value="short">venda</option></select></label>')
    a('<label>sinal <select id="selTipo">'
      '<option value="*">ambos</option><option value="1">absorção</option>'
      '<option value="2">divergência</option></select></label>')
    a('<span class="nav"><button id="btPrev">←</button>'
      '<button id="btProx">→</button>'
      '<span class="conta" id="conta"></span></span>')
    a('</div>')
    a('<p class="conta" id="descVar" style="margin:0 0 10px"></p>')
    a('<canvas id="cvKline"></canvas>')
    a('<div class="ficha" id="ficha"></div>')
    a('<div class="legenda">'
      '<span><i style="background:#8a8a8a"></i>esforço total (barra cinza)</span>'
      '<span><i style="background:#1a7f5a"></i>delta comprador</span>'
      '<span><i style="background:#b3453a"></i>delta vendedor</span>'
      '<span><i style="background:#3d72b8"></i>divergência no pivô</span>'
      '</div>')
    a('</div>')
    a('<div class="painel">')
    a('<h4>curva de resultado acumulado da variante</h4>')
    a('<canvas id="cvCurva"></canvas>')
    a('</div>')

    # --------------------------------------------------------------------- 13
    a('<h2 id="s13">13 · Restrições recomendadas</h2>')
    a('<ol>')
    a('<li><b>Operar a favor da barra de sinal, a mercado no fechamento '
      'dela.</b> A entrada limitada no meio do range abandona %s dos sinais e '
      'não compensa em preço o que perde em amostra.</li>'
      % pct(1 - V['V3']['stats']['taxa_ativacao']))
    a('<li><b>Exigir esforço abaixo de %s do normal da direção.</b> É a única '
      'restrição do estudo inteiro que passou em todos os controles. Sem ela o '
      'gatilho mede %s de acerto; com ela, %s.</li>'
      % (pct(EF['limite']), pct(s7['acerto']), pct(s8['acerto'])))
    a('<li><b>Alvo e stop a meio range (%s ticks).</b> Não por gosto: é onde a '
      'vantagem está, e é a única faixa sem ambiguidade.</li>'
      % n(r['range_nominal'] / 2))
    a('<li><b>Não esticar o alvo.</b> Em dois ranges a expectativa fica '
      'negativa.</li>')
    a('<li><b>Não filtrar por horário.</b> Reprovado fora da amostra (§8).</li>')
    a('<li><b>Não mexer nos parâmetros do indicador.</b> São platôs (§9); '
      'mexer depois de ver a tabela é ajustar à amostra.</li>')
    a('<li><b>Tratar o custo como a restrição dominante.</b> Com %s ticks de '
      'expectativa bruta, 20 ticks de custo consomem %s dela e 40 ticks a '
      'tornam negativa.</li>'
      % (fmt(s8['expectativa_ticks'], 1),
         pct(20 / s8['expectativa_ticks'])))
    a('</ol>')

    # --------------------------------------------------------------------- 14
    a('<h2 id="s14">14 · Glossário</h2>')
    a('<dl class="glos">%s</dl>' % glos)

    # --------------------------------------------------------------------- 15
    a('<h2 id="s15">15 · Limitações</h2>')
    a('<ul>')
    a('<li><b>Uma amostra, um ativo, %s pregões.</b> Tudo aqui é um único '
      'caminho do preço. Nenhuma quantidade de validação interna substitui um '
      'segundo histórico.</li>' % n(D['dias']))
    a('<li><b>A margem cabe dentro do spread.</b> %s ticks por operação, com '
      'risco de %s ticks, é %s R. É real e é pequeno.</li>'
      % (fmt(s8['expectativa_ticks'], 1), n(r['range_nominal'] / 2),
         fmt(s8['expectativa_R'], 3)))
    a('<li><b>O melhor de %s tentativas.</b> O filtro de esforço passou em '
      'quatro validações independentes — muito mais do que o horário '
      'conseguiu — mas continua tendo sido escolhido depois de olhar os '
      'dados.</li>' % n(len(cands)))
    a('<li><b>Slippage não está modelado.</b> A entrada é a mercado no '
      'fechamento de uma barra de range, que é justamente um instante de '
      'movimento. O cenário de 20–40 ticks de custo existe para cobrir isso.</li>')
    a('<li><b>A convenção de agressão é premissa, não fato medido</b> (§2).</li>')
    a('<li><b>O momentum de base pode não ser estável.</b> Os %s de '
      'continuação medidos no §5.2 são deste período. Se essa inclinação '
      'mudar, a vantagem da V8 muda junto, porque parte dela vem dali.</li>'
      % pct(LB['grupos'][0]['acerto'], 2))
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
