"""Vision-based OCR engine using OpenRouter vision models.

This replaces the macOS Vision Framework (Swift) with a cross-platform
solution using OpenRouter's vision-capable LLMs (e.g., Gemini, GPT-4o).
"""

import base64
import os
from pathlib import Path

import httpx

from chronocare.config import settings

# Timeout for vision API call (seconds)
VISION_TIMEOUT = 120.0

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Vision-capable models (prefer fast/cheap ones for OCR)
VISION_MODELS = [
    "google/gemini-2.0-flash",  # Fast, cheap, good vision
    "google/gemini-2.5-flash",  # Newer, still fast
    "openai/gpt-4o-mini",       # Good vision, reasonable cost
]


def _encode_image_base64(image_path: str) -> str:
    """Read image file and encode as base64."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _get_mime_type(image_path: str) -> str:
    """Get MIME type from file extension."""
    ext = Path(image_path).suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".heic": "image/heic",
    }
    return mime_map.get(ext, "image/jpeg")


async def is_vision_available() -> bool:
    """Check if vision OCR is available.

    Returns True if OpenRouter API key is configured.
    """
    api_key = settings.llm_api_key or os.environ.get("OPENROUTER_API_KEY", "")
    return bool(api_key)


async def extract_text_with_vision(image_path: str, model: str | None = None) -> str:
    """Extract text from an image using OpenRouter vision model.

    Args:
        image_path: Absolute path to the image file (PNG, JPG, etc.)
        model: Optional model override. If None, uses settings.llm_model
               or falls back to VISION_MODELS[0].

    Returns:
        Recognized text as a plain string. Empty string if no text found.

    Raises:
        FileNotFoundError: The image file does not exist.
        RuntimeError: Vision API is not available.
        TimeoutError: API call timed out.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    api_key = settings.llm_api_key or os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "OpenRouter API key not configured. "
            "Set OPENROUTER_API_KEY environment variable or llm_api_key in config."
        )

    # Encode image
    image_base64 = _encode_image_base64(str(path.absolute()))
    mime_type = _get_mime_type(str(path))

    # Select model
    selected_model = model or settings.llm_model
    # If the configured model doesn't support vision, fallback
    if "vision" not in selected_model.lower() and not any(
        m in selected_model.lower() for m in ["gpt-4o", "gemini", "claude"]
    ):
        selected_model = VISION_MODELS[0]

    # Build request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": selected_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "请识别并提取这张图片中的所有文字内容。"
                            "如果是医疗文档（化验单、处方、病历等），请准确保留：\n"
                            "- 数值和单位\n"
                            "- 参考范围\n"
                            "- 药品名称和用法\n"
                            "- 诊断和医嘱\n"
                            "直接输出识别到的文字，不要添加解释。"
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_base64}",
                        },
                    },
                ],
            }
        ],
        "max_tokens": 4096,
    }

    try:
        with httpx.Client(timeout=VISION_TIMEOUT) as client:
            response = client.post(OPENROUTER_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices", [])
        if not choices:
            raise ValueError(f"No choices in response: {data}")

        return choices[0]["message"]["content"].strip()

    except httpx.TimeoutException:
        raise TimeoutError(
            f"Vision API timed out after {VISION_TIMEOUT} seconds for: {image_path}"
        ) from None
    except httpx.HTTPStatusError as e:
        raise RuntimeError(
            f"Vision API error: {e.response.status_code} - {e.response.text}"
        ) from e


async def extract_text(image_path: str) -> str:
    """Main OCR entry point — tries vision API first.

    This is the function called by the medical_record service.
    It replaces the Swift Vision Framework with a cross-platform solution.
    """
    if not await is_vision_available():
        raise RuntimeError(
            "Vision OCR is not available. "
            "Ensure OPENROUTER_API_KEY is set in environment or config."
        )

    return await extract_text_with_vision(image_path)
