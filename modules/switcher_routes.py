from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from .cameras import CameraManager
from .director_engine import AutonomousDirector

class SwitcherService:
    def __init__(self, cameras:CameraManager, *, director:Optional[AutonomousDirector]=None, recording:Any=None):
        self.cameras=cameras; self.director=director or AutonomousDirector(); self.recording=recording
        self.transition={"type":"cut","duration_ms":0}
        self.scenes: Dict[str,dict]={}
        self.director.sync_from_camera_manager(cameras)

    def state(self)->dict:
        p=self.cameras.get_program_source(); v=self.cameras.get_preview_source()
        return {"program":getattr(p,"source_id",None),"preview":getattr(v,"source_id",None),
                "transition":dict(self.transition),"sources":[{"id":c.source_id,"name":c.name,"transport":c.transport.value,"endpoint":c.endpoint} for c in self.cameras.list_sources()]}
    def preview(self,camera_id:str)->bool: return self.cameras.set_preview_source(camera_id)
    def cut(self,camera_id:Optional[str]=None)->bool:
        target=camera_id or (self.cameras.get_preview_source().source_id if self.cameras.get_preview_source() else None)
        if not target: return False
        ok=self.cameras.set_program_source(target)
        if ok: self.director.manual_cut(target)
        return ok
    def auto(self, camera_id:Optional[str]=None, *, transition:str="dissolve", duration_ms:int=350)->bool:
        self.transition={"type":transition,"duration_ms":max(0,int(duration_ms))}
        return self.cut(camera_id)


def create_switcher_router(service:SwitcherService)->APIRouter:
    r=APIRouter(prefix="/api/switcher",tags=["Director Switcher"])
    @r.get("/state")
    async def state(): return service.state()
    @r.post("/preview/{camera_id}")
    async def preview(camera_id:str):
        if not service.preview(camera_id): raise HTTPException(404,"camera not found")
        return service.state()
    @r.post("/cut")
    async def cut_preview():
        if not service.cut(): raise HTTPException(409,"no preview camera")
        return service.state()
    @r.post("/cut/{camera_id}")
    async def cut(camera_id:str):
        if not service.cut(camera_id): raise HTTPException(404,"camera not found")
        return service.state()
    @r.post("/transition")
    async def transition(body:Dict[str,Any]):
        camera_id=body.get("camera_id")
        if not service.auto(camera_id,transition=str(body.get("type") or "dissolve"),duration_ms=int(body.get("duration_ms") or 350)):
            raise HTTPException(404,"camera not found or preview unset")
        return service.state()
    @r.post("/ptz/{camera_id}")
    async def ptz(camera_id:str,body:Dict[str,Any]):
        try:
            ok=service.cameras.update_pose(camera_id,position=body.get("position"),rotation=body.get("rotation"),fov=body.get("fov"))
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from None
        if not ok: raise HTTPException(404,"camera not found")
        return service.state()
    @r.get("/scenes")
    async def scenes(): return {"scenes":service.scenes}
    return r
