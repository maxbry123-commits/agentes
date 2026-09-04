"""Unit tests for the shared model-config registry loader/resolver.

Reshaped (2026-07-12) from the former self-contained script
`eval/tests/test_model_registry_resolve.py` into a pytest test — the assertion
logic is byte-for-byte the original `check(...)` conditions, now collected into
one pytest case that fails with the aggregated list of failed checks.

Validates `load_model_registry`'s behavior in isolation against a hand-written
fixture:
  * group expansion + per-model override (mirrors the legacy loader),
  * the 4-tier precedence exact+variant > exact > group > pattern,
  * shallow-merge variant semantics (variant replaces a named top-level key),
  * the G3 STRICT-SUPERSET property: a profile with NO matching variant resolves
    to the base entry byte-identical to the legacy exact/group/pattern result.

CI-safe: hermetic, no network/creds (patches out the base-model resolver).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

# unified_eval_listener reads DCFT at import; point it at the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("DCFT", str(_REPO_ROOT))

import eval.unified_eval_listener as uel  # noqa: E402


_FIXTURE = """
groups:
  - models:
      - "org/group-a"
      - "org/group-b"
    tensor_parallel_size: 2
    max_model_len: 32768
    extra_args: "--enable-prefix-caching"

models:
  # exact override on top of a group member (override wins)
  "org/group-a":
    trust_remote_code: true
  # plain exact entry with a variant block
  "org/has-variant":
    tensor_parallel_size: 2
    max_model_len: 32768
    trust_remote_code: true
    agent_kwargs:
      - 'extra_body={"chat_template_kwargs":{"enable_thinking":true}}'
    variants:
      gh200:
        tensor_parallel_size: 1
        max_model_len: 65536
  # exact entry, NO variants (superset control)
  "org/no-variant":
    tensor_parallel_size: 2
    conda_env: some-env
  # base entry that ALSO has a gh200 STANDALONE override (Option 4): the base carries
  # intrinsic fields the gh200 recipe deliberately DROPS (tool_call_parser), which a variant
  # could not express. The standalone wins wholesale on gh200, no merge.
  "org/has-standalone":
    tensor_parallel_size: 2
    tool_call_parser: hermes
    reasoning_parser: qwen3
    trust_remote_code: true
    extra_args: "--enable-prefix-caching"
  "org/has-standalone@gh200":
    tensor_parallel_size: 1
    trust_remote_code: true
    extra_args: "--enable-prefix-caching"
  # standalone for a DIFFERENT profile only — must be ignored when active profile != that.
  "org/other-only@some-other-profile":
    tensor_parallel_size: 8
  # max_output_tokens forwarding: a model that PINS a serve-output-token budget. Absent on every
  # other entry -> EVAL_MAX_OUTPUT_TOKENS unset (sbatch :-16384 default). A variant may pin it too.
  "org/pinned-budget":
    tensor_parallel_size: 2
    max_output_tokens: 32768
    variants:
      gh200:
        max_output_tokens: 8192

patterns:
  - match: "(?i)32[Bb]"
    trust_remote_code: true
    tensor_parallel_size: 4
    extra_args: "--enable-prefix-caching"
  # profile-scoped pattern: only active on gh200 (forces TP=1 for any 70B-ish name there).
  - match: "(?i)70[Bb]"
    profiles: [gh200]
    trust_remote_code: true
    tensor_parallel_size: 1
  - match: ".*"
    trust_remote_code: true
    tensor_parallel_size: 1
"""


def _load(profile):
    """Fresh load of the fixture under a given hardware_profile (resets the memo globals)."""
    uel._BASELINE_MODEL_CONFIGS = None
    uel._BASELINE_MODEL_PATTERNS = None
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write(_FIXTURE)
        path = f.name
    try:
        configs = uel.load_model_registry(path, hardware_profile=profile)
        patterns = uel._BASELINE_MODEL_PATTERNS
    finally:
        os.unlink(path)
    return configs, patterns


def test_model_registry_resolve(monkeypatch):
    # This test mutates module-level globals on unified_eval_listener (the loader's
    # memo caches, the cluster shape, and the base-model resolver). As a standalone
    # script that was harmless; in-process under pytest it would LEAK into sibling
    # tests (e.g. test_vllm_parallelism_sizing). Register the current values with
    # monkeypatch so they are restored at teardown regardless of the direct
    # reassignments below.
    for _attr in (
        "_CLUSTER_CONFIG",
        "resolve_base_model_name",
        "_BASELINE_MODEL_CONFIGS",
        "_BASELINE_MODEL_PATTERNS",
    ):
        monkeypatch.setattr(uel, _attr, getattr(uel, _attr, None), raising=False)

    failures = []

    def check(name, cond, detail=""):
        if not cond:
            failures.append(f"{name}: {detail}")

    # --- profile=None (no variant active): base entries, superset property ---
    cfg, pats = _load(None)

    # group expansion: group-b gets the group config verbatim
    check(
        "group expansion: group-b inherits group config",
        cfg["org/group-b"]
        == {
            "tensor_parallel_size": 2,
            "max_model_len": 32768,
            "extra_args": "--enable-prefix-caching",
        },
        repr(cfg.get("org/group-b")),
    )

    # per-model override merges on top of the group (override wins; group fields preserved)
    check(
        "override-on-group: group-a keeps group fields + adds trust_remote_code",
        cfg["org/group-a"]
        == {
            "tensor_parallel_size": 2,
            "max_model_len": 32768,
            "extra_args": "--enable-prefix-caching",
            "trust_remote_code": True,
        },
        repr(cfg.get("org/group-a")),
    )

    # superset: a model WITH a variant block, but profile=None -> base entry, variants STRIPPED
    check(
        "superset (profile=None): has-variant is the base entry, no `variants` key",
        cfg["org/has-variant"]
        == {
            "tensor_parallel_size": 2,
            "max_model_len": 32768,
            "trust_remote_code": True,
            "agent_kwargs": [
                'extra_body={"chat_template_kwargs":{"enable_thinking":true}}'
            ],
        }
        and "variants" not in cfg["org/has-variant"],
        repr(cfg.get("org/has-variant")),
    )

    # no-variant entry unchanged
    check(
        "no-variant entry passes through unchanged",
        cfg["org/no-variant"] == {"tensor_parallel_size": 2, "conda_env": "some-env"},
        repr(cfg.get("org/no-variant")),
    )

    # patterns preserved in order, variants stripped
    check(
        "patterns: order preserved + 2 entries",
        [p.get("match") for p in pats] == ["(?i)32[Bb]", ".*"],
        repr(pats),
    )
    check(
        "patterns: no `variants` key leaks through",
        all("variants" not in p for p in pats),
    )

    # --- profile=gh200 (variant active): shallow-merge over base ---
    cfg_g, _ = _load("gh200")
    check(
        "variant active: has-variant TP overridden to 1 (variant wins per-field)",
        cfg_g["org/has-variant"]["tensor_parallel_size"] == 1,
        repr(cfg_g["org/has-variant"]),
    )
    check(
        "variant active: has-variant max_model_len overridden to 65536",
        cfg_g["org/has-variant"]["max_model_len"] == 65536,
        repr(cfg_g["org/has-variant"]),
    )
    check(
        "variant active: base intrinsic fields PRESERVED (trust_remote_code, agent_kwargs)",
        cfg_g["org/has-variant"].get("trust_remote_code") is True
        and cfg_g["org/has-variant"].get("agent_kwargs")
        == ['extra_body={"chat_template_kwargs":{"enable_thinking":true}}'],
        repr(cfg_g["org/has-variant"]),
    )
    # Profile-inheritance rule: a base entry with NO variant for the active (non-default)
    # profile is NOT exposed on that profile (it falls to that profile's standalone / patterns /
    # size-default). On the default profile it WOULD be present (asserted under profile=None above).
    check(
        "non-default profile: a base entry without a matching variant is NOT inherited",
        "org/no-variant" not in cfg_g,
        repr(list(cfg_g.keys())),
    )
    check(
        "default profile DOES expose that same base entry (sharing baseline)",
        cfg["org/no-variant"] == {"tensor_parallel_size": 2, "conda_env": "some-env"},
        repr(cfg.get("org/no-variant")),
    )

    # --- 4-tier precedence via the real resolvers on the merged dict ---
    # set a cluster shape so get_vllm_env_overrides has gpus_per_node
    uel._CLUSTER_CONFIG = {"hardware": {"gpus_per_node": 8}}
    uel.resolve_base_model_name = lambda m: None  # hermetic
    uel._BASE_MODEL_NAME_CACHE.clear()

    cfg_n, _ = _load(None)
    # exact wins over pattern: has-variant resolves to its exact TP (2), not the 32B pattern
    env_exact = uel.get_vllm_env_overrides("org/has-variant", cfg_n)
    check(
        "precedence: exact entry wins over pattern",
        env_exact["EVAL_VLLM_TENSOR_PARALLEL_SIZE"] == "2",
        repr(env_exact),
    )
    # pattern tier: an UNLISTED 32B name hits the (?i)32[Bb] pattern (TP 4)
    env_pat = uel.get_vllm_env_overrides("unlisted/Foo-32B", cfg_n)
    check(
        "precedence: unlisted 32B name hits the 32B pattern (TP=4)",
        env_pat["EVAL_VLLM_TENSOR_PARALLEL_SIZE"] == "4",
        repr(env_pat),
    )
    # catch-all .*: an unlisted small name hits the .* pattern (TP 1)
    env_catch = uel.get_vllm_env_overrides("unlisted/tiny", cfg_n)
    check(
        "precedence: unlisted small name hits the .* catch-all (TP=1)",
        env_catch["EVAL_VLLM_TENSOR_PARALLEL_SIZE"] == "1",
        repr(env_catch),
    )

    # exact+variant wins over exact: under gh200, has-variant resolves to TP 1
    cfg_gv, _ = _load("gh200")
    env_var = uel.get_vllm_env_overrides("org/has-variant", cfg_gv)
    check(
        "precedence: exact+variant wins (gh200 -> TP=1, max_model_len 65536)",
        env_var["EVAL_VLLM_TENSOR_PARALLEL_SIZE"] == "1"
        and env_var.get("EVAL_VLLM_MAX_MODEL_LEN") == "65536",
        repr(env_var),
    )

    # --- Option-4 STANDALONE name@profile (NO inheritance) ---
    # profile=None: the bare base entry resolves; the @gh200 standalone is NOT active and the
    # suffixed key is NOT exposed.
    cfg_n2, _ = _load(None)
    check(
        "standalone inactive (profile=None): bare base entry resolves with its intrinsics",
        cfg_n2["org/has-standalone"].get("tool_call_parser") == "hermes"
        and cfg_n2["org/has-standalone"].get("reasoning_parser") == "qwen3"
        and cfg_n2["org/has-standalone"]["tensor_parallel_size"] == 2,
        repr(cfg_n2.get("org/has-standalone")),
    )
    check(
        "standalone key never exposed as a bare lookup (no '@' keys in resolved dict)",
        not any("@" in k for k in cfg_n2),
        repr([k for k in cfg_n2 if "@" in k]),
    )

    # profile=gh200: the @gh200 standalone REPLACES the bare entry wholesale — the base
    # intrinsics (tool_call_parser, reasoning_parser) are DROPPED (NOT merged in).
    cfg_g2, _ = _load("gh200")
    sa = cfg_g2["org/has-standalone"]
    check(
        "standalone active (gh200): replaces wholesale, TP=1",
        sa["tensor_parallel_size"] == 1,
        repr(sa),
    )
    check(
        "standalone active (gh200): base intrinsics DROPPED (no tool_call_parser/reasoning_parser)",
        "tool_call_parser" not in sa and "reasoning_parser" not in sa,
        repr(sa),
    )
    env_sa = uel.get_vllm_env_overrides("org/has-standalone", cfg_g2)
    check(
        "standalone active (gh200): resolved env has NO parser keys (the un-mergeable removal)",
        "EVAL_VLLM_TOOL_CALL_PARSER" not in env_sa
        and "EVAL_VLLM_REASONING_PARSER" not in env_sa,
        repr(env_sa),
    )
    check(
        "standalone for a non-active profile is ignored (org/other-only absent on gh200)",
        "org/other-only" not in cfg_g2
        and "org/other-only@some-other-profile" not in cfg_g2,
        repr([k for k in cfg_g2 if "other" in k]),
    )

    # --- profile-scoped patterns ---
    # the (?i)70[Bb] pattern is profiles:[gh200] only.
    _, pats_n = _load(None)
    _, pats_g = _load("gh200")
    check(
        "profile-scoped pattern absent off-profile (no 70B pattern under default)",
        not any(p.get("match") == "(?i)70[Bb]" for p in pats_n),
        repr([p.get("match") for p in pats_n]),
    )
    check(
        "profile-scoped pattern present on-profile (70B pattern under gh200)",
        any(p.get("match") == "(?i)70[Bb]" for p in pats_g),
        repr([p.get("match") for p in pats_g]),
    )
    check(
        "profiles filter key stripped from stored patterns",
        all("profiles" not in p for p in pats_g),
    )
    # behavioral: an unlisted 70B name resolves TP=1 under gh200 (its pattern), but falls to the
    # .* catch-all (also TP=1 here) under default — assert the 70B pattern actually fires on gh200.
    uel._CLUSTER_CONFIG = {"hardware": {"gpus_per_node": 1}}
    cfg_g3, _ = _load("gh200")
    env_70 = uel.get_vllm_env_overrides("unlisted/Foo-70B", cfg_g3)
    check(
        "profile-scoped pattern fires (gh200, 70B name -> TP=1 from its pattern)",
        env_70["EVAL_VLLM_TENSOR_PARALLEL_SIZE"] == "1",
        repr(env_70),
    )

    # --- max_output_tokens forwarding (Stage-4) ---
    # ABSENT on a normal entry -> EVAL_MAX_OUTPUT_TOKENS NOT set (sbatch :-16384 default applies).
    uel._CLUSTER_CONFIG = {"hardware": {"gpus_per_node": 8}}
    cfg_mot, _ = _load(None)
    env_absent = uel.get_vllm_env_overrides("org/no-variant", cfg_mot)
    check(
        "max_output_tokens absent -> EVAL_MAX_OUTPUT_TOKENS NOT set (sbatch default)",
        "EVAL_MAX_OUTPUT_TOKENS" not in env_absent,
        repr(env_absent),
    )
    # SET on the entry -> forwarded as EVAL_MAX_OUTPUT_TOKENS=<v> (mirrors max_model_len).
    env_set = uel.get_vllm_env_overrides("org/pinned-budget", cfg_mot)
    check(
        "max_output_tokens set -> EVAL_MAX_OUTPUT_TOKENS=32768",
        env_set.get("EVAL_MAX_OUTPUT_TOKENS") == "32768",
        repr(env_set),
    )
    # A variant may PIN a different budget; the active gh200 variant wins per-field.
    cfg_mot_g, _ = _load("gh200")
    env_var_set = uel.get_vllm_env_overrides("org/pinned-budget", cfg_mot_g)
    check(
        "max_output_tokens variant override -> EVAL_MAX_OUTPUT_TOKENS=8192 (gh200)",
        env_var_set.get("EVAL_MAX_OUTPUT_TOKENS") == "8192",
        repr(env_var_set),
    )

    assert not failures, "registry-resolve checks failed:\n" + "\n".join(failures)
