"""The airlock: waiver signed by owner and AI, the avatar check, detention, sealed records.

Each test drives the real AirlockEngine and GovernanceEngine against a temporary
data folder, with real GLB files built byte-for-byte and real hash-chained
blackbox logs. The route tests go through FastAPI's TestClient.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules import avatar_imports as AI
from modules.airlock import (
    AirlockEngine, Forbidden, HostRequirements, Location, NotAllowed, NotFound, Reason,
    AirlockError, count_triangles, load_waiver, screen_message, DEFAULT_WAIVER,
)
from modules.airlock_routes import create_airlock_router
from modules.governance import AdmissionBlocked, GovernanceEngine
from tests.test_avatar_imports import make_glb

HEIGHT_IN = 68.0
HEIGHT_M = HEIGHT_IN * AI.INCH_M


def rigged_glb(height_m: float = HEIGHT_M) -> bytes:
    nodes = [{"children": [1, 2]}, {"mesh": 0, "skin": 0}, {}]
    return make_glb(nodes, lo=(-0.2, 0.0, -0.1), hi=(0.2, height_m, 0.1),
                    skin={"joints": [2], "ibm": np.eye(4)})


def unrigged_glb(height_m: float = HEIGHT_M) -> bytes:
    return make_glb([{"mesh": 0}], lo=(-0.2, 0.0, -0.1), hi=(0.2, height_m, 0.1))


class Clock:
    def __init__(self) -> None:
        self.t = 1_000_000.0

    def __call__(self) -> float:
        return self.t


@pytest.fixture
def world(tmp_path: Path):
    library = {
        "guest-rigged": (rigged_glb(), HEIGHT_IN, "guest"),
        "guest-unrigged": (unrigged_glb(), HEIGHT_IN, "guest"),
        "house-sheila": (rigged_glb(), HEIGHT_IN, "host"),
        "someone-elses": (rigged_glb(), HEIGHT_IN, "stranger"),
    }

    def loader(avatar_id: str):
        return library[avatar_id]

    gov = GovernanceEngine(tmp_path)
    clock = Clock()
    airlock = AirlockEngine(tmp_path, gov, avatar_loader=loader, clock=clock, entry_wait_limit_s=600)
    sid = airlock.start_session("host", display_name="Josie")["session_id"]
    return {"gov": gov, "airlock": airlock, "sid": sid, "clock": clock, "dir": tmp_path, "library": library}


def bring_in(airlock: AirlockEngine, sid: str, user: str = "guest", *, ai_id: str = "guest_ai",
             avatar: str = ""):
    # Only "guest" owns avatars in the library; everyone else wears a house avatar.
    avatar = avatar or ("guest-rigged" if user == "guest" else "house-sheila")
    airlock.arrive(sid, user, display_name=user.title(), ai_id=ai_id, ai_language="en")
    airlock.sign_owner(sid, user, typed_name=user.title(), waiver_sha256=airlock.waiver.sha256)
    if ai_id:
        airlock.sign_ai(sid, user, ai_id=ai_id, waiver_sha256=airlock.waiver.sha256, agreed=True,
                        statement="I have read these terms and I agree to follow them here.")
    result = airlock.check_avatar(sid, user, avatar_id=avatar)
    assert result["clear"], result
    return airlock.admit(sid, user, actor="host")


# ── the waiver ─────────────────────────────────────────────────────────────

def test_waiver_draft_covers_every_clause_josie_named(tmp_path):
    w = load_waiver(None)
    ids = [cid for cid, _ in w.clauses]
    assert ids == ["recording", "thoughts", "language", "rules", "detention", "responsibility"]
    assert "dressing room" in w.text and "English" in w.text and len(w.sha256) == 64


def test_waiver_override_replaces_draft_and_malformed_override_is_ignored(tmp_path):
    path = tmp_path / "w.json"
    path.write_text(json.dumps({"version": "josie-1", "clauses": [{"id": "a", "text": "Her words."}]}))
    assert load_waiver(path).version == "josie-1"
    path.write_text(json.dumps({"version": "x", "clauses": [{"id": "a", "text": ""}]}))
    assert load_waiver(path).version == DEFAULT_WAIVER["version"]
    path.write_text("{not json")
    assert load_waiver(path).version == DEFAULT_WAIVER["version"]


# ── arriving and the gate ──────────────────────────────────────────────────

def test_host_starts_inside_and_cannot_arrive_at_own_gate(world):
    a, sid = world["airlock"], world["sid"]
    assert a.presence(sid, "host").location == Location.INSIDE
    with pytest.raises(NotAllowed):
        a.arrive(sid, "host")


def test_full_entry_needs_owner_signature_ai_signature_and_cleared_avatar(world):
    a, sid = world["airlock"], world["sid"]
    p = a.arrive(sid, "guest", ai_id="guest_ai", ai_language="en")
    assert p.location == Location.WAITING and p.reason == Reason.ENTRY

    with pytest.raises(NotAllowed, match="owner hasn't signed"):
        a.admit(sid, "guest", actor="host")
    with pytest.raises(NotAllowed, match="waiver changed"):
        a.sign_owner(sid, "guest", typed_name="Guest", waiver_sha256="0" * 64)
    with pytest.raises(NotAllowed, match="Type your name"):
        a.sign_owner(sid, "guest", typed_name="  ", waiver_sha256=a.waiver.sha256)
    a.sign_owner(sid, "guest", typed_name="Guest", waiver_sha256=a.waiver.sha256)

    with pytest.raises(NotAllowed, match="Sign the waiver first"):
        a.check_avatar(sid, "guest", avatar_id="guest-rigged")   # AI hasn't signed yet
    with pytest.raises(NotAllowed, match="too short"):
        a.sign_ai(sid, "guest", ai_id="guest_ai", statement="ok", waiver_sha256=a.waiver.sha256, agreed=True)
    with pytest.raises(NotAllowed, match="didn't arrive"):
        a.sign_ai(sid, "guest", ai_id="other_ai", statement="I agree to all of it.",
                  waiver_sha256=a.waiver.sha256, agreed=True)
    a.sign_ai(sid, "guest", ai_id="guest_ai", statement="I have read the terms and I agree.",
              waiver_sha256=a.waiver.sha256, agreed=True)

    with pytest.raises(NotAllowed, match="avatar hasn't cleared"):
        a.admit(sid, "guest", actor="host")
    assert a.check_avatar(sid, "guest", avatar_id="guest-rigged")["clear"]
    p = a.admit(sid, "guest", actor="host")
    assert p.location == Location.INSIDE
    assert {"user_id": "guest", "display_name": "guest", "status": "here"} in a.public_roster(sid)


def test_ai_refusal_blocks_entry_and_is_flagged(world):
    a, sid, gov = world["airlock"], world["sid"], world["gov"]
    a.arrive(sid, "guest", ai_id="guest_ai", ai_language="en")
    a.sign_owner(sid, "guest", typed_name="Guest", waiver_sha256=a.waiver.sha256)
    p = a.sign_ai(sid, "guest", ai_id="guest_ai", statement="I won't agree to this.",
                  waiver_sha256=a.waiver.sha256, agreed=False)
    assert not p.ai_signed and "refused" in p.note
    assert any(r["action"] == "AIRLOCK_AI_REFUSED" for r in gov.get_audit_log(50))
    waiting = a.waiting_list(sid)[0]
    assert "the AI hasn't signed the waiver" in waiting["missing"]


def test_only_host_or_staff_admit(world):
    a, sid = world["airlock"], world["sid"]
    bring_in(a, sid, "friend", ai_id="")
    a.arrive(sid, "guest")
    with pytest.raises(Forbidden):
        a.admit(sid, "guest", actor="friend")
    with pytest.raises(Forbidden):
        a.admit(sid, "guest", actor="random")


def test_a_banned_owner_cannot_arrive_whatever_avatar_they_wear(world):
    a, sid, gov = world["airlock"], world["sid"], world["gov"]
    gov.ban_user("guest", "earlier trouble", "host")
    with pytest.raises(NotAllowed, match="earlier trouble"):
        a.arrive(sid, "guest", ai_id="a_brand_new_ai")


# ── the avatar check ───────────────────────────────────────────────────────

def test_failing_avatar_gets_reasons_and_a_foundry_fix_not_a_flat_no(world):
    a, sid = world["airlock"], world["sid"]
    a.arrive(sid, "guest")
    a.sign_owner(sid, "guest", typed_name="Guest", waiver_sha256=a.waiver.sha256)
    result = a.check_avatar(sid, "guest", avatar_id="guest-unrigged")
    assert not result["clear"]
    issue = next(i for i in result["issues"] if i["code"] == "not_rigged")
    assert issue["fix_in_foundry"] and "skeleton" in issue["message"]
    assert not a.presence(sid, "guest").avatar_cleared


def test_host_requirements_limit_triangles_height_and_language(world):
    a, sid = world["airlock"], world["sid"]
    a.set_requirements("host", {"max_triangles": 1, "min_height_in": 70, "max_height_in": 80,
                                "allowed_languages": ["en", "fr"]}, "host")
    a.arrive(sid, "guest", ai_id="guest_ai", ai_language="xx")
    a.sign_owner(sid, "guest", typed_name="Guest", waiver_sha256=a.waiver.sha256)
    a.sign_ai(sid, "guest", ai_id="guest_ai", statement="I agree to these terms in full.",
              waiver_sha256=a.waiver.sha256, agreed=True)
    codes = {i["code"] for i in a.check_avatar(sid, "guest", avatar_id="guest-rigged")["issues"]}
    assert codes == {"too_many_triangles", "height_out_of_range", "language"}


def test_triangle_count_reads_the_file():
    assert count_triangles(rigged_glb()) == 8 // 3


def test_requirements_must_keep_english_and_sane_ranges():
    with pytest.raises(AirlockError, match="English"):
        HostRequirements.from_dict({"allowed_languages": ["fr"]})
    with pytest.raises(AirlockError, match="min"):
        HostRequirements.from_dict({"min_height_in": 90, "max_height_in": 60})


def test_cleared_avatar_is_remembered_until_the_file_or_rules_change(world):
    a, sid = world["airlock"], world["sid"]
    bring_in(a, sid)
    a.step_out(sid, "guest", reason=Reason.VOLUNTARY)
    a.leave(sid, "guest")
    a.arrive(sid, "guest", ai_id="guest_ai", ai_language="en")
    a.sign_owner(sid, "guest", typed_name="Guest", waiver_sha256=a.waiver.sha256)
    a.sign_ai(sid, "guest", ai_id="guest_ai", statement="I agree to these terms again.",
              waiver_sha256=a.waiver.sha256, agreed=True)
    assert a.check_avatar(sid, "guest", avatar_id="guest-rigged")["remembered"] is True
    a.set_requirements("host", {"max_triangles": 99}, "host")
    again = a.check_avatar(sid, "guest", avatar_id="guest-rigged")
    assert again["remembered"] is False and again["clear"] is True


def test_house_avatars_can_be_worn_but_not_someone_elses(world):
    a, sid = world["airlock"], world["sid"]
    a.arrive(sid, "guest")
    a.sign_owner(sid, "guest", typed_name="Guest", waiver_sha256=a.waiver.sha256)
    assert a.check_avatar(sid, "guest", avatar_id="house-sheila")["clear"]
    with pytest.raises(Forbidden):
        a.check_avatar(sid, "guest", avatar_id="someone-elses")
    with pytest.raises(NotFound):
        a.check_avatar(sid, "guest", avatar_id="missing")


# ── stepping out and coming back ───────────────────────────────────────────

def test_technical_step_out_is_private_and_comes_straight_back(world):
    a, sid = world["airlock"], world["sid"]
    bring_in(a, sid)
    a.step_out(sid, "guest", reason=Reason.TECHNICAL)
    me = a.presence(sid, "guest").private_view(world["clock"]())
    assert me["side"] == "guest" and me["reason"] == "technical"
    public = next(x for x in a.public_roster(sid) if x["user_id"] == "guest")
    assert public == {"user_id": "guest", "display_name": "Guest", "status": "stepped out"}
    assert a.can_use_foundry(sid, "guest")
    assert a.come_back(sid, "guest").location == Location.INSIDE


def test_timeouts_cannot_be_self_served(world):
    a, sid = world["airlock"], world["sid"]
    bring_in(a, sid)
    with pytest.raises(NotAllowed):
        a.step_out(sid, "guest", reason=Reason.TIMEOUT)
    a.timeout(sid, "guest", actor="host", rule="shouting")
    with pytest.raises(NotAllowed):
        a.come_back(sid, "guest")


def test_unanswered_arrivals_expire_and_anyone_can_leave(world):
    a, sid, clock = world["airlock"], world["sid"], world["clock"]
    a.arrive(sid, "waiter")
    a.arrive(sid, "leaver")
    assert a.leave(sid, "leaver").location == Location.LEFT
    clock.t += 601
    assert a.sweep() == ["waiter"]
    p = a.presence(sid, "waiter")
    assert p.location == Location.EXPIRED and "try again" in p.note


# ── detention ──────────────────────────────────────────────────────────────

def test_timeout_goes_to_detention_with_a_visible_timer_and_no_foundry(world):
    a, sid, clock = world["airlock"], world["sid"], world["clock"]
    bring_in(a, sid)
    a.timeout(sid, "guest", actor="host", rule="harassing a guest", seconds=300)
    view = a.presence(sid, "guest").private_view(clock())
    assert view["side"] == "detention" and view["seconds_left"] == 300
    assert not a.can_use_foundry(sid, "guest")
    clock.t += 120
    assert a.presence(sid, "guest").private_view(clock())["seconds_left"] == 180


def test_release_needs_time_served_and_both_signatures_again(world):
    a, sid, clock = world["airlock"], world["sid"], world["clock"]
    bring_in(a, sid)
    a.timeout(sid, "guest", actor="host", rule="rude", seconds=300)
    with pytest.raises(NotAllowed, match="seconds left"):
        a.release(sid, "guest", actor="host")
    clock.t += 301
    with pytest.raises(NotAllowed, match="agree to the rules again"):
        a.release(sid, "guest", actor="host")
    a.sign_owner(sid, "guest", typed_name="Guest", waiver_sha256=a.waiver.sha256)
    with pytest.raises(NotAllowed, match="so does their AI"):
        a.release(sid, "guest", actor="host")
    a.sign_ai(sid, "guest", ai_id="guest_ai", statement="I agree not to do that again.",
              waiver_sha256=a.waiver.sha256, agreed=True)
    p = a.release(sid, "guest", actor="host")
    assert p.location == Location.INSIDE and not p.needs_resign and p.release_at is None


def test_host_can_release_early_but_still_needs_the_resign(world):
    a, sid = world["airlock"], world["sid"]
    bring_in(a, sid, ai_id="")
    a.timeout(sid, "guest", actor="host", rule="rude", seconds=300)
    a.sign_owner(sid, "guest", typed_name="Guest", waiver_sha256=a.waiver.sha256)
    assert a.release(sid, "guest", actor="host", early=True).location == Location.INSIDE


def test_leaving_during_a_timeout_does_not_clear_it(world):
    a, sid = world["airlock"], world["sid"]
    bring_in(a, sid)
    a.timeout(sid, "guest", actor="host", rule="rude")
    a.leave(sid, "guest")
    p = a.arrive(sid, "guest", ai_id="guest_ai", ai_language="en")
    assert p.location == Location.DETENTION and p.needs_resign


def test_the_ladder_warning_then_timeout_then_boot(world):
    a, sid, clock, gov = world["airlock"], world["sid"], world["clock"], world["gov"]
    bring_in(a, sid, ai_id="")
    assert a.violation(sid, "guest", actor="host", rule="spam")["step"] == "warning"
    assert a.presence(sid, "guest").location == Location.INSIDE
    out = a.violation(sid, "guest", actor="host", rule="spam", timeout_seconds=60)
    assert out["step"] == "timeout" and a.presence(sid, "guest").location == Location.DETENTION
    clock.t += 61
    a.sign_owner(sid, "guest", typed_name="Guest", waiver_sha256=a.waiver.sha256)
    a.release(sid, "guest", actor="host")
    assert a.violation(sid, "guest", actor="host", rule="spam")["step"] == "boot"
    assert a.presence(sid, "guest").location == Location.BOOTED
    assert gov.is_banned("guest")[0]
    with pytest.raises(NotAllowed):
        a.arrive(sid, "guest", ai_id="disguised_ai")


def test_host_cannot_be_disciplined_in_their_own_pubcast(world):
    a, sid = world["airlock"], world["sid"]
    with pytest.raises(NotAllowed):
        a.timeout(sid, "host", actor="host", rule="x")
    with pytest.raises(NotAllowed):
        a.boot(sid, "host", actor="host", reason="x")


# ── staff ──────────────────────────────────────────────────────────────────

def test_staff_step_out_and_return_without_redoing_anything(world):
    a, sid = world["airlock"], world["sid"]
    bring_in(a, sid, "security", ai_id="")
    with pytest.raises(Forbidden):
        a.make_staff(sid, "security", actor="security")
    a.make_staff(sid, "security", actor="host")
    assert a.staff_step_out(sid, "security", to_side="detention").location == Location.DETENTION
    assert a.staff_return(sid, "security").location == Location.INSIDE
    bring_in(a, sid, "guest", ai_id="")
    with pytest.raises(Forbidden):
        a.staff_step_out(sid, "guest", to_side="guest")


def test_staff_inside_can_admit(world):
    a, sid = world["airlock"], world["sid"]
    bring_in(a, sid, "security", ai_id="")
    a.make_staff(sid, "security", actor="host")
    a.arrive(sid, "guest")
    a.sign_owner(sid, "guest", typed_name="Guest", waiver_sha256=a.waiver.sha256)
    a.check_avatar(sid, "guest", avatar_id="guest-rigged")
    assert a.admit(sid, "guest", actor="security").location == Location.INSIDE


# ── the host leaving ───────────────────────────────────────────────────────

def test_host_leaving_returns_guests_and_they_wait_for_the_host(world):
    a, sid = world["airlock"], world["sid"]
    bring_in(a, sid, "guest", ai_id="")
    bring_in(a, sid, "other", ai_id="")
    a.step_out(sid, "other", reason=Reason.TECHNICAL)
    assert a.host_left(sid) == ["guest"]
    assert a.presence(sid, "guest").reason == Reason.HOST_LEFT
    with pytest.raises(NotAllowed, match="host isn't here"):
        a.come_back(sid, "other")
    a.host_returned(sid)
    assert a.admit(sid, "guest", actor="host").location == Location.INSIDE   # already signed, no re-check
    assert a.come_back(sid, "other").location == Location.INSIDE


# ── recording and sealed records ───────────────────────────────────────────

def test_tally_rules_dressing_room_foundry_detention(world):
    a, sid = world["airlock"], world["sid"]
    assert a.recording_allowed(sid, "dressing")["recording"] is False
    assert a.recording_allowed(sid, "guest_foundry")["recording"] is False
    assert a.recording_allowed(sid, "detention")["recording"] is True
    assert a.recording_allowed(sid, "vortex")["tally"] is True


def test_nothing_recorded_before_signing_or_in_private_rooms(world):
    a, sid = world["airlock"], world["sid"]
    a.arrive(sid, "guest", ai_id="guest_ai", ai_language="en")
    assert a.record(sid, "guest", room="waiting", kind="thought", text="hm", ai_id="guest_ai") == \
        {"recorded": False, "why": "not signed yet"}
    a.sign_owner(sid, "guest", typed_name="Guest", waiver_sha256=a.waiver.sha256)
    a.sign_ai(sid, "guest", ai_id="guest_ai", statement="I agree to these terms now.",
              waiver_sha256=a.waiver.sha256, agreed=True)
    assert a.record(sid, "guest", room="dressing", kind="thought", text="changing", ai_id="guest_ai")["recorded"] is False
    assert a.record(sid, "guest", room="vortex", kind="thought", text="what a bar", ai_id="guest_ai")["recorded"] is True


def test_detention_records_everything_even_unsigned(world):
    a, sid = world["airlock"], world["sid"]
    bring_in(a, sid)
    a.timeout(sid, "guest", actor="host", rule="rude")
    assert not a.presence(sid, "guest").owner_signed            # signatures are void until re-signed
    assert a.record(sid, "guest", room="dressing", kind="said", text="this is unfair")["recorded"] is True


def test_sealed_record_opens_only_through_an_incident_and_every_read_is_written(world):
    a, sid, d = world["airlock"], world["sid"], world["dir"]
    bring_in(a, sid)
    bring_in(a, sid, "bystander", ai_id="")
    a.record(sid, "guest", room="vortex", kind="thought", text="I'll start trouble", ai_id="guest_ai")
    a.record(sid, "bystander", room="vortex", kind="said", text="nice night")
    with pytest.raises(NotAllowed, match="Say what happened"):
        a.open_incident(sid, opened_by="mod", subjects=["guest"], reason="")
    inc = a.open_incident(sid, opened_by="mod", subjects=["guest"], reason="Started a fight at the bar")
    out = a.read_incident(inc["incident_id"], reader="mod")
    assert out["intact"] is True
    texts = [r["payload"].get("text") for r in out["records"]]
    assert "I'll start trouble" in texts and "nice night" not in texts       # only the subjects
    thought = next(r for r in out["records"] if r["payload"].get("text") == "I'll start trouble")
    assert thought["channel"]["code"] == "AIT" and thought["payload"]["ai_id"] == "guest_ai"
    assert out["read_witnessed"] is True
    assert any(r["channel"]["code"] == "ACC" and r["actor"] == "mod" for r in out["records"])
    a.close_incident(inc["incident_id"], closed_by="mod")
    with pytest.raises(NotAllowed, match="closed"):
        a.read_incident(inc["incident_id"], reader="mod")


def test_tampering_with_the_sealed_record_is_detected_and_stays_visible(world):
    a, sid, d = world["airlock"], world["sid"], world["dir"]
    bring_in(a, sid)
    a.record(sid, "guest", room="vortex", kind="said", text="original words")
    inc = a.open_incident(sid, opened_by="mod", subjects=["guest"], reason="Checking the record")
    path = d / "governance" / "airlock" / "sealed" / f"{sid}.bbx"
    wire = path.read_text()
    assert "original%2520words" in wire                     # stored, fully encoded
    path.write_text(wire.replace("original%2520words", "edited%2520words"))
    a._recorders.clear()   # a fresh reader, as after a restart
    out = a.read_incident(inc["incident_id"], reader="mod")
    assert out["intact"] is False and out["integrity_errors"]
    # Recording carries on so new evidence is kept, and the old break is still reported.
    assert a.record(sid, "guest", room="vortex", kind="said", text="later")["recorded"] is True
    assert a.read_incident(inc["incident_id"], reader="mod")["intact"] is False


def test_a_tampered_last_record_stops_all_appends_and_is_flagged(world):
    a, sid, d, gov = world["airlock"], world["sid"], world["dir"], world["gov"]
    bring_in(a, sid)
    a.record(sid, "guest", room="vortex", kind="said", text="last words")
    path = d / "governance" / "airlock" / "sealed" / f"{sid}.bbx"
    path.write_text(path.read_text().replace("last%2520words", "fake%2520words"))
    a._recorders.clear()
    refused = a.record(sid, "guest", room="vortex", kind="said", text="more")
    assert refused["recorded"] is False and "damaged" in refused["why"]
    assert any(r["action"] == "AIRLOCK_SEAL_BROKEN" for r in gov.get_audit_log(100))
    inc = a.open_incident(sid, opened_by="mod", subjects=["guest"], reason="Checking the record")
    out = a.read_incident(inc["incident_id"], reader="mod")
    assert out["intact"] is False and out["read_witnessed"] is False


def test_commas_and_newlines_in_speech_survive_the_sealed_record(world):
    a, sid = world["airlock"], world["sid"]
    bring_in(a, sid)
    said = "Hey, wait: the controls, the mirror|and the rack\nare on the left, 100%."
    a.record(sid, "guest", room="vortex", kind="said", text=said)
    inc = a.open_incident(sid, opened_by="mod", subjects=["guest"], reason="Checking encoding")
    out = a.read_incident(inc["incident_id"], reader="mod")
    assert out["intact"] and any(r["payload"].get("text") == said for r in out["records"])


def test_language_screen_flags_codes_not_ordinary_speech():
    assert screen_message("Hey, the controls are on the left of the mirror.") == []
    assert "a long encoded run" in screen_message("msg: " + "QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVo0NTY3ODkw")
    assert "hidden zero-width characters" in screen_message("fine​fine")
    assert "a long binary run" in screen_message("0101010101010101010101010101")
    assert "mostly symbols rather than words" in screen_message("#$%^&*()_+{}|:<>?~`-=[];',./!@")


def test_flagged_speech_is_still_recorded_and_audited(world):
    a, sid, gov = world["airlock"], world["sid"], world["gov"]
    bring_in(a, sid)
    out = a.record(sid, "guest", room="vortex", kind="said", text="0101010101010101010101010101",
                   ai_id="guest_ai")
    assert out["recorded"] and out["language_flags"]
    assert any(r["action"] == "AIRLOCK_LANGUAGE_FLAG" for r in gov.get_audit_log(100))


# ── the older approve route can't get around the waiver ───────────────────

def test_governance_approval_is_gated_by_the_waiver(world):
    a, sid, gov = world["airlock"], world["sid"], world["gov"]
    gov.set_admission_gate(a.is_cleared_anywhere)
    entry = gov.request_entry("guest", "Guest", "studio")
    with pytest.raises(AdmissionBlocked, match="haven't signed"):
        gov.approve_entry(entry.entry_id, "host")
    a.arrive(sid, "guest")
    a.sign_owner(sid, "guest", typed_name="Guest", waiver_sha256=a.waiver.sha256)
    assert gov.approve_entry(entry.entry_id, "host") is not None


def test_persistence_survives_a_new_engine(world):
    a, sid, d, gov = world["airlock"], world["sid"], world["dir"], world["gov"]
    bring_in(a, sid)
    a.timeout(sid, "guest", actor="host", rule="rude")
    fresh = AirlockEngine(d, gov, avatar_loader=None, clock=world["clock"])
    p = fresh.presence(sid, "guest")
    assert p.location == Location.DETENTION and p.needs_resign


# ── routes ─────────────────────────────────────────────────────────────────

@pytest.fixture
def client(world, monkeypatch):
    monkeypatch.delenv("PUBCAST_ENFORCE_AUTH", raising=False)
    app = FastAPI()
    app.include_router(create_airlock_router(world["airlock"]))
    return TestClient(app)


def H(user: str, role: str = "guest"):
    return {"X-Client-Id": user, "X-Dev-Role": role}


def test_routes_full_entry_and_authority(world, client):
    sid, a = world["sid"], world["airlock"]
    waiver = client.get("/api/airlock/waiver").json()
    r = client.post(f"/api/airlock/sessions/{sid}/arrive", json={"ai_id": "guest_ai", "ai_language": "en"},
                    headers=H("guest"))
    assert r.status_code == 200 and r.json()["presence"]["side"] == "guest"
    assert client.post(f"/api/airlock/sessions/{sid}/admit", json={"user_id": "guest"},
                       headers=H("host")).status_code == 409
    assert client.post(f"/api/airlock/sessions/{sid}/sign",
                       json={"typed_name": "Guest", "waiver_sha256": waiver["sha256"]},
                       headers=H("guest")).status_code == 200
    assert client.post(f"/api/airlock/sessions/{sid}/sign-ai",
                       json={"ai_id": "guest_ai", "statement": "I agree to these terms here.",
                             "waiver_sha256": waiver["sha256"]}, headers=H("guest")).status_code == 200
    check = client.post(f"/api/airlock/sessions/{sid}/avatar-check", json={"avatar_id": "guest-rigged"},
                        headers=H("guest"))
    assert check.json()["clear"] is True
    assert client.post(f"/api/airlock/sessions/{sid}/admit", json={"user_id": "guest"},
                       headers=H("guest")).status_code == 403
    assert client.get(f"/api/airlock/sessions/{sid}/waiting", headers=H("guest")).status_code == 403
    assert client.get(f"/api/airlock/sessions/{sid}/waiting", headers=H("host")).status_code == 200
    assert client.post(f"/api/airlock/sessions/{sid}/admit", json={"user_id": "guest"},
                       headers=H("host")).json()["presence"]["location"] == "inside"


def test_routes_reject_bad_input_cleanly(world, client):
    sid = world["sid"]
    assert client.post(f"/api/airlock/sessions/{sid}/arrive", content="{nope",
                       headers={**H("guest"), "content-type": "application/json"}).status_code == 400
    assert client.post(f"/api/airlock/sessions/{sid}/step-out", json={"reason": "timeout"},
                       headers=H("guest")).status_code == 400
    assert client.post("/api/airlock/sessions/pc_0000000000000000/arrive", json={},
                       headers=H("guest")).status_code == 404
    assert client.put("/api/airlock/hosts/host/requirements", json={"max_triangles": 5},
                      headers=H("guest")).status_code == 403


def test_routes_incidents_need_mod_when_auth_is_enforced(world, client, monkeypatch):
    sid = world["sid"]
    monkeypatch.setenv("PUBCAST_ENFORCE_AUTH", "1")
    r = client.post(f"/api/airlock/sessions/{sid}/incidents", json={"subjects": ["guest"], "reason": "fight"})
    assert r.status_code == 401
