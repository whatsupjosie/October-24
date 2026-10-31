# PubCast — next engineering shift: make the 2.5D studio PLAYABLE, then avatars
Date: 2026-10-31, America/Los_Angeles
Authority: PubCast owner / Rear View Foresight. Engineer assignment: **build and repair, not a whole-repository audit**.

## Start here
**Authoritative repository**: https://github.com/whatsupjosie/October-24
**Your writable working branch**: `codex/studio25d-playable-avatar-handoff-2026-10-31`
**Based on**: `pubcast-25d-production-integration-2026-10-30`.
**Preserve** `main`, the 2.5D integration branch, `bella-live-preview-2026-10-30`, all Copilot/Claude/Codex donor branches, and current real working scenes. Do not merge to `main` without the owner's permission.

## The owner wants an actual experience, not another plan
1. **Focused health check**: create a runnable environment, install documented dependencies, run relevant existing tests, boot FastAPI and browser studio, inspect real errors, fix broken imports/routes/state races/console faults. Prioritize issues blocking live operation, not every old module in the repository. Establish objective runtime evidence.
2. **Complete and polish the 2.5D TV studio**: preserve 8 genre packages, real GLB actors, both Program/Preview angles, canonical shared switcher + audio mixer, camera cuts/transitions, working control-room interactions, camera controls, world/2.5D source sharing, reliable operator feedback, proper capture and recordings. Real output only: never label a JPEG confidence monitor as a broadcast recording or Blackbox master.
3. **Then tackle avatars seriously**: connect existing walkable 3D performers and avatar maker/dressing/green-room workflow, reuse existing MakeHuman/GLB and avatar bridge rather than sprites or a replacement rig. Make character selection, loading, animation, staging, movement and camera shooting reliably visible and testable. Be careful with async GLB loader generations/lifecycle and visual occlusion.
4. **Player-mode acceptance**: the owner should be able to start PubCast, enter the studio, select genre and actors, block a scene, choose cameras, operate cut/dissolve and audio, capture an actual shoot, review the result, and reach the minimal rough editor—without engineer-only terminal commands or needing to guess what to click. Record and repair usability blockers observed in this real experience.
5. **Proceed one ingredient at a time**, shipping small verified increments on the working branch. Prefer real observed behavior over speculative architecture and feature expansion. After each increment continue until a genuine blocker, then report precisely what is blocked and why.

## Scope boundary: don't turn PubCast into finishing software
- Production, performances, recording, low-fi proxies, synchronized selects, rough cuts and full-quality **portable** footage are in scope. Fancy editing effects, compositing suites, grading and final theatrical delivery are not. DaVinci Resolve Free is the recommended external finisher, not a sponsor or mandated dependency.
- The current local 2.5D recorder is approximately 1280×720, ~3 Mbps. It **does not** fulfill the hard professional-quality export promise. Preserve production source data and assets for later *deterministic*, selected-shot full-fidelity rendering. Do not upscale a 720p proxy and claim 4K master.
- Owner's 15-second timecode clacker and separate audio blip track are intended for sync. The rough editor has marker/offset logic, including non-destructive **+0.030 second** per-track shift. Actual multi-client sync capture and rendering are still unverified. Source-level replay and true high-fidelity export remain release blockers, not requirements to invent a giant finishing editor.

## Where to look — established branch code
Start `main.py`, relevant FastAPI routers in `modules/`, and:
- `static/production25d.html`, `static/production25d_app.js`,
  `static/production25d_core.js`, `static/production25d_renderer.js`,
  `static/production25d_storage.js`, `static/production25d_switcher_bridge.js`.
- `static/production25d_frame_publisher.js`, `static/studio25d_remote_feed.js`,
  `modules/studio25d_media_routes.py`, `modules/switcher_routes.py`,
  `modules/program_audio.py`, `modules/program_audio_routes.py`,
  `modules/production_routes.py`, `modules/studio_camera_preflight.py`.
- Existing Control Room/actors: `static/control_room.html`,
  `static/control.html`, `static/control_stations.js`,
  `static/director_switcher.html`, `static/world_walk.html`,
  `static/world_walk_glb.js`, `static/avatar_glb_motion_consumer.js`,
  `static/camera_rig.js`, `modules/avatar_performer.py`.
- Minimal rough editor: `static/editor_sync_core.js`,
  `static/editor_sync_store.js`, `static/editor_sync_station.js`,
  `static/editor_interchange.js`; don't expand it into a professional finisher.
- Source of current mission checkpoints and evidence:
  `docs/missions/pubcast-2_5d-studio-completion/{MISSION,STATE,BLOCKERS,DECISIONS,VERIFICATION,OWNER_HANDOFF,THREE_SOLUTIONS_PIVOT,EDITOR_AND_FINISHING_BOUNDARY}.md`.

## Concrete suspected failure points to verify early (not claims of fixes)
- `modules/production_routes.py` panic/audio stop and video cue imports/HTTP execution need actual route tests.
- `POST /api/switcher/select`: check pair-selection concurrency/rollback on failure; mere sequential writes are not truly atomic.
- Source-stage server frame publication requires authentication; verify `static/reach_auth.js` supplies credentials for stage and remote Director under enforced auth, not just dev mode.
- Director confidence displays must not silently advertise JPEG previews as real broadcast program ingest. Check stale-frame text overwritten during periodic status poll.
- Genre/performer GLB ID renaming and async load generation cleanup may break linkage; test real skeletons, gestures and visible motion in browser.
- Multi-client switcher/audio/PANIC/cut operations need actual live browser test and independently owned source registration/release, not only mock state.
- Existing 2.5D local recording is browser-only; no server video/Blackbox guarantee and no audio capture from other browser sessions; server refuses confidence-only virtual cameras for good reason.
- Current studio screenshots may show developer sets; keep replaceable owner artwork and full scenes intact.
- The control-page keyboard map historically assigned Space to live CUT. Recent branch disarms it while inside rough editor; verify this in a real page.

## Verified vs UNVERIFIED
- Existing source-level 2.5D audit exercised isolated mocked V8 scenarios (12/12 reported; not full browser).
- Additional rough editor: 12/12 microsecond clacker/EDL/rough edit V8 tests, 7 JS syntax parses, 48 bound UI controls, fake DOM smoke. **Not** a browser/Node command or real Resolve acceptance.
- Actual GitHub Actions workflow `.github/workflows/pubcast-25d-integrity.yml` had failed/opaque job logs earlier; do not infer real test result from failed runner launch.
- **Not yet observed**: full local server+browser playback, MediaRecorder+GLB+audio integration, 4K deterministic replay render, exact DaVinci import/relink, cross-machine portability.
- Tests to run: `node --test tests/test_production25d_core.cjs tests/test_production25d_wiring.cjs tests/test_production25d_switcher_bridge.cjs tests/test_studio25d_confidence.cjs tests/test_editor_sync_interchange.cjs`; targeted `pytest` of production/studio/recording/switcher/GLB integration; then actual app tests with console/network screenshots or logs.

## External source inventory — don't blindly overwrite active work
Repository tree comparisons performed 2026-10-31 using GitHub's **recursive tree API**:
- Working 2.5D integration branch: 1,662 blobs.
- October-24 `main`: 1,622 blobs; **zero path names missing** from the integration branch. 19 blob SHAs differ.
- `bella-live-preview-2026-10-30`: 1,630 blobs; **zero path names missing** from the integration branch. 16 blob SHAs differ. Especially compare `static/world_walk_glb.js`, `static/control_room.html`, switcher and recording files. Preserve the functioning Bella original.
- Another repository `whatsupjosie/October`: 1,546 blobs; only five distinct names absent, and 43 differing shared files. Treat as donor, not authority.
- `whatsupjosie/Wednesday-`: 1,198 blobs with 969 paths absent from the integration branch, many inside `rust_crate/`, `rubish/`, `bin/` or development artifacts. Do NOT drag these in wholesale. Look at existing avatar/production modules only if needed.
- `whatsupjosie/Pubcast-Reach` has 34 distinct paths, including historical PubWorld and camera architecture documents. `Pub-Partner-Base-Horizon` has 13 distinct names and some changed shared paths. These are *candidate donors*, not evidence of missing current production code.
- Existing specialized branches include `codex/camera-shutdown-hardening-2026-10-28`, `codex/control-room-wiring-2026-10-28`, `codex/recorded-slate-sync-2026-10-28`, `codex/makehuman-demo-walker-2026-10-30`. Compare their functionality and bring in only needed, proven improvements.
- Additional ChatGPT Library archives awaiting targeted reconciliation: `PubCast_Complete_Sync_And_Stems_2026-10-28.zip`, `PubCast_Complete_Control_Room_2026-10-28.zip`, `PubCast_Complete_Agent_Pass_2026-10-28.zip`, `PubCast_Complete_October-24_2026-10-28.zip`. They have **not been exhaustively compared**. Obtain only if the targeted subsystem shows missing code. Do not claim all external files were migrated.

## What constitutes progress
- A real, runnable studio health baseline and a short list of observed faults; fixed critical blockers, regression tests passing.
- A user-visible, repeatable 2.5D production flow from entering stage to watching real recorded material.
- Then substantial avatar lifecycle/animation/control integration verified on the stage.
- Keep commits discrete, preserve the source-of-truth history and user's original designs, don't create TODO/stub pathways.
- Do not stop work after a status report. Continue implementation, test, debug and fix; report only real blockers. Do not merge or claim polished/finished until real runtime evidence supports it.

**Success is measured by the owner being able to PLAY PubCast—not by the size of the audit.**
