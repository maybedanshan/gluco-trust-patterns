# Data licenses and attribution

Original GlucoTrust software is MIT. This does not change source-data licenses or imply endorsement by their creators.

| Material | Creator/source | Version used | Terms |
|---|---|---|---|
| CGMacros CSVs | Gutierrez-Osuna, Kerr, Mortazavi & Das; PhysioNet | 1.0.0, DOI 10.13026/3z8q-x658 | [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) |
| ShanghaiT2DM workbooks | Qinpei Zhao, Jinhao Zhu, Congrong Wang & Weixiong Rao; figshare | 20425518.v5, 2022-09-24 | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| PhysioCGM raw exports | Quamer et al.; figshare | 28136294.v1 | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) as labeled by the repository |

Official records: [CGMacros](https://physionet.org/content/cgmacros/1.0.0/), [Shanghai v5](https://doi.org/10.6084/m9.figshare.20425518.v5), [PhysioCGM v1](https://doi.org/10.6084/m9.figshare.28136294.v1). Checked for this release on 2026-09-13. A paper's publication license is not necessarily its dataset's license.

## Redistributed material

The source release contains original software, documentation, an offline explorer and numerical derived summaries. It contains no source CSVs, Excel workbooks, sensor archives, meal photos, individual glucose traces or private inputs.

- CGMacros-derived summaries embedded in docs/demo/index.html and docs/RESULTS.md are CC BY-NC-SA 4.0. Attribute the dataset and paper, retain the license, indicate modifications, and observe noncommercial/share-alike terms.
- Shanghai-derived summaries are CC BY 4.0 with source version and paper attribution.
- PhysioCGM-derived statistics identify their CC0 source; attribution is retained for research traceability.
- The authored combined results report is provided under CC BY-NC-SA 4.0, retaining source-specific notices. The independent dashboard template and Python code remain MIT. Noncommercial restrictions on CGMacros-derived material are not restrictions on independently usable MIT software.

## Modifications

CGMacros: retain released values, choose complete matched windows, simulate deleted supports, calculate metrics, average by participant/seed, remove original timestamps and glucose traces from the explorer. Released curves already exhibit interpolation features.

Shanghai: parse XLS/XLSX, group by participant ID, select earliest complete windows, retain mg/dL units, simulate deletions and summarize metrics. Identical duplicate timestamps are audited and collapsed; conflicting records are excluded with reasons.

PhysioCGM: retrieve raw cgm.csv archive members, select EGV timestamps, identify internal candidate gaps using a declared threshold, and report descriptive counts. Causes are not verified.

## Original publications

1. Das et al. (2025). [CGMacros: a pilot scientific dataset for personalized nutrition and diet monitoring](https://doi.org/10.1038/s41597-025-05851-7).
2. Zhao et al. (2023). [Chinese diabetes datasets for data-driven machine learning](https://doi.org/10.1038/s41597-023-01940-7).
3. Quamer et al. (2025). [A multimodal physiological dataset for non-invasive blood glucose estimation](https://doi.org/10.1038/s41597-025-06090-6).

CITATION.cff identifies this software only. Cite source data and papers separately. Source authors are not represented as GlucoTrust authors or endorsers.
