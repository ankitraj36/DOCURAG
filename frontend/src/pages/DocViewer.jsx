import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  ArrowLeft, FileText, Layers, Hash, Image, Table2,
  MessageSquare, Sparkles, Loader, CheckCircle
} from 'lucide-react'
import { getDocument, explainPage } from '../services/api'

export default function DocViewer() {
  const { id } = useParams()
  const [doc, setDoc] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedPage, setSelectedPage] = useState(1)
  const [explanation, setExplanation] = useState(null)
  const [explaining, setExplaining] = useState(false)

  useEffect(() => {
    getDocument(id)
      .then((r) => setDoc(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [id])

  const handleExplainPage = async () => {
    setExplaining(true)
    setExplanation(null)
    try {
      const r = await explainPage({ document_id: id, page_number: selectedPage })
      setExplanation(r.data)
    } catch {
      setExplanation({ summary: 'Could not generate explanation. Please try again.' })
    } finally {
      setExplaining(false)
    }
  }

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 100 }}>
      <div className="spinner spinner-lg" />
    </div>
  )

  if (!doc) return (
    <div className="empty-state">
      <h3>Document not found</h3>
      <Link to="/documents" className="btn btn-primary" style={{ marginTop: 12 }}>Back to Library</Link>
    </div>
  )

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <Link to="/documents" className="btn btn-icon btn-ghost"><ArrowLeft size={20} /></Link>
        <div style={{ flex: 1 }}>
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>{doc.original_filename}</h1>
          <div style={{ display: 'flex', gap: 16, marginTop: 4, flexWrap: 'wrap' }}>
            <span className="doc-meta-item"><CheckCircle size={14} style={{color:'var(--success)'}}/> {doc.status}</span>
            <span className="doc-meta-item"><Layers size={14}/> {doc.num_pages} pages</span>
            <span className="doc-meta-item"><Hash size={14}/> {doc.num_words.toLocaleString()} words</span>
            <span className="doc-meta-item"><Table2 size={14}/> {doc.num_tables} tables</span>
            <span className="doc-meta-item"><Image size={14}/> {doc.num_images} images</span>
            <span className="doc-meta-item">{doc.num_chunks} chunks</span>
          </div>
        </div>
        <Link to={`/chat?doc=${id}`} className="btn btn-primary"><MessageSquare size={16}/> Ask AI</Link>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: 24 }}>
        {/* Page Navigator */}
        <div className="card" style={{ padding: 12, maxHeight: 'calc(100vh - 240px)', overflow: 'auto' }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-tertiary)', marginBottom: 8, padding: '0 8px' }}>Pages</div>
          {doc.pages && doc.pages.map((p) => (
            <button
              key={p.page_number}
              onClick={() => { setSelectedPage(p.page_number); setExplanation(null) }}
              style={{
                display: 'block', width: '100%', padding: '8px 12px', textAlign: 'left',
                background: selectedPage === p.page_number ? 'rgba(99,102,241,0.12)' : 'transparent',
                color: selectedPage === p.page_number ? 'var(--primary-light)' : 'var(--text-secondary)',
                border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 13,
                fontFamily: 'var(--font-family)', marginBottom: 2,
              }}
            >
              Page {p.page_number}
              {p.has_tables && <Table2 size={12} style={{marginLeft:4, verticalAlign:-2}}/>}
              {p.has_images && <Image size={12} style={{marginLeft:4, verticalAlign:-2}}/>}
            </button>
          ))}
          {(!doc.pages || doc.pages.length === 0) && (
            <div style={{ fontSize: 13, color: 'var(--text-tertiary)', padding: 8 }}>
              No page data available. Document may still be processing.
            </div>
          )}
        </div>

        {/* Content Area */}
        <div>
          <div className="card" style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ fontSize: 16, fontWeight: 600 }}>Page {selectedPage}</h3>
              <button className="btn btn-primary btn-sm" onClick={handleExplainPage} disabled={explaining}>
                {explaining ? <Loader size={14} className="animate-spin"/> : <Sparkles size={14}/>}
                Explain This Page
              </button>
            </div>
            {doc.pages && doc.pages[selectedPage - 1] ? (
              <div style={{ fontSize: 14, lineHeight: 1.8, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap' }}>
                {doc.pages[selectedPage - 1].text_preview || 'No text content extracted for this page.'}
              </div>
            ) : (
              <div style={{ color: 'var(--text-tertiary)', fontSize: 14 }}>
                Page content not available.
              </div>
            )}
          </div>

          {/* Explanation */}
          {explanation && (
            <div className="card" style={{ borderLeft: '3px solid var(--primary)' }}>
              <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                <Sparkles size={18} style={{color:'var(--primary-light)'}}/> AI Page Explanation
              </h3>
              <div style={{ fontSize: 14, lineHeight: 1.8, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap' }}>
                {explanation.summary}
              </div>
              {explanation.tables_explained && explanation.tables_explained.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 4 }}>Tables</div>
                  {explanation.tables_explained.map((t, i) => (
                    <div key={i} style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>• {t}</div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
