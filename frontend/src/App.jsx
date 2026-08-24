import { Routes, Route } from 'react-router-dom'
import TopBar from './components/TopBar.jsx'
import Dashboard from './pages/Dashboard.jsx'
import JobDetail from './pages/JobDetail.jsx'
import CandidateDetail from './pages/CandidateDetail.jsx'

export default function App() {
  return (
    <div className="min-h-screen">
      <TopBar />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/jobs/:jobId" element={<JobDetail />} />
        <Route path="/candidates/:candidateId" element={<CandidateDetail />} />
      </Routes>
    </div>
  )
}
