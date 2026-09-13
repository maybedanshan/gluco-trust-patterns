"""Describe gaps between raw PhysioCGM EGV timestamps; do not infer disconnection causes."""
import csv
import hashlib
import json
import math
import statistics
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path


def parse_time(value):
    try: return datetime.fromisoformat(value)
    except ValueError: return datetime.strptime(value,'%Y-%m-%d %H:%M:%S')


def gap_events(times, expected_minutes=5, threshold_minutes=7.5):
    times=sorted(set(times))
    return [{'start':(a+timedelta(minutes=expected_minutes)).isoformat(),
             'end':b.isoformat(),'elapsed_between_egv_minutes':(b-a).total_seconds()/60,
             'excess_over_expected_minutes':(b-a).total_seconds()/60-expected_minutes,
             'start_hour':(a+timedelta(minutes=expected_minutes)).hour}
            for a,b in zip(times,times[1:]) if (b-a).total_seconds()/60>threshold_minutes]


def main():
    raw=Path('data/local/physiocgm')
    manifest=json.loads((raw/'manifest.json').read_text(encoding='utf-8'))
    records=[]
    for p in manifest['participants']:
        entry=next(m for m in p['members'] if m['file'].lower()=='cgm.csv')
        path=raw/p['participant']/entry['file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']: raise ValueError('CGM checksum mismatch')
        times=[]
        invalid_values=invalid_times=0
        events=Counter()
        with path.open(encoding='utf-8-sig',newline='') as handle:
            for row in csv.DictReader(handle):
                events[row['Event Type']]+=1
                if row['Event Type']!='EGV': continue
                try: t=parse_time(row['Timestamp (YYYY-MM-DDThh:mm:ss)'])
                except ValueError:
                    invalid_times+=1
                    continue
                times.append(t)
                try: value=float(row['Glucose Value (mg/dL)'])
                except ValueError: value=float('nan')
                invalid_values+=not math.isfinite(value) or value<=0
        if not times: raise ValueError('No timestamped EGV records')
        gaps=gap_events(times)
        records.append({'participant':p['participant'],'event_counts':dict(events),'egv_timestamp_count':len(times),
            'duplicate_egv_timestamps':len(times)-len(set(times)),'non_numeric_or_invalid_egv_values':invalid_values,
            'invalid_egv_timestamps':invalid_times,'start':min(times).isoformat(),'end':max(times).isoformat(),
            'span_days':(max(times)-min(times)).total_seconds()/86400,'gaps':gaps,
            'gap_count':len(gaps),'long_gap_count_over_6h':sum(g['elapsed_between_egv_minutes']>360 for g in gaps)})
    out=Path('outputs/physiocgm')
    out.mkdir(parents=True,exist_ok=True)
    (out/'audit.json').write_text(json.dumps({'source':manifest,'method':'Internal unique EGV timestamp gaps >7.5min; expected interval 5min; exclude no boundary period; do not infer cause',
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'participants':records},indent=2),encoding='utf-8')
    lines=['# PhysioCGM 原始导出时间缺口审查','',
        '数据：10.6084/m9.figshare.28136294.v1，仓库标注 CC0。仅读取 raw ZIP 中的 cgm.csv，没有读取 processed PKL。',
        '论文对缺失的措辞为 “likely due to loss of connectivity”。这是原因推测，不是故障日志验证；不声称本数据集是唯一开放连接缺失数据集。',
        '原始 CGM 导出范围可远超过多模态采集的 24 小时。当前统计整个导出范围，尚未对齐论文的多模态采集窗口，不据此校准正式的掉线模拟参数。','',
        '|参与者|EGV 时间戳数|导出跨度（天）|内部间隔 >7.5 分钟|其中 >6 小时|', '|---|---:|---:|---:|---:|']
    for r in records: lines.append(f"|{r['participant']}|{r['egv_timestamp_count']}|{r['span_days']:.2f}|{r['gap_count']}|{r['long_gap_count_over_6h']}|")
    lines+=['','以 5 分钟为预期频率，超过 7.5 分钟才记为候选时间缺口，容忍秒级抖动。长间隔可能跨越佩戴期或研究阶段；缺口时长是相邻 EGV 间隔减 5 分钟，不是已知掉线时长。',
        '边界之前和之后的缺失不可识别。按唯一 EGV 时间戳计算；非数值血糖另计，未把事件表中的校准、设备、告警当成 CGM 读数。',
        '逐缺口位置与日内起始小时见 audit.json，仅作探索性审查，不进行机制归因。','',
        '来源：[原论文](https://doi.org/10.1038/s41597-025-06090-6)；[数据 v1](https://doi.org/10.6084/m9.figshare.28136294.v1)。']
    (out/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'participants':len(records),'gaps':sum(r['gap_count'] for r in records)}))


if __name__=='__main__': main()
