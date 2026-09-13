"""Save official repository metadata without downloading data archives."""
import json
import argparse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SOURCES={
    'shanghai_user_v5':'https://api.figshare.com/v2/articles/20425518/versions/5',
    'shanghai_collection_v5':'https://api.figshare.com/v2/articles/21600933/versions/5',
    'physiocgm':'https://api.figshare.com/v2/articles/28136294/versions/1',
    'diadata':'https://zenodo.org/api/records/17285631',
}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only',nargs='+',choices=list(SOURCES),default=list(SOURCES))
    args=parser.parse_args()
    out=Path('data/local/catalog')
    out.mkdir(parents=True,exist_ok=True)
    def fetch(item):
        name,url=item
        try:
            with urllib.request.urlopen(url,timeout=60) as response:
                payload=json.load(response)
            (out/f'{name}.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
            metadata=payload.get('metadata',payload)
            return {'name':name,'title':metadata.get('title'),'doi':payload.get('doi'),
                'version':payload.get('version',metadata.get('version')),
                'date':payload.get('published_date',metadata.get('publication_date')),
                'license':metadata.get('license'),'description':metadata.get('description'),
                'files':payload.get('files')}
        except Exception as error:
            return {'name':name,'error':str(error)}
    with ThreadPoolExecutor(max_workers=4) as pool:
        failures=[]
        for result in pool.map(fetch,[(key,SOURCES[key]) for key in args.only]):
            print(json.dumps({k:v for k,v in result.items() if k not in ('files','description')},ensure_ascii=True),flush=True)
            if 'error' in result: failures.append(result['name'])
        if failures: raise SystemExit('Metadata unavailable: '+', '.join(failures))


if __name__=='__main__': main()
