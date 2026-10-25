#!/usr/bin/env python3
"""Build every examples/*.lms with lmpdf, validate the PDFs and render the README pictures.

For each example:
  - runs the script twice (lmscript, with the lmpdf build first on PATH) and checks the bytes are identical;
  - runs veraPDF (PDF/A-2b and PDF/UA-1 profiles) and `qpdf --check` in Docker (verapdf/cli, ropus-pdftools
    image from research/ResearchOpus/tools/Dockerfile.tools);
  - renders page 1 (and the next page when there is one) with PyMuPDF into docs/examples/<name>.png;
  - writes docs/examples/results.json and fills README.md between <!-- EXAMPLES:START --> and <!-- EXAMPLES:END -->.

Usage: python3 examples/render.py --lmpdf target/release/lmpdf [--only NAME ...]
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
DOCS = ROOT / "docs" / "examples"


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def build(script: Path, work: Path, bindir: Path) -> Path:
    work.mkdir(parents=True, exist_ok=True)
    shutil.copy(script, work / script.name)
    out = work / (script.stem + ".pdf")
    env = {**os.environ, "PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}"}
    r = run(["lmscript", script.name, out.name], cwd=work, env=env, timeout=600)
    if r.returncode != 0 or not out.exists():
        raise RuntimeError(f"{script.name}: {r.stdout[-800:]}{r.stderr[-800:]}")
    return out


def verapdf(pdf: Path, flavour: str, retry: bool = True):
    result = _verapdf(pdf, flavour)
    if result["compliant"] is None and retry:  # the container occasionally exits without a report
        result = _verapdf(pdf, flavour)
    return result


def _verapdf(pdf: Path, flavour: str):
    r = run(["docker", "run", "--rm", "-v", f"{pdf.parent}:/w", "verapdf/cli", "--flavour", flavour, "--format", "mrr", f"/w/{pdf.name}"])
    ok = re.search(r'isCompliant="(true|false)"', r.stdout)
    passed = re.search(r'passedRules="(\d+)"', r.stdout)
    failed = re.search(r'failedRules="(\d+)"', r.stdout)
    checks = re.search(r'passedChecks="(\d+)"', r.stdout)
    return {
        "compliant": ok.group(1) == "true" if ok else None,
        "passed_rules": int(passed.group(1)) if passed else None,
        "failed_rules": int(failed.group(1)) if failed else None,
        "passed_checks": int(checks.group(1)) if checks else None,
    }


def qpdf(pdf: Path):
    r = run(["docker", "run", "--rm", "-v", f"{pdf.parent}:/w", "-w", "/w", "ropus-pdftools", "qpdf", "--check", pdf.name])
    return "ok" if "No syntax or stream encoding errors" in r.stdout and "WARNING" not in r.stdout else r.stdout[-300:]


def picture(pdf: Path, png: Path, pages_to_show):
    import pymupdf
    from PIL import Image
    doc = pymupdf.open(pdf)
    shots = []
    for i in pages_to_show:
        if i < doc.page_count:
            pix = doc[i].get_pixmap(matrix=pymupdf.Matrix(1.1, 1.1), alpha=False)
            shots.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
    pad = 14
    w = sum(s.width for s in shots) + pad * (len(shots) + 1)
    h = max(s.height for s in shots) + 2 * pad
    canvas = Image.new("RGB", (w, h), (236, 239, 242))
    x = pad
    for s in shots:
        canvas.paste(s, (x, pad))
        x += s.width + pad
    png.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("P", palette=Image.ADAPTIVE, colors=64).save(png, optimize=True)
    return doc.page_count


def readme(results):
    path = ROOT / "README.md"
    text = path.read_text()
    start, end = "<!-- EXAMPLES:START -->", "<!-- EXAMPLES:END -->"
    if start not in text or end not in text:
        return
    lines = [start,
             "PDF-specific examples in [`examples/`](examples/). Each script is plain lmcode with `cli=\"lmpdf docx\"`;",
             "the caption shows what was checked on the committed build: page count, byte-identical rebuild,",
             "`qpdf --check`, and veraPDF 1.30 for PDF/A-2b and PDF/UA-1 (lmpdf's default output profile).",
             "Rebuild them with `python3 examples/render.py --lmpdf target/release/lmpdf`.",
             ""]
    for r in results:
        a, u = r["verapdf_2b"], r["verapdf_ua1"]
        def v(x):
            if x["compliant"] is None:
                return "not run"
            return ("PASS" if x["compliant"] else "FAIL") + f" ({x['passed_rules']} rules passed, {x['failed_rules']} failed)"
        lines.append(f"**[{r['name']}](examples/{r['name']}.lms)**: {r['summary']}")
        lines.append("")
        lines.append(f'<img src="docs/examples/{r["name"]}.png" width="760" alt="{r["name"]}">')
        lines.append("")
        lines.append(f"<sub>{r['pages']} pages · rebuild byte-identical: {'yes' if r['deterministic'] else 'NO'} · "
                     f"qpdf --check: {r['qpdf']} · veraPDF PDF/A-2b: {v(a)} · veraPDF PDF/UA-1: {v(u)}</sub>")
        lines.append("")
    lines.append(end)
    a, b = text.index(start), text.index(end) + len(end)
    path.write_text(text[:a] + "\n".join(lines) + text[b:])


def summary(script: Path) -> str:
    first = []
    for line in script.read_text(encoding="utf-8").splitlines():
        if not line.startswith("#"):
            break
        first.append(line.lstrip("# ").strip())
    return " ".join(first)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lmpdf", default=str(ROOT / "target" / "release" / "lmpdf"))
    ap.add_argument("--only", nargs="*")
    args = ap.parse_args()
    lmpdf = Path(args.lmpdf).resolve()
    tmp = Path(tempfile.mkdtemp(prefix="lmpdf-examples-"))
    bindir = tmp / "bin"
    bindir.mkdir()
    (bindir / "lmpdf").symlink_to(lmpdf)
    scripts = sorted(EXAMPLES.glob("*.lms"))
    if args.only:
        scripts = [s for s in scripts if s.stem in args.only]
    results_path = DOCS / "results.json"
    previous = {r["name"]: r for r in json.loads(results_path.read_text())} if results_path.exists() else {}
    for script in scripts:
        a = build(script, tmp / "a" / script.stem, bindir)
        b = build(script, tmp / "b" / script.stem, bindir)
        deterministic = hashlib.sha256(a.read_bytes()).digest() == hashlib.sha256(b.read_bytes()).digest()
        pages = picture(a, DOCS / f"{script.stem}.png", [0, 1])
        previous[script.stem] = {
            "name": script.stem, "summary": summary(script), "pages": pages, "bytes": a.stat().st_size,
            "deterministic": deterministic, "qpdf": qpdf(a),
            "verapdf_2b": verapdf(a, "2b"), "verapdf_ua1": verapdf(a, "ua1"),
        }
        r = previous[script.stem]
        print(f"{script.stem:28} pages {pages:3} same-bytes {deterministic} qpdf {r['qpdf']} 2b {r['verapdf_2b']['compliant']} ua1 {r['verapdf_ua1']['compliant']}")
    results = [previous[k] for k in sorted(previous)]
    results_path.write_text(json.dumps(results, indent=1, ensure_ascii=False) + "\n")
    readme(results)
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
