# SupportPilot – AI Ticket Resolution Agent
## Milestone 2 (Weeks 3–4): Knowledge Retrieval & Resolution Generation

**Domain used:** EV charging network support (stuck connectors, safety incidents, billing, RFID, OCPP connectivity).
Architecture follows the milestone brief exactly: **Ticket → Analysis → KB Retrieval → Context Augmentation → Generation → Resolution.**

## Agenda → where it lives in the code

| # | Milestone-2 agenda item | Implemented in |
|---|---|---|
| 1 | Enterprise knowledge base (16 articles, with source + last-updated) | `data/knowledge_base.json` |
| 2 | Ticket analysis & query generation (category, keywords, safety flag, query) | `rag/analyzer.py` |
| 3 | Knowledge-base search – TF-IDF + cosine similarity (the **R** in RAG) | `rag/retriever.py` |
| 4 | Relevance threshold → "insufficient knowledge" instead of guessing | `config.py`, `rag/pipeline.py` |
| 5 | Context augmentation (retrieved articles → context block) | `rag/generator.py → build_context()` |
| 6 | Grounded resolution generation with **citations** | `rag/generator.py` |
| 7 | Optional real-LLM mode (grounded prompt, Anthropic API over HTTPS) | `rag/generator.py → LLMGenerator` |
| 8 | End-to-end RAG pipeline with per-stage timing ("RAG Workflow Status") | `rag/pipeline.py` |
| 9 | Web UI mirroring the milestone screenshot | `templates/index.html`, `app.py` |
| 10 | Metrics: retrieval accuracy, resolution rate, avg response time (all measured) | `evaluate_retrieval.py`, `store.py`, `/api/metrics` |
| 11 | Automated tests | `tests/test_pipeline.py` |

## Folder structure
```
SupportPilot_M2/
├── app.py                    Flask API + UI
├── config.py                 top-k, relevance threshold, optional LLM settings
├── store.py                  agent feedback (for Resolution Rate)
├── evaluate_retrieval.py     retrieval accuracy + threshold sweep
├── data/knowledge_base.json  enterprise KB
├── rag/  analyzer.py retriever.py generator.py pipeline.py
├── models/schemas.py         dataclasses passed between stages
├── templates/index.html
├── tests/test_pipeline.py
├── script.md                 DEMO SCRIPT + viva Q&A
└── requirements.txt
```

## Run it
```bash
pip install -r requirements.txt
python evaluate_retrieval.py          # measures retrieval accuracy -> data/eval_results.json
python evaluate_retrieval.py
python app.py                         # open http://127.0.0.1:5001
```
(Milestone 1 runs on port 5000, so both can be open side by side.)

### Optional: real LLM generation
```bash
export ANTHROPIC_API_KEY=your_key
export SUPPORTPILOT_USE_LLM=1         # optional: SUPPORTPILOT_MODEL to change the model
python app.py
```
The default **extractive generator** needs no key: it assembles the answer only from retrieved KB text, so it cannot invent steps.
The LLM path uses the same retrieved context and a grounding prompt, and falls back to the extractive answer if the API call fails.
*The LLM path was written to the API spec but not run in the build environment (no network or key there) – test it once with your key before demoing it.*

## Design decisions worth knowing
- **Safety first:** any smoke/burning/sparks/shock report forces the Safety article to the top, shows a red safety banner and sets P1.
- **No guessing:** if no article reaches `MIN_RELEVANCE`, the system says "insufficient knowledge" and recommends escalation.
- **Threshold = 0.10, not 0.30:** TF-IDF scores are small on a small KB. In `evaluate_retrieval.py`'s sweep, 0.30 would reject 56 % of valid tickets while 0.10 accepts all and still rejects all 6 off-topic queries.
- **Metrics are measured:** retrieval accuracy comes from the evaluation script, resolution rate from agent 👍/👎 feedback (shows *n/a* until rated), response time is live.

## Measured results (this build)
| Metric | Result | How measured |
|---|---|---|
| Retrieval accuracy (top-1) | 32/32 = 100 % | `evaluate_retrieval.py`, 32 labelled tickets |
| Top-3 hit rate / MRR | 100 % / 1.00 | same |
| Out-of-scope rejection | 6/6 | 6 off-topic questions |
| Avg retrieval time | ≈ 2–3 ms | same |
| Tests | 10/10 pass | `unittest` |

**Caveat – say this out loud in the demo:** the 100 % is optimistic. The KB and test tickets were written by the same author, the
KB articles contain a "Symptoms" section in customer language, and the test set is small. It proves the pipeline works; it is not a
benchmark. With a real KB and real tickets expect lower numbers, and consider embeddings (see `script.md`, Q&A).
Resolution rate has no value until agents give feedback – the brief's 78 % is an example, not something we measured.
