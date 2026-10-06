import { useState } from 'react'
import { Search as SearchIcon, FileText, Filter, Clock, Loader } from 'lucide-react'
import { searchDocuments } from '../services/api'

export default function Search() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [searchTime, setSearchTime] = useState(0)

  const handleSearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    try {
      const r = await searchDocuments({ query: query.trim(), top_k: 20, use_hybrid: true })
      setResults(r.data.results)
      setSearchTime(r.data.search_time_ms)
    } catch {
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Search Documents</h1>
        <p>Hybrid keyword + semantic search across all your documents</p>
      </div>

      {/* Search Bar */}
      <div className="search-bar" style={{ maxWidth: '100%', marginBottom: 24 }}>
        <SearchIcon />
        <input
          className="input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Search for anything across your documents..."
        />
        <button className="btn btn-primary btn-sm" onClick={handleSearch} disabled={loading}>
          {loading ? <Loader size={14} className="animate-spin" /> : 'Search'}
        </button>
      </div>

      {/* Results */}
      {results !== null && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
              {results.length} results found
            </span>
            <span style={{ fontSize: 12, color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', gap: 4 }}>
              <Clock size={12} /> {searchTime}ms
            </span>
          </div>

          {results.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon"><SearchIcon size={32} /></div>
              <h3>No results found</h3>
              <p>Try different keywords or upload more documents.</p>
            </div>
          ) : (
            results.map((r, i) => (
              <div key={i} className="search-result">
                <div className="search-result-header">
                  <div className="search-result-title">
                    <FileText size={16} style={{ color: 'var(--primary-light)' }} />
                    {r.document_name}
                    {r.page_number && (
                      <span className="badge badge-neutral">Page {r.page_number}</span>
                    )}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span className={`file-badge ${r.content_type}`}>{r.content_type}</span>
                    <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
                      Score: {r.score.toFixed(4)}
                    </span>
                  </div>
                </div>
                <div className="search-result-content">
                  {r.content.slice(0, 400)}
                  {r.content.length > 400 && '...'}
                </div>
                {r.highlights && r.highlights.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    {r.highlights.map((h, j) => (
                      <div key={j} style={{
                        fontSize: 13, color: 'var(--text-secondary)', padding: '4px 8px',
                        borderLeft: '2px solid var(--primary)', marginTop: 4, background: 'var(--bg-tertiary)',
                        borderRadius: '0 4px 4px 0'
                      }}>
                        ...{h}...
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
