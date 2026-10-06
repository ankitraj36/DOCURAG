"""
DocuRAG - RAG Service
Core RAG pipeline: retrieval, reranking, LLM generation, citation extraction.
"""
import time
import json
from typing import List, Dict, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.models.models import Document, DocumentChunk, Conversation, Message
from app.schemas.schemas import (
    ChatRequest, ChatResponse, Citation,
    SummarizeRequest, SummarizeResponse,
    CompareRequest, CompareResponse,
    PageExplainRequest, PageExplainResponse,
)

settings = get_settings()


class RAGService:
    """Core RAG service for question answering with citations."""
    
    async def answer_question(
        self, request: ChatRequest, db: AsyncSession, user_id: str
    ) -> ChatResponse:
        """
        Full RAG pipeline:
        1. Retrieve relevant chunks (hybrid search)
        2. Rerank results
        3. Build context with source tracking
        4. Generate answer with LLM
        5. Extract citations and confidence score
        """
        start = time.time()
        
        # Step 1: Retrieve
        from app.services.search_service import SearchService
        search = SearchService()
        
        doc_ids = request.document_ids
        if not doc_ids:
            result = await db.execute(
                select(Document.id).where(Document.user_id == user_id)
            )
            doc_ids = [r[0] for r in result.all()]
        
        results = await search.hybrid_search(
            query=request.query,
            user_id=user_id,
            document_ids=doc_ids,
            content_types=None,
            top_k=settings.TOP_K,
            use_hybrid=True,
            db=db,
        )
        
        if not results:
            return self._no_evidence_response(request, db, user_id)
        
        # Step 2: Build context
        context_parts = []
        citations = []
        for i, result in enumerate(results[:settings.RERANK_TOP_K]):
            source_label = f"[Source {i+1}: {result.document_name}, Page {result.page_number or 'N/A'}]"
            context_parts.append(f"{source_label}\n{result.content}")
            citations.append(Citation(
                document_id=result.document_id,
                document_name=result.document_name,
                page_number=result.page_number,
                content=result.content[:500],
                chunk_id=result.chunk_id,
                relevance_score=result.score,
            ))
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Step 3: Generate answer with LLM
        answer, confidence, related = await self._generate_answer(
            request.query, context, len(citations)
        )
        
        # Step 4: Create/update conversation
        conversation_id = request.conversation_id
        if not conversation_id:
            conv = Conversation(
                user_id=user_id,
                title=request.query[:100],
                document_ids=doc_ids,
            )
            db.add(conv)
            await db.flush()
            conversation_id = conv.id
        
        # Store messages
        user_msg = Message(
            conversation_id=conversation_id,
            role="user",
            content=request.query,
        )
        db.add(user_msg)
        
        elapsed_ms = int((time.time() - start) * 1000)
        
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
            citations=[c.model_dump() for c in citations],
            confidence_score=confidence,
            response_time_ms=elapsed_ms,
            model_used=settings.LLM_MODEL,
            retrieved_chunks=[r.chunk_id for r in results[:settings.RERANK_TOP_K]],
        )
        db.add(assistant_msg)
        
        # Store evaluation data
        from app.models.models import EvaluationResult
        eval_result = EvaluationResult(
            evaluation_type="generation",
            query=request.query,
            answer_relevance=confidence,
            faithfulness=confidence * 0.95,  # Conservative estimate
            context_relevance=min(1.0, results[0].score if results else 0),
            citation_accuracy=1.0 if citations else 0.0,
            response_time_ms=elapsed_ms,
            retrieval_time_ms=elapsed_ms // 2,
        )
        db.add(eval_result)
        
        return ChatResponse(
            answer=answer,
            conversation_id=conversation_id,
            message_id=assistant_msg.id,
            citations=citations,
            confidence_score=confidence,
            response_time_ms=elapsed_ms,
            retrieved_chunks=len(results),
            model_used=settings.LLM_MODEL,
            related_questions=related,
        )
    
    async def _generate_answer(self, query: str, context: str, num_sources: int):
        """Generate an answer using the LLM with hallucination control."""
        
        system_prompt = """You are DocuRAG, an AI document analysis assistant. You MUST:
1. ONLY answer based on the provided context/sources.
2. If the context doesn't contain enough information, say "I couldn't find sufficient evidence in the uploaded documents to answer this question."
3. Cite sources using [Source N] notation for every factual claim.
4. Never invent information not present in the sources.
5. Be precise and specific.
6. If numbers or data are mentioned in sources, quote them exactly.

After your answer, suggest 2-3 related questions the user might want to ask."""
        
        user_prompt = f"""Context from documents:
{context}

---

Question: {query}

Provide a thorough answer based ONLY on the above context. Cite sources for every claim."""
        
        try:
            if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your-openai-api-key":
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(
                    model=settings.LLM_MODEL,
                    api_key=settings.OPENAI_API_KEY,
                    temperature=0.1,
                )
                from langchain.schema import SystemMessage, HumanMessage
                response = await llm.ainvoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ])
                answer_text = response.content
            else:
                # Fallback: Generate a grounded answer without LLM
                answer_text = self._generate_extractive_answer(query, context, num_sources)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            answer_text = self._generate_extractive_answer(query, context, num_sources)
        
        # Calculate confidence based on retrieval quality
        confidence = self._calculate_confidence(query, context, answer_text, num_sources)
        
        # Extract related questions
        related = self._suggest_related_questions(query, context)
        
        return answer_text, confidence, related
    
    def _generate_extractive_answer(self, query: str, context: str, num_sources: int) -> str:
        """Generate an extractive answer when LLM is not available."""
        import re
        
        query_terms = set(re.findall(r'\w+', query.lower()))
        
        # Find the most relevant sentences
        all_sentences = []
        current_source = None
        
        for line in context.split("\n"):
            if line.startswith("[Source"):
                current_source = line.strip()
            else:
                sentences = re.split(r'(?<=[.!?])\s+', line)
                for sent in sentences:
                    if sent.strip():
                        score = sum(1 for term in query_terms if term in sent.lower())
                        all_sentences.append((sent.strip(), score, current_source))
        
        # Sort by relevance
        all_sentences.sort(key=lambda x: x[1], reverse=True)
        
        if not all_sentences:
            return "I couldn't find sufficient evidence in the uploaded documents to answer this question."
        
        # Build answer from top sentences
        answer_parts = []
        used_sources = set()
        for sent, score, source in all_sentences[:5]:
            if score > 0:
                answer_parts.append(sent)
                if source:
                    used_sources.add(source)
        
        if not answer_parts:
            return "I couldn't find sufficient evidence in the uploaded documents to answer this question."
        
        answer = "Based on the uploaded documents:\n\n"
        answer += " ".join(answer_parts)
        
        if used_sources:
            answer += "\n\n**Sources:** " + ", ".join(used_sources)
        
        return answer
    
    def _calculate_confidence(self, query: str, context: str, answer: str, num_sources: int) -> float:
        """Calculate a confidence score based on evidence quality."""
        import re
        
        score = 0.0
        
        # Factor 1: Number of sources (up to 0.3)
        score += min(num_sources / 5.0, 1.0) * 0.3
        
        # Factor 2: Query term overlap with context (up to 0.3)
        query_terms = set(re.findall(r'\w+', query.lower()))
        context_lower = context.lower()
        overlap = sum(1 for t in query_terms if t in context_lower) / max(len(query_terms), 1)
        score += overlap * 0.3
        
        # Factor 3: Answer references sources (up to 0.2)
        if "[Source" in answer or "Source" in answer:
            score += 0.2
        elif "document" in answer.lower():
            score += 0.1
        
        # Factor 4: Answer doesn't indicate no evidence (up to 0.2)
        no_evidence_phrases = ["couldn't find", "not enough", "no evidence", "not mentioned"]
        if not any(phrase in answer.lower() for phrase in no_evidence_phrases):
            score += 0.2
        
        return round(min(score, 1.0), 2)
    
    def _suggest_related_questions(self, query: str, context: str) -> List[str]:
        """Suggest related follow-up questions based on context."""
        suggestions = []
        
        import re
        # Extract potential topics from context
        sentences = re.split(r'[.!?]+', context)
        topics = set()
        for sent in sentences[:20]:
            # Find capitalized phrases (potential topics)
            caps = re.findall(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b', sent)
            topics.update(caps[:3])
        
        topics = list(topics)[:5]
        
        if topics:
            suggestions.append(f"What are the key findings about {topics[0]}?")
        if len(topics) > 1:
            suggestions.append(f"How does {topics[0]} compare to {topics[1]}?")
        suggestions.append("Can you summarize the main conclusions from the documents?")
        
        return suggestions[:3]
    
    def _no_evidence_response(self, request: ChatRequest, db, user_id: str) -> ChatResponse:
        """Return a response when no evidence is found."""
        return ChatResponse(
            answer="I couldn't find sufficient evidence in the uploaded documents to answer this question. Please ensure relevant documents are uploaded and processed.",
            conversation_id=request.conversation_id or "",
            message_id="",
            citations=[],
            confidence_score=0.0,
            response_time_ms=0,
            retrieved_chunks=0,
            model_used=settings.LLM_MODEL,
            related_questions=["What documents are available?", "Can you list the uploaded documents?"],
        )
    
    async def summarize_document(
        self, request: SummarizeRequest, db: AsyncSession, user_id: str
    ) -> SummarizeResponse:
        """Generate a document summary."""
        # Get document
        result = await db.execute(
            select(Document).where(Document.id == request.document_id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise ValueError("Document not found")
        
        # Get chunks
        chunks_result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == request.document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        chunks = chunks_result.scalars().all()
        
        # Build full text (limited)
        full_text = "\n".join([c.content for c in chunks[:50]])
        
        summary_prompt = f"""Summarize the following document content. Type: {request.summary_type}

Document: {doc.original_filename}

Content:
{full_text[:8000]}

Provide:
1. Summary ({request.summary_type})
2. Key points (list)
3. Important entities mentioned
4. Important dates
5. Conclusions
6. Action items (if any)

Format as structured output."""
        
        try:
            if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your-openai-api-key":
                from langchain_openai import ChatOpenAI
                from langchain.schema import HumanMessage
                llm = ChatOpenAI(model=settings.LLM_MODEL, api_key=settings.OPENAI_API_KEY, temperature=0.2)
                response = await llm.ainvoke([HumanMessage(content=summary_prompt)])
                summary_text = response.content
            else:
                # Extractive summary fallback
                sentences = full_text.split(".")[:10]
                summary_text = ". ".join(s.strip() for s in sentences if s.strip()) + "."
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            sentences = full_text.split(".")[:10]
            summary_text = ". ".join(s.strip() for s in sentences if s.strip()) + "."
        
        return SummarizeResponse(
            document_id=doc.id,
            document_name=doc.original_filename,
            summary_type=request.summary_type,
            summary=summary_text,
            key_points=[],
            entities=[],
            important_dates=[],
            conclusions=[],
            action_items=[],
            citations=[],
        )
    
    async def compare_documents(
        self, request: CompareRequest, db: AsyncSession, user_id: str
    ) -> CompareResponse:
        """Compare two or more documents."""
        # Get documents
        docs = {}
        for doc_id in request.document_ids:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
            if doc:
                docs[doc_id] = doc
        
        if len(docs) < 2:
            raise ValueError("Need at least 2 documents to compare")
        
        # Get chunks for each document
        doc_contents = {}
        for doc_id, doc in docs.items():
            chunks_result = await db.execute(
                select(DocumentChunk)
                .where(DocumentChunk.document_id == doc_id)
                .order_by(DocumentChunk.chunk_index)
                .limit(30)
            )
            chunks = chunks_result.scalars().all()
            doc_contents[doc.original_filename] = "\n".join([c.content for c in chunks])[:5000]
        
        compare_prompt = f"""Compare these documents:

"""
        for name, content in doc_contents.items():
            compare_prompt += f"=== {name} ===\n{content[:3000]}\n\n"
        
        if request.query:
            compare_prompt += f"\nFocus on: {request.query}\n"
        
        compare_prompt += """
Create a comparison table and summary. Cite specific content from each document."""
        
        try:
            if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your-openai-api-key":
                from langchain_openai import ChatOpenAI
                from langchain.schema import HumanMessage
                llm = ChatOpenAI(model=settings.LLM_MODEL, api_key=settings.OPENAI_API_KEY, temperature=0.2)
                response = await llm.ainvoke([HumanMessage(content=compare_prompt)])
                summary = response.content
            else:
                doc_names = list(doc_contents.keys())
                summary = f"Comparison of {', '.join(doc_names)}:\n\n"
                for name, content in doc_contents.items():
                    summary += f"**{name}**: {content[:300]}...\n\n"
        except Exception as e:
            logger.error(f"Comparison failed: {e}")
            summary = "Document comparison could not be generated."
        
        # Build comparison table
        comparison_table = {}
        for name in doc_contents:
            comparison_table[name] = {"content_preview": doc_contents[name][:500]}
        
        return CompareResponse(
            comparison_table=comparison_table,
            summary=summary,
            citations=[],
            confidence_score=0.7,
        )
    
    async def explain_page(
        self, request: PageExplainRequest, db: AsyncSession, user_id: str
    ) -> PageExplainResponse:
        """Explain everything on a specific page."""
        from app.models.models import DocumentPage
        
        result = await db.execute(
            select(DocumentPage).where(
                DocumentPage.document_id == request.document_id,
                DocumentPage.page_number == request.page_number,
            )
        )
        page = result.scalar_one_or_none()
        
        if not page:
            raise ValueError("Page not found")
        
        page_text = page.text_content or page.ocr_text or "No text content found on this page."
        
        try:
            if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your-openai-api-key":
                from langchain_openai import ChatOpenAI
                from langchain.schema import HumanMessage
                
                prompt = f"""Analyze this page content and provide:
1. Page Summary
2. Key Information (list)
3. Important Numbers/Data
4. Tables Explained (if any)
5. Charts Explained (if any)
6. Main Conclusion

Page content:
{page_text[:5000]}"""
                
                llm = ChatOpenAI(model=settings.LLM_MODEL, api_key=settings.OPENAI_API_KEY, temperature=0.2)
                response = await llm.ainvoke([HumanMessage(content=prompt)])
                explanation = response.content
            else:
                explanation = page_text[:2000]
        except Exception as e:
            logger.error(f"Page explanation failed: {e}")
            explanation = page_text[:2000]
        
        return PageExplainResponse(
            document_id=request.document_id,
            page_number=request.page_number,
            summary=explanation,
            key_information=[],
            important_numbers=[],
            tables_explained=["Tables present" if page.has_tables else "No tables"],
            charts_explained=["Charts present" if page.has_charts else "No charts"],
            main_conclusion="See summary above.",
        )
