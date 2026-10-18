// The digest board's rules. They are the same four rules as `dove try digest` in the lab
// (lab/dove/experiments.py, policy_pushes), minute for minute, and a unit test checks that the
// results here match the numbers chapter 06 prints.

export const QUIET = 10 // minutes with no new update before a debounce sends
export const CAP = 30 // the most any update may wait under the capped rule
export const GAP = 15 // the throttle sends at most once in this many minutes
export const DAY = 180 // the board shows three hours, in minutes
export const SLOT = 5 // one tap on the board adds an update at the start of a five minute slot

export type Rule = 'every' | 'throttle' | 'debounce' | 'capped'

export const RULES: readonly { id: Rule; label: string; short: string }[] = [
  { id: 'every', label: 'every update', short: 'Every update' },
  { id: 'throttle', label: `throttle, ${GAP} min`, short: `Throttle ${GAP}` },
  { id: 'debounce', label: `debounce, ${QUIET} min`, short: `Debounce ${QUIET}` },
  { id: 'capped', label: `debounce ${QUIET}, cap ${CAP}`, short: `Debounce, cap ${CAP}` },
]

function range(start: number, stop: number, step = 1): number[] {
  return Array.from({ length: Math.ceil((stop - start) / step) }, (_, i) => start + i * step)
}

export const PATTERNS: Record<string, readonly number[]> = {
  'busy shop': range(0, 180, 5),
  'a burst': [...range(30, 42), 150],
  'quiet day': [10, 12, 15, 120],
}

export type Push = { at: number; carried: number[] }

/** Run one rule over a list of update minutes. Each push carries every update waiting for it. */
export function simulate(rule: Rule, updates: readonly number[]): Push[] {
  const sorted = [...updates].sort((a, b) => a - b)
  const end = (sorted[sorted.length - 1] ?? 0) + 60
  const pushes: Push[] = []
  let pending: number[] = []
  let due = 0
  let started = 0
  let last = -1e9
  for (let now = 0; now < end; now++) {
    if (pending.length > 0) {
      const ready = rule === 'throttle' ? now - last >= GAP : now >= due
      if (ready) {
        pushes.push({ at: now, carried: pending })
        last = now
        pending = []
      }
    }
    for (const update of sorted.filter((u) => u === now)) {
      if (rule === 'every' || (rule === 'throttle' && pending.length === 0 && now - last >= GAP)) {
        pushes.push({ at: now, carried: [update] })
        last = now
        continue
      }
      if (pending.length === 0) started = now
      pending.push(update)
      due = rule === 'debounce' ? now + QUIET : Math.min(now + QUIET, started + CAP)
    }
  }
  return pushes
}

export type Summary = { pushes: number; longestWait: number; waiting: number[] }

/** How many pushes, and the longest any update waited. `waiting` is each push's oldest wait. */
export function summarise(pushes: readonly Push[]): Summary {
  const waits = pushes.flatMap((push) => push.carried.map((made) => push.at - made))
  return {
    pushes: pushes.length,
    longestWait: waits.length ? Math.max(...waits) : 0,
    waiting: pushes.map((push) => push.at - Math.min(...push.carried)),
  }
}

/** Tap a slot: clear it if it has updates, or add one update at its start if it is empty. */
export function toggleSlot(updates: readonly number[], slot: number): number[] {
  const from = slot * SLOT
  const inSlot = (minute: number) => minute >= from && minute < from + SLOT
  return updates.some(inSlot)
    ? updates.filter((minute) => !inSlot(minute))
    : [...updates, from].sort((a, b) => a - b)
}

export function clock(minute: number): string {
  const hours = 8 + Math.floor(minute / 60)
  return `${String(hours).padStart(2, '0')}:${String(minute % 60).padStart(2, '0')}`
}
