"""Run:  python -m unittest discover -s tests -v   (from the SupportPilot_M2 folder)"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402

config.FEEDBACK_DB = Path(tempfile.mkdtemp()) / "test_feedback.db"   # keep tests away from real data

import app as app_module  # noqa: E402
from models.schemas import Ticket  # noqa: E402
from rag.pipeline import RAGPipeline  # noqa: E402
from rag.retriever import KnowledgeRetriever, load_knowledge_base  # noqa: E402


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kb = load_knowledge_base()
        cls.pipe = RAGPipeline(KnowledgeRetriever(cls.kb))

    def run_ticket(self, title, desc="", **kw):
        return self.pipe.run(Ticket("T-TEST", title, desc, **kw))

    def test_stuck_connector_retrieves_kb001(self):
        r = self.run_ticket("Connector stuck in my car", "The plug will not release from the port")
        self.assertEqual(r["retrieved_documents"][0]["id"], "KB001")
        self.assertEqual(r["resolution"]["status"], "OK")

    def test_every_step_is_cited_to_a_retrieved_article(self):
        r = self.run_ticket("Charged twice", "I was billed two times for one charge and need a refund")
        used = set(r["used_documents"])
        self.assertTrue(r["resolution"]["steps"])
        for step in r["resolution"]["steps"]:
            self.assertIn(step["source_id"], used)

    def test_safety_report_escalates_and_leads_with_safety_procedure(self):
        r = self.run_ticket("Smoke from charger", "I saw smoke and smelled burning")
        self.assertTrue(r["analysis"]["safety_flag"])
        self.assertEqual(r["resolution"]["status"], "SAFETY_ESCALATION")
        self.assertIn("emergency", r["resolution"]["safety_notice"].lower())
        self.assertEqual(r["resolution"]["steps"][0]["source_id"], "KB004")
        self.assertEqual(r["analysis"]["priority"], "P1")

    def test_off_topic_ticket_is_rejected_not_hallucinated(self):
        r = self.run_ticket("What is the cafeteria menu", "lunch options for tomorrow")
        self.assertEqual(r["resolution"]["status"], "INSUFFICIENT_KNOWLEDGE")
        self.assertEqual(r["resolution"]["steps"], [])

    def test_site_wide_outage_is_p1_and_finds_runbook(self):
        r = self.run_ticket("All chargers offline at depot", "every charger at the fleet depot is offline")
        self.assertEqual(r["retrieved_documents"][0]["id"], "KB016")
        self.assertEqual(r["analysis"]["priority"], "P1")

    def test_category_is_detected_when_not_provided(self):
        r = self.run_ticket("RFID card not working", "I tap my badge and nothing happens")
        self.assertEqual(r["analysis"]["category_source"], "detected")
        self.assertEqual(r["analysis"]["category"], "RFID & Authentication")

    def test_all_four_workflow_stages_are_timed(self):
        r = self.run_ticket("Charger offline", "dashboard shows offline since morning")
        self.assertEqual(len(r["workflow"]), 4)
        self.assertTrue(all(s["status"] == "completed" for s in r["workflow"]))


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()

    def test_health(self):
        self.assertEqual(self.client.get("/api/health").get_json()["kb_articles"], 16)

    def test_resolve_validates_input(self):
        self.assertEqual(self.client.post("/api/resolve", json={"title": "x"}).status_code, 400)

    def test_resolve_and_feedback_roundtrip(self):
        r = self.client.post("/api/resolve", json={"title": "Plug stuck", "description": "connector will not release"})
        self.assertEqual(r.status_code, 200)
        tid = r.get_json()["ticket"]["id"]
        self.assertIsNone(self.client.get("/api/metrics").get_json()["resolution_rate"])
        self.client.post("/api/feedback", json={"ticket_id": tid, "helpful": True})
        stats = self.client.post("/api/feedback", json={"ticket_id": tid, "helpful": False}).get_json()
        self.assertEqual(stats["feedback_count"], 2)
        self.assertEqual(stats["resolution_rate"], 0.5)


if __name__ == "__main__":
    unittest.main()
