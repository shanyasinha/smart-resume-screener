const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options)
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch {
      /* response wasn't JSON */
    }
    throw new Error(detail)
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  listJobs: () => request('/jobs'),
  createJob: (title, description) =>
    request('/jobs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, description }),
    }),
  getJob: (jobId) => request(`/jobs/${jobId}`),
  deleteJob: (jobId) => request(`/jobs/${jobId}`, { method: 'DELETE' }),

  analyzeSingle: (jobId, file) => {
    const form = new FormData()
    form.append('file', file)
    return request(`/jobs/${jobId}/resumes/analyze`, { method: 'POST', body: form })
  },
  analyzeBulk: (jobId, files) => {
    const form = new FormData()
    files.forEach((f) => form.append('files', f))
    return request(`/jobs/${jobId}/resumes/analyze-bulk`, { method: 'POST', body: form })
  },

  listCandidates: (jobId, params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return request(`/jobs/${jobId}/candidates${qs ? `?${qs}` : ''}`)
  },
  getCandidate: (id) => request(`/candidates/${id}`),
  updateStatus: (id, status) =>
    request(`/candidates/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    }),
  deleteCandidate: (id) => request(`/candidates/${id}`, { method: 'DELETE' }),
  exportCsvUrl: (jobId) => `${BASE}/jobs/${jobId}/candidates/export.csv`,
}
