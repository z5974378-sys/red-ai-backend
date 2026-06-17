from openai import OpenAI
from config import settings

client = OpenAI(
    api_key=settings.gemini_api_key,
    base_url=settings.gemini_base_url if settings.gemini_base_url else "https://generativelanguage.googleapis.com/v1beta/openai/",
)
MODEL = settings.gemini_model

ANALYZE_SYSTEM = """你是一个小红书内容策划助手，专门帮助博主从参考素材中提炼选题方向。
你的输出必须是 JSON 格式，包含以下字段：
- positioning: 账号定位建议（1-3句）
- audience: 目标用户描述（1-2句）
- saved_titles: 提炼出的高互动标题候选，每行一个（最多12行）
- comments: 从素材中提取的用户真实疑问，每行一个（最多14条）
- competitors: 竞品摘要（2-4句）
- keywords: 核心关键词数组（最多15个字符串）

规则：
1. 只输出 JSON，不要有任何解释或包裹
2. 如果素材不足，用合理推断补充
3. saved_titles 要直接可用，不要使用占位符"""

GENERATE_SYSTEM = """你是一个小红书内容选题策划专家。根据博主资料生成可执行的选题库。

每个选题必须严格按以下 JSON 格式输出，每个选题独占一行（NDJSON格式，行内不换行）：
{"topic":"...","pain":"...","angle":"...","cover":"...","script":"...","priority":"高|中|低","risk":"...","series":true,"human":false}

字段说明：
- topic: 选题名，格式为"框架名：标题"，例：避坑清单：新手选绘本最容易踩的3个坑
- pain: 用户痛点（1-2句，具体）
- angle: 标题角度（1句，结合选定风格）
- cover: 首图文案+拍摄排版建议（3-5句）
- script: 正文脚本，5段，每段以"第N段："开头，段间用\\n\\n分隔
- priority: 必须是 高/中/低 之一
- risk: 风险提醒（不超过30字）
- series: 布尔值，是否适合做系列
- human: 布尔值，是否需要人工判断

规则：
1. 每行一个完整 JSON 对象，行内不得有换行符
2. 评论区问题优先作为选题，优先级设为高
3. 框架按顺序轮换：避坑清单、新手路线图、预算分层、对比测评、评论区答疑、案例拆解、模板工具
4. 每个选题必须有可执行的具体动作，不生成空泛方向
5. risk 字段不超过30字
6. 只输出 NDJSON，不要有任何前缀说明或总结"""

REWRITE_SYSTEM = """你是一个小红书文案润色专家。用户给你首图文案和正文脚本，你按指定风格重写。
输出必须是严格的 JSON：{"cover": "重写后的首图文案", "script": "重写后的正文脚本"}
只输出 JSON，不要有任何解释。保持原有段落结构和信息点，不要删减内容。"""

COMPLIANCE_SYSTEM = """你是一个小红书内容合规审核助手。找出文案中需要修改的具体短语。
输出必须是 JSON：{"suggestions": ["需修改的短语1", "需修改的短语2"]}
只输出 JSON，每条建议是一个需要弱化的具体短语，不超过20字。"""

TITLE_STYLE_DESC = {
    "bold": "吸睛夸张（bold）：先放大损失感或反差，再给明确判断",
    "qa": "问答讨论（qa）：用用户会问出口的问题做标题，引发评论互动",
    "useful": "干货宝藏（useful）：强调清单、模板、路线图和可收藏价值",
}

RISK_LEVEL_DESC = {
    "normal": "普通行业",
    "strict": "严格模式（避免绝对化表达）",
    "sensitive": "敏感行业（医疗/金融/法律，需极度谨慎）",
}


def _call(system: str, user: str, max_tokens: int = 2000) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=0.9,
    )
    return response.choices[0].message.content or ""


def call_generate(system: str, user: str, max_tokens: int = 6000) -> str:
    return _call(system, user, max_tokens)


def call_json(system: str, user: str, max_tokens: int = 2000) -> str:
    return _call(system, user, max_tokens)


def build_analyze_prompt(note_content: str, note_links: list[str], existing: dict, title_style: str, ocr_text: str = "") -> str:
    parts = []
    if existing.get("positioning"):
        parts.append(f"账号定位方向（已填）：{existing['positioning']}")
    if existing.get("audience"):
        parts.append(f"目标用户（已填）：{existing['audience']}")
    if note_content:
        parts.append(f"参考笔记内容：\n{note_content}")
    if ocr_text:
        parts.append(f"图片OCR识别内容：\n{ocr_text}")
    parts.append(f"标题风格偏好：{TITLE_STYLE_DESC.get(title_style, title_style)}")
    parts.append("请根据以上素材，输出分析结果 JSON。")
    return "\n\n".join(parts)


def build_generate_prompt(data: dict) -> str:
    return f"""账号定位：{data['positioning']}
目标用户：{data['audience']}
收藏标题：{data['saved_titles']}
评论区问题（优先处理）：{data['comments']}
竞品摘要：{data['competitors']}
标题风格：{TITLE_STYLE_DESC.get(data['title_style'], data['title_style'])}
行业风险等级：{RISK_LEVEL_DESC.get(data['risk_level'], data['risk_level'])}
请生成 {data['topic_count']} 个选题，按 NDJSON 格式逐行输出。"""


def build_rewrite_prompt(cover: str, script: str, tone: str, topic_name: str, positioning: str) -> str:
    tone_instructions = {
        "spoken": '口语化。把"用户"改成"你"，去掉书面表达，加入日常语气词（其实、你看、说真的），句子更短。',
        "hook": "钩子感。首图第一句必须制造悬念或反差。正文开头先抛最反常识的结论，后面再解释。句末多用感叹号，节奏要快。",
        "pro": '专业感。去掉"真的、其实、别急"等口语词，句子完整，标点规范，结论有依据。',
    }
    instruction = tone_instructions.get(tone, tone_instructions["pro"])
    return f"""选题：{topic_name}
账号定位：{positioning}
目标风格：{instruction}

首图文案：
{cover}

正文脚本：
{script}"""
