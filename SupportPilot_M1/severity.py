"""
Severity + priority engine (hybrid: ML prediction + explainable rules).

Severity  = how serious the technical problem is        (Low/Medium/High/Critical)
Business impact = how many drivers / how much revenue is affected (Low/Medium/High)
Priority  = P1..P4, derived from BOTH (the Milestone-1 brief says they are not identical)
"""
import re

LEVELS = ["Low", "Medium", "High", "Critical"]

# Anything that can hurt a person or damage property is Critical, whatever the ML says.
CRITICAL_PATTERNS = [
    r"\bsmoke\b", r"\bsmoking\b", r"\bburning\b", r"\bburnt\b", r"\bfire\b",
    r"\bflames?\b", r"\bsparks?\b", r"\bsparking\b", r"\belectric shock\b",
    r"\bshocked\b", r"\bexposed wires?\b", r"\bmelted\b", r"\bmelting\b", r"\boverheating\b",
    r"\bwhole site\b", r"\ball chargers\b",
    r"\bentire (site|station|depot)\b",
]

# Words that show the driver is in a time-critical situation -> bump severity one level (cap: High).
URGENCY_PATTERNS = [
    r"\bstranded\b", r"\bemergency\b", r"\blow battery\b", r"\bimportant meeting\b",
    r"\bclient\b", r"\brunning out of (charge|battery)\b", r"\bambulance\b", r"\bairport\b",
]

# Business-impact signals.
HIGH_IMPACT_PATTERNS = [
    r"\ball chargers\b", r"\bwhole site\b", r"\bentire (site|station|depot)\b",
    r"\bevery (driver|charger|card)\b", r"\bfleet\b", r"\bdepot\b", r"\bmultiple (chargers|stations|drivers)\b",
    r"\bcustomers\b",
]
MEDIUM_IMPACT_PATTERNS = [r"\bstranded\b", r"\bqueue\b", r"\bseveral\b", r"\bbay\b", r"\bmeeting\b"]


def _matches(patterns, text):
    return [p.strip(r"\b") for p in patterns if re.search(p, text)]


def _bump(level: str, steps: int = 1, cap: str = "High") -> str:
    i = min(LEVELS.index(level) + steps, LEVELS.index(cap))
    return LEVELS[max(i, LEVELS.index(level))]


def assess_severity(text: str, ml_label: str, ml_confidence: float):
    """Return (severity, confidence, reasons[])."""
    t = text.lower()
    reasons = [f"ML model predicted '{ml_label}' ({ml_confidence:.0%})"]
    severity = ml_label

    hits = _matches(CRITICAL_PATTERNS, t)
    if hits:
        severity = "Critical"
        reasons.append("Safety/site-wide keyword override: " + ", ".join(hits))
        return severity, max(ml_confidence, 0.95), reasons

    urgent = _matches(URGENCY_PATTERNS, t)
    if urgent:
        bumped = _bump(severity)
        if bumped != severity:
            reasons.append(
                f"Urgency keyword(s) {', '.join(urgent)} raised severity {severity} -> {bumped}"
            )
            severity = bumped
    return severity, ml_confidence, reasons


def business_impact(text: str) -> str:
    t = text.lower()
    if _matches(HIGH_IMPACT_PATTERNS, t):
        return "High"
    if _matches(MEDIUM_IMPACT_PATTERNS, t):
        return "Medium"
    return "Low"


def calculate_priority(severity: str, impact: str) -> str:
    """Single, consistent priority matrix (P1 = respond immediately)."""
    if severity == "Critical":
        return "P1"
    if severity == "High":
        return "P1" if impact == "High" else "P2"
    if severity == "Medium":
        return "P2" if impact == "High" else "P3"
    return "P3" if impact == "High" else "P4"     # Low severity


SLA_TARGET = {"P1": "15 minutes", "P2": "1 hour", "P3": "8 hours", "P4": "2 business days"}
