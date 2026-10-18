# Priority lanes

> Every sender has a rate limit, so every sender has a queue. When a person is waiting for a message and a campaign is not, putting them in one first in, first out queue means the person waits for the campaign.

**Time:** 20 minutes

## Goal

By the end of this chapter you can explain head of line blocking, give transactional messages their own lane, measure what batching does to throughput, and say how strict priority can starve the lower lanes.

## Two kinds of message

Dovecote sends two very different kinds of message through the same pipe:

- **Transactional.** A login code, a password reset, "your driver is outside". One person, waiting now, often with a deadline.
- **Bulk.** The autumn offer, the monthly newsletter, "rate your delivery". Many people, nobody waiting, no deadline worth the name.

Providers know this. Many give transactional and marketing traffic separate rate limits, separate sending addresses and separate reputations, because a spam complaint about the newsletter should not stop password resets.

## Every sender is a queue

The SMS gateway lets Dovecote send fifty texts a second. Anything more has to wait. So in front of every sender sits a queue, whether you built one on purpose or not. A queue has an order, and the order decides who waits.

The classic failure is **head of line blocking**: one big job at the front holds up everything behind it. Six thousand offers at fifty a second is two minutes of sending. A code queued behind them waits two minutes.

## The case

Open `lab/cases/case07_priority.py`. At 09:00 marketing queues the autumn offer for six thousand customers. At 09:00:05 Amara tries to sign in. At 09:00:20 Ben does. Their codes are valid for sixty seconds.

```bash
uv run python -m dove run 7
```

```text
09:00:00  6000 autumn offers queued, sent at 50 a second
09:00:05  Amara asks for a login code. It arrives 115.0 s later: expired before it arrived
09:00:20  Ben asks for a login code. It arrives 100.0 s later: expired before it arrived
last text sent at 09:02:00
```

Nothing is broken in the usual sense. Every text is delivered. The sender never goes over its limit. And two people are locked out of their accounts, probably tapping "send me a code" again, which joins the back of the same queue.

## Reasoning towards the fix

The `Text` already carries a `kind`: `"code"` or `"bulk"`. The `Queue` ignores it.

The rate limit is not the problem, and raising it is not the fix. The gateway sets it, and the next campaign will be bigger. The problem is the order. Think about what the sender should pick each time it has room for one more text:

- If any code is waiting, a code. The oldest one first, so codes stay in the order they were asked for.
- Otherwise, the oldest offer.

That is two queues, each first in, first out, and a rule for choosing between them. Keep the `put`, `get` and `__len__` methods, so the sender does not change.

```bash
uv run python -m dove check 7
```

```text
  FAIL  each login code arrives within 5 seconds (Amara 115.0 s, Ben 100.0 s)
  PASS  codes go out in the order they were asked for
  PASS  all 6000 offers still go out, in order (6000 sent)
  PASS  the sender keeps to 50 texts a second
```

Dropping the campaign fails the third line. So does "newest first", which helps the codes and sends the offers backwards. A single sorted queue looks tempting until you notice that sorting by anything but arrival scrambles the offers too.

## Check it works

```text
  PASS  each login code arrives within 5 seconds (Amara 0.0 s, Ben 0.0 s)
  PASS  codes go out in the order they were asked for
  PASS  all 6000 offers still go out, in order (6000 sent)
  PASS  the sender keeps to 50 texts a second
```

The last offer still goes out at 09:02:00. The campaign lost two slots, and two people could sign in.

## What batching buys you

Bulk traffic has a second lever that transactional traffic does not: you can send it in batches. Most push services accept many messages in one request. Measure what that does, against a real HTTP server on your machine:

```bash
uv run python -m dove try fanout
```

```text
Python 3.13.16, Linux, 4 CPUs

  way                                requests   seconds   pushes/s
  one request each, 1 connection         2000     0.524      3,819
  one request each, 8 connections        2000     0.760      2,633
  batches of 100, 1 connection             20     0.010    199,462
  batches of 500, 1 connection              4     0.003    601,504
```

On this machine, batches of 100 sent pushes about fifty times faster than one request each. Eight connections were slower than one, because the client and the server share one Python process here, and the threads compete for it. Against a real provider across a network, each request also pays a round trip of tens of milliseconds, so the gap from batching is far bigger, and parallel connections do help. Measure your own setup before you believe either number.

## Trade-offs and when the usual advice is wrong

- **Strict priority can starve.** If codes arrived faster than fifty a second, offers would never go out. Real systems use weighted lanes, such as nine slots for transactional to one for bulk, so every lane moves.
- **Separate limits beat shared ones.** Where the provider offers it, send transactional and bulk on separate accounts or sending pools. Then no campaign, however large, can use up the code lane's rate.
- **Spread campaigns out.** A campaign does not need to leave at 09:00:00. Pacing it over an hour keeps the queue short for everything else, and is kinder to your own servers when the replies arrive.
- **Deadlines belong on the message.** A code that would arrive after it expires is worse than useless: it confuses people. Carry an expiry, and drop expired messages on purpose, counted.
- **"Just add a priority field"** is half a fix. The field is useless until the queue reads it, and the case shows how easily it does not.

## Exercise

1. Change the queue to weighted lanes: up to nine codes, then one offer. Add a stream of a hundred codes a second for ten seconds. Do offers still move?
2. Give each code an expiry and have the sender skip codes that would arrive too late. Rerun the shipped case with that change alone. How many codes are sent?
