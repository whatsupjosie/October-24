# Camera state and delivery continuation — 2026-10-28

Branch: `codex/camera-state-and-delivery-2026-10-28`.
Base: `9ed775d20f4decd013edce8a3d6d595622ab27c8` (previous shutdown fixes).

## Completed

1. Pose edits are validated in full before any camera fields change. Invalid
   vectors, booleans, nonfinite coordinates, and invalid FOV are rejected.
   Rejected edits leave the original pose and event stream untouched.
2. The switcher PTZ API returns HTTP 400 for invalid pose edits, preserves
   HTTP 404 for an unknown camera, and still accepts valid edits.
3. Removing a camera selected as both program and preview clears both
   references before listeners are notified.
4. Camera broadcast sends are serialized, so a slow earlier send cannot
   finish after a newer send and roll the receiving stage backwards.
   Failed sends release the send lock; shutdown cancels the active sender
   and queued senders. The lock is recreated on bridge restart.
5. FFmpeg worker cleanup attempts all owned pipes even if closing one fails.
   Close failures are logged. Process ownership and capture flags are reset
   in a final cleanup block, including when process reaping raises.

## Preservation

The original Copilot backup from the first pass remains intact:
`COPILOT_CAMERA_ORIGINALS_2026-10-28.md`.

`CAMERA_BEFORE_CONTINUATION_2026-10-28.md` preserves all four source files
edited in this pass verbatim at the base commit, with SHA-256 hashes.
Both main and Copilot's working branch remain unchanged.

## Verification

Linux, Python 3.12.14. The first nine new regression cases all failed on the
base version before fixes. The final file has 13 cases, including successful
pose editing, API error behavior, failed-send recovery and queued shutdown.

```bash
python -m pytest tests/test_camera_state_and_delivery.py tests/test_camera_shutdown_regressions.py tests/test_camera_manager.py tests/test_camera_broadcast.py tests/test_camera_capture_cleanup.py tests/test_round4_runtime_truth.py tests/test_studio_camera_preflight.py tests/test_01_startup.py tests/test_studio_console_action_routes.py tests/test_studio_console_actions.py -q
```

**92 passed**, one existing Starlette/AnyIO deprecation warning. pytest-asyncio
also prints its existing fixture-loop configuration deprecation at startup.
This includes real application startup, socket camera cuts, real FFmpeg file
capture, cancellation/timeout checks, API validation, and the new regressions.
`git diff --check` passed. Four preserved source blocks were verified against
the base commit, byte-for-byte and by hash.

## Limits and next work

This is focused regression coverage, not the full program suite or a hardware
commissioning claim. Physical cameras, live NDI/RTMP/SRT feeds, Windows and
GPU performance remain untested. Broadcast ordering is guaranteed for sends
scheduled by this bridge; it does not add global ordering across multiple
host processes or make CameraManager a fully synchronized multithread store.
A permanently blocked socket still needs shutdown or disconnection; this pass
does not add a bounded event queue or a slow-client eviction policy.

Next: verify live source reconnect/failover and recording behavior with actual
devices, and assess bounded buffering for slow clients without dropping
authoritative camera state.
