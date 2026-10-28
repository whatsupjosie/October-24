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
        self._generation = 0
        self._send_lock = asyncio.Lock()
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
        if any(not task.done() for task in self._tasks):
            raise RuntimeError("camera bridge still has unfinished shutdown tasks")
        self._tasks.clear()
        self._generation += 1
        self._loop = asyncio.get_running_loop()
        self._send_lock = asyncio.Lock()
        generation = self._generation
        self._token = self.cameras.subscribe(
            lambda event: self._on_event(event, generation=generation)
        )
        if self.hub is not None:
            setattr(self.hub, "camera_events_bridged", True)

    async def stop(self, timeout: float = 5.0) -> None:
        """Cancel deliveries and wait for cleanup; retain and report any stragglers.

        Python cannot forcibly finish a coroutine that suppresses cancellation.
        A timed-out stop therefore raises instead of claiming a clean shutdown.
        Calling stop again can finish cleanup; start refuses while tasks remain.
        """
        if timeout < 0:
            raise ValueError("shutdown timeout must be nonnegative")
        self._generation += 1
        self._loop = None
        if self._token is not None:
            self.cameras.unsubscribe(self._token)
            self._token = None
        if self.hub is not None and getattr(self.hub, "camera_events_bridged", False):
            setattr(self.hub, "camera_events_bridged", False)

        self._seen_event_ids.clear()
        self._tasks.difference_update(task for task in tuple(self._tasks) if task.done())
        pending = [task for task in self._tasks if not task.done()]
        if pending:
            for task in pending:
                task.cancel()
            done, pending = await asyncio.wait(pending, timeout=timeout)
            self._tasks.difference_update(done)
            if pending:
                raise TimeoutError(f"{len(pending)} camera broadcast task(s) did not stop")

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

    def _on_event(self, event: Any, *, generation: Optional[int] = None) -> None:
        loop = self._loop
        generation = self._generation if generation is None else generation
        if (not isinstance(event, CameraSwitchEvent) or self.hub is None
                or loop is None or not self.running or generation != self._generation):
            return
        # Capture the state at the change, before a worker queues delivery.
        message = self.message(event)

        def schedule() -> None:
            # A thread may have queued this immediately before stop, or even
            # before a stop/start cycle. Old subscriptions never send again.
            if (not self.running or self._loop is not loop
                    or generation != self._generation):
                return
            # Cache mutations and task bookkeeping belong to the owning loop.
            if not self._dedupe_event(event):
                return
            task = loop.create_task(self._send(message))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)

        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None
        if running is loop:
            schedule()
        elif not loop.is_closed():
            try:
                loop.call_soon_threadsafe(schedule)
            except RuntimeError:
                # The loop can close between is_closed and enqueueing.
                if not loop.is_closed():
                    raise

    async def _send(self, message: dict) -> None:
        try:
            if self.hub is None or not hasattr(self.hub, "broadcast_system_event"):
                return
            # A slow first cut must finish before a newer cut reaches clients.
            # asyncio locks serve waiters in acquisition order; shutdown still
            # owns and cancels both the sender and the queued waiters.
            async with self._send_lock:
                await self.hub.broadcast_system_event(message)
                self.sent += 1
        except Exception:
            logger.exception("camera_switch broadcast failed for %s", message["payload"].get("source_id"))


__all__ = ["CameraBroadcastBridge"]
