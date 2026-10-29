"""Orchestrator: runs the agent pipeline in a background thread, publishing
progress to the in-memory store so the UI can poll (avoids HTTP timeouts)."""
import threading, uuid, traceback
from .store import store
from .config import Config
from .agents import jd_agent, scraping_agent, matching_agent

def start_search(jd, location):
    run_id = uuid.uuid4().hex[:12]
    run = {"id": run_id, "status": "queued", "jd": jd, "profile": None, "counts": {},
           "open": [], "other": [], "events": [], "sent": 0, "send_status": None, "error": None}
    store.set(run_id, run)
    threading.Thread(target=_pipeline, args=(run, location), daemon=True).start()
    return run_id

def _pipeline(run, location):
    try:
        run["status"] = "analyzing JD"
        run["profile"] = jd_agent.analyze(run["jd"])
        run["status"] = "sourcing candidates"
        cands, run["counts"] = scraping_agent.collect(run["profile"], location, Config.TARGET_CANDIDATES)
        run["status"] = "matching"
        matching_agent.score(run["profile"], run["jd"], cands)
        run["open"], run["other"] = matching_agent.split_and_sort(cands)
        run["status"] = "done"
    except Exception:
        run["status"], run["error"] = "error", traceback.format_exc()[-500:]
