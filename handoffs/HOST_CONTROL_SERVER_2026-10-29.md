# Host control, server half, 2026-10-29, Claude

## Reason

Josie, 2026-10-29: build host control (possess, timeout, profile, gifts, tracker). Design is in `handoffs/HOST_CONTROL_SPEC_2026-10-29.md`. This is the first code for it: the server side, built on the existing governance engine and hub.

## What changed

| Path | Change |
| --- | --- |
| `modules/host_control.py` (new) | `HostControl` and the routes under `/api/host`. Possess and release (the existing avatar freeze, plus who is in control, a timer and an automatic release), drive (host clicks go to the possessed person only), timeout and end-timeout (teleport to the disciplinary side of the waiting room with recording on; ends by itself or by the host), profile (title, position, notes, tracked; the name can never change), privileges (`control_room`), gifts (control room access, accessory), and the tracker log (`data/people_log/<person>/<date>.md`, written only for tracked people). |
| `modules/pubworld_private.py` (new) | Private delivery to walker sockets. See "A finding" below. |
| `static/world_walk_live.js`, `static/world_walk.html` | The walker reacts to the host: the possession notice is shown as plain text exactly as sent, the person's own keys and clicks no longer walk while the host has control or they are in the waiting room, the host's drive moves the avatar, and release and the end of a timeout hand control back. A banner shows the title, the wording and the time left. |
| `main.py` | Imports; mounts the router next to governance; the walker socket handler registers a socket under its verified person (enforced handshake, or a valid in-band token) and removes it when it closes. |
| `tests/test_host_control.py`, `tests/test_pubworld_private.py`, `tests/test_host_control_end_to_end.py` (new) | 38, 4 and 6 tests. |

Rules built in:

- Reading (`state`, a profile, the tracker log) needs `mod`. Taking control, timeout, editing a profile, privileges and gifts need `admin` (the owner passes). Set by `CONTROL_ROLE` and `READ_ROLE`.
- No audit entry, no action: the governance audit entry is written first, and if it cannot be written the action is refused (503).
- Possession is undone, and the audit says so, if nobody verified received the notice (409 `target_not_connected`). It is also refused for someone already frozen by other means (409 `already_frozen`) and for a second possession of the same person in any letter case.
- A possession and a timeout each keep their own timer.

## A finding that shaped this (observed in the code)

The walker's socket (`/pubworld/ws/{client_id}` in `main.py`) is not in the Hub, so `Hub.send_private_event` reaches nobody there. The first version of this code would have refused every possession for that reason. Three ways to fix delivery were weighed: put the walker socket into the Hub (reuses existing delivery but changes shared Hub behaviour), give the walker socket its own per-person registry (smallest change, no extra data use), or have the walker poll an inbox (works anywhere but spends the limited data on constant polling and arrives late). The second was built. `HostControl` tries every channel it was given and counts a delivery on any.

## Josie's wording is not in the code

The possession notice and the timeout message are read from `data/host_control/messages.json` (keys `possession_notice` and `timeout_notice`) at the moment they are used. Possession refuses with 409 `possession_notice_not_set` until Josie has put her approved text there. Timeout still teleports without a message. The tests use made-up wording.

## Tested (observed, Linux, Python 3.13)

48 passed (`tests/test_host_control.py`, `tests/test_pubworld_private.py`, `tests/test_host_control_end_to_end.py`).

Unit and route level: every route refuses a viewer; moderators can read but not take control; the notice reaches the target only and the public mark carries none of its words; possession is undone when undelivered; an already frozen person is not taken over; letter case is one person; no audit entry means no action; a timeout ends by itself or by the host; separate timers; two possessions at once, only one wins; 300 rounds of hostile input on every route (odd ids, huge values, NaN and Infinity, bad JSON, path tricks) never cause a server error and write nothing outside the folders it owns.

End to end, through the real app (`main.app` under uvicorn, a throwaway data folder, auth enforced) with real walker sockets that prove who they are with a token: a possession reaches both tabs of the possessed person (any letter case) and not a third person; drive, timeout (with recording flag and the configured wording), end-timeout and release each arrive as the right event at the possessed person only; a person with no verified socket, a closed socket, a socket that sent no token and a socket with a wrong token cannot be possessed; viewer and moderator are refused and an admin may try, by the real app; the governance audit log holds POSSESS, RELEASE, TIMEOUT and TIMEOUT_END.

Regression: 15 tests in the websocket, route-authorization and walker-host files fail. The same 15 fail with this change removed (checked), so none are caused by it. The PubWorld socket connect tests pass.

## Not done, in this order

1. Roster: the walker must send position, who they walk as and stats; the host keeps and pushes them. Today the host's socket handler only acknowledges a room change, so nobody can be selected from a list yet.
2. The disciplinary waiting room has no picture or room in the world data (`waiting_room_disciplinary` is only an id). A person in timeout is locked and sees the banner, but is not shown a different place until that room exists.
3. The panel (portraits, profile, security tab, possession button). Its look is Josie's to decide; it should be a tray in the Counter, following the tray art rules.
4. Voice, the ban list screen and alias search (see the spec).

Tested in a real browser (added with the walker handling): the notice appears with the exact configured wording; the person's own keys and clicks do not walk; the host's drive moves the avatar to the point; release gives control back; the timeout banner shows the configured wording and locks input; ending it frees the person; no page errors.

Untested: two hosts at once; a restart in the middle of a possession (possession and timeout state live in memory and end with a restart, as the avatar freeze does); real graphics and Windows.
