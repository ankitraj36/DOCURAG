import { Link } from 'react-router-dom'
import {
  Sparkles, FileText, Search, MessageSquare, Image,
  GitCompare, Shield, BarChart3, ArrowRight, Zap, Brain, Eye
} from 'lucide-react'

const features = [
  { icon: FileText, color: '#6366f1', title: 'Multimodal RAG', desc: 'Understand text, tables, images, charts, and scanned content from PDFs, DOCX, PPTX, and images.' },
  { icon: Search, color: '#06b6d4', title: 'Hybrid Search', desc: 'Combine keyword (BM25) and semantic vector search with intelligent reranking for precise results.' },
  { icon: Eye, color: '#8b5cf6', title: 'OCR & Vision', desc: 'Extract text from scanned documents and analyze charts, diagrams, and images using AI vision.' },
  { icon: MessageSquare, color: '#10b981', title: 'AI Chat with Citations', desc: 'Ask natural-language questions and get answers grounded in your documents with page-level citations.' },
  { icon: GitCompare, color: '#f59e0b', title: 'Document Comparison', desc: 'Compare multiple documents side-by-side with AI-generated comparison tables and insights.' },
  { icon: Shield, color: '#ef4444', title: 'Hallucination Control', desc: 'Every answer is evidence-grounded. No fabricated information — only what exists in your documents.' },
  { icon: Brain, color: '#ec4899', title: 'Page Explanation', desc: 'Click "Explain This Page" to get AI analysis of text, tables, charts, and diagrams on any page.' },
  { icon: BarChart3, color: '#14b8a6', title: 'RAG Evaluation', desc: 'Real evaluation metrics — Precision@K, Recall, MRR, Faithfulness, and Answer Relevance.' },
  { icon: Zap, color: '#f97316', title: 'Production Architecture', desc: 'FastAPI backend, React frontend, FAISS vectors, PostgreSQL storage — ready for deployment.' },
]

export default function Landing() {
  return (
    <div style={{ background: 'var(--bg-primary)', minHeight: '100vh' }}>
      {/* Hero */}
      <div className="landing-hero">
        <div className="landing-badge">
          <Sparkles size={14} />
          AI-Powered Document Intelligence
        </div>
        <h1>
          Understand Your Documents<br />
          Like Never <span>Before</span>
        </h1>
        <p>
          DocuRAG extracts knowledge from text, images, tables, charts, and scanned documents,
          then produces evidence-grounded answers with page-level citations.
        </p>
        <div className="landing-actions">
          <Link to="/dashboard" className="btn btn-primary btn-lg">
            Get Started <ArrowRight size={18} />
          </Link>
          <Link to="/upload" className="btn btn-secondary btn-lg">
            Upload Documents
          </Link>
        </div>
      </div>

      {/* Features */}
      <div style={{ padding: '0 24px 80px' }}>
        <h2 style={{
          textAlign: 'center', fontSize: 32, fontWeight: 700,
          letterSpacing: '-0.02em', marginBottom: 12
        }}>
          Everything You Need
        </h2>
        <p style={{
          textAlign: 'center', color: 'var(--text-secondary)',
          fontSize: 16, marginBottom: 48, maxWidth: 500, margin: '0 auto 48px'
        }}>
          A complete multimodal RAG platform with enterprise-grade features.
        </p>
        <div className="landing-features">
          {features.map((f) => (
            <div className="feature-card" key={f.title}>
              <div className="feature-icon" style={{ background: `${f.color}20`, color: f.color }}>
                <f.icon size={24} />
              </div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div style={{
        borderTop: '1px solid var(--border)', padding: '32px 24px',
        textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13
      }}>
        DocuRAG · AI-Powered Multimodal Document & Image Search & Analysis · Built for Hackathon 2026
      </div>
    </div>
  )
}
