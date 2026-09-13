"""Audit meal readiness and sensitivity to complete-window duration and position."""
import csv
import hashlib
import json
import math
import statistics
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from cgmacros import parse_file, regular_window
from glucotrust import experiment


def meals_audit(path, series):
    with path.open(encoding='utf-8-sig',newline='') as handle:
        meals=[r for r in csv.DictReader(handle) if r['Meal Type'].strip()]
    times=[datetime.fromisoformat(r['Timestamp']) for r in meals]
    available={d:{r['timestamp'] for r in rows} for d,rows in series.items()}
    rows=[]
    for meal,t in zip(meals,times):
        valid=True
        for key in ['Calories','Carbs','Protein','Fat','Fiber']:
            try: value=float(meal[key])
            except ValueError: value=float('nan')
            valid=valid and math.isfinite(value) and value>=0
        required={(t+timedelta(minutes=m)).isoformat() for m in range(-30,121)}
        coverage={d:required.issubset(values) for d,values in available.items()}
        overlap=any(t<other<=t+timedelta(minutes=120) for other in times)
        rows.append({'timestamp':t.isoformat(),'meal_type':meal['Meal Type'].strip(),
            'macros_complete_nonnegative':valid,'complete_minus30_plus120':coverage,
            'another_meal_within_120min':overlap,'candidate':valid and all(coverage.values()) and not overlap})
    return {'participant':path.stem,'recorded_meals':len(rows),'meal_type_counts':dict(Counter(r['meal_type'] for r in rows)),
        'complete_macros':sum(r['macros_complete_nonnegative'] for r in rows),
        'complete_dual_cgm_window':sum(all(r['complete_minus30_plus120'].values()) for r in rows),
        'candidate_meals':sum(r['candidate'] for r in rows),'meals':rows}


def main():
    raw=Path('data/local/cgmacros/raw')
    manifest=json.loads((raw/'manifest.json').read_text(encoding='utf-8'))
    out=Path('outputs/cgmacros_audit')
    out.mkdir(parents=True,exist_ok=True)
    all_results=[]
    meals=[]
    windows=[]
    for index,entry in enumerate(manifest['files']):
        path=raw/entry['file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']: raise ValueError('Source checksum mismatch')
        series,_=parse_file(path)
        meals.append(meals_audit(path,series))
        libre={r['timestamp']:r for r in series['libre']}
        common=[r for r in series['dexcom'] if r['timestamp'] in libre]
        for hours in [24,48,72]:
            for position in ['first','last']:
                selected=regular_window(common,1,hours,position)
                window={'participant':path.stem,'hours':hours,'position':position,'included':selected is not None,
                    'start':selected[0]['timestamp'] if selected else None,'end':selected[-1]['timestamp'] if selected else None}
                windows.append(window)
                if selected:
                    for device in ['dexcom','libre']:
                        readings=selected if device=='dexcom' else [libre[r['timestamp']] for r in selected]
                        for r in experiment({path.stem:readings},[.05,.1,.2],list(range(10)),1):
                            compact={k:v for k,v in r.items() if k not in ('removed_indices','removed_timestamps')}
                            all_results.append({**compact,'hours':hours,'position':position,'device':device})
        if (index+1)%10==0: print(f'Audited {index+1} participants',flush=True)
    payload={'source_manifest':manifest,'code_sha256':{n:hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in ['audit_cgmacros.py','cgmacros.py','glucotrust.py']},
        'windows':windows,'results':all_results,'limitation':'Processed curves; nested/overlapping windows and shared participants are not independent replicates.'}
    (out/'robustness.json').write_text(json.dumps(payload),encoding='utf-8')
    (out/'meals.json').write_text(json.dumps(meals,indent=2),encoding='utf-8')
    lines=['# CGMacros 稳健性与餐次审查','',
        '使用发布的一分钟曲线。比较最早/最晚完整的双设备共同窗口，时长为 24、48、72 小时；每个设置保持参与者等权。窗口可重叠，不能作为独立样本。',
        '下表聚焦请求 20% 缺失的 TIR 平均绝对误差（百分点）；5%、10% 和逐种子结果见 robustness.json。不同设置的纳入人群可能不同，变化同时包含窗口与筛选效应。','',
        '|设备|窗口小时|位置|纳入人数|随机缺失 MAE|连续缺失 MAE|夜间缺失 MAE|','|---|---:|---|---:|---:|---:|---:|']
    for device in ['dexcom','libre']:
        for hours in [24,48,72]:
            for position in ['first','last']:
                subset=[r for r in all_results if r['device']==device and r['hours']==hours and r['position']==position and r['requested_ratio']==.2]
                values=[statistics.mean(abs(r['tir_bias_pp']) for r in subset if r['mode']==mode) for mode in ['random','block','night']]
                lines.append(f'|{device}|{hours}|{position}|{len({r["participant"] for r in subset})}|'+ '|'.join(f'{v:.3f}' for v in values)+'|')
    lines+=['','## 餐次盘点','',
        '45 人是现有数据人数，4 个未完成 ID 不在这 45 人内。候选餐定义：五个营养字段有限且非负、双设备餐前 30 至餐后 120 分钟的发布值完整、随后 120 分钟无其他已记录餐次。',
        '候选餐不是已验证训练标签；未处理进食持续时间、未记录零食、用药与活动混杂，也未验证 Amount Consumed 是否已体现在营养量中。此处不重复缩放营养值。','',
        '|参与者|记录餐次|营养完整|双设备窗口完整|候选餐次|','|---|---:|---:|---:|---:|']
    for r in meals: lines.append(f'|{r["participant"]}|{r["recorded_meals"]}|{r["complete_macros"]}|{r["complete_dual_cgm_window"]}|{r["candidate_meals"]}|')
    lines+=['',f'合计：{sum(r["recorded_meals"] for r in meals)} 个记录餐次，{sum(r["candidate_meals"] for r in meals)} 个候选餐次。',
        '数据与派生产物：CC BY-NC-SA 4.0。来源：[CGMacros 1.0.0](https://physionet.org/content/cgmacros/1.0.0/)。']
    (out/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'runs':len(all_results),'recorded_meals':sum(r['recorded_meals'] for r in meals),'candidate_meals':sum(r['candidate_meals'] for r in meals)}))


if __name__=='__main__': main()
