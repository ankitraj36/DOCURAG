import { useState } from 'react'
import { Settings as SettingsIcon, Key, Database, Server, Save, CheckCircle } from 'lucide-react'

export default function Settings() {
  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  return (
    <div>
      <div className="page-header">
        <h1>Settings</h1>
        <p>Configure your DocuRAG instance</p>
      </div>

      {saved && (
        <div className="toast toast-success" style={{ position: 'fixed', top: 20, right: 20, zIndex: 9999 }}>
          <CheckCircle size={18} /> Settings saved successfully
        </div>
      )}

      {/* API Configuration */}
      <div className="card" style={{ marginBottom: 24 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Key size={18} style={{ color: 'var(--primary-light)' }} /> API Configuration
        </h3>
        <div className="input-group">
          <label>OpenAI API Key</label>
          <input className="input" type="password" placeholder="sk-..." defaultValue="" />
          <span style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 4, display: 'block' }}>
            Required for LLM-powered answers. Without it, extractive answers are used.
          </span>
        </div>
        <div className="input-group">
          <label>LLM Model</label>
          <select className="input" defaultValue="gpt-4o">
            <option value="gpt-4o">GPT-4o</option>
            <option value="gpt-4o-mini">GPT-4o Mini</option>
            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
          </select>
        </div>
        <div className="input-group">
          <label>Embedding Model</label>
          <input className="input" defaultValue="all-MiniLM-L6-v2" />
        </div>
      </div>

      {/* Processing Settings */}
      <div className="card" style={{ marginBottom: 24 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Database size={18} style={{ color: 'var(--accent)' }} /> Processing Settings
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="input-group">
            <label>Chunk Size (words)</label>
            <input className="input" type="number" defaultValue={512} />
          </div>
          <div className="input-group">
            <label>Chunk Overlap (words)</label>
            <input className="input" type="number" defaultValue={50} />
          </div>
          <div className="input-group">
            <label>Top-K Retrieval</label>
            <input className="input" type="number" defaultValue={10} />
          </div>
          <div className="input-group">
            <label>Rerank Top-K</label>
            <input className="input" type="number" defaultValue={5} />
          </div>
        </div>
        <div className="input-group">
          <label>OCR Engine</label>
          <select className="input" defaultValue="tesseract">
            <option value="tesseract">Tesseract</option>
            <option value="paddleocr">PaddleOCR</option>
          </select>
        </div>
      </div>

      {/* Server Info */}
      <div className="card" style={{ marginBottom: 24 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Server size={18} style={{ color: 'var(--success)' }} /> Server Information
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          {[
            ['Backend URL', 'http://localhost:8000'],
            ['Vector Store', 'FAISS (local)'],
            ['Database', 'SQLite (dev) / PostgreSQL (prod)'],
            ['Version', 'v1.0.0'],
          ].map(([label, value]) => (
            <div key={label} style={{ fontSize: 14 }}>
              <span style={{ color: 'var(--text-tertiary)' }}>{label}: </span>
              <span style={{ fontWeight: 500 }}>{value}</span>
            </div>
          ))}
        </div>
      </div>

      <button className="btn btn-primary" onClick={handleSave}>
        <Save size={16} /> Save Settings
      </button>
    </div>
  )
}
