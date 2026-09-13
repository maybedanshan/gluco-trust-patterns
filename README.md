# GlucoTrust

**v0.1.0 — reproducible experiments on missing CGM data and glucose-report reliability.**

[中文说明](README.zh-CN.md) · [Results](docs/RESULTS.md) · [Reproduction guide](docs/REPRODUCIBILITY.md) · [Data licenses](docs/DATA_LICENSES.md)

Repository: [maybedanshan/gluco-trust](https://github.com/maybedanshan/gluco-trust). See the [research roadmap](docs/RESEARCH_ROADMAP.md) for planned studies and completion criteria, and the [project brief](docs/PROJECT_BRIEF.md) for an evidence-based overview.

**Post-v0.1 research extension:** [participant-paired comparisons and bootstrap intervals](docs/PAIRED_RESULTS.md) are now implemented locally. Run `python reproduce.py paired` after generating the CGMacros and Shanghai results. This exploratory extension was specified after examining v0.1; it is not preregistered or a published v0.2 release.

**GlucoPatterns initial benchmark:** [protocol](docs/GLUCOPATTERNS_PROTOCOL.md) and [meal audit / model results](docs/GLUCOPATTERNS_RESULTS.md). Install `requirements-patterns.txt`, then run `python reproduce.py patterns`. The benchmark separates held-out participants from early-history adaptation, with identical later test meals across history budgets. It is retrospective on processed curves, not validated real-time forecasting.

At the same missing-data budget, do random deletions, continuous gaps and night-window deletions change glucose reports differently?

GlucoTrust measures signed bias and absolute error in time-weighted mean glucose and time in range (TIR), retaining participant differences and seed variation. It includes an offline interactive explorer.

**Scope:** a research prototype, not a clinical tool. CGMacros contains processed minute-grid curves with interpolation features. Its experiments evaluate **additional missingness after preprocessing**, not the effect or cause of original sensor dropout. Neither CGM is a gold standard.

## Try the offline demo

Development extension: [personal-history missingness experiment](docs/HISTORY_MISSINGNESS_RESULTS.md) connects the two modules. After `python reproduce.py patterns`, run `python reproduce.py history`. It masks early historical CGM inputs while keeping labels and later test meals fixed; it does not simulate simultaneous loss of historical labels.

Python 3.10+ is required. No third-party packages or data downloads are needed:

    git clone https://github.com/maybedanshan/gluco-trust.git
    cd gluco-trust
    python reproduce.py demo
    python -m unittest discover -s tests -v

Open outputs/demo/explorer/index.html. For the bundled real-data summary explorer, open [docs/demo/index.html](docs/demo/index.html) directly in a browser. No CDN scripts, telemetry, uploads or server are needed.

Select dataset/device, observation window, metric and missing fraction. Charts show mean absolute error, participant signed bias and seed variation; hover for exact values or export the table. TIR errors are **percentage points (pp)**, not relative percentages.

## Reproduce real-data experiments

Use an isolated Python environment. Optional Excel readers are needed for Shanghai:

    python -m pip install -r requirements-data.txt
    python reproduce.py all --download

Downloading is explicit and subject to the source licenses. Omit --download to use existing local files offline. Commands work from any current directory; outputs are written beside the scripts.

| Command | Purpose |
|---|---|
| python reproduce.py cgmacros --download --robustness | Matched dual-device windows and 24/48/72-hour first/last sensitivity |
| python reproduce.py shanghai --download | ShanghaiT2DM v5, grouped by participant |
| python reproduce.py physio --download | Exploratory gaps in raw PhysioCGM exports |
| python reproduce.py dashboard | Rebuild the explorer from available local results |
| python reproduce.py release | Build report, explorer and deterministic source ZIP; requires all real-data results |

CGMacros and PhysioCGM use HTTP Range to retrieve selected CGM files without photographs or other sensor streams. Partial downloads validate ZIP member CRC32 and record local SHA256; **full-archive verification is not claimed**. See [recovery and verification](docs/REPRODUCIBILITY.md).

## v0.1 evidence

| Analysis | Included population / scope | Runs |
|---|---|---:|
| CGMacros primary | 44 of 45 people; same 24-hour window and deletion mask on both devices | 7,920 |
| CGMacros sensitivity | Same 44 people; 24/48/72 hours, earliest/latest windows, both devices | 47,520 |
| ShanghaiT2DM validation | 100 people grouped from 109 workbooks; one 24-hour window each | 9,000 |
| PhysioCGM audit | 10 raw CGM exports; candidate timestamp gaps only | No simulation |

The sensitivity set **includes the primary configuration**. Repeated seeds and overlapping windows are not independent participants.

At the 20% requested budget, CGMacros primary TIR MAE was 0.257/0.332 pp for random deletion and 2.504/3.193 pp for continuous blocks (Dexcom/Libre). Shanghai's corresponding values were 1.546 and 4.722 pp, with an actual budget of 19/96 = 19.792%. These are descriptive, dataset-specific findings, not a pooled effect or clinical threshold. [Full report](docs/RESULTS.md).

## Measurement contract

- TIR uses 70–180 mg/dL, inclusive: a fixed research definition, not a personalized clinical target.
- Reading i has forward support equal to the smaller of the next timestamp interval and the support cap. The terminal reading has zero support. Weights are fixed **before deletion**; gaps are not bridged or imputed afterward.
- The reference is the input's observed support, not an unobserved complete physiological trajectory.
- Fractions are rounded to counts of supported readings. On irregular inputs, point fraction differs from time fraction; both are exported.
- Random: sampling without replacement. Block: one contiguous run with a uniformly sampled start. Night: sampling restricted to input clock hours 00:00–06:00, not necessarily one contiguous nightly outage.
- Bias is after deletion minus reference. MAE averages absolute error over seeds per participant, then weights participants equally. The original v0.1 report is descriptive; the separate paired extension supplies pointwise participant-bootstrap intervals, without confirmatory significance claims.
- Input dates must be strictly increasing within a consistent time basis. Date shifts do not restore real calendar context.

## Bring your own data

Provide JSON mapping participant IDs to records with ISO timestamps and glucose_mg_dl:

    {"person-001": [
      {"timestamp": "2025-01-01T00:00:00", "glucose_mg_dl": 105},
      {"timestamp": "2025-01-01T00:05:00", "glucose_mg_dl": 112},
      {"timestamp": "2025-01-01T00:10:00", "glucose_mg_dl": 110}
    ]}

    python glucotrust.py --input data/local/cohort.json --out outputs/custom --support-cap-minutes 5

Outputs retain configuration, input/code hashes, metrics, actual missing fractions and deleted positions. Keep private inputs in data/local/ and local outputs in outputs/; neither is released. Very short recordings or insufficient night coverage may fail explicitly.

## Licenses and citations

Original software: [MIT](LICENSE). External datasets retain their terms. Bundled CGMacros-derived summaries: **CC BY-NC-SA 4.0**; Shanghai-derived summaries: **CC BY 4.0**; PhysioCGM's data record: **CC0**. No raw health records are bundled. [Attribution and modifications](docs/DATA_LICENSES.md).

- Das et al. (2025). *CGMacros: a pilot scientific dataset for personalized nutrition and diet monitoring*. [Paper](https://doi.org/10.1038/s41597-025-05851-7), [data v1.0.0](https://doi.org/10.13026/3z8q-x658).
- Zhao et al. (2023). *Chinese diabetes datasets for data-driven machine learning*. [Paper](https://doi.org/10.1038/s41597-023-01940-7), [actual data version: 20425518.v5](https://doi.org/10.6084/m9.figshare.20425518.v5).
- Quamer et al. (2025). *A multimodal physiological dataset for non-invasive blood glucose estimation*. [Paper](https://doi.org/10.1038/s41597-025-06090-6), [data v1](https://doi.org/10.6084/m9.figshare.28136294.v1).
- Battelino et al. (2019). [International TIR consensus](https://doi.org/10.2337/dci19-0028).
- Prioleau, Lu & Cui (2025). [Glucose-ML, arXiv:2507.14077v1](https://arxiv.org/abs/2507.14077v1). Background for cross-dataset evaluation, not direct evidence of missingness causation or a verified NeurIPS publication claim.

## Contributing and roadmap

See [contribution guidance](CONTRIBUTING.md), [changelog](CHANGELOG.md) and [release notes](docs/RELEASE.md). This is a source distribution, not a PyPI package or hosted service.

The original v0.1 release has no prediction model. The current development tree adds a protocol-fixed exploratory GlucoPatterns benchmark; see its separate report before making any personalization claim. Next: external/native-sample validation and the effect of missing early history. Dropout mechanism calibration remains exploratory until collection windows and missingness provenance are established.
