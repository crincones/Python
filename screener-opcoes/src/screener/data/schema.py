"""Colunas dos artefatos em disco (snake_case). Fonte de verdade para nomes e significados.

Snapshot = pasta data/snapshots/AAAAMMDD_HHMMSS/ contendo:
  underlyings.parquet  um registro por ativo-objeto com opções listadas
  options.parquet      um registro por série coletada (só ativos que passaram no filtro)
  bars.parquet         barras D1/H4 dos ativos aprovados (sinal de viés)
  meta.json            horário, terminal, contagens e configuração usada
Timestamps sempre com timezone America/Sao_Paulo. Campos que o MT5 entrega zerados viram NaN.
"""

from __future__ import annotations

UNDERLYINGS_TABLE = "underlyings"
OPTIONS_TABLE = "options"
BARS_TABLE = "bars"
BIAS_TABLE = "bias"
META_FILE = "meta.json"

UNDERLYINGS_COLUMNS: dict[str, str] = {
    "snapshot_time": "Início da coleta",
    "underlying": "Código do ativo-objeto (campo basis das opções)",
    "listed_series": "Séries de opção listadas no servidor (todas as datas e strikes)",
    "bid": "Melhor oferta de compra do ativo no início da coleta",
    "ask": "Melhor oferta de venda do ativo no início da coleta",
    "last": "Último negócio do ativo no início da coleta",
    "price": "Preço de referência: last, ou mid se last ausente",
    "quote_time": "Horário da última cotação do ativo",
    "avg_daily_turnover_brl": "Média de real_volume × close no D1 dos pregões da janela",
    "sessions_expected": "Pregões na janela de lookback",
    "sessions_used": "Pregões encontrados no histórico D1",
    "history_complete": "Todos os pregões da janela presentes no D1",
    "liquidity_rank": "Posição por volume financeiro entre os elegíveis (1 = mais líquido)",
    "passed_filter": "Passou no filtro inicial e teve séries coletadas",
    "reject_reason": "Motivo da exclusão (nulo se passou)",
    "candidate_series": "Séries dentro da janela de DTE e da faixa de strike (coletadas)",
}

OPTIONS_COLUMNS: dict[str, str] = {
    "snapshot_time": "Início da coleta",
    "read_time": "Momento em que a série foi lida no terminal",
    "symbol": "Ticker da opção",
    "underlying": "Ativo-objeto (basis)",
    "description": "Descrição do servidor",
    "option_type": "call ou put (option_right)",
    "exercise_style": "american ou european (option_mode)",
    "strike": "Preço de exercício atual (option_strike, relido a cada snapshot)",
    "expiration_time": "Fim do dia de vencimento (expiration_time)",
    "expiration_date": "Data de vencimento (lida via DuckDB como datetime64 sem timezone)",
    "dte_business_days": "Pregões após a data do snapshot até o vencimento, inclusive",
    "dte_calendar_days": "Dias corridos da data do snapshot até o vencimento",
    "bid": "Melhor oferta de compra (NaN se zero)",
    "ask": "Melhor oferta de venda (NaN se zero)",
    "last": "Último negócio (NaN se zero)",
    "mid": "(bid + ask) / 2; NaN se bid ou ask ausente",
    "spread_pct_mid": "(ask − bid) / mid",
    "quote_time": "Horário da última cotação da série",
    "quote_age_seconds": (
        "Segundos entre quote_time e o tick mais recente lido no mesmo lote (relógio do servidor)"
    ),
    "deals": "Número de negócios na sessão (session_deals)",
    "volume_qty": "Quantidade de opções negociada na sessão (session_volume)",
    "vwap": "Preço médio ponderado da sessão (session_aw; NaN se zero)",
    "turnover_brl": "Volume financeiro = volume_qty × vwap × contract_size",
    "prev_close": "Fechamento anterior (session_close; NaN se zero)",
    "open_interest": "Contratos em aberto (session_interest; NaN se zero — ausente na XP)",
    "contract_size": "trade_contract_size",
    "tick_size": "trade_tick_size",
    "underlying_bid": "Bid do ativo-objeto no momento da leitura da série",
    "underlying_ask": "Ask do ativo-objeto no momento da leitura da série",
    "underlying_last": "Último do ativo-objeto no momento da leitura da série",
    "underlying_price": "last do ativo-objeto, ou mid se last ausente",
}

SERIES_TABLE = "series"
SPREADS_TABLE = "spreads"
ANALYSIS_META_FILE = "analysis_meta.json"

# series.parquet = OPTIONS_COLUMNS + as colunas abaixo (gerado por `screener analyze`).
SERIES_EXTRA_COLUMNS: dict[str, str] = {
    "t_years": "Prazo em anos de dias úteis (dte_business_days / 252)",
    "rate": "Taxa livre de risco contínua = ln(1 + CDI anual)",
    "iv": "Volatilidade implícita sobre o mid (NaN se iv_status != ok)",
    "iv_status": "Valor de pricing.implied_vol.IVStatus (ok = IV válida)",
    "liquidity_ok": "Passou em todos os mínimos de liquidez da série",
    "liquidity_reject_reason": "Primeiro mínimo reprovado (nulo se aprovada)",
    "liquidity_score": "0–1: percentis ponderados de spread, volume, negócios (e OI) no ativo",
}

SPREADS_COLUMNS: dict[str, str] = {
    "snapshot_time": "Início da coleta do snapshot",
    "underlying": "Ativo-objeto",
    "strategy": "bull_call (trava de alta com calls) ou bear_put (trava de baixa com puts)",
    "direction": "alta ou baixa",
    "option_type": "call ou put",
    "expiration_date": "Vencimento",
    "dte_business_days": "Pregões até o vencimento",
    "t_years": "Prazo em anos de dias úteis",
    "rate": "Taxa contínua usada",
    "spot": "Preço do ativo-objeto (lido junto com a perna comprada)",
    "long_symbol": "Ticker da perna comprada",
    "short_symbol": "Ticker da perna vendida",
    "long_strike": "Strike comprado (K_L)",
    "short_strike": "Strike vendido (K_S)",
    "long_exercise_style": "Estilo da comprada",
    "short_exercise_style": "Estilo da vendida",
    "long_bid": "Bid da comprada",
    "long_ask": "Ask da comprada",
    "long_mid": "Mid da comprada",
    "short_bid": "Bid da vendida",
    "short_ask": "Ask da vendida",
    "short_mid": "Mid da vendida",
    "long_iv": "IV da comprada",
    "short_iv": "IV da vendida",
    "atm_iv": "IV ATM do vencimento (usada em σ e POP)",
    "width": "W = |K_S − K_L|",
    "debit": "Débito realista = ask(L) − bid(S), por opção",
    "debit_mid": "Débito mid = mid(L) − mid(S), por opção (informativo)",
    "execution_cost": "Débito realista − débito mid, por opção (custo de cruzar o book)",
    "execution_cost_pct_width": "Custo de execução / W",
    "max_gain": "W − débito realista, por opção",
    "max_loss": "Débito realista, por opção",
    "reward_risk": "Ganho máximo / débito realista",
    "debit_to_width": "Débito realista / W",
    "breakeven": "Alta: K_L + débito; baixa: K_L − débito",
    "breakeven_distance_pct": "Movimento até o breakeven em fração do spot (+ = a favor)",
    "breakeven_distance_sigma": "Movimento até o breakeven / (atm_iv × √T × spot)",
    "pop": "Prob. neutra ao risco de terminar além do breakeven (BS europeu, IV ATM)",
    "debit_per_lot": "Débito realista × lote",
    "debit_mid_per_lot": "Débito mid × lote",
    "max_gain_per_lot": "Ganho máximo × lote",
    "max_loss_per_lot": "Perda máxima × lote",
    "long_liquidity_score": "Score de liquidez da comprada",
    "short_liquidity_score": "Score de liquidez da vendida",
    "liquidity_score": "Pior score entre as pernas",
    "worst_spread_pct_mid": "Maior spread bid/ask % entre as pernas",
    "min_turnover_brl": "Menor volume financeiro entre as pernas",
    "min_deals": "Menor número de negócios entre as pernas",
    "short_intrinsic": "Valor intrínseco da vendida",
    "short_extrinsic": "Valor extrínseco da vendida = mid − intrínseco",
    "early_exercise_alert": "Alerta de exercício antecipado (não remove do ranking)",
    "early_exercise_reason": "Motivo do alerta",
}

BARS_COLUMNS: dict[str, str] = {
    "underlying": "Ativo-objeto",
    "timeframe": "d1 ou h4",
    "time": "Abertura da barra (America/Sao_Paulo)",
    "open": "Abertura",
    "high": "Máxima",
    "low": "Mínima",
    "close": "Fechamento (última barra pode estar em formação)",
    "tick_volume": "Número de ticks",
    "real_volume": "Quantidade negociada",
}

# bias.parquet (gerado por `screener analyze`): uma linha por ativo. Colunas <tf>_* existem para
# cada timeframe configurado em signals.timeframes (ex.: d1_trend, h4_ema_slow).
BIAS_COLUMNS: dict[str, str] = {
    "underlying": "Ativo-objeto",
    "auto_bias": "Viés do sinal automático (alta/baixa/neutro; nulo sem barras ou desabilitado)",
    "manual_bias": "Viés informado no YAML (nulo se ausente)",
    "bias": "Viés final usado no ranking",
    "bias_source": "manual, automático ou sem sinal",
}
BIAS_TIMEFRAME_FIELDS = ["trend", "close", "ema_fast", "ema_slow", "bars"]

SCORE_COLUMNS: dict[str, str] = {
    "in_pop_band": "POP dentro de [scoring.pop_min, scoring.pop_max]",
    "pct_execution_cost": "Percentil do custo de execução % largura (1 = mais barato)",
    "pct_liquidity": "Percentil da liquidez (1 = mais líquida)",
    "pct_reward_risk": "Percentil do R/R (1 = maior)",
    "score": "0–100: soma ponderada dos percentis (NaN fora da faixa de POP)",
    "bias": "Viés final do ativo",
    "bias_source": "Origem do viés",
    "bias_match": "Direção da trava igual ao viés",
    "ranked": "Entra no ranking (faixa de POP e viés)",
    "rank": "Posição no ranking da estratégia (1 = melhor)",
}
SPREADS_COLUMNS.update(SCORE_COLUMNS)
