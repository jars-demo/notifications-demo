"""Case 05: the 3 a.m. buzz.

Customers choose quiet hours: nothing but urgent pushes from 22:00 to 07:00. The scheduler holds
anything that arrives in that window and sends it at seven. It reads the clock in UTC, where the
servers live. Dovecote now delivers in Mumbai and Los Angeles too.
Run it: uv run python -m dove run 5
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, time, timedelta, timezone

QUIET_FROM = time(22, 0)
QUIET_UNTIL = time(7, 0)
TICK = timedelta(minutes=5)  # how often the scheduler looks at what it is holding


@dataclass(frozen=True)
class Customer:
    name: str
    zone: timezone  # a fixed offset: these dates are well clear of any clock change


@dataclass(frozen=True)
class Push:
    customer: Customer
    body: str
    urgent: bool = False


CUSTOMERS = {
    "Amara": Customer("Amara", timezone(timedelta(0), "London")),
    "Ravi": Customer("Ravi", timezone(timedelta(hours=5, minutes=30), "Mumbai")),
    "Lena": Customer("Lena", timezone(timedelta(hours=-8), "Los Angeles")),
}


def utc(day: int, hour: int, minute: int) -> datetime:
    return datetime(2026, 11, day, hour, minute, tzinfo=UTC)


A, R, L = CUSTOMERS["Amara"], CUSTOMERS["Ravi"], CUSTOMERS["Lena"]
PLAN = [  # when each push is created, in UTC
    (utc(12, 3, 0), Push(R, "Your parcel DC-5101 arrives today.")),
    (utc(12, 4, 10), Push(A, "Someone signed in to your account on a new phone.", urgent=True)),
    (utc(12, 6, 0), Push(L, "Your parcel DC-5102 arrives tomorrow.")),
    (utc(12, 15, 0), Push(L, "How did we do? Rate your delivery.")),
    (utc(12, 21, 35), Push(R, "How did we do? Rate your delivery.")),
    (utc(12, 23, 0), Push(A, "Your parcel DC-5103 arrives tomorrow.")),
]


@dataclass
class Scheduler:
    sent: list[tuple[datetime, Push]] = field(default_factory=list)
    held: list[Push] = field(default_factory=list)

    def is_quiet(self, customer: Customer, now: datetime) -> bool:
        """Quiet hours run from 22:00 to 07:00 on the customer's own clock."""
        clock = now.time()
        return clock >= QUIET_FROM or clock < QUIET_UNTIL

    def submit(self, push: Push, now: datetime) -> None:
        if push.urgent or not self.is_quiet(push.customer, now):
            self.sent.append((now, push))
        else:
            self.held.append(push)

    def tick(self, now: datetime) -> None:
        waiting, self.held = self.held, []
        for push in waiting:
            self.submit(push, now)


def two_days() -> Scheduler:
    scheduler = Scheduler()
    plan = sorted(PLAN, key=lambda item: item[0])
    now = utc(12, 0, 0)
    while now <= utc(13, 18, 0):
        scheduler.tick(now)
        for when, push in plan:
            if when == now:
                scheduler.submit(push, now)
        now += TICK
    return scheduler


def local(push: Push, when: datetime) -> str:
    return when.astimezone(push.customer.zone).strftime("%H:%M")


def quiet_on_their_clock(push: Push, when: datetime) -> bool:
    clock = when.astimezone(push.customer.zone).time()
    return clock >= QUIET_FROM or clock < QUIET_UNTIL


def run() -> None:
    scheduler = two_days()
    made = {push: when for when, push in PLAN}
    print(f"quiet hours: {QUIET_FROM:%H:%M} to {QUIET_UNTIL:%H:%M}, on each customer's clock")
    print("times below are on the customer's clock")
    print()
    for when, push in sorted(scheduler.sent, key=lambda item: made[item[1]]):
        start = made[push]
        note = ""
        if quiet_on_their_clock(push, when) and not push.urgent:
            note = "  <- buzzed in quiet hours"
        elif when > start and not quiet_on_their_clock(push, start):
            note = "  <- held in daytime"
        name = push.customer.name
        print(f"  {name:<6} made {local(push, start)}  sent {local(push, when)}  {push.body}{note}")
