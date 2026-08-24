import { Link } from 'react-router-dom'
import MatchDial from './MatchDial.jsx'

const STATUS_STYLES = {
  new: 'chip-neutral',
  shortlisted: 'chip-matched',
  rejected: 'chip-missing',
}

export default function CandidateTable({ candidates, onStatusChange }) {
  if (!candidates.length) {
    return (
      <div className="card p-10 text-center text-ink-600">
        <p className="font-mono text-sm">No candidates yet — upload resumes above to screen them.</p>
      </div>
    )
  }

  return (
    <div className="card overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-ink-700 text-left text-ink-600 font-mono text-xs uppercase tracking-wide">
            <th className="px-4 py-3 font-medium">Fit</th>
            <th className="px-4 py-3 font-medium">Candidate</th>
            <th className="px-4 py-3 font-medium">Matched skills</th>
            <th className="px-4 py-3 font-medium">Experience</th>
            <th className="px-4 py-3 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((c) => (
            <tr key={c.id} className="border-b border-ink-700/60 last:border-0 hover:bg-ink-800/40 transition-colors">
              <td className="px-4 py-3">
                <MatchDial score={c.match_score} size={52} />
              </td>
              <td className="px-4 py-3">
                <Link to={`/candidates/${c.id}`} className="font-medium text-paper-100 hover:text-amber transition-colors">
                  {c.name || c.filename}
                </Link>
                <div className="text-xs text-ink-600 font-mono">{c.email || c.filename}</div>
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-wrap gap-1 max-w-xs">
                  {(c.matched_skills || []).slice(0, 4).map((s) => (
                    <span key={s} className="chip-matched !text-[10px] !py-0.5">
                      {s}
                    </span>
                  ))}
                  {c.matched_skills?.length > 4 && (
                    <span className="text-[10px] text-ink-600 self-center">+{c.matched_skills.length - 4}</span>
                  )}
                </div>
              </td>
              <td className="px-4 py-3 font-mono text-paper-200">
                {c.experience_years != null ? `${c.experience_years} yrs` : '—'}
              </td>
              <td className="px-4 py-3">
                <select
                  value={c.status}
                  onChange={(e) => onStatusChange(c.id, e.target.value)}
                  className={`${STATUS_STYLES[c.status]} !py-1 bg-transparent cursor-pointer focus:outline-none`}
                >
                  <option value="new" className="bg-ink-900 text-paper-100">new</option>
                  <option value="shortlisted" className="bg-ink-900 text-paper-100">shortlisted</option>
                  <option value="rejected" className="bg-ink-900 text-paper-100">rejected</option>
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
