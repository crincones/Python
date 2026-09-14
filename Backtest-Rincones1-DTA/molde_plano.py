# -*- coding: utf-8 -*-
"""
Molde do plano.html.

A pagina e gerada a partir do PROPRIO markdown que plano.py produz --
ha uma fonte de texto so, entao o .md e o .html nao tem como divergir.
O conversor abaixo cobre so o subconjunto de markdown que o plano usa.

DESENHO
  O relatorio e um documento analitico: azul-petroleo, serifada, para ler
  sentado. Este e outro objeto -- um CARTAO DE PROCEDIMENTO, lido em pe,
  antes da abertura, e conferido durante o pregao. Por isso:

  cor      papel quente de cartolina; verde profundo para o "pode operar",
           ambar so para limite rigido, vermelho so para disjuntor. Tres
           cores de sinal, cada uma com um significado unico -- se ambar
           aparecesse em decoracao, ele deixaria de significar limite.
  tipo     Archivo Narrow (titulos, condensada = sinalizacao operacional),
           Libre Franklin (corpo, para varredura rapida), JetBrains Mono
           (numeros, regras e caixas de conferencia).
  layout   goteira a esquerda com o NUMERO da regra pendurado. A numeracao
           aqui e informacao de verdade: e um procedimento em ordem, e a
           ordem importa (contexto -> entrada -> gestao -> registro).
"""
import re


# ------------------------------------------------------- markdown -> html
def _inline(t):
    t = (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
    t = re.sub(r'`([^`]+)`', lambda m: '<code>%s</code>' % m.group(1), t)
    t = re.sub(r'\*\*([^*]+)\*\*', lambda m: '<strong>%s</strong>' % m.group(1), t)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
               lambda m: '<a href="%s">%s</a>' % (m.group(2), m.group(1)), t)
    t = t.replace('☐', '<span class="box">☐</span>')
    return t


def _tabela(linhas):
    """Linhas de uma tabela markdown -> <table>. A 2a linha e o separador."""
    def celulas(l):
        return [c.strip() for c in l.strip().strip('|').split('|')]

    cab = celulas(linhas[0])
    corpo = [celulas(l) for l in linhas[2:]]
    vazio = not any(c for c in cab)

    def td(c, tag='td'):
        num = bool(re.match(r'^[+\-−]?[\d.,]+%?$', c.replace('*', '')))
        cl = ' class="num"' if num else ''
        return '<%s%s>%s</%s>' % (tag, cl, _inline(c), tag)

    th = ('' if vazio else
          '<thead><tr>%s</tr></thead>' % ''.join(td(c, 'th') for c in cab))
    tb = ''.join('<tr>%s</tr>' % ''.join(td(c) for c in l) for l in corpo)
    return '<div class="scroll"><table>%s<tbody>%s</tbody></table></div>' % (th, tb)


def md_para_html(md):
    linhas = md.split('\n')
    out, i, n = [], 0, len(linhas)
    sec_aberta = False

    while i < n:
        l = linhas[i]

        # --- titulo h1: consumido pelo cabecalho da pagina
        if l.startswith('# '):
            i += 1
            continue

        # --- separador de secao
        if l.strip() == '---':
            i += 1
            continue

        # --- h2: abre uma secao com o numero na goteira
        if l.startswith('## '):
            if sec_aberta:
                out.append('</section>')
            txt = l[3:].strip()
            m = re.match(r'^(\d+)\.\s*(.*)$', txt)
            num, tit = (m.group(1), m.group(2)) if m else ('', txt)
            out.append('<section><div class="gut">%s</div><div class="corpo">'
                       '<h2>%s</h2>' % (num, _inline(tit)))
            sec_aberta = True
            i += 1
            continue

        if l.startswith('### '):
            out.append('<h3>%s</h3>' % _inline(l[4:].strip()))
            i += 1
            continue

        # --- bloco de codigo
        if l.startswith('```'):
            j = i + 1
            buf = []
            while j < n and not linhas[j].startswith('```'):
                buf.append(linhas[j])
                j += 1
            out.append('<pre>%s</pre>'
                       % '\n'.join(x.replace('&', '&amp;').replace('<', '&lt;')
                                   for x in buf))
            i = j + 1
            continue

        # --- citacao: vira o painel de nota
        if l.startswith('> '):
            buf = []
            while i < n and linhas[i].startswith('>'):
                buf.append(linhas[i].lstrip('>').strip())
                i += 1
            txt = ' '.join(x for x in buf if x)
            gerado = txt.startswith('**Este arquivo é gerado.**')
            cls = 'nota gerado' if gerado else 'nota'
            out.append('<aside class="%s">%s</aside>' % (cls, _inline(txt)))
            continue

        # --- tabela
        if l.startswith('|'):
            j = i
            buf = []
            while j < n and linhas[j].startswith('|'):
                buf.append(linhas[j])
                j += 1
            out.append(_tabela(buf))
            i = j
            continue

        # --- listas (com continuacao indentada)
        m = re.match(r'^(\d+)\.\s+(.*)$', l)
        if l.startswith('- ') or m:
            ordenada = bool(m)
            itens, buf = [], None
            while i < n:
                li = linhas[i]
                mm = re.match(r'^(\d+)\.\s+(.*)$', li)
                if li.startswith('- '):
                    if buf is not None:
                        itens.append(buf)
                    buf = li[2:]
                elif mm:
                    if buf is not None:
                        itens.append(buf)
                    buf = mm.group(2)
                elif li.startswith('  ') and buf is not None:
                    buf += ' ' + li.strip()
                else:
                    break
                i += 1
            if buf is not None:
                itens.append(buf)
            tag = 'ol' if ordenada else 'ul'
            out.append('<%s>%s</%s>'
                       % (tag, ''.join('<li>%s</li>' % _inline(x) for x in itens), tag))
            continue

        # --- paragrafo
        if l.strip():
            buf = []
            while i < n and linhas[i].strip() and not re.match(
                    r'^(#{1,3} |\||> |- |\d+\. |```|---$)', linhas[i]):
                buf.append(linhas[i].strip())
                i += 1
            out.append('<p>%s</p>' % _inline(' '.join(buf)))
            continue

        i += 1

    if sec_aberta:
        out.append('</section>')
    return '\n'.join(out)


# ------------------------------------------------------------- a pagina
CSS = """
:root{
  --paper:#E9E7E1; --card:#FAF9F6; --card-2:#F2F0EA;
  --ink:#17191A; --ink-2:#55585A; --ink-3:#85888B;
  --line:#D3D0C8; --line-2:#E3E0D8;
  --accent:#1D4E3F; --accent-soft:#DFE9E4; --on-accent:#FAF9F6;
  --caution:#8F5400; --caution-soft:#F4E9D6;
  --stop:#8E2B20; --stop-soft:#F4E1DE;
  --shadow:0 1px 2px rgba(23,25,26,.05), 0 10px 28px -16px rgba(23,25,26,.22);
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --paper:#131412; --card:#1B1D1A; --card-2:#212420;
    --ink:#EDEBE4; --ink-2:#B0AEA5; --ink-3:#83817A;
    --line:#33362F; --line-2:#282B25;
    --accent:#78C3A4; --accent-soft:#1E2C26; --on-accent:#131412;
    --caution:#E0A649; --caution-soft:#2C2517;
    --stop:#E0836F; --stop-soft:#2E1D1A;
    --shadow:0 1px 2px rgba(0,0,0,.4), 0 10px 28px -16px rgba(0,0,0,.7);
  }
}
:root[data-theme="dark"]{
  --paper:#131412; --card:#1B1D1A; --card-2:#212420;
  --ink:#EDEBE4; --ink-2:#B0AEA5; --ink-3:#83817A;
  --line:#33362F; --line-2:#282B25;
  --accent:#78C3A4; --accent-soft:#1E2C26; --on-accent:#131412;
  --caution:#E0A649; --caution-soft:#2C2517;
  --stop:#E0836F; --stop-soft:#2E1D1A;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 10px 28px -16px rgba(0,0,0,.7);
}

*{box-sizing:border-box}
body{
  margin:0; background:var(--paper); color:var(--ink);
  font-family:"Libre Franklin","Helvetica Neue",Arial,sans-serif;
  font-size:16px; line-height:1.62; -webkit-font-smoothing:antialiased;
}
.wrap{max-width:960px; margin:0 auto; padding:0 22px 96px}

/* ---------- cabecalho ---------- */
header.topo{
  border-bottom:2px solid var(--ink); margin-bottom:8px;
  padding:56px 0 22px;
}
.eyebrow{
  font-family:"JetBrains Mono",ui-monospace,Consolas,monospace;
  font-size:11.5px; letter-spacing:.16em; text-transform:uppercase;
  color:var(--accent); font-weight:600; margin:0 0 14px;
}
h1{
  font-family:"Archivo Narrow","Arial Narrow",Arial,sans-serif;
  font-weight:700; font-size:clamp(34px,6vw,58px); line-height:1.02;
  letter-spacing:-.015em; margin:0 0 16px; text-wrap:balance;
}
.dek{font-size:17px; color:var(--ink-2); max-width:62ch; margin:0}
.chips{display:flex; flex-wrap:wrap; gap:8px; margin:22px 0 0}
.chip{
  font-family:"JetBrains Mono",monospace; font-size:12px; font-weight:500;
  padding:6px 11px; border:1px solid var(--line); border-radius:999px;
  background:var(--card); color:var(--ink-2);
}
.chip b{color:var(--ink); font-weight:600}

/* ---------- secoes com o numero na goteira ---------- */
section{
  display:grid; grid-template-columns:64px minmax(0,1fr); gap:0 22px;
  padding:38px 0 6px; border-bottom:1px solid var(--line-2);
}
section:last-of-type{border-bottom:0}
.gut{
  font-family:"JetBrains Mono",monospace; font-size:13px; font-weight:600;
  color:var(--accent); padding-top:9px; letter-spacing:.04em;
  border-top:2px solid var(--accent); align-self:start; margin-top:8px;
}
.gut:empty{border-top-color:var(--line)}
.corpo{min-width:0}
h2{
  font-family:"Archivo Narrow","Arial Narrow",Arial,sans-serif;
  font-weight:700; font-size:clamp(23px,3.2vw,31px); line-height:1.14;
  margin:0 0 18px; letter-spacing:-.01em; text-wrap:balance;
}
h3{
  font-family:"Archivo Narrow","Arial Narrow",Arial,sans-serif;
  font-weight:700; font-size:18px; margin:32px 0 12px;
  color:var(--accent); letter-spacing:.01em;
}
p{margin:0 0 16px; max-width:66ch}
a{color:var(--accent); text-underline-offset:2px}
strong{font-weight:600}
code{
  font-family:"JetBrains Mono",monospace; font-size:.87em;
  background:var(--card-2); border:1px solid var(--line-2);
  padding:1px 5px; border-radius:4px;
}

/* ---------- listas ---------- */
ul,ol{margin:0 0 16px; padding-left:22px; max-width:66ch}
li{margin:0 0 9px}
li::marker{color:var(--ink-3); font-family:"JetBrains Mono",monospace; font-size:.9em}

/* ---------- blocos de codigo: o fluxo da regra ---------- */
pre{
  font-family:"JetBrains Mono",monospace; font-size:13px; line-height:1.75;
  background:var(--card); border:1px solid var(--line);
  border-left:3px solid var(--accent);
  padding:16px 18px; border-radius:6px; overflow-x:auto; margin:0 0 20px;
  color:var(--ink);
}

/* ---------- tabelas ---------- */
.scroll{overflow-x:auto; margin:0 0 22px; border-radius:8px;
  border:1px solid var(--line); background:var(--card); box-shadow:var(--shadow)}
table{border-collapse:collapse; width:100%; font-size:14.5px}
th,td{padding:11px 14px; text-align:left; border-bottom:1px solid var(--line-2);
  vertical-align:top}
thead th{
  font-family:"JetBrains Mono",monospace; font-size:11px; font-weight:600;
  letter-spacing:.08em; text-transform:uppercase; color:var(--ink-3);
  background:var(--card-2); border-bottom:1px solid var(--line);
}
tbody tr:last-child td{border-bottom:0}
td.num,th.num{
  font-family:"JetBrains Mono",monospace; font-variant-numeric:tabular-nums;
  text-align:right; white-space:nowrap;
}
tbody tr:hover{background:var(--card-2)}
.box{
  font-family:"JetBrains Mono",monospace; font-size:19px; line-height:1;
  color:var(--accent);
}

/* ---------- painel de nota ---------- */
aside.nota{
  background:var(--accent-soft); border-left:3px solid var(--accent);
  padding:15px 18px; margin:0 0 22px; border-radius:0 7px 7px 0;
  font-size:15px; color:var(--ink-2); max-width:70ch;
}
aside.nota strong{color:var(--ink)}
aside.nota.gerado{
  background:transparent; border-left-color:var(--line);
  color:var(--ink-3); font-size:13.5px;
  font-family:"JetBrains Mono",monospace; line-height:1.6;
}

/* ---------- o cartao de pregao ---------- */
.cartao{
  margin:52px 0 0; background:var(--card); border:2px solid var(--ink);
  border-radius:10px; padding:26px 28px; box-shadow:var(--shadow);
}
.cartao h2{margin-top:0}
.cartao .lab{
  font-family:"JetBrains Mono",monospace; font-size:11px; font-weight:600;
  letter-spacing:.16em; text-transform:uppercase; color:var(--ink-3);
  margin:0 0 6px;
}
.grade{display:grid; gap:18px; grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
  margin:22px 0 0}
.celula{border-top:2px solid var(--line); padding-top:12px}
.celula .k{
  font-family:"JetBrains Mono",monospace; font-size:11px; font-weight:600;
  letter-spacing:.12em; text-transform:uppercase; color:var(--ink-3);
}
.celula .v{
  font-family:"Archivo Narrow",Arial,sans-serif; font-weight:700;
  font-size:30px; line-height:1.1; margin:4px 0 2px;
  font-variant-numeric:tabular-nums;
}
.celula .s{font-size:13px; color:var(--ink-2)}
.celula.go{border-top-color:var(--accent)} .celula.go .v{color:var(--accent)}
.celula.cau{border-top-color:var(--caution)} .celula.cau .v{color:var(--caution)}
.celula.par{border-top-color:var(--stop)} .celula.par .v{color:var(--stop)}

.regra-ouro{
  margin:30px 0 0; padding:20px 22px; border-radius:8px;
  background:var(--caution-soft); border:1px solid var(--caution);
  font-family:"Archivo Narrow",Arial,sans-serif; font-weight:700;
  font-size:clamp(19px,2.6vw,25px); line-height:1.25; color:var(--ink);
  text-wrap:balance;
}
.regra-ouro span{
  display:block; font-family:"Libre Franklin",sans-serif; font-weight:400;
  font-size:14.5px; line-height:1.6; color:var(--ink-2); margin-top:10px;
}

footer{
  margin-top:60px; padding-top:22px; border-top:1px solid var(--line);
  font-family:"JetBrains Mono",monospace; font-size:12.5px; color:var(--ink-3);
}
footer a{color:var(--ink-3)}

@media (max-width:640px){
  section{grid-template-columns:1fr; gap:0}
  .gut{margin-bottom:12px; padding-top:6px; display:inline-block; min-width:44px}
}
@media print{
  body{background:#fff} .scroll{box-shadow:none} section{break-inside:avoid}
  .cartao{break-before:page}
}
"""


CABECA = """<meta charset="utf-8">
<title>Plano Operacional Rincones1-DTA</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo+Narrow:wght@600;700&family=Libre+Franklin:wght@400;600&family=JetBrains+Mono:wght@400;500;600&display=swap">
<style>%s</style>
""" % CSS


def render(C, md):
    fu, v26 = C['fu'], C['v26']
    corpo = md_para_html(md)

    cartao = """
<div class="cartao">
  <p class="lab">Cartão de pregão</p>
  <h2>O que eu levo para a tela</h2>
  <p>Se eu só puder olhar uma coisa antes da abertura, é isto.</p>

  <div class="grade">
    <div class="celula go">
      <div class="k">Setup</div><div class="v">D</div>
      <div class="s">descolamento da Hull. O T entra pela mesma regra e é raro.</div>
    </div>
    <div class="celula cau">
      <div class="k">Veto</div><div class="v">Hull plana</div>
      <div class="s">sem inclinação na Hull {hma}, não existe trade.</div>
    </div>
    <div class="celula go">
      <div class="k">Entrada</div><div class="v">1 barra</div>
      <div class="s">limitada no meio do candle. Não preencheu, cancela.</div>
    </div>
    <div class="celula cau">
      <div class="k">Stop</div><div class="v">{stop_rot}</div>
      <div class="s">~{stop} pts com o ATR de hoje · {risco} por contrato. Nunca se afasta.</div>
    </div>
    <div class="celula go">
      <div class="k">Parcial</div><div class="v">+{stop}</div>
      <div class="s">{frac}% da posição, na mesma distância do stop.</div>
    </div>
    <div class="celula go">
      <div class="k">Alvo</div><div class="v">+{alvo}</div>
      <div class="s">pontos, no restante da posição.</div>
    </div>
    <div class="celula par">
      <div class="k">Fim do dia</div><div class="v">3 stops</div>
      <div class="s">ou 1 violação de regra. O que vier primeiro.</div>
    </div>
    <div class="celula par">
      <div class="k">Ritmo</div><div class="v">~{ritmo}</div>
      <div class="s">trades por pregão. O resto do dia é espera.</div>
    </div>
  </div>

  <div class="regra-ouro">
    Um trade vencedor tomado fora das regras conta como falha.
    <span>Ele vale zero na nota de aderência e entra em vermelho no diário.
    Sem esta regra a nota vira enfeite, e o resultado volta a mandar
    justamente nos dias em que o plano mais importa.</span>
  </div>
</div>
""".format(stop=C['stop'], stop_rot=C['stop_rot'], alvo=C['alvo'],
           frac=C['frac'], risco=C['risco_rs'], hma=C['hma_per'],
           ritmo=('%.1f' % fu['por_pregao']).replace('.', ','))

    chips = ''.join(
        '<span class="chip">%s <b>%s</b></span>' % (k, v) for k, v in (
            ('ativo', 'WIN'), ('gráfico', '10.000 ticks'),
            ('setups', 'D + T'),
            ('stop', C['stop_rot']),
            ('alvo', '+%d pts' % C['alvo']),
            ('trades/pregão', '~%s' % ('%.1f' % fu['por_pregao']).replace('.', ',')),
            ('pregões positivos', '%d%%' % round(fu['dias_pos'])),
        ))

    return """%s
<div class="wrap">
<header class="topo">
  <p class="eyebrow">Rincones1-DTA · procedimento operacional</p>
  <h1>Plano operacional<br>WIN · 10.000 ticks</h1>
  <p class="dek">O relatório diz o que foi medido. Este documento diz o que eu
  faço na frente da tela — e como eu avalio se fiz certo, num dia em que o
  resultado não tem como me dizer isso.</p>
  <div class="chips">%s</div>
</header>

%s

%s

<footer>
  Gerado por <code>plano.py</code> a partir de <code>saida/resumo.json</code> —
  os mesmos números de <code>relatorio.html</code>.
  Companheiro de <code>RESULTADOS.md</code> e <code>ESTRATEGIA.md</code>.
  Números descontando 5 pontos de custo por trade.
</footer>
</div>
""" % (CABECA, chips, corpo, cartao)
