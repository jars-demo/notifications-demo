"""notify: ten bugs in a real notification service, one per chapter.

list        every case, and which ones are fixed
run N       run case N and watch the bug happen
check N     check your fix: the bug is gone, and the message still arrives
hint N      a nudge, one step at a time
try NAME    run an experiment: fanout, outbox, backoff or digest
"""

import argparse
import importlib
import sys

from notify.checks import CHECKS
from notify.experiments import EXPERIMENTS

CASES = {
    1: ("case01_outbox", "The invitation to a team that never happened"),
    2: ("case02_idempotency", "One payment, four receipts"),
    3: ("case03_permanent", "The device that no longer exists"),
    4: ("case04_jitter", "The retry storm"),
    5: ("case05_ordering", "Live, then building"),
    6: ("case06_preferences", "The newsletter after the unsubscribe"),
    7: ("case07_quiet_hours", "The 3 a.m. buzz"),
    8: ("case08_digest", "The digest that never went out"),
    9: ("case09_priority", "The sign-in code that came too late"),
    10: ("case10_webhooks", "The delivery receipt from yesterday"),
}

HINTS = {
    1: [
        "Which line talks to the outside world while the transaction is still open?",
        "A rollback undoes rows. It cannot unsend an email.",
        "Write the email as an outbox row in the same transaction. relay() sends it after commit.",
    ],
    2: [
        "Print the keys the worker sends. How many different keys does one event get?",
        "The provider can only spot a repeat if the repeat carries the same key.",
        "Derive the key from the event: f'{event.id}:receipt', once, before the retry loop.",
    ],
    3: [
        "Print each status the push service returns, and what classify() does with it.",
        "429 and 503 may pass. 400 and 410 never will, however long you wait.",
        "Return 'gone' for 410, 'reject' for other 4xx, and 'retry' only for 429 and 5xx.",
    ],
    4: [
        "Print when each client retries. How many come back at exactly the same moment?",
        "Exponential backoff spreads retries over time only if clients do not share a schedule.",
        "Full jitter: wait rng.uniform(0, min(CAP, BASE * 2 ** (attempt - 1))).",
    ],
    5: [
        "Compare the order events arrive in with their seq numbers.",
        "Arrival order is the queue's. Clocks on different machines disagree. seq is the truth.",
        "Remember the newest seq per deployment and drop anything at or below it.",
    ],
    6: [
        "When does the service ask for the user's preferences, and when does it send?",
        "Preferences can change between queueing and sending. The send is what matters.",
        "Queue everything and call prefs.allows() in tick(), just before sending.",
    ],
    7: [
        "Print now.time() for u_3002 at 03:00 UTC. What time is it in Mumbai?",
        "Quiet hours are on the user's wall clock, not the server's.",
        "Convert first: now.astimezone(user.zone).time().",
    ],
    8: [
        "Print digest.due each time an update arrives for the busy user.",
        "min(now + QUIET, now + MAX_WAIT) moves with every update. The cap must not move.",
        "Count the cap from the first update: min(now + QUIET, digest.started + MAX_WAIT).",
    ],
    9: [
        "How many messages are ahead of the code when it joins the queue?",
        "One queue means one order: first in, first out, whoever is waiting.",
        "Give codes their own lane and always serve it first. Bulk keeps its own order.",
    ],
    10: [
        "The signature is valid. What else would tell you the request is old, or a repeat?",
        "The timestamp is signed, so it cannot be changed. The webhook id names one delivery.",
        "Refuse timestamps more than TOLERANCE from now, and act on each webhook-id only once.",
    ],
}


def module(number: int):
    name = f"cases.{CASES[number][0]}"
    importlib.invalidate_caches()
    return importlib.reload(importlib.import_module(name))


def fixed(number: int) -> bool:
    return all(ok for _, ok in CHECKS[number](module(number)))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    parser = argparse.ArgumentParser(prog="notify", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    for name in ("run", "check", "hint"):
        sub.add_parser(name).add_argument("n", type=int, choices=CASES, metavar="N")
    sub.add_parser("try").add_argument("name", choices=sorted(EXPERIMENTS))
    args = parser.parse_args()

    if args.command == "list":
        for number, (_, title) in CASES.items():
            print(f"  {number:2d}  {title:<46} {'fixed' if fixed(number) else ''}")
    elif args.command == "run":
        print(f"case {args.n:02d}: {CASES[args.n][1]}\n")
        module(args.n).run()
    elif args.command == "check":
        results = CHECKS[args.n](module(args.n))
        for label, ok in results:
            print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        print()
        if all(ok for _, ok in results):
            print(f"case {args.n} fixed.")
        else:
            print(f"not yet. Try: uv run python -m notify hint {args.n}")
            raise SystemExit(1)
    elif args.command == "hint":
        for step, hint in enumerate(HINTS[args.n], 1):
            print(f"  {step}. {hint}")
    else:
        EXPERIMENTS[args.name]()


if __name__ == "__main__":
    main()
