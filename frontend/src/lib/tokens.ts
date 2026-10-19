// Colour pairs the site puts text on. Each value mirrors a variable in globals.css, and a unit
// test checks both that they match and that every pair meets WCAG AA (4.5:1).

export const TOKENS = {
  canvas: '#fbf8f1',
  surface: '#ffffff',
  surface2: '#f3efe6',
  ink: '#141412',
  ink2: '#34322d',
  muted: '#6b675f',
  accent: '#ff5a1f',
  accentOn: '#141412',
  accentText: '#c2410c',
  accentWash: '#fff1ea',
  ok: '#15803d',
  okWash: '#ecfdf3',
  bad: '#b91c1c',
  badWash: '#fef2f2',
  codeBg: '#1c1b18',
  codeHead: '#282622',
  codeInk: '#f5f2ea',
  codeMuted: '#b5ae9f',
  codeOk: '#86efac',
  codeBad: '#fca5a5',
  codeAccent: '#ffb38a',
} as const

export type Token = keyof typeof TOKENS

export const TEXT_PAIRS: readonly [Token, Token][] = [
  ['ink', 'canvas'],
  ['ink2', 'canvas'],
  ['muted', 'canvas'],
  ['ink', 'surface'],
  ['ink2', 'surface'],
  ['muted', 'surface'],
  ['ink2', 'surface2'],
  ['muted', 'surface2'],
  ['accentText', 'canvas'],
  ['accentText', 'surface'],
  ['accentText', 'accentWash'],
  ['accentOn', 'accent'],
  ['ink', 'accentWash'],
  ['canvas', 'ink'],
  ['ok', 'okWash'],
  ['ok', 'surface'],
  ['bad', 'badWash'],
  ['bad', 'surface'],
  ['codeInk', 'codeBg'],
  ['codeMuted', 'codeBg'],
  ['codeOk', 'codeBg'],
  ['codeBad', 'codeBg'],
  ['codeAccent', 'codeBg'],
  ['codeMuted', 'codeHead'],
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
