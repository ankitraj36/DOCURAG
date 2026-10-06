import { useState, useEffect } from 'react'
import { GitCompare, FileText, Loader, Sparkles } from 'lucide-react'
import { getDocuments, compareDocuments } from '../services/api'

export default function Compare() {
  const [docs, setDocs] = useState([])
  const [selected, setSelected] = useState([])
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    getDocuments({ page_size: 100 })
      .then((r) => setDocs(r.data.documents))
      .catch(() => {})
  }, [])

  const toggleSelect = (id) => {
    setSelected((prev) => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])
  }

  const handleCompare = async () => {
    if (selected.length < 2) return
    setLoading(true)
    try {
      const r = await compareDocuments({
        document_ids: selected,
        query: query || undefined,
      })
      setResult(r.data)
    } catch {
      setResult({ summary: 'Comparison failed. Please try again.', comparison_table: {} })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Document Comparison</h1>
        <p>Select two or more documents to compare with AI</p>
      </div>

      {/* Document Selection */}
      <div className="card" style={{ marginBottom: 24 }}>
        <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>
          Select Documents ({selected.length} selected)
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: 8 }}>
          {docs.map((doc) => (
            <label
              key={doc.id}
              style={{
                display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px',
                background: selected.includes(doc.id) ? 'rgba(99,102,241,0.12)' : 'var(--bg-tertiary)',
                border: `1px solid ${selected.includes(doc.id) ? 'var(--primary)' : 'var(--border)'}`,
                borderRadius: 8, cursor: 'pointer', fontSize: 14
              }}
            >
              <input type="checkbox" checked={selected.includes(doc.id)} onChange={() => toggleSelect(doc.id)} />
              <FileText size={16} style={{ color: 'var(--primary-light)' }} />
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {doc.original_filename}
              </span>
            </label>
          ))}
        </div>
        {docs.length === 0 && (
          <div style={{ color: 'var(--text-tertiary)', fontSize: 14 }}>
            No documents uploaded yet. Upload documents first.
          </div>
        )}
      </div>

      {/* Optional focus query */}
      <div className="card" style={{ marginBottom: 24 }}>
        <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6, display: 'block' }}>
          Comparison Focus (optional)
        </label>
        <input className="input" value={query} onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g., Compare the proposed methodologies and their results" />
        <button className="btn btn-primary" style={{ marginTop: 12 }} onClick={handleCompare}
          disabled={selected.length < 2 || loading}>
          {loading ? <><Loader size={16} className="animate-spin"/> Comparing...</> : <><GitCompare size={16}/> Compare Documents</>}
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className="card" style={{ borderLeft: '3px solid var(--accent)' }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Sparkles size={18} style={{color:'var(--accent)'}}/> Comparison Result
          </h3>
          <div style={{ fontSize: 14, lineHeight: 1.8, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap' }}>
            {result.summary}
          </div>

          {result.comparison_table && Object.keys(result.comparison_table).length > 0 && (
            <div className="table-container" style={{ marginTop: 20 }}>
              <table>
                <thead>
                  <tr>
                    <th>Document</th>
                    <th>Content Preview</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(result.comparison_table).map(([name, data]) => (
                    <tr key={name}>
                      <td style={{ fontWeight: 600, whiteSpace: 'nowrap' }}>{name}</td>
                      <td style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                        {data.content_preview?.slice(0, 300)}...
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
