# lmcode host protocol

## Release status

[v0.2.17](https://github.com/lmctl-ai/lmpdf/releases/tag/v0.2.17) is the current
qualified lmcode host. Pin `install="github:lmctl-ai/lmpdf@v0.2.17"` in recipes.
The private source commit is `859bcdd8a90fa665b8fb83804a2474b3ff1e9b11`; its
own workflow built the five hosts and layout readers, then the public broker and
read-only worker qualified those exact bytes on every supported platform. The
release is immutable Latest, with `SHA256SUMS`, a sealed asset manifest and
private build provenance. A fresh isolated LMScript install resolved the
v0.2.17 binary and passed schema/signature discovery. The historical v0.1.62
binary retains the retired protocol and is not suitable for these recipes.

## Execution and discovery

Both `lmpdf docx` and `lmpdf pptx` expose:

- `--lmcode FILE`, repeated for builder parts;
- `--lmcode-schema`, with optional `--json`;
- `--lmcode-signatures`, with optional `--without-std`.

Retired execution/schema flags and `--first`/`--last` are refused, without aliases.
The existing native inspection and JSON rendering utilities remain available.
Computed bytecode output paths are internal; examples execute their compiled
program values through `run_lmcode`, with compiler 0.2.456 or newer.

## Invocation, dry execution and results

LMScript supplies invocation manifest v1 through `LMCODE_INVOCATION_FILE`.
The host validates the single/builder manifest before constructing a document
context or reading a program. A supplied manifest must contain boolean `dry`;
missing, string, numeric, null, array or object values fail with exit 2. There is
no metadata repair or silent retry. Standalone host execution without a manifest
is real execution.

Repeated registrations execute in command order, with result identity taken from
the manifest. Each part owns a sealed result slot; a builder result is an array
in manifest order, even for a one-part builder. The document context is shared
across parts. The first failure stops later dispatch and exposes no partial result.

In dry mode, domain callbacks are skipped with SDK typed dummies, including
constructor/method chains and inspection reads. No PDF, image or directory is
created, and existing output files are unchanged. No domain callback currently
opts into real execution during dry mode; the SDK permits optional previews.

Exactly one terminal `LMCODE_RETURN_BEGIN` / `LMCODE_RETURN_END` frame carries
success or structured failure. Exit codes are 0 (success), 2 (CLI/manifest),
3 (load/VM), and 4 (application/I/O). The implementation uses the reviewed Rust
SDK SHA `ebca156c0d56efbe95957c2dee232deca4175eff`, vendored verbatim through its
sync script. No implicit table/image/page output ceilings or process deadlines
are imposed. Invalid document geometry, encoding and PDF-standard requirements
still fail honestly.

## Release qualification

New releases are started by a manual `workflow_dispatch` on main in the private
source repository. The committed `v0.2` floor and workflow run number determine
the automatic candidate version. Private CI seals the five host executables,
native layout readers, release notices, a provenance manifest and SHA256SUMS,
then creates/reuses a public draft and requests qualification through
`repository_dispatch`.

This public workflow resolves the exact draft and SHA256SUMS identity, installs
the candidate through the normal lmscript resolver on each supported OS, and
runs the full protocol/runtime suite, 33-vector html-doc corpus, native safety
controls, deterministic replay, same-input compatibility check, PDF/A-2b and
PDF/UA-1 validation, and tagged/untagged 200-page resource budgets. The deliberate
failure-path control is used only for a throwaway version; its cleanup removes
only that draft release object. Promotion is a separate gated public CI job that
rechecks the sealed candidate before marking it Latest. Existing published
releases are immutable; matching replays are idempotent and checksum conflicts
are rejected. No tag, release, or promotion is performed manually.

The latest qualified release is `v0.2.17`; the source, broker, worker and asset
verification evidence is recorded in the WP312 completion report.
