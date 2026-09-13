# Does personalization survive missing historical inputs?

[Protocol](HISTORY_MISSINGNESS_PROTOCOL.md). Exploratory input-only degradation; outcome labels and later evaluation inputs remain complete. Source-derived summaries: CC BY-NC-SA 4.0.

44 people, 739 fixed later test meals, 5280 simulation runs. Runs and seeds are not independent participants. Ten original history meals per person; fewer may remain usable after masking.

Masks apply to the whole early-history timeline. Exposure is the actual missing fraction inside the historical premeal feature windows; it need not equal the requested timeline budget. Positive benefit favors personalization over pooled prediction; positive cost means worse than clean-history personalization. Units of MAE, benefit and cost: mg/dL.

| Requested | Pattern | Premeal exposure | Usable history | Personalized MAE | Remaining benefit [95% CI] | Degradation cost [95% CI] |
|---|---|---:|---:|---:|---|---|
| 0% | random | 0.00% | 10.00 | 20.747 | 1.773 [0.601, 3.072] | 0.000 [0.000, 0.000] |
| 0% | block | 0.00% | 10.00 | 20.747 | 1.773 [0.601, 3.072] | 0.000 [0.000, 0.000] |
| 0% | night | 0.00% | 10.00 | 20.747 | 1.773 [0.601, 3.072] | 0.000 [0.000, 0.000] |
| 5% | random | 4.94% | 10.00 | 20.747 | 1.773 [0.601, 3.072] | 0.000 [-0.000, 0.000] |
| 5% | block | 4.32% | 9.58 | 20.801 | 1.718 [0.551, 3.015] | 0.055 [0.013, 0.095] |
| 5% | night | 0.57% | 10.00 | 20.747 | 1.773 [0.601, 3.072] | -0.000 [-0.000, 0.000] |
| 10% | random | 9.81% | 10.00 | 20.746 | 1.773 [0.601, 3.072] | -0.000 [-0.000, 0.000] |
| 10% | block | 8.89% | 9.12 | 20.882 | 1.637 [0.513, 2.874] | 0.136 [0.027, 0.255] |
| 10% | night | 1.17% | 9.95 | 20.759 | 1.760 [0.584, 3.061] | 0.013 [-0.001, 0.036] |
| 20% | random | 20.10% | 10.00 | 20.746 | 1.773 [0.601, 3.072] | -0.000 [-0.001, 0.000] |
| 20% | block | 17.57% | 8.25 | 20.951 | 1.568 [0.459, 2.796] | 0.205 [0.046, 0.367] |
| 20% | night | 2.29% | 9.77 | 20.790 | 1.730 [0.560, 3.035] | 0.043 [-0.003, 0.111] |

## Interpretation boundaries

A small or zero night effect can result from little overlap with the premeal windows that this model uses; it does not establish general robustness to nighttime data loss. The adaptation policy drops a meal when fewer than 15/30 premeal minutes remain, but never drops its participant or later test meals. Any incomplete night configuration is reported without an aggregate effect.

Intervals are pointwise participant-bootstrap percentiles after averaging seeds within person, conditional on the fitted folds and fixed simulations. No clinical, causal, multiplicity-adjusted or real-time forecasting claim is made. Published source interpolation remains a limitation. This experiment does not degrade historical labels or nutrition records.

## Reproduction

Run `python reproduce.py patterns` first, then `python reproduce.py history`. Local run metrics and deterministic mask hashes are in `outputs/history_missingness/runs.json`; [aggregate results and source/code hashes](history-missingness-results.json) are bundled. Exact masks regenerate from the fixed timeline, key, seed and code.
