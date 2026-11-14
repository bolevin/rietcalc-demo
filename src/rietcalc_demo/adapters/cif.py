"""Read the subset of CIF the demo needs: cell, symmetry operators and atom sites.

CIF is the standard exchange format of crystallography (International Union of
Crystallography).  The reader understands its lexical rules - quoted strings,
semicolon text fields, comments, ``loop_`` tables, ``?`` and ``.`` for unknown
values, ``value(esd)`` numbers - and takes what it needs from the first data
block that has atoms.  Anything it cannot use is reported with a line number
rather than guessed.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from rietcalc_demo.application.ports import StructureFormatError
from rietcalc_demo.domain import (
    Atom,
    InvalidStructureError,
    Measured,
    Structure,
    SymmetryOperator,
    UnitCell,
    parse_measured,
)

_CELL = (
    "_cell_length_a",
    "_cell_length_b",
    "_cell_length_c",
    "_cell_angle_alpha",
    "_cell_angle_beta",
    "_cell_angle_gamma",
)
_OPERATOR_TAGS = ("_space_group_symop_operation_xyz", "_symmetry_equiv_pos_as_xyz")
_NULL = ("?", ".")
_ELEMENT = re.compile(r"[A-Z][a-z]?")


@dataclass(frozen=True, slots=True)
class _Token:
    text: str
    quoted: bool
    line: int


@dataclass(slots=True)
class _Block:
    name: str
    items: dict[str, tuple[str, int]] = field(default_factory=dict)
    loops: list[tuple[list[str], list[_Token]]] = field(default_factory=list)


def _tokens(text: str) -> Iterator[_Token]:
    """Split CIF text into tokens, honouring quotes, comments and text fields."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        number = i + 1
        if line.startswith(";"):  # a semicolon text field runs to the next ';' line
            body = [line[1:]]
            i += 1
            while i < len(lines) and not lines[i].startswith(";"):
                body.append(lines[i])
                i += 1
            yield _Token("\n".join(body).strip(), True, number)
            i += 1
            continue
        pos = 0
        while pos < len(line):
            ch = line[pos]
            if ch.isspace():
                pos += 1
            elif ch == "#":
                break
            elif ch in "'\"":
                # a quote closes a string only when followed by blank or end of line,
                # so 'the cell's own test' is one token
                end = pos + 1
                while end < len(line) and not (
                    line[end] == ch and (end + 1 == len(line) or line[end + 1].isspace())
                ):
                    end += 1
                yield _Token(line[pos + 1 : end], True, number)
                pos = end + 1
            else:
                end = pos
                while end < len(line) and not line[end].isspace():
                    end += 1
                yield _Token(line[pos:end], False, number)
                pos = end
        i += 1


def _blocks(text: str) -> list[_Block]:
    blocks: list[_Block] = []
    stream = list(_tokens(text))
    i = 0
    while i < len(stream):
        token = stream[i]
        word = token.text.lower()
        if not token.quoted and word.startswith("data_"):
            blocks.append(_Block(token.text[5:]))
            i += 1
        elif not blocks:
            i += 1  # anything before the first data block is ignored
        elif not token.quoted and word == "loop_":
            i += 1
            tags: list[str] = []
            while i < len(stream) and not stream[i].quoted and stream[i].text.startswith("_"):
                tags.append(stream[i].text.lower())
                i += 1
            values: list[_Token] = []
            while i < len(stream) and not (
                not stream[i].quoted
                and (
                    stream[i].text.startswith("_")
                    or stream[i].text.lower() in ("loop_",)
                    or stream[i].text.lower().startswith("data_")
                )
            ):
                values.append(stream[i])
                i += 1
            blocks[-1].loops.append((tags, values))
        elif not token.quoted and token.text.startswith("_"):
            if i + 1 >= len(stream):
                raise StructureFormatError(f"Line {token.line}: {token.text} has no value.")
            blocks[-1].items[word] = (stream[i + 1].text, stream[i + 1].line)
            i += 2
        else:
            i += 1
    return blocks


def _rows(block: _Block, first_tag: str) -> tuple[list[str], list[list[_Token]]] | None:
    for tags, values in block.loops:
        if first_tag in tags:
            if len(values) % len(tags):
                raise StructureFormatError(
                    f"Line {values[0].line if values else '?'}: the {first_tag} table has "
                    f"{len(values)} values for {len(tags)} columns."
                )
            width = len(tags)
            return tags, [values[k : k + width] for k in range(0, len(values), width)]
    return None


def _measured(text: str, what: str, line: int, *, default: float | None = None) -> Measured:
    if text in _NULL:
        if default is None:
            raise StructureFormatError(f"Line {line}: {what} is not given.")
        return Measured(default)
    try:
        value, esd = parse_measured(text)
    except ValueError:
        raise StructureFormatError(f"Line {line}: cannot read {what} from {text!r}.") from None
    return Measured(value, esd)


def _element(type_symbol: str, label: str) -> str:
    for candidate in (type_symbol, label):
        match = _ELEMENT.match(candidate)
        if match:
            return match.group()
    return ""


class CifReader:
    """Implements :class:`rietcalc_demo.application.ports.StructureReader`."""

    def read(self, path: Path) -> Structure:
        text = path.read_text(encoding="utf-8", errors="replace")
        blocks = _blocks(text)
        if not blocks:
            raise StructureFormatError("The file has no CIF data block.")
        block = next((b for b in blocks if _rows(b, "_atom_site_fract_x") is not None), blocks[0])
        try:
            return Structure(
                title=self._title(block),
                cell=self._cell(block),
                operators=self._operators(block),
                atoms=self._atoms(block),
                space_group=self._space_group(block),
            )
        except InvalidStructureError:
            raise
        except (KeyError, IndexError) as missing:  # pragma: no cover - defensive
            raise StructureFormatError(f"Incomplete CIF: {missing}") from None

    @staticmethod
    def _title(block: _Block) -> str:
        name, _line = block.items.get("_chemical_name_common", ("", 0))
        return name if name and name not in _NULL else block.name

    @staticmethod
    def _space_group(block: _Block) -> str:
        for tag in ("_space_group_name_h-m_alt", "_symmetry_space_group_name_h-m"):
            text, _line = block.items.get(tag, ("", 0))
            if text and text not in _NULL:
                return " ".join(text.split())
        return ""

    @staticmethod
    def _cell(block: _Block) -> UnitCell:
        values = []
        for tag in _CELL:
            if tag not in block.items:
                raise StructureFormatError(f"The CIF does not give {tag}.")
            text, line = block.items[tag]
            values.append(_measured(text, tag, line))
        return UnitCell(*values)

    @staticmethod
    def _operators(block: _Block) -> tuple[SymmetryOperator, ...]:
        for tag in _OPERATOR_TAGS:
            found = _rows(block, tag)
            if found is not None:
                tags, rows = found
                column = tags.index(tag)
                return tuple(SymmetryOperator.parse(row[column].text) for row in rows)
        raise StructureFormatError(
            "The CIF lists no symmetry operators.  The demo reads them from "
            "_space_group_symop_operation_xyz; it does not derive them from the "
            "space-group symbol."
        )

    @staticmethod
    def _atoms(block: _Block) -> tuple[Atom, ...]:
        found = _rows(block, "_atom_site_fract_x")
        if found is None:
            raise StructureFormatError("The CIF has no _atom_site table.")
        tags, rows = found
        for needed in ("_atom_site_label", "_atom_site_fract_y", "_atom_site_fract_z"):
            if needed not in tags:
                raise StructureFormatError(f"The _atom_site table has no {needed} column.")

        def cell(row: list[_Token], tag: str) -> _Token | None:
            return row[tags.index(tag)] if tag in tags else None

        atoms = []
        for row in rows:
            label = row[tags.index("_atom_site_label")].text
            symbol = cell(row, "_atom_site_type_symbol")
            occ = cell(row, "_atom_site_occupancy")
            coordinates = [
                _measured(t.text, f"{label} {axis}", t.line)
                for axis, t in zip(
                    "xyz",
                    (row[tags.index(f"_atom_site_fract_{a}")] for a in "xyz"),
                    strict=True,
                )
            ]
            atoms.append(
                Atom(
                    label=label,
                    element=_element(symbol.text if symbol else "", label),
                    x=coordinates[0],
                    y=coordinates[1],
                    z=coordinates[2],
                    occupancy=(
                        _measured(occ.text, f"{label} occupancy", occ.line, default=1.0)
                        if occ
                        else Measured(1.0)
                    ),
                )
            )
        return tuple(atoms)
