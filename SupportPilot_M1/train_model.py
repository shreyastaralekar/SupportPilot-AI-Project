"""
Trains the category and severity models and saves them to models/ticket_classifier.pkl

Run:  python train_model.py
"""
import joblib
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from classifier import MODEL_PATH, build_pipeline

DATA = "data/training_tickets.csv"


def main():
    df = pd.read_csv(DATA)
    print(f"Loaded {len(df)} training tickets, "
          f"{df['category'].nunique()} categories, {df['severity'].nunique()} severity levels\n")

    # Quick hold-out sanity check (note: variants of the same base sentence can land in both
    # halves, so this number is optimistic -- the REAL measurement is evaluate.py on test_tickets.csv)
    X_tr, X_va, yc_tr, yc_va, ys_tr, ys_va = train_test_split(
        df["ticket"], df["category"], df["severity"], test_size=0.2, random_state=42,
        stratify=df["category"],
    )
    quick_cat = build_pipeline().fit(X_tr, yc_tr)
    quick_sev = build_pipeline().fit(X_tr, ys_tr)
    print(f"Validation split (optimistic) category accuracy: "
          f"{accuracy_score(yc_va, quick_cat.predict(X_va)):.1%}")
    print(f"Validation split (optimistic) severity accuracy: "
          f"{accuracy_score(ys_va, quick_sev.predict(X_va)):.1%}\n")

    # Final models are trained on ALL training data
    category_model = build_pipeline().fit(df["ticket"], df["category"])
    severity_model = build_pipeline().fit(df["ticket"], df["severity"])

    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump({"category_model": category_model, "severity_model": severity_model}, MODEL_PATH)
    print(f"Saved models -> {MODEL_PATH}")
    print("Next: python evaluate.py   (measures accuracy on unseen test_tickets.csv)")


if __name__ == "__main__":
    main()
