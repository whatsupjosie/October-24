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
- Examined `static/control_switcher.js` (server `/api/switcher/*`), `static/control_stations.js` (recording, chyron, teleprompter, VTR, audio), `static/camera_rig.js` and `static/control_room.html`. Full integration remains outstanding. Existing audio station has console-only mixer behavior and must not be called wired.
- Attempted local GitHub access with `git ls-remote`; failed due container DNS (`Could not resolve host: github.com`). This prevents cloning for local execution via that path. Continue independent source integration and consider other verified test execution routes.
