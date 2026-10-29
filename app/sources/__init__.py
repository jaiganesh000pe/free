import hashlib

def make_candidate(platform, url, name="", headline="", location="", bio="",
                   skills=None, open_to_work=False, email="", extra=None):
    return {"id": hashlib.sha1(url.lower().encode()).hexdigest()[:10],
            "platform": platform, "url": url, "name": name or url.rstrip("/").split("/")[-1],
            "headline": headline, "location": location, "bio": bio,
            "skills": skills or [], "open_to_work": open_to_work,
            "email": email, "extra": extra or {}, "match": 0.0}
