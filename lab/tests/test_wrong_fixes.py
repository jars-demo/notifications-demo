"""The checks test the real goal, not the shape of one answer. Each wrong fix below is one people
really try: it makes the symptom go away, or looks right, and the check must still fail it. Each
other fix is a different, valid answer, and the check must pass it.

A fix is a list of (old, new) edits applied to the case as shipped ("case") or to its solution
("solution"). Every old string must appear exactly once, so a fix cannot silently stop applying.
"""

import types
from pathlib import Path

import pytest

from notify.__main__ import CASES
from notify.checks import CHECKS

ROOT = Path(__file__).resolve().parent.parent

Edit = tuple[str, str]

WRONG: dict[str, tuple[int, str, list[Edit]]] = {
    "01 send after commit, without an outbox": (
        1,
        "case",
        [
            ("            self.email.send(email, subject)\n", ""),
            (
                '                "UPDATE workspaces SET free_seats = free_seats - 1 WHERE id = ?", (workspace,)\n            )\n',
                '                "UPDATE workspaces SET free_seats = free_seats - 1 WHERE id = ?", (workspace,)\n            )\n        self.email.send(email, subject)\n',
            ),
        ],
    ),
    "02 dedupe by recipient": (
        2,
        "case",
        [("            key = uuid.uuid4().hex\n", "            key = event.email\n")],
    ),
    "03 never retry anything": (
        3,
        "case",
        [('    return "retry"  # anything else might work next time\n', '    return "reject"\n')],
    ),
    "04 a fixed delay": (
        4,
        "case",
        [("    return min(CAP, BASE * 2 ** (attempt - 1))\n", "    return 5.0\n")],
    ),
    "04 a little jitter on short waits": (
        4,
        "case",
        [("    return min(CAP, BASE * 2 ** (attempt - 1))\n", "    return rng.uniform(0, 1)\n")],
    ),
    "05 order by the reporting machine's clock": (
        5,
        "case",
        [
            (
                "    def receive(self, change: Change) -> None:\n",
                "    def receive(self, change: Change) -> None:\n"
                "        last = [c for c in self.notified if c.deployment == change.deployment]\n"
                "        if last and change.at <= last[-1].at:\n"
                "            return\n",
            )
        ],
    ),
    "05 drop a status that was already shown": (
        5,
        "case",
        [
            (
                "    def receive(self, change: Change) -> None:\n",
                "    def receive(self, change: Change) -> None:\n"
                "        if any(c.deployment == change.deployment and c.status == change.status"
                " for c in self.notified):\n"
                "            return\n",
            )
        ],
    ),
    "06 cancel everything queued when preferences change": (
        6,
        "case",
        [
            (
                '            prefs.turn_off("u_2002", {"marketing", "product", "security"})\n',
                '            prefs.turn_off("u_2002", {"marketing", "product", "security"})\n'
                "            service.queue = [n for n in service.queue"
                ' if n.user not in {"u_2001", "u_2002"}]\n',
            )
        ],
    ),
    "07 shift every user by London's offset": (
        7,
        "case",
        [("        clock = now.time()\n", "        clock = (now + timedelta(hours=0)).time()\n")],
    ),
    "08 send every update at once": (
        8,
        "case",
        [("        digest.due = min(now + QUIET, now + MAX_WAIT)\n", "        digest.due = now\n")],
    ),
    "09 send faster than the provider allows": (
        9,
        "case",
        [("RATE = 50  # messages a second", "RATE = 200  # messages a second")],
    ),
    "10 only check the timestamp": (
        10,
        "case",
        [
            (
                "        return hmac.compare_digest(sign(webhook_id, timestamp, body), signature)\n",
                "        if abs(self.now() - timestamp) > TOLERANCE:\n"
                "            return False\n"
                "        return hmac.compare_digest(sign(webhook_id, timestamp, body), signature)\n",
            )
        ],
    ),
}

RIGHT: dict[str, tuple[int, str, list[Edit]]] = {
    "06 check preferences both when queueing and when sending": (
        6,
        "solution",
        [
            (
                "    def enqueue(self, notification: Notification) -> None:\n"
                "        self.queue.append(notification)\n",
                "    def enqueue(self, notification: Notification) -> None:\n"
                "        if self.prefs.allows(notification.user, notification.category):\n"
                "            self.queue.append(notification)\n",
            )
        ],
    ),
    "09 a priority heap keyed on kind, then arrival": (
        9,
        "solution",
        [
            (
                "        return self.urgent.popleft() if self.urgent else self.bulk.popleft()\n",
                "        lane = self.urgent if self.urgent else self.bulk\n"
                "        return lane.popleft()\n",
            )
        ],
    ),
}


def load(number: int, source: str, edits: list[Edit]) -> types.ModuleType:
    name = CASES[number][0]
    path = ROOT / ("cases" if source == "case" else "tests/solutions") / f"{name}.py"
    text = path.read_text()
    for old, new in edits:
        assert text.count(old) == 1, f"edit does not apply: {old!r}"
        text = text.replace(old, new)
    module = types.ModuleType(f"variant_{name}")
    exec(compile(text, str(path), "exec"), module.__dict__)  # noqa: S102
    return module


@pytest.mark.parametrize("name", list(WRONG))
def test_check_rejects_a_wrong_fix(name):
    number, source, edits = WRONG[name]

    results = CHECKS[number](load(number, source, edits))

    assert not all(ok for _, ok in results), results


@pytest.mark.parametrize("name", list(RIGHT))
def test_check_accepts_another_real_fix(name):
    number, source, edits = RIGHT[name]

    results = CHECKS[number](load(number, source, edits))

    assert all(ok for _, ok in results), results
