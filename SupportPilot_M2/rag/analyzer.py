"""
Stage 1 - Ticket Analysis & Query Generation.

Turns a raw ticket into: category (if not supplied), keywords, a safety flag and a search query.
Rule-based on purpose: transparent, instant, and easy to explain in a demo.
(In the full system, Milestone 1's ML classifier supplies the category.)
"""
import re

from models.schemas import Analysis, Ticket

CATEGORY_KEYWORDS = {
    "Safety Hazard": ["smoke", "burning", "burnt", "spark", "sparks", "fire", "flame", "shock", "melting", "melted",
                      "water", "leak", "flood", "puddle", "smoldering", "hot"],
    "Charger Hardware": ["stuck", "jammed", "cable", "connector", "plug", "screen", "display", "broken", "cracked",
                         "damaged", "latch", "handle", "frayed", "dent"],
    "Payment & Billing": ["charged", "billed", "invoice", "receipt", "refund", "payment", "declined", "card",
                          "vat", "statement", "fee", "tariff", "deposit"],
    "Account & App": ["app", "login", "log in", "sign in", "password", "account", "verification", "profile",
                      "email", "sms"],
    "RFID & Authentication": ["rfid", "badge", "tag", "tap", "access card", "authentication", "plug and charge",
                              "recognised", "recognized", "membership"],
    "Charging Session": ["session", "charging", "slow", "speed", "kw", "stops", "interrupted", "preparing",
                         "not start", "power", "rate"],
    "Station Connectivity": ["offline", "online", "heartbeat", "ocpp", "firmware", "reboot", "router", "network",
                             "backend", "dashboard", "unreachable", "signal", "modem", "connection"],
}

SAFETY_PATTERNS = [
    r"\bsmoke\b", r"\bsmoking\b", r"\bburning\b", r"\bburnt\b", r"\bfire\b", r"\bflames?\b", r"\bsparks?\b",
    r"\bsparking\b", r"\belectric shock\b", r"\bshocked\b", r"\btingling\b", r"\bmelting\b", r"\bmelted\b",
    r"\bsmoldering\b", r"\bsmouldering\b",
]
SITE_WIDE_PATTERNS = [r"\ball chargers\b", r"\bentire (site|depot|station)\b", r"\bwhole (site|depot)\b",
                      r"\bevery charger\b", r"\bfleet\b"]


def _tokens(text: str):
    return re.findall(r"[a-z0-9]+", text.lower())


def detect_category(text: str) -> str:
    t = text.lower()
    scores = {
        cat: sum(1 for kw in kws if re.search(rf"\b{re.escape(kw)}", t))
        for cat, kws in CATEGORY_KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "General"


def analyze_ticket(ticket: Ticket) -> Analysis:
    text = f"{ticket.title}. {ticket.description}".lower()

    safety = any(re.search(p, text) for p in SAFETY_PATTERNS)
    site_wide = any(re.search(p, text) for p in SITE_WIDE_PATTERNS)

    if ticket.category:
        category, source = ticket.category, "provided"
    else:
        category, source = ("Safety Hazard" if safety else detect_category(text)), "detected"

    if ticket.priority:
        priority = ticket.priority
    elif safety or site_wide:
        priority = "P1"
    elif category in ("Charger Hardware", "Charging Session", "Station Connectivity"):
        priority = "P2"
    else:
        priority = "P3"

    all_kw = {kw for kws in CATEGORY_KEYWORDS.values() for kw in kws}
    keywords = sorted(kw for kw in all_kw if re.search(rf"\b{re.escape(kw)}", text))


    query = " ".join(_tokens(f"{ticket.title} {ticket.title} {ticket.description}"))

    return Analysis(
        ticket_id=ticket.id, category=category, category_source=source, priority=priority,
        keywords=keywords, safety_flag=safety, query=query,
    )
