import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main
from training import train

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session", autouse=True)
def trained_model():
    if not main.MODEL_PATH.exists():
        subprocess.run([sys.executable, str(PROJECT_ROOT / "training" / "train.py")], check=True)


@pytest.fixture
def client():
    with TestClient(main.app) as c:
        yield c


def test_health_ok(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True
    assert body["model_version"]
    assert 0 < body["model_metrics"]["test_accuracy"] <= 1


def test_index_serves_ui(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "AI Sentiment Demo" in res.text


def test_predict_returns_valid_structure(client):
    res = client.post("/predict", json={"text": "The new AI assistant has made our team's work much faster."})
    assert res.status_code == 200
    body = res.json()
    assert body["sentiment"] in {"positive", "negative", "neutral"}
    assert set(body["probabilities"]) == {"positive", "negative", "neutral"}
    assert abs(sum(body["probabilities"].values()) - 1.0) < 0.01
    assert body["confidence"] == body["probabilities"][body["sentiment"]]


@pytest.mark.parametrize(
    "text, expected",
    [
        ("The new AI assistant has made our team's work much faster.", "positive"),
        ("The service was horrible and slow", "negative"),
        ("The meeting is on Friday at 3 pm", "neutral"),
    ],
)
def test_predict_demo_sentences(client, text, expected):
    assert client.post("/predict", json={"text": text}).json()["sentiment"] == expected


def test_predict_is_deterministic(client):
    payload = {"text": "Our deployment failed again"}
    assert client.post("/predict", json=payload).json() == client.post("/predict", json=payload).json()


def test_quality_on_held_out_business_sentences(client):
    texts, labels = train.load("business_eval.csv")
    preds = [client.post("/predict", json={"text": t}).json()["sentiment"] for t in texts]
    accuracy = sum(p == y for p, y in zip(preds, labels)) / len(labels)
    # Regression guard: v2 scores 0.90; v1 scored 0.82.
    assert accuracy >= 0.87


@pytest.mark.parametrize("payload", [{"text": ""}, {"text": "   "}, {}, {"text": "x" * 1001}, {"text": 123}])
def test_predict_rejects_invalid_input(client, payload):
    assert client.post("/predict", json=payload).status_code == 422


def test_missing_model_is_reported(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "MODEL_PATH", tmp_path / "missing.joblib")
    with TestClient(main.app) as c:
        health = c.get("/health")
        assert health.status_code == 503
        assert health.json()["detail"]["model_loaded"] is False
        assert c.post("/predict", json={"text": "hello"}).status_code == 503
