import requests
from . import make_candidate

class DevToSource:
    name = "devto"

    def search(self, profile, location, limit):
        out = []
        for tag in profile["skills"][:3]:
            r = requests.get("https://dev.to/api/articles", params={"tag": tag.replace(".", ""), "per_page": 50}, timeout=20)
            if not r.ok:
                continue
            for a in r.json():
                u = a["user"]
                out.append(make_candidate("Dev.to", f"https://dev.to/{u['username']}", u["name"],
                                          a["title"], bio=a.get("description", ""), skills=[tag],
                                          extra={"twitter": u.get("twitter_username"),
                                                 "github": u.get("github_username"),
                                                 "website": u.get("website_url")}))
        return out[:limit]
