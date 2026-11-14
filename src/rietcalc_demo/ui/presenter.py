"""Presenter: turns user intent into use-case calls and results into view models."""

from __future__ import annotations

from pathlib import Path

from rietcalc_demo.application import (
    DistanceRun,
    DistanceService,
    LoadedStructure,
    StructureFormatError,
)
from rietcalc_demo.domain import (
    DistanceSettings,
    DomainError,
    expand,
    format_measured,
    histogram,
    multiplicities,
)
from rietcalc_demo.ui.view import (
    AtomRow,
    BondRow,
    CellAtomRow,
    HistogramViewModel,
    MainView,
    Metric,
    ResultViewModel,
    SettingsInput,
    StructureViewModel,
)

#: Width of a histogram bin, Angstrom.  Fine enough to separate the Ti-O bonds of
#: the sample (1.949, 1.953, 1.960 A) from the next shell, coarse enough to read.
BIN_WIDTH = 0.05


class MainPresenter:
    def __init__(self, view: MainView, service: DistanceService, sample: Path) -> None:
        self._view = view
        self._service = service
        self._sample = sample
        self._loaded: LoadedStructure | None = None
        self._run: DistanceRun | None = None

    # ---- user intents --------------------------------------------------
    def open_file(self) -> None:
        path = self._view.ask_open_path()
        if path is not None:
            self.load(path)

    def open_sample(self) -> None:
        self.load(self._sample)

    def load(self, path: Path) -> None:
        try:
            loaded = self._service.load(path)
        except (OSError, StructureFormatError, DomainError) as error:
            self._view.show_error(f"Cannot open {path.name}", str(error))
            return
        self._loaded, self._run = loaded, None
        self._view.clear_result()
        self._view.show_structure(_structure_view_model(loaded))

    def calculate(self) -> None:
        if self._loaded is None:
            self._view.show_error("No structure", "Open a CIF file first.")
            return
        raw: SettingsInput = self._view.settings()
        try:
            run = self._service.analyse(self._loaded, DistanceSettings(raw.r_min, raw.r_max))
        except DomainError as error:
            self._run = None
            self._view.clear_result()
            self._view.show_error("Cannot calculate", str(error))
            return
        self._run = run
        self._view.show_result(_result_view_model(run, self._service.report(run)))

    def save_report(self) -> None:
        if self._run is None:
            self._view.show_error("Nothing to save", "Run the calculation first.")
            return
        suggested = self._run.source.with_name(self._run.source.stem + "_distances.txt")
        path = self._view.ask_save_path(suggested)
        if path is None:
            return
        try:
            self._service.export(self._run, path)
        except OSError as error:
            self._view.show_error("Cannot save the report", str(error))
            return
        self._view.show_success("Report saved", str(path))


def _structure_view_model(loaded: LoadedStructure) -> StructureViewModel:
    st = loaded.structure
    cell = st.cell
    names = ("a, Å", "b, Å", "c, Å", "α, °", "β, °", "γ, °")
    # "P n m a" in a CIF, Pnma on screen
    group = f"{st.space_group.replace(' ', '')} · " if st.space_group else ""
    mults = multiplicities(st)
    return StructureViewModel(
        file_name=loaded.source.name,
        title=st.title,
        summary=(
            f"{group}{len(st.operators)} operators · {len(st.atoms)} independent atoms, "
            f"{sum(mults)} in the cell"
        ),
        cell=(
            *(
                (name, format_measured(p.value, p.esd))
                for name, p in zip(names, cell.parameters, strict=True)
            ),
            ("V, Å³", format_measured(cell.volume.value, cell.volume.esd)),
        ),
        atoms=tuple(
            AtomRow(
                label=a.label,
                element=a.element,
                x=format_measured(a.x.value, a.x.esd),
                y=format_measured(a.y.value, a.y.esd),
                z=format_measured(a.z.value, a.z.esd),
                occupancy=format_measured(a.occupancy.value, a.occupancy.esd),
                multiplicity=str(m),
                # a site that some operator maps onto itself has fewer images than
                # there are operators: it sits on a symmetry element
                position="general" if m == len(st.operators) else "special",
            )
            for a, m in zip(st.atoms, mults, strict=True)
        ),
        operators=tuple(str(op) for op in st.operators),
        cell_atoms=tuple(
            CellAtomRow(
                label=st.atoms[image.atom].label,
                operator=f"{image.operator + 1}: {st.operators[image.operator]}",
                x=f"{image.position[0]:.4f}",
                y=f"{image.position[1]:.4f}",
                z=f"{image.position[2]:.4f}",
            )
            for image in expand(st)
        ),
    )


def _result_view_model(run: DistanceRun, report: str) -> ResultViewModel:
    a = run.analysis
    st = a.structure
    rows: list[BondRow] = []
    for c in a.coordination:
        for k, g in enumerate(c.groups):
            rows.append(
                BondRow(
                    source=c.source if k == 0 else "",
                    coordination=str(c.number) if k == 0 else "",
                    bond=f"{c.source}–{g.target}",
                    distance=format_measured(g.distance.value, g.distance.esd),
                    multiplicity=f"×{g.multiplicity}",
                )
            )
    shortest = min(a.contacts, key=lambda contact: contact.distance.value, default=None)
    bins = histogram((contact.distance.value for contact in a.contacts), BIN_WIDTH)
    s = a.settings
    return ResultViewModel(
        headline=Metric(
            "Cell volume, Å³",
            format_measured(a.volume.value, a.volume.esd),
            "propagated from a, b, c and the angles",
        ),
        metrics=(
            Metric("Atoms in the cell", str(a.atoms_in_cell), f"{len(st.atoms)} independent"),
            Metric("Contacts", str(len(a.contacts)), f"{s.r_min:.2f} ≤ d < {s.r_max:.2f} Å"),
            Metric(
                "Shortest bond, Å",
                format_measured(shortest.distance.value, shortest.distance.esd)
                if shortest
                else "-",
                (
                    f"{st.atoms[shortest.source].label}–{st.atoms[shortest.target].label}"
                    if shortest
                    else ""
                ),
            ),
            Metric(
                "Unique bonds",
                str(sum(len(c.groups) for c in a.coordination)),
                "after symmetry",
            ),
        ),
        bonds=tuple(rows),
        histogram=HistogramViewModel(
            centres=tuple((b.low + b.high) / 2 for b in bins),
            counts=tuple(b.count for b in bins),
            width=BIN_WIDTH,
            caption=f"{len(a.contacts)} contacts, bins of {BIN_WIDTH:g} Å",
        ),
        report=report,
    )
