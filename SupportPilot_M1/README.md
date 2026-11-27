# SupportPilot – AI Ticket Resolution Agent
## Milestone 1 (Weeks 1–2): Ticket Processing & Classification

**Domain used for this implementation:** an **EV charging network** support desk (stuck connectors,
safety hazards, billing, RFID cards, OCPP connectivity) — instead of the usual VPN/password example.
The architecture is identical to the brief and works for any IT/support domain.

## Agenda → where it lives in the code

| # | Milestone-1 agenda item | Implemented in |
|---|---|---|
| 1 | Ticket submission (web form: name, email, title, description, department) | `templates/index.html` |
| 2 | Ticket ingestion → standard JSON via REST API | `app.py` (`POST /api/tickets`) |
| 3 | Storage | `database.py` (SQLite `tickets.db`) |
| 4 | Text pre-processing (lowercase, strip ids/symbols, tokenise, n-grams) | `classifier.py → preprocess()` |
| 5 | AI ticket classification (TF-IDF + Logistic Regression, 7 categories) | `classifier.py`, `train_model.py` |
| 6 | Severity prediction (ML model + safety/urgency rules, explainable reasons) | `severity.py`, `triage.py` |
| 7 | Priority P1–P4 from severity **and** business impact (+ SLA target) | `severity.py → calculate_priority()` |
| 8 | Display classification result + live stats | `templates/index.html`, `GET /api/stats` |
| 9 | Evaluation vs. targets (≥90 % classification, ≥85 % severity) | `evaluate.py` → `evaluation_report.md` |

## Folder structure
```
SupportPilot_M1/
├── app.py                 Flask backend + REST API
├── classifier.py          preprocessing + TF-IDF/LogReg models
├── severity.py            severity rules, business impact, priority matrix
├── triage.py              text -> category/severity/priority (used by API and evaluation)
├── database.py            SQLite storage
├── train_model.py         trains + saves models/ticket_classifier.pkl
├── evaluate.py            accuracy vs. milestone targets
├── generate_dataset.py    builds the synthetic labelled dataset
├── data/                  training_tickets.csv, test_tickets.csv, test_tickets_v2.csv
├── models/                ticket_classifier.pkl (pre-trained)
├── templates/index.html   Bootstrap UI
├── evaluation_report.md   latest evaluation output
└── requirements.txt
```

## Run it
```bash
pip install -r requirements.txt
python generate_dataset.py     # optional – data already included
python train_model.py          # optional – model already included
python evaluate.py             # prints accuracy report
python app.py                  # open http://127.0.0.1:5000
```
> The included `models/ticket_classifier.pkl` was trained with scikit-learn 1.9. If you see a version warning or error,
> just run `python train_model.py` to rebuild it for your installed version (takes a few seconds).

### Try the REST API
```bash
curl -X POST http://127.0.0.1:5000/api/tickets -H "Content-Type: application/json" -d '{
  "title": "Connector stuck",
  "description": "The plug is stuck in my car and I have an important client meeting in 30 minutes"
}'
curl http://127.0.0.1:5000/api/tickets
curl http://127.0.0.1:5000/api/stats
```

## How classification works
```
Ticket text → preprocess → TF-IDF (word 1-2 grams + character 3-5 grams)
            → Logistic Regression → Category + confidence
            → Logistic Regression → ML severity
            → rules: safety keywords force Critical; urgency words raise severity one level
            → business impact (fleet / all chargers / whole site …)
            → priority matrix → P1..P4 + SLA target
```
Priority matrix: Critical → P1 · High+High impact → P1 · High → P2 · Medium+High impact → P2 · Medium → P3 · Low+High impact → P3 · else P4.

## Evaluation results (actual output of `python evaluate.py`)

| Test set | Tickets | Category accuracy (target ≥ 90 %) | Severity accuracy (target ≥ 85 %) |
|---|---|---|---|
| Held-out set 1 | 174 | **94.3 % – PASS** | 73.6 % – below target |
| Fresh held-out set 2 | 174 | 85.6 % – below target | 79.9 % – below target |

**Be upfront about this in your demo:**
- The data is **synthetic**, written by the project author. Test sentences were never in training.
- Round 1 scored ~70 % / 74 %; the training vocabulary was then widened and character n-grams were added.
  Set 1 was used to diagnose that, so **set 2 is the cleaner number**.
- Category target is met on set 1 but not set 2; **severity is below the 85 % target on both**. Severity is genuinely
  harder to infer from wording alone (e.g. "charger refuses my card" can be Low or Medium).
- Safety/Critical cases are caught reliably because of the explicit rule layer.
- To reach the targets: train on real, human-labelled tickets (a few hundred per class) and re-run `evaluate.py`.
  Do not quote the numbers above as final project results.
