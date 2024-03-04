"""A test constants class for the test module."""  # noqa: D205, D415

from dataclasses import dataclass

from virtual_ecosystem.core.constants_class import ConstantsDataclass


@dataclass(frozen=True)
class TestConsts(ConstantsDataclass):
    """Test constants."""

    a_constant: float = 123.4
