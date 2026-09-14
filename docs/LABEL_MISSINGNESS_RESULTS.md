# Historical input and label missingness

[Protocol](LABEL_MISSINGNESS_PROTOCOL.md). Exploratory retrospective experiment; CGMacros-derived summaries are CC BY-NC-SA 4.0. The released v0.2 archive is unchanged.

44 people; 739 fixed later test meals; 5,280 masks shared across three arms and three coverage thresholds (47,520 evaluations, not independent samples). The mask timeline now includes the final historical outcome window and differs from earlier input-only experiments.

Primary label coverage: at least 15/30 premeal minutes and 84/120 postmeal minutes. Labels recompute both retained-window means. Label-only keeps features clean but allows the target baseline to change; joint degradation changes both. All prediction errors and label errors below are mg/dL. Positive benefit favors personalization; positive cost means worse than clean-history personalization.

## Primary 70% postmeal coverage results

| Requested | Pattern | Arm | Usable history | Prediction MAE | Benefit [95% CI] | Cost [95% CI] |
|---|---|---|---:|---:|---|---|
| 0% | block | input_only | 10.00 | 19.075 | 2.445 [1.228, 3.808] | 0.000 [0.000, 0.000] |
| 0% | block | joint | 10.00 | 19.075 | 2.445 [1.228, 3.808] | 0.000 [0.000, 0.000] |
| 0% | block | label_only | 10.00 | 19.075 | 2.445 [1.228, 3.808] | 0.000 [0.000, 0.000] |
| 0% | night | input_only | 10.00 | 19.075 | 2.445 [1.228, 3.808] | 0.000 [0.000, 0.000] |
| 0% | night | joint | 10.00 | 19.075 | 2.445 [1.228, 3.808] | 0.000 [0.000, 0.000] |
| 0% | night | label_only | 10.00 | 19.075 | 2.445 [1.228, 3.808] | 0.000 [0.000, 0.000] |
| 0% | random | input_only | 10.00 | 19.075 | 2.445 [1.228, 3.808] | 0.000 [0.000, 0.000] |
| 0% | random | joint | 10.00 | 19.075 | 2.445 [1.228, 3.808] | 0.000 [0.000, 0.000] |
| 0% | random | label_only | 10.00 | 19.075 | 2.445 [1.228, 3.808] | 0.000 [0.000, 0.000] |
| 5% | block | input_only | 9.53 | 19.129 | 2.391 [1.190, 3.746] | 0.054 [-0.002, 0.119] |
| 5% | block | joint | 9.33 | 19.155 | 2.365 [1.165, 3.710] | 0.080 [0.002, 0.170] |
| 5% | block | label_only | 9.33 | 19.155 | 2.366 [1.166, 3.711] | 0.079 [0.001, 0.169] |
| 5% | night | input_only | 10.00 | 19.076 | 2.445 [1.227, 3.808] | 0.001 [-0.000, 0.002] |
| 5% | night | joint | 10.00 | 19.075 | 2.446 [1.227, 3.811] | -0.001 [-0.007, 0.006] |
| 5% | night | label_only | 10.00 | 19.074 | 2.446 [1.228, 3.812] | -0.001 [-0.008, 0.005] |
| 5% | random | input_only | 10.00 | 19.074 | 2.446 [1.228, 3.809] | -0.001 [-0.004, 0.001] |
| 5% | random | joint | 10.00 | 19.073 | 2.448 [1.231, 3.813] | -0.003 [-0.007, 0.002] |
| 5% | random | label_only | 10.00 | 19.074 | 2.447 [1.231, 3.811] | -0.002 [-0.005, 0.002] |
| 10% | block | input_only | 9.14 | 19.205 | 2.316 [1.135, 3.641] | 0.130 [0.034, 0.236] |
| 10% | block | joint | 8.96 | 19.227 | 2.294 [1.116, 3.620] | 0.151 [0.047, 0.267] |
| 10% | block | label_only | 8.96 | 19.226 | 2.294 [1.116, 3.620] | 0.151 [0.046, 0.267] |
| 10% | night | input_only | 9.98 | 19.088 | 2.433 [1.216, 3.793] | 0.012 [-0.000, 0.031] |
| 10% | night | joint | 9.89 | 19.125 | 2.395 [1.194, 3.727] | 0.050 [0.003, 0.111] |
| 10% | night | label_only | 9.89 | 19.125 | 2.396 [1.195, 3.729] | 0.049 [0.004, 0.110] |
| 10% | random | input_only | 10.00 | 19.075 | 2.446 [1.227, 3.812] | -0.001 [-0.003, 0.002] |
| 10% | random | joint | 10.00 | 19.078 | 2.442 [1.224, 3.809] | 0.003 [-0.006, 0.011] |
| 10% | random | label_only | 10.00 | 19.079 | 2.442 [1.224, 3.808] | 0.004 [-0.005, 0.011] |
| 20% | block | input_only | 8.17 | 19.306 | 2.214 [1.061, 3.503] | 0.231 [0.092, 0.381] |
| 20% | block | joint | 7.97 | 19.326 | 2.194 [1.055, 3.473] | 0.251 [0.102, 0.413] |
| 20% | block | label_only | 7.97 | 19.327 | 2.194 [1.055, 3.473] | 0.251 [0.103, 0.413] |
| 20% | night | input_only | Incomplete | — | — | — |
| 20% | night | joint | Incomplete | — | — | — |
| 20% | night | label_only | Incomplete | — | — | — |
| 20% | random | input_only | 10.00 | 19.072 | 2.448 [1.232, 3.814] | -0.003 [-0.007, 0.001] |
| 20% | random | joint | 9.96 | 19.085 | 2.436 [1.217, 3.799] | 0.009 [-0.004, 0.023] |
| 20% | random | label_only | 9.96 | 19.087 | 2.433 [1.215, 3.794] | 0.012 [-0.001, 0.026] |

## Label errors and threshold sensitivity at 20% timeline missingness

Label errors are conditional on labels passing coverage; stricter selection may lower apparent label error while losing useful history. Counts include repeated masks/seeds, not unique meals. Label diagnostics are identical across arms; only one copy is shown. Complete per-person summaries and other budgets are in the JSON.

| Required post coverage | Pattern | Pre / post exposure | Label-evaluable people | Valid labels / 4400 | Label bias | Label MAE | Max absolute label error | Joint usable meals | Joint prediction MAE | Joint benefit [95% CI] |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 50% | block | 18.3% / 18.1% | 44 | 3529 | -0.050 | 0.079 | 40.355 | 8.02 | 19.320 | 2.201 [1.054, 3.488] |
| 50% | random | 19.9% / 20.0% | 44 | 4400 | -0.006 | 0.954 | 10.496 | 10.00 | 19.080 | 2.441 [1.220, 3.805] |
| 70% | block | 18.3% / 18.1% | 44 | 3509 | -0.018 | 0.030 | 16.743 | 7.97 | 19.326 | 2.194 [1.055, 3.473] |
| 70% | random | 19.9% / 20.0% | 44 | 4383 | -0.006 | 0.954 | 10.496 | 9.96 | 19.085 | 2.436 [1.217, 3.799] |
| 90% | block | 18.3% / 18.1% | 44 | 3492 | 0.002 | 0.008 | 4.424 | 7.94 | 19.340 | 2.181 [1.038, 3.461] |
| 90% | random | 19.9% / 20.0% | 6 | 7 | -0.033 | 0.608 | 1.231 | 0.02 | 21.480 | 0.040 [0.006, 0.091] |

## Paired arm differences: primary threshold, 20% missingness

| Pattern | Joint minus input-only MAE [95% CI] | Joint minus label-only MAE [95% CI] |
|---|---|---|
| block | 0.020 [-0.014, 0.054] | -0.001 [-0.002, 0.000] |
| random | 0.012 [-0.001, 0.026] | -0.003 [-0.007, 0.001] |

## Limits and reproduction

Do not compare these aggregate values directly with old masks to estimate a label effect: the timeline changed. Within this experiment all arms use the same masks and tests. Costs combine measurement damage and adaptation availability. Intervals are pointwise and conditional on fitted folds. Source interpolation, unknown meal metadata timing, small sample and complete-case selection remain limitations. No clinical or prospective forecasting claim is supported.

Run `python reproduce.py labels` after `patterns` and `compare`. Local label diagnostics (including unavailable labels as null), per-run offsets, metrics and mask hashes are in `outputs/label_missingness/`. [Aggregate results and provenance](label-missingness-results.json). The stable v0.2 `full` workflow remains unchanged; this is an additional study.
