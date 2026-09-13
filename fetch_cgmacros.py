"""Fetch only participant CSV members from the official versioned ZIP via HTTP Range."""
import argparse
import hashlib
import io
import json
import re
import urllib.request
import zipfile
import zlib
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

URL = 'https://physionet.org/files/cgmacros/1.0.0/CGMacros_dateshifted365.zip'


class RemoteZip(io.RawIOBase):
    def __init__(self, url=URL):
        self.url = url
        req = urllib.request.Request(self.url, headers={'Range':'bytes=0-0'})
        with urllib.request.urlopen(req, timeout=60) as response:
            if response.status != 206:
                raise RuntimeError('Server must support HTTP Range; use manual ZIP download otherwise')
            self.size = int(response.headers['Content-Range'].split('/')[-1])
            response.read()
        self.pos = 0
        self.cache = {}

    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos

    def seek(self, offset, whence=0):
        self.pos = offset if whence == 0 else self.pos+offset if whence == 1 else self.size+offset
        if self.pos < 0: raise ValueError('Negative seek')
        return self.pos

    def read(self, n=-1):
        if n < 0: n = self.size-self.pos
        n = min(n, self.size-self.pos)
        if n <= 0: return b''
        start, end = self.pos, self.pos+n
        for (lo, hi), content in self.cache.items():
            if lo <= start and end <= hi:
                self.pos = end
                return content[start-lo:end-lo]
        # Prefetch small adjacent headers; cap prevents fetching photographs.
        fetch_end = min(self.size, max(end, start+65536))
        req = urllib.request.Request(self.url, headers={'Range':f'bytes={start}-{fetch_end-1}'})
        with urllib.request.urlopen(req, timeout=60) as response:
            if response.status != 206 or not response.headers['Content-Range'].startswith(f'bytes {start}-{fetch_end-1}/'):
                raise RuntimeError('Unexpected range response')
            content = response.read()
        if len(content) != fetch_end-start: raise IOError('Truncated range response')
        self.cache[(start,fetch_end)] = content
        self.pos = end
        return content[:n]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=Path('data/local/cgmacros/raw'))
    parser.add_argument('--zip',type=Path,help='Read a fully downloaded local ZIP instead')
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.zip if args.zip else RemoteZip()) as archive:
        members=[m for m in archive.infolist() if re.fullmatch(r'CGMacros-\d{3}\.csv',Path(m.filename).name) and not m.filename.startswith('__MACOSX/')]
        if len(members)!=45: raise ValueError(f'Expected 45 participant CSVs, found {len(members)}')
        manifest={'source':URL,'version':'1.0.0','license':'CC BY-NC-SA 4.0',
                  'retrieved_utc':datetime.now(timezone.utc).isoformat(),
                  'verification':'ZIP member CRC32 validated; per-file SHA256 recorded. Full archive SHA256 not checked in HTTP Range mode.', 'files':[]}
        local = threading.local()
        opened = []
        def fetch(member):
            dest=args.out/Path(member.filename).name
            content=dest.read_bytes() if dest.exists() else None
            if content is None or len(content)!=member.file_size or zlib.crc32(content)!=member.CRC:
                if not hasattr(local,'archive'):
                    local.archive=zipfile.ZipFile(args.zip if args.zip else RemoteZip())
                    opened.append(local.archive)
                # Read validates the ZIP member CRC; never extract archive paths.
                content=local.archive.read(member.filename)
            dest.write_bytes(content)
            print(f'{dest.name}: {len(content)} bytes',flush=True)
            return {'member':member.filename,'file':dest.name,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest(),'crc32':f'{member.CRC:08x}'}
        try:
            with ThreadPoolExecutor(max_workers=4) as pool:
                manifest['files']=list(pool.map(fetch,sorted(members,key=lambda m:m.filename)))
        finally:
            for handle in opened: handle.close()
        (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')


if __name__=='__main__': main()
