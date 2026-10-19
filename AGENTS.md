# AGENTS.md

Guidance for AI coding agents and developers. Humans: start with [README.md](README.md).

## What this is

"Once, in order, on time": ten chapters, each a notification engineering idea explained in depth,
with a real bug in a small notification service. `lab/` holds the cases and the checker;
`workshop/` the chapters; `frontend/` the site.

## Map

```text
lab/cases/caseNN_*.py       one deliberate bug each; run() shows the symptom
lab/notify/checks.py        check_NN(module) -> [(label, ok)]; the message must still arrive
lab/notify/provider.py      a local email API over real HTTP, with idempotency keys and faults
lab/notify/experiments.py   `notify try fanout | outbox | backoff | digest`
lab/tests/                  cases fail as shipped, pass with solutions/, reject wrong fixes
frontend/src/lib/site.ts    symptoms and measured numbers: every value is real lab output
frontend/src/lib/storm.json requests per second from case 04 and its fix, seed 7
frontend/src/lib/tokens.ts  colour pairs; a test checks them against globals.css and WCAG AA
```

## Commands

```bash
cd lab && uv sync && uv run pytest && uv run ruff check .
cd frontend && npm ci && npm run verify
```

## Rules

1. **The bugs are the product.** Never fix a case. Change a case, its check and its solution
   together, and keep the tests passing.
2. **Real engineering, no story world.** Cases model a real notification service: users, events,
   providers, queues. Keep examples technical.
3. **Deterministic.** Pretend clocks, scripted faults and seeded randomness. Never lucky timing.
4. **Standard library only** in `lab/`.
5. **Every number is real,** and unit tests compare the site's numbers with the chapters.
6. **Writing style.** Plain English, short sentences, no em dashes. Conventional Commits, no AI
   attribution trailers.
