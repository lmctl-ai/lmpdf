#!/usr/bin/env python3
"""Measure the direct host process on 200 table pages, excluding compiler RSS."""
import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--binary', required=True)
    ap.add_argument('--platform', required=True); ap.add_argument('--output-dir', required=True)
    a = ap.parse_args(); out = Path(a.output_dir).resolve(); out.mkdir(parents=True, exist_ok=True)
    binary = str(Path(a.binary).resolve())
    measure = [sys.executable, str(ROOT/'scripts/measure-build.py'), '--platform', a.platform,
               '--binary', binary, '--output', str(out/'metrics.json')]
    spec = json.loads((ROOT/'tests/release/fixture-200.json').read_text())
    outputs = []
    for tagged in (False, True):
        mode = 'table-200-' + ('tagged' if tagged else 'untagged')
        pdf = out/(mode+'.pdf'); model_path = out/(mode+'.json')
        tables = []; blocks = []
        for page in range(int(spec['pages'])):
            cells = []
            for row in range(int(spec['table_rows'])+1):
                cells.append([{'text': f'Header {col+1}' if row==0 else f'Page {page+1} row {row} cell {col+1}'} for col in range(3)])
            # Match TableBlock::new: empty width vectors otherwise collapse the grid.
            tables.append({'rows': len(cells), 'cols': 3, 'cells': cells, 'column_widths': [None, None, None], 'column_align': ['left', 'left', 'left'], 'repeat_header': True})
            blocks.append({'type': 'table', 'index': page})
            if page+1<int(spec['pages']): blocks.append({'type': 'page_break'})
        model = {'path': str(pdf), 'title': '200-page table benchmark', 'font': 'Carlito', 'font_size': 9.0,
                 'tagged': tagged, 'footer_fields': 'Page {PAGE} of {NUMPAGES}', 'tables': tables, 'blocks': blocks}
        model_path.write_text(json.dumps(model, ensure_ascii=False), encoding='utf-8')
        # Native DocxModel JSON allows the tagged switch without changing the shared Word API.
        command = [binary, 'docx', '--json', str(model_path), '--output', str(pdf)]
        measure += ['--fixture-name', mode, '--fixture-command', shlex.join(command)]
        outputs.append((mode, pdf, tagged))
    subprocess.run(measure, check=True)
    counts = {}
    for mode, pdf, tagged in outputs:
        info = subprocess.run(['pdfinfo', str(pdf)], capture_output=True, text=True, check=True)
        if info.stderr: raise RuntimeError(info.stderr)
        pages = re.search(r'^Pages:\s+(\d+)\s*$', info.stdout, re.M)
        actual = int(pages[1]) if pages else 0
        if actual != 200: raise RuntimeError(f'{mode}: expected 200 actual pages, got {actual}')
        tag = re.search(r'^Tagged:\s+(yes|no)\s*$', info.stdout, re.M)
        if not tag or (tag[1]=='yes') != tagged: raise RuntimeError(f'{mode}: actual tagging differs')
        counts[mode] = actual
    (out/'actual-pages.json').write_text(json.dumps(counts, indent=2)+'\n')
    subprocess.run([sys.executable, str(ROOT/'scripts/check-budgets.py'), '--platform', a.platform,
                    '--binary', binary, '--metrics', str(out/'metrics.json')], check=True, cwd=ROOT)

if __name__ == '__main__':
    main()
