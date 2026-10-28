# PubCast autonomous stability pass — 2026-10-28

Branch: `codex/pubcast-stability-2026-10-28`.
Base: `f0c2297f50b33eda6cde9921ccc28a4908a27f46`.
The previous camera fixes are inherited. Main and Copilot's branch are untouched.

## Final verified results

| Check | Observed result |
| --- | --- |
| Full Python suite, Linux / Python 3.12.14 | **2,025 passed, 0 failed, 2 skipped**, 415.86 seconds |
| Node suite (`npm run test:node`) | **10 passed, 0 failed** |
| Strict camera/private-room/restart CI command, async debug enabled | **74 passed**, ResourceWarning/RuntimeWarning/unraisable/thread exceptions treated as errors |
| Packaged routes and assets preflight | Passed against a disposable data directory |
| Standalone real-browser World Chat lost-receipt/retry check | Passed with the installed Chromium headless shell |
| Preserved source | Nine original files verified byte-for-byte and by SHA-256 |
| Alex vessel | Original Git blob `96fa66a728d07d5ff43b0d3d7fc17a466765cec1`, unchanged |

The two full-suite skips are the intentionally disabled optional Alex Little
One protocol module and its moved compatibility module. They are not skipped
camera, document, saving, World Chat or Studio tests. The full suite reports
211 existing deprecation warnings, including Starlette/AnyIO and utcnow usage;
this is not a warning-free full-suite claim. The separate strict subset passed.

## Changes that affect the program

### Camera displays keep moving when a peer stalls

`modules/hub.py` snapshots room membership before awaiting sends, avoiding a
dictionary-size-change failure when rooms appear during a system broadcast.
Camera switch frames are sent concurrently to independent rooms and peers,
with a two-second per-send deadline. Stalled peers are removed from every room
and closed with retry-later code 1013. Close attempts also have a deadline.
One physical socket receives one camera frame even when registered in multiple
rooms. Private-room revocation checks still run before delivery. Non-camera
room traffic keeps its existing sequential behavior.

The existing stage and avatar-control pages already reconnect their sockets.
The ordered camera bridge and shutdown ownership fixes from the previous
passes remain in place. The deadline assumes the underlying socket transport
cooperates with cancellation; Python cannot forcibly kill arbitrary code that
suppresses cancellation.

### 2i startup and connection storage

The legacy `2i/index.html` settings key is mutable, matching the owner-scoping
code in reach.js; its previous const declaration caused startup to throw.
Both that page and the active `writers-room-v22.html` now retain connection
secrets in sessionStorage and redact those fields in permanent localStorage.
Loading an old owner-scoped configuration migrates the persistent secrets to
the tab session while retaining non-secret model choices. Browser storage is
not an encrypted credential vault; the host's BYOK store remains separate.

New Node checks exercise both actual pages' storage functions, owner isolation,
legacy migration, new-tab behavior and preservation of chosen model names.
The editor test now checks the current unconfirmed-delivery wording plus the
important behavior: no fabricated assistant turn, a failed user attempt and
the draft retained for the writer.

## Test fixture repairs, not changes to product persistence

The old Counter browser fixture used about:blank and supplied no authenticated
owner/config responses. The current program correctly refused to finish its
workspace boot there. It now uses a locally routed trustworthy localhost
origin, a real test owner, and the real auth, writers-room and layout routers.
Assertions check the owner-scoped layout key and nonce-bearing 2i iframe URL.

The five-tray Canvas 2D case advances the real admission/physics engine using
its existing test clock and performs an actual fallback-renderer draw. It
tests admission and rendering, not target-hardware animation speed. The other
Counter lifecycle cases still exercise wall-clock opening and closing.

Two Studio tests assumed every visit was a first visit, even after earlier
tests saved the shared owner's green-room progress. Fresh-start cases now
explicitly start with empty progress in their disposable test account. Their
plain Counter page is always closed. The product still restores saved rooms;
the separate real restart-and-avatar test continues to verify that behavior.

## Preservation and automation

`PUBCAST_STABILITY_ORIGINALS_2026-10-28.md` contains all nine edited originals
from the base commit, verbatim, with hashes. Earlier Copilot and camera-pass
backups remain in handoffs too. `PUBCAST_AGENT_TESTED_SOURCE_2026-10-28.json`
records hashes for twenty relevant runtime/test/workflow files.

`.github/workflows/pubcast-stability.yml` adds Node and strict Python checks for
the changed paths. Its YAML and exact local test command were validated. This
report does not claim that a GitHub-hosted job has executed successfully.
The README now distinguishes current launch instructions from its historical
workspace handoff and old patch-application instructions.

## Verification history

An initial quiet full-suite attempt was interrupted after an apparent stall;
the isolated 2i restore/first-keystroke tests passed. A subsequent completed
run had 2,022 passes and two Studio fresh-start failures caused by shared saved
progress. After the fixture correction, the Studio host/progress subset passed
all 24 cases and the final full run passed as reported above. The first three
new Hub regressions reproduced two failures on the previous implementation;
additional socket deduplication and removal checks were then added.

Full verification used declared runtime/development dependencies, Playwright
1.56.0, its installed Chromium/headless shell and FFmpeg. A temporary local
PATH alias exposed the installed headless shell to the optional World Chat
test, which otherwise searches only for a system `chromium` command. No product
browser code was changed for that alias. Tests used disposable data folders.

```bash
python -m pytest -v --timeout=90 --timeout-method=thread \
  -o faulthandler_timeout=45 --maxfail=10 --junitxml=pubcast-final.xml
npm run test:node
python tools/workbench_preflight.py
```

The exact strict command is preserved in the new workflow. The preflight was
run with PUBCAST_DATA_DIR set to a temporary folder, not the source data tree.
Source and test whitespace checks passed; verbatim backups intentionally retain
original whitespace.

## Run and remaining limits

Extract the complete source ZIP, enter its PubCast directory and run
`python run_reach.py` after initial installation of requirements.txt. Use the
same data directory when restarting. The ZIP contains the complete committed
program source, assets, tests and handoffs; it is not a bundled Python runtime,
dependency installer or model-weight distribution.

Verified here: application startup, account setup, Counter trays, document
edit/save/export/reopen, host-backed restart persistence, camera control and
socket paths, world walking, avatar imports, Studio progress and conversation
storage. Real model generation, physical camera/audio devices, live NDI/RTMP/SRT
feeds, Windows and the owner's GPU/laptop performance remain unverified.
No market-ready or complete hardware commissioning claim is made.
