import fs from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { PATTERNS, type Rule, RULES, simulate, summarise, toggleSlot } from '@/lib/digest'
import { MEASURED } from '@/lib/site'

const chapter = fs.readFileSync(path.join(process.cwd(), '..', 'workshop', '06-digests.md'), 'utf8')
const lab = fs.readFileSync(path.join(process.cwd(), '..', 'lab', 'dove', 'experiments.py'), 'utf8')

describe('the digest board', () => {
  it.each(Object.entries(MEASURED.digest))(
    'gives the same pushes and waits as `dove try digest` for the %s',
    (name, expected) => {
      const updates = PATTERNS[name] ?? []
      for (const rule of RULES) {
        const { pushes, longestWait } = summarise(simulate(rule.id, updates))
        expect([pushes, longestWait], `${name}, ${rule.label}`).toEqual(expected[rule.id])
      }
    },
  )

  it('quotes every number exactly as chapter 06 prints it', () => {
    for (const [name, results] of Object.entries(MEASURED.digest)) {
      const table = chapter.slice(chapter.indexOf(`${name}: `))
      for (const rule of RULES) {
        const [pushes, wait] = results[rule.id as Rule]
        const line = `  ${rule.label.padEnd(22)}${String(pushes).padStart(7)}${String(wait).padStart(10)} min`
        expect(table, `${name}, ${rule.label}`).toContain(line)
      }
    }
  })

  it('uses the same patterns and constants as the lab', () => {
    expect(lab).toContain('"busy shop": list(range(0, 180, 5))')
    expect(lab).toContain('"a burst": [*range(30, 42), 150]')
    expect(lab).toContain('"quiet day": [10, 12, 15, 120]')
    expect(lab).toContain('QUIET, CAP, GAP = 10, 30, 15')
  })

  it('carries every update in exactly one push, under every rule', () => {
    const updates = [0, 3, 4, 20, 21, 22, 23, 90, 179]
    for (const rule of RULES) {
      const carried = simulate(rule.id, updates).flatMap((push) => push.carried)
      expect(carried.sort((a, b) => a - b)).toEqual(updates)
    }
  })

  it('never lets the capped rule keep an update waiting more than 30 minutes', () => {
    const endless = Array.from({ length: 36 }, (_, i) => i * 5)
    expect(summarise(simulate('debounce', endless)).longestWait).toBe(185)
    expect(summarise(simulate('capped', endless)).longestWait).toBe(30)
  })

  it('toggles a slot on and off', () => {
    const one = toggleSlot([], 3)
    expect(one).toEqual([15])
    expect(toggleSlot([15, 16, 40], 3)).toEqual([40])
    expect(summarise(simulate('every', one)).pushes).toBe(1)
    expect(summarise(simulate('every', [])).longestWait).toBe(0)
  })
})
