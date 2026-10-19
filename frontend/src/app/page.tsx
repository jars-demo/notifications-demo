import Link from 'next/link'

import { ChapterList } from '@/components/ChapterList'
import { CopyButton } from '@/components/CopyButton'
import { StormChart } from '@/components/StormChart'
import { MEASURED, QUICKSTART, REPO_URL } from '@/lib/site'
import { CHAPTERS } from '@/lib/workshop'

const hours = (minutes: number) => `${Math.floor(minutes / 60)} h ${minutes % 60} min`

const STEPS = [
  { title: 'Event', body: 'A payment clears, someone is invited, a build fails.', chapters: '01' },
  {
    title: 'Decide',
    body: 'Who hears about it, on which channel, and is now a good time?',
    chapters: '05 to 07',
  },
  {
    title: 'Render',
    body: 'Turn the event into a subject, a body, a push payload.',
    chapters: '08',
  },
  {
    title: 'Deliver',
    body: 'Hand it to an email API, an SMS gateway, a push service.',
    chapters: '02 to 04, 09',
  },
  {
    title: 'Learn',
    body: 'The provider reports back: delivered, bounced, failed.',
    chapters: '10',
  },
]

export default function Home() {
  const minutes = CHAPTERS.reduce((sum, chapter) => sum + chapter.minutes, 0)
  return (
    <>
      <section className="mx-auto flex max-w-4xl flex-col items-center px-4 pt-16 pb-20 text-center sm:pt-24">
        <span className="rise eyebrow">
          A hands-on workshop · {CHAPTERS.length} chapters · {hours(minutes)}
        </span>
        <h1
          className="rise mt-6 font-display text-[3.2rem] leading-[0.98] tracking-[-0.03em] text-balance sm:text-[5.2rem]"
          style={{ '--delay': '80ms' } as React.CSSProperties}
        >
          Notifications that arrive{' '}
          <em className="text-gradient italic">once, in order, on time.</em>
        </h1>
        <p
          className="rise mt-6 max-w-xl text-[18px] leading-relaxed text-pretty text-ink-2"
          style={{ '--delay': '160ms' } as React.CSSProperties}
        >
          Ten chapters on the engineering behind every email, push and SMS a product sends: the
          outbox, idempotency, retries, ordering, consent, time zones, batching, priority and
          webhooks. Each one has a real bug in a small notification service for you to fix.
        </p>
        <div
          className="rise mt-9 flex flex-wrap justify-center gap-3"
          style={{ '--delay': '240ms' } as React.CSSProperties}
        >
          <Link
            href={`/workshop/${CHAPTERS[0]?.slug}`}
            className="inline-flex h-12 items-center rounded-full bg-ink px-6 text-[16px] font-medium text-canvas hover:bg-ink-2"
          >
            Start chapter 01
          </Link>
          <a
            href={REPO_URL}
            className="glass inline-flex h-12 items-center rounded-full px-6 text-[16px] font-medium text-ink"
          >
            Get the lab on GitHub
          </a>
        </div>
      </section>

      <section aria-labelledby="steps" className="mx-auto max-w-5xl px-4 pb-24">
        <h2
          id="steps"
          className="mb-10 text-center font-display text-[2.6rem] leading-tight tracking-[-0.025em] sm:text-5xl"
        >
          Every notification takes <em className="text-gradient italic">five steps.</em>
        </h2>
        <ol className="grid gap-3 sm:grid-cols-5">
          {STEPS.map((step, index) => (
            <li key={step.title} className="card flex flex-col gap-2 p-5">
              <span className="font-mono text-[12px] text-accent-text">0{index + 1}</span>
              <h3 className="font-display text-[26px] leading-none italic">{step.title}</h3>
              <p className="text-[14px] leading-relaxed text-ink-2">{step.body}</p>
              <p className="mt-auto pt-2 text-[12.5px] text-muted">Chapters {step.chapters}</p>
            </li>
          ))}
        </ol>
        <p className="mt-4 text-center text-[14px] text-muted">
          Each step fails in its own ways. The workshop takes them one at a time.
        </p>
      </section>

      <section aria-labelledby="chapters" className="mx-auto max-w-5xl px-4 pb-24">
        <div className="mb-12 flex max-w-3xl flex-col gap-3">
          <h2
            id="chapters"
            className="font-display text-[2.6rem] leading-tight tracking-[-0.025em] sm:text-5xl"
          >
            Ten bugs, <em className="text-gradient italic">ten fixes.</em>
          </h2>
          <p className="text-[17px] leading-relaxed text-ink-2">
            Each chapter explains one idea in depth, then hands you a piece of a notification
            service that gets it wrong the way real systems do. The dark line on each card is what
            it prints before you fix it. A checker proves your fix, and rejects the fixes that only
            hide the symptom.
          </p>
        </div>
        <ChapterList />
      </section>

      <section
        aria-labelledby="storm"
        className="mx-auto grid max-w-5xl gap-10 px-4 pb-24 lg:grid-cols-[1fr_1.4fr] lg:items-center"
      >
        <div className="flex flex-col gap-4">
          <span className="eyebrow">Chapter 04, from the lab</span>
          <h2 id="storm" className="font-display text-[2.6rem] leading-tight tracking-[-0.025em]">
            The retry storm, <em className="text-gradient italic">second by second.</em>
          </h2>
          <p className="text-[17px] leading-relaxed text-ink-2">
            A thousand sends fail during a 30 second outage, and every sender backs off by the
            textbook: 1, 2, 4 seconds and up. They all back off together, so they all come back
            together, ten times over capacity.
          </p>
          <p className="text-[17px] leading-relaxed text-ink-2">
            Switch on full jitter: the same backoff, with a random wait inside each window.
          </p>
        </div>
        <div className="min-w-0">
          <StormChart />
        </div>
      </section>

      <section aria-labelledby="measured" className="mx-auto max-w-5xl px-4 pb-24">
        <div className="mb-8 flex max-w-3xl flex-col gap-3">
          <h2
            id="measured"
            className="font-display text-[2.6rem] leading-tight tracking-[-0.025em]"
          >
            Measured, <em className="text-gradient italic">not quoted.</em>
          </h2>
          <p className="text-[17px] leading-relaxed text-ink-2">
            <code className="font-mono text-[15px]">uv run python -m notify try</code> runs the
            experiments on your machine. These are the numbers from the machine the workshop was
            written on.
          </p>
        </div>
        <div className="grid gap-4 lg:grid-cols-[1fr_1.4fr]">
          <div className="card overflow-x-auto p-5">
            <h3 className="mb-3 text-[15px] font-semibold">
              What an outbox row costs, per payment
            </h3>
            <table className="w-full text-[14px]">
              <tbody>
                {MEASURED.outbox.map((row) => (
                  <tr key={row.label} className="border-t border-hairline">
                    <td className="py-2.5 pr-3 text-ink-2">{row.label}</td>
                    <td className="py-2.5 text-right font-mono whitespace-nowrap">{row.value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-3 text-[13px] text-muted">
              SQLite, WAL, synchronous FULL. The commit is the expensive part.
            </p>
          </div>
          <div className="card overflow-x-auto p-5">
            <h3 className="mb-3 text-[15px] font-semibold">
              1,000 senders retry through a 30 s outage
            </h3>
            <table className="w-full min-w-[460px] text-[14px]">
              <thead>
                <tr className="text-left text-[12.5px] text-muted">
                  <th className="pb-2 font-medium">strategy</th>
                  <th className="pb-2 text-right font-medium">requests</th>
                  <th className="pb-2 text-right font-medium">busiest second</th>
                  <th className="pb-2 text-right font-medium">all sent by</th>
                </tr>
              </thead>
              <tbody>
                {MEASURED.backoff.map((row) => (
                  <tr key={row.strategy} className="border-t border-hairline">
                    <td className="py-2.5 pr-3 text-ink-2">{row.strategy}</td>
                    <td className="py-2.5 text-right font-mono">{row.requests}</td>
                    <td className="py-2.5 text-right font-mono">{row.peak}</td>
                    <td className="py-2.5 text-right font-mono whitespace-nowrap">{row.done}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-4 pb-16">
        <div className="grid gap-8 rounded-panel bg-ink p-8 text-canvas sm:p-12 lg:grid-cols-2 lg:items-center">
          <div className="flex flex-col gap-4">
            <h2 className="font-display text-[2.6rem] leading-tight tracking-[-0.025em]">
              Start in <em className="italic">two minutes.</em>
            </h2>
            <p className="text-[16px] leading-relaxed text-canvas/80">
              You need uv and git. uv installs Python for you, and the lab uses only Python&apos;s
              standard library: the email provider and the webhooks run on localhost.
            </p>
          </div>
          <div className="terminal min-w-0 overflow-hidden">
            <div className="flex items-center justify-between bg-code-head py-1 pr-1 pl-4 font-mono text-[12px] tracking-[0.06em] text-code-muted uppercase">
              <span>shell</span>
              <CopyButton text={QUICKSTART} label="Copy the quick start" />
            </div>
            <pre className="overflow-x-auto p-4 text-[14px] leading-relaxed">{QUICKSTART}</pre>
          </div>
        </div>
      </section>
    </>
  )
}
