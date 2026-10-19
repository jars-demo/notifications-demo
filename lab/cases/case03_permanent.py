"""Case 03: the device that no longer exists.

The push worker retries every failed push with exponential backoff, up to eight times. That is
right for a busy or broken push service, and wrong for an answer that will never change. User
u_1042 replaced their phone months ago. The push service says the old token is gone, and the
worker keeps trying it on every push, forever, and never forgets it.
Run it: uv run python -m notify run 3
"""

import heapq
from dataclasses import dataclass

MAX_ATTEMPTS = 8
LIMIT = 200  # the push service rejects a payload longer than this


class PushService:
    """A fake push service. Its answers, as the real ones (APNs, FCM) document them:

    200 sent        429 too many requests, slow down    503 unavailable, try later
    400 bad request: this message can never be sent    410 gone: this device token is dead
    """

    def __init__(self, scripts: dict[str, list[int]], dead: set[str]) -> None:
        self.scripts = {token: list(codes) for token, codes in scripts.items()}
        self.dead = dead
        self.requests: dict[str, int] = {}
        self.delivered: list[tuple[str, str]] = []

    def push(self, token: str, body: str) -> int:
        self.requests[token] = self.requests.get(token, 0) + 1
        if token in self.dead:
            return 410
        if len(body) > LIMIT:
            return 400
        script = self.scripts.get(token)
        status = script.pop(0) if script else 200
        if status == 200:
            self.delivered.append((token, body))
        return status


def classify(status: int) -> str:
    """What to do with an answer: "done", "retry", "gone" (forget the token) or "reject"."""
    if status == 200:
        return "done"
    return "retry"  # anything else might work next time


@dataclass(order=True)
class Job:
    due: float
    seq: int
    user: str
    token: str
    body: str
    attempt: int = 1


class Worker:
    def __init__(self, service: PushService, devices: dict[str, set[str]]) -> None:
        self.service = service
        self.devices = devices
        self.dead_letters: list[Job] = []
        self.clock = 0.0
        self.queue: list[Job] = []
        self.seq = 0

    def notify(self, user: str, body: str) -> None:
        for token in sorted(self.devices[user]):
            self.seq += 1
            heapq.heappush(self.queue, Job(self.clock, self.seq, user, token, body))

    def drain(self) -> None:
        while self.queue:
            job = heapq.heappop(self.queue)
            self.clock = max(self.clock, job.due)
            outcome = classify(self.service.push(job.token, job.body))
            if outcome == "done":
                continue
            if outcome == "gone":
                self.devices[job.user].discard(job.token)
            elif outcome == "reject" or job.attempt == MAX_ATTEMPTS:
                self.dead_letters.append(job)
            else:  # back off: 1, 2, 4, 8 ... seconds
                job.due = self.clock + 2 ** (job.attempt - 1)
                job.attempt += 1
                heapq.heappush(self.queue, job)


DEVICES = {
    "u_1041": {"tok_1041_ios"},
    "u_1042": {"tok_1042_old", "tok_1042_new"},
    "u_1043": {"tok_1043_android"},
    "u_1044": {"tok_1044_ios"},
}
SCRIPTS = {
    "tok_1043_android": [429, 429],  # the push service is busy, then fine
    "tok_1044_ios": [503, 503, 503],  # a short outage, then fine
}
DEAD = {"tok_1042_old"}
ANNOUNCEMENT = "Release 4.2 is out: " + "faster sync, offline mode and a new dashboard. " * 5


def day() -> tuple[PushService, Worker]:
    """Two rounds of pushes, plus one push that is too long to ever be accepted."""
    service = PushService(SCRIPTS, DEAD)
    worker = Worker(service, {user: set(tokens) for user, tokens in DEVICES.items()})
    for user in DEVICES:
        worker.notify(user, "Build #418 failed on main.")
    worker.notify("u_1041", ANNOUNCEMENT)
    worker.drain()
    for user in DEVICES:
        worker.notify(user, "Build #419 passed on main.")
    worker.drain()
    return service, worker


def run() -> None:
    service, worker = day()
    print(f"pushes delivered: {len(service.delivered)}")
    print(f"requests made:    {sum(service.requests.values())}")
    print()
    for token, count in sorted(service.requests.items()):
        print(f"  {token:<17} requests: {count}")
    print()
    kept = "tok_1042_old" in worker.devices["u_1042"]
    print(f"u_1042's dead token still on file: {'yes' if kept else 'no'}")
    print(f"dead letters: {len(worker.dead_letters)}")
    for job in worker.dead_letters:
        print(f"  {job.token:<17} after {job.attempt} tries: {job.body[:30]}")
