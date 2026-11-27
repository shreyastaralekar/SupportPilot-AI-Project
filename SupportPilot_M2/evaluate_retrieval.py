"""
Measures retrieval quality so the dashboard shows REAL numbers, not hard-coded ones.

  Retrieval accuracy (top-1)  = tickets whose expected KB article is ranked #1
  Top-3 hit rate              = expected article appears in the top 3
  MRR                         = mean reciprocal rank of the expected article
  Out-of-scope rejection      = off-topic questions correctly answered with INSUFFICIENT_KNOWLEDGE
  Threshold sweep             = justifies the MIN_RELEVANCE setting in config.py

Test tickets are written in everyday customer language (different wording from the KB articles),
but by the same author as the KB, and the set is small - treat results as a smoke test, not a benchmark.

Run:  python evaluate_retrieval.py   -> prints a report and writes data/eval_results.json
"""
import json
import time
from datetime import date

import config
from models.schemas import Ticket
from rag.analyzer import analyze_ticket
from rag.retriever import KnowledgeRetriever, load_knowledge_base

IN_SCOPE = [
    ("Connector won't release from my car after charging finished", "KB001"),
    ("plug is stuck in the port, can't pull it out", "KB001"),
    ("The screen on charger bay 3 is completely black", "KB002"),
    ("charger display frozen on the logo screen", "KB002"),
    ("Charging cable insulation is cracked and the copper is showing", "KB003"),
    ("the cable has been run over and the connector housing is split", "KB003"),
    ("smoke coming out of the charging unit", "KB004"),
    ("strong burning smell near charger, sparks when plugging in", "KB004"),
    ("I felt a tingling electric shock from the charger handle", "KB005"),
    ("water is dripping inside the charger cabinet after the storm", "KB005"),
    ("I was billed twice for one charge", "KB006"),
    ("need a refund, the session failed but I was still charged", "KB006"),
    ("my card got declined at the charger but it works in shops", "KB007"),
    ("payment failed at the terminal but charging started", "KB007"),
    ("please send me an invoice for last month's charging", "KB008"),
    ("need VAT receipt for company expense claims", "KB008"),
    ("can't sign in to the mobile app, says invalid password", "KB009"),
    ("reset password email never arrives", "KB009"),
    ("my RFID card is not read by the charger", "KB010"),
    ("tap my membership card and nothing happens", "KB010"),
    ("plug and charge fails to authenticate my car", "KB011"),
    ("vehicle certificate error when auto-start charging", "KB011"),
    ("charging does not start after plugging in", "KB012"),
    ("session stops after a few minutes and shows error", "KB012"),
    ("only getting 7 kW on a fast charger", "KB013"),
    ("charging speed very slow compared to normal", "KB013"),
    ("charger shows offline in the dashboard since morning", "KB014"),
    ("station keeps losing connection to backend, heartbeat missed", "KB014"),
    ("firmware update stuck and charger keeps rebooting", "KB015"),
    ("charger in boot loop after upgrade", "KB015"),
    ("every charger at the depot is offline, entire site down", "KB016"),
    ("total power and network loss at whole site, no chargers responding", "KB016"),
]

OUT_OF_SCOPE = [
    "What is the cafeteria menu for tomorrow",
    "recipe for chocolate cake",
    "who won the football match last night",
    "how many days of annual leave do I get",
    "my laptop keyboard keys are sticking",
    "please book a meeting room for Friday",
]

THRESHOLDS = [0.05, 0.08, 0.10, 0.15, 0.20, 0.30]


def search(retriever, text):
    a = analyze_ticket(Ticket("EVAL", text, ""))
    return retriever.search(a.query, top_k=config.TOP_K, category=a.category)


def main():
    retriever = KnowledgeRetriever(load_knowledge_base())
    top1 = top3 = 0
    rr_sum, top_scores, times, misses = 0.0, [], [], []

    for text, expected in IN_SCOPE:
        t0 = time.perf_counter()
        results = search(retriever, text)
        times.append((time.perf_counter() - t0) * 1000)
        ids = [r.id for r in results]
        top_scores.append(results[0].score)
        if ids and ids[0] == expected:
            top1 += 1
        if expected in ids:
            top3 += 1
            rr_sum += 1 / (ids.index(expected) + 1)
        if not ids or ids[0] != expected:
            misses.append((text, expected, ids))

    oos_scores = [search(retriever, q)[0].score for q in OUT_OF_SCOPE]
    n = len(IN_SCOPE)

    sweep = []
    for th in THRESHOLDS:
        accepted = sum(s >= th for s in top_scores) / n
        rejected = sum(s < th for s in oos_scores) / len(oos_scores)
        sweep.append({"threshold": th, "in_scope_accepted": round(accepted, 3),
                      "out_of_scope_rejected": round(rejected, 3)})

    rejected_now = sum(s < config.MIN_RELEVANCE for s in oos_scores)
    results = {
        "evaluated_on": str(date.today()),
        "n_tickets": n, "n_out_of_scope": len(OUT_OF_SCOPE),
        "retrieval_accuracy_top1": round(top1 / n, 3),
        "top3_hit_rate": round(top3 / n, 3),
        "mrr": round(rr_sum / n, 3),
        "avg_retrieval_ms": round(sum(times) / n, 2),
        "min_relevance": config.MIN_RELEVANCE,
        "out_of_scope_rejection": round(rejected_now / len(OUT_OF_SCOPE), 3),
        "threshold_sweep": sweep,
    }
    with open(config.EVAL_RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print(f"In-scope tickets: {n}   Out-of-scope queries: {len(OUT_OF_SCOPE)}")
    print(f"Retrieval accuracy (top-1): {top1}/{n} = {top1 / n:.1%}")
    print(f"Top-3 hit rate:             {top3}/{n} = {top3 / n:.1%}")
    print(f"MRR:                        {rr_sum / n:.3f}")
    print(f"Avg retrieval time:         {results['avg_retrieval_ms']} ms")
    print(f"Out-of-scope rejected at MIN_RELEVANCE={config.MIN_RELEVANCE}: {rejected_now}/{len(OUT_OF_SCOPE)}")
    print("\nThreshold sweep (in-scope accepted / out-of-scope rejected):")
    for row in sweep:
        print(f"  {row['threshold']:.2f}   {row['in_scope_accepted']:.0%} / {row['out_of_scope_rejected']:.0%}")
    if misses:
        print("\nMisses:")
        for text, expected, ids in misses:
            print(f"  '{text}' expected {expected}, got {ids}")
    print(f"\nSaved -> {config.EVAL_RESULTS_PATH.name}")


if __name__ == "__main__":
    main()
