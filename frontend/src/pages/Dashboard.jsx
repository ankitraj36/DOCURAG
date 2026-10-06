import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  FileText, Layers, Hash, MessageSquare, Search,
  Clock, Upload, ArrowRight, TrendingUp
} from 'lucide-react'
import { getAnalytics } from '../services/api'

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getAnalytics()
      .then((r) => setData(r.data))
      .catch(() => setData({
        total_documents: 0, total_pages: 0, total_chunks: 0,
        total_questions: 0, total_searches: 0, avg_response_time_ms: 0,
        documents_by_type: {}, questions_over_time: [], most_searched_documents: []
      }))
      .finally(() => setLoading(false))
  }, [])

  const stats = data ? [
    { icon: FileText, label: 'Documents', value: data.total_documents, color: 'purple' },
    { icon: Layers, label: 'Pages Processed', value: data.total_pages, color: 'cyan' },
    { icon: Hash, label: 'Chunks Indexed', value: data.total_chunks, color: 'green' },
    { icon: MessageSquare, label: 'Questions Asked', value: data.total_questions, color: 'orange' },
    { icon: Search, label: 'Searches', value: data.total_searches, color: 'purple' },
    { icon: Clock, label: 'Avg Response', value: `${Math.round(data.avg_response_time_ms)}ms`, color: 'cyan' },
  ] : []

  const quickActions = [
    { to: '/upload', icon: Upload, label: 'Upload Documents', desc: 'Add new files for processing' },
    { to: '/chat', icon: MessageSquare, label: 'Ask AI', desc: 'Chat with your documents' },
    { to: '/search', icon: Search, label: 'Search', desc: 'Find information across files' },
    { to: '/evaluation', icon: TrendingUp, label: 'Evaluation', desc: 'View RAG performance metrics' },
  ]

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Overview of your document intelligence platform</p>
      </div>

      {/* Stats */}
      {loading ? (
        <div className="stats-grid">
          {[1,2,3,4,5,6].map(i => <div key={i} className="skeleton skeleton-card" style={{height:100}} />)}
        </div>
      ) : (
        <div className="stats-grid">
          {stats.map((s) => (
            <div className="stat-card" key={s.label}>
              <div className={`stat-icon ${s.color}`}><s.icon size={22} /></div>
              <div className="stat-content">
                <h3>{s.value}</h3>
                <p>{s.label}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Quick Actions */}
      <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>Quick Actions</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16, marginBottom: 32 }}>
        {quickActions.map((a) => (
          <Link to={a.to} key={a.to} className="card" style={{ textDecoration: 'none', color: 'inherit', display: 'flex', alignItems: 'center', gap: 16 }}>
            <div className="stat-icon purple"><a.icon size={22} /></div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 2 }}>{a.label}</div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{a.desc}</div>
            </div>
            <ArrowRight size={18} style={{ color: 'var(--text-tertiary)' }} />
          </Link>
        ))}
      </div>

      {/* Document Types */}
      {data && Object.keys(data.documents_by_type).length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Documents by Type</h3>
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            {Object.entries(data.documents_by_type).map(([type, count]) => (
              <div key={type} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span className={`file-badge ${type}`}>{type}</span>
                <span style={{ fontWeight: 600 }}>{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
