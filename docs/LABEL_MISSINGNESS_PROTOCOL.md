# Historical label missingness: protocol 1.0

Exploratory extension fixed after reviewing input-only experiments, before its first run. Not preregistered. The v0.2 archive and previous result files remain unchanged.

## Fixed objects

Reuse all original eligible meals, outer held-out participants, stored inner-selected ridge penalties, ten early adaptation meals and the same 739 later test meals for 44 people. Global training uses other people only. Test features and outcomes are always complete. Shrunk adaptation remains residual sum / (usable meals + 5), with a pooled fallback when no history meal remains usable. No new tuning or test-set selection.

## Timeline and masks

The early-history timeline now extends from 30 minutes before the first adaptation meal through the end of the tenth meal's 120-minute outcome window (exclusive terminal boundary). This is longer than the input-only timeline, so masks are newly generated, not claimed identical to v0.2 masks. The timeline must end no later than the first later-test premeal input starts. Observed released Dexcom values each have one minute of fixed capped support; no original gap is bridged or interpolated.

Requested timeline fractions: 0/5/10/20%. Patterns: random sampling, one contiguous observed-index block, and night-restricted (00:00–06:00) random sampling. Seeds 0–9. Reuse each mask across all intervention arms and coverage thresholds. Infeasible night budgets are explicitly recorded and incomplete configuration summaries suppressed without dropping people.

## Coverage and damaged labels

The reference label is the complete released mean during [0,120) minus the complete [-30,0) mean, in mg/dL. A damaged label recomputes both means from retained one-minute supports. Require at least 15/30 premeal minutes and, in the **primary analysis**, 84/120 postmeal minutes (70%). No imputation and no zero-filled labels. Prespecified secondary postmeal coverage thresholds are 50% (60 minutes) and 90% (108 minutes), keeping the same masks and later tests. These thresholds are analysis choices, not clinical standards.

The premeal component belongs to the label too. In the label-only arm, the input features remain clean while the label's premeal baseline may be damaged. In the joint arm, the same retained premeal values determine both features and label baseline. Their errors can be correlated; joint effects are not expected to equal the sum of isolated effects.

## Three intervention arms

1. Input-only: degrade premeal features with the existing 15/30 rule, retain original complete labels; postmeal threshold does not affect this arm.
2. Label-only: keep original clean features, use the damaged label only when both coverage requirements pass; otherwise omit that adaptation meal.
3. Joint: require both usable input features and a usable damaged label, then use both degraded versions.

All arms retain every participant and the same later tests regardless of historical usability. Historical nutrition and clock features stay unchanged. The reference is clean selected-model personalization on all ten early meals.

## Outputs and interpretation

Per run: timeline/premeal/postmeal exposure, usable adaptation counts, later prediction MAE, remaining benefit over pooled, and cost relative to clean personalization. Record label signed/absolute error, maximum absolute error, and valid-label counts from labels meeting the coverage rule. Do not substitute a zero error when no labels are usable. Public label-error means pool valid labels within each participant, then average only participants with any valid label and report that denominator. Thus label-error summaries are conditional on availability, not the full-history error distribution.

Average prediction errors over seeds within each participant, then equally across people. Use 10,000 shared participant-bootstrap draws, seed 20260918, 95% pointwise percentile intervals for benefit and cost. The primary threshold is 70%; other thresholds are sensitivity analyses, not opportunities to choose favorable results. Intervals exclude full-refitting uncertainty and multiplicity adjustment. Record paired joint-minus-input and joint-minus-label MAE contrasts on the same person/masks/tests.

Local meal-level diagnostics, predictions/offsets and mask hashes support audit without public raw-record redistribution. Source-derived summaries retain CC BY-NC-SA 4.0. Source interpolation, unknown meal metadata availability, missing meals and complete-case selection still prevent clinical or prospective prediction claims. This experiment studies observationally degraded labels, not loss of all nutrition or entire meal events.
