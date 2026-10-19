import type { Metadata } from 'next'

import { ChapterList } from '@/components/ChapterList'
import { CHAPTERS } from '@/lib/workshop'

export const metadata: Metadata = { title: 'Chapters' }

export default function Workshop() {
  const minutes = CHAPTERS.reduce((sum, chapter) => sum + chapter.minutes, 0)
  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-14 px-4 pt-16 pb-24">
      <header className="flex max-w-3xl flex-col gap-4">
        <span className="eyebrow">
          {CHAPTERS.length} chapters · {minutes} minutes
        </span>
        <h1 className="font-display text-[3.4rem] leading-[1] tracking-[-0.03em] sm:text-[4.4rem]">
          The <em className="text-gradient italic">chapters</em>
        </h1>
        <p className="text-[18px] leading-relaxed text-ink-2">
          Work through them in order. Each chapter explains an idea, hands you a case that gets it
          wrong, and ends with a check that the message still arrives once the bug is gone.
        </p>
      </header>
      <ChapterList />
    </div>
  )
}
