"""Typed data structures passed between the RAG stages."""
from dataclasses import asdict, dataclass, field
from typing import List, Optional


@dataclass
class Ticket:
    id: str
    title: str
    description: str
    category: Optional[str] = None
    priority: Optional[str] = None


@dataclass
class Analysis:
    ticket_id: str
    category: str
    category_source: str          # "provided" or "detected"
    priority: str
    keywords: List[str]
    safety_flag: bool
    query: str


@dataclass
class RetrievedDoc:
    id: str
    title: str
    category: str
    source: str
    last_updated: str
    content: str
    score: float


@dataclass
class Step:
    number: int
    text: str
    source_id: str
    source_title: str


@dataclass
class Resolution:
    status: str                   # "OK" | "INSUFFICIENT_KNOWLEDGE" | "SAFETY_ESCALATION"
    generator: str                # "extractive" | "llm"
    likely_cause: str = ""
    steps: List[Step] = field(default_factory=list)
    escalate_if: str = ""
    safety_notice: str = ""
    message: str = ""
    sources: List[str] = field(default_factory=list)


def to_dict(obj):
    return asdict(obj)
