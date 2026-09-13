# GlucoPatterns: first retrospective benchmark

Exploratory local results, not a validated prospective prediction system. [Fixed protocol](GLUCOPATTERNS_PROTOCOL.md); source-derived summaries: CC BY-NC-SA 4.0.

Recorded meals: 1706; eligible meals: 1179; eligible participants: 44. Reasons overlap, so exclusion columns are not additive. The earlier 1,385 candidate meals used a looser rule without the new prior-meal exclusion.

## Separate evaluation settings

Outcome: Dexcom released mean glucose during [0,120) minutes minus [-30,0) mean, in mg/dL. Macro MAE weights participants equally. Baseline and pooled training exclude the entire held-out participant. History budgets share the same later test meals, after the first 10 eligible meals. No rolling adaptation.

| Setting | History meals | Participants | Test meals | Baseline MAE | Pooled MAE | Personalized MAE | Pooled − personalized MAE, 95% pointwise CI |
|---|---:|---:|---:|---:|---:|---:|---|
| unseen | 0 | 44 | 1179 | 24.247 | 23.887 | N/A (equals pooled) | N/A |
| history | 3 | 44 | 739 | 22.809 | 22.519 | 22.315 | 0.205 [-0.749, 1.174] |
| history | 5 | 44 | 739 | 22.809 | 22.519 | 21.190 | 1.330 [0.344, 2.469] |
| history | 10 | 44 | 739 | 22.809 | 22.519 | 20.747 | 1.773 [0.601, 3.092] |

Positive paired improvement favors personalization; negative values favor pooled prediction. Confidence intervals resample participants, not meals. The unseen and history rows use different meals/populations and cannot be directly compared as a history effect. Leave-one-person-out training sets overlap; intervals summarize the observed participant error contrasts conditional on fitted folds, and do not include full model-refitting uncertainty.

## Participant meal audit

| Participant | Recorded | Eligible | Nutrition invalid | Dual window incomplete | Next meal within 120 min | Prior meal within 150 min |
|---|---:|---:|---:|---:|---:|---:|
| CGMacros-001 | 43 | 26 | 1 | 1 | 6 | 10 |
| CGMacros-002 | 37 | 20 | 0 | 1 | 9 | 10 |
| CGMacros-003 | 35 | 29 | 0 | 2 | 2 | 2 |
| CGMacros-004 | 62 | 24 | 0 | 2 | 23 | 26 |
| CGMacros-005 | 46 | 25 | 0 | 2 | 11 | 13 |
| CGMacros-006 | 38 | 28 | 0 | 0 | 5 | 6 |
| CGMacros-007 | 17 | 0 | 0 | 17 | 1 | 1 |
| CGMacros-008 | 30 | 27 | 0 | 3 | 0 | 0 |
| CGMacros-009 | 41 | 31 | 0 | 1 | 4 | 5 |
| CGMacros-010 | 45 | 28 | 0 | 0 | 8 | 10 |
| CGMacros-011 | 39 | 33 | 0 | 1 | 2 | 3 |
| CGMacros-012 | 33 | 31 | 0 | 1 | 0 | 1 |
| CGMacros-013 | 39 | 30 | 0 | 1 | 4 | 5 |
| CGMacros-014 | 40 | 29 | 0 | 1 | 5 | 6 |
| CGMacros-015 | 52 | 20 | 0 | 3 | 18 | 20 |
| CGMacros-016 | 28 | 27 | 0 | 1 | 0 | 0 |
| CGMacros-017 | 48 | 21 | 0 | 2 | 13 | 15 |
| CGMacros-018 | 39 | 26 | 0 | 1 | 6 | 6 |
| CGMacros-019 | 48 | 24 | 0 | 1 | 13 | 15 |
| CGMacros-020 | 41 | 29 | 0 | 1 | 6 | 6 |
| CGMacros-021 | 39 | 26 | 0 | 1 | 6 | 8 |
| CGMacros-022 | 42 | 31 | 0 | 1 | 5 | 5 |
| CGMacros-023 | 42 | 36 | 0 | 2 | 2 | 2 |
| CGMacros-026 | 36 | 25 | 0 | 4 | 4 | 4 |
| CGMacros-027 | 36 | 26 | 0 | 2 | 4 | 5 |
| CGMacros-028 | 34 | 29 | 0 | 2 | 1 | 2 |
| CGMacros-029 | 30 | 29 | 0 | 1 | 0 | 0 |
| CGMacros-030 | 28 | 27 | 0 | 1 | 0 | 0 |
| CGMacros-031 | 54 | 21 | 0 | 1 | 23 | 23 |
| CGMacros-032 | 20 | 20 | 0 | 0 | 0 | 0 |
| CGMacros-033 | 33 | 32 | 0 | 1 | 0 | 0 |
| CGMacros-034 | 49 | 22 | 0 | 0 | 14 | 17 |
| CGMacros-035 | 27 | 27 | 0 | 0 | 0 | 0 |
| CGMacros-036 | 30 | 29 | 0 | 1 | 0 | 0 |
| CGMacros-038 | 40 | 26 | 0 | 0 | 7 | 7 |
| CGMacros-039 | 34 | 29 | 0 | 1 | 2 | 2 |
| CGMacros-041 | 48 | 34 | 0 | 0 | 7 | 8 |
| CGMacros-042 | 22 | 20 | 0 | 0 | 1 | 1 |
| CGMacros-043 | 64 | 26 | 0 | 1 | 23 | 25 |
| CGMacros-044 | 43 | 25 | 0 | 2 | 8 | 10 |
| CGMacros-045 | 32 | 26 | 0 | 2 | 2 | 2 |
| CGMacros-046 | 29 | 21 | 0 | 2 | 3 | 3 |
| CGMacros-047 | 29 | 26 | 0 | 1 | 1 | 1 |
| CGMacros-048 | 36 | 31 | 0 | 1 | 2 | 3 |
| CGMacros-049 | 28 | 27 | 0 | 1 | 0 | 0 |

## Reproduction and limits

`python -m pip install -r requirements-patterns.txt`, then `python reproduce.py patterns` after downloading CGMacros. Local event exclusions, eligible features/targets, split manifests and per-meal predictions are under `outputs/glucopatterns/`. Aggregate results and provenance are in [glucopatterns-results.json](glucopatterns-results.json).

Published interpolation may introduce future information even into nominal premeal values; results are retrospective and cannot establish online forecasting performance. Meal nutrition availability at prediction time is assumed, not verified. Amount Consumed is not reapplied. Unrecorded snacks, medication, activity, prior-meal carryover, constrained breakfast/lunch design and complete-case selection remain limitations. No clinical utility or causal nutrition effect is inferred. No hyperparameters were selected on test outcomes. Libre and external meal-prediction validation remain future work.
