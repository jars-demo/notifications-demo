"""Case 07: the 3 a.m. buzz.

Users choose quiet hours: nothing but urgent pushes from 22:00 to 07:00. The scheduler holds
anything that arrives in that window and sends it at seven. It reads the clock in UTC, where the
servers live. The product now has users in Mumbai and Los Angeles too.
Run it: uv run python -m notify run 7
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, time, timedelta, timezone

QUIET_FROM = time(22, 0)
QUIET_UNTIL = time(7, 0)
TICK = timedelta(minutes=5)  # how often the scheduler looks at what it is holding


@dataclass(frozen=True)
class User:
    id: str
    zone: timezone  # a fixed offset: these dates are well clear of any clock change


@dataclass(frozen=True)
class Push:
    user: User
    body: str
    urgent: bool = False


USERS = {
    "u_3001": User("u_3001", timezone(timedelta(0), "London")),
    "u_3002": User("u_3002", timezone(timedelta(hours=5, minutes=30), "Mumbai")),
    "u_3003": User("u_3003", timezone(timedelta(hours=-8), "Los Angeles")),
}


def utc(day: int, hour: int, minute: int) -> datetime:
    return datetime(2026, 11, day, hour, minute, tzinfo=UTC)


LON, BOM, LAX = USERS["u_3001"], USERS["u_3002"], USERS["u_3003"]
PLAN = [  # when each push is created, in UTC
    (utc(12, 3, 0), Push(BOM, "Your weekly usage report is ready.")),
    (utc(12, 4, 10), Push(LON, "New sign-in to your account from Chrome on Windows.", urgent=True)),
    (utc(12, 6, 0), Push(LAX, "Your trial ends tomorrow.")),
    (utc(12, 15, 0), Push(LAX, "Priya commented on your pull request.")),
    (utc(12, 21, 35), Push(BOM, "Priya commented on your pull request.")),
    (utc(12, 23, 0), Push(LON, "Your trial ends tomorrow.")),
]


@dataclass
class Scheduler:
    sent: list[tuple[datetime, Push]] = field(default_factory=list)
    held: list[Push] = field(default_factory=list)

    def is_quiet(self, user: User, now: datetime) -> bool:
        """Quiet hours run from 22:00 to 07:00 on the user's own clock."""
        clock = now.astimezone(user.zone).time()  # their wall clock, not the server's
        return clock >= QUIET_FROM or clock < QUIET_UNTIL

    def submit(self, push: Push, now: datetime) -> None:
        if push.urgent or not self.is_quiet(push.user, now):
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
    return when.astimezone(push.user.zone).strftime("%H:%M")


def quiet_on_their_clock(push: Push, when: datetime) -> bool:
    clock = when.astimezone(push.user.zone).time()
    return clock >= QUIET_FROM or clock < QUIET_UNTIL


def run() -> None:
    scheduler = two_days()
    made = {push: when for when, push in PLAN}
    print(f"quiet hours: {QUIET_FROM:%H:%M} to {QUIET_UNTIL:%H:%M}, on each user's clock")
    print("times below are on the user's clock")
    print()
    for when, push in sorted(scheduler.sent, key=lambda item: made[item[1]]):
        start = made[push]
        note = ""
        if quiet_on_their_clock(push, when) and not push.urgent:
            note = "  <- buzzed in quiet hours"
        elif when > start and not quiet_on_their_clock(push, start):
            note = "  <- held in daytime"
        print(
            f"  {push.user.id}  made {local(push, start)}  sent {local(push, when)}  "
            f"{push.body}{note}"
        )
