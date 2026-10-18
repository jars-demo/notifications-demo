// Pip, the carrier pigeon who flies Dovecote's post. For each page: a short note and two quiz
// questions, each with one right answer and the reason it is right.

export type Question = {
  q: string
  options: readonly string[]
  answer: number
  why: string
}

export type Notes = { note: string; quiz: readonly Question[] }

const HOME: Notes = {
  note: 'I am Pip. Pigeons carried messages for centuries, and we learned the hard way that arriving once, in order and on time is the whole job. Try the digest board on this page: play the busy shop with plain debounce, then with the cap, and watch how long the first update waits.',
  quiz: [
    {
      q: 'Your SMS gateway times out. Was the text sent?',
      options: ['No, it failed', 'Yes, it is just slow', 'You cannot tell'],
      answer: 2,
      why: 'A timeout means no answer arrived in time. The text may have gone, and the answer been lost. That is why retries need an idempotency key.',
    },
    {
      q: 'Which does a queue usually promise?',
      options: ['Exactly once delivery', 'At least once delivery', 'At most once delivery'],
      answer: 1,
      why: 'Queues would rather hand you an event twice than lose it. Every handler has to be safe to run twice.',
    },
  ],
}

const WORKSHOP: Notes = {
  note: 'Eight chapters, one bug each, in the order a notification travels: from the change that causes it to the receipt that says what happened. Chapter 02 leans on chapter 01, so do those two first.',
  quiz: [
    {
      q: 'Every check tests two things. Which two?',
      options: [
        'Speed and memory use',
        'That the bug is gone, and the message still arrives',
        'That it compiles, and the tests pass',
      ],
      answer: 1,
      why: 'Sending nothing fixes every duplicate and every 3 a.m. buzz. A real fix still delivers the message.',
    },
    {
      q: 'Where do the fixed versions of the cases live?',
      options: ['lab/tests/solutions/', 'lab/dove/', 'Nowhere, you write them'],
      answer: 0,
      why: 'Peek only when truly stuck. The tests run every check against them, and against wrong fixes people often try.',
    },
  ],
}

const CHAPTERS: Record<string, Notes> = {
  '01-the-outbox': {
    note: 'A rollback cannot recall a text. Anything you do to the outside world inside a transaction is not part of the transaction.',
    quiz: [
      {
        q: 'You move the send to just after the commit. What can still go wrong?',
        options: [
          'Nothing, that is the fix',
          'The process dies between the commit and the send, so the text is never sent',
          'The commit rolls back the text',
        ],
        answer: 1,
        why: 'The change is safe on disk and nobody remembers to send. The outbox row is committed with the change, so a restarted relay finds it.',
      },
      {
        q: 'The outbox relay sends a row, then crashes before marking it sent. What happens?',
        options: [
          'The text is lost',
          'The text is sent again after a restart',
          'The database rolls the text back',
        ],
        answer: 1,
        why: 'An outbox is at least once. Maybe twice is a problem you can solve with idempotency keys. Maybe never is not.',
      },
    ],
  },
  '02-idempotency': {
    note: 'Look where the key is made. If it is inside the retry loop, every attempt is a stranger to the gateway.',
    quiz: [
      {
        q: 'Which idempotency key survives both a retry and a queue redelivery?',
        options: ['uuid4() made before the loop', 'The event id', 'The phone number and the text'],
        answer: 1,
        why: 'A redelivery runs the handler again, so a random key made before the loop is new again. The event id is the same every time.',
      },
      {
        q: 'Chen has two parcels and gets one text. Which key did that?',
        options: ['The event id', 'The phone number and the text', 'A fresh uuid4() per attempt'],
        answer: 1,
        why: 'Two different deliveries with the same words look like one. A key must name the thing you are telling someone about.',
      },
    ],
  },
  '03-ordering': {
    note: 'The van’s scanner runs four minutes slow. Any rule built on its timestamps will throw away the truth.',
    quiz: [
      {
        q: 'Seq 3 arrives, then seq 2. What should the phone do with seq 2?',
        options: ['Show it, it is newer to arrive', 'Drop it quietly', 'Wait for seq 1 first'],
        answer: 1,
        why: 'Seq 3 already holds the current status. Showing seq 2 would tell the customer something that is no longer true.',
      },
      {
        q: 'Why not order by the scanner’s timestamp?',
        options: [
          'Timestamps are too long to compare',
          'Device clocks drift, so a newer scan can carry an older time',
          'Timestamps are not sent with events',
        ],
        answer: 1,
        why: 'Skew of seconds to minutes between machines is normal. A sequence number from the source of truth is an order, not a clock.',
      },
    ],
  },
  '04-permanent-failures': {
    note: 'Three kinds of answer: try later, never for this message, never for this device. The worker already knows what to do with all three. Only classify() does not.',
    quiz: [
      {
        q: 'The push service answers 410 Gone. What should the worker do?',
        options: [
          'Retry with backoff',
          'Stop, and delete the device token',
          'Send it to dead letters and keep the token',
        ],
        answer: 1,
        why: 'The app install behind that token is gone for good. Keeping it costs a request on every future notification.',
      },
      {
        q: 'Why add jitter to exponential backoff?',
        options: [
          'To make each retry faster',
          'So clients that failed together do not all retry together',
          'To use fewer retries',
        ],
        answer: 1,
        why: 'In the backoff experiment, jitter dropped the busiest second from 1,000 requests to under 70.',
      },
    ],
  },
  '05-quiet-hours': {
    note: 'is_quiet() takes the customer and never looks at them. The window logic is right. The clock is the server’s.',
    quiz: [
      {
        q: 'Quiet hours are 22:00 to 07:00. Which test is right for a time t?',
        options: ['22:00 <= t < 07:00', 't >= 22:00 or t < 07:00', 't >= 07:00 and t < 22:00'],
        answer: 1,
        why: 'The window wraps midnight, so it is two ranges joined by or. The first is never true, and the last is the daytime.',
      },
      {
        q: 'A push is created at 03:05 for Ravi in Mumbai. What should happen?',
        options: ['Send it now', 'Drop it', 'Hold it until 07:00 Mumbai time'],
        answer: 2,
        why: 'Hold, do not drop. "Rate your delivery" is still useful in the morning. Only urgent pushes break quiet hours.',
      },
    ],
  },
  '06-digests': {
    note: 'Watch digest.due for Kiln & Co. Both deadlines are measured from now, so the cap moves every time an update arrives.',
    quiz: [
      {
        q: 'Updates arrive every five minutes, forever. When does a plain 10 minute debounce send?',
        options: ['Every 10 minutes', 'Every 5 minutes', 'Never, until they stop'],
        answer: 2,
        why: 'Each update resets the timer before it fires. On the busy shop it waited 185 minutes, and on the case 604.',
      },
      {
        q: 'The cap on a digest should count from which moment?',
        options: ['The latest update', 'The first update in the digest', 'The last push sent'],
        answer: 1,
        why: 'Counting from the latest update moves the cap with every update, so it is no cap at all.',
      },
    ],
  },
  '07-priority': {
    note: 'The rate limit is not the bug. The order is. A code should never stand in line behind a campaign.',
    quiz: [
      {
        q: 'Codes always go first. What can go wrong?',
        options: [
          'Codes arrive out of order',
          'If codes never stop, the campaign never goes out',
          'The sender breaks its rate limit',
        ],
        answer: 1,
        why: 'Strict priority can starve the lower lane. Weighted lanes, like nine codes to one offer, keep every lane moving.',
      },
      {
        q: 'In the fanout experiment, what did batches of 100 do compared with one request each?',
        options: [
          'About the same',
          'About fifty times the pushes a second',
          'Slower, from bigger requests',
        ],
        answer: 1,
        why: '3,819 pushes a second became 199,462 on the same machine. Across a real network, each request saved is also a round trip saved.',
      },
    ],
  },
  '08-webhooks': {
    note: 'The signature check is correct. It reads the timestamp and never looks at it again. A signed request stays signed forever.',
    quiz: [
      {
        q: 'An attacker replays a genuine, signed webhook from yesterday. What stops it?',
        options: [
          'The HMAC signature',
          'Refusing timestamps outside a tolerance window',
          'Comparing with hmac.compare_digest',
        ],
        answer: 1,
        why: 'The signature is valid, because it is the provider’s own request. Only the signed timestamp tells you it is old.',
      },
      {
        q: 'Inside the five minute window, the same receipt arrives twice. What should you do?',
        options: [
          'Refuse it with 401',
          'Act on it again',
          'Answer success and do nothing, because you have seen its id',
        ],
        answer: 2,
        why: 'Providers retry genuine webhooks too. Remember ids for as long as the window, and treat a repeat as already handled.',
      },
    ],
  },
}

export const NOTE_SLUGS = Object.keys(CHAPTERS)

export function notesFor(pathname: string): Notes {
  if (pathname === '/workshop') return WORKSHOP
  const slug = /^\/workshop\/([^/]+)$/.exec(pathname)?.[1]
  return (slug && CHAPTERS[slug]) || HOME
}
