"""Case 01: the text for a parcel that never left.

At seven every morning the dispatcher puts parcels on vans and texts each customer. The text goes
out from inside the database transaction. When a van is full the transaction rolls back and the
parcel stays in the depot, but the text has already gone. A customer waits all day for a parcel
that is still on a shelf.
Run it: uv run python -m dove run 1
"""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager


class Crash(Exception):
    """The dispatcher process dies. Whatever was committed stays committed."""


class Sms:
    """The SMS gateway. Once send returns, the text is on the customer's phone."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def send(self, phone: str, body: str) -> None:
        self.sent.append((phone, body))


PARCELS = [
    ("DC-1041", "Amara", "+44 7700 900101", 7),
    ("DC-1042", "Ben", "+44 7700 900102", 7),
    ("DC-1043", "Noor", "+44 7700 900103", 3),
    ("DC-1044", "Chen", "+44 7700 900104", 7),
    ("DC-1045", "Iris", "+44 7700 900105", 3),
]
VANS = {7: 3, 3: 0}  # van number: free space this morning. Van 3 came back full of returns.


class Depot:
    def __init__(self, sms: Sms) -> None:
        self.sms = sms
        self.db = sqlite3.connect(":memory:", isolation_level=None)
        self.db.executescript(
            """
            CREATE TABLE parcels (id TEXT PRIMARY KEY, customer TEXT, phone TEXT,
                                  status TEXT, van INTEGER);
            CREATE TABLE vans (id INTEGER PRIMARY KEY, space INTEGER CHECK (space >= 0));
            CREATE TABLE outbox (id INTEGER PRIMARY KEY, phone TEXT, body TEXT,
                                 sent INTEGER DEFAULT 0);
            """
        )
        for parcel_id, customer, phone, _ in PARCELS:
            self.db.execute(
                "INSERT INTO parcels VALUES (?, ?, ?, 'in the depot', NULL)",
                (parcel_id, customer, phone),
            )
        for van, space in VANS.items():
            self.db.execute("INSERT INTO vans VALUES (?, ?)", (van, space))
        self.crash_after_next_commit = False
        self.fail_next_commit = False

    @contextmanager
    def transaction(self) -> Iterator[None]:
        self.db.execute("BEGIN")
        try:
            yield
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        if self.fail_next_commit:  # the check uses this to make the commit itself fail
            self.fail_next_commit = False
            self.db.execute("ROLLBACK")
            raise sqlite3.OperationalError("disk I/O error")
        self.db.execute("COMMIT")
        if self.crash_after_next_commit:  # the check uses this to pull the plug
            self.crash_after_next_commit = False
            raise Crash

    def dispatch(self, parcel_id: str, van: int) -> None:
        with self.transaction():
            self.db.execute(
                "UPDATE parcels SET status = 'out for delivery', van = ? WHERE id = ?",
                (van, parcel_id),
            )
            customer, phone = self.db.execute(
                "SELECT customer, phone FROM parcels WHERE id = ?", (parcel_id,)
            ).fetchone()
            body = f"Hi {customer}, {parcel_id} is out for delivery on van {van}."
            # The text is written in the same transaction as the change. The relay sends it
            # only once that transaction has committed.
            self.db.execute("INSERT INTO outbox (phone, body) VALUES (?, ?)", (phone, body))
            # Fails with an IntegrityError when the van has no space left.
            self.db.execute("UPDATE vans SET space = space - 1 WHERE id = ?", (van,))

    def relay(self) -> None:
        """Send whatever is waiting in the outbox, oldest first. It runs every few seconds."""
        rows = self.db.execute(
            "SELECT id, phone, body FROM outbox WHERE sent = 0 ORDER BY id"
        ).fetchall()
        for row_id, phone, body in rows:
            self.sms.send(phone, body)
            self.db.execute("UPDATE outbox SET sent = 1 WHERE id = ?", (row_id,))

    def status(self, parcel_id: str) -> str:
        return self.db.execute("SELECT status FROM parcels WHERE id = ?", (parcel_id,)).fetchone()[
            0
        ]


def morning(
    crash_after: str | None = None, fail_commit: str | None = None
) -> tuple[Depot, Sms, list[str]]:
    """Put every parcel on its van. If crash_after names a parcel, the process dies straight
    after that parcel's commit, and a fresh dispatcher picks up where it left off. If
    fail_commit names one, the database refuses that parcel's commit."""
    sms = Sms()
    depot = Depot(sms)
    log = []
    for parcel_id, _, _, van in PARCELS:
        depot.crash_after_next_commit = parcel_id == crash_after
        depot.fail_next_commit = parcel_id == fail_commit
        try:
            depot.dispatch(parcel_id, van)
            log.append(f"{parcel_id}  van {van}  out for delivery")
        except sqlite3.IntegrityError:
            log.append(f"{parcel_id}  van {van}  van full, stays in the depot")
        except sqlite3.OperationalError:
            log.append(f"{parcel_id}  van {van}  commit failed, stays in the depot")
        except Crash:
            log.append(f"{parcel_id}  van {van}  committed, then the dispatcher crashed")
            depot.sms = sms  # the restarted process talks to the same gateway
        depot.relay()
    return depot, sms, log


def run() -> None:
    depot, sms, log = morning()
    print(f"dispatching {len(PARCELS)} parcels")
    for line in log:
        print(f"  {line}")
    print()
    print(f"texts sent: {len(sms.sent)}")
    wrong = [
        (parcel_id, customer)
        for parcel_id, customer, phone, _ in PARCELS
        if depot.status(parcel_id) == "in the depot" and any(p == phone for p, _ in sms.sent)
    ]
    print(f"texts for parcels still in the depot: {len(wrong)}")
    for parcel_id, customer in wrong:
        print(f"  {customer} was told {parcel_id} is out for delivery. It is on a shelf.")
