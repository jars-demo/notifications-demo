// Pip, the carrier pigeon who flies Dovecote's post: slate feathers, a green sheen on the neck,
// the two black bars of a rock pigeon's wing, and a yellow post bag. Drawn by hand in SVG.
// `face` crops to the head, for the companion button.

export function Pip({ face = false, className }: { face?: boolean; className?: string }) {
  return (
    <svg
      viewBox={face ? '86 28 52 50' : '4 18 140 134'}
      className={className}
      aria-hidden="true"
      focusable="false"
    >
      {face ? null : (
        <g>
          <path d="M40 104L8 116l6 12 32-12z" fill="#4c5564" />
          <path d="M12 120l-4-4 32-12 4 6z" fill="#2a2f37" />
          <path
            d="M74 126l-3 16m0 0l-6 3m6-3l5 3M88 126l2 16m0 0l-5 3m5-3l6 2"
            stroke="#c8505b"
            strokeWidth="3.5"
            strokeLinecap="round"
            fill="none"
          />
          <ellipse cx="80" cy="100" rx="44" ry="29" transform="rotate(-10 80 100)" fill="#8b97a8" />
          <path d="M60 114c16 12 44 10 60-6-6 18-28 26-46 22-8-2-12-8-14-16z" fill="#b8c1cc" />
        </g>
      )}
      <path d="M88 60c-5 14-3 26 8 32l20-6c5-11 5-22 0-30z" fill="#3e8a7c" />
      <path d="M90 66c2 8 6 13 12 16l14-4c2-6 2-12 1-17z" fill="#5aa38c" opacity="0.65" />
      {face ? null : (
        <g className="pip-wing">
          <path d="M54 86c24-16 58-10 66 10-14 13-46 17-74 11z" fill="#6f7b8d" />
          <path
            d="M78 92l26 4M74 100l28 3"
            stroke="#1d2026"
            strokeWidth="3.4"
            strokeLinecap="round"
          />
          <path d="M56 104c-8 2-14 0-18-4" stroke="#4c5564" strokeWidth="3" fill="none" />
        </g>
      )}
      <circle cx="106" cy="50" r="19" fill="#76839a" />
      <path d="M122 47l15 5-15 5z" fill="#34322e" />
      <ellipse cx="123" cy="46.5" rx="3.6" ry="2.4" fill="#ece6d8" />
      <g className="pip-blink">
        <circle cx="111" cy="45" r="5" fill="#f08a24" />
        <circle cx="111.4" cy="45" r="2.5" fill="#121211" />
        <circle cx="112.4" cy="43.9" r="0.9" fill="#ffffff" />
      </g>
      {face ? null : (
        <g>
          <path d="M100 66L68 112" stroke="#121211" strokeWidth="3" strokeLinecap="round" />
          <rect
            x="52"
            y="106"
            width="30"
            height="22"
            rx="2"
            fill="#ffc61a"
            stroke="#121211"
            strokeWidth="2"
          />
          <path
            d="M52 108h30l-4 9H56z"
            fill="#e5ac00"
            stroke="#121211"
            strokeWidth="2"
            strokeLinejoin="round"
          />
          <path d="M58 103h14v6H58z" fill="#ffffff" stroke="#121211" strokeWidth="1.5" />
          <path d="M58 103l7 4 7-4" stroke="#121211" strokeWidth="1.2" fill="none" />
        </g>
      )}
    </svg>
  )
}
