import requests
from . import make_candidate

class StackOverflowSource:
    name = "stackoverflow"

    def search(self, profile, location, limit):
        out = []
        for tag in profile["skills"][:3]:
            r = requests.get(f"https://api.stackexchange.com/2.3/tags/{tag}/top-answerers/all_time",
                             params={"site": "stackoverflow", "pagesize": min(limit, 100)}, timeout=20)
            if not r.ok:
                continue
            for i in r.json().get("items", []):
                u = i["user"]
                out.append(make_candidate("StackOverflow", u["link"], u["display_name"],
                                          f"Top {tag} answerer", skills=[tag]))
        return out[:limit]
