"""Train the demo sentiment model and save it as a single artifact file.

Run from the project root:  python training/train.py
"""

import csv
import sys
from pathlib import Path

import joblib
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "training" / "data" / "sentiment_data.csv"
MODEL_PATH = PROJECT_ROOT / "model" / "sentiment_model.joblib"
MODEL_VERSION = "1.0.0"


def load_data(path: Path) -> tuple[list[str], list[str]]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [r["text"] for r in rows], [r["label"] for r in rows]


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            # Character n-grams generalise better than whole words on a tiny dataset.
            ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True)),
            ("clf", LogisticRegression(C=10.0, max_iter=1000, random_state=42)),
        ]
    )


def main() -> int:
    texts, labels = load_data(DATA_PATH)
    print(f"Loaded {len(texts)} examples from {DATA_PATH.name}")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(build_pipeline(), texts, labels, cv=cv)
    print(f"5-fold cross-validation accuracy: {scores.mean():.2f} (+/- {scores.std():.2f})")

    pipeline = build_pipeline().fit(texts, labels)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "pipeline": pipeline,
            "version": MODEL_VERSION,
            "sklearn_version": sklearn.__version__,
            "classes": [str(c) for c in pipeline.classes_],
            "training_examples": len(texts),
        },
        MODEL_PATH,
    )
    print(f"Saved model v{MODEL_VERSION} to {MODEL_PATH.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
