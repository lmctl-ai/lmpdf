# lmcode host protocol

## Release status

The Rust implementation has adopted the current protocol in the private source
repository. **The public v0.1.62 binary has not adopted it.** A qualified successor
is blocked because Actions is disabled on the source repository by an organization
budget decision. Do not pin v0.1.62 for the migrated examples. A new version and
immutable install pin will be recorded after the repository's own release CI passes.
The example gallery records earlier rendering checks, not protocol qualification
of a future binary.

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

Source main pushes derive `v0.2.RUN_NUMBER`. The publisher waits for the audit,
five native build/protocol/example jobs, independent deterministic PDF replay,
and PDF/A-2b plus PDF/UA-1 validation. It publishes platform binaries and
`SHA256SUMS` to this public repository. Existing releases are immutable: reruns
verify source identity, the complete published checksum set and binary version
rather than replacing assets or requiring rebuilt bytes to be identical. No manual tag or release
is needed. These are configured gates; they remain unqualified until Actions is
re-enabled and the workflow actually succeeds.
