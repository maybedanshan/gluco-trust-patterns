"""Participant-paired MAE contrasts; standard-library cluster bootstrap."""
import hashlib
import json
import math
import random
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def quantile(sorted_values, probability):
    if not sorted_values or not 0 <= probability <= 1:
        raise ValueError('Nonempty sorted values and a probability in [0,1] required')
    position = (len(sorted_values) - 1) * probability
    lo = math.floor(position)
    hi = math.ceil(position)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (position - lo)


def paired_values(rows, ratio, comparator, metric, expected_seeds):
    grouped = {}
    for row in rows:
        if row['requested_ratio'] != ratio or row['mode'] not in ('random', comparator):
            continue
        key = (row['participant'], row['mode'])
        runs = grouped.setdefault(key, {})
        if row['seed'] in runs:
            raise ValueError('Duplicate participant/mode/seed result')
        if not math.isfinite(row[metric]) or not math.isfinite(row['time_missing_ratio']):
            raise ValueError('Nonfinite metric or budget')
        runs[row['seed']] = row
    ids = sorted({pid for pid, _ in grouped})
    if len(ids) < 2:
        raise ValueError('At least two paired participants required')
    people = []
    for pid in ids:
        a = grouped.get((pid, comparator), {})
        b = grouped.get((pid, 'random'), {})
        if set(a) != set(expected_seeds) or set(b) != set(expected_seeds):
            raise ValueError(f'Incomplete paired seeds: {pid}')
        for seed in expected_seeds:
            if not math.isclose(a[seed]['time_missing_ratio'], b[seed]['time_missing_ratio'], abs_tol=1e-12):
                raise ValueError(f'Unmatched missing-time budget: {pid}')
        ma = statistics.mean(abs(a[s][metric]) for s in expected_seeds)
        mb = statistics.mean(abs(b[s][metric]) for s in expected_seeds)
        people.append({'participant': pid, 'comparator_mae': ma, 'random_mae': mb,
                       'difference': ma - mb,
                       'actual_time_fraction': statistics.mean(a[s]['time_missing_ratio'] for s in expected_seeds)})
    return people


def bootstrap_columns(columns, replicates, seed, confidence=.95):
    """Columns share ordered participant IDs; a draw retains every within-person value."""
    if not columns or len(columns[0]) < 2 or replicates < 2 or not 0 < confidence < 1:
        raise ValueError('Invalid bootstrap dimensions or configuration')
    n = len(columns[0])
    if any(len(c) != n or any(not math.isfinite(v) for v in c) for c in columns):
        raise ValueError('Aligned finite participant columns required')
    rng = random.Random(seed)
    draws = [[] for _ in columns]
    for _ in range(replicates):
        counts = [0] * n
        for _ in range(n):
            counts[rng.randrange(n)] += 1
        for column, samples in zip(columns, draws):
            samples.append(sum(v * k for v, k in zip(column, counts)) / n)
    alpha = (1 - confidence) / 2
    return [(quantile(sorted(samples), alpha), quantile(sorted(samples), 1 - alpha)) for samples in draws]


def main():
    config_path = ROOT / 'docs/paired-analysis-config.json'
    cfg = json.loads(config_path.read_text())
    hashes = {}
    datasets = {}
    for label, relative in [('CGMacros / Dexcom', 'outputs/cgmacros/dexcom/results.json'),
                            ('CGMacros / Libre', 'outputs/cgmacros/libre/results.json'),
                            ('ShanghaiT2DM / v5', 'outputs/shanghai_v5/experiment/results.json')]:
        path = ROOT / relative
        content = path.read_bytes()
        hashes[relative] = hashlib.sha256(content).hexdigest()
        datasets[label] = json.loads(content)['results']
    estimates = []
    for label, rows in datasets.items():
        for ratio in cfg['ratios']:
            for comparator in cfg['comparators']:
                for metric in cfg['metrics']:
                    people = paired_values(rows, ratio, comparator, metric, cfg['simulation_seeds'])
                    estimates.append({'dataset': label, 'requested_ratio': ratio, 'comparator': comparator,
                        'metric': metric, 'unit': 'pp' if metric == 'tir_bias_pp' else 'mg/dL',
                        'primary': ratio == cfg['primary_ratio'] and comparator == 'block' and metric == cfg['primary_metric'],
                        'participants': people})
    for group in ['CGMacros', 'ShanghaiT2DM']:
        selected = [e for e in estimates if e['dataset'].startswith(group)]
        ids = [p['participant'] for p in selected[0]['participants']]
        if any([p['participant'] for p in e['participants']] != ids for e in selected):
            raise ValueError('Participant cohorts differ; cannot use shared cluster draws')
        group_seed = int(hashlib.sha256(f'{cfg["bootstrap_seed"]}|{group}'.encode()).hexdigest(), 16)
        intervals = bootstrap_columns([[p['difference'] for p in e['participants']] for e in selected],
                                      cfg['bootstrap_replicates'], group_seed, cfg['confidence_level'])
        for e, (low, high) in zip(selected, intervals):
            values = [p['difference'] for p in e['participants']]
            e.update(n=len(values), mean_difference=statistics.mean(values), ci_low=low, ci_high=high,
                     positive=sum(v > 1e-12 for v in values), negative=sum(v < -1e-12 for v in values),
                     tied=sum(abs(v) <= 1e-12 for v in values))
    payload = {'config': cfg, 'source_sha256': hashes,
               'config_sha256': hashlib.sha256(config_path.read_bytes()).hexdigest(),
               'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'estimates': estimates}
    (ROOT / 'docs/paired-results.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    lines = ['# Participant-paired missingness comparisons', '',
        'Exploratory extension after inspecting v0.1 results; not preregistered. Generated by `python reproduce.py paired`.', '',
        '## Estimand and interval', '',
        'For each participant, average absolute metric error across simulation seeds separately for each pattern, then subtract random MAE from comparator MAE. Average these paired differences with equal participant weight. Positive values mean larger error under the comparator. Absolute errors are computed before averaging, so signed errors cannot cancel.', '',
        'The 95% percentile bootstrap uses 10,000 participant resamples with replacement, with linear interpolation for quantiles. CGMacros devices share participant draws; all contrasts within a dataset also share draws. Shanghai is resampled separately. Seeds are fixed repeated simulations, not independent participants. Intervals describe participant variation conditional on these selected windows, preprocessing and simulated seeds; they do not account for unknown sensor truth or all simulation uncertainty.', '',
        'Primary analysis: block minus random, TIR MAE, 20% requested deletion, earliest complete 24 hours. Each dataset/device is reported separately; the two CGMacros devices are correlated, not independent replications. Shanghai actual deletion is 19/96 (19.792%); CGMacros is 20%.', '',
        '## Primary results', '',
        '| Dataset/device | People | Paired TIR MAE difference (pp) | 95% CI (pp) | Positive / tied / negative people |',
        '|---|---:|---:|---:|---:|']
    for e in estimates:
        if e['primary']:
            lines.append(f'| {e["dataset"]} | {e["n"]} | {e["mean_difference"]:.3f} | [{e["ci_low"]:.3f}, {e["ci_high"]:.3f}] | {e["positive"]} / {e["tied"]} / {e["negative"]} |')
    lines += ['', 'Ties use an absolute numerical tolerance of 1e-12. An interval excluding zero does not establish clinical importance or remove selection bias. These are pointwise intervals; no familywise coverage, multiplicity correction, p-value or confirmatory significance claim is made.', '',
        '## Secondary analyses', '', 'Other budgets, night-minus-random and mean-glucose contrasts are exploratory. All use the same first 24-hour windows; multi-window confidence intervals are not included in this extension.', '',
        '| Dataset/device | Requested | Comparator − random | Metric unit | Mean difference | 95% pointwise CI |',
        '|---|---:|---|---|---:|---:|']
    for e in estimates:
        if not e['primary']:
            lines.append(f'| {e["dataset"]} | {e["requested_ratio"]:.0%} | {e["comparator"]} | {e["unit"]} | {e["mean_difference"]:.3f} | [{e["ci_low"]:.3f}, {e["ci_high"]:.3f}] |')
    lines += ['', '## Reproduction and limitations', '',
        'Run the underlying CGMacros and Shanghai workflows first, then `python reproduce.py paired`. [Configuration](paired-analysis-config.json) and [participant summaries, intervals and provenance](paired-results.json) are included. The analysis fails on duplicate or missing paired seeds, nonfinite metrics, mismatched time budgets or inconsistent participant sets.', '',
        'Complete-window selection limits generalization; bootstrap resampling does not repair it. CGMacros curves contain interpolation features, and no original dropout mechanism is inferred. No pooled cross-dataset effect is estimated. Derived summaries retain the source-specific licenses described in [data licenses](DATA_LICENSES.md).']
    (ROOT / 'docs/PAIRED_RESULTS.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    for e in estimates:
        if e['primary']:
            print(f'{e["dataset"]}: n={e["n"]}, difference={e["mean_difference"]:.3f} pp, 95% CI [{e["ci_low"]:.3f}, {e["ci_high"]:.3f}]')


if __name__ == '__main__':
    main()
