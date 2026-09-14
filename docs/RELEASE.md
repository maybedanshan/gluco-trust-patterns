# GlucoTrust + GlucoPatterns 0.2.0

Source snapshot date: 2026-09-14. This document does not claim that a GitHub tag, Release or hosted CI run has been published.

## Included research

- Time-weighted missingness experiments and participant-paired intervals.
- Meal audit, fixed-model benchmark, inner-selected model comparison and history-only baseline.
- Fixed and selected-model history-input missingness, including an ordered availability/feature decomposition.
- Two offline explorers, protocols, generated reports, source-specific licenses and provenance.

## Reproduce

Use Python 3.12 and `python -m pip install -r requirements-repro.txt`, then `python reproduce.py full`. Downloads require the explicit `--download` flag. `python reproduce.py release` packages generated results and allowlisted source files without raw participant records, local predictions or environments.

The ZIP includes a per-file SHA-256 manifest and has a separate archive checksum. The prior v0.1 archive is preserved. See [validation](VALIDATION.md) for the exact scope actually checked.

## Scientific scope

All prediction studies are retrospective on processed CGMacros values. Interpolation may compromise prospective interpretation. Complete-window selection and unknown meal metadata availability remain limitations. Confidence intervals are pointwise, conditional on fitted folds; the diagnostic decomposition is not causal attribution. Historical labels remain complete in the joint experiments. External meal and native-sample prospective validation are not part of this release.
