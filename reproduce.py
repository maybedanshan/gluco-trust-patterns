"""GlucoTrust + GlucoPatterns: one entry point for reproducible research."""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
VERSION=(ROOT/'VERSION').read_text().strip()


def run(script,*args):
    print(f'>> {script} {" ".join(args)}',flush=True)
    subprocess.run([sys.executable,str(ROOT/script),*args],cwd=ROOT,check=True)


def require(path,instruction):
    if not (ROOT/path).exists():
        raise ValueError(f'Missing {path}. {instruction}')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',action='version',version=VERSION)
    parser.add_argument('task',choices=['demo','cgmacros','shanghai','physio','all','full','dashboard','release','paired','patterns','history','compare','selected-history','labels'])
    parser.add_argument('--download',action='store_true',help='Explicitly retrieve the selected licensed public data')
    parser.add_argument('--robustness',action='store_true',help='Also run 24/48/72h first/last CGMacros sensitivity; included in all')
    args=parser.parse_args()
    os.chdir(ROOT)
    try:
        if args.task=='full':
            for module in ['numpy','openpyxl','xlrd']:
                try: __import__(module)
                except ImportError: raise ValueError('Install requirements-repro.txt with Python 3.12 for the full workflow')
            run('reproduce.py','all',*(['--download'] if args.download else []))
            for script in ['glucopatterns.py','history_missingness.py','model_comparison.py','selected_history.py','build_report.py','build_dashboard.py']:
                run(script)
            print('Full workflow complete. Open docs/demo/research.html')
            return
        if args.task in ('demo','all'):
            run('glucotrust.py')
        if args.task in ('cgmacros','all'):
            if args.download: run('fetch_cgmacros.py')
            require('data/local/cgmacros/raw/manifest.json','Use --download or fetch_cgmacros.py --zip PATH.')
            run('run_cgmacros.py')
            if args.robustness or args.task=='all': run('audit_cgmacros.py')
        if args.task in ('shanghai','all'):
            try:
                import openpyxl, xlrd  # noqa: F401
            except ImportError:
                raise ValueError('Shanghai readers missing. Run python -m pip install -r requirements-data.txt')
            if args.download:
                run('inspect_sources.py','--only','shanghai_user_v5')
                run('fetch_external.py','--only','shanghai')
            require('data/local/shanghai_v5/manifest.json','Use --download.')
            run('shanghai.py')
        if args.task in ('physio','all'):
            if args.download:
                run('inspect_sources.py','--only','physiocgm')
                run('fetch_external.py','--only','physio')
            require('data/local/physiocgm/manifest.json','Use --download.')
            run('audit_physio.py')
        if args.task=='patterns':
            try:
                import numpy
            except ImportError:
                raise ValueError('Install requirements-patterns.txt before running patterns')
            if args.download: run('fetch_cgmacros.py')
            require('data/local/cgmacros/raw/manifest.json','Use patterns --download.')
            run('glucopatterns.py')
        if args.task=='labels':
            require('outputs/model_comparison/selection.json','Run patterns and compare first.')
            run('label_missingness.py')
            print('Done. Open docs/LABEL_MISSINGNESS_RESULTS.md')
            return
        if args.task=='selected-history':
            require('outputs/model_comparison/selection.json','Run patterns, history and compare first.')
            run('selected_history.py')
        if args.task=='compare':
            require('outputs/glucopatterns/splits.json','Run python reproduce.py patterns first.')
            run('model_comparison.py')
        if args.task=='history':
            require('outputs/glucopatterns/splits.json','Run python reproduce.py patterns first.')
            run('history_missingness.py')
        if args.task in ('paired','all'):
            run('paired_analysis.py')
        if args.task=='demo':
            run('build_dashboard.py','--demo-only','--out','outputs/demo/explorer/index.html')
        elif args.task=='release':
            run('build_dashboard.py')
            run('build_report.py')
            run('build_release.py')
        elif args.task not in ('patterns','history','compare','selected-history'):
            run('build_dashboard.py')
        print('Done. Open '+('docs/SELECTED_HISTORY_RESULTS.md' if args.task=='selected-history' else 'docs/MODEL_COMPARISON_RESULTS.md' if args.task=='compare' else 'docs/HISTORY_MISSINGNESS_RESULTS.md' if args.task=='history' else 'docs/GLUCOPATTERNS_RESULTS.md' if args.task=='patterns' else 'outputs/demo/explorer/index.html' if args.task=='demo' else 'docs/demo/index.html'))
    except (ValueError,subprocess.CalledProcessError) as error:
        parser.exit(1,f'GlucoTrust: {error}\n')


if __name__=='__main__': main()
