"""Create an allowlisted, deterministic source ZIP; never include local health data."""
import hashlib
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def release_files(root=ROOT):
    names=['README.md','README.zh-CN.md','LICENSE','VERSION','CITATION.cff','CHANGELOG.md','CONTRIBUTING.md',
           '.gitignore','.gitattributes','requirements-data.txt','requirements-patterns.txt','requirements-repro.txt','demo.html','release_dashboard.html']
    files=[root/name for name in names]
    files+=list(root.glob('*.py'))
    files+=list((root/'tests').glob('*.py'))
    files+=list((root/'.github').rglob('*.yml'))+list((root/'.github').glob('*.md'))
    files+=list((root/'docs').glob('*.md'))+list((root/'docs').glob('*.json'))
    files += [root/'docs/demo/index.html',root/'docs/demo/provenance.json']
    if (root/'docs/demo/preview.png').exists(): files.append(root/'docs/demo/preview.png')
    for relative in ['research_dashboard.html','docs/demo/research.html','docs/demo/research-provenance.json']:
        if (root/relative).exists(): files.append(root/relative)
    for p in files:
        if not p.is_file() or p.is_symlink(): raise ValueError(f'Missing or symlinked release input: {p}')
        if not p.resolve().is_relative_to(root.resolve()): raise ValueError('File escapes source root')
    return sorted(set(files),key=lambda p:p.relative_to(root).as_posix())


def main():
    version=(ROOT/'VERSION').read_text().strip()
    if version!='0.2.0': raise ValueError('Update release script for a new version')
    required=['docs/RESULTS.md','docs/RELEASE.md','docs/DATA_LICENSES.md','docs/REPRODUCIBILITY.md','docs/SELECTED_HISTORY_RESULTS.md','docs/demo/research.html']
    for name in required:
        if not (ROOT/name).exists(): raise ValueError(f'Missing release artifact {name}')
    files=release_files()
    prefix=f'gluco-trust-patterns-{version}'
    out=ROOT/'dist'
    out.mkdir(exist_ok=True)
    dest=out/f'{prefix}.zip'
    manifest=[]
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        def write(name,content):
            info=zipfile.ZipInfo(prefix+'/'+name,date_time=(2026,9,14,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16
            archive.writestr(info,content,compresslevel=9)
        for path in files:
            name=path.relative_to(ROOT).as_posix()
            content=path.read_bytes()
            write(name,content)
            manifest.append(hashlib.sha256(content).hexdigest()+'  '+name)
        write('MANIFEST.sha256',('\n'.join(manifest)+'\n').encode())
    digest=hashlib.sha256(dest.read_bytes()).hexdigest()
    dest.with_suffix('.zip.sha256').write_text(digest+'  '+dest.name+'\n',encoding='ascii')
    print(f'{len(files)} allowlisted files -> {dest} ({dest.stat().st_size:,} bytes)\nSHA256 {digest}')


if __name__=='__main__': main()
