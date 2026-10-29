"""Agent 2: fans out to all sources in parallel, merges and dedupes."""
import re
from concurrent.futures import ThreadPoolExecutor
from ..sources.github import GitHubSource
from ..sources.stackoverflow import StackOverflowSource
from ..sources.devto import DevToSource
from ..sources.websearch import WebSearchSource

SOURCES = [GitHubSource(), StackOverflowSource(), DevToSource(), WebSearchSource()]

def _safe(args):
    src, profile, location, limit = args
    try:
        return src.name, src.search(profile, location, limit)
    except Exception as e:
        return src.name, []

def collect(profile, location, target):
    per = max(50, target // 2)
    with ThreadPoolExecutor(len(SOURCES)) as ex:
        results = list(ex.map(_safe, [(s, profile, location, per) for s in SOURCES]))
    seen, merged, counts = set(), [], {}
    for name, cands in results:
        counts[name] = len(cands)
        for c in cands:
            key = c["url"].lower().rstrip("/")
            nkey = re.sub(r"\W", "", c["name"].lower())
            if key in seen or (len(nkey) > 5 and ("n:" + nkey) in seen):
                continue
            seen.add(key); seen.add("n:" + nkey)
            merged.append(c)
    return merged[:target + 100], counts
