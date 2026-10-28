# Camera Stability Handoff — 2026-10-28

## Branch
camera-stability-review

## Goal
Stabilize the PubCast camera state and broadcast path so the system behaves like a real production pipeline rather than a loose coordination layer.

## Current status
This branch preserves the working camera state model and makes the event flow more trustworthy.

### Included improvements
- CameraManager is the authoritative state holder for program/preview state.
- Source removal clears stale program/preview references.
- Camera events carry stable identity metadata (`event_id`).
- Broadcast bridge deduplicates repeated event IDs.
- Event cache eviction is ordered and bounded.
- Shutdown logic cancels and reaps outstanding tasks instead of leaving leaked workers behind.
- The branch includes a first regression suite for state correctness and bridge stability.

### Files touched
- `modules/cameras.py`
- `modules/camera_broadcast.py`
- `tests/test_camera_manager.py`

## Why this is still not “market ready”
The camera path is stabilized enough to be trusted for state correctness, but it is not yet complete as a full production app. The remaining work is operational verification and feature expansion:

1. Import/startup smoke path
2. Application-level camera bridge boot integration
3. Timeout/failure-path shutdown verification in the app lifecycle
4. Real stream health and failover checks for NDI/RTMP/SRT sources
5. Camera preset, shot management, and live operator workflow

## Minimum verification bar before merge
The following checks should be run before calling the branch stable:

```bash
python -m pytest tests/test_camera_manager.py -q
```

```bash
python - <<'PY'
import asyncio
from modules.camera_broadcast import CameraBroadcastBridge
from modules.cameras import CameraManager, CameraSource, CameraTransport

manager = CameraManager()
manager.register(CameraSource("cam_a", "Cam A", "studio", "test", CameraTransport.VIRTUAL, "virtual://cam_a"))
manager.register(CameraSource("cam_b", "Cam B", "studio", "test", CameraTransport.VIRTUAL, "virtual://cam_b"))
manager.set_program_source("cam_a")
manager.set_preview_source("cam_b")
print(manager.snapshot())
manager.take()
print(manager.snapshot())
print("OK")
PY
```

Additional startup/shutdown checks should also be run:
- import the app startup path
- instantiate the bridge without circular import errors
- trigger a blocked task and confirm `stop(timeout=...)` reaps it
- verify bounded cache eviction retains the newest event IDs and discards the oldest

## Operational recommendation
Do not merge as “fully market-ready.” Treat this as a serious stabilization improvement that is now much closer to production trust, and continue from here with:
- app-level lifecycle verification
- live feed health checks
- operator workflow tests
- camera preset and capture behavior

## Handoff note
This branch is intentionally isolated and reviewable. It contains the camera stability work and the first production-style verification scaffold without pretending to be a feature-complete product.

The next meaningful milestone is not “more features.” It is proving the camera bridge is safe under startup, runtime, and shutdown conditions, and then moving forward with the live source health and recording pipeline.
