# -*- coding: utf-8 -*-
"""Molde do relatorio.html. Substituicao simples de {{chave}}.

Nao ha numero escrito aqui: tudo vem do contexto montado por relatorio.py a
partir de saida/resumo.json. O CSS e o mesmo sistema visual do
Backtest-Rincones1 -- os dois relatorios sao da mesma familia.
"""
import re


def render(ctx):
    def sub(m):
        expr = m.group(1).strip()
        v = ctx
        for parte in expr.split('.'):
            if isinstance(v, dict):
                v = v[parte]
            else:
                v = getattr(v, parte)
        return str(v)
    return re.sub(r'\{\{([^}]+)\}\}', sub, MOLDE)


MOLDE = r"""<meta charset="utf-8">
<title>Rincones1-DTA</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=IBM+Plex+Mono:wght@400;500;600&display=swap">

<style>
:root{
  --paper:#EFF3F5; --card:#FFFFFF; --card-2:#F6F9FA;
  --ink:#111B22; --ink-2:#4B5D69; --ink-3:#7B8C97;
  --line:#D6E0E6; --line-2:#E8EEF1;
  --accent:#1F5A73; --accent-soft:#E2EDF2; --on-accent:#FFFFFF;
  --pos:#1A6E48; --neg:#A93227; --warn:#8A6516; --zero:#7B8C97;
  --pos-bg:#E4F1EA; --neg-bg:#F8E7E5;
  --alta:#2E8B62; --baixa:#C0483C;
  --shadow:0 1px 2px rgba(17,27,34,.06), 0 8px 24px -12px rgba(17,27,34,.14);
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --paper:#0C1216; --card:#141E24; --card-2:#18242B;
  --ink:#E4EDF2; --ink-2:#9DB0BC; --ink-3:#70848F;
  --line:#243239; --line-2:#1C282F;
  --accent:#6FB2CE; --accent-soft:#17303C; --on-accent:#0C1216;
  --pos:#4FB884; --neg:#E27A6E; --warn:#D5A648; --zero:#70848F;
  --pos-bg:#122C22; --neg-bg:#2E1A18;
  --alta:#4FB884; --baixa:#E27A6E;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -12px rgba(0,0,0,.6);
}}
:root[data-theme="dark"]{
  --paper:#0C1216; --card:#141E24; --card-2:#18242B;
  --ink:#E4EDF2; --ink-2:#9DB0BC; --ink-3:#70848F;
  --line:#243239; --line-2:#1C282F;
  --accent:#6FB2CE; --accent-soft:#17303C; --on-accent:#0C1216;
  --pos:#4FB884; --neg:#E27A6E; --warn:#D5A648; --zero:#70848F;
  --pos-bg:#122C22; --neg-bg:#2E1A18;
  --alta:#4FB884; --baixa:#E27A6E;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -12px rgba(0,0,0,.6);
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:"Source Serif 4",Georgia,"Times New Roman",serif;
  font-size:17px;line-height:1.65;-webkit-font-smoothing:antialiased}
.wrap{max-width:1120px;margin:0 auto;padding:0 24px 96px}
h1,h2,h3,h4,h5,.ui,button,select,th,caption,.tile-k,.tile-s,.tag,.b,.lab,.pill,.cs,.legenda
  {font-family:Archivo,"Helvetica Neue",Arial,sans-serif}
.mono,td.num,th.num,.tile-v,.v,.t,.count,.res{font-family:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;
  font-variant-numeric:tabular-nums}

header{border-bottom:1px solid var(--line);
  background:linear-gradient(180deg,var(--card) 0%,var(--paper) 100%)}
.head{max-width:1120px;margin:0 auto;padding:56px 24px 40px}
.eyebrow{font-size:12px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;
  color:var(--accent);margin:0 0 14px;font-family:Archivo,sans-serif}
h1{font-size:clamp(38px,6vw,60px);line-height:1.02;margin:0 0 16px;font-weight:700;
  letter-spacing:-.022em;text-wrap:balance}
.lede{font-size:20px;color:var(--ink-2);max-width:62ch;margin:0 0 28px}
.spec{display:flex;flex-wrap:wrap;gap:8px}
.chip{font-family:"IBM Plex Mono",monospace;font-size:12.5px;padding:5px 11px;
  border:1px solid var(--line);border-radius:999px;background:var(--card);
  color:var(--ink-2);font-variant-numeric:tabular-nums}
.chip b{color:var(--ink);font-weight:600}

section{margin:64px 0 0;scroll-margin-top:20px}
h2{font-size:13px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;
  color:var(--ink-3);margin:0 0 6px;display:flex;align-items:baseline;gap:12px}
h2 .n{color:var(--accent);font-variant-numeric:tabular-nums}
h3{font-size:27px;line-height:1.2;margin:0 0 14px;font-weight:600;
  letter-spacing:-.015em;text-wrap:balance}
p{margin:0 0 16px;max-width:68ch}
.sub{color:var(--ink-2);font-size:.85em}
strong,b{font-weight:600}
code{font-family:"IBM Plex Mono",monospace;font-size:.88em;background:var(--card-2);
  border:1px solid var(--line-2);border-radius:4px;padding:1px 5px}

.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:24px 0}
.tile{background:var(--card);border:1px solid var(--line);border-radius:10px;
  padding:16px 18px;box-shadow:var(--shadow)}
.tile-k{font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
  color:var(--ink-3);margin-bottom:8px}
.tile-v{font-size:27px;font-weight:600;line-height:1;letter-spacing:-.02em}
.tile-s{font-size:13px;color:var(--ink-3);margin-top:6px}
.pos{color:var(--pos)} .neg{color:var(--neg)} .zer{color:var(--zero)}

.setups{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin:26px 0}
.setup{background:var(--card);border:1px solid var(--line);border-radius:12px;
  padding:22px;box-shadow:var(--shadow);position:relative;overflow:hidden}
.setup.best{border-color:var(--accent)} .setup.dead{opacity:.82}
.setup .rail{position:absolute;inset:0 auto 0 0;width:3px;background:var(--line)}
.setup.best .rail{background:var(--accent)} .setup.dead .rail{background:var(--neg)}
.setup h4{font-size:19px;margin:0 0 4px;font-weight:600}
.tag{font-size:11px;font-weight:600;letter-spacing:.09em;text-transform:uppercase;
  padding:3px 9px;border-radius:999px;display:inline-block;margin-bottom:12px}
.tag.on{background:var(--accent-soft);color:var(--accent)}
.tag.off{background:var(--neg-bg);color:var(--neg)}
.setup p{font-size:15.5px;color:var(--ink-2);margin:0 0 16px}
.pair{display:flex;gap:20px;border-top:1px solid var(--line-2);padding-top:14px}
.pair div{flex:1}
.pair .b{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-3);margin-bottom:4px}
.pair .v{font-size:20px;font-weight:600}
.pair .t{font-size:12.5px;color:var(--ink-3)}

.scroll{overflow-x:auto;margin:20px 0;border:1px solid var(--line);border-radius:10px;
  background:var(--card);box-shadow:var(--shadow)}
table{border-collapse:collapse;width:100%;font-size:14.5px}
caption{text-align:left;font-size:13px;font-weight:600;color:var(--ink-2);padding:14px 18px 0}
th,td{padding:9px 14px;text-align:left;border-bottom:1px solid var(--line-2);white-space:nowrap;
  vertical-align:top}
thead th{font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;
  color:var(--ink-3);border-bottom:1px solid var(--line)}
td.num,th.num{text-align:right}
tbody tr:last-child td{border-bottom:none}
tr.hi td{background:var(--accent-soft)}
tr.mute td{color:var(--ink-3)}
td.best{font-weight:600;color:var(--pos)}
td .sub{display:block;white-space:normal;max-width:26ch;line-height:1.35;margin-top:2px}
.mark{background:var(--accent-soft);border-radius:4px;padding:1px 6px;font-weight:600}

.charts{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:18px;margin:24px 0}
.chart{background:var(--card);border:1px solid var(--line);border-radius:12px;
  padding:18px 18px 12px;box-shadow:var(--shadow)}
.chart h5{font-size:14px;font-weight:600;margin:0 0 2px}
.chart .cs{font-size:12.5px;color:var(--ink-3);margin:0 0 12px}
.chart svg{display:block;width:100%;height:auto;overflow:visible}
.tip{position:fixed;pointer-events:none;opacity:0;transition:opacity .12s;
  background:var(--ink);color:var(--paper);font-family:"IBM Plex Mono",monospace;
  font-size:12px;padding:7px 10px;border-radius:6px;z-index:20;white-space:pre;
  font-variant-numeric:tabular-nums;box-shadow:0 6px 20px -6px rgba(0,0,0,.5)}

.note{border-left:3px solid var(--accent);background:var(--card);padding:16px 20px;
  border-radius:0 10px 10px 0;margin:22px 0;box-shadow:var(--shadow)}
.note.risk{border-left-color:var(--neg)}
.note p:last-child{margin-bottom:0}
.note .lab{font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
  color:var(--ink-3);margin-bottom:6px}

ol.acoes{counter-reset:a;list-style:none;padding:0;margin:22px 0;display:grid;gap:10px}
ol.acoes li{counter-increment:a;background:var(--card);border:1px solid var(--line);
  border-radius:10px;padding:15px 18px 15px 52px;position:relative;box-shadow:var(--shadow)}
ol.acoes li::before{content:counter(a);position:absolute;left:18px;top:15px;
  font-family:"IBM Plex Mono",monospace;font-size:14px;font-weight:600;color:var(--accent)}

/* ---------- visualizador ---------- */
.bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:22px 0 14px}
.grp{display:flex;align-items:center;gap:6px;background:var(--card);border:1px solid var(--line);
  border-radius:9px;padding:5px 8px;box-shadow:var(--shadow)}
.grp .lab{font-size:10.5px;font-weight:600;letter-spacing:.09em;text-transform:uppercase;
  color:var(--ink-3);padding-right:2px}
button{font-family:Archivo,sans-serif;font-size:12.5px;font-weight:600;color:var(--ink-2);
  background:transparent;border:1px solid transparent;border-radius:6px;padding:4px 10px;cursor:pointer}
button:hover{background:var(--card-2);color:var(--ink)}
button[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:var(--on-accent)}
button:disabled{opacity:.35;cursor:default}
select{font-size:12.5px;background:var(--card);color:var(--ink);border:1px solid var(--line);
  border-radius:6px;padding:4px 6px}
.count{font-size:12.5px;color:var(--ink-2);min-width:96px;text-align:center}
.painel{display:grid;grid-template-columns:minmax(0,1fr) 262px;gap:16px;align-items:start}
@media(max-width:900px){.painel{grid-template-columns:minmax(0,1fr)}}
.quadro{background:var(--card);border:1px solid var(--line);border-radius:12px;
  padding:14px;box-shadow:var(--shadow);min-width:0}
.quadro .cab{display:flex;flex-wrap:wrap;gap:10px;align-items:baseline;
  margin:0 2px 10px;font-family:Archivo,sans-serif;font-size:12.5px;color:var(--ink-3)}
.quadro .cab b{font-size:14px;font-weight:600;color:var(--ink)}
.quadro .cab .dica{margin-left:auto;font-size:11px}
/* a área do gráfico nunca muda de tamanho: o aviso de "nenhum trade" cobre o
   gráfico em vez de escondê-lo. Escondendo, o observador de resize via altura
   zero e o painel do esforço encolhia para o mínimo — e não voltava. */
.area{position:relative}
#kchart{width:100%;height:470px;min-width:0}
.area .vazio{position:absolute;inset:0;margin:0;max-width:none;display:grid;
  place-items:center;background:var(--card);border-radius:8px;z-index:5}
.area .vazio[hidden]{display:none}  /* o display:grid acima vence o [hidden] do navegador */
@media(max-width:700px){#kchart{height:380px}}
.ficha{background:var(--card);border:1px solid var(--line);border-radius:12px;
  box-shadow:var(--shadow);overflow:hidden}
.ficha .topo{padding:14px 16px;border-bottom:1px solid var(--line-2)}
.ficha .res{font-size:30px;font-weight:600;letter-spacing:-.02em;line-height:1}
.ficha .quando{font-size:12px;color:var(--ink-3);margin-top:6px;font-family:Archivo,sans-serif}
.linhas{padding:6px 0}
.ln{display:flex;justify-content:space-between;gap:10px;padding:6px 16px;font-size:12.5px}
.ln .k{color:var(--ink-3);font-family:Archivo,sans-serif}
.ln .v{font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums;font-weight:500}
.pill{font-size:10.5px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;
  padding:2px 8px;border-radius:999px;display:inline-block}
.p-alvo{background:var(--pos-bg);color:var(--pos)}
.p-stop{background:var(--neg-bg);color:var(--neg)}
.p-zero{background:var(--card-2);color:var(--zero)}
.p-fim{background:var(--card-2);color:var(--warn)}
.lista-wrap{margin-top:16px;background:var(--card);border:1px solid var(--line);
  border-radius:12px;box-shadow:var(--shadow);overflow:hidden}
.lista-wrap h4{font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
  color:var(--ink-3);margin:0;padding:13px 16px 9px}
.lista-wrap table{font-size:12.5px}
.lista-wrap th,.lista-wrap td{padding:7px 16px}
.lista-wrap tbody tr{cursor:pointer}
.lista-wrap tbody tr:hover td{background:var(--card-2)}
.lista-wrap tbody tr[aria-current="true"] td{background:var(--accent-soft)}
.rolagem{max-height:300px;overflow:auto}
.legenda{display:flex;flex-wrap:wrap;gap:14px;margin-top:12px;font-size:11.5px;color:var(--ink-3)}
.legenda span{display:flex;align-items:center;gap:5px}
.sw{width:11px;height:11px;border-radius:2px;display:inline-block}
.sw.l{height:2px;border-radius:0}
.vazio{padding:30px 16px;color:var(--ink-3);font-size:13px;text-align:center}

footer{margin-top:72px;padding-top:24px;border-top:1px solid var(--line);
  font-family:Archivo,sans-serif;font-size:13px;color:var(--ink-3)}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:3px}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style>

<header>
  <div class="head">
    <p class="eyebrow">Backtest · WIN · barras de 10.000 ticks</p>
    <h1>Rincones1-DTA</h1>
    <p class="lede">Uma <em>Hull</em> mede a intensidade do movimento, uma <em>EMA</em> mede a tendência e um <em>canal de Keltner</em> mede o esticamento. O gatilho de esforço decide quando. A medição decide de que lado.</p>
    <div class="spec">
      <span class="chip">EMA <b>{{ema_per}}</b> · Hull <b>{{hma_per}}</b> · Keltner <b>{{kelt_int}}</b>–<b>{{kelt_ext}}</b> ATR</span>
      <span class="chip">gatilho ≥ <b>{{nivel}}</b></span>
      <span class="chip">stop <b>{{stop_rot}}</b></span>
      <span class="chip">parcial <b>{{frac}}%</b> na distância do stop</span>
      <span class="chip">alvo <b>{{alvo}}</b></span>
      <span class="chip">abr–ago/2026</span>
    </div>
  </div>
</header>

<div class="wrap">

<section>
  <h2><span class="n">01</span> O resultado</h2>
  <h3>Carteira D + T, uma posição por vez</h3>
  <div class="tiles">
    <div class="tile"><div class="tile-k">EV por trade · WINV26</div>
      <div class="tile-v {{cls26}}">{{ev26}}</div><div class="tile-s">{{evr26}} R · {{n26}} trades</div></div>
    <div class="tile"><div class="tile-k">EV por trade · WINFUT</div>
      <div class="tile-v {{clsfu}}">{{evfu}}</div><div class="tile-s">{{evrfu}} R · {{nfu}} trades</div></div>
    <div class="tile"><div class="tile-k">t · WINV26</div>
      <div class="tile-v">{{t26}}</div><div class="tile-s">sobre {{preg26}} pregões com trade</div></div>
    <div class="tile"><div class="tile-k">t · WINFUT</div>
      <div class="tile-v">{{tfu}}</div><div class="tile-s">sobre {{pregfu}} pregões</div></div>
    <div class="tile"><div class="tile-k">acerto</div>
      <div class="tile-v">{{ac26}}</div><div class="tile-s">{{acfu}} no WINFUT</div></div>
  </div>
  <p>Os dois arquivos são de <strong>10.000 ticks</strong> do WIN, exportados do Profit. O WINFUT é o contínuo e cobre {{pregfu}} pregões; o WINV26 é o contrato, e dos {{preg26tot}} dias do arquivo só <strong>{{preg26cheio}}</strong> têm pregão de verdade — o resto é de quando o contrato ainda era distante e fazia uma ou duas barras por dia. <strong>WINFUT contém WINV26</strong>: quando os dois concordam, isso vale menos do que parece.</p>
  {{cart26}}
  {{cartfu}}
  <div class="charts" id="charts"></div>
  <p class="sub">Passe o mouse pela curva para ver trade a trade. A letra é o setup.</p>
</section>

<section>
  <h2><span class="n">02</span> As três peças</h2>
  <h3>O que cada uma faz — depois de medida</h3>
  <p>A hipótese de partida era a leitura clássica: <em>comprar com a Hull subindo e o preço acima dela, vender com a Hull descendo e o preço abaixo</em>. Medida, ela não é o que paga. O que cada peça acabou fazendo:</p>
  <div class="setups">
    <article class="setup"><span class="rail"></span>
      <h4>EMA {{ema_per}}</h4><span class="tag on">tendência e régua</span>
      <p>É a linha do meio do canal e a origem de todas as distâncias. A profundidade do mergulho — quanto o preço se afastou dela — é o que limita o setup principal.</p></article>
    <article class="setup best"><span class="rail"></span>
      <h4>Hull {{hma_per}}</h4><span class="tag on">intensidade — e lado</span>
      <p>Faz <strong>duas</strong> coisas, e as duas medem. <b>Veto:</b> Hull plana é o pior balde de todos — sem intensidade, o gatilho não paga. <b>Lado:</b> o trade entra do lado <em>oposto</em> ao que o preço ocupa em relação a ela.</p></article>
    <article class="setup dead"><span class="rail"></span>
      <h4>Keltner {{kelt_int}}–{{kelt_ext}} ATR</h4><span class="tag off">quase inerte</span>
      <p>Mede o esticamento, mas não veta nada que a Hull já não vete, e a leitura clássica da banda mede negativo. Sobra dele a régua e o aviso: <strong>onde o preço está esticado, este operacional não opera.</strong></p></article>
  </div>
  {{ver_pecas}}
</section>

<section>
  <h2><span class="n">03</span> A descoberta</h2>
  <h3>De que lado da Hull vale entrar</h3>
  <p>Para cada gatilho, duas distâncias <strong>assinadas pelo lado do trade</strong>:</p>
  <p class="mono" style="font-size:14px;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px 18px;max-width:none">
    dh = sinal × (close − Hull&nbsp;{{hma_per}}) / ATR &nbsp;&nbsp;&nbsp; de = sinal × (close − EMA&nbsp;{{ema_per}}) / ATR</p>
  <p><code>dh &lt; 0</code> quer dizer <em>comprar abaixo da Hull</em> (ou vender acima dela) — o lado oposto ao que ela ocupa. <code>dh &gt; 0</code> é a leitura clássica. Cada sinal foi medido <strong>isolado</strong>, sem carteira, para que um balde não roube a vaga do outro.</p>
  {{tab_hull}}
  {{ver_hull}}
  <p>Faz sentido com o que o indicador diz de si mesmo: ele acende quando alguém gastou muito e <strong>não</strong> levou o preço — absorção. Absorção se desfaz. Ele não é sinal de continuação, é sinal de <em>falha</em>. A Hull entra medindo se existe movimento para falhar (não plana) e de que lado o preço está em relação a ele.</p>
  {{tab_hull_faixas}}
  {{tab_hull_incl}}
  {{ver_incl}}
</section>

<section>
  <h2><span class="n">04</span> Os setups</h2>
  <h3>Dois ligados, dois medidos e desligados</h3>
  <div class="setups">{{cards}}</div>
  <p class="sub">Números do setup <strong>isolado</strong> — cada sinal medido por si, com a gestão padrão. Na carteira eles disputam a vaga, e é por isso que um setup positivo sozinho pode piorar o conjunto.</p>
  {{tab_setups}}
  {{ver_setups}}
</section>

<section>
  <h2><span class="n">05</span> O nível do gatilho</h2>
  <h3>O parâmetro mais forte do projeto</h3>
  <p>O indicador colore a barra a partir de <strong>0,55</strong> e usa <strong>0,60</strong> como extremo — são as configurações padrão dele, e é com elas que o índice é <em>calculado</em> aqui. Mas o nível a partir do qual vale <em>entrar</em> é outra coisa, e ele foi varrido.</p>
  {{tab_nivel}}
  {{ver_nivel}}
</section>

<section>
  <h2><span class="n">06</span> O canal de Keltner</h2>
  <h3>Onde ele ajuda, onde não</h3>
  {{tab_zonas}}
  <p>A restrição de zona do setup D — <em>só dentro do canal</em> — é <strong>inerte</strong>: com o close do lado oposto da Hull e o mergulho limitado, a barra praticamente nunca está na banda. Desligar o veto não muda o resultado:</p>
  {{tab_veto}}
  <p>E as duas leituras de banda como <em>setup</em>:</p>
  {{tab_canal}}
  {{ver_canal}}
</section>

<section>
  <h2><span class="n">07</span> A gestão</h2>
  <h3>O stop herdado é largo demais para este gatilho</h3>
  <p>Os <strong>sinais são os mesmos</strong> em todas as linhas — o que muda é onde o trade morre e quanto ele paga. A coluna <code>R</code> é o EV dividido pelo próprio stop de cada trade: é ela que compara stops de tamanhos diferentes sem enganar.</p>
  {{tab_gestao}}
  {{ver_gestao}}
  <p>A grade inteira, em pontos fixos — EV por trade:</p>
  {{tab_grade}}
  <p>E com o stop dimensionado pelo ATR da barra do sinal — EV em R, que é o que compara stops diferentes:</p>
  {{tab_grade_atr}}
  <div class="note"><div class="lab">A regra da parcial não mudou</div>
  <p>Parcial de <strong>{{frac}}%</strong> na <strong>mesma distância do stop</strong>, e o stop do restante vai para a <strong>média da operação</strong> — que, com meia posição e a parcial nessa distância, é o próprio stop inicial. O stop não anda, e o trade que volta morre em <strong>zero de verdade</strong>. É a regra do Rincones1, herdada inteira.</p></div>
</section>

<section>
  <h2><span class="n">08</span> A entrada</h2>
  <h3>Ou preenche na barra seguinte, ou o trade morre</h3>
  <p>Ordem <strong>limitada no meio do candle do gatilho</strong>, válida por <strong>{{max_fill}}</strong> barra. Não preencheu na barra seguinte, a operação é abortada. Dos {{sinais26}} sinais do WINV26, {{abort26}} morrem assim; no WINFUT, {{abortfu}} de {{sinaisfu}}.</p>
  {{tab_entrada}}
  {{ver_entrada}}
</section>

<section>
  <h2><span class="n">09</span> O eixo [E2] e o filtro dele</h2>
  <h3>A troca que ajudou o Rincones1 não ajuda aqui</h3>
  <p>O <code>v2</code> do indicador trocou o eixo do deslocamento — que media <code>|delta| / |Close−Open|</code> — por <strong>vaivém</strong>: <code>(|delta|/esforço) × (1 − |Close−Open|/percurso)</code>. Aqui a troca foi remedida com todo o resto congelado.</p>
  {{tab_e2}}
  {{ver_e2}}
  <p>O <code>DESCARTA_E2</code> — jogar fora a barra em que o eixo do vaivém é o maior dos três — <strong>não existe no indicador</strong>; veio do Rincones1. Medido aqui:</p>
  {{tab_filtro_e2}}
  {{ver_filtro_e2}}
</section>

<section>
  <h2><span class="n">10</span> Sensibilidade</h2>
  <h3>Os cortes são platôs ou pontas de agulha?</h3>
  <p>Cada corte varrido sozinho, com o resto congelado. Serve para separar <em>“a regra mede”</em> de <em>“o número foi escolhido a dedo”</em>: se o desempenho desaba ao lado do valor adotado, o valor está ajustado demais.</p>
  {{tab_sens}}
  {{ver_sens}}
</section>

<section>
  <h2><span class="n">11</span> O custo</h2>
  <h3>Quanto sobra depois da corretagem</h3>
  {{tab_custo}}
  <p>E há um custo que <strong>não</strong> está aqui: a ordem limitada é assumida preenchida a preço exato assim que o preço toca o nível. Na prática existe fila, e nem todo toque preenche. Esse otimismo empurra os números para cima de um jeito que não dá para quantificar com dados de barra.</p>
</section>

<section>
  <h2><span class="n">12</span> Mês a mês</h2>
  <h3>Onde o resultado se concentra</h3>
  {{tab_mes}}
  {{ver_mes}}
</section>

<section>
  <h2><span class="n">13</span> Os trades, um a um</h2>
  <h3>Candles, médias, canal, gatilho e desfecho</h3>
  <p class="sub">Todos os sinais de cada setup, medidos isoladamente — inclusive os dos setups desligados, para ver por que falham. Navegue com ← → ou clique na lista. O botão <strong>gestão</strong> troca a variante de stop e alvo: os sinais são os mesmos, o que muda é onde o trade morre.</p>
  <p class="sub">O gráfico carrega o <strong>pregão inteiro</strong>: a <strong>janela</strong> só define o zoom inicial em volta do trade. Roda do mouse dá zoom, arrastar navega o dia, e o cruzamento mostra a barra sob o cursor com preço, hora e índice de esforço.</p>

  <div class="bar">
    <div class="grp"><span class="lab">base</span><span id="gBase"></span></div>
    <div class="grp"><span class="lab">gestão</span><span id="gGestao"></span></div>
    <div class="grp"><span class="lab">setup</span><span id="gSetup"></span></div>
    <div class="grp"><span class="lab">lado da Hull</span><span id="gHull"></span></div>
    <div class="grp"><span class="lab">desfecho</span><span id="gRes"></span></div>
    <div class="grp"><span class="lab">janela</span>
      <select id="selJanela">
        <option value="30">30 barras</option>
        <option value="50" selected>50 barras</option>
        <option value="90">90 barras</option>
        <option value="160">160 barras</option>
      </select></div>
    <div class="grp">
      <button id="btnAnt" title="anterior">←</button>
      <span class="count" id="cont">—</span>
      <button id="btnProx" title="próximo">→</button>
    </div>
  </div>

  <div class="painel">
    <div class="quadro">
      <div class="cab" id="kcab"></div>
      <div class="area">
        <div id="kchart"></div>
        <p class="vazio" id="kvazio" hidden></p>
      </div>
    </div>
    <div>
      <div class="ficha" id="ficha"></div>
      <div class="lista-wrap">
        <h4 id="listaTit">Trades filtrados</h4>
        <div class="rolagem"><table>
          <thead><tr><th>#</th><th>dia</th><th>setup</th><th>lado</th><th class="num">pts</th></tr></thead>
          <tbody id="lista"></tbody>
        </table></div>
      </div>
    </div>
  </div>

  <div class="legenda">
    <span><i class="sw" style="background:var(--alta)"></i>candle de alta</span>
    <span><i class="sw" style="background:var(--baixa)"></i>candle de baixa</span>
    <span><i class="sw l" style="background:var(--accent)"></i>EMA {{ema_per}}</span>
    <span><i class="sw l" style="background:var(--warn)"></i>Hull {{hma_per}}</span>
    <span><i class="sw l" style="background:var(--ink-3)"></i>Keltner ±{{kelt_int}} ATR</span>
    <span><i class="sw" style="background:var(--neg)"></i>stop</span>
    <span><i class="sw" style="background:var(--pos)"></i>alvo</span>
    <span>roda do mouse = zoom · arrastar = navegar o pregão inteiro</span>
  </div>
</section>

<section>
  <h2><span class="n">14</span> Ressalvas</h2>
  <h3>O que enfraquece tudo acima</h3>
  <div class="note risk"><div class="lab">Amostra pequena</div>
    <p>{{pregfu}} pregões no WINFUT e {{preg26cheio}} pregões cheios no WINV26 — dois meses de mercado, um regime só. Os <code>t</code> da carteira estão acima de +2, mas <code>t</code> alto em dois meses não é o mesmo que vantagem estável.</p></div>
  <div class="note risk"><div class="lab">As bases não são independentes</div>
    <p>WINFUT contém WINV26 no período em que os dois existem. A concordância entre eles vale menos do que a de duas amostras separadas.</p></div>
  <div class="note risk"><div class="lab">As regras saíram destes mesmos dados</div>
    <p>O lado da Hull, o veto da Hull plana, o nível do gatilho e o tamanho do stop foram <strong>escolhidos olhando os dois arquivos</strong>. A seção 10 mostra que os cortes são platôs, não pontas — mas platô medido na mesma amostra continua sendo sobreajuste. Não há corte de validação fora da amostra neste projeto.</p></div>
  <div class="note risk"><div class="lab">O canal quase não trabalha</div>
    <p>Das três peças que dão nome ao projeto, o Keltner é a mais decorativa no operacional que ficou de pé: o veto dele é inerte e os setups de banda estão desligados. Ele ficou por medir bem <em>o que não fazer</em>.</p></div>
  <div class="note risk"><div class="lab">Sem filtro de horário, rolagem ou vencimento</div>
    <p>Abertura e fechamento têm dinâmica própria e certamente contaminam os números.</p></div>
  <div class="note risk"><div class="lab">O preenchimento é otimista</div>
    <p>A limitada preenche a preço exato ao primeiro toque, sem fila. É a hipótese mais frágil de todo o backtest, e nenhum número aqui a corrige.</p></div>
</section>

<section>
  <h2><span class="n">15</span> O que eu faria</h2>
  <h3>Em ordem</h3>
  <ol class="acoes">
    <li>{{acao_nivel}}</li>
    <li>{{acao_gestao}}</li>
    <li>{{acao_setups}}</li>
    <li>{{acao_hull}}</li>
    <li><strong>Não ligar os setups de banda.</strong> O K mede positivo sozinho e mesmo assim piora a carteira — ele ocupa a vaga de trades melhores. O KB mede negativo no WINFUT.</li>
    <li><strong>Medir o custo real da sua corretora</strong> e refazer a seção 11 com o número verdadeiro antes de dimensionar posição.</li>
  </ol>
</section>

<footer>
  <p>Gerado por <code>python rodar.py &amp;&amp; python relatorio.py</code> · especificação em <code>ESTRATEGIA.md</code> · números completos em <code>RESULTADOS.md</code> · plano operacional em <code>PLANO.md</code> · operação a operação em <code>saida/trades_*.csv</code></p>
</footer>
</div>

<div class="tip" id="tip"></div>

<script>{{klinecharts_js}}</script>

<script>
const EQ = {
  WINV26: {rot:"WINV26", eq:{{eq26}}, su:"{{su26}}", cs:"{{preg26}} pregões com trade"},
  WINFUT: {rot:"WINFUT", eq:{{eqfu}}, su:"{{sufu}}", cs:"{{pregfu}} pregões"}
};
const D = {{G}};
const GEST_ROT = {{gest_rot}};
const NF = new Intl.NumberFormat('pt-BR');
const tip = document.getElementById('tip');

/* ================= curva de capital ================= */
function curva(base){
  const d = EQ[base], eq = d.eq, n = eq.length;
  const W=520,H=210,ML=46,MR=14,MT=10,MB=24, iw=W-ML-MR, ih=H-MT-MB;
  const lo=Math.min(0,...eq), hi=Math.max(0,...eq);
  const pad=(hi-lo)*0.08||100, y0=lo-pad, y1=hi+pad;
  const X=i=>ML+(n<=1?0:i*iw/(n-1)), Y=v=>MT+ih-(v-y0)/(y1-y0)*ih;
  const linha=eq.map((v,i)=>(i?'L':'M')+X(i).toFixed(1)+' '+Y(v).toFixed(1)).join(' ');
  const area=linha+' L'+X(n-1).toFixed(1)+' '+Y(0).toFixed(1)+' L'+X(0).toFixed(1)+' '+Y(0).toFixed(1)+' Z';
  const passo=Math.ceil((y1-y0)/4/500)*500||500;
  let grade='';
  for(let v=Math.ceil(y0/passo)*passo; v<=y1; v+=passo){
    grade+=`<line x1="${ML}" x2="${W-MR}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}" stroke="var(--line-2)" stroke-width="1"/>`
         + `<text x="${ML-9}" y="${(Y(v)+4).toFixed(1)}" text-anchor="end" font-family="IBM Plex Mono, monospace" font-size="10" fill="var(--ink-3)">${NF.format(v)}</text>`;
  }
  const fim=eq[n-1], gid='g'+base;
  const svg=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Curva de capital do ${base}: ${n} trades, resultado final de ${NF.format(fim)} pontos">
    <defs><linearGradient id="${gid}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="var(--accent)" stop-opacity=".22"/>
      <stop offset="100%" stop-color="var(--accent)" stop-opacity="0"/></linearGradient></defs>
    ${grade}
    <line x1="${ML}" x2="${W-MR}" y1="${Y(0).toFixed(1)}" y2="${Y(0).toFixed(1)}" stroke="var(--ink-3)" stroke-width="1" stroke-dasharray="3 3"/>
    <path d="${area}" fill="url(#${gid})"/>
    <path d="${linha}" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
    <circle cx="${X(n-1).toFixed(1)}" cy="${Y(fim).toFixed(1)}" r="4" fill="var(--accent)" stroke="var(--card)" stroke-width="2"/>
    <text x="${(X(n-1)-6).toFixed(1)}" y="${(Y(fim)-11).toFixed(1)}" text-anchor="end" font-family="IBM Plex Mono, monospace" font-size="12" font-weight="600" fill="var(--accent)">+${NF.format(fim)}</text>
    <line class="cross" x1="0" x2="0" y1="${MT}" y2="${MT+ih}" stroke="var(--ink-3)" stroke-width="1" opacity="0"/>
    <circle class="dot" r="4" fill="var(--accent)" stroke="var(--card)" stroke-width="2" opacity="0"/>
    <rect class="hit" x="${ML}" y="${MT}" width="${iw}" height="${ih}" fill="transparent"/></svg>`;
  const el=document.createElement('div'); el.className='chart';
  el.innerHTML=`<h5>${d.rot}</h5><p class="cs">${d.cs} · ${n} trades</p>${svg}`;
  const s=el.querySelector('svg'), cross=s.querySelector('.cross'), dot=s.querySelector('.dot');
  s.querySelector('.hit').addEventListener('mousemove', ev=>{
    const r=s.getBoundingClientRect(), px=(ev.clientX-r.left)/r.width*W;
    let i=Math.round((px-ML)/(iw/Math.max(1,n-1))); i=Math.max(0,Math.min(n-1,i));
    const x=X(i), y=Y(eq[i]);
    cross.setAttribute('x1',x); cross.setAttribute('x2',x); cross.setAttribute('opacity','.45');
    dot.setAttribute('cx',x); dot.setAttribute('cy',y); dot.setAttribute('opacity','1');
    const res=eq[i]-(i?eq[i-1]:0);
    tip.textContent=`trade ${i+1} de ${n}   setup ${d.su[i]}\n`
      +`resultado   ${res>=0?'+':'−'}${NF.format(Math.abs(res))} pts\n`
      +`acumulado   ${eq[i]>=0?'+':'−'}${NF.format(Math.abs(eq[i]))} pts`;
    tip.style.opacity='1';
    tip.style.left=Math.min(ev.clientX+14, window.innerWidth-190)+'px';
    tip.style.top=(ev.clientY-62)+'px';
  });
  s.querySelector('.hit').addEventListener('mouseleave', ()=>{
    cross.setAttribute('opacity','0'); dot.setAttribute('opacity','0'); tip.style.opacity='0';
  });
  return el;
}
const alvoEl=document.getElementById('charts');
['WINV26','WINFUT'].forEach(b=>alvoEl.appendChild(curva(b)));

/* ================= visualizador de trades ================= */
const RES_ROT={alvo:'alvo',stop:'stop',zero:'zero a zero',fim:'fim do pregão'};
const SU_ROT={{su_rot}};
const GESTOES={{gestoes_js}};
let vBase=Object.keys(D)[0], vGest="{{gestao_padrao}}",
    fSetup='todos', fRes='todos', fHull='todos', janela=50, cur=0;
if(!GESTOES.includes(vGest)) vGest=GESTOES[0];

/* --- a paleta ---
   O gráfico desenha em canvas, e canvas não enxerga variável CSS. Lemos as
   cores do :root na mão e relemos quando o sistema troca claro/escuro. */
const CSSV=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const MONO='"IBM Plex Mono", monospace', SANS='Archivo, sans-serif';
let COR={};
function lePaleta(){
  COR={alta:CSSV('--alta'),baixa:CSSV('--baixa'),accent:CSSV('--accent'),
       ink:CSSV('--ink'),ink2:CSSV('--ink-2'),ink3:CSSV('--ink-3'),
       line:CSSV('--line'),line2:CSSV('--line-2'),card:CSSV('--card'),
       pos:CSSV('--pos'),neg:CSSV('--neg'),warn:CSSV('--warn'),zero:CSSV('--zero')};
}
lePaleta();
function alfa(cor,a){
  const h=cor.replace('#',''), n=h.length===3?h.split('').map(c=>c+c).join(''):h;
  return 'rgba('+parseInt(n.slice(0,2),16)+','+parseInt(n.slice(2,4),16)+','
        +parseInt(n.slice(4,6),16)+','+a+')';
}
const corDoRes=r=>r==='alvo'?COR.pos:r==='stop'?COR.neg:r==='zero'?COR.zero:COR.warn;
const PRECO=v=>NF.format(Math.round(v));

/* --- as peças de desenho próprias, em cima do klinecharts ---------------
   São quatro: a linha de nível (entrada/stop/parcial/alvo, com a etiqueta
   de preço no eixo), a marca de barra (gatilho/entrada/saída), a faixa do
   trade aberto e a seta do lado. */
klinecharts.registerOverlay({
  name:'rin-nivel', totalStep:2, lock:true,
  needDefaultPointFigure:false, needDefaultXAxisFigure:false, needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates,bounding})=>{
    const e=overlay.extendData, y=coordinates[0].y;
    return [
      {type:'line',ignoreEvent:true,
       attrs:{coordinates:[{x:0,y:y},{x:bounding.width,y:y}]},
       styles:{color:e.cor,size:1,style:e.cheia?'solid':'dashed',dashedValue:[4,3]}},
      {type:'text',ignoreEvent:true,
       attrs:{x:e.dir?bounding.width-4:4,y:y-3,text:e.rot,
              align:e.dir?'right':'left',baseline:'bottom'},
       styles:{color:e.cor,size:10,family:SANS,weight:'600',
               backgroundColor:alfa(COR.card,.75),
               paddingLeft:4,paddingRight:4,paddingTop:1,paddingBottom:1,borderRadius:2}}
    ];
  },
  createYAxisFigures:({overlay,coordinates,bounding})=>{
    const e=overlay.extendData;
    if(!e.preco) return [];
    return {type:'text',ignoreEvent:true,
      attrs:{x:bounding.width-2,y:coordinates[0].y,text:e.preco,align:'right',baseline:'middle'},
      styles:{color:COR.card,size:10,family:MONO,weight:'600',backgroundColor:e.cor,
              paddingLeft:4,paddingRight:4,paddingTop:2,paddingBottom:2,borderRadius:2}};
  }
});
klinecharts.registerOverlay({
  name:'rin-marca', totalStep:2, lock:true,
  needDefaultPointFigure:false, needDefaultXAxisFigure:false, needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates,bounding})=>{
    const e=overlay.extendData, x=coordinates[0].x;
    return [
      {type:'line',ignoreEvent:true,
       attrs:{coordinates:[{x:x,y:0},{x:x,y:bounding.height}]},
       styles:{color:e.cor,size:1,style:'dashed',dashedValue:[2,3]}},
      /* as três marcas caem em degraus: gatilho, entrada e saída costumam ficar
         a poucas barras uma da outra, e lado a lado as etiquetas se cobriam */
      {type:'text',ignoreEvent:true,
       attrs:{x:x,y:bounding.height-4-e.degrau*19,text:e.rot,align:'center',
              baseline:'bottom'},
       styles:{color:COR.card,size:10,family:SANS,weight:'600',backgroundColor:e.cor,
               paddingLeft:4,paddingRight:4,paddingTop:2,paddingBottom:2,borderRadius:2}}
    ];
  }
});
klinecharts.registerOverlay({
  name:'rin-zona', totalStep:3, lock:true,
  needDefaultPointFigure:false, needDefaultXAxisFigure:false, needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates,bounding})=>{
    if(coordinates.length<2) return [];
    const a=Math.min(coordinates[0].x,coordinates[1].x);
    const b=Math.max(coordinates[0].x,coordinates[1].x);
    return [{type:'rect',ignoreEvent:true,
      attrs:{x:a,y:0,width:Math.max(1,b-a),height:bounding.height},
      styles:{style:'fill',color:overlay.extendData.cor}}];
  }
});
klinecharts.registerOverlay({
  name:'rin-seta', totalStep:2, lock:true,
  needDefaultPointFigure:false, needDefaultXAxisFigure:false, needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates})=>{
    const e=overlay.extendData, x=coordinates[0].x, y=coordinates[0].y, d=e.compra?1:-1;
    return [{type:'polygon',ignoreEvent:true,
      attrs:{coordinates:[{x:x,y:y+d*7},{x:x-5,y:y+d*17},{x:x+5,y:y+d*17}]},
      styles:{style:'fill',color:e.cor}}];
  }
});

/* As médias, o canal e o índice não são recalculados aqui: vêm prontos da
   engine, pendurados em cada barra. O indicador só repassa. */
klinecharts.registerIndicator({
  name:'DTA_CTX', shortName:'contexto', series:'price', precision:0,
  figures:[{key:'ema',title:'EMA: ',type:'line'},
           {key:'hma',title:'Hull: ',type:'line'},
           {key:'ks',title:'Keltner+: ',type:'line'},
           {key:'ki',title:'Keltner−: ',type:'line'}],
  calc:dl=>dl.map(k=>({ema:k.ema,hma:k.hma,ks:k.ks,ki:k.ki}))
});
klinecharts.registerIndicator({
  name:'DTA_ESF', shortName:'esforço', precision:0, minValue:-100, maxValue:100,
  figures:[{key:'esf',title:'índice: ',type:'bar',baseValue:0,
    styles:d=>{
      const v=(d.current.indicatorData||{}).esf||0;
      return {color:alfa(v>=0?COR.alta:COR.baixa, Math.abs(v)>={{nivel_js}}?.95:.28)};
    }}],
  calc:dl=>dl.map(k=>({esf:k.esf}))
});

/* --- o gráfico --------------------------------------------------------
   As barras são de 10.000 ticks, não de tempo: o eixo anda num passo
   sintético de um minuto por barra e o rótulo mostra o horário real. */
const T_BARRA=60000, ALT_ESF=104;
let kchart=null, kDia=null, kT0=0;
const iDe=ts=>Math.round((ts-kT0)/T_BARRA);

function estilos(){
  return {
    grid:{horizontal:{color:COR.line2},vertical:{show:false}},
    candle:{
      bar:{upColor:COR.alta,downColor:COR.baixa,noChangeColor:COR.ink3,
           upBorderColor:COR.alta,downBorderColor:COR.baixa,noChangeBorderColor:COR.ink3,
           upWickColor:COR.alta,downWickColor:COR.baixa,noChangeWickColor:COR.ink3},
      priceMark:{high:{color:COR.ink3,textSize:10,textFamily:MONO},
                 low:{color:COR.ink3,textSize:10,textFamily:MONO},
                 last:{show:false}},
      tooltip:{showRule:'follow_cross',
        rect:{color:COR.card,borderColor:COR.line},
        text:{size:11,family:MONO,color:COR.ink2},
        custom:dados=>{
          const k=dados.current, i=iDe(k.timestamp);
          const esf=kDia?(kDia.x[i]||0):0;
          return [
            {title:{text:'hora',color:COR.ink3},
             value:{text:kDia?(kDia.hm[i]||'—'):'—',color:COR.ink}},
            {title:{text:'abre',color:COR.ink3},value:{text:PRECO(k.open),color:COR.ink}},
            {title:{text:'máx',color:COR.ink3},value:{text:PRECO(k.high),color:COR.ink}},
            {title:{text:'mín',color:COR.ink3},value:{text:PRECO(k.low),color:COR.ink}},
            {title:{text:'fecha',color:COR.ink3},
             value:{text:PRECO(k.close),color:k.close>=k.open?COR.alta:COR.baixa}},
            {title:{text:'esforço',color:COR.ink3},
             value:{text:(esf>0?'+':'')+esf,
                    color:Math.abs(esf)>={{nivel_js}}?(esf>0?COR.alta:COR.baixa):COR.ink2}},
            {title:{text:'ATR',color:COR.ink3},
             value:{text:kDia?PRECO(kDia.atr[i]||0):'—',color:COR.ink2}}
          ];
        }}},
    indicator:{tooltip:{text:{size:11,family:SANS,color:COR.ink3}}},
    xAxis:{axisLine:{color:COR.line},tickLine:{color:COR.line},
           tickText:{color:COR.ink3,size:10,family:MONO}},
    yAxis:{axisLine:{color:COR.line},tickLine:{color:COR.line},
           tickText:{color:COR.ink3,size:10,family:MONO}},
    separator:{color:COR.line},
    crosshair:{horizontal:{line:{color:COR.ink3,style:'dashed'},
                 text:{color:COR.card,backgroundColor:COR.ink2,borderColor:COR.ink2,
                       size:10,family:MONO}},
               vertical:{line:{color:COR.ink3,style:'dashed'},
                 text:{color:COR.card,backgroundColor:COR.ink2,borderColor:COR.ink2,
                       size:10,family:MONO}}}
  };
}
/* o klinecharts NÃO mescla estilo de linha com o padrão: o array trocado
   substitui o de fábrica inteiro, e cada item precisa vir completo. */
function estiloCtx(){
  const l=(cor,tam,tracejada)=>({color:cor,size:tam,smooth:false,
    style:tracejada?'dashed':'solid',dashedValue:[3,3]});
  return {lines:[l(COR.accent,1.6,false),l(COR.warn,1.6,false),
                 l(COR.ink3,1,true),l(COR.ink3,1,true)]};
}
function iniciaGrafico(){
  kchart=klinecharts.init('kchart',{
    styles:estilos(),
    thousandsSeparator:'.',
    customApi:{
      /* o eixo do tempo é sintético; o rótulo é o horário real da barra */
      formatDate:(fmt,ts,formato,tipo)=>{
        if(!kDia) return '';
        const hm=kDia.hm[iDe(ts)]||'';
        return tipo===0?(kDia.d+'  '+hm):hm;
      },
      formatBigNumber:v=>String(v)
    }
  });
  kchart.setPriceVolumePrecision(0,0);
  kchart.createIndicator({name:'DTA_CTX',styles:estiloCtx()},true,{id:'candle_pane'});
  kchart.createIndicator({name:'DTA_ESF'},false,{id:'esf',height:ALT_ESF});
  /* o resize reparte a altura entre os painéis; refixamos a do esforço para
     ele não ir encolhendo a cada mudança de tamanho. */
  new ResizeObserver(()=>{
    if(!kchart) return;
    kchart.resize();
    kchart.setPaneOptions({id:'esf',height:ALT_ESF});
  }).observe(document.getElementById('kchart'));
  const mq=window.matchMedia('(prefers-color-scheme:dark)');
  const trocaTema=()=>{
    lePaleta();
    kchart.setStyles(estilos());
    kchart.overrideIndicator({name:'DTA_CTX',styles:estiloCtx()},'candle_pane');
    desenha();
  };
  if(mq.addEventListener) mq.addEventListener('change',trocaTema);
}

function carrega(t,dia){
  if(kDia===dia){posiciona(t,dia); return;}
  kDia=dia; kT0=Date.parse(dia.d+'T00:00:00Z');
  const n=dia.o.length, lst=new Array(n);
  for(let i=0;i<n;i++) lst[i]={
    timestamp:kT0+i*T_BARRA,
    open:dia.base+dia.o[i], high:dia.base+dia.h[i],
    low:dia.base+dia.l[i],  close:dia.base+dia.c[i],
    ema:dia.base+dia.ema[i], hma:dia.base+dia.hma[i],
    ks:dia.base+dia.ks[i], ki:dia.base+dia.ki[i],
    esf:dia.x[i]};
  kchart.applyNewData(lst,false,()=>posiciona(t,dia));
}

function posiciona(t,dia){
  const n=dia.o.length, meio=Math.round((t.i+t.k)/2);
  let a=Math.max(0,meio-Math.floor(janela/2));
  let z=Math.min(n-1,a+janela-1); a=Math.max(0,z-janela+1);

  const larg=kchart.getSize('candle_pane','main').width||600;
  kchart.setBarSpace(Math.max(1,Math.min(50,larg/janela)));
  kchart.scrollToDataIndex(z+2);

  const ts=i=>kT0+i*T_BARRA;
  const ent=dia.base+t.ent;
  const stopP=ent-t.s*t.st, parcP=ent+t.s*t.st, alvoP=ent+t.s*t.al;

  kchart.removeOverlay();
  /* a faixa vem primeiro: fica por baixo das linhas e das marcas */
  kchart.createOverlay({name:'rin-zona',lock:true,
    points:[{timestamp:ts(t.f)},{timestamp:ts(t.k)}],
    extendData:{cor:alfa(COR.accent,.07)}},'candle_pane');
  [[alvoP,COR.pos,'alvo',false],[parcP,COR.warn,'parcial',false],
   [ent,COR.accent,'entrada',true],[stopP,COR.neg,'stop',false]].forEach(v=>{
    kchart.createOverlay({name:'rin-nivel',lock:true,points:[{value:v[0]}],
      extendData:{cor:v[1],rot:v[2],cheia:v[3],preco:PRECO(v[0])}},'candle_pane');
  });
  kchart.createOverlay({name:'rin-marca',lock:true,points:[{timestamp:ts(t.i)}],
    extendData:{cor:COR.ink3,rot:'gatilho',degrau:2}},'candle_pane');
  kchart.createOverlay({name:'rin-marca',lock:true,points:[{timestamp:ts(t.f)}],
    extendData:{cor:COR.accent,rot:'entrada',degrau:1}},'candle_pane');
  kchart.createOverlay({name:'rin-marca',lock:true,points:[{timestamp:ts(t.k)}],
    extendData:{cor:corDoRes(t.res),rot:RES_ROT[t.res],degrau:0}},'candle_pane');
  kchart.createOverlay({name:'rin-seta',lock:true,
    points:[{timestamp:ts(t.i),value:dia.base+(t.s===1?dia.l[t.i]:dia.h[t.i])}],
    extendData:{cor:t.s===1?COR.alta:COR.baixa,compra:t.s===1}},'candle_pane');
  /* o corte do gatilho; rótulo à direita, que é onde sobra espaço no painel */
  [{{nivel_js}},-{{nivel_js}}].forEach(v=>{
    kchart.createOverlay({name:'rin-nivel',lock:true,points:[{value:v}],
      extendData:{cor:COR.ink3,rot:(v>0?'+':'−')+Math.abs(v),cheia:false,preco:'',dir:true}},'esf');
  });
}

function lista_trades(){ return D[vBase].trades[vGest]||[]; }
function filtrados(){
  return lista_trades().filter(t=>(fSetup==='todos'||t.su===fSetup)
    &&(fRes==='todos'||t.res===fRes)
    &&(fHull==='todos'||(fHull==='oposto'?t.dh<0:t.dh>=0)));
}
function desenha(){
  const lst=filtrados(), ficha=document.getElementById('ficha');
  const cab=document.getElementById('kcab'), vazio=document.getElementById('kvazio');
  if(!lst.length){
    vazio.hidden=false;
    vazio.textContent='Nenhum trade com estes filtros.';
    cab.innerHTML=''; ficha.innerHTML=''; document.getElementById('lista').innerHTML='';
    document.getElementById('cont').textContent='0 de 0';
    document.getElementById('listaTit').textContent='Trades filtrados';
    document.getElementById('btnAnt').disabled=true;
    document.getElementById('btnProx').disabled=true;
    return;
  }
  vazio.hidden=true;
  cur=Math.max(0,Math.min(cur,lst.length-1));
  const t=lst[cur], dia=D[vBase].dias[t.d];
  const ent=dia.base+t.ent;
  const stopP=ent-t.s*t.st, parcP=ent+t.s*t.st, alvoP=ent+t.s*t.al;

  cab.innerHTML='<b>'+vBase+' · '+dia.d+'</b>'
    +'<span>'+SU_ROT[t.su]+' · '+(t.s===1?'compra':'venda')+' · '+GEST_ROT[vGest]+'</span>'
    +'<span class="dica">'+dia.o.length+' barras no pregão · janela inicial de '+janela+'</span>';
  carrega(t,dia);

  const c=t.pnl>0?'pos':t.pnl<0?'neg':'zer';
  ficha.innerHTML=`<div class="topo">
      <div class="res ${c}">${t.pnl>0?'+':''}${NF.format(t.pnl)} <span style="font-size:14px;color:var(--ink-3)">pts</span></div>
      <div class="quando">${dia.d} · ${dia.hm[t.i]} · <span class="pill p-${t.res}">${RES_ROT[t.res]}</span></div></div>
    <div class="linhas">
      <div class="ln"><span class="k">setup</span><span class="v">${SU_ROT[t.su]}</span></div>
      <div class="ln"><span class="k">lado</span><span class="v">${t.s===1?'compra':'venda'}</span></div>
      <div class="ln"><span class="k">entrada</span><span class="v">${PRECO(ent)}</span></div>
      <div class="ln"><span class="k">stop</span><span class="v neg">${PRECO(stopP)} <span style="color:var(--ink-3)">(${Math.round(t.st)})</span></span></div>
      <div class="ln"><span class="k">parcial</span><span class="v" style="color:var(--warn)">${PRECO(parcP)}</span></div>
      <div class="ln"><span class="k">alvo</span><span class="v pos">${PRECO(alvoP)}</span></div>
      <div class="ln"><span class="k">dh · de</span><span class="v">${t.dh.toFixed(2).replace('.',',')} · ${t.de.toFixed(2).replace('.',',')}</span></div>
      <div class="ln"><span class="k">duração</span><span class="v">${t.bar} ${t.bar===1?'barra':'barras'}</span></div>
      <div class="ln"><span class="k">espera no fill</span><span class="v">${t.f-t.i} ${t.f-t.i===1?'barra':'barras'}</span></div>
      <div class="ln"><span class="k">R$ / contrato</span><span class="v ${c}">${(t.pnl*0.2).toFixed(2).replace('.',',')}</span></div>
    </div>`;

  const tb=document.getElementById('lista');
  tb.innerHTML=lst.map((x,i)=>{
    const cc=x.pnl>0?'pos':x.pnl<0?'neg':'zer';
    return `<tr data-i="${i}" ${i===cur?'aria-current="true"':''}><td class="num">${i+1}</td>`
      +`<td>${x.dia.slice(5)}</td><td>${x.su}</td><td>${x.s===1?'compra':'venda'}</td>`
      +`<td class="num ${cc}">${x.pnl>0?'+':''}${NF.format(x.pnl)}</td></tr>`;
  }).join('');
  tb.querySelectorAll('tr').forEach(tr=>{tr.onclick=()=>{cur=+tr.dataset.i;desenha();};});
  const at=tb.querySelector('[aria-current="true"]'); if(at) at.scrollIntoView({block:'nearest'});

  const soma=lst.reduce((s,x)=>s+x.pnl,0), ac=lst.filter(x=>x.pnl>0).length;
  document.getElementById('cont').textContent=(cur+1)+' de '+lst.length;
  document.getElementById('listaTit').textContent=
    `Trades filtrados — ${lst.length} · ${soma>0?'+':''}${NF.format(Math.round(soma))} pts · ${Math.round(100*ac/lst.length)}% acerto`;
  document.getElementById('btnAnt').disabled=cur===0;
  document.getElementById('btnProx').disabled=cur===lst.length-1;
}
function grupo(el,opcoes,valor,onda){
  el.innerHTML='';
  opcoes.forEach(([v,rot])=>{
    const b=document.createElement('button');
    b.textContent=rot; b.setAttribute('aria-pressed',String(v===valor));
    b.onclick=()=>onda(v); el.appendChild(b);
  });
}
function montaControles(){
  grupo(document.getElementById('gBase'),Object.keys(D).map(k=>[k,k]),vBase,
        v=>{vBase=v;cur=0;montaControles();desenha();});
  grupo(document.getElementById('gGestao'),GESTOES.map(v=>[v,GEST_ROT[v]]),vGest,
        v=>{vGest=v;cur=0;montaControles();desenha();});
  const sus=['todos',...[...new Set(lista_trades().map(t=>t.su))].sort()];
  grupo(document.getElementById('gSetup'),sus.map(v=>[v,v]),fSetup,
        v=>{fSetup=v;cur=0;montaControles();desenha();});
  grupo(document.getElementById('gHull'),
        [['todos','todos'],['oposto','lado oposto'],['mesmo','lado da Hull']],fHull,
        v=>{fHull=v;cur=0;montaControles();desenha();});
  grupo(document.getElementById('gRes'),
        [['todos','todos'],['alvo','alvo'],['stop','stop'],['zero','zero a zero']],fRes,
        v=>{fRes=v;cur=0;montaControles();desenha();});
}
document.getElementById('btnAnt').onclick=()=>{cur--;desenha();};
document.getElementById('btnProx').onclick=()=>{cur++;desenha();};
document.getElementById('selJanela').onchange=e=>{janela=+e.target.value;desenha();};
document.addEventListener('keydown',e=>{
  if(e.target.tagName==='SELECT') return;
  if(e.key==='ArrowLeft'&&cur>0){cur--;desenha();}
  if(e.key==='ArrowRight'){cur++;desenha();}
});
iniciaGrafico(); montaControles(); desenha();
</script>
"""
