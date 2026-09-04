"""Shared HF model/tokenizer loading + generation helpers (otagent env)."""

from __future__ import annotations

import functools
from typing import Dict, List, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from config import DO_SAMPLE, MAX_NEW_TOKENS, pick_device


# Turn-/sequence-ending special-token strings across model families. A model
# only has a few of these; we keep whichever resolve to a real (non-unk) id.
#   Qwen3.5 : <|im_end|>, <|endoftext|>
#   Gemma 4 : <turn|> (end-of-turn), <eos>      (also <end_of_turn> on Gemma 2/3)
#   Llama 3 : <|eot_id|>, <|end_of_text|>
_TURN_END_STRINGS = (
    "<|im_end|>",
    "<|endoftext|>",
    "<turn|>",
    "<end_of_turn>",
    "<eos>",
    "<|eot_id|>",
    "<|end_of_text|>",
)


def stop_ids(tok, model=None) -> List[int] | None:
    """Build a model-agnostic stop-token-id SET for ``generate(eos_token_id=...)``.

    ``model.generate()`` derives its stop token from the *generation-config /
    model.config* eos, NOT from ``tokenizer.eos_token_id``. The set is built
    so it works for ANY model, never narrower than what the model itself
    intends:
      * the tokenizer's own ``eos_token_id``;
      * any known cross-family turn-/sequence-end special string that resolves to
        a real (non-unk) id (Qwen ``<|im_end|>``, Gemma ``<turn|>``, Llama
        ``<|eot_id|>``, ...);
      * the model's authoritative ``generation_config.eos_token_id`` (int or list)
        when a model is supplied -- e.g. Gemma 4 ships ``[1, 106, 50]`` where 106
        is ``<turn|>``.
    Missing/unk ids are filtered, duplicates removed.
    """
    ids = set()
    if tok.eos_token_id is not None:
        ids.add(tok.eos_token_id)
    for t in _TURN_END_STRINGS:
        i = tok.convert_tokens_to_ids(t)
        if isinstance(i, int) and i >= 0 and i != tok.unk_token_id:
            ids.add(i)
    gc = getattr(model, "generation_config", None) if model is not None else None
    if gc is not None and gc.eos_token_id is not None:
        e = gc.eos_token_id
        ids.update(e if isinstance(e, (list, tuple)) else [e])
    return sorted(ids) or None


@functools.lru_cache(maxsize=4)
def load(model_id: str) -> Tuple[object, object, str]:
    """Load (tokenizer, model, device) for a model id, cached per process."""
    device = pick_device()
    tok = AutoTokenizer.from_pretrained(model_id)
    dtype = torch.float16 if device == "mps" else torch.float32
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=dtype)
    model.to(device)
    model.eval()
    return tok, model, device


@torch.no_grad()
def generate_from_ids(
    tok, model, device, input_ids: List[int], max_new_tokens: int = MAX_NEW_TOKENS
) -> List[int]:
    """Greedy-generate from a list of input ids; return ONLY the new ids."""
    inp = torch.tensor([input_ids], device=device)
    out = model.generate(
        inp,
        max_new_tokens=max_new_tokens,
        do_sample=DO_SAMPLE,
        pad_token_id=tok.pad_token_id
        if tok.pad_token_id is not None
        else tok.eos_token_id,
        # Explicit, model-agnostic stop-token set so the model's turn-end token
        # halts generation. Folds in model.generation_config.eos so we're never
        # narrower than the model intends. See stop_ids().
        eos_token_id=stop_ids(tok, model),
    )
    return out[0].tolist()[len(input_ids) :]


def chat_templated_string(tok, messages: List[Dict[str, str]]) -> str:
    """Return the literal string apply_chat_template feeds the model.

    ``enable_thinking=True`` flips Qwen3.5's chat template from its default
    thinking-OFF behaviour (an empty, pre-closed ``<think>\\n\\n</think>``
    block) to thinking-ON: the generation-prompt tail ends with an OPEN
    ``<think>\\n`` so the model actually generates reasoning before its answer.
    Used for the instruct model. (The base chat half feeds a raw completion and
    never calls this.)

    ``enable_thinking`` is model-specific. Templates that don't accept the kwarg
    (older / non-Qwen families) raise ``TypeError``; we fall back to a plain
    templating call so the toolkit works for any instruct model (e.g. Gemma).
    """
    base = dict(add_generation_prompt=True, tokenize=False)
    try:
        return tok.apply_chat_template(messages, enable_thinking=True, **base)
    except TypeError:
        return tok.apply_chat_template(messages, **base)
