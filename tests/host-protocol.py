#!/usr/bin/env python3
"""Real host protocol refusals before dispatch; accepts a released binary too."""
import argparse, json, os, subprocess, tempfile
from pathlib import Path

def frame(p, code):
    assert p.returncode == code, (p.returncode, code, p.stdout, p.stderr)
    assert p.stdout.count('LMCODE_RETURN_BEGIN\n') == 1, p.stdout
    assert p.stdout.count('LMCODE_RETURN_END') == 1, p.stdout
    body = p.stdout.split('LMCODE_RETURN_BEGIN\n')[1].split('\nLMCODE_RETURN_END')[0]
    value = json.loads(body)
    assert value['ok'] == (code == 0), value
    if code: assert 'result' not in value, value
    return value

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--binary', required=True); a = ap.parse_args()
    binary = str(Path(a.binary).resolve())
    checks = 0
    with tempfile.TemporaryDirectory(prefix='lmpdf-protocol-') as td:
        root = Path(td); missing = root/'never-open.dslb'; manifest = root/'invocation.json'
        env = dict(os.environ, LMCODE_INVOCATION_FILE=str(manifest))
        for family in ['docx', 'pptx']:
            for mode in ['single', 'builder']:
                for dry in ['missing', 'yes', 0, None, {}, []]:
                    doc = dict(version=1, mode=mode, parts=[dict(index=0, file=str(missing))])
                    if dry != 'missing': doc['dry'] = dry
                    manifest.write_text(json.dumps(doc))
                    p = subprocess.run([binary, family, '--lmcode', str(missing)], env=env, capture_output=True, text=True)
                    value = frame(p, 2)
                    assert value['phase'] == 'cli', value
                    assert 'dry' in str(value), value
                    assert not missing.exists()
                    checks += 1
            for flag in ['--first', '--last', '--dsl', '--dsl-schema', '--dsl-signatures', '--cli-schema']:
                p = subprocess.run([binary, family, flag, str(missing)], capture_output=True, text=True)
                frame(p, 2); checks += 1
            for flags in [['--lmcode-schema'], ['--lmcode-schema', '--json'], ['--lmcode-signatures']]:
                p = subprocess.run([binary, family, *flags], env=env, capture_output=True, text=True)
                assert p.returncode == 0 and p.stdout and not p.stderr, (flags,p)
                checks += 1
    print(f'host protocol: {checks} checks PASS')
if __name__ == '__main__': main()
