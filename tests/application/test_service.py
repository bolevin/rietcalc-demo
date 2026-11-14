"""The use cases, with every port replaced by a fake: no file is touched."""

from __future__ import annotations

from pathlib import Path

from rietcalc_demo.application import DistanceRun, DistanceService
from rietcalc_demo.domain import DistanceSettings, Structure


class FakeReader:
    def __init__(self, structure: Structure) -> None:
        self.structure = structure
        self.paths: list[Path] = []

    def read(self, path: Path) -> Structure:
        self.paths.append(path)
        return self.structure


class FakeRenderer:
    def render(self, run: DistanceRun) -> str:
        return f"{len(run.analysis.contacts)} contacts"


class FakeStore:
    def __init__(self) -> None:
        self.saved: dict[Path, str] = {}

    def save(self, path: Path, text: str) -> None:
        self.saved[path] = text


def test_load_analyse_export(primitive_cubic: Structure) -> None:
    reader, store = FakeReader(primitive_cubic), FakeStore()
    service = DistanceService(reader, FakeRenderer(), store)

    loaded = service.load(Path("cube.cif"))
    run = service.analyse(loaded, DistanceSettings(0.0, 4.5))
    service.export(run, Path("out.txt"))

    assert reader.paths == [Path("cube.cif")]
    assert run.source == Path("cube.cif")
    assert service.report(run) == "6 contacts"
    assert store.saved == {Path("out.txt"): "6 contacts"}
