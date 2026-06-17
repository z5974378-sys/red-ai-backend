import json
import uuid
from typing import Optional

from fastapi import APIRouter

from models.schemas import GenerateRequest, TopicItem
from services.gemini_client import call_generate, GENERATE_SYSTEM, build_generate_prompt

router = APIRouter()


def _parse_topics(raw: str) -> list[dict]:
    topics = []
    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()
        data = json.loads(cleaned)
        if isinstance(data, list):
            for obj in data:
                if isinstance(obj, dict) and "topic" in obj:
                    obj["id"] = str(uuid.uuid4())
                    topics.append(obj)
            return topics
    except Exception:
        pass

    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("```"):
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict) and "topic" in obj:
                obj["id"] = str(uuid.uuid4())
                topics.append(obj)
        except json.JSONDecodeError:
            start = line.find("{")
            end = line.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    obj = json.loads(line[start:end])
                    if isinstance(obj, dict) and "topic" in obj:
                        obj["id"] = str(uuid.uuid4())
                        topics.append(obj)
                except json.JSONDecodeError:
                    pass

    return topics


@router.post("/generate")
def generate(req: GenerateRequest):
    prompt = build_generate_prompt(req.model_dump())
    raw = call_generate(GENERATE_SYSTEM, prompt, max_tokens=min(6000, req.topic_count * 420))
    topics = _parse_topics(raw)
    return {"topics": topics, "total": len(topics)}
