# PubCast control room, mini console, and shared production slate

Base: `62fda27090ef81c747dbc19b9d2543834d58a1c0`.
Work branch: `codex/control-room-wiring-2026-10-28`.
Copilot's branches and main are not changed by this work.

## Curtsey's direction

The large leather-chair image is the director's console. A new angle is pending;
physical hotspot placement must wait for that angle. The on-set mini console
can work now, with camera selection, its own screen, joystick, preview, and cut.
Aim, movement, and lens controls remain separate selectable modes while the
physical joystick mapping is being decided.

The raised clacker is the global call to stations. Every signed-in PubCast
browser screen must show the same slate during roll call. It stays raised until
the director initiates the clap. The director's actual microphone carries the
spoken call, not generated speech. Only the director can edit, or an assistant
the director explicitly delegates. Each assigned participant can report their
own department ready; they cannot edit the production fields or report someone
else ready. Revoking delegation takes effect on subsequent server commands.

The brain artwork is session crew setup: job, configured AI profile, instructions,
flight patterns, and enable/disable. These are production assignments and never
character or cartridge edits. The Feic Mo Chroí emblem is reserved for one or
two prominent placements, not repeated throughout the controls.

## Implemented behavior

- The director console now uses the correct leather-chair artwork and a working
  control strip, rather than applying the old image's coordinates to this image.
- The mini console uses the supplied screenshot without modifying its pixels;
  CSS frames the artwork and positions the live screen, joystick, CUT, and CREW.
- Virtual camera pose changes reach the actual Three.js stage through the camera
  event bridge. The mini screen pins its chosen source independently of program.
  Three.js is served from the existing local vendor files for offline use.
- Aim adjusts pan/tilt; Move trucks/dollies and permits lift/lower; Lens adjusts
  roll/field of view. Unsupported hardware motion returns a clear error.
- Program/preview cuts use the manager's atomic take operation. Console audio
  commands reach the existing program-audio event queue; volume zero is retained.
- Audio-console sliders no longer emit duplicate pointer-up/change commands;
  knobs no longer also send an unrelated default click action.
- Console state includes cameras, audio buses, recording sessions, and actual
  encoder-process/byte status. Panic stops active/paused captures and program
  audio. The capture engine also shuts down with the app.
- The walkable control room opens director/audio consoles in a modal and returns
  to the same walking position. Its right console offers the mini console; its
  final permanent studio role remains undecided.
- A shared production slate is injected into PubCast HTML screens. Only the
  outermost page mounts it, avoiding duplicate boards in hosted program frames.
- SQLite preserves production fields, director, assistant permissions, crew,
  department assignments, readiness, and a bounded action history across restart.
  Revision checks and writes share a transaction to reject stale edits.
- Only a verified moderator/owner can open a production. Once open, ownership
  belongs to that director, even against another moderator or owner account.
- Standby resets readiness and displays the raised board on every connected
  screen. Only an assigned account can check its department in. The clap waits
  for assigned departments, and schedules a common future cue time.
- The director's microphone uses real browser capture and authenticated sockets
  to send mono PCM to listeners. The server checks director ownership, origin,
  frame size, rate, finite samples, and bounded outbound delivery. Microphone
  tracks stop on dismissal, navigation, or voice disconnection.
- Session crew assignments have typed controls and save only to the production
  session. Saving them does not start autonomous AI agents or claim a model ran.

## Using this build

1. Run the existing PubCast installation and sign in through Reach. For example,
   the tested host command is `python -m uvicorn main:app --host 127.0.0.1 --port 8000`.
2. Open `/director-console`, `/audio-console`, or `/static/mini_console.html`.
3. Choose **Production slate** in the lower-right corner. A moderator/owner can
   open a production and becomes its director.
4. Type production, scene, take, actors, and notes; choose **Save slate**.
5. Assign department names to real account IDs and explicitly grant any assistant
   editing rights. Crew assignments belong only to this production.
6. Choose **Call stations / roll call**. Every signed-in screen shows the same
   raised clacker. Participants choose **At station / ready** for their assignment.
7. Listeners choose **Enable director audio** once to satisfy browser playback
   rules. The director chooses **Start director microphone** and grants browser
   microphone permission. Use HTTPS or localhost for microphone access.
8. Once assigned departments are ready, choose **Clap / begin take**. Dismiss the
   board on all screens when appropriate, or end the production to release it.
   Scene notes remain editable after the clap by authorized editors.

## Practical limits

This is a connected implementation and verification pass, not hardware certification.
The live floor microphone currently uses one PubCast server process; multi-worker
or multi-host voice distribution requires a shared relay. An offline machine can
run the host and local assets, but other participants must have a network path to
that host to see the shared slate or hear its microphone.

Clock offset and approximate round-trip uncertainty are measured for the shared
cue. Browser animation and audio are scheduled against that estimate. The display
explicitly says **recorded audio/video alignment unverified**. The cue is not yet
sample-accurately stamped into FFmpeg recordings or hardware camera tracks. No
claim of correct recorded sync is made, and recording is not artificially slowed.
Physical microphone/speaker latency and a real multi-device take still need
measurement. The virtual FFmpeg source records a test pattern, not the rendered
stage; controls label that limitation.

The mini screen is a virtual-stage preview. NDI/RTMP/SRT video monitoring and PTZ
need actual device drivers and integration. Browser microphone/playback permission
still applies. Legacy production tools remain available; the director/audio/mini
control strips are the verified workflow in this pass.

## Original preservation and downloads

`CONTROL_ROOM_ORIGINALS_2026-10-28.md` preserves 22 original source files verbatim,
with SHA-256 hashes, from the base commit. The five supplied screenshots are
preserved unchanged under `static/control_room_assets/`, with SHA-256 hashes in
`REFERENCES.json`. The complete source archive includes all repository files,
assets, tests, and these handoffs. Dependencies and external model weights are
installed separately; they are not silently included or claimed to be included.

## Verification results

- Broad Python run: 2,034 passed, 2 intentional optional-protocol skips. One
  existing assertion expected byte-for-byte original HTML; it was updated to
  require exactly one slate loader while preserving the original Counter HTML,
  and then passed through the real application lifespan.
- Final browser/permission run: 10 passed, including real browser microphone
  capture from a fake test device, floor-socket delivery, non-silent WebAudio
  playback on a second screen, and track release when dismissed. This caught
  and fixed the saved-token path that lacked a socket session cookie.
- Focused camera/audio/slate routes and bridge run: 22 passed; capture cleanup
  and hotspot-manifest checks also passed.
- Existing Node suite: 10 passed. JavaScript syntax and Python compilation passed.
- The original main and Copilot branch tips were checked and remain unchanged.
  Alex's canonical vessel blob remains `96fa66a728d07d5ff43b0d3d7fc17a466765cec1`.
- No physical microphone, camera protocol input, speaker latency, or recorded
  multi-device sync certification is implied by these automated checks.
