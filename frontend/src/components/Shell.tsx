import Link from 'next/link'

import { BackToTop } from '@/components/BackToTop'
import { REPO_URL, TITLE } from '@/lib/site'

function Bell() {
  return (
    <svg viewBox="0 0 24 24" className="size-5" aria-hidden="true">
      <path
        d="M6 16V11a6 6 0 1 1 12 0v5l1.5 2h-15z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <path d="M10 20.5a2 2 0 0 0 4 0" fill="none" stroke="currentColor" strokeWidth="1.8" />
      <circle cx="17.5" cy="6.5" r="3" fill="#ff5a1f" />
    </svg>
  )
}

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <>
      <header className="sticky top-3 z-40 px-3 pt-3">
        <nav
          aria-label="Main"
          className="glass mx-auto flex h-14 max-w-5xl items-center justify-between gap-3 rounded-full pr-2 pl-4"
        >
          <Link href="/" className="flex min-w-0 items-center gap-2 text-ink">
            <Bell />
            <span className="truncate text-[15px] font-semibold tracking-[-0.01em]">
              <span className="hidden sm:inline">{TITLE}</span>
              <span className="sm:hidden">Notifications</span>
            </span>
          </Link>
          <div className="flex shrink-0 items-center gap-1">
            <Link
              href="/workshop"
              className="inline-flex h-10 items-center rounded-full px-3.5 text-[14.5px] text-ink-2 hover:bg-surface-2 hover:text-ink"
            >
              Chapters
            </Link>
            <a
              href={REPO_URL}
              className="inline-flex h-10 items-center rounded-full bg-ink px-4 text-[14.5px] font-medium text-canvas hover:bg-ink-2"
            >
              GitHub
            </a>
          </div>
        </nav>
      </header>
      <main id="main" className="flex-1">
        {children}
      </main>
      <footer className="mx-auto w-full max-w-5xl px-4 py-12 text-[14px] text-muted">
        <div className="flex flex-col gap-2 border-t border-hairline pt-8 sm:flex-row sm:justify-between">
          <p>{TITLE}. An open-source, hands-on workshop.</p>
          <p>MIT licensed.</p>
        </div>
      </footer>
      <div className="fixed right-[max(1rem,env(safe-area-inset-right))] bottom-[max(1rem,env(safe-area-inset-bottom))] z-30">
        <BackToTop />
      </div>
    </>
  )
}
