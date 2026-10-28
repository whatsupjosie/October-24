# Camera shutdown hardening — 2026-10-28

Base: `camera-stability-review` at `e243181bab18ec5baf865a35092c48488be3dfce`.
Work branch: `codex/camera-shutdown-hardening-2026-10-28`.
Copilot's branch and main are not modified by this work.

## Original code preservation

`COPILOT_CAMERA_ORIGINALS_2026-10-28.md` contains six full original files,
including the camera modules, original tests and application lifecycle code.
Each fenced block was compared byte-for-byte with the base commit and its
SHA-256 was checked before publication. The backup is not a summary or diff.

## Changes

- Camera broadcast shutdown retains unfinished tasks and raises TimeoutError
  when cancellation does not finish within the deadline. Restart is refused
  until the old tasks finish. A caller can retry stop to complete cleanup.
- Queued worker-thread camera callbacks are tied to their subscription's
  generation, so they cannot send after stop or across a stop/start cycle.
  Dedupe cache mutations and task registration now happen on the owning loop.
- Capture shutdown waits for the executor worker after killing ffmpeg. It
  does not cancel the executor future (which cannot stop the thread). An
  unfinished worker remains owned, reports an error and prevents restart.
- Both application lifespan paths finish the other subsystem cleanup before
  re-raising a camera broadcast timeout. A camera timeout is not logged as a
  successful full shutdown.
- Copilot's shutdown test now checks actual task completion, and its dedupe
  test uses the public start/stop lifecycle.

## Verification (Linux, Python 3.12.14)

The first seven new regressions were run against Copilot's original modules:
six failed, reproducing the bugs, and one existing cleanup case passed.
The final nine regressions include two isolated real-application lifespan
checks (first boot and re-entry).

Final command:

```bash
python -m pytest tests/test_camera_shutdown_regressions.py tests/test_camera_manager.py tests/test_camera_broadcast.py tests/test_camera_capture_cleanup.py tests/test_round4_runtime_truth.py tests/test_studio_camera_preflight.py tests/test_01_startup.py tests/test_studio_console_action_routes.py tests/test_studio_console_actions.py -q
```

Result: **79 passed**, one pre-existing Starlette/AnyIO deprecation warning.
pytest-asyncio also emits a configuration deprecation at startup. This run
includes real FFmpeg-generated file input, real app boot, room socket delivery
for five camera cut routes, synthetic forced-kill/timeout tests and shutdown
cleanup checks. `git diff --check` passed.

## Limits

This is a focused camera regression run, not the full program suite. No
physical cameras, NDI/RTMP/SRT feeds, Windows, GPU performance, or recording
hardware were tested. A coroutine that refuses cancellation or an executor
thread that never returns cannot be forcibly stopped safely by Python; the
change reports and retains that condition instead of hiding it.

The separate `stabilize-camera-capture` branch at `5332687` is not merged here;
this patch builds on the reviewed branch's existing FFmpeg pipe cleanup.
