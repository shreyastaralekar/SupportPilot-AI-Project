"""Trains TF-IDF + Logistic Regression models for sub-category and severity."""
from pathlib import Path
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from make_dataset import build

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "tickets.csv"


def fit(X, y):
    mk = lambda: make_pipeline(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True), LogisticRegression(max_iter=1000))
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    return mk().fit(X, y), mk().fit(Xtr, ytr).score(Xte, yte)


def main():
    if not CSV.exists():
        build(CSV)
    df = pd.read_csv(CSV)
    sub, a1 = fit(df.text, df.sub_category)
    sev, a2 = fit(df.text, df.severity)
    parent = df.drop_duplicates("sub_category").set_index("sub_category").category.to_dict()
    metrics = {"sub_category": round(a1 * 100, 1), "severity": round(a2 * 100, 1), "accuracy": round((a1 + a2) * 50, 1)}
    (ROOT / "models").mkdir(exist_ok=True)
    joblib.dump({"sub": sub, "sev": sev, "parent": parent, "metrics": metrics}, ROOT / "models" / "classifier.joblib")
    print("Trained on", len(df), "tickets. Hold-out accuracy:", metrics)


if __name__ == "__main__":
    main()
