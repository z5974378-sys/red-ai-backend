import json

from fastapi import APIRouter

from models.schemas import AnalyzeRequest, AnalyzeResponse
from services.gemini_client import call_json, ANALYZE_SYSTEM, build_analyze_prompt

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    user_prompt = build_analyze_prompt(
        note_content=req.note_content,
        note_links=req.note_links,
        existing=req.existing_fields.model_dump(),
        title_style=req.title_style,
        ocr_text="",
    )

    raw = call_json(ANALYZE_SYSTEM, user_prompt, max_tokens=2000).strip()

    try:
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
    except Exception:
        data = {}

    def to_str(val):
        if isinstance(val, list):
            return "\n".join(str(v) for v in val)
        return val or ""

    return AnalyzeResponse(
        positioning=to_str(data.get("positioning")),
        audience=to_str(data.get("audience")),
        saved_titles=to_str(data.get("saved_titles")),
        comments=to_str(data.get("comments")),
        competitors=to_str(data.get("competitors")),
        keywords=data.get("keywords", []) if isinstance(data.get("keywords"), list) else [],
        ocr_text=None,
    )
