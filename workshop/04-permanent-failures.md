# Errors that never heal

> Retrying is right for a failure that might go away and wrong for one that never will. A worker that cannot tell them apart wastes its time on dead phones, delays the live ones, and never cleans up.

**Time:** 20 minutes

## Goal

By the end of this chapter you can sort a provider's errors into "try later", "never for this message" and "never for this device", explain why backoff needs jitter, and say what belongs in a dead letter queue.

## Three kinds of failure

Push services (and SMS gateways, and email servers) answer each request with a status. The details differ by provider, but they all fall into three groups:

| Answer                         | Meaning                                  | What to do                                    |
| ------------------------------ | ---------------------------------------- | --------------------------------------------- |
| 429 too many, 500, 502, 503    | busy or broken right now                 | wait, then retry, with a limit                |
| 400 bad request, 413 too large | this message can never be sent like this | stop, record it as a dead letter, alert       |
| 410 gone, "unregistered"       | this device token is dead                | stop, and delete the token so you never try again |

The third group is the one teams forget. A device token belongs to an app install. When someone deletes the app, resets their phone or buys a new one, the old token dies, and the push service tells you so. If you keep it, you pay for a request to it on every notification, forever. Over years, dead tokens can outnumber live ones.

## Backoff, and why it needs jitter

For the first group, retry with **exponential backoff**: wait 1 second, then 2, then 4, up to a ceiling, and give up after a set number of tries. Each wait doubles, so a long outage costs few requests.

There is a catch when many clients fail at once, which is exactly what an outage causes. If every client waits exactly 1, 2, 4, 8 seconds, they all come back at the same instant, in waves. Measure it:

```bash
uv run python -m dove try backoff
```

```text
1000 phones fail at 0 s. The gateway is down until 30 s,
then answers 200 requests a second and sends 503 to the rest.

  strategy                         requests  busiest second  all sent by
  retry every second                 33,000           1,000       34.0 s
  exponential, 1 2 4 8 ... 60 s       8,000           1,000      243.0 s
  exponential, full jitter            7,516              48       89.1 s
  exponential, equal jitter           7,000              68       60.8 s
```

Retrying every second finishes soonest here, by hitting the gateway with all 1,000 requests every second for thirty seconds. A real gateway that is struggling to come back would stay down under that load. Plain exponential backoff sends far fewer requests, but they arrive in synchronised waves of 1,000, and each wave mostly fails, so the last text goes out after four minutes. Adding **jitter**, a random part of the wait, spreads the clients out. The busiest second drops from 1,000 requests to under 70, and everyone is served within a minute and a half.

Full jitter (wait a random time between 0 and the ceiling) gives the lowest peak. Equal jitter (half the ceiling, plus a random half) finishes sooner, because nobody retries too early. Both beat no jitter by a wide margin.

## The case

Open `lab/cases/case04_permanent.py`. The worker sends two rounds of pushes, morning and afternoon, to four customers. Ben has two tokens: his new phone, and the one he replaced in the summer. Chen's pushes meet two 429s, Noor's a short outage. And marketing has slipped a catalogue into Amara's queue that is longer than the push service allows.

```bash
uv run python -m dove run 4
```

```text
pushes delivered: 8
requests made:    37

  amara-phone     requests: 10
  ben-new-phone   requests: 2
  ben-old-phone   requests: 16
  chen-phone      requests: 4
  noor-phone      requests: 5

Ben's old phone still on file: yes
dead letters: 3
  ben-old-phone   after 8 tries: Your parcel is out for delivery
  amara-phone     after 8 tries: Autumn at Dovecote: free next-d
  ben-old-phone   after 8 tries: Your parcel has been delivered.
```

Eight pushes needed 37 requests. Sixteen went to a phone that no longer exists, and it is still on file for tomorrow. The catalogue was tried eight times, though the answer was always going to be the same.

## Reasoning towards the fix

Look at the worker's `drain` method. It already knows what to do with each outcome. It deletes a token on `"gone"`. It sends a message straight to dead letters on `"reject"`. It backs off on `"retry"`. The trouble is upstream, in `classify`, which never returns anything but `"done"` or `"retry"`.

Read the docstring of the fake `PushService` and sort its codes into the three groups from the table above. Be careful with 429: it is the service asking you to slow down, not refusing the message, so it belongs with the outages.

```bash
uv run python -m dove check 4
```

```text
  PASS  every live phone gets both pushes, through the 429s and the 503s
  FAIL  Ben's dead token is tried once, then forgotten (tried 16)
  FAIL  the push that is too long goes to dead letters after one try
  FAIL  no request is wasted: 15 in all (37)
```

Never retrying fails the first line. Treating 410 as a plain rejection fails the second, because the token stays on file and the afternoon round tries it again.

## Check it works

```text
  PASS  every live phone gets both pushes, through the 429s and the 503s
  PASS  Ben's dead token is tried once, then forgotten (tried 1)
  PASS  the push that is too long goes to dead letters after one try
  PASS  no request is wasted: 15 in all (15)
```

## Trade-offs and when the usual advice is wrong

- **Honour Retry-After.** A 429 or 503 often says how long to wait. Use it instead of your own schedule when it is there.
- **A dead letter is a bug report, not a bin.** Something sent a message that can never be sent. Count dead letters, alert when the count moves, and keep enough to replay once the cause is fixed.
- **Unknown codes.** When a provider adds a new error code, which group should it fall into? Defaulting to "reject" loses messages loudly. Defaulting to "retry" wastes requests quietly. Loud is usually better.
- **Retry budgets.** Under a long outage, every worker retrying everything multiplies the load. Cap retries as a share of normal traffic, so a bad hour cannot become a bad day.
- **"Retry everything" feels safe** because nothing is ever dropped on purpose. In practice it hides permanent errors under transient ones and delays every live message behind the dead ones.

## Exercise

1. Make the push service return 429 with a pretend `Retry-After` of 30 seconds, and have the worker use it. How does Chen's timeline change?
2. Add a third round tomorrow. How many requests does Ben's old phone get with the shipped code? With yours?
