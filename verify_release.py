"""Verify a release ZIP's external checksum, member paths and complete manifest."""
import argparse
import hashlib
import zipfile
from pathlib import Path, PurePosixPath


def verify(path):
    path=Path(path)
    expected=path.with_suffix('.zip.sha256').read_text(encoding='ascii').split()[0]
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if expected!=digest: raise ValueError('Archive checksum mismatch')
    with zipfile.ZipFile(path) as archive:
        names=archive.namelist()
        if len(names)!=len(set(names)): raise ValueError('Duplicate archive entries')
        for name in names:
            p=PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name:
                raise ValueError('Unsafe archive path')
        roots={PurePosixPath(n).parts[0] for n in names}
        if len(roots)!=1: raise ValueError('Expected one source root')
        prefix=next(iter(roots))+'/'
        manifest_name=prefix+'MANIFEST.sha256'
        lines=archive.read(manifest_name).decode('utf-8').splitlines()
        declared={}
        for line in lines:
            sha,name=line.split('  ',1)
            if name in declared: raise ValueError('Duplicate manifest entry')
            declared[name]=sha
        if {prefix+n for n in declared} != set(names)-{manifest_name}:
            raise ValueError('Manifest does not cover every archive member')
        for name,sha in declared.items():
            if name.startswith(('data/','outputs/','.venv/','build/','.git/')):
                raise ValueError('Local data or environment in archive')
            if hashlib.sha256(archive.read(prefix+name)).hexdigest()!=sha:
                raise ValueError('Member checksum mismatch: '+name)
    return len(declared),digest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path)
    args=parser.parse_args()
    count,digest=verify(args.archive)
    print(f'Verified {count} files; SHA256 {digest}')


if __name__=='__main__':main()
