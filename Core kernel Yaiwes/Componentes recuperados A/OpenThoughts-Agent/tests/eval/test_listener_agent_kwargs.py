"""Regression: the SLURM eval listener delivers agent kwargs (incl. thinking)
via the generic ``EVAL_AGENT_KWARGS`` env — a newline-separated list the sbatch
splits into one ``--agent-kwarg`` each — never the removed ``EVAL_ENABLE_THINKING``
env / ``--enable-thinking`` flag.

The sbatch (``eval/{jupiter,leonardo,tacc}/eval_harbor.sbatch``) reads
``EVAL_AGENT_KWARGS`` and re-emits each line as ``--agent-kwarg <line>``, so the
exact newline-joined serialization here IS the cross-process contract.
"""

from eval.unified_eval_listener import SbatchParams

NESTED = 'extra_body={"chat_template_kwargs":{"enable_thinking":true}}'


def test_to_env_serializes_agent_kwargs_newline_joined():
    env = SbatchParams(agent_kwargs=[NESTED, "parser=xml"]).to_env()
    assert env["EVAL_AGENT_KWARGS"] == f"{NESTED}\nparser=xml"
    # The removed flag env must never reappear.
    assert "EVAL_ENABLE_THINKING" not in env


def test_to_env_empty_agent_kwargs_is_empty_string():
    env = SbatchParams().to_env()
    assert env["EVAL_AGENT_KWARGS"] == ""
    assert "EVAL_ENABLE_THINKING" not in env


def test_sbatchparams_has_no_enable_thinking_attr():
    # The dedicated thinking field is gone; everything rides through agent_kwargs.
    assert not hasattr(SbatchParams(), "enable_thinking")
    assert SbatchParams().agent_kwargs == []
