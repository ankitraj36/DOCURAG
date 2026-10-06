import { useState, useEffect } from 'react'
import {
  FileBarChart, FileText, Loader, Sparkles,
  List, BookOpen, Calendar, Users, Target
} from 'lucide-react'
import { getDocuments, summarizeDocument } from '../services/api'

const summaryTypes = [
  { value: 'executive', label: 'Executive Summary' },
  { value: 'short', label: 'Short Summary' },
  { value: 'detailed', label: 'Detailed Summary' },
  { value: 'key_points', label: 'Key Points' },
]

export default function Summarize() {
  const [docs, setDocs] = useState([])
  const [selectedDoc, setSelectedDoc] = useState('')
  const [summaryType, setSummaryType] = useState('detailed')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    getDocuments({ page_size: 100 })
      .then((r) => setDocs(r.data.documents))
      .catch(() => {})
  }, [])

  const handleSummarize = async () => {
    if (!selectedDoc) return
    setLoading(true)
    try {
      const r = await summarizeDocument({ document_id: selectedDoc, summary_type: summaryType })
      setResult(r.data)
    } catch {
      setResult({ summary: 'Summarization failed. Please try again.', key_points: [] })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Document Summary</h1>
        <p>Generate AI-powered summaries of your documents</p>
      </div>

      {/* Controls */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 16, alignItems: 'end' }}>
          <div>
            <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6, display: 'block' }}>
              Select Document
            </label>
            <select className="input" value={selectedDoc} onChange={(e) => setSelectedDoc(e.target.value)}>
              <option value="">Choose a document...</option>
              {docs.map((d) => (
                <option key={d.id} value={d.id}>{d.original_filename}</option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6, display: 'block' }}>
              Summary Type
            </label>
            <select className="input" value={summaryType} onChange={(e) => setSummaryType(e.target.value)}>
              {summaryTypes.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
          <button className="btn btn-primary" onClick={handleSummarize} disabled={!selectedDoc || loading}>
            {loading ? <><Loader size={16} className="animate-spin"/> Summarizing...</> : <><Sparkles size={16}/> Summarize</>}
          </button>
        </div>
      </div>

      {/* Result */}
      {result && (
        <div>
          <div className="card" style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
              <FileBarChart size={20} style={{ color: 'var(--primary-light)' }} />
              <h3 style={{ fontSize: 16, fontWeight: 600 }}>
                {result.document_name} — {summaryTypes.find(t => t.value === summaryType)?.label}
              </h3>
            </div>
            <div style={{ fontSize: 14, lineHeight: 1.8, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap' }}>
              {result.summary}
            </div>
          </div>

          {result.key_points && result.key_points.length > 0 && (
            <div className="card" style={{ marginBottom: 16 }}>
              <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
                <List size={16}/> Key Points
              </h3>
              {result.key_points.map((p, i) => (
                <div key={i} style={{ fontSize: 14, color: 'var(--text-secondary)', padding: '6px 0', display: 'flex', gap: 8 }}>
                  <Target size={14} style={{ color: 'var(--primary-light)', flexShrink: 0, marginTop: 3 }} /> {p}
                </div>
              ))}
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            {result.entities && result.entities.length > 0 && (
              <div className="card">
                <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}><Users size={14} style={{verticalAlign:-2}}/> Entities</h3>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {result.entities.map((e, i) => <span key={i} className="badge badge-info">{e}</span>)}
                </div>
              </div>
            )}
            {result.important_dates && result.important_dates.length > 0 && (
              <div className="card">
                <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}><Calendar size={14} style={{verticalAlign:-2}}/> Important Dates</h3>
                {result.important_dates.map((d, i) => (
                  <div key={i} style={{ fontSize: 13, color: 'var(--text-secondary)', padding: '2px 0' }}>{d}</div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
