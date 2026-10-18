"""Case 07: the login code that came too late.

Every text leaves through one sender, which the SMS gateway allows fifty messages a second. At
nine marketing queues the autumn offer for six thousand customers. Five seconds later Amara tries
to sign in and asks for a code. It is valid for sixty seconds. It joins the back of the queue.
Run it: uv run python -m dove run 7
"""

from collections import deque
from dataclasses import dataclass

RATE = 50  # texts a second, the most the gateway allows us
CODE_VALID = 60  # seconds a login code works for


@dataclass(frozen=True)
class Text:
    to: str
    body: str
    kind: str  # "code" for login codes and other things a person is waiting for, "bulk" otherwise
    made: float  # seconds after 09:00


class Queue:
    """Texts waiting for the sender."""

    def __init__(self) -> None:
        self.items: deque[Text] = deque()

    def put(self, text: Text) -> None:
        self.items.append(text)

    def get(self) -> Text:
        return self.items.popleft()

    def __len__(self) -> int:
        return len(self.items)


def arrivals() -> list[Text]:
    offers = [
        Text(f"customer-{n:04d}", f"Autumn offer {n}: free next-day delivery", "bulk", 0.0)
        for n in range(1, 6001)
    ]
    codes = [
        Text("Amara", "Your Dovecote code is 481 223", "code", 5.0),
        Text("Ben", "Your Dovecote code is 905 117", "code", 20.0),
    ]
    return offers + codes


def morning() -> list[tuple[float, Text]]:
    """Run the sender, one text every 1/RATE seconds, until the queue is empty."""
    queue = Queue()
    todo = deque(sorted(arrivals(), key=lambda text: text.made))
    sent: list[tuple[float, Text]] = []
    tick = 0
    while todo or len(queue):
        now = tick / RATE
        while todo and todo[0].made <= now:
            queue.put(todo.popleft())
        if len(queue):
            sent.append((now, queue.get()))
        tick += 1
    return sent


def run() -> None:
    sent = morning()
    bulk = sum(1 for _, text in sent if text.kind == "bulk")
    print(f"09:00:00  {bulk} autumn offers queued, sent at {RATE} a second")
    for when, text in sent:
        if text.kind == "code":
            waited = when - text.made
            verdict = "expired before it arrived" if waited > CODE_VALID else "in time"
            print(
                f"09:{int(text.made) // 60:02d}:{int(text.made) % 60:02d}  {text.to} asks for a"
                f" login code. It arrives {waited:.1f} s later: {verdict}"
            )
    print(f"last text sent at 09:{int(sent[-1][0]) // 60:02d}:{int(sent[-1][0]) % 60:02d}")
