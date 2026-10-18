'use client'

import { useState } from 'react'

// Copies a block of text. On a dark code block by default, or on paper with tone="light".

export function CopyButton({ text, tone = 'dark' }: { text: string; tone?: 'dark' | 'light' }) {
  const [state, setState] = useState<'idle' | 'copied' | 'blocked'>('idle')
  const look =
    tone === 'dark'
      ? 'border-code-rule text-code-muted hover:border-code-muted hover:text-code-ink'
      : 'border-rule-strong bg-surface text-ink-2 hover:border-ink hover:text-ink'
  return (
    <button
      type="button"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text)
          setState('copied')
        } catch {
          setState('blocked')
        }
        window.setTimeout(() => setState('idle'), 1600)
      }}
      className={`inline-flex h-10 min-w-16 items-center justify-center border px-3 font-mono text-[11px] font-semibold tracking-[0.1em] uppercase ${look}`}
    >
      <span aria-live="polite">
        {state === 'copied' ? 'Copied' : state === 'blocked' ? 'Select to copy' : 'Copy'}
      </span>
    </button>
  )
}
