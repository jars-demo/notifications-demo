"""Case 06: the newsletter after the unsubscribe.

Users choose which categories of notification they want. Security and billing notices are
required and always go out; product news and marketing are optional. Campaigns are queued in the
morning and sent at 10:00. The service checks preferences when it queues a notification. Two
users unsubscribe from marketing at 09:30. At 10:00 they get the campaign anyway.
Run it: uv run python -m notify run 6
"""

from dataclasses import dataclass, field

REQUIRED = {"security", "billing"}  # account notices a user cannot turn off


@dataclass
class Preferences:
    off: dict[str, set[str]] = field(default_factory=dict)  # user -> categories turned off

    def allows(self, user: str, category: str) -> bool:
        return category in REQUIRED or category not in self.off.get(user, set())

    def turn_off(self, user: str, categories: set[str]) -> None:
        self.off.setdefault(user, set()).update(categories)


@dataclass(frozen=True)
class Notification:
    user: str
    category: str
    subject: str
    send_at: int  # minutes after midnight


@dataclass
class Service:
    prefs: Preferences
    queue: list[Notification] = field(default_factory=list)
    sent: list[tuple[int, Notification]] = field(default_factory=list)

    def enqueue(self, notification: Notification) -> None:
        if self.prefs.allows(notification.user, notification.category):
            self.queue.append(notification)

    def tick(self, now: int) -> None:
        """Send everything that is due. Runs every minute."""
        due = [n for n in self.queue if n.send_at <= now]
        self.queue = [n for n in self.queue if n.send_at > now]
        for notification in due:
            self.sent.append((now, notification))


USERS = ["u_2001", "u_2002", "u_2003", "u_2004"]
CAMPAIGN = "Spring offer: 30% off annual plans"


def morning() -> Service:
    """09:00 the campaign is queued for 10:00 and a security notice for 10:05. u_2004 already
    turned marketing off last week. At 09:30 u_2001 and u_2002 unsubscribe, and u_2002 turns off
    every optional category it can."""
    prefs = Preferences({"u_2004": {"marketing"}})
    service = Service(prefs)
    for now in range(9 * 60, 11 * 60):
        if now == 9 * 60:
            for user in USERS:
                service.enqueue(Notification(user, "marketing", CAMPAIGN, 10 * 60))
            service.enqueue(
                Notification("u_2002", "security", "New sign-in from Firefox on Linux", 10 * 60 + 5)
            )
        if now == 9 * 60 + 30:
            prefs.turn_off("u_2001", {"marketing"})
            prefs.turn_off("u_2002", {"marketing", "product", "security"})
        service.tick(now)
    return service


def run() -> None:
    service = morning()
    print("09:00  the campaign is queued for every user, sending at 10:00")
    print("09:30  u_2001 and u_2002 unsubscribe from marketing")
    print()
    for when, notification in service.sent:
        print(
            f"{when // 60:02d}:{when % 60:02d}  {notification.user}  {notification.category:<9}  "
            f"{notification.subject}"
        )
    unsubscribed = [
        n.user
        for _, n in service.sent
        if n.category == "marketing" and n.user in {"u_2001", "u_2002"}
    ]
    print()
    print(f"marketing sent after an unsubscribe: {len(unsubscribed)}")
