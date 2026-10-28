"""A slow camera display must not freeze other displays or room membership."""
import asyncio
import json

import pytest
from starlette.websockets import WebSocketState
from modules.hub import Hub


class Socket:
    application_state = WebSocketState.CONNECTED

    def __init__(self, *, blocked=False):
        self.blocked = blocked
        self.messages = []
        self.closed = False
        self.entered = asyncio.Event()
        self.release = asyncio.Event()

    async def send_text(self, wire):
        self.entered.set()
        if self.blocked:
            await self.release.wait()
        self.messages.append(json.loads(wire))

    async def close(self, **kwargs):
        self.closed = True
        self.application_state = WebSocketState.DISCONNECTED


@pytest.mark.asyncio
async def test_camera_frame_evicts_slow_peer_and_delivers_to_healthy_peer(tmp_path):
    hub = Hub(tmp_path)
    hub.camera_send_timeout = 0.02
    slow, healthy = Socket(blocked=True), Socket()
    hub.rooms["studio"] = {slow, healthy}
    hub._ws_meta[id(slow)] = {"uid": "slow"}
    event = {"type": "camera_switch", "payload": {"source_id": "overhead"}}
    send = asyncio.create_task(hub.broadcast_system_event(event))
    try:
        await asyncio.wait_for(send, 0.5)
        assert healthy.messages == [event]
        assert slow not in hub.rooms["studio"] and id(slow) not in hub._ws_meta
        assert slow.closed and not slow.messages
    finally:
        slow.release.set()
        if not send.done():
            send.cancel()
            await asyncio.gather(send, return_exceptions=True)


@pytest.mark.asyncio
async def test_system_room_snapshot_survives_room_added_during_send(tmp_path):
    hub = Hub(tmp_path)
    first = Socket(blocked=True)
    hub.rooms["studio"] = {first}
    send = asyncio.create_task(hub.broadcast_system_event({"type": "production_state"}))
    try:
        await asyncio.wait_for(first.entered.wait(), 1)
        hub.rooms["new-room"] = {Socket()}
        first.release.set()
        await asyncio.wait_for(send, 1)
        assert len(first.messages) == 1
    finally:
        first.release.set()
        if not send.done():
            send.cancel()
            await asyncio.gather(send, return_exceptions=True)


@pytest.mark.asyncio
async def test_camera_broadcast_preserves_private_room_revocation_guard(tmp_path):
    hub = Hub(tmp_path)
    hub.dm_authorizer = lambda *args: False
    socket = Socket()
    room = "dm____alice____bob"
    hub.rooms[room] = {socket}
    hub._ws_meta[id(socket)] = {"uid": "alice", "dm_peer": "bob", "authenticated": True}
    await hub.broadcast_system_event({"type": "camera_switch", "payload": {"source_id": "overhead"}})
    assert not socket.messages and socket.closed
    assert socket not in hub.rooms[room]


@pytest.mark.asyncio
async def test_one_socket_in_multiple_rooms_gets_one_camera_frame(tmp_path):
    hub = Hub(tmp_path)
    socket = Socket()
    hub.rooms.update({"studio": {socket}, "lobby": {socket}})
    event = {"type": "camera_switch", "payload": {"source_id": "overhead"}}
    await hub.broadcast_system_event(event)
    assert socket.messages == [event]


@pytest.mark.asyncio
async def test_slow_camera_socket_is_removed_from_every_room(tmp_path):
    hub = Hub(tmp_path)
    hub.camera_send_timeout = 0.01
    socket = Socket(blocked=True)
    hub.rooms.update({"studio": {socket}, "lobby": {socket}})
    await hub.broadcast_system_event({"type": "camera_switch"})
    assert all(socket not in peers for peers in hub.rooms.values())
    assert socket.closed
