import json

from fastapi import APIRouter

from database import get_db
from models.schemas import AnalyzeRequest, AnalyzeResponse
from services.gemini_client import call_json, ANALYZE_SYSTEM, build_analyze_prompt

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    # 收集已上传图片的 OCR 文字
    ocr_text = ""
    if req.image_ids:
        with get_db() as conn:
            for img_id in req.image_ids:
                row = conn.execute(
                    "SELECT ocr_text FROM images WHERE id = ?", (img_id,)
                ).fetchone()
                if row and row["ocr_text"]:
                    ocr_text += row["ocr_text"] + "\n"
        ocr_text = ocr_text.strip()

    user_prompt = build_analyze_prompt(
        note_content=req.note_content,
        note_links=req.note_links,
        existing=req.existing_fields.model_dump(),
        title_style=req.title_style,
        ocr_text=ocr_text,
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
        ocr_text=ocr_text if ocr_text else None,
    )
