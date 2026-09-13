# Research roadmap

This roadmap records planned work, not completed results. The project serves both an application portfolio and sustained, reproducible research. Version 0.1 findings remain descriptive.

## v0.1: reproducible reporting experiments — implemented locally

Compare random-point, continuous-block and night-window deletion under matched budgets. Preserve participants, paired device windows, seeds and actual time support. Release an offline explorer, source distribution, provenance and a limitations report. Hosted CI and a public GitHub release remain to be completed.

Evidence: [results](RESULTS.md), [release validation](RELEASE.md), [reproduction](REPRODUCIBILITY.md). No raw health records belong in the repository.

## Toward v0.2: participant-level uncertainty — implemented locally

The first-window paired extension is now available in [PAIRED_RESULTS.md](PAIRED_RESULTS.md), with 10,000 participant-bootstrap draws, fixed configuration and tests. This is not yet a published v0.2 release. Multi-window interval sensitivity remains future work.

Primary extension: estimate within-participant differences in seed-averaged TIR absolute error between block and random deletion. Report each dataset/device separately at the prespecified 20% requested budget in the first 24-hour window. This is an analysis extension after observing v0.1 results, not prospective preregistration.

- Average absolute errors across seeds within each participant before computing paired differences; do not treat seeds as independent people.
- Bootstrap participants as clusters, retaining all their paired modes and device results. Specify the interval method, bootstrap count and seed in configuration before implementation.
- Report the paired effect, uncertainty interval, participant count and distribution of individual effects. Distinguish population uncertainty from simulation variability.
- Treat 5/10% budgets, other windows and night deletion as secondary sensitivity analyses. Overlapping windows are repeated observations; avoid selecting the most favorable result.
- Describe complete-window selection and exclusions. Shanghai supplies a different population and sampling process, not a direct clinical replication of every CGMacros effect.

Completion: tested estimators, deterministic configurations, result tables generated from code and an updated limitations section. Wide intervals or inconsistent findings are valid outcomes.

## Toward v0.3: meal response prediction — first local benchmark implemented

The [protocol](GLUCOPATTERNS_PROTOCOL.md) now fixes the choices discussed below, and [results](GLUCOPATTERNS_RESULTS.md) report the first comparison. The pooled method is fixed-penalty ridge regression; personalization uses a shrunk early-history residual offset. No tuned model search, external meal validation or native-sample online forecast is claimed. This is not a published v0.3 release.

Use existing CGMacros meal metadata first. Freeze the outcome definition, meal eligibility rules and evaluation protocol before fitting models. A candidate primary outcome is the time-weighted mean glucose during 0–120 minutes after a meal minus the mean during the preceding 30 minutes. Decide boundary coverage and overlapping-meal handling explicitly; do not silently fill missing outcome windows.

Compare three methods on identical eligible test meals: a training-only mean-response baseline, a pooled model with available meal/premeal features, and a limited-history personalized extension. Meal features must be available at the stated prediction time; postmeal values are outcomes, never inputs.

Evaluate two distinct settings:

1. **Unseen participant:** hold out participants entirely; train transformations and tune hyperparameters inside training participants only. This evaluates cross-person generalization, without personal-history adaptation.
2. **Participant with early history:** train global components on other participants, adapt using only the target participant's chronologically earlier labeled meals, and evaluate on later meals. Compare all three methods on the same later-meal set. Purge overlaps between adaptation outcome windows and evaluation inputs.

Report participant-macro-averaged MAE, paired comparisons and the number of usable participants/meals at every history budget. Declare whether updates are fixed after adaptation or rolling. Use nested training/validation splits and reserve test outcomes for final evaluation. Nutrition associations and feature attributions are not causal effects.

Completion: one frozen protocol, simple baselines, leakage checks, an auditable split manifest and an honest report. Shanghai meal data can be considered afterward, subject to a separate harmonization audit.

## Toward v0.4: data quality and personalization — input-only experiment implemented locally

The [joint protocol](HISTORY_MISSINGNESS_PROTOCOL.md) and [results](HISTORY_MISSINGNESS_RESULTS.md) now connect the modules using ten early meals and fixed later test meals. Historical outcome-label degradation, alternative adaptation policies and other history budgets remain future extensions. This is not a published v0.4 release.

Hold later evaluation meals and their reference outcomes fixed. Artificially mask only the early personal history, recompute available historical features and compare the personalized improvement over the pooled model across missingness patterns and budgets. Specify whether adaptation labels are also degraded; feature-only degradation and label degradation are different experiments.

Track coverage, excluded histories and changing eligibility to avoid apparent gains caused by dropping difficult participants. Use matched masks/seeds where meaningful and retain participant pairing. Synthetic deletion describes an intervention on the released records, not proof of a real device failure mechanism.

## What is needed next

No additional dataset is necessary for v0.2 or the initial v0.3 study. Public author identity, application deadline and the intended academic field can refine presentation, but should not change the scientific claims. Adding larger data, deep models or explanation plots is conditional on a demonstrated research need.
