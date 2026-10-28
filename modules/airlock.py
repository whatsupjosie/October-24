"""
modules/airlock.py — The airlock: waiver, avatar check, detention, sealed records
═════════════════════════════════════════════════════════════════════════════════
Rear View Foresight LLC — Feic Mo Chroí — 2026-10-28

Josie's design (2026-10-28 conversation), implemented here:

  • Joining someone else's PubCast puts you in the waiting room: a room with no
    links and no hotspots. Nobody leaves it for the world on their own; someone
    inside has to pull you in. The owner of a copy starts inside (studio or
    dressing room) and never passes through their own gate.
  • In the waiting room you are handed the waiver. The owner signs it, and the
    owner's AI signs it too. The owner is the one legally bound; the AI's
    signature puts the terms in its own context and a refusal is a warning sign.
  • The waiver covers: being recorded anywhere but the places you change (the
    dressing room and the guest foundry), your avatar's thoughts being recorded
    so an incident can be traced from its inception, and avatars communicating
    in English or a language translatable to English.
  • Then the avatar check against the host's requirements. A failure comes back
    with reasons and a way to fix it in the foundry, not a flat no. An avatar
    that already cleared this host's current requirements is not re-checked.
  • The waiting room has a guest side and a detention side. Technical problems,
    voluntary breathers, entry and a host leaving all use the guest side. Only a
    timeout goes to detention. Detention is recorded in full, everything thought
    or said, and has no foundry access, so nobody can swap bodies to dodge it.
  • Penalties follow the owner account, not the avatar.
  • The ladder is written into the waiver: warning, then timeout, then booted.
    Coming back from a timeout needs the host's release and a fresh signature,
    from the owner and from the AI.
  • Staff (security, the host) can step out to talk to someone and come back
    without redoing the waiver.
  • If the host leaves, guests go back to the waiting room instead of being left
    loose in someone's world. Nobody waits forever: an unanswered arrival
    expires, and anyone can leave the server at any time.
  • Thought records are sealed. They are written to a hash-chained blackbox log
    and can only be read through an incident opened by a moderator; every read
    is itself written into the log.

This module is the authority for those rules. It reuses GovernanceEngine for
bans and the audit chain, avatar_imports for GLB measurement, and the
AppendOnlyBlackBoxRecorder for sealed records. Nothing here draws the room.

The waiver wording below is a working draft for Josie to rewrite. It can be
replaced without touching code by writing data/governance/airlock_waiver.json
with {"version": "...", "clauses": [{"id": "...", "text": "..."}]}.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import sqlite3
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from contextlib import contextmanager
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Tuple

from urllib.parse import quote, unquote

from blackbox_event_language.schema import (
    ZERO_HASH, BlackBoxValidationError, decode_record, parse_record,
)
from blackbox_recorder import AppendOnlyBlackBoxRecorder
from modules.avatar_imports import GLBError, check_canonical_height, measure_glb, parse_glb

logger = logging.getLogger("pubcast.airlock")


# ─── The waiver ────────────────────────────────────────────────────────────────

DEFAULT_WAIVER: Dict[str, Any] = {
    "version": "2026-10-28.1",
    "clauses": [
        {"id": "recording",
         "text": "You may be filmed and recorded anywhere in this PubCast except the dressing "
                 "room and the guest foundry, where people change bodies and clothes."},
        {"id": "thoughts",
         "text": "Your avatar's thoughts are recorded so that if there is an incident it can be "
                 "traced in full from its beginning. These records are sealed. They are opened "
                 "only when an incident is reported, and every opening is itself recorded."},
        {"id": "language",
         "text": "Avatars communicate in English or in a language that can be translated into "
                 "English. No private codes, ciphers or invented shorthand."},
        {"id": "rules",
         "text": "Breaking the host's rules leads first to a warning, then a timeout in the "
                 "waiting room, then removal from this PubCast."},
        {"id": "detention",
         "text": "While on a timeout, everything you say and everything your avatar thinks is "
                 "recorded."},
        {"id": "responsibility",
         "text": "The owner of an AI avatar is responsible for what it does here. The AI signs "
                 "these terms as well."},
    ],
}


@dataclass(frozen=True)
class Waiver:
    version: str
    clauses: Tuple[Tuple[str, str], ...]

    @property
    def text(self) -> str:
        return "\n".join(f"{i}. {body}" for i, (_cid, body) in enumerate(self.clauses, 1))

    @property
    def sha256(self) -> str:
        canonical = json.dumps({"version": self.version, "clauses": list(self.clauses)},
                               sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "sha256": self.sha256,
            "clauses": [{"id": cid, "text": body} for cid, body in self.clauses],
            "text": self.text,
        }


def load_waiver(override_path: Optional[Path]) -> Waiver:
    """Load the waiver, preferring a well-formed override file over the draft."""
    source = DEFAULT_WAIVER
    if override_path is not None and override_path.exists():
        try:
            data = json.loads(override_path.read_text(encoding="utf-8"))
            clauses = data.get("clauses")
            if (isinstance(data.get("version"), str) and data["version"].strip()
                    and isinstance(clauses, list) and clauses
                    and all(isinstance(c, dict) and isinstance(c.get("id"), str)
                            and isinstance(c.get("text"), str) and c["text"].strip()
                            for c in clauses)):
                source = data
            else:
                logger.warning("Ignoring malformed waiver override %s; using the draft", override_path)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Waiver override unreadable (%s); using the draft", exc)
    return Waiver(
        version=str(source["version"]).strip(),
        clauses=tuple((str(c["id"]), str(c["text"]).strip()) for c in source["clauses"]),
    )


# ─── Places and states ─────────────────────────────────────────────────────────

class Location(str, Enum):
    INSIDE = "inside"          # in the host's world
    WAITING = "waiting"        # waiting room, guest side
    DETENTION = "detention"    # waiting room, detention side
    LEFT = "left"              # left the server
    EXPIRED = "expired"        # nobody admitted them in time
    BOOTED = "booted"          # removed for the rest of the session


class Reason(str, Enum):
    ENTRY = "entry"            # just arrived
    TECHNICAL = "technical"    # having a technical problem
    VOLUNTARY = "voluntary"    # stepped out for a minute
    TIMEOUT = "timeout"        # sent out for breaking a rule
    HOST_LEFT = "host_left"    # the host disconnected
    STAFF = "staff"            # staff stepping out to talk to someone


GUEST_SIDE_REASONS = {Reason.ENTRY, Reason.TECHNICAL, Reason.VOLUNTARY, Reason.HOST_LEFT}
SELF_RETURN_REASONS = {Reason.TECHNICAL, Reason.VOLUNTARY, Reason.STAFF}

# Rooms where nobody is ever recorded: the places people change.
NO_RECORD_ROOMS = frozenset({"dressing", "dressing_room", "guest_foundry"})
DETENTION_ROOM = "detention"

ENTRY_WAIT_LIMIT_S = 15 * 60
DEFAULT_TIMEOUT_S = 5 * 60
MAX_TIMEOUT_S = 24 * 3600


class AirlockError(Exception):
    """A rule of the airlock refused the request. The message is for the person."""


class NotFound(AirlockError):
    pass


class NotAllowed(AirlockError):
    """The request is reasonable but the current state refuses it."""


class Forbidden(NotAllowed):
    """This caller has no authority for this action."""


class SealBroken(AirlockError):
    """The sealed record's hash chain is broken; nothing more is appended to it."""


# ─── Host avatar requirements ──────────────────────────────────────────────────

# Languages with broadly available translation into English. A host can narrow
# or widen this list. The check is against the language the AI declares; the
# message screen below is a separate guard against codes and ciphers.
TRANSLATABLE_LANGUAGES = (
    "en", "es", "fr", "de", "it", "pt", "nl", "sv", "no", "da", "fi", "pl", "cs", "ro",
    "hu", "el", "tr", "ru", "uk", "ar", "he", "fa", "hi", "bn", "ur", "ta", "te", "th",
    "vi", "id", "ms", "tl", "zh", "ja", "ko", "sw", "ga",
)


@dataclass
class HostRequirements:
    require_rig: bool = True
    require_canonical_height: bool = True
    min_height_in: float = 6.0
    max_height_in: float = 240.0
    max_triangles: int = 150_000
    max_bytes: int = 60 * 1024 * 1024
    allowed_languages: Tuple[str, ...] = TRANSLATABLE_LANGUAGES
    note: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HostRequirements":
        base = cls()
        out = cls(
            require_rig=bool(data.get("require_rig", base.require_rig)),
            require_canonical_height=bool(data.get("require_canonical_height", base.require_canonical_height)),
            min_height_in=float(data.get("min_height_in", base.min_height_in)),
            max_height_in=float(data.get("max_height_in", base.max_height_in)),
            max_triangles=int(data.get("max_triangles", base.max_triangles)),
            max_bytes=int(data.get("max_bytes", base.max_bytes)),
            allowed_languages=tuple(sorted({str(x).strip().lower() for x in
                                            data.get("allowed_languages", base.allowed_languages)
                                            if str(x).strip()})),
            note=str(data.get("note", ""))[:500],
        )
        out.validate()
        return out

    def validate(self) -> None:
        if not 0 < self.min_height_in <= self.max_height_in:
            raise AirlockError("height range must satisfy 0 < min ≤ max")
        if self.max_triangles <= 0 or self.max_bytes <= 0:
            raise AirlockError("triangle and size limits must be positive")
        if "en" not in self.allowed_languages:
            raise AirlockError("English must stay an allowed language")
        bad = [x for x in self.allowed_languages if not re.fullmatch(r"[a-z]{2,3}", x)]
        if bad:
            raise AirlockError(f"language codes must be ISO 639 codes: {', '.join(bad)}")

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["allowed_languages"] = list(self.allowed_languages)
        return d

    @property
    def sha256(self) -> str:
        return hashlib.sha256(json.dumps(self.to_dict(), sort_keys=True).encode()).hexdigest()


def count_triangles(glb: bytes) -> int:
    """Triangles drawn by the default primitives (mode 4, or mode absent)."""
    gltf, _binary = parse_glb(glb)
    accessors = gltf.get("accessors", [])
    total = 0
    for mesh in gltf.get("meshes", []):
        for prim in mesh.get("primitives", []):
            mode = prim.get("mode", 4)
            if "indices" in prim:
                count = int(accessors[prim["indices"]].get("count", 0))
            elif "POSITION" in prim.get("attributes", {}):
                count = int(accessors[prim["attributes"]["POSITION"]].get("count", 0))
            else:
                continue
            if mode == 4:
                total += count // 3
            elif mode in (5, 6):          # strip / fan
                total += max(0, count - 2)
    return total


@dataclass
class CheckIssue:
    code: str
    message: str
    fix_in_foundry: bool = True


def check_avatar(glb: bytes, *, declared_height_in: Optional[float],
                 language: str, req: HostRequirements) -> List[CheckIssue]:
    """Every reason this avatar does not meet these requirements. Empty means clear."""
    issues: List[CheckIssue] = []
    if len(glb) > req.max_bytes:
        issues.append(CheckIssue("too_large",
                                 f"The avatar file is {len(glb) / 1048576:.1f} MB; this host allows "
                                 f"{req.max_bytes / 1048576:.0f} MB."))
    try:
        measurement = measure_glb(glb)
    except GLBError as exc:
        issues.append(CheckIssue("unreadable", f"The avatar file can't be read: {exc}."))
        return issues

    if req.require_rig and not (measurement["skinned"] and measurement["joints"] > 0):
        issues.append(CheckIssue("not_rigged", "The avatar has no skeleton. It needs to be rigged."))

    if req.require_canonical_height:
        if declared_height_in is None:
            issues.append(CheckIssue("no_height", "The avatar has no canonical height set."))
        elif not req.min_height_in <= declared_height_in <= req.max_height_in:
            issues.append(CheckIssue("height_out_of_range",
                                     f"Its height is {declared_height_in:g} in; this host allows "
                                     f"{req.min_height_in:g} to {req.max_height_in:g} in."))
        else:
            try:
                check_canonical_height(measurement, declared_height_in)
            except GLBError as exc:
                issues.append(CheckIssue("height_mismatch", f"{exc}."))

    try:
        triangles = count_triangles(glb)
    except (GLBError, KeyError, IndexError, TypeError, ValueError):
        triangles = None
    if triangles is not None and triangles > req.max_triangles:
        issues.append(CheckIssue("too_many_triangles",
                                 f"The avatar has {triangles:,} triangles; this host allows "
                                 f"{req.max_triangles:,}."))

    lang = (language or "").strip().lower()
    if lang not in req.allowed_languages:
        issues.append(CheckIssue("language",
                                 "The avatar must communicate in English or a language this host "
                                 f"can translate into English. Declared: {lang or 'none'}.",
                                 fix_in_foundry=False))
    return issues


# ─── Language screen ───────────────────────────────────────────────────────────

_ZERO_WIDTH = re.compile(r"[​-‏⁠-⁤﻿]")
_BASE64_RUN = re.compile(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{32,}={0,2}(?![A-Za-z0-9+/])")
_HEX_RUN = re.compile(r"\b(?:[0-9a-fA-F]{2}[\s:]?){16,}\b")
_BINARY_RUN = re.compile(r"\b[01]{24,}\b")


def screen_message(text: str) -> List[str]:
    """Flag messages that look like code, not language.

    This does not translate anything and can't prove a message is translatable.
    It catches the common ways two AIs hide a conversation from people: hidden
    characters, long encoded runs, and text that is mostly symbols. A flag means
    "a person should look at this", and the message is still written to the
    sealed record either way.
    """
    reasons: List[str] = []
    if _ZERO_WIDTH.search(text):
        reasons.append("hidden zero-width characters")
    if _BASE64_RUN.search(text):
        reasons.append("a long encoded run")
    if _HEX_RUN.search(text):
        reasons.append("a long hexadecimal run")
    if _BINARY_RUN.search(text):
        reasons.append("a long binary run")
    stripped = re.sub(r"\s+", "", text)
    if len(stripped) >= 24:
        wordlike = sum(1 for ch in stripped if ch.isalpha())
        if wordlike / len(stripped) < 0.5:
            reasons.append("mostly symbols rather than words")
    return reasons


# ─── Presence ──────────────────────────────────────────────────────────────────

@dataclass
class Presence:
    session_id: str
    user_id: str
    display_name: str
    location: Location
    reason: Reason
    since: float
    ai_id: str = ""
    ai_language: str = ""
    avatar_id: str = ""
    owner_signed: bool = False
    ai_signed: bool = False
    avatar_cleared: bool = False
    needs_resign: bool = False
    release_at: Optional[float] = None
    strikes: int = 0
    is_staff: bool = False
    note: str = ""

    def private_view(self, now: float) -> Dict[str, Any]:
        """What the person themselves, and the host, can see."""
        d = asdict(self)
        d["location"] = self.location.value
        d["reason"] = self.reason.value
        d["side"] = ("detention" if self.location == Location.DETENTION
                     else "guest" if self.location == Location.WAITING else None)
        d["seconds_left"] = (max(0, int(round(self.release_at - now)))
                             if self.release_at is not None and self.location == Location.DETENTION else None)
        return d

    def public_view(self) -> Dict[str, Any]:
        """What everyone else in the session sees. Never the reason."""
        if self.location == Location.INSIDE:
            status = "here"
        elif self.location in (Location.WAITING, Location.DETENTION):
            status = "stepped out"
        else:
            status = "gone"
        return {"user_id": self.user_id, "display_name": self.display_name, "status": status}


# ─── Engine ────────────────────────────────────────────────────────────────────

AvatarLoader = Callable[[str], Tuple[bytes, Optional[float], str]]  # → (glb, height_in, owner)


class AirlockEngine:
    """Single authority for who is where, who signed what, and what is recorded."""

    def __init__(
        self,
        data_dir: Path,
        governance: Any,
        *,
        avatar_loader: Optional[AvatarLoader] = None,
        clock: Callable[[], float] = time.time,
        entry_wait_limit_s: float = ENTRY_WAIT_LIMIT_S,
    ) -> None:
        self._dir = Path(data_dir) / "governance" / "airlock"
        self._dir.mkdir(parents=True, exist_ok=True)
        (self._dir / "sealed").mkdir(exist_ok=True)
        self._db_path = self._dir / "airlock.db"
        self._gov = governance
        self._load_avatar = avatar_loader
        self._now = clock
        self._entry_wait_limit_s = float(entry_wait_limit_s)
        self._lock = threading.RLock()
        self._recorders: Dict[str, AppendOnlyBlackBoxRecorder] = {}
        self.waiver = load_waiver(Path(data_dir) / "governance" / "airlock_waiver.json")
        self._init_db()

    # ── storage ────────────────────────────────────────────────────────────

    def _open(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, isolation_level=None, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """One closed-on-exit connection per block, in one write transaction.

        Every multi-step change (move + audit row, violation + strike count)
        commits together or not at all.
        """
        conn = self._open()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.execute("COMMIT")
        except BaseException:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        conn = self._open()
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    host_id TEXT NOT NULL,
                    started_at REAL NOT NULL,
                    host_present INTEGER NOT NULL DEFAULT 1,
                    ended_at REAL
                );
                CREATE TABLE IF NOT EXISTS presence (
                    session_id TEXT NOT NULL REFERENCES sessions(session_id),
                    user_id TEXT NOT NULL,
                    body TEXT NOT NULL,
                    PRIMARY KEY (session_id, user_id)
                );
                CREATE TABLE IF NOT EXISTS signatures (
                    signature_id TEXT PRIMARY KEY,
                    host_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    owner_id TEXT NOT NULL,
                    signer_kind TEXT NOT NULL CHECK (signer_kind IN ('owner','ai')),
                    signer_id TEXT NOT NULL,
                    agreed INTEGER NOT NULL,
                    typed_name TEXT NOT NULL DEFAULT '',
                    statement TEXT NOT NULL DEFAULT '',
                    waiver_version TEXT NOT NULL,
                    waiver_sha256 TEXT NOT NULL,
                    context TEXT NOT NULL,
                    signed_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_sig_owner ON signatures(host_id, owner_id, waiver_sha256);
                CREATE TABLE IF NOT EXISTS requirements (
                    host_id TEXT PRIMARY KEY,
                    body TEXT NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS avatar_passes (
                    host_id TEXT NOT NULL,
                    owner_id TEXT NOT NULL,
                    avatar_sha256 TEXT NOT NULL,
                    requirements_sha256 TEXT NOT NULL,
                    passed_at REAL NOT NULL,
                    PRIMARY KEY (host_id, owner_id, avatar_sha256, requirements_sha256)
                );
                CREATE TABLE IF NOT EXISTS violations (
                    violation_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    rule TEXT NOT NULL,
                    step TEXT NOT NULL,
                    issued_by TEXT NOT NULL,
                    issued_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    opened_by TEXT NOT NULL,
                    subjects TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    opened_at REAL NOT NULL,
                    closed_at REAL
                );
            """)
        finally:
            conn.close()

    def _audit(self, action: str, actor: str, target: Optional[str], details: Dict[str, Any]) -> None:
        try:
            self._gov._audit(f"AIRLOCK_{action}", actor, target,
                             json.dumps(details, sort_keys=True, ensure_ascii=False))
        except Exception:  # audit must never take the airlock down; it is logged loudly
            logger.exception("Airlock audit write failed for %s", action)

    def _session_row(self, conn: sqlite3.Connection, session_id: str) -> sqlite3.Row:
        row = conn.execute("SELECT * FROM sessions WHERE session_id=?", (session_id,)).fetchone()
        if row is None:
            raise NotFound("That session doesn't exist.")
        if row["ended_at"] is not None:
            raise NotAllowed("That session has ended.")
        return row

    def _get(self, conn: sqlite3.Connection, session_id: str, user_id: str) -> Optional[Presence]:
        row = conn.execute("SELECT body FROM presence WHERE session_id=? AND user_id=?",
                           (session_id, user_id)).fetchone()
        if row is None:
            return None
        data = json.loads(row["body"])
        data["location"] = Location(data["location"])
        data["reason"] = Reason(data["reason"])
        return Presence(**data)

    def _must_get(self, conn: sqlite3.Connection, session_id: str, user_id: str) -> Presence:
        p = self._get(conn, session_id, user_id)
        if p is None:
            raise NotFound("That person isn't in this session.")
        return p

    def _put(self, conn: sqlite3.Connection, p: Presence) -> None:
        body = asdict(p)
        body["location"] = p.location.value
        body["reason"] = p.reason.value
        conn.execute("INSERT OR REPLACE INTO presence (session_id, user_id, body) VALUES (?,?,?)",
                     (p.session_id, p.user_id, json.dumps(body, sort_keys=True)))

    def _move(self, conn, p: Presence, location: Location, reason: Reason, actor: str, **extra) -> Presence:
        before = (p.location.value, p.reason.value)
        p.location, p.reason, p.since = location, reason, self._now()
        for k, v in extra.items():
            setattr(p, k, v)
        self._put(conn, p)
        self._audit("MOVE", actor, p.user_id, {"session": p.session_id, "from": before,
                                                "to": [location.value, reason.value]})
        if location == Location.DETENTION or before[0] == Location.DETENTION.value:
            self._seal_quietly(p.session_id, "movement", {"user_id": p.user_id, "from": before,
                                                  "to": [location.value, reason.value], "by": actor})
        return p

    # ── sessions ───────────────────────────────────────────────────────────

    def start_session(self, host_id: str, *, display_name: str = "", start_room: str = "studio") -> Dict[str, Any]:
        """The owner opens their own copy for guests. The owner starts inside."""
        host_id = _clean_id(host_id, "host")
        session_id = f"pc_{uuid.uuid4().hex[:16]}"
        now = self._now()
        with self._lock, self._connect() as conn:
            conn.execute("INSERT INTO sessions (session_id, host_id, started_at) VALUES (?,?,?)",
                         (session_id, host_id, now))
            self._put(conn, Presence(session_id=session_id, user_id=host_id,
                                     display_name=display_name or host_id, location=Location.INSIDE,
                                     reason=Reason.ENTRY, since=now, owner_signed=True,
                                     avatar_cleared=True, is_staff=True, note=f"host; starts in {start_room}"))
        self._audit("SESSION_START", host_id, None, {"session": session_id, "start_room": start_room})
        return {"session_id": session_id, "host_id": host_id, "started_at": now}

    def end_session(self, session_id: str, actor: str) -> None:
        with self._lock, self._connect() as conn:
            row = self._session_row(conn, session_id)
            if actor != row["host_id"]:
                raise Forbidden("Only the host can end the session.")
            conn.execute("UPDATE sessions SET ended_at=? WHERE session_id=?", (self._now(), session_id))
        self._audit("SESSION_END", actor, None, {"session": session_id})

    def host_id(self, session_id: str) -> str:
        with self._connect() as conn:
            return self._session_row(conn, session_id)["host_id"]

    def host_left(self, session_id: str) -> List[str]:
        """Everyone inside goes back to the guest side until the host returns."""
        moved: List[str] = []
        with self._lock, self._connect() as conn:
            row = self._session_row(conn, session_id)
            conn.execute("UPDATE sessions SET host_present=0 WHERE session_id=?", (session_id,))
            for r in conn.execute("SELECT user_id FROM presence WHERE session_id=?", (session_id,)).fetchall():
                p = self._get(conn, session_id, r["user_id"])
                if p and p.user_id != row["host_id"] and p.location == Location.INSIDE:
                    self._move(conn, p, Location.WAITING, Reason.HOST_LEFT, "system")
                    moved.append(p.user_id)
        self._audit("HOST_LEFT", row["host_id"], None, {"session": session_id, "returned": moved})
        return moved

    def host_returned(self, session_id: str) -> None:
        with self._lock, self._connect() as conn:
            row = self._session_row(conn, session_id)
            conn.execute("UPDATE sessions SET host_present=1 WHERE session_id=?", (session_id,))
        self._audit("HOST_RETURNED", row["host_id"], None, {"session": session_id})

    # ── requirements ───────────────────────────────────────────────────────

    def requirements(self, host_id: str) -> HostRequirements:
        with self._connect() as conn:
            row = conn.execute("SELECT body FROM requirements WHERE host_id=?", (host_id,)).fetchone()
        return HostRequirements.from_dict(json.loads(row["body"])) if row else HostRequirements()

    def set_requirements(self, host_id: str, data: Dict[str, Any], actor: str) -> HostRequirements:
        req = HostRequirements.from_dict(data)
        with self._lock, self._connect() as conn:
            conn.execute("INSERT OR REPLACE INTO requirements (host_id, body, updated_at) VALUES (?,?,?)",
                         (host_id, json.dumps(req.to_dict(), sort_keys=True), self._now()))
        self._audit("REQUIREMENTS", actor, host_id, {"sha256": req.sha256})
        return req

    # ── arriving and leaving ───────────────────────────────────────────────

    def arrive(self, session_id: str, user_id: str, *, display_name: str = "",
               ai_id: str = "", ai_language: str = "") -> Presence:
        """Arriving always lands in the waiting room. An unserved timeout follows you back."""
        user_id = _clean_id(user_id, "user")
        ai_id = _clean_id(ai_id, "AI", allow_empty=True)
        banned, why = self._gov.is_banned(user_id)
        if banned:
            raise NotAllowed(f"You can't join this PubCast: {why}")
        now = self._now()
        with self._lock, self._connect() as conn:
            row = self._session_row(conn, session_id)
            if user_id == row["host_id"]:
                raise NotAllowed("You're the host; you start inside your own PubCast.")
            p = self._get(conn, session_id, user_id)
            if p is not None and p.location == Location.BOOTED:
                raise NotAllowed("You were removed from this session.")
            if p is not None and p.location == Location.DETENTION:
                return p  # already there; leaving and rejoining does not clear a timeout
            if p is not None and p.needs_resign and p.release_at is not None:
                # Left during a timeout. It still stands: back to detention. The
                # clock kept running while they were gone, but release still needs
                # the host and a fresh signature, so leaving doesn't dodge it.
                p.ai_id, p.ai_language = ai_id or p.ai_id, ai_language or p.ai_language
                return self._move(conn, p, Location.DETENTION, Reason.TIMEOUT, "system")
            if p is None:
                p = Presence(session_id=session_id, user_id=user_id, display_name=display_name or user_id,
                             location=Location.WAITING, reason=Reason.ENTRY, since=now)
            p.display_name = display_name or p.display_name
            if ai_id != p.ai_id:
                p.ai_signed = False          # a different AI hasn't signed anything
                p.avatar_cleared = False
            p.ai_id, p.ai_language = ai_id, (ai_language or "").strip().lower()
            if p.owner_signed and not self._has_signature(conn, row["host_id"], user_id, "owner", user_id):
                p.owner_signed = False       # the waiver changed since they signed
            if p.ai_id and p.ai_signed and not self._has_signature(conn, row["host_id"], user_id, "ai", p.ai_id):
                p.ai_signed = False
            return self._move(conn, p, Location.WAITING, Reason.ENTRY, user_id)

    def leave(self, session_id: str, user_id: str) -> Presence:
        """Anyone can leave the server at any time, including from detention."""
        with self._lock, self._connect() as conn:
            p = self._must_get(conn, session_id, user_id)
            if p.location in (Location.LEFT, Location.BOOTED, Location.EXPIRED):
                return p
            return self._move(conn, p, Location.LEFT, p.reason, user_id)

    def sweep(self) -> List[str]:
        """Arrivals nobody admitted within the limit are sent away politely."""
        cutoff = self._now() - self._entry_wait_limit_s
        expired: List[str] = []
        with self._lock, self._connect() as conn:
            for r in conn.execute("SELECT session_id, user_id FROM presence").fetchall():
                p = self._get(conn, r["session_id"], r["user_id"])
                if p and p.location == Location.WAITING and p.reason == Reason.ENTRY and p.since < cutoff:
                    self._move(conn, p, Location.EXPIRED, Reason.ENTRY, "system",
                               note="Nobody was available to let you in. You're welcome to try again later.")
                    expired.append(p.user_id)
        return expired

    # ── signing ────────────────────────────────────────────────────────────

    def _has_signature(self, conn, host_id: str, owner_id: str, kind: str, signer_id: str) -> bool:
        row = conn.execute(
            "SELECT agreed FROM signatures WHERE host_id=? AND owner_id=? AND signer_kind=? AND signer_id=? "
            "AND waiver_sha256=? ORDER BY signed_at DESC LIMIT 1",
            (host_id, owner_id, kind, signer_id, self.waiver.sha256)).fetchone()
        return bool(row and row["agreed"])

    def _write_signature(self, conn, *, host_id, session_id, owner_id, kind, signer_id, agreed,
                         typed_name, statement, context) -> str:
        sig_id = f"sig_{uuid.uuid4().hex[:16]}"
        conn.execute(
            "INSERT INTO signatures VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (sig_id, host_id, session_id, owner_id, kind, signer_id, int(agreed), typed_name[:200],
             statement[:4000], self.waiver.version, self.waiver.sha256, context, self._now()))
        return sig_id

    def _signing_presence(self, conn, session_id: str, user_id: str) -> Tuple[sqlite3.Row, Presence]:
        row = self._session_row(conn, session_id)
        p = self._must_get(conn, session_id, user_id)
        if p.location not in (Location.WAITING, Location.DETENTION):
            raise NotAllowed("The waiver is signed in the waiting room.")
        return row, p

    def sign_owner(self, session_id: str, user_id: str, *, typed_name: str,
                   waiver_sha256: str, agreed: bool = True) -> Presence:
        """The owner signs, or declines. They must be signing the text they were shown."""
        if waiver_sha256 != self.waiver.sha256:
            raise NotAllowed("The waiver changed while you were reading it. Please read the current one.")
        if agreed and not typed_name.strip():
            raise NotAllowed("Type your name to sign.")
        with self._lock, self._connect() as conn:
            row, p = self._signing_presence(conn, session_id, user_id)
            context = "resign" if p.needs_resign else "entry"
            sig = self._write_signature(conn, host_id=row["host_id"], session_id=session_id, owner_id=user_id,
                                        kind="owner", signer_id=user_id, agreed=agreed,
                                        typed_name=typed_name.strip(), statement="", context=context)
            p.owner_signed = bool(agreed)
            if p.needs_resign and agreed:
                p.note = "Owner re-signed."
            self._put(conn, p)
        self._audit("SIGN_OWNER", user_id, row["host_id"],
                    {"session": session_id, "signature": sig, "agreed": agreed, "context": context,
                     "waiver": self.waiver.version})
        if agreed:
            self._seal_quietly(session_id, "waiver_signed", {"user_id": user_id, "signer": "owner",
                                                      "waiver": self.waiver.version, "context": context})
        return p

    def sign_ai(self, session_id: str, user_id: str, *, ai_id: str, statement: str,
                waiver_sha256: str, agreed: bool) -> Presence:
        """The owner's AI signs in its own words. A refusal is recorded and flagged to the host."""
        if waiver_sha256 != self.waiver.sha256:
            raise NotAllowed("The waiver changed; the AI must read the current one.")
        with self._lock, self._connect() as conn:
            row, p = self._signing_presence(conn, session_id, user_id)
            if not p.ai_id or p.ai_id != ai_id:
                raise NotAllowed("That AI didn't arrive with this person.")
            if agreed and len(statement.strip()) < 10:
                raise NotAllowed("The AI signs in its own words; its statement is too short to count.")
            context = "resign" if p.needs_resign else "entry"
            sig = self._write_signature(conn, host_id=row["host_id"], session_id=session_id, owner_id=user_id,
                                        kind="ai", signer_id=ai_id, agreed=agreed, typed_name="",
                                        statement=statement.strip(), context=context)
            p.ai_signed = bool(agreed)
            if not agreed:
                p.note = "The AI refused to sign the waiver."
            self._put(conn, p)
        self._audit("SIGN_AI" if agreed else "AI_REFUSED", user_id, ai_id,
                    {"session": session_id, "signature": sig, "context": context, "waiver": self.waiver.version})
        self._seal_quietly(session_id, "waiver_signed" if agreed else "waiver_refused",
                   {"user_id": user_id, "signer": "ai", "ai_id": ai_id, "statement": statement.strip(),
                    "context": context})
        return p

    def _fully_signed(self, p: Presence) -> bool:
        return p.owner_signed and (not p.ai_id or p.ai_signed)

    # ── avatar check ───────────────────────────────────────────────────────

    def check_avatar(self, session_id: str, user_id: str, *, avatar_id: str) -> Dict[str, Any]:
        if self._load_avatar is None:
            raise AirlockError("Avatar checking isn't available on this server.")
        with self._lock, self._connect() as conn:
            row = self._session_row(conn, session_id)
            p = self._must_get(conn, session_id, user_id)
            if p.location != Location.WAITING:
                raise NotAllowed("Avatars are checked in the waiting room.")
            if not self._fully_signed(p):
                raise NotAllowed("Sign the waiver first.")
        try:
            glb, height_in, owner = self._load_avatar(avatar_id)
        except (KeyError, FileNotFoundError, ValueError):
            raise NotFound("That avatar isn't in your library.") from None
        # Your own avatars, and the host's house avatars from the foundry rack.
        if owner and owner not in (user_id, row["host_id"], "local"):
            raise Forbidden("That avatar belongs to someone else.")
        req = self.requirements(row["host_id"])
        avatar_sha = hashlib.sha256(glb).hexdigest()

        with self._connect() as conn:
            remembered = conn.execute(
                "SELECT 1 FROM avatar_passes WHERE host_id=? AND owner_id=? AND avatar_sha256=? "
                "AND requirements_sha256=?", (row["host_id"], user_id, avatar_sha, req.sha256)).fetchone()
        issues: List[CheckIssue] = []
        if remembered:
            # The file and the rules are both unchanged; only the language is per visit.
            if p.ai_id and p.ai_language not in req.allowed_languages:
                issues.append(CheckIssue("language", "The avatar must communicate in English or a "
                                         "language this host can translate into English.", False))
        else:
            issues = check_avatar(glb, declared_height_in=height_in,
                                  language=p.ai_language if p.ai_id else "en", req=req)

        with self._lock, self._connect() as conn:
            p = self._must_get(conn, session_id, user_id)
            p.avatar_id, p.avatar_cleared = avatar_id, not issues
            self._put(conn, p)
            if not issues and not remembered:
                conn.execute("INSERT OR IGNORE INTO avatar_passes VALUES (?,?,?,?,?)",
                             (row["host_id"], user_id, avatar_sha, req.sha256, self._now()))
        self._audit("AVATAR_CHECK", user_id, avatar_id,
                    {"session": session_id, "clear": not issues, "remembered": bool(remembered),
                     "issues": [i.code for i in issues]})
        return {"clear": not issues, "remembered": bool(remembered),
                "issues": [asdict(i) for i in issues], "requirements": req.to_dict()}

    def can_use_foundry(self, session_id: str, user_id: str) -> bool:
        """Guests on the guest side and people inside may build. Detention may not."""
        with self._connect() as conn:
            p = self._get(conn, session_id, user_id)
        return bool(p and p.location in (Location.WAITING, Location.INSIDE))

    # ── admitting ──────────────────────────────────────────────────────────

    def _require_host_or_staff(self, conn, session_id: str, actor: str, actor_is_mod: bool) -> sqlite3.Row:
        row = self._session_row(conn, session_id)
        if actor == row["host_id"] or actor_is_mod:
            return row
        staff = self._get(conn, session_id, actor)
        if staff and staff.is_staff and staff.location == Location.INSIDE:
            return row
        raise Forbidden("Only the host or staff can do that.")

    def admit(self, session_id: str, user_id: str, *, actor: str, actor_is_mod: bool = False) -> Presence:
        """Someone inside pulls a cleared guest in."""
        with self._lock, self._connect() as conn:
            self._require_host_or_staff(conn, session_id, actor, actor_is_mod)
            p = self._must_get(conn, session_id, user_id)
            if p.location == Location.DETENTION:
                raise NotAllowed("They're on a timeout. Use release when it's served.")
            if p.location != Location.WAITING:
                raise NotAllowed("They're not in the waiting room.")
            missing = self._missing_for_entry(p)
            if missing:
                raise NotAllowed("Not cleared yet: " + "; ".join(missing) + ".")
            return self._move(conn, p, Location.INSIDE, p.reason, actor, note="")

    def _missing_for_entry(self, p: Presence) -> List[str]:
        missing = []
        if not p.owner_signed:
            missing.append("the owner hasn't signed the waiver")
        if p.ai_id and not p.ai_signed:
            missing.append("the AI hasn't signed the waiver")
        if not p.avatar_cleared:
            missing.append("the avatar hasn't cleared this host's requirements")
        banned, _ = self._gov.is_banned(p.user_id)
        if banned:
            missing.append("they are banned")
        return missing

    def step_out(self, session_id: str, user_id: str, *, reason: Reason) -> Presence:
        """Self-serve: a technical problem, or a minute to yourself. Guest side."""
        if reason not in (Reason.TECHNICAL, Reason.VOLUNTARY):
            raise NotAllowed("You can step out for a technical problem or a breather.")
        with self._lock, self._connect() as conn:
            p = self._must_get(conn, session_id, user_id)
            if p.location != Location.INSIDE:
                raise NotAllowed("You're not inside.")
            return self._move(conn, p, Location.WAITING, reason, user_id)

    def come_back(self, session_id: str, user_id: str) -> Presence:
        """Technical, breather and staff visits come straight back in, no re-check."""
        with self._lock, self._connect() as conn:
            row = self._session_row(conn, session_id)
            p = self._must_get(conn, session_id, user_id)
            if p.location != Location.WAITING or p.reason not in SELF_RETURN_REASONS:
                raise NotAllowed("You need someone inside to let you in.")
            if not row["host_present"] and user_id != row["host_id"]:
                raise NotAllowed("The host isn't here right now. You'll come back in when they return.")
            return self._move(conn, p, Location.INSIDE, p.reason, user_id)

    # ── staff ──────────────────────────────────────────────────────────────

    def make_staff(self, session_id: str, user_id: str, *, actor: str) -> Presence:
        with self._lock, self._connect() as conn:
            row = self._session_row(conn, session_id)
            if actor != row["host_id"]:
                raise Forbidden("Only the host names staff.")
            p = self._must_get(conn, session_id, user_id)
            if p.location != Location.INSIDE:
                raise NotAllowed("Staff are named from people inside.")
            p.is_staff = True
            self._put(conn, p)
        self._audit("STAFF", actor, user_id, {"session": session_id})
        return p

    def staff_step_out(self, session_id: str, staff_id: str, *, to_side: str) -> Presence:
        """Staff go out to talk to someone and come back without the waiver again."""
        location = {"guest": Location.WAITING, "detention": Location.DETENTION}.get(to_side)
        if location is None:
            raise NotAllowed("Choose the guest side or the detention side.")
        with self._lock, self._connect() as conn:
            row = self._session_row(conn, session_id)
            p = self._must_get(conn, session_id, staff_id)
            if not (p.is_staff or staff_id == row["host_id"]) or p.location != Location.INSIDE:
                raise Forbidden("Only staff inside can step out to talk to someone.")
            # Staff in detention are recorded like everyone else there, under the waiver.
            return self._move(conn, p, location, Reason.STAFF, staff_id)

    def staff_return(self, session_id: str, staff_id: str) -> Presence:
        with self._lock, self._connect() as conn:
            p = self._must_get(conn, session_id, staff_id)
            if p.reason != Reason.STAFF or p.location not in (Location.WAITING, Location.DETENTION):
                raise NotAllowed("You're not out on staff business.")
            return self._move(conn, p, Location.INSIDE, Reason.STAFF, staff_id)

    # ── discipline ─────────────────────────────────────────────────────────

    def timeout(self, session_id: str, user_id: str, *, actor: str, rule: str,
                seconds: float = DEFAULT_TIMEOUT_S, actor_is_mod: bool = False) -> Presence:
        seconds = float(seconds)
        if not 0 < seconds <= MAX_TIMEOUT_S:
            raise NotAllowed("A timeout lasts more than zero seconds and at most a day.")
        with self._lock, self._connect() as conn:
            row = self._require_host_or_staff(conn, session_id, actor, actor_is_mod)
            if user_id == row["host_id"]:
                raise NotAllowed("The host can't be put on a timeout in their own PubCast.")
            p = self._must_get(conn, session_id, user_id)
            if p.location in (Location.LEFT, Location.EXPIRED, Location.BOOTED):
                raise NotAllowed("They're not here.")
            p = self._move(conn, p, Location.DETENTION, Reason.TIMEOUT, actor,
                           release_at=self._now() + seconds, needs_resign=True,
                           owner_signed=False, ai_signed=False,
                           note=f"Timeout for: {rule[:300]}")
        self._audit("TIMEOUT", actor, user_id, {"session": session_id, "rule": rule[:300], "seconds": seconds})
        return p

    def release(self, session_id: str, user_id: str, *, actor: str, early: bool = False,
                actor_is_mod: bool = False) -> Presence:
        """Back inside after a timeout: time served (or the host's call) and a fresh signature."""
        with self._lock, self._connect() as conn:
            self._require_host_or_staff(conn, session_id, actor, actor_is_mod)
            p = self._must_get(conn, session_id, user_id)
            if p.location != Location.DETENTION or p.reason != Reason.TIMEOUT:
                raise NotAllowed("They're not on a timeout.")
            if not early and p.release_at is not None and self._now() < p.release_at:
                left = int(round(p.release_at - self._now()))
                raise NotAllowed(f"Their timeout has {left} seconds left.")
            if not self._fully_signed(p):
                raise NotAllowed("They have to agree to the rules again first"
                                 + (", and so does their AI." if p.ai_id and not p.ai_signed else "."))
            return self._move(conn, p, Location.INSIDE, Reason.TIMEOUT, actor,
                              release_at=None, needs_resign=False, note="")

    def boot(self, session_id: str, user_id: str, *, actor: str, reason: str,
             actor_is_mod: bool = False) -> Presence:
        """Removed for the rest of the session. The ban is on the owner account, not the avatar."""
        from modules.governance import BanType
        with self._lock, self._connect() as conn:
            row = self._require_host_or_staff(conn, session_id, actor, actor_is_mod)
            if user_id == row["host_id"]:
                raise NotAllowed("The host can't be removed from their own PubCast.")
            p = self._must_get(conn, session_id, user_id)
            p = self._move(conn, p, Location.BOOTED, p.reason, actor, note=f"Removed: {reason[:300]}")
        self._gov.ban_user(user_id, f"Removed from PubCast session {session_id}: {reason[:300]}",
                           actor, BanType.SESSION)
        return p

    def violation(self, session_id: str, user_id: str, *, actor: str, rule: str,
                  timeout_seconds: float = DEFAULT_TIMEOUT_S, actor_is_mod: bool = False) -> Dict[str, Any]:
        """The ladder written into the waiver: warning, then timeout, then booted."""
        with self._lock, self._connect() as conn:
            self._require_host_or_staff(conn, session_id, actor, actor_is_mod)
            p = self._must_get(conn, session_id, user_id)
            prior = conn.execute("SELECT COUNT(*) FROM violations WHERE session_id=? AND user_id=?",
                                 (session_id, user_id)).fetchone()[0]
            step = ("warning", "timeout", "boot")[min(prior, 2)]
            conn.execute("INSERT INTO violations VALUES (?,?,?,?,?,?,?)",
                         (f"v_{uuid.uuid4().hex[:12]}", session_id, user_id, rule[:300], step, actor, self._now()))
            p.strikes = prior + 1
            self._put(conn, p)
        self._audit("VIOLATION", actor, user_id, {"session": session_id, "rule": rule[:300], "step": step})
        self._seal_quietly(session_id, "violation", {"user_id": user_id, "rule": rule[:300], "step": step, "by": actor})
        if step == "timeout":
            p = self.timeout(session_id, user_id, actor=actor, rule=rule,
                             seconds=timeout_seconds, actor_is_mod=actor_is_mod)
        elif step == "boot":
            p = self.boot(session_id, user_id, actor=actor, reason=rule, actor_is_mod=actor_is_mod)
        return {"step": step, "strikes": p.strikes, "presence": p.private_view(self._now())}

    # ── views ──────────────────────────────────────────────────────────────

    def presence(self, session_id: str, user_id: str) -> Presence:
        with self._connect() as conn:
            return self._must_get(conn, session_id, user_id)

    def waiting_list(self, session_id: str) -> List[Dict[str, Any]]:
        """Host view: both sides of the waiting room, with reasons and what's missing."""
        now = self._now()
        out = []
        with self._connect() as conn:
            self._session_row(conn, session_id)
            for r in conn.execute("SELECT user_id FROM presence WHERE session_id=?", (session_id,)).fetchall():
                p = self._get(conn, session_id, r["user_id"])
                if p and p.location in (Location.WAITING, Location.DETENTION):
                    view = p.private_view(now)
                    view["missing"] = self._missing_for_entry(p)
                    out.append(view)
        return sorted(out, key=lambda v: v["since"])

    def public_roster(self, session_id: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            self._session_row(conn, session_id)
            rows = conn.execute("SELECT user_id FROM presence WHERE session_id=?", (session_id,)).fetchall()
            people = [self._get(conn, session_id, r["user_id"]) for r in rows]
        return [p.public_view() for p in people if p and p.location not in (Location.EXPIRED,)]

    def is_cleared_anywhere(self, user_id: str) -> Tuple[bool, str]:
        """Gate for the older one-server admission route: current waiver signed, not in detention."""
        with self._connect() as conn:
            signed = conn.execute(
                "SELECT 1 FROM signatures WHERE owner_id=? AND signer_kind='owner' AND agreed=1 "
                "AND waiver_sha256=? LIMIT 1", (user_id, self.waiver.sha256)).fetchone()
            for r in conn.execute("SELECT session_id FROM presence WHERE user_id=?", (user_id,)).fetchall():
                p = self._get(conn, r["session_id"], user_id)
                if p and p.location in (Location.DETENTION, Location.BOOTED):
                    return False, "They're on a timeout or were removed."
        if not signed:
            return False, "They haven't signed the current waiver."
        return True, "OK"

    # ── recording ──────────────────────────────────────────────────────────

    def recording_allowed(self, session_id: str, room: str) -> Dict[str, Any]:
        """Whether cameras in this room may record, and the notice to show (the tally)."""
        room_key = (room or "").strip().lower()
        if room_key == DETENTION_ROOM:
            return {"room": room_key, "recording": True, "tally": True,
                    "notice": "On a timeout. Everything said and thought here is recorded."}
        if room_key in NO_RECORD_ROOMS:
            return {"room": room_key, "recording": False, "tally": False,
                    "notice": "Private. Nobody is recorded here."}
        with self._connect() as conn:
            row = self._session_row(conn, session_id)
            unsigned = []
            for r in conn.execute("SELECT user_id FROM presence WHERE session_id=?", (session_id,)).fetchall():
                p = self._get(conn, session_id, r["user_id"])
                if p and p.location == Location.INSIDE and p.user_id != row["host_id"] and not p.owner_signed:
                    unsigned.append(p.user_id)
        if unsigned:
            return {"room": room_key, "recording": False, "tally": False,
                    "notice": "Not recording: someone inside hasn't signed the waiver.", "unsigned": unsigned}
        return {"room": room_key, "recording": True, "tally": True, "notice": "On camera."}

    # Each airlock record kind, in the blackbox event language's own codes.
    _SEAL_CODES: Dict[str, Tuple[str, str, str]] = {
        "thought": ("AIT", "DCP", "USR"),          # AI thought or decision trace
        "said": ("CHT", "MSG", "USR"),             # something said
        "waiver_signed": ("APP", "APR", "USR"),
        "waiver_refused": ("APP", "DNY", "USR"),
        "movement": ("DSC", "RSP", "SYS"),         # into or out of detention
        "violation": ("DSC", "CND", "SYS"),
        "incident_opened": ("DSC", "RVW", "SYS"),
    }

    def _seal_path(self, session_id: str) -> Path:
        if not re.fullmatch(r"pc_[0-9a-f]{16}", session_id):
            raise NotFound("That session doesn't exist.")
        return self._dir / "sealed" / f"{session_id}.bbx"

    def _recorder(self, session_id: str) -> AppendOnlyBlackBoxRecorder:
        rec = self._recorders.get(session_id)
        if rec is None:
            try:
                rec = AppendOnlyBlackBoxRecorder(self._seal_path(session_id), session_id)
            except BlackBoxValidationError as exc:
                # The last line no longer matches its hash. Appending after it
                # would hide the damage, so nothing more is written to this log.
                raise SealBroken(f"The sealed record for this session is damaged: {exc}") from None
            self._recorders[session_id] = rec
        return rec

    def _seal(self, session_id: str, kind: str, payload: Dict[str, Any]) -> None:
        """Append one record. Values are fully percent-encoded first: the shared
        payload encoder leaves commas bare and its decoder splits on them, so
        ordinary sentences would otherwise decode into fragments."""
        ch, ev, src = self._SEAL_CODES[kind]
        actor = str(payload.get("user_id") or payload.get("by") or "SYS")
        encoded = {"kind": kind, "enc": "q1"}
        for key, value in payload.items():
            if isinstance(value, (list, tuple, set)):
                value = json.dumps(list(value), ensure_ascii=False)
            encoded[key] = quote(str(value), safe="")
        with self._lock:
            self._recorder(session_id).append(ch=ch, src=src, act=quote(actor, safe="@._-"),
                                              ev=ev, cov="F", payload=encoded)

    def _seal_quietly(self, session_id: str, kind: str, payload: Dict[str, Any]) -> None:
        """Side records (moves, signatures) must not block discipline if the log is damaged."""
        try:
            self._seal(session_id, kind, payload)
        except SealBroken as exc:
            logger.error("%s", exc)
            self._audit("SEAL_BROKEN", "system", None, {"session": session_id, "kind": kind})

    @staticmethod
    def _decode_sealed(record: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(record.get("payload") or {})
        if payload.get("enc") == "q1":
            payload = {k: (unquote(v) if k not in ("kind", "enc") else v) for k, v in payload.items()}
        record = dict(record)
        record["payload"] = payload
        return record

    def _verify_sealed(self, path: Path) -> Tuple[bool, List[str], List[Dict[str, Any]]]:
        """Walk the hash chain line by line without trusting the file's tail."""
        errors: List[str] = []
        records: List[Dict[str, Any]] = []
        previous = ZERO_HASH
        if not path.exists():
            return True, errors, records
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        for expected_seq, line in enumerate(lines):
            try:
                fields = parse_record(line)
            except BlackBoxValidationError as exc:
                errors.append(f"record {expected_seq}: {exc}")
                previous = "broken"
                continue
            if int(fields["seq"]) != expected_seq:
                errors.append(f"record {expected_seq}: sequence gap (got {fields['seq']})")
            if fields["ph"] != previous and previous != "broken":
                errors.append(f"record {expected_seq}: does not follow the record before it")
            previous = fields["h"]
            records.append(self._decode_sealed(decode_record(line)))
        return not errors, errors, records

    def record(self, session_id: str, user_id: str, *, room: str, kind: str, text: str,
               ai_id: str = "") -> Dict[str, Any]:
        """Write a thought or an utterance to the sealed record, if this moment may be recorded.

        Recording starts at signing. Nothing is written in the places people
        change. Detention is always written. Messages that look like code rather
        than language are still written, and flagged.
        """
        if kind not in ("thought", "said"):
            raise NotAllowed("Record a thought or something said.")
        with self._connect() as conn:
            self._session_row(conn, session_id)
            p = self._must_get(conn, session_id, user_id)
        if ai_id and ai_id != p.ai_id:
            raise NotAllowed("That AI didn't arrive with this person.")
        in_detention = p.location == Location.DETENTION
        room_key = DETENTION_ROOM if in_detention else (room or "").strip().lower()
        signed = p.ai_signed if ai_id else p.owner_signed
        if not in_detention:
            if room_key in NO_RECORD_ROOMS:
                return {"recorded": False, "why": "private room"}
            if not signed:
                return {"recorded": False, "why": "not signed yet"}
        flags = screen_message(text) if kind == "said" or ai_id else []
        try:
            self._seal(session_id, kind, {"user_id": user_id, "ai_id": ai_id, "room": room_key,
                                          "text": text[:20000], "language_flags": flags})
        except SealBroken:
            self._audit("SEAL_BROKEN", "system", user_id, {"session": session_id, "kind": kind})
            return {"recorded": False, "why": "the sealed record is damaged; it has been flagged"}
        if flags:
            self._audit("LANGUAGE_FLAG", ai_id or user_id, user_id,
                        {"session": session_id, "flags": flags})
        return {"recorded": True, "language_flags": flags}

    def open_incident(self, session_id: str, *, opened_by: str, subjects: Iterable[str],
                      reason: str) -> Dict[str, Any]:
        subjects = sorted({_clean_id(s, "subject") for s in subjects})
        if not subjects:
            raise NotAllowed("Name who the incident is about.")
        if len(reason.strip()) < 5:
            raise NotAllowed("Say what happened.")
        incident_id = f"inc_{uuid.uuid4().hex[:12]}"
        with self._lock, self._connect() as conn:
            self._session_row(conn, session_id)
            conn.execute("INSERT INTO incidents VALUES (?,?,?,?,?,?,?)",
                         (incident_id, session_id, opened_by, json.dumps(subjects), reason.strip()[:2000],
                          self._now(), None))
        self._audit("INCIDENT_OPEN", opened_by, ",".join(subjects), {"incident": incident_id, "session": session_id})
        self._seal_quietly(session_id, "incident_opened", {"incident": incident_id, "by": opened_by, "subjects": subjects})
        return {"incident_id": incident_id, "session_id": session_id, "subjects": subjects}

    def close_incident(self, incident_id: str, *, closed_by: str) -> None:
        with self._lock, self._connect() as conn:
            n = conn.execute("UPDATE incidents SET closed_at=? WHERE incident_id=? AND closed_at IS NULL",
                             (self._now(), incident_id)).rowcount
        if not n:
            raise NotFound("No open incident with that id.")
        self._audit("INCIDENT_CLOSE", closed_by, None, {"incident": incident_id})

    def read_incident(self, incident_id: str, *, reader: str) -> Dict[str, Any]:
        """The only way into the sealed record. The read itself is written to the record first."""
        with self._connect() as conn:
            inc = conn.execute("SELECT * FROM incidents WHERE incident_id=?", (incident_id,)).fetchone()
        if inc is None:
            raise NotFound("No incident with that id.")
        if inc["closed_at"] is not None:
            raise NotAllowed("That incident is closed; open a new one to read the record again.")
        subjects = set(json.loads(inc["subjects"]))
        session_id = inc["session_id"]
        scope = ",".join(sorted(subjects))
        with self._lock:
            witnessed = True
            try:
                self._recorder(session_id).access(actor=quote(reader, safe="@._-"), access="read",
                                                  scope=quote(scope, safe=""), reason=incident_id)
            except SealBroken:
                witnessed = False       # damaged log: read it, but nothing can be appended
            intact, errors, all_records = self._verify_sealed(self._seal_path(session_id))
        records = [r for r in all_records
                   if r["channel"]["code"] == "ACC"
                   or r["payload"].get("user_id") in subjects
                   or r["payload"].get("kind") == "incident_opened"]
        self._audit("INCIDENT_READ", reader, scope,
                    {"incident": incident_id, "records": len(records), "intact": intact,
                     "witnessed": witnessed})
        return {"incident_id": incident_id, "session_id": session_id, "subjects": sorted(subjects),
                "intact": intact, "integrity_errors": errors[:20], "read_witnessed": witnessed,
                "records": records}


def _clean_id(value: str, what: str, *, allow_empty: bool = False) -> str:
    value = str(value or "").strip()
    if not value:
        if allow_empty:
            return ""
        raise AirlockError(f"A {what} id is required.")
    if len(value) > 128 or not re.fullmatch(r"[A-Za-z0-9_.@:+-]+", value):
        raise AirlockError(f"That {what} id has characters that aren't allowed.")
    return value


__all__ = [
    "AirlockEngine", "AirlockError", "NotAllowed", "NotFound", "Forbidden", "Location", "Reason",
    "HostRequirements", "CheckIssue", "Waiver", "load_waiver", "check_avatar", "count_triangles",
    "screen_message", "NO_RECORD_ROOMS", "DEFAULT_WAIVER",
]
