"""
Complete RAG pipeline:
    1. Ticket Analysis & Query Generation
    2. Knowledge Base Retrieval
    3. Context Augmentation
    4. Response Generation
Each stage is timed so the UI's "RAG Workflow Status" shows real durations, not hard-coded values.
"""
import time

import config
from models.schemas import Ticket, to_dict
from rag.analyzer import analyze_ticket
from rag.generator import ExtractiveGenerator, LLMGenerator, build_context
from rag.retriever import KnowledgeRetriever


class RAGPipeline:
    def __init__(self, retriever: KnowledgeRetriever, generator=None):
        self.retriever = retriever
        self.generator = generator or ExtractiveGenerator()

    def run(self, ticket: Ticket) -> dict:
        stages, t_start = [], time.perf_counter()

        def timed(name, fn):
            t0 = time.perf_counter()
            out = fn()
            stages.append({"stage": name, "status": "completed",
                           "ms": round((time.perf_counter() - t0) * 1000, 2)})
            return out

        analysis = timed("Ticket Analysis & Query Generation", lambda: analyze_ticket(ticket))

        candidates = timed("Knowledge Base Retrieval", lambda: self.retriever.search(
            analysis.query, top_k=config.TOP_K, category=analysis.category))
        relevant = [d for d in candidates if d.score >= config.MIN_RELEVANCE]
        # Safety reports must reach the safety procedure even when wording is unusual.
        if analysis.safety_flag and not any(d.category == "Safety Hazard" for d in relevant):
            extra = [d for d in self.retriever.search(analysis.query, top_k=len(self.retriever.documents),
                                                      category="Safety Hazard")
                     if d.category == "Safety Hazard"][:1]
            relevant = extra + relevant

        context = timed("Context Augmentation", lambda: build_context(relevant))

        if isinstance(self.generator, LLMGenerator):
            resolution = timed("Response Generation",
                               lambda: self.generator.generate(ticket, analysis, relevant, context))
        else:
            resolution = timed("Response Generation",
                               lambda: self.generator.generate(ticket, analysis, relevant))

        return {
            "ticket": to_dict(ticket),
            "analysis": to_dict(analysis),
            "retrieved_documents": [{**to_dict(d), "content": d.content} for d in candidates],
            "used_documents": [d.id for d in relevant],
            "context": context,
            "resolution": to_dict(resolution),
            "workflow": stages,
            "total_ms": round((time.perf_counter() - t_start) * 1000, 2),
            "min_relevance": config.MIN_RELEVANCE,
        }
