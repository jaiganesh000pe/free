"""Agent 5: on-demand enrichment of ONE candidate.
Scope: public professional contact details that the candidate published themselves
(GitHub profile + profile README, their own website/portfolio, Dev.to links).
Respects robots.txt, small page budget, no login-walled sites."""
import re, requests
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup

UA = {"User-Agent": "SourcerBot/1.0 (+recruiting; public pages only)"}
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+[a-z]")
PHONE_CTX = re.compile(r"(?:phone|mobile|cell|call|whatsapp|tel)[^\d+]{0,15}(\+?\d[\d\s().-]{7,17}\d)", re.I)
SOCIAL = {"linkedin": r"linkedin\.com/in/[\w-]+", "github": r"github\.com/[\w-]+",
          "twitter": r"(?:twitter|x)\.com/\w+", "instagram": r"instagram\.com/[\w.]+",
          "whatsapp": r"(?:wa\.me/\d+|api\.whatsapp\.com/send\?phone=\d+)",
          "youtube": r"youtube\.com/(?:@|c/|channel/)[\w-]+", "medium": r"medium\.com/@[\w.]+",
          "kaggle": r"kaggle\.com/[\w-]+", "stackoverflow": r"stackoverflow\.com/users/\d+[\w/-]*"}
RESUME = re.compile(r"""href=["']([^"']+?(?:resume|cv)[^"']*?\.(?:pdf|docx?)|[^"']+\.pdf)["']""", re.I)
SKIP_EMAIL = ("example.", "sentry", "noreply", "no-reply", ".png", ".jpg", "wixpress")

def _allowed(url):
    try:
        p = urlparse(url); rp = RobotFileParser(f"{p.scheme}://{p.netloc}/robots.txt")
        rp.read(); return rp.can_fetch(UA["User-Agent"], url)
    except Exception:
        return True

def _get(url):
    try:
        if _allowed(url):
            r = requests.get(url, headers=UA, timeout=12)
            if r.ok and "text" in r.headers.get("content-type", "text"):
                return r.text[:400_000]
    except Exception:
        pass
    return ""

def _mine(text, base, out):
    for m in EMAIL.findall(text):
        if not any(s in m.lower() for s in SKIP_EMAIL): out["emails"].add(m.lower())
    for m in re.findall(r'tel:([+\d][\d\s().-]{7,})', text) + PHONE_CTX.findall(text):
        digits = re.sub(r"\D", "", m)
        if 10 <= len(digits) <= 15: out["phones"].add(m.strip())
    for k, pat in SOCIAL.items():
        for m in re.findall(pat, text, re.I):
            if k == "github" and m.lower().split("/")[-1] in {"sponsors", "features", "about", "topics"}: continue
            out["links"].setdefault(k, "https://" + m)
    for m in RESUME.findall(text):
        out["resumes"].add(urljoin(base, m))

def enrich(c):
    out = {"emails": set(), "phones": set(), "links": {}, "resumes": set(), "sources": []}
    out["links"][c["platform"].lower()] = c["url"]
    ex, pages = c.get("extra", {}), []
    login = ex.get("login")
    if login:  # GitHub: profile README + profile fields
        pages.append((f"https://raw.githubusercontent.com/{login}/{login}/HEAD/README.md", "github-readme"))
        if ex.get("twitter"): out["links"]["twitter"] = f"https://twitter.com/{ex['twitter']}"
    for key in ("blog", "website"):
        if ex.get(key):
            u = ex[key] if ex[key].startswith("http") else "https://" + ex[key]
            pages.append((u, "personal-site"))
    if c["platform"] == "Dev.to":
        pages.append((c["url"], "devto"))
    if c.get("email"): out["emails"].add(c["email"])
    budget = 6
    while pages and budget:
        url, label = pages.pop(0); budget -= 1
        text = _get(url)
        if not text: continue
        out["sources"].append(url)
        _mine(text, url, out)
        if label == "personal-site":  # follow contact/about/resume pages once
            soup = BeautifulSoup(text, "html.parser")
            for a in soup.find_all("a", href=True):
                if re.search(r"contact|about|resume|cv", a["href"] + a.text, re.I) and len(pages) < 3:
                    nxt = urljoin(url, a["href"])
                    if urlparse(nxt).netloc == urlparse(url).netloc and nxt not in out["sources"]:
                        pages.append((nxt, "site-sub"))
    return {"emails": sorted(out["emails"]), "phones": sorted(out["phones"]),
            "links": out["links"], "resumes": sorted(out["resumes"]), "sources": out["sources"]}
