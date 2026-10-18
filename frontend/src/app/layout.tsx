import type { Metadata, Viewport } from 'next'
import { Archivo, Red_Hat_Mono } from 'next/font/google'

import { Shell } from '@/components/Shell'
import { SITE_URL, TITLE } from '@/lib/site'

import './globals.css'

const sans = Archivo({ variable: '--font-archivo', subsets: ['latin'], axes: ['wdth'] })
const mono = Red_Hat_Mono({ variable: '--font-redhat-mono', subsets: ['latin'] })

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: TITLE, template: `%s · ${TITLE}` },
  description:
    'A hands-on notifications workshop: eight real bugs in one small parcel company. Outboxes, idempotency keys, ordering, permanent errors, quiet hours, digests, priority lanes and signed webhooks.',
}

export const viewport: Viewport = { themeColor: '#141413' }

export default function RootLayout({ children }: LayoutProps<'/'>) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <a
          href="#main"
          className="sr-only bg-signal px-4 py-2 font-semibold text-ink focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50"
        >
          Skip to content
        </a>
        <Shell>{children}</Shell>
      </body>
    </html>
  )
}
