import re, sys
from pathlib import Path
import joblib

ROOT = Path(__file__).parent
MODEL = ROOT / "models" / "classifier.joblib"
if not MODEL.exists():                      # first run: train automatically
    sys.path.insert(0, str(ROOT / "src"))
    import train
    train.main()
B = joblib.load(MODEL)
BLOCKING = re.compile(r"unable|cannot|can't|not working|down|failing|fails|locked", re.I)
ACCURACY = B["metrics"]["accuracy"]


def classify(text):
    p = B["sub"].predict_proba([text])[0]
    sub = str(B["sub"].classes_[p.argmax()])
    q = B["sev"].predict_proba([text])[0]
    return B["parent"][sub], sub, float(p.max()), str(B["sev"].classes_[q.argmax()]), float(q.max())


def priority_for(severity, text):
    """Returns (label, resolve-within hours): P1 24h, P2 48h, P3 1 week, P4 4 weeks."""
    if severity == "Critical" or (severity == "High" and BLOCKING.search(text)):
        return "P1 - Critical", 24
    return {"High": ("P2 - High", 48), "Medium": ("P3 - Medium", 168), "Low": ("P4 - Low", 672)}[severity]
