# Once, in order, on time

A hands-on notifications workshop in ten chapters. Each chapter explains one idea behind every email, push and SMS a product sends, and hands you a real bug in a small notification service to fix: the transactional outbox, idempotency keys, permanent failures, backoff and jitter, ordering, preferences and consent, quiet hours across time zones, digests, priority lanes and signed webhooks.

**Workshop site:** [notifications.jishanahmed.in](https://notifications.jishanahmed.in)

## Quick start

You need [uv](https://docs.astral.sh/uv/) and git. uv installs Python for you. The lab uses the Python standard library only: the email provider and the webhooks run on localhost.

```bash
git clone https://github.com/jars-demo/notifications-demo.git
cd notifications-demo/lab
uv sync
uv run python -m notify run 1
```

## How a case works

| Command | What it does |
| --- | --- |
| `uv run python -m notify list` | every case, and which ones are fixed |
| `uv run python -m notify run N` | run case N and watch the bug happen |
| `uv run python -m notify check N` | check your fix: the bug is gone, and the message still arrives |
| `uv run python -m notify hint N` | a nudge, one step at a time |
| `uv run python -m notify try fanout` | 2,000 pushes to a local HTTP server, one by one or batched |
| `uv run python -m notify try outbox` | what an outbox row costs in a real SQLite commit |
| `uv run python -m notify try backoff` | 1,000 senders retry through an outage, four ways |
| `uv run python -m notify try digest` | the same updates through four batching rules |

Fix the code in `lab/cases/`. Start a case over with `git restore cases/` from `lab/`. Every check tests that the message still arrives, so sending nothing is never a fix.

## The chapters

| # | Chapter | The case |
| --- | --- | --- |
| 01 | [Send after commit: the outbox](workshop/01-the-outbox.md) | The invitation to a team that never happened |
| 02 | [Once, even when you retry](workshop/02-idempotency.md) | One payment, four receipts |
| 03 | [Errors that never heal](workshop/03-permanent-failures.md) | The device that no longer exists |
| 04 | [Backoff and jitter](workshop/04-backoff-and-jitter.md) | The retry storm |
| 05 | [Out of order](workshop/05-ordering.md) | Live, then building |
| 06 | [Preferences and consent](workshop/06-preferences.md) | The newsletter after the unsubscribe |
| 07 | [Quiet hours and time zones](workshop/07-quiet-hours.md) | The 3 a.m. buzz |
| 08 | [Batching without silence](workshop/08-digests.md) | The digest that never went out |
| 09 | [Priority lanes](workshop/09-priority.md) | The sign-in code that came too late |
| 10 | [Webhooks you can trust](workshop/10-webhooks.md) | The delivery receipt from yesterday |

About three and a half hours in all. Chapter 10 ends with a ten point production checklist.

## Layout

```text
lab/cases/            the ten cases: one real notification bug each
lab/notify/           the CLI, the checks, the local email provider and the experiments
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

`npm run verify` runs lint, types, formatting, unit tests and a production build. Browser tests:

```bash
npm run build && npx next start -p 3114
E2E_BASE_URL=http://localhost:3114 npx playwright test
```

## License

[MIT](LICENSE)
