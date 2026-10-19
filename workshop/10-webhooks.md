# Webhooks you can trust

> A valid signature proves who sent a request, not when. A captured request stays valid forever unless you check its timestamp and refuse a webhook id you have already handled.

**Time:** 25 minutes

## Goal

By the end of this chapter you can verify a signed webhook correctly, stop replays with a timestamp window and an id check, and handle provider retries without acting twice. The chapter ends with a production checklist.

## The idea

### Learning what happened

Step five of every notification system is learning what happened to each message. Providers tell you with **webhooks**: they call an HTTPS endpoint of yours with events such as `message.delivered`, `message.failed`, `email.bounced` and `email.complained`. Your system acts on them: it marks messages delivered, retries failures, suppresses dead addresses (chapter 03).

That endpoint is public. Anyone can call it.

### Signatures

The provider and you share a secret. The provider signs each request with an HMAC of its contents, and you recompute it. The Standard Webhooks specification, used by many providers, defines:

```text
webhook-id: wh_9001
webhook-timestamp: 1794000000
webhook-signature: v1,<base64 of HMAC-SHA256(secret, "wh_9001.1794000000.<raw body>")>
```

Three details matter:

- Sign and verify the **raw body bytes**, not a re-serialised JSON object. Re-serialising changes spacing and key order.
- Compare signatures with a constant-time function, such as Python's `hmac.compare_digest`, so the time taken does not leak how many characters matched.
- The id and timestamp are inside the signed text, so they cannot be changed without breaking the signature.

### What a signature does not prove

A signature proves the provider sent this exact request at some point. It does not prove the request is new. Anyone who captures one, from a log, a proxy or a misconfigured debug tool, can send it again, and it will verify. That is a **replay**.

Two checks close it:

1. **Timestamp window.** Refuse requests whose timestamp is more than a few minutes from your clock. Five minutes is common.
2. **Seen ids.** Remember each `webhook-id` you have handled for at least that window, and acknowledge repeats without acting on them. This also makes the provider's own retries harmless.

## The case

Open `lab/cases/case10_webhooks.py`. The SMS provider signs delivery receipts as above. The receiver verifies the signature correctly and, when a message failed, sends it again. Yesterday msg_17 failed and then was delivered. Someone kept a copy of the "failed" receipt.

```bash
uv run python -m notify run 10
```

```text
yesterday: a real receipt says msg_17 failed, so it was sent again
           40 s later a real receipt says it was delivered
today:     a copy of the first receipt arrives 200 times, signature intact

replays accepted:         200 of 200
times msg_17 was resent:  201 (once was right)
msg_17 is now marked:     failed (it was delivered)
```

Every replay passed verification, cost one SMS, and rewrote the message's status to a lie.

## Reasoning towards the fix

The signature check is correct and must stay. Add two things: in `verify()`, refuse a timestamp more than `TOLERANCE` seconds from `self.now()`; in `handle()`, remember each `webhook-id` and answer a repeat with 200 without acting on it. Answer 200, not an error, so the provider stops retrying a delivery it already made.

## Check your fix

```bash
uv run python -m notify check 10
```

As shipped:

```text
  PASS  genuine receipts are accepted, even out of order
  PASS  a forged or tampered receipt is refused
  FAIL  yesterday's receipt sent again today is refused (200 accepted)
  FAIL  a receipt repeated within a minute is acted on once (resent 21x)
```

Checking only the timestamp stops yesterday's replay, and still acts 21 times on a receipt repeated within the window.

## In production

- **Store seen ids durably,** in Redis with a TTL or a table with a unique constraint, shared by every instance of the receiver. A set in one process forgets on restart.
- **Acknowledge fast, process later.** Verify, record the event, answer 2xx, then process from a queue. Providers time out slow endpoints and retry, which multiplies work.
- **Rotate secrets.** Support two secrets during a rotation, and accept a signature from either.
- **Do not trust the order.** Receipts arrive out of order too: apply chapter 05, so "failed" cannot overwrite "delivered".

## Production checklist

Ten questions to ask of any notification system before it ships:

1. Is every notification written in the same transaction as the change it reports? (chapter 01)
2. Does every send carry an idempotency key derived from the event, not the attempt? (chapter 02)
3. Are permanent failures dead-lettered, and dead tokens and bounced addresses removed? (chapter 03)
4. Do retries use exponential backoff with jitter, a cap and a budget? (chapter 04)
5. Are state changes ordered by a sequence number from their source? (chapter 05)
6. Are preferences checked at send time, with a short list of required notices? (chapter 06)
7. Are quiet hours computed on each user's own clock? (chapter 07)
8. Does every batch have a maximum wait counted from its first update? (chapter 08)
9. Do messages someone is waiting for have their own lane? (chapter 09)
10. Are webhooks verified, time-checked and deduplicated by id? (chapter 10)

## Key points

- Webhooks are a public endpoint. Verify an HMAC over the raw body, in constant time.
- A signature proves origin, not freshness.
- Refuse old timestamps and repeated webhook ids, and answer repeats with 200.
- Record first, process later, and apply receipts in order.
