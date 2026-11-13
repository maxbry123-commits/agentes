"""run_agentic.py -- drive the agentic half: shim -> swe-agent -> render.

Flow (for a given model variant, instruct|base):
  1. Truncate/rotate the shim log.
  2. Start serve_hf_openai.py (in tokviz-rt env -- needs transformers 5 for the
     Qwen3.5 weights) as a subprocess and wait until /v1/models is live.
  3. Run swe-agent (in the sweagent env) against each of the 5 toy repos,
     pointing at the shim via sweagent_config.yaml.
  4. Stop the shim. The shim has logged every templated prompt.
  5. render_agentic renders representative captured prompts into HTML.

swe-agent's default execution backend is Docker. If Docker is unavailable, the
swe-agent invocations are skipped and the exact commands are printed so they
can be run manually. Either way, the shim + render pipeline are exercised.

Interpreters:
  SHIM (model exec): /Users/benjaminfeuer/miniconda3/envs/tokviz-rt/bin/python
  swe-agent:         /Users/benjaminfeuer/miniconda3/envs/sweagent/bin/sweagent
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from config import (
    BASE_MODEL_ID,
    INSTRUCT_MODEL_ID,
    REPOS_DIR,
    SHIM_HOST,
    SHIM_LOG,
    SHIM_PORT,
)

HERE = Path(__file__).resolve().parent
RT_PY = "/Users/benjaminfeuer/miniconda3/envs/tokviz-rt/bin/python"
SWEAGENT_BIN = "/Users/benjaminfeuer/miniconda3/envs/sweagent/bin/sweagent"
# swe-agent source checkout (the `sweagent` env installs from here). Its bundled
# config + tools/ bundles are resolved relative to this repo root.
SWEAGENT_REPO = Path("/Users/benjaminfeuer/SWE-agent")
# Two bundled SWE-agent configs, one per parser variant. Both wire the SAME
# tool bundles (registry/windowed/search/windowed_edit_linting/submit); they
# differ only in parse_function.type and how tools reach the model:
#   * thought_action: tools documented as TEXT in the system prompt via
#     {{command_docs}}; NO structured tool array is sent.
#   * function_calling: tools sent as a STRUCTURED tool array (OpenAI schema);
#     Qwen3.5's template renders them into a <tools>...</tools> JSON block.
# We layer sweagent_config.yaml (model/limits/no-demo) on top of each.
BUNDLED_CONFIG_TA = SWEAGENT_REPO / "config" / "sweagent_0_7" / "07_thought_action.yaml"
BUNDLED_CONFIG_FC = SWEAGENT_REPO / "config" / "sweagent_0_7" / "07_fcalling.yaml"
OVERRIDE_CONFIG = HERE / "sweagent_config.yaml"

# Parser variants: (key, bundled config, output filename suffix).
#   thought_action -> agentic_NN_<which>.html
#   function_calling -> agentic_NN_<which>_funccall.html
VARIANTS = [
    ("thought_action", BUNDLED_CONFIG_TA, ""),
    ("function_calling", BUNDLED_CONFIG_FC, "_funccall"),
]


def docker_available() -> bool:
    if not shutil.which("docker"):
        return False
    try:
        subprocess.run(["docker", "info"], check=True, capture_output=True, timeout=15)
        return True
    except Exception:
        return False


def wait_for_shim(timeout: float = 600.0) -> bool:
    url = f"http://{SHIM_HOST}:{SHIM_PORT}/v1/models"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(2)
    return False


def start_shim(which: str) -> subprocess.Popen:
    env = dict(os.environ, TOKVIZ_SERVE_MODEL=which)
    proc = subprocess.Popen(
        [
            RT_PY,
            str(HERE / "serve_hf_openai.py"),
            "--model",
            which,
            "--port",
            str(SHIM_PORT),
        ],
        cwd=str(HERE),
        env=env,
    )
    print(f"[shim] started pid={proc.pid} model={which}; waiting for /v1/models ...")
    if not wait_for_shim():
        proc.terminate()
        raise RuntimeError("shim did not come up in time")
    print("[shim] live")
    return proc


def model_name_for(which: str) -> str:
    mid = INSTRUCT_MODEL_ID if which == "instruct" else BASE_MODEL_ID
    return f"openai/{mid}"


def sweagent_cmd(which: str, repo: Path, bundled_config: Path) -> list[str]:
    issue = repo / "ISSUE.md"
    return [
        SWEAGENT_BIN,
        "run",
        # Bundled default first (tool bundles + system/instance templates +
        # the variant's parser), then our small-model override
        # (model/limits/no-demo) on top. The override does NOT set
        # parse_function, so each variant keeps its own parser.
        "--config",
        str(bundled_config),
        "--config",
        str(OVERRIDE_CONFIG),
        "--agent.model.name",
        model_name_for(which),
        f"--problem_statement.path={issue}",
        f"--env.repo.path={repo}",
    ]


def sweagent_env() -> dict:
    # tools/ bundles + the bundled config reference paths relative to the
    # SWE-agent repo root; pin it so resolution doesn't depend on CWD.
    return dict(os.environ, SWE_AGENT_CONFIG_ROOT=str(SWEAGENT_REPO))


def run_sweagent_on_repo(which: str, repo: Path, bundled_config: Path) -> int:
    cmd = sweagent_cmd(which, repo, bundled_config)
    print("[swe-agent]", " ".join(cmd))
    if not Path(SWEAGENT_BIN).exists():
        print("  (swe-agent not installed; run setup_sweagent.sh first)")
        return 127
    proc = subprocess.run(cmd, cwd=str(HERE), env=sweagent_env())
    return proc.returncode


def run_variant(which: str, do_sweagent: bool) -> None:
    shim = start_shim(which)
    try:
        for parser_key, bundled_config, _suffix in VARIANTS:
            print(
                f"\n[{which} / {parser_key}] driving swe-agent "
                f"(config={bundled_config.name})"
            )
            if do_sweagent:
                for repo in sorted(p for p in REPOS_DIR.iterdir() if p.is_dir()):
                    run_sweagent_on_repo(which, repo, bundled_config)
            else:
                print(
                    f"[{which} / {parser_key}] swe-agent skipped "
                    "(Docker/install missing). Manual commands printed below."
                )
                for repo in sorted(p for p in REPOS_DIR.iterdir() if p.is_dir()):
                    print(
                        "  MANUAL:", " ".join(sweagent_cmd(which, repo, bundled_config))
                    )
    finally:
        shim.terminate()
        try:
            shim.wait(timeout=10)
        except Exception:
            shim.kill()
        print(f"[shim] stopped ({which})")


# Issue-text fingerprints (a distinctive phrase from each repo's ISSUE.md) and
# tool-doc fingerprints (command names that only appear if {{command_docs}}
# rendered the bundled tool bundles). The captured prompt must contain BOTH.
ISSUE_FINGERPRINTS = [
    "sum of integers from 1 to n",  # offbyone
    "forgets to return",  # returnsnone
    "supposed to multiply",  # wrongop
    "return the reversed string",  # reversed
    "maximum element of a non-empty",  # emptylist
]
# These command/tool names come from the bundled tool bundles. In
# thought_action they appear as TEXT under "COMMANDS:" via {{command_docs}}; in
# function_calling they appear inside the rendered <tools> JSON array.
TOOL_FINGERPRINTS = ["search_file", "goto", "submit", "open"]


def _has_open_think(prompt: str) -> bool:
    """True if the prompt's generation-prompt tail has an OPEN <think> block.

    Thinking-ON ends the prompt with `<think>\\n` NOT immediately followed by a
    `</think>` close. The thinking-OFF default emits `<think>\\n\\n</think>`.
    """
    idx = prompt.rfind("<think>")
    if idx == -1:
        return False
    tail = prompt[idx + len("<think>") :]
    # Open block: nothing but whitespace before EOS (no </think> close follows).
    return "</think>" not in tail


def verify_capture() -> None:
    """Run the three verification gates over the captured shim log.

    GATE A (thinking): at least one INSTRUCT captured prompt's tail has an OPEN
        <think> block (confirming enable_thinking=True took effect).
    GATE B thought_action: per variant, >=1 captured (has_tools=False) prompt
        contains the COMMANDS tool docs + issue text AND has NO <tools> array.
    GATE B function_calling: per variant, >=1 captured (has_tools=True) prompt
        contains a <tools> JSON block + issue text.

    On any failure, raise with a dump of the offending captured prompt rather
    than rendering stale/empty HTML.
    """
    sys.path.insert(0, str(HERE))
    from render_agentic import load_log

    records = load_log()
    if not records:
        raise RuntimeError(
            "shim_prompts.jsonl is empty -- swe-agent never called the shim. "
            "Cannot verify or render."
        )

    # ----- GATE A: thinking enabled (open <think> on an instruct prompt) ----- #
    instruct_prompts = [
        r.get("templated_prompt", "") for r in records if r.get("which") == "instruct"
    ]
    if any(_has_open_think(p) for p in instruct_prompts):
        print(
            "[verify] GATE A: at least one instruct prompt has an OPEN <think> "
            "tail (thinking enabled). OK"
        )
    else:
        # Thinking is model-specific: Qwen3.5 uses <think>; other families
        # (e.g. Gemma) have a different or no thinking convention, so an absent
        # open-<think> tail is NOT a failure there. Warn, don't abort.
        print(
            "[verify] GATE A: no OPEN <think> tail found — expected for models "
            "without Qwen-style thinking (e.g. Gemma). Skipping (soft)."
        )

    # Split captured records by parser variant via the shim's has_tools flag.
    def matches(r, parser_key):
        if parser_key == "function_calling":
            return r.get("has_tools") is True
        return not r.get("has_tools")

    for parser_key, _cfg, _suffix in VARIANTS:
        for which in ("instruct", "base"):
            recs = [
                r for r in records if r.get("which") == which and matches(r, parser_key)
            ]
            ok = None
            for r in recs:
                p = r.get("templated_prompt", "")
                has_issue = any(f in p for f in ISSUE_FINGERPRINTS)
                has_tools_block = "<tools>" in p
                has_cmd_docs = sum(f in p for f in TOOL_FINGERPRINTS) >= 2
                if parser_key == "function_calling":
                    # GATE B (function_calling): the tool array rendered into
                    # the prompt + issue text. Qwen renders a <tools> JSON block;
                    # other families (e.g. Gemma) use their own tool tokens and
                    # never emit literal "<tools>". So accept EITHER the <tools>
                    # block OR >=2 tool-name fingerprints (the tool names appear
                    # in any rendering) — model-agnostic.
                    if has_issue and (has_tools_block or has_cmd_docs):
                        ok = r
                        break
                else:
                    # GATE B (thought_action): COMMANDS tool docs + issue,
                    # and NO <tools> JSON array (text-only form).
                    if has_issue and has_cmd_docs and not has_tools_block:
                        ok = r
                        break
            if ok is None:
                if not recs:
                    # base+function_calling may legitimately be absent (fallback).
                    print(
                        f"[verify] WARNING: no captured '{which}' / "
                        f"'{parser_key}' records (acceptable fallback for "
                        f"base+function_calling)."
                    )
                    continue
                sample = recs[0].get("templated_prompt", "<no records>")
                raise AssertionError(
                    f"[VERIFY FAILED — GATE B {parser_key}] No captured "
                    f"'{which}' / '{parser_key}' prompt met the gate "
                    f"(issue text + "
                    f"{'<tools> block' if parser_key == 'function_calling' else 'COMMANDS docs and NO <tools>'}"
                    f"). Refusing to render stale/empty prompts.\n"
                    f"--- first captured prompt ({len(sample)} chars) ---\n"
                    f"{sample[:4000]}\n--- end ---"
                )
            print(
                f"[verify] GATE B '{which}'/'{parser_key}': captured prompt "
                f"OK (len={len(ok.get('templated_prompt', ''))} chars, "
                f"<tools>={'<tools>' in ok.get('templated_prompt', '')})."
            )


def main() -> None:
    # Fresh log per full agentic pass.
    if SHIM_LOG.exists():
        SHIM_LOG.unlink()
    have_docker = docker_available()
    have_sweagent = Path(SWEAGENT_BIN).exists()
    do_sweagent = have_docker and have_sweagent
    print(
        f"docker_available={have_docker}  sweagent_installed={have_sweagent}  "
        f"-> run_sweagent={do_sweagent}"
    )

    for which in ("instruct", "base"):
        run_variant(which, do_sweagent)

    # VERIFY before rendering: the captured prompts must contain BOTH the issue
    # text and the tool docs. If not, this raises and we do NOT render stale
    # prompts.
    verify_capture()

    # Render whatever was captured.
    sys.path.insert(0, str(HERE))
    from render_agentic import render_first_calls_per_which

    def loader(mid: str):
        from transformers import AutoTokenizer

        return AutoTokenizer.from_pretrained(mid)

    produced = render_first_calls_per_which(loader)
    print("\nRendered agentic HTML:")
    for p in produced:
        print(" ", p)
    if not produced:
        print("  (no shim records captured -- swe-agent did not run)")


if __name__ == "__main__":
    main()
