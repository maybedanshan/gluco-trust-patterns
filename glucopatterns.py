"""Retrospective meal benchmark; protocol in docs/GLUCOPATTERNS_PROTOCOL.md."""
import csv
import hashlib
import json
import math
import statistics
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from cgmacros import parse_file, timestamp
from paired_analysis import bootstrap_columns

ROOT = Path(__file__).resolve().parent
NUTRIENTS = ['Calories', 'Carbs', 'Protein', 'Fat', 'Fiber']
FEATURES = NUTRIENTS + ['premeal_mean', 'premeal_change_per_minute', 'hour_sin', 'hour_cos']


def meal_vectors(values, nutrition, time):
    """Values indexed by integer minutes; no postmeal value is used as a feature."""
    pre = statistics.mean(values[m] for m in range(-30, 0))
    target = statistics.mean(values[m] for m in range(120)) - pre
    hour = time.hour + time.minute / 60
    features = nutrition + [pre, (values[-1] - values[-30]) / 29,
                             math.sin(hour * math.pi / 12), math.cos(hour * math.pi / 12)]
    return features, target


def audit_file(path):
    series, _ = parse_file(path)
    glucose = {d: {datetime.fromisoformat(r['timestamp']): r['glucose_mg_dl'] for r in rs} for d, rs in series.items()}
    with path.open(encoding='utf-8-sig', newline='') as f:
        meals = [r for r in csv.DictReader(f) if r['Meal Type'].strip()]
    times = [timestamp(r['Timestamp']) for r in meals]
    audit, retained = [], []
    for index, (meal, t) in enumerate(zip(meals, times)):
        reasons = []
        try:
            nutrition = [float(meal[k]) for k in NUTRIENTS]
            valid = all(math.isfinite(v) and v >= 0 for v in nutrition)
        except (ValueError, TypeError):
            valid = False
        if not valid: reasons.append('nutrition_invalid')
        required = [t + timedelta(minutes=m) for m in range(-30, 121)]
        if not all(all(q in glucose[d] for q in required) for d in glucose): reasons.append('dual_window_incomplete')
        if any(t < other <= t + timedelta(minutes=120) for other in times): reasons.append('next_meal_within120')
        if any(t - timedelta(minutes=150) < other < t for other in times): reasons.append('prior_meal_within150')
        meal_id = f'{path.stem}-meal-{index:03d}'
        audit.append({'meal_id': meal_id, 'timestamp': t.isoformat(), 'meal_type': meal['Meal Type'].strip(), 'reasons': reasons})
        if not reasons:
            values = {m: glucose['dexcom'][t + timedelta(minutes=m)] for m in range(-30, 121)}
            features, target = meal_vectors(values, nutrition, t)
            retained.append({'participant': path.stem, 'meal_id': meal_id, 'timestamp': t.isoformat(),
                             'features': features, 'target': target, 'meal_type': meal['Meal Type'].strip()})
    return audit, retained


def history_split(rows, minimum_test=3):
    ordered = sorted(rows, key=lambda r: r['timestamp'])
    if len(ordered) < 10 + minimum_test: return None
    history, test = ordered[:10], ordered[10:]
    if datetime.fromisoformat(history[-1]['timestamp']) + timedelta(minutes=120) > datetime.fromisoformat(test[0]['timestamp']) - timedelta(minutes=30):
        raise ValueError('Adaptation labels overlap test inputs')
    return history, test


def fit_model(train):
    import numpy as np
    if not train: raise ValueError('Empty global training set')
    counts = Counter(r['participant'] for r in train)
    weights = np.array([1 / (len(counts) * counts[r['participant']]) for r in train])
    x = np.array([r['features'] for r in train], dtype=float)
    y = np.array([r['target'] for r in train], dtype=float)
    mean = (x * weights[:, None]).sum(axis=0)
    scale = np.sqrt(((x - mean) ** 2 * weights[:, None]).sum(axis=0))
    scale[scale < 1e-12] = 1
    z = np.column_stack([np.ones(len(x)), (x - mean) / scale])
    penalty = np.eye(z.shape[1]) * 10
    penalty[0, 0] = 0
    beta = np.linalg.solve(z.T @ (weights[:, None] * z) + penalty, z.T @ (weights * y))
    return {'mean': mean, 'scale': scale, 'beta': beta, 'baseline': float(weights @ y)}


def predict(model, row):
    import numpy as np
    z = np.r_[1., (np.asarray(row['features']) - model['mean']) / model['scale']]
    return float(z @ model['beta'])


def adaptation_offset(model, history):
    return sum(r['target'] - predict(model, r) for r in history) / (len(history) + 5)


def main():
    import numpy as np
    raw = ROOT / 'data/local/cgmacros/raw'
    manifest = json.loads((raw / 'manifest.json').read_text())
    out = ROOT / 'outputs/glucopatterns'
    out.mkdir(parents=True, exist_ok=True)
    events, all_rows, audit_summary, source_hashes = [], [], [], {}
    for entry in manifest['files']:
        path = raw / entry['file']
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != entry['sha256']: raise ValueError('Source hash mismatch')
        source_hashes[entry['file']] = digest
        audit, rows = audit_file(path)
        events += audit
        all_rows += rows
        audit_summary.append({'participant': path.stem, 'recorded': len(audit), 'eligible': len(rows),
                              'reasons': dict(Counter(reason for r in audit for reason in r['reasons'])),
                              'meal_types': dict(Counter(r['meal_type'] for r in rows))})
    ids = sorted({r['participant'] for r in all_rows})
    predictions, splits = [], []
    for pid in ids:
        train = [r for r in all_rows if r['participant'] != pid]
        held = [r for r in all_rows if r['participant'] == pid]
        model = fit_model(train)
        fold = {'participant': pid, 'training_participants': sorted({r['participant'] for r in train}),
                'unseen_test': [r['meal_id'] for r in held], 'history': None}
        def record(setting, budget, test, offset=0):
            for r in test:
                predictions.append({'participant': pid, 'meal_id': r['meal_id'], 'setting': setting, 'history_budget': budget,
                    'target': r['target'], 'baseline': model['baseline'], 'pooled': predict(model, r),
                    'personalized': predict(model, r) + offset})
        record('unseen', 0, held)
        split = history_split(held)
        if split:
            history, test = split
            fold['history'] = {'adaptation_by_budget': {str(k): [r['meal_id'] for r in history[:k]] for k in [3, 5, 10]},
                               'test': [r['meal_id'] for r in test]}
            for k in [3, 5, 10]: record('history', k, test, adaptation_offset(model, history[:k]))
        splits.append(fold)
    summary = []
    for setting, budget in [('unseen', 0), ('history', 3), ('history', 5), ('history', 10)]:
        selected = [r for r in predictions if r['setting'] == setting and r['history_budget'] == budget]
        per_person = []
        for pid in sorted({r['participant'] for r in selected}):
            meals = [r for r in selected if r['participant'] == pid]
            per_person.append({'participant': pid, 'meals': len(meals), **{
                m: statistics.mean(abs(r[m] - r['target']) for r in meals) for m in ['baseline', 'pooled', 'personalized']}})
        if len(per_person) < 2: raise ValueError('Insufficient evaluation participants')
        differences = [p['pooled'] - p['personalized'] for p in per_person]
        interval = bootstrap_columns([differences], 10000, 20260914)[0]
        summary.append({'setting': setting, 'history_budget': budget, 'participants': len(per_person), 'meals': len(selected),
                        'macro_mae': {m: statistics.mean(p[m] for p in per_person) for m in ['baseline', 'pooled', 'personalized']},
                        'personalization_improvement': statistics.mean(differences), 'ci95': interval, 'per_person': per_person})
    payload = {'protocol_sha256': hashlib.sha256((ROOT / 'docs/GLUCOPATTERNS_PROTOCOL.md').read_bytes()).hexdigest(),
               'code_sha256': {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in ['glucopatterns.py', 'cgmacros.py', 'paired_analysis.py']},
               'source_sha256': source_hashes, 'numpy_version': np.__version__, 'features': FEATURES,
               'audit': audit_summary, 'evaluations': summary}
    (out / 'audit-events.json').write_text(json.dumps(events, indent=2), encoding='utf-8')
    (out / 'eligible-meals.json').write_text(json.dumps(all_rows), encoding='utf-8')
    (out / 'splits.json').write_text(json.dumps(splits, indent=2), encoding='utf-8')
    (out / 'predictions.json').write_text(json.dumps(predictions), encoding='utf-8')
    payload['local_output_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.json')}
    (ROOT / 'docs/glucopatterns-results.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    lines = ['# GlucoPatterns: first retrospective benchmark', '',
        'Exploratory local results, not a validated prospective prediction system. [Fixed protocol](GLUCOPATTERNS_PROTOCOL.md); source-derived summaries: CC BY-NC-SA 4.0.', '',
        f'Recorded meals: {len(events)}; eligible meals: {len(all_rows)}; eligible participants: {len(ids)}. Reasons overlap, so exclusion columns are not additive. The earlier 1,385 candidate meals used a looser rule without the new prior-meal exclusion.', '',
        '## Separate evaluation settings', '',
        'Outcome: Dexcom released mean glucose during [0,120) minutes minus [-30,0) mean, in mg/dL. Macro MAE weights participants equally. Baseline and pooled training exclude the entire held-out participant. History budgets share the same later test meals, after the first 10 eligible meals. No rolling adaptation.', '',
        '| Setting | History meals | Participants | Test meals | Baseline MAE | Pooled MAE | Personalized MAE | Pooled − personalized MAE, 95% pointwise CI |',
        '|---|---:|---:|---:|---:|---:|---:|---|']
    for s in summary:
        m = s['macro_mae']
        personal = f'{m["personalized"]:.3f}' if s['setting'] == 'history' else 'N/A (equals pooled)'
        effect = f'{s["personalization_improvement"]:.3f} [{s["ci95"][0]:.3f}, {s["ci95"][1]:.3f}]' if s['setting'] == 'history' else 'N/A'
        lines.append(f'| {s["setting"]} | {s["history_budget"]} | {s["participants"]} | {s["meals"]} | {m["baseline"]:.3f} | {m["pooled"]:.3f} | {personal} | {effect} |')
    lines += ['', 'Positive paired improvement favors personalization; negative values favor pooled prediction. Confidence intervals resample participants, not meals. The unseen and history rows use different meals/populations and cannot be directly compared as a history effect. Leave-one-person-out training sets overlap; intervals summarize the observed participant error contrasts conditional on fitted folds, and do not include full model-refitting uncertainty.', '',
        '## Participant meal audit', '',
        '| Participant | Recorded | Eligible | Nutrition invalid | Dual window incomplete | Next meal within 120 min | Prior meal within 150 min |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for a in audit_summary:
        reasons = a['reasons']
        lines.append(f'| {a["participant"]} | {a["recorded"]} | {a["eligible"]} | ' + ' | '.join(str(reasons.get(k, 0)) for k in ['nutrition_invalid', 'dual_window_incomplete', 'next_meal_within120', 'prior_meal_within150']) + ' |')
    lines += ['', '## Reproduction and limits', '',
        '`python -m pip install -r requirements-patterns.txt`, then `python reproduce.py patterns` after downloading CGMacros. Local event exclusions, eligible features/targets, split manifests and per-meal predictions are under `outputs/glucopatterns/`. Aggregate results and provenance are in [glucopatterns-results.json](glucopatterns-results.json).', '',
        'Published interpolation may introduce future information even into nominal premeal values; results are retrospective and cannot establish online forecasting performance. Meal nutrition availability at prediction time is assumed, not verified. Amount Consumed is not reapplied. Unrecorded snacks, medication, activity, prior-meal carryover, constrained breakfast/lunch design and complete-case selection remain limitations. No clinical utility or causal nutrition effect is inferred. No hyperparameters were selected on test outcomes. Libre and external meal-prediction validation remain future work.']
    (ROOT / 'docs/GLUCOPATTERNS_RESULTS.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'recorded_meals': len(events), 'eligible_meals': len(all_rows), 'results': [{k:v for k,v in s.items() if k != 'per_person'} for s in summary]}, indent=2))


if __name__ == '__main__': main()
