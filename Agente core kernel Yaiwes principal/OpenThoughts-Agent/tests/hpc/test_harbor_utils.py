from hpc.harbor_utils import merge_harbor_config


def test_merge_harbor_config_injects_templated_verifier_openai_key() -> None:
    config = {
        "agents": [{"name": "terminus-2", "model_name": "placeholder", "kwargs": {}}],
        "verifier": {"override_timeout_sec": 60},
    }

    merged = merge_harbor_config(
        config,
        agent_name="terminus-2",
        model_name="vllm/glm",
        n_concurrent=1,
        endpoint_meta=None,
        agent_kwarg_overrides=[],
    )

    assert merged["verifier"]["env"]["OPENAI_API_KEY"] == "${OPENAI_API_KEY}"
    assert "env" not in config["verifier"]


def test_merge_harbor_config_preserves_explicit_verifier_openai_key_template() -> None:
    config = {
        "agents": [{"name": "terminus-2", "model_name": "placeholder", "kwargs": {}}],
        "verifier": {"env": {"OPENAI_API_KEY": "${VERIFIER_OPENAI_API_KEY}"}},
    }

    merged = merge_harbor_config(
        config,
        agent_name="terminus-2",
        model_name="vllm/glm",
        n_concurrent=1,
        endpoint_meta=None,
        agent_kwarg_overrides=[],
    )

    assert merged["verifier"]["env"]["OPENAI_API_KEY"] == "${VERIFIER_OPENAI_API_KEY}"
