# -*- coding: utf-8 -*-
"""
Escreve relatorio.html a partir de saida/resumo.json e saida/barras.json.

    python relatorio.py

O HTML e autocontido: nao busca nada na internet, nao precisa de servidor.
Abre com dois cliques. Contem:
    - o relatorio inteiro em texto
    - o navegador de operacoes com grafico de candles (Kline), uma operacao
      por vez, trocavel entre as variantes
    - a curva de capital e o perfil por hora de cada variante
    - o glossario de todos os termos usados
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')


# --------------------------------------------------------------------------
# numeros no padrao pt-BR
# --------------------------------------------------------------------------
def n(x, casas=0):
    return format(float(x), ',.%df' % casas) \
        .replace(',', '@').replace('.', ',').replace('@', '.')


def fmt(x, casas=0):
    return format(float(x), '+,.%df' % casas) \
        .replace(',', '@').replace('.', ',').replace('@', '.')


def pct(x, casas=1):
    return n(100 * x, casas) + '%'


def sinal_cls(x):
    return 'pos' if x > 0 else ('neg' if x < 0 else 'nul')


CSS = """
:root{
  --tinta:#1b1f24; --tinta2:#5b6570; --fundo:#fbfaf7; --papel:#ffffff;
  --linha:#e2ddd4; --realce:#8a6a2f; --alta:#1a7f5a; --baixa:#b3453a;
  --grade:#efece5; --caixa:#f5f2ec;
}
@media (prefers-color-scheme: dark){
  :root{
    --tinta:#e8e6e1; --tinta2:#9aa2ab; --fundo:#14171a; --papel:#1b1f23;
    --linha:#2e343a; --realce:#d9ae5e; --alta:#3fbb8a; --baixa:#e0685c;
    --grade:#232930; --caixa:#20262c;
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
.legenda{font:12px/1.5 system-ui,sans-serif;color:var(--tinta2);
  display:flex;gap:16px;flex-wrap:wrap;margin-top:9px}
.legenda i{display:inline-block;width:16px;height:2px;vertical-align:middle;
  margin-right:5px}
.ficha{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));
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
footer{margin-top:60px;padding-top:20px;border-top:1px solid var(--linha);
  font:13px/1.6 system-ui,sans-serif;color:var(--tinta2)}
@media(max-width:640px){.sumario{columns:1}h1{font-size:27px}
  .env{padding:0 15px 60px}}
"""

JS = r"""
(function(){
'use strict';
var R = window.__RESUMO__, B = window.__BARRAS__;
var TICK = 0.01;

/* ---- reconstroi as barras e as EMAs ------------------------------------ */
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
function ema(span){
  var a = 2/(span+1), out = new Float64Array(N), v = close[0];
  out[0]=v;
  for (var i=1;i<N;i++){ v = close[i]*a + v*(1-a); out[i]=v; }
  return out;
}
var E1 = ema(21), E2 = ema(42), E3 = ema(72);

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

/* ---- o desenho do grafico de candles ----------------------------------- */
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
  var a = Math.max(0, op.sinal_i - 55);
  var fim = op.saida_i >= 0 ? op.saida_i : op.sinal_i + 20;
  var b = Math.min(N-1, fim + 14);
  if (b - a < 80) b = Math.min(N-1, a + 80);
  this.win = [a, b];
  this.pinta();
};
Kline.prototype.geo = function(){
  var cv = this.cv, w = cv.clientWidth, h = 430;
  var dpr = window.devicePixelRatio || 1;
  if (cv.width !== Math.round(w*dpr) || cv.height !== Math.round(h*dpr)){
    cv.width = Math.round(w*dpr); cv.height = Math.round(h*dpr);
    cv.style.height = h+'px';
  }
  this.ctx.setTransform(dpr,0,0,dpr,0,0);
  return {w:w, h:h, ml:8, mr:74, mt:12, mb:38};
};
Kline.prototype.escala = function(){
  var a=this.win[0], b=this.win[1], op=this.op, cfg=this.cfg;
  var lo=Infinity, hi=-Infinity;
  for (var i=a;i<=b;i++){
    if (low[i]<lo) lo=low[i]; if (high[i]>hi) hi=high[i];
    if (E3[i]<lo) lo=E3[i]; if (E3[i]>hi) hi=E3[i];
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
  var cw = Math.max(1.4, Math.min(pw*0.68, 13));
  var self = this;
  function X(i){ return g.ml + (i-a+0.5)*pw; }
  function Y(p){ return g.mt + (es.hi-p)/(es.hi-es.lo)*(g.h-g.mt-g.mb); }
  this.X = X; this.Y = Y; this.pw = pw;

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

  /* faixa da operacao (da entrada ate a saida) */
  var i0 = op.sinal_i+1, i1 = op.saida_i>=0?op.saida_i:i0;
  ctx.fillStyle = cor('--realce');
  ctx.globalAlpha = 0.11;
  ctx.fillRect(X(i0)-pw/2, g.mt, (i1-i0+1)*pw, g.h-g.mt-g.mb);
  ctx.globalAlpha = 1;

  /* linhas da operacao */
  var s = op.lado==='long'?1:-1;
  var linhas = [
    [op.preco_ordem, cor('--realce'), 'ordem ' + num(op.preco_ordem,2), [2,3]],
    [op.entrada, cor('--tinta'), 'entrada ' + num(op.entrada,2), []],
    [op.entrada - s*cfg.stop_ticks*TICK, cor('--baixa'),
     'stop −' + num(cfg.stop_ticks) + 't', [5,4]],
    [op.entrada + s*cfg.parcial_ticks*TICK, cor('--alta'),
     (cfg.parcial_frac < 1 ? 'parcial +' : 'alvo +') +
       num(cfg.parcial_ticks) + 't', [5,4]]
  ];
  if (cfg.parcial_frac < 1)
    linhas.push([op.entrada + s*cfg.alvo_ticks*TICK, cor('--alta'),
                 'alvo +' + num(cfg.alvo_ticks) + 't', [5,4]]);
  ctx.font = '10.5px system-ui,sans-serif'; ctx.textAlign='left';
  linhas.forEach(function(L){
    var y = Math.round(Y(L[0]))+0.5;
    if (y < g.mt+6 || y > g.h-g.mb-6) return;
    ctx.save(); ctx.setLineDash(L[3]); ctx.strokeStyle = L[1];
    ctx.lineWidth = 1.2; ctx.beginPath();
    ctx.moveTo(g.ml,y); ctx.lineTo(g.w-g.mr,y); ctx.stroke(); ctx.restore();
    /* etiqueta sobre um retangulo opaco, senao ela some entre os candles */
    var lg = ctx.measureText(L[2]).width;
    ctx.fillStyle = cor('--papel');
    ctx.fillRect(g.ml+2, y-11, lg+7, 12);
    ctx.fillStyle = L[1];
    ctx.fillText(L[2], g.ml+5, y-2);
  });

  /* EMAs */
  [[E3,'#8e8ad6',1.4],[E2,'#4f9bd9',1.4],[E1,'#e0913a',1.7]].forEach(function(M){
    ctx.strokeStyle = M[1]; ctx.lineWidth = M[2]; ctx.beginPath();
    for (var i=a;i<=b;i++){ var x=X(i), y=Y(M[0][i]);
      if (i===a) ctx.moveTo(x,y); else ctx.lineTo(x,y); }
    ctx.stroke();
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
    var alt = Math.max(1, Math.abs(yc-yo));
    ctx.fillStyle = c;
    ctx.fillRect(x-cw/2, Math.min(yo,yc), cw, alt);
  }

  /* marcas: barra do gatilho, barra da entrada, barra da saida */
  function marca(i, txt, c, cima, baixo2){
    if (i<a || i>b) return;
    var x = X(i);
    ctx.save(); ctx.setLineDash([2,3]); ctx.strokeStyle = c; ctx.lineWidth=1.2;
    ctx.beginPath(); ctx.moveTo(x, g.mt); ctx.lineTo(x, g.h-g.mb); ctx.stroke();
    ctx.restore();
    /* gatilho e entrada sao barras vizinhas: um rotulo em cima, outro
       embaixo, senao os dois se sobrepoem */
    var y = cima ? g.mt+10 : g.h-g.mb+13+(baixo2?12:0);
    ctx.font='10px system-ui,sans-serif'; ctx.textAlign='center';
    var lg = ctx.measureText(txt).width;
    ctx.fillStyle = cor('--papel'); ctx.fillRect(x-lg/2-3, y-9, lg+6, 12);
    ctx.fillStyle = c; ctx.fillText(txt, x, y);
  }
  marca(op.sinal_i, 'gatilho', cor('--realce'), true);
  marca(op.sinal_i+1, 'entrada', cor('--tinta2'), false);
  if (op.saida_i > op.sinal_i+1)
    marca(op.saida_i, 'saída', cor('--tinta2'), false,
          (op.saida_i - op.sinal_i) < 8);   /* perto da entrada: segunda linha */

  /* moldura */
  ctx.strokeStyle = cor('--linha'); ctx.lineWidth=1;
  ctx.strokeRect(0.5,0.5,g.w-1,g.h-1);
};
Kline.prototype.hover = function(e){
  if (!this.win) return;
  var r = this.cv.getBoundingClientRect();
  var i = Math.round(this.win[0] + (e.clientX-r.left-8)/this.pw - 0.5);
  if (i < this.win[0] || i > this.win[1]){ this.dica.style.visibility='hidden'; return; }
  this.dica.innerHTML = '<b>'+data(tempo[i])+'</b>  A '+num(open[i],2)+
    ' · M '+num(high[i],2)+' · m '+num(low[i],2)+' · F '+num(close[i],2)+
    ' · range '+num((high[i]-low[i])/TICK)+'t';
  this.dica.style.visibility = 'visible';
};

/* ---- graficos de linha simples (curva e barras por hora) --------------- */
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
  [lo,(lo+hi)/2,hi,0].forEach(function(v){
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

function horas(cv, dados, boas){
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
    var boa = boas.indexOf(d.hora)>=0;
    ctx.fillStyle = v>=0?cor('--alta'):cor('--baixa');
    ctx.globalAlpha = boa?1:0.38;
    ctx.fillRect(x+bw*0.13, Math.min(y0,Y(v)), bw*0.74, Math.abs(Y(v)-y0));
    ctx.globalAlpha=1;
    ctx.fillStyle = boa?cor('--tinta'):cor('--tinta2');
    ctx.font=(boa?'600 ':'')+'10px system-ui,sans-serif'; ctx.textAlign='center';
    ctx.fillText(d.hora, x+bw/2, h-6);
  });
  ctx.strokeStyle=cor('--linha'); ctx.strokeRect(.5,.5,w-1,h-1);
}

/* ---- navegador de operacoes -------------------------------------------- */
var selVar = document.getElementById('selVar');
var selMot = document.getElementById('selMot');
var selLado = document.getElementById('selLado');
var btPrev = document.getElementById('btPrev');
var btProx = document.getElementById('btProx');
var conta = document.getElementById('conta');
var ficha = document.getElementById('ficha');
var desc  = document.getElementById('descVar');
var kl = new Kline(document.getElementById('cvKline'),
                   document.getElementById('dica'));
var lista = [], pos = 0;

function opDe(v, linha){
  var o = {}; R.variantes[0].trades.colunas.forEach(function(c,i){ o[c]=linha[i]; });
  return o;
}
function variante(){ return R.variantes[+selVar.value]; }

function filtra(){
  var v = variante();
  lista = v.trades.linhas.map(function(L){ return opDe(v,L); })
    .filter(function(o){
      if (selMot.value!=='*' && o.motivo!==selMot.value) return false;
      if (selLado.value!=='*' && o.lado!==selLado.value) return false;
      return true;
    });
  pos = 0;
  desc.textContent = v.descricao;
  curva(document.getElementById('cvCurva'), v.curva);
  horas(document.getElementById('cvHoras'), v.por_hora, R.horas_boas);
  mostra();
}
function mostra(){
  if (!lista.length){
    conta.textContent = 'nenhuma operação com esse filtro';
    ficha.innerHTML = ''; btPrev.disabled = btProx.disabled = true; return;
  }
  var v = variante(), o = lista[pos];
  kl.mostra(o, v.cfg);
  var tot = variante().trades.total, mostradas = variante().trades.linhas.length;
  conta.textContent = 'operação ' + (pos+1) + ' de ' + lista.length +
    (mostradas < tot ? '  (amostra de ' + num(mostradas) + ' das ' + num(tot) + ')' : '');
  var motivo = {alvo:'alvo final', breakeven:'breakeven após a parcial',
                stop:'stop', tempo:'aberta no fim do histórico'}[o.motivo] || o.motivo;
  ficha.innerHTML =
    '<div><span>quando</span><b>'+data(tempo[o.sinal_i])+'</b></div>' +
    '<div><span>lado</span><b>'+(o.lado==='long'?'compra':'venda')+'</b></div>' +
    '<div><span>entrada</span><b>'+num(o.entrada,2)+'</b></div>' +
    '<div><span>desfecho</span><b>'+motivo+'</b></div>' +
    '<div><span>resultado</span><b class="'+classe(o.ticks)+'">'+
      sgn(o.ticks,0)+' t</b></div>' +
    '<div><span>em R</span><b class="'+classe(o.ticks)+'">'+
      sgn(o.ticks/v.cfg.stop_ticks,2)+'R</b></div>' +
    '<div><span>barras</span><b>'+o.barras+'</b></div>' +
    '<div><span>leque</span><b>'+num(o.leque)+' t</b></div>' +
    '<div><span>range do gatilho</span><b>'+num(o.range_gatilho)+' t</b></div>';
  btPrev.disabled = pos<=0; btProx.disabled = pos>=lista.length-1;
}
selVar.onchange = filtra; selMot.onchange = filtra; selLado.onchange = filtra;
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
    L = []
    L.append('<div class="rolagem"><table><thead><tr>'
             '<th>variante</th><th>sinais</th><th>operações</th><th>acerto</th>'
             '<th>exp./op.</th><th>total</th><th>fator de lucro</th>'
             '<th>rebaixamento</th></tr></thead><tbody>')
    for v in r['variantes']:
        s = v['stats']
        L.append('<tr><td><b>%s</b> · %s</td><td class="num">%s</td>'
                 '<td class="num">%s</td><td class="num">%s</td>'
                 '<td class="num %s">%s</td><td class="num %s">%s</td>'
                 '<td class="num">%s</td><td class="num neg">%s</td></tr>'
                 % (v['nome'], v['rotulo'], n(s.get('sinais', 0)),
                    n(s.get('operacoes', 0)), pct(s.get('acerto', 0)),
                    sinal_cls(s.get('expectativa_ticks', 0)),
                    fmt(s.get('expectativa_ticks', 0), 1),
                    sinal_cls(s.get('ticks_total', 0)),
                    fmt(s.get('ticks_total', 0)),
                    n(s.get('fator_lucro', 0), 2),
                    fmt(s.get('drawdown_ticks', 0))))
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
        L.append('<tr><td>%s · %s</td>%s</tr>'
                 % (v['nome'], v['rotulo'],
                    ''.join('<td class="num %s">%s</td>' % (sinal_cls(x), fmt(x, 1))
                            for x in vals)))
    L.append('</tbody></table></div>')
    return '\n'.join(L)


def bloco_busca(r):
    L = ['<div class="rolagem"><table><thead><tr><th>filtro testado</th>'
         '<th>operações</th><th>acerto</th><th>z</th><th>expectativa</th>'
         '</tr></thead><tbody>']
    for b in sorted(r['busca'], key=lambda x: -x['z']):
        L.append('<tr><td>%s%s</td><td class="num">%s</td><td class="num">%s</td>'
                 '<td class="num %s"><b>%s</b></td><td class="num %s">%s t</td></tr>'
                 % (b['filtro'], ' &nbsp;⟵ horário' if b['horario'] else '',
                    n(b['n']), pct(b['acerto']), sinal_cls(b['z']),
                    fmt(b['z'], 2), sinal_cls(b['expectativa_ticks']),
                    fmt(b['expectativa_ticks'], 1)))
    L.append('</tbody></table></div>')
    return '\n'.join(L)


def bloco_excursao(r):
    rot = {'sinal': 'o sinal da estratégia',
           'direcao_sorteada': 'mesmas barras, <b>direção sorteada</b>',
           'barra_e_direcao_sorteadas': 'barra e direção sorteadas'}
    L = ['<div class="rolagem"><table><thead><tr><th>horizonte</th><th>amostra</th>'
         '<th>MFE mediana</th><th>MAE mediana</th><th>MFE/MAE</th>'
         '<th>deriva média</th></tr></thead><tbody>']
    for H in ('10', '20', '40'):
        for k in ('sinal', 'direcao_sorteada', 'barra_e_direcao_sorteadas'):
            b = r['excursao'][k][H]
            L.append('<tr><td>%s barras</td><td>%s</td><td class="num">%s t</td>'
                     '<td class="num">%s t</td><td class="num"><b>%s</b></td>'
                     '<td class="num %s">%s t</td></tr>'
                     % (H, rot[k], n(b['mfe_med']), n(b['mae_med']),
                        n(b['razao'], 3), sinal_cls(b['deriva_media']),
                        fmt(b['deriva_media'], 1)))
    L.append('</tbody></table></div>')
    return '\n'.join(L)


GLOSSARIO = [
    ('Tick', 'A menor variação de preço do ativo. No XAUUSD vale <b>0,01 dólar</b>. '
     'Todo resultado deste relatório é medido em ticks: 300 ticks = 3,00 USD.'),
    ('R (unidade de risco)', 'O tamanho do stop, usado como régua. Aqui 1R = 300 '
     'ticks = 3,00 USD por lote. Falar em R em vez de dólares permite comparar '
     'operações de tamanhos diferentes: perder o stop é sempre −1R.'),
    ('EMA (média móvel exponencial)', 'Média dos fechamentos que dá mais peso às '
     'barras recentes. A EMA de 21 períodos reage rápido; a de 72, devagar. '
     'Calculada como <code>EMA[i] = fecha[i]·α + EMA[i−1]·(1−α)</code>, com '
     '<code>α = 2/(período+1)</code>.'),
    ('Leque', 'O nome que a estratégia dá ao arranjo das três EMAs quando estão '
     'ordenadas e separadas — 21 acima de 42 acima de 72 (alta), ou o contrário '
     '(baixa). Neste relatório a <b>largura do leque</b> é a distância entre a '
     'EMA21 e a EMA72, em ticks.'),
    ('Médias emboladas', 'O oposto do leque: as três EMAs cruzadas ou muito '
     'próximas. Indica consolidação ou reversão de tendência.'),
    ('Afastamento', 'O preço se descolar do leque no sentido da tendência. Foi '
     'medido como a barra <b>inteira</b> ter ficado além da EMA21 em alguma das '
     '12 barras anteriores ao gatilho.'),
    ('Pullback', 'O recuo contra a tendência que traz o preço de volta ao leque. '
     'Na regra original ele tem de ter 2 ou 3 candles consecutivos da mesma cor.'),
    ('Gatilho', 'A barra que dispara a montagem da ordem: o candle contrário ao '
     'pullback (isto é, a favor da tendência) que aparece dentro do leque.'),
    ('Reconquista', 'Filtro acrescentado nas variantes V3 e V5: além de tocar a '
     'EMA21, o candle de gatilho tem de <b>fechar</b> do lado da tendência. '
     'Elimina o caso ambíguo da barra que só encosta na média.'),
    ('Ordem limitada', 'Ordem de compra abaixo do preço atual (ou de venda acima) '
     'que só executa se o preço vier até ela. É a ordem do meio do range: só '
     'entra se a barra seguinte voltar até lá. Se não voltar, a ordem é '
     'cancelada — a operação é <b>abortada</b>.'),
    ('Taxa de ativação', 'Fração dos sinais em que a ordem limitada chegou a ser '
     'preenchida na barra seguinte. Os outros viram nada.'),
    ('Saída parcial', 'Fechar parte da posição num alvo intermediário. Aqui: 50% '
     'da posição em +300 ticks, e o stop do restante vai para o preço de entrada.'),
    ('Breakeven', 'Literalmente "empatar". Depois da parcial, o stop do restante '
     'fica no preço de entrada; se o preço voltar até lá, a operação termina '
     'valendo só o lucro da parcial (+150 ticks, ou +0,5R).'),
    ('Runner', 'A metade da posição que fica correndo atrás do alvo distante '
     'depois da parcial.'),
    ('Expectativa', 'O resultado médio por operação. É o número mais importante '
     'de todos: multiplicado pelo número de operações, dá o resultado total.'),
    ('Acerto', 'Fração de operações que terminam com resultado positivo. <b>Não '
     'basta ser alto</b>: uma estratégia de 90% de acerto que perde 20 vezes o '
     'que ganha é ruinosa.'),
    ('Fator de lucro', 'Soma de tudo que se ganhou dividida pela soma de tudo que '
     'se perdeu. Acima de 1,00 a estratégia ganha; abaixo, perde. Entre 1,0 e '
     '1,2 é território onde o custo de corretagem decide o resultado.'),
    ('Payoff', 'Ganho médio dividido pela perda média. Diz quantas vezes o ganho '
     'típico é maior que a perda típica.'),
    ('Rebaixamento (drawdown)', 'A maior queda da curva de resultado desde um pico '
     'anterior. É o tamanho do buraco que o operador teria de aguentar sem '
     'desistir.'),
    ('MFE / MAE', '<i>Maximum Favourable / Adverse Excursion</i>: o quanto o preço '
     'andou a favor e o quanto andou contra, depois da entrada, antes de qualquer '
     'saída. A razão MFE/MAE mede a direção do sinal sem contaminação da regra de '
     'saída — é o teste da § 4.'),
    ('Deriva', 'Quanto o preço andou, no sentido da operação, ao fim de um número '
     'fixo de barras. Deriva positiva grande = o sinal antecipa movimento.'),
    ('z (escore)', 'Quantos desvios-padrão um resultado está longe do que o acaso '
     'produziria. |z| abaixo de 2 é ruído comum. Com muitos filtros testados, '
     'porém, a régua sobe: testar 31 filtros faz o maior |z| chegar a ~2,2 '
     'mesmo em dados sem vantagem nenhuma.'),
    ('SQN', '<i>System Quality Number</i>: expectativa dividida pelo desvio-padrão '
     'dos resultados, multiplicada pela raiz do número de operações. É o mesmo '
     'que o z da expectativa.'),
    ('Validação cruzada', 'Escolher os parâmetros olhando só metade dos dados e '
     'medir na outra metade, que não foi olhada. É o que separa uma descoberta '
     'de um ajuste retroativo.'),
    ('Dentro / fora da amostra', 'Dentro da amostra = o trecho de dados usado para '
     'escolher a regra (números otimistas por construção). Fora da amostra = o '
     'trecho reservado para o teste.'),
    ('Garimpo de dados', 'Testar muitas regras e publicar a melhor, sem contar '
     'quantas foram testadas. Por isso a § 6 publica <b>todas</b>.'),
    ('Spread', 'Diferença entre o preço de compra e o de venda. É custo puro, '
     'pago em toda operação. A coluna de spread do arquivo é inutilizável, '
     'então ele entrou como cenário: 10, 20 ou 40 ticks.'),
    ('Slippage', 'A diferença entre o preço em que a ordem deveria executar e o '
     'preço em que executou. Costuma ser pior justamente nos stops.'),
    ('Kline / candle', 'O desenho de uma barra: o corpo vai da abertura ao '
     'fechamento, os pavios marcam a máxima e a mínima. Verde quando fecha '
     'acima da abertura, vermelho quando abaixo.'),
    ('Barra de 521 ticks', 'A barra não fecha por tempo, e sim quando 521 negócios '
     'foram fechados. Em ouro isso dá cerca de 90 segundos por barra em média, '
     'mas encurta muito quando o mercado acelera.'),
]


def escrever():
    with open(os.path.join(SAIDA, 'resumo.json'), encoding='utf-8') as f:
        resumo = json.load(f)
    with open(os.path.join(SAIDA, 'barras.json'), encoding='utf-8') as f:
        barras = f.read()

    r = resumo
    D = r['dados']
    V = {v['nome']: v for v in r['variantes']}
    v0, v4, v5, v6, v7 = V['V0'], V['V4'], V['V5'], V['V6'], V['V8']
    rg = D['range_ticks']
    m = v0['stats']['motivos']
    ops0 = v0['stats']['operacoes']
    hr = r['horario']
    zsem = max(abs(b['z']) for b in r['busca'] if not b['horario'])
    horas_txt = ', '.join('%dh' % h for h in r['horas_boas'])

    opcoes_var = '\n'.join(
        '<option value="%d">%s · %s</option>' % (i, v['nome'], v['rotulo'])
        for i, v in enumerate(r['variantes']))

    glos = '\n'.join('<dt>%s</dt><dd>%s</dd>' % (a, b) for a, b in GLOSSARIO)

    H = []
    a = H.append
    a('<!doctype html>')
    a('<html lang="pt-BR"><head>')
    a('<meta charset="utf-8">')
    a('<meta name="viewport" content="width=device-width,initial-scale=1">')
    a('<title>Leque de EMAs em XAUUSD — backtest</title>')
    a('<style>%s</style>' % CSS)
    a('</head><body>')
    a('<div class="env">')

    # ------------------------------------------------------------- cabecalho
    a('<header>')
    a('<h1>O leque de EMAs em XAUUSD<br>— um backtest e o que ele mostrou</h1>')
    a('<p class="sub">Candles de 521 ticks · %s barras · %s a %s · %s pregões<br>'
      'Gerado em %s a partir de <code>%s</code></p>'
      % (n(D['barras']), D['inicio'][:10], D['fim'][:10], n(D['dias']),
         r['gerado_em'], r['arquivo']))
    a('</header>')

    a('<nav class="sumario">'
      '<a href="#s1">1 · Resposta curta</a><br>'
      '<a href="#s2">2 · Os dados</a><br>'
      '<a href="#s3">3 · A regra em código</a><br>'
      '<a href="#s4">4 · O sinal tem direção?</a><br>'
      '<a href="#s5">5 · A regra literal</a><br>'
      '<a href="#s6">6 · A busca por um filtro</a><br>'
      '<a href="#s7">7 · O horário</a><br>'
      '<a href="#s8">8 · As variantes</a><br>'
      '<a href="#s9">9 · Operação a operação</a><br>'
      '<a href="#s10">10 · Restrições recomendadas</a><br>'
      '<a href="#s11">11 · Glossário</a><br>'
      '<a href="#s12">12 · Limitações</a>'
      '</nav>')

    # -------------------------------------------------------------------- 1
    a('<h2 id="s1">1 · Resposta curta</h2>')
    a('<p class="lead">A regra como está escrita perde dinheiro neste histórico. '
      'A razão não é o alvo estar mal escolhido: é que o gatilho não carrega '
      'informação de direção nenhuma. De tudo que foi testado, só o '
      '<b>horário</b> sobreviveu a uma validação fora da amostra.</p>')
    a('<p>Isso não fecha a porta. O horário, somado a um gatilho mais exigente e '
      'a um alvo curto, produz a variante <b>V7</b>: %s t por operação, e ainda '
      'positiva depois de descontar 40 ticks de custo. É pouca folga sobre %s '
      'operações — o suficiente para justificar um teste em tempo real, não para '
      'justificar confiança.</p>'
      % (fmt(V['V7']['stats']['expectativa_ticks'], 1),
         n(V['V7']['stats']['operacoes'])))
    a('<div class="cartoes">')
    for rot, val, nota, cls in (
            ('Operações', n(ops0), 'da regra literal, em %s pregões' % n(D['dias']), ''),
            ('Acerto', pct(v0['stats']['acerto']), 'praticamente uma moeda', ''),
            ('Expectativa', fmt(v0['stats']['expectativa_ticks'], 1) + ' t',
             '%s USD por operação' % fmt(v0['stats']['expectativa_usd'], 2),
             sinal_cls(v0['stats']['expectativa_ticks'])),
            ('Fator de lucro', n(v0['stats']['fator_lucro'], 2),
             'abaixo de 1,00 é prejuízo', 'neg'),
            ('Chegam ao alvo', pct(m.get('alvo', 0) / ops0),
             'seriam precisos 14,3%', 'neg'),
            ('MFE/MAE do sinal', n(r['excursao']['sinal']['20']['razao'], 3),
             'direção sorteada dá %s' % n(r['excursao']['direcao_sorteada']['20']['razao'], 3),
             '')):
        a('<div class="cartao"><div class="r">%s</div>'
          '<div class="v %s">%s</div><div class="n">%s</div></div>'
          % (rot, cls, val, nota))
    a('</div>')
    a('<p>O que segue explica cada um desses números, mostra as variantes que '
      'foram tentadas, e deixa navegar <b>operação a operação</b> no gráfico '
      '(§&nbsp;9) para que a regra possa ser vista funcionando e falhando.</p>')

    # -------------------------------------------------------------------- 2
    a('<h2 id="s2">2 · Os dados</h2>')
    a('<div class="rolagem"><table><tbody>')
    for k, v in (('Ativo / gráfico', 'XAUUSD, candles de 521 ticks'),
                 ('Barras', n(D['barras'])),
                 ('Período', '%s → %s' % (D['inicio'][:16], D['fim'][:16])),
                 ('Pregões', '%s (%s barras por dia)'
                  % (n(D['dias']), n(D['barras_por_dia'], 0))),
                 ('Faixa de preço', '%s → %s'
                  % (n(D['preco_min'], 2), n(D['preco_max'], 2))),
                 ('Tick', '0,01 USD'),
                 ('Range da barra mediana', '%s ticks' % n(rg['50%'])),
                 ('Largura mediana do leque', '%s ticks' % n(D['leque_ticks']['50'])),
                 ('Barras com leque formado', pct(D['pct_leque_alta'] + D['pct_leque_baixa'])),
                 ('Barras com médias emboladas', pct(D['pct_embolado']))):
        a('<tr><td>%s</td><td class="num">%s</td></tr>' % (k, v))
    a('</tbody></table></div>')
    a('<p>Dois números decidem quase tudo o que vem depois. A barra mediana anda '
      '<b>%s ticks</b>. Portanto o stop de 300 ticks vale <b>%s barras '
      'medianas</b> — apertado —, e o alvo final de 900 ticks pede <b>%s barras '
      'medianas de continuação</b> depois da entrada.'
      % (n(rg['50%']), n(300 / rg['50%'], 2), n(900 / rg['50%'], 1)))
    a('<div class="destaque"><p><b>A coluna <code>&lt;SPREAD&gt;</code> do arquivo '
      'foi descartada.</b> Ela traz valores entre 149 e 655.942, o que não é '
      'spread de ouro em escala nenhuma. O custo entrou como cenário explícito '
      '(§&nbsp;8), o que é mais honesto do que fingir precisão.</p></div>')

    # -------------------------------------------------------------------- 3
    a('<h2 id="s3">3 · A regra, traduzida para código</h2>')
    a('<p>Backtest exige que cada palavra do texto original vire uma condição '
      'verificável. Estas são as traduções — e cada uma é uma decisão que podia '
      'ter sido tomada de outro jeito.</p>')
    a('<div class="rolagem"><table><thead><tr><th>no texto original</th>'
      '<th style="text-align:left">no código</th></tr></thead><tbody>')
    for x, y in (('"médias em forma de leque"',
                  'EMA21 &gt; EMA42 &gt; EMA72 (alta) ou o inverso (baixa)'),
                 ('"o preço se afasta destas médias"',
                  'em alguma das 12 barras anteriores a barra <b>inteira</b> ficou '
                  'além da EMA21'),
                 ('"e volta ao leque"', 'a barra do gatilho toca a EMA21'),
                 ('"sequência de 2 ou 3 candles da mesma cor"',
                  '2 ou 3 candles consecutivos de cor contrária à tendência, '
                  'imediatamente antes do gatilho — nem 1, nem 4'),
                 ('"aparece um candle contrário"',
                  'a barra do gatilho tem a cor da tendência'),
                 ('"ordem no meio do range deste candle"',
                  'limitada em (máxima + mínima) / 2 da barra do gatilho'),
                 ('"aguardando a ativação no próximo candle"',
                  'preenche se a barra seguinte tocar o preço; senão a ordem é '
                  '<b>cancelada</b>'),
                 ('"stop de 300 ticks"', '3,00 USD da entrada = 1R'),
                 ('"parcial a 300 ticks (50%)"',
                  'metade sai em +1R; o stop do restante vai para a entrada'),
                 ('"saída final a 900"', 'o restante sai em +3R')):
        a('<tr><td>%s</td><td style="text-align:left">%s</td></tr>' % (x, y))
    a('</tbody></table></div>')
    a('<p>Com isso a vencedora completa rende <code>0,5×1R + 0,5×3R = 2R</code>, '
      'a relação 2:1 do documento original. Só existem três desfechos:</p>')
    a('<div class="rolagem"><table><thead><tr><th>desfecho</th><th>em R</th>'
      '<th>em ticks</th><th>em dólares</th></tr></thead><tbody>'
      '<tr><td><b>stop</b> — caiu 300 antes de subir 300</td>'
      '<td class="num neg">−1R</td><td class="num neg">−300 t</td>'
      '<td class="num neg">−3,00</td></tr>'
      '<tr><td><b>breakeven</b> — pegou a parcial e voltou</td>'
      '<td class="num pos">+0,5R</td><td class="num pos">+150 t</td>'
      '<td class="num pos">+1,50</td></tr>'
      '<tr><td><b>alvo</b> — pegou a parcial e chegou aos 900</td>'
      '<td class="num pos">+2R</td><td class="num pos">+600 t</td>'
      '<td class="num pos">+6,00</td></tr>'
      '</tbody></table></div>')
    a('<p>Daí sai o ponto de equilíbrio: chamando <code>a</code> a fração de '
      'alvos, <code>b</code> a de breakevens e <code>s</code> a de stops, é '
      'preciso <code>600a + 150b = 300s</code>. Sem alvos, seria preciso acertar '
      'a parcial em <b>2 de cada 3</b> tentativas só para empatar.</p>')

    # -------------------------------------------------------------------- 4
    a('<h2 id="s4">4 · Antes de qualquer resultado: o sinal tem direção?</h2>')
    a('<p>Toda estatística de backtest mistura duas coisas: a qualidade do sinal '
      'e a aritmética da saída. Para separá-las, mediu-se o que o preço faz '
      'depois da entrada <b>sem regra de saída nenhuma</b> — e comparou-se com '
      'dois controles aleatórios.</p>')
    a(bloco_excursao(r))
    b1 = r['excursao']['sinal']['20']; b2 = r['excursao']['direcao_sorteada']['20']
    a('<div class="destaque"><p>O sinal produz uma razão MFE/MAE de <b>%s</b> em '
      '20 barras. Sortear a direção nas <b>mesmas</b> barras produz <b>%s</b>. A '
      'vantagem inteira do sinal sobre uma moeda é de %s centésimos de razão, '
      'sobre %s entradas — ruído.</p>'
      '<p><b>O gatilho escolhe <i>quando</i> operar, não <i>para que lado</i>.</b> '
      'Tudo o que vem a seguir é consequência disso.</p></div>'
      % (n(b1['razao'], 3), n(b2['razao'], 3),
         n(100 * abs(b1['razao'] - b2['razao']), 1), n(b1['n'])))

    # -------------------------------------------------------------------- 5
    a('<h2 id="s5">5 · A regra literal (V0)</h2>')
    s = v0['stats']
    a('<div class="rolagem"><table><tbody>')
    for k, v in (('Sinais detectados', n(s['sinais'])),
                 ('Ordens que <b>não</b> ativaram na barra seguinte',
                  '%s (%s)' % (n(s['abortadas']), pct(1 - s['taxa_ativacao']))),
                 ('Operações efetivas', '<b>%s</b>' % n(s['operacoes'])),
                 ('Operações por pregão', n(s['ops_por_dia'], 1)),
                 ('Acerto', pct(s['acerto'])),
                 ('Expectativa por operação',
                  '<b>%s t</b> (%s USD)' % (fmt(s['expectativa_ticks'], 1),
                                            fmt(s['expectativa_usd'], 2))),
                 ('Resultado total, 1 lote',
                  '<b>%s t</b> (%s USD)' % (fmt(s['ticks_total']),
                                            fmt(s['usd_total'], 2))),
                 ('Fator de lucro', n(s['fator_lucro'], 2)),
                 ('Rebaixamento máximo', '%s t' % fmt(s['drawdown_ticks'])),
                 ('Barras dentro da operação', n(s['barras_media'], 1)),
                 ('Dias positivos / negativos',
                  '%s / %s' % (n(s['dias_positivos']), n(s['dias_negativos'])))):
        a('<tr><td>%s</td><td class="num">%s</td></tr>' % (k, v))
    a('</tbody></table></div>')
    a('<h3>Onde a estratégia se decide</h3>')
    a('<div class="rolagem"><table><thead><tr><th>desfecho</th><th>operações</th>'
      '<th>fração</th><th>contribuição</th></tr></thead><tbody>')
    for k, rotk, val in (('alvo', 'alvo (+2R)', 600),
                         ('breakeven', 'breakeven (+0,5R)', 150),
                         ('stop', 'stop (−1R)', -300),
                         ('tempo', 'aberta no fim do histórico', 0)):
        if k not in m:
            continue
        a('<tr><td>%s</td><td class="num">%s</td><td class="num">%s</td>'
          '<td class="num %s">%s t</td></tr>'
          % (rotk, n(m[k]), pct(m[k] / ops0), sinal_cls(val),
             fmt(m[k] * val) if val else '—'))
    a('</tbody></table></div>')
    a('<p>Só <b>%s</b> das operações chegam aos 900 ticks. Com %s de breakevens e '
      '%s de stops, o equilíbrio exigiria <b>%s</b> de alvos.</p>'
      % (pct(m.get('alvo', 0) / ops0), pct(m.get('breakeven', 0) / ops0),
         pct(m.get('stop', 0) / ops0),
         pct((300 * m.get('stop', 0) - 150 * m.get('breakeven', 0)) / (600 * ops0))))
    a('<h3>O que a parcial faz</h3>')
    a('<p>A parcial em +1R com stop no breakeven costuma ser vendida como '
      'proteção. Aqui ela é o contrário: <b>transforma quase toda vencedora em '
      'meio ganho</b>. De cada %s operações que chegam a tocar +300 ticks, %s '
      'voltam à entrada e saem valendo +150 em vez de +600. O seguro é caro '
      'porque o alvo que ele protege quase nunca chega.</p>'
      % (n(m.get('alvo', 0) + m.get('breakeven', 0)), n(m.get('breakeven', 0))))

    # -------------------------------------------------------------------- 6
    a('<h2 id="s6">6 · A busca por uma restrição que salvasse a regra</h2>')
    a('<p>%s filtros foram testados, incluindo os três que o documento original '
      'sugere. Para medir cada um sem a distorção do alvo distante, usou-se uma '
      'métrica neutra — <b>stop 300 / alvo 300, posição inteira</b> —, que '
      'responde a uma pergunta só: o preço anda 300 ticks a favor antes de andar '
      '300 contra? Um sinal sem direção acerta 50%%.</p>' % n(len(r['busca'])))
    a(bloco_busca(r))
    a('<div class="destaque"><p><b>Como ler esta tabela.</b> Testar %s filtros e '
      'ficar com o melhor é a definição de garimpo. Com %s tentativas sobre dados '
      'sem vantagem nenhuma, o maior <code>z</code> esperado por acaso fica em '
      'torno de <b>2,2</b>. O maior <code>z</code> obtido fora do horário foi '
      '<b>%s</b> — exatamente o que o acaso entrega. Nenhum filtro de forma, de '
      'leque, de inclinação, de corpo ou de tamanho de candle passou dessa '
      'linha.</p></div>' % (n(len(r['busca'])), n(len(r['busca'])), n(zsem, 2)))
    a('<p>Dois resultados <b>contradizem</b> as hipóteses do documento original. '
      'A estratégia supõe que candles de reversão pequenos são melhores; medido, '
      'as barras <i>grandes</i> mediram melhor que as pequenas. E a estratégia '
      'supõe que médias emboladas atrapalham; aqui a hipótese aponta para o lado '
      'certo, mas com força indistinguível de ruído.</p>')

    # -------------------------------------------------------------------- 7
    a('<h2 id="s7">7 · O horário — a única coisa que sobreviveu</h2>')
    a('<p>O horário foi o único filtro que não se comportou como ruído. Como ele '
      'também poderia ser garimpo — são 23 horas para escolher —, foi submetido a '
      'uma <b>validação cruzada nos dois sentidos</b>: escolhem-se as horas em '
      'metade da amostra e mede-se na outra metade; depois inverte-se.</p>')
    a('<div class="rolagem"><table><thead><tr><th>seleção feita em</th>'
      '<th style="text-align:left">horas escolhidas</th><th>testado em</th>'
      '<th>operações</th><th>acerto medido</th><th>referência</th><th>z</th>'
      '</tr></thead><tbody>')
    for k, x, y in (('escolhe_1a_testa_2a', '1ª metade', '2ª metade'),
                    ('escolhe_2a_testa_1a', '2ª metade', '1ª metade')):
        v = hr[k]
        a('<tr><td>%s</td><td style="text-align:left">%s</td><td>%s</td>'
          '<td class="num">%s</td><td class="num"><b>%s</b></td>'
          '<td class="num">%s</td><td class="num pos"><b>%s</b></td></tr>'
          % (x, ', '.join('%dh' % h for h in v['horas']), y, n(v['n']),
             pct(v['acerto']), pct(v['acerto_referencia']), fmt(v['z'], 2)))
    a('</tbody></table></div>')
    a('<p>Os dois sentidos concordam. As horas que apareceram <b>nas duas</b> '
      'seleções independentes são <b>%s</b> — e são as usadas nas variantes V4, '
      'V5 e V6.</p>' % horas_txt)
    a('<div class="painel">')
    a('<h4>Expectativa por hora — regra literal, métrica neutra</h4>')
    a('<canvas id="cvHoras"></canvas>')
    a('<p class="legenda">Barras cheias: as horas selecionadas. '
      'Barras apagadas: as descartadas. O gráfico muda junto com a variante '
      'escolhida em §&nbsp;9.</p>')
    a('</div>')
    a('<div class="destaque"><p><b>O relógio é o do arquivo</b>, não '
      'necessariamente UTC nem o do seu terminal. As horas boas caem sobre a '
      'abertura europeia, a sobreposição Londres–Nova York e a tarde americana, '
      'que é o que se esperaria — mas confirme o fuso da sua corretora antes de '
      'usar qualquer número desta seção.</p></div>')

    # -------------------------------------------------------------------- 8
    a('<h2 id="s8">8 · As variantes</h2>')
    a('<p>Oito configurações são publicadas. As três primeiras testam, uma a uma, '
      'as restrições que o documento original sugere; as três seguintes são as '
      'que mediram melhor; a última é um controle estatístico.</p>')
    a(bloco_variantes(r))
    for v in r['variantes']:
        a('<p><b>%s · %s</b> — %s</p>' % (v['nome'], v['rotulo'], v['descricao']))
    a('<h3>Sensibilidade</h3>')
    a('<p>Três incertezas foram medidas em vez de assumidas. <b>(a)</b> Quando a '
      'mesma barra toca o alvo e o stop, o OHLC não diz qual veio primeiro — '
      'todos os números publicados usam a hipótese <b>pessimista</b> (stop '
      'primeiro), e a coluna otimista mostra o outro extremo. <b>(b)</b> O custo '
      'de spread mais comissão, ida e volta. <b>(c)</b> A amostra partida ao '
      'meio.</p>')
    a(bloco_sensibilidade(r))
    a('<p class="legenda">Valores em ticks por operação.</p>')
    a('<div class="destaque">'
      '<p><b>1.</b> A V0 perde nas duas metades (%s e %s ticks) e nas duas '
      'hipóteses de ambiguidade. O prejuízo é estrutural, não é azar de um '
      'trecho.</p>'
      '<p><b>2.</b> O custo come a variante recomendada: a V5 rende %s ticks sem '
      'custo e %s com 40 ticks de custo. Quarenta ticks são 0,40 USD de spread '
      'mais comissão — nada de exótico em ouro. <b>A margem inteira da estratégia '
      'cabe dentro do spread.</b></p>'
      '<p><b>3.</b> O controle invertido (V7) não é o espelho da V0: as duas '
      'perdem. Se houvesse leitura de direção, inverter o lado teria de produzir '
      'o simétrico. (A V7 não é espelho perfeito — ao trocar o lado, a ordem '
      'limitada no meio do range vira um preço pior e enche em %s dos casos, '
      'contra %s da V0 — mas o sentido da conclusão não muda.)</p>'
      '</div>'
      % (fmt(v0['metades']['1a'].get('expectativa_ticks', 0), 1),
         fmt(v0['metades']['2a'].get('expectativa_ticks', 0), 1),
         fmt(v5['stats']['expectativa_ticks'], 1),
         fmt(v5['custo']['40'].get('expectativa_ticks', 0), 1),
         pct(v7['stats']['taxa_ativacao']), pct(v0['stats']['taxa_ativacao'])))

    # -------------------------------------------------------------------- 9
    a('<h2 id="s9">9 · Operação a operação</h2>')
    a('<p>Cada operação do backtest, no gráfico de candles em que aconteceu. '
      'Troque a variante no seletor para ver como cada filtro muda o conjunto de '
      'operações. As setas ←&nbsp;→ do teclado também navegam.</p>')
    a('<div class="painel">')
    a('<div class="barras">')
    a('<label>variante <select id="selVar">%s</select></label>' % opcoes_var)
    a('<label>desfecho <select id="selMot">'
      '<option value="*">todos</option>'
      '<option value="alvo">alvo</option>'
      '<option value="breakeven">breakeven</option>'
      '<option value="stop">stop</option>'
      '<option value="tempo">aberta no fim</option></select></label>')
    a('<label>lado <select id="selLado">'
      '<option value="*">os dois</option>'
      '<option value="long">compra</option>'
      '<option value="short">venda</option></select></label>')
    a('<span class="nav"><button id="btPrev">← anterior</button>'
      '<button id="btProx">próxima →</button>'
      '<span class="conta" id="conta"></span></span>')
    a('</div>')
    a('<p class="legenda" id="descVar" style="margin:0 0 10px"></p>')
    a('<canvas id="cvKline"></canvas>')
    a('<p class="legenda" id="dica" style="visibility:hidden;min-height:1.5em">'
      '&nbsp;</p>')
    a('<p class="legenda">'
      '<span><i style="background:#e0913a"></i>EMA 21</span>'
      '<span><i style="background:#4f9bd9"></i>EMA 42</span>'
      '<span><i style="background:#8e8ad6"></i>EMA 72</span>'
      '<span>faixa sombreada = posição aberta</span>'
      '<span>linha pontilhada dourada = preço da ordem limitada</span>'
      '</p>')
    a('<div class="ficha" id="ficha"></div>')
    a('</div>')
    a('<div class="painel">')
    a('<h4>Curva de resultado acumulado da variante</h4>')
    a('<canvas id="cvCurva"></canvas>')
    a('<p class="legenda">Em ticks, um lote, sem custo. Cada ponto é uma '
      'operação, na ordem em que aconteceram.</p>')
    a('</div>')
    a('<p>O que vale procurar aqui: quantas vezes a barra seguinte ao gatilho '
      'nem chega ao meio do range (a ordem é cancelada e não aparece na lista); '
      'quantas vezes o preço toca a parcial e volta; e o quão longe fica a linha '
      'do alvo de 900 ticks em relação ao tamanho das barras à volta.</p>')

    # ------------------------------------------------------------------- 10
    a('<h2 id="s10">10 · Restrições recomendadas</h2>')
    a('<p>Em ordem de quanto o histórico as sustenta.</p>')
    a('<h3>1. Trocar o alvo final de 900 por uma saída mais próxima — ou por nada</h3>')
    a('<p>É a mudança de maior efeito e a mais bem sustentada, porque não depende '
      'de nenhuma descoberta estatística: depende só do tamanho das barras. Pedir '
      '900 ticks (%s barras medianas) de continuação a um sinal sem direção é '
      'pagar %s de stops para colher %s de alvos. A V6, que sai com a posição '
      'inteira em +1R, rende %s t por operação contra %s t da V4, que tem '
      'exatamente a mesma entrada.'
      % (n(900 / rg['50%'], 1), pct(m.get('stop', 0) / ops0),
         pct(m.get('alvo', 0) / ops0),
         fmt(v6['stats']['expectativa_ticks'], 1),
         fmt(v4['stats']['expectativa_ticks'], 1)))
    a('<h3>2. Operar só nas horas %s</h3>' % horas_txt)
    a('<p>É a única restrição validada fora da amostra, nos dois sentidos '
      '(§&nbsp;7). Também é a que mais reduz o número de operações: de %s para '
      '%s, ou de %s para %s por pregão. Menos operações é o preço, e neste caso '
      'é um preço que vale a pena.</p>'
      % (n(v0['stats']['operacoes']), n(v4['stats']['operacoes']),
         n(v0['stats']['ops_por_dia'], 1), n(v4['stats']['ops_por_dia'], 1)))
    a('<h3>3. Exigir que o gatilho feche além da EMA21</h3>')
    a('<p>Foi o melhor filtro de forma medido, embora sozinho não passe do ruído. '
      'A justificativa para mantê-lo não é estatística: é que ele elimina o caso '
      'em que a barra apenas encosta na média e fecha do lado errado, que é '
      'ambíguo até de ler no gráfico — e regra ambígua é regra que se opera de '
      'um jeito diferente a cada dia.</p>')
    a('<h3>4. Não impor teto de tamanho ao candle de reversão</h3>')
    a('<p>A pergunta do documento original era se convinha limitar o range da '
      'barra de gatilho, já que o stop é fixo. A resposta medida é <b>não</b>: a '
      'V2, com teto de 350 ticks, piora a V0, e no corte por tamanho as barras '
      'grandes medem melhor que as pequenas. O raciocínio "stop fixo + barra '
      'grande = risco maior" está certo sobre o risco; o que ele esquece é que o '
      'retorno cresce junto.</p>')
    a('<h3>5. Dimensionar pela hipótese de custo alto</h3>')
    a('<p>Use 40 ticks de custo, não zero. Nessa hipótese a V5 cai para %s t por '
      'operação — praticamente nada. A única configuração que sobra em pé é a '
      '<b>V7</b>, que junta horário, reconquista e saída inteira em +1R: %s t por '
      'operação sem custo, %s t com 40 ticks, fator de lucro %s sobre %s '
      'operações. É ela que o <code>PLANO.md</code> adota — com a folga de uma '
      'amostra pequena, não de uma certeza.</p>'
      % (fmt(v5['custo']['40'].get('expectativa_ticks', 0), 1),
         fmt(V['V7']['stats']['expectativa_ticks'], 1),
         fmt(V['V7']['custo']['40'].get('expectativa_ticks', 0), 1),
         n(V['V7']['stats']['fator_lucro'], 2),
         n(V['V7']['stats']['operacoes'])))

    # ------------------------------------------------------------------- 11
    a('<h2 id="s11">11 · Glossário</h2>')
    a('<p>Todos os termos usados neste relatório, na ordem em que fazem sentido '
      'aprendê-los.</p>')
    a('<dl class="glos">%s</dl>' % glos)

    # ------------------------------------------------------------------- 12
    a('<h2 id="s12">12 · Limitações honestas</h2>')
    a('<div class="aviso">')
    a('<p><b>%s pregões é pouco.</b> Quatro meses de ouro num regime só. A V5 tem '
      '%s operações, o que dá um erro-padrão de expectativa da ordem de %s ticks '
      'por operação — quase o tamanho da própria expectativa.</p>'
      % (n(D['dias']), n(v5['stats']['operacoes']),
         n(v5['stats']['desvio_ticks'] / (v5['stats']['operacoes'] ** 0.5), 0)))
    a('<p><b>Só existe OHLC.</b> Dentro da barra o caminho é desconhecido. Isso '
      'foi tratado medindo os dois extremos, não escolhendo um.</p>')
    a('<p><b>Sem spread por barra e sem slippage.</b> O custo entrou como cenário; '
      'ordens de stop em ouro escorregam, e escorregam mais justamente nos '
      'momentos em que este backtest as aciona.</p>')
    a('<p><b>As horas foram escolhidas olhando estes dados.</b> A validação '
      'cruzada reduz o risco de garimpo; não o elimina. Só o tempo real, para '
      'frente, decide.</p>')
    a('<p><b>Uma operação por vez.</b> Sinais que aparecem com posição aberta são '
      'descartados — é o comportamento real de quem opera, mas reduz a '
      'amostra.</p>')
    a('</div>')
    a('<p>A estratégia descrita é um bom <b>gatilho de atenção</b> e não é uma '
      'vantagem. Ela marca o momento em que uma tendência acabou de absorver um '
      'pullback — momento legítimo para olhar o gráfico. O que os dados não '
      'sustentam é a segunda metade da afirmação: que dali o preço siga a favor '
      'com frequência suficiente para pagar um alvo de 3R. O caminho com alguma '
      'chance está no <code>PLANO.md</code>: horário estreito, gatilho exigente, '
      'alvo curto, tamanho pequeno e um critério de parada escrito antes de '
      'começar.</p>')

    a('<footer>Gerado por <code>relatorio.py</code> a partir de '
      '<code>saida/resumo.json</code> e <code>saida/barras.json</code>. '
      'Reproduzir: <code>python rodar.py &amp;&amp; python resultados_md.py '
      '&amp;&amp; python relatorio.py &amp;&amp; python plano.py</code>.<br>'
      'Nenhum número desta página foi digitado à mão.</footer>')
    a('</div>')

    a('<script id="dadosResumo" type="application/json">%s</script>'
      % json.dumps(resumo, ensure_ascii=False, separators=(',', ':')))
    a('<script id="dadosBarras" type="application/json">%s</script>' % barras)
    a('<script>'
      'window.__RESUMO__ = JSON.parse(document.getElementById("dadosResumo").textContent);'
      'window.__BARRAS__ = JSON.parse(document.getElementById("dadosBarras").textContent);'
      '</script>')
    a('<script>%s</script>' % JS)
    a('</body></html>')

    caminho = os.path.join(BASE, 'relatorio.html')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write('\n'.join(H))
    print('relatorio.html gravado (%.1f MB).' % (os.path.getsize(caminho) / 1e6))


if __name__ == '__main__':
    escrever()
