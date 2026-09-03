# -*- coding: utf-8 -*-
"""Molde do relatorio.html. Substituicao simples de {{chave}}.

Nao ha numero escrito aqui: tudo vem do contexto montado por relatorio.py a
partir de saida/resumo.json. O sistema visual (as variaveis de cor, a
tipografia, o visualizador) e o mesmo do projeto do WIN, de proposito -- os
dois relatorios sao lidos lado a lado.
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


MOLDE = r"""<title>Rincones1 XAUUSD</title>
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
<header><div class="head">
  <p class="eyebrow">Backtest · XAUUSD · barras de 521 ticks</p>
  <h1>{{titulo}}</h1>
  <p class="lede">{{lede}}</p>
  <div class="spec">
    <span class="chip">{{barras}} barras · <b>{{pregoes}} pregões</b></span>
    <span class="chip">{{ini}} a {{fim}}</span>
    <span class="chip">gatilho <b>{{gat_txt}}</b></span>
    <span class="chip">stop <b>{{stop_pad}}</b> ou <b>{{stop_alt}}</b></span>
    <span class="chip">parcial <b>{{frac}}%</b> na distância do stop</span>
    <span class="chip">alvo <b>{{alvo}}</b></span>
    <span class="chip">entrada <b>a mercado</b></span>
  </div>
</div></header>

<div class="wrap">

<section id="resultado">
  <h2><span class="n">1</span> O resultado</h2>
  <h3>{{h_resultado}}</h3>
  <p class="sub">Tudo em <strong>USD por onça</strong> — 1,00 de movimento vale {{val_ponto}} USD num lote padrão de 100 oz. Números <strong>brutos</strong>: sem spread, sem swap, sem slippage. <code>t</code> é o t de Student sobre as médias diárias; <code>PF</code> é o fator de lucro; <code>DD</code> é o rebaixamento máximo em USD.</p>

  <div class="tiles">
    <div class="tile"><div class="tile-k">EV por trade</div><div class="tile-v {{cls_ev}}">{{ev}}</div><div class="tile-s">USD · amostra inteira</div></div>
    <div class="tile"><div class="tile-k">t (diário)</div><div class="tile-v">{{t}}</div><div class="tile-s">{{n}} trades em {{pregoes}} pregões</div></div>
    <div class="tile"><div class="tile-k">Acerto</div><div class="tile-v">{{acerto}}</div><div class="tile-s">PF {{pf}}</div></div>
    <div class="tile"><div class="tile-k">Nas duas metades</div><div class="tile-v">{{ev_h1}} / {{ev_h2}}</div><div class="tile-s">1ª / 2ª — EV por trade</div></div>
  </div>

  <div class="scroll">{{tab_principal}}</div>

  <div class="note risk"><div class="lab">Leia antes de qualquer coisa</div>
    <p>{{aviso_metades}}</p>
    <p>{{aviso_custo}}</p>
  </div>
</section>

<section id="porte">
  <h2><span class="n">2</span> O que o porte teve de mudar</h2>
  <h3>{{h_porte}}</h3>
  <p>Este backtest é o mesmo de <code>Backtest-Rincones1</code> (WIN, barras de 10.000 ticks) rodando sobre o ouro. A estrutura não mudou: mesmo índice de esforço em percentil causal, mesmos três regimes de média, mesma gestão de parcial e stop. Quatro coisas mudaram — e as quatro foram <strong>medidas</strong>, não escolhidas.</p>
  <div class="scroll">{{tab_porte}}</div>
  <p>{{ver_porte}}</p>
</section>

<section id="eixos">
  <h2><span class="n">3</span> De que eixo é o índice</h2>
  <h3>{{h_eixos}}</h3>
  <p>O índice do WIN soma três eixos em percentil: <code>[E1]</code> volume agredido, <code>[E2]</code> vaivém e <code>[E3]</code> velocidade da barra. O ouro tem um problema antes de qualquer calibração — e ganha um eixo que o WIN não usa, <code>[E4]</code>, o range da barra.</p>
  <div class="note"><div class="lab">[E1] não existe neste ativo</div>
    <p>{{ver_degenerado}}</p>
  </div>
  <p class="sub">Cada linha é um conjunto de eixos, com o nível de corte calibrado para dar uma quantidade comparável de sinais. Carteira completa, stop {{stop_pad}}.</p>
  <div class="scroll">{{tab_eixos}}</div>
  <p>{{ver_eixos}}</p>
</section>

<section id="e2">
  <h2><span class="n">4</span> O eixo [E2]: fórmula antiga contra a nova</h2>
  <h3>{{h_e2}}</h3>
  <p>O eixo <code>[E2]</code> media <code>|delta| / |Close−Open|</code> — agressão por ponto de <em>saldo</em>, cego ao caminho que o preço fez dentro da barra. A versão 2 mede <strong>vaivém</strong>: <code>(|delta|/esforço) × (1 − |Close−Open|/percurso)</code>, com <code>percurso = 2·(High−Low) − |Close−Open|</code>. A derivação está em <code>Ticks_Esforco_v2.mqh</code>.</p>
  <p>O índice padrão daqui não usa <code>[E2]</code> (§ 3), então a comparação roda sobre o índice de <strong>três eixos</strong> <code>[E2]+[E3]+[E4]</code> — a configuração mais próxima do backtest do WIN que este ativo aceita. Todo o resto congelado.</p>
  <div class="scroll">{{tab_e2}}</div>
  <p>{{ver_e2}}</p>
</section>

<section id="geometria">
  <h2><span class="n">5</span> A geometria de rejeição está invertida</h2>
  <h3>{{h_geo}}</h3>
  <p>O gatilho não é só o índice: a barra também tem de ter a <strong>forma</strong> certa. A regra do WIN é a <em>clássica</em> — candle de alta com corpo pequeno alojado na metade de <strong>baixo</strong> do range, isto é, pavio superior grande: subiu dentro da barra e devolveu. É a geometria de exaustão, e vende-se ali.</p>
  <p>No ouro ela mede negativo. Quem mede é o <strong>lado oposto</strong>: candle de alta com o corpo em <strong>cima</strong>, pavio inferior grande — e vende-se ali do mesmo jeito.</p>
  <div class="scroll">{{tab_geo}}</div>
  <p>{{ver_geo}}</p>
  <div class="note"><div class="lab">Não é achado novo</div>
    <p>O <code>Delta_Fraqueza.mqh</code> já tinha registrado, no <code>XAUUSD_19_DT</code>, que “o pavio de exaustão morreu invertido — no ouro a geometria de rejeição não é exaustão”. O <code>[D4]</code> de <code>Ticks_Esforco_v2.mqh</code> repetiu a medição no <code>XAUUSD_521_TK</code>. Este backtest é a terceira vez que o mesmo sinal aparece trocado, agora no nível do trade e não da barra.</p>
  </div>
</section>

<section id="entrada">
  <h2><span class="n">6</span> A entrada limitada não sobrevive à inversão</h2>
  <h3>{{h_entrada}}</h3>
  <p>No WIN a entrada é uma <strong>ordem limitada no meio do candle do gatilho</strong>, válida por uma barra. Ela funciona lá porque a geometria é clássica: numa barra de alta o corpo está embaixo, o meio do candle fica <strong>acima</strong> do fechamento, e uma venda limitada ali é um preço <em>melhor</em> — espera-se o repique para vender mais caro.</p>
  <p>Com a geometria invertida o corpo está em cima. O meio do candle fica <strong>abaixo</strong> do fechamento, a mesma ordem vira um preço <em>pior</em>, e ela preenche quase sempre — porque o preço já está acima dela. Não é uma ordem que espera nada: é meio range de desconto entregue de graça.</p>
  <div class="scroll">{{tab_entrada}}</div>
  <p>{{ver_entrada}}</p>
</section>

<section id="gestao">
  <h2><span class="n">7</span> Stop, alvo e a regra da parcial</h2>
  <h3>{{h_gestao}}</h3>
  <p>O stop do WIN, escalado pelo range médio da barra, dá <b>{{stop_alt}}</b> no ouro. Ele mede positivo — mas o <strong>dobro</strong> dele mede muito melhor, e a razão é estrutural: a barra do gatilho é, por construção, uma barra de range extremo. Um stop de pouco mais de um range médio cabe <em>dentro da própria barra</em> que disparou o trade.</p>
  <p class="sub">EV por trade, em USD, carteira completa. A coluna é o alvo, a linha é o stop.</p>
  <div class="charts">{{grades}}</div>
  <p>{{ver_grade}}</p>

  <h3 style="margin-top:36px">A parcial e o zero a zero</h3>
  <p>A parcial de {{frac}}% sai na <strong>mesma distância do stop</strong>. Só assim a média da operação cai exatamente em cima do stop inicial: o stop não precisa andar, e o trade que volta morre em <strong>zero de verdade</strong>. O modelo antigo punha o stop do restante na entrada e tirava a parcial mais perto — ali o desfecho chamado “zero a zero” pagava dinheiro.</p>
  <div class="scroll">{{tab_gestao}}</div>
  <p>{{ver_gestao}}</p>
</section>

<section id="regimes">
  <h2><span class="n">8</span> Os três setups e as médias de regime</h2>
  <h3>{{h_setups}}</h3>
  <p>No WIN o gatilho é filtrado pelo <strong>regime</strong> das médias: <b>A</b> só entra em tendência com pullback na média, <b>B</b> só na reversão de um afastamento, <b>C</b> só em consolidação. Aqui os três continuam implementados e medidos — e a marca <b>L</b> (“livre”) recolhe o sinal que nenhum regime reivindicou.</p>
  <p class="sub">Setups isolados: todo sinal do setup vira trade, sem competir com os outros. Carteiras: uma posição por vez, prioridade A &gt; B &gt; C &gt; L. Stop {{stop_pad}}.</p>
  <div class="setups">{{cards}}</div>
  <div class="scroll">{{tab_carteiras}}</div>
  <p>{{ver_setups}}</p>

  <h3 style="margin-top:36px">As médias adaptativas</h3>
  <p>A mesma pergunta do projeto do WIN: uma <strong>KAMA</strong>, <strong>Hull</strong>, <strong>T3</strong> ou <strong>Jurik</strong> não separaria melhor os regimes que o empilhamento de três exponenciais? Com média única a direção passa a ser o sinal da inclinação nas últimas {{ma_slope}} barras, normalizada pelo range médio.</p>
  <div class="scroll">{{tab_ma}}</div>
  <p>{{ver_ma}}</p>
</section>

<section id="estabilidade">
  <h2><span class="n">9</span> O corte é uma família ou um pico?</h2>
  <h3>{{h_estab}}</h3>
  <p>O nível <code>{{nivel}}</code> do índice e o corte de posição <code>{{pos}}</code> do corpo saíram de uma varredura sobre esta mesma amostra. Publicar a varredura inteira é o único jeito honesto de mostrar se o resultado é uma região larga ou um pico isolado que o ajuste encontrou.</p>
  <p class="sub">EV por trade em USD, carteira completa, stop {{stop_pad}}. A célula do padrão está marcada.</p>
  <div class="charts">{{estab}}</div>
  <p>{{ver_estab}}</p>
</section>

<section id="curvas">
  <h2><span class="n">10</span> Curvas de capital</h2>
  <h3>Como o resultado chegou</h3>
  <p class="sub">USD acumulados, carteira completa, stop {{stop_pad}}. Passe o mouse para ver cada operação. As duas metades <strong>não são amostras independentes</strong> — são o mesmo histórico partido em dois.</p>
  <div class="charts" id="charts"></div>
  <div class="scroll">{{tab_mes}}</div>
</section>

<section id="custo">
  <h2><span class="n">11</span> O que o custo faz</h2>
  <h3>{{h_custo}}</h3>
  <p>O spread do XAUUSD em corretora de varejo costuma ficar entre <strong>0,20 e 0,40 USD</strong> de ida e volta, e alarga em notícia. Todos os números das seções anteriores são <strong>brutos</strong>.</p>
  <div class="scroll">{{tab_custo}}</div>
  <p>{{ver_custo}}</p>
</section>

<section id="psico">
  <h2><span class="n">12</span> A forma do desempenho</h2>
  <h3>Não é quanto ganha — é como ele chega</h3>
  <p class="sub">Carteira completa, stop {{stop_pad}}, <strong>com {{custo_psico}} USD de custo por trade</strong>. Sem estes números o operador confunde variância normal com estratégia quebrada.</p>
  <div class="scroll">{{tab_psico}}</div>
  <p>{{ver_psico}}</p>
</section>

<section id="limites">
  <h2><span class="n">13</span> Limites</h2>
  <h3>O que este backtest não prova</h3>
  <div class="note risk"><div class="lab">Leia antes de dimensionar posição</div>
    <ul>
      <li><strong>Uma amostra, não duas.</strong> {{lim_amostra}}</li>
      <li><strong>Quatro meses.</strong> {{lim_periodo}}</li>
      <li><strong>O corte foi varrido.</strong> {{lim_varredura}}</li>
      <li><strong>Números brutos.</strong> {{lim_custo}}</li>
      <li><strong>Preenchimento otimista.</strong> Entrada a mercado no fechamento da barra, sem slippage. Quando stop e alvo cabem na mesma barra, assume-se o <em>stop</em> — isso é pessimista e compensa em parte.</li>
      <li><strong>O delta é inferido.</strong> {{lim_delta}}</li>
    </ul>
  </div>
</section>

<section id="acoes">
  <h2><span class="n">14</span> O que fazer com isto</h2>
  <h3>{{h_acoes}}</h3>
  <ol class="acoes">
    <li>{{acao_1}}</li>
    <li>{{acao_2}}</li>
    <li>{{acao_3}}</li>
    <li>{{acao_4}}</li>
  </ol>
</section>

<section id="viz">
  <h2><span class="n">15</span> Trade a trade</h2>
  <h3>O visualizador</h3>
  <p class="sub">Navegue com as setas ← → ou clique na lista. Candles do pregão, as três EMAs, as linhas de entrada, stop, parcial e alvo, as marcas do gatilho e da saída, e o índice de esforço embaixo com a linha de corte.</p>
  <div class="bar">
    <div class="grp"><span class="lab">amostra</span><span id="gBase"></span></div>
    <div class="grp"><span class="lab">stop</span><span id="gStop"></span></div>
    <div class="grp"><span class="lab">setup</span><span id="gSetup"></span></div>
    <div class="grp"><span class="lab">desfecho</span><span id="gRes"></span></div>
    <div class="grp"><span class="lab">janela</span>
      <select id="selJanela"><option value="30">30</option><option value="50" selected>50</option><option value="90">90</option><option value="150">150</option></select></div>
    <div class="grp"><button id="btnAnt">←</button><span class="count" id="cont"></span><button id="btnProx">→</button></div>
  </div>
  <div class="painel">
    <div class="quadro" id="quadro"></div>
    <div class="ficha" id="ficha"></div>
  </div>
  <div class="legenda">
    <span><i class="sw l" style="background:var(--accent)"></i>EMA 21</span>
    <span><i class="sw l" style="background:var(--ink-3)"></i>EMA 42 / 72</span>
    <span><i class="sw" style="background:var(--pos)"></i>alvo</span>
    <span><i class="sw" style="background:var(--warn)"></i>parcial</span>
    <span><i class="sw" style="background:var(--neg)"></i>stop</span>
    <span>índice de esforço em barras — forte acima do corte</span>
  </div>
  <div class="lista-wrap">
    <h4 id="listaTit">Trades filtrados</h4>
    <div class="rolagem"><table><tbody id="lista"></tbody></table></div>
  </div>
</section>

<footer>
  <p>Gerado por <code>python rodar.py &amp;&amp; python relatorio.py</code> · especificação em <code>ESTRATEGIA.md</code> · números completos em <code>RESULTADOS.md</code> · plano operacional em <code>PLANO.md</code> · operação a operação em <code>saida/trades_*.csv</code></p>
</footer>
</div>

<div class="tip" id="tip"></div>

<script>
const EQ = {{EQJS}};
const D = {{G}};
const NF = new Intl.NumberFormat('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
const NP = new Intl.NumberFormat('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
const tip = document.getElementById('tip');

/* ================= curva de capital ================= */
function curva(base){
  const d = EQ[base], eq = d.eq, n = eq.length;
  const W=520,H=210,ML=52,MR=14,MT=10,MB=24, iw=W-ML-MR, ih=H-MT-MB;
  const lo=Math.min(0,...eq), hi=Math.max(0,...eq);
  const pad=(hi-lo)*0.08||10, y0=lo-pad, y1=hi+pad;
  const X=i=>ML+(n<=1?0:i*iw/(n-1)), Y=v=>MT+ih-(v-y0)/(y1-y0)*ih;
  const linha=eq.map((v,i)=>(i?'L':'M')+X(i).toFixed(1)+' '+Y(v).toFixed(1)).join(' ');
  const area=linha+' L'+X(n-1).toFixed(1)+' '+Y(0).toFixed(1)+' L'+X(0).toFixed(1)+' '+Y(0).toFixed(1)+' Z';
  const bruto=(y1-y0)/4, mag=Math.pow(10,Math.floor(Math.log10(bruto)||0));
  const passo=Math.max(mag,Math.ceil(bruto/mag)*mag);
  let grade='';
  for(let v=Math.ceil(y0/passo)*passo; v<=y1; v+=passo){
    grade+=`<line x1="${ML}" x2="${W-MR}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}" stroke="var(--line-2)" stroke-width="1"/>`
         + `<text x="${ML-9}" y="${(Y(v)+4).toFixed(1)}" text-anchor="end" font-family="IBM Plex Mono, monospace" font-size="10" fill="var(--ink-3)">${Math.round(v)}</text>`;
  }
  const fim=eq[n-1], gid='g'+base;
  const svg=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Curva de capital ${d.rot}: ${n} trades, resultado final de ${NF.format(fim)} USD">
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
      +`resultado   ${res>=0?'+':'−'}${NF.format(Math.abs(res))} USD\n`
      +`acumulado   ${eq[i]>=0?'+':'−'}${NF.format(Math.abs(eq[i]))} USD`;
    tip.style.opacity='1';
    tip.style.left=Math.min(ev.clientX+14, window.innerWidth-200)+'px';
    tip.style.top=(ev.clientY-62)+'px';
  });
  s.querySelector('.hit').addEventListener('mouseleave', ()=>{
    cross.setAttribute('opacity','0'); dot.setAttribute('opacity','0'); tip.style.opacity='0';
  });
  return el;
}
const alvoEl=document.getElementById('charts');
Object.keys(EQ).forEach(b=>alvoEl.appendChild(curva(b)));

/* ================= visualizador de trades ================= */
const RES_ROT={alvo:'alvo',stop:'stop',zero:'zero a zero',fim:'fim do pregão'};
const SU_ROT={{SUROT}};
const BASE_ROT={{BASEROT}};
const ALVO_V={{alvo_js}}, STOPS_V={{stops_js}}, PARC_FIXA={{parc_fixa_js}};
const VAL_PONTO={{val_ponto_js}}, NIVEL={{nivel_js}};
let vBase=Object.keys(D)[0], vStop=String({{stop_pad_js}}), fSetup='todos', fRes='todos', janela=50, cur=0;
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

  const W=760,HP=340,HH=74,MT=10,ML=8,MR=78,GAP=10, iw=W-ML-MR, m=z-a+1;
  const bw=iw/m, cw=Math.max(1.6,Math.min(11,bw*0.62));
  let lo=Infinity,hi=-Infinity;
  for(let i=a;i<=z;i++){
    lo=Math.min(lo,dia.l[i],dia.e1[i],dia.e2[i],dia.e3[i]);
    hi=Math.max(hi,dia.h[i],dia.e1[i],dia.e2[i],dia.e3[i]);
  }
  const stopP=t.ent-t.s*stopPts(), alvoP=t.ent+t.s*ALVO_V, parcP=t.ent+t.s*parcPts();
  [stopP,alvoP,parcP,t.ent].forEach(v=>{lo=Math.min(lo,v);hi=Math.max(hi,v);});
  const pad=(hi-lo)*0.06||1; lo-=pad; hi+=pad;
  const X=i=>ML+(i-a+0.5)*bw, Y=v=>MT+HP-(v-lo)/(hi-lo)*HP;
  const preco=v=>NP.format(v+dia.base);
  let s='';
  [[alvoP,'var(--pos)','alvo'],[parcP,'var(--warn)','parcial'],
   [t.ent,'var(--accent)','entrada'],[stopP,'var(--neg)','stop']].forEach(([v,cor,rot])=>{
    s+=`<line x1="${ML}" x2="${W-MR}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}" stroke="${cor}" stroke-width="1" stroke-dasharray="${rot==='entrada'?'':'4 3'}" opacity=".85"/>`
      +`<text x="${W-MR+6}" y="${(Y(v)+3.5).toFixed(1)}" font-family="IBM Plex Mono, monospace" font-size="9.5" fill="${cor}">${rot} ${preco(v)}</text>`;
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
  const YH=v=>yH+HH-(v/100)*HH;
  s+=`<text x="${ML}" y="${yH-4}" font-family="Archivo, sans-serif" font-size="10" font-weight="600" fill="var(--ink-3)">ÍNDICE DE ESFORÇO (percentil do range)</text>`
    +`<line x1="${ML}" x2="${W-MR}" y1="${YH(0).toFixed(1)}" y2="${YH(0).toFixed(1)}" stroke="var(--line)" stroke-width="1"/>`;
  for(let i=a;i<=z;i++){
    const v=dia.x[i]; if(v===null) continue;
    const x=X(i), forte=v>=NIVEL*100, cor=dia.dc[i]>=0?'var(--alta)':'var(--baixa)';
    s+=`<rect x="${(x-cw/2).toFixed(1)}" y="${YH(v).toFixed(1)}" width="${cw.toFixed(1)}" height="${(YH(0)-YH(v)).toFixed(1)}" fill="${cor}" opacity="${forte?.95:.28}"/>`;
  }
  s+=`<line x1="${ML}" x2="${W-MR}" y1="${YH(NIVEL*100).toFixed(1)}" y2="${YH(NIVEL*100).toFixed(1)}" stroke="var(--ink-3)" stroke-width="1" stroke-dasharray="3 3" opacity=".7"/>`;
  const hAll=yH+HH+14;
  s+=`<text x="${ML}" y="${hAll}" font-family="IBM Plex Mono, monospace" font-size="10" fill="var(--ink-3)">${dia.hm[a]}</text>`
    +`<text x="${W-MR}" y="${hAll}" text-anchor="end" font-family="IBM Plex Mono, monospace" font-size="10" fill="var(--ink-3)">${dia.hm[z]}</text>`;
  quadro.innerHTML=`<svg viewBox="0 0 ${W} ${hAll+6}" role="img" aria-label="Pregão ${dia.d}, trade ${t.su} ${t.s===1?'de compra':'de venda'}, desfecho ${RES_ROT[t.res]}, ${t.pnl} USD">${s}</svg>`;

  const c=t.pnl>0?'pos':t.pnl<0?'neg':'zer';
  ficha.innerHTML=`<div class="topo">
      <div class="res ${c}">${t.pnl>0?'+':''}${NF.format(t.pnl)} <span style="font-size:14px;color:var(--ink-3)">USD</span></div>
      <div class="quando">${dia.d} · ${dia.hm[t.i]} · <span class="pill p-${t.res}">${RES_ROT[t.res]}</span></div></div>
    <div class="linhas">
      <div class="ln"><span class="k">setup</span><span class="v">${SU_ROT[t.su]||t.su}</span></div>
      <div class="ln"><span class="k">lado</span><span class="v">${t.s===1?'compra':'venda'}</span></div>
      <div class="ln"><span class="k">entrada</span><span class="v">${preco(t.ent)}</span></div>
      <div class="ln"><span class="k">stop</span><span class="v neg">${preco(stopP)}</span></div>
      <div class="ln"><span class="k">parcial</span><span class="v" style="color:var(--warn)">${preco(parcP)}</span></div>
      <div class="ln"><span class="k">alvo</span><span class="v pos">${preco(alvoP)}</span></div>
      <div class="ln"><span class="k">duração</span><span class="v">${t.bar} barras</span></div>
      <div class="ln"><span class="k">USD / lote de 100 oz</span><span class="v ${c}">${NF.format(t.pnl*VAL_PONTO)}</span></div>
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
    `Trades filtrados — ${lst.length} · ${soma>0?'+':''}${NF.format(soma)} USD · ${Math.round(100*ac/lst.length)}% acerto`;
  document.getElementById('btnAnt').disabled=cur===0;
  document.getElementById('btnProx').disabled=cur===lst.length-1;
}
function montaControles(){
  grupo(document.getElementById('gBase'),Object.keys(D).map(k=>[k,BASE_ROT[k]||k]),vBase,
        v=>{vBase=v;cur=0;montaControles();desenha();});
  grupo(document.getElementById('gStop'),STOPS_V.map(v=>[v,'stop '+v]),vStop,
        v=>{vStop=v;cur=0;montaControles();desenha();});
  const sus=['todos',...[...new Set(lista_trades().map(t=>t.su))].sort()];
  grupo(document.getElementById('gSetup'),sus.map(v=>[v,v]),fSetup,
        v=>{fSetup=v;cur=0;montaControles();desenha();});
  grupo(document.getElementById('gRes'),
        [['todos','todos'],['alvo','alvo'],['stop','stop'],['zero','zero a zero'],['fim','fim']],fRes,
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
