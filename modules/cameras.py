# PubCast AI — cameras.py
# Copyright © 2024–2026 Josie Curtsey Cobbley (Joshua Cobbley)
# Rearview Foresight LLC — All Rights Reserved
# Feic Mo Chroí — See My Heart
"""
Camera Management System for PubCast AI

Professional camera source management supporting NDI, RTMP, SRT, virtual cameras,
and future integration with Rust rendering core for 3D voxel cameras.
"""

from __future__ import annotations

import time
import uuid
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Union


class CameraTransport(str, Enum):
    """Delivery mechanism for a camera feed."""

    NDI = "ndi"
    RTMP = "rtmp"
    SRT = "srt"
    FILE = "file"
    VIRTUAL = "virtual"
    VOXEL_3D = "voxel_3d"  # For future Rust renderer integration


@dataclass
class CameraSource:
    """Describes a physical or virtual camera feed that can be recorded."""

    source_id: str
    name: str
    location: str
    description: str
    transport: CameraTransport
    endpoint: str
    audio_channels: int = 2
    video_enabled: bool = True
    audio_enabled: bool = True
    tags: List[str] = field(default_factory=list)
    is_private: bool = False

    # 3D positioning for voxel cameras (future Rust integration)
    position: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    rotation: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    fov: float = 60.0


@dataclass(frozen=True)
class CameraSwitchEvent:
    destination: str
    source_id: Optional[str]
    previous_source_id: Optional[str]
    timestamp: float = field(default_factory=time.time)
    event_id: str = field(default_factory=lambda: f"cam-switch-{uuid.uuid4().hex}")


@dataclass(frozen=True)
class CameraPoseEvent:
    source_id: str
    position: List[float]
    rotation: List[float]
    fov: float
    timestamp: float = field(default_factory=time.time)
    event_id: str = field(default_factory=lambda: f"cam-pose-{uuid.uuid4().hex}")


CameraEvent = Union[CameraSwitchEvent, CameraPoseEvent]


@dataclass
class CameraStatus:
    """Represents the health of a camera feed."""

    source_id: str
    online: bool
    last_check: float = field(default_factory=time.time)
    latency_ms: Optional[float] = None
    frame_rate: Optional[float] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class CameraStateSnapshot:
    program: Optional[str] = None
    preview: Optional[str] = None


class CameraManager:
    """
    Keeps track of all camera feeds and their latest health information.
    Designed for integration with Rust rendering core for high-performance 3D cameras.
    """

    def __init__(self) -> None:
        self._sources: Dict[str, CameraSource] = {}
        self._status: Dict[str, CameraStatus] = {}

        # Program/Preview switching (professional broadcast workflow)
        self._program_source: Optional[str] = None
        self._preview_source: Optional[str] = None
        self._listeners: Dict[int, Callable[[CameraEvent], None]] = {}
        self._next_listener_id = 1

    # Registration and lookup
    def register(self, source: CameraSource) -> None:
        """Register a camera source."""
        self._sources[source.source_id] = source
        if source.source_id not in self._status:
            self._status[source.source_id] = CameraStatus(
                source_id=source.source_id,
                online=True,
                notes="Registered",
            )

    def remove(self, source_id: str) -> bool:
        """Remove a source and clear any stale program/preview references."""
        if source_id not in self._sources:
            return False

        previous_program = self._program_source
        previous_preview = self._preview_source

        self._sources.pop(source_id, None)
        self._status.pop(source_id, None)

        if previous_program == source_id:
            self._program_source = None
        if previous_preview == source_id:
            self._preview_source = None
        # Commit both references before listeners can observe the removal.
        if previous_program == source_id:
            self._emit(CameraSwitchEvent("program", None, source_id, time.time()))
        if previous_preview == source_id:
            self._emit(CameraSwitchEvent("preview", None, source_id, time.time()))

        return True

    def list_sources(self) -> List[CameraSource]:
        """Get all registered camera sources."""
        return list(self._sources.values())

    def get(self, source_id: str) -> Optional[CameraSource]:
        """Get specific camera source by ID."""
        return self._sources.get(source_id)

    def snapshot(self) -> CameraStateSnapshot:
        """Return the live program/preview state as a stable snapshot."""
        return CameraStateSnapshot(
            program=self._program_source,
            preview=self._preview_source,
        )

    # Canonical camera events / Program-Preview switching
    def subscribe(self, callback: Callable[[CameraEvent], None]) -> int:
        token = self._next_listener_id
        self._next_listener_id += 1
        self._listeners[token] = callback
        return token

    def unsubscribe(self, token: int) -> bool:
        return self._listeners.pop(token, None) is not None

    def _emit(self, event: CameraEvent) -> None:
        for callback in list(self._listeners.values()):
            try:
                callback(event)
            except Exception:
                # Camera state is authoritative; diagnostics may not roll it back.
                pass

    def _ensure_valid_source(self, source_id: str) -> Optional[CameraSource]:
        if source_id is None:
            return None
        return self._sources.get(source_id)

    def set_program_source(self, source_id: str) -> bool:
        """Set Program. Invalid/idempotent changes do not emit an event."""
        source = self._ensure_valid_source(source_id)
        if source is None:
            return False
        previous = self._program_source
        if previous == source_id:
            return True
        self._program_source = source_id
        self._emit(CameraSwitchEvent("program", source_id, previous, time.time()))
        return True

    def set_preview_source(self, source_id: str) -> bool:
        """Set Preview. Invalid/idempotent changes do not emit an event."""
        source = self._ensure_valid_source(source_id)
        if source is None:
            return False
        previous = self._preview_source
        if previous == source_id:
            return True
        self._preview_source = source_id
        self._emit(CameraSwitchEvent("preview", source_id, previous, time.time()))
        return True

    def update_pose(self, source_id: str, *, position=None, rotation=None, fov=None) -> bool:
        """Validate the whole edit before committing any part of the pose."""
        source = self._sources.get(source_id)
        if source is None:
            return False

        def vector(value, name, current):
            if value is None:
                return list(current)
            if (not isinstance(value, (list, tuple)) or len(value) != 3
                    or any(isinstance(v, bool) or not isinstance(v, (int, float))
                           for v in value)):
                raise ValueError(f"{name} must contain three finite numbers (x,y,z)")
            try:
                result = [float(v) for v in value]
            except (OverflowError, ValueError):
                raise ValueError(f"{name} must contain three finite numbers (x,y,z)") from None
            if not all(math.isfinite(v) for v in result):
                raise ValueError(f"{name} must contain three finite numbers (x,y,z)")
            return result

        pos = vector(position, "position", source.position)
        rot = vector(rotation, "rotation", source.rotation)
        new_fov = source.fov
        if fov is not None:
            try:
                if isinstance(fov, bool):
                    raise ValueError
                new_fov = float(fov)
            except (TypeError, ValueError, OverflowError):
                raise ValueError("fov must be between 1 and 179 degrees") from None
            if not 1.0 <= new_fov <= 179.0:
                raise ValueError("fov must be between 1 and 179 degrees")
        changed = pos != source.position or rot != source.rotation or new_fov != source.fov
        if changed:
            source.position, source.rotation, source.fov = pos, rot, new_fov
            self._emit(CameraPoseEvent(source_id, list(pos), list(rot), new_fov))
        return True

    def take(self) -> bool:
        """Atomically exchange Program and Preview, then emit the resulting changes."""
        if not self._program_source or not self._preview_source:
            return False
        old_program, old_preview = self._program_source, self._preview_source
        if old_program == old_preview:
            return True

        self._program_source, self._preview_source = old_preview, old_program
        now = time.time()
        self._emit(CameraSwitchEvent("program", self._program_source, old_program, now))
        self._emit(CameraSwitchEvent("preview", self._preview_source, old_preview, now))
        return True

    def get_program_source(self) -> Optional[CameraSource]:
        """Get current program source."""
        if self._program_source:
            return self._sources.get(self._program_source)
        return None

    def get_preview_source(self) -> Optional[CameraSource]:
        """Get current preview source."""
        if self._preview_source:
            return self._sources.get(self._preview_source)
        return None

    def get_program_source_id(self) -> Optional[str]:
        return self._program_source

    def get_preview_source_id(self) -> Optional[str]:
        return self._preview_source

    # Status management
    def set_status(
        self,
        source_id: str,
        *,
        online: Optional[bool] = None,
        latency_ms: Optional[float] = None,
        frame_rate: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> None:
        """Update camera status metrics."""
        if source_id not in self._sources:
            raise KeyError(f"Unknown camera '{source_id}'")

        entry = self._status.setdefault(
            source_id,
            CameraStatus(source_id=source_id, online=True),
        )

        if online is not None:
            entry.online = online
        if latency_ms is not None:
            entry.latency_ms = latency_ms
        if frame_rate is not None:
            entry.frame_rate = frame_rate
        if notes is not None:
            entry.notes = notes
        entry.last_check = time.time()

    def status(self, source_id: str) -> Optional[CameraStatus]:
        """Get status for specific camera."""
        return self._status.get(source_id)

    def list_status(self) -> List[CameraStatus]:
        """Get status for all cameras."""
        return list(self._status.values())


# Factory function for default camera setup
def create_default_cameras() -> CameraManager:
    """Create camera manager with default virtual camera setup."""

    manager = CameraManager()

    # Virtual cameras for immediate use
    manager.register(
        CameraSource(
            source_id="wide_shot",
            name="Wide Shot",
            description="Wide angle view of the scene",
            location="virtual",
            transport=CameraTransport.VIRTUAL,
            endpoint="virtual://wide_shot",
            position=[0.0, 2.0, 5.0],
            rotation=[0.0, 0.0, 0.0],
            fov=75.0,
            tags=["virtual", "wide", "establishing"],
        )
    )

    manager.register(
        CameraSource(
            source_id="medium_shot",
            name="Medium Shot",
            description="Medium framing for dialogue",
            location="virtual",
            transport=CameraTransport.VIRTUAL,
            endpoint="virtual://medium_shot",
            position=[2.0, 1.5, 3.0],
            rotation=[0.0, -15.0, 0.0],
            fov=50.0,
            tags=["virtual", "medium", "dialogue"],
        )
    )

    manager.register(
        CameraSource(
            source_id="close_up",
            name="Close Up",
            description="Close framing for emotion",
            location="virtual",
            transport=CameraTransport.VIRTUAL,
            endpoint="virtual://close_up",
            position=[1.0, 1.0, 1.5],
            rotation=[0.0, 0.0, 0.0],
            fov=35.0,
            tags=["virtual", "close", "emotion"],
        )
    )

    manager.register(
        CameraSource(
            source_id="overhead",
            name="Overhead Shot",
            description="Top-down view",
            location="virtual",
            transport=CameraTransport.VIRTUAL,
            endpoint="virtual://overhead",
            position=[0.0, 5.0, 0.0],
            rotation=[90.0, 0.0, 0.0],
            fov=90.0,
            tags=["virtual", "overhead", "establishing"],
        )
    )

    # Physical camera examples (NDI sources)
    manager.register(
        CameraSource(
            source_id="cam1_ndi",
            name="Camera 1 NDI",
            description="Physical NDI camera #1",
            location="studio",
            transport=CameraTransport.NDI,
            endpoint="ndi://camera-1",
            tags=["physical", "ndi", "studio"],
        )
    )

    manager.register(
        CameraSource(
            source_id="cam2_rtmp",
            name="Camera 2 RTMP",
            description="RTMP stream camera #2",
            location="remote",
            transport=CameraTransport.RTMP,
            endpoint="rtmp://streaming-server/cam2",
            tags=["physical", "rtmp", "remote"],
        )
    )

    # Set default program/preview
    manager.set_program_source("wide_shot")
    manager.set_preview_source("medium_shot")

    return manager
