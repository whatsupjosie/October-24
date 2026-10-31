# Engineering decisions

- Prioritize fixed/constrained camera 2.5D television production; preserve separate walkable world.
- Seven independent declarative show packages share one renderer and console.
- Use original procedural scenery as replaceable artwork; do not copy trademarked television sets.
- Reuse existing `world_walk_glb.js` GLB bridge; do not substitute flat character sprites.
- Browser-local MediaRecorder + IndexedDB is a standalone production slice; do not misrepresent as completed Blackbox/server integration.
- Keep work isolated in integration branch; do not merge without owner authorization.

## Shared switcher decision (owner, October 30)
- Both studio environments use the same canonical video switcher and program-audio mixer: do not make competing station implementations.
- 2.5D genre cameras register with the canonical CameraManager under `p25d_<genre>_<shot>` IDs. Existing Control Room switcher can then select them. A browser hosts the actual local 2.5D renderer; this is NOT yet a video stream returned to the server for remote viewing.
- If canonical backend/auth is unavailable, show explicitly LOCAL ONLY, not fake synchronized state. Do not override the backend state after a failed switch.
- Shared audio uses existing ProgramAudioState, including one new master_volume scalar, existing dialogue/music/SFX/etc buses, and a program capture output; local mic can join recorder without creating duplicate playback buses.
- Owner supplies video switcher artwork/reference later; it is not a blocker to wiring.
