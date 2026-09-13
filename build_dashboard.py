"""Build the offline v0.1 explorer from result JSON; embed summaries, not glucose traces."""
import argparse
import hashlib
import json
import os
import statistics
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def summarize(results, dataset, label, window, note):
    grouped=defaultdict(list)
    seeds=defaultdict(list)
    for r in results:
        grouped[(r['participant'],r['mode'],r['requested_ratio'])].append(r)
        seeds[(r['seed'],r['mode'],r['requested_ratio'])].append(r)
    people=[]
    for (pid,mode,ratio),rs in sorted(grouped.items()):
        people.append({'participant':pid,'mode':mode,'ratio':ratio,
            'actual':statistics.mean(r['time_missing_ratio'] for r in rs),
            'mean_bias':statistics.mean(r['mean_bias_mg_dl'] for r in rs),
            'tir_bias':statistics.mean(r['tir_bias_pp'] for r in rs),
            'mean_mae':statistics.mean(abs(r['mean_bias_mg_dl']) for r in rs),
            'tir_mae':statistics.mean(abs(r['tir_bias_pp']) for r in rs)})
    seed_results=[{'seed':seed,'mode':mode,'ratio':ratio,
        'mean_mae':statistics.mean(abs(r['mean_bias_mg_dl']) for r in rs),
        'tir_mae':statistics.mean(abs(r['tir_bias_pp']) for r in rs)} for (seed,mode,ratio),rs in sorted(seeds.items())]
    return {'id':dataset+'-'+window,'dataset':dataset,'label':label,'window':window,'note':note,
        'people':len({r['participant'] for r in results}),'runs':len(results),
        'ratios':sorted({r['requested_ratio'] for r in results}),'seeds':sorted({r['seed'] for r in results}),
        'participants':people,'seed_results':seed_results}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo-only',action='store_true')
    parser.add_argument('--out',type=Path,default=ROOT/'docs/demo/index.html')
    args=parser.parse_args()
    cohorts=[]
    sources={}
    def read(relative):
        path=ROOT/relative
        sources[relative]=hashlib.sha256(path.read_bytes()).hexdigest()
        return json.loads(path.read_text(encoding='utf-8'))
    if not args.demo_only:
        robust=ROOT/'outputs/cgmacros_audit/robustness.json'
        if robust.exists():
            results=read('outputs/cgmacros_audit/robustness.json')['results']
            for device in ['dexcom','libre']:
                for hours in [24,48,72]:
                    for position in ['first','last']:
                        rs=[r for r in results if r['device']==device and r['hours']==hours and r['position']==position]
                        if rs: cohorts.append(summarize(rs,'cgmacros-'+device,'CGMacros / '+device.title(),f'{hours} h · {position}',
                            'Processed minute-grid curves with interpolation features. Extra missingness after preprocessing; not original device dropout. Data-derived results: CC BY-NC-SA 4.0.'))
        else:
            for device in ['dexcom','libre']:
                relative=f'outputs/cgmacros/{device}/results.json'
                if (ROOT/relative).exists(): cohorts.append(summarize(read(relative)['results'],'cgmacros-'+device,'CGMacros / '+device.title(),'24 h · first','Processed minute-grid curves; not original device dropout. CC BY-NC-SA 4.0.'))
        relative='outputs/shanghai_v5/experiment/results.json'
        if (ROOT/relative).exists(): cohorts.append(summarize(read(relative)['results'],'shanghai','ShanghaiT2DM / v5','24 h · first',
            '100 participants; 109 workbooks grouped by person. 15-minute support: requested 5/10/20% becomes actual 5.208/10.417/19.792%. CC BY 4.0.'))
    relative='outputs/demo/results.json'
    if (ROOT/relative).exists(): cohorts.append(summarize(read(relative)['results'],'synthetic','Synthetic / workflow demo','7 days',
        'Synthetic data only. Demonstrates the software pipeline; no real-population inference.'))
    if not cohorts: raise ValueError('No results found. Run python reproduce.py demo first.')
    args.out.parent.mkdir(parents=True,exist_ok=True)
    payload=json.dumps(cohorts,separators=(',',':'),ensure_ascii=True).replace('<','\\u003c')
    page=(ROOT/'release_dashboard.html').read_text(encoding='utf-8').replace('__PAYLOAD__',payload)
    docs_relative=Path(os.path.relpath(ROOT/'docs',args.out.resolve().parent)).as_posix()
    page=page.replace('href="../','href="'+docs_relative+'/')
    args.out.write_text(page,encoding='utf-8')
    (args.out.parent/'provenance.json').write_text(json.dumps({'release':'0.1.0','source_result_sha256':sources,
        'builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'template_sha256':hashlib.sha256((ROOT/'release_dashboard.html').read_bytes()).hexdigest(),
        'notes':'Only derived participant/seed summaries embedded; no glucose traces, meal events, or original timestamps.'},indent=2),encoding='utf-8')
    print(f'{len(cohorts)} cohort/window views -> {args.out}')


if __name__=='__main__': main()
