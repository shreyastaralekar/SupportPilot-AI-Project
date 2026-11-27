"""
SupportPilot - Milestone 2: Knowledge Retrieval & Resolution Generation (Flask)

  GET  /                 web UI
  GET  /api/kb           knowledge base article list
  POST /api/resolve      run the full RAG pipeline on a ticket
  POST /api/feedback     agent marks a resolution helpful / not helpful
  GET  /api/metrics      retrieval accuracy (from evaluation), resolution rate (from feedback), avg response time (live)
  GET  /api/health
"""
import json
import os
import threading
from collections import deque

from flask import Flask, jsonify, render_template, request

import config
import store
from models.schemas import Ticket
from rag.generator import get_generator
from rag.pipeline import RAGPipeline
from rag.retriever import KnowledgeRetriever, load_knowledge_base

app = Flask(__name__)

KB = load_knowledge_base()
pipeline = RAGPipeline(KnowledgeRetriever(KB), get_generator())

_times = deque(maxlen=200)
_counter = {"n": 0}
_lock = threading.Lock()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/kb")
def kb():
    return jsonify([{k: d[k] for k in ("id", "title", "category", "source", "last_updated")} for d in KB])


@app.route("/api/resolve", methods=["POST"])
def resolve():
    data = request.get_json(silent=True) or {}
    title, description = str(data.get("title", "")).strip(), str(data.get("description", "")).strip()
    if not title or not description:
        return jsonify({"error": "title and description are required"}), 400
    with _lock:
        _counter["n"] += 1
        ticket_id = f"T-2026-{4520 + _counter['n']}"
    ticket = Ticket(id=ticket_id, title=title, description=description,
                    category=(data.get("category") or None), priority=(data.get("priority") or None))
    result = pipeline.run(ticket)
    _times.append(result["total_ms"])
    return jsonify(result)


@app.route("/api/feedback", methods=["POST"])
def feedback():
    data = request.get_json(silent=True) or {}
    if "ticket_id" not in data or "helpful" not in data:
        return jsonify({"error": "ticket_id and helpful are required"}), 400
    store.add_feedback(str(data["ticket_id"]), bool(data["helpful"]))
    return jsonify(store.resolution_stats())


@app.route("/api/metrics")
def metrics():
    evaluation = None
    if config.EVAL_RESULTS_PATH.exists():
        evaluation = json.loads(config.EVAL_RESULTS_PATH.read_text())
    avg = round(sum(_times) / len(_times), 1) if _times else None
    return jsonify({
        "retrieval_accuracy": evaluation["retrieval_accuracy_top1"] if evaluation else None,
        "retrieval_eval_n": evaluation["n_tickets"] if evaluation else None,
        "avg_response_ms": avg,
        "requests_served": len(_times),
        "generator": pipeline.generator.name,
        **store.resolution_stats(),
    })


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "kb_articles": len(KB), "generator": pipeline.generator.name})


if __name__ == "__main__":
    app.run(debug=False, port=int(os.environ.get("PORT", 5001)))
