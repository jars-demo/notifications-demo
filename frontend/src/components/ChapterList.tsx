import Link from 'next/link'

import { Inline } from '@/components/Inline'
import { LEVELS, SYMPTOMS } from '@/lib/site'
import { CHAPTERS } from '@/lib/workshop'

// The ten chapters in three parts, each with the real symptom of its bug.

export function ChapterList() {
  return (
    <div className="flex flex-col gap-14">
      {LEVELS.map((level, index) => {
        const chapters = CHAPTERS.filter((chapter) =>
          level.chapters.includes(Number(chapter.number)),
        )
        const minutes = chapters.reduce((sum, chapter) => sum + chapter.minutes, 0)
        return (
          <section
            key={level.name}
            aria-labelledby={`part-${index}`}
            className="flex flex-col gap-5"
          >
            <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
              <h3
                id={`part-${index}`}
                className="font-display text-[30px] leading-tight tracking-[-0.02em]"
              >
                <span className="mr-3 font-sans text-[13px] tracking-[0.18em] text-muted uppercase">
                  Part {index + 1}
                </span>
                <em className="italic">{level.name}</em>
              </h3>
              <p className="text-[14px] text-muted">
                {chapters.length} chapters, {minutes} minutes
              </p>
            </div>
            <p className="max-w-2xl text-[15.5px] text-ink-2">{level.about}</p>
            <ol className="grid gap-4 md:grid-cols-2">
              {chapters.map((chapter) => (
                <li key={chapter.slug}>
                  <Link
                    href={`/workshop/${chapter.slug}`}
                    className="card lift flex h-full flex-col gap-3 p-5 sm:p-6"
                  >
                    <div className="flex items-baseline justify-between gap-3">
                      <span className="font-mono text-[13px] text-accent-text">
                        {chapter.number}
                      </span>
                      <span className="text-[13px] text-muted">{chapter.minutes} min</span>
                    </div>
                    <h4 className="font-display text-[26px] leading-tight tracking-[-0.015em] text-ink">
                      {chapter.title}
                    </h4>
                    <p className="text-[14.5px] leading-relaxed text-ink-2">
                      <Inline text={chapter.summary} />
                    </p>
                    <code className="mt-auto block rounded-xl bg-code-bg px-3.5 py-2.5 font-mono text-[12.5px] leading-relaxed whitespace-pre-wrap text-code-bad [overflow-wrap:anywhere]">
                      {SYMPTOMS[chapter.number]}
                    </code>
                  </Link>
                </li>
              ))}
            </ol>
          </section>
        )
      })}
    </div>
  )
}
