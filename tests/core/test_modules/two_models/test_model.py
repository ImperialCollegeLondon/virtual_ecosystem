"""A test module to test module registration."""

from virtual_ecosystem.core.base_model import BaseModel


class ATestModel1(
    BaseModel,
    model_name="two_models",
    required_init_vars=tuple(),
    model_update_bounds=("1 day", "1 month"),
    vars_updated=tuple(),
):
    """A test module."""


class ATestModel2(
    BaseModel,
    model_name="two_models",
    required_init_vars=tuple(),
    model_update_bounds=("1 day", "1 month"),
    vars_updated=tuple(),
):
    """A second unwanted test module."""
