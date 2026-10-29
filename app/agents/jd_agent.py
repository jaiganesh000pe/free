"""Agent 1: turns a raw JD into a structured search profile."""
import re
from ..llm import ask_json

SKILLS = """python java javascript typescript go golang rust c++ c# ruby php scala kotlin swift
react angular vue node.js django flask fastapi spring aws azure gcp docker kubernetes terraform
sql postgresql mysql mongodb redis kafka spark airflow pytorch tensorflow scikit-learn
machine learning deep learning nlp llm data science devops ci/cd graphql microservices
android ios flutter figma tableau power bi snowflake dbt""".split("\n")
SKILLS = [s for line in SKILLS for s in re.split(r"\s(?=\S)", line)]
MULTI = ["machine learning", "deep learning", "data science", "power bi"]
VOCAB = sorted(set([s for s in SKILLS if s not in
                    {"machine", "learning", "deep", "data", "science", "power", "bi"}] + MULTI))

def extract_skills(text):
    t = text.lower()
    return [s for s in VOCAB if re.search(rf"(?<![\w+#]){re.escape(s)}(?![\w+#])", t)]

def analyze(jd: str) -> dict:
    skills = extract_skills(jd)
    first = next((l.strip() for l in jd.splitlines() if l.strip()), "")[:80]
    profile = {"title": first, "skills": skills[:12], "seniority": None}
    llm = ask_json("Extract hiring requirements from a job description.",
                   'Return {"title":str,"seniority":str,"skills":[str],"keywords":[str]}\n\n' + jd[:4000])
    if llm:
        profile["title"] = llm.get("title") or profile["title"]
        profile["seniority"] = llm.get("seniority")
        profile["skills"] = list(dict.fromkeys([s.lower() for s in llm.get("skills", [])] + skills))[:12]
    return profile
