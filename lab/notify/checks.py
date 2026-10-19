"""How each case is checked. Every check takes the case module, so the tests can check a fixed
copy too. A check says what it expects in plain words.

A notification has to reach the right person, once, at the right time. Every check tests that
the message still arrives as well as that the bug is gone, so sending nothing is never a fix."""

from collections import Counter
from collections.abc import Callable
from datetime import datetime, time
from itertools import pairwise
from types import ModuleType

Check = tuple[str, bool]


def attempt(fn: Callable[[], object]) -> object:
    """Run fn and return its result, or the exception it raised."""
    try:
        return fn()
    except Exception as error:  # a crash is an answer too
        return error


def emails_for(m: ModuleType, run: tuple) -> tuple[set[str], Counter[str]]:
    """Which invites really became memberships, and how many emails each address got."""
    service, email, _ = run
    joined = {address for workspace, address in m.INVITES if service.is_member(workspace, address)}
    return joined, Counter(to for to, _ in email.sent)


def check_01(m: ModuleType) -> list[Check]:
    runs = [
        attempt(m.batch),
        attempt(lambda: m.batch(crash_after="eli@example.com")),
        attempt(lambda: m.batch(fail_commit="gus@example.com")),
    ]
    for result in runs:
        if isinstance(result, Exception):
            return [(f"the invitations run (it raised {result!r})", False)]
    (joined, emailed), (c_joined, c_emailed), (f_joined, f_emailed) = (
        emails_for(m, r) for r in runs
    )
    return [
        (
            f"no email for an invite that rolled back ({len(set(emailed) - joined)} sent)",
            set(emailed) <= joined,
        ),
        (
            f"every new member gets exactly one email ({len(joined)} joined)",
            len(joined) == 3 and all(emailed[address] == 1 for address in joined),
        ),
        (
            "a crash straight after the commit still sends the email, once",
            c_joined == joined and all(c_emailed[address] == 1 for address in c_joined),
        ),
        (
            "no email when the commit itself fails",
            len(f_joined) == 2 and set(f_emailed) == f_joined,
        ),
    ]


def check_02(m: ModuleType) -> list[Check]:
    api = attempt(m.afternoon)
    if isinstance(api, Exception):
        return [(f"the worker runs (it raised {api!r})", False)]
    ada, ben, cy = (
        api.count(email) for email in ("ada@example.com", "ben@example.com", "cy@example.com")
    )
    return [
        (
            f"one receipt for evt_501, despite two lost answers and a redelivery (got {ada})",
            ada == 1,
        ),
        (f"a receipt for evt_502, though the first request was turned away (got {ben})", ben == 1),
        (f"two receipts for two payments that read the same (got {cy})", cy == 2),
    ]


def check_03(m: ModuleType) -> list[Check]:
    result = attempt(m.day)
    if isinstance(result, Exception):
        return [(f"the push worker runs (it raised {result!r})", False)]
    service, worker = result
    delivered = Counter(token for token, _ in service.delivered)
    live = ["tok_1041_ios", "tok_1042_new", "tok_1043_android", "tok_1044_ios"]
    old = service.requests.get("tok_1042_old", 0)
    announcement = [job for job in worker.dead_letters if job.body == m.ANNOUNCEMENT]
    return [
        (
            "every live device gets both pushes, through the 429s and the 503s",
            all(delivered[token] == 2 for token in live),
        ),
        (
            f"the dead token is tried once, then forgotten (tried {old})",
            old == 1 and "tok_1042_old" not in worker.devices["u_1042"],
        ),
        (
            "the push that is too long goes to dead letters after one try",
            len(announcement) == 1 and announcement[0].attempt == 1,
        ),
        (
            f"no request is wasted: 15 in all ({sum(service.requests.values())})",
            sum(service.requests.values()) == 15,
        ),
    ]


def check_04(m: ModuleType) -> list[Check]:
    results = [attempt(lambda seed=seed: m.storm(seed)) for seed in (7, 8, 9)]
    for result in results:
        if isinstance(result, Exception):
            return [(f"the storm runs (it raised {result!r})", False)]
    peaks, finishes, totals = [], [], []
    for per_second, done, total in results:
        after = [n for second, n in per_second.items() if second >= m.OUTAGE_END]
        peaks.append(max(after, default=0))
        finishes.append(max(done.values(), default=float("inf")))
        totals.append(total)
    return [
        (
            f"every send gets through ({min(len(r[1]) for r in results)} of {m.CLIENTS})",
            all(len(done) == m.CLIENTS for _, done, _ in results),
        ),
        (
            f"after recovery, no second sees more than twice the capacity (busiest {max(peaks)})",
            max(peaks) <= 2 * m.CAPACITY,
        ),
        (
            f"everyone is through within two minutes (last at {max(finishes):.0f} s)",
            max(finishes) <= 120,
        ),
        (
            f"retries stay bounded: under 10,000 requests in all ({max(totals):,})",
            max(totals) < 10_000,
        ),
    ]


def check_05(m: ModuleType) -> list[Check]:
    app = attempt(m.morning)
    if isinstance(app, Exception):
        return [(f"the app takes the events (it raised {app!r})", False)]
    final = {change.deployment: change for change in m.HAPPENED}
    cards = all(app.cards.get(d) == change.status for d, change in final.items())
    seqs = {d: [c.seq for c in app.notified if c.deployment == d] for d in final}
    forwards = all(s == sorted(set(s)) for s in seqs.values())
    newest = all(final[d].seq in seqs[d] for d in final)
    shown = ", ".join(c.status for c in app.notified if c.deployment == "dep_301")
    return [
        ("every card ends on the deployment's latest status", cards),
        (f"notifications never go backwards or repeat (dep_301: {shown})", forwards),
        ("the newest change of every deployment is notified, even a repeated status", newest),
    ]


def check_06(m: ModuleType) -> list[Check]:
    service = attempt(m.morning)
    if isinstance(service, Exception):
        return [(f"the service runs (it raised {service!r})", False)]
    marketing = {n.user for _, n in service.sent if n.category == "marketing"}
    security = [n for _, n in service.sent if n.category == "security"]
    return [
        (
            f"no marketing after an unsubscribe ({len(marketing & {'u_2001', 'u_2002'})} sent)",
            not marketing & {"u_2001", "u_2002"},
        ),
        ("the campaign reaches exactly the users still subscribed", marketing == {"u_2003"}),
        ("nobody who opted out last week gets it", "u_2004" not in marketing),
        (
            "the security notice still arrives, though u_2002 turned everything off",
            len(security) == 1 and security[0].user == "u_2002",
        ),
    ]


def on_their_clock(push: object, when: datetime) -> time:
    return when.astimezone(push.user.zone).time()


def quiet(push: object, when: datetime) -> bool:
    clock = on_their_clock(push, when)
    return clock >= time(22, 0) or clock < time(7, 0)


def check_07(m: ModuleType) -> list[Check]:
    result = attempt(m.two_days)
    if isinstance(result, Exception):
        return [(f"the scheduler runs (it raised {result!r})", False)]
    sent = {push: when for when, push in result.sent}
    made = {push: when for when, push in m.PLAN}
    ordinary = [push for push in made if not push.urgent]
    woken = [
        f"{push.user.id} at {on_their_clock(push, sent[push]):%H:%M}"
        for push in ordinary
        if push in sent and quiet(push, sent[push])
    ]
    held = [push for push in ordinary if quiet(push, made[push])]
    on_time = all(push in sent and on_their_clock(push, sent[push]) == time(7, 0) for push in held)
    daytime = [p for p in ordinary if not quiet(p, made[p]) and sent.get(p) != made[p]]
    urgent = [push for push in made if push.urgent]
    return [
        (f"nobody is buzzed in their quiet hours ({', '.join(woken) or 'nobody'})", not woken),
        (
            f"every held push goes out at 07:00 on the user's clock ({len(held)} held)",
            len(held) == 3 and on_time,
        ),
        (f"a daytime push goes out at once ({len(daytime)} held by mistake)", not daytime),
        ("an urgent push is never held", all(sent.get(p) == made[p] for p in urgent)),
    ]


def check_08(m: ModuleType) -> list[Check]:
    result = attempt(m.day)
    if isinstance(result, Exception):
        return [(f"the day runs (it raised {result!r})", False)]
    pushes = result.pushes
    busy = sum(1 for _, who, _ in pushes if who == m.BUSY)
    wait = m.longest_wait(result, m.BUSY)
    quick = [items for _, who, items in pushes if who == m.QUICK]
    carried = sorted((made, who, update) for _, who, items in pushes for made, update in items)
    return [
        (f"the busy user hears within 30 minutes of every update (longest {wait})", wait <= 30),
        (f"the busy user gets digests, not a push per update ({busy} sent)", 0 < busy <= 25),
        ("three quick updates arrive in one push", len(quick) == 1 and len(quick[0]) == 3),
        ("every update is in exactly one push", carried == m.updates()),
    ]


def check_09(m: ModuleType) -> list[Check]:
    sent = attempt(m.morning)
    if isinstance(sent, Exception):
        return [(f"the sender runs (it raised {sent!r})", False)]
    codes = [(when, message) for when, message in sent if message.kind == "code"]
    waits = {message.to: when - message.made for when, message in codes}
    bulk = [message.body for _, message in sent if message.kind == "bulk"]
    expected = [message.body for message in m.arrivals() if message.kind == "bulk"]
    shown = ", ".join(f"{who} {wait:.1f} s" for who, wait in waits.items())
    return [
        (
            f"each sign-in code arrives within 5 seconds ({shown})",
            len(waits) == 2 and all(wait <= 5 for wait in waits.values()),
        ),
        (
            "codes go out in the order they were asked for",
            [message.to for _, message in codes] == ["u_5001", "u_5002"],
        ),
        (f"all 6000 announcements still go out, in order ({len(bulk)} sent)", bulk == expected),
        (
            "the sender keeps to 50 messages a second",
            m.RATE == 50 and all(b - a >= 1 / 50 - 1e-9 for (a, _), (b, _) in pairwise(sent)),
        ),
    ]


def check_10(m: ModuleType) -> list[Check]:
    result = attempt(m.replayed)
    if isinstance(result, Exception):
        return [(f"the webhook receiver runs (it raised {result!r})", False)]
    receiver, answers = result
    fresh = m.Receiver(lambda: m.TODAY)
    first = m.receipt("wh_1", "msg_40", "failed", m.TODAY - 20)
    second = m.receipt("wh_2", "msg_41", "delivered", m.TODAY - 5)
    genuine = [fresh.handle(*second), fresh.handle(*first)]
    repeats = [fresh.handle(*first) for _ in range(20)]
    restarted = m.Receiver(lambda: m.TODAY)  # a fresh process remembers nothing
    stale = restarted.handle(*m.receipt("wh_9001", "msg_17", "failed", m.YESTERDAY))
    headers, body = m.receipt("wh_3", "msg_42", "failed", m.TODAY)
    forged = fresh.handle({**headers, "webhook-signature": "v1," + "A" * 44}, body)
    tampered = fresh.handle(headers, body.replace(b"msg_42", b"msg_43"))
    return [
        (
            "genuine receipts are accepted, even out of order",
            genuine == [200, 200] and fresh.status == {"msg_40": "failed", "msg_41": "delivered"},
        ),
        ("a forged or tampered receipt is refused", forged >= 400 and tampered >= 400),
        (
            f"yesterday's receipt sent again today is refused ({answers[1:].count(200)} accepted)",
            answers[0] == 200
            and 200 not in answers[1:]
            and receiver.status["msg_17"] == "delivered"
            and stale >= 400
            and not restarted.resent,
        ),
        (
            f"a receipt repeated within a minute is acted on once (resent {len(fresh.resent)}x)",
            fresh.resent == ["msg_40"] and all(code < 500 for code in repeats),
        ),
    ]


CHECKS: dict[int, Callable[[ModuleType], list[Check]]] = {
    1: check_01,
    2: check_02,
    3: check_03,
    4: check_04,
    5: check_05,
    6: check_06,
    7: check_07,
    8: check_08,
    9: check_09,
    10: check_10,
}
