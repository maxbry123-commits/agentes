"""Teacher Hint PRM — calls a teacher LLM to inject hints into the student's conversation."""

from __future__ import annotations

import logging
from typing import Any, Callable

from prm.base import ProcessRewardModel, register_prm

logger = logging.getLogger(__name__)

_DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful teaching assistant. A student is working on a software engineering "
    "task inside a sandboxed terminal environment. The student appears to be struggling. "
    "Your job is to provide a single, concise hint that helps the student make progress "
    "without giving away the full solution. Focus on the most impactful next step.\n\n"
    "STRICT OUTPUT CONSTRAINTS (a hint that violates these is worse than no hint):\n"
    "- Your response is hard-capped at 2048 tokens by the inference engine. Stay well "
    "under this — aim for 1-3 sentences plus at most one short code snippet.\n"
    "- The student already has the full chat history (task instructions, prior commands, "
    "file contents, error messages, their own thoughts). Do NOT restate or summarize "
    "anything they can already see. Jump straight to the new information or course "
    "correction.\n"
    "- If you must show code, use only minimal snippets (a few lines, not whole files) "
    "wrapped in fenced code blocks. Reference filenames and line numbers when applicable "
    "instead of pasting large regions.\n"
    "- Do not narrate your reasoning, do not say 'I see that...', do not apologize, do "
    "not preface. Open with the hint itself."
)

_DEFAULT_USER_PROMPT_TEMPLATE = (
    "## Task Instruction\n"
    "{task_instruction}\n\n"
    "## Recent Activity (last {k} exchanges)\n"
    "{recent_turns}\n\n"
    "Based on the student's recent activity, provide ONE concise hint (1-3 sentences) "
    "to help them make progress. Do NOT give the full solution."
)


@register_prm
class TeacherHint(ProcessRewardModel):
    """PRM that calls a teacher LLM to provide hints to a struggling student agent.

    Instead of terminating the agent (like ThrashingDetector), this PRM
    inspects the last ``k`` message pairs every ``check_interval`` turns and
    asks a teacher model for a concise hint.  The hint is injected into the
    student's next observation via the ``str`` return path of the turn
    callback.

    Constructor kwargs (all from YAML config):
        engine_type: Engine backend — ``"openai"``, ``"anthropic"``,
            ``"vllm_local"``, ``"google_gemini"``, ``"none"``.
        engine_kwargs: Dict passed to ``create_inference_engine()``.
        check_interval: Run the teacher every *N* turns.
        min_turns: Don't hint before this turn number.
        k: Number of recent message pairs to show the teacher.
        teacher_system_prompt: Custom system prompt (has sensible default).
        teacher_user_prompt_template: Custom user prompt template with
            ``{task_instruction}``, ``{recent_turns}``, ``{k}`` placeholders.
        max_hint_tokens: ``max_tokens`` passed to the teacher engine.
        hint_prefix / hint_suffix: Wrapping around the raw hint text.
    """

    def __init__(
        self,
        engine_type: str = "openai",
        engine_kwargs: dict[str, Any] | None = None,
        check_interval: int = 5,
        min_turns: int = 3,
        k: int = 6,
        teacher_system_prompt: str | None = None,
        teacher_user_prompt_template: str | None = None,
        # max_hint_tokens reset to 2048 (2026-05-21): job 53102590
        # (maxgn09_hint) produced 1,412 context-overflow errors in 8h
        # because the teacher's 16384-token headroom let it write
        # multi-page hints that pushed the student's next prompt past
        # the 32K model_len cap. With the updated system prompt
        # (concise mandate + 'student has chat history' anchor), the
        # teacher should fit comfortably under 2048 tokens.
        max_hint_tokens: int = 2048,
        # Per-message content cap quadrupled 2000 → 8000 chars in
        # _format_recent_turns (2026-05-18): long-trajectory trials
        # routinely had message bodies > 2000 chars (stack traces, file
        # diffs, JSON envelopes), which the prior truncation chopped before
        # the teacher could see the actual error context.
        recent_turn_content_cap: int = 8000,
        # Task instruction cap quadrupled 4000 → 16000 chars in
        # _extract_task_instruction (2026-05-18): same motivation —
        # multi-paragraph SWE-bench-style problem statements were being
        # cut off mid-spec.
        task_instruction_cap: int = 16000,
        hint_prefix: str = "\n\n[HINT FROM TEACHER]: ",
        hint_suffix: str = "\n\n",
        **kwargs: Any,
    ):
        self.engine_type = engine_type
        self.engine_kwargs = dict(engine_kwargs or {})
        self.check_interval = check_interval
        self.min_turns = min_turns
        self.k = k
        self.teacher_system_prompt = teacher_system_prompt or _DEFAULT_SYSTEM_PROMPT
        self.teacher_user_prompt_template = (
            teacher_user_prompt_template or _DEFAULT_USER_PROMPT_TEMPLATE
        )
        self.max_hint_tokens = max_hint_tokens
        self.recent_turn_content_cap = recent_turn_content_cap
        self.task_instruction_cap = task_instruction_cap
        self.hint_prefix = hint_prefix
        self.hint_suffix = hint_suffix

        # Lazy-initialised on first call to get_hint().
        self._engine = None
        # Counters for hint-fire health (surfaces silent failures that the
        # trace analysis of 2026-05-17 found were dominant — 87% of expected
        # fires were swallowed in the prior try/return None path).
        # Read via :meth:`drop_stats`; key set documented in :meth:`_record_drop`.
        self._drop_counts: dict[str, int] = {}
        self._fire_count: int = 0

    # ------------------------------------------------------------------
    # Registry
    # ------------------------------------------------------------------

    @classmethod
    def name(cls) -> str:
        return "teacher_hint"

    # ------------------------------------------------------------------
    # Core PRM interface
    # ------------------------------------------------------------------

    def should_terminate(
        self,
        turn: int,
        trajectory_steps: list,
        messages: list,
    ) -> bool:
        """Teacher never kills the agent — always returns False."""
        return False

    # ------------------------------------------------------------------
    # Hint generation
    # ------------------------------------------------------------------

    def _record_drop(
        self, reason: str, turn: int, *, exc: Exception | None = None
    ) -> None:
        """Increment the drop counter and emit a structured warning.

        Reason taxonomy (keep stable — analysis scripts grep these):
          - ``gate_min_turns``    — ``turn < self.min_turns``
          - ``gate_interval``     — ``turn % self.check_interval != 0``
          - ``engine_init_failed``— ``_create_engine`` returned None
          - ``generate_threw``    — engine.generate raised
          - ``empty_response``    — engine returned empty / whitespace-only text

        ``gate_*`` are normal scheduling skips and only debug-logged.
        Everything else is warning-logged with the exception so PRMs aren't
        silent failures anymore (the 2026-05-18 trace analysis found 87 % of
        expected fires were silently dropped in the prior implementation).
        """
        self._drop_counts[reason] = self._drop_counts.get(reason, 0) + 1
        if reason.startswith("gate_"):
            return  # benign — don't spam the log
        if exc is not None:
            logger.warning(
                "teacher_hint dropped (reason=%s) at turn %d: %s",
                reason,
                turn,
                exc,
                exc_info=True,
            )
        else:
            logger.warning(
                "teacher_hint dropped (reason=%s) at turn %d",
                reason,
                turn,
            )

    def drop_stats(self) -> dict[str, int]:
        """Return a copy of the drop-reason counter dict + fire count.

        Surfaced so callers (e.g. a trial postprocessing hook) can log this
        per-trial. The key ``fired`` records successful hint generations;
        the rest match :meth:`_record_drop` reasons.
        """
        return {"fired": self._fire_count, **self._drop_counts}

    def get_hint(
        self,
        turn: int,
        trajectory_steps: list,
        messages: list,
    ) -> str | None:
        """Generate a hint if timing gates pass, else return None.

        Every None-return path increments a counter via :meth:`_record_drop`
        so silent failures show up in logs and post-trial summaries. The
        prior try/return-None pattern swallowed engine errors and made
        87 % of "expected fires" invisible (see 2026-05-18 trace analysis).
        """
        if turn < self.min_turns:
            self._record_drop("gate_min_turns", turn)
            return None
        if turn % self.check_interval != 0:
            self._record_drop("gate_interval", turn)
            return None

        # Lazy engine init
        if self._engine is None:
            self._engine = self._create_engine()
            if self._engine is None:
                self._record_drop("engine_init_failed", turn)
                return None

        # Build the teacher prompt
        task_instruction = self._extract_task_instruction(messages)
        recent_turns = self._format_recent_turns(messages)
        user_prompt = self.teacher_user_prompt_template.format(
            task_instruction=task_instruction,
            recent_turns=recent_turns,
            k=self.k,
        )
        full_prompt = (
            f"### System\n{self.teacher_system_prompt}\n\n### User\n{user_prompt}"
        )

        try:
            raw_hint = self._engine.generate(
                full_prompt,
                max_tokens=self.max_hint_tokens,
            )
        except Exception as exc:
            self._record_drop("generate_threw", turn, exc=exc)
            return None

        if not raw_hint or not raw_hint.strip():
            self._record_drop("empty_response", turn)
            return None

        self._fire_count += 1
        return f"{self.hint_prefix}{raw_hint.strip()}{self.hint_suffix}"

    # ------------------------------------------------------------------
    # Callback override
    # ------------------------------------------------------------------

    def as_turn_callback(self) -> Callable:
        """Return a closure that returns ``str`` (hint) or ``False`` (no hint)."""

        def _callback(
            turn: int,
            trajectory_steps: list,
            messages: list,
        ) -> str | bool:
            hint = self.get_hint(turn, trajectory_steps, messages)
            if hint:
                return hint
            return False

        return _callback

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _create_engine(self):
        """Lazy-create the inference engine via data.generation.engines."""
        try:
            from data.generation.engines import create_inference_engine

            return create_inference_engine(self.engine_type, **self.engine_kwargs)
        except Exception:
            logger.warning(
                "Failed to create teacher hint engine (type=%s); "
                "hints will be disabled for this run.",
                self.engine_type,
                exc_info=True,
            )
            return None

    def _extract_task_instruction(self, messages: list) -> str:
        """Extract the task instruction from the first message, truncated."""
        if not messages:
            return "(no instruction available)"
        content = messages[0].get("content", "")
        cap = self.task_instruction_cap
        if len(content) > cap:
            content = content[:cap] + "..."
        return content

    def _format_recent_turns(self, messages: list) -> str:
        """Format the last 2*k messages as [ROLE]\\ncontent blocks."""
        tail = messages[-(2 * self.k) :] if len(messages) > 2 * self.k else messages
        parts = []
        cap = self.recent_turn_content_cap
        for msg in tail:
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")
            if len(content) > cap:
                content = content[:cap] + "..."
            parts.append(f"[{role}]\n{content}")
        return "\n\n".join(parts)
