# Control room original source preservation

Base commit: `62fda27090ef81c747dbc19b9d2543834d58a1c0`.

The following 22 originals are preserved verbatim, including original line endings.

## modules/studio_console_actions.py

SHA-256: 0ebc61cafc31c5ed855fb3a816e4a797e2875480590f7f6f157ea5cfa7d65cd8

`````text
﻿"""Studio console action registry.

This is the click-target mechanism for future console/hotspot art. The image can
place hotspots wherever it wants later; each hotspot only needs an action_id and
optional payload to call these stable backend actions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

from .cameras import CameraManager
from .program_audio import ProgramAudioState, apply_audio_event
from .recording import RecordingService
from .studio_camera_preflight import all_camera_visibility, camera_visibility_report, recording_preflight, studio_readiness


@dataclass(frozen=True)
class StudioActionSpec:
    action_id: str
    label: str
    category: str
    safety: str
    description: str
    required_fields: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "label": self.label,
            "category": self.category,
            "safety": self.safety,
            "description": self.description,
            "required_fields": list(self.required_fields),
        }


_ACTIONS = [
    StudioActionSpec("studio.readiness", "Studio readiness", "studio", "safe", "Check camera, recording, and audio readiness.", []),
    StudioActionSpec("camera.visibility.all", "Check all cameras", "camera", "safe", "Check visibility and recordability for every camera.", []),
    StudioActionSpec("camera.visibility.one", "Check camera", "camera", "safe", "Check one camera source.", ["source_id"]),
    StudioActionSpec("camera.switch.program", "Take program camera", "camera", "mod", "Set the live/program camera.", ["source_id"]),
    StudioActionSpec("camera.switch.preview", "Set preview camera", "camera", "safe", "Set the preview camera.", ["source_id"]),
    StudioActionSpec("camera.cut", "Cut cameras", "camera", "mod", "Swap program and preview.", []),
    StudioActionSpec("recording.preflight", "Recording preflight", "recording", "safe", "Check selected sources and profile before recording.", []),
    StudioActionSpec("recording.start", "Start recording", "recording", "confirm", "Start a recording session after explicit confirmation.", ["confirm"]),
    StudioActionSpec("recording.stop", "Stop recording", "recording", "confirm", "Stop a recording session after explicit confirmation.", ["session_id", "confirm"]),
    StudioActionSpec("audio.status", "Audio status", "audio", "safe", "Read current program audio state.", []),
    StudioActionSpec("audio.event", "Audio event", "audio", "safe", "Apply a validated program audio event.", ["action"]),
    StudioActionSpec("audio.stop_all", "Stop all audio", "audio", "safe", "Stop all active program audio sources.", []),
]


def list_studio_actions() -> List[Dict[str, Any]]:
    return [spec.to_dict() for spec in _ACTIONS]


def _require(payload: Mapping[str, Any], key: str) -> str:
    value = str(payload.get(key) or "").strip()
    if not value:
        raise ValueError(f"{key} is required")
    return value


def _confirmed(payload: Mapping[str, Any]) -> bool:
    return payload.get("confirm") is True or str(payload.get("confirm") or "").strip().lower() == "yes"


def execute_studio_action(
    action_id: str,
    payload: Mapping[str, Any],
    *,
    cameras: CameraManager,
    recording: RecordingService,
    audio_state: ProgramAudioState,
    actor: str = "director",
) -> Dict[str, Any]:
    body = dict(payload or {})
    action_id = str(action_id or "").strip()

    if action_id == "studio.readiness":
        result = studio_readiness(cameras, recording, audio_status=audio_state.status())
    elif action_id == "camera.visibility.all":
        result = all_camera_visibility(cameras)
    elif action_id == "camera.visibility.one":
        source_id = _require(body, "source_id")
        camera = cameras.get(source_id)
        if camera is None:
            raise ValueError(f"Camera source '{source_id}' not found")
        result = camera_visibility_report(camera, cameras.status(source_id))
    elif action_id in {"camera.switch.program", "camera.switch.preview"}:
        source_id = _require(body, "source_id")
        ok = cameras.set_program_source(source_id) if action_id.endswith("program") else cameras.set_preview_source(source_id)
        if not ok:
            raise ValueError(f"Camera source '{source_id}' not found")
        result = {"ok": True, "target": "program" if action_id.endswith("program") else "preview", "source_id": source_id}
    elif action_id == "camera.cut":
        program = cameras.get_program_source()
        preview = cameras.get_preview_source()
        if program is None or preview is None:
            raise ValueError("Both program and preview must be set before cut")
        cameras.set_program_source(preview.source_id)
        cameras.set_preview_source(program.source_id)
        result = {"ok": True, "program": preview.source_id, "preview": program.source_id}
    elif action_id == "recording.preflight":
        sources = body.get("sources") if isinstance(body.get("sources"), list) else []
        result = recording_preflight(
            cameras,
            recording,
            sources=sources,
            profile_id=str(body.get("profile_id") or "broadcast_mp4"),
            host_override=bool(body.get("host_override")),
        )
    elif action_id == "recording.start":
        if not _confirmed(body):
            raise ValueError("recording.start requires confirm=true")
        sources = body.get("sources") if isinstance(body.get("sources"), list) else []
        if not sources:
            program = cameras.get_program_source()
            sources = [program.source_id] if program is not None else []
        session = recording.start_session(
            str(body.get("session_id") or "").strip() or None,
            [str(item) for item in sources],
            profile_id=str(body.get("profile_id") or "broadcast_mp4"),
            operator=actor,
            countdown_seconds=int(body.get("countdown_seconds", 0) or 0),
            host_override=bool(body.get("host_override")),
        )
        result = session.to_dict()
    elif action_id == "recording.stop":
        if not _confirmed(body):
            raise ValueError("recording.stop requires confirm=true")
        result = recording.stop_session(_require(body, "session_id")).to_dict()
    elif action_id == "audio.status":
        result = audio_state.status()
    elif action_id == "audio.event":
        result = apply_audio_event(audio_state, body)
    elif action_id == "audio.stop_all":
        result = apply_audio_event(audio_state, {"action": "stop_all"})
    else:
        raise ValueError(f"Unknown studio action: {action_id}")

    return {"ok": True, "action_id": action_id, "actor": actor, "result": result}


__all__ = ["execute_studio_action", "list_studio_actions", "StudioActionSpec"]

`````

## modules/production_routes.py

SHA-256: a43f81728f1933b84b1dd74eae68779c5b02b4c4645df2677103fdd13c4ef074

`````text
"""
modules/production_routes.py — Camera + Recording REST API
==============================================================================
Wires CameraManager and RecordingService into FastAPI.
Also provides WebSocket broadcast helpers so the control room
console receives live updates on camera switches and recording state.

Usage in main.py:
    from modules.cameras import create_default_cameras
    from modules.recording import create_recording_service
    from modules.production_routes import create_production_router

    cameras = create_default_cameras()
    recording = create_recording_service(DATA_DIR, cameras)
    app.include_router(create_production_router(cameras, recording, hub))

Rear View Foresight LLC — Feic Mo Chroí — 2026-03-24T08:00Z
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse

from modules.cameras import CameraManager, CameraSource, CameraTransport
from modules.recording import (
    RecordingService,
    RecordingState,
    ContainerFormat,
)
from modules.route_security import bound_actor, require_role
from modules.persistence import sanitize_filename, unique_child_path
from modules.runtime_control_routes import create_runtime_control_router
from modules.stage_compat_routes import create_stage_compat_router
from modules.blackbox_runtime import BlackBoxRuntimeWitness
from modules.studio_camera_preflight import all_camera_visibility, camera_visibility_report, recording_preflight, studio_readiness
from modules.program_audio import ProgramAudioState
from modules.program_audio_routes import create_program_audio_router
from modules.studio_console_actions import execute_studio_action, list_studio_actions

logger = logging.getLogger("pubcast.production")


async def _json_dict(request: Request) -> Dict[str, Any]:
    """Parse a request body as a JSON object with clean 400s."""
    try:
        body = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(400, f"Malformed JSON body: {exc.msg}")
    except Exception as exc:
        raise HTTPException(400, f"Invalid JSON body: {exc}")
    if not isinstance(body, dict):
        raise HTTPException(400, "JSON body must be an object")
    return body


def _string_field(body: Dict[str, Any], key: str, *, default: str = "", required: bool = False,
                  max_length: int = 256) -> str:
    value = body.get(key, default)
    if value is None:
        value = default
    if not isinstance(value, str):
        raise HTTPException(400, f"{key} must be a string")
    value = value.strip()
    if required and not value:
        raise HTTPException(400, f"{key} required")
    if len(value) > max_length:
        raise HTTPException(400, f"{key} must be <= {max_length} characters")
    return value


def _bool_field(body: Dict[str, Any], key: str, *, default: bool = False) -> bool:
    value = body.get(key, default)
    if not isinstance(value, bool):
        raise HTTPException(400, f"{key} must be a boolean")
    return value


def _numeric_field(body: Dict[str, Any], key: str, *, default: float | int, minimum: float | None = None) -> float:
    value = body.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise HTTPException(400, f"{key} must be numeric")
    value = float(value)
    if minimum is not None and value < minimum:
        raise HTTPException(400, f"{key} must be >= {minimum}")
    return value


def _vector3(body: Dict[str, Any], key: str) -> List[float]:
    value = body.get(key, [0.0, 0.0, 0.0])
    if not isinstance(value, list) or len(value) != 3:
        raise HTTPException(400, f"{key} must be a 3-item array")
    try:
        vector = [float(v) for v in value]
    except (TypeError, ValueError):
        raise HTTPException(400, f"{key} must contain only numeric values")
    return vector


def _string_list(body: Dict[str, Any], key: str, *, required: bool = False) -> List[str]:
    value = body.get(key, [])
    if value in (None, ""):
        value = []
    if not isinstance(value, list):
        raise HTTPException(400, f"{key} must be an array")
    cleaned: List[str] = []
    for item in value:
        if not isinstance(item, str):
            raise HTTPException(400, f"{key} items must be strings")
        item = item.strip()
        if not item:
            raise HTTPException(400, f"{key} items must not be blank")
        cleaned.append(item)
    if required and not cleaned:
        raise HTTPException(400, f"{key} must contain at least one value")
    return cleaned


def create_production_router(
    cameras: CameraManager,
    recording: RecordingService,
    hub: Any,
    blackbox: Optional[BlackBoxRuntimeWitness] = None,
    program_audio_state: Optional[ProgramAudioState] = None,
    include_overlapping_compat_routes: bool = True,
) -> APIRouter:
    """Create the production API router."""
    router = APIRouter(tags=["Production"])
    program_audio_state = program_audio_state or ProgramAudioState()
    capture_engine = None
    try:
        from modules.capture import FFmpegCaptureEngine
        capture_engine = FFmpegCaptureEngine()
    except Exception as exc:
        logger.warning("FFmpeg capture engine unavailable: %s", exc)

    # Compatibility bridge routes are mounted here because main.py already mounts
    # production_routes after the core runtime managers exist. These bridge routers
    # do not own the systems; they delegate to existing managers and return explicit
    # unavailable payloads instead of letting the panoramic/control-room UI hit 404s.
    router.include_router(create_runtime_control_router(include_overlapping_routes=include_overlapping_compat_routes))
    router.include_router(create_stage_compat_router(hub=hub, cameras=cameras, recording=recording, include_overlapping_routes=include_overlapping_compat_routes))
    router.include_router(create_program_audio_router(program_audio_state, blackbox=blackbox, hub=hub))

    def _blackbox_event(event_type: str, *, source: str, actor: str = "SYS", data: Optional[Dict[str, Any]] = None) -> None:
        if blackbox is not None:
            blackbox.record_event(event_type, source=source, actor=actor, data=data or {})

    async def _start_capture_for_session(session) -> List[str]:
        if capture_engine is None or not getattr(capture_engine, "available", False):
            return []
        if session.state != RecordingState.ACTIVE:
            return []
        source_objects = [cameras.get(source_id) for source_id in session.sources]
        source_objects = [source for source in source_objects if source is not None]
        if not source_objects:
            return []
        profile = recording.get_profile(session.profile_id)
        session_dir = recording._session_dir(session.session_id)
        paths = await capture_engine.start(session.session_id, source_objects, profile, session_dir)
        return [str(path) for path in paths]

    async def _stop_capture_for_session(session_id: str) -> List[Dict[str, Any]]:
        if capture_engine is None or not getattr(capture_engine, "available", False):
            return []
        if not capture_engine.is_capturing(session_id):
            return []
        paths = await capture_engine.stop(session_id)
        artifacts: List[Dict[str, Any]] = []
        for path in paths:
            try:
                artifact = recording.register_artifact(session_id, path)
            except Exception as exc:
                logger.warning("Could not register capture artifact %s for %s: %s", path, session_id, exc)
                continue
            artifacts.append({
                "name": artifact.name,
                "format": artifact.format.value,
                "file_path": artifact.file_path.as_posix(),
                "size_bytes": artifact.size_bytes,
            })
        return artifacts

    # —
    # CAMERAS
    # —

    @router.get("/api/cameras")
    async def list_cameras():
        """List all registered camera sources with status."""
        sources = cameras.list_sources()
        statuses = {s.source_id: s for s in cameras.list_status()}
        pgm = cameras.get_program_source()
        pvw = cameras.get_preview_source()

        return {
            "cameras": [
                {
                    "source_id": cam.source_id,
                    "name": cam.name,
                    "location": cam.location,
                    "transport": cam.transport.value,
                    "endpoint": cam.endpoint,
                    "position": cam.position,
                    "rotation": cam.rotation,
                    "fov": cam.fov,
                    "tags": cam.tags,
                    "status": {
                        "online": statuses.get(cam.source_id, None)
                                  and statuses[cam.source_id].online,
                        "latency_ms": getattr(statuses.get(cam.source_id), "latency_ms", None),
                        "frame_rate": getattr(statuses.get(cam.source_id), "frame_rate", None),
                    },
                }
                for cam in sources
            ],
            "program": pgm.source_id if pgm else None,
            "preview": pvw.source_id if pvw else None,
        }

    @router.get("/api/cameras/program")
    async def get_program_camera():
        """Current program (live/on-air) camera source, if any."""
        pgm = cameras.get_program_source()
        return {"source_id": pgm.source_id if pgm else None}

    @router.get("/api/cameras/preview")
    async def get_preview_camera():
        """Current preview (next-up) camera source, if any."""
        pvw = cameras.get_preview_source()
        return {"source_id": pvw.source_id if pvw else None}

    @router.get("/api/cameras/visibility")
    async def camera_visibility_all(identity: Dict[str, Any] = Depends(require_role("mod"))):
        """Check whether registered cameras are plausibly visible and recordable."""
        report = all_camera_visibility(cameras)
        _blackbox_event(
            "camera.visibility",
            source="recorder",
            actor=str(identity.get("user_id") or "director"),
            data={"camera_count": len(report["cameras"]), "program": report.get("program"), "ok": report.get("ok")},
        )
        return report

    @router.get("/api/cameras/{source_id}/visibility")
    async def camera_visibility_one(source_id: str, identity: Dict[str, Any] = Depends(require_role("mod"))):
        """Check one camera source before switching or recording it."""
        camera = cameras.get(source_id)
        if camera is None:
            raise HTTPException(404, f"Camera source '{source_id}' not found.")
        report = camera_visibility_report(camera, cameras.status(source_id))
        _blackbox_event(
            "camera.visibility",
            source="recorder",
            actor=str(identity.get("user_id") or "director"),
            data={"source_id": source_id, "visible": report.get("visible"), "recordable": report.get("recordable")},
        )
        return report
    @router.post("/api/cameras/switch")
    async def switch_camera(request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
        """Switch program or preview camera. Broadcasts to all control rooms."""
        body = await _json_dict(request)
        target = _string_field(body, "target", default="program", max_length=32) or "program"
        source_id = _string_field(body, "source_id", required=True, max_length=128)

        if target == "program":
            ok = cameras.set_program_source(source_id)
        elif target == "preview":
            ok = cameras.set_preview_source(source_id)
        else:
            raise HTTPException(400, f"Invalid target '{target}'. Use 'program' or 'preview'.")

        if not ok:
            raise HTTPException(404, f"Camera source '{source_id}' not found.")

        _blackbox_event("broadcast.program_frame", source="recorder", actor=str(identity.get("user_id") or "director"), data={"camera_action": "switch", "target": target, "source_id": source_id})

        if hub and not getattr(hub, "camera_events_bridged", False):
            pgm = cameras.get_program_source()
            pvw = cameras.get_preview_source()
            await hub.broadcast_system_event({
                "type": "camera_switch",
                "payload": {
                    "target": target,
                    "source_id": source_id,
                    "program": pgm.source_id if pgm else None,
                    "preview": pvw.source_id if pvw else None,
                    "timestamp": time.time(),
                },
            })

        return {"ok": True, "target": target, "source_id": source_id}

    @router.post("/api/cameras/cut")
    async def cut_cameras(identity: Dict[str, Any] = Depends(require_role("mod"))):
        """Swap program and preview (standard broadcast CUT transition)."""
        pgm = cameras.get_program_source()
        pvw = cameras.get_preview_source()

        if not pgm or not pvw:
            raise HTTPException(400, "Both program and preview must be set to cut.")

        cameras.set_program_source(pvw.source_id)
        cameras.set_preview_source(pgm.source_id)

        _blackbox_event("broadcast.program_frame", source="recorder", actor=str(identity.get("user_id") or "director"), data={"camera_action": "cut", "program": pvw.source_id, "preview": pgm.source_id})

        if hub:
            await hub.broadcast_system_event({
                "type": "camera_cut",
                "payload": {
                    "new_program": pvw.source_id,
                    "new_preview": pgm.source_id,
                    "timestamp": time.time(),
                },
            })

        return {"ok": True, "program": pvw.source_id, "preview": pgm.source_id}

    @router.post("/api/cameras/register")
    async def register_camera(request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
        """Register a new camera source."""
        body = await _json_dict(request)
        try:
            source_id = _string_field(body, "source_id", required=True, max_length=128)
            source = CameraSource(
                source_id=source_id,
                name=_string_field(body, "name", default=source_id, max_length=128),
                location=_string_field(body, "location", default="virtual", max_length=128) or "virtual",
                description=_string_field(body, "description", default="", max_length=512),
                transport=CameraTransport(_string_field(body, "transport", default="virtual", max_length=64) or "virtual"),
                endpoint=_string_field(body, "endpoint", default=f"virtual://{source_id}", max_length=512),
                position=_vector3(body, "position"),
                rotation=_vector3(body, "rotation"),
                fov=_numeric_field(body, "fov", default=60.0, minimum=1.0),
                tags=_string_list(body, "tags"),
            )
        except (KeyError, ValueError) as exc:
            raise HTTPException(400, str(exc))

        cameras.register(source)
        _blackbox_event("broadcast.program_frame", source="recorder", actor=str(identity.get("user_id") or "director"), data={"camera_action": "register", "source_id": source.source_id, "transport": source.transport.value})
        return {"ok": True, "source_id": source.source_id}

    # —
    # RECORDING
    # —

    @router.get("/api/recording/profiles")
    async def list_profiles():
        """List available encoding profiles."""
        profiles = [
            {
                "profile_id": p.profile_id,
                "name": p.name,
                "container": p.container.value,
                "video_codec": p.video_codec,
                "audio_codec": p.audio_codec,
                "resolution": p.resolution,
                "description": p.description,
            }
            for p in recording.list_profiles()
        ]
        return {"profiles": profiles, "count": len(profiles)}

    @router.get("/api/recording/sessions")
    async def list_sessions():
        """List all recording sessions."""
        return [s.to_dict() for s in recording.list_sessions()]

    @router.post("/api/recording/preflight")
    async def recording_preflight_route(request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
        """Validate camera visibility, source policy, and profile availability before recording."""
        body = await _json_dict(request)
        sources = _string_list(body, "sources")
        profile_id = _string_field(body, "profile_id", default="broadcast_mp4", max_length=128) or "broadcast_mp4"
        host_override = _bool_field(body, "host_override", default=False)
        report = recording_preflight(cameras, recording, sources=sources, profile_id=profile_id, host_override=host_override)
        _blackbox_event(
            "recording.preflight",
            source="recording",
            actor=str(identity.get("user_id") or "director"),
            data={"ready": report.get("ready"), "sources": ",".join(report.get("sources", [])), "profile_id": profile_id, "issue_count": len(report.get("issues", []))},
        )
        return report

    @router.get("/api/studio/readiness")
    async def studio_readiness_route(identity: Dict[str, Any] = Depends(require_role("mod"))):
        """Aggregate the current camera and recording readiness for the studio."""
        report = studio_readiness(cameras, recording, audio_status=program_audio_state.status())
        _blackbox_event(
            "studio.readiness",
            source="recording",
            actor=str(identity.get("user_id") or "director"),
            data={"ready": report.get("ready"), "program": report.get("program"), "camera_count": report.get("camera_count"), "recording_profiles": report.get("recording_profiles")},
        )
        return report

    @router.get("/api/studio/actions")
    async def studio_actions_manifest(identity: Dict[str, Any] = Depends(require_role("mod"))):
        """Return stable action IDs that future studio-console hotspots can call."""
        return {"actions": list_studio_actions()}

    @router.post("/api/studio/actions/{action_id}")
    async def studio_action_execute(action_id: str, request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
        """Execute a stable studio action by ID for console art or hotspot overlays."""
        body = await _json_dict(request)
        actor = str(identity.get("user_id") or "director")
        try:
            response = execute_studio_action(
                action_id,
                body,
                cameras=cameras,
                recording=recording,
                audio_state=program_audio_state,
                actor=actor,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc))

        if response.get("ok") and action_id == "recording.start":
            session_data = response.get("result", {})
            session_id = session_data.get("session_id")
            if session_id:
                session = recording.get_session(session_id)
                capture_paths = await _start_capture_for_session(session)
                if capture_paths:
                    session_data["capture_paths"] = capture_paths
        elif response.get("ok") and action_id == "recording.stop":
            session_data = response.get("result", {})
            session_id = session_data.get("session_id") or body.get("session_id")
            if session_id:
                artifacts = await _stop_capture_for_session(str(session_id))
                if artifacts:
                    session_data["artifacts"] = artifacts

        _blackbox_event(
            "studio.action",
            source="recording",
            actor=actor,
            data={"action_id": action_id, "ok": bool(response.get("ok"))},
        )
        if hub:
            await hub.broadcast_system_event({
                "type": "studio_action",
                "payload": {
                    "action_id": action_id,
                    "ok": bool(response.get("ok")),
                    "actor": actor,
                    "result": response.get("result", {}),
                    "timestamp": time.time(),
                },
            })
        return response
    @router.post("/api/recording/start")
    async def start_recording(request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
        """Start a new recording session."""
        body = await _json_dict(request)
        sources = _string_list(body, "sources")
        if not sources:
            pgm = cameras.get_program_source()
            if pgm:
                sources = [pgm.source_id]
            else:
                raise HTTPException(400, "No sources specified and no program source set.")

        profile_id = _string_field(body, "profile_id", default="broadcast_mp4", max_length=128) or "broadcast_mp4"
        operator = bound_actor(request=request, identity=identity, explicit_value=body.get("operator"), field_name="operator") or "director"
        session_id = _string_field(body, "session_id", default="", max_length=128) or None
        countdown = int(_numeric_field(body, "countdown_seconds", default=5, minimum=0))
        host_override = _bool_field(body, "host_override", default=False)

        try:
            session = recording.start_session(
                session_id=session_id,
                sources=sources,
                profile_id=profile_id,
                operator=operator,
                countdown_seconds=countdown,
                host_override=host_override,
            )
        except (ValueError, PermissionError, KeyError) as exc:
            raise HTTPException(400, str(exc))

        capture_paths = await _start_capture_for_session(session)

        if hub:
            await hub.broadcast_system_event({
                "type": "recording_started",
                "payload": {
                    "session_id": session.session_id,
                    "sources": session.sources,
                    "profile_id": session.profile_id,
                    "state": session.state.value,
                    "countdown": countdown,
                    "capture_paths": capture_paths,
                },
            })

        response = session.to_dict()
        if capture_paths:
            response["capture_paths"] = capture_paths
        return response

    @router.post("/api/recording/{session_id}/activate")
    async def activate_recording(session_id: str, identity: Dict[str, Any] = Depends(require_role("mod"))):
        """Activate a recording session (transition from countdown to active)."""
        try:
            session = recording.activate_session(session_id)
        except (KeyError, ValueError) as exc:
            raise HTTPException(400, str(exc))

        capture_paths = await _start_capture_for_session(session)

        if hub:
            await hub.broadcast_system_event({
                "type": "recording_active",
                "payload": {"session_id": session_id, "capture_paths": capture_paths},
            })

        response = session.to_dict()
        if capture_paths:
            response["capture_paths"] = capture_paths
        return response

    @router.post("/api/recording/{session_id}/stop")
    async def stop_recording(session_id: str, identity: Dict[str, Any] = Depends(require_role("mod"))):
        """Stop a recording session."""
        try:
            artifacts = await _stop_capture_for_session(session_id)
            session = recording.stop_session(session_id)
        except KeyError as exc:
            raise HTTPException(404, str(exc))

        if hub:
            await hub.broadcast_system_event({
                "type": "recording_stopped",
                "payload": {
                    "session_id": session_id,
                    "duration": (session.ended_at or time.time()) - session.started_at,
                    "artifacts": artifacts,
                },
            })

        return session.to_dict()

    @router.post("/api/recording/{session_id}/pause")
    async def pause_recording(session_id: str, request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
        """Pause or resume a recording session."""
        body = await _json_dict(request)
        paused = _bool_field(body, "paused", default=True)
        try:
            session = recording.pause_session(session_id, paused)
        except (KeyError, ValueError) as exc:
            raise HTTPException(400, str(exc))
        return session.to_dict()

    @router.post("/api/recording/{session_id}/marker")
    async def add_marker(session_id: str, request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
        """Add a timestamp marker to a recording session."""
        body = await _json_dict(request)
        label = _string_field(body, "label", required=True, max_length=256)
        operator = bound_actor(request=request, identity=identity, explicit_value=body.get("operator"), field_name="operator") if body.get("operator") else identity.get("user_id")
        try:
            marker = recording.mark_moment(session_id, label, operator)
        except KeyError as exc:
            raise HTTPException(404, str(exc))
        return {"ok": True, "timestamp": marker.timestamp, "label": marker.label}

    @router.post("/api/recording/{session_id}/export")
    async def export_recording(session_id: str, request: Request, identity: Dict[str, Any] = Depends(require_role("mod"))):
        """Export a recording session as a zip bundle."""
        body = await _json_dict(request)
        container = _string_field(body, "format", default="mp4", max_length=16) or "mp4"
        try:
            fmt = ContainerFormat(container)
        except ValueError:
            raise HTTPException(400, f"Invalid format '{container}'. Use: mp4, webm, wav, mov")

        try:
            export_path = await asyncio.to_thread(
                recording.export_session, session_id, container=fmt
            )
        except (KeyError, ValueError) as exc:
            raise HTTPException(400, str(exc))

        return FileResponse(
            export_path,
            media_type="application/zip",
            filename=export_path.name,
        )

    @router.post("/api/recording/import")
    async def import_recording(file: UploadFile = File(...), identity: Dict[str, Any] = Depends(require_role("mod"))):
        """Import a recording session from a zip bundle."""
        import_dir = recording.imports_dir
        filename = sanitize_filename(file.filename or "")
        if not filename:
            raise HTTPException(400, "Uploaded file must have a filename")
        if not filename.lower().endswith(".zip"):
            raise HTTPException(400, "Recording import requires a .zip bundle")
        import_path = unique_child_path(import_dir, filename)
        with open(import_path, "wb") as f:
            content = await file.read()
            f.write(content)
        try:
            session = recording.import_session(import_path)
        except (ValueError, FileNotFoundError) as exc:
            raise HTTPException(400, str(exc))
        return session.to_dict()

    @router.get("/api/recording/storage")
    async def storage_status():
        """Get recording storage usage."""
        return recording.storage_status()

    @router.get("/api/recording/privacy")
    async def privacy_matrix():
        """Get recording privacy rules per room."""
        return recording.privacy_matrix()

    # —
    # PANIC / Emergency
    # —

    @router.post("/api/production/panic")
    async def production_panic(identity: Dict[str, Any] = Depends(require_role("mod"))):
        """Emergency: stop all recordings, mute, fade to black."""
        stopped = []
        for session in recording.list_sessions():
            if session.state in (RecordingState.ACTIVE, RecordingState.COUNTDOWN):
                recording.stop_session(session.session_id)
                stopped.append(session.session_id)

        if hub:
            await hub.broadcast_system_event({
                "type": "production_panic",
                "payload": {
                    "timestamp": time.time(),
                    "sessions_stopped": stopped,
                    "message": "PANIC — all recordings stopped, fade to black",
                },
            })
            hub.update_production_state({
                "on_air": False,
                "camera": "black",
                "lower_third": "",
            })

        return {"ok": True, "sessions_stopped": stopped}

    return router








`````

## modules/capture.py

SHA-256: 78c9703490adf297a91c10ba484692201f4e4682841aa208a80239b71b1c427d

`````text
"""
modules/capture.py  —  PubCast AI FFmpeg Capture Engine
=========================================================
Sits alongside RecordingService. When a session is ACTIVE,
FFmpegCaptureEngine spawns one FFmpeg process per source,
writes real media files into the session directory, and
registers them as RecordingArtifacts when stopped.

Transport → FFmpeg input mapping
---------------------------------
  virtual      → lavfi testsrc (safe fallback, always works)
  file         → -i <endpoint>
  rtmp         → -i rtmp://...
  srt          → -i srt://...
  ndi          → -i 'device_name()=<endpoint>' via libndi_newtek (if available)
  voxel_3d     → -i <endpoint> (TCP stream from Rust renderer)

Environment:
  PUBCAST_FFMPEG   path to ffmpeg binary  (default: ffmpeg on PATH)
"""
from __future__ import annotations

import asyncio
import logging
import os
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ── FFmpeg resolution ──────────────────────────────────────────────────────────
def _ffmpeg_bin() -> str:
    env = os.environ.get("PUBCAST_FFMPEG", "")
    if env and Path(env).is_file():
        return env
    found = shutil.which("ffmpeg")
    if found:
        return found
    raise EnvironmentError(
        "ffmpeg not found. Install ffmpeg and ensure it is on PATH, "
        "or set the PUBCAST_FFMPEG environment variable to the binary path."
    )


# ── Transport → FFmpeg input builder ─────────────────────────────────────────
def _build_ffmpeg_input(transport: str, endpoint: str) -> List[str]:
    """Return the FFmpeg input argument list for a given camera source."""
    t = transport.lower()

    if t == "virtual":
        # Lavfi test pattern — reliable fallback that always works
        return ["-f", "lavfi", "-i", "testsrc=size=1920x1080:rate=30"]

    if t == "file":
        return ["-re", "-i", endpoint]          # -re = real-time read-back

    if t in ("rtmp", "srt"):
        return ["-i", endpoint]

    if t == "ndi":
        # Requires FFmpeg built with libndi_newtek
        return ["-f", "libndi_newtek", "-i", endpoint]

    if t == "voxel_3d":
        # TCP stream from the Rust/Voxel renderer
        return ["-i", endpoint]

    # Unknown — try as raw input and hope for the best
    logger.warning("Unknown transport '%s' for endpoint '%s' — using raw -i", t, endpoint)
    return ["-i", endpoint]


def _ffmpeg_bitrate(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    clean = str(value).strip()
    lower = clean.lower()
    if lower.endswith("mbps"):
        return clean[:-4] + "M"
    if lower.endswith("kbps"):
        return clean[:-4] + "k"
    return clean


# ── Encoding profile → FFmpeg output args ─────────────────────────────────────
def _build_ffmpeg_output(profile, output_path: Path) -> List[str]:
    """Return FFmpeg codec/output arguments from an EncodingProfile."""
    args: List[str] = []

    if profile.video_codec and not profile.is_audio_only:
        video_codec = "libx264" if profile.video_codec == "h264" else profile.video_codec
        args += ["-c:v", video_codec]
        video_bitrate = _ffmpeg_bitrate(profile.video_bitrate)
        if video_bitrate:
            args += ["-b:v", video_bitrate]
        if profile.resolution:
            w, h = profile.resolution.split("x")
            args += ["-s", f"{w}x{h}"]
        if profile.frame_rate:
            args += ["-r", profile.frame_rate]
        if video_codec == "libx264":
            args += ["-pix_fmt", "yuv420p"]
    else:
        args += ["-vn"]   # no video

    if profile.audio_codec:
        args += ["-c:a", profile.audio_codec]
        audio_bitrate = _ffmpeg_bitrate(profile.audio_bitrate)
        if audio_bitrate:
            args += ["-b:a", audio_bitrate]
    else:
        args += ["-an"]

    args.append(str(output_path))
    return args


# ── Per-source process handle ─────────────────────────────────────────────────
@dataclass
class _CaptureProcess:
    source_id: str
    output_path: Path
    proc: asyncio.subprocess.Process
    started_at: float = field(default_factory=time.time)

    async def terminate(self) -> None:
        if self.proc.returncode is None:
            try:
                if self.proc.stdin:
                    self.proc.stdin.write(b"q")
                    await self.proc.stdin.drain()
                await asyncio.wait_for(self.proc.wait(), timeout=8.0)
            except asyncio.TimeoutError:
                try:
                    self.proc.terminate()
                    await asyncio.wait_for(self.proc.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    self.proc.kill()
                    await self.proc.wait()
            except (BrokenPipeError, ConnectionResetError):
                await self.proc.wait()
        logger.info("Capture process for %s finished (rc=%s)", self.source_id, self.proc.returncode)


# ── Capture Engine ────────────────────────────────────────────────────────────
class FFmpegCaptureEngine:
    """
    Manages FFmpeg processes for active recording sessions.
    One engine instance lives for the lifetime of the server.
    """

    def __init__(self) -> None:
        self._active: Dict[str, List[_CaptureProcess]] = {}   # session_id → [processes]
        try:
            self._bin = _ffmpeg_bin()
            logger.info("FFmpegCaptureEngine ready: %s", self._bin)
        except EnvironmentError as e:
            self._bin = None
            logger.warning("FFmpegCaptureEngine: %s  —  capture disabled.", e)

    @property
    def available(self) -> bool:
        return self._bin is not None

    # ── Public API ─────────────────────────────────────────────────────────────
    async def start(
        self,
        session_id: str,
        sources,          # list of CameraSource objects
        profile,          # EncodingProfile object
        session_dir: Path,
    ) -> List[Path]:
        """
        Spawn one FFmpeg process per source.
        Returns list of output file paths (one per source).
        """
        if not self.available:
            logger.warning("FFmpeg not available — session %s will have no media.", session_id)
            return []

        if session_id in self._active:
            logger.warning("Session %s already capturing — ignoring duplicate start.", session_id)
            return [cp.output_path for cp in self._active[session_id]]

        procs: List[_CaptureProcess] = []
        output_paths: List[Path] = []

        for src in sources:
            ext = profile.container.value          # mp4 / webm / wav / mov
            safe_name = src.source_id.replace("/", "_").replace(":", "_")
            out_path = session_dir / f"{safe_name}.{ext}"

            input_args  = _build_ffmpeg_input(src.transport.value, src.endpoint)
            output_args = _build_ffmpeg_output(profile, out_path)

            cmd = [self._bin, "-y"] + input_args + output_args
            logger.info("FFmpeg cmd for %s: %s", src.source_id, " ".join(cmd))

            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                cp = _CaptureProcess(
                    source_id=src.source_id,
                    output_path=out_path,
                    proc=proc,
                )
                procs.append(cp)
                output_paths.append(out_path)
                logger.info("Capture started for %s → %s (pid=%d)", src.source_id, out_path, proc.pid)

            except Exception as e:
                logger.error("Failed to start FFmpeg for %s: %s", src.source_id, e)

        if procs:
            self._active[session_id] = procs

        return output_paths

    async def stop(self, session_id: str) -> List[Path]:
        """
        Terminate all FFmpeg processes for a session.
        Returns list of completed output file paths.
        """
        procs = self._active.pop(session_id, [])
        output_paths: List[Path] = []

        for cp in procs:
            await cp.terminate()
            if cp.output_path.exists() and cp.output_path.stat().st_size > 0:
                output_paths.append(cp.output_path)
                logger.info("Artifact ready: %s (%d bytes)", cp.output_path, cp.output_path.stat().st_size)
            else:
                logger.warning("No media written for %s — file missing or empty.", cp.source_id)

        return output_paths

    async def pause(self, session_id: str) -> None:
        """Send SIGSTOP to all processes (Unix) or no-op on Windows."""
        for cp in self._active.get(session_id, []):
            if cp.proc.returncode is None:
                try:
                    import signal
                    cp.proc.send_signal(signal.SIGSTOP)
                except (AttributeError, ProcessLookupError, OSError):
                    pass   # Windows: SIGSTOP not available — silently skip

    async def resume(self, session_id: str) -> None:
        """Send SIGCONT to all processes (Unix) or no-op on Windows."""
        for cp in self._active.get(session_id, []):
            if cp.proc.returncode is None:
                try:
                    import signal
                    cp.proc.send_signal(signal.SIGCONT)
                except (AttributeError, ProcessLookupError, OSError):
                    pass

    def is_capturing(self, session_id: str) -> bool:
        return session_id in self._active

    def active_sessions(self) -> List[str]:
        return list(self._active.keys())

    async def shutdown(self) -> None:
        """Graceful shutdown — stop all active captures."""
        for sid in list(self._active.keys()):
            await self.stop(sid)
        logger.info("FFmpegCaptureEngine shut down.")

`````

## static/studio_console_hotspots.js

SHA-256: 468d878e596b6cdb8fc08819234e37ae082109daabdb001fa045bc993b5f3a9e

`````text
/*
 * PubCast studio console hotspot adapter.
 *
 * This creates no visible UI. It lets future console art bind click/touch
 * hotspots to stable backend studio action IDs.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.PubCastStudioConsoleHotspots = factory();
  }
})(typeof globalThis !== "undefined" ? globalThis : window, function () {
  "use strict";

  function parseJsonObject(value, fallback) {
    if (!value) return fallback || {};
    try {
      const parsed = JSON.parse(value);
      return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : fallback || {};
    } catch (_err) {
      return fallback || {};
    }
  }

  function readElementPayload(element) {
    const payload = parseJsonObject(element.getAttribute("data-studio-payload"), {});
    const attrs = element.attributes || [];
    for (let index = 0; index < attrs.length; index += 1) {
      const attr = attrs[index];
      if (!attr || !attr.name || !attr.name.startsWith("data-studio-param-")) continue;
      const key = attr.name.slice("data-studio-param-".length).replace(/-([a-z])/g, function (_match, char) {
        return char.toUpperCase();
      });
      payload[key] = attr.value;
    }
    return payload;
  }

  function emitTargetEvent(target, name, detail) {
    if (!target || typeof target.dispatchEvent !== "function" || typeof CustomEvent !== "function") return;
    target.dispatchEvent(new CustomEvent(name, { bubbles: true, detail: detail }));
  }

  function requiresConfirmation(actionId, element, spec) {
    const attr = element && typeof element.getAttribute === "function"
      ? String(element.getAttribute("data-studio-confirm") || "").toLowerCase()
      : "";
    if (attr === "false" || attr === "off" || attr === "0") return false;
    if (attr === "true" || attr === "yes" || attr === "1") return true;
    if (spec && spec.safety === "confirm") return true;
    return actionId === "recording.start" || actionId === "recording.stop";
  }

  function buildConfirmModel(actionId, payload, spec) {
    const label = spec && spec.label ? spec.label : actionId;
    const sources = Array.isArray(payload && payload.sources) ? payload.sources.join(", ") : "";
    const details = [];
    if (payload && payload.session_id) details.push("Session: " + payload.session_id);
    if (payload && payload.source_id) details.push("Source: " + payload.source_id);
    if (sources) details.push("Sources: " + sources);
    return {
      actionId: actionId,
      label: label,
      title: actionId === "recording.stop" ? "Stop Recording" : "Confirm Studio Action",
      message: "Confirm " + label + ".",
      details: details,
      confirmText: actionId === "recording.stop" ? "Stop" : "Confirm",
      cancelText: "Cancel",
    };
  }

  function defaultConfirm(model) {
    if (typeof document === "undefined") return Promise.resolve(true);
    return new Promise((resolve) => {
      const overlay = document.createElement("div");
      overlay.className = "pubcast-studio-confirm";
      overlay.innerHTML = [
        '<div class="pubcast-studio-confirm__panel" role="dialog" aria-modal="true">',
        '<div class="pubcast-studio-confirm__eyebrow">Studio Control</div>',
        '<h2>' + escapeHtml(model.title) + "</h2>",
        '<p>' + escapeHtml(model.message) + "</p>",
        model.details.length ? '<ul>' + model.details.map((item) => '<li>' + escapeHtml(item) + "</li>").join("") + "</ul>" : "",
        '<div class="pubcast-studio-confirm__actions">',
        '<button type="button" data-confirm-cancel>' + escapeHtml(model.cancelText) + "</button>",
        '<button type="button" data-confirm-ok>' + escapeHtml(model.confirmText) + "</button>",
        "</div>",
        "</div>",
      ].join("");
      ensureConfirmStyles();
      document.body.appendChild(overlay);
      const done = (value) => {
        document.removeEventListener("keydown", onKey);
        overlay.remove();
        resolve(value);
      };
      const onKey = (event) => {
        if (event.key === "Escape") done(false);
        if (event.key === "Enter") done(true);
      };
      overlay.querySelector("[data-confirm-cancel]").addEventListener("click", () => done(false));
      overlay.querySelector("[data-confirm-ok]").addEventListener("click", () => done(true));
      document.addEventListener("keydown", onKey);
      overlay.querySelector("[data-confirm-ok]").focus();
    });
  }

  function ensureConfirmStyles() {
    if (typeof document === "undefined" || document.getElementById("pubcast-studio-confirm-styles")) return;
    const style = document.createElement("style");
    style.id = "pubcast-studio-confirm-styles";
    style.textContent = [
      ".pubcast-studio-confirm{position:fixed;inset:0;z-index:9999;display:grid;place-items:center;background:rgba(3,4,8,.72);backdrop-filter:blur(8px);padding:18px}",
      ".pubcast-studio-confirm__panel{width:min(420px,100%);background:#101217;color:#f4efe2;border:1px solid rgba(232,255,71,.38);border-radius:8px;padding:20px;box-shadow:0 24px 80px rgba(0,0,0,.55);font-family:Segoe UI,system-ui,sans-serif}",
      ".pubcast-studio-confirm__eyebrow{font:700 11px Consolas,monospace;letter-spacing:.16em;text-transform:uppercase;color:#e8ff47;margin-bottom:10px}",
      ".pubcast-studio-confirm h2{font-size:22px;line-height:1.15;margin:0 0 10px}",
      ".pubcast-studio-confirm p{margin:0 0 12px;color:#c9d0dc;line-height:1.4}",
      ".pubcast-studio-confirm ul{margin:0 0 16px;padding-left:18px;color:#9ca3af;font:12px Consolas,monospace}",
      ".pubcast-studio-confirm__actions{display:flex;justify-content:flex-end;gap:10px}",
      ".pubcast-studio-confirm button{border:1px solid #343a46;background:#181c24;color:#f4efe2;border-radius:6px;padding:9px 13px;font-weight:700;cursor:pointer}",
      ".pubcast-studio-confirm button[data-confirm-ok]{border-color:#ff6b6b;background:rgba(255,107,107,.18);color:#ffd2d2}",
      ".pubcast-studio-confirm button:focus{outline:2px solid #47c8ff;outline-offset:2px}",
    ].join("");
    document.head.appendChild(style);
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, function (char) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char];
    });
  }

  class StudioConsoleHotspots {
    constructor(options) {
      const config = options || {};
      this.fetchImpl = config.fetchImpl || (typeof fetch === "function" ? fetch.bind(globalThis) : null);
      this.baseUrl = String(config.baseUrl || "").replace(/\/$/, "");
      this.confirmImpl = config.confirmImpl || defaultConfirm;
      this._actionsPromise = null;
      this.lastAction = null;
    }

    async actions() {
      const response = await this._fetch("/api/studio/actions", { method: "GET" });
      return response.actions || [];
    }

    async actionSpec(actionId) {
      this._actionsPromise = this._actionsPromise || this.actions().catch(() => []);
      const actions = await this._actionsPromise;
      return actions.find((item) => item.action_id === actionId) || null;
    }

    async execute(actionId, payload) {
      const cleanActionId = String(actionId || "").trim();
      if (!cleanActionId) throw new Error("studio action_id is required");
      const response = await this._fetch("/api/" + "studio/actions/" + encodeURIComponent(cleanActionId), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload || {}),
      });
      this.lastAction = response;
      return response;
    }

    async executeConfirmed(actionId, payload, context) {
      const body = Object.assign({}, payload || {});
      const spec = (context && context.spec) || await this.actionSpec(actionId);
      if (requiresConfirmation(actionId, context && context.element, spec)) {
        const approved = await this.confirmImpl(buildConfirmModel(actionId, body, spec));
        if (!approved) {
          return { ok: false, canceled: true, action_id: actionId };
        }
        body.confirm = true;
      }
      return this.execute(actionId, body);
    }

    bind(rootElement) {
      const rootNode = rootElement || (typeof document !== "undefined" ? document : null);
      if (!rootNode || typeof rootNode.querySelectorAll !== "function") return 0;
      const nodes = rootNode.querySelectorAll("[data-studio-action]");
      nodes.forEach((node) => {
        if (node.__pubcastStudioHotspotBound) return;
        node.__pubcastStudioHotspotBound = true;
        node.addEventListener("click", async (event) => {
          event.preventDefault();
          const actionId = node.getAttribute("data-studio-action");
          const payload = readElementPayload(node);
          emitTargetEvent(node, "pubcast:studio-action-start", { actionId: actionId, payload: payload });
          try {
            const result = await this.executeConfirmed(actionId, payload, { element: node });
            if (result && result.canceled) {
              emitTargetEvent(node, "pubcast:studio-action-cancel", { actionId: actionId, payload: payload });
              return;
            }
            emitTargetEvent(node, "pubcast:studio-action-success", { actionId: actionId, payload: payload, result: result });
          } catch (err) {
            emitTargetEvent(node, "pubcast:studio-action-error", {
              actionId: actionId,
              payload: payload,
              message: err && err.message ? err.message : String(err),
            });
          }
        });
      });
      return nodes.length;
    }

    async _fetch(path, options) {
      if (!this.fetchImpl) throw new Error("fetch is not available for studio console hotspots");
      const response = await this.fetchImpl(this.baseUrl + path, options || {});
      const data = response && typeof response.json === "function" ? await response.json() : {};
      if (!response || !response.ok) {
        const message = data && data.detail ? data.detail : "Studio console request failed";
        throw new Error(message);
      }
      return data;
    }
  }

  return {
    StudioConsoleHotspots: StudioConsoleHotspots,
    buildConfirmModel: buildConfirmModel,
    readElementPayload: readElementPayload,
    requiresConfirmation: requiresConfirmation,
  };
});

`````

## static/console_hotspot_renderer.js

SHA-256: 8429f1d0d706c2d65eb09adab024ebcc7157c8853ef05ff423946fe7f54a9ad2

`````text
/*
 * PubCast image console renderer.
 *
 * Loads a hotspot manifest with source image dimensions, places controls over
 * the console art, and forwards actions through studio_console_hotspots.js.
 */
(function () {
  "use strict";

  const state = {
    manifest: null,
    adapter: null,
    values: new Map(),
  };

  function clamp01(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) return 0;
    return Math.max(0, Math.min(1, number));
  }

  function el(tag, attrs, text) {
    const node = document.createElement(tag);
    Object.entries(attrs || {}).forEach(([key, value]) => {
      if (value === undefined || value === null) return;
      if (key === "className") node.className = value;
      else if (key === "style") Object.assign(node.style, value);
      else node.setAttribute(key, value);
    });
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function actionPayload(hotspot, extra) {
    const payload = Object.assign({}, hotspot.payload || {}, extra || {});
    if (payload.action === "set_volume" && payload.level === undefined) {
      payload.level = payload.value !== undefined ? payload.value : 0.5;
    }
    return payload;
  }

  async function executeHotspot(hotspot, extra) {
    if (!hotspot || !hotspot.action_id || !state.adapter) return;
    setStatus("Sending " + hotspot.label + "...");
    try {
      const result = await state.adapter.executeConfirmed(hotspot.action_id, actionPayload(hotspot, extra), {
        spec: hotspot.safety ? { safety: hotspot.safety, label: hotspot.label } : null,
      });
      if (result && result.canceled) {
        setStatus(hotspot.label + " canceled.");
        return;
      }
      setStatus(hotspot.label + " ok.");
    } catch (err) {
      setStatus((err && err.message) || String(err), true);
    }
  }

  function setStatus(message, isError) {
    const node = document.querySelector("[data-console-status]");
    if (!node) return;
    node.textContent = message;
    node.dataset.level = isError ? "error" : "ok";
  }

  function hotspotStyle(hotspot) {
    return {
      left: (hotspot.x * 100) + "%",
      top: (hotspot.y * 100) + "%",
      width: (hotspot.w * 100) + "%",
      height: (hotspot.h * 100) + "%",
    };
  }

  function makeButton(hotspot) {
    const node = el("button", {
      className: "pc-console-hotspot pc-console-hotspot--" + hotspot.kind,
      type: "button",
      title: hotspot.label,
      "aria-label": hotspot.label,
      "data-studio-action": hotspot.action_id,
      style: hotspotStyle(hotspot),
    });
    node.addEventListener("click", async () => {
      node.classList.toggle("is-active", hotspot.kind === "button" || hotspot.kind === "fan");
      await executeHotspot(hotspot);
    });
    return node;
  }

  function makeSlider(hotspot) {
    const wrap = el("div", {
      className: "pc-console-hotspot pc-console-slider",
      title: hotspot.label,
      style: hotspotStyle(hotspot),
    });
    const input = el("input", {
      type: "range",
      min: "0",
      max: "100",
      value: String(Math.round((hotspot.default_value || 0.55) * 100)),
      "aria-label": hotspot.label,
    });
    const send = () => {
      const value = clamp01(Number(input.value) / 100);
      state.values.set(hotspot.id, value);
      executeHotspot(hotspot, { value: value, level: value });
    };
    input.addEventListener("change", send);
    input.addEventListener("pointerup", send);
    wrap.appendChild(input);
    return wrap;
  }

  function makeKnob(hotspot) {
    const node = makeButton(hotspot);
    node.classList.add("pc-console-knob");
    state.values.set(hotspot.id, hotspot.default_value || 0.5);

    const setValue = (value) => {
      const clean = clamp01(value);
      state.values.set(hotspot.id, clean);
      node.style.setProperty("--turn", ((clean * 270) - 135) + "deg");
      executeHotspot(hotspot, { value: clean, level: clean });
    };

    node.addEventListener("wheel", (event) => {
      event.preventDefault();
      setValue((state.values.get(hotspot.id) || 0.5) + (event.deltaY < 0 ? 0.05 : -0.05));
    }, { passive: false });

    let startX = 0;
    let startValue = 0.5;
    node.addEventListener("pointerdown", (event) => {
      startX = event.clientX;
      startValue = state.values.get(hotspot.id) || 0.5;
      node.setPointerCapture(event.pointerId);
    });
    node.addEventListener("pointerup", (event) => {
      if (!node.hasPointerCapture(event.pointerId)) return;
      node.releasePointerCapture(event.pointerId);
      setValue(startValue + ((event.clientX - startX) / 160));
    });
    node.style.setProperty("--turn", "0deg");
    return node;
  }

  function renderHotspot(hotspot) {
    if (hotspot.kind === "slider") return makeSlider(hotspot);
    if (hotspot.kind === "knob" || hotspot.kind === "dial") return makeKnob(hotspot);
    return makeButton(hotspot);
  }

  function validateManifest(manifest) {
    if (!manifest || !manifest.image || !manifest.image.width_px || !manifest.image.height_px) {
      throw new Error("Console manifest is missing source image dimensions.");
    }
    if (!Array.isArray(manifest.hotspots)) throw new Error("Console manifest hotspots must be an array.");
    manifest.hotspots.forEach((hotspot) => {
      ["x", "y", "w", "h"].forEach((key) => {
        const value = Number(hotspot[key]);
        if (!Number.isFinite(value) || value < 0 || value > 1) {
          throw new Error("Invalid hotspot coordinate for " + (hotspot.id || "unknown"));
        }
      });
    });
  }

  async function init() {
    const root = document.querySelector("[data-console-manifest]");
    if (!root) return;
    const manifestPath = root.getAttribute("data-console-manifest");
    state.adapter = new window.PubCastStudioConsoleHotspots.StudioConsoleHotspots();

    const response = await fetch(manifestPath);
    state.manifest = await response.json();
    validateManifest(state.manifest);

    const frame = el("div", { className: "pc-console-frame" });
    const image = el("img", {
      className: "pc-console-image",
      src: state.manifest.image.clean_path,
      alt: state.manifest.console_id,
      width: String(state.manifest.image.width_px),
      height: String(state.manifest.image.height_px),
    });
    const layer = el("div", { className: "pc-console-layer" });
    state.manifest.hotspots.forEach((hotspot) => layer.appendChild(renderHotspot(hotspot)));
    frame.appendChild(image);
    frame.appendChild(layer);
    root.appendChild(frame);

    const meta = document.querySelector("[data-console-meta]");
    if (meta) {
      meta.textContent = state.manifest.console_id + " map " + state.manifest.image.width_px + " x " + state.manifest.image.height_px;
    }
    setStatus("Console ready.");
  }

  window.PubCastConsoleHotspotRenderer = { init: init, validateManifest: validateManifest };
  document.addEventListener("DOMContentLoaded", () => init().catch((err) => setStatus(err.message || String(err), true)));
})();

`````

## static/console_hotspot_renderer.css

SHA-256: 49e9f1c9b09f5bce45ea1a2db1f9d54bf486fecc3c6c3aff8571845b977abdfe

`````text
html,
body {
  min-height: 100%;
}

body.pc-console-page {
  margin: 0;
  background: #090b0f;
  color: #f3efe4;
  font-family: "Segoe UI", system-ui, sans-serif;
}

.pc-console-shell {
  min-height: 100vh;
  display: grid;
  grid-template-rows: auto 1fr auto;
}

.pc-console-topbar,
.pc-console-statusbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 14px;
  background: rgba(9, 11, 15, 0.92);
  border-bottom: 1px solid rgba(212, 177, 93, 0.28);
}

.pc-console-statusbar {
  border-top: 1px solid rgba(212, 177, 93, 0.28);
  border-bottom: 0;
  font: 12px Consolas, monospace;
  color: #aeb7c2;
}

.pc-console-title {
  margin: 0;
  font-size: 15px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.pc-console-meta {
  font: 12px Consolas, monospace;
  color: #9fb7c9;
}

.pc-console-mount {
  display: grid;
  place-items: center;
  min-height: 0;
  overflow: auto;
  padding: 12px;
}

.pc-console-frame {
  position: relative;
  width: min(100%, 1400px);
  line-height: 0;
}

.pc-console-image {
  width: 100%;
  height: auto;
  display: block;
  user-select: none;
}

.pc-console-layer {
  position: absolute;
  inset: 0;
}

.pc-console-hotspot {
  position: absolute;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  color: transparent;
  padding: 0;
}

.pc-console-hotspot:hover,
.pc-console-hotspot:focus-visible {
  outline: 2px solid rgba(93, 238, 255, 0.86);
  outline-offset: 1px;
  background: rgba(93, 238, 255, 0.08);
}

.pc-console-hotspot.is-active {
  background: rgba(136, 255, 218, 0.20);
  box-shadow: 0 0 18px rgba(136, 255, 218, 0.42);
}

.pc-console-hotspot--monitor:hover,
.pc-console-hotspot--monitor:focus-visible {
  outline-color: rgba(255, 78, 220, 0.88);
  background: rgba(255, 78, 220, 0.08);
}

.pc-console-slider {
  display: grid;
  place-items: center;
  transform: rotate(-8deg);
}

.pc-console-slider input {
  width: 100%;
  accent-color: #e8f0f4;
  opacity: 0.56;
}

.pc-console-knob::after {
  content: "";
  position: absolute;
  left: 46%;
  top: 18%;
  width: 8%;
  height: 32%;
  border-radius: 999px;
  background: rgba(215, 255, 96, 0.7);
  transform: rotate(var(--turn, 0deg));
  transform-origin: 50% 100%;
}

[data-console-status][data-level="error"] {
  color: #ffaaa2;
}

[data-console-status][data-level="ok"] {
  color: #bdf4cb;
}

`````

## static/director_console.html

SHA-256: 7e661896b27a8c0ddebe337a6fdfce7b2c092cc1b71f4c58219079fd1d6e67d3

`````text
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PubCast Director Console</title>
  <link rel="stylesheet" href="/static/console_hotspot_renderer.css">
</head>
<body class="pc-console-page">
  <main class="pc-console-shell">
    <header class="pc-console-topbar">
      <h1 class="pc-console-title">Director Console</h1>
      <div class="pc-console-meta" data-console-meta>director_console map 1024 x 1024</div>
    </header>
    <section class="pc-console-mount" data-console-manifest="/static/director_console_hotspot_manifest.json"></section>
    <footer class="pc-console-statusbar">
      <span data-console-status>Loading console...</span>
      <span>Studio actions live</span>
    </footer>
  </main>
  <script src="/static/studio_console_hotspots.js"></script>
  <script src="/static/console_hotspot_renderer.js"></script>
</body>
</html>

`````

## static/audio_console.html

SHA-256: 87e541d30f19b09cba3a6200c26b4ab7c3f5db1544d078bca967e62498ed606d

`````text
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PubCast Audio Console</title>
  <link rel="stylesheet" href="/static/console_hotspot_renderer.css">
</head>
<body class="pc-console-page">
  <main class="pc-console-shell">
    <header class="pc-console-topbar">
      <h1 class="pc-console-title">Audio Console</h1>
      <div class="pc-console-meta" data-console-meta>audio_console map 1408 x 768</div>
    </header>
    <section class="pc-console-mount" data-console-manifest="/static/audio_console_hotspot_manifest.json"></section>
    <footer class="pc-console-statusbar">
      <span data-console-status>Loading console...</span>
      <span>Studio actions live</span>
    </footer>
  </main>
  <script src="/static/studio_console_hotspots.js"></script>
  <script src="/static/console_hotspot_renderer.js"></script>
</body>
</html>

`````

## static/control_room.html

SHA-256: 7e18a19ce960cc924f085251dcbfb09ab3a9eed46545edf7677850f844590d1d

`````text
﻿<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PubCast AI â€” Control Room</title>
<style>
:root{
  --red:#ff2222;--green:#22dd66;--brass:#e5c17e;--teal:#6dd6c7;
  --cream:#f0e8d8;--cream-dim:#8a8070;--crt-green:#33ff99;
  --gold:#c9a84c;--gold-d:rgba(201,168,76,.3);
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{
  background:#060505;color:var(--cream);font-family:Consolas, 'Courier New', monospace;
  min-height:100vh;overflow-x:hidden;display:flex;flex-direction:column;
  align-items:center;justify-content:center;
}
.console-wrap{position:relative;width:100%;max-width:1200px;user-select:none}
.console-img{width:100%;height:auto;display:block;filter:brightness(1.05) contrast(1.05) saturate(1.1)}
.hotspot{position:absolute;cursor:pointer;border:none;background:transparent;transition:all .15s ease;z-index:10}
.hotspot:hover{filter:brightness(1.4);box-shadow:0 0 12px rgba(229,193,126,.4)}
.hotspot:active{transform:scale(.94);filter:brightness(.8)}
.hotspot.round{border-radius:50%;background:radial-gradient(circle at 40% 35%,rgba(255,255,255,.08),transparent 60%)}
.hotspot.round:hover{background:radial-gradient(circle at 40% 35%,rgba(229,193,126,.25),transparent 60%);box-shadow:0 0 8px rgba(229,193,126,.5)}
.hotspot.rect{border-radius:3px;background:rgba(255,255,255,.02)}
.hotspot.rect:hover{background:rgba(229,193,126,.1);box-shadow:0 0 10px rgba(229,193,126,.3)}
.hotspot.pgm-active{box-shadow:0 0 14px rgba(255,34,34,.6),inset 0 0 6px rgba(255,34,34,.3);background:radial-gradient(circle,rgba(255,34,34,.25),transparent 70%)}
.hotspot.pvw-active{box-shadow:0 0 12px rgba(34,221,102,.5),inset 0 0 5px rgba(34,221,102,.2);background:radial-gradient(circle,rgba(34,221,102,.2),transparent 70%)}
.hotspot.rec-active{box-shadow:0 0 16px rgba(255,34,34,.7);background:radial-gradient(circle,rgba(255,34,34,.35),transparent 60%);animation:pulse-red .8s infinite}
@keyframes pulse-red{0%,100%{opacity:1}50%{opacity:.6}}
.monitor-overlay{position:absolute;z-index:5;display:flex;flex-direction:column;align-items:center;justify-content:center;pointer-events:none;font-family:Consolas, 'Courier New', monospace;text-shadow:0 0 6px currentColor}
.mon-text{font-size:clamp(.5rem,1.2vw,.85rem);font-weight:700;opacity:.8}
.mon-cam{font-size:clamp(.6rem,1.6vw,1rem);font-weight:700;color:var(--cream)}
.mon-tc{font-size:clamp(.3rem,.7vw,.45rem);color:var(--crt-green);opacity:.5}
.mon-label{font-family:Georgia, 'Times New Roman', serif;font-size:clamp(.3rem,.7vw,.45rem);font-weight:700;letter-spacing:2px;padding:1px 6px;background:rgba(0,0,0,.6);margin-top:2px}
.mon-label.pgm{color:var(--red)}.mon-label.pvw{color:var(--green)}.mon-label.chk{color:var(--brass)}
.live-tag{position:absolute;z-index:20;background:var(--red);color:#fff;font-family:Georgia, 'Times New Roman', serif;font-size:clamp(.3rem,.7vw,.45rem);font-weight:700;letter-spacing:2px;padding:2px 8px;display:none;animation:blink 1s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
.hud-rec{position:fixed;top:10px;left:50%;transform:translateX(-50%);z-index:100;background:rgba(0,0,0,.85);border:2px solid var(--red);padding:4px 18px;display:none;align-items:center;gap:8px;font-size:clamp(.8rem,2vw,1.2rem);font-weight:700;color:var(--red);letter-spacing:3px;box-shadow:0 0 20px rgba(255,34,34,.3)}
.hud-rec.on{display:flex}
.hud-dot{width:10px;height:10px;border-radius:50%;background:var(--red);animation:blink .7s infinite}
.tooltip{position:absolute;z-index:50;background:rgba(0,0,0,.9);border:1px solid var(--brass);color:var(--cream);font-size:.6rem;letter-spacing:1px;padding:3px 10px;white-space:nowrap;pointer-events:none;display:none;font-family:Consolas, 'Courier New', monospace}
.hotspot:hover .tooltip{display:block}
.hk-bar{text-align:center;padding:8px;font-size:.55rem;color:var(--cream-dim);letter-spacing:1px}
.hk{color:var(--brass);font-weight:700}
.status-readout{position:absolute;z-index:15;font-size:clamp(.35rem,.65vw,.45rem);color:var(--crt-green);text-shadow:0 0 4px var(--crt-green);line-height:1.4;pointer-events:none}
#stations-bar{display:flex;gap:6px;justify-content:center;padding:6px 0;flex-wrap:wrap}
#stations-bar button{background:rgba(201,168,76,.06);border:1px solid var(--gold-d);color:var(--gold);font-family:Georgia, 'Times New Roman', serif;font-size:9px;letter-spacing:2px;padding:5px 14px;cursor:pointer;transition:all .2s}
#stations-bar button:hover{background:rgba(201,168,76,.15)}
#stations-bar button.active{background:rgba(201,168,76,.2);border-color:var(--gold);box-shadow:0 0 8px rgba(201,168,76,.3)}
.hidden{display:none!important}
.station-panel{background:rgba(10,8,4,.85);border:1px solid var(--gold-d);padding:12px 16px;margin:4px auto;max-width:1200px;font-size:11px;color:var(--cream)}
.station-panel h3{font-family:Georgia, 'Times New Roman', serif;font-size:11px;letter-spacing:3px;color:var(--gold);margin-bottom:8px}
.station-panel input,.station-panel textarea,.station-panel select{background:#0d0a06;border:1px solid var(--gold-d);color:var(--cream);font-family:Consolas, 'Courier New', monospace;font-size:11px;padding:4px 8px}
.station-panel button{background:rgba(201,168,76,.08);border:1px solid var(--gold-d);color:var(--gold);font-size:10px;letter-spacing:2px;padding:4px 12px;cursor:pointer}
.station-panel button:hover{background:rgba(201,168,76,.2)}
#rec-status-badge{display:inline-block;padding:2px 10px;font-size:10px;letter-spacing:2px;font-weight:700;border-radius:2px;color:#fff}
</style>
  <script src="/static/reach_auth.js"></script>
</head>
<body>
<nav style="position:fixed;top:10px;left:10px;z-index:200;display:flex;gap:6px;flex-wrap:wrap">
  <a href="/director-switcher" style="background:rgba(0,0,0,.75);border:1px solid var(--brass);color:var(--brass);font-family:Consolas,'Courier New',monospace;font-size:10px;letter-spacing:1px;padding:6px 10px;text-decoration:none">DIRECTOR SWITCHER</a>
  <a href="/stage" style="background:rgba(0,0,0,.75);border:1px solid var(--brass);color:var(--brass);font-family:Consolas,'Courier New',monospace;font-size:10px;letter-spacing:1px;padding:6px 10px;text-decoration:none">STAGE</a>
</nav>
<div class="hud-rec" id="hudRec"><div class="hud-dot"></div><span id="hudTime">00:00:00</span></div>
<div class="console-wrap" id="consoleWrap">
  <img class="console-img" src="controlroom.jpg" alt="PubCast Control Room" id="consoleImg" draggable="false">
  <!-- PROGRAM monitor (large framed, back right wall) -->
  <div class="monitor-overlay" style="left:60%;top:10%;width:22%;height:28%">
    <div class="mon-tc" id="pgmTc">00:00:00:00</div>
    <div class="mon-cam" id="pgmCamText">CAM 1</div>
    <div class="mon-text" id="pgmFeedText" style="color:var(--cream)">WIDE</div>
    <div class="mon-label pgm">PROGRAM</div>
  </div>
  <div class="live-tag" id="liveTag" style="left:70%;top:11%">â—† LIVE â—†</div>
  <!-- Small monitor bank -->
  <div class="monitor-overlay" style="left:60%;top:41%;width:7%;height:10%"><div class="mon-cam" style="font-size:clamp(.4rem,.8vw,.55rem)">1</div></div>
  <div class="monitor-overlay" style="left:67%;top:41%;width:7%;height:10%"><div class="mon-cam" style="font-size:clamp(.4rem,.8vw,.55rem)">2</div></div>
  <div class="monitor-overlay" style="left:74%;top:41%;width:7%;height:10%"><div class="mon-cam" style="font-size:clamp(.4rem,.8vw,.55rem)">3</div></div>
  <div class="monitor-overlay" style="left:60%;top:52%;width:7%;height:10%"><div class="mon-tc" id="pvwTc" style="font-size:clamp(.28rem,.55vw,.38rem);color:var(--crt-green);opacity:.5"></div><div class="mon-cam" id="pvwCamText" style="font-size:clamp(.4rem,.8vw,.55rem)">PVW</div><div class="mon-label pvw">PVW</div></div>
  <div class="monitor-overlay" style="left:67%;top:52%;width:7%;height:10%"><div class="mon-tc" id="chkTc" style="font-size:clamp(.28rem,.55vw,.38rem);color:var(--crt-green);opacity:.5"></div><div class="mon-cam" id="chkCamText" style="font-size:clamp(.4rem,.8vw,.55rem)">CHK</div><div class="mon-label chk">CHK</div></div>
  <!-- PGM row (center console) -->
  <button class="hotspot round" id="pgm1" style="left:38%;top:46%;width:3.5%;height:5%" onclick="setPGM('cam1')"><span class="tooltip" style="bottom:110%;left:50%;transform:translateX(-50%)">CAM 1 â€” WIDE</span></button>
  <button class="hotspot round" id="pgm2" style="left:42%;top:46%;width:3.5%;height:5%" onclick="setPGM('cam2')"><span class="tooltip" style="bottom:110%;left:50%;transform:translateX(-50%)">CAM 2 â€” TWO-SHOT</span></button>
  <button class="hotspot round" id="pgm3" style="left:46%;top:46%;width:3.5%;height:5%" onclick="setPGM('cam3')"><span class="tooltip" style="bottom:110%;left:50%;transform:translateX(-50%)">CAM 3 â€” CLOSE</span></button>
  <button class="hotspot round" id="pgm4" style="left:50%;top:46%;width:3.5%;height:5%" onclick="setPGM('cam4')"><span class="tooltip" style="bottom:110%;left:50%;transform:translateX(-50%)">CAM 4 â€” OVERHEAD</span></button>
  <button class="hotspot round" id="pgm5" style="left:54%;top:46%;width:3.5%;height:5%" onclick="setPGM('cam5')"><span class="tooltip" style="bottom:110%;left:50%;transform:translateX(-50%)">CAM 5 â€” STAGE</span></button>
  <!-- PVW row -->
  <button class="hotspot round" id="pvw1" style="left:38%;top:52%;width:3.5%;height:5%" onclick="setPVW('cam1')"><span class="tooltip" style="top:110%;left:50%;transform:translateX(-50%)">PVW 1</span></button>
  <button class="hotspot round" id="pvw2" style="left:42%;top:52%;width:3.5%;height:5%" onclick="setPVW('cam2')"><span class="tooltip" style="top:110%;left:50%;transform:translateX(-50%)">PVW 2</span></button>
  <button class="hotspot round" id="pvw3" style="left:46%;top:52%;width:3.5%;height:5%" onclick="setPVW('cam3')"><span class="tooltip" style="top:110%;left:50%;transform:translateX(-50%)">PVW 3</span></button>
  <button class="hotspot round" id="pvw4" style="left:50%;top:52%;width:3.5%;height:5%" onclick="setPVW('cam4')"><span class="tooltip" style="top:110%;left:50%;transform:translateX(-50%)">PVW 4</span></button>
  <button class="hotspot round" id="pvw5" style="left:54%;top:52%;width:3.5%;height:5%" onclick="setPVW('cam5')"><span class="tooltip" style="top:110%;left:50%;transform:translateX(-50%)">PVW 5</span></button>
  <!-- Transport -->
  <button class="hotspot rect" id="tCut" style="left:40%;top:58%;width:6%;height:5%" onclick="cut()"><span class="tooltip" style="bottom:110%;left:50%;transform:translateX(-50%)">CUT (SPACE)</span></button>
  <button class="hotspot rect" id="tRec" style="left:47%;top:58%;width:5%;height:5%" onclick="toggleRec()"><span class="tooltip" style="bottom:110%;left:50%;transform:translateX(-50%)">RECORD (R)</span></button>
  <button class="hotspot rect" id="tPanic" style="left:53%;top:58%;width:5%;height:5%" onclick="panic()"><span class="tooltip" style="bottom:110%;left:50%;transform:translateX(-50%)">PANIC (ESC)</span></button>
  <!-- Audio (left console) -->
  <button class="hotspot round" style="left:22%;top:50%;width:3%;height:4.5%" onclick="cycleAudio(0)"><span class="tooltip" style="right:110%;top:50%;transform:translateY(-50%)">HOST MIC</span></button>
  <button class="hotspot round" style="left:25.5%;top:50%;width:3%;height:4.5%" onclick="cycleAudio(1)"><span class="tooltip" style="right:110%;top:50%;transform:translateY(-50%)">GUEST 1</span></button>
  <button class="hotspot round" style="left:22%;top:55.5%;width:3%;height:4.5%" onclick="cycleAudio(2)"><span class="tooltip" style="right:110%;top:50%;transform:translateY(-50%)">GUEST 2</span></button>
  <button class="hotspot round" style="left:25.5%;top:55.5%;width:3%;height:4.5%" onclick="cycleAudio(3)"><span class="tooltip" style="right:110%;top:50%;transform:translateY(-50%)">MUSIC</span></button>
  <button class="hotspot round" style="left:23.5%;top:61%;width:3%;height:4.5%" onclick="muteAll()"><span class="tooltip" style="right:110%;top:50%;transform:translateY(-50%)">MUTE ALL (M)</span></button>
  <!-- Director modes (right of center desk) -->
  <button class="hotspot round" id="dAuto" style="left:58%;top:48%;width:3%;height:4.5%" onclick="setMode('auto')"><span class="tooltip" style="left:110%;top:50%;transform:translateY(-50%)">AUTO</span></button>
  <button class="hotspot round" id="dNews" style="left:58%;top:53%;width:3%;height:4.5%" onclick="setMode('news')"><span class="tooltip" style="left:110%;top:50%;transform:translateY(-50%)">NEWS</span></button>
  <button class="hotspot round" id="dDoc" style="left:58%;top:58%;width:3%;height:4.5%" onclick="setMode('documentary')"><span class="tooltip" style="left:110%;top:50%;transform:translateY(-50%)">DOCUMENTARY</span></button>
  <button class="hotspot round" id="dCine" style="left:58%;top:63%;width:3%;height:4.5%" onclick="setMode('cinematic')"><span class="tooltip" style="left:110%;top:50%;transform:translateY(-50%)">CINEMATIC</span></button>
  <button class="hotspot round" id="dMan" style="left:58%;top:68%;width:3%;height:4.5%" onclick="setMode('manual')"><span class="tooltip" style="left:110%;top:50%;transform:translateY(-50%)">MANUAL</span></button>
  <!-- Presets -->
  <button class="hotspot round" style="left:33%;top:50%;width:3%;height:4.5%" onclick="firePreset('showOpen')"><span class="tooltip" style="top:110%;left:50%;transform:translateX(-50%)">SHOW OPEN</span></button>
  <button class="hotspot round" style="left:33%;top:55%;width:3%;height:4.5%" onclick="firePreset('interview')"><span class="tooltip" style="top:110%;left:50%;transform:translateX(-50%)">INTERVIEW</span></button>
  <button class="hotspot round" style="left:33%;top:60%;width:3%;height:4.5%" onclick="firePreset('wide')"><span class="tooltip" style="top:110%;left:50%;transform:translateX(-50%)">WIDE SHOT</span></button>
  <button class="hotspot round" style="left:33%;top:65%;width:3%;height:4.5%" onclick="firePreset('showClose')"><span class="tooltip" style="top:110%;left:50%;transform:translateX(-50%)">SHOW CLOSE</span></button>
  <!-- Studio window -->
  <button class="hotspot rect" style="left:15%;top:10%;width:33%;height:35%;opacity:0" onclick="window.open('/static/stage.html','_blank')"><span class="tooltip" style="bottom:110%;left:50%;transform:translateX(-50%)">VIEW STUDIO</span></button>
  <!-- Status readout -->
  <div class="status-readout" id="statusReadout" style="left:43%;top:63%;width:10%">
    <div id="srMode">MODE: AUTO</div>
    <div id="srCam">PGM: CAM 1</div>
    <div id="srRec">REC: OFF</div>
  </div>
</div>
<div id="stations-bar">
  <button data-station="director">DIRECTOR</button>
  <button data-station="recorder">RECORDER</button>
  <button data-station="chyron">CHYRON</button>
  <button data-station="prompter">TELEPROMPTER</button>
  <button data-station="vtr">VTR</button>
</div>
<div id="station-director" class="station-panel hidden"><h3>DIRECTOR / SWITCHER</h3><p style="font-size:10px;color:var(--cream-dim)">Use the console above. Keys: 1â€“5 cameras, SPACE cut, R record, ESC panic, M mute, D cycle modes.</p></div>
<div id="station-recorder" class="station-panel hidden"><h3>RECORDING</h3><div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap"><span id="rec-status-badge" style="background:#555">IDLE</span><span id="rec-active-id" style="font-size:10px;color:var(--cream-dim)"></span><span id="rec-active-timer" style="font-family:'Courier Prime';font-size:13px;color:var(--crt-green)"></span></div><div id="rec-active-panel" style="display:none;margin-top:6px"><button onclick="wsSend({type:'recording_action',action:'pause'})">PAUSE</button> <button onclick="wsSend({type:'recording_action',action:'stop'})">STOP</button></div><div id="rec-storage" style="margin-top:8px;font-size:10px;color:var(--cream-dim)">Storage info loadingâ€¦</div><button id="rec-storage-refresh" style="margin-top:4px">REFRESH</button></div>
<div id="station-chyron" class="station-panel hidden"><h3>CHYRON / LOWER THIRD</h3><input id="chy-lower" placeholder="Lower third textâ€¦" style="width:100%;margin-bottom:6px"><button id="chy-apply">APPLY</button></div>
<div id="station-prompter" class="station-panel hidden"><h3>TELEPROMPTER</h3><textarea id="pro-script" rows="4" placeholder="Paste script hereâ€¦" style="width:100%;resize:vertical;margin-bottom:6px"></textarea><div style="display:flex;gap:8px;align-items:center"><button id="pro-start">START</button><button id="pro-stop">STOP</button><label style="font-size:10px">Speed <input id="pro-speed" type="number" min="1" max="20" value="5" style="width:50px"></label></div></div>
<div id="station-vtr" class="station-panel hidden"><h3>VTR PLAYBACK</h3><input id="vtr-asset" placeholder="Asset path or URLâ€¦" style="width:100%;margin-bottom:6px"><div style="display:flex;gap:8px"><button id="vtr-load">LOAD</button><button id="vtr-play">PLAY</button><button id="vtr-stop">STOP</button></div></div>
<div class="hk-bar"><span class="hk">1â€“5</span> CAMERAS Â· <span class="hk">SPACE</span> CUT Â· <span class="hk">R</span> REC Â· <span class="hk">ESC</span> PANIC Â· <span class="hk">M</span> MUTE ALL Â· <span class="hk">D</span> DIRECTOR</div>
<script src="/static/studio_console_hotspots.js"></script>
<script>
"use strict";
const CAMS=[{id:'cam1',n:'1',l:'WIDE',sourceId:'wide_shot'},{id:'cam2',n:'2',l:'TWO-SHOT',sourceId:'medium_shot'},{id:'cam3',n:'3',l:'CLOSE',sourceId:'close_up'},{id:'cam4',n:'4',l:'OVERHEAD',sourceId:'overhead'},{id:'cam5',n:'5',l:'STAGE',sourceId:'cam1_ndi'}];
const MODES=['auto','news','documentary','cinematic','manual'];
const MODE_BTN_MAP={auto:'dAuto',news:'dNews',documentary:'dDoc',cinematic:'dCine',manual:'dMan'};
const studioActions=window.PubCastStudioConsoleHotspots?new window.PubCastStudioConsoleHotspots.StudioConsoleHotspots():null;
let pgm='cam1',pvw='cam2',isRec=false,recStart=0,mode='auto',ws=null,activeRecordingSessionId='';
let audioMuted=[false,false,true,false,false];
function cam(id){return CAMS.find(c=>c.id===id)||CAMS[0]}
async function runStudioAction(actionId,payload={},spec=null){
  try{
    if(!studioActions)throw new Error('studio action adapter unavailable');
    const result=await studioActions.executeConfirmed(actionId,payload,{spec});
    return result&&result.canceled?null:result;
  }catch(err){
    const sr=document.getElementById('srMode');
    if(sr)sr.textContent='ERR: '+String(err.message||err).slice(0,22).toUpperCase();
    return null;
  }
}
function updateUI(){
  CAMS.forEach((c,i)=>{const el=document.getElementById('pgm'+(i+1));if(el)el.className='hotspot round'+(pgm===c.id?' pgm-active':'')});
  CAMS.forEach((c,i)=>{const el=document.getElementById('pvw'+(i+1));if(el)el.className='hotspot round'+(pvw===c.id?' pvw-active':'')});
  const pc=CAMS.find(c=>c.id===pgm),vc=CAMS.find(c=>c.id===pvw);
  document.getElementById('pgmCamText').textContent=pc?'CAM '+pc.n:'BLACK';
  document.getElementById('pgmFeedText').textContent=pc?pc.l:'BLACK';
  document.getElementById('pvwCamText').textContent=vc?'CAM '+vc.n:'â€”';
  MODES.forEach(m=>{const el=document.getElementById(MODE_BTN_MAP[m]);if(el)el.className='hotspot round'+(mode===m?' pvw-active':'')});
  document.getElementById('srMode').textContent='MODE: '+mode.toUpperCase();
  document.getElementById('srCam').textContent='PGM: '+(pc?'CAM '+pc.n:'BLACK');
  document.getElementById('srRec').textContent='REC: '+(isRec?'â— ON':'OFF');
  document.getElementById('tRec').className='hotspot rect'+(isRec?' rec-active':'');
}
function setPGM(id){pgm=id;updateUI();runStudioAction('camera.switch.program',{source_id:cam(id).sourceId});wsSend({type:'production_state',payload:{camera:id}})}
function setPVW(id){pvw=id;updateUI();runStudioAction('camera.switch.preview',{source_id:cam(id).sourceId})}
function cut(){const o=pgm;pgm=pvw;pvw=o;updateUI();runStudioAction('camera.cut',{});wsSend({type:'production_state',payload:{camera:pgm}})}
async function toggleRec(){
  if(!isRec){
    const started=await runStudioAction('recording.start',{session_id:`image_console_${Date.now()}`,sources:[cam(pgm).sourceId],profile_id:'broadcast_mp4',countdown_seconds:0},{safety:'confirm',label:'Start recording'});
    if(!started||!started.result||!started.result.session_id)return;
    activeRecordingSessionId=started.result.session_id;isRec=true;recStart=Date.now();
  }else{
    const stopped=activeRecordingSessionId?await runStudioAction('recording.stop',{session_id:activeRecordingSessionId},{safety:'confirm',label:'Stop recording'}):null;
    if(activeRecordingSessionId&&!stopped)return;
    activeRecordingSessionId='';isRec=false;document.getElementById('hudTime').textContent='00:00:00';
  }
  document.getElementById('hudRec').classList.toggle('on',isRec);document.getElementById('liveTag').style.display=isRec?'block':'none';updateUI()
}
function panic(){audioMuted=[true,true,true,true,true];pgm='black';updateUI();runStudioAction('audio.stop_all',{});wsSend({type:'production_state',payload:{camera:'black',on_air:false}})}
function muteAll(){audioMuted=[true,true,true,true,true];runStudioAction('audio.stop_all',{});updateUI()}
function cycleAudio(i){audioMuted[i]=!audioMuted[i];const buses=['dialogue','dialogue','dialogue','music','ui'];runStudioAction('audio.event',{action:audioMuted[i]?'mute':'unmute',bus:buses[i]||'sfx'});updateUI()}
function setMode(m){mode=m;updateUI();wsSend({type:'signal',payload:{action:'set_director_mode',mode:m}})}
function firePreset(p){({showOpen:()=>setPGM('cam1'),interview:()=>setPGM('cam2'),wide:()=>setPGM('cam1'),showClose:()=>setPGM('cam1')})[p]?.()}
document.addEventListener('keydown',e=>{
  if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA')return;
  switch(e.key){case'1':setPGM('cam1');break;case'2':setPGM('cam2');break;case'3':setPGM('cam3');break;case'4':setPGM('cam4');break;case'5':setPGM('cam5');break;case' ':e.preventDefault();cut();break;case'r':case'R':toggleRec();break;case'Escape':panic();break;case'm':case'M':muteAll();break;case'd':case'D':mode=MODES[(MODES.indexOf(mode)+1)%MODES.length];updateUI();break}
});
setInterval(()=>{const now=new Date();const tc=`${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')}:${String(Math.floor(Math.random()*30)).padStart(2,'0')}`;document.getElementById('pgmTc').textContent=tc;document.getElementById('pvwTc').textContent=tc.slice(0,8);document.getElementById('chkTc').textContent=tc.slice(0,8);if(isRec){const s=Math.floor((Date.now()-recStart)/1000);document.getElementById('hudTime').textContent=`${String(Math.floor(s/3600)).padStart(2,'0')}:${String(Math.floor(s%3600/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`}},250);
function connectWS(){try{ws=new WebSocket(window.ReachAuth.websocketURL('/ws/controlroom'));ws.onmessage=e=>{try{const m=JSON.parse(e.data);handleWsEvent(m);if(typeof window.__pubcastStationsHook==='function')window.__pubcastStationsHook(m)}catch{}};ws.onclose=()=>setTimeout(connectWS,3000)}catch{}}
function handleWsEvent(m){
  switch(m.type){
    case 'director_cut':
      if(m.data?.to_camera) setPGM(m.data.to_camera);
      break;
    case 'production_state':
      if(m.payload?.camera) setPGM(m.payload.camera);
      if(m.payload?.on_air !== undefined){ document.getElementById('liveTag').style.display=m.payload.on_air?'block':'none'; }
      if(m.payload?.mode) { mode=m.payload.mode; updateUI(); }
      break;
    case 'production_panic':
      pgm='black'; isRec=false;
      document.getElementById('hudRec').classList.remove('on');
      document.getElementById('liveTag').style.display='none';
      updateUI();
      break;
    case 'lighting_preset':{
      const badge=document.getElementById('srMode');
      if(badge) badge.textContent='LX: '+(m.payload?.preset||'').toUpperCase();
      break;
    }
    case 'avatar_camera_directive':{
      const shot=m.payload?.camera_shot||m.shot||'';
      const uid=m.payload?.user_id||'';
      const chk=document.getElementById('chkCamText');
      if(chk && shot) chk.textContent=shot.toUpperCase()+(uid?' Â· '+uid:'');
      break;
    }
    case 'avatar_action_cue':{
      const p=m.payload||{};
      const sr=document.getElementById('srMode');
      if(sr) sr.textContent=(p.avatar_id||'?')+': '+(p.action||'?');
      break;
    }
    case 'choreo_frame':
      // Silently consume â€” control room doesn't render skeleton frames
      break;
    case 'choreo_start':
    case 'choreo_complete':
    case 'choreo_stop':{
      const sr=document.getElementById('srMode');
      if(sr) sr.textContent='CHOREO: '+m.type.replace('choreo_','').toUpperCase();
      break;
    }
    case 'user_update':{
      // Could surface in future presence panel â€” absorb for now
      break;
    }
    case 'recording_started':
      isRec=true; recStart=Date.now();
      document.getElementById('hudRec').classList.add('on');
      document.getElementById('liveTag').style.display='block';
      updateUI();
      break;
    case 'recording_stopped':
    case 'recording_archived':
      isRec=false;
      document.getElementById('hudRec').classList.remove('on');
      document.getElementById('hudTime').textContent='00:00:00';
      document.getElementById('liveTag').style.display='none';
      updateUI();
      break;
  }
}
function wsSend(d){if(ws&&ws.readyState===1)ws.send(JSON.stringify(d))}
updateUI();connectWS();
</script>
<script src="control_stations.js"></script>
</body>
</html>

`````

## static/studio_control_room.html

SHA-256: 53781c0ec9bf6f0d13411f851b26bc1d150106236d61c9dee036ea18dbc84d57

`````text
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PubCast AI — Studio Control Room</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:        #0a0b0f;
    --surface:   #111318;
    --surface2:  #181c24;
    --border:    #252a36;
    --accent:    #e8ff47;
    --accent2:   #47c8ff;
    --accent3:   #ff6b6b;
    --text:      #e2e8f0;
    --muted:     #6b7280;
    --green:     #4ade80;
    --orange:    #fb923c;
    --mono:      'Space Mono', monospace;
    --sans:      'Syne', sans-serif;
  }

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* ── GRID NOISE OVERLAY ── */
  body::before {
    content: "";
    position: fixed; inset: 0;
    background-image:
      linear-gradient(rgba(232,255,71,0.02) 1px, transparent 1px),
      linear-gradient(90deg, rgba(232,255,71,0.02) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
  }

  /* ── SCANLINE ── */
  body::after {
    content: "";
    position: fixed; inset: 0;
    background: repeating-linear-gradient(
      0deg, transparent, transparent 2px,
      rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px
    );
    pointer-events: none;
    z-index: 0;
  }

  .app { position: relative; z-index: 1; display: flex; flex-direction: column; min-height: 100vh; }

  /* ── TOPBAR ── */
  .topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 24px;
    height: 56px;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    position: sticky; top: 0; z-index: 100;
  }

  .logo {
    font-family: var(--sans);
    font-weight: 800;
    font-size: 18px;
    letter-spacing: -0.5px;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .logo-badge {
    background: var(--accent);
    color: #000;
    font-size: 9px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 3px;
    letter-spacing: 1px;
    text-transform: uppercase;
  }

  .topbar-status {
    display: flex;
    align-items: center;
    gap: 20px;
    font-family: var(--mono);
    font-size: 11px;
    color: var(--muted);
  }

  .status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--accent3);
    display: inline-block;
    margin-right: 6px;
    animation: pulse 2s infinite;
  }
  .status-dot.online  { background: var(--green); }
  .status-dot.warning { background: var(--orange); animation: pulse 1s infinite; }
  .status-dot.live    { background: var(--accent3); animation: pulse 0.5s infinite; }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }

  /* ── STUDIO CONTROL ROOM SPECIFIC STYLES ── */
  
  .control-room-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto auto auto;
    gap: 16px;
    padding: 20px;
    height: 100%;
    overflow-y: auto;
  }

  .control-panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    position: relative;
  }

  .panel-header {
    font-family: var(--sans);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .panel-header-badge {
    background: rgba(232,255,71,0.1);
    color: var(--accent);
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 9px;
    letter-spacing: 1px;
  }

  .panel-header-badge.live {
    background: rgba(255,107,107,0.2);
    color: var(--accent3);
    animation: pulse 1s infinite;
  }

  /* ── AUDIO MATRIX ── */
  .audio-channel {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px;
    background: var(--surface2);
    border-radius: 6px;
    margin-bottom: 8px;
    border-left: 3px solid transparent;
    transition: all 0.2s;
  }

  .audio-channel.ok { border-left-color: var(--green); }
  .audio-channel.warning { border-left-color: var(--orange); }
  .audio-channel.critical { border-left-color: var(--accent3); }
  .audio-channel.muted { opacity: 0.5; border-left-color: var(--muted); }
  .audio-channel.ghost { border-left-color: #a855f7; }

  .channel-name {
    flex: 1;
    font-family: var(--mono);
    font-size: 11px;
    font-weight: 700;
    color: var(--text);
  }

  .channel-meter {
    width: 120px;
    height: 8px;
    background: #1a1d24;
    border-radius: 4px;
    overflow: hidden;
    position: relative;
  }

  .meter-fill {
    height: 100%;
    background: linear-gradient(to right, var(--green), var(--accent), var(--orange), var(--accent3));
    width: 0%;
    transition: width 0.1s linear;
  }

  .channel-db {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--muted);
    min-width: 50px;
    text-align: right;
  }

  .channel-toggle {
    width: 32px;
    height: 18px;
    background: var(--border);
    border-radius: 9px;
    position: relative;
    cursor: pointer;
    transition: background 0.2s;
  }

  .channel-toggle.active {
    background: var(--accent);
  }

  .channel-toggle::after {
    content: "";
    position: absolute;
    top: 2px;
    left: 2px;
    width: 14px;
    height: 14px;
    background: var(--surface);
    border-radius: 50%;
    transition: transform 0.2s;
  }

  .channel-toggle.active::after {
    transform: translateX(14px);
  }

  /* ── COUNTDOWN DISPLAY ── */
  .countdown-display {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 250px;
    background: radial-gradient(circle, rgba(232,255,71,0.05), transparent);
    border-radius: 8px;
    position: relative;
  }

  .countdown-number {
    font-family: var(--sans);
    font-size: 96px;
    font-weight: 800;
    color: var(--accent);
    line-height: 1;
    text-shadow: 0 0 40px rgba(232,255,71,0.5);
  }

  .countdown-label {
    font-family: var(--mono);
    font-size: 12px;
    color: var(--muted);
    margin-top: 16px;
    letter-spacing: 2px;
    text-transform: uppercase;
  }

  .countdown-status {
    position: absolute;
    top: 16px;
    right: 16px;
    padding: 4px 12px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 4px;
    font-family: var(--mono);
    font-size: 10px;
    color: var(--muted);
  }

  /* ── CONTROL BUTTONS ── */
  .control-buttons {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }

  .control-btn {
    padding: 16px;
    border: 2px solid var(--border);
    border-radius: 8px;
    background: var(--surface2);
    color: var(--text);
    font-family: var(--sans);
    font-size: 14px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }

  .control-btn:hover {
    border-color: var(--accent);
    background: rgba(232,255,71,0.05);
  }

  .control-btn.primary {
    grid-column: span 2;
    border-color: var(--accent);
    background: rgba(232,255,71,0.1);
    font-size: 18px;
  }

  .control-btn.primary:hover {
    background: rgba(232,255,71,0.2);
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(232,255,71,0.3);
  }

  .control-btn.danger {
    border-color: var(--accent3);
    background: rgba(255,107,107,0.1);
  }

  .control-btn.danger:hover {
    background: rgba(255,107,107,0.2);
  }

  .control-btn .icon {
    font-size: 24px;
  }

  .control-btn.primary .icon {
    font-size: 32px;
  }

  /* ── PREFLIGHT CHECKS ── */
  .preflight-checks {
    max-height: 300px;
    overflow-y: auto;
  }

  .preflight-check {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background: var(--surface2);
    border-radius: 6px;
    margin-bottom: 8px;
    border-left: 3px solid transparent;
  }

  .preflight-check.passed {
    border-left-color: var(--green);
  }

  .preflight-check.failed {
    border-left-color: var(--accent3);
  }

  .preflight-check.pending {
    border-left-color: var(--muted);
  }

  .check-icon {
    font-size: 20px;
  }

  .check-content {
    flex: 1;
  }

  .check-name {
    font-family: var(--sans);
    font-size: 12px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 4px;
  }

  .check-message {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--muted);
  }

  .check-timestamp {
    font-family: var(--mono);
    font-size: 9px;
    color: var(--muted);
  }

  /* ── SYSTEM STATUS ── */
  .system-metrics {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }

  .metric {
    padding: 12px;
    background: var(--surface2);
    border-radius: 6px;
    border-left: 3px solid var(--accent2);
  }

  .metric-label {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--muted);
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .metric-value {
    font-family: var(--sans);
    font-size: 20px;
    font-weight: 800;
    color: var(--text);
  }

  .metric-value .unit {
    font-size: 12px;
    color: var(--muted);
    font-weight: 400;
  }

  /* ── RECORDING STATUS ── */
  .recording-status {
    text-align: center;
    padding: 24px;
  }

  .recording-indicator {
    width: 24px;
    height: 24px;
    background: var(--accent3);
    border-radius: 50%;
    margin: 0 auto 12px;
    animation: pulse 0.8s infinite;
  }

  .recording-duration {
    font-family: var(--mono);
    font-size: 32px;
    font-weight: 700;
    color: var(--accent);
    letter-spacing: 2px;
  }

  .recording-label {
    font-family: var(--mono);
    font-size: 11px;
    color: var(--muted);
    margin-top: 8px;
    letter-spacing: 2px;
    text-transform: uppercase;
  }

  /* ── RESPONSIVE ── */
  @media (max-width: 1200px) {
    .control-room-grid {
      grid-template-columns: 1fr;
    }
  }

  .hidden { display: none !important; }
</style>
  <script src="/static/reach_auth.js"></script>
</head>
<body>

<div class="app">
  <!-- ── TOPBAR ── -->
  <div class="topbar">
    <div class="logo">
      PubCast AI
      <span class="logo-badge">STUDIO</span>
    </div>
    <div class="topbar-status">
      <span><span class="status-dot" id="studioStatusDot"></span><span id="studioStatusText">IDLE</span></span>
      <span><span class="status-dot online"></span>Pete</span>
      <span><span class="status-dot online"></span>Voxel Engine</span>
    </div>
  </div>

  <!-- ── STUDIO CONTROL ROOM ── -->
  <div class="control-room-grid">
    
    <!-- ── AUDIO MATRIX ── -->
    <div class="control-panel">
      <div class="panel-header">
        <span>Audio Matrix</span>
        <span class="panel-header-badge">5 CHANNELS</span>
      </div>
      <div id="audioMatrix"></div>
    </div>

    <!-- ── COUNTDOWN / STATUS ── -->
    <div class="control-panel">
      <div class="panel-header">
        <span>Production Control</span>
        <span class="panel-header-badge" id="stateIndicator">READY</span>
      </div>
      <div id="countdownContainer" class="countdown-display">
        <div class="countdown-number" id="countdownNumber">—</div>
        <div class="countdown-label" id="countdownLabel">STANDBY</div>
      </div>
    </div>

    <!-- ── CONTROL BUTTONS ── -->
    <div class="control-panel">
      <div class="panel-header">
        <span>Operations</span>
      </div>
      <div class="control-buttons">
        <button class="control-btn primary" id="btnStartPreflight">
          <span class="icon">🎬</span>
          <span>START COUNTDOWN</span>
        </button>
        <button class="control-btn" id="btnMuteAll">
          <span class="icon">🔇</span>
          <span>Isolation Mode</span>
        </button>
        <button class="control-btn" id="btnUnmuteAll">
          <span class="icon">🔊</span>
          <span>Unmute All</span>
        </button>
        <button class="control-btn" id="btnStopRecording" disabled>
          <span class="icon">⏹️</span>
          <span>Stop Recording</span>
        </button>
        <button class="control-btn danger" id="btnEmergencySave">
          <span class="icon">🚨</span>
          <span>EMERGENCY SAVE</span>
        </button>
      </div>
    </div>

    <!-- ── PREFLIGHT CHECKS ── -->
    <div class="control-panel">
      <div class="panel-header">
        <span>Preflight Checks</span>
        <span class="panel-header-badge" id="preflightBadge">0/0</span>
      </div>
      <div class="preflight-checks" id="preflightChecks">
        <div style="text-align:center;padding:40px;color:var(--muted);font-family:var(--mono);font-size:11px;">
          No checks run yet
        </div>
      </div>
    </div>

    <!-- ── SYSTEM METRICS ── -->
    <div class="control-panel">
      <div class="panel-header">
        <span>System Status</span>
      </div>
      <div class="system-metrics">
        <div class="metric">
          <div class="metric-label">Pete Health</div>
          <div class="metric-value">PERFECT</div>
        </div>
        <div class="metric">
          <div class="metric-label">Voxel FPS</div>
          <div class="metric-value">60 <span class="unit">fps</span></div>
        </div>
        <div class="metric">
          <div class="metric-label">Pipeline Latency</div>
          <div class="metric-value">12 <span class="unit">ms</span></div>
        </div>
        <div class="metric">
          <div class="metric-label">Ghost Mics</div>
          <div class="metric-value" id="metricGhostMics">0</div>
        </div>
      </div>
    </div>

    <!-- ── RECORDING STATUS ── -->
    <div class="control-panel hidden" id="recordingPanel">
      <div class="panel-header">
        <span>Live Recording</span>
        <span class="panel-header-badge live">ON AIR</span>
      </div>
      <div class="recording-status">
        <div class="recording-indicator"></div>
        <div class="recording-duration" id="recordingDuration">00:00:00</div>
        <div class="recording-label">Recording Duration</div>
      </div>
    </div>

  </div>
</div>

<script src="/static/studio_console_hotspots.js"></script>
<script>
/**
 * STUDIO CONTROL ROOM - FRONTEND CONTROLLER
 * The "Iron Core" JavaScript engine integrated with PubCast AI
 * 
 * Architecture:
 *   - Local-first logic (works offline)
 *   - WebSocket sync with Python backend
 *   - Keyboard shortcuts (Space = Start, Esc = Emergency)
 *   - Real-time audio monitoring
 */

// ─────────────────────────────────────────────
// STATE MANAGEMENT
// ─────────────────────────────────────────────

const StudioEngine = {
  state: 'IDLE', // IDLE, PREFLIGHT, LIVE, EMERGENCY
  ws: null,
  wsReconnectInterval: null,
  studioActions: null,
  activeRecordingSessionId: '',
  currentProgramSource: 'wide_shot',
  recordingStartTime: null,
  recordingInterval: null,
  
  audioMatrix: {
    mic_inputs:   { name: 'Microphone Inputs',       active: true, signal_db: null, status: 'NO_DATA' },
    dialogue:     { name: 'Dialogue Track',          active: true, signal_db: null, status: 'NO_DATA' },
    studio_feed:  { name: 'Studio Feed (SFX/Music)', active: true, signal_db: null, status: 'NO_DATA' },
    system_audio: { name: 'System Audio',            active: true, signal_db: null, status: 'NO_DATA' },
    room_noise:   { name: 'Room Noise',              active: true, signal_db: null, status: 'NO_DATA' }
  },
  audioBusByChannel: {
    mic_inputs: 'dialogue',
    dialogue: 'dialogue',
    studio_feed: 'music',
    system_audio: 'ui',
    room_noise: 'room'
  },
  
  preflightChecks: [],
  
  // Initialize
  init: function() {
    console.log("🎛️ Studio Control Room initializing...");
    this.studioActions = window.PubCastStudioConsoleHotspots
      ? new window.PubCastStudioConsoleHotspots.StudioConsoleHotspots()
      : null;
    this.connectWebSocket();
    this.setupEventListeners();
    this.renderAudioMatrix();
    this.updateUI();
    console.log("✅ Studio Control Room ready");
  },
  
  // ─────────────────────────────────────────────
  // WEBSOCKET CONNECTION
  // ─────────────────────────────────────────────
  
  connectWebSocket: function() {
    // Use the Reach origin (including its configured port and HTTPS scheme).
    // The shared adapter attaches the current, verified session token.
    const wsUrl = window.ReachAuth.websocketURL('/ws/studio');
    console.log(`📡 Connecting to Studio Control WebSocket: ${wsUrl}`);
    
    try {
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        console.log("✅ WebSocket connected");
        if (this.wsReconnectInterval) {
          clearInterval(this.wsReconnectInterval);
          this.wsReconnectInterval = null;
        }
      };
      
      this.ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        this.handleWebSocketMessage(message);
      };
      
      this.ws.onclose = () => {
        console.warn("⚠️ WebSocket disconnected - will retry");
        this.scheduleReconnect();
      };
      
      this.ws.onerror = (error) => {
        console.error("❌ WebSocket error:", error);
      };
    } catch (error) {
      console.error("❌ Failed to create WebSocket:", error);
      this.scheduleReconnect();
    }
  },
  
  scheduleReconnect: function() {
    if (!this.wsReconnectInterval) {
      this.wsReconnectInterval = setInterval(() => {
        console.log("🔄 Attempting WebSocket reconnect...");
        this.connectWebSocket();
      }, 5000);
    }
  },
  
  sendCommand: function(command, data = {}) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ command, ...data }));
    } else {
      console.warn("⚠️ WebSocket not connected - command queued:", command);
      // Fallback to local execution
      this.executeCommandLocally(command, data);
    }
  },

  runStudioAction: async function(actionId, payload = {}, options = {}) {
    try {
      if (!this.studioActions) throw new Error("studio action adapter unavailable");
      const result = await this.studioActions.executeConfirmed(actionId, payload, {
        spec: options.spec || null,
      });
      if (result && result.canceled) {
        this.addPreflightCheck({ check_id: actionId, name: actionId, passed: false, message: 'Canceled by operator' });
        return null;
      }
      return result;
    } catch (error) {
      this.addPreflightCheck({ check_id: actionId, name: actionId, passed: false, message: error.message });
      return null;
    }
  },

  confirmDanger: async function(title, message) {
    if (this.studioActions && this.studioActions.confirmImpl) {
      return this.studioActions.confirmImpl({
        actionId: title,
        title: title,
        label: title,
        message: message,
        details: [],
        confirmText: 'Confirm',
        cancelText: 'Cancel',
      });
    }
    return window.confirm(message);
  },
  
  handleWebSocketMessage: function(message) {
    console.log("📨 Received:", message.type);
    
    switch (message.type) {
      case 'state_update':
        this.setState(message.state);
        break;
      case 'audio_update':
        this.updateAudioMatrix(message.audio_matrix);
        break;
      case 'countdown':
        this.updateCountdown(message.seconds);
        break;
      case 'preflight_check':
        this.addPreflightCheck(message.check);
        break;
    }
  },
  
  // ─────────────────────────────────────────────
  // STATE MANAGEMENT
  // ─────────────────────────────────────────────
  
  setState: function(newState) {
    this.state = newState;
    console.log(`🎛️ State changed: ${newState}`);
    this.updateUI();
  },
  
  updateUI: function() {
    const statusDot = document.getElementById('studioStatusDot');
    const statusText = document.getElementById('studioStatusText');
    const stateIndicator = document.getElementById('stateIndicator');
    const btnStop = document.getElementById('btnStopRecording');
    const recordingPanel = document.getElementById('recordingPanel');
    
    // Update status indicators
    statusDot.className = 'status-dot';
    
    switch (this.state) {
      case 'IDLE':
        statusDot.classList.add('online');
        statusText.textContent = 'IDLE';
        stateIndicator.textContent = 'READY';
        stateIndicator.className = 'panel-header-badge';
        btnStop.disabled = true;
        recordingPanel.classList.add('hidden');
        this.stopRecordingTimer();
        break;
      
      case 'PREFLIGHT':
        statusDot.classList.add('warning');
        statusText.textContent = 'PREFLIGHT';
        stateIndicator.textContent = 'COUNTDOWN';
        stateIndicator.className = 'panel-header-badge';
        btnStop.disabled = true;
        recordingPanel.classList.add('hidden');
        break;
      
      case 'LIVE':
        statusDot.classList.add('live');
        statusText.textContent = 'LIVE';
        stateIndicator.textContent = 'ON AIR';
        stateIndicator.className = 'panel-header-badge live';
        btnStop.disabled = false;
        recordingPanel.classList.remove('hidden');
        this.startRecordingTimer();
        break;
      
      case 'EMERGENCY':
        statusDot.classList.add('live');
        statusText.textContent = 'EMERGENCY';
        stateIndicator.textContent = 'EMERGENCY';
        stateIndicator.className = 'panel-header-badge live';
        break;
    }
  },
  
  // ─────────────────────────────────────────────
  // AUDIO MATRIX
  // ─────────────────────────────────────────────
  
  renderAudioMatrix: function() {
    const container = document.getElementById('audioMatrix');
    container.innerHTML = '';
    
    for (const [id, channel] of Object.entries(this.audioMatrix)) {
      const statusClass = String(channel.status || 'no_data').toLowerCase().replace(/[^a-z0-9_-]/g, '-');
      const hasSignal = Number.isFinite(channel.signal_db);
      const meterWidth = hasSignal ? this.dbToPercent(channel.signal_db) : 0;
      
      const html = `
        <div class="audio-channel ${statusClass}" data-channel="${id}">
          <div class="channel-name">${channel.name}</div>
          <div class="channel-meter">
            <div class="meter-fill" style="width:${meterWidth}%"></div>
          </div>
          <div class="channel-db">${hasSignal ? `${channel.signal_db.toFixed(1)} dB` : 'NO METER DATA'}</div>
          <div class="channel-toggle ${channel.active ? 'active' : ''}" onclick="StudioEngine.toggleChannel('${id}')"></div>
        </div>
      `;
      
      container.insertAdjacentHTML('beforeend', html);
    }
  },
  
  updateAudioMatrix: function(audioData) {
    for (const [id, data] of Object.entries(audioData)) {
      if (this.audioMatrix[id]) {
        this.audioMatrix[id].active = data.active;
        this.audioMatrix[id].signal_db = Number.isFinite(data.signal_db) ? data.signal_db : null;
        this.audioMatrix[id].status = data.status || (Number.isFinite(data.signal_db) ? 'OK' : 'NO_DATA');
      }
    }
    this.renderAudioMatrix();
  },
  
  toggleChannel: async function(channelId) {
    const channel = this.audioMatrix[channelId];
    if (!channel) return;
    
    channel.active = !channel.active;
    await this.runStudioAction('audio.event', {
      action: channel.active ? 'unmute' : 'mute',
      bus: this.audioBusByChannel[channelId] || 'sfx',
    });
    this.renderAudioMatrix();
  },
  
  dbToPercent: function(db) {
    // Convert dB (-60 to 0) to percentage (0 to 100)
    return Math.max(0, Math.min(100, ((db + 60) / 60) * 100));
  },
  
  // ─────────────────────────────────────────────
  // AUDIO TELEMETRY
  // Meter levels are populated only by real `audio_update` WebSocket frames.
  // No synthetic dB animation is generated when telemetry is absent.
  // ─────────────────────────────────────────────
  
  // PREFLIGHT SEQUENCE
  // ─────────────────────────────────────────────
  
  startPreflight: async function() {
    console.log("🎬 Starting preflight countdown...");
    this.preflightChecks = [];
    this.setState('PREFLIGHT');

    const readiness = await this.runStudioAction('studio.readiness');
    const ready = Boolean(readiness && readiness.result && readiness.result.ready);
    this.addPreflightCheck({
      check_id: 'studio.readiness',
      name: 'Studio readiness',
      passed: ready,
      message: readiness ? `ready=${ready}` : 'Studio readiness endpoint unavailable',
    });

    const readinessResult = readiness && readiness.result ? readiness.result : {};
    this.currentProgramSource = readinessResult.program || this.currentProgramSource || 'wide_shot';

    const preflight = await this.runStudioAction('recording.preflight', {
      sources: [this.currentProgramSource],
      profile_id: 'broadcast_mp4',
    });
    const preflightReady = Boolean(preflight && preflight.result && preflight.result.ready);
    this.addPreflightCheck({
      check_id: 'recording.preflight',
      name: 'Recording preflight',
      passed: preflightReady,
      message: preflight ? `issues=${(preflight.result.issues || []).length}` : 'Recording preflight unavailable',
    });

    if (!readiness || !preflight) {
      this.executeLocalPreflight();
      return;
    }
    if (!ready || !preflightReady) {
      this.updateCountdown('!');
      document.getElementById('countdownLabel').textContent = 'CHECK FAILED';
      this.setState('IDLE');
      return;
    }

    for (let i = 5; i > 0; i--) {
      this.updateCountdown(i);
      await this.sleep(1000);
    }

    const sessionId = `studio_${Date.now()}`;
    const started = await this.runStudioAction('recording.start', {
      session_id: sessionId,
      sources: [this.currentProgramSource],
      profile_id: 'broadcast_mp4',
      countdown_seconds: 0,
    }, {
      spec: { safety: 'confirm', label: 'Start recording' },
    });

    if (started && started.result && started.result.session_id) {
      this.activeRecordingSessionId = started.result.session_id;
      this.setState('LIVE');
    } else {
      this.setState('IDLE');
    }
  },
  
  executeLocalPreflight: async function() {
    this.setState('PREFLIGHT');
    this.addPreflightCheck({ check_id: 'local_fallback', name: 'Local fallback', passed: false, message: 'Backend studio action path unavailable; running local visual countdown only' });
    
    for (let i = 5; i > 0; i--) {
      this.updateCountdown(i);
      await this.sleep(1000);
    }
    this.addPreflightCheck({
      check_id: 'backend_required',
      name: 'Production preflight',
      passed: false,
      message: 'Backend verification is unavailable; hardware/audio checks were not fabricated and LIVE was not entered.'
    });
    this.setState('IDLE');
  },
  
  updateCountdown: function(seconds) {
    const numberEl = document.getElementById('countdownNumber');
    const labelEl = document.getElementById('countdownLabel');
    
    numberEl.textContent = seconds;
    labelEl.textContent = `T-MINUS ${seconds}`;
  },
  
  addPreflightCheck: function(check) {
    this.preflightChecks.push(check);
    this.renderPreflightChecks();
  },
  
  renderPreflightChecks: function() {
    const container = document.getElementById('preflightChecks');
    const passedCount = this.preflightChecks.filter(c => c.passed).length;
    const totalCount = this.preflightChecks.length;
    
    document.getElementById('preflightBadge').textContent = `${passedCount}/${totalCount}`;
    
    if (this.preflightChecks.length === 0) {
      container.innerHTML = `<div style="text-align:center;padding:40px;color:var(--muted);font-family:var(--mono);font-size:11px;">No checks run yet</div>`;
      return;
    }
    
    container.innerHTML = this.preflightChecks.map(check => `
      <div class="preflight-check ${check.passed ? 'passed' : 'failed'}">
        <div class="check-icon">${check.passed ? '✅' : '⚠️'}</div>
        <div class="check-content">
          <div class="check-name">${check.name}</div>
          <div class="check-message">${check.message}</div>
        </div>
      </div>
    `).join('');
  },
  
  // ─────────────────────────────────────────────
  // RECORDING CONTROL
  // ─────────────────────────────────────────────
  
  startRecordingTimer: function() {
    if (this.recordingInterval) return;
    this.recordingStartTime = Date.now();
    this.recordingInterval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - this.recordingStartTime) / 1000);
      const hours = Math.floor(elapsed / 3600);
      const minutes = Math.floor((elapsed % 3600) / 60);
      const seconds = elapsed % 60;
      
      const display = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
      document.getElementById('recordingDuration').textContent = display;
    }, 1000);
  },
  
  stopRecordingTimer: function() {
    if (this.recordingInterval) {
      clearInterval(this.recordingInterval);
      this.recordingInterval = null;
    }
  },
  
  stopRecording: async function() {
    console.log("⏹️ Stopping recording...");
    if (this.activeRecordingSessionId) {
      const stopped = await this.runStudioAction('recording.stop', {
        session_id: this.activeRecordingSessionId,
      }, {
        spec: { safety: 'confirm', label: 'Stop recording' },
      });
      if (!stopped) return;
      this.activeRecordingSessionId = '';
    } else {
      this.sendCommand('stop_recording');
    }
    this.setState('IDLE');
  },
  
  // ─────────────────────────────────────────────
  // EMERGENCY SAVE
  // ─────────────────────────────────────────────
  
  emergencySave: function() {
    console.error("🚨 EMERGENCY SAVE TRIGGERED");
    this.sendCommand('emergency_save', { reason: 'Manual trigger' });
    this.setState('EMERGENCY');
    
    setTimeout(() => {
      this.setState('IDLE');
    }, 2000);
  },
  
  // ─────────────────────────────────────────────
  // AUDIO CONTROLS
  // ─────────────────────────────────────────────
  
  muteAllButDialogue: async function() {
    console.log("🔇 Isolation Mode: Dialogue only");
    await Promise.all([
      this.runStudioAction('audio.event', { action: 'unmute', bus: 'dialogue' }),
      this.runStudioAction('audio.event', { action: 'mute', bus: 'music' }),
      this.runStudioAction('audio.event', { action: 'mute', bus: 'sfx' }),
      this.runStudioAction('audio.event', { action: 'mute', bus: 'ui' }),
      this.runStudioAction('audio.event', { action: 'mute', bus: 'vtr' }),
      this.runStudioAction('audio.event', { action: 'mute', bus: 'room' }),
    ]);
    
    for (const [id, channel] of Object.entries(this.audioMatrix)) {
      channel.active = (id === 'dialogue');
    }
    this.renderAudioMatrix();
  },
  
  unmuteAll: async function() {
    console.log("🔊 Unmuting all channels");
    await Promise.all(['dialogue', 'music', 'sfx', 'ui', 'vtr', 'room'].map((bus) =>
      this.runStudioAction('audio.event', { action: 'unmute', bus: bus })
    ));
    
    for (const channel of Object.values(this.audioMatrix)) {
      channel.active = true;
    }
    this.renderAudioMatrix();
  },
  
  // ─────────────────────────────────────────────
  // EVENT LISTENERS
  // ─────────────────────────────────────────────
  
  setupEventListeners: function() {
    // Buttons
    document.getElementById('btnStartPreflight').onclick = () => this.startPreflight();
    document.getElementById('btnStopRecording').onclick = () => this.stopRecording();
    document.getElementById('btnMuteAll').onclick = () => this.muteAllButDialogue();
    document.getElementById('btnUnmuteAll').onclick = () => this.unmuteAll();
    document.getElementById('btnEmergencySave').onclick = async () => {
      if (await this.confirmDanger('Emergency Save', 'Trigger emergency save and flush the studio buffers?')) {
        this.emergencySave();
      }
    };
    
    // Keyboard shortcuts
    window.addEventListener('keydown', async (e) => {
      if (e.code === 'Space' && this.state === 'IDLE') {
        e.preventDefault();
        this.startPreflight();
      }
      if (e.code === 'Escape' && this.state === 'LIVE') {
        e.preventDefault();
        if (await this.confirmDanger('Emergency Stop', 'Emergency stop recording and enter emergency save state?')) {
          this.emergencySave();
        }
      }
    });
  },
  
  executeCommandLocally: function(command, data) {
    // Fallback for when WebSocket is offline
    console.log(`⚠️ Executing command locally: ${command}`);
    
    switch (command) {
      case 'start_preflight':
        this.executeLocalPreflight();
        break;
      case 'stop_recording':
        this.setState('IDLE');
        break;
      case 'mute_all_but_dialogue':
        this.muteAllButDialogue();
        break;
      case 'unmute_all':
        this.unmuteAll();
        break;
    }
  },
  
  sleep: function(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
};

// ─────────────────────────────────────────────
// INITIALIZE ON LOAD
// ─────────────────────────────────────────────

window.addEventListener('DOMContentLoaded', () => {
  StudioEngine.init();
});

// Keyboard shortcuts reminder
console.log(`
🎛️ STUDIO CONTROL ROOM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Keyboard Shortcuts:
  SPACE - Start countdown
  ESC   - Emergency save (during recording)

The "Iron Core" is ready.
Local-first logic: Works even offline.
`);
</script>

</body>
</html>

`````

## static/control_stations.js

SHA-256: 875547a5d025fba11fd8aeac05e8b6aade37efdfbca22941f6da40d36416293e

`````text
/**
 * PubCast AI — control_stations.js (Phase 1 hardened)
 * Hooks into app.js via window.__pubcastStationsHook and window.__pubcastRecHandler.
 * Add to control.html: <script type="module" src="/static/control_stations.js"></script>
 */

// ── Station tab switcher ──────────────────────────────────────────────────────
(function initStations() {
  const bar = document.getElementById('stations-bar');
  if (!bar) return;
  bar.addEventListener('click', e => {
    const btn = e.target.closest('[data-station]'); if (!btn) return;
    const target = btn.dataset.station;
    document.querySelectorAll('[id^="station-"]').forEach(el => el.classList.add('hidden'));
    bar.querySelectorAll('[data-station]').forEach(b => b.classList.remove('active'));
    const panel = document.getElementById(`station-${target}`);
    if (panel) panel.classList.remove('hidden');
    btn.classList.add('active');
    if (target === 'recorder') loadRecorderStation();
  });
  // Default to director on load
  const dir = bar.querySelector('[data-station="director"]');
  if (dir) dir.click();
})();

// ── Recording station ─────────────────────────────────────────────────────────
let _timerInterval = null, _recStartTs = null;

async function loadRecorderStation() {
  await refreshStorage();
}

async function refreshStorage() {
  const el = document.getElementById('rec-storage'); if (!el) return;
  try {
    const s = await fetch('/api/recording/storage').then(r => r.json());
    el.innerHTML = `Local free: <strong>${s.local_free_gb??'—'} GB</strong> &nbsp;·&nbsp;
      Recorded: <strong>${s.recorded_gb??0} GB</strong> &nbsp;·&nbsp;
      Cloud: <strong>${s.cloud_used_gb??'—'} GB</strong> &nbsp;·&nbsp;
      Backup: <strong>${s.backup_status??'—'}</strong>`;
  } catch(_) { el.innerText = 'Storage info unavailable.'; }
}
document.getElementById('rec-storage-refresh')?.addEventListener('click', refreshStorage);

function startRecTimer(startedAt) {
  _recStartTs = startedAt || (Date.now() / 1000);
  stopRecTimer(); // clear any existing
  setBadge('REC', '#c22');
  const panel = document.getElementById('rec-active-panel'); if (panel) panel.style.display = 'block';
  _timerInterval = setInterval(() => {
    const sec = Math.floor(Date.now()/1000 - _recStartTs);
    const t = document.getElementById('rec-active-timer');
    if (t) t.innerText = `${pad(Math.floor(sec/3600))}:${pad(Math.floor((sec%3600)/60))}:${pad(sec%60)}`;
  }, 1000);
}
function stopRecTimer() {
  if (_timerInterval) { clearInterval(_timerInterval); _timerInterval = null; }
  setBadge('IDLE', '#555');
  const panel = document.getElementById('rec-active-panel'); if (panel) panel.style.display = 'none';
}
function setBadge(text, color) {
  const b = document.getElementById('rec-status-badge'); if (!b) return;
  b.innerText = text; b.style.background = color;
}
function pad(n) { return String(n).padStart(2,'0'); }

// Register as the recording event handler for app.js to call
window.__pubcastRecHandler = function(ev) {
  if (ev.type === 'recording_started') {
    startRecTimer(ev.payload.started_at);
    const idEl = document.getElementById('rec-active-id');
    if (idEl) idEl.innerText = ev.payload.session_id;
  }
  if (ev.type === 'recording_stopped' || ev.type === 'recording_archived') stopRecTimer();
  if (ev.type === 'recording_paused')  setBadge('PAUSED', '#a80');
  if (ev.type === 'recording_resumed') setBadge('REC', '#c22');
};

// General WS hook (receives all events from app.js onWsEvent)
window.__pubcastStationsHook = function(ev) {
  // Forward recording events to the rec handler
  if (ev.type.startsWith('recording_') && typeof window.__pubcastRecHandler === 'function') {
    window.__pubcastRecHandler(ev);
  }
};

// ── Chyron ────────────────────────────────────────────────────────────────────
document.getElementById('chy-apply')?.addEventListener('click', async () => {
  const lower = document.getElementById('chy-lower')?.value || '';
  try {
    await fetch('/api/state/production', {method:'POST',
      headers:{'Content-Type':'application/json'}, body: JSON.stringify({lower_third: lower})});
  } catch(e) { console.warn('Chyron failed', e); }
});

// ── Teleprompter ──────────────────────────────────────────────────────────────
let _proTimer = null;
document.getElementById('pro-start')?.addEventListener('click', () => {
  const el = document.getElementById('pro-script'); if (!el||!el.value.trim()) return;
  const spd = parseFloat(document.getElementById('pro-speed')?.value||'5') * 0.4;
  if (_proTimer) clearInterval(_proTimer);
  _proTimer = setInterval(() => { el.scrollTop += spd; }, 50);
});
document.getElementById('pro-stop')?.addEventListener('click', () => {
  if (_proTimer) { clearInterval(_proTimer); _proTimer = null; }
});

// ── VTR ───────────────────────────────────────────────────────────────────────
async function prodPatch(patch) {
  await fetch('/api/state/production',{method:'POST',
    headers:{'Content-Type':'application/json'}, body:JSON.stringify(patch)});
}
document.getElementById('vtr-load')?.addEventListener('click', async () => {
  const a = document.getElementById('vtr-asset')?.value; if (!a) return;
  await prodPatch({mode:'REPLAY', replay_asset: a});
});
document.getElementById('vtr-play')?.addEventListener('click', () => prodPatch({on_air:true}));
document.getElementById('vtr-stop')?.addEventListener('click', () => prodPatch({on_air:false}));

// ── Audio mixer ───────────────────────────────────────────────────────────────
document.getElementById('mixer-apply')?.addEventListener('click', () => {
  const pgm  = document.getElementById('mixer-program')?.value;
  const host = document.getElementById('mixer-hosts')?.value;
  const mus  = document.getElementById('mixer-music')?.value;
  console.log(`Audio mix — PGM:${pgm} Hosts:${host} Music:${mus}`);
  // Phase 2: POST to /api/audio/mix
});

// ── Keyboard shortcuts (Space/C = Cut, F = Fade) ──────────────────────────────
document.addEventListener('keydown', e => {
  if (['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName)) return;
  if (e.code==='Space'||e.key==='c'||e.key==='C') { e.preventDefault(); document.getElementById('vm-cut')?.click(); }
  if (e.key==='f'||e.key==='F') { e.preventDefault(); document.getElementById('vm-take')?.click(); }
});

`````

## static/world_walk.html

SHA-256: dc07efb88a9b2725f38441a837259e0478e92115bd32b02f85c81f27471a9235

`````text
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bella Faux Pas Studio</title>
<link rel="icon" href="data:,">
<style>
:root {
  --bg: #12131a; --panel: #1b1d27; --line: #343748; --ink: #eceef6; --dim: #a3a8bd;
  --accent: #ffd36b; --good: #6be5a0; --fair: #ffd36b; --low: #ff8a7a; --pad: #35d6ff;
}
:root[data-theme="light"] { --bg: #f1f2f6; --panel: #ffffff; --line: #cfd2de; --ink: #1c1e2a; --dim: #565b72; --accent: #8a5a00; --good: #0c7a44; --fair: #8a5a00; --low: #b3261e; --pad: #006e99; }
@media (prefers-color-scheme: light) {
  :root:not([data-theme="dark"]) { --bg: #f1f2f6; --panel: #ffffff; --line: #cfd2de; --ink: #1c1e2a; --dim: #565b72; --accent: #8a5a00; --good: #0c7a44; --fair: #8a5a00; --low: #b3261e; --pad: #006e99; }
}
* { box-sizing: border-box; }
html, body { height: 100%; margin: 0; background: var(--bg); color: var(--ink); font: 14px/1.4 system-ui, -apple-system, "Segoe UI", sans-serif; }
#app { display: flex; height: 100%; min-height: 0; }
#stage { position: relative; flex: 1 1 auto; min-width: 0; background: #000; }
#c { position: absolute; inset: 0; width: 100%; height: 100%; display: block; touch-action: none; cursor: crosshair; }
#banner { position: absolute; left: 12px; top: 12px; right: 12px; display: flex; gap: 8px; align-items: center; pointer-events: none; flex-wrap: wrap; }
#banner > * { pointer-events: auto; }
.chip { background: rgba(10,10,16,.78); color: #fff; border: 1px solid rgba(255,255,255,.22); border-radius: 999px; padding: 4px 12px; font-size: 13px; backdrop-filter: blur(4px); }
.chip.warn { color: var(--accent); border-color: var(--accent); }
.chip.live { color: var(--dim); }
a.chip { text-decoration: none; pointer-events: auto; }
.chip.live.on { color: var(--good); border-color: var(--good); }
.chip.live.air { color: #fff; background: rgba(160,20,20,.82); border-color: #ff6b6b; }
button, select, input { font: inherit; color: inherit; }
button { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 6px 12px; cursor: pointer; min-height: 32px; }
button:hover:not(:disabled) { border-color: var(--accent); }
button:disabled { opacity: .5; cursor: not-allowed; }
button:focus-visible, select:focus-visible, input:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
#back { background: rgba(10,10,16,.78); color: #fff; border-color: rgba(255,255,255,.3); }
#bubble { position: absolute; z-index: 5; background: var(--panel); color: var(--ink); border: 1px solid var(--accent); border-radius: 14px; padding: 12px 14px; max-width: min(320px, 90%); box-shadow: 0 10px 32px rgba(0,0,0,.45); }
#bubble h3 { margin: 0 0 6px; font-size: 15px; }
#bubble p { margin: 0 0 8px; color: var(--dim); font-size: 13px; white-space: pre-line; }
#bubble .choices { display: flex; flex-direction: column; gap: 6px; }
#bubble .choices button { text-align: left; }
#bubble[hidden] { display: none; }
#toast { position: absolute; left: 50%; bottom: 14px; transform: translateX(-50%); background: rgba(10,10,16,.85); color: #fff; padding: 6px 14px; border-radius: 999px; font-size: 13px; opacity: 0; transition: opacity .25s; pointer-events: none; max-width: 90%; text-align: center; }
#toast.on { opacity: 1; }
#fade { position: absolute; inset: 0; background: #000; opacity: 0; transition: opacity .22s; pointer-events: none; }
#fade.on { opacity: 1; }
#panel { flex: 0 0 340px; max-width: 42vw; overflow: auto; background: var(--panel); border-left: 1px solid var(--line); padding: 14px 16px 24px; }
#panel h2 { font-size: 13px; text-transform: uppercase; letter-spacing: .06em; color: var(--dim); margin: 18px 0 8px; font-weight: 600; }
#panel h2:first-child { margin-top: 0; }
#panel label { display: flex; align-items: center; gap: 8px; margin: 3px 0; }
#panel select { width: 100%; background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 6px 8px; }
#panel input[type=range] { width: 100%; }
.row { display: grid; grid-template-columns: 1fr auto; gap: 4px 10px; align-items: center; }
.row output { font-variant-numeric: tabular-nums; color: var(--dim); }
.badge { display: inline-block; border-radius: 6px; padding: 1px 8px; font-weight: 700; border: 1px solid currentColor; text-transform: uppercase; font-size: 12px; letter-spacing: .04em; }
.badge.good { color: var(--good); } .badge.fair { color: var(--fair); } .badge.low { color: var(--low); }
.dim { color: var(--dim); }
.small { font-size: 12.5px; }
ul.tight { margin: 4px 0 0; padding-left: 18px; } ul.tight li { margin: 2px 0; }
#readout { font-variant-numeric: tabular-nums; font-size: 13px; }
details summary { cursor: pointer; color: var(--dim); }
textarea { width: 100%; height: 90px; background: var(--bg); color: var(--ink); border: 1px solid var(--line); border-radius: 8px; padding: 6px; font: 12px/1.3 ui-monospace, Consolas, monospace; }
.btnrow { display: flex; gap: 8px; margin-top: 8px; flex-wrap: wrap; }
.canrow { border: 1px solid var(--line); border-radius: 10px; padding: 6px 8px; margin: 6px 0; }
.canrow.sel { border-color: var(--accent); }
.canrow .btnrow { margin-top: 4px; }
@media (max-width: 820px) {
  #app { flex-direction: column; }
  #stage { flex: 1 1 55%; }
  #panel { flex: 1 1 45%; max-width: none; border-left: 0; border-top: 1px solid var(--line); }
}
</style>
  <script src="/static/reach_auth.js"></script>
</head>
<body>
<div id="app">
  <div id="stage">
    <canvas id="c" aria-label="Room picture. Click the floor to walk."></canvas>
    <div id="banner">
      <button id="back" hidden>&larr; Back</button>
      <span class="chip warn" id="chipStatus">PREVIEW &middot; proposed, nothing approved</span>
      <span class="chip" id="chipRoom"></span>
      <span class="chip live" id="chipLive" title="Connection to the PubCast host">&#9679; Offline</span>
      <a class="chip" id="classicLink" href="/world" title="Open this room in the classic PubWorld page">Classic view</a>
    </div>
    <div id="bubble" hidden role="dialog" aria-live="polite"></div>
    <div id="toast" role="status"></div>
    <div id="fade"></div>
  </div>
  <aside id="panel">
    <h2>Where</h2>
    <select id="viewSel" aria-label="Room and picture"></select>

    <h2>Walk as</h2>
    <label><input type="radio" name="char" value="pete" checked> <span>Pete 5'8"</span></label>
    <label><input type="radio" name="char" value="repeat"> <span>RePete 5'10"</span></label>
    <label><input type="radio" name="char" value="sir_purfluous"> <span>Purfluous 6'2"</span></label>

    <h2>3D avatar</h2>
    <div class="small dim">Load any rigged GLB for the character selected above. It is sized to the exact height this picture gives that character at that spot, and it turns, walks and idles as you click around. If a file has no animations it sways instead.</div>
    <div class="btnrow">
      <button id="glbMannequin">Try the test mannequin</button>
      <button id="glbPick">Load a GLB&hellip;</button>
      <button id="glbClear">Back to flat figure</button>
    </div>
    <input type="file" id="glbFile" accept=".glb,model/gltf-binary" hidden>
    <label><input type="checkbox" id="glbHolo"> Hologram look (glowing outline)</label>
    <label class="small" id="glbLibraryRow" hidden>Your saved avatars
      <select id="glbLibrary" aria-label="Your saved avatars"><option value="">(none for this character)</option></select></label>
    <div class="small dim" id="glbImportRow" hidden><a href="/static/avatar_import.html" target="_blank" rel="noopener">Import a new avatar&hellip;</a>
      It is sized to its canonical height and kept in your library. A file loaded with "Load a GLB" is only for now.</div>
    <div id="glbInfo" class="small dim"></div>
    <div id="progressInfo" class="small dim" role="status" aria-live="polite"></div>

    <h2>Show</h2>
    <label><input type="checkbox" id="shPads" checked> Floor pads (walkable areas)</label>
    <label><input type="checkbox" id="shOcc"> Things in front of / behind the avatar</label>
    <label><input type="checkbox" id="shDoors" checked> Doors and hotspots</label>
    <label><input type="checkbox" id="shHorizon"> Camera horizon line</label>
    <label><input type="checkbox" id="shRefs"> Reference figures (all three, on the floor)</label>
    <label id="altRow" hidden><input type="checkbox" id="shAlt"> Alternative size reading (grey)</label>

    <h2>How big the avatar is here</h2>
    <div id="sizeInfo" class="small"></div>

    <h2>Size tuner</h2>
    <div id="tuner" class="small"></div>
    <div class="btnrow">
      <button id="tuneReset">Reset this picture</button>
      <button id="tuneCopy">Copy my changes</button>
    </div>
    <details><summary>My changes as JSON</summary><textarea id="tuneOut" readonly aria-label="Tuned values as JSON"></textarea></details>

    <h2>Reference cans</h2>
    <div class="small dim">A 12 oz Coke can is 4.83 in tall and has not changed in 70 years. Add one, drop it on any surface (floor, table, lamp, bin), and drag its top handle until it looks like a real can there. Put one near the front, the middle and the back if you can. One can sizes the whole picture the same everywhere; three give it a slope. If the can is on a table or a lamp, press "Set floor point" and click where that thing meets the floor.</div>
    <div class="btnrow"><button id="canAdd">Add a Coke can</button></div>
    <div id="canList" class="small"></div>
    <label><input type="checkbox" id="canUse"> Size the avatars from my cans</label>

    <h2>Right now</h2>
    <div id="readout" class="small"></div>

    <h2>Still open for this picture</h2>
    <div id="open" class="small"></div>

    <h2>Look</h2>
    <label><input type="checkbox" id="themeLight"> Light panel</label>
  </aside>
</div>

<script type="importmap">{"imports":{"three":"/static/vendor/three-0.160.0/build/three.module.js","three/addons/":"/static/vendor/three-0.160.0/examples/jsm/"}}</script>
<script type="module" src="/static/world_walk_glb.js"></script>
<script src="/static/world_walk_live.js"></script>
<script>
"use strict";
/* ===========================================================================
   PubCast world walk (preview). Reads /static/world/world.json, which is
   generated from modules/pubcast_world.py + data/world/placements.json.
   Nothing here is approved: every picture is "proposed" until Josie says so.
   The geometry and size maths mirror modules/pubcast_world_placement.py and are
   checked against it by the tests.
   =========================================================================== */

const WALK_IN_PER_S = 54;          // preview walking speed, real inches per second at the avatar's own depth
const ARRIVE_PX = 3;
const CHAR = {
  pete:          { label: "Pete",      color: "#3fe0b4", sex: "f" },
  repeat:        { label: "RePete",    color: "#5aa9ff", sex: "m" },
  sir_purfluous: { label: "Purfluous", color: "#b77cff", sex: "m" },
};
const CHAR_ORDER = ["sir_purfluous", "repeat", "pete"];

/* ------------------------------ geometry ---------------------------------- */
function pointOnSegment(p, a, b) {
  const cross = (p[1] - a[1]) * (b[0] - a[0]) - (p[0] - a[0]) * (b[1] - a[1]);
  const len = Math.abs(b[0] - a[0]) + Math.abs(b[1] - a[1]);
  if (Math.abs(cross) > 1e-9 * Math.max(1, len)) return false;
  return Math.min(a[0], b[0]) - 1e-9 <= p[0] && p[0] <= Math.max(a[0], b[0]) + 1e-9 &&
         Math.min(a[1], b[1]) - 1e-9 <= p[1] && p[1] <= Math.max(a[1], b[1]) + 1e-9;
}
function pointInPolygon(p, poly) {
  const [x, y] = p; let inside = false; const n = poly.length;
  for (let i = 0; i < n; i++) {
    const a = poly[i], b = poly[(i + 1) % n];
    if (pointOnSegment(p, a, b)) return true;
    if ((a[1] > y) !== (b[1] > y) && x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]) inside = !inside;
  }
  return inside;
}
function closestOnSegment(p, a, b) {
  const dx = b[0] - a[0], dy = b[1] - a[1], seg = dx * dx + dy * dy;
  if (seg === 0) return [a[0], a[1]];
  const t = Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / seg));
  return [a[0] + t * dx, a[1] + t * dy];
}
const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
function floorPolys(view) { return view.zones.map(z => z.points); }
function floorContains(view, p) { return view.zones.some(z => pointInPolygon(p, z.points)); }
function snapToFloor(view, p) {
  if (!view.zones.length) return null;
  if (floorContains(view, p)) return [p[0], p[1]];
  let best = null, bd = Infinity;
  for (const z of view.zones) {
    const poly = z.points;
    for (let i = 0; i < poly.length; i++) {
      const c = closestOnSegment(p, poly[i], poly[(i + 1) % poly.length]);
      const d = dist(c, p);
      if (d < bd) { bd = d; best = c; }
    }
  }
  return best;
}
function distanceToFloor(view, p) {
  const s = snapToFloor(view, p);
  return s ? dist(s, p) : Infinity;
}
function axisFraction(axis, p) {
  const dx = axis[1][0] - axis[0][0], dy = axis[1][1] - axis[0][1], seg = dx * dx + dy * dy;
  if (seg === 0) return 0;
  return Math.max(0, Math.min(1, ((p[0] - axis[0][0]) * dx + (p[1] - axis[0][1]) * dy) / seg));
}
/* altitude in inches above the picture's base level, or null while not known */
function altitudeAt(zone, p) {
  const z = zone.z_in;
  if (zone.kind === "floor" || z === null || z === undefined) return (z === undefined ? null : z);
  if (zone.rise_in === null || zone.rise_in === undefined) return null;
  return z + zone.rise_in * axisFraction(zone.axis, p);
}
function zoneAt(view, p) {
  const inside = view.zones.filter(z => pointInPolygon(p, z.points));
  if (!inside.length) return null;
  inside.sort((a, b) => (a.kind !== "floor" ? 0 : 1) - (b.kind !== "floor" ? 0 : 1));
  return inside[0];
}
/* The lowest row of a footprint polygon at column x (x held inside the polygon's width). */
function footprintFrontY(fp, x) {
  let lo = Infinity, hi = -Infinity;
  for (const p of fp) { lo = Math.min(lo, p[0]); hi = Math.max(hi, p[0]); }
  x = Math.min(Math.max(x, lo), hi);
  let best = null;
  for (let i = 0; i < fp.length; i++) {
    const [x1, y1] = fp[i], [x2, y2] = fp[(i + 1) % fp.length];
    if (x1 === x2) { if (x === x1) best = best === null ? Math.max(y1, y2) : Math.max(best, y1, y2); continue; }
    if (Math.min(x1, x2) <= x && x <= Math.max(x1, x2)) {
      const y = y1 + (x - x1) / (x2 - x1) * (y2 - y1);
      best = best === null ? y : Math.max(best, y);
    }
  }
  return best;
}
/* Where an object meets the floor: its real front edge when it has a footprint, else the single base row. */
function objectBaseY(o, x) {
  if (o.footprint && x !== undefined) { const y = footprintFrontY(o.footprint, x); if (y !== null) return y; }
  return o.base_y;
}
function occluderInFront(o, feetY, x) { return o.always === true || feetY < objectBaseY(o, x); }
function blockedAt(view, p) {
  return view.occluders.some(o => o.footprint && pointInPolygon(p, o.footprint))
    || (view.blockers || []).some(b => pointInPolygon(p, b.footprint));
}

/* ------------------------------ avatar size ------------------------------- */
function fitSamples(samples) {
  if (!samples.length) return null;
  const ys = samples.map(s => s.y);
  if (samples.length === 1 || Math.max(...ys) === Math.min(...ys)) {
    return [samples.reduce((a, s) => a + s.ppi, 0) / samples.length, 0];
  }
  const n = samples.length, my = ys.reduce((a, b) => a + b, 0) / n, mp = samples.reduce((a, s) => a + s.ppi, 0) / n;
  const v = ys.reduce((a, y) => a + (y - my) ** 2, 0);
  const slope = samples.reduce((a, s) => a + (s.y - my) * (s.ppi - mp), 0) / v;
  return [mp - slope * my, slope];
}
function ppiAtSamples(samples, y) {
  const f = fitSamples(samples);
  return f ? f[0] + f[1] * y : null;
}
/* Pixels per inch at row y for a floor at altitude z (null = not known: treated as the main floor).
   `sizing` is {camera, scale}: the picture's own, or the tuned values. */
function ppiFor(sizing, y, z, zone) {
  let ppi;
  if (zone && zone.scale && zone.scale.length) ppi = ppiAtSamples(zone.scale, y);
  else if (sizing.camera) {
    const drop = (z === null || z === undefined) ? 0 : z;
    const den = sizing.camera.eye_in - drop;
    if (den === 0) return null;
    ppi = (y - sizing.camera.horizon_y) / den;     // negative over negative for a floor above the camera
  } else ppi = ppiAtSamples(sizing.scale || [], y);
  return (ppi === null || !(ppi > 0)) ? null : ppi;
}

/* ------------------------------ state ------------------------------------- */
const $ = id => document.getElementById(id);
const canvas = $("c"), ctx = canvas.getContext("2d");
const S = {
  world: null, rooms: {}, room: null, view: null, key: "",
  imgs: {}, pos: [0, 0], target: null, pendingDoor: null, armed: true,
  char: "pete", history: [], tune: {}, lastT: 0, bubbleFor: null,
  show: { pads: true, occ: false, doors: true, horizon: false, refs: false, alt: false },
  hover: null, fit: { s: 1, ox: 0, oy: 0, cw: 1, ch: 1 }, refs: [], lastReadout: "",
  cans: {}, canArm: null, canSel: -1, canDrag: null,
  vel: [0, 1], moving: false, path: [],
  avatarIds: {},            // character -> avatar id in the library, so the choice is kept with your progress
  library: [],
};
const CAN_IN = 4.83, CAN_W_IN = 2.6;     // a 12 oz can: height and diameter in inches
const CANS_KEY = "pubcast_world_walk_cans_v1";
function loadCans() { try { return JSON.parse(localStorage.getItem(CANS_KEY) || "{}") || {}; } catch (e) { return {}; } }
function saveCans() { try { localStorage.setItem(CANS_KEY, JSON.stringify(S.cans)); } catch (e) { /* private window: cans just last this session */ } }
const TUNE_KEY = "pubcast_world_walk_tune_v1";
function loadTune() { try { return JSON.parse(localStorage.getItem(TUNE_KEY) || "{}") || {}; } catch (e) { return {}; } }
function saveTune() { try { localStorage.setItem(TUNE_KEY, JSON.stringify(S.tune)); } catch (e) { /* private window: tuning just lasts this session */ } }
const keyOf = (roomId, viewId) => roomId + "/" + viewId;

/* The size rule in force for a picture: the proposed one, or the user's own: sliders, cans, and an overall x multiplier.
   `noMult` gives the rule before the multiplier (what the camera / sample sliders edit). */
function sizingOf(view, key, noMult) {
  const t = S.tune[key || S.key] || {};
  let camera = view.camera, scale = view.scale;
  if (t.fromCans && t.canScale && t.canScale.length) { camera = null; scale = t.canScale; }
  else if (t.camera && view.camera) { camera = t.camera; scale = []; }
  else if (t.scale && !view.camera) scale = t.scale;
  const m = noMult ? 1 : (t.mult || 1);
  if (m !== 1) {
    if (camera) camera = { horizon_y: camera.horizon_y, eye_in: camera.eye_in / m };   // ppi = (row - horizon) / eye, so x m means eye / m
    else scale = (scale || []).map(q => ({ y: q.y, ppi: q.ppi * m }));
  }
  return { camera, scale };
}
function heightIn(charId) { return S.world.character_height_in[charId]; }
function avatarPx(charId, y, zone, p) {
  const alt = zone ? altitudeAt(zone, p) : null;
  const ppi = ppiFor(sizingOf(S.view), y, alt, zone);
  return ppi === null ? null : heightIn(charId) * ppi;
}

/* ------------------------------ loading ----------------------------------- */
async function loadWorld() {
  const r = await fetch("/static/world/world.json", { cache: "no-cache" });
  if (!r.ok) throw new Error("world.json: HTTP " + r.status);
  const w = await r.json();
  S.world = w;
  for (const room of w.rooms) S.rooms[room.id] = room;
  return w;
}
function loadImage(src) {
  if (S.imgs[src]) return S.imgs[src];
  S.imgs[src] = new Promise((res, rej) => {
    const im = new Image();
    im.onload = () => res(im); im.onerror = () => rej(new Error("image failed: " + src));
    im.src = src;
  });
  return S.imgs[src];
}
function fillViewSelect() {
  const sel = $("viewSel"); sel.textContent = "";
  for (const room of S.world.rooms) {
    if (!room.views.length) continue;
    const g = document.createElement("optgroup"); g.label = room.name + (room.locked ? " (locked)" : "");
    for (const v of room.views) {
      const o = document.createElement("option");
      o.value = keyOf(room.id, v.id); o.textContent = v.label || v.id;
      g.appendChild(o);
    }
    sel.appendChild(g);
  }
}

/* ------------------------------ view switching ---------------------------- */
function toast(msg, ms) {
  const t = $("toast"); t.textContent = msg; t.classList.add("on");
  clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.remove("on"), ms || 2600);
}
function doorReach(view, door) {
  // you cannot get closer to a door than the nearest floor, so standing there counts as being at the door
  return Math.max(door.r * 1.5, distanceToFloor(view, door.at) + 30);
}
function centroid(poly) {
  let x = 0, y = 0; for (const p of poly) { x += p[0]; y += p[1]; }
  return [x / poly.length, y / poly.length];
}
/* A sensible place to stand: open main-level floor in the lower part of the picture, nearest the middle. */
function defaultStart(view) {
  if (!view.zones.length) return null;
  const ys = view.zones.flatMap(z => z.points.map(p => p[1]));
  const y0 = Math.min(...ys), y1 = Math.max(...ys);
  const mainLevel = (p) => { const z = zoneAt(view, p); return z && z.kind === "floor" && z.z_in === 0; };
  const anyLevel = (p) => !!zoneAt(view, p);
  for (const ok of [mainLevel, anyLevel]) {
    for (let d = 0; d <= (y1 - y0); d += 6) {
      for (const row of d === 0 ? [y0 + 0.78 * (y1 - y0)] : [y0 + 0.78 * (y1 - y0) - d, y0 + 0.78 * (y1 - y0) + d]) {
        const xs = [];
        for (let x = 0; x <= view.w; x += 6) if (floorContains(view, [x, row]) && ok([x, row])) xs.push(x);
        if (xs.length) {
          xs.sort((a, b) => Math.abs(a - view.w / 2) - Math.abs(b - view.w / 2));
          return [xs[0], row];
        }
      }
    }
  }
  return snapToFloor(view, centroid(view.zones[0].points));
}
function startPosition(view, fromRoomId) {
  if (!view.zones.length) return null;
  const home = defaultStart(view);
  if (fromRoomId) {
    const d = view.doors.find(d => d.to === fromRoomId);
    if (d) {
      let p = snapToFloor(view, d.at);
      const dd = dist(p, home);
      if (dd > 1) {
        const k = Math.min(1, 28 / dd), q = [p[0] + (home[0] - p[0]) * k, p[1] + (home[1] - p[1]) * k];
        if (floorContains(view, q)) p = q;
      }
      return p;
    }
  }
  return home;
}
async function setView(roomId, viewId, opts) {
  opts = opts || {};
  const room = S.rooms[roomId]; if (!room) return false;
  const view = room.views.find(v => v.id === viewId) || room.views[0];
  if (!view) return false;
  const fade = $("fade"); if (!opts.instant) fade.classList.add("on");
  let img;
  try { img = await loadImage(view.image); }
  catch (e) { fade.classList.remove("on"); toast("Could not load that picture"); return false; }
  S.room = room; S.view = view; S.key = keyOf(room.id, view.id); S.img = img;
  S.target = null; S.path = []; HELD.clear(); S.pendingDoor = null; hideBubble(); S.canArm = null; S.canSel = -1; S.canDrag = null;
  S.pos = startPosition(view, opts.from) || [0, 0];
  if (view.zones.length) S.pos = nearestWalkable(view, S.pos);          // never start inside a table or chair
  S.armed = false;                                  // re-arms once you walk away from the door you arrived at
  S.refs = buildRefs(view);
  $("viewSel").value = S.key;
  $("chipRoom").textContent = room.name + " · " + (view.label || view.id);
  $("back").hidden = S.history.length === 0;
  refreshPanel(); resize();
  requestAnimationFrame(() => fade.classList.remove("on"));
  const L = window.PubCastLive;
  if (L) L.enterView({ room: room.id, view: view.id, liveId: room.live_id || "", layoutId: room.layout_id || "" });
  return true;
}
function goTo(roomId, fromRoomId) {
  const room = S.rooms[roomId];
  if (!room) { toast("That place is not built yet"); return; }
  if (room.locked) { toast(room.name + " is locked. It has not been built yet.", 3600); return; }
  if (!room.views.length) { toast(room.name + " has no picture yet", 3600); return; }
  S.history = [];
  setView(roomId, room.views[0].id, { from: fromRoomId });
}
function openCloseup(viewId) {
  S.history.push({ room: S.room.id, view: S.view.id, pos: S.pos.slice() });
  setView(S.room.id, viewId, {});
}
async function goBack() {
  const h = S.history.pop(); if (!h) return;
  await setView(h.room, h.view, { instant: false });
  S.pos = h.pos; $("back").hidden = S.history.length === 0;
}

/* ------------------------------ reference figures ------------------------- */
function floorRunsAtRow(view, y) {
  // contiguous stretches of floor on one row, so reference figures never stand in the gap between two pads
  const runs = []; let a = null, last = null;
  for (let x = 0; x <= view.w; x += 6) {
    if (floorContains(view, [x, y])) { if (a === null) a = x; last = x; }
    else if (a !== null) { runs.push([a, last]); a = null; }
  }
  if (a !== null) runs.push([a, last]);
  return runs;
}
function buildRefs(view) {
  if (!view.zones.length) return [];
  const ys = view.zones.flatMap(z => z.points.map(p => p[1]));
  const y0 = Math.min(...ys), y1 = Math.max(...ys);
  const out = [];
  [0.14, 0.5, 0.86].forEach((f, i) => {
    let y = y0 + (y1 - y0) * f, runs = floorRunsAtRow(view, y);
    for (let k = 0; !runs.length && k < 30; k++) { y += 6; runs = floorRunsAtRow(view, y); }
    if (!runs.length) return;
    const run = runs[Math.min(runs.length - 1, Math.floor(i * runs.length / 3))];
    out.push({ char: CHAR_ORDER[i], p: [run[0] + (run[1] - run[0]) * [0.2, 0.75, 0.9][i], y] });
  });
  return out;
}

/* ------------------------------ figures ----------------------------------- */
function figureShapes(cx, fy, H, sex) {
  const f = k => k * H;
  const male = sex === "m";
  const sw = f(male ? 0.255 : 0.225), ww = f(male ? 0.19 : 0.165), hw = f(male ? 0.2 : 0.225);
  const yTop = fy - H, yNeck = fy - f(0.835), ySh = fy - f(0.815), yWa = fy - f(0.62), yHip = fy - f(0.52), yCr = fy - f(0.47);
  const shapes = [];
  shapes.push({ type: "ellipse", x: cx, y: yTop + f(0.0667), rx: f(0.051), ry: f(0.0667) });
  shapes.push({ type: "poly", pts: [[cx - f(0.022), yTop + f(0.12)], [cx + f(0.022), yTop + f(0.12)], [cx + f(0.026), ySh], [cx - f(0.026), ySh]] });
  shapes.push({ type: "poly", pts: [[cx - sw / 2, ySh], [cx - f(0.03), yNeck + f(0.012)], [cx + f(0.03), yNeck + f(0.012)], [cx + sw / 2, ySh],
    [cx + ww / 2, yWa], [cx + hw / 2, yHip], [cx + hw / 2 - f(0.005), yCr + f(0.03)], [cx - hw / 2 + f(0.005), yCr + f(0.03)], [cx - hw / 2, yHip], [cx - ww / 2, yWa]] });
  for (const s of [-1, 1]) {
    shapes.push({ type: "poly", pts: [[cx + s * (sw / 2 - f(0.012)), ySh], [cx + s * (sw / 2 + f(0.034)), ySh + f(0.012)],
      [cx + s * (sw / 2 + f(0.05)), fy - f(0.4)], [cx + s * (sw / 2 + f(0.0)), fy - f(0.4)]] });
    shapes.push({ type: "poly", pts: [[cx + s * f(0.003), yCr], [cx + s * (hw / 2 - f(0.002)), yHip + f(0.02)],
      [cx + s * (f(0.062)), fy - f(0.03)], [cx + s * f(0.025), fy - f(0.03)]] });
    shapes.push({ type: "ellipse", x: cx + s * f(0.05), y: fy - f(0.015), rx: f(0.038), ry: f(0.017) });
  }
  return shapes;
}
function tracePath(c, s) {
  c.beginPath();
  if (s.type === "ellipse") c.ellipse(s.x, s.y, s.rx, s.ry, 0, 0, Math.PI * 2);
  else { c.moveTo(s.pts[0][0], s.pts[0][1]); for (let i = 1; i < s.pts.length; i++) c.lineTo(s.pts[i][0], s.pts[i][1]); c.closePath(); }
}
function drawFigure(c, cx, fy, H, color, sex, opts) {
  opts = opts || {};
  if (!(H > 1)) return;
  const sh = figureShapes(cx, fy, H, sex);
  c.save();
  c.globalAlpha = opts.alpha === undefined ? 1 : opts.alpha;
  // contact shadow
  c.fillStyle = "rgba(0,0,0,.38)";
  c.beginPath(); c.ellipse(cx, fy + H * 0.004, H * 0.12, Math.max(1.2, H * 0.022), 0, 0, Math.PI * 2); c.fill();
  // one clean outline: stroke every part first, then fill every part on top
  c.lineJoin = "round"; c.lineCap = "round";
  c.strokeStyle = "rgba(12,14,24,.95)"; c.lineWidth = Math.max(2, H * 0.03);
  for (const s of sh) { tracePath(c, s); c.stroke(); }
  const g = c.createLinearGradient(cx, fy - H, cx, fy);
  g.addColorStop(0, opts.light || color); g.addColorStop(1, color);
  c.fillStyle = g;
  for (const s of sh) { tracePath(c, s); c.fill(); }
  c.restore();
}

/* ------------------------------ drawing ----------------------------------- */
function resize() {
  const r = $("stage").getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.round(r.width * dpr)); canvas.height = Math.max(1, Math.round(r.height * dpr));
  S.fit.cw = r.width; S.fit.ch = r.height; S.fit.dpr = dpr;
  if (S.view) {
    const s = Math.min(r.width / S.view.w, r.height / S.view.h);
    S.fit.s = s; S.fit.ox = (r.width - S.view.w * s) / 2; S.fit.oy = (r.height - S.view.h * s) / 2;
  }
  moveBubble();
}
const toScreen = p => [S.fit.ox + p[0] * S.fit.s, S.fit.oy + p[1] * S.fit.s];
function toPicture(clientX, clientY) {
  const r = canvas.getBoundingClientRect();
  return [(clientX - r.left - S.fit.ox) / S.fit.s, (clientY - r.top - S.fit.oy) / S.fit.s];
}
function polyPath(c, pts) { c.beginPath(); pts.forEach((p, i) => i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1])); c.closePath(); }
const KIND_COLOR = { floor: [53, 214, 255], stairs: [255, 170, 60], ramp: [255, 220, 90] };

function figureList() {
  const v = S.view, list = [];
  if (v.zones.length) {
    const zone = zoneAt(v, S.pos);
    const H = avatarPx(S.char, S.pos[1], zone, S.pos);
    list.push({ char: S.char, p: S.pos, H, main: true });
  }
  if (S.show.refs) for (const r of S.refs) {
    const zone = zoneAt(v, r.p);
    list.push({ char: r.char, p: r.p, H: avatarPx(r.char, r.p[1], zone, r.p), main: false });
  }
  return list.filter(f => f.H).sort((a, b) => a.p[1] - b.p[1]);
}
/* A loaded GLB for this character, drawn at the pixel height the picture's size rule gives. False = use the flat figure. */
function drawGlbFigure(c, fg) {
  const G = window.PubCastGLB; if (!G || !G.has(fg.char)) return false;
  const motion = fg.main ? { vx: S.vel[0], vy: S.vel[1], moving: S.moving, dt: S.dt || 0, pxScale: S.fit.s }
                         : { vx: 0, vy: 1, moving: false, dt: S.dt || 0, pxScale: S.fit.s };
  try { return G.draw(c, fg.char, fg.p[0], fg.p[1], fg.H, motion); }
  catch (e) { G.state.lastError = String(e && e.message || e); G.clear(fg.char); setGlbInfo(); return false; }
}
function draw() {
  const c = ctx, f = S.fit, dpr = f.dpr || 1;
  c.setTransform(dpr, 0, 0, dpr, 0, 0);
  c.fillStyle = "#000"; c.fillRect(0, 0, f.cw, f.ch);
  if (!S.view || !S.img) return;
  const v = S.view;
  c.save(); c.translate(f.ox, f.oy); c.scale(f.s, f.s);
  c.drawImage(S.img, 0, 0, v.w, v.h);

  if (S.show.pads) for (const z of v.zones) {
    const col = KIND_COLOR[z.kind] || KIND_COLOR.floor, unknown = z.z_in === null || (z.kind !== "floor" && z.rise_in === null);
    polyPath(c, z.points);
    c.fillStyle = `rgba(${col[0]},${col[1]},${col[2]},.2)`; c.fill();
    c.lineWidth = 2 / f.s; c.strokeStyle = `rgba(${col[0]},${col[1]},${col[2]},.95)`;
    c.setLineDash(unknown ? [8 / f.s, 5 / f.s] : []); c.stroke(); c.setLineDash([]);
    if (z.axis) {
      c.strokeStyle = "rgba(255,255,255,.9)"; c.lineWidth = 2 / f.s;
      c.beginPath(); c.moveTo(z.axis[0][0], z.axis[0][1]); c.lineTo(z.axis[1][0], z.axis[1][1]); c.stroke();
      const a = z.axis[1], b = z.axis[0], ang = Math.atan2(a[1] - b[1], a[0] - b[0]), hs = 12 / f.s;
      c.beginPath(); c.moveTo(a[0], a[1]); c.lineTo(a[0] - hs * Math.cos(ang - .45), a[1] - hs * Math.sin(ang - .45));
      c.lineTo(a[0] - hs * Math.cos(ang + .45), a[1] - hs * Math.sin(ang + .45)); c.closePath(); c.fillStyle = "rgba(255,255,255,.9)"; c.fill();
    }
  }
  if (S.show.occ) for (const o of v.occluders) {
    const front = occluderInFront(o, S.pos[1], S.pos[0]);
    polyPath(c, o.points);
    c.fillStyle = front ? "rgba(255,60,200,.22)" : "rgba(80,255,120,.12)"; c.fill();
    c.lineWidth = 1.5 / f.s; c.strokeStyle = front ? "rgba(255,60,200,.95)" : "rgba(80,255,120,.8)"; c.stroke();
  }
  if (S.show.occ) {                                   // solid things nobody can walk on: the floor under them, in red
    const solids = v.occluders.filter(o => o.footprint).map(o => o.footprint).concat((v.blockers || []).map(b => b.footprint));
    for (const fp of solids) {
      polyPath(c, fp);
      c.fillStyle = "rgba(255,40,40,.30)"; c.fill();
      c.lineWidth = 2 / f.s; c.strokeStyle = "rgba(255,70,70,.95)"; c.stroke();
    }
  }
  if (S.show.horizon && v.camera) {
    const sz = sizingOf(v);
    c.setLineDash([14 / f.s, 8 / f.s]); c.lineWidth = 2 / f.s; c.strokeStyle = "rgba(255,235,0,.95)";
    c.beginPath(); c.moveTo(0, sz.camera.horizon_y); c.lineTo(v.w, sz.camera.horizon_y); c.stroke(); c.setLineDash([]);
  }
  // figures, far to near; after each one repaint the things that are in front of it
  for (const fg of figureList()) {
    const ch = CHAR[fg.char];
    if (fg.main && S.show.refs) {                     // mark which one is you when the reference figures are on
      c.save(); c.strokeStyle = "rgba(255,255,255,.95)"; c.lineWidth = 2 / f.s;
      c.beginPath(); c.ellipse(fg.p[0], fg.p[1], fg.H * 0.19, Math.max(3, fg.H * 0.04), 0, 0, Math.PI * 2); c.stroke(); c.restore();
    }
    if (!drawGlbFigure(c, fg)) drawFigure(c, fg.p[0], fg.p[1], fg.H, ch.color, ch.sex, { alpha: fg.main ? 1 : 0.85 });
    for (const o of v.occluders) if (occluderInFront(o, fg.p[1], fg.p[0])) {
      c.save(); polyPath(c, o.points); c.clip(); c.drawImage(S.img, 0, 0, v.w, v.h); c.restore();
    }
  }
  if (S.show.alt && v.scale_info && v.scale_info.alt && S.refs.length) {
    const alt = v.scale_info.alt.samples;
    for (const r of S.refs) {
      const ppi = ppiAtSamples(alt, r.p[1]); if (!(ppi > 0)) continue;
      const off = 46 * Math.max(.6, ppiAtSamples(v.scale, r.p[1]) || 1);
      drawFigure(c, r.p[0] + (r.p[0] + off > v.w - 40 ? -off : off), r.p[1], heightIn(r.char) * ppi, "#9aa0ad", CHAR[r.char].sex, { alpha: .9 });
    }
  }
  drawCans(c);
  if (S.show.doors) drawMarkers(c);
  if (S.target && S.view.zones.length) {
    c.strokeStyle = "rgba(255,255,255,.9)"; c.lineWidth = 2 / f.s;
    c.beginPath(); c.arc(S.target[0], S.target[1], 8 / f.s, 0, Math.PI * 2); c.stroke();
  }
  c.restore();
  if (S.show.doors || S.show.pads) drawLabels(c);
}
/* ------------------------------ reference cans ---------------------------- */
function canListNow() { return (S.cans[S.key] = S.cans[S.key] || []); }
function canSample(c) { return { y: c.fy == null ? c.y : c.fy, ppi: c.h / CAN_IN }; }
function applyCans() {
  const t = S.tune[S.key] = S.tune[S.key] || {}, list = canListNow();
  t.canScale = list.map(canSample);
  if (!list.length) t.fromCans = false;
  saveTune(); saveCans(); updateTuneOut();
}
function drawCan(c, can, sel) {
  const h = can.h, w = h * CAN_W_IN / CAN_IN, x = can.x, y = can.y, ry = Math.max(1.2, w * 0.12), f = S.fit.s;
  c.save();
  c.fillStyle = "rgba(0,0,0,.28)"; c.beginPath(); c.ellipse(x, y, w * 0.55, ry * 1.1, 0, 0, Math.PI * 2); c.fill();
  c.beginPath(); c.moveTo(x - w / 2, y - h + ry); c.lineTo(x - w / 2, y);
  c.ellipse(x, y, w / 2, ry, 0, Math.PI, 0, true); c.lineTo(x + w / 2, y - h + ry);
  c.ellipse(x, y - h + ry, w / 2, ry, 0, 0, Math.PI, true); c.closePath();
  const g = c.createLinearGradient(x - w / 2, 0, x + w / 2, 0);
  g.addColorStop(0, "#8f1010"); g.addColorStop(.3, "#e02020"); g.addColorStop(.55, "#ff5a4d"); g.addColorStop(1, "#7a0c0c");
  c.fillStyle = g; c.fill();
  c.lineWidth = 1 / f; c.strokeStyle = "rgba(0,0,0,.6)"; c.stroke();
  c.save(); c.clip();
  c.strokeStyle = "rgba(255,255,255,.9)"; c.lineWidth = Math.max(1, h * 0.08);
  c.beginPath(); c.moveTo(x - w / 2, y - h * 0.32); c.bezierCurveTo(x - w * 0.2, y - h * 0.5, x + w * 0.2, y - h * 0.2, x + w / 2, y - h * 0.42); c.stroke();
  c.restore();
  c.fillStyle = "#cfd3da"; c.beginPath(); c.ellipse(x, y - h + ry, w / 2, ry, 0, 0, Math.PI * 2); c.fill(); c.stroke();
  if (sel) {
    c.strokeStyle = "#ffd36b"; c.lineWidth = 2 / f; c.setLineDash([5 / f, 4 / f]);
    c.strokeRect(x - w / 2 - 4 / f, y - h - ry - 4 / f, w + 8 / f, h + ry * 2 + 8 / f); c.setLineDash([]);
  }
  c.fillStyle = "#ffd36b"; c.strokeStyle = "#000"; c.lineWidth = 1.5 / f;
  c.beginPath(); c.arc(x, y - h - ry - 10 / f, 6 / f, 0, Math.PI * 2); c.fill(); c.stroke();      // resize handle
  if (can.fy != null && Math.abs(can.fy - can.y) > 1) {
    c.strokeStyle = "#ffd36b"; c.lineWidth = 1.5 / f; c.setLineDash([4 / f, 4 / f]);
    c.beginPath(); c.moveTo(x, y); c.lineTo(x, can.fy); c.stroke(); c.setLineDash([]);
    c.beginPath(); c.moveTo(x - 7 / f, can.fy); c.lineTo(x + 7 / f, can.fy); c.stroke();
  }
  c.restore();
}
function drawCans(c) { canListNow().forEach((can, i) => drawCan(c, can, i === S.canSel)); }
function canHit(p) {
  const list = canListNow(), s = S.fit.s;
  for (let i = list.length - 1; i >= 0; i--) {
    const k = list[i], w = k.h * CAN_W_IN / CAN_IN, ry = Math.max(1.2, w * 0.12);
    if (dist(p, [k.x, k.y - k.h - ry - 10 / s]) <= 14 / s) return { i, mode: "resize" };
    if (Math.abs(p[0] - k.x) <= Math.max(w / 2, 10 / s) && p[1] <= k.y + 8 / s && p[1] >= k.y - k.h - ry - 8 / s) return { i, mode: "move" };
  }
  return null;
}
function buildCans() {
  const box = $("canList"); box.textContent = ""; const list = canListNow(), t = S.tune[S.key] || {};
  $("canUse").checked = !!t.fromCans; $("canUse").disabled = !list.length;
  list.forEach((can, i) => {
    const row = el("div", undefined, "canrow" + (i === S.canSel ? " sel" : ""));
    row.appendChild(slider("Can " + (i + 1) + " height on the picture (px)", 4, 120, 0.5, can.h, val => { can.h = val; applyCans(); refreshCanText(row, can); }));
    const info = el("div", "", "dim"); info.dataset.info = "1"; row.appendChild(info);
    const br = el("div", undefined, "btnrow");
    const sel = el("button", i === S.canSel ? "Selected" : "Select"); sel.addEventListener("click", () => { S.canSel = i; buildCans(); });
    const fl = el("button", "Set floor point"); fl.title = "For a can on a table, lamp or bin: click where that thing meets the floor";
    fl.addEventListener("click", () => { S.canArm = { floor: i }; toast("Click the picture where this can's table (or lamp, bin) meets the floor"); });
    const cl = el("button", can.fy == null ? "" : "On the floor"); if (can.fy == null) { cl.hidden = true; } else cl.addEventListener("click", () => { can.fy = null; applyCans(); buildCans(); });
    const rm = el("button", "Remove"); rm.addEventListener("click", () => { list.splice(i, 1); S.canSel = -1; applyCans(); buildCans(); buildTuner(); });
    br.appendChild(sel); br.appendChild(fl); br.appendChild(cl); br.appendChild(rm); row.appendChild(br);
    box.appendChild(row); refreshCanText(row, can);
  });
}
function refreshCanText(row, can) {
  const s = canSample(can), n = row.querySelector("[data-info]");
  if (n) n.textContent = "= " + s.ppi.toFixed(2) + " px per inch at row " + Math.round(s.y) + (can.fy == null ? " (sits on the floor)" : " (floor point set below it)");
}
$("canAdd").addEventListener("click", () => { S.canArm = "place"; toast("Click the picture where the can stands"); });
$("canUse").addEventListener("change", e => {
  const t = S.tune[S.key] = S.tune[S.key] || {}; t.fromCans = e.target.checked; applyCans(); buildTuner(); buildCans();
  toast(e.target.checked ? "Avatars are now sized from your cans" : "Back to the picture's own size rule");
});
function groupDoors(view) {
  const groups = [];
  for (const d of view.doors) {
    let g = d.group ? groups.find(x => x.group === d.group && x.at[0] === d.at[0] && x.at[1] === d.at[1]) : null;
    if (!g) { g = { group: d.group || null, at: d.at, r: d.r, doors: [] }; groups.push(g); }
    g.doors.push(d);
  }
  return groups;
}
function doorName(d) {
  const ex = S.room.exits.find(e => e.to === d.to);
  const r = S.rooms[d.to];
  return d.label || (ex && ex.label) || (r && r.name) || d.to;
}
function drawMarkers(c) {
  const f = S.fit, v = S.view;
  for (const g of groupDoors(v)) {
    c.beginPath(); c.arc(g.at[0], g.at[1], Math.max(10, 10 / f.s), 0, Math.PI * 2);
    const confirmed = g.doors.every(d => d.status === "confirmed");
    c.fillStyle = confirmed ? "rgba(255,211,107,.9)" : "rgba(255,138,122,.85)"; c.fill();
    c.lineWidth = 2 / f.s; c.strokeStyle = "#12131a"; c.stroke();
  }
  for (const h of v.hotspots) {
    c.beginPath(); c.rect(h.at[0] - 8 / f.s, h.at[1] - 8 / f.s, 16 / f.s, 16 / f.s);
    c.fillStyle = "rgba(120,200,255,.9)"; c.fill(); c.lineWidth = 2 / f.s; c.strokeStyle = "#12131a"; c.stroke();
  }
}
function pillText(c, text, x, y, fg, bg) {
  c.font = "600 12px system-ui, sans-serif";
  const w = c.measureText(text).width + 12;
  c.fillStyle = bg; c.beginPath(); c.roundRect ? c.roundRect(x - w / 2, y - 10, w, 20, 10) : c.rect(x - w / 2, y - 10, w, 20); c.fill();
  c.fillStyle = fg; c.textAlign = "center"; c.textBaseline = "middle"; c.fillText(text, x, y);
}
function drawLabels(c) {
  const v = S.view;
  if (S.show.doors) {
    for (const g of groupDoors(v)) {
      const [sx, sy] = toScreen(g.at);
      const text = g.doors.length > 1 ? g.doors.map(doorName).join(" / ") : doorName(g.doors[0]);
      pillText(c, text, Math.min(Math.max(sx, 60), S.fit.cw - 60), Math.max(sy - 22, 16), "#fff", "rgba(18,19,26,.85)");
    }
    for (const h of v.hotspots) {
      const [sx, sy] = toScreen(h.at);
      pillText(c, h.label, Math.min(Math.max(sx, 50), S.fit.cw - 50), Math.min(sy + 22, S.fit.ch - 12), "#06202e", "rgba(150,215,255,.92)");
    }
  }
  if (S.show.refs) for (const fg of figureList()) {
    const [sx, sy] = toScreen(fg.p), inch = heightIn(fg.char);
    const text = (fg.main ? "You: " : "") + CHAR[fg.char].label + " " + Math.floor(inch / 12) + "'" + (inch % 12) + "\" \u00b7 " + Math.round(fg.H) + " px";
    pillText(c, text, Math.min(Math.max(sx, 80), S.fit.cw - 80), Math.min(sy + 22 * 1, S.fit.ch - 12), "#fff", "rgba(18,19,26,.85)");
  }
  if (S.show.pads) for (const z of v.zones) {
    const cc = centroid(z.points), [sx, sy] = toScreen(cc);
    const alt = z.z_in === null ? "altitude ?" : (z.kind === "floor" ? z.z_in + " in" : (z.rise_in === null ? "climb ?" : (z.rise_in > 0 ? "up " : "down ") + Math.abs(z.rise_in) + " in"));
    pillText(c, z.id + " · " + z.level + " · " + alt, sx, sy, "#00222c", "rgba(150,235,255,.88)");
  }
}

/* ------------------------------ movement ---------------------------------- */
/* Walk speed at a spot: the same real inches per second everywhere, so it looks slower far away and quicker up close. */
function walkSpeedPx(p, dirx, diry) {
  const v = S.view, zone = zoneAt(v, p);
  const ppi = ppiFor(sizingOf(v), p[1], zone ? altitudeAt(zone, p) : null, zone) || 1;
  const dl = Math.hypot(dirx, diry) || 1;
  return WALK_IN_PER_S * ppi * (0.62 + 0.38 * Math.abs(dirx) / dl);          // depth moves look slower than sideways ones
}
const walkable = (v, q) => floorContains(v, q) && !blockedAt(v, q);
/* One step of `len` picture pixels towards direction (dx, dy). If something is in the way it creeps round it: tries
   the straight line, then turns 35, 70 and 110 degrees either way (the side nearer the goal first). Awkward on purpose. */
function creepStep(v, p, dx, dy, len) {
  const d = Math.hypot(dx, dy) || 1, ux = dx / d, uy = dy / d;
  for (const deg of [0, 35, -35, 70, -70, 110, -110]) {
    const a = deg * Math.PI / 180, c = Math.cos(a), sn = Math.sin(a);
    const vx = ux * c - uy * sn, vy = ux * sn + uy * c, q = [p[0] + vx * len, p[1] + vy * len];
    if (walkable(v, q)) return { pos: q, dir: [vx, vy] };
  }
  return null;
}
/* A* over a coarse grid of walkable spots, then straightened. Returns waypoints from `a` (excluded) to `b`, or null. */
function findPath(v, a, b) {
  const CELL = 6, xs = [], ys = [];
  for (const z of v.zones) for (const q of z.points) { xs.push(q[0]); ys.push(q[1]); }
  if (!xs.length) return null;
  const x0 = Math.min(...xs) - CELL, y0 = Math.min(...ys) - CELL, W = Math.ceil((Math.max(...xs) - x0) / CELL) + 2, H = Math.ceil((Math.max(...ys) - y0) / CELL) + 2;
  const at = (cx, cy) => [x0 + cx * CELL, y0 + cy * CELL];
  const freeC = new Int8Array(W * H).fill(-1);
  const free = (cx, cy) => { if (cx < 0 || cy < 0 || cx >= W || cy >= H) return false; const i = cy * W + cx; if (freeC[i] < 0) freeC[i] = walkable(v, at(cx, cy)) ? 1 : 0; return freeC[i] === 1; };
  const cellOf = q => [Math.round((q[0] - x0) / CELL), Math.round((q[1] - y0) / CELL)];
  const nearestFree = q => { const [cx, cy] = cellOf(q); for (let r = 0; r < 14; r++) for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) if (Math.max(Math.abs(dx), Math.abs(dy)) === r && free(cx + dx, cy + dy)) return [cx + dx, cy + dy]; return null; };
  const sC = nearestFree(a), gC = nearestFree(b); if (!sC || !gC) return null;
  const idx = (cx, cy) => cy * W + cx, g = new Float32Array(W * H).fill(Infinity), from = new Int32Array(W * H).fill(-1), closed = new Uint8Array(W * H);
  const heap = []; const push = (f, i) => { heap.push([f, i]); let k = heap.length - 1; while (k > 0) { const pk = (k - 1) >> 1; if (heap[pk][0] <= heap[k][0]) break; [heap[pk], heap[k]] = [heap[k], heap[pk]]; k = pk; } };
  const pop = () => { const top = heap[0], last = heap.pop(); if (heap.length) { heap[0] = last; let k = 0; for (;;) { let l = 2 * k + 1, r = l + 1, m = k; if (l < heap.length && heap[l][0] < heap[m][0]) m = l; if (r < heap.length && heap[r][0] < heap[m][0]) m = r; if (m === k) break; [heap[m], heap[k]] = [heap[k], heap[m]]; k = m; } } return top; };
  const hc = (cx, cy) => { const dx = Math.abs(cx - gC[0]), dy = Math.abs(cy - gC[1]); return (dx + dy) + (Math.SQRT2 - 2) * Math.min(dx, dy); };
  g[idx(sC[0], sC[1])] = 0; push(hc(sC[0], sC[1]), idx(sC[0], sC[1]));
  let found = false;
  while (heap.length) {
    const [, i] = pop(); if (closed[i]) continue; closed[i] = 1;
    const cx = i % W, cy = (i / W) | 0;
    if (cx === gC[0] && cy === gC[1]) { found = true; break; }
    for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
      if (!dx && !dy) continue; const nx = cx + dx, ny = cy + dy;
      if (!free(nx, ny)) continue; if (dx && dy && !(free(cx + dx, cy) && free(cx, cy + dy))) continue;
      const j = idx(nx, ny), ng = g[i] + (dx && dy ? Math.SQRT2 : 1);
      if (ng < g[j]) { g[j] = ng; from[j] = i; push(ng + hc(nx, ny), j); }
    }
  }
  if (!found) return null;
  const cells = []; for (let i = idx(gC[0], gC[1]); i >= 0; i = from[i]) cells.push(at(i % W, (i / W) | 0)); cells.reverse();
  const clear = (p, q) => { const n = Math.ceil(Math.hypot(q[0] - p[0], q[1] - p[1]) / 3); for (let k = 1; k < n; k++) { const t = k / n; if (!walkable(v, [p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t])) return false; } return true; };
  const goal = walkable(v, b) ? b : cells[cells.length - 1], out = []; let anchor = a, k = 0;
  while (k < cells.length) {
    let far = k; for (let m = cells.length - 1; m > k; m--) if (clear(anchor, cells[m])) { far = m; break; }
    out.push(cells[far]); anchor = cells[far]; k = far + 1;
  }
  if (out.length) out[out.length - 1] = goal; else out.push(goal);
  return out;
}
/* Set where to walk. Plans a way round obstacles when it can; otherwise heads straight there and creeps round whatever is in the way. */
/* The closest spot to p that is on the floor and not inside furniture, so a click on a table walks up to the table, not into it. */
function nearestWalkable(v, p, maxR) {
  if (walkable(v, p)) return p;
  for (let r = 4; r <= (maxR || 400); r += 4) {
    let best = null, bd = Infinity;
    for (let k = 0; k < 32; k++) {
      const a = k / 32 * Math.PI * 2, q = [p[0] + Math.cos(a) * r, p[1] + Math.sin(a) * r];
      if (walkable(v, q)) { const d = Math.hypot(q[0] - p[0], q[1] - p[1]); if (d < bd) { bd = d; best = q; } }
    }
    if (best) return best;
  }
  return p;
}
function setTarget(pt) {
  S.stall = null;
  if (pt && S.view.zones.length) pt = nearestWalkable(S.view, pt);
  S.target = pt; S.path = [];
  if (!pt || !S.view.zones.length) return;
  const route = findPath(S.view, S.pos, pt);
  if (route) S.path = route;
}
function stepTowards(dt) {
  if (!S.target || !S.view.zones.length) return false;
  const v = S.view, p = S.pos;
  while (S.path && S.path.length && Math.hypot(S.path[0][0] - p[0], S.path[0][1] - p[1]) <= ARRIVE_PX) S.path.shift();
  const wp = (S.path && S.path.length) ? S.path[0] : S.target;
  const dx = wp[0] - p[0], dy = wp[1] - p[1], d = Math.hypot(dx, dy);
  if (d <= ARRIVE_PX) {
    if (wp === S.target || !(S.path && S.path.length)) { S.pos = [S.target[0], S.target[1]]; S.target = null; S.path = []; S.moving = false; return true; }
    S.path.shift(); return true;
  }
  // give up when creeping gets nowhere (no closer to the next waypoint for 3 seconds): it stands still instead of shuffling forever
  if (!S.stall || S.stall.wp !== wp || d < S.stall.best - 1) S.stall = { wp, best: d, t: 0 }; else S.stall.t += dt;
  if (S.stall.t > 3) { S.target = null; S.path = []; S.moving = false; S.stall = null; return true; }
  const len = Math.min(d, Math.max(1, walkSpeedPx(p, dx, dy) * dt));
  const step = creepStep(v, p, dx, dy, len);
  if (!step) { S.target = null; S.path = []; S.moving = false; return true; }            // boxed in: stop
  S.pos = step.pos; S.vel = step.dir; S.moving = true;
  return true;
}
/* Arrow keys / WASD: walk while held. Up is away from the viewer, down is towards it. */
const HELD = new Set();
function keyDir() {
  const dx = (HELD.has("ArrowRight") || HELD.has("d") ? 1 : 0) - (HELD.has("ArrowLeft") || HELD.has("a") ? 1 : 0);
  const dy = (HELD.has("ArrowDown") || HELD.has("s") ? 1 : 0) - (HELD.has("ArrowUp") || HELD.has("w") ? 1 : 0);
  return [dx, dy];
}
function stepKeys(dt) {
  const [dx, dy] = keyDir(); if (!dx && !dy) return false;
  if (!S.view || !S.view.zones.length) return false;
  S.target = null; S.path = []; S.pendingDoor = null;
  const len = Math.max(1, walkSpeedPx(S.pos, dx, dy) * (HELD.has("Shift") ? 1.8 : 1) * dt);
  const step = creepStep(S.view, S.pos, dx, dy, len);
  if (!step) { S.moving = false; return true; }
  S.pos = step.pos; S.vel = step.dir; S.moving = true; return true;
}
function checkDoors() {
  const v = S.view; if (!v.zones.length) return;
  let near = null;
  for (const g of groupDoors(v)) {
    const reach = Math.max(...g.doors.map(d => doorReach(v, d)));
    if (dist(S.pos, g.at) <= reach) { near = g; break; }
  }
  if (!near) { S.armed = true; return; }
  if (!S.armed) return;
  if (S.bubbleFor === near) return;
  S.armed = false; showDoorBubble(near);
}
function frame(t) {
  const dt = Math.min(0.1, (t - (S.lastT || t)) / 1000); S.lastT = t; S.dt = dt;
  if (S.view) {
    const keyed = stepKeys(dt);
    if (!S.target && !keyed) S.moving = false;
    if (keyed || stepTowards(dt)) {
      checkDoors();
      if (!S.target && S.pendingDoor) { const g = S.pendingDoor; S.pendingDoor = null; if (!S.bubbleFor) showDoorBubble(g); }
    }
    draw(); updateReadout();
  }
  requestAnimationFrame(frame);
}

/* ------------------------------ bubbles ----------------------------------- */
function hideBubble() { const b = $("bubble"); b.hidden = true; b.textContent = ""; S.bubbleFor = null; }
function moveBubble() {
  const b = $("bubble"); if (b.hidden || !S.bubbleAt) return;
  const [sx, sy] = toScreen(S.bubbleAt);
  const w = b.offsetWidth, h = b.offsetHeight;
  b.style.left = Math.max(8, Math.min(S.fit.cw - w - 8, sx - w / 2)) + "px";
  b.style.top = Math.max(8, Math.min(S.fit.ch - h - 8, sy - h - 24)) + "px";
}
function makeButton(text, fn, disabled) {
  const b = document.createElement("button"); b.type = "button"; b.textContent = text; b.disabled = !!disabled;
  b.addEventListener("click", fn); return b;
}
function showBubble(title, body, buttons, at) {
  const b = $("bubble"); b.textContent = "";
  const h = document.createElement("h3"); h.textContent = title; b.appendChild(h);
  if (body) { const p = document.createElement("p"); p.textContent = body; b.appendChild(p); }
  const box = document.createElement("div"); box.className = "choices";
  for (const x of buttons) box.appendChild(x);
  b.appendChild(box); b.hidden = false; S.bubbleAt = at; moveBubble();
  const first = box.querySelector("button:not(:disabled)"); if (first) first.focus({ preventScroll: true });
}
function showDoorBubble(g) {
  S.bubbleFor = g;
  const btns = g.doors.map(d => {
    const room = S.rooms[d.to];
    const unbuilt = !room || room.locked || !room.views.length;
    const label = doorName(d) + (room && room.locked ? "  (locked: not built yet)" : (room && !room.views.length ? "  (no picture yet)" : ""));
    return makeButton(label, () => { hideBubble(); goTo(d.to, S.room.id); }, unbuilt);
  });
  btns.push(makeButton("Stay here", () => { hideBubble(); }));
  const names = g.doors.map(doorName);
  const verbish = /^(back|into|up|down|out|to|through|onto)\b/i.test(names[0]);
  showBubble(g.doors.length > 1 ? "Which way?" : (verbish ? names[0] : "Go to " + names[0]) + "?", g.doors.length > 1 ? "" : (g.doors[0].note || ""), btns, g.at);
}
function showHotspotBubble(h) {
  S.bubbleFor = h;
  const a = h.action || {}, L = window.PubCastLive, live = L ? L.actionFor(h) : null;
  const btns = [];
  if (a.type === "view") btns.push(makeButton("Open " + h.label, () => { hideBubble(); openCloseup(a.view); }));
  if (live) btns.push(makeButton(a.type === "view" ? "Use it here" : "Use", () => runLive(h, live, null)));
  btns.push(makeButton("Close", () => hideBubble()));
  const text = a.type === "view" ? (a.event || "Opens a close-up view.") : (a.event || a.animation || a.program || "");
  showBubble(h.label, (a.type === "view" || live ? "" : "Not wired yet. It would: ") + text, btns, h.at);
}
/* Run a hotspot's action on the PubCast host and show the answer, with any follow-up choices it offers. */
async function runLive(h, action, data) {
  const L = window.PubCastLive; if (!L) return;
  const at = h.at;
  showBubble(h.label, "Working\u2026", [], at);
  const out = data ? await L.call(action, data) : await L.use(h);
  if (S.bubbleFor !== h) return;                         // the walker moved on (new picture or another click)
  const d = L.describe(action, out);
  const btns = (d.choices || []).map(c => makeButton(c.label, () => runLive(h, c.action, c.data || {})));
  btns.push(makeButton("Close", () => hideBubble()));
  showBubble(d.title, d.lines.join("\n"), btns, at);
}
function setLiveChip(st) {
  const c = $("chipLive"); if (!c || !st) return;
  c.classList.toggle("on", !!st.online && st.onAir !== true);
  c.classList.toggle("air", st.onAir === true);
  c.textContent = "\u25CF " + (st.onAir === true ? "On air" : st.online ? "Connected" : "Offline");
  c.title = st.online ? "Connected to the PubCast host" + (st.room ? " in " + st.room : "") : "Not connected to the PubCast host. Walking still works.";
}
window.addEventListener("pubcast:live-status", e => setLiveChip(e.detail));
window.addEventListener("pubcast:room", e => {
  const a = $("classicLink"), r = e.detail && e.detail.room;
  // the classic page only knows the rooms it was drawn with; anywhere else it opens at its own start
  if (a) a.href = r ? "/world?room=" + encodeURIComponent(r) : "/world";
});

/* ------------------------------ input ------------------------------------- */
function hitTest(p) {
  const v = S.view, tol = 14 / S.fit.s;
  for (const h of v.hotspots) if (dist(p, h.at) <= Math.max(h.r * 0.5, tol)) return { type: "hotspot", h };
  for (const g of groupDoors(v)) if (dist(p, g.at) <= Math.max(g.r, tol)) return { type: "door", g };
  return null;
}
canvas.addEventListener("pointermove", e => {
  if (!S.view) return;
  if (S.canDrag) {
    const d = S.canDrag, p = toPicture(e.clientX, e.clientY), k = canListNow()[d.i]; if (!k) return;
    if (d.mode === "move") { k.x = p[0] - d.dx; k.y = p[1] - d.dy; if (k.fy != null) k.fy = k.y + d.fyOff; }
    else { const top = p[1] + 10 / S.fit.s; k.h = Math.max(4, Math.min(600, k.y - top)); }
    applyCans(); return;
  }
  if (canHit(toPicture(e.clientX, e.clientY))) { canvas.style.cursor = "grab"; return; }
  const hit = S.show.doors ? hitTest(toPicture(e.clientX, e.clientY)) : null;
  canvas.style.cursor = hit ? "pointer" : (S.view.zones.length ? "crosshair" : "default");
});
canvas.addEventListener("pointerdown", e => {
  // a focused dropdown or slider would swallow the arrow keys (the dropdown would even flip rooms), so hand focus back to the picture
  const ae = document.activeElement; if (ae && ae !== document.body && /^(SELECT|INPUT|TEXTAREA|BUTTON)$/.test(ae.tagName)) ae.blur();
  if (!S.view || e.button > 0) return;
  const p = toPicture(e.clientX, e.clientY);
  if (p[0] < 0 || p[1] < 0 || p[0] > S.view.w || p[1] > S.view.h) return;
  hideBubble();
  if (S.canArm === "place") {
    const ppi = ppiFor(sizingOf(S.view), p[1], null, zoneAt(S.view, p)), h = ppi ? Math.max(8, ppi * CAN_IN) : 24;
    canListNow().push({ x: p[0], y: p[1], h: Math.round(h), fy: null }); S.canSel = canListNow().length - 1; S.canArm = null;
    applyCans(); buildCans(); toast("Drag the yellow dot to size the can until it looks right"); return;
  }
  if (S.canArm && S.canArm.floor !== undefined) {
    const k = canListNow()[S.canArm.floor]; if (k) k.fy = Math.max(k.y, p[1]); S.canArm = null; applyCans(); buildCans(); return;
  }
  const ch = canHit(p);
  if (ch) {
    const k = canListNow()[ch.i]; S.canSel = ch.i;
    S.canDrag = { i: ch.i, mode: ch.mode, dx: p[0] - k.x, dy: p[1] - k.y, fyOff: k.fy == null ? 0 : k.fy - k.y };
    try { canvas.setPointerCapture(e.pointerId); } catch (err) { /* older browsers */ }
    buildCans(); return;
  }
  const hit = hitTest(p);
  if (hit && hit.type === "hotspot") {
    if (S.view.zones.length && distanceToFloor(S.view, hit.h.at) > 40) { setTarget(snapToFloor(S.view, hit.h.at)); }
    showHotspotBubble(hit.h); return;
  }
  if (!S.view.zones.length) return;
  if (hit && hit.type === "door") { S.pendingDoor = hit.g; S.armed = true; setTarget(snapToFloor(S.view, hit.g.at)); return; }
  S.pendingDoor = null;
  setTarget(snapToFloor(S.view, p));
});
canvas.addEventListener("pointerup", () => { if (S.canDrag) { S.canDrag = null; buildCans(); } });
const MOVE_KEYS = new Set(["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "w", "a", "s", "d", "W", "A", "S", "D"]);
const typing = e => /^(INPUT|SELECT|TEXTAREA)$/.test((e.target && e.target.tagName) || "") && !(e.target.type === "checkbox" || e.target.type === "radio");
window.addEventListener("keydown", e => {
  if (MOVE_KEYS.has(e.key) && !typing(e) && !e.ctrlKey && !e.metaKey && !e.altKey) { HELD.add(e.key.length === 1 ? e.key.toLowerCase() : e.key); e.preventDefault(); }
  else if (e.key === "Shift") HELD.add("Shift");
});
window.addEventListener("keyup", e => { HELD.delete(e.key.length === 1 ? e.key.toLowerCase() : e.key); });
window.addEventListener("blur", () => HELD.clear());
window.addEventListener("keydown", e => {
  if (e.key === "Escape") { if (!$("bubble").hidden) hideBubble(); else if (S.history.length) goBack(); }
});
$("back").addEventListener("click", goBack);
$("viewSel").addEventListener("change", e => {
  const [r, v] = e.target.value.split("/"); S.history = []; setView(r, v, {});
  e.target.blur();                                  // so the arrow keys walk instead of flipping through rooms
});
document.querySelectorAll("input[name=char]").forEach(r => r.addEventListener("change", e => { S.char = e.target.value; syncLibrarySelect(); }));
const bind = (id, k) => $(id).addEventListener("change", e => { S.show[k] = e.target.checked; });
bind("shPads", "pads"); bind("shOcc", "occ"); bind("shDoors", "doors"); bind("shHorizon", "horizon"); bind("shRefs", "refs"); bind("shAlt", "alt");
$("themeLight").addEventListener("change", e => {
  document.documentElement.dataset.theme = e.target.checked ? "light" : "dark";
});
window.addEventListener("resize", resize);

/* ------------------------------ panel ------------------------------------- */
const CONF_WORDS = {
  good: "good: measured from several known-size things that agree",
  fair: "fair: measured, but from few things, or with an assumption",
  low: "low: thin or conflicting evidence. Your eye decides.",
};
function el(tag, text, cls) { const e = document.createElement(tag); if (text !== undefined) e.textContent = text; if (cls) e.className = cls; return e; }
function refreshPanel() {
  const v = S.view, info = v.scale_info, box = $("sizeInfo"); box.textContent = "";
  if (info) {
    const line = el("div"); const b = el("span", info.confidence, "badge " + info.confidence); line.appendChild(b);
    line.appendChild(el("span", "  " + CONF_WORDS[info.confidence], "dim")); box.appendChild(line);
    box.appendChild(el("p", info.basis));
    const det = el("details"); det.appendChild(el("summary", "What was measured"));
    const ul = el("ul", undefined, "tight"); info.refs.forEach(r => ul.appendChild(el("li", r))); det.appendChild(ul); box.appendChild(det);
    if (v.camera) box.appendChild(el("p", "Proposed camera: horizon at row " + v.camera.horizon_y + ", eye height " + v.camera.eye_in + " in.", "dim"));
  } else box.appendChild(el("p", "No avatar size for this picture yet: it has no floor to walk on, or it is waiting on your answer.", "dim"));
  $("altRow").hidden = !(info && info.alt);
  if (!(info && info.alt)) { S.show.alt = false; $("shAlt").checked = false; }
  else $("altRow").lastChild.textContent = " Alternative reading (grey): " + info.alt.label;
  buildTuner(); buildCans(); buildOpen(); updateTuneOut(); setGlbInfo();
}
function slider(label, min, max, step, value, onInput) {
  const wrap = el("div"); wrap.className = "row";
  const l = el("label", label); l.style.display = "block"; const o = el("output");
  const r = document.createElement("input"); r.type = "range"; r.min = min; r.max = max; r.step = step; r.value = value;
  r.setAttribute("aria-label", label); o.textContent = (+value).toFixed(step < 1 ? 2 : 0);
  r.addEventListener("input", () => { o.textContent = (+r.value).toFixed(step < 1 ? 2 : 0); onInput(+r.value); });
  wrap.appendChild(l); wrap.appendChild(o); const full = el("div"); full.style.gridColumn = "1 / -1"; full.appendChild(r); wrap.appendChild(full);
  return wrap;
}
function buildTuner() {
  const v = S.view, box = $("tuner"); box.textContent = "";
  if (!v.zones.length) { box.appendChild(el("p", "Nothing to tune: no walkable floor in this picture.", "dim")); return; }
  const cur = sizingOf(v, undefined, true);
  const t0 = S.tune[S.key] || {};
  box.appendChild(slider("Everything bigger or smaller (x)", 0.5, 2, 0.01, t0.mult || 1, val => tuneMult(val)));
  if (t0.fromCans) { box.appendChild(el("p", "Your cans are sizing this picture, so the camera / sample sliders are off. Untick \"Size the avatars from my cans\" to use them.", "dim")); return; }
  if (v.camera) {
    box.appendChild(el("p", "Move the horizon and the camera's height until the figures look right against the furniture. The three reference figures show the same size rule at three depths.", "dim"));
    box.appendChild(slider("Horizon row", -Math.round(v.h * .5), Math.round(v.h * .9), 1, cur.camera.horizon_y, val => tuneCamera("horizon_y", val)));
    box.appendChild(slider("Camera height (inches above the floor)", 24, 400, 1, cur.camera.eye_in, val => tuneCamera("eye_in", val)));
  } else {
    box.appendChild(el("p", "This picture has two size samples (pixels per real inch at a screen row). Change either one.", "dim"));
    cur.scale.forEach((s, i) => box.appendChild(slider("Pixels per inch at row " + s.y, 0.1, 12, 0.05, s.ppi, val => tuneSample(i, val))));
  }
}
function tuneMult(val) {
  const t = S.tune[S.key] = S.tune[S.key] || {};
  t.mult = val; saveTune(); updateTuneOut();
}
function tuneCamera(field, val) {
  const base = S.view.camera, t = S.tune[S.key] = S.tune[S.key] || { camera: { horizon_y: base.horizon_y, eye_in: base.eye_in } };
  if (!t.camera) t.camera = { horizon_y: base.horizon_y, eye_in: base.eye_in };
  t.camera[field] = val; saveTune(); updateTuneOut();
}
function tuneSample(i, val) {
  const t = S.tune[S.key] = S.tune[S.key] || { scale: S.view.scale.map(s => ({ y: s.y, ppi: s.ppi })) };
  if (!t.scale) t.scale = S.view.scale.map(s => ({ y: s.y, ppi: s.ppi }));
  t.scale[i].ppi = val; saveTune(); updateTuneOut();
}
function exportObject() { return { tune: S.tune, cans: S.cans }; }
function updateTuneOut() { $("tuneOut").value = JSON.stringify(exportObject(), null, 1); }
$("tuneReset").addEventListener("click", () => { delete S.tune[S.key]; saveTune(); refreshPanel(); toast("Back to the proposed size for this picture"); });
$("tuneCopy").addEventListener("click", async () => {
  const text = JSON.stringify(exportObject(), null, 1);
  try { await navigator.clipboard.writeText(text); toast("Copied. Paste it to Claude."); }
  catch (e) { $("tuneOut").parentElement.open = true; $("tuneOut").select(); toast("Select and copy the text in the box"); }
});
function buildOpen() {
  const v = S.view, box = $("open"); box.textContent = ""; const items = [];
  items.push("Status: " + v.status + (v.status === "proposed" ? " (placed by Claude by eye, not approved by you)" : ""));
  for (const z of v.zones) {
    if (z.z_in === null) items.push("Zone " + z.id + ": how high or low its floor is");
    if (z.kind !== "floor" && z.rise_in === null) {
      let t = "Zone " + z.id + ": how far the " + z.kind + " climbs";
      if (v.camera) { const top = Math.min(...z.points.map(p => p[1])); if (top <= v.camera.horizon_y) t += " (more than " + v.camera.eye_in + " in: it is drawn above the camera's eye line)"; }
      items.push(t);
    }
  }
  if (v.scale_info && v.scale_info.alt) items.push("Which size reading looks right: coloured or grey");
  if (v.scale_info && v.scale_info.confidence === "low") items.push("Avatar size is low confidence: look at it against the furniture");
  const d = v.doors.filter(x => x.status !== "confirmed").length;
  if (d) items.push(d + " door spot(s) are my guess (red dots), not yours");
  const ul = el("ul", undefined, "tight"); items.forEach(t => ul.appendChild(el("li", t))); box.appendChild(ul);
}
function updateReadout() {
  const v = S.view; let text;
  if (!v.zones.length) text = "No walkable floor in this picture.";
  else {
    const zone = zoneAt(v, S.pos), alt = zone ? altitudeAt(zone, S.pos) : null;
    const sz = sizingOf(v), ppi = ppiFor(sz, S.pos[1], alt, zone), H = ppi ? heightIn(S.char) * ppi : null;
    const lines = ["Feet at (" + Math.round(S.pos[0]) + ", " + Math.round(S.pos[1]) + ")",
      "On: " + (zone ? zone.id + " (" + zone.level + ")" : "off the floor"),
      "Altitude: " + (alt === null ? "not known yet (drawn as if on the main floor)" : Math.round(alt) + " in"),
      "Size here: " + (ppi ? ppi.toFixed(2) + " px per inch, " + CHAR[S.char].label + " drawn " + Math.round(H) + " px tall" : "no size here")];
    const behind = v.occluders.filter(o => occluderInFront(o, S.pos[1], S.pos[0]));
    if (v.occluders.length) lines.push("In front of you: " + (behind.length ? behind.map(o => o.label || o.id).join(", ") : "nothing"));
    text = lines.join("\n");
  }
  if (text !== S.lastReadout) { S.lastReadout = text; const r = $("readout"); r.textContent = ""; text.split("\n").forEach(l => r.appendChild(el("div", l))); }
}

/* ------------------------------ 3D avatars -------------------------------- */
function setGlbInfo(msg) {
  const G = window.PubCastGLB, box = $("glbInfo"); if (!box) return;
  const parts = [];
  if (G) for (const id of CHAR_ORDER) { const i = G.info(id); if (i) parts.push(CHAR[id].label + ": " + i.label + (i.clips.length ? " (" + i.clips.join(", ") + ")" : " (no animations: it sways)")); }
  box.textContent = (msg ? msg + " " : "") + (parts.length ? "Loaded: " + parts.join("; ") + "." : (G && G.state.lastError ? "Could not draw it: " + G.state.lastError : "No 3D avatar loaded: flat figures."));
}
async function loadGlb(url, label) {
  const G = window.PubCastGLB;
  if (!G) { toast("The 3D part is still loading, try again in a moment"); return; }
  try {
    const r = await G.load(S.char, url, label);
    G.state.lastError = "";
    setGlbInfo(r.skinned ? "" : "Note: this file is not rigged, so it will glide without animating.");
    toast(CHAR[S.char].label + " is now " + label);
    return true;
  } catch (e) { G.state.lastError = String(e && e.message || e); setGlbInfo(); toast("That file would not load: " + G.state.lastError); return false; }
}
$("glbMannequin").addEventListener("click", () => { delete S.avatarIds[S.char]; loadGlb("/static/world/test_avatars/Xbot.glb", "test mannequin").then(syncLibrarySelect); });
$("glbPick").addEventListener("click", () => $("glbFile").click());
$("glbFile").addEventListener("change", e => {
  const f = e.target.files && e.target.files[0]; if (!f) return;
  delete S.avatarIds[S.char];
  const url = URL.createObjectURL(f); loadGlb(url, f.name).then(syncLibrarySelect).finally(() => setTimeout(() => URL.revokeObjectURL(url), 5000)); e.target.value = "";
});
$("glbClear").addEventListener("click", () => { const G = window.PubCastGLB; if (G) G.clear(S.char); delete S.avatarIds[S.char]; syncLibrarySelect(); setGlbInfo(); });
$("glbHolo").addEventListener("change", e => { const G = window.PubCastGLB; if (G) G.setHologram(e.target.checked); });
canvas.addEventListener("dragover", e => e.preventDefault());
canvas.addEventListener("drop", e => {
  e.preventDefault(); const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
  if (f && /\.glb$/i.test(f.name)) { const url = URL.createObjectURL(f); loadGlb(url, f.name).finally(() => setTimeout(() => URL.revokeObjectURL(url), 5000)); }
});

/* ------------------------------ your progress (kept on the host) ---------- */
function libraryEntry(id) { return S.library.find(a => a.id === id) || null; }
function syncLibrarySelect() {
  const sel = $("glbLibrary"); if (!sel) return;
  sel.textContent = "";
  sel.appendChild(new Option("(none for this character)", ""));
  for (const a of S.library) sel.appendChild(new Option(a.name + (a.canonical_height_in ? "  (" + a.canonical_height_in + " in)" : ""), a.id));
  sel.value = S.avatarIds[S.char] && libraryEntry(S.avatarIds[S.char]) ? S.avatarIds[S.char] : "";
}
async function refreshLibrary() {
  const L = window.PubCastLive; if (!L) return;
  S.library = await L.avatarLibrary();
  const host = L.state.host === true;
  $("glbLibraryRow").hidden = !host; $("glbImportRow").hidden = !host;
  syncLibrarySelect();
}
$("glbLibrary").addEventListener("change", async e => {
  const a = libraryEntry(e.target.value);
  if (!a) { const G = window.PubCastGLB; if (G) G.clear(S.char); delete S.avatarIds[S.char]; setGlbInfo(); return; }
  if (await loadGlb(a.url, a.name)) S.avatarIds[S.char] = a.id;
  syncLibrarySelect();
});
/* wait for the 3D part (a module that loads on its own) before putting saved avatars on */
function glbReady() {
  return window.PubCastGLB ? Promise.resolve(window.PubCastGLB)
    : new Promise(res => document.addEventListener("pubcast-glb-ready", () => res(window.PubCastGLB), { once: true }));
}
async function wearSavedAvatars() {
  const G = await glbReady();
  for (const [ch, id] of Object.entries(S.avatarIds)) {
    const a = libraryEntry(id); if (!a || !CHAR[ch]) { delete S.avatarIds[ch]; continue; }
    try { await G.load(ch, a.url, a.name); } catch (e) { G.state.lastError = String(e && e.message || e); delete S.avatarIds[ch]; }
  }
  setGlbInfo(); syncLibrarySelect();
}
function progressSnapshot() {
  if (!S.room || !S.view) return null;
  const closeup = S.history.length > 0;               // a close-up returns you to the room you came from
  const base = closeup ? S.history[0] : { room: S.room.id, view: S.view.id, pos: S.pos };
  const G = window.PubCastGLB;
  return { room: base.room, view: base.view, pos: [Math.round(base.pos[0] * 100) / 100, Math.round(base.pos[1] * 100) / 100],
           char: S.char, avatars: Object.assign({}, S.avatarIds), hologram: !!(G && G.state.hologram), tune: S.tune, cans: S.cans };
}
function keepProgress(now) {
  const L = window.PubCastLive; if (!L) return;
  if (!now && (S.moving || S.target)) return;          // saved when you stop, not every step
  const snap = progressSnapshot(); if (snap) L.saveProgress(snap, now);
}
setInterval(() => keepProgress(false), 1000);
addEventListener("pagehide", () => keepProgress(true));
document.addEventListener("visibilitychange", () => { if (document.visibilityState === "hidden") keepProgress(true); });
window.addEventListener("pubcast:live-status", e => {
  const st = e.detail || {}, box = $("progressInfo"); if (!box) return;
  box.textContent = st.host === false ? "Progress is kept only when PubCast is running behind this page."
    : st.progressSavedAt ? "Progress saved on this PubCast (revision " + st.progressRevision + ")." : "";
});

/* ------------------------------ boot -------------------------------------- */
window.PubCastWalk = {
  S, ppiFor, ppiAtSamples, floorRunsAtRow, fitSamples, pointInPolygon, snapToFloor, zoneAt, altitudeAt, axisFraction,
  occluderInFront, objectBaseY, blockedAt, floorContains, distanceToFloor, doorReach, groupDoors, startPosition, setView, goTo,
  avatarPx, figureList, hitTest, toScreen, toPicture, sizingOf, draw, resize, centroid, defaultStart,
  showHotspotBubble, runLive, hideBubble,
};
(async function boot() {
  S.tune = loadTune(); S.cans = loadCans();
  try {
    await loadWorld(); fillViewSelect();
    const q = new URLSearchParams(location.search), k = q.get("view"), live = q.get("live");
    // what you saved on this PubCast: your tuning, who you walk as and your avatars always come back; your room and
    // spot come back unless this link asks for a particular place
    const L = window.PubCastLive, saved = L ? await L.loadProgress() : null;
    if (saved) {
      if (saved.tune && typeof saved.tune === "object") { S.tune = saved.tune; saveTune(); }
      if (saved.cans && typeof saved.cans === "object") { S.cans = saved.cans; saveCans(); }
      if (saved.char && CHAR[saved.char]) { S.char = saved.char; const r = document.querySelector('input[name=char][value="' + saved.char + '"]'); if (r) r.checked = true; }
      if (saved.avatars && typeof saved.avatars === "object") S.avatarIds = Object.assign({}, saved.avatars);
    }
    const resume = saved && !k && !live && saved.room && S.rooms[saved.room] && !S.rooms[saved.room].locked ? saved : null;
    const byLive = live ? S.world.rooms.find(r => r.views.length && !r.locked && (r.live_id === live || r.layout_id === live || r.id === live)) : null;
    // with no ?live= or ?view=, start where the world says (the dressing room), else the first room that has a picture
    const home = S.world.rooms.find(r => r.id === S.world.start && r.views.length && !r.locked) || S.world.rooms.find(r => r.views.length);
    const first = byLive ? [byLive.id, null] : k && k.includes("/") ? k.split("/") : resume ? [resume.room, resume.view || null] : [home.id, null];
    await setView(first[0], first[1], { instant: true });
    if (resume && Array.isArray(resume.pos) && S.view.id === (resume.view || S.view.id) && S.view.zones.length && walkable(S.view, resume.pos)) S.pos = resume.pos.slice();
    refreshLibrary().then(() => { if (Object.keys(S.avatarIds).length) wearSavedAvatars(); });
    if (saved && typeof saved.hologram === "boolean") { $("glbHolo").checked = saved.hologram; glbReady().then(G => G.setHologram(saved.hologram)); }
    if (q.get("pads") === "0") { S.show.pads = false; $("shPads").checked = false; }
    if (q.get("refs") === "1") { S.show.refs = true; $("shRefs").checked = true; }
    if (q.get("occ") === "1") { S.show.occ = true; $("shOcc").checked = true; }
    document.documentElement.dataset.ready = "1";
    requestAnimationFrame(frame);
  } catch (e) {
    toast("Could not start: " + e.message, 8000);
    document.documentElement.dataset.error = e.message;
  }
})();
</script>
</body>
</html>

`````

## static/world_walk_live.js

SHA-256: ea9d67b6653045927c4073e070fb6c9f19ca63619e91eb076849e197e6f337b9

`````text
/* PubCast world walk: the live link to the running Reach host.
 *
 * The walkable world (static/world_walk.html) draws and walks the rooms on its own. This file connects it to the same
 * backend the classic PubWorld page (static/world.html) uses, with the same protocol, so both pages are one world:
 *
 *   - presence   room_change over /pubworld/ws/{client_id}, using each room's live id (the id world.html, the room audio
 *                runtime and the backend already know). While the socket is down the room is held and sent on reconnect.
 *                It also raises the page event "pubcast:room" that static/program_audio_runtime.js listens to, so room
 *                audio rules (the dressing room only lets director announcements through) follow the walker too.
 *   - hotspots   a world hotspot that matches a backend action (typewriter, scripts, phone, wardrobe, makeup, message board,
 *                TV, sitting) calls POST /pubworld/api/hotspot exactly as world.html does, and the result is described as a
 *                title, lines and follow-up choices for the walker to show.
 *   - on air     the production state the backend pushes (welcome / production_state) is kept and announced.
 *
 * Auth follows world.html: when a Reach session exists its token is sent as the first socket message; an auth_error
 * clears the session and sends you to the login page, which returns here.
 * Nothing in this file draws anything. The walker listens for "pubcast:live-status" and calls PubCastLive.actionFor/use.
 */
(function (global) {
  "use strict";

  const PING_MS = 25000, RECONNECT_MS = 4000, CONNECT_DELAY_MS = 600;
  const LOGIN_RETURN = "/walk";

  /* World hotspot id -> backend action (modules/pubworld_hotspots.py ACTION_HANDLERS). Ids not listed here, and close-up
     views, stay local to the walker. Sitting is matched by name so every couch, booth and stool spot is covered. */
  const ACTION_BY_ID = {
    "typewriter": "typewriter",
    "scripts": "scripts",
    "phone": "phone",
    "wardrobe": "wardrobe",
    "makeup-station": "makeup",
    "message-board": "message_board",
    "tv": "tv",
  };
  const SIT_RE = /(^|-)(sit|couch)(-|$)/;

  function actionFor(hotspot) {
    if (!hotspot || typeof hotspot.id !== "string") return null;
    if (Object.prototype.hasOwnProperty.call(ACTION_BY_ID, hotspot.id)) return ACTION_BY_ID[hotspot.id];
    const a = hotspot.action || {};
    if (a.type === "view") return null;                       // "sit down" at the typewriter is a change of picture
    return SIT_RE.test(hotspot.id) ? "sit" : null;
  }

  const clientId = "pw_" + Math.random().toString(36).slice(2, 10);
  const state = {
    clientId, host: null, online: false, ready: false, onAir: null,
    room: "", worldRoom: "", view: "", lastResult: null, lastError: "",
  };
  let ws = null, reconnectTimer = null, pingTimer = null, stopped = false;

  function auth() { return global.ReachAuth || null; }
  function token() { try { const a = auth(); return (a && a.getToken && a.getToken()) || ""; } catch (e) { return ""; } }
  function actorId() {
    try {
      const a = auth(), info = (a && a.getUser && a.getUser()) || {};
      return String(info.user_id || info.username || clientId);
    } catch (e) { return clientId; }
  }
  function announce() {
    global.dispatchEvent(new CustomEvent("pubcast:live-status", { detail: Object.assign({}, state) }));
  }
  function setOnline(on) {
    if (state.online === on && state.ready === on) return;
    state.online = on; state.ready = on; announce();
  }

  function send(obj) {
    if (state.ready && ws && ws.readyState === WebSocket.OPEN) {
      try { ws.send(JSON.stringify(obj)); return true; } catch (e) { return false; }
    }
    return false;
  }

  function post(path, body) {
    return fetch(path, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(Object.assign({ client_id: actorId() }, body)),
    });
  }

  function markReady() {
    if (state.ready) return;
    setOnline(true);
    if (state.room) send({ type: "room_change", room: state.room, view: state.view, world_room: state.worldRoom });
  }

  function onMessage(msg) {
    if (!msg || typeof msg !== "object") return;
    switch (msg.type) {
      case "auth_ok": markReady(); break;
      case "auth_error": {
        setOnline(false); stopped = true;
        const a = auth();
        try { if (a && a.clearSession) a.clearSession(); } catch (e) { /* nothing to clear */ }
        try { if (a && a.redirectToLogin) a.redirectToLogin(LOGIN_RETURN); } catch (e) { /* stay on the page, offline */ }
        break;
      }
      case "welcome":
        markReady();
        if (msg.payload && msg.payload.production_state) applyProduction(msg.payload.production_state);
        break;
      case "production_state": if (msg.payload) applyProduction(msg.payload); break;
      default: break;                                         // pong, room_ack, hotspot_result: nothing to do
    }
  }

  function applyProduction(p) {
    if (p && typeof p.on_air === "boolean" && p.on_air !== state.onAir) { state.onAir = p.on_air; announce(); }
  }

  function connect() {
    clearTimeout(reconnectTimer);
    if (stopped || typeof WebSocket === "undefined") return;
    const proto = global.location.protocol === "https:" ? "wss:" : "ws:";
    try { ws = new WebSocket(`${proto}//${global.location.host}/pubworld/ws/${clientId}`); }
    catch (e) { schedule(); return; }
    ws.onopen = () => {
      state.ready = false;
      const t = token();
      if (t) ws.send(JSON.stringify({ type: "auth", token: t }));
      else markReady();
    };
    ws.onmessage = ev => { try { onMessage(JSON.parse(ev.data)); } catch (e) { /* not JSON: ignore */ } };
    ws.onclose = () => { setOnline(false); schedule(); };
    ws.onerror = () => { state.lastError = "socket error"; };
  }
  function schedule() { if (!stopped) reconnectTimer = setTimeout(connect, RECONNECT_MS); }

  /* The walker calls this after every change of picture. `liveId` is the id the rest of PubCast uses for that room. */
  function enterView(detail) {
    const room = String((detail && (detail.liveId || detail.layoutId || detail.room)) || "");
    const changedRoom = room !== state.room;
    state.room = room; state.worldRoom = String(detail.room || ""); state.view = String(detail.view || "");
    if (changedRoom) global.dispatchEvent(new CustomEvent("pubcast:room", { detail: { room } }));
    if (!room) return;
    // Room changes exist only as a socket message (there is no REST route for them). While the socket is down the room
    // is kept in `state` and sent the moment the socket is ready again (markReady).
    send({ type: "room_change", room, view: state.view, world_room: state.worldRoom });
    announce();
  }

  function session() {
    let user = {};
    try { user = JSON.parse(global.sessionStorage.getItem("pubcast_user") || "null") || {}; } catch (e) { user = {}; }
    let sessionId = "default", projectId = "default";
    try { sessionId = global.sessionStorage.getItem("pubcastSessionId") || "default"; } catch (e) { /* default */ }
    try { projectId = global.localStorage.getItem("pubcastProjectId") || "default"; } catch (e) { /* default */ }
    return { session_id: sessionId, project_id: projectId, display_name: user.display_name || user.name || actorId() };
  }

  /* Run a backend action for a hotspot (or by name, for follow-up choices). Resolves to {status, result} like world.html. */
  async function call(action, data) {
    if (state.host === false) return OFFLINE;
    const body = { room: state.room, action, data: Object.assign({}, data || {}) };
    send(Object.assign({ type: "hotspot" }, body));
    try {
      const res = await post("/pubworld/api/hotspot", body);
      // a page served without the host (a plain file server) answers 404 or HTML, not the hotspot API
      if (res.status === 404 || res.status === 405 || !/json/i.test(res.headers.get("content-type") || "")) {
        state.lastResult = { action, out: OFFLINE }; return OFFLINE;
      }
      const out = await res.json().catch(() => ({ status: "error", message: "The host sent back something that is not JSON" }));
      if (!res.ok && out.status === undefined) out.status = "error";
      state.lastResult = { action, out }; return out;
    } catch (e) {
      state.lastError = String((e && e.message) || e);
      return OFFLINE;
    }
  }
  function use(hotspot, extra) {
    const action = actionFor(hotspot);
    if (!action) return Promise.resolve({ status: "local" });
    const data = Object.assign({}, extra || {});
    if (action === "sit") data.location = data.location || String(hotspot.label || "seat").replace(/^sit\s*\(?|\)?$/gi, "").trim() || "seat";
    if (action === "phone") Object.assign(data, session());
    return call(action, data);
  }

  const OFFLINE = { status: "offline", message: "The PubCast host is not running behind this page, so this can't be used here. Walking still works." };
  const pretty = s => String(s || "").replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
  const TV = { off: "Off", stage_feed: "Stage feed", crew_chatter: "Crew chatter", uploaded_dailies: "Uploaded dailies", previs: "Previs",
               teaser_trailer: "Teaser trailer", pitch_presentation: "Pitch presentation", director_inspiration: "Director inspiration",
               my_media: "My media", my_music: "My music", pubcast_ai_channel: "PubCast AI channel" };

  /* Turn a backend reply into what the walker shows: {title, lines, choices:[{label, action, data}]}. */
  function describe(action, out) {
    if (!out || out.status === "offline") return { title: "Not connected", lines: [(out && out.message) || "PubCast is not reachable from this page right now."], choices: [] };
    if (out.status && out.status !== "ok") return { title: "That did not work", lines: [out.message || ("The host answered: " + out.status)], choices: [] };
    const r = out.result || {};
    switch (action) {
      case "typewriter": return { title: "Typewriter", lines: ["Script draft " + (r.draft_id || "new") + ", " + (r.line_count || 0) + " lines so far."],
                                  choices: [{ label: "My scripts", action: "scripts" }] };
      case "scripts": return { title: "Scripts", lines: (r.scripts && r.scripts.length) ? r.scripts : ["No scripts yet."], choices: [] };
      case "phone": {
        const lines = ["Session " + (r.session_token || "-") + (r.call_handle ? ", your handle " + r.call_handle : "") + "."];
        for (const c of (r.contacts || [])) lines.push((c.credit_name || c.display_name || "Contact") + ": " + (((c.session_role || []).join(", ")) || "session contact") + ", " + (c.availability || "available"));
        if (!(r.contacts || []).length) lines.push("No connected dressing rooms yet.");
        return { title: "Phone", lines, choices: [] };
      }
      case "wardrobe": return { title: "Wardrobe", lines: ["Wearing: " + pretty(r.current || "default_outfit") + "."],
                                choices: (r.wardrobe_items || []).map(i => ({ label: pretty(i), action: "wardrobe", data: { current: i } })) };
      case "makeup": return { title: "Hair and makeup", lines: ["Current look: " + pretty(r.current || "natural") + "."],
                              choices: (r.styles || []).map(s => ({ label: pretty(s), action: "makeup", data: { current: s } })) };
      case "message_board": return { title: "Message board", lines: (r.messages && r.messages.length) ? r.messages.map(m => (m.from || "Someone") + ": " + (m.text || "")) : ["No messages."], choices: [] };
      case "tv": return { title: "TV", lines: ["Channel: " + (TV[r.channel] || pretty(r.channel || "off")) + "."], choices: [{ label: "Flip channel", action: "tv" }] };
      case "sit": return { title: "Take a seat", lines: ["You settle into the " + (r.location || "seat") + "."], choices: [] };
      default: return { title: pretty(action), lines: [JSON.stringify(r)], choices: [] };
    }
  }

  /* Is the PubCast host behind this page? /walk and /world-walk exist only on the host. Anywhere else (the page opened
     from a plain file server) ask /health once. Without a host nothing live is started: no socket, no room-audio polling,
     so the page stays quiet and walking works as before. */
  async function detectHost() {
    if (/^\/(walk|world-walk)\/?$/.test(global.location.pathname)) return true;
    try {
      const r = await fetch("/health", { cache: "no-store" });
      if (!r.ok || !/json/i.test(r.headers.get("content-type") || "")) return false;
      const j = await r.json();
      return !!j && j.status === "ok";
    } catch (e) { return false; }
  }
  /* The room audio runtime is the host's: load it only with a host, then tell it where the walker already is. */
  function loadAudioRuntime() {
    if (global.PubcastProgramAudio || global.document.querySelector('script[data-walk-audio]')) return;
    const sc = global.document.createElement("script");
    sc.src = "/static/program_audio_runtime.js"; sc.dataset.walkAudio = "1";
    sc.onload = () => { if (state.room) global.dispatchEvent(new CustomEvent("pubcast:room", { detail: { room: state.room } })); };
    global.document.head.appendChild(sc);
  }
  let starting = null;
  /* Resolves to whether the host is there; starts the live link once (safe to call any number of times). */
  function start() {
    if (!starting) starting = (async () => {
      state.host = await detectHost();
      announce();
      if (!state.host) return false;
      loadAudioRuntime();
      setTimeout(connect, CONNECT_DELAY_MS);
      pingTimer = setInterval(() => send({ type: "ping" }), PING_MS);
      return true;
    })();
    return starting;
  }
  function stop() { stopped = true; clearInterval(pingTimer); pingTimer = null; clearTimeout(reconnectTimer); try { if (ws) ws.close(); } catch (e) { /* closed */ } setOnline(false); }

  /* ---- Bella Faux Pas progress on the host (modules/studio_progress.py): one record per signed-in owner ---- */
  const PROGRESS_URL = "/api/studio/progress";
  const saving = { pending: null, timer: null, lastSent: "", inflight: null };
  state.progressRevision = 0; state.progressSavedAt = null;
  async function loadProgress() {
    if (!(await start())) return null;
    try {
      const r = await fetch(PROGRESS_URL, { cache: "no-store" });
      if (!r.ok || !/json/i.test(r.headers.get("content-type") || "")) return null;
      const j = await r.json();
      state.progressRevision = j.revision || 0; state.progressSavedAt = j.saved_at || null;
      saving.lastSent = JSON.stringify(j.progress || null);
      return j.progress || null;
    } catch (e) { return null; }
  }
  async function flushProgress(keepalive) {
    const p = saving.pending; if (!p || state.host !== true) return false;
    saving.pending = null; clearTimeout(saving.timer);
    const body = JSON.stringify(p);
    try {
      const r = await fetch(PROGRESS_URL, { method: "PUT", headers: { "Content-Type": "application/json" },
                                            body: JSON.stringify({ progress: p }), keepalive: !!keepalive });
      if (!r.ok) throw new Error("HTTP " + r.status);
      const j = await r.json();
      saving.lastSent = body; state.progressRevision = j.revision; state.progressSavedAt = j.saved_at; announce();
      return true;
    } catch (e) {
      state.lastError = "Could not save studio progress (" + ((e && e.message) || e) + "); it will try again";
      if (!saving.pending) { saving.pending = p; saving.timer = setTimeout(() => flushProgress(false), 5000); }
      announce();
      return false;
    }
  }
  /* Ask for `p` (the walker's whole progress snapshot) to be kept. Unchanged snapshots cost nothing; changes are
     grouped and sent a moment later, or straight away with now=true (used when the page is closing). */
  function saveProgress(p, now) {
    if (state.host !== true || !p) return;
    const body = JSON.stringify(p);
    if (body === saving.lastSent && !saving.pending) return;
    saving.pending = p; clearTimeout(saving.timer);
    if (now) flushProgress(true);
    else saving.timer = setTimeout(() => flushProgress(false), 900);
  }
  /* Your avatars in the avatar library (modules/avatar_imports.py), each already at its canonical height. */
  async function avatarLibrary() {
    if (!(await start())) return [];
    try {
      const r = await fetch("/api/avatars/imports", { cache: "no-store" });
      if (!r.ok) return [];
      const j = await r.json();
      return Array.isArray(j.avatars) ? j.avatars.filter(a => a && a.id && a.url) : [];
    } catch (e) { return []; }
  }

  global.PubCastLive = { state, actionFor, use, call, describe, enterView, start, stop, ACTION_BY_ID,
                         loadProgress, saveProgress, flushProgress, avatarLibrary };
  start();
})(window);

`````

## static/foresight_programs.js

SHA-256: ad85319a97b482d2e7e589707718682d9875ec1b40843a873b76e38bed7c6f42

`````text
/* Foresight Programs — everything PubCast can open in a tray, and how each one is put on its screen.

   This is the content provider for the Foresight Counter (foresight_counter.js). The counter owns each tray's
   physical life (where it sits, its shape and frame, how it is pushed, squeezed, locked, put away, closed into the
   fan); this module owns what is inside: the programs, rooms, tools, chats, web pages, videos and files, and their
   own working state. "A tray's physical state belongs to the tray. Its functional state belongs to its contents."
   (Josie, 2026-10-14.)

   The program list and the way each kind is mounted come from the earlier Foresight page (foresight.html, which is
   kept as it was): the same addresses, the same live status polling, the same Iteration Wallet check, the same
   browser, video, recording and file handling, the same messages from the pages inside trays. What is new is that
   each content also says what it needs from its tray: its natural size, the smallest size at which it stays usable,
   and the general shape it reads best in.

   Usage (see foresight_counter.html):
     const programs = ForesightPrograms.create({config, toast, ask});
     const counter = ForesightCounter.create({..., provider: programs.provider});
     programs.bind(counter);
     programs.open(id, data)   open a program by id (a singleton already open is brought forward instead)
*/
(function(root){
  'use strict';

  const DEFAULT_CONFIG = {
    // PubPartner's canonical full-host spine lives inside Reach; pubpartnerBase may point at a deliberate remote host.
    pubpartnerBase: '',
    pubpartnerStatusPath: '/api/pubpartner/status',
    // Same-origin gateway to the BotManager and the optional 2i utilities; pages never call port 8787 directly.
    twoIBase: '/api/foresight/bridge',
    twoIUi: '/writers-room',
    // Iteration Wallet is a separate local program with its own server (START_ITERATION_WALLET.ps1, port 7432).
    iterationWalletUrl: 'http://127.0.0.1:7432/',
  };

  // The general shape each kind of content reads best in (the tray makes its own exact shape from it). Josie: no
  // squares or rectangles; wide rooms read as octagons, tall chats as hexagons, small panels as heptagons.
  const SHAPE = {room: 'octagon', wide: 'octagon', chat: 'hexagon', tool: 'pentagon', status: 'heptagon',
                 browser: 'octagon', video: 'heptagon', image: 'hexagon', pdf: 'pentagon', text: 'pentagon', list: 'hexagon'};
  const DARK = 'linear-gradient(165deg,#15110d,#090706)';

  // id, title, group, kind, address, natural size (w x h of its screen), smallest usable size, shape.
  const PROGRAMS = [
    // conversation and collaboration
    {id: 'world_chat', title: 'World Chat', group: 'Chat & Collaboration', kind: 'page', url: '/static/world_chat.html',
     w: 440, h: 520, minW: 320, minH: 360, shape: 'chat', singleton: true},
    {id: 'pubpartner_workspace', title: 'PubPartner · Alex & Cartridges', short: 'PubPartner', group: 'Programs', kind: 'page', url: '/pubpartner',
     w: 1000, h: 640, minW: 640, minH: 440, shape: 'wide', singleton: true},
    {id: 'twoi', title: "2i Writer's Room", short: '2i', group: 'Programs', kind: 'page', url: c => c.twoIUi,
     w: 980, h: 620, minW: 640, minH: 420, shape: 'wide', singleton: true},
    {id: 'iteration_wallet', title: 'Iteration Wallet', group: 'Programs', kind: 'external', url: c => c.iterationWalletUrl,
     w: 980, h: 620, minW: 600, minH: 400, shape: 'wide', singleton: true},
    {id: 'pubpartner_chat', title: 'Character Chat', group: 'Programs', kind: 'page', url: '/pub-partner-chat',
     w: 520, h: 560, minW: 360, minH: 380, shape: 'chat', singleton: true},
    {id: 'bella_faux_pas', title: 'Bella Faux Pas Studio', short: 'Studio', group: 'Programs', kind: 'page', url: '/walk', w: 980, h: 620, minW: 600, minH: 400, shape: 'room', singleton: true},
    {id: 'care_eq', title: 'CARE / EQ & Little Mode', short: 'CARE', group: 'Programs', kind: 'page', url: '/static/foresight_care.html',
     w: 640, h: 520, minW: 440, minH: 360, shape: 'tool', singleton: true},
    // studio rooms: direct work navigation, always available beside any walkable map
    {id: 'stage', title: 'Stage', group: 'Studio Rooms', kind: 'page', url: '/static/stage.html', w: 860, h: 560, minW: 520, minH: 360, shape: 'room', singleton: true},
    {id: 'panoramic', title: '360° Panoramic', group: 'Studio Rooms', kind: 'page', url: '/static/stage_panoramic.html', w: 860, h: 560, minW: 520, minH: 360, shape: 'room', singleton: true},
    {id: 'control_room', title: 'Control Room', group: 'Studio Rooms', kind: 'page', url: '/static/control_room.html', w: 860, h: 580, minW: 560, minH: 380, shape: 'room', singleton: true},
    {id: 'studio_control', title: 'Studio Control Room', group: 'Studio Rooms', kind: 'page', url: '/static/studio_control_room.html', w: 860, h: 580, minW: 560, minH: 380, shape: 'room', singleton: true},
    {id: 'director', title: 'Director Switcher', group: 'Studio Rooms', kind: 'page', url: '/static/director_switcher.html', w: 860, h: 580, minW: 560, minH: 380, shape: 'room', singleton: true},
    {id: 'world', title: 'World', group: 'Studio Rooms', kind: 'page', url: '/static/world.html', w: 880, h: 580, minW: 520, minH: 360, shape: 'room', singleton: true},
    {id: 'pubworld_set', title: 'PubWorld Set', group: 'Studio Rooms', kind: 'page', url: '/static/pubworld_stage.html', w: 880, h: 580, minW: 520, minH: 360, shape: 'room', singleton: true},
    {id: 'bar', title: 'Bar', group: 'Studio Rooms', kind: 'page', url: '/static/bar.html', w: 780, h: 540, minW: 480, minH: 340, shape: 'room', singleton: true},
    {id: 'dressing', title: 'Dressing Room', group: 'Studio Rooms', kind: 'page', url: '/static/dressing.html', w: 780, h: 540, minW: 480, minH: 340, shape: 'room', singleton: true},
    {id: 'waiting_room', title: 'Waiting Room', group: 'Studio Rooms', kind: 'page', url: '/static/waiting_room.html', w: 720, h: 500, minW: 440, minH: 320, shape: 'room', singleton: true},
    {id: 'map', title: 'Map / Walk', group: 'Studio Rooms', kind: 'page', url: '/static/map.html', w: 780, h: 540, minW: 480, minH: 340, shape: 'room', singleton: true},
    {id:'saved_files',title:'Saved files',group:'Programs',kind:'page',url:'/static/foresight_file_shelf.html',w:680,h:500,minW:400,minH:300,shape:'wide'},
    {id:'shell',title:'Host shell',group:'Development',kind:'page',url:'/static/foresight_shell.html',w:820,h:540,minW:480,minH:320,shape:'wide'},
    // production tools
    {id: 'teleprompter', title: 'Teleprompter', group: 'Production Tools', kind: 'page', url: '/static/pubcast_teleprompter.html', w: 660, h: 480, minW: 420, minH: 300, shape: 'tool', singleton: true},
    {id: 'gallery', title: 'Gallery', group: 'Production Tools', kind: 'page', url: '/static/gallery.html', w: 660, h: 480, minW: 420, minH: 300, shape: 'tool', singleton: true},
    {id: 'analytics', title: 'Analytics', group: 'Production Tools', kind: 'page', url: '/static/analytics.html', w: 660, h: 460, minW: 420, minH: 300, shape: 'tool', singleton: true},
    {id: 'doctor', title: 'Doctor', group: 'Production Tools', kind: 'page', url: '/static/doctor.html', w: 600, h: 460, minW: 400, minH: 300, shape: 'tool', singleton: true},
    {id: 'recordings', title: 'Recordings', group: 'Production Tools', kind: 'recordings', w: 460, h: 460, minW: 320, minH: 300, shape: 'list', singleton: true},
    // live status of the services Foresight leans on
    {id: 'pubpartner_status', title: 'PubPartner Status', group: 'Status', kind: 'status', service: 'pubpartner', w: 380, h: 300, minW: 300, minH: 240, shape: 'status', singleton: true},
    {id: 'twoi_status', title: '2i Bridge Status', group: 'Status', kind: 'status', service: 'twoi', w: 380, h: 300, minW: 300, minH: 240, shape: 'status', singleton: true},
    // made per use: web pages, videos, files, chats
    {id: 'browser', title: 'Web Browser', group: 'Web & Media', kind: 'browser', w: 900, h: 600, minW: 480, minH: 320, shape: 'browser'},
    {id: 'video', title: 'Video', group: 'Web & Media', kind: 'video', w: 720, h: 420, minW: 320, minH: 190, shape: 'video', minScale: 0.5},
    {id: 'file', title: 'File', group: 'Web & Media', kind: 'file', w: 640, h: 480, minW: 260, minH: 200, shape: 'image', minScale: 0.5},
    {id: 'chat', title: 'Chat', group: 'Chat & Collaboration', kind: 'chat', w: 440, h: 520, minW: 320, minH: 360, shape: 'chat'},
  ];
  const byId = id => PROGRAMS.find(p => p.id === id) || null;

  // ---------------------------------------------------------------- small helpers
  const safeLabel = (v, fallback) => { const s = String(v || '').replace(/[<>]/g, '').trim(); return (s || fallback || '').slice(0, 80); };
  function el(tag, attrs, ...kids){
    const e = document.createElement(tag);
    for(const [k, v] of Object.entries(attrs || {})){ if(k === 'style') e.style.cssText = v; else if(k === 'class') e.className = v; else if(k.startsWith('on')) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v); }
    for(const k of kids){ if(k == null) continue; e.appendChild(typeof k === 'string' ? document.createTextNode(k) : k); }
    return e;
  }
  // Only http(s) pages may be opened. A bare host gets https://; a path stays on this site. Anything else
  // (javascript:, data:, file:, blob:) is refused.
  function normalizeAddress(raw){
    let s = String(raw || '').trim();
    if(!s) throw new Error('Type a web address');
    if(s.startsWith('/')) return new URL(s, location.origin).href;
    if(!/^[a-z][a-z0-9+.-]*:/i.test(s)) s = 'https://' + s;
    let u; try{ u = new URL(s); }catch(e){ throw new Error('That is not a valid web address'); }
    if(u.protocol !== 'http:' && u.protocol !== 'https:') throw new Error('Only http and https addresses can be opened');
    if(!u.hostname) throw new Error('That address has no site name');
    return u.href;
  }
  function addressLabel(address){
    if(!address) return 'Web Browser';
    try{ const u = new URL(address); return u.origin === location.origin ? 'PubCast · ' + u.pathname : u.hostname.replace(/^www\./, ''); }
    catch(e){ return 'Web Browser'; }
  }
  function fileKind(name, mime){
    mime = mime || '';
    if(mime.startsWith('video/') || mime.startsWith('audio/') || /\.(mp4|webm|mov|m4v|ogv|mp3|wav|m4a|ogg|flac)$/i.test(name)) return 'video';
    if(mime.startsWith('image/') || /\.(png|jpe?g|gif|webp|bmp|svg|avif)$/i.test(name)) return 'image';
    if(mime === 'application/pdf' || /\.pdf$/i.test(name)) return 'pdf';
    if(mime.startsWith('text/') || /\.(txt|md|csv|json|log|py|js|ts|jsx|tsx|xml|html|css|yaml|yml|toml|ini|cfg|sh|ps1|sql|c|cpp|h|hpp|rs|docx|odt|pptx|xlsx|2i)$/i.test(name)) return 'text';
    return null;
  }
  // A cross-origin server cannot be inspected from here, but a no-cors request resolves when the server answers
  // and rejects when nothing is listening.
  async function reachable(url, ms){
    const ctl = new AbortController(), timer = setTimeout(() => ctl.abort(), ms || 2500);
    try{ await fetch(url, {mode: 'no-cors', cache: 'no-store', signal: ctl.signal}); return true; }
    catch(e){ return false; }
    finally{ clearTimeout(timer); }
  }

  // ---------------------------------------------------------------- the provider
  function create(opts){
    opts = opts || {};
    const config = Object.assign({}, DEFAULT_CONFIG, root.FORESIGHT_CONFIG || {}, opts.config || {});
    const toast = opts.toast || (t => console.log(t));
    let counter = null;
    const frames = new Map();     // iframe window -> content, for messages from pages inside trays
    const files = new WeakMap();  // content -> picked File; durable originals live in ForesightFiles
    const urlOf = p => typeof p.url === 'function' ? p.url(config) : p.url;

    function programFor(type){ return byId(type); }
    // A panel with a title, a few lines and buttons: used for "not running", "choose the file again" and errors.
    function panel(body, title, lines, actions){
      body.innerHTML = '';
      const wrap = el('div', {class: 'fp-panel'}, el('h3', {}, title));
      for(const l of [].concat(lines || [])) wrap.appendChild(typeof l === 'string' ? el('p', {}, l) : l);
      const row = el('div', {class: 'fp-acts'});
      for(const [label, fn] of actions || []) row.appendChild(el('button', {class: 'fp-btn', onclick: e => { e.stopPropagation(); fn(); }}, label));
      wrap.appendChild(row); body.appendChild(wrap);
      return wrap;
    }
    function frameFor(c, body, src, attrs){
      const f = el('iframe', Object.assign({allow: 'microphone; camera; autoplay; clipboard-read; clipboard-write; fullscreen', loading: 'eager'}, attrs || {}));
      c.frameLoaded=false;c.appReady=false;
      if(['twoi','file'].includes(c.type)){
        c.sessionNonce=crypto.randomUUID();
        const url=new URL(src,location.origin);
        if(url.origin!==location.origin)throw Error('2i must be hosted on the authenticated Reach origin');
        url.searchParams.set('foresightSession',c.sessionNonce);
        src=url.pathname+url.search+url.hash;
      }
      c.readyPromise=new Promise(resolve=>{c.resolveReady=resolve});
      f.addEventListener('load', () => {
        if(c.frame!==f||c.stopped)return;
        c.frameLoaded=true;
        if(counter?.refreshActivity)counter.refreshActivity();
      });
      c.frame=f;
      // Register the WindowProxy before the embedded script can report ready.
      // Origin is also checked for every incoming command and acknowledgement.
      f.src=src;body.appendChild(f);
      if(f.contentWindow)frames.set(f.contentWindow,c);
      return f;
    }

    // --- what each content needs from its tray
    function describe(type, data){
      const p = programFor(type); if(!p) return null;
      data = data || {};
      let title = p.title, shape = p.shape, ink = 'light', bg = DARK;
      if(type === 'browser') title = data.address ? 'Browser · ' + addressLabel(data.address) : 'Web Browser';
      if(type === 'video') title = safeLabel(data.name, 'Video');
      if(type === 'chat') title = safeLabel(data.title, 'Chat');
      if(type === 'file'){ const k = fileKind(data.name || '', data.mime || ''); title = safeLabel(data.name, 'File'); shape = k || 'image'; if(k === 'text'){ ink = 'light'; } }
      if(type === 'video' || type === 'file') bg = '#050403';
      const editor=type==='file'&&!['image','video'].includes(fileKind(data.name||'',data.mime||''));
      return {title, family: SHAPE[shape] || 'pentagon', w: editor?980:p.w, h: editor?620:p.h, minW: editor?640:p.minW, minH: editor?420:p.minH, minScale: p.minScale || 0.7, ink, bg};
    }

    // --- putting a content on its screen
    function mount(c, host){
      const p = programFor(c.type); if(!p) throw new Error('Unknown program: ' + c.type);
      c.data = c.data || {};
      const body = host.body; body.classList.add('fp-body');
      c.host = host;
      if(p.kind === 'page') frameFor(c, body, urlOf(p)+(c.type==='shell'&&c.data.scriptId?'?script='+encodeURIComponent(c.data.scriptId):''));
      else if(p.kind === 'external') mountExternal(c, body, p);
      else if(p.kind === 'status') mountStatus(c, body, p);
      else if(p.kind === 'browser') mountBrowser(c, body);
      else if(p.kind === 'video') mountVideo(c, body);
      else if(p.kind === 'file') mountFile(c, body);
      else if(p.kind === 'recordings') mountRecordings(c, body);
      else if(p.kind === 'chat') frameFor(c, body, '/general-chat?conversation=' + encodeURIComponent(c.data.conversationId || ''));
      return {destroy: () => release(c)};
    }
    function release(c){
      for(const [id,pending] of fileCommands){
        if(pending.content===c){
          clearTimeout(pending.timer);fileCommands.delete(id);
          pending.reject(Error('The application closed before its operation completed'));
        }
      }
      if(c.objectUrl){ URL.revokeObjectURL(c.objectUrl); c.objectUrl = null; }
      if(c.frame){ try{ frames.delete(c.frame.contentWindow); }catch(e){} try{ c.frame.src = 'about:blank'; }catch(e){} c.frame = null; }
      c.appReady=false;
      if(c.resolveReady){c.resolveReady();c.resolveReady=null}
      const v = c.body && c.body.querySelector('video'); if(v){ v.pause(); v.removeAttribute('src'); v.load(); }
      if(c.abort){ c.abort.abort(); c.abort = null; }
      if(c.poll){ clearTimeout(c.poll); c.poll = null; }
      c.stopped = true;
    }

    async function mountExternal(c, body, p){
      const url = urlOf(p);
      panel(body, p.title, 'Checking whether ' + p.title + ' is running…');
      const up = await reachable(url);
      if(c.stopped) return;
      if(!up){
        const code1 = el('code', {}, '.\\START_ITERATION_WALLET.ps1'), code2 = el('code', {}, url);
        panel(body, p.title + ' is not running', [
          'It is a separate program with its own server. Start it on this computer, then press Retry.',
          el('p', {}, 'In PowerShell, from the Iteration Wallet folder: ', code1),
          el('p', {}, 'Expected address: ', code2)],
          [['Retry', () => mountExternal(c, body, p)], ['Open in a new window', () => window.open(url, '_blank', 'noopener')]]);
        return;
      }
      body.innerHTML = '';
      frameFor(c, body, url, {allow: 'clipboard-read; clipboard-write'});
    }

    function mountStatus(c, body, p){
      body.innerHTML = '';
      const wrap = el('div', {class: 'fp-status'}, el('h3', {}, p.title), el('div', {class: 'fp-sub'}, 'Live status, asked of the real service every 4 seconds.'));
      const rows = el('div', {class: 'fp-rows'}, 'Connecting…'); wrap.appendChild(rows); body.appendChild(wrap);
      const url = p.service === 'pubpartner' ? config.pubpartnerBase + config.pubpartnerStatusPath : config.twoIBase + '/health';
      const row = (k, v, cls) => el('div', {class: 'fp-row'}, el('span', {}, k), el('span', cls ? {class: cls} : {}, String(v == null ? '—' : v)));
      async function tick(){
        if(c.stopped) return;
        try{
          const res = await fetch(url, {mode: 'cors'}); if(!res.ok) throw new Error('HTTP ' + res.status);
          const d = await res.json(); rows.innerHTML = '';
          if(p.service === 'pubpartner'){
            const list = v => Array.isArray(v) ? v.join(', ') : (v || '—');
            const vessel = d.vessel && typeof d.vessel === 'object' ? (d.vessel.status || d.vessel.state || 'mounted') : (d.vessel ? 'mounted' : '—');
            rows.append(row('Status', d.ok === false ? 'degraded' : (d.spine || d.status || 'ready'), 'fp-pill ok'), row('Spine', d.spine || d.service),
              row('Protocols', list(d.protocols || d.protocol)), row('Providers', list(d.providers)), row('Vessel', vessel));
          } else {
            const env = d.environment || {}, svc = d.services || {};
            rows.append(row('Status', d.status, 'fp-pill ok'), row('Service', d.service), row('Uptime', d.uptime != null ? d.uptime + 's' : null),
              row('Node', env.node_version), row('Characters', svc.character_count), row('Optional 2i utilities', svc.legacy_2i_utilities));
          }
        }catch(err){
          rows.innerHTML = '';
          rows.append(row('Status', 'unreachable', 'fp-pill bad'),
            el('div', {class: 'fp-err'}, String(err && err.message || err) + '. Is the ' + (p.service === 'pubpartner' ? 'Reach PubPartner spine' : 'Foresight character bridge') + ' running?'));
        }
        if(!c.stopped) c.poll = setTimeout(tick, 4000);
      }
      tick();
    }

    function mountBrowser(c, body){
      body.innerHTML = '';
      const addr = el('input', {class: 'fp-addr', type: 'text', spellcheck: 'false', autocomplete: 'off', placeholder: 'Type a web address and press Enter', 'aria-label': 'Web address'});
      const bar = el('div', {class: 'fp-webbar'},
        el('button', {class: 'fp-btn small', title: 'Reload', onclick: () => { if(c.data.address) frame.src = c.data.address; }}, '↻'), addr,
        el('button', {class: 'fp-btn small', title: 'Go', onclick: () => go(addr.value)}, 'Go'),
        el('button', {class: 'fp-btn small', title: 'Open in a normal browser window', onclick: () => { try{ window.open(normalizeAddress(c.data.address || addr.value), '_blank', 'noopener'); }catch(err){ toast(err.message); } }}, '↗'));
      const frame = el('iframe', {sandbox: 'allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox allow-downloads allow-modals', referrerpolicy: 'strict-origin-when-cross-origin'});
      const note = el('div', {class: 'fp-note'}, 'Some sites refuse to be shown inside another page and stay blank here. Use ↗ to open those in a normal browser window.');
      body.append(el('div', {class: 'fp-web'}, bar, frame, note));
      c.frame = frame;
      function go(raw){
        let href; try{ href = normalizeAddress(raw); }catch(err){ toast(err.message); addr.focus(); return; }
        c.data.address = href; addr.value = href; frame.src = href;
        c.host.setTitle('Browser · ' + addressLabel(href)); c.host.changed();
      }
      addr.addEventListener('keydown', e => { if(e.key === 'Enter'){ e.preventDefault(); go(addr.value); } });
      if(c.data.address){ addr.value = c.data.address; frame.src = c.data.address; } else setTimeout(() => addr.focus(), 60);
    }

    async function mountVideo(c, body){
      const d = c.data;
      let file = files.get(c);
      if(d.type==='file'&&d.fileId){
        try{
          if(file&&!await ForesightFiles.record(d.fileId))await ForesightFiles.record(d.fileId,{id:d.fileId,name:file.name,mime:file.type,original:file,updated:Date.now()});
          if(!file)file=(await ForesightFiles.record(d.fileId))?.original;
          if(file)files.set(c,file);
        }catch(error){panel(body,'Media storage failed',error.message);return;}
        if(c.stopped)return;
      }
      if(d.type === 'file' && !file){
        panel(body, 'Choose the video again', ['Browsers do not keep access to files from your computer after the page reloads. Choose ' + (d.name || 'the file') + ' again to keep watching.'],
          [['Choose file…', () => pickInto(c)]]);
        return;
      }
      body.innerHTML = '';
      const video = el('video', {controls: '', playsinline: '', preload: 'metadata', class: 'fp-video'});
      video.addEventListener('error', () => {
        const code = video.error ? video.error.code : 0;
        panel(body, 'Video unavailable', code === 4 ? 'This browser cannot play this file or format.' : code === 2 ? 'The video stopped loading because of a network error.' : 'The video could not be played.',
          [['Choose another file…', () => pickInto(c)]]);
      });
      body.appendChild(video);
      if(d.type === 'file'){ if(c.objectUrl) URL.revokeObjectURL(c.objectUrl); c.objectUrl = URL.createObjectURL(file); video.src = c.objectUrl; }
      else if(d.type === 'url') video.src = d.url;
      else if(d.type === 'vod') loadRecording(c, body, video);
    }
    // Recordings are protected: a <video src> cannot send the Reach sign-in, so the file is fetched (signed in) and
    // played from memory.
    async function loadRecording(c, body, video){
      const ctl = new AbortController(); c.abort = ctl;
      try{
        const res = await fetch(c.data.url, {signal: ctl.signal}); if(!res.ok) throw new Error('HTTP ' + res.status);
        const blob = await res.blob(); if(c.stopped) return;
        if(c.objectUrl) URL.revokeObjectURL(c.objectUrl);
        c.objectUrl = URL.createObjectURL(blob); video.src = c.objectUrl;
      }catch(err){
        if(err.name === 'AbortError') return;
        panel(body, 'Recording unavailable', 'Could not load this recording: ' + (err.message || err), [['Retry', () => mountVideo(c, body)]]);
      }finally{ c.abort = null; }
    }

    async function mountFile(c, body){
      const file=files.get(c);
      if(!c.data.fileId){
        if(!file){panel(body,'Choose the file again','No saved file bytes found.',[['Choose file…',()=>pickInto(c)]]);return;}
        c.data.fileId=crypto.randomUUID();c.host.changed();
      }
      try{
        if(file&&!await ForesightFiles.record(c.data.fileId))await ForesightFiles.record(c.data.fileId,{id:c.data.fileId,name:file.name,mime:file.type,original:file,updated:Date.now()});
        if(c.stopped)return;
        body.replaceChildren();
        frameFor(c,body,'/writers-room?file='+encodeURIComponent(c.data.fileId),{title:'2i · '+(c.data.name||'File')});
      }catch(error){panel(body,'File storage failed',error.message,[...(file?[['Download original',()=>ForesightFiles.download(file.name,file)]]:[]),['Choose file…',()=>pickInto(c)]]);}
    }
    const fileCommands=new Map();
    async function fileCommand(c,command,payload){
      if(!c.frame||c.stopped)throw Error('2i editor is not open');
      const frame=c.frame;
      if(!c.appReady){
        await new Promise((resolve,reject)=>{
          const timer=setTimeout(()=>reject(Error('2i did not confirm readiness within the deadline')),15000);
          c.readyPromise.then(()=>{clearTimeout(timer);resolve()},error=>{clearTimeout(timer);reject(error)});
        });
      }
      if(c.frame!==frame||c.stopped||!c.appReady)throw Error('2i editor was replaced or did not initialize');
      return new Promise((resolve,reject)=>{
        const requestId=crypto.randomUUID();
        const timer=setTimeout(()=>{fileCommands.delete(requestId);reject(Error('2i did not acknowledge '+command+' within the deadline'))},15000);
        fileCommands.set(requestId,{resolve,reject,timer,source:frame.contentWindow,content:c});
        frame.contentWindow.postMessage({type:'foresight:file-command',version:1,
          fileId:c.data.fileId,requestId,command,payload,sessionNonce:c.sessionNonce},location.origin);
      });
    }
    addEventListener('message',e=>{
      if(e.origin!==location.origin||e.data?.type!=='foresight:file-result')return;
      const pending=fileCommands.get(e.data.requestId);
      if(!pending||pending.source!==e.source||e.data.sessionNonce!==pending.content.sessionNonce)return;
      clearTimeout(pending.timer);fileCommands.delete(e.data.requestId);
      if(e.data.error)pending.reject(Error(e.data.error));else pending.resolve(e.data.result);
    });
    function supportsLifecycle(c){return !!c&&['twoi','file'].includes(c.type)}
    async function setActivityPolicy(c,mode,presentation){
      if(!supportsLifecycle(c))return {supported:false,mode:'uncontrolled',reason:'Application does not provide cooperative activity controls'};
      const response=await fileCommand(c,'activity',{mode,presentation});
      if(response?.mode!==mode)throw Error('2i did not confirm the requested activity policy');
      return {supported:true,...response};
    }
    async function getActivityStatus(c){
      if(!supportsLifecycle(c))return {supported:false,reason:'Application has no status adapter'};
      return {supported:true,...await fileCommand(c,'status')};
    }
    async function prepareClose(c){
      if(!supportsLifecycle(c))return {canClose:false,reason:'This application cannot confirm whether its work is saved',supported:false};
      const response=await fileCommand(c,'prepare-close');
      if(!response||typeof response.canClose!=='boolean')throw Error('2i close handshake did not return a valid decision');
      return {...response,supported:true};
    }

    async function mountRecordings(c, body){
      panel(body, 'Recordings', 'Loading recordings…');
      try{
        const res = await fetch('/api/vod'); if(!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json(); if(c.stopped) return;
        const list = (data.files || []).filter(f => /\.(mp4|webm|mov|m4v|ogg|ogv|mp3|wav|m4a)$/i.test(f.name || ''));
        if(!list.length){ panel(body, 'Recordings', 'No playable recordings yet. Recordings made in the studio appear here.', [['Refresh', () => mountRecordings(c, body)]]); return; }
        const wrap = panel(body, 'Recordings', list.length + ' playable recording' + (list.length === 1 ? '' : 's') + '. Click one to open it in its own tray.', [['Refresh', () => mountRecordings(c, body)]]);
        const ul = el('div', {class: 'fp-list'});
        for(const f of list){
          const mb = f.size_bytes ? (f.size_bytes/1048576).toFixed(1) + ' MB' : '';
          ul.appendChild(el('button', {class: 'fp-item', onclick: () => openProgram('video', {type: 'vod', url: f.url, name: f.name})},
            el('span', {}, f.name), el('span', {class: 'fp-meta'}, [mb, f.ended_at ? String(f.ended_at).slice(0, 16).replace('T', ' ') : ''].filter(Boolean).join(' · '))));
        }
        wrap.appendChild(ul);
      }catch(err){
        if(c.stopped) return;
        panel(body, 'Recordings unavailable', 'Could not list recordings: ' + (err.message || err), [['Retry', () => mountRecordings(c, body)]]);
      }
    }

    // A file picked to go into an existing content (one asking for its file again).
    function pickInto(c){
      const input = el('input', {type: 'file', accept: '*/*'});
      input.addEventListener('change', async () => {
        const f = input.files && input.files[0]; if(!f) return;
        let r;try{r=await resolveFile(f)}catch(error){toast(error.message);return;} if(!r){ toast('This file type cannot be shown in a tray: ' + f.name); return; }
        if(c.tray && counter){ counter.importInto(c.tray, r.type, r.data); }
      });
      input.click();
    }

    // --- route a picked file; mount persists its original before opening the editor.
    const pendingFiles = new Map();   // data object -> File, until the content is made from it
    function fromFile(file){
      const kind = fileKind(file.name, file.type);
      // Unknown types still retain their original and try the strict text fallback.

      const data = {name:file.name,mime:file.type||'',fileId:crypto.randomUUID()};
      pendingFiles.set(data, file);
      if(kind==='video')data.type='file';
      return {type:kind==='video'?'video':'file',data};
    }
    async function resolveFile(file){
      if(/\.url$/i.test(file.name)&&file.size<8192){
        const text=await file.text(),match=text.match(/^URL=(.+)$/m);
        if(text.includes('[InternetShortcut]')&&match)return {type:'browser',data:{address:normalizeAddress(match[1].trim())}};
      }
      if(/\.json$/i.test(file.name)&&file.size<5*1024*1024){
        let value;try{value=JSON.parse(await file.text())}catch{}
        if(value?.kind==='foresight.content'){
          const type=value.program||value.type;
          if(!byId(type))throw Error('This exported tray names an unavailable program: '+String(type));
          return {type,data:value.data&&typeof value.data==='object'?value.data:{}};
        }
      }
      return fromFile(file);
    }
    // claim a picked file for the content made from it (mount runs right after makeContent)
    const mountInner = mount;
    function mountWithFile(c, host){
      if(pendingFiles.has(c.data)){ files.set(c, pendingFiles.get(c.data)); pendingFiles.delete(c.data); }
      return mountInner(c, host);
    }

    // --- what is kept across reloads: the content's own data, never a file or a live object
    function serialize(c){
      const out = Object.assign({}, c.state || {});
      return out;
    }

    // --- Export: the content as a file to keep
    async function exportContent(c){
      const p = programFor(c.type), file = files.get(c);
      if(c.type==='twoi'||c.type==='file'&&c.data.fileId)return fileCommand(c,'export');
      if(file) return {name: file.name, data: file, type: file.type};
      if(c.type === 'browser' && c.data.address){
        // a Windows internet shortcut: double-click it to open the page
        return {name: safeLabel(addressLabel(c.data.address), 'page') + '.url', data: '[InternetShortcut]\r\nURL=' + c.data.address + '\r\n', type: 'application/internet-shortcut'};
      }
      if(c.type === 'video' && c.data.type !== 'file' && c.objectUrl){
        const blob = await fetch(c.objectUrl).then(r => r.blob());
        return {name: c.data.name || 'video', data: blob, type: blob.type};
      }
      return {name: safeLabel(c.title || (p && p.title), 'tray') + '.json', type: 'application/json',
        data: JSON.stringify({kind: 'foresight.content', program: c.type, title: c.title, address: p && p.url ? urlOf(p) : undefined,
          data: Object.assign({}, c.data), exported: new Date().toISOString()}, null, 2)};
    }

    // --- the picker (New blade, File > Open, a tray's Import…)
    function catalog(){
      const items = [];
      const groups = ['Programs', 'Chat & Collaboration', 'Studio Rooms', 'Production Tools', 'Development', 'Status'];
      for(const g of groups) for(const p of PROGRAMS.filter(x => x.group === g && !['browser', 'video', 'file', 'chat'].includes(x.id))){
        items.push({type: p.id, title: p.title, group: g === 'Chat & Collaboration' ? 'Programs' : g, hint: isOpen(p.id) ? 'Already open: brings it forward' : ''});
      }
      items.push({type: 'browser', title: 'Web browser', group: 'Trays', hint: 'Any web address, in a tray'});
      items.push({title: 'Video from a link…', group: 'Trays', hint: 'A direct link to a video file', run: askVideoUrl});
      items.push({title: 'New chat', group: 'Trays', hint: 'A new conversation in a tray', run: newChat});
      return items;
    }
    function isOpen(id){ return !!(counter && counter.trays.some(t => t.stack.some(c => c.type === id))); }
    function trayWith(id){ return counter ? counter.trays.find(t => t.stack.some(c => c.type === id)) : null; }
    // a singleton already open somewhere is brought forward (opened from the fan, brought back, shown) instead
    function bringForward(t, id){
      const k = t.stack.findIndex(c => c.type === id);
      if(t.closed) counter.reopen(t); else if(t.parked) counter.unpark(t); else counter.select(t);
      if(k >= 0 && t.active !== k && counter.show) counter.show(t, k);
      return t;
    }
    function beforeOpen(type, data, tray){
      const p = programFor(type);
      if(type==='file'&&data?.fileId&&counter){const existing=counter.trays.find(t=>t.stack.some(c=>c.type==='file'&&c.data?.fileId===data.fileId));if(existing){bringForward(existing,type);return false;}}
      if(p && p.singleton){ const t = trayWith(type); if(t){ bringForward(t, type); toast(p.title + ' is already open in its own tray'); return false; } }
      return true;
    }
    function openProgram(id, data){
      if(!counter) return null;
      if(!beforeOpen(id, data, null)) return null;
      return counter.open(id, data || {});
    }

    async function askVideoUrl(){
      const raw = opts.ask ? await opts.ask({title: 'Open a video from a link', sub: 'A direct link to a video file (for example .mp4 or .webm). Pages like YouTube are web pages, not video files: open those in a web browser tray.',
        placeholder: 'https://…/video.mp4', validate: normalizeAddress}) : prompt('Video link');
      if(raw == null) return;
      const href = normalizeAddress(raw);
      openProgram('video', {type: 'url', url: href, name: decodeURIComponent(new URL(href).pathname.split('/').pop() || 'Video')});
    }
    async function newChat(){
      const title = 'Chat · ' + new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
      try{
        const res = await fetch('/api/conversations', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({title})});
        if(!res.ok) throw new Error('HTTP ' + res.status);
        const d = await res.json();
        if(!d || typeof d.conversation_id !== 'string' || !d.conversation_id.trim()){
          throw new Error('archive returned no conversation identifier');
        }
        openProgram('chat', {conversationId: d.conversation_id, title});
        return true;
      }catch(err){
        // Never open an apparently writable conversation after the canonical
        // archive has rejected or failed creation. A fallback here can split
        // conversation authority or lose text during an outage.
        toast('Cannot create conversation: ' + (err.message || String(err)));
        return false;
      }
    }

    // --- reload what a tray shows
    async function reload(c){
      const p = programFor(c.type); if(!p || c.stopped) return false;
      // Reload is a destructive navigation for embedded editors. Do not bypass
      // their cooperative save/close handshake or reuse the old frame nonce.
      if(supportsLifecycle(c)){
        try{
          const decision=await prepareClose(c);
          if(!decision.canClose){
            toast(decision.reason || '2i cannot safely reload while work is pending');
            return false;
          }
        }catch(error){
          toast('2i reload cancelled: ' + (error.message || error));
          return false;
        }
        if(c.stopped || !c.frame) return false;
        // An old command reply or readiness notification must not authorize
        // commands against the new document/frame session.
        for(const [id,pending] of fileCommands){
          if(pending.content===c){
            clearTimeout(pending.timer);fileCommands.delete(id);
            pending.reject(Error('2i reloaded before its operation completed'));
          }
        }
        c.frameLoaded=false;c.appReady=false;c.activityRequest=null;
        c.readyPromise=new Promise(resolve=>{c.resolveReady=resolve});
        c.sessionNonce=crypto.randomUUID();
        const url=new URL(c.type==='file'
          ? '/writers-room?file='+encodeURIComponent(c.data.fileId)
          : urlOf(p),location.origin);
        url.searchParams.set('foresightSession',c.sessionNonce);
        c.frame.src=url.pathname+url.search+url.hash;
      }
      else if(p.kind === 'page' && c.frame) c.frame.src=urlOf(p);
      else if(p.kind === 'chat' && c.frame) c.frame.src=c.frame.src;
      else if(p.kind === 'browser' && c.data.address && c.frame) c.frame.src=c.data.address;
      else if(p.kind === 'external') mountExternal(c,c.body,p);
      else if(p.kind === 'recordings') mountRecordings(c,c.body);
      else if(p.kind === 'video') mountVideo(c,c.body);
      else {toast('This tray refreshes itself');return false;}
      toast('Reloaded '+c.title);
      return true;
    }

    // --- messages from the pages inside trays (as the earlier Foresight page took them)
    addEventListener('message', e => {
      // A known WindowProxy can navigate to another origin. Source identity
      // alone must not authorize that new page to issue host commands.
      if(e.origin !== location.origin) return;
      const c = frames.get(e.source); if(!c || !e.data || typeof e.data !== 'object') return;
      if(e.data.type==='foresight:app-status'&&supportsLifecycle(c)){
        if(e.data.sessionNonce!==c.sessionNonce)return;
        if(c.type==='file'&&e.data.fileId!==c.data.fileId)return;
        if(e.data.version!==1)return;
        c.activityAcknowledgment={...(c.activityAcknowledgment||{}),
          dirty:!!e.data.dirty,saving:!!e.data.saving,protected:!!e.data.protected};
        return;
      }
      if(e.data.type==='foresight:file-ready'&&supportsLifecycle(c)){
        if(e.data.sessionNonce!==c.sessionNonce||e.data.version!==1)return;
        if(c.type==='file'&&e.data.fileId!==c.data.fileId)return;
        c.appReady=true;
        if(c.resolveReady){c.resolveReady();c.resolveReady=null}
        if(counter?.refreshActivity)counter.refreshActivity();
        return;
      }
      if(e.data.type==='foresight:run-python'&&c.type==='file'&&e.data.fileId===c.data.fileId){openProgram('shell',{scriptId:e.data.fileId});return;}
      if(e.data.type==='foresight:open-file'&&/^[a-f0-9-]{36}$/.test(e.data.fileId)){openProgram('file',{fileId:e.data.fileId,name:safeLabel(e.data.name,'File')});return;}
      if(e.data.type==='foresight:file-renamed'&&c.type==='file'&&e.data.fileId===c.data.fileId){c.data.name=safeLabel(e.data.name,'File');c.host.setTitle(c.data.name);c.host.changed();return;}
      if(e.data.type==='foresight:file-selected'&&c.type==='file'&&e.data.previousFileId===c.data.fileId&&/^[a-f0-9-]{36}$/.test(e.data.fileId)){
          // The same WindowProxy will navigate to a different document. Its
          // previous Ready confirmation must not authorize a fresh Save.
          c.appReady=false;c.frameLoaded=false;c.activityRequest=null;
          c.readyPromise=new Promise(resolve=>{c.resolveReady=resolve});
          c.data.fileId=e.data.fileId;c.data.name=safeLabel(e.data.name,'File');c.host.setTitle(c.data.name);c.host.changed();return;}
      if(e.data.type === 'foresight:new-chat'){ newChat(); return; }
      if(e.data.type === 'foresight:open-conversation' && e.data.conversationId){ openProgram('chat', {conversationId: String(e.data.conversationId), title: safeLabel(e.data.title, 'Chat')}); return; }
      if(e.data.type === 'foresight:portal-conversation' && c.type === 'chat' && e.data.conversationId){
        c.data.conversationId = String(e.data.conversationId); c.data.title = safeLabel(e.data.title, c.title);
        c.host.setTitle(c.data.title); c.host.changed();
      }
    });

    const provider = {catalog,describe,mount:mountWithFile,serialize,exportContent,fromFile,resolveFile,beforeOpen,
      save:c=>supportsLifecycle(c)?fileCommand(c,'save'):false,
      setActivityPolicy,getActivityStatus,prepareClose,
      supportsLifecycle};
    return {
      provider, programs: PROGRAMS, config, normalizeAddress, reload, newChat, askVideoUrl,
      bind(c){ counter = c; },
      open: openProgram,
      autostart(){ for(const p of PROGRAMS) if(p.autostart && !isOpen(p.id)) openProgram(p.id, {}); },
    };
  }

  root.ForesightPrograms = {create, PROGRAMS, fileKind, normalizeAddress, addressLabel, version: 1};
})(window);

`````

## main.py

SHA-256: a6a2f2b85c9fa1d826db9bb6861cac77fbd858a2480486ed4760edf45324b2a0

`````text
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
            camera_shutdown_error = None
            if rearmed_camera_broadcast is not None:
                try:
                    await rearmed_camera_broadcast.stop()
                except TimeoutError as exc:
                    camera_shutdown_error = exc
                    logger.error("Camera broadcast shutdown incomplete; continuing other cleanup", exc_info=True)
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
            if camera_shutdown_error is not None:
                raise camera_shutdown_error
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
    camera_shutdown_error = None
    if _camera_broadcast is not None:
        try:
            await _camera_broadcast.stop()
        except TimeoutError as exc:
            camera_shutdown_error = exc
            logger.error("Camera broadcast shutdown incomplete; continuing other cleanup", exc_info=True)
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
    if camera_shutdown_error is not None:
        raise camera_shutdown_error
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





`````

## package.json

SHA-256: c75e901ad164393b0554fdf6af9c5645567957d8524d6cd397eb703b7adea023

`````text
{
  "name": "pubcast-reach-dev-tests",
  "private": true,
  "version": "0.0.0",
  "description": "Development/test-only Node dependencies for the PubCast Reach source tree.",
  "engines": {
    "node": ">=16"
  },
  "scripts": {
    "test:editor": "node tests/test_reach_editor.cjs",
    "test:reader": "node tests/test_reader.cjs",
    "test:node": "node --test tests/test_avatar_glb_motion_consumer_node.js tests/test_program_audio_runtime_node.js tests/test_reach_editor.cjs tests/test_reader.cjs tests/test_studio_console_hotspots_node.js tests/test_voxel_block_preview_client_node.js tests/test_switcher_keyboard_node.js tests/test_twoi_connection_storage_node.js"
  },
  "devDependencies": {
    "jsdom": "26.1.0"
  }
}

`````

## modules/camera_broadcast.py

SHA-256: 0826a43675a2b1f6120db25cbd14d885c554b518752d4add7a164adc2cbbc201

`````text
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

`````

## static/stage_3d.html

SHA-256: da3b5b3e734cabc3d2b60fb13d4b38bafd293a6f7a232d9d4eb1737105186e07

`````text
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PubCast AI — 3D Studio (Experimental)</title>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Courier+Prime:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --gold:rgba(212,168,75,1);--gold-dim:rgba(212,168,75,0.18);
  --teal:#6dd6c7;--cream:#e8dfc8;--ink:#0d0b09;
  --amber:#e5c17e;--warm-mid:#a09070;--red-rec:#ff2222;
}
html,body{width:100%;height:100%;overflow:hidden;background:var(--ink)}
body{font-family:'Courier Prime',monospace;color:var(--cream)}
#stage-canvas{position:fixed;inset:0;z-index:0}

/* Experimental banner */
.exp-banner{
  position:fixed;top:0;left:50%;transform:translateX(-50%);z-index:30;
  background:rgba(10,8,6,0.9);border:1px solid rgba(255,34,34,0.3);
  border-top:none;padding:3px 16px;
  font-family:'Cinzel',serif;font-size:0.5rem;letter-spacing:3px;
  color:rgba(255,34,34,0.6);text-transform:uppercase;
}
.back-badge{
  position:fixed;top:10px;left:14px;z-index:30;
  background:rgba(10,8,6,0.85);border:1px solid var(--gold-dim);
  padding:5px 12px;font-family:'Cinzel',serif;font-size:0.52rem;
  letter-spacing:2px;color:rgba(212,168,75,0.5);cursor:pointer;
  transition:all .2s;text-decoration:none;display:block;
  backdrop-filter:blur(4px);
}
.back-badge:hover{border-color:var(--amber);color:var(--amber)}

.chat-panel{
  position:fixed;right:0;top:0;bottom:80px;width:300px;z-index:20;
  background:rgba(10,8,6,0.88);border-left:1px solid var(--gold-dim);
  display:flex;flex-direction:column;backdrop-filter:blur(8px);
}
.chat-header{
  padding:10px 14px;border-bottom:1px solid var(--gold-dim);
  font-family:'Cinzel',serif;font-size:0.65rem;font-weight:700;
  letter-spacing:4px;color:var(--amber);text-transform:uppercase;
  display:flex;align-items:center;gap:8px;
}
.chat-header-dot{width:5px;height:5px;border-radius:50%;background:var(--teal);box-shadow:0 0 6px var(--teal);animation:led-pulse 2s ease-in-out infinite}
@keyframes led-pulse{0%,100%{opacity:.5}50%{opacity:1}}
.chat-messages{flex:1;overflow-y:auto;padding:8px 10px;font-size:.72rem;line-height:1.6;scrollbar-width:thin;scrollbar-color:rgba(212,168,75,.2) transparent}
.chat-msg{margin-bottom:5px}
.chat-msg .user{color:var(--teal);font-weight:700}
.chat-msg .bot{color:var(--amber);font-weight:700}
.chat-msg .text{color:var(--warm-mid)}
.chat-input-bar{display:flex;gap:4px;padding:8px;border-top:1px solid var(--gold-dim)}
.chat-input{flex:1;background:rgba(255,255,255,.04);border:1px solid var(--gold-dim);color:var(--cream);padding:7px 10px;font-family:'Courier Prime',monospace;font-size:.72rem;outline:none;transition:border-color .2s}
.chat-input:focus{border-color:var(--teal)}
.chat-send{background:var(--gold-dim);border:1px solid rgba(212,168,75,.3);color:var(--amber);padding:7px 12px;cursor:pointer;font-family:'Cinzel',serif;font-size:.58rem;font-weight:700;letter-spacing:1px;transition:background .15s}
.chat-send:hover{background:rgba(212,168,75,.28)}
.cam-bar{position:fixed;bottom:40px;left:0;right:300px;z-index:20;display:flex;justify-content:center;gap:4px;padding:5px 8px;background:rgba(8,7,5,.85);border-top:1px solid var(--gold-dim)}
.cam-btn{padding:5px 14px;border:1px solid var(--gold-dim);background:rgba(0,0,0,.4);color:var(--warm-mid);font-family:'Cinzel',serif;font-size:.55rem;font-weight:700;letter-spacing:1.5px;cursor:pointer;transition:all .12s;text-transform:uppercase}
.cam-btn:hover{border-color:var(--amber);color:var(--amber)}
.cam-btn.active{border-color:var(--red-rec);color:var(--red-rec);background:rgba(255,34,34,.08)}
.status-bar{position:fixed;bottom:0;left:0;right:0;height:40px;z-index:20;background:rgba(8,7,5,.92);border-top:1px solid var(--gold-dim);display:flex;align-items:center;justify-content:space-between;padding:0 14px;font-size:.62rem;letter-spacing:1.5px}
.status-left,.status-right{display:flex;gap:14px;align-items:center}
.rec-indicator{display:flex;align-items:center;gap:5px;color:var(--red-rec)}
.rec-dot{width:7px;height:7px;border-radius:50%;background:var(--red-rec);display:none}
.rec-dot.on{display:block;animation:blink .7s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
.cam-indicator{color:var(--amber)}
.room-indicator{color:var(--teal)}
.rec-btn{background:rgba(255,34,34,.12);border:1px solid rgba(255,34,34,.3);color:var(--red-rec);padding:5px 12px;cursor:pointer;font-family:'Cinzel',serif;font-size:.55rem;font-weight:700;letter-spacing:1px;transition:background .15s}
.rec-btn:hover,.rec-btn.on{background:rgba(255,34,34,.25)}
</style>
</head>
<body>
<a href="/safe-console" style="position:fixed;top:12px;left:12px;z-index:9999;background:rgba(0,0,0,.75);border:1px solid #e3b65d;color:#f2f2e8;padding:6px 10px;text-decoration:none;font:700 11px system-ui,sans-serif">HELP / RECOVERY</a>


<canvas id="stage-canvas"></canvas>

<div class="exp-banner">◈ 3D STUDIO — EXPERIMENTAL</div>
<a class="back-badge" href="stage.html">← 2.5D STAGE</a>

<div class="chat-panel">
  <div class="chat-header">
    <div class="chat-header-dot"></div>◆ LIVE CHAT ◆
  </div>
  <div class="chat-messages" id="chatMessages"></div>
  <div class="chat-input-bar">
    <input class="chat-input" id="chatInput" placeholder="Type a message..." maxlength="500">
    <button class="chat-send" onclick="sendChat()">SEND</button>
  </div>
</div>

<div class="cam-bar" id="camBar"></div>

<div class="status-bar">
  <div class="status-left">
    <span class="rec-indicator"><span class="rec-dot" id="recDot"></span><span id="recText">STANDBY</span></span>
    <span class="cam-indicator" id="camLabel">CAM: WIDE</span>
    <span class="room-indicator" id="roomLabel">ROOM: STUDIO</span>
  </div>
  <div class="status-right">
    <span id="timecode" style="color:#33ff99;opacity:0.4;font-size:.6rem">00:00:00:00</span>
    <button class="rec-btn" id="recBtn" onclick="toggleRecord()">● REC</button>
  </div>
</div>

<script src="/static/reach_auth.js"></script>
<script type="importmap">
{"imports":{"three":"https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.module.js"}}
</script>
<script type="module">
import * as THREE from 'three';

// ═══ RENDERER ══════════════════════════════════════════════════════════════

const canvas = document.getElementById('stage-canvas');
const renderer = new THREE.WebGLRenderer({canvas, antialias:true, alpha:false, powerPreference:'low-power'});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));  // cap for Zoidberg
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.1;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x080604);
scene.fog = new THREE.FogExp2(0x080604, 0.028);

// ═══ CAMERAS ═══════════════════════════════════════════════════════════════

const cameras = {
  wide:    new THREE.PerspectiveCamera(72, window.innerWidth/window.innerHeight, 0.1, 80),
  medium:  new THREE.PerspectiveCamera(48, window.innerWidth/window.innerHeight, 0.1, 80),
  close:   new THREE.PerspectiveCamera(32, window.innerWidth/window.innerHeight, 0.1, 80),
  overhead:new THREE.PerspectiveCamera(80, window.innerWidth/window.innerHeight, 0.1, 80),
  stage:   new THREE.PerspectiveCamera(55, window.innerWidth/window.innerHeight, 0.1, 80),
};
cameras.wide.position.set(0, 2.2, 7);    cameras.wide.lookAt(0, 1.2, 0);
cameras.medium.position.set(2, 1.8, 4);  cameras.medium.lookAt(0, 1.4, 0);
cameras.close.position.set(0.8, 1.7, 2.2); cameras.close.lookAt(0, 1.5, 0);
cameras.overhead.position.set(0, 7, 1);  cameras.overhead.lookAt(0, 0, 0);
cameras.stage.position.set(-2.5, 2, 4.5); cameras.stage.lookAt(0.5, 1, 0);

// Smooth camera interpolation targets
let activeCam = cameras.wide, activeCamName = 'wide';
let camPos = new THREE.Vector3().copy(cameras.wide.position);
let camTarget = new THREE.Vector3(0, 1.2, 0);
let camFOV = cameras.wide.fov;

// ═══ LIGHTING — animated, mood-responsive ══════════════════════════════════

// Warm ambient
const ambient = new THREE.AmbientLight(0x100c08, 0.35);
scene.add(ambient);

// Key light — above-right, warm tungsten
const keyLight = new THREE.SpotLight(0xffe4b5, 1.8, 22, Math.PI/3.5, 0.4, 1.2);
keyLight.position.set(3.5, 6, 3);
keyLight.castShadow = true;
keyLight.shadow.mapSize.width = 1024;
keyLight.shadow.mapSize.height = 1024;
keyLight.shadow.camera.near = 0.5;
keyLight.shadow.camera.far = 20;
scene.add(keyLight);

// Fill light — left, cool-teal (broadcast feel)
const fillLight = new THREE.PointLight(0x6dd6c7, 0.35, 12);
fillLight.position.set(-3.5, 3, 2);
scene.add(fillLight);

// Back light / rim — amber separation
const rimLight = new THREE.SpotLight(0xe5c17e, 0.9, 14, Math.PI/2.8, 0.6, 1.5);
rimLight.position.set(0, 5, -3.5);
scene.add(rimLight);

// Floor bounce — very subtle warm
const bounceLight = new THREE.PointLight(0x2a1a08, 0.18, 6);
bounceLight.position.set(0, 0.05, 0);
scene.add(bounceLight);

// Mood state target for light color interpolation
let moodTargetColor = new THREE.Color(0xffe4b5);
let moodCurrentColor = new THREE.Color(0xffe4b5);

const MOOD_COLORS = {
  warm:       new THREE.Color(0xffe4b5),
  theatrical: new THREE.Color(0xd4a0ff),
  tense:      new THREE.Color(0xff8060),
  cool:       new THREE.Color(0x88ddcc),
  dark:       new THREE.Color(0x604030),
  neutral:    new THREE.Color(0xffe4b5),
};

window.setMoodColor = function(state) {
  moodTargetColor = MOOD_COLORS[state] || MOOD_COLORS.neutral;
};

// ═══ GEOMETRY — Belle Époque Studio ═══════════════════════════════════════

// Studio floor — dark polished wood planks suggestion
const floorGeo = new THREE.PlaneGeometry(16, 14);
const floorMat = new THREE.MeshStandardMaterial({
  color:0x18120a, roughness:0.75, metalness:0.08,
});
const floor = new THREE.Mesh(floorGeo, floorMat);
floor.rotation.x = -Math.PI/2;
floor.receiveShadow = true;
scene.add(floor);

// Stage platform — circular riser
const platformGeo = new THREE.CylinderGeometry(3, 3.3, 0.14, 48);
const platformMat = new THREE.MeshStandardMaterial({color:0x22180e, roughness:0.55, metalness:0.15});
const platform = new THREE.Mesh(platformGeo, platformMat);
platform.position.set(0, 0.07, 0);
platform.receiveShadow = true;
scene.add(platform);

// Back wall — painted, architectural
const backWallGeo = new THREE.PlaneGeometry(14, 7);
const backWallMat = new THREE.MeshStandardMaterial({color:0x0e0b07, roughness:0.92});
const backWall = new THREE.Mesh(backWallGeo, backWallMat);
backWall.position.set(0, 3.5, -4.5);
backWall.receiveShadow = true;
scene.add(backWall);

// Arch frame above stage — decorative
const archCurve = new THREE.QuadraticBezierCurve3(
  new THREE.Vector3(-2.5, 3, -4.3),
  new THREE.Vector3(0, 5.5, -4.3),
  new THREE.Vector3(2.5, 3, -4.3),
);
const archPoints = archCurve.getPoints(32);
const archGeo = new THREE.BufferGeometry().setFromPoints(archPoints);
const archMat = new THREE.LineBasicMaterial({color:0x3a2a14, opacity:0.6, transparent:true});
const archLine = new THREE.Line(archGeo, archMat);
scene.add(archLine);

// Broadcast desk — dark mahogany form
function makeDesk() {
  const g = new THREE.Group();
  const topGeo = new THREE.BoxGeometry(3.2, 0.08, 0.7);
  const topMat = new THREE.MeshStandardMaterial({color:0x2e1e0e, roughness:0.6, metalness:0.1});
  const top = new THREE.Mesh(topGeo, topMat);
  top.position.y = 0.8;
  top.castShadow = true; top.receiveShadow = true;
  g.add(top);
  // Front face
  const frontGeo = new THREE.BoxGeometry(3.2, 0.76, 0.06);
  const frontMat = new THREE.MeshStandardMaterial({color:0x221608, roughness:0.7, metalness:0.05});
  const front = new THREE.Mesh(frontGeo, frontMat);
  front.position.set(0, 0.42, 0.37);
  front.castShadow = true;
  g.add(front);
  // Gold trim strip on front top edge
  const trimGeo = new THREE.BoxGeometry(3.2, 0.02, 0.03);
  const trimMat = new THREE.MeshStandardMaterial({color:0xd4a84b, roughness:0.3, metalness:0.8});
  const trim = new THREE.Mesh(trimGeo, trimMat);
  trim.position.set(0, 0.85, 0.35);
  g.add(trim);
  g.position.set(0, 0.14, -0.9);
  return g;
}
const desk = makeDesk();
scene.add(desk);

// Monitor bank — back wall mounted
function makeMonitor(w, h, color, emissive) {
  const g = new THREE.Group();
  const frameGeo = new THREE.BoxGeometry(w+0.04, h+0.04, 0.04);
  const frameMat = new THREE.MeshStandardMaterial({color:0x1a1208, roughness:0.5, metalness:0.4});
  g.add(new THREE.Mesh(frameGeo, frameMat));
  const screenGeo = new THREE.PlaneGeometry(w, h);
  const screenMat = new THREE.MeshStandardMaterial({
    color: color || 0x080c10,
    emissive: emissive || 0x001020,
    emissiveIntensity:0.4,
    roughness:0.1, metalness:0,
  });
  const screen = new THREE.Mesh(screenGeo, screenMat);
  screen.position.z = 0.025;
  g.add(screen);
  return {group:g, screen, screenMat};
}

const pgmMon = makeMonitor(0.9, 0.6, 0x080808, 0x220000);
pgmMon.group.position.set(-1.2, 3.8, -4.35);
scene.add(pgmMon.group);

const pvwMon = makeMonitor(0.9, 0.6, 0x080808, 0x002200);
pvwMon.group.position.set(0, 3.8, -4.35);
scene.add(pvwMon.group);

const auxMon = makeMonitor(0.6, 0.4, 0x080808, 0x080808);
auxMon.group.position.set(1.1, 3.8, -4.35);
scene.add(auxMon.group);

// Lighting rig — horizontal bar with practicals
const rigGeo = new THREE.CylinderGeometry(0.02, 0.02, 10, 8);
const rigMat = new THREE.MeshStandardMaterial({color:0x1a1510, roughness:0.8, metalness:0.6});
const rig = new THREE.Mesh(rigGeo, rigMat);
rig.rotation.z = Math.PI/2;
rig.position.set(0, 5.2, -1);
scene.add(rig);

// Practicals hanging from rig
function makePractical(x) {
  const g = new THREE.Group();
  const hoodGeo = new THREE.ConeGeometry(0.12, 0.2, 8);
  const hoodMat = new THREE.MeshStandardMaterial({color:0x1a1208, roughness:0.7, metalness:0.5});
  g.add(new THREE.Mesh(hoodGeo, hoodMat));
  const bulbGeo = new THREE.SphereGeometry(0.04, 8, 8);
  const bulbMat = new THREE.MeshStandardMaterial({emissive:0xffe4b5, emissiveIntensity:2, color:0x000000});
  const bulb = new THREE.Mesh(bulbGeo, bulbMat);
  bulb.position.y = -0.14;
  g.add(bulb);
  g.position.set(x, 5.0, -1);
  return g;
}
[-2.5, -1.2, 0, 1.2, 2.5].forEach(x => scene.add(makePractical(x)));

// ═══ CHARACTER FIGURES — luminous silhouettes with material depth ═══════════

function makeCharacter(opts) {
  const {x, z, primaryColor, accentColor, name, scale} = opts;
  const s = scale || 1;
  const g = new THREE.Group();

  const charMat = new THREE.MeshStandardMaterial({
    color: primaryColor,
    emissive: primaryColor,
    emissiveIntensity: 0.2,
    transparent: true,
    opacity: 0.82,
    roughness: 0.5,
    metalness: 0.1,
  });

  // Legs
  [[-.1, 0], [.1, 0]].forEach(([lx]) => {
    const geo = new THREE.CylinderGeometry(0.07*s, 0.08*s, 0.75*s, 10);
    const m = new THREE.Mesh(geo, charMat);
    m.position.set(lx*s, 0.38*s, 0);
    m.castShadow = true;
    g.add(m);
  });

  // Torso
  const torsoGeo = new THREE.CylinderGeometry(0.18*s, 0.16*s, 0.65*s, 12);
  const torso = new THREE.Mesh(torsoGeo, charMat);
  torso.position.set(0, 1.05*s, 0);
  torso.castShadow = true;
  g.add(torso);

  // Arms
  [[-1,0.08], [1,-0.08]].forEach(([side, tilt]) => {
    const geo = new THREE.CylinderGeometry(0.05*s, 0.04*s, 0.55*s, 8);
    const m = new THREE.Mesh(geo, charMat);
    m.position.set(0.26*side*s, 0.95*s, 0);
    m.rotation.z = (Math.PI/5 + tilt) * side;
    m.castShadow = true;
    g.add(m);
  });

  // Neck
  const neckGeo = new THREE.CylinderGeometry(0.065*s, 0.07*s, 0.12*s, 8);
  g.add(new THREE.Mesh(neckGeo, charMat)).position?.set(0, 1.44*s, 0);

  // Head
  const headGeo = new THREE.SphereGeometry(0.17*s, 16, 16);
  const head = new THREE.Mesh(headGeo, new THREE.MeshStandardMaterial({
    color: primaryColor,
    emissive: primaryColor,
    emissiveIntensity: 0.35,
    transparent: true, opacity: 0.9,
    roughness: 0.4, metalness: 0.05,
  }));
  head.position.set(0, 1.66*s, 0);
  head.castShadow = true;
  g.add(head);

  // Glow ring at feet
  const ringGeo = new THREE.RingGeometry(0.25*s, 0.42*s, 32);
  const ringMat = new THREE.MeshBasicMaterial({
    color: accentColor || primaryColor,
    transparent: true, opacity: 0.12,
    side: THREE.DoubleSide,
  });
  const ring = new THREE.Mesh(ringGeo, ringMat);
  ring.rotation.x = -Math.PI/2;
  ring.position.y = 0.01;
  g.add(ring);

  // Point light — character emits subtle fill
  const charLight = new THREE.PointLight(primaryColor, 0.3, 4);
  charLight.position.set(0, 1.2*s, 0.3);
  g.add(charLight);

  g.position.set(x, 0.14, z);
  g.userData = {name, ring, ringMat, charLight, head, primaryColor, accentColor, breathPhase: Math.random()*Math.PI*2};
  scene.add(g);
  return g;
}

const pete = makeCharacter({
  x:-1.4, z: 0.3,
  primaryColor: 0x4dc8aa,
  accentColor:  0x6dd6c7,
  name: 'Pete', scale: 1.0,
});

const purfluous = makeCharacter({
  x: 1.4, z: 0.2,
  primaryColor: 0xb064d8,
  accentColor:  0xc078e0,
  name: 'Sir Purfluous', scale: 1.08,
});

const hostSlot = makeCharacter({
  x: 0, z:-0.1,
  primaryColor: 0xd4a84b,
  accentColor:  0xe5c17e,
  name: 'Host', scale: 1.02,
});
hostSlot.visible = false;  // hidden until a host joins

// ═══ ANIMATION LOOP ════════════════════════════════════════════════════════

const clock = new THREE.Clock();
let lerpCamProgress = 0;
let lerpCamFrom = new THREE.Vector3().copy(cameras.wide.position);
let lerpCamTargetPos = new THREE.Vector3().copy(cameras.wide.position);
let lerpCamFromTarget = new THREE.Vector3(0,1.2,0);
let lerpCamToTarget = new THREE.Vector3(0,1.2,0);
let isTransitioning = false;

function animate() {
  requestAnimationFrame(animate);
  const t = clock.getElapsedTime();
  const dt = clock.getDelta ? 0.016 : 0.016;

  // Breathing light animation — 2-3% intensity oscillation, 4.2s cycle
  const breathe = 1 + Math.sin(t * (Math.PI*2/4.2)) * 0.025;
  keyLight.intensity  = 1.8 * breathe;
  bounceLight.intensity = 0.18 * breathe;

  // Mood color interpolation
  moodCurrentColor.lerp(moodTargetColor, 0.01);
  keyLight.color.copy(moodCurrentColor);

  // Monitor flicker — very subtle
  pgmMon.screenMat.emissiveIntensity = 0.4 + Math.sin(t*7.3)*0.02;
  pvwMon.screenMat.emissiveIntensity = 0.35 + Math.sin(t*6.1+1)*0.015;

  // Character breathing + glow ring pulse
  [pete, purfluous, hostSlot].forEach((char, i) => {
    if (!char.visible) return;
    const {ring, ringMat, charLight, breathPhase} = char.userData;
    const b = Math.sin(t * 1.35 + breathPhase);
    char.children.forEach((child, ci) => {
      if (ci < 3) { // legs
        child.position.y = child.position.y; // static
      }
    });
    // Subtle upward bob
    char.position.y = 0.14 + b * 0.012;
    // Ring pulse
    if (ringMat) ringMat.opacity = 0.10 + b * 0.04;
    // Character point light pulse
    if (charLight) charLight.intensity = 0.28 + b * 0.08;
  });

  // Camera smooth transition
  if (isTransitioning) {
    lerpCamProgress = Math.min(1, lerpCamProgress + 0.025);
    const ease = lerpCamProgress < 0.5
      ? 2 * lerpCamProgress * lerpCamProgress
      : -1 + (4 - 2 * lerpCamProgress) * lerpCamProgress;

    activeCam.position.lerpVectors(lerpCamFrom, lerpCamTargetPos, ease);
    const lt = new THREE.Vector3().lerpVectors(lerpCamFromTarget, lerpCamToTarget, ease);
    activeCam.lookAt(lt);

    if (lerpCamProgress >= 1) {
      isTransitioning = false;
      activeCam.position.copy(lerpCamTargetPos);
      activeCam.lookAt(lerpCamToTarget);
    }
  }

  renderer.render(scene, activeCam);
}
animate();

// ═══ CAMERA SWITCHING — with smooth interpolation ══════════════════════════

const CAM_TARGETS = {
  wide:    new THREE.Vector3(0, 1.2, 0),
  medium:  new THREE.Vector3(0, 1.4, 0),
  close:   new THREE.Vector3(0, 1.5, 0),
  overhead:new THREE.Vector3(0, 0, 0),
  stage:   new THREE.Vector3(0.5, 1, 0),
};

function switchCamera(name) {
  if (!cameras[name]) return;
  lerpCamFrom.copy(activeCam.position);
  lerpCamFromTarget.copy(lerpCamToTarget);
  lerpCamTargetPos.copy(cameras[name].position);
  lerpCamToTarget.copy(CAM_TARGETS[name] || new THREE.Vector3(0,1.2,0));
  activeCam = cameras[name];
  activeCamName = name;
  lerpCamProgress = 0;
  isTransitioning = true;
  activeCam.fov = cameras[name].fov;
  activeCam.updateProjectionMatrix();
  document.getElementById('camLabel').textContent = 'CAM: ' + name.toUpperCase();
  buildCamBar();
}
window.switchCamera = switchCamera;

function buildCamBar() {
  const bar = document.getElementById('camBar');
  bar.innerHTML = '';
  Object.keys(cameras).forEach(name => {
    const btn = document.createElement('button');
    btn.className = 'cam-btn' + (activeCamName === name ? ' active' : '');
    btn.textContent = name.toUpperCase();
    btn.onclick = () => switchCamera(name);
    bar.appendChild(btn);
  });
}
buildCamBar();

// ═══ RECORDING ═════════════════════════════════════════════════════════════

let isRecording = false, mediaRecorder = null, recordedChunks = [];

window.toggleRecord = function() {
  if (isRecording) {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop();
    isRecording = false;
    document.getElementById('recDot').classList.remove('on');
    document.getElementById('recText').textContent = 'STANDBY';
    document.getElementById('recBtn').classList.remove('on');
    document.getElementById('recBtn').textContent = '● REC';
  } else {
    recordedChunks = [];
    const stream = canvas.captureStream(30);
    try {
      mediaRecorder = new MediaRecorder(stream, {mimeType:'video/webm;codecs=vp9'});
      mediaRecorder.ondataavailable = e => { if (e.data.size > 0) recordedChunks.push(e.data); };
      mediaRecorder.onstop = () => {
        const blob = new Blob(recordedChunks, {type:'video/webm'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = `pubcast3d_${Date.now()}.webm`; a.click();
        URL.revokeObjectURL(url);
      };
      mediaRecorder.start(100);
      isRecording = true;
      document.getElementById('recDot').classList.add('on');
      document.getElementById('recText').textContent = '● RECORDING';
      document.getElementById('recBtn').classList.add('on');
      document.getElementById('recBtn').textContent = '◼ STOP';
    } catch(e) {
      alert('Recording error: ' + e.message);
    }
  }
};

// ═══ WEBSOCKET ═════════════════════════════════════════════════════════════

let ws = null;
const ROOM = new URLSearchParams(location.search).get('room') || 'studio';
document.getElementById('roomLabel').textContent = 'ROOM: ' + ROOM.toUpperCase();

function connectWS() {
  try {
    ws = new WebSocket(window.ReachAuth.websocketURL(`/ws/room/${encodeURIComponent(ROOM)}`));
    ws.onmessage = e => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === 'chat' && msg.payload) {
          addChatMessage(msg.payload.user||'Anon', msg.payload.text||'', msg.payload.user_id);
        } else if (msg.type === 'history' && msg.payload) {
          msg.payload.forEach(m => addChatMessage(m.user||'Anon', m.text||'', m.user_id));
        } else if (msg.type === 'camera_switch' && msg.payload) {
          if (msg.payload.target === 'program') {
            const map = {wide_shot:'wide',medium_shot:'medium',close_up:'close',overhead:'overhead'};
            switchCamera(map[msg.payload.source_id] || msg.payload.source_id);
          }
        } else if (msg.type === 'mood_change' && msg.payload) {
          window.setMoodColor(msg.payload.state || 'neutral');
        }
      } catch {}
    };
    ws.onclose = () => setTimeout(connectWS, 3000);
  } catch {}
}

window.sendChat = function() {
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text || !ws || ws.readyState !== 1) return;
  ws.send(JSON.stringify({type:'chat', user:'Director', text, user_id:'director'}));
  input.value = '';
};

document.getElementById('chatInput').addEventListener('keydown', e => {
  if (e.key === 'Enter') window.sendChat();
});

function addChatMessage(user, text, userId) {
  const div = document.createElement('div');
  div.className = 'chat-msg';
  const isBot = userId && (userId.startsWith('bot-') || userId.startsWith('agent:'));
  const escaped = text.replace(/</g,'&lt;').replace(/>/g,'&gt;');
  div.innerHTML = `<span class="${isBot?'bot':'user'}">${user}:</span> <span class="text">${escaped}</span>`;
  const c = document.getElementById('chatMessages');
  c.appendChild(div); c.scrollTop = c.scrollHeight;
}

// ═══ TIMECODE & KEYBOARD ═══════════════════════════════════════════════════

setInterval(() => {
  const now = new Date();
  const p = n => String(n).padStart(2,'0');
  const f = Math.floor((now.getMilliseconds()/1000)*30);
  document.getElementById('timecode').textContent =
    `${p(now.getHours())}:${p(now.getMinutes())}:${p(now.getSeconds())}:${p(f)}`;
}, 100);

document.addEventListener('keydown', e => {
  if (e.target.tagName === 'INPUT') return;
  const k = {'1':'wide','2':'medium','3':'close','4':'overhead','5':'stage'};
  if (k[e.key]) { switchCamera(k[e.key]); return; }
  if (e.key==='r'||e.key==='R') window.toggleRecord();
});

window.addEventListener('resize', () => {
  renderer.setSize(window.innerWidth, window.innerHeight);
  Object.values(cameras).forEach(cam => {
    cam.aspect = window.innerWidth/window.innerHeight;
    cam.updateProjectionMatrix();
  });
});

connectWS();
</script>
  <script src="/static/program_audio_runtime.js"></script>
  <script src="/static/avatar_glb_motion_consumer.js"></script>
  <script src="/static/voxel_block_preview_client.js"></script>
</body>
</html>

`````

## tests/test_studio_console_action_routes.py

SHA-256: f9b67eed43ae30797379543f46a6679f5d6fd94eaacea355a381b5ac80401c96

`````text
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.cameras import create_default_cameras
from modules.production_routes import create_production_router
from modules.recording import create_recording_service


class FakeBlackBox:
    def __init__(self):
        self.events = []

    def record_event(self, event_type, *, source, actor, data):
        self.events.append({"event_type": event_type, "source": source, "actor": actor, "data": data})


class FakeHub:
    def __init__(self):
        self.events = []

    async def broadcast_system_event(self, event):
        self.events.append(event)


def make_client(tmp_path: Path):
    cameras = create_default_cameras()
    recording = create_recording_service(tmp_path, cameras)
    blackbox = FakeBlackBox()
    hub = FakeHub()
    app = FastAPI()
    app.include_router(create_production_router(cameras, recording, hub=hub, blackbox=blackbox))
    return TestClient(app), cameras, blackbox, hub


def test_studio_actions_manifest_is_hotspot_ready(tmp_path: Path):
    client, _, _, _ = make_client(tmp_path)

    response = client.get("/api/studio/actions", headers={"X-Client-Id": "director"})

    assert response.status_code == 200
    ids = {item["action_id"] for item in response.json()["actions"]}
    assert "camera.switch.program" in ids
    assert "recording.preflight" in ids
    assert "audio.stop_all" in ids


def test_studio_action_route_executes_and_records_blackbox(tmp_path: Path):
    client, cameras, blackbox, hub = make_client(tmp_path)

    response = client.post(
        "/api/studio/actions/camera.switch.program",
        json={"source_id": "medium_shot"},
        headers={"X-Client-Id": "director"},
    )

    assert response.status_code == 200
    assert response.json()["result"]["source_id"] == "medium_shot"
    assert cameras.get_program_source().source_id == "medium_shot"
    assert blackbox.events[-1]["event_type"] == "studio.action"
    assert blackbox.events[-1]["data"]["action_id"] == "camera.switch.program"
    assert hub.events[-1]["type"] == "studio_action"
    assert hub.events[-1]["payload"]["action_id"] == "camera.switch.program"


def test_studio_action_route_rejects_unconfirmed_recording_start(tmp_path: Path):
    client, _, _, _ = make_client(tmp_path)

    response = client.post(
        "/api/studio/actions/recording.start",
        json={},
        headers={"X-Client-Id": "director"},
    )

    assert response.status_code == 400
    assert "confirm" in response.json()["detail"]

`````

## tests/test_camera_broadcast.py

SHA-256: b292ac08f5c1e79cb439383eb6cfc1381a4a49d26601c824aa380e91858629a6

`````text
"""Camera changes reach the stage pages, whichever route made them.

Regressions covered:
- Only some camera routes broadcast `camera_switch`; cuts from /api/switcher/* and
  the director console's studio actions changed the backend and nothing on screen.
- The stage pages' default room "studio" made them open /ws/studio, which belongs
  to the studio desk protocol, so they received no Hub traffic at all.
"""
from __future__ import annotations

import asyncio
import threading

import pytest

from modules.camera_broadcast import CameraBroadcastBridge
from modules.cameras import create_default_cameras


class FakeHub:
    def __init__(self):
        self.events = []

    async def broadcast_system_event(self, event):
        self.events.append(event)


def program_events(hub):
    return [e["payload"]["source_id"] for e in hub.events if e["payload"]["target"] == "program"]


def test_every_program_and_preview_change_is_broadcast_once():
    async def run():
        cams, hub = create_default_cameras(), FakeHub()
        bridge = CameraBroadcastBridge(cams, hub)
        bridge.start()
        assert hub.camera_events_bridged is True
        cams.set_program_source("close_up")
        cams.set_program_source("close_up")          # idempotent: no event
        cams.set_preview_source("overhead")
        cams.set_program_source("no_such_camera")    # invalid: no event
        await asyncio.sleep(0)
        await bridge.stop()
        return hub

    hub = asyncio.run(run())
    assert [(e["type"], e["payload"]["target"], e["payload"]["source_id"]) for e in hub.events] == [
        ("camera_switch", "program", "close_up"), ("camera_switch", "preview", "overhead")]
    last = hub.events[-1]["payload"]
    assert last["program"] == "close_up" and last["preview"] == "overhead"
    assert hub.camera_events_bridged is False


def test_stopped_bridge_sends_nothing_and_restarts_cleanly():
    async def run():
        cams, hub = create_default_cameras(), FakeHub()
        bridge = CameraBroadcastBridge(cams, hub)
        bridge.start(); bridge.start()              # double start must not double-subscribe
        cams.set_program_source("close_up")
        await asyncio.sleep(0)
        await bridge.stop()
        cams.set_program_source("overhead")          # after stop: silent
        bridge.start()
        cams.set_program_source("medium_shot")
        await asyncio.sleep(0)
        await bridge.stop()
        return hub

    assert program_events(asyncio.run(run())) == ["close_up", "medium_shot"]


def test_change_from_a_worker_thread_is_delivered_on_the_loop():
    async def run():
        cams, hub = create_default_cameras(), FakeHub()
        bridge = CameraBroadcastBridge(cams, hub)
        bridge.start()
        worker = threading.Thread(target=cams.set_program_source, args=("overhead",))
        worker.start(); worker.join()
        for _ in range(50):
            if hub.events:
                break
            await asyncio.sleep(0.01)
        await bridge.stop()
        return hub

    assert program_events(asyncio.run(run())) == ["overhead"]


def test_a_failing_hub_never_rolls_back_camera_state():
    class BrokenHub(FakeHub):
        async def broadcast_system_event(self, event):
            raise RuntimeError("socket gone")

    async def run():
        cams = create_default_cameras()
        bridge = CameraBroadcastBridge(cams, BrokenHub())
        bridge.start()
        cams.set_program_source("close_up")
        await asyncio.sleep(0)
        await bridge.stop()
        return cams.get_program_source().source_id

    assert asyncio.run(run()) == "close_up"


# ── through the real app ───────────────────────────────────────────────────

def _drain_until_camera(ws, limit=40):
    for _ in range(limit):
        msg = ws.receive_json()
        if msg.get("type") == "camera_switch" and msg["payload"]["target"] == "program":
            return msg["payload"]["source_id"]
    raise AssertionError("no camera_switch received")


@pytest.mark.parametrize("cut", [
    lambda c: c.post("/api/switcher/cut/overhead"),
    lambda c: (c.post("/api/switcher/preview/overhead"), c.post("/api/switcher/cut"))[-1],
    lambda c: c.post("/api/cameras/program/overhead"),
    lambda c: c.post("/api/cameras/switch", json={"target": "program", "source_id": "overhead"}),
    lambda c: c.post("/api/studio/actions/camera.switch.program", json={"source_id": "overhead"}),
], ids=["switcher-cut-camera", "switcher-preview-then-cut", "cameras-program", "cameras-switch", "studio-action"])
def test_stage_room_socket_receives_each_kind_of_cut(client, cut):
    client.post("/api/cameras/program/wide_shot")
    with client.websocket_connect("/ws/room/studio") as ws:
        response = cut(client)
        assert response.status_code < 400, response.text
        assert _drain_until_camera(ws) == "overhead"


def test_ws_studio_still_belongs_to_the_studio_desk(client):
    with client.websocket_connect("/ws/studio") as ws:
        first = ws.receive_json()
    assert first.get("type") in {"initial_state", "error"}   # studio desk protocol, not a Hub room


def test_stage_pages_use_the_room_safe_socket_path():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    for page, var in (("stage_panoramic.html", "ROOM"), ("stage.html", "ROOM"),
                      ("stage_3d.html", "ROOM"), ("avatar_controls.html", "room")):
        text = (root / "static" / page).read_text(encoding="utf-8")
        assert f"websocketURL(`/ws/room/${{encodeURIComponent({var})}}`)" in text, page
        assert f"websocketURL(`/ws/${{{var}}}`)" not in text, page

`````

## tests/test_world_walk_host_integration.py

SHA-256: 8b698bf20ee1e7364aa8c73f9f426d403a61f829737c96a6e0fd5d86c7fe5f6c

`````text
"""The walkable world (static/world_walk.html) inside the real PubCast host.

Boots the real ``main.app`` with uvicorn in a separate process against a disposable data directory, then checks:
the /walk routes; the Counter, legacy Foresight and launcher entries; and, in real Chromium, that the walker joins the
same PubWorld socket world.html uses, reports rooms by their live ids (and the host acknowledges them), moves the room
audio runtime with it, runs dressing-room hotspots through /pubworld/api/hotspot, and hops to and from the classic page.
No user data is touched. Browser checks skip when Playwright/Chromium is unavailable.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def host(tmp_path_factory):
    data = tmp_path_factory.mktemp("walk_host_data")
    port = _free_port()
    env = dict(os.environ, PUBCAST_DATA_DIR=str(data), PYTHONUNBUFFERED="1")
    env.pop("PUBCAST_ENFORCE_AUTH", None)
    log = open(data / "host.log", "w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        cwd=str(ROOT), env=env, stdout=log, stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{port}"
    try:
        deadline = time.time() + 90
        while time.time() < deadline:
            if proc.poll() is not None:
                log.flush()
                raise AssertionError("PubCast host exited during startup:\n" + (data / "host.log").read_text(encoding="utf-8")[-4000:])
            try:
                if httpx.get(base + "/health", timeout=0.5).status_code == 200:
                    break
            except httpx.RequestError:
                pass
            time.sleep(0.2)
        else:
            raise AssertionError("PubCast host did not come up within 90 s")
        yield base
    finally:
        proc.terminate()
        try:
            proc.wait(15)
        except subprocess.TimeoutExpired:
            proc.kill(); proc.wait(5)
        log.close()


# ── HTTP: the host serves the walker and everything it loads ────────────────

@pytest.fixture(scope="module")
def owner(host):
    """The first-run owner account, created through the real setup route (pages need a Reach session)."""
    import secrets
    password = secrets.token_urlsafe(24)
    r = httpx.post(host + "/api/auth/setup", json={"username": "walk-owner", "password": password, "confirm_password": password}, timeout=10)
    assert r.status_code in (200, 201), r.text
    data = r.json()
    assert data.get("access_token")
    return data


@pytest.fixture
def fresh_studio_progress(host, owner):
    """A fresh-start assertion needs fresh progress, even after earlier walks saved."""
    response = httpx.put(host + "/api/studio/progress",
        headers={"Authorization": "Bearer " + owner["access_token"]},
        json={"progress": {}}, timeout=10)
    assert response.status_code == 200, response.text


@pytest.fixture
def counter_entry_page(browser):
    """A plain Counter page; no walker WebSocket spy, and always closed."""
    pg = browser.new_page(viewport={"width": 1400, "height": 860})
    pg.problems = []
    pg.on("pageerror", lambda e: pg.problems.append(str(e)))
    try:
        yield pg
    finally:
        pg.close()


@pytest.mark.parametrize("route", ["/walk", "/world-walk"])
def test_the_host_serves_the_walkable_world(host, route):
    r = httpx.get(host + route, timeout=10)
    assert r.status_code == 200
    page = r.text
    assert "<title>Bella Faux Pas Studio</title>" in page
    for script in ("/static/reach_auth.js", "/static/world_walk_glb.js", "/static/world_walk_live.js"):
        assert f'src="{script}"' in page, script
        assert httpx.get(host + script, timeout=10).status_code == 200, script
    # the room audio runtime is loaded by the live link once it knows the host is there
    assert httpx.get(host + "/static/program_audio_runtime.js", timeout=10).status_code == 200
    world = httpx.get(host + "/static/world/world.json", timeout=10)
    assert world.status_code == 200 and world.json()["rooms"]
    for f in ("build/three.module.js", "examples/jsm/loaders/GLTFLoader.js", "examples/jsm/utils/SkeletonUtils.js"):
        assert httpx.get(host + "/static/vendor/three-0.160.0/" + f, timeout=10).status_code == 200, f


def test_the_walk_is_on_every_way_into_the_program():
    counter = (STATIC / "foresight_programs.js").read_text(encoding="utf-8")
    assert "{id: 'bella_faux_pas', title: 'Bella Faux Pas Studio', short: 'Studio', group: 'Programs', kind: 'page', url: '/walk'" in counter
    legacy = (STATIC / "foresight.html").read_text(encoding="utf-8")
    assert "{id:'bella_faux_pas',label:'Bella Faux Pas Studio',group:'Studio Rooms', kind:'iframe', url:'/walk'" in legacy
    assert '<a href="/walk" class="nav-pill">Bella Faux Pas</a>' in (STATIC / "launch.html").read_text(encoding="utf-8")
    classic = (STATIC / "world.html").read_text(encoding="utf-8")
    assert '<a id="walk-link" href="/walk"' in classic
    assert "a.href = '/walk?live=' + encodeURIComponent(e.detail.room)" in classic


def test_every_live_room_id_the_walker_reports_is_one_the_program_already_uses():
    """The walker reports rooms by live_id; those must be ids the classic page and the room audio runtime know."""
    import json, re
    world = json.loads((STATIC / "world" / "world.json").read_text(encoding="utf-8"))
    classic = (STATIC / "world.html").read_text(encoding="utf-8")
    classic_ids = set(re.findall(r"^  ([a-z_]+): \{$", classic[classic.index("const ROOMS = {"):classic.index("GAME STATE")], re.M))
    live = {r["live_id"] for r in world["rooms"] if r["live_id"]}
    assert live and live <= classic_ids | {"palace_theater"}, live - classic_ids
    # the dressing room is where the audio rule applies: its id must match the runtime's
    assert next(r for r in world["rooms"] if r["id"] == "dressing_room")["live_id"] == "dressing"


# ── Browser: the walker inside the real host ─────────────────────────────────

sync_api = pytest.importorskip("playwright.sync_api")

SPY = """
(() => {
  const Native = window.WebSocket;
  window.__wsSent = []; window.__wsGot = [];
  window.WebSocket = class extends Native {
    constructor(...a) {
      super(...a);
      this.addEventListener('message', e => { try { window.__wsGot.push(JSON.parse(e.data)); } catch (err) {} });
    }
    send(d) { try { window.__wsSent.push(JSON.parse(d)); } catch (err) {} return super.send(d); }
  };
})();
"""


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as p:
        try:
            b = p.chromium.launch(args=["--no-sandbox"])
        except Exception as exc:  # no browser installed for this Playwright
            pytest.skip(f"no Chromium available: {exc}")
        yield b
        b.close()


@pytest.fixture()
def page(browser):
    pg = browser.new_page(viewport={"width": 1400, "height": 860})
    pg.problems = []
    pg.on("pageerror", lambda e: pg.problems.append(str(e)))
    pg.add_init_script(SPY)
    yield pg
    pg.close()


@pytest.fixture()
def signed_in(page, owner):
    """A page whose Reach session is the owner's, saved the way login.html saves it (ReachAuth.saveSession)."""
    import json
    session = json.dumps({"token": owner["access_token"], "user": owner.get("username") or "walk-owner", "role": owner.get("role") or "owner"})
    page.add_init_script(f"""
      (s => {{
        if (!sessionStorage.getItem('pubcast_token')) {{
          sessionStorage.setItem('pubcast_token', s.token);
          sessionStorage.setItem('pubcast_user', JSON.stringify({{username: s.user, user_id: s.user, role: s.role}}));
        }}
      }})({session});
    """)
    return page


def _open(page, url):
    page.goto(url)
    page.wait_for_function("document.documentElement.dataset.ready === '1' && !!window.PubCastLive", timeout=30000)


def _use_hotspot(page, hotspot_id, button):
    page.evaluate("(id) => { const W = window.PubCastWalk; W.showHotspotBubble(W.S.view.hotspots.find(h => h.id === id)); }", hotspot_id)
    page.get_by_role("button", name=button, exact=True).click()
    page.wait_for_function("() => { const b = document.getElementById('bubble'); return !b.hidden && !/Working/.test(b.textContent); }", timeout=15000)
    return page.evaluate("() => ({ title: document.querySelector('#bubble h3').textContent, body: (document.querySelector('#bubble p') || {}).textContent || '' })")


def test_the_walker_joins_the_pubworld_socket_and_the_host_acknowledges_its_rooms(host, signed_in):
    page = signed_in
    _open(page, host + "/walk?live=dressing")
    assert page.evaluate("window.PubCastWalk.S.room.id") == "dressing_room"
    page.wait_for_function("window.PubCastLive.state.online === true", timeout=15000)
    assert page.locator("#chipLive").inner_text().endswith("Connected")
    page.wait_for_function("window.__wsGot.some(m => m.type === 'room_ack' && m.room === 'dressing')", timeout=10000)
    # walking through a door is a room change the host hears about, under the id the rest of PubCast uses
    page.evaluate("window.PubCastWalk.goTo('green_room', 'dressing_room')")
    page.wait_for_function("window.__wsGot.some(m => m.type === 'room_ack' && m.room === 'greenroom')", timeout=10000)
    sent = page.evaluate("window.__wsSent.filter(m => m.type === 'room_change').map(m => [m.room, m.world_room])")
    assert ["greenroom", "green_room"] in sent
    assert page.problems == []


def test_the_room_audio_rule_follows_the_walker(host, signed_in):
    page = signed_in
    _open(page, host + "/walk?live=greenroom")
    page.wait_for_function("window.PubCastLive.state.online === true && !!window.PubcastProgramAudio", timeout=15000)
    page.wait_for_function("window.PubcastProgramAudio.room === 'greenroom'", timeout=10000)
    page.evaluate("window.PubCastWalk.goTo('dressing_room', 'green_room')")
    page.wait_for_function("window.PubcastProgramAudio.room === 'dressing'", timeout=10000)
    assert page.evaluate("window.PubcastProgramAudio.allowed()") is False                      # only director announcements
    assert page.evaluate("window.PubcastProgramAudio.allowed({directorAnnouncement: true})") is True
    # a close-up inside the dressing room is the same room: no new room change
    before = page.evaluate("window.__wsSent.filter(m => m.type === 'room_change').length")
    page.evaluate("window.PubCastWalk.setView('dressing_room', 'corkboard', {})")
    page.wait_for_function("window.PubCastWalk.S.view.id === 'corkboard'")
    assert page.evaluate("window.PubcastProgramAudio.room") == "dressing"
    assert page.evaluate("window.__wsSent.filter(m => m.type === 'room_change').length") == before + 1  # view update, same room
    assert page.evaluate("window.__wsSent.filter(m => m.type === 'room_change').pop().room") == "dressing"
    assert page.problems == []


def test_dressing_room_hotspots_run_on_the_host(host, signed_in):
    page = signed_in
    _open(page, host + "/walk?live=dressing")
    page.wait_for_function("window.PubCastLive.state.online === true", timeout=15000)
    typed = _use_hotspot(page, "typewriter", "Use it here")
    assert typed["title"] == "Typewriter" and "Script draft" in typed["body"]
    page.get_by_role("button", name="My scripts", exact=True).click()
    page.wait_for_function("document.querySelector('#bubble h3').textContent === 'Scripts'", timeout=15000)
    assert "Draft" in page.evaluate("document.querySelector('#bubble p').textContent")
    worn = _use_hotspot(page, "wardrobe", "Use")
    assert worn["title"] == "Wardrobe"
    page.get_by_role("button", name="Formal Suit", exact=True).click()
    page.wait_for_function("/Wearing: Formal Suit/.test(document.querySelector('#bubble p').textContent)", timeout=15000)
    board = _use_hotspot(page, "message-board", "Use it here")      # it also opens the corkboard close-up
    assert board["title"] == "Message board" and "Stage Manager" in board["body"]
    look = _use_hotspot(page, "makeup-station", "Use it here")
    assert look["title"] == "Hair and makeup" and "Natural" in look["body"]
    # the walker sends the same hotspot call world.html makes
    calls = page.evaluate("window.__wsSent.filter(m => m.type === 'hotspot').map(m => [m.action, m.room])")
    assert ["typewriter", "dressing"] in calls and ["wardrobe", "dressing"] in calls
    assert page.problems == []


def test_sitting_and_the_tv_in_the_green_room(host, signed_in):
    page = signed_in
    _open(page, host + "/walk?live=greenroom")
    page.wait_for_function("window.PubCastLive.state.online === true", timeout=15000)
    sat = _use_hotspot(page, "couch-sit-left", "Use")
    assert sat["title"] == "Take a seat" and "left curve" in sat["body"]
    tv = _use_hotspot(page, "tv", "Use")
    assert tv["title"] == "TV" and tv["body"].startswith("Channel: ")
    first = tv["body"]
    page.get_by_role("button", name="Flip channel", exact=True).click()
    page.wait_for_function("(b) => document.querySelector('#bubble p').textContent !== b", arg=first, timeout=15000)
    assert page.problems == []


def test_hotspots_the_host_has_no_action_for_stay_local(host, signed_in):
    page = signed_in
    _open(page, host + "/walk?live=controlroom")
    page.evaluate("() => { const W = window.PubCastWalk; W.showHotspotBubble(W.S.view.hotspots.find(h => h.id === 'director-console')); }")
    assert page.get_by_role("button", name="Use", exact=True).count() == 0
    assert "Not wired yet" in page.locator("#bubble p").inner_text()
    assert page.problems == []


def test_classic_pubworld_and_the_walker_hop_to_each_other_at_the_same_room(host, signed_in):
    page = signed_in
    page.goto(host + "/world?room=greenroom")
    page.wait_for_function("document.getElementById('walk-link').getAttribute('href') === '/walk?live=greenroom'", timeout=15000)
    page.click("#walk-link")
    page.wait_for_function("document.documentElement.dataset.ready === '1' && !!window.PubCastWalk", timeout=30000)
    assert page.evaluate("window.PubCastWalk.S.room.id") == "green_room"
    assert page.locator("#classicLink").get_attribute("href") == "/world?room=greenroom"
    assert page.problems == []


def test_without_the_host_behind_it_the_walker_says_so_and_keeps_walking(page, tmp_path):
    # the same page served by a plain file server: no socket, no hotspot API
    port = _free_port()
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=str(ROOT),
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                httpx.get(f"http://127.0.0.1:{port}/static/world_walk.html", timeout=0.3); break
            except httpx.RequestError:
                time.sleep(0.1)
        _open(page, f"http://127.0.0.1:{port}/static/world_walk.html?live=dressing")
        page.wait_for_function("window.PubCastLive.state.host === false", timeout=10000)
        assert page.evaluate("window.PubCastLive.state.online") is False
        assert page.evaluate("!window.PubcastProgramAudio")                # no host: no room-audio polling
        assert page.locator("#chipLive").inner_text().endswith("Offline")
        got = _use_hotspot(page, "wardrobe", "Use")
        assert got["title"] == "Not connected" and "Walking still works" in got["body"]
        assert page.problems == []
    finally:
        srv.terminate(); srv.wait(5)


def test_bella_faux_pas_studio_opens_from_the_foresight_counter_in_the_dressing_room(host, counter_entry_page, owner, fresh_studio_progress):
    """The Counter is the program's front door: its menu opens the walker in a tray, live, under the same session.
    Uses a plain page (no WebSocket recorder: the Counter does not start under it)."""
    import json
    page = counter_entry_page
    page.add_init_script("sessionStorage.setItem('pubcast_token', %s); sessionStorage.setItem('pubcast_user', JSON.stringify({username: 'walk-owner', user_id: 'walk-owner', role: 'owner'}));" % json.dumps(owner["access_token"]))
    # ?once: no continuous animation loop (software graphics here cannot keep up with it); fresh, nosave: a clean Counter
    page.goto(host + "/foresight-counter?once&fresh&nosave")
    try:
        page.wait_for_function("!!window.__programs && !!window.__counter", timeout=30000)
    except Exception:
        pytest.fail(f"the Counter did not start: now at {page.url}; page errors {page.problems}")
    # File > Open... is the Counter's way to open a program: its picker must offer the walker
    page.evaluate("window.__counter.openPicker(null)")
    entry = page.get_by_text("Bella Faux Pas Studio", exact=True)
    entry.first.wait_for(timeout=10000)
    assert entry.count() == 1
    entry.first.evaluate("el => (el.closest('button,[role=button],li') || el).click()")
    page.wait_for_function("() => [...document.querySelectorAll('iframe')].some(f => /\\/walk(\\?|$)/.test(f.getAttribute('src') || ''))", timeout=20000)
    frame = next(f for f in page.frames if "/walk" in f.url)
    frame.wait_for_function("document.documentElement.dataset.ready === '1' && !!window.PubCastLive", timeout=30000)
    frame.wait_for_function("window.PubCastLive.state.online === true", timeout=15000)
    assert frame.evaluate("window.PubCastWalk.S.view.zones.length") > 0
    assert frame.evaluate("window.PubCastWalk.S.room.id") == "dressing_room"        # the studio starts in the dressing room
    assert frame.evaluate("window.PubCastLive.state.room") == "dressing"
    assert page.problems == []



def test_the_studio_starts_in_the_dressing_room_with_no_start_given(host, signed_in, fresh_studio_progress):
    page = signed_in
    _open(page, host + "/walk")
    assert page.evaluate("window.PubCastWalk.S.room.id") == "dressing_room"
    assert page.evaluate("window.PubCastWalk.S.world.start") == "dressing_room"
    page.wait_for_function("window.PubCastLive.state.online === true", timeout=15000)
    page.wait_for_function("window.__wsGot.some(m => m.type === 'room_ack' && m.room === 'dressing')", timeout=10000)
    assert page.problems == []

`````

## tests/test_foresight_reach_runtime.py

SHA-256: 87f1e6d2df76c6d999fd02381fa04d507fb68e3fdd5b5616cf077cce96b8848d

`````text
"""Counter routing and identity checks through the real Reach ASGI lifespan.

Uses the repository's isolated-data client fixture. No service or model response
is substituted. This does not test network binding, a physical GPU or inference.
"""

from pathlib import Path

from modules.auth import create_access_token


def test_counter_and_character_services_with_real_startup(request, monkeypatch):
    monkeypatch.setenv("PUBCAST_ENFORCE_AUTH", "1")
    client = request.getfixturevalue("client")
    headers = {
        "Authorization": "Bearer "
        + create_access_token({"sub": "audit-owner", "role": "owner"})
    }
    page = client.get("/foresight-counter")
    assert page.status_code == 200
    assert (
        page.content
        == (
            Path(__file__).resolve().parents[1] / "static/foresight_counter.html"
        ).read_bytes()
    )
    assert client.get("/static/foresight_counter.js").status_code == 200
    for path in ["/api/pubpartner/status", "/api/foresight/bridge/api/chat/characters"]:
        assert client.get(path).status_code == 401, path
        response = client.get(path, headers=headers)
        assert response.status_code == 200, (path, response.text)
    health = client.get("/api/foresight/bridge/health")
    assert health.status_code == 200 and health.json()["ok"]
    assert health.json()["services"]["character_count"] > 0

`````
