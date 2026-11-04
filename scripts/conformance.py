#!/usr/bin/env python3
"""Run release validators against two fresh lmpdf processes.

The default adapter compiles a private fixture model through LMScript and
invokes the public ``lmpdf docx --lmcode BYTECODE`` contract.
"""
import argparse, hashlib, json, re, shlex, shutil, subprocess, sys, tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
import unicodedata

ROOT = Path(__file__).resolve().parents[1]

def run(argv):
    return subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def required(path, name):
    path = path or shutil.which(name)
    if not path or not Path(path).is_file(): raise RuntimeError(f"missing required validator: {name}")
    return path

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()

def validate_verapdf(verapdf, pdf, xml, profile):
    p = run([verapdf, '--format', 'xml', '--flavour', profile, str(pdf)])
    xml.write_text(p.stdout)
    if p.returncode not in (0, 1): raise RuntimeError(f"veraPDF crashed: {p.stderr}")
    try: root = ET.fromstring(p.stdout)
    except ET.ParseError as e: raise RuntimeError(f"veraPDF emitted invalid XML: {e}")
    reports = [e for e in root.iter() if e.tag.rsplit('}', 1)[-1] == 'validationReport']
    if p.returncode != 0 or len(reports) != 1 or not all(r.attrib.get('isCompliant', '').lower() == 'true' for r in reports):
        raise RuntimeError(f"veraPDF {profile} failed (fail closed): {xml}")
    for element in root.iter():
        if element.tag.rsplit('}', 1)[-1] == 'batchSummary':
            if any(int(element.get(name, '0')) for name in ['failedToParse', 'outOfMemory', 'veraExceptions']):
                raise RuntimeError(f'veraPDF reported a processing failure: {xml}')
    return {'exit': p.returncode, 'reports': len(reports), 'compliant': True}

def validate_pdf(pdf, args):
    qpdf, pdfinfo, mutool = (required(args.qpdf, 'qpdf'), required(args.pdfinfo, 'pdfinfo'), required(args.mutool, 'mutool'))
    q = run([qpdf, '--check', str(pdf)])
    if q.returncode != 0: raise RuntimeError(f'qpdf failed ({q.returncode}): {q.stdout}\n{q.stderr}')
    i = run([pdfinfo, str(pdf)])
    if i.returncode or i.stderr: raise RuntimeError(f'pdfinfo failed/stderr not clean: {i.stderr}')
    if not re.search(r'^Tagged:\s+yes\s*$', i.stdout, re.MULTILINE | re.IGNORECASE):
        raise RuntimeError('pdfinfo does not report Tagged: yes')
    m = run([mutool, 'info', str(pdf)])
    if m.returncode or m.stderr: raise RuntimeError(f'mutool failed/stderr not clean: {m.stderr}')
    text = required(args.pdftotext, 'pdftotext'); t = run([text, str(pdf), '-'])
    if t.returncode or t.stderr or not t.stdout.strip(): raise RuntimeError(f'pdftotext failed or extracted no text: {t.stdout}\n{t.stderr}')
    normalized = ''.join(ch for ch in unicodedata.normalize('NFKC', t.stdout) if unicodedata.category(ch) != 'Cf')
    for expected in getattr(args, 'expected_text', []):
        if expected not in normalized:
            raise RuntimeError(f'PDF is missing required fixture text: {expected!r}')
    return {'qpdf_exit': q.returncode, 'pdfinfo_exit': i.returncode, 'mutool_exit': m.returncode, 'pdftotext_exit': t.returncode, 'text_bytes': len(t.stdout.encode())}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--binary', required=True); ap.add_argument('--fixture', default=str(ROOT/'tests/release/fixture.json'))
    ap.add_argument('--out-dir', required=True); ap.add_argument('--render-command', help='shlex template with {binary} {fixture} {output}; default: {binary} docx --json {fixture} {output}')
    ap.add_argument('--render-only', action='store_true', help='render twice and compare bytes without validators')
    ap.add_argument('--expected-manifest', help='compare the first output hash with another manifest')
    ap.add_argument('--verapdf'); ap.add_argument('--qpdf'); ap.add_argument('--pdfinfo'); ap.add_argument('--mutool'); ap.add_argument('--pdftotext')
    a = ap.parse_args(); fixture = Path(a.fixture).resolve(); out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    if not fixture.is_file(): raise RuntimeError(f'missing fixture: {fixture}')
    a.expected_text = json.loads(fixture.read_text(encoding='utf-8')).get('text', [])
    adapter = shlex.join([sys.executable, str(ROOT/'scripts/render-release-fixture.py'), '--binary', '{binary}', '--fixture', '{fixture}', '--output', '{output}'])
    template = a.render_command or adapter
    vp = None if a.render_only else required(a.verapdf, 'verapdf')
    logical_template = a.render_command or 'render-release-fixture.py --binary {binary} --fixture {fixture} --output {output}'
    manifest = {'fixture': fixture.name, 'render_template': logical_template, 'profiles': ['2b','ua1'], 'runs': []}
    with tempfile.TemporaryDirectory(prefix='lmpdf-conformance-', dir=out) as temp:
        for n in (1, 2):
            pdf = Path(temp) / f'output-{n}.pdf'; cmd = [x.format(binary=a.binary, fixture=str(fixture), output=str(pdf)) for x in shlex.split(template)]
            p = run(cmd)
            if p.returncode or p.stderr: raise RuntimeError(f'host failed ({p.returncode})/stderr not clean: {p.stdout}\n{p.stderr}')
            if not pdf.is_file() or pdf.stat().st_size == 0: raise RuntimeError('host produced no PDF')
            if a.render_only:
                checks = {'render_only': True}; profiles = {}
            else:
                checks = validate_pdf(pdf, a); profiles = {}
                for profile in ('2b','ua1'):
                    xml = out / f'verapdf-{profile}-{n}.xml'; profiles[profile] = validate_verapdf(vp, pdf, xml, profile)
            logical_cmd = [x.format(binary='<binary>', fixture='<fixture>', output=f'<output-{n}.pdf>') for x in shlex.split(template)]
            manifest['runs'].append({'command': logical_cmd, 'sha256': digest(pdf), 'bytes': pdf.stat().st_size, 'validators': {**checks, 'verapdf': profiles}})
            shutil.copy2(pdf, out / f'output-{n}.pdf')
    if manifest['runs'][0]['sha256'] != manifest['runs'][1]['sha256']: raise RuntimeError('byte determinism failed')
    if a.expected_manifest:
        expected = json.loads(Path(a.expected_manifest).read_text())
        if expected.get('runs', [{}])[0].get('sha256') != manifest['runs'][0]['sha256']:
            raise RuntimeError('expected manifest hash mismatch')
    manifest['deterministic'] = True; (out/'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
    print(json.dumps(manifest, indent=2, sort_keys=True))

if __name__ == '__main__':
    try: main()
    except (RuntimeError, OSError) as e: print(f'conformance: {e}', file=sys.stderr); raise SystemExit(1)
