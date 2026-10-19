'use client'

import { useState } from 'react'

import { busiest, CAPACITY, OUTAGE_END, type Strategy, STORMS } from '@/lib/storm'

// Requests per second after a 30 second outage, for two retry strategies. The data is the lab's.

const W = 720
const H = 260
const PAD = { left: 44, right: 12, top: 16, bottom: 30 }
const SECONDS = 180
const TOP = 1000

const x = (second: number) => PAD.left + (second / SECONDS) * (W - PAD.left - PAD.right)
const y = (requests: number) =>
  PAD.top + (1 - Math.min(requests, TOP) / TOP) * (H - PAD.top - PAD.bottom)

const LABELS: Record<Strategy, string> = {
  exponential: 'Exponential backoff',
  jitter: 'With full jitter',
}

export function StormChart() {
  const [strategy, setStrategy] = useState<Strategy>('exponential')
  const storm = STORMS[strategy]
  const peak = busiest(storm, OUTAGE_END)
  const barWidth = (W - PAD.left - PAD.right) / SECONDS

  return (
    <div className="card flex flex-col gap-4 p-4 sm:p-6">
      <fieldset className="flex flex-wrap items-center gap-2">
        <legend className="sr-only">Retry strategy</legend>
        {(Object.keys(LABELS) as Strategy[]).map((id) => (
          <label
            key={id}
            className={`inline-flex h-10 cursor-pointer items-center rounded-full px-4 text-[14px] font-medium has-focus-visible:outline-2 has-focus-visible:outline-accent ${
              strategy === id ? 'bg-ink text-canvas' : 'bg-surface-2 text-ink-2 hover:text-ink'
            }`}
          >
            <input
              type="radio"
              name="strategy"
              value={id}
              checked={strategy === id}
              onChange={() => setStrategy(id)}
              className="sr-only"
            />
            {LABELS[id]}
          </label>
        ))}
      </fieldset>

      <figure className="flex flex-col gap-2">
        <div className="overflow-x-auto">
          <svg
            viewBox={`0 0 ${W} ${H}`}
            role="img"
            aria-label={`${LABELS[strategy]}: busiest second after recovery has ${peak.requests} requests, last send at ${storm.last} seconds`}
            className="h-auto w-full min-w-[520px]"
          >
            <rect
              x={x(0)}
              y={PAD.top}
              width={x(OUTAGE_END) - x(0)}
              height={H - PAD.top - PAD.bottom}
              fill="#f3efe6"
            />
            <text
              x={x(OUTAGE_END / 2)}
              y={PAD.top + 14}
              textAnchor="middle"
              fontSize="11"
              fill="#6b675f"
            >
              outage
            </text>
            {[0, 250, 500, 750, 1000].map((tick) => (
              <g key={tick}>
                <line
                  x1={PAD.left}
                  x2={W - PAD.right}
                  y1={y(tick)}
                  y2={y(tick)}
                  stroke="rgb(20 20 18 / 0.08)"
                />
                <text
                  x={PAD.left - 6}
                  y={y(tick) + 4}
                  textAnchor="end"
                  fontSize="11"
                  fill="#6b675f"
                >
                  {tick}
                </text>
              </g>
            ))}
            {[0, 30, 60, 90, 120, 150, 180].map((tick) => (
              <text
                key={tick}
                x={x(tick)}
                y={H - 10}
                textAnchor="middle"
                fontSize="11"
                fill="#6b675f"
              >
                {tick} s
              </text>
            ))}
            {storm.perSecond
              .slice(0, SECONDS)
              .map((requests, second) =>
                requests ? (
                  <rect
                    key={second}
                    x={x(second)}
                    y={y(requests)}
                    width={Math.max(barWidth - 0.6, 1)}
                    height={y(0) - y(requests)}
                    fill={
                      second < OUTAGE_END ? '#b5ae9f' : requests > CAPACITY ? '#b91c1c' : '#c2410c'
                    }
                  />
                ) : null,
              )}
            <line
              x1={x(OUTAGE_END)}
              x2={W - PAD.right}
              y1={y(CAPACITY)}
              y2={y(CAPACITY)}
              stroke="#141412"
              strokeDasharray="4 4"
            />
            <text
              x={W - PAD.right}
              y={y(CAPACITY) - 6}
              textAnchor="end"
              fontSize="11"
              fill="#141412"
            >
              capacity: {CAPACITY} a second
            </text>
          </svg>
        </div>
        <figcaption className="text-[13px] text-muted">
          Requests per second, 1,000 senders, seed 7. From the lab&apos;s chapter 04 simulation.
          Bars over capacity are red.
        </figcaption>
      </figure>

      <dl className="grid grid-cols-3 gap-px overflow-hidden rounded-2xl bg-hairline">
        {[
          ['Busiest second after recovery', String(peak.requests)],
          ['Requests in all', storm.total.toLocaleString('en')],
          ['Last send through', `${storm.last} s`],
        ].map(([term, value]) => (
          <div key={term} className="flex flex-col gap-0.5 bg-surface px-3 py-3">
            <dt className="text-[12px] leading-tight text-muted">{term}</dt>
            <dd className="font-mono text-[20px] text-ink" data-testid={term}>
              {value}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
