# Changelog

## Unreleased — joint history-input missingness experiment

- Simulate random/block/night missingness across the first ten-meal history timeline while retaining clean adaptation labels and fixed later test meals.
- Report actual premeal exposure, usable adaptation meals, remaining benefit and paired degradation cost with participant-bootstrap intervals.
- Record seed definitions, mask hashes, input/code provenance and explicit infeasible-budget handling.

## Unreleased — GlucoPatterns first benchmark

- Freeze retrospective meal targets, eligibility, features, model penalties and leave-participant-out / early-history splits before the first prediction run.
- Add meal exclusions, split/prediction manifests and participant-macro evaluation of mean baseline, ridge model and shrunk personal offset.
- Require optional NumPy only for prediction; keep the synthetic GlucoTrust workflow dependency-free.

## Unreleased — participant-paired inference

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
