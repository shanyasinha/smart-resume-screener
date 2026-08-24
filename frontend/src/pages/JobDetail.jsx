import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api.js'
import UploadZone from '../components/UploadZone.jsx'
import CandidateTable from '../components/CandidateTable.jsx'

export default function JobDetail() {
  const { jobId } = useParams()
  const [job, setJob] = useState(null)
  const [candidates, setCandidates] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [minScore, setMinScore] = useState(0)

  const refresh = useCallback(() => {
    api.getJob(jobId).then(setJob)
    api.listCandidates(jobId, { min_score: minScore }).then(setCandidates)
  }, [jobId, minScore])

  useEffect(() => {
    refresh()
  }, [refresh])

  async function handleFiles(files) {
    setBusy(true)
    setError(null)
    try {
      if (files.length === 1) {
        await api.analyzeSingle(jobId, files[0])
      } else {
        await api.analyzeBulk(jobId, files)
      }
      refresh()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleStatusChange(candidateId, status) {
    setCandidates((prev) => prev.map((c) => (c.id === candidateId ? { ...c, status } : c)))
    await api.updateStatus(candidateId, status)
  }

  if (!job) return <div className="max-w-6xl mx-auto px-6 py-10 text-ink-600 font-mono text-sm">Loading…</div>

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      <Link to="/" className="text-xs font-mono text-ink-600 hover:text-amber transition-colors">
        ← all jobs
      </Link>

      <div className="grid lg:grid-cols-[320px_1fr] gap-6 mt-4">
        {/* Job description panel */}
        <aside className="card p-5 h-fit lg:sticky lg:top-24">
          <h1 className="font-display font-semibold text-lg text-paper-100">{job.title}</h1>
          <p className="text-sm text-ink-600 mt-3 whitespace-pre-wrap leading-relaxed">{job.description}</p>
          <div className="scanline-divider my-4" />
          <p className="text-xs font-mono uppercase tracking-wide text-ink-600 mb-2">Must-have skills detected</p>
          <div className="flex flex-wrap gap-1.5">
            {job.must_have_skills.map((s) => (
              <span key={s} className="chip-neutral">
                {s}
              </span>
            ))}
          </div>
        </aside>

        {/* Upload + candidates */}
        <div className="flex flex-col gap-6">
          <UploadZone onFiles={handleFiles} busy={busy} />
          {error && <p className="text-rose text-sm font-mono">{error}</p>}

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-xs font-mono uppercase tracking-wide text-ink-600">
                {candidates.length} candidate{candidates.length !== 1 ? 's' : ''}
              </span>
              <input
                type="range"
                min="0"
                max="100"
                value={minScore}
                onChange={(e) => setMinScore(Number(e.target.value))}
                className="accent-amber w-32"
              />
              <span className="text-xs font-mono text-ink-600">min score {minScore}</span>
            </div>
            <a href={api.exportCsvUrl(jobId)} className="btn-secondary text-xs !px-3 !py-1.5">
              ↓ Export CSV
            </a>
          </div>

          <CandidateTable candidates={candidates} onStatusChange={handleStatusChange} />
        </div>
      </div>
    </div>
  )
}
