"""Invalid edits and slow sockets must not leave cameras in contradictory states."""
import asyncio
import io
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from modules.camera_broadcast import CameraBroadcastBridge
from modules.cameras import create_default_cameras
from modules.cameras_advanced import CameraMetadata, CameraSource, CameraTransport
from fastapi import FastAPI
from starlette.testclient import TestClient
from modules.switcher_routes import SwitcherService, create_switcher_router


@pytest.mark.parametrize("edit", [
    {"position": [1, 2, 3], "rotation": [4, 5]},
    {"position": [1, 2, 3], "fov": 0},
    {"position": [float("nan"), 2, 3]},
    {"rotation": [0, float("inf"), 0]},
    {"position": "123"},
    {"position": [True, 2, 3]},
])
def test_invalid_pose_edit_changes_nothing(edit):
    cameras = create_default_cameras()
    camera = cameras.get("wide_shot")
    before = (list(camera.position), list(camera.rotation), camera.fov)
    events = []
    cameras.subscribe(events.append)
    with pytest.raises(ValueError):
        cameras.update_pose("wide_shot", **edit)
    assert (camera.position, camera.rotation, camera.fov) == before
    assert not events


def test_removing_shared_program_preview_is_complete_before_notifications():
    cameras = create_default_cameras()
    cameras.set_preview_source("wide_shot")
    observed = []
    cameras.subscribe(lambda event: observed.append(cameras.snapshot()))
    assert cameras.remove("wide_shot")
    assert len(observed) == 2
    assert all(s.program is None and s.preview is None for s in observed)


def test_pose_route_refuses_bad_edits_without_partial_changes():
    cameras = create_default_cameras()
    app = FastAPI()
    app.include_router(create_switcher_router(SwitcherService(cameras)))
    before = list(cameras.get("wide_shot").position)
    with TestClient(app) as client:
        r = client.post("/api/switcher/ptz/wide_shot",
            json={"position": [1, 2, 3], "fov": 0})
        assert r.status_code == 400
        assert cameras.get("wide_shot").position == before
        assert client.post("/api/switcher/ptz/missing", json={}).status_code == 404
        assert client.post("/api/switcher/ptz/wide_shot",
            json={"position": [1, 2, 3], "rotation": [0, 10, 0], "fov": 60}).status_code == 200
        assert cameras.get("wide_shot").position == [1, 2, 3]


def test_pose_commit_emits_one_complete_event_and_repeating_it_is_silent():
    cameras = create_default_cameras()
    events = []
    cameras.subscribe(events.append)
    edit = {"position": [1, 2, 3], "rotation": [5, 10, 15], "fov": 60}
    assert cameras.update_pose("wide_shot", **edit)
    assert cameras.update_pose("wide_shot", **edit)
    assert len(events) == 1
    assert events[0].position == [1, 2, 3]
    assert events[0].rotation == [5, 10, 15] and events[0].fov == 60


@pytest.mark.asyncio
async def test_slow_first_broadcast_cannot_be_overtaken():
    entered, release = asyncio.Event(), asyncio.Event()

    class SlowHub:
        def __init__(self):
            self.messages = []

        async def broadcast_system_event(self, message):
            if message["payload"]["source_id"] == "close_up":
                entered.set()
                await release.wait()
            self.messages.append(message)

    cameras, hub = create_default_cameras(), SlowHub()
    bridge = CameraBroadcastBridge(cameras, hub)
    bridge.start()
    try:
        cameras.set_program_source("close_up")
        await asyncio.wait_for(entered.wait(), 1)
        cameras.set_program_source("overhead")
        await asyncio.sleep(0)
        assert hub.messages == [], "newer cut overtook the blocked first cut"
        release.set()
        for _ in range(20):
            if len(hub.messages) == 2:
                break
            await asyncio.sleep(0)
        assert [m["payload"]["source_id"] for m in hub.messages] == ["close_up", "overhead"]
    finally:
        release.set()
        await bridge.stop()


@pytest.mark.asyncio
async def test_failed_send_does_not_block_later_cuts():
    class Hub:
        def __init__(self):
            self.delivered = []

        async def broadcast_system_event(self, message):
            if message["payload"]["source_id"] == "close_up":
                raise RuntimeError("disconnected")
            self.delivered.append(message["payload"]["source_id"])

    cameras, hub = create_default_cameras(), Hub()
    bridge = CameraBroadcastBridge(cameras, hub)
    bridge.start()
    try:
        cameras.set_program_source("close_up")
        cameras.set_program_source("overhead")
        for _ in range(20):
            if hub.delivered:
                break
            await asyncio.sleep(0)
        assert hub.delivered == ["overhead"]
        assert cameras.get_program_source_id() == "overhead"
    finally:
        await bridge.stop()


@pytest.mark.asyncio
async def test_shutdown_cancels_blocked_sender_and_queue_then_restarts():
    entered = asyncio.Event()

    class Hub:
        async def broadcast_system_event(self, message):
            entered.set()
            await asyncio.Event().wait()

    cameras = create_default_cameras()
    bridge = CameraBroadcastBridge(cameras, Hub())
    bridge.start()
    cameras.set_program_source("close_up")
    await asyncio.wait_for(entered.wait(), 1)
    cameras.set_program_source("overhead")
    await asyncio.sleep(0)
    tasks = list(bridge._tasks)
    assert len(tasks) == 2
    await bridge.stop(timeout=0.1)
    assert all(t.done() and t.cancelled() for t in tasks)
    assert not bridge._tasks
    bridge.start()
    await bridge.stop()


def test_one_broken_pipe_close_does_not_skip_other_pipes_or_reset(monkeypatch):
    broken = Mock()
    broken.read.return_value = b""
    broken.close.side_effect = OSError("pipe close failed")
    stderr, stdin = io.BytesIO(), io.BytesIO()
    proc = SimpleNamespace(stdout=broken, stderr=stderr, stdin=stdin,
        poll=Mock(return_value=0), terminate=Mock(), wait=Mock(), kill=Mock())
    import subprocess
    monkeypatch.setattr(subprocess, "Popen", Mock(return_value=proc))
    camera = CameraSource("cleanup", CameraMetadata(name="cleanup",
        transport=CameraTransport.FILE_PLAYBACK, connection_string="unused", width=1, height=1))
    camera.is_capturing = True
    camera._capture_frames(["-i", "unused"])
    assert stderr.closed and stdin.closed
    assert camera.capture_process is None and not camera.is_capturing
