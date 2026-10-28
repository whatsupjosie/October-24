# PubCast recorded sync and separate audio tracks

Base commit: `df9d30fc243a84fdab4e5a256a2d8dbe65294e86`.
Branch: `codex/recorded-slate-sync-2026-10-28`.

## Curtsey's final direction

The recurring sync marks belong in the editor, outside the picture. Permanent
red timeline ticks repeat every 15 seconds across video and audio lanes. A
separate Sync Reference audio track carries the timing blips. Music, sound
effects, and vocals/dialogue remain separate tracks. Distortion belongs in an
effect chain on the relevant track, rather than automatically becoming another
source. An editor can jump to the nearest 15-second anchor, adjust that section,
then work backward through earlier anchors. The original recordings stay intact.

## What changed

The director console now has a live program-stage monitor and a take-recorder
control on the production slate. It records the actual rendered stage and routed
program audio. The original FFmpeg virtual test-pattern recorder remains separate
and is not presented as a stage recording.

The recording includes the raised/closing slate as pre-roll. The initial clap
provides a visual mark and a short audio cue for calibration. Once the director
dismisses the slate, the shot contains the stage picture. The recurring red
marks are not burned into the video. The recurring audio blips do not enter the
program mix or the audible monitor path.

A common browser audio clock feeds a 14-channel PCM capture graph. It produces
stereo dialogue, music, sound-effects, UI, VTR, and room stems, plus mono director
floor audio and Sync Reference. The stems have identical sample-frame counts.
Sync Reference captures the actual scheduled blips on that graph; its final
WAV is not reconstructed from a list of wall-clock guesses.

After saving, FFmpeg decodes the recorded visual and audio clap marks, measures
their offset, produces an aligned copy, and checks that copy against a tolerance
of one encoded frame plus 5 ms. Missing cues, invalid media, or failed alignment
produce an unverified result. The original file is retained. Video is conformed
to a 30-fps timeline without speeding up or slowing down the performance; a slow
rendering device can still deliver fewer distinct captured frames.

The captured reference cue anchors the PCM stems to the aligned video. Downloads
include individual PCM WAV tracks, a clean aligned take, an edit copy with the
program mix plus eight separate audio tracks, and timing metadata. The program
mix is the default audio stream; Sync Reference and the separate stems are
non-default streams. Sync Reference is also unchecked in the editor. An NLE may
import all streams, so keep that reference track muted in the final mix.

The take editor shows permanent red ticks in its timeline, separate from its
video element. It can audition selected tracks, jump backward/forward by
15-second anchors, and nudge each track by 5 ms within the current section.
Edit decisions save separately. **Render final take** applies those section
offsets, remixes the enabled production stems, excludes Sync Reference from the
program mix, and stream-copies the picture. The reference remains available as
its own non-default audio stream. Render output is published after completion;
clients cannot download a half-written MP4.

The browser editor uses a video-only WebM preview for codec compatibility. Final
MP4 and WAV downloads remain available for other editors.

## Operator workflow

1. Start the existing PubCast host and sign in. Open `/director-console`.
2. Open **Production slate**, fill the scene/take fields, save, and call stations.
3. Complete the department roll call. Enable the director microphone when needed.
4. Choose **Arm stage take recorder**. Clap once within two minutes of arming.
5. Dismiss the slate and film. The reference blips continue silently on their own
   track at 15-second intervals.
6. Choose the floating **Stop take / save** button. The local original downloads
   immediately. The host measures the encoded cue and saves the separate stems.
7. Open **Open take timeline**. The recurring ticks appear on all timeline lanes.
   Keep Sync Reference muted for normal playback; enable it to inspect anchors.
8. Jump to a nearby marker, adjust the relevant track, audition, and work backward
   as needed. Save the edit decisions. Choose **Render final take** to export the
   corrected program and separate audio tracks.

## Preservation and scope

Five modified original files are preserved byte-for-byte in
`RECORDED_SYNC_ORIGINALS_2026-10-28.md`, including original line endings and
SHA-256 hashes. Earlier Copilot/control-room originals and supplied reference
images remain in the complete archive. Main and Copilot's branches are untouched.

Recorded cue verification applies to the produced artifact. It does not certify
unconnected cameras, remote hardware clocks, acoustic speaker latency, or media
that bypasses PubCast's routed audio graph. A timing track is a useful reference,
not proof that frames or samples were never dropped. Section adjustments should
be auditioned at their boundaries. No automatic time-stretching or respeeding is
used to conceal missing material.

The browser recorder stops at ten minutes, 120 MiB of encoded chunks, or 100 MiB
of non-silent PCM storage, whichever applies first. Host uploads are capped at
128 MiB per file. PCM stems can be larger than compressed video. On a host-save
failure, the local original and local stem-download controls remain available.

FFmpeg, ffprobe, the existing Python dependencies, and a browser with Web Audio,
canvas capture, and MediaRecorder are required. The repository ZIP is complete
source and included assets; installed dependencies and external model weights
are not bundled into it. A local host can operate without internet access.

## Verification

- 29 focused Python tests passed: encoded offset measurement/correction in both
  directions, missing-cue rejection, upload/download permissions, original-file
  preservation, slate permissions, camera actions, and section rendering with
  silent pre-roll. A tone confined to Sync Reference stayed out of the rendered
  program mix.
- The real-browser end-to-end test passed after recording beyond 15 seconds.
  Independent 440/660/880 Hz test signals stayed in their music/dialogue/effects
  stems. Eight captured stems had the same sample-frame count. The periodic
  reference blip was present on its own track and absent from the program mix.
  The edit copy contained nine audio streams with only the program mix default.
- The same browser test opened the editor, verified the red timeline ticks and
  muted reference checkbox, saved a per-section track nudge, and downloaded a
  final render produced from those edit decisions.
- The existing Node suite passed all 10 tests. JavaScript syntax, Python
  compilation, source whitespace, and verbatim-original preservation checks passed.
- Tests use generated signals and fake microphone input where applicable. No
  claim of physical camera or speaker-latency certification is made.
