"""Text files on disk."""

from __future__ import annotations

from pathlib import Path


class FileTextStore:
    """Implements :class:`rietcalc_demo.application.ports.TextStore`."""

    def save(self, path: Path, text: str) -> None:
        path.write_text(text, encoding="utf-8", newline="\r\n")
