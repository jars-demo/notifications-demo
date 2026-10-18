import fs from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { headingsOf, slugify } from '@/components/Markdown'
import { NOTE_SLUGS, notesFor } from '@/lib/pip'
import { CASE_TWO, CASES, CHECKLIST, MEASURED, PIPELINE } from '@/lib/site'
import { CHAPTERS, findChapter } from '@/lib/workshop'

const ROOT = path.join(process.cwd(), '..')
const read = (file: string) => fs.readFileSync(path.join(ROOT, file), 'utf8')
const body = (slug: string) => findChapter(slug)?.body ?? ''

describe('chapters', () => {
  it('has eight chapters numbered in order', () => {
    expect(CHAPTERS.map((chapter) => Number(chapter.number))).toEqual([1, 2, 3, 4, 5, 6, 7, 8])
  })

  it.each(CHAPTERS.map((chapter) => [chapter.slug, chapter] as const))(
    '%s has a summary, a time, the standard sections and its own case',
    (_slug, chapter) => {
      expect(chapter.summary.length).toBeGreaterThan(10)
      expect(chapter.minutes).toBeGreaterThan(0)
      expect(chapter.body).toMatch(/^## Goal$/m)
      expect(chapter.body).toMatch(/^## The case$/m)
      expect(chapter.body).toMatch(/^## Check it works$/m)
      expect(chapter.body).toMatch(/^## Trade-offs and when the usual advice is wrong$/m)
      expect(chapter.body).toMatch(/^## Exercise$/m)
      expect(chapter.body).toContain(`dove run ${Number(chapter.number)}`)
      expect(chapter.body).toContain(`dove check ${Number(chapter.number)}`)
    },
  )

  it('adds up to two and three quarter hours', () => {
    expect(CHAPTERS.reduce((sum, chapter) => sum + chapter.minutes, 0)).toBe(165)
  })

  it('is written in plain style: no em dashes anywhere', () => {
    for (const chapter of CHAPTERS) expect(chapter.body, chapter.slug).not.toMatch(/[—–]/)
  })

  it('only mentions lab files that exist', () => {
    const mentioned = new Set(
      CHAPTERS.flatMap((chapter) =>
        [...chapter.body.matchAll(/`(lab\/[\w./-]+\.\w+)`/g)].map((m) => m[1] ?? ''),
      ),
    )
    expect(mentioned.size).toBeGreaterThanOrEqual(8)
    for (const file of mentioned) {
      expect(fs.existsSync(path.join(ROOT, file)), `${file} is missing`).toBe(true)
    }
  })

  it('shows check output exactly as the checker words it', () => {
    const checks = read('lab/dove/checks.py')
    const labels = CHAPTERS.flatMap((chapter) =>
      [...chapter.body.matchAll(/^ {2}(?:PASS|FAIL) {2}(.+)$/gm)].map((m) => m[1] ?? ''),
    )
    expect(labels.length).toBeGreaterThan(50)
    for (const label of labels) {
      // A measured value at the end is filled in by an f-string; compare the fixed part.
      expect(checks, label).toContain(label.replace(/ \([^()]*\)$/, ''))
    }
  })

  it('shows every case passing in its Check it works section', () => {
    for (const chapter of CHAPTERS) {
      const section = chapter.body.split('## Check it works')[1]?.split('\n## ')[0] ?? ''
      expect(section, chapter.slug).toMatch(/PASS/)
      expect(section, chapter.slug).not.toMatch(/FAIL/)
    }
  })

  it('names only experiments the lab has', () => {
    const experiments = read('lab/dove/experiments.py')
    const named = CHAPTERS.flatMap((chapter) =>
      [...chapter.body.matchAll(/dove try ([\w-]+)/g)].map((m) => m[1] ?? ''),
    )
    expect(new Set(named)).toEqual(new Set(['outbox', 'backoff', 'digest', 'fanout']))
    for (const name of named) expect(experiments).toContain(`"${name}":`)
  })

  it('ends with the same checklist the home page shows', () => {
    const last = body('08-webhooks')
    CHECKLIST.forEach((item, index) => expect(last).toContain(`${index + 1}. ${item}`))
  })
})

describe('cases', () => {
  it('has one case per chapter, titled as the lab titles it', () => {
    const cli = read('lab/dove/__main__.py')
    expect(CASES.map((item) => item.number)).toEqual(CHAPTERS.map((chapter) => chapter.number))
    for (const item of CASES) expect(cli).toContain(`"${item.title}")`)
  })

  it('shows each symptom as it appears in its chapter', () => {
    for (const item of CASES) {
      const chapter = CHAPTERS.find((c) => c.number === item.number)
      expect(chapter?.body, item.number).toContain(item.symptom)
    }
  })

  it('shows the case 02 walkthrough as the lab prints and fixes it', () => {
    for (const line of CASE_TWO.run) expect(body('02-idempotency')).toContain(line)
    for (const line of CASE_TWO.check) expect(body('02-idempotency')).toContain(`  ${line}`)
    for (const line of CASE_TWO.fix) {
      expect(read('lab/tests/solutions/case02_idempotency.py')).toContain(line)
    }
  })

  it('points every pipeline step at chapters that exist', () => {
    const numbers = new Set(CHAPTERS.map((chapter) => chapter.number))
    const covered = new Set(PIPELINE.flatMap((stage) => stage.chapters))
    for (const number of covered) expect(numbers.has(number)).toBe(true)
    expect(covered.size).toBe(8)
  })

  it('links headings by a stable slug', () => {
    expect(slugify('Trade-offs and when the usual advice is wrong')).toBe(
      'trade-offs-and-when-the-usual-advice-is-wrong',
    )
    expect(
      headingsOf('## Goal\n```\n## not a heading\n```\n## Check it works').map((h) => h.id),
    ).toEqual(['goal', 'check-it-works'])
  })
})

describe('measured numbers', () => {
  it('quotes each backoff row exactly as chapter 04 prints it', () => {
    for (const row of MEASURED.backoff.rows) {
      const [requests, busiest, done] = row.values
      const line = `  ${row.label.padEnd(32)}${requests?.padStart(9)}${busiest?.padStart(16)}${done?.replace(' s', '').padStart(11)} s`
      expect(body('04-permanent-failures'), row.label).toContain(line)
    }
  })

  it('marks only the jittered strategies as spreading the load', () => {
    const spread = MEASURED.backoff.rows.filter((row) => row.verdict === 'sent')
    expect(spread.map((row) => row.label)).toEqual([
      'exponential, full jitter',
      'exponential, equal jitter',
    ])
  })

  it('quotes each fanout row exactly as chapter 07 prints it', () => {
    for (const row of MEASURED.fanout) {
      expect(body('07-priority')).toMatch(
        new RegExp(`${row.label}\\s+${row.requests}\\s+[\\d.]+\\s+${row.pushesPerSecond}`),
      )
    }
    expect(body('07-priority')).toContain(MEASURED.machine)
  })

  it("quotes Pip's numbers exactly as the lab measured them", () => {
    const priority = notesFor('/workshop/07-priority')
      .quiz.map((item) => item.why)
      .join(' ')
    expect(priority).toContain(MEASURED.fanout[0].pushesPerSecond)
    expect(priority).toContain(MEASURED.fanout[2].pushesPerSecond)
    const backoff = notesFor('/workshop/04-permanent-failures').quiz[1]?.why ?? ''
    expect(backoff).toContain(MEASURED.backoff.rows[0].values[1])
    const digest = notesFor('/workshop/06-digests').quiz[0]?.why ?? ''
    expect(digest).toContain(String(MEASURED.digest['busy shop'].debounce[1]))
    expect(body('06-digests')).toContain('longest wait: 604 minutes')
  })

  it('quotes each outbox timing exactly as chapter 01 prints it', () => {
    for (const row of MEASURED.outbox) {
      expect(body('01-the-outbox')).toMatch(new RegExp(`${row.label}\\s+${row.shown}`))
    }
  })
})

describe("Pip's notes", () => {
  it('has notes for every chapter and none for chapters that do not exist', () => {
    expect([...NOTE_SLUGS].sort()).toEqual(CHAPTERS.map((chapter) => chapter.slug))
  })

  it('picks the notes for the page you are on', () => {
    expect(notesFor('/workshop/06-digests').note).toContain('digest.due')
    expect(notesFor('/workshop').quiz.length).toBe(2)
    expect(notesFor('/')).toBe(notesFor('/no-such-page'))
  })

  it.each([
    ['/', '/'],
    ['/workshop', '/workshop'],
    ...NOTE_SLUGS.map((slug) => [slug, `/workshop/${slug}`]),
  ])('asks %s two questions with exactly one right answer each', (_name, pathname) => {
    const { quiz } = notesFor(pathname)
    expect(quiz.length).toBe(2)
    for (const item of quiz) {
      expect(item.options.length).toBeGreaterThanOrEqual(3)
      expect(new Set(item.options).size).toBe(item.options.length)
      expect(item.options[item.answer], item.q).toBeDefined()
      expect(item.why.length).toBeGreaterThan(20)
    }
  })
})
