# -*- coding: utf-8 -*-
"""Molde do relatorio.html. Substituicao simples de {{chave}}.

Nao ha numero escrito aqui: tudo vem do contexto montado por relatorio.py
a partir de saida/resumo.json.
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


MOLDE = r"""<title>Rincones1</title>
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
.quadro svg{display:block;width:100%;height:auto;overflow:visible}
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
    <h1>Rincones1</h1>
    <p class="lede">Um gatilho de esforço decide <em>quando</em>. Uma média decide <em>que tipo</em> de coisa aconteceu — e portanto se o trade vai a favor ou contra o movimento.</p>
    <div class="spec">
      <span class="chip">stop <b>{{stop_pad}}</b> ou <b>100</b></span>
      <span class="chip">parcial <b>{{frac}}%</b> na distância do stop</span>
      <span class="chip">stop na média da operação</span>
      <span class="chip">alvo <b>{{alvo}}</b></span>
      <span class="chip">entrada limitada no meio do candle</span>
      <span class="chip">jun–ago/2026</span>
    </div>
  </div>
</header>

<div class="wrap">

<section>
  <h2><span class="n">01</span> O resultado</h2>
  <h3>Carteira A + B, uma posição por vez</h3>
  <p class="sub">Duas bases medidas separadamente, com o stop padrão de {{stop_pad}}. Números <strong>brutos</strong> — sem custo, sem slippage. <code>t</code> é o t de Student sobre as médias diárias; <code>PF</code> é o fator de lucro; <code>DD</code> é o rebaixamento máximo, em pontos.</p>

  <div class="tiles">
    <div class="tile"><div class="tile-k">EV por trade</div><div class="tile-v pos">{{ev26}}</div><div class="tile-s">WINV26 · pontos</div></div>
    <div class="tile"><div class="tile-k">EV por trade</div><div class="tile-v pos">{{evfu}}</div><div class="tile-s">WINFUT · pontos</div></div>
    <div class="tile"><div class="tile-k">Acerto</div><div class="tile-v">{{ac26}} / {{acfu}}</div><div class="tile-s">WINV26 / WINFUT</div></div>
    <div class="tile"><div class="tile-k">t (diário)</div><div class="tile-v">{{t26}} / {{tfu}}</div><div class="tile-s">{{n26}} e {{nfu}} trades</div></div>
    <div class="tile"><div class="tile-k">Frequência</div><div class="tile-v">~5</div><div class="tile-s">trades por pregão</div></div>
  </div>

  <div class="note">
    <div class="lab">As respostas deste relatório</div>
    <p>{{ver_setups}}</p>
    <p>{{ver_stop}}</p>
    <p>E <strong>a regra da barra seguinte</strong> custa pouco: aborta cerca de um sinal em dez. O gatilho desta rodada é o <strong>novo</strong> — o eixo do deslocamento passou a medir o vaivém do preço dentro da barra. A seção 02 mede o que isso mudou.</p>
  </div>
</section>

<section>
  <h2><span class="n">02</span> O eixo [E2]</h2>
  <h3>O gatilho mudou: o deslocamento virou vaivém</h3>
  <p>O índice de esforço tem três eixos — volume, deslocamento e tempo. O eixo do <strong>deslocamento</strong> era <code>|delta| / |Close−Open|</code>: agressão por ponto de <em>saldo</em>. Saldo não é caminho. Uma barra que sobe 60, cai 65 e fecha 30 acima da abertura tem o mesmo <code>|Close−Open|</code> de uma que sobe 30 em linha reta — e as duas contavam igual.</p>
  <p class="sub">O eixo novo é <code>{{e2_rot}}</code>, com <code>percurso = 2·(High−Low) − |Close−Open|</code>, o menor caminho compatível com o OHLC, e <code>volta = 1 − |Close−Open|/percurso</code>, a fração dele que foi desfeita. Produto de duas frações entre 0 e 1, não razão — razão entre peças de dispersão muito diferente mede só a mais volátil das duas. Derivação e medição em <code>Ticks_Esforco_Hist_v2.ntsl</code>.</p>

  {{tab_e2}}

  <div class="note">
    <div class="lab">O que a troca mudou</div>
    <p>{{ver_e2}}</p>
  </div>

  <div class="note">
    <div class="lab">O filtro “E2 não dominante” sobreviveu?</div>
    <p>{{ver_filtro_e2}}</p>
  </div>
</section>

<section>
  <h2><span class="n">03</span> A regra da barra seguinte</h2>
  <h3>Ou preenche na barra seguinte, ou o trade morre</h3>
  <p class="sub">A ordem limitada no meio do candle do gatilho vale por <strong>uma barra</strong>. Não preencheu, o trade é <strong>abortado</strong> — não se persegue o preço, não se deixa ordem esquecida no livro. <strong>Todo número deste relatório já está sob essa regra.</strong></p>

  <p>{{ver_abortos}}</p>

  <div class="note">
    <div class="lab">O que a regra mudou</div>
    <p>{{ver_fill}}</p>
    <p>Nove em cada dez preenchimentos já aconteciam na barra seguinte, então o que a regra corta é a <strong>cauda</strong> — os sinais que o preço demorou a revisitar, que são justamente os piores. O ganho real dela não está na estatística: está em <strong>não deixar você negociando um sinal de dez minutos atrás</strong>.</p>
    <div class="scroll">{{tab_fill}}</div>
  </div>
</section>

<section>
  <h2><span class="n">04</span> Os três setups</h2>
  <h3>Mesmo gatilho, regimes diferentes</h3>
  <p class="sub">Cada setup medido isolado — todo sinal vira trade, sem competir com os outros. É a comparação limpa entre eles. Valores: <strong>EV em pontos</strong>, <code>t</code> e fator de lucro, com stop {{stop_pad}}.</p>
  <div class="setups">{{cards}}</div>

  <div class="note risk">
    <div class="lab">Por que C não funciona</div>
    <p>Testei inverter o sinal (tratar a esticada como rompimento): sobram 0 e 8 trades. A combinação “médias emboladas <em>e</em> preço longe delas” quase não existe — se o preço se afastou de verdade, as médias já não estão mais emboladas.</p>
    <p>A explicação econômica é coerente com o resto: o gatilho é um sinal de <strong>exaustão</strong>, e em regime embolado não houve movimento para exaurir.</p>
  </div>
</section>

<section>
  <h2><span class="n">05</span> A média que dá a direção</h2>
  <h3>Trocar as três EMAs por uma adaptativa ajuda?</h3>
  <p>Você perguntou se uma <strong>KAMA</strong>, <strong>Hull</strong>, <strong>T3</strong> ou <strong>Jurik</strong> não faria melhor que o empilhamento de três exponenciais. Testei as quatro. Com média única, a direção passa a ser o <strong>sinal da inclinação</strong> dela nas últimas {{ma_slope}} barras, normalizada pelo range médio, e o “toque” passa a ser encostar nessa única linha.</p>
  <p class="sub">Carteira <strong>só A</strong> — o setup que carrega a estratégia. Cada família teve período e corte de inclinação varridos, e o valor escolhido foi o que mede bem <strong>nas duas bases</strong>, não o pico de uma.</p>

  <p class="sub"><b>Stop {{stop_pad}}:</b></p>
  {{variantes_150}}
  <p class="sub"><b>Stop 100:</b></p>
  {{variantes_100}}

  <div class="note">
    <div class="lab">A resposta</div>
    <p>{{ver_ma}}</p>
    <p>Faz sentido que o empilhamento vença: ele exige <strong>concordância entre três escalas de tempo</strong>, e isso é informação que a inclinação de uma linha só não carrega. Uma média adaptativa resolve o atraso; não resolve a falta de confirmação.</p>
  </div>

  <div class="note risk">
    <div class="lab">Sobre a “Jurik”</div>
    <p>O JMA da Jurik Research é <strong>proprietário e não publicado</strong>. O que está aqui é uma aproximação pública do estilo — média adaptativa com correção de fase. Leia a linha dela como “uma adaptativa muito suavizada”, <strong>não</strong> como “o JMA foi testado”. Se o resultado dela importasse para a sua decisão, o certo seria licenciar o indicador de verdade e refazer.</p>
  </div>
</section>

<section>
  <h2><span class="n">06</span> O stop</h2>
  <h3>100 contra 150, lado a lado</h3>
  <p>Você opera com 150. Medido lado a lado, com o resto igual (parcial de {{frac}}% na distância do stop, alvo {{alvo}}). Trocar o stop troca as duas linhas: com 150 a parcial sai em +150 e o alvo cheio paga +225 por contrato; com 100, +100 e +200.</p>
  {{stops}}
  <p>{{ver_stop}}</p>

  <h3>A regra da parcial</h3>
  <p class="sub">Quando a parcial sai, o stop do restante vai para a <strong>média da operação</strong> — o preço em que o que já foi realizado cancela exatamente a perda do resto. Com meia posição e a parcial na distância do stop, esse preço <strong>é o stop inicial</strong>: o stop não anda, e o trade que volta morre em <strong>zero de verdade</strong>. A coluna “zero” é a fração dos trades que termina assim.</p>
  {{tab_gestao}}
  <div class="note risk">
    <div class="lab">O que estava errado antes</div>
    <p>{{ver_gestao}}</p>
  </div>
  <p class="sub">O preço é acerto: com stop mais curto você é parado mais vezes. No WINFUT, carteira só A, o acerto cai de {{ac_a_fu_150}} para {{ac_a_fu_100}} — mas cada perda é menor, e o saldo melhora.</p>
</section>

<section>
  <h2><span class="n">07</span> Curva de capital</h2>
  <h3>Trade a trade, carteira A + B</h3>
  <p class="sub">Pontos acumulados, stop {{stop_pad}}. Passe o mouse para ver cada operação. As duas bases se sobrepõem no tempo — não são amostras independentes.</p>
  <div class="charts" id="charts"></div>
</section>

<section>
  <h2><span class="n">08</span> Qualidade contra volume</h2>
  <h3>A escolha real da carteira</h3>
  <p>Uma posição por vez, prioridade A &gt; B &gt; C, stop {{stop_pad}}. Adicionar o setup B <strong>soma mais pontos no total</strong> e <strong>dobra o drawdown</strong>. Adicionar C piora tudo nas duas bases.</p>
  {{cart26}}
  {{cartfu}}
  <p>Não há resposta única. <strong>Se o seu limite é drawdown, é só A</strong> — melhor EV, melhor <code>t</code>, melhor PF e rebaixamento bem menor, a ~2,5 trades por pregão. Se é aproveitar o dia, é A + B.</p>
</section>

<section>
  <h2><span class="n">09</span> Alvo e parcial</h2>
  <h3>O alvo de 300 está no ponto</h3>
  <p>EV em pontos, carteira A + B, com a <strong>parcial acompanhando o stop de cada linha</strong>. A célula em destaque de cada linha é a melhor daquela linha.</p>
  <div class="charts">{{grade26}}{{gradefu}}</div>
  <p><strong>O alvo de {{alvo}} é o melhor da linha em todas as seis linhas das duas tabelas.</strong> Não é um pico isolado: 200 é pior, 400 e 500 são piores.</p>

  <div class="note">
    <div class="lab">Sobre a entrada</div>
    <p>Limitada no meio do candle: <span class="mark">{{ent26_meio}}</span> e <span class="mark">{{entfu_meio}}</span>. A mercado no fechamento: <span class="mark">{{ent26_fecha}}</span> e <span class="mark">{{entfu_fecha}}</span>.</p>
    <p>{{ver_entrada}}</p>
    <p>Isso <strong>não</strong> quer dizer trocar a limitada pela ordem a mercado: as duas linhas medem carteiras diferentes — a mercado faz ~15% mais trades porque nunca aborta. Quer dizer que <strong>perder o preenchimento não é valor esperado perdido</strong>, e que entrar a mercado no fechamento é um plano B legítimo se você preferir volume de operações a preço de entrada.</p>
    <p>Na prática: <strong>se você perder o preenchimento da limitada, entrar a mercado não estraga o trade.</strong></p>
  </div>
</section>

<section>
  <h2><span class="n">10</span> Fora da amostra</h2>
  <h3>Julho é o único mês que não foi visto</h3>
  <p>As duas bases se sobrepõem — o WINFUT contém a janela inteira do WINV26 e mais julho. O único corte quase-independente é o calendário.</p>
  <div class="scroll"><table>
    <caption>WINFUT · carteira A + B · stop {{stop_pad}}</caption>
    <thead><tr><th>mês</th><th class="num">n</th><th class="num">EV</th><th class="num">total</th><th class="num">acerto</th></tr></thead>
    <tbody>{{mes}}</tbody>
  </table></div>
  <p>Julho — o pedaço de dados que não foi visto ao calibrar nada — mede acima da média do conjunto. É o mais próximo de teste fora da amostra que estes dados permitem, e <strong>não é um walk-forward</strong>: são dois meses, e os parâmetros de regime foram varridos olhando os dois arquivos.</p>
</section>

<section>
  <h2><span class="n">11</span> Custos</h2>
  <h3>Leia antes de comemorar</h3>
  <div class="scroll"><table>
    <caption>Carteira A + B · stop {{stop_pad}} · custo de ida e volta, em pontos</caption>
    <thead><tr><th>custo</th><th class="num">WINV26 EV</th><th class="num">t</th><th class="num">WINFUT EV</th><th class="num">t</th></tr></thead>
    <tbody>{{custo}}</tbody>
  </table></div>
  <p>A ~5 trades por pregão, o custo é uma fração material do EV, não um detalhe. A 10 pontos a estratégia ainda vive; a 20 pontos ela praticamente morre no WINFUT.</p>
  <p>E há um custo que <strong>não</strong> está aqui: a ordem limitada é assumida preenchida a preço exato assim que o preço toca o nível. Na prática existe fila, e nem todo toque preenche. Esse otimismo empurra os números para cima de um jeito que não sei quantificar com dados de barra.</p>
</section>

<section>
  <h2><span class="n">12</span> Os trades, um a um</h2>
  <h3>Candles, médias, gatilho e desfecho</h3>
  <p class="sub">Todos os sinais de cada setup, medidos isoladamente — inclusive os do setup C desligado, para ver por que ele falha. Navegue com ← → ou clique na lista. Regime das 3 EMAs. O botão <strong>stop</strong> troca a variante: os sinais são os mesmos, o que muda é onde o trade morre — e a parcial acompanha o stop, então trocar o stop move as duas linhas.</p>

  <div class="bar">
    <div class="grp"><span class="lab">base</span><span id="gBase"></span></div>
    <div class="grp"><span class="lab">stop</span><span id="gStop"></span></div>
    <div class="grp"><span class="lab">setup</span><span id="gSetup"></span></div>
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
    <div class="quadro" id="quadro"></div>
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
    <span><i class="sw l" style="background:var(--accent)"></i>EMA 21</span>
    <span><i class="sw l" style="background:var(--ink-3)"></i>EMA 42 / 72</span>
    <span><i class="sw" style="background:var(--neg)"></i>stop</span>
    <span><i class="sw" style="background:var(--warn)"></i>parcial (na distância do stop)</span>
    <span><i class="sw" style="background:var(--pos)"></i>alvo</span>
  </div>
</section>

<section>
  <h2><span class="n">13</span> Ressalvas</h2>
  <h3>O que enfraquece tudo acima</h3>
  <div class="note risk"><div class="lab">Amostra pequena</div>
    <p>{{pregfu}} pregões no WINFUT, {{preg26tr}} com trade no WINV26. Vários <code>t</code> ficam entre +1 e +2, que não é evidência forte. O setup C tem 7 e 19 trades — a conclusão sobre ele é “não há evidência a favor”, não “está provado que perde”.</p></div>
  <div class="note risk"><div class="lab">As bases não são independentes</div>
    <p>WINFUT contém WINV26. Quando as duas concordam, isso vale menos do que parece.</p></div>
  <div class="note risk"><div class="lab">Parâmetros varridos nas mesmas bases</div>
    <p>Os cortes de regime — e agora também o período e a inclinação de cada média adaptativa — foram escolhidos olhando os dois arquivos. Há sobreajuste embutido; o corte de julho é o que existe contra isso, e é fraco. Isso vale <em>especialmente</em> para a comparação de médias da seção 05: cada família ganhou uma varredura própria.</p></div>
  <div class="note risk"><div class="lab">Duas condições do regime ajudam menos do que parecem</div>
    <p>O leque mínimo mede melhor quanto <strong>menor</strong> — exigir leque aberto piora. E o toque na média é quase indiferente: sem exigir toque nenhum, o setup A mede praticamente igual. O que carrega o A é <strong>o alinhamento das médias mais o gatilho a favor</strong>, não a geometria fina do pullback.</p></div>
  <div class="note risk"><div class="lab">O filtro de “movimento rápido” é inerte</div>
    <p>Exigir percentil de velocidade alto no setup B não muda nada: o gatilho já exige índice ≥ 0,80 e o índice já contém o eixo do tempo — a barra do sinal <strong>já é</strong> rápida por construção.</p></div>
  <div class="note risk"><div class="lab">Sem filtro de horário, rolagem ou vencimento</div>
    <p>Abertura e fechamento têm dinâmica própria e certamente contaminam os números.</p></div>
</section>

<section>
  <h2><span class="n">14</span> O que eu faria</h2>
  <h3>Em ordem</h3>
  <ol class="acoes">
    <li>{{acao_stop}}</li>
    <li>{{acao_carteira}}</li>
    <li>{{acao_ma}}</li>
    <li><strong>Manter o alvo em {{alvo}}.</strong> Melhor da linha nas seis linhas das duas grades.</li>
    <li><strong>Não ligar o setup C.</strong></li>
    <li><strong>Medir o custo real da sua corretora</strong> e refazer a seção 11 com o número verdadeiro antes de dimensionar posição.</li>
  </ol>
</section>

<footer>
  <p>Gerado por <code>python rodar.py &amp;&amp; python relatorio.py</code> · especificação em <code>ESTRATEGIA.md</code> · números completos em <code>RESULTADOS.md</code> · operação a operação em <code>saida/trades_*.csv</code></p>
</footer>
</div>

<div class="tip" id="tip"></div>

<script>
const EQ = {
  WINV26: {rot:"WINV26", eq:{{eq26}}, su:"{{su26}}", cs:"{{preg26tr}} pregões com trade"},
  WINFUT: {rot:"WINFUT", eq:{{eqfu}}, su:"{{sufu}}", cs:"{{pregfu}} pregões"}
};
const D = {{G}};
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
const SU_ROT={A:'A · tendência',B:'B · reversão rápida',C:'C · consolidação'};
const ALVO_V={{alvo}}, STOPS_V={{stops_js}}, PARC_FIXA={{parc_fixa_js}};
let vBase=Object.keys(D)[0], vStop=String({{stop_pad}}), fSetup='todos', fRes='todos', janela=50, cur=0;
if(!STOPS_V.includes(vStop)) vStop=STOPS_V[0];
const stopPts=()=>+vStop, parcPts=()=>PARC_FIXA===null?+vStop:PARC_FIXA;

function grupo(el,opcoes,valor,onda){
  el.innerHTML='';
  opcoes.forEach(([v,rot])=>{
    const b=document.createElement('button');
    b.textContent=rot; b.setAttribute('aria-pressed',String(v===valor));
    b.onclick=()=>onda(v); el.appendChild(b);
  });
}
function lista_trades(){ return D[vBase].trades[vStop]||[]; }
function filtrados(){
  return lista_trades().filter(t=>(fSetup==='todos'||t.su===fSetup)&&(fRes==='todos'||t.res===fRes));
}
function desenha(){
  const lst=filtrados(), quadro=document.getElementById('quadro'), ficha=document.getElementById('ficha');
  if(!lst.length){
    quadro.innerHTML='<p class="vazio">Nenhum trade com estes filtros.</p>';
    ficha.innerHTML=''; document.getElementById('lista').innerHTML='';
    document.getElementById('cont').textContent='0 de 0'; return;
  }
  cur=Math.max(0,Math.min(cur,lst.length-1));
  const t=lst[cur], dia=D[vBase].dias[t.d];
  const meio=Math.round((t.i+t.k)/2), n=dia.o.length;
  let a=Math.max(0,meio-Math.floor(janela/2));
  let z=Math.min(n-1,a+janela-1); a=Math.max(0,z-janela+1);

  const W=760,HP=340,HH=74,MT=10,ML=8,MR=64,GAP=10, iw=W-ML-MR, m=z-a+1;
  const bw=iw/m, cw=Math.max(1.6,Math.min(11,bw*0.62));
  let lo=Infinity,hi=-Infinity;
  for(let i=a;i<=z;i++){
    lo=Math.min(lo,dia.l[i],dia.e1[i],dia.e2[i],dia.e3[i]);
    hi=Math.max(hi,dia.h[i],dia.e1[i],dia.e2[i],dia.e3[i]);
  }
  const stopP=t.ent-t.s*stopPts(), alvoP=t.ent+t.s*ALVO_V, parcP=t.ent+t.s*parcPts();
  [stopP,alvoP,parcP,t.ent].forEach(v=>{lo=Math.min(lo,v);hi=Math.max(hi,v);});
  const pad=(hi-lo)*0.06||20; lo-=pad; hi+=pad;
  const X=i=>ML+(i-a+0.5)*bw, Y=v=>MT+HP-(v-lo)/(hi-lo)*HP;
  const preco=v=>NF.format(Math.round(v+dia.base));
  let s='';
  [[alvoP,'var(--pos)','alvo'],[parcP,'var(--warn)','parcial'],
   [t.ent,'var(--accent)','entrada'],[stopP,'var(--neg)','stop']].forEach(([v,cor,rot])=>{
    s+=`<line x1="${ML}" x2="${W-MR}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}" stroke="${cor}" stroke-width="1" stroke-dasharray="${rot==='entrada'?'':'4 3'}" opacity=".85"/>`
      +`<text x="${W-MR+6}" y="${(Y(v)+3.5).toFixed(1)}" font-family="IBM Plex Mono, monospace" font-size="10" fill="${cor}">${rot} ${preco(v)}</text>`;
  });
  const rota=arr=>{let p='';for(let i=a;i<=z;i++)p+=(i===a?'M':'L')+X(i).toFixed(1)+' '+Y(arr[i]).toFixed(1);return p;};
  s+=`<path d="${rota(dia.e3)}" fill="none" stroke="var(--ink-3)" stroke-width="1.2" opacity=".45"/>`;
  s+=`<path d="${rota(dia.e2)}" fill="none" stroke="var(--ink-3)" stroke-width="1.2" opacity=".8"/>`;
  s+=`<path d="${rota(dia.e1)}" fill="none" stroke="var(--accent)" stroke-width="1.6"/>`;
  for(let i=a;i<=z;i++){
    const alta=dia.c[i]>=dia.o[i], cor=alta?'var(--alta)':'var(--baixa)', x=X(i);
    const yo=Y(dia.o[i]), yc=Y(dia.c[i]);
    const y1=Math.min(yo,yc), alt=Math.max(1.2,Math.abs(yc-yo));
    const op=(i>=t.f&&i<=t.k)||i===t.i?1:.5;
    s+=`<line x1="${x.toFixed(1)}" x2="${x.toFixed(1)}" y1="${Y(dia.h[i]).toFixed(1)}" y2="${Y(dia.l[i]).toFixed(1)}" stroke="${cor}" stroke-width="1" opacity="${op}"/>`
      +`<rect x="${(x-cw/2).toFixed(1)}" y="${y1.toFixed(1)}" width="${cw.toFixed(1)}" height="${alt.toFixed(1)}" fill="${cor}" opacity="${op}"/>`;
  }
  const marca=(i,cor,txt,cima)=>{
    if(i<a||i>z) return '';
    const x=X(i), yT=MT-2, yB=MT+HP+2;
    return `<line x1="${x.toFixed(1)}" x2="${x.toFixed(1)}" y1="${yT}" y2="${yB}" stroke="${cor}" stroke-width="1" stroke-dasharray="2 3" opacity=".7"/>`
      +`<text x="${x.toFixed(1)}" y="${cima?yT-3:yB+11}" text-anchor="middle" font-family="Archivo, sans-serif" font-size="10" font-weight="600" fill="${cor}">${txt}</text>`;
  };
  s+=marca(t.i,'var(--ink-3)','gatilho',true);
  s+=marca(t.f,'var(--accent)','entrada',false);
  const corRes=t.res==='alvo'?'var(--pos)':t.res==='stop'?'var(--neg)':t.res==='zero'?'var(--zero)':'var(--warn)';
  s+=marca(t.k,corRes,RES_ROT[t.res],false);
  if(t.i>=a&&t.i<=z){
    const x=X(t.i), y=t.s===1?Y(dia.l[t.i])+16:Y(dia.h[t.i])-16;
    const pts=t.s===1?`${x},${y-9} ${x-6},${y+2} ${x+6},${y+2}`:`${x},${y+9} ${x-6},${y-2} ${x+6},${y-2}`;
    s+=`<polygon points="${pts}" fill="${t.s===1?'var(--alta)':'var(--baixa)'}"/>`;
  }
  const yH=MT+HP+GAP+14;
  let mx=1; for(let i=a;i<=z;i++) mx=Math.max(mx,Math.abs(dia.x[i]));
  const YH=v=>yH+HH/2-(v/mx)*(HH/2-2);
  s+=`<text x="${ML}" y="${yH-4}" font-family="Archivo, sans-serif" font-size="10" font-weight="600" fill="var(--ink-3)">ÍNDICE DE ESFORÇO (sinal = delta)</text>`
    +`<line x1="${ML}" x2="${W-MR}" y1="${YH(0).toFixed(1)}" y2="${YH(0).toFixed(1)}" stroke="var(--line)" stroke-width="1"/>`;
  for(let i=a;i<=z;i++){
    const v=dia.x[i]; if(!v) continue;
    const x=X(i), forte=Math.abs(v)>=80, cor=v>=0?'var(--alta)':'var(--baixa)';
    s+=`<rect x="${(x-cw/2).toFixed(1)}" y="${Math.min(YH(0),YH(v)).toFixed(1)}" width="${cw.toFixed(1)}" height="${Math.abs(YH(v)-YH(0)).toFixed(1)}" fill="${cor}" opacity="${forte?.95:.3}"/>`;
  }
  [80,-80].forEach(v=>{ s+=`<line x1="${ML}" x2="${W-MR}" y1="${YH(v).toFixed(1)}" y2="${YH(v).toFixed(1)}" stroke="var(--ink-3)" stroke-width="1" stroke-dasharray="3 3" opacity=".6"/>`; });
  const hAll=yH+HH+14;
  s+=`<text x="${ML}" y="${hAll}" font-family="IBM Plex Mono, monospace" font-size="10" fill="var(--ink-3)">${dia.hm[a]}</text>`
    +`<text x="${W-MR}" y="${hAll}" text-anchor="end" font-family="IBM Plex Mono, monospace" font-size="10" fill="var(--ink-3)">${dia.hm[z]}</text>`;
  quadro.innerHTML=`<svg viewBox="0 0 ${W} ${hAll+6}" role="img" aria-label="Pregão ${dia.d}, trade ${t.su} ${t.s===1?'de compra':'de venda'}, desfecho ${RES_ROT[t.res]}, ${t.pnl} pontos">${s}</svg>`;

  const c=t.pnl>0?'pos':t.pnl<0?'neg':'zer';
  ficha.innerHTML=`<div class="topo">
      <div class="res ${c}">${t.pnl>0?'+':''}${NF.format(t.pnl)} <span style="font-size:14px;color:var(--ink-3)">pts</span></div>
      <div class="quando">${dia.d} · ${dia.hm[t.i]} · <span class="pill p-${t.res}">${RES_ROT[t.res]}</span></div></div>
    <div class="linhas">
      <div class="ln"><span class="k">setup</span><span class="v">${SU_ROT[t.su]}</span></div>
      <div class="ln"><span class="k">lado</span><span class="v">${t.s===1?'compra':'venda'}</span></div>
      <div class="ln"><span class="k">entrada</span><span class="v">${preco(t.ent)}</span></div>
      <div class="ln"><span class="k">stop</span><span class="v neg">${preco(stopP)}</span></div>
      <div class="ln"><span class="k">parcial</span><span class="v" style="color:var(--warn)">${preco(parcP)}</span></div>
      <div class="ln"><span class="k">alvo</span><span class="v pos">${preco(alvoP)}</span></div>
      <div class="ln"><span class="k">duração</span><span class="v">${t.bar} barras</span></div>
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
function montaControles(){
  grupo(document.getElementById('gBase'),Object.keys(D).map(k=>[k,k]),vBase,
        v=>{vBase=v;cur=0;montaControles();desenha();});
  grupo(document.getElementById('gStop'),STOPS_V.map(v=>[v,'stop '+v]),vStop,
        v=>{vStop=v;cur=0;montaControles();desenha();});
  const sus=['todos',...[...new Set(lista_trades().map(t=>t.su))].sort()];
  grupo(document.getElementById('gSetup'),sus.map(v=>[v,v]),fSetup,
        v=>{fSetup=v;cur=0;montaControles();desenha();});
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
montaControles(); desenha();
</script>
"""
