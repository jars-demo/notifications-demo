# Out of order

> Queues reorder messages, and the clocks of different machines disagree. Order state changes by a sequence number from the system that owns the state, and drop anything older than what you have already shown.

**Time:** 20 minutes

## Goal

By the end of this chapter you can explain why events arrive out of order, why timestamps cannot fix it, and how to apply each entity's changes in the right order with sequence numbers.

## The idea

### Where reordering comes from

Even when a producer sends events in order, consumers see them out of order:

- several workers take messages from one queue, and a slow one finishes later
- a failed message is retried after newer ones have succeeded
- at-least-once delivery hands the same message over twice (chapter 02)
- push services and email providers make no promise about order at all

For notifications that report a state ("building", "live"), arriving out of order is not cosmetic. The last one to arrive is the one the user believes.

### Why timestamps are not enough

Ordering by `created_at` sounds right and fails in two ways. Clocks on different machines drift, sometimes by minutes. And two events in the same millisecond have no order at all.

### Sequence numbers

The system that owns the state should number each entity's changes: 1, 2, 3, in the order it made them. A consumer then keeps, for each entity, the highest number it has applied:

- a change with a higher number: apply it and notify
- a change with the same or a lower number: it is a duplicate or stale, drop it

The number is per entity, so different deployments never block each other. Kafka gives the same guarantee for one partition, which is why messages are partitioned by entity id.

## The case

Open `lab/cases/case05_ordering.py`. A deploy service emits a change for every step of a deployment. Each change notifies the team and updates the deployment's status card. Two workers share the events. dep_302 failed and was retried by hand, so it really is building again.

```bash
uv run python -m notify run 5
```

```text
changes: 10, events delivered: 11

dep_301 notifications: queued, live, building
  card says: building  the truth: live
dep_302 notifications: queued, building, building, failed, building
  card says: building  the truth: building
dep_303 notifications: queued, live, building
  card says: building  the truth: live
```

Two deployments are live and their cards say building. The team was told "building" after "live", and dep_302's redelivered event notified everyone twice.

## Reasoning towards the fix

Every change carries `seq`, numbered by the deploy service. Remember the newest `seq` applied for each deployment, and drop any change at or below it.

Look at the `at` field before you reach for it: dep_301's "live" was reported by a deploy agent whose clock runs four minutes slow, so by timestamp it happened before it was queued.

## Check your fix

```bash
uv run python -m notify check 5
```

As shipped:

```text
  FAIL  every card ends on the deployment's latest status
  FAIL  notifications never go backwards or repeat (dep_301: queued, live, building)
  PASS  the newest change of every deployment is notified, even a repeated status
```

Two wrong fixes fail. Ordering by the `at` timestamp loses dep_301's "live". Dropping a status that was already shown loses dep_302's second "building", which is real.

## In production

- **Version columns.** The same idea protects database writes: `UPDATE ... SET status = $1, version = $2 WHERE id = $3 AND version < $2`.
- **Gaps.** A consumer can see seq 5 before 4. If the intermediate step matters, hold 5 briefly or fetch the current state from the owner instead of trusting the event.
- **Notify on transitions that matter.** Users rarely want every step. Notifying only on terminal states (live, failed) avoids most ordering problems in what people see.
- **Partition by entity.** In Kafka, use the entity id as the message key, so one entity's events stay in order within a partition and one consumer.

## Key points

- Multiple workers, retries and redeliveries reorder events.
- Timestamps from different machines cannot be trusted to order them.
- Number each entity's changes at the source, and drop anything at or below the last applied number.
- Do not drop a repeated status: a real change can repeat one.
