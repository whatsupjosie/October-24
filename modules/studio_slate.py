"""Director-owned production slate, roll call and live floor microphone.

Slate state survives restart. Readiness belongs to the assigned participant;
editor delegation never grants microphone or director delegation rights.
"""
from __future__ import annotations
import asyncio
import copy
import json
import math
import sqlite3
import time
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, ConfigDict
from modules.auth import role_gte
from modules.route_security import current_identity, authorize_websocket


class SlateCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str
    revision: int | None = None
    data: dict = Field(default_factory=dict)


class SlateStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS slates (id TEXT PRIMARY KEY, state TEXT NOT NULL)')
        self.lock = asyncio.Lock()

    def connect(self):
        return sqlite3.connect(self.path)

    def current(self):
        with self.connect() as db:
            row = db.execute('SELECT state FROM slates ORDER BY rowid DESC LIMIT 1').fetchone()
        return json.loads(row[0]) if row else None

    def save(self, state):
        with self.connect() as db:
            db.execute('INSERT INTO slates VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET state=excluded.state',
                       (state['id'], json.dumps(state)))

    def command(self, command: SlateCommand, identity: dict):
        # Revision checks and writes share one SQLite transaction, including
        # callers in another worker process. A stale editor cannot overwrite.
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            return self._command(command, identity, db)

    def _command(self, command: SlateCommand, identity: dict, db):
        actor = identity['user_id']
        row = db.execute('SELECT state FROM slates ORDER BY rowid DESC LIMIT 1').fetchone()
        s = json.loads(row[0]) if row else None
        action, data = command.action, command.data
        if action == 'create':
            if not role_gte(identity['role'], 'mod'):
                raise HTTPException(403, 'Director privileges required to open a production')
            if s and s['phase'] != 'ended':
                raise HTTPException(409, 'The current director must end the active production first')
            s = {'id': str(uuid.uuid4()), 'director_id': actor, 'editors': [], 'revision': 0,
                 'phase': 'idle', 'visible': False, 'clap_at': None,
                 'fields': {'production': '', 'scene': '1', 'take': '1', 'actors': '', 'notes': ''},
                 'departments': {}, 'crew': [], 'history': [], 'sync_status': 'media_alignment_unverified'}
        else:
            if not s or s['phase'] == 'ended':
                raise HTTPException(409, 'No active production')
            if command.revision != s['revision']:
                raise HTTPException(409, 'Slate changed; refresh before retrying')
            director = actor == s['director_id']
            editor = director or actor in s['editors']
            if action == 'ready':
                department = data.get('department')
                if not isinstance(department, str):
                    raise HTTPException(422, 'department must be text')
                entry = s['departments'].get(department)
                if not entry or entry['user_id'] != actor:
                    raise HTTPException(403, 'Only the assigned participant can report readiness')
                if s['phase'] != 'standby':
                    raise HTTPException(409, 'Roll call is not open')
                if not isinstance(data.get('ready'), bool):
                    raise HTTPException(422, 'ready must be a boolean')
                entry.update(ready=data['ready'], checked_at=time.time())
            else:
                if not editor:
                    raise HTTPException(403, 'Only the director or a delegated assistant can edit the slate')
                if action == 'edit':
                    fields = data.get('fields', {})
                    if not isinstance(fields, dict) or set(fields) - set(s['fields']):
                        raise HTTPException(422, 'Unknown slate field')
                    for key, value in fields.items():
                        if not isinstance(value, str) or len(value) > 8000:
                            raise HTTPException(422, 'Slate fields must be text up to 8000 characters')
                    s['fields'].update(fields)
                elif action == 'delegate':
                    if not director:
                        raise HTTPException(403, 'Only the director can delegate editing')
                    editors = data.get('editors')
                    if not isinstance(editors, list) or len(editors) > 20 or any(not isinstance(v, str) or not v.strip() or len(v) > 128 for v in editors):
                        raise HTTPException(422, 'Provide up to 20 assistant account IDs')
                    s['editors'] = sorted(set(editors) - {actor})
                elif action == 'departments':
                    entries = data.get('departments')
                    if not isinstance(entries, dict) or len(entries) > 40:
                        raise HTTPException(422, 'Provide a department to account ID mapping')
                    if any(not isinstance(k, str) or not k.strip() or len(k) > 80 or not isinstance(v, str) or not v.strip() or len(v) > 128 for k, v in entries.items()):
                        raise HTTPException(422, 'Invalid department assignment')
                    s['departments'] = {k: {'user_id': v, 'ready': False, 'checked_at': None} for k, v in entries.items()}
                elif action == 'standby':
                    s.update(visible=True, phase='standby', clap_at=None)
                    for entry in s['departments'].values():
                        entry.update(ready=False, checked_at=None)
                elif action == 'clap':
                    if s['phase'] != 'standby':
                        raise HTTPException(409, 'Call standby before clapping')
                    if any(not e['ready'] for e in s['departments'].values()):
                        raise HTTPException(409, 'Departments are still checking in')
                    s.update(phase='take', clap_at=time.time() + 1.2, visible=True)
                elif action == 'hide':
                    s['visible'] = False
                elif action == 'end':
                    if not director:
                        raise HTTPException(403, 'Only the director can end the production')
                    s.update(phase='ended', visible=False)
                elif action == 'crew':
                    crew = data.get('crew')
                    allowed = {'label', 'role', 'profile', 'instructions', 'flight_pattern', 'enabled'}
                    if not isinstance(crew, list) or len(crew) > 20:
                        raise HTTPException(422, 'Provide up to 20 session crew assignments')
                    for item in crew:
                        if not isinstance(item, dict) or set(item) - allowed or not isinstance(item.get('enabled'), bool):
                            raise HTTPException(422, 'Invalid crew assignment')
                        if any(not isinstance(v, str) or len(v) > 8000 for k, v in item.items() if k != 'enabled'):
                            raise HTTPException(422, 'Crew instructions must be text')
                    # Deliberately never touches cartridge/personality/memory stores.
                    s['crew'] = copy.deepcopy(crew)
                else:
                    raise HTTPException(422, 'Unknown slate action')
        s['revision'] += 1
        s['updated_at'] = time.time()
        s['history'].append({'action': action, 'actor': actor, 'at': s['updated_at'], 'clap_at': s['clap_at']})
        s['history'] = s['history'][-200:]
        db.execute('INSERT INTO slates VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET state=excluded.state',
                   (s['id'], json.dumps(s)))
        return s


def create_slate_router(path: Path):
    router = APIRouter()
    store = SlateStore(path)
    peers: set[WebSocket] = set()
    peer_locks: dict[WebSocket, asyncio.Lock] = {}

    async def authenticated(identity=Depends(current_identity)):
        if not identity.get('authenticated'):
            raise HTTPException(401, 'Sign in to join the production floor')
        return identity

    def view(s, identity):
        return {'slate': s, 'server_time': time.time(), 'user_id': identity['user_id'],
                'can_edit': bool(s and (identity['user_id'] == s['director_id'] or identity['user_id'] in s['editors'])),
                'is_director': bool(s and identity['user_id'] == s['director_id'])}

    async def send(peer, message):
        async def write():
            async with peer_locks[peer]:
                await peer.send_json(message)
        try:
            await asyncio.wait_for(write(), timeout=.25)
        except Exception:
            peers.discard(peer)
            try:
                await asyncio.wait_for(peer.close(code=1013), timeout=.1)
            except Exception:
                pass

    @router.get('/api/studio/slate')
    async def get_slate(identity=Depends(authenticated)):
        return view(store.current(), identity)

    @router.post('/api/studio/slate')
    async def command(body: SlateCommand, identity=Depends(authenticated)):
        async with store.lock:
            s = store.command(body, identity)
        # Clients fetch personalized permissions rather than trusting broadcast roles.
        await asyncio.gather(*(send(p, {'type': 'slate_changed'}) for p in tuple(peers)))
        return view(s, identity)

    @router.websocket('/studio/slate/live')
    async def live(ws: WebSocket):
        identity = await authorize_websocket(ws)
        if not identity or not identity.get('authenticated'):
            if identity:
                await ws.close(code=1008)
            return
        origin = ws.headers.get('origin')
        if origin and origin.split('://', 1)[-1] != ws.headers.get('host'):
            await ws.close(code=1008)
            return
        await ws.accept()
        peers.add(ws)
        peer_locks[ws] = asyncio.Lock()
        window, frames = time.monotonic(), 0
        try:
            while True:
                raw = await ws.receive_text()
                if len(raw) > 14000:
                    await ws.close(code=1009)
                    break
                try:
                    packet = json.loads(raw)
                except ValueError:
                    await ws.close(code=1008)
                    break
                s = store.current()
                if not s or not s['visible'] or s['phase'] == 'ended' or identity['user_id'] != s['director_id']:
                    await ws.close(code=1008, reason='Only the director can transmit floor voice')
                    break
                now = time.monotonic()
                if now - window >= 1:
                    window, frames = now, 0
                frames += 1
                samples = packet.get('samples') if isinstance(packet, dict) else None
                if frames > 40 or not isinstance(samples, list) or not 1 <= len(samples) <= 2048 or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or abs(v) > 1 for v in samples):
                    await ws.close(code=1008, reason='Invalid microphone frame')
                    break
                # Fixed 16kHz mono PCM, no URLs, no synthesized speech, no disk recording.
                await asyncio.gather(*(send(p, {'type': 'director_voice', 'slate_id': s['id'], 'samples': samples, 'sample_rate': 16000}) for p in tuple(peers) if p is not ws))
        except WebSocketDisconnect:
            pass
        finally:
            peers.discard(ws)
            peer_locks.pop(ws, None)

    router.slate_store = store
    return router


class SlateOverlayMiddleware:
    """Add the floor overlay to HTML, inside compression and outside static routes."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope.get('method') == 'HEAD':
            return await self.app(scope, receive, send)
        if scope.get('path', '').endswith('.html') or any(k == b'accept' and b'text/html' in v for k, v in scope.get('headers', [])):
            scope = dict(scope, headers=[(k, v) for k, v in scope.get('headers', []) if k not in {b'if-none-match', b'if-modified-since'}])
        start, chunks, transform = None, [], False
        async def wrapped(message):
            nonlocal start, transform
            if message['type'] == 'http.response.start':
                headers = dict(message.get('headers', []))
                transform = message['status'] == 200 and b'text/html' in headers.get(b'content-type', b'') and b'content-encoding' not in headers
                if transform:
                    start = message
                    return
            if message['type'] == 'http.response.body' and transform:
                chunks.append(message.get('body', b''))
                if message.get('more_body'):
                    return
                body = b''.join(chunks)
                tag = b'<link rel="stylesheet" href="/static/studio_slate.css"><script defer src="/static/studio_slate.js"></script>'
                if b'/static/studio_slate.js' not in body:
                    index = body.lower().find(b'</head>')
                    body = body[:index] + tag + body[index:] if index >= 0 else body + tag
                start['headers'] = [(k, v) for k, v in start['headers'] if k.lower() not in {b'content-length', b'etag', b'last-modified'}] + [(b'content-length', str(len(body)).encode())]
                await send(start)
                await send({'type': 'http.response.body', 'body': body})
                return
            await send(message)
        await self.app(scope, receive, wrapped)
