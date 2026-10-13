from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class CompiledContext:
    """Contexto acotado que se entrega al modelo/agente.

    SOURCE: arquitectura final de hf.md — Context Manager + Tree-sitter idea.
    """
    objective: str
    relevant_files: tuple[str, ...]
    errors: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    git_diff: str | None = None
    previous_decisions: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()


class ContextManager:
    """Compila contexto relevante en vez de enviar el repo completo."""

    def compile(
        self,
        objective: str,
        candidate_files: Sequence[str],
        max_files: int = 10,
        errors: Sequence[str] = (),
        constraints: Sequence[str] = (),
    ) -> CompiledContext:
        # stub: take first max_files (real version would use tree-sitter / LSP / ranking)
        selected = tuple(candidate_files[:max_files])
        return CompiledContext(
            objective=objective,
            relevant_files=selected,
            errors=tuple(errors),
            constraints=tuple(constraints),
        )
