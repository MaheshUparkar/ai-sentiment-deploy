# Live-Demo Runbook

Two Render services keep the session safe:

| Service | Purpose | When created |
|---|---|---|
| **`ai-sentiment-demo`** (main) | Stable URL for the audience (QR code). Also the fallback. | Days before the session |
| `ai-sentiment-live` (optional) | Created from scratch *during* the session to show the full deployment flow | Live, deleted afterwards |

Both are Free instances from the same repo. Two free services for a few hours stays far inside the 750 free hours/month.

---

## A. Before the session

### 2–3 days before
- [ ] Repo pushed to GitHub, main service deployed and **Live** (README §6).
- [ ] Open the main URL in incognito: UI, `/health`, `/docs`, one prediction all work.
- [ ] **Rehearse** creating a second service from scratch; note the build time: ______ min. If > 6 min, use Option 2 in section B.
- [ ] Delete the rehearsal service (*Settings ▸ Delete Web Service*).
- [ ] Make a QR code for the main URL (any free QR generator) and put it on a slide.
- [ ] **Fallback evidence:** screenshots of (1) the UI with a positive prediction, (2) `/docs`, (3) Render build logs showing the Dockerfile steps, (4) Render *Logs* with `predict sentiment=` lines, (5) the Render settings page showing *Docker* + *Free*. Put them on hidden backup slides.
- [ ] Confirm `APP_VERSION` in `app/main.py` on GitHub is `"1.0.0"` (so the live change to `1.1.0` is visible).

### 30 minutes before
- [ ] Open the main URL → wait for it to wake up (up to ~1 min) → run one prediction. Free services sleep after **15 minutes without traffic**, so:
- [ ] Keep the main URL tab open and click *Analyse* every ~10 minutes until you start, **or** ask a colleague to.
- [ ] Browser tabs, in this order:
  1. Slides
  2. Main app `https://ai-sentiment-demo.onrender.com/` (your actual URL)
  3. Main app `/docs`
  4. GitHub repo (signed in)
  5. Render dashboard (signed in) → main service → *Logs*
  6. Backup screenshots
- [ ] Zoom browser to 125–150% so the back row can read.
- [ ] Close notifications / chat apps.

### 5 minutes before
- [ ] One more prediction on the main URL. Confirm status **Live** in Render.

---

## B. During the session (chronological)

### Step 1 — Show the API (Section 2, ~min 15)
| Do | Audience sees | Say |
|---|---|---|
| Tab 3 `/docs` → `POST /predict` → *Try it out* → *Execute* | Request + JSON response with `sentiment`, `confidence` | "This is the order window. Any system that can send this JSON can use our model." |
| Open `/health` | `{"status":"ok", "served_by":"..."}` | "The 'we're open' sign. Platforms check this automatically." |

**If it fails:** service is probably waking — say "free tier, it's waking up — exactly the cold-start trade-off we'll discuss" and show screenshot 2.

### Step 2 — Walk the code (Section 4, ~min 35)
| Do | Say |
|---|---|
| Tab 4 GitHub → `training/train.py` | "Learn from examples, save one file." |
| `app/main.py` | "Load once, then validate → predict → reply." |
| `Dockerfile` | Read the 9 numbered comments. Linger on step 6 (train at build) and step 9 (`0.0.0.0` + `PORT`). |

### Step 3 — Live deployment (Section 5, ~min 45)

**Option 1 (recommended if rehearsal build ≤ 6 min): create a new service from scratch**

| Do | Audience sees | Say |
|---|---|---|
| Render ▸ **New ▸ Web Service** ▸ pick the repo | The repo list | "Render reads code straight from GitHub." |
| Name `ai-sentiment-live`, Language **Docker**, Region **Singapore**, Instance **Free**, Advanced ▸ Health Check `/health` | The config form | "Language = Docker means: *don't guess, use our Dockerfile.* Free = 0.1 CPU, 512 MB." |
| **Deploy Web Service** | Build logs streaming | Narrate: base image → `pip install` → training prints test accuracy → `Saved model v2.0.0` → image pushed → `Loaded model` → `Uvicorn running on http://0.0.0.0:10000` |
| Wait for **Live** → open the new URL | Same app on a new URL | "Same image, new container, new address. That's portability." |

While waiting, talk through Section 7's *statelessness* and *cost* points to use the time.

**Option 2 (if builds are slow): redeploy the main service via a commit**

| Do | Audience sees | Say |
|---|---|---|
| Render ▸ main service ▸ *Settings* — scroll through Language, Dockerfile path, Instance type, Health check | The configuration | "This is everything the platform needs to know." |
| GitHub ▸ `app/main.py` ▸ ✏️ ▸ change `APP_VERSION = "1.0.0"` → `"1.1.0"` ▸ *Commit changes* | A one-line diff | "A tiny change — watch what the platform does with it." |
| Render ▸ *Events / Logs* | New build starts automatically; cached layers are faster | "Dependencies are cached — only the changed layers rebuild." |
| Refresh app when **Live** | Footer: `App v1.1.0`, new container id | "New container replaced the old one, no downtime." |

**If the build fails or hangs > 8 min:** "Live demos and free tiers — this is why production teams keep the last good version running." Switch to the main URL (already live) and show screenshots 3 and 5. Continue.

### Step 4 — Audience uses the app (Section 6, ~min 60)
| Do | Audience sees | Say |
|---|---|---|
| Show QR slide (main URL) | Phones out | "Type something about your work." |
| Try `Not bad at all` | Model says **negative** (~56%, low confidence) — tested | "Even trained on 34,000 sentences, a simple model trips on negation. Deployment worked perfectly; the *model* is the weak link — that's why monitoring model quality matters." |
| Clear the text box → *Analyse* | "Please enter a sentence first." | "Input validation is part of production readiness." |
| Render ▸ main service ▸ *Logs* | Their requests: `predict sentiment=positive confidence=0.87 chars=58` | "Basic observability — we log outcomes, not personal content." |
| If Option 1 was used: do the Option 2 commit now on the main service | Footer changes to v1.1.0 | "Shipping a change is routine." |

**If 40 people hit it at once and it's slow:** "0.1 CPU for a whole room — this is a capacity-planning conversation." Good segue into scaling.

---

## C. After the session
- [ ] Delete `ai-sentiment-live` (Render ▸ service ▸ *Settings* ▸ *Delete Web Service*).
- [ ] Optionally revert `APP_VERSION` to `"1.0.0"` for the next run.
- [ ] Leave the main service; it sleeps when idle and only consumes free hours while awake.

---

## D. Fallback ladder (in order)

1. Free service asleep → wait ~1 minute; talk about cold starts meanwhile.
2. Live build failing → use the pre-deployed main service.
3. Render down entirely → if you have Python on the laptop: `uvicorn app.main:app` from the repo folder and use `http://localhost:8000` (audience can't reach it, but you can demo).
4. No network → backup screenshots + narrate.

No step in this ladder creates paid resources.
