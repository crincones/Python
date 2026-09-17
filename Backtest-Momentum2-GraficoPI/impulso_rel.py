# -*- coding: utf-8 -*-
"""Relatorio do impulso antes do recuo e dos pavios do trigger:
impulso.html + IMPULSO.md (rodar depois de impulso.py)."""
import json
import os

import engine as E
from relatorio import CSS
from textos import n, rs, cls

BASE = E.BASE
T = json.load(open(os.path.join(BASE, 'saida', 'impulso.json'), encoding='utf-8'))

NOME_G = {'claude': 'Gestao do CLAUDE.md (stop 100, parcial +100, alvo 300)', 'r400': 'Stop 100 / alvo 400 sem parcial'}
CURTO_G = {'claude': 'CLAUDE.md', 'r400': 'Stop 100 / alvo 400', 'claude_fecha': 'CLAUDE.md', 'r400_fecha': 'Stop 100 / alvo 400',
           'claude_extremo': 'CLAUDE.md, stop no extremo'}
NOME_C = {'todos': 'todos os sinais', 'picado': 'so sinais com filtro picado'}


# ------------------------------------------------------------------ acesso
def hip(gk, ck, ini):
    return next(h for h in T['imp_hipoteses'] if h['gestao'] == gk and h['conj'] == ck and h['nome'].startswith(ini))


def cimp(gk, ini):
    return next(l for l in T['imp_carteiras'][gk] if l['nome'].startswith(ini))


def cpav(gk, ini):
    return next(l for l in T['pav_carteiras'][gk] if l['nome'].startswith(ini))


def pad(k):
    return next(p for p in T['pav_padroes'] if p['k'] == k)


def faixa(tab, rot):
    return next(l for l in T['pav_faixas'][tab] if l['faixa'] == rot)


def consistente(h):
    """Mesmo sentido contra o resto no treino e no teste?"""
    a = (h['ev_is'] or 0) - (h['resto_is'] or 0)
    b = (h['ev_oos'] or 0) - (h['resto_oos'] or 0)
    if a > 0 and b > 0:
        return '<span class="tag pos">melhor nos dois</span>', 'melhor nos dois'
    if a < 0 and b < 0:
        return '<span class="tag neg">pior nos dois</span>', 'pior nos dois'
    return '<span class="tag">inverte</span>', 'inverte'


# ------------------------------------------------------------------ tabelas
CAB_CART = ('<div class="tab"><table><thead><tr><th>Filtro</th><th>Trades</th><th>Liquido</th><th>Fator</th><th>Rebaixamento</th>'
            '<th>Treino</th><th>Teste</th><th>Atravessar 5 pts</th>{extra}<th>Pregoes +</th></tr></thead><tbody>')


def linha_cart(l, dest=False, slip=False):
    s = l['stats']; o = l['oos']; i = l['is_']
    ex = (f"<td class=\"{cls(l['slip5'])}\">{rs(l['slip5'])}</td><td class=\"{cls(l['slip10'])}\">{rs(l['slip10'])}</td>" if slip else '')
    return (f"<tr class=\"{'dest' if dest else ''}\"><td>{l['nome']} <span class=\"nota\">({n(l['frac'] * 100, 0)}%)</span></td><td>{n(s['trades'])}</td>"
            f"<td class=\"{cls(s['liquido'])}\">{rs(s['liquido'])}</td><td>{n(s['fator_lucro'], 2)}</td><td>{rs(-s['dd_max'])}</td>"
            f"<td class=\"{cls(i.get('liquido'))}\">{rs(i.get('liquido'))}</td><td class=\"{cls(o.get('liquido'))}\">{rs(o.get('liquido'))}</td>"
            f"<td class=\"{cls(l['atravessa'])}\">{rs(l['atravessa'])}</td>{ex}<td>{n(s['dias_pos'], 0)}%</td></tr>")


def tab_cart(linhas, dest=0, slip=False):
    ex = '<th>Slippage 5 pts</th><th>Slippage 10 pts</th>' if slip else ''
    return CAB_CART.format(extra=ex) + ''.join(linha_cart(l, i == dest, slip) for i, l in enumerate(linhas)) + '</tbody></table></div>'


def tab_hip(gk, ck):
    h = ('<div class="tab"><table><thead><tr><th>Condicao</th><th>Sinais</th><th>R$/trade</th><th>Resto</th><th>Treino (resto)</th>'
         '<th>Teste (resto)</th><th>t</th><th>Percentil sorteio</th><th>Treino x teste</th></tr></thead><tbody>')
    for x in [x for x in T['imp_hipoteses'] if x['gestao'] == gk and x['conj'] == ck]:
        h += (f"<tr><td>{x['nome']}</td><td>{n(x['n'])} <span class=\"nota\">({n(x['frac'] * 100, 0)}%)</span></td>"
              f"<td class=\"{cls(x['ev'])}\">{rs(x['ev'], 1)}</td><td class=\"{cls(x['resto'])}\">{rs(x['resto'], 1)}</td>"
              f"<td><span class=\"{cls(x['ev_is'])}\">{rs(x['ev_is'], 1)}</span> <span class=\"nota\">({rs(x['resto_is'], 1)})</span></td>"
              f"<td><span class=\"{cls(x['ev_oos'])}\">{rs(x['ev_oos'], 1)}</span> <span class=\"nota\">({rs(x['resto_oos'], 1)})</span></td>"
              f"<td>{n(x['t'], 2)}</td><td>{n(x['pct'], 0)}</td><td>{consistente(x)[0]}</td></tr>")
    return h + '</tbody></table></div>'


def tab_familias(gk):
    h = ''
    for F in T['imp_familias']:
        h += f"<h3>{F['familia']}</h3><p class=\"nota\">{F['desc']}</p>"
        for B in F['blocos']:
            g = B['geral'][gk]
            h += (f"<div class=\"card\"><b>{B['rotulo']}</b> <span class=\"nota\">&middot; geral {rs(g['ev'], 1)} (treino {rs(g['ev_is'], 1)} / teste {rs(g['ev_oos'], 1)})</span>"
                  '<div class="tab"><table><thead><tr><th>Faixa (quintis do treino)</th><th>Sinais</th><th>R$/trade</th><th>Acerto</th><th>Treino</th><th>Teste</th>'
                  '<th>Compra</th><th>Venda</th><th>Treino x teste</th></tr></thead><tbody>')
            for l in B['tabs'][gk]:
                if l['n_is'] >= 25 and l['n_oos'] >= 15:
                    a = l['ev_is'] - g['ev_is']; b = l['ev_oos'] - g['ev_oos']
                    tag = ('<span class="tag pos">melhor nos dois</span>' if a > 0 and b > 0 else
                           '<span class="tag neg">pior nos dois</span>' if a < 0 and b < 0 else '<span class="tag">inverte</span>')
                else:
                    tag = '<span class="nota">poucos</span>'
                h += (f"<tr><td>{l['faixa']}</td><td>{n(l['n'])}</td><td class=\"{cls(l['ev'])}\">{rs(l['ev'], 1)}</td><td>{n(l['wr'], 1)}%</td>"
                      f"<td class=\"{cls(l['ev_is'])}\">{rs(l['ev_is'], 1)} <span class=\"nota\">({n(l['n_is'])})</span></td>"
                      f"<td class=\"{cls(l['ev_oos'])}\">{rs(l['ev_oos'], 1)} <span class=\"nota\">({n(l['n_oos'])})</span></td>"
                      f"<td class=\"{cls(l['compra'])}\">{rs(l['compra'], 1)}</td><td class=\"{cls(l['venda'])}\">{rs(l['venda'], 1)}</td><td>{tag}</td></tr>")
            h += '</tbody></table></div></div>'
    return h


def tab_busca(gk):
    b = T['imp_busca'][gk]
    h = (f'<div class="kpis"><div class="kpi"><div class="r">Cortes testados</div><div class="v">{n(b["n_cand"])}</div></div>'
         f'<div class="kpi"><div class="r">Melhor t no treino</div><div class="v">{n(b["max_t"], 2)}</div></div>'
         f'<div class="kpi"><div class="r">Placebo p95 / p99</div><div class="v">{n(b["p95"], 2)} / {n(b["p99"], 2)}</div></div>'
         f'<div class="kpi"><div class="r">Bons no treino que melhoram o teste</div><div class="v">{n(b["frac_bons"] * 100, 0)}%</div></div></div>'
         f'<p class="nota">Sem filtro: {rs(b["base_is"], 1)} por trade no treino, {rs(b["base_oos"], 1)} no teste.</p>'
         '<div class="tab"><table><thead><tr><th>Corte (os 20 melhores do treino)</th><th>% sinais</th><th>R$/trade treino</th><th>t treino</th>'
         '<th>R$/trade teste</th><th>Ganho no teste</th></tr></thead><tbody>')
    for c in b['lista']:
        h += (f"<tr><td>{c['nome']}</td><td>{n(c['frac'] * 100, 0)}%</td><td class=\"{cls(c['ev_is'])}\">{rs(c['ev_is'], 1)}</td><td>{n(c['t_is'], 2)}</td>"
              f"<td class=\"{cls(c['ev_oos'])}\">{rs(c['ev_oos'], 1)}</td><td class=\"{cls(c['ganho_oos'])}\">{rs(c['ganho_oos'], 1)}</td></tr>")
    return h + '</tbody></table></div>'


def tab_grade(gk):
    h = ('<div class="tab"><table><thead><tr><th>Banda</th><th>Janela</th><th>Distancia tipica da EMA</th><th>Sinais alem da banda</th><th>R$/trade</th><th>Resto</th>'
         '<th>Treino (resto)</th><th>Teste (resto)</th><th>t</th><th>Percentil sorteio</th><th>Treino x teste</th></tr></thead><tbody>')
    for x in [x for x in T['kc_grade'] if x['gestao'] == gk]:
        dest = x['tipo'] == 'range' and x['m'] == 2.5
        nome = f"{'Keltner' if x['tipo'] == 'range' else 'Desvio-padrao'} {n(x['m'], 1)}"
        h += (f"<tr class=\"{'dest' if dest else ''}\"><td>{nome}</td><td>{x['W']} candles</td><td>~{n(x['pts_banda'])} pts</td>"
              f"<td>{n(x['n'])} <span class=\"nota\">({n(x['frac'] * 100, 0)}%)</span></td>"
              f"<td class=\"{cls(x['ev'])}\">{rs(x['ev'], 1)}</td><td class=\"{cls(x['resto'])}\">{rs(x['resto'], 1)}</td>"
              f"<td><span class=\"{cls(x['ev_is'])}\">{rs(x['ev_is'], 1)}</span> <span class=\"nota\">({rs(x['resto_is'], 1)})</span></td>"
              f"<td><span class=\"{cls(x['ev_oos'])}\">{rs(x['ev_oos'], 1)}</span> <span class=\"nota\">({rs(x['resto_oos'], 1)})</span></td>"
              f"<td>{n(x['t'], 2)}</td><td>{n(x['pct'], 0)}</td><td>{consistente(x)[0]}</td></tr>")
    return (h + '</tbody></table></div><p class="nota">Destacada: a Keltner do grafico (2,5). A banda da Nelogica e por range; '
            'o desvio-padrao entra so como comparacao.</p>')


def tab_padroes():
    h = ('<div class="tab"><table><thead><tr><th>Padrao</th><th>No estudo anterior</th><th>Gestao</th><th>Sinais</th><th>R$/trade</th><th>Resto</th>'
         '<th>Treino (resto)</th><th>Teste (resto)</th><th>t</th><th>Percentil sorteio</th><th>Treino x teste</th></tr></thead><tbody>')
    for p in T['pav_padroes']:
        for j, gk in enumerate(('claude_fecha', 'r400_fecha', 'claude_extremo')):
            x = p[gk]
            ini = (f"<td rowspan=\"3\"><b>{p['nome']}</b><br><span class=\"nota\">universo: {p['univ']}</span></td><td rowspan=\"3\" class=\"nota\">{p['antes']}</td>"
                   if j == 0 else '')
            h += (f"<tr>{ini}<td>{CURTO_G[gk]}</td><td>{n(x['n'])}</td><td class=\"{cls(x['ev'])}\">{rs(x['ev'], 1)}</td><td class=\"{cls(x['resto'])}\">{rs(x['resto'], 1)}</td>"
                  f"<td><span class=\"{cls(x['ev_is'])}\">{rs(x['ev_is'], 1)}</span> <span class=\"nota\">({rs(x['resto_is'], 1)})</span></td>"
                  f"<td><span class=\"{cls(x['ev_oos'])}\">{rs(x['ev_oos'], 1)}</span> <span class=\"nota\">({rs(x['resto_oos'], 1)})</span></td>"
                  f"<td>{n(x['t'], 2)}</td><td>{n(x['pct'], 0)}</td><td>{consistente(x)[0]}</td></tr>")
    return h + '</tbody></table></div>'


def tab_faixas(tab, key):
    L = T['pav_faixas'][tab]
    h = ('<div class="tab"><table><thead><tr><th>Pavio (pts = % do corpo)</th><th>Sinais</th><th>R$/trade</th><th>Acerto</th><th>Treino</th><th>Teste</th>'
         '<th>Compra</th><th>Venda</th><th>T1</th><th>T2</th></tr></thead><tbody>')
    for l in L:
        x = l[key]
        h += (f"<tr><td>{l['faixa']}</td><td>{n(l['n'])}</td><td class=\"{cls(x['ev'])}\">{rs(x['ev'], 1)}</td><td>{n(x['wr'], 1)}%</td>"
              f"<td class=\"{cls(x['ev_is'])}\">{rs(x['ev_is'], 1)} <span class=\"nota\">({n(l['n_is'])})</span></td>"
              f"<td class=\"{cls(x['ev_oos'])}\">{rs(x['ev_oos'], 1)} <span class=\"nota\">({n(l['n_oos'])})</span></td>"
              f"<td class=\"{cls(x['compra'])}\">{rs(x['compra'], 1)}</td><td class=\"{cls(x['venda'])}\">{rs(x['venda'], 1)}</td>"
              f"<td class=\"{cls(x['t1'])}\">{rs(x['t1'], 1)}</td><td class=\"{cls(x['t2'])}\">{rs(x['t2'], 1)}</td></tr>")
    return h + '</tbody></table></div>'


def tab_mensal(gk):
    M = T['pav_mensal'][gk]
    h = '<div class="tab"><table><thead><tr><th>Mes</th><th>Pavio 0</th><th>Pavio 5-10</th><th>Pavio acima de 10</th><th>0 melhor que 5-10?</th></tr></thead><tbody>'
    for m, v in M.items():
        a = v.get('0', {}); b = v.get('5-10', {}); c = v.get('>10', {})
        h += (f"<tr><td>{m}</td><td class=\"{cls(a.get('ev'))}\">{rs(a.get('ev'), 1)} <span class=\"nota\">({n(a.get('n'))})</span></td>"
              f"<td class=\"{cls(b.get('ev'))}\">{rs(b.get('ev'), 1)} <span class=\"nota\">({n(b.get('n'))})</span></td>"
              f"<td class=\"{cls(c.get('ev'))}\">{rs(c.get('ev'), 1)} <span class=\"nota\">({n(c.get('n'))})</span></td>"
              f"<td>{'sim' if (a.get('ev') or 0) > (b.get('ev') or 0) else 'nao'}</td></tr>")
    return h + '</tbody></table></div>'


def tab_lado_tipo(gk):
    D = T['pav_lado_tipo'][gk]
    grupos = ['Compra', 'Venda', 'T1', 'T2', '2 contra', '3 contra']
    h = '<div class="tab"><table><thead><tr><th>Grupo</th><th>Pavio 0</th><th>Pavio 5-10</th><th>Pavio acima de 10</th></tr></thead><tbody>'
    for g in grupos:
        h += f'<tr><td>{g}</td>'
        for fb in ('0', '5-10', '>10'):
            x = D.get(f'{g}|{fb}', {})
            h += f"<td class=\"{cls(x.get('ev'))}\">{rs(x.get('ev'), 1)} <span class=\"nota\">({n(x.get('n'))})</span></td>"
        h += '</tr>'
    return h + '</tbody></table></div>'


def blocos(prefixo, itens, render):
    """Um div por aba; o JS mostra so o ativo."""
    return ''.join(f'<div class="bl" data-grupo="{prefixo}" data-k="{k}"{"" if i == 0 else " hidden"}>{render(k)}</div>'
                   for i, (k, _) in enumerate(itens))


def abas(prefixo, itens):
    return (f'<div class="abas" data-alvo="{prefixo}">' +
            ''.join(f'<button data-k="{k}" class="{"on" if i == 0 else ""}">{r}</button>' for i, (k, r) in enumerate(itens)) + '</div>')


G2 = [('r400', 'Stop 100 / alvo 400'), ('claude', 'Gestao CLAUDE.md')]


# ------------------------------------------------------------------ corpo
def corpo():
    M = T['meta']; PM = T['pav_meta']
    amp = {gk: hip(gk, 'todos', 'Impulso amplo em 20:') for gk in ('r400', 'claude')}
    kc = {gk: hip(gk, 'todos', 'Preco tocou a banda de Keltner nos 10') for gk in ('r400', 'claude')}
    bb = {gk: hip(gk, 'todos', 'MACD tocou a Bollinger 1000 nos 20') for gk in ('r400', 'claude')}
    tri = {gk: hip(gk, 'todos', 'Impulso amplo em 20 E') for gk in ('r400', 'claude')}
    rec = {gk: hip(gk, 'todos', 'Recuo profundo') for gk in ('r400', 'claude')}
    c_sem = {gk: cimp(gk, 'sem filtro') for gk in ('r400', 'claude')}
    c_nao_amp = {gk: cimp(gk, 'impulso nao amplo') for gk in ('r400', 'claude')}
    c_amp = {gk: cimp(gk, 'impulso amplo') for gk in ('r400', 'claude')}
    c_bb = {gk: cimp(gk, 'MACD tocou') for gk in ('r400', 'claude')}
    c_kc = {gk: cimp(gk, 'tocou Keltner') for gk in ('r400', 'claude')}
    c_nkc = {gk: cimp(gk, 'nao tocou Keltner') for gk in ('r400', 'claude')}
    qa = T['q_imp']['alto']['20']
    bs = T['imp_busca']

    pf = pad('fech'); p0 = pad('fech0s'); pm = pad('mag'); pv = pad('verde'); pp = pad('peq'); pmt = pad('mart')
    sp = T['pav_spearman']
    k_setup = {gk: cpav(gk, 'setup atual') for gk in ('r400', 'claude')}
    k_0 = {gk: cpav(gk, 'pavio do fechamento = 0') for gk in ('r400', 'claude')}
    k_510 = {gk: cpav(gk, 'pavio do fechamento 5-10') for gk in ('r400', 'claude')}
    k_10 = {gk: cpav(gk, 'pavio do fechamento acima') for gk in ('r400', 'claude')}
    k_uni = {gk: cpav(gk, 'sem corte') for gk in ('r400', 'claude')}
    k_0p = {gk: cpav(gk, 'pavio do fechamento = 0 E picado') for gk in ('r400', 'claude')}
    meses = T['pav_mensal']['claude']
    m_ok = sum(1 for v in meses.values() if (v['0']['ev'] or 0) > (v['5-10']['ev'] or 0))
    meses4 = T['pav_mensal']['r400']
    m_ok4 = sum(1 for v in meses4.values() if (v['0']['ev'] or 0) > (v['5-10']['ev'] or 0))
    f0 = faixa('fech', '0'); f510 = faixa('fech', '5-10'); f1525 = faixa('fech', '15-25')

    H = f"""
<h1>Impulso antes do recuo e pavios do trigger</h1>
<p class="sub">Setup EMA 21 + HullRetracao_Azul + MACD &middot; WINFUT PI 20, {M['pregoes']} pregoes ({M['inicio']} a {M['fim']}) &middot;
entrada seca no fechamento &middot; 6 contratos, R$ 0,50 por contrato &middot; treino ate {M['corte']}, teste depois &middot; complemento de <code>relatorio.html</code> e <code>tendencia.html</code></p>

<section id="resumo"><h2>Resposta curta</h2>
<div class="kpis">
<div class="kpi"><div class="r">Impulso amplo (terco superior) &middot; stop 100 / alvo 400</div><div class="v {cls(c_amp['r400']['stats']['liquido'])}">{rs(c_amp['r400']['stats']['liquido'])}</div></div>
<div class="kpi"><div class="r">Impulso nao amplo</div><div class="v {cls(c_nao_amp['r400']['stats']['liquido'])}">{rs(c_nao_amp['r400']['stats']['liquido'])}</div></div>
<div class="kpi"><div class="r">R$/trade: pavio do fechamento 0 / 5-10 / acima de 10</div><div class="v">{rs(f0['r400_fecha']['ev'], 1)} / {rs(f510['r400_fecha']['ev'], 1)} / {rs(pf['r400_fecha']['resto'], 1)}</div></div>
<div class="kpi"><div class="r">Pavio 0 com slippage de 5 pts &middot; setup atual</div><div class="v">{rs(k_0['r400']['slip5'])} &middot; {rs(k_setup['r400']['slip5'])}</div></div>
</div>

<div class="card ruim"><b>1. Impulso amplo e preco alem das bandas nao melhoram o acerto: os movimentos mais esticados foram piores.</b>
<br><b>Keltner da Nelogica (EMA 21 &plusmn; 2,5 x range medio 21)</b>: nos {n(M['kc10_toca'] * 100, 0)}% dos sinais em que o preco passou da banda nos 10 candles antes do recuo,
{rs(kc['r400']['ev'], 1)} por trade contra {rs(kc['r400']['resto'], 1)} dos demais (treino {rs(kc['r400']['ev_is'], 1)} x {rs(kc['r400']['resto_is'], 1)},
teste {rs(kc['r400']['ev_oos'], 1)} x {rs(kc['r400']['resto_oos'], 1)}; CLAUDE.md {rs(kc['claude']['ev'], 1)} x {rs(kc['claude']['resto'], 1)}).
Em carteira, os que passaram da banda deram <b>{rs(c_kc['r400']['stats']['liquido'])}</b> e os demais <b>{rs(c_nkc['r400']['stats']['liquido'])}</b>, rebaixamento {rs(-c_nkc['r400']['stats']['dd_max'])}
(sem filtro {rs(c_sem['r400']['stats']['liquido'])}, {rs(-c_sem['r400']['stats']['dd_max'])}). Na gestao do CLAUDE.md: {rs(c_kc['claude']['stats']['liquido'])} x {rs(c_nkc['claude']['stats']['liquido'])}.
O efeito cresce com a largura da banda (ver <a href="#bandas">Largura da banda</a>): com 1,5 e 2,0 nao separa; com 3,0 e 3,5 os poucos sinais que passaram sao ainda piores.
<br><b>Impulso em pts</b>: 
terco superior do impulso de 20 candles (perna a favor de {n(qa)} pts ou mais antes do recuo): {rs(amp['r400']['ev'], 1)} por trade contra {rs(amp['r400']['resto'], 1)} dos demais
(stop 100 / alvo 400). Ficou abaixo no treino ({rs(amp['r400']['ev_is'], 1)} x {rs(amp['r400']['resto_is'], 1)}) e no teste ({rs(amp['r400']['ev_oos'], 1)} x {rs(amp['r400']['resto_oos'], 1)}).
Na gestao do CLAUDE.md: {rs(amp['claude']['ev'], 1)} x {rs(amp['claude']['resto'], 1)}.
Em carteira, sem esses sinais: {rs(c_sem['r400']['stats']['liquido'])} &rarr; <b>{rs(c_nao_amp['r400']['stats']['liquido'])}</b>, rebaixamento {rs(-c_sem['r400']['stats']['dd_max'])} &rarr; {rs(-c_nao_amp['r400']['stats']['dd_max'])}
(CLAUDE.md: {rs(c_sem['claude']['stats']['liquido'])} &rarr; {rs(c_nao_amp['claude']['stats']['liquido'])}).
<ul>
<li><b>MACD tocando a Bollinger 1000 no impulso</b>: {rs(bb['r400']['ev'], 1)} x {rs(bb['r400']['resto'], 1)}. Pior no treino ({rs(bb['r400']['ev_is'], 1)} x {rs(bb['r400']['resto_is'], 1)}), um pouco melhor no teste ({rs(bb['r400']['ev_oos'], 1)} x {rs(bb['r400']['resto_oos'], 1)}).</li>
<li><b>Impulso amplo + Keltner + MACD na Bollinger juntos</b>: {rs(tri['r400']['ev'], 1)} x {rs(tri['r400']['resto'], 1)} (percentil {n(tri['r400']['pct'], 0)} do sorteio).</li>
</ul>
Nenhum efeito isolado e estatisticamente forte (t entre &minus;0,5 e &minus;1,5). O que da mais confianca na Keltner e a consistencia: pior no treino e no teste, nas duas gestoes, e piorando conforme a banda alarga.
A busca automatica aponta para o mesmo lado: os melhores cortes do treino foram "MACD ainda longe da banda" e "impulso menor que X".</div>

<div class="card ok"><b>2. O corte de pavio do HullRetracao_Azul continua valendo com o toque na EMA 21.</b>
Sem o corte ({n(PM['universo'])} sinais), os {n(pf['r400_fecha']['n'])} com pavio do fechamento ate 10 pts deram {rs(pf['r400_fecha']['ev'], 1)} por trade; os demais {rs(pf['r400_fecha']['resto'], 1)}
(CLAUDE.md {rs(pf['claude_fecha']['ev'], 1)} x {rs(pf['claude_fecha']['resto'], 1)}). Em carteira, os sinais com pavio acima de 10 perdem nas duas gestoes
({rs(k_10['r400']['stats']['liquido'])} / {rs(k_10['claude']['stats']['liquido'])}). Como no estudo anterior, a diferenca e grande no treino e menor no teste.</div>

<div class="card ok"><b>3. Novo: a vantagem esta no pavio ZERO.</b> No PI o pavio anda de 5 em 5 pts, e o corte "ate 10%" junta duas coisas diferentes:
<ul>
<li><b>Fecha no extremo</b> (compra na maxima, venda na minima): {n(f0['n'])} sinais, {rs(f0['r400_fecha']['ev'], 1)} por trade (treino {rs(f0['r400_fecha']['ev_is'], 1)}, teste {rs(f0['r400_fecha']['ev_oos'], 1)}).
Na gestao do CLAUDE.md, {rs(f0['claude_fecha']['ev'], 1)}.</li>
<li><b>1 ou 2 ticks de pavio</b>: {n(f510['n'])} sinais, {rs(f510['r400_fecha']['ev'], 1)} (treino {rs(f510['r400_fecha']['ev_is'], 1)}, teste {rs(f510['r400_fecha']['ev_oos'], 1)}); CLAUDE.md {rs(f510['claude_fecha']['ev'], 1)}.</li>
</ul>
O pavio zero foi melhor que 5-10 no treino e no teste, nas vendas, em T1 e T2, com 2 e com 3 candles contra, e em {m_ok4} de 7 meses (nas compras, so com alvo 400)
(percentil {n(p0['r400_fecha']['pct'], 0)} do sorteio dentro do setup; t = {n(p0['r400_fecha']['t'], 2)}).
Em carteira, com stop 100 / alvo 400: <b>{rs(k_0['r400']['stats']['liquido'])}</b> em {n(k_0['r400']['stats']['trades'])} trades, fator {n(k_0['r400']['stats']['fator_lucro'], 2)},
rebaixamento {rs(-k_0['r400']['stats']['dd_max'])}, positivo no treino e no teste. O setup atual fez {rs(k_setup['r400']['stats']['liquido'])} com rebaixamento {rs(-k_setup['r400']['stats']['dd_max'])}.
<b>Com custo de execucao a diferenca cresce:</b> com 5 pts de slippage por trade o pavio zero fica em {rs(k_0['r400']['slip5'])} e o setup atual em {rs(k_setup['r400']['slip5'])}; com 10 pts, {rs(k_0['r400']['slip10'])} x {rs(k_setup['r400']['slip10'])}.
<br><span class="nota">A separacao 0 x 5-10 nao foi prevista antes: a faixa ja existia no estudo anterior, mas os dois estavam juntos. E um candidato forte, nao uma regra comprovada.
No OHLC, a barra seguinte abre no fechamento do trigger, entao o backtest nao da vantagem artificial de preco a quem fecha no extremo. Mas e justamente ai que a ordem a mercado mais escorrega na vida real; veja as colunas de slippage.</span></div>

<div class="card alerta"><b>4. Pavio da abertura: so metade do padrao anterior se repete.</b>
<ul>
<li><b>Faixa magenta (25-90%)</b> continua abaixo do resto ({rs(pm['r400_fecha']['ev'], 1)} x {rs(pm['r400_fecha']['resto'], 1)}, percentil {n(pm['r400_fecha']['pct'], 0)}),
mas so no treino; no teste empata ou inverte ({rs(pm['claude_fecha']['ev_oos'], 1)} x {rs(pm['claude_fecha']['resto_oos'], 1)} no CLAUDE.md).</li>
<li><b>Faixa verde (5-25%)</b> continua sem separar (percentil {n(pv['claude_fecha']['pct'], 0)} a {n(pv['r400_fecha']['pct'], 0)}), como na Hull a favor do estudo anterior.</li>
<li><b>"Quanto menor, melhor" nao vale aqui.</b> Correlacao de posto entre o pavio da abertura (ate 90%) e o resultado:
{n(sp['r400_fecha']['rho'], 3)} (p = {n(sp['r400_fecha']['p'], 2)}) e {n(sp['claude_fecha']['rho'], 3)} (p = {n(sp['claude_fecha']['p'], 2)}).
Com o stop no extremo ha correlacao ({n(sp['r400_extremo']['rho'], 2)}), mas e mecanica: pavio maior = stop maior.</li>
<li><b>Martelo (pavio da abertura acima de 90 pts)</b>, que ja tinha medido bem antes: {n(pmt['claude_fecha']['n'])} sinais, {rs(pmt['claude_fecha']['ev'], 1)} x {rs(pmt['claude_fecha']['resto'], 1)} no CLAUDE.md,
treino e teste acima (percentil {n(pmt['claude_fecha']['pct'], 0)}). Com alvo 400 so aparece no teste. Sao poucos sinais: observar, nao filtrar.</li>
</ul></div>
</section>

<section id="defs"><h2>Como cada medida foi feita</h2>
<div class="card"><ul>
<li>Tudo <b>orientado pelo lado do trade</b> e medido nos N candles (10, 20, 30) que terminam no candle <b>antes do recuo</b>, sem sair do pregao.</li>
<li><b>Impulso N</b>: do extremo contra ao pico a favor dentro da janela (compra: maxima do pico &minus; menor minima antes dele), em pts. Mediana em 20 candles: {n(M['imp20_med'])} pts.</li>
<li><b>Keltner</b> no padrao do KeltnerCH da Nelogica: EMA 21 &plusmn; 2,5 x media exponencial 21 do range (maxima &minus; minima). No PI, dentro do pregao, o range medio e igual ao ATR
(razao mediana 1,00; so difere logo apos o gap de abertura). Medida: (maxima &minus; EMA 21) / (banda superior &minus; EMA 21), o maior valor da janela; na venda, espelho. 1 = encostou, acima de 1 = passou.
{n(M['kc10_toca'] * 100, 0)}% dos sinais passaram da banda nos 10 candles antes do recuo.</li>
<li><b>MACD x Bollinger</b>: (MACD &minus; media 1000) / (1,0 desvio), o maior valor da janela, a favor do trade. 1 = MACD na banda. {n(M['bb20_toca'] * 100, 0)}% tocaram nos 20 candles.</li>
<li><b>Recuo</b>: do pico ate o extremo dos candles da virada, em pts; recuo / impulso; candles entre o pico e o inicio do recuo.</li>
<li><b>Pavios</b>: no PI 20 o corpo tem sempre 100 pts, entao pts = % do corpo. Lado do <b>fechamento</b> = o que o HullRetracao_Azul limita (compra: maxima &minus; fechamento).
Lado da <b>abertura</b> = o que o PavioContra_Magenta e o PavioFavor_Verde medem (compra: abertura &minus; minima). Para o pavio do fechamento o universo e o setup <b>sem</b> o corte de 10%
({n(PM['universo'])} sinais, contra {n(PM['setup'])} com o corte).</li>
<li><b>Percentil do sorteio</b>: onde o R$/trade do grupo cai entre subconjuntos sorteados do mesmo tamanho, no mesmo universo. 50 = igual ao acaso; acima de 95 ou abaixo de 5 = dificil ser sorte.</li>
<li><b>Resto</b> = os sinais do mesmo universo fora do grupo. <b>Treino x teste</b> compara o grupo com o resto em cada periodo.</li>
<li>Carteiras: uma posicao por vez. "Atravessar 5 pts" = parcial e alvo so executam 1 tick alem. Slippage = pts descontados por trade, 6 contratos.</li>
</ul></div>
</section>

<section id="hip"><h2>Impulso: hipoteses definidas antes</h2>
{abas('hg', G2)}{abas('hc', [('todos', 'Todos os sinais'), ('picado', 'So picado')])}
<div id="hip_box">""" + ''.join(
        f'<div class="bl2" data-g="{gk}" data-c="{ck}"{"" if (gk, ck) == ("r400", "todos") else " hidden"}>{tab_hip(gk, ck)}</div>'
        for gk in ('r400', 'claude') for ck in ('todos', 'picado')) + f"""</div>
<p class="nota">O "recuo profundo" entrou depois de olhar os quintis e esta marcado como achado da exploracao.</p>
</section>

<section id="bandas"><h2>Largura da banda</h2>
<p>Mesmo teste com varias larguras: EMA 21 &plusmn; m x range medio 21 (Keltner Nelogica) e, como comparacao, EMA 21 &plusmn; m x desvio-padrao 21 do fechamento.
Grupo = sinais em que o preco passou da banda na janela antes do recuo; resto = os demais.</p>
{abas('kg', G2)}
{blocos('kg', G2, tab_grade)}
</section>

<section id="cimp"><h2>Impulso em carteira</h2>
{abas('ci', G2)}
{blocos('ci', G2, lambda gk: tab_cart(T['imp_carteiras'][gk]) + f'<div class="card"><div class="graf" id="g_ci_{gk}"></div></div>')}
<p class="nota">Correlacao de posto com a eficiencia de 100 candles (o filtro de consolidacao do estudo anterior): impulso 20 {n(T['imp_corr']['imp_20'], 2)},
Keltner {n(T['imp_corr']['kc_10'], 2)}, MACD na Bollinger {n(T['imp_corr']['bb_20'], 2)}. Sao medidas quase independentes da consolidacao.</p>
</section>

<section id="busca"><h2>Impulso: busca automatica e controle de acaso</h2>
<p>Cortes "manter acima / abaixo" nos quintis do treino, para todas as medidas de impulso, bandas e recuo. Placebo: filtros aleatorios que mantem 30-80% dos sinais.</p>
{abas('bu', G2)}
{blocos('bu', G2, tab_busca)}
<p class="nota">O melhor t fica abaixo do p99 do placebo nas duas gestoes. {n(bs['r400']['frac_bons'] * 100, 0)}% / {n(bs['claude']['frac_bons'] * 100, 0)}% dos cortes bons no treino melhoram o teste
(no estudo de tendencia foram ~54%). O vies para "menos esticado" e fraco, mas nao e zero.</p>
</section>

<section id="fam"><h2>Impulso: faixas por medida</h2>
{abas('fa', G2)}
{blocos('fa', G2, tab_familias)}
</section>

<section id="padroes"><h2>Pavios: o padrao anterior vale aqui?</h2>
<p>Cada linha compara o grupo com o resto do mesmo universo. "No estudo anterior" resume o que <code>PAVIO_CONTRA.md</code> / <code>HULL_CONTRA.md</code> mediram sem a EMA 21 (em pts por sinal, brutos).</p>
{tab_padroes()}
</section>

<section id="faixas"><h2>Pavios: faixas</h2>
{abas('pf', [('r400_fecha', 'Stop 100 / alvo 400'), ('claude_fecha', 'Gestao CLAUDE.md'), ('claude_extremo', 'CLAUDE.md, stop no extremo'), ('r400_extremo', 'Alvo 400, stop no extremo')])}
""" + ''.join(
        f'<div class="bl" data-grupo="pf" data-k="{k}"{"" if k == "r400_fecha" else " hidden"}>'
        f'<h3>Pavio do lado do fechamento (setup sem o corte de 10%)</h3>{tab_faixas("fech", k)}'
        f'<h3>Pavio do lado da abertura (setup atual, fechamento ate 10%)</h3>{tab_faixas("abre_setup", k)}'
        f'<h3>Pavio do lado da abertura (sem corte no fechamento)</h3>{tab_faixas("abre_todos", k)}</div>'
        for k in ('r400_fecha', 'claude_fecha', 'claude_extremo', 'r400_extremo')) + f"""
<p class="nota">Acima de 25 pts no fechamento sobram poucos sinais ({n(sum(faixa('fech', r)['n'] for r in ('30-45', '50-65', '70-90', '95+')))}); as linhas extremas sao ruido.
Com o stop no extremo oposto, o pavio da abertura entra no tamanho do stop.</p>
</section>

<section id="zero"><h2>Pavio zero: estabilidade</h2>
{abas('ze', G2)}
{blocos('ze', G2, lambda gk: '<div class="grade2"><div><h3>Por grupo (R$/trade)</h3>' + tab_lado_tipo(gk) + '</div><div><h3>Mes a mes (R$/trade)</h3>' + tab_mensal(gk) + '</div></div>')}
</section>

<section id="cpav"><h2>Pavios em carteira</h2>
{abas('cp', G2)}
{blocos('cp', G2, lambda gk: tab_cart(T['pav_carteiras'][gk], dest=1, slip=True) + f'<div class="card"><div class="graf" id="g_cp_{gk}"></div></div>')}
<p class="nota">"Picado" = 11+ inversoes nos 20 candles antes do recuo; "fora da consolidacao 100" = eficiencia &ge; 0,08 (ver <code>tendencia.html</code>).
As combinacoes com o pavio zero ficam com poucos trades (~2 a 3 por pregao): servem para ver se os efeitos se somam, nao como regra pronta.</p>
</section>

<section id="aplicar"><h2>Como aplicar</h2>
<div class="card ok"><ul>
<li><b>Nao</b> usar "movimento amplo" nem "preco perto da banda" como condicao de entrada. O lado que mediu melhor e o contrario: <b>pular o sinal quando o preco passou da Keltner 2,5
nos 10 candles antes do recuo</b> (candidato: consistente nos dois periodos, mas t ~ &minus;1). Junto com o filtro de consolidacao 100:
{rs(cimp('r400', 'fora da consolidacao 100 E nao')['stats']['liquido'])} em {n(cimp('r400', 'fora da consolidacao 100 E nao')['stats']['trades'])} trades,
rebaixamento {rs(-cimp('r400', 'fora da consolidacao 100 E nao')['stats']['dd_max'])} (stop 100 / alvo 400).</li>
<li><b>Manter o corte de pavio do fechamento</b> do HullRetracao_Azul.</li>
<li><b>Candidato forte: exigir pavio do fechamento zero</b>, com <code>PavioFechMaxPct(0)</code> no indicador (sobram ~{n(k_0['r400']['stats']['trades'] / M['pregoes'], 1)} trades por pregao).
Menos lucro total que o setup atual na gestao do CLAUDE.md ({rs(k_0['claude']['stats']['liquido'])} x {rs(k_setup['claude']['stats']['liquido'])}), mas metade do rebaixamento
e muito mais resistente a slippage. Com stop 100 / alvo 400 fica perto do setup atual no total ({rs(k_0['r400']['stats']['liquido'])} x {rs(k_setup['r400']['stats']['liquido'])}), com metade do rebaixamento.</li>
<li>Pavio da abertura: <b>nao filtrar</b>. Nem a faixa magenta nem a verde se sustentam aqui. O martelo (abertura acima de 90 pts) fica em observacao.</li>
<li>Somado aos filtros anteriores: pavio zero + picado deu {rs(k_0p['r400']['stats']['liquido'])} em {n(k_0p['r400']['stats']['trades'])} trades, fator {n(k_0p['r400']['stats']['fator_lucro'], 2)}
(CLAUDE.md {rs(k_0p['claude']['stats']['liquido'])}). Poucos trades e combinacao escolhida depois de ver os dados.</li>
</ul></div>
</section>
"""
    return H


JS = r"""
const T=__T__;
const $=s=>document.querySelector(s);
function cv(k){return getComputedStyle(document.documentElement).getPropertyValue('--'+k).trim();}
function fmt(v,c=0){if(v===null||v===undefined||Number.isNaN(v))return '-';return Number(v).toLocaleString('pt-BR',{minimumFractionDigits:c,maximumFractionDigits:c});}
function linhas(el,series,op={}){
  const W=Math.max(300,el.clientWidth||600), H=op.alt||260, m={e:64,d:12,t:10,b:24};
  let ys=[0];series.forEach(s=>s.y.forEach(v=>{if(v!==null)ys.push(v);}));
  let y0=Math.min(...ys),y1=Math.max(...ys); if(y1===y0)y1+=1; const pad=(y1-y0)*.06; y0-=pad; y1+=pad;
  const nx=Math.max(...series.map(s=>s.y.length));
  const X=(i,len)=>m.e+(W-m.e-m.d)*(len<=1?0:i/(len-1)), Y=v=>m.t+(H-m.t-m.b)*(1-(v-y0)/(y1-y0));
  let s=`<svg viewBox="0 0 ${W} ${H}" role="img">`;
  for(let k=0;k<=4;k++){const v=y0+(y1-y0)*k/4;s+=`<line x1="${m.e}" x2="${W-m.d}" y1="${Y(v)}" y2="${Y(v)}" stroke="${cv('grade')}"/><text x="${m.e-6}" y="${Y(v)+4}" text-anchor="end" font-size="11" fill="${cv('mudo')}">${fmt(v)}</text>`;}
  s+=`<line x1="${m.e}" x2="${W-m.d}" y1="${Y(0)}" y2="${Y(0)}" stroke="${cv('eixo')}"/>`;
  s+=`<text x="${W-m.d}" y="${H-6}" text-anchor="end" font-size="11" fill="${cv('mudo')}">trades (cada curva na propria escala) &rarr;</text>`;
  series.forEach(se=>{const L=se.y.length;const p=se.y.map((v,i)=>`${X(i,L).toFixed(1)},${Y(v).toFixed(1)}`).join(' ');
    s+=`<polyline fill="none" stroke="${se.cor}" stroke-width="${se.larg||1.6}" points="${p}"/>`;});
  s+='</svg>';
  el.innerHTML=`<div class="leg">${series.map(se=>`<span><i style="background:${se.cor}"></i>${se.nome}</span>`).join('')}</div>`+s;
}
const CORES=()=>[cv('tinta'),cv('azul'),cv('ganho'),cv('ouro'),cv('perda'),cv('alerta'),cv('prata'),'#8e44ad','#16a085','#d35400','#7f8c8d'];
function curvas(){
  ['r400','claude'].forEach(gk=>{
    const cs=CORES();
    const el1=document.getElementById('g_ci_'+gk); if(el1&&el1.offsetParent)
      linhas(el1,T.imp_carteiras[gk].filter((l,i)=>[0,1,2,3,5,6].includes(i)).map((l,i)=>({nome:l.nome,cor:cs[i],y:l.eq,larg:i===0?2.6:1.5})));
    const el2=document.getElementById('g_cp_'+gk); if(el2&&el2.offsetParent)
      linhas(el2,T.pav_carteiras[gk].filter((l,i)=>[0,1,2,3,4].includes(i)).map((l,i)=>({nome:l.nome,cor:cs[i],y:l.eq,larg:i===1||i===2?2.6:1.4})));
  });
}
document.querySelectorAll('.abas[data-alvo]').forEach(el=>el.addEventListener('click',e=>{
  const b=e.target.closest('button'); if(!b) return;
  el.querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b));
  const g=el.dataset.alvo;
  if(g==='hg'||g==='hc'){
    const gk=document.querySelector('.abas[data-alvo="hg"] .on').dataset.k, ck=document.querySelector('.abas[data-alvo="hc"] .on').dataset.k;
    document.querySelectorAll('.bl2').forEach(x=>x.hidden=!(x.dataset.g===gk&&x.dataset.c===ck));
  } else document.querySelectorAll(`.bl[data-grupo="${g}"]`).forEach(x=>x.hidden=x.dataset.k!==b.dataset.k);
  curvas();
}));
curvas();
let rz; addEventListener('resize',()=>{clearTimeout(rz);rz=setTimeout(curvas,200);});
$('#btema').addEventListener('click',()=>{const r=document.documentElement;
  const escuro=r.dataset.theme?r.dataset.theme==='dark':matchMedia('(prefers-color-scheme: dark)').matches;
  r.dataset.theme=escuro?'light':'dark'; curvas();});
"""

CSS_EXTRA = """
.grade2{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}
.card ul{margin:8px 0 4px;padding-left:20px}
.card li{margin:4px 0}
"""

MENU = [('resumo', 'Resposta'), ('defs', 'Medidas'), ('hip', 'Impulso: hipoteses'), ('bandas', 'Largura da banda'), ('cimp', 'Impulso: carteira'), ('busca', 'Acaso'),
        ('fam', 'Faixas impulso'), ('padroes', 'Pavios x anterior'), ('faixas', 'Faixas pavio'), ('zero', 'Pavio zero'), ('cpav', 'Pavio: carteira'),
        ('aplicar', 'Aplicar')]


def markdown():
    M = T['meta']; PM = T['pav_meta']
    L = ['# Impulso antes do recuo e pavios do trigger', '',
         f"Setup EMA 21 + HullRetracao_Azul + MACD, WINFUT PI 20, {M['pregoes']} pregoes ({M['inicio']} a {M['fim']}). Entrada seca no fechamento, "
         f"6 contratos, R$ 0,50 por contrato. Treino ate {M['corte']}. Tabelas completas e curvas em `impulso.html`.", '',
         '## 1. Movimento amplo a favor antes do recuo / perto das bandas', '',
         f"Impulso = perna a favor ate o candle antes do recuo. Keltner Nelogica (EMA 21 +- 2,5 x range medio 21): {n(M['kc10_toca'] * 100, 0)}% dos sinais passaram da banda nos 10 candles antes do recuo. "
         f"MACD na Bollinger 1000 / 1,0: {n(M['bb20_toca'] * 100, 0)}% tocaram nos 20 candles.", '',
         '| Gestao | Conjunto | Condicao | Sinais | R$/trade | Resto | Treino (resto) | Teste (resto) | t | Percentil |', '|:--|:--|:--|--:|--:|--:|--:|--:|--:|--:|']
    for h in T['imp_hipoteses']:
        if h['conj'] == 'todos':
            L.append(f"| {CURTO_G[h['gestao']]} | {h['conj']} | {h['nome']} | {n(h['n'])} | {rs(h['ev'], 1)} | {rs(h['resto'], 1)} | "
                     f"{rs(h['ev_is'], 1)} ({rs(h['resto_is'], 1)}) | {rs(h['ev_oos'], 1)} ({rs(h['resto_oos'], 1)}) | {n(h['t'], 2)} | {n(h['pct'], 0)} |")
    L += ['', '**Largura da banda** (sinais em que o preco passou da banda antes do recuo)', '',
          '| Gestao | Banda | Janela | Sinais | R$/trade | Resto | Treino (resto) | Teste (resto) | t |', '|:--|:--|--:|--:|--:|--:|--:|--:|--:|']
    for x in T['kc_grade']:
        L.append(f"| {CURTO_G[x['gestao']]} | {'Keltner' if x['tipo'] == 'range' else 'Desvio-padrao'} {n(x['m'], 1)} | {x['W']} | {n(x['n'])} | {rs(x['ev'], 1)} | "
                 f"{rs(x['resto'], 1)} | {rs(x['ev_is'], 1)} ({rs(x['resto_is'], 1)}) | {rs(x['ev_oos'], 1)} ({rs(x['resto_oos'], 1)}) | {n(x['t'], 2)} |")
    L += ['', '**Carteira**', '']
    for gk in ('r400', 'claude'):
        L += [f'_{NOME_G[gk]}_', '', '| Filtro | Trades | Liquido | Fator | Rebaix. | Treino | Teste | Atravessar 5 |', '|:--|--:|--:|--:|--:|--:|--:|--:|']
        for l in T['imp_carteiras'][gk]:
            s = l['stats']
            L.append(f"| {l['nome']} | {n(s['trades'])} | {rs(s['liquido'])} | {n(s['fator_lucro'], 2)} | {rs(-s['dd_max'])} | {rs(l['is_']['liquido'])} | "
                     f"{rs(l['oos']['liquido'])} | {rs(l['atravessa'])} |")
        L.append('')
    b = T['imp_busca']
    L += [f"Busca automatica: {b['r400']['n_cand']} cortes; melhor t no treino {n(b['r400']['max_t'], 2)} (placebo p99 {n(b['r400']['p99'], 2)}) com alvo 400, "
          f"{n(b['claude']['max_t'], 2)} (p99 {n(b['claude']['p99'], 2)}) no CLAUDE.md. Os melhores cortes: " +
          '; '.join(c['nome'] for c in b['r400']['lista'][:4]) + '.', '',
          '## 2. Pavios do trigger com toque na EMA 21', '',
          f"Universo sem o corte de pavio: {n(PM['universo'])} sinais; setup atual (fechamento ate 10%): {n(PM['setup'])}; pavio do fechamento zero: {n(PM['fech0'])}.", '',
          '| Padrao | Universo | Antes | Gestao | Sinais | R$/trade | Resto | Treino (resto) | Teste (resto) | Percentil |', '|:--|:--|:--|:--|--:|--:|--:|--:|--:|--:|']
    for p in T['pav_padroes']:
        for gk in ('claude_fecha', 'r400_fecha', 'claude_extremo'):
            x = p[gk]
            L.append(f"| {p['nome']} | {p['univ']} | {p['antes']} | {CURTO_G[gk]} | {n(x['n'])} | {rs(x['ev'], 1)} | {rs(x['resto'], 1)} | "
                     f"{rs(x['ev_is'], 1)} ({rs(x['resto_is'], 1)}) | {rs(x['ev_oos'], 1)} ({rs(x['resto_oos'], 1)}) | {n(x['pct'], 0)} |")
    sp = T['pav_spearman']
    L += ['', f"Correlacao de posto pavio da abertura (ate 90) x resultado, no setup: alvo 400 {n(sp['r400_fecha']['rho'], 3)} (p {n(sp['r400_fecha']['p'], 2)}), "
          f"CLAUDE.md {n(sp['claude_fecha']['rho'], 3)} (p {n(sp['claude_fecha']['p'], 2)}).", '']
    for tab, tit in (('fech', 'Pavio do fechamento (sem corte)'), ('abre_setup', 'Pavio da abertura (setup atual)')):
        L += [f'**{tit}**, R$/trade', '', '| Pavio | Sinais | Alvo 400 | treino / teste | CLAUDE.md | treino / teste |', '|:--|--:|--:|--:|--:|--:|']
        for l in T['pav_faixas'][tab]:
            a = l['r400_fecha']; c = l['claude_fecha']
            L.append(f"| {l['faixa']} | {n(l['n'])} | {rs(a['ev'], 1)} | {rs(a['ev_is'], 1)} / {rs(a['ev_oos'], 1)} | {rs(c['ev'], 1)} | {rs(c['ev_is'], 1)} / {rs(c['ev_oos'], 1)} |")
        L.append('')
    L += ['**Pavio do fechamento zero x 5-10, mes a mes (R$/trade, alvo 400)**', '', '| Mes | 0 | 5-10 | acima de 10 |', '|:--|--:|--:|--:|']
    for m, v in T['pav_mensal']['r400'].items():
        L.append(f"| {m} | {rs(v['0']['ev'], 1)} | {rs(v['5-10']['ev'], 1)} | {rs(v['>10']['ev'], 1)} |")
    L += ['', '**Carteira**', '']
    for gk in ('r400', 'claude'):
        L += [f'_{NOME_G[gk]}_', '', '| Filtro | Trades | Liquido | Fator | Rebaix. | Treino | Teste | Slippage 5 | Slippage 10 |', '|:--|--:|--:|--:|--:|--:|--:|--:|--:|']
        for l in T['pav_carteiras'][gk]:
            s = l['stats']
            L.append(f"| {l['nome']} | {n(s['trades'])} | {rs(s['liquido'])} | {n(s['fator_lucro'], 2)} | {rs(-s['dd_max'])} | {rs(l['is_']['liquido'])} | "
                     f"{rs(l['oos']['liquido'])} | {rs(l['slip5'])} | {rs(l['slip10'])} |")
        L.append('')
    k0 = cpav('r400', 'pavio do fechamento = 0'); ks = cpav('r400', 'setup atual')
    L += ['## Conclusoes', '',
          '1. **Movimento amplo a favor / alem das bandas nao melhora o acerto; os mais esticados foram piores.** Preco alem da Keltner Nelogica 2,5 nos 10 candles antes do recuo: '
          'pior no treino e no teste, nas duas gestoes, e piorando com banda 3,0 e 3,5 (1,5 e 2,0 nao separam). Impulso no terco superior e MACD na Bollinger tambem abaixo do resto. '
          't de -0,5 a -1,5: candidato a filtro "evitar esticado", nao regra.',
          '2. **O corte de pavio do fechamento do HullRetracao_Azul continua valendo**: acima de 10 pts perde em carteira nas duas gestoes.',
          f"3. **Novo: pavio do fechamento zero concentra a vantagem.** Melhor que 5-10 no treino e no teste, em T1 e T2, 5 de 7 meses. Carteira alvo 400: "
          f"{rs(k0['stats']['liquido'])} (rebaix. {rs(-k0['stats']['dd_max'])}) contra {rs(ks['stats']['liquido'])} (rebaix. {rs(-ks['stats']['dd_max'])}); "
          f"com 5 pts de slippage {rs(k0['slip5'])} x {rs(ks['slip5'])}. Separacao 0 x 5-10 feita depois de ver os dados: candidato forte, `PavioFechMaxPct(0)`.",
          '4. **Pavio da abertura: nao filtrar.** Magenta ainda pior no treino, mas nao no teste; verde nao separa; "menor e melhor" nao aparece (correlacao ~0). '
          'Martelo (acima de 90 pts) bom nos dois periodos na gestao do CLAUDE.md, com poucos sinais: observar.', '',
          'Reproduzir: `python impulso.py && python impulso_rel.py`.', '']
    return '\n'.join(L)


def main():
    html = ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Impulso e pavios</title><style>{CSS}{CSS_EXTRA}</style></head><body>'
            '<nav class="indice"><div class="wrap"><ul>' + ''.join(f'<li><a href="#{a}">{r}</a></li>' for a, r in MENU) +
            '</ul></div></nav><div class="wrap">' + corpo() + '</div>'
            '<button class="tema" id="btema" title="Alternar tema" aria-label="Alternar tema">&#9681;</button>'
            '<script>' + JS.replace('__T__', json.dumps(dict(imp_carteiras=T['imp_carteiras'], pav_carteiras=T['pav_carteiras']), ensure_ascii=False)) +
            '</script></body></html>')
    open(os.path.join(BASE, 'impulso.html'), 'w', encoding='utf-8').write(html)
    open(os.path.join(BASE, 'IMPULSO.md'), 'w', encoding='utf-8').write(markdown())
    print('impulso.html', round(len(html) / 1e6, 2), 'MB')


if __name__ == '__main__':
    main()
