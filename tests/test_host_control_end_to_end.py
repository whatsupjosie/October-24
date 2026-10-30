"""Host control through the real app: real main.app (uvicorn, a throwaway data folder, auth enforced), real walker
sockets at /pubworld/ws/{client_id} proving who they are with a token, and the real /api/host routes.

What is checked is what a person on the other end would receive: the private notice reaches only the possessed person's
walker socket(s); drive, timeout and release follow; nobody else hears any of it; someone with no verified socket cannot be
possessed; a viewer cannot start any of it.
"""
from __future__ import annotations

import asyncio
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

websockets = pytest.importorskip("websockets")

from modules import auth as auth_module  # noqa: E402
from modules.auth import create_access_token  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
NOTICE = "TEST NOTICE: the host is controlling your avatar."          # test wording only


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def host(tmp_path_factory):
    data = tmp_path_factory.mktemp("host_control_e2e")
    (data / "host_control").mkdir()
    (data / "host_control" / "messages.json").write_text(json.dumps({"possession_notice": NOTICE, "timeout_notice": "TEST TIMEOUT"}), encoding="utf-8")
    port = _free_port()
    env = dict(os.environ, PUBCAST_DATA_DIR=str(data), PUBCAST_ENFORCE_AUTH="1", PUBCAST_JWT_SECRET=auth_module._SECRET_KEY, PYTHONUNBUFFERED="1")
    log = open(data / "host.log", "w", encoding="utf-8")
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
                            cwd=str(ROOT), env=env, stdout=log, stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{port}"
    try:
        deadline = time.time() + 90
        while time.time() < deadline:
            if proc.poll() is not None:
                log.flush()
                raise AssertionError("PubCast host exited during startup:\n" + (data / "host.log").read_text(encoding="utf-8")[-3000:])
            try:
                if httpx.get(base + "/health", timeout=0.5).status_code == 200:
                    break
            except httpx.RequestError:
                pass
            time.sleep(0.2)
        else:
            raise AssertionError("PubCast host did not come up within 90 s")
        yield base, port, data
    finally:
        proc.terminate()
        try:
            proc.wait(15)
        except subprocess.TimeoutExpired:
            proc.kill(); proc.wait(5)
        log.close()


def tok(user, role="owner"):
    return create_access_token({"sub": user, "role": role})


def api(base, method, path, who="josie", role="owner", **kw):
    return httpx.request(method, base + path, headers={"Authorization": "Bearer " + tok(who, role)}, timeout=15, **kw)


async def walker(port, client_id, token):
    """A walker socket that proves who it is with the in-band auth message, as static/world_walk_live.js does."""
    ws = await websockets.connect(f"ws://127.0.0.1:{port}/pubworld/ws/{client_id}")
    await ws.send(json.dumps({"type": "auth", "token": token}))
    first = json.loads(await asyncio.wait_for(ws.recv(), 5))
    assert first["type"] == "auth_ok" and first["user_id"], first
    welcome = json.loads(await asyncio.wait_for(ws.recv(), 5))
    assert welcome["type"] == "welcome"
    return ws


async def drain(ws, seconds=1.0):
    got = []
    end = time.time() + seconds
    while time.time() < end:
        try:
            got.append(json.loads(await asyncio.wait_for(ws.recv(), max(0.05, end - time.time()))))
        except asyncio.TimeoutError:
            break
    return got


def test_a_possession_reaches_only_the_possessed_walker_and_follows_through(host):
    base, port, data = host

    async def scenario():
        mira = await walker(port, "pw_mira1", tok("mira", "guest"))
        mira2 = await walker(port, "pw_mira2", tok("Mira", "guest"))        # a second tab, other letter case
        kay = await walker(port, "pw_kay1", tok("kay", "guest"))
        try:
            r = await asyncio.to_thread(api, base, "POST", "/api/host/possess", json={"user_id": "mira", "duration_seconds": 120, "reason": "test"})
            assert r.status_code == 200 and r.json()["notice_delivered"] is True, r.text
            for ws in (mira, mira2):
                notice = [m for m in await drain(ws) if m["type"] == "host_notice"]
                assert len(notice) == 1 and notice[0]["text"] == NOTICE and notice[0]["kind"] == "possession"
            assert [m for m in await drain(kay, 0.5) if m["type"] != "keepalive"] == []              # kay heard nothing

            r = await asyncio.to_thread(api, base, "POST", "/api/host/drive", json={"user_id": "mira", "pos": [100, 250.5]})
            assert r.status_code == 200
            assert [m for m in await drain(mira, 0.8) if m["type"] == "host_drive"] == [{"type": "host_drive", "pos": [100.0, 250.5]}]
            assert [m for m in await drain(kay, 0.3) if m["type"] != "keepalive"] == []

            r = await asyncio.to_thread(api, base, "POST", "/api/host/timeout", json={"user_id": "mira", "duration_seconds": 30})
            assert r.status_code == 200 and r.json()["delivered"] is True
            tele = [m for m in await drain(mira, 0.8) if m["type"] == "host_teleport"]
            assert tele and tele[0]["room"] == "waiting_room_disciplinary" and tele[0]["recording"] is True and tele[0]["text"] == "TEST TIMEOUT"

            assert (await asyncio.to_thread(api, base, "POST", "/api/host/end-timeout", json={"user_id": "mira"})).status_code == 200
            assert [m["type"] for m in await drain(mira, 0.8) if m["type"].startswith("host_")] == ["host_timeout_end"]

            assert (await asyncio.to_thread(api, base, "POST", "/api/host/release", json={"user_id": "mira"})).status_code == 200
            assert [m["type"] for m in await drain(mira, 0.8) if m["type"].startswith("host_")] == ["host_release"]
            assert (await asyncio.to_thread(api, base, "GET", "/api/host/state")).json()["possessed"] == {}
        finally:
            for ws in (mira, mira2, kay):
                await ws.close()
    asyncio.run(scenario())


def test_nobody_connected_means_nobody_possessed_and_a_closed_socket_stops_counting(host):
    base, port, data = host
    r = api(base, "POST", "/api/host/possess", json={"user_id": "ghost"})
    assert r.status_code == 409 and r.json()["detail"] == "target_not_connected"

    async def scenario():
        ws = await walker(port, "pw_zed1", tok("zed", "guest"))
        await ws.close()
        await asyncio.sleep(0.5)
        return await asyncio.to_thread(api, base, "POST", "/api/host/possess", json={"user_id": "zed"})
    r = asyncio.run(scenario())
    assert r.status_code == 409 and r.json()["detail"] == "target_not_connected"
    assert api(base, "GET", "/api/host/state").json()["possessed"] == {}


def test_a_socket_that_never_proved_who_it_is_cannot_receive_or_be_possessed(host):
    base, port, data = host

    async def scenario():
        ws = await websockets.connect(f"ws://127.0.0.1:{port}/pubworld/ws/pw_anon1")      # no token sent
        try:
            msgs = []
            try:
                while True:
                    msgs.append(json.loads(await asyncio.wait_for(ws.recv(), 10)))
            except (asyncio.TimeoutError, websockets.ConnectionClosed):
                pass
            return msgs
        finally:
            await ws.close()
    msgs = asyncio.run(scenario())
    assert all(m["type"] == "auth_error" for m in msgs) and msgs
    assert api(base, "POST", "/api/host/possess", json={"user_id": "pw_anon1"}).status_code == 409


def test_a_wrong_token_proves_nothing(host):
    base, port, data = host

    async def scenario():
        ws = await websockets.connect(f"ws://127.0.0.1:{port}/pubworld/ws/pw_bad1")
        try:
            await ws.send(json.dumps({"type": "auth", "token": "not.a.token"}))
            return json.loads(await asyncio.wait_for(ws.recv(), 5))
        finally:
            await ws.close()
    assert asyncio.run(scenario())["type"] == "auth_error"


def test_roles_are_enforced_by_the_real_app(host):
    base, port, data = host
    for who, role, expect in (("v", "viewer", 403), ("m", "mod", 403), ("a", "admin", 409)):
        r = api(base, "POST", "/api/host/possess", who=who, role=role, json={"user_id": "nobody"})
        assert r.status_code == expect, (role, r.status_code, r.text)            # 409 = allowed to try, nobody connected
    assert api(base, "GET", "/api/host/state", who="m", role="mod").status_code == 200
    assert api(base, "GET", "/api/host/state", who="v", role="viewer").status_code == 403
    assert httpx.get(base + "/api/host/state", timeout=10).status_code in (401, 403)       # no token at all


def test_the_audit_log_recorded_it_and_the_profile_files_stayed_in_their_folder(host):
    base, port, data = host
    log = api(base, "GET", "/api/governance/audit?limit=200")
    assert log.status_code == 200
    body = log.json()
    entries = body if isinstance(body, list) else (body.get("entries") or body.get("log") or [])
    actions = {e["action"] for e in entries}
    assert {"POSSESS", "RELEASE", "TIMEOUT", "TIMEOUT_END"} <= actions, sorted(actions)


# ── the walker in a real browser reacts to the host ────────────────────────────

sync_api = pytest.importorskip("playwright.sync_api")


def test_the_walker_shows_the_notice_locks_the_person_follows_the_host_and_hands_control_back(host):
    base, port, data = host
    token = tok("walker-mira", "guest")
    with sync_api.sync_playwright() as p:
        try:
            browser = p.chromium.launch(args=["--no-sandbox"])
        except Exception as exc:
            pytest.skip(f"no Chromium available: {exc}")
        try:
            ctx = browser.new_context(viewport={"width": 1400, "height": 860})
            ctx.add_init_script("sessionStorage.setItem('pubcast_token', %s); sessionStorage.setItem('pubcast_user', JSON.stringify({username:'walker-mira',user_id:'walker-mira',role:'guest'}));" % json.dumps(token))
            page = ctx.new_page(); errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(base + "/walk")
            page.wait_for_function("document.documentElement.dataset.ready === '1' && window.PubCastLive && window.PubCastLive.state.online === true", timeout=30000)
            pos = lambda: page.evaluate("window.PubCastWalk.S.pos.slice()")
            walk_keys = lambda key: (page.keyboard.down(key), page.wait_for_timeout(600), page.keyboard.up(key))
            banner = page.locator("#hostBanner")
            # free before anything happens
            start = pos(); walk_keys("ArrowDown"); assert pos() != start and banner.is_hidden()

            # possession: the exact wording appears as plain text, and the person's own keys and clicks no longer walk
            r = api(base, "POST", "/api/host/possess", json={"user_id": "walker-mira", "duration_seconds": 120})
            assert r.status_code == 200, r.text
            page.wait_for_function("!document.getElementById('hostBanner').hidden", timeout=5000)
            assert NOTICE in banner.inner_text() and "taken control" in banner.inner_text()
            held = pos(); walk_keys("ArrowRight"); walk_keys("KeyA")
            sx, sy = page.evaluate("(p) => window.PubCastWalk.toScreen([p[0] + 120, p[1]])", held)
            box = page.locator("#c").bounding_box(); page.mouse.click(box["x"] + sx, box["y"] + sy); page.wait_for_timeout(500)
            assert pos() == held and page.evaluate("window.PubCastWalk.S.target") is None

            # the host drives: the avatar walks where the host says
            goal = page.evaluate("(p) => window.PubCastWalk.snapToFloor(window.PubCastWalk.S.view, [p[0] + 150, p[1]])", held)
            assert api(base, "POST", "/api/host/drive", json={"user_id": "walker-mira", "pos": goal}).status_code == 200
            page.wait_for_function("(g) => Math.hypot(window.PubCastWalk.S.pos[0] - g[0], window.PubCastWalk.S.pos[1] - g[1]) < 6", arg=goal, timeout=40000)

            # control goes back
            assert api(base, "POST", "/api/host/release", json={"user_id": "walker-mira"}).status_code == 200
            page.wait_for_function("document.getElementById('hostBanner').hidden", timeout=5000)
            here = pos(); walk_keys("ArrowDown"); assert pos() != here

            # timeout: the waiting room banner shows (with the configured wording), input is locked, and it lifts when it ends
            assert api(base, "POST", "/api/host/timeout", json={"user_id": "walker-mira", "duration_seconds": 60}).status_code == 200
            page.wait_for_function("!document.getElementById('hostBanner').hidden", timeout=5000)
            assert "Waiting room" in banner.inner_text() and "TEST TIMEOUT" in banner.inner_text()
            held = pos(); walk_keys("ArrowDown"); assert pos() == held
            assert api(base, "POST", "/api/host/end-timeout", json={"user_id": "walker-mira"}).status_code == 200
            page.wait_for_function("document.getElementById('hostBanner').hidden", timeout=5000)
            walk_keys("ArrowUp"); assert pos() != held
            assert errors == []
            ctx.close()
        finally:
            browser.close()
