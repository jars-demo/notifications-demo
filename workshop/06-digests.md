# Batching without silence

> Batching stops a busy customer from being buzzed forty times a day. Done carelessly, it stops them from being told anything at all. Every batching rule needs a limit on how long one update may wait.

**Time:** 20 minutes

## Goal

By the end of this chapter you can compare four batching rules (every update, throttle, debounce and capped debounce), predict how each behaves on quiet and busy traffic, and explain why an uncapped debounce starves the busiest customers.

## Fatigue is a real failure

Most notification bugs are about a message that did not arrive. This one is about too many arriving. A customer with forty parcels a day does not want forty buzzes. They mute the app, and then they miss the one push that mattered. Every notification spends a little of the customer's attention, and attention does not refill quickly.

The fix is to send less often, each push carrying several updates: a **digest**. The question is when to send it.

## Four rules

| Rule             | Sends a push when                                                   | Good at                     | Bad at                     |
| ---------------- | ------------------------------------------------------------------- | --------------------------- | -------------------------- |
| every update     | each update arrives                                                 | speed                       | busy customers             |
| throttle         | at most once per window, carrying anything that waited               | a steady, bounded rate      | a burst: splits it up      |
| debounce         | things have been quiet for a while                                  | bursts: one push per burst  | traffic that never pauses  |
| capped debounce  | things go quiet, or the first waiting update reaches a maximum age | both                        | a little more code         |

Debounce is the natural choice for digests, because updates come in bursts: a van is unloaded, twelve parcels are scanned in a minute, then nothing for an hour. Wait for the burst to finish and send one push. The trap is a customer whose updates never stop. Each new update resets the timer, and the timer never fires.

Measure all four on the same traffic:

```bash
uv run python -m dove try digest
```

```text
Updates for one customer, in minutes. A push carries every update waiting for it.

busy shop: 36 updates
  rule                   pushes  longest wait
  every update               36         0 min
  throttle, 15 min           13        15 min
  debounce, 10 min            1       185 min
  debounce 10, cap 30         6        30 min

a burst: 13 updates
  rule                   pushes  longest wait
  every update               13         0 min
  throttle, 15 min            3        14 min
  debounce, 10 min            2        21 min
  debounce 10, cap 30         2        21 min

quiet day: 4 updates
  rule                   pushes  longest wait
  every update                4         0 min
  throttle, 15 min            3        13 min
  debounce, 10 min            2        15 min
  debounce 10, cap 30         2        15 min

a seeded working day: 1,000 customers, 6,924 updates
  rule                   pushes  longest wait
  every update            6,924         0 min
  throttle, 15 min        5,100        15 min
  debounce, 10 min        4,223       117 min
  debounce 10, cap 30     4,325        30 min
```

On a burst or a quiet day, debounce and capped debounce behave the same. They only differ for the busy shop, where plain debounce sends one push after more than three hours. Across a thousand customers the cap costs about 2% more pushes, and in exchange nobody waits more than half an hour. The simulator on the workshop's home page runs these same rules on these same patterns, so you can watch the timers move.

## The case

Open `lab/cases/case06_digest.py`. Kiln & Co, a pottery shop, gets a parcel scan every six minutes from 08:00 to 18:00. The digest code means to send after ten quiet minutes, and never later than thirty minutes after the first update in the digest.

```bash
uv run python -m dove run 6
```

```text
Kiln & Co: 100 updates, 1 push
  pushes at:    18:04
  longest wait: 604 minutes
Amara: 3 updates, 1 push
  pushes at:    09:15
  longest wait: 15 minutes
Ben: 1 update, 1 push
  pushes at:    12:10
  longest wait: 10 minutes
```

Amara and Ben are fine. Kiln & Co, the customer with the most at stake, heard nothing all day, and then got one push with a hundred updates in it, four minutes after closing.

## Reasoning towards the fix

The constants are right: `QUIET = 10`, `MAX_WAIT = 30`. Read `add`, the one line that sets `digest.due`. It takes the earlier of two deadlines, and both of them are measured from `now`. The thirty minute deadline moves forward with every update, just like the quiet one. So the cap is not a cap.

The thirty minutes should be counted from a moment that does not move. The `Pending` record already keeps it.

```bash
uv run python -m dove check 6
```

```text
  FAIL  Kiln & Co hears within 30 minutes of every update (longest 604)
  PASS  Kiln & Co gets a digest, not a buzz per update (1 sent)
  PASS  Amara's three quick updates arrive in one push
  PASS  every update is in exactly one push
```

Sending every update at once fails the second and third lines.

## Check it works

```text
  PASS  Kiln & Co hears within 30 minutes of every update (longest 30)
  PASS  Kiln & Co gets a digest, not a buzz per update (20 sent)
  PASS  Amara's three quick updates arrive in one push
  PASS  every update is in exactly one push
```

A fixed thirty minute window from the first update, with no quiet timer at all, also passes. It is a fair design. It just makes Ben wait thirty minutes for his one update instead of ten.

## Trade-offs and when the usual advice is wrong

- **Not everything can wait.** A login code, a "driver at the door" or a security alert skips the digest entirely. Batching is for updates, not for requests a person is waiting on (chapter 07).
- **Summarise, do not concatenate.** A digest of a hundred lines is no better than a hundred pushes. "17 parcels arrived, 2 need a signature" is.
- **Per channel.** Push might digest every thirty minutes, email once a day, and the in-app inbox not at all. Each channel has its own cost of interruption.
- **Sliding windows hide in other places.** A session that extends on every request, a cache entry whose expiry is renewed on every read, a lock lease that renews on every heartbeat: each one needs a hard maximum, for the same reason.
- **"Debounce it" is common advice** for noisy events in user interfaces, where the stream always stops when the user stops typing. Server traffic does not stop on its own.

## Exercise

1. Change Kiln & Co's scans to every eleven minutes. What does the shipped code do now, and why?
2. Add a rule: never more than four pushes an hour per customer, whatever the batching says. Where does it go, and what happens to updates that would break it?
