import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Send, Bot, User, FileText, Sparkles, Plus,
  ChevronRight, BookOpen, Loader
} from 'lucide-react'
import { sendChatMessage, getConversations, getConversationMessages } from '../services/api'

export default function Chat() {
  const [searchParams] = useSearchParams()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const [conversations, setConversations] = useState([])
  const [docId] = useState(searchParams.get('doc'))
  const messagesEnd = useRef(null)

  useEffect(() => {
    getConversations().then((r) => setConversations(r.data)).catch(() => {})
  }, [])

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadConversation = async (id) => {
    try {
      const r = await getConversationMessages(id)
      setMessages(r.data.map(m => ({
        role: m.role, content: m.content,
        citations: m.citations, confidence: m.confidence_score
      })))
      setConversationId(id)
    } catch {}
  }

  const handleSend = async () => {
    if (!input.trim() || loading) return
    const query = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: query }])
    setLoading(true)

    try {
      const r = await sendChatMessage({
        query,
        conversation_id: conversationId,
        document_ids: docId ? [docId] : undefined,
      })
      const d = r.data
      setConversationId(d.conversation_id)
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: d.answer,
        citations: d.citations,
        confidence: d.confidence_score,
        related: d.related_questions,
        responseTime: d.response_time_ms,
        chunks: d.retrieved_chunks,
      }])
    } catch (err) {
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: 'Sorry, an error occurred. Please check that the backend server is running.',
      }])
    } finally {
      setLoading(false)
    }
  }

  const newChat = () => {
    setMessages([])
    setConversationId(null)
    setInput('')
  }

  const confLevel = (score) => {
    if (score >= 0.7) return 'high'
    if (score >= 0.4) return 'medium'
    return 'low'
  }

  return (
    <div style={{ display: 'flex', gap: 0, height: 'calc(100vh - 96px)', margin: '-32px -32px', padding: 0 }}>
      {/* Sidebar */}
      <div style={{
        width: 260, borderRight: '1px solid var(--border)', background: 'var(--bg-secondary)',
        display: 'flex', flexDirection: 'column', flexShrink: 0
      }}>
        <div style={{ padding: 16 }}>
          <button className="btn btn-primary" style={{ width: '100%' }} onClick={newChat}>
            <Plus size={16} /> New Chat
          </button>
        </div>
        <div style={{ flex: 1, overflow: 'auto', padding: '0 8px' }}>
          {conversations.map((c) => (
            <div key={c.id}
              onClick={() => loadConversation(c.id)}
              style={{
                padding: '10px 12px', borderRadius: 8, cursor: 'pointer', marginBottom: 4,
                background: conversationId === c.id ? 'var(--bg-hover)' : 'transparent',
                fontSize: 13, color: 'var(--text-secondary)', overflow: 'hidden',
                textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}
            >
              <MessageIcon /> {c.title}
            </div>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Messages */}
        <div style={{ flex: 1, overflow: 'auto', padding: '24px 32px' }}>
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', paddingTop: 80 }}>
              <div style={{
                width: 72, height: 72, borderRadius: 20, margin: '0 auto 20px',
                background: 'var(--gradient-brand)', display: 'flex', alignItems: 'center', justifyContent: 'center'
              }}>
                <Sparkles size={32} color="white" />
              </div>
              <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Ask DocuRAG</h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: 15, maxWidth: 400, margin: '0 auto' }}>
                Ask any question about your uploaded documents. Get evidence-grounded answers with citations.
              </p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`chat-message ${msg.role}`}>
              <div className={`chat-avatar ${msg.role === 'assistant' ? 'ai' : 'user-avatar'}`}>
                {msg.role === 'assistant' ? <Bot size={18} /> : <User size={18} />}
              </div>
              <div>
                <div className={`chat-bubble`}>
                  <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
                </div>

                {/* Citations */}
                {msg.citations && msg.citations.length > 0 && (
                  <div style={{ marginTop: 12, maxWidth: '75%' }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-tertiary)', marginBottom: 6 }}>
                      <BookOpen size={12} style={{ display: 'inline', verticalAlign: -2 }} /> Sources
                    </div>
                    {msg.citations.map((c, j) => (
                      <div key={j} className="citation-card">
                        <div className="citation-label">
                          <FileText size={12} />
                          {c.document_name} · Page {c.page_number || 'N/A'}
                        </div>
                        <div className="citation-text">{c.content?.slice(0, 200)}...</div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Confidence */}
                {msg.confidence != null && (
                  <div className="confidence-meter" style={{ maxWidth: '75%' }}>
                    <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Confidence</span>
                    <div className="confidence-bar">
                      <div
                        className={`confidence-fill ${confLevel(msg.confidence)}`}
                        style={{ width: `${msg.confidence * 100}%` }}
                      />
                    </div>
                    <span className={`confidence-label`} style={{
                      color: msg.confidence >= 0.7 ? 'var(--success)' : msg.confidence >= 0.4 ? 'var(--warning)' : 'var(--error)'
                    }}>
                      {Math.round(msg.confidence * 100)}%
                    </span>
                  </div>
                )}

                {/* Related Questions */}
                {msg.related && msg.related.length > 0 && (
                  <div style={{ marginTop: 12, maxWidth: '75%' }}>
                    <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 6 }}>Related questions</div>
                    {msg.related.map((q, j) => (
                      <button key={j} className="btn btn-sm btn-secondary" style={{ marginRight: 6, marginBottom: 6 }}
                        onClick={() => { setInput(q) }}>
                        {q} <ChevronRight size={14} />
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="chat-message assistant">
              <div className="chat-avatar ai"><Bot size={18} /></div>
              <div className="chat-bubble" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Loader size={16} className="animate-spin" /> Thinking...
              </div>
            </div>
          )}
          <div ref={messagesEnd} />
        </div>

        {/* Input */}
        <div style={{ padding: '16px 32px', borderTop: '1px solid var(--border)' }}>
          <div className="chat-input-wrapper">
            <input
              className="input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="Ask a question about your documents..."
              disabled={loading}
            />
            <button className="btn btn-primary" onClick={handleSend} disabled={loading || !input.trim()}>
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function MessageIcon() {
  return <FileText size={14} style={{ display: 'inline', verticalAlign: -2, marginRight: 6 }} />
}
