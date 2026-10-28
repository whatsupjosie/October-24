# PubCast AI — camera_broadcast.py
# Copyright © 2024–2026 Josie Curtsey Cobbley (Joshua Cobbley)
# Rearview Foresight LLC — All Rights Reserved
# Feic Mo Chroí — See My Heart
"""One place that tells every page when the program or preview camera changes.

This bridge is the single canonical outbound message path for camera events.
It listens for CameraManager state changes and re-emits a standard camera_switch
payload to the hub so the UI and other app components stay in sync.
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections import OrderedDict
from typing import Any, Optional, Set

from .cameras import CameraManager, CameraSwitchEvent

logger = logging.getLogger("pubcast.camera_broadcast")


class CameraBroadcastBridge:
    def __init__(self, cameras: CameraManager, hub: Any):
        self.cameras = cameras
        self.hub = hub
        self._token: Optional[int] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._tasks: Set[asyncio.Task] = set()
        self._seen_event_ids: "OrderedDict[str, None]" = OrderedDict()
        self.max_event_cache = 1000
        self.sent = 0

    @property
    def running(self) -> bool:
        return self._token is not None

    def start(self) -> None:
        """Subscribe from inside the running event loop (the app lifespan)."""
        if self._token is not None:
            return
        self._loop = asyncio.get_running_loop()
        self._token = self.cameras.subscribe(self._on_event)
        if self.hub is not None:
            setattr(self.hub, "camera_events_bridged", True)

    async def stop(self, timeout: float = 5.0) -> None:
        if self._token is not None:
            self.cameras.unsubscribe(self._token)
            self._token = None
        if self.hub is not None and getattr(self.hub, "camera_events_bridged", False):
            setattr(self.hub, "camera_events_bridged", False)

        pending = [task for task in self._tasks if not task.done()]
        if pending:
            for task in pending:
                task.cancel()
            done, pending = await asyncio.wait(pending, timeout=timeout, return_when=asyncio.ALL_COMPLETED)
            for task in pending:
                task.cancel()
            self._tasks = {task for task in done if task not in pending}
        self._tasks.clear()
        self._seen_event_ids.clear()

    def _dedupe_event(self, event: CameraSwitchEvent) -> bool:
        event_id = getattr(event, "event_id", None)
        if not event_id:
            return True
        if event_id in self._seen_event_ids:
            self._seen_event_ids.move_to_end(event_id)
            return False
        self._seen_event_ids[event_id] = None
        if len(self._seen_event_ids) > self.max_event_cache:
            self._seen_event_ids.popitem(last=False)
        return True

    def message(self, event: CameraSwitchEvent) -> dict:
        snapshot = self.cameras.snapshot()
        return {
            "type": "camera_switch",
            "payload": {
                "target": event.destination,
                "source_id": event.source_id,
                "previous_source_id": event.previous_source_id,
                "program": snapshot.program,
                "preview": snapshot.preview,
                "timestamp": event.timestamp or time.time(),
                "event_id": getattr(event, "event_id", None),
            },
        }

    def _on_event(self, event: Any) -> None:
        if not isinstance(event, CameraSwitchEvent) or self.hub is None or self._loop is None:
            return
        if not self._dedupe_event(event):
            return
        message = self.message(event)

        def schedule() -> None:
            task = self._loop.create_task(self._send(message))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)

        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None
        if running is self._loop:
            schedule()
        elif not self._loop.is_closed():
            self._loop.call_soon_threadsafe(schedule)

    async def _send(self, message: dict) -> None:
        try:
            if self.hub is None or not hasattr(self.hub, "broadcast_system_event"):
                return
            await self.hub.broadcast_system_event(message)
            self.sent += 1
        except Exception:
            logger.exception("camera_switch broadcast failed for %s", message["payload"].get("source_id"))


__all__ = ["CameraBroadcastBridge"]
