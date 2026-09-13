"""Read ShanghaiT2DM 20425518.v5 XLS/XLSX and select one full 24h window per person."""
import hashlib
import io
import json
import math
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from cgmacros import regular_window


def workbook_rows(content, extension):
    if extension=='.xlsx':
        import openpyxl
        book=openpyxl.load_workbook(io.BytesIO(content),read_only=True,data_only=True)
        try:
            for sheet in book: yield sheet.title,list(sheet.values)
        finally: book.close()
    else:
        import xlrd
        book=xlrd.open_workbook(file_contents=content)
        try:
            for sheet in book.sheets():
                yield sheet.name,[[xlrd.xldate_as_datetime(c.value,book.datemode) if c.ctype==xlrd.XL_CELL_DATE else c.value for c in sheet.row(i)] for i in range(sheet.nrows)]
        finally: book.release_resources()


def parse_rows(table):
    if not table: raise ValueError('Empty worksheet')
    headers=[str(v).strip() for v in table[0]]
    time_col=headers.index('Date')
    glucose_col=headers.index('CGM (mg / dl)')
    records={}
    missing=duplicates=0
    for row in table[1:]:
        if len(row)<=glucose_col or row[glucose_col] in (None,''):
            missing+=1
            continue
        value=float(row[glucose_col])
        if not math.isfinite(value) or value<=0: raise ValueError('Invalid CGM value')
        t=row[time_col]
        if isinstance(t,str): t=datetime.fromisoformat(t)
        if not isinstance(t,datetime): raise ValueError('CGM without a valid timestamp')
        key=t.isoformat()
        if key in records:
            if records[key]!=value: raise ValueError('Conflicting glucose values at one timestamp')
            duplicates+=1
        records[key]=value
    return [{'timestamp':t,'glucose_mg_dl':v} for t,v in sorted(records.items())], {'rows_without_cgm':missing,'identical_duplicates_collapsed':duplicates}


def main():
    root=Path(__file__).resolve().parent
    raw=root/'data/local/shanghai_v5'
    out=root/'outputs/shanghai_v5'
    out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((raw/'manifest.json').read_text(encoding='utf-8'))
    content=(raw/'diabetes_dataset.zip').read_bytes()
    if hashlib.sha256(content).hexdigest()!=manifest['sha256']: raise ValueError('Source archive changed')
    candidates=defaultdict(list)
    audit=[]
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        names=sorted(n for n in archive.namelist() if n.startswith('Shanghai_T2DM/') and n.endswith(('.xls','.xlsx')))
        for name in names:
            pid=Path(name).stem.split('_')[0]
            data=archive.read(name)
            for sheet,table in workbook_rows(data,Path(name).suffix):
                item={'participant':pid,'member':name,'sheet':sheet,'sha256':hashlib.sha256(data).hexdigest()}
                try:
                    rows,details=parse_rows(table)
                    selected=regular_window(rows,15)
                    gaps=Counter((datetime.fromisoformat(b['timestamp'])-datetime.fromisoformat(a['timestamp'])).total_seconds()/60 for a,b in zip(rows,rows[1:]))
                    item.update(details,valid_readings=len(rows),gap_minutes_counts=dict(sorted(gaps.items())),eligible=selected is not None)
                    if selected: candidates[pid].append((selected[0]['timestamp'],name,sheet,selected))
                except ValueError as e:
                    item.update(eligible=False,error=str(e))
                audit.append(item)
    cohort={pid:min(options,key=lambda v:v[:3])[3] for pid,options in sorted(candidates.items())}
    selected_sources={pid:min(options,key=lambda v:v[:3])[1:3] for pid,options in sorted(candidates.items())}
    ids=sorted({r['participant'] for r in audit})
    (out/'cohort.json').write_text(json.dumps(cohort),encoding='utf-8')
    (out/'audit.json').write_text(json.dumps({'source':manifest,'records':audit,'selected_sources':selected_sources,
        'excluded_participants':sorted(set(ids)-cohort.keys()),'adapter_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2),encoding='utf-8')
    if not cohort: raise ValueError('No eligible participants')
    subprocess.run([sys.executable,str(root/'glucotrust.py'),'--input',str(out/'cohort.json'),'--out',str(out/'experiment'),
        '--support-cap-minutes','15','--source-label','ShanghaiT2DM / 20425518.v5 (2022-09-24)，每人最早完整24小时；同人多记录不作为独立参与者。'],cwd=root,check=True)
    text=(out/'experiment/report.md').read_text(encoding='utf-8')
    summary=f'''# ShanghaiT2DM 外部验证

固定来源：10.6084/m9.figshare.20425518.v5，2022-09-24，CC BY 4.0。
实际读取 {len(names)} 份工作簿、{len(ids)} 人；纳入 {len(cohort)} 人。每人仅选择最早可用完整 24 小时，原始 mg/dL 数值不转换、不插值。
每个窗口 96 个等权 15 分钟支持，加一个零权重终点。请求比例 5%、10%、20% 经四舍五入，对应实际 5/96、10/96、19/96（5.208%、10.417%、19.792%）。同一比例下三种模式删除相同时间，但与 CGMacros 的比例有舍入差异，不应直接当成完全匹配。
多记录按文件名参与者 ID 归组。完整窗口筛选与人群/设备差异限制外推；不能把跨数据集差异全部归因于缺失。
排除参与者：{', '.join(sorted(set(ids)-cohort.keys())) or '无'}。明细见 audit.json。

'''
    (out/'report.md').write_text(summary+text,encoding='utf-8')
    print(json.dumps({'workbooks':len(names),'participants':len(ids),'included':len(cohort),'runs':len(cohort)*90}))


if __name__=='__main__': main()
