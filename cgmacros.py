"""Parse released minute-grid CGMacros curves; do not infer original sensor samples."""
import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

DEVICES = {'dexcom': ('Dexcom GL', 5), 'libre': ('Libre GL', 15)}
RELEASED_INTERVAL = 1


def timestamp(value):
    try: return datetime.fromisoformat(value)
    except ValueError: return datetime.strptime(value, '%m/%d/%Y %H:%M')


def parse_file(path):
    series = {device: [] for device in DEVICES}
    missing = Counter()
    count = 0
    previous = None
    with path.open(encoding='utf-8-sig',newline='') as handle:
        reader = csv.DictReader(handle)
        required = {'Timestamp', 'Dexcom GL', 'Libre GL'}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f'{path.name}: missing required columns')
        for row in reader:
            count += 1
            t = timestamp(row['Timestamp'])
            if previous is not None and t <= previous:
                raise ValueError(f'{path.name}: unordered/duplicate timestamp on row {count+1}')
            previous = t
            for device,(column,_) in DEVICES.items():
                raw = row[column].strip()
                if raw.lower() in ('', 'nan', 'na', 'null'):
                    missing[device] += 1
                    continue
                value = float(raw)
                if not math.isfinite(value) or value <= 0:
                    raise ValueError(f'{path.name}: invalid {column} on row {count+1}')
                series[device].append({'timestamp':t.isoformat(),'glucose_mg_dl':value})
    return series, {'csv_rows':count,'empty_cells_by_device':dict(missing)}


def regular_window(rows, interval, hours=24, position='first'):
    """Exact regular window; include terminal observation, no value-based selection."""
    if interval<=0 or hours<=0 or (hours*60)%interval or position not in ('first','last'):
        raise ValueError('Invalid regular-window configuration')
    required = int(hours*60//interval)+1
    start = 0
    found = None
    for i in range(len(rows)):
        if i and (timestamp(rows[i]['timestamp'])-timestamp(rows[i-1]['timestamp'])).total_seconds() != interval*60:
            start = i
        if i-start+1 >= required:
            if position=='first': return rows[start:i+1]
            found = i-required+1
    return rows[found:found+required] if found is not None else None


def quality(rows, interval):
    gaps = [(timestamp(b['timestamp'])-timestamp(a['timestamp'])).total_seconds()/60 for a,b in zip(rows,rows[1:])]
    return {'valid_readings':len(rows),'gap_minutes_counts':dict(sorted(Counter(gaps).items())),
            'median_gap_minutes':statistics.median(gaps) if gaps else None,
            'gaps_exceeding_released_interval':sum(g>interval for g in gaps)}


def agreement(series):
    """Compare forward constant supports on their exact intersection (no time shifting)."""
    intervals = {}
    for device,rows in series.items():
        cap = RELEASED_INTERVAL*60
        intervals[device] = [(timestamp(a['timestamp']),
            min(timestamp(b['timestamp']), timestamp(a['timestamp'])+timedelta(seconds=cap)),
            a['glucose_mg_dl']) for a,b in zip(rows,rows[1:])]
    a,b = intervals['dexcom'], intervals['libre']
    i=j=0
    total=diff=absolute=squared=tir=0.0
    while i<len(a) and j<len(b):
        lo,hi=max(a[i][0],b[j][0]),min(a[i][1],b[j][1])
        duration=max(0,(hi-lo).total_seconds())
        if duration:
            d=a[i][2]-b[j][2]
            total+=duration
            diff+=duration*d
            absolute+=duration*abs(d)
            squared+=duration*d*d
            tir+=duration*(int(70<=a[i][2]<=180)-int(70<=b[j][2]<=180))
        if a[i][1] <= b[j][1]: i+=1
        else: j+=1
    return {'common_supported_minutes':total/60,
            'dexcom_minus_libre_mean_mg_dl':diff/total if total else None,
            'between_device_mae_mg_dl':absolute/total if total else None,
            'between_device_rmse_mg_dl':math.sqrt(squared/total) if total else None,
            'dexcom_minus_libre_tir_pp':100*tir/total if total else None}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw',type=Path,default=Path('data/local/cgmacros/raw'))
    parser.add_argument('--out',type=Path,default=Path('data/local/cgmacros/prepared'))
    args=parser.parse_args()
    paths=sorted(args.raw.glob('CGMacros-*.csv'))
    if not paths: parser.error('No CGMacros participant CSVs found')
    outputs={device:{} for device in DEVICES}
    audit=[]
    for path in paths:
        series, source_quality=parse_file(path)
        pid=path.stem
        libre_by_time={r['timestamp']:r for r in series['libre']}
        common=[r for r in series['dexcom'] if r['timestamp'] in libre_by_time]
        shared_window=regular_window(common,RELEASED_INTERVAL)
        item={'participant':pid,'file_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
              **source_quality,'devices':{},'agreement':agreement(series)}
        for device,(_,interval) in DEVICES.items():
            rows=series[device]
            selected=([r if device=='dexcom' else libre_by_time[r['timestamp']] for r in shared_window]
                      if shared_window else None)
            item['devices'][device]={**quality(rows,RELEASED_INTERVAL),'native_interval_minutes':interval,'included':selected is not None,
                'exclusion_reason':None if selected else 'No common complete released minute-grid 24h window',
                'window_start':selected[0]['timestamp'] if selected else None,
                'window_end':selected[-1]['timestamp'] if selected else None}
            if selected: outputs[device][pid]=selected
        audit.append(item)
    args.out.mkdir(parents=True,exist_ok=True)
    for device,cohort in outputs.items():
        (args.out/f'{device}.json').write_text(json.dumps(cohort),encoding='utf-8')
    payload={'dataset':'CGMacros 1.0.0','license':'CC BY-NC-SA 4.0',
        'adapter_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'selection':'Earliest common complete released minute-grid 24-hour window per participant; same timestamps for both devices; terminal value weight zero',
        'limitation':'Released values include interpolation. This evaluates extra missingness after publication preprocessing, not original sensor dropout.',
        'agreement_method':'All-recording common forward support, capped at 1min; no lag fitting; neither device is ground truth',
        'participants':audit}
    (args.out/'audit.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
    print(json.dumps({'files':len(paths),'included':{d:len(v) for d,v in outputs.items()}},indent=2))


if __name__=='__main__': main()
