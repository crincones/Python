# 01 — Relatorio de validacao dos dados

- **n_rows**: `20000`
- **encoding**: `utf-8-sig`
- **source**: `C:\Users\Carlos\Documents\GitHub\Python\ohlc-renko\WINFUT\WINFUT_11R_AGB_AGS_BDURF_QT_TRD.csv`
- **file_was_reversed**: `True`
- **steps_forward_in_file**: `0`
- **steps_backward_in_file**: `19178`
- **date_min**: `2026-06-29 09:23:12.407000`
- **date_max**: `2026-08-14 18:21:24.449000`
- **n_days**: `35`
- **n_unparsed_dates**: `0`
- **n_duplicate_timestamps**: `1163`
- **n_distinct_timestamps**: `19178`
- **n_out_of_order_after_sort**: `0`
- **n_zero_delta_t**: `822`
## nulls_per_column

| chave | valor |
|---|---|
| `Date` | 0 |
| `Open` | 0 |
| `High` | 0 |
| `Low` | 0 |
| `Close` | 0 |
| `AggBuy` | 0 |
| `AggSell` | 0 |
| `Duration` | 0 |
| `Quantity` | 0 |
| `Trades` | 0 |

- **n_high_lt_low**: `0`
- **n_open_outside_hl**: `0`
- **n_close_outside_hl**: `0`
- **n_negative_agg_buy**: `0`
- **n_negative_agg_sell**: `0`
- **n_negative_duration**: `0`
- **n_negative_quantity**: `0`
- **n_negative_trades**: `0`
- **n_zero_range**: `0`
- **n_zero_body**: `0`
- **n_zero_duration**: `3607`
- **n_zero_agg_total**: `454`
- **n_zero_agg_buy**: `725`
- **n_zero_agg_sell**: `676`
- **n_zero_quantity**: `420`
- **n_zero_trades**: `420`
- **brick_size_nominal**: `50.0`
## body_abs_stats

| chave | valor |
|---|---|
| `count` | 20000 |
| `mean` | 50.0 |
| `std` | 0.0 |
| `min` | 50.0 |
| `p01` | 50.0 |
| `p05` | 50.0 |
| `p25` | 50.0 |
| `p50` | 50.0 |
| `p75` | 50.0 |
| `p95` | 50.0 |
| `p99` | 50.0 |
| `max` | 50.0 |

## range_stats

| chave | valor |
|---|---|
| `count` | 20000 |
| `mean` | 93.78075 |
| `std` | 33.1849701152431 |
| `min` | 50.0 |
| `p01` | 50.0 |
| `p05` | 50.0 |
| `p25` | 60.0 |
| `p50` | 95.0 |
| `p75` | 120.0 |
| `p95` | 145.0 |
| `p99` | 150.0 |
| `max` | 150.0 |

## body_abs_value_counts_top

| chave | valor |
|---|---|
| `50` | 20000 |

- **n_body_equal_brick**: `20000`
- **n_body_gt_brick**: `0`
- **n_body_lt_brick**: `0`
## open_vs_prev_close_value_counts_top

| chave | valor |
|---|---|
| `0.0` | 13604 |
| `50.0` | 3198 |
| `-50.0` | 3197 |

- **n_open_ne_prev_close**: `6395`
## delta_t_seconds_stats

| chave | valor |
|---|---|
| `count` | 19999 |
| `mean` | 200.34461933096657 |
| `std` | 4377.954666817449 |
| `min` | 0.0 |
| `p01` | 0.0 |
| `p05` | 0.002 |
| `p25` | 2.1505 |
| `p50` | 13.626 |
| `p75` | 51.3365 |
| `p95` | 271.37129999999996 |
| `p99` | 732.8599800000004 |
| `max` | 225867.358 |

- **n_intraday_gaps_gt_1h**: `0`
- **n_session_breaks**: `33`
## duration_stats

| chave | valor |
|---|---|
| `count` | 20000 |
| `mean` | 2341.74405 |
| `std` | 58026.990969004975 |
| `min` | 0.0 |
| `p01` | 0.0 |
| `p05` | 0.0 |
| `p25` | 33.0 |
| `p50` | 217.0 |
| `p75` | 850.0 |
| `p95` | 4483.0 |
| `p99` | 11933.169999999973 |
| `max` | 3752167.0 |

- **corr_duration_vs_delta_t**: `0.0009812187312684519`
- **n_rows_flagged_for_exclusion**: `0`
- **excluded_bar_indexes**: 0 itens (ver JSON)
- **detected_brick_size**: `50.0`
- **explicit_exclusions**: 1 itens (ver JSON)