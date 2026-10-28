"""
modules/airlock_routes.py — REST surface for the airlock
════════════════════════════════════════════════════════
Rear View Foresight LLC — Feic Mo Chroí — 2026-10-28

Every action is taken as the authenticated caller (route_security). Nobody can
sign, step out, or leave on someone else's behalf. Host and staff actions are
checked against the session's host inside AirlockEngine, and moderators (mod
role or above) may act in any session. Sealed records are reachable only
through an incident, and only by moderators.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request

from modules.airlock import (
    AirlockEngine, AirlockError, Forbidden, NotAllowed, NotFound, Reason, screen_message,
)
from modules.auth import role_gte
from modules.route_security import current_identity, require_role


async def _body(request: Request) -> Dict[str, Any]:
    raw = await request.body()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(400, f"Malformed JSON body: {exc.msg}")
    if not isinstance(data, dict):
        raise HTTPException(400, "JSON body must be an object")
    return data


def _str(body: Dict[str, Any], key: str, *, required: bool = False, max_length: int = 256) -> str:
    value = body.get(key, "")
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise HTTPException(400, f"{key} must be a string")
    value = value.strip()
    if required and not value:
        raise HTTPException(400, f"{key} required")
    if len(value) > max_length:
        raise HTTPException(400, f"{key} must be <= {max_length} characters")
    return value


def _bool(body: Dict[str, Any], key: str, default: bool) -> bool:
    value = body.get(key, default)
    if not isinstance(value, bool):
        raise HTTPException(400, f"{key} must be true or false")
    return value


def _seconds(body: Dict[str, Any], key: str, default: float) -> float:
    value = body.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise HTTPException(400, f"{key} must be a number of seconds")
    return float(value)


def _me(identity: Dict[str, Any]) -> str:
    return str(identity.get("user_id") or "anon")


def _is_mod(identity: Dict[str, Any]) -> bool:
    return role_gte(str(identity.get("role") or "guest"), "mod")


def _run(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except NotFound as exc:
        raise HTTPException(404, str(exc))
    except Forbidden as exc:
        raise HTTPException(403, str(exc))
    except NotAllowed as exc:
        raise HTTPException(409, str(exc))
    except AirlockError as exc:
        raise HTTPException(400, str(exc))


def create_airlock_router(airlock: AirlockEngine, hub: Any = None) -> APIRouter:
    router = APIRouter(prefix="/api/airlock", tags=["Airlock"])

    async def _tell(event_type: str, payload: Dict[str, Any]) -> None:
        if hub is not None:
            try:
                await hub.broadcast_system_event({"type": event_type, "payload": payload})
            except Exception:
                pass  # a missed live notice is not a failed action; state is already saved

    def _mine(p) -> Dict[str, Any]:
        return p.private_view(airlock._now())

    # ── the waiver and host requirements (readable before you present anything) ──

    @router.get("/waiver")
    async def get_waiver():
        return airlock.waiver.to_dict()

    @router.get("/hosts/{host_id}/requirements")
    async def get_requirements(host_id: str):
        return _run(airlock.requirements, host_id).to_dict()

    @router.put("/hosts/{host_id}/requirements")
    async def put_requirements(host_id: str, request: Request,
                               identity: Dict[str, Any] = Depends(current_identity)):
        if _me(identity) != host_id and not _is_mod(identity):
            raise HTTPException(403, "Only that host sets their requirements.")
        req = _run(airlock.set_requirements, host_id, await _body(request), _me(identity))
        return req.to_dict()

    # ── sessions ──

    @router.post("/sessions")
    async def start_session(request: Request, identity: Dict[str, Any] = Depends(current_identity)):
        body = await _body(request)
        return _run(airlock.start_session, _me(identity),
                    display_name=_str(body, "display_name", max_length=128),
                    start_room=_str(body, "start_room", max_length=64) or "studio")

    @router.post("/sessions/{session_id}/end")
    async def end_session(session_id: str, identity: Dict[str, Any] = Depends(current_identity)):
        _run(airlock.end_session, session_id, _me(identity))
        await _tell("airlock_session_ended", {"session_id": session_id})
        return {"ok": True}

    @router.post("/sessions/{session_id}/host-left")
    async def host_left(session_id: str, identity: Dict[str, Any] = Depends(current_identity)):
        if _me(identity) != _run(airlock.host_id, session_id) and not _is_mod(identity):
            raise HTTPException(403, "Only the host or a moderator reports the host leaving.")
        moved = _run(airlock.host_left, session_id)
        await _tell("airlock_host_left", {"session_id": session_id})
        return {"ok": True, "returned_to_waiting_room": moved}

    @router.post("/sessions/{session_id}/host-returned")
    async def host_returned(session_id: str, identity: Dict[str, Any] = Depends(current_identity)):
        if _me(identity) != _run(airlock.host_id, session_id) and not _is_mod(identity):
            raise HTTPException(403, "Only the host returns as host.")
        _run(airlock.host_returned, session_id)
        return {"ok": True}

    # ── arriving, signing, the avatar check ──

    @router.post("/sessions/{session_id}/arrive")
    async def arrive(session_id: str, request: Request, identity: Dict[str, Any] = Depends(current_identity)):
        airlock.sweep()  # expire unanswered arrivals before anyone looks
        body = await _body(request)
        p = _run(airlock.arrive, session_id, _me(identity),
                 display_name=_str(body, "display_name", max_length=128),
                 ai_id=_str(body, "ai_id", max_length=128),
                 ai_language=_str(body, "ai_language", max_length=8))
        await _tell("airlock_arrival", {"session_id": session_id, "user_id": p.user_id,
                                        "display_name": p.display_name})
        return {"presence": _mine(p), "waiver": airlock.waiver.to_dict(),
                "requirements": airlock.requirements(airlock.host_id(session_id)).to_dict()}

    @router.post("/sessions/{session_id}/sign")
    async def sign(session_id: str, request: Request, identity: Dict[str, Any] = Depends(current_identity)):
        body = await _body(request)
        p = _run(airlock.sign_owner, session_id, _me(identity),
                 typed_name=_str(body, "typed_name", max_length=200),
                 waiver_sha256=_str(body, "waiver_sha256", required=True, max_length=64),
                 agreed=_bool(body, "agreed", True))
        return {"presence": _mine(p)}

    @router.post("/sessions/{session_id}/sign-ai")
    async def sign_ai(session_id: str, request: Request, identity: Dict[str, Any] = Depends(current_identity)):
        """The owner's client relays its AI's own answer. The owner can't sign for it."""
        body = await _body(request)
        p = _run(airlock.sign_ai, session_id, _me(identity),
                 ai_id=_str(body, "ai_id", required=True, max_length=128),
                 statement=_str(body, "statement", max_length=4000),
                 waiver_sha256=_str(body, "waiver_sha256", required=True, max_length=64),
                 agreed=_bool(body, "agreed", True))
        if not p.ai_signed:
            await _tell("airlock_ai_refused", {"session_id": session_id, "user_id": p.user_id, "ai_id": p.ai_id})
        return {"presence": _mine(p)}

    @router.post("/sessions/{session_id}/avatar-check")
    async def avatar_check(session_id: str, request: Request, identity: Dict[str, Any] = Depends(current_identity)):
        body = await _body(request)
        return _run(airlock.check_avatar, session_id, _me(identity),
                    avatar_id=_str(body, "avatar_id", required=True, max_length=80))

    @router.get("/sessions/{session_id}/foundry-access")
    async def foundry_access(session_id: str, identity: Dict[str, Any] = Depends(current_identity)):
        return {"allowed": airlock.can_use_foundry(session_id, _me(identity))}

    # ── in and out ──

    @router.post("/sessions/{session_id}/admit")
    async def admit(session_id: str, request: Request, identity: Dict[str, Any] = Depends(current_identity)):
        body = await _body(request)
        user_id = _str(body, "user_id", required=True, max_length=128)
        p = _run(airlock.admit, session_id, user_id, actor=_me(identity), actor_is_mod=_is_mod(identity))
        await _tell("airlock_admitted", {"session_id": session_id, "user_id": user_id})
        return {"presence": _mine(p)}

    @router.post("/sessions/{session_id}/step-out")
    async def step_out(session_id: str, request: Request, identity: Dict[str, Any] = Depends(current_identity)):
        body = await _body(request)
        raw = _str(body, "reason", max_length=32) or "voluntary"
        if raw not in (Reason.TECHNICAL.value, Reason.VOLUNTARY.value):
            raise HTTPException(400, "reason must be technical or voluntary")
        reason = Reason(raw)
        p = _run(airlock.step_out, session_id, _me(identity), reason=reason)
        await _tell("airlock_stepped_out", {"session_id": session_id, "user_id": p.user_id})
        return {"presence": _mine(p)}

    @router.post("/sessions/{session_id}/come-back")
    async def come_back(session_id: str, identity: Dict[str, Any] = Depends(current_identity)):
        return {"presence": _mine(_run(airlock.come_back, session_id, _me(identity)))}

    @router.post("/sessions/{session_id}/leave")
    async def leave(session_id: str, identity: Dict[str, Any] = Depends(current_identity)):
        return {"presence": _mine(_run(airlock.leave, session_id, _me(identity)))}

    # ── staff ──

    @router.post("/sessions/{session_id}/staff")
    async def make_staff(session_id: str, request: Request, identity: Dict[str, Any] = Depends(current_identity)):
        body = await _body(request)
        p = _run(airlock.make_staff, session_id, _str(body, "user_id", required=True, max_length=128),
                 actor=_me(identity))
        return {"presence": _mine(p)}

    @router.post("/sessions/{session_id}/staff/step-out")
    async def staff_out(session_id: str, request: Request, identity: Dict[str, Any] = Depends(current_identity)):
        body = await _body(request)
        p = _run(airlock.staff_step_out, session_id, _me(identity),
                 to_side=_str(body, "side", required=True, max_length=16))
        return {"presence": _mine(p)}

    @router.post("/sessions/{session_id}/staff/return")
    async def staff_return(session_id: str, identity: Dict[str, Any] = Depends(current_identity)):
        return {"presence": _mine(_run(airlock.staff_return, session_id, _me(identity)))}

    # ── discipline ──

    @router.post("/sessions/{session_id}/violation")
    async def violation(session_id: str, request: Request, identity: Dict[str, Any] = Depends(current_identity)):
        body = await _body(request)
        out = _run(airlock.violation, session_id, _str(body, "user_id", required=True, max_length=128),
                   actor=_me(identity), rule=_str(body, "rule", required=True, max_length=300),
                   timeout_seconds=_seconds(body, "timeout_seconds", 300), actor_is_mod=_is_mod(identity))
        await _tell("airlock_violation", {"session_id": session_id, "step": out["step"]})
        return out

    @router.post("/sessions/{session_id}/timeout")
    async def timeout(session_id: str, request: Request, identity: Dict[str, Any] = Depends(current_identity)):
        body = await _body(request)
        p = _run(airlock.timeout, session_id, _str(body, "user_id", required=True, max_length=128),
                 actor=_me(identity), rule=_str(body, "rule", required=True, max_length=300),
                 seconds=_seconds(body, "seconds", 300), actor_is_mod=_is_mod(identity))
        return {"presence": _mine(p)}

    @router.post("/sessions/{session_id}/release")
    async def release(session_id: str, request: Request, identity: Dict[str, Any] = Depends(current_identity)):
        body = await _body(request)
        p = _run(airlock.release, session_id, _str(body, "user_id", required=True, max_length=128),
                 actor=_me(identity), early=_bool(body, "early", False), actor_is_mod=_is_mod(identity))
        return {"presence": _mine(p)}

    @router.post("/sessions/{session_id}/boot")
    async def boot(session_id: str, request: Request, identity: Dict[str, Any] = Depends(current_identity)):
        body = await _body(request)
        user_id = _str(body, "user_id", required=True, max_length=128)
        p = _run(airlock.boot, session_id, user_id, actor=_me(identity),
                 reason=_str(body, "reason", required=True, max_length=300), actor_is_mod=_is_mod(identity))
        await _tell("airlock_booted", {"session_id": session_id, "user_id": user_id})
        return {"presence": _mine(p)}

    # ── views ──

    @router.get("/sessions/{session_id}/me")
    async def me(session_id: str, identity: Dict[str, Any] = Depends(current_identity)):
        airlock.sweep()  # expire unanswered arrivals before anyone looks
        return {"presence": _mine(_run(airlock.presence, session_id, _me(identity)))}

    @router.get("/sessions/{session_id}/waiting")
    async def waiting(session_id: str, identity: Dict[str, Any] = Depends(current_identity)):
        if _me(identity) != _run(airlock.host_id, session_id) and not _is_mod(identity):
            p = None
            try:
                p = airlock.presence(session_id, _me(identity))
            except AirlockError:
                pass
            if not (p and p.is_staff):
                raise HTTPException(403, "Only the host or staff see the waiting room list.")
        airlock.sweep()  # expire unanswered arrivals before anyone looks
        return {"waiting": _run(airlock.waiting_list, session_id)}

    @router.get("/sessions/{session_id}/roster")
    async def roster(session_id: str):
        return {"people": _run(airlock.public_roster, session_id)}

    @router.get("/sessions/{session_id}/tally/{room}")
    async def tally(session_id: str, room: str):
        return _run(airlock.recording_allowed, session_id, room)

    # ── sealed records ──

    @router.post("/sessions/{session_id}/record")
    async def record(session_id: str, request: Request, identity: Dict[str, Any] = Depends(current_identity)):
        body = await _body(request)
        kind = _str(body, "kind", required=True, max_length=16)
        return _run(airlock.record, session_id, _me(identity),
                    room=_str(body, "room", max_length=64), kind=kind,
                    text=_str(body, "text", required=True, max_length=20000),
                    ai_id=_str(body, "ai_id", max_length=128))

    @router.post("/screen")
    async def screen(request: Request):
        body = await _body(request)
        flags = screen_message(_str(body, "text", required=True, max_length=20000))
        return {"flags": flags, "looks_like_language": not flags}

    @router.post("/sessions/{session_id}/incidents")
    async def open_incident(session_id: str, request: Request,
                            identity: Dict[str, Any] = Depends(require_role("mod"))):
        body = await _body(request)
        subjects = body.get("subjects")
        if not isinstance(subjects, list) or not all(isinstance(s, str) for s in subjects):
            raise HTTPException(400, "subjects must be a list of user ids")
        return _run(airlock.open_incident, session_id, opened_by=_me(identity), subjects=subjects,
                    reason=_str(body, "reason", required=True, max_length=2000))

    @router.get("/incidents/{incident_id}")
    async def read_incident(incident_id: str, identity: Dict[str, Any] = Depends(require_role("mod"))):
        return _run(airlock.read_incident, incident_id, reader=_me(identity))

    @router.post("/incidents/{incident_id}/close")
    async def close_incident(incident_id: str, identity: Dict[str, Any] = Depends(require_role("mod"))):
        _run(airlock.close_incident, incident_id, closed_by=_me(identity))
        return {"ok": True}

    return router


__all__ = ["create_airlock_router"]
