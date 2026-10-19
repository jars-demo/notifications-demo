# Once, even when you retry

> A timeout does not mean the request failed. It means you do not know. Retries are only safe when the receiver can recognise a repeat, and that takes a key that is the same on every attempt.

**Time:** 20 minutes

## Goal

By the end of this chapter you can explain at-least-once delivery, choose a good idempotency key, and make a retrying worker send each notification exactly once.

## The idea

### Three outcomes, not two

When a worker calls a provider over HTTP, it can see:

- **a success:** the provider answered 2xx. It was sent.
- **a refusal:** the provider answered 503, or the connection was refused. It was not sent.
- **nothing:** a timeout, or the connection dropped before the answer. It may have been sent.

The third outcome is the hard one. Retrying risks a duplicate. Not retrying risks a loss. And it is common: every network, load balancer and deploy produces some.

### At-least-once is the normal case

Queues (SQS, Pub/Sub, Kafka consumers, RabbitMQ) and the outbox from chapter 01 all deliver **at least once**. A worker that crashes after doing the work and before acknowledging it gets the same message again. Exactly-once delivery between independent systems is not on offer. What you can build is **exactly-once effect**: deliver as often as needed, and make repeats do nothing.

### Idempotency keys

An operation is idempotent if doing it twice has the same effect as doing it once. Most email, SMS and payment APIs make a send idempotent with a header:

```text
POST /v1/emails
Idempotency-Key: evt_501:receipt
```

The provider stores the key with its first answer, usually for 24 hours. A request with a key it has seen gets that first answer back, and nothing is sent again.

The key must identify **the notification**, not the attempt:

| Key | Problem |
| --- | --- |
| a new random UUID per attempt | every retry looks new, so every retry sends |
| the recipient's address | two different receipts to one person look like one |
| the event id plus the purpose, such as `evt_501:receipt` | correct: the same on every retry and redelivery, and different for different notifications |

## The case

Open `lab/cases/case02_idempotency.py`. When a payment succeeds, a worker emails a receipt through a real HTTP API: `lab/notify/provider.py` runs an email provider on localhost that honours `Idempotency-Key`, and can lose answers or refuse requests on cue. Two answers to ada@example.com are lost after the email was sent, ben@example.com's first request gets a 503, and the queue delivers evt_501 twice.

```bash
uv run python -m notify run 2
```

```text
payments: 4, events handled: 5 (evt_501 arrived twice)
HTTP requests to the provider: 8
receipts sent: 7 (four would be right)

  ada@example.com  got 4  (should get 1)
  ben@example.com  got 1  (should get 1)
  cy@example.com   got 2  (should get 2)
```

One payment, four receipts. The worker did send a key every time. A new one every time.

## Reasoning towards the fix

Follow evt_501: attempt one is sent and its answer lost, attempt two the same, attempt three succeeds, and later the redelivered event sends a fourth. Four keys, four emails. If all of them carried the same key, the provider would send once and answer the rest from memory.

Derive the key from the event, before the retry loop: `f"{event.id}:receipt"`. The purpose suffix matters when one event causes several notifications, such as a receipt and a Slack message.

## Check your fix

```bash
uv run python -m notify check 2
```

As shipped:

```text
  FAIL  one receipt for evt_501, despite two lost answers and a redelivery (got 4)
  PASS  a receipt for evt_502, though the first request was turned away (got 1)
  PASS  two receipts for two payments that read the same (got 2)
```

Using the email address as the key fixes ada and breaks cy: cy made two payments, and must get two receipts.

## In production

- **Not every provider supports keys.** Then keep your own record: insert `(key, status)` into a table with a unique constraint before sending, and skip the send if the insert conflicts. A crash between the insert and the send now loses the message instead of duplicating it, so pick which failure you prefer per notification type.
- **Key lifetime.** Providers forget keys after a day or so. A retry after that is a new send. Keep retry windows shorter than the key lifetime.
- **Consumers too.** Your own webhook and queue consumers need the same treatment: chapter 10 does it for delivery receipts.
- **Retries need limits.** Chapter 03 decides which failures to retry at all, and chapter 04 how to space them.

## Key points

- A timeout or lost answer means "unknown", not "failed".
- Queues and outboxes deliver at least once. Aim for exactly-once effect.
- An idempotency key must be the same on every attempt and different for every notification.
- Derive it from the event and the purpose, never generate it per attempt.
