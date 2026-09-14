"""Matched input-only, label-only and joint historical degradation experiments."""
import hashlib
import json
import math
import random
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from cgmacros import parse_file
from glucotrust import mask
from glucopatterns import predict, adaptation_offset
from history_missingness import degrade_meal
from model_comparison import fit_ridge
from paired_analysis import bootstrap_columns

ROOT=Path(__file__).resolve().parent
THRESHOLDS=[.5,.7,.9]
ARMS=['input_only','label_only','joint']


def damaged_label(meal, glucose, deleted, post_threshold):
    if post_threshold not in THRESHOLDS: raise ValueError('Unsupported prespecified threshold')
    t=datetime.fromisoformat(meal['timestamp'])
    pre=[t+timedelta(minutes=m) for m in range(-30,0)]
    post=[t+timedelta(minutes=m) for m in range(120)]
    if any(q not in glucose for q in pre+post): raise ValueError('Reference support incomplete')
    kept_pre=[q for q in pre if q not in deleted]
    kept_post=[q for q in post if q not in deleted]
    label=None
    if len(kept_pre)>=15 and len(kept_post)>=round(120*post_threshold):
        label=statistics.mean(glucose[q] for q in kept_post)-statistics.mean(glucose[q] for q in kept_pre)
    return label,len(kept_pre),len(kept_post)


def histories(history,glucose,deleted,threshold):
    arms={arm:[] for arm in ARMS}
    diagnostics=[]
    for meal in history:
        feature,_=degrade_meal(meal,glucose,deleted)
        label,pre,post=damaged_label(meal,glucose,deleted,threshold)
        if feature is not None: arms['input_only'].append(feature)
        if label is not None:
            arms['label_only'].append({**meal,'target':label})
            if feature is not None: arms['joint'].append({**feature,'target':label})
        diagnostics.append({'meal_id':meal['meal_id'],'pre_minutes':pre,'post_minutes':post,
                            'label_error':None if label is None else label-meal['target']})
    return arms,diagnostics


def main():
    upstream=ROOT/'docs/model-comparison-results.json'
    provenance={}
    for relative,digest in json.loads(upstream.read_text())['sha256'].items():
        if hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()!=digest: raise ValueError('Upstream changed: '+relative)
        provenance[relative]=digest
    base=ROOT/'outputs/glucopatterns'
    meals=json.loads((base/'eligible-meals.json').read_text())
    indexed={r['meal_id']:r for r in meals}
    splits=json.loads((base/'splits.json').read_text())
    selections={r['held_out']:r for r in json.loads((ROOT/'outputs/model_comparison/selection.json').read_text())}
    raw=ROOT/'data/local/cgmacros/raw'
    entries={Path(e['file']).stem:e for e in json.loads((raw/'manifest.json').read_text())['files']}
    out=ROOT/'outputs/label_missingness';out.mkdir(parents=True,exist_ok=True)
    runs=[]
    with (out/'label-diagnostics.jsonl').open('w',encoding='utf-8') as handle:
        for fold in splits:
            if not fold['history']:continue
            pid=fold['participant']
            training=[r for r in meals if r['participant']!=pid]
            if sorted({r['participant'] for r in training})!=selections[pid]['training_participants']:raise ValueError('Training cohort changed')
            model=fit_ridge(training,selections[pid]['selected_penalty'])
            history=[indexed[mid] for mid in fold['history']['adaptation_by_budget']['10']]
            test=[indexed[mid] for mid in fold['history']['test']]
            residuals=[predict(model,r)-r['target'] for r in test]
            pooled=statistics.mean(abs(v) for v in residuals)
            clean_offset=adaptation_offset(model,history)
            clean=statistics.mean(abs(v+clean_offset) for v in residuals)
            entry=entries[pid];path=raw/entry['file']
            if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:raise ValueError('Raw source changed')
            provenance[path.relative_to(ROOT).as_posix()]=entry['sha256']
            series,_=parse_file(path)
            glucose={datetime.fromisoformat(r['timestamp']):r['glucose_mg_dl'] for r in series['dexcom']}
            start=datetime.fromisoformat(history[0]['timestamp'])-timedelta(minutes=30)
            stop=datetime.fromisoformat(history[-1]['timestamp'])+timedelta(minutes=120)
            first_test=min(datetime.fromisoformat(r['timestamp']) for r in test)-timedelta(minutes=30)
            if stop>first_test:raise ValueError('History mask overlaps later test inputs')
            timeline=sorted(q for q in glucose if start<=q<stop)
            mask_rows=[{'timestamp':q.isoformat()} for q in timeline]+[{'timestamp':stop.isoformat()}]
            for ratio in [0.,.05,.1,.2]:
                for mode in ['random','block','night']:
                    for seed in range(10):
                        key=f'{pid}|history-label-v1|{ratio}|{mode}|{seed}'
                        common={'participant':pid,'ratio':ratio,'mode':mode,'seed':seed,'test_meals':len(test),
                                'pooled_mae':pooled,'clean_mae':clean,'timeline_minutes':len(timeline)}
                        if mode=='night' and round(len(timeline)*ratio)>sum(q.hour<6 for q in timeline):
                            for threshold in THRESHOLDS:
                                for arm in ARMS:runs.append({**common,'post_threshold':threshold,'arm':arm,'status':'infeasible_night_budget'})
                            continue
                        indices=mask(mask_rows,ratio,mode,random.Random(int(hashlib.sha256(key.encode()).hexdigest(),16)))
                        deleted={timeline[i] for i in indices}
                        mask_hash=hashlib.sha256(json.dumps(indices).encode()).hexdigest()
                        for threshold in THRESHOLDS:
                            adapted,diags=histories(history,glucose,deleted,threshold)
                            handle.write(json.dumps({**common,'post_threshold':threshold,'mask_indices_sha256':mask_hash,'meals':diags})+'\n')
                            errors=[d['label_error'] for d in diags if d['label_error'] is not None]
                            arm_errors={}
                            for arm in ARMS:
                                offset=adaptation_offset(model,adapted[arm])
                                mae=statistics.mean(abs(v+offset) for v in residuals)
                                arm_errors[arm]=mae
                                runs.append({**common,'post_threshold':threshold,'arm':arm,'status':'ok','personalized_mae':mae,
                                    'cost':mae-clean,'benefit':pooled-mae,'offset':offset,'usable_history':len(adapted[arm]),
                                    'premeal_missing_fraction':1-sum(d['pre_minutes'] for d in diags)/300,
                                    'postmeal_missing_fraction':1-sum(d['post_minutes'] for d in diags)/1200,
                                    'actual_timeline_fraction':len(indices)/len(timeline),'mask_indices_sha256':mask_hash,
                                    'valid_label_count':len(errors),'label_error_sum':sum(errors),'label_abs_error_sum':sum(abs(v) for v in errors),
                                    'label_max_abs_error':max((abs(v) for v in errors),default=None)})
                            for r in runs[-3:]:
                                r['joint_minus_input']=arm_errors['joint']-arm_errors['input_only']
                                r['joint_minus_label']=arm_errors['joint']-arm_errors['label_only']
    summaries=[]
    ids=sorted({r['participant'] for r in runs})
    grouped={}
    for r in runs:grouped.setdefault((r['post_threshold'],r['ratio'],r['mode'],r['arm']),[]).append(r)
    for (threshold,ratio,mode,arm),rs in sorted(grouped.items()):
        base_summary={'post_threshold':threshold,'ratio':ratio,'mode':mode,'arm':arm,'n':len(ids)}
        if any(r['status']!='ok' for r in rs):
            summaries.append({**base_summary,'status':'incomplete',
                'infeasible_runs':sum(r['status']!='ok' for r in rs),
                'infeasible_people':len({r['participant'] for r in rs if r['status']!='ok'})});continue
        people=[]
        numeric=['personalized_mae','pooled_mae','clean_mae','cost','benefit','usable_history','premeal_missing_fraction','postmeal_missing_fraction','actual_timeline_fraction','joint_minus_input','joint_minus_label']
        for pid in ids:
            pr=[r for r in rs if r['participant']==pid]
            if len(pr)!=10 or {r['seed'] for r in pr}!=set(range(10)):raise ValueError('Incomplete seeds')
            count=sum(r['valid_label_count'] for r in pr)
            people.append({'participant':pid,**{k:statistics.mean(r[k] for r in pr) for k in numeric},
                'valid_labels_over_seeds':count,'label_bias':sum(r['label_error_sum'] for r in pr)/count if count else None,
                'label_mae':sum(r['label_abs_error_sum'] for r in pr)/count if count else None})
        valid=[p for p in people if p['label_mae'] is not None]
        summaries.append({**base_summary,'status':'complete','per_person':people,**{k:statistics.mean(p[k] for p in people) for k in numeric},
            'label_evaluable_people':len(valid),'valid_labels_over_seeds':sum(p['valid_labels_over_seeds'] for p in people),
            'label_bias':statistics.mean(p['label_bias'] for p in valid) if valid else None,
            'label_mae':statistics.mean(p['label_mae'] for p in valid) if valid else None,
            'label_max_abs_error':max((r['label_max_abs_error'] for r in rs if r['label_max_abs_error'] is not None),default=None)})
    complete=[s for s in summaries if s['status']=='complete']
    # One draw sequence for all arms/thresholds and both paired contrasts.
    keys=['benefit','cost','joint_minus_input','joint_minus_label']
    intervals=iter(bootstrap_columns([[p[k] for p in s['per_person']] for s in complete for k in keys],10000,20260918))
    for s in complete:s['ci95']={k:next(intervals) for k in keys}
    (out/'runs.json').write_text(json.dumps(runs),encoding='utf-8')
    for p in [ROOT/'label_missingness.py',ROOT/'docs/LABEL_MISSINGNESS_PROTOCOL.md',ROOT/'glucotrust.py',ROOT/'cgmacros.py',ROOT/'history_missingness.py',out/'runs.json',out/'label-diagnostics.jsonl']:
        provenance[p.relative_to(ROOT).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    result={'config':{'post_thresholds':THRESHOLDS,'primary_post_threshold':.7,'minimum_pre_minutes':15,'bootstrap_replicates':10000,'bootstrap_seed':20260918},
            'sha256':provenance,'people':len(ids),'test_meals':sum(len(f['history']['test']) for f in splits if f['history']),
            'mask_configurations':len(ids)*4*3*10,'arm_threshold_evaluations':len(runs),'summaries':summaries}
    (ROOT/'docs/label-missingness-results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    lines=['# Historical input and label missingness','',
        '[Protocol](LABEL_MISSINGNESS_PROTOCOL.md). Exploratory retrospective experiment; CGMacros-derived summaries are CC BY-NC-SA 4.0. The released v0.2 archive is unchanged.','',
        f'{len(ids)} people; {result["test_meals"]} fixed later test meals; {result["mask_configurations"]:,} masks shared across three arms and three coverage thresholds ({len(runs):,} evaluations, not independent samples). The mask timeline now includes the final historical outcome window and differs from earlier input-only experiments.','',
        'Primary label coverage: at least 15/30 premeal minutes and 84/120 postmeal minutes. Labels recompute both retained-window means. Label-only keeps features clean but allows the target baseline to change; joint degradation changes both. All prediction errors and label errors below are mg/dL. Positive benefit favors personalization; positive cost means worse than clean-history personalization.','',
        '## Primary 70% postmeal coverage results','',
        '| Requested | Pattern | Arm | Usable history | Prediction MAE | Benefit [95% CI] | Cost [95% CI] |',
        '|---|---|---|---:|---:|---|---|']
    def effect(s,k):return f'{s[k]:.3f} [{s["ci95"][k][0]:.3f}, {s["ci95"][k][1]:.3f}]'
    for s in summaries:
        if s['post_threshold']!=.7:continue
        if s['status']!='complete':lines.append(f'| {s["ratio"]:.0%} | {s["mode"]} | {s["arm"]} | Infeasible: {s["infeasible_people"]} people / {s["infeasible_runs"]} runs | — | — | — |');continue
        lines.append(f'| {s["ratio"]:.0%} | {s["mode"]} | {s["arm"]} | {s["usable_history"]:.2f} | {s["personalized_mae"]:.3f} | {effect(s,"benefit")} | {effect(s,"cost")} |')
    lines+=['','## Label errors and threshold sensitivity at 20% timeline missingness','',
        'Label errors are conditional on labels passing coverage; stricter selection may lower apparent label error while losing useful history. Counts include repeated masks/seeds, not unique meals. Label diagnostics are identical across arms; only one copy is shown. Complete per-person summaries and other budgets are in the JSON.','',
        '| Required post coverage | Pattern | Pre / post exposure | Label-evaluable people | Valid labels / 4400 | Label bias | Label MAE | Max absolute label error | Joint usable meals | Joint prediction MAE | Joint benefit [95% CI] |',
        '|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|']
    for s in complete:
        if s['ratio']!=.2 or s['arm']!='joint':continue
        fmt=lambda v:'N/A' if v is None else f'{v:.3f}'
        lines.append(f'| {s["post_threshold"]:.0%} | {s["mode"]} | {s["premeal_missing_fraction"]:.1%} / {s["postmeal_missing_fraction"]:.1%} | {s["label_evaluable_people"]} | {s["valid_labels_over_seeds"]} | {fmt(s["label_bias"])} | {fmt(s["label_mae"])} | {fmt(s["label_max_abs_error"])} | {s["usable_history"]:.2f} | {s["personalized_mae"]:.3f} | {effect(s,"benefit")} |')
    lines+=['','## Paired arm differences: primary threshold, 20% missingness','', '| Pattern | Joint minus input-only MAE [95% CI] | Joint minus label-only MAE [95% CI] |','|---|---|---|']
    for s in complete:
        if s['post_threshold']==.7 and s['ratio']==.2 and s['arm']=='joint':lines.append(f'| {s["mode"]} | {effect(s,"joint_minus_input")} | {effect(s,"joint_minus_label")} |')
    lines+=['','## Limits and reproduction','',
        'Do not compare these aggregate values directly with old masks to estimate a label effect: the timeline changed. Within this experiment all arms use the same masks and tests. Costs combine measurement damage and adaptation availability. Intervals are pointwise and conditional on fitted folds. Source interpolation, unknown meal metadata timing, small sample and complete-case selection remain limitations. No clinical or prospective forecasting claim is supported.','',
        'Run `python reproduce.py labels` after `patterns` and `compare`. Local label diagnostics (including unavailable labels as null), per-run offsets, metrics and mask hashes are in `outputs/label_missingness/`. [Aggregate results and provenance](label-missingness-results.json). The stable v0.2 `full` workflow remains unchanged; this is an additional study.']
    (ROOT/'docs/LABEL_MISSINGNESS_RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps([{k:v for k,v in s.items() if k!='per_person'} for s in complete if s['post_threshold']==.7 and s['ratio']==.2],indent=2))


if __name__=='__main__':main()
