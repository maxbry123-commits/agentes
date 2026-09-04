"""run_chat.py -- the chat / non-agentic half (5 prompts, pure HF transformers).

For each of the 5 hardcoded prompts we produce TWO HTML files:

  chat_NN_instruct.html
      Instruct model. We build chat messages and apply the chat template with
      ``add_generation_prompt=True, tokenize=False`` to get the *literal*
      templated string (the exact thing the tokenizer turns into ids). We then
      tokenize that string and generate a response. The HTML shows the templated
      prompt + the generated continuation (dashed border).

  chat_NN_base.html
      Base model. It is treated as having NO chat template: we feed the raw user
      query as a plain completion prompt and generate. The HTML makes clear this
      is the base / no-template path.
"""

from __future__ import annotations

import sys

from config import (
    BASE_MODEL_ID,
    CHAT_PROMPTS,
    INSTRUCT_MODEL_ID,
    MAX_NEW_TOKENS_INSTRUCT,
    OUTPUT_DIR,
)
from model_utils import chat_templated_string, generate_from_ids, load
from render_tokens import render_to_html


def run_instruct(idx: int, prompt: str) -> str:
    tok, model, device = load(INSTRUCT_MODEL_ID)
    messages = [{"role": "user", "content": prompt}]
    # Literal templated string -- the exact tokenizer input.
    # enable_thinking=True -> the generation-prompt tail ends with an OPEN
    # <think>\n, so generation must be long enough to capture the reasoning
    # block plus the answer.
    templated = chat_templated_string(tok, messages)
    prompt_ids = tok(templated, add_special_tokens=False)["input_ids"]
    gen_ids = generate_from_ids(
        tok, model, device, prompt_ids, max_new_tokens=MAX_NEW_TOKENS_INSTRUCT
    )

    html = render_to_html(
        tok,
        model_id=INSTRUCT_MODEL_ID,
        setting_label=f"Chat #{idx:02d} — INSTRUCT (chat template applied, thinking ON)",
        prompt_ids=prompt_ids,
        generated_ids=gen_ids,
        extra_note=f"User query: {prompt!r}  |  apply_chat_template(add_generation_prompt=True, enable_thinking=True)",
    )
    out = OUTPUT_DIR / f"chat_{idx:02d}_instruct.html"
    out.write_text(html, encoding="utf-8")
    return str(out)


def run_base(idx: int, prompt: str) -> str:
    tok, model, device = load(BASE_MODEL_ID)
    # Base / no-template path: feed the raw query as a completion prompt.
    completion_prompt = prompt + "\n"
    prompt_ids = tok(completion_prompt, add_special_tokens=False)["input_ids"]
    gen_ids = generate_from_ids(tok, model, device, prompt_ids)

    html = render_to_html(
        tok,
        model_id=BASE_MODEL_ID,
        setting_label=f"Chat #{idx:02d} — BASE (NO chat template, raw completion)",
        prompt_ids=prompt_ids,
        generated_ids=gen_ids,
        extra_note=(
            f"User query fed raw (base model has no chat template here): {completion_prompt!r}. "
            "Base-model continuations may be free-form completion rather than a chat answer."
        ),
    )
    out = OUTPUT_DIR / f"chat_{idx:02d}_base.html"
    out.write_text(html, encoding="utf-8")
    return str(out)


def main() -> None:
    produced = []
    for i, prompt in enumerate(CHAT_PROMPTS, start=1):
        print(f"[chat {i:02d}/{len(CHAT_PROMPTS)}] instruct: {prompt!r}", flush=True)
        produced.append(run_instruct(i, prompt))
        print(f"[chat {i:02d}/{len(CHAT_PROMPTS)}] base", flush=True)
        produced.append(run_base(i, prompt))
    print("\nWrote:")
    for p in produced:
        print(" ", p)


if __name__ == "__main__":
    sys.exit(main())
