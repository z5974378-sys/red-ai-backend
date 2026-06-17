from fastapi import APIRouter, HTTPException
from models.schemas import SessionFields

router = APIRouter()


@router.get("/sessions/{session_id}")
def get_session(session_id: str):
    raise HTTPException(status_code=404, detail="会话不存在")


@router.patch("/sessions/{session_id}", status_code=200)
def update_session(session_id: str, fields: SessionFields):
    return {"ok": True}


@router.patch("/sessions/{session_id}/topics/{topic_id}")
def patch_topic(session_id: str, topic_id: str):
    return {"ok": True}
