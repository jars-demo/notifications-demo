"""dove: eight notification bugs in one small parcel company.

list        every case, and which ones are fixed
run N       run case N and watch the bug happen
check N     check your fix: the message arrives, once, on time
hint N      a nudge from Pip
try NAME    run an experiment: fanout, outbox, backoff or digest
"""

import argparse
import importlib
import sys

from dove.checks import CHECKS
from dove.experiments import EXPERIMENTS

CASES = {
    1: ("case01_outbox", "The text for a parcel that never left"),
    2: ("case02_idempotency", "Delivered, delivered, delivered"),
    3: ("case03_ordering", "Delivered, then out for delivery"),
    4: ("case04_permanent", "The phone that no longer exists"),
    5: ("case05_quiet_hours", "The 3 a.m. buzz"),
    6: ("case06_digest", "Silence at the busy shop"),
    7: ("case07_priority", "The login code that came too late"),
    8: ("case08_webhooks", "The receipt that came back from yesterday"),
}

HINTS = {
    1: [
        "When does the text leave? When does the transaction decide whether it happened?",
        "Sending after the commit is not enough: the process can die in between.",
        "Write the text into the outbox table inside the transaction. The relay sends it.",
    ],
    2: [
        "A timeout does not mean the text was not sent. It means you do not know.",
        "The gateway can spot a repeat, but only if the repeat carries the same key.",
        "Make the key from the event, once, before the loop: f'delivered:{event.id}'.",
    ],
    3: [
        "Events do not arrive in the order they happened. What tells you the real order?",
        "Timestamps come from clocks, and the van's clock is four minutes slow.",
        "Remember the highest seq shown for each parcel. Ignore anything at or below it.",
    ],
    4: [
        "Read the push service's docstring. Which answers can change if you wait?",
        "429 and 503 mean later. 410 means never for that token, 400 never for that message.",
        "classify() already has words for gone and reject. Teach it which codes they are.",
    ],
    5: [
        "Print now.time() and the customer's zone for Ravi's 21:35 push.",
        "Quiet hours belong to the person, not the server.",
        "Turn the time into theirs before comparing it: now.astimezone(customer.zone).",
    ],
    6: [
        "Watch digest.due for Kiln & Co. When does it move?",
        "Every update pushes the deadline ten minutes further away. The cap moves with it.",
        "The thirty minutes count from the first update in the digest: digest.started.",
    ],
    7: [
        "Who is waiting for each text? A person at a login screen, or nobody in particular?",
        "One queue, first in first out, means a code waits behind every offer queued before it.",
        "Give codes their own lane and always empty it first. Keep each lane in order.",
    ],
    8: [
        "The signature proves who made the request. Does it prove when?",
        "The timestamp is signed, so you can trust it. Do you look at it?",
        "Refuse anything more than TOLERANCE seconds from now, and remember receipt ids you saw.",
    ],
}


def say(text: str) -> None:
    print("     __")
    print(f"   >(o )__   {text}")
    print("     (___/", flush=True)


def module(number: int):
    name = f"cases.{CASES[number][0]}"
    sys.modules.pop(name, None)  # always the code as it is on disk now
    return importlib.import_module(name)


def fixed(number: int) -> bool:
    return all(ok for _, ok in CHECKS[number](module(number)))


def cmd_list(args: argparse.Namespace) -> None:
    for number, (_, title) in CASES.items():
        print(f"  {number}  {title:<44} {'fixed' if fixed(number) else ''}", flush=True)


def cmd_run(args: argparse.Namespace) -> None:
    say(f"Case {args.n}: {CASES[args.n][1]}.")
    print()
    module(args.n).run()


def cmd_check(args: argparse.Namespace) -> None:
    results = CHECKS[args.n](module(args.n))
    for label, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
    print()
    if all(ok for _, ok in results):
        say(f"Case {args.n} fixed. Delivered.")
    else:
        say(f"Not yet. Try: uv run python -m dove hint {args.n}")
        sys.exit(1)


def cmd_hint(args: argparse.Namespace) -> None:
    say("Here is what I would look at:")
    for hint in HINTS[args.n]:
        print(f"  - {hint}")


def cmd_try(args: argparse.Namespace) -> None:
    EXPERIMENTS[args.name]()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # the same output on every terminal
    parser = argparse.ArgumentParser(prog="dove", description="Eight notification bugs.")
    sub = parser.add_subparsers(required=True)
    sub.add_parser("list", help="every case and which are fixed").set_defaults(func=cmd_list)
    for name, func, text in [
        ("run", cmd_run, "run case N and watch the bug"),
        ("check", cmd_check, "check your fix"),
        ("hint", cmd_hint, "a nudge from Pip"),
    ]:
        p = sub.add_parser(name, help=text)
        p.add_argument("n", type=int, choices=CASES, metavar="N")
        p.set_defaults(func=func)
    p = sub.add_parser("try", help="run an experiment: " + ", ".join(EXPERIMENTS))
    p.add_argument("name", choices=EXPERIMENTS)
    p.set_defaults(func=cmd_try)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
