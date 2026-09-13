# GlucoTrust 0.1.0 release notes

This is a prepared local source release, not a published GitHub release.

## Included

- An offline, interactive explorer with dataset, device, window, metric and missing-fraction controls; participant summaries and CSV export preview.
- Reproducible synthetic, CGMacros, ShanghaiT2DM and PhysioCGM workflows through `reproduce.py`.
- An English README, generated results report, provenance hashes and separate software/data licensing notes.
- A deterministic allowlisted source ZIP and per-file SHA-256 manifest. Raw participant files and local environments are excluded.

## Validation scope

The real-data workflows were rerun locally with Python 3.12. Browser checks covered dataset/metric/window/fraction changes, narrow-screen layout and a Shanghai CSV preview containing 300 data rows. Browser download completion was not independently observable in the embedded browser; the export dialog also provides selectable CSV text.

All 20 local tests passed, including checks against real experiment outputs. A clean extracted-source run with Python's `-S` option (no site packages) completed 540 synthetic experiments; its test suite passed with two real-data checks skipped as expected. Every packaged source file matched the SHA-256 manifest. The GitHub Actions Python 3.10/3.12 matrix is configured; hosted CI has not been run because the project has not been published.

## Scientific boundaries

CGMacros released minute-grid values show interpolation; the experiment measures additional removal from that release, not native device dropout. PhysioCGM timestamp gaps are candidate gaps, not confirmed connection failures. TIR errors use percentage points. Time support is fixed before masking and never extended across removed observations. The sensitivity runs include the primary configuration and must not be added to it as independent experiments.

Meal prediction remains future work. See [results](RESULTS.md), [reproduction](REPRODUCIBILITY.md) and [licenses](DATA_LICENSES.md).
