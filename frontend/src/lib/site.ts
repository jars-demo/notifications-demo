// Facts shown on the site. Every symptom and number is real output from the lab, from
// `uv run python -m dove run N` and `dove try`, and unit tests compare them with the chapters.

export const REPO_URL = 'https://github.com/jars-demo/notifications-demo'
export const SITE_URL = 'https://notifications.jishanahmed.in'
export const TITLE = 'Once, in order, on time'

export const QUICKSTART = `git clone ${REPO_URL}.git
cd notifications-demo/lab
uv sync
uv run python -m dove run 1`

export type Case = {
  number: string
  title: string
  topics: string
  symptom: string
}

export const CASES: readonly Case[] = [
  {
    number: '01',
    title: 'The text for a parcel that never left',
    topics: 'dual writes, transactional outbox',
    symptom: 'texts for parcels still in the depot: 2',
  },
  {
    number: '02',
    title: 'Delivered, delivered, delivered',
    topics: 'timeouts, idempotency keys',
    symptom: 'Amara  got 4 texts  (should get 1)',
  },
  {
    number: '03',
    title: 'Delivered, then out for delivery',
    topics: 'reordering, sequence numbers',
    symptom: 'lock screen says: out for delivery  the truth: delivered',
  },
  {
    number: '04',
    title: 'The phone that no longer exists',
    topics: 'permanent errors, backoff, jitter',
    symptom: 'ben-old-phone   requests: 16',
  },
  {
    number: '05',
    title: 'The 3 a.m. buzz',
    topics: 'quiet hours, time zones',
    symptom: 'Ravi   made 03:05  sent 03:05  How did we do? Rate your delivery.',
  },
  {
    number: '06',
    title: 'Silence at the busy shop',
    topics: 'digests, debounce, caps',
    symptom: 'longest wait: 604 minutes',
  },
  {
    number: '07',
    title: 'The login code that came too late',
    topics: 'priority lanes, batching',
    symptom: 'It arrives 115.0 s later: expired before it arrived',
  },
  {
    number: '08',
    title: 'The receipt that came back from yesterday',
    topics: 'signed webhooks, replay',
    symptom: 'texts sent to Amara again: 201 (one was right)',
  },
]

/** What the home page promises you will learn. */
export const LEARN: readonly string[] = [
  'Why a notification sent inside a transaction can describe something that never happened, and how an outbox fixes it.',
  'Why a timeout is not a failure, and how to choose an idempotency key that survives retries and redeliveries.',
  'Why events arrive out of order, and why a sequence number beats a timestamp.',
  'Which errors to retry, which to give up on, and why backoff needs jitter.',
  "How to keep quiet hours on the customer's clock, and batch noisy updates without going silent.",
  'How to keep a login code from queueing behind a campaign, and how to stop webhook replays.',
]

/** The five steps every notification goes through, and the chapters that cover each. */
export const PIPELINE: readonly { step: string; detail: string; chapters: string[] }[] = [
  { step: 'Something happens', detail: 'A parcel leaves the depot', chapters: ['01'] },
  { step: 'Decide', detail: 'Who, which channel, and is now a good time', chapters: ['05', '06'] },
  { step: 'Order', detail: 'Newest wins, repeats are dropped', chapters: ['03'] },
  {
    step: 'Deliver',
    detail: 'Once, through retries and rate limits',
    chapters: ['02', '04', '07'],
  },
  { step: 'Learn what happened', detail: 'Signed receipts, read once', chapters: ['08'] },
]

/** Case 02 from start to finish, as the home page shows it. */
export const CASE_TWO = {
  run: [
    'deliveries: 4, events handled: 5 (ev-501 came twice)',
    'texts sent:    7 (four would be right)',
    'Amara  got 4 texts  (should get 1)',
  ],
  fix: ['key = f"delivered:{event.id}"', 'for attempt in range(1, self.ATTEMPTS + 1):'],
  check: [
    'PASS  Amara gets one text, despite two timeouts and a redelivery (got 1)',
    'PASS  Ben gets his text, though the first try was refused (got 1)',
    'PASS  Chen gets two texts for two parcels, though they read the same (got 2)',
  ],
}

export const MEASURED = {
  machine: 'Python 3.13.16, Linux, 4 CPUs',
  backoff: {
    headers: ['requests', 'busiest second', 'all sent by'],
    rows: [
      { label: 'retry every second', values: ['33,000', '1,000', '34.0 s'], verdict: 'lost' },
      {
        label: 'exponential, 1 2 4 8 ... 60 s',
        values: ['8,000', '1,000', '243.0 s'],
        verdict: 'lost',
      },
      { label: 'exponential, full jitter', values: ['7,516', '48', '89.1 s'], verdict: 'sent' },
      { label: 'exponential, equal jitter', values: ['7,000', '68', '60.8 s'], verdict: 'sent' },
    ],
  },
  fanout: [
    { label: 'one request each, 1 connection', requests: '2000', pushesPerSecond: '3,819' },
    { label: 'one request each, 8 connections', requests: '2000', pushesPerSecond: '2,633' },
    { label: 'batches of 100, 1 connection', requests: '20', pushesPerSecond: '199,462' },
    { label: 'batches of 500, 1 connection', requests: '4', pushesPerSecond: '601,504' },
  ],
  outbox: [
    { label: 'change only, one commit', shown: '138.8 µs' },
    { label: 'change and outbox row, one commit', shown: '138.2 µs' },
    { label: 'change, then outbox row, two commits', shown: '247.2 µs' },
  ],
  // The busy shop and the seeded day from `dove try digest`: [pushes, longest wait in minutes].
  digest: {
    'busy shop': { every: [36, 0], throttle: [13, 15], debounce: [1, 185], capped: [6, 30] },
    'a burst': { every: [13, 0], throttle: [3, 14], debounce: [2, 21], capped: [2, 21] },
    'quiet day': { every: [4, 0], throttle: [3, 13], debounce: [2, 15], capped: [2, 15] },
  },
} as const

export const CHECKLIST: readonly string[] = [
  'Write the notification in the same transaction as the change, and send it from an outbox.',
  'Assume every queue delivers twice. Make every handler safe to run again.',
  'Make idempotency keys from the event, never from the attempt, and reuse them on every retry.',
  "Order by a sequence number from the source of truth, never by arrival or by a device's clock.",
  'Sort failures into retry later, never for this message, and never for this device. Delete dead tokens.',
  'Back off exponentially, with jitter, and stop after a limit. Count what lands in dead letters.',
  "Read quiet hours on the customer's clock. Hold rather than drop, and let urgent messages through.",
  'Batch noisy updates, and cap how long any update may wait.',
  'Give messages a person is waiting for their own lane, ahead of every campaign.',
  'Verify webhook signatures over the raw body, refuse old timestamps, and remember ids you have handled.',
]
