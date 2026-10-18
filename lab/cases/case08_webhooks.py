"""Case 08: the receipt that came back from yesterday.

The SMS gateway tells Dovecote what happened to each text by calling a webhook. Every call is
signed: an HMAC of the timestamp and the body. When a text fails, Dovecote sends it again. The
signature check is correct, and it is not enough. A signed request stays signed forever, so
anyone who captures one can send it again, as often as they like.
Run it: uv run python -m dove run 8
"""

import hashlib
import hmac
import json
from collections.abc import Callable

SECRET = b"whsec_dovecote_demo_only"  # shared with the gateway; real ones live in a vault
TOLERANCE = 300  # seconds: how far a webhook's timestamp may be from our clock


def sign(timestamp: int, body: bytes, secret: bytes = SECRET) -> str:
    return hmac.new(secret, f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()


def receipt(receipt_id: str, message: str, status: str, timestamp: int) -> tuple[dict, bytes]:
    """A webhook exactly as the gateway sends it: headers and the raw body."""
    body = json.dumps({"id": receipt_id, "message": message, "status": status}).encode()
    headers = {"Dove-Timestamp": str(timestamp), "Dove-Signature": sign(timestamp, body)}
    return headers, body


class Receiver:
    def __init__(self, now: Callable[[], int]) -> None:
        self.now = now
        self.status: dict[str, str] = {}
        self.resent: list[str] = []  # each failed text is sent again, and each one costs money

    def verify(self, headers: dict, body: bytes) -> bool:
        try:
            timestamp = int(headers["Dove-Timestamp"])
            signature = headers["Dove-Signature"]
        except (KeyError, ValueError):
            return False
        return hmac.compare_digest(sign(timestamp, body), signature)

    def handle(self, headers: dict, body: bytes) -> int:
        if not self.verify(headers, body):
            return 401
        event = json.loads(body)
        self.status[event["message"]] = event["status"]
        if event["status"] == "failed":
            self.resent.append(event["message"])
        return 200


YESTERDAY = 1_794_000_000  # a Tuesday afternoon, in Unix seconds
TODAY = YESTERDAY + 86_400


def replayed() -> tuple[Receiver, list[int]]:
    """Yesterday a real receipt said Amara's text failed. Someone kept a copy of the request.
    Today they send it back two hundred times."""
    clock = {"now": YESTERDAY}
    receiver = Receiver(lambda: clock["now"])
    captured = receipt("rc-9001", "msg-17", "failed", YESTERDAY)
    answers = [receiver.handle(*captured)]
    receiver.handle(*receipt("rc-9002", "msg-17", "delivered", YESTERDAY + 40))
    clock["now"] = TODAY
    answers += [receiver.handle(*captured) for _ in range(200)]
    return receiver, answers


def run() -> None:
    receiver, answers = replayed()
    print("yesterday: a real receipt says msg-17 to Amara failed, so it was sent again")
    print("           40 s later a real receipt says it was delivered")
    print("today:     a copy of the first receipt arrives 200 times, signature intact")
    print()
    print(f"replays accepted:          {answers[1:].count(200)} of 200")
    print(f"texts sent to Amara again: {len(receiver.resent)} (one was right)")
    print(f"msg-17 is now marked:      {receiver.status['msg-17']} (it was delivered)")
