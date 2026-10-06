"""
DocuRAG - Embedding Service
Manages sentence-transformer embeddings and FAISS vector store.
"""
import os
import numpy as np
from typing import List, Dict, Optional, Any
from loguru import logger
from app.core.config import get_settings

settings = get_settings()


class EmbeddingService:
    """Service for generating embeddings and managing the FAISS index."""
    
    _model = None
    _index = None
    _metadata_store: List[Dict[str, Any]] = []
    _texts_store: List[str] = []
    
    def __init__(self):
        self._ensure_model()
    
    def _ensure_model(self):
        """Lazy-load the sentence transformer model."""
        if EmbeddingService._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
                EmbeddingService._model = SentenceTransformer(settings.EMBEDDING_MODEL)
                logger.info("Embedding model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise
    
    def _ensure_index(self):
        """Lazy-load or create the FAISS index."""
        if EmbeddingService._index is None:
            try:
                import faiss
                
                # Try to load existing index
                index_path = settings.FAISS_INDEX_PATH + ".index"
                if os.path.exists(index_path):
                    EmbeddingService._index = faiss.read_index(index_path)
                    # Load metadata
                    meta_path = settings.FAISS_INDEX_PATH + "_meta.npy"
                    texts_path = settings.FAISS_INDEX_PATH + "_texts.npy"
                    if os.path.exists(meta_path):
                        EmbeddingService._metadata_store = list(np.load(meta_path, allow_pickle=True))
                    if os.path.exists(texts_path):
                        EmbeddingService._texts_store = list(np.load(texts_path, allow_pickle=True))
                    logger.info(f"Loaded FAISS index with {EmbeddingService._index.ntotal} vectors")
                else:
                    # Create new index
                    dim = EmbeddingService._model.get_sentence_embedding_dimension()
                    EmbeddingService._index = faiss.IndexFlatIP(dim)  # Inner product (cosine on normalized)
                    EmbeddingService._metadata_store = []
                    EmbeddingService._texts_store = []
                    logger.info(f"Created new FAISS index (dim={dim})")
            except ImportError:
                logger.error("faiss-cpu not installed")
                raise
    
    def embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts."""
        embeddings = EmbeddingService._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.array(embeddings, dtype=np.float32)
    
    async def add_documents(self, texts: List[str], metadatas: List[Dict], document_id: str):
        """Add document chunks to the FAISS index."""
        self._ensure_index()
        
        if not texts:
            return
        
        embeddings = self.embed(texts)
        
        import faiss
        EmbeddingService._index.add(embeddings)
        EmbeddingService._metadata_store.extend(metadatas)
        EmbeddingService._texts_store.extend(texts)
        
        # Persist index
        self._save_index()
        
        logger.info(f"Added {len(texts)} vectors for document {document_id}. Total: {EmbeddingService._index.ntotal}")
    
    async def search(self, query: str, top_k: int = 10, filter_doc_ids: Optional[List[str]] = None) -> List[Dict]:
        """Search the FAISS index for similar chunks."""
        self._ensure_index()
        
        if EmbeddingService._index.ntotal == 0:
            return []
        
        query_embedding = self.embed([query])
        
        # Search more than needed if we need to filter
        search_k = min(top_k * 3, EmbeddingService._index.ntotal)
        scores, indices = EmbeddingService._index.search(query_embedding, search_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            if idx >= len(EmbeddingService._metadata_store):
                continue
            
            metadata = EmbeddingService._metadata_store[idx]
            text = EmbeddingService._texts_store[idx] if idx < len(EmbeddingService._texts_store) else ""
            
            # Apply document filter
            if filter_doc_ids and metadata.get("document_id") not in filter_doc_ids:
                continue
            
            results.append({
                "text": text,
                "score": float(score),
                "metadata": metadata,
                "index": int(idx),
            })
            
            if len(results) >= top_k:
                break
        
        return results
    
    async def delete_document(self, document_id: str):
        """Remove all vectors for a document (rebuild index without them)."""
        self._ensure_index()
        
        import faiss
        
        # Filter out the document's entries
        new_metadata = []
        new_texts = []
        keep_indices = []
        
        for i, meta in enumerate(EmbeddingService._metadata_store):
            if meta.get("document_id") != document_id:
                new_metadata.append(meta)
                new_texts.append(EmbeddingService._texts_store[i] if i < len(EmbeddingService._texts_store) else "")
                keep_indices.append(i)
        
        if not keep_indices:
            # All gone, reset index
            dim = EmbeddingService._model.get_sentence_embedding_dimension()
            EmbeddingService._index = faiss.IndexFlatIP(dim)
            EmbeddingService._metadata_store = []
            EmbeddingService._texts_store = []
        else:
            # Rebuild with remaining vectors
            remaining_embeddings = self.embed(new_texts)
            dim = remaining_embeddings.shape[1]
            new_index = faiss.IndexFlatIP(dim)
            new_index.add(remaining_embeddings)
            EmbeddingService._index = new_index
            EmbeddingService._metadata_store = new_metadata
            EmbeddingService._texts_store = new_texts
        
        self._save_index()
        logger.info(f"Deleted vectors for document {document_id}")
    
    def _save_index(self):
        """Persist FAISS index and metadata to disk."""
        import faiss
        
        os.makedirs(os.path.dirname(settings.FAISS_INDEX_PATH), exist_ok=True)
        faiss.write_index(EmbeddingService._index, settings.FAISS_INDEX_PATH + ".index")
        np.save(settings.FAISS_INDEX_PATH + "_meta.npy", EmbeddingService._metadata_store, allow_pickle=True)
        np.save(settings.FAISS_INDEX_PATH + "_texts.npy", EmbeddingService._texts_store, allow_pickle=True)
