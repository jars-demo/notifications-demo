"""Case 05: live, then building.

Every change to a deployment becomes an event: queued, building, live, failed. Each event
notifies the team and updates the deployment's status card in the app. Two queue workers share
the events, so they arrive out of order, and now and then twice. The app believes whatever
arrived last. dep_301 is live in production, and its card says it is still building.
Run it: uv run python -m notify run 5
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Change:
    deployment: str
    seq: int  # the deploy service numbers each deployment's changes 1, 2, 3, ... as they happen
    status: str
    at: str  # the clock of the machine that reported it, as HH:MM:SS


@dataclass
class App:
    cards: dict[str, str] = field(default_factory=dict)  # deployment -> status shown
    notified: list[Change] = field(default_factory=list)
    seen: dict[str, int] = field(default_factory=dict)  # deployment -> newest seq applied

    def receive(self, change: Change) -> None:
        # The deploy service's sequence number orders changes. Machine clocks cannot be trusted
        # to, and arrival order is whatever the queue made it. Older or repeated: drop it.
        if change.seq <= self.seen.get(change.deployment, 0):
            return
        self.seen[change.deployment] = change.seq
        self.cards[change.deployment] = change.status
        self.notified.append(change)


HAPPENED = [  # in the order the changes really happened
    Change("dep_301", 1, "queued", "10:58:10"),
    Change("dep_301", 2, "building", "10:58:12"),
    Change("dep_301", 3, "live", "10:54:40"),  # the deploy agent's clock runs four minutes slow
    Change("dep_302", 1, "queued", "10:59:30"),
    Change("dep_302", 2, "building", "10:59:31"),
    Change("dep_302", 3, "failed", "11:02:44"),
    Change("dep_302", 4, "building", "11:05:20"),  # retried by hand: building again
    Change("dep_303", 1, "queued", "11:01:00"),
    Change("dep_303", 2, "building", "11:01:02"),
    Change("dep_303", 3, "live", "11:04:05"),
]
H = HAPPENED
ARRIVED = [  # what two workers and one redelivery hand to the app
    H[0],
    H[3],
    H[2],  # dep_301 "live" overtook "building"
    H[7],
    H[1],
    H[4],
    H[4],  # a redelivered event: dep_302 "building" arrives twice
    H[5],
    H[6],
    H[9],  # dep_303 "live" overtook "building" too
    H[8],
]


def morning() -> App:
    app = App()
    for change in ARRIVED:
        app.receive(change)
    return app


def run() -> None:
    app = morning()
    final = {change.deployment: change.status for change in HAPPENED}
    print(f"changes: {len(HAPPENED)}, events delivered: {len(ARRIVED)}")
    print()
    for deployment in final:
        sent = ", ".join(c.status for c in app.notified if c.deployment == deployment)
        print(f"{deployment} notifications: {sent}")
        print(f"  card says: {app.cards[deployment]:<9} the truth: {final[deployment]}")
