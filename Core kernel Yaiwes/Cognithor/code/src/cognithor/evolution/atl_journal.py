"""ATL Journal — daily markdown journal for thinking cycles."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

__all__ = ["ATLJournal"]


class ATLJournal:
    """Writes and reads daily markdown journal files for ATL cycles."""

    def __init__(self, journal_dir: Path) -> None:
        self._dir = Path(journal_dir)

    def _today_path(self) -> Path:
        return self._dir / f"{datetime.date.today().isoformat()}.md"

    async def log_cycle(
        self,
        cycle: int,
        summary: str,
        goal_updates: list[dict[str, Any]],
        actions: list[str],
    ) -> None:
        """Append a cycle entry to today's journal file."""
        self._dir.mkdir(parents=True, exist_ok=True)
        now = datetime.datetime.now().strftime("%H:%M")

        lines = [f"\n## Zyklus #{cycle} — {now}\n"]
        lines.append(f"**Gedanken:** {summary}\n")

        if goal_updates:
            lines.append("**Ziel-Updates:**")
            for gu in goal_updates:
                gid = gu.get("goal_id", "?")
                delta = gu.get("progress_delta", gu.get("delta", 0))
                note = gu.get("note", "")
                lines.append(f"- {gid}: +{delta:.0%} {note}")
            lines.append("")

        if actions:
            lines.append("**Aktionen:**")
            for a in actions:
                lines.append(f"- {a}")
            lines.append("")

        lines.append("---\n")

        path = self._today_path()
        if not path.exists():
            header = f"# ATL Journal — {datetime.date.today().isoformat()}\n"
            path.write_text(header, encoding="utf-8")

        with open(path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def today(self) -> str | None:
        """Read today's journal. Returns None if no journal exists."""
        path = self._today_path()
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def recent(self, days: int = 7) -> list[str]:
        """Read journal entries from the last N days."""
        entries = []
        today = datetime.date.today()
        for i in range(days):
            d = today - datetime.timedelta(days=i)
            path = self._dir / f"{d.isoformat()}.md"
            if path.exists():
                entries.append(path.read_text(encoding="utf-8"))
        return entries
