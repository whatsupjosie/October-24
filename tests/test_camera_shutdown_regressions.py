"""Shutdown must account for actual workers, including queued thread callbacks."""
import asyncio
import threading
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from modules.camera_broadcast import CameraBroadcastBridge
from modules.cameras import create_default_cameras
from modules.cameras_advanced import (
    CameraMetadata, CameraSource, CameraStatus, CameraTransport,
)
from tests.host_lifespan_helpers import run_isolated_host


class Hub:
    def __init__(self):
        self.messages = []

    async def broadcast_system_event(self, message):
        self.messages.append(message)


@pytest.mark.asyncio
async def test_stop_retains_resistant_task_and_reports_timeout():
    bridge = CameraBroadcastBridge(create_default_cameras(), Hub())
    bridge.start()
    entered, release = asyncio.Event(), asyncio.Event()

    async def resistant():
        entered.set()
        while not release.is_set():
            try:
                await release.wait()
            except asyncio.CancelledError:
                pass

    task = asyncio.create_task(resistant())
    bridge._tasks.add(task)
    await entered.wait()
    try:
        with pytest.raises(TimeoutError):
            await bridge.stop(timeout=0.01)
        assert not task.done() and task in bridge._tasks
        with pytest.raises(RuntimeError):
            bridge.start()
    finally:
        release.set()
        await task
        await bridge.stop()
    assert not bridge._tasks


def capture_camera():
    return CameraSource("shutdown", CameraMetadata(name="shutdown",
        transport=CameraTransport.FILE_PLAYBACK, connection_string="unused"))


@pytest.mark.asyncio
async def test_capture_waits_for_worker_cleanup_after_forced_kill():
    camera = capture_camera()
    loop = asyncio.get_running_loop()
    worker = loop.create_future()
    cleaned = asyncio.Event()

    async def cleanup():
        await asyncio.sleep(0)
        cleaned.set()
        worker.set_result(None)

    process = SimpleNamespace(poll=Mock(return_value=None), terminate=Mock(),
        kill=Mock(side_effect=lambda: loop.create_task(cleanup())))
    camera.capture_process = process
    camera.capture_task = worker
    await camera.stop_capture(timeout=0.01)
    process.terminate.assert_called_once()
    process.kill.assert_called_once()
    assert worker.done() and not worker.cancelled() and cleaned.is_set()
    assert camera.metadata.status == CameraStatus.OFFLINE


@pytest.mark.asyncio
async def test_capture_timeout_keeps_worker_owned_and_blocks_restart():
    camera = capture_camera()
    camera.capture_task = asyncio.get_running_loop().create_future()
    try:
        with pytest.raises(TimeoutError):
            await camera.stop_capture(timeout=0.01)
        assert not camera.capture_task.done()
        assert camera.metadata.status == CameraStatus.ERROR
        assert await camera.start_capture() is False
    finally:
        camera.capture_task.set_result(None)
        await camera.stop_capture(timeout=0.01)


@pytest.mark.asyncio
async def test_cancelled_capture_stop_does_not_cancel_executor_future():
    camera = capture_camera()
    camera.capture_task = asyncio.get_running_loop().create_future()
    stop = asyncio.create_task(camera.stop_capture(timeout=1))
    await asyncio.sleep(0)
    stop.cancel()
    with pytest.raises(asyncio.CancelledError):
        await stop
    assert not camera.capture_task.done()
    camera.capture_task.set_result(None)
    await camera.stop_capture()


@pytest.mark.asyncio
@pytest.mark.parametrize("restart", [False, True])
async def test_queued_worker_event_cannot_cross_stop_or_restart(restart):
    cameras, hub = create_default_cameras(), Hub()
    bridge = CameraBroadcastBridge(cameras, hub)
    bridge.start()
    worker = threading.Thread(target=cameras.set_program_source, args=("overhead",))
    worker.start()
    worker.join()  # Queue the delivery while deliberately keeping the loop busy.
    await bridge.stop()
    if restart:
        bridge.start()
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    try:
        assert not hub.messages
        assert not bridge._tasks
    finally:
        await bridge.stop()


@pytest.mark.asyncio
async def test_stop_waits_for_task_cleanup_to_finish():
    bridge = CameraBroadcastBridge(create_default_cameras(), Hub())
    bridge.start()
    entered, cleaned = asyncio.Event(), asyncio.Event()

    async def worker():
        try:
            entered.set()
            await asyncio.Event().wait()
        finally:
            await asyncio.sleep(0)
            cleaned.set()

    task = asyncio.create_task(worker())
    bridge._tasks.add(task)
    await entered.wait()
    await bridge.stop()
    assert task.done() and task.cancelled() and cleaned.is_set()
    assert not bridge._tasks


@pytest.mark.parametrize("reentry", [False, True])
def test_app_finishes_other_cleanup_before_reporting_camera_timeout(tmp_path, reentry):
    script = '''
from starlette.testclient import TestClient
import main

if REENTRY:
    with TestClient(main.app):
        pass
cleaned = []
try:
    with TestClient(main.app):
        bridge = main.app.state.camera_broadcast
        original_stop = bridge.stop
        original_shutdown = main.bot_manager.shutdown
        original_memory_close = main.app.state.system_memory.close
        async def stop_with_timeout():
            await original_stop()
            raise TimeoutError("camera regression probe")
        async def finish_bot_cleanup():
            await original_shutdown()
            cleaned.append("bots")
        async def finish_memory_cleanup():
            await original_memory_close()
            cleaned.append("memory")
        bridge.stop = stop_with_timeout
        main.bot_manager.shutdown = finish_bot_cleanup
        main.app.state.system_memory.close = finish_memory_cleanup
except TimeoutError as exc:
    assert "camera regression probe" in str(exc)
else:
    raise AssertionError("camera timeout was hidden")
assert set(cleaned) == {"bots", "memory"}, "camera timeout skipped other subsystem shutdown"
'''.replace("REENTRY", repr(reentry))
    run_isolated_host(script, tmp_path)
