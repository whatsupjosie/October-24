# Continuous Engineering Handoff — October 31 → November 1, 2026
**Branch:** `lead-engineering-control-room-tv-studio-2026-10-31` · **Project:** PubCast AI, Rearview Foresight
**Current mode:** Lead engineering onboarding/reconciliation, not release approval.
**Owner:** creative authority; engineering execution belongs to the assigned agent.

## Authoritative orientation
Read `AGENTS.md`, `START_HERE.md`, `LEAD_ENGINEER_DIRECTIVE.md`,
`SOURCE_RECONCILIATION.md` and `ACCEPTANCE_MATRIX.md` in this folder.
The older `docs/missions/pubcast-2_5d-studio-completion/` package documents
what is present and what is still only mocked/tested in isolation.

Company manifesto: `whatsupjosie/Pubcast-Reach`, file
`About Rear View Foresight and Curtsey`.
Company purpose: help people be seen/heard as they want to be.
Motto: **Feic Mo Chroí — See My Heart.**

## This onboarding session actually accomplished
- Created this new GitHub branch from the recent 2.5D integration branch.
  No production source was deleted or merged to main.
- Verified `October-24` integration branch was 130 commits ahead of its own
  main and zero behind at branch creation.
- Compared `October` main and new `October-24` branch at root and eight
  first-level differing directories: zero missing direct named items from
  `October` at those levels. These are incomplete-depth inventories,
  **not** a claim that all historical sources have been consolidated.
- Identified divergent/renamed `static/vendor/three` vs
  `static/vendor/three-0.160.0`; review real import compatibility,
  licenses and versions before moving anything.
- Enumerated other source repositories and wrote a provenance-first
  reconciliation protocol. `The-Prime`, `Wednesday-`,
  `Pubcast-Reach`, older 2i/Counter and PubPartner still need selective
  recursive review for **actual missing** components and artwork.
- Added `AGENTS.md` for coding agents and the complete lead-engineering
  directive, source inventory, acceptance matrix, starter task and this
  live handoff.
- Verified eight package keys in `static/production25d_core.js`:
  `news`, `late_night`, `debate`, `political_discussion`,
  `audience`, `game`, `variety`, `general`.

**Important limit:** This onboarding session has NOT installed dependencies
or launched the server/browsers. It has NOT rerun the October 30 runtime,
Pytest or CI suites. Do not convert documentation progress to functional
completion. Work mode/Codex cloud environment is not yet launched by this
chat; the user must start that agent task in the supported interface.

## Known implementation already on the branch (not proven by this session)
- 2.5D studio source/config/camera presets/renderer/GLB integration,
  local recording, IndexedDB session storage and genre package tests.
- Existing Director/Control Room frontends with camera rig,
  some shared audio/video switching and source controls.
- Authenticated, low-rate JPEG confidence frame publisher/reader for 2.5D
  remote monitors; NOT full-rate video ingest.
- PANIC/blackout/audio control code and camera CUT refactoring.
- Tiny rough-cut editor with source bin, viewer, clacker references,
  30-ms corrections, minimal split/lift/ripple, EDL and JSON handoff.
- Isolated JavaScript checks were reported from a previous session,
  not a full runtime acceptance. Re-test and don't trust labels.

## Critical next executable work — start here, then continue
1. Open an actual clone of the **new** branch in Codex/Work-capable
   environment; print Python/Node/platform versions, Git HEAD and status.
2. Install pinned dependencies, run FastAPI bootstrap/health. Run
   Python and Node regression commands listed in acceptance matrix.
   Investigate prior opaque CI execution failure.
3. Open both Control Room variants and the 2.5D page in a real browser;
   record runtime/console/network errors and fix them, using reviewable
   commits. Verify behavior with **two actual clients**, including
   Program/Preview/camera switcher ownership.
4. Verify each of eight genres with actual GLB assets and 3D movement.
   Check shot composition, scene props, stage scaling/occlusion and
   repeated teardown; correct all faults discovered.
5. Verify real Audio/Video source transport, cue/joystick, teleprompter,
   VTR/graphics, recording start/stop/pause/PANIC/restart/playback,
   auth/roles and failover. Do not claim server recording from JPEG preview.
6. Implement full-rate ingest and Blackbox-linked recording with
   cross-client audio, then build an authoritative **replayable 3D
   production master** (scene state + assets + timecode + audio).
7. Implement/validate selective native high-quality source-based rendering,
   4K minimum acceptance target, practical pass formats and second-machine
   professional handoff without upscaling. Confirm all user media survives.
8. Run three adversarial audit/debug rounds, test all impacted systems,
   preserve Bella walkable-world demo and editor/2i/Counter integrations.
9. Reconcile other repositories without replacing the new working code.
   Owners supply final visual images/approval when it becomes genuinely
   necessary, not before.
10. At every checkpoint update this document with exact commit, tested
    commands/output, failure ledger, remaining next steps. Keep going.

## Known first inspection candidates / tricky edges
- `main.py` is substantial (~4,900 lines); check route include order,
  double imports, source security and handler idempotency.
- `modules/switcher_routes.py`, `modules/production_routes.py`,
  `modules/studio_console_actions.py`: atomic CUT and confirmed state.
- `modules/studio25d_media_routes.py`: lease/auth/source ownership,
  validation and stale-session cleanup.
- `static/production25d_app.js`: avatar lifecycle, remote
  state transitions, MediaRecorder stream/audio, production cues.
- `static/director_switcher.html`, `static/control_room.html`,
  `static/control.html`: legacy/new console inconsistencies and
  truthful feedback. Ensure keyboard mode isn't hijacking production.
- `static/editor_interchange.js`: CMX3600 frame rounding, media
  references, source quality provenance and Resolve import caveats.
- GitHub CI workflows were previously observed failing with empty
  step histories and unavailable logs. Get actual execution evidence
  rather than assume implementation regressions.
- Owner-only outstanding: final switcher images, set plates,
  subjective polish and owner-specific hardware acceptance.

## Exact state on handoff
- **Engineering mission prepared and linked:** YES.
- **New branch created:** YES.
- **October root/direct-child inventory vs October-24:** YES.
- **All historic files audited/imported:** NO; several repos pending.
- **Environment installed and application running in this session:** NO.
- **Control Room functionally complete:** NOT VERIFIED.
- **2.5D studio functionally complete:** NOT VERIFIED.
- **Native high-quality rendering/portable cinema master:** NOT COMPLETE.
- **Owner approval to seal or launch:** NOT GIVEN.

If the engineering agent encounters limitations, keep this ledger
factually accurate and keep working on independent available steps.
Do not ask the owner to perform development work the agent can do.

## Latest CI probe — same day
`pubcast-25d-integrity.yml` now explicitly includes the NEW lead branch
in its push trigger. GitHub Actions run **41200964842** began on
`a06474a1f6c3e8861f29bc793e917c969fad355f`, and both `python-syntax`
and `javascript` jobs are labeled failure. Their returned step lists are
**empty**, so the failing command is unknown and tests cannot be claimed
executed. The next engineer should reproduce locally or inspect runner
diagnostics with actual logs; avoid repeating empty-result calls.
