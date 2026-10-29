"""Stateless-friendly tracking: tokens are signed (not stored), so a pixel hit
is verifiable even after a restart. Events themselves are kept in memory."""
import time
from itsdangerous import URLSafeSerializer, BadSignature
from flask import current_app

def _s():
    return URLSafeSerializer(current_app.config["SECRET_KEY"], salt="track")

def make(run_id, cid, url=None, email=None):
    return _s().dumps({"r": run_id, "c": cid, "u": url, "e": email})

def read(token):
    try:
        return _s().loads(token)
    except BadSignature:
        return None

GIF = bytes.fromhex("47494638396101000100800000000000ffffff21f90401000000002c00000000010001000002024401003b")

def log(run, kind, cid):
    run["events"].append({"t": time.time(), "kind": kind, "cid": cid})
