# Once, in order, on time

A hands-on notifications workshop. Eight chapters, each explaining one idea in depth, each with a real bug in a small parcel company called Dovecote for you to fix: the transactional outbox, idempotency keys, ordering, permanent errors and backoff, quiet hours across time zones, digests, priority lanes and signed webhooks. **Pip**, the carrier pigeon who flies Dovecote's post, quizzes you along the way.

**Workshop site:** [notifications.jishanahmed.in](https://notifications.jishanahmed.in)

## Quick start

You need [uv](https://docs.astral.sh/uv/) and git. uv installs Python for you. The lab uses the Python standard library only.

```bash
git clone https://github.com/jars-demo/notifications-demo.git
cd notifications-demo/lab
uv sync
uv run python -m dove run 1
```

## How a case works

| Command                             | What it does                                                   |
| ----------------------------------- | -------------------------------------------------------------- |
| `uv run python -m dove list`        | every case, and which ones are fixed                           |
| `uv run python -m dove run N`       | run case N and watch the bug happen                            |
| `uv run python -m dove check N`     | check your fix: the bug is gone, and the message still arrives |
| `uv run python -m dove hint N`      | a nudge from Pip                                               |
| `uv run python -m dove try fanout`  | 2,000 pushes to a local HTTP server, one by one or batched     |
| `uv run python -m dove try outbox`  | what an outbox row costs in a real SQLite commit               |
| `uv run python -m dove try backoff` | 1,000 phones retry through an outage, with and without jitter  |
| `uv run python -m dove try digest`  | the same updates through four batching rules                   |

Fix the code in `lab/cases/`. Start a case over with `git restore cases/` from `lab/`.

Every check tests that the message still arrives, so sending nothing is never a fix.

## The chapters

| #   | Chapter                                                     | The case                                  |
| --- | ----------------------------------------------------------- | ----------------------------------------- |
| 01  | [Send after commit: the outbox](workshop/01-the-outbox.md)  | The text for a parcel that never left     |
| 02  | [Once, even when you retry](workshop/02-idempotency.md)     | Delivered, delivered, delivered           |
| 03  | [Out of order](workshop/03-ordering.md)                     | Delivered, then out for delivery          |
| 04  | [Errors that never heal](workshop/04-permanent-failures.md) | The phone that no longer exists           |
| 05  | [Quiet hours and time zones](workshop/05-quiet-hours.md)    | The 3 a.m. buzz                           |
| 06  | [Batching without silence](workshop/06-digests.md)          | Silence at the busy shop                  |
| 07  | [Priority lanes](workshop/07-priority.md)                   | The login code that came too late         |
| 08  | [Webhooks you can trust](workshop/08-webhooks.md)           | The receipt that came back from yesterday |

About two and three quarter hours in all. Chapter 08 ends with a ten point checklist.

## Layout

```text
lab/cases/            the eight cases: one real notification bug each
lab/dove/             the CLI, the checks and the four experiments
lab/tests/            every case fails as shipped, passes when fixed, and rejects common wrong fixes
workshop/             the chapters, in Markdown
frontend/             the workshop site (Next.js), which renders workshop/
```

Run the lab's tests with `cd lab && uv run pytest`. The solutions are in `lab/tests/solutions/`: peek only when truly stuck.

## Run the site locally

```bash
cd frontend
npm ci
npm run dev
```

`npm run verify` runs lint, type checks, formatting, unit tests and a production build. For the browser tests, build and start the site, then run Playwright against it:

```bash
npm run build && npx next start -p 3114
E2E_BASE_URL=http://localhost:3114 npx playwright test
```

## License

[MIT](LICENSE)
