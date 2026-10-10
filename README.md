# AI Sentiment Demo — Containerization and Model Deployment

A deliberately small, real ML application used to teach **how a model becomes a deployed AI service**:

```
training data ──► train.py ──► model artifact ──► FastAPI service ──► Docker image ──► Render (free) ──► public HTTPS URL
```

A user types a sentence; a scikit-learn model running inside a container in the cloud returns
**positive / negative / neutral** with class probabilities.

---

## 1. Architecture

| Layer | What it is here | File |
|---|---|---|
| Data | ~420 labelled sentences (120 hand-written + 300 template-generated) | [training/data/sentiment_data.csv](training/data/sentiment_data.csv) |
| Training | TF-IDF (character n-grams) + Logistic Regression, saved with joblib | [training/train.py](training/train.py) |
| Model artifact | `model/sentiment_model.joblib` (~50 KB) — created at **image build time** | — |
| Inference service | FastAPI: `GET /`, `GET /health`, `POST /predict`, auto docs at `/docs` | [app/main.py](app/main.py) |
| UI | One static HTML page calling `/predict` | [app/static/index.html](app/static/index.html) |
| Packaging | Dockerfile → image containing Python, libraries, code and trained model | [Dockerfile](Dockerfile) |
| Hosting | Render free web service, builds from the Dockerfile on every Git push | [render.yaml](render.yaml) |

Runtime footprint measured locally: **~130 MB RAM** after 20 predictions (free tier limit: 512 MB).

---

## 2. Hosting decision (verified against official docs, Oct 2026)

**Chosen: Render free web service, Docker runtime.**

| Fact | Source |
|---|---|
| Web services can run on a Free instance: **0.1 CPU / 512 MB RAM** | https://render.com/docs/free |
| Docker builds from a repo Dockerfile are supported (set *Language = Docker*) | https://render.com/docs/docker |
| Free services **spin down after 15 min idle**; wake-up takes **~1 minute** | https://render.com/docs/free |
| **750 free instance hours / month** per workspace | https://render.com/docs/free |
| Ephemeral filesystem — nothing written at runtime survives a restart | https://render.com/docs/free |
| No SSH/shell, single instance only, may be restarted at any time | https://render.com/docs/free |
| Exceeding bandwidth / build minutes **without a payment method** suspends the service — it does **not** bill you | https://render.com/docs/free |
| ⚠️ If `plan` is omitted in `render.yaml`, Render uses the **paid** `0.5c-512mb` plan. This repo sets `plan: free` explicitly. | https://render.com/docs/blueprint-spec |

**Not chosen:** Hugging Face Docker / CPU-Basic Spaces — per current HF docs they need a paid plan for personal accounts.

**Zero-cost guardrails**
- Do **not** add a payment method on Render. Without one, overages suspend the service instead of billing.
- Always confirm the instance type shows **Free** before clicking Deploy.

---

## 3. Project structure

```
ai-sentiment-deploy/
├── app/
│   ├── main.py              # FastAPI inference service
│   └── static/index.html    # Browser UI
├── training/
│   ├── train.py             # Trains and saves the model
│   └── data/sentiment_data.csv
├── tests/test_app.py        # Health, prediction, validation, missing-model tests
├── docs/                    # Session plan, runbook, troubleshooting, Q&A
├── Dockerfile
├── .dockerignore
├── render.yaml              # Render Blueprint (free plan, Singapore)
├── requirements.txt         # Pinned runtime dependencies
└── requirements-dev.txt     # + pytest, httpx
```

---

## 4. Run locally (optional — attendees don't need this)

Requires Python 3.12+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
python training/train.py               # creates model/sentiment_model.joblib
pytest -q                              # 13 tests
uvicorn app.main:app --port 8000       # open http://localhost:8000
```

---

## 5. Run with Docker (optional)

Docker is **not required** for the session — Render builds the image for you. If you want to show
`docker build` / `docker run` live without installing anything, open the repo in **GitHub Codespaces**
(Docker is pre-installed; personal accounts get a monthly free quota — check *GitHub → Settings → Billing*).

```bash
docker build -t ai-sentiment-demo .
docker run --rm -p 8000:8000 ai-sentiment-demo            # host port 8000 → container port 8000
docker run --rm -p 9000:10000 -e PORT=10000 ai-sentiment-demo   # simulate Render's PORT
docker ps                                                  # see the running container
docker logs <container-id>                                 # see application logs
```

### The Dockerfile, line by line

| Instruction | Why |
|---|---|
| `FROM python:3.13-slim` | Start from an official, small image that already has Linux + Python. |
| `ENV PYTHONUNBUFFERED=1 ...` | Logs appear immediately in `docker logs` / Render logs. |
| `WORKDIR /app` | All later steps happen in `/app` inside the image. |
| `COPY requirements.txt` + `RUN pip install` | Install libraries **before** copying code so this slow layer is cached when only code changes. |
| `COPY training/ app/` | Put our code and data into the image. |
| `RUN python training/train.py` | Train at build time → the model is **baked into the image**; every container has the identical model. |
| `useradd` + `USER appuser` | Don't run as root — basic container hygiene. |
| `ENV PORT=8000` / `EXPOSE 8000` | Default port; Render overrides `PORT` at runtime (default 10000). |
| `CMD ... uvicorn --host 0.0.0.0 --port ${PORT}` | Start the server on **all interfaces** so traffic from outside the container can reach it. |

---

## 6. Deploy to Render (you do this — ~10 minutes)

> Never paste passwords or tokens into an AI chat. All authenticated steps below happen in your browser.

### 6.1 Push to GitHub

1. Create an **empty public** repo on GitHub, e.g. `ai-sentiment-deploy` (no README / .gitignore).
2. In this folder (a local Git repo with an initial commit is already prepared):
   ```powershell
   git remote add origin https://github.com/<your-username>/ai-sentiment-deploy.git
   git branch -M main
   git push -u origin main
   ```
   Git will open a browser window for GitHub sign-in the first time.

### 6.2 Create the Render service (dashboard path — recommended, it's also a teaching moment)

1. Go to https://dashboard.render.com/register → **Sign up with GitHub**.
2. If asked to add a card: **skip / don't add**. Free web services don't require one.
3. **New ▸ Web Service** → *Git Provider* → authorise Render for GitHub (you can limit it to this one repo) → select `ai-sentiment-deploy`.
4. Fill in:

   | Field | Value |
   |---|---|
   | Name | `ai-sentiment-demo` (becomes `ai-sentiment-demo.onrender.com` if available) |
   | Language | **Docker** |
   | Branch | `main` |
   | Region | **Singapore** |
   | Root Directory | *(leave empty)* |
   | Dockerfile Path | `./Dockerfile` *(default)* |
   | Instance Type | **Free** ← double-check this |
   | Environment Variables | *none needed* |
   | Advanced ▸ Health Check Path | `/health` |
   | Advanced ▸ Auto-Deploy | On Commit |

5. Click **Deploy Web Service**. Watch the logs: you'll see each Dockerfile step, then
   `Loaded model v1.0.0` and `Uvicorn running on http://0.0.0.0:10000`.
6. When the status is **Live**, open the URL shown at the top of the page.

**Alternative (Blueprint):** *New ▸ Blueprint* → select the repo → Render reads [render.yaml](render.yaml) → confirm
the plan shows **Free** → *Apply*.

### 6.3 Verify the public deployment

Open in a private/incognito window:

- `https://<your-service>.onrender.com/` → UI loads, footer shows `App v1.0.0 · Model v1.0.0 · Container <id>`
- `https://<your-service>.onrender.com/health` → `{"status":"ok", ...}`
- `https://<your-service>.onrender.com/docs` → interactive API docs

```bash
curl https://<your-service>.onrender.com/health

curl -X POST https://<your-service>.onrender.com/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "The new AI assistant has made our team'"'"'s work much faster."}'
```

PowerShell equivalent:

```powershell
Invoke-RestMethod -Method Post -Uri https://<your-service>.onrender.com/predict `
  -ContentType "application/json" -Body '{"text":"The service was horrible and slow"}'
```

Example response (actual local result):

```json
{"text":"The new AI assistant has made our team's work much faster.","sentiment":"positive",
 "confidence":0.8726,"probabilities":{"negative":0.0822,"neutral":0.0451,"positive":0.8726},"model_version":"1.0.0"}
```

Invalid input (empty, whitespace, >1000 chars, wrong type) returns **HTTP 422** with a message.

### 6.4 Redeploy demo (browser only)

1. On GitHub, open `app/main.py` → pencil icon → change `APP_VERSION = "1.0.0"` to `"1.1.0"` → **Commit changes**.
2. Render detects the commit and rebuilds (dependency layer is cached, so it's faster).
3. Refresh the app: footer shows **App v1.1.0** and usually a **new container id** — a new container replaced the old one.

---

## 7. Verification checklist

| # | Check | Command / action | Expected |
|---|---|---|---|
| 1 | Train | `python training/train.py` | `Saved model v1.0.0` |
| 2 | Tests | `pytest -q` | `13 passed` |
| 3 | Local server | `uvicorn app.main:app` → `/health` | `status: ok` |
| 4 | Predict | `POST /predict` | JSON with `sentiment`, `confidence` |
| 5 | Validation | `POST /predict {"text":"  "}` | HTTP 422 |
| 6 | Docker build | `docker build -t ai-sentiment-demo .` | completes, training log visible |
| 7 | Docker run | `docker run -p 8000:8000 ai-sentiment-demo` | `/health` ok on localhost:8000 |
| 8 | Logs | `docker logs <id>` / Render *Logs* tab | `predict sentiment=...` lines |
| 9 | Public URL | incognito browser | UI + prediction works |
| 10 | Redeploy | change `APP_VERSION`, commit | footer shows new version |

---

## 8. Model limitations (say this out loud)

- Trained on ~420 short business sentences, 300 of them generated from templates. Cross-validation accuracy
  (~0.91) is optimistic because templated sentences share phrasing.
- It does not understand sarcasm, negation ("not bad"), domain jargon or long documents.
- "Confidence" is the model's probability estimate, not a guarantee.
- It exists to demonstrate **deployment**, not to be a production sentiment engine. A production system would
  use a stronger model (e.g. a fine-tuned transformer or an LLM API), proper evaluation data, and monitoring.

---

## 9. Session materials

- [docs/session-plan.md](docs/session-plan.md) — 90-minute agenda and speaker notes
- [docs/live-demo-runbook.md](docs/live-demo-runbook.md) — pre-session checklist, step-by-step demo, fallback ladder
- [docs/troubleshooting.md](docs/troubleshooting.md) — one-page fixes
- [docs/discussion-questions.md](docs/discussion-questions.md) — audience questions with answers

---

## 10. Security notes

- No secrets anywhere in code, image, or `render.yaml`. If you later add an LLM API key, set it in the Render
  dashboard as an environment variable — never in the Dockerfile or Git.
- Container runs as a non-root user; input length is capped at 1000 characters.
- The model file is produced by our own build; never `joblib.load` files from untrusted sources (pickle can execute code).
