"""Private delivery to walker sockets (/pubworld/ws/{client_id} in main.py).

The walker's socket is not in the Hub, so ``Hub.send_private_event`` cannot reach it. This registry holds the walker
sockets whose owner has been *verified* (a valid token, never a bare client id) under that person's id, and sends an
event to exactly the people named. Host control uses it for the possession notice, drive commands and timeouts.

A person is matched case-insensitively, as the Hub does. A socket that never proved who it is is never registered, so
an unverified client can neither receive another person's notice nor be mistaken for them.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Iterable, Set

logger = logging.getLogger("pubcast.pubworld_private")


class PubWorldPrivate:
    def __init__(self) -> None:
        self._by_user: Dict[str, Set[Any]] = {}

    def register(self, user_id: str, ws: Any) -> None:
        if isinstance(user_id, str) and user_id.strip():
            self._by_user.setdefault(user_id.casefold(), set()).add(ws)

    def unregister(self, ws: Any) -> None:
        for key in list(self._by_user):
            self._by_user[key].discard(ws)
            if not self._by_user[key]:
                del self._by_user[key]

    def connected(self, user_id: str) -> int:
        return len(self._by_user.get(str(user_id).casefold(), ()))

    async def send(self, user_ids: Iterable[str], event: Dict[str, Any]) -> int:
        """Send `event` to every verified socket of the named people. Returns how many sockets it was written to."""
        wire = json.dumps(event)
        delivered = 0
        for uid in {u.casefold() for u in user_ids if isinstance(u, str) and u}:
            for ws in list(self._by_user.get(uid, ())):
                try:
                    await ws.send_text(wire)
                    delivered += 1
                except Exception:
                    logger.warning("private walker delivery failed; dropping that socket")
                    self.unregister(ws)
        return delivered


__all__ = ["PubWorldPrivate"]
