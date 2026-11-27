"""
SupportPilot - Milestone 1: Ticket Processing & Classification (Flask backend)

Endpoints
  GET  /                    web UI (submit + results dashboard)
  POST /api/tickets         submit a ticket (JSON or form) -> classify -> store -> return result
  GET  /api/tickets         list recent tickets
  GET  /api/tickets/<id>    one ticket
  GET  /api/stats           live statistics computed from the database
"""
import os

from flask import Flask, jsonify, render_template, request

import database
from triage import triage

app = Flask(__name__)
database.init_db()

REQUIRED = ["title", "description"]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/tickets", methods=["POST"])
def create_ticket():
    data = request.get_json(silent=True) or request.form.to_dict()
    missing = [f for f in REQUIRED if not str(data.get(f, "")).strip()]
    if missing:
        return jsonify({"error": f"Missing required field(s): {', '.join(missing)}"}), 400

    result = triage(data["title"].strip(), data["description"].strip())
    ticket = {
        "employee_name": data.get("employee_name", "").strip(),
        "email": data.get("email", "").strip(),
        "department": data.get("department", "").strip(),
        "title": data["title"].strip(),
        "description": data["description"].strip(),
        "status": "Open",
        **{k: result[k] for k in (
            "category", "category_conf", "severity", "severity_conf",
            "business_impact", "priority", "processing_ms")},
    }
    ticket_id = database.insert_ticket(ticket)
    return jsonify({"ticket_id": ticket_id, "status": "Open", **ticket, **{
        "sla_target": result["sla_target"], "reasons": result["reasons"]}}), 201


@app.route("/api/tickets", methods=["GET"])
def list_tickets():
    return jsonify(database.list_tickets(limit=int(request.args.get("limit", 20))))


@app.route("/api/tickets/<ticket_id>")
def get_ticket(ticket_id):
    ticket = database.get_ticket(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404
    return jsonify(ticket)


@app.route("/api/stats")
def stats():
    return jsonify(database.stats())


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
