"""Custom features shared by training and serving (must be importable when the model is unpickled)."""

import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


def vader_features(texts) -> np.ndarray:
    """VADER lexicon scores (neg, neu, pos, compound): captures negation ("not bad"), intensifiers and emojis."""
    scores = [_analyzer.polarity_scores(t) for t in texts]
    return np.array([[s["neg"], s["neu"], s["pos"], s["compound"]] for s in scores])
