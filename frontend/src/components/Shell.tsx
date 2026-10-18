import Link from 'next/link'

import { REPO_URL, TITLE } from '@/lib/site'

import { Companion } from './Companion'

// The black band at the top and bottom of every page, and Pip in the corner.

export function LogoMark({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <rect width="32" height="32" fill="#ffc61a" />
      <rect x="6" y="9" width="20" height="14" fill="none" stroke="#121211" strokeWidth="2.2" />
      <path d="M6.5 9.5L16 17l9.5-7.5" fill="none" stroke="#121211" strokeWidth="2.2" />
      <circle cx="25" cy="8" r="4.2" fill="#121211" />
    </svg>
  )
}

const NAV = [
  { href: '/workshop', label: 'Chapters', phone: true },
  { href: '/#board', label: 'Digest board', phone: false },
]

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <>
      <header className="on-night border-b-4 border-signal bg-night text-on-night">
        <nav
          aria-label="Main"
          className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-3 px-4"
        >
          <Link href="/" className="inline-flex min-h-10 min-w-0 items-center gap-3">
            <LogoMark />
            <span className="display truncate text-[17px] leading-none sm:text-[19px]">
              {TITLE}
            </span>
          </Link>
          <ul className="flex shrink-0 items-center gap-1">
            {NAV.map((item) => (
              <li key={item.href} className={item.phone ? '' : 'hidden md:block'}>
                <Link
                  href={item.href}
                  className="inline-flex h-10 items-center px-3 text-[14.5px] font-medium text-on-night hover:bg-night-2"
                >
                  {item.label}
                </Link>
              </li>
            ))}
            <li className="hidden sm:block">
              <a
                href={REPO_URL}
                className="ml-1 inline-flex h-10 items-center border border-on-night-muted px-3.5 text-[14.5px] font-medium text-on-night hover:border-signal hover:text-signal"
              >
                GitHub
              </a>
            </li>
          </ul>
        </nav>
      </header>
      <main id="main" className="flex-1">
        {children}
      </main>
      <footer className="on-night bg-night text-on-night-muted">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 pt-8 pb-24 text-[14px] sm:flex-row sm:items-center sm:justify-between">
          <span>{TITLE}: a notifications workshop. MIT licensed.</span>
          <a href={REPO_URL} className="inline-flex min-h-10 items-center hover:text-on-night">
            Source on GitHub
          </a>
        </div>
      </footer>
      <Companion />
    </>
  )
}
