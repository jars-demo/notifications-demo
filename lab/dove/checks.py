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


def texts_for(m: ModuleType, run: tuple) -> tuple[set[str], Counter[str]]:
    """Which customers' parcels really left, and how many texts each phone got."""
    depot, sms, _ = run
    left = {phone for pid, _, phone, _ in m.PARCELS if depot.status(pid) == "out for delivery"}
    return left, Counter(phone for phone, _ in sms.sent)


def check_01(m: ModuleType) -> list[Check]:
    runs = [
        attempt(m.morning),
        attempt(lambda: m.morning(crash_after="DC-1042")),
        attempt(lambda: m.morning(fail_commit="DC-1044")),
    ]
    for result in runs:
        if isinstance(result, Exception):
            return [(f"the morning dispatch runs (it raised {result!r})", False)]
    (left, texted), (c_left, c_texted), (f_left, f_texted) = (texts_for(m, r) for r in runs)
    return [
        (
            f"no text for a parcel that stayed in the depot ({len(set(texted) - left)} sent)",
            set(texted) <= left,
        ),
        (
            f"every parcel that left gets exactly one text ({len(left)} left)",
            len(left) == 3 and all(texted[phone] == 1 for phone in left),
        ),
        (
            "a crash straight after the commit still sends the text, once",
            c_left == left and all(c_texted[phone] == 1 for phone in c_left),
        ),
        (
            "no text when the commit itself fails",
            len(f_left) == 2 and set(f_texted) == f_left,
        ),
    ]


def check_02(m: ModuleType) -> list[Check]:
    result = attempt(m.afternoon)
    if isinstance(result, Exception):
        return [(f"the afternoon runs (it raised {result!r})", False)]
    gateway, _ = result
    amara, ben, chen = (m.texts_to(gateway, phone) for phone in (m.AMARA, m.BEN, m.CHEN))
    return [
        (f"Amara gets one text, despite two timeouts and a redelivery (got {amara})", amara == 1),
        (f"Ben gets his text, though the first try was refused (got {ben})", ben == 1),
        (f"Chen gets two texts for two parcels, though they read the same (got {chen})", chen == 2),
    ]


def check_03(m: ModuleType) -> list[Check]:
    phones = attempt(m.morning)
    if isinstance(phones, Exception):
        return [(f"the phones take the events (it raised {phones!r})", False)]
    final = {scan.parcel: scan for scan in m.HAPPENED}
    cards = all(phones[o].card.get(p) == final[p].status for p, o in m.OWNERS.items())
    forwards = all(
        [s.seq for s in phones[o].pushes if s.parcel == p]
        == sorted({s.seq for s in phones[o].pushes if s.parcel == p})
        for p, o in m.OWNERS.items()
    )
    newest = all(any(s.seq == final[p].seq for s in phones[o].pushes) for p, o in m.OWNERS.items())
    ben = ", ".join(scan.status for scan in phones["Ben"].pushes)
    return [
        ("every lock screen ends on the parcel's latest status", cards),
        (f"pushes never go backwards or repeat (Ben got: {ben})", forwards),
        ("the newest scan of every parcel is pushed", newest),
    ]


def check_04(m: ModuleType) -> list[Check]:
    result = attempt(m.day)
    if isinstance(result, Exception):
        return [(f"the push worker runs (it raised {result!r})", False)]
    service, worker = result
    delivered = Counter(token for token, _ in service.delivered)
    live = ["amara-phone", "ben-new-phone", "chen-phone", "noor-phone"]
    old = service.requests.get("ben-old-phone", 0)
    catalogue = [job for job in worker.dead_letters if job.body == m.CATALOGUE]
    return [
        (
            "every live phone gets both pushes, through the 429s and the 503s",
            all(delivered[token] == 2 for token in live),
        ),
        (
            f"Ben's dead token is tried once, then forgotten (tried {old})",
            old == 1 and "ben-old-phone" not in worker.devices["Ben"],
        ),
        (
            "the push that is too long goes to dead letters after one try",
            len(catalogue) == 1 and catalogue[0].attempt == 1,
        ),
        (
            f"no request is wasted: 15 in all ({sum(service.requests.values())})",
            sum(service.requests.values()) == 15,
        ),
    ]


def on_their_clock(push: object, when: datetime) -> time:
    return when.astimezone(push.customer.zone).time()


def quiet(push: object, when: datetime) -> bool:
    clock = on_their_clock(push, when)
    return clock >= time(22, 0) or clock < time(7, 0)


def check_05(m: ModuleType) -> list[Check]:
    result = attempt(m.two_days)
    if isinstance(result, Exception):
        return [(f"the scheduler runs (it raised {result!r})", False)]
    sent = {push: when for when, push in result.sent}
    made = {push: when for when, push in m.PLAN}
    ordinary = [push for push in made if not push.urgent]
    woken = [
        f"{push.customer.name} at {on_their_clock(push, sent[push]):%H:%M}"
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
            f"every held push goes out at 07:00 on the customer's clock ({len(held)} held)",
            len(held) == 3 and on_time,
        ),
        (f"a daytime push goes out at once ({len(daytime)} held by mistake)", not daytime),
        ("an urgent push is never held", all(sent.get(p) == made[p] for p in urgent)),
    ]


def check_06(m: ModuleType) -> list[Check]:
    result = attempt(m.day)
    if isinstance(result, Exception):
        return [(f"the day runs (it raised {result!r})", False)]
    pushes = result.pushes
    kiln = sum(1 for _, who, _ in pushes if who == "Kiln & Co")
    wait = m.longest_wait(result, "Kiln & Co")
    amara = [items for _, who, items in pushes if who == "Amara"]
    carried = sorted((made, who, update) for _, who, items in pushes for made, update in items)
    return [
        (f"Kiln & Co hears within 30 minutes of every update (longest {wait})", wait <= 30),
        (f"Kiln & Co gets a digest, not a buzz per update ({kiln} sent)", 0 < kiln <= 25),
        ("Amara's three quick updates arrive in one push", len(amara) == 1 and len(amara[0]) == 3),
        ("every update is in exactly one push", carried == m.updates()),
    ]


def check_07(m: ModuleType) -> list[Check]:
    sent = attempt(m.morning)
    if isinstance(sent, Exception):
        return [(f"the sender runs (it raised {sent!r})", False)]
    codes = [(when, text) for when, text in sent if text.kind == "code"]
    waits = {text.to: when - text.made for when, text in codes}
    offers = [text.body for _, text in sent if text.kind == "bulk"]
    expected = [text.body for text in m.arrivals() if text.kind == "bulk"]
    shown = ", ".join(f"{who} {wait:.1f} s" for who, wait in waits.items())
    return [
        (
            f"each login code arrives within 5 seconds ({shown})",
            len(waits) == 2 and all(wait <= 5 for wait in waits.values()),
        ),
        (
            "codes go out in the order they were asked for",
            [t.to for _, t in codes] == ["Amara", "Ben"],
        ),
        (f"all 6000 offers still go out, in order ({len(offers)} sent)", offers == expected),
        (
            "the sender keeps to 50 texts a second",
            m.RATE == 50 and all(b - a >= 1 / 50 - 1e-9 for (a, _), (b, _) in pairwise(sent)),
        ),
    ]


def check_08(m: ModuleType) -> list[Check]:
    result = attempt(m.replayed)
    if isinstance(result, Exception):
        return [(f"the webhook receiver runs (it raised {result!r})", False)]
    receiver, answers = result
    clock = {"now": m.TODAY}
    fresh = m.Receiver(lambda: clock["now"])
    first = m.receipt("rc-1", "msg-40", "failed", m.TODAY - 20)
    second = m.receipt("rc-2", "msg-41", "delivered", m.TODAY - 5)
    genuine = [fresh.handle(*second), fresh.handle(*first)]
    repeats = [fresh.handle(*first) for _ in range(20)]
    restarted = m.Receiver(lambda: m.TODAY)  # a fresh process remembers nothing
    stale = restarted.handle(*m.receipt("rc-9001", "msg-17", "failed", m.YESTERDAY))
    headers, body = m.receipt("rc-3", "msg-42", "failed", m.TODAY)
    forged = fresh.handle({**headers, "Dove-Signature": "0" * 64}, body)
    tampered = fresh.handle(headers, body.replace(b"msg-42", b"msg-43"))
    return [
        (
            "genuine receipts are accepted, even out of order",
            genuine == [200, 200] and fresh.status == {"msg-40": "failed", "msg-41": "delivered"},
        ),
        ("a forged or tampered receipt is refused", forged >= 400 and tampered >= 400),
        (
            f"yesterday's receipt sent again today is refused ({answers[1:].count(200)} accepted)",
            answers[0] == 200
            and 200 not in answers[1:]
            and receiver.status["msg-17"] == "delivered"
            and stale >= 400
            and not restarted.resent,
        ),
        (
            "a receipt repeated within a minute is acted on once"
            f" (sent again {len(fresh.resent)}x)",
            fresh.resent == ["msg-40"] and all(code < 500 for code in repeats),
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
}
