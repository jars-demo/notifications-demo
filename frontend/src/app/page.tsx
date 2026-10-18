import Link from 'next/link'

import { ChapterList } from '@/components/ChapterList'
import { CopyButton } from '@/components/CopyButton'
import { DigestBoard } from '@/components/DigestBoard'
import { Pip } from '@/components/Pip'
import {
  CASE_TWO,
  CHECKLIST,
  LEARN,
  MEASURED,
  PIPELINE,
  QUICKSTART,
  REPO_URL,
  TITLE,
} from '@/lib/site'
import { CHAPTERS } from '@/lib/workshop'

function SectionHead({
  id,
  eyebrow,
  title,
  children,
}: {
  id: string
  eyebrow: string
  title: string
  children?: React.ReactNode
}) {
  return (
    <div className="flex max-w-2xl flex-col gap-3">
      <span className="label">{eyebrow}</span>
      <h2 id={id} className="display text-[30px] leading-[1.08] text-ink sm:text-[40px]">
        {title}
      </h2>
      {children ? <p className="text-[17px] leading-relaxed text-ink-2">{children}</p> : null}
    </div>
  )
}

function hours(minutes: number): string {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return m ? `${h} h ${m} min` : `${h} hours`
}

export default function Home() {
  const minutes = CHAPTERS.reduce((sum, chapter) => sum + chapter.minutes, 0)
  return (
    <>
      <section className="border-b border-rule-strong">
        <div className="mx-auto grid max-w-6xl gap-12 px-4 pt-12 pb-16 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)] lg:items-center lg:gap-16 lg:pt-20 lg:pb-24">
          <div className="flex min-w-0 flex-col gap-6">
            <span className="tag self-start">
              Workshop · {CHAPTERS.length} chapters · {hours(minutes)}
            </span>
            <h1 className="display text-[44px] leading-[0.98] text-balance text-ink sm:text-[68px]">
              {TITLE}.
            </h1>
            <p className="max-w-xl text-[19px] leading-relaxed text-ink-2 sm:text-[21px]">
              A notification has one job: reach the right person, once, in the right order, at a
              good time. Learn every way that goes wrong, one real bug at a time, in one small
              parcel company called Dovecote.
            </p>
            <div className="flex flex-wrap gap-3 pt-1">
              <Link
                href={`/workshop/${CHAPTERS[0]?.slug ?? ''}`}
                className="inline-flex h-12 items-center bg-ink px-6 text-[15.5px] font-semibold text-surface hover:bg-night-2"
              >
                Start chapter 01
              </Link>
              <a
                href={REPO_URL}
                className="inline-flex h-12 items-center border-[1.5px] border-ink px-6 text-[15.5px] font-semibold text-ink hover:bg-surface"
              >
                Read the source
              </a>
            </div>
            <dl className="mt-3 grid max-w-lg grid-cols-3 gap-5 border-t-[3px] border-ink pt-5">
              {[
                ['8', 'real bugs to fix'],
                ['0', 'dependencies in the lab'],
                ['4', 'experiments you can run'],
              ].map(([value, label]) => (
                <div key={label} className="flex flex-col gap-1.5">
                  <dt className="sr-only">{label}</dt>
                  <dd className="display text-[34px] leading-none">{value}</dd>
                  <dd className="text-[13.5px] leading-snug text-ink-2">{label}</dd>
                </div>
              ))}
            </dl>
          </div>
          <figure className="slip min-w-0">
            <figcaption className="flex items-center justify-between gap-3 border-b-[1.5px] border-ink px-4 py-3">
              <span className="label text-ink">Route of one notification</span>
              <span className="font-mono text-[12px] text-muted">DC-1043</span>
            </figcaption>
            <ol>
              {PIPELINE.map((stage, index) => (
                <li
                  key={stage.step}
                  className="grid grid-cols-[2.25rem_minmax(0,1fr)_auto] items-start gap-3 border-b border-rule px-4 py-3.5 last:border-0"
                >
                  <span className="grid size-8 place-items-center border-[1.5px] border-ink font-mono text-[13px] font-bold">
                    {index + 1}
                  </span>
                  <span className="flex min-w-0 flex-col gap-0.5">
                    <span className="text-[16px] font-bold text-ink">{stage.step}</span>
                    <span className="text-[14px] leading-snug text-ink-2">{stage.detail}</span>
                  </span>
                  <span className="flex flex-wrap justify-end gap-1 pt-0.5">
                    {stage.chapters.map((number) => {
                      const chapter = CHAPTERS.find((c) => c.number === number)
                      return chapter ? (
                        <Link
                          key={number}
                          href={`/workshop/${chapter.slug}`}
                          aria-label={`Chapter ${number}: ${chapter.title}`}
                          className="grid h-10 min-w-10 place-items-center bg-surface-2 px-1.5 font-mono text-[12.5px] font-semibold text-ink hover:bg-signal"
                        >
                          {number}
                        </Link>
                      ) : null
                    })}
                  </span>
                </li>
              ))}
            </ol>
          </figure>
        </div>
      </section>

      <section aria-labelledby="learn" className="mx-auto flex max-w-6xl flex-col gap-8 px-4 pt-20">
        <SectionHead
          id="learn"
          eyebrow="What you will learn"
          title="Arrive once, in order, on time"
        >
          Each idea comes with the bug it prevents, so you will recognise it in your own code.
        </SectionHead>
        <ul className="grid gap-x-12 md:grid-cols-2">
          {LEARN.map((item) => (
            <li
              key={item}
              className="flex gap-3 border-t border-rule-strong py-4 text-[16px] leading-relaxed text-ink"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 14 14"
                aria-hidden="true"
                className="mt-1 shrink-0"
              >
                <path d="M2.5 7.5l3 3 6-7" fill="none" stroke="currentColor" strokeWidth="2.2" />
              </svg>
              {item}
            </li>
          ))}
        </ul>
      </section>

      <section
        aria-labelledby="chapters"
        className="mx-auto flex max-w-6xl flex-col gap-8 px-4 pt-20"
      >
        <SectionHead id="chapters" eyebrow="The manifest" title="Eight chapters, eight bugs">
          Each chapter explains one idea in depth, then hands you a program that gets it wrong. You
          fix it, and the checker proves the fix: the bug is gone, and the message still arrives.
        </SectionHead>
        <ChapterList />
      </section>

      <section
        id="board"
        aria-labelledby="board-title"
        className="mx-auto grid max-w-6xl scroll-mt-6 gap-10 px-4 pt-24 lg:grid-cols-[minmax(0,21rem)_minmax(0,1fr)] lg:gap-14 [&>*]:min-w-0"
      >
        <div className="flex flex-col gap-5">
          <SectionHead id="board-title" eyebrow="Try it" title="The digest board">
            Three hours of parcel scans for one customer, and the pushes a batching rule makes from
            them. Each green mark is a buzz. Each blue bar is how long an update waited.
          </SectionHead>
          <ol className="flex flex-col gap-3 text-[15.5px] leading-relaxed text-ink-2">
            <li>
              <strong className="font-mono text-ink">1.</strong> With the busy shop and Debounce 10,
              there is one push, after more than three hours. Updates never stop, so the timer never
              fires.
            </li>
            <li>
              <strong className="font-mono text-ink">2.</strong> Choose Debounce, cap 30. Six
              pushes, and nobody waits more than thirty minutes.
            </li>
            <li>
              <strong className="font-mono text-ink">3.</strong> Clear the board and tap your own
              pattern. Then fix the same bug in Python in{' '}
              <Link
                href="/workshop/06-digests"
                className="font-semibold text-ink underline decoration-signal decoration-[3px] underline-offset-3"
              >
                chapter 06
              </Link>
              .
            </li>
          </ol>
        </div>
        <DigestBoard />
      </section>

      <section
        aria-labelledby="method"
        className="mx-auto flex max-w-6xl flex-col gap-8 px-4 pt-24"
      >
        <SectionHead id="method" eyebrow="How a case works" title="Run it, fix it, prove it">
          Every case is a short Python program with one bug in it, and nothing to install but uv.
          Here is case 02 from start to finish.
        </SectionHead>
        <ol className="grid gap-4 lg:grid-cols-3 [&>*]:min-w-0">
          {[
            {
              step: 'Run it',
              command: 'uv run python -m dove run 2',
              lines: CASE_TWO.run,
              tone: 'text-code-lost',
              note: 'Two timeouts and a redelivery: four texts for one parcel.',
            },
            {
              step: 'Fix it',
              command: 'lab/cases/case02_idempotency.py',
              lines: CASE_TWO.fix,
              tone: 'text-code-ink',
              note: 'One key per event, made once, before the retry loop.',
            },
            {
              step: 'Prove it',
              command: 'uv run python -m dove check 2',
              lines: CASE_TWO.check,
              tone: 'text-code-sent',
              note: 'One text each, and Ben still gets his after a refused try.',
            },
          ].map((card, index) => (
            <li key={card.step} className="flex flex-col gap-3">
              <div className="flex items-baseline gap-3">
                <span className="display text-[28px] leading-none">{index + 1}</span>
                <span className="text-[17px] font-bold text-ink">{card.step}</span>
              </div>
              <div className="code flex flex-1 flex-col overflow-hidden">
                <div className="truncate border-b border-code-rule px-3.5 py-2 text-[12px] text-code-muted">
                  {card.command}
                </div>
                <pre
                  className={`px-3.5 py-3 text-[12.5px] leading-relaxed whitespace-pre-wrap [overflow-wrap:anywhere] ${card.tone}`}
                >
                  {card.lines.join('\n')}
                </pre>
              </div>
              <p className="text-[14.5px] text-ink-2">{card.note}</p>
            </li>
          ))}
        </ol>
      </section>

      <section
        aria-labelledby="measured"
        className="mx-auto flex max-w-6xl flex-col gap-8 px-4 pt-24"
      >
        <SectionHead id="measured" eyebrow="Measured, not guessed" title="Retry storms need jitter">
          A thousand phones fail together when the gateway goes down for thirty seconds. Without
          jitter they come back together, in waves of a thousand.
        </SectionHead>
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)] [&>*]:min-w-0">
          <figure className="panel overflow-hidden">
            <figcaption className="flex flex-wrap items-baseline justify-between gap-2 border-b border-rule-strong bg-surface-2 px-4 py-3">
              <span className="text-[16px] font-bold text-ink">Retrying through an outage</span>
              <span className="font-mono text-[12px] text-muted">dove try backoff</span>
            </figcaption>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[30rem] text-[14.5px]">
                <thead>
                  <tr className="border-b border-rule-strong text-left font-mono text-[11.5px] tracking-[0.08em] text-ink uppercase">
                    <th scope="col" className="px-4 py-2.5 font-semibold">
                      Strategy
                    </th>
                    {MEASURED.backoff.headers.map((header) => (
                      <th key={header} scope="col" className="px-3 py-2.5 text-right font-semibold">
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {MEASURED.backoff.rows.map((row) => (
                    <tr key={row.label} className="border-b border-rule last:border-0">
                      <th scope="row" className="px-4 py-2.5 text-left font-medium text-ink">
                        {row.label}
                      </th>
                      {row.values.map((value, index) => (
                        <td
                          key={MEASURED.backoff.headers[index]}
                          className={`px-3 py-2.5 text-right font-mono text-[13.5px] ${
                            index === 1
                              ? `font-semibold ${row.verdict === 'sent' ? 'text-sent' : 'text-lost'}`
                              : 'text-ink-2'
                          }`}
                        >
                          {index === 1 ? (
                            <span className="inline-flex items-center gap-1.5">
                              <span className="sr-only">
                                {row.verdict === 'sent' ? 'spread out:' : 'a wave:'}
                              </span>
                              <svg width="11" height="11" viewBox="0 0 14 14" aria-hidden="true">
                                {row.verdict === 'sent' ? (
                                  <path
                                    d="M2.5 7.5l3 3 6-7"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="2.4"
                                  />
                                ) : (
                                  <path
                                    d="M3 3l8 8M11 3l-8 8"
                                    stroke="currentColor"
                                    strokeWidth="2.4"
                                  />
                                )}
                              </svg>
                              {value}
                            </span>
                          ) : (
                            value
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </figure>
          <figure className="panel overflow-hidden">
            <figcaption className="flex flex-wrap items-baseline justify-between gap-2 border-b border-rule-strong bg-surface-2 px-4 py-3">
              <span className="text-[16px] font-bold text-ink">2,000 pushes, local HTTP</span>
              <span className="font-mono text-[12px] text-muted">dove try fanout</span>
            </figcaption>
            <ul>
              {MEASURED.fanout.map((row) => (
                <li
                  key={row.label}
                  className="flex items-baseline justify-between gap-3 border-b border-rule px-4 py-2.5 last:border-0"
                >
                  <span className="min-w-0 text-[14.5px] text-ink">{row.label}</span>
                  <span className="shrink-0 font-mono text-[13.5px] text-ink-2">
                    {row.pushesPerSecond}/s
                  </span>
                </li>
              ))}
            </ul>
          </figure>
        </div>
        <p className="max-w-2xl text-[14.5px] leading-relaxed text-muted">
          The backoff table is simulated with a fixed seed, so you will see these exact numbers. The
          fanout timings were measured on {MEASURED.machine}. Chapters 04 and 07 explain each one.
        </p>
      </section>

      <section
        aria-labelledby="checklist"
        className="mx-auto flex max-w-6xl flex-col gap-8 px-4 pt-24"
      >
        <SectionHead id="checklist" eyebrow="Keep this" title="The notifications checklist">
          Ten rules, one for every way a message went wrong in the workshop.
        </SectionHead>
        <ol className="grid gap-x-12 md:grid-cols-2">
          {CHECKLIST.map((item, index) => (
            <li
              key={item}
              className="flex gap-4 border-t border-rule-strong py-4 text-[16px] leading-relaxed text-ink"
            >
              <span className="w-7 shrink-0 font-mono text-[15px] leading-7 font-bold">
                {String(index + 1).padStart(2, '0')}
              </span>
              {item}
            </li>
          ))}
        </ol>
      </section>

      <section
        aria-labelledby="start"
        className="mx-auto grid max-w-6xl gap-10 px-4 pt-24 pb-28 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:items-center [&>*]:min-w-0"
      >
        <div className="flex flex-col gap-6">
          <SectionHead id="start" eyebrow="Quick start" title="Your first bug in five minutes">
            You need uv and git. uv installs Python for you, and the lab uses the standard library
            only.
          </SectionHead>
          <div className="code overflow-hidden">
            <div className="flex items-center justify-between border-b border-code-rule py-1 pr-1 pl-4">
              <span className="text-[11.5px] font-semibold tracking-[0.1em] text-code-muted uppercase">
                Shell
              </span>
              <CopyButton text={QUICKSTART} />
            </div>
            <pre className="overflow-x-auto px-4 py-3.5 text-[13px] leading-relaxed">
              {QUICKSTART}
            </pre>
          </div>
        </div>
        <figure className="flex flex-col items-center gap-4 sm:flex-row sm:items-end lg:justify-center">
          <Pip className="w-44 shrink-0 sm:w-52" />
          <figcaption className="slip relative max-w-xs p-4 text-[16px] leading-relaxed text-ink">
            <span className="label mb-1 block text-ink">Pip</span>
            Stuck on a case? Ask me in the corner of any page, or run{' '}
            <code className="bg-surface-2 px-1 font-mono text-[13px]">dove hint 1</code>. I have
            never lost a letter. I have delivered a few twice.
          </figcaption>
        </figure>
      </section>
    </>
  )
}
