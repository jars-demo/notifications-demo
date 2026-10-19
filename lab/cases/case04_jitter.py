"""Case 04: the retry storm.

The SMS provider is down for 30 seconds. In that time 1,000 sends fail, and every worker backs
off exponentially: 1 s, 2 s, 4 s, up to 60 s, exactly as the textbook says. Every one of them
backs off by exactly the same amounts, so they all come back at exactly the same moments. When
the provider recovers, it accepts 100 requests a second and gets 1,000 at once, turns 900 away,
and those 900 come back together a minute later.
Run it: uv run python -m notify run 4
"""

import heapq
import random
from collections import Counter

CLIENTS = 1000
CAPACITY = 100  # requests a second the provider accepts once it is back; the rest get 429
OUTAGE_END = 30.0  # seconds: the provider fails every request before this
BASE = 1.0
CAP = 60.0


def backoff(attempt: int, rng: random.Random) -> float:
    """Seconds to wait before retry number `attempt` (1, 2, 3, ...)."""
    return min(CAP, BASE * 2 ** (attempt - 1))


def storm(seed: int = 7) -> tuple[Counter[int], dict[int, float], int]:
    """Every client sends at t=0 and retries until it gets through.

    Returns the requests made in each one-second window, when each client got through, and the
    total number of requests.
    """
    rng = random.Random(seed)
    queue = [(0.0, client, 1) for client in range(CLIENTS)]
    heapq.heapify(queue)
    per_second: Counter[int] = Counter()
    accepted: Counter[int] = Counter()
    done: dict[int, float] = {}
    while queue:
        when, client, attempt = heapq.heappop(queue)
        second = int(when)
        per_second[second] += 1
        if when >= OUTAGE_END and accepted[second] < CAPACITY:
            accepted[second] += 1
            done[client] = when
            continue
        heapq.heappush(queue, (when + backoff(attempt, rng), client, attempt + 1))
    return per_second, done, sum(per_second.values())


def run() -> None:
    per_second, done, total = storm()
    after = Counter({s: n for s, n in per_second.items() if s >= OUTAGE_END})
    peak_second, peak = after.most_common(1)[0]
    print(
        f"{CLIENTS} sends fail during a {OUTAGE_END:.0f} s outage; the provider then takes "
        f"{CAPACITY} a second"
    )
    print()
    print(
        f"busiest second after recovery: t={peak_second} s, {peak} requests "
        f"({peak / CAPACITY:.1f}x capacity)"
    )
    print(f"requests made:  {total}")
    print(f"last send got through at t={max(done.values()):.0f} s")
    print()
    print("seconds with any traffic, after the outage:")
    busy = [(s, n) for s, n in sorted(per_second.items()) if s >= OUTAGE_END]
    print("  " + ", ".join(f"t={s}: {n}" for s, n in busy[:8]) + (" ..." if len(busy) > 8 else ""))
