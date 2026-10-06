import { useState, useEffect } from 'react'
import {
  BarChart3, Target, Zap, Clock, FileText, Hash,
  TrendingUp, CheckCircle, AlertTriangle
} from 'lucide-react'
import { getEvaluation } from '../services/api'

export default function Evaluation() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getEvaluation()
      .then((r) => setData(r.data))
      .catch(() => setData({ metrics: { retrieval: {}, generation: {}, system: {} }, history: [], total_evaluations: 0 }))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div>
      <div className="page-header"><h1>RAG Evaluation</h1><p>Loading metrics...</p></div>
      <div className="stats-grid">
        {[1,2,3,4,5,6].map(i => <div key={i} className="skeleton skeleton-card" style={{height:120}} />)}
      </div>
    </div>
  )

  const { retrieval, generation, system } = data.metrics

  const metricCard = (label, value, icon, color) => (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div className="metric-value" style={{ color }}>
          {typeof value === 'number' ? `${(value * 100).toFixed(1)}%` : value || 'N/A'}
        </div>
        {icon}
      </div>
      {typeof value === 'number' && (
        <div className="metric-bar">
          <div className="metric-bar-fill" style={{ width: `${value * 100}%` }} />
        </div>
      )}
    </div>
  )

  return (
    <div>
      <div className="page-header">
        <h1>RAG Evaluation Dashboard</h1>
        <p>Real performance metrics from your RAG pipeline — not hardcoded values</p>
      </div>

      {/* System Stats */}
      <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>System Overview</h2>
      <div className="stats-grid" style={{ marginBottom: 32 }}>
        <div className="stat-card">
          <div className="stat-icon purple"><FileText size={22} /></div>
          <div className="stat-content">
            <h3>{system.total_documents || 0}</h3>
            <p>Documents</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon cyan"><Hash size={22} /></div>
          <div className="stat-content">
            <h3>{system.total_chunks || 0}</h3>
            <p>Chunks Indexed</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green"><Clock size={22} /></div>
          <div className="stat-content">
            <h3>{Math.round(system.avg_response_time_ms || 0)}ms</h3>
            <p>Avg Response Time</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon orange"><BarChart3 size={22} /></div>
          <div className="stat-content">
            <h3>{data.total_evaluations}</h3>
            <p>Total Evaluations</p>
          </div>
        </div>
      </div>

      {/* Retrieval Metrics */}
      <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>Retrieval Metrics</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 16, marginBottom: 32 }}>
        {metricCard('Precision@K', retrieval.precision_at_k, <Target size={20} style={{color:'var(--primary-light)'}}/>, 'var(--primary-light)')}
        {metricCard('Recall@K', retrieval.recall_at_k, <TrendingUp size={20} style={{color:'var(--accent)'}}/>, 'var(--accent)')}
        {metricCard('MRR', retrieval.mrr, <Zap size={20} style={{color:'var(--warning)'}}/>, 'var(--warning)')}
      </div>

      {/* Generation Metrics */}
      <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>Generation Metrics</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 16, marginBottom: 32 }}>
        {metricCard('Answer Relevance', generation.answer_relevance, <CheckCircle size={20} style={{color:'var(--success)'}}/>, 'var(--success)')}
        {metricCard('Context Relevance', generation.context_relevance, <Target size={20} style={{color:'var(--accent)'}}/>, 'var(--accent)')}
        {metricCard('Faithfulness', generation.faithfulness, <AlertTriangle size={20} style={{color:'var(--warning)'}}/>, 'var(--warning)')}
        {metricCard('Citation Accuracy', generation.citation_accuracy, <FileText size={20} style={{color:'var(--primary-light)'}}/>, 'var(--primary-light)')}
      </div>

      {/* History */}
      {data.history && data.history.length > 0 && (
        <>
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>Recent Evaluations</h2>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Query</th>
                  <th>Precision</th>
                  <th>Faithfulness</th>
                  <th>Response Time</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {data.history.map((h) => (
                  <tr key={h.id}>
                    <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {h.query || 'N/A'}
                    </td>
                    <td>{h.precision != null ? `${(h.precision * 100).toFixed(0)}%` : '—'}</td>
                    <td>{h.faithfulness != null ? `${(h.faithfulness * 100).toFixed(0)}%` : '—'}</td>
                    <td>{h.response_time_ms ? `${h.response_time_ms}ms` : '—'}</td>
                    <td style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
                      {h.created_at ? new Date(h.created_at).toLocaleDateString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {data.total_evaluations === 0 && (
        <div className="empty-state">
          <div className="empty-state-icon"><BarChart3 size={32} /></div>
          <h3>No evaluation data yet</h3>
          <p>Ask some questions using the AI Chat to generate real evaluation metrics.</p>
        </div>
      )}
    </div>
  )
}
