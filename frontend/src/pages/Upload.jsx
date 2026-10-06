import { useState, useCallback } from 'react'
import { Upload as UploadIcon, File, CheckCircle, AlertCircle, X } from 'lucide-react'
import { uploadDocument } from '../services/api'

export default function Upload() {
  const [files, setFiles] = useState([])
  const [dragOver, setDragOver] = useState(false)

  const ALLOWED = ['.pdf','.docx','.pptx','.txt','.jpg','.jpeg','.png']

  const addFiles = (fileList) => {
    const newFiles = Array.from(fileList).map((f) => ({
      file: f,
      id: Math.random().toString(36).slice(2),
      progress: 0,
      status: 'pending', // pending | uploading | success | error
      result: null,
      error: null,
    }))
    setFiles((prev) => [...prev, ...newFiles])
    newFiles.forEach((nf) => uploadFile(nf))
  }

  const uploadFile = async (fileEntry) => {
    setFiles((prev) => prev.map((f) => f.id === fileEntry.id ? { ...f, status: 'uploading' } : f))
    try {
      const res = await uploadDocument(fileEntry.file, (progress) => {
        setFiles((prev) => prev.map((f) => f.id === fileEntry.id ? { ...f, progress } : f))
      })
      setFiles((prev) => prev.map((f) => f.id === fileEntry.id ? { ...f, status: 'success', result: res.data, progress: 100 } : f))
    } catch (err) {
      setFiles((prev) => prev.map((f) => f.id === fileEntry.id ? { ...f, status: 'error', error: err.message, progress: 0 } : f))
    }
  }

  const removeFile = (id) => setFiles((prev) => prev.filter((f) => f.id !== id))

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
    addFiles(e.dataTransfer.files)
  }, [])

  return (
    <div>
      <div className="page-header">
        <h1>Upload Documents</h1>
        <p>Upload PDFs, DOCX, PPTX, TXT files, or images for AI analysis</p>
      </div>

      {/* Dropzone */}
      <div
        className={`dropzone${dragOver ? ' dragover' : ''}`}
        onClick={() => document.getElementById('file-input').click()}
        onDrop={onDrop}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
      >
        <div className="dropzone-icon"><UploadIcon size={28} /></div>
        <h3>Drop files here or click to browse</h3>
        <p>Supports PDF, DOCX, PPTX, TXT, JPG, PNG · Max 50MB per file</p>
        <input
          id="file-input"
          type="file"
          multiple
          accept={ALLOWED.join(',')}
          style={{ display: 'none' }}
          onChange={(e) => addFiles(e.target.files)}
        />
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>
            Uploads ({files.filter(f => f.status === 'success').length}/{files.length} complete)
          </h3>
          {files.map((f) => (
            <div key={f.id} className="card" style={{ marginBottom: 12, padding: 16, display: 'flex', alignItems: 'center', gap: 16 }}>
              <File size={24} style={{ color: 'var(--primary-light)', flexShrink: 0 }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {f.file.name}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 6 }}>
                  {(f.file.size / 1024).toFixed(0)} KB
                  {f.result && ` · ID: ${f.result.id?.slice(0,8)}`}
                  {f.error && <span style={{ color: 'var(--error)' }}> · {f.error}</span>}
                </div>
                {f.status === 'uploading' && (
                  <div className="progress-bar">
                    <div className="progress-bar-fill" style={{ width: `${f.progress}%` }} />
                  </div>
                )}
              </div>
              <div style={{ flexShrink: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
                {f.status === 'success' && <CheckCircle size={20} style={{ color: 'var(--success)' }} />}
                {f.status === 'error' && <AlertCircle size={20} style={{ color: 'var(--error)' }} />}
                {f.status === 'uploading' && <div className="spinner" />}
                <button className="btn btn-icon btn-ghost" onClick={() => removeFile(f.id)}><X size={16} /></button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
