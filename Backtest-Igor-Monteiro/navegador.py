# -*- coding: utf-8 -*-
"""
Gera a secao "trade a trade" do relatorio.html: candles M1 (KLineCharts,
embutido de vendor/) com cada operacao da configuracao principal desenhada em
cima do pregao - entrada, stop, parcial, alvo, niveis do setup e o ajuste.

Cada trade leva os DOIS desfechos: o da convencao conservadora (a barra de
entrada so resolve o stop) e o da que credita a barra de entrada. As entradas
sao identicas nas duas (o sinal nao depende da saida), so a saida muda - e e
isso que o botao "convencao" alterna no grafico.

O relatorio e escrito a mao; este script so reescreve o trecho entre os
marcadores <!-- navegador:inicio --> e <!-- navegador:fim -->.

    python navegador.py
"""
import json
import os
import re

import engine as E
import rodar as R

BASE = os.path.dirname(os.path.abspath(__file__))
RELATORIO = os.path.join(BASE, 'relatorio.html')
VENDOR_KC = os.path.join(BASE, 'vendor', 'klinecharts-9.8.10.min.js')
INI, FIM = '<!-- navegador:inicio -->', '<!-- navegador:fim -->'

MOTIVO = {'ALVO': 'A', 'STOP': 'S', 'STOP+': 'P', 'FECHAMENTO': 'F'}

# ------------------------------------------------------------ empacotamento
# Sao ~670 mil candles M1. Em JSON puro o relatorio passaria de 10 MB, entao
# cada pregao vira uma string VLQ base64 (o esquema dos source maps): precos em
# ticks e cada barra como 4 inteiros pequenos - abertura menos o fechamento
# anterior, corpo, sombra de cima, sombra de baixo. Quase tudo cabe em 1 char.
B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'


def _vlq(z, out):
    while True:
        d, z = z & 31, z >> 5
        if z:
            out.append(B64[d | 32])
        else:
            out.append(B64[d])
            return


def _zz(v):
    return 2 * v if v >= 0 else -2 * v - 1


def empacota(barras):
    tk = lambda p: int(round(p / E.TICK))
    out = []
    ant = tk(barras[0][1])
    for _, o, h, l, c in barras:
        o, h, l, c = tk(o), tk(h), tk(l), tk(c)
        _vlq(_zz(o - ant), out)
        _vlq(_zz(c - o), out)
        _vlq(h - max(o, c), out)
        _vlq(min(o, c) - l, out)
        ant = c
    return ''.join(out)


def minutos(barras):
    """Minuto da primeira barra + os saltos (o resto e de 1 em 1 minuto)."""
    ms = [int(hm[:2]) * 60 + int(hm[3:5]) for hm, *_ in barras]
    return ms[0], [[j, ms[j] - ms[j - 1]] for j in range(1, len(ms)) if ms[j] - ms[j - 1] != 1]


# -------------------------------------------------------------------- dados
def _desfecho(t):
    return [round(t['pts'], 1), MOTIVO[t['motivo']], t['k'], t['jp']]


# ------------------------------------------------------------------- medias
# As EMA21 de 1, 5 e 60 minutos sao calculadas NO NAVEGADOR a partir dos
# candles, para nao pesar o arquivo; daqui vai so o estado de cada media antes
# do primeiro candle do pregao. _emas_dia e o espelho em Python do codigo JS, e
# coleta() confere que ele reproduz E.medias (M5 e M60: o valor da ultima barra
# JA FECHADA do tempo grafico, o mesmo que o backtest usa) em todos os pregoes.
def _ema_passo(e, v, k):
    return v if e is None else (v - e) * k + e


def _emas_dia(barras_d, e1, e5, e60):
    k = 2.0 / (E.EMA_PER + 1)
    out = []
    htf = {5: [e5, None, None], 60: [e60, None, None]}   # [ema fechada, balde, ultimo fecho]
    for hm, o, h, l, c in barras_d:
        mi = int(hm[:2]) * 60 + int(hm[3:5])
        e1 = _ema_passo(e1, c, k)
        linha = [e1]
        for tf in (5, 60):
            st = htf[tf]
            b = mi // tf
            if st[1] is not None and b != st[1]:
                st[0] = _ema_passo(st[0], st[2], k)
            st[1], st[2] = b, c
            linha.append(st[0])
        out.append(linha)
    return out


def estados_ema(barras, ordem, validos, ema):
    """Estado das tres medias antes de cada pregao valido (continuas entre os
    pregoes, inclusive os descartados, como na engine)."""
    k = 2.0 / (E.EMA_PER + 1)
    e1, ini = None, {}
    for d in ordem:
        ini[d] = e1
        for bar in barras[d]:
            e1 = _ema_passo(e1, bar[4], k)
    est = {d: (ini[d], ema[d][0][0], ema[d][0][1]) for d in validos}
    for d in validos:
        for (_, m5, m60), (r5, r60) in zip(_emas_dia(barras[d], *est[d]), ema[d]):
            for a, b in ((m5, r5), (m60, r60)):
                assert (a is None and b is None) or abs(a - b) < 1e-6, d
    return est


def coleta():
    barras, diario, ordem = E.carrega()
    validos, _ = E.dias_validos(barras, diario, ordem)
    ctx = R.contexto(barras, diario, validos)
    ema = E.medias(barras, ordem)
    cons = R.roda(barras, ctx, validos, ema)
    cred = R.roda(barras, ctx, validos, ema, favoravel_na_entrada=True)
    est = estados_ema(barras, ordem, validos, ema)

    dias, idx = [], {}
    for d in validos:
        b, c = barras[d], ctx[d]
        m0, saltos = minutos(b)
        bo = [px for _, px in c['bolas']]
        idx[d] = len(dias)
        dias.append(dict(
            d=d, b=int(round(b[0][1] / E.TICK)), m0=m0, sx=saltos, x=empacota(b), em=list(est[d]),
            aj=c['aj'], pv=[[nm, round(px, 1)] for nm, px in c['pivos']],
            fu=[[nm, round(px, 1)] for nm, px in c['fund']],
            bo=[int(min(bo) // 1000), int(max(bo) // 1000)]))

    tr = {}
    for k in R.CHAVES:
        a, f = cons[k], cred[k]
        # as entradas nao dependem da saida: tem que casar uma a uma
        assert [(t['dia'], t['i'], t['nivel']) for t in a] == \
               [(t['dia'], t['i'], t['nivel']) for t in f], k
        tr[k] = [dict(d=idx[x['dia']], l=x['lado'], n=x['nivel'], e=round(x['entrada'], 1),
                      a=round(x['alvo'], 1), i=x['i'], h=x['hora'],
                      c=_desfecho(x), f=_desfecho(y))
                 for x, y in zip(a, f)]

    # pstop: onde fica o stop do restante depois da parcial, em pts a favor da
    # entrada (no medio da operacao: -90 com 2/3 em +45)
    cfg = dict(tick=E.TICK, stop=E.STOP, ppts=E.PARCIAL_PTS, pstop=E.stop_resto(),
               medio=E.PARCIAL_STOP == 'medio', pfrac=E.PARCIAL_FRAC, dist=E.DIST_MIN,
               valp=E.VAL_PONTO, lote=E.CONTRATOS, nparc=E.contratos_parcial(),
               emaper=E.EMA_PER)
    return dict(cfg=cfg, dias=dias, tr=tr)


# --------------------------------------------------------------- formatacao
def n0(v):
    return '{:,.0f}'.format(v).replace(',', ' ').replace('-', '−')


def p1(v):
    return ('%.1f%%' % v).replace('.', ',')


def textos(D):
    tr = D['tr']
    diverge = lambda t: t['c'][:2] != t['f'][:2]
    c = tr['C']
    dc = [t for t in c if diverge(t)]
    na_entrada = sum(1 for t in dc if t['f'][3] == t['i'])
    return {
        'n_total': n0(sum(len(v) for v in tr.values())),
        'n_c': n0(len(c)),
        'div_c': n0(len(dc)),
        'pct_c': p1(100.0 * len(dc) / len(c)),
        'na_entrada': n0(na_entrada),
        'n_dias': n0(len(D['dias'])),
        'stop': '%.0f' % E.STOP, 'ppts': '%.0f' % E.PARCIAL_PTS,
        'pfrac': '%d de %d contratos' % (E.contratos_parcial(), E.CONTRATOS),
        'resto': ('no médio (%s)' if E.PARCIAL_STOP == 'medio' else 'em %s')
                 % ('{:+.0f}'.format(E.stop_resto()).replace('-', '−')),
    }


# --------------------------------------------------------------------- monta
def bloco(D):
    dados = json.dumps(D, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    with open(VENDOR_KC, encoding='utf-8') as f:
        kc = f.read()
    html = MOLDE
    for k, v in textos(D).items():
        html = html.replace('@@%s@@' % k, v)
    return html.replace('@@KLINE@@', kc).replace('@@DADOS@@', dados)


def main():
    D = coleta()
    with open(RELATORIO, encoding='utf-8') as f:
        rel = f.read()
    if INI not in rel or FIM not in rel:
        raise SystemExit('relatorio.html sem os marcadores %s ... %s' % (INI, FIM))
    novo = re.sub(re.escape(INI) + '.*?' + re.escape(FIM),
                  lambda _: INI + '\n' + bloco(D) + '\n' + FIM, rel, flags=re.S)
    with open(RELATORIO, 'w', encoding='utf-8', newline='\n') as f:
        f.write(novo)
    print('-> relatorio.html  (%.1f MB, %d trades, %d pregoes)'
          % (os.path.getsize(RELATORIO) / 1e6, sum(len(v) for v in D['tr'].values()),
             len(D['dias'])))


MOLDE = r"""<style>
/* cores das EMA: fora da paleta do trade (tinta, vermelho, azul, âmbar) */
:root{--nv-ema1:#9A8BC4;--nv-ema5:#1E8A6E;--nv-ema60:#B0427F}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --nv-ema1:#A89CD4;--nv-ema5:#3DB394;--nv-ema60:#D66BA8}}
:root[data-theme="dark"]{--nv-ema1:#A89CD4;--nv-ema5:#3DB394;--nv-ema60:#D66BA8}
.nv-bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:26px 0 12px}
.nv-grp{display:flex;flex-wrap:wrap;align-items:center;gap:2px;background:var(--surface);
  border:1px solid var(--rule);border-radius:4px;padding:4px 6px}
.nv-lab{font-family:var(--mono);font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;
  color:var(--ink-3);padding:0 6px 0 3px}
.nv-grp button{font-family:var(--mono);font-size:12px;font-weight:500;color:var(--ink-2);
  background:transparent;border:1px solid transparent;border-radius:3px;padding:3px 9px;cursor:pointer}
.nv-grp button:hover{background:var(--surface-2);color:var(--ink)}
.nv-grp button[aria-pressed="true"]{background:var(--ink);border-color:var(--ink);color:var(--surface)}
.nv-grp button:disabled{opacity:.35;cursor:default;background:transparent;color:var(--ink-2)}
.nv-grp select{font-family:var(--mono);font-size:12px;background:var(--surface);color:var(--ink);
  border:1px solid var(--rule);border-radius:3px;padding:3px 4px}
.nv-cont{font-family:var(--mono);font-size:12px;color:var(--ink-2);min-width:96px;text-align:center}
.nv-painel{display:grid;grid-template-columns:minmax(0,1fr) 290px;gap:14px;align-items:start}
.nv-quadro{background:var(--surface);border:1px solid var(--rule);border-radius:4px;
  padding:14px 14px 12px;min-width:0;box-shadow:var(--shadow)}
.nv-cab{display:flex;flex-wrap:wrap;gap:4px 14px;align-items:baseline;margin:0 2px 10px;
  font-size:14px;color:var(--ink-2)}
.nv-cab b{font-family:var(--mono);font-size:13.5px;font-weight:600;color:var(--ink)}
.nv-dica{margin-left:auto;font-family:var(--mono);font-size:11px;color:var(--ink-3)}
.nv-area{position:relative}
#nvChart{width:100%;height:480px}
.nv-vazio{position:absolute;inset:0;display:grid;place-items:center;margin:0;
  background:var(--surface);color:var(--ink-3);font-size:14px;z-index:5}
.nv-vazio[hidden]{display:none}
.legend i.nv-l{height:2px;border-radius:0;vertical-align:4px;width:16px}
.nv-ficha{background:var(--surface);border:1px solid var(--rule);border-radius:4px;
  box-shadow:var(--shadow);overflow:hidden}
.nv-topo{padding:16px 18px 14px;border-bottom:1px solid var(--rule-2)}
.nv-res{font-family:var(--serif);font-size:40px;font-weight:600;line-height:1;
  letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.nv-res small{font-family:var(--mono);font-size:12px;font-weight:500;color:var(--ink-3);
  letter-spacing:.06em;margin-left:5px}
.nv-quando{font-family:var(--mono);font-size:12px;color:var(--ink-2);margin-top:9px}
.nv-linhas{padding:6px 0 4px}
.nv-ln{display:flex;justify-content:space-between;gap:12px;padding:3px 18px;font-size:14px}
.nv-ln .k{color:var(--ink-2)}
.nv-ln .v{font-family:var(--mono);font-size:12.5px;font-weight:500;font-variant-numeric:tabular-nums;
  text-align:right}
.nv-outra{margin:8px 14px 14px;padding:10px 12px;background:var(--surface-2);
  border:1px solid var(--rule-2);border-radius:3px;font-size:13.5px;color:var(--ink-2);line-height:1.45}
.nv-outra b{color:var(--ink)}
.nv-pill{font-family:var(--mono);font-size:10.5px;font-weight:600;letter-spacing:.08em;
  text-transform:uppercase;padding:1px 7px;border-radius:3px;white-space:nowrap}
.nv-p-A{background:var(--pos-wash);color:var(--pos)}
.nv-p-P{background:var(--surface-2);color:var(--ink-2);border:1px solid var(--rule)}
.nv-p-S{background:var(--neg-wash);color:var(--neg)}
.nv-p-F{background:var(--ajuste-wash);color:var(--ajuste)}
.nv-lista{margin-top:14px;background:var(--surface);border:1px solid var(--rule);border-radius:4px;
  overflow:hidden;box-shadow:var(--shadow)}
.nv-lista h4{margin:0;padding:12px 14px 9px;font-family:var(--mono);font-size:11px;font-weight:500;
  letter-spacing:.08em;text-transform:uppercase;color:var(--ink-2);border-bottom:1px solid var(--rule)}
.nv-rol{max-height:330px;overflow:auto}
.nv-lista table{color:var(--ink)}  /* sem doctype (quirks) a tabela nao herda a cor */
.nv-lista td{padding:5px 8px;font-size:12px}
.nv-lista td:first-child{font-family:var(--mono);font-size:12px;padding-left:14px}
.nv-lista td:last-child{padding-right:14px}
.nv-lista tbody tr{cursor:pointer}
.nv-lista tbody tr[aria-current="true"] td{background:var(--ajuste-wash)}
@media (max-width:900px){.nv-painel{grid-template-columns:minmax(0,1fr)}}
@media (max-width:700px){#nvChart{height:380px} .nv-dica{margin-left:0}}
</style>

<section id="trades">
  <span class="eyebrow">Trade a trade</span>
  <h3>Cada operação, em cima do pregão</h3>
  <p class="lede">Os @@n_total@@ trades da configuração principal, desenhados sobre as barras
    de 1 minuto em que aconteceram. A chave <em>convenção</em> é o achado da primeira seção
    posto na tela: mesmo toque, mesmo candle, e o desfecho muda.</p>
  <div class="col">
    <p>No setup C, <strong>@@div_c@@ dos @@n_c@@ trades (@@pct_c@@) mudam de desfecho</strong>
      quando a barra de entrada passa a ser creditada — e em @@na_entrada@@ deles a parcial
      de +@@ppts@@ sai dentro do próprio candle da entrada. Filtre por “onde divergem” e
      alterne a convenção: o candle não diz se o preço foi primeiro ao nível ou primeiro
      aos +@@ppts@@.</p>
  </div>

  <div class="nv-bar" role="toolbar" aria-label="Filtros do navegador de trades">
    <div class="nv-grp"><span class="nv-lab">setup</span><span id="nvSetup"></span></div>
    <div class="nv-grp"><span class="nv-lab">convenção</span><span id="nvConv"></span></div>
    <div class="nv-grp"><span class="nv-lab">desfecho</span><span id="nvMot"></span></div>
    <div class="nv-grp"><span class="nv-lab">mostrar</span><span id="nvDiv"></span></div>
    <div class="nv-grp"><span class="nv-lab">lado</span><span id="nvLado"></span></div>
    <div class="nv-grp"><span class="nv-lab">ano</span><select id="nvAno" aria-label="ano"></select></div>
    <div class="nv-grp"><span class="nv-lab">janela</span>
      <select id="nvJanela" aria-label="janela do gráfico">
        <option value="60">60 min</option>
        <option value="120" selected>2 h</option>
        <option value="240">4 h</option>
        <option value="dia">pregão inteiro</option>
      </select></div>
    <div class="nv-grp"><button id="nvAnt" aria-label="trade anterior">‹ anterior</button>
      <span class="nv-cont" id="nvCont" aria-live="polite">0 de 0</span>
      <button id="nvProx" aria-label="próximo trade">próximo ›</button></div>
  </div>

  <div class="nv-painel">
    <div class="nv-quadro">
      <div class="nv-cab" id="nvCab"></div>
      <div class="nv-area"><div id="nvChart"></div><p class="nv-vazio" id="nvVazio" hidden></p></div>
      <div class="legend">
        <span><i class="nv-l" style="background:var(--ajuste)"></i>ajuste</span>
        <span><i class="nv-l" style="background:var(--ink)"></i>entrada</span>
        <span><i class="nv-l" style="background:repeating-linear-gradient(90deg,var(--neg) 0 4px,transparent 4px 7px)"></i>stop −@@stop@@</span>
        <span><i class="nv-l" style="background:repeating-linear-gradient(90deg,var(--pos) 0 4px,transparent 4px 7px)"></i>parcial @@pfrac@@ em +@@ppts@@</span>
        <span><i class="nv-l" style="background:repeating-linear-gradient(90deg,var(--ink-2) 0 2px,transparent 2px 5px)"></i>stop do resto @@resto@@</span>
        <span><i class="nv-l" style="background:var(--nv-ema1);height:1px"></i>EMA 21 · 1 min</span>
        <span><i class="nv-l" style="background:var(--nv-ema5)"></i>EMA 21 · 5 min</span>
        <span><i class="nv-l" style="background:var(--nv-ema60);height:3px"></i>EMA 21 · 60 min</span>
        <span><i class="nv-l" style="background:var(--pos)"></i>alvo</span>
        <span><i class="nv-l" style="background:repeating-linear-gradient(90deg,var(--ink-3) 0 3px,transparent 3px 6px)"></i>níveis do setup (claros: a menos de 600 do ajuste)</span>
      </div>
    </div>
    <div>
      <div class="nv-ficha" id="nvFicha"></div>
      <div class="nv-lista">
        <h4 id="nvListaTit">Trades</h4>
        <div class="nv-rol"><table><tbody id="nvLista"></tbody></table></div>
      </div>
    </div>
  </div>
  <p class="col" style="color:var(--ink-2);font-size:14.5px;margin-top:16px">As EMA 21 de 5 e
    60 minutos aparecem em degraus porque cada candle mostra o valor da última barra
    <em>fechada</em> daquele tempo gráfico — o que se sabia naquele minuto, e o mesmo valor
    que o backtest usa. Fora da faixa do trade elas são cortadas, para a escala continuar
    centrada nele. A escala se reajusta a cada trade, mesmo depois de arrastar o eixo.
    Setas ← → navegam quando o gráfico está na tela. Gerado por <code>navegador.py</code>
    a partir da engine — rode de novo depois de mexer em parâmetros.</p>
</section>

<script>@@KLINE@@</script>
<script>
(function(){
'use strict';
const D=@@DADOS@@;
const CFG=D.cfg, TICK=CFG.tick;
const NF=new Intl.NumberFormat('pt-BR');
const MONO='"IBM Plex Mono",ui-monospace,Consolas,monospace';
const SANS='"Source Sans 3","Segoe UI",sans-serif';
const SINAL=v=>(v>0?'+':v<0?'−':'')+Math.abs(v);
const MOT={A:'alvo',S:'stop',P:CFG.medio?'stop no médio':'stop '+SINAL(CFG.pstop),F:'fechamento'};
const SETUP={A:'retorno à abertura',B:'seco no ajuste',C:'pivôs',D:'bolas',CD:'pivôs + bolas'};
const DOW=['dom','seg','ter','qua','qui','sex','sáb'];
const $=id=>document.getElementById(id);

let COR={};
function lePaleta(){
  const s=getComputedStyle(document.documentElement), g=k=>s.getPropertyValue(k).trim();
  COR={surface:g('--surface'),surface2:g('--surface-2'),ink:g('--ink'),ink2:g('--ink-2'),
       ink3:g('--ink-3'),rule:g('--rule'),rule2:g('--rule-2'),aj:g('--ajuste'),
       neg:g('--neg'),pos:g('--pos'),ema1:g('--nv-ema1'),ema5:g('--nv-ema5'),ema60:g('--nv-ema60')};
}
function alfa(cor,a){
  const h=cor.replace('#',''), n=h.length===3?h.split('').map(c=>c+c).join(''):h;
  return 'rgba('+parseInt(n.slice(0,2),16)+','+parseInt(n.slice(2,4),16)+','
        +parseInt(n.slice(4,6),16)+','+a+')';
}
const PRECO=v=>NF.format(Math.round(v));
const PTS=v=>(v>0?'+':v<0?'−':'')+NF.format(Math.abs(Math.round(v*10)/10));
const cls=v=>v>0?'pos':v<0?'neg':'';
const pad=n=>(n<10?'0':'')+n;
const dataBR=d=>d.slice(8,10)+'/'+d.slice(5,7)+'/'+d.slice(0,4);
const HM=ts=>{const x=new Date(ts);return pad(x.getUTCHours())+':'+pad(x.getUTCMinutes());};

/* --- candles: VLQ base64 -> OHLC, um pregão por vez, sob demanda ----------- */
const IDX=new Int16Array(128);
'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'.split('')
  .forEach((c,i)=>{IDX[c.charCodeAt(0)]=i;});
const cache=new Map();
function abre(di){
  let x=cache.get(di); if(x) return x;
  const dd=D.dias[di], s=dd.x; let p=0;
  const le=()=>{let z=0,sh=0,c;do{c=IDX[s.charCodeAt(p++)];z+=(c&31)*Math.pow(2,sh);sh+=5;}while(c&32);return z;};
  const zz=z=>(z%2)?-(z+1)/2:z/2;
  const o=[],h=[],l=[],c=[]; let ant=dd.b;
  while(p<s.length){
    const O=ant+zz(le()), C=O+zz(le()), H=Math.max(O,C)+le(), L=Math.min(O,C)-le();
    o.push(O*TICK); h.push(H*TICK); l.push(L*TICK); c.push(C*TICK); ant=C;
  }
  const n=o.length, ts=new Array(n), mi=new Array(n), salto={};
  dd.sx.forEach(v=>{salto[v[0]]=v[1];});
  const t0=Date.UTC(+dd.d.slice(0,4),+dd.d.slice(5,7)-1,+dd.d.slice(8,10));
  let m=dd.m0;
  for(let i=0;i<n;i++){ if(i) m+=salto[i]||1; mi[i]=m; ts[i]=t0+m*60000; }
  /* EMA21 de 1, 5 e 60 min - espelho de _emas_dia no navegador.py, conferido
     contra a engine: M5 e M60 valem o que a última barra FECHADA daquele tempo
     gráfico dizia (sem olhar o futuro, como no backtest). */
  const k=2/(CFG.emaper+1), passo=(e,v)=>e===null?v:(v-e)*k+e;
  const e1=new Array(n), e5=new Array(n), e60=new Array(n);
  let a1=dd.em[0];
  const htf=[[dd.em[1],null,null,5,e5],[dd.em[2],null,null,60,e60]];
  for(let i=0;i<n;i++){
    a1=passo(a1,c[i]); e1[i]=a1;
    for(const st of htf){
      const b=Math.floor(mi[i]/st[3]);
      if(st[1]!==null&&b!==st[1]) st[0]=passo(st[0],st[2]);
      st[1]=b; st[2]=c[i]; st[4][i]=st[0];
    }
  }
  x={o,h,l,c,ts,n,dd,e1,e5,e60}; cache.set(di,x); return x;
}

/* --- estado --------------------------------------------------------------- */
const ANOS=[...new Set(D.dias.map(d=>d.d.slice(0,4)))];
let fSetup='C', conv='c', fMot='todos', fDiv=false, fLado=0, fAno='todos', janela=120;
let lista=[], cur=0;
const res=t=>t[conv], outra=t=>t[conv==='c'?'f':'c'];
const diverge=t=>t.c[0]!==t.f[0]||t.c[1]!==t.f[1];

/* --- peças de desenho próprias, em cima do klinecharts -------------------- */
const K=klinecharts;
K.registerOverlay({
  name:'nv-nivel', totalStep:2, lock:true,
  needDefaultPointFigure:false, needDefaultXAxisFigure:false, needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates,bounding})=>{
    const e=overlay.extendData, y=coordinates[0].y;
    const f=[{type:'line',ignoreEvent:true,
      attrs:{coordinates:[{x:0,y:y},{x:bounding.width,y:y}]},
      styles:{color:e.cor,size:e.grossa?1.6:1,style:e.tracejada?'dashed':'solid',
              dashedValue:e.pontilhada?[2,3]:[5,4]}}];
    if(e.rot) f.push({type:'text',ignoreEvent:true,
      attrs:{x:e.dir?bounding.width-6:6+(e.dx||0),y:e.baixo?y+3:y-3,text:e.rot,align:e.dir?'right':'left',
             baseline:e.baixo?'top':'bottom'},
      styles:{color:e.corTexto||e.cor,size:10.5,family:MONO,weight:'500',
              backgroundColor:alfa(COR.surface,.8),
              paddingLeft:3,paddingRight:3,paddingTop:1,paddingBottom:1,borderRadius:2}});
    return f;
  },
  createYAxisFigures:({overlay,coordinates,bounding})=>{
    const e=overlay.extendData;
    if(!e.preco) return [];
    return {type:'text',ignoreEvent:true,
      attrs:{x:bounding.width-2,y:coordinates[0].y,text:e.preco,align:'right',baseline:'middle'},
      styles:{color:COR.surface,size:10,family:MONO,weight:'600',backgroundColor:e.corTexto||e.cor,
              paddingLeft:4,paddingRight:4,paddingTop:2,paddingBottom:2,borderRadius:2}};
  }
});
K.registerOverlay({
  name:'nv-marca', totalStep:2, lock:true,
  needDefaultPointFigure:false, needDefaultXAxisFigure:false, needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates,bounding})=>{
    const e=overlay.extendData, x=coordinates[0].x;
    return [
      {type:'line',ignoreEvent:true,attrs:{coordinates:[{x:x,y:0},{x:x,y:bounding.height}]},
       styles:{color:e.cor,size:1,style:'dashed',dashedValue:[2,3]}},
      {type:'text',ignoreEvent:true,
       attrs:{x:x,y:e.topo?4+(2-e.degrau)*19:bounding.height-4-e.degrau*19,text:e.rot,align:'center',
              baseline:e.topo?'top':'bottom'},
       styles:{color:COR.surface,size:10,family:MONO,weight:'600',backgroundColor:e.cor,
               paddingLeft:4,paddingRight:4,paddingTop:2,paddingBottom:2,borderRadius:2}}];
  }
});
K.registerOverlay({
  name:'nv-zona', totalStep:3, lock:true,
  needDefaultPointFigure:false, needDefaultXAxisFigure:false, needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates,bounding})=>{
    if(coordinates.length<2) return [];
    const a=Math.min(coordinates[0].x,coordinates[1].x), b=Math.max(coordinates[0].x,coordinates[1].x);
    return [{type:'rect',ignoreEvent:true,
      attrs:{x:a-3,y:0,width:Math.max(6,b-a+6),height:bounding.height},
      styles:{style:'fill',color:overlay.extendData.cor}}];
  }
});
K.registerOverlay({
  name:'nv-seta', totalStep:2, lock:true,
  needDefaultPointFigure:false, needDefaultXAxisFigure:false, needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates})=>{
    const e=overlay.extendData, x=coordinates[0].x, y=coordinates[0].y, d=e.compra?1:-1;
    return [{type:'polygon',ignoreEvent:true,
      attrs:{coordinates:[{x:x,y:y+d*6},{x:x-5,y:y+d*16},{x:x+5,y:y+d*16}]},
      styles:{style:'fill',color:e.cor}}];
  }
});
/* Indicador invisível: duas linhas transparentes no piso e no teto do trade,
   só para o eixo Y alcançar stop e alvo quando os candles visíveis não chegam
   lá. (O caminho óbvio, minValue/maxValue via overrideIndicator, tem bug na
   9.8.10: o maxValue é gravado em minValue.) */
K.registerIndicator({name:'NV_REF',shortName:'',series:'price',precision:0,
  figures:[{key:'lo',type:'line'},{key:'hi',type:'line'}],
  calc:(dl,ind)=>{const e=ind.extendData||{}; return dl.map(()=>({lo:e.lo,hi:e.hi}));}});
const INVISIVEL={color:'rgba(0,0,0,0)',size:1,style:'solid',smooth:false,dashedValue:[2,2]};
/* As três EMA vêm penduradas em cada candle. Os valores do indicador entram na
   escala do eixo Y, e a de 60 min pode estar a milhares de pontos: fora da
   faixa do trade (extendData lo/hi) a linha é cortada, para a escala continuar
   centrada no trade. */
K.registerIndicator({name:'NV_EMA',shortName:'',series:'price',precision:0,
  figures:[{key:'e1',type:'line'},{key:'e5',type:'line'},{key:'e60',type:'line'}],
  calc:(dl,ind)=>{
    const f=ind.extendData||{}, lo=f.lo===undefined?-Infinity:f.lo, hi=f.hi===undefined?Infinity:f.hi;
    const cl=v=>(v===null||v===undefined||v<lo||v>hi)?undefined:v;
    return dl.map(k=>({e1:cl(k.e1),e5:cl(k.e5),e60:cl(k.e60)}));
  }});
/* o klinecharts não mescla estilo de linha com o padrão: cada item vem completo */
function estiloEma(){
  const l=(cor,tam)=>({color:cor,size:tam,style:'solid',smooth:false,dashedValue:[2,2]});
  return {lines:[l(COR.ema1,1),l(COR.ema5,1.5),l(COR.ema60,2)]};
}

let kchart=null, kDi=-1;
/* Tamanhos de texto dos eixos TÊM de ser inteiros: a altura do eixo X sai
   deles, e com 10.5 o painel de candles fica com 457,5 px. Na 9.8.10 o canvas
   de altura fracionária espera um ResizeObserver que nunca dispara e para de
   redesenhar para sempre. */
function estilos(){
  const eixo={axisLine:{color:COR.rule},tickLine:{color:COR.rule},
              tickText:{color:COR.ink3,size:11,family:MONO}};
  const cruz={line:{color:COR.ink3,style:'dashed'},
              text:{color:COR.surface,backgroundColor:COR.ink2,borderColor:COR.ink2,size:11,family:MONO}};
  return {
    grid:{horizontal:{color:COR.rule2},vertical:{show:false}},
    candle:{
      bar:{upColor:COR.surface,downColor:COR.ink2,noChangeColor:COR.ink2,
           upBorderColor:COR.ink2,downBorderColor:COR.ink2,noChangeBorderColor:COR.ink2,
           upWickColor:COR.ink2,downWickColor:COR.ink2,noChangeWickColor:COR.ink2},
      priceMark:{high:{color:COR.ink3,textSize:10,textFamily:MONO},
                 low:{color:COR.ink3,textSize:10,textFamily:MONO},last:{show:false}},
      tooltip:{showRule:'follow_cross',
        rect:{color:COR.surface,borderColor:COR.rule},
        text:{size:11,family:MONO,color:COR.ink2},
        custom:dados=>{
          const k=dados.current, T=(t,v,c)=>({title:{text:t,color:COR.ink3},value:{text:v,color:c||COR.ink}});
          const E=v=>v===null||v===undefined?'—':PRECO(v);
          return [T('hora',HM(k.timestamp)),T('abre',PRECO(k.open)),T('máx',PRECO(k.high)),
                  T('mín',PRECO(k.low)),T('fecha',PRECO(k.close)),
                  T('amplitude',NF.format(k.high-k.low)+' pts',COR.ink2),
                  T('EMA 1m',E(k.e1),COR.ema1),T('EMA 5m',E(k.e5),COR.ema5),T('EMA 60m',E(k.e60),COR.ema60)];
        }}},
    indicator:{tooltip:{showRule:'none'}},
    xAxis:eixo, yAxis:eixo, separator:{color:COR.rule},
    crosshair:{horizontal:cruz,vertical:cruz}
  };
}
function iniciaGrafico(){
  kchart=K.init('nvChart',{styles:estilos(),thousandsSeparator:'.',
    customApi:{formatDate:(f,ts)=>HM(ts),formatBigNumber:v=>String(v)}});
  kchart.setPriceVolumePrecision(0,0);
  kchart.setOffsetRightDistance(24);
  kchart.createIndicator({name:'NV_REF',styles:{lines:[INVISIVEL,INVISIVEL]}},true,{id:'candle_pane'});
  kchart.createIndicator({name:'NV_EMA',styles:estiloEma()},true,{id:'candle_pane'});
  /* resize() com debounce: na 9.8.10 o ajuste de tamanho do canvas passa pela
     mesma fila do redesenho e se perde se cair junto com um redesenho pendente. */
  let rz=0;
  window.addEventListener('resize',()=>{ clearTimeout(rz); rz=setTimeout(()=>kchart.resize(),120); });
  const trocaTema=()=>{ lePaleta(); kchart.setStyles(estilos());
    kchart.overrideIndicator({name:'NV_EMA',styles:estiloEma()},'candle_pane'); desenha(); };
  const mq=window.matchMedia('(prefers-color-scheme:dark)');
  if(mq.addEventListener) mq.addEventListener('change',trocaTema);
  new MutationObserver(trocaTema).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
}

function niveisDoSetup(s,dd){
  const bola=k=>[NF.format(k*1000),k*1000];
  if(s==='C') return dd.pv;
  if(s==='CD') return dd.fu.map(v=>v[0][0]==='B'?bola(+v[0].slice(1)):v);
  if(s==='D'){ const L=[]; for(let k=dd.bo[0];k<=dd.bo[1];k++) L.push(bola(k)); return L; }
  return [];
}

/* applyNewData é assíncrono (espera o cálculo dos indicadores e reajusta a
   viewport depois): a janela só pode ser posicionada no callback, e o
   callback posiciona o trade que estiver na tela quando ele chegar. */
let carregando=false;
function grafico(t){
  if(kDi===t.d){ if(!carregando) posiciona(t); return; }
  const x=abre(t.d);
  kDi=t.d; carregando=true;
  kchart.applyNewData(x.o.map((o,i)=>({timestamp:x.ts[i],open:o,high:x.h[i],low:x.l[i],close:x.c[i],volume:0,
                                        e1:x.e1[i],e5:x.e5[i],e60:x.e60[i]})),
    false,()=>{ carregando=false; const a=lista[cur]; if(a&&a.d===kDi) posiciona(a); });
}
function posiciona(t){
  const x=abre(t.d), dd=x.dd, r=res(t), k=r[2], jp=r[3], ts=x.ts;
  const e=t.e, stop=e-t.l*CFG.stop, parc=e+t.l*CFG.ppts, pstop=e+t.l*CFG.pstop;
  const alvoNoAjuste=Math.abs(t.a-dd.aj)<0.01;
  /* janela centrada no trade: se ele cabe, o meio do trade vai para o meio do
     gráfico; se não cabe, a entrada fica no primeiro quarto */
  const jan=janela==='dia'?x.n:Math.min(janela,x.n), dur=k-t.i;
  const meio=dur<=jan*0.8?Math.round((t.i+k)/2):t.i+Math.floor(jan/4);
  let a=Math.max(0,meio-Math.floor(jan/2)), z=Math.min(x.n-1,a+jan-1); a=Math.max(0,z-jan+1);

  /* escala Y: candles da janela + entrada, stop e alvo, com folga - o trade fica
     centrado na vertical, e as EMA são cortadas fora dessa faixa. Arrastar o eixo
     desliga a escala automática do klinecharts: ela é religada a cada trade. */
  let lo=Math.min(e,stop,t.a), hi=Math.max(e,stop,t.a);
  for(let i=a;i<=z;i++){ if(x.l[i]<lo) lo=x.l[i]; if(x.h[i]>hi) hi=x.h[i]; }
  const folga=Math.max(30,(hi-lo)*0.05), faixa={lo:lo-folga,hi:hi+folga};
  kchart.overrideIndicator({name:'NV_REF',extendData:faixa},'candle_pane');
  kchart.overrideIndicator({name:'NV_EMA',extendData:faixa},'candle_pane');
  try{
    const ax=kchart.getDrawPaneById('candle_pane').getAxisComponent();
    if(!ax.getAutoCalcTickFlag()) ax.setAutoCalcTickFlag(true);
  }catch(err){}
  const larg=(kchart.getSize('candle_pane','main')||{}).width||700;
  kchart.setBarSpace(Math.max(1,Math.min(40,(larg-24)/(z-a+1))));
  kchart.scrollToDataIndex(z);

  kchart.removeOverlay();
  const nivel=(v,o)=>kchart.createOverlay({name:'nv-nivel',lock:true,points:[{value:v}],extendData:o},'candle_pane');
  /* a entrada é sempre extremo novo do dia: fica no fundo do gráfico nas
     compras e no topo nas vendas - as etiquetas verticais vão para o outro lado */
  const marca=(i,cor,rot,degrau)=>kchart.createOverlay({name:'nv-marca',lock:true,
    points:[{timestamp:ts[i]}],extendData:{cor:cor,rot:rot,degrau:degrau,topo:t.l===1}},'candle_pane');

  const corRes=r[0]>0?COR.pos:r[0]<0?COR.neg:COR.ink3;
  kchart.createOverlay({name:'nv-zona',lock:true,points:[{timestamp:ts[t.i]},{timestamp:ts[k]}],
    extendData:{cor:alfa(corRes,.08)}},'candle_pane');

  niveisDoSetup(fSetup,dd).forEach(v=>{
    if(Math.abs(v[1]-e)<0.01) return;
    const ok=Math.abs(v[1]-dd.aj)>=CFG.dist;
    nivel(v[1],{cor:alfa(COR.ink3,ok?.9:.4),rot:v[0],tracejada:true,pontilhada:true,dir:true});
  });
  if(fSetup!=='A') nivel(x.o[0],{cor:alfa(COR.ink3,.8),rot:'abertura',tracejada:true,dir:true});
  nivel(dd.aj,{cor:COR.aj,rot:alvoNoAjuste?'ajuste · alvo':'ajuste',grossa:true,dir:true,
               preco:(fSetup==='B'||alvoNoAjuste)?'':PRECO(dd.aj)});
  if(!alvoNoAjuste) nivel(t.a,{cor:COR.pos,rot:'alvo +'+NF.format(Math.abs(t.a-e)),preco:PRECO(t.a),
                               baixo:t.l===-1});
  /* stop, stop do resto e parcial ficam a 100, 90 e 45 pts da entrada - poucos
     pixels quando o ajuste entra na escala. Rótulos da entrada e dos stops vão
     para o lado do stop (o do resto deslocado para a direita, porque fica a 10
     pts do stop), o da parcial para o lado oposto; só entrada e stop levam
     etiqueta no eixo. */
  const ladoStop=t.l===1, juntos=Math.abs(pstop-parc)<0.01;
  if(!juntos) nivel(pstop,{cor:COR.ink2,rot:(CFG.medio?'médio ':'resto ')+SINAL(CFG.pstop),
                           tracejada:true,pontilhada:true,baixo:ladoStop,dx:78});
  nivel(parc,{cor:COR.pos,rot:'parcial +'+CFG.ppts+(juntos?' · stop do resto':''),
              tracejada:true,baixo:!ladoStop});
  nivel(stop,{cor:COR.neg,rot:'stop −'+CFG.stop,tracejada:true,preco:PRECO(stop),baixo:ladoStop});
  nivel(e,{cor:COR.ink,rot:'entrada · '+t.n,grossa:true,preco:PRECO(e),baixo:ladoStop,
           corTexto:(t.n==='AJUSTE')?COR.aj:COR.ink});

  marca(t.i,COR.ink,'entrada',2);
  if(jp!==null) marca(jp,COR.pos,'parcial',1);
  marca(k,r[1]==='S'?COR.neg:r[1]==='F'?COR.aj:r[1]==='P'?COR.ink2:COR.pos,MOT[r[1]],0);
  kchart.createOverlay({name:'nv-seta',lock:true,points:[{timestamp:ts[t.i],value:e}],
    extendData:{cor:COR.ink,compra:t.l===1}},'candle_pane');
}

/* --- ficha, lista, controles ---------------------------------------------- */
function ficha(t){
  const x=abre(t.d), dd=x.dd, r=res(t), o=outra(t), e=t.e;
  const dist=e-dd.aj, dow=DOW[new Date(Date.UTC(+dd.d.slice(0,4),+dd.d.slice(5,7)-1,+dd.d.slice(8,10))).getUTCDay()];
  $('nvCab').innerHTML='<b>'+fSetup+' · '+dataBR(dd.d)+' '+dow+'</b>'
    +'<span>'+(t.l===1?'compra':'venda')+(t.n==='ABERTURA'?' na abertura':t.n==='AJUSTE'?' no ajuste':' no '+t.n)
    +(t.n==='AJUSTE'?'':' · '+NF.format(Math.round(Math.abs(dist)))+' pts '+(dist>0?'acima':'abaixo')+' do ajuste')+'</span>'
    +'<span class="nv-dica">'+x.n+' barras M1 · '+HM(x.ts[0])+'–'+HM(x.ts[x.n-1])+'</span>';
  const ln=(k,v,c)=>'<div class="nv-ln"><span class="k">'+k+'</span><span class="v'+(c?' '+c:'')+'">'+v+'</span></div>';
  const dur=Math.round((x.ts[r[2]]-x.ts[t.i])/60000);
  const nomeConv=c=>c==='c'?'conservadora':'creditando a barra de entrada';
  const igual=!diverge(t);
  $('nvFicha').innerHTML='<div class="nv-topo">'
    +'<div class="nv-res '+cls(r[0])+'">'+PTS(r[0])+'<small>pts</small></div>'
    +'<div class="nv-quando">'+t.h+' → '+HM(x.ts[r[2]])+' · <span class="nv-pill nv-p-'+r[1]+'">'+MOT[r[1]]+'</span></div></div>'
    +'<div class="nv-linhas">'
    +ln('setup',fSetup+' · '+SETUP[fSetup])
    +ln('lado',t.l===1?'compra':'venda')
    +ln('entrada',PRECO(e))
    +ln('stop',PRECO(e-t.l*CFG.stop),'neg')
    +ln('parcial (+'+CFG.ppts+')',r[3]===null?'não saiu':HM(x.ts[r[3]])+(r[3]===t.i?' · na entrada':''),r[3]===null?'':'pos')
    +ln(CFG.medio?'stop no médio':'stop do resto',PRECO(e+t.l*CFG.pstop))
    +ln('alvo',PRECO(t.a)+(Math.abs(t.a-dd.aj)<0.01?' · ajuste':''),'pos')
    +ln('ajuste',PRECO(dd.aj))
    +[['EMA 1m',x.e1],['EMA 5m',x.e5],['EMA 60m',x.e60]].map(v=>{
        const m=v[1][t.i]; if(m===null||m===undefined) return ln(v[0]+' na entrada','—');
        const dv=Math.round(e-m);
        return ln(v[0]+' na entrada',PRECO(m)+' <span style="color:var(--ink-3)">('+(dv>0?'+':dv<0?'−':'')+NF.format(Math.abs(dv))+')</span>');
      }).join('')
    +ln('duração',dur+' min')
    +ln('R$ (lote de '+CFG.lote+')',NF.format(Math.round(r[0]*CFG.valp*CFG.lote)),cls(r[0]))
    +'</div><div class="nv-outra">'+(igual
      ?'Mesmo desfecho nas duas convenções.'
      :'<b>'+nomeConv(conv==='c'?'f':'c').replace(/^./,m=>m.toUpperCase())+':</b> '
       +'<span class="'+cls(o[0])+'">'+PTS(o[0])+' pts</span>, '+MOT[o[1]]+' às '+HM(x.ts[o[2]])
       +(o[3]===t.i?' — parcial no candle da entrada':''))
    +'</div>';
}

function filtra(){
  lista=D.tr[fSetup].filter(t=>
    (fMot==='todos'||res(t)[1]===fMot)&&(!fDiv||diverge(t))&&(!fLado||t.l===fLado)
    &&(fAno==='todos'||D.dias[t.d].d.slice(0,4)===fAno));
  const tb=$('nvLista');
  tb.innerHTML=lista.map((t,i)=>{
    const r=res(t);
    return '<tr data-i="'+i+'"><td>'+dataBR(D.dias[t.d].d).slice(0,6)+D.dias[t.d].d.slice(2,4)
      +'</td><td>'+t.h+'</td><td>'+(t.n==='ABERTURA'?'abert.':t.n==='AJUSTE'?'ajuste':t.n)+'</td><td>'+(t.l===1?'C':'V')
      +'</td><td class="'+cls(r[0])+'">'+PTS(r[0])+'</td></tr>';
  }).join('');
  const soma=lista.reduce((s,t)=>s+res(t)[0],0), ac=lista.filter(t=>res(t)[0]>0).length,
        ze=lista.filter(t=>res(t)[0]===0).length, pc=v=>Math.round(100*v/lista.length)+'%';
  $('nvListaTit').textContent=lista.length
    ?(NF.format(lista.length)+' trades · '+PTS(Math.round(soma))+' pts · '+pc(ac)+' ganham · '+pc(ze)+' zeram')
    :'Nenhum trade';
}
function desenha(){
  const vazio=$('nvVazio');
  if(!lista.length){
    vazio.hidden=false; vazio.textContent='Nenhum trade com estes filtros.';
    $('nvCab').innerHTML=''; $('nvFicha').innerHTML=''; $('nvCont').textContent='0 de 0';
    $('nvAnt').disabled=$('nvProx').disabled=true; return;
  }
  vazio.hidden=true;
  cur=Math.max(0,Math.min(cur,lista.length-1));
  const t=lista[cur];
  ficha(t); grafico(t);
  $('nvCont').textContent=NF.format(cur+1)+' de '+NF.format(lista.length);
  $('nvAnt').disabled=cur===0; $('nvProx').disabled=cur===lista.length-1;
  const tb=$('nvLista'), velho=tb.querySelector('[aria-current="true"]');
  if(velho) velho.removeAttribute('aria-current');
  const novo=tb.children[cur];
  if(novo){ novo.setAttribute('aria-current','true');
    const rol=tb.closest('.nv-rol'), rt=novo.offsetTop, rh=novo.offsetHeight;
    if(rt<rol.scrollTop||rt+rh>rol.scrollTop+rol.clientHeight) rol.scrollTop=rt-rol.clientHeight/2; }
}
function grupo(id,opcoes,valor,muda){
  const el=$(id); el.innerHTML='';
  opcoes.forEach(par=>{
    const b=document.createElement('button');
    b.textContent=par[1]; b.setAttribute('aria-pressed',String(par[0]===valor));
    b.onclick=()=>{ muda(par[0]); controles(); refaz(); };
    el.appendChild(b);
  });
}
/* refiltra mantendo o trade na tela quando ele segue na lista - trocar a
   convenção mostra o MESMO trade com o outro desfecho */
function refaz(){
  const t=lista[cur]; filtra();
  const j=t?lista.indexOf(t):-1; cur=j<0?0:j; desenha();
}
function controles(){
  grupo('nvSetup',['A','B','C','D','CD'].map(s=>[s,s]),fSetup,v=>{fSetup=v;});
  grupo('nvConv',[['c','conservadora'],['f','credita a entrada']],conv,v=>{conv=v;});
  grupo('nvMot',[['todos','todos'],['A','alvo'],['S','stop'],['P',MOT.P],['F','fechamento']],fMot,v=>{fMot=v;});
  grupo('nvDiv',[[false,'todos'],[true,'onde divergem']],fDiv,v=>{fDiv=v;});
  grupo('nvLado',[[0,'ambos'],[1,'compra'],[-1,'venda']],fLado,v=>{fLado=v;});
}
$('nvAno').innerHTML='<option value="todos">todos</option>'+ANOS.map(a=>'<option>'+a+'</option>').join('');
$('nvAno').onchange=e=>{fAno=e.target.value; refaz();};
$('nvJanela').onchange=e=>{janela=e.target.value==='dia'?'dia':+e.target.value; desenha();};
$('nvAnt').onclick=()=>{cur--; desenha();};
$('nvProx').onclick=()=>{cur++; desenha();};
$('nvLista').addEventListener('click',e=>{const tr=e.target.closest('tr'); if(tr){cur=+tr.dataset.i; desenha();}});
document.addEventListener('keydown',e=>{
  if(e.altKey||e.ctrlKey||e.metaKey||/^(SELECT|INPUT|TEXTAREA)$/.test(e.target.tagName)) return;
  const r=$('nvChart').getBoundingClientRect();
  if(r.bottom<0||r.top>innerHeight) return;
  if(e.key==='ArrowLeft'&&cur>0){cur--; desenha(); e.preventDefault();}
  if(e.key==='ArrowRight'&&cur<lista.length-1){cur++; desenha(); e.preventDefault();}
});

lePaleta(); iniciaGrafico(); controles(); filtra(); desenha();
})();
</script>"""


if __name__ == '__main__':
    main()
