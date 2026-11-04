#!/usr/bin/env python3
"""Run the pinned html-doc corpus against this checkout's candidate lmpdf binary."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent / "html-doc-conformance"
sys.path.insert(0, str(ROOT))
import run as corpus_runner


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--compiler", required=True)
    parser.add_argument("--binary", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--install", default="github:lmctl-ai/lmpdf@v0.2.6",
                        help="exact lmscript host pin used for candidate real/dry invocation")
    parser.add_argument("--layout-reader", required=True, help="native PDF-operator reader built from examples/html_doc_layout.rs")
    args = parser.parse_args()
    compiler = Path(args.compiler).resolve()
    binary = Path(args.binary).resolve()
    evidence = Path(args.evidence).resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    private_bin = evidence / "private-bin"
    private_bin.mkdir(exist_ok=True)
    host = private_bin / ("lmpdf.exe" if os.name == "nt" else "lmpdf")
    if host.exists() or host.is_symlink():
        host.unlink()
    os.link(binary, host)
    env = dict(os.environ)
    env["PATH"] = str(private_bin) + os.pathsep + env.get("PATH", "")
    corpus = json.loads((ROOT / "corpus.json").read_text(encoding="utf-8"))
    subprocess.run([sys.executable,str(ROOT/"check.py")],check=True)
    records = []
    regression = ROOT / "regressions.json"
    extra=json.loads(regression.read_text()) if regression.exists() else {}
    cases=[dict(c,**extra.get("case_overrides",{}).get(c["id"],{})) for c in corpus["cases"]] + extra.get("cases",[])
    for case in cases:
        for name in [case["xml"],case["css"]]:
            require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==case['input_sha256'][Path(name).name],f"fixture bytes changed: {name}")
        xml = (ROOT / case["xml"]).read_text(encoding="utf-8")
        css = (ROOT / case["css"]).read_text(encoding="utf-8")
        if case["kind"] != "dry-negative":
            trace = corpus_runner.source_trace(xml, css, case["expected"], corpus)
            corpus_runner.assert_subset(case["expected"], trace, f"{case['id']} pinned source trace")
        output = evidence / "runs" / case["id"] / "output.pdf"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.unlink(missing_ok=True)
        source = (
            "xml = " + json.dumps(xml, ensure_ascii=False) + ";\n"
            "css = " + json.dumps(css, ensure_ascii=False) + ";\n"
            f'p = _lmcode_ cli="lmpdf docx" install={json.dumps(args.install)};\n'
            f'let d = docx.create({json.dumps(str(output))});\n'
            "d.html_doc(${xml}, ${css});\n"
            "d.save();\nend _lmcode_\nr = run_lmcode(p);\nprintln(json_stringify(r));\n"
        )
        with tempfile.TemporaryDirectory(prefix="html-doc-", dir=evidence) as temp:
            script = Path(temp) / "case.lms"
            script.write_text(source, encoding="utf-8")
            real = subprocess.run([str(compiler), str(script)], cwd=ROOT, env=env, text=True, capture_output=True)
        negative = case["kind"] == "dry-negative"
        if negative:
            require(not output.exists(), f"{case['id']} negative real unexpectedly wrote output")
            output_bytes = None
        else:
            require(real.returncode == 0, f"{case['id']} real: {real.stdout}{real.stderr}")
            require(output.is_file() and output.stat().st_size > 0, f"{case['id']} real output missing")
            inspect = subprocess.run([str(binary), "inspect", str(output)], cwd=ROOT, env=env, text=True, capture_output=True)
            require(inspect.returncode == 0, f"{case['id']} inspect: {inspect.stdout}{inspect.stderr}")
            details = json.loads(inspect.stdout).get("result", {})
            expected = case.get("expected", {})
            require(details.get("images") == len(expected.get("images", [])),
                    f"{case['id']} image mapping mismatch: {details.get('images')}")
            require(details.get("links") == len(expected.get("links", [])),
                    f"{case['id']} hyperlink mapping mismatch: {details.get('links')}")
            require(details.get("tables") == len(expected.get("tables", [])),
                    f"{case['id']} table mapping mismatch: {details.get('tables')}")
            if case["id"] == "page-break":
                require(details.get("pages") == 2, f"explicit page-break boundary was lost: {details}")
            observed=subprocess.run([str(Path(args.layout_reader).resolve()),str(output)],text=True,capture_output=True)
            require(observed.returncode==0,f"{case['id']} final PDF layout reader: {observed.stderr}")
            layout=json.loads(observed.stdout)
            normalize=lambda text:re.sub(r"\s+"," ",text).strip()
            expected_text=normalize(" ".join(trace["normalized_text_blocks"]))
            actual_text=normalize(layout["text"])
            for word in re.findall(r"[\w]+(?:-[\w]+)+",expected_text):actual_text=actual_text.replace(word.replace("-","- "),word)
            require(actual_text==expected_text,f"{case['id']} final PDF text differs: {actual_text!r} != {expected_text!r}")
            for key,value in case.get('render_assertions',{}).get('page',{}).items():
                require(abs(layout['pages'][0][key]-value)<0.06,f"{case['id']} wrong page {key}")
            def find_span(needle):
                matches=[s for s in layout['spans'] if needle in s['text']]
                require(bool(matches),f"{case['id']} missing observed span {needle!r}")
                return matches[0]
            for check in case.get('render_assertions',{}).get('spans',[]):
                span=find_span(check['text'])
                if 'bold' in check:require(('bold' in span['font'].lower())==check['bold'],f"{case['id']} wrong font weight {span}")
                for name in ['size_pt','x']:
                    if name in check:require(abs(span[name]-check[name])<0.06,f"{case['id']} wrong {name}: {span}")
                if 'rgb' in check:
                    wanted=[int(check['rgb'][i:i+2],16)/255 for i in [0,2,4]]
                    require(all(abs(a-b)<0.005 for a,b in zip(span['rgb'],wanted)),f"{case['id']} wrong color: {span}")
            for check in case.get('render_assertions',{}).get('vertical_gaps',[]):
                require(abs(find_span(check['second'])['y']-find_span(check['first'])['y'])>=check['minimum_pt'],f"{case['id']} authored spacing lost")
            output_bytes = output.stat().st_size
        output.unlink(missing_ok=True)
        with tempfile.TemporaryDirectory(prefix="html-doc-dry-", dir=evidence) as temp:
            script_path = Path(temp) / "case.lms"
            script_path.write_text(source, encoding="utf-8")
            dry = subprocess.run([str(compiler), "--dry-run", "--plan-format", "json", str(script_path)], cwd=ROOT, env=env, text=True, capture_output=True)
        require(not output.exists(), f"{case['id']} dry created the output")
        require(dry.returncode == 0, f"{case['id']} dry: {dry.stdout}{dry.stderr}")
        plan = json.loads(dry.stdout)
        entry = next((e for e in plan.get("entries", []) if e.get("kind") == "lmcode-host-dry"), None)
        require(entry is not None, f"{case['id']} missing dry host entry: {plan}")
        envelope = entry["envelope"]
        negative = case["kind"] == "dry-negative"
        require(envelope.get("dry") is True, f"{case['id']} missing dry marker: {envelope}")
        require(envelope.get("ok") is (not negative), f"{case['id']} dry result mismatch: {envelope}")
        records.append({"case": case["id"], "negative": negative, "dry": envelope,
                        "real_exit": real.returncode, "output_bytes": output_bytes})
    (evidence / "candidate-observations.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"html-doc candidate corpus: {len(records)} vectors PASS; evidence={evidence / 'candidate-observations.json'}")


if __name__ == "__main__":
    main()
