# 🧠 DocuRAG — AI-Powered Multimodal Document & Image Search & Analysis

<p align="center">
  <strong>DocuRAG understands and retrieves information from text, images, tables, charts, and scanned documents, then produces evidence-grounded answers with page-level citations.</strong>
</p>

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 📄 **Multimodal RAG** | Understands text, tables, images, charts, and scanned content |
| 🔍 **Hybrid Search** | BM25 keyword + FAISS semantic vector search with RRF reranking |
| 👁️ **OCR** | Tesseract OCR for scanned documents and images |
| 🖼️ **Image/Chart Analysis** | GPT-4o Vision for chart, diagram, and image understanding |
| 💬 **AI Chat with Citations** | ChatGPT-style interface with page-level source citations |
| 📊 **Document Comparison** | AI-generated comparison tables across multiple documents |
| 📝 **Document Summary** | Executive, short, detailed summaries with key points |
| 🛡️ **Hallucination Control** | Evidence-grounded answers only — no fabricated info |
| 🎯 **RAG Evaluation** | Real Precision@K, Recall, MRR, Faithfulness metrics |
| 🏗️ **Production Architecture** | FastAPI + React + FAISS + SQLite/PostgreSQL |

## 📁 Supported File Types

- PDF (with table & image extraction)
- DOCX
- PPTX
- TXT
- JPG / JPEG / PNG (with OCR)

---

## 🏗️ Architecture

```
┌────────────────┐     ┌─────────────────────────────────┐
│   React + Vite │────▶│   FastAPI Backend                │
│   Frontend     │     │                                  │
│   (Port 5173)  │     │   ├── Document Ingestion         │
│                │     │   ├── Text/Table/Image Extraction│
│   Pages:       │     │   ├── OCR (Tesseract)            │
│   - Dashboard  │     │   ├── Chunking + Embeddings      │
│   - Documents  │     │   ├── FAISS Vector Store         │
│   - Upload     │     │   ├── BM25 Keyword Search        │
│   - AI Chat    │     │   ├── Hybrid Search + RRF        │
│   - Search     │     │   ├── RAG Pipeline               │
│   - Image AI   │     │   ├── LLM Generation             │
│   - Compare    │     │   ├── Citation Extraction        │
│   - Summarize  │     │   └── Evaluation Pipeline        │
│   - Evaluation │     │                                  │
│   - Settings   │     │   Port 8000                      │
└────────────────┘     └──────────┬──────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │   SQLite / PostgreSQL      │
                    │   + FAISS Vector Index     │
                    └───────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Tesseract OCR** (optional, for OCR features)

### 1. Clone the repository

```bash
cd "Documents/7th SEM/DOCURAG"
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your OPENAI_API_KEY (optional — works without it using extractive answers)

# Start the backend
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Open the app

- Frontend: http://localhost:5173
- Backend API docs: http://localhost:8000/docs

---

## 🔑 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for LLM answers | Optional (works without it) |
| `LLM_MODEL` | LLM model name (default: `gpt-4o`) | No |
| `EMBEDDING_MODEL` | Sentence transformer model | No |
| `DATABASE_URL` | Database connection string | No (uses SQLite by default) |
| `OCR_ENGINE` | OCR engine (`tesseract` or `paddleocr`) | No |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/documents/upload` | Upload a document |
| GET | `/api/documents` | List all documents |
| GET | `/api/documents/{id}` | Get document details |
| DELETE | `/api/documents/{id}` | Delete a document |
| POST | `/api/documents/{id}/process` | Reprocess a document |
| POST | `/api/search` | Hybrid search |
| POST | `/api/chat` | Ask a question (RAG) |
| GET | `/api/chat/conversations` | List conversations |
| POST | `/api/documents/compare` | Compare documents |
| POST | `/api/documents/summarize` | Summarize a document |
| POST | `/api/documents/explain-page` | Explain a page |
| POST | `/api/image/analyze` | Analyze an image |
| GET | `/api/evaluation` | Get evaluation metrics |
| GET | `/api/analytics` | Get analytics dashboard |
| GET | `/api/health` | Health check |

---

## 🐳 Docker Deployment

```bash
docker-compose up --build
```

This starts:
- Frontend on port **5173**
- Backend on port **8000**
- PostgreSQL on port **5432**

---

## 📊 RAG Pipeline

```
Document Upload → Content Extraction → OCR → Chunking → Embedding Generation
                                                             ↓
User Query → Query Analysis → Hybrid Retrieval → Reranking → Context Building
                                                                    ↓
                                                          LLM Generation → Citations → Response
```

---

## 🎯 Evaluation Metrics

| Category | Metric |
|----------|--------|
| Retrieval | Precision@K, Recall@K, MRR |
| Generation | Answer Relevance, Context Relevance, Faithfulness, Citation Accuracy |
| System | Avg Response Time, Retrieval Latency, Document Count, Chunk Count |

All metrics are computed from real pipeline data — nothing is hardcoded.

---

## 🛡️ Hallucination Control

DocuRAG implements strict hallucination control:

1. **Evidence-Only Answers**: LLM is instructed to only use retrieved context
2. **Source Citations**: Every claim must reference a source
3. **Confidence Score**: Computed from retrieval quality and evidence overlap
4. **Graceful Decline**: If insufficient evidence exists, the system says so

---

## 📂 Project Structure

```
docurag/
├── frontend/                  # React + Vite
│   ├── src/
│   │   ├── components/        # Layout, shared components
│   │   ├── pages/             # All page components
│   │   ├── services/          # API client
│   │   └── index.css          # Design system
│   └── package.json
├── backend/                   # FastAPI
│   ├── app/
│   │   ├── api/               # REST API routes
│   │   ├── core/              # Config, DB, logging
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── services/          # Business logic
│   ├── requirements.txt
│   └── Dockerfile
├── data/                      # Uploads, processed files, vectors
├── docker-compose.yml
└── README.md
```

---

## 👥 Team

Built for Hackathon 2026.

---

## 📄 License

MIT License
