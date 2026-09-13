"""Reproducible CGM missingness experiments; Python 3.10+, standard library."""
import argparse
import hashlib
import json
import math
import random
import statistics
import html
from datetime import datetime, timedelta
from pathlib import Path


def weights(rows, cap=5.0):
    """Forward support capped in minutes; terminal reading has no support."""
    if len(rows) < 2 or not math.isfinite(cap) or cap <= 0:
        raise ValueError('Need >=2 readings and positive support cap')
    times = [datetime.fromisoformat(r['timestamp']) for r in rows]
    gaps = [(b-a).total_seconds()/60 for a, b in zip(times, times[1:])]
    if any(g <= 0 for g in gaps):
        raise ValueError('Timestamps must be strictly increasing per participant')
    if any(not math.isfinite(float(r['glucose_mg_dl'])) or float(r['glucose_mg_dl']) <= 0 for r in rows):
        raise ValueError('Glucose must be finite and positive, in mg/dL')
    return [min(g, cap) for g in gaps] + [0.0]


def metrics(rows, w, removed=()):
    removed = set(removed)
    pairs = [(float(r['glucose_mg_dl']), t) for i, (r, t) in enumerate(zip(rows, w)) if i not in removed]
    total = sum(t for _, t in pairs)
    if total <= 0:
        raise ValueError('No observed time remains')
    return {'mean_mg_dl': sum(v*t for v,t in pairs)/total,
            'tir_pct': 100*sum(t for v,t in pairs if 70 <= v <= 180)/total}


def mask(rows, ratio, mode, rng):
    if not 0 <= ratio < 1:
        raise ValueError('Missing ratio must be in [0,1)')
    n = len(rows)-1  # terminal sample has zero duration
    k = round(n*ratio)
    if k >= n:
        raise ValueError('Requested ratio removes all supported samples')
    if mode == 'random':
        return sorted(rng.sample(range(n), k))
    if mode == 'block':
        start = rng.randrange(n-k+1)
        return list(range(start, start+k))
    if mode == 'night':
        candidates = [i for i,r in enumerate(rows[:-1]) if datetime.fromisoformat(r['timestamp']).hour < 6]
        if k > len(candidates):
            raise ValueError('Night window cannot satisfy this missing ratio')
        return sorted(rng.sample(candidates, k))
    raise ValueError('Unknown missingness mode')


def synthetic():
    data = {}
    for p in range(6):
        rng = random.Random(100+p)
        start = datetime(2025,1,1)
        data[f'synthetic-{p+1:02}'] = [
            {'timestamp': (start+timedelta(minutes=5*i)).isoformat(),
             'glucose_mg_dl': round(120+8*p+45*math.sin(2*math.pi*i/288)+rng.gauss(0,12),2)}
            for i in range(288*7+1)]
    return data


def experiment(data, ratios, seeds, cap):
    if not data or not ratios or not seeds:
        raise ValueError('Nonempty data, ratios, and seeds are required')
    if len(set(ratios))!=len(ratios) or len(set(seeds))!=len(seeds):
        raise ValueError('Ratios and seeds must be unique')
    results = []
    for pid, rows in sorted(data.items()):
        w = weights(rows, cap)
        base = metrics(rows,w)
        for ratio in ratios:
            for mode in ['random','block','night']:
                for seed in seeds:
                    key = f'{pid}|{ratio}|{mode}|{seed}'
                    rng = random.Random(int(hashlib.sha256(key.encode()).hexdigest(),16))
                    deleted = mask(rows,ratio,mode,rng)
                    after = metrics(rows,w,deleted)
                    results.append({'participant':pid,'mode':mode,'seed':seed,
                        'requested_ratio':ratio,'point_missing_ratio':len(deleted)/(len(rows)-1),
                        'time_missing_ratio':sum(w[i] for i in deleted)/sum(w),
                        'reference_supported_minutes':sum(w),
                        'mean_bias_mg_dl':after['mean_mg_dl']-base['mean_mg_dl'],
                        'tir_bias_pp':after['tir_pct']-base['tir_pct'],
                        'reference':base,'observed':after,'removed_indices':deleted,
                        'removed_timestamps':[rows[i]['timestamp'] for i in deleted]})
    return results


def report(results, synthetic_data, source_label=None):
    lines = ['# GlucoTrust 实验报告', '',
        '数据：'+(source_label or ('合成数据，仅验证流程，不能推出真实人群结论。' if synthetic_data else '用户提供数据；参考值是原始观测支持上的指标，并非真实完整血糖。')), '',
        '偏差 = 删除后 − 参考值。TIR 单位为百分点；平均血糖单位为 mg/dL。', '',
        '每位参与者先跨种子计算绝对误差均值，再对参与者等权汇总；± 为参与者间标准差，不是置信区间。', '',
        '|模式|请求删点比例|平均血糖 MAE ± SD|TIR MAE ± SD（百分点）|', '|---|---:|---:|---:|']
    for mode, ratio in sorted({(r['mode'],r['requested_ratio']) for r in results}):
        selected = [r for r in results if r['mode']==mode and r['requested_ratio']==ratio]
        values = []
        for metric in ['mean_bias_mg_dl','tir_bias_pp']:
            means = [statistics.mean(abs(r[metric]) for r in selected if r['participant']==p) for p in sorted({r['participant'] for r in selected})]
            values.append(f'{statistics.mean(means):.3f} ± {statistics.stdev(means) if len(means)>1 else 0:.3f}')
        lines.append(f'|{mode}|{ratio:.0%}|{values[0]}|{values[1]}|')
    return '\n'.join(lines)+'\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,help='JSON: participant -> timestamp/glucose_mg_dl records')
    parser.add_argument('--out',type=Path,default=Path('outputs/demo'))
    parser.add_argument('--ratios',type=float,nargs='+',default=[0.05,0.1,0.2])
    parser.add_argument('--seeds',type=int,nargs='+',default=list(range(10)))
    parser.add_argument('--support-cap-minutes',type=float,default=5)
    parser.add_argument('--source-label',help='Dataset/version and preprocessing limitation for report and demo')
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding='utf-8')) if args.input else synthetic()
    if not data:
        parser.error('Empty dataset')
    results = experiment(data,args.ratios,args.seeds,args.support_cap_minutes)
    args.out.mkdir(parents=True,exist_ok=True)
    payload = {'schema_version':'1.0','software_version':'0.1.0','synthetic':args.input is None,'source_label':args.source_label,'support_cap_minutes':args.support_cap_minutes,
        'ratios':args.ratios,'seeds':args.seeds,
        'input_sha256':hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest(),
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'results':results}
    (args.out/'results.json').write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')
    (args.out/'report.md').write_text(report(results,args.input is None,args.source_label),encoding='utf-8')
    template = Path(__file__).with_name('demo.html').read_text(encoding='utf-8')
    compact = [{k:v for k,v in r.items() if k not in ['removed_indices','removed_timestamps']} for r in results]
    embedded = json.dumps(compact,ensure_ascii=True).replace('<','\\u003c')
    label=args.source_label or ('合成数据 · 仅用于流程验证' if args.input is None else '用户数据 · 参考值来自原始观测')
    (args.out/'index.html').write_text(template.replace('/*RESULTS*/[]',embedded).replace('/*SOURCE*/',html.escape(label)),encoding='utf-8')
    print(f'{len(results)} runs -> {args.out.resolve()}')


if __name__ == '__main__':
    main()
