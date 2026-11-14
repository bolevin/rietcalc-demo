"""Errors the calculation can raise.  Each one carries a message fit for the user."""


class DomainError(Exception):
    """Base class: the input cannot be analysed as it stands."""


class InvalidStructureError(DomainError):
    """The structure itself is inconsistent (no atoms, impossible cell, bad operator...)."""


class InvalidSettingsError(DomainError):
    """The calculation settings are out of range (e.g. R min not below R max)."""
