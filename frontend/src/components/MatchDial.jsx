/**
 * The signature visual of the app: an instrument-style radial dial rather
 * than a plain progress bar or badge, because "match score" is presented
 * as a measurement/reading, not just a label — reinforcing the tool's
 * evidence-based framing (see justification text alongside it).
 */
function colorForScore(score) {
  if (score >= 75) return '#4FD1C5' // mint
  if (score >= 50) return '#E8A33D' // amber
  return '#D65F5F' // rose
}

export default function MatchDial({ score, size = 96 }) {
  const radius = (size - 12) / 2
  const circumference = 2 * Math.PI * radius
  const arcFraction = 0.75 // 270-degree arc, like an analog meter
  const arcLength = circumference * arcFraction
  const filled = arcLength * (Math.min(Math.max(score, 0), 100) / 100)
  const color = colorForScore(score)
  const center = size / 2
  const rotation = 135 // start angle so the gap sits at the bottom

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-0">
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="#242F3D"
          strokeWidth="8"
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeDashoffset={0}
          strokeLinecap="round"
          transform={`rotate(${rotation} ${center} ${center})`}
        />
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeDashoffset={arcLength - filled}
          strokeLinecap="round"
          transform={`rotate(${rotation} ${center} ${center})`}
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="font-mono font-semibold text-lg" style={{ color }}>
          {Math.round(score)}
        </span>
        <span className="text-[9px] uppercase tracking-wider text-ink-600">/ 100</span>
      </div>
    </div>
  )
}
