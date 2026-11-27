"""
Milestone-1 evaluation against the brief's targets:
    classification accuracy >= 90%     severity accuracy >= 85%

Two held-out sets whose base sentences were NEVER used in training:
    data/test_tickets.csv     - first held-out set (also used to diagnose round-1 weakness)
    data/test_tickets_v2.csv  - fresh set written after training data + rules were frozen
Writes evaluation_report.md

Run:  python evaluate.py
"""
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

from triage import triage

CAT_TARGET, SEV_TARGET = 0.90, 0.85
SETS = [("Held-out set 1", "data/test_tickets.csv"), ("Fresh held-out set 2 (v2)", "data/test_tickets_v2.csv")]
LABELS = ["Low", "Medium", "High", "Critical"]


def status(acc, tgt):
    return "PASS" if acc >= tgt else "BELOW TARGET"


def evaluate(path):
    df = pd.read_csv(path)
    preds = [triage("", t) for t in df["ticket"]]
    df["pred_category"] = [p["category"] for p in preds]
    df["pred_severity"] = [p["severity"] for p in preds]
    df["pred_priority"] = [p["priority"] for p in preds]
    df["ms"] = [p["processing_ms"] for p in preds]
    return df


def main():
    lines = ["# SupportPilot - Milestone 1 Evaluation Report", "",
             "| Test set | Tickets | Category acc. (target >= 90%) | Severity acc. (target >= 85%) | Avg time |",
             "|---|---|---|---|---|"]
    details, frames = [], {}
    for name, path in SETS:
        df = evaluate(path)
        frames[name] = df
        cat = (df["category"] == df["pred_category"]).mean()
        sev = (df["severity"] == df["pred_severity"]).mean()
        lines.append(f"| {name} | {len(df)} | {cat:.1%} ({status(cat, CAT_TARGET)}) | "
                     f"{sev:.1%} ({status(sev, SEV_TARGET)}) | {df['ms'].mean():.1f} ms |")

        cm = confusion_matrix(df["severity"], df["pred_severity"], labels=LABELS)
        details += [
            "", f"## {name}", "", "### Category report", "```",
            classification_report(df["category"], df["pred_category"], zero_division=0), "```",
            "### Severity report", "```",
            classification_report(df["severity"], df["pred_severity"], zero_division=0), "```",
            "### Severity confusion matrix (rows = actual, cols = predicted)", "```",
            "            " + "  ".join(f"{l:>8}" for l in LABELS),
            *[f"{lab:>10}  " + "  ".join(f"{v:>8}" for v in row) for lab, row in zip(LABELS, cm)],
            "```",
        ]
    lines += details + [
        "", "## Honest caveats",
        "- Data is **synthetic** and written by the project author; it shows the pipeline works end-to-end.",
        "- Round 1 (8 base complaints/category) scored ~70% category / ~74% severity on held-out set 1, so the training",
        "  vocabulary was widened. Set 1 was used to diagnose that, so set 2 is the cleaner measurement.",
        "- Re-run on real support tickets before quoting final accuracy.",
    ]
    report = "\n".join(lines)
    open("evaluation_report.md", "w", encoding="utf-8").write(report)
    print(report)

    for name, df in frames.items():
        wrong = df[(df["category"] != df["pred_category"]) | (df["severity"] != df["pred_severity"])]
        if len(wrong):
            print(f"\nExample misclassifications - {name}:")
            print(wrong[["ticket", "category", "pred_category", "severity", "pred_severity"]]
                  .drop_duplicates("ticket").head(6).to_string(index=False))


if __name__ == "__main__":
    main()
