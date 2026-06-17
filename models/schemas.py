from typing import Optional
from pydantic import BaseModel


# ── analyze ──────────────────────────────────────────────────────────────────

class ExistingFields(BaseModel):
    positioning: str = ""
    audience: str = ""
    saved_titles: str = ""
    comments: str = ""
    competitors: str = ""


class AnalyzeRequest(BaseModel):
    note_content: str = ""
    note_links: list[str] = []
    image_ids: list[str] = []
    title_style: str = "bold"
    existing_fields: ExistingFields = ExistingFields()


class AnalyzeResponse(BaseModel):
    positioning: str
    audience: str
    saved_titles: str
    comments: str
    competitors: str
    keywords: list[str]
    ocr_text: Optional[str] = None


# ── generate ─────────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    session_id: Optional[str] = None
    positioning: str = ""
    audience: str = ""
    saved_titles: str = ""
    comments: str = ""
    competitors: str = ""
    topic_count: int = 12
    risk_level: str = "normal"
    title_style: str = "bold"


class TopicItem(BaseModel):
    id: str
    topic: str
    pain: str = ""
    angle: str = ""
    cover: str = ""
    script: str = ""
    priority: str = "中"
    risk: str = ""
    series: bool = True
    human: bool = False


# ── rewrite ──────────────────────────────────────────────────────────────────

class RewriteRequest(BaseModel):
    cover: str
    script: str
    tone: str  # spoken | hook | pro
    topic_name: str = ""
    positioning: str = ""


class RewriteResponse(BaseModel):
    cover: str
    script: str
    tone: str


# ── compliance ───────────────────────────────────────────────────────────────

class ComplianceRequest(BaseModel):
    text: str


class ComplianceResponse(BaseModel):
    status: str  # ok | warning
    local_hits: list[str]
    ai_suggestions: list[str]
    summary: str


# ── images ───────────────────────────────────────────────────────────────────

class ImageItem(BaseModel):
    id: str
    filename: str
    url: str
    size_bytes: int
    ocr_text: Optional[str] = None
    session_id: Optional[str] = None


class ImagesResponse(BaseModel):
    images: list[ImageItem]


# ── sessions ─────────────────────────────────────────────────────────────────

class SessionFields(BaseModel):
    positioning: str = ""
    audience: str = ""
    saved_titles: str = ""
    comments: str = ""
    competitors: str = ""
    note_content: str = ""
    topic_count: int = 12
    risk_level: str = "normal"
    title_style: str = "bold"


class SessionCreate(BaseModel):
    name: Optional[str] = None
    fields: SessionFields = SessionFields()


class SessionSummary(BaseModel):
    id: str
    name: Optional[str]
    created_at: str
    updated_at: str
    topic_count: int


class SessionDetail(BaseModel):
    id: str
    name: Optional[str]
    created_at: str
    updated_at: str
    fields: SessionFields
    topics: list[TopicItem]
    images: list[ImageItem]


class TopicPatch(BaseModel):
    cover: Optional[str] = None
    script: Optional[str] = None
    priority: Optional[str] = None
    human: Optional[bool] = None
