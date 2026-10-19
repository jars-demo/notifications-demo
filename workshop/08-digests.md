# Batching without silence

> A digest that waits for a quiet moment never goes out for your most active users. Every batching rule needs a maximum wait that counts from the first update, not the last.

**Time:** 20 minutes

## Goal

By the end of this chapter you can compare the common batching rules, explain why pure debouncing starves busy users, and build a digest with a hard cap on delay.

## The idea

### Why batch

Forty pushes a day trains people to turn notifications off, and then they miss the one that matters. Batching related updates into one message keeps the signal: "6 new comments on PR #418" instead of six buzzes.

### Three rules

| Rule | How it works | Weakness |
| --- | --- | --- |
| throttle | at most one message per window, carrying everything since the last | waits the full window even for a single update |
| debounce | send once updates stop for N minutes | never sends while updates keep coming |
| debounce with a cap | send after N quiet minutes, or M minutes after the first update, whichever comes first | none worth worrying about |

The cap must be anchored. "M minutes after the **first** update in this digest" is a promise. "M minutes after the latest update" moves every time an update arrives, which makes it no cap at all.

### Measure the trade-off

`uv run python -m notify try digest` runs the same seeded day through each rule, for a thousand users:

```text
a seeded working day: 1,000 users, 6,924 updates
  rule                   pushes  longest wait
  every update            6,924         0 min
  throttle, 15 min        5,100        15 min
  debounce, 10 min        4,223       117 min
  debounce 10, cap 30     4,325        30 min
```

The capped debounce sends almost as few messages as pure debounce, and nobody waits more than 30 minutes.

## The case

Open `lab/cases/case08_digest.py`. Activity updates are gathered into a digest per user: sent after ten quiet minutes, and promised within thirty minutes of the first update. u_4001 follows a busy project that produces an update every six minutes all day.

```bash
uv run python -m notify run 8
```

```text
u_4001: 100 updates, 1 push
  pushes at:    18:04
  longest wait: 604 minutes
u_4002: 3 updates, 1 push
  pushes at:    09:15
  longest wait: 15 minutes
u_4003: 1 update, 1 push
  pushes at:    12:10
  longest wait: 10 minutes
```

The quiet users are fine. The most engaged user heard nothing all day, then one push with 100 updates after the project went quiet in the evening.

## Reasoning towards the fix

Read `add()`: `min(now + QUIET, now + MAX_WAIT)`. Both terms move with every update, and the first is always smaller, so the cap never applies. The digest already records `started`, the minute of its first update. Anchor the cap there.

## Check your fix

```bash
uv run python -m notify check 8
```

As shipped:

```text
  FAIL  the busy user hears within 30 minutes of every update (longest 604)
  PASS  the busy user gets digests, not a push per update (1 sent)
  PASS  three quick updates arrive in one push
  PASS  every update is in exactly one push
```

Sending every update at once passes the 30 minute promise and fails the rest: that is not a digest.

## In production

- **Store pending digests durably.** A digest held in memory is lost on deploy. Keep pending items in a table or a sorted set with their due time.
- **Collapse, do not just concatenate.** "Dana and 4 others commented" reads better than five lines, and push services can replace an earlier notification with a collapse key (`apns-collapse-id`, FCM `collapse_key`).
- **Urgent updates bypass the digest.** A mention or a failed payment should not wait 30 minutes.
- **Per-user rate limits** are the same idea from the other side: a ceiling on messages per hour, with the overflow folded into a digest.

## Key points

- Batching keeps notifications useful for active users.
- Pure debouncing never sends while updates keep coming.
- Cap the wait, and count the cap from the first update in the batch.
- Measure rules by messages sent and the longest wait, on realistic traffic.
