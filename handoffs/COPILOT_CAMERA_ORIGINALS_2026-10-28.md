# Copilot camera source preserved before Codex edits

Source: `whatsupjosie/October-24`, branch `camera-stability-review`, commit `e243181bab18ec5baf865a35092c48488be3dfce`.

Each fenced block below contains the original file verbatim. SHA-256 is over the original UTF-8 bytes.

## modules/cameras.py

SHA-256: `f061563d9749748a7c57d9037f9c7433d060c4a2e86ea6a5b568f8401cd369ec`

````python
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
            self._emit(CameraSwitchEvent("program", None, source_id, time.time()))
        if previous_preview == source_id:
            self._preview_source = None
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
        source = self._sources.get(source_id)
        if source is None:
            return False
        changed = False
        if position is not None:
            pos = [float(v) for v in position]
            if len(pos) != 3:
                raise ValueError("position must contain x,y,z")
            if pos != source.position:
                source.position = pos
                changed = True
        if rotation is not None:
            rot = [float(v) for v in rotation]
            if len(rot) != 3:
                raise ValueError("rotation must contain x,y,z")
            if rot != source.rotation:
                source.rotation = rot
                changed = True
        if fov is not None:
            new_fov = float(fov)
            if not 1.0 <= new_fov <= 179.0:
                raise ValueError("fov must be between 1 and 179 degrees")
            if new_fov != source.fov:
                source.fov = new_fov
                changed = True
        if changed:
            self._emit(CameraPoseEvent(source_id, list(source.position), list(source.rotation), source.fov))
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
````

## modules/camera_broadcast.py

SHA-256: `e038e1b6eb8d322846e014f087f4e1300326f5750aa4cb6cedb2cb472151ee1f`

````python
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
````

## modules/cameras_advanced.py

SHA-256: `14d9502460c6c1bf56c595675a17ba016208caaba915b4d53258e3cf962534e7`

````python
#!/usr/bin/env python3
"""
PubCast AI - Advanced Camera Management System
Copyright (c) 2024-2025 Rear View Foresight LLC
"Feic Mo Chroí - See My Heart"

Complete camera management system with professional broadcast features,
multi-source handling, and seamless integration with the PubCast platform.
"""

import asyncio
import logging
import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
import uuid
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CameraTransport(str, Enum):
    """Camera transport types supported by PubCast"""
    USB_WEBCAM = "usb_webcam"
    IP_CAMERA = "ip_camera"
    NDI_SOURCE = "ndi_source"
    OBS_VIRTUAL = "obs_virtual"
    VOXEL_ENGINE = "voxel_engine"
    SCREEN_CAPTURE = "screen_capture"
    FILE_PLAYBACK = "file_playback"
    VIRTUAL_BACKGROUND = "virtual_background"

class CameraStatus(str, Enum):
    """Camera operational status"""
    OFFLINE = "offline"
    CONNECTING = "connecting"
    ONLINE = "online"
    RECORDING = "recording"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class CameraRole(str, Enum):
    """Camera roles in production"""
    PROGRAM = "program"        # Currently live/program output
    PREVIEW = "preview"        # Selected for next cut
    STANDBY = "standby"        # Available but not selected
    BACKUP = "backup"          # Emergency fallback
    DISABLED = "disabled"      # Temporarily disabled

@dataclass
class CameraMetadata:
    """Rich metadata for camera sources"""
    name: str
    transport: CameraTransport
    status: CameraStatus = CameraStatus.OFFLINE
    role: CameraRole = CameraRole.STANDBY
    
    # Connection details
    connection_string: str = ""
    username: str = ""
    password: str = ""
    port: int = 0
    
    # Video specifications
    width: int = 1920
    height: int = 1080
    fps: float = 30.0
    format: str = "h264"
    
    # Quality metrics
    bitrate: int = 5000000  # 5 Mbps default
    latency_ms: float = 0.0
    frame_drops: int = 0
    signal_strength: float = 100.0
    
    # Position and orientation
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    fov: float = 90.0
    
    # Production settings
    scene_name: str = ""
    preset_name: str = ""
    auto_switch_enabled: bool = False
    effects_enabled: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: float = field(default_factory=time.time)
    last_frame_at: float = 0.0
    last_error_at: float = 0.0
    error_message: str = ""
    
    # Analytics
    total_frames: int = 0
    total_errors: int = 0
    uptime_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CameraMetadata':
        """Create from dictionary"""
        return cls(**data)

class CameraSource:
    """Individual camera source with real-time monitoring"""
    
    def __init__(self, camera_id: str, metadata: CameraMetadata):
        self.id = camera_id
        self.metadata = metadata
        self.is_capturing = False
        self.capture_process: Optional[subprocess.Popen] = None
        self.frame_buffer: List[bytes] = []
        self.buffer_lock = threading.Lock()
        self.stats_lock = threading.Lock()
        
        # Performance monitoring
        self.frame_times: List[float] = []
        self.last_stats_update = time.time()
        self.connection_attempts = 0
        self.max_connection_attempts = 5

        # Voxel engine TCP connection
        self._voxel_reader = None
        self._voxel_writer = None
        
    async def connect(self) -> bool:
        """Establish connection to camera source"""
        try:
            logger.info(f"Connecting to camera {self.id} ({self.metadata.transport.value})")
            self.metadata.status = CameraStatus.CONNECTING
            self.metadata.error_message = ""
            self.connection_attempts += 1
            success = await self._establish_connection()
            
            if success:
                self.metadata.status = CameraStatus.ONLINE
                self.metadata.last_frame_at = time.time()
                logger.info(f"Camera {self.id} connected successfully")
                return True
            else:
                self.metadata.status = CameraStatus.ERROR
                if not self.metadata.error_message:
                    self.metadata.error_message = f"Failed to connect after {self.connection_attempts} attempts"
                logger.error("Failed to connect camera %s: %s", self.id, self.metadata.error_message)
                return False
                
        except Exception as e:
            self.metadata.status = CameraStatus.ERROR
            self.metadata.error_message = str(e)
            self.metadata.last_error_at = time.time()
            logger.error(f"Camera {self.id} connection error: {e}")
            return False
    
    async def _establish_connection(self) -> bool:
        """Transport-specific connection logic"""
        transport = self.metadata.transport
        
        if transport == CameraTransport.USB_WEBCAM:
            return await self._connect_usb_webcam()
        elif transport == CameraTransport.IP_CAMERA:
            return await self._connect_ip_camera()
        elif transport == CameraTransport.NDI_SOURCE:
            return await self._connect_ndi_source()
        elif transport == CameraTransport.OBS_VIRTUAL:
            return await self._connect_obs_virtual()
        elif transport == CameraTransport.VOXEL_ENGINE:
            return await self._connect_voxel_engine()
        elif transport == CameraTransport.SCREEN_CAPTURE:
            return await self._connect_screen_capture()
        elif transport == CameraTransport.FILE_PLAYBACK:
            return await self._connect_file_playback()
        else:
            logger.warning(f"Unsupported transport: {transport}")
            return False
    
    async def _connect_usb_webcam(self) -> bool:
        """Connect to USB webcam via V4L2/DirectShow"""
        try:
            device_path = self.metadata.connection_string or "/dev/video0"
            
            # Test connection with ffprobe
            cmd = [
                "ffprobe", 
                "-v", "quiet",
                "-f", "video4linux2" if "linux" in device_path else "dshow",
                "-i", device_path,
                "-show_streams",
                "-select_streams", "v:0"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd, 
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Parse video specs from ffprobe output
                self._parse_ffprobe_output(stdout.decode())
                return True
            else:
                self.metadata.error_message = stderr.decode()
                return False
                
        except Exception as e:
            self.metadata.error_message = f"USB webcam error: {e}"
            return False
    
    async def _connect_ip_camera(self) -> bool:
        """Connect to IP camera via RTSP/HTTP"""
        try:
            # Build RTSP URL
            if self.metadata.username and self.metadata.password:
                url = f"rtsp://{self.metadata.username}:{self.metadata.password}@{self.metadata.connection_string}"
            else:
                url = f"rtsp://{self.metadata.connection_string}"
            
            if self.metadata.port:
                url += f":{self.metadata.port}"
            
            # Test RTSP stream
            cmd = [
                "ffprobe",
                "-v", "quiet", 
                "-rtsp_transport", "tcp",
                "-i", url,
                "-show_streams",
                "-select_streams", "v:0"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self._parse_ffprobe_output(stdout.decode())
                return True
            else:
                self.metadata.error_message = stderr.decode()
                return False
                
        except Exception as e:
            self.metadata.error_message = f"IP camera error: {e}"
            return False
    
    async def _connect_ndi_source(self) -> bool:
        """NDI requires the native NDI SDK, which this runtime does not bundle."""
        self.metadata.error_message = "NDI capture backend is not installed"
        logger.warning("NDI source %s unavailable: %s", self.id, self.metadata.error_message)
        return False
    
    async def _connect_obs_virtual(self) -> bool:
        """Connect to OBS Virtual Camera"""
        try:
            # OBS Virtual Camera typically shows up as a standard webcam
            return await self._connect_usb_webcam()
        except Exception as e:
            self.metadata.error_message = f"OBS Virtual Camera error: {e}"
            return False
    
    async def _connect_voxel_engine(self) -> bool:
        """
        Connect to PubWorld voxel engine via TCP.
        Sends a HELLO handshake and waits for acknowledgement.
        Voxel engine listens on tcp://localhost:9010 by default.
        """
        import asyncio
        try:
            conn_str = self.metadata.connection_string or "tcp://localhost:9010"
            # Parse tcp://host:port
            if conn_str.startswith("tcp://"):
                conn_str = conn_str[6:]
            host, _, port_str = conn_str.rpartition(":")
            host = host or "127.0.0.1"
            port = int(port_str) if port_str.isdigit() else 9010

            # Attempt TCP connection with timeout
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=5.0
            )

            # Send HELLO handshake: {"type":"hello","client":"pubcast_camera"}
            import json
            hello = json.dumps({
                "type":   "hello",
                "client": "pubcast_camera",
                "width":  self.metadata.width,
                "height": self.metadata.height,
                "fps":    self.metadata.fps,
                "format": self.metadata.format,
            }).encode() + b'\n'

            writer.write(hello)
            await writer.drain()

            # Wait for ACK with timeout
            try:
                ack_line = await asyncio.wait_for(reader.readline(), timeout=3.0)
                ack = json.loads(ack_line.decode().strip())
                if ack.get("type") == "ack":
                    # Store connection for frame reads
                    self._voxel_reader = reader
                    self._voxel_writer = writer
                    logger.info(f"[VoxelCamera] Connected to {host}:{port}")
                    return True
                else:
                    logger.warning(f"[VoxelCamera] Unexpected ACK: {ack}")
                    writer.close()
                    return False
            except asyncio.TimeoutError:
                logger.warning(f"[VoxelCamera] No ACK from {host}:{port} — voxel engine is not ready")
                writer.close()
                self.metadata.error_message = f"No voxel-engine ACK from {host}:{port}"
                return False

        except asyncio.TimeoutError:
            self.metadata.error_message = "Voxel engine connection timed out"
            logger.warning("[VoxelCamera] %s", self.metadata.error_message)
            return False
        except ConnectionRefusedError:
            self.metadata.error_message = "Voxel engine connection refused"
            logger.warning("[VoxelCamera] %s", self.metadata.error_message)
            return False
        except Exception as e:
            self.metadata.error_message = f"Voxel engine connect error: {e}"
            logger.error(f"[VoxelCamera] Connect error: {e}")
            return False
    
    async def _connect_screen_capture(self) -> bool:
        """Connect to screen capture source"""
        try:
            # Screen capture via ffmpeg
            display = self.metadata.connection_string or ":0.0"
            
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-f", "x11grab",
                "-i", display,
                "-show_streams",
                "-select_streams", "v:0"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self._parse_ffprobe_output(stdout.decode())
                return True
            else:
                self.metadata.error_message = stderr.decode()
                return False
                
        except Exception as e:
            self.metadata.error_message = f"Screen capture error: {e}"
            return False
    
    async def _connect_file_playback(self) -> bool:
        """Connect to file playback source"""
        try:
            file_path = self.metadata.connection_string
            
            if not Path(file_path).exists():
                self.metadata.error_message = f"File not found: {file_path}"
                return False
            
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-i", file_path,
                "-show_streams",
                "-select_streams", "v:0"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self._parse_ffprobe_output(stdout.decode())
                return True
            else:
                self.metadata.error_message = stderr.decode()
                return False
                
        except Exception as e:
            self.metadata.error_message = f"File playback error: {e}"
            return False
    
    def _parse_ffprobe_output(self, output: str):
        """Parse ffprobe output to extract video specifications"""
        lines = output.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('width='):
                self.metadata.width = int(line.split('=')[1])
            elif line.startswith('height='):
                self.metadata.height = int(line.split('=')[1])
            elif line.startswith('r_frame_rate='):
                rate = line.split('=')[1]
                if '/' in rate:
                    num, den = rate.split('/')
                    self.metadata.fps = float(num) / float(den)
                else:
                    self.metadata.fps = float(rate)
    
    def _capture_input_args(self) -> Optional[List[str]]:
        """Return ffmpeg input arguments for transports with a real capture backend."""
        transport = self.metadata.transport
        source = self.metadata.connection_string
        if transport in {CameraTransport.USB_WEBCAM, CameraTransport.OBS_VIRTUAL}:
            device = source or "/dev/video0"
            input_format = "video4linux2" if device.startswith("/dev/") else "dshow"
            return ["-f", input_format, "-i", device]
        if transport == CameraTransport.IP_CAMERA:
            if self.metadata.username and self.metadata.password:
                url = f"rtsp://{self.metadata.username}:{self.metadata.password}@{source}"
            else:
                url = f"rtsp://{source}"
            if self.metadata.port:
                url += f":{self.metadata.port}"
            return ["-rtsp_transport", "tcp", "-i", url]
        if transport == CameraTransport.SCREEN_CAPTURE:
            return ["-f", "x11grab", "-i", source or ":0.0"]
        if transport == CameraTransport.FILE_PLAYBACK:
            return ["-re", "-i", source]
        return None

    async def start_capture(self) -> bool:
        """Start a real ffmpeg raw-frame capture pipeline for supported transports."""
        if self.is_capturing:
            return True
        input_args = self._capture_input_args()
        if input_args is None:
            self.metadata.status = CameraStatus.ERROR
            self.metadata.error_message = f"No frame capture backend for {self.metadata.transport.value}"
            logger.warning("Camera %s cannot capture: %s", self.id, self.metadata.error_message)
            return False
        try:
            self.is_capturing = True
            self.metadata.status = CameraStatus.ONLINE
            self.metadata.error_message = ""
            loop = asyncio.get_running_loop()
            self.capture_task = loop.run_in_executor(None, self._capture_frames, input_args)
            logger.info("Started real capture for camera %s", self.id)
            return True
        except Exception as exc:
            self.is_capturing = False
            self.metadata.status = CameraStatus.ERROR
            self.metadata.error_message = str(exc)
            logger.error("Failed to start capture for camera %s: %s", self.id, exc)
            return False

    def _capture_frames(self, input_args: List[str]) -> None:
        """Read RGB frames from ffmpeg; never synthesize frames as capture success."""
        frame_size = int(self.metadata.width) * int(self.metadata.height) * 3
        cmd = [
            "ffmpeg", "-loglevel", "error", *input_args,
            "-vf", f"scale={int(self.metadata.width)}:{int(self.metadata.height)}",
            "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1",
        ]
        try:
            self.capture_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=frame_size * 2
            )
            if self.capture_process.stdout is None:
                raise RuntimeError("ffmpeg capture stdout is unavailable")
            while self.is_capturing:
                started = time.time()
                frame_data = self.capture_process.stdout.read(frame_size)
                if len(frame_data) != frame_size:
                    stderr = b""
                    if self.capture_process.stderr is not None:
                        stderr = self.capture_process.stderr.read() or b""
                    raise RuntimeError(
                        "camera stream ended before a complete frame" +
                        (f": {stderr.decode(errors='replace').strip()}" if stderr else "")
                    )
                with self.buffer_lock:
                    self.frame_buffer.append(frame_data)
                    if len(self.frame_buffer) > 30:
                        self.frame_buffer.pop(0)
                elapsed = time.time() - started
                with self.stats_lock:
                    self.frame_times.append(elapsed)
                    if len(self.frame_times) > 100:
                        self.frame_times.pop(0)
                    self.metadata.last_frame_at = time.time()
                    self.metadata.total_frames += 1
        except Exception as exc:
            if self.is_capturing:
                self.metadata.status = CameraStatus.ERROR
                self.metadata.error_message = str(exc)
                self.metadata.last_error_at = time.time()
                self.metadata.total_errors += 1
                logger.error("Capture error for camera %s: %s", self.id, exc)
        finally:
            proc = self.capture_process
            self.capture_process = None
            if proc is not None:
                try:
                    if proc.poll() is None:
                        proc.terminate()
                        try:
                            proc.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            proc.kill()
                            proc.wait(timeout=2)
                finally:
                    # The capture worker owns these streams. Reap first, then
                    # release both pipes even if ffmpeg already exited itself.
                    for stream in (proc.stdout, proc.stderr, proc.stdin):
                        if stream is not None:
                            stream.close()
            self.is_capturing = False

    async def stop_capture(self):
        """Stop capturing frames and terminate the owned ffmpeg process."""
        self.is_capturing = False
        proc = self.capture_process
        if proc is not None and proc.poll() is None:
            proc.terminate()
        if hasattr(self, "capture_task"):
            try:
                await asyncio.wait_for(asyncio.shield(self.capture_task), timeout=3.0)
            except asyncio.TimeoutError:
                proc = self.capture_process
                if proc is not None and proc.poll() is None:
                    proc.kill()
        self.metadata.status = CameraStatus.OFFLINE
        logger.info("Stopped capture for camera %s", self.id)

    def get_latest_frame(self) -> Optional[bytes]:
        """Get the most recent frame"""
        with self.buffer_lock:
            return self.frame_buffer[-1] if self.frame_buffer else None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get camera performance statistics"""
        with self.stats_lock:
            avg_frame_time = sum(self.frame_times) / len(self.frame_times) if self.frame_times else 0
            
            return {
                "id": self.id,
                "name": self.metadata.name,
                "status": self.metadata.status.value,
                "role": self.metadata.role.value,
                "transport": self.metadata.transport.value,
                "resolution": f"{self.metadata.width}x{self.metadata.height}",
                "fps": self.metadata.fps,
                "total_frames": self.metadata.total_frames,
                "total_errors": self.metadata.total_errors,
                "frame_drops": self.metadata.frame_drops,
                "latency_ms": self.metadata.latency_ms,
                "signal_strength": self.metadata.signal_strength,
                "avg_frame_time_ms": avg_frame_time * 1000,
                "last_frame_ago": time.time() - self.metadata.last_frame_at if self.metadata.last_frame_at else 0,
                "uptime_seconds": self.metadata.uptime_seconds,
                "error_message": self.metadata.error_message
            }

class AdvancedCameraManager:
    """Advanced camera management with professional broadcast features"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("data/cameras.json")
        self.sources: Dict[str, CameraSource] = {}
        self.executor = ThreadPoolExecutor(max_workers=8)
        
        # Production state
        self.program_source: Optional[str] = None
        self.preview_source: Optional[str] = None
        self.recording_sources: List[str] = []
        
        # Monitoring
        self.monitoring_enabled = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Auto-switching
        self.auto_switching_enabled = False
        self.auto_switch_rules: Dict[str, Any] = {}
        
        # Load configuration
        self.load_configuration()
    
    def load_configuration(self):
        """Load camera configuration from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                
                for camera_data in config.get('cameras', []):
                    metadata = CameraMetadata.from_dict(camera_data)
                    camera = CameraSource(camera_data['id'], metadata)
                    self.sources[camera_data['id']] = camera
                
                # Load production state
                production_state = config.get('production_state', {})
                self.program_source = production_state.get('program_source')
                self.preview_source = production_state.get('preview_source')
                self.recording_sources = production_state.get('recording_sources', [])
                
                logger.info(f"Loaded configuration for {len(self.sources)} cameras")
            else:
                logger.info("No camera configuration found, starting with defaults")
                self._create_default_cameras()
                
        except Exception as e:
            logger.error(f"Failed to load camera configuration: {e}")
            self._create_default_cameras()
    
    def _create_default_cameras(self):
        """Create default camera setup"""
        default_cameras = [
            {
                "id": "cam1",
                "metadata": CameraMetadata(
                    name="Main Camera",
                    transport=CameraTransport.USB_WEBCAM,
                    connection_string="/dev/video0",
                    role=CameraRole.PROGRAM
                )
            },
            {
                "id": "cam2", 
                "metadata": CameraMetadata(
                    name="Secondary Camera",
                    transport=CameraTransport.USB_WEBCAM,
                    connection_string="/dev/video1",
                    role=CameraRole.PREVIEW
                )
            },
            {
                "id": "voxel",
                "metadata": CameraMetadata(
                    name="Voxel Engine",
                    transport=CameraTransport.VOXEL_ENGINE,
                    connection_string="tcp://localhost:9001",
                    role=CameraRole.STANDBY,
                    width=1920,
                    height=1080,
                    fps=60.0
                )
            },
            {
                "id": "screen",
                "metadata": CameraMetadata(
                    name="Screen Capture", 
                    transport=CameraTransport.SCREEN_CAPTURE,
                    connection_string=":0.0",
                    role=CameraRole.STANDBY
                )
            }
        ]
        
        for camera_config in default_cameras:
            camera = CameraSource(camera_config["id"], camera_config["metadata"])
            self.sources[camera_config["id"]] = camera
        
        # Set initial program and preview
        if "cam1" in self.sources:
            self.program_source = "cam1"
            self.sources["cam1"].metadata.role = CameraRole.PROGRAM
            
        if "cam2" in self.sources:
            self.preview_source = "cam2"
            self.sources["cam2"].metadata.role = CameraRole.PREVIEW
    
    def save_configuration(self):
        """Save current camera configuration"""
        try:
            config = {
                "cameras": [
                    {
                        "id": camera_id,
                        **source.metadata.to_dict()
                    }
                    for camera_id, source in self.sources.items()
                ],
                "production_state": {
                    "program_source": self.program_source,
                    "preview_source": self.preview_source,
                    "recording_sources": self.recording_sources
                },
                "auto_switch_rules": self.auto_switch_rules,
                "last_updated": time.time()
            }
            
            write_json(self.config_path, config)
                
            logger.info("Camera configuration saved")
            
        except Exception as e:
            logger.error(f"Failed to save camera configuration: {e}")
    
    async def initialize_all_cameras(self) -> Dict[str, bool]:
        """Initialize all configured cameras"""
        results = {}
        
        # Connect all cameras in parallel
        connection_tasks = [
            self.connect_camera(camera_id) 
            for camera_id in self.sources.keys()
        ]
        
        connection_results = await asyncio.gather(*connection_tasks, return_exceptions=True)
        
        for camera_id, result in zip(self.sources.keys(), connection_results):
            if isinstance(result, Exception):
                results[camera_id] = False
                logger.error(f"Failed to initialize camera {camera_id}: {result}")
            else:
                results[camera_id] = result
        
        # Start monitoring
        await self.start_monitoring()
        
        logger.info(f"Camera initialization complete: {sum(results.values())}/{len(results)} cameras online")
        return results
    
    async def connect_camera(self, camera_id: str) -> bool:
        """Connect a specific camera"""
        if camera_id not in self.sources:
            logger.error(f"Camera {camera_id} not found")
            return False
        
        camera = self.sources[camera_id]
        success = await camera.connect()
        
        if success:
            # Start capturing if this is program/preview camera
            if camera_id in [self.program_source, self.preview_source]:
                await camera.start_capture()
        
        return success
    
    async def disconnect_camera(self, camera_id: str):
        """Disconnect a specific camera"""
        if camera_id in self.sources:
            await self.sources[camera_id].stop_capture()
            logger.info(f"Disconnected camera {camera_id}")
    
    async def cut_to_camera(self, camera_id: str) -> bool:
        """Perform immediate cut to specified camera"""
        if camera_id not in self.sources:
            logger.error(f"Camera {camera_id} not found")
            return False
        
        camera = self.sources[camera_id]
        if camera.metadata.status != CameraStatus.ONLINE:
            logger.error(f"Camera {camera_id} is not online")
            return False
        
        # Update roles
        if self.program_source:
            self.sources[self.program_source].metadata.role = CameraRole.STANDBY
        
        camera.metadata.role = CameraRole.PROGRAM
        self.program_source = camera_id
        
        # Ensure camera is capturing
        if not camera.is_capturing:
            await camera.start_capture()
        
        logger.info(f"Cut to camera {camera_id}")
        
        # Save state
        self.save_configuration()
        
        return True
    
    async def set_preview_camera(self, camera_id: str) -> bool:
        """Set preview camera for next transition"""
        if camera_id not in self.sources:
            logger.error(f"Camera {camera_id} not found")
            return False
        
        camera = self.sources[camera_id]
        if camera.metadata.status != CameraStatus.ONLINE:
            logger.error(f"Camera {camera_id} is not online")
            return False
        
        # Update roles
        if self.preview_source:
            self.sources[self.preview_source].metadata.role = CameraRole.STANDBY
        
        camera.metadata.role = CameraRole.PREVIEW
        self.preview_source = camera_id
        
        # Ensure camera is capturing
        if not camera.is_capturing:
            await camera.start_capture()
        
        logger.info(f"Set preview camera to {camera_id}")
        
        # Save state
        self.save_configuration()
        
        return True
    
    async def auto_transition(self, duration_seconds: float = 1.0) -> bool:
        """Perform auto transition from program to preview"""
        if not self.preview_source:
            logger.error("No preview camera set for transition")
            return False
        
        if not self.program_source:
            logger.error("No program camera set")
            return False
        
        preview_camera = self.sources[self.preview_source]
        if preview_camera.metadata.status != CameraStatus.ONLINE:
            logger.error(f"Preview camera {self.preview_source} is not online")
            return False
        
        # Camera-state transition only. Program video mixing is owned elsewhere.
        logger.info(f"Scheduling {duration_seconds}s source-state transition from {self.program_source} to {self.preview_source}")
        await asyncio.sleep(duration_seconds)
        
        # Swap program and preview
        old_program = self.program_source
        new_program = self.preview_source
        
        # Update roles
        self.sources[old_program].metadata.role = CameraRole.STANDBY
        self.sources[new_program].metadata.role = CameraRole.PROGRAM
        
        self.program_source = new_program
        self.preview_source = old_program
        self.sources[old_program].metadata.role = CameraRole.PREVIEW
        
        logger.info(f"Transition complete: {new_program} is now program")
        
        # Save state
        self.save_configuration()
        
        return True
    
    def add_camera(self, camera_id: str, metadata: CameraMetadata) -> bool:
        """Add a new camera source"""
        if camera_id in self.sources:
            logger.warning(f"Camera {camera_id} already exists")
            return False
        
        camera = CameraSource(camera_id, metadata)
        self.sources[camera_id] = camera
        
        logger.info(f"Added camera {camera_id}: {metadata.name}")
        
        # Save configuration
        self.save_configuration()
        
        return True
    
    def remove_camera(self, camera_id: str) -> bool:
        """Remove a camera source"""
        if camera_id not in self.sources:
            logger.warning(f"Camera {camera_id} not found")
            return False
        
        # Disconnect if connected
        _t = asyncio.create_task(self.disconnect_camera(camera_id))
        _t.add_done_callback(lambda t: t.exception() if not t.cancelled() else None)
        
        # Update production state
        if self.program_source == camera_id:
            self.program_source = None
        if self.preview_source == camera_id:
            self.preview_source = None
        if camera_id in self.recording_sources:
            self.recording_sources.remove(camera_id)
        
        del self.sources[camera_id]
        
        logger.info(f"Removed camera {camera_id}")
        
        # Save configuration
        self.save_configuration()
        
        return True
    
    async def start_monitoring(self):
        """Start camera monitoring task"""
        if not self.monitoring_enabled:
            self.monitoring_enabled = True
            self.monitoring_task = asyncio.create_task(self._monitor_cameras())
            logger.info("Camera monitoring started")
    
    async def stop_monitoring(self):
        """Stop camera monitoring"""
        if self.monitoring_enabled:
            self.monitoring_enabled = False
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            logger.info("Camera monitoring stopped")
    
    async def _monitor_cameras(self):
        """Monitor camera health and performance"""
        while self.monitoring_enabled:
            try:
                current_time = time.time()
                
                for camera_id, camera in self.sources.items():
                    if camera.metadata.status == CameraStatus.ONLINE:
                        # Check for frame timeout
                        if camera.metadata.last_frame_at > 0:
                            frame_age = current_time - camera.metadata.last_frame_at
                            if frame_age > 5.0:  # 5 second timeout
                                camera.metadata.status = CameraStatus.ERROR
                                camera.metadata.error_message = "Frame timeout"
                                logger.warning(f"Camera {camera_id} frame timeout")
                        
                        # Update uptime
                        camera.metadata.uptime_seconds += 1.0
                        
                        # Calculate latency
                        with camera.stats_lock:
                            if camera.frame_times:
                                avg_frame_time = sum(camera.frame_times) / len(camera.frame_times)
                                camera.metadata.latency_ms = avg_frame_time * 1000
                
                # Auto-switching logic
                if self.auto_switching_enabled:
                    await self._check_auto_switch_rules()
                
                await asyncio.sleep(1.0)  # Monitor every second
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Camera monitoring error: {e}")
                await asyncio.sleep(1.0)
    
    async def _check_auto_switch_rules(self):
        """
        Check and apply auto-switching rules.
        Reads Switchblade priority vector if available.
        Locks camera during identity moments. Enables auto-switch otherwise.
        """
        # If Switchblade has issued a priority vector, read it
        vector = getattr(self, '_switchblade_vector', None)

        if vector is not None:
            # Identity moment: lock program camera — do not auto-switch
            if getattr(vector, 'identity_moment', False):
                return  # Hard lock — no switch during identity moments

            # If E4 is assisting, don't switch cameras — disrupts render budget
            if getattr(vector, 'e4_assist', False):
                return

        # Normal auto-switch logic: switch if program camera has errors
        if self.program_source and self.program_source in self.sources:
            program_cam = self.sources[self.program_source]
            if program_cam.metadata.status.value == 'error':
                # Find best available backup
                for cam_id, cam in self.sources.items():
                    if (cam_id != self.program_source and
                        cam.metadata.status.value == 'online' and
                        cam.metadata.role.value in ('preview', 'standby')):
                        logger.info(f"[CameraManager] Auto-switch: {self.program_source} → {cam_id} (program cam error)")
                        await self.cut_to_camera(cam_id)
                        break
    
    def get_camera_stats(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific camera"""
        if camera_id in self.sources:
            return self.sources[camera_id].get_stats()
        return None
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for all cameras"""
        stats = {
            "cameras": {},
            "production_state": {
                "program_source": self.program_source,
                "preview_source": self.preview_source,
                "recording_sources": self.recording_sources
            },
            "system": {
                "total_cameras": len(self.sources),
                "online_cameras": len([c for c in self.sources.values() if c.metadata.status == CameraStatus.ONLINE]),
                "error_cameras": len([c for c in self.sources.values() if c.metadata.status == CameraStatus.ERROR]),
                "monitoring_enabled": self.monitoring_enabled,
                "auto_switching_enabled": self.auto_switching_enabled
            }
        }
        
        for camera_id, camera in self.sources.items():
            stats["cameras"][camera_id] = camera.get_stats()
        
        return stats
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of camera system status"""
        online = len([c for c in self.sources.values() if c.metadata.status == CameraStatus.ONLINE])
        total = len(self.sources)
        
        return {
            "total_cameras": total,
            "online_cameras": online,
            "offline_cameras": total - online,
            "program_camera": self.program_source,
            "preview_camera": self.preview_source,
            "health_status": "healthy" if online >= total * 0.8 else "degraded" if online > 0 else "critical"
        }
    
    async def shutdown(self):
        """Shutdown camera manager and all sources"""
        logger.info("Shutting down camera manager")
        
        # Stop monitoring
        await self.stop_monitoring()
        
        # Disconnect all cameras
        disconnect_tasks = [
            self.disconnect_camera(camera_id) 
            for camera_id in self.sources.keys()
        ]
        
        await asyncio.gather(*disconnect_tasks, return_exceptions=True)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        # Save final state
        self.save_configuration()
        
        logger.info("Camera manager shutdown complete")

# Factory functions for common setups

def create_default_cameras() -> AdvancedCameraManager:
    """Create camera manager with default setup"""
    manager = AdvancedCameraManager()
    return manager

def create_voxel_camera() -> CameraMetadata:
    """Create metadata for voxel engine camera"""
    return CameraMetadata(
        name="PubCast Voxel Engine",
        transport=CameraTransport.VOXEL_ENGINE,
        connection_string="tcp://localhost:9001",
        width=1920,
        height=1080,
        fps=60.0,
        format="rgba",
        scene_name="default"
    )

def create_usb_camera(device_path: str = "/dev/video0", name: str = "USB Camera") -> CameraMetadata:
    """Create metadata for USB webcam"""
    return CameraMetadata(
        name=name,
        transport=CameraTransport.USB_WEBCAM,
        connection_string=device_path,
        width=1920,
        height=1080,
        fps=30.0,
        format="h264"
    )

def create_ip_camera(host: str, username: str = "", password: str = "", port: int = 554, name: str = "IP Camera") -> CameraMetadata:
    """Create metadata for IP camera"""
    return CameraMetadata(
        name=name,
        transport=CameraTransport.IP_CAMERA,
        connection_string=host,
        username=username,
        password=password,
        port=port,
        width=1920,
        height=1080,
        fps=30.0,
        format="h264"
    )

# Example usage
if __name__ == "__main__":
    async def main():
        # Create camera manager
        camera_manager = create_default_cameras()
        
        # Add a voxel engine camera
        voxel_meta = create_voxel_camera()
        camera_manager.add_camera("voxel_engine", voxel_meta)
        
        # Initialize all cameras
        results = await camera_manager.initialize_all_cameras()
        
        print("Camera initialization results:")
        for camera_id, success in results.items():
            print(f"  {camera_id}: {'✓' if success else '✗'}")
        
        # Get system stats
        stats = camera_manager.get_all_stats()
        print(f"\\nSystem status: {stats['system']}")
        
        # Exercise source switching in the standalone module demo
        await asyncio.sleep(2)
        
        if camera_manager.sources:
            camera_id = list(camera_manager.sources.keys())[0]
            print(f"\\nCutting to camera: {camera_id}")
            await camera_manager.cut_to_camera(camera_id)
        
        await asyncio.sleep(3)
        
        # Cleanup
        await camera_manager.shutdown()

    asyncio.run(main())
````

## tests/test_camera_manager.py

SHA-256: `4a3d950ba03243e82b669dda50b99a24cb0803e56ffed0ec72006266989b2981`

````python
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
    bridge._loop = asyncio.get_running_loop()

    event = CameraSwitchEvent("program", "cam_b", "cam_a", time.time(), "evt-1")
    bridge._on_event(event)
    bridge._on_event(event)

    await asyncio.sleep(0)

    assert len(hub.messages) == 1
    assert hub.messages[0]["payload"]["event_id"] == "evt-1"


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
````

## tests/test_camera_capture_cleanup.py

SHA-256: `dd3075b265d450c90fd6817d305bd131b1dd309fe02a1f09185eac2ce84bd960`

````python
import io
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

from modules.cameras_advanced import CameraMetadata, CameraSource, CameraTransport


def make_camera():
    camera = CameraSource("cleanup", CameraMetadata(name="cleanup",
        transport=CameraTransport.FILE_PLAYBACK, connection_string="unused", width=1, height=1))
    camera.is_capturing = True
    return camera


def test_capture_closes_owned_pipes_even_when_process_already_exited(monkeypatch):
    process = SimpleNamespace(stdout=io.BytesIO(), stderr=io.BytesIO(), stdin=None,
        poll=Mock(return_value=0), terminate=Mock(), wait=Mock(), kill=Mock())
    monkeypatch.setattr(subprocess, "Popen", Mock(return_value=process))
    camera = make_camera()
    camera._capture_frames(["-i", "unused"])
    assert process.stdout.closed and process.stderr.closed
    assert camera.capture_process is None
    assert not camera.is_capturing


def test_capture_reaps_forced_kill_and_closes_pipes(monkeypatch):
    process = SimpleNamespace(stdout=io.BytesIO(), stderr=io.BytesIO(), stdin=None,
        poll=Mock(return_value=None), terminate=Mock(),
        wait=Mock(side_effect=[subprocess.TimeoutExpired("ffmpeg", 2), 0]), kill=Mock())
    monkeypatch.setattr(subprocess, "Popen", Mock(return_value=process))
    make_camera()._capture_frames(["-i", "unused"])
    process.kill.assert_called_once()
    assert process.wait.call_count == 2
    assert process.stdout.closed and process.stderr.closed
````

## main.py (original application lifecycle integration)

SHA-256: `d334d29cbef585843c3c27ffff8fa648666ea82c22bb7eb4f1fe5b9ac9a3f832`

````python
"""
main.py — PubCast AI v5.5 — Production Entry Point
==============================================================================
Boots all systems in dependency order, wires every integration hook,
and starts the FastAPI server.

Boot Sequence (12 steps + sub-steps):
  1.   Hub (message router + history)
  2.   RoomManager
  2b.  PerformanceManager (profile policy — optional)
  2c.  ChoreographyController (animation tick — optional)
  2d.  LightingEngine (preset management — optional)
  3.   InferenceManager (Ollama Studio + GGUF Architect dual-mind)
  4.   CricketKeeper (per-character SQLite memory — optional)
  5.   BotManager (AI co-hosts: Pete, Sir Purfluous, Jeremy Cricket)
  6.   Cameras + RecordingService
  7.   GovernanceEngine (bans, mute, consent, waiting room)
  8.   BYOK Manager (user-supplied API keys — optional)
  9.   ThinkingContext (Jeremy conductor — optional)
  10.  EtherealAvatarManager (57-joint neon avatars — optional)
  11.  EVO Protocol (Switchblade + VDI + E-Pete Sacred Chain — optional)
  12.  Vault (OS-level file protection — optional)
  12b. Doctor (environment verifier — optional)

Run:
  python main.py
  uvicorn main:app --host 0.0.0.0 --port 8000

Rear View Foresight LLC — Feic Mo Chro— — 2026
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

# — Core modules (always present) —
from modules.appconfig import settings
from modules.hub import Hub
from modules.bots import BotManager
from modules.rooms import RoomManager
from modules.inference import InferenceManager
from modules.models import BotConfig, BotProvider, ProductionState
from modules.cameras import CameraManager, create_default_cameras
from modules.recording import RecordingService, create_recording_service
from modules.blackbox_runtime import BlackBoxRuntimeWitness, create_blackbox_witness
from modules.blackbox_routes import create_blackbox_router
from modules.production_routes import create_production_router
from modules.program_audio import ProgramAudioState, apply_audio_event
from modules.governance import GovernanceEngine
from modules.governance_routes import create_governance_router
from modules.avatar_studio_bridge import AvatarStudioBridge, create_avatar_studio_router
from modules.pubworld_hotspots import create_hotspot_router
from modules.avatar import load_avatar, save_avatar, list_presets as list_avatar_presets
from modules.character_cast import list_cast_characters, get_cast_character
from modules.feature_flags import alex_little_one_enabled
from modules.persistence import read_json, write_json, sanitize_filename, storage_key, unique_child_path

# — NEW: v5.5 Integration modules —
from modules import timeline_routes
from modules import structured_log_routes
from modules import recording_pipeline_routes
from modules import audio_devices as audio_devices_module
from modules import mic_routes as mic_routes_module
from modules import governance_waiting_room
try:
    from modules import bubble_routes as bubble_routes_module
    from modules.bubble_jeremy_adapter import BubbleJeremyAdapter
    _HAS_BUBBLE_STACK = True
except ImportError:
    bubble_routes_module = None
    BubbleJeremyAdapter = None
    _HAS_BUBBLE_STACK = False
from modules import hotspot_system
from modules.structured_log import init_production_log, emit, get_production_log
from modules.recording_pipeline import ServerRecordingSession
from modules.save_metadata import attach_save_metadata
from modules import dressing_room_security as dr_security
from modules import session_runtime
from modules import credits_export
from modules import memory_engine
from modules import memory_routes, character_routes, story_routes, pete_enhanced_routes, personal_ai_memory_api
from modules import character_profiles, pubcast_story_bible
from modules.alex_core import AlexCore
from modules.alex_jeremy_bridge import AlexJeremyBridge
from modules.pub_manager_authority import PubManagerAuthorityStore, create_pub_manager_authority_router, create_pub_manager_control_router
from modules.session_resurrector import SessionResurrector
from modules.memory_ingestor import MemoryIngestor
from modules.universal_memory_system import UniversalMemorySystem
from modules.system_memory import SystemMemory
from modules import alex_routes, auth_routes, userdb, auth as auth_module
from modules.route_security import auth_enforced, current_identity, bound_actor, require_role
from modules.timeline_routes import register_timeline_handler
from modules.timeline import EventType

# — Optional modules — every import guarded; server boots regardless —
_HAS_CRICKET          = False
_HAS_THINKING_CONTEXT = False
_HAS_ETHEREAL         = False
_HAS_EVO              = False
_HAS_VAULT            = False
_HAS_BYOK             = False
_HAS_PERFORMANCE      = False
_HAS_CHOREO           = False
_HAS_LIGHTING         = False
_HAS_DOCTOR           = False

try:
    from modules.jeremy_cricket import CricketKeeper
    _HAS_CRICKET = True
except ImportError:
    CricketKeeper = None

try:
    from thinking_context import mount as tc_mount, CharacterProfile
    _HAS_THINKING_CONTEXT = True
except ImportError:
    tc_mount         = None
    CharacterProfile = None

try:
    from modules.ethereal_avatars import (
        EtherealAvatarManager, create_ethereal_router,
        handle_ethereal_ws_message, ETHEREAL_TYPES,
    )
    _HAS_ETHEREAL = True
except ImportError:
    EtherealAvatarManager      = None
    handle_ethereal_ws_message = None
    ETHEREAL_TYPES             = set()

try:
    from modules.evo import _EVO_CORE_AVAILABLE, EVOOrchestrator
    _HAS_EVO = _EVO_CORE_AVAILABLE
except ImportError:
    _HAS_EVO        = False
    EVOOrchestrator = None

try:
    from modules.byok_manager import BYOKManager
    from modules.byok_routes import mount_byok_routes as create_byok_router
    _HAS_BYOK = True
except ImportError:
    BYOKManager = None

try:
    from modules.pubcast_vault import PubCastVault, create_vault_router
    _HAS_VAULT = True
except ImportError:
    PubCastVault = None

try:
    from modules.performance_manager import PerformanceManager, init_performance_manager
    _HAS_PERFORMANCE = True
except ImportError:
    PerformanceManager = None

try:
    from modules.choreography_controller import ChoreoController as ChoreographyController
    _HAS_CHOREO = True
except ImportError:
    ChoreographyController = None

try:
    from modules.lighting_engine import LightingEngine, LightingHubPatch, list_presets as list_lighting_presets
    _HAS_LIGHTING = True
except ImportError:
    LightingEngine         = None
    LightingHubPatch       = None
    list_lighting_presets  = None

try:
    from modules.doctor import run_doctor as _run_doctor_fn, run_launch_gate as _run_launch_gate_fn
    _HAS_DOCTOR = True
except ImportError:
    _run_doctor_fn = None
    _run_launch_gate_fn = None

# — New subsystem imports (all guarded) —
_HAS_PUBWORLD_ROUTER   = False
_HAS_PUBWORLD_SCENES   = False
_HAS_PUBWORLD_BLOCKS   = False
_HAS_SURFACES          = False
_HAS_PROJECTS          = False
_HAS_AVATAR_ASSETS     = False
_HAS_SCULPTOR          = False
_HAS_STUDIO_CONTROL    = False
_HAS_MOCAP             = False
_HAS_UNITY_BRIDGE      = False
_HAS_VOXEL             = False
_HAS_BRIDGE            = False
_HAS_ORCHESTRATOR      = False
_HAS_VISUAL_PATCH_BRIDGE = False

try:
    from modules.pubworld_router import router as _pubworld_router, push_production_state_to_pubworld, configure_pubworld_state_provider
    _HAS_PUBWORLD_ROUTER = True
except ImportError:
    _pubworld_router = None
    push_production_state_to_pubworld = None
    configure_pubworld_state_provider = None

try:
    from modules.pubworld import list_scenes, create_scene, get_scene
    _HAS_PUBWORLD_SCENES = True
except ImportError:
    list_scenes = create_scene = get_scene = None

try:
    from modules.pubworld_blocks import (
        Block,
        Prop,
        Prototype,
        Tracker,
        create_prop,
        generate_from_prompt as pubworld_generate_from_prompt,
        list_builder_presets,
        list_prototypes,
        list_props,
        recognize_prop,
        save_builder_preset,
        save_prototype,
    )
    _HAS_PUBWORLD_BLOCKS = True
except ImportError:
    Block = Prop = Prototype = Tracker = None
    create_prop = pubworld_generate_from_prompt = None
    list_builder_presets = list_props = save_builder_preset = None
    list_prototypes = save_prototype = recognize_prop = None

try:
    from modules.irm import IRMController
    _HAS_IRM = True
except ImportError:
    IRMController = None
    _HAS_IRM = False

try:
    from modules.avatar_performer import AvatarPerformerManager
    _HAS_AVATAR_PERFORMER = True
except ImportError:
    AvatarPerformerManager = None
    _HAS_AVATAR_PERFORMER = False

try:
    from modules.credentials import CredentialStore
    _HAS_CRED_STORE = True
except ImportError:
    CredentialStore = None
    _HAS_CRED_STORE = False

try:
    from modules.surfaces import Surface, SurfaceManager
    _HAS_SURFACES = True
except ImportError:
    SurfaceManager = None

try:
    from modules.projects import list_autosaves, save_autosave_snapshot
    _HAS_PROJECTS = True
except ImportError:
    list_autosaves = save_autosave_snapshot = None

try:
    from modules.avatar_assets import AvatarManifest, AssetPack
    _HAS_AVATAR_ASSETS = True
except ImportError:
    pass

try:
    from modules.sculptor import Sculptor
    _HAS_SCULPTOR = True
except ImportError:
    Sculptor = None

try:
    from modules.studio_control import StudioControl, StudioState
    from modules.studio_websocket import StudioWebSocketHandler
    _HAS_STUDIO_CONTROL = True
except ImportError:
    StudioControl = None
    StudioWebSocketHandler = None

try:
    from modules.mocap_integration import MocapStreamManager as MocapIntegration
    _HAS_MOCAP = True
except ImportError:
    MocapIntegration = None

try:
    from modules.unity_bridge import UnityBridge
    _HAS_UNITY_BRIDGE = True
except ImportError:
    UnityBridge = None

try:
    from modules.voxel_asset_manager import VoxelAssetManager
    from modules.voxel_llm_adapter import generate_with_cloud as voxel_generate
    from modules.voxel_studio_integration import VoxelStudioIntegration
    from modules.voxel_set_contract import save_voxel_set
    _HAS_VOXEL = True
except ImportError:
    VoxelAssetManager = None
    voxel_generate = None
    VoxelStudioIntegration = None
    save_voxel_set = None

try:
    from modules.visual_patch_approval_bridge import VisualPatchApprovalError, submit_approved_visual_patch
    _HAS_VISUAL_PATCH_BRIDGE = True
except ImportError:
    VisualPatchApprovalError = ValueError
    submit_approved_visual_patch = None

try:
    from modules.pub_manager_recovery import approval_required_actions, build_snapshot, issue_report, safe_actions, suggest_recovery, validate_action
    _HAS_PUB_MANAGER_RECOVERY = True
except ImportError:
    approval_required_actions = build_snapshot = issue_report = safe_actions = suggest_recovery = validate_action = None
    _HAS_PUB_MANAGER_RECOVERY = False

try:
    from modules.bridge_bulletproof import VoxelBridge
    _HAS_BRIDGE = True
except ImportError:
    try:
        from modules.bridge import VoxelBridge
        _HAS_BRIDGE = True
    except ImportError:
        VoxelBridge = None

try:
    from modules.pete_enhanced import PeteEnhanced
    _HAS_PETE_ENHANCED = True
except ImportError:
    PeteEnhanced = None
    _HAS_PETE_ENHANCED = False

try:
    from modules.twin_engine_service import mount_twin_engine, install_twin_engine_routes
    _HAS_TWIN_ENGINE = True
except ImportError:
    mount_twin_engine = install_twin_engine_routes = None
    _HAS_TWIN_ENGINE = False

try:
    from modules.camera_boxer import CameraBoxer, install_camera_boxer_routes
    _HAS_CAMERA_BOXER = True
except ImportError:
    CameraBoxer = install_camera_boxer_routes = None
    _HAS_CAMERA_BOXER = False

try:
    from modules.stt_engine import STTEngine
    _HAS_STT = True
except ImportError:
    STTEngine = None
    _HAS_STT = False

try:
    from modules.tts_engine import TTSEngine
    _HAS_TTS_ENGINE = True
except ImportError:
    TTSEngine = None
    _HAS_TTS_ENGINE = False

try:
    from modules.chat_rooms import (
        create_chat_router, install_chat_websocket,
        VALID_ROLES as CHAT_VALID_ROLES,
    )
    _HAS_CHAT_ROOMS = True
except ImportError:
    create_chat_router = install_chat_websocket = None
    CHAT_VALID_ROLES = set()
    _HAS_CHAT_ROOMS = False

try:
    from modules.animation_authority import AnimationAuthority
    _HAS_ANIM_AUTHORITY = True
except ImportError:
    AnimationAuthority = None
    _HAS_ANIM_AUTHORITY = False

try:
    from modules.cameras_advanced import AdvancedCameraManager
    _HAS_CAMERAS_ADVANCED = True
except ImportError:
    AdvancedCameraManager = None
    _HAS_CAMERAS_ADVANCED = False

try:
    from modules.room_conductor import create_room_conductor, RoomConductorConfig
    _HAS_ROOM_CONDUCTOR = True
except ImportError:
    create_room_conductor = RoomConductorConfig = None
    _HAS_ROOM_CONDUCTOR = False

try:
    from modules.key_recovery import VaultKeyBackup as KeyRecovery
    _HAS_KEY_RECOVERY = True
except ImportError:
    KeyRecovery = None
    _HAS_KEY_RECOVERY = False

try:
    from modules.orchestrator import ConversationOrchestrator
    _HAS_ORCHESTRATOR = True
except ImportError:
    ConversationOrchestrator = None

# — modules.wired — EQ + wired orchestration (guarded) —
_HAS_WIRED = False
_HAS_EQ    = False

try:
    from modules.wired.wired_orchestrator import WiredOrchestrator
    _HAS_WIRED = True
except ImportError:
    WiredOrchestrator = None

try:
    from modules.wired.eq_integration_layer import EQOrchestrator, EQOrchestratorBridge
    _HAS_EQ = True
except ImportError:
    EQOrchestrator = None
    EQOrchestratorBridge = None

try:
    from modules.wired.pubcast_adapter import PubCastAdapter
    _HAS_ADAPTER = True
except ImportError:
    PubCastAdapter = None
    _HAS_ADAPTER = False

# — Logging —
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("pubcast")

# — Paths —
DATA_DIR   = Path(settings.data_dir)
STATIC_DIR = Path(settings.static_dir)
ASSETS_DIR = Path(settings.assets_dir)

for _d in [
    DATA_DIR, DATA_DIR / "logs", DATA_DIR / "users", DATA_DIR / "bots",
    DATA_DIR / "global", DATA_DIR / "jeremy", DATA_DIR / "ethereal",
    DATA_DIR / "vault", DATA_DIR / "governance", DATA_DIR / "recordings",
    DATA_DIR / "exports", DATA_DIR / "imports", DATA_DIR / "byok",
    DATA_DIR / "evo", DATA_DIR / "pubworld" / "scenes",
    DATA_DIR / "projects", DATA_DIR / "sculptures",
    DATA_DIR / "timelines", DATA_DIR / "hotspots", DATA_DIR / "environments",
    STATIC_DIR, ASSETS_DIR,
]:
    _d.mkdir(parents=True, exist_ok=True)

# The doctor's launch gate requires these (data/secure is git-ignored, so a clean
# checkout lacks it); create them here so the app never fails its own gate.
from modules.doctor import ensure_runtime_dirs as _ensure_runtime_dirs
_ensure_runtime_dirs(DATA_DIR)

# — Global refs —
hub:               Optional[Hub]               = None
bot_manager:       Optional[BotManager]        = None
room_manager:      Optional[RoomManager]       = None
inference:         Optional[InferenceManager]  = None
cameras:           Optional[CameraManager]     = None
recording:         Optional[RecordingService]  = None
blackbox_witness:  Optional[BlackBoxRuntimeWitness] = None
governance:        Optional[GovernanceEngine]  = None
cricket_keeper:    Any = None
system_memory:     Any = None
irm_controller:    Any = None
performer_manager: Any = None
cred_store:        Any = None
ethereal_mgr:      Any = None
avatar_studio:     Any = None
evo_orchestrator:  Any = None
vault:             Any = None
byok_mgr:          Any = None
performance_manager: Any = None
choreo_controller: Any = None
stt_engine:        Any = None
tts_engine:        Any = None
lighting_engine:   Any = None
lighting_hub_patch: Any = None
# — New subsystem globals —
surface_manager:        Any = None
studio_control:         Any = None
studio_ws_handler:      Any = None
voxel_asset_manager:    Any = None
voxel_studio:           Any = None
voxel_bridge:           Any = None
pete_enhanced:          Any = None
unity_bridge:           Any = None
mocap:                  Any = None
conv_orchestrator:      Any = None
# — NEW: v5.5 Integration globals —
production_log:         Any = None
timeline_player:        Any = None
waiting_room_manager:   Any = None
hotspot_manager:        Any = None
pipeline_sessions:      Dict[str, Any] = {}
universal_memory_system: Any = None
memory_ingestor:         Any = None
alex_core_instance:     Any = None
alex_bridge:            Any = None
pub_manager_authority:  Any = None
program_audio_state:     Any = None
bubble_jeremy_adapter: Any = None


async def _execute_pub_manager_engineering_action(row: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the small, explicit set of deterministic engineering actions.

    This resolver reads live globals at execution time, so Pub Manager can be
    constructed early while the target subsystems finish booting later.  No
    arbitrary command, file deletion, shell execution, publishing, or spending
    action is exposed here.
    """
    action = str(row.get("action") or "")
    if action == "emergency_save":
        if studio_control is not None and hasattr(studio_control, "emergency_save"):
            result = studio_control.emergency_save()
            if asyncio.iscoroutine(result):
                result = await result
            return {"executor": "studio_control", "result": result}
        # Honest fallback: preserve a bounded runtime snapshot rather than
        # claiming the full studio save ran when StudioControl is unavailable.
        snapshot_path = DATA_DIR / "emergency_saves" / f"pub_manager_{int(time.time() * 1000)}.json"
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "ts": time.time(),
            "kind": "pub_manager_runtime_snapshot",
            "reason": row.get("reason", ""),
            "request_id": row.get("request_id"),
            "systems": {
                "hub": hub is not None,
                "inference": inference.status() if inference is not None else None,
                "recording": recording is not None,
                "studio_control": studio_control is not None,
                "performance_profile": performance_manager.active_profile if performance_manager is not None else None,
            },
        }
        write_json(snapshot_path, payload)
        return {"executor": "fallback_runtime_snapshot", "path": str(snapshot_path)}

    if action == "reduce_performance":
        if performance_manager is None:
            raise RuntimeError("PerformanceManager is unavailable")
        return {"executor": "performance_manager", **performance_manager.set_profile("low")}

    if action == "stop_recording":
        if recording is None:
            raise RuntimeError("RecordingService is unavailable")
        sessions = recording.list_sessions() if hasattr(recording, "list_sessions") else []
        active = []
        for item in sessions or []:
            state = item.get("state") if isinstance(item, dict) else getattr(item, "state", None)
            state_value = getattr(state, "value", state)
            if str(state_value).lower() in {"active", "recording", "countdown"}:
                active.append(item)
        stopped = []
        for item in active:
            session_id = item.get("session_id") if isinstance(item, dict) else getattr(item, "session_id", None)
            if session_id:
                recording.stop_session(session_id)
                stopped.append(session_id)
        return {"executor": "recording_service", "stopped_sessions": stopped}

    raise RuntimeError(f"No engineering executor is registered for {action!r}")


class _StudioPeteShim:
    """Minimal non-speaking Pete stand-in so StudioControl can boot cleanly."""

    is_non_speaking_shim = True

    async def speak(self, *args, **kwargs):
        return None

    async def emergency_flush_buffers(self, *args, **kwargs):
        return None


def _ensure_default_voxel_asset_library(data_dir: Path) -> Path:
    """Create a minimal voxel asset library file if none exists yet."""
    library_path = data_dir / "voxel_asset_library.json"
    if library_path.exists():
        return library_path
    default_library = {
        "furniture": {"standard": [], "fancy": []},
        "home_structure": {"standard": [], "fancy": []},
        "rooms": {"standard": [], "fancy": []},
        "outdoor": {"standard": [], "fancy": []},
        "vehicles": {"standard": [], "fancy": []},
        "props": {"standard": [], "fancy": []},
    }
    library_path.write_text(json.dumps(default_library, indent=2), encoding="utf-8")
    logger.info("[INIT] Created default voxel asset library at %s", library_path)
    return library_path


# — CORS —
def _resolve_cors_origins() -> tuple[list[str], bool]:
    raw = os.getenv("PUBCAST_ALLOWED_ORIGINS", "*")
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    credentials = True
    if "*" in origins:
        if len(origins) > 1:
            origins = [o for o in origins if o != "*"]
            logger.warning("CORS: wildcard mixed with specific — wildcard dropped: %s", origins)
        else:
            credentials = False
            logger.warning("CORS: '*' origin with credentials is not allowed by browsers - allow_credentials forced False. Set PUBCAST_ALLOWED_ORIGINS to specific origin.")
    return origins, credentials


async def _json_dict(request: Request, *, allow_empty: bool = False) -> Dict[str, Any]:
    """Parse a request body and require a JSON object.

    A lot of older routes assumed a dict-shaped body and would explode with a 500
    or odd AttributeError when handed malformed JSON, a list, or a bare string.
    This keeps those boring failures boring.
    """
    try:
        raw = await request.body()
    except Exception as exc:
        if allow_empty:
            return {}
        raise HTTPException(status_code=400, detail="Invalid request body") from exc
    if not raw:
        return {}
    try:
        body = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Malformed JSON body") from exc
    if body is None and allow_empty:
        return {}
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="JSON object body required")
    return body


def _bounded_text(value: Any, *, default: str = '', max_len: int = 120) -> str:
    text = str(default if value is None else value).strip()
    return text[:max_len]


def _bounded_string_list(value: Any, *, field_name: str, max_items: int = 8, max_len: int = 64) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_items = [value]
    elif isinstance(value, (list, tuple, set)):
        raw_items = list(value)
    else:
        raise HTTPException(status_code=400, detail=f"{field_name} must be a string or list of strings")
    out: List[str] = []
    seen: set[str] = set()
    for item in raw_items:
        normalized = _bounded_text(item, max_len=max_len)
        if not normalized or normalized in seen:
            continue
        out.append(normalized)
        seen.add(normalized)
        if len(out) >= max_items:
            break
    return out


def _object_or_empty(value: Any, *, field_name: str) -> Dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise HTTPException(status_code=400, detail=f"{field_name} must be an object")
    return value


def _string_list_field(value: Any, field_name: str, *, max_items: int = 32, max_len: int = 120) -> List[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple, set)):
        raise HTTPException(status_code=400, detail=f"{field_name} must be a list of strings")
    out: List[str] = []
    for item in list(value)[:max_items]:
        out.append(_bounded_text(item, max_len=max_len))
    return out


def _caller_or_body_identity(
    *,
    request: Request,
    identity: Dict[str, Any],
    explicit_value: Any = None,
    field_name: str = "actor",
    allow_privileged_override: bool = True,
    fallback: str = "anon",
) -> str:
    """Bind identities only when auth or explicit caller headers make it meaningful.

    Legacy local flows often omit X-Client-Id entirely; in that relaxed case, let explicit
    body values pass through so older pages/tests keep working. Once auth is enforced or the
    caller explicitly sends X-Client-Id, use the shared security helper to prevent spoofing.
    """
    header_value = request.headers.get("X-Client-Id")
    if auth_enforced() or header_value:
        return bound_actor(
            request=request,
            identity=identity,
            explicit_value=explicit_value if explicit_value not in (None, "") else header_value,
            field_name=field_name,
            allow_privileged_override=allow_privileged_override,
        )
    explicit = str(explicit_value or "").strip()
    return explicit or fallback


# — Body-size guard —
class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    MAX_BODY = 1_048_576  # 1 MB default for every route
    # Routes that legitimately carry documents or media. Their own handlers enforce
    # tighter, type-aware ceilings (Foresight: 32 MB of file bytes = ~43 MB of base64
    # JSON); the global cap used to reject any save above ~780 KB before they ran.
    LARGE_BODY_LIMITS = (
        ("/api/foresight/workspace/file", 44 * 1024 * 1024),
        ("/api/foresight/files/", 44 * 1024 * 1024),
        ("/api/writers-room/documents/", 3 * 1024 * 1024),  # 2i documents may be up to 2 MB of JSON
        ("/api/media/intake", 256 * 1024 * 1024),
        ("/api/avatars/imports", 210 * 1024 * 1024),  # avatar GLBs; the route caps the file at 200 MB
    )

    @classmethod
    def limit_for(cls, path: str) -> int:
        for prefix, limit in cls.LARGE_BODY_LIMITS:
            if path == prefix or (prefix.endswith("/") and path.startswith(prefix)):
                return limit
        return cls.MAX_BODY

    async def dispatch(self, request: Request, call_next):
        max_body = self.limit_for(request.url.path)
        too_large = {"detail": f"Request body too large (max {max_body // (1024 * 1024)}MB)"}
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > max_body:
                    return JSONResponse(too_large, status_code=413)
            except ValueError:
                pass
        body_size = 0
        original_receive = request._receive  # noqa: SLF001

        async def limited_receive():
            nonlocal body_size
            message = await original_receive()
            if message.get("type") == "http.request":
                body_size += len(message.get("body", b""))
                if body_size > max_body:
                    return {"type": "http.request", "body": b"", "more_body": False}
            return message

        request._receive = limited_receive  # noqa: SLF001
        response = await call_next(request)
        if body_size > max_body:
            return JSONResponse(too_large, status_code=413)
        return response


# — ThinkingContext adapter —
class PubCastContextAdapter:
    def __init__(self, h: Hub, bm: BotManager) -> None:
        self._hub = h
        self._bm  = bm
    async def get_recent_history(self, room: str, limit: int = 12) -> list:
        return await self._hub.get_recent_history(room, limit)
    async def nudge(self, room_id: str, hint: str) -> bool:
        return await self._bm.nudge(room_id, hint)


# —
# Lifespan — 12-step boot
# —

@asynccontextmanager
async def lifespan(application: FastAPI):
    global hub, bot_manager, room_manager, inference, cameras, recording, blackbox_witness
    global governance, cricket_keeper, system_memory, ethereal_mgr, avatar_studio, vault, evo_orchestrator
    global byok_mgr, performance_manager, choreo_controller, lighting_engine, lighting_hub_patch
    global surface_manager, studio_control, studio_ws_handler
    global voxel_asset_manager, voxel_studio, voxel_bridge, pete_enhanced, unity_bridge, mocap, conv_orchestrator
    global production_log, timeline_player, waiting_room_manager, hotspot_manager, pipeline_sessions
    global alex_core_instance, alex_bridge, pub_manager_authority, program_audio_state, universal_memory_system, memory_ingestor, bubble_jeremy_adapter
    global irm_controller, performer_manager, cred_store
    global stt_engine, tts_engine

    # This app singleton's lifespan can be entered more than once within a
    # single process: every `with TestClient(app) as c:` against the same
    # `application` object re-triggers ASGI lifespan startup regardless of
    # which fixture or test file constructed that TestClient. Before this
    # guard existed, every re-entry replayed the entire 12-step boot below —
    # re-registering every router (confirmed cause of
    # test_02_routing.py::test_no_duplicate_http_routes failing only under
    # full-suite order), rebuilding every global singleton from scratch and
    # discarding whatever the previous entry had already set up, and
    # re-running step 9's tc_mount(), which is itself non-idempotent and
    # wraps a new lifespan around the previously-installed one on every call
    # (confirmed cause of an unbounded RecursionError once enough boots
    # accumulate in one process — reproduced directly outside pytest: 20
    # repeated TestClient opens against the same app object with this guard
    # absent grow the wrapping depth by exactly one layer per open with no
    # bound). application.state persists on the app singleton across separate
    # lifespan executions, so it is the correct place to record "already
    # booted" and make every entry after the first a no-op.
    if getattr(application.state, "_pubcast_booted", False):
        # Nested TestClients may enter this singleton from another event loop
        # while its owning lifespan is still active. They borrow the live app;
        # they must not re-arm or close the owner's tasks and database handles.
        if getattr(application.state, '_pubcast_lifespan_users', 0):
            application.state._pubcast_lifespan_users += 1
            try:
                yield
            finally:
                application.state._pubcast_lifespan_users -= 1
            return
        # The app-object boot guard intentionally prevents re-registering routers
        # and re-wrapping ThinkingContext on repeated TestClient/lifespan entries.
        # e-PETE is different: its clean shutdown terminates the owned renderer
        # subprocess and disconnects the shared bridge. Re-arm only that runtime
        # component here so the persistent app singleton does not expose stale
        # "connected" diagnostics on a later lifespan entry.
        # SystemMemory owns a SQLite connection and is closed at lifespan exit.
        # Re-open that connection without replaying full boot; RoomConductor keeps
        # the same SystemMemory object reference across app-singleton re-entry.
        if blackbox_witness is not None:
            blackbox_witness.reopen()
        rearmed_system_memory = getattr(application.state, "system_memory", None)
        if rearmed_system_memory is not None and getattr(rearmed_system_memory, "_conn", None) is None:
            try:
                await rearmed_system_memory.init()
            except Exception:
                logger.warning("Re-entrant SystemMemory re-arm failed", exc_info=True)

        rearmed_pete = getattr(application.state, "pete_enhanced", None)
        if rearmed_pete is not None and hasattr(rearmed_pete, "initialize_twin_engine_system"):
            try:
                await rearmed_pete.initialize_twin_engine_system()
                pete_enhanced_routes.set_pete_enhanced_instance(rearmed_pete)
            except Exception:
                logger.warning("Re-entrant e-PETE runtime re-arm failed", exc_info=True)

        rearmed_twin = getattr(application.state, "twin_engine", None)
        if rearmed_twin is not None and hasattr(rearmed_twin, "startup"):
            try:
                await rearmed_twin.startup()
            except Exception:
                logger.warning("Re-entrant TwinEngineService re-arm failed", exc_info=True)

        rearmed_conductor = getattr(application.state, 'room_conductor', None)
        if rearmed_conductor is not None and bot_manager is not None:
            for room in sorted({room for cfg in bot_manager.list_configs() for room in cfg.rooms}):
                await rearmed_conductor.watch_room(room)

        # Re-entry reuses the already-constructed subsystem owners. Emit explicit
        # reused-and-ready evidence so startup diagnostics do not go silent.
        if surface_manager is not None:
            logger.info("[14] Surface manager ready — reused existing owner")
        if voxel_asset_manager is not None:
            asset_count = len(getattr(voxel_asset_manager, "assets", {}) or getattr(voxel_asset_manager, "_assets", {}) or {})
            logger.info("[16] Voxel asset manager ready — reused existing owner (%d assets)", asset_count)
        if studio_control is not None:
            logger.info("[18] Studio Control ready — reused existing owner")
        if evo_orchestrator is not None:
            await evo_orchestrator.start(evo_orchestrator._engine_node, evo_orchestrator._camera_manager)
        rearmed_camera_broadcast = getattr(application.state, "camera_broadcast", None)
        if rearmed_camera_broadcast is not None:
            rearmed_camera_broadcast.start()
        application.state._pubcast_lifespan_users = 1
        try:
            yield
        finally:
            application.state._pubcast_lifespan_users = 0
            if rearmed_camera_broadcast is not None:
                await rearmed_camera_broadcast.stop()
            if evo_orchestrator is not None:
                await evo_orchestrator.stop()
            if rearmed_conductor is not None:
                await rearmed_conductor.shutdown()
            if bot_manager is not None:
                await bot_manager.shutdown()
            if blackbox_witness is not None:
                blackbox_witness.close()
            if rearmed_pete is not None and hasattr(rearmed_pete, "shutdown_twin_engine_system"):
                try:
                    await rearmed_pete.shutdown_twin_engine_system()
                except Exception:
                    logger.debug("Re-entrant e-PETE shutdown failed", exc_info=True)
            if rearmed_twin is not None and hasattr(rearmed_twin, "shutdown"):
                try:
                    await rearmed_twin.shutdown()
                except Exception:
                    logger.debug("Re-entrant TwinEngineService shutdown failed", exc_info=True)
            if rearmed_system_memory is not None and hasattr(rearmed_system_memory, "close"):
                try:
                    await rearmed_system_memory.close()
                except Exception:
                    logger.debug("Re-entrant SystemMemory shutdown failed", exc_info=True)
        return
    application.state._pubcast_booted = True

    logger.info("— PubCast AI v5.6 starting —")
    t0 = time.time()

    # 1. Hub + append-only EQ development evidence seam
    hub = Hub(DATA_DIR)
    from modules.eq_monitoring_recorder import EQMonitoringRecorder
    eq_monitoring_recorder = EQMonitoringRecorder(DATA_DIR, enabled=os.getenv("PUBCAST_EQ_DEV_RECORDING", "1") != "0")
    hub.eq_monitoring_recorder = eq_monitoring_recorder
    application.state.eq_monitoring_recorder = eq_monitoring_recorder
    logger.info("[1/12] Hub ready | EQ development recorder armed")

    # 2. RoomManager
    room_manager = RoomManager()
    logger.info("[2/12] RoomManager ready — %d rooms", len(room_manager.list_rooms()))

    # 2b. PerformanceManager (optional)
    if _HAS_PERFORMANCE and PerformanceManager is not None:
        try:
            performance_manager = init_performance_manager(
                data_dir=DATA_DIR,
                policy_path=Path("system_policy.json"),
            )
            application.state.performance_manager = performance_manager
            logger.info("[2b/12] Performance profile active — %s", performance_manager.active_profile)
        except Exception as exc:
            logger.warning("[2b/12] Performance manager failed: %s", exc)
    else:
        logger.info("[2b/12] Performance profiles — not available")

    # 2c. ChoreographyController (optional)
    if _HAS_CHOREO and ChoreographyController is not None:
        try:
            requested_tick_hz = float(os.getenv("PUBCAST_CHOREO_TICK_HZ", "30"))
            tick_hz = max(10.0, min(60.0, requested_tick_hz))
            choreo_controller = ChoreographyController(hub=hub, tick_hz=tick_hz)

            # Wire AnimationAuthority as the layer arbitration system
            if _HAS_ANIM_AUTHORITY and AnimationAuthority is not None:
                choreo_controller._anim_authority = AnimationAuthority()
                logger.info("[2c/12] Choreography controller ready — %.1f Hz | %d actions | AnimationAuthority wired",
                            tick_hz, len(choreo_controller.list_actions()))
            else:
                logger.info("[2c/12] Choreography controller ready — %.1f Hz | %d actions",
                            tick_hz, len(choreo_controller.list_actions()))
        except Exception as exc:
            logger.warning("[2c/12] Choreography controller failed: %s", exc)
    else:
        logger.info("[2c/12] Choreography controller — not available")

    # 2d. LightingEngine (optional)
    if _HAS_LIGHTING and LightingEngine is not None and LightingHubPatch is not None:
        try:
            lighting_engine    = LightingEngine()
            lighting_hub_patch = LightingHubPatch(lighting_engine, hub)
            preset_count = len(list_lighting_presets() or []) if list_lighting_presets else 0
            logger.info("[2d/12] Lighting engine ready — %d presets", preset_count)
        except Exception as exc:
            logger.warning("[2d/12] Lighting engine failed: %s", exc)
    else:
        logger.info("[2d/12] Lighting engine — not available")

    # 3. Inference
    inference = InferenceManager()
    await inference.startup()
    inf_status = inference.status()
    logger.info(
        "[3/12] Inference — Studio %s | Architect %s",
        "ready"   if inf_status.get("studio",    {}).get("available") else "offline",
        "ready"   if inf_status.get("architect", {}).get("available") else "optional/unavailable",
    )

    # 3a. Auth / user database
    try:
        await userdb.init_db()
        await userdb.create_owner_if_not_exists()
        auth_routes.set_auth_instance(auth_module)
        application.include_router(auth_routes.router)
        logger.info("[3a/12] Auth routes + user database ready")
    except Exception as exc:
        logger.warning("[3a/12] Auth system failed: %s", exc)

    # 3b. Alex + Alex/Jeremy Bridge + explicit Pub Manager authority reviewer
    try:
        alex_core_instance = AlexCore(user_id='default', data_dir=DATA_DIR / 'alex')
        alex_core_instance.eq_monitoring_recorder = eq_monitoring_recorder
        if choreo_controller is not None:
            from modules.affect_choreo_bridge import get_bridge as get_affect_choreo_bridge
            _affect_choreo_bridge = get_affect_choreo_bridge()
            async def _apply_affect_choreo(alex, session_id):
                return await _affect_choreo_bridge.apply(alex, choreo_controller, room=session_id or "main", avatar_id="pete")
            alex_core_instance.affect_choreo_callback = _apply_affect_choreo
        pub_manager_authority = PubManagerAuthorityStore(
            DATA_DIR,
            blackbox_logger=dr_security.log_black_box_event,
            executor=_execute_pub_manager_engineering_action,
        )
        alex_bridge = AlexJeremyBridge(
            DATA_DIR,
            authority_reviewer=pub_manager_authority.reviewer,
            blackbox_logger=dr_security.log_black_box_event,
        )
        try:
            from modules.alex_memory_backup import build_alex_backup_from_env
            alex_bridge.alex_backup = build_alex_backup_from_env(DATA_DIR)
            alex_routes.set_alex_backup(alex_bridge.alex_backup)
            # The default Alex instance is created before the bridge; wire it too.
            if alex_core_instance is not None:
                alex_core_instance.after_turn_hook = alex_bridge._notify_alex_backup
        except Exception as _backup_exc:
            print(f"[alex-backup] disabled: {type(_backup_exc).__name__}: {_backup_exc}")
        from modules.care_eq import CareCoordinator
        care_eq_coordinator = CareCoordinator(DATA_DIR)
        alex_bridge.care_eq = care_eq_coordinator
        alex_routes.set_care_eq(care_eq_coordinator)
        application.state.care_eq = care_eq_coordinator
        alex_routes.set_alex_instance(alex_core_instance)
        alex_routes.set_alex_provider(alex_bridge.alex_for)
        application.include_router(alex_routes.router)
        application.include_router(create_pub_manager_authority_router(pub_manager_authority, alex_bridge))
        application.include_router(create_pub_manager_control_router(pub_manager_authority, alex_bridge))
        logger.info("[3b/12] Alex core + Alex/Jeremy bridge + deterministic Pub Manager control plane ready")
    except Exception as exc:
        alex_core_instance = None
        alex_bridge = None
        pub_manager_authority = None
        logger.warning("[3b/12] Alex bridge failed: %s", exc)
    # 4. Jeremy memory infrastructure: SystemMemory is operational/protocol
    # memory; CricketKeeper is per-character private memory. They are distinct.
    system_memory = SystemMemory(data_dir=DATA_DIR / "system")
    await system_memory.init()
    application.state.system_memory = system_memory

    if _HAS_CRICKET and CricketKeeper is not None:
        cricket_keeper = CricketKeeper(data_dir=DATA_DIR / "jeremy")
        await cricket_keeper.init()
        logger.info("[4/12] CricketKeeper + SystemMemory ready")
    else:
        logger.info("[4/12] SystemMemory ready — CricketKeeper not available")

    # 5. BotManager
    # The integrated PubPartner uses the existing System Alex/Jeremy owners.
    # It must not launch a second coordination service or a second live route.
    from modules import pubpartner_routes
    from modules.pubpartner_vessel import PubPartnerVesselRuntime
    partner_vessel = PubPartnerVesselRuntime.open_or_create(
        DATA_DIR / "pubpartner" / "vessels" / "alex.pubpartner"
    )
    application.state.pubpartner_vessel = partner_vessel
    application.state.pubpartner_spine = pubpartner_routes.configure_pubpartner_spine(
        data_dir=DATA_DIR, alex_bridge=alex_bridge,
        cricket_keeper=cricket_keeper, vessel_runtime=partner_vessel, scoped_memory=True,
    )
    application.state.pubpartner_spine.provider_dispatcher.runtime_repo_root = Path(__file__).resolve().parent
    application.include_router(pubpartner_routes.router)
    from modules.writers_room import create_writers_room_router
    application.include_router(create_writers_room_router(DATA_DIR))
    from modules.manuscript_intelligence import make_router as create_manuscript_intelligence_router
    application.include_router(create_manuscript_intelligence_router(DATA_DIR))

    bot_manager = BotManager(data_dir=DATA_DIR, hub=hub)
    if cricket_keeper:
        bot_manager.set_cricket_keeper(cricket_keeper)
    async def communications_chat_callback(payload):
        conductor = getattr(application.state, 'room_conductor', None)
        if conductor is not None:
            room = payload['room']
            if any(room in cfg.rooms for cfg in bot_manager.list_configs()):
                await conductor.watch_room(room)
                await conductor.on_message(room, str(payload.get('user_id') or ''), str(payload.get('text') or ''))
        await bot_manager.on_chat_message(payload)
    hub.on_chat_callback = communications_chat_callback
    logger.info("[5/12] BotManager ready — %d bots", len(bot_manager.list_configs()))

    # Conversation orchestration belongs to RoomConductor / Jeremy Cricket and the Nudge Protocol.
    if _HAS_IRM and IRMController is not None:
        irm_controller = IRMController()
        logger.info("[5b/12] IRM engine monitor ready")
    else:
        logger.info("[5b/12] IRM engine monitor — not available")
    if _HAS_AVATAR_PERFORMER and AvatarPerformerManager is not None:
        performer_manager = AvatarPerformerManager()
        # Fire-and-forget: PerformerStreamer.connect() already retries forever
        # with backoff (see modules/avatar_performer.py). Awaiting it directly
        # here would block boot indefinitely whenever no Rust renderer is
        # running. Backgrounding it means boot never waits, and the connection
        # comes up automatically the moment a renderer is reachable.
        application.state.avatar_performer_connect_task = asyncio.create_task(
            performer_manager.start()
        )
        application.state.avatar_performer_manager = performer_manager
        logger.info(
            "[5b/12] AvatarPerformerManager ready — connecting to Rust renderer "
            "at %s in the background (non-blocking)", performer_manager._url
        )
    else:
        logger.info("[5b/12] AvatarPerformerManager — not available")
    if _HAS_CRED_STORE and CredentialStore is not None:
        try:
            cred_store = CredentialStore(DATA_DIR)
            logger.info("[5b/12] CredentialStore ready")
        except Exception as exc:
            logger.warning("[5b/12] CredentialStore failed: %s", exc)
    else:
        logger.info("[5b/12] CredentialStore — not available")

    # 6. Cameras + Recording
    cameras   = create_default_cameras()
    blackbox_witness = create_blackbox_witness(DATA_DIR)
    application.state.pubpartner_spine.blackbox_witness = blackbox_witness
    hub.blackbox_witness = blackbox_witness  # All Hub chat paths emit an offline witness event.
    application.include_router(create_blackbox_router(blackbox_witness))
    recording = create_recording_service(DATA_DIR, cameras, blackbox_witness=blackbox_witness)
    program_audio_state = ProgramAudioState()
    application.include_router(create_production_router(cameras, recording, hub, blackbox=blackbox_witness, program_audio_state=program_audio_state, include_overlapping_compat_routes=False))
    from modules.pubcast_vision_integration import PubcastVisionManager
    from modules.pubcast_vision_routes import create_vision_router
    vision_manager = PubcastVisionManager(camera_manager=cameras, data_dir=DATA_DIR)
    application.state.vision_manager = vision_manager
    application.include_router(create_vision_router(vision_manager))
    # Post-baseline director/switcher and reviewed 2.5D stage runtime.
    from modules.director_engine import AutonomousDirector
    from modules.switcher_routes import SwitcherService, create_switcher_router
    director_engine = AutonomousDirector()
    switcher_service = SwitcherService(cameras, director=director_engine, recording=recording)
    application.state.director_engine = director_engine
    application.state.switcher_service = switcher_service
    application.include_router(create_switcher_router(switcher_service))
    # Every program/preview change, from any route, reaches the stage pages.
    from modules.camera_broadcast import CameraBroadcastBridge
    camera_broadcast = CameraBroadcastBridge(cameras, hub)
    camera_broadcast.start()
    application.state.camera_broadcast = camera_broadcast

    from modules.pubworld_stage.manifest_store import ManifestStore
    from modules.pubworld_stage.stage_service import StageService
    from modules.pubworld_stage.routes import create_stage_router
    stage_store = ManifestStore(DATA_DIR / "pubworld" / "scenes")
    stage_service = StageService(stage_store)
    application.state.stage_service = stage_service
    application.include_router(create_stage_router(stage_service))

    from modules.rust_camera_runtime import RustCameraRuntime
    from modules.rust_camera_routes import create_rust_camera_router
    rust_camera_runtime = RustCameraRuntime(cameras)
    application.state.rust_camera_runtime = rust_camera_runtime
    application.include_router(create_rust_camera_router(rust_camera_runtime))
    try:
        await rust_camera_runtime.start()
        if rust_camera_runtime.enabled:
            logger.info("[6a] Authenticated Rust camera Stage-1 control connected")
        else:
            logger.info("[6a] Rust camera Stage-1 source ready but transport disabled (set PUBCAST_ENABLE_RUST_CAMERA_CONTROL=1)")
    except Exception as exc:
        logger.warning("[6a] Rust camera Stage-1 transport unavailable: %s", exc)

    from modules.performance.avatar_adapter import AvatarPerformanceAdapter
    avatar_performance_adapter = AvatarPerformanceAdapter()
    application.state.avatar_performance_adapter = avatar_performance_adapter
    if performer_manager is not None:
        from modules.performance.routes import create_performance_router
        application.include_router(create_performance_router(avatar_performance_adapter, performer_manager))

    logger.info(
        "[6/12] Cameras (%d) + Recording (%d profiles) + Switcher + 2.5D Stage + Avatar adapter ready",
        len(cameras.list_sources()), len(recording.list_profiles()),
    )

    # AdvancedCameraManager is preserved as an incubating donor, not booted as a
    # second camera authority. Enable only for deliberate isolated compatibility.
    application.state.advanced_cameras = None
    if _HAS_CAMERAS_ADVANCED and os.getenv("PUBCAST_ENABLE_LEGACY_ADVANCED_CAMERA", "0") == "1":
        try:
            advanced_cameras = AdvancedCameraManager(config_path=DATA_DIR / "cameras.json")
            application.state.advanced_cameras = advanced_cameras
            logger.warning("[6b] Legacy AdvancedCameraManager explicitly enabled; canonical CameraManager remains production authority")
        except Exception as exc:
            logger.warning("[6b] Legacy AdvancedCameraManager failed: %s", exc)

    # 7. Governance
    governance = GovernanceEngine(DATA_DIR)
    application.include_router(create_governance_router(governance, hub, authority_bridge=alex_bridge, authority_store=pub_manager_authority))
    logger.info("[7/12] Governance ready — bans, freeze, consent, waiting room")

    # 7b. PubWorld Hotspot API
    try:
        hotspot_router = create_hotspot_router(DATA_DIR)
        application.include_router(hotspot_router)
        logger.info("[7b] PubWorld hotspot API ready")
    except Exception as exc:
        logger.warning("[7b] PubWorld hotspot API failed: %s", exc)

    # 7c. NEW: Structured Production Logging
    try:
        production_log = init_production_log(DATA_DIR / "logs")
        emit("startup", "boot_start", {"version": "5.5"})
        application.include_router(structured_log_routes.router)
        logger.info("[7c] Structured production logging ready")
    except Exception as exc:
        logger.warning("[7c] Structured logging failed: %s", exc)

    # 7d. NEW: Timeline Automation System
    try:
        timeline_routes.init_timeline_system(DATA_DIR)
        timeline_player = timeline_routes.player
        application.include_router(timeline_routes.router)
        logger.info("[7d] Timeline automation ready")
    except Exception as exc:
        logger.warning("[7d] Timeline system failed: %s", exc)

    # 7e. NEW: Waiting Room / Airlock
    try:
        waiting_room_manager = governance_waiting_room.init_waiting_room(auto_approve=False)
        application.include_router(governance_waiting_room.create_full_host_waiting_room_router(governance))
        logger.info("[7e] Waiting room / airlock ready")
    except Exception as exc:
        logger.warning("[7e] Waiting room failed: %s", exc)

    # 7e2. Chat room system — role-gated rooms + private messaging with request/accept/decline
    if _HAS_CHAT_ROOMS:
        try:
            from modules.route_security import current_identity
            chat_router = create_chat_router(hub, current_identity)
            application.include_router(chat_router)
            install_chat_websocket(application, hub, current_identity)
            logger.info(
                "[7e2] Chat rooms ready — %d rooms, 6 roles, DM bypass: host/security/mod "
                "| /api/chat/rooms  /ws/chat/{room_id}  /api/chat/dm/request",
                len(__import__('modules.chat_rooms', fromlist=['ROOM_REGISTRY']).ROOM_REGISTRY),
            )
        except Exception as exc:
            logger.warning("[7e2] Chat rooms failed: %s", exc)

    # 7f. NEW: Hotspot Trigger System
    try:
        hotspot_manager = hotspot_system.init_hotspot_system(DATA_DIR)
        application.include_router(hotspot_system.router)
        # Register default handlers
        hotspot_manager.register_handler("transition", hotspot_system.default_transition_handler)
        hotspot_manager.register_handler("animation", hotspot_system.default_animation_handler)
        hotspot_manager.register_handler("custom", hotspot_system.default_custom_handler)
        logger.info("[7f] Hotspot system ready — %d rooms", len(hotspot_manager._rooms))
    except Exception as exc:
        logger.warning("[7f] Hotspot system failed: %s", exc)

    # 7g. NEW: Recording Pipeline Routes
    try:
        application.include_router(recording_pipeline_routes.create_recording_pipeline_router(include_marker_route=False))
        logger.info("[7g] Recording pipeline export routes ready")
    except Exception as exc:
        logger.warning("[7g] Recording pipeline routes failed: %s", exc)

    # 7g2. Audio device management + mic routes -- these routers were fully
    # built (correct /api/audio/... and /api/mic/... paths, real device
    # enumeration logic) but never wired into the app with include_router.
    try:
        application.include_router(audio_devices_module.router)
        application.include_router(mic_routes_module.router)
        logger.info("[7g2] Audio device + mic routes ready")
    except Exception as exc:
        logger.warning("[7g2] Audio device + mic routes failed: %s", exc)

    # 7g3. Bubble Stack spatial-awareness routes
    # Recovered and regression-tested in the historical line; the missing piece
    # was registration in the full host. Keep Bubble state owned by its router
    # and expose only its summary provider to Jeremy/RoomConductor.
    if _HAS_BUBBLE_STACK and bubble_routes_module is not None:
        try:
            application.include_router(bubble_routes_module.router)
            if BubbleJeremyAdapter is not None and hasattr(bubble_routes_module, "get_bubble_summary"):
                bubble_jeremy_adapter = BubbleJeremyAdapter(bubble_routes_module.get_bubble_summary)
                application.state.bubble_jeremy_adapter = bubble_jeremy_adapter
            logger.info("[7g3] Bubble Stack routes ready — /api/bubble-stack")
        except Exception as exc:
            bubble_jeremy_adapter = None
            logger.warning("[7g3] Bubble Stack route registration failed: %s", exc)
    else:
        logger.info("[7g3] Bubble Stack — not available")

    # 7h. Character/story/memory route surface
    try:
        universal_memory_system = UniversalMemorySystem(data_dir=DATA_DIR)
        for character_id in ("pete", "repeat", "sir_purfluous", "jeremy", "default"):
            universal_memory_system.get_or_create_bank(character_id)
        loaded_count = universal_memory_system.load_from_db(DATA_DIR)
        memory_ingestor = MemoryIngestor(
            DATA_DIR,
            memory_system=universal_memory_system,
            alex=alex_core_instance,
            project_id="pubcast",
        )
        memory_routes.set_memory_instance(universal_memory_system)
        personal_ai_memory_api.configure_personal_memory_api(
            data_dir=DATA_DIR,
            memory_system=universal_memory_system,
            ingestor=memory_ingestor,
        )

        class _CharacterProfileAdapter:
            def list_characters(self):
                return character_profiles.list_characters()

            def get_character(self, character_id: str):
                profile = character_profiles.get_character_profile(character_id)
                return profile.__dict__ if profile else None

        class _CharacterEngineAdapter:
            async def speak(self, character_id: str, message: str, context: Optional[Dict[str, Any]] = None):
                # Legacy character endpoint delegates to the canonical BotManager
                # and the same private transcript authority as Foresight.
                # No parallel inference shortcut may bypass profiles/memory.
                from modules.character_service import speak_to_character
                result = await speak_to_character(
                    bot_manager, hub, bot_id=character_id, message=message,
                    user_id=(context or {}).get("user_id", ""),
                    room_id=(context or {}).get("room_id", "studio"),
                )
                return result["reply"]

            def get_character_context(self, character_id: str):
                profile = character_profiles.get_character_profile(character_id)
                return profile.__dict__ if profile else {"character_id": character_id, "known": False}

        class _StoryBibleAdapter:
            def get_overview(self):
                return {
                    "themes": pubcast_story_bible.THEMES,
                    "theme_song_fragment": pubcast_story_bible.THEME_SONG_LYRICS_FRAGMENT,
                }

            def get_characters(self):
                roots = getattr(pubcast_story_bible, "CHARACTER_ROOTS", {})
                return {key: value.__dict__ for key, value in roots.items()}

            def get_beats(self):
                beats = getattr(pubcast_story_bible, "STORY_BEATS", {})
                if isinstance(beats, dict):
                    return {key: value.__dict__ if hasattr(value, "__dict__") else value for key, value in beats.items()}
                return beats

        character_routes.set_character_instances(_CharacterEngineAdapter(), _CharacterProfileAdapter())
        story_routes.set_story_instance(_StoryBibleAdapter())
        application.include_router(memory_routes.router)
        application.include_router(character_routes.router)
        application.include_router(story_routes.router)
        application.include_router(pete_enhanced_routes.router)
        application.include_router(personal_ai_memory_api.router)
        logger.info("[7h] Character/story/memory routes ready; loaded %d persisted memories", loaded_count)
    except Exception as exc:
        logger.warning("[7h] Character/story/memory routes failed: %s", exc)

    # 8. BYOK
    if _HAS_BYOK and BYOKManager is not None:
        try:
            byok_mgr = BYOKManager(DATA_DIR / "byok")
            create_byok_router(application, byok_mgr)
            bot_manager.set_byok_manager(byok_mgr)
            application.state.pubpartner_spine.set_byok_manager(byok_mgr)
            logger.info("[8/12] BYOK ready — user-supplied API keys enabled")
        except Exception as exc:
            logger.warning("[8/12] BYOK failed: %s", exc)
    else:
        logger.info("[8/12] BYOK — not available")

    # 9. ThinkingContext
    #
    # tc_mount() is not idempotent: it captures whatever is currently set as
    # application.router.lifespan_context and wraps a NEW lifespan around it,
    # then reassigns application.router.lifespan_context to that wrapper. This
    # boot sequence *is* application.router.lifespan_context (it runs on every
    # ASGI lifespan startup, once per app boot). Calling tc_mount() from inside
    # it therefore wraps this very lifespan around its own previously-installed
    # wrapper on every re-entrant boot (a second TestClient/server start on the
    # same app object, a test suite that opens more than one TestClient against
    # main.app, a process restart of the ASGI lifespan without a fresh app
    # object) — each boot nests one more layer, with no matching unwrap. The
    # chain is unbounded: enough accumulated boots against the same app
    # eventually exceed Python's recursion limit on entry/exit of the nested
    # async-context-manager chain (observed directly: RecursionError inside
    # TestClient.wait_startup on the ~500th cumulative full-suite boot).
    #
    # application.state persists on the app singleton across separate lifespan
    # executions (Starlette does not reset it between boots), so it is a valid
    # place to mark "already mounted for this app object" and skip re-wrapping
    # on every subsequent boot. This guards the call site only; it does not
    # modify thinking_context/mount.py, whose documented contract is a single
    # call at app-build time — this restores that contract without touching
    # the library.
    if _HAS_THINKING_CONTEXT and tc_mount is not None:
        if getattr(application.state, "thinking_context", None) is not None:
            logger.info("[9/12] ThinkingContext — already mounted on this app, skipping re-mount")
        else:
            try:
                adapter    = PubCastContextAdapter(hub, bot_manager)
                characters = _build_character_profiles()
                tc_mount(
                    application, adapter,
                    characters=characters,
                    snapshot_path=str(DATA_DIR / "memory_snapshot.json"),
                    startup_rooms=["studio", "green_room"],
                )
                logger.info("[9/12] ThinkingContext registered — %d characters (its wrapper lifespan "
                            "only runs on the next app start; RoomConductor [12/12] drives rooms now)", len(characters))
            except Exception as exc:
                logger.warning("[9/12] ThinkingContext failed: %s", exc)
    else:
        logger.info("[9/12] ThinkingContext — not available")

    # 10. Ethereal Avatars
    if _HAS_ETHEREAL and EtherealAvatarManager is not None:
        try:
            ethereal_mgr = EtherealAvatarManager(DATA_DIR)
            application.include_router(create_ethereal_router(ethereal_mgr))
            avatar_studio = AvatarStudioBridge(ethereal_mgr, cameras, hub)
            application.include_router(create_avatar_studio_router(avatar_studio))
            logger.info("[10/12] Ethereal Avatars ready — 57 joints, %d colors",
                        len(ethereal_mgr.get_available_colors()))
            logger.info("[10b/12] Avatar Studio bridge ready")
        except Exception as exc:
            logger.warning("[10/12] Ethereal Avatars failed: %s", exc)
    else:
        logger.info("[10/12] Ethereal Avatars — not available")

    # 11. EVO Protocol — Switchblade + VDI + E-Pete
    if _HAS_EVO and EVOOrchestrator is not None:
        try:
            from modules.evo_host import EVOInferenceBackend
            evo_orchestrator = EVOOrchestrator(
                active_character="pete",
                llm_backend=EVOInferenceBackend(inference),
            )
            # Start the owned worker. Render/camera attachments remain explicit;
            # construction alone must not be reported as an active runtime.
            await evo_orchestrator.start(engine_node=None, camera_manager=None)
            application.state.evo_orchestrator = evo_orchestrator
            logger.info("[11/12] EVO worker started; render/camera attachments are not configured")
        except Exception as exc:
            logger.warning("[11/12] EVO Protocol failed: %s", exc)
    else:
        logger.info("[11/12] EVO Protocol — not available")

    # 12. Vault
    if _HAS_VAULT and PubCastVault is not None:
        try:
            vault = PubCastVault(DATA_DIR / "vault")
            application.include_router(create_vault_router(vault))
            logger.info("[12/12] Vault ready — OS-level protection active")
        except Exception as exc:
            logger.warning("[12/12] Vault failed: %s", exc)
    else:
        logger.info("[12/12] Vault — not available")

    logger.info("[12b] Doctor — %s", "ready" if _HAS_DOCTOR else "not available")

    # 12c. Key recovery — vault key backup and passphrase recovery path
    if _HAS_KEY_RECOVERY:
        try:
            key_recovery = KeyRecovery(DATA_DIR / "vault")
            application.state.key_recovery = key_recovery
            logger.info("[12c] Key recovery ready — vault backup path available")
        except Exception as exc:
            logger.warning("[12c] Key recovery failed: %s", exc)

    # — New subsystems boot —

    # PubWorld router — live production state broadcast to map/world clients
    if _HAS_PUBWORLD_ROUTER and _pubworld_router:
        try:
            if configure_pubworld_state_provider is not None:
                configure_pubworld_state_provider(hub.get_production_state)
            application.include_router(_pubworld_router)
            logger.info("[13] PubWorld router ready — /pubworld/ws live broadcast")
        except Exception as exc:
            logger.warning("[13] PubWorld router failed: %s", exc)

    # Surface manager — placeable media screens in rooms
    if _HAS_SURFACES:
        try:
            surface_manager = SurfaceManager(DATA_DIR)
            logger.info("[14] Surface manager ready")
        except Exception as exc:
            logger.warning("[14] Surface manager failed: %s", exc)

    # Conversation orchestrator — multi-agent turn coordination
    if _HAS_ORCHESTRATOR:
        try:
            conv_orchestrator = ConversationOrchestrator()
            logger.info("[15] ConversationOrchestrator ready")
        except Exception as exc:
            logger.warning("[15] ConversationOrchestrator failed: %s", exc)

    # 15b. Room conductor — Jeremy Cricket conversation orchestra (memory, whisper, conduct)
    if _HAS_ROOM_CONDUCTOR:
        try:
            _room_conductor = await create_room_conductor(
                memory_system    = universal_memory_system,
                bot_manager      = bot_manager,
                hub              = hub,
                adapter_registry = {},   # adapters wired in when inference is live
                cricket_keeper   = cricket_keeper,
                system_memory    = system_memory,
            )
            if _HAS_BUBBLE_STACK and bubble_routes_module is not None and hasattr(bubble_routes_module, "get_bubble_summary"):
                _room_conductor.set_bubble_summary_provider(bubble_routes_module.get_bubble_summary)
            application.state.room_conductor = _room_conductor
            for room in sorted({room for cfg in bot_manager.list_configs() for room in cfg.rooms}):
                await _room_conductor.watch_room(room)
            logger.info("[15b] RoomConductor (Jeremy Cricket) ready — conducting conversations")
        except Exception as exc:
            logger.warning("[15b] RoomConductor failed: %s", exc)

    # Voxel stack — asset manager + LLM generator + studio integration
    if _HAS_VOXEL:
        try:
            voxel_library_path = _ensure_default_voxel_asset_library(DATA_DIR)
            voxel_asset_manager = VoxelAssetManager(library_path=voxel_library_path)
            logger.info("[16] Voxel asset manager ready — %d assets catalogued",
                        len(voxel_asset_manager.get_all_assets()))
        except Exception as exc:
            logger.warning("[16] Voxel stack failed: %s", exc)

    # Twin-engine connection — V3 Windows SHM -> TCP -> filesystem fallback
    if _HAS_BRIDGE:
        try:
            voxel_bridge = VoxelBridge(DATA_DIR)
            if voxel_asset_manager is not None and hasattr(voxel_asset_manager, "config"):
                voxel_asset_manager.config["bridge"] = voxel_bridge
            bridge_status = (
                voxel_bridge.status()
                if hasattr(voxel_bridge, "status") and callable(voxel_bridge.status)
                else getattr(voxel_bridge, "status", "available")
            )
            # Do not connect here. PeteEnhanced activates the shared bridge when
            # available; TwinEngineService connects it otherwise. This prevents
            # three independent connect() calls against one transport.
            logger.info("[17] Voxel bridge constructed — activation deferred to runtime owner (%s)", bridge_status)
        except Exception as exc:
            logger.warning("[17] Voxel bridge not connected (renderer not running): %s", exc)

    # e-PETE — internal twin-engine diagnostics/orchestration.
    # Historical Horizon wiring placed this *after* the real VoxelBridge exists.
    # motion_system is intentionally empty here: PeteEnhanced currently stores the
    # reference for compatibility but does not consume it. Do not replace this with
    # a fake motion runtime just to make the constructor look complete.
    if _HAS_PETE_ENHANCED and PeteEnhanced is not None and voxel_bridge is not None:
        try:
            candidate_pete = PeteEnhanced(
                hub=hub,
                bridge=voxel_bridge,
                motion_system={},
                data_dir=DATA_DIR,
                owns_bridge=False,
            )
            pete_ready = await candidate_pete.initialize_twin_engine_system()
            if pete_ready:
                pete_enhanced = candidate_pete
                pete_enhanced_routes.set_pete_enhanced_instance(pete_enhanced)
                application.state.pete_enhanced = pete_enhanced
                logger.info(
                    "[17a] e-PETE diagnostics active — mode=%s activation=%s",
                    pete_enhanced.get_runtime_component_status().get("runtime_mode"),
                    pete_enhanced.get_runtime_component_status().get("runtime_activation"),
                )
            else:
                pete_enhanced = None
                application.state.pete_enhanced = None
                logger.warning("[17a] e-PETE diagnostics unavailable — bridge/runtime activation failed")
        except Exception as exc:
            pete_enhanced = None
            application.state.pete_enhanced = None
            logger.warning("[17a] e-PETE guarded initialization failed: %s", exc)
    else:
        application.state.pete_enhanced = None
        logger.info("[17a] e-PETE — not available or bridge missing")

    # Twin engine service — proper mount with camera state + /api/twin/* routes
    if _HAS_TWIN_ENGINE:
        try:
            _twin = await mount_twin_engine(app, bridge=voxel_bridge, camera_manager=cameras)
            install_twin_engine_routes(app)
            logger.info(
                "[17b] Twin engine service mounted — mode=%s  /api/twin/status ready",
                _twin.mode.value,
            )
        except Exception as exc:
            logger.warning("[17b] Twin engine service failed to mount: %s", exc)

    # Camera boxer — tiered resource donation, driven by real bridge stress
    if _HAS_CAMERA_BOXER:
        try:
            _boxer = CameraBoxer(bridge=voxel_bridge)
            _boxer.start()
            install_camera_boxer_routes(app, _boxer)
            app.state.camera_boxer = _boxer
            logger.info(
                "[17c] Camera boxer ready — "
                "T1≥65%% T2≥80%% T3≥92%% | audio always protected | /api/boxer/status"
            )
        except Exception as exc:
            logger.warning("[17c] Camera boxer failed to start: %s", exc)

    # STT engine — faster-whisper, loads model lazily on first transcription
    if _HAS_STT:
        try:
            stt_engine = STTEngine(
                model_size   = os.getenv("PUBCAST_STT_MODEL", "medium"),
                device       = os.getenv("PUBCAST_STT_DEVICE", "auto"),
                compute_type = os.getenv("PUBCAST_STT_COMPUTE", "auto"),
            )
            app.state.stt_engine = stt_engine
            logger.info(
                "[17d] STT engine ready — Whisper %s on %s | /api/stt/transcribe",
                stt_engine.model_size, stt_engine.device,
            )
        except Exception as exc:
            logger.warning("[17d] STT engine failed: %s", exc)

    # TTS engine — XTTS-v2 with character voice cloning, pyttsx3 fallback
    if _HAS_TTS_ENGINE:
        try:
            tts_engine = TTSEngine(data_dir=DATA_DIR)
            app.state.tts_engine = tts_engine
            voices = tts_engine.list_voices()
            logger.info(
                "[17e] TTS engine ready — %d voice(s) ready | /api/tts/synthesize",
                len(voices),
            )
            if voices:
                logger.info("[17e] Character voices: %s", list(voices.keys()))
        except Exception as exc:
            logger.warning("[17e] TTS engine failed: %s", exc)

    # Studio control — Iron Core preflight, audio matrix, dead man's switch
    if _HAS_STUDIO_CONTROL:
        try:
            # Prefer the real internal e-PETE orchestrator when available.
            # StudioControl's Pete hooks are advisory and remain safe with the
            # local shim if e-PETE could not activate.
            studio_pete = pete_enhanced if pete_enhanced is not None else _StudioPeteShim()
            studio_control = StudioControl(hub=hub, pete=studio_pete, data_dir=DATA_DIR)
            if _HAS_VOXEL and voxel_asset_manager is not None:
                try:
                    voxel_studio = VoxelStudioIntegration(
                        asset_manager=voxel_asset_manager,
                        studio_control=studio_control,
                        pete=pete_enhanced,
                    )
                    logger.info("[18a] Voxel studio integration ready")
                except Exception as exc:
                    logger.warning("[18a] Voxel studio integration failed: %s", exc)
            studio_ws_handler = StudioWebSocketHandler(
                studio_control=studio_control,
            )
            logger.info("[18] Studio Control ready — preflight + audio matrix active")
        except Exception as exc:
            logger.warning("[18] Studio Control failed: %s", exc)

    # Unity bridge — Unity — PubCast hub WebSocket
    if _HAS_UNITY_BRIDGE:
        try:
            unity_bridge = UnityBridge(hub=hub)
            logger.info("[19] Unity bridge ready — /unity/ws")
        except Exception as exc:
            logger.warning("[19] Unity bridge failed: %s", exc)

    # MoCap integration — live motion capture streaming
    if _HAS_MOCAP:
        try:
            mocap = MocapIntegration(hub=hub, pete=pete_enhanced)
            logger.info("[20] MoCap transport ready — Hub broadcast active; optional avatar/render/record hooks report their own capability state")
        except Exception as exc:
            logger.warning("[20] MoCap integration failed: %s", exc)

    elapsed = time.time() - t0
    logger.info("— PubCast AI v5.5 ready in %.1fs —", elapsed)
    logger.info("    http://%s:%d/",                                       settings.host, settings.port)
    logger.info("    Stage:         /static/stage.html")
    logger.info("    Panoramic:     /static/stage_panoramic.html")
    logger.info("    Control Room:  /static/control_room.html")
    logger.info("    Studio Ctrl:   /studio-control")
    logger.info("    World:         /static/world.html")
    logger.info("    PubWorld Stage:/pubworld-stage")
    logger.info("    Builder:       /builder")
    logger.info("    Map:           /static/map.html")
    logger.info("    Dressing:      /dressing")
    logger.info("    Launch:        /launch")
    logger.info("    Bar:           /bar")
    logger.info("    Gallery:       /gallery")
    logger.info("    Analytics:     /analytics")
    logger.info("    Health:        /health")
    logger.info("    Doctor:        /static/doctor.html  |  /api/doctor")
    logger.info("    Lighting Lab:  /static/pubcast_lighting_explorer.html")
    logger.info("    Voxel API:     /api/voxel/assets  |  /api/voxel/generate")
    logger.info("    Studio API:    /api/studio/status  |  /api/studio/preflight")
    logger.info("    Unity WS:      /unity/ws/{client_id}")
    logger.info("    Studio WS:     /studio/ws")

    # — NEW: Wire event handlers —
    
    # Timeline event handlers
    if timeline_player:
        try:
            # Camera switches
            async def handle_timeline_camera(params):
                to_cam = params.get('to', 'cam_1')
                transition = params.get('transition', 'cut')
                if cameras:
                    # Use correct method: set_program_source (not async)
                    cameras.set_program_source(to_cam)
                if production_log:
                    emit("timeline", "camera_switch", {"to": to_cam, "transition": transition})
            
            # Lighting changes
            async def handle_timeline_lighting(params):
                preset = params.get('preset')
                if lighting_engine and preset:
                    # Use correct method: set_preset
                    lighting_engine.set_preset(preset)
                if production_log:
                    emit("timeline", "lighting_change", {"preset": preset})
            
            # Bot chat
            async def handle_timeline_chat(params):
                user = params.get('user', '')
                text = params.get('text', '')
                room = params.get('room', 'studio')  # Default room for timeline events
                if hub and user and text:
                    # Use correct Hub method: post_chat_message(room, user_id, text)
                    await hub.post_chat_message(room, user, text)
                if production_log:
                    emit("timeline", "bot_chat", {"user": user, "room": room})
            
            # Recording control
            async def handle_timeline_record(params):
                action = params.get('action')
                if action == 'start' and recording:
                    # Create recording session with timeline-specified parameters
                    session = recording.start_session(
                        session_id=None,  # Auto-generate
                        sources=params.get('sources', ['cam_1']),  # Default to cam_1
                        profile_id=params.get('profile_id', 'broadcast_mp4'),  # Default profile
                        operator='timeline_automation',
                        preset=params.get('preset'),
                        host_override=True,  # Timeline has authority
                        countdown_seconds=0,  # Immediate start for timeline
                    )
                    if production_log:
                        emit("timeline", "recording_start", {"session_id": session.session_id})
                elif action == 'stop' and recording:
                    # Stop most recent active session
                    active_sessions = [s for s in recording.list_sessions() 
                                     if s.state in ['active', 'countdown']]
                    if active_sessions:
                        recording.stop_session(active_sessions[-1].session_id)
                    if production_log:
                        emit("timeline", "recording_stop", {})
            
            register_timeline_handler(EventType.CAMERA, handle_timeline_camera)
            register_timeline_handler(EventType.LIGHTING, handle_timeline_lighting)
            register_timeline_handler(EventType.CHAT, handle_timeline_chat)
            register_timeline_handler(EventType.RECORD, handle_timeline_record)
            
            logger.info("[INIT] Timeline event handlers registered")
        except Exception as exc:
            logger.warning("[INIT] Timeline handler registration failed: %s", exc)
    
    # Hotspot event handlers
    if hotspot_manager and hub:
        try:
            # Override default transition handler with hub broadcast
            async def handle_hotspot_transition(action, user_id, hotspot_id, room):
                destination = action.get("destination", "unknown")
                spawn_point = action.get("spawnPoint", "default")
                
                await hub.broadcast_system_event({
                    "type": "transition",
                    "user_id": user_id,
                    "from_room": room,
                    "to_room": destination,
                    "spawn_point": spawn_point,
                })
                
                if production_log:
                    emit("hotspots", "transition", {
                        "user_id": user_id,
                        "from": room,
                        "to": destination,
                    })
                
                return {"transitioned": True, "destination": destination}
            
            hotspot_manager.register_handler("transition", handle_hotspot_transition)
            logger.info("[INIT] Hotspot event handlers registered")
        except Exception as exc:
            logger.warning("[INIT] Hotspot handler registration failed: %s", exc)
    
    # Camera switch logging
    if cameras and production_log:
        try:
            original_set_program = cameras.set_program_source
            def logged_set_program(source_id: str) -> bool:
                from_cam = cameras.get_program_source()
                result = original_set_program(source_id)
                emit("cameras", "switch", {"from": from_cam.source_id if from_cam else "unknown", "to": source_id})
                return result
            cameras.set_program_source = logged_set_program
            logger.info("[INIT] Camera logging enabled")
        except Exception as exc:
            logger.warning("[INIT] Camera logging failed: %s", exc)
    
    if production_log:
        emit("startup", "boot_complete", {"duration_ms": int((time.time() - t0) * 1000)})

    # — Test/introspection aliases —
    # The startup test suite (tests/test_01_startup.py through test_06_regression.py)
    # checks service readiness via short module-level aliases and via
    # application.state, rather than the full internal names above. Expose
    # both so that contract holds without renaming the internal globals
    # everything else in this file already depends on.
    global bot_mgr, cam, rec, room_mgr, studio_ctrl, voxel_asset_mgr, unity_bridge_mgr
    global performer_mgr
    bot_mgr = bot_manager
    cam = cameras
    rec = recording
    room_mgr = room_manager
    studio_ctrl = studio_control
    voxel_asset_mgr = voxel_asset_manager
    unity_bridge_mgr = unity_bridge
    performer_mgr = performer_manager
    application.state.hub = hub
    application.state.data_dir = DATA_DIR
    application.state._pubcast_lifespan_users = 1

    yield
    application.state._pubcast_lifespan_users = 0

    # — Shutdown —
    logger.info("— PubCast AI shutting down —")
    _camera_broadcast = getattr(application.state, "camera_broadcast", None)
    if _camera_broadcast is not None:
        await _camera_broadcast.stop()
    # Stop only processes started through this authenticated host boundary.
    _stop_shells = getattr(application.state, "foresight_stop_sessions", None)
    if callable(_stop_shells):
        await _stop_shells()
    if choreo_controller and hasattr(choreo_controller, "stop"):
        try:
            await choreo_controller.stop()
        except Exception:
            pass
    if evo_orchestrator and hasattr(evo_orchestrator, "stop"):
        try:
            await evo_orchestrator.stop()
        except Exception:
            pass
    if pete_enhanced and hasattr(pete_enhanced, "shutdown_twin_engine_system"):
        try:
            await pete_enhanced.shutdown_twin_engine_system()
        except Exception:
            logger.debug("e-PETE shutdown failed", exc_info=True)
    rust_camera_runtime = getattr(application.state, "rust_camera_runtime", None)
    if rust_camera_runtime is not None:
        try:
            await rust_camera_runtime.stop()
        except Exception:
            logger.debug("RustCameraRuntime shutdown failed", exc_info=True)
    twin_engine_runtime = getattr(application.state, "twin_engine", None)
    if twin_engine_runtime is not None and hasattr(twin_engine_runtime, "shutdown"):
        try:
            await twin_engine_runtime.shutdown()
        except Exception:
            logger.debug("TwinEngineService shutdown failed", exc_info=True)
    if vault and hasattr(vault, "shutdown"):
        vault.shutdown()
    if _room_conductor and hasattr(_room_conductor, "shutdown"):
        try:
            await _room_conductor.shutdown()
        except Exception:
            logger.debug("RoomConductor shutdown failed", exc_info=True)
    if system_memory and hasattr(system_memory, "close"):
        try:
            await system_memory.close()
        except Exception:
            logger.debug("SystemMemory shutdown failed", exc_info=True)
    if bot_manager is not None:
        await bot_manager.shutdown()
    if cricket_keeper and hasattr(cricket_keeper, "close_all"):
        await cricket_keeper.close_all()
    if blackbox_witness is not None:
        blackbox_witness.close()
    logger.info("— PubCast AI stopped —")


# —
# Application
# —

app = FastAPI(
    title="PubCast AI",
    version="5.5.0",
    description="Collaborative AI-Infused Virtual Production — Rear View Foresight LLC",
    lifespan=lifespan,
)

_cors_origins, _cors_credentials = _resolve_cors_origins()
app.add_middleware(CORSMiddleware,
    allow_origins=_cors_origins, allow_credentials=_cors_credentials,
    allow_methods=["*"], allow_headers=["*"])
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(BodySizeLimitMiddleware)
from modules.unicode_guard import UnicodeGuardMiddleware  # noqa: E402
app.add_middleware(UnicodeGuardMiddleware)
from modules.control_plane_guard import ControlPlaneGuardMiddleware  # noqa: E402
app.add_middleware(ControlPlaneGuardMiddleware)
app.mount("/2i-assets", StaticFiles(directory=str(Path(__file__).resolve().parent / "2i" / "2i-assets")), name="writers-room-assets")

if STATIC_DIR.exists() and any(STATIC_DIR.iterdir()):
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
_assets_files = list(ASSETS_DIR.iterdir()) if ASSETS_DIR.exists() else []
if _assets_files:
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

# Conversation Ownership is a separate transcript/archive authority. It is
# intentionally mounted outside the 2i manuscript and PubPartner memory seams.
from modules.conversation_routes import create_conversation_router
app.include_router(create_conversation_router(DATA_DIR))

# Foresight is the unified same-origin entry point for characters and distinct
# optional 2i utilities. It calls the authoritative managers; no copies.
from modules.foresight_gateway import create_foresight_gateway
app.include_router(create_foresight_gateway(lambda: bot_manager, lambda: hub))
# The authenticated local formats, workspace, and host tooling all belong to
# this Reach/Foresight process. They are not independent servers.
from modules.foresight_file_formats import create_file_format_router
from modules.foresight_workspace import create_workspace_router
from modules.foresight_host_tools import create_host_tools_router
app.include_router(create_file_format_router())
app.include_router(create_workspace_router(DATA_DIR))
_foresight_host_tools = create_host_tools_router(DATA_DIR)
app.include_router(_foresight_host_tools)

# Imported avatars: any GLB/glTF/OBJ/FBX, converted in the browser, stored as a
# canonical-height GLB. The server re-measures every upload (modules/avatar_imports.py).
from modules.avatar_imports import create_avatar_import_router  # noqa: E402
_avatar_imports = create_avatar_import_router(DATA_DIR)
app.include_router(_avatar_imports)
# Bella Faux Pas Studio progress (room, spot, who you walk as, your avatars, size tuning), per owner on this host.
from modules.studio_progress import create_studio_progress_router  # noqa: E402
app.include_router(create_studio_progress_router(DATA_DIR))
from modules.counter_layout import create_counter_layout_router  # noqa: E402
app.include_router(create_counter_layout_router(DATA_DIR))
# New PubPartner cartridges (pubpartner/cartridge.py init_cartridge), each registered as a friend; never the Alex vessel.
from modules.pubpartner_cartridges import create_pubpartner_cartridge_router  # noqa: E402
app.include_router(create_pubpartner_cartridge_router(DATA_DIR))
app.state.foresight_stop_sessions = _foresight_host_tools.stop_owned_sessions



# —
# Routes
# —

@app.get("/")
async def root():
    for candidate in [STATIC_DIR / "index.html", STATIC_DIR / "waiting_room.html"]:
        if candidate.exists():
            return FileResponse(candidate)
    return {"message": "PubCast AI v5.5", "health": "/health", "doctor": "/api/doctor"}


@app.get("/airlock")
async def serve_airlock():
    """Serve the waiting room / airlock UI."""
    airlock_path = STATIC_DIR / "waiting_room.html"
    if airlock_path.exists():
        return FileResponse(airlock_path)
    return {"error": "Airlock UI not found", "expected": str(airlock_path)}


@app.get("/health")
async def health():
    return {
        "status": "ok", "version": "5.5.0",
        "systems": {
            "hub":                hub is not None,
            "rooms":              len(room_manager.list_rooms()) if room_manager else 0,
            "bots":               len(bot_manager.list_configs()) if bot_manager else 0,
            "inference":          inference.status() if inference else None,
            "cameras":            len(cameras.list_sources()) if cameras else 0,
            "recording_profiles": len(recording.list_profiles()) if recording else 0,
            "governance":         governance is not None,
            "performance":        performance_manager is not None,
            "choreography":       choreo_controller is not None,
            "lighting":           lighting_engine is not None,
            "cricket":            cricket_keeper is not None,
            "byok":               byok_mgr is not None,
            "thinking_context":   _HAS_THINKING_CONTEXT,
            "ethereal":           _HAS_ETHEREAL and ethereal_mgr is not None,
            "evo":                _HAS_EVO and evo_orchestrator is not None,
            "vault":              _HAS_VAULT and vault is not None,
            "doctor":             _HAS_DOCTOR,
            # New subsystems
            "pubworld_router":    _HAS_PUBWORLD_ROUTER,
            "surfaces":           surface_manager is not None,
            "voxel":              voxel_asset_manager is not None,
            "voxel_bridge":       voxel_bridge is not None,
            "studio_control":     studio_control is not None,
            "unity_bridge":       unity_bridge is not None,
            "mocap":              mocap is not None,
            "orchestrator":       conv_orchestrator is not None,
            "room_conductor":     getattr(app.state, "room_conductor", None) is not None,
            "chat_rooms":         _HAS_CHAT_ROOMS,
            "recording":          recording is not None,
            "stt":                getattr(app.state, "stt_engine", None) is not None,
            "tts":                getattr(app.state, "tts_engine", None) is not None,
            # NEW: v5.5 Integration systems
            "production_log":     production_log is not None,
            "timeline":           timeline_player is not None,
            "waiting_room":       waiting_room_manager is not None,
            "hotspot_system":     hotspot_manager is not None,
        },
    }


@app.get("/api/state/production")
async def get_production_state():
    return hub.get_production_state() if hub else {}


@app.post("/api/state/production")
async def update_production_state(request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
    if not hub:
        raise HTTPException(503, "Hub not initialized")
    body    = await _json_dict(request)
    updated = hub.update_production_state(body)
    await hub.broadcast_system_event({"type": "production_state", "payload": updated})
    # Also push to PubWorld map clients
    if _HAS_PUBWORLD_ROUTER and push_production_state_to_pubworld:
        await push_production_state_to_pubworld(updated)
    return updated


@app.get("/api/state/user")
async def get_user_state(request: Request, identity: Dict[str, Any] = Depends(current_identity)):
    """Return persisted display name / avatar colour for the requesting client."""
    client_id = bound_actor(request=request, identity=identity, explicit_value=request.headers.get("X-Client-Id"), field_name="X-Client-Id", allow_privileged_override=False)
    user_file  = DATA_DIR / "users" / f"{storage_key(client_id)}.json"
    if user_file.exists():
        try:
            payload = read_json(user_file)
            if alex_little_one_enabled():
                from modules.alex_little_one.care_profile import normalize_care_profile
                payload["care_profile"] = normalize_care_profile(payload.get("care_profile"))
            else:
                payload.pop("care_profile", None)
            return payload
        except Exception as exc:
            logger.warning("user state read failed for %s: %s", client_id, exc)
    payload = {"user_id": client_id, "display_name": "", "avatar_color": "#00e0ff", "badge": ""}
    if alex_little_one_enabled():
        from modules.alex_little_one.care_profile import DEFAULT_CARE_PROFILE
        payload["care_profile"] = dict(DEFAULT_CARE_PROFILE)
    return payload


@app.post("/api/state/user")
async def set_user_state(request: Request, identity: Dict[str, Any] = Depends(current_identity)):
    """Persist display name / avatar colour for the requesting client."""
    body       = await _json_dict(request)
    client_id  = bound_actor(request=request, identity=identity, explicit_value=request.headers.get("X-Client-Id"), field_name="X-Client-Id", allow_privileged_override=False)
    user_file  = DATA_DIR / "users" / f"{storage_key(client_id)}.json"
    existing = read_json(user_file) if user_file.exists() else {}
    payload = dict(existing)
    payload.update({
        "user_id":      client_id,
        "display_name": str(body.get("display_name", payload.get("display_name", "")))[:64],
        "avatar_color": str(body.get("avatar_color", payload.get("avatar_color", "#00e0ff")))[:20],
        "badge":        str(body.get("badge", payload.get("badge", "")))[:32],
    })
    if alex_little_one_enabled():
        from modules.alex_little_one.care_profile import normalize_care_profile
        if "care_profile" in body:
            payload["care_profile"] = normalize_care_profile(body.get("care_profile"), payload.get("care_profile"))
        else:
            payload["care_profile"] = normalize_care_profile(payload.get("care_profile"))
    write_json(user_file, payload)
    if hub:
        await hub.broadcast_presence_update(client_id, payload["display_name"])
    response_payload = dict(payload)
    if not alex_little_one_enabled():
        response_payload.pop("care_profile", None)
    return {"ok": True, **response_payload}


@app.post("/api/upload")
async def upload_file(request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
    """Accept a multipart file upload and save it to data/imports/."""
    from fastapi import UploadFile, File, Form
    import shutil, mimetypes
    try:
        form   = await request.form()
        upload = form.get("file")
        target = str(form.get("target", "")).strip()
        if not upload or not hasattr(upload, "filename"):
            raise HTTPException(400, "No file provided")
        safe_name = sanitize_filename(upload.filename or "upload") or "upload"
        dest_dir  = DATA_DIR / "imports"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = unique_child_path(dest_dir, safe_name)
        with dest_path.open("wb") as out:
            shutil.copyfileobj(upload.file, out)
        logger.info("Upload received: %s — %s (target=%s)", upload.filename, dest_path, target)
        return {"ok": True, "filename": safe_name, "target": target, "size": dest_path.stat().st_size}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Upload error: %s", exc)
        raise HTTPException(500, str(exc))


@app.get("/api/bots")
async def list_bots(identity: Dict[str, Any] = Depends(current_identity)):
    if not bot_manager:
        return []
    configs = bot_manager.list_configs()
    if identity.get("authenticated") and identity.get("role") in {"mod", "admin", "owner"}:
        return [cfg.model_dump() for cfg in configs]
    # Ordinary participants need names/models, not private character prompts,
    # key variable names, provider settings or owner identifiers.
    return [{"bot_id": cfg.bot_id, "name": cfg.name, "provider": cfg.provider.value,
             "model": cfg.model, "rooms": list(cfg.rooms)} for cfg in configs]


@app.post("/api/bots")
async def register_bot(request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
    if not bot_manager:
        raise HTTPException(503, "BotManager not initialized")
    body   = await _json_dict(request)
    config = BotConfig(**body)
    bot_manager.upsert_config(config)
    return {"ok": True, "bot_id": config.bot_id}


@app.post("/api/bots/{bot_id}/chat")
async def chat_with_bot(bot_id: str, request: Request,
                        identity: Dict[str, Any] = Depends(current_identity)):
    """
    Send a message directly to a named bot and get a reply.
    This is the primary interface for talking to characters.

    Body: { "message": str, "room_id": str, "user_id": str }
    """
    if not identity.get("authenticated"):
        raise HTTPException(401, "Sign in to use private character chat")
    if not bot_manager:
        raise HTTPException(503, "BotManager not initialized")
    body = await _json_dict(request)
    message = body.get("message")
    room_id = body.get("room_id", "studio")
    user_id = bound_actor(request=request, identity=identity,
                          explicit_value=body.get("user_id"), field_name="user_id",
                          allow_privileged_override=False)

    if not message:
        raise HTTPException(400, "message is required")

    cfg = bot_manager.get_config(bot_id)
    if cfg is None:
        raise HTTPException(404, f"Bot '{bot_id}' not found")

    from modules.character_service import speak_to_character
    return await speak_to_character(bot_manager, hub, bot_id=bot_id,
                                    message=message, room_id=room_id, user_id=user_id)


@app.post("/api/bots/{bot_id}/speak")
async def bot_speak(
    bot_id: str,
    request: Request,
    identity: Dict[str, Any] = Depends(require_role("mod")),
):
    """Post text verbatim into a room as a named bot; no LLM call.

    This is a control-plane impersonation surface, so production auth uses the
    same mod boundary as bot registration/deletion. Relaxed local mode remains
    backward compatible through ``require_role``.
    """
    if not bot_manager:
        raise HTTPException(503, "BotManager not initialized")
    body = await _json_dict(request)
    room = (body.get("room") or "studio").strip()
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    cfg = bot_manager.get_config(bot_id)
    if cfg is None:
        raise HTTPException(404, f"Bot '{bot_id}' not found")
    if hub is None:
        raise HTTPException(503, "Hub not initialized")
    bot_uid = bot_manager.bot_user_id(bot_id)
    await hub.post_chat_message(room, bot_uid, text)
    return {"ok": True, "bot_id": bot_id, "room": room, "text": text}


async def _requested_partner_turn(bot_id, request, identity, required):
    from modules.auth import role_gte
    if not identity.get('authenticated') or not role_gte(identity.get('role', 'guest'), 'mod'):
        raise HTTPException(403, 'Authenticated host required')
    if bot_manager is None:
        raise HTTPException(503, 'BotManager not initialized')
    body = await _json_dict(request)
    room = str(body.get('room') or 'studio').strip()
    hint = str(body.get('direction') or '').strip()
    if len(hint) > 8000:
        raise HTTPException(400, 'Direction exceeds 8000 characters')
    try:
        outcome = await bot_manager.request_turn(bot_id, room, hint,
            actor=identity['user_id'], required=required)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {'ok': outcome['state'] == 'completed', **outcome}


@app.post('/api/bots/{bot_id}/invite')
async def invite_partner(bot_id: str, request: Request, identity=Depends(current_identity)):
    return await _requested_partner_turn(bot_id, request, identity, required=False)


@app.post('/api/bots/{bot_id}/request-turn')
async def require_partner_turn(bot_id: str, request: Request, identity=Depends(current_identity)):
    # Existing /speak retains its exact-text contract. This requests generation.
    return await _requested_partner_turn(bot_id, request, identity, required=True)


@app.get('/api/bots/{bot_id}/turn-requests/{request_id}')
async def partner_turn_receipt(bot_id: str, request_id: str, identity=Depends(current_identity)):
    from modules.auth import role_gte
    if not identity.get('authenticated') or not role_gte(identity.get('role', 'guest'), 'mod'):
        raise HTTPException(403, 'Authenticated host required')
    if bot_manager is None:
        raise HTTPException(503, 'BotManager not initialized')
    item = bot_manager.turn_requests.get(request_id)
    if item is None or item['bot_id'] != bot_id:
        raise HTTPException(404, 'Turn request not found')
    return item


@app.get("/api/bots/{bot_id}/status")
async def bot_status(bot_id: str, identity: Dict[str, Any] = Depends(current_identity)):
    """Check a specific bot's config and whether it has a key configured."""
    if not bot_manager:
        raise HTTPException(503, "BotManager not initialized")
    cfg = bot_manager.get_config(bot_id)
    if cfg is None:
        raise HTTPException(404, f"Bot '{bot_id}' not found")
    has_key = bool(os.getenv(cfg.api_key_env, "").strip()) if cfg.api_key_env else False
    metadata = {"bot_id": cfg.bot_id, "name": cfg.name,
                "provider": cfg.provider.value, "model": cfg.model,
                "rooms": list(cfg.rooms)}
    # Keys and deployment variable names are privileged diagnostic information.
    if identity.get("authenticated") and identity.get("role") in {"mod", "admin", "owner"}:
        metadata.update({"has_key": has_key, "key_env": cfg.api_key_env})
    return metadata
    if bot_manager:
        bot_manager.delete_config(bot_id)
    return {"ok": True}


@app.get("/api/rooms")
async def list_rooms():
    return room_manager.to_dict() if room_manager else {"rooms": []}


@app.post("/api/inference/generate")
async def generate_text(request: Request, identity: Dict[str, Any] = Depends(current_identity)):
    if not inference:
        raise HTTPException(503, "Inference not initialized")
    body = await _json_dict(request)
    return await inference.generate_text(
        prompt          = body.get("prompt", ""),
        temperature     = body.get("temperature", 0.7),
        max_tokens      = body.get("max_tokens", 256),
        requested_route = body.get("route", body.get("role", "auto")),
        task_type       = body.get("task_type", ""),
        user_facing     = body.get("user_facing"),
        allow_fallback  = body.get("allow_fallback"),
    )


@app.post("/api/inference/tts")
async def text_to_speech(request: Request, identity: Dict[str, Any] = Depends(current_identity)):
    if not inference:
        raise HTTPException(503, "Inference not initialized")
    body = await _json_dict(request)
    return await inference.synthesize_speech(
        text  = body.get("text", ""),
        voice = body.get("voice", "default"),
    )


@app.get("/api/inference/status")
async def inference_status():
    """Report inference configuration and availability without turning diagnostics into a 500."""
    if not inference:
        return {
            "available": False,
            "reason": "Inference not initialized",
            "profile": None,
            "available_profiles": [],
        }
    try:
        payload = inference.status()
        payload.setdefault("available", True)
        return payload
    except Exception as exc:
        return {
            "available": False,
            "error": str(exc),
            "profile": None,
            "available_profiles": [],
        }


# ── STT: speech → text ────────────────────────────────────────────────────────

@app.post("/api/stt/transcribe")
async def stt_transcribe(request: Request):
    """
    Transcribe audio to text using faster-whisper.

    Accepts raw audio bytes (multipart or raw body).
    Content-Type hints used to pick ffmpeg decode path.

    Returns: {ok, text, language, duration, latency_ms, segments}
    """
    if stt_engine is None:
        raise HTTPException(503,
            "STT engine not loaded. "
            "Install: pip install faster-whisper  "
            "then restart PubCast."
        )
    content_type = request.headers.get("content-type", "audio/webm")

    # Multipart form upload (from mic_processor.js FormData)
    if "multipart" in content_type:
        form = await request.form()
        file_field = form.get("audio") or form.get("file")
        if file_field is None:
            raise HTTPException(400, "No audio field in form data")
        audio_bytes = await file_field.read()
        mime = file_field.content_type or "audio/webm"
    else:
        # Raw body — Content-Type IS the mime type
        audio_bytes = await request.body()
        mime = content_type.split(";")[0].strip() or "audio/webm"

    if not audio_bytes:
        raise HTTPException(400, "Empty audio data")

    # Optional JSON params in query string
    language = request.query_params.get("language")
    prompt   = request.query_params.get("prompt")  # e.g. "PubCast studio"

    result = await stt_engine.transcribe(
        audio_data = audio_bytes,
        mime_type  = mime,
        language   = language,
        prompt     = prompt,
    )

    if not result.get("ok"):
        raise HTTPException(500, result.get("error", "Transcription failed"))

    return result


@app.get("/api/stt/status")
async def stt_status():
    if stt_engine is None:
        return {"available": False, "reason": "faster-whisper not installed"}
    return {"available": True, **stt_engine.status()}


# ── TTS: text → voice ─────────────────────────────────────────────────────────

@app.post("/api/tts/synthesize")
async def tts_synthesize(request: Request):
    """
    Synthesize text to speech using XTTS-v2 (voice-cloned per character).

    Body: {
        text:         str,
        character_id: str,   "jeremy" | "pete" | "sir_purfluous" | "sheila" | "default"
        language:     str,   default "en"
        speed:        float, default 1.0  (0.7–1.5)
    }

    Returns WAV audio bytes with Content-Type: audio/wav.
    Voice reference files go in data/voices/{character_id}.wav
    """
    if tts_engine is None:
        raise HTTPException(503,
            "TTS engine not loaded. "
            "Install: pip install TTS  "
            "then restart PubCast."
        )
    body = await _json_dict(request)
    text         = (body.get("text") or "").strip()
    character_id = (body.get("character_id") or "default").strip()
    language     = (body.get("language") or "en").strip()
    speed        = float(body.get("speed") or 1.0)

    if not text:
        raise HTTPException(400, "text is required")

    result = await tts_engine.synthesize(
        text         = text,
        character_id = character_id,
        language     = language,
        speed        = speed,
    )

    if not result.get("ok"):
        raise HTTPException(500, result.get("error", "Synthesis failed"))

    from fastapi.responses import Response
    return Response(
        content      = result["audio"],
        media_type   = result.get("mime_type", "audio/wav"),
        headers      = {
            "X-Character":  character_id,
            "X-Engine":     result.get("engine", "unknown"),
            "X-Latency-Ms": str(result.get("latency_ms", 0)),
            "X-Duration":   str(round(result.get("duration", 0), 2)),
        }
    )


@app.get("/api/tts/voices")
async def tts_voices():
    """List which characters have voice reference files ready."""
    if tts_engine is None:
        return {"available": False}
    return {
        "available": True,
        "voices":    tts_engine.list_voices(),
        "voices_dir": str(tts_engine.voices_dir),
        "hint": "Record 6+ seconds of each character's voice and save as data/voices/{id}.wav",
    }


@app.get("/api/tts/status")
async def tts_status():
    if tts_engine is None:
        return {"available": False, "reason": "Coqui TTS not installed"}
    return {"available": True, **tts_engine.status()}


@app.get("/api/lighting/presets")
async def get_lighting_presets():
    if not lighting_engine:
        return {"available": False, "presets": []}
    presets = list_lighting_presets() if list_lighting_presets else []
    return {"available": True, "presets": presets}


@app.get("/api/lighting/active")
async def get_active_lighting():
    """Current lighting state -- what's actually live right now, not just the preset catalog."""
    if not lighting_engine:
        return {"available": False, "state": None}
    return {"available": True, "state": lighting_engine.serialize()}


@app.post("/api/lighting/apply")
async def apply_lighting_preset(request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
    if not lighting_engine:
        raise HTTPException(503, "Lighting engine not initialized")
    body = await _json_dict(request)
    preset = body.get("preset", "normal")
    try:
        lighting_engine.apply_preset(preset)
        # A preset can be validly applied in partial/test initialization before
        # the Hub exists. Broadcasting is supplemental; do not turn a successful
        # lighting state change into a false API failure when hub is unavailable.
        if hub is not None:
            await hub.broadcast_system_event({"type": "lighting_preset", "payload": {"preset": preset}})
        return {"ok": True, "preset": preset}
    except Exception as exc:
        raise HTTPException(400, str(exc))


@app.get("/api/evo/status")
async def evo_status():
    if not _HAS_EVO or evo_orchestrator is None:
        return {"available": False}
    try:
        s = evo_orchestrator.get_status() if hasattr(evo_orchestrator, "get_status") else {}
        return {"available": True, **s}
    except Exception as exc:
        return {"available": False, "error": str(exc)}


@app.get("/api/doctor")
async def doctor_report():
    if not _HAS_DOCTOR or _run_doctor_fn is None:
        return {"available": False, "message": "Doctor module not loaded"}
    try:
        return _run_doctor_fn(DATA_DIR)
    except Exception as exc:
        return {"available": False, "error": str(exc)}


@app.get("/api/doctor/launch-gate")
async def doctor_launch_gate():
    """Return only the launch-gate sub-report — used by doctor.html to decide
    whether to show a GO / NO-GO banner without fetching the full report."""
    if not _HAS_DOCTOR or _run_launch_gate_fn is None:
        return {"allowed": False, "reason": "Doctor module not loaded", "blocking_checks": ["doctor_module_unavailable"]}
    try:
        return _run_launch_gate_fn(DATA_DIR)
    except Exception as exc:
        return {"allowed": False, "reason": str(exc), "blocking_checks": []}


# — Choreography routes —

@app.get("/api/choreo/actions")
async def choreo_list_actions():
    """Return the full action catalogue (label, duration, category) for the UI."""
    if choreo_controller is None:
        # Degrade gracefully: return the static default table so the UI still renders
        from modules.choreography_controller import DEFAULT_ACTIONS
        return {"available": False, "actions": DEFAULT_ACTIONS}
    return {"available": True, "actions": choreo_controller.list_actions()}


@app.post("/api/choreo/start")
async def choreo_start(request: Request):
    """Start a choreography sequence. Body: {room, tick_hz, avatars, steps, constraints}"""
    if choreo_controller is None:
        raise HTTPException(503, "Choreography controller not initialized")
    body = await _json_dict(request)
    room        = body.get("room", "studio")
    steps       = body.get("steps", [])
    avatars     = body.get("avatars")
    tick_hz     = body.get("tick_hz")
    constraints = body.get("constraints")
    if not steps:
        raise HTTPException(400, "steps is required")
    result = await choreo_controller.start(
        room=room, avatars=avatars, steps=steps,
        tick_hz=tick_hz, constraints=constraints,
    )
    return result


@app.post("/api/choreo/stop")
async def choreo_stop():
    if choreo_controller is None:
        raise HTTPException(503, "Choreography controller not initialized")
    await choreo_controller.stop()
    return {"ok": True, "stopped": True}



@app.get("/api/choreo/constraints")
async def choreo_get_constraints():
    """Return current MotionConstraints as a plain dict."""
    if choreo_controller is None:
        from dataclasses import asdict
        from modules.choreography_controller import MotionConstraints
        return {"available": False, "constraints": asdict(MotionConstraints())}
    return {"available": True, "constraints": choreo_controller.get_constraints()}


@app.post("/api/choreo/constraints")
async def choreo_set_constraints(request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
    """Patch MotionConstraints fields.
    Accepts either a flat body  { enabled, max_horizontal_speed, — }
    or the wrapped shape        { constraints: { enabled, — } }
    that stage_panoramic.html sends.
    """
    if choreo_controller is None:
        raise HTTPException(503, "Choreography controller not initialised")
    body = await _json_dict(request)
    # Unwrap nested { constraints: {...} } if present
    patch = body.get("constraints", body) if isinstance(body, dict) else body
    updated = choreo_controller.set_constraints(patch)
    return {"ok": True, "constraints": updated}


@app.post("/api/choreo/cue")
async def choreo_cue_action(request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
    """Fire an action cue for an avatar.
    Body: { room, avatar_id, action, intensity?, duration?, props? }
    Broadcasts an avatar_action_cue WS event to all room subscribers.
    """
    if choreo_controller is None:
        raise HTTPException(503, "Choreography controller not initialised")
    body = await _json_dict(request)
    room      = body.get("room", "studio")
    avatar_id = body.get("avatar_id", "")
    action    = body.get("action", "")
    if not avatar_id or not action:
        raise HTTPException(400, "avatar_id and action are required")
    try:
        result = await choreo_controller.cue_action(
            room      = room,
            avatar_id = avatar_id,
            action    = action,
            intensity = float(body.get("intensity", 1.0)),
            duration  = body.get("duration"),
            props     = body.get("props"),
        )
        return {"ok": True, "cue": result}
    except ValueError as exc:
        raise HTTPException(400, str(exc))


# — Performance profile route —

@app.get("/api/performance/status")
async def performance_status():
    """Return the active performance profile and its settings.
    stage_panoramic.html uses this to gate high-fidelity render features."""
    if performance_manager is None:
        return {
            "available": False,
            "profile": "medium",
            "settings": {"architect_enabled": True, "max_fps": 30, "shadows": True},
        }
    snap = performance_manager.current_profile_snapshot()
    return {"available": True, **snap}


# —
# Static page routes — serve pages from the pubworld build
# —

TEMPLATE_PAGES = {
    "analytics.html",
    "bar.html",
    "control.html",
    "dressing.html",
    "dressing_foundry.html",
    "gallery.html",
}
templates = Jinja2Templates(directory=str(STATIC_DIR))

def _page(name: str, request: Request):
    """Return a rendered template for Jinja pages or a raw static file otherwise."""
    p = STATIC_DIR / name
    if not p.exists():
        raise HTTPException(404, f"Page not found: {name}")
    if name in TEMPLATE_PAGES:
        return templates.TemplateResponse(request, name)
    return FileResponse(p)


@app.get("/foresight", include_in_schema=False)
@app.get("/counter", include_in_schema=False)
async def page_foresight(request: Request):
    return _page("foresight.html", request)


# The Foresight Counter: the tray system with physics, the fan and the tray menus (foresight_counter.html). It runs
# beside the earlier page until it takes over /foresight.
@app.get("/foresight-counter", include_in_schema=False)
async def page_foresight_counter(request: Request):
    return _page("foresight_counter.html", request)


@app.get("/login", include_in_schema=False)
async def page_login(request: Request):
    return _page("login.html", request)

@app.get("/control",         include_in_schema=False) 
async def page_control(request: Request):        return _page("control.html", request)

@app.get("/studio-control",  include_in_schema=False)
async def page_studio_control(request: Request): return _page("studio_control_room.html", request)

@app.get("/audio-console", include_in_schema=False)
async def page_audio_console(request: Request): return _page("audio_console.html", request)

@app.get("/director-console", include_in_schema=False)
async def page_director_console(request: Request): return _page("director_console.html", request)

@app.get("/safe-console", include_in_schema=False)
async def page_safe_console(request: Request): return _page("safe_console.html", request)

@app.get("/recovery", include_in_schema=False)
async def page_recovery_console(request: Request): return _page("safe_console.html", request)

@app.get("/director-switcher", include_in_schema=False)
async def page_director_switcher(request: Request): return _page("director_switcher.html", request)

@app.get("/avatar-import", include_in_schema=False)
async def page_avatar_import(request: Request): return _page("avatar_import.html", request)

@app.get("/avatar-walk-test", include_in_schema=False)
async def page_avatar_walk_test(request: Request): return _page("avatar_walk_test.html", request)

@app.get("/data/avatars/manifest.json", include_in_schema=False)
async def avatar_manifest_file():
    manifest_path = DATA_DIR / "avatars" / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(404, "Avatar manifest not found")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return FileResponse(manifest_path, media_type="application/json")
    # Imported avatars appear as one more pack; the curated file is never rewritten.
    imported = _avatar_imports.store.manifest_pack()
    if imported["assets"]:
        manifest["packs"] = [p for p in manifest.get("packs", []) if p.get("pack_id") != "imported"] + [imported]
    return JSONResponse(manifest)

@app.get("/dressing",        include_in_schema=False)
async def page_dressing(request: Request):       return _page("dressing.html", request)

@app.get("/dressing-foundry",include_in_schema=False)
async def page_dressing_foundry(request: Request): return _page("dressing_foundry.html", request)

@app.get("/pubworld-stage",  include_in_schema=False)
async def page_pubworld_stage(request: Request): return _page("pubworld_stage.html", request)

@app.get("/builder",         include_in_schema=False)
async def page_builder(request: Request):        return _page("builder.html", request)

@app.get("/launch",          include_in_schema=False)
async def page_launch(request: Request):         return _page("launch.html", request)

@app.get("/bar",             include_in_schema=False)
async def page_bar(request: Request):            return _page("bar.html", request)

@app.get("/gallery",         include_in_schema=False)
async def page_gallery(request: Request):        return _page("gallery.html", request)

@app.get("/analytics",       include_in_schema=False)
async def page_analytics(request: Request):      return _page("analytics.html", request)

# Compatibility aliases for legacy/front-end navigation paths that several
# bundled pages still use directly. Keep these small and explicit so the UI
# stops shipping dead links during static navigation flows.
@app.get("/world",           include_in_schema=False)
async def page_world(request: Request):          return _page("world.html", request)

# Bella Faux Pas Studio, the game section of PubCast: the walkable 2.5D world. The same rooms and PubWorld backend as
# /world, walked on each picture's own floor at its own camera scale (static/world_walk.html, docs/WORLD_WALK.md).
# ?live=<room id> or ?view=<room>/<view> picks where to start; with neither it starts in the dressing room.
@app.get("/walk",            include_in_schema=False)
@app.get("/world-walk",      include_in_schema=False)
async def page_world_walk(request: Request):     return _page("world_walk.html", request)

@app.get("/stage",           include_in_schema=False)
async def page_stage(request: Request):          return _page("stage.html", request)

@app.get("/studio",          include_in_schema=False)
async def page_studio(request: Request):         return _page("stage_panoramic.html", request)

@app.get("/byok",            include_in_schema=False)
async def page_byok(request: Request):           return _page("byok.html", request)

@app.get("/api/byok")
async def byok_root_info():
    """Compatibility endpoint for older pages that probe /api/byok directly."""
    return {
        "ok": True,
        "mounted": byok_mgr is not None,
        "catalog": "/api/byok/catalog",
        "hardware": "/api/byok/hardware",
        "models": "/api/byok/models",
        "ollama_status": "/api/byok/ollama/status",
    }

@app.get("/map",             include_in_schema=False)
async def page_map(request: Request):            return _page("map.html", request)


# —
# PubWorld Scenes API
# —

@app.get("/api/pubworld/scenes")
async def pw_list_scenes():
    if not _HAS_PUBWORLD_SCENES:
        return {"scenes": []}
    return {"scenes": [s.model_dump() for s in list_scenes(DATA_DIR)]}

@app.post("/api/pubworld/scenes")
async def pw_create_scene(request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
    if not _HAS_PUBWORLD_SCENES:
        raise HTTPException(503, "PubWorld scene manager not available")
    body = await _json_dict(request)
    name = body.get("name", "Untitled Scene")
    desc = body.get("description", "")
    scene = create_scene(DATA_DIR, name=name, description=desc)
    return {"ok": True, "scene": scene.model_dump()}

@app.get("/api/pubworld/scenes/{scene_id}")
async def pw_get_scene(scene_id: str):
    if not _HAS_PUBWORLD_SCENES:
        raise HTTPException(503, "PubWorld scene manager not available")
    scene = get_scene(DATA_DIR, scene_id)
    if not scene:
        raise HTTPException(404, f"Scene not found: {scene_id}")
    return scene.model_dump()

@app.get("/api/pubworld/props")
async def pw_list_props(scene_id: str | None = None):
    if list_props is None:
        return {"props": []}
    props = list_props(DATA_DIR, scene_id=scene_id)
    return {"props": [p.model_dump() for p in props]}


def _generated_blocks_to_pubworld_blocks(blocks: Any) -> List[Dict[str, Any]]:
    """Normalize generated voxel block shapes into PubWorld Block payloads."""
    rows: List[Dict[str, Any]] = []
    for block in blocks or []:
        if not isinstance(block, dict):
            continue
        raw_pos = block.get("position")
        if isinstance(raw_pos, (list, tuple)) and len(raw_pos) >= 3:
            x, y, z = raw_pos[:3]
        else:
            x = block.get("x", 0)
            y = block.get("y", 0)
            z = block.get("z", 0)
        try:
            row = {
                "x": int(round(float(x))),
                "y": int(round(float(y))),
                "z": int(round(float(z))),
                "kind": str(block.get("kind") or block.get("type") or "cube"),
            }
        except (TypeError, ValueError):
            continue
        color = block.get("color")
        if color:
            row["color"] = str(color)
        texture = block.get("texture")
        if texture:
            row["texture"] = str(texture)
        rows.append(row)
    return rows


def _pubworld_blocks_to_stage_voxels(blocks: Any) -> List[List[int]]:
    voxels: List[List[int]] = []
    for block in blocks or []:
        if isinstance(block, dict):
            x = block.get("x", 0)
            y = block.get("y", 0)
            z = block.get("z", 0)
        else:
            x = getattr(block, "x", 0)
            y = getattr(block, "y", 0)
            z = getattr(block, "z", 0)
        try:
            voxels.append([int(x), int(y), int(z)])
        except (TypeError, ValueError):
            continue
    return voxels


@app.post("/api/pubworld/props")
async def pw_create_prop(request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
    if create_prop is None:
        raise HTTPException(503, "PubWorld block manager not available")
    body = await _json_dict(request)
    scene_id = str(body.get("scene_id") or "scene_default")
    label = str(body.get("label") or body.get("name") or "Voxel Prop")
    description = str(body.get("description") or "")
    blocks = _generated_blocks_to_pubworld_blocks(body.get("blocks") or body.get("voxels") or [])
    prop = create_prop(
        DATA_DIR,
        scene_id=scene_id,
        label=label,
        description=description,
        blocks=blocks,
        variants=body.get("variants"),
    )
    return {"ok": True, "prop": prop.model_dump(), "voxels": _pubworld_blocks_to_stage_voxels(prop.blocks)}


@app.post("/api/pubworld/props/generate")
async def pw_generate_prop(request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
    if create_prop is None:
        raise HTTPException(503, "PubWorld block manager not available")
    body = await _json_dict(request)
    prompt = str(body.get("prompt") or "").strip()
    if not prompt:
        raise HTTPException(400, "prompt required")
    scene_id = str(body.get("scene_id") or "scene_default")
    provider = str(body.get("provider") or "pubworld_rules")

    provider_used = "pubworld_rules"
    label = prompt[:64] or "Voxel Prompt"
    generated_blocks: List[Dict[str, Any]] = []
    if _HAS_VOXEL and voxel_generate is not None and provider != "pubworld_rules":
        result, provider_used = await voxel_generate(prompt, provider=provider)
        if result:
            label, generated_blocks = result
    if not generated_blocks and pubworld_generate_from_prompt is not None:
        label, rule_blocks = pubworld_generate_from_prompt(prompt)
        generated_blocks = [b.model_dump() if hasattr(b, "model_dump") else dict(b) for b in rule_blocks]
        provider_used = "pubworld_rules"

    blocks = _generated_blocks_to_pubworld_blocks(generated_blocks)
    prop = create_prop(
        DATA_DIR,
        scene_id=scene_id,
        label=str(body.get("label") or label),
        description=prompt,
        blocks=blocks,
    )
    return {
        "ok": True,
        "label": label,
        "provider": provider_used,
        "count": len(blocks),
        "blocks": blocks,
        "voxels": _pubworld_blocks_to_stage_voxels(blocks),
        "prop": prop.model_dump(),
    }


@app.get("/api/pubworld/generate/status")
async def pw_generate_status():
    """Generation is synchronous (no background job queue) — this reports
    which generator backends are actually available rather than a fake
    job-progress payload."""
    return {
        "async": False,
        "local_available": _HAS_PUBWORLD_BLOCKS and pubworld_generate_from_prompt is not None,
        "cloud_available": _HAS_VOXEL and voxel_generate is not None,
    }


@app.get("/api/pubworld/prototypes")
async def pw_list_prototypes():
    if list_prototypes is None:
        return {"prototypes": []}
    return {"prototypes": [p.model_dump() for p in list_prototypes(DATA_DIR)]}


@app.post("/api/pubworld/prototypes")
async def pw_save_prototype(request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
    if save_prototype is None:
        raise HTTPException(503, "PubWorld prototype recognition not available")
    body = await _json_dict(request)
    label = str(body.get("label") or "Prototype")
    description = str(body.get("description") or "")
    blocks = _generated_blocks_to_pubworld_blocks(body.get("blocks") or [])
    proto = save_prototype(DATA_DIR, label=label, description=description, blocks=blocks)
    return {"ok": True, "prototype": proto.model_dump()}


@app.post("/api/pubworld/recognize")
async def pw_recognize_prop(request: Request):
    """Match a set of placed blocks against saved prototypes (rotation-aware)."""
    if recognize_prop is None or list_prototypes is None:
        raise HTTPException(503, "PubWorld prototype recognition not available")
    body = await _json_dict(request)
    blocks = _generated_blocks_to_pubworld_blocks(body.get("blocks") or body.get("voxels") or [])
    if not blocks:
        raise HTTPException(400, "blocks required")
    match = recognize_prop(blocks, list_prototypes(DATA_DIR))
    return {"ok": True, "match": match}


@app.post("/api/visual-patch/approve")
async def visual_patch_approve(request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
    """Persist an approved Visual Patch Kit proposal through PubWorld/voxel storage."""
    if not _HAS_VISUAL_PATCH_BRIDGE or submit_approved_visual_patch is None:
        raise HTTPException(503, "Visual Patch approval bridge not available")
    body = await _json_dict(request)
    try:
        result = submit_approved_visual_patch(
            DATA_DIR,
            body,
            create_prop_func=create_prop,
            save_voxel_set_func=save_voxel_set,
            stage_voxels_func=_pubworld_blocks_to_stage_voxels,
        )
        if blackbox_witness is not None:
            blackbox_witness.record_event("visual_patch.approved", source="visual_patch", actor=str(identity.get("user_id") or "director"), data={"patch_kind": result.get("patch_kind"), "target": result.get("target"), "scene_id": body.get("scene_id", "scene_default"), "auto_approved": bool(result.get("approval", {}).get("auto_approved"))})
        return result
    except VisualPatchApprovalError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        logger.exception("Visual Patch approval submission failed")
        raise HTTPException(500, str(exc))


@app.get("/api/pubworld/builder/presets")
async def pw_list_builder_presets():
    if list_builder_presets is None:
        return {"presets": []}
    return {"presets": [p.model_dump() for p in list_builder_presets(DATA_DIR)]}


@app.post("/api/pubworld/builder/presets")
async def pw_save_builder_preset(request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
    if save_builder_preset is None:
        raise HTTPException(503, "PubWorld builder presets not available")
    body = await _json_dict(request)
    name = str(body.get("name") or "Builder Preset")
    blocks = _generated_blocks_to_pubworld_blocks(body.get("blocks") or [])
    preset = save_builder_preset(DATA_DIR, name=name, blocks_data=blocks, links_data=body.get("links"))
    return {"ok": True, "preset": preset.model_dump(), "voxels": _pubworld_blocks_to_stage_voxels(preset.blocks)}


# —
# Surfaces API
# —

@app.get("/api/surfaces")
async def list_surfaces_ep(room_id: str = None):
    if surface_manager is None:
        return {"surfaces": []}
    surfaces = await surface_manager.list_surfaces(room_id=room_id)
    return {"surfaces": [s.model_dump() for s in surfaces]}

@app.post("/api/surfaces")
async def create_surface_ep(request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
    if surface_manager is None:
        raise HTTPException(503, "Surface manager not available")
    body = await _json_dict(request)
    s = await surface_manager.create_surface(
        room_id=body.get("room_id", "studio"),
        label=body.get("label", "Screen"),
        kind=body.get("kind", "custom"),
        quad=body.get("quad"),
        creator_id=bound_actor(request=request, identity=identity, explicit_value=body.get("creator_id"), field_name="creator_id"),
        media_mode=body.get("media_mode", "video"),
    )
    return {"ok": True, "surface": s.model_dump()}


# —
# Projects / autosave API
# —

@app.get("/api/projects/{slug}/autosaves")
async def list_project_autosaves(slug: str):
    if not _HAS_PROJECTS:
        return {"autosaves": []}
    return {"autosaves": list_autosaves(DATA_DIR, slug)}

@app.post("/api/projects/{slug}/autosaves")
async def save_project_autosave(slug: str, request: Request, identity: Dict[str, Any] = Depends(current_identity)):
    if not _HAS_PROJECTS or save_autosave_snapshot is None:
        raise HTTPException(503, "Project autosave system unavailable")
    body = await _json_dict(request)
    session_id = body.get('session_id')
    if session_id:
        try:
            body['session_credits'] = session_runtime.session_credit_block(DATA_DIR, session_id)
        except Exception:
            pass
    save_path = await save_autosave_snapshot(DATA_DIR, slug, body)
    saved = json.loads(save_path.read_text(encoding="utf-8"))
    return {
        "ok": True,
        "path": str(save_path),
        "save_manifest": saved.get("save_manifest", {}),
        "project_identity": saved.get("project_identity", {}),
        "session_credits": saved.get("session_credits", {}),
    }

@app.post("/api/projects/{slug}/savefile/preview")
async def preview_project_savefile(slug: str, request: Request, identity: Dict[str, Any] = Depends(current_identity)):
    body = await _json_dict(request)
    wrapped = attach_save_metadata(slug=slug, payload=body, save_kind="manual_save")
    return {"ok": True, "savefile": wrapped}


# —
# Voxel API
# —

@app.get("/api/projects/{slug}/credits/export")
async def export_project_credits(slug: str, mode: str = 'industry_standard'):
    return {"ok": True, **credits_export.generate_credits(DATA_DIR, slug, mode=mode)}



@app.get("/api/projects/{slug}/credits/crawl.txt")
async def export_project_credit_crawl(slug: str, mode: str = 'industry_standard'):
    data = credits_export.generate_credits(DATA_DIR, slug, mode=mode)
    content = credits_export.render_credit_crawl(data)
    return JSONResponse({'ok': True, 'filename': f'{slug}_credits.txt', 'content': content})

@app.get("/api/voxel/assets")
async def voxel_list_assets(category: str = None):
    if voxel_asset_manager is None:
        return {"available": False, "assets": []}
    if category:
        assets = voxel_asset_manager.get_assets_by_category(category)
    else:
        assets = voxel_asset_manager.get_all_assets()
    return {"available": True, "count": len(assets),
            "assets": [a.to_dict() for a in assets]}

@app.get("/api/voxel/assets/search")
async def voxel_search_assets(q: str = ""):
    if voxel_asset_manager is None:
        return {"assets": []}
    results = voxel_asset_manager.search_assets(q)
    return {"assets": [a.to_dict() for a in results]}

@app.post("/api/voxel/generate")
async def voxel_generate_ep(request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
    """Generate voxel blocks from a text prompt, using the local voxel path by default."""
    if not _HAS_VOXEL or voxel_generate is None:
        raise HTTPException(503, "Voxel generator not available")
    body = await _json_dict(request)
    prompt = body.get("prompt", "").strip()
    if not prompt:
        raise HTTPException(400, "prompt required")
    provider = body.get("provider", "local")
    try:
        result, provider_used = await voxel_generate(prompt, provider=provider)
        if not result:
            raise HTTPException(502, "Voxel generator returned no blocks")
        label, blocks = result
        voxels = _pubworld_blocks_to_stage_voxels(_generated_blocks_to_pubworld_blocks(blocks))
        return {
            "ok": True,
            "label": label,
            "provider": provider_used,
            "blocks": blocks,
            "voxels": voxels,
            "count": len(blocks) if blocks else 0,
        }
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(500, str(exc))

@app.get("/api/voxel/status")
async def voxel_status():
    return {
        "asset_manager": voxel_asset_manager is not None,
        "studio_integration": voxel_studio is not None,
        "bridge": voxel_bridge is not None,
        "bridge_status": (voxel_bridge.status() if hasattr(voxel_bridge, "status") and callable(voxel_bridge.status) else getattr(voxel_bridge, "status", None)) if voxel_bridge else None,
    }


@app.get("/api/bridge/status")
async def bridge_status():
    """Dedicated status endpoint for the voxel/render bridge (Rust renderer
    connection). Same underlying data as /api/voxel/status's bridge fields,
    exposed at its own path since the render bridge is a distinct concern
    from voxel asset management."""
    if not voxel_bridge:
        return {"connected": False, "status": None}
    status = voxel_bridge.status()
    status_value = status.value if hasattr(status, "value") else status
    return {
        "connected": status_value not in (None, "disconnected", "emergency"),
        "status": status_value,
    }


@app.post("/api/bridge/connect")
async def bridge_connect(identity: Dict[str, Any] = Depends(require_role("mod"))):
    """Attempt (or re-attempt) a real handshake with the Rust renderer.
    Honest result — returns connected=False if no renderer is actually
    listening, it does not fabricate success."""
    if not voxel_bridge:
        raise HTTPException(503, "Voxel bridge not initialised")
    connected = voxel_bridge.connect()
    return {"ok": True, **voxel_bridge.to_dict(), "connected": connected}


@app.get("/api/engine/status")
async def engine_status():
    """Distributed-engine resource health (CPU/memory/GPU) from the IRM
    controller. Real system metrics — psutil when available, /proc fallback
    otherwise, 0.0 for GPU fields when no GPU/nvidia-smi is present."""
    if irm_controller is None:
        return {"available": False}
    report = irm_controller.check()
    return {"available": True, **report.to_dict()}


def _voxel_block_kit_status() -> Dict[str, Any]:
    try:
        from modules.voxel_block_kit import DEFAULT_MATERIALS
        from modules.voxel_set_contract import (
            DEFAULT_UNIT_PROFILE,
            PUB_BLOCK_INCHES,
            PUB_BLOCK_METERS,
            PUB_BLOCK_SUBDIVISIONS,
            inches_to_pub_units,
            pub_block_measurement,
        )
    except Exception as exc:
        return {
            "available": False,
            "severity": "warn",
            "message": f"PubBlock voxel kit unavailable: {type(exc).__name__}: {exc}",
        }

    measurements = {name: pub_block_measurement(subdivision) for name, subdivision in PUB_BLOCK_SUBDIVISIONS.items()}
    return {
        "available": True,
        "severity": "ok",
        "message": "PubBlock voxel block kit available as read-only build metadata",
        "unit_profile": DEFAULT_UNIT_PROFILE,
        "base_block_inches": PUB_BLOCK_INCHES,
        "base_block_meters": PUB_BLOCK_METERS,
        "subdivisions": dict(PUB_BLOCK_SUBDIVISIONS),
        "unit_inches": {name: measurement["unit_inches"] for name, measurement in measurements.items()},
        "unit_meters": {name: measurement["unit_meters"] for name, measurement in measurements.items()},
        "builders": [
            "stage_floor",
            "flat_wall",
            "backdrop_panel",
            "guide_grid",
            "doorway_wall",
            "rectangular_prism",
            "make_voxel_set",
        ],
        "materials": sorted(DEFAULT_MATERIALS.keys()),
        "capabilities": [
            "pubblock_measurements",
            "full_half_quarter_blocks",
            "floor_builder",
            "wall_builder",
            "doorway_builder",
            "image_backdrop_surfaces",
            "hidden_guide_grids",
            "contract_validation",
            "sandbox_only_asset_creation",
        ],
        "sample_checks": {
            "six_foot_avatar_rounded_full_blocks": inches_to_pub_units(72, subdivision=1),
            "six_foot_avatar_quarter_units": inches_to_pub_units(72, subdivision=4),
            "quarter_block_inches": measurements["quarter"]["unit_inches"],
        },
        "read_only": True,
        "creates_map_rooms": False,
        "creates_consoles": False,
    }


@app.get("/api/voxel/block-kit/status")
async def voxel_block_kit_status():
    return _voxel_block_kit_status()


@app.get("/api/voxel/block-kit/preview/capabilities")
async def voxel_block_kit_preview_capabilities():
    try:
        from modules.voxel_block_preview import preview_capabilities
        return preview_capabilities()
    except Exception as exc:
        return {"available": False, "read_only": True, "error": f"{type(exc).__name__}: {exc}"}


@app.post("/api/voxel/block-kit/preview")
async def voxel_block_kit_preview(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        raise HTTPException(400, "preview request body must be an object")
    kind = str(body.get("preview_kind") or body.get("kind") or "stage_floor")
    params = body.get("params") if isinstance(body.get("params"), dict) else body
    try:
        from modules.voxel_block_preview import VoxelBlockPreviewError, preview_voxel_asset
        return preview_voxel_asset(kind, params)
    except VoxelBlockPreviewError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        raise HTTPException(500, f"{type(exc).__name__}: {exc}")


# —
# Studio Control API
# —

@app.get("/api/studio/status")
async def studio_status():
    if studio_control is None:
        return {"available": False}
    try:
        return {"available": True, **studio_control.get_status_summary()}
    except Exception as exc:
        return {"available": False, "error": str(exc)}

@app.post("/api/studio/preflight")
async def studio_preflight(request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
    """Trigger the 5-second preflight countdown."""
    if studio_control is None:
        raise HTTPException(503, "Studio Control not available")
    body = await _json_dict(request)
    room = body.get("room", "studio")
    try:
        result = await studio_control.start_preflight(room=room)
        return {"ok": bool(result.get("success")), "result": result}
    except Exception as exc:
        raise HTTPException(500, str(exc))

@app.post("/api/studio/emergency-save")
async def studio_emergency_save(request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
    """Trigger the dead man's switch emergency save."""
    if studio_control is None:
        raise HTTPException(503, "Studio Control not available")
    try:
        result = await studio_control.emergency_save()
        return {"ok": bool(result.get("ok")), "result": result}
    except Exception as exc:
        raise HTTPException(500, str(exc))


# —


def _ai_model_slot_status() -> Dict[str, Any]:
    try:
        from modules.ai_runtime_slots import load_model_slot_status
        status = load_model_slot_status(Path(__file__).resolve().parent)
    except Exception as exc:
        return {"available": False, "severity": "warn", "message": str(exc)}
    slots = status.get("slots", {}) if isinstance(status, dict) else {}
    missing = [role for role, item in slots.items() if not item.get("available")]
    disabled = [role for role, item in slots.items() if item.get("available") and not item.get("enabled")]
    severity = "warn" if missing or disabled else "ok"
    message = "model slots configured" if severity == "ok" else "model slots configured but not fully enabled"
    return {"available": True, "severity": severity, "message": message, **status}
# ------------------------------------------------------------------------------
# Pub Manager Recovery API

def _pub_manager_raw_status() -> Dict[str, Any]:
    return {
        "runtime": {"message": "main route layer responding"},
        "websocket": {"message": "hub present" if hub is not None else "hub unavailable", "warning": None if hub is not None else "hub unavailable"},
        "assets": {"message": "avatar manifest present" if (DATA_DIR / "avatars" / "manifest.json").exists() else "avatar manifest missing", "warning": None if (DATA_DIR / "avatars" / "manifest.json").exists() else "avatar manifest missing"},
        "avatar": {"message": "avatar routes mounted"},
        "motion": {"message": "mocap available" if mocap is not None else "mocap not active", "warning": None if mocap is not None else "mocap not active"},
        "audio": {"message": "program audio state available" if program_audio_state is not None else "program audio unavailable", "warning": None if program_audio_state is not None else "program audio unavailable", "status": program_audio_state.status() if program_audio_state is not None else None},
        "recording": {"message": "recording service available" if recording is not None else "recording unavailable", "warning": None if recording is not None else "recording unavailable"},
        "visual_patch": {"message": "visual patch approval available" if _HAS_VISUAL_PATCH_BRIDGE else "visual patch bridge unavailable", "warning": None if _HAS_VISUAL_PATCH_BRIDGE else "visual patch bridge unavailable"},
        "conversation_ai": {"message": "conversation orchestrator available" if conv_orchestrator is not None else "conversation orchestrator not active", "warning": None if conv_orchestrator is not None else "conversation orchestrator not active"},
        "alex": {"message": "Alex bridge available" if alex_bridge is not None else "Alex bridge not active", "warning": None if alex_bridge is not None else "Alex bridge not active"},
        "jeremy": {"message": "Jeremy Cricket available" if cricket_keeper is not None else "Jeremy Cricket not active", "warning": None if cricket_keeper is not None else "Jeremy Cricket not active"},
        "evo": {"message": "EVO orchestrator available" if evo_orchestrator is not None else "EVO orchestrator not active", "warning": None if evo_orchestrator is not None else "EVO orchestrator not active"},
        "eq": {"message": "EQ layer file present" if (Path(__file__).resolve().parent / "modules" / "wired" / "eq_adaptor.py").exists() else "EQ layer file missing", "warning": None if (Path(__file__).resolve().parent / "modules" / "wired" / "eq_adaptor.py").exists() else "EQ layer file missing"},
        "model_slots": _ai_model_slot_status(),
        "voxel_block_kit": _voxel_block_kit_status(),
        "storage": {"message": "data dir present" if DATA_DIR.exists() else "data dir missing", "warning": None if DATA_DIR.exists() else "data dir missing"},
    }

@app.get("/api/ai/model-slots")
async def ai_model_slots_status():
    return _ai_model_slot_status()

@app.get("/api/menu/coverage")
async def menu_coverage_status():
    path = Path(__file__).resolve().parent / "config" / "menu_coverage.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"available": False, "error": str(exc)}
    return {"available": True, **data}

@app.get("/api/runtime-spine/status")
async def runtime_spine_status():
    spine_root = Path(__file__).resolve().parent / "runtime" / "spine"
    expected_files = [
        "event_bus.py", "runtime_state.py", "station_registry.py", "performer_registry.py",
        "performers/performer_state.py", "performers/locomotion.py", "performers/animation_authority.py",
        "performers/replication.py", "stations/base_station.py", "stations/camera_station.py",
        "stations/director_station.py", "stations/pub_station.py",
    ]
    missing = [rel for rel in expected_files if not (spine_root / rel).exists()]
    try:
        from runtime.spine import EventBus, PerformerRegistry, RuntimeState, StationRegistry
        from runtime.spine.performers.animation_authority import AnimationAuthority
        from runtime.spine.performers.locomotion import LocomotionSystem
        exported = [cls.__name__ for cls in (EventBus, PerformerRegistry, RuntimeState, StationRegistry, AnimationAuthority, LocomotionSystem)]
        import_ok = True
        error = ""
    except Exception as exc:
        exported = []
        import_ok = False
        error = f"{type(exc).__name__}: {exc or 'no detail'}"
    return {
        "available": import_ok and not missing,
        "import_ok": import_ok,
        "error": error,
        "missing_files": missing,
        "exported": exported,
        "capabilities": ["event_bus", "performer_registry", "station_registry", "locomotion", "animation_authority", "replication_scaffold"],
    }

async def _execute_pub_manager_recovery_action(action_id: str) -> Dict[str, Any]:
    """Execute only recovery actions this host can prove it performed."""
    if action_id == "program_audio.stop_all":
        if program_audio_state is None:
            raise HTTPException(503, "Program audio state unavailable")
        return {"action_id": action_id, "status": apply_audio_event(program_audio_state, {"action": "stop_all"})}

    if action_id == "animation.stop_all":
        if choreo_controller is None:
            raise HTTPException(503, "Choreography controller unavailable")
        await choreo_controller.stop()
        return {"action_id": action_id, "stopped": True}

    if action_id == "avatar.reset_pose":
        if performer_manager is None:
            raise HTTPException(503, "Avatar performer manager unavailable")
        await performer_manager.broadcast_dropout()
        return {"action_id": action_id, "reset": True, "performer_count": performer_manager.performer_count}

    if action_id == "mocap.pause":
        if mocap is None:
            raise HTTPException(503, "Mocap manager unavailable")
        await mocap.stop_stream()
        return {"action_id": action_id, "paused": True, "status": mocap.get_status()}

    if action_id == "room.reload_assets":
        if voxel_asset_manager is None:
            raise HTTPException(503, "Voxel asset manager unavailable")
        return {"action_id": action_id, **voxel_asset_manager.reload_asset_library()}

    if action_id == "recording.status":
        if recording is None:
            raise HTTPException(503, "Recording service unavailable")
        sessions = recording.list_sessions() if hasattr(recording, "list_sessions") else []
        normalized = [item if isinstance(item, dict) else item.to_dict() for item in (sessions or [])]
        return {"action_id": action_id, "sessions": normalized, "count": len(normalized)}

    if action_id == "assets.check_manifest":
        manifest_path = DATA_DIR / "avatars" / "manifest.json"
        if not manifest_path.exists():
            return {"action_id": action_id, "ok": False, "manifest_path": str(manifest_path), "error": "manifest_missing"}
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"action_id": action_id, "ok": False, "manifest_path": str(manifest_path), "error": f"{type(exc).__name__}: {exc}"}
        return {"action_id": action_id, "ok": True, "manifest_path": str(manifest_path), "entries": len(payload) if hasattr(payload, "__len__") else None}

    if action_id == "issue.export":
        if issue_report is None or build_snapshot is None:
            raise HTTPException(503, "Issue-report support unavailable")
        snapshot = build_snapshot(_pub_manager_raw_status())
        report = issue_report(snapshot)
        export_dir = DATA_DIR / "exports" / "pub_manager"
        export_dir.mkdir(parents=True, exist_ok=True)
        path = export_dir / f"issue_{int(time.time() * 1000)}.json"
        write_json(path, report)
        return {"action_id": action_id, "path": str(path), "report": report}

    if action_id == "ai.model_slots":
        return {"action_id": action_id, **_ai_model_slot_status()}

    if action_id == "ai.switchblade_status":
        return {"action_id": action_id, "status": await switchblade_status()}

    if action_id == "runtime.spine_status":
        return {"action_id": action_id, "status": await runtime_spine_status()}

    if action_id == "voxel.block_kit_status":
        return {"action_id": action_id, **_voxel_block_kit_status()}

    if action_id == "voxel.block_kit_preview":
        from modules.voxel_block_preview import preview_voxel_asset
        return {"action_id": action_id, "preview": preview_voxel_asset("stage_floor", {})}

    raise HTTPException(404, f"Recovery action is not implemented on this host: {action_id}")

@app.get("/api/pub-manager/safe-actions")
async def pub_manager_safe_actions():
    if not _HAS_PUB_MANAGER_RECOVERY or safe_actions is None:
        return {"available": False, "error": "Pub Manager recovery scaffold unavailable"}
    risky = approval_required_actions() if approval_required_actions is not None else []
    return {"available": True, "safe_actions": safe_actions(), "approval_required_actions": risky}

@app.get("/api/switchblade/status")
async def switchblade_status():
    from modules.pub_partner_chat import ROLE_TO_SLOT, chat_status
    from modules.switchblade_router import AUTO_ROLES, CREATIVE_TERMS, SUPPORT_TERMS, TECHNICAL_TERMS
    try:
        slot_status = chat_status(Path(__file__).resolve().parent)
    except Exception as exc:
        slot_status = {"available": False, "error": str(exc), "slots": {}}
    return {
        "available": True,
        "auto_roles": sorted(AUTO_ROLES),
        "manual_roles": sorted(role for role in ROLE_TO_SLOT if role not in AUTO_ROLES),
        "slot_status": slot_status,
        "signals": {
            "creative_terms": sorted(CREATIVE_TERMS),
            "technical_terms": sorted(TECHNICAL_TERMS),
            "support_terms": sorted(SUPPORT_TERMS),
        },
    }

@app.post("/api/switchblade/route-preview")
async def switchblade_route_preview(request: Request):
    from modules.pub_partner_chat import chat_status
    from modules.switchblade_router import decide_switchblade_role
    body = await _json_dict(request)
    decision = decide_switchblade_role(str(body.get("role") or "auto"), str(body.get("message") or ""))
    try:
        slots = chat_status(Path(__file__).resolve().parent).get("slots", {})
    except Exception:
        slots = {}
    return {"available": True, "decision": decision.to_dict(), "slot_status": slots.get(decision.slot, {})}
@app.get("/api/pub-manager/status")
async def pub_manager_status():
    if not _HAS_PUB_MANAGER_RECOVERY or build_snapshot is None:
        return {"available": False, "error": "Pub Manager recovery scaffold unavailable"}
    snapshot = build_snapshot(_pub_manager_raw_status())
    return {"available": True, **snapshot.to_dict(), "suggestions": suggest_recovery(snapshot)}

@app.post("/api/pub-manager/action")
async def pub_manager_action(request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
    if not _HAS_PUB_MANAGER_RECOVERY or validate_action is None:
        raise HTTPException(503, "Pub Manager recovery scaffold unavailable")
    body = await _json_dict(request)
    action_id = str(body.get("action_id") or "").strip()
    result = validate_action(action_id)
    if result.get("requires_approval"):
        return {"ok": False, "result": result, "message": "Action requires explicit approval or is unknown."}
    execution = await _execute_pub_manager_recovery_action(action_id)
    return {
        "ok": True,
        "result": result,
        "execution": execution,
        "actor": str(identity.get("user_id") or "director"),
        "message": "Recovery action executed.",
    }
@app.get("/api/pub-manager/issue-report")
async def pub_manager_issue_report():
    if not _HAS_PUB_MANAGER_RECOVERY or issue_report is None or build_snapshot is None:
        return {"available": False, "error": "Pub Manager recovery scaffold unavailable"}
    snapshot = build_snapshot(_pub_manager_raw_status())
    return {"available": True, "report": issue_report(snapshot)}


@app.get("/general-chat", include_in_schema=False)
async def general_chat_page():
    return FileResponse(STATIC_DIR / "general_chat.html")

@app.get("/pub-partner-chat", include_in_schema=False)
async def pub_partner_chat_page():
    return FileResponse(STATIC_DIR / "pub_partner_chat.html")

@app.get("/api/pub-partner-chat/status")
async def pub_partner_chat_status():
    from modules.pub_partner_chat import chat_status
    try:
        return {"available": True, **chat_status(Path(__file__).resolve().parent)}
    except Exception as exc:
        return {"available": False, "error": str(exc)}

@app.post("/api/pub-partner-chat/message")
async def pub_partner_chat_message(request: Request, identity=Depends(current_identity)):
    from modules.pub_partner_chat import chat_with_pub_partner
    if not identity.get('authenticated'):
        raise HTTPException(401, 'Sign in to use private partner chat')
    body = await _json_dict(request)
    body['user_id'] = bound_actor(request=request, identity=identity, explicit_value=body.get('user_id'),
                                  allow_privileged_override=False)
    return await chat_with_pub_partner(
        repo_root=Path(__file__).resolve().parent,
        data_dir=DATA_DIR,
        body=body,
        alex_bridge=alex_bridge,
        blackbox_witness=blackbox_witness,
        spine=request.app.state.pubpartner_spine,
    )


@app.get("/2i-v22", include_in_schema=False)
async def writers_room_v22_page():
    """Compatibility URL for the integrated v22 writer."""
    return FileResponse(Path(__file__).resolve().parent / "2i" / "writers-room-v22.html")


@app.get("/2i", include_in_schema=False)
@app.get("/writers-room", include_in_schema=False)
async def writers_room_page():
    return FileResponse(Path(__file__).resolve().parent / "2i" / "writers-room-v22.html")


@app.get("/pubpartner", include_in_schema=False)
async def pubpartner_page():
    return FileResponse(STATIC_DIR / "pubpartner.html")

@app.get("/api/internal/room-conductor/status")
async def internal_room_conductor_status(identity: Dict[str, Any] = Depends(require_role("mod"))):
    """Internal-only Room Conductor diagnostics; not a guest character surface."""
    conductor = getattr(app.state, "room_conductor", None)
    if conductor is None:
        raise HTTPException(503, "Room Conductor not initialized")
    try:
        stats = conductor.get_stats() if hasattr(conductor, "get_stats") else {}
        return {
            "ok": True,
            "internal_only": True,
            "guest_visible": False,
            "character_slot": False,
            "bubble_context_provider": bool(getattr(conductor, "_bubble_summary_provider", None)),
            "stats": stats,
        }
    except Exception as exc:
        raise HTTPException(500, f"Room Conductor status error: {exc}") from exc


# Unity Bridge API
# —

@app.get("/api/internal/pete/status")
async def internal_pete_status(identity: Dict[str, Any] = Depends(require_role("mod"))):
    """Internal e-PETE status alias; never a guest-visible character surface."""
    pete = getattr(app.state, "pete_enhanced", None)
    if pete is None:
        raise HTTPException(503, "Pete Enhanced not initialized")
    return pete.get_twin_engine_status()


@app.get("/api/internal/pete/diagnostics")
async def internal_pete_diagnostics(identity: Dict[str, Any] = Depends(require_role("mod"))):
    """Detailed internal diagnostics while preserving honest fallback state."""
    pete = getattr(app.state, "pete_enhanced", None)
    if pete is None:
        raise HTTPException(503, "Pete Enhanced not initialized")
    status = pete.get_twin_engine_status()
    return {
        "ok": True,
        "internal_only": True,
        "guest_visible": False,
        "status": status,
        "component_status": status.get("components", {}),
    }


@app.get("/api/internal/pete/runtime-components")
async def internal_pete_runtime_components(identity: Dict[str, Any] = Depends(require_role("mod"))):
    """Detected runtime pieces; file presence never implies runtime success."""
    pete = getattr(app.state, "pete_enhanced", None)
    if pete is None:
        raise HTTPException(503, "Pete Enhanced not initialized")
    return {
        "ok": True,
        "internal_only": True,
        "guest_visible": False,
        "components": pete.get_runtime_component_status(),
    }


@app.get("/api/unity/status")
async def unity_status():
    if unity_bridge is None:
        return {"available": False}
    return {"available": True, **unity_bridge.status()}


@app.get("/api/unity/world-brain")
async def unity_world_brain():
    """Snapshot of the shared world-state key/value store Unity reads from."""
    if unity_bridge is None or not hasattr(unity_bridge, "_world_brain"):
        return {"available": False, "keys": {}}
    snapshot = await unity_bridge._world_brain.snapshot()
    return {"available": True, "keys": snapshot}


# —
# MoCap API
# —

@app.get("/api/mocap/status")
async def mocap_status():
    if mocap is None:
        return {"available": False}
    try:
        s = mocap.get_status() if hasattr(mocap, "get_status") else {}
        return {"available": True, **s}
    except Exception as exc:
        return {"available": False, "error": str(exc)}

@app.post("/api/mocap/start")
async def mocap_start(request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
    if mocap is None:
        raise HTTPException(503, "MoCap not available")
    body = await _json_dict(request)
    source_url = _bounded_text(body.get("source_url") or body.get("url") or "udp://127.0.0.1:9001", max_len=500)
    try:
        result = await mocap.start_stream(source_url)
        if not result:
            raise HTTPException(503, f"MoCap stream could not start from {source_url}")
        return {"ok": True, "source_url": source_url, "status": mocap.get_status()}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, str(exc))

@app.post("/api/mocap/stop")
async def mocap_stop(identity: Dict[str, Any] = Depends(require_role("mod"))):
    if mocap is None:
        raise HTTPException(503, "MoCap not available")
    try:
        await mocap.stop_stream()
        return {"ok": True, "status": mocap.get_status()}
    except Exception as exc:
        raise HTTPException(500, str(exc))


# —
# Frontend compatibility routes backed by current Reach runtime owners.
# Routes report unavailable state honestly when their owner is absent.
# —

@app.get("/api/health")
async def api_health_alias():
    """Comprehensive health check — some pages call /api/health instead of
    /health and expect subsystem counts plus AI provider key presence,
    not just a bare status flag."""
    return {
        "status": "ok",
        "version": "5.6.0",
        "timestamp": time.time(),
        "cameras": len(cameras.list_sources()) if cameras else 0,
        "ws_rooms": len(room_manager.list_rooms()) if room_manager else 0,
        "ai_providers": {
            "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("PUBCAST_ANTHROPIC_KEY")),
            "openai": bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("PUBCAST_OPENAI_KEY")),
            "gemini": bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("PUBCAST_GEMINI_KEY")),
        },
    }


@app.get("/api/agents")
async def list_agents():
    """conference.js lists agents/bots for the conference room."""
    if bot_manager is None:
        return {"agents": []}
    return {"agents": [
        {"agent_id": cfg.bot_id, "name": cfg.display_name,
         "provider": cfg.provider, "active": True}
        for cfg in bot_manager.list_configs()
    ]}



@app.post("/api/session/register")
async def register_session_user(request: Request, identity: Dict[str, Any] = Depends(current_identity)):
    body = await _json_dict(request)
    caller_id = _caller_or_body_identity(request=request, identity=identity, explicit_value=body.get('user_id'), field_name='user_id', allow_privileged_override=True)
    user_id = _bounded_text(caller_id, max_len=120) or 'anon'
    display_name = _bounded_text(body.get('display_name') or user_id, max_len=120) or user_id
    session_id = _bounded_text(body.get('session_id') or f"session_{int(time.time())}", max_len=120)
    project_id = _bounded_text(body.get('project_id') or 'default', max_len=120)
    raw_host_user_id = _bounded_text(body.get('host_user_id'), max_len=120) or None
    host_user_id = raw_host_user_id
    if raw_host_user_id:
        # Host assignment may not contradict the caller unless a privileged token is present.
        host_user_id = bound_actor(request=request, identity=identity, explicit_value=raw_host_user_id, field_name='host_user_id')
    stored_user_state = read_json(DATA_DIR / "users" / f"{user_id}.json")
    care_profile = None
    if alex_little_one_enabled():
        from modules.alex_little_one.care_profile import normalize_care_profile
        care_profile = normalize_care_profile(body.get('care_profile'), stored_user_state.get('care_profile'))
    participant = session_runtime.register_participant(
        DATA_DIR,
        session_id=session_id,
        user_id=user_id,
        display_name=display_name,
        project_id=project_id,
        session_role=_bounded_string_list(body.get('session_role'), field_name='session_role'),
        project_role=_bounded_string_list(body.get('project_role'), field_name='project_role'),
        license_role=_bounded_text(body.get('license_role') or 'personal', max_len=40),
        host_user_id=host_user_id,
        credit_name=_bounded_text(body.get('credit_name') or display_name, max_len=120),
        presence_mode=_bounded_text(body.get('presence_mode') or 'avatar_static', max_len=40),
        availability=_bounded_text(body.get('availability') or 'available', max_len=40),
        creditable=bool(body.get('creditable', True)),
        care_profile=care_profile,
    )
    entry_context = await _alex_entry_context(
        user_id=user_id,
        session_id=session_id,
        project_id=project_id,
        room_id=participant.get('dressing_room_id', 'dressing_room'),
        display_name=display_name,
        metadata=body,
    )
    return {
        'ok': True,
        'participant': participant,
        'alex_bridge': entry_context['packet'],
        'jeremy_whisper': entry_context['jeremy_whisper'],
        'session_resurrection': entry_context['resurrection'],
    }


@app.get("/api/session/{session_id}/roster")
async def session_roster(session_id: str):
    return {'ok': True, 'session_id': session_id, 'participants': session_runtime.get_roster(DATA_DIR, session_id)}


async def _alex_entry_context(
    *,
    user_id: str,
    session_id: str,
    project_id: str,
    room_id: str,
    display_name: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the Alex/Jeremy entry packet, preferring warm resurrection when available."""
    if not alex_bridge:
        return {"packet": None, "jeremy_whisper": "", "resurrection": None}

    try:
        alex = alex_bridge.alex_for(user_id)
        resurrector = SessionResurrector(
            alex=alex,
            bridge=alex_bridge,
            memory_engine=memory_engine,
            data_dir=DATA_DIR,
        )
        context = await resurrector.resurrect(
            user_id=user_id,
            session_id=session_id,
            project_id=project_id,
            room_id=room_id,
            display_name=display_name,
        )
        bridge_whisper = alex_bridge.jeremy_whisper(user_id=user_id, session_id=session_id)
        return {
            "packet": context.packet,
            "jeremy_whisper": "\n\n".join(part for part in [bridge_whisper, context.whisper] if part),
            "resurrection": {
                "summary": context.summary,
                "memory_count": context.memory_count,
                "offline_mins": context.offline_mins,
                "whisper": context.whisper,
            },
        }
    except Exception as exc:
        logger.warning("Alex/Jeremy resurrection failed; using entry packet fallback: %s", exc)
        packet = alex_bridge.build_entry_packet(
            user_id=user_id,
            session_id=session_id,
            project_id=project_id,
            room_id=room_id,
            display_name=display_name,
            metadata=metadata,
        )
        return {
            "packet": packet,
            "jeremy_whisper": alex_bridge.jeremy_whisper(user_id=user_id, session_id=session_id),
            "resurrection": {"fallback": True, "error": str(exc)},
        }


if alex_little_one_enabled():
    @app.get("/api/session/{session_id}/public-role-policy")
    async def session_public_role_policy(session_id: str):
        return {'ok': True, 'session_id': session_id, 'policy': session_runtime.public_role_policy(DATA_DIR, session_id)}


    @app.post("/api/session/{session_id}/public-role/phrase")
    async def public_role_phrase(session_id: str, request: Request, identity: Dict[str, Any] = Depends(current_identity)):
        body = await _json_dict(request)
        user_id = _bounded_text(_caller_or_body_identity(request=request, identity=identity, explicit_value=body.get('user_id') or request.headers.get('X-Client-Id'), field_name='user_id', allow_privileged_override=True), max_len=120) or 'anon'
        try:
            result = session_runtime.apply_public_role_phrase(
                DATA_DIR,
                session_id=_bounded_text(session_id, max_len=120),
                user_id=user_id,
                text=_bounded_text(body.get('text') or '', max_len=240),
            )
        except KeyError as exc:
            raise HTTPException(404, str(exc))
        user_file = DATA_DIR / "users" / f"{user_id}.json"
        user_state = read_json(user_file) if user_file.exists() else {"user_id": user_id}
        user_state["care_profile"] = result["care_profile"]
        write_json(user_file, user_state)
        return {'ok': True, 'session_id': session_id, 'user_id': user_id, **result}


    @app.post("/api/session/{session_id}/public-role/moderate")
    async def moderate_public_role_message(session_id: str, request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
        body = await _json_dict(request)
        target_user_id = _bounded_text(body.get('target_user_id'), max_len=120)
        result = session_runtime.moderate_public_role_message(
            DATA_DIR,
            session_id=_bounded_text(session_id, max_len=120),
            message=_bounded_text(body.get('message') or '', max_len=2000),
        )
        moderation = result.get('moderation', {})
        applied = "none"
        if target_user_id and not moderation.get('allowed', True) and governance:
            acting_user_id = _bounded_text(bound_actor(request=request, identity=identity, explicit_value=body.get('acting_user_id') or request.headers.get('X-Client-Id', 'system'), field_name='acting_user_id'), max_len=120)
            reason = "Alex Little One public role boundary violation: " + ", ".join(moderation.get('violations') or [])
            if moderation.get('action') == 'mute':
                governance.mute_user(target_user_id, acting_user_id, duration_seconds=300)
                applied = "muted"
            elif moderation.get('action') == 'remove':
                governance.ban_user(target_user_id, reason, acting_user_id)
                applied = "removed"
            else:
                applied = "warned"
        return {'ok': True, 'session_id': session_id, 'target_user_id': target_user_id, 'applied': applied, **result}


    @app.post("/api/session/{session_id}/public-role/owner-attempt")
    async def public_role_owner_attempt(session_id: str, request: Request, identity: Dict[str, Any] = Depends(current_identity)):
        body = await _json_dict(request)
        result = session_runtime.review_public_role_owner_attempt(
            DATA_DIR,
            session_id=_bounded_text(session_id, max_len=120),
            text=_bounded_text(body.get('text') or '', max_len=1000),
        )
        return {'ok': True, 'session_id': session_id, **result}


@app.post("/api/session/{session_id}/role")
async def update_session_role(session_id: str, request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
    body = await _json_dict(request)
    target_user_id = _bounded_text(body.get('target_user_id'), max_len=120)
    if not target_user_id:
        raise HTTPException(400, 'target_user_id is required')
    session_role = _bounded_string_list(body.get('session_role'), field_name='session_role') if 'session_role' in body else None
    project_role = _bounded_string_list(body.get('project_role'), field_name='project_role') if 'project_role' in body else None
    try:
        participant = session_runtime.update_role(
            DATA_DIR,
            session_id=_bounded_text(session_id, max_len=120),
            acting_user_id=_bounded_text(bound_actor(request=request, identity=identity, explicit_value=body.get('acting_user_id') or request.headers.get('X-Client-Id', 'anon'), field_name='acting_user_id'), max_len=120),
            target_user_id=target_user_id,
            session_role=session_role,
            project_role=project_role,
            creditable=body.get('creditable'),
        )
    except KeyError as exc:
        raise HTTPException(404, str(exc))
    bridge_packet = alex_bridge.current_packet(user_id=participant.get('user_id'), session_id=session_id) if alex_bridge else None
    return {'ok': True, 'participant': participant, 'alex_bridge': bridge_packet, 'jeremy_whisper': alex_bridge.jeremy_whisper(user_id=participant.get('user_id'), session_id=session_id) if alex_bridge else ''}


@app.get("/api/session/{session_id}/call-menu")
async def session_call_menu(session_id: str):
    return {'ok': True, 'session_id': session_id, 'contacts': session_runtime.call_menu(DATA_DIR, session_id)}


@app.post("/api/dressing-room/resolve")
async def resolve_dressing_room(request: Request, identity: Dict[str, Any] = Depends(current_identity)):
    body = await _json_dict(request)
    caller_id = _caller_or_body_identity(request=request, identity=identity, explicit_value=body.get('user_id') or request.headers.get('X-Client-Id'), field_name='user_id', allow_privileged_override=True)
    user_id = _bounded_text(caller_id, max_len=120) or 'anon'
    display_name = _bounded_text(body.get('display_name') or user_id, max_len=120) or user_id
    session_id = _bounded_text(body.get('session_id') or 'default', max_len=120)
    project_id = _bounded_text(body.get('project_id') or 'default', max_len=120)
    resolved = session_runtime.resolve_dressing_room(DATA_DIR, session_id=session_id, user_id=user_id, display_name=display_name, project_id=project_id)
    entry_context = await _alex_entry_context(
        user_id=user_id,
        session_id=session_id,
        project_id=project_id,
        room_id=resolved.get('dressing_room_id', 'dressing_room'),
        display_name=display_name,
        metadata=body,
    )
    return {
        'ok': True,
        **resolved,
        'alex_bridge': entry_context['packet'],
        'jeremy_whisper': entry_context['jeremy_whisper'],
        'session_resurrection': entry_context['resurrection'],
    }

@app.get("/api/dressing-room/security/status")
async def dressing_room_security_status(request: Request, project_id: str = 'default', session_id: str = 'default'):
    room_owner_id = request.headers.get('X-Client-Id', 'anon')
    status = dr_security.get_status(DATA_DIR, room_owner_id=room_owner_id, session_id=session_id)
    status.update({'ok': True, 'project_id': project_id, 'session_id': session_id, 'room_owner_id': room_owner_id})
    return status

@app.post("/api/dressing-room/security/code")
async def dressing_room_security_code(request: Request, identity: Dict[str, Any] = Depends(current_identity)):
    body = await _json_dict(request)
    room_owner_id = _bounded_text(_caller_or_body_identity(request=request, identity=identity, explicit_value=body.get('room_owner_id') or request.headers.get('X-Client-Id'), field_name='room_owner_id'), max_len=120) or 'anon'
    action = _bounded_text(body.get('action') or 'set', max_len=20).lower() or 'set'
    if action not in {'set', 'disable'}:
        raise HTTPException(status_code=400, detail='action must be set or disable')
    try:
        if action == 'disable':
            result = dr_security.disable_code(DATA_DIR, room_owner_id, _bounded_text(body.get('current_code') or body.get('code') or '', max_len=32))
        else:
            result = dr_security.set_code(DATA_DIR, room_owner_id, _bounded_text(body.get('code') or '', max_len=32))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    return {'ok': True, **result, 'room_owner_id': room_owner_id}

@app.post("/api/dressing-room/security/enter")
async def dressing_room_security_enter(request: Request, identity: Dict[str, Any] = Depends(current_identity)):
    body = await _json_dict(request)
    room_owner_id = _bounded_text(body.get('room_owner_id') or request.headers.get('X-Client-Id', 'anon'), max_len=120) or 'anon'
    acting_identity = _bounded_text(_caller_or_body_identity(request=request, identity=identity, explicit_value=body.get('acting_identity') or request.headers.get('X-Client-Id'), field_name='acting_identity', allow_privileged_override=True), max_len=120) or 'anon'
    return dr_security.attempt_entry(
        DATA_DIR,
        room_owner_id=room_owner_id,
        acting_identity=acting_identity,
        project_id=_bounded_text(body.get('project_id') or 'default', max_len=120),
        session_id=_bounded_text(body.get('session_id') or 'default', max_len=120),
        credential_type=_bounded_text(body.get('credential_type') or 'personal', max_len=40),
        code=_bounded_text(body.get('code'), max_len=32) or None,
        valid_routing=bool(body.get('valid_routing', True)),
        access_log=_string_list_field(body.get('accessed_files') or body.get('access_log') or [], 'access_log'),
    )


@app.post("/api/memory/events")
async def record_memory_event(request: Request, identity: Dict[str, Any] = Depends(current_identity)):
    body = await _json_dict(request)
    event = memory_engine.record_event(
        DATA_DIR,
        session_id=_bounded_text(body.get('session_id') or 'default', max_len=120),
        project_id=_bounded_text(body.get('project_id') or 'default', max_len=120),
        user_id=_bounded_text(_caller_or_body_identity(request=request, identity=identity, explicit_value=body.get('user_id') or request.headers.get('X-Client-Id'), field_name='user_id', allow_privileged_override=True), max_len=120) or 'anon',
        room_id=_bounded_text(body.get('room_id') or 'unknown', max_len=120),
        feature_id=_bounded_text(body.get('feature_id') or '', max_len=120),
        event_type=_bounded_text(body.get('event_type') or 'interaction', max_len=80),
        summary=_bounded_text(body.get('summary') or '', max_len=1000),
        speaking_style=_bounded_text(body.get('speaking_style') or '', max_len=120),
        mood_trace=_bounded_text(body.get('mood_trace') or '', max_len=240),
        payload=_object_or_empty(body.get('payload'), field_name='payload'),
    )
    return {'ok': True, 'event': event}


@app.get("/api/memory/context")
async def get_memory_context(
    request: Request,
    session_id: str,
    project_id: str,
    room_id: str,
    user_id: Optional[str] = None,
    identity: Dict[str, Any] = Depends(current_identity),
):
    # SECURITY: previously `user_id` was a raw client-suppliable query param with
    # no auth dependency at all -- any caller could read another user's memory
    # context plus their Alex/Jeremy bridge packet and Jeremy whisper content by
    # simply passing that user's id. Scoped to the authenticated caller via the
    # same bound_actor() helper already used by /api/user/state above (no
    # privileged override -- a regular user cannot read someone else's context
    # just by holding a mod role either, since this is a private memory read,
    # not an administrative action).
    scoped_user_id = bound_actor(
        request=request, identity=identity, explicit_value=user_id,
        field_name="user_id", allow_privileged_override=False,
    )
    context = memory_engine.context_summary(DATA_DIR, session_id=session_id, project_id=project_id, user_id=scoped_user_id, room_id=room_id)
    if alex_bridge:
        context['alex_bridge'] = alex_bridge.current_packet(user_id=scoped_user_id, session_id=session_id)
        context['jeremy_whisper'] = alex_bridge.jeremy_whisper(user_id=scoped_user_id, session_id=session_id)
    return {'ok': True, 'context': context}

@app.post("/api/alex-jeremy/signal")
async def alex_jeremy_signal(request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
    body = await _json_dict(request)
    if not alex_bridge:
        raise HTTPException(503, 'Alex/Jeremy bridge not initialized')
    user_id = _bounded_text(_caller_or_body_identity(request=request, identity=identity, explicit_value=body.get('user_id') or request.headers.get('X-Client-Id'), field_name='user_id', allow_privileged_override=True), max_len=120) or 'anon'
    packet = alex_bridge.signal_from_jeremy(
        user_id=user_id,
        session_id=_bounded_text(body.get('session_id') or 'default', max_len=120),
        room_state=_bounded_text(body.get('room_state') or 'stable', max_len=40),
        urgency=_bounded_text(body.get('urgency') or 'low', max_len=40),
        reason=_bounded_text(body.get('reason') or 'unspecified', max_len=240),
        payload=_object_or_empty(body.get('payload'), field_name='payload'),
    )
    return {'ok': True, 'alex_bridge': packet, 'jeremy_whisper': alex_bridge.jeremy_whisper(user_id=user_id, session_id=body.get('session_id') or 'default')}


@app.get("/api/alex-jeremy/packet")
async def alex_jeremy_packet(
    request: Request,
    session_id: str,
    user_id: Optional[str] = None,
    identity: Dict[str, Any] = Depends(current_identity),
):
    # SECURITY: same IDOR class as /api/memory/context above -- previously a
    # raw client-suppliable user_id with zero auth dependency. Scoped to the
    # authenticated caller the same way.
    if not alex_bridge:
        raise HTTPException(503, 'Alex/Jeremy bridge not initialized')
    scoped_user_id = bound_actor(
        request=request, identity=identity, explicit_value=user_id,
        field_name="user_id", allow_privileged_override=False,
    )
    return {'ok': True, 'alex_bridge': alex_bridge.current_packet(user_id=scoped_user_id, session_id=session_id), 'jeremy_whisper': alex_bridge.jeremy_whisper(user_id=scoped_user_id, session_id=session_id)}

@app.get("/api/cast/characters")
async def list_cast_characters_route():
    return {"characters": [spec.model_dump() for spec in list_cast_characters()], "count": len(list_cast_characters())}


@app.get("/api/cast/characters/{character_id}")
async def get_cast_character_route(character_id: str):
    spec = get_cast_character(character_id)
    if not spec:
        raise HTTPException(404, f"Cast character '{character_id}' not found")
    return spec.model_dump()


@app.get("/api/avatars/me")
async def get_my_avatar(request: Request, identity: Dict[str, Any] = Depends(current_identity)):
    """dressing.html / dressing.js — return the caller's persisted avatar profile."""
    client_id = bound_actor(request=request, identity=identity, explicit_value=request.headers.get("X-Client-Id"), field_name="X-Client-Id", allow_privileged_override=False)
    avatar = load_avatar(DATA_DIR, client_id)
    response = {
        "available": True,
        "user_id": client_id,
        "display_name": getattr(avatar, "display_name", client_id),
        "glow_color": getattr(avatar, "glow_color", "#00FFFF"),
        "badge": getattr(avatar, "metadata", {}).get("badge", ""),
        "preset_id": getattr(avatar, "preset", "MANNY"),
        "color": getattr(avatar, "glow_color", "#00FFFF"),
        "mood": getattr(avatar, "metadata", {}).get("mood", "neutral"),
        "gesture": getattr(avatar, "metadata", {}).get("gesture", "none"),
    }
    if ethereal_mgr is not None:
        try:
            skin = ethereal_mgr.get_or_create_skin(client_id)
            response["mood"] = getattr(skin, "mood", response["mood"])
            response["gesture"] = getattr(skin, "current_gesture", response["gesture"])
        except Exception:
            pass
    return response


@app.post("/api/avatars/me")
async def update_my_avatar(request: Request, identity: Dict[str, Any] = Depends(current_identity)):
    """dressing.js — update caller's avatar skin and persisted profile."""
    client_id = bound_actor(request=request, identity=identity, explicit_value=request.headers.get("X-Client-Id"), field_name="X-Client-Id", allow_privileged_override=False)
    body = await _json_dict(request)
    existing = load_avatar(DATA_DIR, client_id)
    merged = existing.model_dump()
    if "display_name" in body:
        merged["display_name"] = body.get("display_name") or existing.display_name
    if "glow_color" in body or "color" in body:
        merged["glow_color"] = body.get("glow_color") or body.get("color") or existing.glow_color
    if "preset_id" in body:
        merged["preset"] = body.get("preset_id") or existing.preset
    metadata = dict(getattr(existing, "metadata", {}) or {})
    if "badge" in body:
        metadata["badge"] = body.get("badge") or ""
    if "mood" in body:
        metadata["mood"] = body.get("mood")
    if "gesture" in body:
        metadata["gesture"] = body.get("gesture")
    merged["metadata"] = metadata
    avatar = save_avatar(DATA_DIR, client_id, existing.__class__(**merged))
    if ethereal_mgr is not None:
        try:
            if "color" in body or "glow_color" in body:
                ethereal_mgr.set_color(client_id, merged["glow_color"])
            if "mood" in body:
                ethereal_mgr.set_mood(client_id, body["mood"])
        except Exception:
            pass
    return {"ok": True, "user_id": client_id, "display_name": avatar.display_name, "glow_color": avatar.glow_color, "preset_id": avatar.preset, "badge": metadata.get("badge", "")}


@app.get("/api/avatars/presets")
async def list_avatar_presets_route():
    """dressing.html — list available avatar presets."""
    return {"presets": [p.model_dump() for p in list_avatar_presets()]}


@app.post("/api/avatars/me/bake")
async def bake_my_avatar(request: Request, identity: Dict[str, Any] = Depends(current_identity)):
    """dressing.js — bake a photo into a voxel avatar portrait."""
    client_id = bound_actor(request=request, identity=identity, explicit_value=request.headers.get("X-Client-Id"), field_name="X-Client-Id", allow_privileged_override=False)
    if not _HAS_SCULPTOR or Sculptor is None:
        return {"ok": False, "reason": "Sculptor not available — upload a photo when it is"}
    # Multipart photo upload
    try:
        import shutil
        form = await request.form()
        photo = form.get("photo") or form.get("file")
        if not photo or not hasattr(photo, "filename"):
            raise HTTPException(400, "photo file required")
        dest = DATA_DIR / "sculptures" / f"{client_id}_photo{__import__('pathlib').Path(photo.filename).suffix}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as f:
            shutil.copyfileobj(photo.file, f)
        sculptor = Sculptor(mode="webcam")
        result = sculptor.bake_from_photo(dest, client_id)
        if result is None:
            return {"ok": False, "reason": "No face detected in photo"}
        return {"ok": True, "bake": result}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, str(exc))


@app.get("/api/vod")
async def list_vod():
    """gallery.html — list completed recordings available for playback.
    gallery.html reads `d.files` (array of {name, url, ...}), so the
    per-session artifact list is flattened into playable file entries here."""
    if recording is None:
        return {"files": []}
    try:
        sessions = recording.list_sessions() if hasattr(recording, "list_sessions") else []
        files: List[Dict[str, Any]] = []
        for session in sessions:
            data = session.to_dict() if hasattr(session, "to_dict") else session
            if not isinstance(data, dict):
                continue
            for art in data.get("artifacts") or []:
                files.append({
                    "name": art.get("name"),
                    "url": f"/api/vod/{data['session_id']}/{art.get('name')}",
                    "format": art.get("format"),
                    "size_bytes": art.get("size_bytes"),
                    "session_id": data.get("session_id"),
                    "state": data.get("state"),
                    "ended_at": data.get("ended_at"),
                })
        return {"files": files, "count": len(files)}
    except Exception:
        return {"files": [], "count": 0}


@app.get("/api/vod/{session_id}/{artifact_name}")
async def vod_download(session_id: str, artifact_name: str):
    """Serve a single recorded artifact file for playback/download.
    Looks up the artifact by name within the session's own tracked artifact
    list (never builds a filesystem path from the raw request path), so
    there's no traversal risk."""
    if recording is None:
        raise HTTPException(503, "Recording service not available")
    try:
        session = recording.get_session(session_id)
    except Exception:
        raise HTTPException(404, "Recording session not found")
    for art in getattr(session, "artifacts", []):
        if art.name == artifact_name:
            if not art.file_path.is_file():
                raise HTTPException(404, "Artifact file missing on disk")
            return FileResponse(art.file_path, filename=art.file_path.name)
    raise HTTPException(404, "Artifact not found")


@app.get("/api/performer/status")
async def performer_status():
    """launch.html — overall performer/avatar pipeline health check."""
    return {
        "available":    True,
        "running":      bool(performer_manager and performer_manager._running),
        "ethereal":     _HAS_ETHEREAL and ethereal_mgr is not None,
        "evo":          _HAS_EVO and evo_orchestrator is not None,
        "mocap":        mocap is not None,
        "bridge":       voxel_bridge is not None,
        "voxel":        voxel_asset_manager is not None,
        "studio":       studio_control is not None,
        "ws_renderer":  __import__('pathlib').Path("bin/ws_renderer").exists(),
    }


@app.get("/api/me")
async def get_me(identity: Dict[str, Any] = Depends(current_identity)):
    """Current caller's normalized identity."""
    return identity


@app.get("/api/health/breakers")
async def health_breakers():
    """Circuit breaker status for every registered breaker."""
    from modules.circuit_breaker import all_breaker_stats
    return {"breakers": all_breaker_stats()}


@app.get("/api/jeremy/health")
async def jeremy_health():
    """Per-character health for every loaded Jeremy Cricket instance."""
    if not cricket_keeper:
        return {"available": False, "characters": []}
    return {"available": True, "characters": await cricket_keeper.health_all()}


@app.get("/api/audio/tts")
@app.post("/api/audio/tts")
async def audio_tts_alias(request: Request, identity: Dict[str, Any] = Depends(current_identity)):
    """tts.js calls /api/audio/tts — proxy to the inference TTS endpoint."""
    if inference is None:
        raise HTTPException(503, "Inference not available")
    try:
        body = await _json_dict(request) if request.method == "POST" else {}
    except Exception:
        body = {}
    text = body.get("text", body.get("prompt", ""))
    voice = body.get("voice", "default")
    if not text:
        raise HTTPException(400, "text required")
    # Delegate to existing TTS handler
    result = await inference.tts(text=text, voice=voice) if hasattr(inference, "tts") else \
             {"audio_url": None, "text": text, "note": "TTS engine not configured"}
    return result


@app.get("/api/cameras/program/{source_id}")
async def get_program_camera(source_id: str):
    """switcher.js — get program camera state."""
    if cameras is None:
        raise HTTPException(503, "Camera manager not available")
    src = cameras.get(source_id)
    if src is None:
        raise HTTPException(404, f"Camera not found: {source_id}")
    return {"source_id": source_id, "is_program": cameras.get_program_source() and
            cameras.get_program_source().source_id == source_id}


@app.post("/api/cameras/program/{source_id}")
async def set_program_camera(source_id: str, identity: Dict[str, Any] = Depends(require_role("mod"))):
    """switcher.js — set program camera."""
    if cameras is None:
        raise HTTPException(503, "Camera manager not available")
    ok = cameras.set_program_source(source_id)
    if not ok:
        raise HTTPException(404, f"Camera not found: {source_id}")
    if hub and not getattr(hub, "camera_events_bridged", False):
        await hub.broadcast_system_event({
            "type": "camera_switch",
            "payload": {"target": "program", "source_id": source_id}
        })
    if _HAS_PUBWORLD_ROUTER and push_production_state_to_pubworld:
        await push_production_state_to_pubworld({"camera": source_id})
    return {"ok": True, "program": source_id}


@app.get("/api/cameras/preview/{source_id}")
async def get_preview_camera(source_id: str):
    """switcher.js — get preview camera state."""
    if cameras is None:
        raise HTTPException(503, "Camera manager not available")
    src = cameras.get(source_id)
    if src is None:
        raise HTTPException(404, f"Camera not found: {source_id}")
    return {"source_id": source_id, "is_preview": cameras.get_preview_source() and
            cameras.get_preview_source().source_id == source_id}


@app.post("/api/cameras/preview/{source_id}")
async def set_preview_camera(source_id: str, identity: Dict[str, Any] = Depends(require_role("mod"))):
    """switcher.js — set preview camera."""
    if cameras is None:
        raise HTTPException(503, "Camera manager not available")
    ok = cameras.set_preview_source(source_id)
    if not ok:
        raise HTTPException(404, f"Camera not found: {source_id}")
    if hub and not getattr(hub, "camera_events_bridged", False):
        await hub.broadcast_system_event({
            "type": "camera_switch",
            "payload": {"target": "preview", "source_id": source_id}
        })
    return {"ok": True, "preview": source_id}


# —
# WebSocket
# —

# — PubWorld 2.5D client WS —
# world.html connects here. It tracks which room the player is in client-side
# and sends room_change, ping, and hotspot action messages.

_pubworld_clients: dict[str, WebSocket] = {}

@app.websocket("/pubworld/ws/{client_id}")
async def pubworld_ws(ws: WebSocket, client_id: str):
    """PubWorld live channel with an in-band JWT handshake when auth is enforced.

    Native browser WebSockets cannot attach an Authorization header.  Tokens are
    deliberately kept out of the URL (where proxies/history may retain them):
    secured Reach requires the first client message to be
    ``{"type":"auth","token":...}`` before any production state is revealed.
    """
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", client_id):
        await ws.close(code=1008, reason="Invalid PubWorld client identifier")
        return

    await ws.accept()
    actor_id = client_id

    if auth_enforced():
        try:
            raw_auth = await asyncio.wait_for(ws.receive_text(), timeout=8.0)
            auth_message = json.loads(raw_auth)
        except (asyncio.TimeoutError, ValueError, TypeError, json.JSONDecodeError):
            await ws.send_text(json.dumps({"type": "auth_error", "message": "Authentication required"}))
            await ws.close(code=4401)
            return
        if not isinstance(auth_message, dict) or auth_message.get("type") != "auth":
            await ws.send_text(json.dumps({"type": "auth_error", "message": "Authentication required"}))
            await ws.close(code=4401)
            return
        payload = auth_module.decode_access_token(str(auth_message.get("token") or ""))
        if not payload:
            await ws.send_text(json.dumps({"type": "auth_error", "message": "Invalid or expired token"}))
            await ws.close(code=4401)
            return
        actor_id = str(payload.get("sub") or "").strip()
        if not actor_id:
            await ws.send_text(json.dumps({"type": "auth_error", "message": "Invalid token identity"}))
            await ws.close(code=4401)
            return
        await ws.send_text(json.dumps({"type": "auth_ok", "user_id": actor_id}))

    if client_id in _pubworld_clients:
        await ws.close(code=1008, reason="PubWorld client identifier already in use")
        return
    _pubworld_clients[client_id] = ws

    welcome_payload: dict = {"type": "welcome", "payload": {}}
    if hub:
        welcome_payload["payload"]["production_state"] = hub.get_production_state()
    await ws.send_text(json.dumps(welcome_payload))

    try:
        while True:
            raw = await ws.receive_text()
            try:
                data = json.loads(raw)
            except Exception:
                continue
            if not isinstance(data, dict):
                await ws.send_text(json.dumps({"type": "error", "message": "Expected an event object"}))
                continue
            msg_type = data.get("type", "")

            if msg_type == "auth":
                await ws.send_text(json.dumps({"type": "auth_ok", "user_id": actor_id}))
            elif msg_type == "ping":
                await ws.send_text(json.dumps({"type": "pong"}))
            elif msg_type == "room_change":
                room_id = data.get("room", "")
                logger.debug("PubWorld client %s (%s) entered room %s", client_id, actor_id, room_id)
                await ws.send_text(json.dumps({"type": "room_ack", "room": room_id}))
            elif msg_type == "hotspot":
                from modules.pubworld_hotspots import ACTION_HANDLERS
                action = data.get("action", "")
                action_data = data.get("data", {})
                handler = ACTION_HANDLERS.get(action)
                if handler:
                    try:
                        result = handler(actor_id, data.get("room", ""), action_data)
                        await ws.send_text(json.dumps({"type": "hotspot_result", **result}))
                    except Exception as exc:
                        await ws.send_text(json.dumps({"type": "hotspot_result", "status": "error", "message": str(exc)}))
                else:
                    await ws.send_text(json.dumps({"type": "hotspot_result", "status": "unknown_action", "action": action}))
            elif msg_type == "player_move":
                pass
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.warning("PubWorld WS error for client %s: %s", client_id, exc)
    finally:
        if _pubworld_clients.get(client_id) is ws:
            _pubworld_clients.pop(client_id, None)


# — Unity bridge WebSocket —

@app.websocket("/unity/ws/{client_id}")
async def unity_ws(ws: WebSocket, client_id: str):
    """Unity C# clients connect here to bridge WorldBrain state and EventBus."""
    # The bridge sends its full WorldBrain snapshot immediately on accept and
    # accepts state_set / event frames. A caller must be authorized before
    # either of those operations, including through the /ws/unity alias.
    try:
        from modules.chat_rooms import _websocket_identity, ROLE_RANK
        identity = _websocket_identity(ws)
    except (ImportError, ValueError):
        await ws.close(code=1008, reason="Unity bridge authentication required")
        return
    if auth_enforced() and (not identity["authenticated"] or
                            ROLE_RANK.get(identity["role"], -1) < ROLE_RANK["crew"]):
        await ws.close(code=1008, reason="Unity bridge requires crew access")
        return
    if unity_bridge is None:
        await ws.close(code=1013, reason="Unity bridge not initialized")
        return
    await unity_bridge.handle_connection(ws)


# — Studio Control WebSocket —

@app.websocket("/studio/ws")
async def studio_control_ws(ws: WebSocket):
    """Studio control surface (studio_control_room.html) connects here."""
    # Both /studio/ws and its /ws/studio alias reach this handler.  Check the
    # verified caller BEFORE accept(), initial-state disclosure, or commands.
    try:
        from modules.chat_rooms import _websocket_identity, ROLE_RANK
        identity = _websocket_identity(ws)
    except (ImportError, ValueError):
        await ws.close(code=1008, reason="Studio authentication required")
        return
    if auth_enforced() and (not identity["authenticated"] or
                            ROLE_RANK.get(identity["role"], -1) < ROLE_RANK["crew"]):
        await ws.close(code=1008, reason="Studio requires crew access")
        return
    if studio_ws_handler is None:
        await ws.accept()
        await ws.send_json({"type": "error", "message": "Studio Control not initialized"})
        await ws.close()
        return

    # StudioWebSocketHandler owns connect/handle_message/disconnect; it has no
    # monolithic ``handle`` method. This lifecycle is the verified Aug-24 repair
    # and must stay in sync with modules/studio_websocket.py.
    await studio_ws_handler.connect(ws)
    try:
        while True:
            data = await ws.receive_json()
            await studio_ws_handler.handle_message(ws, data)
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.warning("studio_control_ws error: %s", exc)
    finally:
        await studio_ws_handler.disconnect(ws)


# — Control room WebSocket (stage_panoramic.html) —
# Registered directly on `app` (not via include_router) and placed BEFORE the
# /ws/{room} catch-all below so it isn't shadowed. main.app.include_router()
# appends its routes as a single lazily-dispatched wrapper at boot time —
# after every route decorated directly on `app` at import time — so a
# router-nested "/ws/control" (as in modules/stage_compat_routes.py, pulled
# in indirectly via create_production_router) always loses precedence to
# this catch-all in the current FastAPI version. Duplicating the handler
# here, ahead of the catch-all, keeps the dedicated control_ready handshake
# working instead of silently falling back to the generic room handler.
@app.websocket("/ws/control")
async def control_websocket(ws: WebSocket):
    room = ws.query_params.get("room") or "control"
    # This endpoint is a backstage control socket, not an alternate unrestricted
    # entry to arbitrary Hub room histories. Preserve the historical 'control'
    # handshake and explicitly recognized 'controlroom' location only.
    if room not in {"control", "controlroom"}:
        await ws.close(code=1008, reason="Invalid control room")
        return
    try:
        from modules.chat_rooms import _websocket_identity, ROLE_RANK
        identity = _websocket_identity(ws)
    except (ImportError, ValueError) as exc:
        await ws.close(code=1008, reason="Control socket authentication required")
        return
    if auth_enforced() and (not identity["authenticated"] or
                            ROLE_RANK.get(identity["role"], -1) < ROLE_RANK["crew"]):
        await ws.close(code=1008, reason="Control room requires crew access")
        return
    if hub is None or not hasattr(hub, "connect"):
        await ws.accept()
        await ws.send_text(json.dumps({"status": "unavailable", "available": False, "subsystem": "control_websocket"}))
        await ws.close()
        return

    await hub.connect(ws, room, uid=identity["user_id"], username=identity["user_id"],
                      role=identity["role"], authenticated=identity["authenticated"])
    try:
        await ws.send_text(json.dumps({"type": "control_ready", "payload": {"room": room}}))
        while True:
            raw = await ws.receive_text()
            if hasattr(hub, "handle_message"):
                await hub.handle_message(ws, room, raw)
    except WebSocketDisconnect:
        pass
    finally:
        if hasattr(hub, "disconnect"):
            await hub.disconnect(ws, room)


# — Production log WebSocket (structured_log_routes.py, same shadowing
# reason as /ws/control above: registered directly, ahead of the catch-all) —
@app.websocket("/api/logs/ws")
async def logs_websocket_direct(websocket: WebSocket):
    """Real-time production log feed."""
    try:
        from modules.chat_rooms import _websocket_identity, ROLE_RANK
        identity = _websocket_identity(websocket)
    except (ImportError, ValueError):
        await websocket.close(code=1008, reason="Log feed authentication required")
        return
    if auth_enforced() and (not identity["authenticated"] or
                            ROLE_RANK.get(identity["role"], -1) < ROLE_RANK["security"]):
        await websocket.close(code=1008, reason="Log feed requires security access")
        return
    await websocket.accept()
    log = get_production_log()
    if not log:
        await websocket.send_json({"error": "Production log not initialized"})
        await websocket.close()
        return

    async def on_event(event):
        try:
            await websocket.send_json(event)
        except Exception:
            pass

    log.subscribe(on_event)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass


# — Chat/production WS (original) —

# — Studio / Unity WebSocket aliases —
# Historical repair restored these compatibility paths because the shipped
# Studio Control frontend connects to /ws/studio and older Unity clients/tests
# use /ws/unity. They must be declared before /ws/{room}: Starlette uses
# first-match routing, so the generic room handler would otherwise swallow
# these dedicated protocols. Canonical handlers remain /studio/ws and
# /unity/ws/{client_id}; these aliases delegate to them and own no extra state.
@app.websocket("/ws/studio")
async def studio_control_ws_alias(ws: WebSocket):
    await studio_control_ws(ws)


@app.websocket("/ws/unity")
async def unity_ws_alias(ws: WebSocket):
    await unity_ws(ws, "default")


# Rooms named like a dedicated protocol (studio, control, unity) cannot be reached
# through /ws/{room}: those paths belong to the studio desk, control room and Unity
# bridge. Stage and avatar pages use this unambiguous path for their Hub room.
@app.websocket("/ws/room/{room}")
async def websocket_named_room(ws: WebSocket, room: str):
    await websocket_room(ws, room)


@app.websocket("/ws/{room}")
async def websocket_room(ws: WebSocket, room: str):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", room):
        await ws.close(code=1008, reason="Invalid room name")
        return
    # Never let the old hub endpoint bypass the shared-world or DM authority.
    if room.casefold() == "world" or room.casefold().startswith(("dm____", "dmv2_")):
        await ws.close(code=1008, reason="Use the role-gated /ws/chat/{room_id} endpoint")
        return
    try:
        from modules.chat_rooms import _websocket_identity, ROOM_REGISTRY, ROLE_RANK
        identity = _websocket_identity(ws)
    except (ImportError, ValueError):
        await ws.close(code=1008, reason="Room socket authentication required")
        return
    # Historical stage clients still use /ws/{room}; protect their registered
    # backstage/social rooms with the SAME role thresholds as /ws/chat/{room}.
    # Production has an explicit allowlist for non-registry legacy studio buses.
    # The dev-only open-room behavior stays available for the existing local
    # choreography and isolated test clients when auth is not enforced.
    legacy_public_rooms = {"main", "pub", "launch", "pubworld_stage", "default", "green"}
    if auth_enforced():
        if room in ROOM_REGISTRY:
            required = ROOM_REGISTRY[room]["min_role"]
            allowed = ROLE_RANK.get(identity["role"], -1) >= ROLE_RANK[required]
        else:
            allowed = room in legacy_public_rooms
        if not allowed:
            await ws.close(code=1008, reason="Room not accessible")
            return
    # The existing auth-off stage/dev mode remains permissive for compatibility;
    # it must NOT be offered to untrusted network clients. Enforced auth is the
    # actual production boundary. Do not mistake 'local dev' for access control.
    if not hub:
        await ws.close(code=1013, reason="Hub not ready")
        return

    # Legacy user_id is a *display hint only* in local development; when
    # authenticated it is never authoritative for bans, mutes or message authors.
    user_id = identity["user_id"] if identity["authenticated"] else (ws.query_params.get("user_id", "") or "")

    if governance and user_id:
        banned, reason = governance.is_banned(user_id)
        if banned:
            await ws.close(code=4403, reason=f"Banned: {reason}")
            return

    user_is_muted = bool(governance and user_id and governance.is_muted(user_id))

    await hub.connect(ws, room, uid=identity["user_id"], username=identity["user_id"],
                      role=identity["role"], authenticated=identity["authenticated"])

    tc = getattr(app.state, "thinking_context", None)
    if tc:
        try:
            await tc.watch_room(room)
        except Exception:
            pass

    try:
        while True:
            raw = await ws.receive_text()

            # Moderation changes take effect for already-open sockets.
            if user_is_muted or (governance and user_id and governance.is_muted(user_id)):
                continue

            # Ethereal avatar messages
            if _HAS_ETHEREAL and ethereal_mgr:
                try:
                    parsed = json.loads(raw)
                    if parsed.get("type", "") in ETHEREAL_TYPES:
                        # Guests may animate their OWN avatars. Do not turn a
                        # legacy browser's user_id field into authority over
                        # another participant's face, body, or gestures.
                        if auth_enforced() and identity["role"] not in {"mod", "owner"}:
                            parsed["user_id"] = identity["user_id"]
                        await handle_ethereal_ws_message(ethereal_mgr, hub, room, parsed)
                        continue
                except Exception:
                    pass

            # Lighting messages
            if lighting_hub_patch:
                try:
                    parsed = json.loads(raw)
                    if (parsed.get("type", "").startswith("lighting_") and
                        (not auth_enforced() or identity["role"] in {"crew", "mod", "owner"})):
                        lighting_hub_patch.handle_message(parsed)
                        continue
                except Exception:
                    pass

            await hub.handle_message(ws, room, raw)

            if tc:
                try:
                    data = json.loads(raw)
                    if data.get("type") == "chat":
                        asyncio.create_task(tc.on_message(
                            room,
                            identity["user_id"] if identity["authenticated"] else data.get("user_id", data.get("user", "anon")),
                            data.get("text", ""),
                        ))
                except Exception:
                    pass

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.warning("WebSocket error in room %r: %s", room, exc)
    finally:
        await hub.disconnect(ws, room)


# —
# Helpers
# —

def _build_character_profiles() -> list:
    if not _HAS_THINKING_CONTEXT or not CharacterProfile or not bot_manager:
        return []
    return [
        CharacterProfile(
            character_id=f"bot-{cfg.bot_id}",
            name=cfg.name,
            role="host" if cfg.auto_reply else "guest",
        )
        for cfg in bot_manager.list_configs()
    ]


# —
# Entry
# —

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )




````
