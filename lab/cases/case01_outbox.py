"""Case 01: the invitation to a team that never happened.

A workspace admin invites people. The service adds a membership, emails the invite, and takes a
seat on the workspace's plan, all inside one database transaction. When the plan is full, the
seat CHECK fails and the transaction rolls back: no membership. But the email has already gone.
Run it: uv run python -m notify run 1
"""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager


class Crash(Exception):
    """The API process dies. Whatever was committed stays committed."""


class EmailProvider:
    """The email provider. Once send returns, the email is in the recipient's inbox."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def send(self, to: str, subject: str) -> None:
        self.sent.append((to, subject))


INVITES = [
    ("ws_acme", "dana@example.com"),
    ("ws_acme", "eli@example.com"),
    ("ws_orbit", "fay@example.com"),
    ("ws_acme", "gus@example.com"),
    ("ws_orbit", "hal@example.com"),
]
SEATS = {"ws_acme": 3, "ws_orbit": 0}  # free seats. ws_orbit is on a plan that is already full.


class Service:
    def __init__(self, email: EmailProvider) -> None:
        self.email = email
        self.db = sqlite3.connect(":memory:", isolation_level=None)
        self.db.executescript(
            """
            CREATE TABLE workspaces (id TEXT PRIMARY KEY, free_seats INTEGER
                                     CHECK (free_seats >= 0));
            CREATE TABLE memberships (workspace TEXT, email TEXT, PRIMARY KEY (workspace, email));
            CREATE TABLE outbox (id INTEGER PRIMARY KEY, recipient TEXT, subject TEXT,
                                 sent INTEGER DEFAULT 0);
            """
        )
        for workspace, seats in SEATS.items():
            self.db.execute("INSERT INTO workspaces VALUES (?, ?)", (workspace, seats))
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

    def invite(self, workspace: str, email: str) -> None:
        with self.transaction():
            self.db.execute("INSERT INTO memberships VALUES (?, ?)", (workspace, email))
            subject = f"You have been added to {workspace}"
            self.email.send(email, subject)
            # Fails with an IntegrityError when the workspace has no free seat.
            self.db.execute(
                "UPDATE workspaces SET free_seats = free_seats - 1 WHERE id = ?", (workspace,)
            )

    def relay(self) -> None:
        """Send whatever is waiting in the outbox, oldest first. It runs every few seconds."""
        rows = self.db.execute(
            "SELECT id, recipient, subject FROM outbox WHERE sent = 0 ORDER BY id"
        ).fetchall()
        for row_id, recipient, subject in rows:
            self.email.send(recipient, subject)
            self.db.execute("UPDATE outbox SET sent = 1 WHERE id = ?", (row_id,))

    def is_member(self, workspace: str, email: str) -> bool:
        row = self.db.execute(
            "SELECT 1 FROM memberships WHERE workspace = ? AND email = ?", (workspace, email)
        ).fetchone()
        return row is not None


def batch(
    crash_after: str | None = None, fail_commit: str | None = None
) -> tuple[Service, EmailProvider, list[str]]:
    """Send every invite. If crash_after names an email, the process dies straight after that
    invite's commit, and a restarted process carries on. If fail_commit names one, the database
    refuses that invite's commit."""
    email = EmailProvider()
    service = Service(email)
    log = []
    for workspace, address in INVITES:
        service.crash_after_next_commit = address == crash_after
        service.fail_next_commit = address == fail_commit
        try:
            service.invite(workspace, address)
            log.append(f"{address:<18} {workspace:<9} added")
        except sqlite3.IntegrityError:
            log.append(f"{address:<18} {workspace:<9} no free seat, rolled back")
        except sqlite3.OperationalError:
            log.append(f"{address:<18} {workspace:<9} commit failed, rolled back")
        except Crash:
            log.append(f"{address:<18} {workspace:<9} committed, then the process crashed")
        service.relay()
    return service, email, log


def run() -> None:
    service, email, log = batch()
    print(f"sending {len(INVITES)} invitations")
    for line in log:
        print(f"  {line}")
    print()
    print(f"emails sent: {len(email.sent)}")
    wrong = [
        (address, workspace)
        for workspace, address in INVITES
        if not service.is_member(workspace, address) and any(to == address for to, _ in email.sent)
    ]
    print(f"emails for memberships that do not exist: {len(wrong)}")
    for address, workspace in wrong:
        print(f"  {address} was told they joined {workspace}. They did not.")
