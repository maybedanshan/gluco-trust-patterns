# Changelog

## Unreleased — historical-label study

Add matched input-only, label-only and joint historical degradation with 70% primary postmeal coverage and 50/90% sensitivity. Record conditional label errors, history availability and infeasible night budgets. Section 3 of the development explorer presents these results. The v0.2 ZIP and its full workflow remain unchanged.

## 0.2.0 — 2026-09-14

Consolidates the research additions below into one versioned source snapshot. Adds a full workflow, pinned Python 3.12 dependencies, independent-directory validation and deterministic packaging. The v0.1 archive remains unchanged.


### Included — selected-model joint experiment and research explorer

- Repeat v1 masks and later test meals with stored inner-selected ridge penalties, verifying all upstream provenance and mask hashes.
- Decompose total degradation into availability and retained-feature costs using a specified diagnostic order.
- Add an offline interactive model/history explorer and preserve the existing author identity and release citation version.

### Included — stronger model comparison

- Add five inner participant folds for ridge-penalty selection, entirely excluding the outer test person.
- Compare a history-only response mean against personalization on identical later test meals.
- Preserve v1 fixed-penalty results and record local inner-fold/selection manifests under a separate exploratory protocol.

### Included — joint history-input missingness experiment

- Simulate random/block/night missingness across the first ten-meal history timeline while retaining clean adaptation labels and fixed later test meals.
- Report actual premeal exposure, usable adaptation meals, remaining benefit and paired degradation cost with participant-bootstrap intervals.
- Record seed definitions, mask hashes, input/code provenance and explicit infeasible-budget handling.

### Included — GlucoPatterns first benchmark

- Freeze retrospective meal targets, eligibility, features, model penalties and leave-participant-out / early-history splits before the first prediction run.
- Add meal exclusions, split/prediction manifests and participant-macro evaluation of mean baseline, ridge model and shrunk personal offset.
- Require optional NumPy only for prediction; keep the synthetic GlucoTrust workflow dependency-free.

### Included — participant-paired inference

- Add block/night minus random seed-averaged absolute-error contrasts with participant-cluster percentile bootstrap intervals.
- Retain paired device draws; report three primary TIR comparisons and 33 secondary comparisons separately.
- Add fixed configuration, source/code hashes, generated report and six estimator tests. The extension is exploratory after inspection of v0.1 results.

## 0.1.0 — 2026-09-13

- Unified offline reproduction entry point with explicit public-data download mode.
- Offline SVG explorer: error versus missingness, participant signed bias, seed variability and summary export.
- CGMacros primary/sensitivity experiments, ShanghaiT2DM v5 validation and exploratory PhysioCGM gap audit.
- Generated English report, bilingual overview, data licenses, contribution guidance and deterministic source archive.
- Guards against nonfinite support caps and duplicate experimental configurations.

No meal-prediction model, clinical validation, confirmed connection-event model, PyPI package or hosted service is included.
