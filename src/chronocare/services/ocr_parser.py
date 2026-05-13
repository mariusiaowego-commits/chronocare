"""LLM-powered OCR text parser — converts raw OCR text to structured JSON."""

import json
import os
import re
from typing import Any

import httpx

from chronocare.config import settings

# Timeout for LLM API call (seconds)
LLM_TIMEOUT = 60.0

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Valid record types
VALID_RECORD_TYPES = frozenset(
    {"medical_record", "lab_report", "prescription", "doctor_order"}
)

# ---------------------------------------------------------------------------
# Prompt template builders (Chinese medical domain)
# Each function returns the full prompt string for its record_type.
# ---------------------------------------------------------------------------


def _medical_record_prompt() -> str:
    intro = (
        "你是一位专业的中文医疗文书分析助手。\n"
        "你的任务是将一段就医记录的OCR识别文本转换为结构化的JSON数据。\n\n"
        "请严格按照以下JSON Schema输出，不要添加任何解释或额外文本：\n"
    )
    schema = (
        '{\n'
        '  "diagnosis": ["诊断1", "诊断2"],\n'
        '  "symptoms": ["症状1", "症状2"],\n'
        '  "treatment": "治疗方案简要描述",\n'
        '  "followup": "复诊建议或随访说明"\n'
        "}"
    )
    requirements = (
        "要求：\n"
        "- diagnosis：诊断列表，如果没有则返回空数组[]\n"
        "- symptoms：症状列表，从文本中提取，如果没有则返回空数组[]\n"
        "- treatment：字符串，简要描述治疗方案，不可为空（无内容时写\"未提及\"）\n"
        "- followup：字符串，复诊或随访建议，如果没有则写\"未提及\"\n"
        '- 所有字段都必须存在，即使内容为"未提及"\n'
        "- 仅输出JSON，不要包含markdown代码块标记\n\n"
        "OCR原始文本：\n"
    )
    return intro + schema + "\n" + requirements


def _lab_report_prompt() -> str:
    intro = (
        "你是一位专业的中文医学检验报告分析助手。\n"
        "你的任务是将一段化验单的OCR识别文本转换为结构化的JSON数据。\n\n"
        "请严格按照以下JSON Schema输出，不要添加任何解释或额外文本：\n"
    )
    schema = (
        "{\n"
        '  "tests": [\n'
        "    {\n"
        '      "name": "检验项目名称",\n'
        '      "value": "数值结果",\n'
        '      "unit": "单位",\n'
        '      "reference": "参考范围",\n'
        '      "status": "normal|high|low|slightly_high|slightly_low"\n'
        "    }\n"
        "  ],\n"
        '  "summary": "整体检验结果摘要说明"\n'
        "}"
    )
    requirements = (
        "要求：\n"
        "- tests：检验项目数组，每个项目必须包含"
        "name/value/unit/reference/status五个字段\n"
        "- status取值规则：\n"
        "  - 数值高于参考范围上限：high（明显高）或slightly_high（轻微高）\n"
        "  - 数值低于参考范围下限：low（明显低）或slightly_low（轻微低）\n"
        "  - 数值在参考范围内：normal\n"
        "  - 无法判断时默认normal\n"
        "- summary：整体摘要，无内容时写\"未提及\"\n"
        "- 仅输出JSON，不要包含markdown代码块标记\n\n"
        "OCR原始文本：\n"
    )
    return intro + schema + "\n" + requirements


def _prescription_prompt() -> str:
    intro = (
        "你是一位专业的中文处方分析助手。\n"
        "你的任务是将一段处方的OCR识别文本转换为结构化的JSON数据。\n\n"
        "请严格按照以下JSON Schema输出，不要添加任何解释或额外文本：\n"
    )
    schema = (
        "{\n"
        '  "medications": [\n'
        "    {\n"
        '      "name": "药品名称",\n'
        '      "dosage": "剂量（如500mg）",\n'
        '      "frequency": "用药频率（如每日两次）",\n'
        '      "duration": "疗程（如7天、长期）",\n'
        '      "notes": "用药注意事项或特殊说明"\n'
        "    }\n"
        "  ],\n"
        '  "pharmacy": "取药药店或药房信息",\n'
        '  "doctor_advice": "医生其他建议"\n'
        "}"
    )
    requirements = (
        "要求：\n"
        "- medications：药品列表，每个药品必须包含"
        "name/dosage/frequency/duration/notes五个字段\n"
        "- 未提及的字段用\"未提及\"填充\n"
        "- pharmacy：取药地点，没有则写\"未提及\"\n"
        "- doctor_advice：饮食建议、检查建议等其他建议，没有则写\"未提及\"\n"
        "- 仅输出JSON，不要包含markdown代码块标记\n\n"
        "OCR原始文本：\n"
    )
    return intro + schema + "\n" + requirements


def _doctor_order_prompt() -> str:
    intro = (
        "你是一位专业的中文医嘱分析助手。\n"
        "你的任务是将一段医嘱的OCR识别文本转换为结构化的JSON数据。\n\n"
        "请严格按照以下JSON Schema输出，不要添加任何解释或额外文本：\n"
    )
    schema = (
        "{\n"
        '  "medications": [\n'
        "    {\n"
        '      "name": "药品名称",\n'
        '      "dosage": "剂量",\n'
        '      "frequency": "用药频率",\n'
        '      "duration": "疗程",\n'
        '      "notes": "用药注意事项"\n'
        "    }\n"
        "  ],\n"
        '  "lifestyle": ["生活方式建议1", "生活方式建议2"],\n'
        '  "followup": "复诊或随访安排",\n'
        '  "special_instructions": "特殊医嘱或注意事项"\n'
        "}"
    )
    requirements = (
        "要求：\n"
        "- medications：用药列表，字段说明同处方\n"
        "- lifestyle：生活方式建议列表（如饮食、运动、作息等），"
        "没有则返回空数组[]\n"
        "- followup：复诊安排，没有则写\"未提及\"\n"
        "- special_instructions：特殊医嘱，没有则写\"未提及\"\n"
        "- 仅输出JSON，不要包含markdown代码块标记\n\n"
        "OCR原始文本：\n"
    )
    return intro + schema + "\n" + requirements


_PROMPT_BUILDERS: dict[str, callable] = {
    "medical_record": _medical_record_prompt,
    "lab_report": _lab_report_prompt,
    "prescription": _prescription_prompt,
    "doctor_order": _doctor_order_prompt,
}


# ---------------------------------------------------------------------------
# LLM call layer
# ---------------------------------------------------------------------------


def _build_messages(record_type: str, raw_text: str) -> list[dict[str, str]]:
    prompt_template = _PROMPT_BUILDERS[record_type]()
    user_content = prompt_template + raw_text
    return [{"role": "user", "content": user_content}]


def _call_openrouter(messages: list[dict[str, str]], model: str) -> str:
    api_key = settings.llm_api_key or os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not set in environment or config")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 1024,
    }

    with httpx.Client(timeout=LLM_TIMEOUT) as client:
        response = client.post(OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    choices = data.get("choices", [])
    if not choices:
        raise ValueError(f"No choices in OpenRouter response: {data}")
    return choices[0]["message"]["content"]


def _strip_code_fences(text: str) -> str:
    """Remove markdown JSON code fences if present."""
    text = text.strip()
    # Remove opening fence (with optional language tag)
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text, flags=re.IGNORECASE)
    return text.strip()


def _parse_json_robust(text: str) -> dict[str, Any]:
    """Parse JSON, handling markdown fences and trailing text."""
    cleaned = _strip_code_fences(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try extracting first { ... } substring
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(cleaned[start:end])
        raise


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def parse_ocr_text(raw_text: str, record_type: str) -> dict[str, Any]:
    """Parse OCR text into structured JSON using LLM.

    Args:
        raw_text: The raw OCR-recognized text.
        record_type: One of "medical_record", "lab_report",
            "prescription", "doctor_order".

    Returns:
        Structured JSON dict for the given record type.
        On error, returns {"error": "...", "raw_text": raw_text}.
    """
    if not raw_text or not raw_text.strip():
        return {"error": "raw_text is empty", "raw_text": raw_text}

    if record_type not in VALID_RECORD_TYPES:
        return {
            "error": (
                f"Unknown record_type: {record_type}. "
                f"Must be one of {sorted(VALID_RECORD_TYPES)}"
            ),
            "raw_text": raw_text,
        }

    model = settings.llm_model
    messages = _build_messages(record_type, raw_text)

    try:
        raw_response = _call_openrouter(messages, model)
        return _parse_json_robust(raw_response)
    except Exception as exc:  # noqa: BLE001
        return {
            "error": f"{type(exc).__name__}: {exc}",
            "raw_text": raw_text,
        }
