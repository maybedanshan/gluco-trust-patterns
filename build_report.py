"""Generate the versioned English report from local experiment outputs."""
import hashlib
import json
import platform
import statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def load(relative, hashes):
    path=ROOT/relative
    if not path.exists(): raise ValueError(f'Missing {relative}; run python reproduce.py all first')
    hashes[relative]=hashlib.sha256(path.read_bytes()).hexdigest()
    return json.loads(path.read_text(encoding='utf-8'))


def rows_summary(results):
    summary=[]
    for mode in ['random','block','night']:
        for ratio in sorted({r['requested_ratio'] for r in results}):
            rs=[r for r in results if r['mode']==mode and r['requested_ratio']==ratio]
            ids=sorted({r['participant'] for r in rs})
            def per_person(metric):
                return [statistics.mean(abs(r[metric]) for r in rs if r['participant']==pid) for pid in ids]
            means=per_person('mean_bias_mg_dl'); tirs=per_person('tir_bias_pp')
            summary.append((mode,ratio,statistics.mean(r['time_missing_ratio'] for r in rs),statistics.mean(means),statistics.mean(tirs),statistics.stdev(tirs) if len(tirs)>1 else 0))
    return summary


def main():
    hashes={}
    robust=load('outputs/cgmacros_audit/robustness.json',hashes)
    shanghai=load('outputs/shanghai_v5/experiment/results.json',hashes)['results']
    shanghai_audit=load('outputs/shanghai_v5/audit.json',hashes)
    physio=load('outputs/physiocgm/audit.json',hashes)
    cgm_audit=load('outputs/cgmacros/audit.json',hashes)
    cgm=robust['results']
    lines=['# GlucoTrust v0.2 — Results and limitations','',
        'Generated from local result JSON by build_report.py. Software version 0.2.0. This is a descriptive research report, not evidence of clinical utility or a validated device-dropout mechanism.','',
        'An exploratory post-v0.1 extension now reports [participant-paired differences and bootstrap intervals](PAIRED_RESULTS.md). Its estimates and limitations are separate from the descriptive tables below.','',
        '## Research question','',
        'At a matched missing-time budget within an experiment, how do random deletions, a continuous block and night-restricted deletions change time-weighted mean glucose and time in range (TIR)?','',
        '## Data and selection','',
        f'- CGMacros 1.0.0: {len(cgm_audit["participants"])} available participants; {len({r["participant"] for r in cgm})} with common complete dual-device windows. The first 24-hour window is primary. Sensitivity uses first/last windows of 24/48/72 hours.',
        f'- ShanghaiT2DM 20425518.v5 (2022-09-24): {len({r["member"] for r in shanghai_audit["records"]})} workbooks, {len({r["participant"] for r in shanghai_audit["records"]})} people; {len({r["participant"] for r in shanghai})} included after selecting one earliest complete 24-hour window per person.',
        f'- PhysioCGM 28136294.v1: {len(physio["participants"])} raw CGM exports, audited separately for internal candidate timestamp gaps.',
        '- No original CSV/Excel records are redistributed here. CGMacros-derived summaries retain CC BY-NC-SA 4.0; source-specific terms are listed in DATA_LICENSES.md.','',
        '## Metric and aggregation','',
        'TIR uses 70–180 mg/dL inclusive. Each nonterminal value receives capped forward support determined before deletion; the terminal value has zero weight. Deleting a value removes its support without expanding neighboring support or imputing the gap. Reference means the input curve before simulated deletion, not complete physiological truth.',
        'Signed bias = after − reference. TIR bias/MAE is measured in percentage points (pp). For MAE, first average absolute errors across seeds per person, then average persons equally. SD below is between-person SD of that per-person MAE, not a confidence interval. Seeds 0–9 are repeated simulation settings, not independent people.','',
        '## Primary missingness experiments','',
        '| Dataset / device | Pattern | Requested | Actual time missing | Mean-glucose MAE (mg/dL) | TIR MAE (pp) | Between-person TIR MAE SD (pp) |',
        '|---|---|---:|---:|---:|---:|---:|']
    for label,rs in [('CGMacros / Dexcom',[r for r in cgm if r['device']=='dexcom' and r['hours']==24 and r['position']=='first']),
                     ('CGMacros / Libre',[r for r in cgm if r['device']=='libre' and r['hours']==24 and r['position']=='first']),('ShanghaiT2DM',shanghai)]:
        for mode,ratio,actual,mean,tir,sd in rows_summary(rs):
            lines.append(f'|{label}|{mode}|{ratio:.0%}|{actual:.3%}|{mean:.3f}|{tir:.3f}|{sd:.3f}|')
    lines+=['','In these selected windows, random deletion has lower aggregate MAE than the structured patterns. This is a descriptive comparison, not a statistical significance claim. Shanghai budgets are rounded to whole 15-minute readings, so cross-dataset fractions are close but not identical. Differences across datasets cannot be attributed solely to missingness.','',
        '## Window sensitivity at 20% requested missingness','',
        '| Device | Hours | Position | People | Random TIR MAE | Block TIR MAE | Night TIR MAE |', '|---|---:|---|---:|---:|---:|---:|']
    for device in ['dexcom','libre']:
        for hours in [24,48,72]:
            for position in ['first','last']:
                rs=[r for r in cgm if r['device']==device and r['hours']==hours and r['position']==position and r['requested_ratio']==.2]
                values=[statistics.mean(abs(r['tir_bias_pp']) for r in rs if r['mode']==mode) for mode in ['random','block','night']]
                lines.append(f'|{device}|{hours}|{position}|{len({r["participant"] for r in rs})}|'+ '|'.join(f'{v:.3f}' for v in values)+'|')
    lines+=['',f'This grid contains {len(cgm):,} simulations, including the primary configuration. Window overlap, shared participants and reused seeds preclude treating these as independent studies. Larger windows and different positions change the numerical errors; the first-day estimate is not a universal ten-day effect.','',
        '## Cross-device agreement: separate descriptive analysis','',
        'Agreement uses all common observed minute supports, not only the selected 24-hour primary windows. No lag is fitted and neither device serves as a reference standard.']
    agreement=[p['agreement'] for p in cgm_audit['participants'] if p['agreement']['common_supported_minutes']>0]
    lines += [f'Across {len(agreement)} people, equally weighted: mean Dexcom-minus-Libre glucose difference = {statistics.mean(r["dexcom_minus_libre_mean_mg_dl"] for r in agreement):.3f} mg/dL; between-device MAE = {statistics.mean(r["between_device_mae_mg_dl"] for r in agreement):.3f} mg/dL; TIR difference = {statistics.mean(r["dexcom_minus_libre_tir_pp"] for r in agreement):.3f} pp.',
        'These substantial differences may reflect sensors, wear sites, preprocessing and context. They do not identify which device is more accurate.','',
        '## PhysioCGM: candidate gaps, not confirmed disconnections','',
        '| Participant | Timestamped EGV records | Export span (days) | Gaps >7.5 min | Of these, >6 h |','|---|---:|---:|---:|---:|']
    for p in physio['participants']:
        lines.append(f'|{p["participant"]}|{p["egv_timestamp_count"]}|{p["span_days"]:.2f}|{p["gap_count"]}|{p["long_gap_count_over_6h"]}|')
    lines += ['',f'{sum(p["gap_count"] for p in physio["participants"])} candidate gaps were found between unique EGV timestamps. We use a 5-minute expected interval and a >7.5-minute threshold to tolerate timing jitter. No missingness is inferred outside export boundaries.',
        'The paper describes connectivity loss as a likely explanation, not a verified event log. Raw CGM exports span about 18–90 days and are not yet restricted to the multimodal collection sessions. Long gaps may cross wear periods; simulation parameters have not been calibrated from these counts.','',
        '## Limits and next steps','',
        '1. CGMacros contains interpolation features. Remaining values can encode neighboring original information; this is post-preprocessing deletion, not loss-before-interpolation.',
        '2. Complete-window selection may favor better observed periods. Population, device and acquisition differences limit external generalization.',
        '3. No participant bootstrap, significance test or clinical decision threshold is supplied. Variation across seeds is Monte Carlo variability, not population uncertainty.',
        '4. Night restriction uses released clock hours, not verified real-world disconnect causes. Date shifts do not recover calendar context.',
        '5. Meal prediction and joint missingness analyses are available in the companion reports linked from README.md. They remain retrospective, protocol-defined exploratory analyses.','',
        '## Reproduction and attribution','',
        'Run `python reproduce.py all` with the licensed local data, then `python reproduce.py release`. See [reproduction guide](REPRODUCIBILITY.md) and [data attribution](DATA_LICENSES.md).',
        'Sources: [CGMacros data](https://doi.org/10.13026/3z8q-x658) and [paper](https://doi.org/10.1038/s41597-025-05851-7); [Shanghai v5](https://doi.org/10.6084/m9.figshare.20425518.v5) and [paper](https://doi.org/10.1038/s41597-023-01940-7); [PhysioCGM v1](https://doi.org/10.6084/m9.figshare.28136294.v1) and [paper](https://doi.org/10.1038/s41597-025-06090-6).',
        'This authored report: CC BY-NC-SA 4.0. Source-specific licenses remain applicable.','',
        '## Source result hashes','', '| Local result artifact | SHA256 |','|---|---|']
    lines += [f'|{p}|{digest}|' for p,digest in sorted(hashes.items())]
    (ROOT/'docs/RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (ROOT/'docs/result-provenance.json').write_text(json.dumps({'version':'0.2.0','python':platform.python_version(),
        'result_sha256':hashes,'builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2),encoding='utf-8')
    print('Generated docs/RESULTS.md from verified local outputs')


if __name__=='__main__': main()
