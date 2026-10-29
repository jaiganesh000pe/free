"""Agent 3: semantic similarity (ONNX embeddings, no torch -> fits Render free RAM)
blended with explicit skill overlap."""
import numpy as np
from .jd_agent import extract_skills

_model = None
def _get_model():
    global _model
    if _model is None:  # lazy: keeps cold start fast, loads on first search
        from fastembed import TextEmbedding
        _model = TextEmbedding("BAAI/bge-small-en-v1.5")
    return _model

def _text(c):
    return f'{c["name"]}. {c["headline"]}. {c["bio"]}. {" ".join(c["skills"])}. {c["platform"]}'

def score(profile, jd, cands):
    if not cands:
        return
    docs = [_text(c) for c in cands]
    vecs = np.array(list(_get_model().embed([jd[:3000]] + docs)), dtype="float32")
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9
    sims = vecs[1:] @ vecs[0]
    sem = np.clip((sims - 0.40) / 0.45, 0, 1)  # bge-small cosine ~0.4 (unrelated) .. 0.85 (strong)
    need = set(profile["skills"])
    for c, s, d in zip(cands, sem, docs):
        c["skills"] = sorted(set(c["skills"]) | set(extract_skills(d)))
        overlap = len(need & set(c["skills"])) / len(need) if need else 0
        c["match"] = round(100 * (0.7 * float(s) + 0.3 * overlap), 1)

def split_and_sort(cands):
    key = lambda c: -c["match"]
    return (sorted([c for c in cands if c["open_to_work"]], key=key),
            sorted([c for c in cands if not c["open_to_work"]], key=key))
