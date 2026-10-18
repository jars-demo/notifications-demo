# Webhooks you can trust

> A signature proves who made a request. It says nothing about when, or how many times. Check the signature, then check the timestamp, then check that you have not acted on this one before.

**Time:** 25 minutes

## Goal

By the end of this chapter you can verify a signed webhook properly, explain a replay attack, pick a sensible tolerance window, and make a webhook handler safe to call twice. You finish with a checklist for every notification system you build.

## The last step: learning what happened

Step 5 from chapter 01 is learning what happened to a message. Providers tell you by calling **webhooks**: they make an HTTP request to a URL you gave them, with a small JSON body like `{"id": "rc-9001", "message": "msg-17", "status": "failed"}`. You use these receipts to mark messages delivered, to retry on another channel, to stop sending to a dead number.

A webhook URL is public. Anyone who finds it can post to it. So providers sign each request. A common scheme, and the one the case uses:

1. The provider and you share a secret.
2. For each request, the provider takes the current time and the raw body, and computes `HMAC-SHA256(secret, timestamp + "." + body)`.
3. It sends the timestamp and the signature in headers.
4. You compute the same HMAC and compare.

Only someone with the secret can make a valid signature, so a forged receipt fails. Change one byte of the body and the signature fails. That is all a signature can do.

## Replay

Suppose someone captures one genuine request. Perhaps it sat in a log file, a proxy's debug output, or a teammate's terminal history. They cannot change it. They can send it again. And again. Every copy carries a valid signature, because it is the provider's own request.

What happens next depends on what your handler does with a receipt. Dovecote resends a text when a receipt says it failed. A replayed "failed" receipt makes Dovecote send a text, at Dovecote's expense, every time. Fraudsters run exactly this kind of loop against SMS endpoints on purpose. It is called SMS pumping, and it is paid for by whoever sends the texts.

That is why the timestamp is inside the signature. It cannot be changed without breaking the signature, so you can trust it, and refuse anything too old.

## The case

Open `lab/cases/case08_webhooks.py`. Yesterday a genuine receipt said Amara's text `msg-17` had failed, so Dovecote sent it again. Forty seconds later a second genuine receipt said it was delivered. Someone kept a copy of the first request. Today they send it two hundred times.

```bash
uv run python -m dove run 8
```

```text
yesterday: a real receipt says msg-17 to Amara failed, so it was sent again
           40 s later a real receipt says it was delivered
today:     a copy of the first receipt arrives 200 times, signature intact

replays accepted:          200 of 200
texts sent to Amara again: 201 (one was right)
msg-17 is now marked:      failed (it was delivered)
```

Amara got two hundred extra texts, Dovecote paid for each one, and the record now says a delivered message failed.

## Reasoning towards the fix

`verify` does the hard parts well. It signs the timestamp and the raw bytes of the body, not a parsed and re-encoded copy, which would change spacing and break genuine signatures. It compares with `hmac.compare_digest`, which takes the same time whether the first byte or the last one differs, so an attacker cannot learn the signature a byte at a time. It reads the timestamp, and then never looks at it again.

Two separate questions are left.

**Is this request recent?** Compare the signed timestamp with your own clock. Refuse it if the gap is more than `TOLERANCE` seconds, in either direction. Five minutes is a common choice: long enough for retries and clock skew, short enough that a captured request goes stale quickly.

**Have I acted on it already?** Inside the window, a replay is still possible, and providers retry genuine webhooks too. Remember the ids of receipts you have handled. For a repeat, answer success and do nothing. You only need to remember ids for as long as the window, because anything older is refused by the first check.

```bash
uv run python -m dove check 8
```

```text
  PASS  genuine receipts are accepted, even out of order
  PASS  a forged or tampered receipt is refused
  FAIL  yesterday's receipt sent again today is refused (200 accepted)
  FAIL  a receipt repeated within a minute is acted on once (sent again 21x)
```

Each half alone fails one line. A window with no memory accepts twenty repeats in a minute. Memory with no window refuses yesterday's receipt only until the process restarts and forgets. "Only accept receipts newer than the last one" sounds clever and refuses genuine receipts that arrive out of order, which chapter 03 says they will.

## Check it works

```text
  PASS  genuine receipts are accepted, even out of order
  PASS  a forged or tampered receipt is refused
  PASS  yesterday's receipt sent again today is refused (0 accepted)
  PASS  a receipt repeated within a minute is acted on once (sent again 1x)
```

## Trade-offs and when the usual advice is wrong

- **Answer fast, work later.** Providers time out webhooks after a few seconds and retry. Verify, store the receipt, return 200, and do the work from your own queue. A slow handler turns into duplicate deliveries.
- **Rotate secrets without downtime.** Accept signatures from both the old and the new secret for a while, then drop the old one.
- **Your clock matters now.** A server whose clock drifts by six minutes refuses every genuine webhook. Run time sync, and alert on rejections by reason.
- **Sign what you send, too.** When you call your customers' webhooks, sign the same way, include a timestamp and an event id, and document both. Your customers will make every mistake in this chapter unless you make the right thing easy.
- **"We check the signature"** is the answer most teams give, and it is the answer that misses replay. Ask the second question.

## Exercise

1. Change the receiver to keep seen ids in the SQLite outbox database from chapter 01, so a restart keeps its memory. What does that buy you, given the window?
2. Set `TOLERANCE` to five seconds and add a receipt that the provider retried after ten. What happens, and what is the right window for your provider?

## The notifications checklist

Ten rules, one for every way a message went wrong in this workshop:

1. Write the notification in the same transaction as the change, and send it from an outbox.
2. Assume every queue delivers twice. Make every handler safe to run again.
3. Make idempotency keys from the event, never from the attempt, and reuse them on every retry.
4. Order by a sequence number from the source of truth, never by arrival or by a device's clock.
5. Sort failures into retry later, never for this message, and never for this device. Delete dead tokens.
6. Back off exponentially, with jitter, and stop after a limit. Count what lands in dead letters.
7. Read quiet hours on the customer's clock. Hold rather than drop, and let urgent messages through.
8. Batch noisy updates, and cap how long any update may wait.
9. Give messages a person is waiting for their own lane, ahead of every campaign.
10. Verify webhook signatures over the raw body, refuse old timestamps, and remember ids you have handled.
