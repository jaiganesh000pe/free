import requests
from concurrent.futures import ThreadPoolExecutor
from ..config import Config
from . import make_candidate

LANGS = {"python", "java", "javascript", "typescript", "go", "rust", "c++", "c#",
         "ruby", "php", "scala", "kotlin", "swift"}

def _h():
    h = {"Accept": "application/vnd.github+json"}
    if Config.GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {Config.GITHUB_TOKEN}"
    return h

def fetch_user(login):
    r = requests.get(f"https://api.github.com/users/{login}", headers=_h(), timeout=15)
    return r.json() if r.ok else None

class GitHubSource:
    name = "github"

    def search(self, profile, location, limit):
        langs = [s for s in profile["skills"] if s in LANGS][:2]
        kw = [s for s in profile["skills"] if s not in LANGS][:1]
        q = " ".join([f"language:{l}" for l in langs] + kw) or profile["title"]
        q += " repos:>3 followers:>3" + (f' location:"{location}"' if location else "")
        logins = []
        for page in (1, 2, 3, 4):
            if len(logins) >= limit:
                break
            r = requests.get("https://api.github.com/search/users", headers=_h(),
                             params={"q": q, "per_page": 100, "page": page}, timeout=20)
            if not r.ok:
                break
            logins += [i["login"] for i in r.json().get("items", [])]
        with ThreadPoolExecutor(10) as ex:
            users = [u for u in ex.map(fetch_user, logins[:limit]) if u]
        return [make_candidate("GitHub", u["html_url"], u.get("name") or u["login"],
                               u.get("company") or u.get("bio") or "", u.get("location") or "",
                               u.get("bio") or "", open_to_work=bool(u.get("hireable")),
                               email=u.get("email") or "",
                               extra={"login": u["login"], "blog": u.get("blog"),
                                      "twitter": u.get("twitter_username")}) for u in users]
