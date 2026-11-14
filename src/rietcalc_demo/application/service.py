"""The three things a user can do: load a structure, compute distances, export the report."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rietcalc_demo.application.ports import ReportRenderer, StructureReader, TextStore
from rietcalc_demo.domain import DistanceAnalysis, DistanceSettings, Structure, analyse


@dataclass(frozen=True, slots=True)
class LoadedStructure:
    source: Path
    structure: Structure


@dataclass(frozen=True, slots=True)
class DistanceRun:
    """One finished calculation with everything needed to report it."""

    source: Path
    analysis: DistanceAnalysis


class DistanceService:
    """Use cases.  Holds no state: every call says what it works on."""

    def __init__(self, reader: StructureReader, renderer: ReportRenderer, store: TextStore) -> None:
        self._reader = reader
        self._renderer = renderer
        self._store = store

    def load(self, path: Path) -> LoadedStructure:
        return LoadedStructure(source=path, structure=self._reader.read(path))

    def analyse(self, loaded: LoadedStructure, settings: DistanceSettings) -> DistanceRun:
        return DistanceRun(source=loaded.source, analysis=analyse(loaded.structure, settings))

    def report(self, run: DistanceRun) -> str:
        return self._renderer.render(run)

    def export(self, run: DistanceRun, path: Path) -> None:
        self._store.save(path, self._renderer.render(run))
