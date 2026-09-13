"""Download the specified Shanghai v5 archive and only PhysioCGM raw CGM members."""
import hashlib
import argparse
import json
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from fetch_cgmacros import RemoteZip


def fetch_shanghai(catalog):
    shanghai=json.loads((catalog/'shanghai_user_v5.json').read_text(encoding='utf-8'))
    if shanghai['doi']!='10.6084/m9.figshare.20425518.v5': raise ValueError('Unexpected Shanghai version')
    folder=Path('data/local/shanghai_v5')
    folder.mkdir(parents=True,exist_ok=True)
    source=shanghai['files'][0]
    dest=folder/'diabetes_dataset.zip'
    content=dest.read_bytes() if dest.exists() else None
    if content is None or hashlib.md5(content).hexdigest()!=source['computed_md5']:
        with urllib.request.urlopen(source['download_url'],timeout=60) as response: content=response.read()
    if len(content)!=source['size'] or hashlib.md5(content).hexdigest()!=source['computed_md5']:
        raise ValueError('Shanghai archive checksum mismatch')
    dest.write_bytes(content)
    (folder/'manifest.json').write_text(json.dumps({'doi':shanghai['doi'],'published_date':shanghai['published_date'],
        'license':shanghai['license'],'file':source,'sha256':hashlib.sha256(content).hexdigest()},indent=2),encoding='utf-8')
    print(f'Shanghai: {len(content)} bytes, MD5 verified',flush=True)


def fetch_physio(catalog):
    physio=json.loads((catalog/'physiocgm.json').read_text(encoding='utf-8'))
    if physio['doi']!='10.6084/m9.figshare.28136294.v1': raise ValueError('Unexpected PhysioCGM version')
    out=Path('data/local/physiocgm')
    out.mkdir(parents=True,exist_ok=True)
    def fetch(file):
        pid=file['name'].removesuffix('_raw.zip')
        if not pid.isalnum(): raise ValueError('Invalid participant filename')
        folder=out/pid
        folder.mkdir(exist_ok=True)
        with zipfile.ZipFile(RemoteZip(file['download_url'])) as archive:
            selected=[m for m in archive.infolist() if not m.is_dir() and ('/cgm/' in ('/'+m.filename.lower()) or Path(m.filename).name.lower()=='cgm.csv')
                      and '__macosx' not in m.filename.lower() and not Path(m.filename).name.startswith('.')]
            if not selected: raise ValueError(f'No CGM members: {archive.namelist()[:30]}')
            members=[]
            for m in selected:
                if m.file_size>10_000_000: raise ValueError('Unexpectedly large CGM member')
                content=archive.read(m)
                target=folder/Path(m.filename).name
                if any(r['file']==target.name for r in members): raise ValueError('Duplicate member basename')
                target.write_bytes(content)
                members.append({'member':m.filename,'file':target.name,'sha256':hashlib.sha256(content).hexdigest(),'crc32':f'{m.CRC:08x}'})
            print(f'{pid}: {[m["member"] for m in members]}',flush=True)
            return {'participant':pid,'archive':file,'members':members}
    raw=[f for f in physio['files'] if f['name'].endswith('_raw.zip')]
    with ThreadPoolExecutor(max_workers=4) as pool: participants=list(pool.map(fetch,raw))
    (out/'manifest.json').write_text(json.dumps({'doi':physio['doi'],'license':physio['license'],
        'verification':'Selected ZIP members CRC32 verified and SHA256 recorded; full ZIP checksums not verified',
        'participants':participants},indent=2),encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only',choices=['shanghai','physio','both'],default='both')
    args=parser.parse_args()
    catalog=Path('data/local/catalog')
    if args.only in ('shanghai','both'): fetch_shanghai(catalog)
    if args.only in ('physio','both'): fetch_physio(catalog)


if __name__=='__main__': main()
