import Link from 'next/link'

import { CASES } from '@/lib/site'
import { CHAPTERS } from '@/lib/workshop'

// The chapters as a delivery manifest: one row per chapter, with the bug you will meet in it.

export function LostIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true" className="shrink-0">
      <path d="M2.5 2.5l7 7M9.5 2.5l-7 7" stroke="currentColor" strokeWidth="2" />
    </svg>
  )
}

export function ChapterList() {
  return (
    <ol className="border-t-[3px] border-ink">
      {CHAPTERS.map((chapter) => {
        const item = CASES.find((c) => c.number === chapter.number)
        return (
          <li key={chapter.slug} className="border-b border-rule-strong">
            <Link
              href={`/workshop/${chapter.slug}`}
              className="group grid gap-x-6 gap-y-2 py-5 hover:bg-surface sm:grid-cols-[4.5rem_minmax(0,1fr)_auto] sm:px-2"
            >
              <span className="font-mono text-[15px] font-bold text-ink sm:pt-1">
                {chapter.number}
              </span>
              <span className="flex min-w-0 flex-col gap-1.5">
                <span className="display text-[21px] leading-tight text-ink group-hover:underline group-hover:decoration-signal group-hover:decoration-[3px] group-hover:underline-offset-4 sm:text-[24px]">
                  {chapter.title}
                </span>
                {item ? (
                  <span className="text-[15.5px] leading-snug text-ink-2">{item.topics}</span>
                ) : null}
                {item ? (
                  <span className="mt-1 flex items-start gap-2 font-mono text-[12.5px] leading-snug text-lost">
                    <span className="mt-[3px]">
                      <LostIcon />
                    </span>
                    <span>
                      <span className="sr-only">The bug: </span>
                      {item.title}
                    </span>
                  </span>
                ) : null}
              </span>
              <span className="label sm:pt-1.5">{chapter.minutes} min</span>
            </Link>
          </li>
        )
      })}
    </ol>
  )
}
