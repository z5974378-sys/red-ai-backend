import json

from fastapi import APIRouter

from models.schemas import ComplianceRequest, ComplianceResponse
from services.gemini_client import call_json, COMPLIANCE_SYSTEM

router = APIRouter()

SENSITIVE_WORDS = [
    "医疗", "医美", "减肥", "理财", "投资", "保险", "法律", "药",
    "疗效", "治愈", "收益", "贷款", "最", "第一", "保证", "100%", "永久", "无效退款",
]


@router.post("/compliance", response_model=ComplianceResponse)
def compliance(req: ComplianceRequest):
    text = req.text.strip()
    if not text:
        return ComplianceResponse(
            status="ok",
            local_hits=[],
            ai_suggestions=[],
            summary="请先粘贴要检测的文案",
        )

    local_hits = [w for w in SENSITIVE_WORDS if w in text]

    ai_suggestions: list[str] = []
    if len(local_hits) >= 3 or (local_hits and len(text) > 200):
        try:
            raw = call_json(COMPLIANCE_SYSTEM, f"请检查以下小红书文案，找出需要弱化的具体短语：\n\n{text}", max_tokens=400).strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)
            ai_suggestions = data.get("suggestions", [])
        except Exception:
            pass

    if not local_hits:
        summary = "本地词库未发现明显高风险词，发布前仍建议复查。"
        status = "ok"
    else:
        summary = f"发现需复核词：{'、'.join(local_hits)}。建议弱化绝对化、功效化和收益承诺表达。"
        status = "warning"

    return ComplianceResponse(
        status=status,
        local_hits=local_hits,
        ai_suggestions=ai_suggestions,
        summary=summary,
    )
