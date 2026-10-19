import fs from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { headingsOf, slugify } from '@/components/Markdown'
import { QUIZ } from '@/lib/quiz'
import { LEVELS, MEASURED, SYMPTOMS } from '@/lib/site'
import { busiest, OUTAGE_END, STORMS } from '@/lib/storm'
import { CHAPTERS, findChapter } from '@/lib/workshop'

const ROOT = path.join(process.cwd(), '..')
const body = (number: string) => CHAPTERS.find((chapter) => chapter.number === number)?.body ?? ''
const all = CHAPTERS.map((chapter) => chapter.body).join('\n')
const SECTIONS = ['Goal', 'The idea', 'The case', 'Check your fix', 'In production', 'Key points']

describe('chapters', () => {
  it('has ten chapters numbered in order', () => {
    expect(CHAPTERS.map((chapter) => Number(chapter.number))).toEqual([
      1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
    ])
  })

  it.each(CHAPTERS.map((chapter) => [chapter.slug, chapter] as const))(
    '%s has a summary, a time, the standard sections and its case',
    (_slug, chapter) => {
      expect(chapter.summary.length).toBeGreaterThan(20)
      expect(chapter.minutes).toBeGreaterThan(0)
      for (const section of SECTIONS)
        expect(chapter.body).toMatch(new RegExp(`^## ${section}$`, 'm'))
      expect(chapter.body).toContain(`notify run ${Number(chapter.number)}`)
      expect(chapter.body).toContain(`notify check ${Number(chapter.number)}`)
    },
  )

  it('adds up to three hours and twenty five minutes', () => {
    expect(CHAPTERS.reduce((sum, chapter) => sum + chapter.minutes, 0)).toBe(205)
  })

  it('never uses a long dash', () => {
    for (const chapter of CHAPTERS) expect(chapter.body, chapter.slug).not.toMatch(/[–—]/)
  })

  it('only mentions lab files that exist', () => {
    const mentioned = new Set(
      [...all.matchAll(/`(lab\/[\w./-]+)`/g)].map((match) => match[1] ?? ''),
    )
    expect(mentioned.size).toBeGreaterThanOrEqual(10)
    for (const file of mentioned) expect(fs.existsSync(path.join(ROOT, file)), file).toBe(true)
  })

  it('finds chapters by slug and builds an outline from their headings', () => {
    const chapter = findChapter('04-backoff-and-jitter')
    expect(chapter?.title).toBe('Backoff and jitter')
    expect(headingsOf(chapter?.body ?? '').map((h) => h.id)).toContain(slugify('Check your fix'))
  })
})

describe('the numbers on the site come from the chapters', () => {
  it.each(Object.entries(SYMPTOMS))('chapter %s prints its symptom', (number, symptom) => {
    expect(body(number)).toContain(symptom)
  })

  it('quotes the outbox and backoff measurements', () => {
    const row = (...cells: string[]) =>
      new RegExp(cells.map((cell) => cell.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('\\s+'))
    for (const line of MEASURED.outbox) expect(body('01')).toMatch(row(line.label, line.value))
    for (const line of MEASURED.backoff) {
      expect(body('04')).toMatch(row(line.strategy, line.requests, line.peak, line.done))
    }
  })

  it('charts the same storm the chapter prints', () => {
    expect(STORMS.exponential.total).toBe(10500)
    expect(STORMS.exponential.last).toBe(543)
    expect(busiest(STORMS.exponential, OUTAGE_END)).toEqual({ second: 31, requests: 1000 })
    expect(busiest(STORMS.jitter, OUTAGE_END).requests).toBe(STORMS.jitter.peakAfter)
    expect(body('04')).toContain(`requests made:  ${STORMS.exponential.total}`)
  })
})

describe('parts and quiz', () => {
  it('puts every chapter in exactly one part', () => {
    expect(LEVELS.flatMap((level) => level.chapters)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
  })

  it.each(CHAPTERS.map((chapter) => chapter.number))(
    'chapter %s has two answerable questions',
    (number) => {
      const questions = QUIZ[number] ?? []
      expect(questions).toHaveLength(2)
      for (const question of questions) {
        expect(question.options[question.answer]).toBeDefined()
        expect(question.why.length).toBeGreaterThan(20)
      }
    },
  )
})
