import { Link } from 'react-router-dom'

export default function TopBar() {
  return (
    <header className="border-b border-ink-700 bg-ink-950/90 backdrop-blur sticky top-0 z-10">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2.5 group">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className="text-amber">
            <rect x="4" y="3" width="16" height="18" rx="1.5" stroke="currentColor" strokeWidth="1.6" />
            <path d="M8 8h8M8 12h8M8 16h5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            <circle cx="17.5" cy="16.5" r="3" fill="#0B0F14" stroke="currentColor" strokeWidth="1.6" />
            <path d="m19.6 18.6 1.4 1.4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
          </svg>
          <span className="font-display font-semibold tracking-tight text-paper-100 group-hover:text-amber transition-colors">
            Smart Resume Screener
          </span>
        </Link>
        <span className="text-xs font-mono text-ink-600 hidden sm:block">
          resume → JD → ranked shortlist
        </span>
      </div>
    </header>
  )
}
