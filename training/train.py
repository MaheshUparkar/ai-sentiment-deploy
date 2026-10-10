"""Train the sentiment model on public datasets + hand-written business sentences, evaluate it, and save it.

Run from the project root:  python training/train.py
"""

import csv
import sys
import time
from pathlib import Path

import joblib
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import FunctionTransformer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from app.features import vader_features  # noqa: E402

DATA_DIR = PROJECT_ROOT / "training" / "data"
MODEL_PATH = PROJECT_ROOT / "model" / "sentiment_model.joblib"
MODEL_VERSION = "2.0.0"
# Hand-written business sentences are few but closest to how the demo is used, so they count more.
BUSINESS_WEIGHT = 3.0


def load(name: str) -> tuple[list[str], list[str]]:
    with (DATA_DIR / name).open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return [r["text"] for r in rows], [r["label"] for r in rows]


def build_pipeline() -> Pipeline:
    # Settings chosen by macro-F1 on public/tweets_val.csv.
    features = FeatureUnion(
        [
            ("words", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=60000, sublinear_tf=True)),
            ("chars", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=3, max_features=100000, sublinear_tf=True)),
            ("vader", FunctionTransformer(vader_features)),
        ]
    )
    clf = LogisticRegression(C=1.0, max_iter=3000, class_weight="balanced")
    return Pipeline([("features", features), ("clf", clf)])


def evaluate(pipeline: Pipeline, name: str) -> dict:
    texts, labels = load(name)
    preds = pipeline.predict(texts)
    acc, f1 = accuracy_score(labels, preds), f1_score(labels, preds, average="macro")
    print(f"  {name:28s} n={len(texts):5d}  accuracy={acc:.3f}  macro-F1={f1:.3f}")
    return {"dataset": name, "n": len(texts), "accuracy": round(acc, 3), "macro_f1": round(f1, 3), "preds": preds, "labels": labels}


def main() -> int:
    sources = {
        "public/tweets_train.csv": 1.0,
        "public/uci_sentences.csv": 1.0,
        "business_train.csv": BUSINESS_WEIGHT,
    }
    texts, labels, weights = [], [], []
    for name, weight in sources.items():
        x, y = load(name)
        texts += x
        labels += y
        weights += [weight] * len(x)
        print(f"Loaded {len(x):6d} examples from {name}")

    start = time.time()
    pipeline = build_pipeline().fit(texts, labels, clf__sample_weight=weights)
    print(f"Trained on {len(texts)} examples in {time.time() - start:.0f}s")

    print("Evaluation on held-out data (never used for training):")
    test = evaluate(pipeline, "public/tweets_test.csv")
    business = evaluate(pipeline, "business_eval.csv")
    print(classification_report(test["labels"], test["preds"], digits=3))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "pipeline": pipeline,
            "version": MODEL_VERSION,
            "sklearn_version": sklearn.__version__,
            "classes": [str(c) for c in pipeline.classes_],
            "training_examples": len(texts),
            "metrics": {
                "test_accuracy": test["accuracy"],
                "test_macro_f1": test["macro_f1"],
                "business_eval_accuracy": business["accuracy"],
            },
        },
        MODEL_PATH,
        compress=3,
    )
    size_mb = MODEL_PATH.stat().st_size / 1e6
    print(f"Saved model v{MODEL_VERSION} ({size_mb:.1f} MB) to {MODEL_PATH.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
