# Model comparison with inner participant validation

[Protocol](MODEL_COMPARISON_PROTOCOL.md). Exploratory retrospective extension after inspecting v1; not external validation or a confirmatory study. Source-derived results: CC BY-NC-SA 4.0.

Penalties are selected using only other participants in five inner folds. All centering/scaling is fitted inside each training fold. History means and personal residual offsets use only early labels. Outer test meals never enter selection. Errors are participant-macro MAE in mg/dL.

| Setting | History meals | People | Test meals | Mean baseline | Fixed ridge (10) | Selected ridge | Personalized selected ridge | History-only mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| unseen | 0 | 44 | 1179 | 24.247 | 23.887 | 22.305 | N/A | N/A |
| history | 3 | 44 | 739 | 22.809 | 22.519 | 21.521 | 20.815 | 25.552 |
| history | 5 | 44 | 739 | 22.809 | 22.519 | 21.521 | 19.699 | 22.602 |
| history | 10 | 44 | 739 | 22.809 | 22.519 | 21.521 | 19.075 | 21.651 |

## Paired improvements

Positive values favor the second model in each comparison. Intervals are 95% pointwise participant-bootstrap intervals conditional on fitted folds; no familywise or full-refitting uncertainty is claimed.

| Setting | History meals | First minus second | Mean improvement (mg/dL) | 95% CI |
|---|---:|---|---:|---|
| unseen | 0 | baseline minus selected_pooled | 1.942 | [1.037, 2.858] |
| unseen | 0 | fixed_pooled minus selected_pooled | 1.581 | [0.769, 2.401] |
| history | 3 | baseline minus selected_pooled | 1.289 | [0.402, 2.211] |
| history | 3 | fixed_pooled minus selected_pooled | 0.999 | [0.206, 1.828] |
| history | 3 | selected_pooled minus personalized | 0.705 | [-0.301, 1.733] |
| history | 3 | history_mean minus personalized | 4.736 | [2.406, 7.278] |
| history | 5 | baseline minus selected_pooled | 1.289 | [0.402, 2.211] |
| history | 5 | fixed_pooled minus selected_pooled | 0.999 | [0.206, 1.828] |
| history | 5 | selected_pooled minus personalized | 1.822 | [0.754, 2.982] |
| history | 5 | history_mean minus personalized | 2.903 | [1.407, 4.467] |
| history | 10 | baseline minus selected_pooled | 1.289 | [0.402, 2.211] |
| history | 10 | fixed_pooled minus selected_pooled | 0.999 | [0.206, 1.828] |
| history | 10 | selected_pooled minus personalized | 2.445 | [1.210, 3.792] |
| history | 10 | history_mean minus personalized | 2.575 | [1.414, 3.714] |

## Selection and interpretation

Selected penalties across outer folds: {"0.1": 42, "10.0": 1, "100.0": 1}.

Unseen and history settings use different meal sets; compare models within a setting. History budgets share identical later meals. The history-only model tests whether early labels alone explain the benefit; do not attribute all gains to nutrition features or a sophisticated personal model.

Published interpolation and unknown nutrition-record availability prevent a prospective forecasting claim. Complete-case selection, small cohort and overlapping training folds limit generalization. Selection targets unseen-person MAE, not personalized later-meal MAE. The first missingness report still uses the fixed-penalty v1 model; its effects cannot be transferred to this selected model without another experiment.

## Reproduction

`python reproduce.py compare` after `python reproduce.py patterns`. NumPy is required. Exact original splits are reused; local candidate scores and inner-fold participant IDs are in `outputs/model_comparison/selection.json`, and per-meal predictions in `outputs/model_comparison/predictions.json`. [Aggregate results and hashes](model-comparison-results.json) are public; meal-level files stay local.
