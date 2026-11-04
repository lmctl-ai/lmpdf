#!/usr/bin/env bash
set -euo pipefail

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
LOCK="$ROOT/release/poppler-linux-64.explicit"
MANIFEST="$ROOT/release/poppler-packages.json"
PREFIX=${1:-${POPPLER_PREFIX:-"$PWD/.tools/poppler"}}
CACHE=${POPPLER_INSTALL_CACHE:-${TMPDIR:-/tmp}/lmpdf-poppler-installer}
MICROMAMBA_URL=https://api.anaconda.org/download/conda-forge/micromamba/2.9.0/linux-64/micromamba-2.9.0-0.tar.bz2
MICROMAMBA_SHA256=8761c382127e6363bd9e0a2451aa3ef90d071a79133f736e2f759a3bf13040dd

mkdir -p "$CACHE"
archive="$CACHE/micromamba-2.9.0-0.tar.bz2"
binary="$CACHE/bin/micromamba"
if [[ ! -x "$binary" || ! -f "$archive" ]]; then
  curl --fail --location --retry 3 --output "$archive" "$MICROMAMBA_URL"
  echo "$MICROMAMBA_SHA256  $archive" | sha256sum --check --strict
  tar -xjf "$archive" -C "$CACHE"
fi
echo "$MICROMAMBA_SHA256  $archive" | sha256sum --check --strict

if [[ ! -x "$PREFIX/bin/pdfinfo" ]]; then
  MAMBA_ROOT_PREFIX="$CACHE/root" "$binary" create -y -p "$PREFIX" --file "$LOCK"
fi

python3 - "$PREFIX" "$MANIFEST" <<'PY'
import json, pathlib, sys
prefix = pathlib.Path(sys.argv[1])
manifest = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
expected = {p["name"]: p for p in manifest["packages"]}
found = {}
for path in (prefix / "conda-meta").glob("*.json"):
    item = json.loads(path.read_text(encoding="utf-8"))
    found[item["name"]] = item
missing = sorted(set(expected) - set(found))
extra = sorted(set(found) - set(expected))
bad = []
for name, want in expected.items():
    got = found.get(name)
    if not got:
        continue
    for key in ("version", "build", "sha256", "md5"):
        if got.get(key) != want.get(key):
            bad.append(f"{name}.{key}: {got.get(key)!r} != {want.get(key)!r}")
if missing or extra or bad:
    raise SystemExit("Poppler package manifest mismatch: " + ", ".join(missing + extra + bad))
print(f"verified {len(expected)} pinned conda packages")
PY

if [[ -n "${POPPLER_VALIDATE_PDF:-}" ]]; then
  stderr_file="$CACHE/pdfinfo.stderr"
  stdout_file="$CACHE/pdfinfo.stdout"
  "$PREFIX/bin/pdfinfo" -v >"$stdout_file" 2>"$stderr_file"
  cat "$stdout_file" "$stderr_file" | grep -q 'pdfinfo version 26.09.0'
  "$PREFIX/bin/pdfinfo" "$POPPLER_VALIDATE_PDF" >"$stdout_file" 2>"$stderr_file"
  [[ ! -s "$stderr_file" ]]
  grep -q 'PDF version' "$stdout_file"
  echo "validated $POPPLER_VALIDATE_PDF with Poppler 26.09.0 (stderr empty)"
fi
echo "$PREFIX"
