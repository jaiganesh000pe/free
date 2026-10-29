# AI Sourcer (stateless, multi-agent Flask)

```
Browser ──► Flask routes ──► Orchestrator (thread, progress in TTL store)
                               ├─ JD Agent        skills/title (+optional LLM)
                               ├─ Scraping Agent  GitHub API · StackOverflow API · Dev.to API ·
                               │                  Brave site: queries → LinkedIn(snippets), GitLab, Kaggle,
                               │                  HuggingFace, Medium, Hashnode, Behance, Dribbble, CodePen,
                               │                  LeetCode, HackerRank, Wellfound, ResearchGate, ORCID, ...
                               ├─ Matching Agent  fastembed (bge-small, ONNX) + skill overlap → match %
                               ├─ Outreach Agent  smtplib, throttled, List-Unsubscribe, signed pixel
                               └─ Enrichment Agent  on click: public pages the candidate published
```
## Run
    pip install -r requirements.txt
    cp .env.example .env   # fill keys
    gunicorn -w 1 --threads 8 -t 120 wsgi:app

Render: push repo, "New + Blueprint" (render.yaml). Keep **1 worker** (state is in-process).
Set BASE_URL to your Render URL so tracking links resolve.

## Known limits of "no database"
- Results, open/click events and the suppression list vanish on restart / free-tier spin-down.
  Export results before leaving; for durable suppression put unsubscribes in an env var or a free KV store.
- Open tracking is approximate (Apple Mail Privacy Protection and image blocking skew it).
- Gmail SMTP caps ~500/day; use a dedicated domain with SPF/DKIM/DMARC for real volume.
