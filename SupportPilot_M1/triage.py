"""
Full Milestone-1 triage: text -> category -> severity -> business impact -> priority.
Used by both the Flask API (app.py) and the evaluation script (evaluate.py).
"""
import time

from classifier import TicketClassifier
from severity import SLA_TARGET, assess_severity, business_impact, calculate_priority

_classifier = None


def get_classifier() -> TicketClassifier:
    global _classifier
    if _classifier is None:
        _classifier = TicketClassifier()
    return _classifier


def triage(title: str, description: str) -> dict:
    start = time.perf_counter()
    text = f"{title}. {description}".strip()
    clf = get_classifier()

    category, category_conf = clf.predict_category(text)
    ml_severity, ml_conf = clf.predict_severity_ml(text)
    severity, severity_conf, reasons = assess_severity(text, ml_severity, ml_conf)
    impact = business_impact(text)
    priority = calculate_priority(severity, impact)

    return {
        "category": category,
        "category_conf": round(category_conf, 3),
        "severity": severity,
        "severity_conf": round(severity_conf, 3),
        "business_impact": impact,
        "priority": priority,
        "sla_target": SLA_TARGET[priority],
        "reasons": reasons,
        "processing_ms": round((time.perf_counter() - start) * 1000, 2),
    }
