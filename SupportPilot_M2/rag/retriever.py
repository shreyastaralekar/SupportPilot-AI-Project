"""
Stage 2 - Knowledge Base Retrieval  (the "R" in RAG).

TF-IDF (word 1-2 grams) + cosine similarity over the enterprise knowledge base.
A small bonus is added when the article category matches the ticket category.
Swap this class for an embedding + vector-database retriever later; the interface stays the same.
"""
import json
from typing import List, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import config
from models.schemas import RetrievedDoc


def load_knowledge_base(path=config.KB_PATH) -> list:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class KnowledgeRetriever:
    def __init__(self, documents: list):
        self.documents = documents
        # Title is repeated so that title words weigh more than body words.
        texts = [f"{d['title']} {d['title']} {d['content']}" for d in documents]
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
        self.vectors = self.vectorizer.fit_transform(texts)

    def search(self, query: str, top_k: int = config.TOP_K, category: Optional[str] = None) -> List[RetrievedDoc]:
        scores = cosine_similarity(self.vectorizer.transform([query]), self.vectors)[0].copy()
        if category:
            for i, doc in enumerate(self.documents):
                if scores[i] > 0 and doc["category"] == category:
                    scores[i] += config.CATEGORY_BOOST
        ranked = scores.argsort()[::-1][:top_k]
        return [
            RetrievedDoc(
                id=self.documents[i]["id"], title=self.documents[i]["title"],
                category=self.documents[i]["category"], source=self.documents[i].get("source", ""),
                last_updated=self.documents[i].get("last_updated", ""),
                content=self.documents[i]["content"], score=float(scores[i]),
            )
            for i in ranked
        ]
