import { Link } from 'react-router-dom'

export default function JobCard({ job }) {
  return (
    <Link
      to={`/jobs/${job.id}`}
      className="card p-5 hover:border-amber/50 transition-colors group flex flex-col gap-3"
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-display font-semibold text-paper-100 group-hover:text-amber transition-colors">
          {job.title}
        </h3>
        <span className="chip-neutral shrink-0">{job.candidate_count} screened</span>
      </div>
      <p className="text-sm text-ink-600 line-clamp-2 flex-1">{job.description}</p>
      <div className="flex flex-wrap gap-1.5">
        {job.must_have_skills.slice(0, 5).map((s) => (
          <span key={s} className="chip-neutral !text-[10px] !py-0.5">
            {s}
          </span>
        ))}
        {job.must_have_skills.length > 5 && (
          <span className="text-[10px] text-ink-600 self-center">+{job.must_have_skills.length - 5} more</span>
        )}
      </div>
    </Link>
  )
}
