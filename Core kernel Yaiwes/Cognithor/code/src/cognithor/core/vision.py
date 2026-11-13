"""Core Vision Messages -- Backend-agnostic multimodal message construction.

Provides types and functions to send images (screenshots) together
with text to any LLM backend.  Each backend has its
own format:

  - Anthropic: content array with type=image / type=text blocks
  - OpenAI:    content array with type=image_url blocks
  - Ollama:    content=text + images=[base64, ...]

The functions here abstract these differences.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

# ── Typen ─────────────────────────────────────────────────────────────


class ImageMediaType(StrEnum):
    """Supported image formats."""

    PNG = "image/png"
    JPEG = "image/jpeg"
    GIF = "image/gif"
    WEBP = "image/webp"


@dataclass
class ImageContent:
    """Ein einzelnes Base64-kodiertes Bild."""

    data_b64: str
    media_type: ImageMediaType = ImageMediaType.PNG
    alt_text: str = ""


@dataclass
class MultimodalMessage:
    """A message that contains text and optionally images."""

    role: str = "user"
    text: str = ""
    images: list[ImageContent] = field(default_factory=list)

    def has_images(self) -> bool:
        return len(self.images) > 0


# ── Builder ───────────────────────────────────────────────────────────


def build_vision_message(
    text: str,
    images_b64: list[str],
    *,
    media_type: ImageMediaType = ImageMediaType.PNG,
    role: str = "user",
    alt_text: str = "Screenshot",
) -> MultimodalMessage:
    """Baut eine MultimodalMessage aus Text und Base64-Bildern.

    Args:
        text: Der Text-Inhalt der Nachricht.
        images_b64: Liste von Base64-kodierten Bilddaten.
        media_type: Bildformat (Standard: PNG).
        role: Rolle der Nachricht (Standard: user).
        alt_text: Alt text for the images.

    Returns:
        MultimodalMessage mit Text und Bildern.
    """
    images = [
        ImageContent(data_b64=b64, media_type=media_type, alt_text=alt_text)
        for b64 in images_b64
        if b64
    ]
    return MultimodalMessage(role=role, text=text, images=images)


# ── Backend-spezifische Formatierung ─────────────────────────────────


# All OpenAI-compatible backends that support the image_url format
_OPENAI_VISION_BACKENDS = frozenset(
    {
        "openai",
        "lmstudio",
        "groq",
        "together",
        "deepseek",
        "mistral",
        "openrouter",
        "xai",
        "cerebras",
        "github",
        "bedrock",
        "huggingface",
        "moonshot",
    }
)


def format_for_backend(message: MultimodalMessage, backend_type: str) -> dict[str, Any]:
    """Konvertiert eine MultimodalMessage ins Backend-spezifische Format.

    Args:
        message: Die zu konvertierende Nachricht.
        backend_type: "anthropic", "openai", "ollama" oder anderes.

    Returns:
        Dict im Backend-spezifischen Message-Format.
    """
    if not message.has_images():
        return {"role": message.role, "content": message.text}

    if backend_type == "anthropic":
        return _format_anthropic(message)
    elif backend_type in _OPENAI_VISION_BACKENDS:
        return _format_openai(message)
    elif backend_type == "ollama":
        return _format_ollama(message)
    else:
        return _format_text_fallback(message)


def _format_anthropic(message: MultimodalMessage) -> dict[str, Any]:
    """Anthropic format: content array with image/text blocks."""
    content: list[dict[str, Any]] = []
    for img in message.images:
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": img.media_type.value,
                    "data": img.data_b64,
                },
            }
        )
    if message.text:
        content.append({"type": "text", "text": message.text})
    return {"role": message.role, "content": content}


def _format_openai(message: MultimodalMessage) -> dict[str, Any]:
    """OpenAI format: content array with image_url blocks."""
    content: list[dict[str, Any]] = []
    for img in message.images:
        data_url = f"data:{img.media_type.value};base64,{img.data_b64}"
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": data_url},
            }
        )
    if message.text:
        content.append({"type": "text", "text": message.text})
    return {"role": message.role, "content": content}


def _format_ollama(message: MultimodalMessage) -> dict[str, Any]:
    """Ollama-Format: content=text, images=[base64, ...]."""
    return {
        "role": message.role,
        "content": message.text,
        "images": [img.data_b64 for img in message.images],
    }


def _format_text_fallback(message: MultimodalMessage) -> dict[str, Any]:
    """Text fallback for unknown backends: images as alt text."""
    parts = []
    for img in message.images:
        alt = img.alt_text or "Bild"
        parts.append(f"[{alt}]")
    if message.text:
        parts.append(message.text)
    return {"role": message.role, "content": "\n".join(parts)}


# ── Erkennung ─────────────────────────────────────────────────────────


def is_multimodal_message(msg: dict[str, Any]) -> bool:
    """Erkennt ob eine Message multimodalen Inhalt hat.

    Checks all 3 backend formats:
      - Anthropic/OpenAI: content is a list with image/image_url blocks
      - Ollama: images-Feld vorhanden

    Args:
        msg: Eine Message als Dict.

    Returns:
        True if the message contains images.
    """
    if not isinstance(msg, dict):
        return False

    # Ollama-Format: images-Feld
    images = msg.get("images")
    if isinstance(images, list) and len(images) > 0:
        return True

    # Anthropic/OpenAI-Format: content ist Liste
    content = msg.get("content")
    if isinstance(content, list):
        for block in content:
            if not isinstance(block, dict):
                continue
            block_type = block.get("type", "")
            if block_type in ("image", "image_url"):
                return True

    return False
