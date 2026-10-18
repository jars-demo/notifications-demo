"""Case 06: silence at the busy shop.

Every scan of every parcel is an update, and nobody wants forty buzzes a day. So updates are
gathered into a digest: one push, sent once things go quiet for ten minutes, and never more than
thirty minutes after the first update in it. Kiln & Co, a pottery shop, gets a parcel scan every
six minutes all day. Things never go quiet, and the thirty minute promise is not kept.
Run it: uv run python -m dove run 6
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

    def add(self, customer: str, update: str, now: int) -> None:
        digest = self.pending.setdefault(customer, Pending(started=now, due=now))
        digest.updates.append((now, update))
        digest.due = min(now + QUIET, now + MAX_WAIT)

    def tick(self, now: int) -> None:
        for customer, digest in list(self.pending.items()):
            if now >= digest.due:
                self.pushes.append((now, customer, digest.updates))
                del self.pending[customer]


OPEN, CLOSE = 8 * 60, 18 * 60  # the working day, in minutes after midnight


def updates() -> list[tuple[int, str, str]]:
    kiln = [(m, "Kiln & Co", f"DC-6{m:03d} scanned") for m in range(OPEN, CLOSE, 6)]
    amara = [(m, "Amara", f"DC-61{n} scanned") for n, m in enumerate((540, 542, 545))]
    ben = [(720, "Ben", "DC-6200 scanned")]
    return sorted(kiln + amara + ben)


def day() -> Digests:
    digests = Digests()
    todo = updates()
    for now in range(OPEN, CLOSE + 120):  # one tick a minute, until well after closing
        digests.tick(now)
        while todo and todo[0][0] == now:
            _, customer, update = todo.pop(0)
            digests.add(customer, update, now)
    return digests


def hhmm(minute: int) -> str:
    return f"{minute // 60:02d}:{minute % 60:02d}"


def longest_wait(digests: Digests, customer: str) -> int:
    waits = [
        sent - made for sent, who, items in digests.pushes if who == customer for made, _ in items
    ]
    return max(waits, default=0)


def run() -> None:
    digests = day()
    for customer in ("Kiln & Co", "Amara", "Ben"):
        wanted = sum(1 for _, who, _ in updates() if who == customer)
        times = [hhmm(sent) for sent, who, _ in digests.pushes if who == customer]
        count = len(times)
        print(
            f"{customer}: {wanted} update{'s' * (wanted != 1)}, {count} push{'es' * (count != 1)}"
        )
        print(f"  pushes at:    {', '.join(times[:6])}{' ...' if len(times) > 6 else ''}")
        print(f"  longest wait: {longest_wait(digests, customer)} minutes")
