"""Sentiment inference service: loads the trained model once and serves predictions over HTTP."""

import logging
import os
import socket
from contextlib import asynccontextmanager
from pathlib import Path




import joblib
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

APP_VERSION = "1.0.0"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = Path(os.getenv("MODEL_PATH", PROJECT_ROOT / "model" / "sentiment_model.joblib"))
STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_TEXT_LENGTH = 1000

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("sentiment-api")

# Holds the loaded model artifact; stays None if loading fails so the app can still report its health.
model_artifact: dict | None = None


def load_model(path: Path) -> dict | None:
    if not path.exists():
        log.error("Model file not found at %s. Run: python training/train.py", path)
        return None
    try:
        artifact = joblib.load(path)
    except Exception:
        log.exception("Failed to load model from %s", path)
        return None
    log.info("Loaded model v%s (classes=%s)", artifact["version"], artifact["classes"])
    return artifact


@asynccontextmanager
async def lifespan(_: FastAPI):
    global model_artifact
    model_artifact = load_model(MODEL_PATH)
    yield


app = FastAPI(
    title="AI Sentiment Demo",
    description="Demo model-serving API for the 'Containerization and Model Deployment' session.",
    version=APP_VERSION,
    lifespan=lifespan,
)


class PredictRequest(BaseModel):
    text: str = Field(..., max_length=MAX_TEXT_LENGTH, examples=["The new AI assistant has made our team's work much faster."])

    @field_validator("text")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Text must not be empty.")
        return value


class PredictResponse(BaseModel):
    text: str
    sentiment: str
    confidence: float
    probabilities: dict[str, float]
    model_version: str


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    body = {
        "status": "ok" if model_artifact else "model_not_loaded",
        "model_loaded": model_artifact is not None,
        "model_version": model_artifact["version"] if model_artifact else None,
        "model_metrics": model_artifact.get("metrics") if model_artifact else None,
        "app_version": APP_VERSION,
        # The container's hostname: shows the audience which container answered.
        "served_by": socket.gethostname(),
    }
    if model_artifact is None:
        raise HTTPException(status_code=503, detail=body)
    return body


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    if model_artifact is None:
        raise HTTPException(status_code=503, detail="Model is not loaded. Check the server logs.")

    pipeline = model_artifact["pipeline"]
    probs = pipeline.predict_proba([request.text])[0]
    probabilities = {label: round(float(p), 4) for label, p in zip(pipeline.classes_, probs)}
    sentiment = max(probabilities, key=probabilities.get)

    log.info("predict sentiment=%s confidence=%.2f chars=%d", sentiment, probabilities[sentiment], len(request.text))
    return PredictResponse(
        text=request.text,
        sentiment=sentiment,
        confidence=probabilities[sentiment],
        probabilities=probabilities,
        model_version=model_artifact["version"],
    )
