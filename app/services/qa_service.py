from typing import List, Dict, Any, Optional, Tuple
import asyncio
from datetime import datetime
import time
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import re

from app.core.config import settings
from app.services.vector_store import VectorStore
from app.models.schemas import SearchResult, AnswerResponse, CompletenessResult, CompletenessResponse

class QAService:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        
    async def answer_question(
        self,
        question: str,
        max_results: int = 5
    ) -> AnswerResponse:
        start_time = time.time()
        
        relevant_chunks = await self.vector_store.search(
            query=question,
            max_results=max_results
        )
        
        if not relevant_chunks:
            return AnswerResponse(
                question=question,
                answer="No relevant information found in the knowledge base.",
                sources=[],
                confidence=0.0,
                processing_time=time.time() - start_time
            )
        
        context = self._prepare_context(relevant_chunks)
        answer = self._generate_extractive_answer(question, relevant_chunks)
        confidence = self._calculate_confidence(relevant_chunks)
        
        return AnswerResponse(
            question=question,
            answer=answer,
            sources=relevant_chunks,
            confidence=confidence,
            processing_time=time.time() - start_time
        )
    
    def _prepare_context(self, chunks: List[SearchResult]) -> str:
        context_parts = []
        for i, chunk in enumerate(chunks[:5]):  # Limit to top 5 chunks
            context_parts.append(
                f"Source {i+1} ({chunk.filename}):\n{chunk.content}\n"
            )
        return "\n---\n".join(context_parts)
    
    def _generate_extractive_answer(self, question: str, chunks: List[SearchResult]) -> str:
        """Generate answer by extracting and combining relevant sentences from chunks."""
        if not chunks:
            return "No relevant information found."
        
        # Combine all chunk contents
        all_sentences = []
        for chunk in chunks[:3]:  # Use top 3 chunks
            sentences = self._extract_sentences(chunk.content)
            for sent in sentences:
                all_sentences.append((sent, chunk.similarity_score, chunk.filename))
        
        # Score sentences based on relevance to question
        question_words = set(question.lower().split())
        scored_sentences = []
        
        for sent, chunk_score, filename in all_sentences:
            sent_words = set(sent.lower().split())
            word_overlap = len(question_words.intersection(sent_words))
            
            # Score based on word overlap and chunk similarity
            score = (word_overlap / len(question_words)) * 0.5 + chunk_score * 0.5
            scored_sentences.append((sent, score, filename))
        
        # Sort by score and select top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Build answer from top sentences
        answer_parts = []
        used_sentences = set()
        
        for sent, score, filename in scored_sentences[:3]:
            if sent not in used_sentences and score > 0.3:
                answer_parts.append(sent)
                used_sentences.add(sent)
        
        if not answer_parts:
            # Fallback to showing beginning of most relevant chunk
            return f"Based on the search results:\n\n{chunks[0].content[:300]}..."
        
        return " ".join(answer_parts)
    
    def _extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text."""
        # Simple sentence extraction
        sentences = re.split(r'[.!?]+', text)
        # Clean and filter
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        return sentences
    
    def _calculate_confidence(self, chunks: List[SearchResult]) -> float:
        if not chunks:
            return 0.0
        
        avg_similarity = sum(chunk.similarity_score for chunk in chunks) / len(chunks)
        
        top_score = chunks[0].similarity_score if chunks else 0.0
        
        confidence = (avg_similarity * 0.4) + (top_score * 0.6)
        
        return min(confidence, 1.0)
    
    async def check_completeness(
        self,
        topics: List[str],
        document_ids: Optional[List[str]] = None
    ) -> CompletenessResponse:
        results = []
        
        for topic in topics:
            relevant_chunks = await self.vector_store.search(
                query=topic,
                max_results=10,
                document_ids=document_ids
            )
            
            if relevant_chunks:
                covered_aspects, missing_aspects = self._analyze_coverage_locally(
                    topic, relevant_chunks
                )
                coverage_score = len(covered_aspects) / (
                    len(covered_aspects) + len(missing_aspects)
                ) if (covered_aspects or missing_aspects) else 0.0
            else:
                covered_aspects = []
                missing_aspects = [f"No information about {topic}"]
                coverage_score = 0.0
            
            results.append(CompletenessResult(
                topic=topic,
                coverage_score=coverage_score,
                covered_aspects=covered_aspects,
                missing_aspects=missing_aspects,
                relevant_chunks=relevant_chunks[:3]  # Include top 3 chunks
            ))
        
        overall_completeness = (
            sum(r.coverage_score for r in results) / len(results)
            if results else 0.0
        )
        
        recommendations = self._generate_recommendations(results)
        
        return CompletenessResponse(
            overall_completeness=overall_completeness,
            results=results,
            recommendations=recommendations
        )
    
    def _analyze_coverage_locally(
        self,
        topic: str,
        chunks: List[SearchResult]
    ) -> Tuple[List[str], List[str]]:
        """Analyze coverage using keyword and semantic matching."""
        content = " ".join([chunk.content.lower() for chunk in chunks])
        
        # Define common aspects for various topics
        topic_aspects = {
            "machine learning": ["supervised", "unsupervised", "reinforcement", "neural networks", "training", "models"],
            "deep learning": ["neural networks", "backpropagation", "layers", "activation", "convolution", "recurrent"],
            "data science": ["analysis", "visualization", "statistics", "cleaning", "modeling", "insights"],
            "artificial intelligence": ["machine learning", "neural networks", "nlp", "computer vision", "reasoning"],
            "supervised learning": ["classification", "regression", "labeled data", "training", "prediction"],
            "unsupervised learning": ["clustering", "dimensionality", "patterns", "unlabeled", "grouping"],
            "reinforcement learning": ["agent", "environment", "reward", "policy", "action", "state"]
        }
        
        # Get aspects for the topic
        topic_lower = topic.lower()
        aspects = []
        
        # Check if topic matches any predefined topics
        for key, values in topic_aspects.items():
            if key in topic_lower or topic_lower in key:
                aspects.extend(values)
                break
        
        # If no predefined aspects, generate from topic words
        if not aspects:
            topic_words = topic_lower.split()
            aspects = topic_words + [f"{word} examples" for word in topic_words]
        
        # Check which aspects are covered
        covered = []
        missing = []
        
        for aspect in aspects:
            if aspect.lower() in content:
                covered.append(f"Coverage of {aspect}")
            else:
                # Check for semantic similarity
                aspect_words = set(aspect.lower().split())
                content_words = set(content.split())
                if len(aspect_words.intersection(content_words)) > 0:
                    covered.append(f"Partial coverage of {aspect}")
                else:
                    missing.append(f"Missing information about {aspect}")
        
        # If we found good coverage, add a summary
        if len(covered) > len(missing):
            covered.insert(0, f"Good overall coverage of {topic}")
        elif not covered:
            missing.insert(0, f"No clear coverage of {topic}")
        
        return covered[:5], missing[:5]  # Limit to 5 each
    
    def _generate_recommendations(self, results: List[CompletenessResult]) -> List[str]:
        recommendations = []
        
        low_coverage_topics = [
            r.topic for r in results if r.coverage_score < 0.5
        ]
        
        if low_coverage_topics:
            recommendations.append(
                f"Consider adding more content about: {', '.join(low_coverage_topics)}"
            )
        
        missing_aspects_count = sum(len(r.missing_aspects) for r in results)
        if missing_aspects_count > 5:
            recommendations.append(
                "The knowledge base has significant gaps. Consider comprehensive content review."
            )
        
        high_coverage_count = sum(1 for r in results if r.coverage_score > 0.8)
        if high_coverage_count == len(results):
            recommendations.append(
                "Knowledge base has excellent coverage of the specified topics."
            )
        
        return recommendations