# AGENTS.md

Guidance for coding agents and developers. Humans: start with [README.md](README.md).

## What this is

"Once, in order, on time": eight chapters, each a notifications idea explained in depth and a
real bug in a small parcel company, Dovecote, that shows it. `lab/` holds the cases and the
checker; `workshop/` the chapters; `frontend/` the site.

## Map

```text
lab/cases/caseNN_*.py         one deliberate notification bug each; run() shows the symptom
lab/dove/checks.py            check_NN(module) -> [(label, ok)]; tests the fix and the delivery
lab/dove/experiments.py       `dove try fanout | outbox | backoff | digest`
lab/dove/__main__.py          CLI: list, run, check, hint, try; case titles live here
lab/tests/test_cases.py       each case fails as shipped and passes with tests/solutions/
lab/tests/test_wrong_fixes.py wrong fixes must fail their check, other valid fixes must pass
frontend/src/lib/site.ts      cases and measured numbers: every value is real lab output
frontend/src/lib/digest.ts    the digest board's rules, the same as `dove try digest`
frontend/src/lib/pip.ts       Pip's note and quiz for each page
frontend/src/lib/tokens.ts    colour pairs; a test checks them against globals.css and WCAG AA
```

## Commands

```bash
cd lab && uv sync && uv run pytest && uv run ruff check . && uv run ruff format --check .
cd frontend && npm ci && npm run verify
cd frontend && npm run build && npx next start -p 3114   # then, in another shell:
E2E_BASE_URL=http://localhost:3114 npx playwright test    # CHROMIUM_PATH=... to use a local Chromium
```

## Rules

1. **The bugs are the product.** Never fix a bug in `lab/cases/`. Change a case, its check, its
   solution and its wrong fixes together, and keep `test_case_is_broken_as_shipped` passing.
2. **Sending nothing is never a fix.** Every check tests that the message still arrives as well
   as that the bug is gone. Add a wrong fix to `test_wrong_fixes.py` when you find a new one.
3. **Bugs must be deterministic.** A case shows its symptom on every run, on any OS. Use fake
   clocks, scripted faults and fixed seeds, never real timing.
4. **Standard library only** in `lab/`.
5. **Every number is real.** Output and timings in chapters and on the site come from real runs,
   and unit tests compare the site's numbers with the chapters and the lab.
6. **Writing style.** Plain English, short sentences, no em dashes. Conventional Commits, no
   attribution trailers.
