# Priority lanes

> A sign-in code that waits behind six thousand announcements is useless by the time it arrives. Messages that a person is waiting for need their own lane.

**Time:** 20 minutes

## Goal

By the end of this chapter you can explain head-of-line blocking, split traffic into lanes by urgency, and keep bulk traffic flowing without letting it delay transactional messages.

## The idea

### Rate limits make queues

Every provider limits how fast you may send: messages per second for SMS numbers, requests per second for push and email APIs, sends per day for new email domains. When you produce faster than the limit, messages queue. That is fine for an announcement. It is not fine for a two-factor code that expires in 60 seconds.

### Head-of-line blocking

In a single first-in, first-out queue, a message waits for everything ahead of it. One big batch at the front delays everything behind it, however urgent. The fix is not a faster sender. It is a separate path.

### Lanes

Classify every message when it is created:

| Lane | Examples | Promise |
| --- | --- | --- |
| transactional, someone is waiting | sign-in codes, password resets | seconds |
| transactional | receipts, alerts, mentions | minutes |
| bulk | announcements, newsletters, digests | hours |

Serve the urgent lane first, and give bulk whatever capacity is left. Strict priority is right when urgent traffic is small, as it almost always is. If it could ever fill the whole rate, reserve a share for bulk so it cannot starve.

## The case

Open `lab/cases/case09_priority.py`. Every SMS leaves through one sender that the provider allows 50 messages a second. At 09:00 an announcement is queued for 6,000 users. Five seconds later u_5001 asks for a sign-in code, valid for 60 seconds.

```bash
uv run python -m notify run 9
```

```text
09:00:00  6000 announcements queued, sent at 50 a second
09:00:05  u_5001 asks for a sign-in code. It arrives 115.0 s later: expired before it arrived
09:00:20  u_5002 asks for a sign-in code. It arrives 100.0 s later: expired before it arrived
last message sent at 09:02:00
```

Both users could not sign in. The sender was never idle and never broke the rate limit. It just did things in the wrong order.

## Reasoning towards the fix

The rate limit is not the problem: 6,000 messages at 50 a second take two minutes whatever you do. The order is. Give the queue two lanes, put codes in the first, and always serve it before bulk. Bulk keeps its own order inside its lane.

## Check your fix

```bash
uv run python -m notify check 9
```

As shipped:

```text
  FAIL  each sign-in code arrives within 5 seconds (u_5001 115.0 s, u_5002 100.0 s)
  PASS  codes go out in the order they were asked for
  PASS  all 6000 announcements still go out, in order (6000 sent)
  PASS  the sender keeps to 50 messages a second
```

Raising the rate to send everything faster also gets the codes through in time, and breaks the provider's limit, which in real life means 429s, then blocks.

## In production

- **Separate infrastructure.** Large senders use different queues, workers and even different provider accounts, numbers or IP pools for transactional and bulk traffic, so a bulk problem cannot touch codes.
- **Expiry.** A code that is already expired should not be sent at all. Give urgent messages a deadline and drop them after it.
- **Email reputation.** Bulk email that gets spam complaints hurts the domain's reputation. Sending transactional email from a separate subdomain protects it.
- **Fallback channels.** If SMS is slow, offer the code by voice call, email or an authenticator app.

## Key points

- Provider rate limits turn bursts into queues.
- In one FIFO queue, urgent messages wait behind everything ahead of them.
- Classify messages by urgency when they are created, and serve urgent lanes first.
- Keep bulk flowing in its own lane, and never break the provider's limit.
