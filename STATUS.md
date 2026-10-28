# Build — Foresight integration status

**2026-10-22, integration checkpoint.** This is the authoritative short status for
Foresight inside this Build. It is **not** a declaration that all of PubCast is
finished. Never treat a file, route, recovered donor, or test fixture as proof
of live functionality.

## 2026-10-27: Bella Faux Pas Studio (walkable world) integrated

Details and ledger: `handoffs/WORLD_WALK_INTEGRATION_2026-10-27.md`. Guide: `docs/WORLD_WALK.md`.

- **The studio:** Bella Faux Pas Studio, the game section, opens from its own fan blade or File › Open…, in the dressing room. It runs at `/walk` and is live on the same PubWorld socket and hotspot backend as `/world`.
- **Canvas 2D fallback:** it was not actually wired into `foresight_counter.html`. It is now: on a WebGL2 failure the page falls back to `ForesightCanvas2D` and shows a "Graphics compatibility mode" status badge.
- **Full suite** (Python 3.12, 120 s limit per test):
  - clean `022d9ec`: 1,798 passed, 15 failed, 2 errors
  - with this change: 1,938 passed, 17 failed, 0 errors
  - The failing set is the same Foresight browser tests. 13 are in `test_foresight_file_workspace.py` and 4 in `test_foresight_airgapped_ui.py`; the two Canvas 2D tests among them used to error at setup and now reach tray admission, where they time out like the other two.
- **Launch acceptance:** `tests/test_bella_faux_pas_launch_acceptance.py` passes. It covers `run_reach.py`, login, the empty Counter, 2i, PubPartner and the studio.

## Already implemented — do not rebuild from scratch

- Foresight Counter entry point, locally hosted under `/foresight-counter`.
  `run_reach.py` now opens it by default; the original `/foresight` route and
  explicit `--start-page foresight-legacy` remain for compatibility.
- Real Counter geometry, collision physics, five-tray support, fan, locking,
  sizing, menus, persistence and per-program content-provider contract.
- A **Canvas 2D fallback** for devices where HDR/WebGL2 initialization fails:
  ordinary controls and layout remain available with a clearly labeled,
  visually simpler renderer. The original HDR renderer is unchanged.
- Same-origin Reach routes and assets for 2i, PubPartner and other program
  pages. 2i text/manuscript handling, offline local-file workspace and rich
  archive recovery exist; editing rich DOCX *inside* 2i is still unmounted.
- Authenticated supervisor-controlled Quit, saved working copies, local folder
  save/reopen, and source-original preservation.
- The verified Pete identity metadata is now packaged; do not replace the
  distinct PubPartner Alex vessel with donor bytes.

## Verified in this integration run

| Check | Result | Scope |
| --- | --- | --- |
| `pytest` application and workspace subset | 57 passed | Python, FastAPI, formats, roles, routes, local storage contracts |
| `pytest` geometry/physics subset | 35 passed | Deterministic Counter engine; not a target-hardware FPS proof |
| `pytest tests/test_foresight_airgapped_ui.py` | 4 passed | Actual menu clicks, lock/unlock, close/reopen, 2i iframe creation, snapshot restoration; GPU-stubbed for two, actual Canvas 2D fallback for two |
| `pytest tests/test_writers_room_real_http.py` | 1 passed | Real HTTP process and manuscript restart path |
| `python tools/workbench_preflight.py` | passed | Served Counter, 2i, PubPartner pages, scripts and registrations |
| `python tools/foresight_checks/audit_launcher.py` | passed | Real owner setup, anonymous denial, file write/readback, Python syntax, supervised Quit |

The commands above were run on Linux in an isolated test environment using
Python 3.13. The test files and logs are shipped; outcomes are not cumulative
proof of a full studio acceptance run.

## Unverified, and **not** claimed complete

- A clean offline Windows/PowerShell 5 installation on the owner's hardware;
  native file chooser and user permissions, WebGL performance and physical GPU.
- Real page-to-page communication and 2i input inside a Foresight iframe on an
  authenticated browser session. Sandbox browser navigation is administratively
  blocked, so the browser regressions exercised isolated DOM scripts instead.
- Live PubPartner provider/model, multi-document chat continuity, external
  recorder capture, camera/audio hardware and every hosted program's own Save.
- Full five-window GUI stress/load cycle under laptop hardware. A historical
  20.19 ms physics measurement exceeded its **16 ms** target; a passing logic
  suite does not overturn that performance issue.

## Blocked/deferred

- Rich DOCX editor engine binary bundle, HarfBuzz WASM and offline fonts are
  absent from this source checkpoint. Rich `.2i` v5 remains safely recoverable
  without claiming rich editing.
- The recovered donor `data/pubpartner/vessels/alex.pubpartner` in local donor
  ZIPs differs from the repository's authoritative Git blob
  `96fa66a728d07d5ff43b0d3d7fc17a466765cec1`. It is deliberately excluded
  from this distribution rather than impersonating the canonical vessel.
  That vessel remains in the `October` repository under `Backup-Consolidation`.
- The model named `ministral-pubcast:3b` may not exist on the user's machine;
  do not promise a live reply from PubPartner until a provider is verified.
- Automatic ChatGPT-surface capture is not established. It is not needed for
  the Foresight Counter commissioning milestone.
- Github Actions `startup_failure` with zero jobs has not been diagnosed.

## Where work goes next

1. Run `CHECK_FORESIGHT_WINDOWS.ps1` on Windows with a disposable user-data
   directory, installing declared dependencies once and caching wheels where
   possible. Collect command/output/date for every check.
2. Commission Counter in a full browser with real Reach auth. Open, move,
   resize, lock, park, close and restore five application trays. Exercise
   menu actions with mouse and keyboard, saving, denial/cancel, restart, and
   unsupported graphics fallback. Track layout jitter and dropped frames.
3. Connect the existing 2i conversation pane (without rewriting its chat
   engine), then check PubPartner model/vessel separately when authorized.
4. Check the original source and unchanged SHA manifests before promoting to
   a finished production milestone.

**No user's manuscripts, data stores, private keys, recordings or credentials
were intentionally included in this packaged source milestone.**
