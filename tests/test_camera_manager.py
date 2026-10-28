import asyncio
import time

import pytest

from modules.camera_broadcast import CameraBroadcastBridge
from modules.cameras import CameraManager, CameraSource, CameraSwitchEvent, CameraTransport


def make_camera(source_id: str, name: str) -> CameraSource:
    return CameraSource(
        source_id=source_id,
        name=name,
        description="test camera",
        location="studio",
        transport=CameraTransport.VIRTUAL,
        endpoint=f"virtual://{source_id}",
    )


def test_register_and_lookup():
    manager = CameraManager()
    source = make_camera("cam_a", "Cam A")
    manager.register(source)

    assert manager.get("cam_a") == source
    assert manager.list_sources() == [source]


def test_invalid_source_rejected():
    manager = CameraManager()
    manager.register(make_camera("cam_a", "Cam A"))

    assert manager.set_program_source("missing") is False
    assert manager.set_preview_source("missing") is False


def test_take_swaps_program_preview():
    manager = CameraManager()
    cam_a = make_camera("cam_a", "Cam A")
    cam_b = make_camera("cam_b", "Cam B")
    manager.register(cam_a)
    manager.register(cam_b)

    manager.set_program_source("cam_a")
    manager.set_preview_source("cam_b")
    manager.take()

    assert manager.get_program_source_id() == "cam_b"
    assert manager.get_preview_source_id() == "cam_a"


def test_remove_clears_stale_source_refs():
    manager = CameraManager()
    manager.register(make_camera("cam_a", "Cam A"))
    manager.register(make_camera("cam_b", "Cam B"))

    manager.set_program_source("cam_a")
    manager.set_preview_source("cam_b")

    assert manager.remove("cam_a") is True
    assert manager.get_program_source_id() is None
    assert manager.get_preview_source_id() == "cam_b"

    assert manager.remove("cam_b") is True
    assert manager.get_preview_source_id() is None


def test_switch_event_has_event_id():
    manager = CameraManager()
    manager.register(make_camera("cam_a", "Cam A"))
    manager.register(make_camera("cam_b", "Cam B"))

    manager.set_program_source("cam_a")
    source_id = manager.get_program_source_id()
    assert source_id == "cam_a"

    event = CameraSwitchEvent("program", "cam_b", "cam_a", time.time())
    assert event.event_id.startswith("cam-switch-")


@pytest.mark.asyncio
async def test_broadcast_bridge_deduplicates_event_ids():
    manager = CameraManager()
    manager.register(make_camera("cam_a", "Cam A"))
    manager.register(make_camera("cam_b", "Cam B"))

    class FakeHub:
        def __init__(self):
            self.messages = []

        async def broadcast_system_event(self, message):
            self.messages.append(message)

    hub = FakeHub()
    bridge = CameraBroadcastBridge(manager, hub)
    bridge.start()

    event = CameraSwitchEvent("program", "cam_b", "cam_a", time.time(), "evt-1")
    bridge._on_event(event)
    bridge._on_event(event)

    await asyncio.sleep(0)

    assert len(hub.messages) == 1
    assert hub.messages[0]["payload"]["event_id"] == "evt-1"
    await bridge.stop()


def test_snapshot_state_is_stable():
    manager = CameraManager()
    manager.register(make_camera("cam_a", "Cam A"))
    manager.register(make_camera("cam_b", "Cam B"))

    manager.set_program_source("cam_a")
    manager.set_preview_source("cam_b")

    snapshot = manager.snapshot()
    assert snapshot.program == "cam_a"
    assert snapshot.preview == "cam_b"

    manager.take()
    snapshot = manager.snapshot()
    assert snapshot.program == "cam_b"
    assert snapshot.preview == "cam_a"


def test_update_pose_validates_ranges():
    manager = CameraManager()
    manager.register(make_camera("cam_a", "Cam A"))

    manager.update_pose("cam_a", position=[1.0, 2.0, 3.0], rotation=[0.0, 5.0, 10.0], fov=60.0)

    cam = manager.get("cam_a")
    assert cam.position == [1.0, 2.0, 3.0]
    assert cam.rotation == [0.0, 5.0, 10.0]
    assert cam.fov == 60.0

    with pytest.raises(ValueError):
        manager.update_pose("cam_a", position=[1.0, 2.0])

    with pytest.raises(ValueError):
        manager.update_pose("cam_a", fov=0.0)


def test_event_cache_eviction_is_ordered():
    bridge = CameraBroadcastBridge(CameraManager(), object())

    for i in range(bridge.max_event_cache + 2):
        event = CameraSwitchEvent("program", f"cam_{i}", "prev", time.time(), f"evt-{i}")
        bridge._dedupe_event(event)

    keys = list(bridge._seen_event_ids.keys())
    assert keys[0] == "evt-2"
    assert keys[-1] == f"evt-{bridge.max_event_cache + 1}"
    assert len(keys) == bridge.max_event_cache


@pytest.mark.asyncio
async def test_bridge_stop_reaps_stuck_tasks():
    manager = CameraManager()
    hub = object()
    bridge = CameraBroadcastBridge(manager, hub)
    bridge._loop = asyncio.get_running_loop()

    async def stalled_task():
        try:
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            raise

    task = asyncio.create_task(stalled_task())
    bridge._tasks.add(task)

    await bridge.stop(timeout=0.05)

    assert bridge.running is False
    assert bool(bridge._tasks) is False
    assert task.done() and task.cancelled()


@pytest.mark.asyncio
async def test_bridge_startup_smoke():
    manager = CameraManager()
    manager.register(make_camera("cam_a", "Cam A"))
    manager.register(make_camera("cam_b", "Cam B"))

    class FakeHub:
        def __init__(self):
            self.messages = []
            self.camera_events_bridged = False

        async def broadcast_system_event(self, message):
            self.messages.append(message)

    hub = FakeHub()
    bridge = CameraBroadcastBridge(manager, hub)
    bridge.start()

    assert bridge.running is True
    assert getattr(hub, "camera_events_bridged", False) is True

    manager.set_program_source("cam_a")
    await asyncio.sleep(0)

    await bridge.stop(timeout=0.5)
    assert bridge.running is False
    assert getattr(hub, "camera_events_bridged", False) is False


__all__ = [
    "CameraManager",
    "CameraSource",
    "CameraSwitchEvent",
    "CameraTransport",
    "CameraBroadcastBridge",
]
