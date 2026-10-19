// Facts shown on the site. Every symptom and number is real output from the lab:
// `uv run python -m notify run N` and `notify try`. Unit tests compare each one with the chapters.

export const REPO_URL = 'https://github.com/jars-demo/notifications-demo'
export const SITE_URL = 'https://notifications.jishanahmed.in'
export const TITLE = 'Once, in order, on time'
export const TAGLINE =
  'A hands-on notifications workshop in ten chapters: the transactional outbox, idempotency keys, permanent failures, backoff and jitter, ordering, preferences, quiet hours, digests, priority lanes and signed webhooks.'

export type Level = 'Delivering once' | 'Delivering right' | 'Delivering at scale'

export const LEVELS: readonly { name: Level; chapters: readonly number[]; about: string }[] = [
  {
    name: 'Delivering once',
    chapters: [1, 2, 3, 4],
    about:
      'Send only what happened, never twice, and retry only what can succeed, without a storm.',
  },
  {
    name: 'Delivering right',
    chapters: [5, 6, 7],
    about: 'The latest state in the right order, only to people who want it, when they are awake.',
  },
  {
    name: 'Delivering at scale',
    chapters: [8, 9, 10],
    about: 'Batch without silence, keep urgent messages fast, and trust what providers tell you.',
  },
]

export function levelOf(chapter: number): Level {
  return LEVELS.find((level) => level.chapters.includes(chapter))?.name ?? 'Delivering once'
}

/** What goes wrong in each case, as the lab prints it. */
export const SYMPTOMS: Record<string, string> = {
  '01': 'fay@example.com was told they joined ws_orbit. They did not.',
  '02': 'ada@example.com  got 4  (should get 1)',
  '03': 'tok_1042_old      requests: 16',
  '04': 'busiest second after recovery: t=31 s, 1000 requests (10.0x capacity)',
  '05': 'card says: building  the truth: live',
  '06': 'marketing sent after an unsubscribe: 2',
  '07': 'made 03:05  sent 03:05  Priya commented on your pull request.  <- buzzed in quiet hours',
  '08': 'longest wait: 604 minutes',
  '09': 'It arrives 115.0 s later: expired before it arrived',
  '10': 'replays accepted:         200 of 200',
}

/** Real measurements from the chapters and from `notify try`. */
export const MEASURED = {
  outbox: [
    { label: 'change only, one commit', value: '535.1 µs' },
    { label: 'change and outbox row, one commit', value: '576.7 µs' },
    { label: 'change, then outbox row, two commits', value: '1183.8 µs' },
  ],
  backoff: [
    { strategy: 'retry every second', requests: '33,000', peak: '1,000', done: '34.0 s' },
    {
      strategy: 'exponential, 1 2 4 8 ... 60 s',
      requests: '8,000',
      peak: '1,000',
      done: '243.0 s',
    },
    { strategy: 'exponential, full jitter', requests: '7,516', peak: '48', done: '89.1 s' },
    { strategy: 'exponential, equal jitter', requests: '7,000', peak: '68', done: '60.8 s' },
  ],
} as const

export const QUICKSTART = `git clone https://github.com/jars-demo/notifications-demo.git
cd notifications-demo/lab
uv sync
uv run python -m notify run 1`
