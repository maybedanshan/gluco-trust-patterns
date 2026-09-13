# GlucoTrust v0.1 — Results and limitations

Generated from local result JSON by build_report.py. Software version 0.1.0. This is a descriptive research report, not evidence of clinical utility or a validated device-dropout mechanism.

An exploratory post-v0.1 extension now reports [participant-paired differences and bootstrap intervals](PAIRED_RESULTS.md). Its estimates and limitations are separate from the descriptive tables below.

## Research question

At a matched missing-time budget within an experiment, how do random deletions, a continuous block and night-restricted deletions change time-weighted mean glucose and time in range (TIR)?

## Data and selection

- CGMacros 1.0.0: 45 available participants; 44 with common complete dual-device windows. The first 24-hour window is primary. Sensitivity uses first/last windows of 24/48/72 hours.
- ShanghaiT2DM 20425518.v5 (2022-09-24): 109 workbooks, 100 people; 100 included after selecting one earliest complete 24-hour window per person.
- PhysioCGM 28136294.v1: 10 raw CGM exports, audited separately for internal candidate timestamp gaps.
- No original CSV/Excel records are redistributed here. CGMacros-derived summaries retain CC BY-NC-SA 4.0; source-specific terms are listed in DATA_LICENSES.md.

## Metric and aggregation

TIR uses 70–180 mg/dL inclusive. Each nonterminal value receives capped forward support determined before deletion; the terminal value has zero weight. Deleting a value removes its support without expanding neighboring support or imputing the gap. Reference means the input curve before simulated deletion, not complete physiological truth.
Signed bias = after − reference. TIR bias/MAE is measured in percentage points (pp). For MAE, first average absolute errors across seeds per person, then average persons equally. SD below is between-person SD of that per-person MAE, not a confidence interval. Seeds 0–9 are repeated simulation settings, not independent people.

## Primary missingness experiments

| Dataset / device | Pattern | Requested | Actual time missing | Mean-glucose MAE (mg/dL) | TIR MAE (pp) | Between-person TIR MAE SD (pp) |
|---|---|---:|---:|---:|---:|---:|
|CGMacros / Dexcom|random|5%|5.000%|0.143|0.120|0.084|
|CGMacros / Dexcom|random|10%|10.000%|0.189|0.172|0.122|
|CGMacros / Dexcom|random|20%|20.000%|0.300|0.257|0.187|
|CGMacros / Dexcom|block|5%|5.000%|0.952|0.786|0.808|
|CGMacros / Dexcom|block|10%|10.000%|1.716|1.328|1.357|
|CGMacros / Dexcom|block|20%|20.000%|3.099|2.504|2.501|
|CGMacros / Dexcom|night|5%|5.000%|0.490|0.483|0.548|
|CGMacros / Dexcom|night|10%|10.000%|1.030|0.997|1.152|
|CGMacros / Dexcom|night|20%|20.000%|2.334|2.248|2.595|
|CGMacros / Libre|random|5%|5.000%|0.132|0.166|0.078|
|CGMacros / Libre|random|10%|10.000%|0.174|0.244|0.121|
|CGMacros / Libre|random|20%|20.000%|0.263|0.332|0.162|
|CGMacros / Libre|block|5%|5.000%|0.882|1.079|0.666|
|CGMacros / Libre|block|10%|10.000%|1.697|1.854|1.282|
|CGMacros / Libre|block|20%|20.000%|3.020|3.193|2.203|
|CGMacros / Libre|night|5%|5.000%|0.682|0.771|0.719|
|CGMacros / Libre|night|10%|10.000%|1.441|1.629|1.550|
|CGMacros / Libre|night|20%|20.000%|3.239|3.668|3.510|
|ShanghaiT2DM|random|5%|5.208%|0.821|0.733|0.314|
|ShanghaiT2DM|random|10%|10.417%|1.178|1.030|0.457|
|ShanghaiT2DM|random|20%|19.792%|1.766|1.546|0.668|
|ShanghaiT2DM|block|5%|5.208%|1.834|1.479|0.782|
|ShanghaiT2DM|block|10%|10.417%|3.678|2.839|1.510|
|ShanghaiT2DM|block|20%|19.792%|6.537|4.722|2.649|
|ShanghaiT2DM|night|5%|5.208%|1.832|1.321|0.908|
|ShanghaiT2DM|night|10%|10.417%|3.854|2.689|1.978|
|ShanghaiT2DM|night|20%|19.792%|8.123|5.563|4.290|

In these selected windows, random deletion has lower aggregate MAE than the structured patterns. This is a descriptive comparison, not a statistical significance claim. Shanghai budgets are rounded to whole 15-minute readings, so cross-dataset fractions are close but not identical. Differences across datasets cannot be attributed solely to missingness.

## Window sensitivity at 20% requested missingness

| Device | Hours | Position | People | Random TIR MAE | Block TIR MAE | Night TIR MAE |
|---|---:|---|---:|---:|---:|---:|
|dexcom|24|first|44|0.257|2.504|2.248|
|dexcom|24|last|44|0.232|2.087|1.626|
|dexcom|48|first|44|0.184|1.728|1.932|
|dexcom|48|last|44|0.172|1.409|1.469|
|dexcom|72|first|44|0.149|1.422|1.678|
|dexcom|72|last|44|0.140|1.174|1.455|
|libre|24|first|44|0.332|3.193|3.668|
|libre|24|last|44|0.203|1.905|2.194|
|libre|48|first|44|0.238|2.564|2.994|
|libre|48|last|44|0.165|1.613|1.953|
|libre|72|first|44|0.201|1.977|3.131|
|libre|72|last|44|0.126|1.241|1.768|

This grid contains 47,520 simulations, including the primary configuration. Window overlap, shared participants and reused seeds preclude treating these as independent studies. Larger windows and different positions change the numerical errors; the first-day estimate is not a universal ten-day effect.

## Cross-device agreement: separate descriptive analysis

Agreement uses all common observed minute supports, not only the selected 24-hour primary windows. No lag is fitted and neither device serves as a reference standard.
Across 45 people, equally weighted: mean Dexcom-minus-Libre glucose difference = 32.358 mg/dL; between-device MAE = 35.110 mg/dL; TIR difference = 3.060 pp.
These substantial differences may reflect sensors, wear sites, preprocessing and context. They do not identify which device is more accurate.

## PhysioCGM: candidate gaps, not confirmed disconnections

| Participant | Timestamped EGV records | Export span (days) | Gaps >7.5 min | Of these, >6 h |
|---|---:|---:|---:|---:|
|c1s01|25356|89.99|59|2|
|c1s02|21167|76.00|16|4|
|c1s03|25349|89.99|11|3|
|c1s04|4634|18.32|7|4|
|c1s05|25260|90.00|50|1|
|c2s01|25001|90.00|18|2|
|c2s02|25662|90.00|13|0|
|c2s03|24287|89.89|15|6|
|c2s04|25496|89.99|12|1|
|c2s05|24973|89.96|116|2|

317 candidate gaps were found between unique EGV timestamps. We use a 5-minute expected interval and a >7.5-minute threshold to tolerate timing jitter. No missingness is inferred outside export boundaries.
The paper describes connectivity loss as a likely explanation, not a verified event log. Raw CGM exports span about 18–90 days and are not yet restricted to the multimodal collection sessions. Long gaps may cross wear periods; simulation parameters have not been calibrated from these counts.

## Limits and next steps

1. CGMacros contains interpolation features. Remaining values can encode neighboring original information; this is post-preprocessing deletion, not loss-before-interpolation.
2. Complete-window selection may favor better observed periods. Population, device and acquisition differences limit external generalization.
3. No participant bootstrap, significance test or clinical decision threshold is supplied. Variation across seeds is Monte Carlo variability, not population uncertainty.
4. Night restriction uses released clock hours, not verified real-world disconnect causes. Date shifts do not recover calendar context.
5. No meal-response prediction is part of v0.1. Future GlucoPatterns work needs predefined outcomes, person/time splits and leakage checks.

## Reproduction and attribution

Run `python reproduce.py all` with the licensed local data, then `python reproduce.py release`. See [reproduction guide](REPRODUCIBILITY.md) and [data attribution](DATA_LICENSES.md).
Sources: [CGMacros data](https://doi.org/10.13026/3z8q-x658) and [paper](https://doi.org/10.1038/s41597-025-05851-7); [Shanghai v5](https://doi.org/10.6084/m9.figshare.20425518.v5) and [paper](https://doi.org/10.1038/s41597-023-01940-7); [PhysioCGM v1](https://doi.org/10.6084/m9.figshare.28136294.v1) and [paper](https://doi.org/10.1038/s41597-025-06090-6).
This authored report: CC BY-NC-SA 4.0. Source-specific licenses remain applicable.

## Source result hashes

| Local result artifact | SHA256 |
|---|---|
|outputs/cgmacros/audit.json|13e18320aa2ec39881e836f8d6835691a505cf70471a08460db907385d02f9ec|
|outputs/cgmacros_audit/robustness.json|173bdf895f5deabf833730c905b6cf2d92031ea0b85d8a81ce22b2dd809d8fea|
|outputs/physiocgm/audit.json|4ab9ac637d88a11cc0abb7abc170e7ddb18427b08e67b897ad855ef55043c864|
|outputs/shanghai_v5/audit.json|090e8c558cb032f4d099710c2c468bf793e12d2cca03efe4a11ee9bed2387168|
|outputs/shanghai_v5/experiment/results.json|4c40193869cd975b4f4e3423e0543c5e525b065d1f3a8b36a21415040deda83e|
