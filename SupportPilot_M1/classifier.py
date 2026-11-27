"""
Ticket classification for SupportPilot.

Two ML models (TF-IDF + Logistic Regression):
  1. category model  -> which kind of problem is this?
  2. severity model  -> how serious is it?
A small rule layer (severity.py) then applies safety overrides and urgency
boosts on top of the ML severity, so dangerous reports are never under-rated.
"""
import re
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

BASE_DIR = Path(__file__).parent
MODEL_PATH = BASE_DIR / "models" / "ticket_classifier.pkl"


def preprocess(text: str) -> str:
    """Lowercase -> strip station ids -> remove symbols -> collapse spaces."""
    text = str(text).lower()
    text = re.sub(r"\bcp-?\d+\b", " ", text)       # station ids carry no signal
    text = re.sub(r"[^a-z0-9\s]", " ", text)        # remove punctuation/symbols
    return re.sub(r"\s+", " ", text).strip()


def build_pipeline() -> Pipeline:
    features = FeatureUnion(
        [
            # word 1-2 grams keep phrases such as "not working", "stuck connector"
            ("word", TfidfVectorizer(preprocessor=preprocess, ngram_range=(1, 2), sublinear_tf=True)),
            # character 3-5 grams cope with spelling/word-form variants (recognised/recognized, charging/charge)
            ("char", TfidfVectorizer(preprocessor=preprocess, analyzer="char_wb",
                                     ngram_range=(3, 5), sublinear_tf=True)),
        ]
    )
    return Pipeline([("tfidf", features), ("clf", LogisticRegression(max_iter=3000, C=10))])


class TicketClassifier:
    def __init__(self, model_path: Path = MODEL_PATH):
        bundle = joblib.load(model_path)
        self.category_model = bundle["category_model"]
        self.severity_model = bundle["severity_model"]

    def predict_category(self, text: str):
        probs = self.category_model.predict_proba([text])[0]
        idx = probs.argmax()
        return self.category_model.classes_[idx], float(probs[idx])

    def predict_severity_ml(self, text: str):
        probs = self.severity_model.predict_proba([text])[0]
        idx = probs.argmax()
        return self.severity_model.classes_[idx], float(probs[idx])
