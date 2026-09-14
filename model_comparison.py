"""Nested participant-held-out ridge selection and history-only baseline."""
import hashlib
import json
import math
import statistics
from collections import Counter
from pathlib import Path
from glucopatterns import predict, adaptation_offset
from paired_analysis import bootstrap_columns

ROOT = Path(__file__).resolve().parent
GRID = [.001, .01, .1, 1., 10., 100.]


def fit_ridge(train, penalty):
    import numpy as np
    if not train or not math.isfinite(penalty) or penalty <= 0:
        raise ValueError('Nonempty training data and positive finite penalty required')
    counts = Counter(r['participant'] for r in train)
    w = np.array([1 / (len(counts) * counts[r['participant']]) for r in train])
    x = np.array([r['features'] for r in train], dtype=float)
    y = np.array([r['target'] for r in train], dtype=float)
    if not np.isfinite(x).all() or not np.isfinite(y).all(): raise ValueError('Nonfinite training data')
    mean = (x * w[:, None]).sum(axis=0)
    scale = np.sqrt(((x - mean) ** 2 * w[:, None]).sum(axis=0))
    scale[scale < 1e-12] = 1
    z = np.column_stack([np.ones(len(x)), (x - mean) / scale])
    regularizer = np.eye(z.shape[1]) * penalty
    regularizer[0, 0] = 0
    beta = np.linalg.solve(z.T @ (w[:, None] * z) + regularizer, z.T @ (w * y))
    return {'mean': mean, 'scale': scale, 'beta': beta, 'baseline': float(w @ y)}


def inner_folds(ids):
    ids = sorted(set(ids), key=lambda pid: hashlib.sha256(f'20260916|{pid}'.encode()).hexdigest())
    if len(ids) < 5: raise ValueError('Five training participants required')
    return [ids[i::5] for i in range(5)]


def choose_penalty(train):
    folds = inner_folds(r['participant'] for r in train)
    scores = {p: [] for p in GRID}
    for validation_ids in folds:
        validation_set = set(validation_ids)
        fitting = [r for r in train if r['participant'] not in validation_set]
        for penalty in GRID:
            model = fit_ridge(fitting, penalty)
            for pid in validation_ids:
                errors = [abs(predict(model, r) - r['target']) for r in train if r['participant'] == pid]
                scores[penalty].append(statistics.mean(errors))
    means = {penalty: statistics.mean(values) for penalty, values in scores.items()}
    selected = min(GRID, key=lambda p: (means[p], -p))
    return selected, {'validation_participant_folds': folds, 'candidate_macro_mae': means, 'selected_penalty': selected}


def fit_outer(rows, held_id):
    training = [r for r in rows if r['participant'] != held_id]
    penalty, selection = choose_penalty(training)
    return fit_ridge(training, penalty), fit_ridge(training, 10), selection


def main():
    import numpy as np
    local = ROOT / 'outputs/glucopatterns'
    original = json.loads((ROOT / 'docs/glucopatterns-results.json').read_text())
    for name in ['eligible-meals.json', 'splits.json', 'predictions.json']:
        if hashlib.sha256((local / name).read_bytes()).hexdigest() != original['local_output_sha256'][name]:
            raise ValueError(f'Original benchmark input hash mismatch: {name}')
    rows = json.loads((local / 'eligible-meals.json').read_text())
    splits = json.loads((local / 'splits.json').read_text())
    indexed = {r['meal_id']: r for r in rows}
    predictions, selections = [], []
    for i, split in enumerate(splits):
        pid = split['participant']
        model, fixed, selection = fit_outer(rows, pid)
        selections.append({'held_out': pid, 'training_participants': sorted({r['participant'] for r in rows if r['participant'] != pid}), **selection})
        def record(setting, budget, test_ids, history_ids):
            history = [indexed[mid] for mid in history_ids]
            offset = adaptation_offset(model, history)
            own_mean = statistics.mean(r['target'] for r in history) if history else None
            for mid in test_ids:
                row = indexed[mid]
                pooled = predict(model, row)
                predictions.append({'participant': pid, 'meal_id': mid, 'setting': setting, 'history_budget': budget,
                    'target': row['target'], 'baseline': model['baseline'], 'fixed_pooled': predict(fixed, row),
                    'selected_pooled': pooled, 'personalized': pooled + offset if history else None, 'history_mean': own_mean})
        record('unseen', 0, split['unseen_test'], [])
        if split['history']:
            for k in [3, 5, 10]:
                record('history', k, split['history']['test'], split['history']['adaptation_by_budget'][str(k)])
        if (i + 1) % 10 == 0: print(f'Completed {i+1}/{len(splits)} outer participants', flush=True)
    summaries = []
    for setting, budget in [('unseen', 0), ('history', 3), ('history', 5), ('history', 10)]:
        selected = [r for r in predictions if r['setting'] == setting and r['history_budget'] == budget]
        models = ['baseline', 'fixed_pooled', 'selected_pooled'] + (['personalized', 'history_mean'] if setting == 'history' else [])
        participants = sorted({r['participant'] for r in selected})
        per_person = [{'participant': pid, **{m: statistics.mean(abs(r[m] - r['target']) for r in selected if r['participant'] == pid) for m in models}} for pid in participants]
        contrasts = [('baseline', 'selected_pooled'), ('fixed_pooled', 'selected_pooled')]
        if setting == 'history': contrasts += [('selected_pooled', 'personalized'), ('history_mean', 'personalized')]
        differences = [[p[a] - p[b] for p in per_person] for a, b in contrasts]
        intervals = bootstrap_columns(differences, 10000, 20260916)
        summaries.append({'setting': setting, 'history_budget': budget, 'n': len(participants), 'meals': len(selected),
                          'macro_mae': {m: statistics.mean(p[m] for p in per_person) for m in models}, 'per_person': per_person,
                          'contrasts': [{'comparison': a+' minus '+b, 'mean': statistics.mean(d), 'ci95': ci} for (a,b),d,ci in zip(contrasts,differences,intervals)]})
    out = ROOT / 'outputs/model_comparison'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'predictions.json').write_text(json.dumps(predictions), encoding='utf-8')
    (out / 'selection.json').write_text(json.dumps(selections, indent=2), encoding='utf-8')
    paths = [local / name for name in ['eligible-meals.json','splits.json','predictions.json']]
    paths += [ROOT / 'docs/MODEL_COMPARISON_PROTOCOL.md', ROOT / 'model_comparison.py', ROOT / 'glucopatterns.py', ROOT / 'paired_analysis.py', out / 'predictions.json', out / 'selection.json']
    payload = {'grid': GRID, 'numpy_version': np.__version__, 'sha256': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
               'selected_penalties': dict(Counter(str(s['selected_penalty']) for s in selections)), 'evaluations': summaries}
    (ROOT / 'docs/model-comparison-results.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    lines = ['# Model comparison with inner participant validation', '',
        '[Protocol](MODEL_COMPARISON_PROTOCOL.md). Exploratory retrospective extension after inspecting v1; not external validation or a confirmatory study. Source-derived results: CC BY-NC-SA 4.0.', '',
        'Penalties are selected using only other participants in five inner folds. All centering/scaling is fitted inside each training fold. History means and personal residual offsets use only early labels. Outer test meals never enter selection. Errors are participant-macro MAE in mg/dL.', '',
        '| Setting | History meals | People | Test meals | Mean baseline | Fixed ridge (10) | Selected ridge | Personalized selected ridge | History-only mean |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for s in summaries:
        m = s['macro_mae']
        cells = [f'{m[k]:.3f}' if k in m else 'N/A' for k in ['baseline','fixed_pooled','selected_pooled','personalized','history_mean']]
        lines.append(f'| {s["setting"]} | {s["history_budget"]} | {s["n"]} | {s["meals"]} | ' + ' | '.join(cells) + ' |')
    lines += ['', '## Paired improvements', '', 'Positive values favor the second model in each comparison. Intervals are 95% pointwise participant-bootstrap intervals conditional on fitted folds; no familywise or full-refitting uncertainty is claimed.', '',
              '| Setting | History meals | First minus second | Mean improvement (mg/dL) | 95% CI |', '|---|---:|---|---:|---|']
    for s in summaries:
        for c in s['contrasts']:
            lines.append(f'| {s["setting"]} | {s["history_budget"]} | {c["comparison"]} | {c["mean"]:.3f} | [{c["ci95"][0]:.3f}, {c["ci95"][1]:.3f}] |')
    lines += ['', '## Selection and interpretation', '', 'Selected penalties across outer folds: ' + json.dumps(payload['selected_penalties']) + '.', '',
        'Unseen and history settings use different meal sets; compare models within a setting. History budgets share identical later meals. The history-only model tests whether early labels alone explain the benefit; do not attribute all gains to nutrition features or a sophisticated personal model.', '',
        'Published interpolation and unknown nutrition-record availability prevent a prospective forecasting claim. Complete-case selection, small cohort and overlapping training folds limit generalization. Selection targets unseen-person MAE, not personalized later-meal MAE. The first missingness report still uses the fixed-penalty v1 model; its effects cannot be transferred to this selected model without another experiment.', '',
        '## Reproduction', '', '`python reproduce.py compare` after `python reproduce.py patterns`. NumPy is required. Exact original splits are reused; local candidate scores and inner-fold participant IDs are in `outputs/model_comparison/selection.json`, and per-meal predictions in `outputs/model_comparison/predictions.json`. [Aggregate results and hashes](model-comparison-results.json) are public; meal-level files stay local.']
    (ROOT / 'docs/MODEL_COMPARISON_RESULTS.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps({'selected_penalties': payload['selected_penalties'], 'results': [{k:v for k,v in s.items() if k != 'per_person'} for s in summaries]}, indent=2))


if __name__ == '__main__': main()
