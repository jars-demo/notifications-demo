# Quiet hours and time zones

> Quiet hours are a promise about someone's night, so they have to be read on that person's clock. A notification held for the morning must still arrive, and an urgent one must never wait.

**Time:** 20 minutes

## Goal

By the end of this chapter you can explain why time rules belong to the recipient, implement quiet hours that wrap midnight in any time zone, and say which notifications may break them.

## Why "when" is part of "what"

A notification is an interruption. The same words are welcome at nine in the morning and infuriating at three. People who are woken by an app turn its notifications off, and an app with notifications off has lost its best channel for good. So most products let customers set quiet hours, and many apply sensible ones by default.

Two rules come with that promise:

1. **Hold, do not drop.** "Your parcel arrives tomorrow" is still useful at seven. Dropping it to keep the night quiet just moves the failure.
2. **Urgent goes through.** A security alert or a driver at the door matters more than sleep. That is the customer's choice to make, and the default should match what they would choose.

## Time zones are the person's, not the server's

Servers run in UTC, and they should. Customers do not live in UTC. A rule like "between 22:00 and 07:00" is meaningless until you say *whose* 22:00. Read it on the customer's clock, every time, by converting the current instant into their zone before you compare.

Two details catch people:

- **The window wraps midnight.** 22:00 to 07:00 is not `22 <= hour < 7`, which is never true. It is "after 22:00 *or* before 07:00".
- **Offsets are not whole hours.** Mumbai is UTC+5:30. Kathmandu is UTC+5:45. Any code that adds "hours" to the time is wrong for a few hundred million people.

The case uses fixed offsets on dates well away from any clock change, so it runs the same on every machine. In production you would store an IANA zone name like `Asia/Kolkata` and let `zoneinfo` work out the offset for each instant, daylight saving included.

## The case

Open `lab/cases/case05_quiet_hours.py`. Dovecote now delivers in London, Mumbai and Los Angeles. The scheduler checks quiet hours whenever a push is created, holds it if needed, and looks at what it is holding every five minutes.

```bash
uv run python -m dove run 5
```

```text
quiet hours: 22:00 to 07:00, on each customer's clock
times below are on the customer's clock

  Ravi   made 08:30  sent 12:30  Your parcel DC-5101 arrives today.  <- held in daytime
  Amara  made 04:10  sent 04:10  Someone signed in to your account on a new phone.
  Lena   made 22:00  sent 23:00  Your parcel DC-5102 arrives tomorrow.  <- buzzed in quiet hours
  Lena   made 07:00  sent 07:00  How did we do? Rate your delivery.
  Ravi   made 03:05  sent 03:05  How did we do? Rate your delivery.  <- buzzed in quiet hours
  Amara  made 23:00  sent 07:00  Your parcel DC-5103 arrives tomorrow.
```

Ravi was woken at 3:05 to rate a delivery. Lena's 22:00 push was held, but only by luck: it was 06:00 in UTC. It was released at 07:00 UTC, which was 23:00 for her. Ravi's morning news sat in the queue until lunchtime. Amara's pushes are all right, which is exactly why this bug survives testing: the team is in London, where the clock matches UTC for half the year.

## Reasoning towards the fix

All three wrong lines have one cause. `is_quiet` takes the customer as an argument and never uses it. It reads `now.time()` straight off a UTC timestamp. The window logic itself, with its `or` for wrapping midnight, is right.

Turn the instant into the customer's own time before you take the time of day. Python's `datetime` can do that for any `tzinfo`, fixed offset or named zone, in one call.

```bash
uv run python -m dove check 5
```

```text
  FAIL  nobody is buzzed in their quiet hours (Lena at 23:00, Ravi at 03:05)
  FAIL  every held push goes out at 07:00 on the customer's clock (3 held)
  FAIL  a daytime push goes out at once (1 held by mistake)
  PASS  an urgent push is never held
```

The checker does its own time arithmetic, so it cannot be fooled by changing the helpers in the case. Dropping pushes that arrive at night fails the second line. Holding everything, urgent included, fails the last.

## Check it works

```text
  PASS  nobody is buzzed in their quiet hours (nobody)
  PASS  every held push goes out at 07:00 on the customer's clock (3 held)
  PASS  a daytime push goes out at once (0 held by mistake)
  PASS  an urgent push is never held
```

## Trade-offs and when the usual advice is wrong

- **The 07:00 spike.** Holding everything until seven sends it all at seven, in every zone, on the hour. That is a traffic spike for you and a wall of buzzes for the customer. Spread releases over a few minutes, and collapse held updates into one (chapter 06).
- **Some messages expire.** "Your driver is five minutes away" is useless at seven. Give time-sensitive messages a deadline, and drop them, on purpose and counted, when it passes.
- **Where is the customer now?** The zone on their account is where they live. Their phone knows where they are. For push, the device's zone is usually the better guess. For email, it matters less, because email does not buzz.
- **Clock changes.** On the night the clocks go back, 01:30 happens twice. On the night they go forward, 02:30 never happens. Named zones handle this. Hand written offsets do not.
- **"Never send at night" is not always right.** A night shift worker's night is your afternoon. Let people set their own hours, and treat your default as a default.

## Exercise

1. Add a customer in Kathmandu (UTC+5:45). Does your fix need to change?
2. Give "arrives today" pushes a deadline of 18:00 local time, and drop them after it. Which push in the plan would that affect?
