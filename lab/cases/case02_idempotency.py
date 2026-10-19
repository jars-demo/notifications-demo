"""Case 02: one payment, four receipts.

When a payment succeeds, a worker emails the receipt through the provider's HTTP API. When a
request fails, it retries: a lost answer does not mean the email was not sent, it means you do
not know. The worker sends an Idempotency-Key so the provider can spot a repeat, but it makes a
new key for every attempt, so the provider never can. The queue also delivers each event at
least once, so now and then the same event arrives twice.
Run it: uv run python -m notify run 2
"""

import json
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass

from notify.provider import EmailAPI

ATTEMPTS = 5


@dataclass(frozen=True)
class PaymentSucceeded:
    id: str  # the event id: unique per payment, the same on every redelivery
    payment: str
    email: str
    amount: str


class Failed(Exception):
    pass


class Worker:
    def __init__(self, url: str) -> None:
        self.url = url

    def post(self, message: dict, key: str) -> dict:
        request = urllib.request.Request(
            self.url,
            data=json.dumps(message).encode(),
            headers={"Content-Type": "application/json", "Idempotency-Key": key},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.load(response)

    def handle(self, event: PaymentSucceeded) -> str:
        message = {"to": event.email, "subject": f"Receipt for {event.payment}: {event.amount}"}
        for _ in range(ATTEMPTS):
            key = uuid.uuid4().hex
            try:
                return self.post(message, key)["id"]
            except (urllib.error.HTTPError, OSError):
                continue  # a 503, a reset or a lost answer: try again
        raise Failed(event.id)


EVENTS = [
    PaymentSucceeded("evt_501", "pay_7Q1", "ada@example.com", "49.00 USD"),
    PaymentSucceeded("evt_502", "pay_7Q2", "ben@example.com", "12.00 USD"),
    PaymentSucceeded("evt_503", "pay_7Q3", "cy@example.com", "49.00 USD"),
    PaymentSucceeded("evt_504", "pay_7Q4", "cy@example.com", "49.00 USD"),  # a second payment
]
FAULTS = {
    "ada@example.com": ["lost", "lost"],  # sent, and the answer lost, twice
    "ben@example.com": ["unavailable"],  # the first request was turned away, nothing sent
}


def afternoon() -> EmailAPI:
    """Four payments. Then the queue delivers evt_501 a second time, because the worker that took
    it first was restarted before it acknowledged it. At-least-once queues do that."""
    with EmailAPI(FAULTS) as api:
        worker = Worker(api.url)
        for event in [*EVENTS, EVENTS[0]]:
            worker.handle(event)
    return api


def run() -> None:
    api = afternoon()
    print(f"payments: {len(EVENTS)}, events handled: {len(EVENTS) + 1} (evt_501 arrived twice)")
    print(f"HTTP requests to the provider: {api.requests}")
    print(f"receipts sent: {len(api.sent)} (four would be right)")
    print()
    for email, right in [("ada@example.com", 1), ("ben@example.com", 1), ("cy@example.com", 2)]:
        print(f"  {email:<16} got {api.count(email)}  (should get {right})")
