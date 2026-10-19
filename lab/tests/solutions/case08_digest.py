"""Case 08: the digest that never went out.

Every comment, review and status change in a project is an activity update, and nobody wants
forty pushes a day. So updates are gathered into a digest: one push, sent once things go quiet
for ten minutes, and never more than thirty minutes after the first update in it. The busiest
project gets an update every six minutes all day. Things never go quiet, and the thirty minute
promise is not kept.
Run it: uv run python -m notify run 8
"""

from dataclasses import dataclass, field

QUIET = 10  # minutes with no new update before a digest goes out
MAX_WAIT = 30  # and no update waits longer than this, however busy it gets


@dataclass
class Pending:
    started: int  # minute of the first update in this digest
    due: int  # minute the digest goes out
    updates: list[tuple[int, str]] = field(default_factory=list)


@dataclass
class Digests:
    pending: dict[str, Pending] = field(default_factory=dict)
    pushes: list[tuple[int, str, list[tuple[int, str]]]] = field(default_factory=list)

    def add(self, user: str, update: str, now: int) -> None:
        digest = self.pending.setdefault(user, Pending(started=now, due=now))
        digest.updates.append((now, update))
        # The cap counts from the first update, so a stream of updates cannot push it back.
        digest.due = min(now + QUIET, digest.started + MAX_WAIT)

    def tick(self, now: int) -> None:
        for user, digest in list(self.pending.items()):
            if now >= digest.due:
                self.pushes.append((now, user, digest.updates))
                del self.pending[user]


OPEN, CLOSE = 8 * 60, 18 * 60  # the working day, in minutes after midnight
BUSY, QUICK, ONCE = "u_4001", "u_4002", "u_4003"


def updates() -> list[tuple[int, str, str]]:
    busy = [(m, BUSY, f"activity on PR #{m}") for m in range(OPEN, CLOSE, 6)]
    quick = [(m, QUICK, f"review comment {n}") for n, m in enumerate((540, 542, 545), 1)]
    once = [(720, ONCE, "you were mentioned in #infra")]
    return sorted(busy + quick + once)


def day() -> Digests:
    digests = Digests()
    todo = updates()
    for now in range(OPEN, CLOSE + 120):  # one tick a minute, until well after the day ends
        digests.tick(now)
        while todo and todo[0][0] == now:
            _, user, update = todo.pop(0)
            digests.add(user, update, now)
    return digests


def hhmm(minute: int) -> str:
    return f"{minute // 60:02d}:{minute % 60:02d}"


def longest_wait(digests: Digests, user: str) -> int:
    waits = [sent - made for sent, who, items in digests.pushes if who == user for made, _ in items]
    return max(waits, default=0)


def run() -> None:
    digests = day()
    for user in (BUSY, QUICK, ONCE):
        wanted = sum(1 for _, who, _ in updates() if who == user)
        times = [hhmm(sent) for sent, who, _ in digests.pushes if who == user]
        count = len(times)
        print(f"{user}: {wanted} update{'s' * (wanted != 1)}, {count} push{'es' * (count != 1)}")
        print(f"  pushes at:    {', '.join(times[:6])}{' ...' if len(times) > 6 else ''}")
        print(f"  longest wait: {longest_wait(digests, user)} minutes")
