"""Director-owned production slate, roll call and live floor microphone.

Slate state survives restart. Readiness belongs to the assigned participant;
editor delegation never grants microphone or director delegation rights.
"""
from __future__ import annotations
import asyncio
import copy
import hashlib
import json
import math
import sqlite3
import time
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse
from modules.recorded_slate_sync import align, SyncError
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

    analysis_lock = asyncio.Lock()
    takes_dir = path.parent / 'production_takes'

    def take_owner(slate_id, identity):
        with store.connect() as db:
            row = db.execute('SELECT state FROM slates WHERE id=?', (slate_id,)).fetchone()
        if not row:
            raise HTTPException(404, 'Production not found')
        s = json.loads(row[0])
        if identity['user_id'] != s['director_id'] and identity['user_id'] not in s['editors']:
            raise HTTPException(403, 'Director or delegated assistant required')
        return s

    @router.post('/api/studio/slate/takes/{slate_id}')
    async def save_take(slate_id: str, request: Request, identity=Depends(authenticated)):
        s = take_owner(slate_id, identity)
        media_type = request.headers.get('content-type', '').split(';', 1)[0]
        if media_type not in {'video/webm', 'video/mp4'}:
            raise HTTPException(415, 'Upload a WebM or MP4 recording')
        if analysis_lock.locked():
            raise HTTPException(429, 'A take is being processed; your local recording is safe to retry')
        async with analysis_lock:
            folder = takes_dir / s['id'] / str(uuid.uuid4())
            folder.mkdir(parents=True)
            original = folder / ('original.webm' if media_type == 'video/webm' else 'original.mp4')
            digest = hashlib.sha256();size = 0
            try:
                with original.open('xb') as output:
                    async for chunk in request.stream():
                        size += len(chunk)
                        if size > 128 * 1024 * 1024:
                            raise HTTPException(413, 'Take exceeds 128 MiB; the local original is retained')
                        output.write(chunk);digest.update(chunk)
                if not size:
                    raise HTTPException(400, 'Empty recording')
            except BaseException:
                original.unlink(missing_ok=True)
                folder.rmdir()
                raise
            report = {'take_id': folder.name, 'slate_id': s['id'], 'fields': s['fields'],
                'clap_at': s['clap_at'], 'original_sha256': digest.hexdigest(), 'original_bytes': size, 'original_filename': original.name,
                'created_at': time.time(), 'status': 'unverified',
                'original_url': f'/api/studio/slate/takes/{s["id"]}/{folder.name}/original'}
            try:
                report.update(await asyncio.to_thread(align, original, folder / 'aligned.mp4'))
                report['aligned_url'] = f'/api/studio/slate/takes/{s["id"]}/{folder.name}/aligned'
                report['aligned_sha256'] = await asyncio.to_thread(lambda: hashlib.sha256((folder / 'aligned.mp4').read_bytes()).hexdigest())
            except SyncError as exc:
                report['reason'] = str(exc)
            (folder / 'sync.json').write_text(json.dumps(report, indent=2))
            return report

    @router.get('/api/studio/slate/takes/{slate_id}')
    async def list_takes(slate_id: str, identity=Depends(authenticated)):
        s = take_owner(slate_id, identity)
        reports = sorted((takes_dir / s['id']).glob('*/sync.json'), key=lambda p: p.stat().st_mtime, reverse=True)
        return {'takes': [json.loads(p.read_text()) for p in reports[:50]]}

    @router.post('/api/studio/slate/takes/{slate_id}/{take_id}/timing')
    async def save_timing(slate_id: str, take_id: str, request: Request, identity=Depends(authenticated)):
        s = take_owner(slate_id, identity)
        try:
            if str(uuid.UUID(take_id)) != take_id:
                raise ValueError()
        except ValueError:
            raise HTTPException(404, 'Take not found')
        folder = takes_dir / s['id'] / take_id
        if not (folder / 'sync.json').is_file():
            raise HTTPException(404, 'Take not found')
        raw = await request.body()
        if len(raw) > 256 * 1024:
            raise HTTPException(413, 'Timing report is too large')
        try:
            timing = json.loads(raw)
            clap = timing.get('clap_audio_seconds')
            if clap is not None and (isinstance(clap, bool) or not isinstance(clap, (int, float)) or not math.isfinite(clap) or not 0 <= clap <= 7200):raise ValueError()
            report = json.loads((folder / 'sync.json').read_text())
            if not (timing['schema'] == 'pubcast.timing.v1'):raise ValueError()
            if not (timing['original_sha256'] == report['original_sha256']):raise ValueError()
            if not (timing['cadence_seconds'] == 15 and timing['periodic_audio_added'] is False):raise ValueError()
            if not (timing['clock'] == 'browser_audio_context'):raise ValueError()
            if not (timing['sample_rate'] in {16000, 22050, 24000, 44100, 48000, 96000}):raise ValueError()
            points = timing['checkpoints']
            if not (isinstance(points, list) and 1 <= len(points) <= 5000):raise ValueError()
            previous = -1
            for index, point in enumerate(points):
                if not (point['target_seconds'] == index * 15):raise ValueError()
                for key in ['audio_seconds', 'audio_sample', 'compositor_frame', 'performance_ms', 'late_ms']:
                    value = point[key]
                    if not (not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value >= 0):raise ValueError()
                if not (point['audio_seconds'] >= previous):raise ValueError()
                if not (abs(point['audio_sample'] - round(point['audio_seconds'] * timing['sample_rate'])) <= 1):raise ValueError()
                previous = point['audio_seconds']
        except (AssertionError, KeyError, TypeError, ValueError):
            raise HTTPException(422, 'Invalid silent checkpoint report')
        timing['scope'] = 'browser_clock_edit_markers; not independent hardware drift certification'
        if report.get('before') and isinstance(timing.get('clap_audio_seconds'), (int, float)):
            timing['encoded_audio_origin_seconds'] = report['before']['audio_marker_seconds'] - timing['clap_audio_seconds']
        result = {'saved': True, 'checkpoint_count': len(points), 'periodic_audio_added': False}
        prefix = f'/api/studio/slate/takes/{s["id"]}/{take_id}/'
        result.update(reference_url=prefix+'stem-reference', editing_url=prefix+'editing')
        (folder / 'timing.json').write_text(json.dumps(timing, indent=2))
        return result

    stem_names = {'dialogue': 2, 'music': 2, 'sfx': 2, 'ui': 2, 'vtr': 2, 'room': 2, 'floor': 1, 'reference': 1}

    @router.post('/api/studio/slate/takes/{slate_id}/{take_id}/stem/{name}')
    async def save_stem(slate_id: str, take_id: str, name: str, request: Request, identity=Depends(authenticated)):
        import wave
        s = take_owner(slate_id, identity)
        if name not in stem_names:
            raise HTTPException(404, 'Unknown audio stem')
        try:
            if str(uuid.UUID(take_id)) != take_id:raise ValueError()
        except ValueError:
            raise HTTPException(404, 'Take not found')
        folder = takes_dir / s['id'] / take_id
        if not (folder / 'sync.json').is_file():raise HTTPException(404, 'Take not found')
        file = folder / ('stem-' + name + '.wav')
        if file.exists():raise HTTPException(409, 'Stem already saved; original is preserved')
        size = 0
        try:
            with file.open('xb') as output:
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > 128 * 1024 * 1024:raise HTTPException(413, 'Stem is too large')
                    output.write(chunk)
            with wave.open(str(file)) as wav:
                if wav.getnchannels() != stem_names[name] or wav.getsampwidth() != 2 or wav.getframerate() not in {16000, 22050, 24000, 44100, 48000, 96000}:
                    raise ValueError('Invalid stem format')
                expected = wav.getnframes() * wav.getnchannels() * wav.getsampwidth()
                decoded = 0
                while True:
                    block = wav.readframes(65536)
                    if not block:break
                    decoded += len(block)
                if decoded != expected:raise ValueError('Truncated PCM stem')
                metadata = {'name': name, 'channels': wav.getnchannels(), 'sample_rate': wav.getframerate(), 'sample_frames': wav.getnframes(), 'default_muted': name == 'reference'}
            (folder / ('stem-' + name + '.json')).write_text(json.dumps(metadata))
            return metadata
        except BaseException as exc:
            file.unlink(missing_ok=True)
            if isinstance(exc, (ValueError, wave.Error, EOFError)):raise HTTPException(422, 'Invalid PCM WAV stem')
            raise

    @router.post('/api/studio/slate/takes/{slate_id}/{take_id}/stems')
    async def finish_stems(slate_id: str, take_id: str, identity=Depends(authenticated)):
        from modules.recorded_slate_sync import stem_manifest, build_stem_edit_copy
        s = take_owner(slate_id, identity)
        try:
            if str(uuid.UUID(take_id)) != take_id:raise ValueError()
        except ValueError:
            raise HTTPException(404, 'Take not found')
        folder = takes_dir / s['id'] / take_id
        if not (folder / 'sync.json').is_file():raise HTTPException(404, 'Take not found')
        try:
            manifest = await asyncio.to_thread(stem_manifest, folder)
            await asyncio.to_thread(build_stem_edit_copy, folder, manifest)
        except SyncError as exc:
            raise HTTPException(422, str(exc))
        prefix = f'/api/studio/slate/takes/{s["id"]}/{take_id}/'
        for stem in manifest['tracks']:stem['url'] = prefix + 'stem-' + stem['name']
        (folder / 'stems.json').write_text(json.dumps(manifest, indent=2))
        return manifest

    @router.post('/api/studio/slate/takes/{slate_id}/{take_id}/edits')
    async def save_edits(slate_id: str, take_id: str, request: Request, identity=Depends(authenticated)):
        s = take_owner(slate_id, identity)
        try:
            if str(uuid.UUID(take_id)) != take_id:raise ValueError()
        except ValueError:
            raise HTTPException(404, 'Take not found')
        folder = takes_dir / s['id'] / take_id
        if not (folder / 'stems.json').is_file():raise HTTPException(404, 'Take stems not found')
        raw = await request.body()
        if len(raw)>128*1024:raise HTTPException(413, 'Edit decisions too large')
        try:
            edits=json.loads(raw)
            if edits['schema']!='pubcast.take-edits.v1' or edits['cadence_seconds']!=15:raise ValueError()
            enabled=edits.get('enabled_tracks',[n for n in stem_names if n!='reference'])
            if not isinstance(enabled,list) or any(n not in stem_names or n=='reference' for n in enabled):raise ValueError()
            sections=edits['sections']
            if not isinstance(sections,dict) or len(sections)>500:raise ValueError()
            for key,values in sections.items():
                if not key.isdigit() or int(key)>500 or not isinstance(values,dict):raise ValueError()
                for name,value in values.items():
                    if name not in stem_names or isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or abs(value)>2:raise ValueError()
        except (ValueError,TypeError,KeyError):raise HTTPException(422, 'Invalid edit decisions')
        (folder / 'edits.json').write_text(json.dumps(edits,indent=2))
        return {'saved':True,'sections':len(sections),'original_media_preserved':True}

    @router.post('/api/studio/slate/takes/{slate_id}/{take_id}/render')
    async def render_take(slate_id: str, take_id: str, identity=Depends(authenticated)):
        from modules.recorded_slate_sync import render_edits
        s = take_owner(slate_id, identity)
        try:
            if str(uuid.UUID(take_id)) != take_id:raise ValueError()
        except ValueError:
            raise HTTPException(404, 'Take not found')
        folder = takes_dir / s['id'] / take_id
        if not (folder / 'stems.json').is_file():raise HTTPException(404, 'Take stems not found')
        if analysis_lock.locked():raise HTTPException(429, 'A take is already being processed')
        async with analysis_lock:
            try:report=await asyncio.to_thread(render_edits, folder)
            except SyncError as exc:raise HTTPException(422, str(exc))
        report['final_url']=f'/api/studio/slate/takes/{s["id"]}/{take_id}/final'
        (folder/'render.json').write_text(json.dumps(report,indent=2))
        return report

    @router.get('/api/studio/slate/takes/{slate_id}/{take_id}/{version}')
    async def download_take(slate_id: str, take_id: str, version: str, identity=Depends(authenticated)):
        s = take_owner(slate_id, identity)
        try:
            if str(uuid.UUID(take_id)) != take_id:
                raise ValueError()
        except ValueError:
            raise HTTPException(404, 'Take not found')
        filename = {'original': 'original.webm', 'aligned': 'aligned.mp4', 'report': 'sync.json', 'timing': 'timing.json', 'reference': 'sync-reference.wav', 'editing': 'editing.mp4'}.get(version)
        if version.startswith('stem-') and version[5:] in stem_names:
            if not (takes_dir / s['id'] / take_id / (version + '.json')).is_file():
                raise HTTPException(404, 'Stem is not complete')
            filename = version + '.wav'
        if version == 'stems':filename = 'stems.json'
        if version == 'edits':filename = 'edits.json'
        if version == 'preview':filename = 'preview.webm'
        if version == 'final':filename = 'final.mp4'
        if not filename:
            raise HTTPException(404, 'Take version not found')
        folder = takes_dir / s['id'] / take_id
        if version == 'original' and (folder / 'sync.json').is_file():
            filename = json.loads((folder / 'sync.json').read_text()).get('original_filename', 'original.webm')
            if filename not in {'original.webm', 'original.mp4'}:
                raise HTTPException(404, 'Take not found')
        file = folder / filename
        if not file.is_file():
            raise HTTPException(404, 'Take not found')
        return FileResponse(file, filename=take_id + '-' + filename)

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
