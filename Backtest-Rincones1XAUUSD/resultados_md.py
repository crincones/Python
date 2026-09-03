# -*- coding: utf-8 -*-
"""
Gera RESULTADOS.md a partir de saida/resumo.json.

    python rodar.py       # primeiro
    python relatorio.py   # chama este no fim

Mesma fonte do relatorio.html, mesmas frases de veredito: os dois documentos
nao podem discordar porque saem do mesmo lugar.
"""
import json
import os
import re

import engine as E
import relatorio as REL

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')
DEST = os.path.join(BASE, 'RESULTADOS.md')

PRINC = 'COMPLETO'


def _limpa(s):
    """Tira as tags HTML das frases de veredito, que sao compartilhadas."""
    s = re.sub(r'<b>(.*?)</b>', r'**\1**', s, flags=re.S)
    s = re.sub(r'<strong>(.*?)</strong>', r'**\1**', s, flags=re.S)
    s = re.sub(r'<em>(.*?)</em>', r'*\1*', s, flags=re.S)
    s = re.sub(r'<code>(.*?)</code>', r'`\1`', s, flags=re.S)
    s = re.sub(r'<[^>]+>', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def _cel(c):
    """Uma celula. O pipe TEM de ser escapado: os rotulos das metricas de [E2]
    sao |delta| / |Close-Open|, e sem escape eles partem a tabela em colunas
    extras."""
    return str(c).replace('|', r'\|')


def _tab(cab, linhas, alin=None):
    alin = alin or (['---'] + ['---:'] * (len(cab) - 1))
    out = ['| ' + ' | '.join(_cel(c) for c in cab) + ' |',
           '| ' + ' | '.join(alin) + ' |']
    out += ['| ' + ' | '.join(_cel(c) for c in l) + ' |' for l in linhas]
    return '\n'.join(out)


def _met(m):
    if not m:
        return ['—'] * 8
    return [m['n'], REL.usd(m['ev'], 3), REL.usd(m['total'], 1),
            REL.p1(m['acerto']), REL.t2(m['t']), REL.p0(m['dias_pos']),
            REL.f2(m['pf']), REL._br('%.1f' % m['dd'])]


CAB = ['', 'n', 'EV', 'total', 'acerto', 't', 'dias+', 'PF', 'DD']


def secao_comparativa(R, chave, ordem, rotulos, stop, titulo):
    linhas = []
    for base in E.BASES:
        linhas.append(['**%s**' % R['rot_base'][base], '', '', '', '', '', '', '', ''])
        for k in ordem:
            g = R[chave]['grid'][base].get(k)
            if not isinstance(g, dict) or str(stop) not in g:
                continue
            marca = ' ←' if k == R[chave].get('atual') else ''
            linhas.append([rotulos.get(k, k) + marca] + _met(g[str(stop)]))
    tab = _tab(CAB, linhas)
    return ('%s\n\n%s' % (titulo, tab)) if titulo else tab


def grava():
    with open(os.path.join(SAIDA, 'resumo.json'), encoding='utf-8') as f:
        R = json.load(f)

    stop = R['stops'][0]
    st = str(stop)
    p = R['parametros']
    det = R['bases'][PRINC]
    v = R['variantes'][PRINC]['ema3'][st]
    tudo = v['cTudo']
    b = REL._br

    L = []
    A = L.append

    A('# Resultados — Rincones1 XAUUSD')
    A('')
    A('> **Gerado por `python rodar.py && python relatorio.py`. Não edite à mão.** '
      'Todos os números saem de `saida/resumo.json`, os mesmos do `relatorio.html`.')
    A('')
    A('%s barras de 521 ticks do XAUUSD, %d pregões, %s a %s. Valores em **USD por '
      'onça** — 1,00 de movimento vale %d USD num lote padrão de 100 oz. Tudo '
      '**bruto**, exceto a § 8.'
      % (REL.mil(det['barras']), det['pregoes'],
         det['ini'], det['fim'], round(p['VAL_PONTO'])))
    A('')
    A('Configuração padrão: gatilho `[%s] ≥ %s` lido contra a direção do **%s**, '
      'geometria **%s** com corte de posição %s, corpo ≤ %s%% do range · entrada '
      '**%s** · stop %s, parcial de %d%% na distância do stop, alvo %s · uma posição '
      'por vez.'
      % ('+'.join(p['EIXOS']) if isinstance(p['EIXOS'], (list, tuple))
         else str(p['EIXOS']).strip("()',").replace("', '", '+'),
         b('%.2f' % p['NIVEL_MIN']), p['REFERENCIA'], p['GEOMETRIA'],
         b('%.0f' % p['CORTE_POSICAO']), b('%.0f' % p['CORPO_MAX']),
         'a mercado no fechamento' if p['ENTRADA'] == 'fecha'
         else 'limitada no meio do candle',
         b('%.2f' % p['STOP']), round(100 * p['FRAC_PARCIAL']),
         b('%.2f' % p['ALVO'])))
    A('')

    # ---------------------------------------------------------------- 1
    A('## 1. O resultado')
    A('')
    linhas = []
    for base in E.BASES:
        vb = R['variantes'][base]['ema3'][st]
        linhas.append(['**%s** · %d gatilhos' % (R['rot_base'][base], vb['gatilhos']),
                       '', '', '', '', '', '', '', ''])
        for rot, ch in (('carteira completa (A+B+C+L) ←', 'cTudo'),
                        ('só A + B + C', 'cABC'), ('só A + B', 'cAB'),
                        ('só A', 'cA')):
            linhas.append([rot] + _met(vb[ch]))
    A(_tab(CAB, linhas))
    A('')
    A(_limpa(REL.frase_metades(R)))
    A('')

    # ---------------------------------------------------------------- 2
    A('## 2. O que o porte teve de mudar')
    A('')
    A('Quatro peças. Em cada linha, só a coluna muda; todo o resto fica congelado. '
      'EV por trade em USD, amostra inteira, stop %s.' % b('%.2f' % stop))
    A('')
    lin = []
    for rot, sec, ka, kb in (('eixo do índice', 'eixos', 'E2+E3+E4', 'E4'),
                             ('direção lida', 'referencia', 'delta', 'candle'),
                             ('geometria', 'geometria', 'classica', 'inversa'),
                             ('entrada', 'entrada', 'meio', 'fecha')):
        ea = REL._ev(R, sec, ka)[0]
        eb = REL._ev(R, sec, kb)[0]
        lin.append([rot, ka, REL.usd(ea, 3), '**%s**' % kb, REL.usd(eb, 3),
                    REL.usd((eb or 0) - (ea or 0), 3)])
    A(_tab(['o que', 'no WIN', 'EV', 'no ouro', 'EV', 'diferença'], lin))
    A('')
    A(_limpa(REL.ver_porte(R)))
    A('')

    # ---------------------------------------------------------------- 3
    A('## 3. A direção é do candle, não do delta')
    A('')
    A(secao_comparativa(R, 'referencia', R['referencia']['ordem'],
                        R['referencia']['rotulos'], stop, ''))
    A('')
    A('Na B3 a bolsa publica a flag de agressor de cada negócio. No XAUUSD ela é '
      '**inferida** pela tick rule, e o delta resultante concorda com o sinal do '
      'próprio candle em só 63,2% das barras — não é a mesma variável. Medido, a '
      'direção que serve para ler o esforço é a do candle.')
    A('')

    # ---------------------------------------------------------------- 4
    A('## 4. De que eixo é o índice')
    A('')
    A(_limpa(REL.ver_degenerado(R)))
    A('')
    A(secao_comparativa(R, 'eixos', R['eixos']['ordem'],
                        {k: k.replace('+', ' + ') + ' (nível %s)'
                         % b('%.2f' % R['eixos']['niveis'][k])
                         for k in R['eixos']['ordem']}, stop, ''))
    A('')
    A(_limpa(REL.ver_eixos(R)))
    A('')

    # ---------------------------------------------------------------- 5
    A('## 5. O eixo [E2]: fórmula antiga contra a nova')
    A('')
    A('O índice padrão daqui não usa `[E2]` (§ 4), então a comparação roda sobre o '
      'índice de três eixos `%s` no nível %s — a configuração mais próxima do '
      'backtest do WIN que este ativo aceita.'
      % (R['e2']['eixos'], b('%.2f' % R['e2']['nivel'])))
    A('')
    A(secao_comparativa(R, 'e2', R['e2']['metricas'], R['e2']['rotulos'], stop, ''))
    A('')
    A(_limpa(REL.ver_e2(R)))
    A('')

    # ---------------------------------------------------------------- 6
    A('## 6. A geometria de rejeição está invertida')
    A('')
    A(secao_comparativa(R, 'geometria', R['geometria']['ordem'],
                        R['geometria']['rotulos'], stop, ''))
    A('')
    A(_limpa(REL.ver_geo(R)))
    A('')
    A('> Não é achado novo. O `Delta_Fraqueza.mqh` registrou a mesma inversão no '
      '`XAUUSD_19_DT`, e o `[D4]` de `Ticks_Esforco_v2.mqh` a remediu no '
      '`XAUUSD_521_TK`. Esta é a terceira vez que o mesmo sinal aparece trocado no '
      'ouro, agora no nível do trade.')
    A('')

    # ---------------------------------------------------------------- 7
    A('## 7. A entrada')
    A('')
    A(secao_comparativa(R, 'entrada', R['entrada']['ordem'],
                        R['entrada']['rotulos'], stop, ''))
    A('')
    A(_limpa(REL.ver_entrada(R)))
    A('')

    # ---------------------------------------------------------------- 8
    A('## 8. Stop, alvo e custo')
    A('')
    A('EV por trade em USD, amostra inteira. Linha = stop, coluna = alvo.')
    A('')
    g = det['grade']
    cab = ['stop \\ alvo'] + [b('%.1f' % a) for a in det['grade_alvos']]
    lin = []
    for stp in det['grade_stops']:
        cel = []
        for al in det['grade_alvos']:
            vv = g.get('%.1f_%.1f' % (stp, al))
            txt = REL.usd(vv, 2)
            if stp == p['STOP'] and al == p['ALVO']:
                txt = '**%s**' % txt
            cel.append(txt)
        lin.append([b('%.1f' % stp)] + cel)
    A(_tab(cab, lin))
    A('')
    A(_limpa(REL.ver_grade(R)))
    A('')
    A('### O custo')
    A('')
    lin = []
    for base in E.BASES:
        lin.append(['**%s**' % R['rot_base'][base], '', '', '', '', '', '', '', ''])
        for c in (0.0, 0.10, 0.20, 0.50):
            lin.append(['custo %s USD' % b('%.2f' % c)]
                       + _met(R['bases'][base]['custo_%.2f' % c]))
    A(_tab(CAB, lin))
    A('')
    A(_limpa(REL.ver_custo(R)))
    A('')
    A('### A regra da parcial')
    A('')
    A(secao_comparativa(R, 'gestao', R['gestao']['ordem'], R['gestao']['rotulos'],
                        stop, ''))
    A('')
    A(_limpa(REL.ver_gestao(R)))
    A('')

    # ---------------------------------------------------------------- 9
    A('## 9. Os setups e as médias de regime')
    A('')
    lin = []
    for base in E.BASES:
        vb = R['variantes'][base]['ema3'][st]
        lin.append(['**%s**' % R['rot_base'][base], '', '', '', '', '', '', '', ''])
        for su in ('A', 'B', 'C', 'L'):
            lin.append(['setup %s isolado (%d sinais)' % (su, vb['sinais_' + su])]
                       + _met(vb['setup_' + su]))
        for rot, ch in (('carteira A', 'cA'), ('carteira A+B', 'cAB'),
                        ('carteira A+B+C', 'cABC'),
                        ('carteira completa ←', 'cTudo')):
            lin.append([rot] + _met(vb[ch]))
    A(_tab(CAB, lin))
    A('')
    A(_limpa(REL.ver_setups(R)))
    A('')
    A('### As médias adaptativas')
    A('')
    lin = []
    for base in E.BASES:
        lin.append(['**%s**' % R['rot_base'][base], '', '', '', ''])
        for reg in R['regimes']:
            vb = R['variantes'][base][reg][st]
            a, ca = vb['setup_A'], vb['cA']
            lin.append([E.ROT_MA[reg], REL.p0(vb['tend']),
                        (a or {}).get('n', 0), REL.usd((a or {}).get('ev'), 3),
                        REL.t2((a or {}).get('t'))])
    A(_tab(['média de regime', '% em tendência', 'n (setup A)', 'EV do A', 't do A'],
           lin))
    A('')
    A(_limpa(REL.ver_ma(R)))
    A('')

    # ---------------------------------------------------------------- 10
    A('## 10. Estabilidade do corte')
    A('')
    A('EV por trade em USD, carteira completa, stop %s. Linha = nível do índice, '
      'coluna = corte de posição do corpo. O padrão está em negrito.'
      % b('%.2f' % stop))
    A('')
    Rs = R['estabilidade']
    at = '%.2f_%.0f' % tuple(Rs['atual'])
    for base in E.BASES:
        A('**%s**' % R['rot_base'][base])
        A('')
        cab = ['nível \\ pos'] + ['%.0f' % x for x in Rs['pos']]
        lin = []
        for niv in Rs['niveis']:
            cel = []
            for pos in Rs['pos']:
                k = '%.2f_%.0f' % (niv, pos)
                c = Rs['grid'][base].get(k)
                txt = '—' if not c else REL.usd(c['ev'], 2)
                if k == at:
                    txt = '**%s**' % txt
                cel.append(txt)
            lin.append([b('%.2f' % niv)] + cel)
        A(_tab(cab, lin))
        A('')
    A(_limpa(REL.ver_estab(R)))
    A('')

    # ---------------------------------------------------------------- 11
    A('## 11. A forma do desempenho')
    A('')
    A('Carteira completa, stop %s, **com %s USD de custo por trade**.'
      % (b('%.2f' % stop),
         b('%.2f' % det['psico'][st]['tudo_c20']['custo'])))
    A('')
    campos = (('n', 'trades'), ('por_pregao', 'por pregão'),
              ('acerto', 'acerto (%)'), ('ev', 'EV por trade'),
              ('media_dia', 'média por pregão'), ('sd_dia', 'desvio por pregão'),
              ('dias_pos', 'pregões positivos (%)'), ('pior_dia', 'pior pregão'),
              ('melhor_dia', 'melhor pregão'), ('dd', 'rebaixamento máximo'),
              ('seq_trades', 'maior sequência sem ganhar'),
              ('seq_dias', 'maior sequência de pregões negativos'),
              ('p_semana_neg', 'chance de semana negativa (%)'),
              ('p_mes_neg', 'chance de mês negativo (%)'),
              ('p_alvo', 'terminam no alvo (%)'), ('p_stop', 'terminam no stop (%)'),
              ('p_zero', 'terminam em zero a zero (%)'),
              ('p_fim', 'terminam no fim do pregão (%)'))
    ps = {bs: det['psico'][st]['tudo_c20'] if bs == PRINC
          else R['bases'][bs]['psico'][st]['tudo_c20'] for bs in E.BASES}
    lin = []
    for k, rot in campos:
        lin.append([rot] + [('—' if (ps[bs] is None or ps[bs].get(k) is None)
                             else b(str(ps[bs][k]))) for bs in E.BASES])
    A(_tab([''] + [R['rot_base'][bs] for bs in E.BASES], lin))
    A('')
    A(_limpa(REL.ver_psico(R)))
    A('')

    # ---------------------------------------------------------------- 12
    A('## 12. Limites')
    A('')
    A('- **Uma amostra, não duas.** Um instrumento, um histórico. As duas “metades” '
      'são o mesmo arquivo partido ao meio — concordância entre elas é evidência '
      'fraca, não confirmação fora da amostra.')
    A('- **%d pregões, %s a %s.** O ouro passou por um regime só nesse intervalo.'
      % (det['pregoes'], det['ini'], det['fim']))
    A('- **O corte foi varrido.** O nível %s e o corte de posição %s vieram da '
      'varredura da § 10 sobre esta mesma amostra.'
      % (b('%.2f' % p['NIVEL_MIN']), b('%.0f' % p['CORTE_POSICAO'])))
    A('- **Números brutos**, exceto a § 8 e a § 11.')
    A('- **Preenchimento otimista** na entrada (a mercado, sem slippage) e '
      '**pessimista** na saída (stop antes do alvo quando cabem na mesma barra).')
    A('- **O delta é inferido** pela tick rule, não publicado. Ele não é usado como '
      'direção, mas entra no eixo `[E2]` da § 5.')
    A('')

    # ---------------------------------------------------------------- 13
    A('## 13. O que fazer com isto')
    A('')
    for i, a in enumerate(REL.acoes(R), 1):
        A('%d. %s' % (i, _limpa(a)))
    A('')

    txt = '\n'.join(L) + '\n'
    with open(DEST, 'w', encoding='utf-8') as f:
        f.write(txt)
    print('RESULTADOS.md gravado (%.1f KB)' % (len(txt.encode('utf-8')) / 1024))
    return txt


if __name__ == '__main__':
    grava()
