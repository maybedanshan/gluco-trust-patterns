"""Reproduce the CGMacros processed-curve pilot after fetch_cgmacros.py."""
import hashlib
import json
import statistics
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def main():
    raw=ROOT/'data/local/cgmacros/raw'
    manifest=json.loads((raw/'manifest.json').read_text(encoding='utf-8'))
    if len(manifest['files'])!=45: raise ValueError('Full 45-file manifest required')
    for entry in manifest['files']:
        if hashlib.sha256((raw/entry['file']).read_bytes()).hexdigest()!=entry['sha256']:
            raise ValueError(f"Source checksum mismatch: {entry['file']}")
    subprocess.run([sys.executable,str(ROOT/'cgmacros.py')],cwd=ROOT,check=True)
    prepared=ROOT/'data/local/cgmacros/prepared'
    datasets={d:json.loads((prepared/f'{d}.json').read_text(encoding='utf-8')) for d in ['dexcom','libre']}
    if not datasets['dexcom'] or datasets['dexcom'].keys()!=datasets['libre'].keys():
        raise ValueError('Matched nonempty device cohorts required')
    for pid,rows in datasets['dexcom'].items():
        if [r['timestamp'] for r in rows]!=[r['timestamp'] for r in datasets['libre'][pid]]:
            raise ValueError('Device windows are not matched')
    for device in datasets:
        subprocess.run([sys.executable,str(ROOT/'glucotrust.py'),'--input',str(prepared/f'{device}.json'),
            '--out',str(ROOT/f'outputs/cgmacros/{device}'),'--support-cap-minutes','1',
            '--source-label',f'CGMacros 1.0.0 / {device}：发布的一分钟曲线（含插值），仅检验预处理后的额外缺失；不代表原始设备掉线。'],cwd=ROOT,check=True)
    audit=json.loads((prepared/'audit.json').read_text(encoding='utf-8'))
    included=len(datasets['dexcom'])
    excluded=[r['participant'] for r in audit['participants'] if not r['devices']['dexcom']['included']]
    lines=['# CGMacros 发布曲线缺失实验', '',
        '**这是预处理后曲线的额外缺失敏感性实验，不是原始传感器掉线研究，也没有把某台设备作为真值。**','',
        f'来源：CGMacros 1.0.0，45 份参与者 CSV；纳入 {included} 人，排除 {len(excluded)} 人。',
        '排除名单：'+(', '.join(excluded) or '无')+'。原因：没有双设备共同完整的连续 24 小时分钟窗口。','',
        '每人选择最早的共同完整 24 小时；两设备使用相同时间窗、相同删除掩码。完整窗口筛选可能偏向数据质量较好的片段，不代表全部随访。',
        '每种模式使用 5%、10%、20% 的时间缺失，10 个种子（0–9）。每个窗口 1,440 个等权分钟支持及一个零权重终点。',
        '所有偏差 = 删除后 − 删除前。TIR 取 70–180 mg/dL；单位为百分点。','',
        '|设备|模式|缺失比例|平均血糖 MAE mg/dL|TIR MAE pp|TIR MAE 跨种子 SD pp|',
        '|---|---|---:|---:|---:|---:|']
    for device in datasets:
        results=json.loads((ROOT/f'outputs/cgmacros/{device}/results.json').read_text(encoding='utf-8'))['results']
        for mode in ['random','block','night']:
            for ratio in [.05,.1,.2]:
                selected=[r for r in results if r['mode']==mode and r['requested_ratio']==ratio]
                means=[statistics.mean(abs(r[m]) for r in selected) for m in ['mean_bias_mg_dl','tir_bias_pp']]
                by_seed=[statistics.mean(abs(r['tir_bias_pp']) for r in selected if r['seed']==s) for s in range(10)]
                lines.append(f'|{device}|{mode}|{ratio:.0%}|{means[0]:.3f}|{means[1]:.3f}|{statistics.stdev(by_seed):.3f}|')
    agreements=[r['agreement'] for r in audit['participants'] if r['agreement']['common_supported_minutes']>0]
    lines+=['','MAE 对参与者与种子等权；跨种子 SD 描述随机性，不是人群置信区间。每位参与者的有符号偏差和删除位置保留在结果 JSON。', '',
        '## 跨设备一致性（描述性）','',
        f'使用全部记录中双设备共同可观测的时间支持，共 {len(agreements)} 人。每分钟常值支持，不跨缺失外推、不拟合时滞。此处窗口与上面的 24 小时缺失实验不同。',
        f"参与者等权平均：Dexcom − Libre 平均血糖差 {statistics.mean(r['dexcom_minus_libre_mean_mg_dl'] for r in agreements):.3f} mg/dL；设备间 MAE {statistics.mean(r['between_device_mae_mg_dl'] for r in agreements):.3f} mg/dL；TIR 差 {statistics.mean(r['dexcom_minus_libre_tir_pp'] for r in agreements):.3f} 个百分点。", '',
        '## 复现与限制','',
        '`python fetch_cgmacros.py` → `python run_cgmacros.py`。下载记录包含 ZIP 成员 CRC32 和 CSV SHA256；HTTP Range 下载未校验整个 ZIP 的 SHA256。',
        '查看 data/local/cgmacros/prepared/audit.json 获取每人读数数目、间隔分布、筛选起止时间、排除原因与一致性结果。',
        '发布 CSV 包含一分钟插值特征；删除后保留的数值可能已编码邻近原始观测的信息。因此不能估计原始读数丢失后再插值的误差。',
        '未进行设备优劣判断、临床效能推断或人群显著性检验。上海验证集与餐后预测尚未实现。', '',
        '来源：[CGMacros 数据](https://physionet.org/content/cgmacros/1.0.0/)；[Das et al., Scientific Data 2025](https://doi.org/10.1038/s41597-025-05851-7)。',
        '数据与本次派生分析产物按 CC BY-NC-SA 4.0 标注；仓库原创代码采用 MIT。']
    out=ROOT/'outputs/cgmacros'
    (out/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (out/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    (out/'provenance.json').write_text(json.dumps({
        'dataset_manifest':manifest,
        'code_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                       for name in ['glucotrust.py','cgmacros.py','run_cgmacros.py','fetch_cgmacros.py','demo.html']},
        'license':'CGMacros-derived outputs: CC BY-NC-SA 4.0; original code: MIT'
    },indent=2),encoding='utf-8')
    print(f'Report: {out / "report.md"}')


if __name__=='__main__': main()
