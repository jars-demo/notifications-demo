# Backoff and jitter

> Exponential backoff spreads one client's retries over time. It does nothing for a thousand clients that failed at the same moment: they back off together and come back together. Jitter breaks them apart.

**Time:** 20 minutes

## Goal

By the end of this chapter you can explain a retry storm, compare retry strategies by numbers, and implement exponential backoff with full jitter.

## The idea

### Correlated failures

Failures in a notification system rarely come one at a time. A provider outage, a deploy or a network blip fails every in-flight send at once. Each of those sends now runs its retry policy. If the policies are identical, the retries are synchronised.

### What each strategy does

| Strategy | Wait before retry n | What a thousand clients do |
| --- | --- | --- |
| fixed delay | always the same | come back together, forever |
| exponential | 1, 2, 4, 8 ... up to a cap | come back together, less often |
| exponential with full jitter | random between 0 and that ceiling | spread out across the whole window |

After an outage, a provider usually comes back with less capacity than total demand. A synchronised wave hits it at many times its capacity. Most requests are turned away, they all back off by the same amount, and the next wave is synchronised too. This is a **retry storm**, and it can keep a recovered system down.

### Full jitter

Full jitter picks each wait uniformly at random between zero and the exponential ceiling:

```python
wait = random.uniform(0, min(cap, base * 2 ** (attempt - 1)))
```

The average wait halves, but the clients spread out over the whole window instead of arriving in a spike. Marc Brooker's AWS Architecture Blog post "Exponential Backoff And Jitter" compares the variants in detail and is worth reading.

## The case

Open `lab/cases/case04_jitter.py`. A thousand sends fail during a 30 second outage. The provider then accepts 100 requests a second and turns the rest away with 429. Every sender uses textbook exponential backoff: 1, 2, 4 ... seconds, capped at 60. The simulation is seeded, so you will see exactly these numbers.

```bash
uv run python -m notify run 4
```

```text
1000 sends fail during a 30 s outage; the provider then takes 100 a second

busiest second after recovery: t=31 s, 1000 requests (10.0x capacity)
requests made:  10500
last send got through at t=543 s

seconds with any traffic, after the outage:
  t=31: 1000, t=63: 900, t=123: 800, t=183: 700, t=243: 600, t=303: 500, t=363: 400, t=423: 300 ...
```

The provider was back at 30 seconds. The last notification got through after nine minutes, because every minute only one wave arrived and only 100 of it fitted.

## Reasoning towards the fix

The backoff schedule is fine. The problem is that every client shares it. `backoff()` already receives a random number generator. Use it to pick a wait between zero and the exponential ceiling.

## Check your fix

```bash
uv run python -m notify check 4
```

As shipped:

```text
  PASS  every send gets through (1000 of 1000)
  FAIL  after recovery, no second sees more than twice the capacity (busiest 1000)
  FAIL  everyone is through within two minutes (last at 543 s)
  FAIL  retries stay bounded: under 10,000 requests in all (10,500)
```

The checker runs the storm with three seeds. A fixed delay keeps the spike. A random wait of up to one second, with no growth, keeps every client retrying about twice a second: 70,332 requests in all, and 1,798 in the busiest second after recovery.

`uv run python -m notify try backoff` compares four strategies on a provider that recovers with 200 requests a second:

```text
  strategy                         requests  busiest second  all sent by
  retry every second                 33,000           1,000       34.0 s
  exponential, 1 2 4 8 ... 60 s       8,000           1,000      243.0 s
  exponential, full jitter            7,516              48       89.1 s
  exponential, equal jitter           7,000              68       60.8 s
```

Retrying every second gets everyone through fastest here, and costs four times the requests, all of them aimed at a provider that is trying to recover.

## In production

- **Retry budgets.** Limit retries to a fraction of normal traffic, so a big outage cannot multiply your load. Google's SRE book describes per-client and per-request budgets.
- **Circuit breakers.** After many failures in a row, stop calling the provider for a while and fail fast, or switch to a fallback provider.
- **Server hints win.** A `Retry-After` header beats any client-side schedule.
- **Queues help.** A queue in front of the sender turns a spike into a backlog the sender drains at a steady rate. Chapter 09 builds on that.

## Key points

- Failures are correlated, so retries are too.
- Exponential backoff without jitter keeps clients in lockstep.
- Full jitter: wait a random time between zero and the exponential ceiling.
- Measure strategies by peak load and time to recover, not by one client's view.
