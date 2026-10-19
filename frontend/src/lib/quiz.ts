// Two questions at the end of every chapter, each with one right answer and the reason.

export type Question = {
  q: string
  options: readonly string[]
  answer: number
  why: string
}

export const QUIZ: Record<string, readonly Question[]> = {
  '01': [
    {
      q: 'An email is sent inside a transaction that then rolls back. What happens to the email?',
      options: ['It is cancelled too', 'It has already been sent', 'The provider holds it'],
      answer: 1,
      why: 'A rollback undoes rows in your database. It cannot reach into another system.',
    },
    {
      q: 'Why is "send right after commit" not enough?',
      options: [
        'Commits are slow',
        'A crash between the commit and the send loses the message',
        'Providers reject it',
      ],
      answer: 1,
      why: 'Nothing remembers the email was owed. An outbox row commits with the change and survives the crash.',
    },
  ],
  '02': [
    {
      q: 'A request to the provider times out. Was the email sent?',
      options: ['No', 'Yes', 'You cannot know'],
      answer: 2,
      why: 'The provider may have sent it and the answer was lost. That is why retries need idempotency keys.',
    },
    {
      q: 'Which is the best idempotency key for a payment receipt?',
      options: ['A new UUID per attempt', 'The recipient address', 'The event id plus the purpose'],
      answer: 2,
      why: 'It is the same on every retry and redelivery, and different for every notification.',
    },
  ],
  '03': [
    {
      q: 'The push service answers 410 Gone. What should the worker do?',
      options: ['Retry with backoff', 'Delete the token and stop', 'Retry once more'],
      answer: 1,
      why: 'The token is dead and will stay dead. Retrying it wastes requests and hurts your reputation.',
    },
    {
      q: 'Which of these deserves a retry?',
      options: ['400 Bad Request', '429 Too Many Requests', '401 Unauthorized'],
      answer: 1,
      why: '429 means slow down and try later. 400 can never succeed as it is, and 401 needs a human.',
    },
  ],
  '04': [
    {
      q: 'A thousand senders fail together and use the same exponential backoff. What happens?',
      options: ['They spread out', 'They come back together, in waves', 'They give up'],
      answer: 1,
      why: 'The same schedule keeps them in lockstep. Jitter is what spreads them.',
    },
    {
      q: 'What does full jitter wait before retry n?',
      options: [
        'Exactly base x 2^n',
        'A random time between zero and min(cap, base x 2^n)',
        'A random second',
      ],
      answer: 1,
      why: 'Randomising across the whole window spreads clients that failed at the same moment.',
    },
  ],
  '05': [
    {
      q: 'Why not order events by their timestamps?',
      options: [
        'Timestamps are too long',
        'Clocks on different machines disagree',
        'JSON loses them',
      ],
      answer: 1,
      why: 'A slow clock makes a later event look earlier. A sequence number from the source cannot drift.',
    },
    {
      q: 'An event arrives with the same seq as the last one applied. What do you do?',
      options: ['Apply it again', 'Drop it: it is a duplicate', 'Raise an error'],
      answer: 1,
      why: 'At-least-once delivery repeats events. Anything at or below the last seq is old news.',
    },
  ],
  '06': [
    {
      q: 'When should preferences be checked?',
      options: ['When the message is queued', 'When the message is sent', 'Once a day'],
      answer: 1,
      why: 'A user can change them between queueing and sending. The send is what they consented to.',
    },
    {
      q: 'Which notice should a user be unable to turn off?',
      options: ['The weekly summary', 'A new sign-in to their account', 'Release notes'],
      answer: 1,
      why: 'Security notices protect the account itself. Keep the required list short and honest.',
    },
  ],
  '07': [
    {
      q: 'Quiet hours are 22:00 to 07:00. Which clock decides?',
      options: ["The server's, in UTC", "The user's wall clock", 'The provider’s'],
      answer: 1,
      why: 'Convert the instant to the user’s time zone before comparing it with their window.',
    },
    {
      q: 'What should you store for each user?',
      options: ['A UTC offset like +05:30', 'An IANA zone name like Asia/Kolkata', 'Their country'],
      answer: 1,
      why: 'Offsets change with daylight saving time. A zone name carries the rules.',
    },
  ],
  '08': [
    {
      q: 'Why does a pure debounce starve a busy user?',
      options: [
        'It sends too often',
        'It waits for a quiet gap that never comes',
        'It drops updates',
      ],
      answer: 1,
      why: 'Every update resets the timer. With steady traffic, the digest never goes out.',
    },
    {
      q: 'The maximum wait should count from...',
      options: ['The latest update', 'The first update in the digest', 'Midnight'],
      answer: 1,
      why: 'A cap counted from the latest update moves with every update, so it is no cap at all.',
    },
  ],
  '09': [
    {
      q: 'A code is queued behind 6,000 bulk messages at 50 a second. What fixes it?',
      options: [
        'A bigger queue',
        'A separate lane served first',
        'Sending bulk faster than the limit',
      ],
      answer: 1,
      why: 'The limit is fixed. The order is not: urgent messages go first, bulk takes what is left.',
    },
    {
      q: 'What is head-of-line blocking?',
      options: [
        'A message waiting for everything ahead of it in one queue',
        'A crashed worker',
        'A full disk',
      ],
      answer: 0,
      why: 'In a single FIFO queue, one big batch at the front delays everything behind it.',
    },
  ],
  '10': [
    {
      q: 'A captured webhook is sent again a day later. Its signature...',
      options: ['Fails', 'Still verifies', 'Expires automatically'],
      answer: 1,
      why: 'A signature proves origin, not freshness. Check the signed timestamp and the webhook id.',
    },
    {
      q: 'A webhook id you already handled arrives again. What do you answer?',
      options: ['200, and do nothing', '409, so the provider knows', '500'],
      answer: 0,
      why: 'It is usually the provider retrying. Acknowledge it so it stops, and do not act twice.',
    },
  ],
}
