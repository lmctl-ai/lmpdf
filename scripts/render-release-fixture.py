#!/usr/bin/env python3
"""Exercise the public document API through LMScript; JSON controls only this test."""
import argparse
import json
import os
import shutil
from pathlib import Path
import subprocess
import tempfile
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from release.compiler import compiler_command


def q(value):
    return json.dumps(str(value), ensure_ascii=False)


def source(model, output, image):
    pages = int(model.get('pages', 3))
    benchmark = pages >= 200
    rows = int(model.get('table_rows', 35 if benchmark else 24))
    lines = [f'p = _lmcode_ cli={q(model["cli"])};',
             f'let d = docx.create({q(output)});',
             f'd.title({q(model["title"])}).font("Carlito").font_size({9.0 if benchmark else 10.0});',
             'd.header("Release conformance fixture");',
             'd.footer_fields("Page {PAGE} of {NUMPAGES}");']
    if not benchmark:
        lines += ['d.toc("Contents", 2);',
                  'd.heading("Release conformance fixture", 1);',
                  'd.paragraph("English paragraph with office ligatures and AV kerning.");',
                  f'd.paragraph({q("العربية")} ).font("Noto Naskh Arabic").align("right");',
                  f'd.paragraph({q("日本語")} ).font("Kosugi");',
                  'd.paragraph("Link: ").hyperlink("Conformance source", "https://example.com/lmpdf");',
                  'd.paragraph("A footnote follows").footnote("Release fixture footnote");',
                  f'docx.sample_image({q(image)});', f'd.image({q(image)}, 160, 90);']
    for page in range(pages):
        lines.append(f'let t{page} = d.table({rows + 1}, 3);')
        for row in range(1, rows + 2):
            for col in range(1, 4):
                text = f'Header {col}' if row == 1 else f'Page {page+1} row {row-1} cell {col}'
                lines.append(f't{page}.cell({row}, {col}, {q(text)});')
        if page + 1 < pages:
            lines.append('d.page_break();')
    lines += ['d.save();', 'end _lmcode_', 'r = run_lmcode(p); assert(r.ok, json_stringify(r));']
    return '\n'.join(lines) + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--binary', required=True); ap.add_argument('--fixture', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--compiler', default=os.environ.get('LMSCRIPT_BIN', 'lmscript'))
    ap.add_argument('--untagged', action='store_true')
    a = ap.parse_args()
    model = json.loads(Path(a.fixture).read_text(encoding='utf-8'))
    binary = str(Path(a.binary).resolve())
    output = Path(a.output).resolve(); output.parent.mkdir(parents=True, exist_ok=True)
    cli = binary.replace('\\', '/') + ' docx'
    if a.untagged:
        help_run = subprocess.run([binary, 'docx', '--help'], text=True, encoding='utf-8', capture_output=True)
        if '--no-tagged' not in help_run.stdout + help_run.stderr:
            raise SystemExit('untagged benchmark requires host --no-tagged support')
        cli += ' --no-tagged'
    model['cli'] = cli
    with tempfile.TemporaryDirectory(prefix='lmpdf-fixture-') as td:
        if any(ch.isspace() for ch in binary):
            staged = Path(td) / ('lmpdf.exe' if os.name == 'nt' else 'lmpdf')
            shutil.copy2(binary, staged)
            staged.chmod(staged.stat().st_mode | 0o111)
            model['cli'] = str(staged).replace('\\', '/') + ' docx' + (' --no-tagged' if a.untagged else '')
        script = Path(td) / 'fixture.lms'
        script.write_text(source(model, output, output.parent/'fixture-image.png'), encoding='utf-8')
        p = subprocess.run(compiler_command(a.compiler, [str(script)]), text=True, encoding='utf-8', capture_output=True)
        if p.returncode or p.stderr:
            raise SystemExit(f'LMScript failed ({p.returncode}): {p.stdout}\n{p.stderr}')
    if not output.is_file() or not output.stat().st_size:
        raise SystemExit('lmpdf produced no output')

if __name__ == '__main__':
    main()
