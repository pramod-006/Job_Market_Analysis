from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Dict
import spacy
from spacy.matcher import PhraseMatcher
import json


# Load NLP
nlp = spacy.load("en_core_web_sm")

with open("skill_frequency.json", "r") as f:
    skill_frequency = json.load(f)

TREND_THRESHOLD = 0.05


skill_keywords = list(skill_frequency.keys())


matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
patterns = [nlp.make_doc(skill) for skill in skill_keywords]
matcher.add("SKILL", patterns)


app = FastAPI(title="Skill Trend Detector API")


class JobDesc(BaseModel):
    job_description: str


class SkillInfo(BaseModel):
    skill: str
    category: str
    trend_score: float

class SkillResponse(BaseModel):
    detected_skills: List[SkillInfo]

def extract_skills(text: str) -> List[str]:
    doc = nlp(text)
    matches = matcher(doc)
    return list({doc[start:end].text.lower() for _, start, end in matches})


def classify_skill(skill: str) -> Dict:
    score = skill_frequency.get(skill, 0.5)  # default unknown score
    category = "established" if score >= TREND_THRESHOLD else "emerging"
    return {"skill": skill, "category": category, "trend_score": round(score, 2)}


@app.post("/detect_skills", response_model=SkillResponse)
async def detect_skills(job: JobDesc):
    extracted = extract_skills(job.job_description)
    results = [classify_skill(skill) for skill in extracted]
    return {"detected_skills": results}
