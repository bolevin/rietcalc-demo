"""The CIF reader: the bundled sample and the lexical corners of the format."""

from __future__ import annotations

from pathlib import Path

import pytest

from rietcalc_demo.adapters.cif import CifReader
from rietcalc_demo.application import StructureFormatError
from rietcalc_demo.domain import InvalidStructureError, Structure

MINIMAL = """\
data_minimal
_cell_length_a 4.0(1)
_cell_length_b 4.0(1)
_cell_length_c 4.0(1)
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 90
loop_
_symmetry_equiv_pos_as_xyz
x,y,z
loop_
_atom_site_label
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
Na1 0 0 0
"""


def read(tmp_path: Path, text: str) -> Structure:
    path = tmp_path / "test.cif"
    path.write_text(text, encoding="utf-8")
    return CifReader().read(path)


def test_sample(sample: Structure) -> None:
    assert sample.title == "CaTiO3-type perovskite (synthetic demo data)"
    assert sample.space_group == "P n m a"
    assert len(sample.operators) == 8
    assert [a.label for a in sample.atoms] == ["Ca1", "Ti1", "O1", "O2"]
    assert [a.element for a in sample.atoms] == ["Ca", "Ti", "O", "O"]
    assert sample.cell.a.value == 5.4423
    assert sample.cell.a.esd == pytest.approx(0.0003)
    ca = sample.atoms[0]
    assert ca.x.esd == pytest.approx(0.0004)
    assert ca.y.esd == 0.0  # y = 1/4 is fixed by symmetry


def test_old_symmetry_tag_and_element_from_label(tmp_path: Path) -> None:
    structure = read(tmp_path, MINIMAL)
    assert structure.title == "minimal"  # no chemical name: the block name
    assert structure.atoms[0].element == "Na"
    assert structure.atoms[0].occupancy.value == 1.0


def test_quotes_comments_and_text_fields(tmp_path: Path) -> None:
    text = MINIMAL.replace(
        "data_minimal",
        "data_minimal\n"
        "# a comment line\n"
        "_chemical_name_common 'Brese and O'Keeffe test'  # trailing comment\n"
        "_publ_section_title\n;\nA text field with _tags and loop_ inside\n;",
    )
    structure = read(tmp_path, text)
    # a quote closes a string only before a blank: the apostrophe survives
    assert structure.title == "Brese and O'Keeffe test"


def test_unknown_occupancy_means_full(tmp_path: Path) -> None:
    text = MINIMAL.replace("_atom_site_fract_z\n", "_atom_site_fract_z\n_atom_site_occupancy\n")
    structure = read(tmp_path, text.replace("Na1 0 0 0", "Na1 0 0 0 ?"))
    assert structure.atoms[0].occupancy.value == 1.0


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (("_cell_length_c 4.0(1)\n", ""), "_cell_length_c"),
        (("loop_\n_symmetry_equiv_pos_as_xyz\nx,y,z\n", ""), "no symmetry operators"),
        (("Na1 0 0 0", "Na1 0 0"), "values for 4 columns"),
        (("_cell_length_a 4.0(1)", "_cell_length_a four"), "cannot read"),
        (("data_minimal", "no data block here"), "no CIF data block"),
    ],
)
def test_format_errors_name_the_problem(
    tmp_path: Path, change: tuple[str, str], message: str
) -> None:
    with pytest.raises(StructureFormatError, match=message):
        read(tmp_path, MINIMAL.replace(*change))


def test_an_impossible_structure_is_a_domain_error(tmp_path: Path) -> None:
    with pytest.raises(InvalidStructureError):
        read(tmp_path, MINIMAL.replace("_cell_angle_alpha 90", "_cell_angle_alpha 200"))
