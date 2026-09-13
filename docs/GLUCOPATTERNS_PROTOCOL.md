# GlucoPatterns protocol 1.0

Status: fixed before the first prediction run in this project; not externally preregistered. This is an exploratory retrospective benchmark on CGMacros 1.0.0. The existing meal-readiness audit was inspected before these rules were chosen.

## Question and measurement

Can a small amount of a participant's earlier labeled meal history improve later meal-response prediction over a pooled model trained on other participants?

Primary device: Dexcom released glucose values. Outcome (mg/dL): mean glucose over [0,120) minutes after the meal minus mean glucose over [-30,0). Require all 151 minute-grid timestamps from -30 through +120 on both devices, consistent with the earlier audit; the terminal value closes the support interval and is not averaged into the outcome. With complete one-minute support these means are time weighted. No additional interpolation is performed. Libre outcome modeling is deferred.

CGMacros published minute-grid curves contain interpolation features. Even premeal released values may use future sensor information in the source preprocessing; this cannot be audited from these exports alone. This experiment is therefore not a validated real-time forecasting system. The prediction-time assumption is that recorded meal nutrition is known at meal start; its actual recording time is unavailable. Native-sample prospective validation remains necessary.

## Eligibility and audit

Use every recorded nonempty Meal Type event. Require finite nonnegative Calories, Carbs, Protein, Fat and Fiber. Do not rescale by Amount Consumed because whether nutrition already reflects consumption is unresolved. Require complete dual-device support. Exclude another recorded meal in (0,120] minutes afterward, or a previous recorded meal less than 150 minutes earlier. The latter prevents overlapping labeled/input windows and reduces prior-meal contamination; it cannot eliminate physiological carryover or unrecorded snacks. Meal types are audited, not used to select favorable outcomes. Missing/invalid nutrition is never replaced with zero.

Audit reasons are nonexclusive. Store event-level exclusions locally, and publish participant-level counts. Participants without sufficient eligible meals remain in the audit. All retained events are chronological.

## Features and models

Features: the five nutrition fields, premeal glucose mean, premeal change per minute (value at -1 minus value at -30, divided by 29), and sine/cosine of meal clock hour. No postmeal glucose or personal identifiers enter the feature matrix.

1. Baseline: mean training meal response, weighting participants equally.
2. Pooled: ridge regression with an intercept and training-only feature standardization. Minimize participant-balanced mean squared error plus 10 times the squared coefficient norm. Intercept is unpenalized. Lambda 10 is fixed, not tuned on outcomes.
3. Personalized: pooled prediction plus sum of early-history residuals divided by (history count + 5). This shrinks the participant offset toward zero; shrinkage 5 is fixed. Global model and normalization never fit the held-out participant.

The first personalized method is deliberately limited to an intercept correction. More flexible personal models require a separate protocol and validation design.

## Evaluation settings

**Unseen participant:** leave one participant out. Fit both global methods on all eligible meals from other participants, evaluate all eligible meals of the held-out person. Personalization has zero history and reduces exactly to the pooled model; no separate personalization advantage is claimed here. No hyperparameter selection is performed.

**Early-history participant:** reuse the same leave-person-out global models. Adapt using the first 3, 5 or 10 eligible labeled meals of the held-out person. All budgets are evaluated on the identical fixed test set after the first 10 eligible meals. Require at least three later test meals; the last adaptation outcome must end no later than the first test input window starts. No rolling updates. Neither later test outcomes nor unselected early-history labels enter adaptation. Entire subject identity is held out from global training in both settings.

The two settings have different evaluation populations and meal sets; their overall errors must not be interpreted as a direct improvement caused by history. Only the within-setting matched comparisons support that interpretation. Shifted calendar dates are not synchronized across participants.

## Reporting and reproducibility

Report participant-macro MAE in mg/dL, participant and meal counts, and participant paired MAE differences. For history settings, define improvement as pooled MAE minus personalized MAE (positive favors personalization). Use 10,000 paired participant bootstrap draws with seed 20260914, percentile 95% pointwise intervals. History budgets are correlated and exploratory; no multiplicity-adjusted or clinical claim. Reuse draws across budgets with the common cohort.

Record source-file, code and protocol hashes, local split manifests, training participant IDs and per-meal predictions. Publish aggregate results, not raw meal records or precise timestamps. Analyze all outcomes, including deterioration under personalization. Nutrition effects are predictive associations, not causal treatment effects.

No new data or tuned deep model is required for this first comparison. Residual uncertainty includes meal timing, food consumption, activity, medication, source interpolation and complete-case selection. Breakfast/lunch protocol design limits generalization to unconstrained meals.
