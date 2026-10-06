import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  FileText, Search, MessageSquare, Trash2, RefreshCw,
  Eye, Filter, Plus, CheckCircle, Clock, AlertCircle, Loader
} from 'lucide-react'
import { getDocuments, deleteDocument } from '../services/api'

const statusIcon = {
  processed: <CheckCircle size={14} style={{ color: 'var(--success)' }} />,
  processing: <Loader size={14} className="animate-spin" style={{ color: 'var(--warning)' }} />,
  pending: <Clock size={14} style={{ color: 'var(--text-tertiary)' }} />,
  failed: <AlertCircle size={14} style={{ color: 'var(--error)' }} />,
}

const filters = ['All', 'PDF', 'DOCX', 'PPTX', 'TXT', 'Images', 'Processed', 'Processing', 'Failed']

export default function Documents() {
  const [docs, setDocs] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [activeFilter, setActiveFilter] = useState('All')

  const fetchDocs = (filter = 'All') => {
    setLoading(true)
    const params = { page: 1, page_size: 50 }
    if (['PDF','DOCX','PPTX','TXT'].includes(filter)) params.file_type = filter.toLowerCase()
    if (filter === 'Images') params.file_type = 'jpg'
    if (['Processed','Processing','Failed'].includes(filter)) params.status = filter.toLowerCase()
    getDocuments(params)
      .then((r) => { setDocs(r.data.documents); setTotal(r.data.total) })
      .catch(() => { setDocs([]); setTotal(0) })
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchDocs(activeFilter) }, [activeFilter])

  const handleDelete = async (id) => {
    if (!confirm('Delete this document?')) return
    await deleteDocument(id)
    fetchDocs(activeFilter)
  }

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>Document Library</h1>
          <p>{total} documents uploaded</p>
        </div>
        <Link to="/upload" className="btn btn-primary"><Plus size={18} /> Upload</Link>
      </div>

      {/* Filters */}
      <div className="filter-tabs">
        {filters.map((f) => (
          <button key={f} className={`filter-tab${activeFilter === f ? ' active' : ''}`}
            onClick={() => setActiveFilter(f)}>{f}</button>
        ))}
      </div>

      {/* Documents */}
      {loading ? (
        <div className="doc-grid">
          {[1,2,3,4].map(i => <div key={i} className="skeleton skeleton-card" style={{height:180}} />)}
        </div>
      ) : docs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon"><FileText size={32} /></div>
          <h3>No documents yet</h3>
          <p>Upload your first document to get started with AI-powered analysis.</p>
          <Link to="/upload" className="btn btn-primary"><Plus size={18} /> Upload Document</Link>
        </div>
      ) : (
        <div className="doc-grid">
          {docs.map((doc) => (
            <div className="doc-card" key={doc.id}>
              <div className="doc-card-header">
                <div className="doc-card-title">
                  <FileText size={18} style={{ color: 'var(--primary-light)' }} />
                  <span style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {doc.original_filename}
                  </span>
                </div>
                <span className={`file-badge ${doc.file_type}`}>{doc.file_type}</span>
              </div>

              <div className="doc-card-meta">
                <span className="doc-meta-item">{statusIcon[doc.status]} {doc.status}</span>
                <span className="doc-meta-item">{doc.num_pages} pages</span>
                <span className="doc-meta-item">{doc.num_words.toLocaleString()} words</span>
                {doc.num_tables > 0 && <span className="doc-meta-item">{doc.num_tables} tables</span>}
                {doc.num_images > 0 && <span className="doc-meta-item">{doc.num_images} images</span>}
                <span className="doc-meta-item">{doc.num_chunks} chunks</span>
              </div>
              {doc.ocr_applied && <span className="badge badge-info" style={{marginTop:8}}>OCR Applied</span>}

              <div className="doc-card-actions">
                <Link to={`/documents/${doc.id}`} className="btn btn-sm btn-secondary"><Eye size={14} /> View</Link>
                <Link to={`/search?doc=${doc.id}`} className="btn btn-sm btn-ghost"><Search size={14} /> Search</Link>
                <Link to={`/chat?doc=${doc.id}`} className="btn btn-sm btn-ghost"><MessageSquare size={14} /> Ask</Link>
                <button className="btn btn-sm btn-danger" onClick={() => handleDelete(doc.id)}><Trash2 size={14} /></button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
