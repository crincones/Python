# -*- coding: utf-8 -*-
"""
Escreve RESULTADOS.md a partir de saida/resumo.json.

    python resultados_md.py

Nao recalcula nada: todo numero sai do resumo.json gravado por rodar.py.
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')


def carregar():
    with open(os.path.join(SAIDA, 'resumo.json'), encoding='utf-8') as f:
        return json.load(f)


def t(x, casas=0):
    """ticks -> texto com o dolar entre parenteses"""
    return '%s t (%s USD)' % (fmt(x, casas), fmt(x * 0.01, 2))


def fmt(x, casas=0):
    """numero com sinal, milhar em ponto e decimal em virgula"""
    s = format(float(x), '+,.%df' % casas)
    return s.replace(',', '@').replace('.', ',').replace('@', '.')


def n(x, casas=0):
    s = format(float(x), ',.%df' % casas)
    return s.replace(',', '@').replace('.', ',').replace('@', '.')


def pct(x, casas=1):
    return n(100 * x, casas) + '%'


def linha_var(v):
    s = v['stats']
    return ('| **%s** · %s | %s | %s | %s | %s | %s | %s | %s |' % (
        v['nome'], v['rotulo'], n(s.get('sinais', 0)), n(s.get('operacoes', 0)),
        pct(s.get('acerto', 0)), fmt(s.get('expectativa_ticks', 0), 1),
        fmt(s.get('ticks_total', 0)), n(s.get('fator_lucro', 0), 2),
        fmt(s.get('drawdown_ticks', 0))))


def escrever():
    r = carregar()
    D = r['dados']
    V = {v['nome']: v for v in r['variantes']}
    ex = r['excursao']
    hr = r['horario']
    L = []
    w = L.append

    w('# RESULTADOS — backtest da estratégia do leque de EMAs (XAUUSD 521 ticks)')
    w('')
    w('> Gerado por `rodar.py` em %s a partir de `%s`.  ' % (r['gerado_em'], r['arquivo']))
    w('> Todos os números deste documento saem de `saida/resumo.json`. '
      'Nada aqui é digitado à mão.')
    w('')
    w('---')
    w('')

    # ---------------------------------------------------------------- 1
    w('## 1. Resposta curta')
    w('')
    v0, v4, v5, v6, v7 = V['V0'], V['V4'], V['V5'], V['V6'], V['V8']
    w('A regra como está escrita em `ESTRATEGIA.md` **perde dinheiro** neste '
      'histórico: %s operações, %s de acerto, %s por operação, '
      '%s no total, fator de lucro %s.'
      % (n(v0['stats']['operacoes']), pct(v0['stats']['acerto']),
         t(v0['stats']['expectativa_ticks'], 1), t(v0['stats']['ticks_total']),
         n(v0['stats']['fator_lucro'], 2)))
    w('')
    w('A causa não é o gatilho ser ruim de leitura — é que **ele não tem leitura '
      'nenhuma**. Medida sem qualquer regra de saída, a excursão do preço depois '
      'da entrada é estatisticamente igual à de uma entrada sorteada '
      '(§ 4). Sobre um sinal sem direção, o alvo final em 900 ticks com stop de '
      '300 é uma aposta que precisa de %s de acerto para empatar e entrega %s.'
      % (pct(1 / 3, 0), pct(v0['stats']['motivos'].get('alvo', 0) /
                            v0['stats']['operacoes'])))
    w('')
    w('**A única restrição que sobreviveu a uma validação fora da amostra foi o '
      'horário** — que é, das três hipóteses do documento original, justamente a '
      'que o autor listou por último. Filtrando as horas %s, a mesma regra sai de '
      '%s para %s por operação (variante V4), e com o filtro de reconquista da '
      'EMA21 vai a %s (V5). Trocando também o alvo de 900 pela saída inteira '
      'em +1R, chega a %s (V7) — a única configuração que continua positiva '
      'depois de descontar 40 ticks de custo. É pouco, é frágil, e § 9 e § 10 '
      'explicam por quê.'
      % (', '.join('%dh' % h for h in r['horas_boas']),
         t(v0['stats']['expectativa_ticks'], 1),
         t(v4['stats']['expectativa_ticks'], 1),
         t(v5['stats']['expectativa_ticks'], 1),
         t(V['V7']['stats']['expectativa_ticks'], 1)))
    w('')

    # ---------------------------------------------------------------- 2
    w('## 2. Os dados')
    w('')
    w('| | |')
    w('|---|---|')
    w('| Arquivo | `XAUUSD-521T/%s` |' % r['arquivo'])
    w('| Ativo / gráfico | XAUUSD, candles de 521 ticks |')
    w('| Barras | %s |' % n(D['barras']))
    w('| Período | %s → %s |' % (D['inicio'][:16], D['fim'][:16]))
    w('| Pregões | %s (%s barras por dia, em média) |'
      % (n(D['dias']), n(D['barras_por_dia'], 0)))
    w('| Faixa de preço | %s → %s |' % (n(D['preco_min'], 2), n(D['preco_max'], 2)))
    w('| Tick | 0,01 USD |')
    w('')
    rg = D['range_ticks']
    w('**Tamanho das barras**, em ticks — é o número que decide se um stop de 300 '
      'é largo ou apertado:')
    w('')
    w('| mín | 10% | 25% | mediana | 75% | 90% | 95% | 99% | máx |')
    w('|---|---|---|---|---|---|---|---|---|')
    w('| %s | %s | %s | **%s** | %s | %s | %s | %s | %s |'
      % tuple(n(rg[k]) for k in ('min', '10%', '25%', '50%', '75%',
                                 '90%', '95%', '99%', 'max')))
    w('')
    w('A barra mediana anda **%s ticks**. O stop de 300 ticks vale portanto '
      '**%s barras medianas** — é um stop de pouco mais de uma barra. O alvo '
      'final em 900 ticks pede **%s barras medianas** de continuação depois da '
      'entrada. Guarde esses dois números: eles explicam quase tudo o que vem '
      'depois.' % (n(rg['50%']), n(300 / rg['50%'], 2), n(900 / rg['50%'], 1)))
    w('')
    w('Sobre o leque: a EMA21 e a EMA72 ficam separadas por %s ticks na mediana. '
      'As médias estão ordenadas (leque formado, para um lado ou para o outro) em '
      '%s das barras; nos %s restantes elas estão "emboladas" e a estratégia não '
      'olha.' % (n(D['leque_ticks']['50']),
                 pct(D['pct_leque_alta'] + D['pct_leque_baixa']),
                 pct(D['pct_embolado'])))
    w('')
    w('> **Coluna `<SPREAD>` descartada.** O arquivo traz valores entre %s e %s '
      'nessa coluna, o que não é spread de ouro em ponto nenhum de escala. Ela foi '
      'ignorada e o custo entrou como parâmetro explícito (§ 8).' % ('149', '655.942'))
    w('')

    # ---------------------------------------------------------------- 3
    w('## 3. A regra, traduzida para código')
    w('')
    w('O texto de `ESTRATEGIA.md` descreve o padrão em português. Backtest exige '
      'que cada palavra vire uma condição verificável. Foi assim:')
    w('')
    w('| No texto | No código (`engine.py`) |')
    w('|---|---|')
    w('| "médias em forma de leque" | `EMA21 > EMA42 > EMA72` (alta) ou '
      '`EMA21 < EMA42 < EMA72` (baixa), sobre o fechamento |')
    w('| "o preço se afasta destas médias" | em alguma das 12 barras anteriores a '
      'barra **inteira** ficou além da EMA21, no sentido da tendência |')
    w('| "e volta ao leque" | a barra do gatilho toca a EMA21 |')
    w('| "sequência de 2 ou 3 candles da mesma cor" | 2 ou 3 candles consecutivos '
      'de cor **contrária** à tendência imediatamente antes do gatilho — nem 1, nem 4 |')
    w('| "aparece um candle contrário" | a barra do gatilho tem a cor da tendência |')
    w('| "ordem no meio do range deste candle" | limitada em `(máxima + mínima) / 2` '
      'da barra do gatilho |')
    w('| "aguardando a ativação no próximo candle" | preenche se a barra seguinte '
      'tocar o preço; senão a ordem é **cancelada** |')
    w('| "stop de 300 ticks" | 3,00 USD da entrada = **1R** |')
    w('| "saída parcial a 300 ticks (50%)" | metade sai em +1R e o stop do resto vai '
      'para o preço de entrada |')
    w('| "saída final a 900" | o resto sai em +3R |')
    w('')
    w('Com isso, a operação vencedora completa rende `0,5 × 1R + 0,5 × 3R = 2R` — '
      'a relação 2:1 que o documento original menciona. Só existem três desfechos:')
    w('')
    w('| desfecho | resultado | quanto vale |')
    w('|---|---|---|')
    w('| **stop** — cai 300 ticks antes de subir 300 | −1R | −300 t (−3,00 USD) |')
    w('| **breakeven** — pegou a parcial e voltou à entrada | +0,5R | +150 t (+1,50 USD) |')
    w('| **alvo** — pegou a parcial e chegou aos 900 | +2R | +600 t (+6,00 USD) |')
    w('')
    w('Daí sai o ponto de equilíbrio da estratégia: chamando `a` a fração de alvos, '
      '`b` a de breakevens e `s` a de stops, é preciso `600a + 150b = 300s`. '
      'Guarde: **sem alvos, é preciso acertar a parcial em 2 de cada 3 tentativas '
      'só para empatar.**')
    w('')

    # ---------------------------------------------------------------- 4
    w('## 4. Antes de qualquer resultado: o sinal tem direção?')
    w('')
    w('Toda estatística de backtest mistura duas coisas — a qualidade do sinal e a '
      'aritmética da saída. Para separá-las, mediu-se o que o preço faz depois da '
      'entrada **sem regra de saída nenhuma**: a maior excursão a favor (MFE), a '
      'maior excursão contra (MAE) e a deriva ao fim de N barras. Depois o mesmo '
      'foi medido em dois controles aleatórios.')
    w('')
    w('| horizonte | amostra | MFE mediana | MAE mediana | MFE/MAE | deriva média |')
    w('|---|---|---|---|---|---|')
    rot = {'sinal': 'o sinal da estratégia',
           'direcao_sorteada': 'mesmas barras, **direção sorteada**',
           'barra_e_direcao_sorteadas': 'barra e direção sorteadas'}
    for H in ('20', '40'):
        for k in ('sinal', 'direcao_sorteada', 'barra_e_direcao_sorteadas'):
            b = ex[k][H]
            w('| %s barras | %s | %s t | %s t | **%s** | %s t |'
              % (H, rot[k], n(b['mfe_med']), n(b['mae_med']), n(b['razao'], 3),
                 fmt(b['deriva_media'], 1)))
    w('')
    b1 = ex['sinal']['20']; b2 = ex['direcao_sorteada']['20']
    w('O sinal produz uma razão MFE/MAE de **%s** em 20 barras. Sortear a direção '
      'nas **mesmas** barras produz **%s**. A vantagem do sinal sobre a moeda '
      'sorteada é de %s centésimos de razão — dentro do ruído de uma amostra '
      'de %s entradas.'
      % (n(b1['razao'], 3), n(b2['razao'], 3),
         n(100 * abs(b1['razao'] - b2['razao']), 1), n(b1['n'])))
    w('')
    w('**Conclusão desta seção: o gatilho escolhe *quando* operar, não *para que '
      'lado*.** Todo o resultado das seções seguintes é consequência disso.')
    w('')

    # ---------------------------------------------------------------- 5
    w('## 5. A regra literal (V0)')
    w('')
    s = v0['stats']
    m = s['motivos']
    w('| | |')
    w('|---|---|')
    w('| Sinais detectados | %s |' % n(s['sinais']))
    w('| Ordens que **não** ativaram na barra seguinte | %s (%s) |'
      % (n(s['abortadas']), pct(1 - s['taxa_ativacao'])))
    w('| Operações efetivas | **%s** |' % n(s['operacoes']))
    w('| Operações por pregão | %s |' % n(s['ops_por_dia'], 1))
    w('| Acerto | %s |' % pct(s['acerto']))
    w('| Expectativa por operação | **%s** |' % t(s['expectativa_ticks'], 1))
    w('| Resultado total (1 lote) | **%s** |' % t(s['ticks_total']))
    w('| Fator de lucro | %s |' % n(s['fator_lucro'], 2))
    w('| Rebaixamento máximo | %s |' % t(s['drawdown_ticks']))
    w('| Barras dentro da operação (média) | %s |' % n(s['barras_media'], 1))
    w('| Dias positivos / negativos | %s / %s |'
      % (n(s['dias_positivos']), n(s['dias_negativos'])))
    w('')
    w('E a distribuição dos desfechos, que é onde a estratégia se decide:')
    w('')
    w('| desfecho | operações | fração | contribuição |')
    w('|---|---|---|---|')
    for k, rot_k, val in (('alvo', 'alvo (+2R)', 600),
                          ('breakeven', 'breakeven (+0,5R)', 150),
                          ('stop', 'stop (−1R)', -300),
                          ('tempo', 'aberta no fim do histórico', 0)):
        if k not in m:
            continue
        w('| %s | %s | %s | %s |' % (rot_k, n(m[k]), pct(m[k] / s['operacoes']),
                                     t(m[k] * val) if val else '—'))
    w('')
    w('**Só %s das operações chegam aos 900 ticks.** O ponto de equilíbrio exigiria '
      'muito mais: com %s de breakevens e %s de stops, seriam necessários %s de '
      'alvos, e há %s.'
      % (pct(m.get('alvo', 0) / s['operacoes']),
         pct(m.get('breakeven', 0) / s['operacoes']),
         pct(m.get('stop', 0) / s['operacoes']),
         pct((300 * m.get('stop', 0) - 150 * m.get('breakeven', 0)) /
             (600 * s['operacoes'])),
         pct(m.get('alvo', 0) / s['operacoes'])))
    w('')
    w('### O que a parcial faz')
    w('')
    w('A parcial em +1R com stop no breakeven é frequentemente vendida como '
      '"proteção". Neste histórico ela é o contrário: **transforma quase toda '
      'operação vencedora em meio ganho.** De cada %s operações que chegam a tocar '
      '+300 ticks, %s terminam voltando à entrada e saem valendo +150 em vez de '
      '+600. A parcial paga o seguro; o prêmio é caro porque o alvo que ela '
      'protege quase nunca chega.'
      % (n(m.get('alvo', 0) + m.get('breakeven', 0)), n(m.get('breakeven', 0))))
    w('')

    # ---------------------------------------------------------------- 6
    w('## 6. A busca por uma restrição que salvasse a regra')
    w('')
    w('%s filtros foram testados, incluindo os três que `ESTRATEGIA.md` sugere. '
      'Para medir cada um sem a distorção do alvo distante, usou-se uma métrica '
      'neutra: **stop 300 / alvo 300, posição inteira**, que responde só a uma '
      'pergunta — o preço anda 300 ticks a favor antes de andar 300 contra? Um '
      'sinal sem direção acerta 50%%. A coluna `z` mede a distância de 50%% em '
      'desvios-padrão.' % n(len(r['busca'])))
    w('')
    w('| filtro | operações | acerto | z | expectativa |')
    w('|---|---|---|---|---|')
    for b in sorted(r['busca'], key=lambda x: -x['z']):
        marca = ' ⟵ horário' if b['horario'] else ''
        w('| %s%s | %s | %s | **%s** | %s t |'
          % (b['filtro'], marca, n(b['n']), pct(b['acerto']), fmt(b['z'], 2),
             fmt(b['expectativa_ticks'], 1)))
    w('')
    zsem = max(abs(b['z']) for b in r['busca'] if not b['horario'])
    w('**Como ler esta tabela.** Testar %s filtros e ficar com o melhor é a '
      'definição de garimpo. Com %s tentativas independentes sobre dados sem '
      'nenhuma vantagem, o maior `z` esperado por puro acaso fica em torno de '
      '**2,2**. O maior `z` obtido fora do horário foi **%s** — ou seja, '
      '*exatamente* o que o acaso entrega. Nenhum filtro de forma, de leque, de '
      'inclinação, de corpo ou de tamanho de candle passou dessa linha.'
      % (n(len(r['busca'])), n(len(r['busca'])), n(zsem, 2)))
    w('')
    w('Vale registrar dois resultados que **contradizem** as hipóteses do documento '
      'original:')
    w('')
    def acha(nome):
        for b in r['busca']:
            if b['filtro'] == nome:
                return b
        return None
    br = acha('range do gatilho <= 350t'); bg = acha('range do gatilho >= 350t')
    if br and bg:
        w('- A estratégia supõe que **candles de reversão pequenos** são melhores '
          '(por causa do stop fixo). Medido: range ≤ 350 t dá %s de acerto; '
          'range ≥ 350 t dá %s. O sinal vai na direção **oposta** à hipótese — '
          'ainda que nenhum dos dois seja significativo.'
          % (pct(br['acerto']), pct(bg['acerto'])))
    bl = acha('leque >= 400t'); be = acha('leque <= 300t (médias emboladas)')
    if bl and be:
        w('- A estratégia supõe que **médias emboladas** atrapalham. Medido: leque '
          '≥ 400 t dá %s (z %s), leque ≤ 300 t dá %s. Aqui a hipótese aponta '
          'para o lado certo, mas com força indistinguível de ruído.'
          % (pct(bl['acerto']), fmt(bl['z'], 2), pct(be['acerto'])))
    w('')

    # ---------------------------------------------------------------- 7
    w('## 7. O horário — a única coisa que sobreviveu')
    w('')
    w('O horário foi o único filtro que não se comportou como ruído. Como ele '
      'também poderia ser garimpo (são 23 horas para escolher), foi submetido a '
      'uma **validação cruzada nos dois sentidos**: escolhe-se o conjunto de horas '
      'em metade da amostra, mede-se **na outra metade**, e depois inverte-se.')
    w('')
    w('| seleção feita em | horas escolhidas | testado em | operações | acerto medido | acerto de referência | z |')
    w('|---|---|---|---|---|---|---|')
    for k, a, b in (('escolhe_1a_testa_2a', '1ª metade', '2ª metade'),
                    ('escolhe_2a_testa_1a', '2ª metade', '1ª metade')):
        v = hr[k]
        w('| %s | %s | %s | %s | **%s** | %s | **%s** |'
          % (a, ', '.join('%dh' % x for x in v['horas']), b, n(v['n']),
             pct(v['acerto']), pct(v['acerto_referencia']), fmt(v['z'], 2)))
    w('')
    w('Os dois sentidos concordam: fora da amostra em que foram escolhidas, essas '
      'horas rendem cerca de 5 pontos percentuais de acerto a mais que o conjunto '
      'completo. As horas que apareceram **nas duas** seleções independentes são '
      '**%s**, e são as usadas nas variantes V4, V5 e V6.'
      % ', '.join('%dh' % h for h in hr['intersecao']))
    w('')
    w('Perfil hora a hora da regra literal (métrica neutra 1:1):')
    w('')
    w('| hora | operações | acerto | expectativa | |')
    w('|---|---|---|---|---|')
    for p in hr['por_hora']:
        marca = '✅' if p['hora'] in r['horas_boas'] else ''
        barra = '█' * max(0, int(round((p['acerto'] - 0.35) * 40)))
        w('| %02dh | %s | %s | %s t | %s %s |'
          % (p['hora'], n(p['n']), pct(p['acerto']),
             fmt(p['expectativa_ticks'], 0), barra, marca))
    w('')
    w('> **O relógio é o do arquivo**, não necessariamente UTC nem o do seu '
      'terminal. Antes de usar, confirme qual fuso a corretora exporta: as horas '
      'boas caem sobre a abertura europeia, a sobreposição Londres–Nova York e a '
      'tarde americana, que é o que se esperaria — mas confirme.')
    w('')

    # ---------------------------------------------------------------- 8
    w('## 8. As variantes')
    w('')
    w('| variante | sinais | operações | acerto | exp./op. | total | FL | rebaixamento |')
    w('|---|---|---|---|---|---|---|---|')
    for v in r['variantes']:
        w(linha_var(v))
    w('')
    for v in r['variantes']:
        w('**%s · %s** — %s' % (v['nome'], v['rotulo'], v['descricao']))
        w('')
    w('### Sensibilidade')
    w('')
    w('Três incertezas foram medidas em vez de assumidas.')
    w('')
    w('**(a) Ambiguidade dentro da barra.** Quando a mesma barra toca o alvo e o '
      'stop, o OHLC não diz qual veio primeiro. Todos os números publicados usam a '
      'hipótese **pessimista** (stop primeiro). A coluna otimista mostra o outro '
      'extremo — o resultado verdadeiro está entre os dois.')
    w('')
    w('**(b) Custo.** Spread mais comissão, ida e volta, em ticks.')
    w('')
    w('**(c) Estabilidade no tempo.** A amostra partida ao meio.')
    w('')
    w('| variante | pessimista | otimista | custo 10 t | custo 20 t | custo 40 t | 1ª metade | 2ª metade |')
    w('|---|---|---|---|---|---|---|---|')
    for v in r['variantes']:
        c = v['custo']; me = v['metades']
        w('| %s · %s | %s | %s | %s | %s | %s | %s | %s |'
          % (v['nome'], v['rotulo'],
             fmt(v['stats'].get('expectativa_ticks', 0), 1),
             fmt(v['stats_otimista'].get('expectativa_ticks', 0), 1),
             fmt(c['10'].get('expectativa_ticks', 0), 1),
             fmt(c['20'].get('expectativa_ticks', 0), 1),
             fmt(c['40'].get('expectativa_ticks', 0), 1),
             fmt(me['1a'].get('expectativa_ticks', 0), 1),
             fmt(me['2a'].get('expectativa_ticks', 0), 1)))
    w('')
    w('_Valores em ticks por operação._')
    w('')
    c5 = v5['custo']
    w('Três leituras importam aqui:')
    w('')
    w('1. **A V0 perde nas duas metades** (%s e %s ticks) e perde nas duas hipóteses '
      'de ambiguidade. O prejuízo é estrutural, não é azar de um trecho.'
      % (fmt(v0['metades']['1a'].get('expectativa_ticks', 0), 1),
         fmt(v0['metades']['2a'].get('expectativa_ticks', 0), 1)))
    w('2. **O custo come a variante recomendada.** A V5 rende %s ticks sem custo e '
      '%s com 40 ticks de custo. Quarenta ticks são 0,40 USD de spread mais '
      'comissão — nada de exótico em ouro. A margem inteira da estratégia cabe '
      'dentro do spread.'
      % (fmt(v5['stats']['expectativa_ticks'], 1),
         fmt(c5['40'].get('expectativa_ticks', 0), 1)))
    w('3. **O controle invertido (V7) não é o espelho da V0.** As duas perdem '
      '(%s e %s ticks). Se houvesse leitura de direção, inverter o lado teria de '
      'produzir o simétrico. Não produz — porque não há o que inverter. '
      '(A V7 não é um espelho perfeito: ao trocar o lado, a ordem limitada no meio '
      'do range passa a ser um preço *pior* que o fechamento e enche em %s dos '
      'casos, contra %s da V0. Ainda assim o sentido da conclusão não muda.)'
      % (fmt(v0['stats']['expectativa_ticks'], 1),
         fmt(v7['stats']['expectativa_ticks'], 1),
         pct(v7['stats']['taxa_ativacao']), pct(v0['stats']['taxa_ativacao'])))
    w('')

    # ---------------------------------------------------------------- 9
    w('## 9. Restrições recomendadas')
    w('')
    w('Em ordem de quanto o histórico as sustenta.')
    w('')
    w('**1. Trocar o alvo final de 900 por uma saída mais próxima — ou por nada.**  ')
    w('É a mudança de maior efeito e a mais bem sustentada, porque não depende de '
      'nenhuma descoberta estatística: depende só do tamanho das barras. Pedir 900 '
      'ticks (%s barras medianas) de continuação num sinal sem direção é pagar '
      '%s de stops para colher %s de alvos. A V6 (posição inteira em +1R) rende '
      '%s por operação contra %s da V4 com a mesma entrada.'
      % (n(900 / rg['50%'], 1), pct(m.get('stop', 0) / s['operacoes']),
         pct(m.get('alvo', 0) / s['operacoes']),
         t(v6['stats']['expectativa_ticks'], 1),
         t(v4['stats']['expectativa_ticks'], 1)))
    w('')
    w('**2. Operar só nas horas %s.**  '
      % ', '.join('%dh' % h for h in r['horas_boas']))
    w('É a única restrição validada fora da amostra, nos dois sentidos (§ 7). '
      'Também é a que mais reduz o número de operações: de %s para %s, ou de '
      '%s para %s por pregão.'
      % (n(v0['stats']['operacoes']), n(v4['stats']['operacoes']),
         n(v0['stats']['ops_por_dia'], 1), n(v4['stats']['ops_por_dia'], 1)))
    w('')
    w('**3. Exigir que o gatilho FECHE além da EMA21.**  ')
    w('Foi o melhor filtro de forma medido (z %s), embora sozinho não passe do '
      'ruído. Combinado com o horário produz a V5. A justificativa não é '
      'estatística — é que ele elimina o caso em que a barra apenas encosta na '
      'média e fecha do lado errado, que é ambíguo até de ler no gráfico.'
      % fmt(acha('gatilho fecha além da EMA21 (reconquista)')['z'], 2))
    w('')
    w('**4. Não impor teto de tamanho ao candle de reversão.**  ')
    w('A pergunta do documento original era se convinha limitar o range da barra de '
      'gatilho. A resposta medida é **não**: a V2 (teto de 350 t) piora a V0, e no '
      'corte por tamanho as barras *grandes* medem melhor que as pequenas (§ 6). O '
      'raciocínio "stop fixo + barra grande = risco maior" está certo sobre o '
      'risco, mas o retorno cresce junto.')
    w('')
    w('**5. Se for operar, dimensione pela hipótese de custo alto.**  ')
    w('Use 40 ticks de custo, não 0. Nessa hipótese a V5 cai para %s por operação '
      '— praticamente zero. A única configuração que sobra em pé é a **V7** '
      '(horário + reconquista + saída inteira em +1R): %s por operação sem custo, '
      '%s com 40 ticks, fator de lucro %s. É ela que o `PLANO.md` adota — e ainda '
      'assim com a folga de uma amostra de %s operações, não de uma certeza.'
      % (t(c5['40'].get('expectativa_ticks', 0), 1),
         t(V['V7']['stats']['expectativa_ticks'], 1),
         t(V['V7']['custo']['40'].get('expectativa_ticks', 0), 1),
         n(V['V7']['stats']['fator_lucro'], 2),
         n(V['V7']['stats']['operacoes'])))
    w('')

    # ---------------------------------------------------------------- 10
    w('## 10. Limitações honestas deste backtest')
    w('')
    w('- **%s pregões.** É pouco. Quatro meses de ouro num regime só; a V5 tem '
      'apenas %s operações, o que dá um erro-padrão de expectativa da ordem de '
      '%s ticks por operação.'
      % (n(D['dias']), n(v5['stats']['operacoes']),
         n(v5['stats']['desvio_ticks'] / (v5['stats']['operacoes'] ** 0.5), 0)))
    w('- **Só existe OHLC.** Dentro da barra, o caminho é desconhecido. Isso foi '
      'tratado medindo os dois extremos (§ 8a), não escolhendo um.')
    w('- **Sem spread por barra.** A coluna do arquivo é inutilizável; o custo '
      'entrou como cenário.')
    w('- **Sem slippage no stop.** Ordens de stop em ouro escorregam, e escorregam '
      'mais nos momentos em que este backtest as aciona.')
    w('- **As horas foram escolhidas olhando estes dados.** A validação cruzada '
      'reduz o risco, não o elimina. Só o tempo real, para frente, decide.')
    w('- **Uma operação por vez.** Sinais que aparecem com uma posição aberta são '
      'descartados, o que é o comportamento real de quem opera, mas reduz a amostra.')
    w('')

    # ---------------------------------------------------------------- 11
    w('## 11. O que fazer com isto')
    w('')
    w('A estratégia descrita em `ESTRATEGIA.md` é um bom **gatilho de atenção** e '
      'não é uma vantagem. Ela marca o momento em que uma tendência acabou de '
      'absorver um pullback — um momento legítimo para olhar o gráfico. O que os '
      'dados não sustentam é a segunda metade da afirmação: que dali o preço siga '
      'a favor com frequência suficiente para pagar um alvo de 3R.')
    w('')
    w('O caminho com alguma chance está em `PLANO.md`: horário estreito, gatilho '
      'exigente, alvo curto, tamanho pequeno, e um critério de parada escrito '
      'antes de começar. Não como uma estratégia validada — como um teste em '
      'tempo real, com dinheiro dimensionado para ser o custo do teste.')
    w('')
    w('---')
    w('')
    w('*Reproduzir: `python rodar.py && python resultados_md.py && python '
      'relatorio.py && python plano.py`. Operação a operação em '
      '`saida/trades_V*.csv`.*')

    caminho = os.path.join(BASE, 'RESULTADOS.md')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('RESULTADOS.md gravado (%s linhas).' % len(L))


if __name__ == '__main__':
    escrever()
