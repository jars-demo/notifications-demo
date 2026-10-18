# Once, even when you retry

> Exactly once delivery does not exist between two machines. What you can build is at least once delivery plus a receiver that recognises a repeat. The key that makes a repeat recognisable has to come from the event, not from the attempt.

**Time:** 20 minutes

## Goal

By the end of this chapter you can explain why a timeout is not a failure, choose an idempotency key that survives retries and redeliveries, and say where duplicates come from in a real pipeline.

## A timeout means "I do not know"

The worker asks the SMS gateway to send a text and waits. Three things can happen:

1. **Success.** The gateway answers "sent". You are done.
2. **Refused.** The connection fails before the request leaves. Nothing was sent. Retry.
3. **Timeout.** You sent the request and heard nothing back. The text may have gone. The answer may be on its way. The gateway may be down.

Case 3 is the hard one, and it is common. Gateways are slow under load, and a worker that waits forever is a worker that stops working. So you set a timeout and retry. If the first try did send, the customer gets the text twice.

You cannot tell which case you are in, so you cannot fix this on the sending side alone. The two ends have to agree on how to spot a repeat.

## Where duplicates come from

Retries after a timeout are only one source. In a real pipeline there are at least three:

| Source                  | What happens                                                                    |
| ----------------------- | ------------------------------------------------------------------------------- |
| client retry            | the worker times out and sends the same request again                           |
| queue redelivery        | the worker finishes, then dies before it acknowledges, so the queue hands the event to another worker |
| relay retry (chapter 01) | the outbox relay sends, then crashes before marking the row sent                |

Most queues promise **at least once** delivery for this reason. They would rather give you an event twice than lose it. Your handlers have to be safe to run twice.

## Idempotency keys

An operation is **idempotent** if doing it twice has the same effect as doing it once. Sending a text is not. But you can make the request idempotent: attach a key, and have the gateway remember the keys it has seen. A second request with the same key gets the first answer back, and no second text. Most real SMS, push and payment APIs support this, often as an `Idempotency-Key` header.

The key is only useful if every attempt to deliver the *same notification* carries the *same key*, and different notifications carry different keys. That rules out a lot of tempting choices.

## The case

Open `lab/cases/case02_idempotency.py`. Four parcels are delivered this afternoon. The fake gateway in the case is scripted: Amara's first two requests time out *after* the text was sent, and Ben's first request is refused. Then the queue hands Amara's event over a second time, because the worker that took it was restarted before it said it was done.

```bash
uv run python -m dove run 2
```

```text
deliveries: 4, events handled: 5 (ev-501 came twice)
gateway calls: 8
texts sent:    7 (four would be right)

  Amara  got 4 texts  (should get 1)
  Ben    got 1 text   (should get 1)
  Chen   got 2 texts  (should get 2)
```

The worker does send an idempotency key. Look at where it is made.

## Reasoning towards the fix

The key is made inside the retry loop, with `uuid.uuid4()`, so every attempt has a new one. To the gateway, attempt two is a brand new text.

Moving the `uuid4()` call above the loop is the fix most people reach for first. It stops the retries from doubling up. Count what it does to Amara: one text from the three attempts, then one more when the queue redelivers the event, because the redelivery runs `handle` again and makes a new random key. Two texts.

A key on the phone number and the message text fails the other way. Chen ordered twice, and the template says the same thing for both parcels. Two real deliveries, one text.

The key has to identify the *thing you are telling someone about*, so it must come from the event itself, which is the same on every retry and every redelivery. Build it once, before the loop, from the event's id. Prefix it with what kind of message it is, so the same event can still trigger a different notification later.

```bash
uv run python -m dove check 2
```

```text
  FAIL  Amara gets one text, despite two timeouts and a redelivery (got 4)
  PASS  Ben gets his text, though the first try was refused (got 1)
  PASS  Chen gets two texts for two parcels, though they read the same (got 2)
```

Turning retries off is no escape: Ben's refused first try must still end in a text.

## Check it works

```text
  PASS  Amara gets one text, despite two timeouts and a redelivery (got 1)
  PASS  Ben gets his text, though the first try was refused (got 1)
  PASS  Chen gets two texts for two parcels, though they read the same (got 2)
```

## Trade-offs and when the usual advice is wrong

- **The gateway's memory is finite.** Providers keep keys for a window, often 24 hours. A redelivery after that window is a new request. Keep your own record too: a table of `(key, sent_at)` checked before sending turns "at least once" into "effectively once" on your side.
- **Check then send is a race.** Two workers can both check, both see nothing, and both send. Insert the key with a unique constraint first, and only the worker whose insert succeeds sends.
- **Not every channel supports keys.** Plain SMTP has none. There you dedupe on your side, and accept that a crash at the wrong moment can still double send. Pick which mistake you prefer. For a login code, a duplicate is harmless. For "your card was charged", it is alarming.
- **"Exactly once" in a product's docs** almost always means "at least once, with deduplication inside our system". The edges, your code and your customer's phone, are still yours.

## Exercise

1. Add a `keys_sent` set to the worker and skip events whose key it has already seen. What does that protect against that the gateway does not? What does a restart do to it?
2. Change the gateway to forget keys after a pretend hour. Write a run where the redelivery comes after that hour. What do you see?
