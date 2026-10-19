"""Case 09: the sign-in code that came too late.

Every SMS leaves through one sender, which the provider allows fifty messages a second. At 09:00
a product announcement is queued for six thousand users. Five seconds later u_5001 tries to
sign in and asks for a code. It is valid for sixty seconds. It joins the back of the queue.
Run it: uv run python -m notify run 9
"""

from collections import deque
from dataclasses import dataclass

RATE = 50  # messages a second, the most the provider allows us
CODE_VALID = 60  # seconds a sign-in code works for


@dataclass(frozen=True)
class Message:
    to: str
    body: str
    kind: str  # "code" for sign-in codes and anything a person is waiting for, "bulk" otherwise
    made: float  # seconds after 09:00


class Queue:
    """Messages waiting for the sender."""

    def __init__(self) -> None:
        self.items: deque[Message] = deque()

    def put(self, message: Message) -> None:
        self.items.append(message)

    def get(self) -> Message:
        return self.items.popleft()

    def __len__(self) -> int:
        return len(self.items)


def arrivals() -> list[Message]:
    bulk = [
        Message(f"u_{n:05d}", f"Release 4.2 is out, user {n}", "bulk", 0.0) for n in range(1, 6001)
    ]
    codes = [
        Message("u_5001", "Your sign-in code is 481 223", "code", 5.0),
        Message("u_5002", "Your sign-in code is 905 117", "code", 20.0),
    ]
    return bulk + codes


def morning() -> list[tuple[float, Message]]:
    """Run the sender, one message every 1/RATE seconds, until the queue is empty."""
    queue = Queue()
    todo = deque(sorted(arrivals(), key=lambda message: message.made))
    sent: list[tuple[float, Message]] = []
    tick = 0
    while todo or len(queue):
        now = tick / RATE
        while todo and todo[0].made <= now:
            queue.put(todo.popleft())
        if len(queue):
            sent.append((now, queue.get()))
        tick += 1
    return sent


def clock(seconds: float) -> str:
    return f"09:{int(seconds) // 60:02d}:{int(seconds) % 60:02d}"


def run() -> None:
    sent = morning()
    bulk = sum(1 for _, message in sent if message.kind == "bulk")
    print(f"09:00:00  {bulk} announcements queued, sent at {RATE} a second")
    for when, message in sent:
        if message.kind == "code":
            waited = when - message.made
            verdict = "expired before it arrived" if waited > CODE_VALID else "in time"
            print(
                f"{clock(message.made)}  {message.to} asks for a sign-in code. "
                f"It arrives {waited:.1f} s later: {verdict}"
            )
    print(f"last message sent at {clock(sent[-1][0])}")
