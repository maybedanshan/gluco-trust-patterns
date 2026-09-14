"""Build offline development explorer from aggregate results only."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    paths = [ROOT/'docs/model-comparison-results.json', ROOT/'docs/selected-history-results.json']
    model, history = [json.loads(p.read_text()) for p in paths]
    payload = {'models': [{k:v for k,v in s.items() if k!='per_person'} for s in model['evaluations']],
               'history': [{k:v for k,v in s.items() if k!='per_person'} for s in history['summaries']]}
    labels_path=ROOT/'docs/label-missingness-results.json'
    if labels_path.exists():
        labels=json.loads(labels_path.read_text())
        payload['labels']=[{k:v for k,v in s.items() if k!='per_person'} for s in labels['summaries']]
        payload['label_counts']={k:labels[k] for k in ['people','test_meals','mask_configurations','arm_threshold_evaluations']}
        paths.append(labels_path)
    template = ROOT/'research_dashboard.html'
    out = ROOT/'docs/demo'
    out.mkdir(parents=True,exist_ok=True)
    page = template.read_text(encoding='utf-8').replace('__RESEARCH_DATA__',json.dumps(payload,ensure_ascii=True).replace('<','\\u003c'))
    (out/'research.html').write_text(page,encoding='utf-8')
    (out/'research-provenance.json').write_text(json.dumps({'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths+[template,Path(__file__)]}},indent=2),encoding='utf-8')
    print('Open docs/demo/research.html')


if __name__=='__main__': main()
