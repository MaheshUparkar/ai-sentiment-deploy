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
| Data | ~34,400 labelled texts from two public datasets + 150 hand-written business sentences (see §8) | [training/data/](training/data/) |
| Training | Word + character TF-IDF + VADER lexicon scores → Logistic Regression, saved with joblib | [training/train.py](training/train.py), [app/features.py](app/features.py) |
| Model artifact | `model/sentiment_model.joblib` (~4 MB) — created at **image build time** | — |
| Inference service | FastAPI: `GET /`, `GET /health`, `POST /predict`, auto docs at `/docs` | [app/main.py](app/main.py) |
| UI | One static HTML page calling `/predict` | [app/static/index.html](app/static/index.html) |
| Packaging | Dockerfile → image containing Python, libraries, code and trained model | [Dockerfile](Dockerfile) |
| Hosting | Render free web service, builds from the Dockerfile on every Git push | [render.yaml](render.yaml) |

Measured locally: **~185 MB RAM** at runtime (free tier limit: 512 MB), **~47 ms** per prediction, training
**~25 s / ~520 MB peak** — training runs on Render's build machines (2 CPU / 8 GB), not on the 512 MB instance.

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
| Builds run on separate **2 CPU / 8 GB** machines; Hobby workspaces get **500 build minutes / month** | https://render.com/docs/build-pipeline |
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
│   ├── features.py          # VADER features (shared by training and serving)
│   └── static/index.html    # Browser UI
├── training/
│   ├── prepare_data.py      # Downloads + normalises public datasets (already run; output committed)
│   ├── train.py             # Trains, evaluates on held-out data, saves the model
│   └── data/
│       ├── public/          # tweets_{train,val,test}.csv, uci_sentences.csv
│       ├── business_train.csv   # 150 hand-written business sentences
│       └── business_eval.csv    # 60 held-out business sentences (never trained on)
├── tests/test_app.py        # Health, prediction, validation, missing-model, quality tests
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
python training/train.py               # ~25 s; creates model/sentiment_model.joblib and prints test metrics
pytest -q                              # 14 tests
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
| `COPY app/features.py` + `COPY training/` | Copy only what training needs. |
| `RUN python training/train.py` | Train at build time → the model is **baked into the image**; every container has the identical model. Cached unless data/training code changes. |
| `COPY app/` | Copy the rest of the app **after** training, so a UI/API change doesn't retrain (fast redeploys). |
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
   `Saved model v2.0.0`, `Loaded model v2.0.0` and `Uvicorn running on http://0.0.0.0:10000`.
6. When the status is **Live**, open the URL shown at the top of the page.

**Alternative (Blueprint):** *New ▸ Blueprint* → select the repo → Render reads [render.yaml](render.yaml) → confirm
the plan shows **Free** → *Apply*.

### 6.3 Verify the public deployment

Open in a private/incognito window:

- `https://<your-service>.onrender.com/` → UI loads, footer shows `App v1.0.0 · Model v2.0.0 (71% test accuracy) · Container <id>`
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
 "confidence":0.6442,"probabilities":{"negative":0.1962,"neutral":0.1596,"positive":0.6442},"model_version":"2.0.0"}
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
| 1 | Train | `python training/train.py` | `Saved model v2.0.0`, tweet-test accuracy ≈ 0.71 |
| 2 | Tests | `pytest -q` | `14 passed` |
| 3 | Local server | `uvicorn app.main:app` → `/health` | `status: ok` |
| 4 | Predict | `POST /predict` | JSON with `sentiment`, `confidence` |
| 5 | Validation | `POST /predict {"text":"  "}` | HTTP 422 |
| 6 | Docker build | `docker build -t ai-sentiment-demo .` | completes, training log visible |
| 7 | Docker run | `docker run -p 8000:8000 ai-sentiment-demo` | `/health` ok on localhost:8000 |
| 8 | Logs | `docker logs <id>` / Render *Logs* tab | `predict sentiment=...` lines |
| 9 | Public URL | incognito browser | UI + prediction works |
| 10 | Redeploy | change `APP_VERSION`, commit | footer shows new version |

---

## 8. Model, data and limitations (say this out loud)

### Results on held-out data (never used for training)

| Model | Tweet test set (5,205, 3-class) | Business eval set (60) |
|---|---|---|
| v1 — char TF-IDF on 420 mostly templated sentences | 0.444 | 0.817 |
| VADER lexicon alone (no training) | 0.606 | 0.833 |
| **v2 — word + char TF-IDF + VADER, public data** | **0.706** (macro-F1 0.708) | **0.900** |

Settings were chosen on the separate validation split (`tweets_val.csv`); the test sets were scored once.
The business eval set is small (60 sentences), so treat it as a sanity check, not a benchmark.

### Data sources

| Data | Rows | Labels | Licence |
|---|---|---|---|
| [Sp1786/multiclass-sentiment-analysis-dataset](https://huggingface.co/datasets/Sp1786/multiclass-sentiment-analysis-dataset) (tweets; pinned revision in `prepare_data.py`) | 31,232 train / 5,205 val / 5,205 test | pos / neg / neutral | Apache-2.0 as listed on Hugging Face. The texts appear to originate from Kaggle's *Tweet Sentiment Extraction* competition — check its terms before any commercial reuse. |
| [UCI Sentiment Labelled Sentences](https://archive.ics.uci.edu/dataset/331/sentiment+labelled+sentences) — Kotzias et al., *From Group to Individual Labels using Deep Features*, KDD 2015 | 3,000 | pos / neg | CC BY 4.0 |
| `business_train.csv` — hand-written for this demo (incl. 30 negation examples) | 150 | pos / neg / neutral | this repo |
| [VADER](https://github.com/cjhutto/vaderSentiment) lexicon — Hutto & Gilbert, ICWSM 2014 | ~7,500 words | sentiment scores | MIT |

The tweet data is informal social-media text and may contain profanity.

### Limitations

- About **7 in 10** predictions on unseen general text are right; neutral is the hardest class (F1 ≈ 0.64).
- Sarcasm fools it ("Great, another outage." → positive). Bare negations are still shaky: "Not bad at all" →
  negative with low confidence (~0.56), while "Not bad at all, the vendor delivered on time." → positive.
- "Confidence" is the model's probability estimate, not a guarantee.
- It exists to demonstrate **deployment**, not to be a production sentiment engine. A production system would
  use a stronger model (e.g. a fine-tuned transformer or an LLM API), domain-specific evaluation data, and monitoring.

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
