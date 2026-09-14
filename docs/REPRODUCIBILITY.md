# Reproducing GlucoTrust + GlucoPatterns v0.2

## Selected-model joint experiment and explorer

Run `patterns`, `history`, and `compare` first, then `python reproduce.py selected-history`. This verifies upstream result/code hashes, reuses selected penalties and verifies exact v1 mask hashes. `python reproduce.py dashboard` also generates `docs/demo/research.html` from aggregate results. The two diagnostic cost terms sum to total cost under the declared ordering, not a unique causal decomposition. These development additions do not overwrite the original v0.1 ZIP.

## Nested model comparison

With existing `patterns` outputs and NumPy, run `python reproduce.py compare`. Read `docs/MODEL_COMPARISON_PROTOCOL.md` and `docs/MODEL_COMPARISON_RESULTS.md`. Original input hashes are checked, and local inner-fold assignments, candidate scores and selected penalties are written to `outputs/model_comparison/selection.json`. Per-meal predictions remain local. The first fixed-parameter benchmark is not overwritten.

## Joint history-input experiment

After `python reproduce.py patterns`, run `python reproduce.py history` with the same NumPy environment and local CGMacros files. Read `docs/HISTORY_MISSINGNESS_PROTOCOL.md` and `docs/HISTORY_MISSINGNESS_RESULTS.md`. Seeds, timeline construction and mask hashes allow exact mask regeneration; participant/run metrics remain in `outputs/history_missingness/`. No additional downloads or model tuning occur. Original v0.1 ZIP files are not rebuilt by this command.

## GlucoPatterns development benchmark

Install `python -m pip install -r requirements-patterns.txt`, then run `python reproduce.py patterns` with local CGMacros records, or `python reproduce.py patterns --download` to retrieve them explicitly. The protocol and aggregate report are `docs/GLUCOPATTERNS_PROTOCOL.md` and `docs/GLUCOPATTERNS_RESULTS.md`. Local event exclusions, exact split IDs, derived features and per-meal predictions stay in `outputs/glucopatterns/`; do not publish those local files. The aggregate JSON records NumPy version and source/protocol/code/output hashes. Included in v0.2; the historical v0.1 ZIP is preserved.

## Post-v0.1 paired analysis

After generating CGMacros and Shanghai outputs, run `python reproduce.py paired`. This creates `docs/PAIRED_RESULTS.md` and `docs/paired-results.json` from `docs/paired-analysis-config.json`. The 10,000-draw participant bootstrap uses only the standard library, retains all within-participant contrasts, and records input/code/configuration SHA-256 hashes. Run `python -m unittest discover -s tests -v` to validate the estimator and existing workflows. This extension is exploratory and included in the v0.2 source snapshot.

## Offline smoke run

Unzip the source distribution and run with Python 3.10+:

    python reproduce.py demo
    python -m unittest discover -s tests -v

No third-party packages or network calls are required. Open outputs/demo/explorer/index.html. Tests that require real-data outputs skip when those outputs are absent.

## Real data

Create an isolated environment:

    python -m venv .venv

Windows PowerShell:

    .\.venv\Scripts\python.exe -m pip install -r requirements-data.txt
    .\.venv\Scripts\python.exe reproduce.py all --download

macOS/Linux:

    .venv/bin/python -m pip install -r requirements-data.txt
    .venv/bin/python reproduce.py all --download

Only Shanghai requires xlrd/openpyxl. Source spreadsheets are read; no macros, source notebooks or pickle payloads are executed. Read [data licenses](DATA_LICENSES.md) before downloading. Omit --download for an offline rerun with existing data.

| Input | Fixed identifier | Integrity check |
|---|---|---|
| CGMacros | PhysioNet 1.0.0 | Selected ZIP member CRC32; local CSV SHA256 |
| ShanghaiT2DM | figshare 20425518.v5 | Full ZIP MD5 matched to repository; local SHA256 |
| PhysioCGM | figshare 28136294.v1 | Selected ZIP member CRC32; local CGM SHA256 |

HTTP Range retrieval does not verify full archive hashes. A saved local hash is not an independent authenticity guarantee. Analysis scripts validate local input bytes against their manifests.

If Range is blocked, CGMacros supports a fully downloaded official archive:

    python fetch_cgmacros.py --zip /path/to/CGMacros_dateshifted365.zip
    python reproduce.py cgmacros --robustness

PhysioCGM Range failure stops explicitly; v0.1 has no automated full-archive fallback for it. Do not substitute processed PKL files. Network errors and source-version changes are not bypassed silently.

## Experiment conventions

- Seeds: 0–9. RNG key: SHA256 of participant ID, ratio, pattern and seed. CGMacros devices share masks on their matched window.
- Requested fractions: 0.05, 0.10, 0.20. Python round selects the count; actual point/time fractions are saved.
- CGMacros: first complete common 24-hour window; sensitivity adds last and 48/72-hour windows. One-minute support; terminal value has zero weight.
- Shanghai: earliest complete 24-hour window per person across records; 15-minute support. Actual fractions: 5/96, 10/96, 19/96.
- PhysioCGM: unique EGV timestamp gaps strictly over 7.5 minutes; expected interval 5 minutes. Full exports have not been aligned to multimodal 24-hour sessions.
- Nonempty, unique ratios/seeds and finite positive caps are required. Undefined/infeasible configurations fail explicitly.

## Outputs and release

Detailed local results retain deleted positions, metrics, selection decisions and source hashes. They are excluded from release. The explorer embeds only participant/seed summaries, not glucose trajectories or original dates.

    python reproduce.py all
    python reproduce.py release

The release command requires CGMacros sensitivity, Shanghai and PhysioCGM results. It creates dist/glucotrust-0.1.0.zip with a SHA256 sidecar and internal MANIFEST.sha256. File ordering and archive timestamps are fixed. Identical input bytes give an identical archive.

build_report.py generates the English report from JSON, including source-result hashes. docs/demo/provenance.json identifies explorer inputs and template/builder hashes. Across Python/library versions, check numerical results using tolerances; bitwise identity across platforms is not promised. Retain runtime versions and manifests for new analyses.

## Validation

CI is configured for the synthetic pipeline and tests on Python 3.10 and 3.12. Local real-data tests independently recalculate time budgets and metrics. The prepared release is also checked in a browser and from a clean source extraction. See [release notes](RELEASE.md) for validation actually performed.
