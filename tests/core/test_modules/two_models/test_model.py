"""A test module to test module registration."""

from virtual_ecosystem.core.base_model import BaseModel


class ATestModel1(
    BaseModel,
    model_name="two_models",
    vars_required_for_init=tuple(),
    model_update_bounds=("1 day", "1 month"),
    vars_updated=tuple(),
    vars_required_for_update=tuple(),
    vars_populated_by_init=tuple(),
    vars_populated_by_first_update=tuple(),
):
    """A test module."""


class ATestModel2(
    BaseModel,
    model_name="two_models",
    vars_required_for_init=tuple(),
    model_update_bounds=("1 day", "1 month"),
    vars_updated=tuple(),
    vars_required_for_update=tuple(),
    vars_populated_by_init=tuple(),
    vars_populated_by_first_update=tuple(),
):
    """A second unwanted test module."""
