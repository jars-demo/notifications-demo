import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'

import { LostIcon } from '@/components/ChapterList'
import { CopyButton } from '@/components/CopyButton'
import { headingsOf, Markdown } from '@/components/Markdown'
import { CASES } from '@/lib/site'
import { type Chapter, CHAPTERS, findChapter } from '@/lib/workshop'

export function generateStaticParams() {
  return CHAPTERS.map((chapter) => ({ slug: chapter.slug }))
}

export async function generateMetadata(props: PageProps<'/workshop/[slug]'>): Promise<Metadata> {
  const { slug } = await props.params
  const chapter = findChapter(slug)
  return {
    title: chapter ? `${chapter.number}. ${chapter.title}` : 'Chapter',
    description: chapter?.summary,
  }
}

function Outline({ chapter }: { chapter: Chapter }) {
  return (
    <ul className="flex flex-col text-[14px]">
      {headingsOf(chapter.body).map((heading) => (
        <li key={heading.id}>
          <a
            href={`#${heading.id}`}
            className="flex min-h-10 items-center text-ink-2 hover:text-ink hover:underline"
          >
            {heading.text}
          </a>
        </li>
      ))}
    </ul>
  )
}

function Chapters({ current }: { current: Chapter }) {
  return (
    <ol className="flex flex-col text-[14px]">
      {CHAPTERS.map((chapter) => {
        const here = chapter.slug === current.slug
        return (
          <li key={chapter.slug}>
            <Link
              href={`/workshop/${chapter.slug}`}
              aria-current={here ? 'page' : undefined}
              className={`flex min-h-10 items-center gap-2.5 px-2 ${
                here ? 'bg-signal font-semibold text-ink' : 'text-ink-2 hover:text-ink'
              }`}
            >
              <span className="w-5 shrink-0 font-mono text-[12.5px]">{chapter.number}</span>
              {chapter.title}
            </Link>
          </li>
        )
      })}
    </ol>
  )
}

export default async function ChapterPage(props: PageProps<'/workshop/[slug]'>) {
  const { slug } = await props.params
  const chapter = findChapter(slug)
  if (!chapter) notFound()
  const index = CHAPTERS.indexOf(chapter)
  const previous = CHAPTERS[index - 1]
  const next = CHAPTERS[index + 1]
  const item = CASES.find((c) => c.number === chapter.number)
  const n = Number(chapter.number)
  const commands = `uv run python -m dove run ${n}\nuv run python -m dove check ${n}\nuv run python -m dove hint ${n}`

  return (
    <div className="mx-auto max-w-6xl px-4 pt-8 pb-24">
      <nav aria-label="Breadcrumb" className="text-[14px] text-muted">
        <Link
          href="/workshop"
          className="inline-flex min-h-10 items-center hover:text-ink hover:underline"
        >
          Chapters
        </Link>
        <span aria-hidden="true"> / </span>
        <span className="font-mono text-ink-2">{chapter.number}</span>
      </nav>

      <header className="mt-4 grid gap-8 lg:grid-cols-[minmax(0,1fr)_21rem] lg:gap-14">
        <div className="flex min-w-0 flex-col gap-4">
          <span className="tag self-start">
            Chapter {chapter.number} · {chapter.minutes} minutes
          </span>
          <h1 className="display text-[38px] leading-[1.02] text-balance sm:text-[54px]">
            {chapter.title}
          </h1>
          <p className="max-w-2xl text-[19px] leading-relaxed text-ink-2">{chapter.summary}</p>
        </div>
        {item ? (
          <aside aria-label={`Case ${chapter.number}`} className="slip min-w-0 self-end">
            <div className="flex items-baseline justify-between gap-3 border-b-[1.5px] border-ink px-4 py-2.5">
              <span className="label text-ink">Case {chapter.number}</span>
              <span className="text-[12.5px] text-muted">what you will see</span>
            </div>
            <div className="flex flex-col gap-3 p-4">
              <p className="text-[17px] leading-snug font-bold text-ink">{item.title}</p>
              <p className="flex items-start gap-2 bg-lost-wash px-3 py-2 font-mono text-[12.5px] leading-relaxed text-lost">
                <span className="mt-[4px]">
                  <LostIcon />
                </span>
                <span className="min-w-0 whitespace-pre-wrap [overflow-wrap:anywhere]">
                  <span className="sr-only">The symptom: </span>
                  {item.symptom}
                </span>
              </p>
            </div>
          </aside>
        ) : null}
      </header>

      <div className="mt-12 grid gap-10 lg:grid-cols-[minmax(0,1fr)_14rem] lg:gap-14">
        <article className="min-w-0">
          <details className="panel lg:hidden">
            <summary className="flex min-h-11 cursor-pointer items-center px-4 text-[14.5px] font-semibold">
              On this page
            </summary>
            <div className="border-t border-rule px-4 py-2">
              <Outline chapter={chapter} />
            </div>
          </details>

          <div className="prose-post max-w-[44rem]">
            <Markdown>{chapter.body}</Markdown>
          </div>

          <section
            aria-labelledby="commands"
            className="code mt-14 max-w-[44rem] overflow-hidden border-l-4 border-signal"
          >
            <div className="flex items-center justify-between border-b border-code-rule py-1 pr-1 pl-4">
              <h2
                id="commands"
                className="text-[11.5px] font-semibold tracking-[0.1em] text-code-muted uppercase"
              >
                Chapter {chapter.number} · from lab/
              </h2>
              <CopyButton text={commands} />
            </div>
            <pre className="overflow-x-auto px-4 py-4 text-[13px] leading-relaxed">{commands}</pre>
          </section>

          <nav
            aria-label="Previous and next"
            className="mt-8 grid max-w-[44rem] gap-3 sm:grid-cols-2"
          >
            {previous ? (
              <Link
                href={`/workshop/${previous.slug}`}
                className="panel flex flex-col gap-1 p-4 hover:border-ink"
              >
                <span className="label">Previous</span>
                <span className="text-[17px] font-bold">
                  {previous.number}. {previous.title}
                </span>
              </Link>
            ) : (
              <span />
            )}
            {next ? (
              <Link
                href={`/workshop/${next.slug}`}
                className="panel flex flex-col gap-1 p-4 text-right hover:border-ink"
              >
                <span className="label">Next</span>
                <span className="text-[17px] font-bold">
                  {next.number}. {next.title}
                </span>
              </Link>
            ) : (
              <Link
                href="/#checklist"
                className="panel flex flex-col gap-1 p-4 text-right hover:border-ink"
              >
                <span className="label">All eight fixed</span>
                <span className="text-[17px] font-bold">The notifications checklist</span>
              </Link>
            )}
          </nav>
        </article>

        <aside className="hidden lg:block">
          <div className="sticky top-6 flex flex-col gap-8">
            <nav aria-label="On this page" className="flex flex-col gap-2">
              <span className="label">On this page</span>
              <Outline chapter={chapter} />
            </nav>
            <nav aria-label="Chapters" className="flex flex-col gap-2">
              <span className="label">Chapters</span>
              <Chapters current={chapter} />
            </nav>
          </div>
        </aside>
      </div>
    </div>
  )
}
