# Selected-model history missingness

[Protocol and diagnostic definitions](SELECTED_HISTORY_PROTOCOL.md). All 5,280 original simulation keys and feasible mask hashes are reused; historical labels and 739 later test meals remain fixed for 44 participants. CGMacros-derived results: CC BY-NC-SA 4.0.

Positive remaining benefit favors personalization over the selected pooled model. Positive cost means worse than clean selected-model personalization. Availability cost includes the change in shrinkage caused by dropping unusable meals. The retained-feature cost is evaluated on the same retained meals. These costs sum exactly but are order-dependent diagnostics, not causal attribution.

| Requested | Pattern | Exposure | Usable meals | Selected personalized MAE | Remaining benefit [95% CI] | Total cost [95% CI] |
|---|---|---:|---:|---:|---|---|
| 0% | random | 0.00% | 10.00 | 19.0754 | 2.4452 [1.2234, 3.7664] | 0.0000 [0.0000, 0.0000] |
| 0% | block | 0.00% | 10.00 | 19.0754 | 2.4452 [1.2234, 3.7664] | 0.0000 [0.0000, 0.0000] |
| 0% | night | 0.00% | 10.00 | 19.0754 | 2.4452 [1.2234, 3.7664] | 0.0000 [0.0000, 0.0000] |
| 5% | random | 4.94% | 10.00 | 19.0767 | 2.4439 [1.2205, 3.7658] | 0.0012 [-0.0011, 0.0036] |
| 5% | block | 4.32% | 9.58 | 19.1277 | 2.3929 [1.1813, 3.7059] | 0.0522 [0.0093, 0.0975] |
| 5% | night | 0.57% | 10.00 | 19.0753 | 2.4453 [1.2236, 3.7669] | -0.0001 [-0.0006, 0.0003] |
| 10% | random | 9.81% | 10.00 | 19.0748 | 2.4458 [1.2214, 3.7669] | -0.0007 [-0.0029, 0.0016] |
| 10% | block | 8.89% | 9.12 | 19.2126 | 2.3080 [1.1414, 3.5809] | 0.1372 [0.0331, 0.2507] |
| 10% | night | 1.17% | 9.95 | 19.1026 | 2.4180 [1.1951, 3.7344] | 0.0272 [0.0012, 0.0666] |
| 20% | random | 20.10% | 10.00 | 19.0723 | 2.4483 [1.2220, 3.7699] | -0.0031 [-0.0091, 0.0030] |
| 20% | block | 17.57% | 8.25 | 19.2703 | 2.2503 [1.1050, 3.5069] | 0.1948 [0.0319, 0.3643] |
| 20% | night | 2.29% | 9.77 | 19.1944 | 2.3262 [1.1111, 3.6394] | 0.1189 [0.0057, 0.2879] |

## Decomposition and paired comparison with v1

| Requested | Pattern | Availability cost [95% CI] | Retained-feature cost [95% CI] | v1 minus selected degraded MAE [95% CI] |
|---|---|---|---|---|
| 0% | random | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.6711 [0.8197, 2.5659] |
| 0% | block | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.6711 [0.8197, 2.5659] |
| 0% | night | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.6711 [0.8197, 2.5659] |
| 5% | random | 0.0000 [0.0000, 0.0000] | 0.0012 [-0.0011, 0.0036] | 1.6700 [0.8194, 2.5637] |
| 5% | block | 0.0550 [0.0124, 0.0992] | -0.0028 [-0.0076, 0.0004] | 1.6734 [0.8224, 2.5635] |
| 5% | night | 0.0000 [0.0000, 0.0000] | -0.0001 [-0.0006, 0.0003] | 1.6713 [0.8195, 2.5660] |
| 10% | random | 0.0000 [0.0000, 0.0000] | -0.0007 [-0.0029, 0.0016] | 1.6716 [0.8203, 2.5660] |
| 10% | block | 0.1395 [0.0354, 0.2527] | -0.0023 [-0.0079, 0.0010] | 1.6695 [0.8310, 2.5444] |
| 10% | night | 0.0272 [0.0015, 0.0659] | -0.0001 [-0.0011, 0.0010] | 1.6566 [0.8020, 2.5558] |
| 20% | random | 0.0000 [0.0000, 0.0000] | -0.0031 [-0.0091, 0.0030] | 1.6739 [0.8223, 2.5666] |
| 20% | block | 0.1930 [0.0307, 0.3612] | 0.0019 [-0.0009, 0.0056] | 1.6811 [0.8539, 2.5518] |
| 20% | night | 0.1192 [0.0077, 0.2872] | -0.0003 [-0.0070, 0.0072] | 1.5955 [0.7180, 2.5084] |

## Limits and reproduction

Intervals are pointwise participant-bootstrap percentiles conditional on fitted folds, not multiplicity-adjusted or full-refitting intervals. Night exposure is low because masks rarely intersect these premeal features. This does not demonstrate general night robustness. Historical labels remain clean; state B uses clean retained features as a diagnostic counterfactual. Published interpolation and unknown meal-metadata timing prevent prospective forecasting claims.

Run `python reproduce.py selected-history` after `patterns`, `history` and `compare`. Upstream hashes are validated; local exact-mask checks and all per-run metrics are in `outputs/selected_history/runs.json`. [Aggregate results and provenance](selected-history-results.json).
