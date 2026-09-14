"""Abstract base class for document parsers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from cognithor.memory.hierarchical.models import RawSection


class DocumentParser(ABC):
    """Base class that all document parsers must implement."""

    @abstractmethod
    def parse(self, content: str | bytes, source_path: Path) -> list[RawSection]:
        """Parse *content* and return a flat list of sections."""
        ...

    @abstractmethod
    def supported_extensions(self) -> frozenset[str]:
        """Return the set of file extensions this parser handles."""
        ...
