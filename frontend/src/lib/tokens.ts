// Colour pairs the site puts text on. Each value mirrors a variable in globals.css, and a unit
// test checks both that they match and that every pair meets WCAG AA (4.5:1).

export const TOKENS = {
  canvas: '#f2f1ec',
  surface: '#ffffff',
  surface2: '#e8e7e0',
  ink: '#121211',
  ink2: '#3b3a36',
  muted: '#5c5b55',
  signal: '#ffc61a',
  signalDeep: '#7a5800',
  night: '#141413',
  night2: '#232321',
  onNight: '#f2f1ec',
  onNightMuted: '#b0aea5',
  sent: '#126b38',
  sentWash: '#e0f0e5',
  lost: '#b3261e',
  lostWash: '#fbe6e3',
  held: '#1f4fb8',
  heldWash: '#e4ebfa',
  codeBg: '#191917',
  codeInk: '#eceae2',
  codeMuted: '#a9a69c',
  codeLost: '#ff9f93',
  codeSent: '#8fd6a6',
} as const

export type Token = keyof typeof TOKENS

export const TEXT_PAIRS: readonly [Token, Token][] = [
  ['ink', 'canvas'],
  ['ink2', 'canvas'],
  ['muted', 'canvas'],
  ['ink', 'surface'],
  ['muted', 'surface'],
  ['ink2', 'surface2'],
  ['muted', 'surface2'],
  ['ink', 'signal'],
  ['signalDeep', 'canvas'],
  ['signalDeep', 'surface'],
  ['sent', 'sentWash'],
  ['sent', 'surface'],
  ['lost', 'lostWash'],
  ['lost', 'surface'],
  ['held', 'heldWash'],
  ['held', 'surface'],
  ['onNight', 'night'],
  ['onNightMuted', 'night'],
  ['onNight', 'night2'],
  ['signal', 'night'],
  ['codeInk', 'codeBg'],
  ['codeMuted', 'codeBg'],
  ['codeLost', 'codeBg'],
  ['codeSent', 'codeBg'],
]

function channel(hex: string, offset: number): number {
  const value = parseInt(hex.slice(offset, offset + 2), 16) / 255
  return value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4
}

function luminance(hex: string): number {
  return 0.2126 * channel(hex, 1) + 0.7152 * channel(hex, 3) + 0.0722 * channel(hex, 5)
}

export function contrast(a: string, b: string): number {
  const [la, lb] = [luminance(a), luminance(b)]
  return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05)
}
