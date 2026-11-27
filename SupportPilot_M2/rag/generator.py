"""
Stages 3-4 - Context Augmentation and Resolution Generation.

build_context()      formats retrieved articles into the context block given to the generator.
create_prompt()      grounded prompt for a real LLM ("use only the knowledge base, cite sources").
ExtractiveGenerator  default, offline, deterministic: assembles the answer ONLY from retrieved text,
                     so it cannot invent steps. Every step carries its KB source.
LLMGenerator         optional: calls the Anthropic Messages API over plain HTTPS (no SDK needed).
                     Enabled with SUPPORTPILOT_USE_LLM=1 and ANTHROPIC_API_KEY.
"""
import json
import re
import urllib.error
import urllib.request
from typing import List

import config
from models.schemas import Analysis, Resolution, RetrievedDoc, Step, Ticket

STEP_RE = re.compile(r"^\s*(\d+)\.\s+(.*\S)\s*$")
STOPWORDS = {"the", "a", "an", "to", "of", "and", "or", "in", "on", "is", "are", "it", "for", "with", "that",
             "this", "if", "my", "i", "me", "at", "be", "not", "was", "has", "have", "from", "by", "as"}


# ------------------------------------------------------------------ context augmentation
def build_context(docs: List[RetrievedDoc]) -> str:
    blocks = []
    for d in docs:
        blocks.append(
            f"Knowledge Base Article\nID: {d.id}\nTitle: {d.title}\nCategory: {d.category}\n"
            f"Relevance: {d.score:.2f}\n{d.content}\n{'-' * 40}"
        )
    return "\n".join(blocks)


def create_prompt(ticket: Ticket, analysis: Analysis, context: str) -> str:
    return f"""You are an enterprise support assistant for an EV charging network.
Troubleshoot the ticket below for a support agent.

TICKET
------
Title: {ticket.title}
Description: {ticket.description}
Category: {analysis.category}    Priority: {analysis.priority}

KNOWLEDGE BASE
--------------
{context}

INSTRUCTIONS
------------
1. Use ONLY the knowledge base above. Do not invent company policies or steps.
2. Give numbered troubleshooting steps and cite the article ID after each step, e.g. (KB001).
3. State the likely cause when the knowledge base gives one.
4. If the knowledge base lacks enough information, say that further investigation is required.
5. If anyone may be in danger (smoke, fire, shock), the first line must tell the reporter to move away and call emergency services.
6. Keep it concise and suitable for a support agent."""


# ------------------------------------------------------------------ parsing helpers
def _parse(doc: RetrievedDoc):
    cause, escalate, steps = "", "", []
    for line in doc.content.split("\n"):
        line = line.strip()
        if line.startswith("Likely cause:"):
            cause = line[len("Likely cause:"):].strip()
        elif line.startswith("Escalate if:"):
            escalate = line[len("Escalate if:"):].strip()
        elif STEP_RE.match(line):
            steps.append(STEP_RE.match(line).group(2))
    return cause, escalate, steps


def _words(text: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS and len(w) > 2}


SAFETY_NOTICE = ("SAFETY FIRST: tell the reporter to move away from the charger and vehicle and keep others back. "
                 "If there are flames or heavy smoke, they must call the local emergency number now. "
                 "Do not ask anyone to unplug the vehicle or touch the charger.")


# ------------------------------------------------------------------ generators
class ExtractiveGenerator:
    name = "extractive"

    def generate(self, ticket: Ticket, analysis: Analysis, docs: List[RetrievedDoc]) -> Resolution:
        if not docs:
            return Resolution(status="INSUFFICIENT_KNOWLEDGE", generator=self.name,
                              message="No sufficiently relevant knowledge-base articles were found. "
                                      "Additional investigation is required; escalate to a human agent.")

        # Safety reports: put safety articles first so the mandatory procedure leads.
        if analysis.safety_flag:
            docs = sorted(docs, key=lambda d: d.category != "Safety Hazard")

        query_words = _words(analysis.query)
        top = docs[0]
        steps: List[Step] = []
        seen = set()

        def add(text, doc):
            key = text.lower()
            if key not in seen:
                seen.add(key)
                steps.append(Step(number=len(steps) + 1, text=text, source_id=doc.id, source_title=doc.title))

        cause, escalate, top_steps = _parse(top)
        for s in top_steps[:6]:
            add(s, top)

        # Supporting articles: only steps that share vocabulary with the ticket, max 2 each.
        for doc in docs[1:]:
            if doc.score < 0.5 * top.score and not analysis.safety_flag:
                continue
            _, doc_escalate, doc_steps = _parse(doc)
            ranked = sorted(doc_steps, key=lambda s: len(_words(s) & query_words), reverse=True)
            added = 0
            for s in ranked:
                if added == 2 or len(_words(s) & query_words) == 0:
                    break
                add(s, doc)
                added += 1
            if not escalate and doc_escalate:
                escalate = doc_escalate

        return Resolution(
            status="SAFETY_ESCALATION" if analysis.safety_flag else "OK",
            generator=self.name, likely_cause=cause, steps=steps, escalate_if=escalate,
            safety_notice=SAFETY_NOTICE if analysis.safety_flag else "",
            sources=[f"{d.id} - {d.title}" for d in docs],
        )


class LLMGenerator:
    name = "llm"

    def __init__(self, fallback=None):
        self.fallback = fallback or ExtractiveGenerator()

    def generate(self, ticket, analysis, docs, context="") -> Resolution:
        if not docs:
            return self.fallback.generate(ticket, analysis, docs)
        payload = json.dumps({
            "model": config.LLM_MODEL, "max_tokens": 900,
            "messages": [{"role": "user", "content": create_prompt(ticket, analysis, context or build_context(docs))}],
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages", data=payload, method="POST",
            headers={"content-type": "application/json", "x-api-key": config.LLM_API_KEY,
                     "anthropic-version": "2023-06-01"},
        )
        try:
            with urllib.request.urlopen(req, timeout=config.LLM_TIMEOUT_SECONDS) as resp:
                body = json.loads(resp.read())
            text = "".join(b.get("text", "") for b in body.get("content", []) if b.get("type") == "text").strip()
            if not text:
                raise ValueError("empty LLM response")
        except (urllib.error.URLError, ValueError, TimeoutError, OSError) as exc:
            res = self.fallback.generate(ticket, analysis, docs)
            res.message = f"(LLM unavailable: {type(exc).__name__}; showing extractive answer.)"
            return res
        return Resolution(
            status="SAFETY_ESCALATION" if analysis.safety_flag else "OK", generator=self.name, message=text,
            safety_notice=SAFETY_NOTICE if analysis.safety_flag else "",
            sources=[f"{d.id} - {d.title}" for d in docs],
        )


def get_generator():
    if config.USE_LLM and config.LLM_API_KEY:
        return LLMGenerator()
    return ExtractiveGenerator()
