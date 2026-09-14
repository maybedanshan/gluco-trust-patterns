# v0.2 validation record

Validated locally on 2026-09-14 using Windows, Python 3.12.14 and a newly created virtual environment with no system site packages. Dependencies were installed from the fixed requirements-repro.txt: NumPy 2.3.5, openpyxl 3.1.5, et_xmlfile 2.0.0, xlrd 2.0.2. pip check found no dependency conflicts.

## Independent complete reproduction

An independent source directory started with no outputs directory. Existing local source data were copied into that directory, and `python reproduce.py full` completed successfully. Download transport was not revalidated during this offline run; original data checksums and upstream provenance were checked by the analysis scripts.

All 45 research tests present at that point passed in the independent directory. The final source suite contains 46 tests (including the added archive-integrity test); all passed in the isolated environment against the freshly generated outputs. Fresh prediction MAEs and selected-model joint effects matched the prior environment to 1e-12. Reports and generated artifacts in this source snapshot were promoted from that independent full run.

## Archive checks

Two consecutive builds produced byte-identical ZIP files. All 76 packaged files passed the manifest check. In a fresh extracted directory without raw data, `python -S reproduce.py demo` completed 540 synthetic runs without loading site packages. The extracted test suite passed with 10 local-real-output checks skipped as expected (46 total tests). Source-specific licenses and both offline explorers are included.

The release ZIP uses an explicit file allowlist and a complete per-file SHA-256 manifest. Run `python verify_release.py dist/gluco-trust-patterns-0.2.0.zip` with its companion .zip.sha256 file. The archive excludes raw participant files, local per-meal predictions, environments and Git metadata. Original v0.1 archives are retained separately.

## Limits of validation

Local numerical reproducibility and code tests do not establish clinical validity or prospective prediction performance. The GitHub Actions matrix is configured but no hosted run or public GitHub release is claimed by this record. The full environment was tested on Windows/Python 3.12; Python 3.10 remains a source-syntax and configured core-CI target, not an independently verified full-research runtime.
