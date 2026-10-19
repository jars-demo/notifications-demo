# Errors that never heal

> Retrying is right for a provider that is busy or broken, and wrong for an answer that will never change. Read the status code before you retry.

**Time:** 20 minutes

## Goal

By the end of this chapter you can sort provider responses into retry, give up and clean up, and handle each one so that nothing is retried forever and nothing worth sending is dropped.

## The idea

### Transient and permanent failures

| Response | Meaning | What to do |
| --- | --- | --- |
| 2xx | sent | done |
| 429 Too Many Requests | slow down | retry later, honour `Retry-After` |
| 500, 502, 503, 504 | the provider is broken right now | retry later, with backoff |
| 400 Bad Request, 413, 422 | this request can never succeed as it is | do not retry, dead-letter it |
| 410 Gone (push), hard bounce (email) | the address or token is dead | do not retry, remove it |
| 401, 403 | your credentials are wrong | do not retry, alert a human |

Retrying a 400 wastes requests and fills logs. Retrying a 410 is worse: push services and email providers watch for senders who keep hitting dead tokens and bounced addresses, and they throttle or block them. Your sender reputation is shared by every notification you send.

### Dead letters

When a message cannot be sent, or has used up its attempts, it goes to a **dead letter queue**: a place where a person or a tool can look at it, fix the cause and replay it. A dead letter is not a failure to hide. It is evidence.

### Cleaning up after a 410

APNs answers 410 and FCM answers `UNREGISTERED` when an app was uninstalled or a token expired. The only correct response is to delete that token, so no future notification tries it. The same goes for hard bounces in email: suppress the address.

## The case

Open `lab/cases/case03_permanent.py`. A push worker sends two rounds of build notifications to four users and one product announcement that is too long for the push service. Its `classify()` retries everything that is not a 200, with backoff, up to eight attempts. u_1042's old phone token is dead.

```bash
uv run python -m notify run 3
```

```text
pushes delivered: 8
requests made:    37

  tok_1041_ios      requests: 10
  tok_1042_new      requests: 2
  tok_1042_old      requests: 16
  tok_1043_android  requests: 4
  tok_1044_ios      requests: 5

u_1042's dead token still on file: yes
dead letters: 3
  tok_1042_old      after 8 tries: Build #418 failed on main.
  tok_1041_ios      after 8 tries: Release 4.2 is out: faster syn
  tok_1042_old      after 8 tries: Build #419 passed on main.
```

Every live device got its pushes, so nothing looks wrong to the users. But 22 of the 37 requests could never succeed, and the dead token is still on file, ready to be tried 8 more times on every future push.

## Reasoning towards the fix

The worker already knows what to do with `"gone"` (forget the token) and `"reject"` (dead-letter at once). `classify()` just never returns them. Map each status to the right outcome: 200 is done, 410 is gone, 429 and 5xx are worth a retry, and any other 4xx is a rejection.

## Check your fix

```bash
uv run python -m notify check 3
```

As shipped:

```text
  PASS  every live device gets both pushes, through the 429s and the 503s
  FAIL  the dead token is tried once, then forgotten (tried 16)
  FAIL  the push that is too long goes to dead letters after one try
  FAIL  no request is wasted: 15 in all (37)
```

The first check is there so that "never retry anything" fails: the 429s and 503s must still get through.

## In production

- **Honour Retry-After.** A 429 or 503 often says how long to wait. Use it instead of your own schedule when it is present.
- **Validate before sending.** Payload size, address format and template variables can be checked before the first request, which turns some permanent failures into a test failure.
- **Bounce and complaint webhooks.** Email providers report hard bounces and spam complaints asynchronously. Suppress those addresses, or your domain's reputation suffers for every user.
- **Alert on credentials.** A 401 from a provider means every notification is failing. Page someone; do not retry quietly.

## Key points

- Transient failures (429, 5xx) deserve a retry with backoff. Permanent ones (400, 410) never do.
- A dead token or address must be removed, or it is tried forever and hurts your reputation.
- Messages that cannot be sent go to a dead letter queue, where someone can see them.
- Read the status code before deciding to retry.
