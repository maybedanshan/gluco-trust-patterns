# Selected-model history missingness and sequential decomposition

Exploratory extension specified after both v1 missingness and inner-selected model comparison results were inspected. Not preregistered. It does not overwrite either source experiment.

Reuse the original ten-meal history, fixed later test meal IDs, 0/5/10/20% timeline budgets, random/block/night patterns, and ten simulation seeds. Regenerate each v1 mask with the original key and compare its SHA-256 against the stored v1 run. Verify source and model-selection provenance before fitting. Refit each participant's global model using the stored inner-selected penalty and other participants only. Do not tune again on missingness outcomes. Historical labels and all later test inputs/outcomes remain complete.

For each mask and participant, evaluate three adaptation states using the same model and residual-shrinkage rule:

1. A: all ten original clean historical meals.
2. B: only the meals that retain at least 15/30 premeal minutes after masking, but use their original clean features. This is a diagnostic counterfactual, not an operational recovery method.
3. C: the same retained meal IDs as B, using degraded premeal features.

Report availability cost = MAE(B) − MAE(A), retained-feature cost = MAE(C) − MAE(B), total cost = MAE(C) − MAE(A). The first cost includes the changed shrinkage denominator caused by fewer usable history meals. These costs sum exactly under this ordering; this is an order-dependent diagnostic decomposition, not unique causal attribution. Zero usable history falls back to pooled prediction in B and C. Participants and later test meals never disappear.

Report remaining benefit = pooled MAE − MAE(C). Compare selected and v1 models under each identical mask using v1 degraded MAE − selected degraded MAE (positive favors selected). Retain actual premeal exposure and usable-meal counts; night budget feasibility must match v1. Suppress incomplete configuration summaries instead of changing the cohort.

Average simulation seeds within participant, then people equally. Use 10,000 participant bootstrap draws, seed 20260917, 95% pointwise percentile intervals, sharing draws across complete configurations and contrasts. No multiplicity or full refitting uncertainty is included. Preserve all original preprocessing, retrospective and selection limitations. In particular, tiny night effects can reflect low overlap with premeal inputs, and these data do not establish prospective forecasting performance.
