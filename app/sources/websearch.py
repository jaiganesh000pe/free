"""Covers 12+ platforms via a search-engine API (Brave) using site: queries.
Only result titles/snippets are used; we do NOT fetch LinkedIn (or similar) pages,
which their ToS prohibit."""
import re, requests
from concurrent.futures import ThreadPoolExecutor
from ..config import Config
from . import make_candidate

PLATFORMS = {
    "LinkedIn": "linkedin.com/in", "GitLab": "gitlab.com", "Kaggle": "kaggle.com",
    "HuggingFace": "huggingface.co", "Medium": "medium.com/@", "Hashnode": "hashnode.com/@",
    "Behance": "behance.net", "Dribbble": "dribbble.com", "CodePen": "codepen.io",
    "LeetCode": "leetcode.com/u", "HackerRank": "hackerrank.com/profile",
    "Wellfound": "wellfound.com/u", "ResearchGate": "researchgate.net/profile",
    "ORCID": "orcid.org", "Bitbucket": "bitbucket.org", "Substack": "substack.com/@",
}
OTW = re.compile(r"open to work|#opentowork|looking for (new )?(opportunit|role|job)|"
                 r"available for (hire|work)|seeking (new )?(role|opportunit)|actively looking", re.I)

class WebSearchSource:
    name = "websearch"

    def _one(self, args):
        platform, site, q, location = args
        query = f'site:{site} {q}' + (f" {location}" if location else "")
        try:
            r = requests.get("https://api.search.brave.com/res/v1/web/search",
                             headers={"X-Subscription-Token": Config.BRAVE_API_KEY},
                             params={"q": query, "count": 20}, timeout=20)
            items = r.json().get("web", {}).get("results", []) if r.ok else []
        except Exception:
            return []
        out = []
        for it in items:
            text = f'{it.get("title","")} {it.get("description","")}'
            out.append(make_candidate(platform, it["url"],
                                      re.split(r" [-|–·] ", it.get("title", ""))[0][:60],
                                      it.get("title", ""), bio=it.get("description", ""),
                                      open_to_work=bool(OTW.search(text))))
        return out

    def search(self, profile, location, limit):
        if not Config.BRAVE_API_KEY:
            return []
        q = " ".join(profile["skills"][:3] or [profile["title"]])
        jobs = [(p, s, q, location) for p, s in PLATFORMS.items()]
        # extra query variant to surface open-to-work profiles on LinkedIn
        jobs.append(("LinkedIn", "linkedin.com/in", q + ' "open to work"', location))
        with ThreadPoolExecutor(8) as ex:
            res = [c for part in ex.map(self._one, jobs) for c in part]
        return res[:limit]
