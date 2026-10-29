import threading
from flask import Blueprint, jsonify, request, render_template, Response, redirect, current_app
from .store import store, suppressed
from . import orchestrator, tracking
from .agents import outreach_agent, enrichment_agent
from .config import Config

bp = Blueprint("main", __name__)

def _run(run_id):
    return store.get(run_id)

@bp.get("/")
def index(): return render_template("index.html")

@bp.get("/healthz")
def health(): return "ok"

@bp.post("/api/search")
def search():
    d = request.get_json(force=True)
    if len((d.get("jd") or "").strip()) < 40:
        return jsonify(error="Paste a fuller job description"), 400
    return jsonify(run_id=orchestrator.start_search(d["jd"], d.get("location", "")))

@bp.get("/api/runs/<rid>")
def get_run(rid):
    r = _run(rid)
    if not r: return jsonify(error="expired"), 404
    slim = lambda cs: [{k: c[k] for k in ("id", "name", "platform", "url", "headline", "location",
                                           "match", "open_to_work", "skills", "email")} for c in cs]
    return jsonify(status=r["status"], error=r["error"], profile=r["profile"], counts=r["counts"],
                   open=slim(r["open"]), other=slim(r["other"]))

def _all(r): return r["open"] + r["other"]

@bp.post("/api/runs/<rid>/send")
def send(rid):
    r = _run(rid)
    if not r or r["status"] != "done": return jsonify(error="run not ready/expired"), 400
    if not outreach_agent.configured(): return jsonify(error="Email not configured"), 400
    if r.get("send_status") == "sending": return jsonify(error="already sending"), 409
    d = request.get_json(force=True)
    min_match = float(d.get("min_match", 0)); only_open = bool(d.get("only_open"))
    rec = [c for c in _all(r) if c["email"] and c["match"] >= min_match
           and (c["open_to_work"] or not only_open) and not c.get("emailed")]
    threading.Thread(target=outreach_agent.send_bulk, daemon=True,
                     args=(r, rec, d["subject"], d["body"], Config.BASE_URL)).start()
    return jsonify(queued=len(rec), skipped_no_email=sum(1 for c in _all(r) if not c["email"]))

@bp.get("/api/runs/<rid>/stats")
def stats(rid):
    r = _run(rid)
    if not r: return jsonify(error="expired"), 404
    opens = {e["cid"] for e in r["events"] if e["kind"] == "open"}
    clicks = {e["cid"] for e in r["events"] if e["kind"] == "click"}
    names = {c["id"]: c["name"] for c in _all(r)}
    return jsonify(sent=r["sent"], status=r.get("send_status"), unique_opens=len(opens),
                   unique_clicks=len(clicks), total_opens=sum(e["kind"] == "open" for e in r["events"]),
                   engaged=[{"name": names.get(i, i), "clicked": i in clicks} for i in opens | clicks])

@bp.post("/api/runs/<rid>/candidates/<cid>/enrich")
def enrich(rid, cid):
    r = _run(rid)
    c = next((x for x in _all(r or {"open": [], "other": []}) if x["id"] == cid), None)
    if not c: return jsonify(error="not found"), 404
    if "enriched" not in c:
        c["enriched"] = enrichment_agent.enrich(c)
        if c["enriched"]["emails"] and not c["email"]:
            c["email"] = c["enriched"]["emails"][0]
    return jsonify(c["enriched"])

# ---- tracking & unsubscribe (stateless: signed tokens) ----
@bp.get("/t/o/<token>.gif")
def pixel(token):
    t = tracking.read(token)
    if t and (r := _run(t["r"])): tracking.log(r, "open", t["c"])
    return Response(tracking.GIF, mimetype="image/gif", headers={"Cache-Control": "no-store"})

@bp.get("/t/c/<token>")
def click(token):
    t = tracking.read(token)
    if not t or not t.get("u"): return "Invalid link", 400
    if r := _run(t["r"]): tracking.log(r, "click", t["c"])
    return redirect(t["u"])

@bp.route("/unsubscribe/<token>", methods=["GET", "POST"])
def unsubscribe(token):
    t = tracking.read(token)
    if t and t.get("e"): suppressed.add(t["e"].lower())
    return "You have been unsubscribed.", 200
