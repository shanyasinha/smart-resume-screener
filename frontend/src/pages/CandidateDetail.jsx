import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api.js'
import MatchDial from '../components/MatchDial.jsx'

export default function CandidateDetail() {
  const { candidateId } = useParams()
  const [candidate, setCandidate] = useState(null)

  useEffect(() => {
    api.getCandidate(candidateId).then(setCandidate)
  }, [candidateId])

  if (!candidate) return <div className="max-w-5xl mx-auto px-6 py-10 text-ink-600 font-mono text-sm">Loading…</div>

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <Link to={`/jobs/${candidate.job_id}`} className="text-xs font-mono text-ink-600 hover:text-amber transition-colors">
        ← back to shortlist
      </Link>

      <div className="grid md:grid-cols-[1fr_260px] gap-6 mt-4">
        <div className="flex flex-col gap-6">
          <div className="card p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-xl font-display font-semibold text-paper-100">
                  {candidate.name || candidate.filename}
                </h1>
                <p className="text-sm text-ink-600 font-mono mt-1">
                  {candidate.email || '—'} {candidate.phone ? `· ${candidate.phone}` : ''}
                </p>
              </div>
              <MatchDial score={candidate.match_score} />
            </div>

            <div className="scanline-divider my-5" />

            <p className="text-xs font-mono uppercase tracking-wide text-ink-600 mb-2">Why this score</p>
            <p className="text-sm text-paper-200 leading-relaxed">{candidate.justification}</p>

            {(candidate.llm_score != null || candidate.keyword_score != null) && (
              <div className="flex gap-4 mt-4 text-xs font-mono text-ink-600">
                {candidate.llm_score != null && <span>LLM signal: {candidate.llm_score}/100</span>}
                {candidate.keyword_score != null && <span>Keyword overlap: {candidate.keyword_score}/100</span>}
              </div>
            )}
          </div>

          <div className="card p-6 grid sm:grid-cols-2 gap-6">
            <div>
              <p className="text-xs font-mono uppercase tracking-wide text-mint mb-2">Matched skills</p>
              <div className="flex flex-wrap gap-1.5">
                {candidate.matched_skills.length ? (
                  candidate.matched_skills.map((s) => (
                    <span key={s} className="chip-matched">
                      {s}
                    </span>
                  ))
                ) : (
                  <span className="text-ink-600 text-sm">None detected</span>
                )}
              </div>
            </div>
            <div>
              <p className="text-xs font-mono uppercase tracking-wide text-rose mb-2">Missing skills</p>
              <div className="flex flex-wrap gap-1.5">
                {candidate.missing_skills.length ? (
                  candidate.missing_skills.map((s) => (
                    <span key={s} className="chip-missing">
                      {s}
                    </span>
                  ))
                ) : (
                  <span className="text-ink-600 text-sm">None — full coverage</span>
                )}
              </div>
            </div>
          </div>

          {candidate.education.length > 0 && (
            <div className="card p-6">
              <p className="text-xs font-mono uppercase tracking-wide text-ink-600 mb-2">Education</p>
              <ul className="text-sm text-paper-200 space-y-1">
                {candidate.education.map((e, i) => (
                  <li key={i}>{e}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <aside className="card p-5 h-fit">
          <p className="text-xs font-mono uppercase tracking-wide text-ink-600 mb-2">Experience</p>
          <p className="font-mono text-lg text-paper-100 mb-4">
            {candidate.experience_years != null ? `${candidate.experience_years} yrs` : 'Not detected'}
          </p>
          <p className="text-xs font-mono uppercase tracking-wide text-ink-600 mb-2">Source file</p>
          <p className="text-sm text-paper-200 break-all mb-4">{candidate.filename}</p>
          <p className="text-xs font-mono uppercase tracking-wide text-ink-600 mb-2">Status</p>
          <span className="chip-neutral capitalize">{candidate.status}</span>
        </aside>
      </div>
    </div>
  )
}
