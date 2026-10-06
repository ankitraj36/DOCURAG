import { useState } from 'react'
import {
  Upload, Image, Search, Loader, Eye, FileText, Sparkles
} from 'lucide-react'
import { analyzeImage } from '../services/api'

export default function ImageAnalysis() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [query, setQuery] = useState('Describe this image in detail. If it contains a chart, extract the data. If it contains a table, extract the information. If it contains a diagram, explain the components.')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleFile = (f) => {
    setFile(f)
    setResult(null)
    const reader = new FileReader()
    reader.onload = (e) => setPreview(e.target.result)
    reader.readAsDataURL(f)
  }

  const handleAnalyze = async () => {
    if (!file) return
    setLoading(true)
    try {
      const r = await analyzeImage(file, query)
      setResult(r.data)
    } catch {
      setResult({ analysis: 'Analysis failed. Please check backend connection.', confidence_score: 0 })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Image & Chart Analysis</h1>
        <p>Upload images, charts, diagrams, or scanned documents for AI analysis</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Left: Upload */}
        <div>
          <div
            className={`dropzone`}
            onClick={() => document.getElementById('img-input').click()}
            style={{ marginBottom: 16 }}
          >
            <div className="dropzone-icon"><Image size={28} /></div>
            <h3>Drop an image here</h3>
            <p>JPG, PNG, BMP, TIFF, WebP</p>
            <input
              id="img-input" type="file" accept="image/*" style={{ display: 'none' }}
              onChange={(e) => e.target.files[0] && handleFile(e.target.files[0])}
            />
          </div>

          {preview && (
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <img src={preview} alt="Preview" style={{ width: '100%', maxHeight: 400, objectFit: 'contain', background: '#000' }} />
            </div>
          )}

          <div style={{ marginTop: 16 }}>
            <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6, display: 'block' }}>
              Ask about this image
            </label>
            <textarea
              className="input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              rows={3}
              style={{ resize: 'vertical' }}
            />
            <button
              className="btn btn-primary" style={{ marginTop: 12, width: '100%' }}
              onClick={handleAnalyze} disabled={!file || loading}
            >
              {loading ? <><Loader size={16} className="animate-spin"/> Analyzing...</> : <><Sparkles size={16}/> Analyze Image</>}
            </button>
          </div>
        </div>

        {/* Right: Results */}
        <div>
          {result ? (
            <div>
              <div className="card" style={{ marginBottom: 16 }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Eye size={18} style={{ color: 'var(--primary-light)' }} /> Analysis Result
                </h3>
                <div style={{ fontSize: 14, lineHeight: 1.8, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap' }}>
                  {result.analysis}
                </div>
              </div>

              {result.ocr_text && (
                <div className="card" style={{ marginBottom: 16 }}>
                  <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>
                    <FileText size={14} style={{ verticalAlign: -2 }} /> Extracted Text (OCR)
                  </h3>
                  <div style={{ fontSize: 13, color: 'var(--text-tertiary)', whiteSpace: 'pre-wrap', fontFamily: 'monospace', background: 'var(--bg-tertiary)', padding: 12, borderRadius: 8 }}>
                    {result.ocr_text}
                  </div>
                </div>
              )}

              {result.detected_elements && result.detected_elements.length > 0 && (
                <div className="card" style={{ marginBottom: 16 }}>
                  <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>Detected Elements</h3>
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    {result.detected_elements.map((e, i) => (
                      <span key={i} className="badge badge-info">{e}</span>
                    ))}
                  </div>
                </div>
              )}

              <div className="confidence-meter">
                <span style={{ fontSize: 13 }}>Confidence</span>
                <div className="confidence-bar" style={{ maxWidth: 200 }}>
                  <div className={`confidence-fill ${result.confidence_score >= 0.7 ? 'high' : result.confidence_score >= 0.4 ? 'medium' : 'low'}`}
                    style={{ width: `${result.confidence_score * 100}%` }} />
                </div>
                <span style={{ fontSize: 13, fontWeight: 600 }}>{Math.round(result.confidence_score * 100)}%</span>
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon"><Image size={32} /></div>
              <h3>Upload an image to analyze</h3>
              <p>Supports charts, graphs, diagrams, tables, screenshots, and scanned documents.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
