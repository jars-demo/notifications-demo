"""Case 02: delivered, delivered, delivered.

When a parcel is delivered, a worker texts the customer. The SMS gateway is slow, so the worker
gives up waiting after a few seconds and tries again. But a timeout does not mean the text was
not sent. It means you do not know. The worker sends an idempotency key so the gateway can spot
a repeat, but it makes a new key for every attempt, so the gateway never can.
Run it: uv run python -m dove run 2
"""

from dataclasses import dataclass


class Timeout(Exception):
    """No answer in time. The gateway may or may not have sent the text."""


class Refused(Exception):
    """The gateway refused the connection. Nothing was sent."""


@dataclass(frozen=True)
class Event:
    id: str
    parcel: str
    customer: str
    phone: str


class Gateway:
    """A fake SMS gateway. It remembers every idempotency key for a day, and answers a repeat
    with the earlier result instead of sending again. `faults` scripts what goes wrong for each
    phone, one entry per call: "timeout" means it sent the text and the answer was lost."""

    def __init__(self, faults: dict[str, list[str]]) -> None:
        self.faults = {phone: list(script) for phone, script in faults.items()}
        self.keys: dict[str, str] = {}
        self.texts: list[tuple[str, str]] = []
        self.calls = 0

    def send(self, phone: str, body: str, key: str) -> str:
        self.calls += 1
        fault = self.faults.get(phone, []).pop(0) if self.faults.get(phone) else "ok"
        if fault == "refused":
            raise Refused(phone)
        if key not in self.keys:
            self.texts.append((phone, body))
            self.keys[key] = f"msg-{len(self.texts)}"
        if fault == "timeout":
            raise Timeout(phone)
        return self.keys[key]


class Worker:
    ATTEMPTS = 5

    def __init__(self, gateway: Gateway) -> None:
        self.gateway = gateway

    def handle(self, event: Event) -> str:
        body = f"Hi {event.customer}, your parcel has been delivered to your safe place."
        # One key per event, the same on every attempt and every redelivery.
        key = f"delivered:{event.id}"
        for attempt in range(1, self.ATTEMPTS + 1):
            try:
                return self.gateway.send(event.phone, body, key)
            except (Timeout, Refused):
                if attempt == self.ATTEMPTS:
                    raise
        raise AssertionError("unreachable")


AMARA, BEN, CHEN = "+44 7700 900101", "+44 7700 900102", "+44 7700 900104"
EVENTS = [
    Event("ev-501", "DC-2001", "Amara", AMARA),
    Event("ev-502", "DC-2002", "Ben", BEN),
    Event("ev-503", "DC-2003", "Chen", CHEN),
    Event("ev-504", "DC-2004", "Chen", CHEN),  # Chen ordered twice: two parcels, two texts
]
FAULTS = {
    AMARA: ["timeout", "timeout"],  # sent, but the answer was lost, twice
    BEN: ["refused"],  # the first attempt never reached the gateway
}


def afternoon() -> tuple[Gateway, Worker]:
    """Four deliveries. Then the queue hands ev-501 over a second time, because the worker that
    first took it was restarted before it could say it was done. Queues do that."""
    gateway = Gateway(FAULTS)
    worker = Worker(gateway)
    for event in [*EVENTS, EVENTS[0]]:
        worker.handle(event)
    return gateway, worker


def texts_to(gateway: Gateway, phone: str) -> int:
    return sum(1 for to, _ in gateway.texts if to == phone)


def run() -> None:
    gateway, _ = afternoon()
    print(f"deliveries: {len(EVENTS)}, events handled: {len(EVENTS) + 1} (ev-501 came twice)")
    print(f"gateway calls: {gateway.calls}")
    print(f"texts sent:    {len(gateway.texts)} (four would be right)")
    print()
    for name, phone, right in [("Amara", AMARA, 1), ("Ben", BEN, 1), ("Chen", CHEN, 2)]:
        got = texts_to(gateway, phone)
        print(f"  {name:<6} got {got} text{'s' if got != 1 else ' '}  (should get {right})")
