import data from './storm.json'

// Requests per second in the retry storm of chapter 04, exported from the lab's own simulation
// (lab/cases/case04_jitter.py and its solution, seed 7). Nothing here is computed on the site.

export type Strategy = 'exponential' | 'jitter'

export const CAPACITY = 100
export const OUTAGE_END = 30

export type Storm = { perSecond: number[]; total: number; last: number; peakAfter: number }

export const STORMS: Record<Strategy, Storm> = data

/** The busiest second, and the second it happened in, from `from` onwards. */
export function busiest(storm: Storm, from = 0): { second: number; requests: number } {
  let best = { second: from, requests: 0 }
  storm.perSecond.forEach((requests, second) => {
    if (second >= from && requests > best.requests) best = { second, requests }
  })
  return best
}
