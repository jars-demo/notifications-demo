'use client'

import { useEffect, useRef, useState } from 'react'

import {
  CAP,
  clock,
  DAY,
  PATTERNS,
  type Rule,
  RULES,
  simulate,
  SLOT,
  summarise,
  toggleSlot,
} from '@/lib/digest'

// The digest board: one customer's updates over three hours, and the pushes a batching rule
// makes from them. Tap a slot to add or clear updates, pick a rule, and press play to watch the
// day go by. The rules live in lib/digest.ts, which is unit tested against the lab.

const SPAN = DAY + 60 // the timeline runs an hour past the last slot, so late pushes show
const SLOTS = DAY / SLOT
const NOISY = 12 // more pushes than this in three hours is a buzzing phone

function at(minute: number): string {
  return `${(minute / SPAN) * 100}%`
}

function Icon({ kind }: { kind: 'sent' | 'held' | 'lost' }) {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true" className="shrink-0">
      {kind === 'sent' ? (
        <path d="M2.5 7.5l3 3 6-7" fill="none" stroke="currentColor" strokeWidth="2.2" />
      ) : kind === 'lost' ? (
        <path d="M3 3l8 8M11 3l-8 8" stroke="currentColor" strokeWidth="2.2" />
      ) : (
        <g fill="none" stroke="currentColor" strokeWidth="1.8">
          <circle cx="7" cy="7" r="5.2" />
          <path d="M7 4v3.2l2.2 1.4" />
        </g>
      )}
    </svg>
  )
}

function Stat({
  label,
  value,
  verdict,
  note,
}: {
  label: string
  value: string
  verdict: 'sent' | 'lost'
  note: string
}) {
  const tone = verdict === 'sent' ? 'text-sent' : 'text-lost'
  return (
    <div className="flex min-w-0 flex-col gap-1 border-t-[3px] border-ink pt-3">
      <dt className="label">{label}</dt>
      <dd data-testid={label} className="display text-[30px] leading-none text-ink">
        {value}
      </dd>
      <dd className={`flex items-center gap-1.5 text-[13.5px] font-semibold ${tone}`}>
        <Icon kind={verdict} />
        {note}
      </dd>
    </div>
  )
}

export function DigestBoard() {
  const [pattern, setPattern] = useState<string>('busy shop')
  const [updates, setUpdates] = useState<number[]>([...(PATTERNS['busy shop'] ?? [])])
  const [rule, setRule] = useState<Rule>('debounce')
  const [playhead, setPlayhead] = useState<number | null>(null)
  const timer = useRef<number | null>(null)

  const pushes = simulate(rule, updates)
  const summary = summarise(pushes)
  const now = playhead ?? Infinity
  const shown = pushes.filter((push) => push.at <= now)
  const ruleLabel = RULES.find((r) => r.id === rule)?.short ?? rule
  const latest = shown[shown.length - 1]

  useEffect(() => () => stop(), [])

  function stop() {
    if (timer.current !== null) window.clearInterval(timer.current)
    timer.current = null
  }

  function reset(next: () => void) {
    stop()
    setPlayhead(null)
    next()
  }

  function play() {
    stop()
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setPlayhead(null)
      return
    }
    setPlayhead(0)
    timer.current = window.setInterval(() => {
      setPlayhead((minute) => {
        const next = (minute ?? 0) + 2
        if (next >= SPAN) {
          stop()
          return null
        }
        return next
      })
    }, 30)
  }

  const narration =
    playhead !== null
      ? `${clock(playhead)}. ${shown.length} push${shown.length === 1 ? '' : 'es'} so far.`
      : updates.length === 0
        ? 'No updates. Tap a slot to add one.'
        : `${ruleLabel}, ${pattern}: ${summary.pushes} push${summary.pushes === 1 ? '' : 'es'} for ${updates.length} update${updates.length === 1 ? '' : 's'}. The longest any update waited was ${summary.longestWait} minutes.`

  return (
    <div className="slip flex min-w-0 flex-col gap-6 p-4 sm:p-6">
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <span className="label" id="pattern-label">
            Updates
          </span>
          <div role="group" aria-labelledby="pattern-label" className="flex flex-wrap gap-2">
            {[...Object.keys(PATTERNS), 'clear'].map((name) => (
              <button
                key={name}
                type="button"
                aria-pressed={pattern === name}
                onClick={() =>
                  reset(() => {
                    setPattern(name)
                    setUpdates([...(PATTERNS[name] ?? [])])
                  })
                }
                className={`inline-flex h-10 items-center border px-3.5 text-[14.5px] font-semibold ${
                  pattern === name
                    ? 'border-ink bg-ink text-surface'
                    : 'border-rule-strong bg-surface text-ink hover:border-ink'
                }`}
              >
                {name === 'clear' ? 'Clear' : name[0]?.toUpperCase() + name.slice(1)}
              </button>
            ))}
          </div>
        </div>
        <div className="flex flex-col gap-2">
          <span className="label" id="rule-label">
            Batching rule
          </span>
          <div
            role="group"
            aria-labelledby="rule-label"
            className="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap"
          >
            {RULES.map((option) => (
              <button
                key={option.id}
                type="button"
                aria-pressed={rule === option.id}
                onClick={() => reset(() => setRule(option.id))}
                className={`inline-flex min-h-10 items-center justify-center border px-3.5 py-1 text-[14.5px] font-semibold ${
                  rule === option.id
                    ? 'border-ink bg-signal text-ink'
                    : 'border-rule-strong bg-surface text-ink hover:border-ink'
                }`}
              >
                {option.short}
              </button>
            ))}
          </div>
        </div>
      </div>

      <figure className="flex min-w-0 flex-col gap-2">
        <figcaption className="flex flex-wrap items-center justify-between gap-2">
          <span className="label">08:00 to 12:00</span>
          <span className="flex flex-wrap gap-x-4 gap-y-1 text-[12.5px] text-ink-2">
            <span className="inline-flex items-center gap-1.5">
              <span className="inline-block h-3 w-0.5 bg-ink" aria-hidden="true" />
              update
            </span>
            <span className="inline-flex items-center gap-1.5 text-held">
              <Icon kind="held" />
              held
            </span>
            <span className="inline-flex items-center gap-1.5 text-sent">
              <Icon kind="sent" />
              push sent
            </span>
          </span>
        </figcaption>
        <div className="relative h-28 border border-rule-strong bg-canvas" aria-hidden="true">
          {[0, 60, 120, 180].map((minute) => (
            <span
              key={minute}
              className="absolute top-0 bottom-0 border-l border-dashed border-rule-strong"
              style={{ left: at(minute) }}
            >
              <span className="absolute top-1 left-1 font-mono text-[10.5px] text-muted">
                {clock(minute)}
              </span>
            </span>
          ))}
          {updates.map((minute, index) => (
            <span
              key={`${minute}-${index}`}
              className={`absolute top-6 h-6 w-0.5 bg-ink ${minute > now ? 'opacity-25' : ''}`}
              style={{ left: at(minute) }}
            />
          ))}
          {shown.map((push) => {
            const oldest = Math.min(...push.carried)
            return (
              <span key={push.at}>
                <span
                  className="absolute top-[3.6rem] h-2 bg-held"
                  style={{ left: at(oldest), width: at(push.at - oldest) }}
                />
                <span
                  className="absolute top-[4.6rem] -ml-2 grid size-4 place-items-center bg-sent text-surface"
                  style={{ left: at(push.at) }}
                >
                  <svg width="10" height="10" viewBox="0 0 14 14">
                    <path
                      d="M2.5 7.5l3 3 6-7"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.6"
                    />
                  </svg>
                </span>
              </span>
            )
          })}
          {playhead !== null ? (
            <span
              className="sweep absolute top-0 bottom-0 w-0.5 bg-signal-deep"
              style={{ left: at(playhead) }}
            />
          ) : null}
        </div>
      </figure>

      <div className="flex flex-col gap-2">
        <span className="label" id="slots-label">
          Tap a slot to add or clear updates
        </span>
        <div
          role="group"
          aria-labelledby="slots-label"
          className="grid grid-cols-6 gap-1 sm:grid-cols-12"
        >
          {Array.from({ length: SLOTS }, (_, slot) => {
            const count = updates.filter(
              (minute) => minute >= slot * SLOT && minute < (slot + 1) * SLOT,
            ).length
            return (
              <button
                key={slot}
                type="button"
                aria-label={`${clock(slot * SLOT)}, ${count} update${count === 1 ? '' : 's'}`}
                onClick={() =>
                  reset(() => {
                    setPattern('custom')
                    setUpdates((current) => toggleSlot(current, slot))
                  })
                }
                className={`flex h-10 min-w-0 flex-col items-center justify-center border font-mono text-[10.5px] leading-none ${
                  count > 0
                    ? 'border-ink bg-ink text-surface'
                    : 'border-rule bg-surface text-muted hover:border-ink'
                }`}
              >
                <span>{clock(slot * SLOT)}</span>
                {count > 1 ? <span className="mt-0.5 text-[9.5px]">x{count}</span> : null}
              </button>
            )
          })}
        </div>
      </div>

      <dl className="grid grid-cols-2 gap-4">
        <Stat
          label="Pushes"
          value={String(summary.pushes)}
          verdict={summary.pushes <= NOISY ? 'sent' : 'lost'}
          note={summary.pushes <= NOISY ? 'a calm phone' : 'a buzzing phone'}
        />
        <Stat
          label="Longest wait"
          value={`${summary.longestWait} min`}
          verdict={summary.longestWait <= CAP ? 'sent' : 'lost'}
          note={summary.longestWait <= CAP ? `within ${CAP} minutes` : `over ${CAP} minutes`}
        />
      </dl>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <button
          type="button"
          onClick={play}
          disabled={updates.length === 0}
          className="inline-flex h-11 shrink-0 items-center justify-center gap-2 bg-ink px-5 text-[15px] font-semibold text-surface hover:bg-night-2 disabled:opacity-40"
        >
          <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
            <path d="M2 1l9 5-9 5z" fill="currentColor" />
          </svg>
          Play the morning
        </button>
        <p role="status" className="min-w-0 text-[14.5px] leading-snug text-ink-2">
          {narration}
          {playhead !== null && latest
            ? ` Last push at ${clock(latest.at)} carried ${latest.carried.length}.`
            : ''}
        </p>
      </div>
    </div>
  )
}
