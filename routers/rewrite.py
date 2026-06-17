import json

from fastapi import APIRouter

from models.schemas import RewriteRequest, RewriteResponse
from services.gemini_client import call_json, REWRITE_SYSTEM, build_rewrite_prompt

router = APIRouter()


@router.post("/rewrite", response_model=RewriteResponse)
def rewrite(req: RewriteRequest):
    user_prompt = build_rewrite_prompt(
        cover=req.cover,
        script=req.script,
        tone=req.tone,
        topic_name=req.topic_name,
        positioning=req.positioning,
    )

    raw = call_json(REWRITE_SYSTEM, user_prompt, max_tokens=1200).strip()

    try:
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
    except Exception:
        data = {"cover": req.cover, "script": req.script}

    return RewriteResponse(
        cover=data.get("cover", req.cover),
        script=data.get("script", req.script),
        tone=req.tone,
    )
