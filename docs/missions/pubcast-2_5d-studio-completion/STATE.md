# Current state — 2026-10-30

Branch: `pubcast-25d-production-integration-2026-10-30` (separate from working Bella preview and main).

## Implemented in branch, runtime UNVERIFIED
- `static/production25d_core.js`: seven declarative genre packages, shot geometry, event/session core.
- `static/production25d_renderer.js`: layered procedural backgrounds, middleground, furniture/foreground, camera cropping, GLB drawing, graphics and scores.
- `static/production25d_storage.js`: IndexedDB transactional session and media storage.
- `static/production25d_app.js`: browser directing surface, camera cut/dissolve, cue controls, GLB loading, microphone capture/mixer, MediaRecorder, persistence and playback.
- `static/production25d.html`: responsive studio interface and preview/program monitors.

## Not complete / not verified
- Browser runtime and actual end-to-end recorded production not witnessed; run full acceptance sequence.
- Existing Control Room stations and backend orchestration NOT fully integrated; the new browser surface is a provisional local console, not the complete established Control Room.
- Blackbox and server recording integration not verified; local MediaRecorder must not be called full Blackbox.
- Camera rig/keymap, teleprompter, multiple audio channels, VTR, saved camera moves and studio entry point need integration review.
- Genre package staging and avatar occlusion/scale require browser inspection.
- Owner-supplied final images and Control Room photographs pending.

## Next engineering queue
1. Execute Node syntax/unit tests and browser launch of production25d.html.
2. Fix any renderer/recorder/runtime errors observed; validate actual video and manifest.
3. Trace existing Control Room source, keymap, station events, audio/video switcher and backend; integrate without duplicating.
4. Integrate teleprompter, VTR, camera rig and Blackbox as supported.
5. Verify each genre, 3D actor movement, audio, mobile layout, offline behavior.
6. Run objective observation, correction rounds, and full owner handoff.

Always continue after a milestone if actionable work remains.

## Additional integration work
- Added two Node test suites: `tests/test_production25d_core.cjs` and `tests/test_production25d_wiring.cjs` (written but NOT EXECUTED).
- Linked the established `static/control_room.html` navigation to the new 2.5D studio, preserving the existing controls.
- Added `LAUNCH_AND_ASSETS.md` with reproducible local launch, genre verification, asset replacement and recording checks.
- Examined `static/control_switcher.js` (server `/api/switcher/*`), `static/control_stations.js` (recording, chyron, teleprompter, VTR, audio), `static/camera_rig.js` and `static/control_room.html`. Full integration remains outstanding. Existing audio station had console-only mixer behavior; this has now been replaced with checked backend updates (runtime unverified).
- Attempted local GitHub access with `git ls-remote`; failed due container DNS (`Could not resolve host: github.com`). This prevents cloning for local execution via that path. Continue independent source integration and consider other verified test execution routes.

## Shared switcher/audio milestone (October 30)
- Owner directive: **same video switcher and audio mixer** for both environments. Video switcher reference imagery still pending from owner; not a technical blocker.
- Server `modules/switcher_routes.py`: CUT swaps Program/Preview atomically, dissolve validated, write routes require moderator authority.
- `static/production25d_switcher_bridge.js`: stage cameras register into canonical switcher; external source state reported; explicit local-only mode if backend cannot be reached.
- `static/production25d_app.js`: shared switcher attach and backend-driven Preview/CUT/dissolve; local canvas render is not server media ingest.
- Existing Control Room `static/control_switcher.js` now displays command failures.
- Shared `modules/program_audio.py`, `modules/program_audio_routes.py`, `static/program_audio_runtime.js`: authoritative master volume, initial-state sync, browser capture of shared audio bus mix.
- `static/control_stations.js` audio Apply now updates master/dialogue/music via server; removed console-only stub.
- 2.5D local recorder captures mixed audio stream plus optional mic (actual browser execution NOT verified).
- Added test sources `tests/test_shared_studio_switchers.py`, `tests/test_production25d_switcher_bridge.cjs`.
- Isolated trusted-JavaScript parse/mocks PASSED for core, renderer, storage, bridge, app, audio runtime; seven genre viewports validated; all required UI IDs present; shared switcher state changes and local fallback simulated. **This does NOT prove actual browser/pytest integration.**
- Outstanding critical: real browser and FastAPI testing, remote media ingest, Blackbox, full stations/recording wiring.
