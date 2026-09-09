from dataclasses import dataclass
from typing import Literal

Vote = Literal["PASS", "FAIL", "VETO"]


@dataclass(frozen=True)
class TribunalVote:
    role: str
    vote: Vote
    score: int | None = None  # 0-100 for non-veto roles
    reason: str = ""


class Tribunal:
    """Tribunal 6 roles (SOURCE: SALIDA_1_CAPA_CONTROL_PARTE_3 §35).

    SHERIFF / CENTINELA → VETO inmediato
    JUEZ / SUPERVISOR / VALIDADOR / VERIFICADOR → score 0-100
    PASA si score≥70 Y 4/6 aprueban y sin veto.
    """

    ROLES = ("sheriff", "centinela", "juez", "supervisor", "validador", "verificador")

    def evaluate(self, votes: list[TribunalVote]) -> tuple[bool, str]:
        if any(v.vote == "VETO" for v in votes):
            return False, "VETO by sheriff/centinela"

        scores = [v.score for v in votes if v.score is not None]
        if not scores:
            return False, "no scores"

        avg = sum(scores) / len(scores)
        approvals = sum(1 for v in votes if v.vote == "PASS")

        if avg >= 70 and approvals >= 4:
            return True, f"PASS avg={avg:.0f} approvals={approvals}/6"
        return False, f"FAIL avg={avg:.0f} approvals={approvals}/6"
