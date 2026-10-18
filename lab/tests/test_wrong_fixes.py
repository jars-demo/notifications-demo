"""The checks test the real goal, not the shape of one answer. Each wrong fix below is one people
really try. It makes the symptom go away, or looks right, and the check must still fail it. Each
other fix is a different, valid answer, and the check must pass it.

A fix is a list of (old, new) edits applied to the case as shipped ("case") or to its solution
("solution"). Every old string must appear exactly once, so a fix cannot silently stop applying.
"""

import sys
import types
from pathlib import Path

import pytest

from dove.__main__ import CASES
from dove.checks import CHECKS

ROOT = Path(__file__).resolve().parent.parent

Edit = tuple[str, str]

SEND = '            self.sms.send(phone, f"Hi {customer}, {parcel_id} is out for delivery on van {van}.")\n'
MAKE_BODY = '            body = f"Hi {customer}, {parcel_id} is out for delivery on van {van}."\n'
VAN = '            self.db.execute("UPDATE vans SET space = space - 1 WHERE id = ?", (van,))\n'
OUTBOX = (
    '            self.db.execute("INSERT INTO outbox (phone, body) VALUES (?, ?)", (phone, body))\n'
)

WRONG: dict[int, list[tuple[str, str, list[Edit]]]] = {
    1: [
        (
            "send after the transaction",
            "case",
            [
                (SEND, MAKE_BODY),
                (VAN, VAN + "        self.sms.send(phone, body)\n"),
            ],
        ),
        (
            "send last, still inside the transaction",
            "case",
            [
                (SEND, MAKE_BODY),
                (VAN, VAN + "            self.sms.send(phone, body)\n"),
            ],
        ),
        (
            "use the outbox and still send directly",
            "solution",
            [(OUTBOX, OUTBOX + "            self.sms.send(phone, body)\n")],
        ),
    ],
    2: [
        (
            "one random key per event, made before the loop",
            "case",
            [
                (
                    "        for attempt in range(1, self.ATTEMPTS + 1):\n            key = uuid.uuid4().hex\n",
                    "        key = uuid.uuid4().hex\n        for attempt in range(1, self.ATTEMPTS + 1):\n",
                )
            ],
        ),
        (
            "key on the phone and the words",
            "case",
            [
                (
                    "            key = uuid.uuid4().hex\n",
                    '            key = f"{event.phone}:{body}"\n',
                )
            ],
        ),
        (
            "stop retrying",
            "case",
            [("    ATTEMPTS = 5\n", "    ATTEMPTS = 1\n")],
        ),
    ],
    3: [
        (
            "trust the scanner's timestamp",
            "case",
            [
                (
                    "    def receive(self, scan: Scan) -> None:\n",
                    "    def receive(self, scan: Scan) -> None:\n"
                    "        if any(s.parcel == scan.parcel and s.at >= scan.at for s in self.pushes):\n"
                    "            return\n",
                )
            ],
        ),
        (
            "never go back down the list of statuses",
            "case",
            [
                (
                    "    def receive(self, scan: Scan) -> None:\n",
                    "    def receive(self, scan: Scan) -> None:\n"
                    '        rank = ["at the depot", "out for delivery", "missed you, retrying", "delivered"]\n'
                    "        now = self.card.get(scan.parcel)\n"
                    "        if now and rank.index(scan.status) <= rank.index(now):\n"
                    "            return\n",
                )
            ],
        ),
        (
            "drop exact repeats only",
            "case",
            [
                (
                    "    def receive(self, scan: Scan) -> None:\n",
                    "    def receive(self, scan: Scan) -> None:\n"
                    "        if scan in self.pushes:\n"
                    "            return\n",
                )
            ],
        ),
    ],
    4: [
        (
            "never retry anything",
            "case",
            [
                (
                    '    return "retry"  # anything else might work next time\n',
                    '    return "reject"\n',
                )
            ],
        ),
        (
            "retry only server errors",
            "solution",
            [("    if status in (429, 500, 502, 503):\n", "    if status in (500, 502, 503):\n")],
        ),
        (
            "give up on a dead token, but keep it on file",
            "solution",
            [('        return "gone"  # the device', '        return "reject"  # the device')],
        ),
        (
            "treat a bad request as a dead token",
            "solution",
            [('    return "reject"  # 400 and friends', '    return "gone"  # 400 and friends')],
        ),
    ],
    5: [
        (
            "apply the offset the wrong way",
            "case",
            [
                (
                    "        clock = now.time()\n",
                    "        clock = (now - customer.zone.utcoffset(now)).time()\n",
                )
            ],
        ),
        (
            "drop anything that arrives in quiet hours",
            "solution",
            [("            self.held.append(push)\n", "            pass\n")],
        ),
        (
            "hold urgent pushes too",
            "solution",
            [
                (
                    "        if push.urgent or not self.is_quiet(push.customer, now):\n",
                    "        if not self.is_quiet(push.customer, now):\n",
                )
            ],
        ),
    ],
    6: [
        (
            "send every update at once",
            "case",
            [
                (
                    "        digest.due = min(now + QUIET, now + MAX_WAIT)\n",
                    "        digest.due = now\n",
                )
            ],
        ),
        (
            "wait up to thirty minutes from the latest update",
            "case",
            [
                (
                    "        digest.due = min(now + QUIET, now + MAX_WAIT)\n",
                    "        digest.due = now + MAX_WAIT\n",
                )
            ],
        ),
    ],
    7: [
        (
            "drop the campaign",
            "case",
            [
                (
                    "        self.items.append(text)\n",
                    '        if text.kind == "code":\n            self.items.append(text)\n',
                )
            ],
        ),
        (
            "newest first",
            "case",
            [("        return self.items.popleft()\n", "        return self.items.pop()\n")],
        ),
        (
            "sort the queue by kind, then by words",
            "case",
            [
                (
                    "        self.items.append(text)\n",
                    "        self.items.append(text)\n"
                    "        self.items = deque(sorted(self.items, key=lambda t: (t.kind, t.body)))\n",
                )
            ],
        ),
    ],
    8: [
        (
            "check the timestamp, remember nothing",
            "solution",
            [
                (
                    '        if event["id"] in self.seen:\n            return 200',
                    "        if False:\n            return 200",
                )
            ],
        ),
        (
            "remember receipt ids, ignore the timestamp",
            "solution",
            [("        if abs(self.now() - timestamp) > TOLERANCE:\n", "        if False:\n")],
        ),
        (
            "only accept receipts newer than the last one",
            "case",
            [
                (
                    "        return hmac.compare_digest(sign(timestamp, body), signature)\n",
                    "        if timestamp < getattr(self, 'latest', 0):\n"
                    "            return False\n"
                    "        self.latest = timestamp\n"
                    "        return hmac.compare_digest(sign(timestamp, body), signature)\n",
                )
            ],
        ),
    ],
}

RIGHT: dict[int, list[tuple[str, str, list[Edit]]]] = {
    2: [
        (
            "key on the parcel",
            "solution",
            [
                (
                    '        key = f"delivered:{event.id}"\n',
                    '        key = f"delivered:{event.parcel}"\n',
                )
            ],
        ),
        (
            "a uuid5 made from the event id",
            "solution",
            [
                (
                    '        key = f"delivered:{event.id}"\n',
                    "        import uuid\n\n        key = str(uuid.uuid5(uuid.NAMESPACE_URL, event.id))\n",
                )
            ],
        ),
    ],
    3: [
        (
            "compare with the last scan applied",
            "case",
            [
                (
                    "    def receive(self, scan: Scan) -> None:\n",
                    "    def receive(self, scan: Scan) -> None:\n"
                    "        mine = [s.seq for s in self.pushes if s.parcel == scan.parcel]\n"
                    "        if mine and scan.seq <= max(mine):\n"
                    "            return\n",
                )
            ],
        ),
    ],
    4: [
        (
            "retry 429 and every 5xx, forget on 404 or 410",
            "case",
            [
                (
                    '    return "retry"  # anything else might work next time\n',
                    "    if status in (404, 410):\n"
                    '        return "gone"\n'
                    "    if status == 429 or 500 <= status < 600:\n"
                    '        return "retry"\n'
                    '    return "reject"\n',
                )
            ],
        ),
    ],
    5: [
        (
            "add the offset by hand",
            "case",
            [
                (
                    "        clock = now.time()\n",
                    "        clock = (now + customer.zone.utcoffset(now)).time()\n",
                )
            ],
        ),
    ],
    6: [
        (
            "a fixed thirty minute window from the first update",
            "case",
            [
                (
                    "        digest.due = min(now + QUIET, now + MAX_WAIT)\n",
                    "        digest.due = digest.started + MAX_WAIT\n",
                )
            ],
        ),
    ],
    7: [
        (
            "a heap ordered by lane, then arrival",
            "case",
            [
                (
                    "    def __init__(self) -> None:\n        self.items: deque[Text] = deque()\n",
                    "    def __init__(self) -> None:\n"
                    "        import heapq\n\n"
                    "        self.heapq = heapq\n"
                    "        self.items: list = []\n"
                    "        self.count = 0\n",
                ),
                (
                    "        self.items.append(text)\n",
                    "        self.count += 1\n"
                    '        rank = 0 if text.kind == "code" else 1\n'
                    "        self.heapq.heappush(self.items, (rank, self.count, text))\n",
                ),
                (
                    "        return self.items.popleft()\n",
                    "        return self.heapq.heappop(self.items)[2]\n",
                ),
            ],
        ),
    ],
    8: [
        (
            "remember signatures instead of receipt ids",
            "solution",
            [
                (
                    '        if event["id"] in self.seen:\n',
                    '        if headers["Dove-Signature"] in self.seen:\n',
                ),
                (
                    '        self.seen[event["id"]] = int(headers["Dove-Timestamp"])\n',
                    '        self.seen[headers["Dove-Signature"]] = int(headers["Dove-Timestamp"])\n',
                ),
            ],
        ),
    ],
}


def build(number: int, base: str, edits: list[Edit]) -> types.ModuleType:
    name = CASES[number][0]
    folder = "cases" if base == "case" else "tests/solutions"
    source = (ROOT / folder / f"{name}.py").read_text()
    for old, new in edits:
        assert source.count(old) == 1, f"edit does not apply: {old!r}"
        source = source.replace(old, new)
    module = types.ModuleType(f"variant_{name}")
    sys.modules[module.__name__] = module  # dataclasses look their module up while building
    try:
        exec(compile(source, f"{name} (variant)", "exec"), module.__dict__)
    finally:
        del sys.modules[module.__name__]
    return module


def cases(table):
    return [
        pytest.param(number, base, edits, id=f"{number}-{label}")
        for number, fixes in table.items()
        for label, base, edits in fixes
    ]


@pytest.mark.parametrize(("number", "base", "edits"), cases(WRONG))
def test_a_wrong_fix_fails_its_check(number, base, edits):
    results = CHECKS[number](build(number, base, edits))

    assert not all(ok for _, ok in results)


@pytest.mark.parametrize(("number", "base", "edits"), cases(RIGHT))
def test_another_real_fix_passes(number, base, edits):
    failed = [label for label, ok in CHECKS[number](build(number, base, edits)) if not ok]

    assert failed == []


def test_every_case_has_at_least_two_wrong_fixes():
    assert all(len(WRONG.get(number, [])) >= 2 for number in CASES)
