"""Case 10: the delivery receipt from yesterday.

The SMS provider reports what happened to each message by calling a webhook, signed the way the
Standard Webhooks spec describes: an HMAC-SHA256 of the message id, the timestamp and the raw
body. When a message fails, the service sends it again. The signature check is correct, and it
is not enough. A signed request stays signed forever, so anyone who captures one can send it
again, as often as they like.
Run it: uv run python -m notify run 10
"""

import base64
import hashlib
import hmac
import json
from collections.abc import Callable

SECRET = b"whsec-lab-only-not-a-real-secret"  # shared with the provider; real ones live in a vault
TOLERANCE = 300  # seconds: how far a webhook's timestamp may be from our clock


def sign(webhook_id: str, timestamp: int, body: bytes, secret: bytes = SECRET) -> str:
    signed = f"{webhook_id}.{timestamp}.".encode() + body
    return "v1," + base64.b64encode(hmac.new(secret, signed, hashlib.sha256).digest()).decode()


def receipt(webhook_id: str, message: str, status: str, timestamp: int) -> tuple[dict, bytes]:
    """A webhook exactly as the provider sends it: headers and the raw body."""
    body = json.dumps({"type": f"message.{status}", "message": message}).encode()
    headers = {
        "webhook-id": webhook_id,
        "webhook-timestamp": str(timestamp),
        "webhook-signature": sign(webhook_id, timestamp, body),
    }
    return headers, body


class Receiver:
    def __init__(self, now: Callable[[], int]) -> None:
        self.now = now
        self.status: dict[str, str] = {}
        self.resent: list[str] = []  # each failed message is sent again, and each one costs money
        self.seen: set[str] = set()  # webhook ids already handled; keep them longer than TOLERANCE

    def verify(self, headers: dict, body: bytes) -> bool:
        try:
            webhook_id = headers["webhook-id"]
            timestamp = int(headers["webhook-timestamp"])
            signature = headers["webhook-signature"]
        except (KeyError, ValueError):
            return False
        if abs(self.now() - timestamp) > TOLERANCE:  # too old or from the future: a replay
            return False
        return hmac.compare_digest(sign(webhook_id, timestamp, body), signature)

    def handle(self, headers: dict, body: bytes) -> int:
        if not self.verify(headers, body):
            return 401
        if headers["webhook-id"] in self.seen:  # a retry or a replay: acknowledge, do nothing
            return 200
        self.seen.add(headers["webhook-id"])
        event = json.loads(body)
        status = event["type"].removeprefix("message.")
        self.status[event["message"]] = status
        if status == "failed":
            self.resent.append(event["message"])
        return 200


YESTERDAY = 1_794_000_000  # a Tuesday afternoon, in Unix seconds
TODAY = YESTERDAY + 86_400


def replayed() -> tuple[Receiver, list[int]]:
    """Yesterday a real receipt said msg_17 failed. Someone kept a copy of the request. Today
    they send it again two hundred times."""
    clock = {"now": YESTERDAY}
    receiver = Receiver(lambda: clock["now"])
    captured = receipt("wh_9001", "msg_17", "failed", YESTERDAY)
    answers = [receiver.handle(*captured)]
    receiver.handle(*receipt("wh_9002", "msg_17", "delivered", YESTERDAY + 40))
    clock["now"] = TODAY
    answers += [receiver.handle(*captured) for _ in range(200)]
    return receiver, answers


def run() -> None:
    receiver, answers = replayed()
    print("yesterday: a real receipt says msg_17 failed, so it was sent again")
    print("           40 s later a real receipt says it was delivered")
    print("today:     a copy of the first receipt arrives 200 times, signature intact")
    print()
    print(f"replays accepted:         {answers[1:].count(200)} of 200")
    print(f"times msg_17 was resent:  {len(receiver.resent)} (once was right)")
    print(f"msg_17 is now marked:     {receiver.status['msg_17']} (it was delivered)")
