# Troubleshooting (one page)

| Symptom | Likely cause | Fix |
|---|---|---|
| Page shows Render's loading screen for ~1 min | Free service was asleep (15 min idle) | Wait. Warm it up 30 min before the session and keep it busy. |
| Render log: `No open ports detected` / deploy times out | App not listening on `0.0.0.0:$PORT` | Don't change the Dockerfile `CMD`. Don't set a *Docker Command* override in Render. |
| Deploy fails at health check | `/health` returns 503 → model didn't load | Check logs for `Model file not found`. Ensure `training/` is in the repo and the build ran `Saved model v2.0.0`. |
| `/health` → `{"status":"model_not_loaded"}` locally | You didn't train | `python training/train.py` |
| Build error in `pip install` | Network blip or unpinned edit to `requirements.txt` | *Manual Deploy ▸ Clear build cache & deploy*. Keep versions pinned as committed. |
| `Out of memory (used over 512Mi)` | You added a heavy library/model | Revert. This app uses ~185 MB. Transformer models won't fit the free tier comfortably. |
| Render asks for payment details | Selected a paid instance type, or a paid feature | Go back and choose **Free**. Never add a card for this demo. |
| Service suspended | Free hours/bandwidth exhausted (unlikely) | Wait until next month, or show screenshots. Do not upgrade. |
| Render doesn't see the repo | GitHub app not authorised for that repo | GitHub ▸ Settings ▸ Applications ▸ Render ▸ *Configure* ▸ add the repo. |
| Commit doesn't trigger a deploy | Auto-Deploy off or wrong branch | Render ▸ Settings ▸ Auto-Deploy = *On Commit*, Branch = `main`. Or *Manual Deploy ▸ Deploy latest commit*. |
| `git push` asks for a password | HTTPS auth | Use the browser sign-in Git opens, or GitHub Desktop. Never paste tokens into chats. |
| UI shows `Error: Failed to fetch` | Service restarting / network | Refresh after a few seconds. |
| UI prediction obviously wrong | Model limitation | Expected — use it as a teaching moment (README §8). |
| `docker: command not found` | Docker not installed | Not needed — Render builds the image. Use GitHub Codespaces if you want to show Docker commands. |
| Local `docker run` works but browser can't connect | Missing port mapping | `docker run -p 8000:8000 ai-sentiment-demo` |
| `/robots.txt` returns "Disallow" while asleep | Render behaviour for sleeping free services | Harmless. |

**Where to look first:** Render ▸ your service ▸ **Logs** (runtime) and **Events** (each deploy and its build log).
