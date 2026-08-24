import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api.js'
import JobCard from '../components/JobCard.jsx'

export default function Dashboard() {
  const [jobs, setJobs] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.listJobs().then(setJobs).catch((e) => setError(e.message))
  }, [])

  async function handleCreate(e) {
    e.preventDefault()
    setCreating(true)
    setError(null)
    try {
      const job = await api.createJob(title, description)
      navigate(`/jobs/${job.id}`)
    } catch (e) {
      setError(e.message)
      setCreating(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-paper-100">Job openings</h1>
          <p className="text-ink-600 text-sm mt-1">Create a role, then screen resumes against it.</p>
        </div>
        <button className="btn-primary" onClick={() => setShowForm((s) => !s)}>
          {showForm ? 'Cancel' : '+ New job'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="card p-6 mb-8 flex flex-col gap-4">
          <div>
            <label className="text-xs font-mono uppercase tracking-wide text-ink-600 mb-1.5 block">
              Job title
            </label>
            <input
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Senior Backend Engineer"
              className="input-field"
            />
          </div>
          <div>
            <label className="text-xs font-mono uppercase tracking-wide text-ink-600 mb-1.5 block">
              Job description
            </label>
            <textarea
              required
              rows={6}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Paste the full job description, including required skills and experience…"
              className="input-field resize-y"
            />
          </div>
          {error && <p className="text-rose text-sm font-mono">{error}</p>}
          <button className="btn-primary self-start" disabled={creating}>
            {creating ? 'Creating…' : 'Create job'}
          </button>
        </form>
      )}

      {jobs === null && <p className="text-ink-600 font-mono text-sm">Loading…</p>}
      {jobs && jobs.length === 0 && !showForm && (
        <div className="card p-12 text-center text-ink-600">
          <p className="font-mono text-sm">No job openings yet. Create one to start screening resumes.</p>
        </div>
      )}
      {jobs && jobs.length > 0 && (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {jobs.map((job) => (
            <JobCard key={job.id} job={job} />
          ))}
        </div>
      )}
    </div>
  )
}
