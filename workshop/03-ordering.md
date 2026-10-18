# Out of order

> Events arrive in the order the network felt like, not the order they happened. If the receiver believes whatever came last, it will sometimes believe something old. Order needs a number from the source of truth.

**Time:** 20 minutes

## Goal

By the end of this chapter you can explain why queues reorder events, why timestamps are a poor fix, and how a per-entity sequence number lets a receiver drop stale and repeated events safely.

## Why order breaks

Every scan of a parcel becomes an event: at the depot, out for delivery, delivered. One worker reading one queue in order would keep that order. Nobody runs one worker. As soon as you have two, order is gone:

- Worker A takes "out for delivery" and stalls for a garbage collection pause.
- Worker B takes "delivered", which happened a minute later, and finishes first.
- A retry or a redelivery (chapter 02) sends an old event again, minutes after newer ones.

Partitioning by parcel id, so that one parcel's events always go to one worker, helps a lot. It does not save you from retries, redeliveries, a rebalance that moves a partition between workers, or a second path into the phone, like a push and a background refresh that race.

The safe assumption is the one from chapter 02: anything can arrive late, early or twice.

## The case

Open `lab/cases/case03_ordering.py`. Each customer's phone shows a tracking card for their parcel on the lock screen, and buzzes for every new status. `ARRIVED` is the order two workers and a retry delivered the events in. The `Phone.receive` method sets the card to whatever arrives.

```bash
uv run python -m dove run 3
```

```text
scans: 10, events delivered: 11

Ben's pushes:  at the depot, delivered, out for delivery
  lock screen says: out for delivery  the truth: delivered
Iris's pushes:  at the depot, out for delivery, out for delivery, missed you, retrying, out for delivery
  lock screen says: out for delivery  the truth: out for delivery
Noor's pushes:  at the depot, delivered, out for delivery
  lock screen says: out for delivery  the truth: delivered
```

Ben's parcel is on his doormat and his phone says it is on the van. He was buzzed for "delivered" and then, a moment later, buzzed again to say it was not. Iris got the same push twice.

## Reasoning towards the fix

The phone needs a way to tell which of two events is newer. There are four candidates.

**Arrival order.** That is the bug.

**Timestamps.** Each scan carries `at`, the time on the scanner. Comparing timestamps feels right, and it fails in a way that is hard to spot in testing. The time comes from whichever device made the scan, and device clocks drift. In the case, the van's scanner runs four minutes slow, so Ben's "delivered" scan carries an *earlier* time than the depot's "out for delivery". A timestamp rule would throw the true, newest event away. Clock skew between machines of seconds to minutes is normal, and even a well synced clock can step backwards.

**A status ladder.** "Delivered beats out for delivery" works until a parcel goes round twice. Iris was out, missed you, then out for delivery again in the afternoon. A ladder that never goes back down would ignore her second round.

**A sequence number from the source of truth.** The tracking service, the one place that decides what happened to a parcel, numbers each parcel's scans 1, 2, 3 as it records them. That number cannot drift, because it is not a clock. It is an order.

Give the phone a memory of the highest `seq` it has shown for each parcel. An event at or below that number is either stale or a repeat. Drop it quietly: no card change, no buzz.

```bash
uv run python -m dove check 3
```

```text
  FAIL  every lock screen ends on the parcel's latest status
  FAIL  pushes never go backwards or repeat (Ben got: at the depot, delivered, out for delivery)
  PASS  the newest scan of every parcel is pushed
```

## Check it works

```text
  PASS  every lock screen ends on the parcel's latest status
  PASS  pushes never go backwards or repeat (Ben got: at the depot, delivered)
  PASS  the newest scan of every parcel is pushed
```

Ben never hears "out for delivery". That is right. By the time it reached him it was no longer true. Telling him late would have been worse than not telling him.

## Trade-offs and when the usual advice is wrong

- **Drop or reorder?** Dropping stale events is right when each event carries the whole current state, like a status. If events are changes ("add one item to the basket"), you cannot drop one. You have to hold later events until the gap is filled, or fetch the current state from the source.
- **Gaps are allowed.** Ben's phone jumps from seq 1 to seq 3. For a status that is fine: 3 contains everything the customer needs. Do not wait for 2.
- **Version per entity, not global.** A single global counter forces every event through one place. A counter per parcel is cheap and is all a receiver needs.
- **Last write wins with timestamps** is the default in many databases and sync tools. It is a choice to accept lost updates when clocks disagree. Know that you have made it.
- **Collapse keys.** Push services let you send a collapse key or thread id so a newer notification replaces an older one on the device. Use them: they stop a phone that was offline from buzzing five times when it reconnects.

## Exercise

1. Change the case so events carry a change ("one more scan") rather than a status. Which events can you still drop?
2. Add a fourth parcel whose events arrive in reverse. How many pushes does its owner get with your fix, and which ones?
