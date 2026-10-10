# Session Plan & Speaker Notes — Containerization and Model Deployment

**Batch:** Advance Gen AI · **Duration:** 90 min · **Audience:** senior, business-oriented, light technical exposure
**Format:** theory with analogies + live demo · **Participants:** mostly watch, then use the public URL on their phones

**One-sentence promise to open with:**
> "In 90 minutes you'll watch a model go from a file on a laptop to a live AI service anyone in this room can use from their phone — and you'll understand every step well enough to ask your tech teams the right questions."

---

## Agenda

| Time | Section | Mode | Takeaway |
|---|---|---|---|
| 0–10 | 1. Why deployment matters | Theory | A model is not a product |
| 10–22 | 2. Model vs inference service vs application; APIs | Theory + show `/docs` | How software asks a model for a prediction |
| 22–35 | 3. Containers, images, Docker | Theory | Packaging removes "works on my machine" |
| 35–45 | 4. Walk through the code & Dockerfile | Demo | What's actually inside the box |
| 45–60 | 5. Live deployment on Render | Demo | Code → image → running container → URL |
| 60–70 | 6. Audience tests the public app + redeploy | Interactive | It's real, and change is routine |
| 70–82 | 7. Production thinking & GenAI | Discussion | Scaling, cost, latency, monitoring, LLM hosting |
| 82–90 | 8. Recap & Q&A | Discussion | Connect to their own projects |

**Before you start:** the deployed app must already be *Live* and warmed up (see [live-demo-runbook.md](live-demo-runbook.md)).

---

## 1. Why deployment matters (0–10)

**Talking points**
- Most AI value is lost between "the notebook works" and "customers use it". Industry surveys repeatedly report that a large share of ML models never reach production — treat the exact figure loosely, the pattern is well known.
- A trained model is like a **recipe developed in a test kitchen**. Deployment is opening the restaurant: a kitchen that runs every day, serves many customers, at a known cost, with hygiene standards.
- Deployment problems are rarely about the model's intelligence. They're about **environment, packaging, access, reliability and cost**.
- Today's single question: *"How does a model on someone's laptop become something the whole organisation can use?"*

**Ask the room:** "Who has seen an impressive AI demo that never became a real product? What got in the way?"
(Let 2–3 people answer; you'll hear: integration, IT approval, scaling, cost, security. Write them down — you'll map them back at the end.)

---

## 2. Model → inference service → application (10–22)

**Four words to define clearly**

| Term | Plain meaning | Restaurant analogy |
|---|---|---|
| **Model** | A file that turns input into a prediction | The recipe |
| **Inference** | Running the model on new input | Cooking one dish |
| **Inference service / API** | A program that receives requests, runs the model, returns answers | The kitchen with an order window |
| **Application** | What humans use (web page, app, chatbot) | The dining room and menu |

**Talking points**
- An **API** is an order window: a fixed format for what you can ask and what you get back. Our API has one "dish": `POST /predict` with `{"text": "..."}` → `{"sentiment": "positive", "confidence": 0.87}`.
- **HTTP** is the language of the web; every browser click is an HTTP request. A **port** is a numbered door on a machine — the service listens behind door 8000 (or 10000 on Render).
- Why an API instead of emailing the model file around: one central model, many consumers (website, CRM, mobile app, another AI agent), consistent behaviour, controlled updates.
- **Health endpoint** (`/health`) = the "we're open" sign. Platforms check it automatically before sending traffic.

**Show (2 min):** open `<url>/docs`, expand `POST /predict`, *Try it out*, run the default sentence. "This page is generated automatically from our code — this is what developers integrating with us would see."

**Ask the room:** "In your organisation, which systems would want to call a model like this?"

---

## 3. Containers, images and Docker (22–35)

**The problem:** "It works on my machine." The app depends on a specific Python version, ~7 libraries at exact versions, a model file, and a start command. Every machine differs.

**The shipping-container analogy (core of this section)**
- Before standard shipping containers, every port loaded cargo differently — slow, fragile, expensive. After standardisation, *any* ship, crane or truck can move *any* container without knowing what's inside.
- A software container does the same: package the app with everything it needs, so *any* machine that runs containers can run it the same way.

**Image vs container**

| | Image | Container |
|---|---|---|
| What | The packaged template (read-only) | A running instance of an image |
| Analogy | The franchise blueprint / a frozen ready meal | An open restaurant branch / the meal being served |
| Count | Built once per version | Start one or many from the same image |
| Created by | `docker build` (from a Dockerfile) | `docker run` |

- **Dockerfile** = the written recipe for building the image. Version-controlled, reviewable, repeatable.
- **Registry** = the warehouse for images (Docker Hub, cloud registries; Render uses its own private one).

**Containers vs virtual machines**
- A VM emulates a whole computer including its own operating system — heavy, slow to start (minutes), GBs.
- A container shares the host's OS kernel and isolates only the app — light, starts in seconds, MBs.
- Analogy: VM = a separate house with its own plumbing; container = an apartment in a building sharing plumbing but with its own locked door.

**Be honest about limits** (seniors appreciate this)
- Containers do **not** automatically make an app secure, scalable or reliable. They make it *portable and repeatable*. Security, scaling and monitoring are separate work.
- "Works in a container" still depends on the CPU architecture, available memory and external services.

**Containerization ≠ deployment**
- Containerization = *packaging*. Deployment = *putting the package somewhere it runs, reachable, monitored*. You can containerize without deploying and deploy without containers (Render's native Python runtime, for example). We use both because together they're the industry default.

**Ask the room:** "What's the business cost when an app behaves differently in testing and in production?"

---

## 4. Walk through the code (35–45)

Keep it to three files. Don't read code line by line — point at *responsibilities*.

1. **[training/train.py](../training/train.py)** — "Learn from ~34,000 labelled public sentences, test on data it has never seen, save the result to one file." Training happens **once**, separately from serving. Point out the printed test accuracy (~71%) — *measuring* the model is part of shipping it.
2. **[app/main.py](../app/main.py)** — "Load the model once at start-up; for each request: validate input → predict → return JSON." Point out:
   - `/health` reports whether the model loaded and which container answered (`served_by`).
   - Input validation: empty or overly long text is rejected (show this later in the UI).
3. **[Dockerfile](../Dockerfile)** — read it top to bottom using the numbered comments. Key line: `RUN python training/train.py` — "the model is baked into the image, so every copy of the container has the identical model."

**Say:** "Notice what's *not* here: no API keys, no GPU, no database, no paid service. That's on purpose — we're isolating the deployment lesson."

**Model honesty line:** "This is a small classical ML model, not an LLM. It will make mistakes — that's fine. The packaging and deployment pattern is identical for a much bigger model; what changes is size, compute and cost."

---

## 5. Live deployment (45–60)

Follow Step 3 in [live-demo-runbook.md](live-demo-runbook.md): **Option 1** creates a brand-new service live; **Option 2** (if builds are slow) shows the settings and redeploys the main service via a one-line commit.

**What to say while the build runs (it takes a few minutes)**
- "Render is doing what a developer would do with `docker build`: download the base image, install libraries, copy our code, train the model, create the image."
- Point at log lines as they appear: `FROM python:3.13-slim` → `pip install` → `Saved model v2.0.0` → `Loaded model` → `Uvicorn running on http://0.0.0.0:10000`.
- "Render then starts a container from the image, checks `/health`, and only switches traffic when the health check passes — that's a **zero-downtime deploy**."
- "We're on the free tier: 0.1 CPU and 512 MB RAM. Our app uses about 185 MB. That's the kind of sizing conversation you'll have with your teams."

---

## 6. Audience tests the app + redeploy (60–70)

- Share the URL (QR code on a slide works best). Ask everyone to try a sentence about their work.
- Suggested prompts to call out:
  - "The new AI assistant has made our team's work much faster." → positive
  - "The service was horrible and slow" → negative
  - "The meeting is on Friday at 3 pm" → neutral
  - "Not bad at all" → negative with low confidence (~56%) → **teaching moment** on model limitations and evaluation.
  - "Great, another outage. Just what we needed." → positive → sarcasm defeats word-based models.
- **Model iteration story:** "Our first model was right only 44% of the time on real text. We swapped in public data and a sentiment lexicon — now ~71% — and shipped it with the *same* Dockerfile and the *same* deployment. The pipeline didn't change; only the model inside the box did."
- Show an invalid request: clear the box and click *Analyse* → friendly error. "Validation is part of production readiness."
- Show **Render ▸ Logs**: their requests appear as `predict sentiment=... confidence=...`. "This is basic observability."
- **Redeploy** (if you used Option 1 in Section 5): edit `APP_VERSION` on GitHub → commit → Render rebuilds → footer changes to v1.1.0 and usually a new container id. "Shipping a change is now a routine, low-risk event — that's the real payoff."

---

## 7. Production thinking & GenAI (70–82)

Pick the topics the room reacts to; you won't cover all.

**Statelessness & storage** — Our container keeps nothing between restarts (the filesystem is ephemeral). Anything that must survive — user data, logs, feedback — goes to a database or object storage. Stateless containers are what make scaling easy.

**Scaling** — More traffic → run more identical containers from the same image behind a load balancer. That's why one image → many containers matters. Orchestrators (Kubernetes, managed platforms) automate this. Free tier = one instance, no scaling.

**Latency & cold starts** — Free services sleep after 15 min and take ~1 minute to wake up. Paid tiers stay warm. Business trade-off: cost vs responsiveness.

**Cost** — You pay for reserved CPU/RAM/GPU time, not for "the model". A tiny model fits a free tier; a 70B-parameter LLM needs GPUs costing real money per hour.

**Monitoring** — Uptime (health checks), latency, error rates, *and* model quality (is accuracy drifting as language/customers change?). Software can be "up" while the model is quietly wrong.

**Security & configuration** — Secrets (API keys) go in environment variables set in the platform, never in code or images. Run as non-root, keep base images updated, validate inputs, limit request sizes.

**GenAI: two very different deployments**

| | Deploy an **LLM-powered application** | **Self-host the LLM** itself |
|---|---|---|
| What's in the container | Your app + prompt logic; calls OpenAI/Anthropic/Gemini/Azure API | Model weights (GBs) + an inference server (vLLM, TGI, Ollama) |
| Hardware | Small CPU container | GPUs with lots of memory |
| Cost model | Pay per token to the provider | Pay per GPU-hour, whether used or not |
| Main concerns | API keys, data privacy, vendor dependency, rate limits | GPU availability, throughput, batching, quantization, ops skills |
| Our demo is closest to | ✔ (swap `predict` for an API call) | Same pattern, much heavier box |

**Key message:** "Containers are the common unit in both worlds. What changes is what's inside the box and what hardware it needs."

---

## 8. Recap (82–90)

Five sentences to close with:
1. A model becomes useful only when it's **served** — behind an API, reachable by applications.
2. A **container** packages the service with everything it needs; the **image** is the template, the **container** is the running copy.
3. **Deployment** puts the container somewhere it runs, is reachable, is health-checked and can be updated safely.
4. Containers give **portability and repeatability** — not automatic security, scale or quality.
5. For GenAI, decide early: **call an LLM API** or **host the model** — the engineering and cost profiles are completely different.

Map back to the obstacles the room listed in section 1 — tick off which ones today's pattern addresses.
