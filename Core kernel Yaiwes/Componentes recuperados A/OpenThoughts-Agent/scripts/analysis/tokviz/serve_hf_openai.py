"""serve_hf_openai.py -- minimal OpenAI-compatible shim around an HF model.

Wraps the SAME HF transformers Qwen model used by the chat half and exposes:

    POST /v1/chat/completions
    GET  /v1/models

The chat-completions handler accepts the standard ``messages`` array, applies
the Qwen chat template (add_generation_prompt=True), tokenizes, runs
``model.generate``, and returns an OpenAI-shaped response.

Every incoming request's *fully-templated* prompt string is appended to a
JSONL log (config.SHIM_LOG) BEFORE generation, capturing the exact
tokenizer-input for the agentic half.

Select instruct vs base model with the env var TOKVIZ_SERVE_MODEL = "instruct"
(default) or "base", or pass --model base on the command line.

Runs in the otagent env:
    /Users/benjaminfeuer/miniconda3/envs/otagent/bin/python serve_hf_openai.py [--model instruct|base] [--port 8123]
"""

from __future__ import annotations

import argparse
import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional

import torch
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from config import (
    BASE_MODEL_ID,
    INSTRUCT_MODEL_ID,
    MAX_NEW_TOKENS,
    MAX_NEW_TOKENS_INSTRUCT,
    SHIM_HOST,
    SHIM_LOG,
    SHIM_PORT,
)
from model_utils import load, stop_ids


# --------------------------------------------------------------------------- #
# Request / response schemas (loose -- we accept extra fields swe-agent sends)
# --------------------------------------------------------------------------- #
class ChatMessage(BaseModel):
    role: str
    content: Any = ""  # str, or list-of-parts for some clients


class ChatRequest(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage]
    # OpenAI function/tool schema array. When present (function_calling parser),
    # we forward it to apply_chat_template so Qwen3.5 renders the tools into a
    # <tools>...</tools> JSON block in the system message -- the whole point of
    # the function_calling agentic variant.
    tools: Optional[Any] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    stop: Optional[Any] = None

    class Config:
        extra = "allow"


def _content_to_text(content: Any) -> str:
    """Flatten OpenAI content (str or list of {type,text}) to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for p in content:
            if isinstance(p, dict):
                parts.append(p.get("text", ""))
            else:
                parts.append(str(p))
        return "".join(parts)
    return str(content)


def make_app(which: str) -> FastAPI:
    model_id = INSTRUCT_MODEL_ID if which == "instruct" else BASE_MODEL_ID
    tok, model, device = load(model_id)
    app = FastAPI(title=f"hf-openai-shim [{which}]")

    def log_prompt(record: Dict[str, Any]) -> None:
        with open(SHIM_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    @app.get("/v1/models")
    def list_models():
        return {
            "object": "list",
            "data": [{"id": model_id, "object": "model", "owned_by": "tokviz"}],
        }

    _borrowed = {"template": None, "loaded": False}

    def _get_borrowed_template():
        """Lazily fetch the INSTRUCT sibling's chat_template string.

        Used only when the served (base) model's tokenizer has NO chat_template.
        Base and -it share the same vocab/special tokens, so the -it template
        tokenizes correctly through the base tokenizer.
        """
        if not _borrowed["loaded"]:
            _borrowed["loaded"] = True
            try:
                from transformers import AutoTokenizer

                itok = AutoTokenizer.from_pretrained(INSTRUCT_MODEL_ID)
                _borrowed["template"] = itok.chat_template
            except Exception:
                _borrowed["template"] = None
        return _borrowed["template"]

    def _template(messages, tools):
        """Render the chat/agentic prompt. Returns (text, used_borrowed_template).

        Normal path: the served model's own chat template, with enable_thinking
        when the template accepts it (thinking-ON: open <think> tail), else
        without. ``tools``, when present, is forwarded so the template renders the
        structured tool array (Qwen: <tools> JSON; Gemma: <|tool> blocks; etc.).

        Base-model path: a true base (e.g. gemma-4-E2B) has NO chat_template, so
        apply_chat_template raises ValueError. We then BORROW the instruct
        sibling's template and render the prompt anyway -- feeding the base model
        a fully-formed chat/agentic prompt it was never trained on. This is the
        failure mode under study (base + chat formatting); the caller logs a flag
        so the captured record is honest about the borrow.
        """
        kwargs = dict(add_generation_prompt=True, tokenize=False)
        if tools:
            kwargs["tools"] = tools

        def _apply(extra):
            k = {**kwargs, **extra}
            try:
                return tok.apply_chat_template(messages, enable_thinking=True, **k)
            except TypeError:
                # Template doesn't accept enable_thinking -> omit and retry.
                return tok.apply_chat_template(messages, **k)

        try:
            return _apply({}), False
        except ValueError:
            borrowed = _get_borrowed_template()
            if not borrowed:
                raise
            return _apply({"chat_template": borrowed}), True

    @app.post("/v1/chat/completions")
    def chat_completions(req: ChatRequest):
        messages = [
            {"role": m.role, "content": _content_to_text(m.content)}
            for m in req.messages
        ]
        tools = req.tools
        # Build the literal templated string (the exact tokenizer input).
        # borrowed_tmpl=True means the served (base) model had no chat_template
        # and we rendered with the instruct sibling's -- captured honestly below.
        templated, borrowed_tmpl = _template(messages, tools)
        prompt_ids = tok(templated, add_special_tokens=False)["input_ids"]

        # Build the log record up front and write it in `finally` so the
        # templated prompt is preserved even if generation raises. The
        # generated ids/text are filled in if generation succeeds.
        record: Dict[str, Any] = {
            "ts": time.time(),
            "which": which,
            "model_id": model_id,
            "has_tools": bool(tools),
            "borrowed_chat_template": borrowed_tmpl,
            "templated_prompt": templated,
            "prompt_ids": prompt_ids,
            "generated_ids": None,
            "response_text": "",
        }
        gen_ids: List[int] = []
        text = ""
        try:
            with torch.no_grad():
                inp = torch.tensor([prompt_ids], device=device)
                max_new = int(req.max_tokens) if req.max_tokens else MAX_NEW_TOKENS
                # Bound the shim's generation length regardless of what the
                # client requests, so a thinking-ON response stays captured but
                # quick.
                max_new = max(1, min(max_new, MAX_NEW_TOKENS_INSTRUCT))
                out = model.generate(
                    inp,
                    max_new_tokens=max_new,
                    do_sample=False,
                    pad_token_id=tok.pad_token_id
                    if tok.pad_token_id is not None
                    else tok.eos_token_id,
                    # Explicit stop-token set so <|im_end|> halts generation
                    # (model.config.eos is NOT <|im_end|>). See stop_ids().
                    eos_token_id=stop_ids(tok, model),
                )
            gen_ids = out[0].tolist()[len(prompt_ids) :]
            text = tok.decode(gen_ids, skip_special_tokens=True)
            record["generated_ids"] = gen_ids
            record["response_text"] = text
        finally:
            log_prompt(record)

        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model_id,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": text},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": len(prompt_ids),
                "completion_tokens": len(gen_ids),
                "total_tokens": len(prompt_ids) + len(gen_ids),
            },
        }

    return app


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--model",
        choices=["instruct", "base"],
        default=os.environ.get("TOKVIZ_SERVE_MODEL", "instruct"),
    )
    ap.add_argument("--port", type=int, default=SHIM_PORT)
    args = ap.parse_args()
    app = make_app(args.model)
    uvicorn.run(app, host=SHIM_HOST, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
