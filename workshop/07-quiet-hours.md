# Quiet hours and time zones

> "Not between 22:00 and 07:00" means on the user's clock. A server that checks its own clock in UTC wakes up half the world.

**Time:** 20 minutes

## Goal

By the end of this chapter you can store a user's time zone, compute quiet hours on their wall clock, release held notifications at the right moment, and keep urgent ones flowing.

## The idea

### Store instants in UTC, compare on the wall clock

Servers should store and compare **instants** in UTC: `2026-11-12T03:00Z` is one moment for everyone. But "22:00" is not an instant. It is a time on someone's wall clock, and it depends on where they are. Quiet hours are wall-clock rules:

1. Store each user's IANA time zone name, such as `Asia/Kolkata` or `America/Los_Angeles`, not an offset. Offsets change twice a year in many places.
2. To decide, convert the instant to the user's zone, then compare the local time with their window.

### Windows that cross midnight

22:00 to 07:00 wraps past midnight, so "between" is an OR: quiet if the local time is at or after 22:00, or before 07:00. A plain `start <= t < end` is never true for it.

### Urgent notices skip the hold

A new sign-in from an unknown device, a two-factor code, an outage page: these are wanted at 3 a.m. Mark them urgent and send them at once. Everything else is held and released when the window ends.

### Daylight saving time

On the night clocks change, some local times happen twice and some never happen. Python's `zoneinfo` handles both with the `fold` attribute. The lab uses fixed offsets on dates far from any change, to keep the case about the main mistake.

## The case

Open `lab/cases/case07_quiet_hours.py`. Users in London, Mumbai and Los Angeles have quiet hours from 22:00 to 07:00. The scheduler holds anything created in the window and releases it every five minutes. It checks `now.time()` on an aware UTC datetime.

```bash
uv run python -m notify run 7
```

```text
quiet hours: 22:00 to 07:00, on each user's clock
times below are on the user's clock

  u_3002  made 08:30  sent 12:30  Your weekly usage report is ready.  <- held in daytime
  u_3001  made 04:10  sent 04:10  New sign-in to your account from Chrome on Windows.
  u_3003  made 22:00  sent 23:00  Your trial ends tomorrow.  <- buzzed in quiet hours
  u_3003  made 07:00  sent 07:00  Priya commented on your pull request.
  u_3002  made 03:05  sent 03:05  Priya commented on your pull request.  <- buzzed in quiet hours
  u_3001  made 23:00  sent 07:00  Your trial ends tomorrow.
```

Only the London user, whose clock happens to match UTC, gets the behaviour they asked for. Mumbai is buzzed at 03:05 and has a morning push held until lunch. Los Angeles is buzzed at 23:00.

## Reasoning towards the fix

`is_quiet()` receives the user and ignores them. Convert `now` to the user's zone before taking the time: `now.astimezone(user.zone).time()`.

## Check your fix

```bash
uv run python -m notify check 7
```

As shipped:

```text
  FAIL  nobody is buzzed in their quiet hours (u_3003 at 23:00, u_3002 at 03:05)
  FAIL  every held push goes out at 07:00 on the user's clock (3 held)
  FAIL  a daytime push goes out at once (1 held by mistake)
  PASS  an urgent push is never held
```

Shifting every user by one fixed offset, such as London's, fixes nobody but London.

## In production

- **Where the zone comes from.** Ask the device: browsers and phones report an IANA name (`Intl.DateTimeFormat().resolvedOptions().timeZone` in JavaScript). Let users change it, and update it when they travel if they agree.
- **Thundering seven o'clock.** Releasing everything at exactly 07:00 local creates a spike at each zone's 07:00. Spread releases over a few minutes.
- **Schedule, do not poll.** Instead of re-checking every held message every few minutes, compute its release instant once and put it on a delayed queue.
- **Send-time optimisation.** Some systems go further and learn when each user usually opens notifications. Quiet hours are the floor, not the ceiling.

## Key points

- Store instants in UTC and each user's IANA time zone name.
- Quiet hours are wall-clock rules: convert to the user's zone before comparing.
- A window that crosses midnight needs OR, not AND.
- Urgent notices go out at once. Everything else waits for the user's morning.
