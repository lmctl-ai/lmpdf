# lmpdf release qualification

Private `lmctlhq/lmpdf` CI builds the five native hosts and their five native PDF-layout readers, then freezes one run-derived candidate. Public `lmctl-ai/lmpdf` fetches the exact draft in its trusted broker, dispatches the artifact to credential-free native workers, and promotes only the unchanged tested asset set. Promotion is automatic; no release or tag is created by a person.

## Permission boundary

| Job | Permissions | Candidate execution |
| --- | --- | --- |
| regression | `contents:read` | Offline synthetic checks only |
| promote | `contents:write; actions:read` | No; fetches, brokers, verifies and performs release mutation |
| candidate | `contents:read; actions:read` | No; verifies parent and artifact identity |
| qualify-macos-arm64 | `contents:read; actions:read` | Yes, without GitHub credentials or persisted checkout credentials |
| integration | `contents:read; actions:read` | Yes, four additional native platforms |
| replay-macos-arm64 | `contents:read; actions:read` | Yes, deterministic PDF output replay |
| replay | `contents:read; actions:read` | Yes, four additional native replay platforms |
| compatibility | `contents:read; actions:read` | Yes, five same-input operations against the previous public host |
| conformance | `contents:read; actions:read` | Yes, PDF archival checks and RSS budgets |
| deliberate-failure-test | `contents:read` | No; sealed throwaway failure control only |

Only `promote` can change a release object. It dispatches a separate read-only worker, waits for every required job through the Actions API, and validates the child workflow source and candidate identity before making a mutation. Checkout credentials are not persisted. Candidate hosts run without `GH_TOKEN` or `GITHUB_TOKEN`.

## Candidate contents and integrity

A candidate contains the Linux, macOS and Windows hosts, their matching layout readers, `LICENSE`, `THIRD_PARTY_NOTICES.md`, `RELEASE-MANIFEST.json`, `SHA256SUMS`, the frozen asset identity, and the private provenance bundle. The private run number forms the patch version (`0.2.RUN_NUMBER`); the committed version floor is unchanged. The producer verifies the original private workflow run and all required build/audit/smoke jobs, seals the explicit throwaway flag, and attests the frozen identity. Public workers verify the signature, asset IDs and bytes before executing a host.

A retry may reuse only the same source/build attempt and asset identities. It cannot replace an existing asset or repair a missing frozen payload. Public state is recorded in `release-state.json`; `REVOKED` is append-only. Older or revoked candidates are refused. New releases must be immutable before the broker sets Latest.

## Run and observe

Start a production build from private `main`:

```sh
gh workflow run ci.yml -R lmctlhq/lmpdf --ref main
```

Run the sealed throwaway control once when qualifying failure cleanup:

```sh
gh workflow run ci.yml -R lmctlhq/lmpdf --ref main -f deliberate_public_failure=true
```

Follow the private producer, public broker, and public worker runs with `gh run list/view`. Public drafts remain unpublished until all platform, replay, compatibility, conformance, and RSS checks pass. In the throwaway run, the named deliberate test fails only after those gates succeed; the broker records revocation and removes only that sealed draft. A native-test failure leaves the draft unpublished for diagnosis.

If the private build succeeded and only the public handoff or runner queue failed transiently, redrive the original private `publish-draft` job so it reuses the original build attempt and frozen asset IDs, or replay a recorded tag in the public broker:

```sh
gh run rerun <PRIVATE_RUN_ID> -R lmctlhq/lmpdf --failed
gh workflow run qualify-private-draft.yml -f tag=v0.2.<N> -R lmctl-ai/lmpdf --ref main
```

A source or build change requires a new private manual run and a new derived version (`0.2.<run_number>`).

### Operator rollback

If a published release must be rolled back, append the tag and reason to `REVOKED` and push to `lmctl-ai/lmpdf` `main` **first** so any concurrent or subsequent replay of that tag is refused immediately, then move `Latest` back to the last known-good release:

```sh
printf 'v0.2.<BAD> operator rollback: <reason>\n' >> REVOKED
git add REVOKED && git commit -m "Revoke v0.2.<BAD>" && git push origin main
gh release edit v0.2.<GOOD> -R lmctl-ai/lmpdf --latest
```

The current qualified public pin is `github:lmctl-ai/lmpdf@v0.2.19`. It came
from private run `42181002138` (run 19); public broker `42182908771` and
read-only worker `42183010136` succeeded before CI published immutable release
436226856 as Latest. All 16 release asset IDs, sizes and SHA-256 digests matched
the GitHub API, and `SHA256SUMS` passed independently. A fresh isolated LMScript
install resolved this exact pin. Future versions continue to use the existing
0.2.x floor plus the private workflow run number; skipped/throwaway run numbers
are not reused.

## Local offline release controls

```sh
python3 -B -m unittest discover -s tests -p 'test_release*.py'
python3 tests/mutate-release-pipeline.py
```

These controls use synthetic manifests and stubbed APIs. Native host, corpus, compatibility and archival checks run in the private/public workflows above.
