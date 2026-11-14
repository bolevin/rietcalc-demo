"""Ports: what the use cases need from the outside world.

The application owns these interfaces; adapters implement them.  Supporting
another structure format or another report layout means writing one new adapter -
no use case and no line of the calculation changes.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from rietcalc_demo.domain import Structure

if TYPE_CHECKING:
    from rietcalc_demo.application.service import DistanceRun


class StructureFormatError(Exception):
    """The file was read, but it is not a structure in the expected format."""


class StructureReader(Protocol):
    def read(self, path: Path) -> Structure:
        """Parse ``path``.  Raises OSError, StructureFormatError or InvalidStructureError."""
        ...


class ReportRenderer(Protocol):
    def render(self, run: DistanceRun) -> str:
        """The finished analysis as a document."""
        ...


class TextStore(Protocol):
    def save(self, path: Path, text: str) -> None:
        """Persist ``text``.  Raises OSError."""
        ...
