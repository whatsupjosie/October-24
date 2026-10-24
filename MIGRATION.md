# October-24 source migration ledger

This repository is the new PubCast development home.

## Rules
- Keep `whatsupjosie/October` unchanged as a donor and history reference.
- Do not infer that a file staged from October is the latest integrated version.
- Consolidate the October 24 working-tree changes before promoting this repository to the authoritative build.
- Import Foresight, 2i, PubPartner, startup/runtime dependencies, and their tests first.
- Defer unrelated experiments, archival copies, generated output, local databases, model weights, and caches.
- Preserve original source paths and record provenance; do not flatten or rename modules casually.
- Keep secrets, user conversations, credentials, local runtime state, and private data out of Git.
- Require a runnable application, targeted integration tests, and recorded test results before calling a migration benchmark verified.

## Current state
A small set of October-baseline modules and regression tests has been staged. This is not yet a runnable consolidated PubCast source tree. The newer October 24 integration archives and local working tree have not been transferred into GitHub.

## Priority next imports
1. The reconciled local working tree: `main.py`, runtime dependencies, modules, Foresight assets, 2i writer, PubPartner, and relevant tests.
2. The current CI workflow, aligned to actual test filenames and entry points.
3. Minimal run/setup documentation and integrity checks.

## Excluded until needed
Historical handoffs and duplicate archives, experiment branches, generated assets, caches, recordings, large binary models, and dormant features.
