"""Private delivery to walker sockets (modules/pubworld_private.py) and its wiring into host control."""
from __future__ import annotations

import asyncio
import json

from modules.pubworld_private import PubWorldPrivate


class Sock:
    def __init__(self, fail=False):
        self.sent, self.fail = [], fail

    async def send_text(self, text):
        if self.fail:
            raise RuntimeError("closed")
        self.sent.append(json.loads(text))


def run(coro):
    return asyncio.run(coro)


def test_only_the_named_person_gets_it_and_case_does_not_matter():
    reg, mira, kay = PubWorldPrivate(), Sock(), Sock()
    reg.register("Mira", mira); reg.register("kay", kay)
    assert run(reg.send({"MIRA"}, {"type": "host_notice"})) == 1
    assert mira.sent == [{"type": "host_notice"}] and kay.sent == []


def test_every_verified_socket_of_the_person_gets_it_once_and_strangers_none():
    reg, a, b = PubWorldPrivate(), Sock(), Sock()
    reg.register("mira", a); reg.register("mira", b)
    assert run(reg.send({"mira", "nobody"}, {"type": "x"})) == 2
    assert run(reg.send({"stranger"}, {"type": "x"})) == 0 and len(a.sent) == 1 and len(b.sent) == 1


def test_unregister_stops_delivery_and_a_dead_socket_is_dropped_not_fatal():
    reg, live, dead = PubWorldPrivate(), Sock(), Sock(fail=True)
    reg.register("mira", live); reg.register("mira", dead)
    assert run(reg.send({"mira"}, {"type": "x"})) == 1 and reg.connected("mira") == 1
    reg.unregister(live)
    assert reg.connected("mira") == 0 and run(reg.send({"mira"}, {"type": "x"})) == 0


def test_bad_ids_are_ignored():
    reg, s = PubWorldPrivate(), Sock()
    for bad in ("", "   ", None, 5):
        reg.register(bad, s)
    assert reg.connected("") == 0 and run(reg.send(["", None, 5], {"type": "x"})) == 0
